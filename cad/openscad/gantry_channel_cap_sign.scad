// =====================================================================
// ParkFlow (a) parts: CABLE CHANNEL, CABLE BOOT (FDM ASA), POLE CAP
// (FDM ASA), P10 SIGN BRACKET (3 mm 5052), EDGE NODE POLE BRACKET
// (3 mm MS flat bar) - all small pole furniture.
// =====================================================================
include <gantry_params.scad>
include <pf_bought.scad>

// ---------- cable channel (bought 40x25 PVC/ASA trunking, cut to length)
module cable_channel() {
    color(C_PRINT) translate([-pole_w / 2 - duct_d, -duct_w / 2, duct_z0]) difference() {
        cube([duct_d, duct_w, duct_z1 - duct_z0]);
        translate([duct_t, duct_t, -1]) cube([duct_d - 2 * duct_t, duct_w - 2 * duct_t, duct_z1 - duct_z0 + 2]);
    }
    // snap cover strip
    color(C_PRINT * 0.95) translate([-pole_w / 2 - duct_d - 1.5, -duct_w / 2 - 1, duct_z0]) cube([1.5, duct_w + 2, duct_z1 - duct_z0]);
}

// ---------- printed boot: conduit (vertical, from plinth) -> channel ---
module cable_boot() {
    color(C_PRINT) difference() {
        hull() {
            translate([-pole_w / 2 - duct_d - 1.5, -duct_w / 2 - 3, duct_z0 - boot_h]) cube([duct_d + 1.5, duct_w + 6, boot_h]);
            translate([-pole_w / 2 - duct_d / 2, 0, bp_t + 10]) cylinder(d = conduit_d + 8, h = 1);
        }
        translate([-pole_w / 2 - duct_d + 2, -duct_w / 2 + 2, duct_z0 - boot_h + 15]) cube([duct_d - 4, duct_w - 4, boot_h]);
        translate([-pole_w / 2 - duct_d / 2, 0, bp_t]) cylinder(d = conduit_d + 0.6, h = 40);
        translate([-pole_w / 2 - 2, -duct_w / 2 - 10, 0]) cube([10, duct_w + 20, 400]);   // flat back on pole
    }
    color(C_RUBBER) translate([-pole_w / 2 - duct_d / 2, 0, -grout_gap - 40]) cylinder(d = conduit_d, h = bp_t + 40 + grout_gap + 20);
}
// STL-ready boot (printed lying on its back face)
module cable_boot_print() { translate([pole_w / 2, 0, -duct_z0 + boot_h]) cable_boot_body_only(); }
module cable_boot_body_only() {
    color(C_PRINT) difference() {
        hull() {
            translate([-pole_w / 2 - duct_d - 1.5, -duct_w / 2 - 3, duct_z0 - boot_h]) cube([duct_d + 1.5, duct_w + 6, boot_h]);
            translate([-pole_w / 2 - duct_d / 2, 0, bp_t + 10]) cylinder(d = conduit_d + 8, h = 1);
        }
        translate([-pole_w / 2 - duct_d + 2, -duct_w / 2 + 2, duct_z0 - boot_h + 15]) cube([duct_d - 4, duct_w - 4, boot_h]);
        translate([-pole_w / 2 - duct_d / 2, 0, bp_t]) cylinder(d = conduit_d + 0.6, h = 40);
        translate([-pole_w / 2 - 2, -duct_w / 2 - 10, 0]) cube([10, duct_w + 20, 400]);
    }
}

// ---------- pole cap (ASA, prints upside-down without support) --------
module pole_cap() {
    ci = pole_w + 2 * cap_clear;
    color(C_PRINT) difference() {
        union() {
            rbox(ci + 2 * cap_wall, ci + 2 * cap_wall, cap_h, 3);
            translate([0, 0, cap_h]) linear_extrude(8, scale = 0.6) rrect(ci + 2 * cap_wall, ci + 2 * cap_wall, 3);   // drip slope
        }
        translate([0, 0, -1]) rbox(ci, ci, cap_h + 1 - 2.4, 1.5);
    }
    // 4 internal clip ribs that engage the 10 mm slots
    color(C_PRINT) for (a = [0 : 90 : 270]) rotate(a) translate([ci / 2 - 3, -4.5, 2]) cube([3.2, 9, cap_h - 4.4]);
}

// ---------- P10 sign bracket: 3 mm 5052, Z-bent; flat = 200 x 80 -----
sign_br_l = 200; sign_br_w = 80;
module sign_bracket_2d() {
    difference() {
        rrect(sign_br_l, sign_br_w, 5);
        for (y = [-20, 20]) translate([-sign_br_l / 2 + 25, y]) circle(d = 8.5);                // M8 T-nuts in pole slots (40 pitch)
        for (y = [-25, 25]) translate([sign_br_l / 2 - 20, y]) hull() { translate([-4, 0]) circle(d = 6.6); translate([4, 0]) circle(d = 6.6); }  // M6 to cabinet
    }
}
module sign_assy(explode = 0) {
    // cabinet on -y side of pole, LED face toward -y
    for (s = [-1, 1]) color(C_STRUCT)
        translate([0, -pole_d / 2 - sign_br_l / 2 + 25, sign_z + s * 70]) rotate([0, 0, 90]) translate([0, 0, -sign_br_t / 2])
            linear_extrude(sign_br_t) rotate(180) sign_bracket_2d();
    translate([0, -pole_d / 2 - sign_br_l + 50 - 30 - 120 * explode, sign_z]) rotate([90, 0, 0]) p10_cabinet(sign_cab_w, sign_cab_h, sign_cab_d);
}

// ---------- Edge Node pole bracket: 3 mm MS flat bar 340 x 50 ---------
edge_br_l = 340; edge_br_w = 50; edge_br_t = 3; edge_lug_pitch = 300;
module edge_bracket_2d() {
    difference() {
        rrect(edge_br_l, edge_br_w, 4);
        for (x = [-20, 20]) translate([x, 0]) circle(d = 8.5);                        // M8 T-nuts, pole slots
        for (x = [-1, 1]) translate([x * edge_lug_pitch / 2, 0]) hull() { translate([0, -5]) circle(d = 6.6); translate([0, 5]) circle(d = 6.6); }
    }
}

// part view
pole_cap();
translate([150, 0, 0]) linear_extrude(3) sign_bracket_2d();
translate([0, 150, 0]) linear_extrude(3) edge_bracket_2d();
