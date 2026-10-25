#!/usr/bin/env python3
"""
pf_cq.py - CadQuery helpers that mirror the OpenSCAD helpers (pf_common.scad) and the
OpenSCAD transform semantics, so STEP parts can be written with the same frames and the same
placement expressions as the .scad assemblies.

All lengths mm, angles degrees.  Shapes are cq.Workplane objects holding ONE solid unless
stated otherwise.
"""
import math
import cadquery as cq

V = cq.Vector


# ---------------------------------------------------------------- OpenSCAD-style transforms
def translate(s, v):
    return s.translate(V(*v))


def rotate(s, a):
    """OpenSCAD rotate([ax,ay,az]): rotate about X, then Y, then Z (all about the world origin)."""
    ax, ay, az = a
    if ax:
        s = s.rotate((0, 0, 0), (1, 0, 0), ax)
    if ay:
        s = s.rotate((0, 0, 0), (0, 1, 0), ay)
    if az:
        s = s.rotate((0, 0, 0), (0, 0, 1), az)
    return s


def mirror_yz(s):
    """OpenSCAD mirror([1,0,0])  (x -> -x)."""
    return s.mirror("YZ")


def mirror_xy(s):
    """OpenSCAD mirror([0,0,1])  (z -> -z)."""
    return s.mirror("XY")


def place(s, t=(0, 0, 0), r=(0, 0, 0)):
    """translate(t) rotate(r) s   (rotate first, then translate - OpenSCAD reading order)."""
    return translate(rotate(s, r), t)


# ---------------------------------------------------------------- primitives
def box(x, y, z, at=(0, 0, 0)):
    """OpenSCAD cube([x,y,z]) translated to `at` (corner at `at`)."""
    return cq.Workplane("XY").box(x, y, z, centered=False).translate(V(*at))


def cyl(d, h, at=(0, 0, 0), axis="z", center=False):
    """OpenSCAD cylinder(d,h) with its base circle centre at `at`, axis +z (or +x / +y)."""
    s = cq.Workplane("XY").circle(d / 2.0).extrude(h)
    if center:
        s = s.translate(V(0, 0, -h / 2.0))
    if axis == "x":
        s = s.rotate((0, 0, 0), (0, 1, 0), 90)
    elif axis == "y":
        s = s.rotate((0, 0, 0), (1, 0, 0), -90)
    return s.translate(V(*at))


def rrect_w(x, y, r, wp=None):
    """Centred rounded rectangle wire on a workplane (OpenSCAD rrect)."""
    rr = min(r, min(x, y) / 2.0 - 0.01)
    wp = wp or cq.Workplane("XY")
    return wp.rect(x, y), rr


def rbox(x, y, z, r, at=(0, 0, 0)):
    """OpenSCAD rbox: rounded box, centred in x/y, sitting on z=0, vertical-edge radius r."""
    rr = min(r, min(x, y) / 2.0 - 0.01)
    s = cq.Workplane("XY").rect(x, y).extrude(z)
    if rr > 0.001:
        s = s.edges("|Z").fillet(rr)
    return s.translate(V(*at))


def rrect_extrude(x, y, r, t, at=(0, 0, 0)):
    return rbox(x, y, t, r, at)


def hexp(af, h, at=(0, 0, 0)):
    return cq.Workplane("XY").polygon(6, af / math.cos(math.radians(30))).extrude(h).translate(V(*at))


def union(*shapes):
    s = shapes[0]
    for o in shapes[1:]:
        s = s.union(o)
    return s


def cut(base, *tools):
    for t in tools:
        base = base.cut(t)
    return base


def solid_of(s):
    """Return a cq.Shape (single Solid or Compound) from a Workplane/Shape."""
    return s.val() if hasattr(s, "val") else s


def prism_xy(pts, h, z0=0.0):
    """Polygon (list of (x,y)) in the XY plane extruded +z by h starting at z0."""
    return cq.Workplane("XY").workplane(offset=z0).polyline(pts).close().extrude(h)


