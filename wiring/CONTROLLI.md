# Encoder, tasti e OLED

Il front panel è già cablato dall'utente. Questa tabella è il riferimento per
verificarlo rispetto al firmware attuale, che genera ancora un solo inviluppo.
I nomi Dn sono GPIO Daisy, non numeri fisici dei piedini.
La corrispondenza con tutti i piedini fisici e la verifica del budget GPIO sono
in [PINOUT.md](PINOUT.md).

## Collegamenti

| Colonna | CLK / A | DT / B | Click encoder | Tasto separato |
| --- | --- | --- | --- | --- |
| C1 | D0 | D1 | D2 | B1 → D25 |
| C2 | D3 | D4 | D5 | B2 → D24 |
| C3 | D7 | D8 | D9 | B3 → D26 |
| C4 | D10 | D13 | D14 | B4 → D27 |

Encoder nudi: comune quadratura a DGND; click tra il GPIO indicato e DGND.
Moduli encoder: eventuale alimentazione a 3V3_D e massa DGND.
Ogni tasto separato chiude tra il proprio GPIO e DGND. Il firmware gestisce
pull-up e debounce. Se il verso di rotazione è errato, verificare/scambiare A e B.

| OLED | Daisy |
| --- | --- |
| VCC | 3V3_D |
| GND | DGND |
| SCL | D11 |
| SDA | D12 |

Il driver corrente è SSD1306 128×64; il codice prova 0x3C e 0x3D a 100 kHz.
Il controller effettivo del display va identificato se non risponde correttamente.
Nel progetto finale SDA/SCL sono condivisi con il MCP4728 a 0x60.

## Funzioni del firmware attuale

| Controllo | Rotazione | Pressione |
| --- | --- | --- |
| E1 | Rise | Breve: trigger AD; lunga: AD/LFO |
| E2 | Fall; navigazione menu | Breve: curva/selezione/indietro; lunga: menu |
| E3 | Symmetry | Riporta al centro |
| E4 | Livello uscita | Riporta al 100% |
| B1 | — | Trigger |
| B2 | — | AD/LFO |
| B3 | — | Cambia curva |
| B4 | — | Menu / schermata principale |

E1/E3/E4 modificano i parametri nella schermata principale; E2 naviga nel menu.
La pressione lunga E1/E2 viene riconosciuta dopo 750 ms. ENC DEBUG mostra i
quattro encoder e i tasti. Queste assegnazioni non sono ancora un controllo
indipendente di quattro inviluppi.

Sorgente dei pin: [PanelControls.h](../DaisyMonoEnvelope/PanelControls.h).
Procedura di build: [README firmware](../DaisyMonoEnvelope/README.md).
Per jack, alimentazione e stadi analogici seguire [SCHEMI.md](SCHEMI.md).

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
