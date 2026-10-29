"""Run the native KiCad ERC/DRC gates and retain every reported violation."""
from pathlib import Path
from collections import Counter
import json
import hashlib
import os
import shutil
import subprocess

OUT=Path(__file__).parent/'output'


def violations(value):
    if isinstance(value,dict):
        if 'severity' in value and 'type' in value:yield value
        else:
            for child in value.values():yield from violations(child)
    elif isinstance(value,list):
        for child in value:yield from violations(child)


def summarize(path):
    items=list(violations(json.loads(path.read_text(encoding='utf-8'))))
    counts=dict(Counter(v['type'] for v in items))
    print(path.name,len(items),counts)
    return items


def run():
    cli=os.environ.get('KICAD_CLI') or shutil.which('kicad-cli') or 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
    failed=False
    for name in ('main','panel'):
        for kind in ('erc','drc'):
            path=OUT/f'{kind}-{name}.json'
            target=OUT/f'Adolfo-{name}.kicad_{"sch" if kind=="erc" else "pcb"}'
            command=[cli,'sch' if kind=='erc' else 'pcb',kind,'--format','json','--output',str(path),'--exit-code-violations']
            if kind=='drc':command+=['--schematic-parity','--refill-zones','--save-board']
            result=subprocess.run(command+[str(target)],check=False)
            items=summarize(path)
            failed|=bool(result.returncode or items)
    if not failed:
        for name in ('main','panel'):
            for side in ('front','back'):
                layer='F' if side=='front' else 'B'
                command=[cli,'pcb','export','svg','--mode-single','--fit-page-to-board',
                    '--exclude-drawing-sheet','--layers',f'{layer}.Cu,{layer}.SilkS,Edge.Cuts',
                    '--output',str(OUT/f'copper-{name}-{side}.svg')]
                if side=='back':command.append('--mirror')
                subprocess.run(command+[str(OUT/f'Adolfo-{name}.kicad_pcb')],check=True)
    tracked=[OUT/'ADOLFO.kicad_sym',OUT/'fp-lib-table',OUT/'sym-lib-table']
    tracked.extend((OUT/'ADOLFO.pretty').glob('*.kicad_mod'))
    for name in ('main','panel'):
        tracked.extend((OUT/f'Adolfo-{name}.kicad_pcb',OUT/f'Adolfo-{name}.kicad_pro',OUT/f'erc-{name}.json',OUT/f'drc-{name}.json'))
        tracked.extend(OUT.glob(f'Adolfo-{name}*.kicad_sch'))
    (OUT/'native-checks.json').write_text(json.dumps({'status':'FAIL' if failed else 'PASS',
        'files':{p.relative_to(OUT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked}},indent=2)+'\n',encoding='utf-8')
    return 1 if failed else 0


if __name__=='__main__':raise SystemExit(run())
