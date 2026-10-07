# BOM Eurorack — preparazione componenti per circuito

Revisione A, 2026-10-01. Derivata da [SCHEMI.md](SCHEMI.md):
4 trigger IN, 4 CV IN 0–10 V e 4 OUT circa 0–5 V. Il front panel è già cablato.
Questa distinta prepara il prototipo descritto nella guida, ancora da collaudare;
non modifica i suoi limiti di protezione o rende già operativo il nuovo firmware.

Il file [CSV componente per componente](BOM_COMPONENTI.csv) contiene
**93 righe, una per pezzo da predisporre sulla perfboard**, inclusi zoccoli,
portafusibili e ponticello VIN. Usa il separatore `;` in LibreOffice/Excel.
La colonna `preparato` è vuota: segnala lì i pezzi che hai già selezionato.
Le quantità sono di montaggio, senza ricambi; non significano che devi acquistare tutto.

## Preparazione in due fasi

La fase corrente usa solo la USB della Daisy: seguire [AVVIO_USB.md](AVVIO_USB.md).

| Fase | Gruppi da preparare | Pezzi |
| --- | --- | --- |
| USB, adesso | 03.1–03.4 trigger; 04.0–04.4 buffer/CV; 05 DAC | 58 |
| Eurorack, dopo | 01–02 alimentazione; 06.0–06.4 amplificatore/OUT | 35 |

La colonna `fase` del CSV permette di filtrare i due gruppi. I conteggi totali
e le sigle restano invariati. Durante il test USB lasciare U2 TL074 non montato
e le uscite DAC scollegate dagli stadi OUT e dai jack finali.

## Già disponibili / esclusi dai 93 pezzi

| Quantità | Elemento | Stato dichiarato |
| --- | --- | --- |
| 1 | Daisy Seed3 con zoccolo alza pin e perfboard | Già montata |
| 4 | Encoder cliccabili | Front panel cablato |
| 4 | Tasti separati | Front panel cablato |
| 12 | Jack | Front panel cablato |
| 1 | OLED | Front panel cablato |
| 1 | Breakout Adafruit MCP4728 0x60 | Già disponibile; integrazione da fare |
| 1 | Connettore IDC 2×8 | Già disponibile; ingresso alimentazione |

Non aggiungere altri jack, encoder, tasti o pull-up del DAC alla distinta.
Un solo MCP6004 contiene i quattro buffer; un solo TL074 contiene i quattro
amplificatori di uscita. Non servono quattro integrati per tipo.

## Totali da prelevare dalle scorte

Le resistenze elencate sono all’1% per uniformare la preparazione; sui soli
circuiti trigger è accettabile anche il 5%. Non confondere **3,3 Ω** con 3,3 kΩ.
Per i condensatori il valore in volt è la tensione nominale minima.

| Quantità | Componente | Specifica |
| --- | --- | --- |
| 1 | Resistenza: 3,3 Ω | Assiale; 0,5 W; 1% |
| 4 | Resistenza: 1 kΩ | Assiale; 0,25 W; 1% |
| 4 | Resistenza: 2,2 kΩ | Assiale; 0,5 W; 1% |
| 12 | Resistenza: 10 kΩ | Assiale; 0,25 W; 1% |
| 4 | Resistenza: 15 kΩ | Assiale; 0,25 W; 1% |
| 4 | Resistenza: 33 kΩ | Assiale; 0,25 W; 1% |
| 4 | Resistenza: 47 kΩ | Assiale; 0,25 W; 1% |
| 8 | Resistenza: 100 kΩ | Assiale; 0,25 W; 1% |
| 4 | Resistenza: 1 MΩ | Assiale; 0,25 W; 1% |
| 4 | Condensatore: 1 nF | Ceramico; >= 50 V; codice 102 |
| 4 | Condensatore: 10 nF | Ceramico; >= 50 V; codice 103 |
| 7 | Condensatore: 100 nF | Ceramico; >= 50 V; codice 104 |
| 2 | Condensatore: 10 µF | Elettrolitico radiale; >= 10 V |
| 2 | Condensatore: 47 µF | Elettrolitico radiale; >= 25 V |
| 1 | Condensatore: 100 µF | Elettrolitico radiale; >= 25 V |
| 12 | Diodo: 1N4148 | Assiale a foro passante; banda = catodo |
| 2 | Diodo: 1N4007 | Assiale a foro passante; banda = catodo |
| 4 | Transistor: 2N3904 | NPN TO-92; identificare E/B/C dal produttore |
| 1 | Operazionale: MCP6004-I/P | PDIP-14; alimentazione 3V3_A/GND |
| 1 | Operazionale: TL074 DIP-14 | PDIP-14; alimentazione P_PLUS/P_MINUS |
| 1 | Fusibile: T500mA | Ritardato; tensione nominale DC >= 32 V; formato compatibile con HF1 |
| 1 | Fusibile: T100mA | Ritardato; tensione nominale DC >= 32 V; formato compatibile con HF2 |
| 2 | Portafusibile: Per fusibile scelto | Da PCB/perfboard; verificare ingombro e passo |
| 2 | Zoccolo: DIP-14 | Stretto 7,62 mm; passo 2,54 mm |
| 1 | Connettore: Header 1x2 | Passo 2,54 mm; maschio da PCB |
| 1 | Ponticello: Shunt 2 poli | Passo 2,54 mm; removibile |

