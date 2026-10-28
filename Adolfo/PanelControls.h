#pragma once

#include "daisy_seed.h"
#include <array>
#include "UiInput.h"

namespace panel
{
constexpr size_t kColumns = ui::kEncoders;

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
        const uint32_t now = daisy::System::GetNow();
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
            presses_[i].Scan(e.RisingEdge(), e.FallingEdge(), now, pending);
            pending.button_presses += b.RisingEdge() ? 1 : 0;
            pending.button_down = b.Pressed();
        }
        chord_.Scan(pending_[0].down, pending_[3].down, now);
    }

    ui::Frame Consume()
    {
        daisy::ScopedIrqBlocker lock;
        ui::Frame result{pending_, chord_.Consume()};
        for(auto& e : pending_)
        {
            e.delta = 0;
            e.taps = e.long_presses = e.button_presses = 0;
        }
        return result;
    }

  private:
    ui::Chord chord_;
    ui::Press presses_[kColumns];
    daisy::Encoder encoders_[kColumns];
    daisy::Switch buttons_[kColumns];
    std::array<ui::Events, kColumns> pending_{};
};
} // namespace panel
