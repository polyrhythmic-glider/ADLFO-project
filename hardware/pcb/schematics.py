"""Functional, hierarchical KiCad schematics with electrical pin types.

Standard symbols are redistributed under vendor/KICAD-LICENSE.md. Custom IC
pin definitions follow the manufacturer documents recorded in references.json.
"""
from copy import deepcopy
from pathlib import Path
from collections import defaultdict
from math import ceil, cos, sin, radians
from kiutils.symbol import SymbolLib, Symbol
from kiutils.schematic import Schematic
from kiutils.utils import sexpr

HERE=Path(__file__).parent
KICAD=Path('C:/Program Files/KiCad/10.0/share/kicad')


def custom(name, pins):
    """IC blocks use datasheet signal names, never the connected net as pin name."""
    from build import q
    left=[p for p in pins if p[2] not in ('output','power_out','open_collector')]
    right=[p for p in pins if p not in left]
    half=max(len(left),len(right));h=(half+2)*2.54
    rows=[]
    for side,items in [(-1,left),(1,right)]:
        for i,(num,label,typ) in enumerate(items):
            x=side*25.4;y=h/2-2.54*(i+1)
            rows.append(f'(pin {typ} line (at {x} {y} {0 if side<0 else 180}) (length 5.08) '
                        f'(name {q(label)} (effects (font (size 1 1)))) (number {q(num)} (effects (font (size 1 1)))))')
    raw=f'''(symbol "{name}" (pin_names (offset 1)) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 {h/2+5.08} 0) (effects (font (size 1.27 1.27))))
      (property "Value" "{name}" (at 0 {h/2+2.54} 0) (effects (font (size 1.27 1.27))))
      (symbol "{name}_0_1" (rectangle (start -20.32 {h/2}) (end 20.32 {-h/2})
        (stroke (width .254) (type default)) (fill (type background))))
      (symbol "{name}_1_1" {''.join(rows)}))'''
    return Symbol.from_sexpr(sexpr.parse_sexp(raw))


