# Adolfo universal — revisione C

Questa architettura sostituisce completamente la proposta A/B per il solo AD/LFO.
Pannello 20 HP: 4 IN, 4 CTRL, 4 OUT, 4 encoder con click, 4 tasti e OLED rialzato.
Una scheda frontale ospita comandi e jack; una scheda posteriore contiene Daisy,
conversione e analogica. Connettore interno 2×20 candidato.

**Stato: concept elettrico con impronte e due PCB NON sbrogliate. Non ordinare.**
Il frontale e i package sono generati in scala; gli IC sono candidati. Il modulo
5 V ha un ingombro provvisorio, i filtri analogici e il driver SPI/DMA non sono
completati. Lo schema usa simboli terminali con pin passivi: non è un ERC elettrico
completo. Il posizionamento elettronica è un primo packing, non layout analogico.

- [ARCHITECTURE.md](ARCHITECTURE.md): collegamenti, pin, temporizzazioni, sicurezza.
- [PARTS.md](PARTS.md): cosa si riusa e cosa serve aggiungere.
- [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md): blocchi aperti e collaudo.
- [output/index.html](output/index.html): visualizzatore offline e ricerca distinta.
- `output/Adolfo.kicad_sch`: connessioni terminali dei due circuiti.
- `output/Adolfo-panel.kicad_pcb`, `output/Adolfo-main.kicad_pcb`: schede separate.
- `output/design.json`, `bom.csv`, `Adolfo.net`: sorgente esportata e netlist.
- `output/drill.svg`: foratura preliminare, NON ancora da usare sui frontali.

```sh
make pcb
make check
make test
CHROME_BIN=chromium node hardware/pcb/browser-smoke.mjs
```

L'ADC/DAC esterno permette audio e continua senza dipendere dal codec di una
specifica revisione Daisy. La proposta privilegia versatilità e misura delle
tensioni: il DAC è 16 bit, non un codec audio 24 bit. Prestazioni reali, rumore,
linearità e V/oct restano da misurare.
