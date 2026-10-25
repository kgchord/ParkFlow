#!/usr/bin/env python3
"""
build_gantry.py - (a) LANE GANTRY POLE: every fabricated part, bought-in envelope and assembly.

Every dimension is read from the OpenSCAD source (gantry_params.scad + the few file-local
constants in the part .scad files, + pf_bought.scad envelopes) through scadparams.load().
Frames are the OpenSCAD frames: pole axis +z, origin on concrete top / plate underside centre,
+x towards the lane (arms), -y towards approaching vehicles.
"""
import math
import cadquery as cq
from scadparams import load
from pf_cq import *            # noqa: F401,F403
from pf_reg import REG, Asm, Leaf, T, compose

P = load("gantry_antenna_bracket.scad", "gantry_camera_arm.scad", "gantry_channel_cap_sign.scad",
         "gantry_base_weldment.scad", "pf_bought.scad")
D = "gantry"
SRC = ["gantry_params.scad"]
MAT_MS = "IS2062-E250 (MS)"
MAT_5052 = "Al 5052-H32"
MAT_6063 = "Al 6063-T5"
MAT_ASA = "ASA (FDM)"


# ===================================================================== (1) base plate weldment parts
def base_plate():
    p = P
    s = rbox(p.bp_w, p.bp_w, p.bp_t, p.bp_corner_r)
    tools = []
    for a in (45, 135, 225, 315):
        c, sn = math.cos(math.radians(a)), math.sin(math.radians(a))
        tools.append(cyl(p.bp_anchor_hole, p.bp_t + 2, at=(p.bp_pcd / 2 * c, p.bp_pcd / 2 * sn, -1)))
        # 16 x 8 grout/vent slot, long side radial, centre at radius pcd/2 - 40
        r0 = p.bp_pcd / 2 - 40
        slot = box(16, 8, p.bp_t + 2, at=(-8, -4, -1))
        slot = rotate(slot, (0, 0, a)).translate(V(r0 * c, r0 * sn, 0))
        tools.append(slot)
    tools.append(cyl(p.bp_centre_hole, p.bp_t + 2, at=(0, 0, -1)))
    return cut(s, *tools)


def cheek_long():
    p = P
    sock_in = p.pole_w + 2 * p.sock_clear
    sock_long = sock_in + 2 * p.sock_t
    s = box(sock_long, p.sock_h, p.sock_t, at=(-sock_long / 2, 0, 0))
    hole = cyl(p.sock_bolt_d + 1, p.sock_t + 2, at=(0, p.sock_bolt_z1, -1))
    notch = cq.Workplane("XY").workplane(offset=-1).center(0, p.sock_h).ellipse(15, 7.5).extrude(p.sock_t + 2)
    return cut(s, hole, notch)


def cheek_short():
    p = P
    sock_in = p.pole_w + 2 * p.sock_clear
    s = box(sock_in, p.sock_h, p.sock_t, at=(-sock_in / 2, 0, 0))
    return s.cut(cyl(p.sock_bolt_d + 1, p.sock_t + 2, at=(0, p.sock_bolt_z2, -1)))


def gusset():
    p = P
    pts = [(0, p.gus_chamfer), (p.gus_chamfer, 0), (p.gus_l, 0), (p.gus_l, p.gus_tip), (p.gus_tip, p.gus_h),
           (0, p.gus_h)]
    return prism_xy(pts, p.gus_t)


def weldment_asm():
    """Placed weldment parts == OpenSCAD base_weldment(show_bolts=false)."""
    p = P
    sock_in = p.pole_w + 2 * p.sock_clear
    sock_long = sock_in + 2 * p.sock_t
    A = Asm("base_weldment")
    A.add(Leaf("gantry_base_plate", BASE_PLATE, "base_plate_16mm_MS", "steel"))
    for s in (-1, 1):
        f = compose(T((0, s * (sock_in / 2 + p.sock_t / 2), p.bp_t)), T(r=(90, 0, 0)), T((0, 0, -p.sock_t / 2)))
        A.add(Leaf("gantry_socket_cheek_long", CHEEK_L, f"socket_cheek_long_{'+' if s > 0 else '-'}y", "steel").moved(f))
    for s in (-1, 1):
        f = compose(T((s * (sock_in / 2 + p.sock_t / 2), 0, p.bp_t)), T(r=(90, 0, 90)), T((0, 0, -p.sock_t / 2)))
        A.add(Leaf("gantry_socket_cheek_short", CHEEK_S, f"socket_cheek_short_{'+' if s > 0 else '-'}x", "steel").moved(f))
    for k in range(int(p.gus_n)):
        a = k * 360 / p.gus_n
        f = compose(T(r=(0, 0, a)), T((sock_long / 2, 0, p.bp_t)), T(r=(90, 0, 0)), T((0, 0, -p.gus_t / 2)))
        A.add(Leaf("gantry_gusset", GUSSET, f"gusset_{int(a)}deg", "steel").moved(f))
    return A


# ===================================================================== (2) extrusions
def arm40(length):
    return tslot(P.ant_arm_w, P.ant_arm_w, length, P.pole_pitch, P.pole_slot)


