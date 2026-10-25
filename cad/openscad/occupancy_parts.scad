// =====================================================================
// ParkFlow (d) parts: OCCUPANCY NODE - printed base, cover, diffuser.
// Print orientation (for STL export): base: back plate down; cover: rim
// down (dome up) - both support-free; diffuser flat.
// Local frame: z up = away from ceiling (base back plate on z=0).
// =====================================================================
include <occupancy_params.scad>
include <pf_bought.scad>

module oc_base() {
    ri = oc_d / 2 - oc_wall;
    color(C_PRINT) difference() {
        union() {
            cylinder(d = oc_d, h = oc_base_h, $fn = 96);
        }
        translate([0, 0, oc_floor]) cylinder(r = ri, h = oc_base_h, $fn = 96);
        // ceiling screw slots (keyhole)
        for (s = [-1, 1]) translate([s * oc_screw_pitch / 2, 0, -1]) {
            cylinder(d = oc_screw_d, h = 10);
            translate([0, 0, oc_floor - 1.2]) cylinder(d = 10, h = 2);
        }
        translate([0, 18, -1]) cylinder(d = oc_cable_d, h = 10);
        // snap windows (hooks on the cover catch these)
        for (i = [0 : snap_n - 1]) rotate(90 + i * 360 / snap_n)
            translate([oc_d / 2 - oc_wall - 1, -snap_w / 2 - 0.5, oc_base_h - lip_h - 3.5]) cube([oc_wall + 2, snap_w + 1, 2.2]);
    }
    // ESP32-C3 cradle + standoffs
    color(C_PRINT) for (x = [-20, 20]) translate([x, -12, oc_floor]) difference() { cylinder(d = 6, h = esp_standoff); cylinder(d = 2.5, h = 20); }
    // anti-rotation key
    color(C_PRINT) translate([oc_d / 2 - oc_wall - 2, -2, oc_floor]) cube([2.1, 4, oc_base_h - oc_floor - 2]);
}

module oc_cover() {
    ri = oc_d / 2 - oc_wall;
    sp_o = ri - fit_clear;                 // spigot OD radius
    color(C_PRINT) difference() {
        union() {
            // outer skirt + shallow dome
            cylinder(d = oc_d, h = oc_cover_h - 8, $fn = 96);
            translate([0, 0, oc_cover_h - 8]) cylinder(d1 = oc_d, d2 = oc_d - 16, h = 8, $fn = 96);
            // spigot into base
            translate([0, 0, -lip_h]) cylinder(r = sp_o, h = lip_h + 0.01, $fn = 96);
        }
        // hollow
        translate([0, 0, -lip_h - 1]) cylinder(r = sp_o - oc_wall, h = oc_cover_h - 2 + lip_h, $fn = 96);
        // probe bore
        cylinder(d = probe_d + 0.6, h = 60);
        // LED ring window (annulus), filled by the diffuser
        translate([0, 0, oc_cover_h - 3]) difference() { cylinder(d = ring_od + 4, h = 10); translate([0, 0, -1]) cylinder(d = ring_id - 2, h = 12); }
        // snap hook relief slots around each hook
        for (i = [0 : snap_n - 1]) rotate(90 + i * 360 / snap_n)
            for (s = [-1, 1]) translate([sp_o - oc_wall - 1, s * (snap_w / 2 + 0.6) - 0.6, -lip_h - 1 - snap_l + lip_h + 1]) cube([oc_wall + 2, 1.2, snap_l]);
    }
    // snap hooks: cantilever extending from spigot down, barb outward
    color(C_PRINT) for (i = [0 : snap_n - 1]) rotate(90 + i * 360 / snap_n) {
        translate([sp_o - snap_t, -snap_w / 2, -lip_h - snap_l + lip_h]) cube([snap_t, snap_w, snap_l]);
        translate([sp_o, -snap_w / 2, -lip_h + 0.5 - 2]) hull() { cube([0.01, snap_w, 2.2]); translate([0, 0, 2.2]) cube([snap_lip + 0.01, snap_w, 0.01]); }
    }
    // probe clamp boss (internal) + M3 pinch
    color(C_PRINT) translate([0, 0, oc_cover_h - 18]) difference() {
        cylinder(d = probe_d + 8, h = 12);
        translate([0, 0, -1]) cylinder(d = probe_d + 0.4, h = 20);
        translate([-1, 0, -1]) cube([2, probe_d, 20]);
    }
    // LED ring seat
    color(C_PRINT) translate([0, 0, oc_cover_h - 5.5]) difference() { cylinder(d = ring_od + 4, h = 1.5); translate([0, 0, -1]) cylinder(d = ring_od - 2, h = 4); }
}

module oc_diffuser() {
    color([0.97, 0.97, 0.95, 0.85]) difference() {
        cylinder(d = ring_od + 3.6, h = diffuser_t + 1.8);
        translate([0, 0, -1]) cylinder(d = ring_id - 1.6, h = 10);
    }
}

oc_base();
translate([oc_d + 20, 0, lip_h]) oc_cover();
translate([2 * oc_d + 30, 0, 0]) oc_diffuser();
