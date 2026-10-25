#!/usr/bin/env python3
"""Post-process CASE B (antenna bracket).  usage: post_b.py <results/B_...>   (static result)"""
import sys, os, json, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import fea_lib as fl
import post_common as pc

wd = sys.argv[1]
meta = json.load(open(os.path.join(wd, "meta.json")))
mz = np.load(os.path.join(wd, "meta.npz"))
fr = fl.parse_frd(os.path.join(wd, "job.frd"))
ids, xyz, disp, vm, sig = fl.frd_fields(fr)
isy = np.isin(ids, mz["yoke_nodes"]); ist = np.isin(ids, mz["tilt_nodes"])
ca, sa = math.cos(math.radians(meta["tilt"])), math.sin(math.radians(meta["tilt"]))
def rot(p):
    x, y, z = p
    return np.array([x, y * ca - z * sa, y * sa + z * ca])
X = np.array([1.0, 0, 0]); lc = meta["lock_c"]
D_T = 5.0        # 1.0 x sheet thickness: exclusion around constraint edges and bonded (washer/spacer) patch edges
D_SHARP = 5.0    # 1.0 x t around the sharp (un-radiused) ear/face inner corner of the tilt plate (CAD simplification)
support = meta.get("support", "washer")
circ = [(np.array([sx * 80.0, 0, 160.0]), r, np.array([0, 0, 1.0])) for sx in (-1, 1) for r in (3.3, 6.0)]
arm_edges = [(np.array([-130.0, sy * yy, 160.0]), np.array([130.0, sy * yy, 160.0])) for sy in (-1, 1) for yy in (5.0, 20.0)] + \
            [(np.array([sx * 130.0, -20.0, 160.0]), np.array([sx * 130.0, -5.0, 160.0])) for sx in (-1, 1)] + \
            [(np.array([sx * 130.0, 5.0, 160.0]), np.array([sx * 130.0, 20.0, 160.0])) for sx in (-1, 1)]
for sx in (-1, 1):
    for xf in (120.0, 135.0):
        circ.append((np.array([sx * xf, 0, 0]), 8.0, X)); circ.append((np.array([sx * xf, 0, 0]), 5.0, X))
        circ.append((np.array([sx * xf, lc[0], lc[1]]), 8.0, X)); circ.append((np.array([sx * xf, lc[0], lc[1]]), 4.0, X))
D_SUP = 10.0     # 2.0 x t around idealised support patches (fixed washer annuli / fixed arm strips): St Venant zone
d_wash = pc.dist_circles(xyz, circ[:4])
d_spacer = pc.dist_circles(xyz, circ[4:])
# reader bolt-hole rigid patches: distance to the bore axis
axes = []
for sx in (-50.0, 50.0):
    for sz in (-50.0, 50.0):
        axes.append((rot((sx, -45.0, sz)), rot((sx, -40.0, sz))))
d_bore = pc.dist_segments(xyz, axes) - 3.3
d_sharp = pc.dist_segments(xyz, [(rot((sgn * 115.0, -40.0, -50.0)), rot((sgn * 115.0, -40.0, 50.0))) for sgn in (-1, 1)])
d_arm = pc.dist_segments(xyz, arm_edges)
excl = (d_spacer < D_T) | (d_bore < 4.0) | (d_sharp < D_SHARP)
if support in ("washer", "contact"):
    excl |= (d_wash < D_SUP)
if support == "contact":
    excl |= (d_arm < D_T)
if support == "arm":
    excl |= (d_arm < D_SUP)

def feature_name(p, part):
    cand = []
    cand.append((pc.dist_circles(p[None], circ[:4])[0], "web washer support edge"))
    cand.append((pc.dist_circles(p[None], [c for c in circ[4:] if abs(c[0][1]) < 1e-9 and abs(c[0][2]) < 1e-9])[0], "pivot spacer bonded edge"))
    cand.append((pc.dist_circles(p[None], [c for c in circ[4:] if abs(c[0][1]) > 1e-9])[0], "lock spacer bonded edge"))
    cand.append((pc.dist_segments(p[None], axes)[0] - 3.3, "reader bolt-hole rigid patch"))
    if part == "tilt plate":
        cand.append((pc.dist_segments(p[None], [(rot((sgn * 115.0, -40.0, -50.0)), rot((sgn * 115.0, -40.0, 50.0))) for sgn in (-1, 1)])[0],
                     "tilt-plate ear/face inner corner (sharp in model, R5 bend in real part)"))
    else:
        for pe in (np.array([0, -50.0]), np.array([25.0, -43.30])):
            d = math.hypot(p[1] - pe[0], p[2] - pe[1]) if False else math.hypot(p[1] - pe[0], p[2] - pe[1])
        d_slot_a = math.hypot(p[1] - 0.0, p[2] + 50.0); d_slot_b = math.hypot(p[1] - 25.0, p[2] + 43.3)
        cand.append((min(d_slot_a, d_slot_b) - 3.3, "M6 arc-slot end"))
        if 135.0 <= abs(p[0]) <= 140.0 and p[2] > 138.0:
            cand.append((0.0, "yoke bend root (web-cheek, R5/R10)"))
        elif p[2] > 154.0:
            cand.append((10.0, "yoke web"))
    d, nm = min(cand)
    if d < 10.0:
        return f"{nm} ({max(d,0):.1f} mm)"
    return f"{part} body"

