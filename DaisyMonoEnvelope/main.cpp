#include <cmath>
#include <cstdint>
#include <cstdio>

#include "daisy_seed.h"
#include "daisysp.h"
#include "dev/oled_ssd130x.h"

#include "EnvelopeGenerator.h"
#include "PanelControls.h"
#include "OledUi.h"

using namespace daisy;

namespace HardwarePins
{
constexpr auto TriggerInput = seed::D6;

constexpr auto CvInput       = seed::A1; // Alias analogico di D16.

constexpr auto I2cScl = seed::D11;
constexpr auto I2cSda = seed::D12;

// Il DAC hardware non richiede una pin_config: Channel ONE seleziona PA4.
constexpr auto ModulationOut = seed::D23; // A8 / PA4 / DAC OUT 1.
} // namespace HardwarePins

namespace Settings
{
constexpr uint32_t kEnvelopeUpdateRateHz = 10000;
constexpr float kEnvelopeUpdateRate
    = static_cast<float>(kEnvelopeUpdateRateHz);
constexpr uint32_t kEncoderScanRateHz = 1000;
constexpr uint32_t kEncoderScanDivider
    = kEnvelopeUpdateRateHz / kEncoderScanRateHz;
constexpr float kMinimumTimeSeconds = 0.005f;
constexpr float kMaximumTimeSeconds = 10.0f;
constexpr float kInitialTimeNormalized = 0.45f;
constexpr float kEncoderStep = 0.02f;

// Escursione massima di SYMMETRY nel dominio logaritmico normalizzato.
constexpr float kSymmetryDepth = 0.35f;
constexpr float kCvSmoothingAmount = 0.02f;

// Il partitore 100k/47k produce circa 3,20 V con 10 V al jack:
// GetFloat() legge quindi circa 0,97 alla massima tensione prevista.
constexpr float kCvAdcFullScale = 0.97f;
constexpr float kCvTimeDepth = 0.35f;

constexpr uint32_t kDisplayPeriodMs = 150; // Lascia tempo ai controlli a 100 kHz.
constexpr float kLongPressTimeMs = 750.0f;

constexpr uint8_t kOledI2cAddress = 0x3C;

constexpr uint16_t kDacMaximumCode = 4095;

static_assert(kEnvelopeUpdateRateHz % kEncoderScanRateHz == 0,
              "La frequenza encoder deve dividere quella dell'inviluppo");
} // namespace Settings

enum class AdcChannel : uint8_t
{
    TimeCv = 0,
    Count
};

// Il transport SSD1306 standard della versione locale di libDaisy invia ogni
// byte con una transazione separata. Questo transport mantiene lo stesso
// driver, ma invia una pagina da 128 byte per transazione: il refresh OLED non
// monopolizza più il loop dei controlli.
class BufferedSSD1306I2CTransport
{
  public:
    struct Config
    {
        Config()
        {
            i2c_config.periph = I2CHandle::Config::Peripheral::I2C_1;
            i2c_config.speed = I2CHandle::Config::Speed::I2C_100KHZ;
            i2c_config.mode = I2CHandle::Config::Mode::I2C_MASTER;
            i2c_config.pin_config.scl = HardwarePins::I2cScl;
            i2c_config.pin_config.sda = HardwarePins::I2cSda;
            i2c_address = Settings::kOledI2cAddress;
        }

        I2CHandle::Config i2c_config;
        uint8_t i2c_address;
    };

    void Init(const Config& config)
    {
        i2c_address_ = config.i2c_address;
        i2c_.Init(config.i2c_config);
    }

    void SendCommand(uint8_t command)
    {
        uint8_t packet[2] = {0x00, command};
        i2c_.TransmitBlocking(i2c_address_, packet, 2, 100);
    }

