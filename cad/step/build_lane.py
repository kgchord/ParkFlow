#!/usr/bin/env python3
"""
build_lane.py - (e) FULL DEMO LANE LAYOUT 3.5 m x 8 m: the sub-assemblies placed as in lane_layout.scad layout().
Context geometry (asphalt, kerbs, road paint, car, RFID/camera zones) is NOT exported: it is not a ParkFlow product.
The demo ceiling rig (40x40 post 2400 + cross-arm 700, node at x+600, z 2380) uses literals that sit inside
layout() in lane_layout.scad (not named parameters) - copied here with the same values.
"""
import cadquery as cq
from scadparams import load
from pf_cq import *            # noqa: F401,F403
from pf_reg import REG, Asm, Leaf, T, compose

L = load("lane_layout.scad", "barrier_assembly.scad")
RIG_POST_L, RIG_BAR_L, RIG_Y, RIG_NODE_X, RIG_NODE_Z = 2400.0, 700.0, 6800.0, 600.0, 2380.0   # literals of layout()
PB_SPAN = 3600.0                                                                           # barrier_core() default


def build(gantry_asm, gparts, bar, occ_asm):
    p = L
    # demo rig extrusions (40x40, same generic profile as the antenna arm)
    post = tslot(40, 40, RIG_POST_L, 40, 10)
    bar_ = tslot(40, 40, RIG_BAR_L, 40, 10)
    REG.part("lane_rig_post_40x40", post, domain="lane", kind="fabricated", material="Al 6063-T5", color="struct",
             desc="Demo ceiling-rig post 40x40 x 2400 (generic profile)", params=[], sources=["lane_layout.scad:layout"],
             ref="include <pf_common.scad>\ntslot(40, 40, 2400, 40, 10);", mat_key="rig")
    REG.part("lane_rig_crossbar_40x40", bar_, domain="lane", kind="fabricated", material="Al 6063-T5", color="struct",
             desc="Demo ceiling-rig cross-bar 40x40 x 700 (generic profile)", params=[], sources=["lane_layout.scad:layout"],
             ref="include <pf_common.scad>\ntslot(40, 40, 700, 40, 10);", mat_key="rig")
    X = Asm("lane_layout_assembly")
    # gantry on the +x island: translate(...) mirror([1,0,0]) gantry(0,1,0)
    fg = compose(T((p.lane_w + p.island_w / 2, p.pole_y, p.island_h + p.grout_gap)), lambda s: mirror_yz(s))
    X.add(gantry_asm.moved(fg))
    # barrier: translate(...) rotate([0,0,180]) barrier_core(boom_ang)   (photo-beam spans pb_span)
    hub_y = bar["hub_y"]
    by = hub_y + p.pb_dy
    B = Asm("boom_barrier_lane")
    B.add(bar["H"]); B.add(bar["DT"])
    rot = compose(T((0, hub_y, p.shaft_z)), T(r=(90, 0, 0)))
    B.add(bar["R"].moved(compose(rot, T(r=(0, 0, p.boom_ang)))))
    B.add(bar["LS"].moved(rot))
    B.add(bar["pa1"].moved(T((p.hs_x / 2 + 60, by, 0))))
    B.add(bar["pa2"].moved(T((PB_SPAN, by, 0))))
    X.add(B.moved(compose(T((p.lane_w + p.island_w / 2, p.bar_y, p.island_h)), T(r=(0, 0, 180)))))
    # occupancy demo rig
    rig = Asm("occupancy_demo_rig")
    rig.add(Leaf("lane_rig_post_40x40", post, "rig_post"))
    rig.add(Leaf("lane_rig_crossbar_40x40", bar_, "rig_crossbar").moved(compose(T((0, 0, RIG_POST_L)), T(r=(0, 90, 0)), T((0, 0, -20)))))
    rig.add(occ_asm.moved(compose(T((RIG_NODE_X, 0, RIG_NODE_Z)), T(r=(180, 0, 0)))))
    X.add(rig.moved(T((-p.island_w / 2, RIG_Y, p.island_h))))
    ref = (f"include <gantry_params.scad>\ninclude <pf_common.scad>\nuse <gantry_assembly.scad>\nuse <barrier_assembly.scad>\n"
           f"use <occupancy_node_assembly.scad>\n"
           f"translate([{p.lane_w + p.island_w / 2:g}, {p.pole_y:g}, {p.island_h + p.grout_gap:g}]) mirror([1,0,0]) gantry(0,1,0);\n"
           f"translate([{p.lane_w + p.island_w / 2:g}, {p.bar_y:g}, {p.island_h:g}]) rotate([0,0,180]) barrier_core({p.boom_ang:g});\n"
           f"translate([{-p.island_w / 2:g}, {RIG_Y:g}, {p.island_h:g}]) {{ tslot(40,40,2400,40,10);\n"
           f"  translate([0,0,2400]) rotate([0,90,0]) translate([0,0,-20]) tslot(40,40,700,40,10);\n"
           f"  translate([600,0,2380]) rotate([180,0,0]) oc_assy(0); }}\n")
    REG.assembly("lane_layout_assy", X, domain="lane",
                 desc="Lane layout 3.5 x 8 m: gantry (mirrored in x as in the .scad), boom barrier (photo-beam span 3600), occupancy demo rig. "
                      "Context (asphalt, kerbs, paint, car, zones) excluded.",
                 params=["lane_w", "island_w", "island_h", "pole_y", "bar_y", "boom_ang", "grout_gap"], sources=["lane_layout.scad:layout"],
                 ref=ref, ref_fn=40,
                 ref_note="reference STL = the same three layout() placements run through OpenSCAD (hardware included in reference only). "
                          "The gantry is MIRRORED (x -> -x) exactly as in the .scad, so handed parts are mirror-image copies.")
    return X
