# Concept: Simple-First: One Tub + Metal C-Frame

> Design-panel concept (simple-first), 2026-10-23. Input to DESIGN.md, not the design itself.

**A one-piece PETG tub with a drop-in I/O side panel, a module plate in a side bay and a windowed lid. An all-metal C-frame (aluminium bridge, aluminium keel, brass legs, spring plunger) presses the heater onto the FPGA, so no printed part carries the clamp load or sits in the heater zone, and ASA is never needed.**

# Simple-First concept: "One Tub + Metal C-Frame"

## 0. Idea in one paragraph
The concept has **four printed parts, all PETG**: base tub, lid frame, W I/O panel and module plate. The heater clamp is **all metal**: two identical 20 × 3 mm aluminium bars, one above the board (the *bridge*) and one on the floor under it (the *keel*), joined by brass standoff legs outside the PCB outline. A brass and nylon post sits under the FPGA, and a threaded spring plunger in the bridge sets the force. The clamp force runs in a closed metal loop, plunger → stack → PCB → post → keel → legs → bridge. No plastic carries it, so PETG creep and ASA printing are both out of the problem. All connectors sit on one drop-in side panel, which is the only part to reprint when a connector measurement changes. Every board-position feature has adjustment slack, so the photo-estimated board numbers do not force a reprint.

## 1. Coordinate frames
- **Board frame** (board-mechanical.md): N = DB9/VGA edge, S = JTAG/AS/DC-jack edge, W = USB-B/switch edge, E = keys/LEDs edge. bx is measured from the W edge, by from the N edge. Board 136 (N-S) × 106 (E-W), holes about 5 mm in, FPGA centre (57.5, 86). **All MEASURE.**
- **Box frame:** origin at the outer NW bottom corner. X runs E, Y runs S, Z runs up from the underside of the floor. **Box = board + (76, 15).** PCB top Z = 19.6, which assumes a 3 mm floor, 15 mm standoffs and a 1.6 mm PCB (MEASURE).
- In box frame: FPGA centre (133.5, 101). Board footprint X 76–182, Y 15–151.

## 2. Overall arrangement
- Outer base: **200 (X) × 184 (Y) × 70 (Z)**. With the lid fitted the box is 76.2 tall (plus rubber feet).
- Wall thickness 3.0 mm and floor thickness 3.0 mm.
- Along X:

  | Zone | X range (mm) |
  |---|---|
  | W wall / panel | 0–4 |
  | Module bay | 4–61 |
  | W gap | 61–76 |
  | Board | 76–182 |
  | E gap | 182–197 |
  | E wall | 197–200 |

- Along Y:

  | Zone | Y range (mm) |
  |---|---|
  | N wall | 0–3 |
  | N gap | 3–15 |
  | Board | 15–151 |
  | S gap | 151–181 (DC plug, JTAG ribbon) |
  | S wall | 181–184 |

- **Cool side = W** (fan inlet and module bay). **Hot side = E** (exhaust). Air crosses the FPGA from W to E.

### Top view (not to scale; numbers are box mm)
```
 Y\X  0  4            61    76                                     182   197 200
   0  +--+-------------+-----+---------------------------------------+-----+--+ N wall (solid v1)
      |  | lid boss o  |     |o(81,20)  7SEG bx5-20   P3 bx46-71  o  |     |  |
  18  |P | PICO 2H     |  W  |(177,20)                 LEDs bx88-97  |  E  |  |
  43  |A | LOGIC ANAL. | gap |                                       | gap |  |
  75  |N | STAR  MAX31855    |                                       |     |E |
  81->|E |  FAN   BME280(up) | P1 x109-114     +-----+     P2 x155-160     |W |
 101->|L | 40mm  Si5351 ~~~~~|>[LEG]===BRIDGE==|HEAT |=============[LEG]  |A |<- exhaust
 121->|  |        (CLK lead to P1-34)          +-----+  FPGA(133.5,101)   |L | slots
 131  |  | 5V-C  AO3400 INA226                     SW(77-85,128-138)|    |L | Y61-141
 148  |  | FUSE  D4184 heater  o(81,146)   AS    [JTAG X132-152]  o |     |  |
 162  |  | 12V   |             +----DC jack--------------------------+     |  |
 176  |  | boss o|             R/A DC plug -> Y<=176    ribbon up/S        o  |
 184  +--+-------+--------------------------------[notch X130-154]---------+--+ S wall
```

