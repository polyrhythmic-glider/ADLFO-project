# Mappa completa dei pin — verifica del montaggio

Verificata il 2026-10-01 su pinout Seed3, libDaisy locale, PanelControls.h,
main.cpp e assegnazioni correnti dei dodici jack. Nessuna modifica al firmware.

**I jack sono 12:** 4 TRIG IN + 4 CV IN + 4 OUT. Tutti sono inclusi.
La mappa finale occupa **26 dei 31 GPIO esposti** della Seed3, senza conflitti.
Le quattro uscite provengono dal MCP4728 e non richiedono quattro GPIO dedicati.
Il numero di GPIO non è una verifica dello spazio fisico sulla perfboard.

## Conteggio

| Funzione | Quantità fisica | GPIO Daisy impegnati |
| --- | --- | --- |
| Rotazione encoder A/B | 4 encoder | 8 |
| Click encoder | 4 click | 4 |
| Tasti separati | 4 tasti | 4 |
| TRIG IN | 4 jack | 4 |
| CV IN | 4 jack | 4 ADC/GPIO |
| OLED + quad DAC | 2 dispositivi sullo stesso bus | 2, SDA/SCL condivisi |
| OUT dal quad DAC | 4 jack | 0 aggiuntivi oltre al bus |
| **Totale** | **12 jack + controlli + display** | **26** |

## Dodici jack, uno per uno

Le righe sono contate dall’alto guardando il pannello dal davanti; colonne da
sinistra a destra. Tutti gli Sleeve vanno a massa comune.

| Jack | Funzione | Collegamento di segnale |
| --- | --- | --- |
| J1 | TRIG IN 1 | Tip → circuito NPN → D6 |
| J2 | TRIG IN 2 | Tip → circuito NPN → D20 |
| J3 | TRIG IN 3 | Tip → circuito NPN → D21 |
| J4 | TRIG IN 4 | Tip → circuito NPN → D22 |
| J5 | CV IN 1 | Tip → partitore/protezioni/MCP6004 → D16 |
| J6 | CV IN 2 | Tip → partitore/protezioni/MCP6004 → D17 |
| J7 | CV IN 3 | Tip → partitore/protezioni/MCP6004 → D18 |
| J8 | CV IN 4 | Tip → partitore/protezioni/MCP6004 → D19 |
| J9 | OUT 1 | MCP4728 VA → TL074/resistenza serie → Tip |
| J10 | OUT 2 | MCP4728 VB → TL074/resistenza serie → Tip |
| J11 | OUT 3 | MCP4728 VC → TL074/resistenza serie → Tip |
| J12 | OUT 4 | MCP4728 VD → TL074/resistenza serie → Tip |

In fase USB VA–VD sono punti di misura; stadi TL074 e Tip OUT rimangono
scollegati secondo [AVVIO_USB.md](AVVIO_USB.md). Sono quattro uscite previste,
non quattro jack già pilotati dal firmware attuale.

## Tutti i 40 piedini della Seed3

Usare la colonna **pin fisico** per lo zoccolo e la colonna **nome** per il
firmware. Non contare i piedini a intuito: dal lato saldature la vista è specchiata.
Il pinout ufficiale collegato in fondo definisce l’orientamento.

