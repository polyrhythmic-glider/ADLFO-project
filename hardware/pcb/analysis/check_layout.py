"""Native filled-plane and solder-pad checks; run with KiCad's Python."""
from collections import defaultdict
from math import hypot, ceil
from pathlib import Path
import hashlib
import json
import pcbnew as pcb

ROOT=Path(__file__).resolve().parent.parent
path=ROOT/'output'/'Adolfo-main.kicad_pcb'
board=pcb.LoadBoard(str(path))
zones=[z for z in board.Zones() if z.GetLayer()==pcb.In1_Cu and z.GetNetname()=='GND']
assert len(zones)==1 and zones[0].HasFilledPolysForLayer(pcb.In1_Cu)
zone=zones[0];samples=defaultdict(lambda:[0,0,0])
for track in board.GetTracks():
    if isinstance(track,pcb.PCB_VIA):continue
    net=track.GetNetname()
    if not net or net=='GND' or net.startswith(('+','-')):continue
    a,b=track.GetStart(),track.GetEnd()
    count=max(1,ceil(pcb.ToMM(track.GetLength())/2))
    for i in range(count):
        t=(i+.5)/count
        point=pcb.VECTOR2I(round(a.x+(b.x-a.x)*t),round(a.y+(b.y-a.y)*t))
        samples[net][0]+=1
        samples[net][1]+=zone.HitTestFilledArea(pcb.In1_Cu,point,0)
        samples[net][2]+=zone.HitTestFilledArea(pcb.In1_Cu,point,pcb.FromMM(.5))
pads=[p for fp in board.GetFootprints() for p in fp.Pads() if p.GetAttribute()==pcb.PAD_ATTRIB_SMD]
overlaps=[]
for via in board.GetTracks():
    if not isinstance(via,pcb.PCB_VIA):continue
    point=via.GetPosition()
    for pad in pads:
        if pad.GetEffectiveShape(pad.GetLayer()).Collide(pcb.SHAPE_CIRCLE(point,via.GetDrillValue()//2),0):
            overlaps.append({'pad':pad.GetParentFootprint().GetReference()+'.'+pad.GetNumber(),
                             'x':pcb.ToMM(point.x),'y':pcb.ToMM(point.y),'net':via.GetNetname()})
report={'board_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'method':'Trace midpoint samples at <=2 mm intervals against native In1.Cu filled GND, exact and within 0.5 mm. Not an impedance or full-wave model.',
        'plane_samples':{n:{'count':v[0],'exact_pct':round(v[1]/v[0]*100,2),
                            'within_0_5mm_pct':round(v[2]/v[0]*100,2)} for n,v in sorted(samples.items())},
        'drilled_vias_intersecting_smd_lands':overlaps}
out=Path(__file__).with_name('layout-check.json');out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
critical={n:v for n,v in report['plane_samples'].items() if any(k in n for k in ('SCK','MISO','MOSI','CONVST'))}
print(json.dumps({'critical_plane_samples':critical,'smd_via_overlaps':overlaps},indent=2))
assert samples and all(v[0]>0 for v in samples.values())
