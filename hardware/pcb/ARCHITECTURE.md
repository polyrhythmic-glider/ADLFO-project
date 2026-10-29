# Architettura D

Il circuito passa la continua. IN1–4 sono ingressi audio/CV/gate/trigger;
OUT1–4 sono uscite audio/CV/envelope/LFO/gate/trigger. CTRL1–4 possono essere
configurati come ingresso oppure uscita CV/gate/trigger, mantenendo la lettura
ADC anche quando il driver è abilitato. Il codec integrato della Daisy non è
usato per queste porte.

## Conversione e analogica

```text
IN1–4 → 1 kΩ → ADG5412F → filtro attivo 4 poli → 47 Ω → ADC CH1–4
CTRL1–4 → 1 kΩ → ADG5412F → RC 1 kΩ / 1 nF → ADC CH5–8

Daisy SPI1 ↔ AD7606C-18                 Daisy SPI3 → AHCT125 → DAC8568B
                                                               ↓
                         8 amplificatori differenziali, 4×VDAC − 4×VREF_HALF
                                                               ↓
                               OUT1–4: filtro attivo 4 poli; CTRL: diretto
                                                               ↓
                                   1 kΩ → ADG5412F → OUT1–4 / CTRL1–4
```

ADC AD7606C-18BSTZ: AVCC 5 V, VDRIVE 3,3 V, otto canali simultanei. Il firmware
nuovo dovrà selezionare software mode, range nominale ±10 V, banda 220 kHz,
una sola linea DOUTA e il formato senza CRC/header previsto dal protocollo host.
Ogni ingresso negativo è a massa. REFIN usa il riferimento interno; REFCAP,
REGCAP1/2 e ciascun AVCC hanno condensatori locali.

DAC DAC8568BPW: span 0…2,5 V con riferimento interno attivato via software,
reset a metà scala. Due SN74AHCT125 a 5 V adattano clock, dati, SYNC, LDAC e CLR.
Le resistenze serie da 33 Ω sono sul clock/dati ADC e DAC. LDAC aggiorna gli
otto canali dopo il caricamento delle rispettive parole.

Otto stadi OPA4197 con rapporti resistivi 10 kΩ / 40 kΩ producono circa ±5 V
a vuoto da 0…2,5 V. Un follower separato genera 1,25 V dal riferimento DAC.
Le tre sezioni inutilizzate sono chiuse a follower con ingresso a massa.
Resistori 0,1% e calibrazione sono necessari; il progetto non garantisce V/oct.
La resistenza serie di uscita da 1 kΩ più lo switch introduce errore sotto carico
(circa 1% già con un carico da 100 kΩ, prima degli altri errori).

Gli otto percorsi audio (quattro ingressi, quattro uscite) hanno due sezioni
Sallen–Key a guadagno unitario, con R1=R2=11 kΩ 0,1%. Prima sezione:
Cfeedback=820 pF, Cground=680 pF; seconda: 1,8 nF / 270 pF, tutti C0G 1%.
La risposta ideale è circa −3 dB a 20 kHz in uscita, −3,4 dB in ingresso
(inclusa la resistenza serie). `analog_check.py` verifica topologia, valori e
256 combinazioni delle tolleranze per percorso. Non simula il comportamento
reale degli operazionali, distorsione o stabilità. CTRL usa solo il filtro EMI.

## Protezione e consenso

Quattro ADG5412F, due per gli ingressi e due per le uscite. I terminali protetti
S guardano i jack; D guarda il circuito. Gli ingressi hanno 1 kΩ / 1 W prima
dello switch; le uscite hanno 1 kΩ / 1 W fra amplificatore/filtro e switch.
Il circuito non attribuisce al modulo intero il limite ±55 V del solo IC.
I normali dei soli IN1–4 sono a massa per fissare lo stato senza patch.
I normali di CTRL e OUT restano aperti: non devono cortocircuitare un'uscita.

Le otto richieste REQ passano attraverso AND SN74LVC08. Il consenso comune è
`SAFE_PERMIT = SAFE_LATCH AND OUTPUT_PERMIT`. Il GPIO OUTPUT_PERMIT ha pull-down;
richieste e comandi degli switch hanno pull-down dedicati.

