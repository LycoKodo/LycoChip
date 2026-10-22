# Concept massing models: what modelling them found

Each concept in this folder was built as a rough CadQuery massing model (`<concept>_model.py`, renders in `renders/`) on 2026-10-23. Building them exposed places where a concept's own numbers do not add up. These feed DESIGN.md; they are findings from a massing sketch, not verified against hardware.

## demo-first

**Simplified in the model:** This is a massing sketch only. Every part is a box or cylinder at the concept's stated coordinates. Board positions come from the photo estimates in board-mechanical.md.

Frame: the concept's frame (X east, Y south, Z up) is left-handed. The script maps it to world (x, -Y, z), so the renders are not mirrored. The top view has N up and E right, and the 'front' camera stands at the S (visitor) face.

Left out:
- fillets, gussets, rebates on the I/O apertures, inserts and most screw holes
- every engraving and label on the tray, bezel and walls
- the thermocouple and its groove, the snap-cover wire channel on the arm, and the hinge service loop
- all wiring except the JTAG ribbon, the dongle USB cable and the 5 V pigtail
- the bezel's M2.5 screws, the JTAG strain-relief clamp, the analyser strap and backstop, and the shroud's pin-34 hole
- the clamp foot's floor bosses and the ±5 mm cross-slots

Approximated:
- HS10: flange + central tube + 4 fins.
- Fan: frame, hub and 7 flat blades.
- Modules: a PCB on 3 mm bosses plus a terminal or header block. Heights are generic: analyser clone 20.3, star-GND lever block 16, the others about 6.
- Headers: a 2.54 mm black body plus two pin-row bars up to PCB+8.5, using the 3M mating length of 5.97 from the listing.
- D-subs: flange at the PCB edge, shell out to Y -6.
- Switch cap at PCB+20; 7-seg 7.2 mm tall.
- IDC plug top at PCB+17.5, with the ribbon at PCB+30.
- USB-Blaster dongle assumed 60 x 21 x 14 in the gallery.

Choices I made where the concept leaves it open:
- P1 pin 1 is assumed at the S end. That makes the Si5351 N site active (the S site is drawn translucent), puts the CLK-IN shroud at P1's N end, and puts the comb in its S position, hung from the tray edge (Z 8..33).
- The acorn nut is drawn 4.2 mm tall, which is the most that fits (see spec_problems), not a real part.
- The Ø8 lid bosses sit 4 mm from the inner walls, i.e. free-standing, which shows the conflict with the acrylic.

Rendering:
- The sections are CadQuery boolean cuts (shape ∩ half-space), not render()'s clip plane, so the cut faces render solid. The full section keeps the whole N half behind the cut. The zoom keeps only a 16 mm slab (Y 70..86) so the stack reads without background clutter.
- The legend, the labels on the top view and the leader callouts on both sections are added with PIL after rendering. Their pixel positions are computed from render()'s camera fit (bounding sphere, Zoom 1.15) and were checked by eye on each PNG.
- A pairwise BRep interference check runs at the end of the script and prints any overlap above 0.5 mm³.

**Problems found in the concept's numbers:**

