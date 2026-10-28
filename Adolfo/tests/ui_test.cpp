#include "UiController.h"
#include "OledUi.h"
#include <array>
#include <cassert>
#include <fstream>
#include <string>
#include <vector>

struct Canvas
{
    struct TextRun { std::string text; unsigned width; };
    bool pixels[64][128]{};
    int x = 0, y = 0;
    std::vector<TextRun> text;

    void Fill(bool on)
    {
        for(auto& row : pixels) for(auto& p : row) p = on;
        text.clear();
    }
    void SetCursor(int a, int b) { x = a; y = b; }
    void Pixel(int a, int b, bool on)
    {
        assert(a >= 0 && a < 128 && b >= 0 && b < 64);
        pixels[b][a] = on;
    }
    void DrawLine(int a, int b, int c, int e, bool on)
    {
        assert(a == c || b == e);
        for(int j = b; j <= e; ++j) for(int i = a; i <= c; ++i) Pixel(i, j, on);
    }
    void WriteString(const char* s, FontDef f, bool on)
    {
        assert(x >= 0 && y >= 0 && x + int(std::strlen(s)) * f.FontWidth <= 128
               && y + f.FontHeight <= 64);
        text.push_back({s, f.FontWidth});
        for(; *s; ++s, x += f.FontWidth)
            for(int j = 0; j < f.FontHeight; ++j)
                for(int i = 0; i < f.FontWidth; ++i)
                    Pixel(x + i, y + j, (f.data[(*s - 32) * f.FontHeight + j]
                                          & (0x8000 >> i)) ? on : !on);
    }
    void Save(const char* path)
    {
        std::ofstream out(path);
        out << "P1\n128 64\n";
        for(auto& row : pixels)
        {
            for(bool p : row) out << (p ? 0 : 1) << ' ';
            out << '\n';
        }
    }
};

// Exercise the same press/chord pipeline used by the 1 kHz hardware scan,
// including several scans coalesced into one main-loop frame.
struct Panel
{
    ui::Controller state;
    adlfo::EnvelopeBank bank;
    ui::Press presses[4];
    ui::Chord chord;
    ui::Frame pending;
    unsigned held = 0;
    uint32_t now = 0;

    Panel() { bank.Init(10000); }
    void Flush()
    {
        pending.shortcut = chord.Consume();
        state.Process(pending, bank);
        for(auto& e : pending.events)
        {
            e.delta = 0;
            e.taps = e.long_presses = e.button_presses = 0;
        }
    }
    void Scan(unsigned mask, uint32_t elapsed = 1, bool consume = true)
    {
        now += elapsed;
        for(unsigned i = 0; i < 4; ++i)
        {
            const unsigned bit = 1u << i;
            presses[i].Scan((mask & bit) && !(held & bit),
                            !(mask & bit) && (held & bit), now, pending.events[i]);
        }
        held = mask;
        chord.Scan(pending.events[0].down, pending.events[3].down, now);
        if(consume) Flush();
    }
    void Tap(unsigned encoder, uint32_t duration = 40)
    {
        Scan(held | (1u << encoder));
        Scan(held & ~(1u << encoder), duration);
    }
    void Rotate(unsigned encoder, int32_t delta)
    {
        pending.events[encoder].delta += delta;
        Flush();
    }
    void Button(unsigned channel)
    {
        ++pending.events[channel].button_presses;
        Flush();
    }
    void Settings()
    {
        Scan(9);
        Scan(9, ui::kSettingsHoldMs);
        Scan(0);
    }
    void Open(ui::MenuItem item)
    {
        assert(state.page == ui::Page::Settings);
        Rotate(1, int(item) - int(state.menu_item));
        Tap(1);
    }
};

static void AssertZero(adlfo::EnvelopeBank& bank)
{
    assert((bank.Process() == std::array<uint16_t, 4>{{0, 0, 0, 0}}));
}

