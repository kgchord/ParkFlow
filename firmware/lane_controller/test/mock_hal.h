// Mock HAL + crude barrier physics. The PCB hardware interlocks (U9: INH = EN & ESTOP_OK,
// U10: IN_B & BEAM_CLEAR, K1 contactor) are modelled here so closed-loop tests can tell
// "firmware asked" apart from "hardware did". Numbers (rates, currents) are test fixtures,
// not measurements of the real barrier.
#pragma once
#include <cstring>
#include <string>
#include "hal.h"
namespace pf {

struct MockHal : IHal {
  // time
  uint32_t t = 0;
  // physical world (set by tests)
  bool beam_obstructed = false, presence_phys = false, estop_pressed = false, mains_ok = true, bat_ok = true;
  bool rearm_btn = false;
  double angle = 45.0;                 // 0 = closed (down), 90 = open
  double obstacle_deg = -1;            // boom cannot go below this angle while closing (-1 = none)
  bool limit_up_broken = false, limit_dn_broken = false;   // switch stuck "not reached"
  double travel_ms = 3000;
  uint16_t run_mv = 600, inrush_mv = 2500, stall_mv = 3000;
  // actuators as last commanded
  bool in_a = false, in_b = false, en = false, k1 = false, buzzer = false;
  uint8_t led[3] = {0, 0, 0};
  std::string sign;
  // byte pipes
  std::string edge_in, edge_out, rs485_in, rs485_out;
  // bookkeeping
  uint32_t wdi_toggles = 0, twdt_resets = 0;
  uint32_t unsafe_close_requests = 0;  // firmware asked to close while beam broken/presence/estop
  uint32_t reverse_while_moving = 0;   // direction flipped without a stop tick in between
  bool hung = false;                   // test hook
  int last_dir = 0;                    // -1 closing, +1 opening, 0 stopped (hardware-effective)
  uint32_t move_start = 0;
  bool moving_eff = false;
  int fw_prev_dir = 0;

  uint32_t now_ms() override { return t; }
  RawInputs read_inputs() override {
    RawInputs r;
    r.lim_up_ok = limit_up_broken ? true : !(angle >= 89.5);
    r.lim_dn_ok = limit_dn_broken ? true : !(angle <= 0.5);
    r.beam_clear = !beam_obstructed;
    r.presence = presence_phys;
    r.estop_ok = !estop_pressed;
    r.ac_ok = mains_ok;
    r.bat_ok = bat_ok;
    r.rearm_btn_low = rearm_btn;
    return r;
  }
  uint16_t adc_isense_mv() override {
    if (!moving_eff) return 0;
    if (stalled) return stall_mv;
    return (t - move_start < 100) ? inrush_mv : run_mv;
  }
  uint16_t adc_v24_mv() override { return 24000; }
  void set_motor(bool a, bool b, bool e) override {
    in_a = a; in_b = b; en = e;
    if (b && (beam_obstructed || presence_phys || estop_pressed)) ++unsafe_close_requests;
    int dir = (a && !b) ? 1 : (b && !a) ? -1 : 0;
    if (!e) dir = 0;
    if (dir != 0 && fw_prev_dir != 0 && dir != fw_prev_dir) ++reverse_while_moving;
    fw_prev_dir = dir;
  }
  void set_contactor(bool on) override { k1 = on; }
  void set_buzzer(bool on) override { buzzer = on; }
  void set_led_rgb(uint8_t r, uint8_t g, uint8_t b) override { led[0] = r; led[1] = g; led[2] = b; }
  void sign_show(const char* s) override { sign = s; }
  size_t rs485_read(uint8_t* b, size_t cap) override { size_t n = std::min(cap, rs485_in.size()); std::memcpy(b, rs485_in.data(), n); rs485_in.erase(0, n); return n; }
  void rs485_write(const uint8_t* b, size_t n) override { rs485_out.append(reinterpret_cast<const char*>(b), n); }
  size_t edge_read(uint8_t* b, size_t cap) override { size_t n = std::min(cap, edge_in.size()); std::memcpy(b, edge_in.data(), n); edge_in.erase(0, n); return n; }
  void edge_write(const uint8_t* b, size_t n) override { edge_out.append(reinterpret_cast<const char*>(b), n); }
  void wdi_toggle() override { ++wdi_toggles; }
  void task_wdt_reset() override { ++twdt_resets; }

  bool stalled = false;
  bool stall_at_end = true;            // current spikes at the mechanical end stop
  // advance physics by 1 ms using the last commanded pins + hardware interlocks
  void physics_1ms() {
    const bool inh = en && !estop_pressed && k1;            // U9 + contactor
    const bool b_eff = in_b && !beam_obstructed;            // U10
    int dir = 0;
    if (inh) { if (in_a && !b_eff) dir = 1; else if (b_eff && !in_a) dir = -1; }
    stalled = false;
    if (dir != last_dir) move_start = t;
    last_dir = dir;
    moving_eff = dir != 0;
    const double step = 90.0 / travel_ms;
    if (dir > 0) { angle += step; if (angle >= 90.0) { angle = 90.0; stalled = stall_at_end; } }
    if (dir < 0) {
      angle -= step;
      const double floor_deg = obstacle_deg >= 0 ? obstacle_deg : 0.0;
      if (angle <= floor_deg) { angle = floor_deg; stalled = obstacle_deg >= 0 || limit_dn_broken; }
    }
    ++t;
  }
};
}  // namespace pf
