# Agent Lab Box MVP: wiring

> Pin-level wiring for `cad/lab-box/DESIGN.md` v0.1 (§9 bold defaults). Written 2026-10-23.
> **Nothing here has been wired or tested. Every pin assignment is a plan, not a measurement.**
> Parts are the ones in `BOM.md`.

**Sources** (short names): [M] = `research/modules-electronics.md` · [P] =
`research/board-power.md` · [C] = `research/clock-pins.md` · [T] = `research/thermal-safety.md`
· [S] = `research/suppliers-au.md` · [D] = `cad/lab-box/DESIGN.md`. Verifier corrections at the
end of each research file override its body, and they were applied here.

---

## WARNING: 3.3 V only. Read this before connecting anything to the Pico

- **The RP2040 is not 5 V tolerant.** No pin may go above IOVDD + 0.5 V = 3.8 V [M row "RP2040
  pin voltage max"]. The Pico 2 (RP2350) is 5 V tolerant on most pins, but **not** on GP26–28
  [M verifier]. Design to the RP2040 rule anyway, so either board works.
- **Power every module's VIN/VCC from the Pico's 3V3(OUT), physical pin 36.** Never from 5 V.
  *Why:* the Adafruit boards pull SDA/SCL up to **their VIN pin** [M TL;DR 5; C verifier]. Give
  them 5 V and the Pico's I²C pins sit at 5 V through those pull-ups. The 3V3(OUT) budget is
  < 300 mA [M], far more than these modules need.
- **Never power anything from the FPGA board's header 5 V or 3.3 V pins** (P1-35..38, P2-1..4,
  P3-19/20). *Why:* that current flows through the INA226 and gets counted as "board power" [P §3].
- A fan tach line (only if §9.4 goes to a 12 V fan) must be pulled up to **3.3 V**, never 5 V
  or 12 V. Measure the tach wire's open-circuit voltage first [S verifier; M].

---

## 1. Overview diagram

```
                     HOST PC (Mac / Windows)
          ┌──────────────┬───────────────┬──────────────────┐
       USB│           USB│            USB│
          ▼              ▼               ▼
     USB-Blaster      Pico 2 H       Logic analyser
     (inside box,     (box brain)    CH0-7 ──► reserved P1/P2 pins
      IDC on JTAG)       │            GND  ──► P2-6
          │              │
          ▼              │ 3V3(OUT) pin 36 ──► VIN of INA226, BME280, MAX31855, Si5351
   FPGA board JTAG       │ VBUS pin 40 ─────► 5 V fan (+)
                         │ I2C0 GP4/GP5 ────► INA226 0x40 · Si5351 0x60 · BME280 0x77
                         │ SPI0 GP16/17/18 ─► MAX31855 ◄── thermocouple in spreader groove
                         │ GP22 (PWM3 A) ───► heater opto-MOSFET module (signal side)
                         │ GP14 (PWM7 A) ───► fan MOSFET gate
                         │ GP20 (opt.) ─────► 5 V load switch EN
                         │ GND ─────────────► STAR GROUND
                         │
   ── FPGA 5 V domain (metered) ──────────────────────────────────────────────────
   USB-C charger ─► USB-C breakout VBUS ─► INA226 IN+ ─[0.1 Ω]─ IN− ─┬─► [load switch, opt.] ─► pigtail + ─► board DC jack (centre)
                    USB-C breakout GND  ──────────────────────────────┼───────────────────────► pigtail − ─► board DC jack (sleeve)
                                                       INA226 VBUS ◄──┘   (never via the star)
   ── Heater 12 V domain (isolated) ──────────────────────────────────────────────
   12 V plug pack ─► panel jack + ─► FUSE 1 A ─┬─► KSD9700 75 °C ─► HS10 18 Ω ─► module LOAD
                                               └─► module "+" (gate supply)
                     panel jack − ◄────────────── module "−"   (heavy wire, straight back)
   ── Clock ──────────────────────────────────────────────────────────────────────
   Si5351 CLK0 ═══ twisted pair ≤ 60 mm ═══► P1-34 (FPGA PIN_24 = CLK2)
   Si5351 GND  ═══                     ═══► P1-1 / P1-2 (GND)

   STAR GROUND (module plate): Pico GND · INA226 GND · BME280 GND · MAX31855 GND · Si5351 GND
               · heater module SIGNAL GND · fan MOSFET source · ONE thin wire ─► P2-5 (GND)
```