static void TestSettingsGesture()
{
    for(unsigned first : {1u, 8u})
    {
        Panel p;
        p.bank.channels[0].level = .4f;
        // Starting E1 early must not toggle AD/LFO before E4 joins.
        p.Scan(first);
        p.Scan(first, 1100);
        assert(!p.bank.channels[0].envelope.IsCycling());
        p.Scan(9);
        p.Scan(9, ui::kSettingsHoldMs - 1);
        assert(p.state.page == ui::Page::Main);
        p.Scan(9);
        assert(p.state.page == ui::Page::Settings);
        p.Scan(9, 3000);
        assert(p.state.page == ui::Page::Settings);
        p.Scan(first);
        p.Scan(9, 100);
        p.Scan(9, 2000);
        assert(p.state.page == ui::Page::Settings); // No repeat before full release.
        p.Scan(first);
        p.Scan(0);
        assert(!p.bank.channels[0].envelope.IsCycling());
        assert(p.bank.channels[0].level == .4f);
        AssertZero(p.bank);
        p.Settings();
        assert(p.state.page == ui::Page::Main);
        assert(p.bank.channels[0].level == .4f);
        p.Tap(0); // Ordinary controls work again after the chord releases.
        assert(p.bank.channels[0].envelope.GetStage() == Stage::Rise);
    }
    Panel short_hold;
    short_hold.bank.channels[0].level = .3f;
    short_hold.Scan(9);
    short_hold.Scan(9, ui::kSettingsHoldMs - 1);
    short_hold.Scan(1);
    short_hold.Scan(0);
    assert(short_hold.state.page == ui::Page::Main);
    assert(short_hold.bank.channels[0].level == .3f);
    AssertZero(short_hold.bank);

    Panel interrupted;
    interrupted.Scan(9);
    interrupted.Scan(9, 500);
    interrupted.Scan(1);
    interrupted.Scan(9);
    interrupted.Scan(9, 500);
    assert(interrupted.state.page == ui::Page::Main);
    interrupted.Scan(9, 400);
    assert(interrupted.state.page == ui::Page::Settings);

    Panel stalled;
    stalled.Scan(1, 1, false);
    stalled.Scan(9, 1, false);
    stalled.Scan(9, 900, false);
    stalled.Scan(8, 1, false);
    stalled.Scan(0, 1, false);
    stalled.Flush();
    assert(stalled.state.page == ui::Page::Settings);
    AssertZero(stalled.bank);
    stalled.Flush();
    assert(stalled.state.page == ui::Page::Settings);

    Panel wrapped;
    wrapped.now = UINT32_MAX - 600;
    wrapped.Settings();
    assert(wrapped.state.page == ui::Page::Settings);
}