# ===================================================================== (3) pole cap, cable boot, channel
def pole_cap():
    p = P
    ci = p.pole_w + 2 * p.cap_clear
    ow = ci + 2 * p.cap_wall
    base = rbox(ow, ow, p.cap_h, 3)
    k = 0.6
    s1 = cq.Sketch().rect(ow, ow).vertices().fillet(3)
    s2 = cq.Sketch().rect(ow * k, ow * k).vertices().fillet(3 * k)
    slope = (cq.Workplane("XY").workplane(offset=p.cap_h).placeSketch(s1, s2.moved(cq.Location(V(0, 0, 8)))).loft())
    body = base.union(slope)
    body = body.cut(rbox(ci, ci, p.cap_h + 1 - 2.4, 1.5, at=(0, 0, -1)))
    for a in (0, 90, 180, 270):
        rib = box(3.2, 9, p.cap_h - 4.4, at=(ci / 2 - 3, -4.5, 2))
        body = body.union(rotate(rib, (0, 0, a)))
    return body


def cable_boot():
    p = P
    x0 = -p.pole_w / 2 - p.duct_d - 1.5          # box x min
    bx = p.duct_d + 1.5
    by = p.duct_w + 6
    z0 = p.duct_z0 - p.boot_h
    cxm = -p.pole_w / 2 - p.duct_d / 2
    pts = []
    for x in (x0, x0 + bx):
        for y in (-by / 2, by / 2):
            for z in (z0, z0 + p.boot_h):
                pts.append((x, y, z))
    r = (p.conduit_d + 8) / 2
    pts += ngon_pts(cxm, 0, r, p.bp_t + 10, 128) + ngon_pts(cxm, 0, r, p.bp_t + 11, 128)
    h = hull3d(pts)
    inner = box(p.duct_d - 4, p.duct_w - 4, p.boot_h, at=(-p.pole_w / 2 - p.duct_d + 2, -p.duct_w / 2 + 2, z0 + 15))
    cond = cyl(p.conduit_d + 0.6, 40, at=(cxm, 0, p.bp_t))
    back = box(10, p.duct_w + 20, 400, at=(-p.pole_w / 2 - 2, -p.duct_w / 2 - 10, 0))
    return cut(h, inner, cond, back)


def cable_channel():
    p = P
    L = p.duct_z1 - p.duct_z0
    tube = box(p.duct_d, p.duct_w, L, at=(-p.pole_w / 2 - p.duct_d, -p.duct_w / 2, p.duct_z0))
    tube = tube.cut(box(p.duct_d - 2 * p.duct_t, p.duct_w - 2 * p.duct_t, L + 2,
                        at=(-p.pole_w / 2 - p.duct_d + p.duct_t, -p.duct_w / 2 + p.duct_t, p.duct_z0 - 1)))
    cover = box(1.5, p.duct_w + 2, L, at=(-p.pole_w / 2 - p.duct_d - 1.5, -p.duct_w / 2 - 1, p.duct_z0))
    return tube.union(cover)


def conduit():
    p = P
    return cyl(p.conduit_d, p.bp_t + 40 + p.grout_gap + 20, at=(-p.pole_w / 2 - p.duct_d / 2, 0, -p.grout_gap - 40))


# ===================================================================== (4) antenna yoke + tilt plate
def yoke():
    p = P
    t, R = p.yoke_t, p.yoke_bend_r
    wtop = p.pivot_drop - p.ant_arm_w / 2            # web_top_above_pivot
    web = box(p.yoke_w - 2 * (t + R), p.yoke_web_d, t, at=(-(p.yoke_w - 2 * (t + R)) / 2, -p.yoke_web_d / 2, wtop - t))
    web = web.cut(_cyl_pair(p.web_hole_pitch, 6.6))
    parts = [web]
    for s in (-1, 1):
        # quarter bend ring (axis along y) centred at (s*(W/2 - t - R), wtop - t - R)
        cx, cz = s * (p.yoke_w / 2 - t - R), wtop - t - R
        ring = (cq.Workplane("XZ").center(cx, cz).circle(R + t).circle(R).extrude(p.yoke_web_d / 2, both=True))
        quad = box(R + t + 1, p.yoke_web_d + 2, R + t + 1,
                   at=((cx if s > 0 else cx - (R + t + 1)), -p.yoke_web_d / 2 - 1, cz))
        parts.append(ring.intersect(quad))
        # cheek: (y,z) profile extruded through thickness t at x = s*(W/2 - t/2)
        cheek = _cheek_2d(p, cz)
        cheek = cheek.translate(V(s * (p.yoke_w / 2) - (t if s > 0 else 0), 0, 0))
        parts.append(cheek)
    return union(*parts)


def _cyl_pair(pitch, d):
    return union(*[cyl(d, 600, at=(s * pitch / 2, 0, -100)) for s in (-1, 1)])


def _cheek_2d(p, ztop):
    """Yoke cheek, thickness yoke_t, returned in the YOKE frame at x = 0..t (caller shifts in x).
    2D outline (in y,z) = hull(web-depth rectangle, bottom circle) clipped at z = ztop, minus pivot hole,
    tilt-lock arc slot and 5-degree scale notches - exactly cheek_2d()/yoke() of gantry_antenna_bracket.scad."""
    t = p.yoke_t
    wtop = p.pivot_drop - p.ant_arm_w / 2
    outline = hull2d(circles=[(0, p.cheek_bot_c, p.cheek_r)], rects=[(-p.yoke_web_d / 2, 0, p.yoke_web_d / 2, wtop)])
    slab = outline.extrude(t)                          # XY slab: x -> world Y, y -> world Z, z -> world X
    slab = slab.intersect(box(400, 400, t + 2, at=(-200, ztop - 400, -1)))
    slab = slab.cut(cyl(p.pivot_d + 0.5, t + 2, at=(0, 0, -1)))
    slab = slab.cut(_lock_slot(p, t))
    for a in range(int(p.tilt_min), int(p.tilt_max) + 1, 5):
        ang = math.radians(-90 + a)
        n = rotate(box(5, 0.8, t + 2, at=(-2.5, -0.4, -1)), (0, 0, -90 + a))
        slab = slab.cut(n.translate(V((p.lock_r + 9) * math.cos(ang), (p.lock_r + 9) * math.sin(ang), 0)))
    return _to_yz(slab)


