#include <cstring>
#include "lane_fsm.h"
#include "minitest.h"
using namespace pf;

namespace {
struct Rig {
  Config cfg;
  LaneFsm f;
  Inputs in;
  Events ev;
  Outputs out;
  bool auto_hb = true;
  uint32_t next_hb = 0;
  bool saw_pass = false, saw_rev = false, saw_notag = false, saw_tag = false, saw_veh = false;
  TxEvent last_tag;
  MotorCmd prev_motor = MotorCmd::STOP;
  int flips = 0;
  explicit Rig(Config c = Config(), bool closed = true) : cfg(c), f(c) {
    in.lim_dn = closed;
    in.now_ms = 1000;
    in.isense_mv = 0;
  }
  void step(uint32_t dt = 2) {
    in.now_ms += dt;
    if (auto_hb && in.now_ms >= next_hb) { ev.heartbeat = true; next_hb = in.now_ms + 1000; }
    f.step(in, ev, out);
    ev = Events();
    for (int i = 0; i < out.n_tx; ++i) {
      switch (out.tx[i].type) {
        case TxType::PASS: saw_pass = true; break;
        case TxType::REVERSED: saw_rev = true; break;
        case TxType::NOTAG: saw_notag = true; break;
        case TxType::TAG: saw_tag = true; last_tag = out.tx[i]; break;
        case TxType::VEH: saw_veh = true; break;
        default: break;
      }
    }
    if ((prev_motor == MotorCmd::OPEN && out.motor == MotorCmd::CLOSE) || (prev_motor == MotorCmd::CLOSE && out.motor == MotorCmd::OPEN)) ++flips;
    prev_motor = out.motor;
  }
  void run(uint32_t ms) { for (uint32_t t = 0; t < ms; t += 2) step(); }
  bool run_until(State s, uint32_t max_ms) { for (uint32_t t = 0; t < max_ms; t += 2) { step(); if (f.state() == s) return true; } return false; }
  void tag(uint8_t id, int16_t rssi) {
    ev.tag = true; ev.tag_frame = TagFrame(); ev.tag_frame.epc_len = 4;
    std::memset(ev.tag_frame.epc, id, 4); ev.tag_frame.has_rssi = true; ev.tag_frame.rssi = rssi;
  }
  void decide(Decision d) { ev.decision = true; ev.decision_seq = f.veh_seq(); ev.decision_val = d; }
  // physical barrier follows commands crudely: opening takes `travel` ms
  void set_open() { in.lim_dn = false; in.lim_up = true; }
  void set_closed() { in.lim_dn = true; in.lim_up = false; }
  void mid() { in.lim_dn = false; in.lim_up = false; }
  // drive through a full grant until BARRIER_CLOSE
  void grant_to_close() {
    tag(1, -40); step();
    run_until(State::FUSE, 1000);
    decide(Decision::GRANT); step();
    run_until(State::BARRIER_OPEN, 100);
    mid(); run(200);
    set_open(); run_until(State::CLEAR, 100);
  }
};
}  // namespace

TEST(boot_with_closed_limit_goes_idle) {
  Rig r; r.step();
  CHECK(r.f.state() == State::IDLE);
  CHECK(r.out.motor == MotorCmd::STOP);
  CHECK(r.out.contactor);
}

TEST(boot_with_unknown_position_homes_open_never_closes) {
  Rig r(Config(), false); r.mid();
  r.run(10);
  CHECK(r.f.state() == State::BARRIER_OPEN);
  CHECK_EQ(r.out.motor, MotorCmd::OPEN);
  r.run(500);
  r.set_open(); r.run(10);
  CHECK(r.f.state() == State::CLEAR);
  CHECK_EQ(r.out.motor, MotorCmd::STOP);
  CHECK_EQ(r.flips, 0);
}

