#!/usr/bin/env python3
"""Generate editable KiCad, BOM, netlist, mechanical files and offline views."""
from pathlib import Path
from copy import deepcopy
from collections import defaultdict
from dataclasses import fields, is_dataclass
from uuid import uuid5, NAMESPACE_URL
import csv
import json
import math
import hashlib
import xml.etree.ElementTree as ET

from kiutils.board import Board
from kiutils.footprint import Footprint, Pad, DrillDefinition
from kiutils.items.common import Position as P, Net, Effects, Font, TitleBlock, PageSettings
from kiutils.items.fpitems import FpRect, FpText
from kiutils.items.gritems import GrRect, GrText, GrCircle
from kiutils.schematic import Schematic
from kiutils.utils import sexpr
import ezdxf

from design import PANEL, PCB, COLUMNS, MOUNTS, OLED, RAIL_SLOTS, circuit, holes

HERE = Path(__file__).resolve().parent
OUT = HERE / 'output'
LIB = OUT / 'ADLFO.pretty'
PARTS = circuit()
NET_NAMES = sorted({n for p in PARTS for n in p['pins'].values() if n})
NETS = {n:Net(i+1,n) for i,n in enumerate(NET_NAMES)}

def uid(name): return str(uuid5(NAMESPACE_URL, 'adlfo/rev-a/'+name))
def q(text): return json.dumps(str(text), ensure_ascii=False)
def eff(size=1): return Effects(font=Font(height=size,width=size,thickness=0.15))

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
        fp=Footprint.create_new('ADLFO:'+kind,kind,type='through_hole')
        if kind=='seed':
            # Seed oriented horizontally, USB left before flipping to back.
            for i in range(20):
                fp.pads += [pad(i+1,-24.13+i*2.54,7.62,1.1,1.8),
                            pad(40-i,-24.13+i*2.54,-7.62,1.1,1.8)]
            body(fp,51,18)
        elif kind=='recom':
            fp.pads=[pad(i+1,(i-1)*2.54,0,1.0,1.8) for i in range(3)]
            body(fp,11.6,8.5,0,-2.25)
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
    fp.libId='ADLFO:'+kind
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

def make_board():
    board=Board.create_new()
    board.generator='pcbnew';board.version='20221018'
    board.titleBlock=TitleBlock(title='ADLFO — single PCB placement proposal',revision='A / DRAFT',date='2026-10-21')
    board.general.thickness=PCB['thickness']
    board.nets.extend(NETS.values())
    board.graphicItems.append(GrRect(start=P(PCB['x'],PCB['y']),
        end=P(PCB['x']+PCB['width'],PCB['y']+PCB['height']),layer='Edge.Cuts',width=0.05,tstamp=uid('pcb-outline')))
    for text,x,y in [('ADLFO / REV A',60,39),('PLACEMENT ONLY - NOT FOR FABRICATION',60,117.8)]:
        board.graphicItems.append(GrText(text=text,position=P(x,y),layer='F.SilkS',effects=eff(1),tstamp=uid(text)))
    allparts=PARTS+[dict(ref=f'H{i}',value='M3 spacer',footprint='mount',x=x,y=y,pins={},side='F',group='MECHANICAL') for i,(x,y) in enumerate(MOUNTS,1)]
    templates={kind:make_footprint(kind) for kind in {p['footprint'] for p in allparts}}
    for kind,fp in templates.items():fp.to_file(str(LIB/f'{kind}.kicad_mod'))
    for part in allparts:
        fp=deepcopy(templates[part['footprint']])
        fp.tstamp=uid(part['ref']);fp.path=f'/{uid("schematic")}/{uid(part["ref"])}'
        if part['side']=='B':flip(fp)
        fp.position=P(part['x'],part['y'],0)
        for g in fp.graphicItems:
            if isinstance(g,FpText):g.text=part['ref'] if g.type=='reference' else part['value']
        known={str(p.number) for p in fp.pads if p.number!=''}
        assert set(part['pins'])<=known, (part['ref'],set(part['pins'])-known)
        for p in fp.pads:
            p.tstamp=uid(f'{part["ref"]}/pad/{p.number}/{p.position.X}/{p.position.Y}')
            n=part['pins'].get(str(p.number));p.net=NETS[n] if n else None
        board.footprints.append(fp)
    board.to_file(str(OUT/'ADLFO.kicad_pcb'))
    (OUT/'fp-lib-table').write_text('(fp_lib_table\n  (lib (name "ADLFO")(type "KiCad")(uri "${KIPRJMOD}/ADLFO.pretty")(options "")(descr "Local ADLFO footprints"))\n)\n')
    (OUT/'ADLFO.kicad_pro').write_text(json.dumps({'meta':{'filename':'ADLFO.kicad_pro','version':1},
        'board':{'design_settings':{'rules':{'min_clearance':0.2,'min_track_width':0.25,'min_via_diameter':0.6,'min_through_hole_diameter':0.3}}},
        'net_settings':{'classes':[{'name':'Default','clearance':0.2,'track_width':0.25,'via_diameter':0.6,'via_drill':0.3}], 'meta':{'version':3}}},indent=2)+'\n')
    return board

