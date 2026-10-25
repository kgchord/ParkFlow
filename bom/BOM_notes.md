# ParkFlow BOM: assumptions, open quotes and risks

Prices first checked on 24 Oct 2026. About 40 vendor pages were re-checked on 25 Oct 2026 (column P of the BOM sheet shows which), and the pages added in the 25 Oct design update are listed in the Sources sheet. Full detail is in `ParkFlow_BOM.xlsx`, which has three sheets: BOM, Summary and Sources (89 URLs). The workbook was recalculated in LibreOffice on 25 Oct 2026: every formula evaluates and no cell shows an error.

**What changed in the 25 Oct design update (totals moved from ₹1,54,057 to ₹1,83,845).** The BOM was brought into line with the design: (1) the supply is now the Mean Well LRS-200-24 (+₹800) because the 24 V bus peak was 8.66 A against 6.5 A; (2) the 24 V relay module is replaced by the LC1D09BD contactor the schematic and the E-stop loop need (+₹927); (3) the lane-controller lines that did not match the schematic (MAX3485, XL4015, AP2112K) are set to quantity 0 and replaced by one estimate line for the schematic parts (₹2,500–5,000); (4) a separate IP65 power box takes the 24 V supply out of the Edge Node box for thermal reasons (+₹295); (5) the 9 GAP lines are priced or given estimate ranges, so for the first time the total contains every line; (6) the 24 V fail-open backup is dropped from the baseline (fail-in-place with a hand release; see `docs/OPEN_DECISIONS.md` D2) and a storm-lock pin line is added. Earlier the same day: the BOM buys an 80x80 pole (₹8,673; section data still to be confirmed) and uses 1 m of 40x40 for the arms; the Pi UPS line is an estimate, not a verified price.

## Totals (computed from the LibreOffice-recalculated workbook; the Summary and BOM grand totals agree)

| Subsystem | Priced lines | Estimates (low–high) | Budget (priced + high) | Unpriced GAP lines |
|---|---|---|---|---|
| Edge Node | 43,020.00 | 5,099–5,499 | 48,519.00 | 0 |
| Lane Controller PCB | 4,476.54 | 3,300–6,500 | 10,976.54 | 0 |
| UHF RFID Reader | 26,100.60 | – | 26,100.60 | 0 |
| ANPR Camera | 4,071.00 | – | 4,071.00 | 0 |
| PoE Switch | 5,310.00 | – | 5,310.00 | 0 |
| Occupancy Nodes x4 | 4,760.00 | 800–1,400 | 6,160.00 | 0 |
| P10 LED Sign | 1,536.00 | – | 1,536.00 | 0 |
| Barrier Drive | 10,703.94 | 1,700–4,100 | 14,803.94 | 0 |
| Power & Protection | 8,423.32 | 2,350–4,700 | 13,123.32 | 0 |
| Mechanical | 16,431.26 | 10,100–20,100 | 36,531.26 | 0 |
| **Total** | **1,24,832.66** | **23,349–42,299** | **1,67,131.66** | **0** |
| Contingency 10% | | | 16,713.17 | |
| **Grand total** | | | **1,83,844.83** | |

The Edge Node estimate range is 5,099–5,499 because the Pi 5 UPS (4,599, last seen in a related-products block, not reproduced on 25 Oct) is carried as an estimate with low = high.

**How to read the totals.** 18 of the 72 lines (₹23,349–42,299, counted at the top of the range) are estimates with no vendor page behind them; the biggest are the barrier housing (₹5,000–9,000), the heat sink and sun hood (₹2,000–4,500) and the schematic-only PCB parts (₹2,500–5,000). The ranges are sized from STEP masses and the aluminium and steel listings already in the BOM, not from quotes. Three items are decisions, not prices, and are **not** in the total: a ≥ 30 N·m production gearmotor, a 24 V battery buffer, and an industrial PoE switch (all in `docs/OPEN_DECISIONS.md`). If they are all taken, the budget rises by an amount that cannot be stated until quotes arrive.

