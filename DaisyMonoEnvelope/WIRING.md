# Collegamenti breadboard

Il pannello previsto usa otto jack mono da 3,5 mm: sei ingressi e due
uscite.

1. `TRIG IN`;
2. `TIME CV IN`;
3. `RISE CV IN`;
4. `FALL CV IN`;
5. `SHAPE CV IN`;
6. `LEVEL CV IN`;
7. `ENV OUT`;
8. `AUX OUT`.

Il firmware attuale gestisce già `TRIG IN`, `TIME CV IN` ed `ENV OUT`.
I quattro nuovi ingressi CV e `AUX OUT` sono la predisposizione hardware
per la prossima estensione del firmware: cablarli non basta, da soli, ad
attivarne le funzioni.

Usare preferibilmente jack `TS`: Tip è il segnale e Sleeve è la massa. Se si usa un jack TRS/TRRS, identificare i contatti con un multimetro, collegare solo Tip e Sleeve e lasciare Ring/Ring2 scollegati.

Spegnere e scollegare la Daisy prima di modificare la breadboard. Non collegare Trigger o CV direttamente ai pin Daisy: i circuiti di protezione descritti sotto sono obbligatori.

## Tabella completa

| Componente | Pin componente | Pin Daisy | Note |
|------------|-----------------|-----------|------|
| Encoder 1 | CLK | `D0` | Ingresso GPIO con pull-up interno |
| Encoder 1 | DT | `D1` | Ingresso GPIO con pull-up interno |
| Encoder 1 | SW | `D2` | Pulsante attivo verso massa, pull-up interno |
| Encoder 1 | `+` | `3V3_D` | Mai 5 V |
| Encoder 1 | GND | `DGND` | Massa comune |
| Encoder 2 | CLK | `D3` | Ingresso GPIO con pull-up interno |
| Encoder 2 | DT | `D4` | Ingresso GPIO con pull-up interno |
| Encoder 2 | SW | `D5` | Pulsante attivo verso massa, pull-up interno |
| Encoder 2 | `+` | `3V3_D` | Mai 5 V |
| Encoder 2 | GND | `DGND` | Massa comune |
| Trigger In | Uscita del circuito NPN | `D6` | Non collegare il Tip direttamente |
| Potenziometro B10K | Piedino esterno 1 | `AGND` | Estremo a 0 V |
| Potenziometro B10K | Piedino centrale | `A0 / D15` | Cursore verso ADC |
| Potenziometro B10K | Piedino esterno 2 | `3V3_A` | Estremo a 3,3 V |
| Time CV In | Uscita del partitore protetto | `A1 / D16` | ADC, massimo assoluto al pin 3,3 V |
| Rise CV In | Uscita del partitore protetto | `A2 / D17` | ADC, massimo assoluto al pin 3,3 V |
| Fall CV In | Uscita del partitore protetto | `A3 / D18` | ADC, massimo assoluto al pin 3,3 V |
| Shape CV In | Uscita del partitore protetto | `A4 / D19` | ADC, massimo assoluto al pin 3,3 V |
| Level CV In | Uscita del partitore protetto | `A5 / D20` | ADC, massimo assoluto al pin 3,3 V |
| OLED I2C | GND | `DGND` | Massa comune |
| OLED I2C | VDD/VCC | `3V3_D` | Non alimentare a 5 V |
| OLED I2C | SCK/SCL | `D11` | I2C1 SCL, PB8 |
| OLED I2C | SDA | `D12` | I2C1 SDA, PB9 |
| Breadboard | Ponte di massa | `AGND` verso `DGND` | Obbligatorio per una massa comune |
| Envelope Out | DAC Daisy | `D23 / A8 / DAC OUT 1` | PA4, DAC hardware canale 1 |
| Aux Out | DAC Daisy | `D22 / A7 / DAC OUT 2` | PA5, DAC hardware canale 2 |

## 1. Trigger In: circuito NPN

Componenti:

- Q1: `2N3904` oppure altro NPN equivalente;
- R1: `100 kOhm`;
- R2: `1 MOhm`;
- R3: `47 kOhm`;
- D1: `1N4148`.

```text
Tip TRIGGER IN
      |
    R1 100k
      |
      +---------- Base Q1
      |
    R2 1M
      |
     DGND

Q1 emettitore  ---------- DGND
Q1 collettore  ---------- D6
Q1 collettore  -- R3 47k -- 3V3_D
Sleeve jack    ---------- DGND
```

D1 protegge la giunzione base-emettitore dalle tensioni negative:

```text
D1 anodo   -> emettitore / DGND
D1 catodo  -> base Q1
```

Il circuito è invertente: senza gate D6 è alto; con un gate positivo Q1 porta D6 basso. Il firmware usa `GateIn` con inversione standard. Verificare sul datasheet il pinout fisico del transistor: 2N3904 e BC547 possono avere piedini in ordine differente.

## 2. I cinque ingressi CV: partitore e protezione

Tutti i cinque ingressi CV sono progettati per una tensione unipolare
nominale `0 ... 10 V`. Ogni jack deve avere il proprio partitore, il proprio
condensatore e due diodi di protezione. Non condividere resistori o diodi fra
ingressi diversi.

Le funzioni previste sono:

| Jack | Funzione prevista |
|------|-------------------|
| `TIME CV IN` | Allunga insieme Rise e Fall |
| `RISE CV IN` | Modifica solo il tempo di Rise |
| `FALL CV IN` | Modifica solo il tempo di Fall |
| `SHAPE CV IN` | Modifica/miscela la curva LOG, LIN ed EXP |
| `LEVEL CV IN` | Regola l'ampiezza dell'inviluppo |

Componenti complessivi per i cinque ingressi:

- cinque resistori `100 kOhm`;
- cinque resistori `47 kOhm`;
- cinque condensatori `10 nF`;
- dieci diodi Schottky `1N5817` (vanno bene anche `1N5819`, `BAT54` o
  `BAT85`).

Assegnazione dei componenti:

| Ingresso | Serie | Verso AGND | Filtro | Clamp basso | Clamp alto | Pin Daisy |
|----------|-------|------------|--------|-------------|------------|-----------|
| Time CV | R4 100k | R5 47k | C1 10nF | CVT-L | CVT-H | `A1 / D16` |
| Rise CV | R7 100k | R8 47k | C2 10nF | CVR-L | CVR-H | `A2 / D17` |
| Fall CV | R9 100k | R10 47k | C3 10nF | CVF-L | CVF-H | `A3 / D18` |
| Shape CV | R11 100k | R12 47k | C4 10nF | CVS-L | CVS-H | `A4 / D19` |
| Level CV | R13 100k | R14 47k | C5 10nF | CVL-L | CVL-H | `A5 / D20` |

Ripetere questo circuito una volta per ogni riga della tabella:

```text
Tip jack CV -- 100k --+------ pin ADC indicato
                      |
                      +-- 47k ---- AGND
                      |
                      +-- 10nF --- AGND

Sleeve jack CV -------------------- AGND
```

Collegare i due `1N5817` al nodo ADC di ogni ingresso. La banda stampata sul
diodo identifica il catodo:

```text
Clamp basso: anodo AGND,    catodo/banda al nodo ADC
Clamp alto:  anodo nodo ADC, catodo/banda a 3V3_A
```

Ogni partitore produce approssimativamente:

| Tensione al jack | Tensione sul nodo ADC |
|------------------|----------------|
| 0 V | 0 V |
| 3,3 V | 1,05 V |
| 5 V | 1,60 V |
| 10 V | 3,20 V |

Non usare intenzionalmente CV negative: il diodo basso le limita per
protezione, ma questo circuito non ne conserva la parte negativa.

## 3. Envelope Out

Componenti:

- R6: `1 kOhm`.

```text
D23 / DAC OUT 1 -- R6 1k -- Tip ENVELOPE OUT
AGND ---------------------- Sleeve ENVELOPE OUT
```

La punta della sonda dell'oscilloscopio va sul Tip/dopo R6; la massa della sonda va su AGND. L'uscita è unipolare `0 ... circa 3,3 V`, quindi ha un'ampiezza inferiore ai tipici envelope Eurorack 0 ... 8 V.

## 4. Aux Out: secondo DAC interno

Componenti:

- R15: `1 kOhm`.

```text
D22 / DAC OUT 2 -- R15 1k -- Tip AUX OUT
AGND ----------------------- Sleeve AUX OUT
```

`AUX OUT` usa il secondo DAC hardware della Daisy e può generare `0 ... circa
3,3 V`. La funzione verrà scelta dal firmware, per esempio secondo envelope,
inviluppo invertito, LFO o random CV. Non applicare mai una tensione esterna
a D22 o al Tip di questa uscita.

## 5. Distinta componenti completa

Per tutti gli otto jack, inclusi i tre collegamenti originali:

| Quantità | Componente | Uso |
|----------|------------|-----|
| 6 | `100 kOhm` | Trigger e cinque partitori CV |
| 6 | `47 kOhm` | Pull-up Trigger e cinque partitori CV |
| 2 | `1 kOhm` | Protezione delle due uscite DAC |
| 1 | `1 MOhm` | Pull-down base Trigger |
| 5 | `10 nF` | Filtro dei cinque ingressi CV |
| 10 | `1N5817` | Clamp dei cinque ingressi CV |
| 1 | `1N4148` | Protezione base-emettitore Trigger |
| 1 | `2N3904` | Condizionamento Trigger |
| 8 | jack mono TS 3,5 mm | Sei ingressi e due uscite |

## Controlli prima di collegare i pin Daisy

1. Controllare con la continuità che tutti gli Sleeve siano collegati alla massa corretta.
2. Verificare il ponte `AGND-DGND`.
3. Alimentare la breadboard senza collegare D6 e i cinque pin ADC ai rispettivi nodi.
4. Sul collettore Q1 misurare circa 3,3 V senza trigger e circa 0 V applicando un segnale positivo al Tip.
5. Su ciascun nodo CV misurare circa 0 V con 0 V al Tip e circa 1,05 V usando 3V3 come segnale di prova.
6. Verificare con il multimetro l'orientamento dei dieci diodi prima di collegare la Daisy.
7. Collegare D6 e i pin A1-A5 solamente dopo che queste misure sono corrette.
8. Prima di collegare un sintetizzatore, verificare all'oscilloscopio che D22 e D23 restino fra 0 e circa 3,3 V.
9. Non applicare mai tensioni esterne a `ENV OUT`, `AUX OUT`, D22 o D23.

## Note pratiche

- Encoder e OLED usano `3V3_D/DGND`; potenziometro, CV e DAC usano `3V3_A/AGND`.
- Collegare AGND e DGND sulla breadboard in un solo punto comune.
- Se un encoder gira al contrario, scambiare CLK e DT.
- Se il potenziometro lavora al contrario, scambiare solo i due piedini esterni.
- `A0` è alias di `D15/PC0`; gli ingressi CV usano `A1/D16` fino ad `A5/D20`.
- `ENV OUT` e `AUX OUT` sono rispettivamente `D23/DAC1` e `D22/DAC2`.
- Il firmware assume SSD1306 128x64, I2C `0x3C`. Alcuni OLED usano `0x3D` o SH1106.
- Questa resta una prova su breadboard alimentata via USB, non un modulo Eurorack completo e non deve essere alimentata dal bus +/-12 V.