    void SendData(uint8_t* data, size_t size)
    {
        constexpr size_t kMaximumPageSize = 128;
        if(size > kMaximumPageSize)
            return;

        uint8_t packet[kMaximumPageSize + 1];
        packet[0] = 0x40;
        for(size_t index = 0; index < size; ++index)
            packet[index + 1] = data[index];

        i2c_.TransmitBlocking(
            i2c_address_, packet, static_cast<uint16_t>(size + 1), 100);
    }

  private:
    I2CHandle i2c_;
    uint8_t i2c_address_ = Settings::kOledI2cAddress;
};

using BufferedSSD1306Driver
    = SSD130xDriver<128, 64, BufferedSSD1306I2CTransport>;
using Display = OledDisplay<BufferedSSD1306Driver>;

enum class ScreenPage
{
    Main,
    Menu,
    ControlsHelp,
    EncoderDebug
};

enum class MenuItem : uint8_t
{
    Controls = 0,
    EncoderDebug,
    Back,
    Count
};

struct EncoderSnapshot
{
    int32_t encoder1_delta = 0;
    int32_t encoder2_delta = 0;

    bool encoder1_pressed_event = false;
    bool encoder1_released_event = false;
    bool encoder2_pressed_event = false;
    bool encoder2_released_event = false;

    bool encoder1_down = false;
    bool encoder2_down = false;
    uint32_t encoder1_held_ms = 0;
    uint32_t encoder2_held_ms = 0;
};

struct Application
{
    DaisySeed        hardware;
    panel::Controls  panel_controls;
    std::array<panel::Events, panel::kColumns> panel_events{};
    int32_t panel_positions[panel::kColumns]{};
    float output_level = 1.0f;
    ui::EncoderView encoder_view;
    ui::Shortcut shortcut;
    bool encoder4_click_armed = false;
    GateIn            trigger_input;
    Display          display;
    TimerHandle      envelope_timer;
    EnvelopeGenerator envelope;

    float rise_normalized = Settings::kInitialTimeNormalized;
    float fall_normalized = Settings::kInitialTimeNormalized;
    float smoothed_pot = 0.5f;
    float smoothed_cv = 0.0f;
    float normalized_cv = 0.0f;
    float effective_rise_seconds = 0.1f;
    float effective_fall_seconds = 0.1f;

    CurveType curve = CurveType::Logarithmic;
    bool cycling = false;
    bool encoder1_long_press_handled = false;
    bool encoder2_long_press_handled = false;
    bool encoder1_button_down = false;
    bool encoder2_button_down = false;
    ScreenPage screen_page = ScreenPage::Main;
    MenuItem selected_menu_item = MenuItem::Controls;

    int32_t encoder1_position = 0;
    int32_t encoder2_position = 0;
    int32_t last_encoder1_delta = 0;
    int32_t last_encoder2_delta = 0;

    uint32_t encoder_scan_divider = 0;
    uint32_t last_display_update_ms = 0;
};

// Unico stato globale: serve al callback hardware e mantiene insieme tutte le
// periferiche e tutte le variabili applicative.
Application app;

float TimeFromNormalized(float normalized)
{
    normalized = daisysp::fclamp(normalized, 0.0f, 1.0f);
    const float ratio = Settings::kMaximumTimeSeconds
                        / Settings::kMinimumTimeSeconds;
    return Settings::kMinimumTimeSeconds * std::pow(ratio, normalized);
}

const char* CurveName(CurveType curve)
{
    switch(curve)
    {
        case CurveType::Logarithmic: return "LOG";
        case CurveType::Linear: return "LIN";
        case CurveType::Exponential: return "EXP";
    }

    return "?";
}

void CycleCurve(Application& application)
{
    switch(application.curve)
    {
        case CurveType::Logarithmic:
            application.curve = CurveType::Linear;
            break;
        case CurveType::Linear:
            application.curve = CurveType::Exponential;
            break;
        case CurveType::Exponential:
            application.curve = CurveType::Logarithmic;
            break;
    }

    // Il timer può leggere l'inviluppo in qualsiasi istante; il breve blocco
    // IRQ rende atomico l'aggiornamento dei suoi parametri.
    ScopedIrqBlocker irq_blocker;
    application.envelope.SetCurve(application.curve);
}

