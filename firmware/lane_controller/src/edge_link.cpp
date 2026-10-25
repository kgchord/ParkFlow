#include "edge_link.h"
#include "lane_fsm.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
namespace pf {

static uint8_t xor_ck(const char* s, size_t n) { uint8_t c = 0; for (size_t i = 0; i < n; ++i) c ^= static_cast<uint8_t>(s[i]); return c; }

static size_t finish(char* buf, size_t cap, size_t body_len) {  // buf[0]='$', body already written after it
  if (body_len + 6 > cap) return 0;
  const uint8_t ck = xor_ck(buf + 1, body_len - 1);
  int k = std::snprintf(buf + body_len, cap - body_len, "*%02X\n", ck);
  return k > 0 ? body_len + static_cast<size_t>(k) : 0;
}

size_t encode_tx_event(char* buf, size_t cap, const TxEvent& e) {
  int k = 0;
  switch (e.type) {
    case TxType::VEH: k = std::snprintf(buf, cap, "$VEH,%u,%u", (unsigned)e.seq, (unsigned)e.t_ms); break;
    case TxType::NOTAG: k = std::snprintf(buf, cap, "$NOTAG,%u", (unsigned)e.seq); break;
    case TxType::PASS: k = std::snprintf(buf, cap, "$PASS,%u", (unsigned)e.seq); break;
    case TxType::REVERSED: k = std::snprintf(buf, cap, "$REV,%u", (unsigned)e.seq); break;
    case TxType::TAG: {
      char hex[kMaxEpc * 2 + 1];
      for (uint8_t i = 0; i < e.tag.epc_len; ++i) std::snprintf(hex + i * 2, 3, "%02X", e.tag.epc[i]);
      hex[e.tag.epc_len * 2] = 0;
      char rs[8];
      if (e.tag.has_rssi) std::snprintf(rs, sizeof rs, "%d", (int)e.tag.rssi); else std::snprintf(rs, sizeof rs, "NA");
      k = std::snprintf(buf, cap, "$TAG,%u,%s,%s,%u,%u", (unsigned)e.seq, hex, rs, (unsigned)e.peak_ms, (unsigned)e.n_distinct);
      break;
    }
    case TxType::NONE: return 0;
  }
  if (k <= 0 || static_cast<size_t>(k) >= cap) return 0;
  return finish(buf, cap, static_cast<size_t>(k));
}

size_t encode_status(char* buf, size_t cap, State s, Fault f, uint8_t flags, uint16_t v24_mv) {
  int k = std::snprintf(buf, cap, "$ST,%s,%s,%u,%u", state_name(s), fault_name(f), (unsigned)flags, (unsigned)v24_mv);
  if (k <= 0 || static_cast<size_t>(k) >= cap) return 0;
  return finish(buf, cap, static_cast<size_t>(k));
}

static int hexv(char c) {
  if (c >= '0' && c <= '9') return c - '0';
  if (c >= 'A' && c <= 'F') return c - 'A' + 10;
  if (c >= 'a' && c <= 'f') return c - 'a' + 10;
  return -1;
}

bool EdgeLineParser::push(uint8_t b, EdgeMsg& m) {
  if (b == '$') { in_ = true; n_ = 0; return false; }
  if (!in_) return false;
  if (b == '\r') return false;
  if (b != '\n') {
    if (n_ + 1 >= sizeof(line_)) { in_ = false; ++bad_fmt_; return false; }
    line_[n_++] = static_cast<char>(b);
    return false;
  }
  in_ = false;
  line_[n_] = 0;
  // locate '*HH'
  if (n_ < 3 || line_[n_ - 3] != '*') { ++bad_fmt_; return false; }
  const int h1 = hexv(line_[n_ - 2]), h2 = hexv(line_[n_ - 1]);
  if (h1 < 0 || h2 < 0) { ++bad_fmt_; return false; }
  if (xor_ck(line_, n_ - 3) != static_cast<uint8_t>(h1 * 16 + h2)) { ++bad_ck_; return false; }
  line_[n_ - 3] = 0;
  char* tok = line_;
  char* comma = std::strchr(tok, ',');
  if (comma) *comma = 0;
  const char* rest = comma ? comma + 1 : "";
  m = EdgeMsg();
  if (!std::strcmp(tok, "HB")) { m.type = EdgeMsgType::HB; m.n = (uint32_t)std::strtoul(rest, nullptr, 10); return true; }
  if (!std::strcmp(tok, "GUARD")) { m.type = EdgeMsgType::GUARD; return true; }
  if (!std::strcmp(tok, "REARM")) { m.type = EdgeMsgType::REARM; return true; }
  if (!std::strcmp(tok, "RESET")) { m.type = EdgeMsgType::RESET; return true; }
  if (!std::strcmp(tok, "DEC")) {
    char* e1 = nullptr;
    unsigned long seq = std::strtoul(rest, &e1, 10);
    if (!e1 || *e1 != ',') { ++bad_fmt_; return false; }
    const char d = e1[1];
    if (d == 'G') m.decision = Decision::GRANT; else if (d == 'F') m.decision = Decision::FALLBACK;
    else if (d == 'D') m.decision = Decision::DENY; else { ++bad_fmt_; return false; }
    const char* r = std::strchr(e1 + 1, ',');
    m.reason = r ? (uint8_t)std::strtoul(r + 1, nullptr, 10) : 0;
    m.type = EdgeMsgType::DEC; m.n = (uint32_t)seq;
    return true;
  }
  ++bad_fmt_;
  return false;
}
}  // namespace pf
