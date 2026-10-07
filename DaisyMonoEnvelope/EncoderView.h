#pragma once
#include <cstdint>

namespace ui
{
struct Shortcut { unsigned toggles = 0; bool suppress = false; };

// Scan in the interrupt: even a chord completed during OLED I/O is retained.
class Chord
{
  public:
    void Scan(bool first, bool fourth)
    {
        if(first && fourth && !latched_) { ++pending_.toggles; latched_ = true; }
        pending_.suppress |= latched_;
        if(!first && !fourth) latched_ = false;
    }
    Shortcut Consume()
    {
        Shortcut result = pending_;
        result.suppress |= latched_;
        pending_ = {};
        return result;
    }
  private:
    bool latched_ = false;
    Shortcut pending_{};
};

struct EncoderView
{
    bool active = false;
    int32_t values[4]{};
    bool armed[4]{};

    template <typename Events>
    bool Process(const Events& events, Shortcut shortcut)
    {
        if(shortcut.toggles & 1) active = !active;
        if(shortcut.suppress || shortcut.toggles)
        {
            for(auto& arm : armed) arm = false;
            return true;
        }
        if(!active) return false;
        for(unsigned i = 0; i < 4; ++i)
        {
            const int64_t value = int64_t(values[i]) + events[i].delta;
            values[i] = value < -9999 ? -9999 : value > 9999 ? 9999 : value;
            if(events[i].pressed) armed[i] = true;
            if(events[i].released)
            {
                if(armed[i]) values[i] = 0;
                armed[i] = false;
            }
        }
        return true;
    }
};
} // namespace ui
