#pragma once

#include "daisy_seed.h"

namespace hardware_config
{
constexpr auto kI2cScl = daisy::seed::D11;
constexpr auto kI2cSda = daisy::seed::D12;
// DAC + short OLED transactions: target 1 kHz for all four outputs.
constexpr auto kI2cSpeed = daisy::I2CHandle::Config::Speed::I2C_400KHZ;

// Pins deliberately unset until the actual wiring is agreed.
// Assign a valid pin AND enable that input after assembling its conditioner.
struct TriggerInput
{
    daisy::Pin pin;
    bool enabled;
    bool inverted;
};
struct CvInput
{
    daisy::Pin pin;
    bool enabled;
    float full_scale; // ADC fraction at maximum external CV; calibrate after wiring.
};
constexpr TriggerInput kTriggers[4] = {
    {{}, false, true}, {{}, false, true}, {{}, false, true}, {{}, false, true},
};
// Nominal scale of the proposed 100k/33k input divider, not a measured value.
constexpr float kProposedCvFullScale = (10.0f * 33.0f / 133.0f) / 3.3f;
constexpr CvInput kCv[4] = {
    {{}, false, kProposedCvFullScale},
    {{}, false, kProposedCvFullScale},
    {{}, false, kProposedCvFullScale},
    {{}, false, kProposedCvFullScale},
};
} // namespace hardware_config