def make_library():
    """Copy only the symbols used here, flattening standard library aliases."""
    requested={'Device':['R','C','D_Schottky','Polyfuse','L'],
               'Connector_Generic':['Conn_02x20_Odd_Even'],
               'Connector':['TestPoint'],'Switch':['SW_Push'],
               'Amplifier_Operational':['OPA4197xD'],'Comparator':['LM393'],
               'Interface_Expansion':['MCP23017x-x-SO'],
               '74xx':['74AHCT125','74LS08','74HC74'],
               '74xGxx':['74LVC1G08'],
               'Converter_DCDC':['R-78E5.0-1.0'],'power':['PWR_FLAG']}
    symbols={}
    for library,names in requested.items():
        source=SymbolLib.from_sexpr(sexpr.parse_sexp((KICAD/'symbols'/f'{library}.kicad_sym').read_text(encoding='utf-8')))
        all_symbols={s.entryName:s for s in source.symbols}
        def resolve(name):
            s=deepcopy(all_symbols[name])
            if s.extends:
                base=resolve(s.extends);s.units=deepcopy(base.units);s.extends=None
                for u in s.units:u.entryName=name
            return s
        for name in names:
            s=resolve(name);s.libraryNickname=None;symbols[name]=s
    adc={str(i):('DB'+str(i-16),'bidirectional') for i in range(16,34)}
    for n in (1,37,38,48):adc[str(n)]=('AVCC','power_in')
    for n in (2,26,35,40,41,47):adc[str(n)]=('AGND','power_in')
    for n,label in {3:'OS0',4:'OS1',5:'OS2',6:'PAR_SER_SEL',7:'STBY',8:'RANGE',9:'CONVST',10:'WR',11:'RESET',12:'RD_SCLK',13:'CS',29:'DB13_SDI',34:'REF_SELECT'}.items():adc[str(n)]=(label,'input')
    for n,label in {14:'BUSY',15:'FRSTDATA',24:'DB9_DOUTA',25:'DB10_DOUTB',27:'DB11_DOUTC',28:'DB12_DOUTD'}.items():adc[str(n)]=(label,'output')
    adc['23']=('VDRIVE','power_in')
    for n,label in {36:'REGCAPA',39:'REGCAPB',42:'REFIN_REFOUT',44:'REFCAPA',45:'REFCAPB'}.items():adc[str(n)]=(label,'power_out')
    adc['45']=('REFCAPB','passive')
    # These pins are fixed digital inputs in the selected serial/software mode (Table 23).
    for n in (16,17,18,30,31,32,33):adc[str(n)]=(adc[str(n)][0]+'_SERIAL','input')
    adc['43']=('REFGND','power_in');adc['46']=('REFGND','power_in')
    for i in range(8):adc[str(49+2*i)]=(f'V{i+1}P','input');adc[str(50+2*i)]=(f'V{i+1}N','input')
    assert set(adc)=={str(i) for i in range(1,65)}
    dac={1:('LDAC','input'),2:('SYNC','input'),3:('AVDD','power_in'),4:('VOUTA','output'),5:('VOUTC','output'),
         6:('VOUTE','output'),7:('VOUTG','output'),8:('VREFIN_VREFOUT','power_out'),9:('CLR','input'),10:('VOUTH','output'),
         11:('VOUTF','output'),12:('VOUTD','output'),13:('VOUTB','output'),14:('GND','power_in'),15:('DIN','input'),16:('SCLK','input')}
    switch={4:('VNEG','power_in'),5:('GND','power_in'),12:('FF_N','open_collector'),13:('VPOS','power_in')}
    for i,(ctl,drain,source) in enumerate([(1,2,3),(16,15,14),(9,10,11),(8,7,6)],1):
        switch.update({ctl:(f'IN{i}','input'),drain:(f'D{i}','passive'),source:(f'S{i}_PROTECTED','passive')})
    seed={i:('D'+str(i-1 if i<=15 else i-7),'bidirectional') for i in range(1,41)}
    seed.update({16:('AUDIO_IN_L','input'),17:('AUDIO_IN_R','input'),18:('AUDIO_OUT_L','output'),19:('AUDIO_OUT_R','output'),
                 20:('AGND','power_in'),21:('+3V3A','power_out'),38:('+3V3D','power_out'),39:('VIN_5V','power_in'),40:('DGND','power_in')})
    from design import PINS
    for net,n in PINS.items():
        typ='input' if net in ('ADC_BUSY','ADC_MISO','FAULT_N') or net.startswith('ENC') else 'bidirectional' if net.startswith('I2C') else 'output'
        seed[n+1 if n<15 else n+7]=('D'+str(n)+'_'+net,typ)
    custom_parts={'AD7606C_18':adc,'DAC8568B':dac,'ADG5412F':switch,'Daisy_Seed_3':seed,
        'TPS3828':{1:('RESET_N','open_collector'),2:('GND','power_in'),3:('MR_N','input'),4:('WDI','input'),5:('VDD','power_in')},
        'TPS3808':{1:('RESET_N','open_collector'),2:('GND','power_in'),3:('MR_N','input'),4:('CT','passive'),5:('SENSE','input'),6:('VDD','power_in')},
        'OLED_Waveshare':{1:('VCC','power_in'),2:('GND','power_in'),3:('DIN_SDA','bidirectional'),4:('CLK_SCL','input'),5:('CS','input'),6:('DC_ADDR','input'),7:('RESET_N','input')},
        'EC11':{'A':('A','passive'),'B':('B','passive'),'C':('C','passive'),'S1':('SW1','passive'),'S2':('SW2','passive'),'MP':('CASE','passive')},
        'PJ398SM':{'T':('TIP','passive'),'TN':('TIP_NORMAL','passive'),'S':('SLEEVE','passive')},
        'IDC10':{i:(str(i),'passive') for i in range(1,11)}}
    for name,pins in custom_parts.items():symbols[name]=custom(name,[(str(n),label,typ) for n,(label,typ) in pins.items()])
    for s in symbols.values():s.libraryNickname=None
    lib=SymbolLib(symbols=list(symbols.values()))
    lib.to_file(str(HERE/'vendor'/'ADOLFO.kicad_sym'))
    return symbols


def symbol_name(part):
    ref=part['id'];fp=part['footprint']
    exact={'U1':'Daisy_Seed_3','U2':'AD7606C_18','U3':'DAC8568B','U4':'MCP23017x-x-SO',
           'U5':'74LS08','U6':'74LS08','U7':'ADG5412F','U8':'ADG5412F','U14':'ADG5412F','U15':'ADG5412F',
           'U16':'74HC74','U17':'TPS3828','U18':'TPS3808','U19':'LM393','U20':'74LVC1G08',
           'U12':'74AHCT125','U13':'74AHCT125','UREG':'R-78E5.0-1.0','JPOWER':'IDC10','FB1':'L'}
    if ref in exact:return exact[ref]
    if fp=='soic14':return 'OPA4197xD'
    return {'r0805':'R','r2010':'R','c0805':'C','c0603':'C','c1210':'C','sma':'D_Schottky','sod323':'D_Schottky','fuse1206':'Polyfuse',
            'header40':'Conn_02x20_Odd_Even','socket40':'Conn_02x20_Odd_Even','oled7':'OLED_Waveshare','encoder':'EC11','button':'SW_Push',
            'jack':'PJ398SM','testpoint':'TestPoint'}[fp]


