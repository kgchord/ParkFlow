#include "rfid_parser.h"
#include <cstring>
namespace pf {

size_t crc_len(CrcType t) {
  switch (t) {
    case CrcType::NONE: return 0;
    case CrcType::SUM8: case CrcType::XOR8: return 1;
    default: return 2;
  }
}

uint16_t crc_compute(CrcType t, const uint8_t* d, size_t n) {
  uint16_t c = 0;
  switch (t) {
    case CrcType::NONE: return 0;
    case CrcType::SUM8: for (size_t i = 0; i < n; ++i) c = static_cast<uint8_t>(c + d[i]); return c;
    case CrcType::XOR8: for (size_t i = 0; i < n; ++i) c ^= d[i]; return c & 0xFF;
    case CrcType::CRC16_CCITT_FALSE:
      c = 0xFFFF;
      for (size_t i = 0; i < n; ++i) {
        c ^= static_cast<uint16_t>(d[i]) << 8;
        for (int k = 0; k < 8; ++k) c = (c & 0x8000) ? static_cast<uint16_t>((c << 1) ^ 0x1021) : static_cast<uint16_t>(c << 1);
      }
      return c;
    case CrcType::CRC16_ARC: case CrcType::CRC16_MODBUS:
      c = (t == CrcType::CRC16_MODBUS) ? 0xFFFF : 0x0000;
      for (size_t i = 0; i < n; ++i) {
        c ^= d[i];
        for (int k = 0; k < 8; ++k) c = (c & 1) ? static_cast<uint16_t>((c >> 1) ^ 0xA001) : static_cast<uint16_t>(c >> 1);
      }
      return c;
  }
  return 0;
}

// INVENTED example layout (tests only):
// A5 5A | LEN(total) | TYPE=0x01 | RSSI(int8) | EPC_LEN | EPC... | CRC16-CCITT-FALSE (BE) over [LEN..EPC end]
const RfidFrameCfg kIllustrativeProfile = [] {
  RfidFrameCfg c;
  c.sof[0] = 0xA5; c.sof[1] = 0x5A; c.sof_len = 2;
  c.len_offset = 2; c.len_adjust = 0;
  c.min_total = 2 + 1 + 1 + 1 + 1 + 2;
  c.max_total = 2 + 1 + 1 + 1 + 1 + kMaxEpc + 2;
  c.crc = CrcType::CRC16_CCITT_FALSE; c.crc_big_endian = true; c.crc_start = 2;
  c.filter_type = true; c.type_offset = 3; c.type_tag_notify = 0x01;
  c.rssi_offset = 4; c.rssi_signed = true;
  c.epc_len_offset = 5; c.epc_offset = 6;
  return c;
}();

size_t illustrative_encode(uint8_t* out, size_t cap, const uint8_t* epc, uint8_t epc_len, int8_t rssi) {
  const size_t total = 6 + epc_len + 2;
  if (total > cap) return 0;
  out[0] = 0xA5; out[1] = 0x5A; out[2] = static_cast<uint8_t>(total); out[3] = 0x01;
  out[4] = static_cast<uint8_t>(rssi); out[5] = epc_len;
  std::memcpy(out + 6, epc, epc_len);
  const uint16_t c = crc_compute(CrcType::CRC16_CCITT_FALSE, out + 2, total - 2 - 2);
  out[total - 2] = static_cast<uint8_t>(c >> 8);
  out[total - 1] = static_cast<uint8_t>(c & 0xFF);
  return total;
}

void RfidParser::drop(size_t k) {
  if (k >= n_) { n_ = 0; return; }
  std::memmove(buf_, buf_ + k, n_ - k);
  n_ -= k;
}

void RfidParser::push(uint8_t b) {
  if (n_ >= sizeof(buf_)) { drop(1); ++st_.overflow; }
  buf_[n_++] = b;
  scan();
}

void RfidParser::scan() {
  const RfidFrameCfg& c = cfg_;
  for (;;) {
    // 1. align on SOF
    while (n_ > 0) {
      bool ok = true;
      for (uint8_t i = 0; i < c.sof_len && i < n_; ++i) if (buf_[i] != c.sof[i]) { ok = false; break; }
      if (ok) break;
      drop(1); ++st_.resync_drops;
    }
    if (n_ <= c.len_offset) return;                         // need the length byte
    const int total = static_cast<int>(buf_[c.len_offset]) + c.len_adjust;
    if (total < c.min_total || total > c.max_total || total > static_cast<int>(sizeof(buf_))) {
      drop(1); ++st_.bad_len; continue;
    }
    if (n_ < static_cast<size_t>(total)) return;            // wait for more bytes
    const size_t cl = crc_len(c.crc);
    if (cl) {
      const size_t body_end = static_cast<size_t>(total) - cl;
      if (c.crc_start > body_end) { drop(1); ++st_.bad_len; continue; }
      const uint16_t calc = crc_compute(c.crc, buf_ + c.crc_start, body_end - c.crc_start);
      uint16_t got;
      if (cl == 1) got = buf_[body_end];
      else got = c.crc_big_endian ? static_cast<uint16_t>((buf_[body_end] << 8) | buf_[body_end + 1])
                                  : static_cast<uint16_t>((buf_[body_end + 1] << 8) | buf_[body_end]);
      if (calc != got) { drop(1); ++st_.bad_crc; continue; }
    }
    // frame is structurally valid
    if (c.filter_type && (c.type_offset >= total || buf_[c.type_offset] != c.type_tag_notify)) {
      ++st_.other; drop(static_cast<size_t>(total)); continue;
    }
    uint8_t elen = (c.epc_len_offset == 0xFF) ? c.epc_len_fixed : (c.epc_len_offset < total ? buf_[c.epc_len_offset] : 0);
    if (elen == 0 || elen > kMaxEpc || c.epc_offset + elen > total) { ++st_.bad_len; drop(static_cast<size_t>(total)); continue; }
    TagFrame t;
    t.epc_len = elen;
    std::memcpy(t.epc, buf_ + c.epc_offset, elen);
    if (c.rssi_offset != 0xFF && c.rssi_offset < total) {
      t.has_rssi = true;
      t.rssi = c.rssi_signed ? static_cast<int16_t>(static_cast<int8_t>(buf_[c.rssi_offset])) : static_cast<int16_t>(buf_[c.rssi_offset]);
    }
    if ((qt_ + 1) % 8 == qh_) qh_ = (qh_ + 1) % 8;          // queue full: drop oldest
    q_[qt_] = t;
    qt_ = (qt_ + 1) % 8;
    ++st_.frames_ok;
    drop(static_cast<size_t>(total));
  }
}

bool RfidParser::pop(TagFrame& out) {
  if (qh_ == qt_) return false;
  out = q_[qh_];
  qh_ = (qh_ + 1) % 8;
  return true;
}

}  // namespace pf
