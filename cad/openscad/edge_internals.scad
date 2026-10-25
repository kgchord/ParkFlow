// =====================================================================
// ParkFlow (b) parts: EDGE NODE INTERNALS
//   * mounting plate (3 mm 5052-H32, laser cut)          -> DXF
//   * Pi tray (FDM ASA, M2.5 heat-set bosses)              -> STL
//   * heat spreader (5 mm 6061-T6 plate + 10x20 bar)       -> DXF (plate)
//   * external finned heat sink (bought 200x150 extrusion, cut + drilled)
//   * sun hood (2 mm 5052, bent)                           -> DXF (flat)
//   * populated layout: DIN rail + MCB/SPD/fuse, LRS-150-24, PoE switch,
//     Pi 5 + AI HAT+, Lane Controller PCB on M3 standoffs, buck module
// Plate-local frame: x,y in plate, z normal (component side).
// =====================================================================
include <edge_params.scad>
include <pf_bought.scad>

// ---------- mounting plate 2D --------------------------------------
module mount_plate_2d() {
    difference() {
        rrect(mp_w, mp_h, 6);
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx * bp_boss_dx / 2, sy * bp_boss_dy / 2]) circle(d = 4.5);    // M4 to bosses
        // DIN rail M4 holes
        for (x = [-100, 0, 100]) translate([x, din_y]) circle(d = 4.5);
        // SMPS M4 (LRS-150 base: 4x M4, ASSUMED 150 x 50 pattern - check datasheet)
        for (x = [-75, 75], y = [-25, 25]) translate([smps_x + x, smps_y + y]) circle(d = 4.5);
        // Pi tray 4x M3
        for (x = [-45, 45], y = [-32, 32]) translate([pi_x + x, pi_y + y]) circle(d = 3.4);
        // Lane controller 4x M3 standoffs
        for (x = [-1, 1], y = [-1, 1]) translate([lc_x + x * (lc_l / 2 - lc_hole_in), lc_y + y * (lc_w / 2 - lc_hole_in)]) circle(d = 3.4);
        // buck module 2x M3
        for (x = [-20, 20]) translate([buck_x, buck_y + x]) circle(d = 3.4);
        // cable-tie slots
        for (x = [-100 : 50 : 100]) translate([x, -170]) square([4, 10], center = true);
        for (y = [-60, 40]) translate([-120, y]) square([10, 4], center = true);
    }
}
module mount_plate() { color(C_STRUCT) linear_extrude(mp_t) mount_plate_2d(); }

// ---------- printed Pi tray (ASA) ----------------------------------
module pi_tray() {
    color(C_PRINT) difference() {
        union() {
            rbox(100, 75, pitray_t, 4);
            for (x = [0, pi_hole_dx()], y = [0, pi_hole_dy()]) translate([-85 / 2 + 3.5 + x, -56 / 2 + 3.5 + y, 0]) cylinder(d = 6.5, h = pi_standoff);
            // edge rails for stiffness
            for (s = [-1, 1]) translate([-50, s * 37.5 - (s > 0 ? 2 : 0), 0]) cube([100, 2, 6]);
        }
        for (x = [0, pi_hole_dx()], y = [0, pi_hole_dy()]) translate([-85 / 2 + 3.5 + x, -56 / 2 + 3.5 + y, 1.5]) cylinder(d = 3.6, h = 20);   // M2.5 heat-set
        for (x = [-45, 45], y = [-32, 32]) translate([x, y, -1]) { cylinder(d = 3.4, h = 10); translate([0, 0, pitray_t - 1.4]) cylinder(d = 6.2, h = 10); }
        translate([0, 0, -1]) rbox(40, 30, 10, 3);  // airflow window
    }
}
function pi_hole_dx() = 58;
function pi_hole_dy() = 49;

