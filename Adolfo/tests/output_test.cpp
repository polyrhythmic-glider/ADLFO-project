#include "Mcp4728Protocol.h"
#include "OledTransferQueue.h"
#include "EnvelopeBank.h"
#include <cassert>
#include <limits>

int main()
{
    // Four distinct codes detect channel swapping, byte-order and reference errors.
    assert((mcp4728::AllChannels({{0, 2000, 4000, 1000}})
            == std::array<uint8_t, 12>{{0x40, 0x80, 0x00, 0x42, 0x87, 0xd0,
                                       0x44, 0x8f, 0xa0, 0x46, 0x83, 0xe8}}));
    assert(mcp4728::AllChannels({{65535, 4001, 4095, 65535}})
           == mcp4728::AllChannels({{4000, 4000, 4000, 4000}}));
    assert((mcp4728::AllZero() == std::array<uint8_t, 12>{{
        0x40, 0x80, 0, 0x42, 0x80, 0, 0x44, 0x80, 0, 0x46, 0x80, 0}}));
    assert(mcp4728::CodeFromLevel(-1) == 0);
    assert(mcp4728::CodeFromLevel(0) == 0);
    assert(mcp4728::CodeFromLevel(0.5f) == 2000);
    assert(mcp4728::CodeFromLevel(1) == 4000);
    assert(mcp4728::CodeFromLevel(2) == 4000);
    assert(mcp4728::CodeFromLevel(std::numeric_limits<float>::quiet_NaN()) == 0);
    assert(mcp4728::CodeFromLevel(-std::numeric_limits<float>::infinity()) == 0);
    assert(mcp4728::CodeFromLevel(std::numeric_limits<float>::infinity()) == 4000);

    // An idle output stays zero; a manual AD reaches the 2 V peak and returns
    // to zero, and switching out of LFO also forces zero.
    EnvelopeGenerator envelope;
    envelope.Init(10000);
    envelope.SetCurve(CurveType::Linear);
    envelope.SetRiseTime(0.1f);
    envelope.SetFallTime(0.1f);
    assert(mcp4728::CodeFromLevel(envelope.Process()) == 0);
    envelope.Trigger();
    uint16_t peak = 0;
    for(unsigned i = 0; i < 2100; ++i)
    {
        const auto code = mcp4728::CodeFromLevel(envelope.Process());
        assert(code <= 4000);
        if(code > peak) peak = code;
    }
    assert(peak == 4000);
    assert(envelope.GetStage() == Stage::Idle);
    assert(mcp4728::CodeFromLevel(envelope.GetValue()) == 0);
    envelope.SetCycling(true);
    for(unsigned i = 0; i < 2100; ++i) envelope.Process();
    assert(envelope.GetStage() != Stage::Idle);
    envelope.SetCycling(false);
    assert(mcp4728::CodeFromLevel(envelope.Process()) == 0);
    envelope.Trigger();
    for(unsigned i = 0; i < 500; ++i) envelope.Process();
    assert(envelope.GetValue() > 0);
    envelope.Stop();
    assert(envelope.GetStage() == Stage::Idle && !envelope.IsCycling());
    assert(mcp4728::CodeFromLevel(envelope.Process()) == 0);
    envelope.SetCycling(true);
    envelope.Process();
    envelope.Stop();
    assert(!envelope.IsCycling() && envelope.GetValue() == 0);

    // Four independent voices with distinct attack/decay times and amplitudes.
    adlfo::EnvelopeBank bank;
    bank.Init(10000);
    assert((bank.Process() == std::array<uint16_t, 4>{}));
    std::array<uint16_t, 4> peaks{};
    for(unsigned i = 0; i < 4; ++i)
    {
        auto& ch = bank.channels[i];
        ch.rise = ch.fall = 0.2f + 0.1f * i;
        ch.level = 0.25f * (i + 1);
        ch.UpdateTimes(); ch.ApplyTimes();
        bank.Trigger(i);
    }
    bool separated = false;
    for(unsigned tick = 0; tick < 7000; ++tick)
    {
        const auto codes = bank.Process();
        for(unsigned i = 0; i < 4; ++i)
            if(codes[i] > peaks[i]) peaks[i] = codes[i];
        separated |= codes[0] == 0 && codes[3] > 0;
    }
    assert((peaks == std::array<uint16_t, 4>{{1000, 2000, 3000, 4000}}));
    assert(separated && (bank.Process() == std::array<uint16_t, 4>{}));
    // Manual and future external triggers share indexed routing, independent of UI.
    for(unsigned channel = 0; channel < 4; ++channel)
    {
        bank.Trigger(channel);
        bank.Process();
        const auto codes = bank.Process();
        for(unsigned i = 0; i < 4; ++i) assert((codes[i] > 0) == (i == channel));
        bank.StopAll();
    }
    bank.Trigger(4); // Reject invalid routes.
    assert((bank.Process() == std::array<uint16_t, 4>{}));
    bank.channels[0].envelope.SetCycling(true);
    bank.channels[2].envelope.SetCycling(true);
    for(unsigned tick = 0; tick < 500; ++tick) bank.Process();
    const float other = bank.channels[2].envelope.GetValue();
    bank.Trigger(0);
    assert(bank.channels[0].envelope.GetValue() == 0);
    assert(bank.channels[2].envelope.GetValue() == other);
    bank.channels[0].envelope.SetCycling(false);
    for(unsigned tick = 0; tick < 5000; ++tick)
    {
        const auto codes = bank.Process();
        assert(codes[0] == 0 && codes[1] == 0 && codes[3] == 0);
    }
    assert(bank.channels[2].envelope.IsCycling());

    // No input assembled: CV settings must never attenuate or slow a voice.
    auto& ch = bank.channels[1];
    ch.rise = ch.fall = 0.4f; ch.level = 0.8f;
    ch.cv = 1; ch.cv_enabled = false;
    ch.UpdateTimes(); ch.ApplyTimes();
    const float unmodulated = ch.rise_seconds;
    for(auto target : {adlfo::CvTarget::Off, adlfo::CvTarget::Time, adlfo::CvTarget::Rise,
                       adlfo::CvTarget::Fall, adlfo::CvTarget::Level})
    {
        ch.cv_target = target; ch.UpdateTimes(); ch.ApplyTimes();
        assert(ch.rise_seconds == unmodulated && ch.fall_seconds == unmodulated);
        assert(ch.effective_level == 0.8f);
    }
    ch.cv_enabled = true; ch.cv = 0.5f;
    ch.UpdateTimes(); ch.ApplyTimes();
    assert(ch.effective_level == 0.4f); // LEVEL is attenuation relative to E4.
    ch.cv_target = adlfo::CvTarget::Rise; ch.UpdateTimes(); ch.ApplyTimes();
    assert(ch.rise_seconds > unmodulated && ch.fall_seconds == unmodulated);
    assert(ch.effective_level == 0.8f);
    ch.cv_target = adlfo::CvTarget::Fall; ch.UpdateTimes(); ch.ApplyTimes();
    assert(ch.rise_seconds == unmodulated && ch.fall_seconds > unmodulated);
    ch.cv_target = adlfo::CvTarget::Time; ch.UpdateTimes(); ch.ApplyTimes();
    assert(ch.rise_seconds > unmodulated && ch.rise_seconds == ch.fall_seconds);
    ch.cv_target = adlfo::CvTarget::Off; ch.UpdateTimes(); ch.ApplyTimes();
    assert(ch.rise_seconds == unmodulated && ch.effective_level == 0.8f);

    // Test page isolates one output, ignores external triggers and exits at zero.
    bank.BeginTest();
    for(unsigned channel = 0; channel < 4; ++channel)
        for(unsigned volts = 0; volts <= 2; ++volts)
        {
            bank.SetTest(channel, volts);
            for(unsigned i = 0; i < 4; ++i) bank.Trigger(i);
            const auto codes = bank.Process();
            for(unsigned i = 0; i < 4; ++i)
                assert(codes[i] == (i == channel ? volts * 2000 : 0));
        }
    bank.SetTest(3, 99);
    assert(bank.Process()[3] == 4000);
    bank.EndTest();
    for(unsigned i = 0; i < 100; ++i) assert((bank.Process() == std::array<uint16_t, 4>{}));
    for(auto& channel : bank.channels) assert(!channel.envelope.IsCycling());
    assert(bank.channels[1].level == 0.8f); // Parameters survive diagnostic mode.

    // A whole OLED frame must fit, retain command/data order and own a copy
    // of the pixels so later drawing cannot corrupt an in-flight frame.
    OledTransferQueue queue;
    assert(queue.Empty());
    uint8_t oversized[10]{};
    assert(!queue.Push(oversized, sizeof(oversized)));
    assert(!queue.Push(oversized, 0));
    for(unsigned frame = 0; frame < 3; ++frame)
    {
        for(unsigned page = 0; page < 8; ++page)
        {
            for(uint8_t command : {static_cast<uint8_t>(0xb0 + page), uint8_t{0}, uint8_t{0x10}})
            {
                uint8_t data[] = {0x00, command};
                assert(queue.Push(data, sizeof(data)));
            }
            for(unsigned chunk = 0; chunk < 16; ++chunk)
            {
                uint8_t data[9] = {0x40};
                for(unsigned i = 0; i < 8; ++i) data[i + 1] = page * 16 + chunk;
                assert(queue.Push(data, sizeof(data)));
                data[1] = 0xff;
            }
        }
        const uint8_t extra[] = {0, 0};
        assert(!queue.Push(extra, sizeof(extra)));
        for(unsigned page = 0; page < 8; ++page)
        {
            for(uint8_t command : {static_cast<uint8_t>(0xb0 + page), uint8_t{0}, uint8_t{0x10}})
            {
                assert(queue.Front().size == 2);
                assert(queue.Front().data[0] == 0 && queue.Front().data[1] == command);
                queue.Pop();
            }
            for(unsigned chunk = 0; chunk < 16; ++chunk)
            {
                assert(queue.Front().size == 9 && queue.Front().data[0] == 0x40);
                for(unsigned i = 1; i < 9; ++i)
                    assert(queue.Front().data[i] == page * 16 + chunk);
                queue.Pop();
            }
        }
        assert(queue.Empty());
    }
    const uint8_t command[] = {0, 0xaf};
    assert(queue.Push(command, sizeof(command)));
    queue.Clear(); // Failed transfer / discarded frame.
    assert(queue.Empty());
    assert(queue.Push(command, sizeof(command)));
}

