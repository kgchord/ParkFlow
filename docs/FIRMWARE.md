# ParkFlow Demo Lane: Firmware and Edge Software

Status 24 Oct 2026: **host-tested only.** The lane state machine, parsers and Edge Node logic compile and pass their tests on a PC. Nothing here has run on an ESP32-S3, a Raspberry Pi 5 or a real barrier. Every timing and threshold is a **target or placeholder, to be bench-verified**. Billing goes to a **MOCK** ledger; no NPCI/NETC/FASTag network call exists in the code.

Flow diagram: `docs/firmware_flow.png`. Source: `firmware/` (`run_all.sh` rebuilds and re-tests everything; logs in `firmware/test_logs/`).

## 1. Architecture

| Layer | Where | Notes |
|---|---|---|
| Pure state machine `LaneFsm` | `firmware/lane_controller/src/lane_fsm.cpp` | No hardware, heap or clock access. `step(Inputs, Events) -> Outputs`. |
| Glue `LaneApp` | `src/lane_app.cpp` | Debounce, polarity decode, UART parsing, output drive, watchdog kick. |
| Parsers | `rfid_parser.cpp`, `edge_link.cpp` | Generic RS485 reader frames; ASCII+XOR Edge link. |
| HAL interface `IHal` | `include/hal.h` | Implemented by `test/mock_hal.h` (host, with barrier physics and PCB interlock model) and `hal_esp32s3/` (ESP-IDF, **not compiled here**). |
| Edge Node (Python 3, stdlib only) | `firmware/edge_node/parkflow_edge/` | Plate normalisation, fusion, SQLite allow-list, offline queue, mock ledger, simulator. |

Division of work: the Lane Controller reads the tag and drives the barrier. The Edge Node reads the plate and does the fusion. They talk over UART0 (`$TYPE,args*HH`, XOR checksum). A DEC (decision) reply is matched by sequence number, so a late reply for an old vehicle is ignored.

## 2. Lane state machine

| State | Entered when | Motor | LED / buzzer / sign | Leaves to |
|---|---|---|---|---|
| IDLE | boom down (lim_dn), cycle done | stop | green slow blink (amber if link lost) / none / WELCOME | VEHICLE_DETECTED on tag frame, Edge "vehicle" event or presence (tag and Edge triggers ignored 3 s after a cycle) |
| VEHICLE_DETECTED | trigger | stop | blue / none / PLEASE WAIT | READ (next tick); sends `VEH`, optional reader inventory command |
| READ | after trigger | stop | blue | FUSE after 400 ms, or 100 ms after first tag (strongest RSSI kept, peak time and distinct-EPC count recorded); sends `TAG` or `NOTAG` |
| FUSE | tag report sent | stop | blue | GRANT on `DEC,seq,G`; FALLBACK on `F`, `D` or 1000 ms time-out |
| GRANT | decision G or guard command | stop (1 tick) | green / none / PROCEED | BARRIER_OPEN |
| FALLBACK | F/D/time-out | stop | amber solid / double beep every 3 s / SEE GUARD | GRANT on guard command; IDLE after 30 s |
| BARRIER_OPEN | grant, reversal, homing | OPEN (STOP for 100 ms after a reversal) | green; amber fast + alarm after reversal | CLEAR at lim_up; FAULT on time-out (1.5 x nominal) or over-current |
| CLEAR | boom up | stop | green / none / PROCEED | BARRIER_CLOSE when beam clear and no presence for 1.5 s **and** (vehicle passed or 10 s elapsed); sends `PASS` if passed |
| BARRIER_CLOSE | clear | CLOSE | amber fast / short beep 1 s / WAIT | IDLE at lim_dn; BARRIER_OPEN on beam break, presence or over-current (reverse); FAULT on time-out |
| OPEN_HOLD | link lost 3 s, or mains lost 0.5 s (policy FAIL_OPEN_HOLD) | OPEN then hold | amber slow blink / 1 s pulse every 5 s / LANE OPEN | CLEAR once heartbeat is gap-free for 3 s (mains good for 5 s) |
| FAULT | OPEN_TIMEOUT, CLOSE_TIMEOUT, OVERCURRENT_STALL, LIMIT_CONFLICT, OBSTRUCTION_LOCKOUT | stop, K1 off | red, N blinks = fault code / triple beep / LANE CLOSED | latched; `RESET` command runs the safe re-home |
| ESTOP | E-stop loop open (`ESTOP_OK` low) | stop, K1 off | red solid / long beep / STOPPED | only via `REARM` (BOOT button or Edge command) with loop healthy, then re-home |

