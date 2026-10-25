// =====================================================================
// ParkFlow - export driver. Select one part with -D part="name".
// 3D printed parts  -> STL (cad/stl/), print orientation applied.
// 2D laser profiles -> DXF (cad/dxf/), 1:1 mm, flat patterns for bent
// parts (bend lines are at the BA strip edges; K = 0.40, R = t).
// Driven by cad/scripts/export.sh
// =====================================================================
include <gantry_params.scad>
include <pf_bought.scad>
use <gantry_base_weldment.scad>
use <gantry_antenna_bracket.scad>
use <gantry_camera_arm.scad>
use <gantry_channel_cap_sign.scad>
use <edge_internals.scad>
use <barrier_parts.scad>
use <occupancy_parts.scad>

part = "base_plate";

// ---------- STL (FDM ASA / PETG) ---------------------------------
if (part == "pole_cap")        rotate([180, 0, 0]) pole_cap();            // print top-down
if (part == "cable_boot")      rotate([0, -90, 0]) translate([pole_w / 2, 0, 0]) cable_boot_body_only(); // back face on bed
if (part == "edge_pi_tray")    pi_tray();
if (part == "occ_base")        oc_base();
if (part == "occ_cover")       rotate([180, 0, 0]) translate([0, 0, -26]) oc_cover();   // dome down? -> rim up; supports-free annulus
if (part == "occ_diffuser")    oc_diffuser();
if (part == "boom_tip_cap")    boom_tip_cap_print();
if (part == "pb_post_cap")     pb_post_cap_print();

module boom_tip_cap_print() {
    // soft nose cap for 60x30 boom: 27 x 57 spigot (tube ID) + 30 mm nose
    difference() {
        union() {
            hull() { rbox(64, 34, 20, 4); translate([0, 0, 29]) rbox(50, 24, 1, 4); }
            translate([0, 0, -25]) rbox(56.6, 26.6, 25, 1);
        }
        translate([0, 0, -26]) rbox(50, 20, 40, 1);
    }
}
module pb_post_cap_print() { difference() { rbox(24, 24, 8, 3); translate([0, 0, -1]) rbox(20.4, 20.4, 6, 1); } }

// ---------- DXF (laser-cut) -----------------------------------------
if (part == "base_plate")          base_plate_2d();                     // 16 mm MS
if (part == "socket_cheek_long")   socket_cheek_long_2d();              // 6 mm MS x2
if (part == "socket_cheek_short")  socket_cheek_short_2d();             // 6 mm MS x2
if (part == "gusset")              gusset_2d();                         // 6 mm MS x4
if (part == "antenna_yoke_flat")   yoke_flat_2d();                      // 5 mm 5052-H32, 2 bends
if (part == "antenna_tilt_flat")   tilt_plate_flat_2d();                // 5 mm 5052-H32, 2 bends
if (part == "camera_plate")        cam_plate_2d();                      // 5 mm 5052-H32
if (part == "sign_bracket")        sign_bracket_2d();                   // 3 mm 5052-H32 x2 (Z-bent)
if (part == "edge_pole_bracket")   edge_bracket_2d();                   // 3 mm MS x2
if (part == "edge_mount_plate")    mount_plate_2d();                    // 3 mm 5052-H32
if (part == "edge_heat_spreader")  heat_spreader_2d();                  // 5 mm 6061-T6
if (part == "barrier_base_plate")  housing_base_plate_2d();             // 8 mm MS
if (part == "barrier_motor_plate") motor_plate_2d();                    // 6 mm 6061-T6
if (part == "barrier_bearing_plate") bearing_plate_2d();                // 6 mm 6061-T6
if (part == "barrier_front_panel") panel_front_2d();                    // 2 mm 5052-H32
if (part == "boom_carrier_plate")  carrier_plate_2d();                  // 5 mm 6061-T6 x2
if (part == "limit_flag")          limit_flag_2d();                     // 3 mm 5052-H32
if (part == "photo_post_foot")     pb_foot_2d();                        // 5 mm MS x2
