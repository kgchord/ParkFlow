# ParkFlow Demo Lane: Engineering Calculations

All values below are **analytical predictions** from `calcs.py`. They are targets that still need FEA checks and bench verification. None of them is a test result. To regenerate: `python3 cad/calcs/calcs.py --md`, which writes `calcs_results.txt`.

Target factor of safety: **FoS ≥ 2.0 against yield** (0.2 % proof) for every structural part under its design load.

## Materials and section data used

| Material | E (MPa) | Rp0.2 (MPa) | Rm (MPa) | ρ (kg/m³) | Basis |
|---|---|---|---|---|---|
| Al 6063-T5 (T-slot, boom tube) | 69 500 | 110 | 160 | 2700 | EN 755-2 min (conservative for T-slot) |
| Al 6063-T6 | 69 500 | 170 | 215 | 2700 | EN 755-2 min |
| Al 5052-H32 sheet | 70 300 | 130 | 210 | 2680 | EN 485-2 min |
| Al 6061-T6 plate/bar | 68 900 | 240 | 290 | 2700 | EN 755-2 / ASTM B209 |
| MS IS 2062 E250 (≈ S275 check) | 200 000 | 250 | 410 | 7850 | IS 2062 |
| ASA (FDM, design value) | 2 000 | 25 | 30 | 1070 | layered-part knock-down from ~40 MPa bulk |
| Bolts, class 8.8 | – | 640 | 800 | – | ISO 898-1; tensile stress area As: M12 = 84.3 mm² |

T-slot section properties (Wolweiss profiles, vendor pages on reiman.pt):

| Profile | Ix / Iy (cm⁴) | Wx / Wy (cm³) | Source |
|---|---|---|---|
| 40x40 4-slot | 9.1 / 9.1 | 4.6 / 4.6 | https://reiman.pt/en/ast04004004-aluminium-profile-40x40-4-slots/ |
| 40x80 6-slot | 16.6 / 63.2 | 8.3 / 15.8 | https://reiman.pt/en/ast04008006-aluminium-profile-40x80-6-slots/ |
| 80x80 8-slot | 109.9 / 109.9 | 27.5 / 27.5 | https://reiman.pt/en/ast08008008-aluminium-profile-80x80-8-slots |

Assumption: the supplier for the Indian build (Delhi NCR / Bengaluru) must provide a profile with W ≥ 27 cm³. Confirm against its datasheet when ordering.

---

## 1. Wind on the lane gantry pole (IS 875 Part 3 : 2015)

**Formulas.** Vz = Vb·k1·k2·k3·k4 ; pz = 0.6·Vz² (Pa) ; pd = Kd·Ka·Kc·pz ≥ 0.7·pz ; F = Cf·pd·A ; M = Σ F·z.

**Factors:**
- k1 = 1.00 (Table 1, general structure, 50-year life).
- k2 = 1.00 (Table 2, Terrain Category 2, open parking lot, z ≤ 10 m; k2 is not reduced below 10 m).
- k3 = 1.00 (flat site).
- k4 = 1.00 (non-cyclonic importance).
- Kd = Ka = Kc = 1.0. This is conservative; the code would allow reductions.
- Cf = 1.3 for flat plate-like boxes (reader, sign, enclosure), 1.2 for the cylindrical camera, 2.0 for square sections (pole, arms).

**Exposed items at Delhi, Vb = 47 m/s** (Vz = 47.0 m/s, pz = pd = **1325 Pa**):

| Item | A (m²) | Cf | F (N) | z (m) | M (N·m) |
|---|---|---|---|---|---|
| RFID reader 260x260 | 0.0676 | 1.3 | 116.5 | 1.45 | 168.9 |
| Antenna arm 40x40x350 | 0.0140 | 2.0 | 37.1 | 1.60 | 59.4 |
| ANPR camera 220x80 | 0.0176 | 1.2 | 28.0 | 1.20 | 33.6 |
| Camera arm 40x40x300 | 0.0120 | 2.0 | 31.8 | 1.20 | 38.2 |
| P10 sign cabinet 360x200 | 0.0720 | 1.3 | 124.1 | 2.25 | 279.1 |
| Edge Node 300x400 + hood | 0.1200 | 1.3 | 206.8 | 0.90 | 186.1 |
| Pole 80x80 x 2.4 m | 0.1920 | 2.0 | 509.0 | 1.20 | 610.7 |
| **Total wind** | | | **1053** | | **1376** |
| Gravity eccentricity (all brackets on one side) | | | | | 28 |
| **Design base moment M** | | | **V = 1053 N** | | **1404 N·m** |

