#!/usr/bin/env python3
"""Generate rev D source CAD; native preparation, routing and checks follow."""
from pathlib import Path
from copy import deepcopy
from dataclasses import fields,is_dataclass
from uuid import uuid5,NAMESPACE_URL
import csv,json,math,xml.etree.ElementTree as ET
from kiutils.board import Board
from kiutils.footprint import Footprint,Pad,DrillDefinition
from kiutils.items.common import Position as P,Net,Effects,Font,TitleBlock
from kiutils.items.fpitems import FpRect,FpText
from kiutils.items.gritems import GrRect
from kiutils.utils import sexpr
from design import PANEL,PCB,COLUMNS,MOUNTS,OLED,RAIL_SLOTS,PORTS,PINS,RATES,INTERCONNECT,RELEASE_BLOCKERS,circuit,holes
HERE=Path(__file__).resolve().parent
OUT=HERE/'output'
LIB=OUT/'ADOLFO.pretty'
def uid(s):return str(uuid5(NAMESPACE_URL,'adolfo/universal-c/'+s))
def q(s):return json.dumps(str(s),ensure_ascii=False)
def eff(size=1):return Effects(font=Font(height=size,width=size,thickness=.15))
def pad(num, x, y, drill=1.0, diameter=1.8):
    return Pad(number=str(num),type='thru_hole',shape='circle',position=P(x,y),
               size=P(diameter,diameter),drill=DrillDefinition(diameter=drill),layers=['*.Cu','*.Mask'])

def npth(x,y,d):
    p=pad('',x,y,d,d); p.type='np_thru_hole'; return p

def body(fp,w,h,cx=0,cy=0):
    for layer,margin in [('F.Fab',0),('F.SilkS',0.12),('F.CrtYd',0.4)]:
        fp.graphicItems.append(FpRect(start=P(cx-w/2-margin,cy-h/2-margin),
            end=P(cx+w/2+margin,cy+h/2+margin),layer=layer,width=0.1 if layer!='F.CrtYd' else 0.05))

def positions(obj):
    # Dataclass traversal avoids losing circles, lines or arc points during centering/flipping.
    if isinstance(obj,P): yield obj
    elif isinstance(obj,list):
        for x in obj: yield from positions(x)
    elif is_dataclass(obj):
        for f in fields(obj):
            if f.name not in ('size','drill','effects','models'):
                yield from positions(getattr(obj,f.name))

def make_footprint(kind):
    path=HERE/'vendor'/f'{kind}.kicad_mod'
    if path.exists():
        fp=Footprint.from_file(str(path))
        # Pin number and manufacturer's pad geometry stay intact.
        offset={'encoder':(7.5,2.5),'button':(3.25,2.25),'idc10':(1.27,5.08),'recom':(2.54,0)}.get(kind,(0,0))
        for p in positions(fp.graphicItems+fp.pads):
            p.X=round(p.X-offset[0],5);p.Y=round(p.Y-offset[1],5)
        if kind=='button': fp.description='E-Switch TL1105DF160Q, 6 x 6 mm, 13 mm actuator, 6.5 x 4.5 mm pin pitch'
    else:
        fp=Footprint.create_new('ADOLFO:'+kind,kind,type='through_hole')
        if kind=='seed':
            # Seed oriented horizontally, USB left before flipping to back.
            for i in range(20):
                fp.pads += [pad(i+1,-24.13+i*2.54,7.62,1.1,1.8),
                            pad(40-i,-24.13+i*2.54,-7.62,1.1,1.8)]
            body(fp,51,18)
        elif kind in ('header40','socket40'):
            sign=1 if kind=='header40' else -1
            for i in range(20):
                fp.pads += [pad(2*i+1,-1.27*sign,-24.13+i*2.54),pad(2*i+2,1.27*sign,-24.13+i*2.54)]
            # SSW body maximum includes Samtec's 0.25 mm length tolerance.
            body(fp,4.95 if kind=='socket40' else 5.08,51.56 if kind=='socket40' else 50.8)
        elif kind=='oled7':
            fp.pads=[pad(i+1,(i-3)*2.54,0) for i in range(7)]
            body(fp,26,26,cy=11.5)
        elif kind=='testpoint':
            fp.pads=[pad(1,0,0,0.8,2.0)]
        elif kind=='mount':
            fp.pads=[npth(0,0,3.2)]
            body(fp,6,6)
            fp.attributes.excludeFromBom=True
        else: raise ValueError(kind)
    fp.libId='ADOLFO:'+kind
    fp.properties.clear()
    fp.version='20211014';fp.generator='kiutils'
    fp.models=[]  # The deliverable is the native electrical/mechanical CAD, without a 3D rendering.
    fp.position=P(0,0,0);fp.tstamp=None
    # Remove inherited labels; compact labels generated consistently for this board.
    fp.graphicItems=[g for g in fp.graphicItems if not isinstance(g,FpText)]
    if kind=='mount':fp.graphicItems=[g for g in fp.graphicItems if getattr(g,'layer',None)!='F.SilkS']
    silk=kind in ('seed','lqfp64','tssop16','soic14','soic28','soic8')
    for typ,y,layer in [('reference',0,'F.SilkS' if silk else 'F.Fab'),('value',2.6,'F.Fab')]:
        fp.graphicItems.append(FpText(type=typ,text='REF**' if typ=='reference' else kind,
            position=P(0,y),layer=layer,effects=eff(1)))
    return fp

