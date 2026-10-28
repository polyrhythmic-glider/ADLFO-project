"""Static design checks. PASS is not an electrical/production release."""
from pathlib import Path
from itertools import combinations
import json,math,xml.etree.ElementTree as ET
from kiutils.board import Board
from kiutils.schematic import Schematic
from design import PANEL,PCB,PINS,PORTS,INTERCONNECT,circuit,holes
HERE=Path(__file__).parent;OUT=HERE/'output';checks=[]
def check(ok,msg):
 if not ok:raise AssertionError(msg)
 checks.append(msg)
def ref(fp):return next(g.text for g in fp.graphicItems if getattr(g,'type',None)=='reference')
d=json.loads((OUT/'design.json').read_text());parts=d['parts'];byref={p['ref']:p for p in parts}
check(len(byref)==len(parts),'Unique part references')
check({p['ref']:p['pins'] for p in parts}=={p['ref']:p['pins'] for p in circuit()},'Export matches current electrical source')
check(len(PORTS)==12 and len(PINS)==len(set(PINS.values())),'12 ports and no GPIO conflicts')
check(PANEL['hp']==20 and PANEL['width']<=101.6,'20 HP envelope')
check([p['adc'] for p in PORTS if 'adc' in p]==list(range(4))+list(range(4,8)),'Eight unique ADC channel assignments')
check([p['dac'] for p in PORTS if 'dac' in p]==list(range(4))+list(range(4,8)),'Eight unique DAC channel assignments')
check(byref['JM']['pins']==byref['JP']['pins']=={str(k):v for k,v in INTERCONNECT.items()},'Stack connector pin agreement')
check(all(p['pins']['TN'] is None for p in parts if p['footprint']=='jack'),'All jack normals open including bidirectional CTRL')
check('DAC8568B' in byref['U3']['value'],'DAC gain-one midscale-reset B grade selected')
check(byref['U3']['pins']=={'1':'DAC_LDAC_5V','2':'DAC_SYNC_5V','3':'+5A','4':'DAC1','5':'DAC3','6':'DAC5','7':'DAC7','8':'REF2V5','9':'DAC_CLR_5V','10':'DAC8','11':'DAC6','12':'DAC4','13':'DAC2','14':'GND','15':'DAC_MOSI_5V','16':'DAC_SCK_5V'},'DAC8568 TSSOP16 pinout and shifted logic')
check(byref['U2']['pins']['23']=='+3V3' and all(byref['U2']['pins'][str(i)]=='+5A' for i in [1,37,38,48]),'ADC VDRIVE 3.3 V, analog supply 5 V')
for i in range(8):check(byref['U2']['pins'][str(49+2*i)]==f'ADC_IN{i+1}' and byref['U2']['pins'][str(50+2*i)]=='GND',f'ADC bipolar single-ended channel {i+1}')
for bank in range(2):
 p=byref[f'U{7+bank}']['pins']
 for j,(ctl,drain,source) in enumerate([(1,2,3),(16,15,14),(9,10,11),(8,7,6)]):
  n=bank*4+j+1;port=f'OUT{j+1}' if bank==0 else f'CTRL{j+1}'
  check(p[str(source)]==port and p[str(drain)]==f'DRIVE{n}' and p[str(ctl)]==f'SW_ON{n}',f'Protected source faces {port}, driver faces drain')
