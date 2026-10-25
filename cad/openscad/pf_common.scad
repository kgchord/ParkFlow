// =====================================================================
// ParkFlow - shared colours and geometry helpers (include<> this file)
// Units: mm. Colour code: structure grey, electronics green,
// sensors blue, moving parts orange (per project CAD convention).
// =====================================================================

// ---------- colour code -------------------------------------------------
C_STRUCT      = [0.66, 0.68, 0.71];   // structure (Al extrusion, sheet, plates) - grey
C_STRUCT_DK   = [0.48, 0.50, 0.54];   // structural steel (MS plates, painted) - dark grey
C_PRINT       = [0.80, 0.81, 0.83];   // FDM ASA/PETG structural prints - light grey
C_ELEC        = [0.16, 0.56, 0.27];   // electronics (PCBs, PSU, switch) - green
C_ELEC_DK     = [0.10, 0.36, 0.18];   // electronics enclosures / connectors
C_SENSOR      = [0.15, 0.42, 0.82];   // sensors (RFID, camera, ultrasonic, photo-beam) - blue
C_MOVE        = [0.96, 0.55, 0.10];   // moving parts (boom, hub, flags, counterweight) - orange
C_HW          = [0.30, 0.31, 0.34];   // fasteners / hardware
C_RUBBER      = [0.12, 0.12, 0.13];   // gaskets, cable, rubber
C_GROUND      = [0.86, 0.86, 0.83];   // concrete
C_ASPHALT     = [0.42, 0.43, 0.45];   // asphalt
C_WHITE       = [0.97, 0.97, 0.97];   // road paint / reflective bands
C_LED         = [1.00, 0.85, 0.30];   // LED emitter
C_ZONE_RFID   = [0.15, 0.45, 0.95, 0.16];  // translucent RFID read zone
C_ZONE_CAM    = [0.10, 0.75, 0.95, 0.14];  // translucent camera FOV
C_BEAM        = [0.95, 0.10, 0.10, 0.55];  // photo-beam line
C_CUT         = [0.80, 0.22, 0.22];        // section cut faces (preview colours cut faces with the cutter)

$fn = 40;    // default facet count (override with -D '$fn=..')

// ---------- primitives --------------------------------------------------
// rounded rectangle 2D, centred
module rrect(x, y, r) {
    rr = min(r, min(x, y) / 2 - 0.01);
    offset(r = rr) square([x - 2 * rr, y - 2 * rr], center = true);
}
// rounded box, centred in x/y, sitting on z=0
module rbox(x, y, z, r) { linear_extrude(z) rrect(x, y, r); }

// hexagon prism (across-flats af), on z=0
module hexp(af, h) { cylinder(d = af / cos(30), h = h, $fn = 6); }

// simple ISO bolt: head on z=0 pointing -z, shank along +z
module bolt(d = 8, l = 25, head = "hex") {
    color(C_HW) {
        if (head == "hex")      translate([0, 0, -0.7 * d]) hexp(1.5 * d + 1, 0.7 * d);
        else if (head == "skt") translate([0, 0, -d]) cylinder(d = 1.5 * d, h = d);
        else                    translate([0, 0, -0.6 * d]) cylinder(d1 = 2 * d, d2 = 1.1 * d, h = 0.6 * d);
        cylinder(d = d, h = l);
    }
}
module nut(d = 8) { color(C_HW) difference() { hexp(1.5 * d + 1, 0.8 * d); translate([0, 0, -1]) cylinder(d = d, h = d + 2); } }
module washer(d = 8) { color(C_HW) difference() { cylinder(d = 2.1 * d, h = 0.2 * d); translate([0, 0, -1]) cylinder(d = d + 0.5, h = d); } }

// ---------- aluminium T-slot extrusion ---------------------------------
// tslot2d(w, h, pitch, slot_w): generic approximation of an aluminium
// profile cross-section: square/rect body, one slot per 'pitch' on each
// face (slot opening slot_w, T-cavity behind), centre bores.
// 20-series: pitch 20, slot 6 ; 40-series: pitch 40, slot 10 (Wolweiss/
// Bosch-style 10 mm slot) ; 80x80 = 40-series 8-slot.
module tslot2d(w = 40, h = 40, pitch = 40, slot_w = 10) {
    lip   = pitch == 20 ? 1.8 : 4.0;      // lip thickness at slot opening
    cav_w = pitch == 20 ? 11  : 20;       // T-cavity width
    cav_d = pitch == 20 ? 4.2 : 8.0;      // T-cavity depth behind the lip
    bore  = pitch == 20 ? 4.2 : 8.5;      // centre bore (tapping size M5 / M10)
    nx = round(w / pitch); ny = round(h / pitch);
    difference() {
        rrect(w, h, 1.5);
        // slots on +/-y faces (spaced along x)
        for (i = [0 : nx - 1], s = [-1, 1]) {
            cx = -w / 2 + pitch / 2 + i * pitch;
            translate([cx, s * (h / 2 - lip / 2)]) square([slot_w, lip + 0.2], center = true);
            translate([cx, s * (h / 2 - lip - cav_d / 2)])
                polygon([[-cav_w / 2, s * cav_d / 2], [cav_w / 2, s * cav_d / 2],
                         [slot_w / 2, -s * cav_d / 2], [-slot_w / 2, -s * cav_d / 2]]);
        }
        // slots on +/-x faces (spaced along y)
        for (j = [0 : ny - 1], s = [-1, 1]) {
            cy = -h / 2 + pitch / 2 + j * pitch;
            translate([s * (w / 2 - lip / 2), cy]) square([lip + 0.2, slot_w], center = true);
            translate([s * (w / 2 - lip - cav_d / 2), cy])
                polygon([[s * cav_d / 2, -cav_w / 2], [s * cav_d / 2, cav_w / 2],
                         [-s * cav_d / 2, slot_w / 2], [-s * cav_d / 2, -slot_w / 2]]);
        }
        // centre bores at each pitch node
        for (i = [0 : nx - 1], j = [0 : ny - 1])
            translate([-w / 2 + pitch / 2 + i * pitch, -h / 2 + pitch / 2 + j * pitch]) circle(d = bore, $fn = 20);
    }
}
// extrusion along +z from z=0
module tslot(w = 40, h = 40, len = 100, pitch = 40, slot_w = 10, col = C_STRUCT) {
    color(col) linear_extrude(len, convexity = 6) tslot2d(w, h, pitch, slot_w);
}

// rectangular hollow section along +z (boom tube etc.)
module rhs(w, h, t, len) {
    linear_extrude(len, convexity = 4) difference() { rrect(w, h, t); rrect(w - 2 * t, h - 2 * t, 0.5); }
}

// generic cast 40-series corner bracket (bought-in), legs along +x and +z
module corner_bracket40(l = 40, w = 35, t = 4) {
    color(C_STRUCT_DK) {
        cube([l, w, t]); cube([t, w, l]);
        hull() { translate([0, w / 2 - 1.5, 0]) cube([t, 3, l]); translate([0, w / 2 - 1.5, 0]) cube([l, 3, t]); }
    }
}

// cable gland (bought-in), axis +z, from the wall outer face (z=0) outwards
module gland(m = 20) {
    color(C_RUBBER) {
        translate([0, 0, -4]) cylinder(d = m, h = 4);          // thread through wall
        hexp(m + 4, 6);
        translate([0, 0, 6]) cylinder(d1 = m + 2, d2 = m - 2, h = m * 0.7);
    }
}
