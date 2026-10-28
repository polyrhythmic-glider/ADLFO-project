#pragma once

#include <array>
#include <cstdint>

namespace mcp4728
{
// Internal 2.048 V reference, gain 1: 4000 counts = nominally 2.000 V.
constexpr uint16_t kMaximumCode = 4000;

inline uint16_t CodeFromLevel(float level)
{
    if(!(level > 0.0f)) // Also handles NaN.
        return 0;
    if(level >= 1.0f)
        return kMaximumCode;
    return static_cast<uint16_t>(level * kMaximumCode + 0.5f);
}

// DS22187E, figure 5-8: Multi-Write updates volatile registers only.
// A/B/C/D, UDAC=0, internal Vref, normal power, gain 1. No EEPROM writes.
inline std::array<uint8_t, 12> AllChannels(const std::array<uint16_t, 4>& codes)
{
    std::array<uint8_t, 12> packet{};
    for(unsigned i = 0; i < 4; ++i)
    {
        const uint16_t code = codes[i] > kMaximumCode ? kMaximumCode : codes[i];
        packet[3 * i] = static_cast<uint8_t>(0x40 | (i << 1));
        packet[3 * i + 1] = static_cast<uint8_t>(0x80 | (code >> 8));
        packet[3 * i + 2] = static_cast<uint8_t>(code & 0xff);
    }
    return packet;
}

inline std::array<uint8_t, 12> AllZero()
{
    return AllChannels({{0, 0, 0, 0}});
}
} // namespace mcp4728
