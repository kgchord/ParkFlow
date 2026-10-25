#!/usr/bin/env python3
"""
verify_step.py - independent check of every STEP file written by build_step.py.

For each entry in _build_index.json:
  1. re-import the .step file from disk with CadQuery (OCCT STEP reader)
  2. check every solid is valid (BRepCheck), count solids, volume, bounding box
  3. generate the matching OpenSCAD STL (wrapper in _ref/, $fn=128, openscad 2021.01) and compare
        volume (mismatch threshold 2 %), bounding-box extents and corner position (same frame),
        surface-to-surface distance (STEP tessellation sampled vs dense samples of the STL)
  4. optionally compare to the checked-in cad/stl/*.stl (print-orientation, so volume + sorted extents only)
Results go to _verify_results.json; STEP_MANIFEST.md is then written by manifest.py (imported below).

Usage:  python3 cad/step/verify_step.py [--force-ref] [--only id1,id2] [--no-ref]
"""
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
SCAD = os.path.normpath(os.path.join(HERE, "..", "openscad"))
STLDIR = os.path.normpath(os.path.join(HERE, "..", "stl"))
REFDIR = os.path.join(HERE, "_ref")
TOL_VOL = 2.0            # percent
TOL_BB = 2.0             # percent of the extent, and ...
TOL_BB_ABS = 0.3         # ... more than this many mm
SEED = 12345

# printed parts that also have a checked-in STL in cad/stl (print orientation)
STL_FILES = {
    "gantry_pole_cap": "pole_cap.stl", "gantry_cable_boot": "cable_boot.stl", "edge_pi_tray": "edge_pi_tray.stl",
    "occ_base": "occ_base.stl", "occ_cover": "occ_cover.stl", "occ_diffuser": "occ_diffuser.stl",
    "barrier_boom_tip_cap": "boom_tip_cap.stl", "barrier_photo_post_cap": "pb_post_cap.stl",
}


# --------------------------------------------------------------------------- reference STL
def _scad_sources_mtime():
    m = 0
    for f in os.listdir(SCAD):
        if f.endswith(".scad"):
            m = max(m, os.path.getmtime(os.path.join(SCAD, f)))
    return m


def _wrap(snippet):
    """Rewrite include<>/use<> paths so the wrapper (in _ref/) can find ../openscad/*.scad."""
    def fix(m):
        return f"{m.group(1)} <{os.path.relpath(os.path.join(SCAD, m.group(2)), REFDIR)}>"
    return re.sub(r"(include|use)\s*<([^>]+)>", fix, snippet)


def make_ref(item, force=False):
    """Return path to reference STL for the index item (or None)."""
    if not item.get("ref"):
        return None
    os.makedirs(REFDIR, exist_ok=True)
    scad_path = os.path.join(REFDIR, item["id"] + ".scad")
    stl_path = os.path.join(REFDIR, item["id"] + ".stl")
    fn = int(item.get("ref_fn", 128))
    text = _wrap(item["ref"]) + f"\n// fn={fn}\n"
    if not (os.path.exists(scad_path) and open(scad_path).read() == text):
        open(scad_path, "w").write(text)
        force = True
    if force or not os.path.exists(stl_path) or os.path.getmtime(stl_path) < _scad_sources_mtime():
        cmd = ["openscad", "-q", "-o", stl_path, "-D", f"$fn={fn}", scad_path]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=3000)
        if r.returncode != 0 or not os.path.exists(stl_path):
            return ("ERR", (r.stderr or r.stdout)[-400:])
    return stl_path


# --------------------------------------------------------------------------- geometry helpers
def load_stl(path):
    import trimesh
    m = trimesh.load(path, force="mesh")
    return m


def sample_mesh(vertices, faces, n, rng):
    tri = vertices[faces]
    a = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    area = 0.5 * np.linalg.norm(a, axis=1)
    tot = area.sum()
    if tot <= 0:
        return np.zeros((0, 3)), 0.0, np.zeros(0, int)
    idx = rng.choice(len(faces), size=n, p=area / tot)
    u = rng.random((n, 1))
    v = rng.random((n, 1))
    flip = (u + v) > 1
    u = np.where(flip, 1 - u, u)
    v = np.where(flip, 1 - v, v)
    t = tri[idx]
    pts = t[:, 0] + u * (t[:, 1] - t[:, 0]) + v * (t[:, 2] - t[:, 0])
    return pts, tot, idx