def flip(fp):
    for p in positions(fp.graphicItems+fp.pads):
        p.X=-p.X
        if p.angle is not None: p.angle=(-p.angle)%360
    for item in fp.graphicItems+fp.pads:
        if hasattr(item,'layer') and item.layer.startswith('F.'):item.layer='B.'+item.layer[2:]
        if hasattr(item,'layers'):item.layers=[('B.'+x[2:]) if x.startswith('F.') else x for x in item.layers]
        if isinstance(item,FpText):item.effects.justify.mirror=True
    fp.layer='B.Cu'


def bounds(fp):
    pts=[]
    for g in fp.graphicItems:
        if getattr(g,'layer','').endswith('CrtYd'):
            for k in ['start','end']:
                if hasattr(g,k):
                    p=getattr(g,k);pts.append((p.X,p.Y))
    for p in fp.pads:pts += [(p.position.X-p.size.X/2,p.position.Y-p.size.Y/2),(p.position.X+p.size.X/2,p.position.Y+p.size.Y/2)]
    return (min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts))

def board(parts,name,templates,nets,paths):
    b=Board.create_new();b.version='20221018';b.generator='pcbnew'
    b.titleBlock=TitleBlock(title='Adolfo universal / '+name,revision='D ENGINEERING - BENCH VALIDATION REQUIRED',date='2026-10-28')
    b.general.thickness=1.6;b.nets=list(nets.values())
    b.graphicItems.append(GrRect(start=P(PCB['x'],PCB['y']),end=P(PCB['x']+PCB['width'],PCB['y']+PCB['height']),layer='Edge.Cuts',width=.05,tstamp=uid(name+'edge')))
    for part in parts:
        fp=deepcopy(templates[part['footprint']]);fp.tstamp=uid(part['ref']);fp.path=paths[part['ref']]
        # Native pcbnew performs the final back-side flip, including its orientation.
        fp.position=P(part['x'],part['y'],0)
        for g in fp.graphicItems:
            if isinstance(g,FpText):g.text=part['ref'] if g.type=='reference' else part['value']
        known={str(p.number) for p in fp.pads if p.number}
        assert set(part['pins'])<=known,(part['ref'],set(part['pins'])-known)
        for p in fp.pads:
            p.tstamp=uid(f'{part["ref"]}/{p.number}/{p.position.X}/{p.position.Y}')
            net=part['pins'].get(str(p.number));p.net=nets[net] if net else None
        b.footprints.append(fp)
    for i,(x,y) in enumerate(MOUNTS,1):
        fp=deepcopy(templates['mount']);fp.position=P(x,y);fp.tstamp=uid(name+f'H{i}')
        for g in fp.graphicItems:
            if isinstance(g,FpText) and g.type=='reference':g.text=f'H{i}'
        b.footprints.append(fp)
    b.to_file(str(OUT/f'Adolfo-{name}.kicad_pcb'));return b

