# ParkFlow finite-element evidence (Vishwakarma Stage 2)

Everything in this file comes from runs executed in this folder (`scripts/run_all.sh` reproduces them; about 2 h on 2 cores).

**Solver:** CalculiX ccx 2.21 (SPOOLES, 2 cores). **Mesher:** gmsh 4.15 (OpenCASCADE kernel) on the STEP files; 10-node tetrahedra (C3D10) for cases A and B, 8-node shells (S8) for case C. Own Python deck writer (`scripts/fea_lib.py`), post-processing in numpy, pictures in pyvista.

**Geometry and loads checked against the repo as it stands now.** The STEP files in `cad/step/` (base_weldment, antenna_yoke, antenna_tilt_plate, antenna_bracket_assy, barrier_boom_tube, barrier_hub, ...) were byte-compared with the snapshot used (`models/repo_step_snapshot`, hashes in `SHA256SUMS.txt`) after the last design-doc changes: identical. Pole 80x80 (I = 109.9 cm4), base plate 16 mm E250, loads = `calcs.pole_case(47, "80x80")`: 1053 N total wind, 1404 N.m design base moment (CALCS section 1). The 12 mm plate is only a sensitivity run. No barrier STEP geometry other than the tube/hub was used; the boom is a simplified shell model (see below).

## Results

| Case | Load | Max vM [MPa] (design reading) | FoS = Rp0.2/vM | Max defl [mm] | Elements | Solver |
|---|---|---|---|---|---|---|
| A1 pole+base, wind on face | IS 875 gust 47 m/s, 1053 N, 1404 N.m | 140.5 (socket cheek inner corner near top rim) | 1.78 (E250, 250) | 25.3 (pole top, hand 26.0) | 39 127 tet10 | CalculiX 2.21 |
| A2 pole+base, wind on diagonal | same | 131.7 (socket top rim, cheek) | 1.90 | 25.2 | 39 127 tet10 | CalculiX 2.21 |
| B1 antenna bracket, arm face contact + bolts (headline) | wind 116.5 N + 29.4 N weight on reader | 43.4 (yoke bend root, web-cheek) | 3.0 (5052-H32, 130) | 1.94 (reader CG 1.01) | 65 581 tet10 | CalculiX 2.21 |
| B2 bracket, washer-only support (recipe R2 literal) | same | 51.6 (yoke) | 2.5 | 3.07 (CG 1.62) | 110 471 tet10 | CalculiX 2.21 |
| B3 bracket, arm face fixed | same | 18.5 (tilt plate body; yoke 15.8) | 7.0 | 0.34 (CG 0.11) | 110 471 tet10 | CalculiX 2.21 |
| C1 boom, 50 N down + self weight | 50 N + 0.15 kg fittings + gravity | 12.4 FE beyond clamp+60 mm; 13.3 at clamp edge (beam theory) | 8.3 (6063-T5, 110) | 2.01 (tip 2.10) | 11 704 S8 | CalculiX 2.21 |
| C2 boom, 50 N horizontal | 50 N lateral at tip | 17.1 FE at x=265 mm; 18.0 at clamp edge (beam theory) | 6.1 | 5.71 (tip 5.98) | 11 704 S8 | CalculiX 2.21 |

FoS uses the finest mesh of each case and the stress read outside singular zones (below). Rows A1/A2 use the worst design value over the mesh sequence at the finest mesh.

### Mesh convergence (3 or more sizes each; PNGs 1920 px wide in `figures/`)

| Case | Elements | Design max vM | Raw nodal peak | Displacement |
|---|---|---|---|---|
| A face | 13 792 / 22 013 / 39 127 | 119.5 / 118.6 / 140.5 | 402 / 880 / 694 | 25.18 / 25.21 / 25.26 pole top |
| A diag | 13 792 / 22 013 / 39 127 | 106.1 / 136.8 / 131.7 | 483 / 772 / 461 | 25.11 / 25.21 / 25.20 |
| B contact | 27 816 / 45 551 / 65 581 | 41.7 / 40.8 / 43.4 | 101 / 131 / 129 | CG 0.991 / 0.994 / 1.005 |
| B washer | 25 209 / 41 729 / 110 471 | 51.2 / 51.4 / 51.6 | 111 / 137 / 160 | CG 1.594 / 1.600 / 1.622 |
| B arm | 25 209 / 41 729 / 110 471 | 19.1 / 18.1 / 18.5 | 25 / 28 / 32 | CG 0.107 / 0.112 / 0.114 |
| C vert | 530 / 1 246 / 2 926 / 5 340 / 11 704 | 12.44 / 12.42 / 12.43 / 12.41 / 12.43 (beyond clamp+60) | clamp corner 17.4 / 16.3 / 18.3 / 24.1 / 28.3 (grows) | tip 2.14 / 2.11 / 2.11 / 2.10 / 2.10 |
| C horiz | same | 16.97 / 16.90 / 16.92 / 16.89 / 16.90 | 34.3 / 35.3 / 40.5 / 52.8 / 61.5 (grows) | tip 6.06 / 6.01 / 6.01 / 5.96 / 5.98 |