// ---------- heat spreader + external sink ---------------------------
// spreader sits on Hailo-8 + Pi SoC via 1.5 mm thermal pads; bar runs
// along +x to the side wall where it clamps to the heat-sink base.
module heat_spreader_2d() {
    difference() {
        union() {
            translate([-spr_l / 2, -spr_w / 2]) square([spr_l, spr_w]);
        }
        for (x = [-1, 1], y = [-1, 1]) translate([x * 29, y * 24.5]) circle(d = 2.9);   // M2.5 on Pi pattern
    }
}
module heat_spreader(bar_len = 60) {
    color([0.78, 0.80, 0.83]) {
        linear_extrude(spr_t) heat_spreader_2d();
        translate([spr_l / 2 - 5, -spr_bar_w / 2, 0]) cube([bar_len, spr_bar_w, spr_bar_t]);
    }
    color([0.55, 0.65, 0.95]) translate([-11, -11, -1.5]) cube([22, 22, 1.5]);   // thermal pad
}
module heat_sink() {
    // base in y-z plane at x=0, fins grow +x
    color([0.62, 0.64, 0.67]) {
        translate([0, -hs_base_l / 2, -hs_base_w / 2]) cube([hs_base_t, hs_base_l, hs_base_w]);
        for (i = [0 : hs_fin_n - 1]) translate([hs_base_t, -hs_base_l / 2, -hs_base_w / 2 + 2 + i * (hs_base_w - 4 - hs_fin_t) / (hs_fin_n - 1)])
            cube([hs_fin_h, hs_base_l, hs_fin_t]);
    }
    color(C_RUBBER) translate([-1.5, -hs_cut_l / 2 - 8, -hs_cut_w / 2 - 8]) difference() {   // window gasket
        cube([1.5, hs_cut_l + 16, hs_cut_w + 16]);
        translate([-1, 4, 4]) cube([4, hs_cut_l + 8, hs_cut_w + 8]);
    }
}

// ---------- sun hood (2 mm 5052, 3 bends) --------------------------
module sun_hood() {
    w = enc_w + 2 * (hood_gap + hood_t);
    color(C_STRUCT) {
        // top canopy (in x-z plane above enclosure)
        translate([-w / 2, enc_h / 2 + hood_gap, -10]) cube([w, hood_t, enc_d + hood_front + 10]);
        // sides (half-height)
        for (s = [-1, 1]) translate([s * (w / 2 - hood_t / 2) - hood_t / 2, enc_h / 2 + hood_gap - 220, -10]) cube([hood_t, 220, enc_d + 20]);
    }
}

// ---------- populated mounting plate --------------------------------
module internals(explode = 0) {
    ex = explode;
    mount_plate();
    z0 = mp_t;
    // DIN rail + devices
    translate([-din_len / 2, din_y, z0 + 20 * ex]) din_rail(din_len);
    // MCB (2 mod), SPD (2 mod), fuse terminals (4x1), terminal blocks
    devs = [[-115, 2, [0.95, 0.95, 0.93]], [-78, 2, [0.85, 0.30, 0.25]], [-40, 1, [0.25, 0.25, 0.27]], [-20, 1, [0.25, 0.25, 0.27]],
            [0, 1, [0.25, 0.25, 0.27]], [20, 1, [0.25, 0.25, 0.27]], [40, 1, [0.15, 0.35, 0.80]], [55, 1, [0.15, 0.35, 0.80]], [70, 1, [0.6, 0.6, 0.6]]];
    for (d = devs) translate([d[0], din_y, z0 + 7.5 + 60 * ex]) rotate([0, 0, 0]) translate([0, 0, 0]) din_device(d[1], d[2], 70);
    // PoE switch on DIN rail, right end
    translate([105, din_y, z0 + 7.5 + 60 * ex]) rotate([0, 0, 0]) poe_switch();
    // SMPS
    translate([smps_x, smps_y, z0 + 50 * ex]) lrs150();
    // buck 5 V 5 A
    color(C_ELEC) translate([buck_x - 15, buck_y - 30, z0 + 50 * ex]) cube([30, 60, 18]);
    // Pi tray + Pi stack
    translate([pi_x, pi_y, z0 + 40 * ex]) {
        pi_tray();
        translate([0, 0, pi_standoff + 50 * ex]) pi_stack();
    }
    // spreader over AI HAT: pi_standoff + 1.6 + 16 + 1.6 + 3 + pad
    translate([pi_x + 6, pi_y, z0 + pi_standoff + 1.6 + 16 + 1.6 + 4.5 + 120 * ex]) heat_spreader(enc_w / 2 - enc_wall - (pi_x + 6) - spr_l / 2 + 5 - (enc_w - mp_w) / 2 + 20);
    // Lane controller on M3 standoffs
    translate([lc_x, lc_y, z0 + 40 * ex]) {
        color([0.85, 0.70, 0.30]) for (x = [-1, 1], y = [-1, 1]) translate([x * (lc_l / 2 - lc_hole_in), y * (lc_w / 2 - lc_hole_in), 0]) cylinder(d = 5.5, h = lc_standoff, $fn = 6);
        translate([0, 0, lc_standoff + 50 * ex]) lane_controller_pcb();
    }
    // wiring trunking (25x25 slotted) across bottom
    color([0.60, 0.62, 0.64]) translate([-mp_w / 2 + 10, -170 + 8, z0]) cube([mp_w - 20, 20, 25]);
}

mount_plate();
translate([0, 0, 0]) internals();
