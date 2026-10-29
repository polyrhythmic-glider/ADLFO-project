"""Short, collision-screened SMD ground connections to the dedicated inner plane.

Freerouting treats a Specctra plane net as already connected; KiCad still needs
physical vias from surface pads. Native DRC is mandatory after this step.
"""
from collections import defaultdict
from math import hypot
import heapq
import pcbnew as pcb


def connect_ground(board):
    scale=pcb.FromMM(1);cell=pcb.FromMM(2);clearance=pcb.FromMM(.16)
    obstacles=defaultdict(list);holes=defaultdict(list);ground=[]
    def cells(box):
        for x in range(box.GetLeft()//cell,box.GetRight()//cell+1):
            for y in range(box.GetTop()//cell,box.GetBottom()//cell+1):yield x,y
    def index(item,layers):
        for layer in layers:
            shape=item.GetEffectiveShape(layer)
            for key in cells(item.GetBoundingBox()):obstacles[(layer,*key)].append((item.GetNetCode(),shape))
    def hole(item,diameter):
        if not diameter:return
        shape=pcb.SHAPE_CIRCLE(item.GetPosition(),diameter//2)
        for key in cells(shape.BBox()):holes[key].append(shape)
    copper=list(board.GetEnabledLayers().CuStack())
    pads=[p for fp in board.GetFootprints() for p in fp.Pads()]
    gnd=board.FindNet('GND').GetNetCode()
    assert gnd>0 and pcb.In1_Cu in copper,'Requires the four-layer board and GND net'
    for pad in pads:
        index(pad,[l for l in copper if pad.IsOnLayer(l)])
        hole(pad,max(pad.GetDrillSize().x,pad.GetDrillSize().y))
        if pad.GetNetCode()==gnd and pad.GetAttribute()==pcb.PAD_ATTRIB_PTH:ground.append((pad.GetPosition(),None))
    for track in board.GetTracks():
        via=isinstance(track,pcb.PCB_VIA)
        index(track,copper if via else [track.GetLayer()])
        if via:
            hole(track,track.GetDrillValue())
            if track.GetNetCode()==gnd:ground.append((track.GetPosition(),track))
    def nearby(shape,layer):
        box=shape.BBox();box.Inflate(clearance)
        for key in cells(box):yield from obstacles[(layer,*key)]
    def free(shape,layer):
        return all(net==gnd or not pcb.SHAPE.Collide(shape,other,clearance) for net,other in nearby(shape,layer))
    def via_free(point):
        circle=pcb.SHAPE_CIRCLE(point,pcb.FromMM(.3));box=circle.BBox();box.Inflate(pcb.FromMM(.25))
        # Same-net pads on the other side still wick solder into an untented hole.
        hole_shape=pcb.SHAPE_CIRCLE(point,pcb.FromMM(.15))
        if any(p.GetAttribute()==pcb.PAD_ATTRIB_SMD and p.GetEffectiveShape(p.GetLayer()).Collide(hole_shape,pcb.FromMM(.1)) for p in pads):return False
        if any(pcb.SHAPE.Collide(circle,h,pcb.FromMM(.10)) for key in cells(box) for h in holes[key]):return False
        return all(free(circle,l) for l in copper)
    edge=board.GetBoardEdgesBoundingBox();margin=pcb.FromMM(.62)
    def inside(point):return edge.GetLeft()+margin<=point.x<=edge.GetRight()-margin and edge.GetTop()+margin<=point.y<=edge.GetBottom()-margin
    def line_free(a,b,layer):return free(pcb.SHAPE_SEGMENT(a,b,pcb.FromMM(.2)),layer)
    def add_line(a,b,layer):
        if a==b:return
        track=pcb.PCB_TRACK(board);track.SetStart(a);track.SetEnd(b);track.SetWidth(pcb.FromMM(.2))
        track.SetLayer(layer);track.SetNetCode(gnd);board.Add(track);index(track,[layer])
    count=0;unresolved=[]
    offsets=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
    for pad in pads:
        if pad.GetNetCode()!=gnd or pad.GetAttribute()!=pcb.PAD_ATTRIB_SMD:continue
        a=pad.GetPosition();layer=pcb.F_Cu if pad.IsOnLayer(pcb.F_Cu) else pcb.B_Cu;done=False
        for b,_ in sorted(ground,key=lambda item:hypot(item[0].x-a.x,item[0].y-a.y)):
            if hypot(b.x-a.x,b.y-a.y)>pcb.FromMM(3):break
            if line_free(a,b,layer):add_line(a,b,layer);done=True;break
        if done:continue
        for distance in (.8,1,1.2,1.5,2,2.5,3,4):
            for dx,dy in offsets:
                b=pcb.VECTOR2I(a.x+round(dx*distance*scale),a.y+round(dy*distance*scale))
                if not inside(b):continue
                # Keep the drilled hole out of the solderable pad (no via-in-pad requirement).
                if pad.GetEffectiveShape(layer).Collide(pcb.SHAPE_CIRCLE(b,pcb.FromMM(.15)),pcb.FromMM(.1)):continue
                if not via_free(b) or not line_free(a,b,layer):continue
                via=pcb.PCB_VIA(board);via.SetPosition(b);via.SetWidth(pcb.FromMM(.6));via.SetDrill(pcb.FromMM(.3))
                via.SetViaType(pcb.VIATYPE_THROUGH);via.SetLayerPair(pcb.F_Cu,pcb.B_Cu);via.SetNetCode(gnd)
                board.Add(via);index(via,copper);hole(via,via.GetDrillValue());ground.append((b,via))
                add_line(a,b,layer);count+=1;done=True;break
            if done:break
        if not done:
            # Escape closely spaced IC pins before looking for a free drilled-via location.
            step=pcb.FromMM(.2);queue=[(0,0,0)];costs={(0,0):0};parents={};target=None
            while queue:
                cost,x,y=heapq.heappop(queue)
                if cost>costs[(x,y)]:continue
                b=pcb.VECTOR2I(a.x+x*step,a.y+y*step)
                if inside(b) and not pad.GetEffectiveShape(layer).Collide(pcb.SHAPE_CIRCLE(b,pcb.FromMM(.15)),pcb.FromMM(.1)) and via_free(b):
                    target=(x,y);break
                for dx,dy in offsets:
                    nxt=(x+dx,y+dy)
                    if abs(nxt[0])>30 or abs(nxt[1])>30:continue
                    candidate=cost+hypot(dx,dy)
                    if candidate>=costs.get(nxt,float('inf')):continue
                    c=pcb.VECTOR2I(a.x+nxt[0]*step,a.y+nxt[1]*step)
                    if not inside(c) or not line_free(b,c,layer):continue
                    costs[nxt]=candidate;parents[nxt]=(x,y);heapq.heappush(queue,(candidate,*nxt))
            if target is not None:
                b=pcb.VECTOR2I(a.x+target[0]*step,a.y+target[1]*step)
                via=pcb.PCB_VIA(board);via.SetPosition(b);via.SetWidth(pcb.FromMM(.6));via.SetDrill(pcb.FromMM(.3))
                via.SetViaType(pcb.VIATYPE_THROUGH);via.SetLayerPair(pcb.F_Cu,pcb.B_Cu);via.SetNetCode(gnd)
                board.Add(via);index(via,copper);hole(via,via.GetDrillValue());ground.append((b,via));count+=1
                while target!=(0,0):
                    previous=parents[target];c=pcb.VECTOR2I(a.x+previous[0]*step,a.y+previous[1]*step)
                    add_line(c,b,layer);b=c;target=previous
                done=True
        if not done:unresolved.append(pad.GetParentFootprint().GetReference()+'.'+pad.GetNumber())
    print('Ground plane:',count,'new vias;',len(unresolved),'pads require further routing',unresolved)
    return unresolved


def inset_edge_vias(board):
    edge=board.GetBoardEdgesBoundingBox();moved=0
    tracks=list(board.GetTracks());pads=[p for fp in board.GetFootprints() for p in fp.Pads()]
    copper=list(board.GetEnabledLayers().CuStack())
    for via in tracks:
        if not isinstance(via,pcb.PCB_VIA):continue
        margin=via.GetWidth(pcb.F_Cu)//2+pcb.FromMM(.35);a=via.GetPosition()
        inset=pcb.VECTOR2I(max(edge.GetLeft()+margin,min(a.x,edge.GetRight()-margin)),max(edge.GetTop()+margin,min(a.y,edge.GetBottom()-margin)))
        if a==inset:continue
        connected=[t for t in tracks if not isinstance(t,pcb.PCB_VIA) and t.GetNetCode()==via.GetNetCode() and (t.GetStart()==a or t.GetEnd()==a)]
        obstacles=[(p.GetEffectiveShape(l),l) for p in pads if p.GetNetCode()!=via.GetNetCode() for l in copper if p.IsOnLayer(l)]
        obstacles += [(t.GetEffectiveShape(l),l) for t in tracks if t.GetNetCode()!=via.GetNetCode() for l in (copper if isinstance(t,pcb.PCB_VIA) else [t.GetLayer()])]
        done=False
        for dx,dy in [(0,0)]+[(x,y) for r in (.2,.4,.6,.8,1,1.2) for x,y in ((r,0),(-r,0),(0,r),(0,-r))]:
            b=pcb.VECTOR2I(inset.x+pcb.FromMM(dx),inset.y+pcb.FromMM(dy))
            if not (edge.GetLeft()+margin<=b.x<=edge.GetRight()-margin and edge.GetTop()+margin<=b.y<=edge.GetBottom()-margin):continue
            shapes=[(pcb.SHAPE_CIRCLE(b,via.GetWidth(pcb.F_Cu)//2),l) for l in copper]
            for t in connected:shapes.append((pcb.SHAPE_SEGMENT(b,t.GetEnd() if t.GetStart()==a else t.GetStart(),t.GetWidth()),t.GetLayer()))
            if any(pcb.SHAPE.Collide(s,o,pcb.FromMM(.16)) for s,l in shapes for o,m in obstacles if l==m):continue
            for t in connected:
                if t.GetStart()==a:t.SetStart(b)
                if t.GetEnd()==a:t.SetEnd(b)
            via.SetPosition(b);moved+=1;done=True;break
        assert done,'No clear inset for edge via; manual routing required'
    print('Inset edge vias:',moved)