def make_schematic():
    # Explicit terminal diagrams, grouped by electrical function. Embedded symbols keep it portable.
    sid=uid('schematic')
    defs=[];instances=[];wires=[];labels=[];ncs=[];legacy=[];texts=[]
    cols=8;cell_w=140;row_y=35
    groups=['SYSTEM','CH1','CH2','CH3','CH4']
    for group in groups:
        gp=[p for p in PARTS if p['group']==group]
        texts.append(f'(text {q(group+" / terminal net schematic")} (at 20 {row_y} 0) (effects (font (size 3 3)) (justify left)) (uuid {uid("title"+group)}))')
        row_y+=12
        for start in range(0,len(gp),cols):
            batch=gp[start:start+cols]
            maxh=max(max(12,math.ceil(len(p['pins'])/2)*3.81+4) for p in batch)
            for col,part in enumerate(batch):
                ref=part['ref'];lib='ADLFO:'+ref;name=ref;pinlist=list(part['pins'].items())
                h=max(12,math.ceil(len(pinlist)/2)*3.81+4);bw=25.4
                x=60+col*cell_w;y=row_y+h/2+7
                d=[f'(symbol {q(lib)} (pin_names (offset 1.0)) (in_bom yes) (on_board yes)',
                    f'(property "Reference" {q(ref)} (id 0) (at 0 {h/2+4} 0) (effects (font (size 1.27 1.27))))',
                    f'(property "Value" {q(part["value"])} (id 1) (at 0 {h/2+1.5} 0) (effects (font (size 1.27 1.27))))',
                    f'(symbol {q(name+"_0_1")} (rectangle (start {-bw/2} {h/2}) (end {bw/2} {-h/2}) (stroke (width 0.254) (type default)) (fill (type background))))',
                    f'(symbol {q(name+"_1_1")}']
                half=math.ceil(len(pinlist)/2)
                for i,(num,net) in enumerate(pinlist):
                    left=i<half;px=(-bw/2-5.08) if left else (bw/2+5.08)
                    py=h/2-3.81-(i if left else i-half)*3.81
                    label=num
                    if ref=='U1':label=net or {16:'AUDIO_IN_L',17:'AUDIO_IN_R',18:'AUDIO_OUT_L',19:'AUDIO_OUT_R',21:'3V3_A_NC'}.get(int(num),'NC')
                    if ref=='U2':label={'1':'VDD','2':'SCL','3':'SDA','4':'LDAC','5':'RDY_BSY','6':'VA','7':'VB','8':'VC','9':'VD','10':'VSS'}[num]
                    d.append(f'(pin passive line (at {px} {py} {0 if left else 180}) (length 5.08) (name {q(label)} (effects (font (size 1 1)))) (number {q(num)} (effects (font (size 1 1)))))')
                    ax=x+px;ay=y-py;ex=ax+(-5.08 if left else 5.08)
                    if net:
                        wires.append(f'(wire (pts (xy {ax} {ay}) (xy {ex} {ay})) (stroke (width 0) (type default)) (uuid {uid(ref+num+"wire")}))')
                        labels.append(f'(label {q(net)} (at {ex} {ay} {0 if left else 180}) (effects (font (size 1.0 1.0)) (justify {"left" if left else "right"} bottom)) (uuid {uid(ref+num+"label")}))')
                    else:ncs.append(f'(no_connect (at {ax} {ay}) (uuid {uid(ref+num+"nc")}))')
                d.append('))');defs.append('\n'.join(d))
                fp='ADLFO:'+part['footprint']
                instances.append(f'(symbol (lib_id {q(lib)}) (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (uuid {uid(ref)})\n'
                    f'(property "Reference" {q(ref)} (id 0) (at {x} {y-h/2-4} 0) (effects (font (size 1.27 1.27))))\n'
                    f'(property "Value" {q(part["value"])} (id 1) (at {x} {y-h/2-1.5} 0) (effects (font (size 1.27 1.27))))\n'
                    f'(property "Footprint" {q(fp)} (id 2) (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide)))')
                legacy.append(f'(path "/{uid(ref)}" (reference {q(ref)}) (unit 1) (value {q(part["value"])}) (footprint {q(fp)}))')
            row_y+=maxh+23
        row_y+=12
    assert row_y<810, row_y
    sch='\n'.join(['(kicad_sch (version 20211123) (generator eeschema)',f'(uuid {sid})','(paper "A0")',
        '(title_block (title "ADLFO REV A — electrical placement draft") (rev "A DRAFT") (comment 1 "Terminal diagrams; passive pin types. Full ERC and routing pending."))',
        '(lib_symbols '+ '\n'.join(defs)+')',*texts,*wires,*labels,*ncs,*instances,
        '(sheet_instances (path "/" (page "1")))','(symbol_instances '+ '\n'.join(legacy)+')',')'])
    # Parse and reserialize through KiUtils, not merely text masquerading as CAD.
    obj=Schematic.from_sexpr(sexpr.parse_sexp(sch))
    obj.to_file(str(OUT/'ADLFO.kicad_sch'))
    return obj

