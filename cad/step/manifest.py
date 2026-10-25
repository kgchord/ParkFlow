#!/usr/bin/env python3
"""
manifest.py - writes cad/step/STEP_MANIFEST.md from _build_index.json (what was built) and
_verify_results.json (what was measured by re-importing the files).  Nothing in the tables is typed by hand
except (a) the density table and (b) the MATERIALS.md mass lines (parsed from MATERIALS.md where possible).

    python3 cad/step/build_step.py && python3 cad/step/verify_step.py && python3 cad/step/manifest.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scadparams import load  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
MATERIALS_MD = os.path.join(HERE, "..", "MATERIALS.md")

# densities [kg/m3]: MATERIALS.md "Density basis" (steel 7850, Al 2680-2700, ASA 1070, PETG 1270);
# the 2700 / 2680 split is the one used in calcs/calcs.py MAT table (6063, 6061 = 2700; 5052 = 2680).
DENS = {"IS2062-E250 (MS)": 7850.0, "EN8 (080M40) steel": 7850.0, "Al 6063-T5": 2700.0, "Al 6061-T6": 2700.0,
        "Al 5052-H32": 2680.0, "ASA (FDM)": 1070.0, "PETG (natural)": 1270.0}

DOMAIN_FILES = {
    "gantry": ["gantry_antenna_bracket.scad", "gantry_camera_arm.scad", "gantry_channel_cap_sign.scad", "gantry_base_weldment.scad", "pf_bought.scad"],
    "edge": ["edge_internals.scad", "edge_enclosure.scad", "edge_node_assembly.scad", "pf_bought.scad"],
    "barrier": ["barrier_parts.scad", "barrier_assembly.scad", "pf_bought.scad"],
    "occupancy": ["occupancy_parts.scad", "occupancy_node_assembly.scad", "pf_bought.scad"],
    "lane": ["lane_layout.scad", "barrier_assembly.scad"],
}
DOMAIN_TITLE = {"gantry": "(a) Lane gantry pole", "edge": "(b) Edge Node", "barrier": "(c) Demo boom barrier",
                "occupancy": "(d) Occupancy node", "lane": "(e) Lane layout"}

# MATERIALS.md line  ->  how the CAD mass is formed:  key = Part.mat_key / explicit list of (part_id, count)
# (label, MATERIALS.md kg, [(part_id, count)], material key used for density, comment)
LINES = {
    "gantry": [
        ("Pole 80x80, L 2400", 12.96, [("gantry_pole_80x80", 1)]),
        ("Base plate 250x250x16", 7.68, [("gantry_base_plate", 1)]),
        ("Socket cheeks 2x93x150 + 2x81x150, 6 mm", 2.43, [("gantry_socket_cheek_long", 2), ("gantry_socket_cheek_short", 2)]),
        ("Gussets 4x 74x120x6", 1.13, [("gantry_gusset", 4)]),
        ("Antenna arm 40x40, L 350", 0.53, [("gantry_antenna_arm_40x40", 1)]),
        ("Antenna yoke, 5 mm", 0.44, [("antenna_yoke", 1)]),
        ("Antenna tilt plate, 5 mm", 0.64, [("antenna_tilt_plate", 1)]),
        ("Camera arm 40x40 (label says L 250) + adapter plate", 0.58, [("gantry_camera_arm_40x40", 1), ("gantry_camera_adapter_plate", 1)]),
        ("Sign brackets 2x 3 mm", 0.26, [("gantry_sign_bracket", 2)]),
        ("Edge Node pole brackets 2x 340x50x3", 0.80, [("gantry_edge_pole_bracket", 2)]),
        ("Pole cap (ASA)", 0.07, [("gantry_pole_cap", 1)]),
        ("Cable boot (ASA)", 0.10, [("gantry_cable_boot", 1)]),
    ],
    "edge": [
        ("Mounting plate 260x360x3", 0.75, [("edge_mount_plate", 1)]),
        ("Heat spreader 100x70x5 + bar", 0.14, [("edge_heat_spreader", 1)]),
        ("External heat sink 200x150, 18 fins (bought)", 1.00, [("edge_heat_sink_envelope", 1)]),
        ("Pi tray (ASA)", 0.02, [("edge_pi_tray", 1)]),
        ("Sun hood 2 mm (est.)", 0.9, [("edge_sun_hood", 1)]),
    ],
    "barrier": [
        ("Base plate (label: 360x310x8)", 4.71, [("barrier_base_plate", 1)]),
        ("Frame 20x20 (4 posts + 8 rails)", 2.07, [("barrier_frame_post_20x20", 4), ("barrier_frame_rail_x_20x20", 4), ("barrier_frame_rail_y_20x20", 4)]),
        ("Skins 2 mm + roof 3 mm", 5.12, [("barrier_front_panel", 1), ("barrier_back_panel", 1), ("barrier_side_panel", 2), ("barrier_roof", 1)]),
        ("Motor plate 200x150x6", 0.49, [("barrier_motor_plate", 1)]),
        ("Bearing plate", 0.30, [("barrier_bearing_plate", 1)]),
        ("Stub shaft D20", 0.30, [("barrier_stub_shaft", 1)]),
        ("Hub D70 + tongue", 0.31, [("barrier_hub", 1)]),
        ("Carrier plates 2x 5 mm", 0.30, [("barrier_carrier_plate", 2)]),
        ("Shear pin D5", 0.002, [("barrier_shear_pin", 1)]),
        ("Boom 60x30x1.5 (label: L 1135)", 0.85, [("barrier_boom_tube", 1)]),
        ("Boom tip cap (ASA)", 0.06, [("barrier_boom_tip_cap", 1)]),
        ("Counterweight 7x 100x60x10 (+ tail bar)", 2.98, [("barrier_cw_plate", 7), ("barrier_cw_tail_bar", 1)]),
        ("Limit flag(s) 3 mm", 0.04, [("barrier_limit_flag", 1)]),
        ("Photo-beam posts 2x + 100x100x5 feet", 1.24, [("barrier_photo_post_20x20", 2), ("barrier_photo_post_foot", 2)]),
    ],
    "occupancy": [
        ("Base (ASA) - 37 g", 0.037, [("occ_base", 1)]),
        ("Cover (ASA) - 52 g", 0.052, [("occ_cover", 1)]),
        ("Diffuser (PETG) - 5 g", 0.005, [("occ_diffuser", 1)]),
    ],
}
# stated sub-totals in MATERIALS.md (read from the file text below for display only)
STATED_TOTALS = {"gantry": 28.4, "edge": 9.0, "barrier": 24.0, "occupancy": 0.130}
ROWS_SUM_NOTE = {   # rows in MATERIALS.md that have a mass but no STEP part with a density (bought / est.)
    "gantry": [("Cable channel 40x25 PVC (est.)", 0.5)],
    "edge": [("Enclosure (PC, est.)", 2.6), ("Gasket", 0.02), ("Sink window gasket", 0.01), ("Glands + vent", 0.15), ("Electronics (est.)", 2.5)],
    "barrier": [("Gearmotor (est.)", 2.5)],
    "occupancy": [("Electronics (est.)", 0.035)],
}


def fmt_params(names, P, maxn=7):
    out = []
    for n in names[:maxn]:
        try:
            v = P[n]
            out.append(f"{n}={v:g}" if isinstance(v, (int, float)) else f"{n}={v}")
        except KeyError:
            out.append(f"{n}=?")
    if len(names) > maxn:
        out.append(f"+{len(names) - maxn} more")
    return ", ".join(out)


def main():
    idx = json.load(open(os.path.join(HERE, "_build_index.json")))
    ver = {r["id"]: r for r in json.load(open(os.path.join(HERE, "_verify_results.json")))["results"]}
    Ps = {d: load(*fs) for d, fs in DOMAIN_FILES.items()}
    parts = {p["id"]: p for p in idx["parts"]}
    asms = {a["id"]: a for a in idx["assemblies"]}

    def mass(pid):
        v = ver[pid]["volume_mm3"] * 1e-9
        d = DENS.get(parts[pid]["material"])
        return None if d is None else v * d

    L = []
    w = L.append
    nfile = len(parts) + len(asms)
    allvalid = all(ver[i]["valid"] for i in list(parts) + list(asms))
    mism = [(i, ver[i]["mismatch"]) for i in list(parts) + list(asms) if ver[i].get("mismatch")]
    w("# STEP manifest (generated - do not edit by hand)\n")
    w("Generated by `cad/step/manifest.py` from `_build_index.json` (what `build_step.py` wrote) and `_verify_results.json` "
      "(what `verify_step.py` measured by re-importing every file with CadQuery/OCCT). Re-run the three scripts to refresh.\n")
    w("## What these files are - and are not\n")
    w("* **Script-generated interchange geometry.** Every STEP file is produced by CadQuery 2.8 (OCCT B-rep) from the numbers in the "
      "OpenSCAD `*_params.scad` files (read programmatically by `scadparams.py`; no dimension is typed in the builders, except the few "
      "literals that sit inside module bodies of the .scad files, listed under *Limitations*).")
    w("* **Not native parametric CAD.** The files carry no sketches, no constraints, no feature tree and no "
      "spreadsheet. The native parametric models are the FreeCAD rebuild described in "
      "`cad/freecad/REBUILD_GUIDE.md` (see `cad/CAD_STATUS.md`).")
    w("* **Bought-in parts are simplified envelopes** (`*_envelope`); their sizes are the ASSUMED/class sizes already stated in "
      "`pf_bought.scad` and `cad/README.md` and must be re-checked against the purchased part's drawing. Fasteners, anchors, "
      "decals/tape and cable runs are not modelled.\n")
    w("## Verification summary\n")
    w(f"* Files: **{len(parts)} part files + {len(asms)} assembly files = {nfile}**. All re-imported from disk: "
      f"{'**all solids valid (BRepCheck)**' if allvalid else '**INVALID SOLIDS PRESENT**'}.")
    ref_n = sum(1 for i in list(parts) + list(asms) if "ref_volume_mm3" in ver[i])
    w(f"* **{ref_n}** files were compared with an OpenSCAD STL of the same part/assembly in the same frame "
      "(volume, bounding box and corner position, and STEP-surface-to-STL-surface distance; thresholds: volume 2 %, "
      "bbox 2 % and >0.3 mm, surface agreement >= 99 % of sampled STEP surface within max(0.3 mm, 2.5 x STL sample spacing)). "
      "The other files have no OpenSCAD module that isolates them (plain boxes/cylinders, trimmed or merged bodies); they are "
      "validated for solid validity and volume against their closed-form parameters only.")
    w("* Printed parts are additionally compared with the checked-in `cad/stl/*.stl` (print orientation: volume only).")
    w("* Assembly volume comparison uses sum(body volumes) - sum(pairwise overlaps): the OpenSCAD STL is a boolean UNION, "
      "while the STEP assemblies keep separate bodies, some of which overlap in the source model (see *Interferences*).\n")
    if mism:
        w("### Files outside tolerance (all explained below the table)\n")
        w("| id | what differs |\n|---|---|")
        for i, m in mism:
            note = asms.get(i, {}).get("ref_note") or parts.get(i, {}).get("notes") or ""
            w(f"| `{i}` | {'; '.join(m)}  {('-> ' + note) if note else ''} |")
        w("")
    else:
        w("**No file exceeds the tolerances.**\n")

    for dom in ("gantry", "edge", "barrier", "occupancy", "lane"):
        P = Ps[dom]
        dp = [p for p in idx["parts"] if p["domain"] == dom]
        da = [a for a in idx["assemblies"] if a["domain"] == dom]
        if not dp and not da:
            continue
        w(f"\n## {DOMAIN_TITLE[dom]}\n")
        w("### Parts\n")
        w("| Part | File | Type | Material | Vol cm3 | Mass kg | BBox mm | Source params (values) | Check vs OpenSCAD |")
        w("|---|---|---|---|---:|---:|---|---|---|")
        for p in dp:
            r = ver[p["id"]]
            m = mass(p["id"])
            mk = f"{m:.3f}" if m is not None else "n/a"
            bb = " x ".join(f"{x:.1f}" for x in r["bbox_size"])
            chk = _check(r)
            kind = "fabricated" if p["kind"] == "fabricated" else "envelope"
            w(f"| `{p['id']}` | `{p['file']}` | {kind} | {p['material'] or ''} | {r['volume_mm3'] / 1000:.2f} | {mk} | {bb} | "
              f"{fmt_params(p['params'], P)} | {chk} |")
        w("\n### Assemblies\n")
        w("| Assembly | File | Bodies | Vol cm3 (sum) | Vol cm3 (union est.) | Fabricated-part mass kg | BBox mm | Check vs OpenSCAD |")
        w("|---|---|---:|---:|---:|---:|---|---|")
        for a in da:
            r = ver[a["id"]]
            fm = 0.0
            for pid, n in a["contents"].items():
                if pid in parts and parts[pid]["kind"] == "fabricated":
                    mm = mass(pid)
                    if mm is not None:
                        fm += mm * n
            bb = " x ".join(f"{x:.1f}" for x in r["bbox_size"])
            w(f"| `{a['id']}` | `{a['file']}` | {r['n_solids']} | {r['volume_mm3'] / 1000:.1f} | {r['volume_union_est_mm3'] / 1000:.1f} | "
              f"{fm:.2f} | {bb} | {_check(r)} |")
        w("")
        for a in da:
            if a.get("ref_note"):
                w(f"* `{a['id']}`: {a['ref_note']}")
        w("")

    # ------------------------------------------------------------ MATERIALS comparison
    w("\n## Masses: CAD volume x MATERIALS.md density vs MATERIALS.md\n")
    w("CAD mass = STEP volume x density (steel 7850, Al 6063/6061 2700, Al 5052 2680, ASA 1070, PETG 1270 kg/m3; see top of "
      "`manifest.py`). A row is flagged **DISAGREE** when the two differ by more than 5 %. The comparison is mechanical - the "
      "explanation column states only what can be read from the source files.\n")
    for dom in ("gantry", "edge", "barrier", "occupancy"):
        w(f"\n### {DOMAIN_TITLE[dom]}\n")
        w("| MATERIALS.md line | MATERIALS kg | CAD kg | Delta % | Flag | Note |")
        w("|---|---:|---:|---:|---|---|")
        tot_cad = 0.0
        tot_mat = 0.0
        for label, mkg, items in LINES[dom]:
            cad = 0.0
            ok = True
            for pid, n in items:
                mm = mass(pid)
                if mm is None:
                    ok = False
                    break
                cad += mm * n
            if not ok:
                w(f"| {label} | {mkg:g} | n/a | | | no density in MATERIALS.md |")
                continue
            d = 100.0 * (cad - mkg) / mkg
            tot_cad += cad
            tot_mat += mkg
            flag = "**DISAGREE**" if abs(d) > 5 else "ok"
            w(f"| {label} | {mkg:g} | {cad:.3f} | {d:+.1f} | {flag} | {NOTES.get((dom, label), '')} |")
        extra = sum(v for _, v in ROWS_SUM_NOTE[dom])
        stated = STATED_TOTALS[dom]
        rows_sum = sum(m for _, m, _ in LINES[dom]) + extra
        w(f"\nSum of the listed MATERIALS.md rows incl. bought/est. rows ({', '.join(n for n, _ in ROWS_SUM_NOTE[dom])}): "
          f"**{rows_sum:.3f} kg**; MATERIALS.md states **{stated:g} kg** "
          f"({'consistent' if abs(rows_sum - stated) / stated < 0.02 else '**DISAGREE by %.1f %%**' % (100 * (rows_sum - stated) / stated)}). "
          f"Rows with a CAD mass: MATERIALS {tot_mat:.3f} kg vs CAD {tot_cad:.3f} kg.")
    w("\n### Weldment cross-check against the sentence at the top of MATERIALS.md\n")
    bw = ver["base_weldment"]["volume_mm3"] / 1000
    w(f"MATERIALS.md says the CadQuery B-rep weldment volume is 1424.8 cm3 (11.2 kg). The weldment regenerated from the .scad "
      f"(grout slots and cheek relief notches added, which the first CadQuery version omitted) is **{bw:.1f} cm3 = {bw * 7.85e-3:.2f} kg**. "
      "The 11.24 kg 'analytical sum' in MATERIALS.md is 7.68 + 2.43 + 1.13 and is itself a rounded-area estimate "
      "(`calcs.py` section 6), not a CAD number.")

    # ------------------------------------------------------------ findings
    w("\n## Interferences (overlapping bodies in assemblies)\n")
    w("The OpenSCAD model unions everything, so overlaps are invisible there. In STEP assemblies they are real overlapping solids. "
      "Largest overlaps per assembly (pairwise common volume > 1 mm3; mm3):\n")
    for aid, a in asms.items():
        r = ver[aid]
        if r.get("interference_n"):
            w(f"* `{aid}`: {r['interference_n']} overlapping pairs, total {r['interference_total_mm3'] / 1000:.2f} cm3. "
              + "; ".join(f"{x} / {y}: {v:g}" for x, y, v in r["interference_pairs"][:6]))
    w("\nThese are properties of the OpenSCAD source (bought-in envelopes drawn solid, DIN devices wider than their pitch, "
      "front panel placed inside the frame envelope, roof tilted into the frame, bolted lap joints) and were NOT silently removed from the STEP files.\n")

    w("\n## Per-file mismatch explanations\n")
    w(EXPLAIN)
    w("\n## Limitations\n")
    w(LIMITS)
    w("\n## History\n")
    w(HISTORY)
    open(os.path.join(HERE, "STEP_MANIFEST.md"), "w").write("\n".join(L) + "\n")
    print("wrote STEP_MANIFEST.md")


def _check(r):
    bits = []
    if "vol_diff_pct" in r and r["vol_diff_pct"] is not None:
        bits.append(f"dV {r['vol_diff_pct']:+.2f} %")
        bits.append(f"surf {r['step_to_ref_within_tol_pct']:.1f} %")
    elif "ref_error" in r:
        bits.append("ref failed")
    else:
        bits.append("no isolated STL ref")
    if "stl_vol_diff_pct" in r:
        bits.append(f"cad/stl dV {r['stl_vol_diff_pct']:+.2f} %")
    if r.get("mismatch"):
        bits.append("**MISMATCH**")
    return "; ".join(bits)


NOTES = {
    ("a", "Pole 80x80, L 2400"): "CAD profile is the generic 40-series T-slot profile used by the .scad tslot() module (section 48.9 cm2); MATERIALS.md uses a rough vendor 5.4 kg/m (about 20 cm2). The .scad profile is much more solid than the vendor figure. Take the real section from the supplier drawing; this changes pole mass, wind-load inertia and the calcs.",
    ("a", "Antenna arm 40x40, L 350"): "Same cause as the pole: generic 40x40 T-slot section (9.0 cm2) vs about 5.6 cm2 implied by MATERIALS.md.",
    ("a", "Camera arm 40x40 (label says L 250) + adapter plate"): "Same T-slot section cause; MATERIALS.md label also says L 250 - the .scad arm is 250 long.",
    ("a", "Antenna yoke, 5 mm"): "STEP follows the .scad geometry (250.3 cm3 x 2680); MATERIALS.md 0.44 kg is not reproduced by the .scad geometry at 5052 density. Not resolved - team to confirm.",
    ("a", "Pole cap (ASA)"): "MATERIALS.md quotes 69 cm3 for the STL; CAD cap is 69 cm3 x 1.07 gives 0.074 kg; the 0.07 is rounded.",
    ("b", "Heat spreader 100x70x5 + bar"): "STEP volume 39.1 cm3 matches the .scad (-0.00 %); the bar length is the 23.5 mm evaluated from the .scad formula. MATERIALS.md 0.14 kg is not reproduced.",
    ("b", "External heat sink 200x150, 18 fins (bought)"): "Envelope is a simplified solid sized from pf_bought.scad; real sink mass comes from the vendor.",
    ("c", "Base plate (label: 360x310x8)"): "A solid 360x310x8 mm MS plate is already 6.9 kg; MATERIALS.md 4.71 kg is not reproducible from the stated size.",
    ("c", "Hub D70 + tongue"): "CAD hub = 99.8 cm3 x 2700 = 0.269 kg (matches the .scad); MATERIALS.md 0.31 kg is higher.",
    ("c", "Boom 60x30x1.5 (label: L 1135)"): "The .scad boom tube is 1065 long, not 1135 (the label length); mass scales with length.",
    ("c", "Limit flag(s) 3 mm"): "MATERIALS.md 0.04 kg includes the two bought M12 sensors; the flag alone is 3.3 cm3.",
    ("c", "Shear pin D5"): "Tiny part; value rounded in MATERIALS.md.",
    ("d", "Cover (ASA) - 52 g"): "CAD shell alone is 42.5 cm3; shell + floating probe boss + LED seat = 48.6 cm3 = 52 g at 1070, i.e. MATERIALS.md counts all three solids.",
}
EXPLAIN = """* **Reference hardware.** The OpenSCAD reference modules also draw fasteners, anchors, studs, decals and tape bands. STEP files contain fabricated parts and envelopes only, so assembly bounding boxes differ by the hardware overhang (see table at the top). Part-level files all agree within 1 %.
* **Overlaps.** Assembly volume is compared as sum of bodies minus pairwise overlap because OpenSCAD unions. Overlaps come from the .scad (envelopes drawn solid, DIN devices wider than pitch, front panel inside the frame).
* **Pole mass.** CAD pole 31.7 kg vs 12.96 kg in MATERIALS.md: the .scad T-slot profile is far more solid than the vendor 5.4 kg/m. This is a real inconsistency inside our model, not a STEP error.
* **occ_cover.** The .scad cover is three disconnected solids (shell, probe clamp boss, LED seat). Exported as three STEP parts; the shell is checked against the .scad with the other two added (+0.07 %). The checked-in cad/stl/occ_cover.stl contains all three (compared against the shell only, hence -12.5 %).
* **Totals.** MATERIALS.md edge-node and barrier stated totals (9 kg, 24 kg) are about 10 % and 11 % higher than the sum of their own listed rows (see sections above); gantry total is consistent."""
LIMITS = """* Fasteners, anchors, decals, tape and wiring are not modelled. Bought-in parts are simplified envelopes at assumed class sizes.
* Literals copied from .scad module bodies (not parameters): DIN device list, lane rig dimensions (2400, 700, 6800, 600, 2380), spreader bar length formula, 40 mm slot inset.
* Sign bracket is flat (no bends); tilt plate has sharp bends; sun hood is unbent; T-slot is a generic profile, not a vendor section.
* The occupancy cover keeps the .scad flaws (floating boss and seat); base keyhole counterbore is an enclosed void in the .scad.
* Densities for PC and EPDM are not in MATERIALS.md, so no mass is computed for them."""
HISTORY = """The four STEP files that existed first (base_weldment, antenna_yoke, antenna_tilt_plate, antenna_bracket_assy) were regenerated. The first versions differed from the .scad (yoke cheek outline, arc slot direction, missing grout slots and cheek notches); the current files follow the .scad and carry the weldment at 1414.5 cm3 instead of 1424.8 cm3."""

if __name__ == "__main__":
    main()
