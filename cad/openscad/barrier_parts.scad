// =====================================================================
// ParkFlow (c) parts: DEMO BOOM BARRIER
//   housing frame + skins + base plate, motor plate, bearing plate,
//   stub shaft, hub with tongue (6061-T6, CNC/lathe), carrier clevis
//   plates (laser 5 mm 6061), boom tube, counterweight tail + plates,
//   limit flags (3 mm 5052), photo-beam posts, ASA tip cap & cable clips.
// 2D (*_2d) modules are laser profiles -> DXF.
// =====================================================================
include <barrier_params.scad>
include <pf_bought.scad>

hy_front = -hs_y / 2;                              // front panel plane (outer)
hub_y    = hy_front - panel_t - hub_gap - hub_t / 2; // hub mid-plane y
boom_y   = hub_y - hub_t / 2 - tongue_t / 2 - 2;      // boom/carrier mid-plane... carrier straddles tongue

// ---------------- housing ---------------------------------------------
module housing_base_plate_2d() {
    difference() {
        rrect(hs_x + 2 * hsg_bp_mx, hs_y + 2 * hsg_bp_mx, 10);
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx * (hs_x / 2 + hsg_bp_mx / 2 - 2), sy * (hs_y / 2 + hsg_bp_mx / 2 - 2)]) circle(d = anchor_d + 2);
        translate([60, 0]) circle(d = 40);      // cable entry
    }
}
module housing_frame() {
    // 4 corner posts + top/bottom rails, 20x20
    for (sx = [-1, 1], sy = [-1, 1]) translate([sx * (hs_x / 2 - frame_w / 2), sy * (hs_y / 2 - frame_w / 2), hsg_bp_t]) tslot(20, 20, hs_z - 2, 20, 6);
    for (z = [hsg_bp_t, hsg_bp_t + hs_z - frame_w - 2], sy = [-1, 1])
        translate([-hs_x / 2 + frame_w, sy * (hs_y / 2 - frame_w / 2), z + frame_w / 2]) rotate([0, 90, 0]) translate([-0, 0, 0]) tslot(20, 20, hs_x - 2 * frame_w, 20, 6);
    for (z = [hsg_bp_t, hsg_bp_t + hs_z - frame_w - 2], sx = [-1, 1])
        translate([sx * (hs_x / 2 - frame_w / 2), -hs_y / 2 + frame_w, z + frame_w / 2]) rotate([-90, 0, 0]) tslot(20, 20, hs_y - 2 * frame_w, 20, 6);
}
module panel_front_2d() {        // x-z, with shaft hole + bearing bolts + service label
    difference() {
        translate([-hs_x / 2, 0]) square([hs_x, hs_z]);
        translate([0, shaft_z - hsg_bp_t]) { circle(d = shaft_d + 10); for (s = [-1, 1]) translate([s * 45, 0]) circle(d = 10.5); }
    }
}
module housing_skins(cut_front = false) {
    color(C_STRUCT) {
        // front (-y) with shaft hole
        translate([0, -hs_y / 2 + panel_t, hsg_bp_t]) rotate([90, 0, 0]) linear_extrude(panel_t) panel_front_2d();
        // back (+y) - access door (shown closed)
        translate([-hs_x / 2, hs_y / 2 - 0.01, hsg_bp_t]) cube([hs_x, panel_t, hs_z]);
        // sides (x)
        for (s = [-1, 1]) translate([s * (hs_x / 2) - (s > 0 ? 0 : panel_t), -hs_y / 2, hsg_bp_t]) cube([panel_t, hs_y, hs_z]);
    }
    // roof with fall
    color(C_STRUCT) translate([0, 0, hsg_bp_t + hs_z]) rotate([5, 0, 0]) translate([-hs_x / 2 - 10, -hs_y / 2 - 15, 0]) cube([hs_x + 20, hs_y + 30, roof_t]);
    // yellow/black hazard band on front
    for (i = [0 : 7]) color(i % 2 ? [0.1, 0.1, 0.1] : [0.98, 0.80, 0.10])
        translate([-hs_x / 2 + i * hs_x / 8, -hs_y / 2 - 0.4, hsg_bp_t + 40]) cube([hs_x / 8, 0.5, 60]);
}
// ---------------- drive train -----------------------------------------
module motor_plate_2d() {
    difference() {
        translate([-mplate_w / 2, -mplate_h / 2]) square([mplate_w, mplate_h]);
        circle(d = 26);                                            // output boss clearance
        for (x = [-35, 35], z = [-25, 25]) translate([-gm_shaft_off + x, z]) circle(d = 6.6);   // gearmotor 4x M6 on 70 x 50 (ASSUMED)
        for (x = [-1, 1], z = [-1, 1]) translate([x * (mplate_w / 2 - 10), z * (mplate_h / 2 - 10)]) circle(d = 5.5);  // M5 T-nuts to frame cross-rails
    }
}
module bearing_plate_2d() {
    difference() {
        translate([-(hs_x - 2 * frame_w) / 2, -50]) square([hs_x - 2 * frame_w, 100]);
        circle(d = shaft_d + 10);
        for (s = [-1, 1]) translate([s * 45, 0]) circle(d = 10.5);
        for (x = [-1, 1]) translate([x * ((hs_x - 2 * frame_w) / 2 - 10), 0]) circle(d = 5.5);
    }
}
module flange_bearing() {   // UCFL204-class 2-bolt flange unit (envelope)
    color([0.35, 0.36, 0.40]) rotate([90, 0, 0]) {
        hull() { for (s = [-1, 1]) translate([s * 45, 0, 0]) cylinder(d = 26, h = 11); cylinder(d = 60, h = 11); }
        cylinder(d = 46, h = 24);
    }
    color([0.80, 0.80, 0.82]) rotate([90, 0, 0]) translate([0, 0, -6]) cylinder(d = 34, h = 36);   // insert collar
}
module drive_train(explode = 0) {
    ex = explode;
    // motor plate (vertical x-z plane at y=gm_face_y)
    color([0.70, 0.72, 0.75]) translate([0, gm_face_y + 120 * ex, shaft_z]) rotate([90, 0, 0]) linear_extrude(mplate_t) motor_plate_2d();
    // gearmotor behind plate (+y), output shaft -> -y
    translate([0, gm_face_y + 200 * ex, shaft_z]) rotate([90, 0, 0]) translate([-gm_shaft_off, 0, 0]) gearmotor();
    // jaw coupling
    color([0.85, 0.30, 0.15]) translate([0, gm_face_y - 15 + 60 * ex, shaft_z]) rotate([90, 0, 0]) cylinder(d = coup_d, h = coup_l);
    // bearing plate + bearing
    color([0.70, 0.72, 0.75]) translate([0, brg_plate_y + 30 * ex, shaft_z]) rotate([90, 0, 0]) linear_extrude(mplate_t) bearing_plate_2d();
    translate([0, brg_plate_y - mplate_t + 30 * ex, shaft_z]) flange_bearing();
    // front bearing outside front panel
    translate([0, -hs_y / 2 - 0 - 40 * ex, shaft_z]) flange_bearing();
    // stub shaft (orange - moving)
    color(C_MOVE) translate([0, gm_face_y - 40 - 100 * ex, shaft_z]) rotate([90, 0, 0]) cylinder(d = shaft_d, h = (gm_face_y - 40) - (hub_y - hub_t / 2) + 5 );
}