## Assumptions
1. **GST.** All unit costs include 18% GST. Where a page said "excluding all taxes" (IndiaMART) or did not state GST (LionCircuits parts, some IndiaMART listings), we added 18% on top. This is conservative and is recorded in each row's Notes. (25 Oct: the 12 V mini UPS listing does say "excluding all taxes"; the number used is unchanged.)
2. **Estimates.** Estimate lines have no unit cost: the Unit cost column says "quote needed", and the range sits in a separate column labelled as an estimate. The base budget counts estimates at the top of their range. Ranges for the base plate and gussets were set for aluminium plate and have not been re-estimated for 16 mm mild steel. The ranges added on 25 Oct (barrier housing, heat sink and hood, vent and glands, thermostats, drive-train machined parts, storm-lock pin, schematic parts) are explained in each row's Notes.
3. **Not included.** Shipping, courier and IndiaMART freight are excluded. Most Bengaluru webstores ship free above a threshold.
4. **Local flag.** "Local-Delhi NCR" means the seller is in Delhi, Gurugram, Noida, Faridabad or Ghaziabad, near the team in Sonipat. "Domestic" means Bengaluru, Mumbai/Navi Mumbai or Chennai.
5. **Lead times.** These are calendar days to arrival in Sonipat. Where a page stated dispatch time (e.g. "ships in 7–10 days", "ships within 3 days", "1 week") we used it. For in-stock Bengaluru webstore items we assumed 4 days, and for out-of-stock items 14 days. Estimate lines carry a guess of 3 to 10 days.
6. **No NVMe.** The AI HAT+ uses the Pi 5's single PCIe lane, so the Edge Node boots from a 128 GB microSD. NVMe would need a PCIe switch HAT.
7. **Pi 5 power.** Inside the enclosure the Pi 5 runs from 24 V through an XL4015 buck set to 5.1 V. The 27 W USB-C PSU is only for the bench. The XL4015 page itself recommends 2 to 3 A for passive cooling and a heatsink above 3 A, so a 5 A Pi load is a target to be bench-verified. An industrial DC-DC is the fallback.
8. **Quantities.** Extrusion is priced per metre (80x80: 3 m; 40x40: 1 m; 20x20: 2× 600 mm). The boom tube is priced per kg (about 2.6 kg for one stock length, estimated from section geometry). The photo-beam is costed as 2 pieces (emitter + receiver).

## Sourcing-rule compliance
- **Rejected for city:** Hubtronics (its own contact page and GSTIN 27… show Pune) and Robu.in (Pune). Also rejected: Idis India (Ahmedabad), CP Plus listings from Ahmednagar and Pune, Hikvision listings from Dehradun and Srinagar, Sumit Engineering (Ahmedabad), Global Automate (Pune), Apcon (Bhiwadi, Rajasthan).
- **City verified from the vendor's own page:** Probots (Nagarbhavi and Koramangala, Bengaluru; re-checked 25 Oct on the product pages), Robocraze (Kalyan Nagar, Bengaluru), Thingbits (Mulund W, Mumbai; re-checked 25 Oct), PrimeABGB (Lamington Rd, Mumbai), ID Tech Solutions (Udyog Vihar, Gurugram; via TradeIndia, re-checked 25 Oct).
- **City from IndiaMART seller card only (weaker evidence; re-checked 25 Oct for the ones marked):** Eco Track*, Samriddhi*, Pioneer Enterprises*, Super Electricals*, Gokal Chand* (New Delhi); SBM Electric*, Simplex Profilo* (Gurugram); Enervation* (Noida); Reliable Laser Works (Faridabad); Secure Bazaar* (Chennai); Accruepole* (Mumbai); Pixel Led* (Navi Mumbai, alternative only).
- **Lines that do not yet meet the rule with evidence (flagged):**
  - **LionCircuits, 8 lines** (ESP32-S3, SM712, PC817C, PCB fab, passives, schematic parts estimate; MAX3485 and AP2112K are now quantity 0): the site gives no street address. Bengaluru is inferred from its 080 phone number and its Karnataka facilities. Confirm before ordering, or buy the same parts from a vendor with a printed Bengaluru address (Probots lists an ESP32-S3 board).
  - **L&T-SuFin MCB, 1 line:** the seller, SV Nexus Enterprises, shows no city, and the MOQ is 10 pieces. Buy the MCB over the counter in Delhi's electrical market instead.
  - **Moglix wiper motor, 1 line:** the packer's address is in Shahdara, New Delhi, but Moglix's dispatch warehouse is not shown (re-checked 25 Oct, still not shown).
  - **10 estimate lines with no named seller** (5 V node adapters, wiring, DIN rail and terminals, structural fasteners, counterweight and shear pins, thermostats, drive-train machined parts, storm-lock pin, heat sink and hood, vent and glands) say only "Delhi NCR market" or "to be named". A named Delhi NCR, Bengaluru, Chennai or Mumbai seller is required for each before purchase.
