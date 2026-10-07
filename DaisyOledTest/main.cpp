#include "daisy_seed.h"
#include "dev/oled_ssd130x.h"
#include "hid/disp/oled_display.h"
#include <cstdio>

using namespace daisy;

DaisySeed seed_board;
OledDisplay<SSD130xI2c128x64Driver> display;

int main()
{
    seed_board.Configure();
    seed_board.Init();
    System::Delay(200);

    OledDisplay<SSD130xI2c128x64Driver>::Config config;
    auto& bus = config.driver_config.transport_config;
    bus.i2c_address = 0x3C;
    bus.i2c_config.periph = I2CHandle::Config::Peripheral::I2C_1;
    bus.i2c_config.mode = I2CHandle::Config::Mode::I2C_MASTER;
    bus.i2c_config.speed = I2CHandle::Config::Speed::I2C_100KHZ;
    bus.i2c_config.pin_config.scl = seed::D11;
    bus.i2c_config.pin_config.sda = seed::D12;

    // Probe both common OLED addresses before running the display driver.
    // 0x00 selects command mode; 0xE3 is NOP on SSD1306 and SH1106.
    I2CHandle probe;
    probe.Init(bus.i2c_config);
    bool found = false;
    while(!found)
    {
        for(uint8_t address : {0x3C, 0x3D})
        {
            uint8_t nop[] = {0x00, 0xE3};
            if(probe.TransmitBlocking(address, nop, sizeof(nop), 20)
               == I2CHandle::Result::OK)
            {
                bus.i2c_address = address;
                found = true;
                break;
            }
        }
        if(!found)
        {
            // Three quick flashes: neither address acknowledges.
            for(int i = 0; i < 3; ++i)
            {
                seed_board.SetLed(true);
                System::Delay(100);
                seed_board.SetLed(false);
                System::Delay(100);
            }
            System::Delay(900);
        }
    }
    display.Init(config);

    // Light every pixel briefly, independently of framebuffer contents.
    SSD130xI2CTransport commands;
    commands.Init(bus);
    commands.SendCommand(0xA5);
    seed_board.SetLed(true);
    System::Delay(2000);
    commands.SendCommand(0xA4);

    unsigned count = 0;
    while(true)
    {
        seed_board.SetLed((count & 1) != 0);
        display.Fill(false);
        display.DrawRect(0, 0, 127, 63, true, false);
        display.SetCursor(10, 10);
        display.WriteString("DAISY OLED", Font_7x10, true);
        display.SetCursor(10, 26);
        display.WriteString("TEST DISPLAY", Font_7x10, true);
        char text[24];
        snprintf(text, sizeof(text), "Count: %u", count++);
        display.SetCursor(10, 44);
        display.WriteString(text, Font_7x10, true);
        display.Update();
        System::Delay(500);
    }
}
