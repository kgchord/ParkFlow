#!/usr/bin/env python3
"""
ParkFlow Demo Lane - mechanical & thermal hand calculations.
All results are ANALYTICAL PREDICTIONS (targets, to be bench-verified / FEA-checked).
Units: SI unless suffixed (mm, kg, N, Nm, MPa, W, degC).

Run:  python3 calcs.py            (prints all sections)
      python3 calcs.py --md       (also writes calcs_results.txt next to this file)

Sources / assumptions (also listed in CALCS.md):
  * IS 875 (Part 3):2015 - Vz = Vb k1 k2 k3 k4 ; pz = 0.6 Vz^2 ; pd = Kd Ka Kc pz (we take Kd=Ka=Kc=1.0,
    conservative; code floor pd >= 0.7 pz). k2 Table 2 values for z <= 10 m:
    TC1 1.05, TC2 1.00, TC3 0.91, TC4 0.80 (k2 is not reduced below 10 m).
  * T-slot section properties: Wolweiss profiles via reiman.pt product pages
    40x40 4-slot: Ix=Iy=9.1 cm4, Wx=Wy=4.6 cm3
    40x80 6-slot: Ix=16.6 / Iy=63.2 cm4, Wx=8.3 / Wy=15.8 cm3
    80x80 8-slot: Ix=Iy=109.9 cm4, Wx=Wy=27.5 cm3
  * Material minima (EN 755-2 for 6063 extrusions, EN 485-2 for 5052 sheet, IS 2062 for MS, ISO 898-1 bolts).
"""
import math, sys

G = 9.81

# ----------------------------------------------------------------------------- materials
MAT = {
    # name: (E [MPa], yield Rp0.2 [MPa], ultimate Rm [MPa], density [kg/m3])
    "6063-T5":   (69500, 110, 160, 2700),   # EN 755-2 min, 3 < e <= 25 mm (conservative for T-slot)
    "6063-T6":   (69500, 170, 215, 2700),   # EN 755-2 min, e <= 10 mm
    "5052-H32":  (70300, 130, 210, 2680),   # EN 485-2 min (sheet 0.5-40 mm)
    "IS2062-E250": (200000, 250, 410, 7850),# mild steel plate (S275 equivalent check also given)
    "S275":      (200000, 275, 410, 7850),
    "6061-T6":   (68900, 240, 290, 2700),
    "ASA-FDM":   (2000, 25, 30, 1070),      # design value for FDM layered part (bulk ~40 MPa)
}
BOLT_88 = dict(fyb=640, fub=800)             # ISO 898-1 class 8.8
AS = {"M5": 14.2, "M6": 20.1, "M8": 36.6, "M10": 58.0, "M12": 84.3}   # tensile stress area mm2

# T-slot profiles (W = section modulus cm3, I = second moment cm4, A = area cm2 approx, kg/m approx)
PROFILES = {
    "40x40":  dict(I=9.1,  W=4.6,  Iweak=9.1,  Wweak=4.6,  kgpm=1.50),
    "40x80":  dict(I=63.2, W=15.8, Iweak=16.6, Wweak=8.3,  kgpm=2.80),
    "80x80":  dict(I=109.9, W=27.5, Iweak=109.9, Wweak=27.5, kgpm=5.40),
}

out_lines = []
def p(s=""):
    print(s); out_lines.append(s)

def hdr(s):
    p(); p("=" * 78); p(s); p("=" * 78)

# ============================================================================== 1. WIND
hdr("1. WIND LOAD ON LANE GANTRY POLE  (IS 875 Part 3 : 2015)")
k1 = 1.00   # Table 1: general structures, 50-yr mean probable design life
k2 = 1.00   # Table 2: Terrain Category 2 (open parking lot / campus, scattered obstructions <10 m), z <= 10 m
k3 = 1.00   # cl 6.3.3: flat site, upwind slope < 3 deg
k4 = 1.00   # cl 6.3.4: non-cyclonic importance (1.15 only for post-cyclone-importance structures on coast)
Kd = Ka = Kc = 1.0   # cl 7.2: conservative (code permits Kd=0.9, Kc=0.9 etc.); pd >= 0.7 pz floor
cities = {"Delhi (pilot)": 47, "Mumbai": 44, "Chennai": 50, "Bengaluru": 33}

# Exposed items on the pole: name, (width m, height m), Cf, centroid height z (m), lever arm for eccentric weight (m), mass (kg)
# Heights measured from top of base plate (pole foot). Worst case = every item loaded normal to its largest face simultaneously.
ITEMS = [
    # name                     area m2               Cf    z_c   mass  ecc_arm
    ("RFID reader 260x260",    0.260 * 0.260,        1.3,  1.45, 3.0,  0.30),
    ("Antenna arm 40x40x350",  0.040 * 0.350,        2.0,  1.60, 0.6,  0.17),
    ("ANPR camera 220x80",     0.220 * 0.080,        1.2,  1.20, 1.2,  0.30),
    ("Camera arm 40x40x300",   0.040 * 0.300,        2.0,  1.20, 0.5,  0.15),
    ("P10 sign cabinet 360x200", 0.360 * 0.200,      1.3,  2.25, 2.5,  0.10),
    ("Edge Node IP65 300x400", 0.300 * 0.400,        1.3,  0.90, 9.0,  0.13),
]
POLE_H = 2.40   # m, pole length above base plate

def pole_case(Vb, prof, verbose=True, plate_t=12.0):
    Vz = Vb * k1 * k2 * k3 * k4
    pz = 0.6 * Vz ** 2
    pd = max(Kd * Ka * Kc * pz, 0.7 * pz)
    w_pole = 0.080 if prof == "80x80" else 0.040
    Cf_pole = 2.0                           # square section, wind normal to face (IS 875-3 force coeff. ~2.0)
    rows = []
    M = 0.0; Fsum = 0.0
    for name, A, Cf, z, m, e in ITEMS:
        F = pd * Cf * A
        rows.append((name, A, Cf, F, z, F * z))
        M += F * z; Fsum += F
    Fp = pd * Cf_pole * w_pole * POLE_H
    rows.append((f"Pole {prof} x {POLE_H} m", w_pole * POLE_H, Cf_pole, Fp, POLE_H / 2, Fp * POLE_H / 2))
    M += Fp * POLE_H / 2; Fsum += Fp
    # gravity eccentricity (worst: all eccentric masses on one side)
    Mg = sum(m * G * e for (_, _, _, _, m, e) in ITEMS)
    Mtot = M + Mg
    pr = PROFILES[prof]
    sigma = Mtot / (pr["Wweak"] * 1e-6) / 1e6    # MPa (weak axis governs; any wind direction)
    res = dict(Vz=Vz, pz=pz, pd=pd, rows=rows, Mw=M, Mg=Mg, M=Mtot, F=Fsum, sigma=sigma)
    for mat in ("6063-T5", "6063-T6"):
        res["FoS_" + mat] = MAT[mat][1] / sigma
    # tip deflection (cantilever, point loads + UDL) at pole top, weak axis
    E = MAT["6063-T5"][0] * 1e6; I = pr["Iweak"] * 1e-8; L = POLE_H
    d = 0.0
    for name, A, Cf, F, z, Mi in rows[:-1]:
        a = min(z, L)
        d += F * a ** 2 * (3 * L - a) / (6 * E * I)
    wudl = Fp / L
    d += wudl * L ** 4 / (8 * E * I)
    res["defl_top_mm"] = d * 1000
    # deflection at camera height (1.2 m) - for ANPR image stability
    res["F_pole"] = Fp
    return res