All items are assumed loaded face-on at the same time, which is an upper bound.

**Pole section check** (weak axis governs, since wind can come from any direction). σ = M / W ; FoS = Rp0.2 / σ.

| City | Vb (m/s) | pd (Pa) | Profile | M (N·m) | σ (MPa) | FoS 6063-T5 | FoS 6063-T6 | Top deflection (mm) |
|---|---|---|---|---|---|---|---|---|
| **Delhi (pilot)** | 47 | 1325 | 40x40 | 1099 | 238.8 | **0.46 ✗** | 0.71 | 244 |
| Delhi | 47 | 1325 | 40x80 | 1099 | 132.4 | 0.83 ✗ | 1.28 | 134 |
| **Delhi** | 47 | 1325 | **80x80** | **1404** | **51.1** | **2.15 ✓** | 3.33 | **26.0** |
| Mumbai | 44 | 1162 | 80x80 | 1234 | 44.9 | 2.45 | 3.79 | 22.8 |
| Chennai | 50 | 1500 | 80x80 | 1585 | 57.6 | 1.91 (use T6 → 2.95) | 2.95 | 29.4 |
| Bengaluru | 33 | 653 | 80x80 | 706 | 25.7 | 4.28 | 6.62 | 12.8 |
| Bengaluru | 33 | 653 | 40x40 | 556 | 120.8 | 0.91 ✗ | 1.41 | 120 |

**Design decision.** Our initial concept of a single 40x40 pole (Stage 1 does not specify a pole) is predicted **not adequate**: it reaches FoS 0.46 at Delhi design wind and would yield. The pole is upsized to an **80x80 8-slot** profile, which gives FoS 2.15 on T5 minima. 40x40 is still used for the arms and 20x20 for the photo-beam and barrier frames. For a Chennai site, specify 6063-T6 (FoS 2.95).

Pole-top deflection is 26 mm (about L/92) at the design gust. That is acceptable for strength. ANPR image stability at service wind (~15 m/s) scales as (15/47)², giving about 2.6 mm at the top and less than 1 mm at camera height.

## 2. Base plate and anchors (MS E250, 250 x 250, 4x M12 on 190 PCD)

The bolts sit on a 134.4 mm square (side s = PCD/√2).

| Check | Formula | Value |
|---|---|---|
| Bolt tension, wind normal to a side (2 bolts) | T = M / (2s) | 5.23 kN |
| Bolt tension, diagonal wind (1 bolt), **governs** | T = M / PCD | **7.39 kN** |
| M12 8.8 tensile stress | σ = T / As | 87.7 MPa → **FoS 7.3** vs 640 MPa nominal yield Rp0.2 (ISO 898-1 proof stress is 580 MPa, which gives FoS 6.6) |
| Shear per bolt | V/4 | 263 N (3.1 MPa, negligible) |
| Chemical anchor demand (×2.0) | | 14.8 kN, to be checked against the anchor's ETA/datasheet |
| Plate bending, 10 mm | σ = 3T/t² (45° yield-line cantilever, no gusset credit) | 222 MPa, FoS 1.13 ✗ |
| Plate bending, 12 mm | same | 154 MPa, FoS 1.62 ✗ |
| **Plate bending, 16 mm (selected)** | same | **87 MPa, FoS 2.89 ✓** |
| Socket bearing (h = 150) | F = M / (2/3·h) | 14.0 kN; 8.8 MPa on 80x20 contact |
| Gusset 6 mm, axial | F = M / (2·0.10 m) | 7.02 kN → 19.5 MPa, FoS 12.8 |
| Gusset fillet welds 6 mm leg, a = 4.2, L = 440 mm | τ = F/(a·L) | 3.8 MPa (vs fvw ≈ 189 MPa) |

