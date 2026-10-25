#!/usr/bin/env python3
"""
ParkFlow FEA helpers: gmsh -> CalculiX (ccx) deck writer, .frd parser, mesh statistics, VTK conversion.
Units everywhere: mm, N, MPa, tonne (density in t/mm^3), s.
"""
import os, re, subprocess, time, json
import numpy as np

# ------------------------------------------------------------------ materials (values from cad/calcs/CALCS.md table)
# name: (E MPa, nu, Rp0.2 MPa, rho t/mm3)
MATERIALS = {
    "MS_E250":     (200000.0, 0.30, 250.0, 7.85e-9),   # IS 2062 E250
    "AL6063T5":    (69500.0,  0.33, 110.0, 2.70e-9),   # EN 755-2 min
    "AL5052H32":   (70300.0,  0.33, 130.0, 2.68e-9),   # EN 485-2 min
    "AL6061T6":    (68900.0,  0.33, 240.0, 2.70e-9),   # EN 755-2 / ASTM B209
    "STEEL88":     (200000.0, 0.30, 640.0, 7.85e-9),   # class 8.8 bolt/spacer proof
}

# ------------------------------------------------------------------ gmsh mesh extraction
def extract_tet10(gmsh, vol_tags):
    """Return nodes dict {tag: xyz}, and per-volume list of (elem_tag, [10 nodes in Abaqus/ccx order])."""
    nodes = {}
    elems = {}
    for v in vol_tags:
        types, etags, enodes = gmsh.model.mesh.getElements(3, v)
        for t, tags, nn in zip(types, etags, enodes):
            assert t == 11, f"expected tet10 (gmsh type 11), got {t}"
            nn = np.array(nn, dtype=np.int64).reshape(-1, 10)
            # gmsh node 9 = mid(3-4), 10 = mid(2-4); Abaqus/ccx: 9 = mid(2-4), 10 = mid(3-4) -> swap
            nn = nn[:, [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]]
            elems[v] = (np.array(tags, dtype=np.int64), nn)
    ntags, ncoord, _ = gmsh.model.mesh.getNodes()
    allc = {int(t): c for t, c in zip(ntags, np.array(ncoord).reshape(-1, 3))}
    used = set()
    for v, (tg, nn) in elems.items():
        used.update(nn.ravel().tolist())
    nodes = {t: allc[t] for t in used}
    return nodes, elems


def tet_face_map(elems):
    """map frozenset(3 corner nodes) -> (elem_tag, face_no 1..4) for all tets (ccx C3D10 face numbering)."""
    fm = {}
    # ccx C3D10: S1: 1-2-3 ; S2: 1-4-2 ; S3: 2-4-3 ; S4: 3-4-1   (corner node positions 0..3)
    faces = {1: (0, 1, 2), 2: (0, 3, 1), 3: (1, 3, 2), 4: (2, 3, 0)}
    for v, (tg, nn) in elems.items():
        for e, row in zip(tg, nn):
            for f, idx in faces.items():
                fm[frozenset((int(row[idx[0]]), int(row[idx[1]]), int(row[idx[2]])))] = (int(e), f)
    return fm


def surface_faces(gmsh, surf_tags, fmap):
    """element-face list [(elem, face)] for gmsh surface entities (their tri6/tri3 corner nodes matched to tets)."""
    out = []
    for s in surf_tags:
        types, etags, enodes = gmsh.model.mesh.getElements(2, s)
        for t, tags, nn in zip(types, etags, enodes):
            npe = {2: 3, 9: 6}[t]
            nn = np.array(nn, dtype=np.int64).reshape(-1, npe)[:, :3]
            for row in nn:
                key = frozenset(int(x) for x in row)
                if key in fmap:
                    out.append(fmap[key])
    return out


def surface_nodes(gmsh, surf_tags):
    s = set()
    for t in surf_tags:
        nt, _, _ = gmsh.model.mesh.getNodes(2, t, includeBoundary=True)
        s.update(int(x) for x in nt)
    return s


