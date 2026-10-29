"""Quantify the analog filter's rejection where sampling creates aliases/images."""
from math import log10, sin, pi
from pathlib import Path
import json
import check_full_paths as full

HERE=Path(__file__).resolve().parent
design=json.loads((full.PCB/'output'/'design.json').read_text(encoding='utf-8'))
full.FREQUENCIES=(1000,20000,24000,28000,48000,76000,96000)
full.HERE=HERE/'image_work';full.HERE.mkdir(exist_ok=True)
results=full.check_filters(design['parts'],'ideal')
output=next(r['db_at_hz'] for r in results if r['path']=='OUT1')
input_=next(r['db_at_hz'] for r in results if r['path']=='IN1')
fs=design['rates']['audio_hz'];tone=20000;image=fs-tone
sinc=lambda f:sin(pi*f/fs)/(pi*f/fs)
image_dbc=output[str(image)]-output[str(tone)]+20*log10(abs(sinc(image)/sinc(tone)))
alias_db=input_['76000']-input_['20000']
assert -14<image_dbc<-10
assert -45<alias_db<-42
report={'results':results,'audio_dac_sample_rate_hz':fs,'tone_hz':tone,'first_image_hz':image,
        'analog_output_gain_db':output[str(tone)],'analog_first_image_gain_db':output[str(image)],
        'first_image_relative_dbc_with_ideal_zoh':image_dbc,
        'adc_76khz_alias_to_20khz_relative_db':alias_db,
        'model':'Ideal voltage-output DAC with zero-order hold; ideal active analog filters; no digital interpolation.',
        'interpretation':'The present four-pole 20 kHz network alone is not a high-rejection 48 kHz DAC reconstruction filter. Define an audio image/alias rejection requirement before release.'}
(HERE/'sampling_images.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2))
print(f'DAC 48 kHz, 20 kHz tone: first 28 kHz image {image_dbc:.4f} dBc including ideal ZOH and analog filter.')
print(f'ADC 96 kHz: external-filter rejection of 76 kHz aliased onto 20 kHz is {alias_db:.4f} dB relative to 20 kHz gain.')
