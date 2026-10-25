#!/usr/bin/env python3
"""Generate the ParkFlow Lane Controller schematic (KiCad 7 .kicad_sch).

Every pin is joined to its net by a short wire stub and a net label, so the
netlist is correct by construction. After writing, run
  kicad-cli sch export netlist -o lane_controller.net lane_controller.kicad_sch
and verify_netlist() compares KiCad's netlist against the intended one.
"""
import os, re, sys, subprocess, collections
sys.path.insert(0, os.path.dirname(__file__))
import schlib

OUT = os.path.join(os.path.dirname(__file__), '..', 'kicad')
SCH = os.path.join(OUT, 'lane_controller.kicad_sch')

schlib.CUSTOM_LIB = os.path.join(OUT, 'ParkFlow.kicad_sym')
schlib.write_custom_lib(schlib.CUSTOM_LIB)
s = schlib.Sch('ParkFlow Lane Controller (ESP32-S3) - Rev A', 'lane_controller')
intended = collections.defaultdict(set)

def P(lib, name, ref, value, at, nets, rot=0, fp='', extra=None, dnp=False):
    s.add(lib, name, ref, value, at, nets, rot_=rot, fp=fp, extra=extra, dnp=dnp)
    _, pins = schlib._extract(lib, name)
    for p in pins:
        n = nets.get(p['num'], nets.get(p['name']))
        if n and n != 'NC':
            intended[n].add((ref, p['num']))

R = lambda ref, val, at, a, b, rot=0, fp='Resistor_SMD:R_0603_1608Metric': P('Device', 'R', ref, val, at, {'1': a, '2': b}, rot, fp)
C = lambda ref, val, at, a, b, rot=0, fp='Capacitor_SMD:C_0603_1608Metric': P('Device', 'C', ref, val, at, {'1': a, '2': b}, rot, fp)

# ------------------------------------------------------------------ titles
s.text('1. 24 V INPUT PROTECTION (fuse, reverse-polarity P-FET, TVS)', (20, 25), 2.5)
s.text('2. 24 V -> 5 V BUCK  (TPS54560, 5 A)', (20, 125), 2.5)
s.text('3. 5 V -> 3.3 V BUCK (TLV62569, 2 A) + USB-C', (20, 215), 2.5)
s.text('4. ESP32-S3-WROOM-1-N16R8 + RESET / BOOT / WATCHDOG / EDGE LINK', (250, 25), 2.5)
s.text('5. RS485 TO UHF RFID READER (THVD1450 + SM712)', (250, 215), 2.5)
s.text('6. H-BRIDGE: IBT-2 (BTS7960) MODULE HEADER + hardware interlocks (74AHCT1G08 @ 5 V)', (500, 25), 2.5)
s.text('7. OPTO-ISOLATED 24 V INPUTS (active-high: 24 V at the terminal = LED on = output HIGH)', (500, 222), 2.5)
s.text('8. E-STOP LOOP + CONTACTOR COIL DRIVER (firmware-independent motor cut)', (20, 330), 2.5)
s.text('9. HUB12 (P10) + WS2812 LEVEL SHIFT (74HCT245 @5 V), BUZZER', (250, 330), 2.5)
s.text('10. FIELD CONNECTORS (5.08 mm fixed screw terminals / JST-XH)', (500, 400), 2.5)
s.note('Notes: (a) Symbol MAX481E used for THVD1450DR (identical 8-pin RS485 pinout). (b) TLV62568DBV symbol used for TLV62569DBVR (same pinout).\n'
       '(c) 74LS245 symbol used for SN74HCT245PWR and 74LVC1G08 symbol used for the 74AHCT1G08 gates U9/U10/U19 (same pinout).\n'
       '(d) K1 is the external DIN contactor LC1D09BD (24 VDC coil); only its coil terminals reach this PCB. The motor power path (K1 contacts -> IBT-2 module B+/B- -> motor) does NOT pass over this PCB.\n'
       '(e) Values marked * are design targets - verify against datasheets during layout. (f) GPIO3/45/46 (straps) and GPIO35-37 (octal PSRAM on N16R8) left unconnected; module is the BOM part N16R8, the N8 is footprint- and pin-compatible.',
       (20, 560), 1.5)

# ------------------------------------------------------------------ 1. input protection
P('Connector', 'Screw_Terminal_01x02', 'J1', '24V_LOGIC_IN', (30, 50), {'1': 'VIN_RAW', '2': 'GND'},
  fp='TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-3-2-5.08_1x02_P5.08mm_Horizontal')
