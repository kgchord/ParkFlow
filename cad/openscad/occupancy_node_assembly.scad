// =====================================================================
// ParkFlow ASSEMBLY (d): CEILING OCCUPANCY SENSOR NODE
// Shown as installed: ceiling slab above, housing hanging, sensor and
// LED ring pointing down at the bay.  -D explode=1 | -D section=1
// =====================================================================
include <occupancy_params.scad>
include <pf_bought.scad>
use <occupancy_parts.scad>

explode   = 0;
section   = 0;      // 1 = cut on the x-z plane (front half removed)
show_slab = 1;
show_beam = 0;      // 60 deg ultrasonic cone (short) for context

module oc_assy(explode = 0) {
    ex = explode;
    // everything modelled "base on z=0, growing +z"; flipped below
    oc_base();
    translate([0, -12, oc_floor + esp_standoff + 45 * ex]) esp32c3_board();
    // cable grommet
    color(C_RUBBER) translate([0, 18, -4 - 30 * ex]) cylinder(d = 12, h = 6);
    // cover
    translate([0, 0, oc_base_h + 100 * ex]) {
        oc_cover();
        // A02YYUW: flange (body) inside, probe protruding out through bore (+z here)
        translate([0, 0, oc_cover_h - a02_probe_l + 2 - 70 * ex]) mirror([0, 0, 1]) a02yyuw();   // probe points away from ceiling, 2 mm proud of dome
        // LED ring on seat
        translate([0, 0, oc_cover_h - 4 + 20 * ex]) ws2812_ring(ring_od, ring_id);
        translate([0, 0, oc_cover_h - 3 + 50 * ex]) oc_diffuser();
    }
    // M5 screws
    for (s = [-1, 1]) translate([s * oc_screw_pitch / 2, 0, oc_floor + 0.5 + 60 * ex]) rotate([180, 0, 0]) bolt(5, 35, "csk");
}

module oc_scene() {
    if (show_slab) color(C_GROUND) translate([-90, -90, 0]) cube([180, 180, 12]);
    // flip: housing hangs below the ceiling (z<0)
    rotate([180, 0, 0]) oc_assy(explode);
    if (show_beam) color(C_ZONE_CAM) translate([0, 0, -oc_base_h - oc_cover_h - 8]) mirror([0, 0, 1]) cylinder(r1 = 17, r2 = 17 + 300 * tan(30), h = 300);
}

if (section == 1) difference() { oc_scene(); color(C_CUT) translate([-200, -400, -400]) cube([400, 400, 800]); }
else oc_scene();
