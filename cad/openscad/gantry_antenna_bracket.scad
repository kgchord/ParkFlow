// =====================================================================
// ParkFlow (a) part: RFID ANTENNA ARM + TILT BRACKET
//   * arm: 40x40 Al T-slot, ant_arm_len, fixed to pole +x face with 2x
//     cast corner brackets + M8 T-nuts
//   * yoke: 5 mm 5052-H32, laser cut + 2 x 90 deg press-brake bends
//     (R = t), bolted to arm underside with 2x M6 T-nuts in the slot
//   * tilt plate: 5 mm 5052-H32, 2 x 90 deg bends (ears); M8 shoulder
//     pivots; M6 lock bolt in 0-30 deg arc slot (graduated in 5 deg)
// Local frame of yoke/tilt: origin on pivot axis, x across lane.
// =====================================================================
include <gantry_params.scad>
include <pf_bought.scad>

// derived
web_top_above_pivot = pivot_drop - ant_arm_w / 2;     // yoke web top (outer) above pivot (160)
cheek_r      = 45;                                    // cheek bottom radius around (0,-30)
cheek_bot_c  = -30;                                   // centre of bottom radius below pivot
cheek_x      = yoke_w / 2 - yoke_t;                   // cheek inner face x (135)
tp_off       = 40;                                    // tilt plate rear face offset in front of pivot (-y)
ear_d        = 60;                                    // ear depth (y)
ear_half_h   = 50;                                    // ear half height
bend_k       = 0.40;                                  // K-factor, 5052-H32, R = t
bend_allow   = PI / 2 * (yoke_bend_r + bend_k * yoke_t);           // BA = 11.0 mm
bend_deduct  = 2 * (yoke_bend_r + yoke_t) - bend_allow;            // BD = 9.0 mm
web_hole_pitch = 160;                                  // M6 T-nut holes along web

// ---------- 2D profiles ------------------------------------------------
// cheek profile in (y, z) about pivot; z up
module cheek_2d() {
    difference() {
        hull() {
            translate([-yoke_web_d / 2, 0]) square([yoke_web_d, web_top_above_pivot]);
            translate([0, cheek_bot_c]) circle(r = cheek_r);
        }
        circle(d = pivot_d + 0.5);
        // tilt-lock arc slot, angle 0..tilt_max, radius lock_r, below pivot
        for (a = [tilt_min : 1 : tilt_max - 1]) hull() {
            rotate(-90 + a) translate([lock_r, 0]) circle(d = lock_slot_w, $fn = 16);
            rotate(-90 + a + 1) translate([lock_r, 0]) circle(d = lock_slot_w, $fn = 16);
        }
        // tilt scale notches every 5 deg (laser-etched marks)
        for (a = [tilt_min : 5 : tilt_max]) rotate(-90 + a) translate([lock_r + 9, 0]) square([5, 0.8], center = true);
    }
}
// flat pattern of yoke: strip along x with cheeks unfolded at both ends
module yoke_flat_2d() {
    web_flat = yoke_w - 2 * (yoke_t + yoke_bend_r);       // flat web between bends
    leg = web_top_above_pivot - yoke_t - yoke_bend_r;      // straight cheek from bend tangent to pivot
    difference() {
        union() {
            translate([-web_flat / 2, -yoke_web_d / 2]) square([web_flat, yoke_web_d]);
            for (s = [-1, 1]) {
                // bend zone
                translate([s * (web_flat / 2 + bend_allow / 2), 0]) square([bend_allow + 0.01, yoke_web_d], center = true);
                // cheek, unfolded: z -> outward x
                translate([s * (web_flat / 2 + bend_allow + leg), 0]) rotate(s > 0 ? 90 : -90)
                    intersection() {
                        cheek_2d();
                        translate([-100, -200]) square([200, 200 + leg]);
                    }
            }
        }
        for (s = [-1, 1]) translate([s * web_hole_pitch / 2, 0]) circle(d = 6.6);
    }
}
// tilt plate front face (x, z)
module tilt_plate_face_2d() {
    difference() {
        rrect(tp_w, tp_h, 8);
        for (x = [-1, 1], z = [-1, 1]) translate([x * reader_hole_pitch / 2, z * reader_hole_pitch / 2]) circle(d = 6.6);
        circle(d = 30);                                                   // connector pass-through
        for (x = [-1, 1]) translate([x * 80, 0]) rrect(30, 120, 6);       // lightening slots
    }
}
// ear profile in (y, z) about pivot
module ear_2d() {
    difference() {
        hull() {
            translate([-tp_off - yoke_t, -ear_half_h]) square([0.1, 2 * ear_half_h]);
            circle(r = 16);
            translate([0, -lock_r]) circle(r = 10);
        }
        circle(d = pivot_d + 0.3);
        translate([0, -lock_r]) circle(d = 6.6);
    }
}
module tilt_plate_flat_2d() {
    face_flat = tp_w - 2 * (yoke_t + yoke_bend_r);
    union() {
        difference() { tilt_plate_face_2d(); for (s = [-1, 1]) translate([s * (tp_w / 2), 0]) square([2 * (yoke_t + yoke_bend_r), tp_h + 2], center = true); }
        for (s = [-1, 1]) {
            translate([s * (face_flat / 2 + bend_allow / 2), 0]) square([bend_allow + 0.01, 2 * ear_half_h], center = true);
            translate([s * (face_flat / 2 + bend_allow - (yoke_t + yoke_bend_r) + tp_off + yoke_t), 0])
                mirror([s < 0 ? 1 : 0, 0]) ear_2d();
        }
    }
}