static void TestChannelsAndControls()
{
    Panel p;
    for(unsigned channel = 0; channel < 4; ++channel)
    {
        p.Button(channel);
        assert(p.state.channel == channel && p.state.page == ui::Page::Main);
        AssertZero(p.bank); // B1..B4 never trigger, toggle mode or open settings.
        assert(p.bank.channels[channel].curve == CurveType::Linear);
        p.Rotate(0, 1 + channel);
        p.Rotate(1, -1 - int(channel));
        p.Rotate(2, 1 + channel);
        p.Rotate(3, -1 - int(channel));
    }
    for(unsigned channel = 0; channel < 4; ++channel)
    {
        p.Button(channel);
        auto& voice = p.bank.channels[channel];
        assert(std::fabs(voice.rise - (.7f + .02f * (channel + 1))) < .00001f);
        assert(std::fabs(voice.level - (1.f - .02f * (channel + 1))) < .00001f);
    }
    p.Rotate(0, INT32_MAX);
    p.Rotate(1, INT32_MIN);
    assert(p.bank.channels[3].rise == 1 && p.bank.channels[3].fall == 0);
    p.Tap(2);
    p.Tap(3);
    assert(p.bank.channels[3].symmetry == .5f && p.bank.channels[3].level == 1);
    p.Tap(1, 1000); // E2 hold is no longer a menu shortcut.
    assert(p.state.page == ui::Page::Main && p.bank.channels[3].curve == CurveType::Exponential);
    p.Tap(0, ui::kLongPressMs);
    assert(p.bank.channels[3].envelope.IsCycling());
    for(int i = 0; i < 20; ++i) p.bank.Process();
    p.Button(0);
    assert(p.bank.channels[3].envelope.IsCycling());
    p.Tap(0);
    assert(p.bank.channels[0].envelope.GetStage() == Stage::Rise);
    p.Settings();
    const float before = p.bank.channels[3].envelope.GetValue();
    p.bank.Process();
    assert(p.bank.channels[3].envelope.GetValue() > before); // Settings keep voices running.

    Panel stale;
    stale.Scan(1);
    stale.Button(2);
    stale.Scan(0, 1000);
    assert(!stale.bank.channels[2].envelope.IsCycling());
    AssertZero(stale.bank); // A held encoder cannot act on the newly selected voice.
    stale.Tap(0);
    assert(stale.bank.channels[2].envelope.GetStage() == Stage::Rise);
    stale.Scan(2);
    stale.Button(1);
    stale.Scan(0, 40);
    assert(stale.bank.channels[1].curve == CurveType::Linear);
}

static void TestSettingsPages()
{
    Panel p;
    p.Settings();
    p.Rotate(1, -1);
    assert(p.state.menu_item == ui::MenuItem::Back);
    p.Open(ui::MenuItem::CvTarget);
    assert(p.state.page == ui::Page::CvTarget);
    p.Rotate(1, 1);
    assert(p.bank.channels[0].cv_target == adlfo::CvTarget::Rise);
    p.Button(3);
    assert(p.state.page == ui::Page::CvTarget);
    assert(p.bank.channels[3].cv_target == adlfo::CvTarget::Time);
    p.Rotate(1, -2);
    assert(p.bank.channels[3].cv_target == adlfo::CvTarget::Level);
    assert(p.bank.channels[0].cv_target == adlfo::CvTarget::Rise);
    p.Tap(1);
    p.Open(ui::MenuItem::Controls);
    assert(p.state.page == ui::Page::Controls);
    p.Button(1);
    assert(p.state.page == ui::Page::Controls && p.state.channel == 1);
    p.Tap(1);
    p.Open(ui::MenuItem::Encoders);
    assert(p.state.page == ui::Page::Encoders);
    const auto previous_curve = p.bank.channels[1].curve;
    for(unsigned i = 0; i < 4; ++i)
    {
        p.Rotate(i, -25);
        assert(p.state.encoder_values[i] == -25);
        p.Tap(i);
        assert(p.state.encoder_values[i] == 0 && p.state.page == ui::Page::Encoders);
    }
    assert(p.bank.channels[1].curve == previous_curve);
    p.Rotate(0, INT32_MAX);
    assert(p.state.encoder_values[0] == 9999);
    p.Rotate(0, INT32_MIN);
    assert(p.state.encoder_values[0] == -9999);
    p.Settings();
    assert(p.state.page == ui::Page::Settings);
    p.Open(ui::MenuItem::Back);
    assert(p.state.page == ui::Page::Main);
}

