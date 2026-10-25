# FreeCAD 1.x rebuild guide - the five most important parts

Purpose: native parametric CAD for the key parts. The STEP files in `cad/step/` are script-generated interchange geometry and are **not** that. This guide sets out how we build the five key parts in FreeCAD 1.x Part Design, driven by spreadsheets whose cell names equal the OpenSCAD variable names.

**Status of this guide.** Not yet followed end to end in FreeCAD, and `make_spreadsheet.py` has not been run there either. Menu names follow FreeCAD 1.0 Part Design; if a button is named differently in your build, use the equivalent. Correct the text as the steps are tested. Every number comes from `cad/openscad/*_params.scad` or from the module bodies named in each part.

The finished FreeCAD files must contain **unsuppressed sketches** (the sketches stay visible in the tree, fully constrained, not hidden or suppressed), and **screenshots** (section 8 lists them). Importing the STEP files does not count as a rebuild.

## 0. One-time setup

1. File > New. Save as `cad/freecad/ParkFlow_<part>.FCStd` (one file per part keeps recomputes fast).
2. Macro > Macros... > create or open `cad/freecad/make_spreadsheet.py` > Execute. It creates the spreadsheets `GantryParams`, `BarrierParams`, `OccParams` (also `EdgeParams`, `LaneParams`). Column A is the name, B the value (alias set on B), C unit, D comment. Check that cell B of `bp_t` shows `16 mm` and that its alias is `bp_t`. If the macro errors, fix it or type the sheet by hand from the `.scad` file; the aliases are what matter.
3. Derived values (`sock_in`, `sock_long`, `web_top_above_pivot`, `bend_allow`) are spreadsheet formulas, for example `sock_in` = `=pole_w + 2 * sock_clear`. Do not type their results.
4. In every expression field reference a value as `<Sheet>.<alias>`, for example `GantryParams.bp_t`. Angles: `=45 deg`. If one object lives in a different document, use `<<ParkFlow_gantry>>#GantryParams.bp_t` or keep the parameter sheet in the part's own file.
5. Units: write lengths with the unit (`=16 mm`) so a unitless value is never mixed with a length. A "Unit mismatch" error nearly always means one cell lacks `mm` or `deg`.

Conventions used below: "constrain" means the sketch is fully constrained (solver shows 0 degrees of freedom, all geometry green) and every dimensional constraint carries a Name and an expression, not a typed number.

## Part 1 - Base weldment (`gantry_base_weldment.scad`, STEP `base_weldment`)

Reference volume: **1414.5 cm3** (STEP, matches the .scad within 0.1 %). Bbox 250 x 250 x 166 mm, origin at plate underside centre, +z up.

Body: `Body_Base`. Make the plate, socket cheeks and gussets as one fused Body (the .scad draws them as one union; weld beads are not modelled).

1. **Plate sketch** `SkPlate` on `XY_Plane`.
   - Centre rectangle, 2 construction symmetry constraints about the origin. Width and height `=GantryParams.bp_w`.
   - Fillet the four corners, radius `=GantryParams.bp_corner_r`, equal-radius constraint.
   - Circle at origin, diameter `=GantryParams.bp_centre_hole`.
   - Construction circle diameter `=GantryParams.bp_pcd` centred on the origin; one bolt-hole circle on it at 45 deg, diameter `=GantryParams.bp_anchor_hole`, centre constrained to the construction circle with an angle `=45 deg` from the x axis.
   - Pad `PadPlate`, length `=GantryParams.bp_t`.
