# ParkFlow Demo Lane: Materials, Processes and Mass Estimates

Each mass is an analytical volume × density from `calcs/calcs.py`, section 6. Every factor of safety quoted below is an **analytical prediction** from `calcs/CALCS.md` (hand calculation, no FEA run yet), not a test result. For the base weldment, the CadQuery B-rep volume (1424.8 cm³ × 7850 kg/m³ = 11.2 kg) agrees with the analytical sum of 11.24 kg. Bought-in items carry vendor or class masses and are marked "(est.)".

All fabrication is chosen to fit a student lab: a laser-cut job shop (MS up to 16 mm, Al up to 6 mm), press brake, MIG welding, a drill press, FDM printers with an enclosed chamber for ASA, and M5/M6/M8/M12 hardware.

## (a) Lane gantry pole

| Part | Material | Process | Mass (kg) | Rationale |
|---|---|---|---|---|
| Pole 80x80 8-slot, L 2400 | Al 6063-T5 (T6 preferred) | Bought extrusion, saw cut, end-tapped M10 | 12.96 (vendor-basis; range 10.7 to 13.0) | Calcs predict 40x40 fails at Delhi wind (FoS 0.46). 80x80 is predicted to give FoS 2.15 on 6063-T5 minimum properties. **Mass basis reconciled 25 Oct:** 5.4 kg/m (calcs; I = 109.9 cm⁴, Wolweiss) gives 12.96 kg; Systeal's 80x80/10 mm-slot lists 4.45 kg/m, 1649 mm², I = 130 cm⁴ (10.7 kg). The STEP model weighs 31.7 kg because its generic T-slot is 4891 mm² (76 % of the 80x80 envelope), not a vendor section; see the reconciliation section below. The Simplex 8080 listing in the BOM gives no weight or section modulus: get the drawing and confirm W ≥ 27 cm³. |
| Base plate 250x250x16 | MS IS 2062 E250 | Laser cut (DXF `base_plate`), drilled | 7.68 | 16 mm needed for FoS 2.89 with no gusset credit. MS is weldable, cheap and available everywhere. |
| Socket cheeks 2×93x150 + 2×81x150, 6 mm | MS E250 | Laser cut, MIG 6 mm fillet | 2.43 | Socket carries the moment into the plate as a bearing couple (8.8 MPa). The pole can be removed without welding the Al. |
| Gussets 4× 74x120x6 | MS E250 | Laser cut, MIG | 1.13 | Stiffen the plate edges; stress 19.5 MPa, FoS 12.8. |
| Weldment finish | Hot-dip galvanising (IS 4759) or zinc primer + 2-pack PU | Job shop | – | Corrosion protection for an outdoor parking lot (C3 environment). |
| Anchors 4× M12 chemical studs, 8.8, hef ≥ 110 | Zinc-plated steel + epoxy resin | Drill, inject | 0.6 (est.) | Design tension 7.39 kN, FoS 7.3 in the bolt. Resin anchor has small edge distances. |
| Antenna arm 40x40, L 350 | Al 6063-T5 | Saw cut | 0.53 | 10.6 MPa, FoS 10.4. |
| Antenna yoke, 5 mm (2 bends) | Al 5052-H32 | Laser cut + press brake (R = t, K 0.40) | 0.44 | 5052 bends at R = t without cracking (6061-T6 would crack). FoS 12.4. |
| Antenna tilt plate, 5 mm (2 bends) | Al 5052-H32 | Laser + brake | 0.64 | 0–30° tilt with a laser-etched 5° scale. |
| Camera arm 40x40, L 250 + adapter plate 5 mm | Al 6063-T5 / 5052-H32 | Saw / laser | 0.58 | Slotted plate gives 30 mm fore-aft adjustment; ball joint gives 15–25° pitch. |
| Sign brackets 2× 3 mm | Al 5052-H32 | Laser + Z-bend | 0.26 | Light payload (P10 cabinet ≈ 2.5 kg). |
| Edge Node pole brackets 2× 340x50x3 | MS E250, galvanised | Laser | 0.80 | Clamp the 9 kg enclosure via M8 T-nuts. |
| Pole cap | ASA | FDM, 0.2 mm, 4 walls, 30 % gyroid | 0.07 (STL volume 69 cm³) | UV-stable. Drip slope sheds water; ribs clip into the slots. |
| Cable boot | ASA | FDM | 0.10 | Transition from flexible conduit to trunking. |
| Cable channel 40x25 | PVC trunking (UV-stabilised) | Bought, cut | 0.5 (est.) | Off-the-shelf part. |
| **Gantry structural subtotal** | | | **≈ 28.7** (sum of the rows above; was printed as 28.4) | Excludes reader, camera, sign and Edge Node. |

