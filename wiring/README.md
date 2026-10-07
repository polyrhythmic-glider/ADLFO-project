# Hardware e cablaggio ADLFO

Stato aggiornato al 2026-10-01. Questa cartella è il riferimento hardware
corrente, separato dai sorgenti del firmware.

**Fase attuale: montaggio e debug alimentati dalla USB della Daisy.**
Alimentazione Eurorack e uscite TL074 vengono integrate dopo il collaudo della
sezione a 3,3 V. Seguire prima [AVVIO_USB.md](AVVIO_USB.md).

## Documenti da usare

| Documento | Contenuto |
| --- | --- |
| [AVVIO_USB.md](AVVIO_USB.md) | Cosa saldare adesso, cosa rimandare e prove con la sola USB |
| [PINOUT.md](PINOUT.md) | Verifica dei 12 jack e dei GPIO; tabella di tutti i 40 piedini Seed3 |
| [SCHEMI.md](SCHEMI.md) | Collegamenti elettrici, IDC, alimentazioni, trigger, CV, DAC, uscite e collaudo |
| [BOM.md](BOM.md) | Pezzi per circuito, totali e caselle di preparazione |
| [BOM_COMPONENTI.csv](BOM_COMPONENTI.csv) | 93 righe con sigle univoche, una per pezzo da predisporre |
| [CONTROLLI.md](CONTROLLI.md) | Encoder, tasti, OLED e funzioni del firmware attuale |
| [pannello/](pannello/README.md) | Disegno SVG, geometria e assegnazione proposta dei jack |

Gli schemi disponibili sono descrizioni elettriche e diagrammi testuali, non
una PCB pronta o una disposizione foro-per-foro della perfboard.

## Cosa è già presente

- Daisy Seed3 montata su zoccolo alza pin sopra la perfboard.
- Front panel già cablato dall'utente: 4 encoder con click, 4 tasti, 12 jack, OLED.
- Breakout Adafruit MCP4728, indirizzo dichiarato 0x60, già disponibile.
- Connettore IDC 16 poli (8×2) e alimentazioni Eurorack +12 V, GND, −12 V disponibili.
- Richiesto uso di diodi normali a foro passante: 1N4148 per segnali,
  1N4007 sui rami di alimentazione.

Il cablaggio del pannello è dichiarato completato; non equivale a un collaudo
documentato di tutti i contatti. Lo zoccolo alza pin non contiene regolatori
né protezioni.

## Progetto hardware corrente, ancora da montare e verificare

| Sezione | Scelta corrente | Stato |
| --- | --- | --- |
| Alimentazione | IDC, fusibili, diodi e filtro VIN della Seed3 | Cablaggio documentato; montaggio non confermato |
| Trigger | 4 circuiti 2N3904 + 1N4148 | Da montare e collaudare |
| CV | 4 ingressi 0–10 V, partitori, diodi e MCP6004 a 3,3 V | Da montare e collaudare |
| DAC | MCP4728 a 3,3 V, I2C condiviso con OLED | Disponibile; integrazione non confermata |
| Uscite | TL074 sui rail ±, guadagno 2,5 e resistori serie | 4 OUT circa 0–5 V da montare e collaudare |

La disposizione proposta è: J1–J4 trigger, J5–J8 CV, J9–J12 uscite.
È una mappa di progetto, non una conferma del collegamento fisico dei cavetti.
Le sigle effettive dei componenti già nelle scorte dell'utente non sono state
inventariate: la BOM specifica quelli necessari, non quelli mancanti.

Sono stati controllati riferimenti dei datasheet, conteggi BOM, conflitti GPIO
e calcoli nominali. Non è stato eseguito il collaudo elettrico sul montaggio reale.
Restano da verificare dimensioni della perfboard, disposizione dei fori,
assorbimenti, polarità, rumore, offset e comportamento all'accensione.

La revisione corrente non è qualificata per patch attive a modulo spento,
ESD o qualsiasi collegamento fra uscite contrapposte; non comprende mute hardware.
I limiti e le modalità di prova sono riportati negli [schemi](SCHEMI.md).

## Software effettivamente presente

Il codice in [DaisyMonoEnvelope](../DaisyMonoEnvelope/README.md) implementa:

- un motore AD/LFO con curve LOG/LIN/EXP;
- quattro encoder cliccabili e quattro tasti;
- OLED e pagina di debug dei controlli;
- trigger D6, CV D16 e uscita DAC interna D23;
- generazione a 10 kHz e scansione controlli a 1 kHz.

Non implementa ancora il MCP4728, i quattro motori, gli altri tre trigger/CV
o la calibrazione per il nuovo circuito. La scala CV nel codice è ancora 0,97;
il nuovo partitore richiede nominalmente circa 0,752 e successiva calibrazione.
Le quattro uscite esterne non diventano operative caricando il firmware attuale.

## Prossimo lavoro, in ordine

1. Preparare i 58 pezzi della fase USB nella BOM e verificarne le sigle reali.
2. Verificare Daisy e controlli sul pannello già cablato, con alimentazione USB.
3. Montare e misurare un trigger e un CV prima di collegarli ai pin Daisy.
4. Collegare MCP4728 a 3,3 V e predisporre quattro punti di misura VA–VD.
5. Aggiungere diagnostica firmware, replicare i circuiti e provare quattro canali.
6. Montare i 35 pezzi della fase Eurorack: alimentazione e stadi OUT TL074.
7. Collaudare alimentazione/stadi, completare integrazione e calibrazione.

Il passo immediato è il montaggio progressivo USB; le uscite amplificate
richiedono il successivo ramo analogico ±12 V.