Reading: displacements and the B and C design values converge within about 3 %. **Case A design stress is not converged**: it varies 106 to 141 MPa between meshes (not monotonic) because the maximum sits next to the socket top rim where the rigid frictionless pole bears on the cheek (a contact edge). Treat A as "about 120 to 140 MPa, FoS 1.8 to 2.1", not as one number. The raw peaks (up to 880 MPa) are weld-toe / constraint singularities and are not design stresses; they are reported only to show that they move with the mesh.

## Models and how singularities were handled

* **A**: `base_weldment.step` (16 mm plate, 4 gussets, socket) + a 600 mm tall pole stub stiffness-matched to the 80x80 extrusion (E_eq = E x 109.9 cm4 / I of the chamfered solid square), frictionless contact pole/socket (surface-to-surface, linear pressure-overclosure K=2000), bolts-only support (4 M12 washer annuli fixed in z; in-plane determinate restraint), CALCS item forces applied at their heights as a couple at the pole top, plus dead weight. Welds are assumed fully bonded (shared mesh), no weld geometry. Gravity eccentricity included.
* **B**: `antenna_bracket_assy.step` (yoke + tilt plate at 20 deg), bonded spacer patches at pivot and lock, reader as a rigid body (3 kg, CG offset) tied to the 4 reader bolt holes, force on the CG. Three support variants: B2 reproduces recipe R2 literally; it is non-physical because nothing resists the torsion the reader load puts into the web, so the web deflects more. B1 adds the two 40x40 arm faces as contact strips; B3 fixes them. B1 is the realistic one.
* **C**: no barrier boom STEP exists in the repo, so the boom is a mid-surface shell model of the 60x30x1.5 RHS (x = 105 to 1170 mm from the shaft axis), top and bottom walls fixed for x = 105 to 205 mm (the carrier-plate clamp), rigid tip tied to a reference point at 1200 mm. Shell model checked against beam theory: far-field stress within 1 to 3 % of beam theory at x >= 265 mm, tip deflection within 2 % (vertical) and 5 % (horizontal) of a beam clamped at x = 205 mm.
* **Singularities**: the design reading excludes nodes within 0.5 x thickness of weld toes, gusset-cheek junction lines, contact edges and anchor-washer edges (A: 8 mm of the plate toes, 3 mm of cheek/gusset lines), within 1 x t of bonded patches and 2 x t of idealised fixed patches (B), and the sharp tilt-plate ear corner. About 16 to 28 % of bracket nodes and 19 % of weldment nodes are excluded. Both the raw and the design values are stored in `results/*/metrics.json`. For C the reading is taken beyond clamp+60 mm and compared with beam stress at the clamp edge.

Mesh statistics (nodes, elements, SICN quality, solve time) for every run: `results/mesh_stats.csv`. Quality of the headline meshes: A h8 min SICN 0.010, mean 0.795, 1 element below 0.1; B contact h5 min 0.008, mean 0.778, 47 elements below 0.1 of 65 581; B arm/washer h4 min 0.020, 7 below 0.1; shells have min Jacobian ratio 1.0. A few poor tets sit at small features, none were at the reported peak locations. Solver logs: `results/<run>/job.log`, `job.sta`.

## FE versus hand calculation (CALCS.md)

