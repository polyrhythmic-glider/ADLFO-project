"""Design consistency checks. This does not replace KiCad ERC/DRC or a bench test."""
from collections import defaultdict
from itertools import combinations
from pathlib import Path
import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET

from kiutils.board import Board
from kiutils.schematic import Schematic
from kiutils.items.common import Position
import ezdxf
from design import PANEL, PCB, COLUMNS, MOUNTS, OLED, ENCODERS, BUTTONS, TRIGGERS, CV, circuit, holes

HERE=Path(__file__).resolve().parent;OUT=HERE/'output'
parts=circuit();byref={p['ref']:p for p in parts}
results=[]
def check(condition,message):
    if not condition:raise AssertionError(message)
    results.append(message)
def ref(fp):return next(x.text for x in fp.graphicItems if getattr(x,'type',None)=='reference')
def at(p):return (round(p.X,5),round(p.Y,5))

board=Board.from_file(str(OUT/'ADLFO.kicad_pcb'))
sch=Schematic.from_file(str(OUT/'ADLFO.kicad_sch'))
check(len(board.footprints)==len(parts)+len(MOUNTS),'KiCad board round trip: all electrical parts and 4 spacers present')
check(len(sch.schematicSymbols)==len(parts),'KiCad schematic round trip: all electrical parts present')
check(not board.traceItems,'Routing status truthful: no copper tracks; board is a placement draft')

# Connect schematic wire ends to labels, and recover terminal nets from embedded symbols.
parent={}
def root(p):
    parent.setdefault(p,p)
    if parent[p]!=p:parent[p]=root(parent[p])
    return parent[p]
for wire in sch.graphicalItems:
    if getattr(wire,'type',None)=='wire':
        a,b=map(at,wire.points);parent[root(a)]=root(b)
labels={}
for label in sch.labels:
    p=root(at(label.position))
    check(p not in labels or labels[p]==label.text,f'Schematic label {label.text}: no conflicting name')
    labels[p]=label.text
lib={s.libId:s for s in sch.libSymbols}
sch_nets={}
for s in sch.schematicSymbols:
    sr=next(p.value for p in s.properties if p.key=='Reference')
    for u in lib[s.libId].units:
        for pin in u.pins:
            xy=(round(s.position.X+pin.position.X,5),round(s.position.Y-pin.position.Y,5))
            sch_nets[(sr,str(pin.number))]=labels.get(root(xy))
expected={(p['ref'],pin):n for p in parts for pin,n in p['pins'].items()}
check(sch_nets==expected,'All schematic terminal nets match the electrical source, including NC pins')
pcb_nets={}
for fp in board.footprints:
    r=ref(fp)
    if r not in byref:continue
    for p in fp.pads:
        if p.number!='':
            key=(r,str(p.number));net=p.net.name if p.net else None
            check(key not in pcb_nets or pcb_nets[key]==net,f'Duplicate pad net coherent: {r}.{p.number}')
            pcb_nets[key]=net
check(pcb_nets==expected,'Every electrical KiCad pad matches the schematic and source net')
xml=ET.parse(OUT/'ADLFO.net')
xmlnets={(n.attrib['ref'],n.attrib['pin']):net.attrib['name'] for net in xml.findall('./nets/net') for n in net}
check(xmlnets=={k:v for k,v in expected.items() if v},'Exported netlist matches all connected schematic and PCB pins')

# Verify baseline firmware pin assignments, without enabling unfinished inputs.
firmware=(HERE.parent.parent/'DaisyMonoEnvelope'/'PanelControls.h').read_text()
rows=re.findall(r'\{daisy::seed::D(\d+), daisy::seed::D(\d+), daisy::seed::D(\d+), daisy::seed::D(\d+)\}',firmware)
check([tuple(map(int,r)) for r in rows]==[e+(b,) for e,b in zip(ENCODERS,BUTTONS)],'Encoder/button assignments match existing firmware (including B1/B2 swap)')
used=[d for row in ENCODERS for d in row]+BUTTONS+TRIGGERS+CV+[11,12]
check(len(used)==len(set(used)),'26 assigned GPIOs are unique; no I2C/control/input conflicts')
check(CV==[15,16,17,18],'CV proposal uses Daisy ADC-capable A0–A3')
check(all(byref[f'J{1+3*i}']['pins']['TN']=='GND' and byref[f'J{2+3*i}']['pins']['TN']=='GND' for i in range(4)),'All unused TRIG/CV jack normals connect to ground')
check(byref['U2']['pins']=={'1':'+3V3','2':'D11','3':'D12','4':'GND','5':None,'6':'DAC1','7':'DAC2','8':'DAC3','9':'DAC4','10':'GND'},'MCP4728 pin map matches Microchip table 3-1')
check(byref['D1']['pins']=={'1':'+12VA','2':'+12V_IN'} and byref['D2']['pins']=={'1':'-12V_IN','2':'-12VA'},'Reverse-polarity series diodes have opposite orientation on positive/negative rails')
check(byref['D3']['pins']=={'1':'+5V_SEED','2':'+5V_REG'},'5 V series diode blocks current from Seed toward the converter')

