"""Engineering previews derived from the same coordinates and actual KiCad pads."""
import math
from html import escape
import svgwrite
from design import PANEL, PCB, OLED, COLUMNS, COLORS, MOUNTS, RAIL_SLOTS, holes

W,H=PANEL['width'],PANEL['height']

class Canvas:
    def __init__(self,w,h):
        self.d=svgwrite.Drawing(size=(str(w),str(h)),viewBox=f'0 0 {w} {h}')
        self.w,self.h=w,h
    def rect(self,x,y,w,h,fill,stroke='none',sw=.2,r=0):
        self.d.add(self.d.rect((x,y),(w,h),rx=r,fill=fill,stroke=stroke,stroke_width=sw))
    def circle(self,x,y,r,fill,stroke='none',sw=.2):
        self.d.add(self.d.circle((x,y),r,fill=fill,stroke=stroke,stroke_width=sw))
    def text(self,x,y,t,size=2.3,color='#e6e7de',anchor='middle',weight='normal',spacing=0):
        self.d.add(self.d.text(t,insert=(x,y),font_family='DejaVu Sans, sans-serif',font_size=size,
            fill=color,text_anchor=anchor,font_weight=weight,letter_spacing=spacing))
    def line(self,xy,c='#86938d',sw=.2,dash=None):
        obj=self.d.polyline(xy,fill='none',stroke=c,stroke_width=sw,stroke_linecap='round',stroke_linejoin='round')
        if dash:obj.dasharray(dash)
        self.d.add(obj)
    def save(self,path):self.d.saveas(str(path))
    def inner(self):
        s=self.d.tostring();return s[s.index('>')+1:s.rindex('</svg>')]

