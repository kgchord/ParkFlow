// =====================================================================
// ParkFlow ASSEMBLY (c): DEMO BOOM BARRIER
//   24 V worm gearmotor -> jaw coupling -> 20 mm stub shaft on 2 flange
//   bearings -> keyed hub -> breakaway carrier (M8 hinge + 5 mm 6061
//   shear pin) -> 1.2 m 60x30x1.5 boom; counterweight tail (7 x MS
//   plates @200 mm); limit flag + 2 inductive sensors (0/90 deg);
//   through-beam photo-electric pair on 20x20 posts, beam at 300 mm.
// Overrides: -D explode=1 | -D section=1 | -D boom_angle=0..90
// =====================================================================
include <barrier_params.scad>
include <pf_bought.scad>
use <barrier_parts.scad>

explode = 0;
section = 0;      // 1 = vertical cut on the y-z plane through the shaft axis (x<0 half removed): drive line in elevation
with_ground = 1;

hy_front_ = -hs_y / 2;
hub_y_    = hy_front_ - panel_t - hub_gap - hub_t / 2;

module barrier(explode = 0, angle = 0, ground = -1, pb_span = -1) {
    ex = explode;
    pbx2 = pb_span > 0 ? pb_span : pb_x2;
    if ((ground < 0 && with_ground == 1) || ground == 1) color(C_GROUND) translate([-400, -700, -40]) cube([2200, 1300, 40]);
    // base plate + anchors
    color(C_STRUCT_DK) linear_extrude(hsg_bp_t) housing_base_plate_2d();
    for (sx = [-1, 1], sy = [-1, 1]) translate([sx * (hs_x / 2 + hsg_bp_mx / 2 - 2), sy * (hs_y / 2 + hsg_bp_mx / 2 - 2), hsg_bp_t]) nut(anchor_d);
    // frame & skins
    translate([0, 0, 0.0]) housing_frame();
    if (ex == 0) housing_skins();
    else translate([-hs_x * 0 + 0, 0, 0]) {
        // exploded: skins pushed out radially / roof up
        translate([0, 450, 0]) intersection() { housing_skins(); translate([-500, hs_y / 2 - 5, 0]) cube([1000, 50, 2000]); }
        translate([-420, 0, 0]) intersection() { housing_skins(); translate([-hs_x / 2 - 30, -hs_y / 2 + 1, 0]) cube([30, hs_y - 2, hsg_bp_t + hs_z]); }
        translate([0, 0, 500]) intersection() { housing_skins(); translate([-500, -500, hsg_bp_t + hs_z - 1]) cube([1000, 1000, 100]); }
        translate([0, -900, 0]) intersection() { housing_skins(); translate([-500, -hs_y / 2 - 5, 0]) cube([1000, 8, hsg_bp_t + hs_z - 1]); }
    }
    // drive train
    translate([0, -ex * 0, 0]) drive_train(ex);
    // rotor
    translate([0, hub_y_ - 1050 * ex, shaft_z]) rotate([90, 0, 0]) {
        rotate([0, 0, angle]) rotor(ex);
        limit_sensors();
    }
    // photo-beam pair
    by = hub_y_ + pb_dy;
    translate([hs_x / 2 + 60, by, 0]) photo_post(1, ex);
    translate([pbx2, by, 0]) photo_post(-1, ex);
    color(C_BEAM) translate([hs_x / 2 + 130, by, pb_z]) rotate([0, 90, 0]) cylinder(d = 3, h = pbx2 - hs_x / 2 - 200);
}

// layout entry: no ground slab, photo-beam spanning the full lane
module barrier_core(angle = 0, pb_span = 3600) { barrier(0, angle, 0, pb_span); }

if (section == 1) {
    difference() { barrier(explode, boom_angle); color(C_CUT) translate([-3000, -3000, -100]) cube([3000, 6000, 3000]); }
} else barrier(explode, boom_angle);
