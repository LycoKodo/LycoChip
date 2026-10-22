# LycoChip Agent Lab Box — MVP CAD Brief for Claude Code

> Paste this whole file into Claude Code (or save it in the repo as `docs/lab-box/BRIEF.md` and point Claude Code at it).
> Repo: `~/Desktop/LycoChip` (GitHub: LycoKodo/LycoChip).

---

## 0. Your job in one paragraph

Design the **mechanical CAD** for the MVP "Agent Lab Box": an enclosure and internal mounting system that holds Alex's FPGA dev board in the middle, surrounded by off-the-shelf sensor and actuator modules, so that an AI agent can **turn physical knobs** (temperature, airflow, clock frequency) and **read physical sensors** (package temperature, ambient temperature, power) around real silicon. Produce parametric CAD source, exported printable parts, a bill of materials, and a wiring table. **No custom PCB in this phase** — everything is off-the-shelf breakout modules wired to a microcontroller.

Before you model anything, **ask Alex the questions in Section 9**. Do not guess dimensions.

---

## 1. Why this box exists (the bigger idea)

- Alex's long-term idea: an FPGA-based chip platform **designed to be programmed by AI agents, not humans**. The platform is the product; the agents are its users.
- The gap being targeted: agents can already write RTL and read tool reports, but they **never touch the physical lab**. In real chip development, post-silicon lab work (bring-up, validation, characterisation, debug) is a huge share of engineering effort, and it relies on humans with instruments and the instinct for which instrument answers which question.
- Agents lack three things a human has in the lab:
  1. **Knobs** — change real conditions (temperature, clock, inputs, later voltage).
  2. **Eyes** — see signals and physical quantities at real speed.
  3. **Choosing where to look** — move the probe based on a hypothesis.
- This box supplies the off-chip half of (1) and (2). A separate RTL "lab region" inside the FPGA (probe mux, capture buffer, cycle counters, ring-oscillator sensor, PLL clock sweep) supplies the on-chip half. That RTL is **out of scope for this task**, but the box must leave room and cable paths for it to be used.
- Audience: a clean desk demo Alex can show to contacts at Cerebras, plus a college-application capstone. **It should look deliberate**: labelled ports, a window to see the board's LEDs and 7-segment display, tidy cable exits.

---

## 2. Hardware Alex already owns

**FPGA board:** OMDAZZ Cyclone IV V3.0 dev board
- FPGA: Intel/Altera **EP4CE6E22C8N** (144-pin EQFP; commercial grade, rated **0–85 °C junction**).
- Resources: 6,272 LEs, 276,480 M9K memory bits, 15 18×18 multipliers, 92 user I/O.
- On-board: 50 MHz oscillator, 4 LEDs and 4 keys (both **active low**; LEDs on PIN_84–87), 4-digit 7-segment display, RS-232 via MAX3232 (DB9; needs a USB-to-RS-232 adapter), VGA out, JTAG via USB-Blaster.
- Core supply is a **fixed 1.2 V on-board regulator** — we are **not** adding a voltage knob in this phase (no board modifications).
- **Unknown, must be measured or looked up (do not invent):** board length × width, mounting hole positions and diameter, tallest component height, positions and heights of every connector (power input, JTAG header, VGA, DB9, GPIO headers), how the board is powered (USB? 5 V barrel? which connector), the FPGA package position on the board and its top-surface height.

**Computers:** M1 MacBook Pro (main dev machine; Quartus runs in a container) and a Windows PC with Quartus Prime Lite 25.1 + Icarus Verilog.

**Design status for context:** a reference MNIST demo design runs on the board (Quartus STA predicts Fmax **72.37 MHz**; 16/16 test images bit-exact over JTAG). Alex's own RTL is at the foundations stage.

---

## 3. MVP sensor and actuator set — what to keep and what to cut

**Selection criteria.** Every item must: (a) give the agent a knob or eye it doesn't otherwise have, (b) be an off-the-shelf module, (c) be fully software-controllable, (d) be safe to leave under software control with a hardware backstop.

### KEEP (MVP)

