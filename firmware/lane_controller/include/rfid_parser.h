// Generic, configurable RS485 UHF-reader frame parser.
//
// !! The exact reader's command set is UNVERIFIED. The ParkFlow BOM names an
// !! integrated 865-867 MHz EPC Gen2 reader with RS485, but its vendor frame
// !! format has not been checked against a datasheet or a physical unit.
// !! This parser therefore describes a frame layout with data (RfidFrameCfg)
// !! instead of hard-coding one vendor protocol. kIllustrativeProfile is an
// !! invented example used only by the tests; it is NOT any real reader's format.
#pragma once
#include <cstddef>
#include <cstdint>
#include "types.h"
namespace pf {

enum class CrcType : uint8_t { NONE, SUM8, XOR8, CRC16_CCITT_FALSE, CRC16_ARC, CRC16_MODBUS };

uint16_t crc_compute(CrcType t, const uint8_t* d, size_t n);
size_t crc_len(CrcType t);

struct RfidFrameCfg {
  uint8_t sof[2] = {0, 0};
  uint8_t sof_len = 0;           // 0..2
  uint8_t len_offset = 0;        // offset (from frame start) of the length byte
  int8_t  len_adjust = 0;        // total_frame_len = length_byte + len_adjust
  uint8_t min_total = 4;
  uint8_t max_total = 64;
  CrcType crc = CrcType::NONE;
  bool    crc_big_endian = true; // trailing CRC bytes order
  uint8_t crc_start = 0;         // CRC covers [crc_start, total - crc_len)
  bool    filter_type = false;
  uint8_t type_offset = 0;
  uint8_t type_tag_notify = 0;   // frame is a tag report when frame[type_offset] == this
  uint8_t epc_len_offset = 0xFF; // 0xFF: fixed EPC length
  uint8_t epc_len_fixed = 12;
  uint8_t epc_offset = 0;
  uint8_t rssi_offset = 0xFF;    // 0xFF: no RSSI in frame
  bool    rssi_signed = true;
  uint8_t inventory_cmd[16] = {0};  // optional bytes sent to the reader when a vehicle is detected
  uint8_t inventory_cmd_len = 0;
};

extern const RfidFrameCfg kIllustrativeProfile;

struct RfidStats { uint32_t frames_ok = 0, bad_crc = 0, bad_len = 0, resync_drops = 0, other = 0, overflow = 0; };

class RfidParser {
 public:
  explicit RfidParser(const RfidFrameCfg& c) : cfg_(c) {}
  void push(uint8_t b);                // feed one byte from the UART
  bool pop(TagFrame& out);             // next decoded tag report, if any
  const RfidStats& stats() const { return st_; }
  void reset() { n_ = 0; qh_ = qt_ = 0; }
 private:
  void drop(size_t k);
  void scan();
  const RfidFrameCfg cfg_;
  uint8_t buf_[96];
  size_t n_ = 0;
  TagFrame q_[8];
  size_t qh_ = 0, qt_ = 0;
  RfidStats st_;
};

// Test/bench helper: build a frame of the illustrative profile.
size_t illustrative_encode(uint8_t* out, size_t cap, const uint8_t* epc, uint8_t epc_len, int8_t rssi);
}  // namespace pf
