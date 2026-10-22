# Concept: Thermal-first: bulkhead + gantry

> Design-panel concept (thermal-first), 2026-10-23. Input to DESIGN.md, not the design itself.

**A glass-topped hot chamber holds the board on an ASA cradle. A removable ASA gantry closes the clamp load loop inside that cradle and presses on a ball-and-cone spreader. A cool annex, behind a bulkhead, holds the electronics; its fan blows through a nozzle across the FPGA and out an exhaust grille.**

# Concept "thermal-first": bulkhead + gantry

Nothing here is measured. Every board position comes from `board-mechanical.md` (photo-estimate) and must stay a `params.py` value marked MEASURE. **MEASURE** marks a value I introduce; anything else is from a datasheet or the research.

## 1. Organising idea

1. **Two chambers.** A *hot chamber* holds only the board, the clamp, the Si5351 (it has to sit near P1) and the USB-Blaster. A *cool annex* holds everything else. A solid bulkhead separates them, and the fan sits in the bulkhead. This keeps the MAX31855 cold junction, the Pico, the INA226 and the fan out of the heater's air and out of its line of sight.
2. **One datum, one load loop.** A single ASA **cradle** carries:
   - the board standoffs;
   - the back-support post;
   - the clamp **gantry**.

   The clamp force runs cradle → gantry → spring → spreader → package → PCB → back-support post → cradle. The PETG shell carries no clamp force, so warping or creep in the shell cannot change the force.
3. **One defined air path:** annex intake grille → fan → nozzle → across the FPGA zone → W exhaust grille. Every other opening is sealed: the blanking plate, cable glands, and no ribbon slot. Experiments are always run with the lid on.

## 2. Coordinate frames

- **Board frame** (`board-mechanical.md`): x runs E from the W edge, y runs S from the N edge.
- **Box frame:** X runs E from the outer face of the W wall, Y runs S from the outer face of the N (back) wall, Z runs up from the underside of the floor.
- **Mapping:** X = x + 27, Y = y + 11. This comes from a 3 mm wall plus a 24 mm W gap, and a 3 mm wall plus an 8 mm N gap.
- **FPGA centre:** (57.5, 86) in the board frame = **(84.5, 97)** in the box frame.

### Top view (schematic, about 4 mm per character)

```
X:  0        40        80       120      161|164        234
Y=0 +------[== D-SUB WINDOW X46-122 + BLANK ==]---++[PICO USB][5V IN]+  N (back)
    |  N gap 8                                    ||  Pico   INA226  |
 11 |  .  +------------- BOARD 106x136 ------+    || (flip)          |
    |     | 7SEG      ==P3==         LEDs    |  |N|| MAX31855 perfbd|
 57 |     |                                  |  |L|| (TC)  (star GND)|
 E  |[W  ]|  P1   [KSD ]            P2      |  |E||                 |
 X  |[pst]=====P1==[ BALL ]==========P2===BEAM==|G||<4010  BME280  <<| AIR IN
 H  |     |  P1   [HS10]  FPGA      P2      |  |S||  fan  (mast)  <<| Y62-132
 A  |     |        (84.5,97)                 |  |S||                 |
 U  |     |                                  |  |  ||  D4184 module   |
147 |     +------[AS]---[JTAG]---------------+     || [12V HEATER IN]<|
    |   [DC plug]    ribbon v    [BLASTER holster]  || [FUSE 1A F]    <|
184 +---------------------------------[USB gland]--++-----------------+  S (front)
    W wall: EXHAUST grille Y62-132, LA PROBES slot Y138-162   bulkhead X161-164
```

### Side section at Y = 97, looking N