TEST(happy_path_tag_and_plate_granted) {
  Rig r; r.step();
  r.tag(0xAB, -40); r.step();
  CHECK(r.saw_veh);
  CHECK(r.f.state() == State::VEHICLE_DETECTED);
  r.step();
  CHECK(r.f.state() == State::READ);
  CHECK(r.run_until(State::FUSE, 500));
  CHECK(r.saw_tag);
  CHECK_EQ(r.last_tag.tag.epc[0], 0xAB);
  CHECK_EQ(r.last_tag.seq, r.f.veh_seq());
  CHECK_EQ(r.out.motor, MotorCmd::STOP);            // never open before a decision
  r.decide(Decision::GRANT); r.step();
  CHECK(r.f.state() == State::GRANT);
  r.step();
  CHECK(r.f.state() == State::BARRIER_OPEN);
  r.mid(); r.step();
  CHECK_EQ(r.out.motor, MotorCmd::OPEN);
  r.set_open(); r.step();
  CHECK(r.f.state() == State::CLEAR);
  // vehicle passes: beam breaks then clears
  r.in.beam_clear = false; r.run(300);
  CHECK(r.f.state() == State::CLEAR);
  r.in.beam_clear = true; r.run(1000);
  CHECK(r.f.state() == State::CLEAR);                // dwell not elapsed yet
  CHECK(r.run_until(State::BARRIER_CLOSE, 1000));
  CHECK(r.saw_pass);
  r.mid(); r.step();
  CHECK_EQ(r.out.motor, MotorCmd::CLOSE);
  r.set_closed(); r.step();
  CHECK(r.f.state() == State::IDLE);
  CHECK_EQ(r.out.motor, MotorCmd::STOP);
}

TEST(plate_only_no_tag_reports_notag_then_can_grant) {
  Rig r; r.step();
  r.ev.edge_vehicle = true; r.step();
  CHECK(r.run_until(State::FUSE, 1000));
  CHECK(r.saw_notag);
  CHECK(!r.saw_tag);
  r.decide(Decision::GRANT); r.step();
  CHECK(r.f.state() == State::GRANT);
}

TEST(strongest_rssi_wins_and_distinct_counted) {
  Rig r; r.step();
  r.tag(0x11, -60); r.step();
  r.step(); r.tag(0x22, -30); r.step();     // stronger, different EPC (e.g. adjacent lane vs this lane)
  r.tag(0x11, -55); r.step();
  CHECK(r.run_until(State::FUSE, 1000));
  CHECK_EQ(r.last_tag.tag.epc[0], 0x22);
  CHECK_EQ(r.last_tag.n_distinct, 2);
}

TEST(decision_timeout_goes_to_fallback_and_guard_can_open) {
  Rig r; r.step();
  r.ev.edge_vehicle = true; r.step();
  CHECK(r.run_until(State::FUSE, 1000));
  CHECK(r.run_until(State::FALLBACK, r.cfg.decision_timeout_ms + 50));
  CHECK_EQ(r.out.motor, MotorCmd::STOP);
  CHECK(r.out.sign == Sign::SEE_GUARD);
  CHECK(r.out.led == LedColor::AMBER);
  r.ev.guard_open = true; r.step();
  CHECK(r.f.state() == State::GRANT);
}

TEST(deny_goes_to_fallback_and_fallback_times_out_to_idle) {
  Rig r; r.step();
  r.tag(5, -40); r.step();
  CHECK(r.run_until(State::FUSE, 1000));
  r.decide(Decision::DENY); r.step();
  CHECK(r.f.state() == State::FALLBACK);
  CHECK(r.run_until(State::IDLE, r.cfg.fallback_timeout_ms + 100));
  // lockout then retrigger allowed
  r.run(r.cfg.retrigger_lockout_ms + 100);
  r.tag(6, -40); r.step();
  CHECK(r.f.state() == State::VEHICLE_DETECTED);
}

TEST(stale_decision_sequence_is_ignored) {
  Rig r; r.step();
  r.tag(5, -40); r.step();
  CHECK(r.run_until(State::FUSE, 1000));
  r.ev.decision = true; r.ev.decision_seq = r.f.veh_seq() + 7; r.ev.decision_val = Decision::GRANT; r.step();
  CHECK(r.f.state() == State::FUSE);
  r.ev.decision = true; r.ev.decision_seq = r.f.veh_seq() - 1; r.ev.decision_val = Decision::GRANT; r.step();
  CHECK(r.f.state() == State::FUSE);
}

TEST(retrigger_lockout_after_cycle_blocks_tag_but_not_presence) {
  Rig r; r.step();
  r.grant_to_close();
  r.in.beam_clear = false; r.run(20); r.in.beam_clear = true;
  CHECK(r.run_until(State::BARRIER_CLOSE, 3000));
  r.set_closed(); r.step();
  CHECK(r.f.state() == State::IDLE);
  r.tag(9, -40); r.step();
  CHECK(r.f.state() == State::IDLE);          // same car's tag still in field: ignored
  r.in.presence = true; r.step();
  CHECK(r.f.state() == State::VEHICLE_DETECTED);
}

