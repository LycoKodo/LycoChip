# Breakout modules: mechanical and electrical facts

Researched 2026-10-23 for the Agent Lab Box (`docs/lab-box/BRIEF.md` §2, §3, §5, §7). Scope: Pico / Pico 2, MAX31855, BME280, INA226 / INA219, Si5351A, MOSFET drivers, USB logic analyser, I2C address map.

**TL;DR**
1. **Pico and Pico 2 share one footprint:** 51 × 21 × 1.0 mm PCB, 4 × Ø2.1 mm holes on a 47.0 × 11.4 mm rectangle, 2.0 mm from the short edges and 4.8 mm from the long edges. Holes take **M2**, not M3. Micro-USB on a short edge overhangs it by 1.3 mm. The tallest part (USB) is 2.73 mm above the PCB, from the official STEP. The brief's pin map checks out: GP4/5 = I2C0 SDA/SCL, GP16/17/18 = SPI0 RX/CSn/SCK, GP13 = PWM6 B, GP14 = PWM7 A, GP15 = PWM7 B. **GP14 and GP15 share slice 7, so they share one frequency.**
2. **Adafruit boards have exact drawings, taken from Adafruit's own Eagle files** *(verifier: every one of those files is older than the revision Adafruit ships today, so the drawings are exact for the old revision and need a caliper check)*. #269 MAX31855: 20.32 × 22.86 mm, 2 × Ø2.0 mm holes (diameter UNVERIFIED: the fab print suggests ≈ 2.2–2.3). #2652 BME280 (STEMMA QT): 25.4 × 17.78 mm, 2 × Ø2.5 mm plus 2 × Ø2.54 mm holes. #904 INA219 (STEMMA QT): 25.4 × 20.32 mm, 4 × Ø2.5 mm holes. #2045 Si5351A: 30.48 × 21.59 mm, 2 × Ø2.5 mm holes. Adafruit's STEP models give 1.57 mm PCBs for the BME280 and INA219; the other two boards' thickness is unverified. **The generic clones (CJMCU-226, GY-BME280, red/purple MAX31855) have no trustworthy drawings, so measure them.**
3. **I2C map, no collisions:** INA226 0x40, Si5351A 0x60 (fixed), BME280 0x77 (Adafruit default) or 0x76 (GY-BME280 default). If an INA219 is added next to an INA226, both default to 0x40, so move one.
4. **Do not use the IRF520 module.** Its V<sub>GS(th)</sub> can be as high as 4.0 V, and R<sub>DS(on)</sub> is only specified at V<sub>GS</sub> = 10 V, so a 3.3 V gate may not turn it on at all. For the heater, the opto-isolated **D4184 module** puts about 6 V on the gate when run from 12 V. It only suits slow PWM, and it cannot switch a 5 V load. For the fan, an **AO3400A** is the only candidate with R<sub>DS(on)</sub> guaranteed at V<sub>GS</sub> = 2.5 V (≤ 48 mΩ).
5. **The RP2040 is not 5 V tolerant** (V<sub>PIN</sub> ≤ IOVDD + 0.5 V). Adafruit I2C boards pull SDA/SCL up to their VIN pin, so **power every I2C/SPI module from the Pico's 3V3(OUT) (pin 36), not from 5 V.**

---

## Conventions

- **Module coordinates:** top (component-side) view, origin at the PCB's **bottom-left corner**, with the **main header edge at the bottom**. X points right and Y points up, in mm. "Header row y = 2.54" means pin centres sit 2.54 mm above the header edge.
- **Confidence tags:**
  - **datasheet**: the manufacturer's own document. That includes Raspberry Pi's datasheets and STEP files, and Adafruit's own Eagle `.brd` files, fab prints and STEP models. Adafruit is the manufacturer of its boards.
  - **listing**: a shop page, including Adafruit's own product-page "Product Dimensions", which are rounded.
  - **photo-estimate**: read off a graph or drawing.
  - **derived**: calculated; the calculation is shown.
- I read Eagle coordinates with a Python parser and STEP bounding boxes with CadQuery 2.8. Both ran this session, and the scripts sit in the session scratchpad. Nothing was measured on Alex's hardware.

## Sources

| Tag | Document |
|---|---|
| S1 | Raspberry Pi Pico datasheet, Release 21 (build 03/07/2026). https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf |
| S2 | Raspberry Pi Pico 2 datasheet, Release 5 (build 03/07/2026). https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf |
| S3 | Pico R3 pinout sheet. https://datasheets.raspberrypi.com/pico/Pico-R3-A4-Pinout.pdf |
| S4 | Pico R3 official STEP. https://datasheets.raspberrypi.com/pico/Pico-R3-step.zip (bounding boxes measured with CadQuery). A Pico 2 STEP at the analogous URL returned 404. |
| S5 | RP2040 datasheet (build 2025-02-20). https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf |
| S6 | RP2350 datasheet, Release 8 (build 01/10/2026). https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf |
| S7 | Adafruit MAX31855 Eagle, `Adafruit_MAX31855 v2.brd` (repo last changed 2019). https://github.com/adafruit/Adafruit-MAX31855-breakout-board |
| S8 | Adafruit MAX31855 fab print (inches). https://cdn-learn.adafruit.com/assets/assets/000/035/636/original/temperature_fabprint.png |
| S9 | Adafruit #269 product page. https://www.adafruit.com/product/269 |
| S10 | Maxim MAX31855 datasheet 19-5793 Rev 2 (2/12), Adafruit mirror. https://cdn-shop.adafruit.com/datasheets/MAX31855.pdf |
| S11 | Adafruit BMP280/BME280 STEMMA QT Eagle, `Adafruit BMP280 STEMMA QT.brd`. Adafruit's BME280 guide links this repo as the QT version's files. https://github.com/adafruit/Adafruit-BMP280-Breakout-PCB |
| S12 | Adafruit BME280 STEMMA QT fab print. https://cdn-learn.adafruit.com/assets/assets/000/097/134/original/adafruit_products_BME280_fab_print.png |
| S13 | Adafruit CAD parts STEP: `2652 BMP280 STEMMA QT.step` and `904 INA219 Stemma.step`. https://github.com/adafruit/Adafruit_CAD_Parts |
| S14 | Adafruit #2652 product page. https://www.adafruit.com/product/2652 |
| S15 | Adafruit original (pre-QT) BME280 Eagle. https://github.com/adafruit/Adafruit-BME280-Breakout-PCB |
| S16 | Bosch BME280 datasheet BST-BME280-DS001-23 Rev 1.23, Adafruit mirror. https://cdn-learn.adafruit.com/assets/assets/000/115/588/original/bst-bme280-ds002.pdf |
| S17 | ProtoSupplies GY-BME280. https://protosupplies.com/product/gy-bme280-pressure-humidity-temperature-sensor-module/ |
| S18 | TI INA226 SBOS547C. https://www.ti.com/lit/ds/symlink/ina226.pdf |
| S19 | TI INA219 SBOS448G. https://www.ti.com/lit/ds/symlink/ina219.pdf |
| S20 | Adafruit INA219 Eagle (old board and STEMMA QT board). https://github.com/adafruit/Adafruit-INA219-Current-Sensor-PCB |
| S21 | Adafruit #904 product page. https://www.adafruit.com/product/904 |
| S22 | openelab CJMCU-226 listing. https://openelab.io/products/ina226-voltage-and-current-module-cjmcu-226-monitor |
| S23 | how2electronics INA226 module guide. https://how2electronics.com/how-to-use-ina226-dc-current-sensor-with-arduino/ |
| S24 | Adafruit Si5351A Eagle: #2045 https://github.com/adafruit/Adafruit-Si5351A-Clock-Generator-Breakout-PCB and #5640 https://github.com/adafruit/Adafruit-Si5351A-Clock-Generator-with-STEMMA-QT-PCB |
| S25 | Adafruit #2045 product page. https://www.adafruit.com/product/2045 |
| S26 | Skyworks Si5351 datasheet Rev 1.3 (Aug 2021). https://www.skyworksinc.com/-/media/Skyworks/SL/documents/public/data-sheets/Si5351-B.pdf |
| S27 | Vishay IRF520, doc 91017 Rev C (2021). https://www.vishay.com/docs/91017/irf520.pdf |
| S28 | AOS AOD4184A Rev 1.0 (Sep 2023). https://www.aosmd.com/res/datasheets/AOD4184A.pdf |
| S29 | AOS AO3400A Rev 3.1 (Jul 2023). https://www.aosmd.com/res/datasheets/AO3400A.pdf |
| S30 | IR/Infineon IRLZ44NPbF. https://www.infineon.com/dgdl/irlz44npbf.pdf?fileId=5546d462533600a40153567217c32725 |
| S31 | ProtoSupplies IRF520 module. https://protosupplies.com/product/irf520-n-ch-mosfet-module/ |
| S32 | ProtoSupplies D4184 opto MOSFET module. https://protosupplies.com/product/d4184-mosfet-control-module/ |
| S33 | ProtoSupplies dual-AOD4184 module MOD-117. https://protosupplies.com/product/high-power-dual-mosfet-switch-module/ |
| S34 | ShillehTek 24 MHz 8-ch logic analyser manual. https://shillehtek.com/blogs/shillehtek-product-manuals/24mhz-8-channel-usb-logic-analyzer-digital-debugger-for-arduino-manual |
| S35 | sigrok wiki, MCU123 Saleae Logic clone. https://sigrok.org/wiki/MCU123_Saleae_Logic_clone |

