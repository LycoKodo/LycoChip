# Archive

Finished work that is no longer the focus. Kept in git, out of the build picker.

## exercises/ — Phase 0 warm-ups

The Verilog Alex wrote while learning HDL, before work moved to the main design in
`projects/mnist/`. Each one is a complete Quartus project, unchanged since the move.
The story of each, including what went wrong, is in `docs/PROGRESS.md`; the concepts
they raised are cards in `docs/LEARNING.md`.

| Exercise | What it is | First logged |
|---|---|---|
| `blink/` | 4-bit counter on the LEDs at 2 Hz. The first bitstream on the board, and the design that exposed openFPGALoader's silent `.rbf` no-op | 2026-09-04 |
| `full_adder/` | 1-bit full adder, keys in, LEDs out, no clock. Two logic elements | 2026-09-05 |
| `button_counter/` | 4-bit counter clocked by a push button, reset by another | 2026-09-08 |
| `clock_counter/` | 4-bit counter driven from the 50 MHz oscillator. The fitter infers four latches here (`Warning (13310)`) | 2026-09-08 |
| `keytest/` | Purely combinational AND of two keys. The "cannot animate" load test from Article IV | 2026-09-22 |

Note: the header comment in `button_counter`, `clock_counter` and `full_adder` is
still `blink`'s, copied and never updated. It does not describe those files.

### Building one again

The build scripts only look in `projects/`. To rebuild an exercise, move it back:

```sh
git mv archive/exercises/keytest projects/keytest
./build.sh keytest
```

Old builds of these designs stay in `builds/` (local, last 25 kept), so
`./upload.sh` can still program one without a rebuild, until newer builds
push it out.

## docs/

- `QUIZ-INBOX.md`: the Cowork → Claude Code quiz queue. Retired 2026-09-23 (see the
  amendment in `docs/HANDSHAKE.md`); every entry was folded into `docs/LEARNING.md`.
