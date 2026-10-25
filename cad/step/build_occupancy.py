#!/usr/bin/env python3
"""
build_occupancy.py - (d) CEILING OCCUPANCY SENSOR NODE: printed base / cover / diffuser, bought-in envelopes, assembly.
Frame: z = 0 on the base back plate (ceiling side), housing grows +z (occupancy_parts.scad / oc_assy frame).
"""
import math
import cadquery as cq
from scadparams import load
from pf_cq import *            # noqa: F401,F403
from pf_reg import REG, Asm, Leaf, T, compose

P = load("occupancy_parts.scad", "occupancy_node_assembly.scad", "pf_bought.scad")
D = "occupancy"
ASA, PETG = "ASA (FDM)", "PETG (natural)"


def oc_base():
    p = P
    ri = p.oc_d / 2 - p.oc_wall
    s = cyl(p.oc_d, p.oc_base_h)
    s = s.cut(cyl(2 * ri, p.oc_base_h, at=(0, 0, p.oc_floor)))
    for sg in (-1, 1):
        x = sg * p.oc_screw_pitch / 2
        s = s.cut(cyl(p.oc_screw_d, 10, at=(x, 0, -1)))
        s = s.cut(cyl(10, 2, at=(x, 0, -1 + p.oc_floor - 1.2)))
    s = s.cut(cyl(p.oc_cable_d, 10, at=(0, 18, -1)))
    for i in range(int(p.snap_n)):
        w = box(p.oc_wall + 2, p.snap_w + 1, 2.2, at=(p.oc_d / 2 - p.oc_wall - 1, -p.snap_w / 2 - 0.5, p.oc_base_h - p.lip_h - 3.5))
        s = s.cut(rotate(w, (0, 0, 90 + i * 360 / p.snap_n)))
    for x in (-20, 20):
        st = cyl(6, p.esp_standoff, at=(x, -12, p.oc_floor)).cut(cyl(2.5, 20, at=(x, -12, p.oc_floor)))
        s = s.union(st)
    s = s.union(box(2.1, 4, p.oc_base_h - p.oc_floor - 2, at=(p.oc_d / 2 - p.oc_wall - 2, -2, p.oc_floor)))
    return s


def oc_cover():
    p = P
    ri = p.oc_d / 2 - p.oc_wall
    sp_o = ri - p.fit_clear
    skirt = cyl(p.oc_d, p.oc_cover_h - 8)
    dome = (cq.Workplane("XY").workplane(offset=p.oc_cover_h - 8).circle(p.oc_d / 2).workplane(offset=8).circle((p.oc_d - 16) / 2).loft())
    spig = cyl(2 * sp_o, p.lip_h + 0.01, at=(0, 0, -p.lip_h))
    s = union(skirt, dome, spig)
    s = s.cut(cyl(2 * (sp_o - p.oc_wall), p.oc_cover_h - 2 + p.lip_h, at=(0, 0, -p.lip_h - 1)))
    s = s.cut(cyl(p.probe_d + 0.6, 60))
    win = cyl(p.ring_od + 4, 10, at=(0, 0, p.oc_cover_h - 3)).cut(cyl(p.ring_id - 2, 12, at=(0, 0, p.oc_cover_h - 3 - 1)))
    s = s.cut(win)
    for i in range(int(p.snap_n)):
        for sg in (-1, 1):
            sl = box(p.oc_wall + 2, 1.2, p.snap_l, at=(sp_o - p.oc_wall - 1, sg * (p.snap_w / 2 + 0.6) - 0.6,
                                                         -p.lip_h - 1 - p.snap_l + p.lip_h + 1))
            s = s.cut(rotate(sl, (0, 0, 90 + i * 360 / p.snap_n)))
    for i in range(int(p.snap_n)):
        cant = box(p.snap_t, p.snap_w, p.snap_l, at=(sp_o - p.snap_t, -p.snap_w / 2, -p.lip_h - p.snap_l + p.lip_h))
        wedge = (cq.Workplane("XZ").polyline([(0, 0), (0.01, 0), (p.snap_lip + 0.01, 2.2), (0, 2.2)]).close()
                 .extrude(-p.snap_w)).translate(V(sp_o, -p.snap_w / 2, -p.lip_h + 0.5 - 2))
        s = s.union(rotate(cant.union(wedge), (0, 0, 90 + i * 360 / p.snap_n)))
    return s


