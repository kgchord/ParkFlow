#!/usr/bin/env python3
"""
CASE B - RFID antenna tilt bracket (5 mm 5052-H32 yoke + tilt plate at 20 deg), CALCS.md section 3, recipe R2.

usage: case_b.py <h_mm> [--nosolve] [--freq]

Model
  * yoke = models/antenna_yoke_slotfix.step (repo yoke with the M6 arc slot mirrored - see FEA.md "CAD defect")
  * tilt plate = models/antenna_tilt_plate_20deg.step (repo plate rotated 20 deg about +x)
  * 4 steel spacer tubes (2 at the M8 pivot, 2 at the M6 lock bolt, OD16, 15 mm long between ear and cheek) are imprinted/bonded
    to the cheek and ear faces (conformal mesh): they represent the clamped bolt joints (no slip, CALCS slip FoS 30).
  * supports: all DOF fixed on the annulus D6.6..D12 (washer) on the top face of the yoke web at both M6 web holes.
  * load: reader as remote load at its CG (60 mm in front of the tilt-plate face) through a rigid body tied to the 4 reader bolt
    holes: 116.5 N wind (+y) and 29.4 N gravity (-z), values from calcs.py/CALCS.md section 3.
"""
import sys, os, io, json, math, contextlib
import numpy as np
import gmsh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fea_lib as fl

ROOT = os.path.abspath(os.path.join(HERE, ".."))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
h = float(args[0])
solve = "--nosolve" not in sys.argv
freq = "--freq" in sys.argv
support = "arm" if "--arm" in sys.argv else ("contact" if "--contact" in sys.argv else "washer")
tag = f"B_{support}_h{h:g}" + ("_freq" if freq else "")
wd = os.path.join(ROOT, "results", tag); os.makedirs(wd, exist_ok=True)

with contextlib.redirect_stdout(io.StringIO()):
    sys.path.insert(0, os.path.join(ROOT, "..", "calcs"))
    import calcs
R = calcs.pole_case(47, "80x80")
pd = R["pd"]
F_wind = pd * 1.3 * 0.26 * 0.26            # N  (calcs.py section 3: F_ant)
W_ant = 3.0 * calcs.G                      # N
TILT = 20.0
ca, sa = math.cos(math.radians(TILT)), math.sin(math.radians(TILT))
def rot(p):          # rotate about +x by TILT (as cq rotate in the repo STEP assembly)
    x, y, z = p
    return np.array([x, y * ca - z * sa, y * sa + z * ca])
def unrot(p):
    x, y, z = p
    return np.array([x, y * ca + z * sa, -y * sa + z * ca])

gmsh.initialize(); gmsh.option.setNumber("General.Terminal", 0)
gmsh.model.add(tag)
occ = gmsh.model.occ
imp = occ.importShapes(os.path.join(ROOT, "models", "repo_step_snapshot", "antenna_bracket_assy.step"))
occ.synchronize()
def bbx(v):
    return gmsh.model.getBoundingBox(3, v)
imp_t = [t for d, t in imp]
Y = [(3, t) for t in imp_t if abs((bbx(t)[3] - bbx(t)[0]) - 280.0) < 1.0][0]
T = [(3, t) for t in imp_t if abs((bbx(t)[3] - bbx(t)[0]) - 240.0) < 1.0][0]
lock_c = rot((0, 0, -50.0))[1:]          # (y,z) of M6 lock centre after tilt
sp = []
def tube(xa, xb, cy, cz, ro, ri):
    c1 = occ.addCylinder(xa, cy, cz, xb - xa, 0, 0, ro)
    c2 = occ.addCylinder(xa - 1, cy, cz, xb - xa + 2, 0, 0, ri)
    out, _ = occ.cut([(3, c1)], [(3, c2)])
    return out[0]
for s in (-1, 1):
    xa, xb = (120.0, 135.0) if s > 0 else (-135.0, -120.0)
    sp.append(tube(xa, xb, 0.0, 0.0, 8.0, 5.0))                 # pivot spacer OD16 / ID10
    sp.append(tube(xa, xb, lock_c[0], lock_c[1], 8.0, 4.0))     # lock spacer  OD16 / ID8
occ.synchronize()
objs = [Y, T] + sp
out, m = occ.fragment(objs[:1], objs[1:])
occ.synchronize()
arm_v = []
if support == "contact":
    # 40x40 arm modelled as two 15 mm strips either side of the 10 mm T-slot, bearing on the web top face (z=160); free-standing
    # bodies (NOT fragmented with the yoke) so that they only interact through CONTACT.  Arm top face fixed (rigid support).
    for y0 in (5.0, -20.0):
        arm_v.append(occ.addBox(-130.0, y0, 160.0, 260.0, 15.0, 40.0))
    occ.synchronize()