Totale: **45 resistenze, 20 condensatori, 14 diodi, 4 transistor, 2 operazionali,
2 fusibili, 2 portafusibili, 2 zoccoli DIP-14, 1 header VIN e 1 shunt**.

## Gruppi da preparare sul banco

Prepara un contenitore per ogni gruppo sotto. I gruppi condivisi si preparano
una sola volta. Le sigle R/C/D sono il riferimento univoco per il cablaggio corrente.
I riferimenti rimangono univoci anche quando la numerazione salta fra i gruppi.

### 01 Alimentazione Eurorack

| Pronto | Sigla | Pezzo | Specifica | Funzione |
| --- | --- | --- | --- | --- |
| ☐ | F1 | T500mA | Ritardato; tensione nominale DC >= 32 V; formato compatibile con HF1 | Ramo positivo |
| ☐ | F2 | T100mA | Ritardato; tensione nominale DC >= 32 V; formato compatibile con HF2 | Ramo negativo |
| ☐ | HF1 | Per fusibile scelto | Da PCB/perfboard; verificare ingombro e passo | Supporto F1 |
| ☐ | HF2 | Per fusibile scelto | Da PCB/perfboard; verificare ingombro e passo | Supporto F2 |
| ☐ | D1 | 1N4007 | Assiale a foro passante; banda = catodo | Positivo: anodo verso F1, catodo P_PLUS |
| ☐ | D2 | 1N4007 | Assiale a foro passante; banda = catodo | Negativo: catodo verso F2, anodo P_MINUS |
| ☐ | C1 | 47 µF | Elettrolitico radiale; >= 25 V | P_PLUS/GND; positivo P_PLUS |
| ☐ | C2 | 47 µF | Elettrolitico radiale; >= 25 V | GND/P_MINUS; positivo GND |
| ☐ | C3 | 100 nF | Ceramico; >= 50 V; codice 104 | P_PLUS/GND |
| ☐ | C4 | 100 nF | Ceramico; >= 50 V; codice 104 | P_MINUS/GND |

### 02 Filtro alimentazione Daisy

| Pronto | Sigla | Pezzo | Specifica | Funzione |
| --- | --- | --- | --- | --- |
| ☐ | R1 | 3,3 Ω | Assiale; 0,5 W; 1% | P_PLUS verso JP_VIN |
| ☐ | JP_VIN | Header 1x2 | Passo 2,54 mm; maschio da PCB | Interruzione ramo VIN |
| ☐ | SH_VIN | Shunt 2 poli | Passo 2,54 mm; removibile | Chiusura JP_VIN |
| ☐ | C5 | 100 µF | Elettrolitico radiale; >= 25 V | VIN/GND; positivo VIN |
| ☐ | C6 | 100 nF | Ceramico; >= 50 V; codice 104 | VIN/GND |

### 03.1 TRIG1 — J1 / D6

| Pronto | Sigla | Pezzo | Specifica | Funzione |
| --- | --- | --- | --- | --- |
| ☐ | Q1 | 2N3904 | NPN TO-92; identificare E/B/C dal produttore | Trigger 1 |
| ☐ | R2 | 100 kΩ | Assiale; 0,25 W; 1% | Tip verso base |
| ☐ | R3 | 1 MΩ | Assiale; 0,25 W; 1% | Base verso GND |
| ☐ | R4 | 47 kΩ | Assiale; 0,25 W; 1% | Collettore verso 3V3_D |
| ☐ | D3 | 1N4148 | Assiale a foro passante; banda = catodo | Anodo GND; catodo base |