def _to_yz(slab):
    """(x,y,z) -> (z,x,y): cyclic rotation = 120 deg about (1,1,1)."""
    return slab.rotate((0, 0, 0), (1, 1, 1), 120)


def _lock_slot(p, t):
    """M6 tilt-lock slot: centre-line radius lock_r, swept from -90 deg to -90+tilt_max (towards +y),
    width lock_slot_w, round ends (== chain of hulled circles in the .scad)."""
    r0, r1 = p.lock_r - p.lock_slot_w / 2, p.lock_r + p.lock_slot_w / 2
    a0, a1 = math.radians(p.tilt_min - 90), math.radians(p.tilt_max - 90)
    am = 0.5 * (a0 + a1)

    def Pt(r, a):
        return (r * math.cos(a), r * math.sin(a))
    sector = (cq.Workplane("XY").workplane(offset=-1).moveTo(*Pt(r1, a0)).threePointArc(Pt(r1, am), Pt(r1, a1))
              .lineTo(*Pt(r0, a1)).threePointArc(Pt(r0, am), Pt(r0, a0)).close().extrude(t + 2))
    ends = union(*[cyl(p.lock_slot_w, t + 2, at=(Pt(p.lock_r, a)[0], Pt(p.lock_r, a)[1], -1)) for a in (a0, a1)])
    return sector.union(ends)


def tilt_plate():
    p = P
    t, R = p.yoke_t, p.yoke_bend_r
    # face (x,z) plate, normal y: y in [-(tp_off+t), -tp_off]
    face = rbox(p.tp_w, p.tp_h, t, 8)                 # XY plate, z thickness -> rotate to XZ below
    holes = [cyl(6.6, t + 2, at=(sx * p.reader_hole_pitch / 2, sz * p.reader_hole_pitch / 2, -1))
             for sx in (-1, 1) for sz in (-1, 1)]
    holes.append(cyl(30, t + 2, at=(0, 0, -1)))
    for sx in (-1, 1):
        holes.append(rbox(30, 120, t + 2, 6, at=(sx * 80, 0, -1)))
    face = cut(face, *holes)
    face = face.rotate((0, 0, 0), (1, 0, 0), 90).translate(V(0, -p.tp_off, 0))   # extrude z[0,t] -> y[-t,0]; shift
    parts = [face]
    for s in (-1, 1):
        parts.append(_ear(p).translate(V(s * (p.tp_w / 2) - (t if s > 0 else 0), 0, 0)))
    return union(*parts)


def _ear(p):
    t = p.yoke_t
    outline = hull2d(circles=[(0, 0, 16), (0, -p.lock_r, 10)],
                     rects=[(-p.tp_off - t, -p.ear_half_h, -p.tp_off - t + 0.1, p.ear_half_h)])
    slab = outline.extrude(t)
    slab = slab.cut(cyl(p.pivot_d + 0.3, t + 2, at=(0, 0, -1)))
    slab = slab.cut(cyl(6.6, t + 2, at=(0, -p.lock_r, -1)))
    return _to_yz(slab)


# ===================================================================== (5) flat plates
def cam_plate():
    p = P
    s = rbox(p.cam_plate_l, p.cam_plate_w, p.cam_plate_t, 8)
    tools = []
    for x in (-p.cam_plate_l / 2 + 15, -p.cam_plate_l / 2 + 45):
        tools.append(hull2d(circles=[(x - 5, 0, 3.3), (x + 5, 0, 3.3)]).extrude(p.cam_plate_t + 2).translate(V(0, 0, -1)))
    cx = p.cam_plate_l / 2 - 35
    for a in (90, 210, 330):
        tools.append(cyl(5.5, p.cam_plate_t + 2, at=(cx + p.cam_mount_pcd / 2 * math.cos(math.radians(a)),
                                                    p.cam_mount_pcd / 2 * math.sin(math.radians(a)), -1)))
    tools.append(cyl(18, p.cam_plate_t + 2, at=(cx, 0, -1)))
    return cut(s, *tools)


def sign_bracket():
    p = P
    s = rbox(p.sign_br_l, p.sign_br_w, p.sign_br_t, 5)
    tools = [cyl(8.5, p.sign_br_t + 2, at=(-p.sign_br_l / 2 + 25, y, -1)) for y in (-20, 20)]
    for y in (-25, 25):
        x = p.sign_br_l / 2 - 20
        tools.append(hull2d(circles=[(x - 4, y, 3.3), (x + 4, y, 3.3)]).extrude(p.sign_br_t + 2).translate(V(0, 0, -1)))
    return cut(s, *tools)


def edge_bracket():
    p = P
    s = rbox(p.edge_br_l, p.edge_br_w, p.edge_br_t, 4)
    tools = [cyl(8.5, p.edge_br_t + 2, at=(x, 0, -1)) for x in (-20, 20)]
    for sx in (-1, 1):
        x = sx * p.edge_lug_pitch / 2
        tools.append(hull2d(circles=[(x, -5, 3.3), (x, 5, 3.3)]).extrude(p.edge_br_t + 2).translate(V(0, 0, -1)))
    return cut(s, *tools)


# ===================================================================== (6) bought-in envelopes
def corner_bracket40(l=40.0, w=35.0, t=4.0):
    prof = [(0, 0), (l, 0), (l, t), (t, l), (0, l)]
    gus = (cq.Workplane("XZ").polyline(prof).close().extrude(-3)).translate(V(0, w / 2 - 1.5, 0))
    return union(box(l, w, t), box(t, w, l), gus)


