# Concept: Glass-Top Lab Bench (demo-first)

> Design-panel concept (demo-first), 2026-10-23. Input to DESIGN.md, not the design itself.

**A 196 x 178 x ~85 mm desk instrument whose whole top is an acrylic window. The FPGA board sits right of centre, a labelled module tray runs down the left, and an orange hinged heater arm on an ASA C-frame reaches over the chip. Air enters the left wall and leaves the right wall past the heater, every cable plugs in at the back through replaceable I/O plates, the front face carries only the nameplate, and every printed part fits a 220 bed in one piece.**

# Concept: Glass-Top Lab Bench (demo-first)

**The idea.** The visitor stands at the **S (front)** face and looks down through a window that covers about 82 % of the top. From left to right they see:
- the "lab": a module tray with an engraved label beside every knob and eye;
- an **orange heater arm** reaching in from the left over the FPGA;
- the board's 7-seg display and LEDs.

Air goes in through the left wall and out through the right. **Every cable plugs in at the back (N)** through replaceable I/O plates, and the front carries only the nameplate.

Colour coding: orange ASA = heat, blue = air, dark-grey PETG shell, black bezel.

## 1. Frame and key numbers

**Box frame = board frame** (board-mechanical.md):
- X runs from the board's W edge, positive toward E.
- Y runs from the board's N edge, positive toward S (toward the visitor).
- Z runs up from the inside floor surface.

The board occupies X 0..106, Y 0..136, and the FPGA centre is at (57.5, 86). **All of these are MEASURE and parametric** (BOARD_W/L, HOLE_INSET 5, HOLE_PITCH 96x126, FPGA_X/Y, P1_X, P1_PIN1_END, STANDOFF_L, PCB_T).

| Item | Value |
|---|---|
| Outer | X -79..117 (196), Y -9..169 (178), Z -3..78.6, plus feet ≈ 85 mm |
| Interior | X -76..114 (190) by Y -6..166 (172). Floor top Z 0, lid underside Z 70.6 |
| Board to wall | W: 68 mm tray bay + 8 mm gap. E: 8. N: 6. S: 30 (front gallery) |
| Walls / floor | 3.0 / 3.0 mm, thinned to 2.5 mm only on the I/O plates |
| PCB | bottom Z 16.0, top Z 17.6 (1.6 mm, MEASURE) |

All photo-estimate collisions keep at least 5 mm of margin: board to walls, the arm to the JTAG plug, and the stack to the headers.

## 2. Top view (about 3 mm per character across, 6 mm per line down)

```
X: -79        -43       -8 0                  57.5          106 117
+================================================================+  Y=-9  N wall (back): I/O plates
# +------++--------+                                             #
# |PICO  ||LOGIC   |+--+  +-------+---------------------+-----+  #  Y=0   board N edge (DB9|VGA X24-90)
# |CTRL  ||ANALYSR ||FU|  |       +---------------------+     |  #
# |      ||8-CH    ||SE|  |                                   |  #
# |      ||        ||  |  | +----+                            |  #
# |      ||        ||  |  | |7SEG|                            |  #
# |      ||        ||  |  | |    |                         keys  #
# |      ||        ||  |  | |    |                            |  #
# +------+|        |+--+  | |    |                            |  #
#         +--+---------+  | +----+                      +--+  |  >  Y=50
#            |CLOCK    |  |                          ++ |LE|  |  >
>+--+        |Si5351 N |  |          +-+             || +--+  |  >
>|D +---+    |         |  |          |P|             ||       |  >   (P2 = the || column, X~81)
>|U |F  |   +MAST/ARM---+ |          |1|  +------+   ||       |  >
>|C |A  >>  |           | |          | |  |      |   ||       |  >
>|T |N  |   |   o=============================@  |   ||       |  >  Y=86  arm; plunger @ (57.5,86)
>|BM|   >>  |           | |          | |  FPGA   |   ||       |  >
>|  |   |   ++---------++ |          | |  +------+   ||       |  >
>|  |   |    |CLOCK    |  |          | |             ||       |  >
>+--+---+    |Si5351 S |  |+-+       +-+             ++       |  >
# +-----+    |         |  ||S|---+                            |  >
# |CHIP | +-----++------+ |+-+DC |  +------+ +------+         |  #
# |TEMP | |STAR ||AIR   | |  |   |  |AS    | |JTAG  |         |  #
# |MAX  | +-----+|DRV   | +--+---+--+------+-+------+---------+  #  Y=136 board S edge
# +----------++--------++           +------------------------+   #
# |HEAT DRV  ||POWER   |     plug   |USB-BLASTER dongle zone |   #
# |D4184     ||INA226  |            |(front gallery)         |   #
# +----------++--------+            |                        |   #
+===================================+------------------------+===+  Y=169 S wall (front): nameplate only
 '>' on W wall = intake slots, '>' on E wall = exhaust slots, 'o' = arm hinge, '@' = plunger
```