### 03.2 TRIG2 — J2 / D20

| Pronto | Sigla | Pezzo | Specifica | Funzione |
| --- | --- | --- | --- | --- |
| ☐ | Q2 | 2N3904 | NPN TO-92; identificare E/B/C dal produttore | Trigger 2 |
| ☐ | R5 | 100 kΩ | Assiale; 0,25 W; 1% | Tip verso base |
| ☐ | R6 | 1 MΩ | Assiale; 0,25 W; 1% | Base verso GND |
| ☐ | R7 | 47 kΩ | Assiale; 0,25 W; 1% | Collettore verso 3V3_D |
| ☐ | D4 | 1N4148 | Assiale a foro passante; banda = catodo | Anodo GND; catodo base |

### 03.3 TRIG3 — J3 / D21

| Pronto | Sigla | Pezzo | Specifica | Funzione |
| --- | --- | --- | --- | --- |
| ☐ | Q3 | 2N3904 | NPN TO-92; identificare E/B/C dal produttore | Trigger 3 |
| ☐ | R8 | 100 kΩ | Assiale; 0,25 W; 1% | Tip verso base |
| ☐ | R9 | 1 MΩ | Assiale; 0,25 W; 1% | Base verso GND |
| ☐ | R10 | 47 kΩ | Assiale; 0,25 W; 1% | Collettore verso 3V3_D |
| ☐ | D5 | 1N4148 | Assiale a foro passante; banda = catodo | Anodo GND; catodo base |

### 03.4 TRIG4 — J4 / D22

| Pronto | Sigla | Pezzo | Specifica | Funzione |
| --- | --- | --- | --- | --- |
| ☐ | Q4 | 2N3904 | NPN TO-92; identificare E/B/C dal produttore | Trigger 4 |
| ☐ | R11 | 100 kΩ | Assiale; 0,25 W; 1% | Tip verso base |
| ☐ | R12 | 1 MΩ | Assiale; 0,25 W; 1% | Base verso GND |
| ☐ | R13 | 47 kΩ | Assiale; 0,25 W; 1% | Collettore verso 3V3_D |
| ☐ | D6 | 1N4148 | Assiale a foro passante; banda = catodo | Anodo GND; catodo base |

### 04.0 Buffer CV condiviso

| Pronto | Sigla | Pezzo | Specifica | Funzione |
| --- | --- | --- | --- | --- |
| ☐ | U1 | MCP6004-I/P | PDIP-14; alimentazione 3V3_A/GND | Quattro buffer CV in un solo integrato |
| ☐ | XU1 | DIP-14 | Stretto 7,62 mm; passo 2,54 mm | Zoccolo U1 |
| ☐ | C15 | 100 nF | Ceramico; >= 50 V; codice 104 | Disaccoppiamento U1, pin 4/GND |
| ☐ | C16 | 10 µF | Elettrolitico radiale; >= 10 V | 3V3_A/GND; positivo 3V3_A |

### 04.1 CV1 — J5 / D16

| Pronto | Sigla | Pezzo | Specifica | Funzione |
| --- | --- | --- | --- | --- |
| ☐ | R14 | 100 kΩ | Assiale; 0,25 W; 1% | Tip verso nodo X |
| ☐ | R15 | 33 kΩ | Assiale; 0,25 W; 1% | Nodo X verso GND |
| ☐ | R16 | 10 kΩ | Assiale; 0,25 W; 1% | Nodo X verso nodo Y |
| ☐ | R17 | 1 kΩ | Assiale; 0,25 W; 1% | Uscita buffer verso ADC |
| ☐ | C7 | 10 nF | Ceramico; >= 50 V; codice 103 | Nodo X verso GND |
| ☐ | C8 | 1 nF | Ceramico; >= 50 V; codice 102 | ADC dopo 1 kΩ verso GND |
| ☐ | D7 | 1N4148 | Assiale a foro passante; banda = catodo | Clamp basso: anodo GND; catodo Y |
| ☐ | D8 | 1N4148 | Assiale a foro passante; banda = catodo | Clamp alto: anodo Y; catodo 3V3_A |

### 04.2 CV2 — J6 / D17

