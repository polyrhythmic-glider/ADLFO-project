"""ADLFO revision B: single source of electrical and mechanical intent (mm).

This is a reviewable placement proposal, not released manufacturing data.
Coordinates are viewed from the panel, origin at its upper left.
"""
PANEL = dict(width=101.2, height=128.5, thickness=2.0, hp=20)
PCB = dict(x=2.5, y=9.0, width=96.2, height=110.5, thickness=1.6)
COLUMNS = [17.5, 39.5, 61.5, 83.5]
COLORS = ['#efb65c', '#60c9bd', '#98a9ef', '#e28eac']
MOUNTS = [(6.5, 12), (94.7, 12), (6.5, 116), (94.7, 116)]
RAIL_SLOTS = [(7.5, 3), (93.86, 3), (7.5, 125.5), (93.86, 125.5)]
OLED = dict(x=24, y=22.5, width=27, height=15, body_width=27.5,
            body_height=27.8, header_y=11.0)
ENCODERS = [(0, 1, 2), (3, 4, 5), (7, 8, 9), (10, 13, 14)]
BUTTONS = [25, 24, 26, 27]
TRIGGERS = [6, 19, 20, 21]
CV = [15, 16, 17, 18]

def gpio(d):
    return f'D{d}'

def circuit():
    parts = []
    def add(ref, value, footprint, x, y, pins, side='B', group='SYSTEM', note=''):
        parts.append(dict(ref=ref, value=value, footprint=footprint, x=x, y=y,
                          pins={str(k): v for k, v in pins.items()}, side=side,
                          group=group, note=note))
    def two(ref, value, fp, x, y, n1, n2, group='SYSTEM', note=''):
        add(ref, value, fp, x, y, {1:n1, 2:n2}, group=group, note=note)
    seed = {i+1:gpio(i) for i in range(15)}
    seed.update({i+7:gpio(i) for i in range(15, 31)})
    seed.update({16:None, 17:None, 18:None, 19:None, 20:'GND',
                 21:None, 38:'+3V3', 39:'+5V_SEED', 40:'GND'})
    for d in [22, 23, 28, 29, 30]: seed[d+7] = None
    add('U1', 'Daisy Seed (socketed)', 'seed', 70, 24, seed,
        note='2 x 20 sockets, 2.54 mm pitch; row spacing 15.24 mm; USB toward right in panel view.')
    # Adafruit MCP4728 STEMMA QT: JP1 pins 1..6, JP2 pins 7..12.
    # Derived from the upstream Eagle board, not the bare IC pinout.
    add('U2', 'Adafruit MCP4728 STEMMA QT breakout', 'mcp4728_breakout', 29, 24,
        {1:'+3V3', 2:'GND', 3:'D11', 4:'D12', 5:'GND', 6:None,
         7:'GND', 8:'DAC1', 9:'DAC2', 10:'DAC3', 11:'DAC4', 12:'+3V3'},
        note='Two 1x6 female sockets, rows 12.70 mm apart; module 25.4 x 17.78 mm. JP1: VCC/GND/SCL/SDA/LDAC/RDY. Verify actual board revision; no second DAC IC on carrier.')
    in_pins = {4:'+3V3', 11:'GND'}
    out_pins = {4:'+12VA', 11:'-12VA'}
    for ch, (plus, minus, out) in enumerate([(3,2,1),(5,6,7),(10,9,8),(12,13,14)], 1):
        in_pins.update({plus:f'CV_CLAMP{ch}', minus:f'CV_BUF{ch}', out:f'CV_BUF{ch}'})
        out_pins.update({plus:f'OUT_PLUS{ch}', minus:f'OUT_FB{ch}', out:f'OUT_AMP{ch}'})
    add('U3', 'MCP6004-I/SL', 'soic14', 28.5, 60, in_pins)
    add('U4', 'TL074CDR', 'soic14', 50.5, 60, out_pins,
        note='Dual supply; nominal non-inverting gain 2.5. Feedback before output resistor.')
    add('U5', 'R-78E5.0-0.5', 'recom', 51, 40.5,
        {1:'+12VA', 2:'GND', 3:'+5V_REG'}, note='Candidate 500 mA converter, not a confirmed budget. Size from Daisy + OLED + DAC + analog load, startup and thermal measurements; no case +5 V required.')
    add('J13', 'EURORACK 2x5 keyed', 'idc10', 10.5, 25,
        {1:'-12V_IN',2:'-12V_IN',3:'GND',4:'GND',5:'GND',6:'GND',7:'GND',8:'GND',9:'+12V_IN',10:'+12V_IN'},
        note='Red stripe = pins 1/2 = -12 V. Key orientation must match cable.')
    add('J14', 'OLED SSD1306 128x64', 'oled', OLED['x'], OLED['header_y'],
        {1:'GND',2:'+3V3',3:'D11',4:'D12'}, 'F',
        note='Assumed module GND/VCC/SCL/SDA, 0.96 inch; measure actual glass, PCB and connector before release.')
    add('F1', 'PTC 0.5A hold candidate', 'ptc1812', 8, 58,
        {1:'+12V_IN',2:'+12V_FUSED'},
        note='Candidate only: select rated voltage >=24 V and hold/trip current from measured startup and hot-case load. Package must match selected PTC.')
    two('D1', 'SS14', 'sma', 12, 38.5, '+12VA', '+12V_FUSED', note='Pad 1 cathode: protected positive rail.')
    two('D2', 'SS14', 'sma', 30, 36, '-12V_IN', '-12VA', note='Pad 1 cathode: raw negative rail.')
    two('D3', 'SS14', 'sma', 73, 38, '+5V_SEED', '+5V_REG', note='Blocks reverse feed from USB into 5 V converter; check specific Seed revision.')
    two('C1', '10uF 50V X7R', 'c0805', 12, 11.5, '+12VA', 'GND', note='Allow for MLCC DC bias; 1206 may be needed after part selection.')
    two('C2', '10uF 50V X7R', 'c0805', 32, 11.5, 'GND', '-12VA')
    two('C3', '10uF 10V X7R', 'c0805', 61, 34.5, '+5V_REG', 'GND')
    two('C4', '10uF 10V X7R', 'c0805', 73, 34.5, '+5V_SEED', 'GND')
    two('C5', '100nF', 'c0805', 37, 36, '+3V3', 'GND')
    two('C6', '10uF 10V X7R', 'c0805', 37, 39, '+3V3', 'GND')
    two('C7', '100nF', 'c0805', 23, 60, '+3V3', 'GND')
    two('C8', '100nF 50V', 'c0805', 45, 60, '+12VA', 'GND')
    two('C9', '100nF 50V', 'c0805', 50.5, 52.5, '-12VA', 'GND')
    two('C10', '47uF 10V low ESR candidate', 'radial_cap', 94, 37, '+5V_SEED', 'GND',
        note='Local 5 V bulk capacitor; check regulator stability, startup and actual case size before fitting.')
    two('C11', '100nF', 'c0805', 79, 34.5, '+5V_SEED', 'GND')
    two('C12', '100nF', 'c0805', 91, 42, '+3V3', 'GND')
    two('R1', '4.7k DNP', 'r0805', 39, 11.5, '+3V3', 'D11')
    two('R2', '4.7k DNP', 'r0805', 45, 11.5, '+3V3', 'D12')
    for i, (net, x, y) in enumerate([('GND',14,118),('+12VA',32,118),('-12VA',50,118),
                                      ('+5V_SEED',68,118),('+3V3',90,118)],1):
        add(f'TP{i}',net,'testpoint',x,y,{1:net})
    for i, x in enumerate(COLUMNS, 1):
        group = f'CH{i}'
        a,b,sw=ENCODERS[i-1]
        # Preserve E3's existing software direction compensation; validate on hardware.
        add(f'ENC{i}', ['RISE','FALL','SYMMETRY','LEVEL'][i-1], 'encoder', x,48,
            {'A':gpio(a),'B':gpio(b),'C':'GND','S1':gpio(sw),'S2':'GND','MP':'GND'}, 'F', group,
            note='ALPS EC11E15244G1 candidate; shaft height, anti-rotation tab and E3 direction to verify.')
        add(f'SW{i}', f'CH {i}', 'button', x,67, {1:gpio(BUTTONS[i-1]),2:'GND'}, 'F', group,
            note='6x6 mm tact, 13 mm actuator candidate, 4 mm panel aperture; match actual actuator.')
        for j, (role,y) in enumerate([('TRIG',80),('CV',95),('OUT',110)]):
            add(f'J{(i-1)*3+j+1}', f'{role}{i}', 'jack', x,y,
                {'S':'GND','T':f'{role}{i}','TN':'GND' if role!='OUT' else None}, 'F', group,
                note='PJ398SM/WQP518MA; input normal contact grounded; central 3 mm NPTH added.')
        # Trigger: 100k series, 1M B-E, 47k collector pull-up, reverse B-E diode.
        base=f'TRIG_BASE{i}'
        two(f'R{i}01','100k','r0805',x-7,77,f'TRIG{i}',base,group)
        two(f'R{i}02','1M','r0805',x-7,81,base,'GND',group)
        two(f'R{i}03','47k','r0805',x-7,85,'+3V3',gpio(TRIGGERS[i-1]),group)
        add(f'Q{i}','MMBT3904','sot23',x+6,80,
            {1:base,2:'GND',3:gpio(TRIGGERS[i-1])},group=group)
        two(f'D{i}01','1N4148W','sod123',x+6,85,base,'GND',group)
        # CV input: divider, RC, series impedance, Schottky clamps, buffer, ADC RC.
        two(f'R{i}04','100k 0.1%','r0805',x-7,92,f'CV{i}',f'CV_DIV{i}',group)
        two(f'R{i}05','33k 0.1%','r0805',x-7,96,f'CV_DIV{i}','GND',group)
        two(f'R{i}06','10k','r0805',x-7,100,f'CV_DIV{i}',f'CV_CLAMP{i}',group)
        two(f'C{i}01','10nF','c0805',x+6,90,f'CV_DIV{i}','GND',group)
        add(f'D{i}02','BAT54S','sot23',x+6,94,
            {1:'GND',2:'+3V3',3:f'CV_CLAMP{i}'},group=group)
        two(f'R{i}07','1k','r0805',x+6,99,f'CV_BUF{i}',gpio(CV[i-1]),group)
        two(f'C{i}02','1nF','c0805',x+6,103,gpio(CV[i-1]),'GND',group)
        # Output matches repository proposal; intentionally not a precision pitch output.
        two(f'R{i}08','10k','r0805',x,56,f'DAC{i}',f'OUT_PLUS{i}',group)
        two(f'R{i}09','10k 0.1%','r0805',x,59.5,f'OUT_FB{i}','GND',group)
        two(f'R{i}10','15k 0.1%','r0805',x,63,f'OUT_AMP{i}',f'OUT_FB{i}',group)
        two(f'R{i}11','2.2k 0.5W','r2010',x+7,110,f'OUT_AMP{i}',f'OUT{i}',group,
            note='Nominal 5 V open circuit; about 4.89 V into 100k. Check reverse patch and thermal behavior.')
        # Optional external pulls; libDaisy already debounces controls in software.
        for j, (pin, y) in enumerate([(a,35.5),(b,39),(sw,71.5),(BUTTONS[i-1],74.5)], 1):
            two(f'RP{i}{j}', '10k DNP', 'r0805', x+3, y, '+3V3', gpio(pin), group,
                note='Optional external pull-up. Fit only after checking internal pull-ups and actual encoder/module; never pull GPIO to 5 V.')
        add(f'TP{10+i}',f'DAC{i}','testpoint',x-7,70,{1:f'DAC{i}'},group=group)
    return parts

def holes():
    result=[]
    for i,x in enumerate(COLUMNS,1):
        for kind,y,d in [('encoder',48,7.2),('button',67,4.0),('trig',80,6.2),('cv',95,6.2),('out',110,6.2)]:
            result.append(dict(ref=f'{kind.upper()}{i}',x=x,y=y,diameter=d,kind=kind))
    for i,(x,y) in enumerate(MOUNTS,1):
        result.append(dict(ref=f'M{i}',x=x,y=y,diameter=3.2,kind='mount'))
    return result