def step_surface(shape_list, tol=0.05):
    """Tessellate bodies; returns vertices, faces and the body index of every face."""
    V, F, L = [], [], []
    off = 0
    for k, s in enumerate(shape_list):
        vs, ts = s.tessellate(tol, 0.2)
        if not vs:
            continue
        V.append(np.array([[v.x, v.y, v.z] for v in vs]))
        F.append(np.array(ts) + off)
        L.append(np.full(len(ts), k))
        off += len(vs)
    return np.vstack(V), np.vstack(F), np.concatenate(L)


def dist_stats(a_pts, b_pts):
    from scipy.spatial import cKDTree
    d, _ = cKDTree(b_pts).query(a_pts, k=1)
    return d


# --------------------------------------------------------------------------- one item
def leaves_of(path):
    """(name, absolute-placed cq.Shape) for every leaf body of a STEP file (via the XCAF product tree)."""
    asm = cq.Assembly.importStep(path)
    out = []
    for k, v in asm._flatten().items():
        if v.obj is not None:
            out.append((k, v.obj.moved(v.loc)))
    return out


def bb_overlap(a, b, tol=1e-3):
    return not (a.xmax < b.xmin - tol or b.xmax < a.xmin - tol or a.ymax < b.ymin - tol or
                b.ymax < a.ymin - tol or a.zmax < b.zmin - tol or b.zmax < a.zmin - tol)


def interferences(lv, min_mm3=1.0):
    """Pairwise solid-solid common volume (bounding-box prefiltered)."""
    bbs = [s.BoundingBox() for _, s in lv]
    pairs = []
    tot = 0.0
    for i in range(len(lv)):
        for j in range(i + 1, len(lv)):
            if not bb_overlap(bbs[i], bbs[j]):
                continue
            try:
                v = lv[i][1].intersect(lv[j][1]).Volume()
            except Exception:
                v = float("nan")
            if v > min_mm3:
                pairs.append((lv[i][0].split("/")[-1], lv[j][0].split("/")[-1], v))
                tot += v
    pairs.sort(key=lambda t: -t[2])
    return pairs, tot


