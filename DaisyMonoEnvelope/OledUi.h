#pragma once
#include <cstdio>
#include <cstring>
#include "util/oled_fonts.h"

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
    Center(d, left, width, 2, label, Font_6x8);
    Center(d, left, width, 13, value, Font_11x18);
    Center(d, left, width, 33, milliseconds ? "ms" : "s", Font_6x8);
}
template <typename Display>
void DrawMain(Display& d, float rise, float fall, float out, float symmetry,
              float level, float cv, bool cycling, const char* curve)
{
    d.Fill(false);
    d.DrawLine(42, 0, 42, 42, true);
    d.DrawLine(86, 0, 86, 42, true);
    d.DrawLine(0, 42, 127, 42, true);
    d.DrawLine(77, 42, 77, 63, true);
    TimeCell(d, 0, 42, rise, "RISE");
    TimeCell(d, 43, 43, fall, "FALL");
    Center(d, 87, 41, 2, "OUT", Font_6x8);
    char text[16];
    std::snprintf(text, sizeof(text), "%u", Percent(out));
    Center(d, 87, 41, 13, text, Font_11x18);
    Center(d, 87, 41, 33, "%", Font_6x8);
    std::snprintf(text, sizeof(text), "E3 SYM:%u", Percent(symmetry));
    Text(d, 2, 45, text);
    std::snprintf(text, sizeof(text), "E4 LVL:%u", Percent(level));
    Text(d, 2, 55, text);
    std::snprintf(text, sizeof(text), "%s %s", cycling ? "LFO" : "AD", curve);
    Text(d, 80, 45, text);
    std::snprintf(text, sizeof(text), "CV:%u%%", Percent(cv));
    Text(d, 80, 55, text);
}
template <typename Display>
void DrawEncoders(Display& d, const int32_t* values, const bool* down,
                  const bool* buttons)
{
    d.Fill(false);
    d.DrawLine(63, 0, 63, 63, true);
    d.DrawLine(0, 31, 127, 31, true);
    for(unsigned i = 0; i < 4; ++i)
    {
        const int x = (i % 2) * 64, y = (i / 2) * 32;
        char text[16];
        if(buttons[i])
        {
            // Full quadrant feedback; the encoder counter remains unchanged.
            for(int row = y; row < y + 32; ++row)
                d.DrawLine(x, row, x + 63, row, true);
            std::snprintf(text, sizeof(text), "B%u", i + 1);
            d.SetCursor(x + 21, y + 7);
            d.WriteString(text, Font_11x18, false);
            continue;
        }
        std::snprintf(text, sizeof(text), "E%u", i + 1);
        Text(d, x + 3, y + 1, text);
        // Each quadrant pairs its encoder with the separate panel button.
        std::snprintf(text, sizeof(text), "B%u", i + 1);
        d.SetCursor(x + 23, y + 1);
        d.WriteString(text, Font_6x8, true);
        if(down[i]) Text(d, x + 43, y + 1, "RST");
        std::snprintf(text, sizeof(text), "%ld", static_cast<long>(values[i]));
        Center(d, x, 63, y + 12, text, Font_11x18);
    }
}
} // namespace ui
