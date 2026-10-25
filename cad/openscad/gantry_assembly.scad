// =====================================================================
// ParkFlow ASSEMBLY (a): LANE GANTRY POLE
//   80x80 Al pole in 16 mm MS base-plate/socket/gusset weldment on 4x M12
//   chemical anchors (190 PCD), RFID antenna arm + tilt bracket @1.5 m,
//   ANPR camera arm @1.2 m, cable channel + boot, P10 sign, pole cap,
//   Edge Node enclosure on +y face.
// Overrides:  -D explode=1   -D section=1   -D with_edge=0
// =====================================================================
include <gantry_params.scad>
include <pf_bought.scad>
use <gantry_base_weldment.scad>
use <gantry_antenna_bracket.scad>
use <gantry_camera_arm.scad>
use <gantry_channel_cap_sign.scad>
use <edge_node_assembly.scad>

explode   = 0;     // 0 = assembled, 1 = exploded
section   = 0;     // 1 = cut away x>0 half (y-z plane section)
with_edge = 1;     // show Edge Node enclosure on pole
with_plinth = 1;   // show concrete plinth context
ex_gap    = 260;   // explode distance scale (mm)

module gantry(explode = 0, with_edge = 1, with_plinth = 1) {
    ex = explode;
    // plinth (context)
    if (with_plinth) color(C_GROUND) translate([0, 0, -grout_gap - plinth_h]) rbox(plinth_w, plinth_w, plinth_h, 10);
    if (with_plinth) color([0.78, 0.78, 0.74]) translate([0, 0, -grout_gap]) rbox(bp_w + 30, bp_w + 30, grout_gap, 14);
    // anchors stay in concrete
    anchors();
    // weldment
    translate([0, 0, 0.6 * ex * ex_gap]) base_weldment();
    // pole
    translate([0, 0, bp_t + 1.6 * ex * ex_gap]) tslot(pole_w, pole_d, pole_len, pole_pitch, pole_slot);
    // pole cap
    translate([0, 0, bp_t + pole_len - cap_h + 2.4 + 2.6 * ex * ex_gap]) pole_cap();
    // antenna bracket + reader
    translate([1.0 * ex * ex_gap, 0, 1.6 * ex * ex_gap]) antenna_bracket_assy(ant_tilt, ex);
    // camera arm + camera
    translate([0, -0.5 * ex * ex_gap, 1.6 * ex * ex_gap]) camera_arm_assy(ex);
    // cable channel + boot
    translate([-0.8 * ex * ex_gap, 0, 1.6 * ex * ex_gap]) cable_channel();
    translate([-0.8 * ex * ex_gap, 0, 0.6 * ex * ex_gap]) cable_boot();
    // sign
    translate([0, -0.4 * ex * ex_gap, 1.6 * ex * ex_gap]) sign_assy(ex);
    // edge node on +y face (enclosure back towards pole)
    if (with_edge) {
        for (s = [-1, 1]) color(C_STRUCT_DK) translate([0, pole_d / 2 + 1.5 + 0.4 * ex * ex_gap, edge_z + s * 150 + 1.6 * ex * ex_gap])
            rotate([90, 0, 0]) translate([0, 0, -1.5]) linear_extrude(3) edge_bracket_2d();
        translate([0, pole_d / 2 + 3 + edge_standoff + 1.0 * ex * ex_gap, edge_z + 1.6 * ex * ex_gap])
            rotate([-90, 0, 0]) rotate([0, 0, 180]) edge_node_on_pole();
    }
}

if (section == 1) {
    difference() { gantry(explode, with_edge, with_plinth); color(C_CUT) translate([0, -2000, -1000]) cube([4000, 4000, 5000]); }
} else gantry(explode, with_edge, with_plinth);
