"""Adolfo universal carrier D: DC-coupled analog, protected I/O and hardware interlock.

Panel coordinates in mm, viewed from the front. Selected parts must be qualified
against its datasheet and hardware; the firmware Adolfo/ is the old prototype.
"""
PANEL = dict(width=101.2, height=128.5, hp=20, thickness=2)
PCB = dict(x=2.5, y=9, width=96.2, height=110.5, thickness=1.6)
COLUMNS = [17.5,39.5,61.5,83.5]
MOUNTS = [(6.5,12),(94.7,12),(6.5,116),(94.7,116)]
OLED = dict(x=PANEL['width']/2, y=22.5, width=22.2, height=11.6, header_y=11)
RAIL_SLOTS = [(7.5,3),(93.86,3),(7.5,125.5),(93.86,125.5)]
# New board ONLY. SPI assignments checked against libDaisy per/spi.cpp.
PINS = dict(DAC_SYNC=0,DAC_LDAC=1,DAC_SCK=2,ADC_BUSY=3,ADC_CONVST=4,
            ADC_RESET=5,DAC_MOSI=6,ADC_CS=7,ADC_SCK=8,ADC_MISO=9,
            ADC_MOSI=10,I2C_SCL=11,I2C_SDA=12,DAC_CLR=13,OUTPUT_PERMIT=14,
            ENC1_A=15,ENC1_B=16,ENC2_A=17,ENC2_B=18,
            ENC3_A=19,ENC3_B=20,ENC4_A=21,ENC4_B=22,IO_RESET=23,
            WATCHDOG=24,FAULT_N=25,OLED_RESET=26)
PORTS = ([dict(id=f'IN{i}',direction='input',adc=i-1,modes=['audio','cv','gate','trigger']) for i in range(1,5)]
       + [dict(id=f'OUT{i}',direction='output',dac=i-1,modes=['audio','cv','envelope','lfo','gate','trigger']) for i in range(1,5)]
       + [dict(id=f'CTRL{i}',direction='bidirectional',adc=i+3,dac=i+3,modes=['cv_in','gate_in','trigger_in','cv_out','gate_out','trigger_out']) for i in range(1,5)])
# ADC frame: eight 18-bit words serialized into 18 bytes; use SPI 8-bit DMA.
RATES = dict(adc_hz=96000,audio_hz=48000,control_hz=1000,
             adc_spi_target_hz=25000000,dac_spi_target_hz=25000000,
             adc_bits_per_frame=144,dac_bits_per_word=32)
# These are release blockers, independent of ERC/DRC and nominal payload checks.
RELEASE_BLOCKERS = {
    'ADC_SUPPLY_SEQUENCE': 'ADC VDRIVE can exceed AVCC + 0.3 V with USB-only power or unequal rail decay; supply and host-signal isolation need a hardware revision.',
    '5V_MONITOR_MARGIN': 'R-78E output tolerance and TPS3808 threshold/hysteresis do not guarantee both ADC operating voltage and reset release.',
    'CONVERTER_BACKEND': 'The new ADC/DAC backend is absent; stock libDaisy clocks and shared SPI DMA cannot sustain the declared rates.'}
INTERCONNECT = {i+1:n for i,n in enumerate(
    [f'{role}{i}' for role in ['IN','CTRL','OUT'] for i in range(1,5)]
    +[f'ENC{i}_{p}' for i in range(1,5) for p in ['A','B','CLICK']]
    +[f'KEY{i}' for i in range(1,5)]
    +['I2C_SCL','I2C_SDA','+3V3','GND','GND','GND','GND','GND','GND','GND','GND','GND'])}
INTERCONNECT[40]='OLED_RESET'

def holes():
    return ([dict(ref=f'{role}{i}',x=x,y=y,diameter=d,kind=role)
        for i,x in enumerate(COLUMNS,1)
        for role,y,d in [('ENC',48,7.2),('KEY',67,4),('IN',80,6.2),('CTRL',95,6.2),('OUT',110,6.2)]]
        +[dict(ref=f'H{i}',x=x,y=y,diameter=3.2,kind='mount') for i,(x,y) in enumerate(MOUNTS,1)])