def rfid_reader():
    p = P
    a = rbox(p.rfid_w, p.rfid_h, p.rfid_t - 8, 14, at=(0, 0, 8))
    b = rbox(p.rfid_w - 20, p.rfid_h - 20, 8, 10)
    c = rbox(p.rfid_w - 30, p.rfid_h - 30, 1, 12, at=(0, 0, p.rfid_t - 0.6))
    d = cyl(16, 18, at=(0, -p.rfid_h / 2 + 30, -18))
    return union(a, b, c, d)


def bullet_camera():
    p = P
    base = cyl(70, 6)
    stem = cyl(26, p.cam_knuckle)
    ball = cq.Workplane("XY").sphere(15).translate(V(0, 0, p.cam_knuckle))
    zc = p.cam_knuckle + p.cam_dia / 2 - 5
    body = cyl(p.cam_dia - 8, p.cam_len - 20, at=(-60, 0, zc), axis="x")
    cap = cyl(p.cam_dia - 14, 6, at=(-60 + p.cam_len - 20, 0, zc), axis="x")
    lens = cyl(48, 2, at=(-60 + p.cam_len - 15, 0, zc), axis="x")
    hood = box(p.cam_len - 10, p.cam_dia, 4, at=(-60 + 20, -p.cam_dia / 2, zc + p.cam_dia / 2 - 14))
    return union(base, stem, ball, body, cap, lens, hood)


def bullet_camera_aimed():
    """OpenSCAD bullet_camera_aimed(): fixed base+stem, plus camera body (minus its own base/stem) pitched about the knuckle."""
    p = P
    fixed = union(cyl(70, 6), cyl(26, p.cam_knuckle))
    body = bullet_camera().cut(cyl(71, p.cam_knuckle - 15))
    k = p.cam_knuckle
    body = body.translate(V(0, 0, -k)).rotate((0, 0, 0), (0, 1, 0), p.cam_pitch).translate(V(0, 0, k))
    return fixed.union(body)


def p10_cabinet_parts():
    p = P
    w, h, d = p.sign_cab_w, p.sign_cab_h, p.sign_cab_d
    tray = box(w, h, d, at=(-w / 2, -h / 2, 0)).cut(box(w - 6, h - 6, d, at=(-w / 2 + 3, -h / 2 + 3, 3)))
    mod = box(p.p10_w, p.p10_h, p.p10_t - 2, at=(-p.p10_w / 2, -p.p10_h / 2, d - p.p10_t - 4))
    front = box(w - 6, h - 6, 2, at=(-w / 2 + 3, -h / 2 + 3, d - 2))      # trimmed into the tray opening (scad overlaps the walls)
    psu = box(120, 80, 20, at=(-60, -40, 4))
    return tray, mod, front, psu


# ===================================================================== build
BASE_PLATE = CHEEK_L = CHEEK_S = GUSSET = None


