#!/usr/bin/env python3
"""Render von Mises contour PNGs (1920 px wide, white background) for the finest mesh of each headline case.
usage: render_all.py   (run under xvfb-run)"""
import os, sys, json, glob
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import render_lib as rl
ROOT = os.path.abspath(os.path.join(HERE, "..")); RES = os.path.join(ROOT, "results"); FIG = os.path.join(ROOT, "figures")
os.makedirs(FIG, exist_ok=True)

def finest(pattern):
    best = None
    for d in glob.glob(os.path.join(RES, pattern)):
        mf = os.path.join(d, "metrics.json")
        if not os.path.exists(mf) or not os.path.exists(os.path.join(d, "job.frd")): continue
        if d.endswith("_freq"): continue
        m = json.load(open(mf)); n = m.get("elements", m.get("shell_elements", 0))
        if best is None or n > best[0]: best = (n, d, m)
    return best

def scale_for(grid, target_mm):
    dm = float(np.abs(grid["disp_mag_mm"]).max())
    return target_mm / dm if dm > 0 else 1.0

def go(pattern, name, rp, views, target_mm, heading, undeformed=True, **kw):
    b = finest(pattern)
    if not b: print("no result for", pattern); return
    n, d, m = b
    g = rl.load(os.path.join(d, "job.frd"))
    sc = scale_for(g, target_mm); sc = float(f"{sc:.2g}")
    clim = (0.0, rp / 2.0)
    for vname, cam, clip, zoom in views:
        notes = [f"Deformation scale x{sc:g} {"(grey outline = undeformed)" if undeformed else ""}. Colour range 0 to Rp0.2/2 = {rp/2:g} MPa, dark red = above range.",
                 f"CalculiX 2.21, {n} elements (run {os.path.basename(d)}). Raw nodal values; singular edges not filtered in picture."]
        out = os.path.join(FIG, f"vm_{name}_{vname}.png")
        rl.render(g, out, f"{heading}  |  max displacement {float(g['disp_mag_mm'].max()):.2f} mm", clim, sc, camera=cam, notes=notes,
                  clip=clip, zoom=zoom, show_undeformed=undeformed, **kw)
        print("wrote", out)

# ---- Case A: pole + base weldment (Rp 250, E250 plate/socket; pole is Al-equivalent solid, shown at the same range)
go("A_face_t16_eq_h*", "A_face", 250.0, [("base", "iso", [-260, 260, -260, 260, -20, 330], 0.8),
                                          ("pole", "xz", None, 1.0)], 40.0,
   "CASE A  pole+base, wind on face, 47 m/s")
go("A_diag_t16_eq_h*", "A_diag", 250.0, [("base", "iso", [-260, 260, -260, 260, -20, 330], 0.8)], 40.0,
   "CASE A  pole+base, wind on diagonal, 47 m/s")
# ---- Case B
for supp, lab in (("contact", "arm-face contact + bolts"), ("arm", "arm face fixed"), ("washer", "washer-only support")):
    go(f"B_{supp}_h*", f"B_{supp}", 130.0, [("iso", "iso", None, 1.0)], 6.0, f"CASE B  antenna bracket, {lab}")
# ---- Case C
go("C_boom_vert_s*", "C_boom_vert", 110.0, [("iso", "iso", None, 1.0), ("clamp", "iso", [90, 420, -40, 40, -40, 40], 1.0)], 60.0,
   "CASE C  barrier boom, 50 N down at tip", undeformed=False, subdiv=1, smooth=False, lighting=False)
go("C_boom_horiz_s*", "C_boom_horiz", 110.0, [("iso", "iso", None, 1.0)], 60.0, "CASE C  barrier boom, 50 N lateral at tip", undeformed=False, subdiv=1, smooth=False, lighting=False)