hdr_line = f"{'Item':28s} {'A m2':>7s} {'Cf':>4s} {'F N':>7s} {'z m':>5s} {'M Nm':>7s}"
r = pole_case(47, "80x80")
p(f"Assumptions: k1={k1} k2={k2} (TC2, z<=10 m) k3={k3} k4={k4}; Kd=Ka=Kc=1.0 (conservative)")
p(f"Delhi Vb = 47 m/s -> Vz = {r['Vz']:.1f} m/s, pz = 0.6 Vz^2 = {r['pz']:.0f} Pa, pd = {r['pd']:.0f} Pa")
p()
p(hdr_line)
for name, A, Cf, F, z, Mi in r["rows"]:
    p(f"{name:28s} {A:7.4f} {Cf:4.1f} {F:7.1f} {z:5.2f} {Mi:7.1f}")
p(f"{'Total wind':28s} {'':7s} {'':4s} {r['F']:7.1f} {'':5s} {r['Mw']:7.1f}")
p(f"Gravity eccentricity moment (all brackets one side): {r['Mg']:.1f} Nm")
p(f"DESIGN BASE MOMENT  M = {r['M']:.0f} Nm   (base shear V = {r['F']:.0f} N)")

p()
p("Pole section check (weak axis, any wind direction):")
p(f"{'City':16s} {'Vb':>4s} {'pd Pa':>6s} {'Profile':>7s} {'M Nm':>6s} {'sig MPa':>8s} {'FoS T5':>7s} {'FoS T6':>7s} {'top defl mm':>11s}")
pole_table = {}
for city, Vb in cities.items():
    for prof in ("40x40", "40x80", "80x80"):
        rr = pole_case(Vb, prof)
        pole_table[(city, prof)] = rr
        p(f"{city:16s} {Vb:4d} {rr['pd']:6.0f} {prof:>7s} {rr['M']:6.0f} {rr['sigma']:8.1f} "
          f"{rr['FoS_6063-T5']:7.2f} {rr['FoS_6063-T6']:7.2f} {rr['defl_top_mm']:11.1f}")
p("=> 40x40 single profile FAILS at Delhi design wind (FoS < 1). 80x80 8-slot profile selected for the pole;")
p("   40x40 retained for arms, 20x20 for sign/photo-beam posts.")

# --------------------------------------------------------------- base plate & anchors
hdr("2. BASE PLATE (250x250, MS IS 2062 E250) AND 4x M12 ANCHORS ON 190 mm PCD")
rD = pole_table[("Delhi (pilot)", "80x80")]
M = rD["M"]; V = rD["F"]
PCD = 0.190
s = PCD / math.sqrt(2)            # bolt square side = 134.4 mm
# Case A: wind normal to a side -> 2 bolts in tension, lever = bolt row spacing (rotation about far bolt row; conservative)
T_side = M / (2 * s)
# Case B: wind on diagonal -> 1 bolt in tension, lever = PCD (rotation about opposite bolt)
T_diag = M / PCD
# self weight relieves tension - ignored (conservative)
T = max(T_side, T_diag)
sig_b = T / AS["M12"]
p(f"Bolt square side s = PCD/sqrt2 = {s*1000:.1f} mm")
p(f"Case A (side wind):     T = M/(2 s)  = {T_side/1000:.2f} kN per bolt")
p(f"Case B (diagonal wind): T = M/PCD    = {T_diag/1000:.2f} kN (single bolt)  <- governs")
p(f"M12 8.8 tensile stress = T/As = {T:.0f}/{AS['M12']} = {sig_b:.1f} MPa ; FoS vs proof(640) = {BOLT_88['fyb']/sig_b:.1f}")
p(f"Shear per bolt = V/4 = {V/4:.0f} N  (negligible; tau = {V/4/AS['M12']:.1f} MPa)")
p("Anchor: M12 chemical anchor, hef >= 110 mm in M20 concrete - vendor tension resistance typically >> 10 kN;")
p(f"  required design tension {T/1000:.1f} kN x 2.0 = {2*T/1000:.1f} kN -> confirm from anchor ETA/datasheet.")
# plate bending: cantilever from stiffener line with 45-deg dispersion b_eff = 2e -> sigma = 6 T e / (2e t^2) = 3T/t^2
for t in (10.0, 12.0, 16.0):
    sig_p = 3 * T / t ** 2
    p(f"Plate t={t:.0f} mm: yield-line cantilever sigma = 3T/t^2 = {sig_p:.0f} MPa ; FoS(E250) = {250/sig_p:.2f}")
p("=> 16 mm plate selected: FoS >= 2 with NO credit for gusset edge support (10/12 mm fail the FoS 2.0 target")
p("   on this conservative model; FEA with gussets may justify 12 mm - see FEM recipe).")
PLATE_T = 16.0
# Socket bearing couple: extrusion moment transferred into 150 mm tall MS socket
hs = 0.150
Fc = M / (2 / 3 * hs)
p(f"Socket (4x 6 mm MS cheeks, h=150 mm): bearing couple F = M/(2/3 h) = {Fc/1000:.1f} kN; "
  f"bearing on 80 mm x 20 mm contact = {Fc/(80*20):.1f} MPa (OK)")
