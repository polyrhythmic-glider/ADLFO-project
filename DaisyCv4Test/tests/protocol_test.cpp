#include "../Cv4Protocol.h"
#include <cassert>
#include <limits>

int main()
{
    // Known frame from the datasheet field order, including all four channel IDs.
    const std::array<uint8_t, 12> expected{
        0x40, 0x00, 0x00, 0x42, 0x04, 0x00,
        0x44, 0x08, 0x00, 0x46, 0x0f, 0xa0};
    assert(cv4::Packet({0, 1024, 2048, 4000}) == expected);
    const auto limited = cv4::Packet({4095, 65535, 4001, 4000});
    for(unsigned ch = 0; ch < 4; ++ch)
    {
        assert(limited[3*ch] == 0x40 + 2*ch); // Volatile Multi-Write, never EEPROM.
        assert(limited[3*ch+1] == 0x0f); // VDD ref, normal power, gain 1.
        assert(limited[3*ch+2] == 0xa0);
    }
    assert(cv4::CodeFromAdc(0.0f) == 0);
    assert(cv4::CodeFromAdc(-1.0f) == 0);
    assert(cv4::CodeFromAdc(std::numeric_limits<float>::quiet_NaN()) == 0);
    assert(cv4::CodeFromAdc(5.0f * 33.0f / 133.0f / 3.3f) == 2000);
    assert(cv4::CodeFromAdc(10.0f * 33.0f / 133.0f / 3.3f) == 4000);
    assert(cv4::CodeFromAdc(1.0f) == 4000);
}
