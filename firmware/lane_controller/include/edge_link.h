// Edge Node <-> Lane Controller link (UART0, 3.3 V TTL, 115200 8N1 target).
// ASCII lines with XOR checksum so a human can read them on a serial monitor:
//     $TYPE,arg,arg*HH\n        HH = XOR of every byte between '$' and '*', hex
// Edge -> Controller: HB,<n>  DEC,<seq>,<G|F|D>,<reason>  GUARD  REARM  RESET
// Controller -> Edge: VEH,<seq>,<ms>  TAG,<seq>,<epchex>,<rssi|NA>,<peak_ms>,<ndistinct>
//                     NOTAG,<seq>  PASS,<seq>  REV,<seq>  ST,<state>,<fault>,<flags>,<v24_mv>
// This is a project-defined protocol (not a standard).
#pragma once
#include <cstddef>
#include <cstdint>
#include "types.h"
namespace pf {

enum class EdgeMsgType : uint8_t { NONE, HB, DEC, GUARD, REARM, RESET };
struct EdgeMsg {
  EdgeMsgType type = EdgeMsgType::NONE;
  uint32_t n = 0;               // HB counter or DEC seq
  Decision decision = Decision::NONE;
  uint8_t reason = 0;
};

// Returns bytes written (without NUL), 0 if cap too small.
size_t encode_tx_event(char* buf, size_t cap, const TxEvent& e);
size_t encode_status(char* buf, size_t cap, State s, Fault f, uint8_t flags, uint16_t v24_mv);

class EdgeLineParser {
 public:
  // feed one byte; returns true when a valid message has been decoded into `m`
  bool push(uint8_t b, EdgeMsg& m);
  uint32_t bad_checksum() const { return bad_ck_; }
  uint32_t malformed() const { return bad_fmt_; }
 private:
  char line_[96];
  size_t n_ = 0;
  bool in_ = false;
  uint32_t bad_ck_ = 0, bad_fmt_ = 0;
};
}  // namespace pf