## (b) Edge Node

| Part | Material | Process | Mass (kg) | Rationale |
|---|---|---|---|---|
| Enclosure IP65 (**BOM part: GRASP 300x300x210**; CAD/STEP still models 300x400x180) | Polycarbonate (UL94 V-0/V-2, UV-stabilised) | Bought, CNC/drilled glands + sink window | 2.6 (est.) | RF-transparent, non-conductive, IP65/66 rated. Thermal calcs now use the bought 300x300x210 (0.342 m²); CAD layout and sink window must be re-checked in it (docs/OPEN_DECISIONS.md D6). |
| Gasket | EPDM/silicone cord, Ø4.5 | Bought | 0.02 | 25 % compression on a 3 mm tongue. |
| Mounting plate 260x360x3 | Al 5052-H32 | Laser cut (DXF `edge_mount_plate`) | 0.75 | Flat, conductive ground plane; also spreads heat. |
| Heat spreader 100x70x5 + bar | Al 6061-T6 | Laser/saw + drill | 0.14 | k ≈ 167 W/mK. Carries 9.6 W from the Pi and HAT to the wall. |
| External heat sink 200x150, 18 fins | Al 6063-T5 extruded sink | Bought, cut, drilled | 1.00 | 0.219 m² of fin area against 0.152 m² required. Keeps the box at IP65 with no fan. |
| Sink window gasket | EPDM sheet 1.5 mm | Die/laser cut | 0.01 | Seals the 160x110 cut-out. |
| Pi tray | ASA (or PETG indoors) | FDM, M2.5 heat-set inserts | 0.02 | Isolates the Pi from the plate and sets standoff height to suit the spreader. |
| Sun hood | Al 5052-H32, 2 mm | Laser + brake | 0.9 (est.) | Cuts about 34 W of solar gain by roughly 80 %. |
| Glands M25/M20×3/M16 + ePTFE vent | Nylon PA66, IP68 | Bought | 0.15 | Pressure equalisation prevents gasket pumping. |
| Pole brackets (see a) | MS | – | – | – |
| Electronics (Pi 5, HAT, PoE switch, buck, DIN items, PCB, IBT-2 module; the 24 V supply is no longer inside) | – | Bought | ≈ 1.8 (est.) | – |
| Separate power box (plastic 250x190x95) with LRS-200-24, LRS-100-12, MCBs, RCCB, SPD, 12 V mini UPS | PVC/ABS box + bought devices | Bought | ≈ 1.2 for the box and DIN gear (est.; vendor masses not checked) | Moves 9.6 W out of the Edge box (CALCS §5). Mounted on the pole base, shaded. Not yet in the CAD. |
| **Edge Node total** | | | **≈ 8.2** (7.4 from the rows above + 0.8 kg pole brackets listed under (a); excludes the separate power box) | CALCS keeps 9 kg for the wind/eccentricity calcs (conservative). |

## (c) Demo boom barrier

