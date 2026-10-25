#include "indicators.h"
namespace pf {
bool buzzer_level(Buzz b, uint32_t t) {
  switch (b) {
    case Buzz::OFF: return false;
    case Buzz::BEEP_SHORT_1S: return (t % 1000) < 100;                 // 100 ms beep every 1 s
    case Buzz::DOUBLE_BEEP_3S: { uint32_t p = t % 3000; return p < 120 || (p >= 240 && p < 360); }
    case Buzz::SLOW_PULSE_5S: return (t % 5000) < 1000;                // 1 s on every 5 s
    case Buzz::ALARM_FAST: return (t % 200) < 100;
    case Buzz::LONG_2S: return (t % 2000) < 800;
    case Buzz::FAULT_TRIPLE: { uint32_t p = t % 2000; return p < 150 || (p >= 300 && p < 450) || (p >= 600 && p < 750); }
  }
  return false;
}
bool led_lit(LedMode m, uint8_t n, uint32_t t) {
  switch (m) {
    case LedMode::SOLID: return true;
    case LedMode::BLINK_SLOW: return (t % 1000) < 500;
    case LedMode::BLINK_FAST: return (t % 250) < 125;
    case LedMode::FAULT_CODE: {
      const uint32_t on_off = 400, pause = 1200;
      const uint32_t cycle = n * on_off + pause;
      const uint32_t p = t % cycle;
      return p < n * on_off && (p % on_off) < 200;
    }
  }
  return false;
}
Rgb led_rgb(LedColor c) {
  switch (c) {
    case LedColor::OFF: return {0, 0, 0};
    case LedColor::GREEN: return {0, 64, 0};
    case LedColor::BLUE: return {0, 0, 64};
    case LedColor::AMBER: return {64, 32, 0};
    case LedColor::RED: return {64, 0, 0};
    case LedColor::WHITE: return {40, 40, 40};
  }
  return {0, 0, 0};
}
const char* sign_text(Sign s) {
  switch (s) {
    case Sign::WELCOME: return "WELCOME";
    case Sign::PLEASE_WAIT: return "PLEASE WAIT";
    case Sign::GRANTED: return "PROCEED";
    case Sign::SEE_GUARD: return "SEE GUARD";
    case Sign::CLOSING: return "WAIT";
    case Sign::OBSTACLE: return "OBSTACLE";
    case Sign::LANE_OPEN: return "LANE OPEN";
    case Sign::LANE_CLOSED: return "LANE CLOSED";
    case Sign::STOPPED: return "STOPPED";
    case Sign::COUNT_: break;
  }
  return "";
}
}  // namespace pf