// ---------------- hub (moving, orange) --------------------------------
// hub-local: shaft along local z (= world -y), tongue along local +x
module hub() {
    color(C_MOVE) difference() {
        union() {
            cylinder(d = hub_d, h = hub_t, center = true);
            translate([0, -tongue_w / 2, -tongue_t / 2]) cube([tongue_l + hinge_r - 25, tongue_w, tongue_t]);
            // counterweight tail stub (-x)
            translate([-hub_d / 2 - 10, -cw_bar_w / 2, -cw_bar_t / 2]) cube([30, cw_bar_w, cw_bar_t]);
        }
        cylinder(d = shaft_d + 0.05, h = hub_t + 2, center = true);
        translate([hinge_r, 0, 0]) rotate([90, 0, 0]) cylinder(d = hinge_d + 0.2, h = tongue_w + 2, center = true);   // hinge bore, vertical (world z) when closed
        translate([hinge_r + shear_e, 0, 0]) rotate([90, 0, 0]) cylinder(d = shear_d + 0.1, h = tongue_w + 2, center = true); // shear-pin bore
        translate([0, 0, -hub_t]) rotate([0, 0, 0]) translate([-3, shaft_d / 2 - 1, 0]) cube([6, 4, 2 * hub_t]);           // 6 mm key way
    }
}
// limit flags bolted to hub face at 0 deg and 90 deg sense positions
module limit_flag_2d() {
    difference() {
        hull() { circle(d = 16); translate([flag_r - 8, 0]) square([16, 20], center = true); }
        circle(d = 5.5);
    }
}
module limit_flags() {
    // single flag: at 0 deg (closed) faces sensor S1 at 225 deg; at 90 deg (open) faces sensor S2 at 315 deg
    color(C_MOVE) rotate([0, 0, 225]) translate([0, 0, hub_t / 2]) linear_extrude(flag_t) limit_flag_2d();
}
// ---------------- carrier (breakaway clevis) ---------------------------
// Two plates above & below the tongue (normal = hub-local y, which is the
// world vertical axis when the boom is closed). Hinge M8 at hinge_r,
// shear pin at hinge_r + shear_e... the plates also clamp the boom.
module carrier_plate_2d() {
    difference() {
        hull() {
            translate([hinge_r, 0]) circle(d = 40);
            translate([hinge_r + carrier_l - 10, -carrier_w / 2 + 10]) circle(r = 10);
            translate([hinge_r + carrier_l - 10, carrier_w / 2 - 10]) circle(r = 10);
            translate([hinge_r + 20, -carrier_w / 2]) square([1, carrier_w]);
        }
        translate([hinge_r, 0]) circle(d = hinge_d + 0.3);
        translate([hinge_r + shear_e, 0]) circle(d = shear_d + 0.1);
        for (i = [0, 1]) translate([hinge_r + 80 + i * clamp_pitch, 0]) circle(d = 6.6);
    }
}
module carrier(explode = 0) {
    color(C_MOVE * 0.92) for (s = [-1, 1]) translate([0, s * (tongue_w / 2 + carrier_t / 2 + 0.5 + 60 * explode), 0])
        rotate([90, 0, 0]) translate([0, 0, -carrier_t / 2]) linear_extrude(carrier_t) carrier_plate_2d();
    // hinge bolt + shear pin (along hub-local y)
    color(C_HW) translate([hinge_r, -tongue_w / 2 - carrier_t - 8, 0]) rotate([-90, 0, 0]) cylinder(d = hinge_d, h = tongue_w + 2 * carrier_t + 16);
    color([0.85, 0.15, 0.15]) translate([hinge_r + shear_e, -tongue_w / 2 - carrier_t - 3 - 40 * explode, 0]) rotate([-90, 0, 0]) cylinder(d = shear_d, h = tongue_w + 2 * carrier_t + 6);
}
// ---------------- boom ---------------------------------------------------
// boom tube from r = hinge_r + 60 to boom_L, cross-section 30 (y_local) x 60 (z_local?)
// hub-local frame: x radial, y = carrier plate normal (world z when closed), z = shaft axis.
// Tube: 60 tall measured in hub-local y? No - boom vertical bending depth (60) must be
// world-vertical when closed = hub-local y.  It sits BETWEEN the carrier plates -> carrier
// spacing set by tube: we let the tube pass through/between plates, plates sandwich the
// tube's 60 mm faces?  For simplicity tube 60 dim along hub-local y equals tongue_w + 2*0.5+...
module boom(explode = 0) {
    r0 = hinge_r + 60;
    translate([r0 + 200 * explode, 0, 0]) rotate([0, 90, 0]) {
        color(C_MOVE) translate([0, 0, 0]) rotate([0, 0, 90]) rhs(boom_h, boom_b, boom_t, boom_L - r0 - tip_cap_l);
        // red bands
        for (z = [band_pitch / 2 : band_pitch * 2 : boom_L - r0 - band_pitch]) color([0.85, 0.12, 0.12])
            translate([0, 0, z]) rotate([0, 0, 90]) linear_extrude(band_pitch) difference() { rrect(boom_h + 0.6, boom_b + 0.6, 1.5); rrect(boom_h - 0.2, boom_b - 0.2, 1); }
        // ASA tip cap
        color([0.95, 0.20, 0.15]) translate([0, 0, boom_L - r0 - tip_cap_l]) rotate([0, 0, 90]) hull() { rbox(boom_h + 4, boom_b + 4, tip_cap_l - 10, 4); translate([0, 0, tip_cap_l - 1]) rbox(boom_h - 10, boom_b - 6, 1, 4); }
    }
    // clamp bolts
    color(C_HW) for (i = [0, 1]) translate([hinge_r + 80 + i * clamp_pitch, -boom_h / 2 - carrier_t - 8, 0]) rotate([-90, 0, 0]) cylinder(d = 6, h = boom_h + 2 * carrier_t + 16);
}
// ---------------- counterweight ------------------------------------------
module counterweight(explode = 0) {
    color(C_STRUCT_DK) translate([-cw_arm - cw_plate_x / 2 - 10, -cw_bar_w / 2, -cw_bar_t / 2]) cube([cw_arm + cw_plate_x / 2 - hub_d / 2 + 20, cw_bar_w, cw_bar_t]);  // tail bar
    color([0.85, 0.48, 0.10]) for (i = [0 : cw_n - 1]) translate([-cw_arm - cw_plate_x / 2, -cw_plate_z / 2, cw_bar_t / 2 + i * cw_plate_t + 150 * explode * (i + 1) / cw_n])
        cube([cw_plate_x, cw_plate_z, cw_plate_t - 0.3]);
    color(C_HW) for (x = [-cw_arm - 30, -cw_arm + 30]) translate([x, 0, -cw_bar_t / 2 - 8]) cylinder(d = 8, h = cw_bar_t + cw_n * cw_plate_t + 20);
}