Re-home (power-up, fault reset, re-arm): lim_dn means IDLE, lim_up means CLEAR, otherwise **open**. Firmware never starts a close from an unknown position.

### Anti-crush rules (all in `lane_fsm.cpp`)
1. Closing is entered only from CLEAR, after the beam and presence have been clear for 1.5 s.
2. In BARRIER_CLOSE any beam break or presence stops and reverses at once.
3. Motor current above `oc_threshold_mv` for 50 ms (after a 300 ms in-rush blanking) reverses. In-rush spikes and a 40 ms spike do not trip (tested).
4. A final gate at the end of every tick turns CLOSE into STOP unless state is BARRIER_CLOSE, beam clear, no presence, E-stop healthy.
5. The PCB gates the CLOSE input with `BEAM_CLEAR` (U10) and the bridge enable with `ESTOP_OK` (U9). The mock HAL models both, so a test can tell "firmware asked" from "hardware did".
6. After 3 consecutive reversals the boom is driven fully open and the controller latches OBSTRUCTION_LOCKOUT (lane left open, guard attends).
7. A 100 ms stop is inserted between opposite directions.

### Link-loss behaviour and rationale
Default (`FAIL_OPEN_HOLD`): no valid heartbeat for 3 s (Edge sends 1 per second) means drive the boom open, hold, amber LED, buzzer pulse, sign LANE OPEN. Recovery needs 3 s of gap-free heartbeats, then the normal close rules apply. This matches `docs/safety/SAFETY.md` F9/F11.

Why fail-open:
1. Life safety outranks revenue. A parking exit is an evacuation route, and a boom stuck closed traps people and vehicles.
2. An open boom carries no crush hazard. Opening is the only motion firmware starts without a decision.
3. Stage 1 promises no hard-block without a human alternative.
4. Revenue can be recovered: passes made while open are still seen by the Lane Controller and, once the Edge Node is back, reconciled from its logs.

Price of this choice: while the Edge Node is down (including a normal Pi reboot after the 45 s boot grace) the lane is **unauthenticated and open**. Sites that cannot accept that set `LinkLossPolicy::FAIL_SECURE`: the boom is never opened automatically, vehicles are not processed (sign SEE GUARD) and a guard must use the manual-release key. In fail-secure mode mains loss also no longer opens the boom (tested). No claim is made that fail-open is right for every site.

Mains loss (25 Oct decision, SAFETY F11): the BOM has no 24 V backup, so on loss of mains the motor driver loses power and the boom **fails in place**; a hand-release pin frees it. The AC_OK input and the open-hold in `lane_fsm.cpp` stay in the code and only act if the optional 24 V battery buffer is fitted (OPEN_DECISIONS D2). The heartbeat-loss fail-open above is unaffected (it needs motor power).

### Watchdogs
* Internal: ESP-IDF task watchdog (`app_main.cpp`, 2 s) fed from the control task.
* External: TPS3823 `WDI` (GPIO14) toggled only if the control loop checked in within 50 ms of the previous tick; an overrun skips the kick (tested). A hung loop stops kicking, the chip resets the MCU, and the boot path re-homes open. `MOT_EN` and `MOT_IN_A` have 100 k pull-downs on the PCB, so a reset leaves the motor off.
* Edge Node hang is covered by the heartbeat rule above.