# Gusset (4x, 6 mm, 100 x 120): tension flange force ~ M / lever (socket half width + gusset centroid)
lev = 0.040 + 0.6 * 0.100
Fg = M / (2 * lev)   # two gussets share on tension side for side wind
tg = 6.0; hg_eff = 60.0
p(f"Gusset 6 mm: axial F ~ M/(2*{lev:.2f} m) = {Fg/1000:.2f} kN; stress on 60 mm effective section = "
  f"{Fg/(tg*hg_eff):.1f} MPa; FoS(E250) = {250/(Fg/(tg*hg_eff)):.1f}")
weld_a = 4.0  # mm throat 6mm leg fillet ~4.2
Lw = 2 * 120 + 2 * 100
p(f"Gusset fillet welds 6 mm leg (a=4.2 mm), L={Lw} mm: tau = {Fg/(4.2*Lw):.1f} MPa (E250 weld fvw ~ 189 MPa)")

# --------------------------------------------------------------- antenna bracket
hdr("3. RFID ANTENNA TILT BRACKET (5 mm 5052-H32 bent yoke + tilt plate, M8 pivot, M6 lock)")
pd = rD["pd"]
F_ant = pd * 1.3 * 0.26 * 0.26
W_ant = 3.0 * G
p(f"Wind on reader: F = pd*Cf*A = {pd:.0f}*1.3*0.0676 = {F_ant:.0f} N ; weight = {W_ant:.0f} N")
# Yoke cheek: 2 cheeks share; cheek is a 5 mm plate loaded in-plane: cantilever length from bend to pivot 70 mm, width 80 mm
Lc = 0.070; bc = 0.080; tc = 0.005
Fch = math.hypot(F_ant, W_ant) / 2
Mc = Fch * Lc
sig_c_inplane = 6 * Mc / (tc * bc ** 2) / 1e6
p(f"Cheek in-plane bending: M = {Fch:.0f} N x 70 mm = {Mc:.2f} Nm -> sigma = 6M/(t b^2) = {sig_c_inplane:.1f} MPa")
# eccentric moment: reader CG 60 mm in front of pivot plane -> moment about pivot handled by M6 lock bolt in arc slot (r=50mm)
e_cg = 0.060
Mpiv = W_ant * e_cg + F_ant * 0.030
F_lock = Mpiv / 0.050 / 2
p(f"Tilt moment about pivot = W*60mm + F*30mm = {Mpiv:.2f} Nm -> lock-bolt force per side = {F_lock:.0f} N")
p(f"  M6 8.8 friction clamp (preload ~ 8 kN, mu 0.2) = 1600 N/side -> FoS {1600/F_lock:.1f} vs slip")
# Bend root out-of-plane: worst = wind with unequal sharing (assume 100% on one cheek, 30 mm offset from bend)
Mroot = F_ant * 0.030
sig_root = 6 * Mroot / (bc * tc ** 2) / 1e6
p(f"Bend-root out-of-plane (all wind to one cheek, 30 mm offset): sigma = {sig_root:.1f} MPa")
# Pivot pin bearing (M8 in 5 mm plate)
brg = Fch / (8 * 5)
p(f"M8 pivot bearing in 5 mm plate: {brg:.1f} MPa ; M8 shear (single) = {Fch/AS['M8']:.1f} MPa")
sig_max_br = max(sig_c_inplane, sig_root)
p(f"Governing bracket stress = {sig_max_br:.1f} MPa ; FoS (5052-H32, Rp0.2 130) = {130/sig_max_br:.1f}")
p(f"If MS 5 mm used: FoS (E250) = {250/sig_max_br:.1f}")
# Arm 40x40 x 350
La = 0.35
Ma = math.hypot((F_ant + pd * 2.0 * 0.04 * La / 2) * La, (W_ant + 0.6 * G) * La)
p(f"Antenna arm 40x40 (L=350 mm) root moment = {Ma:.0f} Nm -> sigma = {Ma/4.6e-6/1e6:.1f} MPa ; "
  f"FoS(6063-T5) = {110/(Ma/4.6e-6/1e6):.1f}")
Tq = F_ant * 0.18
p(f"Arm torsion (reader centre 180 mm below arm axis): T = {Tq:.0f} Nm -> resisted by 2x M8 corner brackets + "
  f"M6 T-nuts on yoke (couple over 200 mm = {Tq/0.2:.0f} N)")
ant_br = dict(F_ant=F_ant, sig=sig_max_br, FoS=130 / sig_max_br, arm_sig=Ma / 4.6e-6 / 1e6)

# --------------------------------------------------------------- boom barrier
hdr("4. DEMO BOOM BARRIER (1.2 m boom, Al 6063-T5 rect tube 60x30x1.5)")
bH, bB, bt = 60.0, 30.0, 1.5
Lb = 1.200                     # boom length from hub axis to tip (m)
A_b = bH * bB - (bH - 2 * bt) * (bB - 2 * bt)                    # mm2
I_b = (bB * bH ** 3 - (bB - 2 * bt) * (bH - 2 * bt) ** 3) / 12   # mm4 (vertical bending)
I_bh = (bH * bB ** 3 - (bH - 2 * bt) * (bB - 2 * bt) ** 3) / 12  # mm4 (horizontal bending)
W_b = I_b / (bH / 2); W_bh = I_bh / (bB / 2)
m_tube = A_b * 1e-6 * 2700 * Lb
m_extras = 0.15                 # printed end cap + reflective tape + 2 rivnuts
m_boom = m_tube + m_extras
p(f"Section A = {A_b:.0f} mm2, Iv = {I_b:.0f} mm4, Wv = {W_b:.0f} mm3, Ih = {I_bh:.0f} mm4, Wh = {W_bh:.0f} mm3")
p(f"Boom mass = {m_tube:.3f} kg tube + {m_extras} kg fittings = {m_boom:.3f} kg  ({m_tube/Lb:.3f} kg/m)")
Ftip = 50.0
w = m_tube * G / Lb             # N/m
Mhub = Ftip * Lb + w * Lb ** 2 / 2 + m_extras * G * Lb
sig_hub = Mhub * 1e3 / W_b
E = 69500.0
d_tip = Ftip * (Lb * 1e3) ** 3 / (3 * E * I_b) + (w / 1e3) * (Lb * 1e3) ** 4 / (8 * E * I_b) \
        + m_extras * G * (Lb * 1e3) ** 3 / (3 * E * I_b)
