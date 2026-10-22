# Clock-capable pins on the OMDAZZ board: does the Si5351 stay?

Researched 2026-10-23 for the Agent Lab Box brief (`docs/lab-box/BRIEF.md` §3 item 7, §9 Q3).

## TL;DR

1. **Yes, there is a free clock pin.** FPGA **PIN_24 = CLK2 (DIFFCLK_1p)** is a dedicated clock input that feeds the global clock network and **PLL_1**. In the V2.1 schematic it goes to **header P1, pin 34** and to nothing else. **The Si5351 stays in the MVP**, as long as a continuity check on the real V3.0 board confirms this (the schematic is V2.1).
2. The other six clock pins are not usable. PIN_23 (CLK1) is the 50 MHz oscillator. PIN_25 (CLK3) is RESET, with a 100 nF capacitor to GND. PIN_88–91 (CLK7–CLK4) are KEY1–4 and the DIP switch: they do reach header P3 (pins 7–10), but turning a DIP switch ON shorts the line straight to GND, and pressing a key pulls it to GND through 220 Ω. *(Corrected by verifier: P3 pins were wrongly given as 5–8, and a key press goes through 220 Ω, not a direct short.)* **CLK0 does not exist on the EP4CE6.**
3. **The logic levels match.** The Adafruit Si5351 board runs its outputs from 3.3 V: high ≥ 2.7 V and low ≤ 0.6 V (at 5 pF). The FPGA input (3.3-V LVTTL) needs high ≥ 1.7 V and low ≤ 0.8 V. The low-side margin is only **0.2 V**, so keep the lead short and the ground solid.
4. **Physical hazard:** P1-34 sits next to **3.3 V (P1-35/36)** and **5 V (P1-37/38)**. P1's only GND pins are P1-1/2 at the far end. Use a keyed, labelled connector and run a separate ground wire.
5. The **on-chip PLL alone is also a workable clock knob.** Its C8 limits are: input 5–472.5 MHz, VCO 600–1300 MHz, output ≤ 402.5 MHz. From 50 MHz it can reach frequencies about 17 kHz apart near 72 MHz (median step; derived). But every frequency step needs either a recompile or runtime PLL-reconfiguration logic. The Si5351 needs neither.

## Facts

