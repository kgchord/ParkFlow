// =====================================================================
// ParkFlow (a) part: ANPR CAMERA ARM + ADAPTER PLATE
//   * arm: 40x40 Al T-slot, cam_arm_len, on pole -y face (towards the
//     approaching vehicle), 2x corner brackets
//   * adapter plate: 5 mm 5052-H32 laser cut, bolted on arm top with
//     2x M6 T-nuts, overhangs arm end; bullet camera 3x M5 on 60 PCD
//   * camera ball joint gives pitch cam_pitch (15-25 deg) and yaw cam_yaw
// =====================================================================
include <gantry_params.scad>
include <pf_bought.scad>

cam_arm_len_eff = 250;          // as built: 250 mm (300 nominal in the concept; shortened to keep camera behind sign drip line)
cam_plate_overhang = 60;        // plate overhang beyond arm end

module cam_plate_2d() {
    difference() {
        rrect(cam_plate_l, cam_plate_w, 8);
        // 2x M6 slots to arm T-nuts (along arm), 30 mm adjust
        for (x = [-cam_plate_l / 2 + 15, -cam_plate_l / 2 + 45]) hull() { translate([x - 5, 0]) circle(d = 6.6); translate([x + 5, 0]) circle(d = 6.6); }
        // camera 3-hole M5 pattern on PCD + cable hole
        translate([cam_plate_l / 2 - 35, 0]) {
            for (a = [90, 210, 330]) rotate(a) translate([cam_mount_pcd / 2, 0]) circle(d = 5.5);
            circle(d = 18);
        }
    }
}

module camera_arm_assy(explode = 0, with_camera = true) {
    ex = explode;
    // arm along -y from pole -y face
    translate([0, -pole_d / 2, cam_z]) rotate([90, 0, 0]) tslot(40, 40, cam_arm_len_eff, 40, 10);
    translate([0, -pole_d / 2 - 50 * ex, 0]) {
        translate([-35 / 2, 0, cam_z + 20]) rotate([0, 0, -90]) translate([0, 0, 0]) corner_bracket40();
        translate([35 / 2, 0, cam_z - 20]) rotate([180, 0, -90]) corner_bracket40();
    }
    // adapter plate on arm top: plate x-axis along -y
    py = -pole_d / 2 - cam_arm_len_eff + cam_plate_l / 2 - cam_plate_overhang;
    translate([0, py, cam_z + 20 + 60 * ex]) rotate([0, 0, -90]) {
        color(C_STRUCT) linear_extrude(cam_plate_t) cam_plate_2d();
        if (with_camera) translate([cam_plate_l / 2 - 35, 0, cam_plate_t + 80 * ex])
            rotate([0, 0, cam_yaw]) bullet_camera_aimed();
    }
}
// camera with pitch applied at the knuckle
module bullet_camera_aimed() {
    // bullet_camera(): optical axis +x ; tilt body down by cam_pitch about knuckle
    color(C_SENSOR) { cylinder(d = 70, h = 6); cylinder(d = 26, h = cam_knuckle); }
    translate([0, 0, cam_knuckle]) rotate([0, cam_pitch, 0]) translate([0, 0, -cam_knuckle]) difference() {
        bullet_camera();
        cylinder(d = 71, h = cam_knuckle - 15);
    }
}

camera_arm_assy();
