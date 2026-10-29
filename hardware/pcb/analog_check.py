"""Small-signal checks for the populated DC-coupled filter networks.

Ideal op-amp calculations check topology/values, not noise, protection or real
op-amp stability. Those remain physical qualification measurements.
"""
from itertools import product
from math import pi, log10
from pathlib import Path
import json
import numpy as np
from design import circuit

PARTS={p['id']:p for p in circuit()}

def quantity(value):
    value=value.split()[0]
    for suffix,scale in [('pF',1e-12),('nF',1e-9),('uF',1e-6),('k',1e3),('M',1e6),('R',1)]:
        if value.endswith(suffix):return float(value[:-len(suffix)])*scale
    return float(value)


def response(frequency,source=0,scales=(1,)*8):
    s=2j*pi*frequency;gain=1
    for i in range(2):
        stem=f'{"IN" if source else "OUT"}1F{i+1}'
        r1=quantity(PARTS['R'+stem+'A']['value'])*scales[i*4]+(source if i==0 else 0)
        r2=quantity(PARTS['R'+stem+'B']['value'])*scales[i*4+1]
        c1=quantity(PARTS['C'+stem+'A']['value'])*scales[i*4+2];c2=quantity(PARTS['C'+stem+'B']['value'])*scales[i*4+3]
        gain/=1+s*c2*(r1+r2)+s*s*r1*r2*c1*c2
    return gain


def run():
    parts=PARTS
    for direction in ('IN','OUT'):
        for channel in range(1,5):
            for stage in (1,2):
                stem=f'{direction}{channel}F{stage}'
                assert parts['R'+stem+'A']['pins']['2']==stem+'_A'
                assert parts['R'+stem+'B']['pins']=={'1':stem+'_A','2':stem+'_B'}
                assert parts['C'+stem+'A']['pins']=={'1':stem+'_A','2':stem+'_OUT'}
                assert parts['C'+stem+'B']['pins']=={'1':stem+'_B','2':'GND'}
    assert abs(response(0)-1)<1e-12
    result={}
    for name,source in [('input',1010),('output',0)]:
        result[name]={str(f):round(20*log10(abs(response(f,source))),3) for f in (1000,10000,18000,20000,48000,76000,100000)}
        assert result[name]['18000']>-3
        assert result[name]['76000']<-43
        assert result[name]['1000']>-.05
        # Simultaneous tolerance corners: 0.1% resistors and 1% C0G capacitors.
        peak=0
        frequencies=np.geomspace(1,20000,80)
        for signs in product((-1,1),repeat=8):
            scales=tuple(1+sign*(.001 if i%4<2 else .01) for i,sign in enumerate(signs))
            peak=max(peak,max(abs(response(f,source,scales)) for f in frequencies))
        assert peak<1.08
        result[name]['worst_corner_peak_db']=round(20*log10(peak),3)
    # Nominal rail-monitor thresholds; accuracy/temperature are separate qualification checks.
    r=lambda ref:quantity(parts[ref]['value'])
    ref_mon=3.3*r('RMONREF2')/(r('RMONREF1')+r('RMONREF2'))
    result['rail_trip_nominal']={'positive_v':ref_mon*(1+r('RPMON1')/r('RPMON2')),
                                'negative_v':-(3.3-ref_mon)*r('RNMON1')/r('RNMON2')+ref_mon,
                                'analog_5v':.405*(1+r('R5MON1')/r('R5MON2'))}
    assert 10.3<result['rail_trip_nominal']['positive_v']<10.6
    assert -10.6<result['rail_trip_nominal']['negative_v']<-10.3
    assert 4.79<result['rail_trip_nominal']['analog_5v']<4.85
    result['not_verified']=['finite op-amp bandwidth/stability','noise and distortion','transient/fault response','component temperature drift']
    (Path(__file__).parent/'output'/'analog-check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':run()
