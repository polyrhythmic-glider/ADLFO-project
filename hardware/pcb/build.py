#!/usr/bin/env python3
"""Generate rev C: panel PCB and main-board candidate, no routing or Gerbers."""
from pathlib import Path
from copy import deepcopy
from dataclasses import fields,is_dataclass
from uuid import uuid5,NAMESPACE_URL
import csv,json,math,hashlib,xml.etree.ElementTree as ET
from kiutils.board import Board
from kiutils.footprint import Footprint,Pad,DrillDefinition
from kiutils.items.common import Position as P,Net,Effects,Font,TitleBlock
from kiutils.items.fpitems import FpRect,FpText
from kiutils.items.gritems import GrRect,GrText
from kiutils.schematic import Schematic
from kiutils.utils import sexpr
from design import PANEL,PCB,COLUMNS,MOUNTS,OLED,RAIL_SLOTS,PORTS,PINS,RATES,INTERCONNECT,circuit,holes
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
        offset={'encoder':(7.5,2.5),'button':(3.25,2.25),'idc10':(1.27,5.08)}.get(kind,(0,0))
        for p in positions(fp.graphicItems+fp.pads):
            p.X=round(p.X-offset[0],5);p.Y=round(p.Y-offset[1],5)
        if kind=='button': fp.description='6x6 mm tact geometry; 13 mm actuator candidate (verify actual part)'
        if kind=='jack': fp.pads.append(npth(0,0,3))
    else:
        fp=Footprint.create_new('ADOLFO:'+kind,kind,type='through_hole')
        if kind=='seed':
            # Seed oriented horizontally, USB left before flipping to back.
            for i in range(20):
                fp.pads += [pad(i+1,-24.13+i*2.54,7.62,1.1,1.8),
                            pad(40-i,-24.13+i*2.54,-7.62,1.1,1.8)]
            body(fp,51,18)
        elif kind=='header40':
            for i in range(20):
                fp.pads += [pad(2*i+1,-1.27,-24.13+i*2.54),pad(2*i+2,1.27,-24.13+i*2.54)]
            body(fp,5.08,50.8)
        elif kind=='power_module':
            fp.pads=[pad(1,-2.54,0),pad(2,0,0),pad(3,2.54,0)]
            body(fp,18,14)
            fp.description='UNSELECTED converter envelope only: MUST replace footprint before release.'
        elif kind=='oled':
            fp.pads=[pad(i+1,(i-1.5)*2.54,0) for i in range(4)]
            body(fp,10.16,2.54)
        elif kind=='testpoint':
            fp.pads=[pad(1,0,0,0.8,2.0)]
        elif kind=='mount':
            fp.pads=[npth(0,0,3.2)]
            body(fp,6,6)
            fp.attributes.excludeFromBom=True
        else: raise ValueError(kind)
    fp.libId='ADOLFO:'+kind
    fp.version='20211014';fp.generator='kiutils'
    fp.models=[]  # No broken system-library model references; assembly viewer is explicit.
    fp.position=P(0,0,0);fp.tstamp=None
    # Remove inherited labels; compact labels generated consistently for this board.
    fp.graphicItems=[g for g in fp.graphicItems if not isinstance(g,FpText)]
    for typ,y,layer in [('reference',-2.6,'F.SilkS'),('value',2.6,'F.Fab')]:
        fp.graphicItems.append(FpText(type=typ,text='REF**' if typ=='reference' else kind,
            position=P(0,y),layer=layer,effects=eff(0.75)))
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

def board(parts,name,templates,nets):
    b=Board.create_new();b.version='20221018';b.generator='pcbnew'
    b.titleBlock=TitleBlock(title='Adolfo universal / '+name,revision='C CONCEPT - NOT FOR FABRICATION',date='2026-10-24')
    b.general.thickness=1.6;b.nets=list(nets.values())
    b.graphicItems.append(GrRect(start=P(PCB['x'],PCB['y']),end=P(PCB['x']+PCB['width'],PCB['y']+PCB['height']),layer='Edge.Cuts',width=.05,tstamp=uid(name+'edge')))
    for part in parts:
        fp=deepcopy(templates[part['footprint']]);fp.tstamp=uid(part['ref']);fp.path=f'/{uid("schematic")}/{uid(part["ref"])}'
        if part['side']=='B':flip(fp)
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
        fp=deepcopy(templates['mount']);fp.position=P(x,y);fp.tstamp=uid(name+f'H{i}');b.footprints.append(fp)
    b.to_file(str(OUT/f'Adolfo-{name}.kicad_pcb'));return b

def pack_main(parts,templates):
    """Shelf search for review only; electrical locality and routing are not optimized."""
    boxes=[];pads=[]
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
    fixed=[p for p in main if p['ref'] in ['U1','JM','JPOWER']]
    for p in fixed:
        box,pp=geometry(p,p['x'],p['y']);assert fits(box,pp),p['ref'];boxes.append(box);pads.extend(pp)
    def area(p):
        a,b,c,d=bounds(templates[p['footprint']]);return (c-a)*(d-b)
    for p in sorted([p for p in main if p not in fixed],key=area,reverse=True):
        done=False
        for y in range(11,118):
            for x in range(5,97):
                box,pp=geometry(p,x,y)
                if fits(box,pp):p['x']=x;p['y']=y;boxes.append(box);pads.extend(pp);done=True;break
            if done:break
        if not done:raise RuntimeError('No placement space for '+p['ref'])

