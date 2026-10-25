// Hardware abstraction layer. The state machine never sees this; LaneApp does.
// Two implementations: hal_esp32s3/ (ESP-IDF, NOT compiled in this repo's host
// CI, untested on target) and test/mock_hal.h (host).
#pragma once
#include <cstddef>
#include <cstdint>
namespace pf {

// Raw GPIO logic levels exactly as seen at the ESP32-S3 pins (see pins.h for polarity).
struct RawInputs {
  bool lim_up_ok = true, lim_dn_ok = true;   // HIGH = not at limit
  bool beam_clear = true;                    // HIGH = clear
  bool presence = false;                     // HIGH = occupied
  bool estop_ok = true, ac_ok = true, bat_ok = true;
  bool rearm_btn_low = false;                // BOOT button pressed (active low) -> true
};

class IHal {
 public:
  virtual ~IHal() {}
  virtual uint32_t now_ms() = 0;
  virtual RawInputs read_inputs() = 0;
  virtual uint16_t adc_isense_mv() = 0;
  virtual uint16_t adc_v24_mv() = 0;        // after the 100k/10k divider is undone
  // Motor: PCB ANDs `en` with ESTOP_OK and gates `in_b` with BEAM_CLEAR in hardware.
  virtual void set_motor(bool in_a, bool in_b, bool en) = 0;
  virtual void set_contactor(bool on) = 0;
  virtual void set_buzzer(bool on) = 0;
  virtual void set_led_rgb(uint8_t r, uint8_t g, uint8_t b) = 0;
  virtual void sign_show(const char* text) = 0;      // HUB12 stub
  virtual size_t rs485_read(uint8_t* buf, size_t cap) = 0;          // non-blocking
  virtual void rs485_write(const uint8_t* buf, size_t n) = 0;       // handles DE, blocks until sent
  virtual size_t edge_read(uint8_t* buf, size_t cap) = 0;           // non-blocking
  virtual void edge_write(const uint8_t* buf, size_t n) = 0;
  virtual void wdi_toggle() = 0;                    // kick TPS3823 (edge on WDI)
  virtual void task_wdt_reset() = 0;                // ESP-IDF TWDT feed
};
}  // namespace pf
