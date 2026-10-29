# Revisione meccanica e comandi — 28 ottobre 2026

Sola lettura dei generatori, delle impronte salvate e dei documenti produttore.
Non sono stati modificati file produttivi.

## Correzioni piccole raccomandate

- **Socket Samtec SSW-120-02-G-D:** il disegno ufficiale CM, p1 fig1, indica corpo lungo `20×2,54 +0,51 ±0,25 =51,31±0,25 mm`, largo 4,95 mm e alto 8,51 mm. Il generatore applica 50,8 mm sia all'header sia al socket: il corpo socket è sottostimato di 0,51 mm nominali, 0,76 mm al massimo. Il courtyard corrente è lungo 51,6 mm e lascia appena 0,02 mm per lato rispetto al corpo massimo. Separare l'ingombro socket da quello header, senza cambiare pad o numerazione.
- **IDC Wurth 61201021621:** documento produttore p1 indica fori raccomandati Ø1,10 mm; l'impronta usa Ø1,00 mm con pad Ø1,70 mm. Il pin nominale 0,64 mm quadro entra, ma il foro più piccolo riduce il margine. Ø1,10 lascia ancora anello radiale 0,30 mm e conserva tutti i pad e le piste. L'involucro 20,36×8,85 mm e il passo 2,54 mm corrispondono all'impronta generica.

## OLED Waveshare D

La wiki ufficiale ammette esplicitamente **CS non collegato in I2C**. J14.5 aperto non è un errore. I sette pin VCC/GND/DIN/CLK/CS/DC/RES corrispondono al carrier.

Per I2C serve rimuovere R1, che di fabbrica seleziona SPI. Per indirizzo 0x3c serve R2 da 0 Ω e DC basso; il carrier collega già DC a GND. Il modulo D usa SSD1315, PCB 26×26 mm, area visualizzata 21,74×11,18 mm. La finestra corrente 22,2×11,6 mm lascia nominalmente 0,23/0,21 mm per lato: l'allineamento reale resta da misurare.

Lo schema ufficiale Rev1.1 conferma i sette pin e mostra il circuito di adattamento dei livelli, il regolatore e pull-up da 10 kΩ. I pull-up del carrier da 2,2 kΩ devono essere valutati con quelli del modulo e con la capacità reale del bus; questa revisione non dimostra i tempi di salita a 400 kHz.

## Encoder ALPS EC11E18244AU

Il catalogo ufficiale aggiornato 2510 associa il codice al disegno 2: albero piatto 20 mm, 36 scatti/18 impulsi, switch con corsa 0,5 mm. Il centro albero dell'impronta è correttamente ricentrato dal generatore con offset (7,5;2,5) mm.

I tre contatti A/C/B hanno passo 2,5 mm e si trovano a 7,5 mm dall'asse; i contatti switch sono separati di 5 mm e a 7 mm dall'asse opposto. Ruotando di 90° il disegno del produttore, i cinque contatti coincidono con le coordinate dell'impronta.

I fori dei supporti richiedono ancora la prova fisica: il catalogo indica asole 2,6×1,5 mm, l'impronta importata usa 2,8×1,5 mm. Il catalogo quota 12,5 mm fra i bordi esterni delle asole; l'impronta usa centri distanti 11,2 mm, cioè ingombro esterno 12,7 mm. Non confondere questo confronto nominale con una qualifica di inserzione e ritenzione. L'albero sporge nominalmente 8 mm oltre un pannello da 2 mm posto a 10 mm dalla PCB; la corsa del click riduce la sporgenza di 0,5 mm.

## Pulsanti E-Switch TL1105DF160Q

Il catalogo p1 identifica attuatore D da 13 mm; p2 mostra reticolo 6,5×4,5 mm e coppie di terminali collegate lungo il lato da 6,5 mm. L'impronta usa le medesime coordinate e connessioni, dopo rotazione del riferimento del disegno. Il generatore ricentra correttamente con offset (3,25;2,25) mm.