P('Device', 'Fuse', 'F1', '3A NANO2 0451003.MRL (very fast-acting)', (55, 50), {'1': 'VIN_RAW', '2': 'VIN_F'}, rot=90, fp='Fuse:Fuse_Littelfuse-NANO2-451_453')
# reverse polarity P-FET: drain = VIN_F side, source = +24V, gate -> GND via 10k, zener G-S
P('Device', 'Q_PMOS_GDS', 'Q1', 'FQD11P06 (-60V P-FET)*', (85, 55), {'1': 'Q1_G', '2': 'VIN_F', '3': '+24V'}, fp='Package_TO_SOT_SMD:TO-252-2')
P('Device', 'D_Zener', 'D1', 'BZT52C15 (Vgs clamp)', (110, 70), {'1': '+24V', '2': 'Q1_G'}, rot=90, fp='Diode_SMD:D_SOD-123')
R('R1', '10k', (85, 85), 'Q1_G', 'GND')
P('Device', 'D_TVS', 'D2', 'SMBJ33A', (130, 70), {'1': 'GND', '2': '+24V'}, rot=90, fp='Diode_SMD:D_SMB')
P('Device', 'C_Polarized', 'C1', '100uF 50V', (150, 70), {'1': '+24V', '2': 'GND'}, fp='Capacitor_SMD:CP_Elec_10x10.5')
R('R2', '100k', (175, 60), '+24V', 'V24_SENSE')
R('R3', '10k', (175, 90), 'V24_SENSE', 'GND')
C('C2', '100nF', (195, 90), 'V24_SENSE', 'GND')
P('power', 'PWR_FLAG', '#FLG01', 'PWR_FLAG', (200, 45), {'1': '+24V'})
P('power', 'PWR_FLAG', '#FLG02', 'PWR_FLAG', (215, 45), {'1': 'GND'})
# field supply polyfuse
P('Device', 'Polyfuse', 'F2', 'MF-R075 (0.75A hold, 60V)', (220, 75), {'1': '+24V', '2': '+24V_FIELD'}, fp='Fuse:Fuse_Bourns_MF-RG500')

# ------------------------------------------------------------------ 2. 5 V buck
P('Regulator_Switching', 'TPS54560BDDA', 'U1', 'TPS54560BDDA', (70, 165),
  {'BOOT': 'U1_BOOT', 'VIN': '+24V', 'EN': 'U1_EN', 'RT/CLK': 'U1_RT', 'FB': 'U1_FB', 'COMP': 'U1_COMP', 'GND': 'GND', 'SW': 'U1_SW'},
  fp='Package_SO:TI_SO-PowerPAD-8_ThermalVias')
C('C3', '4.7uF 50V X7R', (25, 150), '+24V', 'GND', fp='Capacitor_SMD:C_1210_3225Metric')
C('C4', '4.7uF 50V X7R', (50, 150), '+24V', 'GND', fp='Capacitor_SMD:C_1210_3225Metric')
R('R4', '200k (fsw 500 kHz)', (25, 185), 'U1_RT', 'GND')
R('R5', '10k* (Rc)', (55, 185), 'U1_COMP', 'U1_CC')
C('C5', '6.8nF* (Cc)', (55, 200), 'U1_CC', 'GND')
R('R6', '100k (EN/UVLO upper)', (75, 135), '+24V', 'U1_EN')
R('R90', '10k (EN/UVLO lower, UVLO ~13 V)', (90, 135), 'U1_EN', 'GND')
C('C6', '100nF', (105, 140), 'U1_BOOT', 'U1_SW')
P('Device', 'D_Schottky', 'D3', 'B560C (60V 5A)', (110, 190), {'K': 'U1_SW', 'A': 'GND'}, rot=90, fp='Diode_SMD:D_SMC')
P('Device', 'L', 'L1', '6.8uH Isat>=7A*', (130, 160), {'1': 'U1_SW', '2': '+5V'}, rot=90, fp='Inductor_SMD:L_12x12mm_H8mm')
R('R7', '53.6k (Vout=5.09V)', (150, 185), '+5V', 'U1_FB')
R('R8', '10k', (180, 185), 'U1_FB', 'GND')
C('C7', '47uF 10V X5R', (185, 165), '+5V', 'GND', fp='Capacitor_SMD:C_1210_3225Metric')
C('C8', '47uF 10V X5R', (215, 165), '+5V', 'GND', fp='Capacitor_SMD:C_1210_3225Metric')
P('power', 'PWR_FLAG', '#FLG03', 'PWR_FLAG', (230, 150), {'1': '+5V'})

# ------------------------------------------------------------------ 3. 3.3 V buck + USB-C
P('Regulator_Switching', 'TLV62568DBV', 'U2', 'TLV62569DBVR', (60, 245),
  {'EN': '+5V_LOGIC', 'GND': 'GND', 'SW': 'U2_SW', 'VIN': '+5V_LOGIC', 'FB': 'U2_FB'}, fp='Package_TO_SOT_SMD:SOT-23-5')