p(f"Load case: self weight + {Ftip:.0f} N vertical tip load (boom horizontal)")
p(f"  M_hub = {Mhub:.1f} Nm ; sigma = {sig_hub:.1f} MPa ; FoS(6063-T5) = {110/sig_hub:.1f}")
p(f"  Tip deflection = {d_tip:.1f} mm  (L/{Lb*1e3/d_tip:.0f})")
Mh = Ftip * Lb
p(f"  50 N horizontal tip push (vehicle nudge): M = {Mh:.0f} Nm, sigma_h = {Mh*1e3/W_bh:.1f} MPa, FoS = {110/(Mh*1e3/W_bh):.1f}")
# Rivet/bolt clamp at hub: boom clamped in carrier by 2x M6 through-bolts 60 mm apart
Fbolt = Mhub / 0.060
p(f"  Carrier clamp: 2x M6 through-bolts @60 mm -> couple force {Fbolt:.0f} N; bearing on 2x1.5 mm walls "
  f"= {Fbolt/(6*3):.0f} MPa vs 6063-T5 bearing ~1.5*Rm=240 -> FoS {240/(Fbolt/(6*3)):.1f} (use crush tube / sleeve)")

# Shear pin (breakaway): hinge axis vertical (closed pose), shear pin offset e from hinge
e_sp = 0.035; L_hinge = Lb - 0.045
F_break_tip = 2.0 * Ftip                          # break at 2x design horizontal tip load
F_pin = F_break_tip * L_hinge / e_sp
tau_u_pin = 0.6 * MAT["6061-T6"][2]               # MPa
d_pin = math.sqrt(4 * F_pin / (math.pi * tau_u_pin))
p(f"Breakaway shear pin (single shear, e = {e_sp*1e3:.0f} mm from hinge): break at {F_break_tip:.0f} N tip -> "
  f"F_pin = {F_pin:.0f} N")
p(f"  6061-T6 pin tau_u ~ 0.6 Rm = {tau_u_pin:.0f} MPa -> d = {d_pin:.2f} mm -> use d = 5.0 mm "
  f"(breaks at {math.pi*25/4*tau_u_pin*e_sp/L_hinge:.0f} N tip; 50 N service = "
  f"{Ftip*L_hinge/e_sp/(math.pi*25/4*tau_u_pin)*100:.0f}% of break)")

# Motor torque
m_carrier = 0.45                                   # kg, 2x 5 mm Al carrier plates + hinge pin + bolts
r_carrier = 0.03
m_cw_arm = 0.20                                    # m, counterweight lever arm (tail)
T_boom = m_tube * G * (Lb / 2) + m_extras * G * Lb + m_carrier * G * r_carrier
balance_target = 0.85                              # design target: counterweight balances 85% of boom moment
plate_m = 0.1 * 0.06 * 0.01 * 7850                 # kg, one MS plate 100x60x10
n_plates = 7                                       # as modelled in CAD (cw_n=7) and bought in the BOM
m_cw_req = balance_target * T_boom / (G * m_cw_arm)
m_cw = n_plates * plate_m                          # installed counterweight (7 plates)
balance = m_cw * G * m_cw_arm / T_boom             # installed balance, MUST stay < 1.0 (boom-heavy: gravity closes it, never opens it)
assert balance < 1.0
I_boom = m_tube * Lb ** 2 / 3 + m_extras * Lb ** 2
I_cw = m_cw * m_cw_arm ** 2
t_open = 2.5; t_acc = 0.4                          # s, 90 deg trapezoidal profile
theta = math.pi / 2
omega = theta / (t_open - t_acc)
alpha = omega / t_acc
T_fric = 0.3                                       # Nm bearing/seal friction at output

# --- wind on the RAISED boom. Boom 60 (in the rotation plane) x 30 (across it), long axis vertical when raised.
# Wind along the lane, in the rotation plane, sees the 30 mm face. Oblique wind (angle th from the lane axis) gives an
# in-plane force component 30 cos^2(th) + 60 sin(th) cos(th) (mm of equivalent face, Cf kept at 2.0): worst case below.
def f_obl(th): return 30 * math.cos(th) ** 2 + 60 * math.sin(th) * math.cos(th)
w_obl = max(f_obl(math.radians(d)) for d in range(0, 90)); th_obl = max(range(0, 90), key=lambda d: f_obl(math.radians(d)))
def M_raised(V, w_mm):                              # hub moment from wind on the raised boom (arm Lb/2), Cf 2.0
    return 0.6 * V ** 2 * 2.0 * (w_mm / 1e3) * Lb * (Lb / 2)
def T_req(V, w_mm, with_cw=True):
    Mw = M_raised(V, w_mm)
    if with_cw:
        return (1 - balance) * T_boom + (I_boom + I_cw) * alpha + Mw + T_fric
    return T_boom + I_boom * alpha + Mw + T_fric
V_op = 15.0                                        # m/s, production operating-wind requirement
p_op = 0.6 * V_op ** 2
Mw_op = M_raised(V_op, w_obl)                      # 48.5 mm worst-oblique face (was: 60 mm, over-conservative for the rotation plane)
Mw_60 = M_raised(V_op, 60.0)
Mw_30 = M_raised(V_op, 30.0)
T_noCW = T_req(V_op, w_obl, False)
T_CW = T_req(V_op, w_obl, True)
T_CW_60 = T_req(V_op, 60.0, True); T_noCW_60 = T_req(V_op, 60.0, False)
rpm = omega / (2 * math.pi) * 60
p(f"Static gravity torque of boom about shaft = {T_boom:.2f} Nm")
p(f"Counterweight: target {balance_target*100:.0f}% balance at {m_cw_arm*1e3:.0f} mm tail -> {m_cw_req:.2f} kg required; "
  f"MS plate 100x60x10 = {plate_m:.3f} kg -> {n_plates} plates = {m_cw:.2f} kg INSTALLED (balance {balance*100:.0f}%, still boom-heavy)")
p(f"  Residual gravity closing torque with the motor unpowered = {(1-balance)*T_boom:.2f} Nm = {(1-balance)*T_boom/Lb:.2f} N at the boom tip (cannot crush; breakaway pin covers lateral hits)")
p(f"Motion 0->90 deg in {t_open} s, accel {t_acc} s: omega = {omega:.2f} rad/s ({rpm:.1f} rpm), alpha = {alpha:.2f} rad/s2")
p(f"Inertia: boom {I_boom:.3f} kg m2, counterweight {I_cw:.3f} kg m2")
p(f"Operating wind {V_op:.0f} m/s (p={p_op:.0f} Pa) on RAISED boom, Cf 2.0, hub moment by projected face:")
p(f"  30 mm face (wind in the rotation plane): {Mw_30:.2f} Nm ; worst oblique {w_obl:.1f} mm at {th_obl} deg: {Mw_op:.2f} Nm ; "
  f"old 60 mm face: {Mw_60:.2f} Nm")