The plate is set at **16 mm** because the hand model gives no credit to the gussets stiffening the plate edges. If FEA (recipe R1) shows a 12 mm plate reaches FoS ≥ 2.0 with the gussets acting, it can be thinned to save about 1.9 kg.

## 3. RFID antenna tilt bracket (5 mm 5052-H32 yoke + tilt plate, M8 pivots, M6 arc-slot lock)

| Check | Value |
|---|---|
| Wind on reader F = pd·Cf·A | 116 N; weight 29 N |
| Cheek in-plane bending (each cheek carries half of the resultant, 70 mm lever) | 0.8 MPa |
| Bend root, out-of-plane (all wind on one cheek, 30 mm offset) σ = 6M/(b·t²) | **10.5 MPa → FoS 12.4** (5052-H32); 23.8 if 5 mm MS |
| Tilt moment about pivot (W·60 + F·30 mm) | 5.26 N·m → 53 N per M6 lock (friction capacity ≈ 1600 N, slip FoS 30) |
| M8 pivot bearing in 5 mm / pin shear | 1.5 MPa / 1.6 MPa |
| 40x40 arm root (L = 350), biaxial | 49 N·m → 10.6 MPa, FoS 10.4 |
| Arm torsion (reader 180 mm below arm axis) | 21 N·m, taken by 2 corner brackets + 2 T-nuts (105 N couple) |

The bracket is stiffness-driven, not strength-driven. 5 mm sheet keeps the first natural frequency high, so the reader does not flutter.

## 4. Demo boom barrier (1.2 m, Al 6063-T5 RHS 60x30x1.5)

**Section properties.** A = 261 mm². Iv = 123 316 mm⁴, Wv = 4111 mm³. Ih = 41 506 mm⁴, Wh = 2767 mm³.

**Boom mass.** 0.846 kg for the tube (0.705 kg/m) plus 0.15 kg of fittings, total **1.00 kg**.

| Load case | Formula | Result |
|---|---|---|
| Self-weight + 50 N vertical tip load | M = F·L + wL²/2 + m_tip·g·L | **M_hub = 66.7 N·m** |
| Bending stress at the hub | σ = M / Wv | **16.2 MPa → FoS 6.8** |
| Tip deflection | δ = FL³/3EI + wL⁴/8EI + … | **3.7 mm (L/327)** |
| 50 N horizontal tip push | σ = F·L / Wh | 21.7 MPa → FoS 5.1 |
| Carrier clamp, 2x M6 at 60 mm | couple = M / 0.06 | 1112 N; 62 MPa bearing on 2 × 1.5 mm walls → FoS 3.9. Fit crush sleeves. |
| **Breakaway shear pin** (6061-T6, τu ≈ 0.6·Rm = 174 MPa, e = 35 mm from hinge, lever 1155 mm) | d = √(4F/(π·τu)) for a 100 N break | d = 4.91 → **use 5.0 mm**. Breaks at 104 N at the tip; 50 N service load is 48 % of break. |

**Drive torque.** The boom opens 0 → 90° in 2.5 s with a 0.4 s trapezoidal acceleration ramp: ω = 0.75 rad/s (7.1 rpm), α = 1.87 rad/s².

*Corrections made on 25 Oct (design update).* (1) The counterweight is the 7 plates actually in the CAD and BOM: 7 × 0.471 = **3.30 kg, 94 % balance** (the earlier table used 85 % and printed "7 plates = 2.98 kg"). The boom stays boom-heavy (balance < 100 %), so with the motor unpowered it can only close, with a residual tip force of 0.34 N. (2) The raised boom is 60 mm in the rotation plane and 30 mm across it, so wind along the lane acts on the **30 mm face**; the worst oblique direction (32°) gives an equivalent 48.5 mm face (30 cos²θ + 60 sinθ cosθ, Cf kept at 2.0). The old table used the 60 mm bounding face.

