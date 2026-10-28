# Prima della produzione

Stato C: **concept elettrico / due PCB non sbrogliate**. Ogni voce aperta è un
blocco reale; non rimuoverla perché il generatore passa i test.

- [ ] Prova di acquisizione ADC 96 kHz su SPI/DMA e aggiornamento DAC 48 kHz con LDAC.
- [ ] Configurazione software AD7606C-18: one-DOUT, range, bandwidth, reset, dati signed.
- [ ] Riferimento DAC, zero/midscale, timings e level shifting su entrambe le Daisy.
- [ ] Filtri analogici antialias e ricostruzione: il RC attuale non basta.
- [ ] Filtri digitali per passaggio 96→48 kHz, misura aliasing e banda utile.
- [ ] Dimensionare alimentazione, fusibile/protezione corrente, stabilità e termica.
- [ ] Supervisore brownout/rails, watchdog e comportamento a firmware bloccato.
- [ ] Dimostrare protezione ingressi e backfeed a scheda spenta; gate negativi/overshoot.
- [ ] Corti e patch uscita-uscita entro un inviluppo definito; verifica driver e switch.
- [ ] Offset/guadagno/linearità, deriva e uscita V/oct sotto carico.
- [ ] Isteresi trigger, durata minima impulsi, jitter e latenza reale.
- [ ] Verificare package, footprint, pin 1 e datasheet contro ogni componente ordinabile.
- [ ] Misure reali encoder, pulsanti, display e frontale; stack height e accesso USB.
- [ ] Valutare RAM/flash e budget CPU per quattro canali audio simultanei.
- [ ] Convertire i simboli terminali passivi in schema funzionale gerarchico con pin elettrici.
- [ ] Completare layout analogico, masse, riferimenti, disaccoppiamento e sbroglio.
- [ ] ERC/DRC nativi puliti e schema/PCB concordanti per ogni scheda.
- [ ] Collaudo limitato in corrente, tutte le transizioni di modo e cicli di accensione/reset.
- [ ] Solo dopo: dima definitiva e file Gerber/foratura di produzione.

Si possono completare schema e sviluppo senza modificare il prototipo già funzionante.
I file generati non certificano banda audio, prestazioni elettriche o producibilità.
