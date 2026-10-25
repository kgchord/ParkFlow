#!/usr/bin/env python3
"""
CASE A - gantry pole + base-plate weldment under IS 875-3 wind (CALCS.md section 1/2, recipe R1).

usage: case_a.py <face|diag> <h_mm> [plate_t=16|12] [pole=eq|solid] [--nosolve]

Model
  * base_weldment.step (repo, 16 mm plate; or models/base_weldment_t12.step) - ONE fused solid (idealised weld, no weld geometry)
  * pole: 80x80 solid box 2400 mm above the plate top, separate bodies, frictionless CONTACT with the socket inner faces and
    the plate top. Flexural rigidity of the real 8-slot extrusion (I=109.9 cm4) is reproduced by scaling E of the solid box
    (E_eq = E*109.9/341.3 = 22.4 GPa) ["eq"], or true E ["solid", sensitivity run].
  * supports: all DOF fixed on the 4 anchor washer annuli (D14 hole .. D24), top of plate; NO support under the plate
    (bolts only = worst case of recipe R1).
  * loads: item wind forces from calcs.py (same numbers as CALCS.md table), spread over node slabs at their heights;
    pole self-wind spread uniformly; gravity eccentricity moment 28.0 N.m as a vertical couple at the pole top.
    face = wind along +x (normal to a side); diag = along (+x,+y)/sqrt2 (bolt diagonal).
"""
import sys, os, io, json, math, contextlib
import numpy as np
import gmsh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fea_lib as fl

ROOT = os.path.abspath(os.path.join(HERE, ".."))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
direction = args[0]; h = float(args[1])
plate_t = float(args[2]) if len(args) > 2 else 16.0
pole_mode = args[3] if len(args) > 3 else "eq"
solve = "--nosolve" not in sys.argv
KCONT = float(os.environ.get('KCONT', '2000'))

tag = f"A_{direction}_t{int(plate_t)}_{pole_mode}_h{h:g}"
wd = os.path.join(ROOT, "results", tag); os.makedirs(wd, exist_ok=True)

# ---------------------------------------------------------------- loads from calcs.py (unchanged)
sys.path.insert(0, os.path.join(ROOT, "..", "calcs"))
with contextlib.redirect_stdout(io.StringIO()):
    import calcs
R = calcs.pole_case(47, "80x80")
items = [(n, F, z * 1000.0) for (n, A, Cf, F, z, M) in R["rows"][:-1]]      # N, mm above plate top
F_pole = R["F_pole"]; Mg = R["Mg"] * 1000.0                                   # N, N.mm
POLE_H = 2400.0
u = np.array([1.0, 0.0]) if direction == "face" else np.array([1.0, 1.0]) / math.sqrt(2.0)

# ---------------------------------------------------------------- geometry + mesh
step = os.path.join(ROOT, "models", "repo_step_snapshot", "base_weldment.step") if plate_t == 16 else os.path.join(ROOT, "models", f"base_weldment_t{int(plate_t)}.step")
PT = 16.0   # z of the plate top face (12 mm variant keeps the same top face)
gmsh.initialize(); gmsh.option.setNumber("General.Terminal", 0)
gmsh.model.add(tag)
occ = gmsh.model.occ
W = occ.importShapes(step)[0][1]
sock_h = 150.0; zs = PT + sock_h
CH = 4.0     # 4 x 4 mm corner chamfer of the pole profile (real T-slot extrusions have radiused corners; a sharp corner would
             # create an artificial corner-to-corner contact singularity in the socket).  Planar facets keep the mesh coarse.
def pole_section(z, height):
    P = [(-40 + CH, -40), (40 - CH, -40), (40, -40 + CH), (40, 40 - CH), (40 - CH, 40), (-40 + CH, 40), (-40, 40 - CH), (-40, -40 + CH)]
    pts_ = [occ.addPoint(x, y, z) for x, y in P]
    lns = [occ.addLine(pts_[i], pts_[(i + 1) % 8]) for i in range(8)]
    sf = occ.addPlaneSurface([occ.addCurveLoop(lns)])
    return [t for d, t in occ.extrude([(2, sf)], 0, 0, height) if d == 3][0]
