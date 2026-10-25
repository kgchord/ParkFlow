// =====================================================================
// ParkFlow ASSEMBLY (e): FULL DEMO LANE LAYOUT  3.5 m x 8 m
//   Vehicles travel +y. Gantry pole on the driver's (right, +x) kerb
//   island at y = pole_y, sensors facing -y towards approaching vehicle.
//   Boom barrier just downstream of the pole, boom across the lane
//   (pointing -x). P10 sign on the pole. Translucent RFID read zone and
//   camera FOV cone. Occupancy node shown on a ceiling frame over the
//   first bay (demo rig).  -D explode=0/1 (not used), -D show_car=1
// =====================================================================
include <pf_bought.scad>
include <gantry_params.scad>
use <gantry_assembly.scad>
use <barrier_assembly.scad>
use <barrier_parts.scad>
use <occupancy_node_assembly.scad>

explode   = 0;      // kept for interface consistency (no exploded layout)
section   = 0;      // no section for layout
show_car  = 1;      // context vehicle approaching the read zone
show_zones = 1;     // RFID read zone + camera FOV
boom_ang  = 0;      // barrier angle (0 closed, 90 open)

lane_w    = 3500;   // lane width (x)
lane_l    = 8000;   // lane length (y)
island_w  = 600;    // kerb island width (+x side)
island_h  = 150;    // kerb height
pole_y    = 5200;   // pole station along the lane (from lane entry y=0)
bar_y     = 5700;   // barrier housing centre y
car_y     = 2400;   // car centre y (front bumper inside the RFID read zone)

// RFID read zone - target, to be bench-verified (reader >= 6 m class range,
// configured to ~2.5 m x 3 m zone 3-5 m ahead of the pole at bumper/windscreen height)
rz_y0 = pole_y - 5000; rz_y1 = pole_y - 2500; rz_w = 3000; rz_h = 1800;
// camera FOV: 2MP bullet, ~4 mm lens -> ~ 85 deg H x 45 deg V (ASSUMED lens);
// shown as cone to the plate plane at 4 m
cam_hfov = 40;   // deg (narrowed: 8-12 mm varifocal set for ANPR, ~150 px plate width at 4 m)
cam_vfov = 24;
cam_range = 5500;

module lane() {
    // asphalt
    color(C_ASPHALT) translate([0, 0, -60]) cube([lane_w, lane_l, 60]);
    // kerb island
    color(C_GROUND) translate([lane_w, 0, -60]) cube([island_w, lane_l, 60 + island_h]);
    color(C_GROUND) translate([-island_w, 0, -60]) cube([island_w, lane_l, 60 + island_h]);
    // road paint: edge lines, stop line under boom, ParkFlow chevrons
    color(C_WHITE) {
        for (x = [100, lane_w - 250]) translate([x, 0, 0]) cube([150, lane_l, 2]);
        translate([0, bar_y - 450, 0]) cube([lane_w, 300, 2]);
        for (y = [800 : 900 : 4000]) translate([lane_w / 2, y, 0]) for (s = [-1, 1]) rotate(s * 35) translate([-60, 0, 0]) cube([120, 700, 2]);
    }
    // hatched read zone marking
    color([0.95, 0.80, 0.15]) for (y = [rz_y0 : 400 : rz_y1]) translate([lane_w / 2 - rz_w / 2, y, 0]) cube([rz_w, 80, 2.5]);
}

module zones() {
    // RFID read zone (translucent box)
    color(C_ZONE_RFID) translate([lane_w / 2 - rz_w / 2, rz_y0, 0]) cube([rz_w, rz_y1 - rz_y0, rz_h]);
    // camera FOV pyramid from camera position (approx on pole, -y face, 1.2 m)
    cp = [lane_w + island_w / 2, pole_y - pole_d / 2 - 250 + 60, island_h + 1200 + 110];
    // clipped at road level (z = 0) so the cone shows the ground footprint of the view
    color(C_ZONE_CAM) intersection() {
        translate(cp) rotate([0, 0, 270 - cam_yaw]) rotate([0, cam_pitch, 0])
            hull() {
                sphere(r = 10);
                translate([cam_range, 0, 0]) cube([1, 2 * cam_range * tan(cam_hfov / 2), 2 * cam_range * tan(cam_vfov / 2)], center = true);
            }
        translate([-island_w, 0, 1]) cube([lane_w + 2 * island_w, lane_l, 3000]);   // clip to site footprint
    }
}

module layout() {
    lane();
    // gantry on right island, rotated so its +x arms reach over the lane (-x world) and sensors face -y
    translate([lane_w + island_w / 2, pole_y, island_h + grout_gap + 0]) mirror([1, 0, 0]) gantry(0, 1, 0);
    // boom barrier on right island, boom pointing -x across lane
    translate([lane_w + island_w / 2, bar_y, island_h]) rotate([0, 0, 180]) barrier_core(boom_ang);
    // car
    if (show_car) translate([lane_w / 2, car_y, 0]) rotate([0, 0, -90]) car();
    if (show_zones) zones();
    // occupancy node demo rig: 2 m frame on the far side (bay demo), node at 2.4 m
    translate([-island_w / 2, 6800, island_h]) {
        color(C_STRUCT) { tslot(40, 40, 2400, 40, 10); translate([0, 0, 2400]) rotate([0, 90, 0]) translate([0, 0, -20]) tslot(40, 40, 700, 40, 10); }
        translate([600, 0, 2380]) rotate([180, 0, 0]) oc_assy(0);
    }
}

layout();
