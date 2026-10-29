"""Candidate-only repair of three native SMD drill intersections on main PCB."""
from pathlib import Path
import hashlib
import json
import shutil
import pcbnew as pcb

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output'
WORK=ROOT/'build'/'via-layout-candidate'
WORK.mkdir(exist_ok=True)
SOURCE=OUT/'Adolfo-main.kicad_pcb'
BASE=WORK/'before.kicad_pcb'
if not BASE.exists():shutil.copy2(SOURCE,BASE)
assert hashlib.sha256(BASE.read_bytes()).digest()==hashlib.sha256(SOURCE.read_bytes()).digest(), 'Source changed after candidate baseline'
b=pcb.LoadBoard(str(SOURCE));gnd=b.FindNet('GND').GetNetCode()
point=lambda x,y:pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y))
old_bottom=point(36.815,34.338);new_bottom=point(36.0,34.338)
old_top=point(36.815,27.732);new_top=point(36.0,27.732)
changed=[]
for t in list(b.GetTracks()):
    if isinstance(t,pcb.PCB_VIA) or t.GetNetname()!='+3V3' or t.GetLayer()!=pcb.F_Cu:continue
    touched=False
    for which in ('Start','End'):
        at=getattr(t,'Get'+which)()
        if at==old_bottom:getattr(t,'Set'+which)(new_bottom);touched=True
        if at==old_top:getattr(t,'Set'+which)(new_top);touched=True
    if touched:changed.append(t)
assert len(changed)==4
for old,new in [(point(37.475,28.25),point(36.6,28.25)),
                (point(37.475,29.75),point(36.6,29.75))]:
    vias=[t for t in b.GetTracks() if isinstance(t,pcb.PCB_VIA) and t.GetPosition()==old]
    assert len(vias)==1 and vias[0].GetNetCode()==gnd
    vias[0].SetPosition(new);changed.append(vias[0])
    for t in b.GetTracks():
        if isinstance(t,pcb.PCB_VIA) or t.GetNetCode()!=gnd:continue
        touched=False
        if t.GetStart()==old:t.SetStart(new);touched=True
        if t.GetEnd()==old:t.SetEnd(new);touched=True
        if touched:changed.append(t)
old=point(36.55,36.675);target=point(37.75,40)
vias=[t for t in b.GetTracks() if isinstance(t,pcb.PCB_VIA) and t.GetPosition()==old]
assert len(vias)==1 and vias[0].GetNetCode()==gnd
b.Remove(vias[0])
assert any(isinstance(t,pcb.PCB_VIA) and t.GetPosition()==target and t.GetNetCode()==gnd for t in b.GetTracks())
t=pcb.PCB_TRACK(b);t.SetStart(old);t.SetEnd(target);t.SetLayer(pcb.F_Cu)
t.SetWidth(pcb.FromMM(.2));t.SetNetCode(gnd);b.Add(t);changed.append(t)

# Check exact native effective shapes on every occupied copper layer.
cu=list(b.GetEnabledLayers().CuStack());pads=[p for fp in b.GetFootprints() for p in fp.Pads()]
tracks=list(b.GetTracks());violations=[]
for t in changed:
    layers=cu if isinstance(t,pcb.PCB_VIA) else [t.GetLayer()]
    for layer in layers:
        shape=t.GetEffectiveShape(layer)
        for pad in pads:
            if pad.GetNetCode()!=t.GetNetCode() and pad.IsOnLayer(layer) and pcb.SHAPE.Collide(shape,pad.GetEffectiveShape(layer),pcb.FromMM(.16)):
                violations.append((t.GetNetname(),b.GetLayerName(layer),'pad '+pad.GetParentFootprint().GetReference()+'.'+pad.GetNumber()))
        for other in tracks:
            if other.GetNetCode()!=t.GetNetCode() and (isinstance(other,pcb.PCB_VIA) or other.GetLayer()==layer) and pcb.SHAPE.Collide(shape,other.GetEffectiveShape(layer),pcb.FromMM(.16)):
                violations.append((t.GetNetname(),b.GetLayerName(layer),'track '+other.GetNetname()))
assert not violations,violations
intersections=[]
for via in tracks:
    if not isinstance(via,pcb.PCB_VIA):continue
    hole=pcb.SHAPE_CIRCLE(via.GetPosition(),via.GetDrillValue()//2)
    for pad in pads:
        if pad.GetAttribute()==pcb.PAD_ATTRIB_SMD and pcb.SHAPE.Collide(hole,pad.GetEffectiveShape(pad.GetLayer()),0):
            intersections.append((pcb.ToMM(via.GetPosition().x),pcb.ToMM(via.GetPosition().y),pad.GetParentFootprint().GetReference(),pad.GetNumber()))
assert not intersections,intersections
pcb.ZONE_FILLER(b).Fill(b.Zones())
pcb.SaveBoard(str(WORK/'Adolfo-main.kicad_pcb'),b)
for src in OUT.glob('Adolfo-main*.kicad_sch'):shutil.copy2(src,WORK/src.name)
for name in ['Adolfo-main.kicad_pro','ADOLFO.kicad_sym','fp-lib-table','sym-lib-table']:
    shutil.copy2(OUT/name,WORK/name)
shutil.copytree(OUT/'ADOLFO.pretty',WORK/'ADOLFO.pretty',dirs_exist_ok=True)
print('Candidate saved',WORK/'Adolfo-main.kicad_pcb')
print('Changed objects:',len(changed),'Drill/SMD intersections:',len(intersections))