static void TestOutputSafety()
{
    for(bool exit_with_chord : {false, true})
    {
        Panel p;
        p.bank.channels[0].envelope.SetCycling(true);
        p.bank.channels[2].envelope.SetCycling(true);
        p.Settings();
        p.Open(ui::MenuItem::OutputTest);
        assert(p.state.page == ui::Page::OutputTest);
        AssertZero(p.bank);
        for(unsigned channel = 0; channel < 4; ++channel)
        {
            p.Button(channel);
            assert(p.state.channel == channel && p.state.page == ui::Page::OutputTest);
            assert(p.state.test_volts == 0);
            AssertZero(p.bank);
            p.Rotate(0, 5); // Only the buttons select an output.
            assert(p.state.channel == channel && p.state.test_volts == 0);
            for(unsigned volts = 1; volts <= 2; ++volts)
            {
                p.Rotate(1, 1);
                const auto codes = p.bank.Process();
                for(unsigned i = 0; i < 4; ++i)
                    assert(codes[i] == (i == channel ? volts * 2000 : 0));
            }
        }
        p.Rotate(1, INT32_MAX);
        assert(p.state.test_volts == 2);
        p.Rotate(1, INT32_MIN);
        assert(p.state.test_volts == 0);
        AssertZero(p.bank);
        p.Rotate(1, 2);
        p.Button(3); // Re-selecting the same output also zeros its test voltage.
        AssertZero(p.bank);
        p.Rotate(1, 2);
        if(exit_with_chord) p.Settings();
        else p.Tap(1);
        assert(p.state.page == ui::Page::Settings && p.state.test_volts == 0);
        AssertZero(p.bank);
        for(const auto& voice : p.bank.channels) assert(!voice.envelope.IsCycling());
        p.Settings();
        p.Tap(0);
        assert(p.bank.channels[3].envelope.GetStage() == Stage::Rise);
    }
}

static void TestRendering()
{
    Canvas d;
    for(float time : {.005f, .15f, .9994f, .9995f, 1.f, 9.94f, 9.95f, 10.f})
        for(float value : {0.f, .5f, 1.f})
            for(unsigned ch = 1; ch <= 4; ++ch)
                for(bool cycling : {false, true})
                {
                    ui::DrawMain(d, time, time, value, value, value, cycling, "EXP", ch);
                    assert(d.text[0].text == "CH " + std::to_string(ch) && d.text[0].width == 11);
                }
    for(unsigned ch = 1; ch <= 4; ++ch)
    {
        for(unsigned i = 0; i < unsigned(ui::MenuItem::Count); ++i)
            ui::DrawSettings(d, static_cast<ui::MenuItem>(i), ch);
        for(unsigned target = 0; target < unsigned(adlfo::CvTarget::Count); ++target)
            for(bool enabled : {false, true})
                ui::DrawCvTarget(d, ch, static_cast<adlfo::CvTarget>(target), 1, enabled);
        for(unsigned volts = 0; volts <= 2; ++volts) ui::DrawOutputTest(d, ch, volts);
    }
    const int32_t values[] = {-9999, 9999, 0, -1};
    std::array<ui::Events, 4> events{};
    for(unsigned mask = 0; mask < 256; ++mask)
    {
        for(unsigned i = 0; i < 4; ++i)
        {
            events[i].down = (mask >> i) & 1;
            events[i].button_down = (mask >> (i + 4)) & 1;
        }
        ui::DrawEncoders(d, values, events, 4);
    }
    ui::DrawMain(d, .15f, 1.2f, .65f, .5f, 1.f, true, "LOG", 2);
    d.Save("/tmp/adlfo-main.pbm");
    ui::DrawSettings(d, ui::MenuItem::Encoders, 2);
    d.Save("/tmp/adlfo-settings.pbm");
    events = {};
    events[1].button_down = true;
    events[2].down = true;
    ui::DrawEncoders(d, values, events, 2);
    d.Save("/tmp/adlfo-encoders.pbm");
    ui::DrawCvTarget(d, 2, adlfo::CvTarget::Time, .42f, true);
    d.Save("/tmp/adlfo-cv.pbm");
    ui::DrawOutputTest(d, 2, 1);
    d.Save("/tmp/adlfo-output.pbm");
    ui::DrawControls(d);
    d.Save("/tmp/adlfo-controls.pbm");
}

int main()
{
    TestSettingsGesture();
    TestChannelsAndControls();
    TestSettingsPages();
    TestOutputSafety();
    TestRendering();
}