// ------------------------------------------------------------------ anti-crush
TEST(close_never_starts_while_beam_broken_even_after_no_pass_timeout) {
  Rig r(Config(), false); r.set_open(); r.step();
  CHECK(r.f.state() == State::CLEAR);
  r.in.beam_clear = false;
  for (int i = 0; i < 20000 / 2; ++i) { r.step(); CHECK(r.out.motor != MotorCmd::CLOSE); }
  CHECK(r.f.state() == State::CLEAR);
}

TEST(close_never_starts_while_presence_sensed) {
  Rig r(Config(), false); r.set_open(); r.step();
  r.in.presence = true;
  for (int i = 0; i < 20000 / 2; ++i) { r.step(); CHECK(r.out.motor != MotorCmd::CLOSE); }
  r.in.presence = false;
  CHECK(r.run_until(State::BARRIER_CLOSE, 5000));
}

TEST(reverse_on_beam_break_while_closing_with_dead_time) {
  Rig r; r.step();
  r.grant_to_close();
  r.in.beam_clear = false; r.step(); r.in.beam_clear = true;
  CHECK(r.run_until(State::BARRIER_CLOSE, 20000));
  r.mid(); r.run(100);
  CHECK_EQ(r.out.motor, MotorCmd::CLOSE);
  r.in.beam_clear = false; r.step();
  CHECK(r.f.state() == State::BARRIER_OPEN);
  CHECK_EQ(r.out.motor, MotorCmd::STOP);              // dead time, never a direct flip
  CHECK(r.saw_rev);
  CHECK(r.out.sign == Sign::OBSTACLE);
  r.run(r.cfg.reverse_dead_ms + 10);
  CHECK_EQ(r.out.motor, MotorCmd::OPEN);
  CHECK_EQ(r.flips, 0);
  r.in.beam_clear = true; r.set_open(); r.run(10);
  CHECK(r.f.state() == State::CLEAR);
}

TEST(reverse_on_presence_while_closing) {
  Rig r; r.step();
  r.grant_to_close();
  r.in.beam_clear = false; r.step(); r.in.beam_clear = true;
  CHECK(r.run_until(State::BARRIER_CLOSE, 20000));
  r.mid(); r.run(50);
  r.in.presence = true; r.step();
  CHECK(r.f.state() == State::BARRIER_OPEN);
  CHECK(r.saw_rev);
}

TEST(overcurrent_trips_only_after_inrush_blank_and_hold) {
  Rig r; r.step();
  r.grant_to_close();
  r.in.beam_clear = false; r.step(); r.in.beam_clear = true;
  CHECK(r.run_until(State::BARRIER_CLOSE, 20000));
  r.mid();
  // inrush: high current during blanking window is ignored
  r.in.isense_mv = 4000; r.run(r.cfg.inrush_blank_ms - 20);
  CHECK(r.f.state() == State::BARRIER_CLOSE);
  r.in.isense_mv = 600; r.run(100);
  // 40 ms spike < 50 ms hold: no trip
  r.in.isense_mv = 4000; r.run(40);
  r.in.isense_mv = 600; r.run(20);
  CHECK(r.f.state() == State::BARRIER_CLOSE);
  // sustained >= 50 ms: reverse
  r.in.isense_mv = 4000; r.run(r.cfg.oc_hold_ms + 6);
  CHECK(r.f.state() == State::BARRIER_OPEN);
  CHECK(r.saw_rev);
}

TEST(repeated_reversals_lock_out_with_boom_left_open) {
  Config c; c.max_reversals = 2;
  Rig r(c); r.step();
  r.grant_to_close();
  for (int k = 0; k < 3; ++k) {
    r.in.beam_clear = false; r.step(); r.in.beam_clear = true;
    CHECK(r.run_until(State::BARRIER_CLOSE, 20000));
    r.mid(); r.run(50);
    r.in.presence = true; r.step(); r.in.presence = false;
    r.run(r.cfg.reverse_dead_ms + 10);
    r.set_open(); r.run(10);
  }
  CHECK(r.f.state() == State::FAULT);
  CHECK(r.f.fault() == Fault::OBSTRUCTION_LOCKOUT);
  CHECK_EQ(r.out.motor, MotorCmd::STOP);
  CHECK(!r.out.contactor);
}

