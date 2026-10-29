# Digital and analog subsystem review, 2026-10-28

Reviewed current 301-part revision D. Production files were not modified.
`findings.json` contains three findings for the root review's evidence gate.
Calculations are reproducible with `check_digital_budget.py hardware/pcb/output/design.json`.

## Findings

1. **Blocker, U1/U2 supply sequencing.** With carrier off, USB still powers the Seed's 3V3 output; U2 VDRIVE is on that output, AVCC is on the unpowered carrier 5A. AD7606C-18 Rev B p14 Table6 requires VDRIVE <= AVCC+0.3V. A 3.3V/0V combination exceeds that maximum by 3.0V. Gate/output disabling cannot repair this. Also consider differing rail decay during ordinary shutdown. Hardware supply/signalling sequencing needs resolution; a clamp diode alone must not be assumed safe because it backfeeds the 5A/5D network.
2. **Blocker for the proposed backend, U1/U2/U3 throughput.** Stock libDaisy serializes all SPI DMA jobs on streams2/3. At 96k ADC and48k DAC, 25MHz each means104.448% lower-bound occupation. Its default25MHz SPI kernel plus minimum /2 prescaler only supplies12.5MHz SCK, already too slow for the ADC alone. A future100MHz kernel with ADC50MHz and DAC25MHz is arithmetically possible at76.8%, but the DAC must be split into32-bit word jobs around ADC read slots. SI, interrupts, setup/hold, conversion times and settling still need a measured schedule. Do not present a requested clock as an implemented one.
3. **Warning, fixed inputs float when unpatched.** J1/J4/J7/J10 TN terminals are open. Their unity-gain Sallen-Key plus inputs have no DC return once capacitors are considered open. Ground those four normals only. A patch on CTRL must not short an enabled output, so its normal remains open; define unused CTRL behavior in the future backend.

## No-change conclusions

- U2's 64-pin assignments were compared to AD7606C-18 Table9 pp15-17 and serial-mode Table23 p42: AVCC1/37/38/48, VDRIVE23, sixAGND pins, all eight VxP/VxN pairs, REFIN42, REFCAP44/45, REGCAP36/39, CS13, SCLK12, BUSY14, RESET11, CONVST9 and SDI29 agree. OS[2:0]=111 selects software mode; PAR/SER=1 selects serial; oneDOUTA requires register configuration. Unused DOUT lines stay open and serial-N/A pins are grounded. No pin swap found.
- U3's PW16 pin order matches DAC8568 RevF p4. GradeB is the required unity-gain2.5V/midscale-reset variant (p3 family table; p32 eq1); other grades cannot be substituted blindly. Four-byte write construction in `platform/ConverterProtocol.h` matches p35 Table1 and p36 control matrix: channel atDB23:20, dataDB19:4, write-input command0. Decoder sign extension correctly recovers eight packed18-bit two's-complement words.
- U12/U13 AHCT125 have VCC14/GND7, enables1/4/10/13 low and correct A/Y pairs2/3,5/6,9/8,12/11. AHCT inputs accept TTL levels, so 3.3V host to5V DAC is appropriate; unused inputs are grounded and outputs open. Supply5A is within the4.5-5.5V rating while operating normally. The default-enabled buffers and their high-speed behavior do not themselves establish safe ADC sequencing.
- U4 SOIC28 pinout matches MCP23017 DS20001952C Table2-1 p10; GPB0=KEY4 and GPA7/GPB7 are reserved as outputs. Three addresses grounded give0x20. Reset has a pull-up. I2C400kHz at3.3V is supported; parallel pull-ups on the display still need actual hardware measurement.
- Daisy Seed3 pin map matches v2.1 pp5-7: D0..14 physical1..15, D15..30 physical22..37; both grounds20/40; VIN39; digital3V3 pin38; analog3V3 pin21 unused. Its SPI1 and SPI3 alternate-function choices are valid. Correct pins do not imply independent DMA resources.
- U9/U10 differential stages implement `(1+40k/10k)*0.8*VDAC -4*VREF_HALF =4*VDAC -5V`. Nominal no-load output is -5V through4.999847V; zero is code32768. Reference divider10k/10k plus U11 follower supplies1.25V. Reference load is modest. Calibration and load-dependent1k series error remain required.
- U9/U10/U11/U21-U24 OPA4197 SOIC14 pin order agrees with RevC pp3-4. All seven devices have both supplies and local bypass. Every filter follower and feedback capacitor topology agrees with the declared two-section Sallen-Key network. ±12V is within the part supply range. 20kHz,5V peak requires0.628V/us, below the20V/us typical slew specification. This is a plausibility margin, not a measured distortion/stability result.
- Seven OPA4197 packages have nominal28-amplifier quiescent current near28mA. At24V total supply the approximate total quiescent dissipation is0.672W, or0.096W/package; SOIC θJA86.4C/W gives8.3C/package rise before signal and collision loads. These numbers are estimates; output contention can dominate thermal behavior.
- `Adolfo/` is intentionally the working MCP4728 prototype. It must remain separated from the unsupported new ADC/DAC carrier. Its current hardware map must not be silently retargeted to this board.

## Primary evidence

- [AD7606C-18 Rev B](https://www.analog.com/media/en/technical-documentation/data-sheets/ad7606c-18.pdf), pp12/14-17/42/47-50. Official PDF web-readable; direct download failed twice with remote disconnect.
- [DAC8568 Rev F](https://www.ti.com/lit/ds/symlink/dac8568.pdf), pp3-4/32/34-36. Local `datasheets/dac8568.pdf` and page-separatedTXT.
- [OPA4197 Rev C](https://www.ti.com/lit/ds/symlink/opa4197.pdf), pp1/3-9. Local `datasheets/opa4197.pdf` andTXT.
- [AHCT125 Rev R](https://www.ti.com/lit/ds/symlink/sn74ahct125.pdf), pp2/4-6. Local `datasheets/sn74ahct125.pdf` andTXT.
- [MCP23017 DS20001952C](https://ww1.microchip.com/downloads/en/DeviceDoc/20001952C.pdf), pp1/4/6/10. The project's original manufacturer URL is404; this official alternative works and was saved locally.
- [Seed3 v2.1](https://daisy.nyc3.cdn.digitaloceanspaces.com/products/seed3/Daisy_Seed3_datasheet.pdf), pp5-10. Local `datasheets/daisy_seed3.pdf` andTXT.
- [libDaisy SPI source](https://raw.githubusercontent.com/daisyaudio/libDaisy/master/src/per/spi.cpp), `InitDma`, `IsDmaBusy`, `DmaReceive`, `DmaTransmit`, pin alternate-function table.
- [libDaisy system source](https://raw.githubusercontent.com/daisyaudio/libDaisy/master/src/sys/system.cpp), PLL2 configuration and `Spi123ClockSelection`.
- [ST HAL RCC source](https://raw.githubusercontent.com/STMicroelectronics/stm32h7xx-hal-driver/master/Src/stm32h7xx_hal_rcc_ex.c), SPI123CLKSOURCE_PLL2 usesPLL2_P_Frequency.

Not checked here: PCB geometric routing/DFM/ERC, hardware measurements, EMC compliance, purchase-qualified passive MPNs, real converter backend. Root handles geometry/analyzers and consolidated verdict. USB sequencing and backend timing remain release risks.
