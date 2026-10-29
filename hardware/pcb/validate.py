"""Cross-check source, compiled schematic, native board audit and fresh ERC/DRC."""
from pathlib import Path
import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from design import PANEL, OLED, PINS, PORTS, INTERCONNECT, RELEASE_BLOCKERS, circuit
from build import placement_constraints
import analog_check

OUT=Path(__file__).parent/'output'
checks=[]


def check(ok,message):
    if not ok:raise AssertionError(message)
    checks.append(message)


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    design=json.loads((OUT/'design.json').read_text(encoding='utf-8'))
    parts=design['parts'];source=circuit()
    signature=lambda ps:{p['ref']:{k:p[k] for k in ('id','value','footprint','pins','board','side','mpn','manufacturer','datasheet')} for p in ps}
    check(signature(parts)==signature(source),'Export matches current electrical source and packages')
    byid={p['id']:p for p in parts};byref={p['ref']:p for p in parts}
    check(len(byref)==len(byid)==len(parts),'Unique references and circuit roles')
    check(all(re.fullmatch(r'[A-Za-z]+[0-9]+',r) for r in byref),'Native KiCad reference annotation')
    check(PANEL['hp']==20 and PANEL['width']<=101.6,'20 HP panel envelope')
    check(OLED['x']==PANEL['width']/2 and all(p['x']==OLED['x'] and p['y']==OLED['header_y'] for ps in (parts,source) for p in ps if p['id']=='J14'),'OLED window and module centered on the panel')
    check(len(PORTS)==12 and len(PINS)==len(set(PINS.values())),'Twelve ports; no GPIO conflicts')
    check([p['adc'] for p in PORTS if 'adc' in p]==list(range(8)),'Eight distinct ADC channels')
    check([p['dac'] for p in PORTS if 'dac' in p]==list(range(8)),'Eight distinct DAC channels')
    pins=lambda role:byid[role]['pins']
    check(pins('JM')==pins('JP')=={str(k):v for k,v in INTERCONNECT.items()},'All forty interconnect signals agree')
    check(all(p['pins']['TN']==('GND' if p['pins']['T'].startswith('IN') else None) for p in parts if p['footprint']=='jack'),'Fixed input normals grounded; CTRL/OUT normals open')
    check(byid['U16']['value']=='SN74HCS74DR','Schmitt-input fault latch tolerates open-drain reset edges')
    check(all(p['mpn']=='CRCW20101K00FKEFHP' and p['value']=='1k 1W 1%' for p in parts if p['footprint']=='r2010'),'All sixteen jack protection resistors specified for 1 W')
    check('DAC8568B' in byid['U3']['value'] and byid['U3']['footprint']=='tssop16','Gain-one midscale-reset DAC8568B')
    check(pins('U3')=={'1':'DAC_LDAC_5V','2':'DAC_SYNC_5V','3':'+5A','4':'DAC1','5':'DAC3','6':'DAC5','7':'DAC7','8':'REF2V5','9':'DAC_CLR_5V','10':'DAC8','11':'DAC6','12':'DAC4','13':'DAC2','14':'GND','15':'DAC_MOSI_5V','16':'DAC_SCK_5V'},'DAC pinout and shifted 5 V logic')
    check(byid['U4']['footprint']=='soic28' and all(pins('U4')[str(k)]==v for k,v in {9:'+3V3',10:'GND',12:'I2C_SCL',13:'I2C_SDA',8:'REQ7',28:'REQ8',21:'ENC1_CLICK',24:'ENC4_CLICK'}.items()),'MCP23017 SOIC pinout; GPA7/GPB7 outputs only')
    check(pins('U17')=={'1':'SAFE_CLEAR_N','2':'GND','3':'+3V3','4':'WATCHDOG','5':'+3V3'},'TPS3828 watchdog pinout')
    check(pins('U18')=={'1':'SAFE_CLEAR_N','2':'GND','3':'+3V3','4':'RESET_DELAY','5':'SENSE_5A','6':'+3V3'},'TPS3808 supply monitor pinout')
    check(all(pins('U16')[str(k)]==v for k,v in {1:'SAFE_CLEAR_N',2:'+3V3',3:'OUTPUT_PERMIT',4:'+3V3',5:'SAFE_LATCH'}.items()),'Fault latch needs a fresh permit edge')
    check(all(pins('U20')[str(k)]==v for k,v in {1:'SAFE_LATCH',2:'OUTPUT_PERMIT',3:'GND',4:'SAFE_PERMIT',5:'+3V3'}.items()),'Permit and fault latch qualify output enables')
    check(all(pins(u)[str(k)]=='SAFE_PERMIT' for u in ('U5','U6') for k in (2,5,10,13)),'All channel gates use qualified permit')
    check(pins('RPERMIT')=={'1':'OUTPUT_PERMIT','2':'GND'},'Permit defaults low')
    check(all(pins(f'RE{n}')=={'1':f'SW_ON{n}','2':'GND'} for n in range(1,9)),'All output switches default disconnected')
    check('R-78E5.0-1.0' in byid['UREG']['value'] and byid['UREG']['footprint']=='recom','Exact 1 A regulator and footprint')
    check(pins('JPOWER')=={'1':'-12_IN','2':'-12_IN','3':'GND','4':'GND','5':'GND','6':'GND','7':'GND','8':'GND','9':'+12_IN','10':'+12_IN'},'Eurorack IDC10 polarity')
    check(pins('U2')['23']=='+3V3' and all(pins('U2')[str(n)]=='+5A' for n in (1,37,38,48)),'ADC supply and logic domains')
    for n in range(1,9):
        check(pins('U2')[str(47+2*n)]==f'ADC_IN{n}' and pins('U2')[str(48+2*n)]=='GND',f'ADC input pair {n}')
    for bank in range(2):
        for j,(ctl,drain,src) in enumerate(((1,2,3),(16,15,14),(9,10,11),(8,7,6))):
            n=bank*4+j+1;port=f'{"OUT" if bank==0 else "CTRL"}{j+1}'
            p=pins(f'U{7+bank}')
            check(p[str(src)]==port and p[str(drain)]==f'DRIVE{n}' and p[str(ctl)]==f'SW_ON{n}' and p['12']=='SAFE_CLEAR_N',f'Protected output {n}: source faces jack')
            p=pins(f'U{14+bank}')
            check(p[str(src)]==f'INPUT_LIMIT{n}' and p[str(drain)]==f'PROTECTED{n}' and p['12']=='SAFE_CLEAR_N',f'Protected input {n}: source faces jack')
    check(PINS['WATCHDOG']==24 and PINS['FAULT_N']==25 and PINS['OLED_RESET']==26,'Dedicated safety and OLED GPIO')

    metrics=json.loads((OUT/'board-metrics.json').read_text(encoding='utf-8'))
    padmaps={}
    for name in ('main','panel'):
        data=metrics[name];board=OUT/f'Adolfo-{name}.kicad_pcb'
        check(data['sha256']==digest(board),f'{name}: audit matches saved board')
        check(not data['via_in_smd'],f'{name}: no drilled vias intersect SMD solder lands')
        check(data['layers']==(4 if name=='main' else 2) and data['tracks']>0,f'{name}: routed copper and intended layers')
        expected={(p['ref'],pin):net for p in parts if p['board']==name for pin,net in p['pins'].items()}
        found={}
        for ref,fp in data['parts'].items():
            if ref not in byref:
                check(ref in ('H1','H2','H3','H4'),f'{name}: only mounting holes board-only')
                continue
            p=byref[ref]
            check(p['board']==name and p['side']==fp['side'] and math.hypot(p['x']-fp['x'],p['y']-fp['y'])<1e-5,f'{ref}: board, side and placement')
            check(all(fp[k]==p[k] for k in ('value','mpn','manufacturer','datasheet')),f'{ref}: PCB value and part metadata match source')
            for pad in fp['pads']:
                if not pad['number']:continue
                key=(ref,pad['number']);net=pad['net']
                net=None if not net or net.startswith('unconnected-') else net
                check(key not in found or found[key]==net,f'{ref}.{pad["number"]}: repeated pads agree')
                found[key]=net
        check(found==expected,f'{name}: all native PCB pad nets match source')
        compiled=ET.parse(OUT/f'Adolfo-{name}.net')
        snets={(node.attrib['ref'],node.attrib['pin']):net.attrib['name'] for net in compiled.findall('./nets/net') if not net.attrib['name'].startswith('unconnected-') for node in net.findall('node')}
        check(snets=={k:v for k,v in expected.items() if v is not None},f'{name}: native compiled schematic graph matches source')
        padmaps[name]={(ref,p['number']):p for ref,fp in data['parts'].items() for p in fp['pads'] if p['number']}
    check(not metrics['main']['plane_signal_tracks'] and any(z['net']=='GND' and z['layer']=='In1.Cu' and z['filled'] for z in metrics['main']['zones']),'Inner ground plane reserved from signal tracks')
    power=metrics['main']['parts'][byid['JPOWER']['ref']]['pads']
    check(len(power)==10 and all(abs(p['drill_x']-1.1)<1e-6 and abs(p['drill_y']-1.1)<1e-6 for p in power),'IDC10 holes follow the manufacturer 1.10 mm recommendation')
    for n in range(1,41):
        a=padmaps['main'][(byid['JM']['ref'],str(n))];b=padmaps['panel'][(byid['JP']['ref'],str(n))]
        check(abs(a['x']-b['x'])<1e-6 and abs(a['y']-b['y'])<1e-6,f'Mating physical pin {n}')
    _,bypass,analog=placement_constraints();distances={}
    for group,limit in ((bypass,8),(analog,12)):
        for role,(owner,pin) in group.items():
            p=byid[role];pad=padmaps['main'][(byid[owner]['ref'],pin)]
            distance=math.hypot(p['x']-pad['x'],p['y']-pad['y']);distances[role]=round(distance,3)
            maximum=6 if role.startswith('CADC') or role in ('CVDRV','CREFADC','CREFCAP','CREG1','CREG2') else limit
            check(distance<=maximum,f'{role}: near {owner}.{pin} ({distance:.2f} mm <= {maximum} mm)')
    native=json.loads((OUT/'native-checks.json').read_text(encoding='utf-8'))
    check(native['status']=='PASS','Native ERC/DRC, unconnected and schematic parity all zero')
    for filename,sha in native['files'].items():check(digest(OUT/filename)==sha,f'Fresh native check: {filename}')
    analog_check.run()
    rates=design['rates'];adc_us=rates['adc_bits_per_frame']/rates['adc_spi_target_hz']*1e6;dac_us=8*rates['dac_bits_per_word']/rates['dac_spi_target_hz']*1e6
    check(adc_us<1e6/rates['adc_hz'] and dac_us<1e6/rates['audio_hz'],'SPI payload fits target periods; real DMA timing remains open')
    report={'status':'PASS_CAD_RELEASE_BLOCKED','cad_status':'PASS','release_status':'BLOCKED',
        'release_blockers':RELEASE_BLOCKERS,'checks':len(checks),'parts':len(parts),'revision':'D',
        'routing':{name:{k:metrics[name][k] for k in ('layers','tracks','vias','track_length_mm')} for name in metrics},
        'locality_mm':distances,'adc_payload_us':adc_us,'dac_payload_us':dac_us,
        'not_verified':['physical component and stack fit','real firmware drivers, DMA and timing','power, thermal and fault transients','noise, distortion and stability on hardware','calibration and loaded output accuracy'],
        'details':checks}
    design['status']='ROUTED_CAD_RELEASE_BLOCKED'
    design['release_blockers']=RELEASE_BLOCKERS
    (OUT/'design.json').write_text(json.dumps(design,indent=2)+'\n',encoding='utf-8')
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f'PASS CAD: {len(checks)} checks; {len(parts)} parts. RELEASE BLOCKED: {", ".join(RELEASE_BLOCKERS)}')


if __name__=='__main__':
    try:run()
    except Exception as error:
        (OUT/'validation.json').write_text(json.dumps({'status':'FAIL','checks_passed':len(checks),'error':str(error)},indent=2)+'\n',encoding='utf-8')
        raise
