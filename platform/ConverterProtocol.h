#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
namespace adolfo {
// AD7606C-18 software mode, one DOUTA, no CRC/status header.
// CS remains asserted across 144 clocks. SPI data size stays 8 bits:
// byte-aligned DMA receives 18 bytes, then unpacking restores eight 18-bit words.
inline bool DecodeAdc(const uint8_t* bytes,size_t size,std::array<int32_t,8>& values) {
 if(!bytes||size!=18)return false;
 for(unsigned ch=0;ch<8;++ch) {
  uint32_t raw=0;
  for(unsigned bit=0;bit<18;++bit) {
   const unsigned pos=ch*18+bit;
   raw=(raw<<1)|((bytes[pos/8]>>(7-pos%8))&1u);
  }
  values[ch]=(raw&0x20000u)?int32_t(raw)-262144:int32_t(raw);
 }
 return true;
}
// DAC8568: command 0 writes an input register without updating the output.
// Physical backend frames each 32-bit word with SYNC, then pulses LDAC once.
inline bool DacWriteInput(unsigned channel,uint16_t value,std::array<uint8_t,4>& bytes) {
 if(channel>=8)return false;
 const uint32_t word=(uint32_t(channel)<<20)|(uint32_t(value)<<4);
 bytes={{uint8_t(word>>24),uint8_t(word>>16),uint8_t(word>>8),uint8_t(word)}};
 return true;
}
}
