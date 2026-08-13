# DaisyMonoEnvelope

Firmware essenziale per una prova su breadboard con Daisy Seed3. Genera sul DAC hardware un segnale mono unipolare `0 ... 3,3 V` con forma `0 -> Rise -> 1 -> Fall -> 0`. Il firmware attuale gestisce Trigger In, Time CV In ed Envelope Out. Il cablaggio è inoltre predisposto per quattro nuovi ingressi CV e la seconda uscita DAC interna; queste cinque nuove porte richiedono ancora l'estensione del firmware descritta in [WIRING.md](WIRING.md).

Sono disponibili due modalità:

- **AD Envelope**: una pressione breve di Encoder 1 avvia un singolo ciclo quando l'inviluppo è in Idle.
- **Cycling AD / LFO**: Rise e Fall si ripetono continuamente.

Il progetto usa libDaisy per hardware, controlli, OLED, timer e DAC. DaisySP è incluso e collegato dal Makefile; viene usato solo per le semplici limitazioni numeriche. L'inviluppo è una classe dedicata perché rende esplicite le curve LOG/LIN/EXP e la macchina a stati.

## Hardware richiesto

- Daisy Seed3;
- due encoder rotativi con CLK, DT, SW, `+` e GND;
- un potenziometro lineare B10K;
- un OLED I2C 128x64 da circa 1 pollice, assunto SSD1306;
- otto jack mono TS da 3,5 mm, oppure jack TRS/TRRS usando solo Tip e Sleeve;
- un transistor NPN 2N3904;
- un diodo `1N4148` e dieci diodi Schottky `1N5817`/`1N5819`;
- resistenze `1 kOhm` (due), `47 kOhm` (sei), `100 kOhm` (sei) e `1 MOhm`;
- cinque condensatori da `10 nF`;
- breadboard, cavetti e oscilloscopio.

La Daisy e i circuiti attivi sono alimentati via USB/3,3 V; i segnali ai jack attraversano obbligatoriamente i circuiti di condizionamento. I collegamenti completi sono in [WIRING.md](WIRING.md).

## Dipendenze

Servono:

- toolchain ARM GNU `arm-none-eabi-gcc/g++`;
- `make`;
- `dfu-util` per il caricamento USB DFU;
- libDaisy;
- DaisySP.

Su questo sistema le librerie sono già presenti in:

```text
/home/maurice/Documenti/DaisyExamples/libDaisy
/home/maurice/Documenti/DaisyExamples/DaisySP
```

Il Makefile usa perciò i percorsi relativi:

```make
LIBDAISY_DIR ?= ../../DaisyExamples/libDaisy
DAISYSP_DIR ?= ../../DaisyExamples/DaisySP
```

### Installazione se le librerie non sono presenti

Il modo più semplice è clonare il repository ufficiale con i submodule e compilare entrambe le librerie:

```sh
git clone --recursive https://github.com/electro-smith/DaisyExamples.git
make -C DaisyExamples/libDaisy
make -C DaisyExamples/DaisySP
```

Poi indicare i percorsi assoluti o relativi durante la build:

```sh
make LIBDAISY_DIR=/percorso/DaisyExamples/libDaisy \
     DAISYSP_DIR=/percorso/DaisyExamples/DaisySP
```

Le istruzioni aggiornate per l'ambiente C++ sono nella [documentazione ufficiale Daisy](https://daisy.audio/tutorials/cpp-dev-env/).

## Struttura

