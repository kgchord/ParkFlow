// ESP-IDF v5.x HAL for the ParkFlow Lane Controller. UNTESTED ON TARGET (not yet
// built with ESP-IDF). Pin numbers come from pins.h (= schematic). Review points:
//  * RS485: UART1 in IDF RS485 half-duplex mode, RTS pin = DE (DE and /RE are tied on the PCB).
//  * Edge link: UART0 pins GPIO43/44 (the default console UART is moved to USB-Serial-JTAG in sdkconfig.defaults).
//  * ADC: uncalibrated linear estimate; use adc_cali_* and the commissioning procedure before trusting mV.
//  * WS2812 and HUB12 are stubs (log only). TODO: led_strip (RMT) and a 1/4-scan HUB12 refresh task.
#include "hal_esp32s3.h"
#include "driver/gpio.h"
#include "driver/uart.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_log.h"
#include "esp_task_wdt.h"
#include "esp_timer.h"
#include "pins.h"

namespace pf {
namespace {
const char* TAG = "hal";

class Esp32s3Hal : public IHal {
 public:
  Esp32s3Hal() {
    const int outs[] = {pins::MOT_IN_A, pins::MOT_IN_B, pins::MOT_EN, pins::K1_EN, pins::BUZ_CTRL, pins::WDT_WDI,
                        pins::HUB_A, pins::HUB_B, pins::HUB_CLK, pins::HUB_LAT, pins::HUB_OE, pins::HUB_R, pins::WS2812};
    for (int p : outs) { gpio_reset_pin((gpio_num_t)p); gpio_set_direction((gpio_num_t)p, GPIO_MODE_OUTPUT); gpio_set_level((gpio_num_t)p, 0); }
    gpio_set_level((gpio_num_t)pins::HUB_OE, 1);   // sign blanked (OE high) until the stub is replaced
    const int ins[] = {pins::LIM_UP_OK, pins::LIM_DN_OK, pins::BEAM_CLEAR, pins::PRESENCE, pins::ESTOP_OK, pins::AC_OK, pins::BAT_OK, pins::BOOT_BTN};
    for (int p : ins) { gpio_reset_pin((gpio_num_t)p); gpio_set_direction((gpio_num_t)p, GPIO_MODE_INPUT); }

    uart_config_t uc = {};
    uc.baud_rate = 115200; uc.data_bits = UART_DATA_8_BITS; uc.parity = UART_PARITY_DISABLE; uc.stop_bits = UART_STOP_BITS_1;
    uc.flow_ctrl = UART_HW_FLOWCTRL_DISABLE; uc.source_clk = UART_SCLK_DEFAULT;
    uart_driver_install(UART_NUM_0, 512, 512, 0, nullptr, 0);
    uart_param_config(UART_NUM_0, &uc);
    uart_set_pin(UART_NUM_0, pins::EDGE_TX, pins::EDGE_RX, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
    uc.baud_rate = 9600;   // PLACEHOLDER: set to the reader's real RS485 baud rate once its datasheet is verified
    uart_driver_install(UART_NUM_1, 512, 512, 0, nullptr, 0);
    uart_param_config(UART_NUM_1, &uc);
    uart_set_pin(UART_NUM_1, pins::RS485_DI, pins::RS485_RO, pins::RS485_DE, UART_PIN_NO_CHANGE);
    uart_set_mode(UART_NUM_1, UART_MODE_RS485_HALF_DUPLEX);

    adc_oneshot_unit_init_cfg_t ic = {}; ic.unit_id = ADC_UNIT_1;
    adc_oneshot_new_unit(&ic, &adc_);
    adc_oneshot_chan_cfg_t cc = {}; cc.atten = ADC_ATTEN_DB_12; cc.bitwidth = ADC_BITWIDTH_DEFAULT;
    adc_unit_t u; adc_oneshot_io_to_channel(pins::MOT_ISENSE, &u, &ch_is_);  adc_oneshot_config_channel(adc_, ch_is_, &cc);
    adc_oneshot_io_to_channel(pins::V24_SENSE, &u, &ch_v24_); adc_oneshot_config_channel(adc_, ch_v24_, &cc);
    ESP_LOGW(TAG, "HAL up (untested-on-target build)");
  }
  uint32_t now_ms() override { return (uint32_t)(esp_timer_get_time() / 1000); }
  RawInputs read_inputs() override {
    RawInputs r;
    r.lim_up_ok = gpio_get_level((gpio_num_t)pins::LIM_UP_OK);
    r.lim_dn_ok = gpio_get_level((gpio_num_t)pins::LIM_DN_OK);
    r.beam_clear = gpio_get_level((gpio_num_t)pins::BEAM_CLEAR);
    r.presence = gpio_get_level((gpio_num_t)pins::PRESENCE);
    r.estop_ok = gpio_get_level((gpio_num_t)pins::ESTOP_OK);
    r.ac_ok = gpio_get_level((gpio_num_t)pins::AC_OK);
    r.bat_ok = gpio_get_level((gpio_num_t)pins::BAT_OK);
    r.rearm_btn_low = !gpio_get_level((gpio_num_t)pins::BOOT_BTN);
    return r;
  }
  uint16_t adc_isense_mv() override { return read_mv(ch_is_); }
  uint16_t adc_v24_mv() override { return (uint16_t)(read_mv(ch_v24_) * 11u); }   // 100k/10k divider
  void set_motor(bool a, bool b, bool en) override {
    // order matters: drop enable first, then change direction, then raise enable
    gpio_set_level((gpio_num_t)pins::MOT_EN, 0);
    gpio_set_level((gpio_num_t)pins::MOT_IN_A, a);
    gpio_set_level((gpio_num_t)pins::MOT_IN_B, b);
    gpio_set_level((gpio_num_t)pins::MOT_EN, en);
  }
  void set_contactor(bool on) override { gpio_set_level((gpio_num_t)pins::K1_EN, on); }
  void set_buzzer(bool on) override { gpio_set_level((gpio_num_t)pins::BUZ_CTRL, on); }
  void set_led_rgb(uint8_t r, uint8_t g, uint8_t b) override { (void)r; (void)g; (void)b; /* TODO led_strip RMT on GPIO21 */ }
  void sign_show(const char* text) override { ESP_LOGI(TAG, "SIGN: %s (HUB12 stub)", text); }
  size_t rs485_read(uint8_t* b, size_t cap) override { int n = uart_read_bytes(UART_NUM_1, b, cap, 0); return n > 0 ? (size_t)n : 0; }
  void rs485_write(const uint8_t* b, size_t n) override { uart_write_bytes(UART_NUM_1, b, n); uart_wait_tx_done(UART_NUM_1, 50 / portTICK_PERIOD_MS); }
  size_t edge_read(uint8_t* b, size_t cap) override { int n = uart_read_bytes(UART_NUM_0, b, cap, 0); return n > 0 ? (size_t)n : 0; }
  void edge_write(const uint8_t* b, size_t n) override { uart_write_bytes(UART_NUM_0, b, n); }
  void wdi_toggle() override { wdi_ = !wdi_; gpio_set_level((gpio_num_t)pins::WDT_WDI, wdi_); }
  void task_wdt_reset() override { esp_task_wdt_reset(); }

 private:
  uint16_t read_mv(adc_channel_t ch) {
    int raw = 0;
    adc_oneshot_read(adc_, ch, &raw);
    return (uint16_t)((raw * 3100) / 4095);   // uncalibrated approximation (12 dB range ~ 0..3.1 V)
  }
  adc_oneshot_unit_handle_t adc_ = nullptr;
  adc_channel_t ch_is_, ch_v24_;
  bool wdi_ = false;
};
}  // namespace

IHal& esp32s3_hal() { static Esp32s3Hal h; return h; }
}  // namespace pf
