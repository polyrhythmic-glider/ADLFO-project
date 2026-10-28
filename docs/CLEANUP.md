# Pulizia del branch

Conservato il firmware principale, rinominato `DaisyMonoEnvelope/` → `Adolfo/`;
aggiornati target, percorsi e documentazione. Nessuna migrazione automatica del
cablaggio o del backend del prototipo.

Rimossi `DaisyCv4Test/`, `DaisyOledTest/`, `wiring/`, il generatore PCB A/B e
relativi export, footprint e riferimenti non più usati. La nuova cartella PCB
contiene solo il progetto universale C, con nomi IN/CTRL/OUT e stato esplicito.
Non vengono mantenute dime di foratura A/B accanto a quelle nuove.

Snapshot recuperabile prima di questa riorganizzazione:
https://github.com/polyrhythmic-glider/ADLFO-project/tree/b1032b753d214c1852f0d1f13f15a48cb0d2ef67

Le vecchie foto/immagini di misure restano nello snapshot, non nel progetto attivo.
`docs/PROTOTYPE.md` conserva il riepilogo necessario per il test funzionante.
Le licenze dei footprint usati sono conservate in `hardware/pcb/vendor/`.
