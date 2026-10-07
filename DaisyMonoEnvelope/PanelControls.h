#pragma once

#include "daisy_seed.h"
#include <array>
#include "EncoderView.h"

namespace panel
{
constexpr size_t kColumns = 4;
constexpr size_t kJacksPerColumn = 3;

// Physical positions only; electrical jack roles belong to the I/O backend.
struct ColumnPins
{
    daisy::Pin encoder_a, encoder_b, encoder_switch, button;
};

// B1/B2 scambiati per corrispondere al cablaggio del pannello verificato dall'utente.
constexpr ColumnPins kPins[kColumns] = {
    {daisy::seed::D0, daisy::seed::D1, daisy::seed::D2, daisy::seed::D25},
    {daisy::seed::D3, daisy::seed::D4, daisy::seed::D5, daisy::seed::D24},
    {daisy::seed::D7, daisy::seed::D8, daisy::seed::D9, daisy::seed::D26},
    {daisy::seed::D10, daisy::seed::D13, daisy::seed::D14, daisy::seed::D27},
};

struct Events
{
    int32_t delta = 0;
    uint32_t clicks = 0;
    uint32_t button_presses = 0;
    bool pressed = false, released = false, down = false, button_down = false;
    uint32_t held_ms = 0;
};

struct Frame
{
    std::array<Events, kColumns> events;
    ui::Shortcut shortcut;
};

class Controls
{
  public:
    void Init()
    {
        for(size_t i = 0; i < kColumns; ++i)
        {
            encoders_[i].Init(kPins[i].encoder_a, kPins[i].encoder_b,
                              kPins[i].encoder_switch);
            buttons_[i].Init(kPins[i].button);
        }
    }

    // Called only by the 1 kHz control interrupt.
    void Scan()
    {
        for(size_t i = 0; i < kColumns; ++i)
        {
            auto& e = encoders_[i];
            auto& b = buttons_[i];
            auto& pending = pending_[i];
            e.Debounce();
            b.Debounce();
            // E3: sul pannello attuale la rotazione a destra deve decrementare.
            // Possibile ordine A/B invertito nel cablaggio (non verificato):
            // compensiamo qui il verso, sia per i parametri sia per il test.
            const int32_t increment = e.Increment();
            pending.delta += (i == 2) ? -increment : increment;
            pending.pressed |= e.RisingEdge();
            pending.released |= e.FallingEdge();
            pending.clicks += e.RisingEdge() ? 1 : 0;
            pending.button_presses += b.RisingEdge() ? 1 : 0;
            pending.down = e.Pressed();
            pending.button_down = b.Pressed();
            pending.held_ms = static_cast<uint32_t>(e.TimeHeldMs());
        }
        chord_.Scan(pending_[0].down, pending_[3].down);
    }

    Frame Consume()
    {
        daisy::ScopedIrqBlocker lock;
        Frame result{pending_, chord_.Consume()};
        for(auto& e : pending_)
        {
            e.delta = 0;
            e.clicks = e.button_presses = 0;
            e.pressed = e.released = false;
        }
        return result;
    }

  private:
    ui::Chord chord_;
    daisy::Encoder encoders_[kColumns];
    daisy::Switch buttons_[kColumns];
    std::array<Events, kColumns> pending_{};
};
} // namespace panel
