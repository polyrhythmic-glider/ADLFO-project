#include "../PortConfig.h"
#include <cassert>
#include <limits>
int main() {
 using namespace adolfo;
 PortConfig p;assert(p.SwitchMask()==0);
 for(unsigned i=0;i<4;++i) {assert(p.Set(i,Mode::AudioIn));assert(!p.Set(i,Mode::AudioOut));assert(!p.Ready(i));}
 for(unsigned i=4;i<8;++i) {assert(p.Set(i,Mode::AudioOut));assert(p.Ready(i));}
 for(unsigned i=8;i<12;++i) {assert(!p.Set(i,Mode::AudioIn));assert(!p.Set(i,Mode::AudioOut));assert(p.Set(i,Mode::CvOut));assert(p.Ready(i));}
 assert(p.SwitchMask()==0);p.Arm(true,true,true);assert(p.SwitchMask()==255);
 assert(p.Set(8,Mode::CvIn));assert(p.SwitchMask()==239);assert(!p.Ready(8));
 assert(p.Set(8,Mode::TriggerOut));assert(p.SwitchMask()==239);assert(p.Ready(8));assert(p.SwitchMask()==255);
 p.Arm(false,true,true);assert(p.SwitchMask()==0);p.Arm(true,true,true);assert(p.SwitchMask()==0);
 assert(!p.Set(12,Mode::CvOut));assert(!p.Ready(99));
 uint16_t code=7;assert(VoltsToCode(0,code)&&code==32768);assert(VoltsToCode(-10,code)&&code==0);assert(VoltsToCode(10,code)&&code==65535);
 assert(VoltsToCode(4.999999f,code)&&code==65535);
 assert(!VoltsToCode(std::numeric_limits<float>::quiet_NaN(),code));
 assert(!VoltsToCode(std::numeric_limits<float>::infinity(),code));
}
