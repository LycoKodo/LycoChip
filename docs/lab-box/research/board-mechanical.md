# Board mechanical facts — OMDAZZ / RZRD "Cyclone IV V3.0" (EP4CE6E22C8N)

Research note for the Agent Lab Box CAD. Written 2026-10-23. Nothing on this page was measured on Alex's board.

**TL;DR**
1. The maker's own product page gives the size as **136 × 106 mm** (caption on the acrylic-case photo). My photo-scaling agrees to within about 2 % (107 × 136 mm). Thickness is **unknown**. *[Verifier: the caption is confirmed. The photo check is **not independent**, though: the photo frame was scaled from the caption itself. It cannot tell the PCB from a slightly larger acrylic plate at the ±3 mm level. Treat 136 × 106 as UNVERIFIED for the PCB.]*
2. There are **4 corner holes, about 5 mm in from each edge** (pattern about 96 × 126 mm). The holes look like M3 (about 3 mm hole, 6–7 mm pad). The vendor kit uses brass hex standoffs. Every hole and standoff number here is a photo-estimate. **Measure them.** *[Verifier: the 96 × 126 pitch is derived from the caption itself, so it is UNVERIFIED. The only independent check is that each hole is roughly 3 mm across inside a pad of about 6.5–7 mm (SE hole in TB2i78je).]*
3. The **FPGA centre is about 57 mm from the W (USB/LCD) edge and about 86 mm from the N (DB9/VGA) edge**, ±4 mm. That puts it in the southern half, about 50 mm from the S edge. The package top sits **1.45–1.65 mm** above the PCB (Altera datasheet). P1 is about 22 mm W of the FPGA centre and P2 about 24 mm E. That leaves only a **~41 mm wide gap** for the heater clamp.
4. Edges, with the DB9/VGA edge as the "back" (N):
   - **N:** PS/2, DB9 and VGA, all facing out, plus the IR receiver at the NE corner. *[Verifier: the DB9 and VGA flanges nearly touch, with a gap of about 4 mm or less, not the ~10 mm implied below. Plan one combined cut-out about 65 mm wide, X ≈ 24–90.]*
   - **W:** USB-B, which is power only, then the push-on/push-off power switch and the 1×20 LCD socket.
   - **S:** the DC jack (it appears to face **S**, not W; unverified), then the AS and JTAG 2×5 box headers. Both headers plug in **from above**. *[Verifier: the vendor manual's own photo (p.1) also shows the jack's mouth on the AS/JTAG edge. That strengthens "faces S", but it is still unverified on Alex's board.]*
   - **E:** keys S1–S4 and the LEDs. There are no cable connectors on this edge. *[Verifier: the key order runs **S4 at the north** (next to the IR receiver) down to **S1 at the south**, and LED1 is the southmost LED. The table and sketch below had this reversed; both are now corrected.]*
5. The tallest part is probably the **power switch cap in its "up" (DC-jack) position**. My rough photo-estimate is 15–25 mm, because it pokes through the vendor's top acrylic. *[Verifier: I scaled TB2wl6nb against the USB-B shell (12.04 × 10.62 mm per the Würth datasheet; the board's own USB-B part is unidentified). That gives about 14–20 mm. Still a photo-estimate.]* Next are DB9/VGA at about 12.6 mm (standard flange). The bottom side is **unknown**: no photo exists. Every position on this page comes from RZRD-branded vendor photos, and Alex's OMDAZZ-branded board may be a different PCB revision.

Coordinate frame used throughout: a **top view with the DB9/VGA edge at the top (N)**, the USB/LCD edge on the left (W), the JTAG/AS edge at the bottom (S, the "front"), and the keys edge on the right (E). **X is measured from the W edge** (mm, increasing toward E). **Y is measured from the N edge** (mm, increasing toward S). Photo-estimates are given as "X, Y" of the part's centre or footprint.

---

## Facts table

Sources are abbreviated. The full list is at the end.

*[Verifier: in the connector rows below, a **vendor-doc** tag covers only what the part is and that it exists (from the schematic). Every X/Y position, size and height in the Notes column is a **photo-estimate** unless that row says otherwise. Do not carry the vendor-doc tag over to the positions in CAD.]*

