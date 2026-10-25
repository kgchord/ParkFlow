// =====================================================================
// ParkFlow - bought-in component ENVELOPES (simplified, for packaging,
// clearance and rendering only). Load with use<pf_bought.scad>.
// Dimensions are vendor nominal / class envelopes - ASSUMPTIONS noted;
// confirm against the final purchased part's datasheet before release.
// =====================================================================
include <pf_common.scad>

// ---------------------------------------------------------------------
// Integrated UHF RFID reader, 865-867 MHz, 8-9 dBic circular-pol, IP65.
// ASSUMED envelope 260 x 260 x 60 mm (typical "integrated long-range
// reader" class), rear 100x100 M6 mounting square, M12 cable connector.
// Origin: rear face centre, front face towards -y after rotation; here
// the radome faces +z (local), rear face on z=0.
// ---------------------------------------------------------------------
rfid_w = 260; rfid_h = 260; rfid_t = 60; rfid_holes = 100;
module rfid_reader() {
    color(C_SENSOR) translate([0, 0, 8]) rbox(rfid_w, rfid_h, rfid_t - 8, 14);
    color(C_SENSOR * 0.75) rbox(rfid_w - 20, rfid_h - 20, 8, 10);           // rear housing step
    color([0.85, 0.88, 0.95]) translate([0, 0, rfid_t - 0.6]) rbox(rfid_w - 30, rfid_h - 30, 1, 12); // radome label face
    color(C_RUBBER) translate([0, -rfid_h / 2 + 30, -18]) cylinder(d = 16, h = 18);   // M12 connector
}

// ---------------------------------------------------------------------
// 2 MP IR bullet IP camera (PoE, 850 nm), ASSUMED 220 x 80 x 80 envelope
// incl. sun hood; 3-hole base on 60 mm PCD; bracket knuckle 50 mm tall.
// Local frame: optical axis +x, base mount at origin (z=0 top of mount).
// ---------------------------------------------------------------------
cam_len = 220; cam_dia = 80; cam_knuckle = 50;
module bullet_camera() {
    color(C_SENSOR) {
        cylinder(d = 70, h = 6);                                           // mount base
        cylinder(d = 26, h = cam_knuckle);                                 // ball-joint stem
        translate([0, 0, cam_knuckle]) sphere(d = 30);
    }
    translate([-60, 0, cam_knuckle + cam_dia / 2 - 5]) {
        color(C_SENSOR) rotate([0, 90, 0]) cylinder(d = cam_dia - 8, h = cam_len - 20);
        color(C_SENSOR * 0.85) translate([cam_len - 20, 0, 0]) rotate([0, 90, 0]) cylinder(d = cam_dia - 14, h = 6);
        color([0.05, 0.06, 0.08]) translate([cam_len - 15, 0, 0]) rotate([0, 90, 0]) cylinder(d = 48, h = 2);   // lens/IR window
        color(C_SENSOR * 0.9) translate([20, -cam_dia / 2, cam_dia / 2 - 14]) cube([cam_len - 10, cam_dia, 4]); // sun hood
    }
}

// ---------------------------------------------------------------------
// P10 outdoor LED module 320 x 160 x ~15 mm (HUB12/HUB75, 32x16 px).
// LEDs face +z (local).
// ---------------------------------------------------------------------
p10_w = 320; p10_h = 160; p10_t = 15;
module p10_module(lit = true) {
    color([0.08, 0.08, 0.09]) cube([p10_w, p10_h, p10_t - 2]);
    for (i = [0 : 31], j = [0 : 15])
        color(lit && ((j > 3 && j < 12 && (i % 8 < 5)) || j == 2 || j == 13) ? [1, 0.2, 0.1] : [0.25, 0.08, 0.06])
            translate([5 + i * 10, 5 + j * 10, p10_t - 2]) cylinder(d = 5, h = 1.6, $fn = 8);
}
// sign cabinet: 3 mm 5052 tray + acrylic front, 1 module
module p10_cabinet(w = 360, h = 200, d = 60) {
    color(C_STRUCT) difference() {
        translate([-w / 2, -h / 2, 0]) cube([w, h, d]);
        translate([-w / 2 + 3, -h / 2 + 3, 3]) cube([w - 6, h - 6, d]);
    }
    translate([-p10_w / 2, -p10_h / 2, d - p10_t - 4]) p10_module();
    color([0.6, 0.6, 0.65, 0.25]) translate([-w / 2, -h / 2, d - 2]) cube([w, h, 2]);   // polycarbonate front
    color(C_ELEC) translate([-60, -40, 4]) cube([120, 80, 20]);                         // 5 V 10 A driver PSU
}