def panel(technical=False,assembled=True):
    c=Canvas(W,H)
    c.rect(.15,.15,W-.3,H-.3,'#fff' if technical else '#172126','#344047' if not technical else '#111',.3,.8)
    for x,y in RAIL_SLOTS:
        c.rect(x-2.6,y-1.6,5.2,3.2,'#fff' if technical else '#0a1013','#111' if technical else '#465052',.18,1.6)
    for x,y in MOUNTS:
        c.circle(x,y,1.6,'white' if technical else '#7d8581','#111' if technical else '#0b1012',.2)
        if not technical:c.line([(x-.8,y),(x+.8,y)],'#293336',.2)
    if technical:
        for h in holes():
            if h['kind']=='mount':continue
            c.circle(h['x'],h['y'],h['diameter']/2,'none','#111',.1)
            c.line([(h['x']-1,h['y']),(h['x']+1,h['y'])],'#8a9ba3',.08)
            c.line([(h['x'],h['y']-1),(h['x'],h['y']+1)],'#8a9ba3',.08)
        c.rect(OLED['x']-13.5,OLED['y']-7.5,27,15,'none','#111',.1)
        c.text(70,20,'ADLFO · 20 HP',4,'#192d39',weight='bold')
        c.text(70,25,'101.2 × 128.5 mm',2.5,'#192d39')
        c.text(W/2,121,'DIMA 1:1 · QUOTE DA VERIFICARE SUI COMPONENTI',1.7,'#192d39')
        return c
    c.text(49,19,'ADLFO',9.3,anchor='start',weight='bold',spacing=.4)
    c.text(49.5,24,'QUAD ENVELOPE / OSCILLATOR',1.65,'#a4b3b7',anchor='start',spacing=.12)
    c.line([(49.5,28),(93,28)],'#617273',.25)
    for i,color in enumerate(COLORS):c.circle(51+i*4,31,0.65,color)
    c.text(93,31.7,'REV B',1.8,'#a4b3b7','end')
    ox,oy=OLED['x']-13.5,OLED['y']-7.5
    c.rect(ox-.7,oy-.7,28.4,16.4,'#0a1114','#354348',.3,.6)
    c.rect(ox,oy,27,15,'#06252a')
    if assembled:
        c.text(ox+1.6,oy+3.8,'CH 1',3,'#a3efdd','start','bold')
        c.text(ox+25.3,oy+3.5,'AD  EXP',1.5,'#9adacb','end')
        c.line([(ox+2,oy+11),(ox+7,oy+6),(ox+9,oy+8),(ox+12,oy+10),(ox+17,oy+11.6),(ox+25,oy+12)],'#a3efdd',.3)
        c.text(ox+1.6,oy+14,'250 ms     720 ms',1.55,'#91c8c3','start')
    c.line([(10,34.8),(93,34.8)],'#47585e',.2)
    names=['RISE','FALL','SYMMETRY','LEVEL'];small=['TRIG · MODE','CURVE','RESET 50%','RESET 100%']
    for i,(x,color) in enumerate(zip(COLUMNS,COLORS)):
        c.text(x,39,names[i],2.4,weight='bold',spacing=.2)
        for n in range(11):
            a=math.radians(-220+n*26)
            c.line([(x+9.4*math.cos(a),48+9.4*math.sin(a)),(x+9.9*math.cos(a),48+9.9*math.sin(a))],'#627276',.22)
        if assembled:
            c.circle(x+.5,48.7,8.5,'#0d1418')
            c.circle(x,48,8.1,'#39454a','#607075',.25)
            c.circle(x,48,7.3,'#202b31','#10191e',.2)
            for a in range(0,360,15):
                t=math.radians(a);c.line([(x+7.5*math.cos(t),48+7.5*math.sin(t)),(x+7.85*math.cos(t),48+7.85*math.sin(t))],'#718082',.2)
            a=math.radians(-125+i*20)
            c.line([(x+4.7*math.cos(a),48+4.7*math.sin(a)),(x+6.7*math.cos(a),48+6.7*math.sin(a))],color,.65)
        else:c.circle(x,48,3.6,'#080e11','#657274',.2)
        c.text(x,60,small[i],1.6,'#a3afb2',spacing=.12)
        c.circle(x,67,3.45,'#0b1317','#56686a',.22)
        c.circle(x,67,2.7,color)
        c.text(x,73,f'CH {i+1}',2.2,color,weight='bold',spacing=.2)
        c.rect(x-9,103.4,18,14.2,color,r=1)
        for y in [80,95,110]:
            c.circle(x+.3,y+.45,4.7,'#0b1317')
            c.circle(x,y,4.35,'#abb4ae','#d6dbd1',.2)
            c.circle(x,y,3.55,'#465154','#18292c',.2)
            c.circle(x,y,2.6,'#a4afaa')
            c.circle(x,y,1.8,'#070e12','#263235',.2)
            c.circle(x-.45,y-.5,.4,'#526064')
        c.text(x,116.6,str(i+1),1.8,'#172126',weight='bold')
    for t,y in [('TRIG',80),('CV IN',95),('OUT',110)]:c.text(2,y+.8,t,1.35,'#b6c2c1','start','bold')
    c.text(W/2,122,'4 × AD / LFO     •     CV 0–10 V     •     OUT 0–5 V*',1.7,'#a8b7ba',spacing=.08)
    return c

