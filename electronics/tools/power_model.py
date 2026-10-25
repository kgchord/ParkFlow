"""Single source of the power-budget numbers used by gen_power_tree.py and quoted in ESDS.md.
Every load figure is a design TARGET / assumption (to be bench-verified) unless the comment says 'datasheet'."""
EFF_BUCK5 = 0.90      # TPS54560 24->5 V, target
EFF_XL = 0.85         # XL4015 24->5.1 V, target
EFF_3V3 = 0.90        # TLV62569 5->3.3 V, target
# ---- 5 V rail on the Lane Controller (TPS54560BDDA, 5 A rated)
v5 = [  # name, typ A, peak A
    ('3V3 buck input (ESP32-S3 0.5 A peak @3.3 V, optos, THVD1450, logic)', 0.15 * 3.3 / EFF_3V3 / 5, 0.55 * 3.3 / EFF_3V3 / 5),
    ('WS2812 12-LED ring (J10), firmware-capped to 25 % brightness', 0.15, 0.18),
    ('P10 sign module (J13, labelled 5 V / 3 A)', 1.0, 3.0),
    ('74HCT245 + misc', 0.01, 0.02),
]
v5_typ = sum(x[1] for x in v5); v5_pk = sum(x[2] for x in v5)
lc24_typ = v5_typ * 5 / EFF_BUCK5 / 24; lc24_pk = v5_pk * 5 / EFF_BUCK5 / 24
# ---- Edge chain
pi_typ_w, pi_pk_w, ups_chg_w = 8.0, 20.0, 5.0
edge24_typ = pi_typ_w / EFF_XL / 24 + 0.02
edge24_pk = (pi_pk_w + ups_chg_w) / EFF_XL / 24
# ---- 24 V bus (LRS-200-24, 8.8 A, replaces the LRS-150-24 6.5 A after the 25 Oct design update)
b24 = [  # name, typ A, peak A, note
    ('Barrier motor, Lucas TVS 24 V 18 N.m (via K1 + IBT-2 BTS7960 module)', 2.0, 5.0, 'ASSUMPTION: vendor gives no current; 5 A = firmware current limit on the IS sense, to be bench-verified (was 6 A with the 6.5 A supply)'),
    ('Lane Controller 24 V logic input (F1 -> TPS54560 5 V rail incl. P10 + ring)', lc24_typ, lc24_pk, 'from 5 V table'),
    ('24 V field: 6 opto inputs, sensors, buzzer (F2)', 0.10, 0.30, 'target'),
    ('K1 coil (LC1D09BD 24 VDC) + E-stop loop', 0.20, 0.30, 'ASSUMPTION: contactor coil power not on the vendor page; 0.2 A hold / 0.3 A pull-in is a placeholder to be confirmed on the Schneider datasheet'),
    ('Edge chain: XL4015 -> X1202 UPS -> Pi 5 + AI HAT+ (peak = 20 W + 5 W UPS charge)', edge24_typ, edge24_pk, 'target'),
]
b24_typ = sum(x[1] for x in b24); b24_pk = sum(x[2] for x in b24)
LRS150_A = 6.5      # datasheet (Mean Well LRS-150 sheet): the ORIGINAL BOM supply, kept for the before/after comparison
LRS200_A = 8.8      # Mean Well LRS-200-24 rated current (Probots product page 25 Oct: 24 V 8.8 A 211.2 W, overload 110-140 %, convection cooled)
PSU_A = LRS200_A
HICCUP = 1.10 * PSU_A   # overload protection starts at 110 % of rated current (vendor page; Mean Well sheet not opened for the -200)
DRS240_A = 10.0     # design intent figure from block diagram; datasheet NOT opened
others_pk = b24_pk - b24[0][2]
motor_max_rated = PSU_A - others_pk
motor_max_derated = 0.8 * PSU_A - others_pk
old_peak = others_pk + 6.0      # peak with the old 6 A motor limit
old_margin = LRS150_A - old_peak
# ---- 12 V bus (LRS-100-12, 8.5 A)
b12 = [('ID Tech IDT 85 UHF reader (9-12 VDC; current NOT stated by vendor)', 0.6, 1.5, 'target'),
       ('12 V mini DC UPS charging (Enerva 27.5 Wh)', 0.3, 1.0, 'target')]
b12_typ = sum(x[1] for x in b12); b12_pk = sum(x[2] for x in b12); LRS100_A = 8.5
# ---- UPS arithmetic
cell_ah, cell_v, ncell = 2.5, 3.6, 2
ups_nom = cell_ah * cell_v * ncell
ups_use = ups_nom * 0.8 * 0.85 * 0.8      # 80 % depth of discharge, 85 % boost eff, 80 % end-of-life capacity
ups_need = pi_pk_w * 10 / 60
ups_margin = ups_use / ups_need
mini_use = 27.5 * 0.7; mini_need = 1.5 * 12 * 10 / 60; mini_margin = mini_use / mini_need
# ---- mains
PF = 0.6
m1 = 211.2 / 0.89; m2 = 102 / 0.85 + 66.78
mcb1 = m1 / (230 * PF); mcb2 = m2 / (230 * PF)
def ipc(i, dT=20, oz=1.0):
    return ((i / (0.048 * dT ** 0.44)) ** (1 / 0.725)) / (1.378 * oz) * 0.0254
if __name__ == '__main__':
    print('5V typ %.2f pk %.2f A (%.0f%% of 5 A); LC 24V typ %.3f pk %.3f' % (v5_typ, v5_pk, 100 * v5_pk / 5, lc24_typ, lc24_pk))
    print('edge24 typ %.3f pk %.3f' % (edge24_typ, edge24_pk))
    print('24V bus typ %.2f A (%.0f W, %.0f%%) pk %.2f A (%.0f W, %.0f%%) others_pk %.2f motor_max rated %.2f derated %.2f hiccup %.2f' % (b24_typ, b24_typ * 24, 100 * b24_typ / PSU_A, b24_pk, b24_pk * 24, 100 * b24_pk / PSU_A, others_pk, motor_max_rated, motor_max_derated, HICCUP))
    print('12V typ %.2f pk %.2f (%.0f%%)' % (b12_typ, b12_pk, 100 * b12_pk / 8.5))
    print('UPS nom %.1f use %.2f need %.2f margin %.2f ; mini use %.2f need %.2f margin %.2f' % (ups_nom, ups_use, ups_need, ups_margin, mini_use, mini_need, mini_margin))
    print('old: peak with 6 A motor %.2f A vs LRS-150 6.5 A -> %+.2f A' % (old_peak, old_margin))
    print('mains W %.0f %.0f ; MCB A %.2f %.2f' % (m1, m2, mcb1, mcb2))
    for i in (0.82, 3.6, 0.55, 6, 10): print('IPC', i, round(ipc(i), 2))