vols = [t for d, t in gmsh.model.getEntities(3)]
# classify volumes by mass centre
vinfo = {}
for v in vols:
    cx, cy, cz = occ.getCenterOfMass(3, v)
    vol = occ.getMass(3, v)
    vinfo[v] = (cx, cy, cz, vol)
yoke_v = [v for v in vols if abs((bbx(v)[3] - bbx(v)[0]) - 280.0) < 1.0][0]
tilt_v = [v for v in vols if abs((bbx(v)[3] - bbx(v)[0]) - 240.0) < 1.0 and v not in arm_v][0]
spacer_v = [v for v in vols if v not in (yoke_v, tilt_v) and v not in arm_v]
assert len(spacer_v) == 4, (vinfo, yoke_v, tilt_v)

ncurv = {6.0: 10, 4.0: 16, 3.0: 22}.get(h, int(round(60 / h)))
if support == "contact":
    gmsh.model.mesh.field.add("MathEval", 1)
    gmsh.model.mesh.field.setString(1, "F", f"Min(10, {h} + 0.6*Max(0, z-160.5))")
    gmsh.model.mesh.field.setAsBackgroundMesh(1)
    gmsh.option.setNumber("Mesh.MeshSizeMax", 10)
else:
    gmsh.option.setNumber("Mesh.MeshSizeMax", h)
gmsh.option.setNumber("Mesh.MeshSizeMin", 0.6)
gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", ncurv)
gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 1)
gmsh.option.setNumber("Mesh.Algorithm3D", 1)
gmsh.option.setNumber("Mesh.Optimize", 1)
gmsh.model.mesh.generate(3)
gmsh.model.mesh.setOrder(2)
try:
    gmsh.model.mesh.optimize("HighOrder")
except Exception:
    pass
qual = fl.mesh_quality(gmsh)
nodes, elems = fl.extract_tet10(gmsh, vols)
xyz = {k: np.array(v) for k, v in nodes.items()}
nel = {v: len(elems[v][0]) for v in vols}
stats = dict(tag=tag, h=h, nodes=len(nodes), elements=sum(nel.values()),
             elements_yoke=nel[yoke_v], elements_tilt=nel[tilt_v], elements_spacers=sum(nel[v] for v in spacer_v), quality=qual)

def box_surfs(x0, y0, z0, x1, y1, z1, e=0.02):
    return [t for dd, t in gmsh.model.getEntitiesInBoundingBox(x0 - e, y0 - e, z0 - e, x1 + e, y1 + e, z1 + e, 2)]
ynodes = set(elems[yoke_v][1].ravel().tolist()); tnodes = set(elems[tilt_v][1].ravel().tolist())
fmap = fl.tet_face_map(elems) if support == "contact" else None

# fixed: washer annulus on the web top face (z = 160) at x = +-80, y = 0
if support in ("washer", "contact"):      # recipe R2 literally: washer annulus D6.6..D12 around the 2 M6 web holes
    fixed = [k for k in ynodes if abs(xyz[k][2] - 160.0) < 1e-3 and
             any(3.3 - 1e-3 <= math.hypot(xyz[k][0] - sx * 80.0, xyz[k][1]) <= 6.0 + 1e-3 for sx in (-1, 1))]
else:                        # web top face clamped to the 40x40 arm underside: two 15 mm strips either side of the 10 mm T-slot
    fixed = [k for k in ynodes if abs(xyz[k][2] - 160.0) < 1e-3 and abs(xyz[k][0]) <= 130.0 + 1e-3 and
             5.0 - 1e-3 <= abs(xyz[k][1]) <= 20.0 + 1e-3]
# reader bolt holes: nodes of the tilt plate on the 4 bores (local frame)
bore = []
for k in tnodes:
    p = unrot(xyz[k])
    if -45.2 <= p[1] <= -39.8:
        for sx in (-50.0, 50.0):
            for sz in (-50.0, 50.0):
                if abs(math.hypot(p[0] - sx, p[2] - sz) - 3.3) < 0.02:
                    bore.append(k)
bore = sorted(set(bore))
cg = rot((0.0, -45.0 - 60.0, 0.0))
ref = max(nodes) + 1
nodes_out = dict(nodes); nodes_out[ref] = cg
rot_node = ref + 1; nodes_out[rot_node] = cg
mid_ref = None