## 3. Side section at Y = 86 (vertical not to scale)

```
 Z
78.6 +==================================================================+ bezel 3 on lid ring 5, acrylic 3 in pocket
70.6 +---- lid underside = PCB+53 -------------------------------------+
65.4 |                                              [#] preload screw + jam nut (PCB+47.8, tallest)
60.0 |      +--o hinge X-32 Z53.6 ---- ARM 16 x 12 ASA ------[ B ]     |
47.6 |      |  |<- mast fin                                 [ A ]     | arm underside PCB+30
41.6 |>FAN>>|  |                                            [ R ]     | barrel bottom PCB+24
37.6 |      |  |                                       cap   =!=      | stack top PCB+19.95
36.0 | duct |  |                                      HS10  [###] K   | KSD on angle leg, Z 30.6-38.1
27.3 | BME  |  |                     P1 pins          angle =======S   | HS10 base PCB+9.65
25.3 |      |  |                       ||              foot  [##]  D   |
17.6 |tray  |  |   ====================||======= PCB ====[FPGA]==========  PCB top
16.0 |Z5-8  |  |                                        post   I       | 10 mm standoffs at corners
 8.0 |      |  +-------------- SOLE 30 x 8 (ASA) -------------+        |
 0.0 +==================================================================+ floor 3, feet below
X:  -76  -66 -36 -8 0                35                  57.5        106 114
```

## 4. Board mounting

- **Standoffs:** 4 x M3 brass F-F hex, 10 mm (Harwin R30-1011002 class, 5.5 A/F). They sit on Ø8 x 6 mm floor bosses with M3 x 5.7 inserts. The insert hole is Ø4.0 x 6.7, and floor plus boss is 9 mm, leaving a 2.3 mm skin. The board is fixed with M3 x 6 screws from above.
- **Reusing the vendor parts:** if the vendor's brass standoffs are M3 x 10, reuse them. Remove the vendor acrylic plates.
- **USB-B socket:** a printed flush blank plug with an upward pull tab, labelled `NOT USED - 5V ARRIVES METERED VIA DC JACK`.
- **Power switch:** stays UP, which selects the DC jack. Pressing it only switches the board off, because the USB-B is blanked. There is no unmetered path.

## 5. Heater stack (metal on the package)

Heights are above the PCB top, using worst-case tolerances.

1. **Insulation:** 50 µm Kapton plus non-conductive paste on the 18 x 18 contact face, with Kapton wrapped up the sides of the foot. Alternative: a 0.5 mm TP-3 pad, slotted along the thermocouple groove. Top of this layer: PCB+2.15.
2. **Foot:** Al 18 x 18 x 5.5, centred on the 20 x 20 body (1 mm margin). Its top is at PCB+7.65.
   - Thermocouple groove in the bottom face, running from the centre to the W edge. Width = bead Ø + 0.3, depth = bead Ø - 0.15 (bead MEASURE). The groove is Kapton-lined, and the bead touches the package top through paste.
   - 2 x M3 tapped holes at (0, ±5), plus 2 x M2 on the HS10 hole pattern (11.3 x 12.4 diagonal).
3. **Angle:** Al equal angle 20 x 20 x 2, 28 long in the N-S direction.
   - The horizontal leg bolts to the foot with 2 x M3 countersunk screws and paste. It overhangs the body 4 mm to N and S only, at ≥ PCB+7.65, which keeps it 6.0 mm above the leads (5.35 with minimum tolerances).
   - The vertical leg sits on the E side, trimmed to 13 tall (top at PCB+20.65).
