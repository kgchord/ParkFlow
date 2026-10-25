// Closed-loop tests: LaneApp + MockHal (with PCB interlock + crude barrier physics).
#include <algorithm>
#include <cstdio>
#include <string>
#include "lane_app.h"
#include "minitest.h"
#include "mock_hal.h"
using namespace pf;

namespace {
std::string mkline(const std::string& body) {
  uint8_t ck = 0; for (char ch : body) ck ^= (uint8_t)ch;
  char tail[8]; std::snprintf(tail, sizeof tail, "*%02X\n", ck);
  return "$" + body + tail;
}

struct Sim {
  MockHal hal;
  Config cfg;
  LaneApp app;
  bool hb = true, edge_auto_grant = true;
  uint32_t next_hb = 500;
  size_t scanned = 0;
  std::string log;                 // everything the controller sent to the Edge Node
  double min_angle_after_mark = 1e9; bool marking = false;
  static Config mk(Config c) { c.travel_nominal_ms = 3000; return c; }
  explicit Sim(Config c = Config(), const RfidFrameCfg& r = kIllustrativeProfile, double start_angle = 0.0) : cfg(mk(c)), app(hal, cfg, r) { hal.angle = start_angle; }
  void poll_edge() {
    log += hal.edge_out; 
    // scripted edge: reply GRANT to the first TAG/NOTAG line seen
    size_t pos;
    while ((pos = hal.edge_out.find('\n')) != std::string::npos) {
      std::string line = hal.edge_out.substr(0, pos);
      hal.edge_out.erase(0, pos + 1);
      if (!edge_auto_grant) continue;
      if (line.rfind("$TAG,", 0) == 0 || line.rfind("$NOTAG,", 0) == 0) {
        unsigned seq = std::stoul(line.substr(line.find(',') + 1));
        hal.edge_in += mkline("DEC," + std::to_string(seq) + ",G,0");
      }
    }
  }
  void run(uint32_t ms) {
    for (uint32_t i = 0; i < ms; ++i) {
      if (hb && hal.t >= next_hb) { hal.edge_in += mkline("HB," + std::to_string(hal.t)); next_hb = hal.t + 1000; }
      if (hal.t % 2 == 0) app.tick();
      hal.physics_1ms();
      if (hal.t % 5 == 0) poll_edge();
      if (marking) min_angle_after_mark = std::min(min_angle_after_mark, hal.angle);
    }
  }
  bool run_until(bool (*pred)(Sim&), uint32_t max_ms) { for (uint32_t i = 0; i < max_ms; ++i) { run(1); if (pred(*this)) return true; } return false; }
  void send_tag(const uint8_t* epc, uint8_t n, int8_t rssi) {
    uint8_t f[64]; size_t len = illustrative_encode(f, sizeof f, epc, n, rssi);
    hal.rs485_in.append(reinterpret_cast<char*>(f), len);
  }
  bool has(const char* s) const { return log.find(s) != std::string::npos; }
};
const uint8_t EPC[12] = {0xE2, 0x80, 0x11, 0x60, 0x60, 0x00, 0x02, 0x05, 0x5A, 0x11, 0x22, 0x33};
}  // namespace

TEST(sim_full_cycle_rfid_to_barrier_closed_again) {
  Sim s; s.run(1200);
  CHECK(s.app.fsm().state() == State::IDLE);
  s.send_tag(EPC, 12, -45);
  s.run(1500);                                    // read, decision (scripted), opening
  CHECK(s.has("$VEH,1,"));
  CHECK(s.has("$TAG,1,E28011606000020"));
  CHECK(s.hal.angle > 1.0 || s.app.fsm().state() == State::BARRIER_OPEN);
  CHECK(s.hal.sign == "PROCEED");
  CHECK(s.hal.k1);
  CHECK(s.run_until([](Sim& x) { return x.app.fsm().state() == State::CLEAR; }, 6000));
  CHECK(s.hal.angle >= 89.0);
  // car drives through: beam broken 600 ms
  s.hal.beam_obstructed = true; s.run(600); s.hal.beam_obstructed = false;
  CHECK(s.run_until([](Sim& x) { return x.app.fsm().state() == State::IDLE; }, 15000));
  CHECK(s.hal.angle <= 0.6);
  CHECK(s.has("$PASS,1*"));
  CHECK_EQ(s.hal.unsafe_close_requests, 0);
  CHECK_EQ(s.hal.reverse_while_moving, 0);
  CHECK(s.hal.wdi_toggles > 100);
}

