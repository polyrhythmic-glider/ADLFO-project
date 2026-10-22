# ADLFO

Quattro AD/LFO indipendenti con Daisy Seed e MCP4728.
Montaggio confermato: SDA D12, SCL D11; VA–VD ai quattro jack tramite 1 kΩ,
sleeve a GND. Tensioni ancora da verificare.

- [Firmware e comandi](DaisyMonoEnvelope/README.md).
- [Schemi conservati e lavoro hardware restante](wiring/README.md).
- [Proposta PCB, pannello e visualizzatore offline](hardware/pcb/README.md).
- Diagnostica separata: [CV/DAC](DaisyCv4Test/README.md) e [OLED](DaisyOledTest/README.md).

TRIG/CV non ancora collegati: pin da decidere, ingressi disabilitati nel codice.
Gli schemi sono proposte: non presumere che descrivano il cablaggio reale.

## Compilazione e test

Servono GNU Make, la toolchain `arm-none-eabi`, un compilatore C++ per i test
locali e le librerie libDaisy/DaisySP già compilate. I Makefile cercano queste
librerie in `../DaisyExamples/` rispetto alla radice del repository; per altri
percorsi passare `LIBDAISY_DIR` e `DAISYSP_DIR` a `make`.

```sh
make -C DaisyMonoEnvelope
make -C DaisyMonoEnvelope test
make -C DaisyCv4Test
make -C DaisyOledTest
c++ -std=c++14 -Wall -Wextra -Werror DaisyCv4Test/tests/protocol_test.cpp -o /tmp/adlfo-cv4-protocol-test
/tmp/adlfo-cv4-protocol-test
```

Le cartelle `build/` e le cache locali sono escluse da Git. I file hardware in
`hardware/pcb/output/` sono invece versionati per poter aprire e revisionare
il progetto senza rigenerarlo; le istruzioni sono nel relativo README.
