"""Payload lower bounds; no assertion of a working DMA schedule or board timing."""
import json
import sys
from pathlib import Path


def utilization(adc_hz, dac_hz, adc_clock, dac_clock):
    return adc_hz * 144 / adc_clock + dac_hz * 256 / dac_clock


assert utilization(1, 1, 144, 256) == 2
design = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
rates = design["rates"]
adc_rate, dac_rate = rates["adc_hz"], rates["audio_hz"]
adc_clock, dac_clock = rates["adc_spi_target_hz"], rates["dac_spi_target_hz"]
print(f"Current payload occupancy with globally serialized SPI DMA: {100 * utilization(adc_rate, dac_rate, adc_clock, dac_clock):.3f}%")
print(f"Default libDaisy PLL2P=25MHz, minimum prescaler /2: ADC frame {144 / 12.5:.3f}us versus period {1e6 / adc_rate:.3f}us")
print(f"Future explicit 100MHz SPI kernel, ADC /2=50MHz and DAC /4=25MHz: serialized payload {100 * utilization(adc_rate, dac_rate, 50e6, 25e6):.3f}%")
print("USB-only: VDRIVE=3.3V and AVCC=0V; allowed VDRIVE<=AVCC+0.3V gives 3.000V excess")
for part in design["parts"]:
    if part["footprint"] == "jack" and part["value"].startswith("IN"):
        print(f"{part['ref']} {part['value'].split()[0]} normal contact: {part['pins']['TN']!r}")
