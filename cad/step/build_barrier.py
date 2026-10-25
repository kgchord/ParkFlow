#!/usr/bin/env python3
"""
build_barrier.py - (c) DEMO BOOM BARRIER: fabricated parts, bought-in envelopes, assemblies.
World frame = barrier_assembly.scad frame (origin ground centre under housing, +x across lane / boom side when
closed, -y approach side, z up).  Rotor parts are modelled in the HUB-LOCAL frame of barrier_parts.scad
(x radial, y = carrier-plate normal = world z when closed, z = shaft axis = world -y) exactly as the scad does.
"""
import math
import cadquery as cq
from scadparams import load
from pf_cq import *            # noqa: F401,F403
from pf_reg import REG, Asm, Leaf, T, compose

P = load("barrier_parts.scad", "barrier_assembly.scad", "pf_bought.scad")
D = "barrier"
MS, A5052, A6061, A6063, ASA, EN8 = "IS2062-E250 (MS)", "Al 5052-H32", "Al 6061-T6", "Al 6063-T5", "ASA (FDM)", "EN8 (080M40) steel"


def corners(dx, dy):
    return [(sx * dx, sy * dy) for sx in (-1, 1) for sy in (-1, 1)]


# ------------------------------------------------------------------------------------ plates
def base_plate():
    p = P
    s = rbox(p.hs_x + 2 * p.hsg_bp_mx, p.hs_y + 2 * p.hsg_bp_mx, p.hsg_bp_t, 10)
    for sx, sy in corners(1, 1):
        s = s.cut(cyl(p.anchor_d + 2, p.hsg_bp_t + 2, at=(sx * (p.hs_x / 2 + p.hsg_bp_mx / 2 - 2),
                                                           sy * (p.hs_y / 2 + p.hsg_bp_mx / 2 - 2), -1)))
    return s.cut(cyl(40, p.hsg_bp_t + 2, at=(60, 0, -1)))


def front_panel():
    p = P
    s = box(p.hs_x, p.panel_t, p.hs_z, at=(-p.hs_x / 2, -p.panel_t, 0))   # == rotate([90,0,0]) linear_extrude(panel_t) panel_front_2d()
    zc = p.shaft_z - p.hsg_bp_t
    s = s.cut(cyl(p.shaft_d + 10, p.panel_t + 2, at=(0, -p.panel_t - 1, zc), axis="y"))
    for sg in (-1, 1):
        s = s.cut(cyl(10.5, p.panel_t + 2, at=(sg * 45, -p.panel_t - 1, zc), axis="y"))
    return s            # y in [-panel_t, 0]


def plain_panel(x, y, z):
    return box(x, y, z)


def motor_plate():
    p = P
    s = rbox_sharp(p.mplate_w, p.mplate_h, p.mplate_t)
    s = s.cut(cyl(26, p.mplate_t + 2, at=(0, 0, -1)))
    for x in (-35, 35):
        for z in (-25, 25):
            s = s.cut(cyl(6.6, p.mplate_t + 2, at=(-p.gm_shaft_off + x, z, -1)))
    for x, z in corners(p.mplate_w / 2 - 10, p.mplate_h / 2 - 10):
        s = s.cut(cyl(5.5, p.mplate_t + 2, at=(x, z, -1)))
    return s


def rbox_sharp(x, y, t):
    return box(x, y, t, at=(-x / 2, -y / 2, 0))


def bearing_plate():
    p = P
    w = p.hs_x - 2 * p.frame_w
    s = rbox_sharp(w, 100, p.mplate_t)
    s = s.cut(cyl(p.shaft_d + 10, p.mplate_t + 2, at=(0, 0, -1)))
    for sg in (-1, 1):
        s = s.cut(cyl(10.5, p.mplate_t + 2, at=(sg * 45, 0, -1)))
    for sg in (-1, 1):
        s = s.cut(cyl(5.5, p.mplate_t + 2, at=(sg * (w / 2 - 10), 0, -1)))
    return s


def limit_flag():
    p = P
    s = hull2d(circles=[(0, 0, 8)], rects=[(p.flag_r - 8 - 8, -10, p.flag_r - 8 + 8, 10)]).extrude(p.flag_t)
    return s.cut(cyl(5.5, p.flag_t + 2, at=(0, 0, -1)))