TEST(sim_plate_only_vehicle_no_tag_still_gets_decision) {
  Sim s; s.run(1200);
  s.hal.edge_in += mkline("HB,1");
  // camera-triggered (no tag): emulate edge vehicle notice via presence at the boom instead
  s.hal.presence_phys = true; s.run(300); s.hal.presence_phys = false; s.run(600);
  CHECK(s.has("$NOTAG,1*"));
}

TEST(sim_beam_break_during_close_reverses_and_hardware_stops_descent_at_once) {
  Sim s; s.run(1200);
  s.send_tag(EPC, 12, -45); s.run(500);
  CHECK(s.run_until([](Sim& x) { return x.app.fsm().state() == State::CLEAR; }, 6000));
  s.hal.beam_obstructed = true; s.run(100); s.hal.beam_obstructed = false;
  CHECK(s.run_until([](Sim& x) { return x.app.fsm().state() == State::BARRIER_CLOSE; }, 8000));
  s.run(1000);                                    // boom partway down
  CHECK(s.hal.angle < 80.0 && s.hal.angle > 10.0);
  s.hal.beam_obstructed = true;
  const double a0 = s.hal.angle;
  s.marking = true; s.min_angle_after_mark = a0;
  s.run(10);
  CHECK(a0 - s.min_angle_after_mark <= 0.1);      // PCB gate (U10) + firmware: descent stops within ~ms
  s.run(2500);
  CHECK(s.hal.angle >= 89.0);                     // reversed all the way up
  CHECK(s.app.fsm().state() == State::CLEAR);
  CHECK(s.has("$REV,"));
  CHECK_EQ(s.hal.unsafe_close_requests, 0);
  CHECK_EQ(s.hal.reverse_while_moving, 0);
  // still blocked while the beam stays broken
  s.run(20000);
  CHECK(s.hal.angle >= 89.0);
  s.hal.beam_obstructed = false;
  CHECK(s.run_until([](Sim& x) { return x.app.fsm().state() == State::IDLE; }, 20000));
}

TEST(sim_unbeamed_obstacle_overcurrent_reverses_then_locks_out_open) {
  Config c; c.max_reversals = 3;
  Sim s(c); s.run(1200);
  s.send_tag(EPC, 12, -45); s.run(500);
  CHECK(s.run_until([](Sim& x) { return x.app.fsm().state() == State::CLEAR; }, 6000));
  s.hal.beam_obstructed = true; s.run(100); s.hal.beam_obstructed = false;   // car passed
  s.hal.obstacle_deg = 30.0;                                                  // object above beam height
  CHECK(s.run_until([](Sim& x) { return x.app.fsm().state() == State::FAULT; }, 120000));
  CHECK(s.app.fsm().fault() == Fault::OBSTRUCTION_LOCKOUT);
  CHECK(s.hal.angle >= 89.0);                     // left OPEN
  CHECK(!s.hal.k1);
  CHECK_EQ(s.hal.reverse_while_moving, 0);
  CHECK_EQ(s.hal.unsafe_close_requests, 0);
}

TEST(sim_estop_cuts_motion_immediately_even_if_firmware_is_blind) {
  Sim s; s.run(1200);
  s.send_tag(EPC, 12, -45); s.run(500);
  CHECK(s.run_until([](Sim& x) { return x.app.fsm().state() == State::CLEAR; }, 6000));
  s.hal.beam_obstructed = true; s.run(100); s.hal.beam_obstructed = false;
  CHECK(s.run_until([](Sim& x) { return x.app.fsm().state() == State::BARRIER_CLOSE; }, 8000));
  s.run(800);
  s.hal.estop_pressed = true;
  s.run(100);
  const double a = s.hal.angle;
  CHECK(s.app.fsm().state() == State::ESTOP);
  CHECK(!s.hal.k1);
  s.run(2000);
  CHECK(std::abs(s.hal.angle - a) < 1e-9);
  s.hal.estop_pressed = false; s.run(2000);
  CHECK(s.app.fsm().state() == State::ESTOP);     // no auto restart
  CHECK(std::abs(s.hal.angle - a) < 1e-9);
  s.hal.rearm_btn = true; s.run(10); s.hal.rearm_btn = false;
  CHECK(s.run_until([](Sim& x) { return x.app.fsm().state() == State::CLEAR; }, 8000));
  CHECK(s.hal.angle >= 89.0);                     // homed OPEN, not closed
}