| Term (15 m/s production case) | Without counterweight | With 7-plate counterweight (94 %) |
|---|---|---|
| Gravity of boom about shaft | 6.88 N·m | 0.41 N·m |
| Inertia (boom 0.622, counterweight 0.132 kg·m²) × α | 1.16 N·m | 1.41 N·m |
| Operating wind, 15 m/s, raised boom, 48.5 mm worst-oblique face | 9.44 N·m | 9.44 N·m |
| Bearing/seal friction | 0.30 N·m | 0.30 N·m |
| **Required torque** | **17.8 N·m** | **11.6 N·m** |
| Same with the old 60 mm bounding face | 20.0 N·m | 13.8 N·m |

- **Production specification (unchanged): ≥ 30 N·m.** max(2.0 × 11.6, 1.5 × 17.8) = 26.7 N·m, rounded up to 30 N·m (≈ 306 kgf·cm). 24 V DC, self-locking worm, 10–15 rpm output, shaft ≥ 12 mm with key or D-flat, **datasheet** rated torque. No such part is in the BOM yet (docs/OPEN_DECISIONS.md D1).
- **Power:** peak mechanical power 8.6 W; at about 40 % worm efficiency roughly 27 W electrical. The motor current is not stated by the vendor; the electrical design assumes a 5 A firmware limit on the IS sense (to be bench-verified).
- **BOM motor (Lucas TVS wiper motor, listed 18 N·m) is accepted as a DEMO motor with a wind limit, not as a 15 m/s motor.** Margin at 15 m/s is 18 / 11.6 = 1.56 (< 2.0). Still-air requirement is 2.1 N·m (8.5× margin). The highest operating wind that keeps a 2.0 margin on 18 N·m is **12.8 m/s (46 km/h)**; 15.4 m/s gives 1.5. **Demo rule: raise/lower the boom only in wind ≤ 12 m/s (43 km/h); at 12 m/s the requirement is 8.2 N·m, margin 2.2.** Whether 18 N·m is a rated or a stall figure is not stated, so this margin is itself to be bench-verified (stall-torque test, current and temperature rise at 10 cycles/min).
- **Self-locking is not assumed.** The vendor page does not say the worm is self-locking. The design does not rely on it: with the motor unpowered the 94 % counterweight leaves 0.41 N·m of closing torque, and the survival load case below is carried by a storm-lock pin.

**Raised-boom survival case (47 m/s Delhi design gust; was "not analysed").** p = 0.6·47² = 1325 Pa (IS 875-3, Kd = Ka = Kc = 1), Cf = 2.0, boom 1.2 m, arm 0.6 m.

| Face used | Hub moment trying to back-drive the drive |
|---|---|
| 30 mm (wind exactly in the rotation plane) | 57 N·m |
| **48.5 mm worst oblique (design value)** | **93 N·m** |
| 60 mm bounding face (the earlier "100–115 N·m") | 115 N·m |

- The 18 N·m gearmotor **cannot be assumed to hold 93 N·m**. The load path is a **storm-lock pin** through the hub/carrier into the frame: proposed 10 mm MS pin in double shear at a 60 mm lever = 1.54 kN, 10 MPa, FoS 14.8 (not yet in the CAD; FEA/bench to confirm). With the boom locked, the stub shaft (Ø20 MS) is not loaded by wind.
- If the boom is left up and unpinned, the Ø20 mm stub shaft sees 59 MPa (FoS 2.5 vs 145 MPa shear yield) and the 6×6×25 key 124 MPa bearing (FoS 2.0). The lateral reaction on the two UCFL204 bearings is only 95 N. These are hand numbers.
- **Storm rule.** There is no anemometer in the BOM, so the rule is procedural: on an IMD thunderstorm / dust-storm warning (or wind above 12 m/s) the guard lowers the boom and drops the storm-lock pin. This is an open decision (docs/OPEN_DECISIONS.md D5): a wind sensor + automatic lock-down would remove the dependence on a person.