// ------------------------------------------------------------------ travel / limit faults
TEST(open_timeout_faults_at_1p5x_nominal_and_latches) {
  Rig r; r.step();
  r.tag(1, -40); r.step(); r.run_until(State::FUSE, 1000);
  r.decide(Decision::GRANT); r.step(); r.step();
  r.mid();
  uint32_t t0 = r.in.now_ms;
  CHECK(r.run_until(State::FAULT, 10000));
  CHECK(r.f.fault() == Fault::OPEN_TIMEOUT);
  CHECK(r.in.now_ms - t0 >= r.cfg.travel_timeout_ms() - 10 && r.in.now_ms - t0 <= r.cfg.travel_timeout_ms() + 10);
  CHECK_EQ(r.out.motor, MotorCmd::STOP);
  CHECK(!r.out.contactor);
  CHECK(r.out.led == LedColor::RED);
  CHECK_EQ(r.out.led_n, 1);
  r.run(2000);
  CHECK(r.f.state() == State::FAULT);              // latched
  r.ev.fault_reset = true; r.step();               // technician reset -> safe homing open
  CHECK(r.f.state() == State::BARRIER_OPEN);
  CHECK_EQ(r.out.motor, MotorCmd::OPEN);
}

TEST(close_timeout_faults) {
  Rig r(Config(), false); r.set_open(); r.run(10);
  r.in.beam_clear = false; r.run(20); r.in.beam_clear = true;
  CHECK(r.run_until(State::BARRIER_CLOSE, 5000));
  r.mid();
  CHECK(r.run_until(State::FAULT, 10000));
  CHECK(r.f.fault() == Fault::CLOSE_TIMEOUT);
}

TEST(open_stall_overcurrent_faults_not_reverses) {
  Rig r(Config(), false); r.mid(); r.run(10);
  CHECK(r.f.state() == State::BARRIER_OPEN);
  r.run(r.cfg.inrush_blank_ms + 10);
  r.in.isense_mv = 4000; r.run(80);
  CHECK(r.f.state() == State::FAULT);
  CHECK(r.f.fault() == Fault::OVERCURRENT_STALL);
}

TEST(both_limits_reached_is_a_fault) {
  Rig r; r.step();
  r.in.lim_up = true; r.step();
  CHECK(r.f.state() == State::FAULT);
  CHECK(r.f.fault() == Fault::LIMIT_CONFLICT);
  CHECK_EQ(r.out.motor, MotorCmd::STOP);
}

// ------------------------------------------------------------------ E-stop
TEST(estop_stops_everything_and_needs_explicit_rearm) {
  Rig r; r.step();
  r.grant_to_close();
  r.in.beam_clear = false; r.step(); r.in.beam_clear = true;
  CHECK(r.run_until(State::BARRIER_CLOSE, 20000));
  r.mid(); r.run(100);
  r.in.estop_ok = false; r.step();
  CHECK(r.f.state() == State::ESTOP);
  CHECK_EQ(r.out.motor, MotorCmd::STOP);
  CHECK(!r.out.contactor);
  CHECK(r.out.led == LedColor::RED);
  r.in.estop_ok = true; r.run(2000);
  CHECK(r.f.state() == State::ESTOP);               // released but not re-armed
  CHECK_EQ(r.out.motor, MotorCmd::STOP);
  r.ev.rearm = true; r.step();
  CHECK(r.f.state() == State::BARRIER_OPEN);        // position unknown -> open, never close
  CHECK_EQ(r.out.motor, MotorCmd::OPEN);
}

TEST(rearm_ignored_while_estop_still_pressed) {
  Rig r; r.step();
  r.in.estop_ok = false; r.step();
  r.ev.rearm = true; r.step();
  CHECK(r.f.state() == State::ESTOP);
}