def mesh_quality(gmsh, dim=3):
    """element quality stats using SICN (signed inverse condition number) and gamma (inscribed/circumscribed ratio)."""
    tags = []
    for d, t in gmsh.model.getEntities(dim):
        _, et, _ = gmsh.model.mesh.getElements(dim, t)
        for x in et:
            tags += list(x)
    tags = np.array(tags, dtype=np.int64)
    out = {}
    for name in ("minSICN", "gamma", "minSJ"):
        try:
            q = np.array(gmsh.model.mesh.getElementQualities(tags.tolist(), name))
            out[name] = dict(min=float(q.min()), mean=float(q.mean()), p5=float(np.percentile(q, 5)),
                             n_lt_0p1=int((q < 0.1).sum()))
        except Exception as ex:   # quality measure unavailable for the element type
            out[name] = dict(error=str(ex))
    return out


# ------------------------------------------------------------------ deck writing
def fmt_ids(ids, per_line=10):
    ids = list(ids)
    lines = []
    for i in range(0, len(ids), per_line):
        lines.append(", ".join(str(x) for x in ids[i:i + per_line]))
    return "\n".join(lines)


class Deck:
    def __init__(self, title):
        self.parts = [f"** {title}", "** units: mm, N, MPa, tonne, s"]

    def add(self, s):
        self.parts.append(s)

    def nodes(self, nodes):
        self.add("*NODE")
        self.add("\n".join(f"{t}, {c[0]:.6f}, {c[1]:.6f}, {c[2]:.6f}" for t, c in sorted(nodes.items())))

    def elements(self, name, tags, nn, etype="C3D10"):
        self.add(f"*ELEMENT, TYPE={etype}, ELSET={name}")
        self.add("\n".join(f"{int(t)}, " + ", ".join(str(int(x)) for x in row) for t, row in zip(tags, nn)))

    def nset(self, name, ids):
        ids = sorted(int(i) for i in ids)
        self.add(f"*NSET, NSET={name}")
        self.add(fmt_ids(ids))

    def elsurf(self, name, faces):
        """element-face surface; faces = [(elem, face_no)]"""
        self.add(f"*SURFACE, NAME={name}, TYPE=ELEMENT")
        byf = {}
        for e, f in faces:
            byf.setdefault(f, []).append(e)
        lines = []
        for f in sorted(byf):
            for e in byf[f]:
                lines.append(f"{e}, S{f}")
        self.add("\n".join(lines))

    def material(self, name, key, density=True):
        E, nu, ry, rho = MATERIALS[key]
        self.add(f"*MATERIAL, NAME={name}\n*ELASTIC\n{E}, {nu}")
        if density:
            self.add(f"*DENSITY\n{rho:.4e}")

    def text(self):
        return "\n".join(self.parts) + "\n"

    def write(self, path):
        with open(path, "w") as f:
            f.write(self.text())


def run_ccx(jobname, workdir, threads=2, timeout=7200):
    """run `ccx -i jobname` in workdir; return (elapsed s, return code). Output captured to jobname.log."""
    env = dict(os.environ, OMP_NUM_THREADS=str(threads), CCX_NPROC_EQUATION_SOLVER=str(threads),
               OMP_STACKSIZE="256M")
    t0 = time.time()
    with open(os.path.join(workdir, jobname + ".log"), "w") as lg:
        p = subprocess.run(["ccx", "-i", jobname], cwd=workdir, stdout=lg, stderr=subprocess.STDOUT, env=env,
                           timeout=timeout)
    return time.time() - t0, p.returncode


# ------------------------------------------------------------------ frd parser
def _f12(line, start, n):
    return [float(line[start + 12 * i: start + 12 * (i + 1)]) for i in range(n)]


CCX_FRD_ELTYPE = {1: "C3D8", 2: "C3D6", 3: "C3D4", 4: "C3D20", 5: "C3D15", 6: "C3D10", 7: "S3", 8: "S6", 9: "S4",
                  10: "S8", 11: "B2", 12: "B3"}