C('C9', '10uF 10V', (30, 245), '+5V_LOGIC', 'GND', fp='Capacitor_SMD:C_0805_2012Metric')
P('Device', 'L', 'L2', '2.2uH 3A', (90, 235), {'1': 'U2_SW', '2': '+3V3'}, rot=90, fp='Inductor_SMD:L_Taiyo-Yuden_NR-40xx')
R('R9', '453k', (105, 255), '+3V3', 'U2_FB')
R('R10', '100k', (120, 255), 'U2_FB', 'GND')
C('C10', '22uF 10V', (140, 245), '+3V3', 'GND', fp='Capacitor_SMD:C_0805_2012Metric')
C('C11', '22uF 10V', (155, 245), '+3V3', 'GND', fp='Capacitor_SMD:C_0805_2012Metric')
P('power', 'PWR_FLAG', '#FLG04', 'PWR_FLAG', (170, 230), {'1': '+3V3'})
# USB-C (programming / native USB-JTAG on GPIO19/20)
P('Connector', 'USB_C_Receptacle_USB2.0_16P', 'J12', 'USB-C 16P (GCT USB4105-GF-A)', (40, 300),
  {'GND': 'GND', 'VBUS': 'VBUS', 'CC1': 'USB_CC1', 'CC2': 'USB_CC2', 'D+': 'USB_DP_C', 'D-': 'USB_DN_C',
   'SBU1': 'NC', 'SBU2': 'NC', 'SHIELD': 'GND'}, fp='Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal')
R('R11', '5.1k', (80, 280), 'USB_CC1', 'GND')
R('R12', '5.1k', (92, 280), 'USB_CC2', 'GND')
P('Power_Protection', 'USBLC6-2P6', 'U3', 'USBLC6-2SC6', (115, 300),
  {'1': 'USB_DP_C', '6': 'USB_DP', '3': 'USB_DN_C', '4': 'USB_DN', '2': 'GND', '5': 'VBUS'}, fp='Package_TO_SOT_SMD:SOT-23-6')
P('Device', 'D_Schottky', 'D4', 'SS14 (VBUS OR)', (150, 290), {'A': 'VBUS', 'K': '+5V_LOGIC'}, fp='Diode_SMD:D_SMA')
P('Device', 'D_Schottky', 'D18', 'SS14 (5V OR)', (150, 275), {'A': '+5V', 'K': '+5V_LOGIC'}, fp='Diode_SMD:D_SMA')
P('power', 'PWR_FLAG', '#FLG05', 'PWR_FLAG', (185, 230), {'1': '+5V_LOGIC'})
R('R13', '22R', (170, 300), 'USB_DP', 'GPIO20_USB_DP', rot=90)
R('R14', '22R', (170, 312), 'USB_DN', 'GPIO19_USB_DN', rot=90)

# ------------------------------------------------------------------ 4. ESP32-S3
esp = {
    '3V3': '+3V3', 'GND': 'GND', 'EN': 'ESP_EN',
    'IO0': 'GPIO0_BOOT', 'IO1': 'MOT_ISENSE', 'IO2': 'BAT_OK', 'IO3': 'NC', 'IO4': 'V24_SENSE',
    'IO5': 'MOT_IN_A', 'IO6': 'MOT_IN_B_MCU', 'IO7': 'MOT_EN_MCU', 'IO8': 'ESTOP_OK', 'IO9': 'LIM_UP_OK',
    'IO10': 'LIM_DN_OK', 'IO11': 'BEAM_CLEAR', 'IO12': 'PRESENCE', 'IO13': 'AC_OK', 'IO14': 'WDT_WDI',
    'IO15': 'RS485_DI', 'IO16': 'RS485_RO', 'IO17': 'RS485_DE', 'IO18': 'BUZ_CTRL',
    'IO19': 'GPIO19_USB_DN', 'IO20': 'GPIO20_USB_DP', 'IO21': 'WS2812_3V3',
    'IO35': 'NC', 'IO36': 'NC', 'IO37': 'NC',
    'IO38': 'HUB_A_3V3', 'IO39': 'HUB_B_3V3', 'IO40': 'HUB_CLK_3V3', 'IO41': 'HUB_LAT_3V3', 'IO42': 'HUB_OE_3V3',
    'IO45': 'NC', 'IO46': 'NC', 'IO47': 'HUB_R_3V3', 'IO48': 'K1_EN',
    'RXD0': 'EDGE_RX', 'TXD0': 'EDGE_TX',
}
P('RF_Module', 'ESP32-S3-WROOM-1', 'U4', 'ESP32-S3-WROOM-1-N16R8', (340, 110), esp, fp='RF_Module:ESP32-S3-WROOM-1')
C('C12', '22uF', (300, 55), '+3V3', 'GND', fp='Capacitor_SMD:C_0805_2012Metric')
C('C13', '100nF', (312, 55), '+3V3', 'GND')
R('R15', '10k', (270, 60), '+3V3', 'ESP_EN')
C('C14', '1uF', (270, 85), 'ESP_EN', 'GND')
R('R16', '10k', (270, 110), '+3V3', 'GPIO0_BOOT')
P('Switch', 'SW_Push', 'SW1', 'BOOT', (270, 135), {'1': 'GPIO0_BOOT', '2': 'GND'}, fp='Button_Switch_SMD:SW_SPST_TL3342')
P('Switch', 'SW_Push', 'SW2', 'RESET', (270, 150), {'1': 'ESP_EN', '2': 'GND'}, fp='Button_Switch_SMD:SW_SPST_TL3342')
# external watchdog TPS3823-33 (WDI 1.6 s): RESET pulls EN low through Schottky (diode-OR with RC / Pi)
P('ParkFlow', 'TPS3823-33', 'U5', 'TPS3823-33DBVR (WDT 1.6 s)', (420, 60),
  {'1': 'WDT_RST_N', '2': 'GND', '3': '+3V3', '4': 'WDT_WDI', '5': '+3V3'}, fp='Package_TO_SOT_SMD:SOT-23-5')