| Pronto | Sigla | Pezzo | Specifica | Funzione |
| --- | --- | --- | --- | --- |
| ☐ | R18 | 100 kΩ | Assiale; 0,25 W; 1% | Tip verso nodo X |
| ☐ | R19 | 33 kΩ | Assiale; 0,25 W; 1% | Nodo X verso GND |
| ☐ | R20 | 10 kΩ | Assiale; 0,25 W; 1% | Nodo X verso nodo Y |
| ☐ | R21 | 1 kΩ | Assiale; 0,25 W; 1% | Uscita buffer verso ADC |
| ☐ | C9 | 10 nF | Ceramico; >= 50 V; codice 103 | Nodo X verso GND |
| ☐ | C10 | 1 nF | Ceramico; >= 50 V; codice 102 | ADC dopo 1 kΩ verso GND |
| ☐ | D9 | 1N4148 | Assiale a foro passante; banda = catodo | Clamp basso: anodo GND; catodo Y |
| ☐ | D10 | 1N4148 | Assiale a foro passante; banda = catodo | Clamp alto: anodo Y; catodo 3V3_A |

### 04.3 CV3 — J7 / D18

| Pronto | Sigla | Pezzo | Specifica | Funzione |
| --- | --- | --- | --- | --- |
| ☐ | R22 | 100 kΩ | Assiale; 0,25 W; 1% | Tip verso nodo X |
| ☐ | R23 | 33 kΩ | Assiale; 0,25 W; 1% | Nodo X verso GND |
| ☐ | R24 | 10 kΩ | Assiale; 0,25 W; 1% | Nodo X verso nodo Y |
| ☐ | R25 | 1 kΩ | Assiale; 0,25 W; 1% | Uscita buffer verso ADC |
| ☐ | C11 | 10 nF | Ceramico; >= 50 V; codice 103 | Nodo X verso GND |
| ☐ | C12 | 1 nF | Ceramico; >= 50 V; codice 102 | ADC dopo 1 kΩ verso GND |
| ☐ | D11 | 1N4148 | Assiale a foro passante; banda = catodo | Clamp basso: anodo GND; catodo Y |
| ☐ | D12 | 1N4148 | Assiale a foro passante; banda = catodo | Clamp alto: anodo Y; catodo 3V3_A |

### 04.4 CV4 — J8 / D19

| Pronto | Sigla | Pezzo | Specifica | Funzione |
| --- | --- | --- | --- | --- |
| ☐ | R26 | 100 kΩ | Assiale; 0,25 W; 1% | Tip verso nodo X |
| ☐ | R27 | 33 kΩ | Assiale; 0,25 W; 1% | Nodo X verso GND |
| ☐ | R28 | 10 kΩ | Assiale; 0,25 W; 1% | Nodo X verso nodo Y |
| ☐ | R29 | 1 kΩ | Assiale; 0,25 W; 1% | Uscita buffer verso ADC |
| ☐ | C13 | 10 nF | Ceramico; >= 50 V; codice 103 | Nodo X verso GND |
| ☐ | C14 | 1 nF | Ceramico; >= 50 V; codice 102 | ADC dopo 1 kΩ verso GND |
| ☐ | D13 | 1N4148 | Assiale a foro passante; banda = catodo | Clamp basso: anodo GND; catodo Y |
| ☐ | D14 | 1N4148 | Assiale a foro passante; banda = catodo | Clamp alto: anodo Y; catodo 3V3_A |

### 05 Integrazione MCP4728 già disponibile

| Pronto | Sigla | Pezzo | Specifica | Funzione |
| --- | --- | --- | --- | --- |
| ☐ | C17 | 100 nF | Ceramico; >= 50 V; codice 104 | 3V3_D/GND vicino al breakout, esterno alla scheda |
| ☐ | C18 | 10 µF | Elettrolitico radiale; >= 10 V | 3V3_D/GND; positivo 3V3_D, esterno al breakout |

### 06.0 Amplificatore OUT condiviso

| Pronto | Sigla | Pezzo | Specifica | Funzione |
| --- | --- | --- | --- | --- |
| ☐ | U2 | TL074 DIP-14 | PDIP-14; alimentazione P_PLUS/P_MINUS | Quattro stadi OUT in un solo integrato |
| ☐ | XU2 | DIP-14 | Stretto 7,62 mm; passo 2,54 mm | Zoccolo U2 |
| ☐ | C19 | 100 nF | Ceramico; >= 50 V; codice 104 | U2 pin 4 verso GND |
| ☐ | C20 | 100 nF | Ceramico; >= 50 V; codice 104 | U2 pin 11 verso GND |

### 06.1 OUT1 — VA / J9

