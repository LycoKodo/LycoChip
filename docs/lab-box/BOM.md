# Agent Lab Box MVP: bill of materials

> **Nothing here has been bought. Alex approves every line before any money is spent.**
> This is a shopping *proposal*, built from `cad/lab-box/DESIGN.md` v0.1 (the §9 bold defaults)
> and the research in `docs/lab-box/research/`. Written 2026-10-23.

**About the prices.** Every price is **AUD incl. GST, before shipping, unverified (read 2026-10-23)**.
Most were read by the research agents from shop pages, and three were read for this file
(the Little Bird USB-C breakout and the Altronics fuse holder and fuse). A web page is not
a quote. AliExpress prices are the cheapest variant shown, and the frequent AU$1.49 looks like
a new-user promotion, so treat it as a floor. Little Bird's page does not say whether GST is included.

**Sources** (short names used below): [S] = `research/suppliers-au.md` · [M] =
`research/modules-electronics.md` · [P] = `research/board-power.md` · [C] =
`research/clock-pins.md` · [T] = `research/thermal-safety.md` · [TM] =
`research/modules-thermal-mech.md` · [D] = `cad/lab-box/DESIGN.md`. Verifier corrections at
the end of each research file override its body, and they were applied here.

**Columns.** *Fast* = the local fast route (Core, Altronics, Jaycar, Bunnings, Little Bird).
*Cheap* = AliExpress where it saves money. A **§9.n** tag means the line depends on one of
Alex's open decisions in DESIGN.md §9. The bold default is what is priced.

**Key words.** "Knob" = something the agent can change. "Eye" = something it can read.
"Backstop" = a safety part that works even if the software is wrong.

---

## Known gaps (read these first)

1. **No locally stocked thermostat fits.** None of the local shops checked sells a normally-closed
   (NC) thermostat at 70–80 °C that is rated to switch 12 V DC at the heater current. Jaycar's
   ST382x family is only rated 32 V DC **100 mA**. Altronics S5612 trips at 90 °C, above the
   FPGA's 85 °C limit [S red flag 1]. The KSD9700 from AliExpress has **no published DC
   rating**: the one named-maker datasheet gives AC 250 V 5 A only [T facts; S verifier].
   Running it at 12 V and 0.7 A is far below that current, but **how it behaves on DC is unverified**.
   **75 °C is not confirmed in stock either.** The cheap AliExpress listing offers 15–70 °C [S
   row 86]. An **80 °C** named-maker part (Xucheng KSD9700-80/5JSB/080A, LCSC C51934112) exists
   and [T §4] rates 80 °C "acceptable". Other options: a DC-rated thermostat from element14, or
   a low-current thermostat that cuts a relay coil [S red flag 1]. **Alex decides.**
2. **The HS10-class heater is not sold locally.** Core, Jaycar and Altronics have no
   aluminium-clad resistor of this size [S TL;DR 3]. An Arcol HS10 18 Ω needs element14 AU,
   RS AU or DigiKey AU. All three blocked the research scripts (HTTP 403), so **there is no price**.
   **Naming trap:** Arcol writes the decimal point as R. "HS10 **18R** J" is 18 Ω. "HS10
   **R18** J" is 0.18 Ω (web search, 2026-10-23, not opened). Check the part number twice.
3. **The INA226 is only sold locally by Little Bird** (CJMCU-226, $3.30). Core, Jaycar and
   Altronics don't list one [S row 50–51]. The page states **no shunt value**. Read the marking
   when it arrives: R100 = 0.1 Ω is the value the design assumes [P §3].
4. **No local opto-isolated D4184 module was found.** The research recommends one for the
   heater [M MOSFET table]. Core's CE09733 (direct-drive, dual AOD4184) is the local fallback.
   It is only "typical" at a 3.3 V gate, so measure V_DS at the real current before trusting it
   [M row AOD4184A; M must-measure 10].
5. **Not researched, so no SKU or price:** the clamp spring, ball/plunger, locating pins,
   20 mm square aluminium bar, knurled thumbscrews, M2 hardware sold locally, silicone wire,
   heat-shrink, the small parts (resistors, capacitor, AO3400A), and the optional 5 V load
   switch. These are listed as "not priced" below. A short supplier pass is needed before ordering.

---

## 1. Electronics

