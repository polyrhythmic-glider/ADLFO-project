#include <cmath>
#include <cstdint>
#include <cstdio>

#include "daisy_seed.h"
#include "daisysp.h"
#include "dev/oled_ssd130x.h"

#include "EnvelopeGenerator.h"

using namespace daisy;

namespace HardwarePins
{
// I nomi Dn sono quelli reali di libDaisy per Daisy Seed/Seed3.
constexpr auto Encoder1A      = seed::D0;
constexpr auto Encoder1B      = seed::D1;
constexpr auto Encoder1Switch = seed::D2;

constexpr auto Encoder2A      = seed::D3;
constexpr auto Encoder2B      = seed::D4;
constexpr auto Encoder2Switch = seed::D5;

constexpr auto TriggerInput = seed::D6;

constexpr auto Potentiometer = seed::A0; // Alias analogico di D15.
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
constexpr float kSmoothingAmount = 0.01f;
constexpr float kCvSmoothingAmount = 0.02f;

// Il partitore 100k/47k produce circa 3,20 V con 10 V al jack:
// GetFloat() legge quindi circa 0,97 alla massima tensione prevista.
constexpr float kCvAdcFullScale = 0.97f;
constexpr float kCvTimeDepth = 0.35f;

constexpr uint32_t kDisplayPeriodMs = 50; // Circa 20 aggiornamenti al secondo.
constexpr float kLongPressTimeMs = 750.0f;

constexpr uint8_t kOledI2cAddress = 0x3C;

constexpr float kOutputMaximum = 1.0f;
constexpr uint16_t kDacMaximumCode = 4095;

static_assert(kEnvelopeUpdateRateHz % kEncoderScanRateHz == 0,
              "La frequenza encoder deve dividere quella dell'inviluppo");
} // namespace Settings

enum class AdcChannel : uint8_t
{
    SymmetryPot = 0,
    TimeCv,
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
            i2c_config.speed = I2CHandle::Config::Speed::I2C_400KHZ;
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

// Mailbox scritta soltanto dall'interrupt a 1 kHz e consumata dal main loop
// con gli IRQ brevemente sospesi. Gli scatti non vanno persi durante il refresh.
struct EncoderMailbox
{
    volatile int32_t encoder1_delta = 0;
    volatile int32_t encoder2_delta = 0;

    volatile bool encoder1_pressed_event = false;
    volatile bool encoder1_released_event = false;
    volatile bool encoder2_pressed_event = false;
    volatile bool encoder2_released_event = false;

    volatile bool encoder1_down = false;
    volatile bool encoder2_down = false;
    volatile uint32_t encoder1_held_ms = 0;
    volatile uint32_t encoder2_held_ms = 0;
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
    Encoder          encoder1;
    Encoder          encoder2;
    GateIn            trigger_input;
    Display          display;
    TimerHandle      envelope_timer;
    EnvelopeGenerator envelope;
    EncoderMailbox   encoder_mailbox;

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
    application.encoder1.Debounce();
    application.encoder2.Debounce();

    application.encoder_mailbox.encoder1_delta
        += application.encoder1.Increment();
    application.encoder_mailbox.encoder2_delta
        += application.encoder2.Increment();

    if(application.encoder1.RisingEdge())
        application.encoder_mailbox.encoder1_pressed_event = true;
    if(application.encoder1.FallingEdge())
        application.encoder_mailbox.encoder1_released_event = true;
    if(application.encoder2.RisingEdge())
        application.encoder_mailbox.encoder2_pressed_event = true;
    if(application.encoder2.FallingEdge())
        application.encoder_mailbox.encoder2_released_event = true;