```
Z 86 +====== acrylic 3 mm in lid top (Z82-86) ======+
  78 |                          knob [M4]            |
  70 |                       [carriage 62-70]        |       annex cover Z66-70
  62 |[Wpost]=====BEAM 48-62=====|spring|======[portal X139-151]+-----------+
  48 |  |  Si5351 on beam  P1 Dupont<=41  chamfer  | nozzle Z24-48 | 4010 fan  |< AIR
  38 |  |   [KSD][ball][HS10] plate 35.1-38.1      |  >>>>>>>>     |X164-174   |
  26 |  |   pedestal 26.2-35.1 / pkg top 26.15     |               | Z16-56    |
24.6 |  |  ===== PCB 23-24.6 =====                 |               |  modules  |
  13 |  |  standoffs 13-23   back-support post     |               |           |
   7 |========== ASA cradle 3-7 (+bosses) ===================|               |
   0 +================== PETG floor 0-3 ===================bulkhead 161-164=====+ X234
     W wall (exhaust)
```

## 3. Height chain (as it goes into `params.py`)

| Item | Z (mm) | Basis |
|---|---|---|
| Floor | 0–3 | PETG, 3.0 |
| Cradle plate | 3–7 | ASA, 4.0 |
| Standoff bosses | 7–13 | M3 insert, 7 mm deep hole ≥ 6.7 |
| Brass M3 M-F hex standoff | 13–23 | 10 mm (Harwin 5.5 A/F class) |
| PCB | 23–24.6 | t = 1.6 MEASURE |
| Package top | 26.15 (26.05–26.25) | A = 1.45/1.55/1.65 datasheet |
| Header pin tips | 33.1 | pin_h = 8.5 MEASURE |
| Plate top (= HS10 base) | **38.1** | pin tips + 5 mm, so the live lugs clear pins and leads by ≥ 5 |
| Pedestal height | 8.9 | 38.1 − 3 (plate) − 26.15 − 0.05 (Kapton) |
| Dupont/LA housing top on P1 | 41.1 | PCB + 2.5 + 14 MEASURE |
| Beam underside over the board | **48** | 41.1 + ≈7 |
| Beam top | 62 | 14 deep |
| Carriage | 62–70 | |
| Preload knob top | 78 | |
| Lid ceiling / lid top | 82 / 86 | 4 mm clear above the knob |
| Power switch cap, up | ≤ 49.6 | PCB + 25 (photo-estimate 14–25) |
| JTAG box / IDC plug / ribbon fold | 33.9 / ≈43 / ≈48 | 9.3 listing + MEASURE |

The base walls rise to Z 66. The lid is a 20 mm cover (Z 66–86). Overall the box is **234 × 184 × 86 mm**.

## 4. Printed parts and the 220 bed

| Part | Material | Bounding box (mm) | Fits 220 with ≥ 5 mm margin? |
|---|---|---|---|
| Hot base shell (floor, N/W/S walls, bulkhead) | PETG | 164 × 184 × 66 | yes (28 / 18 mm margin) |
| Annex shell (N/E/S walls, floor, W perimeter flange) | PETG | 70 × 184 × 66 | yes |
| Cradle | ASA | 152 × 172 × 15 | yes |
| Gantry (W post + beam + E portal, one piece, printed beam-down) | ASA | 142 × 80 × 55 | yes |
| Spring carriage / knob | ASA | 40 × 26 × 22 / Ø18 × 10 | yes |
| Inlet nozzle | PETG | 46 × 48 × 25 | yes |
| Lid frame | PETG | 164 × 184 × 20 | yes |
| Window retaining frame | PETG | 156 × 176 × 4 | yes |
| Annex cover | PETG | 70 × 184 × 4 | yes |
| Module plate | PETG | 63 × 174 × 10 | yes |
| Small parts: back-support cap (ASA), Si5351 bracket (ASA), D-sub blank, BME mast, push-rod and bushing, USB-B dummy, Blaster holster, LA holster, glands | as listed | all ≤ 110 | yes |

The largest dimension is 184. The two base shells are joined at the bulkhead because 234 mm is wider than the bed.

**Walls:**
- 3.0 mm everywhere; locally thinned at the panel jacks to their maximum panel thickness (MEASURE).
- Lid top border 10 mm wide, 4 mm thick.
- Ribs ≥ 1.6 mm.
- Insert bosses: OD ≥ 7.2, hole Ø4.0, depth ≥ 6.7.