Una sezione SN74HCS74 con ingressi Schmitt memorizza l'abilitazione sul fronte crescente del permit.
`SAFE_CLEAR_N` cancella il latch quando intervengono watchdog TPS3828, monitor
5 V TPS3808, comparatori dei rail ±12 V oppure un fault degli ADG. Dopo un fault
il ritorno dei rail non riattiva le uscite: serve un nuovo fronte di permit.
Portare permit basso apre sempre gli switch, anche se il latch conserva lo stato.

Soglie nominali dei monitor: +12VA sotto 10,41 V, −12VA meno negativo di −10,39 V,
+5A sotto 4,82 V; il watchdog supervisiona anche il 3,3 V. Il riferimento dei
comparatori è un divisore del 3,3 V, indipendente dal riferimento DAC. Le soglie
reali comprendono tolleranze, deriva e tempi di avvio: vanno misurate.
Il TPS3808G01 con il divisore presente può intervenire fra 4,712 e 4,928 V
e richiedere fino a 5,075 V per rilasciare reset; il RECOM ammette ±5%.
Questo è un problema di dimensionamento ancora aperto: serve rivedere insieme
regolazione e supervisione. Abbassare soltanto la soglia non garantisce il
minimo AVCC di 4,75 V dell'ADC. I monitor ±12 V dipendono dal 3,3 V e non
stabiliscono soglie assolute indipendenti dalla sua variazione.

Sequenza del backend da implementare: permit basso, REQ a zero, inizializzazione
ADC/DAC e riferimento, zero volt su ogni DAC, attesa di assestamento, verifica
dei monitor e calibrazione valida, selezione REQ, poi fronte di permit.
Al primo avvio l'AD7606C-18 richiede complessivamente oltre 2 s fra power-up
e device setup (Rev B, tabella 3, nota 3); il solo tempo di reset successivo
non descrive questa condizione.
A ogni cambio direzione: aprire la porta, preparare il valore e attendere prima
di richiuderla. Alimentare periodicamente WATCHDOG dal percorso che verifica
il funzionamento della conversione, evitando un interrupt indipendente che
continui a farlo anche quando l'elaborazione è bloccata.

## Collegamenti digitali

| Funzione | Pin Daisy |
| --- | --- |
| DAC SPI3 | SYNC D0, LDAC D1, SCK D2, MOSI D6, CLR D13 |
| ADC SPI1 | BUSY D3, CONVST D4, RESET D5, CS D7, SCK D8, MISO D9, MOSI D10 |
| I²C1 | SCL D11, SDA D12 |
| OUTPUT_PERMIT | D14 |
| Encoder A/B | E1 D15/D16; E2 D17/D18; E3 D19/D20; E4 D21/D22 |
| Reset MCP23017 | D23 |
| WATCHDOG | D24 |
| FAULT_N / SAFE_CLEAR_N | D25 |
| OLED RESET | D26 |

MCP23017 a 0x20, package **SOIC28**. GPA0–3 sono click E1–4, GPA4–6 tasti K1–3,
GPB0 è K4. GPB1–7 comandano REQ1–7; GPA7 comanda REQ8. GPA7/GPB7 sono usati
solo come uscite, rispettando la limitazione del produttore. La mappa precedente
QFN e la precedente assegnazione di un tasto a GPA7 sono state corrette.
I pull-up I²C da 2,2 kΩ sono montati: verificare il parallelo con quelli presenti
sul display. OLED SSD1315 a 0x3c, predisposto fisicamente per I²C.

Il connettore 2×20 porta segnali analogici e comandi al pannello; i pin 1…40
hanno identiche coordinate fisiche sulle schede sovrapposte. Il socket posteriore
ha numerazione specchiata rispetto all'header: non scambiare impronte o lato.

## Tempi e firmware

