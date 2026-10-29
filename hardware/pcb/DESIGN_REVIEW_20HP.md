# Adolfo 20 HP — revisione completa del progetto

**Data:** 28 ottobre 2026. **Branch:** `pcb/rev-b-20hp-eurorack`, base Git `e35e8da` con modifiche locali già presenti.
**Oggetto:** revisione D, 301 componenti, due PCB, schemi gerarchici KiCad 10, generatori e protocolli host.
**Aggiornamento meccanico, 29 ottobre 2026:** OLED e finestra centrati a X = 50,6 mm; intestazione e sottotitolo riallineati. Aggiornati connettore J14, piste del frontale, BOM, viste e DXF. Ripetuti ERC/DRC, audit nativo e validazione; le analisi elettriche e le simulazioni restano quelle del 28 ottobre.
**Verdetto:** i controlli CAD passano; **il progetto non è pronto per il rilascio hardware**. Tre problemi richiedono ancora una correzione di progetto. Non sono semplicemente prove al banco mancanti.

## Problemi bloccanti

| Priorità | Problema e conseguenza | Evidenza | Criterio per chiuderlo |
| --- | --- | --- | --- |
| Critica | U2 VDRIVE è alimentato dalla Daisy anche con AVCC spento: USB può applicare 3,3 V contro il limite AVCC + 0,3 V. Possibile violazione dei massimi assoluti. | AD7606C-18 Rev B, p14 tabella 6; Seed3 v2.1 p10; collegamenti U1.38/U2.23 e U2.1/37/38/48. | Circuito di alimentazione e isolamento dei segnali che rispetti i limiti in tutte le sequenze previste, inclusi spegnimento e USB. |
| Alta | Regolatore e monitor 5 V non hanno un intervallo garantito comune: un regolatore conforme può mantenere reset attivo; un monitor al limite opposto può consentire AVCC insufficiente. | RECOM ±5%; TPS3808G01, accuratezza/isteresi; calcolo dei corner: intervento 4,712…4,928 V, rilascio fino a 5,075 V. | Regolazione e supervisione dimensionate insieme con tolleranze, ripple, temperatura, cadute e transitori. |
| Alta | Il backend dei nuovi convertitori manca. I target dichiarati non sono sostenibili dal DMA SPI standard esaminato. | A 25 MHz: ADC 55,296% + DAC 49,152% = **104,448%**, prima dell'overhead. Clock SPI standard esaminato: massimo SCK 12,5 MHz. | Backend con clock e risorse DMA espliciti, schedule completo e misure di timing alle frequenze dichiarate. |

**Non collegare USB con il carrier spento prima di risolvere il primo problema.** Tenere permit basso non protegge i pin di alimentazione dell'ADC. Anche la sola prescrizione di una sequenza di accensione non risolve il circuito.

Questi tre blocchi sono registrati in `design.py`, esportati in `design.json` e riportati da `validate.py`. Il risultato distingue `cad_status: PASS` da `release_status: BLOCKED`.

## Correzioni applicate

Il confronto è con lo stato locale iniziale conservato in `build/review-baseline-20261028/`, non con il solo HEAD: le modifiche preesistenti non vengono attribuite a questa revisione.

Il delta automatico della principale riporta 40 componenti con campi modificati nello schema e 17 nella PCB; non sono 40 errori distinti. I confronti sono conservati in [schematic-delta.json](analysis/schematic-delta.json) e [pcb-delta.json](analysis/pcb-delta.json). Numero di componenti e piedinatura dei convertitori restano invariati; le correzioni geometriche e i normali del frontale sono riportati qui sotto.