## 5. Board placement

- **Standoffs:** four brass M3 M-F hex standoffs, 10 mm, at box (32,16), (128,16), (32,142), (128,142). These assume a hole pitch of 96 × 126 (photo-estimate). It is the number most likely to ruin a print, so it is MEASURE before the cradle is printed.
- **Margins:**
  - N gap 8 mm: the D-sub flange overhang is unknown.
  - W gap 24 mm: W post, exhaust.
  - E gap 28 mm: portal, nozzle.
  - S gap 34 mm: DC plug, JTAG ribbon, Blaster.
- **The board's USB-B is deliberately blocked.** There is no wall cut-out at it, and a printed USB-B dummy plug fills the socket. The only 5 V path the board can use is therefore the metered DC-jack pigtail. The DPDT cap stays up (= DC); pressing it simply turns the board off.

## 6. Heater stack (metal at the contact)

- **Pedestal:** aluminium, foot **18 × 18 mm**, 8.9 mm tall, centred on the package. Box X 75.5–93.5, Y 88–106. Cut from 18–20 mm square bar (stock MEASURE). It is 1 mm inside the body on each side and 2 mm inside the lead tips.
- **Insulation:** 50 µm Kapton film, cut 24 × 24 with corner darts, folded 3 mm up the four foot faces. A thin layer of non-conductive paste goes between the film and the package top.
- **Thermocouple groove:** 1.2 mm wide, depth = bead Ø − 0.15 (MEASURE), lined with Kapton. It runs from the W face to a **blind end at the foot centre**, so the bead lands in the same place every time. The groove exits the **W (downstream) face**, so the lead sits in the stack's wake, not the inlet jet. The first 20 mm of the lead is Kapton-taped up the pedestal face, which sinks the lead to spreader temperature.
- **Top plate:** 3 mm aluminium (the Bunnings 20 × 3 bar), 20 (X) × 37 (Y), box X 74.5–94.5, Y 83–120. It is joined to the pedestal with 2 × M2.5 countersunk screws plus paste. It carries three things:
  - **Ball seat at (84.5, 97):** a 90° cone in a Ø6.5 × 2 mm counterbore holds a Ø6 stainless ball.
  - **KSD9700 75 °C on the N wing**, Y 84–91.5, long axis E-W. The unprinted (sensing) face goes down on Kapton. A stainless strap with Kapton under it is held by 2 × M2. The case is treated as live. This is option (a) from the verifier: the thermostat sits on the hottest *spreader* metal, 12 mm above the leads.
  - **HS10 (18–22 Ω) on the S wing**, centred Y 111, lugs E-W. It is fixed with 2 × M2 through its Ø2.4 holes, with paste. **Both solder tags are bent up 90°** before soldering, so the live tips sit at X ≈ 74.5 / 94.5, inside the plate outline, and rise to Z ≈ 50. Both are sleeved in heat-shrink.
- **Plate notch:** 3 × 4 mm in the W edge at Y 95–99, where the thermocouple rises.

The stack's added thermal mass is about 13 g of aluminium, roughly +12 J/K, so τ grows by about 1.6× (derived).

**Clearances, all ≥ 5 mm** (photo-estimate parts carry ±2.5–4):

| Gap | mm |
|---|---|
| Plate N edge to P3 body | 10 |
| Plate W edge to P1 body E face | 9.5 |
| Plate E edge to P2 body | 11.5 |
| Bent-up tags to P1 / P2 bodies | ≥ 9.5 |
| Lowest live metal (Z 38.1) above pin tips | 5.0 |
| Lowest live metal above FPGA leads | 11.8 |
| Plate S edge (Y 120) to JTAG box N face (Y 135) | 15 |

## 7. Clamp mechanism