- **New 25 Oct sellers (city from the IndiaMART seller card only):** Prem Associates (New Delhi, contactor), Golf Automation Solutions (Noida, loop detector), Arihant Enterprises (Chennai, bearings), Trademinds (Mumbai, Mulund West, RCCB), Jenshri India (New Delhi, power box), AR Industries (Noida, cable duct).
- **Authorised distributors (rule 2):** this is not met with evidence.
  - Raspberry Pi: element14 India is an authorised distributor (Rs 16,718), but its stock ships from Singapore/UK (re-checked 25 Oct: 3–5 business days from SG, 4–6 from UK), so it is listed only as an alternative. Not yet verified whether Probots or Robocraze are Raspberry Pi Approved Resellers.
  - Mean Well: no authorised distributor page found.
  - Espressif: LionCircuits is a parts marketplace, not a confirmed authorised distributor.
  - Action: confirm with Raspberry Pi's approved-reseller list for India and Mean Well India before ordering.
- **Imported items:** none in the primary BOM. The only imported option is the element14 Pi 5 alternative (plus possible customs duty and IGST at clearance).

## Lines whose specification was corrected on 25 Oct
| Line | Was | Now |
|---|---|---|
| Pi 5 UPS | "Waveshare UPS", Rs 4,599 verified | Geekworm X1202; the Probots page shows the X1202-C1 case at Rs 2,649, and Rs 4,599 is kept only as an estimate |
| Gantry pole | 40x40, 3 m | 80x80 pole (3 m, Rs 2,450/m + GST) and 1 m of 40x40 for arms |
| Base plate / gussets | Al 6061 10 mm, Al gussets | MS E250 16 mm and MS gussets plus 4 socket cheeks (re-quote) |
| RFID reader spec | "RS485, IP65, EPC Gen2" | Those three are only on TradeIndia or from the earlier check; IndustryBuying shows Wiegand + RS232, no IP rating |
| SPD spec | "Uc 320 V" | Rated voltage 320 V; Uc not listed |
| E-stop spec | "IP65" | "Waterproof"; no IP rating on the page |
| Motor note | "18 Nm meets the 10-20 Nm target" | 18 N·m is below the ≥ 30 N·m specification in CALCS |
| Counterweight spec | "steel block" | 7 plates of 100x60x10 (3.30 kg) |
| 24 V supply (25 Oct) | Mean Well LRS-150-24, 6.5 A | LRS-200-24, 8.8 A (bus peak 7.66 A with a 5 A motor limit) |
| Motor power switch (25 Oct) | 24 V 30 A relay module (conflicting DC rating, no coil-loop topology) | Schneider LC1D09BD contactor, 24 VDC coil |
| Lane-controller parts (25 Oct) | MAX3485, XL4015 and AP2112K lines | quantity 0; one estimate line for the schematic parts (THVD1450, TPS54560, TLV62569, 74AHCT1G08 …) |
| Cable channel (25 Oct) | 40x25 PVC, quote needed | 38x38 PVC duct priced (no 40x25 found in the allowed cities) |

## Items needing a quote (18 estimate lines, ₹23,349–42,299)
18650 cells for the Pi UPS (2 or 4: confirm); Pi 5 UPS board; misc PCB passives and connectors; schematic-only PCB parts; 4× 5 V node adapters; fuse holders and fuses; wiring and cabling (now including the loop-detector loop wire); DIN rail and terminals; bimetal thermostats; laser-cut 16 mm base plate; gussets and socket cheeks; structural fasteners and M12 anchors; counterweight and shear pins; barrier housing; heat sink and sun hood; vent and large glands; drive-train machined parts; storm-lock and manual-release pins.

**Firm up these too:**
- RFID reader: the OEM's TradeIndia price is about ₹14,000 against ₹25,959 on IndustryBuying. A direct quote from ID Tech could save about ₹10–12 k. Ask for RS485, IP rating, the WPC ETA certificate and the India channel plan.
- PCB fab: the ₹799 price is the homepage offer. Get a quote for the real board size.
- 80x80 profile: get the supplier drawing (weight per metre, W ≥ 27 cm³) before ordering. Another vendor lists 4.45 kg/m.
- Contactor and loop detector: the listings do not state the contactor coil power or DC rating, or the detector's relay rating.
- Power box: confirm that the LRS-200-24, LRS-100-12, three DIN breakers and the SPD fit in 250×190×95 mm.