**Closed boom, lateral gust vs the breakaway pin.** Gust moment about the vertical hinge = 1325 × 2.0 × 0.060 × 1.155 × 0.578 = **106 N·m**. The 5 mm 6061-T6 pin breaks at π·5²/4 × 174 MPa × 35 mm ≈ **120 N·m** (= 104 N at the 1.155 m tip lever, as quoted in the table above). So the design gust is **89 % of the break value**: nuisance shearing is possible in the strongest gust, which is fail-safe (the boom swings free) but costs a spare pin. A 50 % service load is reached at 35.3 m/s. Pin batch scatter of ±10 % would move this to 80–98 %: test pins from the actual rod (bench).

## 5. Edge Node enclosure: thermal (sealed IP65, natural convection, back face on the pole)

**Corrections made on 25 Oct (design update).** (1) The allowable internal air temperature is now **50 °C** (AI HAT+ ambient rating), not the 55 °C used before. (2) The box modelled is now the one that is bought: **GRASP 300 × 300 × 210 mm, exposed area 0.342 m²** (CAD/MATERIALS still show 300 × 400 × 180, 0.372 m²; both are computed below). (3) The supply is the **LRS-200-24** (the LRS-150-24 was too small for the 24 V bus peak), same loss model.

| Heat source inside the box | W |
|---|---|
| Raspberry Pi 5 8 GB + AI HAT+ (Hailo-8), peak | 12.0 |
| 24→5 V 5 A buck (η 92 %) | 1.0 |
| Industrial PoE switch (self) | 4.0 |
| PoE conversion loss for a 6 W camera (η 85 %) | 1.1 |
| Lane Controller PCB | 2.0 |
| Motor H-bridge (IBT-2 module), 10 % duty average | 1.0 |
| DC-UPS float charge | 1.0 |
| Mean Well LRS-200-24 losses (44 W out at an assumed 87 %) | 6.6 |
| **Total Q** (22.1 W without the 24 V supply) | **28.7 W** |

h = 5 W/m²K natural convection is the design basis; radiation (ε 0.9, h_r = 6.7) is shown as a sensitivity only. T_amb = 45 °C. "Sink" = 5 mm spreader + through-wall finned sink taking 80 % of the Pi/HAT heat (and 50 % of the supply loss when the supply is inside).

| Box | Case | Q left in the air | T_int convection only | T_int incl. radiation | Highest ambient for 50 °C (conv.) |
|---|---|---|---|---|---|
| 300×400×180 (CAD) | sealed | 28.7 W | 60.4 °C ✗ | 51.6 °C ✗ | 34.6 °C |
| 300×400×180 (CAD) | + sink | 15.8 W | 53.5 °C ✗ | 48.6 °C | 41.5 °C |
| 300×400×180 (CAD) | 24 V supply moved out + sink | 12.5 W | 51.7 °C ✗ | 47.9 °C | 43.3 °C |
| **300×300×210 (BOM)** | sealed | 28.7 W | 61.8 °C ✗ | 52.2 °C ✗ | 33.2 °C |
| **300×300×210 (BOM)** | + sink | 15.8 W | 54.2 °C ✗ | 48.9 °C | 40.8 °C |
| **300×300×210 (BOM)** | **24 V supply moved out + sink (chosen)** | **12.5 W** | **52.3 °C ✗** | **48.1 °C** | **42.7 °C (46.9 °C with radiation)** |

| Other item | Result |
|---|---|
| Fin area needed at a 65 °C sink base for 9.6 W (η_fin 0.85) | 0.113 m²; provided 0.219 m² (1.94×) |
| Power box (plastic 250 × 190 × 95 mm, 0.131 m²) holding the LRS-200-24, LRS-100-12, MCBs, RCCB, SPD: Q ≈ 9.6 W | ΔT = 14.6 K, air about 59.6 °C at 45 °C ambient (PSU derating at that temperature to be confirmed on the Mean Well sheet) |
| Solar gain, unshaded (α 0.30) | ≈ 32 W. **The sun hood is mandatory** (2 mm Al, 25 mm air gap). |
| Fan alternative | 10.3 m³/h for a 5 K rise. Rejected because it drops the box to IP54. |