| # | Function | Suggested part | Interface | Why it earns its place |
|---|----------|---------------|-----------|------------------------|
| 1 | **Box controller** | Raspberry Pi Pico (RP2040 or RP2350) | USB serial to host | One brain for every off-chip knob/sensor; runs the closed-loop heater control so the agent sets a *temperature*, not a PWM duty. 3.3 V logic matches the modules. |
| 2 | **Temperature knob (heat)** | Aluminium-clad power resistor (~10 Ω, 10–25 W) or a small Kapton heater pad, pressed onto the FPGA package with a thermal pad; driven by a logic-level N-MOSFET module, PWM from the Pico | PWM GPIO | Real temperature is a real physical variable that shifts silicon timing. This is the headline knob. |
| 3 | **Temperature knob (cool / settle)** | Small 5 V fan (40 mm), PWM via MOSFET (or 4-pin PWM fan) | PWM GPIO (+ optional tach) | Lets the controller pull temperature down as well as up, and makes settling faster and repeatable. |
| 4 | **Package temperature** | K-type thermocouple on the FPGA package + **MAX31855** breakout | SPI | Ground truth for "what temperature is the chip actually at". Also used later to calibrate the on-chip ring-oscillator sensor (a demo result in itself). |
| 5 | **Ambient temperature** | BME280 or similar | I²C | Distinguishes "box air is hot" from "chip is hot". Cheap context for every experiment. |
| 6 | **Power sensor** | **INA226** (or INA219) breakout in series with the FPGA board's supply line | I²C | Power per experiment is data agents never normally see. Note: this measures the **whole board**, not the FPGA core alone (core-only needs a custom PCB later). |
| 7 | **Clock knob (conditional)** | **Si5351A** programmable clock breakout (8 kHz–160 MHz, 3 outputs) | I²C | One part replaces "a drawer of different crystals". **Only useful if the board breaks out an FPGA clock-capable input pin on its headers — check the board schematic before buying.** If not, the on-chip PLL sweep (RTL side) is the clock knob and this item is dropped. |
| 8 | **External eyes** | Cheap 8-channel USB logic analyser (sigrok/PulseView compatible) clipped to the GPIO header | USB to host | An independent check on what the chip's pins actually do, outside the FPGA's own view. Low sample rate (~24 MHz class) is fine for slow I/O; full-speed internal capture comes from the on-chip capture buffer. |
| 9 | **Hardware safety backstop** | Normally-closed bimetal thermostat (~70 °C, e.g. KSD9700 type) in series with the heater supply, plus an inline fuse on the heater supply | none (passive) | Cuts the heater even if software or the Pico fails. Non-negotiable. |

### CUT (and why)

- **Multiple crystal oscillators** → replaced by one Si5351 (if a clock pin exists) and the on-chip PLL.
- **Core voltage knob** → the board's 1.2 V regulator is fixed; changing it needs board surgery. This is the main reason for a custom PCB in a later phase.
- **Oscilloscope** → expensive; logic analyser + on-chip capture covers the MVP. Add a USB or SCPI scope later.
- **Peltier (cold side)** → needs several amps and a heatsink; heater + fan is enough for the MVP. Revisit in v2.
- **Camera** (reading LEDs/7-seg optically) → interesting later, not MVP.

### Power domains (keep separate)

- **FPGA board:** its own supply (whatever it uses today), routed **through the INA226 shunt**.
- **Heater + fan:** a separate 12 V DC wall adapter (≈2 A) → inline fuse → thermostat → MOSFET → heater. Fan from 5 V (or 12 V fan from the same adapter).
- **Pico:** powered over its USB from the host.
- **Common ground** between Pico, modules, MOSFET modules and the FPGA board (needed for logic signals). No mains wiring inside the box — only plug-in adapters.

---

## 4. System architecture (for cable routing and layout)

```
Host (Mac / Windows PC) — runs the AI agent
 ├── USB serial ──► Pico (box controller)
 │                   ├─ I²C: Si5351 (if used), INA226, BME280
 │                   ├─ SPI: MAX31855 ◄─ thermocouple on FPGA package
 │                   ├─ PWM: heater MOSFET ─► heater on FPGA package
 │                   └─ PWM: fan MOSFET ─► fan
 ├── USB-Blaster (JTAG) ──► FPGA board (bitstream + on-chip lab region)
 └── USB ──► logic analyser ─► FPGA GPIO header

12 V adapter ─► fuse ─► thermostat ─► heater MOSFET ─► heater
FPGA board supply ─► INA226 shunt ─► FPGA board
```

Later (not this task): both host channels get wrapped in one MCP server so any agent can call `set_temperature`, `set_clock`, `read_sensors`, `program`, `capture`.

