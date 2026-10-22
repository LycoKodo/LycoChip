# Board power and INA226 insertion: research notes

**TL;DR**
1. The board takes a **regulated 5 V** supply through either a **DC barrel jack** (centre pin = +5 V) or a **power-only USB-B** socket. A red latching **DPDT push button selects the source**: pressed = USB, up = DC jack. It is not a plain on/off switch. There is **no fuse, no reverse-polarity protection and no over-voltage protection**.
2. All three rails come from linear **1117-series LDOs** (SOT-223): 5 V → **3.3 V** (U1), 5 V → **2.5 V** (U3), and **3.3 V → 1.2 V** (U2, fixed output, no adjust pin). The core rail is fixed. Because every rail is linear, **current in at 5 V ≈ the sum of every rail's current**.
3. Estimated input current is about **70 / 125 / 290 mA** (low / typical / high, *derived*, not measured; worst-case silicon at Tj 85 °C adds ≈ 28 mA, so the high case is ≈ 320 mA — see Verification). The FPGA's own share for the demo build is small: about 84 mW per Quartus. **Measure the real figure** before trusting any of this.
4. Recommendation: a **high-side** INA226 in the **+5 V wire of a DC-jack pigtail** (panel jack → IN+ → shunt → IN− → plug → board), with VBUS wired to IN−. The **stock 0.1 Ω module works**: full scale is 0.819 A, the LSB is 25 µA (CAL = 2048), and the drop is about 13 mV at 125 mA. A low-side (GND) shunt is **fragile** *(corrected — was "will not work")*: it reads right only while nothing but the shunt touches the 5 V supply's negative; an earthed adapter or a USB-port supply lets return current bypass it through the USB-Blaster, logic analyser and Pico grounds.
5. Ground: use one star point on the module plate (Pico GND, INA226 GND, sensor GNDs, MOSFET-module *signal* GND, and **one** thin wire to an FPGA header GND pin). Heater current goes straight from the MOSFET source back to the **isolated (2-prong) 12 V adapter**, never through the star, the Pico or the FPGA board. The 5 V and 12 V inlets must be **physically impossible to swap**.

---

## Sources (short names used below)

| Tag | Document |
|---|---|
| SCH | `resources/Altera-Cyclone-IV-board-V3.0 documentation/Hardware documentation/Development board schematic diagram V2.1.pdf`. This is a single A1 sheet; the blocks used are "Power and light", "3.3V, 2.5V, 1.2V power", "FPGA main chip", "JTAG and AS", "IO interface", "SDRAM", "Crystal and reset", "Digital Tube" and "Button, LED". |
| MAN | `.../Dev Board Manual.pdf`, page 1, "1. Power supply" (text and photo) |
| PHOTO | Photo on MAN page 1, plus `.../board.jpg` |
| AMS | AMS1117 datasheet (Advanced Monolithic Systems, **800 mA** edition), https://files.waveshare.com/upload/b/b8/AMS1117-datasheet.pdf, pages 1–3 *(verifier: dropout, current limit and quiescent current are on p3, not p2)* |
| QPOW-MAX | `quartus_pow` re-run by the verifier this session on its own scratch copy of the same demo fit, with `POWER_USE_DEVICE_CHARACTERISTICS=MAXIMUM` (worst-case silicon), Tj 25 and 85 °C, default toggle rates. Same "Low" confidence caveat. |
| USOL | universal-solder.ca INA226 module listing, https://universal-solder.ca/ina226-current-sensor-module/ (shop page; not confirmed to be the same PCB as the purple CJMCU-226) |
| SDRAM | `.../Components manual/HY57V641620.pdf`, page 9, "DC Characteristics II" |
| MAX3232 | `.../Components manual/max3232.pdf`, page 3 |
| EPCS | `.../Components manual/Serial Configuration Devices(EPCS4,EPCS16).pdf`, page 35, Table 14–22 |
| QPOW | `quartus_pow` (Quartus 25.1std), run **this session** on a scratch copy of `~/.lycochip-build/projects/demo` (the MNIST demo, fitted 2026-10-21). The repo and the build directory were not touched. Quartus rates this "Low" confidence because it is a vectorless toggle estimate. |
| INA226 | TI INA226 datasheet SBOS547C, https://www.ti.com/lit/ds/symlink/ina226.pdf: §5.1, §5.5, §6.5, Table 6-2, Table 7-3 |
| INA219 | TI INA219 datasheet SBOS448G, https://www.ti.com/lit/ds/symlink/ina219.pdf: Electrical Characteristics, Table 1 |
| TINK | Tinkery AU kit listing for the OMDAZZ board, https://www.tinkery.com.au/products/altera-cyclone-iv-fpga-kit |
| ARDF | Arduino forum, CJMCU-226 thread, https://forum.arduino.cc/t/current-sensor-cjmcu-226/1002787 |
| H2E | how2electronics INA226 module guide, https://how2electronics.com/how-to-use-ina226-dc-current-sensor-with-arduino/ |

## Facts table

