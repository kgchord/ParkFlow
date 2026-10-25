// Pure helpers that turn (pattern, time) into the instantaneous LED/buzzer level,
// plus the sign text table. Hardware writes happen in the HAL.
#pragma once
#include "types.h"
namespace pf {
bool buzzer_level(Buzz b, uint32_t t_ms);
// true = LED lit at time t. FAULT_CODE: n blinks (200 ms on / 200 ms off) then 1.2 s pause.
bool led_lit(LedMode m, uint8_t n, uint32_t t_ms);
struct Rgb { uint8_t r, g, b; };
Rgb led_rgb(LedColor c);
const char* sign_text(Sign s);
}  // namespace pf