void SetCycling(Application& application, bool enabled)
{
    application.cycling = enabled;
    ScopedIrqBlocker irq_blocker;
    application.envelope.SetCycling(enabled);
}

void TriggerEnvelope(Application& application)
{
    ScopedIrqBlocker irq_blocker;
    application.envelope.Trigger();
}

void MoveMenuSelection(Application& application, int32_t increment)
{
    constexpr int32_t kMenuItemCount
        = static_cast<int32_t>(MenuItem::Count);
    int32_t selection
        = static_cast<int32_t>(application.selected_menu_item) + increment;
    selection %= kMenuItemCount;
    if(selection < 0)
        selection += kMenuItemCount;

    application.selected_menu_item = static_cast<MenuItem>(selection);
}

void OpenSelectedMenuItem(Application& application)
{
    switch(application.selected_menu_item)
    {
        case MenuItem::Controls:
            application.screen_page = ScreenPage::ControlsHelp;
            break;
        case MenuItem::EncoderDebug:
            application.screen_page = ScreenPage::EncoderDebug;
            break;
        case MenuItem::Back:
            application.screen_page = ScreenPage::Main;
            break;
        case MenuItem::Count:
            break;
    }
}

void UpdateEnvelopeTimes(Application& application)
{
    // Il potenziometro sposta Rise e Fall in direzioni opposte nel dominio
    // normalizzato. Al centro (symmetry == 0) i tempi base non cambiano.
    const float symmetry = (application.smoothed_pot - 0.5f) * 2.0f;
    const float time_cv_offset
        = application.normalized_cv * Settings::kCvTimeDepth;
    const float rise_position = daisysp::fclamp(
        application.rise_normalized + time_cv_offset
            + symmetry * Settings::kSymmetryDepth,
        0.0f,
        1.0f);
    const float fall_position = daisysp::fclamp(
        application.fall_normalized + time_cv_offset
            - symmetry * Settings::kSymmetryDepth,
        0.0f,
        1.0f);

    application.effective_rise_seconds = TimeFromNormalized(rise_position);
    application.effective_fall_seconds = TimeFromNormalized(fall_position);

    ScopedIrqBlocker irq_blocker;
    application.envelope.SetRiseTime(application.effective_rise_seconds);
    application.envelope.SetFallTime(application.effective_fall_seconds);
}

void ScanEncodersFromTimer(Application& application)
{
    application.panel_controls.Scan();
}

EncoderSnapshot ConsumeEncoderSnapshot(Application& application)
{
    const auto frame = application.panel_controls.Consume();
    application.panel_events = frame.events;
    application.shortcut = frame.shortcut;
    const auto& first = application.panel_events[0];
    const auto& second = application.panel_events[1];
    EncoderSnapshot snapshot;
    snapshot.encoder1_delta = first.delta;
    snapshot.encoder2_delta = second.delta;
    snapshot.encoder1_pressed_event = first.pressed;
    snapshot.encoder2_pressed_event = second.pressed;
    snapshot.encoder1_released_event = first.released;
    snapshot.encoder2_released_event = second.released;
    snapshot.encoder1_down = first.down;
    snapshot.encoder2_down = second.down;
    snapshot.encoder1_held_ms = first.held_ms;
    snapshot.encoder2_held_ms = second.held_ms;
    return snapshot;
}

