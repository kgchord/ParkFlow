// =====================================================================
// ParkFlow (b) part: IP65 ENCLOSURE BASE + LID (PC, bought-in, machined)
//   base: inner floor bosses for mounting plate, 4 lid-screw bosses,
//         rim tongue; bottom wall gland + vent holes; +x side wall
//         heat-sink cut-out; 4 external mounting lugs
//   lid:  gasket groove matching the tongue, 4 screw pockets
// =====================================================================
include <edge_params.scad>
include <pf_common.scad>

C_ENC = [0.80, 0.82, 0.84];     // light grey PC (structure)
base_d = enc_d - enc_lid_d;      // base depth (140)

module shell(w, h, d, r, t, open_top = true) {
    difference() {
        rbox(w, h, d, r);
        translate([0, 0, t]) rbox(w - 2 * t, h - 2 * t, d, r - t);
    }
}

module enclosure_base() {
    color(C_ENC) difference() {
        union() {
            shell(enc_w, enc_h, base_d, enc_r, enc_wall);
            // rim tongue (mates with lid gasket)
            translate([0, 0, base_d]) linear_extrude(tongue_h) difference() {
                rrect(enc_w - enc_wall + tongue_w, enc_h - enc_wall + tongue_w, enc_r - enc_wall / 2);
                rrect(enc_w - enc_wall - tongue_w, enc_h - enc_wall - tongue_w, enc_r - enc_wall / 2 - 1);
            }
            // lid screw bosses (corners, full height)
            for (sx = [-1, 1], sy = [-1, 1]) translate([sx * (enc_w / 2 - lid_boss_in), sy * (enc_h / 2 - lid_boss_in), 0])
                cylinder(d = lid_boss_d, h = base_d);
            // back-plate bosses
            for (sx = [-1, 1], sy = [-1, 1]) translate([sx * bp_boss_dx / 2, sy * bp_boss_dy / 2, 0])
                cylinder(d = bp_boss_d, h = enc_wall + bp_boss_h);
            // external mounting lugs (back face)
            for (sx = [-1, 1], sy = [-1, 1]) translate([sx * mlug_x, sy * mlug_y, 0])
                hull() { translate([-sx * 15, 0, 0]) cylinder(d = mlug_w, h = 8); cylinder(d = mlug_w * 0.5 + 6, h = 8); }
        }
        // lid screw holes (M4 heat-set inserts)
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx * (enc_w / 2 - lid_boss_in), sy * (enc_h / 2 - lid_boss_in), base_d - 20])
            cylinder(d = 5.6, h = 30);
        // back-plate M4 inserts
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx * bp_boss_dx / 2, sy * bp_boss_dy / 2, 2]) cylinder(d = 5.6, h = 30);
        // lug holes M6
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx * mlug_x, sy * mlug_y, -1]) cylinder(d = 6.6, h = 20);
        // glands + vent through bottom wall (y = -enc_h/2)
        for (i = [0 : len(gland_x) - 1]) translate([gland_x[i], -enc_h / 2 - 1, base_d / 2]) rotate([-90, 0, 0]) cylinder(d = gland_m[i] + 0.5, h = enc_wall + 2);
        translate([vent_x, -enc_h / 2 - 1, base_d / 2]) rotate([-90, 0, 0]) cylinder(d = 12.5, h = enc_wall + 2);
        // heat-sink window on +x wall
        translate([enc_w / 2 - enc_wall - 1, hs_y - hs_cut_l / 2, base_d / 2 - hs_cut_w / 2]) cube([enc_wall + 2, hs_cut_l, hs_cut_w]);
        for (dy = [-1, 1], dz = [-1, 1]) translate([enc_w / 2 - enc_wall - 1, hs_y + dy * (hs_cut_l / 2 + 12), base_d / 2 + dz * (hs_cut_w / 2 + 12)])
            rotate([0, 90, 0]) cylinder(d = 4.5, h = enc_wall + 2);
    }
}

module enclosure_lid() {
    color([0.86, 0.88, 0.90, 1]) difference() {
        union() {
            // lid shell, open side facing -z
            translate([0, 0, enc_lid_d]) mirror([0, 0, 1]) shell(enc_w, enc_h, enc_lid_d, enc_r, enc_wall);
            for (sx = [-1, 1], sy = [-1, 1]) translate([sx * (enc_w / 2 - lid_boss_in), sy * (enc_h / 2 - lid_boss_in), 0])
                cylinder(d = lid_boss_d, h = enc_lid_d);
            // groove land (thickened rim)
            linear_extrude(groove_d + 2) difference() {
                rrect(enc_w, enc_h, enc_r);
                rrect(enc_w - 2 * enc_wall - 6, enc_h - 2 * enc_wall - 6, enc_r - enc_wall);
            }
        }
        // gasket groove
        translate([0, 0, -0.01]) linear_extrude(groove_d) difference() {
            rrect(enc_w - enc_wall + groove_w, enc_h - enc_wall + groove_w, enc_r - enc_wall / 2);
            rrect(enc_w - enc_wall - groove_w, enc_h - enc_wall - groove_w, enc_r - enc_wall / 2 - 1);
        }
        // screw pockets (counterbore from outside)
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx * (enc_w / 2 - lid_boss_in), sy * (enc_h / 2 - lid_boss_in), -1]) {
            cylinder(d = 4.5, h = enc_lid_d + 2);
            translate([0, 0, enc_lid_d - 8]) cylinder(d = 9, h = 10);
        }
    }
    // gasket cord
    color(C_RUBBER) translate([0, 0, groove_d - gasket_d * 0.8]) linear_extrude(gasket_d * 0.8) difference() {
        rrect(enc_w - enc_wall + gasket_d / 2 + 0.4, enc_h - enc_wall + gasket_d / 2 + 0.4, enc_r - enc_wall / 2);
        rrect(enc_w - enc_wall - gasket_d / 2 - 0.4, enc_h - enc_wall - gasket_d / 2 - 0.4, enc_r - enc_wall / 2 - 1);
    }
    // ParkFlow label plate
    color(C_STRUCT) translate([0, enc_h / 2 - 50, enc_lid_d]) rbox(120, 30, 0.8, 3);
}

enclosure_base();
translate([enc_w + 40, 0, 0]) enclosure_lid();
