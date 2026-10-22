"""Download primary reference files; build.py itself works offline."""
from pathlib import Path
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE / "vendor"
BASE = "https://raw.githubusercontent.com/KiCad/kicad-footprints/master/"
FILES = {
    "encoder.kicad_mod": BASE + "Rotary_Encoder.pretty/RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm.kicad_mod",
    "button.kicad_mod": BASE + "Button_Switch_THT.pretty/SW_PUSH_6mm_H9.5mm.kicad_mod",
    "r0805.kicad_mod": BASE + "Resistor_SMD.pretty/R_0805_2012Metric.kicad_mod",
    "r2010.kicad_mod": BASE + "Resistor_SMD.pretty/R_2010_5025Metric.kicad_mod",
    "c0805.kicad_mod": BASE + "Capacitor_SMD.pretty/C_0805_2012Metric.kicad_mod",
    "soic14.kicad_mod": BASE + "Package_SO.pretty/SOIC-14_3.9x8.7mm_P1.27mm.kicad_mod",
    "msop10.kicad_mod": BASE + "Package_SO.pretty/MSOP-10_3x3mm_P0.5mm.kicad_mod",
    "sot23.kicad_mod": BASE + "Package_TO_SOT_SMD.pretty/SOT-23.kicad_mod",
    "sod123.kicad_mod": BASE + "Diode_SMD.pretty/D_SOD-123.kicad_mod",
    "sma.kicad_mod": BASE + "Diode_SMD.pretty/D_SMA.kicad_mod",
    "idc10.kicad_mod": BASE + "Connector_IDC.pretty/IDC-Header_2x05_P2.54mm_Vertical.kicad_mod",
    "KICAD-LICENSE.md": BASE + "LICENSE.md",
    "recom-datasheet.pdf": "https://recom-power.com/pdf/Innoline/R-78E-0.5.pdf",
    "jack.kicad_mod": "https://raw.githubusercontent.com/clacktronics/AudioJacks/main/AudioJacks.pretty/Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical.kicad_mod",
    "AUDIOJACKS-LICENSE": "https://raw.githubusercontent.com/clacktronics/AudioJacks/main/LICENSE",
}

def fetch(item):
    name, url = item
    data = (ROOT / name).read_bytes() if (ROOT / name).exists() else urlopen(url, timeout=35).read()
    (ROOT / name).write_bytes(data)
    return name, {"url": url, "sha256": hashlib.sha256(data).hexdigest()}

if __name__ == "__main__":
    ROOT.mkdir(parents=True, exist_ok=True)
    manifest = {}
    with ThreadPoolExecutor(max_workers=5) as pool:
        for name, meta in pool.map(fetch, FILES.items()):
            manifest[name] = meta
            print(name, flush=True)
    (ROOT / "sources.json").write_text(json.dumps(manifest, indent=2) + "\n")