p(f"Required torque WITHOUT counterweight (worst oblique) = {T_noCW:.2f} Nm   [60 mm face: {T_noCW_60:.2f}]")
p(f"Required torque WITH counterweight    (worst oblique) = {T_CW:.2f} Nm   [60 mm face: {T_CW_60:.2f}]")
T_sel = max(2.0 * T_CW, 1.5 * T_noCW)
p(f"Production selection: rated >= max(2.0 x {T_CW:.1f} (with CW), 1.5 x {T_noCW:.1f} (CW-missing fault)) = {T_sel:.1f} Nm "
  f"at output speed >= {rpm:.0f} rpm  -> keep the >= 30 Nm specification for a 15 m/s operating-wind rating")
p("  (specify a 24 V DC self-locking worm gearmotor with a DATASHEET rated torque >= 30 Nm, 10-15 rpm output, >= 12 mm shaft;")
p("   no such part is in the BOM yet - see docs/OPEN_DECISIONS.md.)")

# --- the 18 Nm BOM motor (Lucas TVS wiper motor): what can it actually do?
T_motor = 18.0
p()
p("BOM motor check (Lucas TVS 24 V wiper motor, listed 18 Nm; rated vs stall, speed, duty and self-locking NOT stated by the vendor):")
p(f"  Margin at {V_op:.0f} m/s: 18 / {T_CW:.1f} = {T_motor/T_CW:.2f} (target >= 2.0) -> SHORT for a 15 m/s rating")
# operating-wind limit for the 18 Nm motor at SF 2.0 (with installed counterweight) and at SF 1.5
def V_limit(SF, w_mm=w_obl):
    base = T_req(0.0, w_mm, True)
    k = M_raised(1.0, w_mm)
    return math.sqrt(max(0.0, (T_motor / SF - base) / k))
V_sf2 = V_limit(2.0); V_sf15 = V_limit(1.5)
T_still = T_req(0.0, w_obl, True)
p(f"  Still-air requirement (gravity residual + acceleration + friction) = {T_still:.2f} Nm -> margin {T_motor/T_still:.1f}x")
p(f"  Highest operating wind for margin 2.0 on 18 Nm = {V_sf2:.1f} m/s ({V_sf2*3.6:.0f} km/h); for margin 1.5 = {V_sf15:.1f} m/s ({V_sf15*3.6:.0f} km/h)")
V_demo = math.floor(V_sf2)
p(f"  => DEMO rating chosen: operate the boom only in wind <= {V_demo} m/s ({V_demo*3.6:.0f} km/h); above that the boom stays lowered/pinned. "
  f"Production rating (15 m/s) needs the >= 30 Nm motor.")
Tq_demo = T_req(V_demo, w_obl, True)
p(f"  Check: at {V_demo} m/s required {Tq_demo:.2f} Nm, 18 Nm gives margin {T_motor/Tq_demo:.2f}")
P_mech = T_CW * omega
p(f"  Mechanical power at peak (15 m/s case) = {P_mech:.1f} W ; with worm eff. ~40% -> electrical ~ {P_mech/0.4/0.8:.0f} W")
p("  Motor current is NOT known (no vendor figure). The 24 V bus is sized for a 5 A firmware limit (IS sense); stall current to be bench-measured.")
p("  Self-locking is NOT assumed anywhere in this design: holding is by the lowered-boom rest/stop and a storm-lock pin (below).")

# --- 7. raised-boom survival wind (boom left up, 47 m/s Delhi gust) - previously unanalysed
V_surv = 47.0; p_surv = 0.6 * V_surv ** 2
p()
p(f"RAISED-BOOM SURVIVAL CASE: Delhi design gust {V_surv:.0f} m/s -> p = {p_surv:.0f} Pa (IS 875-3, Kd=Ka=Kc=1.0), Cf 2.0, arm Lb/2 = {Lb/2:.2f} m")
M_s30 = M_raised(V_surv, 30.0); M_sob = M_raised(V_surv, w_obl); M_s60 = M_raised(V_surv, 60.0)
p(f"  back-driving moment at the hub: 30 mm face {M_s30:.0f} Nm ; worst oblique ({w_obl:.1f} mm) {M_sob:.0f} Nm ; 60 mm bounding face {M_s60:.0f} Nm")
M_s_design = M_sob
p(f"  design value used for checks = {M_s_design:.0f} Nm (oblique); the earlier '100-115 Nm' quote was the 60 mm bounding face ({M_s60:.0f} Nm)")
d_sh = 20.0; Wp = math.pi * d_sh ** 3 / 16
p(f"  20 mm stub shaft (MS E250): tau = T/Wp = {M_s_design*1e3/Wp:.0f} MPa (E250 shear yield ~0.58x250 = 145 MPa) -> FoS {145/(M_s_design*1e3/Wp):.1f}")
Fk = M_s_design / (d_sh / 2e3); kb, kh, kL = 6.0, 6.0, 25.0
p(f"  6x6x25 key: shear {Fk/(kb*kL):.0f} MPa, bearing {Fk/((kh/2)*kL):.0f} MPa (E250 yield 250) -> FoS {250/(Fk/((kh/2)*kL)):.1f} bearing")
Flat = p_surv * 2.0 * 0.030 * Lb
p(f"  lateral reaction on the two UCFL204 bearings from the raised boom: {Flat:.0f} N total (30 mm face) -> well below a UC204 static rating (datasheet value to be confirmed)")
p(f"  The 18 Nm motor/gearbox CANNOT be assumed to hold {M_s_design:.0f} Nm (stall 18 Nm, back-drive behaviour unknown).")
p("  => the survival load path is a STORM-LOCK PIN through the hub/boom carrier into the frame (boom lowered or raised), not the gearbox.")
p("     Storm rule (no anemometer in the BOM): on an IMD thunderstorm / dust-storm warning the guard lowers the boom and drops the pin.")
p(f"     Pin check (PROPOSED, not yet in the CAD): 10 mm MS pin in double shear carries {M_s_design:.0f} Nm at a 60 mm lever = {M_s_design/0.060:.0f} N -> "
  f"tau = {M_s_design/0.060/(2*math.pi*25):.0f} MPa (FoS {145/(M_s_design/0.060/(2*math.pi*25)):.1f} vs 145 MPa). FEA/bench to confirm.")