def circuit():
    parts=[]
    def add(ref,value,fp,x,y,pins,board='main',side='F',note='',group='SYSTEM'):
        parts.append(dict(ref=ref,value=value,footprint=fp,x=x,y=y,
            pins={str(k):v for k,v in pins.items()},board=board,side=side,note=note,group=group))
    def two(ref,value,x,y,n1,n2,fp='r0805',**kw):add(ref,value,fp,x,y,{1:n1,2:n2},**kw)
    def cap(ref,value,x,y,rail,fp='c0805'):two(ref,value,x,y,rail,'GND',fp)
    # Mirrored rear socket and front header use matching physical pin coordinates.
    add('JM','Panel link 2x20 candidate','header40',50.6,87,INTERCONNECT)
    add('JP','Panel link 2x20 candidate','socket40',50.6,87,INTERCONNECT,'panel','B',note='Mirrored socket numbering mates to JM pin-for-pin.')
    for i,x in enumerate(COLUMNS,1):
        add(f'E{i}','EC11 click candidate','encoder',x,48,{'A':f'ENC{i}_A','B':f'ENC{i}_B','C':'GND','S1':f'ENC{i}_CLICK','S2':'GND','MP':'GND'},'panel')
        add(f'K{i}','6x6 tact height TBD','button',x,67,{1:f'KEY{i}',2:'GND'},'panel')
        for j,(role,y) in enumerate([('IN',80),('CTRL',95),('OUT',110)]):
            add(f'J{3*(i-1)+j+1}',f'{role}{i} PJ398SM','jack',x,y,{'S':'GND','T':f'{role}{i}','TN':'GND' if role=='IN' else None},'panel',note='Fixed IN normal grounded for a defined unpatched input; CTRL/OUT normals open to avoid shorting an output.')
    add('J14','SSD1306 breakout raised','oled',OLED['x'],OLED['header_y'],{1:'GND',2:'+3V3',3:'I2C_SCL',4:'I2C_SDA'},'panel',note='Assumed GND/VCC/SCL/SDA order; module dimensions unconfirmed.')
    seed={i+1:None for i in range(40)}
    for name,d in PINS.items():seed[d+1 if d<15 else d+7]=name
    seed.update({20:'GND',38:'+3V3',39:'+5D',40:'GND'})
    add('U1','Daisy Seed 3','seed',70,24,seed,side='B',note='Seed 3 40-pin carrier; onboard codec and MCU DAC unused. Verify physical USB access on the assembled stack.')
    adc={i:None for i in range(1,65)}
    adc.update({i:'+5A' for i in [1,37,38,48]})
    adc.update({i:'GND' for i in [2,26,35,40,41,47,16,17,18,30,31,32,33,8,10,43,46]})
    adc.update({3:'+3V3',4:'+3V3',5:'+3V3',6:'+3V3',7:'+3V3',9:'ADC_CONVST',11:'ADC_RESET',12:'ADC_SCK',13:'ADC_CS',14:'ADC_BUSY',23:'+3V3',24:'ADC_MISO',29:'ADC_MOSI',34:'+3V3',36:'REGCAP1',39:'REGCAP2',42:'ADC_REF',44:'ADC_REFCAP',45:'ADC_REFCAP'})
    for i in range(8):adc[49+2*i]=f'ADC_IN{i+1}';adc[50+2*i]='GND'
    add('U2','AD7606C-18 candidate','lqfp64',27,51,adc,note='SOFTWARE mode OS[2:0]=111; select one DOUTA, bipolar ranges, bandwidth per channel. No audio HPF. Register/DMA driver missing.')
    dac={1:'DAC_LDAC_5V',2:'DAC_SYNC_5V',3:'+5A',4:'DAC1',5:'DAC3',6:'DAC5',7:'DAC7',8:'REF2V5',9:'DAC_CLR_5V',10:'DAC8',11:'DAC6',12:'DAC4',13:'DAC2',14:'GND',15:'DAC_MOSI_5V',16:'DAC_SCK_5V'}
    add('U3','DAC8568B (gain 1, midscale reset) candidate','tssop16',62,50,dac,note='B grade matters: internal 2.5 V reference, output span 2.5 V, midscale reset; enable reference in software. 16-bit output, not a 24-bit codec.')
    # MCP23017 SOIC28; GPA7/GPB7 are output-only, so K4 uses GPB0.
    io={1: 'KEY4', 2: 'REQ1', 3: 'REQ2', 4: 'REQ3', 5: 'REQ4', 6: 'REQ5', 7: 'REQ6', 8: 'REQ7', 9: '+3V3', 10: 'GND', 11: None, 12: 'I2C_SCL', 13: 'I2C_SDA', 14: None, 15: 'GND', 16: 'GND', 17: 'GND', 18: 'IO_RESET', 19: None, 20: None, 21: 'ENC1_CLICK', 22: 'ENC2_CLICK', 23: 'ENC3_CLICK', 24: 'ENC4_CLICK', 25: 'KEY1', 26: 'KEY2', 27: 'KEY3', 28: 'REQ8'}
    add('U4','MCP23017-E/SO candidate','soic28',27,28,io,note='I2C 0x20. Encoders A/B stay on MCU GPIO; only clicks/keys and static output requests use expander.')
    # Two quad AND gates: permit defaults low independently from expander state.
    for bank,x in enumerate([45,67]):
        pins={7:'GND',14:'+3V3'}
        for j,(a,b,y) in enumerate([(1,2,3),(4,5,6),(9,10,8),(12,13,11)]):
            n=bank*4+j+1;pins.update({a:f'REQ{n}',b:'OUTPUT_PERMIT',y:f'SW_ON{n}'})
        add(f'U{5+bank}','SN74LVC08A candidate','soic14',x,74,pins)
    # Source terminals face jacks; only sources have the quoted fault protection.
    for bank,x in enumerate([45,67]):
        pins={4:'-12VA',5:'GND',12:f'FAULT{bank+1}',13:'+12VA'}
        for j,(control,drain,source) in enumerate([(1,2,3),(16,15,14),(9,10,11),(8,7,6)]):
            n=bank*4+j+1;port=f'OUT{j+1}' if bank==0 else f'CTRL{j+1}'
            pins.update({control:f'SW_ON{n}',drain:f'DRIVE{n}',source:port})
        add(f'U{7+bank}','ADG5412FBRUZ candidate','tssop16',x,89,pins,note='Not ADG5413F. IN=0 disconnects. Protected S faces jack; driver on D. Fault/power-off isolation needs bench qualification; not protection against every output collision.')
    # 8 bipolar differential amplifier candidates plus reference follower.
    quadpins=[{4:'+12VA',11:'-12VA'} for _ in range(3)]
    for n in range(1,9):
        idx=(n-1)//4;plus,minus,out=[(3,2,1),(5,6,7),(10,9,8),(12,13,14)][(n-1)%4]
        quadpins[idx].update({plus:f'PLUS{n}',minus:f'MINUS{n}',out:f'AMP{n}'})
        x=10+(n-1)*11;y=66
        two(f'RA{n}','10k 0.01% matched network TBD',x,y,f'DAC{n}',f'PLUS{n}')
        two(f'RB{n}','40k 0.01% matched network TBD',x,y+3,f'PLUS{n}','GND')
        two(f'RC{n}','10k 0.01% matched network TBD',x,y+6,'REF_BUF',f'MINUS{n}')
        two(f'RD{n}','40k 0.01% matched network TBD',x,y+9,f'AMP{n}',f'MINUS{n}')
        two(f'RO{n}','100R 0.25W candidate',x,83,f'AMP{n}',f'DRIVE{n}')
        two(f'RE{n}','100k',x,93,f'SW_ON{n}','GND')
        two(f'RQ{n}','100k',x,96,f'REQ{n}','GND')
    quadpins[2].update({3:'REF_HALF',2:'REF_BUF',1:'REF_BUF'})
    for plus,minus,out in [(5,6,7),(10,9,8),(12,13,14)]:quadpins[2].update({plus:'GND',minus:f'UNUSED_FB{out}',out:f'UNUSED_FB{out}'})
    for i,x in enumerate([13,45,80]):
        add(f'U{9+i}','OPA4197ID candidate','soic14',x,60,quadpins[i],note='Candidate: verify offset, stability, noise, output protection and matched ratios. 4*Vdac - 4*Vref gives approximately +/-5 V.')
        cap(f'CP{i}P','100nF 50V',x-5,55,'+12VA');cap(f'CP{i}N','100nF 50V',x-5,58,'-12VA')
    # DAC VIH at 5 V is 0.7*AVDD: 3.3 V direct drive is NOT guaranteed.
    # AHCT inputs have TTL thresholds; shift all five control lines to 5 V.
    signals=['DAC_SCK','DAC_MOSI','DAC_SYNC','DAC_LDAC','DAC_CLR']
    for bank in range(2):
        pins={1:'GND',4:'GND',7:'GND',10:'GND',13:'GND',14:'+5A'}
        for j,(a,y) in enumerate([(2,3),(5,6),(9,8),(12,11)]):
            idx=bank*4+j
            pins[a]=signals[idx] if idx<len(signals) else 'GND'
            pins[y]=signals[idx]+'_5V' if idx<len(signals) else None
        add(f'U{12+bank}','SN74AHCT125 candidate','soic14',70+bank*12,57,pins,note='5 V powered TTL-input buffers; validate timing/skew at selected SPI clock. Not LVC125 at 5 V.')
        cap(f'CBUF{bank}','100nF',70+bank*12,53,'+5A')
    two('RREF1','10k 0.01% matched',60,60,'REF2V5','REF_HALF')
    two('RREF2','10k 0.01% matched',60,63,'REF_HALF','GND')
    # Input RC base; complete_circuit adds protected inputs and the four-pole audio filters.
    for n,port in enumerate([f'IN{i}' for i in range(1,5)]+[f'CTRL{i}' for i in range(1,5)],1):
        x=9+(n-1)*11
        two(f'RI{n}','1k input protection candidate',x,41,port,f'ADC_IN{n}')
        cap(f'CI{n}','1nF EMI only - NOT full antialias',x,44,f'ADC_IN{n}')
        two(f'RP{n}','10k',x,37,f'ENC{(n-1)//2+1}_{"A" if n%2 else "B"}','+3V3')
    for n,net in enumerate([f'ENC{i}_CLICK' for i in range(1,5)]+[f'KEY{i}' for i in range(1,5)],1):two(f'RK{n}','10k',9+(n-1)*11,107,net,'+3V3')
    for n,net in enumerate(['ADC_CS','DAC_SYNC','DAC_LDAC','DAC_CLR','IO_RESET'],1):two(f'RU{n}','10k',9+(n-1)*11,111,net,'+3V3')
    two('RPERMIT','10k',80,111,'OUTPUT_PERMIT','GND')
    two('RSCL','4.7k DNP',80,15,'I2C_SCL','+3V3');two('RSDA','4.7k DNP',90,15,'I2C_SDA','+3V3')
    # Eurorack input; complete_circuit adds fuses and rail supervision.
    add('JPOWER','Eurorack IDC10 keyed','idc10',10.5,24,{1:'-12_IN',2:'-12_IN',3:'GND',4:'GND',5:'GND',6:'GND',7:'GND',8:'GND',9:'+12_IN',10:'+12_IN'})
    two('DPOWERP','SS14',10,13,'+12VA','+12_IN','sma');two('DPOWERN','SS14',23,13,'-12_IN','-12VA','sma')
    add('UREG','5V >=1A module - selection OPEN','power_module',80,42,{1:'+12VA',2:'GND',3:'+5D'},note='Envelope placeholder, not an orderable/verified footprint. Compare converter ripple, startup and heat. No case +5V required.')
    two('FB1','Ferrite 600R@100MHz candidate',64,37,'+5D','+5A')
    for ref,value,x,y,rail in [('C5D','47uF 10V',85,34,'+5D'),('C5A','10uF 10V',58,37,'+5A'),('CVDRV','100nF',34,51,'+3V3'),('CREG1','1uF',20,57,'REGCAP1'),('CREG2','1uF',23,57,'REGCAP2'),('CREFADC','100nF',26,57,'ADC_REF'),('CREFCAP','10uF low ESR',29,57,'ADC_REFCAP'),('CREFDAC','100nF',62,56,'REF2V5')]:cap(ref,value,x,y,rail)
    for j in range(4):cap(f'CADC{j}','100nF',18+j*3,48,'+5A')
    for n,(rail,x,y) in enumerate([('+5D',90,34),('+5A',62,44),('+3V3',33,24),('+3V3',40,74),('+3V3',62,74),('+12VA',40,89),('-12VA',40,92),('+12VA',62,89),('-12VA',62,92)],1):cap(f'CD{n}','100nF',x,y,rail)
    for j,(net,x) in enumerate([('GND',10),('+12VA',25),('-12VA',40),('+5D',55),('+5A',70),('REF_BUF',85)],1):add(f'TP{j}',net,'testpoint',x,117,{1:net})
    return complete_circuit(parts)


