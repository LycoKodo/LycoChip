# Agent Lab Box: parametric CAD (MVP, DESIGN.md v0.1)

This is the printable CAD for the Agent Lab Box described in [`DESIGN.md`](DESIGN.md): the
simple-first base concept plus all 32 amendments in DESIGN.md §3. CadQuery builds it from one
parameter file. `make.py` exports the parts and checks them, and `checks.py` measures the
clearances that DESIGN.md gives a number for.

**Nothing here has been measured on the real board.** There are 102 `MEASURE` placeholders,
listed at the end. A PASS from `make.py` or `checks.py` means the model agrees with itself.
It does not mean the box fits Alex's board. Print the footprint gauge and the insert coupon
first, measure the board, update `params.py`, and regenerate (DESIGN.md §6 step 1).

## Files

| File | What it is |
|---|---|
| `params.py` | Every dimension, in mm. Each value has a comment naming its source (research note, datasheet, DESIGN.md section). Unmeasured values go through `MEASURE()`. Also holds the bed size and `SPLIT_BASE`. |
| `box.py` | The model. It defines `PARTS` (printable parts in print orientation), `ASSEMBLY()` (everything placed in the box), `ALLOWED_OVERLAPS` (empty) and `SECTIONS`. Run `python box.py` to write the bar-part DXF drawings. |
| `make.py` | Harness, unchanged. Exports STEP and STL, then checks that every part is watertight and one body, that it fits the bed, and that no assembly items collide. Renders PNGs. |
| `render.py` | Off-screen VTK renderer, unchanged. |
| `checks.py` | Numeric clearance report against the DESIGN.md rules, using exact BRep distances. Exits 1 if any rule fails. |
| `parts/*.step`, `parts/*.stl` | The printable parts in print orientation. Slice the STL. |
| `parts/{bridge,keel,top_plate,spreader,pressure_bar}.dxf` | Cut and drill drawings for the aluminium parts: outline, holes with numbered callouts, a hole-coordinate table and notes. |
| `renders/part_*.png` | Each printed part in print orientation. |
| `renders/assembly_*.png` | Closed box views (iso, iso_back, top, front, left). `assembly_open_*` shows the box with the lid off. |
| `renders/section_clamp_ew.png`, `section_clamp_ns.png` | E-W and N-S sections through the FPGA centre, showing the whole clamp stack. |
| `concepts/` | The three design-panel concepts and their massing models. Kept as input, not as the design. |

## Regenerate

From `cad/lab-box/` (Windows, Git Bash or PowerShell):

```
python -m venv .venv
.venv/Scripts/python.exe -m pip install cadquery trimesh
.venv/Scripts/python.exe make.py          # export + checks + renders (about 3 min)
.venv/Scripts/python.exe checks.py        # clearance report (about 25 s)
.venv/Scripts/python.exe box.py           # DXF drawings of the bar parts
```

On macOS or Linux the interpreter is `.venv/bin/python`. Engraved labels use Arial Bold
(`params.FONT`, `C:/Windows/Fonts/arialbd.ttf`). It was checked on this PC: `→ ° · ² —` all
render. On another OS, point `FONT` at a TTF that has those glyphs. `ezdxf` and `matplotlib`
came in with cadquery.

Variants (each one was built once and checked for collisions, 2026-10-23):
- `P1_PIN1_END = "S"` moves the CLK-IN shroud and the active Si5351 wall to the other end,
  and re-keys the LA comb labels to P1 pins 23–30.