| Item | Hand | FE | Comment |
|---|---|---|---|
| Pole-top deflection, 47 m/s | 25.96 mm | 25.2 to 25.3 mm | -3 %, mesh independent |
| Bolt tension, wind on face | 5.23 kN | 5.17 kN (h8) | -1 % |
| Bolt tension, diagonal (governs) | 7.39 kN | 7.00 kN (h8) | -5 %; FE slightly lower, hand calc is conservative |
| Pole stress at z=600 mm (face wind) | 29.5 MPa (moment/W at that section) | 30.4 MPa | +3 %. Diagonal wind: 40.3 MPa = 1.37 x hand, consistent with the corner being sqrt(2) further from the neutral axis |
| Base plate / gusset | plate 87 MPa (yield line, no gusset credit); gusset 19.5 MPa | plate 46 to 50 MPa; gusset 54 (face) to 90 (diag) MPa at the gusset-cheek junction line | plate hand calc conservative (gussets help). Gusset FE value is a junction reading, mesh dependent, not an axial stress |
| Socket cheek | not checked by hand (bearing 8.8 MPa) | 120 to 140 MPa near the top rim | **New finding**, not in the hand calc. FoS about 1.8 to 2.1 on the idealised rigid frictionless contact |
| Yoke bend root | 10.5 MPa, FoS 12.4 | 41 to 43 MPa (B1), 51 (B2), 14 (B3) | Hand calc **underestimates** by about 4x. It assumed the wind moment enters as out-of-plane bending of one cheek. In the FE the reader's in-plane moment goes through the web as torsion into the bend roots. FoS about 3, still acceptable; CALCS should be updated |
| Boom bending, vertical | 16.2 MPa at hub, 3.7 mm | 12.4 MPa (13.3 at clamp edge), 2.1 mm | Hand uses the lever to the shaft axis (66.7 N.m); FE clamps at x = 205 mm (54.4 N.m). Same beam formula gives FE agreement within 1 %. If the load path really starts at the hub the hand calc governs |
| Boom, horizontal | 21.7 MPa | 18.0 MPa (beam, clamp edge), FE 17.1 | same lever explanation |
| Bracket first frequency | "stiff" (not quantified) | 35.9 Hz (arm face fixed, 3 kg reader as lumped mass) | upper bound, since the arm is not rigid |

## CAD observations from the FE work

* The M10 cross-bolt holes in the socket cheeks are blocked by the gussets on the same centre-line (interference in `base_weldment.step`); not modelled as a load path.
* The tilt plate has a sharp inner corner between ear and face (a bend radius is missing in the model); FE excludes 5 mm around it.
* The earlier STEP with a mirrored lock slot was corrected by the CAD team before the snapshot; the snapshot hashes are in `models/repo_step_snapshot/SHA256SUMS.txt`.

## What this does and does not prove

Proves: with the stated idealisations, the pole deflection (26 mm), bolt tensions and pole stress agree with the hand calc to within about 5 %; the 16 mm plate and gussets are not the weak point; the bracket and the boom carry the design loads with FoS 3 and above at the design-reading locations; the hand calc for the yoke bend root was optimistic and FE gives a better-founded 41 to 43 MPa.

Does not prove:
* A design stress at the socket cheek top rim is not converged and rests on a rigid, frictionless, chamfered-corner pole; real pole/socket contact, clearance, the cross bolts and the weld strength could move it either way.
* Welds are not modelled as welds (no toe geometry, no HAZ, no fatigue, no weld throat check). FE does not replace the fillet-weld hand check.
* Pivot and lock bearing stress is not resolved (bonded patches); rely on the hand-calc 1.5 MPa.
* Boom bolt-hole bearing is not modelled; the carrier clamp is an ideal fix. The hub and shear pin were not FE-modelled (load path ambiguous).
* Wind is static, all items face-on at once, as in CALCS; no gust dynamics, no vibration beyond one modal run, no impact.
* The pole is an equivalent-stiffness solid, so pole stress near the socket is not valid and the extrusion's slot geometry is not represented.
* These are not FreeCAD or Fusion screenshots; the runs are to be repeated natively (next section).

## Repeat in FreeCAD FEM

Common: FreeCAD 0.21+ or 1.0 with FEM workbench, CalculiX and Gmsh installed (Edit > Preferences > FEM > CalculiX, Gmsh binary paths).