def carrier_plate():
    p = P
    s = hull2d(circles=[(p.hinge_r, 0, 20),
                        (p.hinge_r + p.carrier_l - 10, -p.carrier_w / 2 + 10, 10),
                        (p.hinge_r + p.carrier_l - 10, p.carrier_w / 2 - 10, 10)],
               rects=[(p.hinge_r + 20, -p.carrier_w / 2, p.hinge_r + 21, p.carrier_w / 2)]).extrude(p.carrier_t)
    s = s.cut(cyl(p.hinge_d + 0.3, p.carrier_t + 2, at=(p.hinge_r, 0, -1)))
    s = s.cut(cyl(p.shear_d + 0.1, p.carrier_t + 2, at=(p.hinge_r + p.shear_e, 0, -1)))
    for i in (0, 1):
        s = s.cut(cyl(6.6, p.carrier_t + 2, at=(p.hinge_r + 80 + i * p.clamp_pitch, 0, -1)))
    return s


def photo_foot():
    p = P
    s = rbox(p.pb_foot, p.pb_foot, 5, 6)
    for sx, sy in corners(35, 35):
        s = s.cut(cyl(8.5, 7, at=(sx, sy, -1)))
    for sg in (-1, 1):
        s = s.cut(cyl(5.5, 7, at=(sg * 10, 0, -1)))
    return s


def sensor_bracket():
    p = P
    c = [(p.lim_sw_r - 6) * math.cos(math.radians(a)) for a in (225, 315)]
    sn = [(p.lim_sw_r - 6) * math.sin(math.radians(a)) for a in (225, 315)]
    s = hull2d(circles=[(c[0], sn[0], 13), (c[1], sn[1], 13)]).extrude(3)
    return s.cut(cyl(p.shaft_d + 6, 5, at=(0, 0, -1)))         # hole lies outside the hull in the .scad too (no-op)


# ------------------------------------------------------------------------------------ rotating parts
def hub():
    p = P
    s = cyl(p.hub_d, p.hub_t, at=(0, 0, -p.hub_t / 2))
    s = s.union(box(p.tongue_l + p.hinge_r - 25, p.tongue_w, p.tongue_t, at=(0, -p.tongue_w / 2, -p.tongue_t / 2)))
    s = s.union(box(30, p.cw_bar_w, p.cw_bar_t, at=(-p.hub_d / 2 - 10, -p.cw_bar_w / 2, -p.cw_bar_t / 2)))
    s = s.cut(cyl(p.shaft_d + 0.05, p.hub_t + 2, at=(0, 0, -p.hub_t / 2 - 1)))
    s = s.cut(cyl(p.hinge_d + 0.2, p.tongue_w + 2, at=(p.hinge_r, -p.tongue_w / 2 - 1, 0), axis="y"))
    s = s.cut(cyl(p.shear_d + 0.1, p.tongue_w + 2, at=(p.hinge_r + p.shear_e, -p.tongue_w / 2 - 1, 0), axis="y"))
    s = s.cut(box(6, 4, 2 * p.hub_t, at=(-3, p.shaft_d / 2 - 1, -p.hub_t)))
    return s


def shear_pin():
    p = P
    L = p.tongue_w + 2 * p.carrier_t + 6
    return cyl(p.shear_d, L, at=(0, -p.tongue_w / 2 - p.carrier_t - 3, 0), axis="y").translate(V(p.hinge_r + p.shear_e, 0, 0))


def boom_tube():
    p = P
    r0 = p.hinge_r + 60
    return rhs(p.boom_h, p.boom_b, p.boom_t, p.boom_L - r0 - p.tip_cap_l)


def boom_tip_cap():
    """boom_tip_cap_print() of export_parts.scad (the printed part; spigot into the tube)."""
    outer = loft_rr(64, 34, 4, 20, 50, 24, 4, 29, 1)
    spig = rbox(56.6, 26.6, 25, 1, at=(0, 0, -25))
    s = outer.union(spig)
    return s.cut(rbox(50, 20, 40, 1, at=(0, 0, -26)))


def loft_rr(w0, h0, r0, z0, w1, h1, r1, z1, t1):
    """hull of rbox(w0,h0,z0,r0) and a thin rbox(w1,h1,t1,r1) at z1 == ruled loft between same-radius rounded rectangles."""
    body = rbox(w0, h0, z0, r0)
    s0 = cq.Sketch().rect(w0, h0).vertices().fillet(r0)
    s1 = cq.Sketch().rect(w1, h1).vertices().fillet(r1)
    loft = (cq.Workplane("XY").workplane(offset=z0).placeSketch(s0, s1.moved(cq.Location(V(0, 0, z1 - z0)))).loft(ruled=True))
    top = rbox(w1, h1, t1, r1, at=(0, 0, z1))
    return body.union(loft).union(top)


def cw_bar():
    p = P
    return box(p.cw_arm + p.cw_plate_x / 2 - p.hub_d / 2 + 20, p.cw_bar_w, p.cw_bar_t,
               at=(-p.cw_arm - p.cw_plate_x / 2 - 10, -p.cw_bar_w / 2, -p.cw_bar_t / 2))