void ProcessControls(Application& application)
{
    const EncoderSnapshot encoders = ConsumeEncoderSnapshot(application);

    const float raw_cv = daisysp::fclamp(
        application.hardware.adc.GetFloat(
            static_cast<uint8_t>(AdcChannel::TimeCv)),
        0.0f,
        1.0f);
    application.smoothed_cv += Settings::kCvSmoothingAmount
                               * (raw_cv - application.smoothed_cv);
    application.normalized_cv = daisysp::fclamp(
        application.smoothed_cv / Settings::kCvAdcFullScale, 0.0f, 1.0f);
    UpdateEnvelopeTimes(application);

    if(application.encoder_view.Process(application.panel_events, application.shortcut))
    {
        application.encoder1_long_press_handled = true;
        application.encoder2_long_press_handled = true;
        application.encoder4_click_armed = false;
        return;
    }

    // Mantiene visibile l'ultimo movimento non nullo tra due refresh OLED.
    if(encoders.encoder1_delta != 0)
    {
        application.last_encoder1_delta = encoders.encoder1_delta;
    }
    if(encoders.encoder2_delta != 0)
    {
        application.last_encoder2_delta = encoders.encoder2_delta;
    }
    application.encoder1_position += encoders.encoder1_delta;
    application.encoder2_position += encoders.encoder2_delta;
    application.encoder1_button_down = encoders.encoder1_down;
    application.encoder2_button_down = encoders.encoder2_down;

    if(application.screen_page == ScreenPage::Main)
    {
        application.rise_normalized = daisysp::fclamp(
            application.rise_normalized
                + static_cast<float>(encoders.encoder1_delta)
                      * Settings::kEncoderStep,
            0.0f,
            1.0f);
        application.fall_normalized = daisysp::fclamp(
            application.fall_normalized
                + static_cast<float>(encoders.encoder2_delta)
                      * Settings::kEncoderStep,
            0.0f,
            1.0f);
    }
    else if(application.screen_page == ScreenPage::Menu
            && encoders.encoder2_delta != 0)
    {
        MoveMenuSelection(application, encoders.encoder2_delta);
    }

    for(size_t i = 0; i < panel::kColumns; ++i)
        application.panel_positions[i] += application.panel_events[i].delta;

    if(application.screen_page == ScreenPage::Main)
    {
        application.smoothed_pot = daisysp::fclamp(
            application.smoothed_pot + application.panel_events[2].delta * Settings::kEncoderStep,
            0.0f, 1.0f);
        if(application.panel_events[2].clicks)
            application.smoothed_pot = 0.5f;
        float level = daisysp::fclamp(
            application.output_level + application.panel_events[3].delta * Settings::kEncoderStep,
            0.0f, 1.0f);
        if(application.panel_events[3].pressed)
            application.encoder4_click_armed = true;
        if(application.panel_events[3].released)
        {
            if(application.encoder4_click_armed) level = 1.0f;
            application.encoder4_click_armed = false;
        }
        {
            ScopedIrqBlocker lock;
            application.output_level = level;
        }
    }
    if(application.panel_events[0].button_presses)
        TriggerEnvelope(application);
    if(application.panel_events[1].button_presses & 1)
        SetCycling(application, !application.cycling);
    for(uint32_t i = 0; i < application.panel_events[2].button_presses % 3; ++i)
        CycleCurve(application);
    if(application.panel_events[3].button_presses & 1)
        application.screen_page = application.screen_page == ScreenPage::Main
            ? ScreenPage::Menu : ScreenPage::Main;

    // Encoder 1: una pressione breve viene riconosciuta al rilascio. In questo
    // modo la stessa pressione può diventare lunga senza lanciare prima l'AD.
    if(encoders.encoder1_pressed_event)
        application.encoder1_long_press_handled = false;

    if(application.screen_page == ScreenPage::Main && encoders.encoder1_down
       && !application.encoder1_long_press_handled
       && encoders.encoder1_held_ms >= Settings::kLongPressTimeMs)
    {
        SetCycling(application, !application.cycling);
        application.encoder1_long_press_handled = true;
    }

    if(application.screen_page == ScreenPage::Main
       && encoders.encoder1_released_event
       && !application.encoder1_long_press_handled && !application.cycling)
    {
        TriggerEnvelope(application);
    }

    // Encoder 2: nella pagina principale il click cambia curva e la pressione
    // lunga apre il menu. Nel menu ruota/seleziona; nelle sottopagine il click
    // torna al menu. La pressione lunga chiude sempre la UI e torna a Main.
    if(encoders.encoder2_pressed_event)
        application.encoder2_long_press_handled = false;

    if(encoders.encoder2_down && !application.encoder2_long_press_handled
       && encoders.encoder2_held_ms >= Settings::kLongPressTimeMs)
    {
        application.screen_page
            = application.screen_page == ScreenPage::Main
                  ? ScreenPage::Menu
                  : ScreenPage::Main;
        application.encoder2_long_press_handled = true;
    }

    if(encoders.encoder2_released_event
       && !application.encoder2_long_press_handled)
    {
        switch(application.screen_page)
        {
            case ScreenPage::Main:
                CycleCurve(application);
                break;
            case ScreenPage::Menu:
                OpenSelectedMenuItem(application);
                break;
            case ScreenPage::ControlsHelp:
            case ScreenPage::EncoderDebug:
                application.screen_page = ScreenPage::Menu;
                break;
        }
    }
}