| Part | Material | Process | Mass (kg) | Rationale |
|---|---|---|---|---|
| Base plate 360x310x8 | MS E250 | Laser | 4.71 | Four M10 anchors or 4 sandbags for the indoor demo. |
| Frame 20x20 (4 posts + 8 rails) | Al 6063-T5 | Saw, M5 T-nuts | 2.07 | Fast build; panels screw onto the slots. |
| Skins 2 mm, roof 3 mm (5° fall) | Al 5052-H32, powder-coated | Laser + brake | 5.12 | Weather and finger protection over the drive. |
| Motor plate 200x150x6 / bearing plate | Al 6061-T6 | Laser + drill | 0.49 + 0.3 | Rigid mount for the gearmotor (18 N·m demo motor now; a 30 N·m production motor needs the plate re-checked). |
| Stub shaft Ø20 | EN8 (080M40) steel | Lathe, 6 mm keyway | 0.3 | Two UCFL204 flange bearings take the boom moment off the gearbox. |
| Hub Ø70 + tongue | Al 6061-T6 | Lathe/mill, keyed + M8 clamp | 0.31 | Carries the hinge and shear pin. |
| Carrier plates 2× 5 mm | Al 6061-T6 | Laser + ream | 0.30 | Clevis for the breakaway hinge (M8 shoulder bolt). |
| Shear pin Ø5 | Al 6061-T6 rod | Cut to length (sacrificial) | 0.002 | Predicted to break at about 104 N at the tip, to protect vehicle and gearbox (to be tested). Spares are cheap. |
| Boom 60x30x1.5, L 1135 | Al 6063-T5, red/white reflective tape | Saw | 0.85 | 16.2 MPa, FoS 6.8, 3.7 mm deflection, light (low inertia). |
| Boom tip cap | ASA, red | FDM | 0.06 | Soft nose. |
| Counterweight 7× 100x60x10 | MS (painted orange) | Saw/laser | 3.30 (7 × 0.471 kg) | **Adopted: 7 plates, 94 % balance** (CALCS §4 now uses the installed value; required for 85 % is 2.98 kg, 6 plates would be 81 %). With the motor unpowered the boom can only close, with 0.34 N at the tip. The STEP tail bar adds 0.74 kg (CAD counterweight 3.94 kg including it); the tail bar's moment is not in CALCS. |
| Limit flag 3 mm + 2 ME-8108 roller limit switches (NC) | Al 5052 / bought | Laser | 0.04 | **Decision 25 Oct: the BOM roller switches are kept** (NC wiring is what the schematic J5 expects); the M12 inductive sensors are dropped. Flag geometry in the CAD must be checked against the roller. |
| Photo-beam posts 2× 20x20x450 + 100x100x5 feet | Al 6063 / MS | Saw / laser | 1.24 | Beam at 300 mm per the safety spec. |
| Gearmotor 24 V worm (BOM: Lucas TVS wiper motor, listed 18 N·m) | – | Bought | ≈ 2.5 (est.) | Demo motor, rated for ≤ 12 m/s operating wind (CALCS §4). Self-locking is **not** assumed. Production: ≥ 30 N·m self-locking (OPEN_DECISIONS D1). |
| Storm-lock pin Ø10 MS + manual-release pin (lanyard) | MS / SS | Bought/turned | 0.05 (est.) | Holds the boom against the 93 N·m survival gust; manual release if power is lost. Not yet in the CAD. |
| **Barrier total** | | | **≈ 21.7** (sum of the rows above with 7 counterweight plates; was printed as ≈ 24) | |

## (d) Occupancy node (×4)

| Part | Material | Process | Mass (g) | Rationale |
|---|---|---|---|---|
| Base (ceiling plate) Ø96 | ASA | FDM, no supports (STL `occ_base`, 34.8 cm³) | 37 | Basement carparks run humid and warm. ASA (Tg ≈ 100 °C) is chosen over PLA. |
| Cover with 3 snap hooks | ASA | FDM, rim down (STL `occ_cover`, 48.6 cm³) | 52 | 1.6 mm cantilever, 0.8 mm undercut, about 1.5 % strain (R5 recipe). |
| Diffuser ring | Natural PETG | FDM, 1.2–3 mm | 5 | Diffuses the WS2812 ring for bay status. |
| Electronics | ESP32-C3, A02YYUW, WS2812 ring | Bought | 35 (est.) | – |
| **Node total** | | | **≈ 130 g** | Two M5 screws into the slab. |

## Density basis
Steel 7850, aluminium 2680–2700, ASA 1070, PETG 1270 kg/m³. FDM masses use the solid STL volume; with 30 % infill the real print is about 15–25 % lighter.

## Reconciliation with `cad/step/STEP_MANIFEST.md` (25 Oct 2026)

The STEP manifest multiplies each STEP volume by the density used here and flags rows that differ by more than 5 %. Rule adopted: **the analytical masses in this file stay the basis for the wind and eccentricity calculations (CALCS), and the STEP mass is quoted beside them; where the STEP geometry is simply more detailed than the hand estimate, the STEP value is the better number.** Nothing in `cad/` was edited.