## Facts table

| Item | Value | Unit | Source | Confidence | Notes |
|---|---|---|---|---|---|
| **Pico / Pico 2** PCB outline | 51 × 21 | mm | S1 §2 p.6 Fig 3; S2 §3 p.7 Fig 3 | datasheet | Identical drawings |
| Pico PCB thickness | 1.0 | mm | S1 §2; S4 (STEP: 1.00) | datasheet | |
| Pico mounting holes | 4 × Ø2.1 ± 0.05 | mm | S1 §2 | datasheet | Takes **M2**; M3 does not fit |
| Pico hole spacing across the width | 11.4 (4.8 from each long edge) | mm | S1 Fig 3 | datasheet | 4.8 + 11.4 + 4.8 = 21 |
| Pico hole centre from the short edges | 2.0 | mm | S1 Fig 3; S4 | datasheet | Dimensioned at the USB end. The far end scales to 2.0 on the drawing. *(Verifier: in the official STEP the four Ø2.10 holes sit at 4.8 / 16.2 mm across and 2.0 / 49.0 mm along, so both ends are 2.0.)* |
| Pico hole spacing along the length | 47.0 | mm | 51 − 2 × 2.0; S4 STEP (49.0 − 2.0) | derived; datasheet (STEP) | Verifier confirmed it in the official STEP |
| Pico header rows | 2 × 20, 2.54 pitch, rows 17.78 apart, 1.61 from the long edges | mm | S1 Fig 3 | datasheet | Ø1.0 holes plus edge castellations |
| Pico first/last pin from the short edge | 1.37 | mm | (51 − 48.26)/2; S4 | derived; datasheet (STEP) | Assumes the 48.26 span is centred. *(Verifier: the STEP puts pin 1's castellation 1.37 mm from the USB edge and the pin rows 1.61 mm from the long edges, so it is centred.)* |
| Pico pin 1 | GP0, at the USB end; pins 1–20 on one side, 21–40 back along the other | – | S3; S2 p.3 Fig 1 | datasheet | Pico 2 silkscreen is the same |
| Pico SWD pads | 3 (SWCLK, GND, SWDIO) at the non-USB short edge, 1.6 mm from that edge | mm | S1 Fig 3; S3 | datasheet | |
| Pico USB | Micro-USB B on the short edge, overhanging 1.3 (typ) | mm | S1 §2, Fig 3 | datasheet | |
| Pico USB connector width | 8 (drawing); body 7.58 in STEP | mm | S1 Fig 3; S4 | datasheet | |
| Pico tallest part | USB shell, 2.73 above the PCB top (3.73 overall, no headers) | mm | S4 STEP bbox (top 3.23, PCB top 0.50) | datasheet | BOOTSEL button 2.50 above PCB. Pico 2: assumed the same, **unverified** (no STEP found) |
| Pico supply | VBUS 5 V ± 10 %; VSYS 1.8–5.5 V | V | S1 §2.3 p.10–11 | datasheet | |
| Pico 3V3(OUT) budget | < 300 recommended | mA | S1 §2.1 p.8 | datasheet | Pin 36. Enough for all the sensor modules |
| Pico temperature | −20 to +85 operating; 70 recommended max ambient | °C | S1 §2.3; S2 p.12 | datasheet | Keep it on the cool plate |
| GP4 / GP5 | I2C0 SDA / SCL; physical pins 6 / 7 | – | S5 §1.4.3 Table 2; S6 §1.2.3 Table 3; S3 | datasheet | Pinout sheet marks I2C0 on GP4/5 as default |
| GP16 / GP17 / GP18 | SPI0 RX (MISO) / CSn / SCK; pins 21 / 22 / 24 | – | S5 Table 2; S6 Table 3; S3 | datasheet | Pin 23 = GND. GP19 (SPI0 TX, pin 25) not needed by MAX31855 |
| GP13 | PWM6 B; pin 17 | – | S5 Table 2 + §4.5.2; S6 Table 3 | datasheet | A B channel, so it can be the counter input (tach). That consumes all of slice 6 |
| GP14 | PWM7 A; pin 19 | – | same | datasheet | |
| GP15 | PWM7 B; pin 20 | – | same | datasheet | **Same slice as GP14** |
| PWM slice structure | One 16-bit counter, one 8.4 fractional divider and one wrap value, shared by A and B | – | S5 §4.5.1 p.521 | datasheet | So A and B always run at the **same frequency**; only the duty differs |
| Lowest hardware PWM frequency | ≈ 7.45 @ 125 MHz; ≈ 8.94 @ 150 MHz | Hz | f_sys / (256 × 65536) | derived | 125 MHz (RP2040) and 150 MHz (RP2350) are the datasheets' typical clk_sys; check the SDK setting. *(Corrected formula: the largest divisor is 256, set by writing DIV_INT = 0 (S5 §4.5.2.5), not 255.9375. The answer rounds to the same value. S5 §4.5.2.4 says "approximately 7.5Hz from a 125MHz system clock". Phase-correct mode halves it, to ≈ 3.7 Hz.)* |
| RP2040 pin voltage max | IOVDD + 0.5 (= 3.8 at 3.3 V) | V | S5 §5.5.3.1 (PDF p.615) | datasheet | **Not 5 V tolerant** |
| RP2350 pin voltage max | 5.5 with IOVDD = 3.3 V (FT pads) | V | S6 §14.8.2.1, §14.9.1 (PDF p.1336) | datasheet | Pico 2 only. Design to the RP2040 limit anyway. *(Verifier: the ADC-capable pins, GP26–28 on the Pico 2 header, are of type "Digital IO / Analogue" and are **not** FT, so they are IOVDD + 0.5 V only. Source: S6 §14.8.2.1, Table 1673.)* |
| RP2350 erratum E9 | Leaky input pads; internal pull-down cannot hold a floating input low | – | S6 Appendix C, erratum RP2350-E9 (printed p.1358–1359) | datasheet | "Affects RP2350 A2". Use external pull resistors ≤ 8.2 kΩ, or pull-ups |
| **MAX31855 Adafruit #269** PCB | 20.32 × 22.86 (0.8 × 0.9 in) | mm | S7; S8 | datasheet | Eagle v2 file (2019). The 6 Jun 2024 revision added a pre-soldered terminal block and new silkscreen (S9); whether the outline moved is not stated |
| #269 holes | 2 × Ø2.0 plated at (2.54, 20.32), (17.78, 20.32); 15.24 apart | mm | S7; S8 | datasheet (positions); **diameter UNVERIFIED** | Both on the terminal-block edge, 2.54 from its top. Takes M2. *(Verifier: the hole positions match in S7 and S8. The Ø2.0 comes only from the S7 drill, though. S8's callout at the hole reads 0.09 in (≈ 2.3 mm), and Adafruit's older BME280 board uses the same "2.0" footprint with a 2.2 mm drill. A 2.0 mm hole gives an M2 screw no clearance. Gauge the hole.)* |
| #269 header | 6 pins, 2.54 pitch, row y = 2.03, x = 3.81…16.51 | mm | S7 | datasheet | Left to right: **Vin, 3Vo, GND, DO, CS, CLK**. *(y corrected from 2.02: the Eagle value is 2.032.)* |
| #269 thermocouple terminal | 2-pos 3.5 mm screw terminal, pads at (8.46, 19.05) "Red −" and (11.96, 19.05) "Yellow +" | mm | S7 (pads + silkscreen + nets) | datasheet | + is on the right. Verifier traced J1.1 (x = 11.96) through FB2 to MAX31855 pin 3 (T+). The silkscreen uses ANSI colours (K: yellow +, red −). An IEC 60584 probe is green + and white − (https://www.tcdirect.co.uk/thermocouple-sensors/thermocouple-colour-codes.aspx, listing), so check which code the probe Alex buys uses |
| #269 tallest part | Terminal block, height **unknown** | mm | – | unknown | MEASURE |
| #269 chip | MAX31855**K** (K-type only) | – | S9; S10 ordering info p.12 | datasheet | The suffix letter is the thermocouple type |
| #269 supply / logic | Vin 3.3–5 V (on-board 3.3 V LDO); I/O 3.3–5 V compatible; DO driven at 3.3 V | V | S9 ("3.3 to 5v power supply and logic level compliant"); S7 nets | listing (range); datasheet (DO) | Feed it 3.3 V from the Pico anyway. *(Downgraded: the supply range comes from the product page, which this report's own convention tags as listing. In the S7 nets, DO runs straight from MAX31855 pin 7 to the header, and CS and CLK go through 1N4148 diodes with 10 kΩ pull-ups to 3.3 V.)* |
| MAX31855 chip supply | 3.0–3.6 | V | S10 p.2 | datasheet | Bare chip, which is what a regulator-less clone exposes |
| MAX31855 SPI | Read-only, 32-bit frame; SCK ≤ 5 MHz; mode 0 | – | S10 p.4, p.9 | datasheet / derived | Mode 0 derived: D31 is valid after CS falls, and later bits change on SCK falling edges |
| MAX31855 conversion | 70 typ / 100 max per conversion; 200 at power-up | ms | S10 p.4 | datasheet | Useful read rate ≤ 10 Hz |
| MAX31855 faults | Detects thermocouple open, short to GND (SCG), short to VCC (SCV) | – | S10 p.9–10 | datasheet | See the heater-clamp warning below |
| **Generic MAX31855 (red/purple)** | Dimensions, holes, regulator: **unknown** | – | No usable source | unknown | Pins usually GND, VCC, SCK, CS, SO. MEASURE |
| **BME280 Adafruit #2652 (STEMMA QT, since 11 Nov 2020)** PCB | 25.4 × 17.78 (1.00 × 0.70 in) | mm | S11; S12 | datasheet | Listing says 25.2 × 18.0 × 4.6 (S14). *(Verifier: the S11 files date from Jul 2020. S14 reports a further revision on 18 Sep 2023, a new "Pinguin" silkscreen, that has no published files, so the current board's outline is UNVERIFIED.)* |
| #2652 QT holes | Plated Ø2.5 at (2.54, 15.24), (22.86, 15.24); non-plated Ø2.54 at (2.54, 2.54), (22.86, 2.54) | mm | S11; S12 | datasheet | Bottom holes sit 2.54 from the header end pins, so a screw head may clash with the header |
| #2652 QT header | 7 pins, row y = 2.54, x = 5.08…20.32 | mm | S11; S12 | datasheet | **VIN, 3Vo, GND, SCK(SCL), SDO, SDI(SDA), CS** |
| #2652 QT STEMMA QT | JST-SH 4-pin on both 17.78 mm edges, centred y ≈ 8.9 | mm | S11 | datasheet | |
| #2652 QT tallest part / PCB | STEMMA QT, 2.96 above PCB (4.53 overall, no header); PCB 1.57 | mm | S13 STEP | datasheet | The STEP is named BMP280 QT; same PCB |
| #2652 I2C address | 0x77 default (SDO 10 kΩ pull-up to 3.3 V); SDO to GND gives 0x76 | – | S11 nets; S16 §6.2 p.32 | datasheet | |
| #2652 supply | VIN 3–5 V (LDO + BSS138 shifters); host-side SDA/SCL pulled up 10 kΩ **to VIN** | – | S11 nets; S14 | datasheet | If VIN = 5 V, the Pico's pins see 5 V pull-ups |
| BME280 original #2652 (pre-QT) | 17.78 × 19.05; Ø2.2 holes at (2.54, 16.51), (15.24, 16.51); 7-pin row y = 2.54, x = 1.27…16.51 | mm | S15 | datasheet | Only if Alex has an old one |
| BME280 chip supply | VDD 1.71–3.6; VDDIO 1.2–3.6 | V | S16 p.1 | datasheet | |
| BME280 operating range | −40 to +85 | °C | S16 p.1 | datasheet | |
| **GY-BME280 generic, 6-pin** | 15.5 × 11.5 PCB; pins VCC, GND, SCL, SDA, CSB, SDO; **3.3 V only**; default 0x76 | mm | S17 | listing | 10 kΩ pull-ups. Holes not stated. MEASURE |
| GY-BME280 generic, 4-pin "5 V" | Regulated + level-shifted, per sellers; dimensions **unknown** | – | S17 (mention only) | listing / unknown | Sellers contradict each other on which variant has the regulator. *(Verifier: S17 never describes a 4-pin board. It mentions a separate "BME280 I2C module" with "a built in regulator and logic level shifters" and gives no pin count, so the 4-pin attribution is UNVERIFIED.)* |
| **INA226** chip | Bus 0–36 V; supply 2.7–5.5 V; shunt full scale ±81.92 mV | V / mV | S18 p.1; §5.5 p.5 | datasheet | |
| INA226 addresses | 16: 0x40–0x4F via A0/A1 to GND/VS/SDA/SCL; 0x40 with both at GND | – | S18 Table 6-2 p.18 | datasheet | Sampled on every transaction; do not leave the pins floating |
| INA226 with 0.1 Ω (R100) shunt | Full scale 0.819 A | A | 81.92 mV / 0.1 Ω | derived | Board estimate ≤ 0.32 A (`board-power.md`), so R100 is fine |
| **CJMCU-226 generic** PCB | 20 × 27, "fixed 3 mm holes" | mm | S22 | listing | Single source. MEASURE |
| CJMCU-226 pins | VCC, GND, SDA, SCL, ALE(RT), VBUS, IN−, IN+ | – | S23 | listing | Physical order not confirmed; read the silkscreen. *(Verifier: S22 lists a different set, "VCC, GND, SDA, SCL, ALERT, A0, A1", so at least two pin-outs are sold under this name.)* |
| CJMCU-226 shunt | Usually R100 (0.1 Ω) — **UNVERIFIED** | Ω | ~~S22 (product titles "INA226 R100")~~ S23 code comment ("default is 100 mOhm") | listing | Read the marking: R100 = 0.1 Ω, R010 = 0.01 Ω. *(Source corrected: the S22 page as fetched gives no shunt value. S23 says only that its sketch assumes 100 mΩ.)* |
| **INA219 Adafruit #904 (STEMMA QT, since 29 Jan 2021)** PCB | 25.4 × 20.32 | mm | S20 `Adafruit INA219 STEMMA QT.brd` | datasheet | Listing says 25.6 × 20.4 × 4.7 (S21). *(Verifier: the S20 QT files were committed Aug 2021. S21 reports two later changes: on 22 Sep 2022, "either the INA219A or INA219B and in SOT-23 or SOIC package"; on 31 May 2024, a pre-soldered terminal block. The current board's outline and holes are UNVERIFIED.)* |
| #904 QT holes | 4 × Ø2.5 plated, centres 2.54 mm in from each edge (20.32 × 15.24 rectangle) | mm | S20 | datasheet | M2.5 |
| #904 QT header | 6 pins, row y = 2.54, x = 6.35…19.05 | mm | S20 | datasheet | **VIN(VCC), GND, SCL, SDA, VIN−, VIN+** |
| #904 QT power terminal | 2-pos 3.5 mm, pads (10.9, 16.51) = Vin−, (14.4, 16.51) = Vin+ | mm | S20 (pads; polarity from silkscreen position) | datasheet / derived | Pre-soldered since 31 May 2024 (S21). Height unknown, MEASURE |
| #904 QT tallest part (excl. terminal) / PCB | STEMMA QT 2.96 above PCB; PCB 1.57 | mm | S13 STEP | datasheet | The STEP has no terminal block or header |
| #904 old (pre-2021) | 25.4 × 22.24; 4 × Ø2.5 at (2.54, 2.54), (22.86, 2.54), (2.54, 19.70), (22.86, 19.70) | mm | S20 `Adafruit_INA219_CurPowerMonitor.brd` | datasheet | |
| INA219 chip | Bus 0–26 V; shunt ±320 mV; supply 3–5.5 V; 0.1 Ω shunt gives ±3.2 A | – | S19 p.1, p.5 (Electrical Characteristics); S21 | datasheet | |
| #904 addresses | 0x40 / 0x41 / 0x44 / 0x45 via A0/A1 jumpers; SDA/SCL pulled up 10 kΩ to VCC | – | S21; S20 nets | datasheet | **Same default (0x40) as the INA226** |
| **Si5351A Adafruit #2045** PCB | 30.48 × 21.59 | mm | S24 `Adafruit Si5351A.brd` | datasheet | Listing says 31 × 22 × 2 (S25). *(Verifier: the S24 file dates from 2016–2019. S25 reports a "Pinguin" silkscreen revision on 22 Dec 2023 that has no published files, so the current board is UNVERIFIED.)* |
| #2045 holes | 2 × Ø2.5 plated at (2.54, 2.54), (27.94, 2.54); 25.4 apart | mm | S24 | datasheet | Both on the header edge; the SMA edge has none |
| #2045 header | 7 pins, row y = 2.54, x = 7.62…22.86 | mm | S24 | datasheet | Left to right: **CLK0, CLK1, CLK2, SCL, SDA, GND, VIN** |
| #2045 RF connectors | 3 × edge-launch SMA footprints on the top edge at x = 5.08 (CLK0), 15.24 (CLK1), 25.40 (CLK2); **no u.FL footprint** | mm | S24 nets | datasheet | SMAs are optional and not included (S25) |
| #2045 I2C | 0x60 (MSOP-10 has no A0 pin); 10 kΩ host-side pull-ups **to VIN** | – | S26 p.18 (I2C address, Fig 6); S24 nets | datasheet | |
| #2045 output | 3.3 V CMOS: V<sub>OH</sub> ≥ VDD − 0.6, V<sub>OL</sub> ≤ 0.6 (C<sub>L</sub> = 5 pF); about 3 Vpp | V | S26 Table 7 p.10; S25 | datasheet | VDDO tied to the 3.3 V LDO (S24 nets) |
| #2045 frequency | Chip 2.5 kHz–200 MHz; Adafruit quotes 8 kHz–160 MHz | Hz | S26 p.1; S25 | datasheet / listing | |
| Si5351A Adafruit #5640 (STEMMA QT) | 25.4 × 17.78; 4 × Ø2.5 at 2.54 from the edges; 1 SMA (CLK1) on the top edge, centred | mm | S24 QT `.brd` | datasheet | Second 5-pin row, pad 1 first: CLK0, GND, CLK1, GND, CLK2 |
| **IRF520** threshold | V<sub>GS(th)</sub> 2.0–4.0 (at 250 µA) | V | S27 p.2 | datasheet | **Not logic level** |
| IRF520 on-resistance | ≤ 0.27 at V<sub>GS</sub> = 10 V, I<sub>D</sub> = 5.5 A; not specified at any lower V<sub>GS</sub> | Ω | S27 p.2 | datasheet | |
| IRF520 module | Dimensions **UNVERIFIED** (the original "about 33–34 × 24–30, height 12–18" came from search snippets); SIG/VCC/GND header (VCC n/c); 2 screw terminals | mm | S31 (pins, terminals, advice only) | listing / unknown | Seller: "I don't recommend using this module with 3.3V logic"; limit to "about 1A" if used. *(Verifier: S31 gives no dimensions and search snippets cannot be checked. The module is rejected anyway.)* |
| **AOD4184A** | V<sub>DS</sub> 40 V; V<sub>GS(th)</sub> 1.7 / 2.1 / 2.6; R<sub>DS(on)</sub> ≤ 7 mΩ @ 10 V, ≤ 9.5 mΩ @ 4.5 V | V / mΩ | S28 p.1–2 | datasheet | Not specified at 3.3 V |
| AOD4184A at 3.0–3.3 V gate | Typical I<sub>D</sub> ≈ **2.6 A @ 3.0 V** *(corrected from "4–5 A")*, ≈ 17.5 A @ 3.3 V (V<sub>DS</sub> = 5 V, 25 °C); at 125 °C ≈ 7.4 A @ 3.0 V, ≈ 25 A @ 3.3 V | A | S28 Fig 2 p.3 | photo-estimate | Typical curve, not a guarantee. The verifier read these off the PDF's vector curve data, which is more precise than eyeballing. The old 4–5 A figure is roughly the 125 °C curve. **Worst case:** V<sub>GS(th)</sub> max is 2.6 V against 2.1 V typical. A max-threshold part could act like the typical curve shifted about +0.5 V, which is ≈ 0.5 A at a 3.3 V gate (derived, rough) |
| **D4184 opto module** (single) | 35 × 16 × 14; 2 × Ø2 holes 12 apart at the signal end | mm | S32 | listing | Recommended for the heater, with conditions |
| D4184 opto module connections | Signal end: 2-pin PWM/GND (4 mm screw terminal or 0.1 in header). Other end: 3-pin screw terminal "+ / LOAD / −" | – | S32 | listing | Signal GND is isolated from load GND |
| D4184 opto module drive | PC817 + 1 kΩ input, 2.5–20 V; gate = ½ load supply (4.7 k / 4.7 k), 4.7 k pull-down; load 6–36 V | – | S32 (reverse-engineered by seller) | listing | ≈ 6 V gate at 12 V. **≈ 2.5 V gate at 5 V, which will not switch** |
| D4184 opto LED current at 3.3 V | ≈ 2.1 | mA | (3.3 − 1.2 V)/1 kΩ | derived | 1.2 V is a typical PC817 V<sub>F</sub>, assumed; within the Pico's 4 mA default drive. *(Verifier: no PC817 datasheet was checked. Whether about 2 mA of LED current drives the opto hard enough to bring the gate to ≈ ½ V<sub>load</sub> is **UNVERIFIED**. Measure the gate voltage at 100 % duty with a DMM.)* |
| Dual-AOD4184 direct module (MOD-117) | 34 × 17 × 12; 3.3–20 V input; output 5–36 V; signal GND = VIN− | mm | S33 | listing | Works from 3.3 V "but derate"; holes not stated |
| **AO3400A** | V<sub>DS</sub> 30 V; V<sub>GS</sub> ±12 V; V<sub>GS(th)</sub> 0.65 / 1.05 / 1.45 V; R<sub>DS(on)</sub> ≤ 26.5 / 32 / **48 mΩ @ 10 / 4.5 / 2.5 V**; I<sub>D</sub> 5.7 A; R<sub>θJA</sub> 125 °C/W max steady | – | S29 p.1–2 | datasheet | Only part here with R<sub>DS(on)</sub> guaranteed below 3.3 V. SOT-23, so it needs an adapter on perfboard |
| AO3400A at 1.5 A | ≤ 0.108 W, ΔT ≤ 13.5 °C | W / °C | 1.5² × 0.048; × 125 | derived | R<sub>θJA</sub> is for 1 in² of 2 oz copper; perfboard will run hotter |
| **IRLZ44N** | V<sub>GS(th)</sub> 1.0–2.0 V; R<sub>DS(on)</sub> ≤ 22 / 25 / 35 mΩ @ 10 / 5 / 4 V | – | S30 p.2 | datasheet | Not specified at 3.3 V. TO-220, so easy on perfboard |
| **USB logic analyser** (CY7C68013A clone) | 56 × 27.6 × 20.3 case | mm | S34 | listing | One seller only. MEASURE |
| Logic analyser connector | USB Mini-B (S34). "Some newer units USB-C" is **UNVERIFIED** (source was a search snippet). Probe header CH0–CH7 + GND (some add CLK) | – | S34 | listing | Pin count and arrangement: MEASURE |
| Logic analyser inputs | −0.5 to 5.25 V; V<sub>IH</sub> 2.0, V<sub>IL</sub> 0.8; 74HC245 buffer; 24 MHz max in sigrok (fx2lafw) | V | S35; S34 | listing | 3.3 V FPGA I/O is compatible. *(Verifier: S35 gives "-0.5V — 5.25V" and describes one specific clone with a CY7C68013 and an NXP HC245. Other clones may differ. S34 quotes "24 MS/s (single channel) / 12 MS/s (8 channels)", which differs from sigrok's 24 MHz.)* |

## Discussion

### Pico / Pico 2
- **Mechanical:** the two boards are interchangeable. S2 reproduces S1's Figure 3, dimension for dimension.
- **Bosses:** M2 bosses at 2.0 mm from the short edges and 4.8 mm from the long edges.
- **USB cut-out:** leave room for the 1.3 mm overhang and the cable overmould, which Alex must measure on his own cable.
- **Headers:** if they are soldered on (or it is a Pico H), the module plate needs clearance holes or a socket under the 2 × 20 rows. The header height has not been measured.
- **Pin map:** the brief's map (§4) is consistent with the official function tables. The PWM conflict below is the only issue.

**The GP14/GP15 problem.** Both pins sit on slice 7, which has one counter, one divider and one wrap value. A 25 kHz fan PWM therefore forces the heater PWM to 25 kHz too. That frequency is too fast for the opto D4184 module (next section). Options, for Alex to choose:
- (a) Move the heater to a pin on an unused slice, for example GP22 = PWM3 A (pin 29) or GP10 = PWM5 A (pin 14). Neither is used by the brief's map.
- (b) Drive the heater as a firmware time-proportioned GPIO with a period of about 1 s. Heater thermal time constants are seconds, so this is enough.
- (c) Keep both on slice 7 and use a direct-drive MOSFET for the heater, which tolerates 25 kHz.

**Fan tach on GP13** (PWM6 B):
- The PWM block can count tach edges on GP13, but only by putting slice 6 into edge-counting mode. Slice 6 then cannot also generate PWM on GP12 or GP28.
- A GPIO interrupt or a PIO counter avoids that.
- Pull the tach up to **3.3 V**, never 5 V or 12 V (RP2040 V<sub>PIN</sub> limit).

### MAX31855
**Use the Adafruit #269 board, because it has an exact drawing.**
- The two holes are both at the terminal-block end. The 6-pin header end has no holes, so support the header end with a printed rest.
- It has a 3.3 V regulator and diode level shifting, and DO comes straight from the 3.3 V chip, so it is safe for the Pico.
- Generic red/purple boards: I found no dimensional source. Many are bare-chip boards with a 3.0–3.6 V supply (S10). MEASURE before modelling. *(Verifier: S10 supports only the chip's 3.0–3.6 V range. That clones are mostly regulator-less boards is **UNVERIFIED**, so check for an LDO before connecting anything but 3.3 V.)*

**Heater-clamp consequence.** The MAX31855 flags a thermocouple shorted to GND or VCC (S10). A bare-bead thermocouple pressed against a metal clamp, or an aluminium heater body that touches ground, will read as a fault or as noise.
- Insulate the junction from the metal, for example with Kapton tape.
- Or use an insulated-junction probe.

**Cold junction:** keep the board on the cool plate. Its cold-junction reference is the chip die (S10).

### BME280
- **Current Adafruit #2652 (STEMMA QT):** 25.4 × 17.78 mm with 4 holes. Only the two at the top are plated; the two non-plated holes sit next to the header ends. Its I2C pull-ups go to VIN, so **power it at 3.3 V.**
- **GY-BME280 6-pin:** about 15.5 × 11.5 mm. It is **3.3 V only**: the Bosch operating supply range is 1.71–3.6 V, and the absolute maximum is 4.25 V (S16 §2, Table 5), so 5 V exceeds it. *(Wording corrected: 1.71–3.6 V is the operating range, not the absolute range.)* Default address is 0x76.
- **GY-BME280 4-pin:** sellers disagree about which variant has the regulator, so check the board for an LDO before connecting 5 V.

**Fake parts:** a "BME280" that is really a BMP280 has no humidity reading. The id register (0xD0) reads 0x60 for a BME280 (S16 §5.4.1) and 0x58 for a BMP280. The value 0x60 is a register value, not an I2C address, so it does not clash with the Si5351.

### INA226 / INA219
- The INA226 is the better meter: 36 V bus, ±81.92 mV shunt range, 16 addresses (S18).
- **CJMCU-226 mechanics** come from a single listing (20 × 27 mm, 3 mm holes). Treat them as unknown and measure.
- **Shunt choice:** with the common R100 shunt, full scale is 0.819 A. `board-power.md` estimates the board at ≤ 0.32 A, so R100 suits it.
- **INA219 alternative:** Adafruit #904 has exact Eagle geometry (above). Its terminal block is on the edge opposite the header.

### Si5351A
- **#2045 holes:** only the header edge has holes. The top edge carries the 3 SMA footprints, which are edge-launch, so they need a slot or overhang in the plate if fitted.
- **No u.FL** on either Adafruit board.
- **Output:** 3.3 V CMOS, fixed address 0x60.
- **Is there a clock pin to drive?** `clock-pins.md` covers this: PIN_24 on header P1-34, which it says the real board still needs checked.

### MOSFET drivers for heater (12 V, ≤ 1.5 A) and fan

| Option | 3.3 V gate guaranteed? | Pros | Cons | Verdict |
|---|---|---|---|---|
| IRF520 module | **No.** V<sub>th</sub> up to 4.0 V; R<sub>DS(on)</sub> only at 10 V | Cheap, everywhere | May not turn on at all from a Pico | **Reject** |
| D4184 opto module | Not needed: the gate is driven at ½ V<sub>load</sub> ≈ 6 V from 12 V | Pico only lights an LED (≈ 2 mA); heater ground isolated from logic ground (matches `board-power.md` TL;DR item 5 and §4; *cite corrected: that file has no §5*); ≤ 9.5 mΩ class | Needs ≥ ≈ 6 V load supply (9 V+ advised), so **useless on a 5 V fan**; opto plus 4.7 kΩ gate network is slow | **Heater: yes**, at low PWM (≈ 10–100 Hz) or time-proportioned |
| Dual-AOD4184 direct module | No (typical only) | Simple, shared ground, any frequency | 3.3 V operation is "derate" territory (S33: "must be derated"). ~~though trivial at 1.5 A~~ **UNVERIFIED for a worst-case part**: with V<sub>GS(th)</sub> up to 2.6 V, a 3.3 V gate may conduct well under 1.5 A and sit in its linear region, where it heats (see the AOD4184A row) | Fallback only, after measuring V<sub>DS</sub> at the real load current |
| AO3400A discrete | **Yes** (≤ 48 mΩ @ 2.5 V) | Guaranteed, tiny, fast | SOT-23 needs an adapter; add a gate resistor, a 10–100 kΩ pull-down and a fan flyback diode | **Fan: yes** (5 V, 25 kHz OK) |
| IRLZ44N discrete | No (spec'd at ≥ 4 V) | TO-220, easy to solder | Not guaranteed at 3.3 V | Only if AO3400A is impractical |

**Opto speed (derived, unverified):**
- Turn-off discharges about 1.8 nF C<sub>iss</sub> (max, S28) through 4.7 kΩ, so τ ≈ 8.5 µs. Turn-on goes through about 2.35 kΩ, so τ ≈ 4 µs. Both are before adding the PC817's own delay and the Miller plateau.
- 25 kHz has a 40 µs period, so it is not workable. The seller gives no frequency limit.
- **Measure** the module's output edges with the logic analyser before choosing a PWM frequency.

**Recommended-module mechanics (listing only):** 35 × 16 × 14 mm; 2 × Ø2 mm holes 12 mm apart at the signal end; PWM/GND input at that end; the "+ / LOAD / −" screw terminal at the other end. Hole offsets from the edges are unknown, so MEASURE before modelling bosses.

### Logic analyser
- Only one listing gives dimensions (56 × 27.6 × 20.3 mm), and the connector varies (Mini-B or USB-C). It has no mounting holes, so mount it with a strap or clip pocket, sized from calipers.
- Inputs are 5.25 V tolerant with a 2.0 V V<sub>IH</sub>, so they suit 3.3 V FPGA I/O.

### Final I2C address map (I2C0, GP4 = SDA, GP5 = SCL)

| Addr | Device | Set by |
|---|---|---|
| 0x40 | INA226 (A1 = A0 = GND) | module default; check its jumpers |
| (0x41) | INA219 #904, only if fitted alongside the INA226 | bridge the A0 jumper |
| 0x60 | Si5351A (MSOP-10) | fixed |
| 0x76 or 0x77 | BME280 | Adafruit 0x77 (SDO pulled high); GY-BME280 0x76 (SDO weak pull-down) |

- **No collisions** in the MVP set. None of these addresses are in the reserved 0x00–0x07 or 0x78–0x7F ranges.
- **Pull-ups:** each Adafruit board adds 10 kΩ, so three in parallel give ≈ 3.3 kΩ (derived). That is fine at 100 and 400 kHz.

## Must measure (calipers; reference = header edge as X axis and left edge as Y axis, top view)
1. Each module actually bought:
   - PCB length × width × thickness;
   - every hole centre from the two nearest edges, and the hole Ø (drill-shank gauge);
   - the tallest part above the PCB top, including terminal blocks and soldered headers;
   - pin order, read from the silkscreen.
2. Terminal-block heights on the Adafruit #269 and #904.
3. The Pico as fitted: header type and height if soldered (Pico H?), and the micro-USB plug overmould on Alex's cable.
4. INA226 module:
   - shunt marking (R100 / R010);
   - A0/A1 jumper state, confirmed with an I2C scan;
   - real board current, with a USB meter or bench supply.
5. GY-BME280: pin count, regulator present (yes/no), and chip id (0x60 = BME280).
6. MOSFET module chosen:
   - hole offsets and terminal positions;
   - **output edge timing at the intended PWM frequency**, captured with the logic analyser.
7. Logic analyser case dimensions, connector type, and header pin count and order.
8. If using a Pico 2: the RP2350 stepping marking (E9 affects A2).
9. *(Added by verifier)* Every Adafruit board bought: confirm the outline and hole centres against the Eagle numbers above, because all four files predate the current revision. On the #269, gauge the hole Ø (2.0 or ≈ 2.2) before choosing M2 hardware.
10. *(Added by verifier)* The heater MOSFET module: gate voltage at 100 % duty (DMM, gate to source) and V<sub>DS</sub> at the real heater current. A low gate voltage or a V<sub>DS</sub> well above I × R<sub>DS(on)</sub> means the FET is not fully on.

## Verification (adversarial pass)

Done 2026-10-23 by an independent verifier. Each primary source below was downloaded again this session into a separate scratch folder and read directly:
- PDFs were read with PyMuPDF text extraction or rendered pages;
- Eagle `.brd` files were parsed by a fresh Python script (outline on layer 20, element pads transformed for rotation, nets from `contactref`);
- STEP files were opened in CadQuery 2.8 (solid bounding boxes, cylinder-face radii and centres).

None of the original author's scripts or files were reused. Nothing was measured on Alex's hardware.

### Checked and confirmed (no change)
| # | Claim | Re-derived from |
|---|---|---|
| 1 | Pico / Pico 2: 51 × 21 × 1.0 mm, 4 × Ø2.1 ± 0.05 holes, 11.4 across (4.8 from the long edges), 2.0 from the USB edge, rows 17.78 apart (1.61 from the edges), 48.26 pin span, USB 8 wide overhanging 1.3 (typ) | S1 PDF p.7 Fig 3 and S2 PDF p.8 Fig 3, rendered at 600 dpi: identical dimension sets |
| 2 | Far-end hole also 2.0, so 47.0 along the length | S4 STEP: cylinder faces r = 1.05 at (4.8 / 16.2, 2.0 / 49.0). Now confirmed, not just scaled |
| 3 | PCB 1.00 thick; USB shell top 2.73 above the PCB (3.23 − 0.50); USB overhang 1.3 (52.3 − 51.0); BOOTSEL 2.50; USB body 7.58 wide | S4 STEP solid bounding boxes |
| 4 | GP4/5 = I2C0 SDA/SCL (pins 6/7); GP16/17/18 = SPI0 RX/CSn/SCK (pins 21/22/24, pin 23 GND); GP13 = PWM6 B (pin 17); GP14 = PWM7 A (pin 19); GP15 = PWM7 B (pin 20); GP22 = PWM3 A (pin 29); GP10 = PWM5 A (pin 14); 3V3(OUT) = pin 36 | S5 Table 2 (PDF p.13–14), S6 Table 3, S3 pinout sheet rendered |
| 5 | GP14 and GP15 share slice 7, which has one 16-bit counter, one 8.4 fractional divider and one wrap (TOP) value, so they share one frequency | S5 §4.5.1–4.5.2 (PDF p.523–528) |
| 6 | RP2040 V<sub>PIN</sub> max = IOVDD + 0.5 V (not 5 V tolerant); RP2350 FT pads 5.5 V at IOVDD = 3.3 V; erratum E9 "Affects RP2350 A2" | S5 Table 622 (PDF p.615); S6 §14.9.1 (PDF p.1336), Appendix D.5.1 (printed p.1358) |
| 7 | 3V3 load < 300 mA recommended; VBUS 5 V ± 10 %; VSYS 1.8–5.5 V; −20 to 85 °C; 70 °C recommended max ambient | S1 PDF p.9, p.11–12; S2 PDF p.10 |
| 8 | #269 MAX31855: 20.32 × 22.86 outline; holes (2.54, 20.32), (17.78, 20.32); header Vin/3Vo/GND/DO/CS/CLK; T+ on the right | S7 `Adafruit_MAX31855 v2.brd` parsed; nets traced J1.1 → FB2 → IC1 pin 3 (T+) |
| 9 | MAX31855: V<sub>CC</sub> 3.0–3.6 V; f<sub>SCL</sub> ≤ 5 MHz; t<sub>CONV</sub> 70 typ / 100 max ms; 200 ms at power-up; "K" suffix = K type; T− "Do not connect to GND" | S10 pp.2–4, pin table, ordering info |
| 10 | #2652 QT: 25.4 × 17.78; plated Ø2.5 at (2.54 / 22.86, 15.24); non-plated Ø2.54 at (2.54 / 22.86, 2.54); 7-pin order; SDO 10 kΩ to 3.3 V gives 0x77; host-side SDA/SCL 10 kΩ to VIN (resistor-pack pairs 1–8, 3–6 to VCC); STEMMA QT 2.96 above a 1.57 PCB (4.53 overall) | S11 brd parsed; S13 STEP; S12 fab print; Adafruit guide says the QT board "is the same exact PCB as the BMP280" |
| 11 | BME280 0x76/0x77 via SDO; chip_id 0x60; VDD 1.71–3.6 V | S16 §6.2 (PDF p.32), §5.4.1 |
| 12 | #904 QT: 25.4 × 20.32; 4 × Ø2.5 at a 2.54 mm inset; header VCC/GND/SCL/SDA/VIN−/VIN+; terminal pads (10.9 / 14.4, 16.51) = VIN− / VIN+; SDA/SCL pulled to VCC; A0/A1 pulled down, giving 0x40/41/44/45 | S20 brd parsed; S21 |
| 13 | #2045: 30.48 × 21.59; Ø2.5 at (2.54 / 27.94, 2.54); header CLK0, CLK1, CLK2, SCL, SDA, GND, VIN left to right; SMA at x = 5.08 / 15.24 / 25.40; no u.FL; host-side pull-ups to VIN; VDD and VDDO both on the 3.3 V LDO. #5640 QT: 25.4 × 17.78, 4 × Ø2.5, 1 SMA | S24 brds parsed (both) |
| 14 | Si5351: 0x60 when there is no A0 pin ("Only the Si5351A 20-QFN and Si5351A 16-QFN have the A0 LSB pin option"); V<sub>OH</sub> ≥ VDD − 0.6, V<sub>OL</sub> ≤ 0.6 at C<sub>L</sub> = 5 pF; 2.5 kHz–200 MHz | S26 Rev 1.3 PDF p.18, p.10, p.1 |
| 15 | INA226: 16 addresses, A1 = A0 = GND gives 0x40, pins "sampled on every bus communication"; shunt −81.9175 to 81.92 mV; bus 0–36 V; supply 2.7–5.5 V. 81.92 mV / 0.1 Ω = 0.819 A, which covers `board-power.md`'s ≈ 320 mA high case | S18 Table 6-2 (PDF p.18), §5.5 |
| 16 | IRF520: V<sub>GS(th)</sub> 2.0–4.0 V at 250 µA; R<sub>DS(on)</sub> ≤ 0.27 Ω at V<sub>GS</sub> = 10 V, I<sub>D</sub> = 5.5 A only. **Verdict "reject" stands** | S27 S21-0819 Rev C, p.2 |
| 17 | AOD4184A: 40 V; V<sub>GS(th)</sub> 1.7 / 2.1 / 2.6 V; ≤ 7 mΩ at 10 V, ≤ 9.5 mΩ at 4.5 V; C<sub>iss</sub> max 1800 pF | S28 p.1–2 |
| 18 | AO3400A: 30 V; ±12 V; V<sub>GS(th)</sub> 0.65 / 1.05 / 1.45 V; ≤ 26.5 / 32 / 48 mΩ at 10 / 4.5 / 2.5 V; 5.7 A; R<sub>θJA</sub> steady 125 °C/W max on 1 in² 2 oz FR-4. 1.5² × 0.048 = 0.108 W, × 125 = 13.5 °C. **Verdict "fan: yes" stands** | S29 p.1–2, Note A |
| 19 | IRLZ44N: V<sub>GS(th)</sub> 1.0–2.0 V; ≤ 22 / 25 / 35 mΩ at 10 / 5 / 4 V | S30 p.2, rendered |
| 20 | D4184 opto module: 35 × 16 × 14; 2 × Ø2 holes 12 apart at the signal end; PC817 + 1 kΩ; 4.7 k / 4.7 k divider, so the gate is at 50 % of supply; load 6–36 V. τ arithmetic: 4.7 kΩ × 1.8 nF = 8.5 µs; 2.35 kΩ × 1.8 nF = 4.2 µs | S32 (listing), S28 |
| 21 | Dual-AOD4184 MOD-117: 34 × 17 × 12; 3.3–20 V input; 5–36 V output; signal GND = VIN− | S33 (listing) |
| 22 | GY-BME280: 15.5 × 11.5; VCC, GND, SCL, SDA, CSB, SDO; 0x76 default; 10 k pull-ups to its 3.3 V | S17 (listing) |
| 23 | I2C map has no collision (0x40, 0x60, 0x76/0x77); three 10 kΩ pull-ups in parallel ≈ 3.33 kΩ | From items 10–15 |

### Corrected
- **AOD4184A at a 3.0 V gate:** ≈ 2.6 A typical at 25 °C, not "4–5 A" (S28 Fig 2, read from the PDF's vector path data). The 3.3 V figure (≈ 17.5 A) was right. The "trivial at 1.5 A" claim for the direct-drive dual-AOD4184 module is now marked UNVERIFIED for worst-case-threshold parts.
- **PWM floor formula:** the largest divisor is 256 (DIV_INT = 0), not 255.9375. The result, ≈ 7.45 Hz at 125 MHz, is unchanged. Added that phase-correct mode halves it.
- **#269 header row y = 2.03** (Eagle 2.032), not 2.02. **Terminal pad y = 19.05**, not 19.04.
- **#269 supply row:** "Vin 3–5 V" becomes "3.3–5 V" (S9 wording), and the tag drops from datasheet to listing, by this report's own convention that product pages are listings.
- **CJMCU-226 shunt source:** S22 as fetched does not state a shunt value. Re-sourced to S23's code comment and marked UNVERIFIED. This matches `board-power.md`'s own verifier.
- **Cross-reference:** "board-power.md §5" becomes TL;DR item 5 / §4, since that file has no §5.
- **BME280 wording:** 1.71–3.6 V is the operating range. The absolute maximum is 4.25 V (S16 Table 5).
- **#904 holes:** "2.54 in from each edge" now reads "2.54 mm", so it cannot be read as inches.

### Downgraded or marked UNVERIFIED
- **All four Adafruit Eagle files predate the shipping revision.** The commit dates (GitHub API) against the product-page notes:

  | Board | Files committed | Later product-page revision |
  |---|---|---|
  | #269 | 2019 | 6 Jun 2024 |
  | #2652 QT | Jul 2020 | 18 Sep 2023 "Pinguin" |
  | #904 QT | Aug 2021 | 22 Sep 2022 chip/package change; 31 May 2024 terminal block |
  | #2045 | 2016–2019 | 22 Dec 2023 "Pinguin" |

  The listing dimensions still agree to within rounding, so the outlines have probably not moved, but that is unproven.
- **#269 hole diameter:** the S8 fab print's callout at the hole reads 0.09 in (≈ 2.3 mm), against S7's 2.0 mm drill, and Adafruit's old BME280 uses a 2.2 mm drill in a footprint of the same name. Marked UNVERIFIED; gauge it.
- **IRF520 module dimensions:** S31 gives none, and the numbers came from unverifiable search snippets.
- **Logic analyser:** "Some newer units USB-C" came from a search snippet. Input range corrected to −0.5…5.25 V per S35, and S34's conflicting "12 MS/s with 8 channels" is noted.
- **Generic MAX31855 boards** being mostly regulator-less is not supported by S10.
- **GY-BME280 4-pin "5 V" variant:** S17 does not describe a 4-pin board.
- **D4184 opto at about 2 mA LED drive:** no PC817 datasheet was checked, so measure the gate voltage.
- **RP2350 FT caveat added:** the ADC-capable pins (GP26–28) are not 5 V tolerant even on a Pico 2.

### Still unverified after this pass (not re-checked)
- **Pico 2 tallest-part height:** there is still no Pico 2 STEP; both URLs tried returned 404 this session.
- **Generic clones** (CJMCU-226, GY-BME280, red/purple MAX31855, D4184 hole offsets, logic-analyser case): only listing data exists.
- **Opto switching speed and the 25 kHz unsuitability:** the τ arithmetic is right, but the PC817's own delay was not checked.
- **Terminal-block heights** on #269 and #904.
- **The MAX31855 SPI-mode-0 inference.**

The original author's Pico 2 and pin-map conclusions, the IRF520 rejection, the AO3400A choice and the address map all survived.
