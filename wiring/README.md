# Hardware

Confermato: MCP4728 via STEMMA QT, SDA D12, SCL D11;
VA/VB/VC/VD → ciascuno 1 kΩ → tip OUT1/2/3/4; sleeve a GND comune.
Il funzionamento elettrico delle uscite è ancora da verificare.

Restano soltanto questi schemi **proposti**, non la fotografia del montaggio:

- [TRIG IN su breadboard](trigger_in/README.md).
- [Quattro CV IN su breadboard](cv_in/README.md).
- [Stadio analogico TL074 da realizzare](out_tl074/README.md).

Da fare: decidere i pin TRIG/CV, montare e misurare i condizionatori,
abilitare gli ingressi; definire alimentazione e protezioni dello stadio analogico.
Le immagini in `misure/` conservano le acquisizioni precedenti.
