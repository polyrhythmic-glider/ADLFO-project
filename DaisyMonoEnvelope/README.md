# Firmware ADLFO

Il firmware attuale genera **un solo inviluppo AD/LFO** e gestisce quattro
encoder cliccabili, quattro tasti e OLED. La migrazione al quad DAC MCP4728
non è ancora implementata.

Tutta la documentazione hardware è in [wiring/](../wiring/README.md):
[schemi](../wiring/SCHEMI.md), [BOM](../wiring/BOM.md) e
[controlli](../wiring/CONTROLLI.md).

## Funzioni presenti

- Motore AD: Rise e Fall, 5 ms–10 s; trigger accettato da Idle.
- Modalità LFO: ripetizione del ciclo; trigger esterno riavvia Rise.
- Curve LOG, LIN ed EXP; simmetria e livello regolati dagli encoder E3/E4.
- Menu OLED e debug dei quattro encoder/tasti.
- Trigger condizionato D6, lettura CV D16/A1, DAC interno D23/A8.
- TIM5 a 10 kHz per inviluppo/DAC; scansione controlli a 1 kHz.
- OLED SSD1306 128×64, indirizzi 0x3C/0x3D, I2C1 su D11/D12 a 100 kHz.

La scala CV presente nel codice è 0,97 e non è ancora aggiornata per il nuovo
partitore 100 kΩ / 33 kΩ. Sono da implementare driver MCP4728, quattro motori,
altri ingressi, coordinamento del bus e calibrazione. D23 non va collegato
alle uscite del MCP4728. Il front panel cablato non implica che le dodici porte
siano già operative.

## File

| File | Funzione |
| --- | --- |
| [main.cpp](main.cpp) | Inizializzazione hardware, timer, controlli e display |
| [PanelControls.h](PanelControls.h) | Pin, scansione e raccolta eventi dei quattro encoder/tasti |
| [EnvelopeGenerator.h](EnvelopeGenerator.h) / [EnvelopeGenerator.cpp](EnvelopeGenerator.cpp) | Motore AD/LFO |
| [Makefile](Makefile) | Build libDaisy/DaisySP e programmazione DFU |

## Compilazione

Servono ARM GNU `arm-none-eabi-gcc/g++`, `make`, libDaisy e DaisySP compilate.
Il Makefile usa questi percorsi, relativi alla cartella firmware:

```make
LIBDAISY_DIR ?= ../../DaisyExamples/libDaisy
DAISYSP_DIR ?= ../../DaisyExamples/DaisySP
```

Dalla radice del progetto:

```sh
make -C DaisyMonoEnvelope
```

Per librerie in altre posizioni:

```sh
make -C DaisyMonoEnvelope LIBDAISY_DIR=/percorso/libDaisy DAISYSP_DIR=/percorso/DaisySP
```

Il binario viene generato in `build/DaisyMonoEnvelope.bin`. La presenza di
file nella cartella build non dimostra che il montaggio attuale sia collaudato.

## Programmazione USB DFU

Questa versione usa `APP_TYPE=BOOT_NONE`, quindi la flash interna.
Preparare l'alimentazione USB secondo la procedura in
[SCHEMI.md](../wiring/SCHEMI.md), con JP_VIN tolto e patch scollegate.

1. Collegare USB.
2. Tenere BOOT, premere e rilasciare RESET, poi rilasciare BOOT.
3. Eseguire dalla radice:

```sh
make -C DaisyMonoEnvelope program-dfu
```

È necessario `dfu-util`. La programmazione sostituisce il firmware sulla Daisy.

## Verifica dei controlli

Aprire ENC DEBUG e verificare rotazione, click e tasto di ogni colonna.
Controllare le funzioni secondo [CONTROLLI.md](../wiring/CONTROLLI.md).
Il collaudo elettrico dei nuovi ingressi e uscite segue invece la sequenza
in [SCHEMI.md](../wiring/SCHEMI.md), prima di collegarli al processore o al synth.

## Nuova vista OLED e test encoder

La schermata principale usa tre colonne RISE / FALL / OUT, valori grandi e
una fascia inferiore con simmetria, livello, modalità, curva e CV. OUT e CV
sono percentuali; i tempi passano automaticamente da millisecondi a secondi.

Premere insieme i click **E1 + E4**, poi rilasciarli, per aprire la vista
con quattro contatori. Ruotare ogni encoder per variare il proprio valore;
un click, al rilascio, azzera soltanto quel contatore. E2 qui azzera E2,
non apre il menu. Premere nuovamente E1 + E4 per tornare alla pagina precedente.
I contatori partono da zero all'avvio, persistono tra le aperture e sono limitati
a −9999…9999. In questa vista gli encoder e i quattro tasti non modificano
i parametri; l'inviluppo e gli ingressi esterni continuano a funzionare.

La combinazione non esegue il trigger E1 né il reset livello E4. Nella vista
principale il reset E4 viene quindi eseguito al rilascio del click.

Nella vista E1 + E4 ogni riquadro mostra anche **B1, B2, B3 o B4**:
l'intero riquadro diventa bianco con il nome del bottone grande in nero mentre
il relativo tasto separato è premuto; al rilascio torna al valore dell'encoder. Si possono verificare anche più tasti insieme;
in questa vista non attivano trigger, cambio modalità, curva o menu.