# ---------------------------------------------------------------- aluminium T-slot extrusion
def tslot(w, h, length, pitch, slot_w):
    """Faithful B-rep translation of pf_common.scad tslot2d()/tslot(): extruded along +z from 0.
    The profile is the same GENERIC approximation used by the OpenSCAD model (not a vendor profile)."""
    lip = 1.8 if pitch == 20 else 4.0
    cav_w = 11.0 if pitch == 20 else 20.0
    cav_d = 4.2 if pitch == 20 else 8.0
    bore = 4.2 if pitch == 20 else 8.5
    nx = int(math.floor(w / pitch + 0.5))
    ny = int(math.floor(h / pitch + 0.5))
    body = rbox(w, h, length, 1.5)
    tools = []
    L2 = length + 2.0
    for i in range(nx):
        cx = -w / 2 + pitch / 2 + i * pitch
        for s in (-1, 1):
            # opening
            tools.append(cq.Workplane("XY").workplane(offset=-1).center(cx, s * (h / 2 - lip / 2))
                         .rect(slot_w, lip + 0.2).extrude(L2))
            # T-cavity (wide side outward, near the lip)
            cy = s * (h / 2 - lip - cav_d / 2)
            pts = [(cx - cav_w / 2, cy + s * cav_d / 2), (cx + cav_w / 2, cy + s * cav_d / 2),
                   (cx + slot_w / 2, cy - s * cav_d / 2), (cx - slot_w / 2, cy - s * cav_d / 2)]
            tools.append(prism_xy(pts, L2, -1))
    for j in range(ny):
        cy = -h / 2 + pitch / 2 + j * pitch
        for s in (-1, 1):
            tools.append(cq.Workplane("XY").workplane(offset=-1).center(s * (w / 2 - lip / 2), cy)
                         .rect(lip + 0.2, slot_w).extrude(L2))
            cx = s * (w / 2 - lip - cav_d / 2)
            pts = [(cx + s * cav_d / 2, cy - cav_w / 2), (cx + s * cav_d / 2, cy + cav_w / 2),
                   (cx - s * cav_d / 2, cy + slot_w / 2), (cx - s * cav_d / 2, cy - slot_w / 2)]
            tools.append(prism_xy(pts, L2, -1))
    for i in range(nx):
        for j in range(ny):
            tools.append(cyl(bore, L2, at=(-w / 2 + pitch / 2 + i * pitch, -h / 2 + pitch / 2 + j * pitch, -1)))
    cutter = tools[0]
    for t in tools[1:]:
        cutter = cutter.union(t)
    return body.cut(cutter)


def rhs(w, h, t, length):
    """Rectangular hollow section along +z (OpenSCAD rhs(): outer corner radius t, inner 0.5)."""
    outer = rbox(w, h, length, t)
    inner = rbox(w - 2 * t, h - 2 * t, length + 2, 0.5, at=(0, 0, -1))
    return outer.cut(inner)


def hollow_cyl(od, id_, h, at=(0, 0, 0)):
    return cyl(od, h, at).cut(cyl(id_, h + 2, at=(at[0], at[1], at[2] - 1)))


