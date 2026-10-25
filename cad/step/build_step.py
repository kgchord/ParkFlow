#!/usr/bin/env python3
"""
ParkFlow - CadQuery (OCCT B-rep) STEP interchange files for EVERY fabricated part and EVERY assembly.

    python3 cad/step/build_step.py          # writes cad/step/*.step and cad/step/_build_index.json
    python3 cad/step/verify_step.py         # re-imports every file, checks validity, compares with OpenSCAD STL
    python3 cad/step/manifest.py            # writes cad/step/STEP_MANIFEST.md from the two JSON files

SINGLE SOURCE OF TRUTH: no dimension is typed in these scripts.  scadparams.py reads the numbers from
cad/openscad/*_params.scad (and the few file-local constants in the part .scad files and pf_bought.scad),
by the same variable names, so editing a *_params.scad value and re-running this script regenerates the
STEP files.  A renamed/removed variable raises KeyError instead of silently using a stale number.

NOTE: these files are *script-generated interchange geometry* that mirrors the OpenSCAD
model.  They contain no sketch constraints, no feature history and no FreeCAD spreadsheet.  See cad/CAD_STATUS.md and cad/freecad/REBUILD_GUIDE.md.

Modules
  build_gantry.py   (a) lane gantry pole              build_edge.py      (b) edge node
  build_barrier.py  (c) demo boom barrier             build_occupancy.py (d) occupancy node
  build_lane.py     (e) lane layout (assemblies of the above)

Original four files (kept under their original names): base_weldment.step, antenna_yoke.step,
antenna_tilt_plate.step, antenna_bracket_assy.step.  They were re-derived from the .scad in this
revision because the first version differed from the .scad (see STEP_MANIFEST.md, "History").
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pf_reg import REG  # noqa: E402


def main():
    t0 = time.time()
    import build_gantry
    gparts = build_gantry.build()
    edge_asm = None
    try:
        import build_edge
        edge_asm = build_edge.build()
    except ImportError:
        pass
    G = build_gantry.gantry_assembly(gparts, edge_asm)
    REG.assembly("gantry_assembly", G, domain="gantry",
                 desc="Lane gantry: weldment, pole, cap, antenna arm + yoke + tilt plate + reader, camera arm, cable channel/boot, "
                      "P10 sign + brackets, Edge Node on pole (explode = 0; plinth, anchors, bolts excluded)",
                 params=["pole_len", "ant_z", "cam_z", "sign_z", "edge_z", "edge_standoff"],
                 sources=["gantry_assembly.scad:gantry"],
                 ref="include <gantry_params.scad>\nuse <gantry_assembly.scad>\ngantry(0, 1, 0);",
                 ref_note="reference STL additionally contains anchors, cross bolts, pivot bolts and conduit hardware; STEP has none")
    import build_barrier, build_occupancy, build_lane
    bar = build_barrier.build()
    occ = build_occupancy.build()
    build_lane.build(G, gparts, bar, occ)
    REG.export_all()
    REG.write_index()
    print(f"wrote {len(REG.parts)} part files + {len(REG.asms)} assembly files in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
