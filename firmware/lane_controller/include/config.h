#pragma once
#include "types.h"
namespace pf {
// Every value is a DESIGN TARGET or a PLACEHOLDER to be set at commissioning /
// bench-verified. None is a measured result.
struct Config {
  // control loop
  uint32_t loop_period_ms = 2;              // target 500 Hz control task
  // Edge link (SAFETY F9: heartbeat 1 s, time-out 3 s)
  uint32_t heartbeat_timeout_ms = 3000;
  uint32_t link_recover_ms = 3000;          // heartbeats must be gap-free this long
  uint32_t link_boot_grace_ms = 45000;      // Pi boot time allowance (placeholder)
  LinkLossPolicy link_policy = LinkLossPolicy::FAIL_OPEN_HOLD;
  // read / fuse
  uint32_t read_window_ms = 400;            // wait for a tag after trigger
  uint32_t read_settle_ms = 100;            // after first tag, keep listening for a stronger one
  uint32_t decision_timeout_ms = 1000;      // controller-side patience; NOT the 300 ms Edge target
  uint32_t fallback_timeout_ms = 30000;     // guard window
  uint32_t retrigger_lockout_ms = 3000;     // ignore tag/edge triggers after a cycle ends
  int16_t  min_rssi = -32768;               // RSSI gate (disabled; unit unverified)
  // barrier mechanics
  uint32_t travel_nominal_ms = 4000;        // 0->90 deg nominal (placeholder, measure)
  uint32_t travel_timeout_x10 = 15;         // 1.5 x nominal (SAFETY F12)
  uint32_t inrush_blank_ms = 300;
  uint32_t reverse_dead_ms = 100;           // motor stopped this long between opposite directions (placeholder)
  uint16_t oc_threshold_mv = 1500;          // PLACEHOLDER: 1.5 x running current, set at commissioning (F3). With the IBT-2 module the IS scale is about 0.1 V/A (to be bench-calibrated), so a 5 A limit is about 540 mV; 1500 mV would be about 14 A and is NOT a safe field value
  uint32_t oc_hold_ms = 50;                 // F3
  // anti-crush / passage
  uint32_t clear_dwell_ms = 1500;           // beam+presence clear this long before close
  uint32_t no_pass_close_ms = 10000;        // close anyway if nobody passes
  uint8_t  max_reversals = 3;               // consecutive; then OBSTRUCTION_LOCKOUT (boom left open)
  // power
  uint32_t mains_loss_debounce_ms = 500;
  uint32_t mains_recover_ms = 5000;
  uint32_t travel_timeout_ms() const { return travel_nominal_ms * travel_timeout_x10 / 10; }
};
}  // namespace pf