P('Device', 'D_Schottky', 'D5', 'BAT54W', (450, 60), {'A': 'ESP_EN', 'K': 'WDT_RST_N'}, fp='Diode_SMD:D_SOD-323')
# Edge-Node link: UART0 3.3 V TTL + Pi-controlled EN/BOOT (auto-flash)
R('R17', '100R', (420, 110), 'EDGE_TX', 'J11_TX', rot=90)
R('R18', '100R', (420, 125), 'EDGE_RX', 'J11_RX', rot=90)
P('Device', 'Q_NMOS_GSD', 'Q2', '2N7002', (430, 150), {'G': 'PI_EN_CTRL', 'S': 'GND', 'D': 'ESP_EN'}, fp='Package_TO_SOT_SMD:SOT-23')
P('Device', 'Q_NMOS_GSD', 'Q3', '2N7002', (460, 150), {'G': 'PI_BOOT_CTRL', 'S': 'GND', 'D': 'GPIO0_BOOT'}, fp='Package_TO_SOT_SMD:SOT-23')
R('R19', '100k', (430, 180), 'PI_EN_CTRL', 'GND')
R('R20', '100k', (460, 180), 'PI_BOOT_CTRL', 'GND')
P('Connector_Generic', 'Conn_01x05', 'J11', 'EDGE LINK JST-XH 5P (B5B-XH-A)', (470, 110),
  {'1': 'GND', '2': 'J11_TX', '3': 'J11_RX', '4': 'PI_EN_CTRL', '5': 'PI_BOOT_CTRL'}, fp='Connector_JST:JST_XH_B5B-XH-A_1x05_P2.50mm_Vertical')
# status LED
R('R21', '1k', (300, 190), '+3V3', 'LED_PWR_A')
P('Device', 'LED', 'D6', 'GREEN 0603 (3V3 OK)', (300, 205), {'A': 'LED_PWR_A', 'K': 'GND'}, rot=270, fp='LED_SMD:LED_0603_1608Metric')

# ------------------------------------------------------------------ 5. RS485
P('Interface_UART', 'MAX481E', 'U6', 'THVD1450DR', (300, 260),
  {'RO': 'RS485_RO', '~{RE}': 'RS485_DE', 'DE': 'RS485_DE', 'DI': 'RS485_DI', 'GND': 'GND', 'A': 'RS485_A', 'B': 'RS485_B', 'VCC': '+3V3'},
  fp='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm')
C('C15', '100nF', (275, 240), '+3V3', 'GND')
R('R22', '10k (DE pull-down)', (275, 290), 'RS485_DE', 'GND')
R('R23', '680R fail-safe bias (DNP)', (345, 245), '+3V3', 'RS485_A')
R('R24', '680R fail-safe bias (DNP)', (345, 290), 'RS485_B', 'GND')
R('R25', '120R term', (365, 268), 'RS485_A', 'RS485_TERM')
P('Jumper', 'Jumper_2_Open', 'JP1', 'TERM EN', (390, 268), {'A': 'RS485_TERM', 'B': 'RS485_B'}, fp='Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical')
P('Diode', 'SM712_SOT23', 'D7', 'SM712', (420, 268), {'A1': 'RS485_A', 'A2': 'RS485_B', 'common': 'GND'}, fp='Package_TO_SOT_SMD:SOT-23')
P('Connector', 'Screw_Terminal_01x03', 'J7', 'RS485 RFID (A,B,0V)', (460, 268),
  {'1': 'RS485_A', '2': 'RS485_B', '3': 'GND'}, fp='TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-3-3-5.08_1x03_P5.08mm_Horizontal')

# ------------------------------------------------------------------ 6. H-bridge (IBT-2 / BTS7960 module, BOM part)
# The BOM part is the 43 A IBT-2 module (2x BTS7960, 5.5-27 V motor supply, 5 V logic via an on-board buffer).
# Its B+/B-/M+/M- screw terminals are wired directly: K1 contacts -> B+/B-, M+/M- -> motor. Only the 8 logic pins
# come to this PCB on J14. 3.3 V ESP32 outputs are level-shifted to 5 V by 74AHCT1G08 gates (VIH 2.0 V at Vcc 5 V),
# which also implement the hardware interlocks.
P('Connector_Generic', 'Conn_01x08', 'J14', 'IBT-2 LOGIC 1x8 (RPWM,LPWM,R_EN,L_EN,R_IS,L_IS,VCC,GND)', (530, 60),
  {'1': 'MOT_RPWM', '2': 'MOT_LPWM', '3': 'MOT_INH', '4': 'MOT_INH', '5': 'IS_A', '6': 'IS_B', '7': '+5V', '8': 'GND'},
  fp='Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical')