def make_exports(board):
    root=ET.Element('export',version='D');design=ET.SubElement(root,'design')
    ET.SubElement(design,'source').text='ADLFO.kicad_sch'
    ET.SubElement(design,'tool').text='ADLFO / KiUtils 1.4.8'
    comps=ET.SubElement(root,'components');nets=ET.SubElement(root,'nets')
    for p in PARTS:
        c=ET.SubElement(comps,'comp',ref=p['ref'])
        ET.SubElement(c,'value').text=p['value'];ET.SubElement(c,'footprint').text='ADLFO:'+p['footprint']
        ET.SubElement(c,'tstamps').text=uid(p['ref'])
    for n in NET_NAMES:
        node=ET.SubElement(nets,'net',code=str(NETS[n].number),name=n)
        for p in PARTS:
            for pin,net in p['pins'].items():
                if net==n:ET.SubElement(node,'node',ref=p['ref'],pin=pin)
    ET.indent(root);ET.ElementTree(root).write(OUT/'ADLFO.net',encoding='utf-8',xml_declaration=True)
    with (OUT/'bom.csv').open('w',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['Reference','Value / candidate','Footprint','Side','Group','Notes'])
        for p in PARTS:w.writerow([p[k] for k in ['ref','value','footprint','side','group']]+[p.get('note','')])
    with (OUT/'placement.csv').open('w',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['Reference','X_panel_mm','Y_panel_mm','Side','Rotation_deg'])
        for p in PARTS:w.writerow([p['ref'],p['x'],p['y'],p['side'],0])
    with (OUT/'panel-holes.csv').open('w',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['Reference','X_from_left_mm','Y_from_top_mm','Diameter_mm','Type'])
        for h in holes():w.writerow([h['ref'],h['x'],h['y'],h['diameter'],h['kind']])
        for i,(x,y) in enumerate(RAIL_SLOTS,1):w.writerow([f'RAIL{i}',x,y,'3.2 x 5.2','horizontal slot'])
        w.writerow(['OLED',OLED['x'],OLED['y'],'27 x 15','rectangle; corner radius 0; verify glass'])
    (OUT/'design.json').write_text(json.dumps(dict(panel=PANEL,pcb=PCB,oled=OLED,mounts=MOUNTS,
        holes=holes(),rail_slots=RAIL_SLOTS,parts=PARTS,status='PLACEMENT_DRAFT_UNROUTED'),indent=2)+'\n')
    (OUT/'source-hashes.json').write_text(json.dumps({str(p.relative_to(HERE.parent.parent)):
        hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE.parent.parent/'DaisyMonoEnvelope'/x for x in ['PanelControls.h','HardwareConfig.h','Mcp4728Protocol.h']]},indent=2)+'\n')