def parse_frd(path):
    """Parse ccx ASCII .frd. Returns dict(nodes{id:xyz}, elems[(id,type,[nodes])], results{name: {increment_index: {node: vals}}})
    Only the LAST increment of every result block name is kept in out['last'][name] = (ids array, values array)."""
    nodes = {}
    elems = []
    blocks = []   # (name, ncomp, compnames, ids, vals, header)
    with open(path) as f:
        lines = f.read().split("\n")
    i = 0
    n = len(lines)
    while i < n:
        L = lines[i]
        if L.startswith("    2C"):
            i += 1
            while i < n and not lines[i].startswith(" -3"):
                l = lines[i]
                if l.startswith(" -1"):
                    nid = int(l[3:13]); nodes[nid] = _f12(l, 13, 3)
                i += 1
        elif L.startswith("    3C"):
            i += 1
            cur = None
            while i < n and not lines[i].startswith(" -3"):
                l = lines[i]
                if l.startswith(" -1"):
                    if cur is not None:
                        elems.append(cur)
                    cur = [int(l[3:13]), int(l[13:18]), []]
                elif l.startswith(" -2"):
                    cur[2] += [int(l[3 + 10 * k:13 + 10 * k]) for k in range((len(l) - 3) // 10) if l[3 + 10 * k:13 + 10 * k].strip()]
                i += 1
            if cur is not None:
                elems.append(cur)
        elif L.startswith("  100C"):
            hdr = L
            i += 1
            name = None; comps = []; ids = []; vals = []
            while i < n and not lines[i].startswith(" -3"):
                l = lines[i]
                if l.startswith(" -4"):
                    name = l[5:13].strip(); ncomp = int(l[13:18])
                elif l.startswith(" -5"):
                    c = l[5:13].strip()
                    # -5 lines with menu=1 are real components; others (ALL) skip
                    if int(l[13:18]) == 1 and int(l[18:23]) in (1, 2, 4):
                        comps.append(c)
                elif l.startswith(" -1"):
                    nid = int(l[3:13])
                    nv = (len(l) - 13) // 12
                    v = _f12(l, 13, nv)
                    # continuation lines
                    while len(v) < len(comps) and i + 1 < n and lines[i + 1].startswith(" -2"):
                        i += 1
                        v += _f12(lines[i], 3, (len(lines[i]) - 3) // 12)
                    ids.append(nid); vals.append(v)
                i += 1
            if name is not None:
                blocks.append((name, comps, np.array(ids), np.array(vals), hdr))
        i += 1
    last = {}
    for name, comps, ids, vals, hdr in blocks:
        last[name] = (comps, ids, vals, hdr)
    return dict(nodes=nodes, elems=elems, blocks=blocks, last=last)


def von_mises(s):
    """s: (n,6) S11 S22 S33 S12 S23 S31"""
    s11, s22, s33, s12, s23, s31 = [s[:, k] for k in range(6)]
    return np.sqrt(0.5 * ((s11 - s22) ** 2 + (s22 - s33) ** 2 + (s33 - s11) ** 2) + 3 * (s12 ** 2 + s23 ** 2 + s31 ** 2))


def frd_fields(fr):
    """Return node id array, coords (n,3), disp (n,3), vm (n,), stress (n,6) aligned on node ids of the stress block."""
    comps, ids, vals, hdr = fr["last"]["STRESS"]
    sig = vals[:, :6]
    d_comps, d_ids, d_vals, _ = fr["last"]["DISP"]
    dmap = {int(k): v[:3] for k, v in zip(d_ids, d_vals)}
    disp = np.array([dmap.get(int(k), [0, 0, 0]) for k in ids])
    xyz = np.array([fr["nodes"][int(k)] for k in ids])
    return ids, xyz, disp, von_mises(sig), sig


def frd_to_vtk(fr):
    """Build a pyvista UnstructuredGrid from the frd mesh (tet10 / shell-expanded hex20 / etc.)."""
    import pyvista as pv
    vtk_type = {"C3D10": 24, "C3D20": 25, "C3D8": 12, "C3D4": 10, "C3D6": 13, "C3D15": 26}
    ids = sorted(fr["nodes"])
    idx = {k: j for j, k in enumerate(ids)}
    pts = np.array([fr["nodes"][k] for k in ids])
    cells = []; types = []
    for eid, et, nn in fr["elems"]:
        name = CCX_FRD_ELTYPE.get(et)
        if name not in vtk_type:
            continue
        nn = list(nn)
        if name == "C3D20":
            # ccx/Abaqus C3D20 ordering == VTK quadratic hexahedron ordering except top-mid ordering is the same; keep.
            pass
        if name == "C3D10":
            pass
        cells.append([len(nn)] + [idx[x] for x in nn]); types.append(vtk_type[name])
    cells_flat = np.concatenate([np.array(c) for c in cells])
    grid = pv.UnstructuredGrid(cells_flat, np.array(types, dtype=np.uint8), pts)
    return grid, ids, idx
