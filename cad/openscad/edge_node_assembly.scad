// =====================================================================
// ParkFlow ASSEMBLY (b): EDGE NODE IP65 ENCLOSURE
//   Overrides: -D explode=1 | -D section=1 | -D show_hood=0
//   section=1 cuts at y = pi_y (horizontal plane through Pi/heat path).
// =====================================================================
include <edge_params.scad>
include <pf_bought.scad>
use <edge_enclosure.scad>
use <edge_internals.scad>

explode   = 0;
section   = 0;
show_hood = 1;
ex_gap    = 1;

base_d_ = enc_d - enc_lid_d;
inner_floor = enc_wall + bp_boss_h;   // mounting plate seat (z)

module edge_node(explode = 0, show_hood = 1, show_lid = 1) {
    ex = explode;
    enclosure_base();
    // mounting plate + internals
    translate([0, 0, inner_floor + 120 * ex]) internals(ex);
    // lid
    if (show_lid) translate([0, 0, base_d_ + 650 * ex]) enclosure_lid();
    // heat sink on +x wall
    translate([enc_w / 2 + 160 * ex, hs_y, base_d_ / 2]) heat_sink();
    // glands + vent on bottom wall
    for (i = [0 : len(gland_x) - 1]) translate([gland_x[i], -enc_h / 2 - 80 * ex, base_d_ / 2]) rotate([90, 0, 0]) gland(gland_m[i]);
    color([0.25, 0.25, 0.27]) translate([vent_x, -enc_h / 2 - 80 * ex, base_d_ / 2]) rotate([90, 0, 0]) { cylinder(d = 18, h = 10); }
    if (show_hood) translate([0, 140 * ex, 0]) sun_hood();
}
// version for the pole: no explode, hood on
module edge_node_on_pole() { edge_node(0, 1, 1); }

orient = 1;   // 1 = shown as wall-mounted (local y -> world z, lid faces viewer -y)

module edge_view() {
    if (section == 1) {
        // cut: remove everything ABOVE the horizontal plane y = pi_y + 8 (plane runs through the
        // Pi stack, heat spreader bar, side-wall heat-sink window + gasket, lid gasket groove);
        // viewed from above, the lower half shows the full heat path Pi -> spreader -> wall -> fins.
        difference() {
            edge_node(explode, show_hood);
            color(C_CUT) translate([-1000, pi_y + 8, -1000]) cube([2000, 2000, 3000]);
        }
    } else edge_node(explode, show_hood);
}
if (orient == 1) rotate([90, 0, 0]) edge_view(); else edge_view();