2. **Anchor holes**: instead of drawing four circles, draw one in the sketch and later use a PolarPattern (step 6) on a Pocket. Either way all four must be on the 45/135/225/315 deg diagonals.
3. **Grout slots** (4 of them): the .scad cuts a 16 x 8 mm rectangle centred at radius `bp_pcd/2 - 40` on each 45 deg diagonal. The numbers 40, 16 and 8 are literals in the .scad module body, not parameters. Add three rows to `GantryParams` named `grout_slot_off` (=40 mm), `grout_slot_l` (=16 mm), `grout_slot_w` (=8 mm), and keep them in the `.scad` too so the two models stay equal. Sketch `SkGrout` on `XY_Plane`: a rectangle centred on the x axis at `=GantryParams.bp_pcd / 2 - GantryParams.grout_slot_off`, rotate the whole profile 45 deg (sketch Placement angle `=45 deg`) so its long side is radial. Pocket through all of the plate.
4. **Socket cheeks.** Socket inner span `GantryParams.sock_in` (81), outer long cheek length `GantryParams.sock_long` (93).
   - Sketch `SkCheekLong` on `XZ_Plane`, attachment offset in the sketch's normal direction so it sits at y = `sock_in/2 + sock_t/2`. Mind that the FreeCAD `XZ_Plane` normal points to -y; verify visually that the cheek lands at the +y face before you pad. Rectangle length `=GantryParams.sock_long`, height `=GantryParams.sock_h`, bottom edge on z = `GantryParams.bp_t` (set via the sketch AttachmentOffset z). Pad `PadCheekLong`, length `=GantryParams.sock_t`, "Symmetric to plane" so the thickness is centred.
   - Hole for the lower M10 cross bolt: circle diameter `=GantryParams.sock_bolt_d + 1 mm` at height `GantryParams.sock_bolt_z1` above the plate top. Pocket `PocketBolt1`.
   - Top relief notch: the .scad subtracts an ellipse of diameter 30 scaled 1:0.5 at the top of the long cheek. Draw an ellipse with major radius 15 mm, minor radius 7.5 mm, centred on the cheek top edge (literals from the module body; add `relief_d` = 30 mm as a spreadsheet row). Pocket through the cheek.
   - Mirror the cheek across the XZ plane with `Mirrored` (mirror plane `XZ_Plane`), giving the -y long cheek.
   - Short cheeks (on the +/-x faces): length `=GantryParams.sock_in`, hole diameter `sock_bolt_d + 1` at height `sock_bolt_z2`. Sketch on `YZ_Plane` (normal +x), offset `= GantryParams.sock_in / 2 + GantryParams.sock_t / 2`. Pad, hole pocket, mirror about `YZ_Plane`.
5. **Gusset.** Sketch `SkGusset` on `XZ_Plane` (so that u runs along x, v along z), polygon with these vertices in (u, v), measured from the socket outer face and the plate top: (0, `gus_chamfer`), (`gus_chamfer`, 0), (`gus_l`, 0), (`gus_l`, `gus_tip`), (`gus_tip`, `gus_h`), (0, `gus_h`). Use six lines, coincident endpoints, horizontal/vertical constraints on the three axis-parallel edges and named dimensional constraints with the expressions above. Place the sketch with AttachmentOffset x = `GantryParams.sock_long / 2`, z = `GantryParams.bp_t`. Pad `PadGusset`, length `=GantryParams.gus_t`, symmetric to plane.
6. **Patterns.**
   - `PolarPattern` of `PadGusset`: axis = the sketch normal of `SkPlate` (Z axis), angle 360 deg, occurrences `=GantryParams.gus_n`.
   - `PolarPattern` of the anchor-hole pocket: Z axis, 360 deg, 4 occurrences (the .scad uses 4, not a parameter; a row `anchor_n` = 4 is fine).
   - `PolarPattern` of the grout slot pocket: the same.
7. **Cross-check** (see section 7).

Do not add: weld beads, anchors, nuts. The .scad draws anchors and bolts as separate hardware, not part of this part.

## Part 2 - Antenna yoke (`gantry_antenna_bracket.scad`, STEP `antenna_yoke`)

Reference volume **250.3 cm3**, bbox 280 x 90 x 235 mm, origin on the pivot axis, x across the lane, z up. 5 mm 5052-H32. The STEP is a formed shape (web + two quarter-tube bends + two cheeks), matching the 3D module, not the flat pattern.

Derived sheet rows: `web_top_above_pivot` (=`pivot_drop - ant_arm_w / 2`, 160 mm), `cheek_r` (45), `cheek_bot_c` (-30), `cheek_x` (=`yoke_w / 2 - yoke_t`), `web_hole_pitch` (160). The last three are literals of the .scad.

