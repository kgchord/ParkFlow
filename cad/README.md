# ParkFlow: CAD and Mechanical Package (Stage 2)

This package holds parametric OpenSCAD models (every dimension is a named variable in mm), renders, STL/DXF/STEP exports, hand calculations with FEM recipes, and a FreeCAD rebuild plan for a native parametric feature tree.

> **Key design change from our initial concept (Stage 1 does not specify a pole).** The gantry pole is an **80x80** 8-slot extrusion, not 40x40. At the Delhi basic wind speed Vb = 47 m/s (IS 875-3:2015), the hand calculation predicts a 40x40 pole reaches 239 MPa (FoS 0.46) and the 80x80 pole 51 MPa (FoS 2.15). Both are analytical predictions on 6063-T5 minimum properties; FEA and bench tests have not been run. See `calcs/CALCS.md` §1. The base plate is also 16 mm, not 10 mm.

## File index

```
cad/
├── openscad/                       parametric source (OpenSCAD 2021.01+)
│   ├── pf_common.scad              colour code + helpers (T-slot profile generator, bolts, glands)
│   ├── pf_bought.scad              bought-in envelopes: RFID reader 260x260x60, bullet cam 220x80x80,
│   │                               P10 320x160x15, Pi 5 85x56 + AI HAT+, LRS-150-24 159x97x30,
│   │                               PoE switch, Lane Controller 100x80, DIN rail, ESP32-C3, A02YYUW,
│   │                               WS2812 ring, worm gearmotor, photo-beam head, context car
│   ├── gantry_params.scad          (a) master parameters  ("GantryParams" spreadsheet)
│   ├── gantry_base_weldment.scad   (a) base plate + socket + gussets, anchors
│   ├── gantry_antenna_bracket.scad (a) 40x40 arm, bent yoke, tilt plate (0-30°), pivots
│   ├── gantry_camera_arm.scad      (a) camera arm + adapter plate, aimed camera
│   ├── gantry_channel_cap_sign.scad(a) cable channel, cable boot, pole cap, sign + Edge brackets
│   ├── gantry_assembly.scad        (a) ASSEMBLY   -D explode=0|1  -D section=0|1
│   ├── edge_params.scad            (b) parameters
│   ├── edge_enclosure.scad         (b) IP65 base (bosses, tongue, lugs, gland/vent/sink holes) + lid (gasket groove)
│   ├── edge_internals.scad         (b) mount plate, Pi tray, spreader, heat sink, sun hood, populated layout
│   ├── edge_node_assembly.scad     (b) ASSEMBLY   -D explode -D section -D show_hood
│   ├── barrier_params.scad         (c) parameters (boom_angle animatable)
│   ├── barrier_parts.scad          (c) housing, drive train, hub, carrier/shear pin, boom, counterweight, flag, posts
│   ├── barrier_assembly.scad       (c) ASSEMBLY   -D explode -D section -D boom_angle=0..90
│   ├── occupancy_params.scad       (d) parameters
│   ├── occupancy_parts.scad        (d) base, snap cover, diffuser
│   ├── occupancy_node_assembly.scad(d) ASSEMBLY   -D explode -D section
│   ├── lane_layout.scad            (e) 3.5 m x 8 m lane: all of the above + RFID zone + camera FOV + car
│   └── export_parts.scad           export driver (-D part="...")
├── renders/                        1920x1440 PNG (light background, orthographic iso)
│   ├── gantry_iso / gantry_exploded / gantry_detail_base / gantry_detail_antenna
│   ├── edge_node_iso / edge_node_exploded / edge_node_section
│   ├── barrier_iso / barrier_exploded / barrier_section / barrier_anim.gif (+ anim_frames/)
│   ├── occupancy_iso / occupancy_exploded / occupancy_section
│   └── lane_layout_iso / lane_layout_top / lane_layout_approach
├── stl/   pole_cap, cable_boot, edge_pi_tray, occ_base, occ_cover, occ_diffuser, boom_tip_cap, pb_post_cap
├── dxf/   base_plate, socket_cheek_long/short, gusset, antenna_yoke_flat, antenna_tilt_flat, camera_plate,
│          sign_bracket, edge_pole_bracket, edge_mount_plate, edge_heat_spreader, barrier_base_plate,
│          barrier_motor_plate, barrier_bearing_plate, barrier_front_panel, boom_carrier_plate,
│          limit_flag, photo_post_foot                        (1:1 mm, flat patterns for bent parts)
├── step/  build_step.py (CadQuery 2.8) -> base_weldment.step, antenna_yoke.step,
│          antenna_tilt_plate.step, antenna_bracket_assy.step   (valid single solids, AP214)
├── calcs/ calcs.py, calcs_results.txt, CALCS.md (wind, base plate, bracket, boom, torque, thermal, FEM recipes)
├── scripts/ render.sh, barrier_anim.py, export.sh
└── MATERIALS.md
```

