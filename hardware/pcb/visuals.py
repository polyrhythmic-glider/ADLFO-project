"""Offline engineering views; not an assembly-height or routing validation."""
from pathlib import Path
from html import escape
import json
import svgwrite
from design import PANEL,PCB,COLUMNS,OLED,RAIL_SLOTS,holes
W,H=PANEL['width'],PANEL['height'];OUT=Path(__file__).parent/'output'
def canvas():return svgwrite.Drawing(size=(f'{W}mm',f'{H}mm'),viewBox=f'0 0 {W} {H}')
def text(d,x,y,s,size=2,fill='#e8eeea',anchor='middle'):d.add(d.text(s,insert=(x,y),font_family='sans-serif',font_size=size,fill=fill,text_anchor=anchor))
def panel(drill=False):
 d=canvas();bg='white' if drill else '#16282e';ink='#182930' if drill else '#e8eeea'
 d.add(d.rect((.1,.1),(W-.2,H-.2),fill=bg,stroke=ink,stroke_width=.2))
 for x,y in RAIL_SLOTS:d.add(d.rect((x-2.6,y-1.6),(5.2,3.2),rx=1.6,fill='none',stroke=ink,stroke_width=.1))
 d.add(d.rect((OLED['x']-13.5,OLED['y']-7.5),(27,15),fill='none' if drill else '#061417',stroke=ink,stroke_width=.15))
 if not drill:
  text(d,69,22,'ADOLFO',6);text(d,69,28,'UNIVERSAL / 20 HP',2)
  text(d,24,24,'PATCH / PRESET',2,'#a3dfcf')
  for i,x in enumerate(COLUMNS,1):text(d,x,38,f'E{i}',2)
 for h in holes():
  r=h['diameter']/2
  if not drill and h['kind']=='ENC':r=8
  if not drill and h['kind'] in ['IN','CTRL','OUT']:r=4
  d.add(d.circle((h['x'],h['y']),r,fill='none' if drill else '#344f55',stroke=ink,stroke_width=.15))
  if not drill and h['kind'] not in ['mount','ENC','KEY']:text(d,h['x'],h['y']+8,h['ref'],2)
 if not drill:text(d,W/2,123,'C / CONCEPT - NOT FOR FABRICATION',1.8,'#f2b880')
 return d

def pcb(parts,name):
 from build import make_footprint,bounds
 d=canvas();d.add(d.rect((PCB['x'],PCB['y']),(PCB['width'],PCB['height']),fill='#164438',stroke='#90b6a1',stroke_width=.3))
 for p in parts:
  if p['board']!=name:continue
  a,b,c,e=bounds(make_footprint(p['footprint']))
  if p['side']=='B':a,c=-c,-a
  rect=d.rect((p['x']+a,p['y']+b),(c-a,e-b),fill='#294e52' if p['side']=='F' else '#37436b',stroke='#c8d4bd',stroke_width=.1)
  rect.set_desc(title=f'{p["ref"]}: {p["value"]}',desc=p['note']);d.add(rect);text(d,p['x'],p['y']+.5,p['ref'],1.1)
 text(d,W/2,7,f'{name.upper()} / ENVELOPES ONLY',2,'#203f46');return d

def render(parts):
 views={'front':panel(),'main':pcb(parts,'main'),'panel':pcb(parts,'panel'),'drill':panel(True)}
 for n,d in views.items():d.saveas(str(OUT/f'{n}.svg'))
 tabs=''.join(f'<button data-view="{n}">{s}</button>' for n,s in [('front','Frontale'),('main','Elettronica'),('panel','PCB frontale'),('drill','Foratura preliminare')])
 figures=''.join(f'<section id="{n}" class="view">{d.tostring()}</section>' for n,d in views.items())
 rows=''.join(f'<tr><td>{p["ref"]}</td><td>{escape(p["value"])}</td><td>{p["board"]}</td><td>{escape(p["note"])}</td></tr>' for p in parts)
 page='''<!doctype html><html lang="it"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Adolfo universal C</title><style>body{font:16px/1.5 system-ui;margin:24px auto;padding:0 20px;max-width:1100px;background:#edf0e9;color:#203b40}h1{font-size:38px}nav{display:flex;gap:8px;flex-wrap:wrap}button,input{padding:10px;border:1px solid #8da6a0;border-radius:6px;background:white}button{cursor:pointer}.view{display:none;margin:20px 0}.view.active{display:block}.view svg{display:block;max-width:100%;height:650px;margin:auto}.notice{background:#f4dfbf;padding:16px;border-left:4px solid #ab681e}table{width:100%;font-size:13px;border-collapse:collapse}td,th{padding:8px;border-bottom:1px solid #bbc9bf;text-align:left}td:last-child{max-width:400px}.scroll{overflow:auto}a{color:#23566b}</style><h1>ADOLFO / Universal C</h1><p>4 IN audio/CV/gate/trigger · 4 OUT audio/CV/envelope/LFO/gate/trigger · 4 CTRL bidirezionali CV/gate/trigger. Pannello 20 HP, quattro encoder con click e quattro tasti.</p><p class="notice"><strong>Progetto elettrico candidato, non sbrogliato.</strong> Filtri analogici antialias/ricostruzione, DMA, regolatore e meccanica restano aperti. Le impronte degli IC sono reali; il convertitore 5 V ha solo un ingombro provvisorio. Il firmware del prototipo non pilota questa scheda.</p><nav>'''+tabs+'</nav>'+figures+'''<p>Due schede sovrapposte: frontale con comandi e jack; elettronica con Daisy, conversione e protezioni. Il posizionamento della scheda elettronica è preliminare e non ottimizzato per le piste.</p><p><a href="Adolfo.kicad_sch">Schema terminale</a> · <a href="Adolfo-main.kicad_pcb">PCB elettronica</a> · <a href="Adolfo-panel.kicad_pcb">PCB frontale</a> · <a href="bom.csv">Distinta candidati</a> · <a href="../README.md">Stato e istruzioni</a></p><input id="search" aria-label="Cerca componenti" placeholder="Cerca componente"><div class="scroll"><table><thead><tr><th>Ref</th><th>Candidato</th><th>Scheda</th><th>Note</th></tr></thead><tbody>'''+rows+'''</tbody></table></div><script>document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v.id===b.dataset.view))});document.querySelector('[data-view]').click();document.querySelector('#search').oninput=e=>document.querySelectorAll('tbody tr').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(e.target.value.toLowerCase()));</script></html>'''
 (OUT/'index.html').write_text(page)