```text
DaisyMonoEnvelope/
|-- Makefile
|-- main.cpp
|-- EnvelopeGenerator.h
|-- EnvelopeGenerator.cpp
|-- WIRING.md
`-- README.md
```

- `EnvelopeGenerator.*`: macchina a stati Idle/Rise/Fall e curve.
- `main.cpp`: pin, controlli, ADC, smoothing, timer, DAC e funzioni OLED isolate.
- `Makefile`: build libDaisy/DaisySP e target di programmazione.
- `WIRING.md`: cablaggio e avvertenze elettriche.

## Compilazione

Dalla cartella del progetto:

```sh
make
```

Il file da caricare viene creato come:

```text
build/DaisyMonoEnvelope.bin
```

Per ricompilare da zero:

```sh
make clean
make
```

## Flash USB DFU

Questa versione usa `APP_TYPE=BOOT_NONE` e viene scritta direttamente nella flash interna.

1. Collegare la Daisy via USB.
2. Tenere premuto BOOT.
3. Premere e rilasciare RESET.
4. Rilasciare BOOT.
5. Eseguire:

```sh
make program-dfu
```

In alternativa si può caricare `build/DaisyMonoEnvelope.bin` con il [Daisy Web Programmer ufficiale](https://electro-smith.github.io/Programmer/), scegliendo la flash interna.

## Controlli

| Controllo | Azione | Risultato |
|-----------|--------|-----------|
| Encoder 1 | Rotazione | Modifica Rise su scala esponenziale, 5 ms ... 10 s |
| Encoder 1 | Pressione breve e rilascio | Avvia AD, solo in modalità AD e da Idle |
| Encoder 1 | Pressione per almeno 750 ms | Alterna AD e LFO; il cambio avviene durante la pressione |
| Encoder 2 | Rotazione | Modifica Fall su scala esponenziale, 5 ms ... 10 s |
| Encoder 2 | Pressione breve e rilascio | Cambia curva `LOG -> LIN -> EXP -> LOG` |
| Encoder 2 | Pressione per almeno 750 ms | Apre il piccolo menu OLED; dal menu/sottopagine torna alla schermata principale |
| Potenziometro | Centro | Mantiene i tempi base degli encoder |
| Potenziometro | Verso GND/sinistra | Rise più corto, Fall più lungo |
| Potenziometro | Verso 3V3/destra | Rise più lungo, Fall più corto |
| Trigger In | Fronte positivo | In AD avvia da Idle; in LFO riporta il ciclo all'inizio |
| Time CV In | 0 ... 10 V unipolare | Da 0 = nessun effetto fino ad allungare insieme Rise e Fall |

Le pressioni brevi vengono riconosciute al rilascio, così non eseguono l'azione breve prima che la pressione possa diventare lunga. Se direzione degli encoder o del potenziometro è invertita, vedere `WIRING.md`. Rise e Fall vengono modificati solo nella schermata principale: quando il menu è aperto, Encoder 2 serve alla navigazione.

I valori mostrati di Rise e Fall sono i tempi effettivi dopo SYMMETRY e Time CV, non solo i valori base degli encoder. Sulla schermata principale ogni parametro controllato dagli encoder riporta anche `E1` o `E2`: `E1 Mode`, `E1 Rise`, `E2 Fall` ed `E2 Curve`. `CV` mostra il valore normalizzato 0,00 ... 1,00. Le costanti `kSmoothingAmount`, `kCvSmoothingAmount`, `kSymmetryDepth` e `kCvTimeDepth` in `main.cpp` rendono facilmente regolabili smoothing e profondità.

## Modalità e curve

In modalità AD la macchina a stati esegue:

```text
Idle -> Rise -> Fall -> Idle
```

In AD un trigger manuale o esterno è accettato solo da Idle. In modalità LFO esegue:

```text
Rise -> Fall -> Rise -> Fall -> ...
```

Entrando in LFO parte da zero. Un trigger esterno durante LFO riporta Rise a fase zero, permettendo una sincronizzazione semplice. Tornando in AD forza immediatamente valore zero e stato Idle.

La fase di ogni tratto è normalizzata `0.0 ... 1.0`. Le curve sono:

- `LIN`: fase lineare;
- `EXP`: fase al cubo;
- `LOG`: uno meno il cubo della fase inversa.

Fall usa `1.0 - curva(fase)`. Le moltiplicazioni al cubo evitano `powf` nel callback real-time.

## Riferimento progettuale: Mutable Instruments Peaks

Il motore è stato confrontato con il firmware open source di [Mutable Instruments Peaks](https://github.com/pichenettes/eurorack/tree/master/peaks), in particolare con [multistage_envelope.cc](https://github.com/pichenettes/eurorack/blob/master/peaks/modulations/multistage_envelope.cc) e con la [generazione delle lookup table](https://github.com/pichenettes/eurorack/blob/master/peaks/resources/lookup_tables.py).

Da Peaks sono ripresi come principi progettuali:

- segmenti con fase normalizzata e transizioni esplicite;
- un incremento di fase separato dal valore corrente;
- looping ottenuto tornando dal segmento finale a quello iniziale;
- famiglia di curve concava, lineare e convessa;
- percorso real-time privo di calcoli inutilmente costosi.

In questa implementazione gli incrementi di fase di Rise e Fall vengono calcolati quando cambia il rispettivo tempo; il callback a 10 kHz esegue solo accumulo, curve cubiche, confronti e scrittura DAC. Le cubiche restano quelle richieste per `LOG/LIN/EXP` e sono molto vicine, come comportamento, alle curve tabellate di Peaks senza richiedere tabelle o interpolazione.

Non è stato copiato il framework hardware di Peaks: usa periferiche, interfaccia e rappresentazione fixed-point specifiche del modulo originale. Questo progetto continua a dipendere soltanto da libDaisy/DaisySP e conserva l'obiettivo breadboard mono. Trigger e CV usano piccoli front-end dedicati descritti in `WIRING.md`; non trasformano la breadboard in un modulo Eurorack completo. Peaks è distribuito con licenza MIT; il collegamento serve come riferimento tecnico e storico, non come dipendenza di compilazione.

## Menu OLED e guida controlli

Tenere premuto Encoder 2 per almeno 750 ms per aprire:

```text
MENU
> CONTROLS
  ENC DEBUG
  BACK