| Elemento | Prima | Dopo |
| --- | --- | --- |
| IN1–4 senza patch | Normali aperti, ingresso del filtro privo di ritorno DC | TN di J1/J4/J7/J10 a GND; CTRL e OUT restano aperti |
| Latch U16 | SN74HC74 su reset condiviso open-drain | **SN74HCS74DR**, ingressi Schmitt, stesso package e pinout |
| RI1–8 e RO1–8 | 1 kΩ / 0,5 W senza MPN preciso | **CRCW20101K00FKEFHP**, 1 kΩ, 1%, 2010, 1 W a 70°C |
| Tre vie GND | Fori dentro C11.2 e U2.32 | Due vie riposizionate, una eliminata, collegamenti conservati e riscontro nativo senza intersezioni |
| Socket SSW | Corpo generico lungo 50,8 mm | Ingombro massimo **51,56 × 4,95 mm**, con courtyard aggiuntivo |
| IDC Wurth | Fori da 1,00 mm | Dieci fori da **1,10 mm**, pad e piste conservati |
| Tracciabilità | MPN e datasheet non esportati come campi | Proprietà dei simboli, campi PCB e colonne BOM; confronto nel validatore |
| Documentazione | Possibile lettura di un PASS CAD come disponibilità del modulo | Blocchi espliciti in README, architettura, checklist, viewer e rapporto |

La riparazione delle vie è descritta in [via_repair.json](analysis/spice_verification/via_repair.json). Il generatore dei collegamenti GND ora evita anche pad SMD della stessa rete sul lato opposto. L'audit finale controlla ogni foro di via contro tutti i pad SMD, non soltanto le due segnalazioni dell'analizzatore.

## Portata e basi di verifica

- **Coerenza completa:** tutti i 301 riferimenti, i pin collegati e non collegati, le netlist compilate e i pad PCB sono confrontati dal validatore. Anche lato, posizione, valore, MPN, produttore e datasheet entrano nel controllo.
- **Riscontro con il produttore:** i 25 IC/moduli sono stati esaminati per pinout, alimentazioni e uso previsto, con le fonti indicate sotto. Questo non equivale a una misura delle loro prestazioni nel circuito.
- **Passivi:** topologie e valori sono controllati nel contesto; molti componenti non hanno ancora un MPN acquistabile. Capacità effettiva, derating, TCR e varianti acquistate non sono tutti qualificati.
- **Diodi:** orientamento interno e marcatura del footprint controllati; SS14 è coerente con la famiglia SMA 1 A / 40 V del produttore. Il costruttore/codice completo di D1/D2 e la scelta acquistata di BAT54WS restano da fissare prima dell'assemblaggio.
- **Meccanica:** disegni e pad confrontati; nessun montaggio fisico. Piccole differenze nelle asole encoder e tolleranze dello stack restano da provare.
- **Simulazioni:** passivi ideali e modelli di operazionale ideali/a polo dominante; non macromodelli completi dei componenti reali.

Le evidenze strutturate sono in [deep_review.json](analysis/deep_review.json), con passaggi separati per le due PCB. Il gate ha accettato 10 rilievi: 7 con evidenza completa secondo il suo controllo e 3 parziali; nessuno in quarantena. Il gate controlla ancore e citazioni, non certifica il circuito.

L'elenco [component-review.csv](analysis/component-review.csv) copre ogni componente e distingue coerenza CAD, confronto con il produttore e limiti rimasti. I PDF disponibili sono in `datasheets/`; URL e impronte dei documenti sono in [references.json](references.json) e nel manifest locale.

## Inventario

| Categoria fisica | Quantità |
| --- | ---: |
| Resistori | 146 |
| Condensatori | 94 |
| IC e moduli di conversione/elaborazione/alimentazione | 25 |
| Jack, connettori e modulo display | 16 |
| Encoder | 4 |
| Pulsanti | 4 |
| Diodi | 3 |
| Fusibili ripristinabili | 2 |
| Ferrite | 1 |
| Test point | 6 |
| **Totale** | **301** |

Principale: 279 componenti più quattro fori di montaggio. Frontale: 22 componenti più quattro fori. Le unità dei simboli multipli non sono componenti aggiuntivi: la lista dell'analizzatore contiene anche le singole sezioni.

