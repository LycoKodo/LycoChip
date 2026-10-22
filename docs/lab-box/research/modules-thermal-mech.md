# Lab Box research: thermal parts and enclosure hardware (mechanical facts)

**TL;DR**
1. The EP4CE6E22 package is a 20 × 20 mm body with leads reaching 22 × 22 mm. Its top sits at most 1.65 mm above the PCB. The exposed pad is on the **bottom**, is ground, and Altera says it is "for electrical connectivity and not for thermal purposes". The heater may touch the moulded top only, so plan a contact face of about **18 × 18 mm or less**, centred.
2. 12 V across 10 Ω is **14.4 W**. That is more than an Arcol HS10 is rated for even on a heatsink (10 W; 5 W in free air). An HS25 is rated for it (25 W) but is 28 × 27.3 mm, wider than the package, so it would overhang the leads. *(Verifier: the HS10's 16.5 × 15.9 mm is only its envelope. Its flat base under the body is about 8.5 mm wide, and its 12 V solder lugs reach about 7 mm past each end, over the leads.)* The steady-state power needed is probably **about 5–8 W**, a rough estimate that has to be measured. Pick R to suit: 15 Ω gives 9.6 W, 22 Ω gives 6.5 W.
3. **PETG has no margin in the heater zone.** Its heat-deflection temperature (HDT, 0.45 MPa) is 68–69 °C, which is the top of the 60–70 °C target. Use ASA (HDT 93–100 °C) or metal in the heater zone and PETG only in the cool zone. PLA's HDT is 57 °C.
4. The KSD9700 body is 20.5 × 7.5 × 3.7 mm (28 × 8.9 × 5.1 mm with its sleeve). It is normally closed, rated 5 A at 250 VAC resistive, with no DC rating published. Opening tolerance is ±5 °C. Mounted on the heater block, a 70 °C part can open at 65 °C, so it **caps the package below about 65 °C**. That makes a 70 °C setpoint impossible: Alex has to pick the thermostat temperature. *(Verifier: the maker's drawing says one lead is joined to the iron shell, so treat the bare shell as live.)*
5. The 40 mm fan (Sunon MF40100V1 datasheet) is 40 × 40 × 10 mm, with Ø4.3 mm holes on 32 mm centres. It moves 8.0 CFM at 0.68 W and is **rated only to 70 °C**, so mount it on the cool inlet side. Cheap fans, DC jacks, fuse holders and thermocouple beads differ between makers, so **buy first, then measure** before fixing those cut-outs.

Confidence tags follow the brief: datasheet | vendor-doc | listing | photo-estimate | derived | unknown.
"Read via mirror" means the manufacturer's own PDF was read from a distributor's copy.

---

## Facts table

| Item | Value | Unit | Source | Confidence | Notes |
|---|---|---|---|---|---|
| **FPGA package** | | | | | |
| Package | 144-pin EQFP, JEDEC MS-026 var. BFB-HD | – | [PKG] p1 | datasheet | Ordering code "E"; copper leadframe; Pb-free finish matte Sn |
| Body size D1 × E1 | 20.00 × 20.00 BSC | mm | [PKG] p1 table | datasheet | Moulded plastic body |
| Lead-tip span D × E | 22.00 × 22.00 BSC | mm | [PKG] p1 table | datasheet | [HB] Table 1-3 also lists E144 as "22 × 22" |
| Lead overhang beyond body, per side | 1.0 | mm | (D − D1)/2 = (22 − 20)/2 | derived | |
| Seated height A (PCB to top) | 1.45 min / 1.55 nom / 1.65 max | mm | [PKG] p1 | datasheet | Top of the package above the PCB surface |
| Body thickness A2 | 1.30 / 1.45 / 1.60 | mm | [PKG] p1 | datasheet | |
| Standoff A1 | 0.05 / 0.10 / 0.15 | mm | [PKG] p1 | datasheet | |
| Lead pitch e | 0.50 BSC | mm | [PKG] p1 | datasheet | |
| Lead width b | 0.17 / 0.22 / 0.27 | mm | [PKG] p1 | datasheet | |
| Lead thickness c | 0.09 – 0.20 | mm | [PKG] p1 | datasheet | |
| Foot length L / L1 | 0.45–0.75 / 1.00 REF | mm | [PKG] p1 | datasheet | |
| Lead coplanarity | 0.08 | mm | [PKG] p1 | datasheet | |
| Exposed pad D2 × E2 | 5.40 nom (5.25–5.55) square, **bottom side** | mm | [PKG] p1 table, p2 "BOTTOM VIEW" | datasheet | |
| Exposed pad purpose | Ground; "for electrical connectivity and not for thermal purposes" | – | [HB] PDF p19, Table 1-3 note (1) | datasheet | The heat path for heating is the moulded top, not the pad |
| Package weight | 1.3 (typ) | g | [PKG] p1 | datasheet | |
| Pin-1 mark on top | "ID dot, or a special feature" near pin 1 | – | [PKG] p1 note, p2 top view | datasheet | Diameter and depth are not given |
| Flat area of the top face | not dimensioned | – | [PKG] | unknown | The drawing gives no top-face size, edge draft or ejector marks. Inspect with a loupe |
| Suggested contact face on the package | ≤ 18 × 18, centred | mm | 20 − 2 × 1 mm margin | derived | A design margin, not a datasheet value |
| Operating junction temperature, C8 (commercial) | 0 to 85 | °C | [DS] p4, Table 1-3 | datasheet | Absolute maximum TJ is −40 to 125 °C ([DS] p2, Table 1-1). That is not an operating range. *(Verifier: Table 1-1 labels that row "Operating junction temperature", but the table is "Absolute Maximum Ratings". Design to 0–85 °C.)* |
| Thermal resistance θJA / θJC, E144 | not found | °C/W | Altera thermal-resistance web page (HTTP 403 when fetched) | unknown | Not in the local handbook or datasheet |
| **Heater (a): aluminium-clad wirewound** | | | | | |
| Arcol HS10 rating | 10 W on standard heatsink; 5 W with no heatsink (25 °C) | W | [ARCOL] p2 | datasheet | Standard heatsink is 415 cm² × 1 mm aluminium |
| Arcol HS25 rating | 25 W on standard heatsink; 9 W with no heatsink | W | [ARCOL] p2 | datasheet | Standard heatsink is 535 cm² × 1 mm aluminium |
| Arcol HS10 / HS25 "typical surface rise, HS mounted" | 5.8 / 4.2 | °C/W | [ARCOL] p2 | datasheet | The column has no unit. *(Verifier, corrected: °C/W is confirmed by the p1 graph's HS15 / HS25 / HS50 points, which read about 5.0 / 4.3 / 2.9 °C/W against the table's 5.1 / 4.2 / 3.0. The HS10 point itself reads about 60 °C at about 7.5–10 W. The graph is too coarse to read "10 W ≈ 58 °C" from it.)* |
| Arcol HS10 outline A × E × C | 16.5 × 15.9 × 8.8 max | mm | [ARCOL] p2 dimension table | datasheet | A = width across the flanges, E = body length, C = height. *(Verifier: this is the **envelope**. The drawing shows the 16.5 width is reached only by two small tabs at diagonally opposite corners.)* |
| Arcol HS10 flat contact base under the body | ≈ D × E = ≤ 8.5 × 15.9 (≈ 135 mm²) | mm | [ARCOL] p2 top and end views; D, E from the table | derived | Added by the verifier. Base width ≈ D is read from the drawing, which is not to scale and does not dimension it. That is about half of 16.5 × 15.9 (262 mm²). **Measure the part that is bought** |
| Arcol HS10 overall length B (with terminals) | 30.0 max | mm | [ARCOL] p2 | datasheet | |
| Arcol HS10 solder-lug reach beyond the body | ≈ (30.0 − 15.9) / 2 ≈ 7.0 per end; lug axis ≤ 4.5 (H) above the base | mm | [ARCOL] p2, B, E, H | derived | Added by the verifier. Centred on the package, the lug tips reach about ±15 mm from centre, against lead tips at ±11 mm. **The 12 V lugs overhang the leads and the PCB** |
| Arcol HS10 holes F × G, Ø L | 11.3 × 12.4 (±0.3), Ø2.4 (±0.25) | mm | [ARCOL] p2 | datasheet | Two holes in diagonally opposite flanges. Ø2.4 does **not** pass M3 (M2 fits). The verifier confirmed that L points at the hole on the drawing. ±0.25 gives 2.15–2.65 mm |
| Arcol HS10 flange thickness K / body width D | 1.8 / 8.5 max | mm | [ARCOL] p2 | datasheet | |
| Arcol HS25 outline A × E × C | 28.0 × 27.3 × 14.8 max | mm | [ARCOL] p2 | datasheet | **Wider than the 20 mm package body**. Body width D = 14.2 max, so the overhang is along the length (E) and at the tabs |
| Arcol HS25 B / holes F × G / Ø L / K | 51.0 / 18.3 × 19.8 / Ø3.2 / 2.6 | mm | [ARCOL] p2 | datasheet | Ø3.2 passes M3. *(Verifier: L is ±0.25, so the hole can be as small as 2.95 mm (derived). An M3 still passes, but it can be tight.)* |
| Arcol HS maximum hot spot | 200; derates linearly to 0 W at 200 °C | °C | [ARCOL] p1 | datasheet | |
| Arcol HS insulation, element to case | 10,000 MΩ min; HS10 voltage proof 1400 V peak / 1000 V rms | – | [ARCOL] p1, p2 | datasheet | The element is isolated, but the **case is bare aluminium. Treat it as a conductor** next to 0.5 mm-pitch leads |
| TE/CGS HSA10 size L × W × H | 36.5 × 21 × 11 | mm | [TE-HSA10] p2 | datasheet | TE rates it at 16 W. **Same size as an Arcol HS15, not an Arcol HS10**, despite the "10" |
| TE/CGS HSA25 size | 51 × 28 × 15 | mm | TE sheet HSA2510KJ, quoted in search results (not opened) | listing | Same size as an Arcol HS25 |
| Vishay RH-10 / RH-25 dimensions | not retrieved | – | vishay.com returned 404 | unknown | Distributors list RH-25 at 26.97 × 19.84 × 13.87 mm (listing). Not used |
| 12 V across 10 Ω | 1.2 A, 14.4 W | – | I = V/R, P = V²/R | derived | At 12.6 V (+5 %): 15.9 W |
| R that keeps full-on power ≤ 10 W at 12 V | ≥ 14.4 Ω (15 Ω → 9.6 W, 0.8 A) | Ω | R = V²/P | derived | |
| R that keeps full-on power ≤ 5 W at 12 V | ≥ 28.8 Ω (33 Ω → 4.4 W, 0.36 A) | Ω | R = V²/P | derived | A heater that falls off its clamp then stays inside the HS10 free-air rating |
| Power needed to hold the package ~40 °C above ambient | roughly 5–8 (assumption-laden) | W | 40 °C ÷ 5.8 °C/W ≈ 6.9 W (see §2) | derived | **Must be measured** with a step test |
| **Heater (b): polyimide (Kapton) film** | | | | | |
| Polyimide heater limit with adhesive backing (PSA) | ~149 °C continuous (film itself ~200 °C) | °C | Omega KH/KHLV pages, quoted in search results (not opened) | listing | |
| Film heater thickness | ~0.2–0.25 | mm | Omega (0.010 in max; kit 0.203 mm), via search | listing | Has no stiffness of its own, so it needs a backing plate |
| 20 × 20 / 25 × 25 mm 12 V 5–10 W pads | not found from a traceable source | – | – | unknown | AliExpress-type listings only. 12 V at 10 W needs 14.4 Ω |
| Watt density, 20 × 20 mm at 10 W | ≈ 16 | W/in² | 10 W ÷ 0.62 in² | derived | Above Omega's top catalogue density (10 W/in², listing). Expect hot spots |
| Adafruit 1481 heating pad | 110.65 × 70.45 × 1.54 mm, 5 V up to 1 A | – | adafruit.com/product/1481 | listing | Fabric heater, far too large. Not a fit. *(Verifier: the same page's description also says "Apply 5–12VDC".)* |
| **Heater (c): PTC (self-limiting)** | | | | | |
| DFRobot FIT0845 | 25 × 20 × 5 mm, 5 V, < 5 W, **100 ± 10 °C**, aluminium tube, insulated | – | [DFR] p3–4 | **listing** *(verifier: downgraded from datasheet)* | The [DFR] PDF is a printout of DFRobot's **store page** (price, cart, "Store /" breadcrumb), not a datasheet. Values confirmed on it. 100 °C is above the 85 °C junction limit. **Not usable** as a heater for this chip |
| 12 V "80 °C" PTC air heater | ~35 × 21 × 5 mm, aluminium shell, 80 °C | – | Zbotic/Robu listings via search | listing | Tolerance unknown. Its 80 °C limit is the built-in safety feature |
| **Thermostat** | | | | | |
| KSD9700 body (iron shell) | 20.5 × 7.5 × 3.7 | mm | [XC-KSD] p2 drawing | datasheet | XC Electronics part KSD9700-100/5JSB/080A |
| KSD9700 with clear silicone sleeve | 28 × 8.9 × 5.1 | mm | [XC-KSD] p2 | datasheet | |
| KSD9700 leads | 80 ± 3 mm, 20 AWG silicone (UL3135), 8 ± 1 mm stripped | mm | [XC-KSD] p2 | datasheet | |
| KSD9700 contact type | Normally closed, auto-reset snap-action bimetal | – | [XC-KSD] p2 ("常闭") | datasheet | |
| KSD9700 rating | AC 250 V, 5 A resistive, 10,000 cycles | – | [XC-KSD] p1–2 | datasheet | **No DC rating given**. *(Verifier: p1 also lists CQC AC 250 V 5 A for 6,000 cycles and UL AC 125 V 5 A for 10,000 cycles. The 10,000-cycle figure at 250 V is TUV's.)* |
| KSD9700 shell is connected to one lead | Drawing callout on one lead: "此线与铁壳体虚接" ("this lead is connected to the iron shell") | – | [XC-KSD] p2 drawing | datasheet | Added by the verifier. 虚接 is loose wording. **Treat the bare iron shell as live**, at that lead's potential, until a multimeter shows otherwise. Clamped bare to a metal spreader, it makes the spreader live too, and the spreader sits within about 1 mm of the leads. Keep the silicone sleeve on (rated −40 to 230 °C, [XC-KSD] p4) or add Kapton |
| KSD9700 open / reset (100 °C part) | 100 ± 5 / 80 ± 10 | °C | [XC-KSD] p1–2 | datasheet | Gap between opening and re-closing is about 20 °C |
| KSD9700 sensing face | the **unprinted** face ("印字面在非感温面") | – | [XC-KSD] p2 | datasheet | Put the unprinted face against the heater block |
| KSD9700 contact R / insulation | ≤ 50 mΩ / ≥ 100 MΩ at 500 VDC; 1450 VAC for 1 min | – | [XC-KSD] p1 | datasheet | |
| KSD9700 70 °C part, opening window | 65–75 if it has the same ±5 °C tolerance | °C | ±5 °C taken from the 100 °C drawing | derived | Check the drawing for the part actually bought |
| KSD9700 reset, 60 / 80 °C parts | 40 ± 10 / 60 ± 10 | °C | uelectronics.com listing via search | listing | Interpolating, a 70 °C part resets at about 50 ± 10 °C |
| KSD301 | Ø16 disc, 250 V 10 A, 6.3 mm tabs, ~33.4 × 16 × 18.9 overall | mm | Alibaba/robu listings via search | listing | Flange hole spacing not found. Bulkier than the KSD9700 |
| **Thermocouple** | | | | | |
| Adafruit 270 K-type, glass-braid insulated | 1 m long, 1.45 mm thick, up to 500 °C, bare bead | – | adafruit.com/product/270, via search | listing | Bead diameter **not stated** |
| M6 ring ("washer") K-type probe | M6 ring terminal, 0–600 °C, fibreglass with stainless braid, 1 m | – | protosupplies.com M6 ring probe | listing | Ring inner/outer diameter and thickness not stated |
| MAX31855 with a grounded junction | reports a short-to-GND fault; it does not work with grounded thermocouples | – | Arduino forum and Zanduino wiki via search | listing | The bead must be electrically isolated from grounded metal |
| MAX31855 T− pin, SCG fault | T−: "Do not connect to GND". Bit D1 (SCG) = 1 when the thermocouple is shorted to GND; D16 = any fault | – | [MAX31855] p7 pin description, p10 Table 2 | datasheet | Added by the verifier. This upgrades the row above: the datasheet forbids grounding T−. "Does not work with grounded thermocouples" is still Adafruit/forum wording (listing) |
| **Fan** | | | | | |
| Sunon MF40100V1-1000U-A99 frame | 40 ± 0.5 square × 10 (+0.5/−0) | mm | [SUNON] p6 | datasheet | |
| Sunon hole pattern | 4 × Ø4.3 ± 0.3 on 32 ± 0.3 centres | mm | [SUNON] p3, p6 | datasheet | Sunon recommends M4 machine or Ø5 self-tapping screws |
| Sunon electrical | 5 VDC (3.5–6 V), 136 mA (157 max), 0.68 W, 7000 rpm ± 15 % | – | [SUNON] p3–4 | datasheet | 2-wire. The -G99 variant adds a tach wire (listing) |
| Sunon airflow / static pressure / noise | 8.0 CFM / 0.19 inH₂O / 27.3 dB(A) | – | [SUNON] p4 | datasheet | 8.0 CFM ≈ 13.6 m³/h (derived) |
| Sunon operating temperature | **−10 to +70** | °C | [SUNON] p3 | datasheet | The fan must breathe cool inlet air |
| Sunon leads | 300 ± 10 mm, UL1007 26 AWG | mm | [SUNON] p6 | datasheet | Auto-restart after a stall; polarity protected ([SUNON] p4) |
| Noctua NF-A4x10 5V PWM | 5000 rpm max (1050 rpm at 20 % PWM, 0 at 0 %), 8.9 m³/h (5.24 CFM), 1.95 mm H₂O, 19.6 dB(A), 5 V (max 5.5 V) | – | noctua.at spec page via search (fetch got HTTP 429) | listing | 4-pin PWM |
| 4-wire PWM fan interface | PWM 25 kHz (21–28 kHz); tach open-drain, 2 pulses/rev; PWM pin pulled up inside the fan (≤ 5.25 V) | – | Intel 4-Wire PWM Fan spec rev 1.2/1.3 (mirror), via search | listing | *(Verifier: the mirror returned HTTP 403, so it was confirmed only through a search summary. That summary also says the spec pulls the tach up to 12 V (max 13.2 V) on a motherboard and is written for 12 V fans. An open-drain tach can be pulled up to 3.3 V instead. Whether a given 5 V PWM fan follows this spec is UNVERIFIED.)* |
| 3-wire fan switched low-side by PWM | tach pulses get chopped by the PWM. Fix with "pulse stretching" or use a 4-wire fan | – | Microchip SmartFusion DC fan control app note; TI SPRT839, via search | listing | See §5 |
| **Panel hardware** | | | | | |
| 5.5 × 2.1 mm panel DC jack, panel hole | 7.8–8 (small DC-022B type) up to 12–12.7 (round, nut type) | mm | sigmanortec, protosupplies (12 mm hole, 14 mm OD, panel ≤ 7.9 mm), RS PRO (M12.7 thread) | listing | **Measure the part that is bought** |
| Switchcraft 712A (2.5 mm pin) | 0.313 in (7.95 mm) hole, panel ≤ 0.125 in (3.2 mm) | – | Switchcraft catalogue (e-sonic copy), via search | listing | Wrong pin for a 2.1 mm plug. Warning only |
| Inline ATO blade-fuse holder | ATO fuse 19.1 × 5.1 mm; holder 20 A max, 16 AWG, ~3.5 in leads | – | Littelfuse FHAC series, via search/DigiKey | listing | |
| M205 (5 × 20 mm) panel fuse holders (Jaycar) | SZ2028 Ø19.0 × 39.8; SZ2030 Ø15.5 × 37.0; SZ2034 14.8 × 34.2 | mm | jaycar.com.au listings via search | listing | Panel cut-out not stated. Measure |
| Heater fuse load current | 1.2 A at 10 Ω, 0.8 A at 15 Ω | A | V/R | derived | Fuse value is a wiring decision |
| Panel USB-B to micro-B (Adafruit 937) | ears 27–29 mm apart (sources disagree), 2 × M3 × 12 mm, wall 3.2–6.4 mm | – | Proto-PIC listing; Adafruit 937 sheet via search | listing | |
| Panel micro-B to micro-B (ADA3258) | 4-40 screws, 18 mm apart | – | via search | listing | Core Electronics stocks it |
| **Fasteners** | | | | | |
| CNC Kitchen M3 standard insert | L 5.7, outer Ø4.6, tip Ø3.9, **hole Ø4.0**, min wall 1.6 | mm | 3djake CNC Kitchen M3 standard page | listing | |
| CNC Kitchen M3 short insert | L 3.0, otherwise as standard (hole Ø4.0) | mm | 3djake via search | listing | |
| CNC Kitchen M3 "Voron" insert | L 4.0, outer Ø5.0, hole Ø4.4, min wall 1.3 | mm | 3djake via search | listing | |
| ruthex M3x5.7 (RUT-GE-M3x57-001) | D1 4.6, D2 3.9, D3 4.0, L 5.7, W min 1.6 | mm | 3djake ruthex page | listing | Same numbers as the CNC Kitchen standard insert |
| Insert blind-hole depth | ≥ L + 1 (standard insert → 6.7; short → 4.0) | mm | [CNCK] blog ("about 1 mm deeper") | derived | Straight hole, no taper. Print a test coupon |
| Insert boss outer Ø (minimum) | ≥ 4.0 + 2 × 1.6 = 7.2 | mm | from min wall | derived | |
| Insert iron temperature | print temperature + 10–20; PLA ~225, PETG ~245, ABS ~265 | °C | [CNCK] blog | listing | ASA not given. Derived: ASA nozzle 240–270 + 10–20 gives about 260–280 |
| M3 clearance hole (ISO 273) | fine 3.2 / medium 3.4 / coarse 3.6 | mm | Optimas table, via search | listing | Printed holes come out undersize. 3.4 is a good default |
| M3 socket cap (ISO 4762) | head Ø5.5 max (−0.18), height 3.0 max (2.86 min), 2.5 mm hex key | mm | fasten.it / engineersedge ISO 4762, via search | listing | |
| M3 hex nut (ISO 4032) | 5.5 AF (5.32–5.5), 2.4 high max (2.15 min), 6.01 across corners min | mm | fasten.it ISO 4032, via search | listing | Nut trap ≈ 5.7–5.8 AF × 2.6 deep (derived: +0.2–0.3 mm) |
| M3 brass F-F hex standoff | 5 mm across flats (Harwin R30-10xx), lengths 5, 6, 8, 10, 12, 14, 16, 18, 20 | mm | RS Harwin listings | listing | DigiKey lists "5.50 mm hex OD", which conflicts. Measure |
| Harwin M3 F-F brass hex, 10 mm (verifier) | **R30-1001002: 5.00 A/F; R30-1011002: 5.50 A/F**. Both M3 F-F, 10 mm, nickel-plated brass | mm | harwin.com/products/R30-1001002 and /R30-1011002 | datasheet | Added by the verifier. This **corrects** the row above: both hex sizes are in Harwin's own range, so the DigiKey 5.50 is a different part, not a conflict. Size bosses and spanner clearance for 5.5 A/F (≈ 6.35 mm across corners, derived 5.5 / cos 30°). The list of lengths remains a listing |
| **Window** | | | | | |
| Clear acrylic stock | 2 and 3 mm common; 3 mm cast ~300 × 200 mm for about AUD 3.91 | – | koenigmachinery.com.au listing via search | listing | Price unverified. Sheet thickness varies, so measure before sizing the groove |
| **Thermal interface** | | | | | |
| Arctic TP-3 silicone pad | 0.5 / 1.0 / 1.5 mm; −40 to 150 °C; electrically non-conductive | – | scan.co.uk / inside-tech listings via search; **verifier: arctic.de/en/TP-3/ACTPD00052A** | **datasheet** *(verifier: upgraded; maker's own page)* | Arctic's page gives 0.5 / 1.0 / 1.5 mm, "Continuous Use Temperature −40~150 °C", "electrically insulating", volume resistance 2.69 × 10¹² Ω·cm and 55 Shore OO. **Arctic publishes no thermal conductivity**, so the 6 W/m·K figure is a reseller claim (UNVERIFIED) |
| Bergquist Gap Pad 1500 family | 1.5 W/m·K; −60 to 200 °C; 6000 VAC breakdown; 0.020/0.040 in available | – | distributor listings via search | listing | |
| Pad resistance, 16 × 16 mm face, k = 1.5 | 0.5 mm → 1.3 K/W; 1.0 mm → 2.6 K/W | K/W | R = t/(k·A), A = 2.56 × 10⁻⁴ m² | derived | At 6 W, a 0.5 mm pad drops about 8 °C. Put the thermocouple on the package side |
| Pad resistance, HS10 directly on the package (≈ 8.5 × 15.9 mm face), k = 1.5 | 0.5 mm → ≈ 2.5 K/W; 1.0 mm → ≈ 4.9 K/W | K/W | A ≈ 1.35 × 10⁻⁴ m²; 0.5 × 10⁻³ / (1.5 × 1.35 × 10⁻⁴) = 2.47 | derived | Added by the verifier. At 6 W that is about 15 °C across a 0.5 mm pad. A spreader block of about 16–18 mm restores the 16 × 16 figure above |
| **Print materials** | | | | | |
| PLA (Bambu PLA Basic) | Tg 60, HDT 57 (0.45 MPa) / 54 (1.8 MPa), Vicat 57 | °C | Bambu TDS V2.0 (read via mirror) | datasheet | |
| PETG (Prusament PETG) | HDT 68 (0.45 MPa) and 68 (1.8 MPa) | °C | Prusament PETG TDS v1.1, 2022-02-16 | datasheet | Nozzle 250 ± 10 °C |
| PETG (Bambu PETG Basic) | Tg 68, HDT 69 (0.45) / 65 (1.8), Vicat 78 | °C | Bambu TDS V2.0 (read via mirror) | datasheet | Nozzle 240–270 °C |
| PETG service limit (Prusa) | "temperatures below 80 °C" | °C | help.prusa3d.com/article/petg_2059 | datasheet | Marketing wording. The HDT numbers are the ones to design to |
| ASA (Bambu ASA) | HDT 100 (0.45) / 92 (1.8), Vicat 106; Tg not given | °C | Bambu TDS V2.0 (read via mirror) | datasheet | Nozzle 240–270 °C |
| ASA (Prusa) | "temperature resistance up to 93 °C"; nozzle 260, bed 105–110 °C | °C | help.prusa3d.com/article/asa_1809 | datasheet | Warps. Needs an enclosure or draft shield |
| Minimum wall, 0.4 mm nozzle | ~0.8–1.0 (two perimeters ≈ 0.9); use ≥ 2 for enclosure walls | mm | Wevolver guide 0.75 supported / 1.0 unsupported, via search | listing | ≥ 2 mm is a design choice |
| Fit clearance | sliding 0.2–0.3; separately printed parts 0.4–0.5 to start | mm | Wevolver; GrabCAD tutorial, via search | listing | Print a fit test |

---

## 1. The FPGA package: what the heater may touch

* From [PKG]: the body is **20 × 20 mm** and the lead tips span **22 × 22 mm**, so each lead sticks out 1.0 mm. The top is **1.45–1.65 mm** above the PCB.
* The drawing does not give a height for where the leads leave the body. It shows them leaving at roughly mid-thickness. That puts the lead shoulders about 0.5–0.8 mm below the top plane of the package (a rough reading of the drawing, not a dimension). Anything flat and conductive that hangs past the body edge is therefore **within about half a millimetre of 144 live leads**.
* The **exposed pad is on the bottom** (5.4 mm square). It is soldered to ground, and Altera says not to use it for thermal purposes [HB]. The only practical place to apply heat is the **moulded top**.
* The flat area of the top face, the edge draft, the size of the pin-1 dot and any ejector-pin marks are **not dimensioned**. Design the heater contact face as **≤ 18 × 18 mm, centred** (1 mm margin per side). A 0.5–1.0 mm conformable pad will cover a shallow dimple. Do not put the thermocouple bead in the pin-1 dimple: it sits near a corner and does not represent the body.
* The package document gives **no mechanical load limit**. The clamp should use a modest force from a spring. Support the PCB from below under the FPGA so the clamp force does not bend the board.
* From [board.jpg] (photo-estimate only): yellow 2.54 mm pin headers stand close to the FPGA on at least three sides. The board also ships with a clear acrylic top plate on brass standoffs, which has to come off. Whether the heater stack fits between the headers or must rise above them depends on measurements Alex has not made yet.

## 2. Heater options

**(a) Aluminium-clad resistor.** Its flat base is the mounting face; the fins sit on top ([ARCOL] p2 end view).
* **HS10:** the base footprint is 16.5 × 15.9 mm, which fits inside the 18 mm contact limit. It is rated 10 W on a 415 cm² × 1 mm aluminium plate and 5 W in free air. Its holes are only **Ø2.4 mm**, so they take M2 screws, not M3.
  * *Verifier correction.* 16.5 × 15.9 mm is the **envelope**, not a flat rectangle. On the p2 drawing the flat base under the body is about the body width D (≤ 8.5 mm) by E (15.9 mm). The extra width is two small tabs at diagonally opposite corners. Directly on the package, the HS10 heats a strip about 8.5 mm wide, and a 0.5 mm pad then costs about 2.5 K/W rather than 1.3 (derived, table).
  * The solder lugs reach about 7 mm past each end of the body (B = 30.0 max), at up to H = 4.5 mm above the base. With the body centred on the package, the **live 12 V lugs hang over the leads and the PCB** (derived). Sleeve them in heat-shrink and check their clearance to the headers.
  * An aluminium spreader of about 16–18 mm square under the HS10 fixes the narrow contact. The spreader is also where the thermocouple groove goes (§4).
* **HS25:** 28 × 27.3 mm, rated 25 W. It is **wider than the package**. It would need an aluminium or copper spreader block of 18 mm or less between it and the package, tall enough to keep the resistor's edge clear of the leads and the headers.
* **TE "HSA10" is not the same size as an Arcol HS10.** TE's sheet gives 36.5 × 21 × 11 mm and 16 W [TE-HSA10], which is the size of an Arcol HS15. Do not mix part numbers when modelling.
* The case is bare aluminium. The element inside is isolated (10,000 MΩ), but the case still conducts, and the solder lugs carry 12 V. A thermal pad between case and package, plus heat-shrink on the lugs, is mandatory.

**(b) Polyimide film heater.** It is thin (about 0.2 mm) and electrically insulating on both faces, which is the safest option near fine-pitch leads. It has no stiffness of its own: bond it to a small aluminium plate and clamp the plate. Small 12 V sizes such as 20 × 20 mm are sold only on marketplaces with no traceable datasheet (unknown). 10 W on 20 × 20 mm is about 16 W/in² (derived), above Omega's top standard density, so expect hot spots. Prefer 5 W on 25 × 25 mm, then cut the spreader down to 18 mm.

**(c) PTC element.** It limits its own temperature, so a stuck-on MOSFET cannot overheat it. That is a real safety advantage. The only part with a traceable spec page, the DFRobot FIT0845, settles at **100 ± 10 °C**, which is too hot for an 85 °C chip. *(Verifier: that page is DFRobot's store listing, not a datasheet, so it is tagged listing.)* A 12 V, 80 °C part exists only as a listing (about 35 × 21 × 5 mm). As a PTC gets close to its limit its power falls, so reaching 70 °C with an 80 °C PTC while the fan runs may be slow. That is unknown until tested.

**Is 14.4 W (12 V, 10 Ω) sensible?** This is a rough bound (derived) and has to be measured.
* The package has to be held about 40 °C above ambient (25 → 65 °C).
* Arcol's own figure: an HS10 on a 415 cm² aluminium plate rises 5.8 °C/W. Treat the FPGA board as a heatsink. It is FR4 rather than aluminium and about that size or smaller, so it is probably a *worse* heatsink, which means *less* power is needed for a given rise.
* Holding +40 °C would therefore take about 40 / 5.8 ≈ **7 W or less** with the fan off. A cooling fan raises that.
* So 14.4 W gives about 2× headroom for fast ramps. If the MOSFET fails on, 14.4 W × 5.8 °C/W ≈ 84 °C of rise puts the chip well past 85 °C. That is why the thermostat and fuse are not optional.
* With an HS10, 14.4 W also exceeds its 10 W heatsink rating. Use **15 Ω (9.6 W)** or **22 Ω (6.5 W)**, or move to an HS25 with a spreader. Any PWM duty limit is software and does not count as protection.
* Measure the board's real thermal resistance before choosing R. Apply a known 3–5 W, wait for steady state, then θ = ΔT / P.

## 3. Thermostat (KSD9700)

* Body 20.5 × 7.5 × 3.7 mm, iron shell; 28 × 8.9 × 5.1 mm with the factory silicone sleeve. Leads are 80 mm.
* It is **normally closed**: it opens when hot and re-closes by itself when it cools. Rated 5 A at 250 VAC resistive. **No DC rating is published.** 1.2 A at 12 VDC is far below 5 A but outside what is documented (unknown, low risk).
* The sensing face is the **unprinted** side. Clamp or epoxy that face to the heater or spreader block, not to the air.
* *Verifier addition.* **The iron shell is connected to one lead.** The [XC-KSD] p2 drawing has a callout on one lead reading "此线与铁壳体虚接" ("this lead is connected to the iron shell"; 虚接 is loose wording). In series with the 12 V heater feed, the bare shell then sits at 12 V or at the switched node. Clamped bare to a metal spreader, it makes the spreader live, and the spreader is within about a millimetre of 144 FPGA leads. Either keep the factory silicone sleeve (rated −40 to 230 °C, [XC-KSD] p4), which costs some thermal coupling, or put a layer of Kapton under the shell. Check shell-to-lead continuity on the part that is bought.
* With heating from outside, heat flows from the heater block into the package, then the die, then the board. The **heater block is therefore the hottest point**, and a thermostat mounted on it limits the die temperature (plus the die's own small self-heating, which can be measured with the INA226).
* **Decision for Alex.** A 70 °C part opens anywhere from 65 to 75 °C (derived from ±5 °C). Mounted on the block it can stop the package short of 65 °C, so a 70 °C setpoint cannot be reached. The options:
  * keep the demo setpoints at 60 °C or below;
  * use a 75 °C part, which opens no later than 80 °C, leaving about 5 °C of margin to 85 °C;
  * mount the thermostat on the package side.

  Re-closing comes about 20 °C below opening (the 100 °C part: 100 ± 5 open, 80 ± 10 re-close), so the thermostat cycles. Software should treat any opening as a fault.
* KSD301: about Ø16 mm disc with 6.3 mm tabs, 10 A rated. It is bulkier, and its flange spacing was not found (listing). The KSD9700 suits a small block better.

## 4. Thermocouple

* **Bare bead (Adafruit 270 style):** the bead size is **not published**. Measure it with calipers. This is the one to use.
* **Ring/washer probe (M6):** it has to be bolted, and there is nothing to bolt to on a QFP top. Bolted to the spreader it would read the heater, not the package. The ring and braid may be electrically joined to the junction, so check with a multimeter. If they are, it is a grounded thermocouple, which the MAX31855 rejects.
* **Screw probe (M6 thread):** needs a tapped block at least about 6 mm thick. Same objection as the ring probe.
* **Recommended attachment, in order:**
  1. A shallow groove in the underside of the spreader, about the bead diameter minus 0.1–0.2 mm deep, so the bead touches the package top. That gives the same position every time it is assembled.
  2. Line the groove with a layer of Kapton tape so the bead cannot touch the metal block. The MAX31855 grounded-thermocouple fault applies if the block is ever grounded.
  3. Add a dab of non-conductive paste.

  The alternative is the bead taped with Kapton to the package top beside the heater face. It is simpler, but repeatability depends on where it lands.
* Keep the bead on the **package side of the thermal pad**. A 0.5 mm pad can drop several °C (§ table, derived).

## 5. Fan (40 mm)

* The 4010 format is standard: 40 × 40 × 10 mm with 32 mm hole centres (Sunon datasheet: 32 ± 0.3).
* **Hole diameter varies by maker.** Sunon is Ø4.3 mm and recommends M4 screws. Others differ, so measure before fixing the bosses. M3 screws pass a 4.3 mm hole with play. Fix with M3 into heat-set inserts in the enclosure, or with nuts.
* The **operating limit is 70 °C** [SUNON]. Mount the fan on the **inlet** so it pushes room air across the FPGA zone, and vent the far side. Do not mount it as an exhaust behind the heater.
* **2-wire:** speed set by PWM only, no feedback.
* **3-wire switched low-side by a MOSFET:** the tach output is powered from the fan's own (switched) ground. While the switch is off the tach is garbage, and readings go unstable as duty changes. The fix is "pulse stretching": force 100 % on for a short window while reading the tach. Unverified extra risk with a 12 V fan: when the low-side switch is off, the fan's internal ground node floats up toward +12 V. Check the tach line's voltage before connecting it to a 3.3 V Pico pin.
* **4-wire PWM:** power is always on and speed is a 25 kHz logic signal. The tach is open-drain, 2 pulses per revolution, so pull it up to 3.3 V on the Pico side. The fan pulls its own PWM pin up to as much as 5.25 V, so drive that pin through an open-drain transistor rather than straight from a 3.3 V GPIO. This is the clean option if a real speed reading matters.
* **Fan guard:** no source checked. 40 mm guards normally use the same 32 mm pattern (unknown). Buy, then measure.

## 6. Panel connectors

* **DC jack (5.5 × 2.1 mm):** the panel hole varies from about **8 mm** (small DC-022B style; one seller says panel ≤ 3 mm) to **12–12.7 mm** (round nut types; ProtoSupplies: 12 mm hole, 14 mm OD, panel ≤ 7.9 mm). Print the wall locally thinned to the jack's maximum panel thickness. Do not mix 2.1 and 2.5 mm pins: the Switchcraft 712A is 2.5 mm.
* **Fuse:**
  * an inline ATO blade holder (fuse 19.1 × 5.1 mm) needs only a cable clip;
  * an M205 (5 × 20 mm) panel holder (Jaycar SZ2028 is Ø19 × 39.8 mm) needs a measured cut-out and about 40 mm of depth behind the panel.
* **USB panel extension (optional):** the Pico uses micro-B. Adafruit 3258 (micro-B to micro-B) uses 4-40 screws on 18 mm centres. Adafruit 937 (B to micro-B) uses 2 × M3 on 27–29 mm centres. Sources disagree, so measure.

## 7. Fasteners

* **Heat-set insert, M3 × 5.7:** hole Ø4.0 mm, blind depth ≥ 6.7 mm, wall ≥ 1.6 mm, so the boss is ≥ 7.2 mm OD. Straight hole, no taper. Install with the iron 10–20 °C above the print temperature. FDM holes come out undersize, so print the CNC Kitchen test coupon in the real material first.
* **Clearance holes:** Ø3.4 mm.
* **Socket head counterbore:** about Ø6.0 × 3.3 mm (derived: 5.5 mm head and 3.0 mm height plus clearance).
* **Nut trap:** about 5.7–5.8 mm across flats × 2.6 mm deep.
* **Brass standoffs under the board:** M3, F-F, 5 mm hex, lengths 5–20 mm in 1–2 mm steps. The board's own standoffs (seen in the photo) may already fit. Measure their length and thread.

## 8. Window

* Use 2 or 3 mm clear cast acrylic. 3 mm is stiffer over a span the size of the board.
* Measure the actual sheet thickness before printing the frame groove. Cast sheet varies.
* Acrylic's softening temperature was not researched (unknown). Keep the window out of the heater's line of sight; its zone is above the board, not touching the heater.
* An Australian source, a listing with an unverified price: koenigmachinery.com.au, 3 mm clear cast, about 300 × 200 mm for about AUD 3.91. A local plastics supplier's offcut bin is the alternative.

## 9. Thermal pad and paste

* Use an **electrically insulating silicone pad**. 0.5 mm suits a flat spreader on the flat package top. Use 1.0 mm only if the faces are not parallel. Both listed products are rated far above 70 °C (Arctic TP-3: 150 °C; Gap Pad: 200 °C).
* A thicker pad adds about 1.3 K/W per 0.5 mm on a 16 mm face (derived, k = 1.5). That drop is why the thermocouple goes under the pad.
* Paste alternative: use only non-conductive paste. Never use metal or liquid-metal compounds near 0.5 mm leads. Paste can creep, and a pad is more repeatable for the demo.

## 10. Print materials

| Material | HDT 0.45 MPa | Margin over a 70 °C zone | Use |
|---|---|---|---|
| PLA (Bambu Basic) | 57 °C | −13 °C | nowhere near the heat (as the brief says) |
| PETG (Prusament / Bambu Basic) | 68 / 69 °C | −2 / −1 °C | **cool zone only** (module plate, lid, outer shell away from the heater) |
| ASA (Prusa / Bambu) | 93 / 100 °C | +23 / +30 °C | heater clamp, anything in the FPGA zone |

The brief says "Prefer PETG or ASA". The datasheet HDT values leave **PETG no margin in the heater zone**, so it is not acceptable there. *(Verifier: the datasheets give HDT numbers, not a verdict. "Not acceptable" is a design judgement drawn from them, and a fair one.)* The heater block runs hotter than the package, so anything that touches the block should be **metal**, with ASA held back by a small-area metal spring or standoff.

* Heat-set inserts in the heater zone will creep in PETG.
* ASA warps without an enclosure. Alex's printer setup is not known.
* Walls: ≥ 2 mm for the shell, ≥ 0.9 mm (2 perimeters) for ribs.
* Fits: sliding 0.2–0.3 mm, lid into frame 0.3–0.4 mm. These are starting points; check them with a printed fit test.

---

## Red flags (summary)
1. An HS25 or any aluminium heater wider than about 18 mm overhangs the 22 mm lead span, about 0.5 mm above the leads. That risks shorts. *(Verifier: "about 0.5 mm" comes from reading the drawing, not from a dimension. It is the no-pad, worst case at the body edge, about 0.5–0.8 mm. A 0.5 mm pad adds 0.5 mm, and the gap grows where the leads bend down to the PCB. Treat it as a photo-estimate.)*
2. 10 Ω at 12 V (14.4 W) exceeds the HS10's 10 W rating, and its free-air rating 3×.
3. The Arcol HS10 holes are Ø2.4 mm, so they take M2, not M3.
4. PETG HDT of 68–69 °C is at or below the zone temperature. Not acceptable near the heater.
5. A 70 °C thermostat on the heater block makes a 70 °C package setpoint unreachable.
6. The KSD9700 is rated for AC only (DC undocumented).
7. The fan is rated only to 70 °C, so it must sit on the cool inlet.
8. A 3-wire fan switched low-side gives a corrupted tach reading. With a 12 V fan the tach line may also reach 12 V (unverified).
9. The MAX31855 faults if the thermocouple junction is grounded through a metal block or ring probe.
10. The PTC with a traceable spec page (DFRobot, 100 °C; a store listing, not a datasheet) is too hot for an 85 °C part.
11. *(Verifier)* One KSD9700 lead is connected to its iron shell ([XC-KSD] p2). A bare shell clamped to the spreader makes the spreader live, next to the leads.
12. *(Verifier)* The Arcol HS10's live solder lugs reach about 7 mm past each end of the body, over the package leads (derived from B, E, H). Its flat base is only about 8.5 mm wide, not 16.5 mm.

## Must measure (calipers unless stated)
* The package top height above the PCB, at the package centre, from the PCB top surface. Expect 1.45–1.65 mm. Check whether the top is flat and where the pin-1 dot and any ejector marks sit.
* The gap from each package body edge to the nearest component on all four sides, and the height of the pin headers above the PCB.
* Whether the PCB can be supported from below under the FPGA (what parts are on the bottom side).
* The bead diameter of the thermocouple bought, and continuity between bead or ring and both leads on a ring/screw probe.
* The KSD9700 actually bought: printed temperature and body size. Confirm the sensing face.
* The fan bought: hole diameter, and whether it is 2, 3 or 4-wire.
* The DC jack bought: thread OD, nut across-flats and maximum panel thickness. The same for the fuse holder (cut-out, any D-flat, depth behind the panel).
* The acrylic sheet's real thickness.
* The board's existing brass standoffs: length and thread.
* Thermal step test on the real board: apply a known 3–5 W, record ΔT at steady state, θ = ΔT / P. This sets the heater resistance.
* *(Verifier)* The power resistor that is bought: the width of the flat base under the body (calipers across the base, between the fins' bottom edges), the lug length past the body, and the hole diameter.
* *(Verifier)* The KSD9700 that is bought: continuity from each lead to the bare iron shell (multimeter, sleeve slid back).

## Sources
* [PKG] `resources/Altera-Cyclone-IV-board-V3.0 documentation/Cyclone IV chip/EP4CE6 package information.pdf`, Altera 04R-00402-1.0, Jan 2011. p1 dimension table, p2 outline drawing.
* [HB] `.../Cyclone IV chip/Cyclone IV Handbook.pdf`, PDF p19, Table 1-3 and note (1).
* [DS] `.../Cyclone IV chip/Cyclone IV Datasheet.pdf`, p2 Table 1-1, p4 Table 1-3.
* [board.jpg] `resources/Altera-Cyclone-IV-board-V3.0 documentation/board.jpg` (photo-estimate only). The Dev Board Manual p1 says the board is powered by USB or a 5 V adapter.
* [ARCOL] Arcol HS Aluminium Housed Resistors datasheet 12/14.08, read via https://static.chipdip.ru/lib/017/DOC027017802.pdf (p1–2).
* [TE-HSA10] TE HSA10680RJ product sheet, https://docs.rs-online.com/1d40/A700000015967534.pdf p1–2. The same values are on HSA1010KJ, https://docs.rs-online.com/a881/A700000015967526.pdf.
* [XC-KSD] XC Electronics (Shenzhen) KSD9700 test report and drawing, 2025-09-13, https://atta.szlcsc.com/upload/public/pdf/source/20250917/851B236838E2399B8D14C94DA645621B.pdf p1–2.
* [SUNON] Sunon spec D04114150G-02, MF40100V1-1000U-A99, https://www.sunonusa.com/wp-content/uploads/2026/05/MF40100V1-1000U-A99-D04114150G-02-1.pdf p3, p4, p6.
* [DFR] DFRobot FIT0845 product page PDF, https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/6648/FIT0845.pdf p3–4. (A store-page printout, not a datasheet.)
* [MAX31855] Maxim MAX31855 datasheet 19-5793 Rev 2 (2/12), read via the Adafruit mirror https://cdn-shop.adafruit.com/datasheets/MAX31855.pdf, p7 pin description, p10 Table 2. Added by the verifier.
* Harwin product pages https://www.harwin.com/products/R30-1001002/ and https://www.harwin.com/products/R30-1011002/. Added by the verifier.
* Arctic TP-3 product page https://www.arctic.de/en/TP-3/ACTPD00052A. Added by the verifier.
* Filament data sheets:
  * Prusament PETG TDS v1.1: https://www.3dprintergear.com.au/assets/files/technical-data-sheet%20(1).pdf
  * Bambu PLA Basic TDS V2.0: https://www.additive-x.com/shop/mpattachments/file/viewonline/id/494/product_id/2236
  * Bambu PETG Basic TDS V2.0: .../id/580/product_id/2330
  * Bambu ASA TDS V2.0: .../id/612/product_id/2399
  * Prusa KB: https://help.prusa3d.com/article/petg_2059 and https://help.prusa3d.com/article/asa_1809
* Inserts:
  * CNC Kitchen blog: https://cnckitchen.com/blog/tips-and-tricks-for-heat-set-inserts
  * 3DJake CNC Kitchen M3 standard: https://3djake.ch/en-CH/cnc-kitchen/threaded-inserts-m3-standard
  * 3DJake ruthex M3x5.7: https://www.3djake.ch/en-CH/ruthex/threaded-insert-m3-100-pieces
* Listings, read directly or via search summaries:
  * Adafruit 270 and 1481
  * ProtoSupplies M6 ring thermocouple and panel DC jack
  * Noctua NF-A4x10 5V PWM spec page
  * Intel 4-Wire PWM Fan spec (mikrocontroller.net mirror)
  * Microchip SmartFusion DC fan control app note
  * Littelfuse FHAC
  * Jaycar SZ2028 / SZ2030 / SZ2034
  * Adafruit 937 / 3258
  * Koenig Machinery acrylic
  * Arctic TP-3 (scan.co.uk)
  * Bergquist Gap Pad 1500 (distributors)
  * Omega KH/KHLV
  * fasten.it ISO 4762 / ISO 4032
  * Optimas ISO 273 table
  * Harwin R30 (RS)
  * Wevolver / GrabCAD FDM guides
  * Arduino forum / Zanduino wiki (MAX31855)

---

## Verification (adversarial pass)

Verifier pass on 2026-10-23. Every check below was re-derived from the primary file in this session. The local PDFs were read with pymupdf, and the web PDFs were downloaded and rendered page by page. Nothing was taken from the first author's notes.

### Checked and confirmed (no change needed)
| # | Claim | Re-derived from | Result |
|---|---|---|---|
| 1 | Package: D1/E1 20.00, D/E 22.00, A 1.45/1.55/1.65, A1 0.05–0.15, A2 1.30–1.60, e 0.50, b 0.17–0.27, c 0.09–0.20, L 0.45–0.75, L1 1.00 REF, coplanarity 0.08, 1.3 g, MS-026 BFB-HD | [PKG] p1 table, p2 drawing | Exact match |
| 2 | Exposed pad D2/E2 5.25–5.55 on the **bottom** | [PKG] p2 "BOTTOM VIEW" | Confirmed |
| 3 | Pad is ground, "for electrical connectivity and not for thermal purposes" | [HB] PDF p19, notes to Table 1-3, note (1) | Verbatim match |
| 4 | TJ 0–85 °C commercial; −40 to 125 °C absolute maximum | [DS] p4 Table 1-3; p2 Table 1-1 | Confirmed (the Table 1-1 label is noted above) |
| 5 | Board powered by USB or a 5 V adapter | Dev Board Manual p1 | Confirmed |
| 6 | Arcol HS10 10 W / 5 W; HS25 25 W / 9 W; rise 5.8 / 4.2; heatsinks 415 and 535 cm² × 1 mm; 200 °C hot spot; 10,000 MΩ; 1400 / 1000 V | [ARCOL] p1–2 | Exact match |
| 7 | Arcol HS10 A 16.5, B 30.0, C 8.8, D 8.5, E 15.9, F 11.3, G 12.4, K 1.8, **L (hole) 2.4**; HS25 28.0 / 51.0 / 14.8 / 27.3 / 18.3 / 19.8 / 3.2 / 2.6 | [ARCOL] p2 table plus zoomed drawing (L's leader points at the hole) | Numbers confirmed. Footprint interpretation corrected (below) |
| 8 | TE HSA10: 16 W, 36.5 × 21 × 11 mm, the same size as an Arcol HS15 | [TE-HSA10] p1–2; [ARCOL] p2 HS15 row (21.0 / 36.5 / 11.0) | Confirmed |
| 9 | KSD9700 20.5 × 7.5 × 3.7 bare, 28 × 8.9 × 5.1 sleeved, 80 ± 3 mm leads, 8 ± 1 mm strip, NC (常闭), AC 250 V 5 A resistive, 100 ± 5 / 80 ± 10 °C, unprinted face senses ("印字面在非感温面"), ≤ 50 mΩ, > 100 MΩ, 1450 VAC / 1 min; no DC rating | [XC-KSD] p1–2 (rendered drawing) | Confirmed |
| 10 | Sunon MF40100V1-1000U-A99: 40 ± 0.5 × 10 (+0.5/−0), 4 × Ø4.3 ± 0.3 on 32 ± 0.3, 5 V (3.5–6), 136 / 157 mA, 0.68 W, 7000 rpm ± 15 %, 8.0 CFM, 0.19 inH₂O, 27.3 dB(A), −10 to +70 °C, 300 ± 10 mm UL1007 26 AWG, 2-wire, M4 or Ø5 self-tapping screws | [SUNON] p3, p4, p6 (rendered) | Exact match |
| 11 | HDT 0.45 MPa: Prusament PETG 68 (1.8 MPa: 68); Bambu PLA 57 (Tg 60, Vicat 57, 1.8 MPa: 54); Bambu PETG 69 (Tg 68, Vicat 78, 1.8 MPa: 65); Bambu ASA 100 (Vicat 106, 1.8 MPa: 92); nozzle temperatures | The TDS PDFs listed in Sources | Exact match |
| 12 | Prusa KB: ASA "up to 93 °C", nozzle 260 °C, bed 105 / 110 °C; PETG "below 80 °C" | help.prusa3d.com asa_1809, petg_2059 | Confirmed |
| 13 | Insert M3 × 5.7: D1 4.6, D2 3.9, hole D3 4.0, W min 1.6; blind hole "approx. 1 mm" deeper; iron PLA 225 / PETG 245 / ABS 265, i.e. 10–20 °C over the print temperature; straight holes | 3djake CNC Kitchen M3 standard page; cnckitchen.com blog | Confirmed |
| 14 | ISO 4762 M3 head 5.5 / 3.0 (2.86 min), 2.5 hex; ISO 4032 M3 5.5 AF, 2.40 / 2.15 high, 6.01 e min | fasten.it tables (via search) | Confirmed (listing-grade source, as tagged) |
| 15 | Arithmetic: 14.4 W / 1.2 A; 15.9 W at 12.6 V; 14.4 Ω; 9.6 W / 0.8 A; 28.8 Ω; 4.4 W / 0.36 A; 6.5 W; 40 / 5.8 = 6.9 W; 14.4 × 5.8 = 83.5 °C; 400 mm² = 0.62 in² → 16 W/in²; 8.0 CFM = 13.6 m³/h; 8.9 m³/h = 5.24 CFM; pad 1.30 / 2.60 K/W; boss 7.2 mm | recomputed | All correct |
| 16 | Adafruit 270: 1 m, 1.45 mm, 500 °C, bead size not stated; Adafruit 1481 dimensions | adafruit.com product pages | Confirmed (1481 also says 5–12 VDC) |
| 17 | Board photo: yellow headers close to the FPGA, clear acrylic plate on brass standoffs | board.jpg | Consistent; stays photo-estimate |

### Corrected
1. **Arcol HS10 footprint.** "Base footprint 16.5 × 15.9 mm" is the envelope only. The flat base under the body is about D × E (≤ 8.5 × 15.9 mm, derived from the drawing), plus two small corner tabs. Added a derived row for the narrower contact (≈ 2.5 K/W through a 0.5 mm pad) and a spreader recommendation.
2. **Arcol HS10 lugs.** Not mentioned before. The live 12 V solder lugs reach about 7 mm past each end of the body, over the leads (derived from B, E and H).
3. **Arcol graph note.** "HS10 at 10 W ≈ 58 °C" cannot be read from the coarse p1 graph. The °C/W unit is confirmed instead by the HS15, HS25 and HS50 points.
4. **Arcol hole tolerances.** Added ±0.25 on L. The HS25's Ø3.2 can be 2.95 mm.
5. **KSD9700 shell is live.** The drawing's callout "此线与铁壳体虚接" puts one lead on the iron shell. Added a facts row, a §3 bullet, red flag 11 and a measure item. Also recorded the CQC (6,000 cycles) and UL (AC 125 V) ratings next to the TUV 10,000-cycle figure.
6. **DFRobot FIT0845 confidence: datasheet → listing.** The cited PDF is a store-page printout.
7. **Harwin standoff hex.** The "5 mm vs DigiKey 5.50 conflict" is not a conflict. Harwin's own pages give R30-1001002 = 5.00 A/F and R30-1011002 = 5.50 A/F. Design for 5.5.
8. **MAX31855 grounding: listing → datasheet** for the essential fact: "T−: Do not connect to GND", with the SCG fault bit D1 ([MAX31855] p7, p10).
9. **Arctic TP-3: listing → datasheet** for thickness, −40 to 150 °C and insulating (arctic.de). Arctic publishes no k, so the 6 W/m·K is a reseller claim.
10. **Wording.** "PETG will not survive" became "no margin", because the datasheets give HDT, not a verdict. "~0.5 mm above the leads" is marked as a drawing reading (photo-estimate). Noted that [DS] Table 1-1 labels the −40 to 125 °C row "Operating junction temperature" although it is the absolute-maximum table.

### Still UNVERIFIED after this pass
* θJA / θJC for the E144 package. Not found in the local docs or by search, and it would sharpen the heater-power estimate.
* The Intel 4-wire PWM fan spec values. The mirror returned HTTP 403 and the values were seen only in a search summary. It is also unverified whether a 5 V PWM fan, such as the Noctua NF-A4x10 5V PWM, follows the 5.25 V PWM pull-up limit. The Noctua page returned HTTP 429.
* Every 70 °C / 75 °C KSD9700 opening and reset figure. Only the 100 °C part has a maker's drawing; the rest is derived or from listings.
* The 3-wire low-side "tach floats to 12 V" risk (unchanged; unverified).
* DC jack, fuse-holder, USB panel-extension, fan-guard, acrylic-price, polyimide-pad, 12 V 80 °C PTC, KSD301, M6 ring probe, Omega watt density, CNC Kitchen short and Voron insert sizes, Bergquist Gap Pad, Noctua figures and Wevolver/GrabCAD fit numbers. All remain listing-grade or unknown, as the original author tagged them, and were not re-opened here.
* The 5–8 W steady-state power estimate. It is a heuristic built on Arcol's aluminium-plate figure and must be replaced by the step test.
