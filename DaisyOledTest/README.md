# Diagnostica OLED

Firmware separato per verificare il display collegato alla Daisy.
**Caricarlo sostituisce il firmware ADLFO; non pilota il MCP4728.**

Cablaggio e alimentazione del display sono in
[wiring/CONTROLLI.md](../wiring/CONTROLLI.md): VCC 3,3 V, GND, SCL D11 e SDA D12.
Per la programmazione USB del montaggio Eurorack seguire
[SCHEMI.md](../wiring/SCHEMI.md): JP_VIN tolto e patch scollegate.

Il codice usa SSD1306 128×64, cerca 0x3C e 0x3D e comunica a 100 kHz.
Il controller reale non è identificabile dalle sole scritte sui quattro pin.

## Build e caricamento

Dalla radice del progetto:

```sh
make -C DaisyOledTest
```

Il binario è `build/DaisyOledTest.bin`, destinato alla flash interna.
Entrare in DFU tenendo BOOT, premendo/rilasciando RESET e rilasciando BOOT;
poi eseguire:

```sh
make -C DaisyOledTest program-dfu
```

## Risultato atteso

- Nessuna risposta I2C: tre lampeggi rapidi, pausa e nuovo tentativo.
- Risposta I2C: tutti i pixel accesi per due secondi, poi cornice,
  scritte DAISY OLED / TEST DISPLAY e contatore.
- Il LED cambia stato a ogni aggiornamento.

Una risposta I2C non conferma che il controller sia SSD1306. Se il display resta
nero, verificare cablaggio e modello. Al termine ricaricare il
[firmware principale](../DaisyMonoEnvelope/README.md) per tornare ad ADLFO.