def generate(parts,out):
    from build import uid,q
    symbols=make_library();paths={}
    # The two boards have separate project roots so native schematic parity is meaningful.
    for board,project in [('main','Adolfo-main'),('panel','Adolfo-panel')]:
        rootid=uid(project+'/root');pages=defaultdict(list)
        for part in parts:
            if part['board']!=board:continue
            name=symbol_name(part);symbol=symbols[name]
            units=sorted({u.unitId for u in symbol.units if u.pins}) or [1]
            for unit in units:
                group=part['group']
                if group=='CONTROL':
                    group='GPIO_BIASES'
                    if part['id']=='U4' or part['id'].startswith('RK'):group='IO_EXPANDER'
                    if part['id'] in ('U5','U6') or part['id'].startswith(('RE','RQ')):group='OUTPUT_ENABLE'
                if board=='panel':group='FRONT_CONTROLS' if part['footprint'] not in ('jack','header40','socket40') else 'JACKS_AND_LINK'
                if name=='OPA4197xD':
                    ref=part['id'];n=int(ref[1:])
                    if unit==5:group='ANALOG_DECOUPLING'
                    elif n in (9,10):group=f'OUT{(n-9)*4+unit}_DRIVER'
                    elif n==11:group='REFERENCE'
                    elif n>=21:group=f'{"IN" if n<23 else "OUT"}{((n-21)%2)*2+(unit-1)//2+1}_FILTER'
                if part['id'].startswith(('RA','RB','RC','RD','RO')) and part['id'][2:].isdigit():group='OUT'+part['id'][2:]+'_DRIVER'
                if part['id'].startswith('RREF'):group='REFERENCE'
                pages[group].append((part,name,unit))
        rootfile=project+'.kicad_sch';pagefiles=[]
        for page,(group,items) in enumerate(pages.items(),2):
            filename=project+'-'+group.lower()+'.kicad_sch';sheetid=uid(filename);pagefiles.append((filename,sheetid,group))
            definitions={};instances=[];connections=[];x=55.88;y=45.72;rowh=0
            functional=group.endswith('_FILTER') or (group.startswith('OUT') and group.endswith('_DRIVER'))
            positions={}
            if functional:
                from functional_sheets import layout
                positions,connections=layout(group,items,symbols)
            for part,name,unit in items:
                symbol=symbols[name];pinlist=[p for u in symbol.units if u.unitId in (0,unit) for p in u.pins]
                assert pinlist,(part['ref'],unit)
                pinsheight=max(p.position.Y for p in pinlist)-min(p.position.Y for p in pinlist)
                height=max(25.4,pinsheight+25.4)
                if x>510:x=55.88;y+=rowh;rowh=0
                rowh=max(rowh,height)
                if y+height>395:raise RuntimeError('Schematic sheet overfull: '+group)
                sy=round((y+height/2)/1.27)*1.27;sx=x
                angle=90 if name in ('R','L','Polyfuse','D_Schottky') else 0
                if functional:sx,sy,angle=positions[(part['id'],unit)]
                key='ADOLFO:'+name;lib=deepcopy(symbol);lib.libraryNickname='ADOLFO';definitions[key]=lib.to_sexpr()
                ref=part['ref'];sid=uid(filename+'/'+ref+'/'+str(unit));path=f'/{rootid}/{sheetid}'
                paths.setdefault(ref,path+'/'+sid)
                for pin in pinlist:
                    assert pin.number in part['pins'],(ref,pin.number)
                    if functional:continue
                    r=radians(angle)
                    px=round(sx+pin.position.X*cos(r)-pin.position.Y*sin(r),5)
                    py=round(sy-pin.position.X*sin(r)-pin.position.Y*cos(r),5)
                    net=part['pins'][pin.number];pid=uid(sid+'/'+pin.number)
                    if net is None:
                        connections.append(f'(no_connect (at {px} {py}) (uuid {pid}))');continue
                    orientation=((pin.position.angle or 0)+angle)%360;a=radians(orientation)
                    ex=round(px-5.08*cos(a),5);ey=round(py+5.08*sin(a),5)
                    connections.append(f'(wire (pts (xy {px} {py}) (xy {ex} {ey})) (stroke (width 0) (type default)) (uuid {pid}))')
                    if orientation in (90,270):
                        nx=round(ex-7.62,5)
                        connections.append(f'(wire (pts (xy {ex} {ey}) (xy {nx} {ey})) (stroke (width 0) (type default)) (uuid {uid(pid+"elbow")}))')
                        ex=nx;orientation=0
                    connections.append(f'(global_label {q(net)} (shape bidirectional) (at {ex} {ey} {orientation}) '
                        f'(effects (font (size 1 1)) (justify {"right" if orientation==0 else "left"})) (uuid {uid(pid+"label")}))')
                top=max(pin.position.Y for pin in pinlist)
                rx,ry,vx,vy,justify=sx,sy-top-7.62,sx,sy-top-5.08,''
                if name in ('R','L','Polyfuse','D_Schottky','C'):
                    if angle in (90,270):rx,ry,vx,vy=sx,sy-5.08,sx,sy+5.08
                    else:rx,ry,vx,vy,justify=sx+5.08,sy-1.27,sx+5.08,sy+2.54,' (justify left)'
                instances.append(f'''(symbol (lib_id {q(key)}) (at {sx} {sy} {angle}) (unit {unit}) (in_bom yes) (on_board yes) (uuid {sid})
                    (property "Reference" {q(ref)} (at {rx} {ry} {90 if angle in (90,270) else 0}) (effects (font (size 1.27 1.27)){justify}))
                    (property "Value" {q(part['value'])} (at {vx} {vy} {90 if angle in (90,270) else 0}) (effects (font (size 1 1)){justify}))
                    (property "Footprint" {q('ADOLFO:'+part['footprint'])} (at {sx} {sy} 0) (effects (font (size 1 1)) hide))
                    (property "MPN" {q(part['mpn'])} (at {sx} {sy} 0) (effects (font (size 1 1)) hide))
                    (property "Manufacturer" {q(part['manufacturer'])} (at {sx} {sy} 0) (effects (font (size 1 1)) hide))
                    (property "Datasheet" {q(part['datasheet'])} (at {sx} {sy} 0) (effects (font (size 1 1)) hide))
                    (property "BOM Comments" {q(part['note'])} (at {sx} {sy} 0) (effects (font (size 1 1)) hide))
                    (instances (project "{project}" (path "{path}" (reference "{ref}") (unit {unit})))) )''')
                x+=91.44
            raw=f'''(kicad_sch (version 20231120) (generator eeschema) (uuid {sheetid}) (paper "{'A3' if functional else 'A2'}")
                (title_block (title "ADOLFO / {group}") (rev "D ENGINEERING") (comment 1 "DC-coupled universal carrier / physical validation required"))
                (lib_symbols {''.join(definitions.values())}) {''.join(connections)} {''.join(instances)})'''
            Schematic.from_sexpr(sexpr.parse_sexp(raw)).to_file(str(out/filename))
        # Power flags declare the external and passively filtered power sources explicitly.
        flags=['GND','+12_IN','-12_IN','+12VA','-12VA','+5A'] if board=='main' else ['GND','+3V3']
        defs=deepcopy(symbols['PWR_FLAG']);defs.libraryNickname='ADOLFO'
        content=[]
        for i,net in enumerate(flags):
            x=25.4+i*40.64;y=25.4;sid=uid(project+'/flag/'+net)
            content.append(f'''(symbol (lib_id "ADOLFO:PWR_FLAG") (at {x} {y} 0) (unit 1) (in_bom no) (on_board no) (uuid {sid})
              (property "Reference" "#FLG{i+1:02d}" (at {x} {y-7.62} 0) (effects (font (size 1 1)) hide))
              (property "Value" "PWR_FLAG" (at {x} {y-5.08} 0) (effects (font (size 1 1))))
              (instances (project "{project}" (path "/{rootid}" (reference "#FLG{i+1:02d}") (unit 1)))))
              (global_label "{net}" (shape input) (at {x} {y} 0) (effects (font (size 1 1)) (justify left)) (uuid {uid(sid+'label')}))''')
        for i,(filename,sheetid,group) in enumerate(pagefiles):
            x=25.4+(i%4)*177.8;y=55.88+(i//4)*45.72
            content.append(f'''(sheet (at {x} {y}) (size 152.4 30.48) (stroke (width .254) (type default))
              (fill (color 0 0 0 0)) (uuid {sheetid})
              (property "Sheetname" "{group}" (at {x} {y-1.27} 0) (effects (font (size 1.27 1.27)) (justify left bottom)))
              (property "Sheetfile" "{filename}" (at {x} {y+31.75} 0) (effects (font (size 1 1)) (justify left top)))
              (instances (project "{project}" (path "/{rootid}" (page "{i+2}")))))''')
        root=f'''(kicad_sch (version 20231120) (generator eeschema) (uuid {rootid}) (paper "A1")
          (title_block (title "ADOLFO / {board.upper()} / schematic index") (rev "D ENGINEERING"))
          (lib_symbols {defs.to_sexpr()}) {''.join(content)} (sheet_instances (path "/" (page "1"))))'''
        Schematic.from_sexpr(sexpr.parse_sexp(root)).to_file(str(out/rootfile))
    SymbolLib(symbols=list(symbols.values())).to_file(str(out/'ADOLFO.kicad_sym'))
    (out/'sym-lib-table').write_text('(sym_lib_table (lib (name "ADOLFO") (type "KiCad") (uri "${KIPRJMOD}/ADOLFO.kicad_sym") (options "") (descr "Local electrical symbols")))\n')
    return paths