lo = pole_section(PT, sock_h)
up = pole_section(zs, POLE_H - sock_h)
out, _ = occ.fragment([(3, lo)], [(3, up)])
occ.synchronize()
pole_vols = [t for d, t in gmsh.model.getEntities(3) if t != W]
H_POLE = 30.0
gmsh.model.mesh.field.add("MathEval", 1)
gmsh.model.mesh.field.setString(1, "F", f"Min({H_POLE}, {h} + 0.25*Max(0, z-{zs+5}))")
gmsh.model.mesh.field.setAsBackgroundMesh(1)
gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 14)
gmsh.option.setNumber("Mesh.MeshSizeMin", 1.2)
gmsh.option.setNumber("Mesh.Algorithm3D", 1)
gmsh.option.setNumber("Mesh.Optimize", 1)
gmsh.model.mesh.generate(3)
gmsh.model.mesh.setOrder(2)
try:
    gmsh.model.mesh.optimize("HighOrder")
except Exception:
    pass
qual = fl.mesh_quality(gmsh)
allv = [W] + pole_vols
nodes, elems = fl.extract_tet10(gmsh, allv)
fmap = fl.tet_face_map(elems)
n_el = {v: len(elems[v][0]) for v in allv}
stats = dict(tag=tag, h=h, plate_t=plate_t, nodes=len(nodes), elements_weldment=n_el[W],
             elements_pole=sum(n_el[v] for v in pole_vols), elements=sum(n_el.values()), quality=qual)

# ---------------------------------------------------------------- node sets / surfaces
def box_surfs(x0, y0, z0, x1, y1, z1, e=0.02):
    return [t for d, t in gmsh.model.getEntitiesInBoundingBox(x0 - e, y0 - e, z0 - e, x1 + e, y1 + e, z1 + e, 2)]

# socket inner faces (master) and pole lower side faces (slave)
sock_in = []; pole_side = []
for sgn in (-1, 1):
    sock_in += box_surfs(sgn * 40.5, -40.5, PT, sgn * 40.5, 40.5, zs)
    sock_in += box_surfs(-40.5, sgn * 40.5, PT, 40.5, sgn * 40.5, zs)
    pole_side += box_surfs(sgn * 40, -40, PT, sgn * 40, 40, zs)
    pole_side += box_surfs(-40, sgn * 40, PT, 40, sgn * 40, zs)
plate_in = [s for s in box_surfs(-40.5, -40.5, PT, 40.5, 40.5, PT) if s not in sock_in]
pole_bot = box_surfs(-40, -40, PT, 40, 40, PT)
# keep only those belonging to the right volumes
def own(sl, vols):
    keep = []
    for s in sl:
        up_, _ = gmsh.model.getAdjacencies(2, s)
        if any(v in vols for v in up_):
            keep.append(s)
    return keep
sock_in = own(sock_in, [W]); plate_in = own(plate_in, [W])
pole_side = own(pole_side, pole_vols); pole_bot = own(pole_bot, pole_vols)
assert len(sock_in) == 4 and len(pole_side) == 4 and len(plate_in) >= 1 and len(pole_bot) == 1, \
    (len(sock_in), len(pole_side), len(plate_in), len(pole_bot))
S_master_side = fl.surface_faces(gmsh, sock_in, fmap)
S_slave_side = fl.surface_faces(gmsh, pole_side, fmap)
S_master_bot = fl.surface_faces(gmsh, plate_in, fmap)
S_slave_bot = fl.surface_faces(gmsh, pole_bot, fmap)

wnodes = set(elems[W][1].ravel().tolist())
pnodes = set()
for v in pole_vols:
    pnodes.update(elems[v][1].ravel().tolist())
xyz = {k: np.array(v) for k, v in nodes.items()}
bolt_xy = [(sx * 190.0 / 2 * math.cos(math.radians(45)), sy * 190.0 / 2 * math.sin(math.radians(45))) for sx in (-1, 1) for sy in (-1, 1)]
bolts = {}
for i, (bx, by) in enumerate(bolt_xy):
    s = []
    for k in wnodes:
        p = xyz[k]
        if abs(p[2] - PT) < 1e-3:
            r = math.hypot(p[0] - bx, p[1] - by)
            if 6.99 <= r <= 12.001:
                s.append(k)
    bolts[f"BOLT{i+1}"] = s
