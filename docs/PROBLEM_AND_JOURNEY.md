# Problem Context and User Journey

Source: `docs/ParkFlow_Stage1.pdf` (Stage 1 submission), with external figures re-checked where noted. Anything marked **Target** is a Stage 1 internal projection, to be validated in the pilot. None of it is a measured result.

---

## Problem Context

**Title:** ParkFlow: "Just Drive" parking for India
**Track:** Smart Mobility / Urban Infrastructure
**Core innovation (1 line):** An on-site Edge Node fuses the car's existing FASTag (UHF RFID) with its number plate (ANPR) in under 300 ms (target), so the barrier opens without a stop, a token or a new wallet.

### KPI tiles

| Tile | Value | Source |
|---|---|---|
| FASTag is the toll rail India already built | **>98 %** of National Highway user fees are collected via FASTag | MoRTH, reported by Times Drive, 30 Jan 2026 [D1]. This is a share of toll payments. Stage 1 §2 turned it into "close to 98 percent of those same vehicles carry a tag"; the source does not say that, and two-wheelers have no FASTag. The share of vehicles in a given parking lot that carry a working tag is unknown and is measured at the pilot |
| Tags issued | **11.86 crore** FASTags issued (as of Dec 2025) | MoRTH via Times Drive [D1] |
| Time lost at a manual barrier | **45 to 90 s** per vehicle, per gate | Stage 1 §2 / §4.4 baseline. Stage 1 gives no source: treat as an unsourced typical figure until we time a manual gate |
| Manual lane capacity | **40 to 60 vehicles/h** vs **800 to 1,000+ veh/h target** | Stage 1 §5.2 (target, to be confirmed in pilot) |

**Target beneficiary:** Daily commuters into tech parks and malls (e.g. "Priya, tech-park employee, Bengaluru"). Also facility operators (mall managers, tech-park/SEZ developers, RWAs) and municipal lots (Stage 1 §4.1).

### Before-state flow (today)
`Slow & stop` → `Take paper token` → `Queue at peak` → `Circle for a slot` → `Find token, pay cash/card, wait for barrier`
*8 to 12 min of active friction per round trip · cash handled · no digital record* (Stage 1 §8)

### Public-search disclosure: competitors (Stage 1 §7.1)
| Player | What they do | Gap ParkFlow targets |
|---|---|---|
| Legacy token / boom-barrier vendors | Hardware only, regionally fragmented | No identity or billing layer |
| Park+ | Car-ownership super-app: FASTag, ANPR, parking, challans | App-led; ParkFlow requires **tag + plate fusion** at the edge |
| Get My Parking / ParkingRhino | IoT smart-parking for municipalities, airports, campuses | Single-modality per site |
| City aggregators (e.g. GetParking) | ANPR-based off-street aggregation in a few metros | ANPR-only; weak against misreads |

*Based on public company information as disclosed at Stage 1; figures are self-reported by the companies and indicative.* FASTag-based fuel payment already exists, so ParkFlow does not claim novelty for that use (Stage 1 §6.2).

---

## User Journey (before / after)

| Step | Before: manual grind | After: with ParkFlow | Gain (target) |
|---|---|---|---|
| 1. Arrive | Brake and halt at the barrier | Drive up at normal speed, no braking | Stop removed |
| 2. Identify | Guard hands out a paper/plastic token | RFID + ANPR cross-check on the Edge Node | **< 300 ms** decision (target) vs 45 to 90 s |
| 3. Pass gate | Queue behind other cars at peak | Barrier lifts before arrival, or there is no barrier | Queue **10 to 20+ vehicles → near zero** (target) |
| 4. Park | Circle floors looking for a space | LED sign + app point to a free bay | Minutes of circling removed (target) |
| 5. Exit & pay | Find token, pay cash or card, wait | Auto-debit from FASTag wallet, e-receipt | **< 5 s** per gate (target); 0 cash handled |
| Totals | **8 to 12 min** friction per round trip; 0 % digital record | **< 5 s** per gate; **100 %** of entries/exits logged (target) | roughly **13× to 25×** lane throughput (Stage 1 says ≈ 20×): 40 to 60 → 800 to 1,000+ veh/h (Stage 1 projection, not measured) |

**Persona line (Stage 1 §8):** *Before:* Priya leaves home 20 minutes early to beat the gate queue, stops for a token and circles two basement levels. *After:* she drives through at normal speed, her phone shows a free bay on Level 2, and the fee is debited and receipted by the time she reaches her desk.

**Note:** Targets are Stage 1 internal projections from queueing estimates. The Stage 2 prototype measures decision latency (AC1) and fused accuracy (AC2) at a campus gate pilot in Feb 2027.
