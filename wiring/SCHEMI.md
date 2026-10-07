# Cablaggio perfboard con alimentazione Eurorack e MCP4728

**Montaggio corrente: prima USB.** Questa è la configurazione completa finale;
per montare ora solo la sezione a 3,3 V seguire [AVVIO_USB.md](AVVIO_USB.md).
Alimentazione IDC/VIN e stadi OUT TL074 vengono dopo il collaudo USB.

Revisione A, 2026-10-01. Proposta controllata su datasheet, assegnazione pin e
calcoli nominali; non ancora montata o collaudata. Non è un progetto qualificato
contro ESD, qualsiasi errore di patch o segnali applicati a modulo spento.

Configurazione scelta per procedere: quattro trigger IN positivi, quattro CV IN
0–10 V, quattro OUT unipolari circa 0–5 V. I CV negativi non vengono misurati.
La tensione di 5 V è un obiettivo del nuovo firmware, non del firmware attuale.
Le protezioni descritte limitano tensioni/correnti, ma non autorizzano prove di
guasto sulla Daisy. Prima collaudare i singoli stadi scollegati dal processore.

## Montaggio e componenti precisi

Daisy Seed3 su zoccolo alza pin sopra la perfboard; Adafruit MCP4728 0x60;
connettore IDC 2×8 per INGRESSO alimentazione. Lo zoccolo non contiene elettronica.
Tutti gli integrati analogici qui indicati sono in formato DIP su zoccolo:

- U1: MCP6004-I/P, buffer dei quattro CV, alimentato a 3V3_A.
- U2: TL074 in DIP-14, amplificatore delle quattro uscite, alimentato dai rail ±.
- Q1–Q4: 2N3904; verificare piedinatura sul datasheet del produttore reale.
- Diodi segnale: 1N4148; diodi alimentazione: 1N4007, non intercambiabili per uso.

Se questi integrati non sono disponibili, procurarseli o rivedere il circuito
per le sigle reali. Un TL074 non sostituisce U1 a 3,3 V; un MCP6004 non può
ricevere ±12 V. Le connessioni sotto valgono per Seed3, verificata nel datasheet.

## 1. IDC 16 poli

Identificare il pin 1 sul componente e verificare il cavo a circuito spento.
Questa è la numerazione elettrica standard; non una dima del lato saldature.
Partendo dall'estremità pin 1 / fascia rossa / −12 V:

| Coppia | Segnale | Collegamento sulla perfboard |
| --- | --- | --- |
| 1–2 | −12 V | Unire la coppia → protezione negativa |
| 3–4 | GND | Massa comune |
| 5–6 | GND | Massa comune |
| 7–8 | GND | Massa comune |
| 9–10 | +12 V | Unire la coppia → protezione positiva |
| 11–12 | +5 V bus | Non collegati |
| 13–14 | CV bus | Non collegati |
| 15–16 | Gate bus | Non collegati |

La tacca della scatola da sola non certifica la polarità del cavo. Verificare
continuità fino alle scritte del bus board, quindi tensioni prima del modulo.
Mai inserire/sfilare il cavo con alimentazione accesa.

## 2. Protezione e distribuzione dell'alimentazione

Ramo positivo: IDC 9/10 → F1 → anodo D1 → catodo D1 → P_PLUS.
Ramo negativo: IDC 1/2 → F2 → catodo D2 → anodo D2 → P_MINUS.

- D1 e D2: 1N4007. La banda è il CATODO: verso circuito sul positivo,
  verso connettore sul negativo.
- F1: fusibile ritardato 500 mA, tensione nominale almeno 32 V.
- F2: fusibile ritardato 100 mA, tensione nominale almeno 32 V.
- F1/F2 sono protezioni dei rami, non limitatori istantanei per i semiconduttori;
  verificare spunto/assorbimento al collaudo prima di cambiare calibro.
