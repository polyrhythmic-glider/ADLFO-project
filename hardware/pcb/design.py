"""Adolfo universal carrier C: electrical candidate, two unrouted boards.

Panel coordinates in mm, viewed from the front. Every candidate must be reviewed
against its datasheet and hardware; the firmware Adolfo/ is the old prototype.
"""
PANEL = dict(width=101.2, height=128.5, hp=20, thickness=2)
PCB = dict(x=2.5, y=9, width=96.2, height=110.5, thickness=1.6)
COLUMNS = [17.5,39.5,61.5,83.5]
MOUNTS = [(6.5,12),(94.7,12),(6.5,116),(94.7,116)]
OLED = dict(x=24, y=22.5, width=27, height=15, header_y=11)
RAIL_SLOTS = [(7.5,3),(93.86,3),(7.5,125.5),(93.86,125.5)]
# New board ONLY. SPI assignments checked against libDaisy per/spi.cpp.
PINS = dict(DAC_SYNC=0,DAC_LDAC=1,DAC_SCK=2,ADC_BUSY=3,ADC_CONVST=4,
            ADC_RESET=5,DAC_MOSI=6,ADC_CS=7,ADC_SCK=8,ADC_MISO=9,
            ADC_MOSI=10,I2C_SCL=11,I2C_SDA=12,DAC_CLR=13,OUTPUT_PERMIT=14,
            ENC1_A=15,ENC1_B=16,ENC2_A=17,ENC2_B=18,
            ENC3_A=19,ENC3_B=20,ENC4_A=21,ENC4_B=22,IO_RESET=23)
PORTS = ([dict(id=f'IN{i}',direction='input',adc=i-1,modes=['audio','cv','gate','trigger']) for i in range(1,5)]
       + [dict(id=f'OUT{i}',direction='output',dac=i-1,modes=['audio','cv','envelope','lfo','gate','trigger']) for i in range(1,5)]
       + [dict(id=f'CTRL{i}',direction='bidirectional',adc=i+3,dac=i+3,modes=['cv_in','gate_in','trigger_in','cv_out','gate_out','trigger_out']) for i in range(1,5)])
# ADC frame: eight 18-bit words serialized into 18 bytes; use SPI 8-bit DMA.
RATES = dict(adc_hz=96000,audio_hz=48000,control_hz=1000,
             adc_spi_target_hz=25000000,dac_spi_target_hz=25000000,
             adc_bits_per_frame=144,dac_bits_per_word=32)
