#!/usr/bin/env python3
"""Post-process CASE C (boom shell model). usage: post_c.py <results/C_...>"""
import sys, os, json, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import fea_lib as fl
import post_common as pc

wd = sys.argv[1]
meta = json.load(open(os.path.join(wd, "meta.json")))
fr = fl.parse_frd(os.path.join(wd, "job.frd"))
ids, xyz, disp, vm, sig = fl.frd_fields(fr)
XC, X1, XT = meta["XC"], meta["X1"], meta["XT"]
HZ, HY, T = meta["HZ"], meta["HY"], meta["T"]
E = fl.MATERIALS["AL6063T5"][0]
# thin-wall section of the shell model (mid-surface) -> I about horizontal (vertical bending) and vertical axis
If = 2 * (HY * T * (HZ / 2) ** 2 + HY * T ** 3 / 12.0); Iw = 2 * (T * HZ ** 3 / 12.0)
Iv = If + Iw                                   # vertical bending (about y)
Ih = 2 * (HZ * T * (HY / 2) ** 2 + HZ * T ** 3 / 12.0) + 2 * (T * HY ** 3 / 12.0)
Wv = Iv / (HZ / 2 + T / 2); Wh = Ih / (HY / 2 + T / 2)
A = 2 * T * (HY + HZ)
rho = 2.7e-9; g = 9810.0
w = rho * A * g                                # N/mm
def M_beam(x):
    if meta["mode"] == "vert":
        F = 50.0 + 0.15 * 9.81
        return F * (XT - x) + w * (X1 - x) ** 2 / 2.0
    return 50.0 * (XT - x)
W = Wv if meta["mode"] == "vert" else Wh
I = Iv if meta["mode"] == "vert" else Ih
# beam-theory tip deflection of a cantilever clamped at XC (point load at XT; distributed weight on XC..X1)
Lc = XT - XC
if meta["mode"] == "vert":
    F = 50.0 + 0.15 * 9.81
    d_beam = F * Lc ** 3 / (3 * E * I) + w * (X1 - XC) ** 4 / (8 * E * I) + w * (X1 - XC) * 0  # weight tail beyond X1 absent
    # point load at XT but weight ends at X1 -> use exact integral for the UDL with its end 30 mm short of the tip
    # delta_tip from UDL over [XC,X1] on a cantilever of length Lc: w a^2/(24EI) *(4 Lc... ) -> compute by numerical integration below
    xs = np.linspace(XC, X1, 4001); M = np.array([w * (X1 - x) ** 2 / 2 for x in xs])
    mt = (XT - xs)                                       # unit-load moment arm
    d_udl = np.trapezoid(M * mt, xs) / (E * I)
    d_beam = F * Lc ** 3 / (3 * E * I) + d_udl
else:
    d_beam = 50.0 * Lc ** 3 / (3 * E * I)
ref = meta["ref"]
import re
dat = open(os.path.join(wd, "job.dat")).read()
mm = re.search(r"displacements \(vx,vy,vz\) for set NREF.*?\n\s*\n\s*(\d+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)", dat, re.S)
uref = [float(mm.group(2)), float(mm.group(3)), float(mm.group(4))]
tip = abs(uref[2]) if meta["mode"] == "vert" else abs(uref[1])
out = dict(tag=meta["tag"], mode=meta["mode"], s=meta["s"], shell_elements=meta["elements"], shell_nodes=meta["nodes"],
           nodes_in_frd_expanded=int(len(fr["nodes"])), quality=meta["quality"])
i_raw = int(np.argmax(vm))
out["raw_max"] = float(vm[i_raw]); out["raw_xyz"] = xyz[i_raw].round(1).tolist()
# design reading: beyond the clamp-end disturbance zone (one section height 60 mm after the clamp edge)
far = xyz[:, 0] >= XC + 60.0
i_far = int(np.argmax(np.where(far, vm, -1)))
out["max_vm_beyond_XC_plus_60"] = float(vm[i_far]); out["max_vm_beyond_xyz"] = xyz[i_far].round(1).tolist()
# clamp-edge reading (first 15 mm outside the clamp)
edge = (xyz[:, 0] >= XC) & (xyz[:, 0] <= XC + 15.0)
i_e = int(np.argmax(np.where(edge, vm, -1)))
out["max_vm_clamp_edge_zone"] = float(vm[i_e]); out["clamp_edge_xyz"] = xyz[i_e].round(1).tolist()
for xs_ in (XC + 60.0, 400.0, 700.0):
    sl = np.abs(xyz[:, 0] - xs_) < 6.0
    out[f"sigma_xx_max_at_x{int(xs_)}_FE"] = float(np.abs(sig[sl, 0]).max())
    out[f"sigma_beam_at_x{int(xs_)}"] = float(M_beam(xs_) / W)
out["beam_M_at_XC_Nmm"] = float(M_beam(XC)); out["beam_sigma_at_XC_MPa"] = float(M_beam(XC) / W)
out["tip_disp_FE_mm"] = float(tip); out["tip_disp_beam_clamped_at_XC_mm"] = float(d_beam)
out["section_W_mm3"] = float(W)
comps, fid, fvals, _ = fr["last"]["FORC"]
fixed_nodes = set(int(k) for k, p in zip(ids, xyz) if p[0] <= XC + 1e-6 and abs(abs(p[2]) - (HZ / 2)) < 1e-6 or False)
out["max_disp_mm"] = float(np.linalg.norm(disp, axis=1).max())
json.dump(out, open(os.path.join(wd, "metrics.json"), "w"), indent=1)
np.savez_compressed(os.path.join(wd, "fields.npz"), ids=ids, xyz=xyz, disp=disp, vm=vm)
print(json.dumps(out, indent=1))