### Reader parser (generic by design)
`RfidFrameCfg` describes a frame as data: SOF bytes, length byte position and adjust, CRC type (none, SUM8, XOR8, CRC16 CCITT-FALSE, ARC, MODBUS), CRC order and span, frame-type filter, EPC offset and length (fixed or in-frame), RSSI offset and signedness, and an optional inventory command. **The exact reader's command set is unverified**: no datasheet or unit was available to check. `kIllustrativeProfile` is an invented layout used only for tests and must not be mistaken for a real reader's protocol. The default UART baud (9600) in the HAL is a placeholder. A second invented layout in the tests shows the parser is configurable.

### Sign output
`sign_show(text)` is a **stub** (log only). HUB12 pins are defined (A, B, CLK, LAT, OE, R) and OE has a pull-up so the sign is blank at reset. A real 1/4-scan refresh is not written.

## 3. Pin usage (from `electronics/tools/gen_lane_controller_sch.py`, dict `esp`; mirrored in `include/pins.h`)

| GPIO | Net | Dir | Firmware use |
|---|---|---|---|
| 0 | GPIO0_BOOT | in | re-arm button after boot (active low) |
| 1 | MOT_ISENSE | ADC1_CH0 | motor current, IBT-2 module R_IS/L_IS via 100R + 1k + clamp |
| 2 | BAT_OK | in | UPS battery OK (high = OK) |
| 4 | V24_SENSE | ADC1_CH3 | 24 V rail via 100k/10k, reported in status |
| 5 | MOT_IN_A | out | OPEN drive |
| 6 | MOT_IN_B_MCU | out | CLOSE drive (PCB ANDs with BEAM_CLEAR) |
| 7 | MOT_EN_MCU | out | bridge enable (PCB ANDs with ESTOP_OK) |
| 8 | ESTOP_OK | in | high = E-stop loop healthy |
| 9 | LIM_UP_OK | in | NC switch: low = reached or wire break |
| 10 | LIM_DN_OK | in | same polarity |
| 11 | BEAM_CLEAR | in | high = clear; low = broken or cable cut |
| 12 | PRESENCE | in | high = occupied (**assumed polarity**) |
| 13 | AC_OK | in | high = mains OK |
| 14 | WDT_WDI | out | TPS3823 kick |
| 15 / 16 / 17 | RS485_DI / RO / DE | UART1 TX / RX / DE+/RE | RFID reader |
| 18 | BUZ_CTRL | out | 24 V piezo, high = sound |
| 19 / 20 | USB D- / D+ | USB | programming only |
| 21 | WS2812_3V3 | out | status RGB LED (**HAL stub**) |
| 38 / 39 / 40 / 41 / 42 / 47 | HUB A / B / CLK / LAT / OE / R | out | HUB12 sign (**stub**) |
| 43 / 44 | EDGE_TX / EDGE_RX (TXD0 / RXD0) | UART0 | Edge Node link |
| 48 | K1_EN | out | contactor coil driver (motor power) |
| 3, 35, 36, 37, 45, 46 | NC | | strap / PSRAM pins left unconnected in the schematic |

## 4. Timing budget (TARGETS, none measured)

| Item | Target | Status |
|---|---|---|
| Control loop period | 2 ms | to bench-verify on ESP32-S3 (FreeRTOS tick 1 kHz) |
| Beam break to motor stop request | 1 loop (2 ms) plus 30 ms debounce only on release, none on break | logic tested on host; hardware gate on PCB; stop time to bench-verify |
| Over-current trip | 50 ms hold after 300 ms in-rush blank | threshold is a placeholder; calibrate at 1.5 x running current |
| Tag read window | 400 ms (100 ms settle after first tag) | tune against real reader |
| Edge decision latency (camera + ANPR + fusion + UART) | **300 ms, a TARGET to bench-verify on the Pi 5; not achieved or measured** | open |
| Edge Node internal reply deadline | 600 ms (fallback if the camera has no plate) | design value |
| Controller wait for decision | 1000 ms, then FALLBACK | design value |
| Heartbeat | 1 s send, 3 s time-out, 3 s recovery | SAFETY F9 |
| Travel time-out | 1.5 x nominal (nominal 4000 ms placeholder) | SAFETY F12 |

