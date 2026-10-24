# Revisione B — 20 HP, moduli riutilizzabili e alimentazione Eurorack

## Vincoli concordati

Un frontale vergine da 20 HP; Daisy Seed e DAC Adafruit già disponibili;
OLED breakout rialzato; quattro encoder con click, quattro pulsanti e dodici
jack verticali PJ398SM/Thonkiconn da saldare sulla PCB. I quattro pulsanti
selezionano i canali e non sostituiscono i click degli encoder.

Il passo nominale 20 HP è 101,6 mm. Il contorno proposto è 101,2 × 128,5 mm,
con 0,4 mm di gioco complessivo; misurare il frontale reale prima della foratura.
La PCB è 96,2 × 110,5 mm. Le colonne sono a X 17,5 / 39,5 / 61,5 / 83,5 mm:
passo 22 mm, almeno 6 mm tra manopole da 16 mm. Coordinate viste dal pannello,
origine in alto a sinistra. Non dividere il vecchio disegno da 24 HP per una scala:
i componenti mantengono le loro dimensioni reali.

## Alimentazione

IDC10 polarizzato: pin 1/2 = −12 V (fascia rossa), 3–8 = GND, 9/10 = +12 V.
Il +5 V del case non serve. F1 sul ramo positivo precede il diodo di protezione;
D1/D2 proteggono dall'inversione dei rail. Il ramo positivo protetto alimenta
il convertitore 5 V e il TL074; il ramo negativo protetto alimenta il TL074.

U5 R-78E5.0-0.5 è un **candidato** da 500 mA, non un budget dimostrato.
Misurare consumo a regime, spunto e temperatura con Daisy, OLED e DAC attivi.
Per il rail +12 V conteggiare la potenza convertita, l'efficienza e il consumo
analogico; 500 mA di uscita a 5 V non equivalgono a 500 mA assorbiti dal +12 V.
F1 è un candidato PTC 1812, hold 0,5 A: scegliere codice, tensione nominale,
derating termico, corrente di intervento e land pattern sul componente reale.
Non proteggere GND con un fusibile.

C1/C2 filtrano i rail protetti; C3/C4 il ramo 5 V. C10 propone 47 µF / 10 V
vicino al connettore di alimentazione della Daisy, C11 100 nF sullo stesso rail;
C12 è un ulteriore 100 nF sui 3,3 V. Il condensatore polarizzato C10 ha il positivo
sul pad 1. Confermare stabilità del convertitore, ESR, capacità ammessa e spunto:
non aumentare arbitrariamente i condensatori e non considerarli una batteria.
I 100 nF di DAC/buffer/opamp vanno vicini ai pin durante lo sbroglio, con ritorni
brevi. C8/C9 disaccoppiano separatamente i rail ±12 V del TL074.

D3 limita il ritorno dal ramo Seed verso U5; non certifica la convivenza di USB
e alimentazione esterna. **Per questa revisione scollegare il cavo Eurorack prima
di collegare USB.** La revisione della Daisy e la sua architettura di alimentazione
devono essere identificate prima di consentire le due sorgenti contemporaneamente.
Con la sola USB, il TL074 non ha alimentazione duale: non aspettarsi uscite valide.

## DAC e bus I²C

U2 è il modulo Adafruit MCP4728 STEMMA QT su due zoccoli 1×6, passo 2,54 mm,
interasse delle file 12,70 mm, scheda 25,4 × 17,78 mm. La mappa deriva dai file
Eagle ufficiali Adafruit (vedere `vendor/adafruit-mcp4728-reference.json`).
Il carrier non contiene un secondo MCP4728 SMD.

| Fila del modulo | Pad carrier | Segnali nell'ordine originale Adafruit |
| --- | --- | --- |
| JP1 | 1–6 | VCC, GND, SCL, SDA, LDAC, RDY |
| JP2 | 7–12 | GND, VA, VB, VC, VD, VCC |

Alimentare il modulo a **3,3 V**, SDA D12 e SCL D11; LDAC a massa, RDY scollegato.
I file ufficiali mostrano pull-up da 4,7 kΩ e condensatori 10 µF + 100 nF già
presenti. R1/R2 aggiuntive sono perciò **DNP** (non montare di default).
Controllare le pull-up dell'OLED: due coppie da 4,7 kΩ danno circa 2,35 kΩ;
verificare corrente di sink, capacità del bus e fronti a 400 kHz con oscilloscopio.
Tutte le pull-up dei segnali devono riferirsi a 3,3 V, mai a 5 V.
Confrontare scritte, revisione e posizione dei connettori con il modulo posseduto.

