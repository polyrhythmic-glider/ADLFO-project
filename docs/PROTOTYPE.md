# Prototipo da preservare

L'utente identifica **DaisyMonoEnvelope**, ora `Adolfo/`, come firmware funzionante.
Il cambio di nome non cambia pin, algoritmo, protocollo DAC o comandi.
I nomi interni `adlfo` e `EnvelopeBank` descrivono il motore attuale e sono conservati.

Cablaggio documentato nel repository precedente:

- Daisy SDA D12 e SCL D11; DAC Adafruit MCP4728 via STEMMA QT.
- VA/VB/VC/VD verso OUT1–4 tramite 1 kΩ, sleeve a massa comune.
- Encoder/pulsanti: vedere `Adolfo/PanelControls.h`; conservati lo scambio B1/B2
  e la compensazione software del verso E3.
- OLED configurato dal firmware attuale. TRIG/CV esterni disabilitati e senza
  pin assegnati in `Adolfo/HardwareConfig.h`.

L'utente conferma il funzionamento del test, non una misura completa di livelli,
protezioni o accuratezza. Non abilitare ingressi proposti su cablaggi non verificati.
Il nuovo pinout della PCB universale NON va copiato su questo prototipo.

DaisyCv4Test era una diagnostica separata DAC/ADC; DaisyOledTest era una diagnostica
I²C/display. Entrambe rimosse dal progetto attivo, recuperabili nella storia Git.
