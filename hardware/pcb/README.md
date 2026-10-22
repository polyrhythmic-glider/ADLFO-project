# Proposta PCB ADLFO — revisione A

Progetto di posizionamento per un pannello da 24 HP e una singola PCB.
**La scheda non è sbrogliata e non è pronta per la produzione.**
I pin TRIG/CV qui proposti restano disabilitati nel firmware corrente.

- Aprire [output/index.html](output/index.html) in un browser per il visualizzatore
  offline: assemblaggio, fronte, retro, pannello, ricerca BOM e collegamenti.
- Aprire [output/ADLFO.kicad_pro](output/ADLFO.kicad_pro) in KiCad per schema e PCB.
- [output/bom.csv](output/bom.csv), [output/placement.csv](output/placement.csv)
  e [output/panel-holes.csv](output/panel-holes.csv) raccolgono componenti,
  posizionamento e fori; `output/` contiene anche DXF, SVG, PDF e OpenSCAD.

## Sorgenti e rigenerazione

`design.py` definisce circuito, pin, componenti e quote. `build.py` genera i file
KiCad e gli export; `visuals.py` e `viewer-template.html` generano le viste.
`vendor/` conserva footprint, riferimenti e relative licenze; `sources.json`
registra URL e hash SHA-256. La generazione usa questi file locali e funziona offline.

Dalla radice del repository, con Python 3 e il supporto `venv`:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r hardware/pcb/requirements.txt
.venv/bin/python hardware/pcb/build.py
.venv/bin/python hardware/pcb/validate.py
```

Gli export sono versionati insieme ai sorgenti. Dopo una modifica, rigenerarli
e controllare il diff. Il generatore produce le viste SVG/HTML; per aggiornare
anche le anteprime PNG/PDF, con Inkscape installato:

```sh
inkscape hardware/pcb/output/overview.svg --export-width=1800 --export-filename=hardware/pcb/output/overview.png
inkscape hardware/pcb/output/panel-drilling-1to1.svg --export-filename=hardware/pcb/output/panel-drilling-1to1.pdf
```

`fetch_sources.py` recupera i riferimenti mancanti e aggiorna il manifest;
conserva i file già presenti in `vendor/`.

## Verifiche

`validate.py` controlla coerenza di connessioni e pin tra sorgenti, schema,
netlist e PCB, posizionamento, fori e unità degli export. Il rapporto è in
[output/validation.json](output/validation.json).
Non esegue ERC/DRC nativi di KiCad, sbroglio o misure sul circuito reale.

Il test del visualizzatore richiede Node.js e `google-chrome` nel PATH:

```sh
node hardware/pcb/browser-smoke.mjs
```

Controlla le cinque viste, i collegamenti, la ricerca BOM, il cursore
dell'assemblaggio esploso e la larghezza mobile. Salva le schermate in
`/tmp/adlfo-viewer-checks/`.