def pcb(board,parts,rear=True,ratsnest=False):
    c=Canvas(W,H);bx,by,bw,bh=[PCB[k] for k in ['x','y','width','height']]
    mx=(lambda x:W-x) if rear else (lambda x:x)
    c.rect(bx,by,bw,bh,'#17483e','#759b78',.5,1)
    c.rect(bx+1,by+1,bw-2,bh-2,'none','#37695a',.2,.7)
    for x,y in MOUNTS:c.circle(mx(x),y,2.65,'#c9b57d');c.circle(mx(x),y,1.6,'#111e22')
    if ratsnest:
        nets={}
        for fp in board.footprints:
            for p in fp.pads:
                if p.net and p.net.name not in ['GND','+3V3','+12VA','-12VA']:
                    nets.setdefault(p.net.name,[]).append((mx(fp.position.X+p.position.X),fp.position.Y+p.position.Y))
        for coords in nets.values():
            for pt in coords[1:]:c.line([coords[0],pt],'#749d85',.12)
    # Actual copper pads, including bottom mirroring already applied by KiUtils generator.
    for fp in board.footprints:
        for p in fp.pads:
            if p.type=='smd' and (fp.layer=='B.Cu')!=rear:continue
            x=mx(fp.position.X+p.position.X);y=fp.position.Y+p.position.Y
            if p.type=='np_thru_hole':c.circle(x,y,p.size.X/2,'#132428');continue
            c.rect(x-p.size.X/2,y-p.size.Y/2,p.size.X,p.size.Y,'#d5c082',r=min(.25,p.size.X/3))
            if p.drill:
                if p.drill.oval:
                    dw,dh=p.drill.diameter,p.drill.width
                    c.rect(x-dw/2,y-dh/2,dw,dh,'#132428',r=min(dw,dh)/2)
                else:c.circle(x,y,p.drill.diameter/2,'#132428')
    for p in parts:
        if (p['side']=='B')!=rear:continue
        x,y=mx(p['x']),p['y'];k=p['footprint'];ref=p['ref']
        if k=='seed':
            c.rect(x-25.5,y-9,51,18,'#223034','#6b897f',.2,.6)
            for i in range(20):
                for py in [y-7.62,y+7.62]:c.rect(x-24.13+i*2.54-.5,py-.8,1,1.6,'#d2bd83')
            c.rect(x-5,y-4.3,8.6,8.6,'#10191e','#4e6364',.15)
            c.rect(x+8,y-3.5,10,7,'#10191e')
            c.rect(x-27,y-3.7,5,7.4,'#a8b7b4','#40504e',.2,.4)
            c.text(x,y-10.7,'U1 / DAISY SEED · SOCKETED',1.6,'#d4e3d5',weight='bold')
            c.text(x,y+1,'STM32',1.2,'#becbc4')
        elif k=='mcp4728_breakout':
            c.rect(x-12.7,y-8.89,25.4,17.78,'#163549','#8ca4a7',.2,.8)
            c.text(x,y-1,'ADAFRUIT',1.7,weight='bold')
            c.text(x,y+2,'MCP4728',1.7)
            c.text(x,y+11,'U2 / SOCKETED',1.3)
        elif k=='radial_cap':
            c.circle(x,y,3.15,'#26343b','#98a8a4',.2)
            c.text(x,y+1,'+',2)
        elif k in ['soic14','msop10']:
            ww,hh=(3.9,8.7) if k=='soic14' else (3,3)
            c.rect(x-ww/2,y-hh/2,ww,hh,'#142025','#455752',.2,.2)
            c.circle(x-ww/2+.6,y-hh/2+.6,.25,'#b9c5ba')
            c.text(x,y+hh/2+2.1,ref,1.5,'#e4ecdf',weight='bold')
        elif k in ['r0805','r2010','c0805']:
            ww,hh=(5,2.5) if k=='r2010' else (2,1.25)
            c.rect(x-ww/2,y-hh/2,ww,hh,'#c4a783' if k=='c0805' else '#152127',r=.1)
            c.text(x,y-1.6,ref,1.15,'#b9d5bf')
        elif k in ['sma','sod123','sot23']:
            ww,hh={'sma':(4.6,2.6),'sod123':(2.7,1.6),'sot23':(1.3,2.9)}[k]
            c.rect(x-ww/2,y-hh/2,ww,hh,'#162126',r=.12)
            c.text(x,y-hh/2-1,ref,1.2,'#d3e2cf')
        elif k=='recom':
            c.rect(x-5.8,y-6.5,11.6,8.5,'#162126','#5a7668',.15,.5)
            c.text(x,y-3,'RECOM',1.5,weight='bold');c.text(x,y-1,'5 V / 0.5 A',1.1)
        elif k=='idc10':
            c.rect(x-4.5,y-10.2,9,20.4,'#142025','#829589',.25,.5)
            c.rect(x-3.3,y-8.6,6.6,17.2,'#0d181c',r=.3)
            for j in range(5):
                for px in [x-1.27,x+1.27]:c.rect(px-.35,y-5.08+j*2.54-.35,.7,.7,'#dbbe79')
            c.rect(x-4.5,y-10.2,9,1.5,'#c5665d')
            c.text(x,y+12.8,'−12V STRIPE ↑',1.6,'#dbe7d4',weight='bold')
        elif k=='testpoint':c.text(x,y-2,ref,1.3,'#dbe7d4')
        elif k=='encoder':c.rect(x-6,y-6,12,12,'#8a9691','#152328',.3,1);c.circle(x,y,3,'#bec5bd')
        elif k=='button':c.rect(x-3,y-3,6,6,'#263139','#9ba69a',.2);c.circle(x,y,1.75,'#778f84')
        elif k=='jack':c.rect(x-4.5,y-6,9,10.5,'#18252b',r=.5);c.circle(x,y,3,'#a1afa5');c.circle(x,y,1.8,'#142025')
        elif k=='oled':c.rect(OLED['x']-13.75,OLED['y']-13.9,27.5,27.8,'#173838','#79948a',.2,.3)
    c.text(W/2,39,'ADLFO  /  B',2.8,'#d3e5d3',weight='bold',spacing=.4)
    c.text(W/2,43,'PLACEMENT · NO ROUTING',1.4,'#9dc3ae',spacing=.15)
    c.text(W/2,118,'KIUTILS → KICAD   /   96.2 × 110.5 mm',1.35,'#c4ddc6')
    return c