// ------------------------------------------------------------------ link loss
TEST(link_loss_fail_open_opens_and_holds_then_recovers_with_hysteresis) {
  Rig r; r.step();
  r.run(1500);
  CHECK(r.f.link_ok());
  r.auto_hb = false;
  uint32_t t0 = r.in.now_ms;
  CHECK(r.run_until(State::OPEN_HOLD, 6000));
  CHECK(r.in.now_ms - t0 <= r.cfg.heartbeat_timeout_ms + 1100);   // last HB was up to 1 s before t0
  CHECK(r.f.hold_reason() == HoldReason::LINK_LOSS);
  r.mid(); r.step();
  CHECK_EQ(r.out.motor, MotorCmd::OPEN);
  CHECK(r.out.sign == Sign::LANE_OPEN);
  CHECK(r.out.buzz == Buzz::SLOW_PULSE_5S);
  r.set_open(); r.step();
  CHECK_EQ(r.out.motor, MotorCmd::STOP);
  r.run(5000);
  CHECK(r.f.state() == State::OPEN_HOLD);           // stays open while link is dead
  // a single heartbeat is not enough
  r.ev.heartbeat = true; r.step(); r.run(500);
  CHECK(r.f.state() == State::OPEN_HOLD);
  // gap > timeout resets recovery; then 1 Hz heartbeats for >= link_recover_ms
  r.run(4000);
  r.auto_hb = true; r.next_hb = r.in.now_ms;
  CHECK(r.run_until(State::CLEAR, 6000));
  // and from CLEAR it closes only via the normal dwell rules
  CHECK(r.run_until(State::BARRIER_CLOSE, r.cfg.no_pass_close_ms + 3000));
}

TEST(link_boot_grace_then_open_hold_if_edge_never_appears) {
  Rig r; r.auto_hb = false; r.step();
  r.run(40000);
  CHECK(r.f.state() == State::IDLE);
  CHECK(r.run_until(State::OPEN_HOLD, 10000));
}

TEST(fail_secure_policy_never_auto_opens_on_link_loss) {
  Config c; c.link_policy = LinkLossPolicy::FAIL_SECURE;
  Rig r(c); r.step();
  r.run(1500); r.auto_hb = false; r.run(10000);
  CHECK(r.f.state() == State::IDLE);
  CHECK_EQ(r.out.motor, MotorCmd::STOP);
  CHECK(r.out.sign == Sign::SEE_GUARD);
  r.tag(1, -40); r.step();
  CHECK(r.f.state() == State::IDLE);                // cannot decide without the Edge Node
}

TEST(link_loss_while_closing_reverses_via_dead_time) {
  Rig r; r.step();
  r.grant_to_close();
  r.in.beam_clear = false; r.step(); r.in.beam_clear = true;
  CHECK(r.run_until(State::BARRIER_CLOSE, 20000));
  r.mid(); r.run(100);
  r.auto_hb = false;
  CHECK(r.run_until(State::OPEN_HOLD, 6000));
  r.run(r.cfg.reverse_dead_ms + 20);
  CHECK_EQ(r.out.motor, MotorCmd::OPEN);
  CHECK_EQ(r.flips, 0);
}

// ------------------------------------------------------------------ mains
TEST(mains_loss_debounced_then_opens_and_drops_contactor_when_open) {
  Rig r; r.step();
  r.run(1200);
  r.in.ac_ok = false; r.run(r.cfg.mains_loss_debounce_ms - 100);
  CHECK(r.f.state() == State::IDLE);
  r.in.ac_ok = true; r.run(100);                    // flicker ends
  r.in.ac_ok = false; r.run(r.cfg.mains_loss_debounce_ms + 50);
  CHECK(r.f.state() == State::OPEN_HOLD);
  CHECK(r.f.hold_reason() == HoldReason::MAINS_LOSS);
  r.mid(); r.step();
  CHECK_EQ(r.out.motor, MotorCmd::OPEN);
  r.set_open(); r.step();
  CHECK_EQ(r.out.motor, MotorCmd::STOP);
  CHECK(!r.out.contactor);
  r.in.ac_ok = true; r.run(r.cfg.mains_recover_ms - 500);
  CHECK(r.f.state() == State::OPEN_HOLD);
  CHECK(r.run_until(State::CLEAR, 1500));
}

// ------------------------------------------------------------------ property / fuzz
namespace {
struct Lcg { uint64_t s; uint32_t next() { s = s * 6364136223846793005ULL + 1442695040888963407ULL; return static_cast<uint32_t>(s >> 33); } };
}

