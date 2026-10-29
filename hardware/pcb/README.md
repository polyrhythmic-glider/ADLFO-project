# Adolfo universal — revisione D

Due PCB per un modulo Eurorack da 20 HP: 4 IN, 4 OUT, 4 CTRL bidirezionali,
quattro encoder con click, quattro tasti e OLED. La revisione D completa lo schema
funzionale, i filtri, l'alimentazione, la supervisione e le piste delle due schede.

**Alimentazione dal connettore Eurorack IDC10, senza USB-C:** il +12 V del case,
attraverso fusibile e protezione di polarità, alimenta il convertitore RECOM a 5 V.
Questi 5 V alimentano VIN della Daisy (pin 39) e il ramo analogico filtrato;
la Daisy genera i 3,3 V. Il −12 V alimenta il ramo analogico negativo.
Non serve il +5 V del case. Lasciare scollegata la USB-C della Seed nel modulo
assemblato: la Seed standard può alimentarsi da USB e il carrier non interrompe
quel percorso interno. Per programmare via USB, estrarre la Seed dal carrier
con il case spento e scollegato.

**Rilascio bloccato dalla [revisione completa](DESIGN_REVIEW_20HP.md):** sequenziamento
AVCC/VDRIVE dell'ADC, margini del monitor 5 V e backend SPI/DMA da riprogettare.
Il superamento dei controlli CAD non risolve questi problemi elettrici.
I datasheet consultati sono conservati localmente in `datasheets/`;
`references.json` registra le fonti e la revisione riporta le basi di verifica.

Aprire con **KiCad 10**:

- [output/Adolfo-main.kicad_pro](output/Adolfo-main.kicad_pro): progetto principale, schema gerarchico e PCB a quattro strati.
- [output/Adolfo-panel.kicad_pro](output/Adolfo-panel.kicad_pro): comandi, jack, display e PCB frontale a due strati.
- [output/index.html](output/index.html): viste 2D e distinta ricercabile.
- [output/front.svg](output/front.svg): frontale aggiornato con display centrale.
- [output/drill.svg](output/drill.svg) e [DXF](output/panel-concept.dxf): dima e taglio nominali aggiornati.
- [output/bom.csv](output/bom.csv): valori, codici scelti, lato e coordinate.
- [output/validation.json](output/validation.json): esito dei controlli sulla revisione salvata.

Le librerie locali sono incluse: tenere tutta la cartella `output` insieme.
Le viste correnti sono SVG; le vecchie copie PNG/PDF della revisione C e la
netlist unica del vecchio progetto sono state rimosse. Le netlist native correnti
sono `Adolfo-main.net` e `Adolfo-panel.net`.
In KiCad, dal gestore progetto aprire lo schema oppure l'editor PCB. Le piste
visibili nell'editor sono rame reale del file PCB. Non è inclusa un'immagine 3D.

La qualifica CAD comprende ERC, DRC, collegamenti mancanti e parità schema/PCB,
oltre al confronto pin per pin fra sorgente, netlist compilata e schede salvate.
I rapporti nativi sono `erc-main.json`, `erc-panel.json`, `drc-main.json` e
`drc-panel.json`. `native-checks.json` ne registra le impronte SHA256, insieme
ai file CAD verificati: una modifica richiede nuovi controlli.

**Prototipo ingegneristico, non ancora qualificato al banco.** Il firmware in
`Adolfo/` pilota il vecchio prototipo con MCP4728; per questa PCB occorre il
backend ADC/DAC, il filtro digitale e il collaudo indicato nella
[lista di qualifica](RELEASE_CHECKLIST.md). Non confondere DRC pulito con misura
di rumore, stabilità, termica o precisione sotto carico.

[Architettura](ARCHITECTURE.md) · [Componenti e montaggio](PARTS.md)

## Rigenerazione

La generazione iniziale **sostituisce le schede e rimuove lo sbroglio esistente**.
Usarla solo quando si intende ricostruire la revisione, conservando prima il lavoro.
Servono Python con `requirements.txt`, KiCad 10 e Java 21 con
[Freerouting 2.0.1](https://github.com/freerouting/freerouting/releases/tag/v2.0.1).
Il JAR va in `.venv/tools/freerouting-2.0.1.jar` oppure in `FREEROUTING_JAR`.
Il router lavora localmente, con telemetria disattivata (`-da`).

PowerShell, dalla radice del repository:

```powershell
& .\.venv\Scripts\python.exe -X utf8 hardware/pcb/build.py
& 'C:\Program Files\KiCad\10.0\bin\python.exe' -X utf8 hardware/pcb/board_setup.py
& 'C:\Program Files\KiCad\10.0\bin\python.exe' -X utf8 hardware/pcb/route.py
& .\.venv\Scripts\python.exe -X utf8 hardware/pcb/native_checks.py
& 'C:\Program Files\KiCad\10.0\bin\python.exe' -X utf8 hardware/pcb/board_setup.py audit
& .\.venv\Scripts\python.exe -X utf8 hardware/pcb/validate.py
```

Per ricontrollare i file esistenti eseguire solo gli ultimi tre comandi.
`build.py` genera schema, impronte, distinta e posizionamento; `board_setup.py`
compila le netlist, applica i lati, configura gli strati, collega i pad di massa al piano con vie fisiche e crea i DSN. `route.py`
importa una nuova sessione solo dopo che il router termina correttamente.
`native_checks.py` richiede zero segnalazioni, senza esclusioni DRC, ed esporta quattro viste SVG del rame.
`validate.py` rifiuta rapporti o audit riferiti a file precedenti.

I file DSN/SES intermedi restano nella cartella ignorata `build/`. Il router
può lasciare connessioni aperte: la revisione consegnata comprende la chiusura
finale delle reti di alimentazione e supera i controlli. Dopo una rigenerazione
ricontrollare il risultato e completare eventuali reti residue in KiCad; il
validatore rifiuta uno sbroglio parziale. I file `.kicad_pcb` salvati sono il
risultato completo da aprire e modificare. I disegni meccanici hanno quote nominali e
richiedono una prova fisica prima di forare il frontale definitivo.
