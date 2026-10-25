// =====================================================================
// ParkFlow - (c) DEMO BOOM BARRIER : master parameter set (mm, deg)
// Frame: origin = ground centre under housing; +x = across lane (boom
// points +x when closed); -y = approach side (hub/boom outside the
// housing front panel); z up. Boom rotates about the y-axis shaft.
// =====================================================================
boom_angle   = 0;      // 0 = closed (horizontal), 90 = open (vertical) - animate with -D

// ---------- housing ----------------------------------------------------
hs_x         = 300;    // housing footprint x
hs_y         = 250;    // housing footprint y
hs_z         = 800;    // housing height (panels) above base plate
hsg_bp_t     = 8;      // base plate thickness (MS, 4x M10 anchors)
hsg_bp_mx    = 30;     // base plate margin beyond housing (anchor flange)
frame_w      = 20;     // 20x20 Al T-slot frame (6 mm slot)
panel_t      = 2;      // 5052-H32 skin panels
roof_t       = 3;      // roof panel 3 mm, 5 deg fall
anchor_d     = 10;     // M10 anchors

// ---------- drive train -----------------------------------------------
shaft_z      = 720;    // output shaft centre height above ground
shaft_d      = 20;     // stub shaft dia (EN8, keyed both ends)
gm_face_y    = 15;     // gearmotor output face y (shaft points -y)
mplate_t     = 6;      // motor plate 6061-T6 (vertical, x-z plane)
mplate_w     = 200;    // motor plate width (x)
mplate_h     = 150;    // motor plate height (z)
coup_d       = 30;     // jaw coupling D x L
coup_l       = 30;
brg_plate_y  = -70;    // internal bearing plate y
brg_flange   = 60;     // 2-bolt flange bearing (UCFL204 class, 20 bore) - envelope length
hub_d        = 70;     // hub flange dia (6061-T6, keyed on shaft, M8 clamp)
hub_t        = 16;     // hub flange thickness
hub_gap      = 35;     // gap from front panel outer face to hub
tongue_l     = 70;     // hub tongue (radial) carrying hinge + shear pin
tongue_t     = 12;     // tongue thickness (y)
tongue_w     = 60;     // tongue height (world z when closed) = boom_h so carrier plates clamp the boom

// ---------- boom carrier + breakaway ----------------------------------
carrier_l    = 160;    // carrier clevis plate length (along boom)
carrier_w    = 70;     // carrier plate width
carrier_t    = 5;      // 6061-T6 plates (two, above/below tongue)
hinge_d      = 8;      // M8 shoulder bolt hinge (vertical when closed)
hinge_r      = 45;     // hinge distance from shaft axis along boom
shear_d      = 5;      // 6061-T6 shear pin dia (calcs: breaks at ~104 N tip)
shear_e      = 35;     // shear pin offset from hinge (in y)
clamp_pitch  = 60;     // 2x M6 through-bolts clamping boom in carrier

// ---------- boom --------------------------------------------------------
boom_L       = 1200;   // boom length from shaft axis to tip
boom_h       = 60;     // Al 6063-T5 rect tube 60 x 30 x 1.5
boom_b       = 30;
boom_t       = 1.5;
band_pitch   = 200;    // red/white reflective bands
tip_cap_l    = 30;     // printed ASA tip cap (soft nose)

// ---------- counterweight ---------------------------------------------
cw_arm       = 200;    // counterweight centroid radius (tail along -x)
cw_plate_x   = 100;    // MS plate 100 x 60 x 10 each
cw_plate_z   = 60;
cw_plate_t   = 10;
cw_n         = 7;      // number of plates (calcs: 2.98 kg -> 7 x 0.47 kg)
cw_bar_w     = 40;     // tail bar 40 x 10 flat (MS)
cw_bar_t     = 10;

// ---------- limit flags & sensors --------------------------------------
flag_r       = 55;     // flag tip radius
flag_t       = 3;      // 5052 flag
lim_sw_r     = 62;     // inductive sensor (M12) radius from shaft

// ---------- photo-beam --------------------------------------------------
pb_z         = 300;    // beam height above ground
pb_post_h    = 450;    // 20x20 post height
pb_dy        = 300;    // ASSUMPTION: beam line 300 mm downstream (+y) of the boom plane, beam height pb_z
pb_x1        = 250;    // post 1 x (beside housing)
pb_x2        = 1400;   // post 2 x (past boom tip)
pb_foot      = 100;    // 5 mm MS foot plate side