**Verdict (not a pass).**
- **Sealed, all-in-one box:** 61.8 °C. The earlier "53.5 °C with the sink" was the CAD box with the sink and was already above 50 °C; in the bought box the same arrangement is **54.2 °C ✗**.
- **The box size is not the lever.** 300×400×180 versus 300×300×210 changes the result by 0.6 K; the heat load is what matters.
- **Chosen mitigation: move the 24 V supply (6.6 W) and the mains devices to a separate small power box** on the pole base, keep the sink, spreader and sun hood. Predicted Edge-box air: **52.3 °C on convection alone, 48.1 °C counting radiation.** That straddles the 50 °C limit, so **margin is not demonstrated**: the highest ambient that keeps the air at 50 °C is 42.7 °C (46.9 °C with radiation). Delhi summer afternoons exceed that.
- **Derating plan (targets, to be bench-verified):** ANPR frame rate capped from a 75 °C SoC reading; Pi 5 Active Cooler (BOM) circulates the internal air; a thermocouple log decides whether the Hailo-8 junction and Pi SoC stay below throttle even if the air exceeds 50 °C.
- **Netgear GS305P is rated 0–40 °C:** its air is the box air (≈ 52 °C), so it is outside its rating at 45 °C ambient in every case here. An industrial PoE switch (docs/OPEN_DECISIONS.md D8) or moving it out of the Edge box is needed.
- Bench-verify with thermocouples on the SoC, the Hailo-8 and the internal air at 45 °C in a hot-box; the AC4 soak is the real test.

---

## 6. FreeCAD FEM (CalculiX) recipes

Use FreeCAD 0.21 / 1.0, the FEM workbench, the ccx solver and the Gmsh mesher. Use second-order tetrahedra (Tet10) everywhere. The acceptance target is **FoS = Rp0.2 / σ_vM,max ≥ 2.0**, ignoring singular peaks at point constraints. Report the value 1 element away from any singularity, or at a fillet.

| # | Model (STEP) | Material (FEM material card) | Constraints | Loads | Mesh | Screenshot / result to report |
|---|---|---|---|---|---|---|
| R1 | `cad/step/base_weldment.step` with an 80x80 dummy pole: solid box 80 x 80 x 600 mm, E of 6063 scaled to I = 109.9 cm⁴, or import the true profile | E250: E 200 GPa, ν 0.3, Rp 250 | `ConstraintFixed` on the 4 anchor-hole washer faces (Ø24 annulus, top of plate). `ConstraintDisplacement` z = 0 (compression-only approximation) on the underside grout contact. Better: run once with no underside support (bolts only) as the worst case. | `ConstraintForce` 1053 N horizontal at z = 1.2 m on the dummy pole top face, plus `ConstraintForce` acting as a moment couple to give a total base moment of 1404 N·m. Two runs: wind on a face, and wind on the diagonal (45°). | Global 8 mm; 2 mm on the gusset toes, socket-to-plate weld line and bolt holes (mesh region) | von Mises contour (max at gusset toe or bolt hole), max displacement; probe plate σ next to the governing bolt. Target σ ≤ 125 MPa. Repeat with a 12 mm plate to test the thinning. |
| R2 | `cad/step/antenna_bracket_assy.step` (yoke + tilt plate at 20°) | 5052-H32: E 70.3 GPa, ν 0.33, Rp 130 | Fixed on the 2 web M6 hole washer faces (Ø12). Tie yoke ↔ tilt plate at the pivot holes with a pin-like constraint, or a bonded `ConstraintContact` at the spacer faces, plus the lock-bolt hole. | Reader as a remote load: 116 N wind (−y → +y) + 29 N gravity at the reader CG, 60 mm in front of the tilt plate. Apply it with `ConstraintForce` on the 4 reader bolt-hole faces (¼ each). | 3 mm global, 1 mm at the bend roots and slot ends | von Mises at the cheek bend root and arc-slot ends, displacement at the reader centre. Target σ ≤ 65 MPa. Also run `Frequency` analysis (with 3 kg point mass): first mode > 25 Hz. |
| R3 | Boom: RHS 60x30x1.5 x 1200 extrusion (Part workbench) + carrier plates from `cad/dxf/boom_carrier_plate.dxf` extruded 5 mm | 6063-T5: E 69.5 GPa, Rp 110; 6061-T6: Rp 240 for carrier/hub | Fixed on the hub-side hinge + shear-pin bore surfaces of the carrier | Gravity (`ConstraintSelfWeight`) + 50 N tip (vertical). Second run: 50 N horizontal. Third run: 100 N horizontal to check that the shear pin (5 mm 6061, shear-stress probe) fails before the boom/carrier yield. | 2.5 mm global (shell alternative: `ElementGeometry2D` 1.5 mm), 1 mm at the clamp holes | σ_vM at the clamp bolt holes and hub end; tip deflection (expect ≈ 3.7 mm); pin shear τ ≈ 168 MPa at 100 N |
| R4 | Hub (6061-T6 Ø70 x 16 + tongue): model from barrier_params | 6061-T6: E 68.9 GPa, Rp 240 | Fixed on the keyway + bore faces | Moment 30 N·m (motor stall limit) as a force couple on the hinge and shear-pin bores | 1.5 mm | σ_vM at the keyway root and tongue fillet. Target ≤ 120 MPa. |
| R5 | Occupancy snap hook: `cad/stl/occ_cover.stl` → meshed via Mesh→Part, or rebuild the hook as a 12 x 10 x 1.6 cantilever | ASA: E 2.0 GPa, ν 0.35, design σ 25 MPa | Fixed at the hook root | Prescribed displacement 0.8 mm (snap-lip undercut) at the barb | 0.4 mm | Peak strain ≤ 1.5 % (ASA allowable for repeated snap). Report σ and ε_max. |
| R6 | Edge Node thermal (optional): enclosure shell + spreader + sink | PC: k 0.2 W/mK; 6061: k 167; 6063: k 200 | `ConstraintTemperature` none; `ConstraintHeatflux` convection h = 5 W/m²K, T∞ = 45 °C on all external faces except the back | `ConstraintHeatflux` / body heat 12 W on Pi/HAT pad faces, 6.6 W on the SMPS base | 5 mm | Temperature contour. Target: Hailo/SoC pad ≤ 70 °C, internal wall mean ≤ 55 °C. |

