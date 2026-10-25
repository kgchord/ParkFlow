#include "lane_app.h"
#include <cstring>
namespace pf {

LaneApp::LaneApp(IHal& hal, const Config& cfg, const RfidFrameCfg& rfid)
    : hal_(hal), fsm_(cfg), rfid_(rfid),
      d_beam_(true, 30, 0),     // beam: break is instant, "clear" needs 30 ms stable
      d_pres_(false, 0, 30),    // presence: occupied is instant, vacant needs 30 ms
      d_up_(false, 10, 10), d_dn_(false, 10, 10),
      d_estop_(true, 50, 0),    // e-stop: opening the loop is instant
      rcfg_(rfid) {
  sup_.configure(kTaskControl, 50);   // control loop must run at least every 50 ms
}

void LaneApp::tick() {
  const uint32_t now = hal_.now_ms();
  const RawInputs r = hal_.read_inputs();
  if (first_) {  // seed debouncers with the first real reading so boot does not look like an edge
    d_beam_ = Debounce(r.beam_clear, 30, 0);
    d_pres_ = Debounce(r.presence, 0, 30);
    d_up_ = Debounce(!r.lim_up_ok, 10, 10);
    d_dn_ = Debounce(!r.lim_dn_ok, 10, 10);
    d_estop_ = Debounce(r.estop_ok, 50, 0);
    first_ = false;
  }
  Inputs in;
  in.now_ms = now;
  in.beam_clear = d_beam_.update(r.beam_clear, now);
  in.presence = d_pres_.update(r.presence, now);
  in.lim_up = d_up_.update(!r.lim_up_ok, now);     // NC switch: LOW == limit reached or wire break
  in.lim_dn = d_dn_.update(!r.lim_dn_ok, now);
  in.estop_ok = d_estop_.update(r.estop_ok, now);
  in.ac_ok = r.ac_ok;
  in.bat_ok = r.bat_ok;
  in.isense_mv = hal_.adc_isense_mv();

  Events ev;
  uint8_t buf[64];
  // Edge Node link
  size_t n = hal_.edge_read(buf, sizeof buf);
  for (size_t i = 0; i < n; ++i) {
    EdgeMsg m;
    if (!edge_.push(buf[i], m)) continue;
    switch (m.type) {
      case EdgeMsgType::HB: ev.heartbeat = true; break;
      case EdgeMsgType::DEC: ev.decision = true; ev.decision_seq = m.n; ev.decision_val = m.decision; ev.decision_reason = m.reason; break;
      case EdgeMsgType::GUARD: ev.guard_open = true; break;
      case EdgeMsgType::REARM: ev.rearm = true; break;
      case EdgeMsgType::RESET: ev.fault_reset = true; break;
      case EdgeMsgType::NONE: break;
    }
  }
  const bool btn = r.rearm_btn_low;
  if (btn && !rearm_prev_) ev.rearm = true;   // local re-arm button (BOOT, GPIO0)
  rearm_prev_ = btn;
  // RFID reader
  n = hal_.rs485_read(buf, sizeof buf);
  for (size_t i = 0; i < n; ++i) rfid_.push(buf[i]);
  TagFrame tf;
  if (rfid_.pop(tf)) { ev.tag = true; ev.tag_frame = tf; }   // one tag per tick; the rest stay queued

  fsm_.step(in, ev, out_);

  // outputs
  const bool a = out_.motor == MotorCmd::OPEN, b = out_.motor == MotorCmd::CLOSE;
  hal_.set_contactor(out_.contactor);
  if (out_.contactor) { if (!k1_on_) { k1_on_ = true; k1_t_ = now; } } else k1_on_ = false;
  const bool k1_ready = k1_on_ && now - k1_t_ >= kContactorSettleMs;   // no motor drive into a still-closing contactor
  hal_.set_motor(a && k1_ready, b && k1_ready, out_.motor != MotorCmd::STOP && k1_ready);
  hal_.set_buzzer(buzzer_level(out_.buzz, now));
  const Rgb c = led_rgb(out_.led);
  if (led_lit(out_.led_mode, out_.led_n, now)) hal_.set_led_rgb(c.r, c.g, c.b); else hal_.set_led_rgb(0, 0, 0);
  const char* st = sign_text(out_.sign);
  if (st != last_sign_) { hal_.sign_show(st); last_sign_ = st; }

  char line[112];
  for (uint8_t i = 0; i < out_.n_tx; ++i) {
    if (out_.tx[i].type == TxType::VEH && rcfg_.inventory_cmd_len) hal_.rs485_write(rcfg_.inventory_cmd, rcfg_.inventory_cmd_len);
    send_edge(line, encode_tx_event(line, sizeof line, out_.tx[i]));
  }
  if (now - last_status_ >= 1000) {
    last_status_ = now;
    const uint8_t flags = (fsm_.link_ok() ? 1 : 0) | (in.ac_ok ? 2 : 0) | (in.bat_ok ? 4 : 0) | (in.beam_clear ? 8 : 0) | (in.presence ? 16 : 0);
    send_edge(line, encode_status(line, sizeof line, fsm_.state(), fsm_.fault(), flags, hal_.adc_v24_mv()));
  }

  // watchdog chain: only a completed, on-time control cycle keeps the external watchdog fed
  const bool on_time = sup_.healthy(now);   // evaluated BEFORE this tick checks in: catches loop overruns
  sup_.checkin(kTaskControl, now);
  if (on_time) {
    hal_.wdi_toggle();
    hal_.task_wdt_reset();
    ++wdi_kicks_;
  }
}
}  // namespace pf
