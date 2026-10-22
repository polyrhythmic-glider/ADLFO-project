#include "daisy_seed.h"
#include "Cv4Protocol.h"

using namespace daisy;

namespace
{
DaisySeed hardware;
I2CHandle bus;
Switch buttons[4];
uint8_t dac_address = 0;
enum class Mode { Zero, Levels, Lfo, Follow };

bool WriteDac(const cv4::Codes& values)
{
    auto data = cv4::Packet(values);
    return bus.TransmitBlocking(dac_address, data.data(), data.size(), 10)
           == I2CHandle::Result::OK;
}

[[noreturn]] void Fault(const char* message)
{
    // An unreachable DAC may retain its last value; LED/log never imply zero.
    if(dac_address != 0)
        WriteDac({0, 0, 0, 0});
    for(unsigned tick = 0;; ++tick)
    {
        hardware.SetLed(tick % 2 == 0);
        if(tick % 10 == 0)
            hardware.PrintLine("ERRORE: %s. OUT non garantite a zero. Spegnere e controllare.", message);
        System::Delay(100);
    }
}

const char* ModeName(Mode mode)
{
    switch(mode)
    {
        case Mode::Zero: return "ZERO";
        case Mode::Levels: return "LIVELLI";
        case Mode::Lfo: return "LFO";
        case Mode::Follow: return "CV";
    }
    return "?";
}
} // namespace

int main()
{
    hardware.Init();
    hardware.StartLog(false);

    I2CHandle::Config config;
    config.periph = I2CHandle::Config::Peripheral::I2C_1;
    config.mode = I2CHandle::Config::Mode::I2C_MASTER;
    config.speed = I2CHandle::Config::Speed::I2C_100KHZ;
    config.pin_config.scl = seed::D11;
    config.pin_config.sda = seed::D12;
    if(bus.Init(config) != I2CHandle::Result::OK)
        Fault("inizializzazione I2C");
    System::Delay(30);

    // Read only: 24 bytes = DAC+EEPROM state of four channels.
    // This demo expects exactly one MCP4728, at an Adafruit default address.
    unsigned found = 0;
    for(const uint8_t address : {uint8_t{0x60}, uint8_t{0x64}})
    {
        uint8_t state[24]{};
        if(bus.ReceiveBlocking(address, state, sizeof(state), 10)
           == I2CHandle::Result::OK)
        {
            dac_address = address;
            ++found;
        }
    }
    if(found != 1)
    {
        dac_address = 0; // Do not write to an ambiguous bus.
        Fault("atteso un MCP4728 a 0x60 oppure 0x64");
    }
    if(!WriteDac({0, 0, 0, 0}))
        Fault("inizializzazione DAC a zero");

    AdcChannelConfig adc[4];
    const Pin adc_pins[4] = {seed::D16, seed::D17, seed::D18, seed::D19};
    for(unsigned channel = 0; channel < 4; ++channel)
        adc[channel].InitSingle(adc_pins[channel]);
    hardware.adc.Init(adc, 4);
    hardware.adc.Start();
    const Pin button_pins[4] = {seed::D25, seed::D24, seed::D26, seed::D27};
    for(unsigned button = 0; button < 4; ++button)
        buttons[button].Init(button_pins[button]);

    Mode mode = Mode::Zero;
    uint32_t mode_start = System::GetNow();
    uint32_t last_update = mode_start;
    uint32_t last_log = mode_start;
    cv4::Codes values{};
    constexpr uint32_t periods_ms[4] = {8000, 6000, 4000, 2000};

    for(;;)
    {
        const uint32_t now = System::GetNow();
        for(auto& button : buttons)
            button.Debounce();
        // B1 has priority over other simultaneous presses.
        Mode next = mode;
        if(buttons[0].RisingEdge()) next = Mode::Zero;
        else if(buttons[1].RisingEdge()) next = Mode::Levels;
        else if(buttons[2].RisingEdge()) next = Mode::Lfo;
        else if(buttons[3].RisingEdge()) next = Mode::Follow;
        if(next != mode)
        {
            mode = next;
            mode_start = now;
        }

        if(now - last_update >= 5) // Nominally 200 Hz: slow CV bench test.
        {
            last_update = now;
            values = {0, 0, 0, 0};
            if(mode == Mode::Levels)
                values = {0, 1024, 2048, 4000};
            for(unsigned channel = 0; channel < 4; ++channel)
            {
                if(mode == Mode::Follow)
                    values[channel] = cv4::CodeFromAdc(hardware.adc.GetFloat(channel));
                else if(mode == Mode::Lfo)
                {
                    const uint32_t period = periods_ms[channel];
                    const uint32_t phase = (now - mode_start) % period;
                    const uint32_t ramp = phase <= period / 2 ? phase : period - phase;
                    values[channel] = static_cast<uint16_t>(ramp * 8000u / period);
                }
            }
            if(!WriteDac(values))
                Fault("trasferimento al MCP4728");
            hardware.SetLed(mode == Mode::Zero || now % 1000 < 100);
        }

        if(now - last_log >= 500)
        {
            last_log = now;
            // Integers avoid dependence on printf float support. CV estimates
            // assume VDDA=3.300 V and ideal 100k/33k dividers.
            unsigned mv[4];
            for(unsigned channel = 0; channel < 4; ++channel)
                mv[channel] = static_cast<unsigned>(hardware.adc.GetFloat(channel)
                                                    * 3300.0f * 133.0f / 33.0f + 0.5f);
            hardware.PrintLine("DAC=0x%02X mode=%s IN_mV=%u,%u,%u,%u OUT_code=%u,%u,%u,%u",
                               unsigned(dac_address), ModeName(mode),
                               mv[0], mv[1], mv[2], mv[3],
                               unsigned(values[0]), unsigned(values[1]),
                               unsigned(values[2]), unsigned(values[3]));
        }
        System::Delay(1);
    }
}