- **Gantry** (one ASA part):
  - W post X 9–21, Y 90–104, 6 mm from both the W wall and the board edge.
  - Beam X 9–151, Y 90–104, Z 48–62 over the board. Over X > 133 the underside rises to Z 52 to clear the nozzle.
  - E **portal**: legs X 139–151 at Y 57–69 and Y 125–137, crossbeam Z 52–62. The legs straddle the inlet jet so nothing blocks it.
  - The beam's S lower edge is chamfered 6 × 45° over X 70–100. That gives ≥ 7.0 mm of air from the HS10 body to ASA.
  - The gantry sits on three cradle pads: the W pad has a Ø4 dowel in a hole, the S leg has a dowel in a slot along X (for tolerance and thermal growth), and the N leg is screw-only. Three M3 knurled thumbscrews go into inserts.
  - Stiffness: 8 N at mid-span on a 130 mm span, 14 × 14 ASA (E ≈ 1.5 GPa assumed) deflects about **0.08 mm**. That is under 1 % of the 8 mm spring compression (derived).
- **Spring cartridge:**
  - A Ø8.4 bore runs through the beam at (84.5, 97), with an ASA guide bush (Ø4.3) at its foot.
  - The plunger is M4 stainless rod with a 90° countersink in its lower end, which seats on the ball. Ball between two cones means the spreader can swivel to seat flat, while its X-Y position is set by the plunger.
  - On the rod: a nut and washer spring seat, then a stainless spring (OD ≤ 7.5, k ≈ 1 N/mm, free length ≈ 16, MEASURE), then a cap.
  - Preload comes from an M4 thumbscrew in an M4 insert in the carriage. One turn is about 0.7 N. A printed stop collar caps the force at 12 N.
- **Setting the force:**
  1. Measure k by compressing the bare spring on a kitchen scale.
  2. A slot in the carriage shows the seat washer and the cap against an engraved mm scale, so F = k(L0 − L) can be read at every reassembly, independently of the screw.
  3. Target **8 N** (range 5–10).
- **X-Y alignment:** the carriage plate (40 × 26) is held by 2 × M3 in Ø7 holes, which allows ±1.8 mm of adjustment. Align once:
  1. Hand-centre the spreader using a printed ASA centring gauge.
  2. Lower the gantry so the ball drops into both cones.
  3. Lock the carriage.

  After that, reinstalling the gantry on its dowels puts the spreader back in the same place.
- **Back-support post:**
  - An M4 stainless set screw in an M4 insert boss on the cradle, under (84.5 + dx, 97 + dy). The offset is MEASURE: the post must touch solder mask only.
  - It has a lock nut and a **printed ASA cap, Ø8 × 5**. The 3 mm ASA web is a thermal break of about 600 K/W. A bare brass post would be about 7 K/W, a heat leak as large as the PCB itself.
  - Set it to "just pinches paper" with the clamp off, then lock it.
  - The cap has a Ø3 × 1.5 pocket for an optional second sensor that would bracket Tj.
- **Removing it for access:**
  1. Lid: 4 thumbscrews.
  2. Si5351 leads: unplug them from P1 (board unpowered).
  3. Gantry: 3 thumbscrews, then lift it off. The preload stays set.
  4. The spreader lifts off.

## 8. Airflow

- **Fan:** a 4010 on the bulkhead's annex face, X 164–174, centred at (Y 97, Z 36). Its four M3 screws go through the 32 mm pattern into bulkhead inserts. It breathes room air only (rated to 70 °C).
- **Nozzle:** 40 × 40 in, 44 (Y) × 24 (Z) out, at Z 24–48, Y 75–119, X 139–161. The jet sweeps just above the PCB, across the keys, SDRAM and P2, then the stack, then P1.
- **Grille areas:**
  - Exhaust grille, W wall: 6 slots 4 × 70 at Y 62–132, Z 24–62, giving 1680 mm².
  - Intake grille, annex E wall: 1680 mm², Y 62–132, Z 14–52.
  - Both are ≥ 1.5× the 1056 mm² nozzle.