### Side section at Y = 101, looking N (W on the left)
```
 Z  76 ===== lid: PETG frame 6.2 + 3 mm acrylic in underside rabbet ==============
    70 ---- wall top = lid underside -------------------------------------------
    65                                   [plunger top]
 51-54      [W leg]=========== BRIDGE Al 20x3 ===========================[E leg]
            |25+20|  FAN 40x40           |ball|
 47.6       |brass|  Z19.6-59.6          [foot 16x16x3]
 44.6       |     |                      [HS10 8.8 tall]
 35.8       |     |   BME280(Z~26)       [Al block 18x18x14]  KSD9700 on S face
 21.3       |     |                      [pad 0.5 / package 1.65]
 19.6       |     |      ===============PCB (1.6)==============
 18         |     |      |15 standoff|      [nylon tip post]     |15|
  6   ======|=====|===== KEEL Al 20x3 on floor ==========================
  3   ---- floor 3.0 ------------- (feet >=5 under) -----------------------
```

## 3. Printed parts (all PETG) and bed fit
The bed is 220 × 220 (MEASURE). The 5 mm margin rule allows a footprint of up to 210 × 210.

| Part | Bounding box (mm) | Margin | Notes |
|---|---|---|---|
| Base tub | 200 × 184 × 70 | 10 / 18 | One piece, printed floor-down. W wall is a frame with a 156 × 64 opening for the panel. |
| Lid frame | 200 × 184 × 10.2 | 10 / 18 | Printed top face down. 3.0 skin, 3.3 underside rabbet, 4 mm locating lip. |
| W I/O panel | 164 × 64 × 3 | flat | Labels engraved on the bed face, so they print crisp. |
| Module plate | 56 × 154 × 6 | flat | 3 mm plate plus 3 mm rails and rest pads. |

Construction details:
- **Inserts.** M3 heat-set holes are Ø4.0 × 6.7 deep in Ø9 bosses (wall 2.5 ≥ 1.6).
  - Base: 4 lid bosses at the inside corners (8, 8), (192, 8), (8, 176), (192, 176), plus 4 floor bosses for the module plate.
  - Lid: 4 short inserts (M3 × 4, 5 mm deep holes) for the window clamps.
- **Clearance holes** are 3.4 mm.
- **If the real bed is smaller than about 210** (MEASURE), set `split_base=True`. The tub then splits at X = 61 into a bay tub (64 × 184) and a main tub (139 × 184), joined by 3 M3 screws through flanges, with 2 printed dowels.

