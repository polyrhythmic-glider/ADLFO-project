#include <cstdint>

#include "daisy_seed.h"
#include "dev/oled_ssd130x.h"

#include "EnvelopeBank.h"
#include "HardwareConfig.h"
#include "PanelControls.h"
#include "OledUi.h"
#include "Mcp4728Protocol.h"
#include "OledTransferQueue.h"

using namespace daisy;

namespace Settings
{
constexpr uint32_t kEnvelopeUpdateRateHz = 10000;
constexpr float kEnvelopeUpdateRate
    = static_cast<float>(kEnvelopeUpdateRateHz);
constexpr uint32_t kEncoderScanRateHz = 1000;
constexpr uint32_t kEncoderScanDivider
    = kEnvelopeUpdateRateHz / kEncoderScanRateHz;

constexpr float kCvSmoothingAmount = 0.02f;

constexpr uint32_t kDisplayPeriodMs = 150;

constexpr uint8_t kOledI2cAddress = 0x3C;

constexpr uint32_t kDacPeriodUs = 1000;

static_assert(kEnvelopeUpdateRateHz % kEncoderScanRateHz == 0,
              "La frequenza encoder deve dividere quella dell'inviluppo");
} // namespace Settings

// Un solo bus, inizializzato una volta: DAC e OLED lo usano dal main loop.
I2CHandle shared_i2c;
bool shared_i2c_ready = false;
OledTransferQueue oled_queue;
bool oled_deferred = false;
bool oled_available = false;
uint8_t oled_address = Settings::kOledI2cAddress;

// Il disegno accoda un frame; il loop invia al massimo 8 byte di pixel per
// transazione, lasciando spazio agli aggiornamenti DAC anche durante il refresh.
class BufferedSSD1306I2CTransport
{
  public:
    struct Config
    {
        uint8_t i2c_address = Settings::kOledI2cAddress;
    };

    void Init(const Config& config)
    {
        oled_address = config.i2c_address;
    }

    void SendCommand(uint8_t command)
    {
        uint8_t packet[2] = {0x00, command};
        Send(packet, sizeof(packet));
    }

    void SendData(uint8_t* data, size_t size)
    {
        for(size_t offset = 0; offset < size; offset += OledTransferQueue::kDataBytes)
        {
            const size_t count = size - offset < OledTransferQueue::kDataBytes
                                     ? size - offset : OledTransferQueue::kDataBytes;
            uint8_t packet[OledTransferQueue::kDataBytes + 1] = {0x40};
            for(size_t i = 0; i < count; ++i)
                packet[i + 1] = data[offset + i];
            Send(packet, count + 1);
        }
    }

  private:
    void Send(uint8_t* packet, size_t size)
    {
        if(!oled_available)
            return;
        const bool ok = oled_deferred
            ? oled_queue.Push(packet, size)
            : shared_i2c.TransmitBlocking(oled_address, packet, size, 10)
                  == I2CHandle::Result::OK;
        if(!ok)
        {
            oled_available = false;
            oled_queue.Clear();
        }
    }
};

using BufferedSSD1306Driver
    = SSD130xDriver<128, 64, BufferedSSD1306I2CTransport>;
using Display = OledDisplay<BufferedSSD1306Driver>;

struct Application
{
    DaisySeed        hardware;
    panel::Controls  panel_controls;
    ui::Frame        panel_frame;
    ui::Controller   ui;
    GateIn trigger_inputs[adlfo::kChannels];
    int8_t adc_indices[adlfo::kChannels] = {-1, -1, -1, -1};
    float smoothed_cv[adlfo::kChannels]{};
    Display          display;
    TimerHandle      envelope_timer;
    adlfo::EnvelopeBank bank;
    uint8_t dac_address = 0;
    bool timer_started = false;
    volatile uint16_t pending_dac_codes[adlfo::kChannels]{}; // ISR -> main, IRQ guard.
    uint32_t last_dac_update_us = 0;
    uint32_t encoder_scan_divider = 0;
    uint32_t last_display_update_ms = 0;
};

// Stato applicativo condiviso con il callback hardware.
Application app;

adlfo::Channel& Selected(Application& application)
{
    return application.bank.channels[application.ui.channel];
}

[[noreturn]] void SignalInitializationError(Application& application,
                                           const char* message);