# --- closed boom, lateral gust vs the breakaway shear pin
M_break = math.pi * 5.0 ** 2 / 4 * tau_u_pin * e_sp          # Nm (d = 5 mm [mm2] x tau [N/mm2] x e [m]; single shear, e = 35 mm)
F_lat = p_surv * 2.0 * 0.060 * L_hinge
M_lat = F_lat * L_hinge / 2
V_pin50 = math.sqrt((0.5 * M_break) / (0.6 * 2.0 * 0.060 * L_hinge * L_hinge / 2))
p()
p(f"CLOSED-BOOM GUST vs BREAKAWAY PIN: gust moment about the vertical hinge = {p_surv:.0f} Pa x 2.0 x 60 mm x {L_hinge:.3f} m x {L_hinge/2:.3f} m = {M_lat:.0f} Nm")
p(f"  5 mm 6061-T6 pin breaks at about {M_break:.0f} Nm (nominal tau_u 0.6 Rm; scatter of +/-10 % is normal) -> gust = {M_lat/M_break*100:.0f} % of break")
p(f"  Wind speed that loads the pin to 50 % of its break value (the service margin used for the 50 N push) = {V_pin50:.1f} m/s")
p("  => in the 47 m/s design gust the pin is at about 90 % of break: a nuisance shear is possible (fail-safe: the boom swings free). Keep spare pins (BOM).")
barrier = dict(m_boom=m_boom, sig=sig_hub, FoS=110 / sig_hub, d=d_tip, T_noCW=T_noCW, T_CW=T_CW, m_cw=m_cw,
               Mhub=Mhub, balance=balance, V_demo=V_demo, V_sf2=V_sf2, M_s_design=M_s_design, M_s60=M_s60,
               M_lat=M_lat, M_break=M_break, T_still=T_still, T_CW_60=T_CW_60, n_plates=n_plates, m_cw_req=m_cw_req,
               Mw_op=Mw_op, w_obl=w_obl, th_obl=th_obl, V_pin50=V_pin50)

# --------------------------------------------------------------- thermal
hdr("5. EDGE NODE IP65 ENCLOSURE - THERMAL (sealed, natural convection)")
T_amb = 45.0
T_HAT_MAX = 50.0                # Raspberry Pi AI HAT+ operating ambient limit 0-50 degC (Raspberry Pi product brief)
T_SW_MAX = 40.0                 # Netgear GS305P operating limit 0-40 degC
T_int_max = T_HAT_MAX           # the limit that matters (the previous 55 degC allowance exceeded the HAT+ rating)
h = 5.0                         # W/m2K natural convection, enclosure walls (assumed)
eps = 0.90
BOXES = {   # name: (W, H, D) m external; back face against the pole is not counted
    "CAD/CALCS box 300x400x180": (0.300, 0.400, 0.180),
    "BOM box 300x300x210 (GRASP, bought)": (0.300, 0.300, 0.210),
}
BOX_USED = "BOM box 300x300x210 (GRASP, bought)"
def box_area(W, H, D): return W * H + 2 * H * D + 2 * W * D
Tm = (T_amb + T_int_max) / 2 + 273.15
h_r = 4 * eps * 5.67e-8 * Tm ** 3
# SMPS loading: everything on 24 V (incl. RFID reader 10 W + motor avg 6 W, which dissipate outside). Same loading model as before.
P_out_24 = 12.0 / 0.92 + 4.0 + 6.0 / 0.85 + 2.0 + 10.0 + 6.0 + 2.0
eff_smps = 0.87                 # assumed ~87 % at ~30 % load (LRS-200-24 curve NOT opened; the old LRS-150 figure is kept)
P_smps_loss = P_out_24 * (1 / eff_smps - 1)
loads = [
    ("Raspberry Pi 5 8GB + AI HAT+ (Hailo-8) peak", 12.0),
    ("24->5 V 5 A buck for Pi (eff 92%)", 12.0 * (1 / 0.92 - 1)),
    ("Industrial PoE switch 5-port (self) ", 4.0),
    ("PoE conversion loss for 6 W camera (85%)", 6.0 * (1 / 0.85 - 1)),
    ("Lane Controller PCB (ESP32-S3, drivers, LED, buzzer)", 2.0),
    ("Motor H-bridge (IBT-2 module) losses, 10% duty avg", 1.0),
    ("DC-UPS module (float charge)", 1.0),
]
loads_smps = (f"Mean Well LRS-200-24 losses ({P_out_24:.0f} W out @ {eff_smps*100:.0f}%)", P_smps_loss)
Q_all = sum(x[1] for x in loads) + P_smps_loss
Q_noSMPS = sum(x[1] for x in loads)
for n, q in loads + [loads_smps]:
    p(f"  {n:58s} {q:5.1f} W")
p(f"  {'TOTAL, everything in one box':58s} {Q_all:5.1f} W   (without the 24 V PSU: {Q_noSMPS:.1f} W)")
p(f"Limits: AI HAT+ air {T_HAT_MAX:.0f} degC (the old 55 degC allowance was above it) ; GS305P switch {T_SW_MAX:.0f} degC. Ambient {T_amb:.0f} degC.")
p(f"Radiation coefficient (eps {eps}, T_mean {Tm-273.15:.0f} degC): h_r = {h_r:.1f} W/m2K. CONVECTION-ONLY numbers are the design basis; radiation is shown as a sensitivity.")
frac, frac_smps = 0.80, 0.50    # through-wall sink takes 80 % of Pi/HAT heat (5 mm Al spreader + pads) and 50 % of PSU loss if it is inside
res = {}
def case(name, W, H, D, Q, Q_sink):
    A = box_area(W, H, D)
    dT = (Q - Q_sink) / (h * A); dTr = (Q - Q_sink) / ((h + h_r) * A)
    return dict(name=name, A=A, Q=Q, Q_sink=Q_sink, dT=dT, T=T_amb + dT, Tr=T_amb + dTr, Tmax_amb=T_HAT_MAX - dT, Tmax_amb_r=T_HAT_MAX - dTr)