# Pad clearance screening across sides: through-hole pads occupy both copper layers.
allpads=[]
for fp in board.footprints:
    for p in fp.pads:
        x=fp.position.X+p.position.X;y=fp.position.Y+p.position.Y
        check(x-p.size.X/2>=PCB['x'] and x+p.size.X/2<=PCB['x']+PCB['width'] and
              y-p.size.Y/2>=PCB['y'] and y+p.size.Y/2<=PCB['y']+PCB['height'],f'Pad inside board outline: {ref(fp)}.{p.number}')
        allpads.append((fp,p,x,y))
clashes=[]
for (f,p,x,y),(g,q,u,v) in combinations(allpads,2):
    if f.tstamp==g.tstamp:continue
    if p.type=='smd' and q.type=='smd' and f.layer!=g.layer:continue
    if p.net and q.net and p.net.name==q.net.name:continue
    dx=abs(x-u)-(p.size.X+q.size.X)/2;dy=abs(y-v)-(p.size.Y+q.size.Y)/2
    if dx<0.2 and dy<0.2:
        if p.shape=='circle' and q.shape=='circle' and math.hypot(x-u,y-v)>(p.size.X+q.size.X)/2+.2:continue
        clashes.append(f'{ref(f)}.{p.number}/{ref(g)}.{q.number}')
check(not clashes,'0 pad overlap/clearance candidates at 0.20 mm: '+', '.join(clashes))
boxes=[]
for fp in board.footprints:
    pts=[]
    for g in fp.graphicItems:
        if getattr(g,'layer','').endswith('CrtYd'):
            for name in ('start','end'):
                if hasattr(g,name):
                    p=getattr(g,name);pts.append((fp.position.X+p.X,fp.position.Y+p.Y))
    if pts:boxes.append((ref(fp),fp.layer,min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)))
clashes=[]
for a,b in combinations(boxes,2):
    if a[1]==b[1] and min(a[4],b[4])-max(a[2],b[2])>.01 and min(a[5],b[5])-max(a[3],b[3])>.01:
        clashes.append(a[0]+'/'+b[0])
check(not clashes,'0 same-side courtyard bounding-box overlaps: '+', '.join(clashes))
for i,x in enumerate(COLUMNS,1):
    for typ,part in [('encoder',f'ENC{i}'),('button',f'SW{i}'),('trig',f'J{3*i-2}'),('cv',f'J{3*i-1}'),('out',f'J{3*i}')]:
        h=next(h for h in holes() if h['ref']==f'{typ.upper()}{i}')
        p=byref[part];check((h['x'],h['y'])==(p['x'],p['y']),f'Panel/PCB center alignment: {part}')
for a,b in combinations(holes(),2):
    check(math.hypot(a['x']-b['x'],a['y']-b['y'])>(a['diameter']+b['diameter'])/2+1,
          f'Panel apertures separated: {a["ref"]}/{b["ref"]}')
check(min(COLUMNS[i+1]-COLUMNS[i] for i in range(3))-16==10,'16 mm knobs have 10 mm horizontal edge-to-edge clearance')
dxf=ezdxf.readfile(OUT/'front-panel.dxf')
check(dxf.units==4,'DXF units are millimeters')
check(len(dxf.modelspace().query('CIRCLE'))==24,'DXF contains 20 control/jack holes + 4 spacer holes')
audit=dxf.audit();check(not audit.errors,'DXF audit passes')
svg=ET.parse(OUT/'panel-drilling-1to1.svg').getroot()
check(svg.attrib['width']=='121.6mm' and svg.attrib['height']=='128.5mm','Printable SVG has physical 1:1 dimensions')
gain=1+15000/10000;adc10=10*33000/133000
check(gain==2.5 and 2.48<adc10<2.49,'Nominal calculations: output gain 2.5; 10 V CV -> 2.4812 V at ADC')
report={'status':'PASS_LIMITED_STATIC_CHECKS','parts':len(parts),'nets':len(board.nets)-1,
    'checks_passed':len(results),'scope':['KiUtils parsing','source/schematic/netlist/PCB connectivity equivalence',
    'existing firmware GPIO mapping','pad clearance screening','panel alignment','DXF audit','physical SVG scale'],
    'not_verified':['native KiCad ERC/DRC','routing (absent)','component body/height tolerance stack',
    'electrical simulation','power-up/shutdown behavior','real hardware measurements'],
    'nominal':{'cv_adc_at_10V':adc10,'cv_fullscale_fraction':adc10/3.3,'output_gain':gain,'out_at_100k_load':5*100000/102200},
    'details':results}
(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'PASS: {len(results)} static checks; {len(parts)} parts; {len(board.nets)-1} nets. Native ERC/DRC and routing NOT performed.')