// ---------------------------------------------------------------------
// Raspberry Pi 5 (85 x 56 mm, 4x M2.5 on 58 x 49) + AI HAT+ (Hailo-8)
// on 16 mm stacking header, + Active Cooler footprint.
// Origin: PCB corner (lower-left), board on z=0.
// ---------------------------------------------------------------------
pi_l = 85; pi_w = 56; pi_t = 1.6; pi_hole_dx = 58; pi_hole_dy = 49; pi_hole_off = 3.5;
module rpi5() {
    color(C_ELEC) difference() {
        rbox(pi_l, pi_w, pi_t, 3) ;
        for (x = [0, pi_hole_dx], y = [0, pi_hole_dy])
            translate([-pi_l / 2 + pi_hole_off + x, -pi_w / 2 + pi_hole_off + y, -1]) cylinder(d = 2.7, h = 4);
    }
    // connectors
    color([0.75, 0.76, 0.78]) {
        translate([pi_l / 2 - 21, -pi_w / 2 + 2, pi_t]) cube([21, 16, 13.5]);    // RJ45
        translate([pi_l / 2 - 17, pi_w / 2 - 18, pi_t]) cube([17, 13, 15.5]);    // USB3
        translate([pi_l / 2 - 17, 2, pi_t]) cube([17, 13, 15.5]);                // USB2
    }
    color([0.15, 0.15, 0.16]) translate([-pi_l / 2 + 7, pi_w / 2 - 6.5, pi_t]) cube([51, 5, 8.5]);    // GPIO header
    color([0.2, 0.2, 0.22]) translate([-12, -10, pi_t]) cube([30, 30, 9]);                         // active cooler
}
module ai_hat() {
    color(C_ELEC * 1.1) difference() {
        rbox(65, 56.5, 1.6, 3);
    }
    color([0.15, 0.15, 0.16]) translate([-8, -10, 1.6]) cube([22, 22, 3]);      // Hailo-8 + pad
}
module pi_stack() {
    rpi5();
    translate([-pi_l / 2 + 32.5 + 0.0, 0, pi_t + 16]) ai_hat();
    color(C_HW) for (x = [0, pi_hole_dx], y = [0, pi_hole_dy])
        translate([-pi_l / 2 + pi_hole_off + x, -pi_w / 2 + pi_hole_off + y, pi_t]) cylinder(d = 4.5, h = 16, $fn = 6);
}

// ---------------------------------------------------------------------
// Mean Well LRS-150-24 enclosed SMPS: 159 x 97 x 30 mm (datasheet).
// Origin: base centre, z=0 on mounting face.
// ---------------------------------------------------------------------
smps_l = 159; smps_w = 97; smps_h = 30;
module lrs150() {
    color([0.72, 0.74, 0.76]) difference() {
        translate([-smps_l / 2, -smps_w / 2, 0]) cube([smps_l, smps_w, smps_h]);
        for (i = [0 : 10]) translate([-smps_l / 2 + 30 + i * 9, -smps_w / 2 + 12, smps_h - 1]) cube([5, smps_w - 24, 2]);
    }
    color(C_ELEC_DK) translate([-smps_l / 2 - 0.1, -smps_w / 2 + 6, 3]) cube([16, smps_w - 12, 14]);   // terminal block
    color(C_ELEC) translate([-smps_l / 2 + 1, -smps_w / 2 + 2, smps_h]) cube([24, 8, 0.4]);            // label
}