d = fl.Deck(f"ParkFlow case B: antenna bracket, h={h}")
d.nodes(nodes_out)
d.elements("EL_YOKE", elems[yoke_v][0], elems[yoke_v][1])
d.elements("EL_TILT", elems[tilt_v][0], elems[tilt_v][1])
st = np.concatenate([elems[v][0] for v in spacer_v]); sn = np.concatenate([elems[v][1] for v in spacer_v])
d.elements("EL_SPACER", st, sn)
d.material("AL", "AL5052H32", density=True)
d.material("ST", "STEEL88", density=True)
d.add("*SOLID SECTION, ELSET=EL_YOKE, MATERIAL=AL\n*SOLID SECTION, ELSET=EL_TILT, MATERIAL=AL\n*SOLID SECTION, ELSET=EL_SPACER, MATERIAL=ST")
d.nset("NFIX", fixed); d.nset("NBORE", bore)
d.add(f"*NSET, NSET=NREF\n{ref}\n*NSET, NSET=NROT\n{rot_node}")
d.add(f"*RIGID BODY, NSET=NBORE, REF NODE={ref}, ROT NODE={rot_node}")
d.add("*BOUNDARY\nNFIX, 1, 3")
if support == "contact":
    at = np.concatenate([elems[v][0] for v in arm_v]); an = np.concatenate([elems[v][1] for v in arm_v])
    d.elements("EL_ARM", at, an)
    d.material("ALARM", "AL6063T5", density=True)
    d.add("*SOLID SECTION, ELSET=EL_ARM, MATERIAL=ALARM")
    anodes = set(an.ravel().tolist())
    d.nset("NARMTOP", [k for k in anodes if abs(xyz[k][2] - 200.0) < 1e-3])
    d.add("*BOUNDARY\nNARMTOP, 1, 3")
    web_s = [t for t in [x for x in box_surfs(-141, -31, 160, 141, 31, 160)] if yoke_v in gmsh.model.getAdjacencies(2, t)[0]]
    arm_s = [t for t in [x for x in box_surfs(-131, -21, 160, 131, 21, 160)] if any(a in gmsh.model.getAdjacencies(2, t)[0] for a in arm_v)]
    d.elsurf("SWEB", fl.surface_faces(gmsh, web_s, fmap)); d.elsurf("MARM", fl.surface_faces(gmsh, arm_s, fmap))
    d.add("*SURFACE INTERACTION, NAME=IC\n*SURFACE BEHAVIOR, PRESSURE-OVERCLOSURE=LINEAR\n1.0E5,")
    d.add("*CONTACT PAIR, INTERACTION=IC, TYPE=SURFACE TO SURFACE\nSWEB, MARM")
if freq:
    d.add(f"*ELEMENT, TYPE=MASS, ELSET=EMASS\n{max(elems[yoke_v][0].max(), elems[tilt_v][0].max(), st.max()) + 1}, {ref}\n*MASS, ELSET=EMASS\n3.0e-3")
    d.add("*STEP\n*FREQUENCY\n8\n*NODE FILE\nU\n*END STEP")
else:
    d.add("*STEP\n*STATIC")
    d.add(f"*CLOAD\n{ref}, 2, {F_wind:.6f}\n{ref}, 3, {-W_ant:.6f}")
    d.add("*NODE FILE\nU, RF\n*EL FILE\nS")
    d.add("*NODE PRINT, NSET=NFIX, TOTALS=ONLY\nRF")
    d.add("*END STEP")
d.write(os.path.join(wd, "job.inp"))
np.savez_compressed(os.path.join(wd, "meta.npz"), yoke_nodes=np.array(sorted(ynodes)), tilt_nodes=np.array(sorted(tnodes)))
json.dump(dict(stats, support=support, F_wind=F_wind, W=W_ant, cg=cg.tolist(), n_fixed=len(fixed), n_bore=len(bore), lock_c=list(lock_c), tilt=TILT),
          open(os.path.join(wd, "meta.json"), "w"), indent=1)
gmsh.finalize()
print(json.dumps({k: v for k, v in stats.items() if k != "quality"}), "fixed", len(fixed), "bore", len(bore), flush=True)
print("quality", json.dumps(stats["quality"]), flush=True)
if solve:
    t, rc = fl.run_ccx("job", wd)
    print(f"ccx finished in {t:.0f} s rc={rc}", flush=True)
    json.dump(dict(stats, solve_s=t, rc=rc), open(os.path.join(wd, "meta_run.json"), "w"), indent=1)