- 47 µF / 25 V fra P_PLUS e GND: positivo a P_PLUS.
- 47 µF / 25 V fra GND e P_MINUS: positivo a GND, negativo a P_MINUS.
- 100 nF / almeno 50 V in parallelo a ciascuno dei due elettrolitici.

I rail P_PLUS/P_MINUS saranno indicativamente +11…+11,5 V e −11…−11,5 V
sotto carico, non esattamente ±12 V. Non mettere condensatori da 16 V fra i
due rail; tutti i condensatori indicati sono fra UN rail e GND.

Questa protezione a diodi limita il rischio di inversione dei rail, ma non
protegge da qualsiasi cavo IDC crimpato/spostato in modo errato.

### Daisy Seed3

P_PLUS → 3,3 Ω / 0,5 W → jumper removibile JP_VIN → VIN Seed3 (pin fisico 39).
Vicino a VIN: 100 µF / 25 V e 100 nF verso GND, positivo elettrolitico a VIN.
AGND (20) e DGND (40) collegati alla massa comune, con collegamenti corti.
La massa non va interrotta da fusibili o jumper.

Il datasheet Seed3, sezione Power, ammette 4–17 V su VIN e mostra un ingresso
Eurorack: non occorre aggiungere un buck per questa versione. Questo NON vale
per i pin 3V3, GPIO, ADC o VCC MCP4728, che non devono ricevere 12 V.

Procedura conservativa per il primo montaggio: uso rack con JP_VIN inserito e
USB scollegata; programmazione USB con JP_VIN tolto e cavi patch scollegati.
Non è stata verificata qui la condivisione automatica USB/VIN della scheda reale.
Per misurare gli stadi analogici durante debug USB, i rail ± devono essere
alimentati e JP_VIN deve restare tolto; tutte le masse rimangono comuni.

## 3. Controlli e pin dei dodici jack

I nomi Dn NON sono numeri fisici dei piedini. Conservare encoder e tasti:

| Colonna | A/CLK | B/DT | Click | Tasto |
| --- | --- | --- | --- | --- |
| 1 | D0 | D1 | D2 | D25 |
| 2 | D3 | D4 | D5 | D24 |
| 3 | D7 | D8 | D9 | D26 |
| 4 | D10 | D13 | D14 | D27 |

Contatti a massa, pull-up del firmware. Moduli encoder eventualmente alimentati
a 3V3_D. OLED: VCC 3V3_D, GND DGND, SCL D11, SDA D12.

Assegnazione PROPOSTA per il pannello frontale di pannello/layout.json, da sinistra a destra:

| Riga | Canale 1 | Canale 2 | Canale 3 | Canale 4 |
| --- | --- | --- | --- | --- |
| Alta: TRIG | J1 → D6 | J2 → D20 | J3 → D21 | J4 → D22 |
| Centrale: CV | J5 → D16/A1 | J6 → D17/A2 | J7 → D18/A3 | J8 → D19/A4 |
| Bassa: OUT | J9 da VA | J10 da VB | J11 da VC | J12 da VD |

Le frecce attraversano SEMPRE i circuiti sotto. D23 resta libero dal pannello:
non collegarlo a nessuna uscita MCP4728. La vecchia uscita mono su D23 non va
unita alle nuove uscite. La mappa è stata confrontata con il file firmware PanelControls.h:
nessun conflitto fra questi ingressi e i controlli esistenti.

## 4. Quattro trigger

Ripetere per ogni ingresso:

1. Tip → 100 kΩ → base Q.
2. Base → 1 MΩ → GND.
3. 1N4148: anodo GND, catodo/banda base.
4. Emettitore → GND.
5. Collettore → 47 kΩ → 3V3_D.
6. Collettore → GPIO della tabella, dopo collaudo.
7. Sleeve → GND.

Ingressi positivi nominali 3,3–10 V; il circuito è invertente. Nessun trigger:
collettore circa 3,3 V; trigger presente: circa 0–0,3 V. La resistenza 100 kΩ
limita la corrente e il diodo protegge la giunzione base-emettitore da negativo.
Non aggiungere grossi condensatori che cancellerebbero impulsi brevi.