def probe_clamp_boss():
    p = P
    boss = cyl(p.probe_d + 8, 12, at=(0, 0, p.oc_cover_h - 18))
    boss = boss.cut(cyl(p.probe_d + 0.4, 20, at=(0, 0, p.oc_cover_h - 18 - 1)))
    return boss.cut(box(2, p.probe_d, 20, at=(-1, 0, p.oc_cover_h - 18 - 1)))


def led_seat():
    p = P
    return cyl(p.ring_od + 4, 1.5, at=(0, 0, p.oc_cover_h - 5.5)).cut(cyl(p.ring_od - 2, 4, at=(0, 0, p.oc_cover_h - 5.5 - 1)))


def oc_diffuser():
    p = P
    return cyl(p.ring_od + 3.6, p.diffuser_t + 1.8).cut(cyl(p.ring_id - 1.6, 10, at=(0, 0, -1)))


def esp32c3_board():
    return union(box(48, 26, 1.6, at=(-24, -13, 0)), box(16, 16, 2.6, at=(-6, -8, 1.6)), box(7.5, 9, 3.2, at=(-25, -4.5, 1.6)))


def a02yyuw():
    p = P
    probe = cyl(p.a02_probe_d, p.a02_probe_l, at=(0, 0, -p.a02_probe_l))
    body = box(p.a02_body_l, p.a02_body_w, p.a02_body_h, at=(-p.a02_body_l / 2, -p.a02_body_w / 2, 0))
    win = cyl(p.a02_probe_d - 6, 0.6, at=(0, 0, -p.a02_probe_l - 0.5))
    cable = cyl(5, 25, axis="x", at=(p.a02_body_l / 2, 0, p.a02_body_h / 2))
    return union(probe, body, win, cable)


def ws2812_ring(od=50, id_=36, n=12):
    s = cyl(od, 1.6).cut(cyl(id_, 4, at=(0, 0, -1)))
    for i in range(n):
        a = math.radians(i * 360 / n)
        r = (od + id_) / 4
        s = s.union(box(5, 5, 1.6, at=(r * math.cos(a) - 2.5, r * math.sin(a) - 2.5, 1.6 - 0.8)).rotate(
            (r * math.cos(a), r * math.sin(a), 0), (r * math.cos(a), r * math.sin(a), 1), i * 360 / n))
    return s


def grommet():
    return cyl(12, 6)


