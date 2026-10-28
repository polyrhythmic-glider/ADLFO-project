#pragma once

#include "EnvelopeBank.h"
#include "UiInput.h"

namespace ui
{
static_assert(kEncoders == adlfo::kChannels, "One panel button per channel");

enum class Page { Main, Settings, Controls, Encoders, OutputTest, CvTarget };
enum class MenuItem : unsigned { CvTarget, Controls, Encoders, OutputTest, Back, Count };

inline unsigned WrapSelection(int64_t value, unsigned count)
{
    value %= count;
    return static_cast<unsigned>(value < 0 ? value + count : value);
}

// UI state and commands live here; the hardware caller serializes access to
// the envelope bank. All four voices keep running while settings are open.
class Controller
{
  public:
    Page page = Page::Main;
    MenuItem menu_item = MenuItem::CvTarget;
    unsigned channel = 0;
    unsigned test_volts = 0;
    int32_t encoder_values[kEncoders]{};

    void Process(const Frame& frame, adlfo::EnvelopeBank& bank)
    {
        const unsigned previous_channel = channel;
        bool selected = false;
        for(unsigned i = 0; i < kEncoders; ++i)
            if(frame.events[i].button_presses)
            {
                channel = i;
                selected = true;
            }
        if(selected && page == Page::OutputTest)
        {
            test_volts = 0;
            bank.SetTest(channel, 0);
        }

        if(frame.shortcut.toggles)
        {
            for(unsigned i = 0; i < frame.shortcut.toggles; ++i)
                ChangePage(page == Page::Settings ? Page::Main : Page::Settings,
                           frame, bank);
        }
        if(frame.shortcut.suppress || frame.shortcut.toggles
           || channel != previous_channel || (selected && page == Page::OutputTest))
        {
            BlockHeld(frame);
            return;
        }

        auto events = frame.events;
        for(unsigned i = 0; i < kEncoders; ++i)
        {
            if(blocked_[i])
            {
                blocked_[i] = events[i].down;
                events[i] = {};
            }
        }
        auto& voice = bank.channels[channel];
        const bool click = events[1].taps || events[1].long_presses;
        switch(page)
        {
            case Page::Main:
                voice.rise = Adjust(voice.rise, events[0].delta);
                voice.fall = Adjust(voice.fall, events[1].delta);
                voice.symmetry = Adjust(voice.symmetry, events[2].delta);
                voice.level = Adjust(voice.level, events[3].delta);
                if(events[0].long_presses & 1)
                    voice.envelope.SetCycling(!voice.envelope.IsCycling());
                if(events[0].taps) bank.Trigger(channel);
                for(unsigned i = 0; i < (events[1].taps + events[1].long_presses) % 3; ++i)
                {
                    voice.curve = static_cast<CurveType>(
                        (static_cast<unsigned>(voice.curve) + 1) % 3);
                    voice.envelope.SetCurve(voice.curve);
                }
                if(events[2].taps || events[2].long_presses) voice.symmetry = 0.5f;
                if(events[3].taps || events[3].long_presses) voice.level = 1.0f;
                break;
            case Page::Settings:
                menu_item = static_cast<MenuItem>(WrapSelection(
                    int64_t(menu_item) + events[1].delta, unsigned(MenuItem::Count)));
                if(click)
                {
                    switch(menu_item)
                    {
                        case MenuItem::CvTarget: ChangePage(Page::CvTarget, frame, bank); break;
                        case MenuItem::Controls: ChangePage(Page::Controls, frame, bank); break;
                        case MenuItem::Encoders: ChangePage(Page::Encoders, frame, bank); break;
                        case MenuItem::OutputTest: ChangePage(Page::OutputTest, frame, bank); break;
                        case MenuItem::Back: ChangePage(Page::Main, frame, bank); break;
                        case MenuItem::Count: break;
                    }
                }
                break;
            case Page::CvTarget:
                voice.cv_target = static_cast<adlfo::CvTarget>(WrapSelection(
                    int64_t(voice.cv_target) + events[1].delta, unsigned(adlfo::CvTarget::Count)));
                if(click) ChangePage(Page::Settings, frame, bank);
                break;
            case Page::Controls:
                if(click) ChangePage(Page::Settings, frame, bank);
                break;
            case Page::Encoders:
                for(unsigned i = 0; i < kEncoders; ++i)
                {
                    const int64_t value = int64_t(encoder_values[i]) + events[i].delta;
                    encoder_values[i] = value < -9999 ? -9999 : value > 9999 ? 9999 : value;
                    if(events[i].taps || events[i].long_presses) encoder_values[i] = 0;
                }
                break;
            case Page::OutputTest:
            {
                const int64_t value = int64_t(test_volts) + events[1].delta;
                test_volts = value < 0 ? 0 : value > 2 ? 2 : value;
                bank.SetTest(channel, test_volts);
                if(click) ChangePage(Page::Settings, frame, bank);
                break;
            }
        }
    }

  private:
    bool blocked_[kEncoders]{};

    static float Adjust(float value, int32_t delta)
    {
        return adlfo::Clamp01(value + static_cast<float>(delta) * 0.02f);
    }

    void BlockHeld(const Frame& frame)
    {
        for(unsigned i = 0; i < kEncoders; ++i) blocked_[i] = frame.events[i].down;
    }

    void ChangePage(Page next, const Frame& frame, adlfo::EnvelopeBank& bank)
    {
        if(page == Page::OutputTest)
        {
            bank.EndTest();
            test_volts = 0;
        }
        if(next == Page::OutputTest)
        {
            bank.BeginTest();
            test_volts = 0;
            bank.SetTest(channel, 0);
        }
        if(next == Page::Encoders)
            for(auto& value : encoder_values) value = 0;
        page = next;
        BlockHeld(frame);
    }
};
} // namespace ui