Workflow for each recipe:
1. Import the STEP (Part → Import).
2. Create the FEM Analysis and add the Material card from the table.
3. Add the constraints and loads. Label each one with the load-case name, e.g. "R1_wind_diag".
4. Run Gmsh (Tet10, sizes from the table, plus mesh regions).
5. Run CalculiX (static linear).
6. In the result object, use Colour → von Mises, scale 0 to Rp/2. Screenshot with the legend, then save the `.FCStd` beside the screenshot under `cad/fea/`.

---

## Assumptions and open items
- Wind assumes Terrain Category 2 at a 50-year return period, with all items face-on at once. Kd, Ka and Kc were set to 1 even where the code would allow reductions.
- The 80x80 profile section modulus is taken from one EU vendor's data. The Indian supplier's profile must provide W ≥ 27 cm³.
- The Mean Well efficiency at 30 % load is assumed to be 87 % (the LRS-150 figure, reused for the LRS-200-24; its curve was not opened). The PoE switch dissipation of 4 W is a class value.
- No dynamic, fatigue or impact calculation was made for vehicle strikes on the boom. The shear pin limits the force transmitted to about 100 N at the tip.
- The 80x80 profile: calcs use 5.4 kg/m and I = 109.9 cm4 (Wolweiss, reiman.pt). A second vendor (Systeal 80x80, 10 mm slot) lists 4.45 kg/m, A = 1649 mm2, I = 130 cm4; both are lighter than the STEP model (31.7 kg for 2.4 m, 4891 mm2), so the stress/FoS here uses the weaker I and is conservative. The Simplex 8080 listing in the BOM states neither weight nor section modulus: get the drawing.
- The 24 V bus peak with a 5 A motor limit is 7.66 A (87 % of the 8.8 A LRS-200-24; electronics/tools/power_model.py). A stalled wiper motor above 5 A is stopped by the firmware limit (placeholder threshold to be set at commissioning); the supply's overload behaviour must be confirmed on the bench.
- Every value is analytical. FEA (R1–R6) and the bench tests in the Stage 2 roadmap must confirm them before they are quoted as verified.