def placement_constraints():
    anchors={'U2':(33,31),'U3':(70,44),'U4':(30,100),'U5':(40,58),'U6':(62,58),
             'U7':(80,108),'U8':(75,85),'U9':(56,47),'U10':(88,48),'U11':(50,29),
             'U12':(82,47),'U13':(92,47),'U14':(10,65),'U15':(10,91),
             'U16':(46,45),'U17':(49,17),'U18':(57,17),'U19':(60,28),'U20':(65,17),
             'U21':(26,55),'U22':(26,80),'U23':(75,69),'U24':(75,95),'UREG':(29,17),
             'DPOWERP':(13,43),'DPOWERN':(13,49),'FPOWERP':(21,35),'FPOWERN':(10,42),'FB1':(44,18),'C5A':(43,21)}
    bypass={'CVDRV':('U2','23'),'CREG1':('U2','36'),'CREG2':('U2','39'),
            'CREFADC':('U2','42'),'CREFCAP':('U2','44'),'CREFDAC':('U3','8'),
            'CBUF0':('U12','14'),'CBUF1':('U13','14'),'C5D':('UREG','3'),
            'CREGIN':('UREG','1'),'CREGOUT':('UREG','3')}
    for j,pin in enumerate((1,37,38,48)):bypass[f'CADC{j}']=('U2',str(pin))
    for n in range(3):
        bypass[f'CP{n}P']=(f'U{9+n}','4');bypass[f'CP{n}N']=(f'U{9+n}','11')
    for n in range(21,25):
        bypass[f'CFAMP{n}P']=(f'U{n}','4');bypass[f'CFAMP{n}N']=(f'U{n}','11')
    for n,pin in [(16,14),(17,5),(18,6),(19,8),(20,5)]:bypass[f'CSAFE{n}']=(f'U{n}',str(pin))
    for n in range(2):
        bypass[f'CIP{n}P']=(f'U{14+n}','13');bypass[f'CIP{n}N']=(f'U{14+n}','4')
    for n,owner,pin in [(1,'UREG',3),(2,'U3',3),(3,'U4',9),(4,'U5',14),(5,'U6',14),
                        (6,'U7',13),(7,'U7',4),(8,'U8',13),(9,'U8',4)]:bypass[f'CD{n}']=(owner,str(pin))
    analog_owner={}
    units=[(3,2,1),(5,6,7),(10,9,8),(12,13,14)]
    for n in range(1,9):
        owner=f'U{9+(n-1)//4}';plus,minus,output=units[(n-1)%4]
        for prefix,pin in [('RA',plus),('RB',plus),('RC',minus),('RD',minus)]:analog_owner[prefix+str(n)]=(owner,str(pin))
    for direction in ('IN','OUT'):
        for ch in range(1,5):
            owner=f'U{(21 if direction=="IN" else 23)+(ch-1)//2}'
            for stage in (1,2):
                pin=units[((ch-1)%2)*2+stage-1][0]
                for prefix in ('R','C'):
                    for suffix in ('A','B'):analog_owner[f'{prefix}{direction}{ch}F{stage}{suffix}']=(owner,str(pin))
    analog_owner.update({'RREF1':('U11','3'),'RREF2':('U11','3'),
                        'RNMON1':('U19','6'),'RNMON2':('U19','6'),'CMONN':('U19','6'),
                        'RPMON1':('U19','3'),'RPMON2':('U19','3'),'CMONP':('U19','3'),
                        'R5MON1':('U18','5'),'R5MON2':('U18','5'),'CMON5':('U18','5')})
    analog_owner.update({'RADC_SCK':('U1','9'),'RADC_MOSI':('U1','11'),
                        'RDAC_SCK':('U12','3'),'RDAC_MOSI':('U12','6')})
    return anchors,bypass,analog_owner