- **Fan figures (Sunon datasheet):** 8.0 CFM free air, 47 Pa maximum. The real flow is MEASURE: use inlet (BME280) against exhaust ΔT at a known heater power.
- **Rules that keep the flow repeatable:**
  - Logic-analyser leads go on **P1 only**, which is downstream. P2 stays bare; it shares pins with the SDRAM anyway.
  - Harnesses run in fixed clips.
  - The fan runs at a fixed baseline duty.
  - The lid is always on.

## 9. Annex module plate

The plate sits on the annex floor; its top is at Z 6. The annex is in three zones from N to S, labelled on the cover.

- **Logic and 5 V (N third):**
  - Pico 2H, mounted **flipped** on M2 × 6 standoffs (4 × Ø2.1 holes on 47 × 11.4) so its header pins point up for Dupont leads. X 170–191, Y 5–56, with USB out through the N wall.
  - INA226: X 202–229, Y 22–42.
  - Interface perfboard (star ground, AO3400 fan switch, gate pull-downs): X 205–229, Y 46–76.
  - MAX31855 #269: X 180–203, Y 56–76.
- **Air (middle):**
  - Plenum keep-out: X 174–200, Y 77–117, Z 16–56.
  - BME280 on a mast at X 222–226, Y 84–110, Z 30–56, facing the intake. It is the first thing the air touches, and the bulkhead and fan block it from the heater.
- **12 V (S third):**
  - D4184 opto module: X 172–207, Y 128–144.
  - 12 V jack and fuse holder on the E wall. Nothing else carries 12 V.

Module sizes other than the Pico are listings or Eagle-file values: MEASURE.

## 10. Wall cut-outs and labels

Labels are engraved 0.6 mm deep, 6 mm text.

| Wall | Cut-out | Label |
|---|---|---|
| Hot N | D-sub window X 46–122, Z 18–46, covered by a screwed blanking plate | "VGA · RS-232" |
| Hot W | Exhaust grille | "EXHAUST" |
| Hot W | Brush slot 30 × 6 at Y 138–162, Z 26–34, for the external LA holster | "LA PROBES → P1" |
| Hot S | Gland for the Blaster USB cable (X 150, Z 15) | "USB-BLASTER (JTAG) · do not unplug JTAG while powered" |
| Bulkhead (inside) | Gland, Y 61, Z 56 | "TC" |
| Bulkhead (inside) | Gland, Y 67, Z 56 | "I2C" |
| Bulkhead (inside) | Gland, Y 131, Z 56 | "HEATER 12V" |
| Bulkhead (inside) | Gland, Y 20, Z 12 | "5V/GND" |
| Annex N | Micro-USB cut-out | "PICO USB" |
| Annex N | 5 V inlet of a different family (default USB-C power-only breakout) | "FPGA 5V IN" |
| Annex E | Intake grille | "AIR IN" |
| Annex E | 5.5 × 2.1 panel jack (Y 150) | "12V HEATER IN" |
| Annex E | Panel fuse holder (Y 168) | "FUSE 1A F" |
| Lid | Ø10 hole in the acrylic for the power push-rod at (32, 129) | "FPGA PWR ▲ON" |
| Annex cover | Engraved chain: "12V → FUSE 1A → THERMOSTAT 75 °C → MOSFET → HEATER 18 Ω", and the I²C map (0x40 / 0x60 / 0x77) | — |

Strain relief: printed split glands with cable-tie anchors behind every exit.

## 11. Lid and window

- **Lid:** PETG frame, 164 × 184 × 20. It locates with a 2 mm inner lip (0.4 mm clearance) and is held by 4 × M3 knurled thumbscrews into wall-top corner inserts.
- **Window:** 3 mm acrylic, 152 × 172 (cut from Altronics H0725, 199 × 199). It sits on a 4 mm ledge under the 144 × 164 opening and is held by the PETG window frame with 8 × M3. It shows the 7-segment (box X 32–47, Y 30–61), the LEDs (X 115–124, Y 65–73) and the whole clamp.
- **Power push-rod:** a PETG rod Ø8, about 41 long, in a guide bushing. It rests on the switch cap, so rod up = ON. Its length is set from both cap heights (MEASURE).
- **Annex cover:** a flat 4 mm PETG plate on 4 × M3. Its top is 16 mm below the hot lid, so the two volumes read as separate.

