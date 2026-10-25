#!/usr/bin/env python3
"""
gen_param_tables.py - regenerates the PARAMETER TABLES block inside make_spreadsheet.py from the OpenSCAD
source files (cad/openscad/*.scad), so the FreeCAD spreadsheet keeps ONE source of truth with the .scad model.

    python3 cad/freecad/gen_param_tables.py            # rewrites the block between the BEGIN/END markers

It runs in normal Python (not inside FreeCAD).  It uses cad/step/scadparams.py to read the numbers.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "step"))
from scadparams import load, SCAD_DIR  # noqa: E402

ANGLES = {"boom_angle", "tilt_min", "tilt_max", "ant_tilt", "cam_pitch", "cam_yaw", "cam_hfov", "cam_vfov", "boom_ang"}
COUNTS = {"gus_n", "hs_fin_n", "snap_n", "cw_n", "bend_k"}

# (sheet name, [files whose top-level assignments are ALL taken], [(file, [names]) extra file-local constants], formulas)
# formulas: name -> FreeCAD expression using only aliases of the same sheet (unit-consistent: lengths +/- lengths only)
SHEETS = [
    ("GantryParams", ["gantry_params.scad"],
     [("gantry_base_weldment.scad", ["sock_in", "sock_long"]),
      ("gantry_antenna_bracket.scad", ["cheek_r", "cheek_bot_c", "cheek_x", "tp_off", "ear_d", "ear_half_h", "bend_k",
                                       "bend_allow", "bend_deduct", "web_hole_pitch", "web_top_above_pivot"]),
      ("gantry_camera_arm.scad", ["cam_arm_len_eff", "cam_plate_overhang"]),
      ("gantry_channel_cap_sign.scad", ["sign_br_l", "sign_br_w", "edge_br_l", "edge_br_w", "edge_br_t", "edge_lug_pitch"])],
     {"sock_in": "pole_w + 2 * sock_clear", "sock_long": "sock_in + 2 * sock_t", "cheek_x": "yoke_w / 2 - yoke_t",
      "web_top_above_pivot": "pivot_drop - ant_arm_w / 2",
      "bend_allow": "pi / 2 * (yoke_bend_r + bend_k * yoke_t)", "bend_deduct": "2 * (yoke_bend_r + yoke_t) - bend_allow"}),
    ("EdgeParams", ["edge_params.scad"], [("edge_node_assembly.scad", ["base_d_", "inner_floor"])],
     {"base_d_": "enc_d - enc_lid_d", "inner_floor": "enc_wall + bp_boss_h"}),
    ("BarrierParams", ["barrier_params.scad"], [("barrier_parts.scad", ["hy_front", "hub_y", "boom_y"])],
     {"hy_front": "-hs_y / 2", "hub_y": "hy_front - panel_t - hub_gap - hub_t / 2",
      "boom_y": "hub_y - hub_t / 2 - tongue_t / 2 - 2 mm"}),
    ("OccParams", ["occupancy_params.scad"], [], {}),
    ("LaneParams", [], [("lane_layout.scad", ["lane_w", "lane_l", "island_w", "island_h", "pole_y", "bar_y", "car_y", "rz_w", "rz_h",
                                              "cam_hfov", "cam_vfov", "cam_range", "boom_ang"])], {}),
]


def comments(path):
    out = {}
    for line in open(path):
        for m in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*[^;]+;\s*(//\s*(.*))?", line):
            if m.group(3):
                out.setdefault(m.group(1), m.group(3).strip())
    return out


def unit_of(name):
    if name in ANGLES:
        return "deg"
    if name in COUNTS:
        return ""
    return "mm"


def build():
    lines = []
    for sheet, files, extras, formulas in SHEETS:
        rows = []
        seen = set()

        def add(name, value, src, cm):
            if name in seen:
                return
            seen.add(name)
            if isinstance(value, list):
                for i, v in enumerate(value, 1):
                    rows.append((f"{name}_{i}", float(v), unit_of(name), f"{cm} [element {i} of {name}[] in {src}]".strip(), None))
                return
            rows.append((name, float(value), unit_of(name), (cm or "").strip(), formulas.get(name)))
        for f in files:
            P = load(f)
            cm = comments(os.path.join(SCAD_DIR, f))
            # only names assigned in THIS file (not included ones)
            for n, v in P.items():
                if P.origin.get(n) == f:
                    add(n, v, f, cm.get(n, ""))
        for f, names in extras:
            P = load(f)
            cm = comments(os.path.join(SCAD_DIR, f))
            for n in names:
                add(n, P[n], f, cm.get(n, "") or f"file-local constant of {f}")
        lines.append(f'    "{sheet}": [')
        for (n, v, u, c, fm) in rows:
            c = c.replace('"', "'").replace("\\", "/")
            lines.append(f'        ({n!r}, {v!r}, {u!r}, {c!r}, {fm!r}),')
        lines.append("    ],")
    return "\n".join(lines)


def main():
    path = os.path.join(HERE, "make_spreadsheet.py")
    src = open(path).read()
    a = src.index("# BEGIN GENERATED PARAMETER TABLES")
    b = src.index("# END GENERATED PARAMETER TABLES")
    new = ("# BEGIN GENERATED PARAMETER TABLES (python3 cad/freecad/gen_param_tables.py) -------------------------\n"
           "# sheet -> rows of (alias, value, unit, comment, formula-or-None).  Values are the numbers in the .scad files.\n"
           "TABLES = {\n" + build() + "\n}\n")
    open(path, "w").write(src[:a] + new + src[b:])
    print("updated", path)


if __name__ == "__main__":
    main()