def schematic(parts):
    # Embedded terminal symbols: numbered real pins, passive types explicitly NOT full ERC.
    defs=[];instances=[];wires=[];labels=[];ncs=[];legacy=[]
    cols=10;cellw=110;row=25
    for start in range(0,len(parts),cols):
        batch=parts[start:start+cols];maxh=max(max(12,math.ceil(len(p['pins'])/2)*3.81+4) for p in batch)
        for col,part in enumerate(batch):
            ref=part['ref'];lib='ADOLFO:'+ref;pins=list(part['pins'].items());h=max(12,math.ceil(len(pins)/2)*3.81+4);bw=25.4
            x=60+col*cellw;y=row+h/2+7
            d=[f'(symbol {q(lib)} (pin_names (offset 1)) (in_bom yes) (on_board yes)',f'(property "Reference" {q(ref)} (id 0) (at 0 {h/2+4} 0) (effects (font (size 1.27 1.27))))',f'(property "Value" {q(part["value"])} (id 1) (at 0 {h/2+1.5} 0) (effects (font (size 1.27 1.27))))',f'(symbol {q(ref+"_0_1")} (rectangle (start {-bw/2} {h/2}) (end {bw/2} {-h/2}) (stroke (width .254) (type default)) (fill (type background))))',f'(symbol {q(ref+"_1_1")}']
            half=math.ceil(len(pins)/2)
            for i,(num,net) in enumerate(pins):
                left=i<half;px=-bw/2-5.08 if left else bw/2+5.08;py=h/2-3.81-(i if left else i-half)*3.81
                d.append(f'(pin passive line (at {px} {py} {0 if left else 180}) (length 5.08) (name {q(net or "NC")} (effects (font (size 1 1)))) (number {q(num)} (effects (font (size 1 1)))))')
                ax=x+px;ay=y-py;ex=ax+(-5.08 if left else 5.08)
                if net:
                    wires.append(f'(wire (pts (xy {ax} {ay}) (xy {ex} {ay})) (stroke (width 0) (type default)) (uuid {uid(ref+num+"wire")}))')
                    labels.append(f'(label {q(net)} (at {ex} {ay} {0 if left else 180}) (effects (font (size 1 1)) (justify {"left" if left else "right"} bottom)) (uuid {uid(ref+num+"label")}))')
                else:ncs.append(f'(no_connect (at {ax} {ay}) (uuid {uid(ref+num+"nc")}))')
            d.append('))');defs.append('\n'.join(d));fp='ADOLFO:'+part['footprint']
            instances.append(f'(symbol (lib_id {q(lib)}) (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (uuid {uid(ref)}) (property "Reference" {q(ref)} (id 0) (at {x} {y-h/2-4} 0) (effects (font (size 1.27 1.27)))) (property "Value" {q(part["value"])} (id 1) (at {x} {y-h/2-1.5} 0) (effects (font (size 1.27 1.27)))) (property "Footprint" {q(fp)} (id 2) (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide)))')
            legacy.append(f'(path "/{uid(ref)}" (reference {q(ref)}) (unit 1) (value {q(part["value"])}) (footprint {q(fp)}))')
        row+=maxh+20
    # A0 portrait-like custom sheet when many terminals are present.
    raw='\n'.join(['(kicad_sch (version 20211123) (generator eeschema)',f'(uuid {uid("schematic")})',f'(paper "User" 1189 {max(841,math.ceil(row+30))})','(title_block (title "Adolfo universal C - terminal candidate, NOT full electrical ERC") (rev "C CONCEPT"))','(lib_symbols '+'\n'.join(defs)+')',*wires,*labels,*ncs,*instances,'(sheet_instances (path "/" (page "1")))','(symbol_instances '+'\n'.join(legacy)+')',')'])
    obj=Schematic.from_sexpr(sexpr.parse_sexp(raw));obj.to_file(str(OUT/'Adolfo.kicad_sch'))

def main():
    OUT.mkdir(exist_ok=True);LIB.mkdir(exist_ok=True);parts=circuit()
    templates={k:make_footprint(k) for k in {p['footprint'] for p in parts}|{'mount'}}
    for k,fp in templates.items():fp.to_file(str(LIB/f'{k}.kicad_mod'))
    pack_main(parts,templates)
    names=sorted({n for p in parts for n in p['pins'].values() if n});nets={n:Net(i+1,n) for i,n in enumerate(names)}
    for name in ['panel','main']:board([p for p in parts if p['board']==name],name,templates,nets)
    schematic(parts)
    (OUT/'fp-lib-table').write_text('(fp_lib_table (lib (name "ADOLFO")(type "KiCad")(uri "${KIPRJMOD}/ADOLFO.pretty")(options "")(descr "Local candidate footprints")))\n')
    (OUT/'Adolfo.kicad_pro').write_text(json.dumps({'meta':{'filename':'Adolfo.kicad_pro','version':1}},indent=2)+'\n')
    (OUT/'design.json').write_text(json.dumps(dict(revision='C',status='CONCEPT_UNROUTED_NOT_FOR_FABRICATION',panel=PANEL,pcb=PCB,ports=PORTS,pins=PINS,rates=RATES,parts=parts,holes=holes(),blocking=['analog antialias/reconstruction filters','converter selection and supply budget','SPI8 DMA scheduling and clock proof','mechanical stack','native ERC/DRC','routing and bench tests']),indent=2)+'\n')
    with (OUT/'bom.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['Reference','Candidate value','Footprint','Board','X','Y','Notes']);w.writerows([p[k] for k in ['ref','value','footprint','board','x','y','note']] for p in parts)
    with (OUT/'panel-holes.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['Reference','X_mm','Y_mm','Diameter_mm']);w.writerows([p[k] for k in ['ref','x','y','diameter']] for p in holes())
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
    print(f'Generated {len(parts)} candidate parts, {len(names)} nets; two unrouted boards. Filters and driver proof OPEN.')
if __name__=='__main__':main()
