#pragma once

#include <array>
#include <cmath>
#include <cstddef>
#include "EnvelopeGenerator.h"
#include "Mcp4728Protocol.h"

namespace adlfo
{
constexpr size_t kChannels = 4;
enum class CvTarget { Off, Time, Rise, Fall, Level, Count };
inline float Clamp01(float value)
{
    return !(value > 0.0f) ? 0.0f : value >= 1.0f ? 1.0f : value;
}

struct Channel
{
    EnvelopeGenerator envelope;
    float rise = 0.70f, fall = 0.70f, symmetry = 0.5f, level = 1.0f;
    float cv = 0.0f;
    bool cv_enabled = false;
    CvTarget cv_target = CvTarget::Time;
    float effective_level = 1.0f;
    float rise_seconds = 0.1f, fall_seconds = 0.1f;
    CurveType curve = CurveType::Linear;

    void UpdateTimes()
    {
        const float offset = cv_enabled ? Clamp01(cv) * 0.35f : 0.0f;
        const float rise_offset = cv_target == CvTarget::Time || cv_target == CvTarget::Rise ? offset : 0.0f;
        const float fall_offset = cv_target == CvTarget::Time || cv_target == CvTarget::Fall ? offset : 0.0f;
        const float balance = (symmetry - 0.5f) * 0.70f;
        rise_seconds = 0.005f * std::pow(2000.0f, Clamp01(rise + rise_offset + balance));
        fall_seconds = 0.005f * std::pow(2000.0f, Clamp01(fall + fall_offset - balance));
    }

    void ApplyTimes()
    {
        envelope.SetRiseTime(rise_seconds);
        envelope.SetFallTime(fall_seconds);
        effective_level = Clamp01(level) * (cv_enabled && cv_target == CvTarget::Level ? Clamp01(cv) : 1.0f);
    }
};

// Owns all four voices. The UI only selects which Channel to edit.
// Callers serialize main/ISR access; no I2C or GPIO belongs in this class.
class EnvelopeBank
{
  public:
    std::array<Channel, kChannels> channels{};

    void Init(float rate)
    {
        for(auto& ch : channels)
        {
            ch = Channel{};
            ch.envelope.Init(rate);
            ch.envelope.SetCurve(ch.curve);
            ch.UpdateTimes();
            ch.ApplyTimes();
        }
        testing_ = false;
        test_channel_ = test_volts_ = 0;
    }

    void Trigger(size_t index)
    {
        if(!testing_ && index < kChannels)
            channels[index].envelope.Trigger();
    }

    void StopAll()
    {
        for(auto& ch : channels) ch.envelope.Stop();
    }

    void BeginTest()
    {
        StopAll();
        testing_ = true;
        test_channel_ = test_volts_ = 0;
    }

    void SetTest(size_t channel, unsigned volts)
    {
        if(channel >= kChannels) return;
        test_channel_ = channel;
        test_volts_ = volts > 2 ? 2 : volts;
    }

    void EndTest()
    {
        StopAll();
        testing_ = false;
        test_volts_ = 0;
    }

    std::array<uint16_t, kChannels> Process()
    {
        std::array<uint16_t, kChannels> codes{};
        if(testing_)
            codes[test_channel_] = static_cast<uint16_t>(2000u * test_volts_);
        else
            for(size_t i = 0; i < kChannels; ++i)
                codes[i] = mcp4728::CodeFromLevel(
                    channels[i].envelope.Process() * channels[i].effective_level);
        return codes;
    }

  private:
    bool testing_ = false;
    size_t test_channel_ = 0;
    unsigned test_volts_ = 0;
};
} // namespace adlfo
