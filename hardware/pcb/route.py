"""Local Specctra routing/import. Run with KiCad's Python after board_setup.py."""
from pathlib import Path
import os
import subprocess
import sys
import pcbnew as pcb

HERE=Path(__file__).parent;OUT=HERE/'output'


def route(name):
    jar=Path(os.environ.get('FREEROUTING_JAR','.venv/tools/freerouting-2.0.1.jar')).resolve()
    if not jar.is_file():raise FileNotFoundError('Install the pinned Freerouting jar; see hardware/pcb/README.md')
    temporary=HERE/'build'/f'{name}-routing.ses';temporary.parent.mkdir(exist_ok=True)
    temporary.unlink(missing_ok=True)
    subprocess.run(['java','-Djava.awt.headless=true','-jar',str(jar),'--gui.enabled=false','-da',
        '-de',str(HERE/'build'/f'Adolfo-{name}.dsn'),'-do',str(temporary),'-mp','80','-mt','2'],check=True)
    if not temporary.is_file():raise RuntimeError('Autorouter did not produce a session; board not changed')
    path=OUT/f'Adolfo-{name}.kicad_pcb';b=pcb.LoadBoard(str(path))
    if not pcb.ImportSpecctraSES(b,str(temporary)):raise RuntimeError('Native session import failed')
    from ground_plane import inset_edge_vias
    inset_edge_vias(b)
    b.GetTitleBlock().SetRevision('D ENGINEERING - BENCH VALIDATION REQUIRED')
    pcb.ZONE_FILLER(b).Fill(b.Zones());pcb.SaveBoard(str(path),b)
    print(name,len(list(b.GetTracks())),'tracks/vias imported; native DRC is required next.')


if __name__=='__main__':
    targets=sys.argv[1:] or ['main','panel']
    if any(n not in ('main','panel') for n in targets):raise SystemExit('Usage: route.py [main|panel]')
    for name in targets:route(name)