## 2. Power domains

There are four separate power sources. *Why separate:* each current should come back to its own
source on its own wires. Then the heater's 0.7 A never flows through a ground wire that the
INA226 or a logic signal shares [P §4].

| Domain | Source | Feeds | Return path |
|---|---|---|---|
| **FPGA 5 V (metered)** | 2-prong USB-C charger, ≥ 1 A → USB-C breakout (5.1 kΩ CC pull-downs) [D 3.4.18] | Whole FPGA board, via INA226 and its DC jack | Breakout GND → pigtail sleeve → board jack. **Not** through the star |
| **Heater 12 V** | 2-prong 12 V 2 A plug pack → panel jack | Fuse → thermostat → heater → MOSFET | Module "−" → panel jack − directly |
| **Pico + logic** | Host USB → Pico micro-USB | Pico; 3V3(OUT) → all modules; VBUS → fan | Pico GND → star |
| **Logic analyser, USB-Blaster** | Host USB | themselves | via host USB ground |

### 2.1 FPGA 5 V, step by step

| From | To | Wire | Why |
|---|---|---|---|
| USB-C breakout VBUS | INA226 **IN+** | 22 AWG | 5 V goes in on the high side |
| INA226 **IN−** | INA226 **VBUS** pin | short jumper | The module brings VBUS out as a separate pin. Left open, the voltage and power readings are meaningless [P red flag 4] |
| INA226 IN− | load switch IN (§7), or straight to the pigtail + if §9.5 → manual | 22 AWG | |
| load switch OUT | pigtail centre (+) → board DC jack | 22 AWG, short | Keep the drop small: the board needs ≥ 4.75 V at its 5 V pad, and that leaves only 0.25 V of margin [P facts "Minimum board input"] |
| USB-C breakout GND | pigtail sleeve (−) | 22 AWG | Supply current returns on its own wire, not through the star |
| INA226 VCC / GND | Pico 3V3(OUT) pin 36 / star | Dupont | Powering it from the board would add its own current to the reading [P §3] |

- **Why high-side** (shunt in the + wire, not the ground wire): the board's ground is already
  tied to the host through the USB-Blaster and the logic analyser. A ground-side shunt could be
  bypassed through those paths. In the + wire, the shunt is the only way in [P §3, verifier
  correction 2].
- **Board DPDT power button stays UP** (DC jack). Pressed = USB-B. **Block the board's USB-B**
  with the printed blank. If USB-B were powered and the button pressed, the board would run
  un-metered and the INA226 would read ≈ 0 [P red flag 3; D 3.4.19].
- **Board jack polarity:** centre = +5 V from the V2.1 schematic. **Unverified on your V3.0
  board.** Check it with continuity (§9). The board has **no fuse, no reverse-polarity
  protection, no over-voltage protection** [P TL;DR 1]. 12 V into it is destructive [P facts
  "AMS1117 Vin abs max"]. The USB-C 5 V inlet and the 12 V barrel are different connector
  families, so they cannot be swapped [P red flag 1].
- INA226 setup (firmware, for later): Current_LSB 25 µA, CAL = 2048, CT 1.1 ms, AVG 64 [P §3].

### 2.2 Heater 12 V chain (the safety chain)

```
12 V adapter + ─► panel jack ─► FUSE 1 A fast ─► KSD9700 75 °C NC ─► HS10 18 Ω ─► D4184 module LOAD
                                     │                                                   │ (switch)
                                     └──────────────────────► D4184 module "+"           │
12 V adapter − ◄─ panel jack ◄──────────────────────────────── D4184 module "−" ◄─────────┘
```

