#include "../ConverterProtocol.h"
#include <cassert>
int main(){
 using namespace adolfo;
 const uint8_t raw[18]={0x0,0x0,0x0,0x0,0x17,0xff,0xfe,0x0,0x0,0xff,0xff,0xd2,0x34,0x55,0x55,0x56,0xaa,0xaa};
 std::array<int32_t,8> values{};
 const std::array<int32_t,8> expected{{0,1,131071,-131072,-1,74565,87381,-87382}};
 assert(DecodeAdc(raw,18,values)&&values==expected);
 assert(!DecodeAdc(raw,17,values));assert(!DecodeAdc(nullptr,18,values));
 std::array<uint8_t,4> out{};
 assert(DacWriteInput(0,32768,out));
 assert((out==std::array<uint8_t,4>{{0,8,0,0}}));
 assert(DacWriteInput(7,65535,out));
 assert((out==std::array<uint8_t,4>{{0,0x7f,0xff,0xf0}}));
 assert(!DacWriteInput(8,0,out));
}
