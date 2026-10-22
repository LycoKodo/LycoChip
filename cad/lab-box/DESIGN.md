# Agent Lab Box — MVP design (v0.1)

> Canonical spec for the CAD in this folder. Base concept: **`concepts/simple-first.md`**
> ("One Tub + Metal C-Frame"), amended by everything below. Where this file and the
> concept disagree, **this file wins**. Written 2026-10-23 by Claude (lead session) from
> the design panel: three concepts, three lens judges, and massing models of each
> (`concepts/MODELLING-FINDINGS.md`). Nothing here is verified on hardware.

## 1. What this box is

A PETG tub that holds the FPGA board on brass standoffs, with a small metal bridge over
the chip that presses a heater block onto the package with a spring. A side bay holds the
Pico and the sensor/driver modules; a 40 mm fan blows room air across the board and out
the far wall. A clear lid shows the board. An agent sets a chip temperature, the Pico
holds it, and the agent sweeps the clock and records pass/fail and power.

## 2. Why this concept

Panel scores (sum of three judges, /30): demo-first 19.5, thermal-first 18, simple-first
17.5. Close on paper. Simple-first was chosen because:

- **It can be built before the Cerebras demo**: 4 printed parts, PETG only, no ASA
  (no enclosed printer needed), bought metal is a 20 × 3 mm aluminium bar and standoffs.
- **The clamp load path is all metal** (bridge, brass legs, keel). Plastic never carries
  the spring force near the heater, so clamp force does not creep and runs stay
  repeatable (learning card `plastic-heat-creep`).
- **Fewest manual adjustments**, which matters for the long-term goal: unattended boxes
  used by agent fleets (§10).

Its weaknesses (judged worst on demo looks and access) are fixed by the amendments in §3,
mostly grafts from demo-first.

## 3. Amendments to the base concept (all mandatory)

### 3.1 Clamp and heater stack
1. **Metal top plate carries the load**, not the HS10 fins: bridge → spring plunger →
   ball → cone seat in an aluminium top plate (from 20 × 3 bar) → spreader block →
   insulating pad → package. The HS10 bolts to the plate's side; it is out of the load path.
2. **Spreader contact face ≤ 18 × 18 mm**, centred on the package, edges broken. Stock is
   a **decision for Alex** (§9): 20 mm square aluminium bar filed to 18, or stacked
   20 × 3 flat. Nothing metal may sit over the 22 × 22 mm lead ring.
3. **HS10 lugs run N–S**, both tags and joints in heat-shrink, ≥ 5 mm from any header pin
   or Dupont housing *after* the ±4 mm photo tolerance. Do not bend tags at the end cap.
4. **KSD9700 75 °C** on a wing of the top plate ≥ 10 mm above the leads, held by a
   screwed FR4 strap (2 × M2) over Kapton. No cable ties. Case treated as live.
5. **Thermocouple**: insulated junction, in a blind Kapton-lined groove in the spreader's
   contact face at the package centre. The lead exits downstream and is anchored 20 mm along.
6. **Spring force readable**: a soft spring (~1–2 N/mm), target 8 N (range 5–10 N), with an
   engraved length scale so force = k·(L0 − L) is read, not counted in screw turns.
7. **Repeatable placement**: 2 locating pins at each bridge-to-leg joint plus a printed
   spreader centring gauge for first placement and every refit.
8. **Back-support post**: several sites in the keel (centre and ±6 mm in X and Y) to dodge
   unknown bottom-side parts; insulating (nylon/ASA) tip, height set with a paper feeler.
   Fixes modelling finding: the concept's nylon screw in a standoff cannot be assembled.
9. ≥ 5 mm air (target 25 mm) between any printed part and heater metal; no printed
   feature in the plume above the HS10. Silicone/PTFE wire within 15 mm of the heater.
10. No screw tip may protrude below the top plate toward the board.

### 3.2 Board mounting
11. **Print a 1.2 mm board-footprint gauge and an insert coupon first** (holes, FPGA
    outline, P1/P2/P3, JTAG, DC jack, USB-B). Lay it on the real board, update
    `params.py`, *then* print the tub. This replaces the concept's Ø9-hole "slack",
    which the fit judge showed gives ±0.5 mm, not ±2.8.
12. Keel-to-floor fasteners must clear the leg hexes (concept: 0.0 mm, corners touch).

