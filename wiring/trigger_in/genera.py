from pathlib import Path
from html import escape
p=Path(__file__).parent
s=['<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="1370" viewBox="0 0 1500 1370">']
def rect(x,y,w,h,fill,stroke='none',rx=0): s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}"/>')
def text(x,y,t,size=20,color='#172b40',anchor='start'):
 s.append(f'<text x="{x}" y="{y}" font-family="DejaVu Sans,sans-serif" font-size="{size}" fill="{color}" text-anchor="{anchor}">{escape(t)}</text>')
def line(points,color='#485767',w=3):
 s.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in points)+f'" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')
def hole(x,y):s.append(f'<circle cx="{x}" cy="{y}" r="4" fill="#586472"/>')
def x(n): return 200+(n-1)*34
def y(l):return dict(zip('abcdefghij',[320,340,360,380,400,460,480,500,520,540]))[l]
def dot(xx,yy,c):s.append(f'<circle cx="{xx}" cy="{yy}" r="5" fill="{c}"/>')
def resistor(a,b,yy,label):
 xa,xb=x(a),x(b); mid=(xa+xb)/2
 line([(xa,yy),(xb,yy)],'#876244',3)
 rect(mid-40,yy-8,80,16,'#a5d7e7','#387188',4)
 text(xa-12,yy+6,label,17,anchor='end') if label=='100 kΩ' else text(mid,yy-16,label,17,anchor='middle')
 for xx in [xa,xb]:dot(xx,yy,'#876244')
rect(0,0,1500,1370,'#f5f8fc')
text(65,60,'TRIGGER • schema proposto su breadboard',34)
text(65,96,'Un canale · 2N3904 · alimentazione 3,3 V · Daisy scollegata',23)
text(65,139,'Vista dall’alto. Ogni coordinata indica un foro: per esempio f10 = lettera f, numero 10.',20)
rect(145,265,1090,405,'#e6e9e9','#aeb9c2',15)
rect(165,415,1050,27,'#c9d0d4',rx=8)
for n in range(1,31):
 xx=x(n)
 text(xx,295,str(n),15,anchor='middle'); text(xx,571,str(n),15,anchor='middle')
 for l in 'abcdefghij':hole(xx,y(l))
 for yy in [600,640]:hole(xx,yy)
for l in 'abcdefghij':text(171,y(l)+5,l,16)
line([(184,585),(1205,585)],'#2067bd',2);line([(184,655),(1205,655)],'#dc3333',2)
text(120,606,'−',25,'#2067bd');text(120,647,'+',25,'#dc3333')
# Shade / annotate three transistor columns, maintaining hole visibility.
for n,c in [(10,'#1c794b'),(11,'#bd7213'),(12,'#733bc0')]:
 s.append(f'<rect x="{x(n)-10}" y="449" width="20" height="102" rx="7" fill="none" stroke="{c}" stroke-width="2" stroke-dasharray="4 3"/>')
# NPN flat face facing observer, leads E B C left to right.
rect(x(10)-17,409,102,32,'#252e39',rx=5)
text(x(11),431,'2N3904',16,'white','middle')
for n,l in [(10,'E'),(11,'B'),(12,'C')]:
 line([(x(n),441),(x(n),460)],'#777',4);dot(x(n),460,'#252e39');text(x(n),397,l,19,anchor='middle')
# Parts.
resistor(5,11,y('h'),'100 kΩ')
resistor(11,18,y('i'),'1 MΩ')
resistor(12,23,y('g'),'47 kΩ')
line([(x(7),y('g')),(x(11),y('g'))],'#876244',3)
mid=(x(7)+x(11))/2
rect(mid-25,472,50,16,'#bd7254','#75402b',5);rect(mid+15,473,6,14,'#252e39')
text(mid,461,'1N4148',16,anchor='middle')
text(260,452,'Banda verso B →',17,'#925522')
# Ground jumpers.
for n in [7,10,18]:
 line([(x(n),540),(x(n),600)],'#2067bd',5);dot(x(n),540,'#2067bd');dot(x(n),600,'#2067bd')
line([(x(23),540),(x(23),640)],'#dc3333',5)
dot(x(23),540,'#dc3333');dot(x(23),640,'#dc3333')
# Source/probe points.
line([(x(5),540),(x(5),558),(80,558),(80,715)],'#cb7517',5)
dot(x(5),540,'#cb7517');text(65,744,'IN: tip Crave + punta CH1',21,'#a55c09')
line([(x(12),540),(x(12),559),(x(12)+30,559),(x(12)+30,709),(685,709)],'#733bc0',5)
dot(x(12),540,'#733bc0');text(699,716,'OUT: punta CH2',22,'#733bc0')
line([(x(28),640),(x(28),770),(1170,770)],'#dc3333',5)
text(1190,779,'+3,3 V',24,'#c92d2d')
line([(x(30),600),(1280,600),(1280,680)],'#2067bd',5)
text(1260,708,'GND comune',19,'#2067bd')
text(1030,816,'Negativo alimentatore, sleeve Crave,',17,'#2067bd')
text(1030,842,'masse CH1 e CH2 → barra blu.',17,'#2067bd')
# Instructions in separated lower cards.
rect(55,875,680,433,'white','#d1dbe5',12)
text(80,913,'COMPONENTI: inserisci nei fori indicati',23)
rows=[('2N3904','E → f10     B → f11     C → f12'),('100 kΩ','h5 ↔ h11'),('1 MΩ','i11 ↔ i18'),('47 kΩ','g12 ↔ g23'),('1N4148','g7 ↔ g11; banda sul lato g11'),('Ponti GND','j7, j10, j18 → barra blu'),('Ponte +3,3 V','j23 → barra rossa'),('Segnali','IN = j5       OUT = j12')]
for i,(a,b) in enumerate(rows):
 yy=953+i*43;text(80,yy,a,19);text(250,yy,b,18)
rect(765,875,680,433,'white','#d1dbe5',12)
text(790,913,'PRIMA DI COLLEGARE IL CRAVE',23)
notes=['1. Alimentatore spento durante il cablaggio.', '2. Faccia piatta del 2N3904 verso di te:', '   piedini in basso, ordine E–B–C (onsemi TO-92).', '3. Verifica continuità della barra blu e rossa:', '   se sono interrotte a metà, unisci le due metà.', '4. Alimenta a 3,3 V. IN a GND → OUT ≈ 3,3 V.', '5. IN a +3,3 V → OUT ≈ 0–0,3 V.', '   Usa j5: la resistenza 100 kΩ resta in serie.']
for i,t in enumerate(notes):text(790,953+i*39,t,18)
text(65,1346,'I fili che si incrociano NON sono collegati: i contatti sono solo nei fori indicati. Usa esclusivamente le barre inferiori.',18)
s.append('</svg>')
(p/'trigger_breadboard.svg').write_text('\n'.join(s))