| Pronto | Sigla | Pezzo | Specifica | Funzione |
| --- | --- | --- | --- | --- |
| ☐ | R30 | 10 kΩ | Assiale; 0,25 W; 1% | Uscita DAC verso ingresso + U2 |
| ☐ | R31 | 10 kΩ | Assiale; 0,25 W; 1% | Ingresso − U2 verso GND |
| ☐ | R32 | 15 kΩ | Assiale; 0,25 W; 1% | Uscita U2 prima di 2,2 kΩ verso ingresso − |
| ☐ | R33 | 2,2 kΩ | Assiale; 0,5 W; 1% | Uscita U2 verso Tip jack |

### 06.2 OUT2 — VB / J10

| Pronto | Sigla | Pezzo | Specifica | Funzione |
| --- | --- | --- | --- | --- |
| ☐ | R34 | 10 kΩ | Assiale; 0,25 W; 1% | Uscita DAC verso ingresso + U2 |
| ☐ | R35 | 10 kΩ | Assiale; 0,25 W; 1% | Ingresso − U2 verso GND |
| ☐ | R36 | 15 kΩ | Assiale; 0,25 W; 1% | Uscita U2 prima di 2,2 kΩ verso ingresso − |
| ☐ | R37 | 2,2 kΩ | Assiale; 0,5 W; 1% | Uscita U2 verso Tip jack |

### 06.3 OUT3 — VC / J11

| Pronto | Sigla | Pezzo | Specifica | Funzione |
| --- | --- | --- | --- | --- |
| ☐ | R38 | 10 kΩ | Assiale; 0,25 W; 1% | Uscita DAC verso ingresso + U2 |
| ☐ | R39 | 10 kΩ | Assiale; 0,25 W; 1% | Ingresso − U2 verso GND |
| ☐ | R40 | 15 kΩ | Assiale; 0,25 W; 1% | Uscita U2 prima di 2,2 kΩ verso ingresso − |
| ☐ | R41 | 2,2 kΩ | Assiale; 0,5 W; 1% | Uscita U2 verso Tip jack |

### 06.4 OUT4 — VD / J12

| Pronto | Sigla | Pezzo | Specifica | Funzione |
| --- | --- | --- | --- | --- |
| ☐ | R42 | 10 kΩ | Assiale; 0,25 W; 1% | Uscita DAC verso ingresso + U2 |
| ☐ | R43 | 10 kΩ | Assiale; 0,25 W; 1% | Ingresso − U2 verso GND |
| ☐ | R44 | 15 kΩ | Assiale; 0,25 W; 1% | Uscita U2 prima di 2,2 kΩ verso ingresso − |
| ☐ | R45 | 2,2 kΩ | Assiale; 0,5 W; 1% | Uscita U2 verso Tip jack |

## Cablaggi e minuteria da verificare separatamente

Questi elementi non sono compresi nel conteggio dei 93 componenti:

| Quantità | Materiale | Nota |
| --- | --- | --- |
| 1 | Cavo alimentazione Eurorack 16→16 poli | Lunghezza adatta al case; verificare fascia rossa e continuità |
| Secondo montaggio | Connettori a passo 2,54 mm per breakout/cavetti | Verificare quali sono già saldati; non ordinare una quantità senza misurare |
| Quanto basta | Filo isolato per ponticelli e distribuzione alimentazione | Distinguere GND, 3,3 V, P_PLUS e P_MINUS |
| Secondo montaggio | Distanziali, viti, guaina termorestringente | Evitare contatti con pannello e saldature |

I 12 cavetti dei Tip già sul pannello si collegano ai relativi circuiti;
non contano come resistenze, protezioni o altri pezzi da aggiungere.

## Ordine di assemblaggio

1. Verificare i controlli già cablati usando USB.
2. Un gruppo TRIG e poi gruppo 04.0 con un CV; collaudo prima dei pin Daisy.
3. Gruppo 05: MCP4728 a 3,3 V con bus e punti di misura.
4. Diagnostica firmware, replica trigger/CV e prove dei quattro canali via USB.
5. Successivamente gruppi 01 e 02: alimentazione Eurorack, misure senza Daisy.
6. Gruppo 06.0 e un OUT, collaudo; poi altri canali e calibrazione finale.

**Alimentazioni diverse:** U1 MCP6004 usa 3V3_A/GND; U2 TL074 usa P_PLUS/P_MINUS.
I 1N4148 sono diodi di segnale; i 1N4007 sono quelli dei rami di alimentazione.
Il cablaggio completo e i limiti operativi restano in [SCHEMI.md](SCHEMI.md).