## 12. Cable routing

- **Thermocouple:** groove → W pedestal face → clipped channel under the beam → N portal leg → TC gland → MAX31855. It is kept 12 mm or more from the heater tags.
- **Heater harness:** four wires, 20 AWG silicone (KSD in/out, HS10 A/B). They go up from the tags into a channel on the beam's S side → S portal leg → HEATER gland → fuse and D4184.
- **I²C to the Si5351:** along the beam's N top channel. The Si5351 sits on an ASA bracket on the beam top at X 30–60, above P1.
  - Clock lead to P1-34: about 30–45 mm, twisted with ground.
  - Ground continues to P1-1/2.
  - Which end of P1 is pin 1 is MEASURE.
- **5 V pigtail and star-ground wire:** from the 5V/GND gland through a channel in the cradle under the board's N and W margins (out of the airflow), then up at the S edge to the DC jack. The plug zone is X 44–58, Y 147–170, and the jack is assumed to face S (MEASURE). The ground wire goes to a header GND pin.
- **JTAG:** the ribbon folds S into a Blaster holster in the S gap (X 110–160, Y 151–178).
- **Logic-analyser leads:** in through the brush slot to P1.

## 13. Assembly order

1. Print insert test coupons in PETG and ASA, and a fit test.
2. Alex measures. Update `params.py`, then print.
3. Fit the heat-set inserts.
4. Make the spreader: tap M2 and M2.5, drill the cone, file the groove and the notch, then deburr.
5. Bench isolation checks with a DMM (Article IV): TC to sheath open, KSD lead to case, HS10 tags to housing, spreader to everything.
6. Fit the cradle with standoffs, the back-support post (loose) and the Blaster holster.
7. Board on. Fit the USB-B dummy, set the back-support post with a paper feeler, plug in JTAG (unpowered).
8. Fit Kapton, paste, and the pre-wired spreader with the bead in its groove.
9. Gantry on its dowels, carriage loose. Seat the ball, lock the carriage, set 8 N on the scale.
10. Dress the harnesses. Plug the Si5351 leads to P1.
11. Drop the cradle into the base and screw it from below.
12. Assemble the annex on the bench, mount the fan, join the annex to the bulkhead (4 × M3 + 2 pegs), and connect through the glands.
13. Power tests before any heat: INA226 known-resistor step, TC reads ambient, heater open-loop at low duty, KSD trip measured in place.
14. Fit the lid and the annex cover.

## 14. New MEASURE placeholders

- Header pin height; Dupont/LA housing height.
- Switch cap height, up and down.
- IDC plug height, ribbon bend radius, ribbon length.
- Blaster case size.
- USB-B overhang (for the dummy plug); D-sub overhang past the N edge.
- DC jack facing, and plug length (right-angle preferred).
- Bottom-side parts, and the back-support offset (dx, dy).
- Aluminium bar sizes available.
- HS10 tag bendability and base width.
- KSD9700 as bought.
- Spring L0 and k.
- M4 insert size.
- Every module's outline and holes (other than the Pico).
- Panel jack, fuse-holder and gland cut-outs.
- USB-C breakout size.
- Acrylic thickness.
- Fan holes, and real airflow.
- P1 pin-1 end.
- Window temperature during a 60 °C hold.

## 15. Main risks

See the `risks` list. The largest are:
- the box is 86 mm tall, driven by stacked photo-estimated heights;
- the taller spreader slows settling;
- bending the HS10 tags could crack them;
- the bottom of the board is unknown, so the back-support position is unknown;
- the Si5351 sits in warm air above P1.


## Printed parts