void InitDisplay(Application& application)
{
    // Tutta la configurazione SSD1306 resta confinata qui per poter cambiare
    // facilmente driver se il modulo reale usa un controller diverso.
    Display::Config config;
    auto& i2c = config.driver_config.transport_config.i2c_config;
    i2c.periph = I2CHandle::Config::Peripheral::I2C_1;
    i2c.mode = I2CHandle::Config::Mode::I2C_MASTER;
    i2c.speed = I2CHandle::Config::Speed::I2C_100KHZ;
    i2c.pin_config.scl = HardwarePins::I2cScl;
    i2c.pin_config.sda = HardwarePins::I2cSda;
    config.driver_config.transport_config.i2c_address
        = Settings::kOledI2cAddress;

    // Stessi pin e velocita del test OLED verificato sulla breadboard.
    System::Delay(200);
    I2CHandle probe;
    probe.Init(i2c);
    const uint8_t addresses[] = {Settings::kOledI2cAddress, 0x3D};
    for(uint8_t address : addresses)
    {
        uint8_t nop[] = {0x00, 0xE3};
        if(probe.TransmitBlocking(address, nop, sizeof(nop), 20)
           == I2CHandle::Result::OK)
        {
            config.driver_config.transport_config.i2c_address = address;
            break;
        }
    }

    application.display.Init(config);
    application.display.Fill(false);
    application.display.Update();
}

void WriteDisplayLine(Display& display, uint8_t row, const char* text)
{
    constexpr uint8_t kLineHeight = 10;
    display.SetCursor(0, row * kLineHeight);
    display.WriteString(text, Font_6x8, true);
}

void WriteDisplayText(Display& display,
                      uint8_t  x,
                      uint8_t  y,
                      const char* text)
{
    display.SetCursor(x, y);
    display.WriteString(text, Font_6x8, true);
}

void UpdateMenuDisplay(Application& application)
{
    constexpr const char* kMenuLabels[] = {
        "CONTROLS",
        "ENC DEBUG",
        "BACK",
    };

    application.display.Fill(false);
    WriteDisplayText(application.display, 52, 0, "MENU");
    application.display.DrawLine(0, 10, 127, 10, true);

    for(uint8_t index = 0;
        index < static_cast<uint8_t>(MenuItem::Count);
        ++index)
    {
        const uint8_t y = static_cast<uint8_t>(14 + index * 13);
        if(index
           == static_cast<uint8_t>(application.selected_menu_item))
        {
            application.display.DrawRect(1, y - 2, 126, y + 9, true);
            application.display.DrawLine(5, y + 1, 9, y + 4, true);
            application.display.DrawLine(9, y + 4, 5, y + 7, true);
        }
        WriteDisplayText(application.display, 14, y, kMenuLabels[index]);
    }

    WriteDisplayText(application.display, 4, 55, "E2 ROT/TAP  HLD EXIT");
    application.display.Update();
}