## Risks
| # | Risk | Impact | Mitigation |
|---|---|---|---|
| 1 | Second vendors out of stock on 24 and 25 Oct: Robocraze Pi 5 and AI HAT+, Thingbits BTS7960 and A02YYUW. Primary vendor out of stock: Probots VL53L1X and P10 module, Robocraze 2020 extrusion | Single-source exposure on the critical Pi 5 and AI HAT+ | Order Pi 5 + AI HAT+ in week 1. element14 is the authorised fallback (imported shipment, about 1 week) |
| 2 | Wiper motor: "available on request"; rpm, rated-vs-stall torque, self-locking and stall current not stated; 18 N·m is below the ≥ 30 N·m specification | Cannot be rated for a 15 m/s operating wind (margin 1.56) | Decided for the demo: operate only in wind ≤ 12 m/s (margin 2.2), self-locking not assumed, storm-lock pin for the 93 N·m survival gust. A ≥ 30 N·m motor stays open (OPEN_DECISIONS D1). The Probots 6280 (about 4.7 N·m) and 5840 (4.4 N·m) are far too weak |
| 3 | IndiaMART specs inconsistent: camera spec table says "Analog"; PoE, RTSP and IR wavelength not listed; PoE budget of the switch not listed; RFID RS485 not listed on IndustryBuying | Wrong part delivered | Get written confirmation of PoE/RTSP, 850 nm IR, RS485 and 865–867 MHz before payment |
| 4 | Enclosure is 300×300×210, not the 300×400×180 used by CAD and MATERIALS | DIN layout and sink window not checked in the bought box. Thermal: box size changes the result by only 0.6 K; sealed 61.8 °C, with sink 54.2 °C, with the supply moved out 52.3 °C (48.1 °C counting radiation) against the 50 °C HAT+ rating | Bought box kept (CALCS §5); supply moved to a separate power box; CAD owner to re-check the layout (OPEN_DECISIONS D6); the AC4 soak decides |
| 5 | Schematic-only PCB parts have no vendor page behind the ₹2,500–5,000 estimate | Budget and lead time uncertain | Quote against the generated netlist; the 600 mA AP2112K concern is gone because the schematic uses a 2 A TLV62569 buck |
| 6 | E-stop contacts rated 1 A DC | Cannot break motor current directly | E-stop is in the 24 V coil loop of the LC1D09BD contactor (coil current about 0.2 A assumed) and also forces the IBT-2 enables low through U9/U19. Confirm coil power and the DC rating of the contactor on the datasheet |
| 7 | PETG outdoors (no ASA found at an allowed vendor) | UV degradation over months; MATERIALS assumes ASA | Acceptable for a 4-month demo; paint or replace before Stage 3, or change MATERIALS |
| 8 | Unbranded SPD from IndiaMART (Uc not listed) | Unknown protection level | Ask for a datasheet, or substitute an OBO/Phoenix unit from the Delhi electrical market |
| 9 | Prices change, and IndiaMART prices are "approximate" | Budget drift | 10% contingency; re-check prices on the PO date |
| 10 | 18 estimate lines (₹23,349–42,299) with no vendor page; 3 open decisions (production motor, 24 V buffer, industrial PoE switch) not in the total | Budget could still move by more than the contingency | Quote in week 1; update the BOM before the design freeze on 27 Nov |
| 11 | LRS-200-24 (8.8 A) feeds motor, controller and Pi; peak 7.66 A relies on a 5 A motor limit | A stalled wiper motor above 5 A trips the supply (overload starts at 110 %) | Bench-test stall current; set the firmware current threshold (placeholder 1500 mV is about 14 A and must be changed to about 540 mV); consider a hardware limit |
| 12 | BTS7960 module motor supply is 5.5–27 V (one page also says 21–30 V) | The LRS-200-24 trim range is 21.6–28.8 V and motor kick-back can exceed 27 V | Keep the trim at 24 V, add the SMCJ28A + 470 µF at the module terminals (in the misc line), bench-check the supply-pin transients |

## Evidence quality (72 lines)
| Evidence type | Lines |
|---|---|
| Price read from the vendor's own product page | 33 |
| Price read from a store or IndiaMART listing page | 18 |
| Price read from a related-products block on a vendor page | 2 |
| Vendor homepage offer (PCB fab) | 1 |
| Estimate, quote needed | 18 |
| GAP, not priced, not in budget | 0 |
| Price from a search snippet only | 0 |

(Three of the priced lines are the superseded MAX3485, XL4015 and AP2112K at quantity 0.)

**Note:** ASA filament, Mean Well authorised dealers and 400×300 enclosure dealers have not been searched further yet. The 25 Oct re-check of about 40 pages found no price or stock change on any priced line except the Pi 5 UPS. The 25 Oct design update added the pages for the contactor, RCCB, loop detector, bearings, power box, cable duct and LRS-200-24; no usable page was found for the thermostats, the 200x150 heat sink, the vent and glands (heat-sink pages found list no size or price).