Colour code in every render: **structure grey, electronics green, sensors blue, moving parts orange.** Section cut faces show in red.

## Regenerating

```bash
# renders (about 15 s) + barrier GIF (about 30 s); needs openscad + xvfb-run + Pillow
bash cad/scripts/render.sh            # or: bash cad/scripts/render.sh quick   (no GIF)
# STL + DXF
bash cad/scripts/export.sh
# STEP (needs: pip install --break-system-packages cadquery)
python3 cad/step/build_step.py
# calculations
python3 cad/calcs/calcs.py --md
# one-off view with overrides, e.g. exploded barrier with boom at 45 deg:
xvfb-run -a openscad -o out.png --imgsize=1920,1440 --colorscheme=Tomorrow \
  --camera=0,0,0,62,0,35,0 --viewall --autocenter --projection=o \
  -D explode=1 -D boom_angle=45 cad/openscad/barrier_assembly.scad
```

To change a design, edit the `*_params.scad` file and re-run the three scripts. Every dependent part, render and DXF updates with it. `calcs.py` and `build_step.py` carry the same variable names. Keep all three in sync, or better, move them into the FreeCAD spreadsheet described below.

## Modelling assumptions (bought-in envelopes)
- **RFID reader.** Integrated 865–867 MHz, assumed 260 x 260 x 60 mm, 3 kg, rear 100x100 M6 pattern. Re-check against the chosen reader's drawing.
- **ANPR bullet camera.** Envelope 220 x 80 x 80 mm incl. sun hood, base with 3 holes on a 60 mm PCD (assumed). The FOV cone assumes an 8–12 mm varifocal lens set to about 40° H x 24° V for about 150 px plate width at 4 m. The BOM camera (CP Plus CP-UNC-TD21ZL6C) is listed with a 2.7–13.5 mm motorised lens; its dimensions are not on the listing, so the envelope stays an assumption.
- **A02YYUW.** Physical dimensions are not published on the DFRobot wiki or product page. Modelled as Ø34 x 26 mm probe + 36 x 42 x 18 mm body. 60° beam, 3–450 cm range (wiki). **Measure the real part before printing the cover.**
- **Gearmotor.** Modelled as a 24 V worm gearmotor with a Ø12 shaft (assumed). The BOM part is a Lucas TVS wiper motor listed at 18 N·m; the calcs ask for ≥ 30 N·m, so the motor plate pattern and shaft diameter must be re-checked against the real part.
- **LRS-150-24.** 159 x 97 x 30 mm (datasheet). The 4x M4 base pattern is assumed as 150 x 50. **Check against the datasheet.**
- **PoE switch.** 140 x 105 x 40 DIN class. Worm gearmotor box 90x75x70 + Ø60x110 motor, Ø12 shaft, M6 on 70x50 (assumed).
- **Edge enclosure.** Generic 300x400x180 PC IP65 class, modelled with the features we specify (groove, bosses, lugs). The BOM currently buys a 300x300x210 GRASP box (25 Oct 2026): the model, the DIN layout and the thermal calculation (exposed area 0.372 m²) have not been re-done for it (0.342 m²).
- **RFID read zone.** Drawn as a 3.0 m wide x 2.5 m long x 1.8 m high box, 2.5–5 m ahead of the pole. This is a **target, to be bench-verified** with a real FASTag.

## FreeCAD Part Design rebuild plan (native parametric feature tree)

OpenSCAD is CSG-scripted. It has no sketch constraints, no feature history and no native B-rep. We want a parametric feature tree and native files, so the key parts are being rebuilt in **FreeCAD 1.0** (Part Design + Sheet Metal + Assembly workbenches). The rebuild steps are below. STEP files from `cad/step/` can be imported as a reference body (Part → Import, then `Std_LinkMake`) and used to check each rebuilt feature by overlay.

