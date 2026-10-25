# CAD status

What exists in `cad/`, how far it has been checked, and what is still to do.

## Summary

* The `.step` files in `cad/step/` are **script-generated interchange files** (CadQuery/OCCT, from the numbers in the OpenSCAD `*_params.scad`). They have no sketches, constraints or feature tree.
* The native parametric models are being rebuilt in FreeCAD following `cad/freecad/REBUILD_GUIDE.md`, saved as `.FCStd` files with unsuppressed sketches.
* `cad/freecad/make_spreadsheet.py` and the rebuild guide have **not yet been run in FreeCAD**.

## Done (by script)

| Item | Where | State |
|---|---|---|
| STEP for every fabricated part and every assembly | `cad/step/*.step` (89 part files + 16 assembly files) | Generated; re-imported with CadQuery from disk; all solids valid |
| Bought-in parts as simplified solids | `cad/step/*_envelope.step` | Sizes are the assumed sizes from `pf_bought.scad`; not vendor geometry |
| Dimensions read from the .scad files | `cad/step/scadparams.py` | No dimension typed twice, except literals listed in the manifest "Limitations" |
| Validation against OpenSCAD | `cad/step/verify_step.py`, `_verify_results.json` | Volume, bbox, surface distance, overlaps |
| Mass vs MATERIALS.md | `cad/step/STEP_MANIFEST.md` | Disagreements listed |
| FreeCAD spreadsheet macro | `cad/freecad/make_spreadsheet.py`, `gen_param_tables.py` | Written; syntax and aliases checked in plain Python only; not yet run in FreeCAD |
| FreeCAD rebuild instructions, 5 parts | `cad/freecad/REBUILD_GUIDE.md` | Written; not yet followed in FreeCAD |

Re-run: `python3 cad/step/build_step.py`, then `python3 cad/step/verify_step.py` (needs `openscad`, CadQuery, trimesh, scipy), then `python3 cad/step/manifest.py`.

## Validation result

* 105 files; all valid solids. Part files agree with the OpenSCAD STL within about 0.1 % volume (largest: boom tip cap -0.79 %, Pi tray +0.41 %); surface agreement about 100 %.
* Outside the 2 % rule or bbox rule (all explained in `STEP_MANIFEST.md`): assemblies whose OpenSCAD reference also draws bolts, studs, anchors, decals or tape (`gantry_antenna_arm_assy`, `gantry_assembly`, `barrier_rotor_assy` -3.2 %, `barrier_photo_post_assy`, `barrier_assembly`, `occupancy_node_assy`, `lane_layout_assy`), and `occ_cover` vs the checked-in STL (the .scad cover is three disconnected solids).
* The first four STEP files were regenerated; they had differed from the .scad (yoke cheek outline, slot direction, missing grout slots and notches). The weldment is now 1414.5 cm3, not the 1424.8 cm3 quoted in MATERIALS.md.

## Open problems in the model

1. **Pole mass.** The .scad T-slot profile gives 31.7 kg for the 80x80 pole; MATERIALS.md uses 12.96 kg (vendor 5.4 kg/m, "rough"). The real section has to come from the supplier drawing; the wind calc uses W = 27.5 cm3. Update 25 Oct: the Systeal listing gives 4.45 kg/m, 1649 mm2, I = 130 cm4 (about 10.7 kg); the STEP uses a generic 4891 mm2 section (31.7 kg, 76 % of the envelope), so the CAD pole is not a real mass and is stiffer than a real one. MATERIALS.md keeps 12.96 kg (range 10.7 to 13.0). Owner: CAD/FEA (OPEN_DECISIONS D6). Also still modelled: enclosure 300x400x180 (bought box 300x300x210), no power box, no storm-lock pin.
2. **Disagreements over 5 %** between CAD mass and MATERIALS.md on many rows (arms, yoke, barrier base plate, frame, bearing plate, shaft, counterweight, hub, boom and others) and in the stated Edge Node (-10 %) and barrier (-11 %) totals. See the tables in `STEP_MANIFEST.md`. Not yet decided which side is right.
3. **Occupancy cover:** `oc_cover()` yields three disconnected solids (shell, probe clamp boss, LED seat). Fix the .scad, then regenerate.
4. **Occupancy base:** the keyhole counterbore leaves an enclosed void.
5. **Overlapping solids in the .scad** (DIN devices wider than their pitch, SMPS vs wire trunking, front panel inside the frame): listed in the manifest; they are real in the STEP assemblies.
6. MATERIALS.md says ASA parts are PETG at the allowed seller; PC and EPDM have no density, so no mass is computed.

## To do

1. Install FreeCAD 1.x; run `make_spreadsheet.py`; fix it if it fails; commit the corrected macro.
2. Build the five parts natively (weldment, antenna yoke, tilt plate, barrier hub, occupancy cover) per the guide, with fully constrained, unsuppressed sketches and spreadsheet-driven dimensions. Build the other fabricated parts the same way or mark them as exchange-only.
3. Take screenshots (list in the guide, section 8) and commit the `.FCStd` files.
4. Replace every `*_envelope` with dimensions from the actual purchased part's drawing (Pi, switch, SMPS, camera, reader, gearmotor, bearings, heat sink).
5. Decide the pole section, resolve the MATERIALS.md vs CAD mass disagreements, and fix the .scad flaws above.
6. Model what the STEP files omit: fasteners, anchors, bends with real radii (sign bracket and tilt plate are flat or sharp), the unbent sun hood, vendor T-slot sections.
7. Run the FEA (`cad/fea/`) on the corrected geometry.