4. **HS10, 18-22 Ω, lugs pointing N-S:** base at PCB+9.65.
   - Lug tips land at Y 71 and Y 101: more than 8 mm above the leads and 10.2 mm from P3's inner row.
   - Lugs pointing E-W would leave only 5.7 mm ±3 to P1, so that orientation was rejected.
5. **KSD9700, 75 °C:** clamped to the vertical leg's E face, unprinted (sensing) face inward, with Kapton between.
   - Held by an FR4 strap (26 x 6 x 1.6) with 2 x M2 at Y ±12.
   - Position: X 68.0..71.7, Z PCB+13..20.5. That is 8.5 mm from P2's inner row and 11 mm above the leads.
6. **Pressure cap:** Al 16 x 16 x 1.5 resting on the HS10 fins, with a Ø3 x 90° centre countersink. Top at PCB+19.95.

## 6. Heater clamp: hinged arm on a C-frame

**Clamp frame (one ASA print):**
- **Foot:** X -43..-8, Y 76..96, on the floor.
- **Mast fin:** X -36..-8. It is 16 thick up to Z 47.6, where it forms shoulders, then 8 thick up to Z 59.6.
- **Sole:** X -8..66, Y 71..101, 8 tall, running under the PCB with 8 mm of vertical clearance (at least 5 mm over THT tails assumed ≤ 3 mm, MEASURE).
- **Back-support post:** sits on the sole directly under the plunger.

The force loop is plunger → stack → package → PCB → post → sole → mast → arm. The frame is self-equilibrating and is bolted to the base, so the base reacts it and locates it. Neither the PCB span nor the floor carries clamp load.

**Floor fixing and XY adjustment:**
- 2 floor bosses with M3 inserts stand inside ±5 mm cross-slots in the foot. M3 screws with fender washers clamp the foot.
- This gives the XY adjustment needed for the ±4 mm FPGA photo-estimate.

**Arm (ASA, 16 W x 12 D, X -38..64.5):**
- Underside at Z 47.6 (PCB+30), top at Z 59.6.
- The root forks around the fin. The hinge is an M3 x 20 pin at (X -32, Z 53.6).
- The latch is a knurled M3 pin at X -14 through both ears and the fin. Its shear load is 10 x 89.5 / 18 ≈ 50 N (derived).
- The lowered position is set by the ears resting on the fin shoulders, not by the latch.

**Plunger barrel at the arm tip:**
- Ø14, Z 41.6..60.0, axis at X 57.5.
- Bottom lip 1.5 mm thick with a Ø3.4 hole, and a Ø6.0 bore above it.
- The plunger is an M3 socket-head screw (head Ø5.5 x 3) guided in the bore. The shank goes down through the lip, and an M3 acorn nut (MEASURE) forms the domed contact.
- A compression spring sits on the head. Above it, an M3 preload screw runs in a captive M3 nut, with a jam nut on top.
- When engaged, the head lifts about 2 mm off the lip.

**Spring (select, then MEASURE):** OD ≤ 5.6, L0 ≈ 10-12, k ≈ 1.5-2 N/mm, solid length ≤ 4. That gives about 8 N at an installed length L_i ≈ 6.

**Setting the force:**
1. Measure k on a kitchen scale.
2. Compute L_i = L0 - F/k.
3. Turn the preload screw until the spring's top washer reaches L_i. Read it through a 3 x 8 mm slot in the barrel engraved with 1 mm ticks (the "force window").

Two derived effects on the force:
- Stack tolerance of ±0.35 mm gives ±0.7 N.
- Frame compliance is about 1.4 mm at 10 N (assumed ASA E ≈ 2 GPa) and acts in series with the spring. Re-check the force after a 24 h soak.

**Removing it for access:**
1. Pull the latch pin.
2. Tilt the arm up about 100°. The wires have a 40 mm service loop at the hinge.
3. Lift the stack off; it stays on its own leads.

The preload is untouched, so the force returns unchanged.

**Refitting:** place the foot by eye (1 mm margin per side) and lower the arm. The dome drops into the countersink and centres the stack.

**Clearances:**
- The arm band covers Y 78..94 at ≥ PCB+30. The JTAG box (Y ≥ 121 worst case) is 27 mm south of it.
- P2 is never crossed.
- P1 is crossed at PCB+30. Dupont leads on P1 rows under the arm are fine only if their wires leave toward W below PCB+25. No hook grabbers on P1 rows Y 74..98.
- The barrel bottom clears the cap by 4.05 mm and the KSD/angle by 3.35 mm.