bool WriteAllDacZero(Application& application)
{
    auto packet = mcp4728::AllZero();
    return application.dac_address != 0
           && shared_i2c.TransmitBlocking(application.dac_address,
                                         packet.data(), packet.size(), 10)
                  == I2CHandle::Result::OK;
}

bool InitOutputBus(Application& application)
{
    I2CHandle::Config config;
    config.periph = I2CHandle::Config::Peripheral::I2C_1;
    config.mode = I2CHandle::Config::Mode::I2C_MASTER;
    config.speed = hardware_config::kI2cSpeed;
    config.pin_config.scl = hardware_config::kI2cScl;
    config.pin_config.sda = hardware_config::kI2cSda;
    if(shared_i2c.Init(config) != I2CHandle::Result::OK)
        return false;
    shared_i2c_ready = true;
    System::Delay(30);

    unsigned found = 0;
    for(uint8_t address : {uint8_t{0x60}, uint8_t{0x64}})
    {
        uint8_t state[24]{};
        if(shared_i2c.ReceiveBlocking(address, state, sizeof(state), 10)
           == I2CHandle::Result::OK)
        {
            application.dac_address = address;
            ++found;
        }
    }
    if(found != 1)
    {
        application.dac_address = 0;
        return false;
    }
    return WriteAllDacZero(application);
}

void ServiceDac(Application& application)
{
    const uint32_t now = System::GetUs();
    if(now - application.last_dac_update_us < Settings::kDacPeriodUs)
        return;
    std::array<uint16_t, adlfo::kChannels> codes{};
    {
        ScopedIrqBlocker lock;
        for(size_t i = 0; i < adlfo::kChannels; ++i)
            codes[i] = application.pending_dac_codes[i];
    }
    auto packet = mcp4728::AllChannels(codes);
    if(shared_i2c.TransmitBlocking(application.dac_address,
                                  packet.data(), packet.size(), 10)
       != I2CHandle::Result::OK)
        SignalInitializationError(application, "MCP4728 I2C ERROR");
    application.last_dac_update_us = now;
}