p()
p(f"{'Case':62s} {'A m2':>6s} {'Q_air W':>8s} {'T_int':>6s} {'T_int+rad':>9s} {'max Tamb':>8s}  verdict (<= {T_HAT_MAX:.0f} degC)")
for bn, (W, H, D) in BOXES.items():
    for tag, Q, Qs in (
        ("sealed, all loads in box", Q_all, 0.0),
        ("+ through-wall sink (80 % Pi/HAT, 50 % PSU)", Q_all, frac * 12.0 + frac_smps * P_smps_loss),
        ("PSU moved to separate power box + sink (80 % Pi/HAT)", Q_noSMPS, frac * 12.0),
    ):
        c = case(f"{bn}: {tag}", W, H, D, Q, Qs)
        res[(bn, tag)] = c
        v = "FAILS" if c["T"] > T_HAT_MAX else "ok"
        v2 = "FAILS" if c["Tr"] > T_HAT_MAX else "ok"
        p(f"{c['name']:62s} {c['A']:6.3f} {c['Q']-c['Q_sink']:8.1f} {c['T']:6.1f} {c['Tr']:9.1f} {c['Tmax_amb']:8.1f}  conv {v} / with radiation {v2}")
tag_sink = "+ through-wall sink (80 % Pi/HAT, 50 % PSU)"
tag_move = "PSU moved to separate power box + sink (80 % Pi/HAT)"
c_sealed = res[(BOX_USED, "sealed, all loads in box")]
c_hs = res[(BOX_USED, tag_sink)]
c_move = res[(BOX_USED, tag_move)]
p()
p(f"CONCLUSION (bought box 300x300x210): sealed {c_sealed['T']:.1f} degC ; with sink {c_hs['T']:.1f} degC (FAILS the {T_HAT_MAX:.0f} degC HAT+ limit, as before);")
p(f"  with the 24 V PSU moved to a small separate power box the Edge box is {c_move['T']:.1f} degC convection-only, {c_move['Tr']:.1f} degC counting radiation.")
p(f"  That straddles the limit: NOT demonstrated. The highest ambient that keeps the air at {T_HAT_MAX:.0f} degC is {c_move['Tmax_amb']:.1f} degC (convection) to {c_move['Tmax_amb_r']:.1f} degC (with radiation).")
p(f"  Changing the box from 300x300x210 to 300x400x180 changes the sealed/sink result by <= 1 K ({res[(list(BOXES)[0], tag_move)]['T']:.1f} vs {c_move['T']:.1f} degC): the box size is NOT the lever, the heat load is.")
p(f"  GS305P: its air is the same box air ({c_move['T']:.0f} degC) against a {T_SW_MAX:.0f} degC rating -> the consumer switch is outside its rating at 45 degC ambient in every case; see OPEN_DECISIONS (industrial PoE switch).")
Q_air = c_hs['Q'] - c_hs['Q_sink']
# power box (PSU + LRS-100-12 + MCBs + SPD + RCCB), plastic 250x190x95 (Jenshri pole box), 5 exposed faces
A_pb = 0.25 * 0.19 + 2 * 0.19 * 0.095 + 2 * 0.25 * 0.095
Q_pb = P_smps_loss + 2.0 + 1.0       # LRS-200-24 loss + LRS-100-12 loss (assumed 2 W) + mini UPS float (1 W)
dT_pb = Q_pb / (h * A_pb)
p(f"Power box 250x190x95 (plastic), A = {A_pb:.3f} m2, Q = {Q_pb:.1f} W -> dT = {dT_pb:.1f} K -> {T_amb+dT_pb:.1f} degC air at 45 degC ambient (PSU derating at that temperature: confirm on the Mean Well sheet)")
# heat sink sizing for the sink case
T_sink = 65.0; eta_fin = 0.85
Q_hs = c_move['Q_sink']
A_hs = Q_hs / (h * eta_fin * (T_sink - T_amb))
nf, Lf, Hf, Bw, Bl = 18, 0.150, 0.035, 0.200, 0.150
A_hs_prov = nf * 2 * Lf * Hf + Bw * Bl
p(f"Sink: {Q_hs:.1f} W through a 200 x 150 mm extruded sink at {T_sink:.0f} degC base, eta_fin {eta_fin}: required A = Q/(h eta dT) = {A_hs:.3f} m2 ; "
  f"provided ({nf} fins x {Hf*1e3:.0f} x {Lf*1e3:.0f} + base) {A_hs_prov:.3f} m2 (margin {A_hs_prov/A_hs:.2f}x)")
Qsol = 0.30 * 1000 * (0.300 * 0.210 + 0.300 * 0.300 * 0.5)
p(f"Solar gain (unshaded, alpha 0.30, 1000 W/m2 on top + 50% front) ~ {Qsol:.0f} W -> sun shield is MANDATORY")
p("  (2 mm Al canopy, 25 mm ventilated air gap, cuts absorbed solar ~80%; not included above).")
V_fan = Q_air / (1.1 * 1005 * max(T_HAT_MAX - T_amb, 1e-9)) * 3600
p(f"Fan alternative: airflow = Q/(rho cp dT) = {V_fan:.1f} m3/h for a 5 K rise (one 60 mm fan) but it drops the rating to IP54 - not chosen.")
p("Derating that does not need hardware (targets, to be bench-verified): ANPR frame rate capped from 75 degC SoC; Pi 5 Active Cooler fan (BOM) inside the box.")
thermal = dict(Q=Q_all, A=c_sealed['A'], dT_sealed=c_sealed['dT'], T_sealed=c_sealed['T'], T_hs=c_hs['T'], T_move=c_move['T'], T_move_r=c_move['Tr'],
               A_hs=A_hs, A_hs_prov=A_hs_prov, Tmax_amb=c_move['Tmax_amb'], Tmax_amb_r=c_move['Tmax_amb_r'], T_pb=T_amb + dT_pb,
               T_sealed_cad=res[(list(BOXES)[0], "sealed, all loads in box")]['T'], T_hs_cad=res[(list(BOXES)[0], tag_sink)]['T'])

# --------------------------------------------------------------- masses
hdr("6. MASS ESTIMATES (analytical volume x density; see MATERIALS.md)")
rho = {k: v[3] for k, v in MAT.items()}
masses = []
def m(name, vol_mm3, mat):
    kg = vol_mm3 * 1e-9 * rho[mat]
    masses.append((name, mat, kg)); return kg