**First alignment:**
1. Install the board and place the stack by eye.
2. Loosen the frame's foot screws and latch the arm. The dome pulls the frame into line.
3. Tighten the foot screws.

## 7. Back-support post

- **Post:** M3 brass screw threaded up through an M3 insert in the sole, with a jam nut. A nylon acorn cap (MEASURE) forms the insulating tip on bare solder mask.
- **Five insert sites:** the centre and ±6 mm in X and in Y, so the post can dodge unknown bottom-side parts. A 6 mm offset adds only about 60 N·mm of local moment (derived).
- **Height:** ±3 mm by thread, plus FR4 or Kapton shims.
- **Adjustment:** from below, through a 22 x 22 floor access hole (X 46.5..68.5, Y 75..97) closed by a plug labelled `CLAMP POST ADJ`.
  1. Lift the arm.
  2. Raise the post until it just grips a sheet of paper against the PCB.
  3. Lock the jam nut.

## 8. Airflow

1. **Intake:** W wall, Y 62..112, Z 8..64, 10 vertical slots 3 x 56 mm = **1680 mm²**.
2. **Plenum:** a blue PETG duct, X -76..-66, 10 mm deep. The BME280 hangs vertically inside it (Z 2..27) behind a solid lower shield panel, so it has no line of sight to the heater.
3. **Fan:** 4010 on the duct's E face, Y 68..108, Z 24..64, centre Z 44 ≈ PCB+26. Fixed with M3 into inserts (Sunon holes Ø4.3, Core 4 mm: MEASURE).
4. **Across the box:** over the tray (modules ≤ Z 25), past the mast fin and arm (both edge-on to the flow, about 20 % blockage), then over P1, the heater stack and P2/SDRAM.
5. **Exhaust:** E wall, Y 50..120, Z 20..66, 14 slots 3 x 46 mm = **1932 mm²**.

**Vent sizing:** the fan's free area is about 957 mm², derived from an assumed Ø38 bore and Ø15 hub (MEASURE). That makes the intake about 1.75x and the exhaust about 2.0x the fan area.

**Pressure:** the box runs at positive pressure, so the I/O plates only leak inlet air outward. The fan only ever sees inlet air, which matters because it is rated to 70 °C.

## 9. Module tray (one PETG plate, X -75.6..-8.4, Y -5.6..165.6, 3 mm thick)

The tray sits on six 5 mm floor bosses (tray at Z 5..8), so cables run underneath it. It is notched around the duct and the clamp foot, and there is an engraved label beside every module.