def pack_main(parts,templates):
    """Place ICs, then local bypass/feedback parts, respecting both-side courtyards."""
    boxes=[(x-3.5,y-3.5,x+3.5,y+3.5,side) for x,y in MOUNTS for side in ('F','B')];pads=[]
    cached={}
    def geometry(p,x,y):
        if p['ref'] in cached:
            local,points=cached[p['ref']]
            a,c,d,e=local
            return (x+a-.25,y+c-.25,x+d+.25,y+e+.25,p['side']),[(x+u,y+v,w,h,typ) for u,v,w,h,typ in points]
        fp=deepcopy(templates[p['footprint']])
        if p['side']=='B':flip(fp)
        a,c,d,e=bounds(fp);box=(x+a-.25,y+c-.25,x+d+.25,y+e+.25,p['side'])
        localpoints=[(t.position.X,t.position.Y,t.size.X/2+.15,t.size.Y/2+.15,t.type) for t in fp.pads]
        cached[p['ref']]=((a,c,d,e),localpoints)
        pp=[(x+u,y+v,w,h,typ) for u,v,w,h,typ in localpoints]
        return box,pp
    def fits(box,pp):
        if box[0]<3.2 or box[1]<9.7 or box[2]>98 or box[3]>118.8:return False
        for a,c,d,e,side in boxes:
            if box[4]==side and min(d,box[2])>max(a,box[0]) and min(e,box[3])>max(c,box[1]):return False
        for x,y,w,h,typ in pp:
            for u,v,r,s,other in pads:
                if typ=='smd' and other=='smd':continue # same side handled by courtyard
                if abs(x-u)<w+r and abs(y-v)<h+s:return False
        return True
    main=[p for p in parts if p['board']=='main']
    role=lambda p:p['id']
    for p in main:
        if role(p)=='U1':p['y']=27
        if role(p)=='JPOWER':p['y']=28
    fixed=[p for p in main if role(p) in ['U1','JM','JPOWER']]
    for p in fixed:
        box,pp=geometry(p,p['x'],p['y']);assert fits(box,pp),p['ref'];boxes.append(box);pads.extend(pp)
    def area(p):
        a,b,c,d=bounds(templates[p['footprint']]);return (c-a)*(d-b)
    anchors,bypass,analog_owner=placement_constraints()
    placed={role(p):p for p in fixed}
    candidates=[(x,y) for y in range(11,118) for x in range(5,97)]
    rails={'GND','+3V3','+5A','+5D','+12VA','-12VA','SAFE_CLEAR_N','SAFE_PERMIT'}
    for p in sorted([p for p in main if p not in fixed],key=lambda p:(role(p).startswith('U'),role(p).startswith('CADC') or role(p)=='CVDRV',role(p) in bypass,role(p) in analog_owner,area(p)),reverse=True):
        done=False
        connected=[q for q in placed.values() if (set(p['pins'].values())-rails-{None}) & set(q['pins'].values())]
        target=anchors.get(role(p),(sum(q['x'] for q in connected)/len(connected),sum(q['y'] for q in connected)/len(connected)) if connected else (50,60))
        if role(p) in bypass or role(p) in analog_owner:
            owner,pin=(bypass if role(p) in bypass else analog_owner)[role(p)];o=placed[owner]
            pad=next(t for t in templates[o['footprint']].pads if str(t.number)==pin)
            target=(o['x']+pad.position.X*1.4*(-1 if o['side']=='B' else 1),o['y']+pad.position.Y*1.4)
            if role(p) in bypass and p['side']!=o['side']:
                target=(o['x']+pad.position.X*(-1 if o['side']=='B' else 1),o['y']+pad.position.Y)
        for x,y in sorted(candidates,key=lambda pt:(pt[0]-target[0])**2+(pt[1]-target[1])**2):
            box,pp=geometry(p,x,y)
            if fits(box,pp):p['x']=x;p['y']=y;boxes.append(box);pads.extend(pp);placed[role(p)]=p;done=True;break
        if not done:raise RuntimeError('No placement space for '+p['ref'])