def cw_plate():
    p = P
    return box(p.cw_plate_x, p.cw_plate_z, p.cw_plate_t - 0.3)


def post_cap():
    return rbox(24, 24, 8, 3).cut(rbox(20.4, 20.4, 6, 1, at=(0, 0, -1)))


# ------------------------------------------------------------------------------------ bought-in envelopes
def flange_bearing():
    """UCFL204-class unit: hull flange 11 thick, boss D46 x 24, collar D34 x 36; local z -> world -y via rotate([90,0,0])."""
    flange = hull2d(circles=[(-45, 0, 13), (45, 0, 13), (0, 0, 30)]).extrude(11)
    boss = cyl(46, 24)
    collar = cyl(34, 36, at=(0, 0, -6))
    return rotate(union(flange, boss, collar), (90, 0, 0))


def gearmotor():
    p = P
    gb = box(p.gm_box_x, p.gm_box_y, p.gm_box_z, at=(-p.gm_box_x / 2, -p.gm_box_y / 2, -p.gm_box_z))
    mot = rotate(cyl(p.gm_motor_d, p.gm_motor_l), (0, -90, 0)).translate(V(-p.gm_box_x / 2, -p.gm_box_y / 2 + 37, -p.gm_box_z / 2 - 10))
    sh = cyl(p.gm_shaft_d, p.gm_shaft_l).cut(box(5, 20, 40, at=(p.gm_shaft_d / 2 - 1.2, -10, 5)))
    return union(gb, mot, sh.translate(V(p.gm_shaft_off, 0, 0)))


def jaw_coupling():
    return cyl(P.coup_d, P.coup_l)       # axis +z; placed with rotate([90,0,0])


def photo_head():
    head = cyl(18, 60, axis="x")
    nut = rotate(hexp(27, 4), (0, 90, 0)).translate(V(10, 0, 0))
    lens = cyl(12, 0.6, axis="x", at=(60, 0, 0))
    return union(head, nut, lens)


def m12_sensor():
    return cyl(12, 45)