| Module / tray label | Footprint (source) | X | Y | Notes |
|---|---|---|---|---|
| Pico 2 `CONTROL` | 51x21 (datasheet) | -74..-53 | -5.5..45.5 | 4 x M2 on 47x11.4, 4 mm bosses; micro-B centre Z 14.4 |
| Logic analyser `LOGIC 8-CH` | 54.7x27.4x14.1 TOL-18627 / 56x27.6x20.3 clone (listing) | -50..-22 | -5.5..50 | strap + backstop rib; USB end N, probe end S |
| Inline 3AG holder `FUSE 1A` | S6001 (listing) | -19..-10 | 0..45 | 1 A fast for 18 Ω |
| Si5351 `CLOCK`, N site | 30.48x21.59 (#2045) | -40..-9.5 | 52..73.6 | used if P1 pin 1 is at S (P1-34 ≈ Y 68) |
| Si5351, S site | same | -40..-9.5 | 100..121.6 | used if pin 1 is at N (P1-34 ≈ Y 104) |
| MAX31855 `CHIP TEMP` | 20.32x22.86 (#269) | -74..-53.7 | 116..138.9 | kept out of the fan footprint |
| Opto D4184 `HEAT DRIVE` | 35x16x14 (listing) | -74..-39 | 143..159 | hole offsets MEASURE |
| Star ground `STAR GND` | lever block ≤ 20x13 (MEASURE) | -50..-30 | 125..138 | |
| AO3400 driver `AIR DRIVE` | ≤ 20x16 (MEASURE) | -28..-8 | 124..140 | |
| INA226 `BOARD POWER` | 20x27 CJMCU (listing) | -36..-9 | 142..162 | 40 mm pigtail to the board jack |
| BME280 `AIR TEMP` | 25.4x25.4 PiicoDev (listing) | -75..-68 (in duct) | 63..88 | vertical card |

An overlap check found no collisions. The tightest gaps are 2 mm.

## 10. Inlets and every wall cut-out

| Wall | Opening, position | Label |
|---|---|---|
| N (back) | POWER plate, aperture 56x24, X -62..-6, Z 38..62 | Over the 5 V inlet (X -48, Z 50): `FPGA 5V · USB-C · POWER ONLY · METERED`. Over the 12 V jack (X -18, Z 50): `HEATER 12V · 5.5x2.1 · 1A FUSE INSIDE` |
| N | DATA plate, aperture 54x18, X -74..-20, Z 6..24 | `PICO · CONTROL` (micro-B flush at X -63.5, Z 14.4). `LOGIC ANALYSER` (port position MEASURE) |
| N | RS-232/VGA aperture 66x20, X 24..90, Z 14..34 | blank plate `RS-232 · VGA (OPTIONAL)` |
| N | JTAG plate, X 104..114, Z 2..18, with a 2-piece printed cable clamp | `JTAG · USB-BLASTER` |
| W (left) | intake slot field | embossed `AIR IN ->`, `AMBIENT SENSOR` |
| E (right) | exhaust slot field | embossed `AIR OUT · WARM` |
| S (front) | none | Embossed `LYCOCHIP AGENT LAB` (10 mm text) and `KNOBS: HEAT · AIR · CLOCK   EYES: CHIP TEMP · AIR TEMP · POWER · LOGIC` (4 mm) |
| Floor | post access 22x22 | `CLAMP POST ADJ` |

**Why plates:** each I/O plate is a separate 2.5 mm print screwed into a rebated aperture. A wrong port position or panel thickness (all MEASURE) then costs a reprint of the plate, not the base. Connectors are screwed to plates or modules, so plug force never reaches a solder joint.

**5 V and 12 V cannot be swapped:** the 5 V inlet is USB-C and the 12 V inlet is a 5.5x2.1 barrel jack. Neither plug fits the other inlet, in either direction.

## 11. Lid and window

- **Lid ring (PETG):** 196x178x5, plus a 3 mm locating skirt (2 mm thick, 0.4 mm clearance inside the walls).
  - The pocket for the sheet is 184.6x166.6x(t+0.2).
  - The ledge opening is 172x154 (X -67..105, Y 3..157).
- **Acrylic:** 184x166x3, cut from a 199x199x3 sheet (Altronics H0725, listing). Sheet thickness is MEASURE.
- **Bezel:** 196x178x3 in a contrasting colour, with the same opening. It clamps the sheet over a 6 mm band and is held to the ring by 4 x M2.5 self-tappers, so the lid stays one unit off the box.
- **Lid to base:** 6 x M3 x 16 through bezel and ring into inserts in gusseted hanging bosses (Ø8 x 10, Z 60.6..70.6). The bosses are at the 4 corners and at X 19 on the N and S walls.
- **Engravings on the bezel:**
  - Front border: `LYCOCHIP · AGENT LAB BOX · MVP`.
  - Edge pointers: `CONTROL`, `LOGIC`, `CLOCK`, `AIR IN`, `HEAT ARM`, `FPGA EP4CE6`, `LEDS`, `AIR OUT`, `JTAG - UNPLUG 5V FIRST`.
- **Height check:** the window sits 38 mm above the stack top. The lid underside clears the tallest part (the preload screw at Z 65.4) by 5.2 mm.
  - Switch cap ≤ PCB+25: clear.
  - JTAG plug plus ribbon, budgeted at PCB+30: clear.

## 12. Cable routing

- **JTAG.**
  - The IDC plug stays in permanently (vendor hot-plug warning).
  - The ribbon rises to ≤ PCB+30, folds south over the board edge, and drops into the front gallery to the dongle zone (X 30..104, Y 140..164). The ribbon must be ≥ ~60 mm (MEASURE).
  - The dongle's USB cable runs east along the gallery floor, then north in a clipped floor channel in the E gap (X 107..113, Z 0..8), and out through the JTAG clamp, with an internal tie anchor.
- **Logic-analyser leads.**
  - From the analyser's S-end probe header to a printed comb in the tray/board gap (X -8..0). The comb has two positions, Y 54..72 or Y 98..112, chosen by P1_PIN1_END.
  - From the comb to P1 rows at the pin-1 end, with GND on P1-1/2.
  - Leads stay below PCB+25 and never under the arm.
- **Si5351 lead.**
  - Twisted pair (CLK0 + GND), about 60 mm, from the active site's header edge to P1-34.
  - It plugs in through a printed ASA `CLK IN` key shroud over P1-31..38 that leaves only pin 34 open. This matters because P1-35..38 carry 3.3 V and 5 V.
  - GND goes to P1-1/2, which are P1's only GND pins.
  - Optional 33 Ω series resistor at the Si5351 end (clock-pins.md).
- **Heater, thermostat and thermocouple.**
  - All leave the stack upward: the HS10 lugs at N and S, the KSD leads from its N end, and the thermocouple from the foot's W face.
  - They run in a snap-cover channel on top of the arm, then down the mast's W face with a 40 mm hinge service loop, then under the tray to the D4184, the fuse and the MAX31855.
  - Spare thermocouple length is coiled in the harness zone (X -64..-44, Y 64..114) behind a tie anchor, so no pull reaches the groove.
  - Within 15 mm of the stack, all wire is silicone, PTFE or glass-braid.
- **12 V path:** jack → fuse → under the tray → mast → arm → KSD → HS10 → D4184 LOAD. D4184 "−" returns to the jack's "−".
- **5 V path:** USB-C inlet → pair under the tray → INA226 IN+ → shunt → IN− (with VBUS) → right-angle plug (MEASURE) into the S-facing board jack at X 9..19.

## 13. Assembly order

1. Print an insert test coupon and a **1.2 mm board gauge** (holes, FPGA, P1/P2/JTAG outlines). Lay the gauge on the real board and update params.
2. Fit the base inserts, I/O plates and panel parts.
3. Fit the duct with the fan and the pre-wired BME280.
4. Bench-wire the tray, drop it in, and align the ports with the plates.
5. Fit the clamp frame loosely, with the post backed off.
6. Fit the standoffs, the board, the USB-B blank and the DC pigtail.
7. On the bench, assemble the stack, with continuity checks: thermocouple isolated, KSD case, HS10 isolation.
8. Place the stack, latch the arm, and tighten the frame.
9. Set the post from below.
10. Set the force.
11. Route the wires.
12. With the board unpowered, plug in the JTAG and route the dongle cable.
13. Fit the Si5351 lead with its shroud, and the analyser leads through the comb.
14. Fit the lid.

## 14. New MEASURE placeholders

- USB-Blaster dongle size and ribbon length.
- IDC plug plus ribbon-bend height (budgeted at PCB+30).
- Right-angle board-jack plug length (budgeted at ≤ 20).
- Dupont housing height. Wires under the arm must stay at or below PCB+25.
- P1 pin-1 end. This picks the Si5351 site and comb position.
- Board underside: THT tails ≤ 3 mm assumed along the sole, and a bare-mask spot for the post.
- Spring k, L0, OD and solid length. M3 acorn-nut height.
- Thermocouple bead diameter.
- HS10 as bought: lug height, base width, and envelope. Only 0.25 mm separates the envelope from the angle's leg.
- Aluminium stock (18 mm bar, 20x20x2 angle).
- USB-C inlet: outline, holes, and whether 5.1 kΩ CC pull-downs are fitted.
- 12 V jack: hole size and maximum panel thickness.
- Analyser port position. Pico micro-B plug overmould.
- Fan bore and hub size.
- Sizes of the lever block, fan driver, D4184, INA226 and PiicoDev holes.
- Acrylic sheet thickness.
- Rubber feet.
- ASA creep: clamp force after a 24 h soak.
- Direction the 7-seg digits read.

## 15. Main risks

- All board geometry is still photo-estimated.
- Box height and the lead rules on P1 are set by the arm.
- Tray packing is tight while the generic module sizes are unmeasured.
- ASA frame compliance and creep can let the force drift.
- The stack is heavier than the research's 2 mm spreader, so settling is slower.
- The thermostat sits on a bolted joint, which adds lag.
- The one-piece base is a long print.

Details are in the risks field.

## Printed parts

| Part | Material | BBox (mm) | Fits 220 bed | Notes |
|---|---|---|---|---|
| Base enclosure tray (walls, floor, bosses, vent slots, I/O apertures) | PETG (ASA optional) | 196 x 178 x 73.6 | True | Bed margins 12/21 mm. 3 mm walls and floor. 4 board bosses Ø8x6, 6 tray bosses, 2 clamp-foot bosses, 6 hanging lid bosses, 22x22 post access hole. If the bed is under 206 mm, split at X=-6 into 73x178 and 123x178 parts (needs a 188 mm bed), joined by a lap joint, 4 x M3 and 2 dowels. |
| Lid ring (acrylic pocket + locating skirt) | PETG | 196 x 178 x 8 | True | 5 mm ring plus 3 mm skirt. Pocket is 184.6x166.6x(t+0.2) for the sheet; ledge opening 172x154. Split at X=-6 if the bed is too small; the acrylic bridges the joint. |
| Bezel (engraved labels) | PETG, contrasting colour | 196 x 178 x 3 | True | Clamps the acrylic over a 6 mm band. 4 x M2.5 to the ring; 6 x M3 x 16 through bezel and ring into base inserts. |
| Module tray | PETG | 67.2 x 171.2 x ~9 | True | Sits on 5 mm floor bosses so cables run beneath. Notched around the duct and clamp foot. Two Si5351 sites. Engraved function labels beside each module. |
| Clamp frame (foot + mast fin + sole) | ASA | 109 x 30 x 59.6 | True | Printed on its side (109 x 59.6 on the bed, 30 tall). Sole is 30x8 under the PCB. ±5 mm XY cross-slots in the foot. Five M3 insert sites for the post. Fin shoulders at Z 47.6 are the arm's down-stop. |
| Heater arm with plunger barrel | ASA (orange) | 102.5 x 16 x 18.4 | True | Printed flat, barrel vertical. Hinge and latch holes Ø3.4. Barrel Ø14 with a Ø6.0 bore, 1.5 mm lip, captive M3 nut, and a 3x8 force-window slot with 1 mm ticks. Snap-cover wire channel on top. |
| Intake duct / fan mount / BME280 shield | PETG (blue) | 52 x 65 x 10 | True | Printed lying on its W face. 32 mm fan pattern with M3 inserts. Solid shield panel Z 0..24 hides the BME280 from the heater. |
| I/O plates (POWER, DATA, RS-232/VGA blank, JTAG) | PETG | up to 70 x 24 x 2.5 each | True | Replaceable. Plate thickness follows each panel part's maximum panel thickness (MEASURE). Labels engraved. |
| JTAG cable strain-relief clamp (2 pieces) | PETG | 30 x 16 x 10 | True | Saddle clamp with 2 x M3, plus an internal tie anchor. |
| P1-34 'CLK IN' key shroud | ASA | 12 x 7 x 9 | True | Covers P1-31..38 except pin 34, guarding against the 3.3 V / 5 V pins next to it. Pin-1 end and header pin height are MEASURE. |
| Logic-analyser lead comb | PETG | 30 x 10 x 25 | True | Two mounting positions in the tray/board gap, chosen by P1_PIN1_END. |
| USB-B blank plug with pull tab | PETG | ~15 x 13 x 12 | True | Flush in the board's power-only USB-B; tab points up, not W, so it stays clear of the comb. Socket opening MEASURE. |
| Analyser strap/backstop, fuse cradle, floor access plug | PETG | each ≤ 50 x 24 x 20 | True | Small accessories. |
| Board footprint gauge + insert test coupon (fit tests, not installed) | PETG | 116 x 146 x 1.2 | True | Printed first. Checks the photo-estimated hole pitch, FPGA, P1/P2/JTAG positions and insert fit before the 20-hour base print. |

## Decisions for Alex

- Visitor side: S, the frame's 'front' (default). The heater arm and FPGA are nearest the visitor and every cable is at the back. If the 7-seg digits only read upright from the E, the alternative is turning the box 90° on the desk, but then the exhaust and a side wall face the visitor. Check the digit direction on the real board.
- FPGA 5 V inlet family. Option 1, USB-C power-only (default): uses any Class II USB-C charger and can never mate with the 12 V barrel, but it needs 5.1 kΩ CC pull-downs or a C-to-C charger delivers 0 V, and people may expect it to carry data. Option 2, GX12-2 aviation connector: screw-locked and unmistakable, but needs a soldered adapter lead. Option 3: XT30.
- Arm height. PCB+30 (default) keeps the box about 85 mm tall, but only Dupont leads with sideways wires can go on the P1 rows under the arm, and no hook grabbers there. PCB+42 lets any clip go anywhere, at the cost of 12 mm more box height and a window further from the board.
- Heater stack form. Foot + angle bracket (default): two simple aluminium parts, HS10 lugs ≥ 8 mm above the leads, KSD on a vertical leg. A single tall pedestal block: one part, but about 4 mm taller and heavier, so settling is slower. A polyimide film heater on a flat spreader: lowest and has no live lugs, but it is a marketplace part with hot-spot risk.
- Clamp release. Hinged tilt-up arm with a latch pin (default): force and alignment survive service. Bolt-on lift-off arm: simpler to print, but it has to re-seat on dowels each time.
- Printer and materials. The clamp frame, arm and CLK-IN shroud need ASA, which needs an enclosed printer. If ASA is not possible, outsource those three prints or make the arm and sole from aluminium bar (PETG is not allowed there). The base can be PETG (default) or ASA (more heat margin, but hard to print at 196 x 178).
- Base as one piece (needs a bed ≥ 206 mm) or split at X=-6 into two parts (needs ≥ 188 mm, gives a visible seam and 4 extra bolts). This depends on which printer is used.
- Logic analyser on P1 (default): short leads from the tray, no SDRAM conflict, but it must avoid the arm band. On P2: the leads cross the window, and every P2 pin is shared with the SDRAM, so the test design must keep the SDRAM deselected.
- Fuse. Inline 3AG holder inside, visible on the tray (default, cheap, a listed part). Or a panel fuse holder on the POWER plate: looks more like an instrument, but needs about 40 mm of depth, its cut-out is unknown, and it costs more.
- Lid fixing: M3 socket screws (default) or M3 knurled thumb screws, which make lid-off demos tool-free.

## Risks

- Every board position is a photo-estimate. The FPGA is ±4 mm, and the hole pitch comes from a caption that may describe the acrylic plate, not the PCB. Mitigation: print the 1.2 mm board gauge first, use the ±5 mm XY slots in the clamp frame, keep all positions parametric.
- The arm sets the box height and crosses P1 at PCB+30. The rules for leads under it rest on unmeasured header-pin and Dupont-housing heights.
- Tray packing is tight: 2 mm gaps, with the generic module sizes still unmeasured. Fallback: widen the bay by 10 mm (box 206 mm, which still fits a 220 bed at a 7 mm margin) or move the star block and fan driver under the tray.
- The ASA C-frame flexes about 1.4 mm at 10 N (derived from an assumed E of 2 GPa) and can creep. Force can drift. Re-measure after a 24 h soak at 60 °C. Fallback: an aluminium flat-bar insert in the sole.
- The stack carries about 10.5 g of aluminium, roughly 9-10 J/K of extra heat capacity (derived). Settling is slower than the research's 2 mm spreader model, so each shmoo temperature step takes longer.
- The KSD9700 sits on a bolted angle leg. The extra contact resistance adds lag between the foot and the thermostat. Its trip point must be measured in place before 75 °C is trusted.
- On datasheet maxima, the HS10 envelope clears the angle's vertical leg by only about 0.25 mm. Measure the part actually bought; if it does not fit, offset the HS10 toward W by up to 1 mm.
- The USB-Blaster dongle and ribbon length are unmeasured. If the dongle does not fit the 30 mm front gallery, S_GAP grows. The box stays under 190 mm deep and still fits the bed.
- The one-piece PETG base (196 x 178 x 74 mm) is a long print with a risk of corner lift. A failure costs about a day.
- A USB-C 5 V inlet without CC pull-downs supplies 0 V from C-to-C chargers. Supplying 5 V from a host port adds an earth path; the high-side shunt still reads correctly.
- The 7-seg display may not read upright from the S face.
- The back-support post occupies the spot under the exposed pad that thermal-safety.md suggests for a second sensor to bracket Tj. A later post with an embedded thermistor would be needed.
- The mast fin and arm block part of the fan jet (about 20 %). The box runs at positive pressure, so airflow repeatability depends on the I/O plates staying fitted.