| Part | Material | BBox (mm) | Fits 220 bed | Notes |
|---|---|---|---|---|
| Hot base shell (floor, N/W/S walls, bulkhead with fan bore, glands, nozzle mount) | PETG | 164 x 184 x 66 | True | 28/18 mm bed margin. Carries no clamp load (the ASA cradle does). The D-sub window has a screwed blanking plate. The exhaust grille is in the W wall. Joined to the annex at the bulkhead with 4 x M3 + 2 pegs. |
| Annex shell (N/E/S walls, floor, W perimeter flange) | PETG | 70 x 184 x 66 | True | The W side is an open perimeter frame around the fan. Holds the intake grille, the 12V jack, the fuse holder, the Pico USB cut-out and the FPGA 5V inlet. |
| Cradle (board datum: standoff bosses, back-support boss, gantry pads with dowels, under-board cable channel, Blaster holster seat) | ASA | 152 x 172 x 15 | True | The largest ASA print and the one most likely to warp; needs an enclosed printer. Standoff positions come from the photo-estimated 96 x 126 hole pitch, so measure before printing. |
| Clamp gantry (W post + beam + E portal, one piece) | ASA | 142 x 80 x 55 | True | Print beam-face down with the posts and legs pointing up. Beam 14 x 14; S lower edge chamfered 6 x 45 deg over X 70-100. Mid-span deflection about 0.08 mm at 8 N (derived). |
| Spring carriage + M4 preload knob + stop collar | ASA | 40 x 26 x 22 (knob dia 18 x 10) | True | Holds an M4 heat-set insert. A window slot with an engraved mm scale lets the spring length (and so the force) be read. Ø7 holes give ±1.8 mm X-Y adjustment. |
| Back-support cap | ASA | dia 8 x 5 | True | Thermal and electrical break on the M4 support screw. Has a Ø3 x 1.5 pocket for an optional second (under-PCB) sensor. |
| Si5351 bracket (on the beam top above P1) | ASA | 36 x 26 x 10 | True | Within about 20 mm of the heater plume, so ASA, not PETG. |
| Inlet nozzle (40x40 to 44x24) | PETG | 46 x 48 x 25 | True | Cool inlet side; snaps into the bulkhead bore. Outlet at Z 24-48, Y 75-119. |
| Lid frame | PETG | 164 x 184 x 20 | True | 10 mm top border with a 144 x 164 opening and a 4 mm ledge. 4 corner thumbscrews; locating lip. |
| Window retaining frame | PETG | 156 x 176 x 4 | True | Clamps the 152 x 172 x 3 acrylic (Altronics H0725) with 8 x M3. Engraved 'HEATER ZONE' near the gantry. |
| Annex cover | PETG | 70 x 184 x 4 | True | Engraved zone map, safety-chain diagram and I2C address map. |
| Module plate | PETG | 63 x 174 x 10 | True | M2/M2.5 bosses for every module plus a BME280 mast socket. Every hole position except the Pico's is MEASURE. |
| BME280 mast | PETG | 30 x 10 x 60 | True | Holds the sensor face-on to the intake, out of the heater's line of sight. |
| Small parts: D-sub blanking plate, USB-B dummy plug, power push-rod + bushing, Blaster holster, external LA holster, split cable glands, spreader centring gauge | PETG (gauge: ASA) | largest 110 x 40 x 25 | True | The push-rod length and USB-B dummy size depend on measured switch and socket dimensions. |

## Decisions for Alex

