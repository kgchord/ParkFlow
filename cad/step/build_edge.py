#!/usr/bin/env python3
"""
build_edge.py - (b) EDGE NODE IP65 ENCLOSURE: fabricated parts, bought-in envelopes, assemblies.
Frame (OpenSCAD edge frame): x = width, y = height, z = out of the mounting wall towards the lid;
z = 0 is the enclosure back outer face.  All numbers come from edge_params.scad / pf_bought.scad via scadparams.
"""
import math
import cadquery as cq
from scadparams import load
from pf_cq import *            # noqa: F401,F403
from pf_reg import REG, Asm, Leaf, T, compose

P = load("edge_internals.scad", "edge_enclosure.scad", "edge_node_assembly.scad", "pf_bought.scad")
D = "edge"
MAT_5052, MAT_6061, MAT_6063, MAT_ASA = "Al 5052-H32", "Al 6061-T6", "Al 6063-T5", "ASA (FDM)"
MAT_PC = "Polycarbonate (bought enclosure)"
# internals(): device list on the DIN rail [x of device corner, modules] - copied from the module body of
# edge_internals.scad (they are literals inside the module, not parameters), see manifest "limitations".
DIN_DEVICES = [(-115, 2), (-78, 2), (-40, 1), (-20, 1), (0, 1), (20, 1), (40, 1), (55, 1), (70, 1)]
DIN_H = 70


def corners(dx, dy):
    return [(sx * dx, sy * dy) for sx in (-1, 1) for sy in (-1, 1)]


def ring(w_out, h_out, r_out, w_in, h_in, r_in, z0, h):
    o = rbox(w_out, h_out, h, r_out, at=(0, 0, z0))
    return o.cut(rbox(w_in, h_in, h + 2, r_in, at=(0, 0, z0 - 1)))