fixed = [k for s in bolts.values() for k in s]

# ---------------------------------------------------------------- loads
pole_node_ids = np.array(sorted(pnodes))
pz = np.array([xyz[k][2] for k in pole_node_ids]) - PT       # height above plate top
cload = {}   # node -> [fx, fy, fz]
def add_force(nid, f):
    cload.setdefault(nid, np.zeros(3))
    cload[nid] += f
def spread(Ftot, zc, half):
    sel = pole_node_ids[np.abs(pz - zc) <= half]
    if len(sel) < 8:
        sel = pole_node_ids[np.abs(pz - zc) <= 2 * half]
    f = Ftot / len(sel)
    for k in sel:
        add_force(int(k), np.array([f * u[0], f * u[1], 0.0]))
    return len(sel)
for (n, F, zc) in items:
    spread(F, zc, 25.0)
nb = int(POLE_H // 50)
for b in range(nb):                       # self-wind of pole as uniform line load, 50 mm bins
    z0 = b * 50.0
    sel = pole_node_ids[(pz >= z0) & (pz < z0 + 50.0)]
    f = F_pole * 50.0 / POLE_H / len(sel)
    for k in sel:
        add_force(int(k), np.array([f * u[0], f * u[1], 0.0]))
top = [int(k) for k, z in zip(pole_node_ids, pz) if z > POLE_H - 1e-3]
S = sum(float(u @ xyz[k][:2]) ** 2 for k in top)
uc = np.mean([float(u @ xyz[k][:2]) for k in top])          # centre the couple so that its net force is exactly 0
S = sum((float(u @ xyz[k][:2]) - uc) ** 2 for k in top)
for k in top:                              # gravity-eccentricity couple (adds to overturning)
    add_force(k, np.array([0.0, 0.0, -Mg / S * (float(u @ xyz[k][:2]) - uc)]))
# dead weight of pole (5.4 kg/m x 2.4 m) + attachments (16.8 kg, CALCS ITEMS) seats the pole on the plate (CALCS neglects it for the
# bolts, a conservative simplification; it relieves each bolt by < 0.1 kN).  Spread over the pole-top face nodes.
W_dead = (5.4 * 2.4 + sum(m for (_, _, _, _, m, _) in calcs.ITEMS)) * 9.81
for k in top:
    add_force(k, np.array([0.0, 0.0, -W_dead / len(top)]))
F_sum = np.sum(list(cload.values()), axis=0)
M_app = sum(np.cross(xyz[k] - np.array([0, 0, PT]), f) for k, f in cload.items())
stats["dead_weight_N"] = W_dead; stats["applied_force_sum_N"] = F_sum.tolist(); stats["applied_moment_about_plate_top_Nmm"] = M_app.tolist()

# ---------------------------------------------------------------- deck
E_true = fl.MATERIALS["AL6063T5"][0]
def I_chamfered_square(a, ch, n=4000):
    xs = (np.arange(n) + 0.5) / n * a - a / 2
    X, Y = np.meshgrid(xs, xs)
    inside = (np.abs(X) + np.abs(Y)) <= (a - ch)             # 45 degree corner cuts
    return float((Y ** 2 * inside).sum() * (a / n) ** 2)
I_pole = I_chamfered_square(80.0, CH)                        # mm4, solid chamfered square
E_eq = E_true * 109.9e4 / I_pole if pole_mode == "eq" else E_true
d = fl.Deck(f"ParkFlow case A: pole + base weldment, wind {direction}, plate {plate_t} mm, pole {pole_mode}")
d.nodes(nodes)
d.elements("EL_WELD", elems[W][0], elems[W][1])
pt = np.concatenate([elems[v][0] for v in pole_vols]); pn = np.concatenate([elems[v][1] for v in pole_vols])
d.elements("EL_POLE", pt, pn)
d.material("MS", "MS_E250", density=False)
d.add(f"*MATERIAL, NAME=POLEMAT\n*ELASTIC\n{E_eq:.1f}, 0.33")
d.add("*SOLID SECTION, ELSET=EL_WELD, MATERIAL=MS")
d.add("*SOLID SECTION, ELSET=EL_POLE, MATERIAL=POLEMAT")
d.nset("NFIX", fixed)
for k, v in bolts.items():
    d.nset(k, v)
d.elsurf("MSIDE", S_master_side); d.elsurf("SSIDE", S_slave_side)
d.elsurf("MBOT", S_master_bot); d.elsurf("SBOT", S_slave_bot)
d.add(f"*SURFACE INTERACTION, NAME=IC\n*SURFACE BEHAVIOR, PRESSURE-OVERCLOSURE=LINEAR\n{KCONT:g},")
d.add("*CONTACT PAIR, INTERACTION=IC, TYPE=SURFACE TO SURFACE, ADJUST=0.6\nSSIDE, MSIDE")
d.add("*CONTACT PAIR, INTERACTION=IC, TYPE=SURFACE TO SURFACE\nSBOT, MBOT")
# anchors: vertical restraint at all 4 washer annuli; in-plane restraint is statically determinate (BOLT1: x,y; BOLT4: the
# component perpendicular to the BOLT1-BOLT4 diagonal) so that no spurious membrane forces are locked into the plate
# (anchors sit in D14 clearance holes for M12, they do not restrain in-plane strain between them).
d.add("*BOUNDARY\nNFIX, 3, 3\nBOLT1, 1, 2")
c45 = math.cos(math.radians(45))
d.add(f"*TRANSFORM, TYPE=R, NSET=BOLT4\n{c45:.8f}, {c45:.8f}, 0., {-c45:.8f}, {c45:.8f}, 0.")
d.add("*BOUNDARY\nBOLT4, 2, 2")
# rigid-body stabilisation of the pole (frictionless contact leaves y-translation and z-rotation free): the two pole-top nodes
# are held against displacement TRANSVERSE to the wind. By symmetry of the load these supports carry ~zero reaction.
ztop = max(xyz[k][2] for k in pnodes)
def topnode(px, py):
    return min((k for k in pnodes if abs(xyz[k][2] - ztop) < 1e-3), key=lambda k: (xyz[k][0] - px) ** 2 + (xyz[k][1] - py) ** 2)
if direction == "face":
    na, nb_ = topnode(-40, -40), topnode(40, -40)
    d.nset("NSTAB", [na, nb_])
    d.add("*BOUNDARY\nNSTAB, 2, 2")
else:
    na, nb_ = topnode(-40, -40), topnode(40, 40)
    d.nset("NSTAB", [na, nb_])
    c = math.cos(math.radians(45))
    d.add(f"*TRANSFORM, TYPE=R, NSET=NSTAB\n{c:.8f}, {c:.8f}, 0., {-c:.8f}, {c:.8f}, 0.")
    d.add("*BOUNDARY\nNSTAB, 2, 2")
d.add("*STEP, INC=300\n*STATIC\n0.5, 1.0, 1e-4, 1.0")
d.add("*CLOAD")
lines = []
for k, f in sorted(cload.items()):
    for c in range(3):
        if abs(f[c]) > 0:
            lines.append(f"{k}, {c+1}, {f[c]:.6e}")
d.add("\n".join(lines))
d.add("*NODE FILE\nU, RF\n*EL FILE\nS")
for k in bolts:
    d.add(f"*NODE PRINT, NSET={k}, TOTALS=ONLY\nRF")
d.add("*END STEP")
d.write(os.path.join(wd, "job.inp"))
# mesh info for post-processing
np.savez_compressed(os.path.join(wd, "meta.npz"), weld_nodes=np.array(sorted(wnodes)), pole_nodes=np.array(sorted(pnodes)))
json.dump(dict(stats, plate_top=PT, E_eq=E_eq, direction=direction, u=u.tolist(), bolt_xy=bolt_xy, items=items, F_pole=F_pole, Mg=Mg),
          open(os.path.join(wd, "meta.json"), "w"), indent=1)
gmsh.finalize()
print(json.dumps({k: v for k, v in stats.items() if k != "quality"}), flush=True)
print("quality", json.dumps(stats["quality"]), flush=True)
if solve:
    t, rc = fl.run_ccx("job", wd)
    print(f"ccx finished in {t:.0f} s rc={rc}", flush=True)
    json.dump(dict(stats, solve_s=t, rc=rc), open(os.path.join(wd, "meta_run.json"), "w"), indent=1)