## 5. Edge Node behaviour

Plate normalisation (`plate.py`): strips spaces, dashes and dots; folds case; tries every character-class layout of the right length (standard `SS d{1,2} L{1,3} d{1,4}` and BH `YY BH dddd L{1,2}`), fixes O/0, I/1, B/8, S/5 (Z/2, G/6 opt-in) where a character sits in the wrong class, and picks the layout with the fewest corrections. A reading that is legal as written is never "corrected" (`MH1ZAB1234` stays). State codes come from a snapshot list; unknown state is parsed but not valid. BH letter restrictions are not enforced (unverified).

Fusion cases (`fusion.py`, each covered by a test and a simulator scenario):

| Case | Result |
|---|---|
| tag + plate agree (edit distance 0, OCR conf >= 0.5, inside +-500 ms) | GRANT / MATCH |
| tag matches, plate differs by 1 char | FALLBACK / SOFT_MATCH (guard) |
| confident plate (>= 0.8) disagrees with tag record | FALLBACK / TAG_PLATE_MISMATCH, alert, possible clone |
| mismatch with plate conf < 0.8 | FALLBACK / LOW_CONFIDENCE (misread is likelier than a clone) |
| plate conf < 0.5 | FALLBACK / LOW_CONFIDENCE |
| TID registered and different | FALLBACK / TID_MISMATCH, clone alert (needs TID from the reader; not yet carried on the serial link) |
| tag only | FALLBACK / TAG_ONLY (policy flag can allow GRANT) |
| plate only, resident pass flag (two-wheelers) | GRANT / PLATE_ONLY_PASS |
| plate only, registered with a tag | FALLBACK / PLATE_ONLY_NO_TAG |
| plate only, unknown or 1 edit from a known plate | FALLBACK / UNKNOWN_PLATE or SOFT_MATCH |
| tag outside +-500 ms of this lane's plate, or below RSSI gate | tag ignored (flag CROSS_LANE_TAG_IGNORED), plate-only path |
| blacklisted plate or EPC | DENY / BLACKLIST (the only DENY; controller treats it like FALLBACK) |
| plate 1 edit from blacklisted plate | FALLBACK / BLACKLIST_NEAR, alert |
| inactive registration, unknown tag, unparseable plate, nothing read | FALLBACK with matching reason |

Property test: over a 45-input grid GRANT occurs only for MATCH (distance 0, both signals) or PLATE_ONLY_PASS.

Clock handling: the controller reports tag peak time in its own clock; the Edge Node converts it using the offset measured at the `VEH` message (assumes UART latency of a few ms).

Storage: SQLite allow-list (WAL), near-plate search through a deletion-neighbourhood index (replaced a full scan, found when the first benchmark was far too slow; checked against brute force). Offline queue is store-and-forward, oldest first, exponential back-off, head-of-line blocking (a test found younger events overtaking a backed-off one; fixed), permanent rejections parked. `event_id` is the idempotency key end to end; a lost ack followed by a retry produces exactly one mock debit (tested).

Privacy: events (queue, ledger) carry only salted HMAC tokens. The allow-list itself stores plaintext plates and EPCs because edit-distance matching cannot run on tokens; it is meant to sit on the LUKS-encrypted node disk. This is a narrower reading of the FMEA #10 "plates stored only as HMAC token" wording and should be reviewed. The salt in the code is a demo value.

Mock ledger (`netc_mock.py`): in-process, no sockets, `mock: true` in every response, flat demo fee.