Sono popolati MPN per 40 componenti della principale, corrispondenti a 14 codici distinti. Questo migliora la tracciabilità degli IC e dei resistori di protezione, ma **non completa la distinta di acquisto**. I riferimenti dei test point e i fori non richiedono la stessa qualifica di un componente acquistato.

## Albero di alimentazione e sequenziamento

```text
IDC10 +12 V -> PTC positivo -> SS14 -> +12VA -> RECOM -> +5D -> Daisy -> +3V3
                                      |                  |
                                      |                  +-> ferrite -> +5A -> ADC/DAC/buffer
                                      +-> OPA4197 e ADG5412F
IDC10 -12 V -> PTC negativo -> SS14 -> -12VA -> OPA4197 e ADG5412F
GND comune -> piano In1.Cu, ritorni e collegamento frontale
```

IDC pin 1/2 = −12 V, 3…8 = GND, 9/10 = +12 V. Il verso dei due diodi serie è coerente con entrambe le polarità. La protezione riguarda queste condizioni dichiarate; il limite ±55 V del solo switch non è un limite del modulo completo.

Il budget preliminare di 0,7 A sul 5 V vale 3,5 W erogati. Usando soltanto gli estremi di efficienza 85…93% come stima, il convertitore dissipa circa 0,26…0,62 W: occorrono corrente reale, derating e temperatura nel case. Non è una previsione garantita per ogni punto operativo. Fusibili e spunto richiedono la prova a caldo.

Il divisore del TPS3808 produce nominalmente `0,405 × (1 + 109k/10k) = 4,8195 V`. I corner includono accuratezza ±2%, isteresi massima 3%, resistori 0,1% e corrente SENSE ±25 nA. Non includono TCR dei passivi, cadute PCB o transitori: questi possono ridurre ulteriormente il margine. [Calcolo riproducibile](analysis/power_safety/check_current.py).

I monitor ±12 V usano un riferimento pari a metà del 3,3 V. A 3,300 V i corner calcolati danno circa +10,356…10,468 V e −10,515…−10,319 V. A 2,86 V, limite basso del monitor TPS3828 considerato, scendono verso +8,97…9,08 V e −9,12…−8,94 V. I valori nominali ±10,4 V non sono soglie indipendenti dalla rail.

