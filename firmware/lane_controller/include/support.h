// Small pure helpers: asymmetric debouncer and multi-task liveness supervisor.
#pragma once
#include <cstdint>
namespace pf {

// Output changes to true only after raw has been true for rise_ms, to false only
// after raw has been false for fall_ms. Safety inputs use 0 ms in the unsafe
// direction so a beam break / presence is never delayed.
class Debounce {
 public:
  Debounce(bool initial, uint32_t rise_ms, uint32_t fall_ms) : out_(initial), rise_(rise_ms), fall_(fall_ms) {}
  bool update(bool raw, uint32_t now) {
    if (raw == out_) { pending_ = false; return out_; }
    if (!pending_) { pending_ = true; t0_ = now; }
    if (now - t0_ >= (raw ? rise_ : fall_)) { out_ = raw; pending_ = false; }
    return out_;
  }
  bool value() const { return out_; }
 private:
  bool out_, pending_ = false;
  uint32_t rise_, fall_, t0_ = 0;
};

// Software side of the watchdog chain: every registered task must check in
// within its deadline before the external TPS3823 WDI pin is toggled.
class TaskSupervisor {
 public:
  static constexpr int kMax = 4;
  void configure(int id, uint32_t deadline_ms) { if (id >= 0 && id < kMax) { dl_[id] = deadline_ms; used_[id] = true; } }
  void checkin(int id, uint32_t now) { if (id >= 0 && id < kMax) last_[id] = now; }
  bool healthy(uint32_t now) const {
    for (int i = 0; i < kMax; ++i) if (used_[i] && now - last_[i] > dl_[i]) return false;
    return true;
  }
 private:
  uint32_t dl_[kMax] = {}, last_[kMax] = {};
  bool used_[kMax] = {};
};
}  // namespace pf
