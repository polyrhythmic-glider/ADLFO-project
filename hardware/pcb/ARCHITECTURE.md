# Architettura C: dodici jack universali

## Specifiche di progetto, non prestazioni già collaudate

| Gruppo | Quantità | Direzione | Modi |
| --- | --- | --- | --- |
| IN | 4 | ingresso | audio, CV, gate, trigger |
| OUT | 4 | uscita | audio, CV, envelope, LFO, gate, trigger |
| CTRL | 4 | selezionabile | CV/gate/trigger in oppure out |

Tutti i percorsi passano la continua. IN1–4 possono lavorare insieme a OUT1–4
in audio, lasciando quattro controlli. CTRL non sono specificate per audio.
Il pannello non assegna nomi fissi di parametri agli encoder: preset e firmware
ne cambiano la funzione. Il nome del progetto è Adolfo.

Proposta: ingressi con campo nominale ±10 V; uscite circa ±5 V, con envelope,
gate e trigger unipolari 0…5 V. Valori definitivi subordinati a filtri, guadagni,
carichi e misure. Non assumere che 16 bit nominali garantiscano precisione V/oct.

## Percorsi analogici

```text
IN1–4 ── protezione + filtro DA COMPLETARE ── ADC canali 1–4
CTRL1–4 ─ protezione + filtro DA COMPLETARE ─ ADC canali 5–8
                                                  │ SPI1
                                             Daisy Seed
                                                  │ SPI3 + level shift
                                             DAC 8 canali
                                                  │
                                  8 stadi bipolari + filtro DA COMPLETARE
                                                  │
                       8 switch protetti ───── OUT1–4 e CTRL1–4
```

**ADC candidato: AD7606C-18**, 8 canali simultanei a 18 bit, ingresso bipolare,
impedenza minima 1 MΩ, 5 V analogici e VDRIVE 3,3 V. Il modello **C-18** conta:
il precedente AD7606B è stato scartato per la banda d'ingresso. La famiglia
C-18 consente 25/220 kHz per canale. Per audio si valuta il modo 220 kHz con
filtri esterni e sovracampionamento; il solo RC 1 kΩ/1 nF disegnato è EMI,
**non** un filtro antialias adeguato. CRC e status header disabilitati nel formato
iniziale; configurare software mode e una sola linea DOUTA prima di leggere.

**DAC candidato: DAC8568B**, 8 canali a 16 bit. Grado B: span 2,5 V con riferimento
interno, reset a metà scala. Non sostituire con A/C/D senza cambiare progetto.
Span 2,5 V lascia margine sul rail analogico 5 V; gli stadi OPA4197 candidati
realizzano `Vjack ≈ 4 × Vdac − 4 × 1,25 V`. Il riferimento 1,25 V è ottenuto
con divisore abbinato dal riferimento 2,5 V e follower dedicato. Gli altri tre
opamp inutilizzati del terzo quad sono chiusi a follower a massa.

Il riferimento interno del grado B non ha la deriva dei gradi C/D: per pitch
accurato serve qualificare deriva, linearità, rapporti resistivi, calibrazione
ed eventualmente un riferimento esterno. Il carico vede anche 100 Ω serie e
la resistenza dello switch: correggere solo offset/guadagno a vuoto non elimina
la caduta dipendente dal carico. Non promettere un'uscita pitch precisa prima
del collaudo a carichi e temperature diversi.

DAC alimentato a 5 V: il requisito VIH può essere 0,7 × AVDD. Perciò cinque
segnali SPI/controllo passano attraverso **SN74AHCT125** a 5 V, con ingressi TTL.
Non collegarli direttamente a 3,3 V e non sostituire AHCT con LVC alimentata a 5 V.
I buffer richiedono verifica di ritardi e skew sul clock reale.

## Porte configurabili e stato sicuro

Due **ADG5412FBRUZ** candidati disconnettono gli otto driver, inclusi i quattro
OUT fissi, fino al consenso software/hardware. Usare **5412F**, non 5413F:
controllo basso = aperto. Il terminale protetto **S va al jack**; D va al driver.
La specifica ±55 V riguarda i terminali protetti del componente nelle condizioni
del datasheet, non è una specifica garantita dell'intero modulo.

CTRL rimane collegato al proprio ADC anche in uscita: utile per feedback e
rilevamento di anomalie. Un semplice GPIO tri-state non sostituisce lo switch.
Il contatto normalizzato dei dodici jack è lasciato aperto: non mettere a massa
quello di un CTRL che può essere usato come uscita.

Otto richieste statiche da MCP23017 passano attraverso AND SN74LVC08 con un
**OUTPUT_PERMIT diretto dalla Daisy e pull-down hardware**. Richieste e comandi
degli switch hanno pull-down. Reset della Daisy o GPIO non inizializzati lasciano
i driver disconnessi; non affidarsi ai soli valori salvati nei preset.