def mechanical():
    doc=ezdxf.new('R2010');doc.units=4;m=doc.modelspace()
    for name,col in [('CUT',1),('DRILL',3),('REFERENCE',8)]:doc.layers.new(name,dxfattribs={'color':col})
    H=PANEL['height'];W=PANEL['width']
    m.add_lwpolyline([(0,0),(W,0),(W,H),(0,H)],close=True,dxfattribs={'layer':'CUT'})
    for h in holes():m.add_circle((h['x'],H-h['y']),h['diameter']/2,dxfattribs={'layer':'DRILL'})
    x=OLED['x']-OLED['width']/2;y=H-OLED['y']-OLED['height']/2
    m.add_lwpolyline([(x,y),(x+OLED['width'],y),(x+OLED['width'],y+OLED['height']),(x,y+OLED['height'])],close=True,dxfattribs={'layer':'CUT'})
    for x,yt in RAIL_SLOTS:
        y=H-yt;r=1.6;d=1.0
        m.add_line((x-d,y-r),(x+d,y-r),dxfattribs={'layer':'CUT'})
        m.add_line((x-d,y+r),(x+d,y+r),dxfattribs={'layer':'CUT'})
        m.add_arc((x+d,y),r,270,90,dxfattribs={'layer':'CUT'})
        m.add_arc((x-d,y),r,90,270,dxfattribs={'layer':'CUT'})
    doc.saveas(OUT/'front-panel.dxf')
    # Parametric mechanical solids, idealized component envelopes (not vendor STEP models).
    scad=f'''// ADLFO review assembly. Coordinates match design.json. NOT machining release.
// Set explode=0 for nominal assembly. Z=0 is PCB front; panel underside=10 mm.
$fn=64; explode=15; panel_gap=10; panel_thickness=2;
module panel() {{
 difference() {{
  cube([{W},{H},panel_thickness]);
'''
    for h in holes():scad+=f'  translate([{h["x"]},{H-h["y"]},-1]) cylinder(h=4,d={h["diameter"]});\n'
    for x,y in RAIL_SLOTS:scad+=f'  hull() {{translate([{x-1},{H-y},-1]) cylinder(h=4,d=3.2); translate([{x+1},{H-y},-1]) cylinder(h=4,d=3.2);}}\n'
    scad+=f'  translate([{OLED["x"]-13.5},{H-OLED["y"]-7.5},-1]) cube([27,15,4]);\n }}\n}}\n'
    scad+=f'color([0.08,0.1,0.12]) translate([0,0,panel_gap+explode]) panel();\n'
    scad+=f'color([0.07,0.32,0.24]) difference() {{translate([{PCB["x"]},{H-PCB["y"]-PCB["height"]},-1.6]) cube([{PCB["width"]},{PCB["height"]},1.6]);\n'
    for x,y in MOUNTS:scad+=f'translate([{x},{H-y},-2]) cylinder(d=3.2,h=3);\n'
    for p in PARTS:
        if p['footprint']=='jack':scad+=f'translate([{p["x"]},{H-p["y"]},-2]) cylinder(d=3,h=3);\n'
    scad+='}\n'
    for x,y in MOUNTS:scad+=f'color("silver") translate([{x},{H-y},0]) difference(){{cylinder(d=5,h=panel_gap);cylinder(d=3.2,h=panel_gap);}}\n'
    for p in PARTS:
        x,y=p['x'],H-p['y'];k=p['footprint']
        if k=='encoder':scad+=f'color("silver") translate([{x},{y},0]) cylinder(d=6,h=20);\n'
        if k=='jack':scad+=f'color("silver") translate([{x},{y},0]) difference(){{cylinder(d=6,h=13);cylinder(d=3.5,h=14);}}\n'
        if k=='button':scad+=f'color("gray") translate([{x},{y},0]) cylinder(d=3.5,h=13);\n'
        if k=='seed':scad+=f'color([0.1,0.2,0.22]) translate([{x-25.5},{y-9},-13]) cube([51,18,1.6]);\n'
    (OUT/'assembly.scad').write_text(scad)

def main():
    OUT.mkdir(exist_ok=True);LIB.mkdir(exist_ok=True)
    board=make_board();make_schematic();make_exports(board);mechanical()
    from visuals import render
    render(board,PARTS,OUT)
    print(f'Generated {len(PARTS)} electrical parts, {len(NETS)} nets. Routing deliberately absent.')

if __name__=='__main__':main()