- Heater body: an HS10 18-22 ohm with both tags bent up 90 degrees has a datasheet but needs the 8.9 mm pedestal, and the tags could crack. A 20x20 polyimide pad is flat with no lugs, so the stack could be lower, but it has no traceable datasheet and runs at high watt density. The same clamp takes either.
- Contact interface: 50 um Kapton plus non-conductive paste is lowest resistance (about 0.6-1.3 K/W) and keeps the bead touching the package, but the paste has to be renewed at every reassembly. A 0.5 mm silicone pad is more repeatable to fit, but puts the bead on the wrong side unless the pad is cut around the groove.
- Base material: PETG shells with an ASA cradle, gantry and clamp parts (my default; the PETG never carries clamp load) versus all-ASA. All-ASA is more heat margin everywhere, but warp-prone on 164 x 184 parts and needs an enclosed printer.
- FPGA 5 V inlet family: USB-C power-only breakout (common, cannot mate with a barrel, but a host USB port could become the supply), GX12 2-pin aviation connector (unambiguous, needs re-terminated leads), or a 2.5 mm barrel (cheapest, but keys only the dangerous direction).
- Fuse: panel M205 holder on the annex wall (visible, swappable, needs about 40 mm depth, extra cost) versus an inline 3AG holder (Altronics S6001, cheaper, hidden in the annex).
- Logic analyser and USB-Blaster placement: my default is the LA outside in a holster on the W wall (leads through a brush slot, matching the brief's 'lead slot') and the Blaster inside the S gap (only a USB cable exits). Either can flip; the inside LA costs space in the W gap, the outside Blaster costs a ribbon slot that leaks air.
- Optional thermal extras, each costing money: (a) a second sensor in the back-support cap to bracket Tj (T_pcb <= Tj <= T_top); (b) a second BME280 at 0x76 on the exhaust grille to measure air temperature rise; (c) a lid reed switch so firmware refuses setpoints with the lid off; (d) a 4-wire or tach fan instead of 2-wire, so the baseline fan speed is verified rather than assumed.
- Spreader fabrication: hand-cut and filed from 18-20 mm square bar plus the Bunnings 20 x 3 bar (cheap, flatness unverified), or a school or makerspace mill (flat, square, repeatable cone and groove).

## Risks

- The box is 86 mm tall and the lid clears the knob by only 4 mm. Header pin height (8.5 placeholder), Dupont housing height (14) and switch cap height (up to 25) all feed the height chain and are unmeasured; if they come out larger the box grows. The chain is parametric, but the gantry, lid and push-rod would all need reprinting.
- The 18 x 18 x 8.9 pedestal plus 3 mm plate adds about 13 g of aluminium (about +12 J/K). Derived settling time constant rises about 1.6x, to roughly 3-11 min, so a 4-setpoint run takes longer.
- HS10 tags bent up 90 degrees could crack or break the resistor's seal. If they cannot be bent, the lugs point E-W at about Z 43 and come within about 5 mm horizontally of P1 Dupont housings; the fallback is the polyimide pad.
- The bottom of the board is unknown. The back-support post may have no clear solder-mask spot under the FPGA (decoupling caps are probably there), in which case it needs a tripod tip or an offset contact, which loads the board less evenly.
- Every board position (standoff pitch, FPGA centre, P1/P2/P3, JTAG, DC jack facing, switch) is a photo-estimate at ±2.5-5 mm, and the board may be a different revision from the photos. The cradle, gantry and push-rod must be printed from Alex's measurements. The cradle is the largest ASA print, so a measuring error is expensive.
- The Si5351 sits on the gantry in warm downstream air above P1, a few K above inlet (derived). Crystal drift is small next to the shmoo step but is an uncontrolled variable. Its clock and ground leads must be unplugged from P1 every time the gantry is removed.
- The KSD9700 trip point on the N wing has an untested thermal path; heat reaches it through the 3 mm plate. A 75 C part could nuisance-trip at a 60 C setpoint, or trip late, so it must be measured in place before trusting it.
- Airflow repeatability depends on discipline: lid on, D-sub blank fitted, LA leads only on P1, harnesses in their clips, fixed fan duty. The real flow through the nozzle and grilles is unknown; the Sunon 8 CFM figure is free-air.
- The two-piece base (hot chamber + annex) must stay aligned at the bulkhead. A poor joint leaks air around the fan and bypasses the intake grille and the BME280.
- ASA prints (cradle 152 x 172, gantry 142 x 80 x 55) need an enclosed printer, and Alex's printer is unknown. The PETG shells and acrylic window are at least 35 mm from the heater, but the window temperature during a 60 C hold is unverified.
- The board's power switch is driven by a lid push-rod aligned to a photo-estimated cap position. If it is misaligned the board cannot be power-cycled with the lid on, which matters because JTAG must not be hot-plugged.