    application.encoder_mailbox.encoder1_down
        = application.encoder1.Pressed();
    application.encoder_mailbox.encoder2_down
        = application.encoder2.Pressed();
    application.encoder_mailbox.encoder1_held_ms
        = static_cast<uint32_t>(application.encoder1.TimeHeldMs());
    application.encoder_mailbox.encoder2_held_ms
        = static_cast<uint32_t>(application.encoder2.TimeHeldMs());
}

EncoderSnapshot ConsumeEncoderSnapshot(Application& application)
{
    EncoderSnapshot snapshot;
    ScopedIrqBlocker irq_blocker;

    snapshot.encoder1_delta = application.encoder_mailbox.encoder1_delta;
    snapshot.encoder2_delta = application.encoder_mailbox.encoder2_delta;
    snapshot.encoder1_pressed_event
        = application.encoder_mailbox.encoder1_pressed_event;
    snapshot.encoder1_released_event
        = application.encoder_mailbox.encoder1_released_event;
    snapshot.encoder2_pressed_event
        = application.encoder_mailbox.encoder2_pressed_event;
    snapshot.encoder2_released_event
        = application.encoder_mailbox.encoder2_released_event;
    snapshot.encoder1_down = application.encoder_mailbox.encoder1_down;
    snapshot.encoder2_down = application.encoder_mailbox.encoder2_down;
    snapshot.encoder1_held_ms = application.encoder_mailbox.encoder1_held_ms;
    snapshot.encoder2_held_ms = application.encoder_mailbox.encoder2_held_ms;

    application.encoder_mailbox.encoder1_delta = 0;
    application.encoder_mailbox.encoder2_delta = 0;
    application.encoder_mailbox.encoder1_pressed_event = false;
    application.encoder_mailbox.encoder1_released_event = false;
    application.encoder_mailbox.encoder2_pressed_event = false;
    application.encoder_mailbox.encoder2_released_event = false;

    return snapshot;
}

void ProcessControls(Application& application)
{
    const EncoderSnapshot encoders = ConsumeEncoderSnapshot(application);

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

    // Formula di smoothing intenzionalmente semplice e facile da regolare.
    const float raw_pot = daisysp::fclamp(
        application.hardware.adc.GetFloat(
            static_cast<uint8_t>(AdcChannel::SymmetryPot)),
        0.0f,
        1.0f);
    application.smoothed_pot
        += Settings::kSmoothingAmount * (raw_pot - application.smoothed_pot);

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
    i2c.speed = I2CHandle::Config::Speed::I2C_400KHZ;
    i2c.pin_config.scl = HardwarePins::I2cScl;
    i2c.pin_config.sda = HardwarePins::I2cSda;
    config.driver_config.transport_config.i2c_address
        = Settings::kOledI2cAddress;

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

void FormatTime(float seconds, char* destination, size_t destination_size)
{
    if(seconds < 1.0f)
    {
        const uint32_t milliseconds
            = static_cast<uint32_t>(seconds * 1000.0f + 0.5f);
        std::snprintf(destination,
                      destination_size,
                      "%lu ms",
                      static_cast<unsigned long>(milliseconds));
    }
    else
    {
        const uint32_t hundredths
            = static_cast<uint32_t>(seconds * 100.0f + 0.5f);
        std::snprintf(destination,
                      destination_size,
                      "%lu.%02lu s",
                      static_cast<unsigned long>(hundredths / 100),
                      static_cast<unsigned long>(hundredths % 100));
    }
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

void DrawEncoderIcon(Display& display, uint8_t center_x)
{
    // Freccia a due punte sopra una piccola manopola stilizzata.
    display.DrawLine(center_x - 13, 11, center_x + 13, 11, true);
    display.DrawLine(center_x - 13, 11, center_x - 9, 8, true);
    display.DrawLine(center_x - 13, 11, center_x - 9, 14, true);
    display.DrawLine(center_x + 13, 11, center_x + 9, 8, true);
    display.DrawLine(center_x + 13, 11, center_x + 9, 14, true);
    display.DrawCircle(center_x, 23, 8, true);
    display.DrawLine(center_x, 23, center_x + 4, 19, true);
}

void UpdateControlsHelpDisplay(Application& application)
{
    application.display.Fill(false);
    WriteDisplayText(application.display, 13, 0, "CONTROLS  E2=BACK");

    DrawEncoderIcon(application.display, 31);
    DrawEncoderIcon(application.display, 96);
    WriteDisplayText(application.display, 25, 32, "E1");
    WriteDisplayText(application.display, 90, 32, "E2");

    WriteDisplayText(application.display, 2, 40, "ROT:RISE");
    WriteDisplayText(application.display, 68, 40, "ROT:FALL");
    WriteDisplayText(application.display, 2, 48, "TAP:TRG");
    WriteDisplayText(application.display, 68, 48, "TAP:CUR");
    WriteDisplayText(application.display, 2, 56, "HLD:MODE");
    WriteDisplayText(application.display, 68, 56, "HLD:MENU");

    application.display.Update();
}

void UpdateEncoderDebugDisplay(Application& application)
{
    char line[22];
    application.display.Fill(false);

    WriteDisplayLine(application.display, 0, "DEBUG ENCODERS");

    std::snprintf(line,
                  sizeof(line),
                  "E1 pos: %ld",
                  static_cast<long>(application.encoder1_position));
    WriteDisplayLine(application.display, 1, line);

    std::snprintf(line,
                  sizeof(line),
                  "E2 pos: %ld",
                  static_cast<long>(application.encoder2_position));
    WriteDisplayLine(application.display, 2, line);

    std::snprintf(line,
                  sizeof(line),
                  "Last: %+ld %+ld",
                  static_cast<long>(application.last_encoder1_delta),
                  static_cast<long>(application.last_encoder2_delta));
    WriteDisplayLine(application.display, 3, line);

    std::snprintf(line,
                  sizeof(line),
                  "SW: E1 %s E2 %s",
                  application.encoder1_button_down ? "ON" : "OFF",
                  application.encoder2_button_down ? "ON" : "OFF");
    WriteDisplayLine(application.display, 4, line);

    WriteDisplayLine(application.display, 5, "E2 TAP: back");
    application.display.Update();
}

void UpdateMainDisplay(Application& application)
{
    float output_value;
    {
        ScopedIrqBlocker irq_blocker;
        output_value = application.envelope.GetValue();
    }

    char line[22];
    char time_text[12];

    application.display.Fill(false);

    std::snprintf(line,
                  sizeof(line),
                  "E1 Mode: %s",
                  application.cycling ? "LFO" : "AD");
    WriteDisplayLine(application.display, 0, line);

    FormatTime(application.effective_rise_seconds,
               time_text,
               sizeof(time_text));
    std::snprintf(line, sizeof(line), "E1 Rise: %s", time_text);
    WriteDisplayLine(application.display, 1, line);

    FormatTime(application.effective_fall_seconds,
               time_text,
               sizeof(time_text));
    std::snprintf(line, sizeof(line), "E2 Fall: %s", time_text);
    WriteDisplayLine(application.display, 2, line);

    std::snprintf(
        line, sizeof(line), "E2 Curve: %s", CurveName(application.curve));
    WriteDisplayLine(application.display, 3, line);

    const uint32_t cv_hundredths = static_cast<uint32_t>(
        daisysp::fclamp(application.normalized_cv, 0.0f, 1.0f) * 100.0f
        + 0.5f);
    const uint32_t output_hundredths = static_cast<uint32_t>(
        daisysp::fclamp(output_value, 0.0f, 1.0f) * 100.0f + 0.5f);
    std::snprintf(line,
                  sizeof(line),
                  "CV:%c.%c%c Out:%c.%c%c",
                  static_cast<int>('0' + cv_hundredths / 100),
                  static_cast<int>('0' + (cv_hundredths / 10) % 10),
                  static_cast<int>('0' + cv_hundredths % 10),
                  static_cast<int>('0' + output_hundredths / 100),
                  static_cast<int>('0' + (output_hundredths / 10) % 10),
                  static_cast<int>('0' + output_hundredths % 10));
    WriteDisplayLine(application.display, 4, line);

    WriteDisplayLine(application.display, 5, "E2 Hold: MENU");

    application.display.Update();
}

void UpdateDisplay(Application& application)
{
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

    // GateIn è pensato per il circuito BJT invertente documentato in WIRING.md.
    // In AD avvia da Idle; in LFO riallinea immediatamente il ciclo a zero.
    if(application->trigger_input.Trig())
        application->envelope.Trigger();

    const float value = daisysp::fclamp(
        application->envelope.Process() * Settings::kOutputMaximum,
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

    app.encoder1.Init(HardwarePins::Encoder1A,
                      HardwarePins::Encoder1B,
                      HardwarePins::Encoder1Switch);
    app.encoder2.Init(HardwarePins::Encoder2A,
                      HardwarePins::Encoder2B,
                      HardwarePins::Encoder2Switch);
    app.trigger_input.Init(HardwarePins::TriggerInput);

    AdcChannelConfig
        adc_config[static_cast<uint8_t>(AdcChannel::Count)];
    adc_config[static_cast<uint8_t>(AdcChannel::SymmetryPot)]
        .InitSingle(HardwarePins::Potentiometer);
    adc_config[static_cast<uint8_t>(AdcChannel::TimeCv)]
        .InitSingle(HardwarePins::CvInput);
    app.hardware.adc.Init(
        adc_config, static_cast<uint8_t>(AdcChannel::Count));
    app.hardware.adc.Start();
    System::Delay(10);
    app.smoothed_pot = daisysp::fclamp(
        app.hardware.adc.GetFloat(
            static_cast<uint8_t>(AdcChannel::SymmetryPot)),
        0.0f,
        1.0f);
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
