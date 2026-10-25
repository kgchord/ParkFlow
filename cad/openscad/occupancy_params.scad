// =====================================================================
// ParkFlow - (d) CEILING OCCUPANCY SENSOR NODE : parameters (mm)
// ESP32-C3 + DFRobot A02YYUW ultrasonic (or VL53L1X ToF on the same
// carrier) + 12x WS2812B ring (bay status), FDM ASA, two-part housing:
//   base  = ceiling plate, screwed to slab with 2x M5 / 6 mm anchors on
//           the 60 mm (Indian 3-pin box / 60 mm junction-box) pitch
//   cover = sensor carrier + diffuser window, 3 snap hooks + 1 M3 screw
// Frame: z = 0 at ceiling plane, housing hangs in -z. Shown inverted
// (as installed) in the assembly.
// =====================================================================
oc_d         = 96;    // outer diameter
oc_wall      = 2.4;   // wall (6 perimeters @0.4 nozzle)
oc_base_h    = 22;    // base cup depth
oc_cover_h   = 26;    // cover depth (incl. dome)
oc_floor     = 3;     // base back plate thickness
oc_r_edge    = 4;     // edge fillet (approx.)
oc_screw_pitch = 60;  // ceiling screw pitch
oc_screw_d   = 5.5;   // M5 / #10 wood screw clearance
oc_cable_d   = 8;     // rear cable entry (grommet)
snap_n       = 3;     // snap hooks
snap_w       = 10;    // hook width
snap_l       = 12;    // cantilever length
snap_t       = 1.6;   // cantilever thickness (ASA strain at 0.8 mm deflection ~ 1.5 % OK)
snap_lip     = 0.8;   // hook undercut
lip_h        = 5;     // cover spigot overlap into base
fit_clear    = 0.25;  // spigot radial clearance
esp_standoff = 5;     // ESP32-C3 board standoffs
ring_od      = 50;    // WS2812 ring OD (12 LED)
ring_id      = 36;
probe_d      = 34;    // A02YYUW probe (ASSUMED, see pf_bought.scad)
diffuser_t   = 1.2;   // printed natural/white PETG diffuser ring thickness