// ---------------- rotating group (hub frame) ------------------------------
module rotor(explode = 0) {
    hub();
    limit_flags();
    translate([60 * explode, 0, -0 * explode]) carrier(explode);
    translate([0, 0, 0]) boom(explode);
    translate([-80 * explode, 0, 0]) counterweight(explode);
}

// ---------------- limit sensor bracket (fixed) ---------------------------
module limit_sensors() {
    // two M12 inductive proximity sensors on a 3 mm bracket, sensing the flags
    for (a = [225, 315]) rotate([0, 0, a]) translate([lim_sw_r - 6, 0, hub_t / 2 + flag_t + 3]) color(C_SENSOR) cylinder(d = 12, h = 45);
    // sensor bracket (3 mm 5052, fixed to front bearing bolts) - simplified arc plate
    color(C_STRUCT) translate([0, 0, hub_t / 2 + flag_t + 48]) linear_extrude(3) difference() {
        hull() for (a = [225, 315]) rotate(a) translate([lim_sw_r - 6, 0]) circle(d = 26);
        circle(d = shaft_d + 6);
    }
}

// ---------------- photo-beam posts ---------------------------------------
module pb_foot_2d() { difference() { rrect(pb_foot, pb_foot, 6); for (sx = [-1, 1], sy = [-1, 1]) translate([sx * 35, sy * 35]) circle(d = 8.5); for (sx = [-1, 1]) translate([sx * 10, 0]) circle(d = 5.5); } }
module photo_post(dir = 1, explode = 0) {
    color(C_STRUCT_DK) linear_extrude(5) pb_foot_2d();
    translate([0, 0, 5 + 40 * explode]) tslot(20, 20, pb_post_h, 20, 6);
    translate([0, 0, 5 + pb_post_h + 40 * explode]) color(C_PRINT) rbox(24, 24, 6, 3);
    translate([dir * 10, 0, pb_z + 80 * explode]) rotate([0, 0, dir > 0 ? 0 : 180]) photo_head();
}

// part sheet view
rotor();