TEST(sim_edge_node_death_opens_lane_and_recovery_closes_it) {
  Sim s; s.run(3000);
  CHECK(s.app.fsm().state() == State::IDLE);
  s.hb = false;
  CHECK(s.run_until([](Sim& x) { return x.app.fsm().state() == State::OPEN_HOLD; }, 5000));
  s.run(4000);
  CHECK(s.hal.angle >= 89.0);
  CHECK(s.hal.sign == "LANE OPEN");
  s.run(8000);
  CHECK(s.hal.angle >= 89.0);                     // still open
  s.hb = true; s.next_hb = s.hal.t;
  CHECK(s.run_until([](Sim& x) { return x.app.fsm().state() == State::IDLE; }, 40000));
  CHECK(s.hal.angle <= 0.6);
  CHECK_EQ(s.hal.reverse_while_moving, 0);
}

TEST(sim_mains_loss_opens_boom_and_holds) {
  Sim s; s.run(3000);
  s.hal.mains_ok = false;
  CHECK(s.run_until([](Sim& x) { return x.app.fsm().state() == State::OPEN_HOLD; }, 3000));
  s.run(5000);
  CHECK(s.hal.angle >= 89.0);
  CHECK(!s.hal.k1);                               // contactor dropped once open: UPS energy saved
}

TEST(sim_limit_switch_failure_hits_hard_stop_and_faults_on_overcurrent) {
  Sim s; s.run(1200);
  s.hal.limit_up_broken = true;                   // switch never reports "reached"
  s.send_tag(EPC, 12, -45);
  CHECK(s.run_until([](Sim& x) { return x.app.fsm().state() == State::FAULT; }, 15000));
  CHECK(s.app.fsm().fault() == Fault::OVERCURRENT_STALL);   // boom reaches the mechanical stop first
  CHECK(!s.hal.k1 && !s.hal.in_a && !s.hal.in_b && !s.hal.en);
}

TEST(sim_limit_switch_failure_without_stall_current_hits_time_out) {
  Sim s; s.run(1200);
  s.hal.limit_up_broken = true; s.hal.stall_at_end = false;  // e.g. shear pin gone / slipping coupling
  s.send_tag(EPC, 12, -45);
  CHECK(s.run_until([](Sim& x) { return x.app.fsm().state() == State::FAULT; }, 15000));
  CHECK(s.app.fsm().fault() == Fault::OPEN_TIMEOUT);
  CHECK(!s.hal.k1 && !s.hal.in_a && !s.hal.in_b && !s.hal.en);
}

TEST(sim_external_watchdog_not_kicked_after_a_stalled_control_loop) {
  Sim s; s.run(500);
  const uint32_t before = s.hal.wdi_toggles;
  s.run(100);
  const uint32_t steady = s.hal.wdi_toggles - before;
  CHECK(steady >= 40);                            // ~1 per 2 ms tick
  // simulate a 200 ms scheduling stall: time advances, no tick
  for (int i = 0; i < 200; ++i) s.hal.physics_1ms();
  const uint32_t b2 = s.hal.wdi_toggles;
  s.app.tick();                                   // first tick after the stall: overrun detected, no kick
  CHECK_EQ(s.hal.wdi_toggles, b2);
  s.hal.physics_1ms(); s.hal.physics_1ms(); s.app.tick();
  CHECK_EQ(s.hal.wdi_toggles, b2 + 1);            // healthy again
}

TEST(sim_inventory_command_is_sent_to_reader_on_vehicle_detect) {
  RfidFrameCfg r = kIllustrativeProfile;
  r.inventory_cmd[0] = 0xA5; r.inventory_cmd[1] = 0x01; r.inventory_cmd_len = 2;
  Sim s(Config(), r); s.run(1200);
  s.hal.presence_phys = true; s.run(200); s.hal.presence_phys = false;
  CHECK_EQ(s.hal.rs485_out.size(), 2);
}

TEST(sim_edge_garbage_does_not_change_state) {
  Sim s; s.run(1200);
  s.hal.edge_in += "$DEC,1,G,0*00\n$DEC,1,G,0\nrandom\n";
  s.run(100);
  CHECK(s.app.fsm().state() == State::IDLE);
  CHECK(s.app.edge().bad_checksum() >= 1);
}
