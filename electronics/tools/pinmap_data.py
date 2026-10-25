"""Hand-written semantics for each ESP32-S3 net in gen_lane_controller_sch.py.
The GPIO -> net binding is NOT here: it is read from the schematic generator's `esp` dict, so PINMAP.md cannot drift.
Each entry: net -> (function, direction wrt MCU, level, protection / reset-state text, refs that text cites).
gen_lane_controller_sch.py asserts that every cited ref really sits on that net or one hop away."""
INFO = {
 'MOT_ISENSE':   ('H-bridge current sense (IBT-2 module R_IS / L_IS outputs, 1k on the module)', 'in (ADC1)', '0 to 3.3 V analog', 'R29 1k series + D9 BAT54S clamp to 3V3/GND + C18 10nF; module IS pins (J14.5/J14.6) joined through R91/R92 100R; R28 is DNP because the module already has 1k to GND on each IS pin. Scale about 0.1 V/A (kILIS ~8.5 mA/A typ, to be bench-calibrated)', ['R29', 'D9', 'C18', 'R28', 'R91', 'R92']),
 'BAT_OK':       ('Battery/UPS OK, opto-isolated 24 V input (J6.2)', 'in', '3.3 V, HIGH = OK', 'PC817 U16 opto + R61 10k pull-down + C35 10nF filter; 24 V side has 1N4148W reverse diode', ['R61', 'C35']),
 'V24_SENSE':    ('24 V bus monitor (100k/10k divider)', 'in (ADC1)', '0 to 2.5 V for 27.6 V in', 'R2 100k + R3 10k + C2 100nF; no clamp, R2 limits injected current', ['R2', 'R3', 'C2']),
 'MOT_IN_A':     ('H-bridge OPEN request (to RPWM through U19, gated by ESTOP_OK)', 'out', '3.3 V CMOS', 'R32 100k pull-down: request LOW at reset; U19 74AHCT1G08 level-shifts to 5 V and ANDs ESTOP_OK', ['R32', 'U19']),
 'MOT_IN_B_MCU': ('H-bridge CLOSE request (to LPWM through U10, gated by beam)', 'out', '3.3 V CMOS', 'R31 100k pull-down; U10 74AHCT1G08 forces LPWM LOW unless BEAM_CLEAR=1 and level-shifts to 5 V', ['R31', 'U10']),
 'MOT_EN_MCU':   ('Motor enable request (gated by E-stop sense into R_EN/L_EN)', 'out', '3.3 V CMOS', 'R30 100k pull-down; U9 74AHCT1G08 AND-gate with ESTOP_OK drives IBT-2 R_EN and L_EN (J14.3/J14.4) at 5 V', ['R30', 'U9']),
 'ESTOP_OK':     ('E-stop loop healthy sense (also hard-wired into U9)', 'in', '3.3 V, HIGH = loop closed', 'PC817 U17 + R82 4.7k + R83 10k pull-down + C36 10nF; broken loop reads LOW', ['R82', 'R83', 'C36', 'U17', 'U9']),
 'LIM_UP_OK':    ('Limit switch UP (J5.3), NC wiring', 'in', '3.3 V, HIGH = switch closed (not at limit)', 'PC817 U11 + R40 4.7k + D10 reverse diode + R41 10k + C30 10nF', ['R41', 'C30']),
 'LIM_DN_OK':    ('Limit switch DOWN (J5.4), NC wiring', 'in', '3.3 V, HIGH = switch closed (not at limit)', 'PC817 U12 + R44 4.7k + D11 + R45 10k + C31 10nF', ['R45', 'C31']),
 'BEAM_CLEAR':   ('Photo-beam clear (J5.5, PNP light-ON receiver drives 24 V when clear); also gates CLOSE in hardware', 'in', '3.3 V, HIGH = beam clear', 'PC817 U13 + R48 4.7k + D12 + R49 10k + C32 10nF; same net feeds U10 pin 2', ['R49', 'C32', 'U10']),
 'PRESENCE':     ('Presence/vehicle-under-boom sensor (J5.6)', 'in', '3.3 V, HIGH = sensor output active', 'PC817 U14 + R52 4.7k + D13 + R53 10k + C33 10nF', ['R53', 'C33']),
 'AC_OK':        ('Mains OK from PSU/UPS dry contact (J6.1)', 'in', '3.3 V, HIGH = mains OK', 'PC817 U15 + R56 4.7k + D14 + R57 10k + C34 10nF', ['R57', 'C34']),
 'WDT_WDI':      ('Watchdog kick to TPS3823-33 (toggle faster than 0.9 s)', 'out', '3.3 V CMOS', 'High-Z at reset: TPS3823 generates its own pulses so it does not reset during boot', ['U5']),
 'RS485_DI':     ('RS485 TX data to THVD1450 DI (UART1 TX)', 'out', '3.3 V CMOS', 'Direct 3.3 V logic to U6 (bus side protected by SM712 D7, termination R25/JP1)', ['U6', 'D7']),
 'RS485_RO':     ('RS485 RX data from THVD1450 RO (UART1 RX)', 'in', '3.3 V CMOS', 'Direct, driven by transceiver at 3.3 V', ['U6']),
 'RS485_DE':     ('RS485 driver enable, DE and /RE tied together', 'out', '3.3 V CMOS, HIGH = transmit', 'R22 10k pull-down: receive mode at reset', ['R22', 'U6']),
 'BUZ_CTRL':     ('Buzzer driver (24 V piezo, low-side MOSFET Q5)', 'out', '3.3 V CMOS', 'R77 100R series + R78 100k pull-down on gate: buzzer off at reset; D17 flyback', ['R77', 'R78', 'Q5']),
 'GPIO19_USB_DN':('USB D- (native USB-Serial-JTAG) to J12', 'bidir', 'USB 3.3 V differential', 'R14 22R series + USBLC6-2SC6 U3 at the connector', ['R14', 'U3']),
 'GPIO20_USB_DP':('USB D+ (native USB-Serial-JTAG) to J12', 'bidir', 'USB 3.3 V differential', 'R13 22R series + USBLC6-2SC6 U3 at the connector', ['R13', 'U3']),
 'WS2812_3V3':   ('Status RGB ring data (via 74HCT245 U18 to 5 V)', 'out', '3.3 V CMOS into 74HCT245 input (TTL-compatible threshold; verify VIH against the datasheet)', 'U18 level shifter, R76 330R series at the ring, C21 bulk on ring supply', ['U18', 'R76']),
 'HUB_A_3V3':    ('HUB12 row-select A (to J9 via U18)', 'out', '3.3 V CMOS into HCT', 'U18 buffer + R70 33R series', ['U18', 'R70']),
 'HUB_B_3V3':    ('HUB12 row-select B (to J9 via U18)', 'out', '3.3 V CMOS into HCT', 'U18 buffer + R71 33R series', ['U18', 'R71']),
 'HUB_CLK_3V3':  ('HUB12 shift clock (to J9 via U18)', 'out', '3.3 V CMOS into HCT', 'U18 buffer + R72 33R series', ['U18', 'R72']),
 'HUB_LAT_3V3':  ('HUB12 latch (to J9 via U18)', 'out', '3.3 V CMOS into HCT', 'U18 buffer + R73 33R series', ['U18', 'R73']),
 'HUB_OE_3V3':   ('HUB12 output enable, HIGH = sign dark (to J9 via U18)', 'out', '3.3 V CMOS into HCT', 'R64 10k pull-up: sign dark at reset', ['R64', 'U18', 'R74']),
 'HUB_R_3V3':    ('HUB12 red data (to J9 via U18)', 'out', '3.3 V CMOS into HCT', 'U18 buffer + R75 33R series', ['U18', 'R75']),
 'K1_EN':        ('Motor-power relay/contactor K1 coil enable (Q4 low side)', 'out', '3.3 V CMOS, HIGH = K1 on', 'R80 100R series + R81 100k pull-down on Q4 gate: K1 off at reset; E-stop breaks the coil supply regardless', ['R80', 'R81', 'Q4']),
 'EDGE_RX':      ('Link from Edge Node, UART0 RX (GPIO44)', 'in', '3.3 V TTL', 'R18 100R series to J11.3', ['R18']),
 'EDGE_TX':      ('Link to Edge Node, UART0 TX (GPIO43)', 'out', '3.3 V TTL', 'R17 100R series to J11.2', ['R17']),
 'ESP_EN':       ('Chip enable / reset', 'in', '3.3 V, LOW = reset', 'R15 10k pull-up + C14 1uF + SW2 RESET + Q2 (Pi) + D5 (watchdog)', ['R15', 'C14', 'SW2', 'Q2', 'D5']),
 'GPIO0_BOOT':   ('BOOT select (strapping)', 'in at reset', '3.3 V, LOW at reset = download mode', 'R16 10k pull-up + SW1 BOOT + Q3 (Pi auto-flash)', ['R16', 'SW1', 'Q3']),
}
GPIO_ALIAS = {'RXD0': 44, 'TXD0': 43}      # WROOM-1 module pin names for UART0
STRAP = {
 0:  'STRAPPING (Table 4-1: weak pull-up, default 1). External 10k pull-up R16 keeps it HIGH = SPI boot; SW1/Q3 pull it LOW only on purpose. OK.',
 3:  'STRAPPING (Table 4-1: floating, JTAG source select). Left unconnected on purpose; do not drive. OK.',
 45: 'STRAPPING (Table 4-1: weak pull-down, default 0). Left unconnected so the module keeps its factory setting. OK.',
 46: 'STRAPPING (Table 4-1: weak pull-down, default 0). Left unconnected. OK.',
}
RESERVED = {35: 'reserved for octal PSRAM on the N16R8 module (Table 3-1 note b)', 36: 'reserved for octal PSRAM on the N16R8 module (Table 3-1 note b)', 37: 'reserved for octal PSRAM on the N16R8 module (Table 3-1 note b)'}