## 6. Test summary (logs in `firmware/test_logs/`)

| Suite | Result |
|---|---|
| Lane controller, g++ 13.3 `-std=c++17 -Wall -Wextra -Wpedantic -Werror` | 53 tests, 1,717,877 checks, 0 failures |
| Same suite under AddressSanitizer + UBSan | 53 tests, 0 failures |
| Edge Node `pytest` | 86 tests passed |
| Scripted scenarios (`parkflow_edge.simulator`) | 21 of 21 matched their scripted expectation |

What the C++ tests cover: every state transition, happy path, plate-only, stale decision, lockout, beam and presence reversal, over-current blanking and hold, reversal lockout, open/close time-outs, limit conflict, E-stop and re-arm, link loss and recovery hysteresis, boot grace, fail-secure policy, mains loss, parser resync and CRC rejection, link checksums, LED/buzzer patterns, debounce, watchdog overrun, closed-loop runs against a mock barrier, and a seeded fuzz (20 seeds x 60,000 ticks) asserting: CLOSE only with beam clear, no presence, E-stop healthy and state BARRIER_CLOSE; no motion or contactor with E-stop open; no direct direction flip. The fuzz is checked for non-vacuity (reaches all 12 states, 35k+ close ticks). Two deliberate code mutations (removing the beam reversal; removing the over-current hold) were caught by the tests. The mock barrier's rates and currents are fixtures, not measurements.

### Fusion CPU time
**Host CPU, not target hardware, not an end-to-end latency.** `fuse()` only (plate normalisation, in-memory SQLite lookups, decision), 20,000 calls, 5,000-plate allow-list, Intel Xeon 2.1 GHz VM, Python 3.13: mean 0.038 ms, median 0.027 ms, p95 0.047 ms, p99 0.073 ms, max 8.1 ms (single outlier, probably scheduler). Excludes camera, ANPR inference, RFID read, UART and disk. **The 300 ms decision-latency target is not demonstrated by this number**; it must be bench-verified on the Pi 5 with the real pipeline.

## 7. Known limitations

1. `hal_esp32s3/` has not yet been compiled with ESP-IDF or run on target. WS2812 and HUB12 are stubs; ADC mV conversion is an uncalibrated estimate; reader baud rate is a placeholder.
2. Reader protocol is unverified (see section 2). Reader RSSI units are unknown, so the RSSI gate is off by default.
3. Schematic vs SAFETY F3: SAFETY says a hardware comparator also gates the H-bridge on over-current, but the schematic script only routes `MOT_ISENSE` to the ADC. Over-current protection is therefore firmware-only (2 ms loop, 50 ms hold). Either the PCB needs the comparator or SAFETY needs rewording.
4. No dedicated re-arm button in the schematic; the BOOT button (GPIO0) and an Edge command are used instead.
5. No photo-beam self-test per cycle (no transmitter-control pin on the schematic), although SAFETY cites EN 12978 for it.
6. `PRESENCE` polarity is assumed (high = occupied). Unlike the beam, a cut presence cable reads as "vacant", so presence is not fail-safe.
7. Boom drifting up while IDLE (wind back-driving) is not detected. A CLOSE_TIMEOUT leaves the boom mid-travel and the contactor off until a technician resets it.
8. Fail-open leaves the lane open and unauthenticated during any Edge Node outage; sites may need fail-secure.
9. Gen2 TID is supported in fusion but not carried on the serial link yet. The Python and C++ link code are cross-checked by one shared golden vector, not by a shared test suite.
10. Plate rules: state list is a snapshot, BH letter rules are not enforced, 2-row and decorative plates are the OCR model's problem.
11. All thresholds (over-current mV, travel time, windows, confidences) are placeholders until commissioning and bench tests. The fuzz is seeded random testing, not formal verification. No EMC, timing-on-target or endurance testing has been done.
