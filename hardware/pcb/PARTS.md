# Componenti e montaggio — D

La distinta completa è [output/bom.csv](output/bom.csv). `Reference` è la sigla
KiCad; `Circuit role` mantiene il nome funzionale usato dal generatore e dalle
note. Le tolleranze e le tensioni scritte nei valori fanno parte della scelta.

| Funzione | Scelta |
| --- | --- |
| Processore | 1× Daisy Seed 3; VIN dal 5 V locale, AGND e DGND collegati |
| ADC | 1× AD7606C-18BSTZ, LQFP64 |
| DAC | 1× DAC8568BPW, TSSOP16; gain 1, reset a metà scala |
| Protezione ingressi e uscite | 4× ADG5412FBRUZ, TSSOP16 |
| Amplificatori e filtri | 7× OPA4197ID, SOIC14 |
| Expander | 1× MCP23017-E/SO, SOIC28 |
| Logica | 2× SN74LVC08ADR, 2× SN74AHCT125DR, SN74HCS74DR, SN74LVC1G08DBVR |
| Supervisione | TPS3828-33DBVR, TPS3808G01DBVR, LM393BDR |
| Convertitore | RECOM R-78E5.0-1.0, SIP3, 5 V / 1 A |
| Alimentazione Eurorack | Wurth 61201021621, IDC10; pin 1 sul −12 V |
| Fusibili ripristinabili | Littelfuse 1206L075/24YR sul positivo; 1206L025/30YR sul negativo |
| Filtro ramo analogico | Murata BLM21PG601SN1D |
| Collegamento tra PCB | Samtec TSW-120-07-G-D + SSW-120-02-G-D, 2×20 |
| Encoder | 4× ALPS EC11E18244AU, albero piatto da 20 mm, click, 36 scatti / 18 impulsi |
| Pulsanti | 4× E-Switch TL1105DF160Q, attuatore da 13 mm |
| Display | Waveshare 0.96inch OLED Module (D), SSD1315, bianco, PCB 26×26 mm |
| Jack | 12× PJ398SM / Thonkiconn verticali |

Non sostituire DAC8568B con gradi A/C/D, AD7606C-18 con AD7606B, ADG5412F con
ADG5413F, oppure AHCT125 con un LVC125 alimentato a 5 V senza rivedere il circuito.

L'OLED ha sette pin, nell'ordine VCC/GND/DIN/CLK/CS/DC/RES. Configurare i ponticelli
del modulo per **I²C 0x3c**; DIN diventa SDA e CLK diventa SCL. CS è lasciato
aperto, DC è a massa e RES è controllato dalla Daisy. Rimuovere R1 del modulo
e montare R2 da 0 Ω per I²C 0x3c, secondo la wiki Waveshare. Non usare automaticamente
un breakout a quattro pin con piedinatura diversa.

I resistori dei filtri sono 0,1%; i condensatori dei filtri sono C0G 1%.
Le sedici resistenze serie dei jack sono Vishay **CRCW20101K00FKEFHP**,
1 kΩ, 2010, 1%, **1 W a 70°C**: limitano la corrente e
introducono una caduta dipendente dal carico. L'uscita nominale ±5 V è a vuoto.
Il condensatore ADC REFCAP è 10 µF / 25 V X7R, 1210: verificare la capacità
**effettiva** alla tensione di lavoro sul componente acquistato.
La potenza di 1 W richiede derating sopra 70°C; non elimina la necessità di
misurare la termica degli operazionali durante collisioni simultanee.
I codici e i datasheet selezionati sono ora proprietà dei simboli KiCad e
colonne della distinta. Molti passivi hanno ancora specifiche senza MPN:
la distinta non è una lista di acquisto completa.

## Accessori e stack nominale

- Due strip femmina singole da 20 pin, passo 2,54 mm, per la Daisy, per esempio Samtec SSW-120-02-G-S.
- Quattro distanziali M3 da 10 mm fra retro del frontale da 2 mm e lato componenti della PCB comandi, con viti e dadi adatti.
- Quattro distanziali M3 da circa 11 mm fra le PCB, da adattare all'altezza d'innesto effettiva della coppia Samtec.
- Connettore da sette pin per OLED, montato/rialzato in modo che vetro e corpo non tocchino il pannello o l'encoder; verificare con il modulo reale.
- Manopole adatte all'albero dell'EC11 scelto; cavo IDC Eurorack correttamente polarizzato.

Le PCB sono 96,2×110,5×1,6 mm; il pannello nominale è 101,2×128,5×2 mm.
Prevedere almeno **45 mm nominali** di profondità dietro il pannello, più il
raggio di curvatura del cavo. Questa è una previsione di montaggio: tolleranze,
vetro OLED, altezze reali dei connettori e accesso USB vanno provati su pezzi
fisici prima della foratura finale. Il convertitore è sul retro della principale
perché il suo corpo è alto 10,4 mm. I pin dello stack sono simmetrici e senza
chiave: marcare pin 1 e verso, senza ruotare una scheda di 180°.

Il DAC Adafruit MCP4728 e i breakout già funzionanti restano al prototipo;
non vanno cablati in parallelo ai convertitori della nuova PCB.

Riferimenti meccanici: [catalogo ALPS EC11E, disegno 2](https://tech.alpsalpine.com/cms.media/product_catalog_ec_01_ec11e_en_611f078659.pdf) e [catalogo E-Switch TL1105, opzione D da 13 mm](https://configured-product-images.s3.amazonaws.com/Datasheets/TL1105.pdf).
