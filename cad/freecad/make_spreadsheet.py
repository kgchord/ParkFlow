# -*- coding: utf-8 -*-
"""
ParkFlow - FreeCAD macro: create the parameter Spreadsheets for the native rebuild.

  Macro > Execute macro   (FreeCAD 1.0 / 1.x, any workbench)

Creates (in the active document, or a new document "ParkFlow") five Spreadsheet objects
    GantryParams  EdgeParams  BarrierParams  OccParams  LaneParams
Column A = alias text, B = value (alias set on this cell, so sketches/pads use  GantryParams.bp_t ),
C = unit, D = comment copied from the .scad source line.  The alias names are IDENTICAL to the OpenSCAD
variable names.  Derived values (sock_in, sock_long, web_top_above_pivot, bend_allow, hub_y ...) are written as
spreadsheet FORMULAS of the other aliases so they stay parametric.  List variables (gland_x[], gland_m[]) become
gland_x_1 ... gland_x_5.

STATUS: this macro has not yet been executed in FreeCAD.  It uses only the long-standing Spreadsheet API (addObject("Spreadsheet::Sheet"),
Sheet.set / setAlias / setColumnWidth, Document.recompute).  First run it on an empty document, check that the
sheets look right, and report/fix any error.  If a sheet already exists it is left untouched (set OVERWRITE=True
below to rebuild it).  The tables are generated from the .scad files by cad/freecad/gen_param_tables.py; re-run
that script (normal Python) after you change a *_params.scad value, then re-run this macro.
"""
import FreeCAD as App

OVERWRITE = False
ONLY = None            # e.g. ["GantryParams"] to create just one sheet