def overview(front,back,parts):
    c=Canvas(1800,1100);c.rect(0,0,1800,1100,'#eaeae2')
    c.text(75,62,'ADLFO / HARDWARE STUDY 01',17,'#4b6264','start',spacing=3)
    c.text(75,130,'Quattro canali. Una sola scheda.',48,'#1b3037','start','bold')
    c.text(77,177,'Pannello forato + PCB unica • proposta Eurorack 20 HP • scala e collegamenti condivisi',20,'#576b6c','start')
    c.text(85,231,'01   FRONT PANEL',16,'#3c535a','start','bold',2)
    c.text(930,231,'02   PCB — VISTA DAL RETRO',16,'#3c535a','start','bold',2)
    # Embed real generated vector views without raster approximation.
    body=c.inner()
    body+=f'<g transform="translate(85 255) scale(5.25)">{front.inner()}</g>'
    body+=f'<g transform="translate(925 255) scale(5.25)">{back.inner()}</g>'
    lower=Canvas(1800,1100)
    lower.line([(85,960),(1715,960)],'#b6c0b9',1)
    lower.text(85,998,'101,2 × 128,5 mm',23,'#223b41','start','bold')
    lower.text(85,1029,'Alluminio 2 mm · encoder, pulsanti, 12 jack',17,'#607275','start')
    lower.text(685,998,'4 encoder  /  4 selettori  /  OLED',23,'#223b41','start','bold')
    lower.text(685,1029,'Ingresso TRIG + CV e uscita per ciascun canale',17,'#607275','start')
    lower.text(1715,998,'REV B · PROPOSTA',22,'#8c613b','end','bold')
    lower.text(1715,1029,'PCB da sbrogliare e collaudare',17,'#8c613b','end')
    lower.text(85,1070,'* OUT: obiettivo 0–5 V a vuoto. Modelli dei componenti e distanze dal pannello da verificare sul materiale reale.',14,'#607275','start')
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1100" viewBox="0 0 1800 1100">{body}{lower.inner()}</svg>'

def render(board,parts,out):
    front=panel();back=pcb(board,parts);frontpcb=pcb(board,parts,False);cut=panel(technical=True)
    for name,obj in [('front-panel',front),('pcb-back',back),('pcb-front',frontpcb),('panel-drilling',cut),('pcb-ratsnest',pcb(board,parts,True,True))]:
        obj.save(out/(name+'.svg'))
    # Explicit physical units make 100% PDF/print export a true 1:1 drilling template.
    raw=cut.d.tostring().replace(f'width="{W}"',f'width="{W}mm"').replace(f'height="{H}"',f'height="{H}mm"')
    (out/'panel-drilling-1to1.svg').write_text(raw)
    (out/'overview.svg').write_text(overview(front,back,parts))
    template=(__import__('pathlib').Path(__file__).parent/'viewer-template.html').read_text()
    table=''.join(f'<tr><td>{escape(p["ref"])}</td><td>{escape(p["value"])}</td><td>{p["side"]}</td><td>{p["x"]:g}, {p["y"]:g}</td></tr>' for p in parts)
    for key,val in {'FRONT':front.d.tostring(),'BACK':back.d.tostring(),'PCBFRONT':frontpcb.d.tostring(),'CUT':cut.d.tostring(),
                    'RATSNEST':pcb(board,parts,True,True).d.tostring(),'BOM':table,'COUNT':str(len(parts))}.items():
        template=template.replace('{{'+key+'}}',val)
    (out/'index.html').write_text(template)