def build():
    global BASE_PLATE, CHEEK_L, CHEEK_S, GUSSET
    p = P
    SRCS = ["gantry_params.scad"]

    # ------------------------------------------------ base plate weldment parts
    BASE_PLATE = base_plate()
    REG.part("gantry_base_plate", BASE_PLATE, domain=D, kind="fabricated", material=MAT_MS, color="steel",
             desc="Base plate 250x250x16, 4x D14 anchor holes on PCD190, D30 centre hole, 4 grout slots (laser cut)",
             params=["bp_w", "bp_t", "bp_corner_r", "bp_pcd", "bp_anchor_hole", "bp_centre_hole"],
             sources=["gantry_params.scad", "gantry_base_weldment.scad:base_plate_2d"],
             ref="include <gantry_params.scad>\nuse <gantry_base_weldment.scad>\nlinear_extrude(bp_t) base_plate_2d();",
             mat_key="base_plate")
    CHEEK_L = cheek_long()
    REG.part("gantry_socket_cheek_long", CHEEK_L, domain=D, kind="fabricated", material=MAT_MS, color="steel",
             desc="Socket cheek (long, 93x150x6) with M10 cross-bolt hole z1 and weld-start relief notch",
             params=["pole_w", "sock_clear", "sock_t", "sock_h", "sock_bolt_d", "sock_bolt_z1"],
             sources=["gantry_params.scad", "gantry_base_weldment.scad:socket_cheek_long_2d"],
             ref="include <gantry_params.scad>\nuse <gantry_base_weldment.scad>\nlinear_extrude(sock_t) socket_cheek_long_2d();",
             mat_key="cheeks")
    CHEEK_S = cheek_short()
    REG.part("gantry_socket_cheek_short", CHEEK_S, domain=D, kind="fabricated", material=MAT_MS, color="steel",
             desc="Socket cheek (short, 81x150x6) with M10 cross-bolt hole z2",
             params=["pole_w", "sock_clear", "sock_t", "sock_h", "sock_bolt_d", "sock_bolt_z2"],
             sources=["gantry_params.scad", "gantry_base_weldment.scad:socket_cheek_short_2d"],
             ref="include <gantry_params.scad>\nuse <gantry_base_weldment.scad>\nlinear_extrude(sock_t) socket_cheek_short_2d();",
             mat_key="cheeks")
    GUSSET = gusset()
    REG.part("gantry_gusset", GUSSET, domain=D, kind="fabricated", material=MAT_MS, color="steel",
             desc="Gusset 74x120x6 with weld-clearance snipe and 15 mm flat tip",
             params=["gus_l", "gus_h", "gus_t", "gus_chamfer", "gus_tip"],
             sources=["gantry_params.scad", "gantry_base_weldment.scad:gusset_2d"],
             ref="include <gantry_params.scad>\nuse <gantry_base_weldment.scad>\nlinear_extrude(gus_t) gusset_2d();",
             mat_key="gussets")

    wasm = weldment_asm()
    # fused weldment (one solid) - same file name as before
    fused = union(*[l.shape for l in wasm.leaves()])
    REG.part("base_weldment", fused, domain=D, kind="fabricated", material=MAT_MS, color="steel",
             desc="Base weldment as one fused solid (plate + 4 cheeks + 4 gussets); cross bolts and anchors excluded",
             params=["bp_w", "bp_t", "sock_h", "sock_t", "gus_n", "gus_l", "gus_h"],
             sources=["gantry_params.scad", "gantry_base_weldment.scad:base_weldment"],
             ref="include <gantry_params.scad>\nuse <gantry_base_weldment.scad>\nbase_weldment(false);",
             file="base_weldment.step", mat_key="weldment")
    REG.assembly("gantry_base_weldment_assy", wasm, domain=D,
                 desc="Base weldment as an assembly of its 9 laser-cut plates (unwelded bodies)",
                 params=["bp_t", "sock_clear", "sock_t", "gus_n"],
                 sources=["gantry_base_weldment.scad:base_weldment"],
                 ref="include <gantry_params.scad>\nuse <gantry_base_weldment.scad>\nbase_weldment(false);")

    # ------------------------------------------------ extrusions
    pole = tslot(p.pole_w, p.pole_d, p.pole_len, p.pole_pitch, p.pole_slot)
    REG.part("gantry_pole_80x80", pole, domain=D, kind="fabricated", material=MAT_6063, color="struct",
             desc="Pole: 80x80 8-slot extrusion cut to length (GENERIC profile of the .scad model, not the vendor profile)",
             params=["pole_w", "pole_d", "pole_len", "pole_pitch", "pole_slot"],
             sources=["gantry_params.scad", "pf_common.scad:tslot2d"],
             ref="include <gantry_params.scad>\ninclude <pf_common.scad>\ntslot(pole_w, pole_d, pole_len, pole_pitch, pole_slot);",
             mat_key="pole", notes="Generic profile is heavier than the vendor 5.4 kg/m section - see manifest")
    arm = arm40(p.ant_arm_len)
    REG.part("gantry_antenna_arm_40x40", arm, domain=D, kind="fabricated", material=MAT_6063,
             desc="RFID antenna arm 40x40 T-slot, L = ant_arm_len",
             params=["ant_arm_w", "ant_arm_len", "pole_pitch", "pole_slot"],
             sources=["gantry_params.scad"],
             ref="include <gantry_params.scad>\ninclude <pf_common.scad>\ntslot(ant_arm_w, ant_arm_w, ant_arm_len, 40, 10);",
             mat_key="ant_arm")
    carm = arm40(p.cam_arm_len_eff)
    REG.part("gantry_camera_arm_40x40", carm, domain=D, kind="fabricated", material=MAT_6063,
             desc="ANPR camera arm 40x40 T-slot, L = cam_arm_len_eff (250, file-local constant in gantry_camera_arm.scad)",
             params=["ant_arm_w", "cam_arm_len_eff", "pole_pitch", "pole_slot"],
             sources=["gantry_camera_arm.scad:cam_arm_len_eff"],
             ref=f"include <gantry_params.scad>\ninclude <pf_common.scad>\ntslot(40, 40, {p.cam_arm_len_eff:g}, 40, 10);",
             mat_key="cam_arm",
             notes="gantry_params.scad cam_arm_len = 300 is NOT used by the .scad model (it uses 250)")

    # ------------------------------------------------ yoke, tilt plate
    yk = yoke()
    REG.part("antenna_yoke", yk, domain=D, kind="fabricated", material=MAT_5052,
             desc="Antenna yoke, 5 mm 5052-H32, 2 x 90 deg bends R = t (bent state), pivot holes, tilt-lock arc slots",
             params=["yoke_t", "yoke_w", "yoke_web_d", "yoke_bend_r", "pivot_d", "pivot_drop", "ant_arm_w", "lock_r",
                     "lock_slot_w", "tilt_min", "tilt_max", "web_hole_pitch", "cheek_r", "cheek_bot_c"],
             sources=["gantry_params.scad", "gantry_antenna_bracket.scad:yoke,cheek_2d"],
             ref="include <gantry_params.scad>\nuse <gantry_antenna_bracket.scad>\nyoke();",
             file="antenna_yoke.step", mat_key="yoke")
    tp = tilt_plate()
    REG.part("antenna_tilt_plate", tp, domain=D, kind="fabricated", material=MAT_5052,
             desc="Antenna tilt plate, 5 mm 5052-H32, face + 2 ears (sharp-cornered bends; bend radius only in the DXF flat)",
             params=["yoke_t", "tp_w", "tp_h", "tp_off", "reader_hole_pitch", "pivot_d", "lock_r", "ear_half_h"],
             sources=["gantry_params.scad", "gantry_antenna_bracket.scad:tilt_plate,ear_2d,tilt_plate_face_2d"],
             ref="include <gantry_params.scad>\nuse <gantry_antenna_bracket.scad>\ntilt_plate();",
             file="antenna_tilt_plate.step", mat_key="tilt")
    aa = Asm("antenna_bracket")
    aa.add(Leaf("antenna_yoke", yk, "yoke_5052H32_5mm"))
    aa.add(Leaf("antenna_tilt_plate", tp, "tilt_plate_5052H32_5mm").moved(T(r=(p.ant_tilt, 0, 0))))
    REG.assembly("antenna_bracket_assy", aa, domain=D,
                 desc="Yoke + tilt plate at ant_tilt about the pivot axis (pivot hardware excluded)",
                 params=["ant_tilt"], sources=["gantry_antenna_bracket.scad"],
                 ref="include <gantry_params.scad>\nuse <gantry_antenna_bracket.scad>\nyoke();\nrotate([ant_tilt,0,0]) tilt_plate();",
                 file="antenna_bracket_assy.step")

    # ------------------------------------------------ plates
    cp = cam_plate()
    REG.part("gantry_camera_adapter_plate", cp, domain=D, kind="fabricated", material=MAT_5052,
             desc="Camera adapter plate 120x80x5 with 2 slots, 3-hole PCD pattern and cable hole",
             params=["cam_plate_l", "cam_plate_w", "cam_plate_t", "cam_mount_pcd"],
             sources=["gantry_params.scad", "gantry_camera_arm.scad:cam_plate_2d"],
             ref="include <gantry_params.scad>\nuse <gantry_camera_arm.scad>\nlinear_extrude(cam_plate_t) cam_plate_2d();",
             mat_key="cam_plate")
    sb = sign_bracket()
    REG.part("gantry_sign_bracket", sb, domain=D, kind="fabricated", material=MAT_5052,
             desc="P10 sign bracket 200x80x3 (modelled FLAT as in the .scad; the 'Z-bend' mentioned in its comment is not modelled)",
             params=["sign_br_t", "sign_br_l", "sign_br_w"],
             sources=["gantry_params.scad", "gantry_channel_cap_sign.scad:sign_bracket_2d"],
             ref="include <gantry_params.scad>\nuse <gantry_channel_cap_sign.scad>\nlinear_extrude(sign_br_t) sign_bracket_2d();",
             mat_key="sign_br")
    eb = edge_bracket()
    REG.part("gantry_edge_pole_bracket", eb, domain=D, kind="fabricated", material=MAT_MS,
             desc="Edge Node pole bracket 340x50x3 MS flat bar with 2 pole holes and 2 lug slots",
             params=["edge_br_l", "edge_br_w", "edge_br_t", "edge_lug_pitch"],
             sources=["gantry_channel_cap_sign.scad:edge_bracket_2d"],
             ref=f"include <gantry_params.scad>\nuse <gantry_channel_cap_sign.scad>\nlinear_extrude({p.edge_br_t:g}) edge_bracket_2d();",
             mat_key="edge_br")

    # ------------------------------------------------ printed
    pc = pole_cap()
    REG.part("gantry_pole_cap", pc, domain=D, kind="fabricated", material=MAT_ASA, color="print",
             desc="Pole cap (FDM ASA) with drip slope and 4 clip ribs",
             params=["pole_w", "cap_wall", "cap_h", "cap_clear"],
             sources=["gantry_params.scad", "gantry_channel_cap_sign.scad:pole_cap"],
             ref="include <gantry_params.scad>\nuse <gantry_channel_cap_sign.scad>\npole_cap();",
             mat_key="pole_cap")
    cb = cable_boot()
    REG.part("gantry_cable_boot", cb, domain=D, kind="fabricated", material=MAT_ASA, color="print",
             desc="Cable boot (FDM ASA): conduit to trunking transition (convex hull body, cavity, conduit bore)",
             params=["pole_w", "duct_w", "duct_d", "duct_z0", "boot_h", "conduit_d", "bp_t"],
             sources=["gantry_params.scad", "gantry_channel_cap_sign.scad:cable_boot_body_only"],
             ref="include <gantry_params.scad>\nuse <gantry_channel_cap_sign.scad>\ncable_boot_body_only();",
             mat_key="boot", notes="Hull body is a faceted B-rep (128-gon for the conduit circle), as the .scad hull is faceted")

    # ------------------------------------------------ bought-in envelopes
    ch = cable_channel()
    REG.part("gantry_cable_channel_envelope", ch, domain=D, kind="bought_envelope", material="PVC trunking (bought)",
             color="print", desc="Cable channel 40x25 PVC/ASA trunking incl. snap cover, cut to length (envelope)",
             params=["duct_w", "duct_d", "duct_t", "duct_z0", "duct_z1", "pole_w"],
             sources=["gantry_channel_cap_sign.scad:cable_channel"],
             ref="include <gantry_params.scad>\nuse <gantry_channel_cap_sign.scad>\ncable_channel();", mat_key="channel")
    cd = conduit()
    REG.part("gantry_conduit_envelope", cd, domain=D, kind="bought_envelope", material="flexible conduit (bought)",
             color="rubber", desc="Flexible conduit OD25 as a SOLID cylinder (envelope; the .scad also models it solid)",
             params=["conduit_d", "bp_t", "grout_gap", "duct_d", "pole_w"],
             sources=["gantry_channel_cap_sign.scad:cable_boot"],
             ref=None, notes="no separate reference STL (module is shared with the boot)")
    cb40 = corner_bracket40()
    REG.part("gantry_corner_bracket40_envelope", cb40, domain=D, kind="bought_envelope", material="cast Al (bought)",
             color="steel", desc="Cast 40-series corner bracket 40x35x4 with 3 mm rib (envelope)",
             params=[], sources=["pf_common.scad:corner_bracket40"],
             ref="include <pf_common.scad>\ncorner_bracket40();")
    rr = rfid_reader()
    REG.part("rfid_reader_envelope", rr, domain=D, kind="bought_envelope", material="bought",
             color="sensor", desc="UHF RFID reader envelope 260x260x60 (ASSUMED size) with M12 connector stub",
             params=["rfid_w", "rfid_h", "rfid_t"], sources=["pf_bought.scad:rfid_reader"],
             ref="use <pf_bought.scad>\nrfid_reader();")
    bc = bullet_camera()
    REG.part("bullet_camera_envelope", bc, domain=D, kind="bought_envelope", material="bought",
             color="sensor", desc="ANPR bullet camera envelope 220x80x80 (ASSUMED size), unpitched, optical axis +x",
             params=["cam_len", "cam_dia", "cam_knuckle"], sources=["pf_bought.scad:bullet_camera"],
             ref="use <pf_bought.scad>\nbullet_camera();")
    bca = bullet_camera_aimed()
    REG.part("bullet_camera_aimed_envelope", bca, domain=D, kind="bought_envelope", material="bought",
             color="sensor", desc="Camera envelope with ball-joint pitch cam_pitch applied (as mounted on the camera arm)",
             params=["cam_pitch", "cam_len", "cam_dia", "cam_knuckle"],
             sources=["gantry_camera_arm.scad:bullet_camera_aimed"],
             ref="include <gantry_params.scad>\nuse <gantry_camera_arm.scad>\nbullet_camera_aimed();")
    tray, mod, front, psu = p10_cabinet_parts()
    sign = Asm("p10_sign_cabinet")
    sign.add(Leaf("p10_cabinet_tray_envelope", tray, "cabinet_tray_5052_3mm", "struct"))
    sign.add(Leaf("p10_module_envelope", mod, "p10_led_module_320x160", "rubber"))
    sign.add(Leaf("p10_front_window_envelope", front, "pc_front_window", "sensor"))
    sign.add(Leaf("p10_driver_psu_envelope", psu, "led_driver_psu_120x80x20", "elec"))
    REG.part("p10_cabinet_tray_envelope", tray, domain=D, kind="bought_envelope", material="Al 5052-H32 (sheet tray)",
             desc="P10 cabinet tray 360x200x60, 3 mm walls/floor (envelope; the .scad lists it as bought 'cabinet')",
             params=["sign_cab_w", "sign_cab_h", "sign_cab_d"], sources=["pf_bought.scad:p10_cabinet"],
             ref=None, color="struct")
    REG.part("p10_module_envelope", mod, domain=D, kind="bought_envelope", material="bought",
             desc="P10 LED module block 320x160x13 (the 512 pixel cylinders are omitted)",
             params=["p10_w", "p10_h", "p10_t"], sources=["pf_bought.scad:p10_module"], color="rubber",
             ref=None,
             notes="512 LED pixel cylinders (D5 x 1.6, 8-gons) omitted: +2.2 % of module volume in the .scad")
    REG.part("p10_front_window_envelope", front, domain=D, kind="bought_envelope", material="polycarbonate (bought)",
             desc="Cabinet front window 354x194x2, TRIMMED to the tray opening (the .scad plate is 360x200 and overlaps the walls)",
             params=["sign_cab_w", "sign_cab_h", "sign_cab_d"], sources=["pf_bought.scad:p10_cabinet"], color="sensor",
             ref=None, notes="no reference STL (trimmed deliberately to avoid body interference)")
    REG.part("p10_driver_psu_envelope", psu, domain=D, kind="bought_envelope", material="bought",
             desc="5 V LED driver PSU block 120x80x20", params=[], sources=["pf_bought.scad:p10_cabinet"], color="elec",
             ref=None)
    REG.assembly("gantry_p10_sign_cabinet_assy", sign, domain=D,
                 desc="P10 sign cabinet envelope assembly (tray, LED module block, front window, driver PSU)",
                 params=["sign_cab_w", "sign_cab_h", "sign_cab_d", "p10_w", "p10_h", "p10_t"],
                 sources=["pf_bought.scad:p10_cabinet"],
                 ref="include <gantry_params.scad>\nuse <pf_bought.scad>\np10_cabinet(sign_cab_w, sign_cab_h, sign_cab_d);",
                 ref_note="reference STL includes 512 LED pixels and the full-size front plate overlapping the walls")

    # =========================================================== antenna arm assembly + gantry assembly
    t_pole = p.pole_w
    ant = Asm("antenna_arm_assembly")
    # arm: translate([pole_w/2, -ant_arm_w/2, ant_z]) rotate([0,90,0]) translate([0,ant_arm_w/2,0]) tslot(...)
    f_arm = compose(T((t_pole / 2, -p.ant_arm_w / 2, p.ant_z)), T(r=(0, 90, 0)), T((0, p.ant_arm_w / 2, 0)))
    ant.add(Leaf("gantry_antenna_arm_40x40", arm, "antenna_arm").moved(f_arm))
    f_cb1 = compose(T((t_pole / 2, -35 / 2, p.ant_z + p.ant_arm_w / 2)))
    f_cb2 = compose(T((t_pole / 2, 35 / 2, p.ant_z - p.ant_arm_w / 2)), T(r=(180, 0, 0)))
    ant.add(Leaf("gantry_corner_bracket40_envelope", cb40, "corner_bracket_top", "steel").moved(f_cb1))
    ant.add(Leaf("gantry_corner_bracket40_envelope", cb40, "corner_bracket_bottom", "steel").moved(f_cb2))
    yc = t_pole / 2 + p.ant_arm_len - p.yoke_w / 2
    f_y = T((yc, 0, p.ant_z - p.pivot_drop))
    ant.add(Leaf("antenna_yoke", yk, "yoke").moved(f_y))
    f_t = compose(f_y, T(r=(p.ant_tilt, 0, 0)))
    ant.add(Leaf("antenna_tilt_plate", tp, "tilt_plate").moved(f_t))
    f_r = compose(f_t, T((0, -p.tp_off - p.yoke_t, 0), (90, 0, 0)))
    ant.add(Leaf("rfid_reader_envelope", rr, "rfid_reader", "sensor").moved(f_r))
    REG.assembly("gantry_antenna_arm_assy", ant, domain=D,
                 desc="RFID antenna arm + 2 corner brackets + yoke + tilt plate + reader envelope, in the POLE frame",
                 params=["ant_z", "ant_arm_len", "pivot_drop", "ant_tilt", "yoke_w", "tp_off"],
                 sources=["gantry_antenna_bracket.scad:antenna_bracket_assy"],
                 ref="include <gantry_params.scad>\nuse <gantry_antenna_bracket.scad>\nantenna_bracket_assy(ant_tilt, 0);",
                 ref_note="reference STL also contains the M8 pivot bolts and nylon spacers (hardware, not in STEP)")

    cam = Asm("camera_arm_assembly")
    f_carm = compose(T((0, -p.pole_d / 2, p.cam_z)), T(r=(90, 0, 0)))
    cam.add(Leaf("gantry_camera_arm_40x40", carm, "camera_arm").moved(f_carm))
    cam.add(Leaf("gantry_corner_bracket40_envelope", cb40, "corner_bracket_a", "steel").moved(
        compose(T((0, -p.pole_d / 2, 0)), T((-35 / 2, 0, p.cam_z + 20)), T(r=(0, 0, -90)))))
    cam.add(Leaf("gantry_corner_bracket40_envelope", cb40, "corner_bracket_b", "steel").moved(
        compose(T((0, -p.pole_d / 2, 0)), T((35 / 2, 0, p.cam_z - 20)), T(r=(180, 0, -90)))))
    py = -p.pole_d / 2 - p.cam_arm_len_eff + p.cam_plate_l / 2 - p.cam_plate_overhang
    f_pl = compose(T((0, py, p.cam_z + 20)), T(r=(0, 0, -90)))
    cam.add(Leaf("gantry_camera_adapter_plate", cp, "camera_adapter_plate").moved(f_pl))
    f_cam = compose(f_pl, T((p.cam_plate_l / 2 - 35, 0, p.cam_plate_t)), T(r=(0, 0, p.cam_yaw)))
    cam.add(Leaf("bullet_camera_aimed_envelope", bca, "bullet_camera", "sensor").moved(f_cam))
    REG.assembly("gantry_camera_arm_assy", cam, domain=D,
                 desc="Camera arm + 2 corner brackets + adapter plate + aimed camera envelope, in the POLE frame",
                 params=["cam_z", "cam_arm_len_eff", "cam_plate_overhang", "cam_pitch", "cam_yaw"],
                 sources=["gantry_camera_arm.scad:camera_arm_assy"],
                 ref="include <gantry_params.scad>\nuse <gantry_camera_arm.scad>\ncamera_arm_assy(0);")

    # ------------------------------------------------ full gantry (edge node is nested later by build_step)
    return dict(wasm=wasm, pole=pole, pc=pc, cb=cb, ch=ch, cd=cd, ant=ant, cam=cam, sign=sign, eb=eb, sb=sb)