- `VISITOR_FACE = "N"` moves the nameplate.
- `SPLIT_BASE = True` splits the tub at X 64 into `base_tub_w` and `base_tub_e`, joined by
  internal flanges and 4 × M3 (DESIGN #17).

## How the model meets DESIGN.md §3, and where it had to interpret

Frame: box X runs east and Y runs **south** (DESIGN.md §4). In `box.py` every solid is built
in the right-handed world frame (x, −y, z). Positions are converted, but no solid is ever
mirrored, so engraved text reads correctly everywhere.

- **#1 Clamp stack (changed).** A single top plate cannot carry the cone seat, the HS10 and
  the KSD at once. The HS10's tags run N-S (#3) across 30 mm. Centred on the press point they
  hit the plunger, and moved far enough to clear it they hit P3 or JTAG. The model therefore
  uses a **yoke**: package → 0.5 pad → 18×18×7 spreader → 20×3 **top plate** (HS10 bolted on
  it, KSD on its S wing) → two Ø5 × 10 posts → **pressure bar** (20×3 × 22, with the 90° cone
  seat) → Ø6.35 ball → spring → M6 adjuster in the bridge. The load path is all metal and the
  HS10 is out of it. The difference from DESIGN.md is that the cone seat is in the pressure
  bar, not in the top plate.
- **#3** The HS10 sits 2 mm S of centre so that its N tag joint is 9.46 mm from P3's Dupont
  envelope (rule: 5 + 4 photo tolerance = 9). Only 0.46 mm of that is spare.
- **#4** The KSD9700 sits on the top plate's S wing over Kapton, under an FR4 strap held by
  2 × M2. Its underside is 11.25 mm above the lead tops. That is why the spreader is 7 mm tall
  (it must be at least 6.4).
- **#6** The spring is readable. The printed `spring_scale` clips onto the bridge, and its
  tongue carries mm ticks for the spring length L (engraved 4–12), so F = k·(L0 − L). The M6
  set-screw length is a hard force limit: the screw leaves its jam nut at about 11.6 N.
- **#7 (interpreted).** "2 locating pins per joint" is done with **two legs per joint**. The
  bridge is held by 2 close-fit M3 screws per end, drilled Ø3.1 through bridge and keel as a
  pair, and those screws are the pins. There are 4 legs, not 2. The spreader centring gauge
  locates on the P1, P2 and P3 header bodies, not on the package edge, which would be within
  0.3 mm of the leads.
- **#8** There are 5 tapped post sites in the keel. The centre one is fitted with a brass M-F
  6 mm standoff (stud flush in the keel), a nylon M3×8 pan screw as the tip, and a nylon jam
  nut. Adjust range is ±1.2 mm.
- **#12** Keel floor screws are 15 mm inboard of each leg pair, 9.5 mm from the nearest hex.
- **#24 (changed).** A straight E-W bridge cannot move its W leg off the fan axis, and moving
  the fan off-axis would miss the FPGA. The whole clamp line is therefore **skewed 23.7°**
  (W end south), so the W leg pair sits 1.4 mm S of the fan frame. The bridge is also 6.4 mm
  above the fan top, so it is out of the jet too.
- **#25** The fan is mounted 20 mm in from the panel on a printed intake duct. The BME280
  stands inside the duct, upstream of the fan and parallel to the flow, on two piers.
- **#27 (moved).** With the Si5351 lying in the bay, the real lead was 74 mm, because the
  wire leaves the top of the Dupont housing on P1-34. The Si5351 now **stands on edge on a
  printed wall** at the jet's edge, with CLK0 near the height where the Dupont wire exits.
  The route is 55 mm. Both walls are printed; `P1_PIN1_END` decides which one is used.
- **#21** The USB-Blaster lies on its side in the S gap, which is why the box is 186 deep,
  not 184. The ribbon runs through a printed clip. The USB cable leaves through the **E wall**
  under a printed clamp marked "JTAG NO HOT-PLUG". The wall is engraved "USB-BLASTER / JTAG"
  and "DO NOT UNPLUG JTAG WHILE POWERED".
- **#13–15** The lid has 4 captive knurled thumbscrews (each threads once through a Ø2.6
  collar). The window acrylic is held by 4 screws that pass **through** the acrylic, so they
  must clamp it.
- **#14** At F = 0, with the adjuster backed out, its top is at Z 79.9. The lid underside is
  at 86, so the margin is 6.1 mm. This is what sets the box height: 92.3 mm with the lid,
  against the concept's 76.2.
- **#17** All slots are vertical. Every part is at least 5 mm inside a 220 bed, and the tub
  can be split with `SPLIT_BASE`.
- **#19** The USB-B blank plugs into the board socket. Its pull tab hangs below the jet in
  the W gap and is engraved "NOT USED — 5 V ARRIVES / METERED VIA DC JACK".
