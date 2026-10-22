# Uscite analogiche — da realizzare

[Schema breadboard proposto](breadboard_mcp4728_tl074_4out.svg) · [PDF](breadboard_mcp4728_tl074_4out.pdf).

Obiettivo: DAC 0–2 V → quattro OUT circa 0–5 V.
Per canale: DAC → 10 kΩ → ingresso +; ingresso − → 10 kΩ → GND;
uscita → 15 kΩ → ingresso −; uscita → 2,2 kΩ / 0,5 W → tip; sleeve a GND.

TL074: pin 4 al rail positivo, pin 11 al negativo; 100 nF da ogni rail a GND.
Richiede alimentazione duale circa ±12 V: la sola USB non basta.
Alimentazione, protezioni e montaggio definitivo restano da concordare e collaudare.
Le quattro resistenze da 1 kΩ attuali appartengono al montaggio provvisorio.