# BEGIN GENERATED PARAMETER TABLES (python3 cad/freecad/gen_param_tables.py) -------------------------
# sheet -> rows of (alias, value, unit, comment, formula-or-None).  Values are the numbers in the .scad files.
TABLES = {
    "GantryParams": [
        ('pole_w', 80.0, 'mm', 'pole profile width  (x)', None),
        ('pole_d', 80.0, 'mm', 'pole profile depth  (y)', None),
        ('pole_pitch', 40.0, 'mm', 'slot pitch of 40-series profile', None),
        ('pole_slot', 10.0, 'mm', 'slot opening width (10 mm, 40-series)', None),
        ('pole_len', 2400.0, 'mm', 'pole length above base plate', None),
        ('bp_w', 250.0, 'mm', 'base plate side (square)', None),
        ('bp_t', 16.0, 'mm', 'base plate thickness (calcs: 16 -> FoS 2.89; 12 -> 1.62)', None),
        ('bp_corner_r', 12.0, 'mm', 'plate corner radius', None),
        ('bp_pcd', 190.0, 'mm', 'anchor bolt pitch-circle diameter (4 bolts on 45 deg diagonals)', None),
        ('bp_anchor_d', 12.0, 'mm', 'anchor size M12 (chemical anchor, class 8.8 stud)', None),
        ('bp_anchor_hole', 14.0, 'mm', 'clearance hole for M12 (+2 mm for site tolerance)', None),
        ('bp_centre_hole', 30.0, 'mm', 'centre drain / grout-vent hole', None),
        ('grout_gap', 25.0, 'mm', 'levelling-nut / non-shrink grout gap under plate', None),
        ('sock_h', 150.0, 'mm', 'socket cheek height above plate', None),
        ('sock_t', 6.0, 'mm', 'socket cheek plate thickness', None),
        ('sock_clear', 0.5, 'mm', 'per-side clearance pole <-> socket', None),
        ('sock_bolt_d', 10.0, 'mm', 'M10 cross bolts through socket + pole', None),
        ('sock_bolt_z1', 45.0, 'mm', 'lower cross bolt height above plate top', None),
        ('sock_bolt_z2', 115.0, 'mm', 'upper cross bolt height (rotated 90 deg)', None),
        ('gus_n', 4.0, '', 'number of gussets (on face centre-lines)', None),
        ('gus_l', 74.0, 'mm', 'gusset base length (socket face -> 4 mm short of plate edge)', None),
        ('gus_h', 120.0, 'mm', 'gusset height', None),
        ('gus_t', 6.0, 'mm', 'gusset thickness', None),
        ('gus_chamfer', 12.0, 'mm', 'corner snipe for weld clearance', None),
        ('gus_tip', 15.0, 'mm', 'flat at top of gusset (no sharp tip)', None),
        ('ant_z', 1500.0, 'mm', 'arm centreline height above plate underside', None),
        ('ant_arm_len', 350.0, 'mm', '40x40 arm length from pole face', None),
        ('ant_arm_w', 40.0, 'mm', 'arm profile (40x40, 10 mm slot)', None),
        ('yoke_t', 5.0, 'mm', 'yoke + tilt plate sheet thickness (5052-H32)', None),
        ('yoke_w', 280.0, 'mm', 'yoke top-web length (across x) = reader width + 2 cheeks + clear', None),
        ('yoke_web_d', 60.0, 'mm', 'yoke web depth (y)', None),
        ('yoke_cheek_h', 200.0, 'mm', 'yoke cheek drop below arm underside', None),
        ('yoke_cheek_d', 80.0, 'mm', 'cheek width (y)', None),
        ('yoke_bend_r', 5.0, 'mm', 'inside bend radius (= t for 5052-H32, 90 deg)', None),
        ('pivot_d', 8.0, 'mm', 'M8 pivot bolts', None),
        ('pivot_drop', 180.0, 'mm', 'pivot axis below arm centreline', None),
        ('lock_r', 50.0, 'mm', 'radius of M6 tilt-lock arc slot from pivot', None),
        ('lock_slot_w', 6.6, 'mm', 'M6 clearance slot width', None),
        ('tilt_min', 0.0, 'deg', 'tilt range (deg, down from vertical face)', None),
        ('tilt_max', 30.0, 'deg', '', None),
        ('ant_tilt', 20.0, 'deg', 'as-installed antenna down-tilt (deg)', None),
        ('tp_w', 240.0, 'mm', 'tilt plate width (x) - matches reader VESA-style pattern', None),
        ('tp_h', 200.0, 'mm', 'tilt plate height', None),
        ('tp_ear_h', 60.0, 'mm', 'tilt plate side ear depth (bent 90 deg, carries pivot)', None),
        ('reader_hole_pitch', 100.0, 'mm', 'reader rear mounting hole square (assumed 100x100, M6)', None),
        ('cam_z', 1200.0, 'mm', 'camera arm centreline height', None),
        ('cam_arm_len', 300.0, 'mm', '40x40 arm length', None),
        ('cam_pitch', 20.0, 'deg', 'camera down-tilt (15-25 deg band, read zone 3-5 m)', None),
        ('cam_yaw', 12.0, 'deg', 'camera yaw toward lane centre (deg)', None),
        ('cam_plate_l', 120.0, 'mm', 'adapter plate length (5 mm 5052)', None),
        ('cam_plate_w', 80.0, 'mm', 'adapter plate width', None),
        ('cam_plate_t', 5.0, 'mm', 'adapter plate thickness', None),
        ('cam_mount_pcd', 60.0, 'mm', 'bullet-camera base 3-hole PCD (assumed, typical 2MP bullet)', None),
        ('duct_w', 40.0, 'mm', 'PVC/ASA trunking width (on -x face)', None),
        ('duct_d', 25.0, 'mm', 'trunking depth', None),
        ('duct_t', 2.0, 'mm', 'wall', None),
        ('duct_z0', 180.0, 'mm', 'start height (above socket)', None),
        ('duct_z1', 2200.0, 'mm', 'end height (below sign cabinet)', None),
        ('boot_h', 90.0, 'mm', 'printed ASA transition boot height', None),
        ('conduit_d', 25.0, 'mm', 'flexible conduit OD from plinth', None),
        ('cap_wall', 2.4, 'mm', 'cap wall', None),
        ('cap_h', 18.0, 'mm', 'cap skirt depth', None),
        ('cap_clear', 0.3, 'mm', 'fit clearance', None),
        ('sign_z', 2250.0, 'mm', 'P10 cabinet centre height', None),
        ('sign_cab_w', 360.0, 'mm', 'cabinet (1x P10 + 20 mm frame each side)', None),
        ('sign_cab_h', 200.0, 'mm', '', None),
        ('sign_cab_d', 60.0, 'mm', '', None),
        ('sign_br_t', 3.0, 'mm', 'sign bracket 3 mm 5052', None),
        ('edge_z', 900.0, 'mm', 'Edge Node enclosure centre height (on +y face)', None),
        ('edge_standoff', 30.0, 'mm', 'bracket standoff from pole face', None),
        ('plinth_w', 450.0, 'mm', '', None),
        ('plinth_h', 150.0, 'mm', 'shown above-ground portion', None),
        ('sock_in', 81.0, 'mm', 'socket inner span (81)', 'pole_w + 2 * sock_clear'),
        ('sock_long', 93.0, 'mm', 'long cheek length (93)', 'sock_in + 2 * sock_t'),
        ('cheek_r', 45.0, 'mm', 'cheek bottom radius around (0,-30)', None),
        ('cheek_bot_c', -30.0, 'mm', 'centre of bottom radius below pivot', None),
        ('cheek_x', 135.0, 'mm', 'cheek inner face x (135)', 'yoke_w / 2 - yoke_t'),
        ('tp_off', 40.0, 'mm', 'tilt plate rear face offset in front of pivot (-y)', None),
        ('ear_d', 60.0, 'mm', 'ear depth (y)', None),
        ('ear_half_h', 50.0, 'mm', 'ear half height', None),
        ('bend_k', 0.4, '', 'K-factor, 5052-H32, R = t', None),
        ('bend_allow', 10.995574287564276, 'mm', 'BA = 11.0 mm', 'pi / 2 * (yoke_bend_r + bend_k * yoke_t)'),
        ('bend_deduct', 9.004425712435724, 'mm', 'BD = 9.0 mm', '2 * (yoke_bend_r + yoke_t) - bend_allow'),
        ('web_hole_pitch', 160.0, 'mm', 'M6 T-nut holes along web', None),
        ('web_top_above_pivot', 160.0, 'mm', 'yoke web top (outer) above pivot (160)', 'pivot_drop - ant_arm_w / 2'),
        ('cam_arm_len_eff', 250.0, 'mm', 'as built: 250 mm (300 nominal in the concept; shortened to keep camera behind sign drip line)', None),
        ('cam_plate_overhang', 60.0, 'mm', 'plate overhang beyond arm end', None),
        ('sign_br_l', 200.0, 'mm', 'file-local constant of gantry_channel_cap_sign.scad', None),
        ('sign_br_w', 80.0, 'mm', 'file-local constant of gantry_channel_cap_sign.scad', None),
        ('edge_br_l', 340.0, 'mm', 'file-local constant of gantry_channel_cap_sign.scad', None),
        ('edge_br_w', 50.0, 'mm', 'file-local constant of gantry_channel_cap_sign.scad', None),
        ('edge_br_t', 3.0, 'mm', 'file-local constant of gantry_channel_cap_sign.scad', None),
        ('edge_lug_pitch', 300.0, 'mm', 'file-local constant of gantry_channel_cap_sign.scad', None),
    ],
    "EdgeParams": [
        ('enc_w', 300.0, 'mm', 'external width  (x)', None),
        ('enc_h', 400.0, 'mm', 'external height (y)', None),
        ('enc_d', 180.0, 'mm', 'external depth  (z), base + lid', None),
        ('enc_lid_d', 40.0, 'mm', 'lid depth (z)', None),
        ('enc_wall', 3.5, 'mm', 'wall thickness', None),
        ('enc_r', 10.0, 'mm', 'vertical corner radius', None),
        ('lid_boss_d', 14.0, 'mm', 'lid screw boss OD (4 corners, inside base)', None),
        ('lid_screw', 4.0, 'mm', 'M4 captive stainless lid screws', None),
        ('lid_boss_in', 13.0, 'mm', 'boss centre inset from outer corner (x and y)', None),
        ('tongue_w', 2.0, 'mm', 'rim tongue width on base', None),
        ('tongue_h', 3.0, 'mm', 'rim tongue height', None),
        ('groove_w', 4.2, 'mm', 'lid gasket groove width', None),
        ('groove_d', 5.0, 'mm', 'lid gasket groove depth', None),
        ('gasket_d', 4.5, 'mm', 'EPDM/silicone cord dia (25 % compression on tongue)', None),
        ('bp_boss_d', 12.0, 'mm', 'back-plate mounting boss OD', None),
        ('bp_boss_h', 10.0, 'mm', 'back-plate boss height above inner floor', None),
        ('bp_boss_dx', 230.0, 'mm', 'back-plate boss pitch (x)', None),
        ('bp_boss_dy', 340.0, 'mm', 'back-plate boss pitch (y)', None),
        ('mlug_w', 30.0, 'mm', 'external mounting lug width', None),
        ('mlug_x', 165.0, 'mm', 'lug centre x (+/-) -> 330 pitch to pole bracket', None),
        ('mlug_y', 150.0, 'mm', 'lug centre y (+/-)', None),
        ('mp_w', 260.0, 'mm', 'mounting plate width', None),
        ('mp_h', 360.0, 'mm', 'mounting plate height', None),
        ('mp_t', 3.0, 'mm', 'thickness', None),
        ('din_y', 100.0, 'mm', 'DIN rail centreline', None),
        ('din_len', 240.0, 'mm', 'DIN rail length', None),
        ('smps_x', -40.0, 'mm', 'LRS-150-24 centre', None),
        ('smps_y', -120.0, 'mm', '', None),
        ('pi_x', 72.0, 'mm', 'Raspberry Pi 5 centre', None),
        ('pi_y', -15.0, 'mm', '', None),
        ('pi_standoff', 12.0, 'mm', 'Pi M2.5 standoff height (on printed tray)', None),
        ('lc_x', -68.0, 'mm', 'Lane Controller PCB centre', None),
        ('lc_y', -15.0, 'mm', '', None),
        ('lc_standoff', 10.0, 'mm', 'M3 brass hex standoffs', None),
        ('buck_x', 88.0, 'mm', '24->5 V 5 A buck module', None),
        ('buck_y', -120.0, 'mm', '', None),
        ('pitray_t', 3.0, 'mm', 'printed Pi tray base thickness (ASA)', None),
        ('hs_base_l', 200.0, 'mm', 'heat-sink base length (y), on +x side wall', None),
        ('hs_base_w', 150.0, 'mm', 'heat-sink base width (z)', None),
        ('hs_base_t', 6.0, 'mm', 'heat-sink base thickness', None),
        ('hs_fin_n', 18.0, '', 'fins (vertical, along y, for natural convection)', None),
        ('hs_fin_t', 2.0, 'mm', 'fin thickness', None),
        ('hs_fin_h', 35.0, 'mm', 'fin height (outward x)', None),
        ('hs_cut_l', 160.0, 'mm', 'side-wall cut-out sealed by heat-sink base + gasket', None),
        ('hs_cut_w', 110.0, 'mm', '', None),
        ('hs_y', -15.0, 'mm', 'heat-sink centre y', None),
        ('spr_t', 5.0, 'mm', 'spreader plate thickness (6061-T6) over Pi/HAT', None),
        ('spr_l', 100.0, 'mm', 'spreader plate length (x)', None),
        ('spr_w', 70.0, 'mm', 'spreader plate width (y)', None),
        ('spr_bar_w', 20.0, 'mm', 'spreader bar to wall (y)', None),
        ('spr_bar_t', 10.0, 'mm', 'spreader bar thickness (z)', None),
        ('gland_x_1', -110.0, 'mm', 'positions along bottom [element 1 of gland_x[] in edge_params.scad]', None),
        ('gland_x_2', -60.0, 'mm', 'positions along bottom [element 2 of gland_x[] in edge_params.scad]', None),
        ('gland_x_3', -10.0, 'mm', 'positions along bottom [element 3 of gland_x[] in edge_params.scad]', None),
        ('gland_x_4', 40.0, 'mm', 'positions along bottom [element 4 of gland_x[] in edge_params.scad]', None),
        ('gland_x_5', 90.0, 'mm', 'positions along bottom [element 5 of gland_x[] in edge_params.scad]', None),
        ('gland_m_1', 25.0, 'mm', 'M25 mains, M20 PoE cam, M20 RFID, M20 motor/IO, M16 sensors [element 1 of gland_m[] in edge_params.scad]', None),
        ('gland_m_2', 20.0, 'mm', 'M25 mains, M20 PoE cam, M20 RFID, M20 motor/IO, M16 sensors [element 2 of gland_m[] in edge_params.scad]', None),
        ('gland_m_3', 20.0, 'mm', 'M25 mains, M20 PoE cam, M20 RFID, M20 motor/IO, M16 sensors [element 3 of gland_m[] in edge_params.scad]', None),
        ('gland_m_4', 20.0, 'mm', 'M25 mains, M20 PoE cam, M20 RFID, M20 motor/IO, M16 sensors [element 4 of gland_m[] in edge_params.scad]', None),
        ('gland_m_5', 16.0, 'mm', 'M25 mains, M20 PoE cam, M20 RFID, M20 motor/IO, M16 sensors [element 5 of gland_m[] in edge_params.scad]', None),
        ('vent_x', 125.0, 'mm', 'M12 pressure-equalisation vent (ePTFE)', None),
        ('hood_gap', 25.0, 'mm', '', None),
        ('hood_t', 2.0, 'mm', '', None),
        ('hood_front', 60.0, 'mm', 'visor overhang in front of lid', None),
        ('base_d_', 140.0, 'mm', 'file-local constant of edge_node_assembly.scad', 'enc_d - enc_lid_d'),
        ('inner_floor', 13.5, 'mm', 'mounting plate seat (z)', 'enc_wall + bp_boss_h'),
    ],
    "BarrierParams": [
        ('boom_angle', 0.0, 'deg', '0 = closed (horizontal), 90 = open (vertical) - animate with -D', None),
        ('hs_x', 300.0, 'mm', 'housing footprint x', None),
        ('hs_y', 250.0, 'mm', 'housing footprint y', None),
        ('hs_z', 800.0, 'mm', 'housing height (panels) above base plate', None),
        ('hsg_bp_t', 8.0, 'mm', 'base plate thickness (MS, 4x M10 anchors)', None),
        ('hsg_bp_mx', 30.0, 'mm', 'base plate margin beyond housing (anchor flange)', None),
        ('frame_w', 20.0, 'mm', '20x20 Al T-slot frame (6 mm slot)', None),
        ('panel_t', 2.0, 'mm', '5052-H32 skin panels', None),
        ('roof_t', 3.0, 'mm', 'roof panel 3 mm, 5 deg fall', None),
        ('anchor_d', 10.0, 'mm', 'M10 anchors', None),
        ('shaft_z', 720.0, 'mm', 'output shaft centre height above ground', None),
        ('shaft_d', 20.0, 'mm', 'stub shaft dia (EN8, keyed both ends)', None),
        ('gm_face_y', 15.0, 'mm', 'gearmotor output face y (shaft points -y)', None),
        ('mplate_t', 6.0, 'mm', 'motor plate 6061-T6 (vertical, x-z plane)', None),
        ('mplate_w', 200.0, 'mm', 'motor plate width (x)', None),
        ('mplate_h', 150.0, 'mm', 'motor plate height (z)', None),
        ('coup_d', 30.0, 'mm', 'jaw coupling D x L', None),
        ('coup_l', 30.0, 'mm', '', None),
        ('brg_plate_y', -70.0, 'mm', 'internal bearing plate y', None),
        ('brg_flange', 60.0, 'mm', '2-bolt flange bearing (UCFL204 class, 20 bore) - envelope length', None),
        ('hub_d', 70.0, 'mm', 'hub flange dia (6061-T6, keyed on shaft, M8 clamp)', None),
        ('hub_t', 16.0, 'mm', 'hub flange thickness', None),
        ('hub_gap', 35.0, 'mm', 'gap from front panel outer face to hub', None),
        ('tongue_l', 70.0, 'mm', 'hub tongue (radial) carrying hinge + shear pin', None),
        ('tongue_t', 12.0, 'mm', 'tongue thickness (y)', None),
        ('tongue_w', 60.0, 'mm', 'tongue height (world z when closed) = boom_h so carrier plates clamp the boom', None),
        ('carrier_l', 160.0, 'mm', 'carrier clevis plate length (along boom)', None),
        ('carrier_w', 70.0, 'mm', 'carrier plate width', None),
        ('carrier_t', 5.0, 'mm', '6061-T6 plates (two, above/below tongue)', None),
        ('hinge_d', 8.0, 'mm', 'M8 shoulder bolt hinge (vertical when closed)', None),
        ('hinge_r', 45.0, 'mm', 'hinge distance from shaft axis along boom', None),
        ('shear_d', 5.0, 'mm', '6061-T6 shear pin dia (calcs: breaks at ~104 N tip)', None),
        ('shear_e', 35.0, 'mm', 'shear pin offset from hinge (in y)', None),
        ('clamp_pitch', 60.0, 'mm', '2x M6 through-bolts clamping boom in carrier', None),
        ('boom_L', 1200.0, 'mm', 'boom length from shaft axis to tip', None),
        ('boom_h', 60.0, 'mm', 'Al 6063-T5 rect tube 60 x 30 x 1.5', None),
        ('boom_b', 30.0, 'mm', '', None),
        ('boom_t', 1.5, 'mm', '', None),
        ('band_pitch', 200.0, 'mm', 'red/white reflective bands', None),
        ('tip_cap_l', 30.0, 'mm', 'printed ASA tip cap (soft nose)', None),
        ('cw_arm', 200.0, 'mm', 'counterweight centroid radius (tail along -x)', None),
        ('cw_plate_x', 100.0, 'mm', 'MS plate 100 x 60 x 10 each', None),
        ('cw_plate_z', 60.0, 'mm', '', None),
        ('cw_plate_t', 10.0, 'mm', '', None),
        ('cw_n', 7.0, '', 'number of plates (calcs: 2.98 kg -> 7 x 0.47 kg)', None),
        ('cw_bar_w', 40.0, 'mm', 'tail bar 40 x 10 flat (MS)', None),
        ('cw_bar_t', 10.0, 'mm', '', None),
        ('flag_r', 55.0, 'mm', 'flag tip radius', None),
        ('flag_t', 3.0, 'mm', '5052 flag', None),
        ('lim_sw_r', 62.0, 'mm', 'inductive sensor (M12) radius from shaft', None),
        ('pb_z', 300.0, 'mm', 'beam height above ground', None),
        ('pb_post_h', 450.0, 'mm', '20x20 post height', None),
        ('pb_dy', 300.0, 'mm', 'ASSUMPTION: beam line 300 mm downstream (+y) of the boom plane, beam height pb_z', None),
        ('pb_x1', 250.0, 'mm', 'post 1 x (beside housing)', None),
        ('pb_x2', 1400.0, 'mm', 'post 2 x (past boom tip)', None),
        ('pb_foot', 100.0, 'mm', '5 mm MS foot plate side', None),
        ('hy_front', -125.0, 'mm', 'front panel plane (outer)', '-hs_y / 2'),
        ('hub_y', -170.0, 'mm', 'hub mid-plane y', 'hy_front - panel_t - hub_gap - hub_t / 2'),
        ('boom_y', -186.0, 'mm', 'boom/carrier mid-plane... carrier straddles tongue', 'hub_y - hub_t / 2 - tongue_t / 2 - 2 mm'),
    ],
    "OccParams": [
        ('oc_d', 96.0, 'mm', 'outer diameter', None),
        ('oc_wall', 2.4, 'mm', 'wall (6 perimeters @0.4 nozzle)', None),
        ('oc_base_h', 22.0, 'mm', 'base cup depth', None),
        ('oc_cover_h', 26.0, 'mm', 'cover depth (incl. dome)', None),
        ('oc_floor', 3.0, 'mm', 'base back plate thickness', None),
        ('oc_r_edge', 4.0, 'mm', 'edge fillet (approx.)', None),
        ('oc_screw_pitch', 60.0, 'mm', 'ceiling screw pitch', None),
        ('oc_screw_d', 5.5, 'mm', 'M5 / #10 wood screw clearance', None),
        ('oc_cable_d', 8.0, 'mm', 'rear cable entry (grommet)', None),
        ('snap_n', 3.0, '', 'snap hooks', None),
        ('snap_w', 10.0, 'mm', 'hook width', None),
        ('snap_l', 12.0, 'mm', 'cantilever length', None),
        ('snap_t', 1.6, 'mm', 'cantilever thickness (ASA strain at 0.8 mm deflection ~ 1.5 % OK)', None),
        ('snap_lip', 0.8, 'mm', 'hook undercut', None),
        ('lip_h', 5.0, 'mm', 'cover spigot overlap into base', None),
        ('fit_clear', 0.25, 'mm', 'spigot radial clearance', None),
        ('esp_standoff', 5.0, 'mm', 'ESP32-C3 board standoffs', None),
        ('ring_od', 50.0, 'mm', 'WS2812 ring OD (12 LED)', None),
        ('ring_id', 36.0, 'mm', '', None),
        ('probe_d', 34.0, 'mm', 'A02YYUW probe (ASSUMED, see pf_bought.scad)', None),
        ('diffuser_t', 1.2, 'mm', 'printed natural/white PETG diffuser ring thickness', None),
    ],
    "LaneParams": [
        ('lane_w', 3500.0, 'mm', 'lane width (x)', None),
        ('lane_l', 8000.0, 'mm', 'lane length (y)', None),
        ('island_w', 600.0, 'mm', 'kerb island width (+x side)', None),
        ('island_h', 150.0, 'mm', 'kerb height', None),
        ('pole_y', 5200.0, 'mm', 'pole station along the lane (from lane entry y=0)', None),
        ('bar_y', 5700.0, 'mm', 'barrier housing centre y', None),
        ('car_y', 2400.0, 'mm', 'car centre y (front bumper inside the RFID read zone)', None),
        ('rz_w', 3000.0, 'mm', 'file-local constant of lane_layout.scad', None),
        ('rz_h', 1800.0, 'mm', 'file-local constant of lane_layout.scad', None),
        ('cam_hfov', 40.0, 'deg', 'deg (narrowed: 8-12 mm varifocal set for ANPR, ~150 px plate width at 4 m)', None),
        ('cam_vfov', 24.0, 'deg', 'file-local constant of lane_layout.scad', None),
        ('cam_range', 5500.0, 'mm', 'file-local constant of lane_layout.scad', None),
        ('boom_ang', 0.0, 'deg', 'barrier angle (0 closed, 90 open)', None),
    ],
}
# END GENERATED PARAMETER TABLES