R('R28', '1k* R_IS (DNP: the IBT-2 module already has 1k on each IS pin)', (640, 175), 'MOT_IS', 'GND', )
R('R91', '100R (IS_A isolation)', (600, 160), 'IS_A', 'MOT_IS', rot=90)
R('R92', '100R (IS_B isolation)', (600, 172), 'IS_B', 'MOT_IS', rot=90)
R('R29', '1k', (660, 160), 'MOT_IS', 'MOT_ISENSE', rot=90)
P('Diode', 'BAT54S', 'D9', 'BAT54S (ADC clamp)', (690, 165), {'A': 'GND', 'K': '+3V3', 'COM': 'MOT_ISENSE'}, fp='Package_TO_SOT_SMD:SOT-23')
C('C18', '10nF', (710, 175), 'MOT_ISENSE', 'GND')
# hardware interlocks
P('74xGxx', '74LVC1G08', 'U9', '74AHCT1G08 (R_EN = L_EN = MOT_EN & ESTOP_OK, 5 V out)', (560, 185), {'1': 'MOT_EN_MCU', '2': 'ESTOP_OK', '3': 'GND', '4': 'MOT_INH', '5': '+5V'},
  fp='Package_TO_SOT_SMD:SOT-23-5')
P('74xGxx', '74LVC1G08', 'U10', '74AHCT1G08 (LPWM = CLOSE only if BEAM_CLEAR)', (630, 192), {'1': 'MOT_IN_B_MCU', '2': 'BEAM_CLEAR', '3': 'GND', '4': 'MOT_LPWM', '5': '+5V'},
  fp='Package_TO_SOT_SMD:SOT-23-5')
P('74xGxx', '74LVC1G08', 'U19', '74AHCT1G08 (RPWM = OPEN request & ESTOP_OK)', (700, 215), {'1': 'MOT_IN_A', '2': 'ESTOP_OK', '3': 'GND', '4': 'MOT_RPWM', '5': '+5V'},
  fp='Package_TO_SOT_SMD:SOT-23-5')
R('R30', '100k', (525, 195), 'MOT_EN_MCU', 'GND')
R('R31', '100k', (595, 192), 'MOT_IN_B_MCU', 'GND')
R('R32', '100k', (530, 140), 'MOT_IN_A', 'GND')
C('C19', '100nF', (700, 192), '+5V', 'GND')
C('C22', '100nF', (740, 215), '+5V', 'GND')

# ------------------------------------------------------------------ 7. opto inputs
# Active-high (sourcing-compatible) input: the field device drives 24 V onto terminal IN_x (PNP sensor output, or a
# dry contact / NC limit switch closing to +24V_FIELD). IN_x -> R(4.7k) -> LED anode, LED cathode -> GND.
# Output: emitter follower, collector +3V3, emitter -> 10k to GND -> GPIO (HIGH when LED on). Open or broken wire = LOW = safe.
inputs = [  # (ref idx, terminal net, logic net)
    ('IN_LIM_UP', 'LIM_UP_OK'), ('IN_LIM_DN', 'LIM_DN_OK'), ('IN_BEAM', 'BEAM_CLEAR'),
    ('IN_PRES', 'PRESENCE'), ('IN_ACOK', 'AC_OK'), ('IN_BATOK', 'BAT_OK')]