### 3.3 Enclosure, lid, access
13. **Lid off without tools**: ≤ 4 captive knurled thumbscrews. Removing the lid must not
    disturb the clamp, the JTAG plug or any wire.
14. **Lid clearance ≥ 5 mm** over the tallest part at maximum adjustment: plunger backed
    out, power-switch cap up (14–25 mm, photo-estimate), IDC plug + ribbon bend.
    Lid locating lip must clear the fan and fuse holder (concept margin was ~6 mm, not stated).
15. Window clamping must actually reach the acrylic (concept: washers fall short).
16. Floor is 3 mm, too thin for 6.7 mm inserts: module plate fixes through **bosses**,
    not floor inserts.
17. Vertical vent slots only (no long bridges); every part ≥ 5 mm inside the 220 bed,
    with a split option parametrised for when the printer is known.

### 3.4 Power, JTAG, cables
18. **FPGA 5 V enters on USB-C** (breakout with 5.1 kΩ CC pull-downs, or it gives 0 V from
    C-to-C chargers), physically unlike the 12 V barrel. It runs high-side through the
    INA226 (VBUS tied to IN−) to the board's DC jack via a pigtail. DPDT stays **up**.
19. **Board USB-B blocked** by a printed blank with a pull tab: "NOT USED — 5 V ARRIVES
    METERED VIA DC JACK".
20. **12 V chain**: panel barrel jack → **panel-mount fuse holder, 1 A fast** (reachable
    from outside) → KSD9700 → 18–22 Ω HS10 → low-side D4184 → straight back to the
    adapter's negative, never through the star ground.