def gantry_assembly(parts, edge_asm=None):
    """Full gantry in the pole frame (explode = 0, no plinth, no anchors/bolts)."""
    p = P
    G = Asm("gantry_assembly")
    G.add(parts["wasm"])
    G.add(Leaf("gantry_pole_80x80", parts["pole"], "pole_80x80").moved(T((0, 0, p.bp_t))))
    G.add(Leaf("gantry_pole_cap", parts["pc"], "pole_cap", "print").moved(T((0, 0, p.bp_t + p.pole_len - p.cap_h + 2.4))))
    G.add(parts["ant"])
    G.add(parts["cam"])
    G.add(Leaf("gantry_cable_channel_envelope", parts["ch"], "cable_channel", "print"))
    G.add(Leaf("gantry_cable_boot", parts["cb"], "cable_boot", "print"))
    G.add(Leaf("gantry_conduit_envelope", parts["cd"], "flexible_conduit", "rubber"))
    # sign: brackets + cabinet
    for s in (-1, 1):
        f = compose(T((0, -p.pole_d / 2 - p.sign_br_l / 2 + 25, p.sign_z + s * 70)), T(r=(0, 0, 90)),
                    T((0, 0, -p.sign_br_t / 2)), T(r=(0, 0, 180)))
        G.add(Leaf("gantry_sign_bracket", parts["sb"], f"sign_bracket_{'up' if s > 0 else 'low'}").moved(f))
    f_cab = compose(T((0, -p.pole_d / 2 - p.sign_br_l + 50 - 30, p.sign_z)), T(r=(90, 0, 0)))
    G.add(parts["sign"].moved(f_cab))
    # edge brackets + edge node
    for s in (-1, 1):
        f = compose(T((0, p.pole_d / 2 + 1.5, p.edge_z + s * 150)), T(r=(90, 0, 0)), T((0, 0, -1.5)))
        G.add(Leaf("gantry_edge_pole_bracket", parts["eb"], f"edge_bracket_{'up' if s > 0 else 'low'}", "steel").moved(f))
    if edge_asm is not None:
        f_e = compose(T((0, p.pole_d / 2 + 3 + p.edge_standoff, p.edge_z)), T(r=(-90, 0, 0)), T(r=(0, 0, 180)))
        G.add(edge_asm.moved(f_e))
    return G