| Part | This file (kg) | STEP (kg) | Cause | Number to use |
|---|---:|---:|---|---|
| **Pole 80x80 x 2400** | 12.96 | **31.69** | STEP section is 4891 mm² (76 % of the 6400 mm² envelope); vendor sections are 1649 mm² (Systeal, 4.45 kg/m, 10.7 kg) to about 2000 mm² (5.4 kg/m, 12.96 kg). The CAD profile is a generic T-slot, not a vendor section | **12.96** (conservative; confirm with the Simplex drawing). The 31.7 kg is not a real mass and the CAD profile is also stiffer than a real one (I from a 4891 mm² section), so any model built on it overstates pole stiffness: the FEA owner should apply I = 109.9 cm⁴ (CALCS R1) |
| Antenna arm 40x40 x 350 | 0.53 | 0.85 | analytical used 1.5 kg/m, STEP section is heavier (2.43 kg/m) | 0.85 until the vendor drawing is seen (4040 "light" is 1.2 kg/m per the BOM listing, 0.42 kg) |
| Antenna yoke 5 mm | 0.44 | 0.67 | hand flat-area estimate misses the bend flanges | 0.67 (STEP) |
| Camera arm + adapter | 0.58 | 0.73 | arm length 250 vs 300 mm label; heavier section | 0.73 (STEP) |
| Pole cap | 0.07 | 0.074 | +6 %, rounding | either |
| Heat spreader + bar | 0.14 | 0.105 | bar length in the .scad is shorter | 0.105 (STEP) |
| Heat sink | 1.00 | 1.17 | fin thickness/base in the .scad | 1.17 (STEP) |
| Pi tray, sun hood | 0.02 / 0.90 | 0.022 / 0.946 | +10 % / +5 % | STEP |
| Barrier base plate | 4.71 | 6.90 | the hand estimate used 300x250x8; STEP uses the 360x310x8 plate named in the BOM | **6.90 (STEP)** |
| Barrier frame / skins | 2.07 / 5.12 | 2.71 / 5.43 | 0.5 kg/m assumed for the 20x20 vs the STEP profile; skin areas | STEP |
| Bearing plate, stub shaft, hub | 0.30 / 0.30 / 0.31 | 0.41 / 0.39 / 0.27 | detail | STEP |
| Boom 60x30x1.5 | 0.85 (L 1135) | 0.75 (L 1065) | tube length excludes hinge length in STEP | 0.75 for the tube; CALCS keeps 0.85 + 0.15 fittings (conservative) |
| **Counterweight** | 3.30 (plates) | 3.94 (plates 3.20 + tail bar 0.74) | the tail bar is not in the hand calculation | 3.94 as modelled; CALCS balance uses plates only (94 %); the tail bar adds a few percent of balance: **bench-check that the boom stays boom-heavy** (balance < 100 %) |
| Limit flag | 0.04 | 0.009 | one flag modelled | STEP |
| Occupancy cover | 0.052 | 0.046 | cover shell only in STEP | either |
| Edge Node total | printed 9 | 8.09 (own rows) | rounding up | 8.2 here (7.4 + 0.8 pole brackets), see (b) |
| Barrier total | printed 24 | 21.27 (own rows) | rounding up | 21.7 here, see (c) |

Gantry structural mass on the STEP basis would be 28.7 − 12.96 + 31.69 = 47.4 kg; on the vendor-section basis about 26.4 to 28.7 kg. The calcs use the vendor-section basis.

## Open mismatches with the BOM (updated 25 Oct 2026, design update)

| Item here | What the BOM buys | Status |
|---|---|---|
| Enclosure 300x400x180 PC in CAD/STEP | GRASP 300x300x210 (0.342 m²) | **Decided:** thermal calcs use the bought box (CALCS §5); box size is not the lever (0.6 K). CAD layout, DIN rail and sink window in 300x300x210 still to be re-checked by the CAD owner (OPEN_DECISIONS D6) |
| External heat sink, sun hood, ePTFE vent, M25/M20/M16 glands | Listed as GAP lines; BOM glands are PG-9 and PG-11 brass | Still unpriced estimates (no usable vendor page found); the thermal result does not pass without the sink and hood |
| 24 V supply inside the Edge box | Moved to a separate power box (plastic 250x190x95, priced from an IndiaMART listing) | **Decided**, not in CAD yet |
| ASA for pole cap, cable boot, Pi tray, tip cap, occupancy nodes | PETG 1.75 mm only (ASA not found at an allowed seller) | Open: source ASA or accept PETG (OPEN_DECISIONS D10) |
| Gearmotor ≥ 30 N·m, self-locking | Lucas TVS wiper motor, 18 N·m, self-locking not stated | **Decided for the demo:** keep 18 N·m with a ≤ 12 m/s operating-wind rule and a storm-lock pin; ≥ 30 N·m motor is an open production item (D1) |
| 2 M12 inductive limit sensors | 2 ME-8108 roller limit switches | **Decided:** roller switches (NC), M12 sensors dropped |
| Barrier housing, UCFL204 bearings, stub shaft, hub, carrier plates | Bearings now priced (Chennai listing); housing, shaft, hub, plates are estimate ranges | Housing/hub/shaft/plates still need a fabricator quote |
| Base plate MS 250x250x16 + MS gussets and socket cheeks | Laser-cut lines are estimate ranges | Re-quote |
| Storm-lock pin, manual-release pin | New BOM estimate line | Not in CAD |