// ---------------------------------------------------------------------
// 5-port industrial PoE switch, DIN-rail. ASSUMED 140 x 105 x 40 mm
// (class envelope of 4+1 port 24-48 V PoE switches). Base on z=0.
// ---------------------------------------------------------------------
sw_l = 140; sw_w = 40; sw_h = 105;
module poe_switch() {
    color([0.30, 0.32, 0.35]) translate([-sw_w / 2, -sw_l / 2, 0]) cube([sw_w, sw_l, sw_h]);
    color(C_ELEC) for (i = [0 : 4]) translate([-sw_w / 2 + 6, -sw_l / 2 + 10 + i * 24, sw_h]) cube([16, 18, 1]);
    color([0.85, 0.86, 0.88]) for (i = [0 : 4]) translate([-sw_w / 2 + 6, -sw_l / 2 + 10 + i * 24, sw_h - 14]) cube([16.5, 16, 14.2]);
}

// ---------------------------------------------------------------------
// Lane Controller PCB 100 x 80 x 1.6 (custom, 2-layer) with ESP32-S3,
// terminal blocks, H-bridge. 4x M3 holes 4 mm from corners.
// ---------------------------------------------------------------------
lc_l = 100; lc_w = 80; lc_hole_in = 4;
module lane_controller_pcb() {
    color(C_ELEC) difference() {
        translate([-lc_l / 2, -lc_w / 2, 0]) cube([lc_l, lc_w, 1.6]);
        for (x = [-1, 1], y = [-1, 1]) translate([x * (lc_l / 2 - lc_hole_in), y * (lc_w / 2 - lc_hole_in), -1]) cylinder(d = 3.2, h = 4);
    }
    color([0.80, 0.82, 0.85]) translate([-10, 5, 1.6]) cube([18, 25.5, 3.2]);              // ESP32-S3-WROOM-1
    color([0.10, 0.45, 0.20]) for (i = [0 : 5]) translate([-lc_l / 2 + 8 + i * 15, -lc_w / 2 + 2, 1.6]) cube([12, 8, 10]); // terminal blocks
    color([0.15, 0.15, 0.16]) translate([20, 0, 1.6]) cube([22, 22, 12]);                  // H-bridge + heatsink
    color([0.85, 0.65, 0.20]) translate([-40, 20, 1.6]) cylinder(d = 10, h = 12);          // bulk cap
}

// ---------------------------------------------------------------------
// 35 mm DIN rail (EN 60715, 7.5 mm top-hat). Along +x, back on z=0.
// ---------------------------------------------------------------------
module din_rail(len = 200) {
    color([0.80, 0.80, 0.78]) rotate([90, 0, 90]) linear_extrude(len) polygon([
        [-17.5, 7.5], [-12.5, 7.5], [-12.5, 0], [12.5, 0], [12.5, 7.5], [17.5, 7.5],
        [17.5, 6.5], [13.5, 6.5], [13.5, -1], [-13.5, -1], [-13.5, 6.5], [-17.5, 6.5]]);
}
// DIN-rail modular device (MCB / SPD / fuse terminal), width in modules (17.5 mm)
module din_device(mods = 1, col = [0.92, 0.92, 0.90], h = 70) {
    color(col) translate([0, -45, 0]) cube([mods * 17.5 - 0.5, 90, h - 10]);
    color(col * 0.95) translate([0, -22.5, h - 10]) cube([mods * 17.5 - 0.5, 45, 10]);
}

// ---------------------------------------------------------------------
// ESP32-C3 SuperMini/DevKit class board 22.5 x 18 (supermini) - we
// assume ESP32-C3-DevKitM-1 class 48 x 26 mm for robustness.
// ---------------------------------------------------------------------
module esp32c3_board() {
    color(C_ELEC) translate([-24, -13, 0]) cube([48, 26, 1.6]);
    color([0.80, 0.82, 0.85]) translate([-6, -8, 1.6]) cube([16, 16, 2.6]);
    color([0.75, 0.76, 0.78]) translate([-25, -4.5, 1.6]) cube([7.5, 9, 3.2]);  // USB-C
}