check(byref['RPERMIT']['pins']=={'1':'OUTPUT_PERMIT','2':'GND'},'Output permit external pull-down')
check(all(byref[f'RE{i}']['pins']=={'1':f'SW_ON{i}','2':'GND'} for i in range(1,9)),'All output switches default disconnected')
check(byref['JPOWER']['pins']=={'1':'-12_IN','2':'-12_IN','3':'GND','4':'GND','5':'GND','6':'GND','7':'GND','8':'GND','9':'+12_IN','10':'+12_IN'},'Eurorack IDC10 polarity')
check(byref['U4']['pins']['17']=='ENC1_CLICK' and byref['U4']['pins']['28']=='REQ4','MCP23017 click/request mapping')
# Independently parse KiCad boards, recover pad nets and test copper pad separation.
expected={(p['ref'],pin):net for p in parts for pin,net in p['pins'].items()};found={}
for name in ['main','panel']:
 b=Board.from_file(str(OUT/f'Adolfo-{name}.kicad_pcb'));pads=[];boxes=[]
 check(not b.traceItems,f'{name}: no false claim of routed tracks')
 for fp in b.footprints:
  r=ref(fp)
  if r not in byref:continue
  check(byref[r]['board']==name,f'{r} belongs to correct board')
  for p in fp.pads:
   if p.number:
    key=(r,str(p.number));net=p.net.name if p.net else None
    check(key not in found or found[key]==net,f'{r}.{p.number}: repeated pad net agrees');found[key]=net
   x=fp.position.X+p.position.X;y=fp.position.Y+p.position.Y
   check(x-p.size.X/2>=PCB['x']+.2 and x+p.size.X/2<=PCB['x']+PCB['width']-.2 and y-p.size.Y/2>=PCB['y']+.2 and y+p.size.Y/2<=PCB['y']+PCB['height']-.2,f'{r}.{p.number}: pad inside board')
   pads.append((r,p,x,y,fp.layer))
  pts=[]
  for g in fp.graphicItems:
   if getattr(g,'layer','').endswith('CrtYd'):
    for k in ['start','end']:
     if hasattr(g,k):
      z=getattr(g,k);pts.append((fp.position.X+z.X,fp.position.Y+z.Y))
  if pts:boxes.append((r,fp.layer,min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)))
 clashes=[]
 for (r,p,x,y,l),(s,q,u,v,m) in combinations(pads,2):
  if r==s or (p.type=='smd' and q.type=='smd' and l!=m):continue
  if p.net and q.net and p.net.name==q.net.name:continue
  if abs(x-u)<(p.size.X+q.size.X)/2+.2 and abs(y-v)<(p.size.Y+q.size.Y)/2+.2:
   if p.shape==q.shape=='circle' and math.hypot(x-u,y-v)>(p.size.X+q.size.X)/2+.2:continue
   clashes.append(f'{r}.{p.number}/{s}.{q.number}')
 check(not clashes,f'{name}: pad-clearance screening: '+','.join(clashes))
 overlaps=[]
 for a,b in combinations(boxes,2):
  if a[1]==b[1] and min(a[4],b[4])-max(a[2],b[2])>.01 and min(a[5],b[5])-max(a[3],b[3])>.01:overlaps.append(a[0]+'/'+b[0])
 check(not overlaps,f'{name}: same-side courtyards do not overlap: '+','.join(overlaps))
check(found==expected,'All PCB pads agree with electrical source')
x=ET.parse(OUT/'Adolfo.net');xmlnets={(n.attrib['ref'],n.attrib['pin']):net.attrib['name'] for net in x.findall('./nets/net') for n in net}
check(xmlnets=={k:v for k,v in expected.items() if v},'XML netlist equivalent')
# Reconstruct the schematic wire/label graph rather than only counting symbols.
sch=Schematic.from_file(str(OUT/'Adolfo.kicad_sch'));parent={}
def xy(p):return round(p.X,5),round(p.Y,5)
def root(p):
 parent.setdefault(p,p)
 if parent[p]!=p:parent[p]=root(parent[p])
 return parent[p]
for w in sch.graphicalItems:
 if getattr(w,'type',None)=='wire':
  a,b=map(xy,w.points);parent[root(a)]=root(b)
labels={}
for l in sch.labels:
 pos=root(xy(l.position));check(pos not in labels or labels[pos]==l.text,'No conflicting schematic labels');labels[pos]=l.text
libs={s.libId:s for s in sch.libSymbols};snets={}
for s in sch.schematicSymbols:
 r=next(p.value for p in s.properties if p.key=='Reference')
 for u in libs[s.libId].units:
  for pin in u.pins:
   pos=(round(s.position.X+pin.position.X,5),round(s.position.Y-pin.position.Y,5));snets[(r,str(pin.number))]=labels.get(root(pos))
check(snets==expected,'Schematic terminal graph equals source and boards')
for h in holes():
 if h['kind']=='mount':continue
 refname=('E'+h['ref'][3:]) if h['kind']=='ENC' else ('K'+h['ref'][3:]) if h['kind']=='KEY' else next(p['ref'] for p in parts if p['board']=='panel' and p['value'].startswith(h['ref']+' '))
 p=byref[refname];check((p['x'],p['y'])==(h['x'],h['y']),f'{h["ref"]} front/PCB alignment')
r=d['rates'];adc_us=r['adc_bits_per_frame']/r['adc_spi_target_hz']*1e6;dac_us=8*r['dac_bits_per_word']/r['dac_spi_target_hz']*1e6
check(adc_us<1e6/r['adc_hz'] and dac_us<1e6/r['audio_hz'],'Raw SPI payload fits theoretical frame period; overhead proof still open')
report=dict(status='PASS_STATIC_ONLY_NOT_RELEASED',checks=len(checks),parts=len(parts),adc_payload_us=adc_us,dac_payload_us=dac_us,blocking=d['blocking'],not_verified=['analog audio filters','drivers/DMA/clock','native ERC/DRC clean','power and thermal','height stack','real hardware','V/oct accuracy'],details=checks)
(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'PASS {len(checks)} static checks; {len(parts)} candidate parts. Hardware release remains blocked.')