## 5. Quattro CV 0–10 V con diodi normali e buffer

U1 MCP6004: pin 4 → 3V3_A (Seed3 pin 21); pin 11 → GND.
100 nF vicinissimo fra pin 4 e GND; 10 µF / almeno 10 V sulla stessa alimentazione.
Non collegare insieme 3V3_A e 3V3_D con un ponte esterno.

Per ciascun CV:

```text
Tip ── 100k ── X ── 10k ── Y ── ingresso + U1
               │
               ├── 33k ── GND
               └── 10nF ─ GND

U1 uscita ──┬── ingresso − U1 (feedback diretto)
            └── 1k ── ADC Daisy
                        │
                       1nF
                        │
                       GND
```

Due 1N4148 al nodo Y, NON al pin ADC:

- basso: anodo GND, catodo Y;
- alto: anodo Y, catodo 3V3_A.

Tutte le resistenze del partitore 1%. Il buffer, alimentato dalla stessa rail
analogica della Daisy, separa il nodo limitato dai diodi dall'ADC. Non bypassarlo.
La resistenza 10 kΩ limita anche la scarica del condensatore verso il buffer.
Il datasheet MCP6004 descrive la protezione tramite resistenze e diodi alla rail;
questo non autorizza a usare altri operazionali con gli stessi collegamenti.

| Canale U1 | Ingresso + (Y) | Ingresso − | Uscita | ADC dopo 1 kΩ |
| --- | --- | --- | --- | --- |
| A | 3 | 2 | 1 | D16 |
| B | 5 | 6 | 7 | D17 |
| C | 10 | 9 | 8 | D18 |
| D | 12 | 13 | 14 | D19 |

Tensioni nominali: 0 V → circa 0 V; 5 V → 1,241 V; 10 V → 2,481 V;
12 V → 2,977 V. Il margine rispetto a 3,3 V è intenzionale. Il fondo scala
software a 10 V sarà circa 0,752, da calibrare (quello attuale 0,97 è superato).
Il filtro 100k || 33k con 10 nF ha frequenza di taglio circa 641 Hz.
Controllo agli estremi delle tolleranze 1%: con +12 V il partitore produce
2,933–3,023 V, prima degli errori del buffer. A −12 V, assumendo un clamp
a −0,7 V, la corrente dal nodo Y verso il partitore è circa 65 µA.

Negativo: viene limitato, non misurato. Anche se la corrente calcolata a −12 V
è piccola, la risposta fuori range va verificata sul banco col processore
scollegato. A modulo spento i clamp possono rialimentare la rail: niente patch
attive durante spegnimento/programmazione in questa revisione. Per ammetterle
serve un ulteriore progetto di isolamento, non una sostituzione di diodi.

## 6. MCP4728 e quattro uscite

VCC → 3V3_D; GND → massa comune; SCL → D11; SDA → D12; LDAC → GND;
RDY non collegato. Il bus è condiviso con OLED. Non aggiungere pull-up a 5 V.
Il breakout ha già pull-up e disaccoppiamento; sulla perfboard prevedere 10 µF
e 100 nF vicino all'arrivo della sua alimentazione.

Configurazione da impostare nel firmware: riferimento interno 2,048 V, gain ×1,
normal power. VA/VB/VC/VD non vanno direttamente ai jack.

U2 TL074 DIP-14: pin 4 → P_PLUS, pin 11 → P_MINUS.
100 nF dal pin 4 a GND e 100 nF dal pin 11 a GND, vicini all'integrato.

Per ogni canale:

- Uscita DAC → 10 kΩ → ingresso + U2.
- Ingresso − U2 → 10 kΩ → GND.
- Uscita U2 → 15 kΩ → ingresso − U2.
- Uscita U2 → 2,2 kΩ / 0,5 W → Tip jack OUT.
- Sleeve → GND.

