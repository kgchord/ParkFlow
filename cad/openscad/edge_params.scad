// =====================================================================
// ParkFlow - (b) EDGE NODE IP65 ENCLOSURE : master parameter set (mm)
// Local frame: x = width (left->right), y = height (up), z = out of
// mounting wall towards the lid (z=0 = enclosure back outer face).
// Body: bought-in IP65 polycarbonate box class 300 x 400 x 180 (ASSUMED
// generic Indian-market PC/ABS enclosure; modelled with the features we
// machine/specify: lid gasket groove, lid screw bosses, back-plate bosses,
// gland and vent holes, heat-sink cut-out).
// =====================================================================
enc_w        = 300;   // external width  (x)
enc_h        = 400;   // external height (y)
enc_d        = 180;   // external depth  (z), base + lid
enc_lid_d    = 40;    // lid depth (z)
enc_wall     = 3.5;   // wall thickness
enc_r        = 10;    // vertical corner radius
lid_boss_d   = 14;    // lid screw boss OD (4 corners, inside base)
lid_screw    = 4;     // M4 captive stainless lid screws
lid_boss_in  = 13;    // boss centre inset from outer corner (x and y)
tongue_w     = 2.0;   // rim tongue width on base
tongue_h     = 3.0;   // rim tongue height
groove_w     = 4.2;   // lid gasket groove width
groove_d     = 5.0;   // lid gasket groove depth
gasket_d     = 4.5;   // EPDM/silicone cord dia (25 % compression on tongue)
bp_boss_d    = 12;    // back-plate mounting boss OD
bp_boss_h    = 10;    // back-plate boss height above inner floor
bp_boss_dx   = 230;   // back-plate boss pitch (x)
bp_boss_dy   = 340;   // back-plate boss pitch (y)
mlug_w       = 30;    // external mounting lug width
mlug_x       = 165;   // lug centre x (+/-) -> 330 pitch to pole bracket
mlug_y       = 150;   // lug centre y (+/-)

// ---------- internal mounting plate (3 mm 5052-H32, laser cut) -------
mp_w         = 260;   // mounting plate width
mp_h         = 360;   // mounting plate height
mp_t         = 3;     // thickness

// ---------- layout (centres on mounting plate, plate-local x,y) -------
din_y        = 100;   // DIN rail centreline
din_len      = 240;   // DIN rail length
smps_x       = -40;   // LRS-150-24 centre
smps_y       = -120;
pi_x         = 72;    // Raspberry Pi 5 centre
pi_y         = -15;
pi_standoff  = 12;    // Pi M2.5 standoff height (on printed tray)
lc_x         = -68;   // Lane Controller PCB centre
lc_y         = -15;
lc_standoff  = 10;    // M3 brass hex standoffs
buck_x       = 88;    // 24->5 V 5 A buck module
buck_y       = -120;
pitray_t     = 3;     // printed Pi tray base thickness (ASA)

// ---------- thermal path ---------------------------------------------
hs_base_l    = 200;   // heat-sink base length (y), on +x side wall
hs_base_w    = 150;   // heat-sink base width (z)
hs_base_t    = 6;     // heat-sink base thickness
hs_fin_n     = 18;    // fins (vertical, along y, for natural convection)
hs_fin_t     = 2;     // fin thickness
hs_fin_h     = 35;    // fin height (outward x)
hs_cut_l     = 160;   // side-wall cut-out sealed by heat-sink base + gasket
hs_cut_w     = 110;
hs_y         = -15;   // heat-sink centre y
spr_t        = 5;     // spreader plate thickness (6061-T6) over Pi/HAT
spr_l        = 100;   // spreader plate length (x)
spr_w        = 70;    // spreader plate width (y)
spr_bar_w    = 20;    // spreader bar to wall (y)
spr_bar_t    = 10;    // spreader bar thickness (z)

// ---------- glands & vent (bottom wall) ------------------------------
gland_x      = [-110, -60, -10, 40, 90];   // positions along bottom
gland_m      = [25, 20, 20, 20, 16];        // M25 mains, M20 PoE cam, M20 RFID, M20 motor/IO, M16 sensors
vent_x       = 125;                         // M12 pressure-equalisation vent (ePTFE)

// ---------- sun hood (2 mm 5052, 25 mm air gap) ----------------------
hood_gap     = 25;
hood_t       = 2;
hood_front   = 60;    // visor overhang in front of lid