m("Pole 80x80 x 2400 (5.4 kg/m vendor approx)", 5.4 / 2700 * 1e9 * 2.4 / 1, "6063-T5")
m("Base plate 250x250x16 - 4xD14 - D30", (250 * 250 - 4 * math.pi * 7 ** 2 - math.pi * 15 ** 2) * 16, "IS2062-E250")
m("Socket cheeks 2x(92x150x6)+2x(80x150x6)", (2 * 92 + 2 * 80) * 150 * 6, "IS2062-E250")
m("Gussets 4x (0.5x100x120x6)", 4 * 0.5 * 100 * 120 * 6, "IS2062-E250")
m("Antenna arm 40x40x350", 1.5 / 2700 * 1e9 * 0.35, "6063-T5")
m("Antenna yoke 5 mm flat 280x... (flat area ~ 280x60+2x100x80)", (280 * 60 + 2 * 100 * 80) * 5, "5052-H32")
m("Antenna tilt plate 5 mm (flat ~ 240x200 + 2x80x60 - holes)", (240 * 200 + 2 * 80 * 60 - 4 * 50 * 50) * 5, "5052-H32")
m("Camera arm 40x40x300", 1.5 / 2700 * 1e9 * 0.30, "6063-T5")
m("Camera adapter plate 5 mm 120x80", 120 * 80 * 5, "5052-H32")
m("Sign bracket 3 mm 5052 (2x 200x80)", 2 * 200 * 80 * 3, "5052-H32")
m("Pole cap ASA 84x84x15 shell 2 mm", (84 * 84 * 2 + 4 * 84 * 13 * 2), "ASA-FDM")
m("Edge backplate 3 mm 5052 260x360", 260 * 360 * 3, "5052-H32")
m("Edge heat spreader 5 mm 6061 100x70 + bar 10x20x90", 100 * 70 * 5 + 10 * 20 * 90, "6061-T6")
m("Edge heat sink 200x150 base 6 mm + 18 fins 2x35x150", 200 * 150 * 6 + 18 * 2 * 35 * 150, "6063-T5")
m("Edge wall brackets 2x 3 mm MS 340x50", 2 * 340 * 50 * 3, "IS2062-E250")
m("Edge Pi tray PETG/ASA 100x75x3 + bosses", 100 * 75 * 3 + 8 * 400, "ASA-FDM")
m("Barrier base plate 300x250x8", 300 * 250 * 8, "IS2062-E250")
m("Barrier frame 20x20 posts 4x800 + 4x(260+210) rails (0.5 kg/m)", 0.5 / 2700 * 1e9 * (4 * 0.8 + 2 * 0.26 + 2 * 0.21) * 2 / 2, "6063-T5")
m("Barrier panels 2 mm 5052 (2x300x800 + 2x250x800 + 300x250)", (2 * 300 * 800 + 2 * 250 * 800 + 300 * 250) * 2, "5052-H32")
m("Motor plate 6 mm 6061 200x150", 200 * 150 * 6, "6061-T6")
m("Hub 6061 D70x30 + flange", math.pi * 35 ** 2 * 30, "6061-T6")
m("Boom carrier 2x 5 mm 6061 160x70", 2 * 160 * 70 * 5, "6061-T6")
m("Boom 60x30x1.5 x 1200", A_b * 1200, "6063-T5")
m("Counterweight MS plates (7 x 100x60x10)", barrier["m_cw"] / 7850 * 1e9, "IS2062-E250")
m("Limit flags 2x 3 mm 5052 60x40", 2 * 60 * 40 * 3, "5052-H32")
m("Photo-beam posts 2x 20x20x450 + 2x 100x100x5 feet", 0.5 / 2700 * 1e9 * 0.9 / 1 + 2 * 100 * 100 * 5 * 7850 / 2700, "6063-T5")
m("Occ node base ASA (D90 shell 2.4 mm)", math.pi * 45 ** 2 * 3 + math.pi * 90 * 30 * 2.4, "ASA-FDM")
m("Occ node cover ASA", math.pi * 45 ** 2 * 2.4 + math.pi * 90 * 18 * 2.4 - math.pi * 17 ** 2 * 2.4, "ASA-FDM")
for n, mt, kg in masses:
    p(f"  {n:62s} {mt:12s} {kg:7.3f} kg")

# --------------------------------------------------------------- summary
hdr("SUMMARY (analytical predictions - to be FEA-checked and bench-verified)")
p(f"Pole base moment (Delhi 47 m/s, all items)      : {rD['M']:.0f} Nm, base shear {rD['F']:.0f} N")
p(f"80x80 pole stress / FoS (6063-T5 Rp0.2 110 MPa)  : {rD['sigma']:.1f} MPa / {rD['FoS_6063-T5']:.2f}")
p(f"40x40 pole stress / FoS (rejected)                : {pole_table[('Delhi (pilot)','40x40')]['sigma']:.0f} MPa / "
  f"{pole_table[('Delhi (pilot)','40x40')]['FoS_6063-T5']:.2f}")
p(f"Pole top deflection at design wind (80x80)       : {rD['defl_top_mm']:.1f} mm")
p(f"Anchor tension (diag) / M12 FoS vs proof          : {T/1000:.2f} kN / {BOLT_88['fyb']/sig_b:.1f}")
p(f"Base plate 16 mm stress / FoS (E250)              : {3*T/PLATE_T**2:.0f} MPa / {250/(3*T/PLATE_T**2):.2f}")
p(f"Antenna bracket peak stress / FoS (5052-H32)      : {ant_br['sig']:.1f} MPa / {ant_br['FoS']:.1f}")
p(f"Boom hub moment / stress / FoS / tip deflection   : {barrier['Mhub']:.1f} Nm / {barrier['sig']:.1f} MPa / "
  f"{barrier['FoS']:.1f} / {barrier['d']:.1f} mm")
p(f"Motor torque req. without / with counterweight    : {barrier['T_noCW']:.1f} / {barrier['T_CW']:.1f} Nm at 15 m/s "
  f"-> production spec >= 30 Nm rated; BOM 18 Nm motor rated for <= {barrier['V_demo']} m/s operating wind (demo)")
p(f"Raised-boom survival moment at 47 m/s (oblique / 60 mm) : {barrier['M_s_design']:.0f} / {barrier['M_s60']:.0f} Nm -> storm-lock pin, not the gearbox")
p(f"Closed-boom gust moment / pin break moment        : {barrier['M_lat']:.0f} / {barrier['M_break']:.0f} Nm")
p(f"Edge Node dissipation / sealed T_int / with HS    : {thermal['Q']:.1f} W / {thermal['T_sealed']:.1f} degC / "
  f"{thermal['T_hs']:.1f} degC (FAILS 50 degC HAT+ limit) ; PSU moved out: {thermal['T_move']:.1f} degC conv. / {thermal['T_move_r']:.1f} degC with radiation")

if "--md" in sys.argv:
    import os
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "calcs_results.txt"), "w") as f:
        f.write("\n".join(out_lines) + "\n")