La retroazione 15 kΩ prende il segnale PRIMA della resistenza 2,2 kΩ.
Resistenze di guadagno 1%. Nessun condensatore in serie al segnale CV.

| DAC | + U2 | − U2 | Uscita U2 | Jack dopo 2,2 kΩ |
| --- | --- | --- | --- | --- |
| VA | 3 | 2 | 1 | J9 |
| VB | 5 | 6 | 7 | J10 |
| VC | 10 | 9 | 8 | J11 |
| VD | 12 | 13 | 14 | J12 |

Guadagno 2,5: codice DAC 4000 → nominalmente 5,000 V prima della resistenza;
4095 → 5,119 V. Scegliere limite 4000 nel firmware per circa 0–5 V a vuoto.
Con carico 100 kΩ, 5 V diventano circa 4,89 V al jack. Questa impedenza è un
compromesso per la limitazione della corrente; non è un'uscita calibrata 1 V/oct.

La resistenza limita un corto a massa a circa 2,3 mA con uscita a 5 V e isola
la capacità del cavo. Non si fa affidamento sul solo corto interno del TL074:
il datasheet pone condizioni alla sua protezione. Una patch accidentale a −12 V
produce una stima di 7,7 mA attraverso 2,2 kΩ se l'uscita resta a +5 V; questa
è una stima di corrente, NON una certificazione di resistenza al guasto.
Non è ancora verificata la tolleranza a uscite contrapposte, ESD e modulo spento.
Non aggiungere clamp 1N4148 ai rail dichiarandoli una soluzione completa:
potrebbero rialimentare i rail e non garantiscono i limiti di ogni versione IC.

All'accensione il DAC può richiamare valori EEPROM non nulli; il firmware deve
inizializzare subito a zero. Questa revisione non contiene un mute hardware.

## 7. Disposizione sulla perfboard

- IDC, fusibili, 1N4007 e condensatori grandi sul bordo, con spazio per il cavo.
- Collegamenti di massa corti e robusti; ritorno Daisy direttamente alla zona
  di alimentazione, senza farlo passare lungo i ritorni dei quattro CV.
- Trigger vicini all'arrivo dei relativi cavetti; partitori vicino a U1.
- U1 vicino ai pin ADC; condensatori 1 nF sul lato ADC delle resistenze 1 kΩ.
- MCP4728 vicino a U2; feedback 15 kΩ/10 kΩ aderente ai pin U2.
- Evitare cavetti I2C lunghi affiancati ai nodi X/Y analogici.
- Zoccoli U1/U2 orientati nello stesso verso ma etichettati: alimentazioni diverse.
- Con perfboard a isole, ogni collegamento è un ponticello; su stripboard
  interrompere le piste sotto gli integrati. Verificare con continuità.
- Le posizioni foro-per-foro richiedono dimensioni/foto della basetta reale.

## 8. Distinta base per questi circuiti

Per preparare i pezzi sul banco usare [BOM.md](BOM.md),
ordinata per circuito con sigle individuali, oppure il
[CSV con una riga per pezzo](BOM_COMPONENTI.csv).
Il front panel già cablato è escluso dai componenti da aggiungere.

Oltre a Daisy, pannello, MCP4728, IDC e cablaggi:

| Quantità | Componente |
| --- | --- |
| 1 + 1 | MCP6004-I/P + TL074 DIP-14, due zoccoli DIP-14 |
| 4 | 2N3904 |
| 12 | 1N4148: 4 trigger + 8 CV |
| 2 | 1N4007 |
| 1 + 1 | Fusibile T500mA + T100mA e portafusibili |
| 8 | 100 kΩ: 4 trigger + 4 CV |
| 4 | 1 MΩ |
| 4 | 47 kΩ |
| 4 | 33 kΩ, 1% |
| 12 | 10 kΩ: 4 CV + 8 OUT; guadagno 1% |
| 4 | 15 kΩ, 1% |
| 4 | 1 kΩ |
| 4 | 2,2 kΩ / 0,5 W |
| 1 | 3,3 Ω / 0,5 W |
| 4 + 4 | 10 nF + 1 nF ceramici |
| 7 | 100 nF ceramici, almeno 50 V |
| 2 | 47 µF / 25 V |
| 1 | 100 µF / 25 V |
| 2 | 10 µF / almeno 10 V |
| 1 | Jumper removibile JP_VIN |

