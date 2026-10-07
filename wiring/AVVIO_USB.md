# Prima fase: montaggio e debug via USB

Scelta dell'utente: montare e collaudare prima la sezione a 3,3 V alimentando
la Daisy dalla sua USB; integrare successivamente l'alimentazione Eurorack
e gli stadi di uscita amplificati. I collegamenti sono quelli di
[SCHEMI.md](SCHEMI.md), limitati ai blocchi indicati qui.

## Cosa montare adesso

| Blocco | Componenti della BOM | Alimentazione |
| --- | --- | --- |
| Daisy, encoder, tasti, OLED | Già presenti sul montaggio | USB Daisy, poi 3V3_D per moduli/OLED |
| Quattro trigger | Gruppi 03.1–03.4 | Pull-up a 3V3_D; massa comune |
| Buffer e quattro CV | Gruppi 04.0–04.4 | U1 MCP6004 a 3V3_A/GND |
| MCP4728 | Breakout già disponibile e gruppo 05 | 3V3_D/GND |

Totale aggiunte della fase USB: **58 pezzi** della BOM completa. La colonna
`fase` in [BOM_COMPONENTI.csv](BOM_COMPONENTI.csv) li identifica con `USB`.
Il front panel cablato, Daisy e il breakout già disponibili sono esclusi da
questo conteggio. Cablaggi, connettori eventuali e punti di misura sono separati.

## Cosa lasciare per dopo

- Gruppi 01 e 02: IDC, protezioni dei rail e filtro VIN.
- Gruppi 06.0–06.4: TL074 e quattro stadi OUT.
- Le quattro uscite finali ai jack, nominalmente circa 0–5 V.

Sono gli altri **35 pezzi**, marcati `Eurorack` nel CSV. Riservare spazio sulla
perfboard e accesso ai punti di collegamento prima di saldare i blocchi USB.

Il TL074 del progetto usa P_PLUS/P_MINUS; non alimentarlo a 3,3 V e non trattare
GND come sostituto del rail negativo in questo circuito. Lasciare U2 fuori dallo
zoccolo e VA–VD scollegati dagli stadi OUT durante la fase USB. Se gli stadi
fossero già montati, scollegare il percorso DAC → ingressi U2 prima di provarli
senza alimentazione analogica.

## Alimentazione e collegamenti USB

1. Il cavo USB entra nella porta della Daisy, senza alimentazioni esterne.
2. Collegare AGND e DGND alla massa comune della perfboard.
3. Lasciare VIN senza alimentazione esterna; se JP_VIN è già montato, toglierlo.
4. Lasciare il cavo IDC Eurorack scollegato.
5. Non unire con un ponte 3V3_A e 3V3_D.

Scollegare USB prima di ogni saldatura, inserimento di integrati o modifica.
Non collegare segnali da un sintetizzatore alla basetta spenta.

### MCP4728

| Pin breakout | Collegamento |
| --- | --- |
| VCC | 3V3_D |
| GND | Massa comune |
| SCL | D11, insieme a SCL OLED |
| SDA | D12, insieme a SDA OLED |
| LDAC | GND |
| RDY | Non collegato |
| VA/VB/VC/VD | Quattro punti di misura accessibili e isolati dagli stadi OUT |

C17 100 nF e C18 10 µF fra 3V3_D e GND vicino al breakout. Non aggiungere pull-up
a 5 V. I Tip dei quattro jack OUT restano isolati per questa fase; misurare
VA–VD con multimetro/oscilloscopio ad alta impedenza, massa alla massa comune.

Con il futuro firmware di prova, riferimento interno 2,048 V e guadagno 1:
codici 0/2048/4000 danno nominalmente circa 0/1,024/2 V sui punti DAC.
Sono tensioni da collaudo, non le quattro uscite amplificate a 5 V.
Prima dell'inizializzazione i valori dipendono dalla EEPROM: non assumere zero.

## Sequenza pratica di collaudo

1. Verificare che la Daisy avvii il firmware e provare encoder, tasti e OLED.
2. A USB scollegata montare TRIG1. Alimentare e misurare il collettore con GPIO
   scollegato: circa 3,3 V con Tip a GND, circa 0 V con Tip a 3V3_D attraverso
   il circuito 100 kΩ/base. Spegnere prima di collegarlo a D6.
3. Montare U1, C15/C16 e CV1. Alimentare U1 dalla 3V3_A della Daisy; tenere ADC
   scollegato durante le misure. Con Tip a GND attendersi circa 0 V; con Tip a
   3V3_D attendersi circa 0,819 V dopo il buffer, se 3V3_D misura 3,300 V.
   Se la rail differisce, valore atteso = tensione misurata × 33/133.
4. Collegare il primo ADC D16 solo dopo controllo, a USB scollegata. Non
   interpretare la percentuale CV attuale come calibrazione: la scala software
   non è ancora aggiornata.
5. Collegare il DAC, poi verificare via firmware l'indirizzo 0x60 e tensioni
   fisse su VA–VD. Questo richiede ancora l'aggiunta della diagnostica MCP4728.
6. Replicare e collaudare gli altri tre trigger/CV; completare la diagnostica
   delle letture e poi la generazione dei quattro canali.

La sorgente locale 3,3 V permette un primo controllo senza un altro alimentatore.
Non verifica tutto il range CV 0–10 V: quel collaudo richiederà successivamente
una sorgente nota con massa comune, secondo SCHEMI.md.

## Stato del software e passaggio al rack

Il firmware attuale può provare i controlli e il primo trigger/CV, ma genera
ancora sul DAC interno D23 e non comunica con MCP4728. Non è stato modificato
in questa riorganizzazione USB. Il passo software successivo è una diagnostica
che mantenga OLED/controlli e aggiunga letture dei quattro ingressi e valori
fissi sui quattro DAC, senza scrivere continuamente la EEPROM.

Dopo il collaudo USB, montare i gruppi alimentazione e OUT, verificarli separati
dalla Daisy e completare le prove descritte in [SCHEMI.md](SCHEMI.md). Controlli,
trigger, CV e collegamenti digitali del DAC rimangono quelli già collaudati.