# ---------------------------------------------------------------- exact 2D hull of discs / points
def hull2d(circles=(), points=(), rects=()):
    """Exact 2D convex hull (true arcs + tangent lines) of circles (cx,cy,r), points (x,y) and
    axis-aligned rectangles (xmin,ymin,xmax,ymax) - the equivalent of OpenSCAD hull() on 2D children.
    Returns a closed cq.Workplane("XY") wire ready for .extrude()."""
    items = [(c[0], c[1], c[2]) for c in circles] + [(p[0], p[1], 0.0) for p in points]
    for (x0, y0, x1, y1) in rects:
        items += [(x0, y0, 0.0), (x1, y0, 0.0), (x1, y1, 0.0), (x0, y1, 0.0)]
    # remove duplicates
    uniq = []
    for it in items:
        if not any(abs(it[0] - u[0]) < 1e-9 and abs(it[1] - u[1]) < 1e-9 and abs(it[2] - u[2]) < 1e-9 for u in uniq):
            uniq.append(it)
    items = uniq
    N = 72000
    step = 2 * math.pi / N

    def support(th):
        ux, uy = math.cos(th), math.sin(th)
        best, bi = -1e18, -1
        for k, (cx, cy, r) in enumerate(items):
            v = cx * ux + cy * uy + r
            if v > best + 1e-9:
                best, bi = v, k
        return bi

    # scan; collapse into runs of active item
    seq = []
    for n in range(N):
        seq.append(support(n * step))
    # rotate so that we start at a run boundary
    start = 0
    for n in range(N):
        if seq[n] != seq[n - 1]:
            start = n
            break
    runs = []   # [item, theta_start_sample]
    prev = None
    for m in range(N):
        n = (start + m) % N
        if seq[n] != prev:
            runs.append([seq[n], n])
            prev = seq[n]
    # tangent angles between consecutive runs (exact): (ci - cj).u = rj - ri
    K = len(runs)
    bounds = []  # theta at which run k ends (== run k+1 begins)
    for k in range(K):
        i, j = runs[k][0], runs[(k + 1) % K][0]
        (xi, yi, ri), (xj, yj, rj) = items[i], items[j]
        dx, dy, kk = xi - xj, yi - yj, rj - ri
        d = math.hypot(dx, dy)
        base = math.atan2(dy, dx)
        al = math.acos(max(-1.0, min(1.0, kk / d)))
        cands = [base + al, base - al]
        approx = runs[(k + 1) % K][1] * step
        th = min(cands, key=lambda c: abs(((c - approx + math.pi) % (2 * math.pi)) - math.pi))
        bounds.append(th % (2 * math.pi))
    # build path: for run k (item i) arc from bounds[k-1] to bounds[k]
    segs = []
    for k in range(K):
        i = runs[k][0]
        cx, cy, r = items[i]
        a0, a1 = bounds[k - 1], bounds[k]
        if a1 < a0:
            a1 += 2 * math.pi
        segs.append((cx, cy, r, a0, a1))

    def pt(cx, cy, r, a):
        return (cx + r * math.cos(a), cy + r * math.sin(a))

    wp = cq.Workplane("XY")
    cur = pt(*segs[0][:3], segs[0][3])
    wp = wp.moveTo(*cur)
    for (cx, cy, r, a0, a1) in segs:
        p0, p1 = pt(cx, cy, r, a0), pt(cx, cy, r, a1)
        if math.hypot(p0[0] - cur[0], p0[1] - cur[1]) > 1e-7:
            wp = wp.lineTo(*p0)
        if r > 1e-9 and (a1 - a0) > 1e-7:
            wp = wp.threePointArc(pt(cx, cy, r, 0.5 * (a0 + a1)), p1)
            cur = p1
        else:
            cur = p0
    return wp.close()


# ---------------------------------------------------------------- exact 3D convex hull (planar faces only)
def hull3d(points):
    """Convex hull of a point cloud as a B-rep solid (planar faces, coplanar triangles merged).
    Equivalent of OpenSCAD hull() of polyhedral children; circles must be supplied as N-gons."""
    import numpy as np
    from scipy.spatial import ConvexHull
    pts = np.asarray(points, dtype=float)
    hull = ConvexHull(pts)
    faces = []
    for tri in hull.simplices:
        a, b, c = [V(*pts[i]) for i in tri]
        w = cq.Wire.makePolygon([a, b, c], close=True)
        faces.append(cq.Face.makeFromWires(w))
    shell = cq.Shell.makeShell(faces)
    sol = cq.Solid.makeSolid(shell)
    if sol.Volume() < 0:
        sol = cq.Solid(sol.wrapped.Reversed())
    return cq.Workplane("XY").newObject([sol]).clean()


def ngon_pts(cx, cy, r, z, n=128):
    return [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n), z) for k in range(n)]
