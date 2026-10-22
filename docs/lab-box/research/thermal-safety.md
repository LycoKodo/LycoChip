# Lab Box research: thermal and safety analysis for the heater clamp

**TL;DR**
1. **The thermocouple on the package top does not read Tj.** With the heater off, the top is at most about 1 K *below* the die (83.6 mW × θJC 10.5 K/W). With the heater clamped on top the error flips sign: heat flows top → die → PCB, so the top reads **about 3–7 K above Tj in still air and 6–12 K above Tj with the fan on** at the 60 °C point (*derived*). Quartus' own corners imply about 0.09 %/K of Fmax, so that error is the same size as the effect the shmoo is trying to measure. The EP4CE6 has **no on-die temperature diode**.
2. **Holding power at 60 °C is about 1–2.5 W fan-off and 3–5.5 W fan-on** (*derived*). So 12 V across 10 Ω (14.4 W) is 3–13× too much. Prefer **18–22 Ω** in an HS10-size body: 6.5–8 W, which caps power *in hardware*. If the 10 Ω part is kept, cap duty at **≤ 55 %** in firmware. An HS25 does not fit on the 20 mm package body.
3. **Mount the thermostat on the heater spreader, not near the package.** The spreader is the hottest part of the stack, so a cut-out there bounds everything downstream. Use a **75 °C** KSD9700, or 80 °C. **Not 70 °C**: its trip window starts at 65 °C, and the spreader runs 2–7 K above the package, so a 70 °C part nuisance-trips at a 60 °C setpoint. *(Verifier: a 20.5 × 7.5 mm KSD9700 does **not physically fit** on an 18 × 18 mm spreader that already carries a 15.9 × 16.5 mm HS10. The spreader needs a tab that rises clear of the package leads, or the thermostat goes on the HS10 housing. See Verification, item V5.)* Firmware should trip at **70 °C on the thermocouple**. The fuse should be **1 A (or 1.25 A for margin)** for an 18 Ω heater, and **2 A** if the 10 Ω part is kept. *(Corrected: the original said 1.5 A and 2–2.5 A. Littelfuse's 60 % derating applies to the fuseholder's rating, not to the fuse. See V2.)*
4. **Electrical rules:** the spreader must be at most 18 × 18 mm (at least 1 mm inside the 20 mm body, 2 mm from the lead tips) with Kapton or an insulating pad underneath. The thermocouple junction must be **isolated** (MAX31855: "T-: Do not connect to GND"). On the metal-case KSD9700 drawing, **one lead is marked as joined to the iron case**. The note reads "此线与铁壳体虚接", and "虚接" is ambiguous, so whether the case is live is **UNVERIFIED** until a continuity test. Insulate it from the spreader either way. The header pins next to the FPGA are live I/O. *(Verifier: the HS10's own solder terminals sit at +12 V and overhang the lead tips by about 4 mm per side. See V6.)*
5. **Mechanics and materials:** use a spring clamp at about 5–10 N that reacts against the board's own standoffs, with a support post under the PCB directly below the FPGA (10 N unsupported bends the board about 0.4–0.8 mm, about 450 µε). Contact parts are metal, the bracket arms ASA (PETG HDT is 68 °C, too close), and the fan blows *in* on the cool side and exhausts past the heater. Run it at a **fixed baseline** during sweeps.

Confidence tags: **datasheet** (manufacturer document or manufacturer tool data) | **vendor-doc** (board vendor file in `resources/`) | **listing** (shop or third-party, unverified) | **photo-estimate** | **derived** (calculated, working shown) | **unknown**.
"Quartus pow" means `quartus_pow` from Quartus Prime Lite **25.1std.0 Build 1129**. It was run on a *scratch copy* of the `projects/demo` build (`~/.lycochip-build/projects/demo`, fitted 2026-10-21), so the repo and the build directory were not touched. The command to re-run it is in section 10.

---

## Facts table

| Item | Value | Unit | Source | Confidence | Notes |
|---|---|---|---|---|---|
| Package body (D1 × E1) | 20.00 × 20.00 | mm | `Cyclone IV chip/EP4CE6 package information.pdf` p.1 (04R-00402-1.0) | datasheet | BSC |
| Lead tip to lead tip (D × E) | 22.00 × 22.00 | mm | same, p.1 | datasheet | leads stick out 1 mm per side |
| Package height above seating plane (A) | 1.45 / 1.55 / 1.65 | mm | same, p.1 | datasheet | min / nom / max |
| Body standoff (A1) | 0.05 – 0.15 | mm | same, p.1 | datasheet | air gap under body |
| Exposed pad (D2 = E2), bottom | 5.25 / 5.40 / 5.55 | mm | same, p.1 | datasheet | copper leadframe |
| Lead pitch (e) / lead width (b) | 0.50 / 0.17–0.27 | mm | same, p.1 | datasheet | |
| Package mass | 1.3 | g | same, p.1 | datasheet | |
| Exposed pad purpose | GND; "for electrical connectivity and not for thermal purposes" | — | `Cyclone IV Handbook.pdf` (CYIV-5V1-1.8) PDF p.19, Table 1–3 note 1; `EP4CE6 pin information.pdf` p.6 note 4 | datasheet | Altera publishes no thermal use for it |
| Tj, recommended, commercial | 0 – 85 | °C | `Cyclone IV Datasheet.pdf` (CYIV-53001-1.7) Table 1–3, PDF p.4 | datasheet | C8 part |
| Tj, absolute max / Tstg | −40 – 125 / −65 – 150 | °C | same, Table 1–1, PDF p.2 | datasheet | damage limit, not operating limit |
| θJC (junction to case top) | 10.50 | K/W | Quartus pow, *Operating Conditions Used* | datasheet | device model inside the manufacturer's tool. Intel's θ table page now returns 404. *Verifier: reproduced, along with θCA 16.60 / 12.30 / 11.10 / 8.80. This is manufacturer **tool output**, not a published table* |
| θCA, no heatsink, still air (typical board) | 16.60 | K/W | Quartus pow, preset "No Heat Sink With Still Air" | datasheet | "Board model used: Typical" |
| θCA at 100 / 200 / 400 LFM | 12.30 / 11.10 / 8.80 | K/W | Quartus pow, presets "No Heat Sink With N Lfpm Airflow" | datasheet | |
| θJA still / 100 / 200 / 400 LFM | 27.1 / 22.8 / 21.6 / 19.3 | K/W | θJC + θCA | derived | Quartus' board, not the OMDAZZ board |
| θJB, ψJT | not found | K/W | — | unknown | not in Quartus output or the local docs |
| FPGA power, MNIST demo build | 83.62 (core dyn 10.89, static 43.01, I/O 29.72) | mW | Quartus pow, default settings | derived | Quartus says "confidence Low" (vectorless, 12.5 % toggle). *Verifier re-ran it 2026-10-23 and reproduced it exactly. The still-air preset gives 83.70 mW (static 43.10), a negligible difference* |
| Core static power at Tj 30 / 60 / 70 / 85 °C | 43.33 / 46.51 / 47.91 / 50.43 | mW | Quartus pow with POWER_TJ_VALUE fixed | derived | leakage rises about 3 mW from 30 to 60 °C |
| Worst-case bracket | 145.39 | mW | Quartus pow, MAXIMUM silicon, Tj 85, 50 % toggle | derived | upper bound for this design |
| Tj − Ttop, self-heating only | ≤ 0.88 (≤ 1.52 worst) | K | P × θJC | derived | upper bound (θJC assumes all heat leaves through the top) |
| Ttop − Tj, heater on top, hold 60 °C | 2.6 – 6.6 (still), 6.2 – 11.6 (fan) | K | network model, section 1 | derived | sign flips vs heater-off |
| Fmax, slow corner 85 °C / 0 °C | 72.37 / 78.43 | MHz | `demo.sta.rpt` (Slow 1200mV 85C / 0C Fmax Summary) | datasheet | Quartus timing model |
| Fmax temperature sensitivity | ≈ 0.091 | %/K | (78.43−72.37)/78.43/85 K | derived | model corners, not measured silicon |
| On-die temperature sensing diode / ADC | none | — | Handbook 488 pp.: 0 hits for "temperature sens", "TEMPDIODE", "sensing diode"; pin list and pin-connection guide: 0 "TEMP" pins | datasheet | evidence of absence across both E and GX chapters |
| Board supply | USB or 5 V adapter, selected by red push switch | — | `Dev Board Manual.pdf` p.1 | vendor-doc | board input 0.34 / 0.63 / 1.46 W (low/typ/high) per `board-power.md` table, whose verification raises the high case to about 320 mA, about 1.6 W (derived, not measured) |
| MAX31855 T- pin | "Do not connect to GND" | — | MAX31855 datasheet 19-5793 Rev 2, p.7 | datasheet | read via Adafruit mirror |
| MAX31855 fault bits | D16 = any fault; D2 SCV; D1 SCG; D0 OC | — | same, p.9–10 | datasheet | T- ground ref is opened during fault test |
| MAX31855K gain/offset error | ±2 (TC −200…+700 °C, TA −20…+85 °C) | °C | same, p.3 | datasheet | excludes cold-junction error and nonlinearity |
| MAX31855 cold-junction error | ±2 (TA −20…+85 °C) | °C | same, p.4 | datasheet | keep the module away from heat (p.9) |
| MAX31855 resolution / conversion time | 0.25 / 70 typ, 100 max | °C / ms | same, p.1, p.4 | datasheet | |
| MAX31855 input filter | 10 nF across T+/T− "strongly recommended" | — | same, p.11 | datasheet | check whether the breakout has it |
| KSD9700 rating | AC 250 V 5 A resistive; NC; auto-reset; 10,000 cycles; ≤ 50 mΩ | — | XC Electronics KSD9700 spec (LCSC-hosted PDF) p.1–3 | datasheet | **no DC rating published** |
| KSD9700 trip / reset tolerance | trip ±5; reset 80 ±10 for the 100 °C part | °C | same, p.1–2 | datasheet | differential about 20 K. 70/75 °C part not seen in a datasheet |
| KSD9700 body | 20.5 × 7.5 × 3.7 (28 × 8.9 × 5.1 with sleeve); leads 80 ±3 | mm | same, p.2 drawing | datasheet | sensing face = unprinted face |
| KSD9700 metal case | one lead is marked as joined to the iron shell; electrical meaning **UNVERIFIED** | — | same, p.2 drawing note, which actually reads **"此线与铁壳体虚接"** (*corrected*: the original quoted "…连接") | datasheet (note exists) / unknown (meaning) | "虚接" can mean a nominal or loose joint, not a designed current path. **Treat the case as possibly live and insulate it.** Confirm with a continuity test (section 9, item 4) |
| KSD9700 mounting surface limit | ≤ 120 % of rated temperature | — | same, p.2 | datasheet | |
| Arcol HS10 rating | 10 W on 415 cm² × 1 mm Al; 5 W no heatsink; 200 °C max hot spot | — | Arcol HS datasheet 12/14.08 p.1–2 | datasheet | read via chipdip mirror ("Downloaded from Arrow.com") |
| HS10 size (A × E × C) | 16.5 × 15.9 × 8.8 (30.0 incl. terminals) | mm | same, p.2 | datasheet | the housing fits inside the 20 mm body. *Verifier:* A includes the two diagonal mounting tabs. **B = 30.0 mm overall**, so the terminals stick out about 7 mm from each end and overhang the 22 mm lead span by about 4 mm per side (derived: (30 − 22)/2) |
| HS10 finned-body width D / terminal axis height H / mounting holes | 8.5 max / 4.5 max / Ø2.0 ± 0.25 at F 11.3 × G 12.4 | mm | same, p.2 table and drawing | datasheet | *added in verification.* H is measured above the base, so with a 2 mm spreader the +12 V terminals sit about 8 mm above the PCB. That is near header-pin-tip height |
| HS10 typical surface rise, heatsink-mounted | 5.8 | K/W | same, p.2 | datasheet | *added in verification.* That figure is on the 415 cm² standard heatsink, not on an 18 mm spreader |
| HS25 size (A × E) | 28.0 × 27.3 | mm | same, p.2 | datasheet | **wider than the package** |
| HS10 isolation | 1000 V rms proof; ≥ 10,000 MΩ | — | same, p.1–2 | datasheet | housing isolated from element |
| Holding power, top at 60 °C | 1.1 – 2.5 (closed, still) / 2.7 – 5.5 (fan full + vents) | W | section 3 | derived | **measure** |
| PCB "fin" resistance, footprint to air | 8.8 – 20 (still) / 5.4 – 12 (fan) | K/W | radial-fin model, section 3 | derived | layer count and size unknown |
| Local heat capacity / time constant | ≈ 20 / 2 – 7 | J/K / min | section 3 | derived | **measure** with a step test |
| Box air rise, sealed, 3–5 W inside | +6 to +25 | K | P/(U·A), U 2.5–4 W/m²K, A 0.08–0.12 m² | derived | why the fan should always run |
| Through-flow air heat capacity, 4.83 CFM | 2.66 | W/K | ṁ·c | derived | 5 W → +1.9 K |
| Noctua NF-A4x10 5V | 8.2 m³/h (4.83 CFM), 1.78 mmH₂O, 0.22 W | — | noctua.at spec page (read through search summary) | **UNVERIFIED** (*downgraded from datasheet*: the primary page returned HTTP 429 to both agents and was never opened) | example 40 mm 5 V fan. 0.22 W is Noctua's *typical* input power, not its maximum. 4.83 CFM is free-air flow; a vented box gives less |
| PETG HDT (0.45 and 1.80 MPa) | 68 | °C | Prusament PETG TDS v1.1, 2022-02-16, ISO 75 | datasheet | |
| ASA HDT | ≈ 93 | °C | reseller pages for Prusament ASA | listing | |
| Kapton 25 µm / 0.5 mm pad (k 1.5) over 18 × 18 mm | 0.64 / 1.03 | K/W | t/(kA) | derived | k of Kapton 0.12 W/mK assumed |
| PCB bend, 10 N centre load, corner-supported | 0.4 – 0.8 mm, ≈ 420 – 480 | mm, µε | beam model, section 6 | derived | a real plate is worse; use back-support. *Verifier:* the arithmetic checks (0.44 / 0.84 mm, 419 / 476 µε). Every input is **assumed, not measured**: t = 1.6 mm, E = 20 GPa, beam width 70–80 mm, span 100–130 mm |
| Fuse derating | run the **fuse** at ≤ 75 % of its rating at 25 °C. Run the **fuseholder** at ≤ 60 % of the *holder's* rating | — | Littelfuse Fuseology Design Guide, PDF p.4 (75 %) and p.5 (fuseholders "derated by 40 %") | datasheet (*verified from the PDF*) | *Corrected:* the 60 % applies to the holder's current rating, **not** to the fuse inside it. Fuse sizing stays at ≤ 75 % |
| IRF520N gate | VGS(th) 2.0–4.0 V; RDS(on) 0.20 Ω at VGS = 10 V | — | IR IRF520N datasheet (UCSB mirror) p.2; Vishay IRF520 datasheet p.2 | datasheet (*upgraded from listing: PDFs opened*) | **not** a 3.3 V logic-level part. The non-N Vishay IRF520 has the same 2.0–4.0 V threshold and 0.27 Ω at 10 V |

---

## 1. What the package-top thermocouple actually measures

**Data.** Quartus' device model for EP4CE6E22C8 gives θJC = 10.5 K/W. The case-to-ambient figures are 16.6 K/W in still air, and 12.3 / 11.1 / 8.8 K/W at 100 / 200 / 400 LFM, with a "typical" board. θJB and ψJT are not published anywhere I could reach. Intel's Cyclone IV thermal-resistance page now redirects to a 404. The exposed pad is officially "not for thermal purposes", so Altera gives no thermal figure for the path through the PCB.

**Heater off (self-heating only).** Heat flows die → top and die → board. The top is cooler than Tj by at most P × θJC = 0.0836 × 10.5 = **0.9 K**, or 1.5 K at the 145 mW worst-case bracket (*derived*). θJC is measured with *all* power leaving through the top, so this is an upper bound.

**Heater on top (the briefed design).** The heat-flow direction reverses. Heat enters the top and passes through the mould compound to the die and leadframe, then into the PCB, which is the main heat sink. **The top becomes the hottest point of the package, and the die sits between the top and the PCB.** A lumped network was solved for this case (script: scratchpad `thermal/model.py`). Its nodes and resistances:
- top → die: θJC = 10.5 K/W
- top → leads → PCB, bypassing the die: 5–15 K/W (assumed)
- die → paddle/solder → PCB: 2–8 K/W (assumed, because θJB is unknown)
- PCB footprint → air: from the fin model in section 3
- heater surfaces → air: 25–90 K/W (assumed)
- FPGA dissipation: 0.1 W

| Condition (package top held at 60 °C) | Heater power | Tj | PCB under package | **Ttop − Tj** |
|---|---|---|---|---|
| Closed box, still air (box air 32 °C) | 1.1 – 2.5 W | 53 – 57 °C | 48 – 57 °C | **2.6 – 6.6 K** |
| Fan full + vents (box air 26 °C) | 2.7 – 5.5 W | 48 – 54 °C | 39 – 52 °C | **6.2 – 11.6 K** |

*All derived; the inputs are assumptions with wide ranges.* The direction of the error is robust. Its size scales with **heater power flowing through the package**, so it is near zero at the 30 °C point and largest at 60 °C with the fan on.

**Why it matters for the demo.** Quartus' own timing corners give 78.43 MHz at 0 °C and 72.37 MHz at 85 °C for this design, about **0.09 %/K**. A 6–12 K error in "temperature" is therefore about 0.5–1 % of Fmax. Because the error grows with setpoint, plotting Fmax against T_top **stretches the temperature axis**. Across 30 → 60 °C the die may move only about 18–27 K. The apparent dFmax/dT would then be understated by roughly 10–40 % (*derived*).

**What to do (Alex picks):**
- Label the reading **T_top (package top)**, never "Tj", in logs and plots.
- **Bracket Tj** with a second sensor on the PCB underside directly below the exposed pad. With top heating, T_pcb ≲ Tj ≲ T_top. This needs a second thermocouple and converter, or a thermistor. That costs money, so ask first.
- **Calibrate the gradient**: hold T_top fixed and switch the fan baseline, which changes the heater power. Any shift in the on-chip ring-oscillator frequency is the gradient showing itself. Fitting Tj ≈ T_top − k·P_heater gives k. The ring-oscillator RTL is Alex's to write; this is only the measurement method.
- **Fixed fan baseline during sweeps.** That makes P_heater, and so the error, repeatable at each setpoint.
- **Alternative geometry (option B, not briefed):** heat from **under the PCB below the exposed pad**, which is the copper path to the die, and cap the package top with an insulating cover. Little heat then crosses the mould compound. T_top falls within about 0.3 K of Tj with a foam cap, 1.1 K bare in still air, and 3.8 K bare with the fan on (*derived*: (Tj−Tair)/(θJC + R_top-air) × θJC, with R_top-air 1000 / 250 / 83 K/W). Costs: it needs a bare underside (unknown: decoupling caps or a base plate may be there), and the heater then also heats the PCB directly.

## 2. On-die temperature sensing

None. The local Cyclone IV handbook (Vol 1 CYIV-5V1-1.8 plus the datasheet chapter) covers both E and GX. It has **no** "temperature sensing diode", "TEMPDIODE" or temperature ADC in 488 pages, and the EP4CE6 pin list and pin-connection guidelines contain no TEMP pins. So the external thermocouple is the only absolute reference. A ring oscillator measures *Tj-dependent delay*, which is exactly what is wanted, but it has to be calibrated against something. Calibrating it against T_top while the top heater is running carries the section 1 error into the calibration. **Calibrate at zero heater power (fully soaked box), or extrapolate to zero heater power.**

## 3. Heater power budget

**Working (derived; every input is an assumption, so treat the result as an order-of-magnitude figure to be measured).**
1. *PCB as a fin.* The board is modelled as an annular fin from the package footprint (r₁ = 12.4 mm, the equivalent of 22 × 22 mm) out to r₂ = 40–60 mm, with an adiabatic edge.
   - In-plane sheet conductance k·t: 0.011 W/K (2-layer, 1 oz, 40 % copper), 0.019 W/K (2-layer, 70 %), 0.040 W/K (4-layer with planes).
   - h per side, including radiation: 10/7 W/m²K top/bottom in still air, 30/12 W/m²K with the fan.
   - The fin length 1/m is only 16–48 mm, so the board's far corners hardly help.
   - Result: **R_pcb = 8.8–20 K/W still, 5.4–12 K/W fan.**
2. *Package internals:* section 1.
3. *Heater body to air:* HS10 surface ≈ 8 cm². With h = 10–15 W/m²K still that is ~~60–90~~ **83–125 K/W**; with h = 30–50 W/m²K under the fan, ~~25–35~~ **25–42 K/W**. *(Corrected arithmetic: 1/(h·A) = 1/(10 × 8×10⁻⁴) = 125 and 1/(15 × 8×10⁻⁴) = 83 K/W. The model used 60/90 and 25/35. Heater surface loss is only about 0.2–0.5 W of the total, so the holding-power result moves by ≲ 0.1–0.2 W.)*
4. *Box air.* Sealed: ΔT = P/(U·A) = +6 to +25 K for 3–5 W inside. With the fan through-venting: P/(ṁc) = +1 to +2 K.
5. Solving the network for T_top = 60 °C gives **P_heater ≈ 1.1–2.5 W (closed box, still) and 2.7–5.5 W (fan full, vents)**.

**Is 10 Ω / 14.4 W too much? Yes.**
- **3–13× the holding power.** The PID would live at 10–40 % duty, and quantisation and overshoot get worse.
- **Larger heater-to-package gradient while ramping.** About 14 W × 1.2 K/W ≈ 17 K, so the heater body reaches about 77 °C while the package passes 60 °C.
- **Stuck-on steady state far above anything safe.** ~~14.4 W × 6–25 K/W lands well above 150 °C~~ *(corrected: that did not match the arithmetic or the author's own model)*. The model uses a stack-to-air R of 5–15 K/W. That gives 14.4 W × 5–8 K/W ≈ **100–140 °C with the fan** and 14.4 W × 8–15 K/W ≈ **150–250 °C in still air** (derived, `model.py` output). So it is bounded only by the thermostat. Even 18 Ω (8 W) stuck-on reaches about 95–150 °C (8 × 8–15 + 32, derived) without the thermostat.
- **Faster runaway.** About 0.5–0.6 K/s at the package (with C ≈ 20 J/K), more at the heater body, so the thermostat overshoots further.
- **Over HS10's rating.** HS10 is 10 W *on a 415 cm² heatsink* and 5 W in free air. HS25 (25 W) is 28 × 27.3 mm and does not fit the 20 mm body. *(Verifier: an 18 Ω / 8 W heater is **also** above the 5 W no-heatsink rating at full duty. An 18 mm spreader on a QFP is much closer to "no heatsink" than to 415 cm². The recommendation below is acceptable only because the average holding power is ≤ 5.5 W and full duty is bounded by firmware and the thermostat. A 27–33 Ω part (4.4–5.3 W at 12 V) stays inside 5 W but cannot hold 60 °C at fan-full on the upper estimate. Alex chooses.)*

**Recommendation.**
- **Hardware power cap:** pick R so that V²/R is about 1.5× the worst-case holding power. At a 12.0–12.6 V adapter, **18 Ω → 8.0–8.8 W** (preferred) or **22 Ω → 6.5–7.2 W**, in an HS10-size housing. This cap holds even if the firmware is wrong. Supply current 0.55–0.70 A.
- **Firmware duty cap:** D_max = P_cap·R/V². For a kept 10 Ω part, **D_max = 0.55** (7.9 W at 12 V). It does nothing for a stuck-on MOSFET, which is why the R choice above is the real limit.
- **Settling.** Local C ≈ 20 J/K: HS10 4 g, Al spreader 18×18×2 mm, package 1.3 g, and a PCB disc of r 37 mm. With R 6–20 K/W, τ ≈ 2–7 min. The passive 3τ is 6–20 min. A PID can overdrive heating steps, but **cooling steps are limited by passive τ**, and the fan roughly halves it. Define "stable" as T_top within ±0.25 °C (one LSB) of the setpoint *and* |slope| < 0.02 K/s for 60 s; the PCB tail creeps. *Derived; tune from a measured step response.*

## 4. Hardware backstop: thermostat, fuse, interlocks

**Where the KSD9700 goes.** During heating the temperatures are ordered **heater element > spreader > package top > die > PCB**.
- **On the spreader:** the cut-out sees the hottest accessible metal, so it bounds the clamp, the pads, the PETG/ASA and, downstream, the package. The price is an early trip: it opens when the *spreader* reaches its rating, so the package can only get to (rating − P·R_spreader→top). That margin is ≈ 2–7 K at holding power.
- **On or near the package (in practice the PCB, since the top is covered):** it lags the heater by P·R. With a stuck-on 14 W that is about 15–30 K, so the heater and clamp run far above the trip temperature while the package is still "safe". Rejected.
- *(Verifier, geometry: **the "on the spreader" option does not fit as drawn.** The KSD9700 body is 20.5 × 7.5 × 3.7 mm (datasheet), longer than the whole 18 mm spreader. The spreader's top face is almost fully covered by the HS10 base (15.9 mm long, 16.5 mm across its tabs), leaving about 1 mm per side. The options need a CAD decision by Alex:*
  - *(a) Give the spreader a tab that rises at least 1–2 mm above the package-top plane before it extends past the 20 mm body, so it clears the leads, and clamp the KSD9700 there, sensing face down on Kapton.*
  - *(b) Clamp the KSD9700 to the HS10 housing (finned body D = 8.5 mm wide), which is hotter still. That trips earlier, so the 75/80 °C choice must be re-checked.*
  - *Either way the thermal path differs from the "spreader" figures above. **Measure the trip point in place** (section 9, item 4).)*

**Rating.** KSD9700 trip tolerance is ±5 °C (datasheet).

| Thermostat nominal | Trip window (spreader) | Package top when it trips at holding power | Verdict |
|---|---|---|---|
| 70 °C | 65 – 75 °C | as low as about 58 – 63 °C | **nuisance-trips at the 60 °C setpoint**. Use only if setpoints stay ≤ 55 °C |
| **75 °C** | 70 – 80 °C | ≥ about 63 °C | **recommended**: clears 60 °C with margin; bounds the spreader at ≤ 80 °C plus overshoot |
| 80 °C | 75 – 85 °C | ≥ about 68 °C | acceptable. Listed at LCSC as XC KSD9700-80/5JSB/080A |

Stuck-on check for an 18 Ω / 8 W heater with a 75 °C part:
- Ramp ≈ 0.15–0.3 K/s, times an unknown bimetal lag of about 10–30 s, gives roughly 2–9 K of overshoot.
- The spreader peaks at about 89 °C or less. The package is lower and Tj lower still, around the 85 °C *operating* limit and far below the **125 °C absolute maximum**. Nothing is damaged. *(Verifier: the KSD9700 datasheet, p.2, limits the mounting surface to ≤ 120 % of the rated temperature. For a 75 °C part that is 90 °C, so an 89 °C peak is right at the limit. The 80 °C part gives 96 °C of headroom against a peak of about 94 °C. Derived; the ±5 °C tolerance is taken from the 100 °C part's drawing.)*
- The thermostat auto-resets about 20 K below its trip point, so a stuck MOSFET produces slow cycling, not a fire. Optional: add a **one-shot thermal cutoff (TCO, about 95–100 °C)** on the spreader in series, so that a stuck-on fault ends permanently instead of cycling. *Derived; the lag is not in the datasheet. Measure it (section 9).*

**Ordering of limits (recommended):**

| Layer | Limit |
|---|---|
| setpoint clamp (firmware) | demo 30–60 °C; reject > 65 °C |
| duty cap (firmware) | 18 Ω: none needed. 10 Ω: ≤ 55 % |
| over-temp trip (firmware) | T_top ≥ 70 °C → heater off, **latched** until the host clears it |
| power cap (hardware) | V²/R ≈ 8 W (18 Ω) |
| temperature cut-out (hardware) | KSD9700 75 °C on the spreader |
| current cut-out (hardware) | fuse at the 12 V inlet |

**Other firmware interlocks (Marlin-style "thermal runaway" logic):**
- Heater off on any of these: MAX31855 D16 set, an SPI read of all 0s or all 1s, a reading that does not change for 5 s, or a reading outside 0–100 °C.
- Duty ≥ 50 % for 60 s with < 2 K rise → off (sensor has fallen off).
- Duty = 0 while T rises > 1 K/min → raise a "**heater stuck on – unplug 12 V**" alarm to the host.
- RP2040 hardware watchdog on.
- Gate pull-down on the MOSFET input, so a Pico reset or unplugged USB leaves the heater off.
- Host heartbeat timeout → setpoint to idle.

**Fuse (12 V inlet, before the thermostat):**
- **18 Ω** heater (0.70 A at 12.6 V) plus a 5 V fan supplied elsewhere: **1 A, or 1.25 A for margin, fast-acting**, bare or in a holder (0.70/0.75 = 0.93 A minimum fuse rating). The holder itself must be rated ≥ 0.70/0.6 = 1.17 A, and any common 5 × 20 mm or blade holder is. *(Corrected: the original said "1.5 A in an inline holder". Littelfuse's 60 % rule, Fuseology p.5, derates the **fuseholder's** rating, not the fuse's.)*
- **10 Ω** heater (1.26 A): **2 A** (1.26/0.75 = 1.68 A minimum), bare or in a holder. ~~2.5 A in a holder~~ is not supported, for the same reason. 2 A equals the adapter's rating, so the fuse guards the wiring only, which is one more reason to raise R. Add 0.1 A or so if a 12 V fan shares the adapter.
- The KSD9700 has **no DC rating**. 12 V / ≤ 1.3 A is far below its AC rating, but its DC switching life is unverified.

## 5. Electrical hazards at the clamp

**Spreader geometry.**
- The leads occupy the 1 mm ring between the 20 mm body and the 22 mm tips, and sit below the top surface.
- Make the spreader **≤ 18 × 18 mm, centred**, so it stays at least 1 mm inside the body edge and 2 mm from the lead tips even if it is off by 1 mm. Break all edges.
- The HS10 base (16.5 × 15.9 mm) fits on it.
- Insulate the spreader's underside **and its edges**: 25–50 µm Kapton (adds 0.64–1.29 K/W) with non-conductive paste, or a 0.5 mm insulating silicone pad (0.5–1.0 K/W). Never use a metal-filled paste.

**Header pins.** In `board.jpg`, 2.54 mm header strips run within a few mm of the FPGA on at least two sides (*photo-estimate*, unscaled). They are live FPGA I/O. Any metal clamp arm, screw head or spring has to clear them in all positions. **Measure** this clearance.

**Thermocouple and the MAX31855.**
- The datasheet says **"T-: Do not connect to GND"** (p.7). T- is tied to an internal ground reference during conversion, and the fault test checks for shorts to VCC or GND (D2 SCV, D1 SCG, D16 summary).
- A **bare bead** touching a grounded spreader, or a **grounded-junction** probe (the M6-lug / screw probes often sold with MAX6675/31855 boards), puts the junction on ground. Expect SCG faults or corrupted readings.
- One forum report (ez.analog.com thread 598020, *listing*) says T+ tied to GND left all fault bits at 0. **Do not rely on the fault bits to catch it.**
- Use an **insulated / ungrounded junction** probe (≤ 1 mm sheath), or a bare bead wrapped in Kapton where it meets metal.
- Route the bead in a ~1.2 mm groove in the spreader's underside to the package-top centre, with the groove lined in Kapton. The reading still blends spreader and package temperatures: spreader − top ≈ P × 0.5–1 K/W ≈ 1–5 K.
- Fit 10 nF across T+/T− (datasheet p.11). Mount the MAX31855 module on the cool plate, since cold-junction error comes from local heating (p.9).
- If readings are noisy with PWM on, try grounding the spreader *only after* confirming the junction is isolated.

**KSD9700 live case.** On the metal-shell part, one lead is connected to the shell (datasheet drawing). *(Verifier: the drawing note actually reads "此线与铁壳体虚接". "虚接" is ambiguous (a nominal or loose joint), so a live case is **UNVERIFIED**. Do the continuity test in section 9, item 4. The precautions below stand either way.)* In a high-side position the case sits at +12 V. Either:
- put Kapton between the case and the spreader, clamping it with its **unprinted (sensing) face** down, or
- use a plastic-case variant.

**Heater element.** The HS10 housing is isolated from the element (1000 V rms proof). With a low-side MOSFET, both heater terminals sit at +12 V when the MOSFET is off.

*(Verifier, added: **the HS10 terminals overhang the FPGA.** Overall length B is 30.0 mm (datasheet), so the solder tags reach about 15 mm from the package centre, about 4 mm past the 22 mm lead tips. Their axis is ≤ 4.5 mm above the HS10 base, about 8 mm above the PCB with a 2 mm spreader. In `board.jpg` the header strips P1, P2 and a third strip sit around the FPGA, roughly 5–12 mm from the body edge, with pin tips at a similar height (photo-estimate, perspective, unscaled). A +12 V tag or a soldered wire touching a header pin would put 12 V on FPGA I/O. **Requirements:**)*
- *Point the terminal axis along the side with the most measured clearance.*
- *Sleeve both tags and the wire joints in heat-shrink.*
- *Route the heater leads up and away from the board.*
- *Add the HS10 tag positions to the clearance measurement in section 9, item 1.*

**MOSFET module.**
- Common IRF520 modules are not logic-level (VGS(th) up to 4 V, RDS(on) specified at 10 V). At 3.3 V gate drive they can run partly on and get hot. A hot MOSFET can fail short, which is exactly the stuck-on case.
- Use a module whose MOSFET specifies RDS(on) at VGS ≤ 2.5–4.5 V. Read the part number on the module.

## 6. Mechanical load on the QFP

- **No limit found.** Altera AN 358 (Thermal Management for FPGAs, v4.0, 2012) exists, but I did not retrieve its text; no QFP top-load limit was found anywhere.
- **Load path.** Force on the top goes through the mould compound into the soldered exposed pad and the leads, then into the PCB. The risk is **PCB bending** (cracked joints and MLCCs), not crushing the package.
- **Board bending (derived, 1.6 mm FR4, E ≈ 20 GPa, centre point load, supported 100–130 mm apart):**
  - 5 N: 0.2–0.4 mm deflection, about 210–240 µε
  - 10 N: 0.4–0.8 mm, about 420–480 µε
  - 20 N: 0.9–1.7 mm, about 840–950 µε

  A plate held at its corners deflects *more* than this beam model.
- **Contact pressure.** 10 N on 18 × 18 mm is about 31 kPa (4.5 psi). That is too low for many gap pads to reach their datasheet impedance, so a **thin pad or paste + Kapton** is better than a thick pad.

**Approach:**
- A compression spring sets the force, preloaded by a screw: **5–10 N**.
- The bracket reacts against the **board's own corner standoffs**, never the enclosure lid, so lid tolerances cannot change the force.
- Put a **back-support post under the PCB directly below the FPGA**. It must touch only solder mask, never parts or vias, and have an insulating tip. Then the clamp force goes straight through and the board does not bow.
- A ball or swivel contact on the spreader top lets the spreader seat flat on the package.
- Set the force by compressing the spring on a kitchen scale to its installed length.
- *(Verifier, added: in the vendor photo `board.jpg` the board sits between a **clear acrylic top plate and a bottom plate on brass standoffs** (photo-estimate). If Alex's board has them, the top plate covers the FPGA and must be removed or cut out for the clamp. The bottom plate may be the natural reaction surface for the back-support post. Whether Alex's unit has the plates, and their thickness and standoff heights, is **unknown**: measure.)*

## 7. Fan and airflow

- **Direction.** Inlet fan on the **cool side** (module plate, Pico, MAX31855, INA226). The BME280 sits in the inlet stream, out of the heater's line of sight. Air then crosses the FPGA zone and exhausts through a vent just past the heater.
  - Modules then see room air.
  - The ambient reading is the true inlet temperature.
  - Heated air leaves immediately.
  - The fan itself never sits in hot air. The sibling report `modules-thermal-mech.md` cites a 40 mm Sunon rated only to 70 °C.
- **Effect.** A 40 mm 5 V fan moves about 4.8–8 CFM in free air (Noctua NF-A4x10 5V: 4.83 CFM, 0.22 W). Fed through the box, that is a heat capacity of about 2.7 W/K, so box air stays within about 1–2 K of the room instead of rising 6–25 K sealed. *(Verifier: that is a **lower bound** on the rise. 4.83 CFM is free-air flow, and the Noctua's maximum static pressure is only 1.78 mmH₂O, about 17 Pa (search summary, UNVERIFIED). Vents, the board and modules in the path cut the real flow, and the rise scales as 1/flow. Measure it as inlet vs exhaust air temperature with the BME280 and the thermocouple.)*
  - It roughly **doubles the heater power needed at 60 °C** (to 2.7–5.5 W), which also doubles the section 1 gradient.
  - It roughly **halves τ** for cool-down.
  - The fan cannot pull the package below inlet-air temperature.
- **Repeatability.** Pick a **fixed baseline fan duty** (for example 30–50 %) for every sweep, and let the heater alone regulate. Use full fan only for step-downs. With fan speed constant, each setpoint has one heater power, and therefore one top-vs-Tj offset to calibrate.

## 8. Materials near a 70 °C heater

- **Metal:**
  - spreader: Al 6061 or Cu, about 18 × 18 × 2 mm
  - heater housing
  - the clamp's contact point on the heater: a stainless or brass screw tip, or a metal pressure plate
  - spring: stainless
  - standoffs: brass
- **ASA** for the clamp bracket arms and anything within about 15 mm of the heater (HDT ≈ 93 °C, *listing*).
- **PETG** (HDT 68 °C, *datasheet*) only in the cool zone and for walls. It must not carry spring load near the heater: under load at 60 °C it creeps.
- **PLA:** nowhere in the box.
- **Thermal break.** The bracket arm touches the heater only through a standoff, so it does not become a heatsink. An M3 nylon or PEEK spacer, or a small-contact metal screw tip, puts at least 5 mm of air between the printed arm and the heater.
- **Wire.** Thermocouple and heater leads near the heater should be glass-braid, PFA or silicone insulated (the KSD9700's sleeve is rated −40 to 230 °C).

## 9. Must measure (Alex)

1. **Clearances.** FPGA body edge to the nearest header pin or component on all 4 sides; header pin height above the PCB; package top height (expect 1.45–1.65 mm). Calipers from the body edge.
2. **PCB.** Thickness, and layer count if visible at an edge or by backlighting. Does the underside below the FPGA have parts, a via array or a base plate? This decides the back-support and option B.
3. **Thermocouple isolation.** Multimeter from each TC lead to the probe sheath or lug: it must read **open**.
4. **KSD9700.** Continuity from each lead to its case. Then its *actual* trip and reset: clamp it to the spreader beside the TC, ramp ≤ 0.2 K/s, and log when the circuit opens and closes.
5. **Heater R and adapter voltage**, both no-load and loaded. Then P_max = V²/R.
6. **Holding power** at 30/40/50/60 °C with the fan off, at baseline and at full: P = D·V²/R from the logged duty. This replaces the derived 1.1–5.5 W.
7. **Gradients.** A second sensor on the spreader top, and one under the PCB below the FPGA, during holds.
8. **Step response** (open loop, fixed duty) → τ and gain for PID tuning; record the cool-down τ with the fan off and at full.
9. **Clamp force** (spring on a scale to its installed length), and board bow before and after clamping (straight-edge or feeler).
10. **MOSFET module part number** → RDS(on) at the Pico's 3.3 V gate drive.
11. **Board input power** (INA226) at 25 °C vs 60 °C. Quartus predicts the core static part rising from 43.3 to 46.5 mW (typical silicon).

## 10. Sources and reproduction

- Local: `resources/Altera-Cyclone-IV-board-V3.0 documentation/`
  - `Cyclone IV chip/EP4CE6 package information.pdf` p.1
  - `Cyclone IV chip/Cyclone IV Datasheet.pdf` PDF p.2, p.4
  - `Cyclone IV chip/Cyclone IV Handbook.pdf` PDF p.19, whole-text search
  - `Cyclone IV chip/EP4CE6 pin information.pdf` p.6
  - `Cyclone IV chip/Cyclone IV pin connection design guide.pdf`
  - `Dev Board Manual.pdf` p.1
  - `board.jpg`
- Quartus Power Analyzer: copy `~/.lycochip-build/projects/demo` to a scratch folder, then run
  `C:\altera_lite\25.1std\quartus\bin64\quartus_pow.exe demo --write_settings_files=off "--set=POWER_PRESET_COOLING_SOLUTION=NO HEAT SINK WITH STILL AIR"`
  (also `... WITH 100|200|400 LFPM AIRFLOW`; `--set=POWER_AUTO_COMPUTE_TJ=OFF --set=POWER_TJ_VALUE=60`; `--set=POWER_USE_DEVICE_CHARACTERISTICS=MAXIMUM --default_toggle_rate=50% --use_vectorless_estimation=off`). Read *Operating Conditions Used* in `demo.pow.rpt`.
- STA corners: `~/.lycochip-build/projects/demo/demo.sta.rpt`, the "Slow 1200mV 85C/0C Model Fmax Summary" sections.
- MAX31855 datasheet 19-5793 Rev 2 (2/12), via https://cdn-shop.adafruit.com/datasheets/MAX31855.pdf. The analog.com copy timed out.
- KSD9700 (XC Electronics, spec and test report, 2025-09-13): https://atta.szlcsc.com/upload/public/pdf/source/20250917/851B236838E2399B8D14C94DA645621B.pdf
- Arcol HS series datasheet 12/14.08: https://static.chipdip.ru/lib/410/DOC043410072.pdf (Arrow copy)
- Prusament PETG TDS v1.1: https://www.3dprintergear.com.au/assets/files/technical-data-sheet%20(1).pdf
- Prusament ASA HDT ≈ 93 °C (listing): https://siddament.com.au/products/prusament-asa-natural-800g
- Noctua NF-A4x10 5V: https://noctua.at/en/nf-a4x10-5v/specification (read through search summary; the fetch got HTTP 429)
- Littelfuse fuse derating: https://info.littelfuse.com/hubfs/Fuseology%20Design%20Guide.pdf (read through search summary; *verifier opened the PDF: p.4 = 75 % fuse rule, p.5 = 60 % **fuseholder** rule*)
- IRF520N: https://web.ece.ucsb.edu/~ilan/Classes/ECE2A_F2010/Labs/Datasheets/irf520n.pdf (mirror; read through search summary; *verifier opened the PDF, p.2*). Vishay IRF520: https://www.vishay.com/docs/91017/irf520.pdf (p.2)
- MAX31855 T+-to-GND not flagged (forum, listing): https://ez.analog.com/data_converters/precision_adcs/f/q-a/598020/max31855-doesn-t-detect-a-short-circuit-to-vcc
- θJC measured with the thermocouple at the top-surface centre: https://community.altera.com/kb/knowledge-base/how-is-the-junction-to-ambient-thermal-resistance-theta-ja-and-the-junction-to-c/343449 (search summary)
- Not reachable: Intel Cyclone IV thermal-resistance table (`intel.com/.../lit-pkg/thermal.html?family=Cyclone_IV` → 404), Altera AN 358 body text.
- Model script (scratch, not in the repo): `C:\Users\Alex\AppData\Local\Temp\claude\C--Users-Alex-Documents-GitHub-LycoChip\45139045-1ae9-4209-8e0f-da8135f40e46\scratchpad\thermal\model.py`

---

## Verification (adversarial pass)

Done 2026-10-23 by a second agent. Every check below was re-derived from the primary source opened this session. Downloads went to isolated scratch folders; the repo and `~/.lycochip-build` were not modified. Quartus was re-run on a fresh scratch copy (`scratchpad\vthermal\pow`).

### Checked and confirmed (no change)

| # | Claim | How it was checked | Result |
|---|---|---|---|
| C1 | Package D1/E1 20.00, D/E 22.00, A 1.45/1.55/1.65, A1 0.05–0.15, D2/E2 5.25/5.40/5.55, e 0.50, b 0.17–0.27, 1.3 g | `EP4CE6 package information.pdf` p.1 read directly | all match |
| C2 | Exposed pad is GND, "not for thermal purposes" | Handbook PDF p.19 (Table 1–3 note 1); pin information PDF p.6 note 4 | match |
| C3 | Tj 0–85 °C commercial; Tj −40…125 / Tstg −65…150 abs max | `Cyclone IV Datasheet.pdf` (CYIV-53001-1.7) PDF p.4 Table 1–3, PDF p.2 Table 1–1 | match |
| C4 | No on-die temperature diode or ADC | full-text search of the 488-page handbook, datasheet and pin-connection guide: no "temperature sens", "TSD", "sensing diode"; "diode" hits are only PCI-clamp and config-protection diodes | confirmed (absence in local docs) |
| C5 | θJC 10.50; θCA 16.60 / 12.30 / 11.10 / 8.80 K/W | `quartus_pow` 25.1std re-run with each preset | reproduced exactly |
| C6 | 83.62 mW default; static 43.33 / 46.51 / 47.91 / 50.43 mW at Tj 30/60/70/85; 145.39 mW worst case | same, with the stated `--set` options | reproduced exactly |
| C7 | Fmax 72.37 MHz (Slow 1200mV 85C) / 78.43 MHz (0C); 0.091 %/K | `demo.sta.rpt` lines 148–153, 719–724; (78.43−72.37)/78.43/85 = 0.000909 | match |
| C8 | MAX31855: T- "Do not connect to GND" (p.7); D16/D2/D1/D0 fault bits (p.10); T- ground switch S3 opened during fault test (p.9); ±2 °C gain/offset for K at TC −200…700, TA −20…85 (p.3); ±2 °C cold-junction (p.4); 0.25 °C; tCONV 70/100 ms (p.4); 10 nF across T+/T− "strongly recommended" (p.11) | MAX31855 19-5793 Rev 2 PDF opened (Adafruit mirror) | all match |
| C9 | KSD9700: AC250 V 5 A resistive, NC, 10,000 cycles (TUV/UL; CQC 6,000), ≤ 50 mΩ, trip 100 ± 5, reset 80 ± 10, mounting surface ≤ 120 % of rating, no DC rating, 20.5 × 7.5 × 3.7 body (28 × 8.9 × 5.1 sleeved), leads 80 ± 3, printed face is the non-sensing face ("印字面在非感温面") | XC Electronics PDF p.1–4 and p.2 drawing, opened and rendered | match (lead-to-case note: see V3) |
| C10 | Arcol HS10: 10 W on 415 cm² × 1 mm, 5 W no heatsink, 200 °C hot spot, 1000 V rms proof, ≥ 10,000 MΩ, 4 g; A 16.5, E 15.9, C 8.8, B 30.0; HS25 A 28.0 × E 27.3 | Arcol HS datasheet 12/14.08 (Arrow copy via chipdip) p.1–2, rendered | match |
| C11 | Prusament PETG HDT 68 °C at both 0.45 and 1.80 MPa (ISO 75), TDS v1.1 16-02-2022 | PDF opened | match |
| C12 | Arithmetic: 0.0836 × 10.5 = 0.88 K; 0.145 × 10.5 = 1.52 K; θJA sums; 12²/18 = 8.0, 12.6²/18 = 8.82, 12²/22 = 6.55, 12.6²/22 = 7.22 W; 0.55 × 14.4 = 7.9 W; Kapton 0.64 / 1.29 K/W, pad 1.03 K/W; 31 kPa; 2.66 W/K; C ≈ 20.1 J/K; τ 2.0–6.7 min; ramp 0.54–0.62 K/s; option-B 0.29 / 1.13 / 3.82 K | recomputed, and the author's `model.py` re-run from a copy | match |
| C13 | Holding power 1.1–2.5 W (still) / 2.7–5.5 W (fan); Ttop − Tj 2.6–6.6 / 6.2–11.6 K; R_pcb 8.8–20.1 / 5.4–12.2 K/W | `model.py` re-run | reproduced. The model is self-consistent, but **every input is assumed** (see U1) |

### Corrected

| # | Original claim | Problem | Fix applied |
|---|---|---|---|
| V1 | "14.4 W × 6–25 K/W lands well above 150 °C" (section 3) | arithmetic: 14.4 × 6 + 26 ≈ 112 °C, not above 150. It also disagrees with the author's own model (5–15 K/W → 98–248 °C) | replaced with ≈ 100–140 °C (fan) and 150–250 °C (still); added 18 Ω stuck-on ≈ 95–150 °C |
| V2 | Fuse "1.5 A in a holder" (18 Ω), "2.5 A in a holder" (10 Ω); derating row "≤ 60 % in a fuseholder" | Littelfuse Fuseology p.5: the 60 % applies to the **fuseholder's** rating, not the fuse's. The source had been read only through a search summary | 18 Ω → 1 A (1.25 A for margin); 10 Ω → 2 A; holder rated ≥ 1.17 A. Row upgraded to datasheet after opening the PDF |
| V3 | KSD9700 drawing note quoted as "此线与铁壳体连接"; "case is live" tagged datasheet | the rendered drawing reads **"此线与铁壳体虚接"**. "虚接" is ambiguous (a nominal or loose joint) | quote corrected; electrical meaning marked **UNVERIFIED**; insulate anyway; continuity test (section 9, item 4) decides |
| V4 | Heater surface to air "60–90 K/W still, 25–35 K/W fan" for 8 cm² at h 10–15 / 30–50 | arithmetic: 1/(hA) = 83–125 and 25–42 K/W | corrected; effect on holding power ≲ 0.2 W |
| V5 | "Put the KSD9700 on the spreader" (TL;DR 3, section 4) | **geometry**: a 20.5 × 7.5 mm thermostat cannot sit on an 18 × 18 mm spreader whose top is covered by a 15.9 × 16.5 mm HS10 (about 1 mm free per side) | flagged in TL;DR and section 4, with two CAD options (raised spreader tab, or on the HS10 housing); trip point to be measured in place |
| V6 | HS10 "fits inside the 20 mm body" | only the housing does. B = 30.0 mm puts the +12 V solder tags about 4 mm past the lead tips at about 8 mm above the PCB, near header-pin-tip height | added HS10 D/H/hole rows and a section 5 hazard note: orient, sleeve, measure |
| V7 | HS10 "over rating" is a reason to reject 10 Ω, while 18 Ω / 8 W is recommended | 8 W also exceeds the 5 W no-heatsink rating; an 18 mm spreader is far from the 415 cm² reference heatsink | caveat added in section 3: acceptable only because the average power is ≤ 5.5 W and full duty is bounded; 27–33 Ω is the in-rating alternative |
| V8 | Noctua NF-A4x10 5V tagged datasheet | primary page never opened (HTTP 429 for both agents); 0.22 W is *typical*, not max; 4.83 CFM is free-air | downgraded to UNVERIFIED; the box-air rise of +1–2 K is a lower bound |
| V9 | IRF520N tagged listing | PDF opened: VGS(th) 2.0–4.0 V, RDS(on) 0.20 Ω at 10 V (IR, p.2); Vishay IRF520 0.27 Ω | upgraded to datasheet; IRF520 figures added |
| V10 | Board input "0.35–1.45 W" | `board-power.md` table says 0.34 / 0.63 / 1.46 W, and its verification raises the high case to about 1.6 W | corrected the note (still derived, not measured) |

### Still unverified or assumed (Alex must measure, or treat as order-of-magnitude)

- **U1 – every thermal-network input**: θJB, the lead-path R (5–15 K/W), the pad R (2–8 K/W), the PCB layer count, copper fraction and size, h values, box air 26/32 °C. Also: if the OMDAZZ board's exposed pad is poorly soldered (R_pad ≫ 8 K/W), the die sits closer to T_top and the Ttop − Tj error *shrinks* (for example R_pad 30 K/W gives about 2–4 K instead of 6–12 K with the fan; derived: 10.5/(10.5+30) × (T_top − T_pcb), with T_top − T_pcb ≈ 8–14 K). Pad soldering is unknown, and an X-ray or reflow inspection is not practical, so the two-sensor bracket (section 1) is the way to find out.
- **U2 – KSD9700 70 / 75 / 80 °C tolerance**: ±5 °C is taken from the 100 °C part's drawing. No 70/75/80 °C datasheet was opened. The LCSC "KSD9700-80/5JSB/080A" part is a *listing* (not opened by the verifier). In the naming scheme on p.3 the trailing "080A" is an internal code, not a reset temperature.
- **U3 – KSD9700 thermal lag (10–30 s)**: not in any datasheet. The stuck-on overshoot (2–9 K) depends on it.
- **U4 – ASA HDT ≈ 93 °C**: retailer listings only. The Prusament TDS URLs tried returned 404.
- **U5 – Header clearance** to the FPGA (roughly 5–12 mm, three strips: P1, P2 and a third): photo-estimate from a perspective vendor photo. The original said "at least two sides"; the photo shows three. **Measure with calipers from the package body edge.**
- **U6 – The acrylic top/bottom plates** seen in `board.jpg`: unknown whether Alex's unit has them.
- **U7 – PCB bend figures**: the board's thickness, size and support points are unmeasured.
- **U8 – Altera AN 358 / QFP top-load limit**: still not found. The 5–10 N clamp force is a conservative judgement, not a rating.
- **U9 – θJC test method** (community KB link): read only through a search summary.

### Not checked

Littelfuse ambient rerating curves; the Marlin firmware logic; the Sunon fan figures (they live in the sibling report `modules-thermal-mech.md`). None of these changes a CAD dimension.
