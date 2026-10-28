# Adolfo — firmware del prototipo funzionante

VA/VB/VC/VD = OUT1/2/3/4, nominalmente 0–2 V. Quattro AD/LFO indipendenti;
ognuno mantiene tempi, simmetria, livello, curva e destinazione CV durante l’uso.
Avvio/reset: tutti in AD a zero; impostazioni non salvate in memoria permanente.

- B1/B2/B3/B4 selezionano direttamente CH 1/2/3/4, corrispondenti a OUT1/2/3/4,
  anche nelle impostazioni. Nessuna pagina CHANNEL o funzione alternativa sui pulsanti.
- Ruota E1/E2: Rise/Fall; E3: simmetria; E4: livello del canale selezionato.
- Click E1: trigger AD / risincronizzazione LFO. Pressione lunga E1 (almeno 750 ms,
  azione al rilascio): AD/LFO. Click E2: curva; tenerlo premuto non apre il menu.
- Click E3/E4: reset simmetria al 50% / livello al 100%.
- **E1 + E4 tenuti insieme per 900 ms: impostazioni.** La combinazione non attiva
  trigger, cambio modo o reset. Rilascia entrambi prima di usarla di nuovo.

Schermata principale: **CH 1–4** grande in alto, modo/curva e uscita corrente a destra;
Rise/Fall con unità al centro, simmetria/livello in basso.
[Anteprima delle schermate](ui-preview.png).

Nelle impostazioni, ruota E2 e premi per aprire una voce:

- **CV TARGET**: E2 sceglie OFF, RISE+FALL, RISE, FALL o LEVEL per il canale selezionato;
  qui si leggono anche il CV corrente e l'abilitazione dell'ingresso.
- **CONTROLS**: guida ai comandi.
- **ENCODER TEST**: contatori di rotazione e stato degli switch/pulsanti;
  ogni encoder azzera il proprio contatore al click, compreso E2.
- **OUTPUT TEST**: tensione fissa su una sola uscita.
- **BACK**: ritorno alla schermata principale.

E2 premuto torna dalle sottopagine alle impostazioni, tranne in ENCODER TEST:
lì si torna con E1 + E4 tenuti premuti. La stessa combinazione torna alle impostazioni
da ogni sottopagina e le chiude quando si è già nel menu.

Gli altri canali continuano mentre ne modifichi uno. CV sui tempi li allunga;
LEVEL attenua il livello E4 (CV minimo = zero, massimo = livello E4).

Impostazioni → OUTPUT TEST: sospende tutti gli AD/LFO. B1–B4 scelgono l’uscita
e riportano la tensione a zero, anche riselezionando lo stesso canale;
E2 imposta 0/1/2 V. Le altre uscite restano a zero.
Click E2 o E1 + E4 tenuti premuti escono con tutti i canali in AD a zero.
Misurare tip rispetto a sleeve,
con jack scollegati dagli strumenti.

[HardwareConfig.h](HardwareConfig.h): SDA D12, SCL D11; TRIG/CV disabilitati e senza pin assegnati.
Dopo il montaggio: assegnare pin e abilitazioni per canale, verificare inversione trigger
e scala CV. Ogni TRIG avvia il proprio AD o risincronizza il proprio LFO.
La scala CV preimpostata vale solo per il partitore proposto 100k/33k e campo 0–10 V.

Compilazione dalla radice: `make -C Adolfo`.
Binario: `Adolfo/build/Adolfo.bin`. Firmware indicato dall’utente come test funzionante. La rinomina non modifica
il comportamento; nessun nuovo caricamento è stato eseguito in questa sessione.
Uscite elettriche ancora da misurare.
Test locali: `make -C Adolfo test`.

Motori a 10 kHz; invio dei quattro DAC dal loop con obiettivo 1 kHz, I2C a 400 kHz
con OLED a blocchi. Frequenza effettiva e tensioni da misurare sul montaggio.
[Protocollo MCP4728](https://ww1.microchip.com/downloads/en/DeviceDoc/22187E.pdf):
riferimento interno 2,048 V, limite 4000, scritture volatili; EEPROM invariata.

Questo firmware è conservato per il prototipo Daisy + MCP4728: non è il driver della nuova PCB universale. Vedere ../hardware/pcb/README.md.