def complete_circuit(parts):
    """Rev D electrical completion; the working breakout prototype is separate."""
    byref={p['ref']:p for p in parts}
    def add(ref,value,fp,pins,group,note=''):
        p=dict(ref=ref,value=value,footprint=fp,x=0,y=0,pins={str(k):v for k,v in pins.items()},
               board='main',side='F',group=group,note=note)
        parts.append(p);byref[ref]=p;return p
    def two(ref,value,n1,n2,group,fp='r0805',note=''):
        return add(ref,value,fp,{1:n1,2:n2},group,note)
    def cap(ref,value,rail,group):return two(ref,value,rail,'GND',group,'c0805')
    # Populate exact, separately reviewed parts instead of an unselected regulator envelope.
    values={'U1':'Daisy Seed 3','U2':'AD7606C-18BSTZ','U3':'DAC8568BPW',
            'U4':'MCP23017-E/SO','U5':'SN74LVC08ADR','U6':'SN74LVC08ADR',
            'U7':'ADG5412FBRUZ','U8':'ADG5412FBRUZ','U9':'OPA4197ID','U10':'OPA4197ID',
            'U11':'OPA4197ID','U12':'SN74AHCT125DR','U13':'SN74AHCT125DR',
            'UREG':'R-78E5.0-1.0','FB1':'BLM21PG601SN1D',
            'JM':'Samtec TSW-120-07-G-D','JP':'Samtec SSW-120-02-G-D',
            'J14':'Waveshare 0.96inch OLED Module (D), I2C',
            'JPOWER':'Wurth 61201021621 IDC10'}
    for p in parts:
        p['value']=values.get(p['ref'],p['value'].replace(' candidate','').replace(' matched network TBD','').replace(' matched','').replace('0.01%','0.1%'))
        if p['ref'].startswith('E') and p['footprint']=='encoder':p['value']='ALPS EC11E18244AU'
        if p['footprint']=='button':p['value']='E-Switch TL1105DF160Q'
        if p['footprint']=='power_module':p['footprint']='recom'
        if p['ref'].startswith('RO'):
            p['value']='1k 0.5W 1%';p['footprint']='r2010'
            p['note']='Limits fault current; specify/calibrate the intended load. Not a load-independent pitch output.'
        if p['ref']=='UREG':p['note']='RECOM R-78E5.0-1.0, 8-28 V input, 5 V/1 A output, SIP3; max capacitive load 220 uF.'
    # The display header has seven real pins. Fit the module jumpers for I2C, address 0x3c.
    byref['J14']['footprint']='oled7'
    byref['J14']['pins']={'1':'+3V3','2':'GND','3':'I2C_SDA','4':'I2C_SCL','5':None,'6':'GND','7':'OLED_RESET'}
    byref['J14']['note']='Waveshare module (D), SSD1315, 26 x 26 mm; I2C hardware configuration required. Seven-pin order VCC/GND/DIN/CLK/CS/DC/RES.'
    # Hardware watchdog and a fault latch: recovery never silently re-enables the outputs.
    add('U16','SN74HCS74DR','soic14',{1:'SAFE_CLEAR_N',2:'+3V3',3:'OUTPUT_PERMIT',4:'+3V3',5:'SAFE_LATCH',6:None,7:'GND',
        8:None,9:None,10:'+3V3',11:'GND',12:'GND',13:'GND',14:'+3V3'},'SAFETY')
    add('U17','TPS3828-33DBVR','sot23_5',{1:'SAFE_CLEAR_N',2:'GND',3:'+3V3',4:'WATCHDOG',5:'+3V3'},'SAFETY')
    add('U18','TPS3808G01DBVR','sot23_6',{1:'SAFE_CLEAR_N',2:'GND',3:'+3V3',4:'RESET_DELAY',5:'SENSE_5A',6:'+3V3'},'SAFETY')
    add('U19','LM393BDR','soic8',{1:'SAFE_CLEAR_N',2:'REF_MON',3:'SENSE_POS',4:'GND',5:'REF_MON',6:'SENSE_NEG',7:'SAFE_CLEAR_N',8:'+5A'},'SAFETY')
    add('U20','SN74LVC1G08DBVR','sot23_5',{1:'SAFE_LATCH',2:'OUTPUT_PERMIT',3:'GND',4:'SAFE_PERMIT',5:'+3V3'},'SAFETY')
    # Daisy sees the hardware fault and must preload/settle all outputs before a new permit edge.
    two('RFAULT_LINK','0R','SAFE_CLEAR_N','FAULT_N','SAFETY')
    two('RFAULT','10k','SAFE_CLEAR_N','+3V3','SAFETY')
    two('RWDI','10k','WATCHDOG','GND','SAFETY')
    two('R5MON1','109k 0.1%','+5A','SENSE_5A','SAFETY')
    two('R5MON2','10k 0.1%','SENSE_5A','GND','SAFETY')
    two('RPMON1','53.1k 0.1%','+12VA','SENSE_POS','SAFETY')
    two('RPMON2','10k 0.1%','SENSE_POS','GND','SAFETY')
    two('RNMON1','1M 0.1%','-12VA','SENSE_NEG','SAFETY')
    two('RNMON2','137k 0.1%','+3V3','SENSE_NEG','SAFETY')
    two('RMONREF1','10k 0.1%','+3V3','REF_MON','SAFETY')
    two('RMONREF2','10k 0.1%','REF_MON','GND','SAFETY')
    two('DMONCLAMP','BAT54WS','SENSE_NEG','GND','SAFETY','sod323',note='Anode at GND; limits the negative comparator input if 3.3 V disappears before the negative rail.')
    cap('CMONP','10nF','SENSE_POS','SAFETY');cap('CMONN','1nF','SENSE_NEG','SAFETY')
    cap('CMON5','10nF','SENSE_5A','SAFETY');cap('CDELAY','10nF','RESET_DELAY','SAFETY')
    for n in (16,17,18,20):cap(f'CSAFE{n}','100nF','+3V3','SAFETY')
    cap('CSAFE19','100nF','+5A','SAFETY')
    for ref in ('U5','U6'):
        p=byref[ref]['pins']
        for pin,net in list(p.items()):
            if net=='OUTPUT_PERMIT':p[pin]='SAFE_PERMIT'
    for ref in ('U7','U8'):byref[ref]['pins']['12']='SAFE_CLEAR_N'
    # Protection on both sets of inputs also isolates externally driven jacks when power is absent.
    for bank in range(2):
        pins={4:'-12VA',5:'GND',12:'SAFE_CLEAR_N',13:'+12VA'}
        for j,(ctl,drain,source) in enumerate([(1,2,3),(16,15,14),(9,10,11),(8,7,6)]):
            n=bank*4+j+1;pins.update({ctl:'+3V3',drain:f'PROTECTED{n}',source:f'INPUT_LIMIT{n}'})
        add(f'U{14+bank}','ADG5412FBRUZ','tssop16',pins,'INPUT_PROTECTION')
        cap(f'CIP{bank}P','100nF 50V','+12VA','INPUT_PROTECTION')
        cap(f'CIP{bank}N','100nF 50V','-12VA','INPUT_PROTECTION')
    for n in range(1,9):
        byref[f'RI{n}']['pins']['2']=f'INPUT_LIMIT{n}'
        byref[f'RI{n}']['value']='1k 0.5W 1%';byref[f'RI{n}']['footprint']='r2010'
        byref[f'CI{n}']['value']='100pF C0G' if n<=4 else '1nF C0G'
        if n>4:two(f'RIC{n}','1k',f'PROTECTED{n}',f'ADC_IN{n}','CTRL_INPUTS')
    # Unity-gain Sallen-Key sections. Two unequal-C sections approximate a fourth-order
    # Butterworth at 20 kHz while preserving DC. Values are checked in analog_check.py.
    opamps=[{4:'+12VA',11:'-12VA'} for _ in range(4)]
    for direction in ('IN','OUT'):
        for ch in range(1,5):
            src=f'PROTECTED{ch}' if direction=='IN' else f'AMP{ch}'
            for stage,(c1,c2) in enumerate([('820pF C0G 1%','680pF C0G 1%'),('1.8nF C0G 1%','270pF C0G 1%')]):
                idx=(0 if direction=='IN' else 2)+(ch-1)//2
                section=((ch-1)%2)*2+stage
                plus,minus,output=[(3,2,1),(5,6,7),(10,9,8),(12,13,14)][section]
                stem=f'{direction}{ch}F{stage+1}';out=f'{stem}_OUT';a=stem+'_A';b=stem+'_B'
                opamps[idx].update({plus:b,minus:out,output:out})
                group=f'{direction}{ch}_FILTER'
                two('R'+stem+'A','11k 0.1%',src,a,group)
                two('R'+stem+'B','11k 0.1%',a,b,group)
                two('C'+stem+'A',c1,a,out,group,'c0805')
                cap('C'+stem+'B',c2,b,group)
                src=out
            if direction=='IN':two(f'RADCF{ch}','47R',src,f'ADC_IN{ch}',f'IN{ch}_FILTER')
            else:byref[f'RO{ch}']['pins']['1']=src
    for i,pins in enumerate(opamps,21):
        add(f'U{i}','OPA4197ID','soic14',pins,'INPUT_FILTER_AMPS' if i<23 else 'OUTPUT_FILTER_AMPS')
        cap(f'CFAMP{i}P','100nF 50V','+12VA','FILTER_POWER')
        cap(f'CFAMP{i}N','100nF 50V','-12VA','FILTER_POWER')
    # Separate rail fuses precede the polarity diodes. The 5 V module includes short protection.
    two('FPOWERP','Littelfuse 1206L075/24YR','+12_IN','+12_FUSED','POWER','fuse1206')
    two('FPOWERN','Littelfuse 1206L025/30YR','-12_IN','-12_FUSED','POWER','fuse1206')
    byref['DPOWERP']['pins']['2']='+12_FUSED';byref['DPOWERN']['pins']['1']='-12_FUSED'
    for ref,rail in [('CBULKP','+12VA'),('CBULKN','-12VA')]:
        p=cap(ref,'22uF 25V X7R',rail,'POWER');p['footprint']='c1210'
    cap('CREGIN','100nF 50V','+12VA','POWER');cap('CREGOUT','100nF','+5D','POWER')
    two('RRESET_OLED','10k','OLED_RESET','+3V3','PANEL_CONTROL')
    for signal,pin in [('ADC_SCK',12),('ADC_MOSI',29)]:
        byref['U2']['pins'][str(pin)]=signal+'_TERM'
        two('R'+signal,'33R',signal,signal+'_TERM','ADC')
    for signal,buffer_pin in [('DAC_SCK',3),('DAC_MOSI',6)]:
        byref['U12']['pins'][str(buffer_pin)]=signal+'_BUFFER'
        two('R'+signal,'33R',signal+'_BUFFER',signal+'_5V','DAC')
    for ref in ('RSCL','RSDA'):byref[ref]['value']='2.2k'
    for ref in ('CADC0','CADC1','CADC2','CADC3','CVDRV','CREFADC','CREG1','CREG2'):
        byref[ref]['footprint']='c0603'
    # Each group becomes a functional schematic sheet and a placement constraint.
    for p in parts:
        if p['group']!='SYSTEM':continue
        ref=p['ref']
        if p['board']=='panel':group='PANEL'
        elif ref in ('U1','JM'):group='PROCESSOR'
        elif ref in ('U2',) or ref.startswith(('CADC','CREG1','CREG2','CREFADC','CREFCAP','CVDRV')):group='ADC'
        elif ref in ('U3','U12','U13') or ref.startswith(('CREFDAC','CBUF')):group='DAC'
        elif ref in ('U7','U8'):group='OUTPUT_SWITCHES'
        elif ref in ('U9','U10','U11') or ref.startswith(('RA','RB','RC','RD','RO','RREF','CP')):group='OUTPUT_DRIVERS'
        elif ref in ('U4','U5','U6') or ref.startswith(('RE','RQ','RK','RP','RU','RS','RPERMIT')):group='CONTROL'
        else:group='POWER'
        p['group']=group
    digital={'U4','U5','U6','U12','U13','U16','U17','U18','U19','U20','UREG',
             'CBUF0','CBUF1','CD3','CD4','CD5','RADC_SCK','RADC_MOSI','RDAC_SCK','RDAC_MOSI',
             'CREFADC','CREFCAP','CREG1','CREG2'}
    for p in parts:
        if p['board']=='main' and (p['ref'] in digital or p['group'] in ('CONTROL','SAFETY','PANEL_CONTROL')):p['side']='B'
    byref['CREFCAP']['value']='10uF 25V X7R low ESR';byref['CREFCAP']['footprint']='c1210'
    for p in parts:
        p.update(mpn='',manufacturer='',datasheet='')
        if p['ref'].startswith(('RO','RI')) and p['footprint']=='r2010':
            p.update(value='1k 1W 1%',mpn='CRCW20101K00FKEFHP',manufacturer='Vishay',
                     datasheet='https://www.vishay.com/docs/20043/crcwhpe3.pdf')
        elif p['ref'].startswith('U') and p['ref'] not in ('U1','UREG'):
            p['mpn']=p['value']
            if p['value'].startswith(('AD7606','ADG')):
                p['manufacturer']='Analog Devices'
                pdf='ad7606c-18' if p['ref']=='U2' else 'ADG5412F_5413F'
                p['datasheet']=f'https://www.analog.com/media/en/technical-documentation/data-sheets/{pdf}.pdf'
            elif p['ref']=='U4':
                p.update(manufacturer='Microchip',datasheet='https://ww1.microchip.com/downloads/en/DeviceDoc/20001952C.pdf')
            else:
                p['manufacturer']='Texas Instruments'
                family={'U3':'dac8568','U16':'sn74hcs74','U17':'tps3828','U18':'tps3808',
                        'U19':'lm393b','U20':'sn74lvc1g08'}.get(p['ref'],
                        'sn74lvc08a' if p['ref'] in ('U5','U6') else 'sn74ahct125' if p['ref'] in ('U12','U13') else 'opa4197')
                p['datasheet']=f'https://www.ti.com/lit/ds/symlink/{family}.pdf'
        elif p['ref']=='UREG':
            p.update(mpn=p['value'],manufacturer='RECOM',datasheet='https://recom-power.com/pdf/Innoline/R-78E-1.0.pdf')
    # Keep descriptive IDs in the source/BOM, but use annotatable physical references in KiCad.
    import re
    used={p['ref'] for p in parts if re.fullmatch(r'[A-Za-z]+[0-9]+',p['ref'])}
    for p in parts:
        p['id']=p['ref']
        if p['ref'] in used:continue
        prefix=p['ref'][0];n=1
        while prefix+str(n) in used:n+=1
        p['ref']=prefix+str(n);used.add(p['ref'])
    assert len({p['ref'] for p in parts})==len(parts)
    return parts