## Comandi, ingressi e uscite

RP11–RP44 offrono pull-up opzionali da 10 kΩ per A/B/click degli encoder e
pulsanti. Sono DNP: il firmware usa Encoder/Switch libDaisy con debounce e
configurazione predefinita; verificare i pull-up della versione effettivamente
compilata prima del collaudo. Non aggiungere grossi condensatori sugli encoder:
possono deformare le fasi. Eventuali filtri aggiuntivi richiedono misure.

TRIG: 100 kΩ alla base, 1 MΩ base-emettitore, NPN con pull-up 47 kΩ a 3,3 V,
diodo contro la polarizzazione inversa base-emettitore. L'ingresso è invertente;
verificare soglia, ampiezza massima e impulsi prima di abilitare il firmware.

CV: partitore 100 kΩ / 33 kΩ, filtro 10 nF, resistenza 10 kΩ verso i clamp
BAT54S, buffer MCP6004 a 3,3 V, poi 1 kΩ / 1 nF verso ADC. Nominalmente 10 V
diventano 2,481 V: è un ingresso unipolare 0–10 V, non bipolare. Il clamp sul
rail 3,3 V può iniettare corrente e retroalimentare il sistema spento: la
protezione a scheda spenta **non è validata**. Calcolare le correnti, misurare
il rail e scegliere eventuali protezioni ulteriori prima della produzione.
I contatti normalizzati dei jack TRIG/CV sono a massa quando scollegati.

Uscite: TL074 a ±12 V, guadagno nominale 1 + 15k/10k = 2,5. Il firmware usa
un riferimento DAC interno di 2,048 V e limite 4000: il fondo scala teorico è
circa 2 V, quindi circa 5 V dopo l'amplificatore, da misurare e calibrare.
La resistenza serie da 2,2 kΩ / 0,5 W limita le correnti ma non costituisce una
protezione universale: verificare cortocircuiti, patch verso altre uscite,
potenza e comportamento dell'opamp. Con 100 kΩ di carico, 5 V a vuoto diventano
circa 4,89 V. La retroazione resta prima della resistenza serie.

## Quote e selezioni ancora aperte

- Encoder nudi EC11 con click: footprint ALPS candidato, non confermato dal solo
  nome “standard”; verificare pin, linguette, boccola, altezza e manopole.
- OLED: ipotesi SSD1306 128×64 0,96″, pin GND/VCC/SCL/SDA; misurare il breakout,
  il vetro e l'altezza del rialzo. Non assumere tutti gli OLED equivalenti.
- Pulsanti: impronta 6×6 mm candidata, altezza attuatore da scegliere insieme
  alla distanza PCB/pannello imposta dai jack PJ398SM.
- Verificare il PJ398SM reale rispetto all'impronta conservata, incluso foro
  centrale e orientamento tip/sleeve/normal. Il link del componente è nel README.
- Verificare revisioni di Daisy e DAC, e i package di opamp/passivi posseduti:
  la proposta usa MCP6004/TL074 SOIC e passivi SMD, non impronte DIP generiche.
- Distacco pannello/PCB 10 mm e spessore frontale 2 mm sono provvisori. Zoccoli
  Daisy/DAC sul retro devono lasciare spazio alle saldature e alla USB.

## Verifica e completamento

Rigenerare gli export e lanciare `validate.py`. I controlli statici verificano
equivalenza delle connessioni, geometria delle piazzole, distanza dal bordo,
fori, alimentazione IDC10 e impostazioni DNP. Non sostituiscono una verifica
elettrica o delle tolleranze in altezza.

Eseguiti anche ERC/DRC con KiCad 9.0.2; riepilogo in `output/native-checks.json`.
Rimangono collegamenti non sbrogliati, serigrafia e avvisi di libreria/schema.
I simboli generati hanno pin passivi: ERC non controlla correttamente direzioni
e alimentazioni degli IC. Servono simboli elettrici appropriati e un ERC pulito,
poi routing, piani di massa, DRC e collaudo. Nessun Gerber emesso.

Prima alimentazione con sorgente limitata in corrente: controllare polarità e
assenza di corti, misurare i rail senza moduli, poi inserire Daisy/DAC/OLED a
scheda spenta. Verificare i rail anche al carico massimo; collaudare separatamente
TRIG, CV e OUT prima di assegnare/abilitare i pin nel firmware. Non forare i due
frontali né ordinare la PCB sulla sola base della dima preliminare.