void UpdateControlsHelpDisplay(Application& application)
{
    application.display.Fill(false);
    WriteDisplayLine(application.display, 0, "E1 RISE  E2 FALL");
    WriteDisplayLine(application.display, 1, "E3 SYM   E4 LEVEL");
    WriteDisplayLine(application.display, 2, "B1 TRIG  B2 AD/LFO");
    WriteDisplayLine(application.display, 3, "B3 CURVE B4 MENU");
    WriteDisplayLine(application.display, 4, "E3/E4 TAP: RESET");
    WriteDisplayLine(application.display, 5, "E2 TAP: BACK");
    application.display.Update();
}

void UpdateEncoderDebugDisplay(Application& application)
{
    char line[22];
    application.display.Fill(false);
    WriteDisplayLine(application.display, 0, "ENC POS / SW / BUTTON");
    for(size_t i = 0; i < panel::kColumns; ++i)
    {
        std::snprintf(line, sizeof(line), "%u:%ld S:%u B:%u",
                      static_cast<unsigned>(i + 1),
                      static_cast<long>(application.panel_positions[i]),
                      application.panel_events[i].down ? 1u : 0u,
                      application.panel_events[i].button_down ? 1u : 0u);
        WriteDisplayLine(application.display, i + 1, line);
    }
    WriteDisplayLine(application.display, 5, "E2 TAP: BACK");
    application.display.Update();
}

void UpdateMainDisplay(Application& application)
{
    float output_value;
    {
        ScopedIrqBlocker irq_blocker;
        output_value = application.envelope.GetValue() * application.output_level;
    }

    ui::DrawMain(application.display,
                 application.effective_rise_seconds, application.effective_fall_seconds,
                 output_value, application.smoothed_pot, application.output_level,
                 application.normalized_cv, application.cycling, CurveName(application.curve));
    application.display.Update();
}

void UpdateDisplay(Application& application)
{
    if(application.encoder_view.active)
    {
        bool down[4], buttons[4];
        for(unsigned i = 0; i < 4; ++i)
        {
            down[i] = application.panel_events[i].down;
            buttons[i] = application.panel_events[i].button_down;
        }
        ui::DrawEncoders(application.display, application.encoder_view.values, down, buttons);
        application.display.Update();
        return;
    }
    switch(application.screen_page)
    {
        case ScreenPage::Main:
            UpdateMainDisplay(application);
            break;
        case ScreenPage::Menu:
            UpdateMenuDisplay(application);
            break;
        case ScreenPage::ControlsHelp:
            UpdateControlsHelpDisplay(application);
            break;
        case ScreenPage::EncoderDebug:
            UpdateEncoderDebugDisplay(application);
            break;
    }
}

void EnvelopeTimerCallback(void* context)
{
    auto* application = static_cast<Application*>(context);

    // L'inviluppo resta a 10 kHz; ogni dieci tick gli encoder vengono letti a
    // 1 kHz, indipendentemente dai trasferimenti OLED del loop principale.
    ++application->encoder_scan_divider;
    if(application->encoder_scan_divider >= Settings::kEncoderScanDivider)
    {
        application->encoder_scan_divider = 0;
        ScanEncodersFromTimer(*application);
    }

    // GateIn usa il circuito BJT invertente documentato in ../wiring/SCHEMI.md.
    // In AD avvia da Idle; in LFO riallinea immediatamente il ciclo a zero.
    if(application->trigger_input.Trig())
        application->envelope.Trigger();

    const float value = daisysp::fclamp(
        application->envelope.Process() * application->output_level,
        0.0f,
        1.0f);
    const uint16_t dac_code = static_cast<uint16_t>(
        value * static_cast<float>(Settings::kDacMaximumCode) + 0.5f);

    // DAC1 converte 0...4095 nel livello unipolare 0...VDDA (circa 3,3 V).
    application->hardware.dac.WriteValue(DacHandle::Channel::ONE, dac_code);
}