def _value_text(value, unit, formula):
    if formula:
        return "=" + formula
    if unit:
        return "=%s %s" % (repr(float(value)).rstrip("0").rstrip(".") if value != int(value) else str(int(value)), unit)
    return "=%s" % (repr(float(value)).rstrip("0").rstrip(".") if value != int(value) else str(int(value)))


def make_sheet(doc, name, rows):
    existing = doc.getObject(name)
    if existing is not None:
        if not OVERWRITE:
            App.Console.PrintWarning("ParkFlow: sheet %s exists - left untouched (OVERWRITE=False)\n" % name)
            return existing
        doc.removeObject(name)
    sh = doc.addObject("Spreadsheet::Sheet", name)
    sh.set("A1", "alias")
    sh.set("B1", "value")
    sh.set("C1", "unit")
    sh.set("D1", "comment (source: OpenSCAD *.scad)")
    # aliases first, so formulas can refer to them regardless of row order
    for i, (alias, value, unit, comment, formula) in enumerate(rows, start=2):
        sh.set("A%d" % i, alias)
        sh.setAlias("B%d" % i, alias)
    for i, (alias, value, unit, comment, formula) in enumerate(rows, start=2):
        sh.set("B%d" % i, _value_text(value, unit, formula))
        sh.set("C%d" % i, unit or "-")
        sh.set("D%d" % i, comment or "")
    try:
        sh.setColumnWidth("A", 160)
        sh.setColumnWidth("B", 90)
        sh.setColumnWidth("C", 50)
        sh.setColumnWidth("D", 520)
    except Exception:
        pass
    return sh


def run():
    doc = App.ActiveDocument or App.newDocument("ParkFlow")
    for name, rows in TABLES.items():
        if ONLY and name not in ONLY:
            continue
        make_sheet(doc, name, rows)
        App.Console.PrintMessage("ParkFlow: %s - %d parameters\n" % (name, len(rows)))
    doc.recompute()
    App.Console.PrintMessage("ParkFlow: done. Use expressions like  GantryParams.bp_t  in sketches / pads.\n")


run()