// ---------------------------------------------------------------------
// DFRobot A02YYUW (SEN0311) waterproof ultrasonic sensor.
// ASSUMED envelope (vendor drawing not verified online): sealed probe
// D=34 mm x 26 mm long with M30-class mounting body, 60 deg beam,
// 3-450 cm range (DFRobot wiki). Probe faces -z, flange at z=0.
// ---------------------------------------------------------------------
a02_probe_d = 34; a02_probe_l = 26; a02_body_w = 42; a02_body_l = 36; a02_body_h = 18;
module a02yyuw() {
    color(C_SENSOR) {
        translate([0, 0, -a02_probe_l]) cylinder(d = a02_probe_d, h = a02_probe_l);
        translate([-a02_body_l / 2, -a02_body_w / 2, 0]) cube([a02_body_l, a02_body_w, a02_body_h]);
    }
    color([0.85, 0.87, 0.90]) translate([0, 0, -a02_probe_l - 0.5]) cylinder(d = a02_probe_d - 6, h = 0.6);
    color(C_RUBBER) translate([a02_body_l / 2, 0, a02_body_h / 2]) rotate([0, 90, 0]) cylinder(d = 5, h = 25);
}

// WS2812B ring (12-LED, 50 mm OD x 37 ID class)
module ws2812_ring(od = 50, id = 36, n = 12) {
    color(C_ELEC) difference() { cylinder(d = od, h = 1.6); translate([0, 0, -1]) cylinder(d = id, h = 4); }
    for (i = [0 : n - 1]) rotate(i * 360 / n) translate([(od + id) / 4, 0, 1.6]) color(C_LED) cube([5, 5, 1.6], center = true);
}

// ---------------------------------------------------------------------
// 24 V DC worm gearmotor, ASSUMED envelope: gearbox 90 x 75 x 70,
// motor can D60 x 110, output shaft D12 x 30 (12 mm D-flat), 4x M6
// mounting on 70 x 50. Output shaft along +z, gearbox face on z=0.
// ---------------------------------------------------------------------
gm_box_x = 90; gm_box_y = 75; gm_box_z = 70; gm_motor_d = 60; gm_motor_l = 110; gm_shaft_d = 12; gm_shaft_l = 30;
gm_shaft_off = 20;   // output shaft offset from gearbox centre along +x
module gearmotor() {
    color([0.25, 0.27, 0.30]) translate([-gm_box_x / 2, -gm_box_y / 2, -gm_box_z]) cube([gm_box_x, gm_box_y, gm_box_z]);
    color([0.20, 0.22, 0.25]) translate([-gm_box_x / 2, -gm_box_y / 2 + 37, -gm_box_z / 2 - 10]) rotate([0, -90, 0]) cylinder(d = gm_motor_d, h = gm_motor_l);
    color([0.82, 0.82, 0.84]) translate([gm_shaft_off, 0, 0]) difference() {
        cylinder(d = gm_shaft_d, h = gm_shaft_l);
        translate([gm_shaft_d / 2 - 1.2, -10, 5]) cube([5, 20, 40]);
    }
}

// slotted photo-electric sensor head (through-beam emitter/receiver),
// M18 cylindrical, axis +x.
module photo_head() {
    color(C_SENSOR) rotate([0, 90, 0]) cylinder(d = 18, h = 60);
    color(C_HW) translate([10, 0, 0]) rotate([0, 90, 0]) hexp(27, 4);
    color([0.9, 0.2, 0.2]) translate([60, 0, 0]) rotate([0, 90, 0]) cylinder(d = 12, h = 0.6);
}

// simple car (context) - hatchback 3.9 x 1.7 x 1.5 m class
module car() {
    color([0.75, 0.80, 0.86]) {
        translate([-1950, -850, 180]) hull() {
            translate([0, 0, 0]) cube([3900, 1700, 520]);
            translate([600, 80, 520]) cube([2100, 1540, 10]);
        }
        translate([-1350, -800, 700]) hull() {
            cube([2300, 1600, 10]);
            translate([500, 60, 580]) cube([1300, 1480, 10]);
        }
    }
    color([0.25, 0.30, 0.38, 0.9]) translate([-1300, -810, 760]) hull() { cube([2200, 1620, 10]); translate([520, 60, 500]) cube([1200, 1500, 10]); }
    color(C_RUBBER) for (x = [-1250, 1250], y = [-760, 760]) translate([x, y, 310]) rotate([90, 0, 0]) cylinder(d = 620, h = 200, center = true);
    color(C_WHITE) translate([-1960, -260, 380]) cube([10, 520, 110]);   // number plate
    color([0.2, 0.2, 0.2]) translate([-1965, -230, 410]) cube([4, 460, 50]);
}