Resistenze non diversamente specificate: almeno 0,25 W; partitore CV 1%.

## 9. Collaudo e migrazione

La sequenza sotto riguarda l'integrazione Eurorack completa. La prima fase
con la sola USB segue invece [AVVIO_USB.md](AVVIO_USB.md).

1. Tutto spento: verificare pinout IDC, continuità GND, assenza corti fra rail,
   diodi ed elettrolitici. Non confondere la carica dei condensatori con un corto.
2. Scollegare Daisy, DAC e U1/U2. Alimentare solo la distribuzione con una sorgente
   protetta/limitata in corrente e verificare polarità P_PLUS/P_MINUS e VIN.
3. Spegnere, collegare Daisy senza patch. Verificare 3V3_A/3V3_D e controlli.
4. Spegnere, collegare U1/U2 e DAC; lasciare ADC/GPIO dei jack scollegati.
5. Verificare un trigger con 0/3,3 V sul Tip. Replicare quando funziona.
6. Verificare un CV con sorgente nota 0/5/10 V e massa comune. Misurare dopo
   il buffer, prima di collegare ADC. Poi verificare gli altri canali.
7. Firmware di collaudo DAC: indirizzo 0x60, zero, 2048 e 4000 separatamente
   sui quattro canali. Attesi circa 0/1,024/2 V sul DAC e 0/2,56/5 V dopo U2
   a vuoto. A zero sono possibili piccoli offset degli operazionali.
8. Solo dopo questi controlli collegare una destinazione CV del sintetizzatore.

Il firmware attuale è mono, usa D6/D16 e DAC interno D23: non pilota MCP4728,
non legge gli altri ingressi e usa la vecchia scala CV. Nessuna modifica firmware
è inclusa in questa guida. Ordine successivo: diagnostica I/O, un canale esterno,
quattro motori, calibrazione. Non caricare aspettandosi già quattro uscite attive.

Il timer esistente è a 10 kHz, OLED a 100 kHz I2C. Una scrittura fast dei quattro
canali richiede almeno 81 clock: circa 810 µs a 100 kHz o 203 µs a 400 kHz,
senza contare OLED e overhead. Quindi non trasferire quattro canali a 10 kHz
su quel bus. Prevedere scheduler unico, refresh OLED suddiviso in piccoli blocchi
e frequenza DAC misurata al banco; niente I2C bloccante nel timer.

## Riferimenti consultati

- [Doepfer: bus e cablaggio A-100](https://doepfer.de/a100_man/a100t_e.htm)
- [Seed3 datasheet: Power, pinout, ADC](https://daisy.nyc3.cdn.digitaloceanspaces.com/products/seed3/Daisy_Seed3_datasheet.pdf)
- [Adafruit MCP4728 pinout](https://learn.adafruit.com/adafruit-mcp4728-i2c-quad-dac/pinouts)
- [MCP4728 datasheet e schemi breakout](https://learn.adafruit.com/adafruit-mcp4728-i2c-quad-dac/downloads)
- [Microchip MCP4728: protocollo e caratteristiche](https://ww1.microchip.com/downloads/en/DeviceDoc/22187E.pdf)
- [Microchip MCP6004, sezioni 1 e 4.1.2](https://ww1.microchip.com/downloads/en/DeviceDoc/MCP6001-1R-1U-2-4-1-MHz-Low-Power-Op-Amp-DS20001733L.pdf)
- [TI TL074: pinout, alimentazioni e limiti](https://www.ti.com/lit/ds/symlink/tl074.pdf)
