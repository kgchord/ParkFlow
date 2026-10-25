#pragma once
#include <cstddef>
#include <cstdint>
namespace pf {

enum class State : uint8_t {
  IDLE, VEHICLE_DETECTED, READ, FUSE, GRANT, FALLBACK,
  BARRIER_OPEN, CLEAR, BARRIER_CLOSE, OPEN_HOLD, FAULT, ESTOP, COUNT_
};
enum class Fault : uint8_t {
  NONE = 0, OPEN_TIMEOUT = 1, CLOSE_TIMEOUT = 2, OVERCURRENT_STALL = 3,
  LIMIT_CONFLICT = 4, OBSTRUCTION_LOCKOUT = 5
};
enum class HoldReason : uint8_t { NONE = 0, LINK_LOSS = 1, MAINS_LOSS = 2 };
enum class MotorCmd : uint8_t { STOP, OPEN, CLOSE };
enum class Decision : uint8_t { NONE, GRANT, FALLBACK, DENY };
enum class LinkLossPolicy : uint8_t { FAIL_OPEN_HOLD, FAIL_SECURE };

constexpr size_t kMaxEpc = 16;
struct TagFrame {
  uint8_t epc[kMaxEpc];
  uint8_t epc_len = 0;
  bool has_rssi = false;
  int16_t rssi = 0;      // reader-defined units (unverified; see FIRMWARE.md)
};

// Conditioned, polarity-decoded inputs: true == the physical condition named.
struct Inputs {
  uint32_t now_ms = 0;
  bool estop_ok = true;       // E-stop loop healthy
  bool beam_clear = true;     // photo-beam unobstructed (false on cable cut)
  bool presence = false;      // vehicle/person under boom
  bool lim_up = false;        // boom at 90 deg
  bool lim_dn = false;        // boom at 0 deg
  bool ac_ok = true;
  bool bat_ok = true;
  uint16_t isense_mv = 0;     // motor shunt, mV at ADC pin (calibrate at commissioning)
};

// Events from RS485 reader and Edge Node link (all optional per step).
struct Events {
  bool heartbeat = false;
  bool edge_vehicle = false;      // Edge Node camera says a vehicle is approaching
  bool tag = false;               // a tag frame was parsed this step
  TagFrame tag_frame;
  bool decision = false;
  uint32_t decision_seq = 0;
  Decision decision_val = Decision::NONE;
  uint8_t decision_reason = 0;
  bool guard_open = false;
  bool rearm = false;
  bool fault_reset = false;
};

enum class TxType : uint8_t { NONE, VEH, TAG, NOTAG, PASS, REVERSED };
struct TxEvent {
  TxType type = TxType::NONE;
  uint32_t seq = 0;
  uint32_t t_ms = 0;
  TagFrame tag;
  uint32_t peak_ms = 0;
  uint8_t n_distinct = 0;
};

enum class LedColor : uint8_t { OFF, GREEN, BLUE, AMBER, RED, WHITE };
enum class LedMode : uint8_t { SOLID, BLINK_SLOW, BLINK_FAST, FAULT_CODE };
enum class Buzz : uint8_t { OFF, BEEP_SHORT_1S, DOUBLE_BEEP_3S, SLOW_PULSE_5S, ALARM_FAST, LONG_2S, FAULT_TRIPLE };
enum class Sign : uint8_t { WELCOME, PLEASE_WAIT, GRANTED, SEE_GUARD, CLOSING, OBSTACLE, LANE_OPEN, LANE_CLOSED, STOPPED, COUNT_ };

struct Outputs {
  MotorCmd motor = MotorCmd::STOP;
  bool contactor = false;       // K1_EN
  LedColor led = LedColor::OFF;
  LedMode led_mode = LedMode::SOLID;
  uint8_t led_n = 0;            // blink count in FAULT_CODE
  Buzz buzz = Buzz::OFF;
  Sign sign = Sign::WELCOME;
  TxEvent tx[4];
  uint8_t n_tx = 0;
};

}  // namespace pf
