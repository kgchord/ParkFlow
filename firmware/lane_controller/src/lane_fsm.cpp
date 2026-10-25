#include "lane_fsm.h"
#include <cstring>
namespace pf {

static bool before(uint32_t a, uint32_t b) { return static_cast<int32_t>(a - b) < 0; }

const char* state_name(State s) {
  static const char* n[] = {"IDLE", "VEHICLE_DETECTED", "READ", "FUSE", "GRANT", "FALLBACK",
                            "BARRIER_OPEN", "CLEAR", "BARRIER_CLOSE", "OPEN_HOLD", "FAULT", "ESTOP"};
  return static_cast<unsigned>(s) < static_cast<unsigned>(State::COUNT_) ? n[static_cast<unsigned>(s)] : "?";
}
const char* fault_name(Fault f) {
  switch (f) {
    case Fault::NONE: return "NONE";
    case Fault::OPEN_TIMEOUT: return "OPEN_TIMEOUT";
    case Fault::CLOSE_TIMEOUT: return "CLOSE_TIMEOUT";
    case Fault::OVERCURRENT_STALL: return "OVERCURRENT_STALL";
    case Fault::LIMIT_CONFLICT: return "LIMIT_CONFLICT";
    case Fault::OBSTRUCTION_LOCKOUT: return "OBSTRUCTION_LOCKOUT";
  }
  return "?";
}

void LaneFsm::enter(State s, uint32_t now) {
  state_ = s;
  t_enter_ = now;
  if (s == State::CLEAR) clear_run_ = false;
}

void LaneFsm::begin_travel(MotorCmd c, uint32_t now) {
  cmd_ = c;
  t_travel_ = now;
  oc_pending_ = false;
}

void LaneFsm::to_fault(Fault f, uint32_t now) {
  fault_ = f;
  cmd_ = MotorCmd::STOP;
  enter(State::FAULT, now);
}

bool LaneFsm::locked(uint32_t now) const { return lockout_active_ && before(now, t_lockout_until_); }

void LaneFsm::finish_cycle(uint32_t now) {
  lockout_active_ = true;
  t_lockout_until_ = now + cfg_.retrigger_lockout_ms;
  have_tag_ = false;
  cmd_ = MotorCmd::STOP;
  enter(State::IDLE, now);
}

// Decide where to go after power-up, E-stop re-arm or fault reset. Barrier
// position is unknown unless a limit switch says otherwise, so the only
// motion ever started here is OPENING (the safe direction).
void LaneFsm::post_reset(const Inputs& in) {
  const uint32_t now = in.now_ms;
  fault_ = Fault::NONE;
  hold_ = HoldReason::NONE;
  reversals_ = 0;
  lockout_pending_ = false;
  homing_ = false;
  reversing_ = false;
  passed_ = false;
  cmd_ = MotorCmd::STOP;
  if (in.lim_up && in.lim_dn) {
    to_fault(Fault::LIMIT_CONFLICT, now);
  } else if (in.lim_dn) {
    enter(State::IDLE, now);
  } else if (in.lim_up) {
    enter(State::CLEAR, now);
  } else {
    homing_ = true;
    begin_travel(MotorCmd::OPEN, now);
    enter(State::BARRIER_OPEN, now);
  }
}

void LaneFsm::update_link(const Inputs& in, const Events& ev) {
  const uint32_t now = in.now_ms;
  if (ev.heartbeat) {
    if (!seen_hb_) {
      seen_hb_ = true;
      link_ok_ = true;
    } else if (!link_ok_) {
      if (!recover_run_ || now - t_last_hb_ > cfg_.heartbeat_timeout_ms) {
        recover_run_ = true;
        t_recover_start_ = now;
      } else if (now - t_recover_start_ >= cfg_.link_recover_ms) {
        link_ok_ = true;
        recover_run_ = false;
      }
    }
    t_last_hb_ = now;
  }
  if (link_ok_ && now - t_last_hb_ > cfg_.heartbeat_timeout_ms) {
    link_ok_ = false;
    recover_run_ = false;
  }
}

void LaneFsm::update_mains(const Inputs& in) {
  const uint32_t now = in.now_ms;
  if (!in.ac_ok) {
    mains_good_run_ = false;
    if (!mains_down_) {
      if (!mains_bad_run_) { mains_bad_run_ = true; t_mains_bad_ = now; }
      if (now - t_mains_bad_ >= cfg_.mains_loss_debounce_ms) mains_down_ = true;
    }
  } else {
    mains_bad_run_ = false;
    if (mains_down_) {
      if (!mains_good_run_) { mains_good_run_ = true; t_mains_good_ = now; }
      if (now - t_mains_good_ >= cfg_.mains_recover_ms) { mains_down_ = false; mains_good_run_ = false; }
    }
  }
}

bool LaneFsm::oc_trip(const Inputs& in) {
  if (cmd_ == MotorCmd::STOP || in.now_ms - t_travel_ < cfg_.inrush_blank_ms) { oc_pending_ = false; return false; }
  if (in.isense_mv > cfg_.oc_threshold_mv) {
    if (!oc_pending_) { oc_pending_ = true; t_oc_since_ = in.now_ms; }
    return in.now_ms - t_oc_since_ >= cfg_.oc_hold_ms;
  }
  oc_pending_ = false;
  return false;
}

void LaneFsm::check_hold(const Inputs& in) {
  if (state_ == State::OPEN_HOLD || state_ == State::FAULT || state_ == State::ESTOP) return;
  if (cfg_.link_policy != LinkLossPolicy::FAIL_OPEN_HOLD) return;  // fail-secure: no automatic opening
  const uint32_t now = in.now_ms;
  HoldReason r = HoldReason::NONE;
  if (mains_down_) r = HoldReason::MAINS_LOSS;
  else if (link_lost(now)) r = HoldReason::LINK_LOSS;
  if (r == HoldReason::NONE) return;
  hold_ = r;
  homing_ = false;
  reversing_ = (cmd_ == MotorCmd::CLOSE);  // dead time before flipping direction
  t_reverse_ = now;
  begin_travel(in.lim_up ? MotorCmd::STOP : MotorCmd::OPEN, now);
  enter(State::OPEN_HOLD, now);
}

void LaneFsm::consider_tag(const TagFrame& t, uint32_t now) {
  if (t.has_rssi && t.rssi < cfg_.min_rssi) return;
  bool known = false;
  for (uint8_t i = 0; i < n_distinct_ && i < 4; ++i)
    if (distinct_len_[i] == t.epc_len && std::memcmp(distinct_[i], t.epc, t.epc_len) == 0) known = true;
  if (!known && n_distinct_ < 4) {
    std::memcpy(distinct_[n_distinct_], t.epc, t.epc_len);
    distinct_len_[n_distinct_] = t.epc_len;
    ++n_distinct_;
  }
  if (!have_tag_) {
    have_tag_ = true;
    first_tag_ts_ = now;
    best_ = t;
    best_ts_ = now;
  } else if (t.has_rssi && (!best_.has_rssi || t.rssi >= best_.rssi)) {
    best_ = t;
    best_ts_ = now;  // time of peak RSSI (R2 mitigation: fusion window is anchored on it)
  }
}

bool LaneFsm::drive_open(const Inputs& in, MotorCmd& m) {
  const uint32_t now = in.now_ms;
  if (in.lim_up) { cmd_ = MotorCmd::STOP; m = MotorCmd::STOP; return true; }
  if (cmd_ != MotorCmd::OPEN) begin_travel(MotorCmd::OPEN, now);
  // dead time after a reversal so the bridge never flips direction at speed
  m = (reversing_ && now - t_reverse_ < cfg_.reverse_dead_ms) ? MotorCmd::STOP : MotorCmd::OPEN;
  if (m == MotorCmd::OPEN && oc_trip(in)) { to_fault(Fault::OVERCURRENT_STALL, now); m = MotorCmd::STOP; return false; }
  if (now - t_travel_ >= cfg_.travel_timeout_ms()) { to_fault(Fault::OPEN_TIMEOUT, now); m = MotorCmd::STOP; }
  return false;
}

void LaneFsm::start_reverse(const Inputs& in) {
  const uint32_t now = in.now_ms;
  if (reversals_ < 255) ++reversals_;
  if (reversals_ > cfg_.max_reversals) lockout_pending_ = true;
  reversing_ = true;
  t_reverse_ = now;
  begin_travel(MotorCmd::OPEN, now);
  enter(State::BARRIER_OPEN, now);
}

void LaneFsm::step(const Inputs& in, const Events& ev, Outputs& out) {
  out = Outputs();
  const uint32_t now = in.now_ms;
  MotorCmd m = MotorCmd::STOP;
  bool contactor = true;

  if (!started_) {
    started_ = true;
    t_boot_ = now;
    post_reset(in);
  }
  update_link(in, ev);
  update_mains(in);

  // ---- global priorities -------------------------------------------------
  if (!in.estop_ok) {
    if (state_ != State::ESTOP) { cmd_ = MotorCmd::STOP; reversing_ = false; enter(State::ESTOP, now); }
  } else if (state_ == State::ESTOP && ev.rearm) {
    post_reset(in);
  }
  if (state_ == State::FAULT && ev.fault_reset && in.estop_ok) post_reset(in);
  if (state_ != State::ESTOP && state_ != State::FAULT && in.lim_up && in.lim_dn) to_fault(Fault::LIMIT_CONFLICT, now);
  check_hold(in);

  // ---- per-state behaviour ----------------------------------------------
  switch (state_) {
    case State::IDLE: {
      const bool lk = locked(now);
      const bool secure_offline = cfg_.link_policy == LinkLossPolicy::FAIL_SECURE && link_lost(now);
      const bool trig = !secure_offline && (in.presence || (!lk && (ev.edge_vehicle || ev.tag)));
      if (trig) {
        ++veh_seq_;
        have_tag_ = false; n_distinct_ = 0; passed_ = false; decision_ = Decision::NONE;
        reversals_ = 0;
        if (ev.tag) consider_tag(ev.tag_frame, now);
        TxEvent& t = out.tx[out.n_tx++];
        t.type = TxType::VEH; t.seq = veh_seq_; t.t_ms = now;
        enter(State::VEHICLE_DETECTED, now);
      }
      break;
    }
    case State::VEHICLE_DETECTED:
      enter(State::READ, now);  // reader inventory is (re)started by the app layer on VEH
      break;
    case State::READ: {
      if (ev.tag) consider_tag(ev.tag_frame, now);
      const bool settled = have_tag_ && now - first_tag_ts_ >= cfg_.read_settle_ms;
      if (settled || age(now) >= cfg_.read_window_ms) {
        TxEvent& t = out.tx[out.n_tx++];
        t.seq = veh_seq_;
        t.t_ms = now;
        if (have_tag_) { t.type = TxType::TAG; t.tag = best_; t.peak_ms = best_ts_; t.n_distinct = n_distinct_; }
        else t.type = TxType::NOTAG;
        enter(State::FUSE, now);
      }
      break;
    }
    case State::FUSE:
      if (ev.decision && ev.decision_seq == veh_seq_ && ev.decision_val != Decision::NONE) {
        decision_ = ev.decision_val;
        enter(decision_ == Decision::GRANT ? State::GRANT : State::FALLBACK, now);
      } else if (age(now) >= cfg_.decision_timeout_ms) {
        decision_ = Decision::NONE;
        enter(State::FALLBACK, now);
      }
      break;
    case State::GRANT:
      begin_travel(MotorCmd::OPEN, now);
      reversing_ = false;
      enter(State::BARRIER_OPEN, now);
      break;
    case State::FALLBACK:
      if (ev.guard_open) enter(State::GRANT, now);
      else if (age(now) >= cfg_.fallback_timeout_ms) finish_cycle(now);
      break;
    case State::BARRIER_OPEN: {
      if (!in.beam_clear || in.presence) passed_ = true;
      const bool up = drive_open(in, m);
      if (state_ == State::BARRIER_OPEN && up) {
        const bool lock = lockout_pending_;
        reversing_ = false; homing_ = false;
        if (lock) to_fault(Fault::OBSTRUCTION_LOCKOUT, now);
        else enter(State::CLEAR, now);
      }
      break;
    }
    case State::CLEAR: {
      if (!in.beam_clear || in.presence) { passed_ = true; clear_run_ = false; }
      else if (!clear_run_) { clear_run_ = true; t_clear_since_ = now; }
      const bool dwell = clear_run_ && now - t_clear_since_ >= cfg_.clear_dwell_ms;
      if (dwell && (passed_ || age(now) >= cfg_.no_pass_close_ms)) {
        if (passed_) { TxEvent& t = out.tx[out.n_tx++]; t.type = TxType::PASS; t.seq = veh_seq_; t.t_ms = now; }
        begin_travel(MotorCmd::CLOSE, now);
        enter(State::BARRIER_CLOSE, now);
      }
      break;
    }
    case State::BARRIER_CLOSE: {
      m = MotorCmd::CLOSE;
      if (!in.beam_clear || in.presence) {              // anti-crush rule 1: reverse on beam/presence
        m = MotorCmd::STOP;
        start_reverse(in);
        TxEvent& t = out.tx[out.n_tx++]; t.type = TxType::REVERSED; t.seq = veh_seq_; t.t_ms = now;
      } else if (oc_trip(in)) {                         // anti-crush rule 2: reverse on over-current
        m = MotorCmd::STOP;
        start_reverse(in);
        TxEvent& t = out.tx[out.n_tx++]; t.type = TxType::REVERSED; t.seq = veh_seq_; t.t_ms = now;
      } else if (in.lim_dn) {
        m = MotorCmd::STOP;
        reversals_ = 0;
        finish_cycle(now);
      } else if (now - t_travel_ >= cfg_.travel_timeout_ms()) {
        m = MotorCmd::STOP;
        to_fault(Fault::CLOSE_TIMEOUT, now);
      }
      break;
    }
    case State::OPEN_HOLD: {
      if (!(mains_down_ || link_lost(now))) {
        hold_ = HoldReason::NONE;
        reversing_ = false;
        passed_ = false;
        cmd_ = MotorCmd::STOP;
        enter(State::CLEAR, now);  // re-closes only after the normal clear-dwell rules
        break;
      }
      hold_ = mains_down_ ? HoldReason::MAINS_LOSS : HoldReason::LINK_LOSS;
      const bool up = drive_open(in, m);
      if (state_ == State::OPEN_HOLD && up && hold_ == HoldReason::MAINS_LOSS) contactor = false;  // save UPS energy
      break;
    }
    case State::FAULT:
    case State::ESTOP:
      contactor = false;
      break;
    case State::COUNT_: break;
  }

  // ---- final safety gate (belt and braces, independent of the state logic) --
  if (m == MotorCmd::CLOSE && (!in.beam_clear || in.presence || !in.estop_ok || state_ != State::BARRIER_CLOSE)) m = MotorCmd::STOP;
  if (!in.estop_ok || state_ == State::FAULT || state_ == State::ESTOP) { m = MotorCmd::STOP; contactor = false; }
  out.motor = m;
  out.contactor = contactor;
  decorate(in, out);
}

void LaneFsm::decorate(const Inputs& in, Outputs& out) const {
  out.led = LedColor::GREEN; out.led_mode = LedMode::SOLID; out.buzz = Buzz::OFF; out.sign = Sign::WELCOME;
  switch (state_) {
    case State::IDLE:
      out.led_mode = LedMode::BLINK_SLOW;
      if (link_lost(in.now_ms)) { out.led = LedColor::AMBER; out.sign = Sign::SEE_GUARD; }
      break;
    case State::VEHICLE_DETECTED: case State::READ: case State::FUSE:
      out.led = LedColor::BLUE; out.sign = Sign::PLEASE_WAIT; break;
    case State::GRANT: out.sign = Sign::GRANTED; break;
    case State::BARRIER_OPEN:
      out.sign = Sign::GRANTED;
      if (reversing_) {
        out.led = LedColor::AMBER; out.led_mode = LedMode::BLINK_FAST; out.sign = Sign::OBSTACLE;
        if (in.now_ms - t_reverse_ < 2000) out.buzz = Buzz::ALARM_FAST;
      } else if (homing_) {
        out.led = LedColor::AMBER; out.led_mode = LedMode::BLINK_SLOW; out.sign = Sign::LANE_CLOSED;
      }
      break;
    case State::CLEAR: out.sign = Sign::GRANTED; break;
    case State::BARRIER_CLOSE:
      out.led = LedColor::AMBER; out.led_mode = LedMode::BLINK_FAST; out.buzz = Buzz::BEEP_SHORT_1S; out.sign = Sign::CLOSING; break;
    case State::FALLBACK:
      out.led = LedColor::AMBER; out.buzz = Buzz::DOUBLE_BEEP_3S; out.sign = Sign::SEE_GUARD; break;
    case State::OPEN_HOLD:
      out.led = LedColor::AMBER; out.led_mode = LedMode::BLINK_SLOW; out.buzz = Buzz::SLOW_PULSE_5S; out.sign = Sign::LANE_OPEN; break;
    case State::FAULT:
      out.led = LedColor::RED; out.led_mode = LedMode::FAULT_CODE; out.led_n = static_cast<uint8_t>(fault_);
      out.buzz = Buzz::FAULT_TRIPLE; out.sign = Sign::LANE_CLOSED; break;
    case State::ESTOP:
      out.led = LedColor::RED; out.buzz = Buzz::LONG_2S; out.sign = Sign::STOPPED; break;
    case State::COUNT_: break;
  }
}

}  // namespace pf
