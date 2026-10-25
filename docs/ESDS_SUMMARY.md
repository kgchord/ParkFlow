# ESDS summary (electronics, Rev A)

Full document: `electronics/ESDS.md`. GPIO table: `electronics/PINMAP.md` (generated). Power tree: `electronics/diagrams/power_tree.png`.

- **Architecture:** Raspberry Pi 5 + AI HAT+ Edge Node; ESP32-S3-WROOM-1-N16R8 Lane Controller (RS485 to the ID Tech IDT 85 reader, UART to the Edge Node, IBT-2 / BTS7960 motor-driver module on header J14); PoE camera via Netgear GS305P.
- **Safety:** E-stop opens the contactor coil loop and gates the motor-driver enable (MOT_INH) in hardware; CLOSE is blocked by the beam in hardware; TPS3823-33 watchdog.
- **Power (targets, to be bench-verified):** 24 V bus typ 2.9 A but coincident peak 7.66 A (87 %) against an 8.8 A LRS-200-24 with the motor limited to 5 A (the old 6.5 A supply peaked at 8.66 A). The 5 A limit is firmware-only and the IS scale is to be bench-calibrated. Edge UPS ride-through 9.8 Wh usable vs 3.3 Wh needed (2.9x). No 24 V backup for the barrier is in the BOM: the barrier fails in place on mains loss and is released by hand (OPEN_DECISIONS D2); the PoE switch and camera have no UPS (D3).
- **Verification:** KiCad ERC 0 errors / 0 warnings. PCB is **placement only, unrouted** (DRC: 4 USB-C library hole-clearance errors, 225 unconnected pads); routing and final review are still to be done in KiCad.
- **Biggest open inconsistencies:** schematic, BOM, contactor, PNP beam input and motor driver voltage are now one consistent design (25 Oct). Still open: 18 N.m motor vs the 30 N.m requirement (demo wind limit 12 m/s), thermal margin (52.3 / 48.1 deg C vs 50 deg C, GS305P rated 40 deg C), no UPS for PoE/camera. Full lists: ESDS Section 11 and docs/OPEN_DECISIONS.md.