**Suggested default Pico pin map (verify against the official Pico pinout before committing):**
- I²C0: SDA GP4, SCL GP5 → Si5351, INA226, BME280 (check addresses don't collide)
- SPI0: SCK GP18, MISO GP16, CS GP17 → MAX31855
- Heater MOSFET PWM: GP15
- Fan MOSFET PWM: GP14; optional fan tach: GP13

---

## 5. Enclosure requirements

**Layout**
- FPGA board in the centre on standoffs, with clear access to its JTAG header, power input, GPIO header (for the logic analyser), and optionally VGA and DB9.
- A **heater clamp bracket**: a separate part that presses the heater (with thermal pad) and the thermocouple tip onto the FPGA package top, with adjustable pressure (screw or spring). It must not short anything and must not load the board unevenly. Needs the measured package position and height.
- **Thermal zoning:** heater zone around the FPGA; Pico, MOSFET modules, INA226 and Si5351 on a separate mounting plate away from the heat. Fan positioned to move air across the FPGA zone, with inlet/outlet vents.
- Ambient sensor placed in the air path but away from the heater's direct radiation.

**Material and heat**
- The heater zone may run near 60–70 °C. **PLA softens around 55–65 °C — do not use PLA near the heater.** Prefer PETG or ASA for printed parts; use **brass/metal standoffs** under the FPGA board and metal or high-temp parts in the heater clamp where it touches the heater.

**Access and looks (it's a demo object)**
- Removable lid with a clear window (e.g. acrylic insert) over the FPGA board so the LEDs and 7-segment display are visible.
- Labelled cut-outs: USB-Blaster cable, FPGA power, Pico USB, 12 V barrel jack, logic-analyser lead slot, optional VGA/DB9. Engraved or embossed text labels.
- Fasteners: M3 screws into heat-set inserts.
- Cable strain relief at exits.

**Manufacturing**
- Fabrication method is not decided yet (see questions). Default to 3D-printed parts that fit a 220 × 220 mm bed, split into multiple parts if needed. If Alex says laser cutting, switch to a panel design and export DXF.

---

## 6. Deliverables

Put everything under the repo:

```
cad/lab-box/
  params.py        # every dimension in one place; MEASURE placeholders loudly marked
  box.py           # parametric model (CadQuery preferred)
  parts/           # exported STEP + STL per part: base, lid, window frame, heater clamp, module plate
  renders/         # PNG/SVG renders of the full assembly and each part, for Alex to check
  README.md        # how to regenerate, print settings, assembly order
docs/lab-box/
  BOM.md           # part, qty, purpose, suggested Australian suppliers (Core Electronics, Jaycar, Altronics, AliExpress), approx AUD price marked "unverified"
  wiring.md        # pin-level wiring table + diagram, power domains, safety chain
```

**Tooling:** CadQuery (Python) is preferred because it exports STEP as well as STL. Verify it installs on Alex's machine before relying on it; if it won't install cleanly, fall back to OpenSCAD and say so.

---

## 7. Working rules (from the LycoChip project — follow them)

- **Evidence over assertion.** Say "unverified" when something is unverified. An exit code of 0 is not evidence — render the model and look at it, check that exported meshes are watertight, check that parts actually fit their measured counterparts.
- **Never invent dimensions.** Any value not measured or taken from a datasheet is a loud `MEASURE` placeholder, listed in the README.
- **Flag early and plainly** if something won't fit, won't be safe, or won't work (e.g. no clock-capable pin on the headers → drop the Si5351).
- **Alex is learning.** Briefly explain each design decision and the reasoning, in plain words. He prefers video tutorials for new technical material, so point to one where it would genuinely help.
- **Ask before anything that costs money** (part choices that commit to a purchase).
- Correct "pin" gently when he means a port.

---

## 8. Demo the box must support (design for this)

1. Agent sets the package temperature to a sequence of setpoints (e.g. 30 → 40 → 50 → 60 °C), waits for it to settle (controller reports "stable").
2. At each temperature, the agent sweeps the clock (on-chip PLL, or Si5351 if available) and records pass/fail of a self-checking test design plus board power.
3. Output: a **shmoo-style map** (frequency × temperature, pass/fail), compared against Quartus's STA prediction (72.37 MHz for the reference design).
4. Second demo: a planted bug (skipping the `mac_en` one-cycle delay makes 3 of 16 MNIST images misclassify) — compare an agent with lab access against an agent with source code only.

The CAD must make these repeatable: stable heater contact, consistent thermocouple placement, repeatable airflow.

---

## 9. Ask Alex these before modelling

1. **Board measurements** (calipers): length × width; mounting hole positions and diameter; FPGA package position and top height; positions/heights of power input, JTAG header, GPIO headers, VGA, DB9; tallest component height. Photos from above and each side help.
2. **How is the board powered** today (which connector, what voltage)?
3. **Does the board break out a clock-capable FPGA input pin** on its headers? (Check the board schematic — decides whether the Si5351 stays.)
4. **Fabrication:** 3D printer (which model, bed size, which materials available?) or laser cutter? School access?
5. **Budget** for MVP parts.
6. How he wants to view CAD (a STEP viewer, a slicer, or just renders).

---

## 10. Out of scope for this task

- Any custom PCB. (Planned later: v2 = a simple sensor board that plugs into the FPGA board's headers, designed in KiCad; v3 = Alex's own FPGA board with a programmable core-voltage supply and core-only power sensing.)
- FPGA RTL for the on-chip lab region.
- Pico firmware and the agent/MCP server (separate tasks — but leave the pin map and wiring docs ready for them).