Target ADC: 96 kframe/s; audio elaborato: 48 kHz; CTRL: circa 1 kHz.
ADC: 8×18 bit = 18 byte = 5,76 µs a 25 MHz, contro un periodo di 10,417 µs.
DAC: 8×32 bit = 10,24 µs a 25 MHz, contro 20,833 µs a 48 kHz.
Questi conti coprono solo il payload: conversione/BUSY, intervalli SYNC,
settling, DMA/cache e jitter richiedono misure. Due periferiche SPI separate
non garantiscono DMA simultaneo: il driver libDaisy standard condivide gli
stream DMA e serializza le richieste. A 25 MHz i soli payload richiedono il
104,448% del tempo; inoltre il clock standard SPI123 da 25 MHz con prescaler
minimo /2 produce 12,5 MHz di SCK. Il solo frame ADC richiede allora 11,52 µs,
oltre il periodo disponibile di 10,417 µs. Il backend deve configurare clock,
risorse DMA e uno schedule dimostrabile; questi target non sono impostazioni
già funzionanti. Serve anche il filtro digitale per decimare 96→48 kHz.

La simulazione completa dei filtri dà −3,403 dB in ingresso e −2,988 dB in
uscita a 20 kHz. Senza interpolazione DAC, a 48 kHz l'immagine di un tono
20 kHz compare a 28 kHz a circa −11,49 dBc, includendo ZOH e filtro analogico.
Un disturbo a 76 kHz che aliasa a 20 kHz nell'ADC riceve circa 43,54 dB di
reiezione relativa dal solo filtro esterno. Occorre fissare banda utile e
reiezioni richieste, poi dimensionare insieme filtri, frequenze e traffico SPI.

`platform/` contiene policy e protocollo verificabili su host. `Adolfo/` rimane
il firmware del prototipo con DAC MCP4728: **non pilota questa PCB**. La nuova
scheda richiede backend, temporizzazione e collaudo prima di un uso musicale.
Gate/trigger letti via ADC hanno latenza e una durata minima da qualificare.

## Alimentazione e layout

IDC10: pin 1/2 −12 V, 3…8 GND, 9/10 +12 V. Fusibili ripristinabili e diodi serie
proteggono i due rail. RECOM R-78E5.0-1.0 genera +5D dal positivo; la ferrite
BLM21PG601SN1D separa il ramo +5A. La Daisy genera +3V3. Non serve +5 V dal case.
L'ingresso previsto per il modulo assemblato è solo IDC10 Eurorack: +5D va
al pin VIN 39 della Daisy, non alla sua USB-C. Lasciare USB-C scollegata;
per programmare via USB estrarre la Seed dal carrier a case spento e scollegato.
Il carrier non può disabilitare il circuito USB di alimentazione interno alla Seed.
Il budget preliminare assegna fino a circa 0,7 A al ramo 5 V: consumi reali,
spunto, ripple, caduta sui fusibili e termica devono essere misurati.
La protezione USB/VIN della Seed non risolve il sequenziamento dell'ADC:
con USB e case spento, VDRIVE può essere a 3,3 V mentre AVCC è a zero,
superando il limite AVCC + 0,3 V. Anche lo spegnimento dei rail va analizzato.
Non collegare USB con il carrier spento prima di risolvere alimentazione e
iniezione dai segnali host; il permit delle uscite non protegge questi pin.
Il rilascio resta bloccato su questo punto: una procedura di accensione non
sostituisce un circuito che rispetta i limiti in tutte le sequenze previste.

Principale a quattro strati: F.Cu prevalentemente analogica, In1.Cu piano GND,
In2.Cu e B.Cu per gli altri percorsi; logica, Daisy e regolatore sul retro.
Il router non usa il piano GND per piste di segnale. Frontale a due strati.
Piste normali, +3V3 e +5A 0,20 mm; dorsali dei rail da 0,30 a 0,50 mm, distanze minime native 0,15 mm,
via 0,60 / foro 0,30 mm; il router usa un piccolo margine sulle distanze.
I condensatori critici di riferimento/REGCAP sono sotto l'ADC; la validazione
controlla la vicinanza al pin, oltre alla correttezza dei collegamenti.

Le misure e il montaggio nominale sono in [PARTS.md](PARTS.md). Una verifica CAD
non dimostra ingombro fisico, rumore, comportamento ai corti o stabilità analogica.