Con PCB a 10 mm dal retro pannello e pannello da 2 mm, l'attuatore da 13 mm sporge nominalmente 1 mm. La corsa tipica è 0,25 mm; le tolleranze dello stack e l'accessibilità del tasto vanno provate. Il nome originario dell'impronta da 9,5 mm non costituisce una prova dell'altezza reale del componente acquistato.

## Mating Samtec e IDC

TSW e SSW sono famiglie accoppiabili secondo le pagine ufficiali. Entrambi sono 2×20 a passo 2,54 mm. TSW-07 ha post da 5,84 mm; SSW-02 ha coda da 4,93 mm. Il corpo SSW alto 8,51 mm sommato al corpo TSW da 2,54 mm dà circa 11,05 mm di interasse fra superfici PCB a innesto completo: la prescrizione di circa 11 mm è nominalmente ragionevole e richiede controllo del campione.

La numerazione specchiata del socket montato sul retro produce identiche posizioni fisiche pad per pad, come controllato dal progetto. Le strip non sono polarizzate: occorre riconoscere pin 1 e impedire montaggio ruotato di 180°. Non è stata qui validata l'accessibilità delle marcature nella scheda completamente montata.

IDC pin 1/2 sul -12 V, 3-8 GND e 9/10 sul +12 V è coerente con la scelta Eurorack dichiarata. La chiave meccanica non dimostra il corretto orientamento del cavo reale o del bus nel case.

## Codice firmware/policy

Letti `platform/PortConfig.h`, relativo test, `Adolfo/main.cpp`, `EnvelopeBank.h` e test uscite. Non è emerso un ulteriore errore grave nelle transizioni policy: `Set` invalida la readiness, `Disarm` azzera permit/readiness e `Arm` fallito disarma. La conversione tensione/codice rifiuta valori non finiti.

Il prototipo azzera il DAC all'avvio prima di avviare il timer; interrompe il timer e tenta lo zero su errore I2C. Un DAC irraggiungibile può mantenere l'ultimo valore: il codice e la documentazione lo dichiarano già. Questo firmware resta distinto dal backend ADC/DAC mancante della nuova carrier. Nessun nuovo test host è stato eseguito in questo sottogruppo.

## Fonti primarie e materiali locali

- [Waveshare wiki](https://www.waveshare.com/wiki/0.96inch_OLED_Module), sezioni Pin Function / Hardware Configuration. Salvata come `datasheets/waveshare_oled_page.html`.
- [Waveshare schema Rev1.1](https://files.waveshare.com/upload/8/8f/0.96inch_OLED_Module_Schematic.pdf), `datasheets/waveshare_oled_schematic.pdf`.
- [ALPS catalogo EC11E](https://tech.alpsalpine.com/cms.media/product_catalog_ec_01_ec11e_en_611f078659.pdf), pp1-2, `datasheets/alps_ec11e.pdf`. Render e dettagli in questa cartella.
- [E-Switch TL1105](https://configured-product-images.s3.amazonaws.com/Datasheets/TL1105.pdf), catalogo produttore pp1-2, `datasheets/tl1105.pdf`.
- [Samtec SSW drawing CM](https://suddendocs.samtec.com/prints/ssw-1xx-xx-xxx-x-xx-xxx-xx-mkt.pdf), p1, `datasheets/samtec_ssw.pdf`.
- [Samtec TSW drawing DS](https://suddendocs.samtec.com/prints/tsw-xxx-xx-xxx-x-xx-xxx-mkt.pdf), pp1-2/6, `datasheets/samtec_tsw.pdf`.
- [Wurth disegno originale](https://www.we-online.com/components/products/datasheet/61201021621.pdf), p1. Accesso diretto 403/timeout; le quote p1 sono presenti nell'indice del documento produttore [ripubblicato qui](https://www.verical.com/datasheet/wurth-elektronik-headers---pcb-receptacles-61201021621-6949211.pdf). Non è una verifica di disponibilità commerciale.

Saltati montaggio reale, tolleranze complete della dima, accesso USB e prove di durata/forza. Il CAD non dimostra che tutti i componenti acquistati entrino e funzionino nello stack.