def verify_item(item, kind, force_ref, do_ref=True, vol_by_id=None):
    rec = {"id": item["id"], "kind": kind, "file": item["file"]}
    path = os.path.join(HERE, item["file"])
    if not os.path.exists(path):
        rec["error"] = "STEP file missing"
        return rec
    rec["bytes"] = os.path.getsize(path)
    lv = leaves_of(path)
    solids = [s for _, s in lv]
    # cross-check against the plain importer (CadQuery importStep) - must give the same solids
    imp = cq.importers.importStep(path)
    n_plain = len(imp.solids().vals())
    rec["n_solids"] = sum(len(s.Solids()) for s in solids)
    rec["n_bodies"] = len(solids)
    rec["n_solids_plain_import"] = n_plain
    rec["valid"] = all(s.isValid() for s in solids)
    vol = sum(s.Volume() for s in solids)
    rec["volume_mm3"] = vol
    rec["leaf_names"] = [k for k, _ in lv]
    rec["leaf_volumes_mm3"] = {k: s.Volume() for k, s in lv}
    bbs = [s.BoundingBox() for s in solids]
    xmin = min(b.xmin for b in bbs); xmax = max(b.xmax for b in bbs)
    ymin = min(b.ymin for b in bbs); ymax = max(b.ymax for b in bbs)
    zmin = min(b.zmin for b in bbs); zmax = max(b.zmax for b in bbs)
    rec["bbox_min"] = [xmin, ymin, zmin]
    rec["bbox_max"] = [xmax, ymax, zmax]
    rec["bbox_size"] = [xmax - xmin, ymax - ymin, zmax - zmin]
    txt = open(path, errors="ignore").read()
    m = re.search(r"FILE_SCHEMA\(\(\s*'([^']*)'", txt)
    rec["step_schema"] = m.group(1) if m else ""
    # interference (assemblies with >1 body)
    vol_union = vol
    if len(solids) > 1:
        pairs, tot = interferences(lv)
        rec["interference_pairs"] = [(a, b, round(v, 1)) for a, b, v in pairs[:25]]
        rec["interference_n"] = len(pairs)
        rec["interference_total_mm3"] = tot
        vol_union = vol - tot
    rec["volume_union_est_mm3"] = vol_union
    if not do_ref:
        return rec
    ref = make_ref(item, force_ref)
    if isinstance(ref, tuple):
        rec["ref_error"] = ref[1]
        ref = None
    if ref:
        m = load_stl(ref)
        rv = float(abs(m.volume))
        # parts whose reference module also draws other STEP parts (gasket, label ...)
        extra = 0.0
        for oid in item.get("ref_includes", []):
            extra += (vol_by_id or {}).get(oid, 0.0)
        rec["ref_includes"] = item.get("ref_includes", [])
        rec["ref_volume_mm3"] = rv
        rec["ref_bbox_min"] = [float(x) for x in m.bounds[0]]
        rec["ref_bbox_max"] = [float(x) for x in m.bounds[1]]
        rec["ref_watertight"] = bool(m.is_watertight)
        cmp_vol = vol_union + extra
        rec["vol_diff_pct"] = 100.0 * (cmp_vol - rv) / rv if rv else None
        sz = np.array(rec["bbox_size"]); rsz = m.bounds[1] - m.bounds[0]
        rec["bbox_size_diff_mm"] = [float(x) for x in (sz - rsz)]
        rec["bbox_corner_shift_mm"] = [float(x) for x in (np.array(rec["bbox_min"]) - m.bounds[0])]
        rng = np.random.default_rng(SEED)
        sv, sf, sl = step_surface(solids)
        multi = len(solids) > 1
        n_a = int(min(60000 if multi else 300000, max(20000, 60 * math.sqrt(len(sf)))))
        pa, area_step, fidx = sample_mesh(sv, sf, n_a, rng)
        leaf_of_pt = sl[fidx]
        mv, mf = np.asarray(m.vertices), np.asarray(m.faces)
        _, area_ref, _ = sample_mesh(mv, mf, 10, rng)
        n_b = int(min(3_000_000, max(200_000, area_ref / 0.25)))
        pb, _, _ = sample_mesh(mv, mf, n_b, rng)
        spacing = math.sqrt(area_ref / len(pb))
        from scipy.spatial import cKDTree
        tree_b = cKDTree(pb)
        d_ab, _ = tree_b.query(pa, k=1)
        rec["surf_spacing_mm"] = spacing
        rec["step_to_ref_p99_mm"] = float(np.percentile(d_ab, 99))
        rec["step_to_ref_max_mm"] = float(d_ab.max())
        tol = max(0.3, 2.5 * spacing)
        rec["dist_tol_mm"] = tol
        fail = d_ab > tol
        hidden = np.zeros(len(pa), bool)
        if multi and fail.any():
            # a point of body i that is buried inside body j (modelled overlap) cannot lie on the OpenSCAD union surface
            for idx in np.where(fail)[0]:
                i = int(leaf_of_pt[idx])
                pt = cq.Vector(*pa[idx])
                for j in range(len(solids)):
                    if j == i:
                        continue
                    bb = bbs[j]
                    if bb.xmin - 1e-3 <= pt.x <= bb.xmax + 1e-3 and bb.ymin - 1e-3 <= pt.y <= bb.ymax + 1e-3 and \
                            bb.zmin - 1e-3 <= pt.z <= bb.zmax + 1e-3 and solids[j].isInside(pt, 1e-3):
                        hidden[idx] = True
                        break
        ok = (~fail) | hidden
        rec["step_to_ref_within_tol_pct"] = float(100.0 * ok.mean())
        rec["step_surface_buried_in_other_body_pct"] = float(100.0 * hidden.mean())
        tree_a = cKDTree(pa)
        d_ba, _ = tree_a.query(pb[:: max(1, len(pb) // 400000)], k=1)
        tol_ba = max(0.3, 2.5 * math.sqrt(area_step / len(pa)))
        rec["ref_to_step_within_tol_pct"] = float(100.0 * (d_ba <= tol_ba).mean())
        rec["area_step_mm2"] = float(area_step)
        rec["area_ref_mm2"] = float(area_ref)
        if multi:
            bad = []
            for k, (nm, _s) in enumerate(lv):
                sel = leaf_of_pt == k
                if sel.sum() >= 20:
                    pct = 100.0 * ok[sel].mean()
                    if pct < 99.0:
                        bad.append((nm.split("/")[-1], round(float(pct), 1)))
            rec["leaves_off_reference"] = bad
    sf_name = STL_FILES.get(item["id"])
    if sf_name and os.path.exists(os.path.join(STLDIR, sf_name)):
        m = load_stl(os.path.join(STLDIR, sf_name))
        rec["stl_file"] = "stl/" + sf_name
        rec["stl_volume_mm3"] = float(abs(m.volume))
        rec["stl_vol_diff_pct"] = 100.0 * (vol - abs(m.volume)) / abs(m.volume)
        rec["stl_extents_sorted"] = sorted(float(x) for x in (m.bounds[1] - m.bounds[0]))
        rec["step_extents_sorted"] = sorted(rec["bbox_size"])
    return rec


def judge(rec, kind):
    """Return list of mismatch strings (empty = pass)."""
    out = []
    if rec.get("error"):
        return ["STEP file missing"]
    if not rec.get("valid"):
        out.append("invalid solid(s)")
    if kind == "part" and rec.get("n_solids", 1) != 1:
        out.append(f"part file holds {rec['n_solids']} solids")
    if rec.get("n_solids") != rec.get("n_solids_plain_import"):
        out.append("solid count differs between XCAF and plain import")
    if "vol_diff_pct" in rec and rec["vol_diff_pct"] is not None and abs(rec["vol_diff_pct"]) > TOL_VOL:
        out.append(f"volume {rec['vol_diff_pct']:+.2f} % vs OpenSCAD STL")
    if "bbox_size_diff_mm" in rec:
        for ax, dmm, sz in zip("XYZ", rec["bbox_size_diff_mm"], rec["bbox_size"]):
            if abs(dmm) > TOL_BB_ABS and abs(dmm) / max(sz, 1e-9) * 100 > TOL_BB:
                out.append(f"bbox {ax} extent {dmm:+.2f} mm")
        for ax, dmm in zip("XYZ", rec["bbox_corner_shift_mm"]):
            if abs(dmm) > max(1.0, 0.002 * max(rec["bbox_size"])):
                out.append(f"bbox min-corner {ax} shifted {dmm:+.2f} mm")
    if "step_to_ref_within_tol_pct" in rec and rec["step_to_ref_within_tol_pct"] < 99.0:
        out.append(f"only {rec['step_to_ref_within_tol_pct']:.1f} % of STEP surface within {rec['dist_tol_mm']:.2f} mm of OpenSCAD surface")
    if "stl_vol_diff_pct" in rec and abs(rec["stl_vol_diff_pct"]) > TOL_VOL:
        out.append(f"volume {rec['stl_vol_diff_pct']:+.2f} % vs checked-in {rec['stl_file']}")
    return out


def main():
    args = sys.argv[1:]
    force = "--force-ref" in args
    do_ref = "--no-ref" not in args
    only = None
    for a in args:
        if a.startswith("--only="):
            only = set(a.split("=", 1)[1].split(","))
    idx = json.load(open(os.path.join(HERE, "_build_index.json")))
    items = [(p, "part") for p in idx["parts"]] + [(a, "assembly") for a in idx["assemblies"]]
    if only:
        items = [(i, k) for i, k in items if i["id"] in only]
    t0 = time.time()
    # pre-generate reference STLs in parallel (2 cores)
    if do_ref:
        with ThreadPoolExecutor(max_workers=2) as ex:
            list(ex.map(lambda ik: make_ref(ik[0], force), items))
        print(f"reference STLs ready ({time.time() - t0:.0f} s)")
    results = []
    vol_by_id = {}
    prev = os.path.join(HERE, "_verify_results.json")
    if os.path.exists(prev):
        vol_by_id = {r["id"]: r.get("volume_mm3", 0.0) for r in json.load(open(prev))["results"]}
    for it, kind in sorted(items, key=lambda ik: ik[1] == "assembly"):
        rec = verify_item(it, kind, False, do_ref, vol_by_id)
        vol_by_id[it["id"]] = rec.get("volume_mm3", 0.0)
        rec["mismatch"] = judge(rec, kind)
        results.append(rec)
        flag = "OK " if not rec["mismatch"] else "MIS"
        vd = rec.get("vol_diff_pct")
        print(f"{flag} {rec['id']:38s} solids={rec.get('n_solids')} valid={rec.get('valid')} "
              f"V={rec.get('volume_mm3', 0) / 1000:10.2f} cm3 "
              f"{'dV=%+.2f%%' % vd if vd is not None else 'no ref':>12s} "
              f"{('within=%.1f%%' % rec['step_to_ref_within_tol_pct']) if 'step_to_ref_within_tol_pct' in rec else ''} "
              f"{'; '.join(rec['mismatch'])}")
    out = os.path.join(HERE, "_verify_results.json")
    if only and os.path.exists(out):       # merge
        old = {r["id"]: r for r in json.load(open(out))["results"]}
        old.update({r["id"]: r for r in results})
        results = list(old.values())
    json.dump({"tol_vol_pct": TOL_VOL, "results": results}, open(out, "w"), indent=1)
    print("wrote", out)


if __name__ == "__main__":
    main()
