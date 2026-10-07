# ADLFO — stato attuale

Modulo AD/LFO con Daisy Seed3 su zoccolo alza pin e perfboard. Il front panel
è già cablato: quattro encoder cliccabili, quattro tasti, dodici jack e OLED.
Sono disponibili il quad DAC Adafruit MCP4728 e il connettore Eurorack IDC 2×8.

**Si procede prima via USB:** montaggio e debug di controlli, trigger, CV e DAC
a 3,3 V. Alimentazione Eurorack e stadi di uscita TL074 sono la seconda fase.
La guida da seguire ora è [AVVIO_USB.md](wiring/AVVIO_USB.md).

La documentazione hardware corrente è raccolta in **[wiring/](wiring/README.md)**:

- [Stato del montaggio e prossimi passi](wiring/README.md)
- [Mappa completa dei pin, verificata per tutti i 12 jack](wiring/PINOUT.md)
- [Schemi testuali, alimentazione, protezioni e pin](wiring/SCHEMI.md)
- [BOM ordinata per circuito](wiring/BOM.md)
- [BOM CSV, una riga per componente](wiring/BOM_COMPONENTI.csv)
- [Controlli e display](wiring/CONTROLLI.md)
- [Disegno e geometria del pannello](wiring/pannello/README.md)

Il progetto hardware corrente prevede quattro trigger IN, quattro CV IN 0–10 V
e quattro OUT circa 0–5 V. I circuiti posteriori sono definiti nella guida,
ma montaggio e collaudo non sono ancora confermati.

Il **[firmware principale](DaisyMonoEnvelope/README.md) è ancora mono**:
gestisce i quattro encoder e i quattro tasti, un trigger su D6, un CV su D16
e il DAC interno D23. Il MCP4728 e i quattro canali non sono ancora implementati.

[DaisyOledTest](DaisyOledTest/README.md) è un firmware separato di diagnostica
del display; il suo caricamento sostituisce il programma principale.
