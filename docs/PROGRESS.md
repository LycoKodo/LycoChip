# Lycochip progress log

Handoff channel to the learning-tracking Claude session. Governed by **Article II**
of `CLAUDE.md`. Append only — never edit a past entry.

---

## 2026-09-04 — Toolchain up, first bitstream on hardware

**Phase:** 0 — environment
**Built:** No RTL of Alex's yet. Quartus Prime Lite 20.1.1 installed on lyco-server;
`build.sh` / `program.sh` created; build archive with a source-hash staleness guard.
**Verified:** Hardware. `blink` (4-bit counter) programmed to SRAM, then written to the
W25Q16 config flash and confirmed booting standalone after a power cycle.
**Resources:** blink — 50 / 6,272 LEs · 28 registers · 0 memory bits · 0 multipliers ·
6 / 92 pins · worst-case setup slack +14.8 ns at the 85 °C corner.
**Learned:** Alex refused to accept the first hardware result. Told the LEDs were
blinking, he pointed out the factory demo also blinks, so the test proved nothing —
which is what forced the real diagnosis. That instinct found a genuine silent bug:
openFPGALoader reports `Load SRAM: 100.00% Done` and exits 0 while never configuring
this part. The fix was to program via a Quartus-generated `.svf`.
**Stuck on:** Nothing blocking. Article IV was written out of this episode.

---

## 2026-09-05 — full_adder, first RTL written by Alex

**Phase:** 1 — combinational fundamentals
**Built:** `projects/full_adder/rtl/full_adder.v` — a 1-bit full adder. 3 keys in
(a, b, c_in), 2 LEDs out (S, c_out), purely combinational, no clock.
**Verified:** Synthesis clean (0 errors). Hardware programming path proven on this
board, but the **truth table has not been walked** — all 8 input combinations are
reachable by hand and have not been confirmed one by one.
**Resources:** 2 / 6,272 LEs · 0 / 6,272 registers · 0 / 276,480 memory bits ·
0 / 30 9-bit multiplier elements · 5 / 92 pins. No clock, so no Fmax.
The whole adder collapses into **two** logic elements — one 4-input LUT each for `S`
and `c_out`, since both are functions of the same 3 inputs. Worth remembering when
estimating the accelerator: an LE is a small lookup table, not a gate.
**Learned:** Alex derived the carry logic himself and landed on the canonical
structure — two half-adders feeding an OR — with `c_out = (a^b)·c_in + a·b`. He also
got the active-low convention right in *both* directions, inverting the keys on the way
in and the LEDs on the way out, which is the half people usually miss.
**Stuck on:** Four concepts raised and carded in `docs/LEARNING.md`, none yet quizzed:
`wire` vs `reg`; why the design compiled with eight undeclared signals (implicit nets,
`` `default_nettype none ``); vector declaration syntax and packed vs unpacked
dimensions; and logical vs bitwise operators — the code uses `&&`/`!` where `&`/`~`
are meant, which is harmless at 1 bit and breaks silently the moment signals widen.
Also outstanding: dead `IO_STANDARD` lines in `full_adder.qsf` for `key[3]`, `led[2]`
and `led[3]`, which the port list does not declare, and a stale header comment still
describing the old blink counter.
