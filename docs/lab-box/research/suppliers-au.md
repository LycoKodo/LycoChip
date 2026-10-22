# Australian suppliers and AUD prices for the Lab Box MVP

All prices were read on **2026-10-23** and are **unverified**: they come from web pages, not quotes. They include GST and **exclude shipping**. Feeds `docs/lab-box/BOM.md`. Nothing was bought and no accounts were created.

## TL;DR

1. **Totals (derived, below).** The local fast route (Core, Altronics, Jaycar, Bunnings, plus Little Bird for the INA226) comes to **about AUD 300–346 plus shipping** *(verifier: was "300–340". The 339.71 dearer-choice figure left out the two AliExpress parts the local route is forced to use (heater, thermostat). With them it is 340.64–345.68, derived below)*. The cheap route (AliExpress, with the plug pack, acrylic and Pico bought locally) comes to **about AUD 104–182 plus shipping** *(verifier: was "105–180". The table sums to 104.29–181.68)*. Both include the logic analyser and 1 kg of PETG. The Si5351 adds AUD 14.60 locally or AU$1.49–2.82 on AliExpress.
2. **Thermostat gap.** No local shop I could read sells a **~70 °C normally-closed (NC) thermostat rated for 12 V DC at 1.2 A or more**. Jaycar's ST3823 is 70 °C NC, but its contacts are rated **32 VDC 100 mA**, so it cannot switch the heater directly. Altronics' S5612 trips at **90 °C**. The AliExpress KSD9700 listings give **AC ratings only** (5 A 250 V). *(Verifier: confirmed that ST3823 is rated 32 VDC 100 mA, and so are Jaycar's 60 °C ST3821 and 90 °C ST3825. The rating belongs to the whole family. One correction: the AliExpress titles say "250V 5A" and **do not say whether that is AC or DC**. The one named-maker KSD9700 checked, Xucheng KSD9700-80/5JSB/080A at LCSC, states "AC 250V … 5A (resistive load)" and gives no DC rating. The conclusion stands: no DC rating was found.)*
3. **Heater gap.** No aluminium-clad 10 Ω 25 W resistor at Core, Jaycar or Altronics. element14, RS and DigiKey pages returned **HTTP 403**, so I have no AUD price from them. AliExpress RX24 parts are AU$0.55–2.69. At 12 V, 10 Ω gives **1.2 A and 14.4 W (derived)**, so Jaycar's 10 W RR3352 is under-rated. *(Verifier: the "25 W" on an aluminium-clad resistor assumes a large heat sink. Vishay's RH025 is rated 25 W on a 5 × 7 × 2 in aluminium chassis, but only **12.5 W in free air** (Vishay doc 30201, rev. 02-Sep-2026, p.3, datasheet). So 14.4 W at full duty is also over the free-air rating of a "25 W" part. A 20 mm spreader is not that heat sink. At full duty, only the control loop and the thermostat keep the heater in bounds.)*
4. **INA226.** Core, Jaycar and Altronics do not list one. Little Bird (Sydney) has the **CJMCU-226 at $3.30** *(verifier: the page does not say whether GST is included, or what the shunt value is)*. With a 0.1 Ω shunt it reads up to **±0.819 A** (derived from TI's ±81.92 mV). Read the shunt marking before you rely on that.
5. **Where the money goes locally:** logic analyser $49.30, PETG $36.00, MAX31855 breakout $28.25, 12 V 2 A plug pack $24.75–26.35, BME280 $23.50. **Buy the plug pack locally**: Australian approval matters, and AliExpress adapters were not priced.

**How the prices were read.**
- **Core Electronics** and **Altronics**: from each product page's own structured data (schema.org JSON-LD or microdata), downloaded with a script this session.
- **Jaycar**: jaycar.com.au returns 403 to automated fetches. Prices come from Jaycar's own storefront host `jaycar-prod.australia-southeast1.gcp.storefrontcloud.io` where noted, otherwise from a search-engine snippet.
- **AliExpress**: from search-results pages. Each figure is the **displayed price of the cheapest variant or pack size, before shipping**. **AU$1.49 shows up on many unrelated items.** That pattern looks like a new-user promotion, so treat AU$1.49 as a floor, not the real price (inference).
- **Bunnings**: from the JSON embedded in its search page.
- **element14 AU, RS AU, DigiKey AU, Core's shipping page, Officeworks product data**: blocked (403) or not readable.

## Facts table

Unit for every price is **AUD incl. GST, unverified, checked 2026-10-23**. "Core" = core-electronics.com.au, "Alt" = altronics.com.au, "Jay-SFC" = Jaycar storefrontcloud host, "Ali" = aliexpress.com search page.

| Item | Value | Unit | Source | Confidence | Notes |
|---|---|---|---|---|---|
| **1. Controller** | | | | | |
| Raspberry Pi Pico 2H (RP2350, headers soldered), Core **CE10154** | 9.90 | AUD | core-electronics.com.au/raspberry-pi-pico-2-h-with-headers.html | listing | In stock (48 local). **Design for this one** |
| Raspberry Pi Pico 2 (no headers), Core CE09936 | 8.70 | AUD | core-electronics.com.au/raspberry-pi-pico-2.html | listing | In stock |
| Raspberry Pi Pico H (RP2040, headers), Core CE08702 | 8.65 | AUD | core-electronics.com.au/raspberry-pi-pico-h-with-headers.html | listing | In stock |
| Raspberry Pi Pico (RP2040, no headers), Core CE07564 | 6.60 | AUD | core-electronics.com.au/raspberry-pi-pico.html | listing | **Out of stock** |
| Pico 2 RP2350, Alt ZA6421 / Pico H, Alt Z6421B / Pico, Alt Z6421 | 15.25 / 15.00 / 8.95 | AUD | altronics.com.au/product/za6421-…, z6421b-…, z6421-… | listing | In stock |
| "Pico 2" listings, Ali | 1.49–21.39 | AUD | aliexpress.com/w/wholesale-raspberry-pi-pico-2.html | listing | Mostly third-party RP2350 boards. None verifiably official. Not worth it at Core's price |
| **2. Package thermometer** | | | | | |
| Adafruit MAX31855 breakout v2.0, Core **ADA269** | 28.25 | AUD | core-electronics.com.au/thermocouple-amplifier-max31855-breakout-board-max6675-upgrade-v2-0.html | listing | In stock (9). Includes terminal block, **no thermocouple** |
| SparkFun MAX31855K breakout, Core SEN-13266 | 34.95 | AUD | core-electronics.com.au/sparkfun-thermocouple-breakout-max31855k.html | listing | Backorder |
| MAX31855 modules, Ali | 2.81–13.79 | AUD | aliexpress.com/w/wholesale-max31855-module.html | listing | Several titles say "MAX31855 MAX6675". Whether the chip is genuine is unverified |
| Adafruit K-type thermocouple, glass braid, Core **ADA270** | 19.95 | AUD | core-electronics.com.au/thermocouple-type-k-glass-braid-insulated-k.html | listing | **Exposed bead**. 1 m, 500 °C, 2.18 mm thick. "Insulated" in the name refers to the braid, not the junction |
| SparkFun K-type stainless probe, Core SEN-13715 | 18.25 | AUD | core-electronics.com.au/thermocouple-type-k-stainless-steel.html | listing | 200 mm × 5 mm rigid probe with a mini connector. Wrong shape for a package top |
| DFRobot K-type, Core SEN0139 | 4.65 | AUD | core-electronics.com.au/k-type-thermocouple.html | listing | 3 × 25 mm stainless tip, **125 mm** leads (too short to reach a MAX31855 in the cool zone) |
| K-type multimeter probe, Alt Q1127 | 14.95 | AUD | altronics.com.au/product/q1127-micron-k-type-multimeter-temperature-probe | listing | 700 mm lead, banana plugs (cut off) |
| K-type "ungrounded" sheathed bendable probe, 1/2/3/5 mm, Ali | 4.19–13.49 | AUD | aliexpress.com/w/wholesale-k-type-thermocouple-ungrounded-1mm.html | listing | The only **insulated-junction** option found. Choose a 1 mm sheath |
| K-type PTFE probe, exposed welded junction, mini plug, Ali | 5.81 | AUD | aliexpress.com/item/1005012638354764.html | listing | Exposed junction |
| **3. Ambient sensor** | | | | | |
| PiicoDev BME280, Core **CE07503** | 23.50 | AUD | core-electronics.com.au/piicodev-atmospheric-sensor-bme280.html | listing | In stock (18). 25.4 × 25.4 mm, 2.54 mm header pads, I²C 0x77 (0x76 with switch). Its connector is 3.3 V only. **Design for this one**. *(Verifier: re-read; all confirmed. The page also gives **2 × M2.5 mounting holes**, listing; their positions are not given, so MEASURE them)* |
| Adafruit BME280, Core ADA2652 | 26.30 | AUD | core-electronics.com.au/adafruit-bme280-i2c-or-spi-temperature-humidity-pressure-sensor.html | listing | Lead time: dispatch 2–4 Nov |
| SparkFun BME280 with headers, Core SEN-13905 | 38.60 | AUD | core-electronics.com.au/sparkfun-atmospheric-sensor-breakout-bme280-with-headers.html | listing | Backorder |
| BME280 sensor, Alt Z6455 | 37.50 | AUD | altronics.com.au/product/z6455-bme280-temperature-humidity-pressure-sensor | listing | In stock |
| GY-BME280 modules, Ali | 1.49–12.29 | AUD | aliexpress.com/w/wholesale-bme280-module.html | listing | Titles mix **BME280 and BMP280**. The BMP280 has no humidity sensor |
| **4. Power sensor** | | | | | |
| CJMCU-226 INA226 module, Little Bird **LB-LS0221** | 3.30 | AUD | littlebirdelectronics.com.au/products/cjmcu-226-ina226-voltage-current-power-monitor-alarm-module-36v-bi-directional-i2c | listing | In stock (9 local, 250 supplier). Australian (Sydney) shop; not on the preferred list but the only local INA226 found. *(Verifier: the price and stock are confirmed. The page **does not say whether GST is included**. It **does not state the shunt value or the board size**. It also says "12 programmable addresses", while the TI datasheet says 16, so the listing text is unreliable)* |
| INA226 at Core / Jaycar / Altronics | none found | – | site searches, 2026-10-23 | listing | Core lists INA219, INA260, INA228 and INA3221 instead |
| INA226 / CJMCU-226 modules, Ali | 1.49–10.79 | AUD | aliexpress.com/w/wholesale-ina226-module.html | listing | Includes 2-packs |
| Adafruit INA219, Core **ADA904** (fallback) | 17.30 | AUD | core-electronics.com.au/ina219-high-side-dc-current-sensor-breakout-26v-3-2a-max.html | listing | In stock (13). 0.1 Ω 1 % 2 W shunt, rated 26 V ±3.2 A. *(Verifier: confirmed. The page also gives 25.6 × 20.4 × 4.7 mm and I²C addresses 0x40 / 0x41 / 0x44 / 0x45, set with jumpers, listing)* |
| Adafruit INA260 ADA4226 / INA228 ADA5832 / INA3221 ADA6062, Core | 18.45 / 29.10 / 20.45 | AUD | core-electronics.com.au (product pages) | listing | Alternatives, in stock |
| INA219 modules, Ali | 1.49–3.99 | AUD | aliexpress.com/w/wholesale-ina219-module.html | listing | |
| INA226 shunt input range | ±81.92 | mV | TI INA226 datasheet Rev. C, ti.com/lit/ds/symlink/ina226.pdf, p.5 | datasheet | Same datasheet, p.1: 16 programmable addresses, 0–36 V bus, 2.7–5.5 V supply. *(Verifier: re-derived from SBOS547C (revised Aug 2026), §5.5, p.5. The exact range is **−81.9175 to +81.92 mV**. Table 6-2 puts the 16 addresses at 0x40–0x4F, so they share the INA219 range but not the BME280's 0x76/0x77)* |
| INA226 full scale with a 0.1 Ω (R100) shunt | 0.819 | A | 81.92 mV ÷ 0.1 Ω | derived | With 0.01 Ω (R010): 8.19 A. The sibling note `board-power.md` estimates the board draws 70–290 mA (derived, not measured). *(Verifier: the arithmetic checks out (0.08192 / 0.1 = 0.8192 A). `board-power.md` now puts the high case at ≈ 320 mA with worst-case silicon, still under 0.819 A. Valid only if the CJMCU-226 shunt really is R100; Little Bird does not state it)* |
| **5. Clock knob (conditional; `clock-pins.md` says it stays)** | | | | | |
| Adafruit Si5351A breakout, Core **ADA2045** | 14.60 | AUD | core-electronics.com.au/adafruit-si5351a-clock-generator-breakout-board-8khz-to-160mhz.html | listing | In stock (2 local). 31 × 22 × 2 mm, 3–5 V supply, I²C level-shifted. Page text says "<8 kHz up to 150+ MHz" |
| Adafruit Si5351A STEMMA QT, Core ADA5640 | 13.90 | AUD | core-electronics.com.au/adafruit-si5351a-clock-generator-with-stemma-qt-8khz-to-160mhz.html | listing | Backorder |
| CJMCU-5351 modules, Ali | 1.49–2.82 | AUD | aliexpress.com/w/wholesale-si5351a-module.html | listing | |
| **6. MOSFET switch modules (×2)** | | | | | |
| MOSFET Power Switch Module, Core **CE09733** | 1.35 each | AUD | core-electronics.com.au/mosfet-power-switch-module.html | listing | In stock (327). 2× AOD4184, "3.3–5 V logic", 10 A / 30 V load, about 34 × 17 × 14 mm, headers not included. **Design for this one** |
| MOSFET Module (screw terminals), Core CE09435 | 1.80 | AUD | core-electronics.com.au/mosfet-module-screw-terminals.html | listing | Rated for **5 V logic** and 3 A: not suited to the Pico's 3.3 V |
| D4184 / "isolated MOSFET" modules, Ali | 0.86–8.76 | AUD | aliexpress.com/w/wholesale-d4184-mosfet-module.html | listing | Many are opto-isolated variants |
| AOD4184A gate threshold V(GS)th | 1.7 / 2.1 / 2.6 (min/typ/max) | V | AOS AOD4184A datasheet, electrical characteristics (aosmd.com/res/datasheets/AOD4184A.pdf) | datasheet | R(DS)on is < 9.5 mΩ at V(GS) = 4.5 V. **No figure is given at 3.3 V**. *(Verifier: re-derived from AOD4184A Rev1.0 (Sept 2023), p.2. V(GS)th is measured at V(DS) = V(GS), I(D) = 250 µA. R(DS)on is 7.6 typ / 9.5 max mΩ at V(GS) = 4.5 V, I(D) = 15 A. The part is rated 40 V. Core's page says "AOD4184", so the fitted MOSFET may be the non-A part or a "D4184" clone: read the marking)* |
| **7. Fan (40 mm)** | | | | | |
| 40 × 40 × 10 mm fan, Core **CE10142** | 2.40 | AUD | core-electronics.com.au/40x40mm-5v-fan-dupont-connector.html | listing | 5 V, about 200 mA, 2-wire Dupont lead, 4 mm holes, no tach. *(Verifier: confirmed, including "functions down to 3.3V" and a 20 cm lead. The page does **not** give the hole spacing, RPM, airflow or wire count. "2-wire" and "no tach" are inferred from what is missing, so they are UNVERIFIED. MEASURE the hole spacing)* |
| Adafruit 5 V USB fan 4 cm, Core ADA6101 | 13.45 | AUD | core-electronics.com.au/adafruit-5v-usb-fan-4cm-cooling.html | listing | USB plug |
| Sunon MF40100V1-1000U-A99 5 V 40 mm, Alt F1110 | 19.50 | AUD | altronics.com.au/product/f1110-sunon-40mm-5vdc-maglev-bearing-fan | listing | Named maker part, so a datasheet is available |
| 40 mm 12 V 3-wire ball-bearing fan, Jaycar **XC5054** | 19.95 | AUD | Jay-SFC /40mm-3-wire-12v-dc-ball-bearing-fan/p/XC5054 | listing | 80 mA, 6000 RPM, **tach output at 1 pulse/rev**. Can run from the 12 V adapter |
| 4010 5 V fans, Ali | 1.49–11.99 | AUD | aliexpress.com/w/wholesale-4010-5v-fan.html | listing | 2-pin, 3-pin and 4-pin PWM variants listed |
| **8. Heater** | | | | | |
| RX24 aluminium-shell wirewound resistor 25 W (10 Ω option), Ali | 0.55–2.69 | AUD | aliexpress.com/w/wholesale-aluminum-shell-resistor-25w-10-ohm.html | listing | The price shown is the cheapest variant, not necessarily 10 Ω / 25 W. *(Verifier: "25 W" on this style of part is a heat-sink rating. For comparison, Vishay's RH025 is **12.5 W in free air** (doc 30201 p.3, datasheet). A no-name RX24 has no datasheet, so its free-air rating is unknown)* |
| "RH-25 10R 1 %" aluminium resistors, 3–10 pcs, Ali | 25.59 | AUD | aliexpress.com/item/1005012491094277.html | listing | Claims to be the Vishay part. Unverified |
| Vishay RH02510R00FC02 (10 Ω 25 W ±1 %), element14 AU order code 1653237 | **not fetched** | – | au.element14.com/vishay/rh02510r00fc02/…/dp/1653237 (search index; page returned 403) | unknown | Name brand. Get the price by hand |
| Arcol HS25 10R J, RS AU stock no. 1664092 | **not fetched** | – | au.rs-online.com/web/p/chassis-mount-resistors/1664092 (page returned 403) | unknown | One RS listing gives the HS25 body as about 27.3 × 28 × 14.8 mm (search snippet only, unverified). *(Verifier: the RS listings **disagree**. HS25 "wire wound" parts are listed at 51 × 28 × 14.6 mm and "aluminium" parts at 27.3 × 28 × 14.8 mm. Arcol's own datasheet did not load (HTTP 522). UNVERIFIED: do not model the clamp from either number)* |
| 10 Ω 10 W axial wirewound, Jaycar RR3352 | 1.80 | AUD | Jay-SFC /10-ohm-10-watt-wire-wound-resistor/p/RR3352 | listing | **Under-rated**: 14.4 W at 12 V. Axial body, nothing flat to clamp |
| 12 V polyimide film heaters, sizes from 7–14 mm up, Ali | 3.46–4.52 | AUD | aliexpress.com/w/wholesale-12v-polyimide-heater-film.html | listing | Wattage depends on size. Check it per size before ordering |
| Adafruit heating pad 10 × 5 cm, Core ADA1481 | 11.90 | AUD | core-electronics.com.au/electric-heating-pad-10cm-x-5cm.html | listing | Fabric pad, much bigger than a 20 mm package |
| Heater current and power, 10 Ω at 12 V | 1.2 / 14.4 | A / W | I = 12/10, P = 12²/10 | derived | 100 % duty |
| **9. Safety backstop** | | | | | |
| 70 °C thermal circuit breaker, NC, auto-reset, Jaycar **ST3823** | 6.75 (SFC) / 6.50 (search snippet) | AUD | Jay-SFC /70-c-thermal-circuit-breaker/p/ST3823; jaycar.com.au/70-c-thermal-circuit-breaker/p/ST3823 | listing | Trips 70 °C, resets 58 °C, ±5 °C at 32 VDC. Contacts **32 VDC 100 mA**, 125 VAC 10 A, 250 VAC 6 A. 30.3 mm dia × 21.2 mm. *(Verifier: every figure re-read from the SFC page and confirmed. Jaycar's 60 °C ST3821 (NC, resets at 40 °C) and 90 °C ST3825 are also rated "32VDC-100mA", so no Jaycar ST382x part can carry the heater current)* |
| 90 °C NC thermal circuit breaker, Alt S5612 | 5.50 | AUD | altronics.com.au/product/s5612-90-degree-nc-thermal-circuit-breaker | listing | 10 A 250 VAC, mounting-hole centres 23.5 mm. **Trips above the FPGA's 85 °C rating**. *(Verifier: confirmed from the page. It also gives a 16 mm contact surface. It gives **no DC rating, no reset temperature and no body size**. The 85 °C is the commercial **junction** limit (0–85 °C): Cyclone IV datasheet CYIV-53001-1.7, Table 1–3, p.4, datasheet)* |
| 77 °C thermal fuse (one-shot), Alt S5631 | 3.60 | AUD | altronics.com.au/product/s5631-77-degree-celsius-thermal-fuse | listing | Electrical rating not shown in the page data |
| KSD9700 NC, 5 A 250 V, options 15–70 °C, Ali | 0.38–0.55 | AUD | aliexpress.com/w/wholesale-ksd9700-70c-normally-closed.html | listing | **No DC rating stated**. *(Verifier: re-fetched and the same AU$0.38 / 0.55 listings are present. No title says AC or DC. For a named maker, LCSC C51934112 (Xucheng KSD9700-80/5JSB/080A) states AC 250 V 5 A resistive and **no DC rating** (listing))* |
| KSD9700 NC 16 A metal-cap, options include 70 °C, Ali | 3.28 | AUD | aliexpress.com/item/1005013205364883.html | listing | **No DC rating stated** |
| In-line 3AG fuse holder, Alt **S6001** | 1.70 | AUD | altronics.com.au/product/s6001-3ag-3a-12vdc-in-line-fuse-holder | listing | Rated 3 A at 12 VDC, leads about 140 mm |
| In-line M205 fuse holder, Alt S6004 | 3.00 | AUD | altronics.com.au/product/s6004-10a-in-line-m205-fuse-holder | listing | 10 A, 32 VDC |
| 2 A fast-blow fuse: 3AG Alt S5804 / M205 Alt S5734 | 0.40 / 0.40 | AUD | altronics.com.au/product/s5804-2a-6x32-fuse; …/s5734-2a-m205-fuse | listing | |
| 3AG in-line fuse holder, Jaycar SZ2015 | 2.00 | AUD | Jay-SFC /5a-3ag-inline-fuse-holder-standard-duty/p/SZ2015 | listing | **Comes with a 5 A fuse.** Swap it for a 2 A fuse |
| 5 × 20 mm in-line holders, 5–10 pcs, Ali | 1.49 | AUD | aliexpress.com/w/wholesale-5x20-fuse-holder-inline.html | listing | |
| **10. Power in** | | | | | |
| 12 V 2 A plug pack, fixed 2.1 mm tip-positive plug, Alt **M8936D** | 24.75 | AUD | altronics.com.au/product/m8936d-powertran-12v-dc-2a-fixed-21mm-tip-appliance-plugpack | listing | Page says "Energy authority approved. MEPS approved." The RCM mark itself is not shown; check the label. *(Verifier: confirmed. The page also gives a **1.8 m** lead, 44 W × 80 H × 40 D mm, regulated, centre positive)* |
| 12 V 2 A plug pack, **2.5 mm** tip-positive plug, Alt MB8936C | 24.75 | AUD | altronics.com.au/product/mb8936c-powertran-12v-dc-2a-fixed-25mm-tip-positive-appliance-plugpack | listing | 2.5 ID × 5.5 OD × 10 L mm, 75 × 42 × 40 mm. Lets the 12 V and 5 V plugs differ (see Discussion). *(Verifier: the plug size is confirmed. **The body size contradicts itself on the page**: "75L x 42W x 40D mm" in one place and "44W x 80H x 40D mm" in another. The lead is 1.2 m)* |
| 12 V 2 A plug pack, 2.1 mm, Core AM8936 | 26.35 | AUD | core-electronics.com.au/12v-dc-2a-fixed-2-1mm-tip-appliance-plugpack.html | listing | Same description as M8936D, and its GTIN (9321758226322) carries Altronics' 9321758 prefix, so it is **probably the same unit** (inference). 1.2 m lead, 5.5/2.1 plug. *(Verifier: **weakened**. AM8936 has a 1.2 m lead and M8936D has 1.8 m, so they are not the same SKU. At most they are the same family (UNVERIFIED). The GTIN was not shown when re-fetched. Core lists the brand as "Core Electronics". Its body size contradicts itself on the page: 75 × 30 × 50 mm and 75 × 42 × 40 mm)* |
| 5 V 2 A plug pack, 2.1 mm tip-positive, Alt M8904A | 21.95 | AUD | altronics.com.au/product/m8904a-powertran-5v-dc-2a-fixed-21mm-tip-appliance-plugpack | listing | Only needed if the FPGA board is fed from its barrel jack through the INA226. Its plug must fit the board's jack, which has **not been measured** |
| 2.1 mm plastic chassis DC socket, Alt **P0628** | 2.25 | AUD | altronics.com.au/product/p0628-21mm-female-plastic-chassis-mount-dc-power-socket | listing | 13 mm hole, 3 A 12 VDC max. *(Verifier: confirmed. The page gives no panel-thickness limit and no body depth: MEASURE)* |
| 2.1 mm metal chassis DC socket, Alt P0622 | 5.35 | AUD | altronics.com.au/product/p0622-21mm-female-metal-chassis-mount-dc-power-socket | listing | 8 mm hole. *(Verifier: confirmed. The page also gives max 5.0 A at 24 V DC. No panel-thickness limit is given)* |
| 2.5 mm DC socket: plastic Alt P0629 / metal Alt P0623 | 2.25 / 4.75 | AUD | altronics.com.au search tiles (product pages not opened) | listing | Pair with MB8936C |
| Adafruit panel-mount 2.1 mm jack, Core ADA610 | 5.45 | AUD | core-electronics.com.au/panel-mount-2-1mm-dc-barrel-jack.html | listing | For panels up to 8 mm thick |
| 2.1 mm bulkhead DC connector, Jaycar PS0522 | 2.95 | AUD | Jay-SFC /2-1mm-bulkhead-male-dc-power-connector/p/PS0522 | listing | Spec table contradicts itself (also says "2.5mm Socket"). Do not design around it |
| DC-022 5.5 × 2.1 panel jacks, 5–10 pcs, Ali | 1.49–3.34 | AUD | aliexpress.com/w/wholesale-dc-022-panel-jack.html | listing | |
| DC lead, 2.1 mm tip-positive plug, 30 cm, Alt **P6714** | 3.40 | AUD | altronics.com.au/product/p6714-pigtail-dc-power-lead-21mm-plug-30cm-tip-positive | listing | Bare ends |
| Female barrel to screw terminal, Core CE08698 | 1.40 | AUD | core-electronics.com.au/female-dc-barrel-jack-adapter-21mm.html | listing | |
| 5.5/2.1 DIY plug: Core ADA3310 / Core PRT-11476 | 2.05 / 2.15 | AUD | core-electronics.com.au/5-5-2-1mm-barrel-connector-dc-power-plug.html; …/dc-barrel-jack-plug-male.html | listing | |
| 5.5 × 2.1 male/female pigtails, 5–10 pcs, Ali | 1.49 | AUD | aliexpress.com/item/1005007317225328.html | listing | |
| **11. Thermal stack** | | | | | |
| Aluminium flat bar 20 × 3 mm × 1 m, Bunnings (Metal Mate) | 11.01 | AUD | bunnings.com.au/metal-mate-20-x-3mm-1m-aluminium-flat-bar-silver-1m_p1064265 | listing | Cut into 20 × 20 × 3 mm blanks, with many spares |
| Copper shims 15 × 15 / 20 × 20 mm, 0.3–2 mm thick, 5–20 pcs, Ali | 1.49–1.99 | AUD | aliexpress.com/w/wholesale-copper-shim-20x20.html | listing | Thinner than 3 mm |
| EP4CE6 E144 body size (D1 = E1) | 20.00 | mm | `resources/.../Cyclone IV chip/EP4CE6 package information.pdf` p.1 (Altera 04R-00402-1.0) | datasheet | Across the leads (D = E): 22.00 mm. Height A: 1.45 / 1.55 / 1.65 mm (min/nom/max). *(Verifier: re-read on p.1 and confirmed. A is the seated height above the PCB, including the A1 stand-off of 0.05–0.15 mm. Derived: a 20 × 20 mm spreader is exactly the body size, so it has **zero** lateral margin before it overhangs the leads)* |
| Thermal transfer tape 100 × 100 × 0.5 mm, Jaycar NM2790 | 18.95 | AUD | Jay-SFC /thermal-transfer-tape-100x100x0-5mm/p/NM2790 | listing | 1.6 W/m·K, −60 to 250 °C, self-adhesive. Spec row reads "Insulation Voltage 7.0 V" (sic) |
| 3M 8810 thermal tape 80 × 80 mm, Core ADA1468 | 8.75 | AUD | core-electronics.com.au/heat-sink-thermal-tape-3m-8810-80mm-x-80mm.html | listing | Adhesive tape, not a compliant gap pad |
| Silicone thermal pads, 0.5–3 mm, Ali | 1.49–3.55 | AUD | aliexpress.com/w/wholesale-thermal-pad-1mm.html | listing | Claimed 6–22 W/m·K, unverified. A non-adhesive gap pad was found **only on AliExpress** |
| Polyimide (Kapton) tape 8 mm × 33 m, Alt **T2971A** / 12 mm, Alt T2972A | 11.50 / 14.50 | AUD | altronics.com.au/product/t2971a-…; …/t2972a-… | listing | In stock |
| Polyimide tape 10 mm × 33 m, Core ADA3057 | 12.15 | AUD | core-electronics.com.au/high-temperature-polyimide-tape-1cm-wide-x-33-meter-roll.html | listing | Backorder |
| Kapton tape, Ali | 1.49–3.07 | AUD | aliexpress.com/w/wholesale-kapton-tape.html | listing | |
| **12. Fasteners** | | | | | |
| Brass heat-set inserts M3 × 4 mm, 50-pack, Core **ADA4255** | 12.05 | AUD | core-electronics.com.au/brass-heat-set-inserts-for-plastic-m3-x-4mm-50-pack.html | listing | **OD 4.2 mm**, length 4 mm (from the page text) |
| Brass heat-set inserts M3 × 3 mm, 50-pack, Core ADA4256 | 12.15 | AUD | core-electronics.com.au/brass-heat-set-inserts-for-plastic-m3-x-3mm-50-pack.html | listing | **OD 4.5 mm**, length 3 mm |
| Heat-set tip for Hakko T18 irons, Core ADA4239 | 22.20 | AUD | core-electronics.com.au/heat-set-insert-for-soldering-irons-4-40-m3-inserts.html | listing | Out of stock |
| M3 heat-set insert kits, Ali | 1.49–7.13 | AUD | aliexpress.com/w/wholesale-m3-heat-set-insert-brass.html | listing | Dimensions vary by seller |
| M3 × 10 pan Pozi screws, nickel, 25-pack, Alt **H3120A** | 2.60 | AUD | altronics.com.au/product/h3120a-m3-x-10mm-pan-pozi-nickel-bolt-pk-25 | listing | |
| M3 × 10 pan Phillips screws, zinc steel, 25-pack, Core POLOLU-2695 | 4.30 | AUD | core-electronics.com.au/machine-screw-m3-10mm-length-phillips-25-pack.html | listing | |
| 304 stainless M2–M5 screw assortments, Ali | 1.49–6.52 | AUD | aliexpress.com/w/wholesale-m3-screw-assortment-kit-stainless.html | listing | |
| M3 × 10 tapped spacer, chrome-plated brass, 8-pack, Alt **H1216** | 4.95 | AUD | altronics.com.au/product/h1216-m3-x-10mm-tapped-spacer-pk-8 | listing | 15 mm: H1233 $6.95. 20 mm: H1250 $6.95. 25 mm: H1266 $7.50 (search tile) |
| SparkFun 210-piece brass standoff kit, Core KIT-24115 | 40.45 | AUD | core-electronics.com.au/standoff-kit-210-piece.html | listing | M3 and M2.5 |
| DFRobot M3 × 10 hex standoffs, 10 sets, Core FIT0063 | 3.96 | AUD | core-electronics.com.au/10-sets-m3-10-hexagonal-standoffs-mounting-kit.html | listing | Material not stated |
| M3 brass standoff kits, Ali | 2.87–10.71 | AUD | aliexpress.com/w/wholesale-m3-brass-standoff-kit.html | listing | |
| **13. Window** | | | | | |
| Clear acrylic 199 × 199 × 3 mm, Alt **H0725** | 15.75 | AUD | altronics.com.au/product/h0725-199mm-x-199mm-3mm-acrylic-sheet-clear | listing | In stock |
| Clear acrylic 195 × 195 × 3 mm, Jaycar HM9509 | 14.95 | AUD | Jay-SFC /clear-acrylic-sheet/p/HM9509 | listing | Marked "Clearance" |
| Suntuf clear acrylic 900 × 600 × 5 mm, Bunnings | 99.94 | AUD | bunnings.com.au/suntuf-900-x-600-x-5mm-clear-acrylic-sheet-clear_p1010490 | listing | Only clear acrylic Bunnings lists. Too big and too thick |
| xTool 1 mm clear acrylic, 300 × 300, 10-pack, Core CE10523 | 33.98 | AUD | core-electronics.com.au/xtool-1mm-clear-acrylic-sheets-10pcs.html | listing | 1 mm, thinner than the 2–3 mm target |
| Officeworks clear acrylic 2–3 mm | none found | – | officeworks.com.au search (only polypropylene sheets) | listing | |
| **14. External eyes and wiring** | | | | | |
| SparkFun USB Logic Analyzer 24 MHz / 8-ch, Core **TOL-18627** | 49.30 | AUD | core-electronics.com.au/usb-logic-analyzer-24mhz-8-channel.html | listing | sigrok/PulseView. Inputs 5.25 V max, V_IH ≥ 2.0 V, V_IL ≤ 0.8 V. USB-C, 54.7 × 27.4 × 14.1 mm |
| 24 MHz 8-ch logic analyser clones, Ali | 5.44–11.40 | AUD | aliexpress.com/w/wholesale-24mhz-8-channel-logic-analyzer.html | listing | Generic, same class |
| Jumper wires 20 cm F/F × 40, Core **CE05098** / M/F × 40, Core CE09130 | 3.95 / 3.95 | AUD | core-electronics.com.au/solderless-breadboard-jumper-cable-wires-female-female-40-pieces.html; …/male-female-jumper-wire-40-20cm.html | listing | 30 AWG |
| Mixed jumper pack, 60 pcs, Alt P1017 | 12.75 | AUD | altronics.com.au/product/p1017-prototyping-jumper-wires-mixed-for-breadboard-arduino | listing | |
| 20 cm Dupont packs, Ali | 3.94–4.21 | AUD | aliexpress.com/item/32944533429.html; …/1005007481724098.html | listing | |
| **15. Print material** | | | | | |
| Bambu Lab PETG-HF black, 1 kg with spool, Core **CE10443** | 36.00 | AUD | core-electronics.com.au/bambu-lab-black-petg-hf-filament-1kg-with-spool.html | listing | In stock. The refill (CE10572, $30.99) is out of stock |
| PETG 1 kg, Ali | 17.90 (Anycubic) – 26.99 (Geeetech) | AUD | aliexpress.com/w/wholesale-petg-filament-1kg.html | listing | No Australian warehouse mentioned |
| PETG at Altronics | none found | – | altronics.com.au search "PETG" | listing | Lists Creality PLA and ABS only |
| **Board context (from vendor docs)** | | | | | |
| How the FPGA board is powered | USB, or a 5 V adapter, chosen by a push switch | – | `resources/.../Dev Board Manual.pdf` p.1; schematic V2.1 ("外部+5V电源" → 1117-3.3 / -2.5 / -1.2) | vendor-doc | |
| Board barrel-jack size | unknown | mm | not stated in the manual or schematic; the jack is visible in `board.jpg` | unknown | Measure it (see Must measure) |

## Discussion

### Suggested BOM picks (design for these)

| # | Part | Local fast route | AUD | Cheap route | AUD |
|---|---|---|---|---|---|
| 1 | Pico | Core CE10154 Pico 2H | 9.90 | same (Core) | 9.90 |
| 2 | MAX31855 | Core ADA269 | 28.25 | Ali module | 2.81–9.60 |
| 3 | Thermocouple | Core ADA270 (bead, Kapton over it) | 19.95 | Ali 1 mm ungrounded or exposed junction | 1.49–5.81 |
| 4 | BME280 | Core CE07503 | 23.50 | Ali GY-BME280 | 1.49–12.29 |
| 5 | INA226 | Little Bird LB-LS0221 | 3.30 | Ali CJMCU-226 | 1.49–4.72 |
| 6 | MOSFET module ×2 | Core CE09733 ×2 | 2.70 | Ali D4184 ×2 | 1.72–5.38 |
| 7 | Fan | Core CE10142 (5 V) | 2.40 | Ali 4010 5 V | 1.49–4.16 |
| 8 | Heater | *no local source found*: Ali RX24 | 0.55–2.69 | Ali RX24 | 0.55–2.69 |
| 9 | 70 °C NC thermostat | *no suitable local part*: Ali KSD9700 | 0.38–3.28 | Ali KSD9700 | 0.38–3.28 |
| 10 | Fuse holder + 2 A fuse | Alt S6001 + S5804 | 2.10 | Ali holder + Alt fuse | 1.89 |
| 11 | 12 V 2 A plug pack | Alt M8936D (or MB8936C) | 24.75 | same (local only) | 24.75 |
| 12 | Panel jacks ×2 | Alt P0628 ×2 | 4.50 | Ali DC-022 pack | 1.49–3.34 |
| 13 | Pigtails ×2 | Alt P6714 ×2 | 6.80 | Ali pack | 1.49–2.55 |
| 14 | Heat spreader | Bunnings 20 × 3 mm aluminium bar | 11.01 | Ali copper shims | 1.49–1.99 |
| 15 | Thermal pad | Jaycar NM2790 (adhesive tape) | 18.95 | Ali silicone pad | 1.49–3.55 |
| 16 | Kapton tape | Alt T2971A | 11.50 | Ali | 1.49–3.07 |
| 17 | Heat-set inserts | Core ADA4255 | 12.05 | Ali kit | 1.49–7.13 |
| 18 | M3 screws | Alt H3120A | 2.60 | Ali kit | 1.49–6.52 |
| 19 | Brass standoffs | Alt H1216 (10 mm, 8-pack) | 4.95 | Ali kit | 2.87–10.71 |
| 20 | Clear acrylic | Alt H0725 | 15.75 | same (local) | 15.75 |
| 21 | Logic analyser | Core TOL-18627 | 49.30 | Ali clone | 5.44–11.40 |
| 22 | Jumpers | Core CE05098 + CE09130 | 7.90 | Ali pack | 3.94–4.21 |
| 23 | PETG 1 kg | Core CE10443 | 36.00 | Ali | 17.90–26.99 |
| | **Total (derived, sum of the column, no shipping)** | | **≈ 299–304** | | **≈ 104–182** |
| | Si5351 (conditional) | Core ADA2045 | +14.60 | Ali | +1.49–2.82 |

**Calculation.**
- **Local column:** the fixed prices sum to **298.16**. Adding the two AliExpress items it is forced to use (heater 0.55–2.69, thermostat 0.38–3.28) gives **299.09–304.13**.
- **Dearer local choices** raise that to about **339.71**: Jaycar XC5054 tach fan instead of CE10142, INA219 ADA904 instead of the INA226, Core AM8936 instead of the Altronics plug pack, Core ADA610 jacks, and 15 mm standoffs.
  - *Correction (verifier):* the swaps add 17.55 + 14.00 + 1.60 + 6.40 + 2.00 = **41.55**. The author added them to 298.16, which **leaves out** the heater and thermostat the local route has to buy from AliExpress. The correct figure is 299.09–304.13 + 41.55 = **340.64–345.68** (derived; re-summed with a script this session).
- **Cheap column:** low **104.29**, high **181.68**.
- **Shipping is extra and unknown.** Core's shipping page returned 403. Altronics prices freight in the basket. AliExpress shipping depends on the seller.

**Things Alex may already own.** The vendor photo (`board.jpg`) shows the board sitting between acrylic plates on brass standoffs (photo-estimate). Check whether your board came with them before buying standoffs. Also check for jumper wires and PETG.

### Why these variants

- **Pico 2H (CE10154):** official, in stock, headers already fitted, and only $1.25 more than the Pico H. AliExpress offers no real saving and its listings are unverified clones.
- **Thermocouple:** none of the local options has an insulated junction. Two ways to get one:
  - Use the Adafruit exposed bead and insulate it yourself with a layer of Kapton.
  - Buy a 1 mm ungrounded sheathed probe from AliExpress. Its sheath is metal, but the junction is isolated from it.

  Either way, keep the bead from touching the aluminium heater body or the spreader. The MAX31855 datasheet is the reference for grounded-junction faults; I did not open it this session.
- **BME280:** PiicoDev is the only locally stocked one with 2.54 mm pads. AliExpress modules may be BMP280s (no humidity). The test that cannot pass by accident is to read the chip-ID register and compare it with the value in the Bosch datasheet.
- **INA226 vs INA219:** the INA226 at Little Bird is $3.30 against $17.30 for the Adafruit INA219.
  - With the usual 0.1 Ω shunt the INA226 reads to ±0.819 A (derived). That covers the 70–290 mA estimate in `board-power.md`, which is not measured. *(Verifier: `board-power.md` now gives ≈ 320 mA as the worst case, which is still covered. The Little Bird page does not state the shunt value, so read the marking: R100 = 0.1 Ω, R010 = 0.01 Ω.)*
  - The INA219 board (0.1 Ω, ±3.2 A per the listing) is the fallback if the board draws more than about 0.8 A.
- **MOSFET module:** CE09733 is the only local module described as working from 3.3 V logic. The AOD4184A datasheet does not specify R(DS)on below V(GS) = 4.5 V, and its V(GS)th can be as high as 2.6 V. At 3.3 V on the gate it should switch 1.2 A, but that is **unverified until measured**. The opto-isolated AliExpress modules behave differently: the opto-isolator limits the usable PWM frequency, so check how fast they can switch. *(Verifier: inference with no source cited. UNVERIFIED for any particular module.)*
- **Fan:**
  - CE10142 at $2.40 is the cheapest 5 V 40 mm fan, but it has no tach.
  - If you want the optional tach input (GP13 in the brief), Jaycar XC5054 is 12 V with 1 pulse per revolution and can run from the heater adapter. Its tach wire is driven from the 12 V side, so check that the tach level is safe for the Pico. *(Verifier: **UNVERIFIED**. The Jaycar page says only "The third wire provides a pulse output. 1 pulse per revolution." It does not say whether the output is open-collector or pulled up to 12 V. Measure the open-circuit voltage on the tach wire before it goes anywhere near a Pico pin. The "1 pulse per revolution" is confirmed from the listing.)*
  - Sunon F1110 has a named maker part number, so its datasheet can settle airflow figures.
- **Heater:** an aluminium-clad resistor has a flat face to clamp. Over the package, use a heat spreader no wider than the **20.00 mm body**; the leads extend to 22.00 mm. Do not use axial or fabric heaters.
  - *Verifier:* a 20 × 20 mm spreader has no placement margin (derived), so any offset puts metal over the leads.
  - The resistor's "25 W" assumes a heat sink. Vishay RH025 is 12.5 W in free air (doc 30201 p.3). At full duty (14.4 W), nothing but the control loop and the thermostat limits the heater temperature.
- **Plug packs:** M8936D (2.1 mm) and MB8936C (2.5 mm) are the same price.
  - `board-power.md` asks that the 5 V and 12 V inlets be impossible to swap. Using a **2.5 mm plug for 12 V** (MB8936C, with P0629 or P0623 sockets) and the board's native size for 5 V is one cheap way to do that.
  - Do this only after the board jack has been measured. If the board jack itself is 2.5 mm, reverse the choice.

### Red flags

1. **Jaycar ST3823 (70 °C NC) is rated 32 VDC at 100 mA.** It must not sit in series with a 1.2 A heater. Wiring it there is outside its rating.
   - Altronics S5612 is rated 10 A, but only at 250 VAC, and it trips at 90 °C, above the FPGA's 85 °C rating.
   - AliExpress KSD9700 listings give AC ratings only. Using one at 12 VDC and 1.2 A is far below its AC current rating, but DC is not stated, so it is **unverified**. *(Verifier: more precisely, the titles say "250V 5A" without saying AC or DC. A named-maker part (Xucheng, LCSC C51934112) states it as AC. A DC rating cannot be read off an AC one: DC has no zero-crossing to put out the arc when the contacts open. That is a general principle, not a sourced figure for this part.)*
   - Alex decides how the backstop works: either find a thermostat rated for DC, or have a low-current thermostat cut something that can carry the heater current, such as a relay coil.
2. **The thermostat can trip earlier than its rating.** ST3823's tolerance is ±5 °C at 32 VDC. A 70 °C part can therefore open at 65 °C. If it is mounted on the heater, which runs hotter than the package, it may trip during the 60 °C setpoint (derived). Placement and trip temperature need deciding together.
3. **A 10 W 10 Ω resistor at 12 V dissipates 14.4 W** (derived). That rules out Jaycar RR3352 for continuous full-duty heating. *(Verifier: confirmed. The RR3352 page gives "Continuous Power 10.0 W", axial. The same 14.4 W is also above the **12.5 W free-air rating** of a Vishay RH025-class "25 W" aluminium-clad part (doc 30201 p.3). The thermostat is what bounds a stuck-on heater, not the resistor's rating.)*
4. **AliExpress mains plug packs:** none were priced. An approved Australian supply is the only safe choice for something left plugged in unattended. Even the local Altronics and Core pages say only "Energy authority approved"; confirm the RCM tick on the label.
5. **Jaycar PS0522's spec table contradicts itself** (2.1 mm vs 2.5 mm). Do not design a panel cut-out around it. The Altronics P0628 (13 mm hole) and P0622 (8 mm hole) state their hole sizes.
6. **AliExpress prices** show the cheapest variant before shipping, and AU$1.49 is probably a new-user price. The real cart total will be higher.
7. **Fetch limits.** The resistor price at element14, RS and DigiKey was **not obtained** (HTTP 403). Every Jaycar price except ST3823's search snippet came from Jaycar's storefrontcloud host, not from jaycar.com.au itself.

### Not done

- No shipping quotes.
- No live stock check beyond what the pages said.
- No datasheet for the thermostats, the Sunon fan, the MAX31855 or the BME280. Those are the next documents to open.

## Verification (adversarial pass)

Done 2026-10-23 by a second agent. I re-derived each claim below from its primary source this session: the PDF in `resources/`, the manufacturer datasheet PDF read as text with pymupdf, or the shop page fetched again. I did not use the original author's notes. Prices are still **unverified** listing prices.

### Checked and confirmed

| # | Claim | Re-derived from | Result |
|---|---|---|---|
| 1 | Jaycar ST3823: 70 °C NC, resets 58 °C, ±5 °C at 32 VDC, contacts **32 VDC 100 mA**, 125 VAC 10 A, 250 VAC 6 A, 30.3 × 21.2 mm, $6.75 | Jaycar storefrontcloud page | Confirmed. Jaycar.com.au itself still returns 403. **ST3821 (60 °C) and ST3825 (90 °C) carry the same 32 VDC 100 mA rating**, so the whole family is out |
| 2 | Altronics S5612: 90 °C NC, 10 A 250 VAC, hole centres 23.5 mm, $5.50 | altronics.com.au product page | Confirmed. No DC rating, reset temperature or body size is given |
| 3 | FPGA "85 °C rating" | `Cyclone IV Datasheet.pdf` CYIV-53001-1.7, Table 1–3, p.4 | Confirmed: commercial T<sub>J</sub> 0–85 °C. It is a **junction** limit, not a case limit |
| 4 | INA226 shunt range ±81.92 mV (p.5); 16 addresses, 0–36 V bus, 2.7–5.5 V supply (p.1) | TI SBOS547C (revised Aug 2026), downloaded | Confirmed. Exact range −81.9175 / +81.92 mV. Addresses 0x40–0x4F (Table 6-2) |
| 5 | 0.819 A full scale with 0.1 Ω; 8.19 A with 0.01 Ω | arithmetic | Confirmed (0.08192 / 0.1, 0.08192 / 0.01) |
| 6 | Heater 1.2 A / 14.4 W at 12 V, 10 Ω | arithmetic | Confirmed |
| 7 | AOD4184A V<sub>GS(th)</sub> 1.7 / 2.1 / 2.6 V; R<sub>DS(on)</sub> < 9.5 mΩ at 4.5 V; nothing at 3.3 V | AOS AOD4184A Rev1.0 (Sept 2023), p.2, downloaded | Confirmed. 7.6 typ / 9.5 max mΩ at V<sub>GS</sub> 4.5 V, I<sub>D</sub> 15 A |
| 8 | EP4CE6 E144 D1 = E1 = 20.00 mm, D = E = 22.00 mm, A 1.45 / 1.55 / 1.65 mm | `EP4CE6 package information.pdf` (04R-00402-1.0) p.1 | Confirmed |
| 9 | Board power: USB or 5 V adapter, chosen by a push switch | `Dev Board Manual.pdf` p.1 | Confirmed ("Press … USB power supply; Lift … 5V power adapter") |
| 10 | PiicoDev BME280 CE07503: $23.50, 25.4 × 25.4 mm, 0x77 / 0x76, connector 3.3 V only | Core page | Confirmed. Also has **2 × M2.5 holes** (positions not given) |
| 11 | MOSFET module CE09733: $1.35, 2 × AOD4184, 3.3–5 V logic, 10 A / 30 V, about 34 × 17 × 14 mm, no headers | Core page | Confirmed. The page does not mention a gate resistor or pull-down |
| 12 | Plug pack M8936D: $24.75, 5.5 / 2.1 mm, centre positive, "Energy authority approved. MEPS approved.", RCM not shown | Altronics page | Confirmed. The lead is 1.8 m |
| 13 | Panel sockets: P0628 13 mm hole, 3 A 12 VDC; P0622 8 mm hole | Altronics pages | Confirmed. P0622 is rated 5 A at 24 VDC |
| 14 | Logic analyser TOL-18627: $49.30, 5.25 V max, V<sub>IH</sub> ≥ 2.0 V, V<sub>IL</sub> ≤ 0.8 V, 54.7 × 27.4 × 14.1 mm, USB-C | Core page | Confirmed |
| 15 | Heat-set inserts ADA4255 OD 4.2 mm × 4 mm; ADA4256 OD 4.5 mm × 3 mm | Core pages | Confirmed |
| 16 | Si5351 ADA2045: $14.60, 31 × 22 × 2 mm, 3–5 V, level-shifted I²C, "<8KHz up to 150+ MHz" | Core page | Confirmed |
| 17 | Thermocouple ADA270: 1 m, 500 °C, 2.18 mm, bare bead | Core page | Confirmed ("bare wires bead-probe") |
| 18 | Fan CE10142 $2.40, 40 × 40 × 10 mm, 5 V, ~200 mA, 4 mm holes; Jaycar XC5054 80 mA, 6000 RPM, 1 pulse/rev | Core page; Jaycar SFC page | Confirmed. CE10142 hole spacing is **not given** |
| 19 | Pico 2H CE10154 $9.90, RP2350, headers soldered, 48 in stock | Core page | Confirmed. Board is 21 × 51 mm |
| 20 | Other rows re-read: ADA904 INA219, CE09435, S6001, H0725, Bunnings 1064265 (6063-T5), NM2790, RR3352, ADA610 | Shop pages | Confirmed as written |
| 21 | Local-route sum 298.16 → 299.09–304.13; cheap route 104.29–181.68 | Python re-sum of the BOM columns | Confirmed |

### Corrected

1. **Dearer local total.** The original gave 339.71, which leaves out the heater and thermostat the local route is forced to buy. The correct range is **340.64–345.68**. The TL;DR now reads "about 300–346" and the cheap route "about 104–182", to match the table.
2. **KSD9700 "AC ratings only".** The AliExpress titles say "250V 5A" and do not say AC or DC. The AC reading comes from a named-maker listing (Xucheng at LCSC). The conclusion is unchanged: no DC rating was found.
3. **AM8936 "probably the same unit" as M8936D.** Weakened. The leads differ (1.2 m vs 1.8 m), so they are not the same SKU, and Core lists the brand as Core Electronics.
4. **MB8936C body size.** The page gives two conflicting sizes (75 × 42 × 40 mm and 44 W × 80 H × 40 D mm). The original quoted only the first.
5. **Heater power rating.** Added: an aluminium-clad "25 W" rating assumes a heat sink. Vishay RH025 is 12.5 W in free air (doc 30201 rev. 02-Sep-2026, p.3), so 14.4 W at full duty is over that too.
6. **Little Bird INA226.** The page does not say whether GST is included, and gives no shunt value or board size. Its "12 programmable addresses" contradicts TI's 16.

### Marked UNVERIFIED

- XC5054 tach wire "driven from the 12 V side": the listing does not say open-collector or pulled up. Measure it.
- CE10142 "2-wire" and "no tach": inferred from what the page leaves out.
- "The opto-isolator limits the usable PWM frequency" for AliExpress MOSFET modules: inference with no source.
- Arcol HS25 body size: RS listings disagree (51 × 28 × 14.6 mm vs 27.3 × 28 × 14.8 mm). Arcol's datasheet returned HTTP 522.

### Still not checked by me

- Every AliExpress price except the KSD9700 search page. Element14, RS and DigiKey are still unreachable (403), and jaycar.com.au itself is 403.
- The Jaycar ST3823 search-snippet price of $6.50.
- The AM8936 GTIN (it was not shown when I re-fetched the page).
- Stock counts other than those quoted above.

### Leads for Alex (not prices, not verified)

- A Multicomp Pro **MP-12 70 °C NC** thermal switch (element14's house brand) shows up in a Novapart listing rated "15 A, 125 V". I did not check whether that is AC or DC. It may be a local 70 °C NC option through element14 AU. Look up its DC rating before relying on it.
- No address clash found so far on the I²C bus: BME280 0x76 / 0x77 (Core listing) and INA226 0x40–0x4F (TI). For the Si5351, a forum post (not a datasheet) says 0x60; **unverified**. Read it from the Si5351 datasheet before finalising `wiring.md`.
