"""Generate the front-panel SVG from physical geometry only (standard library)."""
import json
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent

ROOT = Path(__file__).resolve().parent
layout = json.loads((ROOT / "layout.json").read_text())
assert layout["counts"]["oled"] == 1
for group in ("encoders", "buttons", "columns", "mounting_holes"):
    assert len(layout[group]) == layout["counts"][group], group

assert sum("push_switch" in e for e in layout["encoders"]) == layout["counts"]["encoder_switches"]
assert sum(len(c["jacks"]) for c in layout["columns"]) == layout["counts"]["jacks"]
encoders = {e["id"]: e for e in layout["encoders"]}
buttons = {b["id"]: b for b in layout["buttons"]}
for column in layout["columns"]:
    assert len(column["jacks"]) == layout["counts"]["jacks_per_column"]
    x = encoders[column["encoder_id"]]["x"]
    assert buttons[column["button_id"]]["x"] == x
    assert all(jack["x"] == x for jack in column["jacks"])

svg = Element("svg", xmlns="http://www.w3.org/2000/svg",
              viewBox=f'0 0 {layout["panel"]["width"]} {layout["panel"]["height"]}',
              role="img", **{"aria-labelledby": "title description"})
SubElement(svg, "title", id="title").text = "ADLFO — riferimento fisico front panel"
SubElement(svg, "desc", id="description").text = (
    "OLED centrale, due fori superiori, quattro encoder cliccabili neri con indicatore bianco, "
    "quattro pulsanti allineati e quattro colonne di tre jack ciascuna. Quote relative.")


def shape(tag, **attrs):
    return SubElement(svg, tag, {key: str(value) for key, value in attrs.items()})


def label(x, y, text):
    node = shape("text", x=x, y=y, fill="#475569",
                 **{"text-anchor": "middle", "font-family": "sans-serif", "font-size": 12})
    node.text = text


shape("rect", x=1, y=1, width=398, height=638, fill="#e2e5e9", stroke="#64748b")
for hole in layout["mounting_holes"]:
    shape("circle", id=hole["id"], cx=hole["x"], cy=hole["y"],
          r=hole["radius"], fill="#ffffff", stroke="#64748b")
oled = layout["oled"]
shape("rect", **{key: value for key, value in oled.items()}, fill="#101820", rx=2)
label(200, 144, "OLED1")
for encoder in layout["encoders"]:
    x, y, radius = encoder["x"], encoder["y"], encoder["radius"]
    shape("circle", id=encoder["id"], cx=x, cy=y, r=radius,
          fill="#151515", stroke="#525252", **{"stroke-width": 2})
    shape("line", x1=x, y1=y-radius+5, x2=x, y2=y-10,
          stroke="white", **{"stroke-width": 3})
    label(x, y+radius+18, encoder["id"])
    label(x, y+radius+31, "CLICK" if "push_switch" in encoder else "")
for button in layout["buttons"]:
    shape("circle", id=button["id"], cx=button["x"], cy=button["y"],
          r=button["radius"], fill="#252525", stroke="#64748b")
    label(button["x"], button["y"]+28, button["id"])
for column in layout["columns"]:
    for jack in column["jacks"]:
        shape("circle", id=jack["id"], cx=jack["x"], cy=jack["y"],
              r=jack["radius"], fill="#aeb6c0", stroke="#525252", **{"stroke-width": 2})
        shape("circle", cx=jack["x"], cy=jack["y"], r=8, fill="#111827")
        label(jack["x"], jack["y"]+34, jack["id"])
indent(svg)
ElementTree(svg).write(ROOT / "panel.svg", encoding="utf-8", xml_declaration=True)
