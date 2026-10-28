# Adolfo

Piattaforma Eurorack programmabile da 20 HP: quattro ingressi universali,
quattro uscite universali e quattro porte di controllo bidirezionali.
Quattro encoder con click, quattro tasti e OLED. Alimentazione Eurorack IDC10 ±12 V.

| Porta | Funzioni previste |
| --- | --- |
| IN1–4 | audio, CV, gate, trigger |
| OUT1–4 | audio, CV, envelope, LFO, gate, trigger |
| CTRL1–4 | CV/gate/trigger, ingresso oppure uscita |

## Due stati distinti

- **[Adolfo/](Adolfo/README.md)** è il firmware funzionante del prototipo
  Daisy + DAC Adafruit MCP4728, rinominato da DaisyMonoEnvelope. Motori e
  comandi sono conservati; il nome del binario diventa `Adolfo.bin`.
- **[hardware/pcb/](hardware/pcb/README.md)** contiene la nuova architettura C:
  due schede e conversione esterna DC coupled. È una proposta elettrica
  non sbrogliata, con filtri e altri blocchi ancora da completare. Non è
  pilotata dal firmware del prototipo e non è pronta per l'ordine.

Le vecchie PCB 24/20 HP per il solo AD/LFO, le diagnostiche separate e gli
schemi breadboard superati sono stati rimossi dal branch. La storia Git conserva
il materiale precedente; [pulizia e conservazione](docs/CLEANUP.md).

## Da dove iniziare

1. [Architettura e compromessi](hardware/pcb/ARCHITECTURE.md).
2. [Componenti da aggiungere e materiale da riutilizzare](hardware/pcb/PARTS.md).
3. [Cablaggio del prototipo preservato](docs/PROTOTYPE.md).
4. [Lavoro restante prima della produzione](hardware/pcb/RELEASE_CHECKLIST.md).

## Generazione e controlli

Python 3 con venv, compilatore C++ per i test locali. Per KiCad usare la versione
9 o successiva; i controlli nativi non sostituiscono il collaudo.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r hardware/pcb/requirements.txt
make pcb
make check
make test
```

Per il firmware del prototipo servono libDaisy/DaisySP e `arm-none-eabi`:

```sh
make -C Adolfo
make -C Adolfo test
```

I percorsi delle librerie restano sovrascrivibili con `LIBDAISY_DIR` e
`DAISYSP_DIR`. Nessun comando di generazione carica firmware o ordina una PCB.
