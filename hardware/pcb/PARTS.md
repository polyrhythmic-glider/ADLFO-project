# Materiale e candidati

**Non è ancora una lista per ordinare.** `output/bom.csv` contiene i candidati
con valori e note. Filtri, alimentazione e ingombri non sono finalizzati.

| Materiale posseduto | Impiego |
| --- | --- |
| Daisy Seed 3 | processore principale previsto; controllare ingombro USB-C |
| Daisy Seed 2 DFM | seconda scheda per verificare compatibilità; non montarle insieme |
| Due frontali vergini 20 HP | usarne uno dopo conferma di tutte le quote |
| Jack verticali PJ398SM/Thonkiconn | dodici jack, stessa meccanica per tutti i ruoli |
| OLED breakout | su connettore rialzato; misurare PCB, vetro e ordine pin |
| Encoder breakout | usare encoder nudi compatibili dopo verifica piedinatura/altezza; non dissaldare ancora gli esemplari del test |
| DAC Adafruit MCP4728 | mantenuto per il prototipo; non è convertitore audio né parte della nuova scheda |
| TL074 / MCP6004 / passivi precedenti | non assumerli sostituibili ai nuovi driver; selezionare package e prestazioni reali |

Nuovi blocchi candidati:

- 1× AD7606C-18 LQFP64: ADC simultaneo 8 canali, 18 bit; non il modello B.
- 1× DAC8568B TSSOP16: DAC 8 canali, gain 1, reset midscale; non C/D.
- 2× ADG5412FBRUZ TSSOP16: switch protetti, quattro canali ciascuno.
- 3× OPA4197ID SOIC14: otto stadi bipolari, riferimento bufferizzato e sezioni
  inutilizzate correttamente chiuse; scelta da validare per rumore/stabilità.
- 2× SN74AHCT125 per i cinque segnali DAC a 5 V.
- 2× SN74LVC08A per il consenso hardware degli otto switch.
- 1× MCP23017-E/SO, comandi lenti e richieste switch; encoder A/B direttamente MCU.
- Convertitore 5 V, protezione di corrente, filtri, reti resistive abbinate,
  condensatori di disaccoppiamento e zoccoli/connettore di stack da selezionare.
- Quattro encoder nudi con click e quattro pulsanti con altezza compatibile
  con i jack e la distanza dal pannello.

Per finalizzare servono misure o codici dei quattro encoder, pulsanti e OLED,
spessore e larghezza effettivi del frontale, profondità libera nel case e i
connettori già saldati sulle Daisy. Disponibilità, package, costo e capacità
richiesta per l'assemblaggio SMD vanno verificati prima dell'acquisto.

Il solo cambio software non aggiunge ADC, conversione audio o protezione alle
schede breakout attuali. Il prototipo funzionante resta indipendente da questo sviluppo.