| From | To | Wire | Why |
|---|---|---|---|
| Panel jack centre (+) | Fuse holder (panel, "FUSE 1A") | 22 AWG | The fuse comes first, so it protects every wire after it |
| Fuse holder | KSD9700 lead 1 | silicone 22 AWG | The thermostat opens at ~75 °C even if the Pico has crashed or the MOSFET has failed short |
| KSD9700 lead 2 | HS10 tag A | silicone, heat-shrunk | |
| HS10 tag B | D4184 module **LOAD** | silicone, heat-shrunk | Low-side switch: the MOSFET sits between the heater and ground |
| Fuse holder output (or after the KSD) | D4184 module **"+"** | 24 AWG | The opto module makes its gate voltage from this (≈ ½ × 12 V ≈ 6 V) [M row "D4184 opto module drive"] |
| D4184 module **"−"** | Panel jack sleeve (−) | 22 AWG, direct | **The heater return never goes through the star ground** |
| D4184 module signal **PWM / GND** | Pico GP22 (pin 29) / star | Dupont | The Pico only lights an LED in the opto (≈ 2 mA) |

- **Why the heater return skips the star:** 0.7 A through the thin star wire would put a few
  millivolts of heater ripple on every sensor ground and onto the FPGA board's ground. The
  INA226 and the thermocouple (tens of µV per °C) would see it. With the opto module, heater
  ground and logic ground are not connected at all [M MOSFET table; P §4].
- **If you use the CE09733 fallback** (not isolated): its signal GND and power GND are probably
  the same copper (**unverified**: check with a DMM [P §4]). Then that module is the *one* tie
  between the domains, and the rule still holds: heater current enters and leaves on its power
  terminals and the star wire carries only milliamps.
- **Both supplies must be 2-prong (Class II).** *Why:* the host PC is earthed. If the 12 V
  negative were also earthed, heater current could split through mains earth → PC → USB
  shields → Pico and FPGA grounds [P §4].
