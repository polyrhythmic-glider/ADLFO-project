"""Preliminary DXF only; real component measurements are still required."""
from pathlib import Path
import ezdxf
from design import PANEL,OLED,RAIL_SLOTS,holes
out=Path(__file__).parent/'output';d=ezdxf.new('R2010');d.units=4;m=d.modelspace();W=PANEL['width'];H=PANEL['height']
for name,color in [('CUT',1),('DRILL',3)]:d.layers.new(name,dxfattribs={'color':color})
m.add_lwpolyline([(0,0),(W,0),(W,H),(0,H)],close=True,dxfattribs={'layer':'CUT'})
for h in holes():m.add_circle((h['x'],H-h['y']),h['diameter']/2,dxfattribs={'layer':'DRILL'})
x=OLED['x']-OLED['width']/2;y=H-OLED['y']-OLED['height']/2
m.add_lwpolyline([(x,y),(x+OLED['width'],y),(x+OLED['width'],y+OLED['height']),(x,y+OLED['height'])],close=True,dxfattribs={'layer':'CUT'})
for x,y0 in RAIL_SLOTS:
 y=H-y0;r=1.6;a=1
 m.add_line((x-a,y-r),(x+a,y-r),dxfattribs={'layer':'CUT'});m.add_line((x-a,y+r),(x+a,y+r),dxfattribs={'layer':'CUT'})
 m.add_arc((x+a,y),r,270,90,dxfattribs={'layer':'CUT'});m.add_arc((x-a,y),r,90,270,dxfattribs={'layer':'CUT'})
d.saveas(out/'panel-concept.dxf')