bool InitDacAndTimer(Application& application)
{
    (void)HardwarePins::ModulationOut; // Documenta il pin fisso scelto dal DAC1.

    DacHandle::Config dac_config;
    dac_config.bitdepth = DacHandle::BitDepth::BITS_12;
    dac_config.buff_state = DacHandle::BufferState::ENABLED;
    dac_config.mode = DacHandle::Mode::POLLING;
    dac_config.chn = DacHandle::Channel::ONE;
    dac_config.target_samplerate
        = static_cast<uint32_t>(Settings::kEnvelopeUpdateRate);

    if(application.hardware.dac.Init(dac_config) != DacHandle::Result::OK)
        return false;

    application.hardware.dac.WriteValue(DacHandle::Channel::ONE, 0);

    TimerHandle::Config timer_config;
    timer_config.periph = TimerHandle::Config::Peripheral::TIM_5;
    timer_config.dir = TimerHandle::Config::CounterDir::UP;
    timer_config.enable_irq = true;
    timer_config.period = 1;

    if(application.envelope_timer.Init(timer_config)
       != TimerHandle::Result::OK)
        return false;

    const uint32_t timer_ticks
        = application.envelope_timer.GetFreq()
          / static_cast<uint32_t>(Settings::kEnvelopeUpdateRate);
    if(timer_ticks < 2
       || application.envelope_timer.SetPeriod(timer_ticks - 1)
              != TimerHandle::Result::OK)
        return false;

    application.envelope_timer.SetCallback(EnvelopeTimerCallback, &application);
    return application.envelope_timer.Start() == TimerHandle::Result::OK;
}

[[noreturn]] void SignalInitializationError(Application& application)
{
    // Nessuna stampa o allocazione: un lampeggio rapido indica errore DAC/timer.
    while(true)
    {
        application.hardware.SetLed(true);
        System::Delay(100);
        application.hardware.SetLed(false);
        System::Delay(100);
    }
}

int main(void)
{
    app.hardware.Init();

    app.panel_controls.Init();
    app.trigger_input.Init(HardwarePins::TriggerInput);

    AdcChannelConfig
        adc_config[static_cast<uint8_t>(AdcChannel::Count)];
    adc_config[static_cast<uint8_t>(AdcChannel::TimeCv)]
        .InitSingle(HardwarePins::CvInput);
    app.hardware.adc.Init(
        adc_config, static_cast<uint8_t>(AdcChannel::Count));
    app.hardware.adc.Start();
    System::Delay(10);
    app.smoothed_cv = daisysp::fclamp(
        app.hardware.adc.GetFloat(static_cast<uint8_t>(AdcChannel::TimeCv)),
        0.0f,
        1.0f);
    app.normalized_cv = daisysp::fclamp(
        app.smoothed_cv / Settings::kCvAdcFullScale, 0.0f, 1.0f);

    app.envelope.Init(Settings::kEnvelopeUpdateRate);
    UpdateEnvelopeTimes(app);
    app.envelope.SetCurve(app.curve);

    InitDisplay(app);

    if(!InitDacAndTimer(app))
        SignalInitializationError(app);

    UpdateDisplay(app);
    app.last_display_update_ms = System::GetNow();

    while(true)
    {
        ProcessControls(app);

        const uint32_t now = System::GetNow();
        if(now - app.last_display_update_ms >= Settings::kDisplayPeriodMs)
        {
            app.last_display_update_ms = now;
            UpdateDisplay(app);
        }

        System::Delay(1);
    }
}