INTERCONNECT = {i+1:n for i,n in enumerate(
    [f'{role}{i}' for role in ['IN','CTRL','OUT'] for i in range(1,5)]
    +[f'ENC{i}_{p}' for i in range(1,5) for p in ['A','B','CLICK']]
    +[f'KEY{i}' for i in range(1,5)]
    +['I2C_SCL','I2C_SDA','+3V3','GND','GND','GND','GND','GND','GND','GND','GND','GND'])}

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
    # Both boards use exactly the same connector pin numbers; key direction is TBD.
    add('JM','Panel link 2x20 candidate','header40',50.6,87,INTERCONNECT)
    add('JP','Panel link 2x20 candidate','header40',50.6,87,INTERCONNECT,'panel','B',note='Stack height and connector polarity require physical review.')
    for i,x in enumerate(COLUMNS,1):
        add(f'E{i}','EC11 click candidate','encoder',x,48,{'A':f'ENC{i}_A','B':f'ENC{i}_B','C':'GND','S1':f'ENC{i}_CLICK','S2':'GND','MP':'GND'},'panel')
        add(f'K{i}','6x6 tact height TBD','button',x,67,{1:f'KEY{i}',2:'GND'},'panel')
        for j,(role,y) in enumerate([('IN',80),('CTRL',95),('OUT',110)]):
            add(f'J{3*(i-1)+j+1}',f'{role}{i} PJ398SM','jack',x,y,{'S':'GND','T':f'{role}{i}','TN':None},'panel',note='Normals left open: must never ground a CTRL port used as output.')
    add('J14','SSD1306 breakout raised','oled',24,11,{1:'GND',2:'+3V3',3:'I2C_SCL',4:'I2C_SDA'},'panel',note='Assumed GND/VCC/SCL/SDA order; module dimensions unconfirmed.')
    seed={i+1:None for i in range(40)}
    for name,d in PINS.items():seed[d+1 if d<15 else d+7]=name
    seed.update({20:'GND',38:'+3V3',39:'+5D',40:'GND'})
    add('U1','Daisy Seed 3 / Seed2 DFM compatibility review','seed',70,24,seed,side='B',note='Common 40-pin footprint candidate; onboard audio and 12-bit DAC unused. Check USB-C and DFM mechanical envelope.')
    adc={i:None for i in range(1,65)}
    adc.update({i:'+5A' for i in [1,37,38,48]})
    adc.update({i:'GND' for i in [2,26,35,40,41,47,16,17,18,30,31,32,33,8,10,43,46]})
    adc.update({3:'+3V3',4:'+3V3',5:'+3V3',6:'+3V3',7:'+3V3',9:'ADC_CONVST',11:'ADC_RESET',12:'ADC_SCK',13:'ADC_CS',14:'ADC_BUSY',23:'+3V3',24:'ADC_MISO',29:'ADC_MOSI',34:'+3V3',36:'REGCAP1',39:'REGCAP2',42:'ADC_REF',44:'ADC_REFCAP',45:'ADC_REFCAP'})
    for i in range(8):adc[49+2*i]=f'ADC_IN{i+1}';adc[50+2*i]='GND'
    add('U2','AD7606C-18 candidate','lqfp64',27,51,adc,note='SOFTWARE mode OS[2:0]=111; select one DOUTA, bipolar ranges, bandwidth per channel. No audio HPF. Register/DMA driver missing.')
    dac={1:'DAC_LDAC_5V',2:'DAC_SYNC_5V',3:'+5A',4:'DAC1',5:'DAC3',6:'DAC5',7:'DAC7',8:'REF2V5',9:'DAC_CLR_5V',10:'DAC8',11:'DAC6',12:'DAC4',13:'DAC2',14:'GND',15:'DAC_MOSI_5V',16:'DAC_SCK_5V'}
    add('U3','DAC8568B (gain 1, midscale reset) candidate','tssop16',62,50,dac,note='B grade matters: internal 2.5 V reference, output span 2.5 V, midscale reset; enable reference in software. 16-bit output, not a 24-bit codec.')
    # MCP23017 SOIC28. Port A: 4 clicks + 4 keys, port B: 8 switch requests.
    io={1:'REQ5',2:'REQ6',3:'REQ7',4:'REQ8',5:'+3V3',6:'GND',7:None,8:'I2C_SCL',9:'I2C_SDA',10:None,11:'GND',12:'GND',13:'GND',14:'IO_RESET',15:None,16:None,17:'ENC1_CLICK',18:'ENC2_CLICK',19:'ENC3_CLICK',20:'ENC4_CLICK',21:'KEY1',22:'KEY2',23:'KEY3',24:'KEY4',25:'REQ1',26:'REQ2',27:'REQ3',28:'REQ4'}
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
    # First-pass RC only. A proper analog antialias/reconstruction design is OPEN.
    for n,port in enumerate([f'IN{i}' for i in range(1,5)]+[f'CTRL{i}' for i in range(1,5)],1):
        x=9+(n-1)*11
        two(f'RI{n}','1k input protection candidate',x,41,port,f'ADC_IN{n}')
        cap(f'CI{n}','1nF EMI only - NOT full antialias',x,44,f'ADC_IN{n}')
        two(f'RP{n}','10k',x,37,f'ENC{(n-1)//2+1}_{"A" if n%2 else "B"}','+3V3')
    for n,net in enumerate([f'ENC{i}_CLICK' for i in range(1,5)]+[f'KEY{i}' for i in range(1,5)],1):two(f'RK{n}','10k',9+(n-1)*11,107,net,'+3V3')
    for n,net in enumerate(['ADC_CS','DAC_SYNC','DAC_LDAC','DAC_CLR','IO_RESET'],1):two(f'RU{n}','10k',9+(n-1)*11,111,net,'+3V3')
    two('RPERMIT','10k',80,111,'OUTPUT_PERMIT','GND')
    two('RSCL','4.7k DNP',80,15,'I2C_SCL','+3V3');two('RSDA','4.7k DNP',90,15,'I2C_SDA','+3V3')
    # Eurorack input and candidate power module, analog branch filtered.
    add('JPOWER','Eurorack IDC10 keyed','idc10',10.5,24,{1:'-12_IN',2:'-12_IN',3:'GND',4:'GND',5:'GND',6:'GND',7:'GND',8:'GND',9:'+12_IN',10:'+12_IN'})
    two('DPOWERP','SS14',10,13,'+12VA','+12_IN','sma');two('DPOWERN','SS14',23,13,'-12_IN','-12VA','sma')
    add('UREG','5V >=1A module - selection OPEN','power_module',80,42,{1:'+12VA',2:'GND',3:'+5D'},note='Envelope placeholder, not an orderable/verified footprint. Compare converter ripple, startup and heat. No case +5V required.')
    two('FB1','Ferrite 600R@100MHz candidate',64,37,'+5D','+5A')
    for ref,value,x,y,rail in [('C5D','47uF 10V',85,34,'+5D'),('C5A','10uF 10V',58,37,'+5A'),('CVDRV','100nF',34,51,'+3V3'),('CREG1','1uF',20,57,'REGCAP1'),('CREG2','1uF',23,57,'REGCAP2'),('CREFADC','100nF',26,57,'ADC_REF'),('CREFCAP','10uF low ESR',29,57,'ADC_REFCAP'),('CREFDAC','100nF',62,56,'REF2V5')]:cap(ref,value,x,y,rail)
    for j in range(4):cap(f'CADC{j}','100nF',18+j*3,48,'+5A')
    for n,(rail,x,y) in enumerate([('+5D',90,34),('+5A',62,44),('+3V3',33,24),('+3V3',40,74),('+3V3',62,74),('+12VA',40,89),('-12VA',40,92),('+12VA',62,89),('-12VA',62,92)],1):cap(f'CD{n}','100nF',x,y,rail)
    for j,(net,x) in enumerate([('GND',10),('+12VA',25),('-12VA',40),('+5D',55),('+5A',70),('REF_BUF',85)],1):add(f'TP{j}',net,'testpoint',x,117,{1:net})
    return parts
