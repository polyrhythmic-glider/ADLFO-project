#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

// One SSD1306 frame: 8 pages * (3 commands + 16 chunks of 8 pixels bytes).
// Queue complete I2C transactions so DAC writes can run between OLED chunks.
// Used exclusively in the foreground; no interrupt accesses this queue.
class OledTransferQueue
{
  public:
    static constexpr size_t kDataBytes = 8;
    static constexpr size_t kCapacity = 8 * (3 + 128 / kDataBytes);
    struct Packet
    {
        std::array<uint8_t, kDataBytes + 1> data{};
        uint8_t size = 0;
    };

    bool Push(const uint8_t* data, size_t size)
    {
        if(size == 0 || size > kDataBytes + 1 || write_ == kCapacity)
            return false;
        auto& packet = packets_[write_++];
        packet.size = static_cast<uint8_t>(size);
        for(size_t i = 0; i < size; ++i)
            packet.data[i] = data[i];
        return true;
    }

    bool Empty() const { return read_ == write_; }
    Packet& Front() { return packets_[read_]; }
    void Pop()
    {
        if(!Empty())
            ++read_;
        if(Empty())
            Clear();
    }
    void Clear() { read_ = write_ = 0; }

  private:
    std::array<Packet, kCapacity> packets_{};
    size_t read_ = 0, write_ = 0;
};
