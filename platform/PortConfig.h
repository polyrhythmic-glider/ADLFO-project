#pragma once
#include <array>
#include <cstdint>
#include <cmath>
namespace adolfo {
enum class Mode { AudioIn, CvIn, GateIn, TriggerIn, AudioOut, CvOut, EnvelopeOut, LfoOut, GateOut, TriggerOut, Disabled };
inline bool IsOutput(Mode m) { return m>=Mode::AudioOut && m<=Mode::TriggerOut; }
inline bool Allowed(unsigned port, Mode m) {
    if(port>=12) return false;
    if(m==Mode::Disabled) return true;
    if(port<4) return m>=Mode::AudioIn && m<=Mode::TriggerIn;
    if(port<8) return IsOutput(m);
    return m==Mode::CvIn||m==Mode::GateIn||m==Mode::TriggerIn||m==Mode::CvOut||m==Mode::GateOut||m==Mode::TriggerOut;
}
// Policy only: no claim to initialize ADC/DAC, switches, clocks or hardware.
// Backends MUST apply the returned off mask before writing a new DAC value,
// wait for settling, then explicitly mark the channel ready.
class PortConfig {
 public:
    PortConfig() { modes_.fill(Mode::Disabled); }
    bool Set(unsigned port, Mode mode) {
        if(!Allowed(port,mode)) return false;
        modes_[port]=mode;
        if(port>=4) ready_[port-4]=false;
        return true;
    }
    bool Ready(unsigned port) {
        if(port<4||port>=12||!IsOutput(modes_[port]))return false;
        ready_[port-4]=true; return true;
    }
    // On any fault, reset both permit and readiness. Re-arming requires
    // each backend to preload/calibrate/settle again, not just toggle permit.
    void Disarm() { permit_=false; ready_.fill(false); }
    void Arm(bool rails_ok,bool drivers_ok,bool calibration_ok) {
        if(!(rails_ok&&drivers_ok&&calibration_ok)) { Disarm();return; }
        permit_=true;
    }
    uint8_t SwitchMask() const {
        uint8_t mask=0;
        if(permit_)for(unsigned i=0;i<8;++i)if(ready_[i]&&IsOutput(modes_[i+4]))mask|=uint8_t(1u<<i);
        return mask;
    }
 private:
    std::array<Mode,12> modes_;
    std::array<bool,8> ready_{};
    bool permit_=false;
};
// Ideal DAC8568B span 0..2.5 V; external gain 4 and offset -5 V.
// Real calibration, load-dependent error and temperature are backend concerns.
inline bool VoltsToCode(float volts,uint16_t& code) {
    if(!std::isfinite(volts))return false;
    if(volts<=-5.f)code=0;
    else if(volts>=5.f)code=65535;
    else { const long raw=std::lround((volts+5.f)*65536.f/10.f); code=static_cast<uint16_t>(raw>65535?65535:raw); }
    return true;
}
}