- Lid screws versus the acrylic: the M3 x 16 lid screws and Ø8 hanging bosses cannot coexist with the acrylic pocket and the skirt as written. Outside the 184.6 x 166.6 pocket the ring band is only 5.7 mm wide (X -79..-73.3, Y -9..-3.3). A free-standing Ø8 boss against the wall (axis about 4 mm inside, e.g. X -72) puts its screw through the acrylic sheet; the model reports 16.6-18.9 mm³ of overlap per screw, all 6 screws. The screw axis has to sit at about the wall's inner face (X/Y ≈ -76), which means half-buried bosses. Separately, the 3 mm skirt (0.4..2.4 mm inside the walls, Z 67.6..70.6) collides with the bosses (320 mm³ in total in the model) and will hit the screws wherever they go, so it needs 6 notches. The bezel's 4 x M2.5 screws must also fit in that 5.7 mm band.
- Acorn nut height: the barrel bottom (Z 41.6) is 4.05 mm above the cap top (Z 37.55). A Ø5.5 dome seated on the Ø3 countersink rim has its tip at Z 37.10. Engaged (head lifted 2 mm), the nut's top must stay below the lip, so the whole acorn nut must be ≤ 4.5 mm tall with zero clearance. Common M3 acorn (dome) nuts are, from memory and unchecked this session, about 5.5-6 mm tall. The concept lists the nut height as MEASURE, but the stack leaves no room for a standard part: the barrel or the arm would need to rise about 2 mm, or a low dome would be needed.
- Clamp foot fixing has no room: the foot is X -43..-8 x Y 76..96 (700 mm²). The mast fin's 16-thick lower part (X -36..-8, Y 78..94) covers almost all of it; only 252 mm² is reachable from above (a 7 x 20 strip W of the fin plus two 2 mm side strips). Two M3 screws in ±5 mm cross-slots with fender washers do not fit: a ±5 mm X-slot alone needs at least 13.4 mm of free foot length. The foot cannot grow either: the Si5351 sites are at Y ≤ 73.6 and ≥ 100, the harness zone is at X ≤ -44, and the sole runs under the PCB. The screws would have to come down through the fin (deep counterbores), or the fixing has to move.
- Si5351 'twisted pair' cannot stay twisted: P1-1/2 (stated as P1's only GND pins) and P1-34 are 16 rows apart, which is 40.6 mm. The CLK0 + GND pair must split for about 40 mm along P1, a large return loop for the clock. With pin 1 at the N end, the GND lead also runs under the arm band (Y 78..94, at ≤ PCB+25).
- BME280 versus the shield: the card is placed at Z 2..27 (a 25.4 mm card), but the solid shield is Z 0..24. The top 3.4 mm of the card stands above the shield, in the fan-opening band (Z 24..64). The 'no line of sight to the heater' claim then rests only on the fan rotor and the mast fin happening to be in the way. The shield cannot rise without raising the fan, whose bottom edge is at Z 24.
- Logic analyser height: the clone's 20.3 mm height on the tray top (Z 8) gives Z 28.3. That contradicts §8's 'modules ≤ Z 25'. Its stated Y span of -5.5..50 (55.5 mm) is also 0.5 mm shorter than the clone's 56 mm length, and it already sits 0.5 mm from the N wall's inner face.
- Analyser lead comb: the printed comb's bounding box (30 x 10 x 25) does not fit its stated envelope. The tray/board gap is 8 mm wide (X -8..0), and the two positions are 18 mm (Y 54..72) and 14 mm (Y 98..112) long. The S position sits directly in front of the USB-B mouth (Y ≈ 99..111 in board-mechanical), with zero margin to the flush blank plug. The clamp sole also fills that gap at Y 71..101, Z 0..8, so a comb standing on the floor would overlap it by 1 mm (N position) or 3 mm (S position). It has to hang from the tray edge.
- Window area: the 172 x 154 opening is 75.9% of the 196 x 178 top, not 'about 82%'. 81.1% is the figure against the 190 x 172 interior. The W 7 mm of the Pico, MAX31855 and D4184, and all of the duct and fan's W half, sit under the opaque ring band (the opening starts at X -67), which works against the demo intent that a visitor sees a label beside every module.
- AO3400 overhang: the AO3400 module is placed at X -28..-8, but the tray's E edge is X -8.4, so it overhangs by 0.4 mm into the gap that the comb and sole use. This is trivial but contradicts 'no collisions'.
- D-sub shells versus the N wall (low confidence): the N gap is 6 mm. A right-angle D-sub shell typically protrudes about 6 mm past its flange (from memory, unverified). With the flange at the PCB edge, the DB9/VGA shells reach the N wall's inner plane at Y -6, leaving about 0.5 mm to a 2.5 mm blank plate mounted flush with the outside. Any flange overhang past the PCB edge, which is unmeasured, makes them hit the RS-232/VGA blank plate.
- Checked and fine: the arm band (Y 78..94, at PCB+30 and above) is 31 mm N of the JTAG IDC plug (Y 125..131), so the S-side conflict flagged in board-mechanical.md is avoided. The stack heights (insulation, foot, angle, HS10, cap at PCB+19.95), the 4.05 / 3.35 mm barrel clearances, the 5.2 mm lid clearance over the preload screw (Z 65.4) and the vent areas (1680 / 1932 mm²) all reproduce from the concept's own numbers. With the fixes above, the model reports no other interference above 0.5 mm³.

## thermal-first

**Simplified in the model:** This is a massing sketch only, so it leaves a lot out:

- **Simplified geometry:** there are no fillets, rounded PCB corners, heat-set inserts, thumbscrews, dowels, gantry pads, lid corner bosses, engraved labels or cradle cable channel. Glands are holes with black stubs. The nozzle is a ruled hollow loft with 1.6 mm walls and no snap flange. The fan is a box with a bore and a hub. Headers are a body plus two thin pin-row bars. D-subs are a body, a flange and a shell nose.
- **Spreader:** the thermocouple groove and the Kapton darts are not cut. The plunger is a plain Ø4 rod, with no countersink modelled. The spring is a 4-turn helix sitting in the beam bore at Z 55-61.4 under a cap.
- **Assumed sizes (the concept does not give them):** HS10 base 16x16x2.5 with a 16 x 11 x 8.5 box body; KSD9700 15 x 7.5 x 4; Blaster 46 x 23 x 18; logic analyser 54 x 26 x 13, lying along Y at Y 129-183, Z 38-64 on the W wall; Si5351 module 26 x 18; Pico pins; 12 V jack and fuse-holder body lengths, both at Z 30; USB-C inlet 12 x 15.
- **Board parts:** positions are the research photo-estimates mapped with X = x+27, Y = y+11. The USB-B is at board y 99, 12 wide, with a 5 mm dummy-plug grip. The DC jack is at board x 9-19, and the plug is drawn in line with the jack, not in the concept's X 44-58 zone. The back-support post is at dx = dy = 0.
- **Lid:** I read it as a 4 mm top border, with the acrylic in a 3 mm pocket at Z 82-85 (leaving a 1 mm lip) and the retaining frame below at Z 78-82.
- **Wires:** the thermocouple, the heater pair and the LA lead bundle are straight pipe segments on my own routing, following the concept's description. The I2C, Si5351 clock, 5 V pigtail and star-ground leads are left out.
- **Render settings:** in open_iso the S and E walls are drawn see-through (opacity 0.18). The annex cover is removed together with the lid in the open views.

**Problems found in the concept's numbers:**

- The inlet nozzle collides with the gantry's E portal. The nozzle grows from 24 mm tall at X 139 (top Z 48) to 40 mm at X 161 (top Z 56). At X 151 its inner top is already at Z 52.36, and its outer top is at Z 53.96 with a 1.6 mm wall. The portal crossbeam and the raised beam underside sit at Z 52 over X 133-151. The model measures 233 mm3 of overlap (shown in pink in section_detail). Possible fixes: raise the portal underside to at least about 56, move the portal W of X 139, or keep the nozzle at a constant height under the portal.
- The fan mounting conflicts with the nozzle bore. The 4010 is said to screw into bulkhead inserts on the 32 mm pattern (holes at +/-16 mm from centre). But the nozzle's 40x40 inlet (46 x 48 bounding box) 'snaps into the bulkhead bore', so the bore must be at least 40x40 (+/-20 mm). The insert positions would then fall inside the hole. Either the fan screws through a nozzle flange, or the nozzle mounts some other way.
- The carriage height does not agree with itself. The parts table gives 40 x 26 x 22, but the height chain gives the carriage as Z 62-70 (8 mm), with the knob top at 78 and the ceiling at 82. A 22 mm carriage on the beam top would reach Z 84, above the ceiling.
- The section drawing puts the spring inside the beam bore (Z 48-62), but section 7 says a slot in the carriage shows the seat washer and cap against a mm scale. Also, the 3 mm guide bush plus the seat nut and washer plus the spring at 8 mm compression already fill the 14 mm beam. The 16 mm free length cannot be assembled inside the beam.
- The ball and plunger do not seat as described. An M4 rod is 4.0 mm across, but a 90-degree cone touches a 6 mm ball on a 4.24 mm circle. So the ball bears on the rod's rim edge, not on the cone faces as 'ball between two cones' implies. The rod tip sits at about Z 39.3, with the ball top at Z 40.1.
- The Si5351 bracket position looks like a board-frame number. It is 36 mm long but placed 'at X 30-60 ... above P1'. In the box frame P1 is at X 60-65 (board x 35.5), so X 30-60 is W of P1, over the LCD socket and 7-segment area. The bracket must also clear the carriage, which starts at X 64.5. Centred at X 45 it spans X 27-63, which leaves 1.5 mm.
- The DC plug zone does not line up with the jack. The concept puts it at X 44-58 (centre 51), but the research has the jack at board x 9-19, which is box X 36-46 (centre 41). That is about 10 mm off. The LA brush slot (Y 138-162) is directly W of the jack and plug, so the LA leads from P1 must cross over the DC plug and pigtail on the way out.
- The LA brush slot is given as '30 x 6 at Y 138-162, Z 26-34', but those ranges are 24 x 8.
- The airflow text says the jet sweeps 'across the keys'. The keys are at box Y 30-63 (and the LEDs at Y 65-73), which is outside the nozzle's Y 75-119 jet band. Only the SDRAM, P2, the spreader stack and P1 are in the jet.
- The gantry W post (X 9-21, Y 90-104, Z 7-62) stands 6 mm in front of the W exhaust grille (Y 62-132, Z 24-62). It blocks 14 of the 70 mm of slot length (20%), right on the jet axis (Y 97). So the exhaust area is effectively smaller than the 1680 mm2 claimed.
- The USB-B dummy plug has almost no room next to the W post. At board y 99 the USB-B socket spans box Y 104-116, so its N edge lines up exactly with the post's S face (Y 104). Any dummy grip that sticks out more than 6 mm W of the board edge would hit the post. With a 5 mm grip the model leaves 1.0 mm. The verifier's re-estimates (board y 105-112) move the socket S, which would ease this.
- The chamfer clearance claim depends on the HS10's real shape. The concept claims at least 7.0 mm of air from the HS10 to the ASA. With my assumed box-profile body (16 long, 11 wide, 8.5 high, centred at Y 111), the model measures 6.3 mm from the body to the chamfered beam. The bent-up tags clear by 7.2 mm and the heat-shrink by 6.5 mm. The HS10 width and height need measuring before this is trusted.
- The lid build-up is ambiguous. The concept puts 3 mm acrylic 'in lid top Z82-86' on a 4 mm ledge under the 144 x 164 opening, held by a 4 mm retaining frame. Either the PETG over the ledge is only 1 mm thick (acrylic at Z 82-85, frame below at Z 78-82, which is how I modelled it), or the frame sits on top and the box is 90 mm tall, not 86.
- The carriage's 7 mm holes give +/-1.8 mm of adjustment for an M3 (3.4 mm shank). But a standard M3 socket head (5.5 mm) is smaller than a 7 mm hole, so it needs large washers. The concept does not list any.
- Minor: the Blaster holster (X 110-160) overhangs the cradle (X 6-158) by 2 mm. The Pico (Y 5-56) and the MAX31855 (Y 56-76) touch with no gap.
- These checks came out OK: the Blaster IDC plug and ribbon are 32 mm from the gantry. The plate-to-P1, P2, P3 and JTAG gaps match the concept (9.5, 11.5, 10 and 15 mm in plan). The knob clears the acrylic by 4.0 mm. The P1 Dupont housings clear the beam by 6.9 mm. The thermocouple can be routed 12 mm or more from the heater wires.

## simple-first

**Simplified in the model:** Every part is a box, cylinder or hex prism. There are no fillets, drafts or engraving, and no heat-set inserts. Not modelled: the plate's rails, pads and floor bosses, tie slots, the bridge's tie holes, the thermocouple groove, and M2/M2.5 holes. The W wall is a 4 mm frame with a plain groove holding the panel.

Board dummy: positions the concept does not give come from board-mechanical.md photo estimates:
- USB-B centre at by ~104
- DB9 at bx 24-56 and VGA at bx 58-90, with a 7 mm shell overhang
- keys, LEDs and DIP switch
- IR receiver moved to the verifier's centre (bx 100, by 16), because the original estimate touches the NE screw head

PS/2, the LCD socket, SDRAM and the bottom-side THT tails are omitted. The FPGA package is 1.65 thick (the concept's max A, so the stack touches), not 1.55. Headers are 2.5 mm of plastic with pins to 8.5 mm above the PCB (the concept's assumption). A translucent grey box up to Z 36.1 stands for the assumed Dupont housings.

Clamp details:
- HS10 is a 2-step block (18x17x2 flange plus a 16x16.5x6.8 body) with no fins.
- HS10 lugs run N-S at Z 39-39.8. HS10_LUG_Z is unknown, so this height is my guess.
- KSD9700 is a plain 20.5x7.5x3.7 box, and the coated tie is flat bands.
- The plunger is a cylinder with a 3 mm ball. The legs are 25+20 hex prisms; no studs or screws are shown inside them.

Cables: only the heater pair (one red line, on the bridge N edge) and the thermocouple (yellow, on the S edge) are shown, both routed roughly down the W leg. Not shown: KSD leads, the 5 V/12 V harness, the Si5351 pair and logic-analyser leads. The JTAG ribbon is a flat strip at Z 43-44 on 3 mm foam, and the lid tongue bottom is set at Z 44.

Fan: a 40x40x10 frame with a hub and no blades. The grille's rings and spokes are approximate.

Panel connectors are generic bodies:
- USB-C cut-out 12x6 (placeholder)
- 12 V jack: the Ø8 P0622 option
- fuse holder: Ø12 x 40 inside, Ø15 cap outside

Lid: the locating lip is 2 mm thick with 0.3 mm clearance and notched at the bosses. Window-clamp washers and screws are not modelled.

Rubber-foot positions (12 mm in from the corners) are my choice, not the concept's. The split_base and N-wall VGA-slot flags are off.

In open_iso the S and E walls above Z 8 are drawn as a 12% ghost so the inside reads. Through the closed iso window you mainly see the S half of the board; that is the real line of sight at this camera angle, not a render fault.

**Problems found in the concept's numbers:**

- Back-support post does not fit. The concept uses a nylon M3x10 pan screw in a 6 mm F-F standoff (Z 6-12), with the head top set at Z 18. A pan head is about 2.1 tall, so the shank tip ends at about Z 5.9: it fills the whole standoff thread down to the keel. That leaves no thread for the countersunk screw that holds the standoff to the keel from below. Fix: a shorter nylon screw (about M3x6) or a longer standoff.
- Keel-to-floor fastener at X 74.5 is only 6.0 mm (centre to centre) from the W leg at X 68.5. In the model an M3 nut (5.5 AF) and the 5.5 AF leg hex come out at distance 0.0 (corners touch). A standard M3 washer (OD 7) would overlap the leg by about 0.7 mm, and a nut driver cannot get onto it. Also, §5.3 says the bridge and keel are 'identical' bars drilled as a clamped pair, but the keel-only floor-screw holes (12 and 112 mm from its W end) are missing from that drilling list.
- Window-clamp washers cannot reach the acrylic. The acrylic is 110x146 in a 111x147 rabbet (0.5 mm gap per side). With an Ø4 insert hole and the concept's own ≥1.6 mm wall, the hole centre must sit ≥3.6 mm outside the rabbet edge. An OD 7 washer (r 3.5) then stops 0.1 mm outside the rabbet edge, 0.6 mm short of the acrylic, so there is no overlap at all. It needs bigger washers or tabs, or the hole has to break into the rabbet.
- Lid thickness does not add up. The lid is 76.2 - 70 = 6.2 thick, but the stated 3.0 skin plus 3.3 rabbet is 6.3. Either the skin over the rabbet is really 2.9, or the closed box is 76.3 tall.
- Module plate fixing is inconsistent. The plate lies on the floor (Z 3-6, 'top at Z 6') but is 'held by 4 M3 screws into floor inserts'. The floor is only 3 mm, while an insert needs a 4.0x6.7 hole in an Ø9 boss. A boss tall enough would lift the plate by ≥3.7 mm or poke through it. If bosses are added, every module Z in §8/§9 moves (Pico USB Z 18.4, LA USB Z 13, 'everything below Z 20 under the jet').
- Logic-analyser USB-C has no room inside. The LA fills the bay at X 4-59 with its USB-C end on the panel's inner face (X 4). §9 says the cable's USB-C plug 'passes inward' through a 14x8 grommet hole, but there is 0 mm of space between the panel and the LA for a plug overmould (about 20 mm). The bay is 57 wide and the LA 55, so the LA cannot move E by a plug length.
- The lid's locating lip (4 mm, down to Z 66, running inside the walls) sits directly over the fan and the fuse holder. The real margins are about 6.4 mm for the fan (top Z 59.6) and about 10 mm for the fuse holder, not the 10.4 and 14 in the §10 height table, which measures to Z 70. The lip also needs notches at the four Ø9 corner bosses that run up to Z 70. The concept does not mention them.
- E exhaust-slot numbers do not match. 13 slots, 3 wide at 6 mm pitch, span 75 mm (Y 63.5-138.5 if centred on Y 101), not the 80 mm of 'Y 61-141'. The 1404 mm² total is correct.
- The clamp frame sits in the fan jet, which §7 does not account for. The W leg (6.35 across corners, X 68.5) stands on the fan axis (Y 101), and the bridge (Z 51-54) crosses the upper part of the jet (Z 19.6-59.6) across the whole box. The E leg and the bridge's E end sit 4.3 mm and 1.5 mm in front of the centre exhaust slots. None of these collide, but they affect the airflow.
- BME280 (X 20-45.4, Y 94-119.4) overlaps the MAX31855 (X 37-57.3, Y 75-98) and the Si5351 (X 38-59.6, Y 100-130.5) in plan. It only works as a stack: the BME280 sits at Z 26 on 20 mm standoffs above modules that top out at about Z 19. Its footprint covers 7.4x19 mm of the Si5351 and 8.4x4 mm of the MAX31855.
- HS10 N-lug joint is not dimensioned. The '9 mm from P3' figure is measured to the bare N lug tip (the model gives 8.96 mm in plan). The S joint is dimensioned as running about 8 mm past its tip. If the N joint is made the same way, it ends about 1 mm (in plan) from P3's body, about 1.5 mm above the assumed Dupont tops (Z 36.1). That vertical figure assumes my lug height of Z ~39.4, since HS10_LUG_Z is still MEASURE.

