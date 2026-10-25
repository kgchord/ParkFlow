#!/usr/bin/env python3
"""Post-process CASE A result dir: metrics.json (+ fields.npz).  usage: post_a.py <results/A_...>"""
import sys, os, json, math, re
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import fea_lib as fl
import post_common as pc

wd = sys.argv[1]
meta = json.load(open(os.path.join(wd, "meta.json")))
mz = np.load(os.path.join(wd, "meta.npz"))
pt = meta["plate_top"]; zs = pt + 150.0
u = np.array(meta["u"])
fr = fl.parse_frd(os.path.join(wd, "job.frd"))
ids, xyz, disp, vm, sig = fl.frd_fields(fr)
idpos = {int(k): j for j, k in enumerate(ids)}
isw = np.isin(ids, mz["weld_nodes"]); isp = np.isin(ids, mz["pole_nodes"])

# ---------------- singular / non-design features (3D polylines and circles)
Rs = lambda ang: np.array([[math.cos(ang), -math.sin(ang), 0], [math.sin(ang), math.cos(ang), 0], [0, 0, 1]])
def P3(x, y, z): return np.array([x, y, z], float)
so, si = 46.5, 40.5
D_PLATE, D_LOC = 8.0, 3.0           # 0.5 x plate thickness (16 mm); 0.5 x cheek/gusset thickness (6 mm)
segs_pl = []; segs_loc = []; circ_pl = []
for k in range(4):
    R = Rs(k * math.pi / 2)
    # socket outer footprint (weld toe on plate top), one side per k
    segs_pl.append((R @ P3(so, -so, pt), R @ P3(so, so, pt)))
    # gusset footprint outline on plate top (3 sides) and vertical gusset/cheek junction lines
    segs_pl += [(R @ P3(so, -3, pt), R @ P3(so + 74, -3, pt)), (R @ P3(so, 3, pt), R @ P3(so + 74, 3, pt)),
                (R @ P3(so + 74, -3, pt), R @ P3(so + 74, 3, pt))]
    segs_loc += [(R @ P3(so, -3, pt), R @ P3(so, -3, pt + 120)), (R @ P3(so, 3, pt), R @ P3(so, 3, pt + 120))]
    # contact edges: socket top inner rim, inner base edge, inner vertical corners
    segs_loc.append((R @ P3(si, -si, zs), R @ P3(si, si, zs)))
    segs_loc.append((R @ P3(si, -si, pt), R @ P3(si, si, pt)))
    segs_loc.append((R @ P3(si, -si, pt), R @ P3(si, -si, zs)))
for bx, by in meta["bolt_xy"]:
    circ_pl += [(P3(bx, by, pt), 12.0, P3(0, 0, 1)), (P3(bx, by, pt), 7.0, P3(0, 0, 1))]
# M10 cross-bolt holes D11 in the cheeks (z=131 in the +-x cheeks, z=61 in the +-y cheeks): as drawn they run into the gusset
# on the same centre-line (CAD interference, see FEA.md) -> hole edges are excluded from the design reading
hole_axes = [(P3(sx * 40.5, 0, pt + 115), P3(sx * 46.5, 0, pt + 115)) for sx in (-1, 1)] + \
            [(P3(0, sy * 40.5, pt + 45), P3(0, sy * 46.5, pt + 45)) for sy in (-1, 1)]
d_hole = pc.dist_segments(xyz, hole_axes) - 5.5
d_pl = np.minimum(pc.dist_segments(xyz, segs_pl), pc.dist_circles(xyz, circ_pl))
d_loc = pc.dist_segments(xyz, segs_loc)
excl = (d_pl < D_PLATE) | (d_loc < D_LOC) | (d_hole < D_LOC)

# region classification of weldment nodes
ax, ay, az = np.abs(xyz[:, 0]), np.abs(xyz[:, 1]), xyz[:, 2]
outside = np.maximum(ax, ay) > so + 1e-3
region = np.full(len(ids), "", dtype=object)
region[isw & (az <= pt + 1e-3) & ((az < pt - 1e-3) | outside)] = "base plate"
region[isw & (az > pt + 1e-3) & outside] = "gusset"
region[isw & (region == "")] = "socket cheek"
region[isp] = "pole"

def feature_name(p):
    """named feature of the point nearest to a known detail (for the table)"""
    cands = []
    for name, segs, circs in (
            ("anchor washer edge (support)", [], circ_pl),
            ("plate-socket weld toe", [s for s in segs_pl[0::4]], []),
            ("plate-gusset weld toe", [s for i, s in enumerate(segs_pl) if i % 4 in (1, 2, 3)], []),
            ("gusset-cheek junction line", segs_loc[0::5] + segs_loc[1::5], []),
            ("socket top rim (pole bearing / contact edge)", segs_loc[2::5], []),
            ("socket inner base edge (pole bearing)", segs_loc[3::5], []),
            ("socket inner corner", segs_loc[4::5], []),
            ("M10 cross-bolt hole edge (blocked by gusset in CAD)", hole_axes, [])):
        d = pc.dist_segments(p[None, :], segs)[0] if segs else np.inf
        if circs:
            d = min(d, pc.dist_circles(p[None, :], circs)[0])
        cands.append((d, name))
    d, name = min(cands)
    if d > 12.0:
        r = "gusset free edge/body" if (max(abs(p[0]), abs(p[1])) > so and p[2] > pt + 1e-3) else (
            "plate bulk" if p[2] <= pt + 1e-3 else "socket cheek body")
        return f"{r} ({d:.0f} mm from nearest weld/constraint feature {name.split(' (')[0]})"
    return f"{name} ({d:.1f} mm)"

