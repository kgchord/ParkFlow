// =====================================================================
// ParkFlow - (a) LANE GANTRY POLE : master parameter set  (all mm, deg)
// This file is the OpenSCAD equivalent of the FreeCAD spreadsheet
// "GantryParams" - identical variable names are used in the rebuild plan.
//
// Frame: pole axis = +z, origin at concrete top / plate underside centre.
// +x = towards lane centre (arms point this way), -y = towards approaching
// vehicles (sensors face -y), +y = downstream.
// =====================================================================

// ---------- pole ------------------------------------------------------
// DESIGN CHANGE vs Stage 1: calcs.py shows a single 40x40 profile reaches
// sigma = 239 MPa (FoS 0.46) at Delhi Vb = 47 m/s. Pole upsized to 80x80
// 8-slot (Wolweiss AST08008008: I = 109.9 cm4, W = 27.5 cm3) -> FoS 2.15.
pole_w          = 80;     // pole profile width  (x)
pole_d          = 80;     // pole profile depth  (y)
pole_pitch      = 40;     // slot pitch of 40-series profile
pole_slot       = 10;     // slot opening width (10 mm, 40-series)
pole_len        = 2400;   // pole length above base plate

// ---------- base plate weldment (MS IS 2062 E250, laser cut + MIG) ----
bp_w            = 250;    // base plate side (square)
bp_t            = 16;     // base plate thickness (calcs: 16 -> FoS 2.89; 12 -> 1.62)
bp_corner_r     = 12;     // plate corner radius
bp_pcd          = 190;    // anchor bolt pitch-circle diameter (4 bolts on 45 deg diagonals)
bp_anchor_d     = 12;     // anchor size M12 (chemical anchor, class 8.8 stud)
bp_anchor_hole  = 14;     // clearance hole for M12 (+2 mm for site tolerance)
bp_centre_hole  = 30;     // centre drain / grout-vent hole
grout_gap       = 25;     // levelling-nut / non-shrink grout gap under plate
sock_h          = 150;    // socket cheek height above plate
sock_t          = 6;      // socket cheek plate thickness
sock_clear      = 0.5;    // per-side clearance pole <-> socket
sock_bolt_d     = 10;     // M10 cross bolts through socket + pole
sock_bolt_z1    = 45;     // lower cross bolt height above plate top
sock_bolt_z2    = 115;    // upper cross bolt height (rotated 90 deg)
gus_n           = 4;      // number of gussets (on face centre-lines)
gus_l           = 74;     // gusset base length (socket face -> 4 mm short of plate edge)
gus_h           = 120;    // gusset height
gus_t           = 6;      // gusset thickness
gus_chamfer     = 12;     // corner snipe for weld clearance
gus_tip         = 15;     // flat at top of gusset (no sharp tip)

// ---------- RFID antenna arm + tilt bracket ---------------------------
ant_z           = 1500;   // arm centreline height above plate underside
ant_arm_len     = 350;    // 40x40 arm length from pole face
ant_arm_w       = 40;     // arm profile (40x40, 10 mm slot)
yoke_t          = 5;      // yoke + tilt plate sheet thickness (5052-H32)
yoke_w          = 280;    // yoke top-web length (across x) = reader width + 2 cheeks + clear
yoke_web_d      = 60;     // yoke web depth (y)
yoke_cheek_h    = 200;    // yoke cheek drop below arm underside
yoke_cheek_d    = 80;     // cheek width (y)
yoke_bend_r     = 5;      // inside bend radius (= t for 5052-H32, 90 deg)
pivot_d         = 8;      // M8 pivot bolts
pivot_drop      = 180;    // pivot axis below arm centreline
lock_r          = 50;     // radius of M6 tilt-lock arc slot from pivot
lock_slot_w     = 6.6;    // M6 clearance slot width
tilt_min        = 0;      // tilt range (deg, down from vertical face)
tilt_max        = 30;
ant_tilt        = 20;     // as-installed antenna down-tilt (deg)
tp_w            = 240;    // tilt plate width (x) - matches reader VESA-style pattern
tp_h            = 200;    // tilt plate height
tp_ear_h        = 60;     // tilt plate side ear depth (bent 90 deg, carries pivot)
reader_hole_pitch = 100;  // reader rear mounting hole square (assumed 100x100, M6)

// ---------- camera arm -----------------------------------------------
cam_z           = 1200;   // camera arm centreline height
cam_arm_len     = 300;    // 40x40 arm length
cam_pitch       = 20;     // camera down-tilt (15-25 deg band, read zone 3-5 m)
cam_yaw         = 12;     // camera yaw toward lane centre (deg)
cam_plate_l     = 120;    // adapter plate length (5 mm 5052)
cam_plate_w     = 80;     // adapter plate width
cam_plate_t     = 5;      // adapter plate thickness
cam_mount_pcd   = 60;     // bullet-camera base 3-hole PCD (assumed, typical 2MP bullet)

// ---------- cable channel --------------------------------------------
duct_w          = 40;     // PVC/ASA trunking width (on -x face)
duct_d          = 25;     // trunking depth
duct_t          = 2;      // wall
duct_z0         = 180;    // start height (above socket)
duct_z1         = 2200;   // end height (below sign cabinet)
boot_h          = 90;     // printed ASA transition boot height
conduit_d       = 25;     // flexible conduit OD from plinth

// ---------- pole cap (FDM ASA) ---------------------------------------
cap_wall        = 2.4;    // cap wall
cap_h           = 18;     // cap skirt depth
cap_clear       = 0.3;    // fit clearance

// ---------- payloads carried by the pole -----------------------------
sign_z          = 2250;   // P10 cabinet centre height
sign_cab_w      = 360;    // cabinet (1x P10 + 20 mm frame each side)
sign_cab_h      = 200;
sign_cab_d      = 60;
sign_br_t       = 3;      // sign bracket 3 mm 5052
edge_z          = 900;    // Edge Node enclosure centre height (on +y face)
edge_standoff   = 30;     // bracket standoff from pole face

// ---------- concrete plinth (context only) ---------------------------
plinth_w        = 450;
plinth_h        = 150;    // shown above-ground portion