## 4. Board mounting (tolerant of photo error)
- **Standoffs:** 4 × brass M3 F-F, 15 mm (MEASURE; or the board's own). Nominal positions (81, 20), (177, 20), (81, 146), (177, 146).
- **Floor holes are Ø9, not Ø3.4.** Each standoff is clamped by an M3 × 8 button head from below, through an M3 fender washer (OD 12, MEASURE). That gives about ±2.8 mm of slide in X and Y, which covers the "hole pitch might be 2.5 mm off" risk without a reprint.
- The floor underside needs ≥ 5 mm stick-on rubber feet (MEASURE) to clear the screw heads.
- **Clearance to walls and legs** (nominal):

  | Gap | Size | Note |
  |---|---|---|
  | W board edge to W leg | 4.3 mm | Hex across corners 6.35 |
  | E board edge to E leg | 4.3 mm | |
  | Bay edge to W leg | 4.3 mm | |
  | N board edge to N wall | 12 mm | Assumes D-sub overhang ≤ 7, MEASURE |
  | S board edge to S wall | 30 mm | |

- **Measured power path is enforced by geometry.** The USB-B faces the 15 mm W gap, and a USB-B plug cannot physically be inserted there. The board's DC jack is therefore the only usable input. The DPDT stays **up (DC)**. The lid carries an engraved "PWR SEL: UP = DC" next to the switch, which sits at box X 77–85, Y 128–138 and is visible through the window. Pressing the switch simply turns the board off.

## 5. Heater stack and clamp (the core)

### 5.1 Stack from the PCB up (Z values in box frame)

| Layer | Z (mm) | Notes |
|---|---|---|
| Package top | 21.25 | Max A = 1.65 |
| Insulating pad, 0.5 mm silicone, or Kapton + non-conductive paste | 21.25–21.75 | Kapton also wraps the lower 2 mm of the block's edges |
| Spreader block, Al, 18 × 18 × 14, centred on the 20 mm body | 21.75–35.75 | Contact face ≤ 18 × 18 |
| HS10-class resistor (18–22 Ω) on the block top | top at 44.55 | Lug axis runs N-S |
| Pressure foot, Al 16 × 16 × 3, Kapton under it | top at 47.6 | Cut from the 20 × 3 bar, with a drill-point dimple at its centre |

Spreader block details:
- **Thermocouple groove:** 1.2 mm wide on the contact face, from the centre out to the **W** face. Depth = bead Ø − 0.15 (MEASURE). Line it with Kapton.
- **Top:** 2 × M2 tapped holes on the diagonal for the HS10 (F × G = 11.3 × 12.4; the HS10 holes are Ø2.4).

HS10 placement:
- **Lugs N-S.** The lug tips then sit at by 71 and by 101. The lugs are ≥ 14 mm above the PCB and ≥ 12 mm above the lead tops (well over the 5 mm rule). The N lug is about 9 mm from the P3 body.
- **Why not E-W:** that would put the lugs about 4.4 mm from Dupont housings on P1, at the same height.

### 5.2 Thermostat (KSD9700, 75 °C)
The 20.5 × 7.5 × 3.7 body does not fit on the top of an 18 mm spreader that carries the HS10. It therefore goes **on the block's S face, long axis E-W**:
- **Height:** its bottom sits 4.45 mm up the block, which is **6.6 mm above the PCB, about 5.5 mm above the S lead row**. Its top is 2 mm below the block top, so it clears the S lug.
- **Fixing:** one **epoxy-coated stainless cable tie** around the block at mid-height. The tie head goes on the N face, where there is 9 mm to P3.
- **Insulation:** Kapton under the sensing (unprinted) face, plus a Kapton wrap over its back where the tie crosses.
- **Leads** exit at the W end and go up to the bridge (80 mm leads; about 35 mm is needed).

The block height of 14 mm is set only by this placement (see Decisions).

### 5.3 C-frame
- **Bridge and keel:** two identical Al 20 × 3 bars, 133 long, cut from the Bunnings 20 × 3 × 1 m bar. Drill them **as a clamped pair**:
  - leg holes Ø3.4 at 6 and 127 (121 mm span; legs at box X 68.5 and 189.5);
  - a centre hole at the **measured** FPGA X (nominal 71 from the W end): an M6 tap in the bridge, an M3 countersink in the keel.
  - Deflection at 10 N and a 121 mm span is 10·121³/(48·69 000·45) = **0.12 mm** per bar. The frame is far stiffer than the spring, so the force stays where it is set.
- **Legs:** brass M3, 25 + 20 mm, from keel top Z 6 to bridge underside Z 51. They are fixed to the keel by countersunk M3 screws from below, so the keel lies flat, and to the bridge by M3 × 6 screws.
- **Keel location:** the keel is screwed to the floor by 2 × M3 + nut through **floor slots 3.4 × 20 mm (Y 91–111)** at box X 74.5 and 174.5. The **whole clamp line can slide ±10 mm in Y** to follow the measured FPGA Y. The FPGA X is handled by where the bars are drilled.
- **Back-support post:** a brass M3 F-F 6 mm standoff on the keel (countersunk from below), topped by a **nylon M3 × 10 pan screw** locked with a nylon nut. Adjustment is ±1.5 mm.
  - Before the board goes in, set the head top to the same height as the corner standoffs (15.00 above the floor top) with a caliper depth gauge. That gives zero preload, so the PCB is never lifted.
  - The nylon head (Ø ~5.5) is the insulating tip. It must land on bare solder mask: the board's bottom side is MEASURE.
- **Spring element:** a **threaded ball-nose spring plunger, M6 (MEASURE thread, body length and force curve)**.
  - It screws into the tapped bridge with an M6 lock nut on top. The ball sits in the foot's dimple, which centres the force and lets the stack seat flat (a swivel).
  - The plunger body spans Z ≈ 49–65 and the lock nut Z 54–59.
  - **DIY fallback:** M3 screw, stainless compression spring and washer, in the same tapped hole.

### 5.4 Setting the force (5–10 N)
1. On the bench, thread the plunger through a bridge offcut and press it onto a kitchen scale. Record force against turns (M6 pitch 1.0 mm/turn).
2. In the box, back the plunger off. Screw it down until the ball just touches the foot (the foot stops wiggling).
3. Turn it in the number of turns that gave 5–10 N. Lock the nut.

The PCB sees only local compression between the stack and the post. The corner standoffs are unloaded.

### 5.5 Access, removal and refit
- **Removal:**
  1. Loosen the lock nut and back the plunger out 3 turns (force goes to 0).
  2. Remove the 2 bridge screws. The bridge swings aside on its wires.
  3. Lift off the foot, then lift the heater puck (block, HS10 and KSD tied together, TC in its groove) and park it on its wires.
- After that every header pin is open for re-wiring.
- **Refit:** scribed centre lines on the block. Check by eye that about 1 mm of package body shows on all four sides.

### 5.6 Clearance checks (nominal board numbers, photo-estimate ±3)

| Pair | Clearance |
|---|---|
| KSD W end to P1 Dupont housing edge | 9.2 mm |
| KSD E end to P2 Dupont housing edge | 11.2 mm |
| Block, HS10 and foot to P1/P2 | > 10 mm |
| Block W face (TC run) to P1 | 10.4 mm |
| S lug and joint (by ~109) to JTAG box (by 124) | about 15 mm |
| KSD clip (by 100.3) to JTAG box | 23.7 mm |
| Bridge (Z 51) to tops of Dupont housings on P1/P2 (Z ≈ 36, assumes 8.5 mm pins, MEASURE) | 15 mm, for wire bends |
| Bridge (Y 91–111) to JTAG IDC plug (Y 139–147) | 28 mm horizontally |
| Legs | Outside the PCB outline |

## 6. Materials and heat
- No printed part is within 15 mm of the heater. The nearest is the lid underside, Z 70, which is 25 mm above the HS10 top. The bay plate is more than 60 mm away.
- The clamp is aluminium, brass, stainless and nylon. **PLA appears nowhere, and no ASA is required.**
- The acrylic is about 25 mm above the HS10 top. Its plume temperature is unknown, so measure it (see Risks).
- Heater, thermostat and thermocouple wires are silicone, PTFE or glass-braid. They are tied to the bridge with PA66 ties through Ø3 holes drilled every 20 mm.

## 7. Airflow
- **Fan:** 4010, mounted on the panel's inner face.
  - Centre at **(Y 101, Z 39.6)**. Its bottom edge is level with the PCB top, so the jet goes over the board and not under it.
  - Holes at Y 85/117, Z 23.6/55.6 (32 mm pitch). M3 × 16 screws and nuts.
- **Inlet:** panel grille Ø38 with 4 spokes and 2 rings, about 850 mm² open (derived).
- **BME280:** in the jet, about 5–30 mm downstream of the fan face, on 20 mm standoffs (board at Z ≈ 26), lying flat in the stream. It has no line of sight to the heater past P1, the leads and the bridge.
- **Path:** bay, then W gap, then over P1, then over the heater (box X 133.5), then out of **E-wall exhaust slots**.
  - 13 vertical slots, 3 × 36 mm, at 6 mm pitch, Y 61–141, Z 24–60. Total **1404 mm²**, about 1.7× the fan annulus (derived).
  - The slots are vertical so that only their 3 mm tops have to bridge when printed.
- **Leaks are deliberately closed:** no N-wall cut-out in v1, the lid tongue closes the S ribbon notch, and the port holes are small. That keeps the airflow repeatable.
- **Dressing:** dress the logic-analyser leads to P1 along the N side of the jet. Leads hanging in the jet change the flow (see Risks).

## 8. Module plate
The plate is 56 × 154 × 3, at box X 4–60, Y 15–169, top at Z 6. It is held by 4 M3 screws into floor inserts. Positions are nominal and parametric; all generic modules are MEASURE.

| Module | X | Y | Mount |
|---|---|---|---|
| Pico 2H | 4.5–55.5 | 18–39 | 4 × M2 on 10 mm standoffs (header-tail clearance, MEASURE). USB end at the panel. |
| Logic analyser (SparkFun TOL-18627) | 4–59 | 43–71 | 2 printed rails, plus a hook-and-loop strap through 2 plate slots. Probe header faces E. |
| Star ground (lever connector) | 5–25 | 75–89 | 2 tie slots |
| MAX31855 #269 | 37–57.3 | 75–98 | 2 × M2 at the terminal edge (faces E, toward the W leg). Printed rest pad at the header edge. |
| BME280 (PiicoDev) | 20–45.4 | 94–119 | 2 × M2.5 on 20 mm standoffs at its W side (holes MEASURE) |
| Si5351 #2045 | 38–59.6 | 100–130.5 | 2 × M2.5 at the header edge, which faces E toward P1 |
| AO3400 fan switch | 5–30 | 131–146 | M2 or tape (MEASURE) |
| INA226 CJMCU-226 | 33–60 | 131–151 | Nylon standoffs (holes MEASURE) |
| D4184 heater module | 25–60 | 153–169 | 2 × M2 at the signal end (offsets MEASURE) |

Everything except the BME280 stays below Z 20, under the jet.

## 9. Power inlets and every cut-out
**W I/O panel** (drop-in; Y and Z are box values; labels engraved 0.6 deep, 5 mm text):

| Label | Y | Z | Cut-out |
|---|---|---|---|
| PICO USB | 28.5 | 18.4 | 12 × 9 rectangle (micro-B overmould, MEASURE) |
| LOGIC ANALYSER | 57 | 13 | 14 × 8 obround grommet hole. The USB-C plug passes inward. Strain relief is a tie anchor on the plate. Optional TPU bush. |
| AIR IN (arrow) | 101 | 39.6 | Ø38 grille plus 4 × Ø3.4 |
| FPGA 5V IN | 132 | 22 | USB-C power-only panel socket (cut-out MEASURE) |
| HEATER FUSE 1A | 148 | 46 | Panel fuse holder (cut-out and about 40 mm depth MEASURE; sits above the modules) |
| HEATER 12V IN | 162 | 22 | 5.5 × 2.1 jack. Ø8.0 (Altronics P0622) or Ø13 (P0628), max panel thickness MEASURE |

Power-path notes:
- The two inlets are **different connector families** (USB-C and barrel), so they cannot be swapped.
- **5 V path:** USB-C → INA226 IN+ → shunt → IN− (VBUS jumpered to IN−) → right-angle DC plug into the board jack (box X 85–95, mouth at Y 151, plug ≤ 25 long, MEASURE). The plug is tied to a floor tie slot at (75, 165).
- **12 V path:** jack → fuse → up the W leg → along the bridge → thermostat → HS10 → back along the bridge → D4184 → 12 V −.

**Other walls:**
- **S wall:** an open-top **"JTAG"** notch, X 130–154, Z 40–70. The lid's tongue (23.2 wide) drops in and presses the ribbon onto a foam strip. The tongue bottom = notch bottom + ribbon thickness + foam (parametric).
- **E wall:** "EXHAUST" slots, as in §7.
- **N wall:** solid in v1. A "VGA · RS-232" slot (X 98–168, Z 17–36) is a parameter flag.

**Lid top:** engraved "LYCOCHIP · AGENT LAB BOX" over the bay, plus a module legend and "PWR SEL: UP = DC".

## 10. Lid and window
- **Lid frame:** 200 × 184.
- **Window opening:** X 77–177, Y 14–150. That shows bx 1–101 and by −1…135, which includes the 7-segment display (bx 5–20, by 19–50), LED1–4 (bx 88–97, by 54–62), the keys, the FPGA, the clamp and the JTAG header.
- **Acrylic:** 110 × 146 × 3, cut from Altronics H0725 (199 × 199) with two score-and-snap cuts. It sits in an underside rabbet (111 × 147 × 3.3; acrylic thickness MEASURE). It is held by 4 M3 × 6 screws whose washers (OD 7) overlap its edge, screwed into lid inserts.
- **Fixing:** the lid locates with its 4 mm lip and is held by 4 × M3 × 10 into the corner bosses (thumb screws optional). The rabbet is ≥ 5 mm from the bosses.
- **Height check against the lid underside (Z 70):**

  | Part | Top (Z) | Margin (mm) |
  |---|---|---|
  | Plunger | 65 | 5 |
  | Fan | 59.6 | 10.4 |
  | Fuse holder | about 56 | 14 |
  | Bridge nut | 59 | 11 |
  | Ribbon bend (box header 9.3 + IDC plug + bend, MEASURE) | about 45 | 25 |
  | Switch cap, worst case | 44.6 | 25.4 |

## 11. Cable routing
- **JTAG:** the IDC plug stays seated on the board permanently. The ribbon goes up, then S, out through the notch. The Blaster sits outside the box.
- **Logic analyser:** leads leave its E end, cross the W gap and drop onto P1/P2/P3, routed along the N part of the board.
- **Si5351:** a twisted pair, CLK0 plus module GND, about 60–80 mm, crosses the W gap at Z ≈ 25–30, under the bridge. CLK goes to P1-34. GND goes to P1-1/2, which may be 40 mm along P1 depending on which end pin 1 is (continuity check first). It is kept ≥ 20 mm from the heater wires.
- **Heater and thermostat:** on the bridge's **N edge**.
- **Thermocouple:** on the bridge's **S edge**, from the block's W face. Both then go down the W leg (tied) to the D4184 and the MAX31855 respectively.
- **Fan:** to the AO3400. Power the fan from the Pico's VBUS, never from the board header 5 V.

## 12. Assembly order
1. Print a heat-set insert coupon. Then print the base, panel, plate and lid. Fit the inserts.
2. Measure the board (§13), then set the parameters.
3. Cut the bars and drill them as a pair (legs at 6/127, centre at the measured FPGA X). Tap M6 in the bridge. Countersink the keel. Make the block (cut, face, tap 2 × M2, groove) and the foot.
4. Fit the keel to the floor, with the post (height-set) and the legs.
5. Place the standoffs (fender washers), lower the board between the legs and tighten.
6. Fit the pad, thermocouple bead (Kapton), block, HS10 (paste) and KSD (Kapton plus tie). Sleeve the lugs.
7. Fit the foot, bolt on the bridge, and set the plunger force (§5.4).
8. Mount the modules on the plate and screw the plate down. Build up the panel (jacks, fuse, fan) and drop it in.
9. Wire everything. Seat the ribbon in the notch.
10. Fit the acrylic to the lid, then fit the lid.

## 13. New MEASURE placeholders this concept introduces
- `PLUNGER_THREAD`, `PLUNGER_BODY_LEN`, `PLUNGER_BALL_PROTRUSION`, `PLUNGER_FORCE_VS_TRAVEL`
- `BLOCK_STOCK` (20 mm square Al bar: source and size)
- `FENDER_WASHER_OD`, `FOOT_HEIGHT`
- `LEG_STANDOFF_LENGTHS` (25 + 20), `POST_STANDOFF_LEN` (6), `BOARD_STANDOFF_LEN` (15)
- `PCB_BOTTOM_UNDER_FPGA` (post landing area)
- `RA_DC_PLUG_LEN` (≤ 25), `IDC_PLUG_RIBBON_Z`, `RIBBON_T`
- `PICO_USB_OVERMOULD`, `LA_USBC_OVERMOULD`, `LA_USB_Z`
- `INLET_5V_CUTOUT`, `FUSE_HOLDER_CUTOUT_DEPTH`, `JACK12_HOLE_AND_PANEL_T`
- `DSUB_N_OVERHANG` (≤ 7), `USBB_W_OVERHANG`
- `KSD_LEAD_EXIT_END`, `HS10_LUG_Z`, `TIE_WIDTH`
- `ACRYLIC_T`, `PRINTER_BED_XY`
- BME280, INA226, D4184 and AO3400 hole positions; star connector size

## 14. Main risks (short)
The full list is in `risks`. In brief:
- A 14 mm block makes settling slower.
- The bottom side under the FPGA is unknown.
- The 200 mm base is near the bed limit.
- Plunger force is unknown.
- Airflow repeatability depends on how the leads in the jet are dressed.
- The thermostat sits only about 5.5 mm above the S lead row.


## Printed parts

| Part | Material | BBox (mm) | Fits 220 bed | Notes |
|---|---|---|---|---|
| Base tub (floor + 4 walls; W wall is a frame with grooves for the drop-in panel) | PETG | 200 x 184 x 70 | True | 10 mm margin in X and 18 mm in Y on a 220 bed. Printed floor-down with no supports. Walls and floor 3.0 mm. 4 corner lid bosses (Ø9, M3 insert 4.0 x 6.7) and 4 floor bosses for the module plate. Ø9 floor holes for the board standoffs (fender washer, ±2.8 mm adjust). Two 3.4 x 20 floor slots for the keel (±10 mm in Y). 13 vertical E exhaust slots, 3 x 36. Open-top JTAG notch in the S wall (X 130-154, Z 40-70). Tie slots in the S gap. Not in the heater zone: the floor is 15 mm below the PCB and carries no clamp load. Fallback split_base=True at X=61 if the real bed is under about 210. |
| Lid frame with window rabbet, locating lip and ribbon tongue | PETG | 200 x 184 x 10.2 | True | Printed top face down, so there are no overhangs. 3.0 skin, 3.3 deep underside rabbet for 110 x 146 x 3 acrylic (window opening X 77-177, Y 14-150), 4 mm lip. 4 x M3x4 inserts for washer clamps. Tongue drops into the S notch to clamp the ribbon. Engraved title, legend and 'PWR SEL: UP = DC'. Underside is 25 mm above the HS10 top. |
| W I/O panel (drop-in, captured by lid lip) | PETG | 164 x 64 x 3 | True | Printed flat with labels engraved on the bed face. Carries every connector: PICO USB, LOGIC ANALYSER grommet hole, fan grille plus 4 holes on a 32 mm pitch, FPGA 5V IN (USB-C), HEATER FUSE 1A (panel holder), HEATER 12V IN (5.5x2.1). This is the only part to reprint when connector measurements change. |
| Module plate | PETG | 56 x 154 x 6 | True | 3 mm plate plus 3 mm rails and rest pads. M2/M2.5 holes for the Pico (47 x 11.4 pattern), MAX31855, Si5351 and BME280 standoffs. Logic-analyser cradle rails and strap slots, tie slots. 4 x M3 into floor inserts. Cool zone, more than 60 mm from the heater. |
| Optional: bridge/keel drilling jig | PETG | 150 x 30 x 15 | True | Clamps both 133 mm Al bars together so the leg holes (6/127) and the centre hole line up. Not structural. |

## Decisions for Alex

- Thermostat placement sets the box height. Option (a), as briefed: KSD9700 on the spreader's S face. The block must then be 14 mm tall to keep the thermostat 5.5 mm above the lead row. That adds about 11 J/K, so settling is slower. Option (b): KSD on the HS10 housing. The block drops to 6 mm, the box gets about 8 mm lower and settling is faster, but the thermostat trips earlier, so 75 vs 80 C has to be re-checked.
- Force element. A commercial M6 ball-nose spring plunger is one part, but its force-vs-travel curve is unknown until measured on a kitchen scale and it may be too stiff. The alternative is a DIY M3 screw + stainless compression spring + washer: the force is easier to choose, but it has more loose parts. Either one costs money.
- 5 V inlet connector family. Option 1: a USB-C power-only panel socket fed from a USB-C wall charger. It is ubiquitous, cannot mate with the 12 V barrel, and needs a new charger. Option 2: a locking 2-pin panel connector (e.g. GX12) on a 5 V barrel adapter whose plug is cut off. It is more robust but uglier.
- VGA/DB9 access. v1 keeps the N wall solid so airflow stays repeatable. The slot (X 98-168) is a parameter flag that can be switched on once the D-sub positions and overhang are measured. Turning it on adds a leak, or needs a blank.
- USB-Blaster: outside the box with the ribbon through the S notch (simplest), or in an internal bay in the S gap. The internal bay is tidier, with all host cables on the W panel, but it needs the Blaster's body dimensions and ribbon length.
- Window extent: board only, with the bay hidden under an opaque frame carrying an engraved module legend (this concept), or a full-interior window that shows the modules. That needs a 190 x 178 acrylic piece and moved lid screws.
- Logic analyser cable: grommet hole (works with any analyser case; this concept) or a direct panel USB-C port (neater, but the analyser case must be measured first).
- Lid fastening: 4 x M3 screws into inserts (as in the brief), knurled M3 thumb screws, or glued-in magnets. The last two allow tool-free access for re-wiring.
- Base print: one 200 x 184 x 70 piece if the printer really prints 210+ mm, otherwise split_base at X = 61 (2 parts + 3 screws). Which printer is it?

## Risks

- Bottom side under the FPGA is unknown. The nylon post tip (about Ø5.5) may have nowhere to land if decoupling caps or vias fill that area. The fallback is two posts either side of the package, or a forked tip, which needs a new keel hole.
- A 14 mm aluminium block roughly doubles the local heat capacity versus an 18x18x2 spreader (about +11 J/K, derived). Settling (3τ) may grow by about 1.5x. The thermostat on the block's side also reads cooler than the HS10, so its trip point relative to the package must be measured in place.
- The thermostat sits only about 5.5 mm above the S lead row and is held by one coated stainless tie. If the tie slips the case could drop toward the leads. It is Kapton-wrapped, but check the tie tension and look at it after each heat cycle.
- Spring-plunger force is unknown. Many ball plungers are stiffer than 10 N even at small travel. If so, use the DIY spring fallback.
- The 200 x 184 base is near the limit of a 220 bed (10 mm margin in X). Some '220' printers have a smaller true area, and a large PETG box can warp or lift at the corners. split_base is the fallback.
- Airflow repeatability: logic-analyser leads on P1 sit in the fan jet upstream of the FPGA. Moving them changes the flow and so the heater power and the top-vs-Tj offset. Leads need fixed routing (N side) between runs.
- Board outline and hole-pitch errors larger than the ±2.8 mm floor-hole slack, or a D-sub overhang past the N edge larger than 7 mm, would force a base reprint, which is the longest print. Measure before printing the base.
- The acrylic window is about 25 mm above the HS10 top, and the plume temperature there is unknown. Log the air under the lid at a 60 C hold before leaving it running unattended.
- The Si5351 lead is 60-80 mm, and its ground return to P1-1/2 may run 40 mm along the header. The low-side logic margin is only 0.2 V, so check edges with the logic analyser and keep the pair twisted.
- Removing and refitting the heater puck relies on visual centring (about 1 mm margin per side to the body edge). The lower block edges must keep their Kapton wrap in case of mis-centring.
