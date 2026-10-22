"""Breadboard TL074 x4 + MCP4728 + jack: disegno e verifica delle reti.

python3 wiring/out_tl074/genera.py
"""
from pathlib import Path
import os
import re
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parent))
from svg_utils import Svg

W, H = 3300, 2350
INK, MUTED = '#203443', '#566c7c'
RED, NEG, GND = '#cb3346', '#2863ce', '#263541'
COLORS = {1: '#12836f', 2: '#ba6714', 3: '#7845ae', 4: '#147aa1'}
PINS = {**{p: f'f{27+p}' for p in range(1, 8)},
        **{p: f'e{42-p}' for p in range(8, 15)}}
CHANNELS = {1: (3, 2, 1), 2: (5, 6, 7), 3: (10, 9, 8), 4: (12, 13, 14)}
RAILS = {'TG': (620, 'GND', GND), 'TN': (660, 'P_MINUS', NEG),
         'BG': (1280, 'GND', GND), 'BP': (1320, 'P_PLUS', RED)}


def transform(h, ch):
    row, col = h[0], int(h[1:])
    if ch in (2, 3): col = 62 - col
    if ch in (3, 4): row = dict(zip('abcdefghij', 'jihgfedcba'))[row]
    return f'{row}{col}'


def xy(h):
    if h[:2] in RAILS:
        col, y = int(h[2:]), RAILS[h[:2]][0]
    else:
        col = int(h[1:])
        y = dict(zip('abcdefghij', (780,820,860,900,940,1040,1080,1120,1160,1200)))[h[0]]
    return 500 + 36 * (col - 1), y


class Board:
    def __init__(self):
        self.parts, self.wires, self.ports = [], [], []
        self.pin_nets = {4: 'P_PLUS', 11: 'P_MINUS'}
        for ch, (plus, minus, out) in CHANNELS.items():
            self.pin_nets.update({plus: f'P{ch}', minus: f'M{ch}', out: f'O{ch}'})
            t = lambda h: transform(h, ch)
            r = 30 + (ch - 1) * 4
            for ref, value, a, b, n1, n2 in (
                (r, '10k', 'h3', 'h9', f'DAC{ch}', f'P{ch}'),
                (r+1, '10k', 'i15', 'i19', f'M{ch}', 'GND'),
                (r+2, '15k', 'h15', 'h23', f'M{ch}', f'O{ch}'),
                (r+3, '2,2k', 'i28', 'i22', f'O{ch}', f'OUT{ch}')):
                self.parts.append(dict(ref=f'R{ref}', value=value, a=t(a), b=t(b), n1=n1, n2=n2, ch=ch, kind='R'))
            for a, b, net, role in (
                ('f9', 'g30', f'P{ch}', 'plus'),
                ('g15', 'g29', f'M{ch}', 'minus'),
                ('g23', 'h28', f'O{ch}', 'out')):
                self.wire(t(a), t(b), net, ch, role)
            ground = 'BG' if ch < 3 else 'TG'
            h = t('j19')
            self.wire(h, ground+h[1:], 'GND', ch)
            self.port(t('j3'), f'DAC{ch}', f'V{"ABCD"[ch-1]}', ch)
            self.port(t('j22'), f'OUT{ch}', f'TIP OUT{ch}', ch)
            self.port(ground+t('j22')[1:], 'GND', f'SLEEVE OUT{ch}', ch)

        self.parts += [dict(ref='C19', value='100nF', kind='C', a='j31', b='j36', n1='P_PLUS', n2='GND', ch=0),
                       dict(ref='C20', value='100nF', kind='C', a='a31', b='a36', n1='P_MINUS', n2='GND', ch=0)]
        self.wire('g31', 'BP31', 'P_PLUS')
        self.wire('h36', 'BG36', 'GND')
        self.wire('d31', 'TN31', 'P_MINUS')
        self.wire('c36', 'TG36', 'GND')
        self.wire('TG63', 'BG63', 'GND', role='ground_link')
        for rail, (_, net, _) in RAILS.items():
            self.wire(rail+'30', rail+'34', net, role='rail_bridge')
        self.port('BP2', 'P_PLUS', 'P_PLUS')
        self.port('TN2', 'P_MINUS', 'P_MINUS')
        self.port('TG2', 'GND', 'ALIM GND')
        self.port('TG3', 'GND', 'MCP GND')

    def wire(self, a, b, net, ch=0, role='wire'):
        self.wires.append(dict(a=a, b=b, net=net, ch=ch, role=role))

    def port(self, hole, net, label, ch=0):
        self.ports.append(dict(hole=hole, net=net, label=label, ch=ch))

    def verify(self):
        occupied, parent, claims = {}, {}, []
        def strip(h):
            if h[:2] in RAILS:
                col = int(h[2:])
                assert 1 <= col <= 63
                return h[:2] + ('L' if col <= 31 else 'R')
            assert re.fullmatch(r'[a-j][0-9]+', h), h
            assert 1 <= int(h[1:]) <= 63
            return ('top' if h[0] <= 'e' else 'bottom') + h[1:]
        def terminal(h, net, label):
            assert h not in occupied, (h, label, occupied.get(h))
            occupied[h] = label
            n = strip(h)
            parent.setdefault(n, n)
            claims.append((n, net, label))
        def root(n):
            while parent[n] != n: n = parent[n]
            return n
        for p, h in PINS.items(): terminal(h, self.pin_nets[p], f'U2.{p}')
        for p in self.parts:
            terminal(p['a'], p['n1'], p['ref']+'.1')
            terminal(p['b'], p['n2'], p['ref']+'.2')
        for i, w in enumerate(self.wires):
            for end in ('a', 'b'): terminal(w[end], w['net'], f'W{i}.{end}')
        for p in self.ports: terminal(p['hole'], p['net'], p['label'])
        for w in self.wires: parent[root(strip(w['a']))] = root(strip(w['b']))
        nets, nodes = {}, {}
        for n, net, label in claims:
            n = root(n)
            assert n not in nets or nets[n] == net, ('CORTO', net, nets.get(n), label)
            assert net not in nodes or nodes[net] == n, ('APERTO', net, label)
            nets[n], nodes[net] = net, n
        assert len(nodes) == 23
        assert len(self.parts) == 18
        print(f'OK: {len(occupied)} terminali distinti, 23 reti, 16 resistenze, 2 condensatori; rail spezzati ponticellati.')