| # | Item | Qty | Purpose | Recommended part | Supplier · SKU · URL | Fast | Cheap |
|---|---|---|---|---|---|---|---|
| E1 | Box controller | 1 | The brain. Runs the heater loop, reads every eye, talks USB to the host | Raspberry Pi Pico 2 H (RP2350, headers fitted) | Core **CE10154** · core-electronics.com.au/raspberry-pi-pico-2-h-with-headers.html | 9.90 | 9.90 (same) |
| E2 | Thermocouple amplifier | 1 | **Eye: chip temp** (T_top, package top) | Adafruit MAX31855 v2.0 (#269) | Core **ADA269** · core-electronics.com.au/thermocouple-amplifier-max31855-breakout-board-max6675-upgrade-v2-0.html · Cheap: AliExpress MAX31855 module · aliexpress.com/w/wholesale-max31855-module.html | 28.25 | 2.81–9.60 |
| E3 | K-type thermocouple | 1 | Eye: chip temp (the probe itself) | **Insulated (ungrounded) junction, 1 mm sheath** [D 3.1.5] | Cheap/preferred: AliExpress "K-type ungrounded" · aliexpress.com/w/wholesale-k-type-thermocouple-ungrounded-1mm.html · Fast: Core **ADA270** (bare bead, wrap the junction in Kapton) · core-electronics.com.au/thermocouple-type-k-glass-braid-insulated-k.html | 19.95 | 4.19–13.49 |
| E4 | Ambient sensor | 1 | **Eye: air temp** at the intake | PiicoDev BME280 (I²C 0x77) | Core **CE07503** · core-electronics.com.au/piicodev-atmospheric-sensor-bme280.html · Cheap: GY-BME280 · aliexpress.com/w/wholesale-bme280-module.html | 23.50 | 1.49–12.29 |
| E5 | Power monitor | 1 | **Eye: power** (whole FPGA board, high-side in the 5 V line) | INA226 module (CJMCU-226), 0.1 Ω shunt | Little Bird **LB-LS0221** · littlebirdelectronics.com.au/products/cjmcu-226-ina226-voltage-current-power-monitor-alarm-module-36v-bi-directional-i2c · Cheap: aliexpress.com/w/wholesale-ina226-module.html | 3.30 | 1.49–4.72 |
| E6 | Clock generator **§9.6** | 1 | **Knob: clock**, into FPGA PIN_24 via P1-34 | Adafruit Si5351A (#2045) | Core **ADA2045** · core-electronics.com.au/adafruit-si5351a-clock-generator-breakout-board-8khz-to-160mhz.html · Cheap: aliexpress.com/w/wholesale-si5351a-module.html | 14.60 | 1.49–2.82 |
| E7 | Heater switch | 1 | **Knob: heat** (low-side switch for the 12 V heater) | **Opto-isolated D4184 module** (PC817 + D4184; gate at ≈ ½ × 12 V) [M] | Cheap/preferred: aliexpress.com/w/wholesale-d4184-mosfet-module.html · Fast fallback: Core **CE09733** (direct-drive, not isolated) · core-electronics.com.au/mosfet-power-switch-module.html | 1.35 | 0.86–8.76 |
| E8 | Fan switch | 1 | **Knob: air** (switches the 5 V fan) | **AO3400A** N-MOSFET (the only part with R_DS(on) guaranteed at 2.5 V gate) + SOT-23 adapter, 100 Ω gate resistor, 47–100 kΩ pull-down, flyback diode [M] | Not priced. Fast fallback: Core **CE09733** (as E7) | 1.35 | not priced |
| E9 | Fan **§9.4** | 1 | Knob: air | 40 × 40 × 10 mm 5 V fan, powered from Pico VBUS | Core **CE10142** · core-electronics.com.au/40x40mm-5v-fan-dupont-connector.html · Cheap: aliexpress.com/w/wholesale-4010-5v-fan.html · *If §9.4 goes 12 V with tach:* Jaycar **XC5054** $19.95 | 2.40 | 1.49–4.16 |
| E10 | Logic analyser | 1 | **Eye: logic**, an independent view of the FPGA pins | 24 MHz 8-ch, sigrok/PulseView | Core **TOL-18627** · core-electronics.com.au/usb-logic-analyzer-24mhz-8-channel.html · Cheap: aliexpress.com/w/wholesale-24mhz-8-channel-logic-analyzer.html | 49.30 | 5.44–11.40 |
| E11 | USB-C power inlet | 1 | FPGA 5 V enters here (can't be confused with the 12 V barrel) [D 3.4.18] | SparkFun USB-C 2.0 breakout BOB-17110 (**5.1 kΩ CC pull-downs**, so a charger gives 5 V) | Little Bird **SF-BOB-17110** · littlebirdelectronics.com.au/products/usb-2-0-type-c-connector-breakout-board-1 | 5.80 | 5.80 |
| E12 | 5 V load switch **§9.5** | 1 | Lets the Pico power-cycle the FPGA (fleet goal, [D §10]) | **Not chosen.** Needs: high-side, ≥ 1 A, ≤ 0.1 Ω on, 3.3 V enable. See `wiring.md` §7 | not researched | not priced | not priced |
| E13 | Jumper wires | 40+40 | Module and header connections | 20 cm F/F and M/F Dupont | Core **CE05098** + **CE09130** · core-electronics.com.au/solderless-breadboard-jumper-cable-wires-female-female-40-pieces.html | 7.90 | 3.94–4.21 |
| E14 | Small parts | — | 10 nF across the thermocouple input [T §5]; 4.7 kΩ heater-pin pull-down (keeps the heater off during a Pico reset) [T §4; M E9]; optional 33 Ω series resistor for the clock lead [C §4] | any 0.25 W resistors, ceramic capacitor | not priced (resistor kit) | — | — |
| E15 | Star-ground terminal | 1 | The single meeting point for all signal grounds [P §4] | 5-way lever connector or screw terminal | not priced | — | — |

E7/E8 fast column: the research's local pick was CE09733 ×2 (one for each) [S BOM picks]. That
total is shown here. The research's *recommended* parts (opto for the heater, AO3400A for the fan)
are the cheap-column choices.

## 2. Thermal (the heater stack)

| # | Item | Qty | Purpose | Recommended part | Supplier · SKU · URL | Fast | Cheap |
|---|---|---|---|---|---|---|---|
| T1 | Heater resistor **§9.3** | 1 | Knob: heat. 18 Ω at 12 V = 8 W max. That caps heater power **in hardware**, even if the firmware is wrong [T §3] | **Arcol HS10 18R J** (HS10-class, 16.5 × 15.9 mm body). 22 Ω is the §9.3 alternative | element14 AU / RS AU / DigiKey AU: **price not obtained** (403). DigiKey lists the HS10 family (e.g. digikey.ie …/HS10-10R-F, a 10 Ω part: wrong value, shown only as the family) | **not priced** | **not priced** |
| T2 | Thermostat | 1 | **Backstop**: cuts heater power at about 75 °C even if the Pico has crashed | KSD9700, NC, **75 °C** (80 °C acceptable) [D 3.1.4; T §4] | AliExpress · aliexpress.com/w/wholesale-ksd9700-70c-normally-closed.html (75 °C variant not confirmed). Named maker, 80 °C: LCSC C51934112 | 0.38–3.28 | 0.38–3.28 |
| T3 | Thermal interface | 1 | Heat path from the spreader into the package, **electrically insulating** | Thin pad, or paste plus Kapton. 10 N gives only ~31 kPa, too low for thick gap pads [T §6] | Jaycar **NM2790** (0.5 mm, 1.6 W/m·K) · Jaycar product page /p/NM2790 · Cheap: aliexpress.com/w/wholesale-thermal-pad-1mm.html | 18.95 | 1.49–3.55 |
| T4 | Kapton tape | 1 roll | Insulates the spreader face, the thermocouple groove and under the KSD9700 | 8 mm polyimide tape | Altronics **T2971A** · altronics.com.au/product/t2971a-… · Cheap: aliexpress.com/w/wholesale-kapton-tape.html | 11.50 | 1.49–3.07 |
| T5 | High-temp wire | ~1 m | Any wire within 15 mm of the heater [D 3.1.9] | Silicone or PTFE insulated, 22 AWG | not priced | — | — |
| T6 | Heat-shrink | assorted | Sleeves the HS10 tags and joints (+12 V near header pins) [D 3.1.3] | — | not priced | — | — |

## 3. Power and safety

| # | Item | Qty | Purpose | Recommended part | Supplier · SKU · URL | Fast | Cheap |
|---|---|---|---|---|---|---|---|
| P1 | 12 V supply | 1 | Heater power. **Buy locally**: Australian approval matters for something left plugged in [S red flag 4] | 12 V 2 A plug pack, 5.5/2.1 mm, centre positive, **2-prong (Class II)** | Altronics **M8936D** · altronics.com.au/product/m8936d-powertran-12v-dc-2a-fixed-21mm-tip-appliance-plugpack | 24.75 | 24.75 |
| P2 | 12 V panel jack | 1 | "HEATER 12V IN" | 2.1 mm chassis socket, 13 mm hole | Altronics **P0628** · altronics.com.au/product/p0628-21mm-female-plastic-chassis-mount-dc-power-socket · Cheap: aliexpress.com/w/wholesale-dc-022-panel-jack.html | 2.25 | 1.49–3.34 |
| P3 | Fuse holder | 1 | **Backstop**: the "FUSE 1A" panel holder, reachable from outside [D 3.4.20] | M205 chassis-mount holder | Altronics **S5991** · altronics.com.au/category/m205-fuse-holders (read for this file; DC rating and panel thickness not shown, MEASURE) | 2.25 | 2.25 |
| P4 | Fuse | 1 (+ spares) | Backstop: 1 A fast. An 18 Ω heater draws ≤ 0.70 A at 12.6 V, so a 1 A fuse runs at ≤ 75 % of its rating [T §4] | 1 A fast-blow M205 | Altronics **S5724** ($0.40) or **S5725** 10-pack ($3.30) · altronics.com.au/category/m205-fuses | 0.40 | 0.40 |
| P5 | DC pigtail to the board | 1 | Carries metered 5 V into the board's DC jack | 2.1 mm tip-positive plug, 30 cm | Altronics **P6714** · altronics.com.au/product/p6714-pigtail-dc-power-lead-21mm-plug-30cm-tip-positive · Cheap: aliexpress.com/item/1005007317225328.html. **The board jack size is unmeasured** [P must-measure 1]: buy after measuring | 3.40 | 1.49–2.55 |
| P6 | 5 V USB-C charger | 1 | FPGA board supply, through E11 → INA226 | Any **2-prong** USB-C charger, ≥ 1 A at 5 V | Alex probably owns one. Not priced | — | — |

## 4. Mechanical and metal

| # | Item | Qty | Purpose | Recommended part | Supplier · SKU · URL | Fast | Cheap |
|---|---|---|---|---|---|---|---|
| K1 | Aluminium flat bar 20 × 3 mm × 1 m | 1 | Bridge, keel and top plate: the all-metal clamp load path [D §5] | 6063-T5 flat bar | Bunnings (Metal Mate) **1064265** · bunnings.com.au/metal-mate-20-x-3mm-1m-aluminium-flat-bar-silver-1m_p1064265 | 11.01 | 11.01 |
| K2 | Spreader stock **§9.2** | 1 short length | ≤ 18 × 18 mm contact face on the package [D 3.1.2] | **20 mm square aluminium bar, filed to 18 mm** (or stacked K1 offcuts) | not priced | — | — |
| K3 | Brass M3 standoffs | 8 | Board legs and the clamp's metal legs | M3 hex, brass; **heights: MEASURE** | Altronics **H1216** (10 mm, 8-pack) · altronics.com.au/product/h1216-m3-x-10mm-tapped-spacer-pk-8 · Cheap: aliexpress.com/w/wholesale-m3-brass-standoff-kit.html. *Check whether the board came with its own standoffs first* [S] | 4.95 | 2.87–10.71 |
| K4 | Window | 1 | Clear lid, shows LEDs and the 7-segment display | 3 mm clear acrylic, 199 × 199 | Altronics **H0725** · altronics.com.au/product/h0725-199mm-x-199mm-3mm-acrylic-sheet-clear | 15.75 | 15.75 |
| K5 | Clamp spring | 1–2 | Sets 8 N (5–10 N) by its length, so force = k·(L0 − L) [D 3.1.6] | Soft compression spring, ~1–2 N/mm, stainless | not priced. **MEASURE rate and free length** | — | — |
| K6 | Ball + cone seat / plunger | 1 | Lets the spreader seat flat [D 3.1.1; T §6] | Spring plunger or steel ball | not priced | — | — |
| K7 | Locating pins | 4 | Repeatable bridge placement [D 3.1.7] | 2–3 mm steel dowels | not priced | — | — |
| K8 | Back-support post | 1 | Stops the board bending under the clamp [D 3.1.8] | Nylon M3 screw/post, insulating tip | not priced | — | — |
| K9 | FR4 strap | 1 | Holds the KSD9700 with 2 × M2, no cable ties [D 3.1.4] | Offcut of plain perfboard | not priced | — | — |

## 5. Fasteners

| # | Item | Qty | Purpose | Recommended part | Supplier · SKU · URL | Fast | Cheap |
|---|---|---|---|---|---|---|---|
| F1 | Heat-set inserts M3 × 4 | 50 | Threads in printed parts | Brass, OD 4.2 mm | Core **ADA4255** · core-electronics.com.au/brass-heat-set-inserts-for-plastic-m3-x-4mm-50-pack.html · Cheap: aliexpress.com/w/wholesale-m3-heat-set-insert-brass.html | 12.05 | 1.49–7.13 |
| F2 | M3 × 10 screws | 25 | General | Pan head | Altronics **H3120A** · altronics.com.au/product/h3120a-m3-x-10mm-pan-pozi-nickel-bolt-pk-25 · Cheap: 304 stainless M2–M5 kit, aliexpress.com/w/wholesale-m3-screw-assortment-kit-stainless.html (also covers F3) | 2.60 | 1.49–6.52 |
| F3 | M2 screws and nuts | ~16 | Pico (Ø2.1 holes take **M2, not M3**) [M], HS10 (Ø2.0–2.4 holes) [T; TM], MAX31855, KSD strap | M2 × 6–10 | fast route: not priced. Cheap: in the F2 kit | — | (in F2) |
| F4 | Knurled thumbscrews M3 | 4 | Tool-free, captive lid screws [D 3.3.13] | — | not priced | — | — |

## 6. Printing

| # | Item | Qty | Purpose | Recommended part | Supplier · SKU · URL | Fast | Cheap |
|---|---|---|---|---|---|---|---|
| R1 | PETG filament **§9.1** | 1 kg | Tub, lid frame, I/O panel, module plate, gauges, shroud | PETG (**never PLA**: it softens at 55–65 °C) | Core **CE10443** · core-electronics.com.au/bambu-lab-black-petg-hf-filament-1kg-with-spool.html · Cheap: aliexpress.com/w/wholesale-petg-filament-1kg.html | 36.00 | 17.90–26.99 |

The printer is still unknown (§9.1). If it cannot fit a part, the split option in the CAD applies.

## 7. Tools and consumables (assumed owned, not priced)

- **Multimeter**: needed for every isolation check in `wiring.md` §9. It is essential.
- Calipers, for the MEASURE list ([D §11]) and the footprint gauge.
- Soldering iron, plus a heat-set insert tip (Core ADA4239 $22.20, **out of stock** [S]).
- Hacksaw, files, drill and bits for the bar parts. Kitchen scale for the spring force [T §6].
- Solder, flux, heat-shrink, cable ties (not near the heater).

---

## Totals (derived)

Sum of the priced lines above. **Shipping not included. Unpriced lines not included.**

| Route | Total | What it assumes |
|---|---|---|
| **Local fast** | **≈ AUD 314–317** | Core / Altronics / Bunnings / Little Bird. AliExpress only for the thermostat (no local option). CE09733 for both switches. Si5351 included (§9.6 default) |
| **Cheap** | **≈ AUD 123–208** | AliExpress where it is cheaper. Pico, plug pack, acrylic, fuse parts, USB-C breakout and aluminium bar bought locally |
| Without the Si5351 (if §9.6 → defer) | local ≈ 299–302 · cheap ≈ 122–206 | |

**Still to add to both totals:** the HS10 18 Ω heater (element14/RS/DigiKey), the spring,
plunger/ball, pins, square bar, thumbscrews, M2 hardware (fast route), silicone wire,
heat-shrink, small parts, AO3400A (cheap route), the star terminal and the load switch (§9.5).
Each is probably a few dollars. The heater and the load switch may be more. **Unknown until priced.**

These totals differ from DESIGN.md §9.7 ("300–340 / 105–180") and from `suppliers-au.md`
("300–346 / 104–182"). The research priced a 10 Ω heater, a 2 A in-line fuse and two barrel
jacks. DESIGN.md changed those to 18 Ω HS10, a 1 A panel fuse and a USB-C 5 V inlet, and added
the Si5351 by default. The research's cheap route also used an exposed-bead thermocouple and
copper shims. Here the cheap route uses the insulated-junction probe and the aluminium bar
that DESIGN.md needs.

## Before ordering

1. **Alex approves the list**, and decides §9.1–9.6.
2. **Measure first** where a part depends on the board: board DC-jack size (P5), standoff
   height (K3), and **P1-34 continuity to FPGA pin 24** (E6: the Si5351 is only useful if this
   beeps [C §6.2]).
3. For E5, plan to read the shunt marking on arrival. For E4 on the cheap route, read chip-ID
   register 0xD0: 0x60 = BME280, 0x58 = BMP280, which is a fake with no humidity [M].