# ------------------------------------------------------------------------------------ build
def build():
    p = P
    hy_front = -p.hs_y / 2
    hub_y = hy_front - p.panel_t - p.hub_gap - p.hub_t / 2
    bp = base_plate()
    REG.part("barrier_base_plate", bp, domain=D, kind="fabricated", material=MS, color="steel",
             desc="Housing base plate 360x310x8 (hs + 2 x hsg_bp_mx), 4 anchor holes D12, cable entry D40 (laser cut)",
             params=["hs_x", "hs_y", "hsg_bp_t", "hsg_bp_mx", "anchor_d"], sources=["barrier_params.scad", "barrier_parts.scad:housing_base_plate_2d"],
             ref="include <barrier_params.scad>\nuse <barrier_parts.scad>\nlinear_extrude(hsg_bp_t) housing_base_plate_2d();", mat_key="bar_base")
    # frame
    post = tslot(p.frame_w, p.frame_w, p.hs_z - 2, 20, 6)
    rail_x = tslot(p.frame_w, p.frame_w, p.hs_x - 2 * p.frame_w, 20, 6)
    rail_y = tslot(p.frame_w, p.frame_w, p.hs_y - 2 * p.frame_w, 20, 6)
    REG.part("barrier_frame_post_20x20", post, domain=D, kind="fabricated", material=A6063, color="struct",
             desc="Frame post 20x20 T-slot (generic profile), length hs_z - 2", params=["frame_w", "hs_z"],
             sources=["barrier_params.scad", "pf_common.scad:tslot2d"],
             ref=f"include <barrier_params.scad>\ninclude <pf_common.scad>\ntslot(frame_w, frame_w, hs_z - 2, 20, 6);", mat_key="bar_frame",
             notes="generic profile; MATERIALS/calcs use 0.5 kg/m")
    REG.part("barrier_frame_rail_x_20x20", rail_x, domain=D, kind="fabricated", material=A6063, color="struct",
             desc="Frame rail along x, length hs_x - 2 frame_w", params=["frame_w", "hs_x"], sources=["barrier_params.scad"],
             ref="include <barrier_params.scad>\ninclude <pf_common.scad>\ntslot(frame_w, frame_w, hs_x - 2*frame_w, 20, 6);", mat_key="bar_frame")
    REG.part("barrier_frame_rail_y_20x20", rail_y, domain=D, kind="fabricated", material=A6063, color="struct",
             desc="Frame rail along y, length hs_y - 2 frame_w", params=["frame_w", "hs_y"], sources=["barrier_params.scad"],
             ref="include <barrier_params.scad>\ninclude <pf_common.scad>\ntslot(frame_w, frame_w, hs_y - 2*frame_w, 20, 6);", mat_key="bar_frame")
    fp = front_panel()
    REG.part("barrier_front_panel", fp, domain=D, kind="fabricated", material=A5052, color="struct",
             desc="Front skin 300x800x2 with shaft hole D30 and 2 bearing bolt holes (STEP frame: x across, y thickness, z up)",
             params=["hs_x", "hs_z", "panel_t", "shaft_z", "hsg_bp_t", "shaft_d"], sources=["barrier_parts.scad:panel_front_2d"],
             ref="include <barrier_params.scad>\nuse <barrier_parts.scad>\nrotate([90,0,0]) linear_extrude(panel_t) panel_front_2d();",
             mat_key="bar_skins", notes="in the .scad the panel sits at y = -hs_y/2 .. -hs_y/2+panel_t, i.e. INSIDE the frame envelope (overlaps posts/rails by 2 mm)")
    back = plain_panel(p.hs_x, p.panel_t, p.hs_z)
    REG.part("barrier_back_panel", back, domain=D, kind="fabricated", material=A5052, color="struct",
             desc="Back skin / access door 300x800x2 (plain, as in the .scad)", params=["hs_x", "hs_z", "panel_t"],
             sources=["barrier_parts.scad:housing_skins"], ref=None, mat_key="bar_skins")
    side = plain_panel(p.panel_t, p.hs_y, p.hs_z)
    REG.part("barrier_side_panel", side, domain=D, kind="fabricated", material=A5052, color="struct",
             desc="Side skin 250x800x2 (x2, plain)", params=["hs_y", "hs_z", "panel_t"], sources=["barrier_parts.scad:housing_skins"],
             ref=None, mat_key="bar_skins")
    roof = box(p.hs_x + 20, p.hs_y + 30, p.roof_t, at=(-(p.hs_x + 20) / 2, -(p.hs_y + 30) / 2, 0))
    REG.part("barrier_roof", roof, domain=D, kind="fabricated", material=A5052, color="struct",
             desc="Roof 320x280x3 (installed with 5 deg fall)", params=["hs_x", "hs_y", "roof_t"], sources=["barrier_parts.scad:housing_skins"],
             ref=None, mat_key="bar_skins")
    mpl = motor_plate()
    REG.part("barrier_motor_plate", mpl, domain=D, kind="fabricated", material=A6061, color="struct",
             desc="Motor plate 200x150x6 (gearmotor 4xM6 pattern, corner T-nut holes)", params=["mplate_w", "mplate_h", "mplate_t", "gm_shaft_off"],
             sources=["barrier_parts.scad:motor_plate_2d"],
             ref="include <barrier_params.scad>\nuse <barrier_parts.scad>\nlinear_extrude(mplate_t) motor_plate_2d();", mat_key="bar_motor_plate")
    bpl = bearing_plate()
    REG.part("barrier_bearing_plate", bpl, domain=D, kind="fabricated", material=A6061, color="struct",
             desc="Bearing plate 260x100x6", params=["hs_x", "frame_w", "mplate_t", "shaft_d"], sources=["barrier_parts.scad:bearing_plate_2d"],
             ref="include <barrier_params.scad>\nuse <barrier_parts.scad>\nlinear_extrude(mplate_t) bearing_plate_2d();", mat_key="bar_bearing_plate")
    shaft_len = (p.gm_face_y - 40) - (hub_y - p.hub_t / 2) + 5
    shaft = cyl(p.shaft_d, shaft_len)
    REG.part("barrier_stub_shaft", shaft, domain=D, kind="fabricated", material=EN8, color="move",
             desc="Stub shaft D20 (keyways NOT modelled in the shaft, as in the .scad), length from gm_face_y/hub_y",
             params=["shaft_d", "gm_face_y", "hub_t", "hub_gap", "panel_t", "hs_y"], sources=["barrier_parts.scad:drive_train"],
             ref=None, mat_key="bar_shaft")
    hb = hub()
    REG.part("barrier_hub", hb, domain=D, kind="fabricated", material=A6061, color="move",
             desc="Hub D70x16 with tongue 90x60x12, tail stub, hinge bore, shear-pin bore, keyway (HUB-LOCAL frame)",
             params=["hub_d", "hub_t", "tongue_l", "tongue_t", "tongue_w", "hinge_r", "hinge_d", "shear_e", "shear_d", "shaft_d", "cw_bar_w", "cw_bar_t"],
             sources=["barrier_parts.scad:hub"], ref="include <barrier_params.scad>\nuse <barrier_parts.scad>\nhub();", mat_key="bar_hub")
    fl = limit_flag()
    REG.part("barrier_limit_flag", fl, domain=D, kind="fabricated", material=A5052, color="move",
             desc="Limit flag 3 mm", params=["flag_r", "flag_t"], sources=["barrier_parts.scad:limit_flag_2d"],
             ref="include <barrier_params.scad>\nuse <barrier_parts.scad>\nlinear_extrude(flag_t) limit_flag_2d();", mat_key="bar_flag")
    cp = carrier_plate()
    REG.part("barrier_carrier_plate", cp, domain=D, kind="fabricated", material=A6061, color="move",
             desc="Breakaway carrier clevis plate 5 mm (x2): hinge M8, shear pin D5, clamp holes", params=["carrier_l", "carrier_w", "carrier_t", "hinge_r", "hinge_d", "shear_e", "shear_d", "clamp_pitch"],
             sources=["barrier_parts.scad:carrier_plate_2d"],
             ref="include <barrier_params.scad>\nuse <barrier_parts.scad>\nlinear_extrude(carrier_t) carrier_plate_2d();", mat_key="bar_carrier")
    sp = shear_pin()
    REG.part("barrier_shear_pin", sp, domain=D, kind="fabricated", material=A6061, color="hw",
             desc="Sacrificial shear pin D5, length tongue_w + 2 carrier_t + 6 (HUB-LOCAL frame, axis y)", params=["shear_d", "tongue_w", "carrier_t", "hinge_r", "shear_e"],
             sources=["barrier_parts.scad:carrier"], ref=None, mat_key="bar_pin")
    bt = boom_tube()
    REG.part("barrier_boom_tube", bt, domain=D, kind="fabricated", material=A6063, color="move",
             desc="Boom: rect tube 60x30x1.5 (STEP frame: along +z, 60 along x), length boom_L - (hinge_r+60) - tip_cap_l",
             params=["boom_h", "boom_b", "boom_t", "boom_L", "hinge_r", "tip_cap_l"], sources=["barrier_parts.scad:boom"],
             ref=f"include <barrier_params.scad>\ninclude <pf_common.scad>\nrhs(boom_h, boom_b, boom_t, {p.boom_L - p.hinge_r - 60 - p.tip_cap_l:g});",
             mat_key="bar_boom", notes="length 1065 mm; MATERIALS.md says L 1135")
    tc = boom_tip_cap()
    REG.part("barrier_boom_tip_cap", tc, domain=D, kind="fabricated", material=ASA, color="print",
             desc="Boom tip cap (FDM ASA) = boom_tip_cap_print() of export_parts.scad (spigot + hollow nose)", params=["boom_h", "boom_b"],
             sources=["export_parts.scad:boom_tip_cap_print"], ref="use <export_parts.scad>\nboom_tip_cap_print();", mat_key="bar_tipcap",
             notes="barrier_assembly.scad draws a DIFFERENT (solid, spigot-less) inline cap; the printed part is used here")
    cbar = cw_bar()
    REG.part("barrier_cw_tail_bar", cbar, domain=D, kind="fabricated", material=MS, color="steel",
             desc="Counterweight tail bar 40x10 flat", params=["cw_arm", "cw_plate_x", "hub_d", "cw_bar_w", "cw_bar_t"],
             sources=["barrier_parts.scad:counterweight"], ref=None, mat_key="bar_cw_bar")
    cpl = cw_plate()
    REG.part("barrier_cw_plate", cpl, domain=D, kind="fabricated", material=MS, color="steel",
             desc="Counterweight plate 100x60x9.7 (cw_plate_t - 0.3 as modelled; MATERIALS says 10 mm), x cw_n", params=["cw_plate_x", "cw_plate_z", "cw_plate_t", "cw_n"],
             sources=["barrier_parts.scad:counterweight"], ref=None, mat_key="bar_cw_plate")
    pf = photo_foot()
    REG.part("barrier_photo_post_foot", pf, domain=D, kind="fabricated", material=MS, color="steel",
             desc="Photo-beam post foot plate 100x100x5", params=["pb_foot"], sources=["barrier_parts.scad:pb_foot_2d"],
             ref="include <barrier_params.scad>\nuse <barrier_parts.scad>\nlinear_extrude(5) pb_foot_2d();", mat_key="bar_foot")
    pp = tslot(20, 20, p.pb_post_h, 20, 6)
    REG.part("barrier_photo_post_20x20", pp, domain=D, kind="fabricated", material=A6063, color="struct",
             desc="Photo-beam post 20x20 T-slot (generic profile) x pb_post_h", params=["pb_post_h"], sources=["barrier_parts.scad:photo_post"],
             ref="include <barrier_params.scad>\ninclude <pf_common.scad>\ntslot(20, 20, pb_post_h, 20, 6);", mat_key="bar_post")
    pcap = post_cap()
    REG.part("barrier_photo_post_cap", pcap, domain=D, kind="fabricated", material=ASA, color="print",
             desc="Photo-beam post cap (FDM ASA) = pb_post_cap_print()", params=[], sources=["export_parts.scad:pb_post_cap_print"],
             ref="use <export_parts.scad>\npb_post_cap_print();", mat_key="bar_postcap",
             notes="assembly .scad draws a solid 24x24x6 cap instead; printed part used here")
    sb = sensor_bracket()
    REG.part("barrier_limit_sensor_bracket", sb, domain=D, kind="fabricated", material=A5052, color="struct",
             desc="Limit-sensor bracket 3 mm (stadium plate; no DXF exists for it)", params=["lim_sw_r", "shaft_d"],
             sources=["barrier_parts.scad:limit_sensors"], ref=None, mat_key="bar_sens_br")
    # envelopes
    fb = flange_bearing()
    REG.part("barrier_flange_bearing_envelope", fb, domain=D, kind="bought_envelope", material="bought (UCFL204 class)", color="hw",
             desc="2-bolt flange bearing envelope (SOLID, no bore - interferes with the shaft in the assembly)", params=["brg_flange"],
             sources=["barrier_parts.scad:flange_bearing"], ref="include <barrier_params.scad>\nuse <barrier_parts.scad>\nflange_bearing();")
    gm = gearmotor()
    REG.part("barrier_gearmotor_envelope", gm, domain=D, kind="bought_envelope", material="bought", color="hw",
             desc="24 V worm gearmotor envelope (ASSUMED 90x75x70 gearbox, D60x110 motor, D12 shaft with D-flat)",
             params=["gm_box_x", "gm_box_y", "gm_box_z", "gm_motor_d", "gm_motor_l", "gm_shaft_d", "gm_shaft_l", "gm_shaft_off"],
             sources=["pf_bought.scad:gearmotor"], ref="use <pf_bought.scad>\ngearmotor();")
    jc = jaw_coupling()
    REG.part("barrier_jaw_coupling_envelope", jc, domain=D, kind="bought_envelope", material="bought", color="move",
             desc="Jaw coupling D30x30 envelope (solid)", params=["coup_d", "coup_l"], sources=["barrier_parts.scad:drive_train"], ref=None)
    ph = photo_head()
    REG.part("barrier_photo_head_envelope", ph, domain=D, kind="bought_envelope", material="bought", color="sensor",
             desc="M18 through-beam photo-electric head with nut and lens disc", params=[], sources=["pf_bought.scad:photo_head"],
             ref="use <pf_bought.scad>\nphoto_head();")
    ms = m12_sensor()
    REG.part("barrier_m12_inductive_sensor_envelope", ms, domain=D, kind="bought_envelope", material="bought", color="sensor",
             desc="M12 inductive proximity sensor envelope D12 x 45", params=[], sources=["barrier_parts.scad:limit_sensors"], ref=None)

    # =================================================================== HOUSING assembly (world frame)
    H = Asm("barrier_housing")
    H.add(Leaf("barrier_base_plate", bp, "base_plate_8mm_MS", "steel"))
    for sx, sy in corners(1, 1):
        H.add(Leaf("barrier_frame_post_20x20", post, f"frame_post_{sx:+d}{sy:+d}").moved(
            T((sx * (p.hs_x / 2 - p.frame_w / 2), sy * (p.hs_y / 2 - p.frame_w / 2), p.hsg_bp_t))))
    zs = [p.hsg_bp_t, p.hsg_bp_t + p.hs_z - p.frame_w - 2]
    for zi, z in enumerate(zs):
        for sy in (-1, 1):
            f = compose(T((-p.hs_x / 2 + p.frame_w, sy * (p.hs_y / 2 - p.frame_w / 2), z + p.frame_w / 2)), T(r=(0, 90, 0)))
            H.add(Leaf("barrier_frame_rail_x_20x20", rail_x, f"rail_x_z{zi}_{sy:+d}").moved(f))
        for sx in (-1, 1):
            f = compose(T((sx * (p.hs_x / 2 - p.frame_w / 2), -p.hs_y / 2 + p.frame_w, z + p.frame_w / 2)), T(r=(-90, 0, 0)))
            H.add(Leaf("barrier_frame_rail_y_20x20", rail_y, f"rail_y_z{zi}_{sx:+d}").moved(f))
    # skins
    H.add(Leaf("barrier_front_panel", fp, "front_panel").moved(T((0, -p.hs_y / 2 + p.panel_t, p.hsg_bp_t))))
    H.add(Leaf("barrier_back_panel", back, "back_panel").moved(T((-p.hs_x / 2, p.hs_y / 2 - 0.01, p.hsg_bp_t))))
    for s in (-1, 1):
        H.add(Leaf("barrier_side_panel", side, f"side_panel_{s:+d}").moved(
            T((s * (p.hs_x / 2) - (0 if s > 0 else p.panel_t), -p.hs_y / 2, p.hsg_bp_t))))
    H.add(Leaf("barrier_roof", roof, "roof").moved(compose(T((0, 0, p.hsg_bp_t + p.hs_z)), T(r=(5, 0, 0)))))
    REG.assembly("barrier_housing_assy", H, domain=D,
                 desc="Housing: base plate, 12 frame extrusions (4 posts + 8 rails), 4 skins, roof (hazard-band decals, anchor nuts excluded)",
                 params=["hs_x", "hs_y", "hs_z", "hsg_bp_t", "frame_w", "panel_t", "roof_t"], sources=["barrier_assembly.scad:barrier"],
                 ref="include <barrier_params.scad>\nuse <barrier_parts.scad>\nlinear_extrude(hsg_bp_t) housing_base_plate_2d();\nhousing_frame();\nhousing_skins();",
                 ref_note="reference STL also contains 8 hazard-band decal strips 0.5 mm thick")

    # =================================================================== DRIVE TRAIN (world frame)
    DT = Asm("barrier_drive_train")
    DT.add(Leaf("barrier_motor_plate", mpl, "motor_plate", "struct").moved(compose(T((0, p.gm_face_y, p.shaft_z)), T(r=(90, 0, 0)))))
    DT.add(Leaf("barrier_gearmotor_envelope", gm, "gearmotor", "hw").moved(
        compose(T((0, p.gm_face_y, p.shaft_z)), T(r=(90, 0, 0)), T((-p.gm_shaft_off, 0, 0)))))
    DT.add(Leaf("barrier_jaw_coupling_envelope", jc, "jaw_coupling", "move").moved(
        compose(T((0, p.gm_face_y - 15, p.shaft_z)), T(r=(90, 0, 0)))))
    DT.add(Leaf("barrier_bearing_plate", bpl, "bearing_plate", "struct").moved(
        compose(T((0, p.brg_plate_y, p.shaft_z)), T(r=(90, 0, 0)))))
    DT.add(Leaf("barrier_flange_bearing_envelope", fb, "flange_bearing_rear", "hw").moved(
        T((0, p.brg_plate_y - p.mplate_t, p.shaft_z))))
    DT.add(Leaf("barrier_flange_bearing_envelope", fb, "flange_bearing_front", "hw").moved(T((0, -p.hs_y / 2, p.shaft_z))))
    DT.add(Leaf("barrier_stub_shaft", shaft, "stub_shaft", "move").moved(
        compose(T((0, p.gm_face_y - 40, p.shaft_z)), T(r=(90, 0, 0)))))
    REG.assembly("barrier_drive_train_assy", DT, domain=D,
                 desc="Drive train: motor plate, gearmotor, coupling, bearing plate, 2 flange bearings, stub shaft (world frame)",
                 params=["shaft_z", "gm_face_y", "brg_plate_y", "mplate_t"], sources=["barrier_parts.scad:drive_train"],
                 ref="include <barrier_params.scad>\nuse <barrier_parts.scad>\ndrive_train(0);")

    # =================================================================== ROTOR (hub-local frame)
    R = Asm("barrier_rotor")
    R.add(Leaf("barrier_hub", hb, "hub", "move"))
    R.add(Leaf("barrier_limit_flag", fl, "limit_flag", "move").moved(
        compose(T(r=(0, 0, 225)), T((0, 0, p.hub_t / 2)))))
    for s in (-1, 1):
        R.add(Leaf("barrier_carrier_plate", cp, f"carrier_plate_{s:+d}", "move").moved(
            compose(T((0, s * (p.tongue_w / 2 + p.carrier_t / 2 + 0.5), 0)), T(r=(90, 0, 0)), T((0, 0, -p.carrier_t / 2)))))
    R.add(Leaf("barrier_shear_pin", sp, "shear_pin", "hw"))
    r0 = p.hinge_r + 60
    fb_ = compose(T((r0, 0, 0)), T(r=(0, 90, 0)), T(r=(0, 0, 90)))
    R.add(Leaf("barrier_boom_tube", bt, "boom_tube", "move").moved(fb_))
    R.add(Leaf("barrier_boom_tip_cap", tc, "boom_tip_cap", "print").moved(
        compose(fb_, T((0, 0, p.boom_L - r0 - p.tip_cap_l)))))
    R.add(Leaf("barrier_cw_tail_bar", cbar, "counterweight_tail_bar", "steel"))
    for i in range(int(p.cw_n)):
        R.add(Leaf("barrier_cw_plate", cpl, f"counterweight_plate_{i}", "steel").moved(
            T((-p.cw_arm - p.cw_plate_x / 2, -p.cw_plate_z / 2, p.cw_bar_t / 2 + i * p.cw_plate_t))))
    REG.assembly("barrier_rotor_assy", R, domain=D,
                 desc="Rotating group in HUB-LOCAL frame (boom_angle = 0): hub, flag, carrier, shear pin, boom, tip cap, counterweight",
                 params=["boom_L", "hinge_r", "cw_n", "cw_arm"], sources=["barrier_parts.scad:rotor"],
                 ref="include <barrier_params.scad>\nuse <barrier_parts.scad>\nrotor(0);",
                 ref_note="reference STL also contains the M8 hinge bolt, 2 M6 clamp bolts, 2 M8 counterweight studs, red tape bands and a different (solid) inline tip cap")

    # =================================================================== limit sensors (hub-local, fixed)
    LS = Asm("barrier_limit_sensors")
    for a in (225, 315):
        LS.add(Leaf("barrier_m12_inductive_sensor_envelope", ms, f"inductive_sensor_{a}", "sensor").moved(
            compose(T(r=(0, 0, a)), T((p.lim_sw_r - 6, 0, p.hub_t / 2 + p.flag_t + 3)))))
    LS.add(Leaf("barrier_limit_sensor_bracket", sb, "sensor_bracket", "struct").moved(T((0, 0, p.hub_t / 2 + p.flag_t + 48))))
    REG.assembly("barrier_limit_sensors_assy", LS, domain=D, desc="Two M12 inductive sensors + bracket (hub-local frame)",
                 params=["lim_sw_r", "hub_t", "flag_t"], sources=["barrier_parts.scad:limit_sensors"],
                 ref="include <barrier_params.scad>\nuse <barrier_parts.scad>\nlimit_sensors();")

    # =================================================================== photo-beam posts (world)
    def post_asm(name, dir_):
        A = Asm(name)
        A.add(Leaf("barrier_photo_post_foot", pf, "foot", "steel"))
        A.add(Leaf("barrier_photo_post_20x20", pp, "post", "struct").moved(T((0, 0, 5))))
        A.add(Leaf("barrier_photo_post_cap", pcap, "cap", "print").moved(T((0, 0, 5 + p.pb_post_h))))
        A.add(Leaf("barrier_photo_head_envelope", ph, "photo_head", "sensor").moved(
            compose(T((dir_ * 10, 0, p.pb_z)), T(r=(0, 0, 0 if dir_ > 0 else 180)))))
        return A
    pa1, pa2 = post_asm("photo_post_1", 1), post_asm("photo_post_2", -1)
    REG.assembly("barrier_photo_post_assy", pa1, domain=D,
                 desc="Photo-beam post (emitter side, local frame, dir = +1): foot, post, cap, M18 head",
                 params=["pb_post_h", "pb_z", "pb_foot"], sources=["barrier_parts.scad:photo_post"],
                 ref="include <barrier_params.scad>\nuse <barrier_parts.scad>\nphoto_post(1, 0);",
                 ref_note="reference photo_post() draws a solid 24x24x6 cap instead of the printed hollow cap")

    # =================================================================== full barrier (world frame, explode 0, boom_angle from params)
    B = Asm("boom_barrier_assembly")
    B.add(H)
    B.add(DT)
    rot = compose(T((0, hub_y, p.shaft_z)), T(r=(90, 0, 0)))
    B.add(R.moved(compose(rot, T(r=(0, 0, p.boom_angle)))))
    B.add(LS.moved(rot))
    by = hub_y + p.pb_dy
    B.add(pa1.moved(T((p.hs_x / 2 + 60, by, 0))))
    B.add(pa2.moved(T((p.pb_x2, by, 0))))
    REG.assembly("barrier_assembly", B, domain=D,
                 desc="Demo boom barrier: housing, drive train, rotor (boom_angle from params), limit sensors, photo-beam posts at hs_x/2+60 and pb_x2",
                 params=["boom_angle", "pb_x2", "pb_dy", "pb_z"], sources=["barrier_assembly.scad:barrier"],
                 ref="include <barrier_params.scad>\nuse <barrier_assembly.scad>\nbarrier(0, boom_angle, 0);",
                 ref_note="reference STL additionally has anchor nuts, hinge/clamp bolts, studs, decals, tape bands, beam line, solid inline caps")
    return dict(B=B, H=H, DT=DT, R=R, LS=LS, pa1=pa1, pa2=pa2, hub_y=hub_y)