1. Part workbench: File > Import `cad/step/base_weldment.step` (case A) or `cad/step/antenna_bracket_assy.step` (case B).
2. Switch to FEM workbench. Model > Analysis container (FEM analysis).
3. Case A pole: Part > Primitives > Box 80 x 80 x 600 mm placed on the socket centre, bottom at the plate top + 0 (it sits in the 81 x 81 mm socket); Part > Compound or leave separate. Case B: nothing to add.
4. Materials: Model > Material for solid. Case A: Steel, E 200 000 MPa, nu 0.3, plate/socket. Pole box: E = 200 000 x 109.9 cm4 / (80^4/12 mm4 = 341.3 cm4) -> E = 64 400 MPa (or import the true profile and use 6063-T5, E 69 500). Case B: 5052-H32, E 70 300, nu 0.33 (Rp0.2 130). Case C: 6063-T5, E 69 500, nu 0.33 (Rp0.2 110).
5. Constraints:
   * A: Fixed on the 4 anchor-hole washer faces (diameter 24 mm around each hole); Contact between pole sides and socket inner faces (Constraints > Contact, friction 0, slope 2000). Fixed support is enough; check that bolt reactions are about 5.2 kN (face) and 7.0 to 7.4 kN (diagonal).
   * B: Fixed on the two Ø12 web washer faces (R2), then repeat with Fixed on the 130 x 15 mm arm-contact strips; Constraint Rigid body on the 4 reader bolt holes.
   * C: Fixed on the two 60 mm-wide faces under the carrier plates, x = 105 to 205 mm.
6. Loads: Constraint Force (or Pressure). A: forces from the CALCS table (116.5 N at z 1.45 m, 37.1 N at 1.60, 28.0 at 1.20, 31.8 at 1.20, 124.1 at 2.25, 206.8 at 0.90, pole 509 N distributed) acting in the wind direction on the pole faces/box; for a first run apply the resultant 1053 N at 1.31 m height and gravity (Constraint Self-weight). B: 116.5 N horizontal (wind) and 29.4 N down at the reader centre, on a rigid reference. C: 50 N down on the tip end face, plus Self-weight; second run 50 N sideways.
7. Mesh: FEM Mesh from shape by Gmsh. Element order: 2nd (Tet10). Max size: A plate/weldment 8 mm (pole 16 to 30 mm), B 5 mm, C shell 6 mm; Min size 1 mm; click Apply. Run it at three sizes (about 2x finer each) for the convergence table. Record Nodes/Elements from the mesh properties.
8. Solver: Solve > CalculiX. Set Analysis type Static, enable nonlinear (geometric) off for the first run. Run, then Close.
9. Results: double-click CCX_Results. Show Von Mises stress, "Displacement magnitude" and enable Deformation: set scale to a fixed value and write it in the screenshot caption. Set the colour range 0 to Rp0.2/2 (case A 125 MPa, B 65, C 55) via the stress filter, and screenshot with the legend (View > Save picture, white background). Read the maximum with the "Result" panel but also probe a point 5 mm away from weld toes and corners; quote the filtered value, not the corner peak.
10. Save as `ParkFlow_<case>.FCStd`. Compare against the table above (pole-top 25 mm, bolt 5.2 / 7.0 kN, B bend root about 40 MPa with contact, boom 12 to 13 MPa).

## Files

* `scripts/run_all.sh`: whole pipeline. `case_a.py`, `case_b.py`, `case_c.py` build mesh and deck and run ccx; `post_*.py` extract metrics; `summarize.py` convergence PNGs; `render_all.py` contour PNGs; `pack.sh` compression.
* `models/`: frozen STEP snapshot + `SHA256SUMS.txt`, `base_weldment_t12.step` (sensitivity variant).
* `results/<run>/`: `job.inp.gz` (kept for A face h8, A face and diag h16, B contact h6, B arm freq h6; the others can be rebuilt without solving), `job.log`, `job.sta`, `job.dat.gz`, `meta.json`, `metrics.json`; `.frd` files were deleted for size (regenerate with `run_all.sh`; decks can be rebuilt without solving by `case_*.py ... --nosolve`). `results/summary.json`, `results/mesh_stats.csv`.
* `figures/`: `convergence_*.png` and `vm_*.png` (1920 px wide, white background, deformation scale and colour range 0 to Rp0.2/2 printed on each).
* Sensitivities in `results/`: A diag with a 12 mm plate (cheek design 138 MPa, plate 91 MPa, so 12 mm would be marginal), A face with a solid (non-equivalent) pole (pole top 9.35 mm, i.e. unrealistically stiff, shows why the equivalent-stiffness pole matters). The failed `h4` modal run was discarded.
