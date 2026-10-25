#!/usr/bin/env python3
"""
CASE C - demo barrier boom, Al 6063-T5 RHS 60x30x1.5 (CALCS.md section 4, recipe R3), SIMPLIFIED shell model.

usage: case_c.py <vert|horiz> <s_mm> [--nosolve]

Model (no STEP of the barrier exists in cad/step; geometry from cad/openscad/barrier_params.scad):
  * boom tube modelled with 8-node shell elements (S8, ccx) on the wall mid-surfaces: 58.5 x 28.5 mm section, t = 1.5 mm,
    from x = 105 mm (hinge_r + 60) to x = 1170 mm (boom_L - tip_cap_l), x measured from the shaft axis.
  * clamp: the carrier plates (5 mm 6061-T6, x = 65..205 mm) sandwich the two 60 mm-high (top/bottom) walls: those two wall
    strips are fully fixed for 105 <= x <= 205 mm; side walls are left free there.  Bolt-hole bearing is NOT modelled.
  * tip: a rigid body (printed nose cap region) ties the end ring at x = 1170 to a reference point at x = 1200 mm (boom_L), where
    the 50 N load acts (same lever arm as CALCS: L = 1.2 m).
  * vert : gravity (tube + 0.15 kg fittings at tip) + 50 N down at the tip, boom horizontal
  * horiz: 50 N horizontal (lane direction) at the tip, no gravity (CALCS 'horizontal nudge' case)
"""
import sys, os, io, json, math
import numpy as np
import gmsh

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import fea_lib as fl
ROOT = os.path.abspath(os.path.join(HERE, ".."))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
mode = args[0]; s = float(args[1])
solve = "--nosolve" not in sys.argv
tag = f"C_boom_{mode}_s{s:g}"
wd = os.path.join(ROOT, "results", tag); os.makedirs(wd, exist_ok=True)

X0, X1, XC, XT = 105.0, 1170.0, 205.0, 1200.0
HZ, HY, T = 58.5, 28.5, 1.5            # mid-surface section: z (vertical, 60 mm face) x y (30 mm face)
gmsh.initialize(); gmsh.option.setNumber("General.Terminal", 0)
gmsh.model.add(tag)
occ = gmsh.model.occ
pts = [occ.addPoint(X0, y, z) for (y, z) in ((-HY / 2, -HZ / 2), (HY / 2, -HZ / 2), (HY / 2, HZ / 2), (-HY / 2, HZ / 2))]
lines = [occ.addLine(pts[i], pts[(i + 1) % 4]) for i in range(4)]
surfs = []
for l in lines:
    r = occ.extrude([(1, l)], X1 - X0, 0, 0)
    surfs.append([t for d, t in r if d == 2][0])
occ.removeAllDuplicates()
occ.synchronize()
nh = max(2, round(HZ / s)); nb = max(2, round(HY / s)); nl = max(8, round((X1 - X0) / s))
for d, c in gmsh.model.getEntities(1):
    x0, y0, z0, x1, y1, z1 = gmsh.model.getBoundingBox(d, c)
    if x1 - x0 > 100:
        gmsh.model.mesh.setTransfiniteCurve(c, nl + 1)
    elif z1 - z0 > 50:
        gmsh.model.mesh.setTransfiniteCurve(c, nh + 1)
    else:
        gmsh.model.mesh.setTransfiniteCurve(c, nb + 1)
for d, c in gmsh.model.getEntities(2):
    gmsh.model.mesh.setTransfiniteSurface(c)
    gmsh.model.mesh.setRecombine(2, c)
gmsh.option.setNumber("Mesh.SecondOrderIncomplete", 1)
gmsh.model.mesh.generate(2)
gmsh.model.mesh.setOrder(2)
nodes = {}; quads = []; tri = 0
for d, c in gmsh.model.getEntities(2):
    types, etags, enodes = gmsh.model.mesh.getElements(2, c)
    for t, tg, nn in zip(types, etags, enodes):
        assert t == 16, f"expected quad8 (type 16), got {t}"
        nn = np.array(nn, dtype=np.int64).reshape(-1, 8)
        for a, row in zip(tg, nn):
            quads.append((int(a), row))
ntags, ncoord, _ = gmsh.model.mesh.getNodes()
allc = {int(t): c for t, c in zip(ntags, np.array(ncoord).reshape(-1, 3))}
used = sorted({int(x) for _, r in quads for x in r})
nodes = {k: allc[k] for k in used}
quality = {}
try:
    tags = [a for a, _ in quads]
    for nm in ("minSJ", "gamma"):
        q = np.array(gmsh.model.mesh.getElementQualities(tags, nm))
        quality[nm] = dict(min=float(q.min()), mean=float(q.mean()))
except Exception as ex:
    quality["error"] = str(ex)
gmsh.finalize()
xyz = {k: np.array(v) for k, v in nodes.items()}

fixed = [k for k, p in xyz.items() if p[0] <= XC + 1e-6 and abs(abs(p[2]) - HZ / 2) < 1e-6]
endring = [k for k, p in xyz.items() if abs(p[0] - X1) < 1e-6]
ref = max(nodes) + 1; rot = ref + 1
nodes_o = dict(nodes); nodes_o[ref] = np.array([XT, 0.0, 0.0]); nodes_o[rot] = np.array([XT, 0.0, 0.0])
d = fl.Deck(f"ParkFlow case C: boom shell model, {mode}, s={s}")
d.nodes(nodes_o)
d.elements("EL_BOOM", [a for a, _ in quads], np.array([r for _, r in quads]), etype="S8")
d.material("AL", "AL6063T5", density=True)
d.add(f"*SHELL SECTION, ELSET=EL_BOOM, MATERIAL=AL\n{T}")
d.nset("NFIX", fixed); d.nset("NEND", endring)
d.add(f"*NSET, NSET=NREF\n{ref}\n*NSET, NSET=NROT\n{rot}")
d.add(f"*RIGID BODY, NSET=NEND, REF NODE={ref}, ROT NODE={rot}")
d.add("*BOUNDARY\nNFIX, 1, 6")
d.add("*STEP\n*STATIC")
if mode == "vert":
    d.add("*DLOAD\nEL_BOOM, GRAV, 9810., 0., 0., -1.")
    d.add(f"*CLOAD\n{ref}, 3, {-(50.0 + 0.15 * 9.81):.6f}")
else:
    d.add(f"*CLOAD\n{ref}, 2, 50.0")
d.add("*NODE FILE\nU, RF\n*EL FILE\nS\n*NODE PRINT, NSET=NFIX, TOTALS=ONLY\nRF\n*NODE PRINT, NSET=NREF\nU")
d.add("*END STEP")
d.write(os.path.join(wd, "job.inp"))
stats = dict(tag=tag, s=s, mode=mode, ref=ref, rot=rot, nodes=len(nodes), elements=len(quads), quality=quality, n_fixed=len(fixed), n_end=len(endring),
             XC=XC, X1=X1, XT=XT, HZ=HZ, HY=HY, T=T)
json.dump(stats, open(os.path.join(wd, "meta.json"), "w"), indent=1)
print(json.dumps(stats), flush=True)
if solve:
    t, rc = fl.run_ccx("job", wd)
    print(f"ccx finished in {t:.0f} s rc={rc}", flush=True)
    json.dump(dict(stats, solve_s=t, rc=rc), open(os.path.join(wd, "meta_run.json"), "w"), indent=1)