- **#28** The LA comb stands in the W gap, N of the jet. The rows reserved for LA clips
  (outside the bridge's plan footprint and the CLK shroud) are worked out from `params` and
  engraved on the comb: P1 pins 1–16 and P2 rows 1–3 from the N end, with pin 1 at the N end.
- **#29–31** Labels are engraved on every exit. The nameplate, unit-ID and CAL fields are on
  the visitor face. The safety chain, the I²C map and a module legend are on the lid.

## Print settings

All parts are **PETG**: nozzle 240–250 °C, bed 80 °C. No part is in the heater zone; the
closest is 5.6 mm from heater metal (see clearances). Orientation is exactly as exported in
`parts/*.stl`. **No part needs supports.**

| Part | Layer | Walls | Infill | Notes |
|---|---|---|---|---|
| `footprint_gauge` | 0.2 | 3 | 100 % | 1.2 mm sheet. The rail off the W edge holds the NW and SW corners on. |
| `insert_coupon` | 0.2 | 3 | 25 % | Print in the **same PETG** as the tub. Holes: inserts Ø3.8–4.2, M3 clearance 3.2/3.4/3.6, M2 pilots 1.5/1.7/1.9. |
| `centring_gauge` | 0.2 | 3 | 100 % | Print after measuring (it is built from the P1, P2 and P3 positions). |
| `base_tub` | 0.2 | 3 (≥ 1.2 mm) | 20 % gyroid | Floor down. 200 × 186 × 86 is near the bed limit, so use a 5 mm brim against corner lift. If the bed is under about 210 mm, use `SPLIT_BASE`. |
| `lid` | 0.2 | 3 | 20 % | Top face down: the engraving is on the bed side and prints crisp. |
| `io_panel` | 0.2 | 3 | 30 % | Outer (labelled) face down. The duct, fan bosses and BME piers rise from the bed. |
| `module_plate` | 0.2 | 3 | 25 % | Flat. The Si5351 walls and Pico standoffs (Ø3.6, M2 pilot) stand up. |
| `usb_b_blank` | 0.12 | 3 | 100 % | Label plate on the bed, plug up. Its text is 2.5 mm high. |
| `clk_in_shroud` | 0.12 | 3 | 100 % | Top down. Test the 1.1 mm pin holes with a header offcut. |
| `la_comb` | 0.16 | 3 | 40 % | L-bracket, base down. |
| `spring_scale` | 0.12 | 3 | 100 % | Spine down; the ticks and numbers are on the bed face. |
| `cable_clamp`, `ribbon_clip` | 0.16 | 3 | 40 % | As exported. |
| `drill_jig` | 0.2 | 4 | 40 % | Guide plate down. In use it is turned over onto the clamped bar pair, with the bars' W ends against the end stop. The hole labels are on the bed face and read from above in use. |

## Print order

1. **`footprint_gauge` + `insert_coupon` first.** Lay the gauge on the real board (acrylic
   off). The holes must take an M3 screw into each board hole, and every part must sit in its
   window. Press a test insert into each coupon hole and pick the hole that holds. Update
   `params.py` (`INSERT_D` and every board MEASURE), then rerun `make.py` and `checks.py`.
   DESIGN.md #11.
2. `drill_jig`, then cut and drill the aluminium (DXFs).
3. `base_tub`, `io_panel`, `module_plate`, `lid`.
4. `centring_gauge`, `usb_b_blank`, `clk_in_shroud`, `la_comb`, `spring_scale`, `cable_clamp`,
   `ribbon_clip`.

## Assembly order (DESIGN.md §6, made specific to this CAD)

1. Gauge and coupon, then measure and regenerate (above).
2. Print. Fit M3 heat-set inserts with the iron at about 245 °C for PETG [TM]: 4 lid corner
   bosses, 4 module-plate floor bosses, 2 comb bosses and 1 ribbon-clip boss in the floor, and
   4 in the duct end for the fan. The Blaster clamp pedestal uses Ø2.5 pilots for M3
   self-tapping screws.
3. Metal: cut the bridge and keel (142.1) from the 20×3 bar. Clamp them as a pair in the
   drill jig and drill the 4 leg holes Ø3.1 through both. Keel only: the floor-screw holes
   3.4, the 5 post sites tapped M3, and the 4 leg holes countersunk from below. Bridge only:
   the centre hole opened to 5.0 and tapped M6. Then the top plate (46 long), the pressure bar
   (22 long, centre 90° countersink Ø5) and the spreader (20 mm square bar filed to 18 × 18 ×
   7, contact face flat, TC groove 1.2 × 1.0 from the centre to the E face, lined with Kapton).
   Coordinates are in each DXF's hole table.
4. **DMM isolation checks before first heat** (DESIGN.md §6.4), all with the stack assembled
   but off the board:
   - thermocouple lead to spreader: **open**
   - find which KSD lead is joined to its case, then KSD case to top plate: **open**
     (through the Kapton)
   - HS10 tags to HS10 housing: **open**
   - spreader, top plate, posts, pressure bar, ball and bridge to every board ground:
     **open** once mounted (the KSD case is live)
5. Mount the board on the 15 mm standoffs. Set the back post: wind the nylon screw up until
   a paper strip between its head and the PCB underside just drags. Then fit the clamp:
   centring gauge on the package, pad + spreader through its window, lift the gauge off, top
   plate (2 × M3 CSK, flush) carrying the HS10 and the KSD (Kapton + strap), posts, pressure
   bar, ball and spring cups, spring, and the bridge onto the legs. Back the adjuster off until
   the spring is free, then turn it in until the spring scale reads **L ≈ 6.7 mm** (8 N at
   k = 1.5; measure k first and recompute L = L0 − 8/k). Lock the jam nut.
6. Wire per `docs/lab-box/wiring.md`. Seat the JTAG plug and lay the ribbon in its clip. Put
   the Blaster cable in its clamp, put the CLK-IN shroud on P1-31..38, fit the USB-B blank,
   and close the lid.
7. **Before trusting it:** a 60 °C hold with the fan off, and a stuck-on test with the
   thermostat in circuit. Log the heater body, the nearest printed part (the spring scale),
   the lid underside and the fan inlet.

## Clearances (`checks.py`, 2026-10-23, nominal MEASURE values)

| Rule | Result |
|---|---|
| Spreader to lead ring (#2) | 1.52 mm 3D. The spreader edge is 1.0 inside the body and 2.0 inside the lead tips. |
| Lowest metal over the 22 × 22 lead ring | 8.15 above the lead tops (top plate) |
| HS10 tags + sleeves to nearest pin / Dupont / JTAG (#3) | 9.46 (P3 Dupont); rule ≥ 9 |
| Printed part to heater metal (#9) | 5.60 (spring scale to pressure bar); rule ≥ 5, target 25 not met for this part |
| Printed parts in the plume above the HS10 | none |
| Lid underside to the tallest part, adjuster backed out (#14) | 6.07 (adjuster top 79.93) |
| Lid lip to fan / fuse holder / USB-C / 12 V jack | 27.6 / 4.25 / 7.5 / 7.0 |
| KSD9700 underside above the lead tops (#4) | 11.25 (10.60 above the package top) |
| Screw tips above the top-plate underside (#10) | HS10 M2 +0.8, strap M2 +0.4 |
| Keel floor fasteners to leg hexes (#12) | 9.51 |
| W leg pair to fan frame (#24) | 1.43 S of it; bridge 6.4 above the fan |
| Si5351 CLK0 to P1-34 (#27) | 53.9 straight, 55.3 routed over the Dupont top; rule ≤ 60 |

## Open items and known conflicts

- **#27 "twisted with a dedicated ground to P1-1/2"**: P1-1/2 are 40.6 mm along P1 from
  P1-34, so the pair cannot stay twisted for that distance.
- **#9 target of 25 mm air**: met everywhere except the spring scale (5.6 mm). It reads a
  spring that sits on the heated stack, so it cannot be far from it.
- **#3 margin**: 0.46 mm spare after the 4 mm photo tolerance. Re-check once P3 and the
  FPGA are measured.
- **HS10 M2 screws**: the datasheet puts the ear hole 1.4 mm from the 8.5 mm body. A Ø3.8
  pan head does not fit there; the model uses a Ø2.8 head. Measure the bought HS10 and pick
  a screw.
- **Pico standoffs** are Ø3.6 with a 1.6 pilot (0.95 mm wall), so they clear the header
  strips. If one splits, use an M2 screw and nut.
- The box is 92.3 mm tall with the lid. The height comes from #14, which counts the
  plunger backed out (F = 0): the adjuster then stands 10.9 mm above the bridge top. A
  shorter M6 screw would lower the box but could no longer reach 10 N. If "backed out" were
  redefined as "at 5 N", the lid could come down about 3.3 mm. That is Alex's call.

## MEASURE placeholders (as printed by `make.py`)

```
MEASURE placeholders still in use: 102
  - BOARD_W/PCB width E-W = 106.0 — calipers, acrylic off [BM caption 136x106, unverified]
  - BOARD_L/PCB length N-S = 136.0 — calipers [BM]
  - PCB_T/PCB thickness = 1.6 — calipers at an edge [BM: unknown, FR-4 default]
  - BOARD_CORNER_R/PCB corner radius = 2.5 — radius gauge [BM photo 2-3]
  - HOLE_INSET/mounting-hole centre inset from W and N edges = 5.0 — edge to hole edge + r [BM 4.5-6]
  - HOLE_PITCH_X/hole pitch E-W = 96.0 — calipers across hole edges [BM: derived from caption, UNVERIFIED]
  - HOLE_PITCH_Y/hole pitch N-S = 126.0 — calipers [BM: UNVERIFIED, most likely to ruin a print]
  - HOLE_D/mounting hole diameter = 3.0 — pin gauge [BM ~3]
  - BOARD_STANDOFF/floor-to-PCB standoff length = 15.0 — choose from stock [C §1]
  - STANDOFF_AF/brass standoff across flats = 5.5 — calipers [TM Harwin 5.0 or 5.5]
  - FPGA_BX/FPGA centre from W edge = 57.5 — mean of body-edge distances [BM ±4]
  - FPGA_BY/FPGA centre from N edge = 86.0 — mean of body-edge distances [BM ±4]
  - PITCH/header pitch = 2.54 — calipers over 10 pins [CP: not stated in vendor docs]
  - HDR_PLASTIC_H/header plastic height = 2.5 — calipers
  - HDR_PIN_H/header pin top above PCB = 8.5 — calipers [BM unknown; 3M mating 5.97 + 2.5]
  - DUPONT_TOP_H/Dupont housing top above PCB = 16.5 — plastic + 14 mm housing, measure with a lead on
  - P1_BX/P1 centreline from W edge = 35.5 — [BM 57.5-22 vs 34: pick by measuring]
  - P1_BY_N/P1 N end of body = 63.0 — [BM Y 63-111]
  - P2_BX/P2 centreline from W edge = 81.5 — [BM ±2.5]
  - P2_BY_N/P2 N end of body = 56.0 — [BM Y 56-112]
  - P3_BY/P3 centreline from N edge = 59.5 — [BM ±2.5]
  - P3_BX_W/P3 W end of body = 46.0 — [BM X 46-71]
  - P1_PIN1_END/end of P1 that carries pins 1/2 = 'N' — silkscreen / square pad [CP §6 item 1]
  - P1_EVEN_COL/column (E/W) of P1's even pins = 'E' — square pad + continuity [CP]
  - JTAG_BX/JTAG box header centre bx = 66.0 — [BM ±5]
  - JTAG_BY/JTAG box header centre by = 128.0 — [BM ±3]
  - AS_BX/AS box header centre bx = 40.0 — [BM ±5]
  - BOXHDR_L/2x5 box header length = 20.0 — [BM DC3-10P listing]
  - BOXHDR_W/2x5 box header width = 9.0 — [BM listing]
  - BOXHDR_H/2x5 box header height above PCB = 9.3 — [BM 3M 30310 listing]
  - IDC_PLUG/IDC plug L x W x height above box top = (17.0, 7.0, 8.5) — with the Blaster cable seated
  - USBB_BY/board USB-B centre by = 104.5 — [BM 99-110, ±6]
  - USBB_OVERHANG/USB-B mouth past the W edge = 0.0 — calipers
  - DCJ_BX/board DC jack bx range = (9.0, 19.0) — [BM verifier: 9-19]
  - DCJ_BY/board DC jack by range (mouth at S edge) = (117.0, 136.0) — [BM: faces S, unverified]
  - DCJ_H/board DC jack height = 11.0 — calipers [BM unknown]
  - SW_BX/power switch bx range = (1.0, 9.0) — [BM]
  - SW_BY/power switch by range = (113.0, 123.0) — [BM]
  - SW_BODY_H/power switch body height = 9.0 — calipers
  - SW_CAP_UP_H/switch cap top above PCB, cap UP (DC) = 25.0 — [BM 14-25, worst case used]
  - SEG7/7-seg bx0,bx1,by0,by1,h = (5.0, 20.0, 19.0, 50.0, 7.2) — [BM photo]
  - SEG7_DIGITS_READ_FROM/edge the 7-seg digits read upright from = 'S' — look at it [D #32]
  - KEYS_BX/key column bx = 98.0 — [BM]
  - KEYS_BY/keys S4..S1 by = (22.5, 31.5, 40.0, 48.5) — [BM verifier]
  - RESET_KEY/RESET key centre = (90.0, 128.0) — [BM]
  - DIP/DIP switch centre + size = (72.0, 41.0, 10.0, 6.0) — [BM]
  - BUZZER/buzzer centre, dia, h = (40.0, 41.0, 12.0, 9.5) — [BM]
  - POT/contrast pot bx0,bx1,by0,by1 = (5.0, 13.0, 13.0, 19.0) — [BM]
  - LCD_SOCKET/LCD socket bx0,bx1,by0,by1,h = (1.0, 5.0, 33.0, 84.0, 8.5) — [BM]
  - IR/IR receiver centre = (100.0, 16.0) — [BM verifier]
  - LEDS/LED1-4 footprint = (88.0, 97.0, 54.0, 62.0) — [BM]
  - DB9_BX/DB9 body bx = (24.0, 56.0) — [BM verifier]
  - VGA_BX/VGA body bx = (57.0, 90.0) — [BM verifier]
  - PS2_BX/PS/2 bx = (9.0, 23.0) — [BM 7-23; moved 2 E so it clears the NW screw head]
  - PS2_DEPTH/PS/2 body depth from N edge = 12.8 — [BM unknown; must end before the pot at by 13]
  - DSUB_OVERHANG/D-sub shell past the N edge = 6.5 — calipers [C: <= 7]
  - PCB_BOTTOM_CLEAR/longest bottom-side protrusion = 3.0 — photo + calipers [BM unknown]
  - ACRYLIC_T/acrylic sheet thickness = 3.0 — calipers [TM: cast sheet varies]
  - THUMB/knurled M3 thumbscrew head dia, head h, length = (10.0, 4.0, 12.0) — [D #13] buy, then measure
  - BAR_T/flat bar thickness = 3.0 — calipers [SU listing]
  - SPREADER_H/spreader block height = 7.0 — [D §9.2] stock decision; >= 6.4 keeps KSD 10 mm up
  - TC_GROOVE/thermocouple groove width, depth = (1.2, 1.0) — [C §5.1] bead dia - 0.15, measure bead
  - POST_D/pressure-bar post dia (round M3 M-F Al spacer, stud cut to 2.5) = 5.0 — calipers; round so it clears the HS10 body and ears
  - POST_H/pressure-bar post length = 10.0 — HS10 C 8.8 + 1.2 clearance; standard length
  - BALL_D/steel ball dia (1/4 in) = 6.35 — calipers
  - SPRING_L0/spring free length = 12.0 — calipers [D #6]
  - SPRING_K/spring rate N/mm = 1.5 — kitchen scale, 3 points [D #6: ~1-2 N/mm]
  - SPRING_OD/spring outside dia = 7.0 — calipers
  - ADJ_LEN/M6 set-screw adjuster length = 16.0 — sets the hard force limit: screw top leaves the jam nut at ~11.6 N (checks.py)
  - LEG_LEN/leg standoff stack (keel top to bridge) = 60.0 — 30 + 30 brass M3 F-F / M-F
  - LEG_AF/leg standoff across flats = 5.5 — calipers [TM 5.5 A/F]
  - BACKPOST_SO/back-post brass M-F standoff length = 6.0 — stud in tapped keel
  - BACKPOST_SCREW/nylon M3 pan screw length, head d, head h = (8.0, 5.5, 2.1) — [D #8]
  - FAN_HOLE_D/fan hole dia = 4.3 — [TM Sunon 4.3; others differ]
  - PICO_SO/Pico standoff height (header tails below) = 9.0 — Pico 2H pins: measure
  - LA/logic analyser case L x W x H = (54.7, 27.4, 14.1) — [SU] Core TOL-18627 listing
  - LA_USB_Z/LA USB centre above its base = 7.0 — calipers [D #22: connector may be Mini-B]
  - MAX_TERM_H/MAX31855 terminal block height above PCB = 8.5 — [ME unknown]
  - SI5351_H/Si5351 tallest part above PCB (wires soldered, no header) = 3.0 — keep < jet
  - INA226/INA226 CJMCU-226 L x W x H = (27.0, 20.0, 4.0) — [ME listing 20 x 27]
  - D4184/D4184 module L x W x H = (35.0, 16.0, 14.0) — [ME listing]
  - AO3400/AO3400 fan-switch module L x W x H = (25.0, 15.0, 5.0) — [ME unknown]
  - LOADSW/5 V load-switch module L x W x H = (20.0, 15.0, 5.0) — [D §9.5 default: include]
  - STAR/star-ground lever connector L x W x H = (20.0, 19.0, 9.0) — [C §8]
  - BME/BME280 board L x W x PCB t x overall t = (25.4, 17.78, 1.57, 4.5) — [ME] Adafruit 2652; GY clone 15.5 x 11.5
  - BME_HOLES/BME280 mounting holes (board coords) = ((2.54, 15.24), (22.86, 15.24)) — [ME 2652]
  - USBC_CUT/USB-C panel socket cut-out = (9.4, 3.8) — [D #18] buy, then measure
  - USBC_SCREWS/USB-C socket flange screw offset +- = 8.0 — calipers
  - USBC_BODY/USB-C socket body behind panel = (14.0, 7.0, 18.0) — calipers
  - FUSE_HOLE/panel fuse-holder hole = 12.5 — [TM Jaycar SZ2030 class]
  - FUSE_BODY/fuse holder body dia, depth behind panel = (15.5, 30.0) — [D #20] ~40 max
  - JACK12_HOLE/12 V panel jack hole = 8.0 — [SU] Altronics P0622 8 mm
  - JACK12_BODY/12 V jack body dia, depth = (10.0, 15.0) — calipers
  - PICO_USB_CUT/Pico micro-B plug overmould cut-out = (12.0, 9.0) — measure the cable [C §9]
  - LA_USB_CUT/LA USB plug overmould cut-out = (13.0, 8.0) — measure the cable [D #22]
  - BLASTER/USB-Blaster dongle L x W x H = (60.0, 26.0, 15.0) — [D #21] measure before printing the tub
  - BLASTER_RIBBON/Blaster ribbon length = 150.0 — [D #21]
  - BLASTER_CABLE_D/Blaster USB cable dia = 4.0 — calipers
  - BLASTER_PLUG_L/Blaster-side USB plug overmould length = 18.0 — calipers
  - RA_DC_PLUG/right-angle DC plug length, body dia = (25.0, 10.0) — [C §9] <= 25
  - FOOT/rubber foot dia, height = (12.0, 5.0) — [C §4] >= 5 clears screw heads
  - VISITOR_FACE/wall that carries the nameplate = 'S' — after the 7-seg check [D #32]
```

`SEG7_DIGITS_READ_FROM`, `PCB_BOTTOM_CLEAR` and `BLASTER_RIBBON` drive no geometry yet. They
are on the list so they get measured: they decide `VISITOR_FACE`, the back-post landing, and
whether the ribbon reaches the dongle.
