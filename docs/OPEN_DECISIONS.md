# ParkFlow: Open Decisions

Items that need a team or vendor decision before Stage 2 can be called closed. Written 25 Oct 2026. Every number is predicted or taken from a cited page; nothing here is a measured result, and targets are "to be bench-verified". Cost impacts are against the current BOM (subtotal Rs 1,67,132, 10 % contingency Rs 16,713, total Rs 1,83,845).

| ID | Decision | Recommendation | Cost / time |
|---|---|---|---|
| D1 | Production barrier motor (>= 30 N.m, self-locking) | Keep the 18 N.m wiper motor as a demo-only part; pick a worm-gear motor after FEA | unpriced; 1 to 2 weeks to source |
| D2 | 24 V battery buffer for mains loss | Do not fit for the demo; document fail-in-place + hand release | about Rs 3,000 to 6,000 estimate if fitted |
| D3 | UPS for PoE switch and camera | State the limitation; fit only if the pilot site has frequent outages | about Rs 2,000 to 4,000 (not priced) |
| D4 | Edge cooling choice (sink size, spreader, Active Cooler) | Build the 4 h soak first, then size the sink | Rs 2,000 to 4,500 estimate already in BOM |
| D5 | Storm procedure / anemometer | Procedure only (guard lowers and pins boom); no anemometer in BOM | Rs 0 now |
| D6 | Update CAD: enclosure, power box, pole section | CAD/FEA owner to apply (see below) | about 1 day CAD work |
| D7 | Hardware current comparator for the motor | Optional; firmware trip is the only motor over-current protection today | about Rs 100 to 300 parts + a PCB spin |
| D8 | Industrial PoE switch (GS305P is rated 0 to 40 deg C) | Replace if the soak shows the switch above 40 deg C | not priced |
| D9 | LionCircuits quote for the schematic parts | Request a quote against the regenerated netlist | 1 to 2 days; adds the Rs 2,500 to 5,000 estimate line |
| D10 | ASA filament for printed outdoor parts | Confirm an Indian stockist page | small |

## D1. Production motor and self-locking

- Problem: the BOM motor is a Lucas TVS 24 V wiper motor listed at 18 N.m. The requirement is >= 30 N.m.
- Arithmetic (cad/calcs/CALCS.md section 4): with the 7-plate counterweight (3.30 kg, 94 % balance) the required drive torque at a 15 m/s wind is 11.6 N.m (17.8 N.m without the counterweight). Margin of the 18 N.m motor is 1.56 at 15 m/s and 2.2 at 12 m/s. Still-air need is 2.1 N.m.
- Resolved in the design: the load was reduced (counterweight, 30 mm face across the lane), so the 18 N.m motor is acceptable for the demo with a wind limit of 12 m/s.
- Not resolved: the >= 30 N.m figure and self-locking. A wiper worm gear is not assumed to self-lock; the raised-boom storm case (93 N.m, 57 to 115 N.m by face) back-drives it, so a storm-lock pin is proposed.
- Options: (a) keep the 18 N.m motor and state the 12 m/s limit; (b) a >= 30 N.m worm-gear motor (needs a vendor page, not yet found in the four cities); (c) a larger reduction stage.
- Recommendation: (a) for Stage 2, (b) for Stage 3 after the static hold test.

## D2. Mains loss and the 24 V buffer

- Decision taken: baseline is fail-in-place with a hand-release pin. The earlier "automatic fail-open" claim is withdrawn (SAFETY F11) because nothing in the BOM kept the motor driven after the 40 ms hold-up of the supply.
- Option: a 24 V battery buffer and charger (not in the BOM). If fitted, the firmware AC_OK open-hold already in code applies.
- Recommendation: do not fit for the demo; fit in production if the site requires automatic opening.
- Impact: estimate only; no vendor page found.

## D3. PoE switch and camera on mains loss

- The PoE switch and camera have no UPS. In an outage ANPR stops; RFID and the guard check remain. The Pi has the X1202 UPS.
- Recommendation: state the limitation in the documentation. Fit a small DC UPS for the switch only if the pilot site needs it.

## D4. Edge cooling

- Predicted air temperature at 45 deg C ambient: 61.8 deg C sealed, 54.2 deg C with a sink, 52.3 deg C (convection only) / 48.1 deg C (with radiation) with the supply moved to a power box. The AI HAT+ limit is 50 deg C, so the margin is not demonstrated.
- Recommendation: run the 4 h soak (T-11) with the current arrangement, then decide.

## D5. Storm procedure

- No anemometer is in the BOM. Recommendation: written procedure (lower and pin the boom on a storm warning); anemometer only if the pilot site is exposed.

## D6. CAD and FEA owner actions (nothing under cad/ was edited by this pass)

- Enclosure: CAD is 300x400x180; the bought box is 300x300x210. Thermal result differs by under 1 K, but fit of the sink and the power box must be re-checked.
- Pole: the STEP pole section is a generic 4891 mm2 (31.7 kg). The real Systeal section is 1649 mm2 (4.45 kg/m, I = 130 cm4, about 10.7 kg); calculations use 5.4 kg/m (12.96 kg). The STEP pole is not a real mass and is stiffer than a real one; FEA results using it should be flagged.
- Supply: CAD and the .scad files model the LRS-150-24 (159x97x30); the BOM now buys the LRS-200-24 (larger body, dimensions not yet taken from a sheet); motor driver is the IBT-2 module, not a bare board.
- Add: storm-lock pin, power box, 7-plate counterweight, 30 mm boom face across the lane.

## D7. Hardware current comparator

- The IBT-2 module current sense (IS, about 0.1 V/A, to be bench-calibrated) feeds an ADC; the over-current trip is firmware only (placeholder threshold must be set at commissioning, about 540 mV for 5 A).
- Recommendation: leave as is for the demo; add a comparator in the next board spin.

## D8. PoE switch rating

- Netgear GS305P is rated 0 to 40 deg C and is outside its rating in every thermal case. Recommendation: replace with an industrial PoE switch if the soak confirms.

## D9. Schematic parts quote

- The BOM carries one estimate line (Rs 2,500 to 5,000) for the schematic parts not otherwise listed. Obtain a LionCircuits quote from the regenerated netlist.

## D10. ASA filament

- No Indian stockist page was usable. Keep as an estimate.

## Other quotes still without a vendor page (estimate lines in the BOM)

Occupancy sensor RS485 nodes, RFID and camera written confirmations, authorised-distributor evidence, thermostats, heat sink and sun hood, vent and glands, barrier housing, drive-train machined parts, storm-lock pin.