E2 ROT/TAP  HLD EXIT
```

Nel menu:

- ruotare Encoder 2 per spostare il riquadro di selezione;
- premere brevemente Encoder 2 per aprire la voce;
- tenere premuto Encoder 2 per tornare direttamente alla schermata principale.

`CONTROLS` mostra due manopole stilizzate con una guida compatta:

```text
E1                  E2
ROT:RISE            ROT:FALL
TAP:TRG             TAP:CUR
HLD:MODE            HLD:MENU
```

Un click di Encoder 2 torna al menu. Le abbreviazioni significano rotazione, pressione breve e pressione lunga.

### Debug degli encoder

Dal menu scegliere `ENC DEBUG` per aprire:

```text
DEBUG ENCODERS
E1 pos: ...
E2 pos: ...
Last: ... ...
SW: E1 ... E2 ...
E2 TAP: back
```

`E1 pos` e `E2 pos` sono contatori firmati degli scatti riconosciuti dall'accensione. `Last` conserva l'ultimo incremento non nullo di ciascun encoder e `SW` mostra lo stato dei pulsanti. In questa pagina la rotazione aggiorna i contatori ma non modifica Rise/Fall. Un click di Encoder 2 torna al menu; una pressione lunga torna direttamente alla schermata principale.

## Frequenza di aggiornamento e DAC

TIM5 aggiorna inviluppo, Trigger In e DAC a 10 kHz. Ogni dieci tick esegue anche la breve scansione digitale degli encoder a 1 kHz e deposita scatti/pulsanti in una mailbox; il loop principale li consuma senza perderli durante il refresh OLED. Rendering OLED, ADC, smoothing CV e calcoli dei parametri restano fuori dall'interrupt. TIM2, usato internamente da libDaisy, non viene toccato.

`kOutputMaximum = 1.0f` limita l'uscita alla piena scala DAC. Il codice normalizzato `0.0 ... 1.0` viene convertito in `0 ... 4095`, cioè circa `0 ... 3,3 V` sul canale DAC1 (`D23/A8/PA4`). L'uscita audio non viene usata.

## OLED

Il codice assume:

```text
SSD1306, 128x64, I2C1, indirizzo 0x3C, 400 kHz
```

Il display viene richiesto circa ogni 50 ms e mostra Mode, Rise, Fall, Curve, CV normalizzata e Output. L'aggiornamento non avviene nel callback del timer. Un piccolo transport locale invia ciascuna pagina OLED da 128 byte in una sola transazione, evitando le 1024 transazioni separate del transport standard presente nella versione locale di libDaisy.

Il modello indicato dall'utente è presunto: un OLED apparentemente simile potrebbe essere `0x3D`, SH1106 o 128x32. Tutta la configurazione è isolata in `InitDisplay()`, mentre la resa testuale è isolata in `UpdateDisplay()`/`WriteDisplayLine()`. Se il display non si accende, verificare prima indirizzo e controller con la documentazione del modulo.

## Limiti elettrici

- Daisy e componenti attivi sono alimentati via USB/3,3 V; non usare il bus +/-12 V.
- Il pin ADC ammette solo 0 ... 3,3 V: il jack CV deve passare dal partitore e dai clamp.
- Time CV In è progettato per 0 ... 10 V unipolare; le tensioni negative vengono solo limitate e non interpretate.
- Trigger In deve passare dal circuito NPN invertente.
- DAC unipolare, massimo circa 3,3 V.
- Non applicare tensioni esterne al DAC.
- Collegare sempre la massa della sonda alla massa Daisy.
- Nessuna alimentazione Eurorack, uscita amplificata a 8/10 V, preset, flash, MIDI o menu avanzato.

Solo gli otto jack condizionati come indicato in `WIRING.md` possono essere collegati esternamente. I cinque nuovi collegamenti sono una predisposizione hardware e non sono ancora gestiti dal firmware attuale. Nessun altro pin Daisy è protetto per segnali modulari.

## Procedura di test

Prima di alimentare, ricontrollare ogni riga di `WIRING.md` e impostare il potenziometro circa al centro.

### Test 1 - Accensione

- collega Daisy Seed via USB;
- verifica che l'OLED si accenda;
- verifica che non ci siano componenti caldi;
- verifica che il firmware non si blocchi.

Un lampeggio rapido e continuo del LED integrato indica un errore di inizializzazione DAC/timer.

### Test 2 - Encoder

- ruota Encoder 1;
- verifica che cambi Rise;
- ruota Encoder 2;
- verifica che cambi Fall;
- premi Encoder 2;
- verifica che cambi LOG/LIN/EXP.
- tieni premuto Encoder 2 per almeno 750 ms per aprire il menu;
- ruota Encoder 2 fino a `ENC DEBUG` e premi per entrare;
- verifica che `E1 pos` e `E2 pos` cambino ruotando gli encoder;
- premi Encoder 2 per tornare al menu, oppure tienilo premuto per tornare alla schermata principale.

### Test 3 - Potenziometro

- porta il potenziometro al centro;
- verifica che Rise e Fall mantengano i valori impostati;
- ruotalo a sinistra e a destra;
- verifica che cambi la simmetria.

### Test 4 - Modalità AD

- imposta modalità AD;
- premi e rilascia brevemente Encoder 1;
- verifica sull'oscilloscopio che il segnale salga e poi scenda.
- applica un gate positivo al jack Trigger In;
- verifica che un nuovo ciclo parta quando l'inviluppo è in Idle.

### Test 5 - Modalità LFO

- tieni premuto Encoder 1 per almeno 750 ms per attivare LFO;
- verifica che il segnale continui a ciclare;
- applica un fronte al Trigger In e verifica che il ciclo riparta da zero;
- cambia Rise e Fall;
- cambia curva;
- osserva le differenze sull'oscilloscopio.

### Test 6 - Time CV

- partire con 0 V al jack Time CV In;
- verificare che il display mostri `CV:0.00`;
- aumentare lentamente la tensione senza superare 10 V;
- verificare che `CV` salga verso 1,00;
- verificare che Rise e Fall si allunghino insieme;
- riportare la CV a 0 V e verificare il ritorno ai tempi base.

Impostazione iniziale consigliata per l'oscilloscopio:

```text
1 V/div
100 ms/div oppure 500 ms/div
accoppiamento DC
```

Per tornare ad AD, tenere nuovamente premuto Encoder 1 per almeno 750 ms: l'uscita deve tornare a zero.
