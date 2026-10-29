"""SPICE the complete populated filters and DAC differential amplifiers.

The ideal model checks network math. The single-pole model is sensitivity only;
neither represents OPA4197 overload recovery, output current or full stability.
"""
from pathlib import Path
from math import pi
import json
import hashlib
import re
import sys
from run_detected import SharedNgspice

HERE = Path(__file__).resolve().parent
PCB = HERE.parents[1]
sys.path.insert(0, str(PCB))
from analog_check import quantity, response

FREQUENCIES = (1000, 10000, 18000, 20000, 48000, 76000, 100000)
UNITS = ((3,2,1), (5,6,7), (10,9,8), (12,13,14))


def node(net):
    return '0' if net == 'GND' else re.sub(r'[^a-zA-Z0-9_]', '_', net)


def model(kind):
    if kind == 'ideal':
        return '.subckt op plus minus out\nEamp out 0 plus minus 1e9\n.ends op'
    # OPA4197 nominal 10 MHz GBW, represented by one dominant pole only.
    return f'.subckt op plus minus out\nEamp raw 0 plus minus 1e6\nRdom raw pole 1k\nCdom pole 0 {1/(2*pi*10*1000)}\nEbuf out 0 pole 0 1\n.ends op'


def run_circuit(name, lines, control):
    path = HERE/(name+'.cir')
    out = HERE/(name+'.out')
    lines += ['.control', *control, 'echo '+ ' '.join(
        f'{key}=$&{key}' for key in ('gain0','gain1','gain2','gain3','gain4','gain5','gain6'))
        +' > '+out.as_posix(), '.endc', '.end']
    path.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    ok, stdout, stderr = SharedNgspice().run(path, timeout=10)
    path.with_suffix('.log').write_text(stdout+'\n'+stderr, encoding='utf-8')
    assert ok, (path, stdout, stderr)
    from spice_results import parse_output_file
    data = parse_output_file(str(out))
    assert all(data.get('gain'+str(i)) is not None for i in range(7)), (path,data,stdout)
    return data


def check_filters(parts, kind):
    byid = {p['id']:p for p in parts}
    results = []
    for direction in ('IN', 'OUT'):
        for ch in range(1,5):
            first = f'PROTECTED{ch}' if direction == 'IN' else f'AMP{ch}'
            last = f'{direction}{ch}F2_OUT'
            lines = [f'{direction}{ch} complete 4-pole filter ({kind})', model(kind)]
            path_parts = [p for p in parts if p['group'] == f'{direction}{ch}_FILTER']
            for p in path_parts:
                pins = p['pins']
                lines.append(f"{p['ref']} {node(pins['1'])} {node(pins['2'])} {quantity(p['value'])}")
            for stage in (1,2):
                owner = f'U{(21 if direction == "IN" else 23)+(ch-1)//2}'
                plus, minus, out = UNITS[((ch-1)%2)*2+stage-1]
                pins = byid[owner]['pins']
                assert pins[str(plus)] == f'{direction}{ch}F{stage}_B'
                assert pins[str(minus)] == pins[str(out)] == f'{direction}{ch}F{stage}_OUT'
                lines.append(f'Xstage{stage} {node(pins[str(plus)])} {node(pins[str(minus)])} {node(pins[str(out)])} op')
            if direction == 'IN':
                r=byid[f'RI{ch}'];c=byid[f'CI{ch}']
                lines += [f'Vtest port 0 dc 0 ac 1',
                          f'Rjack port limit {quantity(r["value"])}',
                          f'Rswitch limit {node(first)} 10',
                          f'Cemi {node(c["pins"]["1"])} 0 {quantity(c["value"])}',
                          f'Radc {node(c["pins"]["1"])} adc_bias 1Meg', 'Vbias adc_bias 0 2']
                measure=node(c['pins']['1'])
            else:
                lines += [f'Vtest {node(first)} 0 dc 0 ac 1']
                measure=node(last)
            control=['ac dec 500 10 1Meg']
            control += [f'meas ac gain{i} find vdb({measure}) at={f}' for i,f in enumerate(FREQUENCIES)]
            data = run_circuit(f'{direction}{ch}_{kind}',lines,control)
            if kind == 'ideal':
                for i,f in enumerate(FREQUENCIES):
                    expected=20*__import__('math').log10(abs(response(f,1010 if direction=='IN' else 0)))
                    assert abs(data[f'gain{i}']-expected) < .02, (direction,ch,f,data[f'gain{i}'],expected)
            results.append({'path':f'{direction}{ch}', 'model':kind,
                            'db_at_hz':{str(f):data[f'gain{i}'] for i,f in enumerate(FREQUENCIES)},
                            'status':'pass',
                            'source_resistance_ohm':1010 if direction=='IN' else 0})
    return results


def check_drivers(parts):
    byid = {p['id']:p for p in parts};results=[]
    for ch in range(1,9):
        lines=[f'OUT{ch} differential amplifier',model('ideal')]
        for prefix in ('RA','RB','RC','RD'):
            p=byid[f'{prefix}{ch}']
            lines.append(f'{p["ref"]} {node(p["pins"]["1"])} {node(p["pins"]["2"])} {quantity(p["value"])}')
        owner=f'U{9+(ch-1)//4}';plus,minus,out=UNITS[(ch-1)%4];pins=byid[owner]['pins']
        lines += [f'Xgain {node(pins[str(plus)])} {node(pins[str(minus)])} {node(pins[str(out)])} op',
                  f'VDAC DAC{ch} 0 1.25', 'VREF REF_BUF 0 1.25']
        control=['dc VDAC 0 2.5 0.625']
        control += [f'meas dc gain{i} find v(AMP{ch}) at={v}' for i,v in enumerate((0,.625,1.25,1.875,2.5,1.25,1.25))]
        data=run_circuit(f'driver{ch}',lines,control)
        expected=(-5,-2.5,0,2.5,5)
        for i,v in enumerate(expected):assert abs(data[f'gain{i}']-v)<1e-6,(ch,data)
        results.append({'path':f'AMP{ch}', 'model':'ideal', 'status':'pass',
                        'dac_input_v':[0,.625,1.25,1.875,2.5],
                        'amp_output_v':[data[f'gain{i}'] for i in range(5)]})
    return results


if __name__ == '__main__':
    design_path=PCB/'output'/'design.json'
    design=json.loads(design_path.read_text(encoding='utf-8'))
    parts=design['parts']
    results=check_filters(parts,'ideal')+check_filters(parts,'dominant_pole')+check_drivers(parts)
    report={'simulator':'ngspice-46 shared library bundled with KiCad 10.0',
            'source':str(design_path),'source_sha256':hashlib.sha256(design_path.read_bytes()).hexdigest(),
            'results':results,
            'limits':['Ideal passives; 10 ohm ADG RON is an assumption.',
                      'ADC input loading approximated as 1 Mohm to 2 V.',
                      'Dominant-pole model uses nominal 10 MHz GBW, not the manufacturer macromodel.',
                      'No slew, saturation, leakage, thermal, short-circuit, noise or full stability validation.']}
    (HERE/'full_paths.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