out = dict(tag=meta["tag"], direction=meta["direction"], plate_t=pt, nodes=meta["nodes"], elements=meta["elements"],
           elements_weldment=meta["elements_weldment"], quality_min_SICN=meta["quality"]["minSICN"]["min"],
           quality_mean_SICN=meta["quality"]["minSICN"]["mean"])
res = {}
for reg in ("base plate", "gusset", "socket cheek"):
    m = region == reg
    i_raw = pc.top_k(vm, m)[0]
    i_des = pc.top_k(vm, m & ~excl)[0]
    res[reg] = dict(raw_max=float(vm[i_raw]), raw_xyz=xyz[i_raw].round(1).tolist(), raw_feature=feature_name(xyz[i_raw]),
                    design_max=float(vm[i_des]), design_xyz=xyz[i_des].round(1).tolist(), design_feature=feature_name(xyz[i_des]))
mw = isw
i_raw = pc.top_k(vm, mw)[0]; i_des = pc.top_k(vm, mw & ~excl)[0]
out["weldment_raw_max"] = float(vm[i_raw]); out["weldment_raw_xyz"] = xyz[i_raw].round(1).tolist()
out["weldment_raw_feature"] = feature_name(xyz[i_raw]); out["weldment_raw_region"] = region[i_raw]
out["weldment_design_max"] = float(vm[i_des]); out["weldment_design_xyz"] = xyz[i_des].round(1).tolist()
out["weldment_design_feature"] = feature_name(xyz[i_des]); out["weldment_design_region"] = region[i_des]
out["regions"] = res
out["excluded_node_fraction_weldment"] = float((excl & isw).sum() / isw.sum())

# displacement: pole top along wind, magnitude max
top = np.argmax(np.where(isp, xyz[:, 2], -1e9))
ztop = xyz[top, 2]
tops = isp & (xyz[:, 2] > ztop - 1e-3)
out["pole_top_disp_along_wind_mm"] = float((disp[tops, :2] @ u).mean())
out["max_disp_mm"] = float(np.linalg.norm(disp, axis=1).max())
# displacement of the socket top (rigid-body+base compliance contribution): mean over pole nodes at z = zs
s_sel = isp & (np.abs(xyz[:, 2] - zs) < 1e-3)
out["disp_along_wind_at_socket_top_mm"] = float((disp[s_sel, :2] @ u).mean())

# bolt reactions
comps, fid, fvals, _ = fr["last"]["FORC"]
fmap = {int(k): v for k, v in zip(fid, fvals)}
bolt_T = []
for bx, by in meta["bolt_xy"]:
    sel = [int(k) for k, p in zip(ids, xyz) if abs(p[2] - pt) < 1e-3 and 6.99 <= math.hypot(p[0] - bx, p[1] - by) <= 12.001]
    f = np.sum([fmap[k][:3] for k in sel], axis=0)
    bolt_T.append(f.tolist())
out["bolt_reaction_N"] = bolt_T
out["bolt_max_tension_kN"] = float(max(-b[2] for b in bolt_T) / 1000.0)     # reaction of fixed support on plate: negative z = bolt pulls plate down = bolt tension
out["bolt_max_compression_kN"] = float(max(b[2] for b in bolt_T) / 1000.0)
allrf = np.sum([fmap[int(k)][:3] for k in ids if int(k) in fmap and abs(xyz[idpos[int(k)], 2] - pt) < 1e-3 and
                any(6.99 <= math.hypot(xyz[idpos[int(k)], 0] - bx, xyz[idpos[int(k)], 1] - by) <= 12.001 for bx, by in meta["bolt_xy"])], axis=0)
out["support_reaction_sum_N"] = allrf.tolist()

# pole section stress away from the base (equivalent extrusion stress), at zc above plate top
E_true = fl.MATERIALS["AL6063T5"][0]
zc = 600.0
sel = isp & (np.abs(xyz[:, 2] - pt - zc) < 25.0)
out["pole_axial_stress_FE_solid_MPa"] = float(np.abs(sig[sel, 2]).max())
out["pole_axial_stress_equiv_extrusion_MPa"] = float(np.abs(sig[sel, 2]).max() * E_true / meta["E_eq"])
items = meta["items"]; Fp = meta["F_pole"]; L = 2400.0; Mg = meta["Mg"]
Mz = sum(F * (z - zc) for (_, F, z) in items if z > zc) / 1000.0 + Fp * (L - zc) ** 2 / (2 * L) / 1000.0 + Mg / 1000.0
out["pole_section_zc_mm"] = zc
out["hand_moment_at_zc_Nm"] = Mz
out["hand_pole_stress_at_zc_MPa"] = Mz / 27.5e-6 / 1e6
json.dump(out, open(os.path.join(wd, "metrics.json"), "w"), indent=1)
np.savez_compressed(os.path.join(wd, "fields.npz"), ids=ids, xyz=xyz, disp=disp, vm=vm, excl=excl, region=region.astype(str))
print(json.dumps({k: v for k, v in out.items() if k not in ("regions",)}, indent=1))
for k, v in res.items():
    print(k, json.dumps(v))