void ServiceDisplay()
{
    if(!oled_available || oled_queue.Empty())
        return;
    auto& packet = oled_queue.Front();
    if(shared_i2c.TransmitBlocking(oled_address, packet.data.data(),
                                  packet.size, 10) != I2CHandle::Result::OK)
    {
        // Un OLED assente/guasto non deve bloccare indefinitamente il DAC.
        oled_available = false;
        oled_queue.Clear();
        app.hardware.PrintLine("OLED I2C ERROR: display disabilitato fino al reset");
        return;
    }
    oled_queue.Pop();
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

void UpdateEnvelopeTimes(Application& application)
{
    for(size_t i = 0; i < adlfo::kChannels; ++i)
    {
        auto& channel = application.bank.channels[i];
        channel.cv_enabled = application.adc_indices[i] >= 0;
        if(channel.cv_enabled)
        {
            const float raw = application.hardware.adc.GetFloat(application.adc_indices[i]);
            application.smoothed_cv[i] += Settings::kCvSmoothingAmount
                                         * (raw - application.smoothed_cv[i]);
            channel.cv = adlfo::Clamp01(application.smoothed_cv[i] / hardware_config::kCv[i].full_scale);
        }
        else channel.cv = 0.0f;
        channel.UpdateTimes(); // powf stays outside the IRQ blocker.
        ScopedIrqBlocker lock;
        channel.ApplyTimes();
    }
}

void ProcessControls(Application& application)
{
    application.panel_frame = application.panel_controls.Consume();
    const auto previous_page = application.ui.page;
    const auto previous_channel = application.ui.channel;
    const auto previous_test_volts = application.ui.test_volts;
    ScopedIrqBlocker lock;
    application.ui.Process(application.panel_frame, application.bank);
    // Clear queued DAC values immediately on test entry, exit, channel change
    // or zero selection. The next timer tick supplies the new bank values.
    if((previous_page == ui::Page::OutputTest || application.ui.page == ui::Page::OutputTest)
       && (previous_page != application.ui.page || previous_channel != application.ui.channel
           || (previous_test_volts != 0 && application.ui.test_volts == 0)))
        for(auto& code : application.pending_dac_codes) code = 0;
}

void InitDisplay(Application& application)
{
    if(!shared_i2c_ready)
        return;
    // Tutta la configurazione SSD1306 resta confinata qui per poter cambiare
    // facilmente driver se il modulo reale usa un controller diverso.
    Display::Config config;
    config.driver_config.transport_config.i2c_address
        = Settings::kOledI2cAddress;

    // Stessi pin e velocita del test OLED verificato sulla breadboard.
    System::Delay(200);
    const uint8_t addresses[] = {Settings::kOledI2cAddress, 0x3D};
    for(uint8_t address : addresses)
    {
        uint8_t nop[] = {0x00, 0xE3};
        if(shared_i2c.TransmitBlocking(address, nop, sizeof(nop), 20)
           == I2CHandle::Result::OK)
        {
            config.driver_config.transport_config.i2c_address = address;
            oled_available = true;
            break;
        }
    }

    if(oled_available)
        application.display.Init(config);
    oled_deferred = true;
}

void WriteDisplayLine(Display& display, uint8_t row, const char* text)
{
    constexpr uint8_t kLineHeight = 10;
    display.SetCursor(0, row * kLineHeight);
    display.WriteString(text, Font_6x8, true);
}

void UpdateDisplay(Application& application)
{
    if(!oled_available || !oled_queue.Empty())
        return;
    auto& display = application.display;
    const auto& state = application.ui;
    const auto& voice = Selected(application);
    const unsigned channel = state.channel + 1;
    switch(state.page)
    {
        case ui::Page::Main:
        {
            float output;
            bool cycling;
            {
                ScopedIrqBlocker lock;
                output = voice.envelope.GetValue() * voice.effective_level;
                cycling = voice.envelope.IsCycling();
            }
            ui::DrawMain(display, voice.rise_seconds, voice.fall_seconds, output,
                         voice.symmetry, voice.level, cycling, CurveName(voice.curve), channel);
            break;
        }
        case ui::Page::Settings:
            ui::DrawSettings(display, state.menu_item, channel);
            break;
        case ui::Page::Controls:
            ui::DrawControls(display);
            break;
        case ui::Page::Encoders:
            ui::DrawEncoders(display, state.encoder_values, application.panel_frame.events, channel);
            break;
        case ui::Page::CvTarget:
            ui::DrawCvTarget(display, channel, voice.cv_target, voice.cv, voice.cv_enabled);
            break;
        case ui::Page::OutputTest:
            ui::DrawOutputTest(display, channel, state.test_volts);
            break;
    }
    display.Update();
}

void EnvelopeTimerCallback(void* context)
{
    auto* application = static_cast<Application*>(context);

    // I quattro inviluppi girano a 10 kHz; ogni dieci tick gli encoder vengono letti a
    // 1 kHz, indipendentemente dai trasferimenti OLED del loop principale.
    ++application->encoder_scan_divider;
    if(application->encoder_scan_divider >= Settings::kEncoderScanDivider)
    {
        application->encoder_scan_divider = 0;
        application->panel_controls.Scan();
    }

    for(size_t i = 0; i < adlfo::kChannels; ++i)
        if(hardware_config::kTriggers[i].enabled && application->trigger_inputs[i].Trig())
            application->bank.Trigger(i);

    const auto codes = application->bank.Process();
    for(size_t i = 0; i < adlfo::kChannels; ++i)
        application->pending_dac_codes[i] = codes[i];

}

bool InitEnvelopeTimer(Application& application)
{
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
    application.timer_started = application.envelope_timer.Start() == TimerHandle::Result::OK;
    return application.timer_started;
}

[[noreturn]] void SignalInitializationError(Application& application, const char* message)
{
    if(application.timer_started)
        application.envelope_timer.Stop();
    if(shared_i2c_ready && application.dac_address != 0)
        WriteAllDacZero(application); // Tentativo: un DAC irraggiungibile può tenere l'ultimo valore.
    application.hardware.PrintLine("ERRORE: %s. Uscite non garantite a zero.", message);
    oled_queue.Clear();
    oled_deferred = false;
    if(oled_available)
    {
        application.display.Fill(false);
        WriteDisplayLine(application.display, 0, "DAC ERROR");
        WriteDisplayLine(application.display, 2, message);
        WriteDisplayLine(application.display, 4, "CHECK WIRING / RESET");
        application.display.Update();
    }
    while(true)
    {
        application.hardware.SetLed(true);
        System::Delay(100);
        application.hardware.SetLed(false);
        System::Delay(100);
    }
}

bool InitExternalInputs(Application& application)
{
    Pin used[2 + 4 * panel::kColumns + 2 * adlfo::kChannels];
    size_t count = 0;
    used[count++] = hardware_config::kI2cScl;
    used[count++] = hardware_config::kI2cSda;
    for(const auto& p : panel::kPins)
        for(auto pin : {p.encoder_a, p.encoder_b, p.encoder_switch, p.button}) used[count++] = pin;
    auto reserve = [&](Pin pin) {
        if(!pin.IsValid()) return false;
        for(size_t i = 0; i < count; ++i) if(used[i] == pin) return false;
        used[count++] = pin;
        return true;
    };
    const Pin analog_pins[] = {seed::A0, seed::A1, seed::A2, seed::A3, seed::A4,
        seed::A5, seed::A6, seed::A7, seed::A8, seed::A9, seed::A10, seed::A11};
    for(size_t i = 0; i < adlfo::kChannels; ++i)
    {
        const auto& trig = hardware_config::kTriggers[i];
        const auto& cv = hardware_config::kCv[i];
        if(trig.enabled && !reserve(trig.pin)) return false;
        if(cv.enabled)
        {
            bool analog = false;
            for(auto pin : analog_pins) analog |= pin == cv.pin;
            if(!analog || !reserve(cv.pin) || !(cv.full_scale > 0.0f && cv.full_scale <= 1.0f)) return false;
        }
    }
    AdcChannelConfig configs[adlfo::kChannels];
    uint8_t adc_count = 0;
    for(size_t i = 0; i < adlfo::kChannels; ++i)
    {
        const auto& trig = hardware_config::kTriggers[i];
        if(trig.enabled)
        {
            application.trigger_inputs[i].Init(trig.pin, trig.inverted);
            application.trigger_inputs[i].Trig(); // Prime state: no artificial startup edge.
        }
        if(hardware_config::kCv[i].enabled)
        {
            application.adc_indices[i] = adc_count;
            configs[adc_count++].InitSingle(hardware_config::kCv[i].pin);
        }
    }
    if(adc_count)
    {
        application.hardware.adc.Init(configs, adc_count);
        application.hardware.adc.Start();
        System::Delay(10);
        for(size_t i = 0; i < adlfo::kChannels; ++i)
            if(application.adc_indices[i] >= 0)
                application.smoothed_cv[i] = application.hardware.adc.GetFloat(application.adc_indices[i]);
    }
    return true;
}

int main(void)
{
    app.hardware.Init();
    app.hardware.StartLog(false);

    app.panel_controls.Init();
    app.bank.Init(Settings::kEnvelopeUpdateRate);

    const bool dac_ok = InitOutputBus(app);
    InitDisplay(app);
    if(!dac_ok)
        SignalInitializationError(app, "CHECK DAC 0x60/0x64");

    if(!InitExternalInputs(app))
        SignalInitializationError(app, "CHECK INPUT CONFIG");
    UpdateEnvelopeTimes(app);
    if(!InitEnvelopeTimer(app))
        SignalInitializationError(app, "TIMER ERROR");

    UpdateDisplay(app);
    app.last_display_update_ms = System::GetNow();
    uint32_t last_controls_ms = app.last_display_update_ms;
    app.hardware.PrintLine("ADLFO 4: MCP4728 0x%02X, VA/VB/VC/VD 0-2V",
                           unsigned(app.dac_address));

    while(true)
    {
        ServiceDac(app);

        const uint32_t now = System::GetNow();
        if(now - last_controls_ms >= 1)
        {
            last_controls_ms = now;
            ProcessControls(app);
            UpdateEnvelopeTimes(app);
        }
        if(now - app.last_display_update_ms >= Settings::kDisplayPeriodMs
           && oled_queue.Empty())
        {
            app.last_display_update_ms = now;
            UpdateDisplay(app);
        }

        ServiceDisplay();
        if(oled_queue.Empty())
            System::DelayUs(50);
    }
}