out = dict(tag=meta["tag"], support=support, h=meta["h"], nodes=meta["nodes"], elements=meta["elements"],
           quality_min_SICN=meta["quality"]["minSICN"]["min"], quality_mean_SICN=meta["quality"]["minSICN"]["mean"],
           quality_n_SICN_below_0p1=meta["quality"]["minSICN"]["n_lt_0p1"])
regs = {}
for name, m in (("yoke", isy), ("tilt plate", ist)):
    ir = pc.top_k(vm, m)[0]; idd = pc.top_k(vm, m & ~excl)[0]
    regs[name] = dict(raw_max=float(vm[ir]), raw_xyz=xyz[ir].round(1).tolist(), raw_feature=feature_name(xyz[ir], name),
                      design_max=float(vm[idd]), design_xyz=xyz[idd].round(1).tolist(), design_feature=feature_name(xyz[idd], name))
out["regions"] = regs
bracket = isy | ist
ir = pc.top_k(vm, bracket)[0]; idd = pc.top_k(vm, bracket & ~excl)[0]
out["raw_max"] = float(vm[ir]); out["raw_xyz"] = xyz[ir].round(1).tolist(); out["raw_part"] = "yoke" if isy[ir] else "tilt plate"
out["raw_feature"] = feature_name(xyz[ir], out["raw_part"])
out["design_max"] = float(vm[idd]); out["design_xyz"] = xyz[idd].round(1).tolist(); out["design_part"] = "yoke" if isy[idd] else "tilt plate"
out["design_feature"] = feature_name(xyz[idd], out["design_part"])
# yoke bend-root reading (true radii, no singularity): max over yoke nodes in the bend zone
bend = isy & (xyz[:, 2] > 138.0) & (np.abs(xyz[:, 0]) >= 134.0) & ~excl
ib = pc.top_k(vm, bend)[0]
out["yoke_bend_root_max"] = float(vm[ib]); out["yoke_bend_root_xyz"] = xyz[ib].round(1).tolist()
out["excluded_node_fraction"] = float((excl & bracket).sum() / bracket.sum())
# displacement of the reader CG (rigid body reference node)
cg_id = max(fr["nodes"])
dmap = dict(zip(*[fr["last"]["DISP"][1], fr["last"]["DISP"][2]]))
# the reference nodes are not in the STRESS block; get from DISP block ids
d_ids = fr["last"]["DISP"][1]; d_vals = fr["last"]["DISP"][2]
ref_candidates = [i for i in d_ids if i > ids.max() - 5 and i not in set(ids)]
if ref_candidates:
    rid = min(ref_candidates)
    uref = d_vals[list(d_ids).index(rid)][:3]
else:
    uref = disp[np.isin(ids, mz["tilt_nodes"])][0]
out["reader_cg_disp_mm"] = [float(x) for x in uref]; out["reader_cg_disp_mag_mm"] = float(np.linalg.norm(uref))
out["max_disp_mm"] = float(np.linalg.norm(disp, axis=1).max())
comps, fid, fvals, _ = fr["last"]["FORC"]
fixed_ids = [int(k) for k in ids if abs(fr["nodes"][int(k)][2] - 160.0) < 1e-3 and (
             (support in ("washer", "contact") and any(3.3 - 1e-3 <= math.hypot(fr["nodes"][int(k)][0] - sx * 80.0, fr["nodes"][int(k)][1]) <= 6.0 + 1e-3 for sx in (-1, 1))) or
             (support == "arm" and abs(fr["nodes"][int(k)][0]) <= 130.0 + 1e-3 and 5.0 - 1e-3 <= abs(fr["nodes"][int(k)][1]) <= 20.0 + 1e-3))]
fm = {int(k): v for k, v in zip(fid, fvals)}
out["support_reaction_sum_N"] = np.sum([fm[k][:3] for k in fixed_ids], axis=0).tolist()
json.dump(out, open(os.path.join(wd, "metrics.json"), "w"), indent=1)
np.savez_compressed(os.path.join(wd, "fields.npz"), ids=ids, xyz=xyz, disp=disp, vm=vm, excl=excl, isy=isy, ist=ist)
print(json.dumps({k: v for k, v in out.items()}, indent=1))