# ---------------------------------------------------------------------------------- enclosure
def enclosure_base():
    p = P
    base_d = p.enc_d - p.enc_lid_d
    s = rbox(p.enc_w, p.enc_h, base_d, p.enc_r).cut(
        rbox(p.enc_w - 2 * p.enc_wall, p.enc_h - 2 * p.enc_wall, base_d, p.enc_r - p.enc_wall, at=(0, 0, p.enc_wall)))
    tongue = ring(p.enc_w - p.enc_wall + p.tongue_w, p.enc_h - p.enc_wall + p.tongue_w, p.enc_r - p.enc_wall / 2,
                  p.enc_w - p.enc_wall - p.tongue_w, p.enc_h - p.enc_wall - p.tongue_w, p.enc_r - p.enc_wall / 2 - 1,
                  base_d, p.tongue_h)
    s = s.union(tongue)
    for (x, y) in corners(p.enc_w / 2 - p.lid_boss_in, p.enc_h / 2 - p.lid_boss_in):
        s = s.union(cyl(p.lid_boss_d, base_d, at=(x, y, 0)))
    for (x, y) in corners(p.bp_boss_dx / 2, p.bp_boss_dy / 2):
        s = s.union(cyl(p.bp_boss_d, p.enc_wall + p.bp_boss_h, at=(x, y, 0)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            lug = hull2d(circles=[(sx * p.mlug_x - sx * 15, sy * p.mlug_y, p.mlug_w / 2),
                                  (sx * p.mlug_x, sy * p.mlug_y, (p.mlug_w * 0.5 + 6) / 2)]).extrude(8)
            s = s.union(lug)
    tools = []
    for (x, y) in corners(p.enc_w / 2 - p.lid_boss_in, p.enc_h / 2 - p.lid_boss_in):
        tools.append(cyl(5.6, 30, at=(x, y, base_d - 20)))
    for (x, y) in corners(p.bp_boss_dx / 2, p.bp_boss_dy / 2):
        tools.append(cyl(5.6, 30, at=(x, y, 2)))
    for (x, y) in corners(p.mlug_x, p.mlug_y):
        tools.append(cyl(6.6, 20, at=(x, y, -1)))
    for gx, gm in zip(p.gland_x, p.gland_m):
        tools.append(cyl(gm + 0.5, p.enc_wall + 2, at=(gx, -p.enc_h / 2 - 1, base_d / 2), axis="y"))
    tools.append(cyl(12.5, p.enc_wall + 2, at=(p.vent_x, -p.enc_h / 2 - 1, base_d / 2), axis="y"))
    tools.append(box(p.enc_wall + 2, p.hs_cut_l, p.hs_cut_w,
                     at=(p.enc_w / 2 - p.enc_wall - 1, p.hs_y - p.hs_cut_l / 2, base_d / 2 - p.hs_cut_w / 2)))
    for dy in (-1, 1):
        for dz in (-1, 1):
            tools.append(cyl(4.5, p.enc_wall + 2, axis="x",
                             at=(p.enc_w / 2 - p.enc_wall - 1, p.hs_y + dy * (p.hs_cut_l / 2 + 12),
                                 base_d / 2 + dz * (p.hs_cut_w / 2 + 12))))
    return cut(s, *tools)


def enclosure_lid():
    p = P
    lid = rbox(p.enc_w, p.enc_h, p.enc_lid_d, p.enc_r).cut(
        rbox(p.enc_w - 2 * p.enc_wall, p.enc_h - 2 * p.enc_wall, p.enc_lid_d, p.enc_r - p.enc_wall, at=(0, 0, -p.enc_wall)))
    for (x, y) in corners(p.enc_w / 2 - p.lid_boss_in, p.enc_h / 2 - p.lid_boss_in):
        lid = lid.union(cyl(p.lid_boss_d, p.enc_lid_d, at=(x, y, 0)))
    land = ring(p.enc_w, p.enc_h, p.enc_r, p.enc_w - 2 * p.enc_wall - 6, p.enc_h - 2 * p.enc_wall - 6, p.enc_r - p.enc_wall,
                0, p.groove_d + 2)
    lid = lid.union(land)
    groove = ring(p.enc_w - p.enc_wall + p.groove_w, p.enc_h - p.enc_wall + p.groove_w, p.enc_r - p.enc_wall / 2,
                  p.enc_w - p.enc_wall - p.groove_w, p.enc_h - p.enc_wall - p.groove_w, p.enc_r - p.enc_wall / 2 - 1,
                  -0.01, p.groove_d)
    lid = lid.cut(groove)
    for (x, y) in corners(p.enc_w / 2 - p.lid_boss_in, p.enc_h / 2 - p.lid_boss_in):
        lid = lid.cut(cyl(4.5, p.enc_lid_d + 2, at=(x, y, -1)))
        lid = lid.cut(cyl(9, 10, at=(x, y, p.enc_lid_d - 8)))
    return lid


def lid_gasket():
    p = P
    return ring(p.enc_w - p.enc_wall + p.gasket_d / 2 + 0.4, p.enc_h - p.enc_wall + p.gasket_d / 2 + 0.4, p.enc_r - p.enc_wall / 2,
                p.enc_w - p.enc_wall - p.gasket_d / 2 - 0.4, p.enc_h - p.enc_wall - p.gasket_d / 2 - 0.4, p.enc_r - p.enc_wall / 2 - 1,
                p.groove_d - p.gasket_d * 0.8, p.gasket_d * 0.8)


def label_plate():
    p = P
    return rbox(120, 30, 0.8, 3, at=(0, p.enc_h / 2 - 50, p.enc_lid_d))


# ---------------------------------------------------------------------------------- internals (fabricated)
def mount_plate():
    p = P
    s = rbox(p.mp_w, p.mp_h, p.mp_t, 6)
    tools = []

    def h(x, y, d):
        tools.append(cyl(d, p.mp_t + 2, at=(x, y, -1)))
    for (x, y) in corners(p.bp_boss_dx / 2, p.bp_boss_dy / 2):
        h(x, y, 4.5)
    for x in (-100, 0, 100):
        h(x, p.din_y, 4.5)
    for x in (-75, 75):
        for y in (-25, 25):
            h(p.smps_x + x, p.smps_y + y, 4.5)
    for x in (-45, 45):
        for y in (-32, 32):
            h(p.pi_x + x, p.pi_y + y, 3.4)
    for x in (-1, 1):
        for y in (-1, 1):
            h(p.lc_x + x * (p.lc_l / 2 - p.lc_hole_in), p.lc_y + y * (p.lc_w / 2 - p.lc_hole_in), 3.4)
    for x in (-20, 20):
        h(p.buck_x, p.buck_y + x, 3.4)
    for x in range(-100, 101, 50):
        tools.append(box(4, 10, p.mp_t + 2, at=(x - 2, -170 - 5, -1)))
    for y in (-60, 40):
        tools.append(box(10, 4, p.mp_t + 2, at=(-120 - 5, y - 2, -1)))
    return cut(s, *tools)


def pi_tray():
    p = P
    s = rbox(100, 75, p.pitray_t, 4)
    hx = [-p.pi_l / 2 + 3.5 + x for x in (0, p.pi_hole_dx)]
    hy = [-p.pi_w / 2 + 3.5 + y for y in (0, p.pi_hole_dy)]
    for x in hx:
        for y in hy:
            s = s.union(cyl(6.5, p.pi_standoff, at=(x, y, 0)))
    for sg in (-1, 1):
        s = s.union(box(100, 2, 6, at=(-50, sg * 37.5 - (2 if sg > 0 else 0), 0)))
    for x in hx:
        for y in hy:
            s = s.cut(cyl(3.6, 20, at=(x, y, 1.5)))
    for x in (-45, 45):
        for y in (-32, 32):
            s = s.cut(cyl(3.4, 10, at=(x, y, -1)))
            s = s.cut(cyl(6.2, 10, at=(x, y, p.pitray_t - 1.4)))
    s = s.cut(rbox(40, 30, 10, 3, at=(0, 0, -1)))
    return s


def spreader_bar_len():
    # exactly the argument edge_internals.scad internals() passes to heat_spreader(): see scad line
    # "heat_spreader(enc_w/2 - enc_wall - (pi_x+6) - spr_l/2 + 5 - (enc_w - mp_w)/2 + 20)"
    p = P
    return p.enc_w / 2 - p.enc_wall - (p.pi_x + 6) - p.spr_l / 2 + 5 - (p.enc_w - p.mp_w) / 2 + 20


def heat_spreader():
    p = P
    s = box(p.spr_l, p.spr_w, p.spr_t, at=(-p.spr_l / 2, -p.spr_w / 2, 0))
    for x in (-1, 1):
        for y in (-1, 1):
            s = s.cut(cyl(2.9, p.spr_t + 2, at=(x * 29, y * 24.5, -1)))
    bar = box(spreader_bar_len(), p.spr_bar_w, p.spr_bar_t, at=(p.spr_l / 2 - 5, -p.spr_bar_w / 2, 0))
    return s.union(bar)


def thermal_pad():
    return box(22, 22, 1.5, at=(-11, -11, -1.5))


def sun_hood():
    p = P
    w = p.enc_w + 2 * (p.hood_gap + p.hood_t)
    top = box(w, p.hood_t, p.enc_d + p.hood_front + 10, at=(-w / 2, p.enc_h / 2 + p.hood_gap, -10))
    s = top
    for sg in (-1, 1):
        s = s.union(box(p.hood_t, 220, p.enc_d + 20,
                        at=(sg * (w / 2 - p.hood_t / 2) - p.hood_t / 2, p.enc_h / 2 + p.hood_gap - 220, -10)))
    return s


# ---------------------------------------------------------------------------------- bought-in envelopes
def heat_sink():
    p = P
    s = box(p.hs_base_t, p.hs_base_l, p.hs_base_w, at=(0, -p.hs_base_l / 2, -p.hs_base_w / 2))
    n = int(p.hs_fin_n)
    for i in range(n):
        z = -p.hs_base_w / 2 + 2 + i * (p.hs_base_w - 4 - p.hs_fin_t) / (n - 1)
        s = s.union(box(p.hs_fin_h, p.hs_base_l, p.hs_fin_t, at=(p.hs_base_t, -p.hs_base_l / 2, z)))
    return s


def sink_gasket():
    p = P
    o = box(1.5, p.hs_cut_l + 16, p.hs_cut_w + 16, at=(-1.5, -p.hs_cut_l / 2 - 8, -p.hs_cut_w / 2 - 8))
    return o.cut(box(4, p.hs_cut_l + 8, p.hs_cut_w + 8, at=(-2.5, -p.hs_cut_l / 2 - 4, -p.hs_cut_w / 2 - 4)))


def gland(m):
    thread = cyl(m, 4, at=(0, 0, -4))
    hexa = hexp(m + 4, 6)
    cone = cq.Workplane("XY").workplane(offset=6).circle((m + 2) / 2).workplane(offset=m * 0.7).circle((m - 2) / 2).loft()
    return union(thread, hexa, cone)


def vent_plug():
    return cyl(18, 10)


def rpi5():
    p = P
    s = rbox(p.pi_l, p.pi_w, p.pi_t, 3)
    for x in (0, p.pi_hole_dx):
        for y in (0, p.pi_hole_dy):
            s = s.cut(cyl(2.7, 4, at=(-p.pi_l / 2 + p.pi_hole_off + x, -p.pi_w / 2 + p.pi_hole_off + y, -1)))
    z = p.pi_t
    parts = [s,
             box(21, 16, 13.5, at=(p.pi_l / 2 - 21, -p.pi_w / 2 + 2, z)),
             box(17, 13, 15.5, at=(p.pi_l / 2 - 17, p.pi_w / 2 - 18, z)),
             box(17, 13, 15.5, at=(p.pi_l / 2 - 17, 2, z)),
             box(51, 5, 8.5, at=(-p.pi_l / 2 + 7, p.pi_w / 2 - 6.5, z)),
             box(30, 30, 9, at=(-12, -10, z))]
    return union(*parts)


def ai_hat():
    s = rbox(65, 56.5, 1.6, 3)
    return s.union(box(22, 22, 3, at=(-8, -10, 1.6)))


def lrs150():
    p = P
    s = box(p.smps_l, p.smps_w, p.smps_h, at=(-p.smps_l / 2, -p.smps_w / 2, 0))
    for i in range(11):
        s = s.cut(box(5, p.smps_w - 24, 2, at=(-p.smps_l / 2 + 30 + i * 9, -p.smps_w / 2 + 12, p.smps_h - 1)))
    s = s.union(box(16, p.smps_w - 12, 14, at=(-p.smps_l / 2 - 0.1, -p.smps_w / 2 + 6, 3)))
    s = s.union(box(24, 8, 0.4, at=(-p.smps_l / 2 + 1, -p.smps_w / 2 + 2, p.smps_h)))
    return s


def poe_switch():
    p = P
    s = box(p.sw_w, p.sw_l, p.sw_h, at=(-p.sw_w / 2, -p.sw_l / 2, 0))
    for i in range(5):
        s = s.union(box(16, 18, 1, at=(-p.sw_w / 2 + 6, -p.sw_l / 2 + 10 + i * 24, p.sw_h)))
        s = s.union(box(16.5, 16, 14.2, at=(-p.sw_w / 2 + 6, -p.sw_l / 2 + 10 + i * 24, p.sw_h - 14)))
    return s


def lane_controller_pcb():
    p = P
    s = box(p.lc_l, p.lc_w, 1.6, at=(-p.lc_l / 2, -p.lc_w / 2, 0))
    for x in (-1, 1):
        for y in (-1, 1):
            s = s.cut(cyl(3.2, 4, at=(x * (p.lc_l / 2 - p.lc_hole_in), y * (p.lc_w / 2 - p.lc_hole_in), -1)))
    s = s.union(box(18, 25.5, 3.2, at=(-10, 5, 1.6)))
    for i in range(6):
        s = s.union(box(12, 8, 10, at=(-p.lc_l / 2 + 8 + i * 15, -p.lc_w / 2 + 2, 1.6)))
    s = s.union(box(22, 22, 12, at=(20, 0, 1.6)))
    s = s.union(cyl(10, 12, at=(-40, 20, 1.6)))
    return s


def din_rail(length):
    pts = [(-17.5, 7.5), (-12.5, 7.5), (-12.5, 0), (12.5, 0), (12.5, 7.5), (17.5, 7.5),
           (17.5, 6.5), (13.5, 6.5), (13.5, -1), (-13.5, -1), (-13.5, 6.5), (-17.5, 6.5)]
    return cq.Workplane("YZ").polyline(pts).close().extrude(length)


def din_device(mods, h=DIN_H):
    w = mods * 17.5 - 0.5
    return box(w, 90, h - 10, at=(0, -45, 0)).union(box(w, 45, 10, at=(0, -22.5, h - 10)))


def buck_module():
    return box(30, 60, 18)


def trunking():
    p = P
    return box(p.mp_w - 20, 20, 25)


# ---------------------------------------------------------------------------------- build
def build():
    p = P
    base_d = p.enc_d - p.enc_lid_d
    inner_floor = p.enc_wall + p.bp_boss_h
    SRC = ["edge_params.scad"]

    eb = enclosure_base()
    REG.part("edge_enclosure_base", eb, domain=D, kind="fabricated", material=MAT_PC, color="print",
             desc="IP65 enclosure base 300x400x140 (bought PC blank + our machining: rim tongue, bosses, lugs, gland/vent holes, heat-sink window)",
             params=["enc_w", "enc_h", "enc_d", "enc_lid_d", "enc_wall", "enc_r", "lid_boss_d", "lid_boss_in", "tongue_w", "tongue_h",
                     "bp_boss_d", "bp_boss_h", "bp_boss_dx", "bp_boss_dy", "mlug_w", "mlug_x", "mlug_y", "gland_x", "gland_m",
                     "vent_x", "hs_cut_l", "hs_cut_w", "hs_y"],
             sources=["edge_params.scad", "edge_enclosure.scad:enclosure_base"],
             ref="include <edge_params.scad>\nuse <edge_enclosure.scad>\nenclosure_base();", mat_key="enc_base")
    el = enclosure_lid()
    REG.part("edge_enclosure_lid", el, domain=D, kind="fabricated", material=MAT_PC, color="print",
             desc="IP65 enclosure lid 300x400x40 with gasket groove, screw bosses and counterbored screw holes",
             params=["enc_w", "enc_h", "enc_lid_d", "enc_wall", "enc_r", "groove_w", "groove_d", "lid_boss_d", "lid_boss_in"],
             sources=["edge_params.scad", "edge_enclosure.scad:enclosure_lid"],
             ref="include <edge_params.scad>\nuse <edge_enclosure.scad>\nenclosure_lid();", mat_key="enc_lid",
             ref_includes=["edge_lid_gasket_envelope", "edge_label_plate"],
             notes="reference module enclosure_lid() also draws the gasket cord and the label plate (separate STEP parts)")
    gk = lid_gasket()
    REG.part("edge_lid_gasket_envelope", gk, domain=D, kind="bought_envelope", material="EPDM/silicone cord (bought)",
             color="rubber", desc="Lid gasket cord as a rectangular-section ring 2.4 x 3.6 (the .scad models the cord this way)",
             params=["gasket_d", "groove_d", "enc_w", "enc_h", "enc_wall", "enc_r"], sources=["edge_enclosure.scad:enclosure_lid"],
             ref=None, mat_key="gasket")
    lp = label_plate()
    REG.part("edge_label_plate", lp, domain=D, kind="fabricated", material="not specified in MATERIALS.md", color="struct",
             desc="ParkFlow label plate 120x30x0.8 on the lid (cosmetic)", params=["enc_h", "enc_lid_d"],
             sources=["edge_enclosure.scad:enclosure_lid"], ref=None)
    mp = mount_plate()
    REG.part("edge_mount_plate", mp, domain=D, kind="fabricated", material=MAT_5052, color="struct",
             desc="Internal mounting plate 260x360x3, laser cut (DXF edge_mount_plate)",
             params=["mp_w", "mp_t", "bp_boss_dx", "bp_boss_dy", "din_y", "smps_x", "smps_y", "pi_x", "pi_y", "lc_x", "lc_y",
                     "buck_x", "buck_y"],
             sources=["edge_params.scad", "edge_internals.scad:mount_plate_2d"],
             ref="include <edge_params.scad>\nuse <edge_internals.scad>\nmount_plate();", mat_key="mount_plate")
    pt = pi_tray()
    REG.part("edge_pi_tray", pt, domain=D, kind="fabricated", material=MAT_ASA, color="print",
             desc="Pi tray (FDM ASA) with 4 standoffs, edge rails, heat-set holes, airflow window",
             params=["pitray_t", "pi_standoff"], sources=["edge_params.scad", "edge_internals.scad:pi_tray"],
             ref="include <edge_params.scad>\nuse <edge_internals.scad>\npi_tray();", mat_key="pi_tray")
    hs = heat_spreader()
    bl = spreader_bar_len()
    REG.part("edge_heat_spreader", hs, domain=D, kind="fabricated", material=MAT_6061, color="struct",
             desc=f"Heat spreader 100x70x5 + {bl:g} mm bar 20x10 (bar length as assembled in internals())",
             params=["spr_t", "spr_l", "spr_w", "spr_bar_w", "spr_bar_t"],
             sources=["edge_params.scad", "edge_internals.scad:heat_spreader,heat_spreader_2d"],
             ref=(f"include <edge_params.scad>\nuse <edge_internals.scad>\nlinear_extrude(spr_t) heat_spreader_2d();\n"
                  f"translate([spr_l/2-5, -spr_bar_w/2, 0]) cube([{bl:g}, spr_bar_w, spr_bar_t]);"),
             mat_key="spreader", notes="reference wrapper re-states the bar cube of heat_spreader(); module also draws a pad")
    tpad = thermal_pad()
    REG.part("edge_thermal_pad_envelope", tpad, domain=D, kind="bought_envelope", material="thermal pad (bought)",
             color="sensor", desc="Thermal pad 22x22x1.5", params=[], sources=["edge_internals.scad:heat_spreader"], ref=None)
    sh = sun_hood()
    REG.part("edge_sun_hood", sh, domain=D, kind="fabricated", material=MAT_5052, color="struct",
             desc="Sun hood 2 mm 5052: canopy + 2 side plates exactly as in sun_hood() (separate flat plates fused; the bends/flanges of a brake-formed hood are not modelled)",
             params=["enc_w", "enc_h", "enc_d", "hood_gap", "hood_t", "hood_front"],
             sources=["edge_params.scad", "edge_internals.scad:sun_hood"],
             ref="include <edge_params.scad>\nuse <edge_internals.scad>\nsun_hood();", mat_key="hood")

    # --- bought-in envelopes
    hsk = heat_sink()
    REG.part("edge_heat_sink_envelope", hsk, domain=D, kind="bought_envelope", material=MAT_6063, color="struct",
             desc="External finned heat sink 200x150, base 6 + 18 fins 2x35 (bought extrusion, cut + drilled)",
             params=["hs_base_l", "hs_base_w", "hs_base_t", "hs_fin_n", "hs_fin_t", "hs_fin_h"], sources=["edge_internals.scad:heat_sink"],
             ref=None, mat_key="heat_sink")
    sg = sink_gasket()
    REG.part("edge_sink_gasket_envelope", sg, domain=D, kind="bought_envelope", material="EPDM sheet (bought)", color="rubber",
             desc="Heat-sink window gasket (frame 4 mm wide, 1.5 thick)", params=["hs_cut_l", "hs_cut_w"],
             sources=["edge_internals.scad:heat_sink"], ref=None)
    glands = {}
    for m in sorted(set(int(x) for x in p.gland_m)):
        g = gland(m)
        glands[m] = g
        REG.part(f"edge_gland_M{m}_envelope", g, domain=D, kind="bought_envelope", material="Nylon PA66 (bought)", color="rubber",
                 desc=f"Cable gland M{m} envelope (thread, hex, cone), axis +z from wall face", params=["gland_m"],
                 sources=["pf_common.scad:gland"], ref=f"include <pf_common.scad>\ngland({m});")
    vp = vent_plug()
    REG.part("edge_vent_plug_envelope", vp, domain=D, kind="bought_envelope", material="ePTFE vent (bought)", color="rubber",
             desc="Pressure-equalisation vent as a D18 x 10 cylinder", params=["vent_x"],
             sources=["edge_node_assembly.scad:edge_node"], ref=None)
    pi = rpi5()
    REG.part("rpi5_envelope", pi, domain=D, kind="bought_envelope", material="bought", color="elec",
             desc="Raspberry Pi 5 envelope 85x56 + connectors + active cooler", params=["pi_l", "pi_w", "pi_t", "pi_hole_dx", "pi_hole_dy"],
             sources=["pf_bought.scad:rpi5"], ref="use <pf_bought.scad>\nrpi5();")
    ah = ai_hat()
    REG.part("ai_hat_envelope", ah, domain=D, kind="bought_envelope", material="bought", color="elec",
             desc="AI HAT+ (Hailo-8) envelope 65x56.5x1.6 + 22x22x3 module", params=[],
             sources=["pf_bought.scad:ai_hat"], ref="use <pf_bought.scad>\nai_hat();")
    sm = lrs150()
    REG.part("smps_lrs150_envelope", sm, domain=D, kind="bought_envelope", material="bought", color="steel",
             desc="Mean Well LRS-150-24 envelope 159x97x30 (vent slots, terminal block)", params=["smps_l", "smps_w", "smps_h"],
             sources=["pf_bought.scad:lrs150"], ref="use <pf_bought.scad>\nlrs150();")
    sw = poe_switch()
    REG.part("poe_switch_envelope", sw, domain=D, kind="bought_envelope", material="bought", color="steel",
             desc="DIN-rail PoE switch envelope 40x140x105 (ASSUMED class size)", params=["sw_l", "sw_w", "sw_h"],
             sources=["pf_bought.scad:poe_switch"], ref="use <pf_bought.scad>\npoe_switch();")
    lc = lane_controller_pcb()
    REG.part("lane_controller_pcb_envelope", lc, domain=D, kind="bought_envelope", material="custom PCB (bought)", color="elec",
             desc="Lane Controller PCB 100x80x1.6 with component blocks", params=["lc_l", "lc_w", "lc_hole_in"],
             sources=["pf_bought.scad:lane_controller_pcb"], ref="use <pf_bought.scad>\nlane_controller_pcb();")
    dr = din_rail(p.din_len)
    REG.part("edge_din_rail_envelope", dr, domain=D, kind="bought_envelope", material="steel/Al DIN rail (bought)", color="steel",
             desc="35 mm top-hat DIN rail, length din_len", params=["din_len"], sources=["pf_bought.scad:din_rail"],
             ref="include <edge_params.scad>\nuse <pf_bought.scad>\ndin_rail(din_len);")
    dev = {}
    for mods in sorted(set(m for _, m in DIN_DEVICES)):
        dev[mods] = din_device(mods)
        REG.part(f"edge_din_device_{mods}mod_envelope", dev[mods], domain=D, kind="bought_envelope", material="bought",
                 color="struct", desc=f"DIN-rail modular device, {mods} module(s) wide (MCB / SPD / terminal)", params=[],
                 sources=["pf_bought.scad:din_device"], ref=f"use <pf_bought.scad>\ndin_device({mods}, [1,1,1], 70);")
    bk = buck_module()
    REG.part("edge_buck_module_envelope", bk, domain=D, kind="bought_envelope", material="bought", color="elec",
             desc="24 V to 5 V buck module envelope 30x60x18", params=[], sources=["edge_internals.scad:internals"], ref=None)
    tk = trunking()
    REG.part("edge_wire_trunking_envelope", tk, domain=D, kind="bought_envelope", material="PVC trunking (bought)", color="steel",
             desc="Wiring trunking block 240x20x25 (solid envelope)", params=["mp_w"], sources=["edge_internals.scad:internals"], ref=None)

    # ============================================================== internals assembly (plate-local frame)
    z0 = p.mp_t
    I = Asm("edge_internals")
    I.add(Leaf("edge_mount_plate", mp, "mount_plate_3mm_5052"))
    I.add(Leaf("edge_din_rail_envelope", dr, "din_rail", "steel").moved(T((-p.din_len / 2, p.din_y, z0))))
    for k, (x, mods) in enumerate(DIN_DEVICES):
        I.add(Leaf(f"edge_din_device_{mods}mod_envelope", dev[mods], f"din_device_{k}", "struct").moved(T((x, p.din_y, z0 + 7.5))))
    I.add(Leaf("poe_switch_envelope", sw, "poe_switch", "steel").moved(T((105, p.din_y, z0 + 7.5))))
    I.add(Leaf("smps_lrs150_envelope", sm, "smps_lrs150", "steel").moved(T((p.smps_x, p.smps_y, z0))))
    I.add(Leaf("edge_buck_module_envelope", bk, "buck_module", "elec").moved(T((p.buck_x - 15, p.buck_y - 30, z0))))
    I.add(Leaf("edge_pi_tray", pt, "pi_tray", "print").moved(T((p.pi_x, p.pi_y, z0))))
    I.add(Leaf("rpi5_envelope", pi, "rpi5", "elec").moved(T((p.pi_x, p.pi_y, z0 + p.pi_standoff))))
    I.add(Leaf("ai_hat_envelope", ah, "ai_hat", "elec").moved(
        T((p.pi_x - p.pi_l / 2 + 32.5, p.pi_y, z0 + p.pi_standoff + p.pi_t + 16))))
    zs = z0 + p.pi_standoff + 1.6 + 16 + 1.6 + 4.5
    I.add(Leaf("edge_heat_spreader", hs, "heat_spreader_6061", "struct").moved(T((p.pi_x + 6, p.pi_y, zs))))
    I.add(Leaf("edge_thermal_pad_envelope", tpad, "thermal_pad", "sensor").moved(T((p.pi_x + 6, p.pi_y, zs))))
    I.add(Leaf("lane_controller_pcb_envelope", lc, "lane_controller_pcb", "elec").moved(T((p.lc_x, p.lc_y, z0 + p.lc_standoff))))
    I.add(Leaf("edge_wire_trunking_envelope", tk, "wire_trunking", "steel").moved(T((-p.mp_w / 2 + 10, -170 + 8, z0))))
    REG.assembly("edge_internals_assy", I, domain=D,
                 desc="Populated internal mounting plate (plate-local frame, z = component side). Fasteners, standoffs excluded.",
                 params=["mp_w", "mp_t", "din_y", "smps_x", "pi_x", "pi_y", "lc_x", "lc_y", "pi_standoff", "lc_standoff"],
                 sources=["edge_internals.scad:internals"],
                 ref="include <edge_params.scad>\nuse <edge_internals.scad>\ninternals(0);",
                 ref_note="reference STL also contains the Pi hex spacers and the 4 Lane Controller brass standoffs (hardware, not in STEP)")

    # ============================================================== full edge node (edge frame)
    E = Asm("edge_node_assembly")
    E.add(Leaf("edge_enclosure_base", eb, "enclosure_base", "print"))
    E.add(I.moved(T((0, 0, inner_floor))))
    E.add(Leaf("edge_enclosure_lid", el, "enclosure_lid", "print").moved(T((0, 0, base_d))))
    E.add(Leaf("edge_lid_gasket_envelope", gk, "lid_gasket", "rubber").moved(T((0, 0, base_d))))
    E.add(Leaf("edge_label_plate", lp, "label_plate", "struct").moved(T((0, 0, base_d))))
    E.add(Leaf("edge_heat_sink_envelope", hsk, "heat_sink", "struct").moved(T((p.enc_w / 2, p.hs_y, base_d / 2))))
    E.add(Leaf("edge_sink_gasket_envelope", sg, "heat_sink_window_gasket", "rubber").moved(T((p.enc_w / 2, p.hs_y, base_d / 2))))
    for i, (gx, gm) in enumerate(zip(p.gland_x, p.gland_m)):
        E.add(Leaf(f"edge_gland_M{int(gm)}_envelope", glands[int(gm)], f"gland_{i}_M{int(gm)}", "rubber").moved(
            T((gx, -p.enc_h / 2, base_d / 2), (90, 0, 0))))
    E.add(Leaf("edge_vent_plug_envelope", vp, "vent_plug", "rubber").moved(T((p.vent_x, -p.enc_h / 2, base_d / 2), (90, 0, 0))))
    E.add(Leaf("edge_sun_hood", sh, "sun_hood", "struct"))
    REG.assembly("edge_node_assy", E, domain=D,
                 desc="Edge Node: enclosure base + lid + gasket, populated plate, heat sink, glands, vent, sun hood (edge frame, explode = 0)",
                 params=["enc_w", "enc_h", "enc_d", "enc_lid_d", "bp_boss_h", "hs_y"],
                 sources=["edge_node_assembly.scad:edge_node"],
                 ref="use <edge_node_assembly.scad>\nedge_node(0, 1, 1);",
                 ref_note="reference STL also contains Pi/LC hex standoffs")
    return E
