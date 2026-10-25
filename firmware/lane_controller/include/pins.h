// ESP32-S3-WROOM-1 pin assignment for the ParkFlow Lane Controller (Rev A).
// SOURCE OF TRUTH: electronics/tools/gen_lane_controller_sch.py, dict `esp`.
// If the schematic changes, change this file (test_pins in the host suite
// cross-checks the table below against itself for duplicates only; it cannot
// read the Python script).
#pragma once
namespace pf {
namespace pins {
constexpr int BOOT_BTN   = 0;   // GPIO0_BOOT  (also used as RE-ARM button after boot, see FIRMWARE.md)
constexpr int MOT_ISENSE = 1;   // ADC1_CH0, IBT-2 module R_IS/L_IS via R91/R92 100R + R29 1k + clamp
constexpr int BAT_OK     = 2;   // opto in, UPS battery OK (HIGH = ok)
constexpr int V24_SENSE  = 4;   // ADC1_CH3, 100k/10k divider on +24V
constexpr int MOT_IN_A   = 5;   // H-bridge half A IN (OPEN drive)
constexpr int MOT_IN_B   = 6;   // H-bridge half B IN (CLOSE drive); PCB gates it with BEAM_CLEAR (U10)
constexpr int MOT_EN     = 7;   // H-bridge INH request; PCB ANDs it with ESTOP_OK (U9)
constexpr int ESTOP_OK   = 8;   // opto in, HIGH = E-stop loop healthy
constexpr int LIM_UP_OK  = 9;   // opto in, NC switch: HIGH = NOT at limit, LOW = reached or wire break
constexpr int LIM_DN_OK  = 10;  // same polarity as LIM_UP_OK
constexpr int BEAM_CLEAR = 11;  // opto in, HIGH = beam clear (light-ON receiver); LOW = broken or cable cut
constexpr int PRESENCE   = 12;  // opto in, HIGH = occupied (ASSUMED: sensor type not fixed by schematic)
constexpr int AC_OK      = 13;  // opto in, HIGH = mains OK (PSU relay closed)
constexpr int WDT_WDI    = 14;  // TPS3823-33 WDI, toggled to kick external watchdog (1.6 s)
constexpr int RS485_DI   = 15;  // ESP TX -> THVD1450 DI
constexpr int RS485_RO   = 16;  // ESP RX <- THVD1450 RO
constexpr int RS485_DE   = 17;  // DE and /RE tied together
constexpr int BUZ_CTRL   = 18;  // 24 V piezo, low-side MOSFET, HIGH = sound
constexpr int USB_DN     = 19;  // native USB (programming)
constexpr int USB_DP     = 20;
constexpr int WS2812     = 21;  // status RGB LED (via 74HCT245 level shift)
constexpr int HUB_A      = 38;  // HUB12 via 74HCT245
constexpr int HUB_B      = 39;
constexpr int HUB_CLK    = 40;
constexpr int HUB_LAT    = 41;
constexpr int HUB_OE     = 42;  // R64 pull-up: sign blanked at reset
constexpr int HUB_R      = 47;  // HUB12 data
constexpr int K1_EN      = 48;  // contactor coil driver, HIGH = energise K1 (motor power on)
constexpr int EDGE_TX    = 43;  // UART0 TXD0 -> Edge Node (R17 100R)
constexpr int EDGE_RX    = 44;  // UART0 RXD0 <- Edge Node (R18 100R)
}  // namespace pins
}  // namespace pf
