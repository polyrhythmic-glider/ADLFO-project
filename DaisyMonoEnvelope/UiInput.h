#pragma once

#include <array>
#include <cstdint>

namespace ui
{
constexpr unsigned kEncoders = 4;
constexpr uint32_t kLongPressMs = 750;
constexpr uint32_t kSettingsHoldMs = 900;

struct Events
{
    int32_t delta = 0;
    uint32_t taps = 0, long_presses = 0, button_presses = 0;
    bool down = false, button_down = false;
};

struct Shortcut
{
    unsigned toggles = 0;
    bool suppress = false;
};

struct Frame
{
    std::array<Events, kEncoders> events{};
    Shortcut shortcut;
};

// Classify on release, so even E1 held before E4 cannot change AD/LFO while
// starting the settings gesture. Unsigned subtraction also handles clock wrap.
class Press
{
  public:
    void Scan(bool pressed, bool released, uint32_t now, Events& pending)
    {
        if(pressed)
        {
            down_ = true;
            started_ = now;
        }
        if(released && down_)
        {
            if(now - started_ >= kLongPressMs) ++pending.long_presses;
            else ++pending.taps;
            down_ = false;
        }
        pending.down = down_;
    }

  private:
    bool down_ = false;
    uint32_t started_ = 0;
};

// Scanned at 1 kHz, independently of OLED transfers. A partial chord cancels
// individual clicks until BOTH encoders are released; only a continuous hold
// opens settings, once per gesture.
class Chord
{
  public:
    void Scan(bool first, bool fourth, uint32_t now)
    {
        if(first && fourth)
        {
            latched_ = true;
            if(!holding_)
            {
                holding_ = true;
                started_ = now;
            }
            if(!fired_ && now - started_ >= kSettingsHoldMs)
            {
                ++pending_.toggles;
                fired_ = true;
            }
        }
        else holding_ = false;

        pending_.suppress |= latched_;
        if(!first && !fourth) latched_ = fired_ = false;
    }

    Shortcut Consume()
    {
        Shortcut result = pending_;
        result.suppress |= latched_;
        pending_ = {};
        return result;
    }

  private:
    bool latched_ = false, holding_ = false, fired_ = false;
    uint32_t started_ = 0;
    Shortcut pending_{};
};
} // namespace ui
