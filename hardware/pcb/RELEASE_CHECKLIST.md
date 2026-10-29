# Qualifica della revisione D

## Blocchi emersi dalla revisione del 28 ottobre 2026

- [ ] Risolvere il sequenziamento AVCC/VDRIVE dell'ADC e l'iniezione dai segnali host, inclusi USB e spegnimenti asimmetrici.
- [ ] Riprogettare insieme regolatore e monitor 5 V: il reset non ha margini garantiti con i componenti attuali.
- [ ] Implementare un backend con clock, risorse DMA e schedulazione compatibili: i payload attuali richiedono il 104,448% del tempo con DMA serializzato a 25 MHz.
- [ ] Definire e rispettare la reiezione di immagini/alias audio; il solo filtro attuale non stabilisce prestazioni audio di precisione.
- [ ] Completare gli MPN dei passivi e la qualifica della distinta prima dell'acquisto.

Dettagli, calcoli e fonti: [revisione completa 20 HP](DESIGN_REVIEW_20HP.md).
`validation.json` distingue `cad_status: PASS` da `release_status: BLOCKED`.

La consegna CAD comprende schema, distinta, PCB sbrogliate e rapporti nativi.
Lo stato esatto dei file salvati è in `output/validation.json`; i controlli
passano solo con zero segnalazioni ERC/DRC, zero reti mancanti e zero differenze
fra schema e PCB. Nessuna esclusione nasconde errori.

## Controlli di progetto

- Schema gerarchico con pin elettrici, filtri e amplificatori cablati.
- Confronto del pinout degli IC con i datasheet selezionati; specifiche e MPN dei passivi ancora parziali.
- Filtri analogici a quattro poli su IN1–4 e OUT1–4, verifica ideale e tolleranze.
- Alimentazione con convertitore specifico, fusibili e disaccoppiamenti.
- Watchdog, monitor rail, latch di fault e consenso delle otto uscite.
- Piste su entrambe le PCB; piano GND interno sulla principale.
- Riscontro indipendente di pad, netlist compilate e connettore a quaranta pin.
- ERC/DRC con controllo di parità e rapporti legati ai file mediante SHA256.

## Prima di qualificare l'hardware

- [ ] Stampare una dima 1:1 e montare encoder, tasti, OLED e connettori reali; verificare altezze, USB, distanziali e case.
- [ ] Controllare la distinta di acquisto, l'orientamento e il pin 1 di ogni package; scegliere passivi con capacità effettiva e derating adeguati.
- [ ] Prima accensione con alimentatore limitato in corrente, senza Daisy: rail, ripple, spunto, fusibili e assorbimento.
- [ ] Montare Daisy, inizializzare con permit basso; controllare alimentazioni e condizioni di reset senza abilitare uscite.
- [ ] Implementare il backend AD7606C-18/DAC8568, DMA, watchdog e rilevamento fault.
- [ ] Misurare CONVST/BUSY, SPI, SYNC/LDAC, margini e jitter con analizzatore/oscilloscopio a 96/48 kHz.
- [ ] Implementare e verificare decimazione digitale 96→48 kHz; misurare aliasing, banda, rumore e distorsione.
- [ ] Misurare stabilità dei filtri/amplificatori e risposta a carichi capacitivi e patch realistiche.
- [ ] Provare reset, rail mancanti, brownout, firmware fermo, watchdog e fault ADG; verificare che serva un nuovo consenso dopo il ripristino.
- [ ] Provare ingressi e patch con scheda spenta, limitando energia e corrente secondo i datasheet.
- [ ] Qualificare corti e collisioni fra uscite, temperatura dei resistori e stato degli switch.
- [ ] Calibrare offset/guadagno; misurare linearità, deriva e tensione sotto carico. Non dichiarare V/oct prima di queste misure.
- [ ] Provare impulsi gate/trigger minimi, isteresi, latenza, CPU e memoria con quattro canali audio.
- [ ] Dopo il campione montato, fissare dima meccanica e revisione per produzione.

L'assenza di violazioni CAD autorizza la revisione del campione ingegneristico;
non certifica prestazioni elettriche né sostituisce i test della scheda costruita.
