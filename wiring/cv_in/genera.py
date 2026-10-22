"""Quattro CV IN proposti; python3 wiring/cv_in/genera.py."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parent))
from svg_utils import Svg, INK, BLUE, RED, GREEN, PURPLE, ORANGE

W, H = 2600, 1838
COLORS = {1: GREEN, 2: PURPLE, 3: '#ac601e', 4: '#366db0'}
PIN_HOLES = {**{i: f'f{27+i}' for i in range(1, 8)},
             **{i: f'e{42-i}' for i in range(8, 15)}}
CHANNEL_PINS = {1: (3, 2, 1), 2: (5, 6, 7), 3: (10, 9, 8), 4: (12, 13, 14)}


def transform(hole, channel):
    letter, col = hole[0], int(hole[1:])
    if channel in (2, 3):
        col = 62 - col
    if channel in (3, 4):
        letter = dict(zip('abcdefghij', 'jihgfedcba'))[letter]
    return f'{letter}{col}'


class Board:
    def __init__(self):
        kind = self.kind = 'IN'
        self.ic = 'U1'
        self.rail = '3V3_A'
        self.parts, self.wires, self.ports = [], [], []
        self.pin_nets = {}
        for ch, (plus, minus, out) in CHANNEL_PINS.items():
            self.pin_nets[plus] = f'Y{ch}'
            self.pin_nets[minus] = self.pin_nets[out] = f'BUF{ch}'
        self.pin_nets[4], self.pin_nets[11] = 'VDD', 'GND'
        for rail in ('T+', 'T-', 'B+', 'B-'):
            self.wire(rail+'30', rail+'34', 'VDD' if '+' in rail else 'GND', 0)
        self.wire('T+63', 'B+63', 'VDD', 0)
        self.wire('T-62', 'B-62', 'GND', 0)
        self.wire('j31', 'B+31', 'VDD', 0)
        self.wire('a31', 'T-31', 'GND', 0)
        c = 9
        self.part(f'C{c}', 'C', '100 nF', 'd31', 'g31', 'GND', 'VDD', 0)
        self.part(f'C{c+1}', 'E', '10 µF', 'a24', 'a26', 'VDD', 'GND', 0)
        self.wire('b24', 'T+24', 'VDD', 0)
        self.wire('b26', 'T-26', 'GND', 0)
        for ch in range(1, 5):
            t = lambda h: transform(h, ch)
            rail = 'T' if ch > 2 else 'B'
            def add(ref, typ, val, a, b, n1, n2):
                self.part(ref, typ, val, t(a), t(b), n1, n2, ch)
            r, c, d = 4*ch-3, 2*ch-1, 2*ch-1
            add(f'R{r}', 'R', '100 kΩ', 'h3', 'h6', f'IN{ch}', f'X{ch}')
            add(f'R{r+1}', 'R', '33 kΩ', 'i6', 'i9', f'X{ch}', 'GND')
            add(f'R{r+2}', 'R', '10 kΩ', 'g6', 'g11', f'X{ch}', f'Y{ch}')
            add(f'R{r+3}', 'R', '1 kΩ', 'h28', 'h22', f'BUF{ch}', f'ADC{ch}')
            add(f'C{c}', 'C', '10 nF', 'j6', 'j9', f'X{ch}', 'GND')
            add(f'C{c+1}', 'C', '1 nF', 'i22', 'i19', f'ADC{ch}', 'GND')
            add(f'D{d}', 'D', '1N4148', 'h9', 'h11', 'GND', f'Y{ch}')
            add(f'D{d+1}', 'D', '1N4148', 'i11', 'i13', f'Y{ch}', 'VDD')
            for hole, net in [('f9', 'GND'), ('j13', 'VDD'), ('j19', 'GND')]:
                h = t(hole)
                self.wire(h, rail + ('+' if net == 'VDD' else '-') + h[1:], net, ch)
            start = 'f11'
            self.port(t('j3'), f'IN{ch}', f'TIP · CV IN {ch}', ch)
            self.port(t('j22'), f'ADC{ch}', f'ADC{ch} · GPIO da scegliere', ch)
            self.wire(t(start), t('g30'), f'Y{ch}', ch)
            self.wire(t('g28'), t('g29'), f'BUF{ch}', ch)

    def part(self, ref, typ, val, a, b, n1, n2, ch):
        self.parts.append(dict(ref=ref, typ=typ, val=val, a=a, b=b, n1=n1, n2=n2, ch=ch))

    def wire(self, a, b, net, ch):
        self.wires.append(dict(a=a, b=b, net=net, ch=ch))

    def port(self, hole, net, label, ch):
        self.ports.append(dict(hole=hole, net=net, label=label, ch=ch))

    def verify(self):
        # Ogni foro contiene un terminale soltanto. Unione delle strip e dei fili,
        # quindi confronto dei nodi reali con i nodi attesi dello schema.
        occupied, parent, claims = {}, {}, []
        def strip(h):
            if re.fullmatch(r'[TB][+-]\d+', h):
                assert 1 <= int(h[2:]) <= 63
                return h[:2] + ('L' if int(h[2:]) <= 31 else 'R')
            assert re.fullmatch(r'[a-j]\d+', h), h
            assert 1 <= int(h[1:]) <= 63
            return ('top' if h[0] <= 'e' else 'bottom') + h[1:]
        def terminal(h, net, ref):
            assert h not in occupied, f'{self.kind}: {h}: {ref} / {occupied.get(h)}'
            occupied[h] = ref
            n = strip(h); parent[n] = n; claims.append((n, net, ref))
        for pin, h in PIN_HOLES.items():
            terminal(h, self.pin_nets[pin], f'{self.ic}.{pin}')
        for p in self.parts:
            terminal(p['a'], p['n1'], p['ref']+'.1')
            terminal(p['b'], p['n2'], p['ref']+'.2')
        for i, w in enumerate(self.wires):
            for end in ('a', 'b'):
                terminal(w[end], w['net'], f'W{i}.{end}')
        for p in self.ports:
            terminal(p['hole'], p['net'], p['label'])
        def root(n):
            while parent[n] != n:
                n = parent[n]
            return n
        for w in self.wires:
            parent[root(strip(w['a']))] = root(strip(w['b']))
        nets, nodes = {}, {}
        for n, net, ref in claims:
            n = root(n)
            assert n not in nets or nets[n] == net, f'Corto: {ref}: {net}/{nets.get(n)}'
            assert net not in nodes or nodes[net] == n, f'Rete aperta: {net}, {ref}'
            nets[n] = net; nodes[net] = n
        assert len(nodes) == 22
        print(f'BB-{self.kind}: OK, {len(occupied)} terminali in fori distinti, {len(nodes)} reti.')


class Sheet(Svg):
    def __init__(self, title, subtitle):
        super().__init__(W, H)
        self.text(65, 65, title, 42, bold=True)
        self.text(65, 110, subtitle, 25)

    def save(self, name):
        # Dimensioni di pagina A3; viewBox mantiene le coordinate di disegno.
        self.s[0] = f'<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 {W} {H}">'
        path = HERE / f'{name}.svg'
        path.write_text('\n'.join(self.s + ['</svg>']))
        return path


def xy(h):
    if h[0] in 'TB':
        c = int(h[2:]); y = {'T+': 295, 'T-': 335, 'B-': 950, 'B+': 990}[h[:2]]
    else:
        c = int(h[1:]); y = dict(zip('abcdefghij', [430,470,510,550,590,690,730,770,810,850]))[h[0]]
    return 180 + 34*(c-1), y


def draw_board(board):
    s = Sheet(f'BB-{board.kind} · quattro CV {board.kind} · cablaggio foro per foro',
              f'{board.ic} = MCP6004-I/P · breadboard 63 colonne · tacca a sinistra · rosso = {board.rail} / +3,3 V')
    s.text(65, 151, 'Punti pieni = fori di contatto. Incroci senza punto = fili separati. Le barre vanno rese continue con i ponti.', 23)
    s.box(110, 260, 2270, 780, '#e9eeee', '#b7c4cc', 16)
    s.box(135, 615, 2220, 52, '#c9d4d8', radius=8)
    for col in range(1, 64):
        x, _ = xy(f'a{col}')
        s.text(x, 391, str(col), 18, anchor='middle')
        s.text(x, 900, str(col), 18, anchor='middle')
        for row in 'abcdefghij':
            s.dot(*xy(row+str(col)), '#84939c', 4)
        for rail in ('T+', 'T-', 'B-', 'B+'):
            s.dot(*xy(rail+str(col)), '#84939c', 4)
    for row in 'abcdefghij':
        s.text(130, xy(row+'1')[1]+6, row, 22)
    for y, color, sign in [(278, RED, '+'),(352, BLUE, '−'),(933, BLUE, '−'),(1007, RED, '+')]:
        s.line([(163,y),(2327,y)], color, 2)
        s.text(82,y+7,sign,28,color)
    left, right = xy('f28')[0]-20, xy('f34')[0]+20
    s.box(left, 612, right-left, 56, '#273845', '#182734', 7)
    s.path(f'M{left} 625 Q{left+20} 640 {left} 655', '#c9d4d8', '#182734', 2)
    s.dot(left+15,658,'white',3)
    for pin, h in PIN_HOLES.items():
        x,y = xy(h)
        s.line([(x,668 if h[0]=='f' else 612),(x,y)],'#667a88',6)
        s.text(x,657 if h[0]=='f' else 626,str(pin),13,'white','middle')
    s.text(left+44,646,board.ic,20,'white',bold=True)
    for w in board.wires:
        a,b,net,ch = w['a'],w['b'],w['net'],w['ch']
        ax,ay=xy(a); bx,by=xy(b)
        color = RED if net=='VDD' else BLUE if net=='GND' else COLORS[ch]
        route=[]
        if a[:2] == b[:2] and a[0] in 'TB':
            yy = ay - 14 if '+' in a else ay + 14
            route = [(ax,yy),(bx,yy)]
        elif a in ('T+63','T-62'):
            xx=2440 if '+' in a else 2408
            route=[(xx,ay),(xx,by)]
        elif net.startswith('Y'):
            yy=678 if ch<=2 else 602
            route=[(ax,yy),(bx,yy)]
        elif b[0] in 'TB' and a[0] in 'fa':
            # Passa fra i numeri senza cancellarli.
            route=[(ax+15,ay-15),(ax+15,by)]
        s.line([(ax,ay)]+route+[(bx,by)],color,5,True)
        s.dot(ax,ay,color);s.dot(bx,by,color)
    for p in board.parts:
        ax,ay=xy(p['a']);bx,by=xy(p['b']);mx,my=(ax+bx)/2,(ay+by)/2
        if ay!=by:
            mx=ax+16
            s.line([(ax,ay),(mx,ay+20),(mx,by-20),(bx,by)],'#83684c',3,True)
        else:
            s.line([(ax,ay),(bx,by)],'#83684c',3,True)
        if p['typ']=='R':
            s.box(mx-27,my-11,54,22,'#bcdfed','#578094',4)
            s.text(mx,my+6,p['ref'],16,INK,'middle',True)
        elif p['typ']=='D':
            s.box(mx-23,my-11,46,22,'#d99c7c','#8c6045',4)
            s.box(mx+(13 if bx>ax else -19),my-10,6,20,'#263443')
            s.text(mx,my+5,p['ref'],14,INK,'middle',True)
            s.text(bx+(8 if bx>ax else -8),by-11,'K',14,ORANGE,'start' if bx>ax else 'end')
        elif p['typ']=='E':
            s.box(mx-18,my-19,36,38,'#456b84','#213f54',7)
            s.box(mx+9,my-17,6,34,'#d8e0e4',2)
            s.text(mx-26,my-10,'+',20,RED,'end',True)
            s.text(mx,my+5,p['ref'],14,'white','middle',True)
        else:
            s.dot(mx,my,'#d79a3f',15)
            s.text(mx+(23 if ay!=by else 0),my+5,p['ref'],14,'white' if ay!=by else INK,'start' if ay!=by else 'middle',True)
        s.dot(ax,ay,'#83684c',4);s.dot(bx,by,'#83684c',4)
    for p in board.ports:
        x,y=xy(p['hole']); top=p['ch']>2; target=225 if top else 1100
        xx=x-16 if int(p['hole'][1:])<31 else x+16
        s.line([(x,y),(xx,y-20 if top else y+20),(xx,target)],COLORS[p['ch']],5,True)
        s.dot(x,y,COLORS[p['ch']],6)
        s.text(xx,194 if top else 1135,p['label'],22,COLORS[p['ch']],'middle',True)
        s.text(xx,220 if top else 1164,f"foro {p['hole']}",19,INK,'middle')
    # Quattro schede montaggio, una per canale.
    for ch in range(1,5):
        x=55+(ch-1)*630
        s.box(x,1210,605,510,'white','#d4dfe6',12)
        s.text(x+20,1252,f'CANALE {ch}',27,COLORS[ch],bold=True)
        rows=[]
        for p in board.parts:
            if p['ch']==ch:
                ends=f"A {p['a']} · K {p['b']}" if p['typ']=='D' else f"{p['a']}–{p['b']}"
                rows.append(f"{p['ref']} {p['val']}  {ends}")
        for w in board.wires:
            if w['ch']==ch:
                rows.append(f"Filo {w['a']} → {w['b']}")
        for i,row in enumerate(rows):
            s.text(x+20,1290+29*i,row,20)
    s.text(65,1761,f"{board.ic}: pin 1…7 = f28…f34; pin 14…8 = e28…e34. Pin 4 → rossa; pin 11 → blu. Barre T = sopra, B = sotto.",23)
    c=9
    s.text(65,1803,f"C{c} 100 nF: d31–g31 sopra {board.ic}, reofori isolati. C{c+1} 10 µF: +a24 / −a26; b24 → T+24, b26 → T−26.",22)
    return s.save('breadboard')


def resistor(s,x1,y1,x2,y2,label):
    s.line([(x1,y1),(x2,y2)])
    x,y=(x1+x2)/2,(y1+y2)/2
    if y1==y2:
        s.box(x-43,y-12,86,24,'white',INK)
        s.text(x,y-27,label,23,anchor='middle')
    else:
        s.box(x-12,y-28,24,56,'white',INK)
        s.text(x+24,y+8,label,22)


def ground(s,x,y):
    s.line([(x,y),(x,y+10)])
    for dy,half in [(10,18),(18,12),(26,5)]:
        s.line([(x-half,y+dy),(x+half,y+dy)],BLUE)


def cap(s,x,y1,y2,label):
    y=(y1+y2)/2
    s.line([(x,y1),(x,y-6)]);s.line([(x,y+6),(x,y2)])
    for yy in [y-6,y+6]:s.line([(x-18,yy),(x+18,yy)])
    s.text(x+28,y+7,label,22)


def diode(s,x,y1,y2,label):
    y=(y1+y2)/2
    s.line([(x,y1),(x,y-17)]);s.line([(x,y+17),(x,y2)])
    s.line([(x-16,y-17),(x+16,y-17)],INK,5)
    s.path(f'M{x-16} {y+17} L{x+16} {y+17} L{x} {y-17} Z')
    s.text(x+27,y+6,label,22);s.text(x-25,y-22,'K',16,ORANGE)


def amp(s,x,y,ic,ch):
    plus,minus,out=CHANNEL_PINS[ch];color=COLORS[ch]
    s.path(f'M{x} {y-50} L{x} {y+110} L{x+170} {y+30} Z','#f0f8f5',color)
    s.text(x+14,y+6,'+',27,color);s.text(x+14,y+72,'−',27,color)
    s.text(x-13,y-13,str(plus),21,color,'end')
    s.text(x-13,y+91,str(minus),21,color,'end')
    s.text(x+175,y+14,str(out),21,color)
    s.text(x+70,y+43,ic+'ABCD'[ch-1],25,color,'middle',True)
    s.line([(x+170,y+30),(x+260,y+30)])
    s.dot(x+220,y+30)
    s.line([(x+220,y+30),(x+220,y+130),(x-55,y+130),(x-55,y+65),(x,y+65)])


def schema_in():
    s=Sheet('4 CV IN · schema elettrico completo', 'U1 MCP6004-I/P · alimentazione 3V3_A · ingressi unipolari 0–10 V · proposta da montare e verificare')
    for ch in range(1,5):
        top=160+(ch-1)*340;y=top+125;r=4*ch-3;c=2*ch-1;d=2*ch-1
        s.box(55,top,2490,320,'white','#d4dfe6',12)
        s.text(80,top+42,f'CV IN {ch}',28,COLORS[ch],bold=True)
        s.text(110,y-23,'Tip',22)
        resistor(s,110,y,420,y,f'R{r} 100 kΩ')
        s.line([(420,y),(810,y)]);resistor(s,810,y,1040,y,f'R{r+2} 10 kΩ')
        s.line([(1040,y),(1640,y)])
        for x in [450,710,1110,1360]:s.dot(x,y)
        s.text(474,y-21,f'X{ch}',24,COLORS[ch]);s.text(1520,y-21,f'Y{ch}',24,COLORS[ch])
        resistor(s,450,y,450,y+125,f'R{r+1} 33 kΩ');ground(s,450,y+125)
        cap(s,710,y,y+125,f'C{c} 10 nF');ground(s,710,y+125)
        diode(s,1110,y,y+125,f'D{d}');ground(s,1110,y+125)
        diode(s,1360,y-73,y,f'D{d+1}');s.text(1360,y-87,'3V3_A',23,RED,'middle',True)
        amp(s,1640,y,'U1',ch)
        resistor(s,1900,y+30,2140,y+30,f'R{r+3} 1 kΩ')
        s.line([(2140,y+30),(2490,y+30)])
        s.dot(2170,y+30);cap(s,2170,y+30,y+145,f'C{c+1} 1 nF');ground(s,2170,y+145)
        s.text(2490,y-26,f'ADC{ch} → GPIO da scegliere',26,COLORS[ch],'end',True)
        s.text(2490,y+7,'collegare dopo il collaudo',22,COLORS[ch],'end')
        s.text(80,top+299,'Sleeve → GND · diodi 1N4148 · K = banda · il buffer resta fra clamp e ADC.',22)
    s.box(55,1540,2490,190,'white','#d4dfe6',12)
    s.text(80,1587,'U1: pin 4 → 3V3_A (Seed3 21); pin 11 → GND (Seed3 20 + 40).',27,bold=True)
    s.text(80,1630,'C9 100 nF e C10 10 µF fra pin 4 e GND; positivo C10 sul +3,3 V. Le quattro sezioni sono tutte utilizzate.',25)
    s.text(80,1674,'Valori attesi su ogni ADC: IN 0 V → ≈0 V; 3,3 V → 0,819 V; 5 V → 1,241 V; 10 V → 2,481 V.',25)
    s.text(80,1710,'V_ADC ≈ V_IN × 33/133. Non misurare tensioni negative; niente patch attive sul circuito spento.',23)
    s.text(65,1798,'Proposta di circuito; pin Daisy e cablaggio effettivo da confermare.',22)
    return s.save('schema')


def main():
    board=Board(); board.verify()
    paths=[schema_in(),draw_board(board)]
    with tempfile.TemporaryDirectory(prefix='adlfo-cv-') as tmp:
        env=os.environ|{'INKSCAPE_PROFILE_DIR':tmp+'/inkscape','XDG_CACHE_HOME':tmp+'/cache'}
        for source in paths:
            subprocess.run(['inkscape',str(source),'--export-width=2600',f'--export-filename={source.with_suffix(".png")}'],check=True,env=env)
if __name__=='__main__': main()
