"""Run the supplied kicad-happy SPICE orchestration through KiCad's ngspice DLL."""
from pathlib import Path
import json
import hashlib
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
SKILL = Path('C:/Users/LENOVO/.codex/plugins/cache/kicad-happy/kicad-happy/2.3.2/skills/spice/scripts')
sys.path.insert(0, str(SKILL))
from spice_simulator import NgspiceBackend
from simulate_subcircuits import simulate_subcircuits


class SharedNgspice(NgspiceBackend):
    def find(self):
        return str(HERE/'ngspice_worker.py')

    def run(self, cir_file, timeout=5):
        Path(cir_file).with_suffix('.out').unlink(missing_ok=True)
        try:
            result = subprocess.run([sys.executable, self.find(), str(cir_file)],
                                    capture_output=True, text=True, timeout=timeout)
            error = re.search(r'^stderr (?:Error|Fatal)', result.stdout, re.MULTILINE|re.IGNORECASE)
            return result.returncode == 0 and not error, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, '', f'Simulation timed out after {timeout}s'


if __name__ == '__main__':
    backend = SharedNgspice()
    ok, stdout, stderr = backend.run(HERE/'self_check.cir')
    match = re.search(r'v\(out\) = ([0-9.eE+-]+)', stdout)
    assert ok and match and abs(float(match[1])-1.65) < 1e-6, (stdout, stderr)
    source = Path(sys.argv[1]).resolve()
    data = json.loads(source.read_text(encoding='utf-8'))
    parasitics = json.loads((HERE/'parasitics.json').read_text(encoding='utf-8'))
    report = simulate_subcircuits(data, workdir=str(HERE/'detected_work'),
                                 timeout=10, parasitics=parasitics,
                                 simulator_backend=backend)
    report['backend'] = 'ngspice-46 KiCad shared DLL, isolated worker per circuit'
    report['input_schematic_analysis'] = str(source)
    report['input_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    report['adapter_self_check'] = {'expected_v':1.65, 'measured_v':float(match[1]), 'status':'pass'}
    (HERE/'detected.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report['summary'], indent=2))
    for item in report['simulation_results']:
        if item['status'] != 'pass':
            print(json.dumps(item, ensure_ascii=False)[:1500])
