// =====================================================================
// ParkFlow (a) part: BASE PLATE + SOCKET + GUSSET WELDMENT
// Material: MS IS 2062 E250 (S275 equivalent), laser-cut 16 mm plate,
// 6 mm socket cheeks and gussets, MIG fillet welds 6 mm leg, hot-dip
// galvanised or zinc-primer + PU paint.
// Open this file directly to view the part; use<> it from assemblies.
// 2D modules (*_2d) are the laser-cut profiles exported to DXF.
// =====================================================================
include <gantry_params.scad>
include <pf_common.scad>

sock_in   = pole_w + 2 * sock_clear;              // socket inner span (81)
sock_long = sock_in + 2 * sock_t;                 // long cheek length (93)

// ---------- 2D laser-cut profiles ----------------------------------
module base_plate_2d() {
    difference() {
        rrect(bp_w, bp_w, bp_corner_r);
        for (a = [45 : 90 : 315]) rotate(a) translate([bp_pcd / 2, 0]) circle(d = bp_anchor_hole);
        circle(d = bp_centre_hole);
        // 4 grout/vent slots between gussets
        for (a = [45 : 90 : 315]) rotate(a) translate([bp_pcd / 2 - 40, 0]) square([16, 8], center = true);
    }
}
// long socket cheek (on +/-y faces): length sock_long, height sock_h
module socket_cheek_long_2d() {
    difference() {
        translate([-sock_long / 2, 0]) square([sock_long, sock_h]);
        translate([0, sock_bolt_z1]) circle(d = sock_bolt_d + 1);
        translate([0, sock_h]) scale([1, 0.5]) circle(d = 30);   // top relief / drain notch for weld start
    }
}
// short socket cheek (on +/-x faces): length sock_in
module socket_cheek_short_2d() {
    difference() {
        translate([-sock_in / 2, 0]) square([sock_in, sock_h]);
        translate([0, sock_bolt_z2]) circle(d = sock_bolt_d + 1);
    }
}
// gusset: u = radial (from socket face), v = up
module gusset_2d() {
    polygon([[0, gus_chamfer], [gus_chamfer, 0], [gus_l, 0], [gus_l, gus_tip],
             [gus_tip, gus_h], [0, gus_h]]);
}

// ---------- 3D weldment --------------------------------------------
module base_weldment(show_bolts = true) {
    color(C_STRUCT_DK) {
        linear_extrude(bp_t) base_plate_2d();
        // long cheeks on +/-y
        for (s = [-1, 1]) translate([0, s * (sock_in / 2 + sock_t / 2), bp_t])
            rotate([90, 0, 0]) translate([0, 0, -sock_t / 2]) linear_extrude(sock_t) socket_cheek_long_2d();
        // short cheeks on +/-x
        for (s = [-1, 1]) translate([s * (sock_in / 2 + sock_t / 2), 0, bp_t])
            rotate([90, 0, 90]) translate([0, 0, -sock_t / 2]) linear_extrude(sock_t) socket_cheek_short_2d();
        // gussets on face centre-lines
        for (a = [0 : 360 / gus_n : 359]) rotate(a)
            translate([sock_long / 2, 0, bp_t])
                rotate([90, 0, 0]) translate([0, 0, -gus_t / 2]) linear_extrude(gus_t) gusset_2d();
    }
    if (show_bolts) {
        // cross bolts M10 through socket + pole
        color(C_HW) {
            translate([0, -sock_long / 2 - 8, bp_t + sock_bolt_z1]) rotate([-90, 0, 0]) cylinder(d = sock_bolt_d, h = sock_long + 16);
            translate([-sock_long / 2 - 8, 0, bp_t + sock_bolt_z2]) rotate([0, 90, 0]) cylinder(d = sock_bolt_d, h = sock_long + 16);
        }
    }
}

// anchor set (M12 chemical anchor stud, levelling nut, washer, top nut)
module anchors() {
    for (a = [45 : 90 : 315]) rotate(a) translate([bp_pcd / 2, 0, 0]) {
        color(C_HW) translate([0, 0, -grout_gap - 120]) cylinder(d = bp_anchor_d, h = 120 + grout_gap + bp_t + 22);
        translate([0, 0, -10]) nut(bp_anchor_d);
        translate([0, 0, bp_t]) washer(bp_anchor_d);
        translate([0, 0, bp_t + 2.4]) nut(bp_anchor_d);
    }
}

base_weldment();
