// Pure lane state machine. No hardware, no heap, no clock: everything arrives
// through Inputs/Events and leaves through Outputs, so it is fully host-testable.
#pragma once
#include "config.h"
#include "types.h"
namespace pf {

class LaneFsm {
 public:
  explicit LaneFsm(const Config& c = Config()) : cfg_(c) {}
  // One control tick. `out` is fully overwritten.
  void step(const Inputs& in, const Events& ev, Outputs& out);

  State state() const { return state_; }
  Fault fault() const { return fault_; }
  HoldReason hold_reason() const { return hold_; }
  bool link_ok() const { return link_ok_; }
  uint32_t veh_seq() const { return veh_seq_; }
  uint8_t reversals() const { return reversals_; }
  const Config& config() const { return cfg_; }

 private:
  void enter(State s, uint32_t now);
  void post_reset(const Inputs& in);
  void update_link(const Inputs& in, const Events& ev);
  void update_mains(const Inputs& in);
  bool oc_trip(const Inputs& in);
  void begin_travel(MotorCmd c, uint32_t now);
  void to_fault(Fault f, uint32_t now);
  void start_reverse(const Inputs& in);
  void decorate(const Inputs& in, Outputs& out) const;
  void check_hold(const Inputs& in);
  void finish_cycle(uint32_t now);
  void consider_tag(const TagFrame& t, uint32_t now);
  bool locked(uint32_t now) const;
  bool link_lost(uint32_t now) const { return !link_ok_ && (seen_hb_ || now - t_boot_ >= cfg_.link_boot_grace_ms); }
  // opening drive shared by BARRIER_OPEN and OPEN_HOLD; true when lim_up reached
  bool drive_open(const Inputs& in, MotorCmd& m);
  uint32_t age(uint32_t now) const { return now - t_enter_; }

  Config cfg_;
  State state_ = State::IDLE;
  Fault fault_ = Fault::NONE;
  HoldReason hold_ = HoldReason::NONE;
  bool started_ = false;
  uint32_t t_enter_ = 0;
  // link
  bool link_ok_ = false;
  uint32_t t_boot_ = 0, t_last_hb_ = 0, t_recover_start_ = 0;
  bool seen_hb_ = false;
  // mains
  bool mains_down_ = false;
  uint32_t t_mains_bad_ = 0, t_mains_good_ = 0;
  // cycle
  uint32_t veh_seq_ = 0;
  uint32_t t_lockout_until_ = 0;
  bool lockout_active_ = false;
  bool have_tag_ = false;
  TagFrame best_;
  uint32_t best_ts_ = 0, first_tag_ts_ = 0;
  uint8_t n_distinct_ = 0;
  uint8_t distinct_[4][kMaxEpc]; uint8_t distinct_len_[4];
  Decision decision_ = Decision::NONE;
  // motion
  MotorCmd cmd_ = MotorCmd::STOP;
  uint32_t t_travel_ = 0;
  uint32_t t_oc_since_ = 0; bool oc_pending_ = false;
  bool homing_ = false, reversing_ = false, passed_ = false;
  uint32_t t_clear_since_ = 0; bool clear_run_ = false;
  uint8_t reversals_ = 0;
  bool lockout_pending_ = false;
  bool recover_run_ = false, mains_bad_run_ = false, mains_good_run_ = false;
  uint32_t t_reverse_ = 0;
};

const char* state_name(State s);
const char* fault_name(Fault f);
}  // namespace pf