def dotwire(s, pts, color, width=5):
    s.line(pts, color, width, True)
    s.dot(*pts[0], color, 6)
    s.dot(*pts[-1], color, 6)


def draw(board):
    s = Svg(W, H)
    s.text(65, 70, 'ADLFO  |  MCP4728 + TL074 + 4 jack OUT', 48, bold=True)
    s.text(65, 118, 'Stadio finale previsto: DAC 0–2 V → guadagno 2,5 → OUT circa 0–5 V a vuoto', 29, MUTED)
    s.text(65, 159, 'Vista dall’alto · proposta foro per foro da collaudare · nessun collegamento ai CV IN', 23, MUTED)

    # Power source is the already protected / filtered part of the project.
    s.box(65, 210, 660, 320, 'white', '#c8d4de', 15)
    s.text(90, 252, 'ALIMENTAZIONI SEPARATE', 28, bold=True)
    s.text(90, 296, 'MCP4728: 3,3 V dalla Daisy via QT', 25)
    s.text(90, 340, 'TL074: P_PLUS / GND / P_MINUS', 25)
    s.text(90, 378, 'Rail Eurorack già protetti e filtrati:', 23, MUTED)
    s.text(90, 414, 'circa +11…12 V / 0 V / −11…12 V', 25, bold=True)
    s.text(90, 456, 'USB da sola NON alimenta il TL074.', 24, RED, bold=True)
    s.text(90, 495, 'Mai portare ±12 V al MCP4728.', 24, RED, bold=True)

    s.box(450, 580, 2340, 800, '#e8eeee', '#b3c2cc', 18)
    s.box(472, 962, 2294, 56, '#ccd6dc', radius=8)
    s.text(500, 565, 'Breadboard 63 colonne — ogni colonna a–e è unita; ogni colonna f–j è unita; il canale centrale le separa.', 22)
    for c in range(1, 64):
        x = xy('a'+str(c))[0]
        s.text(x, 743, str(c), 17, anchor='middle')
        s.text(x, 1250, str(c), 17, anchor='middle')
        for row in 'abcdefghij': s.dot(*xy(row+str(c)), '#8a9aa4', 4)
        for rail in RAILS: s.dot(*xy(rail+str(c)), '#8a9aa4', 4)
    for row in 'abcdefghij': s.text(468, xy(row+'1')[1]+6, row, 22)
    for rail, (y, net, color) in RAILS.items():
        s.line([(485, y-13), (1598, y-13)], color, 3)
        s.line([(1635, y-13), (2750, y-13)], color, 3)
        text = {'TG': 'TG · GND', 'TN': 'TN · −12 V*', 'BG': 'BG · GND', 'BP': 'BP · +12 V*'}[rail]
        s.text(2905, y+8, text, 27, color, bold=True)
    s.text(2905, 720, '* Rail dopo le protezioni', 19, MUTED)
    s.text(2905, 750, 'P_PLUS / P_MINUS.', 19, MUTED)
    s.text(2905, 815, 'Etichetta le barre', 23, bold=True)
    s.text(2905, 850, 'come nel disegno.', 23)
    s.text(2905, 900, 'GND ≠ −12 V', 27, RED, bold=True)
    s.text(2905, 1000, 'Ponti 30 ↔ 34:', 23, bold=True)
    s.text(2905, 1037, 'uniscono le due metà', 21)
    s.text(2905, 1072, 'di ciascuna barra.', 21)
    s.text(2905, 1135, 'TG e BG sono unite', 21)
    s.text(2905, 1170, 'dal filo a destra.', 21)

    # DIP-14 with notch on the left, pin 1 at the bottom left.
    left, right = xy('f28')[0]-20, xy('f34')[0]+20
    s.box(left, 960, right-left, 60, '#273745', '#182530', 7)
    s.path(f'M{left} 973 Q{left+22} 990 {left} 1007', '#ccd6dc', '#182530', 2)
    s.dot(left+16,1009,'white',3)
    for pin, h in PINS.items():
        x,y = xy(h)
        s.line([(x,1020 if h[0]=='f' else 960),(x,y)], '#687d8b', 7)
        s.text(x,1011 if h[0]=='f' else 977,str(pin),14,'white','middle')
    s.text((left+right)/2,1000,'TL074',25,'white','middle',True)
    s.text((left+right)/2,1430,'U2 · DIP-14 · tacca a sinistra',25,INK,'middle',True)

    for w in board.wires:
        a,b,ch,net = w['a'],w['b'],w['ch'],w['net']
        ax,ay = xy(a); bx,by = xy(b)
        color = RED if net=='P_PLUS' else NEG if net=='P_MINUS' else GND if net=='GND' else COLORS[ch]
        route = []
        if w['role'] in ('plus','minus','out'):
            yy = {'plus':1030,'minus':1060,'out':1100}[w['role']]
            if ch > 2: yy = 1980-yy
            route = [(ax,yy),(bx,yy)]
        elif w['role']=='ground_link': route=[(2845,ay),(2845,by)]
        elif w['role']=='rail_bridge': route=[(ax,ay-23),(bx,by-23)]
        elif net=='GND' and a[0] in 'aj':
            xx=ax+13
            route=[(xx,ay-18 if ch>2 else ay+18),(xx,by)]
        dotwire(s, [(ax,ay)]+route+[(bx,by)], color, 4 if w['role']=='rail_bridge' else 5)

    for p in board.parts:
        ax,ay=xy(p['a']); bx,by=xy(p['b']); mx,my=(ax+bx)/2,(ay+by)/2
        s.line([(ax,ay),(bx,by)], '#846e4c', 3, True)
        if p['kind']=='R':
            s.box(mx-42,my-14,84,28,'#cee4ee','#7393a4',5)
            s.text(mx,my+7,p['value'],19,INK,'middle',True)
            s.text(mx,my-23,p['ref'],16,COLORS[p['ch']],'middle',True)
        else:
            s.dot(mx,my,'#ce8a2b',19)
            s.text(mx,my+6,'104',14,'white','middle',True)
            s.text(mx,my-30,p['ref']+' · 100 nF',20,INK,'middle',True)
        s.dot(ax,ay,'#846e4c',5);s.dot(bx,by,'#846e4c',5)

    # DAC board is intentionally a labelled block, not a claimed footprint.
    s.box(65, 800, 310, 380, '#126250', '#064b3b', 14)
    for x in (88,352):
        for y in (822,1158): s.dot(x,y,'#d3dce0',8)
    s.text(220,855,'MCP4728',32,'white','middle',True)
    s.text(220,889,'breakout Adafruit',20,'#d6eae4','middle')
    s.box(140,920,90,100,'#24313c','#182530',5)
    s.text(185,978,'DAC',22,'white','middle',True)
    s.text(85,1052,'LDAC → GND',22,'white')
    s.text(85,1090,'RDY: libero',22,'white')
    s.text(85,1130,'GND',22,'white')
    s.dot(375,1123,GND,7)
    dotwire(s,[(375,1123),(405,1123),(405,620),xy('TG3')],GND,5)
    for ch in (1,2,3,4):
        y = 925 + (ch-1)*42
        color = COLORS[ch]
        s.text(338,y+7,'V'+'ABCD'[ch-1],24,'white','end',True)
        s.dot(375,y,color,7)
        h=transform('j3',ch); x,hy=xy(h)
        if ch==1: pts=[(375,y),(420,y),(420,hy),(x,hy)]
        elif ch==2: pts=[(375,y),(435,y),(435,1410),(x,1410),(x,hy)]
        elif ch==3: pts=[(375,y),(430,y),(430,540),(x,540),(x,hy)]
        else: pts=[(375,y),(415,y),(415,hy),(x,hy)]
        dotwire(s,pts,color)
        s.text(x+(15 if ch in (1,4) else -15),hy+(28 if ch<3 else -20),
               f'V{"ABCD"[ch-1]} → {h}',22,color,'start' if ch in (1,4) else 'end',True)

    s.text(65,1230,'Blocco per sigle: segui le scritte',19,MUTED)
    s.text(65,1260,'sul tuo breakout, non la posizione',19,MUTED)
    s.text(65,1290,'grafica dei suoi piedini.',19,MUTED)
    s.box(65,1350,310,360,'white','#c8d4de',12)
    s.text(85,1390,'STEMMA QT',26,bold=True)
    s.text(85,1428,'verso DAISY:',23)
    for i,(label,color) in enumerate((('rosso: 3V3_D · 38',RED),('nero: DGND · 40',GND),('blu: SDA · D12/13',NEG),('giallo: SCL · D11/12','#a67e13'))):
        s.text(85,1471+i*40,label,21,color,bold=True)
    s.text(85,1645,'Dn / pin fisico',18,MUTED)
    s.text(85,1680,'SDA/SCL condivisi con OLED.',16,MUTED)

    # Power feed endpoints: each is already downstream of the protection block.
    for label,h,color,y in [('GND','TG2',GND,560),('P_MINUS','TN2',NEG,590),('P_PLUS','BP2',RED,1350)]:
        x,hy=xy(h)
        start=(470,y)
        dotwire(s,[start,(x-10,y),(x-10,hy), (x,hy)],color)
        s.text(480,y-10,label,20,color,bold=True)

    # Four physical jack illustrations with distinct tip/sleeve leads.
    for ch in (1,2,3,4):
        color=COLORS[ch]; top=ch>2
        cx=xy(transform('j22',ch))[0]
        cy=330 if top else 1600
        s.box(cx-190,cy-105,380,210,'white','#c7d5df',14)
        s.text(cx,cy-63,f'OUT {ch} · J{ch+8}',30,color,'middle',True)
        s.dot(cx,cy+4,'#a5b3be',45)
        s.dot(cx,cy+4,'#334554',34)
        s.dot(cx,cy+4,'#121c23',21)
        s.text(cx,cy+80,'≈ 0–5 V',24,INK,'middle',True)
        ty=cy+105 if top else cy-105
        tip=(cx-65,ty); sleeve=(cx+90,ty)
        h=transform('j22',ch); x,hy=xy(h)
        via=cy+160 if top else cy-150
        dotwire(s,[tip,(tip[0],via),(x,via),(x,hy)],color)
        rail=('TG' if top else 'BG')+h[1:]
        gx,gy=xy(rail)
        dotwire(s,[sleeve,(sleeve[0],via+20 if top else via-20),(gx+16,via+20 if top else via-20),(gx+16,gy),(gx,gy)],GND,4)
        s.text(tip[0]-12,ty+(30 if top else -14),'TIP',20,color,'end',True)
        s.text(sleeve[0]+10,ty+(30 if top else -14),'SLEEVE',18,GND,bold=True)
        s.text(x-15,hy+(25 if top else -18),h,22,color,'end',True)

    s.text(2650,290,'GUADAGNO PER CANALE',25,INK,'middle',True)
    s.text(2650,335,'1 + 15k / 10k = 2,5',31,INK,'middle',True)
    s.text(2650,380,'0 / 1 / 2 V dal DAC',25,MUTED,'middle')
    s.text(2650,420,'↓',30,MUTED,'middle')
    s.text(2650,460,'0 / 2,5 / 5 V prima delle 2,2k',25,INK,'middle',True)

    s.text(500,1755,'Punti pieni = terminali nei fori. Incroci senza punto = fili isolati, NON giunzioni. Resistenze 1%; le 2,2k sono da 0,5 W.',24)
    for ch in range(1,5):
        x=65+(ch-1)*800
        s.box(x,1800,770,360,'white','#cbd7df',12)
        plus,minus,out=CHANNELS[ch]
        s.text(x+20,1840,f'OUT {ch}  ·  TL074 +{plus} / −{minus} / uscita {out}',26,COLORS[ch],bold=True)
        lines=[]
        for p in board.parts:
            if p['ch']==ch: lines.append(f"{p['ref']} {p['value']}   {p['a']} ↔ {p['b']}")
        for w in board.wires:
            if w['ch']==ch: lines.append(f"Filo: {w['a']} ↔ {w['b']}")
        lines.append(f"V{'ABCD'[ch-1]} → {transform('j3',ch)}; tip → {transform('j22',ch)}")
        for i,line in enumerate(lines): s.text(x+20,1880+i*29,line,22)
    s.text(65,2210,'U2: pin 1…7 = f28…f34; pin 14…8 = e28…e34. Pin 4 → P_PLUS; pin 11 → P_MINUS. Feedback 15k PRIMA della 2,2k.',23,bold=True)
    s.text(65,2252,'C19: j31–j36, C20: a31–a36, entrambi 100 nF / ≥50 V verso GND. Alimentazione protetta/filtrata a monte non disegnata.',23)
    s.text(65,2294,'Quattro uscite; verificare il firmware effettivamente caricato. Montaggio non ancora collaudato contro errori di patch, ESD o modulo spento.',23,MUTED)
    path=HERE/'breadboard_mcp4728_tl074_4out.svg'
    s.s[0]=f'<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="299.09mm" viewBox="0 0 {W} {H}">'
    path.write_text('\n'.join(s.s+['</svg>']))
    return path


if __name__=='__main__':
    b=Board(); b.verify()
    source=draw(b)
    with tempfile.TemporaryDirectory(prefix='adlfo-tl074-') as tmp:
        env=os.environ | {'INKSCAPE_PROFILE_DIR':tmp+'/profile','XDG_CACHE_HOME':tmp+'/cache'}
        for ext in ('png','pdf'):
            cmd=['inkscape',str(source),f'--export-filename={source.with_suffix("."+ext)}']
            if ext=='png': cmd.append('--export-width=3300')
            subprocess.run(cmd,check=True,env=env)
    print('Creati SVG, PNG e PDF.')
