# Power and safety review — 2026-10-28

Analyzed generator mappings and saved design parts for every power/safety IC and all four protection switches. Evidence PDFs and text are in `hardware/pcb/datasheets/` and this folder. Manufacturer sources: TPS382x Rev O pp. 4–7; TPS3808 Rev N pp. 4–7; LM393B Rev AH pp. 3–7; SN74HC74 Rev F pp. 3–7; SN74HCS74 Rev D pp. 3–6; SN74LVC1G08 Rev AA pin table/ratings; RECOM R-78E-1.0 Rev 9/2024 pp. 1–4; ADG5412F Rev C pp. 3, 11–13, 25–27; Vishay CRCW-HP e3 doc 20043 Rev 17-Mar-2026 pp. 1–3, 6, 9.

## Pinout and function conclusions

- U17 TPS3828-33: pin 1 RESET, 2 GND, 3 MR, 4 WDI, 5 VDD matches the circuit. WDI has a 10 kΩ pull-down, preventing the watchdog from being disabled through a floating MCU pin. The falling supply threshold is 2.93 V nominal, 2.86–3.00 V over −40..85°C.
- U18 TPS3808 SOT-23-6: pin 1 RESET, 2 GND, 3 MR, 4 CT, 5 SENSE, 6 VDD matches. CT = 10 nF programs approximately 58 ms nominal using the datasheet equation. Threshold accuracy and hysteresis require the redesign described in findings.json.
- U16: active latch pins 1 CLR, 2 D, 3 CLK, 4 PRE and 5 Q are coherent; unused channel inputs are fixed at valid levels. Firmware still must wait for reset release/recovery before producing a new permit edge. HCS74 adds Schmitt inputs without changing the pinout or package.
- U19 LM393B: pins 1 OUT1, 2 IN1−, 3 IN1+, 4 GND, 5 IN2+, 6 IN2−, 7 OUT2, 8 VCC match. Positive undervoltage and missing negative rail both pull SAFE_CLEAR_N low. Normal inputs around 1.5–1.9 V satisfy common-mode limits at 5 V.
- U20 SN74LVC1G08 SOT-23-5: pins 1 A, 2 B, 3 GND, 4 Y, 5 VCC match. The 3.3 V logic domains and ADG input high threshold of 2.0 V align.
- ADG5412F TSSOP: protected source pins 3/14/11/6 face the external jacks; drains 2/15/10/7 face internal circuits. Controls 1/16/9/8, VSS pin 4, GND pin 5, VDD pin 13 and FF pin 12 match. Input switches remain enabled; output switches use qualified permit.
- ADG FF uses a weak internal pull-up and may share a fault bus. The official manufacturer FAQ explicitly permits combining flags into one interrupt: https://ez.analog.com/switches_multiplexers/a/documents/do26787/faq-adg54xxf (Q1). This connection is not push-pull contention.
- The positive and negative series polarity diodes are oriented correctly. IDC10 pins 1/2 = −12 V, 3..8 = GND, 9/10 = +12 V match.
- ADG power-off protection requires ground and applies with both supplies absent. It does not establish that every circuit path is isolated during USB-only operation or partial rail loss.

## Calculated limits

`check_current.py` reads saved design values, enumerates specified corners and contains assertions. Output excludes unspecified resistor TCR, trace drops and dynamic response.

| Monitor | Assumptions | Result |
| --- | --- | --- |
| 5A falling | TPS3808 ±2%, R ±0.1%, sense current ±25 nA | 4.711744–4.927632 V |
| 5A rising | Same corners plus maximum 3% hysteresis | Up to 5.075379 V |
| Positive rail falling | V33 = 3.300 V, R ±0.1%, LM393B offset ±4 mV and bias 0..50 nA per pin | 10.355751–10.467912 V |
| Negative rail fault | Same | −10.514931..−10.318781 V |
| Positive rail at V33 = 2.86 V | Immediately before the worst low TPS3828 trip | 8.971271–9.075983 V |
| Negative rail at V33 = 2.86 V | Same | −9.124047..−8.937973 V |

The ±12 V monitors are ratiometric. These values cannot be advertised as fixed 10.4 V limits without specifying the 3.3 V reference range. RECOM output may be 4.75 V from its ±5% accuracy before ripple; the regulator and supervisor therefore do not guarantee either reset release or ADC minimum supply.

## Output collisions and thermal limits

With R = 1 kΩ ±1%, use Rmin = 990 Ω and ignore switch resistance conservatively:

| Driver / external source | Current | Resistor dissipation |
| --- | --- | --- |
| +5 V / −12 V, or −5 V / +12 V | 17.172 mA | 0.291919 W |
| +5 V / −5 V | 10.101 mA | 0.101010 W |
| Saturated driver +11.5 V / external −12 V | 23.737 mA | 0.557828 W |
| Conservative +12 V / −12 V | 24.242 mA | 0.581818 W |

A 0.5 W component plausibly handles normal ±5 V collisions at suitable local temperature, but lacks continuous margin for the rail saturation fault. Vishay CRCW20101K00FKEFHP is a real 1 kΩ ±1% 2010 HP part. Manufacturer doc 20043 gives P70 = 1 W; 1.75 W is conditional on terminal temperature and must not be claimed as an unconditional rating. Linear derating gives approximately 0.647 W at 100°C local ambient, leaving about 11% margin against the 0.582 W fault before TCR. Film temperature must remain ≤155°C.

ADG TSSOP continuous channel current is 29 mA at 125°C in the conservative rail-to-rail case (datasheet p. 11), exceeding these calculated currents. This is a static comparison, not a transient-current guarantee.

OPA4197 SOIC θJA = 86.4°C/W (p. 6), with maximum Iq = 1.5 mA per amplifier (p. 8). Four simultaneous collisions into +12 V produce maximum output-stage dissipation around Vcmd = (+12 − 11.5)/2 = 0.25 V. At Rmin = 990 Ω, Pquad ≈ 4 × 11.75²/990 + 23 V × 6 mA = 0.696 W, giving an estimated junction rise of 60.1°C. The datasheet asks Tj ≤125°C for multiple high-current channels. Local ambient near 65°C would consume the entire estimated margin before board thermal coupling. Bench qualification remains necessary.

## Remaining power qualification

R-78E operates to 85°C with derating. A 0.7 A / 5 V load is 3.5 W; efficiency endpoints of 85–93% suggest 0.26–0.62 W converter heat, only an estimate until the actual 12 V/load operating point is measured. The seven quad amplifiers add up to 28 × 1.5 mA = 42 mA quiescent load per analog supply path before output currents. Both PTCs need hot hold-current and inrush qualification. RECOM's application page asks for a soft-start source; Eurorack hot-plug behavior has not been demonstrated.

TPS3808E retains broad threshold error and up to 2.5% hysteresis, so it does not alone solve the 5A budget. TSR1-2450 has better set accuracy than R-78E but still has line/load/temperature/ripple errors and does not solve G01 hysteresis. No untested drop-in replacement is represented as a completed fix.