TEST(fuzz_invariants_hold_for_random_inputs) {
  long steps = 0, close_ticks = 0, state_seen_mask = 0, reversals_seen = 0, faults_seen = 0;
  for (uint64_t seed = 1; seed <= 20; ++seed) {
    Lcg g{seed * 7919};
    Config c; c.link_boot_grace_ms = 2000;
    LaneFsm f(c);
    Inputs in; Events ev; Outputs out;
    in.now_ms = 100; in.lim_dn = true;
    MotorCmd prev = MotorCmd::STOP;
    uint32_t hold_until[8] = {0};
    bool v[8] = {false, true, false, false, true, false, true, false};
    for (int i = 0; i < 60000; ++i, ++steps) {
      in.now_ms += 2;
      // sticky random signals so conditions persist for realistic spans
      for (int k = 0; k < 8; ++k) if (in.now_ms >= hold_until[k]) {
        hold_until[k] = in.now_ms + 2 + g.next() % (k == 1 ? 3000 : 800);
        v[k] = (g.next() % (k == 1 ? 12 : 5)) == 0 ? !v[k] : v[k];
        if (k == 1) v[k] = (g.next() % 12) != 0;     // beam mostly clear
        if (k == 0) v[k] = (g.next() % 6) == 0;      // presence mostly absent
      }
      in.presence = v[0]; in.beam_clear = v[1]; in.estop_ok = (g.next() % 400) != 0 || !v[2];
      in.ac_ok = (g.next() % 3000) != 0;
      in.lim_up = v[3]; in.lim_dn = v[4] && !v[3];
      if (seed % 3 == 0) { in.lim_up = false; in.lim_dn = false; }              // switches stuck: exercises time-outs
      if (seed % 5 == 0 && (g.next() % 3000) == 0) { in.lim_up = true; in.lim_dn = true; }   // wiring conflict
      in.isense_mv = (g.next() % 100 == 0) ? 4000 : 600;
      ev = Events();
      ev.heartbeat = (g.next() % 400) < 2 || (v[5] && (g.next() % 100) < 4);
      ev.tag = (g.next() % 500) == 0; if (ev.tag) { ev.tag_frame.epc_len = 4; ev.tag_frame.epc[0] = (uint8_t)g.next(); ev.tag_frame.has_rssi = true; ev.tag_frame.rssi = -(int)(g.next() % 80); }
      ev.edge_vehicle = (g.next() % 700) == 0;
      ev.decision = (g.next() % 150) == 0; ev.decision_seq = f.veh_seq(); ev.decision_val = (Decision)(1 + g.next() % 3);
      ev.guard_open = (g.next() % 900) == 0; ev.rearm = (g.next() % 600) == 0; ev.fault_reset = (g.next() % 600) == 0;
      f.step(in, ev, out);
      state_seen_mask |= 1L << (int)f.state();
      if (out.motor == MotorCmd::CLOSE) ++close_ticks;
      for (int q = 0; q < out.n_tx; ++q) if (out.tx[q].type == TxType::REVERSED) ++reversals_seen;
      if (f.state() == State::FAULT) ++faults_seen;
      // I1 anti-crush: CLOSE only in BARRIER_CLOSE with beam clear, no presence, e-stop healthy
      if (out.motor == MotorCmd::CLOSE) {
        CHECK(in.beam_clear && !in.presence && in.estop_ok && f.state() == State::BARRIER_CLOSE);
      }
      // I2 e-stop: motor stopped and contactor dropped whenever the loop is open
      if (!in.estop_ok) { CHECK(out.motor == MotorCmd::STOP && !out.contactor); }
      // I3 FAULT/ESTOP never drive
      if (f.state() == State::FAULT || f.state() == State::ESTOP) CHECK(out.motor == MotorCmd::STOP);
      // I4 no direct direction flip between consecutive ticks
      CHECK(!((prev == MotorCmd::OPEN && out.motor == MotorCmd::CLOSE) || (prev == MotorCmd::CLOSE && out.motor == MotorCmd::OPEN)));
      prev = out.motor;
    }
  }
  CHECK(steps == 20 * 60000);
  // non-vacuity: the fuzz must actually reach every state, close the boom and reverse
  CHECK_EQ(state_seen_mask, (1L << (int)State::COUNT_) - 1);
  CHECK(close_ticks > 1000);
  CHECK(reversals_seen > 10);
  CHECK(faults_seen > 100);
  std::printf("  fuzz coverage: close_ticks=%ld reversals=%ld fault_ticks=%ld states_mask=0x%lx\n", close_ticks, reversals_seen, faults_seen, state_seen_mask);
}