| Pin fisico | Nome | Destinazione nel progetto |
| --- | --- | --- |
| 1 | D0 | E1 CLK/A |
| 2 | D1 | E1 DT/B |
| 3 | D2 | E1 click |
| 4 | D3 | E2 CLK/A |
| 5 | D4 | E2 DT/B |
| 6 | D5 | E2 click |
| 7 | D6 | J1 — TRIG IN 1, dopo condizionamento |
| 8 | D7 | E3 CLK/A |
| 9 | D8 | E3 DT/B |
| 10 | D9 | E3 click |
| 11 | D10 | E4 CLK/A |
| 12 | D11 | SCL I2C1 condiviso: OLED + MCP4728 |
| 13 | D12 | SDA I2C1 condiviso: OLED + MCP4728 |
| 14 | D13 | E4 DT/B |
| 15 | D14 | E4 click |
| 16 | AUDIO IN L | Non usato |
| 17 | AUDIO IN R | Non usato |
| 18 | AUDIO OUT L | Non usato |
| 19 | AUDIO OUT R | Non usato |
| 20 | AGND | Massa comune, collegata anche a DGND |
| 21 | 3V3_A | Alimentazione buffer MCP6004 e clamp CV |
| 22 | D15 / A0 | Libero / riserva |
| 23 | D16 / A1 | J5 — CV IN 1, dopo condizionamento |
| 24 | D17 / A2 | J6 — CV IN 2, dopo condizionamento |
| 25 | D18 / A3 | J7 — CV IN 3, dopo condizionamento |
| 26 | D19 / A4 | J8 — CV IN 4, dopo condizionamento |
| 27 | D20 / A5 | J2 — TRIG IN 2, dopo condizionamento |
| 28 | D21 / A6 | J3 — TRIG IN 3, dopo condizionamento |
| 29 | D22 / A7 | J4 — TRIG IN 4, dopo condizionamento |
| 30 | D23 / A8 | Non assegnato al pannello finale; DAC interno ancora attivo nel firmware attuale |
| 31 | D24 / A9 | B2 tasto |
| 32 | D25 / A10 | B1 tasto |
| 33 | D26 | B3 tasto |
| 34 | D27 | B4 tasto |
| 35 | D28 / A11 | Libero / riserva |
| 36 | D29 | Non assegnato; funzione alternativa USB esterna da preservare se prevista |
| 37 | D30 | Non assegnato; funzione alternativa USB esterna da preservare se prevista |
| 38 | 3V3_D | OLED, eventuali breakout controlli, pull-up trigger e MCP4728 |
| 39 | VIN | Nessuna alimentazione esterna nella fase USB; futuro ramo Eurorack protetto |
| 40 | DGND | Massa comune, collegata anche ad AGND |

## Pin rimasti e periferiche

- Non assegnati nella mappa finale: **D15, D23, D28, D29, D30**.
- D23 è ancora usato dal DAC interno del firmware: non riutilizzarlo adesso.
  Restano quindi quattro GPIO non impegnati anche considerando il codice corrente.
- D29/D30 sono PB14/PB15, la coppia della periferica USB esterna. libDaisy
  distingue questa periferica dalla USB interna usata sul connettore della scheda.
  La mappa attuale li lascia comunque liberi e non interferisce con il debug USB.
- D16–D19 sono realmente ADC A1–A4; i quattro CV non occupano pin solo digitali.
- D22 viene destinato a un trigger, quindi il secondo DAC interno non è disponibile
  contemporaneamente su quel pin. È intenzionale: le quattro OUT usano MCP4728.
- LDAC del MCP4728 va a GND nella configurazione corrente; RDY resta scollegato.
  Un controllo LDAC futuro potrebbe usare un GPIO di riserva, senza spostare i controlli.
- OLED 0x3C/0x3D e MCP4728 dichiarato 0x60 non hanno conflitti di indirizzo;
  verificare gli indirizzi reali con la futura diagnostica.
- Il bus condiviso richiede ancora coordinamento software e verifica della
  frequenza di aggiornamento: disponibilità dei pin non equivale a firmware pronto.
- Alimentazioni, masse, BOOT/RESET sulla scheda e connettore di debug dedicato
  non richiedono GPIO aggiuntivi nella mappa del pannello.

## Esito

**La configurazione corrente entra nei pin disponibili.** Per encoder, tasti,
OLED, quattro trigger, quattro CV e quad DAC non serve aggiungere un espansore GPIO.
La verifica è sulla mappa elettrica e sul codice: resta da controllare la continuità
dei cavetti saldati sul montaggio reale.

## Riferimenti

- [Pinout e funzioni Seed3, pagine 5–6](https://daisy.nyc3.cdn.digitaloceanspaces.com/products/seed3/Daisy_Seed3_datasheet.pdf)
- [Breakout Adafruit MCP4728](https://learn.adafruit.com/adafruit-mcp4728-i2c-quad-dac/pinouts)
- [Pin dei controlli nel firmware](../DaisyMonoEnvelope/PanelControls.h)
- [Firmware attuale](../DaisyMonoEnvelope/main.cpp)
- [Assegnazioni jack](pannello/functions.json)
- [Schemi di condizionamento](SCHEMI.md)