Sequenza prevista: permit basso → richieste a zero → verificare rail e reset
ADC/DAC → attivare riferimento e impostare zero volt → attendere stabilizzazione
→ calibrazione valida → abilitare solo le porte richieste. Prima di cambiare
modo/direzione: aprire lo switch interessato, preparare il valore, attendere
settling e infine richiuderlo. Per fault, watchdog o ripristino preset, disarmare.
La policy in `platform/` è testata su host, ma il backend hardware che la applica
non è ancora implementato. Supervisione brownout/rails e watchdog hardware esterno
restano da progettare: un blocco del firmware con GPIO alto non è risolto dalle AND.

## Risorse Daisy e pinout nuovo

La Daisy fornisce CPU, RAM, memoria, USB, GPIO, timer, SPI e I²C. Il codec integrato
2-in/2-out e il DAC interno non sono usati come porte universali: non coprono da
soli il requisito 4+4 e cambiano fra revisioni. L'attuale libDaisy riconosce Seed 3
(TAC5242/USB-C) e Seed 2 DFM (PCM3060). Usare il firmware/libDaisy corretti per
la propria scheda. La compatibilità meccanica e di alimentazione va verificata
sui due esemplari; non usare i pin extra D31/D32 esclusivi DFM.

| Risorsa | Segnali / pin Daisy |
| --- | --- |
| SPI1 ADC | SCK D8, MISO D9, MOSI D10, CS D7 |
| ADC controllo | CONVST D4 (candidato timer PC8/TIM8_CH3), BUSY D3, RESET D5 |
| SPI3 DAC | SCK D2, MOSI D6, SYNC D0 |
| DAC controllo | LDAC D1, CLR D13, tramite level shift |
| I²C1 | SCL D11, SDA D12; OLED e MCP23017 0x20 |
| Consenso uscite | OUTPUT_PERMIT D14 |
| Encoder A/B | E1 D15/D16, E2 D17/D18, E3 D19/D20, E4 D21/D22 |
| Expander reset | D23 |
| Click e tasti | MCP23017 port A: click 1–4, poi tasti 1–4 |
| Richieste uscite | MCP23017 port B: OUT1–4, poi CTRL1–4 |

A/B degli encoder restano su MCU per evitare dipendenza dal traffico OLED.
MCP23017 gestisce solo click/tasti e richieste statiche. I²C non trasporta audio.
Pull-up aggiuntive I²C DNP finché non si misurano quelle dell'OLED; tutte a 3,3 V.
Il DAC Adafruit non occupa più il bus sulla nuova PCB.

## Budget temporale da dimostrare su hardware

Obiettivo: ADC 96 kframe/s, audio elaborato a 48 kHz con filtro digitale e
conversione di frequenza 2:1; CTRL aggiornati a circa 1 kHz. Non usare una semplice
selezione di un campione ogni due senza filtro digitale antialias.

SPI ADC a 25 MHz: 8 × 18 = **144 clock = 5,76 µs** per lettura; il periodo ADC è
10,417 µs. In software mode CS può restare basso per l'intero frame: SPI a 8 bit
legge **18 byte**, poi si ricostruiscono otto valori signed a 18 bit. Non impostare
alla cieca DMA a 18 bit: libDaisy configura l'allineamento DMA SPI per byte.
`ConverterProtocol.h` verifica questo formato su host, non i timing reali.
Aggiungere conversione BUSY, comandi, DMA/cache, IRQ e margini al conto di banda.

DAC a 25 MHz: ogni parola è 32 bit, 1,28 µs; otto parole richiedono **10,24 µs**
più intervalli SYNC. LDAC aggiorna simultaneamente i canali dopo il caricamento.
48 kHz significa 20,833 µs per frame. Il settling può arrivare a 10 µs nelle
condizioni del datasheet; scheduling e filtri richiedono collaudo, soprattutto
per transizioni grandi. Questo non è un codec 24 bit con filtri audio integrati.

SPI1 e SPI3 devono operare su DMA separati; testare cache e priorità. Clock esatto,
timer, latenza, jitter, rumore e carico CPU sono ancora aperti. Gate/trigger
riconosciuti dall'ADC hanno latenza di campionamento/elaborazione, non sono ingressi
asincroni a latenza zero. Prevedere isteresi e test degli impulsi minimi.

## Alimentazione e meccanica

IDC10 ±12 V: pin 1/2 −12 V, 3–8 GND, 9/10 +12 V. Convertitore locale 5 V con
obiettivo almeno 1 A, poi ramo analogico filtrato; niente +5 V richiesto al case.
Il convertitore specifico, il fusibile e il filtraggio finale NON sono selezionati:
`UREG` è un envelope, non una distinta d'acquisto. Verificare dropout, ripple,
consumo e spunto, e aggiungere protezione di corrente dimensionata. Considerare
il bilancio di potenza del case, non solo la corrente di uscita del convertitore.
Per ora scollegare Eurorack prima di USB: coesistenza delle fonti non validata.

Due PCB da 96,2 × 110,5 mm dietro un pannello proposto da 101,2 × 128,5 mm
(20 HP nominali 101,6 mm). Quote reali dei frontali da misurare. Connettore 2×20
con pin corrispondenti sulle due schede: verso di innesto/chiave e stack height
ancora da verificare. Nessuna scala automatica delle impronte.