x0, y0 = 515, 245
for i, (tin, logic) in enumerate(inputs):
    x = x0 + (i % 3) * 75
    y = y0 + (i // 3) * 70
    n = 40 + i * 4
    R(f'R{n}', '4.7k 1206', (x, y), tin, f'OPTO{i}_A', fp='Resistor_SMD:R_1206_3216Metric')
    P('Isolator', 'PC817', f'U{11+i}', 'EL817S1(C) / PC817', (x + 25, y + 15), {'1': f'OPTO{i}_A', '2': 'GND', '3': logic, '4': '+3V3'},
      fp='Package_DIP:SMDIP-4_W9.53mm')
    P('Device', 'D', f'D{10+i}', '1N4148W (rev.)', (x, y + 30), {'K': f'OPTO{i}_A', 'A': 'GND'}, rot=90, fp='Diode_SMD:D_SOD-123')
    R(f'R{n+1}', '10k', (x + 50, y + 30), logic, 'GND')
    C(f'C{30+i}', '10nF', (x + 62, y + 30), logic, 'GND')

# ------------------------------------------------------------------ 8. E-stop loop + contactor coil
# +24V_FIELD -> J4.1 -> [E-stop NC, external] -> J4.2 = ESTOP_LOOP -> J4.3 -> K1 coil A1 ; K1 A2 -> J4.4 = K1_COIL_LO -> Q4 -> GND
P('Connector', 'Screw_Terminal_01x04', 'J4', 'E-STOP NC LOOP + K1 COIL', (30, 365),
  {'1': '+24V_FIELD', '2': 'ESTOP_LOOP', '3': 'ESTOP_LOOP', '4': 'K1_COIL_LO'},
  fp='TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-3-4-5.08_1x04_P5.08mm_Horizontal')
P('Device', 'D', 'D16', 'S1M (coil flyback)', (75, 375), {'K': 'ESTOP_LOOP', 'A': 'K1_COIL_LO'}, rot=90, fp='Diode_SMD:D_SMA')
P('Device', 'Q_NMOS_GSD', 'Q4', 'IRLML0060TRPBF (60V)', (110, 395), {'G': 'K1_G', 'S': 'GND', 'D': 'K1_COIL_LO'}, fp='Package_TO_SOT_SMD:SOT-23')
R('R80', '100R', (85, 410), 'K1_EN', 'K1_G', rot=90)
R('R81', '100k', (130, 415), 'K1_G', 'GND')
# E-stop healthy sense (fail-safe: loop broken -> ESTOP_OK low)
R('R82', '4.7k 1206', (150, 365), 'ESTOP_LOOP', 'OPTO6_A', fp='Resistor_SMD:R_1206_3216Metric')
P('Isolator', 'PC817', 'U17', 'EL817S1(C) / PC817', (180, 380), {'1': 'OPTO6_A', '2': 'GND', '3': 'ESTOP_OK', '4': '+3V3'}, fp='Package_DIP:SMDIP-4_W9.53mm')
R('R83', '10k', (215, 400), 'ESTOP_OK', 'GND')
C('C36', '10nF', (228, 400), 'ESTOP_OK', 'GND')
s.note('K1 = external DIN contactor Schneider LC1D09BD (24 VDC coil); its contacts switch the +24V line to the IBT-2 module B+ (off this PCB). E-stop (BOM: ProMax 22 mm 2-pole, contacts 1 A DC)\n'
       'NC contact in series with the coil supply: pressing it de-energises K1 and removes motor power regardless of firmware; ESTOP_OK also forces the IBT-2 R_EN/L_EN and RPWM low via U9/U19.\n'
       'The contactor coil current (about 0.2 A at 24 V, assumed, to be confirmed on the datasheet) is carried by J4.1 / the E-stop contact, which is rated 1 A DC.', (20, 430), 1.4)

# ------------------------------------------------------------------ 9. HUB12 + WS2812 + buzzer
P('74xx', '74LS245', 'U18', 'SN74HCT245PWR (5 V, TTL inputs)', (300, 390),
  {'A->B': '+5V', 'CE': 'GND', 'GND': 'GND', 'VCC': '+5V',
   'A0': 'HUB_A_3V3', 'A1': 'HUB_B_3V3', 'A2': 'HUB_CLK_3V3', 'A3': 'HUB_LAT_3V3', 'A4': 'HUB_OE_3V3', 'A5': 'HUB_R_3V3',
   'A6': 'WS2812_3V3', 'A7': 'U18_A7_TIE',
   'B0': 'HUB_A_5', 'B1': 'HUB_B_5', 'B2': 'HUB_CLK_5', 'B3': 'HUB_LAT_5', 'B4': 'HUB_OE_5', 'B5': 'HUB_R_5',
   'B6': 'WS2812_5', 'B7': 'NC'}, fp='Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm')
C('C20', '100nF', (275, 360), '+5V', 'GND')
R('R93', '10k (unused A7 tie)', (255, 395), 'U18_A7_TIE', 'GND')
R('R64', '10k (OE pull-up: sign off at reset)', (265, 425), 'HUB_OE_3V3', '+3V3')
hub = [('HUB_A_5', 'HUB_A'), ('HUB_B_5', 'HUB_B'), ('HUB_CLK_5', 'HUB_CLK'), ('HUB_LAT_5', 'HUB_LAT'), ('HUB_OE_5', 'HUB_OE'), ('HUB_R_5', 'HUB_R')]
for i, (a, b) in enumerate(hub):
    R(f'R{70+i}', '33R', (350, 365 + i * 10), a, b, rot=90)
P('Connector_Generic', 'Conn_02x08_Odd_Even', 'J9', 'HUB12 2x8 IDC (verify vs P10 silkscreen)', (400, 400),
  {'1': 'HUB_OE', '2': 'HUB_A', '3': 'GND', '4': 'HUB_B', '5': 'GND', '6': 'NC', '7': 'GND', '8': 'HUB_CLK',
   '9': 'GND', '10': 'HUB_LAT', '11': 'GND', '12': 'HUB_R', '13': 'GND', '14': 'NC', '15': 'GND', '16': 'NC'},
  fp='Connector_IDC:IDC-Header_2x08_P2.54mm_Vertical')
R('R76', '330R', (350, 440), 'WS2812_5', 'WS2812_DOUT', rot=90)
P('Connector_Generic', 'Conn_01x03', 'J10', 'WS2812 JST-XH 3P (B3B-XH-A)', (400, 455), {'1': '+5V', '2': 'WS2812_DOUT', '3': 'GND'},
  fp='Connector_JST:JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical')
C('C21', '470uF 10V (LED bulk)', (440, 455), '+5V', 'GND', fp='Capacitor_SMD:CP_Elec_8x10')
P('Connector', 'Screw_Terminal_01x02', 'J13', 'P10 SIGN POWER 5V/3A', (440, 490), {'1': '+5V', '2': 'GND'},
  fp='TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-3-2-5.08_1x02_P5.08mm_Horizontal')
# buzzer: 24 V piezo, low-side switch
P('Device', 'Q_NMOS_GSD', 'Q5', 'IRLML0060TRPBF', (300, 490), {'G': 'BUZ_G', 'S': 'GND', 'D': 'BUZ_LO'}, fp='Package_TO_SOT_SMD:SOT-23')
R('R77', '100R', (270, 505), 'BUZ_CTRL', 'BUZ_G', rot=90)
R('R78', '100k', (320, 515), 'BUZ_G', 'GND')
P('Device', 'D', 'D17', '1N4148W', (340, 480), {'K': '+24V_FIELD', 'A': 'BUZ_LO'}, rot=90, fp='Diode_SMD:D_SOD-123')
P('Connector', 'Screw_Terminal_01x02', 'J8', 'BUZZER 24V (+, -)', (380, 500), {'1': '+24V_FIELD', '2': 'BUZ_LO'},
  fp='TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-3-2-5.08_1x02_P5.08mm_Horizontal')

# ------------------------------------------------------------------ 10. field connectors
P('Connector', 'Screw_Terminal_01x08', 'J5', 'FIELD I/O 8P', (530, 450),
  {'1': '+24V_FIELD', '2': 'GND', '3': 'IN_LIM_UP', '4': 'IN_LIM_DN', '5': 'IN_BEAM', '6': 'IN_PRES', '7': '+24V_FIELD', '8': 'GND'},
  fp='TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-3-8-5.08_1x08_P5.08mm_Horizontal')
P('Connector', 'Screw_Terminal_01x03', 'J6', 'PSU/UPS STATUS (AC-OK, BAT-OK dry contacts to +24V)', (620, 450),
  {'1': 'IN_ACOK', '2': 'IN_BATOK', '3': '+24V_FIELD'}, fp='TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-3-3-5.08_1x03_P5.08mm_Horizontal')
s.note('J5: limit switches (BOM: ME-8108) wired on the NC contact between +24V_FIELD (J5.1) and IN_LIM_x (open = limit reached or wire break -> LOW -> safe); confirm the NC terminal on the real part.\n'
       'IN_BEAM: the BOM through-beam receiver (Delta PS-MT5 series, PNP) drives 24 V onto IN_BEAM when the beam is clear (light-ON) -> compatible with the active-high input; break / loss of supply = LOW = blocked (fail-safe). Confirm light-ON/NO output on the real part.\n'
       'J6: dry contacts closed to +24V_FIELD (J6.3) = OK; no AC-OK / BAT-OK source device is in the BOM (LRS-150/200-24 has no status output): link J6.1 to J6.3 to disable mains-loss sensing in the baseline.', (515, 480), 1.4)

open(os.path.join(OUT, 'sym-lib-table'), 'w').write(
    '(sym_lib_table\n  (lib (name "ParkFlow")(type "KiCad")(uri "${KIPRJMOD}/ParkFlow.kicad_sym")(options "")(descr "ParkFlow custom symbols"))\n)\n')
s.write(SCH, paper='A1', comments=('Lane Controller PCB 2-layer ~100x80 mm',
                                   'Generated by electronics/tools/gen_lane_controller_sch.py',
                                   'Design targets - to be bench-verified', ''))
print('wrote', SCH)

# ------------------------------------------------------------------ PINMAP.md (generated from `esp` above so it cannot drift)
def write_pinmap():
    import pinmap_data as pd
    _, pins = schlib._extract('RF_Module', 'ESP32-S3-WROOM-1')
    modpin = {p['name']: p['num'] for p in pins}
    comp = {r: v for r, v, *_ in s.comps}
    rows = []
    for pname, net in esp.items():
        if pname in ('3V3', 'GND'): continue
        g = pd.GPIO_ALIAS.get(pname)
        if g is None and pname.startswith('IO'): g = int(pname[2:])
        rows.append((9999 if g is None else g, pname, g, net))
    rows.sort()
    out = ['# ESP32-S3-WROOM-1-N16R8 pin map (Lane Controller PCB, Rev A)', '',
           'GENERATED by `electronics/tools/gen_lane_controller_sch.py` from the same `esp` dictionary that places the nets in `lane_controller.kicad_sch`; do not edit by hand.',
           'Strapping / reserved-pin facts: Espressif ESP32-S3-WROOM-1 datasheet, Table 4-1 and Table 3-1 note b, https://documentation.espressif.com/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf (opened for this document).',
           'All GPIO are 3.3 V logic. Every figure for timing/current is a design target, to be bench-verified.', '',
           '| GPIO | Module pin | Net | Function | Direction (MCU) | Level | Protection / state at reset | Other parts on net (auto from netlist) | Strapping-pin check |',
           '|---|---|---|---|---|---|---|---|---|']
    used = set()
    for _, pname, g, net in rows:
        ref_pins = sorted(x for x in intended.get(net, ()) if x[0] != 'U4' and not x[0].startswith('#'))
        auto = ', '.join(f'{r}.{p}({comp[r].split(" (")[0].split(" ")[0]})' for r, p in ref_pins) or '-'
        if net == 'NC':
            gnum = f'GPIO{g}' if g is not None else pname
            chk = pd.STRAP.get(g) or pd.RESERVED.get(g) and 'NOT USED: ' + pd.RESERVED[g] or 'not used'
            out.append(f'| {gnum} | {modpin.get(pname, "")} | NC | unused (no-connect flag) | - | - | left floating | - | {chk} |')
            continue
        info = pd.INFO[net]
        used.add(net)
        on_net = {r for r, _ in ref_pins}
        for ref in info[4]:
            assert ref in comp, f'{net}: cited ref {ref} not in schematic'
        gnum = f'GPIO{g}' if g is not None else pname
        chk = pd.STRAP.get(g, 'not a strapping pin') if g is not None else 'dedicated EN pin'
        out.append(f'| {gnum} | {modpin.get(pname, "")} | {net} | {info[0]} | {info[1]} | {info[2]} | {info[3]} | {auto} | {chk} |')
    missing = {n for n in esp.values() if n != 'NC'} - used - {'+3V3', 'GND'}
    assert not missing, f'nets without pinmap info: {missing}'
    out += ['', '## Strapping summary', '',
            '| Pin | Level seen by the chip at reset | Result |', '|---|---|---|',
            '| GPIO0 | 10 k pull-up (R16), SW1/Q3 open | HIGH: normal SPI boot; holding BOOT or Pi Q3 gives download mode |',
            '| GPIO3 | floating (NC) | datasheet: floating default, no internal pull; unused, no action |',
            '| GPIO45 | NC (weak pull-down) | datasheet default 0; unconnected so the module keeps its factory VDD_SPI setting |',
            '| GPIO46 | NC (weak pull-down) | default |', '',
            '## Not available / not used', '',
            '- GPIO35, GPIO36, GPIO37: connected to the octal PSRAM on the BOM module N16R8 (datasheet Table 3-1 note b); left as no-connect.',
            '- GPIO19/20 carry native USB (J12); GPIO43/44 are UART0 to the Edge Node, so the ROM boot log also appears on that link at reset.', '']
    path = os.path.join(os.path.dirname(__file__), '..', 'PINMAP.md')
    open(path, 'w').write('\n'.join(out))
    print('wrote', path, f'({len(rows)} module signal rows)')

write_pinmap()

# ------------------------------------------------------------------ verify
def verify():
    net = os.path.join(OUT, 'lane_controller.net')
    subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '-o', net, SCH], check=True, capture_output=True)
    txt = open(net).read()
    got = collections.defaultdict(set)
    blocks = re.split(r'\(net \(code "\d+"\) \(name "', txt.split('(nets', 1)[1])[1:]
    for b in blocks:
        name = b.split('"', 1)[0].lstrip('/')
        for r, p in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', b):
            if not r.startswith('#'):
                got[name].add((r, p))
    intended_f = {k: {x for x in v if not x[0].startswith('#')} for k, v in intended.items()}
    bad = 0
    # every intended net must appear exactly as a KiCad net
    by_members = {frozenset(v): k for k, v in got.items()}
    for k, v in intended_f.items():
        if not v: continue
        if frozenset(v) not in by_members:
            bad += 1
            cand = [g for g, gv in got.items() if gv & v]
            print('MISMATCH', k, sorted(v)[:6], '-> kicad nets', cand[:4])
    single = [k for k, v in intended_f.items() if len(v) == 1]
    print(f'nets intended={len(intended_f)} kicad={len(got)} mismatches={bad}')
    print('single-pin nets (check intentional):', single)
    refs=re.findall(r'\(comp \(ref "([^"]+)"', txt)
    dup=[r for r,c in collections.Counter(refs).items() if c>1]
    print('components', len(refs), 'duplicate refs', dup)
    bad += len(dup)
    bad += check_footprints()
    return bad

FPDIR = '/usr/share/kicad/footprints'
def check_footprints():
    """Every symbol pin number must exist as a pad in the assigned footprint (ERC does not check this)."""
    bad = 0
    for ref, value, lib, name, fp in s.comps:
        if ref.startswith('#'): continue
        if not fp:
            print('NO FOOTPRINT', ref); bad += 1; continue
        flib, fname = fp.split(':')
        path = os.path.join(FPDIR, flib + '.pretty', fname + '.kicad_mod')
        if not os.path.exists(path):
            print('FOOTPRINT FILE MISSING', ref, fp); bad += 1; continue
        pads = set(re.findall(r'\(pad "?([^"\s)]+)"?\s', open(path).read()))
        _, pins = schlib._extract(lib, name)
        miss = sorted({p['num'] for p in pins} - pads)
        if miss:
            print('PIN/PAD MISMATCH', ref, fp, 'pins without pad:', miss); bad += 1
    print('footprint check done, problems =', bad)
    return bad
if __name__ == '__main__':
    sys.exit(1 if verify() else 0)
