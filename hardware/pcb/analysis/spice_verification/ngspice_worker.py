"""Run a local netlist with the ngspice shared library distributed by KiCad."""
import ctypes as ct
import os
from pathlib import Path
import sys


def run(path):
    binary = Path('C:/Program Files/KiCad/10.0/bin/ngspice.dll')
    search = os.add_dll_directory(str(binary.parent))
    dll = ct.CDLL(str(binary))
    output = []
    string_callback = ct.CFUNCTYPE(ct.c_int, ct.c_char_p, ct.c_int, ct.c_void_p)
    exit_callback = ct.CFUNCTYPE(ct.c_int, ct.c_int, ct.c_bool, ct.c_bool, ct.c_int, ct.c_void_p)

    @string_callback
    def send_text(text, ident, user):
        output.append(text.decode('utf-8', errors='replace'))
        return 0

    @exit_callback
    def on_exit(status, immediate, quit_exit, ident, user):
        return 0

    dll.ngSpice_Init.argtypes = [string_callback, string_callback, exit_callback,
                                ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p]
    dll.ngSpice_Init.restype = ct.c_int
    assert dll.ngSpice_Init(send_text, send_text, on_exit, None, None, None, None) == 0
    dll.ngSpice_Circ.argtypes = [ct.POINTER(ct.c_char_p)]
    dll.ngSpice_Circ.restype = ct.c_int
    # A CLI testbench ends with quit; shared-library clients retain ownership of exit.
    lines = [line.encode('utf-8') for line in Path(path).read_text().splitlines()
             if line.strip().lower() != 'quit']
    circuit = (ct.c_char_p * (len(lines)+1))(*lines, None)
    status = dll.ngSpice_Circ(circuit)
    print('\n'.join(output))
    return status


if __name__ == '__main__':
    raise SystemExit(run(sys.argv[1]))