1. Body `Body_Yoke`.
2. **Web.** Sketch `SkWeb` on `XY_Plane`, attachment offset z = `GantryParams.web_top_above_pivot - GantryParams.yoke_t`. Rectangle: x length `=GantryParams.yoke_w - 2*(GantryParams.yoke_t + GantryParams.yoke_bend_r)`, y length `=GantryParams.yoke_web_d`, centred on the origin. Pad `PadWeb`, length `=GantryParams.yoke_t`. Two M6 holes diameter 6.6 mm at x = +/- `web_hole_pitch/2`: Pocket `PocketWebHoles` through all.
3. **Bend.** Quarter tube radius inside `=GantryParams.yoke_bend_r`, outside `=yoke_bend_r + yoke_t`, width `=yoke_web_d`, centred at x = `yoke_w/2 - yoke_t - yoke_bend_r`, z = `web_top_above_pivot - yoke_t - yoke_bend_r`. Sketch `SkBend` on `XZ_Plane`: two concentric arcs, two radial lines closing the quarter, coincident constraints, radius expressions as above. Pad symmetric, length `=yoke_web_d`. (FreeCAD's Sheet Metal workbench is not needed; we keep Part Design so the numbers remain identical to the .scad.)
4. **Cheek outline.** Sketch `SkCheek` on `YZ_Plane`, attached at x = `GantryParams.yoke_w / 2 - GantryParams.yoke_t / 2`. The outline is the convex hull of (a) a rectangle `yoke_web_d` wide (y from `-yoke_web_d/2` to `+yoke_web_d/2`) and `web_top_above_pivot` tall starting at the pivot height (z from 0), and (b) the circle radius `cheek_r` centred at (0, `cheek_bot_c`). Because the circle is 90 mm wide and the rectangle only 60 mm wide, the hull is: the bottom arc of radius `cheek_r` about (0, `cheek_bot_c`), two straight lines tangent to that arc and ending at the rectangle's lower corners (+/-30, 0) (give them "Tangent" constraints to the arc and coincident endpoints), two vertical lines up the rectangle sides at y = +/- `yoke_web_d/2`, and a horizontal closing line at z = `web_top_above_pivot - yoke_t - yoke_bend_r` (the cheek is clipped there). Pivot hole: circle diameter `=GantryParams.pivot_d + 0.5 mm` at the origin. Pad `PadCheek`, length `=GantryParams.yoke_t`, symmetric to plane.
5. **Lock arc slot** (tilt lock, M6): an arc slot on radius `lock_r`, width `lock_slot_w`, sweeping from angle `tilt_min` to `tilt_max` measured from straight below the pivot (the .scad uses -90 + a). Sketch `SkLockSlot` on the cheek face: construction arc radius `=GantryParams.lock_r` about the pivot, from `-90 deg + tilt_min` to `-90 deg + tilt_max`; slot ends are circles of diameter `lock_slot_w`; the two long sides are arcs of radius `lock_r +/- lock_slot_w/2`. Pocket through the cheek.
6. **Scale notches** every 5 deg: a 5 x 0.8 mm rectangle at radius `lock_r + 9` rotated by -90 deg + a. Draw one, Pocket `PocketNotch` (depth through the cheek is what the .scad does; if you only want an etched mark, set depth 0.3 mm and record the difference). Pattern: `PolarPattern` about the pivot axis (X), angle `=GantryParams.tilt_max` (30 deg), 7 occurrences (0, 5, ... 30). 7 comes from `(tilt_max - tilt_min)/5 + 1`; add that as a formula row.
7. **Mirror** the cheek, the bend and the notches about `YZ_Plane` so both sides exist (`Mirrored`, plane `YZ_Plane`).
8. Cross-check section 7.

## Part 3 - Antenna tilt plate (STEP `antenna_tilt_plate`)

Reference volume **243.9 cm3**, bbox 240 x 61 x 200 mm. Origin on the pivot axis.

1. Body `Body_TiltPlate`.
2. Face sketch `SkFace` on `XZ_Plane`, attachment offset such that the rear face lies `GantryParams.tp_off` in front of (toward -y of) the pivot; FreeCAD's `XZ_Plane` normal is -y, so a positive offset along its normal moves toward -y. Rounded rectangle `=GantryParams.tp_w` by `=GantryParams.tp_h`, corner radius 8 mm (literal in the .scad `tilt_plate_face_2d`; name it `tp_corner_r`). Four holes diameter 6.6 mm on a square `=GantryParams.reader_hole_pitch` (use one circle, symmetric constraints, then a `LinearPattern` or four circles with symmetry constraints); a centre hole diameter 30 mm; two lightening slots 30 x 120 mm with corner radius 6 mm centred at x = +/-80 mm (literals; add `lighten_*` rows).
3. Pad `PadFace`, length `=GantryParams.yoke_t`, direction away from the pivot (check by looking at the bbox: y from -45 to +16 mm at the end of the build, from the STEP).
4. Ear sketch `SkEar` on `YZ_Plane` at x = `GantryParams.tp_w/2 - GantryParams.yoke_t/2`: hull of a thin vertical line at y = `-tp_off - yoke_t` (height `2*ear_half_h` = 100 mm), a circle radius 16 about the pivot, and a circle radius 10 about (0, -`lock_r`). Pivot hole diameter `=pivot_d + 0.3 mm`; lock hole 6.6 mm at (0, -`lock_r`). Pad `PadEar` length `=yoke_t` symmetric to plane; `Mirrored` about `YZ_Plane`.
5. The .scad has sharp bends (no inside radius, no bend allowance in the solid); the real part has R = t. Model the sharp version first to match the volume check, then add a fillet of radius `=GantryParams.yoke_bend_r` on the inside corner if the team wants the formed shape, and record the volume change.

## Part 4 - Barrier hub (`barrier_parts.scad`, STEP `barrier_hub`)

Reference volume **99.81 cm3**, bbox 135 x 70 x 16 mm (6061-T6). Local frame: shaft axis = z, hub centred on z = 0, tongue pointing +x.

1. Body `Body_Hub`.
2. `SkHub` on `XY_Plane`: circle diameter `=BarrierParams.hub_d`. Pad symmetric to plane, length `=BarrierParams.hub_t`.
3. `SkTongue` on `XY_Plane`: rectangle from x = 0 to x = `=BarrierParams.tongue_l + BarrierParams.hinge_r - 25 mm` (the literal 25 from the module body; add row `tongue_trim` = 25 mm), y = +/- `tongue_w/2`. Pad symmetric, length `=BarrierParams.tongue_t`.
4. `SkTail` (counterweight tail stub, -x): rectangle x from `-hub_d/2 - 10` to `-hub_d/2 + 20`, y width `cw_bar_w`, thickness `cw_bar_t`, symmetric pad. (`cw_bar_w`, `cw_bar_t` live in `BarrierParams`. The 10 and 30 are literals of the module body.)
5. Bores:
   - Shaft bore: circle diameter `=BarrierParams.shaft_d + 0.05 mm`, Pocket through all (axis z).
   - Hinge bore: sketch on `XZ_Plane`, circle diameter `=BarrierParams.hinge_d + 0.2 mm` at x = `hinge_r`, Pocket through all, symmetric. It runs along y.
   - Shear pin bore: same plane, x = `=hinge_r + shear_e`, diameter `=shear_d + 0.1 mm`.
6. Keyway: rectangle 6 mm wide, 4 mm high at y from `shaft_d/2 - 1`; pocket through all. 6 and 4 are literals in the module body (add `key_w`, `key_h` rows).

## Part 5 - Occupancy sensor cover shell (`occupancy_parts.scad`, STEP `occ_cover`)

This part is a revolve. **Warning: the .scad module `oc_cover()` produces three disconnected solids** (the shell, a probe clamp boss, and an LED seat that are only positioned, never joined to the shell). The STEP exports them as `occ_cover`, `occ_probe_clamp_boss` and `occ_led_seat`. Before you build this part, fix the geometry decision with the team: either (a) extend the shell wall to connect the boss and seat (a design change; record it), or (b) model three separate bodies as the .scad does. This guide builds the shell.

Reference volume of the shell **42.54 cm3** (shell + boss + seat = 48.6 cm3, which is also the checked-in `cad/stl/occ_cover.stl`). Origin on the cover axis; the spigot extends to z = -5 and the hooks to z = -12.

1. Body `Body_Cover`. Derived values in `OccParams`: `ri` = `=oc_d / 2 - oc_wall` (45.6), `sp_o` = `=ri - fit_clear` (45.35).
2. **Revolve sketch** `SkCoverSection` on `XZ_Plane` (x = radius, z = height). Closed polygon, in (r, z):
   (27, 23) > (`sp_o - oc_wall`, 23) > (`sp_o - oc_wall`, `-lip_h`) > (`sp_o`, `-lip_h`) > (`sp_o`, 0) > (`oc_d/2`, 0) > (`oc_d/2`, `oc_cover_h - 8`) > (`oc_d/2 - 8`, `oc_cover_h`) > (27, `oc_cover_h`) > back to (27, 23).
   The 23 is `oc_cover_h - 3` and 27 is `ring_od/2 + 2` (the LED window radius). Name the constraints with those expressions. Constrain the three horizontal and four vertical lines, and the dome line by two dimensions.
3. `Revolution` about the sketch's vertical axis (V_Axis), 360 deg.
4. **Probe bore**: not needed in the shell, because the window radius 27 is larger than the bore radius (`probe_d + 0.6)/2` = 17.3). Check that statement with the volume test; if your volume is off, the bore is the first suspect.
5. **Snap hooks.** Cantilever: box `snap_t` x `snap_w` x `snap_l`, located at radius `sp_o - snap_t`, running from z = `-snap_l` to z = 0 (as the .scad). Barb: hull of a `snap_w` x 0.01 x 2.2 slab and a slab at +2.2 mm, projecting `snap_lip` outward at z = `-lip_h + 0.5 - 2`. Sketch the hook profile in the XZ plane at the 90 deg position, Pad symmetric by `snap_w`. `PolarPattern` about the Z axis, `=OccParams.snap_n` occurrences, 360 deg, starting at 90 deg (rotate the first sketch by 90 deg).
6. **Relief slots** around each hook: boxes 1.2 mm wide, `snap_l` long, at offset `snap_w/2 + 0.6`, Pocket, patterned with the hooks.

## 6. Naming checklist (all parts)

Spreadsheet aliases are the .scad names exactly (case sensitive). If you need a number that is only a literal in the .scad (listed in each part above), first add it to the sheet and to the `.scad` file, then reference it. Do not leave a typed number in a constraint.

## 7. Acceptance tests (each part)

- Sketch solver: 0 DoF, no red or orange constraints; no sketch suppressed or hidden-as-deleted.
- Recompute with no errors; change `bp_t` from 16 to 12 (weldment), `yoke_w` from 280 to 300 (yoke), `hub_d` from 70 to 80, `oc_d` from 96 to 100: the model follows without a broken sketch. Change it back.
- Volume at the default parameters: weldment 1414.5 cm3, yoke 250.3, tilt plate 243.9, hub 99.81, cover shell 42.54 (tolerance 1 %). In FreeCAD, select the Body, Part > Check Geometry, tick "Shape content", read Volume. Differences over 1 % mean a missing feature; do not tune a parameter to hit a number.
- Bounding box equals the one stated for the part.
- Part > Check Geometry reports no errors.
- Optional: Export as STEP and compare with the file in `cad/step/` with `python3 cad/step/verify_step.py --only=<id> --no-ref` (needs CadQuery).

## 8. Screenshots to take

For each of the five parts: (1) the Model tree with all features and the sketches visible; (2) each main sketch with the constraints shown, and the solver message "Fully constrained"; (3) the spreadsheet with aliases; (4) a recompute after changing one parameter (before and after); (5) the Check Geometry volume result. Save under `cad/renders/` or `cad/freecad/screens/` with the date in the file name.

## 9. Troubleshooting

- "Unknown identifier" in an expression: the sheet name or alias is mistyped, or the sheet is in another document.
- "Unit mismatch": add `mm` or `deg` to the spreadsheet cell or the formula term.
- Pad goes the wrong way: reverse in the Pad dialog; do not flip the sketch.
- `XZ_Plane` normal points to -y and `YZ_Plane` normal to +x. Several offsets above depend on this; check the first feature visually.
- Pocket leaves a skin: use "Through all" with both directions rather than a length.
- Toponaming: avoid Fillet or Chamfer on edges chosen by clicking; put the fillet radii in the sketches where possible.