### 0. Master spreadsheet
1. Create `ParkFlow.FCStd`, then **Spreadsheet → Create** `GantryParams`. Make column A the names and column B the values. Copy **every variable from `gantry_params.scad` with exactly the same names** (`pole_w`, `bp_w`, `bp_t`, `bp_pcd`, `gus_h`, `yoke_t`, `ant_tilt`, …). Set the alias of each B cell equal to its name (select cell → Properties → Alias).
2. Do the same for `EdgeParams`, `BarrierParams` and `OccParams`, from the matching `*_params.scad` files.
3. Every sketch dimension, pad length and placement is then an expression, e.g. `=GantryParams.bp_t`. Nothing is typed as a literal.

### 1. Base weldment (Body `BaseWeldment`, Part Design, multi-feature single solid)
| # | Feature | Sketch / constraints | Expression links |
|---|---|---|---|
| 1 | `SkPlate` on XY | Centred rectangle (symmetric constraint to origin), equal sides, 4 corner fillets (Sketcher fillet, radius constraint) | width = `bp_w`, radius = `bp_corner_r` |
| 2 | `PadPlate` | Pad SkPlate | length = `bp_t` |
| 3 | `SkAnchorHoles` on plate top | 4 circles, centres on a construction circle (diameter constraint) at 45° (angle constraint), equal radii | construction Ø = `bp_pcd`, hole Ø = `bp_anchor_hole` |
| 4 | `PocketAnchors` | Through all | – |
| 5 | `HoleCentre` | Hole feature, centre | Ø = `bp_centre_hole` |
| 6 | `SkSocket` on plate top | Two concentric centred squares (outer/inner) | outer = `pole_w + 2*sock_clear + 2*sock_t`, inner = `pole_w + 2*sock_clear` |
| 7 | `PadSocket` | Pad | `sock_h` |
| 8 | `SkGusset` on XZ | Closed polyline: base on plate top, inner edge on socket face (coincident to external geometry), chamfer and tip lengths | `gus_l`, `gus_h`, `gus_chamfer`, `gus_tip` |
| 9 | `PadGusset` | Symmetric to plane | `gus_t` |
| 10 | `PolarPattern` | Gusset ×4 about Z | count = `gus_n` |
| 11 | `HoleCross1/2` | Hole features on the socket faces, through all | Ø = `sock_bolt_d + 1`, z = `sock_bolt_z1/2` |
| 12 | Chamfers (weld preps) | Optional 45° x 3 on the gusset contact edges | – |

**Laser parts.** For each plate/cheek/gusset, create a `TechDraw` page or use `Draft → Shape2DView` → **Export DXF** (compare with `cad/dxf/`).

### 2. Antenna yoke and tilt plate (Sheet Metal workbench, Body `AntennaYoke` / `TiltPlate`)
1. `SkYokeWeb` on XY: rectangle `yoke_w - 2*(yoke_t+yoke_bend_r)` x `yoke_web_d`, with 2 holes on the centreline at `web_hole_pitch`. Then **SheetMetal → Make Base Wall**, thickness `yoke_t`.
2. **Make Wall** on both short edges: 90°, bend radius `yoke_bend_r`, length = `pivot_drop - ant_arm_w/2 - yoke_t - yoke_bend_r`, relief none.
3. `SkCheek` on the cheek face:
   - Arc profile with a radius-45 bottom around a point `(0,-30)` from the pivot.
   - Pivot hole Ø `pivot_d + 0.5`.
   - Arc slot built from 2 concentric arcs (radius `lock_r ± lock_slot_w/2`), sweep angle `tilt_max`, tangent end arcs.
   - Pocket through both cheeks (mirror).
4. **SheetMetal → Unfold**, K-factor 0.40 (5052-H32, R = t), then export the flat DXF. It must match `cad/dxf/antenna_yoke_flat.dxf` (732 x 90 mm envelope).
5. Tilt plate: base wall `tp_w x tp_h`, two **Make Wall** ears (90°, R = `yoke_bend_r`, length `tp_off`). Then a sketch on each ear for the pivot hole and the M6 lock hole at `lock_r`, and a face sketch for the 4 reader holes at `reader_hole_pitch` plus the lightening slots.
6. Add a property `ant_tilt` to the assembly joint (below) so the tilt angle is driven from the spreadsheet.

