#pragma once
#include <cstdio>
#include <cstring>
#include "util/oled_fonts.h"
#include "UiController.h"

namespace ui
{
template <typename Display>
void Text(Display& d, int x, int y, const char* text, FontDef font = Font_6x8)
{
    d.SetCursor(x, y);
    d.WriteString(text, font, true);
}
template <typename Display>
void Center(Display& d, int left, int width, int y, const char* text, FontDef font)
{
    Text(d, left + (width - int(std::strlen(text)) * font.FontWidth) / 2, y, text, font);
}
inline unsigned Percent(float value)
{
    return value <= 0 ? 0 : value >= 1 ? 100 : unsigned(value * 100 + 0.5f);
}
template <typename Display>
void TimeCell(Display& d, int left, int width, float seconds, const char* label)
{
    char value[12];
    const bool milliseconds = seconds < 0.9995f;
    if(milliseconds) std::snprintf(value, sizeof(value), "%u", unsigned(seconds * 1000 + 0.5f));
    else
    {
        unsigned tenths = unsigned(seconds * 10 + 0.5f);
        if(tenths >= 100) std::snprintf(value, sizeof(value), "%u", tenths / 10);
        else std::snprintf(value, sizeof(value), "%u.%u", tenths / 10, tenths % 10);
    }
    char title[12];
    std::snprintf(title, sizeof(title), "%s %s", label, milliseconds ? "ms" : "s");
    Center(d, left, width, 23, title, Font_6x8);
    Center(d, left, width, 33, value, Font_11x18);
}
template <typename Display>
void DrawMain(Display& d, float rise, float fall, float out, float symmetry,
              float level, bool cycling, const char* curve, unsigned channel)
{
    d.Fill(false);
    char text[16];
    std::snprintf(text, sizeof(text), "CH %u", channel);
    Text(d, 2, 0, text, Font_11x18);
    std::snprintf(text, sizeof(text), "%s  %s", cycling ? "LFO" : "AD", curve);
    Text(d, 68, 1, text);
    std::snprintf(text, sizeof(text), "OUT %u%%", Percent(out));
    Text(d, 68, 11, text);
    d.DrawLine(0, 20, 127, 20, true);
    d.DrawLine(63, 21, 63, 63, true);
    d.DrawLine(0, 53, 127, 53, true);
    TimeCell(d, 0, 63, rise, "RISE");
    TimeCell(d, 64, 64, fall, "FALL");
    std::snprintf(text, sizeof(text), "SYM %u%%", Percent(symmetry));
    Center(d, 0, 63, 56, text, Font_6x8);
    std::snprintf(text, sizeof(text), "LVL %u%%", Percent(level));
    Center(d, 64, 64, 56, text, Font_6x8);
}

template <typename Display>
void PageHeader(Display& d, const char* title, unsigned channel)
{
    d.Fill(false);
    Text(d, 1, 0, title, Font_7x10);
    char text[8];
    std::snprintf(text, sizeof(text), "CH %u", channel);
    Text(d, 103, 1, text);
    d.DrawLine(0, 12, 127, 12, true);
}

template <typename Display>
void Footer(Display& d, const char* text = "E2 CLICK: BACK")
{
    d.DrawLine(0, 54, 127, 54, true);
    Center(d, 0, 128, 56, text, Font_6x8);
}

template <typename Display>
void DrawSettings(Display& d, MenuItem selected, unsigned channel)
{
    constexpr const char* labels[] = {
        "CV TARGET", "CONTROLS", "ENCODER TEST", "OUTPUT TEST", "BACK"
    };
    PageHeader(d, "SETTINGS", channel);
    for(unsigned i = 0; i < unsigned(MenuItem::Count); ++i)
    {
        const int y = 14 + 10 * i;
        const bool active = i == unsigned(selected);
        if(active)
            for(int row = y; row < y + 10; ++row) d.DrawLine(0, row, 127, row, true);
        d.SetCursor(7, y + 1);
        d.WriteString(labels[i], Font_6x8, !active);
    }
}

template <typename Display>
void DrawControls(Display& d)
{
    constexpr const char* lines[] = {
        "E1 RISE  E2 FALL", "E3 SYM   E4 LEVEL", "E1 TAP:TRIG HOLD:MODE",
        "E2 TAP: CURVE", "E3/E4 TAP: RESET", "B1-4: CH1-4", "E1+E4 HOLD: SETTINGS"
    };
    d.Fill(false);
    for(unsigned i = 0; i < 7; ++i) Text(d, 1, i * 8, lines[i]);
    Text(d, 1, 56, "E2 CLICK: BACK");
}

template <typename Display>
void DrawEncoders(Display& d, const int32_t* values,
                  const std::array<Events, kEncoders>& events, unsigned channel)
{
    PageHeader(d, "ENCODERS", channel);
    for(unsigned i = 0; i < kEncoders; ++i)
    {
        const int y = 14 + i * 10;
        char text[16];
        std::snprintf(text, sizeof(text), "E%u", i + 1);
        Text(d, 2, y, text);
        std::snprintf(text, sizeof(text), "%ld", static_cast<long>(values[i]));
        Text(d, 22, y, text, Font_7x10);
        d.SetCursor(71, y);
        d.WriteString("SW", Font_6x8, !events[i].down);
        std::snprintf(text, sizeof(text), "B%u", i + 1);
        d.SetCursor(109, y);
        d.WriteString(text, Font_6x8, !events[i].button_down);
    }
    Footer(d, "E1+E4 HOLD: BACK");
}

inline const char* CvTargetName(adlfo::CvTarget target)
{
    switch(target)
    {
        case adlfo::CvTarget::Off: return "OFF";
        case adlfo::CvTarget::Time: return "RISE+FALL";
        case adlfo::CvTarget::Rise: return "RISE";
        case adlfo::CvTarget::Fall: return "FALL";
        case adlfo::CvTarget::Level: return "LEVEL";
        case adlfo::CvTarget::Count: break;
    }
    return "?";
}

template <typename Display>
void DrawCvTarget(Display& d, unsigned channel, adlfo::CvTarget target,
                  float cv, bool enabled)
{
    PageHeader(d, "CV TARGET", channel);
    Center(d, 0, 128, 18, CvTargetName(target), Font_11x18);
    char text[22];
    if(enabled) std::snprintf(text, sizeof(text), "CV IN %u%%", Percent(cv));
    else std::snprintf(text, sizeof(text), "CV INPUT DISABLED");
    Center(d, 0, 128, 40, text, Font_6x8);
    Footer(d);
}

template <typename Display>
void DrawOutputTest(Display& d, unsigned channel, unsigned volts)
{
    PageHeader(d, "OUTPUT TEST", channel);
    char text[12];
    std::snprintf(text, sizeof(text), "%u V", volts);
    Center(d, 0, 128, 18, text, Font_11x18);
    Center(d, 0, 128, 40, "B1-4:OUT E2:0/1/2V", Font_6x8);
    Footer(d);
}
} // namespace ui