| Item | Value | Unit | Source | Confidence | Notes |
|---|---|---|---|---|---|
| PCB length × width | 136 × 106 | mm | [S5] image TB2el2ab (caption "尺寸: 136*106MM") | listing | This is the maker's own shop page. The caption is on the acrylic-case photo, so it **could be the acrylic plate size**. |
| PCB outline, photo check | ≈107 × 136 (±2 %) | mm | [S5] TB2i78je, rectified (see Method) | photo-estimate | The aspect ratio and known-size parts agree with 136 × 106. **[Verifier: circular.]** The holes were mapped onto a 96 × 126 rectangle that was itself taken from the caption. Only the two known-size parts give an independent scale, and both read ~2 % large. Both are 8–13 mm tall parts, and that height alone can make them look a few % larger. So the check is *consistent with* 136 × 106 but cannot exclude a PCB 2–3 mm smaller. |
| PCB thickness | unknown | mm | — | unknown | 1.6 mm is the common FR-4 default. Use it only as a placeholder marked MEASURE. |
| Corner shape | rounded, r ≈ 2–3 | mm | [S5] TB2A61Mg corners | photo-estimate | |
| Mounting holes | 4, one per corner | — | [S5] TB2i78je, [S6] | photo-estimate | All 4 are visible in TB2i78je. |
| Hole centre inset from edges | ≈5 (range 4.5–6) | mm | derived: rectified outline −5.5 / +101.5 / −5 / +131 vs. hole rectangle | photo-estimate | The hole pattern is ≈96 (E-W) × 126 (N-S) mm. With a 106 mm board that is 95–96 mm. **[Verifier: UNVERIFIED.]** 96 × 126 = caption − 2 × inset, so any error in the caption carries straight into the standoff spacing. My own rough corner picks in TB2i78je give insets of 3–7 mm. A 2 % scale error is 2.5 mm over 126 mm, enough to miss a standoff. **Measure before printing.** |
| Hole Ø / pad Ø | ≈3 / ≈6–7 | mm | [S5] TB2i78je, rectified at 10 px/mm | photo-estimate | Consistent with M3 clearance. Measure with a pin gauge. |
| Vendor standoffs | brass hex, ≈5.5–6 mm across | mm | [S5] TB2el2ab, SE corner, local scale ≈4.3 px/mm | photo-estimate | Consistent with M3. The thread is **unverified**. |
| Upper standoff stack (PCB top → top of acrylic screw head) | ≈15–23 | mm | derived from a camera-pose fit on TB2el2ab | photo-estimate (low) | Very rough, because the two focal-length estimates disagreed. **Measure.** |
| Lower standoff (PCB bottom → bottom acrylic) | ≈10–18 | mm | same | photo-estimate (very low) | **Measure.** |
| FPGA package | EQFP-144, body 20.00 × 20.00, lead tip-to-tip 22.00 × 22.00 | mm | [S4] p.1 (D1/E1, D/E) | datasheet | Verifier re-read [S4] p.1: D1/E1 20.00 BSC, D/E 22.00 BSC. ✓ |
| FPGA height above PCB (A) | 1.45 min / 1.55 nom / 1.65 max | mm | [S4] p.1 | datasheet | The A1 standoff is 0.05–0.15 and the lead pitch is 0.50 mm. Verifier re-read ✓. Note: A is measured from the seating plane; the solder fillet adds a few hundredths of a mm. |
| FPGA exposed pad (bottom) | 5.40 × 5.40 (5.25–5.55) | mm | [S4] p.1 (D2/E2) | datasheet | Soldered to GND ("GND 145") per [S2]. Heat goes into the PCB. Verifier re-read ✓: U5L lists pin 145 = GND. |
| FPGA centre position | X ≈ 57.5, Y ≈ 86 (±4) | mm | [S5] TB2el2ab rectified; cross-checked with TB24uDrb + TB2i78je | photo-estimate | That is ≈49 mm from the E edge and ≈50 mm from the S edge. Its edges run parallel to the board edges. |
| P1 header | 2 × 19, 2.54 pitch, male, vertical | — | [S2] "Header 19X2"; pitch checked in rectified TB24uDrb (45.7 mm / 18) | vendor-doc + photo | Runs N-S. Centreline X ≈ 34 (±2.5), Y ≈ 63–111. About 22 mm W of the FPGA centre. *[Verifier: these two numbers disagree. 57.5 − 22 = 35.5, not 34. That is within the ±2.5, but pick one; the 41 mm gap row below uses 35.5.]* |
| P2 header | 2 × 22, 2.54 pitch, male, vertical | — | [S2] "Header 22X2" | vendor-doc + photo | Runs N-S. Centreline X ≈ 81.5 (±2.5), Y ≈ 56–112. About 24 mm E of the FPGA centre. Body length 55.9 mm (3M 929836-03-22 listing [S8e]). Carries the SDRAM pins [S2]. |
| P3 header | 2 × 10, 2.54 pitch, male, vertical | — | [S2] "Header 10X2"; 22.9 mm over 9 pitches in TB24uDrb | vendor-doc + photo | Runs E-W. Centreline Y ≈ 59.5 (±2.5), X ≈ 46–71. About 26.5 mm N of the FPGA centre. |
| Header pin height | unknown | mm | — | unknown | The photos show plain straight headers. One reference: the 3M 2.54 mm header has a 5.97 mm (0.235") mating length [S8e]. **Measure.** |
| Clear gap between P1 and P2 bodies (heater-clamp envelope, E-W) | ≈41 (±3) | mm | derived: 22 + 24 − 2 × 2.54 | photo-estimate | N-S, the gap runs from P3 (≈24 mm N of the FPGA centre) to the AS/JTAG boxes (≈36 mm S). Only flat SMD parts sit in between. Arithmetic re-checked: 22 + 24 − 5.08 = 40.9 ✓. *[Verifier: by this table's own numbers, the JTAG box (X ≈ 56–76) sits directly S of the FPGA (X ≈ 46.5–68.5). A clamp arm coming in from the S has to clear the USB-Blaster IDC plug and ribbon.]* |
| JTAG header | 2 × 5 shrouded box, 2.54 pitch, **top entry** | — | [S2] "JTAG HEADER 5X2"; [S1] p.1 photo; [S5] TB2gojeb | vendor-doc | S edge. Centre X ≈ 66 (±5), Y ≈ 128 (±3). Long axis runs E-W. |
| AS header | 2 × 5 shrouded box, 2.54 pitch, top entry | — | [S2] "AS HEADER 5X2"; [S1] p.1 | vendor-doc | S edge, W of JTAG. Centre X ≈ 40 (±5), Y ≈ 128 (±3). |
| Box header body size | ≈20 × 9 × 12 (L × W × H) | mm | DC3-10P listing [S8d] | listing | The part on the board is not identified, and the height varies by part. **Measure.** *[Verifier: the listing (re-fetched) gives "Total Size: 20 x 9 x 12mm (L*W*H)" without saying whether H includes the pin tails. A 3M 30310-6002HB vertical 2×5 box header lists a 9.3 mm profile height ([S8h]). So expect about 9 mm above the PCB, plus the IDC plug on top. Both are listings.]* |
| RESET key | 6 × 6 tact, top-actuated | — | [S5] TB2gojeb | photo-estimate | X ≈ 90, Y ≈ 128 (SE, near the hole) |
| USB connector | **USB Type-B (full size), power only** | — | [S2] "USB" pins 2–3 not connected, pin 1 → switch, pin 4 → GND; [S5] TB2wl6nb label "USB供电" (USB power) | vendor-doc | W edge, opening faces W. Centre Y ≈ 99 (±3), X ≈ 0–16. Not a data/JTAG port. Verifier re-read [S2]: pins 2/3 are open stubs, pin 1 → SW-DPDT, pin 4 and the shell → GND ✓. The maker's page text also says "方口USB接口电源插座" (square-USB power socket) ✓. **[Verifier: the Y position is UNVERIFIED and the ±3 is overstated.]** Re-estimates came out at Y ≈ 105–108 (TB2i78je hole-frame homography; TB2el2ab projection from the P1 S end) and ≈112 (manual p.1 photo). Use **Y ≈ 99–110** until measured. |
| USB-B height | ≈11 | mm | Würth 61400416121 listing [S8b] | listing | The board's part is not identified. Measure. **[Verifier: corrected from the manufacturer drawing.]** Würth 61400416121 datasheet p.1 [S8b′]: shell 12.04 ± 0.20 wide, 16.5 ± 0.25 deep, 10.62 ± 0.20 high (11.05 ± 0.20 over the top tabs). The listing's "11.25" is not on the drawing. These numbers are **datasheet** for that Würth part only, since the board's own part is unidentified. |
| DC jack | barrel jack, "external +5 V" | — | [S2] "外部+5V电源" / POWER; [S1] p.1 | vendor-doc | Plug size unknown. It looks like the common DC-005 type: **check with a plug**. |
| DC jack position / facing | SW corner, X ≈ 6–16, Y ≈ 117–136, **opening appears to face S** | mm | [S5] TB2wl6nb, TB2WT4Ug, TB28RsGc, TB2i78je | photo-estimate | Medium confidence. Its long axis is parallel to the W edge in 4 photos. **Verify before cutting.** *[Verifier: the facing is supported by the vendor manual [S1] p.1 photo. The jack's square mouth face sits on the same board edge as the AS/JTAG boxes in the second photo on that page. The X range is doubtful, though: X 6–16 overlaps the SW hole pad (centre 5.5, 131, pad Ø 6–7) and the switch footprint (X 1–9, Y 113–123). In the manual photo the jack sits E of the hole and E of the switch, so X ≈ 9–19 is more likely. Photo-estimate.]* |
| DC jack body | one listing gives 15 × 14.5 × 9 (axes not stated) | mm | uElectronics DC-005 listing [S8c] | listing | Height unknown; measure. |
| Power switch | DPDT push-on/push-off, coloured cap (red or blue; varies between vendor photos) | — | [S2] "SW-DPDT"; [S1] p.1 | vendor-doc | **Pressed (down) = USB power. Released (up) = DC-jack power** [S1]. W edge near the SW corner, X ≈ 1–9, Y ≈ 113–123. *[Verifier: the mode text was re-read verbatim from [S1] p.1: "Press the switch button: USB power supply; Lift the switch button: 5V power adapter power supply." ✓ Correction: `board.jpg` is **not Alex's photo**. It is the vendor image in `resources/`, the same shot as TB2el2ab. The cap is red in board.jpg, TB2el2ab, TB2wl6nb and the manual; it is blue in TB2i78je, TB28RsGc, TB2WT4Ug and TB2A61Mg.]* |
| Power switch height (cap up) | ≈15–25 | mm | [S5] TB2el2ab / [S6]: the cap rises through the top acrylic | photo-estimate (low) | **Probably the tallest part.** Measure both positions. *[Verifier: a second photo-estimate from TB2wl6nb, scaled on the USB-B shell, gives ≈14–20 mm (cap ≈6 mm Ø, rising ≈12 mm above the switch body). It is still low confidence.]* |
| DB9 (RS-232) | D-sub shell size E (DE-9), right angle | — | [S2] "DB" 9-pin + MAX3232; [S6] | vendor-doc | N edge, faces N. X ≈ 24–55 (centre ≈ 39.5 ±4). Gender not confirmed. Verifier re-estimate from TB2i78je: body X ≈ 25–57, D-shell centre ≈ 39 ✓. |
| VGA | DE-15 HD, shell size E, right angle, blue | — | [S2] "VGA"; [S6] | vendor-doc | N edge, faces N. ~~X ≈ 65–96 (centre ≈ 80 ±4)~~ **[Verifier: corrected to X ≈ 57–90, centre ≈ 73–77 (±4), photo-estimate.]** Four vendor photos show the DB9 and VGA flanges nearly touching (gap ≲ 4 mm): TB2i78je, TB2el2ab/board.jpg, TB2WT4Ug and TB2A61Mg, taken from opposite sides. A 10 mm gap would be about 30 px wide in TB2i78je, and none is visible. Mapping TB2i78je through the hole-frame homography puts the VGA body at X ≈ 57.5–93 (its E side face is included in that). With the IR receiver at X ≈ 96–101, a VGA ending at 96 would collide with it. |
| D-sub flange (DB9 and VGA) | 30.8 wide × 12.6 high | mm | JAE DE-9 listing [S8a] | listing | Standard shell-E flange. Height above the PCB depends on mounting, so measure. Photo width checks out: 31.4 mm measured. *[Verifier: RS returned 403, so not re-read. A search snippet suggests the 30.8 × 10.8 × 12.6 JAE item is a cable-mount part. Amphenol right-angle shell-E DE-9 listings on RS give 30.81 mm × 12.58 mm, the same flange. Keep the listing tag.]* |
| PS/2 jack | 6-pin mini-DIN in a metal shield box (inferred) | — | [S2] "PS2-6PIN"; grey box in [S6] | vendor-doc + photo | NW corner, E of the NW hole, faces N, X ≈ 7–23. Size and height unknown. |
| IR receiver | 3-pin module (U10) | — | [S2] "红外接收 IR" | vendor-doc | NE corner, X ≈ 96–101, Y ≈ 7–15. Orientation unclear (possibly lying flat, facing E). *[Verifier: TB2WT4Ug shows it between the NE hole and key S4, about 11 mm S and 2 mm W of the hole centre, so centre ≈ (100, 16) ±3 (photo-estimate). The box above slightly overlaps the NE hole pad. The position is the photo-estimate it was; the "vendor-doc" tag covers only its existence (U10).]* |
| 1602/12864 LCD socket | 1 × 20 female, 2.54 pitch | — | [S2] "LCD 1602/12864" 20-pin | vendor-doc | Along the W edge, X ≈ 1–5, Y ≈ 33–84. Top entry. Photo length 51–52 vs. 50.8 nominal. |
| LCD contrast pot | blue trimmer (10 k, "RW") | — | [S2]; [S6] | vendor-doc | X ≈ 5–13, Y ≈ 13–19 (NW) |
| 7-segment display | 4-digit, common anode, ≈14 × 30 footprint | mm | [S2] "共阳数码管"; size from rectified TB2i78je | photo-estimate | X ≈ 5–20, Y ≈ 19–50. Long axis N-S. The size matches a 0.36" 4-digit part. One 0.36" listing gives 7.2 mm height [S8f]. *[Verifier: TB2WT4Ug shows the marking "…3641BH", i.e. 0.36", 4 digits, which fits the common-anode schematic. But [S8f] is a **3-digit** part (LCSC lists 22 × 14 × 7.2 mm), so its 7.2 mm height is only an analogy. Measure.]* |
| LEDs LED1–4 | SMD, flat | — | [S2]; [S5] TB2i78je | photo-estimate | X ≈ 88–97, Y ≈ 54–62 (E side). A power LED (D1) sits next to the USB-B. *[Verifier: TB2WT4Ug shows the LEDs in a row parallel to the E edge, with **LED1 southmost and LED4 northmost** (nearest the keys).]* |
| Keys S1–S4 | 6 × 6 tact | — | [S5] TB2i78je | photo-estimate | Column at X ≈ 98, Y ≈ 22.5 / 31.5 / 40 / 48.5. **[Verifier: corrected order.] S4 ≈ 22.5, S3 ≈ 31.5, S2 ≈ 40, S1 ≈ 48.5.** The silkscreen "S1 S2 S3 S4" is readable in TB2WT4Ug, TB2A61Mg and TB28RsGc, and S4 is always the key next to the IR receiver and VGA (N). The Y values agree with my TB2i78je re-estimate (22.2 / 30.8 / 39.4 / 47.3); only the labels were reversed. |
| DIP switch | 4-way, red | — | [S3] "Dial switch" ckey1–4 = pins 88–91 | vendor-doc + photo | Centre X ≈ 72, Y ≈ 41. Verifier: the [S3] p.1 pin mapping was re-read ✓; my TB2i78je re-estimate is (75, 43), within tolerance. |
| Buzzer | Ø ≈12 magnetic buzzer | mm | [S2] "SPEAKER" via Q5; [S6] | photo-estimate | Centre X ≈ 40, Y ≈ 41 (±4). Similar 12 mm buzzers are 9.5 mm tall [S8g]. |
| SDRAM U6 | TSOP-54, flat | — | [S2] HY57V641620; [S5] TB28RsGc | vendor-doc + photo | E of P2, roughly X ≈ 88–98, Y ≈ 73–103 |
| TFT / FPC connector | **none on the main board** | — | [S2]; [S5] TB2i78je (7" screen through an adapter board on the headers) | vendor-doc | Cameras, TFTs and Ethernet plug into "全能扩展板" adapter boards that sit on P1/P2/P3. |
| Bottom side | unknown | — | no photo found | unknown | 19 decoupling caps (C16–C34) are in [S2] but not visible on top in the close-up TB24uDrb, so they are **probably under the FPGA on the bottom** (inference). Expect THT pin tails everywhere. |

---

## Top-view layout sketch (rough; for cut-out planning only)

Scale is about 2 mm per character horizontally and 4 mm per line vertically. Boxes are footprints from photo rectification, with uncertainty **±3–5 mm**, worse for tall parts. `O` marks a mounting hole. The SW hole sits right beside the DC jack and switch, and the photos cannot separate them cleanly. Arrows show which way a connector opens.

```
                          N  (back)    ^ PS2, DB9, VGA open to the N
      X (mm from W) ->  0         20        40        60        80        100
                        +----:......:...............::...............:---------+
   Y=0 (N edge)         |    : PS2  :      DB9      ::      VGA      :         |
                        |   O:......:               ::               :     O   |
                        |  :...:    :...............::...............:  :...:  |
                        |  :pot:                                        :IR :  |
                        |  :...:                                        :...:  |
   20                   |  :.......:                                     S4:   |
                        |  :       :                                     :.:   |
                        |  :       :                                     :.:   |
                       :...: 7SEG  :                                     S3:   |
                       :|  :       :      :.....:         :....:         :.:   |
   40                  :|  :       :      : BZ  :         :DIP :         S2:   |
                       :|  :       :      :     :         :    :         :.:   |
                       :|  :.......:      :.....:         :....:         S1:   |   E
                       :|  :                                             :.:   |  (keys,
             LCD 1x20  :|L :                    :............:   :.: :....:    |  LEDs;
         (top entry)   :|  :                    :  P3 2x10   :   : : :LED :    |  no cable
   60                  :|  :             :..:   :............:   : : :....:    |  connectors)
                       :|  :             :  :                    : :           |
      W                :|  :             :  :                    : :           |
  (USB, LCD,           :|  :             :  :   :..........:     : :           |
   switch)             :|  :             :  :   :          :     : :           |
   80                  :|  :             :  :   :  FPGA    :     : :           |
                       :...:             :  :   : 57.5,86  :     P2:           |
                        |                P1 :   :          :     : :           |
                <==    :........:        :  :   :..........:     : :           |
       USB-B opens W   :|USB-B  :        :  :                    : :           |
   100                 :|       :        :  :                    : :           |
                       :........:        :  :                    : :           |
                        |                :  :                    : :           |
                        |:...:           :..:                    :.:           |
         power switch   |:SW:....:                                             |
   120  (cap up = DC)   |:  ::   :      :..........: :.........:               |
                        |:..::   :      :   AS     : :  JTAG   :     :.:       |
                        |   :DC  :      :  2x5 box : : 2x5 box :     RST       |
                        |   O    :      :..........: :.........:     :.:   O   |
                        |   :    :      (AS, JTAG: IDC plugs from ABOVE)       |
   136 (S edge)         +---:....:---------------------------------------------+
                            v DC jack opens to the S (unverified)
                          S  (front)
```

How sure each part of the sketch is:
- **High confidence:** which edge each item is on, the order of items along each edge, and which way PS/2, DB9, VGA and USB-B face.
- **Medium confidence:** the DC jack facing S, and the FPGA, P1, P2 and P3 positions (±3–4 mm).
- **Low confidence:** exact X of the AS and JTAG headers (±5 mm), heights, and the IR receiver orientation.

*[Verifier edits to the sketch:]*
- **Keys:** the labels were swapped, so S4 is now at the N and S1 at the S, as the silkscreen shows in three vendor photos.
- **N edge:** the VGA box moved W so that it nearly touches the DB9 (DB9 X ≈ 24–56, VGA X ≈ 58–90). The IR box moved 2 mm W.
- **Not redrawn, still uncertain:**
  - The USB-B box (Y ≈ 96–108 as drawn; true centre somewhere in Y ≈ 99–110).
  - The DC jack box, which probably sits a few mm further E (X ≈ 9–19) so that it clears the SW hole and the switch.
- **"Order of items along each edge":** correct for the edges, but it was wrong for the keys, so this was not fully "high confidence".

---

## Discussion

### Where each number came from (method)

There is **no dimensioned drawing** of this board anywhere I could find:
- The vendor PDFs contain no size. The manual is two pages of usage notes, and the schematic is electrical only.
- SlithyMatt's fork and its parent repo (jvitkauskas) hold the same files as `resources/`.
- No KiCad, STEP or case model turned up.
- rzrd.net now returns 404. The Wayback copy (2021-01-28) only carries Taobao detail images.

Those images are the best evidence available.

1. **Overall size.** The maker's acrylic-case photo carries the caption "尺寸: 136*106MM" ("size: 136 × 106 mm"). It does not say whether that is the PCB or the acrylic.
2. **Photo-scaling.** Vendor image TB2i78je is the shot with the 7-inch screen. It is the least oblique photo, and all 4 mounting holes are visible in it. I fitted a projective transform (homography) mapping the 4 hole centres onto a 96 × 126 mm rectangle, then checked the result against parts of known size:
   - 1×20 LCD socket: measured 51.4–52 mm vs. 50.8 nominal.
   - VGA body: measured 31.4 mm vs. 30.8 nominal.
   - Rectified PCB outline: 107 × 136 mm.
   
   All of these agree to within about 2 %, which supports 136 × 106 being the PCB itself and the holes sitting about 5 mm in from each edge.

   *[Verifier: this overstates it. Three problems:*
   - *The 96 × 126 target rectangle came from the caption (136 × 106 minus about 5 mm per side). So "outline = 107 × 136" mostly restates the caption.*
   - *Only the LCD socket (N-S) and the VGA (E-W) are independent scale checks, and both read ~2 % large, in the same direction.*
   - *Both are tall parts (≈8.5 and ≈12.6 mm). A camera a few hundred mm away makes things that tall look about 2–4 % larger, because they sit closer to it.*

   *So the data is consistent with a 136 × 106 PCB, and also with a PCB 2–3 mm smaller inside 136 × 106 acrylic. Neither the size nor the hole pitch is established; both must be measured.]*
3. **FPGA position.** Two estimates agree to within about 1–3 mm:
   - (a) The acrylic-case image TB2el2ab, rectified with a 7-point least-squares homography (residuals 1–7 px). The FPGA comes out square, 22 mm across including leads, centred at hole-frame (52, 81).
   - (b) The close-up TB24uDrb, rectified on the FPGA body as a 20 mm square. This reproduces the 2.54 mm header pitch on P1 and P3, and gives P1 at −22 mm, P2 at +24 mm and P3 at −26.5 mm (north) from the FPGA centre. Combining that with P2's position in TB2i78je gives (52.5, 81).
   
   Adding the ≈5.5 mm (W) and 5 mm (N) hole insets gives X ≈ 57.5, Y ≈ 86.
4. **Lean bias.** Tall parts lean away from the camera in an oblique photo. In TB2i78je the camera is SE of the board, so the tops of tall parts shift toward the NW. In TB2el2ab and board.jpg the camera is SW, so tops shift NE. Positions of tall parts (connectors, box headers, switch, display) therefore carry ±4–5 mm. The flat FPGA and SMD parts are better, about ±3 mm.
5. **Facing direction of the DC jack.** In TB2wl6nb, TB2WT4Ug, TB28RsGc and the rectified TB2i78je, the jack's long axis (≈15 mm) lies **parallel to the W edge**. Its flange end is at the S edge, and the switch and USB-B sit directly N of it. A jack aligned like that can only open to the S. Treat this as medium confidence until Alex looks at his own board. *[Verifier: there is better evidence in the vendor's own manual, [S1] p.1. Its first photo is nearly top-down. It shows the corner standoff, the switch and the USB-B along one edge (the W edge, with the USB-B mouth on it). The DC jack's square mouth face is on the adjacent edge, and the second photo on that page shows the AS and JTAG boxes on that same edge. TB2wl6nb shows the same thing, with the jack's mouth and the AS box on one edge. So the jack faces **S** (vendor-doc photo, RZRD board).]*

### Power input, mechanically

- **USB-B is power only.** USB pins 2/3 (D−/D+) are not connected; pin 1 goes to the switch [S2]. It cannot carry JTAG or data. The silkscreen reads "USB供电" (USB power) [S5].
- **The red cap selects the source.** Pressed (down) = USB power. Released (up) = 5 V barrel jack [S1 p.1].
  - If the box feeds the board through the barrel jack (INA226 inline), the cap stays **up**, which is the tallest state. The lid or window must clear it, or a cut-out must expose it.
  - If the box feeds the board through a USB-B cable with the shunt inline, the cap stays down.
- The two inputs exit on **different edges**: the USB-B on the W edge, and the DC jack on the S edge (if the reading above is right). Plan only the one that will be used, plus a blanking plate.
- `board-power.md` covers the electrical side.

### Heater-clamp envelope around the FPGA

- **Package:** the top is 1.45–1.65 mm above the PCB. The body is 20 × 20 mm; the 0.5 mm-pitch gull-wing leads reach 22 × 22 mm [S4].
- **Contact area:** the heater and thermal pad should sit **inside the 20 mm body**, so nothing metal can touch or bridge the leads.
- **Small parts next to the package:** ferrite beads and caps FB1–FB4 and C11–C14 sit 3–5 mm off the package corners (TB24uDrb).
- **Tall parts boxing it in:** P1 on the W side, P2 on the E, and P3 on the N. The clear width between the P1 and P2 header bodies is about **41 mm**. Header pins (and any Dupont or logic-analyser grabbers on them) rise well above the FPGA top, so a clamp arm has to come in from the S side or bridge over the headers. *[Verifier: the S side is not open either. The JTAG box header (X ≈ 56–76, Y ≈ 124–132 by this report's own estimates) sits directly S of the package (X ≈ 46.5–68.5). Under BRIEF §4 the USB-Blaster stays plugged in, so its IDC plug and ribbon occupy that approach. A bridge over the headers, or a lid-mounted spring, looks like the safer default.]*
- **There are no mounting holes anywhere near the FPGA.** The nearest anchors are the four corner holes (pattern ≈96 × 126 mm), or the enclosure itself. A clamp hanging from two diagonal corner standoffs would load the PCB in the middle. Bridging across two standoffs on the same edge, or using a lid-mounted spring, keeps the load even (BRIEF §5).

### Things that need clearance from above (lid design)

- **JTAG and AS are top-entry box headers** about 4–13 mm in from the S edge. A plugged-in USB-Blaster IDC plug plus its ribbon bend needs room above the board, then a path out through the S or W wall. *[Verifier: a typical vertical 2×5 box header is ~9 mm above the PCB (3M 30310-6002HB lists 9.3 mm [S8h]), not 12. The IDC plug and the ribbon bend add more height on top; measure that with the cable inserted.]*
- **The vendor warns that plugging or unplugging JTAG/AS while powered can destroy the FPGA** [S1 p.1]. The box should let the JTAG cable stay connected permanently, with strain relief.
- The LCD socket and headers P1/P2/P3 are also top entry.

### Things on the bottom

- Nothing is documented and no bottom photo was found.
- Expect THT tails from every connector, header, display, buzzer and switch.
- The schematic lists 19 decoupling caps (C16–C34) that do not appear on the top side near the FPGA. They are probably on the bottom, under the package. That matters if anyone puts a sensor or heater under the board. It also means standoffs must not land under the FPGA area.
- The exposed pad is soldered to GND, so the area under the package on the bottom is likely a thermal-via field (inference).

### Side findings (out of this topic; see the sibling reports)

- **Clock-capable inputs on the headers** [S2, S3]:
  - FPGA PIN_24 (CLK2) is on **P1 pin 34**.
  - PIN_88–91 (CLK7..CLK4) are on **P3 pins 5–8**. They are shared with KEY1–4 (10 k pull-ups plus push buttons) and the DIP switch.
  
  `clock-pins.md` should be the authority on this.
- The schematic shows an **LM75 temperature sensor (U9)** on SCL/SDA = FPGA pins 112/113 [S2, S3]. If it is fitted, it is a free board-temperature reading. Whether it is fitted is unverified: look for "U9". *[Verifier: the schematic was re-read ✓. U9 LM75 has 5.1 k pull-ups R27/R28 and A0–A2 tied to GND, and its SDA/SCL nets are on P1 pins 4/3 as FPGA 113/112. The maker's archived page text lists "板载…温度传感器芯片LM75A" (LM75A fitted on board), which is evidence for the RZRD board. Alex's board is still unverified.]*
- *[Verifier, for `clock-pins.md`: KEY1–4 = PIN_88–91 each carry **two** 10 k pull-ups (R38–41 and R42–45), a 220 Ω series resistor, a push button to GND, **and** a DIP-switch position to GND [S2]. Any DIP position left ON holds that clock pin at GND. The DIP switch must be all OFF before PIN_88–91 can be driven from outside.]*

### Variant risk

- Alex's board is sold as **OMDAZZ**. The photos in `resources/board.jpg` and all vendor images carry the **RZRD** ("www.rzrd.net") silkscreen.
- One FPGA course repo [S7] says the two boards differ functionally only in LED pin order. CLAUDE.md records that Alex's LED order is indeed reversed against the vendor table, so his board is not identical.
- The schematic is **V2.1 (2014-12-09)**, while the board is sold as **V3.0**.
- The vendor photos themselves vary: switch cap colour, P1 populated or not (TB2wl6nb shows bare P1 pads).

**So no position on this page should be used for a cut-out until Alex confirms it on his own board.**

### What Alex must measure (calipers; reference = PCB edges, not the acrylic)

1. PCB length (N-S) and width (E-W), with the acrylic removed. Measure thickness at an edge. Note the corner radius.
2. For each hole: distance from the hole edge to the W/E edge and to the N/S edge, plus the hole diameter (centre = edge distance + radius). Also measure the pad diameter, which sets how big a standoff can be.
3. Standoff thread (does an M3 screw fit?), across-flats, and lengths above and below the PCB.
4. FPGA: distance from the W edge and N edge to the body edges (centre = mean). Measure the package top height with a depth gauge from the PCB.
5. Every edge connector: centre position along its edge (from the NW corner), width, height above the PCB top, and overhang past the PCB edge:
   - PS/2, DB9, VGA and the IR receiver on N
   - USB-B on W
   - DC jack: also **confirm which edge it opens to**
6. Power switch height with the cap up and down. Write down which position is DC power.
7. JTAG and AS: position along the S edge, box height, and height with the USB-Blaster plug inserted and the ribbon bent.
8. P1, P2 and P3: pin-1 corner position, and pin height above the PCB.
9. 7-segment display and LED1–4 footprint positions, for the window.
10. Tallest component (lay a steel rule across it).
11. Bottom side: a photo, the longest protrusion, and anything SMD under the FPGA.
12. Board marking and revision text (OMDAZZ vs RZRD, "V3.0").
13. DC plug size (5.5/2.1 or 5.5/2.5): try a plug.

### Sources

- **[S1]** `resources/Altera-Cyclone-IV-board-V3.0 documentation/Dev Board Manual.pdf`, p.1 (power switch modes, AS/JTAG hot-plug warning, photos).
- **[S2]** `.../Hardware documentation/Development board schematic diagram V2.1.pdf`, single sheet, dated 2014-12-09 (blocks used: Power and light, IO interface P1/P2/P3, JTAG and AS, VGA, RS232, PS2, IR, temperature sensor, U5 GND 145).
- **[S3]** `.../Hardware documentation/Development board pin information.pdf`, pp.1–2.
- **[S4]** `.../Cyclone IV chip/EP4CE6 package information.pdf`. Altera 04R-00402-1.0, 144-pin EQFP, p.1 dimension table.
- **[S5]** Maker's product page, rzrd.net (live page 404 on 2026-10-23), archived at http://web.archive.org/web/20210128152708/http://rzrd.net/product/?79_502.html. Detail images under `https://img.alicdn.com/imgextra/.../133921378/`:
  - TB2el2abVXXXXc3XXXXXXXXXXXX (acrylic case, 136*106MM)
  - TB2i78jeFXXXXb6XXXXXXXXXXXX (top-ish view with 7" screen)
  - TB24uDrbVXXXXXwXXXXXXXXXXXX (FPGA close-up)
  - TB2wl6nbVXXXXarXXXXXXXXXXXX (power input close-up)
  - TB2gojebVXXXXckXXXXXXXXXXXX (AS/JTAG close-up)
  - TB2WT4UgVXXXXbeXpXXXXXXXXXX, TB28RsGcpXXXXXbXpXXXXXXXXXX, TB2A61MgVXXXXXtXXXXXXXXXXXX (add-on boards)
- **[S6]** `resources/.../board.jpg` (same pose as TB2el2ab; 501 × 461 px).
- **[S7]** https://github.com/yuri-panchul/basics-graphics-music/tree/main/boards/rzrd (README: RzRd vs Omdazz differ only in LED pin order; header pinout images).
- **[S8]** Generic-part listings, used only for typical sizes:
  - (a) JAE DE-9 socket, RS: https://uk.rs-online.com/web/p/d-sub-connectors/1756433 (30.8 × 10.8 × 12.6 mm)
  - (b) Würth 61400416121 USB-B, https://www.lioncircuits.com/parts/61400416121 (height 11.25 mm; field labels not verified)
  - (c) DC-005, https://uelectronics.com/producto/conector-dc-power-jack-socket-hembra-para-arduino/
  - (d) DC3-10P box header, https://thinkrobotics.com/products/shrouded-box-header-2x5-pin-dc3-10p-4-pieces
  - (e) 3M 929836-03-22, https://www.datasheets.com/3m/929836-03-22
  - (f) ARKLED SP410361N 0.36" display, https://www.lcsc.com/product-detail/C98923.html
  - (g) TMB12A05 buzzer, https://www.thingbits.in/products/tmb12a05-5v-dc-active-buzzer-12-x-9-5mm
  - (b′) *[added by verifier]* Würth 61400416121 manufacturer datasheet, p.1 drawing: https://www.we-online.com/components/products/datasheet/61400416121.pdf
  - (h) *[added by verifier]* 3M 30310-6002HB 2×5 vertical box header, profile height 9.3 mm (distributor listing): https://www.ozdisan.com/en/p/box-headers-295/3m-30310-6002hb-610429

---

## Verification (adversarial pass)

Done 2026-10-23 by a second agent. I re-opened the primary sources myself:
- the four vendor PDFs, read with PyMuPDF; the schematic was rendered and cropped;
- the archived rzrd.net page, both its HTML text and all eight of its detail images, downloaded from img.alicdn.com;
- the Würth datasheet;
- the box-header and LCSC listings;
- the yuri-panchul README.

I then ran my own 4-point homography on TB2i78je from the four bare hole centres. Every position I give is a **photo-estimate**, the same class as the original. I measured nothing on Alex's board.

### Confirmed (re-derived from the primary source)

| Claim | Source re-read | Result |
|---|---|---|
| Caption "尺寸: 136*106MM" on the acrylic-case image | TB2el2ab, downloaded from img.alicdn.com | ✓ present, on a photo headed "定制透明板保护" (custom clear-plate protection). The page text has no size. Tag stays **listing**. |
| EQFP-144: A 1.45/1.55/1.65; A1 0.05–0.15; D/E 22.00; D1/E1 20.00; D2/E2 5.25/5.40/5.55; e 0.50 | [S4] p.1 table | ✓ all match |
| Pad = GND pin 145 | [S2] U5L block | ✓ |
| P1 = 2×19, P2 = 2×22, P3 = 2×10; AS and JTAG = HEADER 5X2; SW-DPDT; PS2-6PIN; U10 IR; SPEAKER; dated 2014/12/9 | [S2] text layer and render | ✓ |
| USB pins 2/3 open, pin 1 → switch, pin 4 and shell → GND | [S2] "Power and light" render | ✓ USB is power only |
| Pressed = USB, lifted = 5 V adapter; AS/JTAG hot-plug warning | [S1] p.1 text | ✓ verbatim |
| P1 pin 34 = FPGA 24 (CLK2); P3 pins 5–8 = 88–91 (CLK7..CLK4); DIP ckey1–4 = 88–91; SCL/SDA = 112/113 | [S2] P1/P3 render; [S3] pp.1–2; `EP4CE6 pin information.pdf` | ✓ |
| LM75 = U9 on SCL/SDA | [S2] render | ✓. The maker page also says LM75A is fitted (RZRD board). |
| 3 expansion headers at 2.54 mm; 1×20 LCD socket; square-USB power socket; self-locking power switch; 5 V DC socket | archived rzrd.net page text | ✓ |
| "Only functional difference between RzRd and Omdazz is LED pin order" | yuri-panchul README | ✓ (functional only; says nothing about mechanics) |
| Header-pitch arithmetic (45.7/18, 22.9/9); 41 mm gap; 48.5 / 50 mm edge distances; header lengths 48.3 / 55.9 / 25.4; LCD 50.8 | arithmetic | ✓ |
| P1 −22 / P2 +24 / P3 −26.5 mm from the FPGA centre; FPGA Y ≈ 86 relative to the P1/P2 S ends | my rough re-scale of TB24uDrb on the 20 mm body | ✓ consistent (about −21 / +24…28 / −25) |
| DIP, RESET, JTAG, keys (Y), P2 N end, AS | my TB2i78je homography, in the author's frame | ✓ within 1–5 mm |
| Only 4 mounting holes, none near the FPGA | TB2i78je | ✓ |
| 7-segment is 0.36", 4-digit | TB2WT4Ug part marking "…3641BH" | ✓ (new evidence) |

### Corrected

1. **Key order was reversed.** The silkscreen in TB2WT4Ug, TB2A61Mg and TB28RsGc shows S4 next to the IR receiver and VGA (N), and S1 at the S end. Fixed in the table and sketch: S4 ≈ 22.5, S3 ≈ 31.5, S2 ≈ 40, S1 ≈ 48.5. LED1 is also the southmost LED.
2. **The DB9–VGA gap was about 10 mm in the original; it is ≲ 4 mm.** Four photos taken from opposite sides show the two shell-E flanges nearly touching. The VGA moves from X ≈ 65–96 to **X ≈ 57–90** (photo-estimate, ±4). That also stops it colliding with the IR receiver. For the enclosure, one combined cut-out of about X 24–90.
3. **USB-B centre Y:** the original gave 99 ± 3. Three re-estimates gave 105–112, so it is now **UNVERIFIED, Y ≈ 99–110**.
4. **USB-B height:** the listing's 11.25 mm is replaced by the manufacturer drawing for that same Würth part: 10.62 shell / 11.05 overall, 12.04 wide, 16.5 deep.
5. **Box-header height:** the listing's "12 mm" probably includes pin tails. A 3M vertical 2×5 box header lists 9.3 mm (listing).
6. **"Alex's photo" was wrong.** `board.jpg` is the vendor image in `resources/`, the same shot as TB2el2ab.
7. **The 136 × 106 photo cross-check was circular** (frame scaled from the caption). It is downgraded from "agrees within 2 %" to "consistent with; cannot tell PCB from acrylic". The hole pitch 96 × 126 is marked UNVERIFIED.
8. **Internal inconsistencies flagged, not silently fixed:**
   - P1 X 34 vs 57.5 − 22 = 35.5.
   - The DC jack box (X 6–16) overlaps both the SW hole pad and the switch box. The jack is more likely at X ≈ 9–19.
   - The IR box slightly overlaps the NE hole pad.
9. **Heater-clamp access:** added that the S approach is blocked by the permanently plugged JTAG box, IDC plug and ribbon.
10. **[S8f] is a 3-digit display** (22 × 14 × 7.2 mm). Its 7.2 mm height is an analogy only.
11. **Side finding for `clock-pins.md`:** PIN_88–91 also carry DIP-switch positions to GND, so the DIP switch must be all OFF before those pins can take an external clock.

### Still unverified (Alex must measure; the original "What Alex must measure" list stands)

- PCB size and thickness; hole pitch, hole Ø and pad Ø; standoff thread and lengths. **The hole pitch is the single number most likely to ruin a print.**
- Every connector position. Each is a photo-estimate at ±3–5 mm or worse, and the USB-B Y is ±6.
- All heights: the switch cap (14–25 mm across two estimates), D-subs, box headers, header pins, the 7-segment, the buzzer.
- Which edge the DC jack opens to on **Alex's** board. The RZRD vendor photos and manual agree on S.
- Bottom side: nothing found.
- Whether Alex's OMDAZZ PCB matches the RZRD photos mechanically at all. The only cross-brand source compares function, not layout.
- Listings I could not re-open (HTTP 403): RS JAE DE-9 [S8a], 3M 929836 mating length [S8e], DC-005 [S8c]. Their numbers stay **listing**, not re-checked.