Sources, abbreviated (paths relative to `resources/Altera-Cyclone-IV-board-V3.0 documentation/`):
**PIN** = `Cyclone IV chip/EP4CE6 pin information.pdf` (Altera PT-EP4CE6-1.2) ·
**HB** = `Cyclone IV chip/Cyclone IV Handbook.pdf` (Vol 1 ch. 5 is CYIV-51005-2.4; page numbers below are PDF pages) ·
**DS** = `Cyclone IV chip/Cyclone IV Datasheet.pdf` (CYIV-53001-1.7, May 2013) ·
**PCG** = `Cyclone IV chip/Cyclone IV pin connection design guide.pdf` (PCG-01008-1.4) ·
**SCH** = `Hardware documentation/Development board schematic diagram V2.1.pdf` (one sheet; the named block is given) ·
**TBL** = `Hardware documentation/Development board pin information.pdf` (+ `.xls`) ·
**SI** = Skyworks Si5351A/B/C-B datasheet Rev 1.3, 27 Aug 2021 (fetched from https://cdn.components.ru/media/PDF/461362.pdf; this is the same document Adafruit links at https://cdn-learn.adafruit.com/assets/assets/000/116/463/original/Si5351-B_datasheet.pdf) ·
**ADA** = Adafruit Si5351A guide https://learn.adafruit.com/adafruit-si5351-clock-generator-breakout (pages `/pinouts` and `/downloads`) and its original-breakout schematic image (Rev B, 2014) https://cdn-learn.adafruit.com/assets/assets/000/018/765/medium800/adafruit_products_schem.png

| Item | Value | Unit | Source | Confidence | Notes |
|---|---|---|---|---|---|
| CLK1 (DIFFCLK_0n) | E144 pin 23, bank B1 | pin | PIN p.1 | datasheet | Its p-partner DIFFCLK_0p is absent, so CLK1 is single-ended only (PIN note 1, p.6) |
| CLK2 (DIFFCLK_1p) | pin 24, bank B2 | pin | PIN p.1 | datasheet | **The free one** |
| CLK3 (DIFFCLK_1n) | pin 25, bank B2 | pin | PIN p.1 | datasheet | |
| CLK4 (DIFFCLK_2p) | pin 91, bank B6 | pin | PIN p.3 | datasheet | |
| CLK5 (DIFFCLK_2n) | pin 90, bank B6 | pin | PIN p.3 | datasheet | |
| CLK6 (DIFFCLK_3p) | pin 89, bank B5 | pin | PIN p.3 | datasheet | |
| CLK7 (DIFFCLK_3n) | pin 88, bank B5 | pin | PIN p.3 | datasheet | |
| CLK0 | not present on EP4CE6 | — | PIN p.1 (no row); HB p.63 ("CLK[15..1]"), p.73 note 6 | datasheet | E144 pin 22 is GND (PIN p.5) |
| Dedicated clock pins on E144 | 7 (3 on the left side, 4 on the right) | count | HB p.63 | datasheet | "EP4CE6 and EP4CE10 … three … on the left side and four … on the right side" |
| PLLs in EP4CE6 | PLL_1, PLL_2 | — | HB p.71, Table 5–3 note 3 | datasheet | |
| GCLK networks in EP4CE6 | 10 (GCLK 0–9) | count | HB p.71, Table 5–3 note 1 | datasheet | |
| Clock pin → PLL | CLK1–3 → PLL_1; CLK4–7 → PLL_2 | — | HB p.76 Fig 5–4; p.83 Fig 5–10 note 1 | datasheet | "any of the four clock pins located on the same side of the device as the PLL" |
| PLL1_CLKOUTp / n | pin 43 / 44 (bank B3) | pin | PIN p.2 | datasheet | Output pins, not inputs |
| PLL2_CLKOUTn / p | pin 112 / 113 (bank B7) | pin | PIN p.4 | datasheet | Output pins, not inputs |
| DPCLK pins (can reach GCLK, cannot feed a PLL) | 10, 30, 42, 68, 85, 104, 110, 142 | pin | PIN p.1–5; HB p.72 Table 5–4 | datasheet | |
| Board: PIN_23 | 50 MHz oscillator, CLKout through R3 = 33 Ω, net FPGA_CLK | — | SCH "Crystal and reset" + U5I; TBL p.1 | vendor-doc | Cannot be overdriven |
| Board: PIN_25 | RESET: R2 10 kΩ pull-up to 3.3 V, **C10 100 nF to GND**, push button to GND | — | SCH "Crystal and reset" + U5I; TBL p.1 | vendor-doc | Capacitor makes it useless as a clock (see derived row) |
| Board: PIN_24 | net "24" → **P1 pin 34**; no other connection | — | SCH U5I + "IO interface" P1 | vendor-doc | Pin table (PDF and .xls string table) has no entry for pin 24 |
| Board: PIN_88/89/90/91 | KEY1/KEY2/KEY3/KEY4 = CLK7/6/5/4; also on **P3 pins 7/8/9/10** (corrected; was "5/6/7/8") | — | SCH "Button, LED, DIP switch" + P3; TBL p.1 | vendor-doc | 220 Ω (R34–37) → node with 10 kΩ pull-up (R38–41) + button to GND. P3-3/4/5/6 are LED1–4 (FPGA 84/85/86/87), P3-1/2 GND, P3-19 5 V, P3-20 3.3 V |
| Board: DIP switch on KEY1–4 | SW pins 5–8 on KEY1–4 nets; SW pins 1–4 to GND; extra 10 kΩ pull-ups R42–45 | — | SCH "Button, LED, DIP switch"; TBL p.1 ("Dial switch ckey1–4 = 88–91") | vendor-doc | Switch ON = that KEY net shorted straight to GND |
| DIP switch fitted on V3.0? | red 4-way DIP visible in vendor photo | — | `board.jpg` | photo-estimate | Check Alex's board |
| Board: PIN_43 / 44 | SDRAM CLK / SDRAM DQ15; also P2 pins 35 / 34 | — | TBL p.3; SCH P2 | vendor-doc | |
| Board: PIN_112 / 113 | SCL / SDA of **LM75 temperature sensor U9**, 5.1 kΩ pull-ups R27/R28; also P1 pins 5 / 6 | — | SCH "Temperature Sensor"; TBL p.1 ("IIC") | vendor-doc | Side finding: the board already has an I²C temperature sensor, read by the FPGA |
| P1 pins next to P1-34 | 33 = FPGA pin 11 (LCD11); 32 = FPGA pin 10 (LCD9, DPCLK0); **35/36 = 3.3 V; 37/38 = 5 V; GND only at 1/2** | — | SCH "IO interface" P1 (Header 19×2) | vendor-doc | |
| VCCIO, all banks (incl. B2) | 3.3 | V | SCH U5K | vendor-doc | |
| I/O standard used in this repo | "3.3-V LVTTL" | — | `projects/demo/demo.qsf` line 65 | vendor-doc | Repo file, not a vendor file; tagged vendor-doc as the nearest fit |
| Unused-pin setting in this repo | RESERVE_ALL_UNUSED_PINS "AS INPUT TRI-STATED" | — | `projects/demo/demo.qsf` l.22; `projects/mnist/mnist.qsf` l.13 | vendor-doc | Repo files. Keeps PIN_24 high-impedance while unused |
| 3.3-V LVTTL input levels | VIL ≤ 0.8; VIH ≥ 1.7 (max 3.6); VCCIO 3.135–3.465 | V | DS Table 1–15, p.12 | datasheet | |
| DC input absolute max | −0.5 to 4.2 | V | DS Table 1–1, p.2 | datasheet | Overshoot to 4.3 V allowed for 65 % of high time (10-year lifetime), DS Table 1–2 p.3 |
| Clock-pin input capacitance | 6 (typical, QFP, "right" clock pins) | pF | DS Table 1–11, p.10 | datasheet | The table gives no separate left-side figure |
| PLL fIN (−8 grade) | 5 – 472.5 | MHz | DS Table 1–25, p.24 | datasheet | |
| PLL fINPFD | 5 – 325 | MHz | DS Table 1–25, p.24 | datasheet | |
| PLL fVCO | 600 – 1300 | MHz | DS Table 1–25, p.24 | datasheet | |
| PLL input duty cycle | 40 – 60 | % | DS Table 1–25, p.24 | datasheet | |
| PLL input jitter tolerance (FREF < 100 MHz) | ±750 | ps | DS Table 1–25, p.24 | datasheet | Note 5: for low output jitter, feed it < 200 ps |
| PLL fOUT to GCLK (−8 grade) | ≤ 402.5 | MHz | DS Table 1–25, p.24 | datasheet | fOUT_EXT ≤ 472.5 MHz, also limited by the I/O standard |
| PLL lock time (after config / after reconfig) | ≤ 1 / ≤ 1 | ms | DS Table 1–25, p.24–25 | datasheet | tLOCK / tDLOCK |
| PLL M, N, C counters | 1 – 512 (C 1–256 if duty ≠ 50 %) | — | HB p.81 Table 5–6 (duty-cycle note 1 is on p.82) | datasheet | 5 C outputs; user-mode reconfiguration supported; phase-shift steps down to 96 ps |
| PLL scanclk (for reconfiguration) | ≤ 100 | MHz | DS Table 1–25, p.25 | datasheet | |
| GCLK tree fmax, EP4CE6 C8 | 402 | MHz | DS Table 1–24, p.23 | datasheet | |
| Reference design Fmax | 72.37 (period 13.818 ns) | MHz | `docs/lab-box/BRIEF.md` l.40 (72.37 only); period derived = 1000/72.37 | unknown | Taken from the brief; not checked against a timing report here. The brief does not state the period |
| Si5351A output frequency | 0.0025 – 200 | MHz | SI Table 7, p.10 | datasheet | Only two distinct frequencies above 112.5 MHz at a time |
| Adafruit's stated range | "<8 KHz up to 150+ MHz" (product title: "8KHz to 160MHz") | — | ADA overview | listing | |
| Si5351 VOH / VOL | ≥ VDD − 0.6 / ≤ 0.6 (CL = 5 pF) | V | SI Table 7, p.10 | datasheet | |
| Si5351 rise/fall (20–80 %, 5 pF) | 1 typ / 1.5 max | ns | SI Table 7, p.10 | datasheet | |
| Si5351 duty cycle (≤ 160 MHz) | 45 – 55 | % | SI Table 7, p.10 | datasheet | Within the PLL's 40–60 % |
| Si5351 period jitter (10-MSOP, all outputs on) | 70 typ / 155 max | ps pk-pk | SI Table 7, p.10 | datasheet | Cycle-to-cycle: 70 typ / 150 max ps |
| Si5351 max load | 15 | pF | SI Table 7, p.10 | datasheet | |
| Si5351 output impedance (3.3 V VDDO, default high drive) | 50 | Ω | SI Table 4, p.8 | datasheet | |
| Si5351 VDDO options | 1.71–1.89 / 2.25–2.75 / 3.0–3.60 | V | SI Table 3, p.8 | datasheet | |
| Si5351 frequency-change time | ≤ 10 | µs | SI Table 5, p.9 | datasheet | Front page: "Glitchless frequency changes" |
| Si5351 I²C address | 0x60 | — | SI p.18 | datasheet | |
| Adafruit 2045: VDDO | tied to VDD = 3.3 V LDO output | — | ADA schematic image | listing | Read from an 800-px schematic image |
| Adafruit 2045: output network | CLK0/1/2 go straight to header JP1 pins 7/6/5 and to SMA pads; no series resistor visible | — | ADA schematic image | listing | JP1: 1 VIN, 2 GND, 3 SDA, 4 SCL, 5 CLK2, 6 CLK1, 7 CLK0 (only one GND) |
| Adafruit 2045: output swing | "square waves, from 0-3V" | V | ADA `/pinouts` | listing | |
| High-side margin (Si5351 → FPGA) | 2.7 − 1.7 = **1.0** (nominal VDDO 3.3); 2.4 − 1.7 = 0.7 (VDDO 3.0 min) | V | derived (SI Table 7, DS Table 1–15) | derived | SI Table 7 references VOH to **VDD** (core), not VDDO; on the Adafruit board VDD and VDDO are the same node, so the numbers stand |
| Low-side margin | 0.8 − 0.6 = **0.2** | V | derived | derived | Thin. Ground bounce on a long return path uses it up |
| Load budget left for wiring | 15 − 6 = 9 | pF | derived (SI Table 7, DS Table 1–11) | derived | Keep the lead short |
| C10 impedance at 72 MHz | 1/(2π·72e6·100e-9) = 0.022 | Ω | derived | derived | A short to GND at clock frequencies. RC = 10 kΩ × 100 nF = 1 ms |
| P1-34 to nearest GND (P1-1/2) | 16 rows × 2.54 = 40.6 | mm | derived | derived | Assumes 2.54 mm pitch, which is **not stated in any vendor doc**: measure |
| PLL frequency grid from 50 MHz, 70–75 MHz | 261 distinct values; median gap 17.4 kHz; max gap 163.4 kHz | — | derived (script below; DS Table 1–25 + HB Table 5–6 limits) | derived | Ideal counter arithmetic. Quartus's loop-filter rules may exclude some (unverified) |

## 1. The clock pins and where each one goes

| Clock pin | Pkg pin | Bank | Feeds | On the board | On a header? | Usable for Si5351 without a mod? |
|---|---|---|---|---|---|---|
| CLK1 | 23 | B1 | PLL_1, GCLK | 50 MHz oscillator via 33 Ω | no | **No.** It would fight the oscillator |
| **CLK2** | **24** | **B2** | **PLL_1, GCLK** | **nothing** | **P1-34** | **Yes** |
| CLK3 | 25 | B2 | PLL_1, GCLK | RESET: 10 kΩ pull-up, 100 nF to GND, button | no | **No.** 100 nF ≈ 0.02 Ω at 72 MHz |
| CLK4 | 91 | B6 | PLL_2, GCLK | KEY4 + DIP 4 | P3-10 *(corrected from P3-8)* | Only with the DIP switch OFF and the key never pressed; 2 × 10 kΩ pull-ups load it |
| CLK5 | 90 | B6 | PLL_2, GCLK | KEY3 + DIP 3 | P3-9 *(corrected from P3-7)* | same |
| CLK6 | 89 | B5 | PLL_2, GCLK | KEY2 + DIP 2 | P3-8 *(corrected from P3-6)* | same |
| CLK7 | 88 | B5 | PLL_2, GCLK | KEY1 + DIP 1 | P3-7 *(corrected from P3-5)* | same |

The vendor left CLK2 unconnected and routed it to P1 pin 34. P1 pin 34 is one of only two FPGA pins on P1 with no peripheral attached (SCH "IO interface"). The other is P1-4 = FPGA pin 111, a regular I/O that is not clock-capable. *(Corrected by verifier: the original said P1-34 was the only one.)* Altera's pin guideline says to tie unused CLK pins to GND (PCG p.2). The board doesn't, so the pin floats while nothing is plugged into it. That is harmless with the repo's "AS INPUT TRI-STATED" setting.

The board uses the PLL output pins as follows. Pins 43/44 carry SDRAM CLK and DQ15. Pins 112/113 carry the LM75 temperature sensor's SCL and SDA. Both pairs are outputs, so neither matters for a clock *input*.

## 2. What a pin that is not a clock pin can and cannot do (option b, checked)

- **It cannot feed a PLL.** HB p.80: "The general I/O pins cannot drive the PLL clock input pins." HB p.72, Table 5–4: clock control blocks driven by DPCLK pins or by internal logic "are not able to drive PLL inputs". HB p.83, Fig 5–10 note 3: "An internally generated global signal cannot drive the PLL."
- **It can drive the global clock network.** HB p.72, Table 5–4: "internal logic … can all feed the clock control block for each GCLK". A regular I/O reaches the clock control block through ordinary routing. That adds routing delay and makes the clock arrival less predictable, which the PLL normally compensates for (HB p.85: "Input and output delays are fully compensated by the PLL only if you are using the dedicated clock input pins"). DPCLK pins have a direct path into the clock control block. On P1 these are FPGA pin 10 (P1-32, LCD9), pin 142 (P1-25, LCD4) and pin 110 (P1-3, BEEP, which drives the buzzer transistor).
- Which warnings Quartus prints for these setups was **not tested** this session.

## 3. Verdict and options

**Keep the Si5351. Wire it to P1-34 = PIN_24 = CLK2.** This needs no board modification. It is a dedicated clock pin, so the Si5351 can either:
- drive the global clock network directly. This is the simplest choice for a shmoo: the test logic runs straight off the Si5351, and nothing on the FPGA has to re-lock. Or
- feed PLL_1, which is fully compensated (CLK2 is on the left side, the same side as PLL_1).

Clock pins 1–3 all reach PLL_1, so PLL_1 can take the 50 MHz oscillator (CLK1) and the Si5351 (CLK2) as its two inputs. **UNVERIFIED:** the handbook says each PLL input can come from any clock pin on the same side (HB p.83 Fig 5–10 note 1), but Figure 5–1 does not show legibly which pins can go to inclk0 and which to inclk1, and this pairing was not tried in Quartus. It does not affect the simpler direct-to-GCLK option.

The options the brief asked about:
- **(a) Drop the Si5351 and sweep with the on-chip PLL.** This works: the grid is dense (median step ~17 kHz near 72 MHz, derived). Two costs:
  - Each step needs either a recompile and reprogram (~22–115 s per build with this repo's backends, CLAUDE.md Art. V) or runtime reconfiguration logic (scan-chain reconfiguration, then up to 1 ms to re-lock).
  - The frequency is generated on the same die being heated. It stays locked to the 50 MHz oscillator, but that oscillator also sits on the heated board.
  
  Keep this as the **fallback** if the continuity check fails, and as a second, independent knob.
- **(b) A regular I/O header pin.** Can drive the global clock network, cannot feed a PLL (§2). Not needed now.
- **(c) Board mod**, such as removing C10 to free CLK3, or cutting a key trace. Not needed, and out of scope.

**What the Si5351 adds over the PLL:** continuous frequency steps without a recompile ("0 ppm error" synthesis, SI p.1; ≤ 10 µs frequency change, SI Table 5). It also sits off-chip and outside the heat zone, so the agent's clock knob is independent of the chip under test.

**Caution:** changing the frequency can still glitch the clock. Have the test design take a reset after every frequency change before it records pass/fail. (This is a recommendation. Whether the change actually glitches is unverified.)

## 4. Electrical match: Si5351 (Adafruit 2045) → PIN_24 (3.3-V LVTTL)

- **Levels:** with VDDO = 3.3 V the levels fit: 1.0 V margin on the high side, 0.2 V on the low side (derived above). Assign `IO_STANDARD "3.3-V LVTTL"` to the pin, as the repo already does for its other pins.
- **Overshoot:** the Si5351 edges are fast (1 ns typical), and its board has no series resistor. Bank 2 is at 3.3 V and the FPGA's DC limit is 4.2 V. Ringing on a long, unterminated jumper could overshoot that. The Si5351's 50 Ω output impedance roughly matches 50 Ω coax, so the SMA output plus a short coax lead is the cleanest connection (the SMA connectors are optional parts that have to be soldered on). The board's own oscillator uses a 33 Ω series resistor (R3), and the same idea is a reasonable fallback for a plain wire. Both are recommendations, not measured.
- **Ground:** the module header has one GND pin (JP1-2), not next to CLK0 (JP1-7). P1 has GND only at pins 1/2, about 40 mm (derived) from pin 34. Run a dedicated ground wire from the Si5351 GND to P1-1/2, or to a nearer GND point on the board, kept close to the signal wire.
- **Contention:** whatever design is loaded in the FPGA must never drive PIN_24. The repo's projects tri-state unused pins (demo.qsf l.22, mnist.qsf l.13). **It is unknown what the design in configuration flash does with pin 24 at power-up.** Until that is checked, have the Pico keep the Si5351 outputs disabled until the SRAM-loaded design is running.
- **Duty cycle and jitter, if it feeds PLL_1:** 45–55 % duty is inside the PLL's 40–60 %. 150 ps max cycle-to-cycle jitter is inside the ±750 ps tolerance and under the 200 ps the datasheet advises.

## 5. PLL range for the shmoo (alternative or second knob)

C8 limits (DS Table 1–25): fIN 5–472.5 MHz; PFD 5–325 MHz; VCO 600–1300 MHz; output to the global clock ≤ 402.5 MHz. The global clock tree itself is good to 402 MHz on EP4CE6 C8 (Table 1–24). Both are far above the 60–85 MHz shmoo window, so the window is limited only by the logic.

Output = 50 MHz × M / (N × C). Examples with the VCO kept in range (derived):

| Target | N | M | C | VCO (MHz) | Output (MHz) |
|---|---|---|---|---|---|
| 60.000 | 1 | 12 | 10 | 600 | 60.000 |
| 70.000 | 1 | 14 | 10 | 700 | 70.000 |
| 72.000 | 5 | 72 | 10 | 720 | 72.000 |
| 72.37 → | 7 | 152 | 15 | 1085.71 | 72.381 (11 kHz off) |
| 75.000 | 1 | 12 | 8 | 600 | 75.000 |
| 80.000 | 1 | 16 | 10 | 800 | 80.000 |

Method: enumerate N, M, C from 1 to 512 with the PFD and VCO limits applied. The script was a scratch file, not kept in the repo.

## 6. What Alex must measure or verify on the real board

1. **Find P1 and its pin 1** on the V3.0 board: the silkscreen label, the square pad or triangle marker, and which header in `board.jpg` it is. Measure where P1-34 sits relative to the board edge he will use as the reference, for the cable-exit design.
2. **Continuity, board unpowered:** P1-34 ↔ FPGA package pin 24 (on the pins-1-to-36 edge; count from the pin-1 dot) should beep. P1-34 ↔ GND and P1-34 ↔ 3.3 V should read open (the schematic shows no pull resistor). This confirms the V2.1 schematic matches the V3.0 board.
3. **Header pitch and pin height** with calipers. The 2.54 mm pitch is assumed, not documented.
4. **Whether the DIP switch is fitted, and its positions.** This only matters if P3 (CLK4–7) is ever used.
5. **The Si5351 module's VDDO:** measure the module's 3.3 V rail with a multimeter. Clone modules may differ from the Adafruit board; this report assumes the **Adafruit 2045** (original, with 3 SMA pads).
6. **What the flash image does with pin 24.** Check the `.pin` report of whatever design is in flash, or keep the Si5351 outputs disabled until a known design is loaded over JTAG.
7. **A test that cannot pass by accident** (Article IV): a design that counts PIN_24 edges against the 50 MHz reference and reports the ratio over JTAG.
   - Command an unusual frequency (e.g. 12.345 MHz, then 31.416 MHz). The reported value must follow each command.
   - With the Si5351 output disabled, the count must be **0**.
   - A floating or miswired pin cannot follow commanded odd frequencies.
   
   The counter is RTL, so it is Alex's to write (Article I).

## 7. Side findings

- The board has an **LM75 temperature sensor** (U9) on FPGA pins 112/113 and an AT24C08 EEPROM on pins 98/99 (SCH). Whether the LM75 is fitted on V3.0 is unverified. If it is, the FPGA can read a board temperature itself, which gives the box another reading for free.
- All P2 header pins are shared with the SDRAM (TBL p.3; SCH P2). If the logic analyser goes on P2, the design must keep the SDRAM deselected (pin 72, SD CS). That is a separate topic.

## Verification (adversarial pass)

Done 2026-10-23 by a second agent that re-derived each claim from the primary file, not from the report. Schematic crops were rendered from the vector PDF at 500–1400 dpi with pymupdf. The net-label search used the PDF's own text layer.

**Checked and confirmed (32 claims):**

- **Clock pin numbers** (PIN p.1, p.3, extracted rows): CLK1 = 23 (B1, DIFFCLK_0n), CLK2 = 24 and CLK3 = 25 (B2), CLK7/6 = 88/89 (B5), CLK5/4 = 90/91 (B6).
- **No CLK0 anywhere in the EP4CE6 pin list.** Pin 22 is GND (p.5). Note 1, p.6 is quoted correctly.
- **PLL output pins:** PLL1_CLKOUTp/n = 43/44 and PLL2_CLKOUTn/p = 112/113.
- **DPCLK pins:** 10, 30, 42, 68, 85, 104, 110, 142.
- **Handbook clock topology:**
  - HB p.63: 3 + 4 clock pins on EP4CE6.
  - p.71: GCLK 0–9, PLL_1/PLL_2 only.
  - p.76 Fig 5–4: CLK[3..1] feed PLL_1 on a solid (compensated) path; CLK[7..4] feed PLL_2.
  - p.80: "The general I/O pins cannot drive the PLL clock input pins."
  - p.72 Table 5–4: DPCLK- and internal-logic-driven clock control blocks "are not able to drive PLL inputs".
  - p.83 Fig 5–10 note 3.
  - The p.85 compensation quote.
  - All verbatim.
- **Datasheet:**
  - Table 1–15, p.12: 3.3-V LVTTL VIL ≤ 0.8, VIH ≥ 1.7, VIH max 3.6, VCCIO 3.135–3.465.
  - Table 1–1, p.2: VI −0.5 to 4.2 V.
  - Table 1–2, p.3: 4.30 V for 65 %.
  - Table 1–11, p.10: CCLKLR = 6 pF QFP. The table's "right" wording is as the author said.
  - Table 1–24, p.23: EP4CE6 C8 = 402 MHz.
  - Table 1–25, pp.24–25: every PLL number in the facts table (fIN, fINPFD, fVCO, duty, ±750 ps, fOUT 402.5, fOUT_EXT 472.5, tLOCK, tDLOCK, scanclk 100 MHz, note 5's 200 ps).
- **Board, V2.1 schematic:**
  - "Crystal and reset": R3 = 33 Ω, 50 MHz CLKout to FPGA_CLK, R2 10k to 3.3 V, C10 marked "104" (= 100 nF), and a button to GND.
  - U5I: pin 23 → FPGA_CLK, pin 24 → net "24", pin 25 → RESET.
  - The net label "24" appears **only** at U5I and at P1. The other "24" strings are SDRAM and P2 pin numbers.
  - P1-34 = 24, P1-35/36 = 3.3 V, P1-37/38 = 5 V, GND only at P1-1/2. P1-32 = 10, P1-33 = 11, P1-25 = 142, P1-3 = 110 (BEEP), P1-5/6 = 112 SCL / 113 SDA.
  - U5K: every VCCIO pin tied to 3.3 V.
  - LM75 U9 sits on SDA/SCL with 5.1 kΩ R27/R28. AT24C08 sits on I2C_SCL/I2C_SDA (pin table: 99/98).
  - P2-35/34 = FPGA 43/44.
  - DIP: SW 1–4 go to GND, SW 8/7/6/5 go to KEY1–4, with R42–45 10k pull-ups.
- **Independent corroboration of P1-34 = FPGA 24:** `Hardware documentation/expansion board schematics.pdf` (the mating board) also labels P1 pin 34 as "24".
- **Pin table** (PDF, all 3 pages): no entry for pin 24 (and none for 111). SDRAM CLK = 43, DQ15 = 44. The .xls string table has no function name that maps to pin 24. Its numeric cells were not decoded.
- **Si5351 datasheet** (re-downloaded from the Adafruit CDN URL; Rev 1.3, 27 Aug 2021):
  - Table 7, p.10: 0.0025–200 MHz, CL ≤ 15 pF, duty 45–55 %, tr/tf 1/1.5 ns, VOH ≥ VDD−0.6, VOL ≤ 0.6, period jitter 70/155 ps, cycle-to-cycle jitter 70/150 ps for 10-MSOP.
  - Table 4, p.8: ZO = 50 Ω.
  - Table 3, p.8: the VDDO ranges.
  - Table 5, p.9: TFREQ ≤ 10 µs.
  - p.18: address 0x60.
  - p.1: "Glitchless frequency changes" and "0 ppm error".
- **Adafruit 2045:**
  - Product page title: "8KHz to 160MHz".
  - Guide: "<8KHz up to 150+ MHz", "square waves, from 0-3V", "3.3V LDO".
  - Full-resolution schematic (`.../original/adafruit_products_schem.png`): VDDO tied to VDD, JP1 = VIN, GND, SDA, SCL, CLK2, CLK1, CLK0, and no series resistors on CLK0–2.
- **Arithmetic:**
  - 1/(2π·72 MHz·100 nF) = 0.022 Ω. RC = 1 ms.
  - 16 rows × 2.54 = 40.6 mm.
  - Margins: 1.0 / 0.7 / 0.2 V.
  - 15 − 6 = 9 pF.
  - Every row of the §5 PLL example table.
  - The PLL grid, recomputed with an independent script (exact fractions, same limits): **261 distinct values in 70–75 MHz, median gap 17.43 kHz, max 163.40 kHz, closest to 72.37 = 72.381 MHz (N 7, M 152, C 15)**. All match.
  - The VCO post-scale counter K (÷2, HB p.83; DS Table 1–25 note 4) does not add values in this window, because ÷2·C is already reachable with C ≤ 512 (derived).
- **Repo:** `demo.qsf` l.22 and l.65 and `mnist.qsf` l.13 say what the report claims.

**Corrected:**

1. **KEY1–4 / CLK7–4 header pins: P3-7/8/9/10, not P3-5/6/7/8.** At high zoom, each net label sits just above its wire. P3-3/4/5/6 are LED1–4 (FPGA 84–87). Fixed in the facts table and in §1. This matters only if anyone ever clips onto P3, but it was a wrong pin number.
2. **A key press pulls the line to GND through 220 Ω (R34–37), not a dead short.** Only the DIP switch is a direct short. TL;DR item 2 is reworded.
3. **"P1-34 is the only FPGA pin on P1 with no peripheral"** is false. P1-4 = FPGA pin 111 also has nothing else on it in V2.1 (net "111" appears only at U5 and P1). It is not clock-capable, so the verdict does not change.
4. Small citation fixes: the 13.818 ns period is derived, not in the brief, and Table 5–6's duty-cycle note is on p.82.

**Marked UNVERIFIED:**

- That PLL_1 accepts CLK1 and CLK2 together as inclk0/inclk1. The handbook does not show the pairing legibly, and Quartus was not run.

**Still unverified (unchanged from the author, all correctly flagged):**

- The V3.0 board matches the V2.1 schematic on P1-34. **The continuity check in §6 item 2 is still the gate for buying the Si5351.**
- Header pitch: no vendor doc states 2.54 mm. Searched Dev Board Manual, schematic and expansion schematic.
- What the flash image does with pin 24.
- Quartus warnings for the I/O-to-GCLK path.
- Whether a Si5351 frequency change glitches the clock at the FPGA.
- Whether the LM75 and DIP switch are fitted on V3.0 (a red 4-way DIP switch is visible in the vendor `board.jpg`).

**New wiring and safety findings (the author did not cover these):**

- **Power the Si5351 breakout's VIN from the Pico's 3.3 V, not 5 V.**
  - Source: the Adafruit schematic (Rev B 2014, listing). The JP1 SDA/SCL pins are the *5 V side* of BSS138 level shifters, pulled up to **VIN** through 10 kΩ (R7/R8).
  - With VIN = 5 V, the Pico's I²C pins would be pulled up to 5 V. Whether the Pico's GPIO can tolerate that was **not checked here** (RP2040 vs RP2350 differ; see the Pico chip's datasheet absolute maximums). Powering VIN from 3.3 V avoids the question entirely.
  - The CLK outputs run from the on-board LDO (VDD = VDDO), so the clock level does not depend on VIN.
  - With VIN = 3.3 V, VDD sits below 3.3 V by the LDO's dropout. That was not checked. Measure it (§6 item 5): it must stay ≥ 3.0 V for the SI Table 3 "3.3 V" range.
- **The Si5351A 10-MSOP on this board has no OEB pin** (SI p.33 Table 20: the 10-MSOP pins are VDD, XA, XB, SCL, SDA, CLK2, VDDO, GND, CLK1, CLK0. OEB is on the 20-QFN, SI p.27 Table 14. The Adafruit schematic part is Si5351A-B-GT, a 10-MSOP). "Keep outputs disabled" therefore has to be done over I²C.
  - SI p.17 says a disabled output can be set to high, low or high-impedance. That statement is made for the OEB pin. The matching register bits (AN619) were not checked here.
  - Choose high-impedance or low while the FPGA's pin-24 behaviour is unknown.