// ---------- 3D parts -------------------------------------------------
module yoke() {
    color(C_STRUCT) {
        // web (top)
        difference() {
            translate([-yoke_w / 2 + yoke_t + yoke_bend_r, -yoke_web_d / 2, web_top_above_pivot - yoke_t])
                cube([yoke_w - 2 * (yoke_t + yoke_bend_r), yoke_web_d, yoke_t]);
            for (s = [-1, 1]) translate([s * web_hole_pitch / 2, 0, 0]) cylinder(d = 6.6, h = 500);
        }
        for (s = [-1, 1]) {
            // bend (quarter tube)
            translate([s * (yoke_w / 2 - yoke_t - yoke_bend_r), 0, web_top_above_pivot - yoke_t - yoke_bend_r])
                rotate([90, 0, 0]) translate([0, 0, -yoke_web_d / 2])
                    intersection() {
                        difference() { cylinder(r = yoke_bend_r + yoke_t, h = yoke_web_d); translate([0, 0, -1]) cylinder(r = yoke_bend_r, h = yoke_web_d + 2); }
                        translate([s > 0 ? 0 : -20, 0, -1]) cube([20, 20, yoke_web_d + 2]);
                    }
            // cheek
            translate([s * (yoke_w / 2 - yoke_t / 2), 0, 0]) rotate([90, 0, 90]) translate([0, 0, -yoke_t / 2])
                linear_extrude(yoke_t) intersection() {
                    cheek_2d();
                    translate([-100, -200]) square([200, 200 + web_top_above_pivot - yoke_t - yoke_bend_r]);
                }
        }
    }
}
module tilt_plate() {
    color(C_STRUCT) {
        translate([0, -tp_off, 0]) rotate([90, 0, 0]) linear_extrude(yoke_t) tilt_plate_face_2d();
        for (s = [-1, 1]) translate([s * (tp_w / 2 - yoke_t / 2), 0, 0]) rotate([90, 0, 90]) translate([0, 0, -yoke_t / 2])
            linear_extrude(yoke_t) ear_2d();
    }
}
module pivot_hardware() {
    for (s = [-1, 1]) {
        translate([s * (yoke_w / 2 + 2), 0, 0]) rotate([0, s * 90, 0]) bolt(pivot_d, 30, "hex");
        color([0.15, 0.15, 0.15]) translate([s * (cheek_x - 0.5), 0, 0]) rotate([0, -s * 90, 0]) difference() { cylinder(d = 20, h = cheek_x - tp_w / 2 - 1); cylinder(d = 8.5, h = 30, center = true); }  // nylon spacer
    }
}

// complete antenna sub-assembly in POLE frame (pole axis z, origin plate underside)
module antenna_bracket_assy(tilt = ant_tilt, explode = 0, with_reader = true) {
    ex = explode;
    // arm
    translate([pole_w / 2, -ant_arm_w / 2, ant_z]) rotate([0, 90, 0]) translate([0, 0, 0])
        rotate([0, 0, 0]) translate([0, ant_arm_w / 2, 0]) rotate([0, 0, 0])
            tslot(ant_arm_w, ant_arm_w, ant_arm_len, 40, 10);
    // corner brackets (top and bottom of arm root)
    translate([pole_w / 2 + 50 * ex, 0, 0]) {
        translate([0, -35 / 2, ant_z + ant_arm_w / 2]) corner_bracket40();
        translate([0, 35 / 2, ant_z - ant_arm_w / 2]) rotate([180, 0, 0]) corner_bracket40();
    }
    // yoke + tilt plate + reader at arm end
    yc = pole_w / 2 + ant_arm_len - yoke_w / 2;
    translate([yc, 0, ant_z - pivot_drop - 120 * ex]) {
        yoke();
        translate([0, -60 * ex, -60 * ex]) rotate([tilt, 0, 0]) {
            tilt_plate();
            if (with_reader) translate([0, -tp_off - yoke_t - 140 * ex, 0]) rotate([90, 0, 0]) rfid_reader();
        }
        translate([0, -60 * ex, -60 * ex]) pivot_hardware();
    }
}

// part view
yoke();
rotate([ant_tilt, 0, 0]) tilt_plate();
pivot_hardware();
