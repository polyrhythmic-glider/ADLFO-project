#pragma once

#include <array>
#include <cstdint>

namespace cv4
{
constexpr uint16_t kMaximumCode = 4000;
constexpr float kAdcAtTenVolts = (10.0f * 33.0f / 133.0f) / 3.3f;
using Codes = std::array<uint16_t, 4>;

// MCP4728, DS22187E figure 5-8: Multi-Write, volatile DAC registers only.
// VREF=VDD, PD=normal, gain=1, UDAC=0; LDAC is physically tied to GND.
inline std::array<uint8_t, 12> Packet(const Codes& codes)
{
    std::array<uint8_t, 12> data{};
    for(unsigned channel = 0; channel < 4; ++channel)
    {
        const auto value = codes[channel] > kMaximumCode
                               ? kMaximumCode : codes[channel];
        data[3 * channel] = static_cast<uint8_t>(0x40 | (channel << 1));
        data[3 * channel + 1] = static_cast<uint8_t>((value >> 8) & 0x0f);
        data[3 * channel + 2] = static_cast<uint8_t>(value & 0xff);
    }
    return data;
}

inline uint16_t CodeFromAdc(float adc)
{
    if(!(adc > 0.0f)) // Includes invalid/NaN readings.
        return 0;
    const float level = adc / kAdcAtTenVolts;
    if(level >= 1.0f)
        return kMaximumCode;
    return static_cast<uint16_t>(level * kMaximumCode + 0.5f);
}
} // namespace cv4