- **Both HS10 tags sit at +12 V when the MOSFET is off** (that's what low-side switching means).
  Run the tags N–S, heat-shrink both, and keep them ≥ 5 mm from any header pin [D 3.1.3; T §5].
- **Treat the KSD9700 case as live.** One lead may be joined to the iron case. The drawing note
  "虚接" is ambiguous, so this is **unverified** [T verifier V3]. Mount it over Kapton with its
  unprinted (sensing) face down [T §5].
- **Numbers (derived [T §3–4]):** 12–12.6 V / 18 Ω = 0.67–0.70 A, 8.0–8.8 W. The 1 A fast fuse
  runs at ≤ 75 % of its rating (Littelfuse rule). The fuse holder needs ≥ 1.17 A, and the 10 A
  S5991 is fine.

### 2.3 Fan (5 V from Pico VBUS, §9.4 default)

| From | To | Why |
|---|---|---|
| Pico **VBUS, pin 40** | Fan + | This is host-USB 5 V. **Never** the board's header 5 V: that would pollute the INA226 reading [D 3.4.23] |
| Fan − | AO3400A drain | Low-side switch |
| AO3400A source | star | |
| Pico **GP14, pin 19** | 100 Ω → AO3400A gate; 47–100 kΩ gate → source | Gate resistor limits ringing. Pull-down keeps the fan off while the Pico boots [M MOSFET table] |
| Flyback diode | across the fan, cathode to +5 V | A motor is an inductor. The diode catches the voltage spike when the switch opens [M] |

The fan draws ~200 mA [S row 68] from the host USB port, alongside the Pico. Whether a 2-wire
fan behaves well with its supply PWM-switched at 25 kHz is **unverified**. If it whines or
stalls, use a lower PWM frequency or fixed speed steps. The research advises a **fixed baseline
fan duty during sweeps** [T §7].

## 3. Pico GPIO map

**Fixed from the brief.** The brief put the heater on GP15 and the fan on GP14. Both are PWM
**slice 7**, and a slice has one counter and one divider, so both would be forced to the same
frequency [M "The GP14/GP15 problem"; RP2040 datasheet §4.5.1]. The fan wants ~25 kHz. The opto
heater module is too slow for that: its gate takes ~4–9 µs to charge and discharge, against a
40 µs period [M "Opto speed"]. **The heater moves to GP22 = PWM slice 3 A** (option (a) in
[M]), run slowly (~10–100 Hz). GP15 is left unused so slice 7 belongs to the fan alone.

| Function | GP | Physical pin | PWM slice / ch | Connects to | Notes |
|---|---|---|---|---|---|
| I²C0 SDA | GP4 | 6 | (2 A, unused) | INA226 SDA, Si5351 SDA, BME280 SDA | [M facts] |
| I²C0 SCL | GP5 | 7 | (2 B, unused) | INA226 SCL, Si5351 SCL, BME280 SCL | |
| SPI0 RX (MISO) | GP16 | 21 | — | MAX31855 **DO** | [M facts] |
| SPI0 CSn | GP17 | 22 | — | MAX31855 **CS** | |
| SPI0 SCK | GP18 | 24 | — | MAX31855 **CLK** | ≤ 5 MHz, mode 0 [M] |
| **Heater PWM** | **GP22** | **29** | **3 A** | D4184 opto module PWM input | **4.7 kΩ pull-down to GND** (see below). Slow PWM. Lowest hardware PWM ≈ 7.5 Hz at 125 MHz [M], or time-proportion in firmware with a ~1 s period [M option (b)] |
| **Fan PWM** | **GP14** | **19** | **7 A** | AO3400A gate (via 100 Ω) | ~25 kHz |
| Fan tach (only if §9.4 → 12 V fan) | GP13 | 17 | 6 B | fan tach, **pulled up to 3.3 V** | Counting on the PWM block uses up slice 6. A GPIO interrupt or PIO avoids that [M] |
| Load-switch EN (§9.5) | GP20 | 26 | 2 A (unused as PWM) | load switch enable | Default state on reset: Alex's choice, see §7 |
| INA226 ALERT (optional) | GP21 | 27 | 2 B (unused) | INA226 ALE | Open-drain. Pull up to 3.3 V |
| 3V3(OUT) | — | 36 | — | VIN of every module | < 300 mA total [M] |
| VBUS | — | 40 | — | fan + | host USB 5 V |
| GND | — | 3, 8, 13, 18, **23**, 28, 33, 38 | — | star (one or two of these) | Pin 23 is the GND beside the SPI pins [M] |
| (unused) | GP15 | 20 | 7 B | — | Leave free: it shares slice 7 with the fan |

Physical pins other than 6, 7, 17, 19, 20, 21, 22, 23, 24, 29, 36 were not re-read by the
research. They come from the official Pico pinout sheet (S3 in [M]): GP20 = 26, GP21 = 27,
VBUS = 40. Check them against the silkscreen.

- **Why the heater pin has a pull-down.** During a reset, or with the Pico unplugged, the pin
  floats. The pull-down holds it low, so the heater stays off [T §4 interlocks]. On a Pico 2 the
  RP2350-E9 erratum means the *internal* pull-down cannot hold a floating input low. Use an
  external one ≤ 8.2 kΩ, hence 4.7 kΩ [M row "RP2350 erratum E9"].
- Firmware interlocks to build later (not wiring, listed so the pins make sense): latched heater
  off at T_top ≥ 70 °C; off on any MAX31855 fault bit or a frozen reading; RP2040/RP2350
  watchdog on; host heartbeat timeout → idle [T §4].

## 4. I²C bus (I²C0, GP4 SDA / GP5 SCL)

| Address | Device | Set by | Module pins → Pico |
|---|---|---|---|
| **0x40** | INA226 (CJMCU-226) | A0 = A1 = GND (module default; confirm with a scan) [M; P] | VCC → 3V3(OUT) · GND → star · SDA → GP4 · SCL → GP5 · ALE → GP21 (opt.) |
| **0x60** | Si5351A (Adafruit #2045) | fixed, 10-MSOP has no address pin [M; C] | VIN → 3V3(OUT) · GND → star · SDA → GP4 · SCL → GP5 · CLK0 → §6 |
| **0x77** | BME280 (PiicoDev CE07503) | default; its switch gives 0x76 [S row 44] | 3V3 → 3V3(OUT) · GND → star · SDA/SCL → GP4/GP5 |

- **No collisions** [M final I²C map]. **Cheap-route warning:** a GY-BME280 defaults to **0x76**,
  not 0x77 [M]. Then the engraved I²C map on the box [D 3.7.31] would be wrong. Either strap it
  to 0x77 or change the label.
- **Pull-ups:** I²C lines only ever get pulled *up*, and something has to do it. Each Adafruit
  board adds 10 kΩ to its VIN. Several in parallel give ≈ 3.3 kΩ, which is fine at 100–400 kHz
  [M]. The CJMCU-226 and PiicoDev pull-up values are **unknown** [P facts "Module A0/A1"]. Measure
  SDA→3V3 and SCL→3V3 resistance with the modules wired and unpowered. **Aim for 2–10 kΩ.** If it
  reads open, add 4.7 kΩ from each line to 3V3(OUT). Don't rely on the Pico's internal pull-ups:
  they are too weak for a bus.
- The BME280 sits at the air intake, on its own mount [D 3.5.25]. Keep its I²C run short and
  away from the heater leads.
- **Self-check that cannot pass by accident:** an I²C scan must show exactly 0x40, 0x60 and 0x77.
  Then read BME280 register 0xD0: it must return 0x60. A BMP280 returns 0x58 [M].

## 5. SPI to the MAX31855 (Adafruit #269)

Header, left to right: **Vin, 3Vo, GND, DO, CS, CLK** [M row "#269 header"].

| MAX31855 pin | To | Notes |
|---|---|---|
| Vin | Pico 3V3(OUT), pin 36 | 3.3 V even though the board accepts 5 V |
| 3Vo | — | leave unconnected |
| GND | star (or Pico pin 23) | |
| DO | GP16 (pin 21) | data from the chip, read-only |
| CS | GP17 (pin 22) | |
| CLK | GP18 (pin 24) | ≤ 5 MHz |
| Thermocouple **+** (yellow, ANSI) | right-hand screw terminal | Adafruit uses ANSI colours. An IEC probe is **green +, white −**. Check which one you bought [M row "#269 thermocouple terminal"] |
| Thermocouple **−** (red, ANSI) | left-hand terminal | **T− must not touch ground** [T §5]. That's why the junction must be insulated from the spreader |
| 10 nF capacitor | across T+ / T− at the terminal | Recommended by the datasheet. Check whether the breakout already has one [T facts] |

- Mount the MAX31855 on the cool module plate. Its cold-junction reference is its own chip, so
  local heating shows up as reading error [T §5].
- Label the reading **T_top**, not Tj. With the heater on top, the package top reads 3–12 K
  **above** the die [D §7; T §1].

## 6. Clock: Si5351 → FPGA PIN_24 (§9.6 default: include)

| From | To | Notes |
|---|---|---|
| Si5351 **CLK0** | **P1-34** = FPGA **PIN_24** = CLK2 (dedicated clock input, feeds global clocks and PLL_1) | **≤ 60 mm**, twisted with the ground wire [D 3.6.27]. Optional 33 Ω series resistor at the Si5351 end. That copies the board's own oscillator (R3 = 33 Ω) and damps ringing [C §4] |
| Si5351 **GND** | **P1-1 / P1-2** (P1's only GND pins) | Dedicated wire, twisted with CLK0. *Why:* the low-level margin is only 0.2 V (Si5351 low ≤ 0.6 V, FPGA needs ≤ 0.8 V). A long ground return would use it up [C TL;DR 3, §4] |
| Si5351 VIN / SDA / SCL | 3V3(OUT) / GP4 / GP5 | VIN at 3.3 V keeps the I²C pull-ups at 3.3 V [C verifier]. Check the module's own 3.3 V rail still reads ≥ 3.0 V [C §6.5] |

- **Keyed shroud.** P1-34 sits next to **3.3 V (P1-35/36) and 5 V (P1-37/38)** [C TL;DR 4].
  The printed "CLK IN" shroud over P1-31..38 leaves only pin 34 open [D 3.6.27]. *Why:* a clock
  output pushed onto a power pin fights a supply.
- **Pin-1 end of P1 is unverified.** The CAD has two Si5351 positions keyed to `P1_PIN1_END`
  [D 3.6.27]. Find the square pad or triangle first [C §6.1].
- **Continuity check pending** (the gate for buying the Si5351): board unpowered, P1-34 ↔ FPGA
  package pin 24 must beep. P1-34 ↔ GND and ↔ 3.3 V must be open. The pin map comes from the V2.1
  schematic, and your board is V3.0 [C §6.2; D §12].
- **Keep the Si5351 outputs disabled** (over I²C: this chip has no output-enable pin) until a
  known design is loaded over JTAG. Also keep them disabled whenever the FPGA's 5 V is off.
  *Why:* nobody knows what the design in flash does with pin 24 at power-up, and two outputs on
  one wire fight [C §4 "Contention"]. Driving a signal into an unpowered chip can also feed it
  through its input protection diodes (general principle; **not checked for this part**).
- The FPGA side is Alex's: `IO_STANDARD "3.3-V LVTTL"` on PIN_24, and the edge-counting RTL
  that proves the clock arrives [C §6.7]. That RTL is Alex's to write (Article I).

## 7. Optional: 5 V load switch for remote power cycling (§9.5 default: include)

*Why:* the fleet goal says no step may need a human [D §10]. A Pico-controlled switch in the
metered 5 V line lets an agent power-cycle a hung FPGA board.

**The part is not chosen.** Nothing in the research covers it. Requirements, each with its reason:

| Requirement | Why |
|---|---|
| **High-side** (switches the + wire, not ground) | A ground-side switch would leave the board's ground connected through the USB-Blaster and logic analyser. Current could then sneak back that way [P §3, same reason as the INA226] |
| After INA226 IN− (between IN− and the pigtail) | The INA226 then still reads the supply voltage when the board is off. Its drop sits outside the measured VBUS. For the true board voltage, add an optional VBUS sense wire to P2-1 [P §3] |
| ≥ 1 A, on-resistance ≤ 0.1 Ω | At 0.32 A (high estimate [P]) that is ≤ 32 mV, a small part of the 0.25 V margin |
| Enable works from a 3.3 V GPIO (GP20, pin 26) | RP2040 limit |
| A defined state when the Pico resets | **Decision for Alex:** off-by-default is safer, but a Pico reboot would kill the FPGA. On-by-default keeps the FPGA running |

A common topology is a P-channel MOSFET in the + line, with its gate pulled up to 5 V (off) and
pulled down by a small N-MOSFET or NPN that GP20 drives. This is offered as a starting point to
research, not a checked design. Firmware order for a power cycle: disable Si5351 outputs → switch
off → wait → switch on → reload over JTAG → re-enable the clock.

## 8. Logic analyser

| From | To | Notes |
|---|---|---|
| LA CH0–CH7 | The reserved, engraved **P1/P2 rows** outside the bridge footprint, through the printed lead comb [D 3.6.28] | Which FPGA signals go there is set by the on-chip lab region (Alex's RTL), so pins are TBD |
| LA GND | **P2-6** (GND) | P2-5 carries the star wire. P1-1/2 carry the clock ground |

- **Never clip onto** P1-34 (clock in), P1-35..38, P2-1..4 or P3-19/20 (power) [P facts "Header power pins"].
- **All P2 signal pins are shared with the SDRAM** [C §7]. A design that outputs on P2 must keep
  the SDRAM deselected (pin 72, SD CS).
- Inputs tolerate up to 5.25 V and switch at V_IH ≥ 2.0 V. 3.3 V FPGA I/O is fine [S row 137].
- The 2.54 mm header pitch is assumed. No vendor document states it [C verifier]. Measure it.

## 9. Pre-power checklist

Do these **in order**, with a multimeter, before the first power-up. Each check is designed so
that a wrong build fails it. "Open" means no continuity / > 1 MΩ.

**A. Isolation (everything unpowered, all supplies unplugged)** [D §6.4; T §9]

| # | Probe between | Expect | If it fails |
|---|---|---|---|
| A1 | Thermocouple lead (each) ↔ spreader | **open** | The junction is touching metal. The MAX31855 will fault or read garbage |
| A2 | Thermocouple lead ↔ probe sheath | **open** | Grounded-junction probe: wrong part |
| A3 | KSD9700 each lead ↔ its case | record the result | If one beeps, the case is live: confirm Kapton under it |
| A4 | KSD9700 case ↔ top plate / spreader | **open** | Insulation missing |
| A5 | HS10 each tag ↔ HS10 housing | **open** | Damaged heater |
| A6 | Spreader ↔ every board GND (P1-1, P2-5, P3-1) | **open** | Metal is touching the leads or the exposed pad path |
| A7 | HS10 tags ↔ every nearby header pin | **open** | A tag is touching a header pin: 12 V on FPGA I/O |
| A8 | Heater + (after the fuse) ↔ star ground | **open** | Heater domain tied to logic ground |
| A9 | Opto module PWM/GND side ↔ "−" terminal | **open** (opto) / record (CE09733) | Not the isolated module you thought |
| A10 | Each plug pack: DC − ↔ mains earth pin | **open** | Earthed adapter: replace it [P must-measure 8] |
| A11 | P1-34 ↔ FPGA package pin 24 | **beep** | Don't connect the Si5351 |
| A12 | P1-34 ↔ GND, and ↔ 3.3 V (P1-35) | **open** | |

**B. Values (unpowered)**

| # | Check | Expect |
|---|---|---|
| B1 | Heater resistance, through fuse + KSD to module LOAD | 18 Ω ± tolerance (≈ 17–19). A reading of 0.18 Ω means the wrong part (R18) |
| B2 | Fuse fitted, marked 1 A fast | — |
| B3 | INA226 shunt marking | **R100** (0.1 Ω). If it is R010, the CAL value changes |
| B4 | SDA→3V3 and SCL→3V3, modules wired | 2–10 kΩ |
| B5 | Pigtail: centre ↔ INA226 IN−/switch out; sleeve ↔ USB-C breakout GND | beep |
| B6 | Board DC jack centre ↔ board "5V" test pad, button **up** | beep [P must-measure 2] |

**C. First power, one domain at a time**

| # | Step | Expect |
|---|---|---|
| C1 | Pico USB only. I²C scan | exactly 0x40, 0x60, 0x77. BME280 0xD0 = 0x60 |
| C2 | Pico USB only. Si5351 outputs disabled. Module 3.3 V rails | ≥ 3.0 V |
| C3 | USB-C 5 V in, board connected | board 5 V pad ≥ 4.75 V under load [P must-measure 5]; INA226 reads a plausible 70–320 mA [P TL;DR 3] |
| C4 | **Test that cannot pass by accident:** hang 100 Ω (≥ 0.5 W) across a header 5 V/GND pair | INA226 current rises by ≈ 50 mA. If the shunt were not in the path, it would not move [P must-measure 7] |
| C5 | 12 V in, **Pico unplugged** | heater stays cold (the gate is held off by the pull-down) |
| C6 | Heater module at 100 % duty (Pico) | opto gate ≈ 6 V. V_DS across the MOSFET ≈ I × R_DS(on). A low gate or a high V_DS means the FET is not fully on [M must-measure 10] |
| C7 | Before trusting it: 60 °C hold with the fan off, and a stuck-on test with the thermostat in circuit | KSD opens near its rating. Log heater body, nearest printed part, lid underside, fan inlet [D §6.7]. Record the actual trip and reset temperatures [T §9.4] |