Riferimenti: [RECOM, pp1–4](https://recom-power.com/pdf/Innoline/R-78E-1.0.pdf), [TPS3808, p6](https://www.ti.com/lit/ds/symlink/tps3808.pdf), [TPS3828, p6](https://www.ti.com/lit/ds/symlink/tps3828.pdf), [LM393B, pp3–7](https://www.ti.com/lit/ds/symlink/lm393b.pdf).

## Riscontro degli IC

| Riferimenti | Parte e verifica | Esito e limite |
| --- | --- | --- |
| U1 | Seed3 v2.1 pp5–10: GPIO, VIN39, GND20/40, 3V3D38 | Mappa coerente; USB non rende sicura l'alimentazione del carrier |
| U2 | AD7606C-18 Rev B pp15–17 tabella 9, p42 tabella 23: 64 pin, otto coppie analogiche, seriale/software | Collegamenti coerenti; sequenziamento bloccante e configurazione firmware ancora assente |
| U3 | DAC8568 Rev F pp3–4 e pp32–36: PW16, grado B, reset e protocollo | Pinout coerente; mantenere il grado B e attivare il riferimento via software |
| U4 | MCP23017 DS20001952C p10: SOIC28 e indirizzo 0x20 | Coerente; GPA7/GPB7 usati solo come uscite, K4 su GPB0 |
| U5/U6 | [SN74LVC08A SCAS283W](https://www.ti.com/lit/ds/symlink/sn74lvc08a.pdf) pp4,6–7, AND a quattro sezioni | Ingressi REQ/SAFE_PERMIT, uscite SW_ON e alimentazioni coerenti; tempi e rampe da provare |
| U7/U8/U14/U15 | ADG5412F Rev C p13 e sezioni fault/protezione | S verso jack, D verso circuito, control e rail coerenti; non confondere con ADG5413F |
| U9/U10/U11/U21–U24 | OPA4197 Rev C pp3–9: SOIC14, sette package | Pinout e follower/reti di feedback coerenti; stabilità e distorsione non misurate |
| U12/U13 | AHCT125 Rev R pp2,4–6 | TTL in a 3,3 V, alimentazione 5 V e pin A/Y/OE coerenti; skew e timing da misurare |
| U16 | HCS74 Rev D pp3–6 | Sostituzione Schmitt applicata, pinout conservato; rispettare recovery/reset prima del permit |
| U17 | TPS3828 Rev O pp4–7 | RESET1, GND2, MR3, WDI4, VDD5 coerenti; WDI ha pull-down |
| U18 | TPS3808 Rev N pp4–7 | Pinout coerente; budget di soglia non chiuso |
| U19 | LM393B Rev AH pp3–7 | Polarità dei due confronti coerente; riferimento ratiometrico |
| U20 | LVC1G08 Rev AA: A1/B2/GND3/Y4/VCC5 | Consenso comune coerente |
| U25 | R-78E5.0-1.0, pp1–4 | Pinout e ingresso nominale coerenti; precisione e avvio non chiudono i requisiti di sistema |

Le uscite FF dei quattro ADG possono condividere la rete di fault: la [FAQ ufficiale ADI, domanda 1](https://ez.analog.com/switches_multiplexers/a/documents/do26787/faq-adg54xxf) descrive questa combinazione. Il pull-up è verso 3,3 V: non si tratta di un'uscita push-pull a 12 V collegata alla logica.

Fonti digitali/analogiche: [ADC](https://www.analog.com/media/en/technical-documentation/data-sheets/ad7606c-18.pdf), [DAC](https://www.ti.com/lit/ds/symlink/dac8568.pdf), [MCP23017](https://ww1.microchip.com/downloads/en/DeviceDoc/20001952C.pdf), [OPA4197](https://www.ti.com/lit/ds/symlink/opa4197.pdf), [AHCT125](https://www.ti.com/lit/ds/symlink/sn74ahct125.pdf), [HCS74](https://www.ti.com/lit/ds/symlink/sn74hcs74.pdf), [Seed3](https://daisy.nyc3.cdn.digitaloceanspaces.com/products/seed3/Daisy_Seed3_datasheet.pdf).

## Analogica, protezioni e simulazioni

Gli otto amplificatori differenziali realizzano nominalmente `4 × VDAC − 5 V`: il codice 32768 produce zero ideale. I rapporti resistivi, l'offset e il carico richiedono calibrazione; il numero di bit del convertitore non dimostra precisione equivalente del modulo.

La resistenza di uscita di 1 kΩ, più RON, causa già circa 1% di attenuazione con 100 kΩ. Con carichi diversi cambia l'errore: una calibrazione a vuoto non garantisce V/oct sotto carico. I CTRL aperti hanno inoltre il carico/bias dell'ADC, non un pull-down ideale a zero.

Per una collisione ±5 V contro la rail esterna opposta di 12 V, Rmin = 990 Ω dà 17,17 mA e 0,292 W. Un differenziale di guasto di 24 V porta a 0,582 W: la scelta da 1 W migliora il margine. Sopra 70°C occorre derating. Non rende automaticamente sicure tutte le collisioni simultanee degli operazionali. [Vishay doc20043, pp1–3](https://www.vishay.com/docs/20043/crcwhpe3.pdf).

È stato usato **ngspice-46**, nella DLL installata con KiCad, con adattatore locale e self-check del partitore 3,3 V → 1,65 V. Non è stato installato un nuovo simulatore.

| Verifica | Risultato | Limite |
| --- | --- | --- |
| Orchestrazione `simulate_subcircuits.py`, con parassiti PCB estratti | 59 pass, 4 skip, 0 fail | Reti rilevate automaticamente; copertura non equivalente ai filtri completi |
| Otto filtri completi con operazionali ideali | Pass | RON assunto 10 Ω, passivi ideali |
| Otto filtri con polo dominante a GBW 10 MHz | Pass | Sensibilità alla banda, non macromodello completo OPA |
| Otto stadi differenziali | Pass, da −5 a +5 V nei punti ideali provati | Non include saturazione, rumore o carico reale |
| Corner dei filtri | 256 combinazioni per tipo di percorso, senza picco oltre il limite del controllo | R 0,1%, C 1%; non comprende temperatura o invecchiamento |

Tre skip automatici sono testbench PDN con misura del minimo non riuscita; il quarto usa una corrente non salvata e una classificazione errata dell'inrush RECOM. I simboli OPA multisezione non vengono ricostruiti correttamente dal rilevatore: per questo sono state aggiunte le 24 simulazioni mirate.

Risultati: [detected.json](analysis/spice_verification/detected.json), [full_paths.json](analysis/spice_verification/full_paths.json), [sampling_images.json](analysis/spice_verification/sampling_images.json).

### Limite della risposta audio

| Grandezza simulata | Valore |
| --- | ---: |
| IN a 20 kHz | −3,403 dB |
| OUT a 20 kHz | −2,988 dB |
| OUT a 28 kHz | −11,557 dB |
| Prima immagine di un tono 20 kHz, DAC 48 kHz, includendo ZOH | **−11,49 dBc** |
| Reiezione relativa esterna di 76 kHz che aliasa a 20 kHz con ADC 96 kHz | **43,54 dB** |

La sola frequenza di taglio a 20 kHz non dimostra una buona ricostruzione audio a 48 kHz. Servono requisiti di banda, immagini e aliasing, poi una scelta coerente fra interpolazione/sovracampionamento, filtri e traffico SPI. La decimazione digitale non elimina un alias già creato nel campionamento.

## Clock, protocolli e firmware

I test C++ di `platform` passano per unpacking dei frame ADC a 18 bit, segno, framing DAC a 32 bit, valori limite e policy di abilitazione. Il test uscite del prototipo passa. Questo non implementa il backend della nuova carrier.

I pin scelti corrispondono alle periferiche SPI1/SPI3 esaminate. Nel [driver libDaisy](https://raw.githubusercontent.com/daisyaudio/libDaisy/master/src/per/spi.cpp) esaminato, gli stream DMA sono condivisi e una variabile globale serializza i trasferimenti. La [configurazione clock](https://raw.githubusercontent.com/daisyaudio/libDaisy/master/src/sys/system.cpp) esaminata usa PLL2P = 25 MHz; il prescaler minimo /2 dà 12,5 MHz SCK. Il backend deve fissare anche la versione della libreria e ricontrollare queste condizioni.

Un frame ADC di 144 bit a 12,5 MHz richiede 11,52 µs, contro un periodo di 10,417 µs. Due periferiche distinte non assicurano due DMA simultanei. Un futuro kernel a 100 MHz con ADC a 50 MHz e DAC a 25 MHz ridurrebbe il solo payload serializzato al 76,8%, ma non dimostra uno schedule: i burst DAC vanno intercalati con le letture ADC e occorrono tutti gli intervalli del protocollo.

L'avvio iniziale dell'ADC richiede oltre 2 s complessivi fra power-up e setup, secondo Rev B p10 tabella 3 nota 3. Devono precedere l'abilitazione delle uscite: configurazione, riferimento assestato, valori zero caricati, monitor stabili e calibrazione valida.

Il firmware in `Adolfo/` continua a pilotare il prototipo MCP4728. Non è stato retargettizzato alla nuova PCB né presentato come compatibile. Il test UI completo e il build ARM non sono stati eseguiti in questa revisione; le dipendenze libDaisy/DaisySP non sono parte del checkout esaminato.

## Layout, ritorni ed EMC

| Dato | Principale | Frontale |
| --- | ---: | ---: |
| Dimensioni | 96,2 × 110,5 mm | 96,2 × 110,5 mm |
| Strati rame | 4 | 2 |
| Footprint, inclusi fori | 283 | 26 |
| Segmenti di pista | 4105 | 320 |
| Vie | 425 | 13 |
| Lunghezza complessiva piste | 9035,70 mm | 2248,51 mm |
| Violazioni ERC / DRC native | 0 / 0 | 0 / 0 |
| Connessioni mancanti / parità schema | 0 / 0 | 0 / 0 |
| Fori via dentro pad SMD | 0 | 0 |

La principale ha un piano GND In1.Cu riempito, con circa 92,8% di area riempita e una sola isola GND nel grafo. Nessuna pista di segnale usa quel piano. Distanze native 0,15 mm, bordo rame 0,30 mm, via 0,60/0,30 mm; non è stato fissato uno stackup produttivo con impedenze garantite.

Gli allarmi GP-001 sono in gran parte falsi positivi: senza stackup esplicito, il codice dell'analizzatore confronta F.Cu e B.Cu e non usa il piano interno reale. Il [controllo nativo aggiuntivo](analysis/check_layout.py) campiona le piste ogni ≤2 mm sul riempimento In1.Cu. Entro 0,5 mm trova riferimento per il 100% dei campioni ADC_SCK_TERM/CONVST e DAC_SCK/linee DAC a 5 V, e per il 96,3% di ADC_MISO. Le zone vuote presso fori e le porzioni residue richiedono interpretazione; questo non è un modello di integrità del segnale.

Restano da qualificare: parallelismo SCK/MISO, transizioni di strato, ritorni su B.Cu/In2.Cu e margini alle frequenze effettive. La regola 3H dell'analizzatore assume uno spessore dielettrico non definito dal produttore; il numero non è una misura del crosstalk reale.

Sono presenti condensatori locali per alimentazioni e riferimenti; il validatore controlla ogni vincolo di vicinanza al pin, fino a 6 mm per i componenti critici ADC. I controlli automatici basati sul centro del package non sostituiscono il percorso reale della corrente: rumore di alimentazione, loop dei bypass e risposta transitoria restano prove richieste.

Non esistono antenna o sensori touch nel progetto; i TP sono test point. La continuità delle masse non è una certificazione EMC. Il frontale ha ritorni GND anche sui numerosi pin passanti; la segnalazione di assenza di vie GND non considera questi collegamenti come stitching dedicato.

## Termica

`analyze_thermal.py` è stato eseguito a 50°C su entrambe le PCB. La stima di **829°C su U25 è scartata**: il modulo switching è trattato come un regolatore lineare con un'uscita/efficienza errata. Anche le segnalazioni di prossimità derivate da tale temperatura non sono stime utilizzabili. Il frontale non ha dissipazioni quantificabili dal modello e viene dichiarato skipped.

Per i sette OPA4197, 28 amplificatori a circa 1 mA tipico e 24 V complessivi danno circa 0,672 W complessivi a riposo; il carico può dominare. Un corner di quattro collisioni simultanee su un package dà circa 0,696 W inclusa la corrente a riposo massima assunta; con θJA = 86,4°C/W l'incremento è circa 60°C. È una stima con condizioni termiche di riferimento, non una misura sulla PCB. Non si può dichiarare un corto continuo sicuro per tutti i canali e tutte le temperature.

Vanno misurati regolatore, diodi, fusibili, resistori e OPA nel case, con carichi e guasti simultanei. Gli IC scelti non hanno un exposed pad centrale che richieda una matrice dedicata di vie termiche; non va applicata a questi SOIC/TSSOP/LQFP una regola QFN generica.

## Meccanica, produzione e distinta

Il confronto dei 40 pin dello stack è fisico, per numero e coordinate, e passa su tutti i pin. Il socket montato sul retro ha numerazione specchiata: sostituirlo con l'impronta dell'header rende errato il mating.

Il [disegno Samtec SSW, p1](https://suddendocs.samtec.com/prints/ssw-1xx-xx-xxx-x-xx-xxx-xx-mkt.pdf) dà 51,31 ±0,25 mm di lunghezza corpo; il nuovo ingombro include il massimo. L'interasse nominale delle PCB è circa 11 mm, da controllare all'innesto reale. I connettori non sono polarizzati: pin 1 e verso devono restare riconoscibili durante il montaggio.

Per l'IDC, il disegno Wurth 61201021621 indica Ø1,10 mm; con pad da 1,70 mm resta un anello di 0,30 mm. L'orientamento del cavo reale deve comunque essere controllato.

Il [catalogo ALPS EC11E, pp1–2](https://tech.alpsalpine.com/cms.media/product_catalog_ec_01_ec11e_en_611f078659.pdf) corrisponde ai cinque contatti. Le asole del supporto dell'impronta importata sono leggermente diverse dal disegno: serve il campione fisico. Il [TL1105, pp1–2](https://configured-product-images.s3.amazonaws.com/Datasheets/TL1105.pdf) conferma reticolo 6,5 × 4,5 mm e attuatore D da 13 mm: la sporgenza nominale sullo stack dichiarato è solo 1 mm.

La [wiki Waveshare](https://www.waveshare.com/wiki/0.96inch_OLED_Module) consente CS aperto in I²C. Rimuovere R1 e montare R2 = 0 Ω per 0x3c; DC è già GND. La finestra offre poco margine rispetto all'area visualizzata e richiede una dima. Verificare anche il parallelo dei pull-up da 2,2 kΩ con quelli del modulo e il tempo di salita del bus.

Mancano fiduciali per l'assemblaggio automatico; predisporli sul pannello di produzione o sulla PCB prima di quel processo. La copertura ICT automatica è limitata: i sei TP servono soprattutto alimentazioni/riferimento, mentre jack, stack e pin passanti offrono altri punti accessibili. Occorre ancora un piano di collaudo della scheda assemblata.

Il pannello è 101,2 × 128,5 × 2 mm. Profondità, accesso USB, encoder, display, distanziali, dadi e raggio del cavo richiedono il montaggio di prova. La dima nominale non è stata dichiarata pronta alla lavorazione definitiva.

### Lifecycle

Dopo autorizzazione esplicita dell'utente è stato eseguito `lifecycle_audit.py --only lcsc` sui 14 MPN presenti. Esito: **14 unknown**. Il servizio usato non espone uno stato lifecycle e l'analizzatore lo dichiara: non significa che le parti siano attive né obsolete. Il limite resta aperto finché non è disponibile una fonte che restituisca il dato. Nessuna verifica di stock o prezzo è stata presentata come eseguita.

## Falsi positivi e limiti degli analizzatori

| Segnalazione | Triage |
| --- | --- |
| PP-001 sulle alimentazioni negative | Il rilevatore non riconosce correttamente la rail negativa; netlist e pad mostrano il percorso IDC → fusibile → diodo → carichi. |
| VM-001 su SAFE_CLEAR_N | Bus di fault open-drain/pseudo open-drain con pull-up a 3,3 V, non un pilotaggio push-pull a 12 V. |
| RS-001 su rail dopo fusibile | Percorso passivo presente; assenza di una sorgente riconosciuta dal rilevatore non equivale a rail interrotta. |
| GP-001 / CP-002 massivi | Modello degli strati incompleto; confrontato con il piano interno nativo. Non si assume che ogni rischio EMC sia risolto. |
| PM-002 sui fori M3 | Il courtyard comprende il fastener e può oltrepassare il bordo senza che il foro lo faccia. Restano circa 1,4 mm di materiale sul bordo superiore e 1,9 mm su quello inferiore; provare serraggio e distanziali. |
| PM-002 sul display | Pad del connettore vicino al bordo; il corpo del modulo si estende verso l'interno. Richiede controllo dello stack, non uno spostamento automatico. |
| TS-001/TS-004 e prossimità U25 | Modello lineare errato per il convertitore switching; temperatura automatica scartata. |
| SS-001 | **Rilievo reale:** la distinta non ha MPN completi. |
| FD-001 / TE-001 | Limiti reali per assemblaggio automatico e ICT, da affrontare con il processo produttivo scelto. |

## Controlli eseguiti e omissioni esplicite

| Controllo | Stato |
| --- | --- |
| `analyze_schematic.py`, entrambe le radici | Eseguito, gerarchia inclusa |
| `analyze_pcb.py --full --proximity`, entrambe le PCB | Eseguito sui file finali |
| `cross_analysis.py` | Eseguito: zero rilievi sulla principale; avviso stitching sul frontale |
| `analyze_emc.py --market eu` | Eseguito; risultati triagiati, nessuna previsione di conformità |
| `analyze_thermal.py --ambient 50` | Eseguito; modello U25 scartato, pannello senza potenze quantificabili |
| `extract_parasitics.py` e `simulate_subcircuits.py` | Eseguiti, più simulazioni complete mirate |
| ERC, DRC, refill, parità e SVG nativi | Eseguiti: tutti a zero segnalazioni |
| Audit nativo e `validate.py` | **2.027 controlli superati**, compresi centratura OLED, pad, campi e assenza di via nei pad SMD |
| Generazione e preparazione da sorgenti | Provate in `build/rebuild-review-check/`: 133 vie GND iniziali, nessun foro dentro pad SMD, tutti i 40 pin dello stack coincidenti. Non ripetuto lo sbroglio completo da zero; le PCB consegnate sono quelle controllate sopra. |
| Test C++ porte, converter, uscite prototipo | Superati con C++14, warning come errori |
| `deep_review_gate.py` | Eseguito per entrambe le schede; 10 rilievi accettati, 3 con evidenza parziale |
| Lifecycle | Eseguito su 14 MPN; risultato non determinato dalla fonte |
| Delta precedente | Confronto con snapshot locale iniziale e analisi iniziale della principale; nessuna precedente revisione narrativa trovata |
| `analyze_gerbers.py` | Non applicabile: nessun Gerber/Excellon di fabbricazione presente. `drill.svg` non è un file Excellon. |
| Estrazione datasheet strutturata | Non eseguita; confronto manuale con PDF/pagine del produttore. PDF ADC/ADG consultati via web, download locale non riuscito. |
| Pinout specifico dei tre diodi acquistati | Parziale: famiglie/marcature coerenti, costruttori e codici completi da fissare |
| Build ARM, test UI completo | Non eseguiti; dipendenze esterne non comprese nel checkout |
| Prove elettriche, termiche, EMC e meccaniche | Non eseguite; richiedono campione, strumenti e condizioni definite |

Le impronte dei file verificati sono in [native-checks.json](output/native-checks.json). Le analisi complete rigenerabili sono conservate sotto `analysis/main/` e `analysis/panel/`; gli script locali e i risultati mirati permettono di ripetere i calcoli. Non è stato creato un ordine né un pacchetto di produzione.

## Condizioni per il rilascio

1. Chiudere alimentazione/sequenziamento e budget del monitor con nuovi valori/componenti documentati e limiti garantiti.
2. Fissare requisiti audio/CV, algoritmo di ricostruzione/decimazione e budget SPI/DMA, quindi implementare il backend.
3. Completare MPN, lifecycle, stackup e processo di assemblaggio; aggiornare le verifiche sui file risultanti.
4. Eseguire la [checklist di qualifica](RELEASE_CHECKLIST.md) con misure, inclusi reset, rail mancanti, corti/collisioni e temperature nel case.

Il risultato attuale è una revisione CAD corretta nei punti indicati e controllabile, con problemi aperti resi espliciti. Non è una dichiarazione di perfezione, sicurezza in ogni guasto o prontezza alla produzione.
