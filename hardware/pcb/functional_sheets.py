"""Readable, wired drawings of the actual Sallen-Key and output-driver circuits."""
from math import cos,sin,radians


def layout(group,items,symbols):
    from build import uid,q
    positions={};graphics=[];points={};seq=0
    roles={p['id']:p for p,_,_ in items}
    def put(role,x,y,angle=0,unit=1):positions[(role,unit)]=(x,y,angle)
    def wire(*vertices):
        nonlocal seq
        for a,b in zip(vertices,vertices[1:]):
            if a==b:continue
            seq+=1;graphics.append(f'(wire (pts (xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})) (stroke (width 0) (type default)) (uuid {uid(group+"wire"+str(seq))}))')
    def label(net,point,angle=0):
        nonlocal seq
        seq+=1;graphics.append(f'(global_label {q(net)} (shape bidirectional) (at {point[0]} {point[1]} {angle}) '
            f'(effects (font (size 1 1)) (justify {"right" if angle==0 else "left"})) (uuid {uid(group+"label"+str(seq))}))')
    def dot(point):
        graphics.append(f'(junction (at {point[0]} {point[1]}) (diameter 0) (color 0 0 0 0) (uuid {uid(group+"dot"+str(point))}))')
    def note(value,x,y):
        graphics.append(f'(text {q(value)} (at {x} {y} 0) (effects (font (size 2 2)) (justify left)) (uuid {uid(group+value)}))')
    filt=group.endswith('_FILTER')
    direction='IN' if group.startswith('IN') else 'OUT'
    ch=int(group[len(direction)] if filt else group[3])
    if filt:
        amp='U'+str((21 if direction=='IN' else 23)+(ch-1)//2)
        for stage in (1,2):
            offset=(stage-1)*162.56;stem=f'{direction}{ch}F{stage}'
            put('R'+stem+'A',55.88+offset,99.06,90)
            put('R'+stem+'B',91.44+offset,99.06,90)
            put('C'+stem+'A',109.22+offset,73.66,90)
            put('C'+stem+'B',109.22+offset,119.38)
            put(amp,132.08+offset,101.6,unit=((ch-1)%2)*2+stage)
        if direction=='IN':put(f'RADCF{ch}',350.52,101.6,90)
    else:
        amp='U'+str(9+(ch-1)//4);put(amp,177.8,101.6,unit=(ch-1)%4+1)
        put(f'RA{ch}',91.44,99.06,90);put(f'RB{ch}',132.08,124.46)
        put(f'RC{ch}',91.44,157.48,90);put(f'RD{ch}',200.66,157.48,270)
        put(f'RO{ch}',294.64,101.6,90)
    assert len(positions)==len(items),(group,len(positions),len(items))
    for part,name,unit in items:
        x,y,angle=positions[(part['id'],unit)];a=radians(angle)
        for u in symbols[name].units:
            if u.unitId not in (0,unit):continue
            for p in u.pins:
                points[(part['id'],unit,p.number)]=(round(x+p.position.X*cos(a)-p.position.Y*sin(a),5),
                    round(y-p.position.X*sin(a)-p.position.Y*cos(a),5))
    def pin(role,num,unit=1):return points[(role,unit,str(num))]
    units=[(3,2,1),(5,6,7),(10,9,8),(12,13,14)]
    if filt:
        previous=None
        for stage in (1,2):
            off=(stage-1)*162.56;stem=f'{direction}{ch}F{stage}';unit=((ch-1)%2)*2+stage
            plus,minus,output=units[unit-1]
            ra,rb,ca,cb=['R'+stem+'A','R'+stem+'B','C'+stem+'A','C'+stem+'B']
            if previous is None:
                source=(43.18,99.06);wire(source,pin(ra,1));label(roles[ra]['pins']['1'],source)
            else:wire(previous,(184.15,101.6),(184.15,99.06),pin(ra,1))
            aa=(73.66+off,99.06);bb=(109.22+off,99.06);oo=(149.86+off,101.6)
            wire(pin(ra,2),aa,pin(rb,1));wire(aa,(aa[0],73.66),pin(ca,1));dot(aa)
            wire(pin(rb,2),bb,pin(amp,plus,unit));wire(bb,pin(cb,1));dot(bb)
            wire(pin(amp,output,unit),oo);wire(pin(ca,2),(oo[0],73.66),oo)
            wire(pin(amp,minus,unit),(121.92+off,104.14),(121.92+off,139.7),(oo[0],139.7),oo);dot(oo)
            label(stem+'_A',(aa[0],81.28));label(stem+'_B',(bb[0],109.22))
            label(stem+'_OUT',(oo[0],91.44),180)
            wire(pin(cb,2),(bb[0],132.08));label('GND',(bb[0],132.08))
            previous=oo
        if direction=='IN':
            resistor=f'RADCF{ch}';wire(previous,pin(resistor,1));end=(365.76,101.6)
            wire(pin(resistor,2),end);label(roles[resistor]['pins']['2'],end,180)
        note(f'{direction}{ch}: unity-gain, DC-coupled fourth-order low-pass, approximately 20 kHz.',25.4,180.34)
        note('C0G capacitors 1%, resistors 0.1%. Op-amp supply units: ANALOG_DECOUPLING.',25.4,190.5)
    else:
        unit=(ch-1)%4+1;plus,minus,output=units[unit-1]
        aa=(132.08,99.06);bb=(157.48,157.48);oo=(228.6,101.6)
        source=(76.2,99.06);wire(source,pin(f'RA{ch}',1));label(f'DAC{ch}',source)
        wire(pin(f'RA{ch}',2),aa,pin(amp,plus,unit));wire(aa,pin(f'RB{ch}',1));dot(aa)
        wire(pin(f'RB{ch}',2),(132.08,137.16));label('GND',(132.08,137.16))
        source=(76.2,157.48);wire(source,pin(f'RC{ch}',1));label('REF_BUF',source)
        wire(pin(f'RC{ch}',2),bb,pin(f'RD{ch}',2));dot(bb)
        wire(bb,(157.48,104.14),pin(amp,minus,unit))
        wire(pin(amp,output,unit),oo,(228.6,157.48),pin(f'RD{ch}',1));dot(oo)
        wire(oo,(228.6,91.44));label(f'AMP{ch}',(228.6,91.44),180)
        label(f'PLUS{ch}',(132.08,109.22));label(f'MINUS{ch}',(157.48,147.32))
        if ch<=4:
            source=(279.4,101.6);wire(source,pin(f'RO{ch}',1));label(f'OUT{ch}F2_OUT',source)
            note(f'AMP{ch} -> OUT{ch}_FILTER -> series resistor -> protected output switch.',25.4,190.5)
        else:wire(oo,pin(f'RO{ch}',1))
        end=(317.5,101.6);wire(pin(f'RO{ch}',2),end);label(f'DRIVE{ch}',end,180)
        note('Vamp = 4 x Vdac - 4 x Vref; Vref = 1.25 V. Output approximately -5 V to +5 V.',25.4,180.34)
        note('Series 1 kohm / 0.5 W limits patch-fault current; calibrate for the intended load.',25.4,200.66)
    return positions,graphics