def schematic(parts):
    from schematics import generate
    return generate(parts,OUT)

def main():
    OUT.mkdir(exist_ok=True);LIB.mkdir(exist_ok=True);parts=circuit()
    templates={k:make_footprint(k) for k in {p['footprint'] for p in parts}|{'mount'}}
    for k,fp in templates.items():fp.to_file(str(LIB/f'{k}.kicad_mod'))
    pack_main(parts,templates)
    names=sorted({n for p in parts for n in p['pins'].values() if n});nets={n:Net(i+1,n) for i,n in enumerate(names)}
    paths=schematic(parts)
    for name in ['panel','main']:board([p for p in parts if p['board']==name],name,templates,nets,paths)
    (OUT/'fp-lib-table').write_text('(fp_lib_table (lib (name "ADOLFO")(type "KiCad")(uri "${KIPRJMOD}/ADOLFO.pretty")(options "")(descr "Local candidate footprints")))\n')
    (OUT/'Adolfo-main.kicad_pro').write_text(json.dumps({'meta':{'filename':'Adolfo-main.kicad_pro','version':1}},indent=2)+'\n')
    (OUT/'Adolfo-panel.kicad_pro').write_text(json.dumps({'meta':{'filename':'Adolfo-panel.kicad_pro','version':1}},indent=2)+'\n')
    (OUT/'design.json').write_text(json.dumps(dict(revision='D',status='ENGINEERING_BUILD_PENDING_ROUTING_AND_NATIVE_CHECKS',panel=PANEL,pcb=PCB,ports=PORTS,pins=PINS,rates=RATES,parts=parts,holes=holes(),release_blockers=RELEASE_BLOCKERS,blocking=[*RELEASE_BLOCKERS.values(),'physical assembly verification','electrical and thermal bench qualification','calibration']),indent=2)+'\n',encoding='utf-8')
    with (OUT/'bom.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['Reference','Circuit role','Value / part','Footprint','Board','Side','X','Y','Notes','MPN','Manufacturer','Datasheet']);w.writerows([p[k] for k in ['ref','id','value','footprint','board','side','x','y','note','mpn','manufacturer','datasheet']] for p in parts)
    with (OUT/'panel-holes.csv').open('w',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['Reference','X_mm','Y_mm','Diameter_mm']);w.writerows([p[k] for k in ['ref','x','y','diameter']] for p in holes())
    root=ET.Element('export',version='D');comps=ET.SubElement(root,'components');ns=ET.SubElement(root,'nets')
    for p in parts:
        c=ET.SubElement(comps,'comp',ref=p['ref']);ET.SubElement(c,'value').text=p['value'];ET.SubElement(c,'footprint').text='ADOLFO:'+p['footprint']
    for name in names:
        n=ET.SubElement(ns,'net',name=name,code=str(nets[name].number))
        for p in parts:
            for pin,net in p['pins'].items():
                if net==name:ET.SubElement(n,'node',ref=p['ref'],pin=pin)
    ET.indent(root);ET.ElementTree(root).write(OUT/'Adolfo.net',encoding='utf-8',xml_declaration=True)
    import export_mechanical
    from visuals import render
    render(parts)
    (OUT/'validation.json').write_text(json.dumps({'status':'PENDING_NATIVE_VALIDATION','parts':len(parts)},indent=2)+'\n',encoding='utf-8')
    print(f'Generated {len(parts)} parts, {len(names)} nets. Next: native board preparation, routing and ERC/DRC.')
if __name__=='__main__':main()