### 3. Other Part Design bodies (same pattern: sketch → pad/pocket → pattern, all expressions)
- **Camera adapter plate.** Rectangle `cam_plate_l x cam_plate_w`, slot pair, 3-hole PCD `cam_mount_pcd` (polar pattern).
- **Edge Node.**
  - Mounting plate: holes driven by `bp_boss_dx/dy`, `smps_x/y`, `pi_x/y`, `lc_x/y`.
  - Enclosure base: Pad → Thickness (shell) `enc_wall` → bosses Pad.
  - Rim tongue: Pad from an offset sketch, `tongue_w x tongue_h`.
  - Lid: Groove via Pocket of an offset sketch, `groove_w x groove_d`.
  - Gland holes via Hole features driven by the `gland_x` list (one sketch per gland).
- **Hub.** Revolution of a half-section (`hub_d`, `hub_t`), tongue Pad, keyway Pocket, hinge/shear-pin Holes at `hinge_r`, `hinge_r + shear_e`.
- **Occupancy cover.**
  - Revolution of the profile (`oc_d`, `oc_cover_h`, spigot `lip_h`).
  - Snap hook: Pad of `snap_t x snap_w x snap_l`, plus a Chamfer for the barb, then Polar pattern ×`snap_n`.
  - Probe bore Hole `probe_d + 0.6`.

### 4. Assemblies (FreeCAD 1.0 Assembly workbench)
- **Gantry.**
  - Ground the `BaseWeldment` (Fixed joint).
  - Pole: *Fixed* joint to the socket bottom.
  - Antenna arm: *Slider* joint along the pole slot. Offset = `ant_z`, locked by a spreadsheet expression.
  - Yoke: *Fixed* to the arm end.
  - Tilt plate: *Revolute* about the pivot axis, angle = `GantryParams.ant_tilt`, limits `tilt_min..tilt_max`.
  - Camera arm: *Slider* at `cam_z`.
  - Sign and Edge Node: *Fixed*.
  - Use *Exploded View* (Assembly → Create Exploded View) for the exploded figure.
- **Barrier.**
  - Housing fixed.
  - Shaft–hub: *Revolute* angle = `BarrierParams.boom_angle` (0–90 limits).
  - Carrier: *Revolute* about the hinge, with a *Fixed* joint representing the shear pin. Delete it to demonstrate breakaway.
  - The Assembly → *Simulation* (FreeCAD 1.0) can drive `boom_angle` 0→90 to make the animation natively.
- **Edge Node and Occupancy.** Fixed joints only, plus an exploded view.
- **Lane layout.** Link the four sub-assemblies (`App::Link`) and place them with expressions from `LaneParams` (`lane_w`, `pole_y`, `bar_y`).

### 5. Outputs from FreeCAD
1. **STEP AP214** for every body and assembly: File → Export → `*.step`, written into `cad/step/` and overwriting the CadQuery versions once verified.
2. **Native files**: `cad/freecad/ParkFlow.FCStd` (one file with spreadsheets + bodies + assemblies), or one `.FCStd` per assembly linked to a shared `Params.FCStd`.
3. **TechDraw** drawings: a GA drawing per assembly with a balloon BOM, plus part drawings for the weldment (weld symbols, GD&T on the anchor PCD ±1 mm) and sheet parts (flat pattern + bend table).
4. **FEM**: run recipes R1–R6 from `calcs/CALCS.md` §6 on the rebuilt bodies. Save the analysis containers inside the same `.FCStd`.

### Feature-tree acceptance checklist
- [ ] Change `GantryParams.bp_t` from 16 to 12. The plate, socket base, gusset placement and DXF all update with no broken references.
- [ ] Change `ant_tilt` from 20 to 30. The assembly re-solves and the reader clears the cheeks.
- [ ] Change `pole_w` from 80 to 40. The socket and cap resize. (The calcs then flag FoS < 1.)
- [ ] Sheet-metal unfold reproduces the DXF flat sizes to within ±0.5 mm.

## Limitations
- The OpenSCAD models are packaging- and presentation-grade. Bought-in parts are envelopes, and the threads, welds and fillets are simplified.
- The STEP files are generated by CadQuery from the OpenSCAD parameters (`step/STEP_MANIFEST.md`); native FreeCAD files depend on the rebuild.
- FEA has been run in CalculiX for cases A to C (`fea/FEA.md`). Every stress, FoS, deflection, torque and temperature is still a prediction until bench tests confirm it.