| Item | Value | Unit | Source | Confidence | Notes |
|---|---|---|---|---|---|
| Power inputs | DC jack "POWER" (3-pin) + USB-B "USB" (6-pin incl. shell) | – | SCH Power and light; PHOTO ("USB供电" = USB power) | vendor-doc | USB pins 2 and 3 (D−/D+) are unconnected, so the socket carries **power only**. TINK says the same. |
| Input voltage | 5 (regulated) | V | SCH label "外部+5V电源" (external +5 V supply); MAN; TINK | vendor-doc | TINK: "must be regulated 5V DC… no over-voltage nor reverse polarity protection" |
| Barrel polarity | centre pin (pin 1) = +5 V; pins 2 and 3 (sleeve/switch) = GND | – | SCH; TINK "Center/pin positive" | vendor-doc | Confirm with a continuity check (see Must measure) |
| Barrel size | **unknown** | mm | none found | unknown | 5.5 × 2.1 is common on boards like this, but no source confirms it. Measure it. |
| Power switch | SW-DPDT, red latching push button. Both poles in parallel. **Selects** the source: pressed = USB, up = DC jack | – | SCH; MAN | vendor-doc | Only +5 V is switched. Both input grounds are always tied to board GND. With a single source plugged in, the button works as on/off (TINK). |
| Power LED | D1 + R1 2 kΩ from 5 V | – | SCH | vendor-doc | ≈ (5 − 2)/2000 = 1.5 mA, assuming Vf ≈ 2 V (*derived*) |
| U1 | 1117-3.3, Vin = 5 V → 3.3 V | – | SCH | vendor-doc | Also feeds U2, so all 1.2 V current passes through U1 |
| U3 | 1117-2.5, Vin = 5 V → 2.5 V | – | SCH | vendor-doc | Feeds VCCA (PLL analog) and the JTAG header pin 4 (VREF) |
| U2 | 1117-1.2, Vin = **3.3 V** → 1.2 V | – | SCH | vendor-doc | Fixed output (pin 1 = GND, no adjust divider), so **the core rail is fixed** |
| Regulator package | SOT-223 (3 leads + tab) | – | PHOTO (U1/U2/U3 silkscreen) | photo-estimate | The maker is **unknown**: the schematic only says "1117". The AMS 800 mA datasheet lists no fixed 1.2 V version, so U2 may come from another vendor. Read the markings. |
| LDO caps | 10 µF/16 V polarised (tantalum in photo) + 100 nF on each output; C2 10 µF on U1 input | – | SCH; PHOTO | vendor-doc | Tantalums fail short when reverse-biased, which adds to the reverse-polarity risk |
| Rail use | VCCINT 1.2 V (8 pins); VCCD_PLL 1.2 V via ferrite beads; VCCA 2.5 V; VCCIO all banks 3.3 V; SDRAM, osc, EPCS, MAX3232, LEDs, 7-seg on 3.3 V | – | SCH FPGA main chip, SDRAM, Crystal, JTAG/AS | vendor-doc | 5 V is used by the power LED, PS/2 (R23/R24 10 kΩ pull-ups), the **header 5 V pins** (P1 37/38, P2 1/2, P3 19) **and the 1602/12864 LCD connector** *(corrected — the original said "only" and missed it)*: LCD pins 2, 15, 17, 19 are on 5 V, and the contrast divider RW 10 kΩ + R29 1 kΩ sits across 5 V → ≈ 5/11 kΩ = 0.45 mA always (*derived*, if RW/R29 are fitted). An LCD plugged into that socket would add its logic and backlight current to "board power". |
| Header power pins | P1: GND 1,2 · 3.3 V 35,36 · 5 V 37,38; P2: 5 V 1,2 · 3.3 V 3,4 · GND 5,6; P3: GND 1,2 · 5 V 19 · 3.3 V 20 | – | SCH IO interface | vendor-doc | Anything powered from these pins is counted in "board power" |
| Rail test pads | plated holes labelled GND, 3.3 V(?), 5 V, 1.2 V near U1/U2 | – | PHOTO (MAN p1) | photo-estimate | The "3.3V" label is partly hidden. Useful for checking rail voltages. |
| On-board protection | none (no fuse, polyfuse, diode, TVS) | – | SCH power blocks; TINK | vendor-doc | |
| AMS1117 dropout | 1.1 typ / 1.3 max at 800 mA | V | AMS **p3** *(page corrected)* | datasheet | Decreases at lower current. Applies only if U1–U3 really are AMS parts (maker unknown). |
| AMS1117 quiescent current | 5 typ / 10 max (each) | mA | AMS **p3** *(page corrected)* | datasheet | ×3 regulators, and all of it is drawn from the 5 V input |
| AMS1117 current limit | 0.9 min / 1.1 typ / 1.5 max | A | AMS **p3** *(page corrected)* | datasheet | |
| AMS1117 Vin abs max | 15 | V | AMS p2 | datasheet | The 15 V rating is datasheet. "Survives a 12 V mis-plug for a while" is **UNVERIFIED** (no source). *Derived:* U1 at 12 V with ≈ 100 mA on the 3.3 V side dissipates (12 − 3.3) × 0.1 ≈ 0.87 W → +78 °C at 90 °C/W, i.e. Tj ≈ 140 °C in a 60 °C box, above the 125 °C control-section limit; C2 (10 µF/16 V tantalum) would sit at 75 % of rating. And the **5 V header pins, PS/2 pull-ups and LCD socket would carry 12 V**. Treat a 12 V mis-plug as destructive. |
| AMS1117 θJA SOT-223 | 90 (46 to >90 depending on copper) | °C/W | AMS p2 | datasheet | |
| Minimum board input | **4.75** *(corrected from ≈ 4.6)* | V | AMS p2: AMS1117-3.3 output tolerance is specified for "4.75 V ≤ VIN ≤ 12 V" | datasheet (if U1 is an AMS part) | 3.3 + 1.3 = 4.6 V is only the 800 mA dropout bound, not the guaranteed operating condition, so it is not "conservative". At ~0.1 A the real dropout is lower and the board will probably still regulate at 4.6 V, but that is **unverified**. Margin from a 5.00 V adapter is **0.25 V**, not 0.4 V, and a 5 V ±5 % adapter can use all of it. |
| FPGA currents (demo build, Tj 26 °C) | VCCINT 19.2 · VCCIO 6.8 · VCCA 15.5 · VCCD 1.0 | mA | QPOW | derived | Total 83.6 mW (static 43.0, dynamic 10.9, I/O 29.7) |
| FPGA static vs Tj | VCCINT static 9.96 / 10.60 / 11.56 / 13.03 at Tj 25 / 45 / 65 / 85 °C; VCCA 15.47 / 15.90 / 16.40 / 16.98 | mA | QPOW, `POWER_TJ_VALUE` fixed | derived | Uses typical silicon. Input-current change from 25 °C: **+1.1 / +2.6 / +4.6 mA** (includes VCCD +0.03/+0.05 mA; verifier reproduced the 25, 65 and 85 °C points). |
| FPGA currents, **worst-case silicon** | Tj 25 °C: VCCINT 21.50 · VCCIO 9.28 · VCCA 18.27 · VCCD 1.94; Tj 85 °C: VCCINT 36.90 · VCCIO 9.28 · VCCA 20.19 · VCCD 3.80 | mA | QPOW-MAX | derived | *(added by verifier)* Input-current change 25 → 85 °C is **+19.2 mA**, about 4× the typical-silicon +4.6 mA. A real chip lies somewhere between; the leakage signal is uncertain by ≈ 4×. |
| SDRAM (HY57V641620) | IDD2PS 2 · IDD2NS 15 · IDD3N 40 · IDD1/IDD4 100–120 · IDD5 150–170 | mA | SDRAM p9 | datasheet | Max limits, 3.3 V. The fitted part may be a different 64 Mb SDRAM (the folder also holds k4s641632h.pdf). Read the marking. |
| MAX3232 Icc | 0.3 typ / 1 max | mA | MAX3232 p3 | datasheet | |
| EPCS16 Icc | 0.05 standby / 5–14 active | mA | EPCS Table 14–22 | datasheet | Active only during configuration |
| 50 MHz oscillator | part unknown, 3.3 V | – | SCH Crystal | unknown | 5–25 mA is used below as a **placeholder assumption** |
| User LEDs | 4 × 470 Ω from 3.3 V, active low | – | SCH Button/LED | vendor-doc | (3.3 − Vf)/470 ≈ 3 mA each if red (Vf ~1.9 V assumed) |
| 7-segment | 220 Ω per segment, 8550 PNP digit drivers from 3.3 V, multiplexed | – | SCH Digital Tube | vendor-doc | ≈ 5–6.4 mA per lit segment; ≤ ~51 mA average with all 8 lit (*derived*, Vf/Vce assumed) |
| **Board input current** | ~70 low / ~125 typical / ~290 high | mA | see calculation below | derived | **Not measured.** The high case excludes heavy FPGA designs and anything on the headers. It also uses typical silicon at 25 °C: worst-case silicon at Tj 85 °C (QPOW-MAX, 70.2 mA total vs 42.4 mA) puts the high case at ≈ 320 mA (*derived*), still 2.6× under the 0.1 Ω full scale. |
| INA226 shunt range | ±81.92 | mV | INA226 §5.5 | datasheet | |
| INA226 shunt LSB | 2.5 | µV | INA226 §5.5 | datasheet | 16-bit ADC |
| INA226 bus range / LSB | 0–36 / 1.25 | V / mV | INA226 §5.5 | datasheet | Measured at the **VBUS pin**, not IN− |
| INA226 offset / gain error | ±2.5 typ, ±10 max µV / 0.02 typ, 0.1 max % | – | INA226 §5.5 | datasheet | |
| INA226 supply | 2.7–5.5 V, IQ 330 typ / 420 max µA | – | INA226 §5.5 | datasheet | Power it from the Pico's 3.3 V |
| INA226 abs max on IN+/IN−/VBUS | −0.3 to 40 | V | INA226 §5.1 | datasheet | |
| INA226 conversion / averaging | 140 µs to 8.244 ms; AVG 1, 4, 16, 64, 128 … 1024 | – | INA226 §5.5, Table 7-3 | datasheet | |
| INA226 address | 16 options, 0x40–0x4F; A1 = A0 = GND → **0x40** | – | INA226 Table 6-2 | datasheet | A0/A1 can each tie to GND, VS, SDA or SCL |
| INA226 calibration | CAL = 0.00512 / (Current_LSB × R); Current_LSB ≥ Imax / 2^15; Power LSB = 25 × Current_LSB | – | INA226 §6.5 | datasheet | |
| Purple / CJMCU-226 shunt | "R100" = 0.100 Ω | Ω | ~~ARDF / search snippets~~ USOL ("factory-assembled shunt … 0.1 Ohm", "about −820 to +820 mA"); SMD "R" code | listing | *(source corrected: the ARDF thread does not mention the shunt value or an R100 marking; "search snippets" cannot be checked.)* USOL is a different shop's INA226 module, so the value for **your** CJMCU-226 is **UNVERIFIED**. Read the marking on your module. |
| Module pinout | VCC GND SCL SDA ALE **VBS** IN− IN+ | – | ARDF; H2E | listing | **VBUS is a separate pin.** Wire it to IN− (H2E: "Connect the VBus pin to Vin- pin"). |
| Module A0/A1 | 10 kΩ pull-downs on both → 0x40 | – | ARDF (one user's DMM reading) | listing | Measure your module. I²C pull-up values are **unknown**. |
| 0.1 Ω full-scale current | 81.92 mV / 0.1 Ω = **0.819** | A | – | derived | 2.8× the high estimate |
| 0.1 Ω resolution | 2.5 µV / 0.1 Ω = **25 µA** → CAL = 0.00512 / (25e-6 × 0.1) = **2048**; power LSB 625 µW | – | – | derived | |
| 0.1 Ω offset error | ±10 µV / 0.1 Ω = ±100 µA max (±25 µA typ) | – | – | derived | Can be zeroed with the board off |
| 0.1 Ω burden / dissipation | 12.5 mV, 1.6 mW at 125 mA; 29 mV, 8.4 mW at 290 mA; 82 mV, 67 mW at full scale | – | V = IR, P = I²R | derived | |
| INA219 (compare) | shunt ±40/80/160/320 mV (PGA /1–/8); LSB 10 µV; 12-bit; bus 0–26 V abs (16/32 V FSR); bus LSB 4 mV; offset ±10 typ / ±100 max µV (PGA /1, A grade); IQ 0.7/1 mA; same 0x40–0x4F address map | – | INA219 EC table, Table 1 | datasheet | With 0.1 Ω: FS 0.4 A (PGA /1) to 3.2 A (/8), LSB 100 µA, offset up to ±1 mA |
| Heater current | 12 V / 10 Ω = 1.2 | A | BRIEF §3 values | derived | The brief gives ~1–1.5 A. *(Verifier note:)* P = 12²/10 = 14.4 W at 100 % duty, more than a 10 W resistor's rating; flag for the heater report. |

## 1. How the board is powered (SCH "Power and light" + MAN p1)

```
DC jack pin1 (centre) ──┬── SW pin4 ─┐                      ┌── 5V rail ──┬─ U1 1117-3.3 ─ 3.3V ─┬─ U2 1117-1.2 ─ 1.2V (VCCINT, VCCD_PLL)
                        └── SW pin1 ─┤  "up"  (DC)  ──► 6,3 ┤             │                      └─ VCCIO, SDRAM, osc, EPCS, LEDs, 7-seg, MAX3232 …
USB-B VBUS (pin1) ──────┬── SW pin5 ─┤  "pressed" (USB) ──► ┘             ├─ U3 1117-2.5 ─ 2.5V (VCCA, JTAG VREF pin 4)
                        └── SW pin2 ─┘                                    └─ power LED, PS/2, header 5 V pins
DC jack pins 2,3 + USB GND/shell ─────────── board GND (always connected, never switched)
```

- The DPDT has both poles in parallel; it chooses which input feeds the 5 V rail. With only one input plugged in, it works as on/off.
- **Because every regulator is linear, the 5 V input current equals the sum of all rail currents plus three regulator quiescent currents (5–10 mA each).** This is useful: an INA226 at the input sees a 1 mA change on VCCINT as a 1 mA change at 5 V. It follows that **board-input power over-states a core-power change by 5 V / 1.2 V ≈ 4.2×**. The extra is burned in U1 (1.7 V × ΔI) and U2 (2.1 V × ΔI). Log current, not just power, and convert to core power with ΔP_core ≈ 1.2 V × ΔI_in when only VCCINT moved.
- The 5 V → 3.3 V stage has 1.7 V of headroom against a 1.3 V maximum dropout. Keep the board's 5 V at or above **4.75 V** under load *(corrected from "about 4.6 V": 4.75 V is the input range over which AMS specifies the 1117-3.3 output, AMS p2)*. **Do not add a series diode** for reverse-polarity protection: a 0.3–0.7 V drop uses up the whole margin.

## 2. Current-draw estimate (derived; replace with a measurement)

The input current is the 3.3 V-side load plus U1's quiescent current, plus the 2.5 V side, plus loads on 5 V directly. Values are in mA.

| Load | Low | Typical (demo-like) | High | Basis |
|---|---|---|---|---|
| FPGA VCCIO | 6.8 | 6.8 | 6.8 | QPOW (design-dependent) |
| 1.2 V rail: VCCINT 19.2 + VCCD 1.0 + U2 quiescent | 25.2 | 25.2 | 30.2 | QPOW + AMS quiescent 5/10 |
| SDRAM | 2 (CKE low) | 15 (IDD2NS) | 120 (IDD4) | SDRAM p9 |
| 50 MHz oscillator | 5 | 15 | 25 | **assumption**, part unknown |
| MAX3232 + EPCS standby | 0.35 | 0.35 | 1.05 | datasheets |
| LM75 + AT24C08 + IR receiver | 1 | 2 | 5 | **assumption**, not looked up |
| 4 LEDs | 0 | 6 | 13 | 470 Ω, Vf assumed |
| 7-segment (multiplexed) | 0 | 27 | 51 | 220 Ω, Vf/Vce assumed |
| U1 quiescent | 5 | 5 | 10 | AMS |
| 2.5 V rail: VCCA 15.5 + JTAG pull-ups/VREF + U3 quiescent | 20.5 | 21 | 27 | QPOW + AMS; Blaster VREF draw unknown |
| Power LED (5 V) | 1.5 | 1.5 | 1.5 | SCH |
| **Total at 5 V input** | **≈ 67** | **≈ 125** | **≈ 291** | 0.34 / 0.63 / 1.46 W |

*(Verifier: the column sums were re-added and are right: 67.35 / 124.85 / 290.55 mA. Not in the table: the always-on LCD contrast divider, ≈ 0.45 mA from 5 V, which is negligible. The FPGA rows use typical silicon at 25 °C; see the worst-case row in the facts table.)*

A bigger or faster FPGA design adds its extra VCCINT current one-for-one at the input. Run `quartus_pow` on each build to predict it. No published measurement of this board's draw was found (searches on 2026-10-23 returned only spec listings), so this table is the best available until Alex measures. A **5 V adapter rated at least 1 A** gives more than 3× margin over the high case.

## 3. Inserting the INA226 without modifying the board

**Recommended: a DC-jack pigtail with a high-side shunt.** Leave the board's USB-B **unplugged**. Then the red button is a clean on/off, and the board cannot quietly switch to an un-metered USB supply.

```
 5 V regulated adapter (isolated, 2-prong, >=1 A)
        │ plug
  [box panel jack "FPGA 5V"]──── GND conductor (straight through, NOT via the shunt) ───────────┐
        │ +5 V                                                                                   │
        └──► INA226 IN+ ──[ R100 0.1 Ω ]── IN− ──┬──► +5 V ──► male DC plug (centre +) ──► board jack
                                                 └── VBS/VBUS (short jumper to IN−)         board jack sleeve ◄┘
   INA226 VCC ◄── Pico 3V3     SDA/SCL ◄──► Pico I²C (GP4/GP5 per brief)     ALE ─► optional Pico GPIO
   INA226 GND ──► STAR (module plate) ──► one thin wire ──► FPGA header GND (e.g. P2 pin 5/6)
```

- **Use high-side.** Board GND is already tied to the host through the USB-Blaster and the logic analyser, and the Pico is tied to the host through its USB. *(Corrected — the original said a ground-wire shunt "would be bypassed".)* That only happens if the 5 V supply's negative has a second path to the host: an earthed adapter, an earthed bench supply, or the USB pass-through below, whose negative *is* host ground. With a truly floating (Class II) adapter, all DC return current still has to go through a low-side shunt, so it would read correctly. High-side is still the right choice because it does not depend on what the adapter's negative is tied to. In the high-side +5 V wire, the only path for supply current is through the shunt. The INA226 can sit at 5 V because its common-mode range is 0–36 V (§5.5); the 126 dB minimum CMRR is why the 5 V offset adds no meaningful error.
- **VBUS must be wired**, because the module brings it out as a separate pin. If it is left open, the bus-voltage and power registers are meaningless. Tying it to IN− logs the voltage delivered to the pigtail, so the box can watch the 4.6 V margin continuously. An optional refinement is a separate VBUS sense wire to header P2 pin 1 (5 V, after the switch), which reads the true board rail. It draws only about 6 µA (VBUS input impedance 830 kΩ).
- **Calibration:** use Current_LSB = 25 µA and CAL = 2048. The current register then equals the shunt register: 1 count = 25 µA. A suggested logging setup is CT = 1.1 ms on both channels with AVG = 64, giving an update every ≈ 2 × 1.1 ms × 64 ≈ 141 ms (*derived*). The averaging smooths the 7-segment multiplexing ripple. The shunt tolerance on the module is unknown and probably dominates the INA226's 0.1% gain error, so trim CAL against a bench DMM in series.
- **Power the INA226 from the Pico's 3.3 V**, not from the FPGA board. Powering it from the board would add its own current to the reading and create an extra ground tie. The same rule applies to everything else: **power no fan, module or Si5351 from the board's header 5 V or 3.3 V pins**, or it gets counted as "board power".
- **Alternative: a USB pass-through.** Because the board's USB-B is power-only, a USB-A plug → INA226 (in VBUS) → USB-B plug pigtail is equally non-invasive. It is not preferred because the host port becomes the supply (noisier, with a current limit) and the switch must stay pressed. A commercial USB power meter cannot be read by the Pico, but it is a good **independent cross-check** under Article IV.

**Is the stock 0.1 Ω module right?** Yes. Full scale is 0.819 A, about 2.8× the high estimate. The resolution is 25 µA (0.125 mW at 5 V). The drop is about 13–29 mV, inside the **0.25 V** margin *(corrected from 0.4 V)*, though it uses 5–12 % of it. A 0.2 Ω shunt would halve the LSB but cap the range at 0.41 A, too close to the high case for design-dependent loads. A 0.05 Ω shunt (1.64 A full scale) is only worth it if Alex starts powering things from the headers.

**INA226 vs INA219.** The headline experiment wants FPGA leakage against temperature. QPOW predicts only **+1.1 / +2.6 / +4.6 mA** at the input for Tj 45 / 65 / 85 °C relative to 25 °C. The INA226 resolves that as 43–185 LSBs with at most ±0.1 mA offset. The INA219 with the same shunt gives 11–46 LSBs (100 µA LSB) with up to ±1 mA offset, the same size as the signal, although the offset can be zeroed. Choose the **INA226**. Both use the same 0x40–0x4F address map, so never put both on the bus at default straps. *(Verifier: these deltas are for typical silicon. With Quartus's worst-case silicon (QPOW-MAX), the 25 → 85 °C change is +19.2 mA, or 768 INA226 LSBs and 192 INA219 LSBs. The INA226 is still the better choice, but the size of the leakage signal is uncertain by about 4×.)*

**Honest caveat.** The INA226 measures **the whole board**: LDO quiescent current, SDRAM, oscillator and display, plus any of those warmed by the heater. A rise in board current with temperature is therefore not purely FPGA leakage. Run a control experiment with a static bitstream and the display blank.

## 4. Grounding: keep the heater current out of the board and the meter

The goal is that every current returns to its own source on its own wires. The only shared conductor between power domains should be a star wire that carries signal-level (mA) currents.

- **The star point** is a screw terminal, lever connector or solder lug on the module plate beside the Pico. Connect to it: Pico GND, INA226 GND, MAX31855 GND, BME280 GND, Si5351 GND, the **signal** GND of each MOSFET module (the pin beside its PWM input), and **one** wire to an FPGA header GND pin (P2 pin 5/6 or P3 pin 1/2 per SCH).
- **Heater loop:** 12 V adapter + → fuse → KSD9700 thermostat → heater → MOSFET drain; MOSFET source / module power-GND terminal → **directly** back to the 12 V adapter −, with heavy wire. Nothing else connects to the 12 V negative. On most cheap MOSFET modules the signal GND and power GND are the same copper (**UNVERIFIED**: no source was given; check continuity on your module with a DMM), so that module is the single tie between the domains. Heater current enters and leaves on the power terminals and never uses the thin star wire. (On an opto-isolated module there is no tie at all, which is also fine.)
- **FPGA supply loop:** the 5 V adapter − goes only through the pigtail to the board jack sleeve. It does not go to the star. The star-to-board wire therefore carries no supply current, and the INA226 GND tracks the board GND to within microvolts.
- **Use 2-prong (Class II, unearthed) adapters for both supplies.** The host PC is earthed through its own mains cord. If the 12 V adapter's negative were also earthed, heater return current could split through mains earth → PC → USB shields → Pico and FPGA grounds. **Fan:** put a 12 V fan on the heater adapter with its own MOSFET, following the same rules. A 5 V fan must not run from the FPGA board's 5 V. A Si5351 clock into the FPGA needs its own ground return beside the signal (coax or a twisted pair). Detail that in the wiring doc.

## Red flags

1. **No protection on the board.** There is no fuse, no reverse-polarity diode, no TVS. The box also contains a **12 V barrel supply**. Mis-plugging 12 V into the FPGA inlet puts 12 V on the header 5 V pins; reversing polarity back-biases the LDOs and tantalum capacitors. Make the inlets impossible to swap: use different connector families, or a 5 V inlet with a 2.5 mm pin and a 12 V adapter with a 2.1 mm-bore plug, which physically cannot mate. *(Verifier: that keying works one way only. The 5 V adapter's 2.5 mm-bore plug will still go, loosely, into a 2.1 mm-pin 12 V inlet. That direction is harmless, since it only puts 5 V on the heater, but "impossible to swap" is true only for the dangerous direction. Different connector families key both ways.)* Verify by test-fitting. If protection is wanted, use a polyfuse + TVS or an ideal-diode module, **not** a series diode. Alex decides; this costs money.
2. **A low-side (GND) shunt can read wrong** *(softened from "will")*: whenever the 5 V supply's negative has any second path to host ground (an earthed adapter, a bench supply, or a USB-port supply), the USB-Blaster, logic analyser and Pico grounds bypass it.
3. **The source switch can bypass the meter.** If the USB-B is plugged in and the button gets pressed, the board runs from USB and the INA226 reads about 0 while the board works. Leave the USB-B unplugged, or have the lid hold the button "up".
4. **The module's VBUS pin is separate.** Unwired, it gives invalid bus-voltage and power readings.
5. **Header-powered loads pollute "board power".** Keep every module, fan and Si5351 on the Pico's 3.3 V or the 12 V domain.
6. **Earthed adapters** create a heater-current path through the host USB grounds.
7. **Brown-out margin is only about 0.25 V** *(corrected from 0.4 V; the datasheet floor is 4.75 V)*. Keep the pigtail short and check the board's 5 V pad under load.
8. The INA226 module is a bare PCB at 5 V. Mount it on insulating standoffs on the cool plate, away from the heater clamp.
9. MAN warns against plugging or unplugging the JTAG cable while the board is powered. The box should let the Blaster stay connected; power-cycle with the button only.

## Must measure (calipers / DMM)

1. **DC jack size.** Test-fit a 5.5 × 2.1 plug: a firm grip means 5.5 × 2.1; if it will not go over the pin, the pin is about 2.5 mm; if it will not enter the bore, it is a smaller family. Or measure the pin diameter and the bore inner diameter with calipers.
2. **Polarity and switch.** With the board unpowered, check continuity from the jack centre to the "5V" test pad with the button up, and from USB-B VBUS to the "5V" pad with it pressed.
3. **Markings.** Read U1/U2/U3 (maker and current rating), the SDRAM part number, and the 50 MHz oscillator part number.
4. **Real board current** with a bench DMM in series (or a USB meter on the USB-B input): blank/flash design, demo design, and display all-on, all at room temperature. This replaces the §2 table.
5. **Board 5 V under load** at the test pad with the pigtail fitted. Target at least **4.75 V** *(corrected from 4.6 V)*, ideally at least 4.85 V.
6. **INA226 module.** The shunt marking (R100?); A0/A1 pull-down resistance and whether SDA/SCL pull-ups exist (DMM, unpowered); then trim CAL against the series DMM.
7. **A test that cannot pass by accident.** Hang a known resistor (for example 100 Ω, ≥0.5 W) across a header 5 V/GND pair. The INA226 reading must rise by V/R ≈ 50 mA. If the shunt were not in the path, the step would be zero. With the button pressed and USB unplugged (board off), the reading must be within about ±0.1 mA of 0.
8. **Adapters.** Confirm both are 2-prong/Class II. On any 3-prong adapter, check there is no continuity from DC − to the earth pin.

## Verification (adversarial pass)

Done 2026-10-23 by a separate verifier agent. Each claim below was re-derived from the primary source. Schematic blocks were rendered at 9–20× from the PDF with PyMuPDF. The manual was text-extracted, and its page-1 photo was extracted. The TI and AMS datasheets were downloaded and text-extracted. `quartus_pow` was re-run on a private scratch copy of the demo fit.

**Confirmed (no change needed)**

| # | Claim | Re-derived from |
|---|---|---|
| 1 | DC jack "POWER" with pin 1 = the centre symbol and pins 2/3 = GND; label 外部+5V电源 | SCH, Power and light block |
| 2 | USB socket: pin 1 to the switch, pins 2/3 unconnected, pin 4 + shell 5/6 to GND (power only) | SCH; TINK ("data pins are not connected") |
| 3 | SW-DPDT with both poles in parallel (pins 4/1 = DC jack, 5/2 = USB, 6/3 = 5 V). Pressed = USB, lifted = DC jack | SCH; MAN p1 text ("Press … USB power supply; Lift … 5V power adapter"); TINK ("Down = USB, Up = DC Power Jack") |
| 4 | Centre positive; regulated 5 V; no over-voltage or reverse-polarity protection | SCH; TINK quotes |
| 5 | Barrel size not published | Two web searches 2026-10-23 found no source. It stays **unknown**. |
| 6 | U1 1117-3.3 (5 V in), U3 1117-2.5 (5 V in), U2 1117-1.2 (**3.3 V in**); pin 1 = GND (fixed versions, no adjust divider); 104 + 10 µF/16 V caps | SCH, "3.3V, 2.5V, 1.2V power" block |
| 7 | VCCINT on 8 pins at 1.2 V, VCCIO banks 1–8 at 3.3 V, VCCA1/2 at 2.5 V, VCCD_PLL from 1.2 V through ferrite beads FB2/FB4; JTAG pin 4 = 2.5 V | SCH, U5K/U5M and JTAG blocks |
| 8 | Header power pins P1 (GND 1,2; 3.3 V 35,36; 5 V 37,38), P2 (5 V 1,2; 3.3 V 3,4; GND 5,6), P3 (GND 1,2; 5 V 19; 3.3 V 20) | SCH, IO interface block |
| 9 | LED 470 Ω ×4 from 3.3 V; 7-seg 220 Ω + 8550 PNP from 3.3 V; R1 2 kΩ power LED; 50 MHz oscillator on 3.3 V, part unmarked | SCH |
| 10 | AMS1117 values: dropout 1.1/1.3 V, Iq 5/10 mA, current limit 0.9/1.1/1.5 A, Vin abs max 15 V, θJA 90 °C/W (46 to >90); no fixed 1.2 V in the AMS ordering table | AMS p1–p3 (page numbers corrected) |
| 11 | INA226: ±81.92 mV (table min is −81.9175), 2.5 µV LSB, 0–36 V bus, 1.25 mV LSB, Vos ±2.5/±10 µV, gain error 0.02/0.1 %, VS 2.7–5.5 V, IQ 330/420 µA, CMRR ≥ 126 dB, VBUS 830 kΩ, CT 140 µs–8.244 ms, AVG 1…1024, CAL = 0.00512/(Current_LSB·R), Power_LSB = 25·Current_LSB, abs max common-mode/VBUS −0.3 to 40 V, A1 = A0 = GND → 1000000b = 0x40 (16 addresses) | TI SBOS547C §5.1, §5.5, §6.5, Tables 6-2 and 7-3 |
| 12 | INA219 comparison values (PGA ranges, 10 µV and 4 mV LSBs, 12-bit, 26 V, Vos ±10/±100 µV A-grade at /1) | TI SBOS448G, EC table |
| 13 | Module pin labels IN+, IN−, VBS, ALE, SCL, SDA, GND, VCC; VBUS is a separate pin; "Connect the VBus pin to Vin- pin"; A0/A1 10 kΩ pull-downs (one user's DMM reading) | ARDF post 1/3; H2E |
| 14 | Arithmetic: 0.819 A full scale; 25 µA LSB; CAL 2048; 625 µW power LSB; ±100 µA offset; 12.5 mV/1.6 mW, 29 mV/8.4 mW, 82 mV/67 mW; 0.2 Ω → 0.41 A and 0.05 Ω → 1.64 A; 141 ms update; current-table sums 67.35/124.85/290.55 mA; 5/1.2 = 4.2× | recomputed |
| 15 | QPOW typical-silicon figures: Tj 25 °C VCCINT 19.15 / VCCIO 6.80 / VCCA 15.47 / VCCD 1.00 mA (83.51 mW); Tj 65 °C 20.74/6.80/16.40/1.03; Tj 85 °C 22.21/6.80/16.98/1.05. Δ at the input = +2.55 (65 °C) and +4.62 mA (85 °C), i.e. 185 LSBs | re-run this session (QPOW) |
| 16 | SDRAM IDD2PS 2, IDD2NS 15, IDD3N 40, IDD1/IDD4 100–120, IDD5 150–170 mA; MAX3232 ICC 0.3/1 mA; EPCS ICC0 50 µA, ICC1 5–14 mA | SDRAM p9; MAX3232 p3; EPCS p35 Table 14–22 |
| 17 | SOT-223-style regulators, tantalum-looking C2/C4/C8, test pads "GND 3.?V 5V … 1.2V" | MAN p1 photo (photo-estimate, as tagged) |

**Corrected in place**

1. **Minimum board input**: changed from ≈ 4.6 V (labelled "conservative") to **4.75 V**, the datasheet's specified input floor for the 1117-3.3 (AMS p2). The brown-out margin goes from 0.4 V to **0.25 V** in the facts table, §1, §3, red flag 7 and must-measure 5.
2. **Low-side shunt verdict**: changed from "will not work" to "fragile / can read wrong". With a floating Class II adapter, the shunt is the only DC return path to the adapter's negative, so the bypass needs a second path from that negative to host ground. The high-side recommendation is unchanged.
3. **5 V users**: the original said "only" the power LED, PS/2 and headers. The LCD connector (pins 2, 15, 17, 19) and an always-on contrast divider (≈ 0.45 mA) are also on 5 V.
4. **AMS page citations**: dropout, quiescent current and current limit are on p3, not p2.
5. **Shunt source**: "R100 = 0.1 Ω" was attributed to the Arduino-forum thread, which does not mention it. It is replaced with a shop listing (USOL) and marked UNVERIFIED for the CJMCU-226 itself.
6. **"Survives a 12 V mis-plug for a while"**: marked UNVERIFIED. The derived thermal estimate says it would not survive in a 60 °C box.
7. **CMRR wording**: the 0–36 V common-mode range is what lets the INA226 sit at 5 V; CMRR sets the error.
8. **Added**: worst-case-silicon power (QPOW-MAX). The leakage signal from 25 to 85 °C is +4.6 to +19.2 mA depending on silicon, and the high current case is ≈ 320 mA. Neither changes the 0.1 Ω or INA226 verdicts.
9. **Keying note**: the 2.5 mm / 2.1 mm keying blocks only the dangerous direction.
10. **Heater power**: 14.4 W at 12 V / 10 Ω is noted for the heater report.

**Still unverified (needs Alex's hands)**

- DC jack outer and inner diameter, and actual polarity (continuity test as in must-measure 1 and 2).
- Who makes U1/U2/U3 and their ratings. Every AMS-derived number assumes AMS parts.
- The 50 MHz oscillator part and its current; the LM75, AT24C08 and IR-receiver currents (placeholders in §2).
- Whether RW/R29 (LCD contrast) are populated.
- The CJMCU-226 shunt value, A0/A1 resistors, and SDA/SCL pull-ups (DMM on the actual module).
- Whether the chosen MOSFET module ties signal GND to power GND.
- Real board current and the 5 V pad voltage under load. Everything in §2 is an estimate until measured.
- The QPOW figures are vectorless estimates that Quartus itself rates "Low" confidence.