def build():
    p = P
    base = oc_base()
    REG.part("occ_base", base, domain=D, kind="fabricated", material=ASA, color="print",
             desc="Ceiling base cup D96x22 (FDM ASA): keyhole slots, cable entry, snap windows, ESP32 standoffs, key",
             params=["oc_d", "oc_wall", "oc_base_h", "oc_floor", "oc_screw_pitch", "oc_screw_d", "oc_cable_d", "snap_n", "snap_w", "lip_h", "esp_standoff"],
             sources=["occupancy_params.scad", "occupancy_parts.scad:oc_base"],
             ref="include <occupancy_params.scad>\nuse <occupancy_parts.scad>\noc_base();", mat_key="occ_base",
             notes="the 'keyhole' counterbore in the .scad (z = 0.8..2.8) is an enclosed void 0.2 mm below the cup floor; reproduced as modelled")
    cover = oc_cover()
    boss = probe_clamp_boss()
    seat = led_seat()
    REG.part("occ_cover", cover, domain=D, kind="fabricated", material=ASA, color="print",
             ref_includes=["occ_probe_clamp_boss", "occ_led_seat"],
             notes="MODEL ISSUE: in the .scad the probe clamp boss and the LED seat are NOT connected to this shell (3 separate solids); exported as 3 parts",
             desc="Sensor cover shell D96x26 (FDM ASA): dome, spigot, 3 snap hooks, probe bore, LED window",
             params=["oc_d", "oc_wall", "oc_cover_h", "fit_clear", "lip_h", "snap_n", "snap_w", "snap_l", "snap_t", "snap_lip", "probe_d", "ring_od", "ring_id"],
             sources=["occupancy_params.scad", "occupancy_parts.scad:oc_cover"],
             ref="include <occupancy_params.scad>\nuse <occupancy_parts.scad>\noc_cover();", mat_key="occ_cover")
    REG.part("occ_probe_clamp_boss", boss, domain=D, kind="fabricated", material=ASA, color="print",
             desc="Probe clamp boss D42/D34.4 x 12 with 2 mm slit (floating in the .scad cover - see occ_cover notes)",
             params=["probe_d", "oc_cover_h"], sources=["occupancy_parts.scad:oc_cover"], ref=None, mat_key="occ_cover")
    REG.part("occ_led_seat", seat, domain=D, kind="fabricated", material=ASA, color="print",
             desc="LED ring seat D54/D48 x 1.5 (floating in the .scad cover - see occ_cover notes)",
             params=["ring_od", "oc_cover_h"], sources=["occupancy_parts.scad:oc_cover"], ref=None, mat_key="occ_cover")
    diff = oc_diffuser()
    REG.part("occ_diffuser", diff, domain=D, kind="fabricated", material=PETG, color="print",
             desc="Diffuser ring D53.6 x 3 (natural PETG)", params=["ring_od", "ring_id", "diffuser_t"],
             sources=["occupancy_parts.scad:oc_diffuser"],
             ref="include <occupancy_params.scad>\nuse <occupancy_parts.scad>\noc_diffuser();", mat_key="occ_diffuser")
    esp = esp32c3_board()
    REG.part("esp32c3_board_envelope", esp, domain=D, kind="bought_envelope", material="bought", color="elec",
             desc="ESP32-C3 board envelope 48x26 (ASSUMED DevKitM-1 class)", params=[], sources=["pf_bought.scad:esp32c3_board"],
             ref="use <pf_bought.scad>\nesp32c3_board();")
    a02 = a02yyuw()
    REG.part("a02yyuw_ultrasonic_envelope", a02, domain=D, kind="bought_envelope", material="bought", color="sensor",
             desc="DFRobot A02YYUW envelope (ASSUMED: probe D34x26 + 36x42x18 body; MEASURE the real part)",
             params=["a02_probe_d", "a02_probe_l", "a02_body_w", "a02_body_l", "a02_body_h"], sources=["pf_bought.scad:a02yyuw"],
             ref="use <pf_bought.scad>\na02yyuw();")
    ring = ws2812_ring(p.ring_od, p.ring_id)
    REG.part("ws2812_ring_envelope", ring, domain=D, kind="bought_envelope", material="bought", color="elec",
             desc="WS2812B 12-LED ring envelope D50/D36", params=["ring_od", "ring_id"], sources=["pf_bought.scad:ws2812_ring"],
             ref="include <occupancy_params.scad>\nuse <pf_bought.scad>\nws2812_ring(ring_od, ring_id);")
    grom = grommet()
    REG.part("occ_cable_grommet_envelope", grom, domain=D, kind="bought_envelope", material="rubber (bought)", color="rubber",
             desc="Cable grommet D12x6", params=[], sources=["occupancy_node_assembly.scad:oc_assy"], ref=None)

    A = Asm("occupancy_node_assembly")
    A.add(Leaf("occ_base", base, "base", "print"))
    A.add(Leaf("esp32c3_board_envelope", esp, "esp32c3", "elec").moved(T((0, -12, p.oc_floor + p.esp_standoff))))
    A.add(Leaf("occ_cable_grommet_envelope", grom, "cable_grommet", "rubber").moved(T((0, 18, -4))))
    zc = p.oc_base_h
    A.add(Leaf("occ_cover", cover, "cover_shell", "print").moved(T((0, 0, zc))))
    A.add(Leaf("occ_probe_clamp_boss", boss, "probe_clamp_boss", "print").moved(T((0, 0, zc))))
    A.add(Leaf("occ_led_seat", seat, "led_seat", "print").moved(T((0, 0, zc))))
    A.add(Leaf("a02yyuw_ultrasonic_envelope", a02, "a02yyuw", "sensor").moved(
        compose(T((0, 0, zc + p.oc_cover_h - p.a02_probe_l + 2)), T(r=(0, 0, 0)), lambda s: mirror_xy(s))))
    A.add(Leaf("ws2812_ring_envelope", ring, "ws2812_ring", "elec").moved(T((0, 0, zc + p.oc_cover_h - 4))))
    A.add(Leaf("occ_diffuser", diff, "diffuser", "print").moved(T((0, 0, zc + p.oc_cover_h - 3))))
    REG.assembly("occupancy_node_assy", A, domain=D,
                 desc="Occupancy node, base-on-z=0 frame (as oc_assy()): base, cover, diffuser, ESP32-C3, A02YYUW, LED ring, grommet (M5 screws excluded)",
                 params=["oc_d", "oc_base_h", "oc_cover_h", "oc_floor", "esp_standoff"], sources=["occupancy_node_assembly.scad:oc_assy"],
                 ref="use <occupancy_node_assembly.scad>\noc_assy(0);",
                 ref_note="reference STL also contains the 2 M5 countersunk screws")
    return A