21. **USB-Blaster lives inside**, IDC plug permanently seated, ribbon strain-relieved;
    only its USB cable exits, through a labelled clamp ("DO NOT UNPLUG JTAG WHILE
    POWERED"). Dongle size and ribbon length: MEASURE before printing the tub.
    (Concept had it hanging outside through a front notch.)
22. Pico and logic-analyser USB: printed backstop rib behind each USB end plus an
    external tie anchor. LA connector may be Mini-B, not USB-C: MEASURE.
23. Fan runs from Pico VBUS (5 V fan) or 12 V (12 V fan), **never** the board's header
    rails (that would pollute the INA226 reading).

### 3.5 Airflow and sensors
24. No clamp structure in the fan jet core upstream of the FPGA: move the W leg off the
    fan axis (concept: leg on axis at Y 101) or move the fan.
25. **BME280 at the intake**, upstream of the fan, its own position, not stacked over
    other modules (concept stacked it on 20 mm standoffs).
26. Exhaust slot numbers made consistent (concept: 13 × 3 mm @ 6 mm spans 75, not 80 mm).

### 3.6 Clock and logic-analyser leads
27. **Si5351**: ≤ 60 mm lead to P1-34, twisted with a dedicated ground to P1-1/2. A
    printed **"CLK IN" key shroud** over P1-31..38 leaves only pin 34 open, so the clock
    lead can never land on 3.3 V/5 V (P1-35..38). Two Si5351 positions keyed to a
    `P1_PIN1_END` parameter (pin-1 end is unverified).
28. Reserved, engraved P1/P2 rows for logic-analyser clips, outside the bridge's
    footprint; a lead comb keyed to `P1_PIN1_END`.

### 3.7 Labels (engraved)
29. Every exit: USB-BLASTER / JTAG · PICO USB · LOGIC ANALYSER · FPGA 5V IN (USB-C,
    METERED) · HEATER 12V IN · FUSE 1A · AIR IN · AIR OUT.
30. Front nameplate: "KNOBS: HEAT · AIR · CLOCK   EYES: CHIP TEMP · AIR TEMP · POWER · LOGIC".
31. Safety chain on a visible surface: "12V → FUSE 1A → THERMOSTAT 75°C → MOSFET → HEATER".
    I²C map: 0x40 INA226 · 0x60 Si5351 · 0x77 BME280. A unit-ID plate (§10).
32. Visitor face chosen **after** measuring which way the 7-segment digits read.

## 4. Coordinates

Board frame (from `docs/lab-box/research/board-mechanical.md`): X from the W edge, Y from
the N (DB9/VGA) edge, board 106 (X) × 136 (Y), FPGA centre (57.5, 86). The box frame and
the board's offset in it are as in `concepts/simple-first.md`, adjusted where §3 moves
things. Every board-derived number is a `MEASURE` placeholder in `params.py`.

## 5. Parts

| Part | Material | Source |
|---|---|---|
| Base tub | PETG | printed |
| Lid frame (acrylic rebate, thumbscrew bosses) | PETG | printed |
| W I/O panel (drop-in) | PETG | printed |
| Module plate | PETG | printed |
| Board-footprint gauge, insert coupon, spreader centring gauge | PETG | printed, fit tools |
| USB-B blank, CLK-IN shroud, LA comb, cable clamps | PETG (shroud ASA optional) | printed, small |
| Bridge, keel, top plate | Al 20 × 3 flat bar | bought, cut + drilled |
| Spreader block | Al (stock: decision §9) | bought, cut + filed |
| Legs | brass M3 hex standoffs | bought |
| Window | 3 mm clear acrylic | bought, cut |

## 6. Assembly order (outline)

1. Print the footprint gauge and insert coupon; measure; update `params.py`; re-run `make.py`.
2. Print tub, panel, plate, lid. Set heat-set inserts.
3. Cut and drill bar parts with the printed jig; file the spreader; check flatness.
4. **DMM isolation checks before first heat**: thermocouple lead to spreader (open),
   KSD lead to case, HS10 tags to housing, spreader to every board ground (open).
5. Mount board, set back-support post with a feeler, fit clamp, set 8 N by spring length.
6. Wire per `docs/lab-box/wiring.md`; seat JTAG; close lid.
7. **Before trusting it**: a 60 °C hold with the fan off, and a stuck-on test with the
   thermostat in circuit, logging heater body, nearest printed part, lid underside and
   fan inlet temperatures.

## 7. Thermal note for the data

The package-top thermocouple reads 3–12 K **above** the die while heating from the top
(`research/thermal-safety.md`). Label it T_top, not Tj, and calibrate the ring-oscillator
sensor at zero heater power.

## 8. Not in v0.1

Peltier cooling, core-voltage control, camera, custom PCB.

## 9. Decisions for Alex (CAD default in bold)

1. **Printer**: model, bed size, enclosed or not. CAD default **220 × 220 × 250, PETG**.
2. Spreader stock: **20 mm square Al bar filed to 18 mm** / stacked 20 × 3 flat.
3. Heater resistor: **18 Ω** / 22 Ω (both HS10-class; 10 Ω ruled out).
4. Fan: **5 V 4010 from Pico VBUS** / 12 V 4-wire PWM fan (speed feedback).
5. Remote power control of the FPGA (§10): **include a 5 V load switch driven by the Pico** / leave manual.
6. Si5351 in v1: **include** (cheap) / defer until the P1-34 continuity check.
7. Budget: local fast route ~AUD 300–340 vs AliExpress ~105–180 (slow); prices unverified.

## 10. Fleet-ready (the long-term goal)

The end goal is autonomous chip labs used by agent swarms, so no step may need a human:
- **Remote power cycle** of the FPGA board (Pico-driven load switch in the metered 5 V line).
- **Repeatable clamp force** across units (spring-length scale, locating pins, gauge).
- **Unit ID + calibration record** per box (thermocouple offset, °C per heater watt).
- **Self-test that cannot pass by accident**: heater actually raises T_top, fan tach
  actually reads, INA226 sees the board's current change when the FPGA is reset.
- JTAG permanently connected.

## 11. MEASURE list

All board positions (see the research's must-measure list), board hole pitch and
diameter, standoff heights, PCB bottom side, power-switch cap height (both positions),
JTAG/AS box height, USB-Blaster dongle and ribbon, header pin height, P1 pin-1 end,
7-segment orientation, every generic module (INA226, BME280 clone, MAX31855 clone,
MOSFET modules, logic analyser), DC jack plug size, fuse holder depth, panel jack hole,
spreader stock, spring rate and free length.

## 12. Known risks

- Every board position is a photo-estimate (±3–5 mm) of an RZRD-branded board; Alex's
  OMDAZZ V3.0 may differ. Step 1 of §6 exists for this.
- No DC rating published for the KSD9700 (low risk at 12 V 0.6 A; unverified).
- No manufacturer clamp-force limit for EQFP packages; 5–10 N spring-limited is a
  conservative choice, not a spec.
- P1-34 = PIN_24 is from the V2.1 schematic; continuity check pending.
