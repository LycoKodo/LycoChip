# LycoChip

A handwritten-digit (MNIST) recogniser, built by hand on an **OMDAZZ Cyclone IV board
V3.0** (`EP4CE6E22C8N`), to learn how an AI accelerator works at the level of logic,
timing and tradeoffs.

```
Mac  ──image──▶  FPGA runs the network  ──digit──▶  answer comes back
```

**Status:** Phase 0, foundations. The main design lives in
[`projects/mnist/`](projects/mnist/README.md) and has no RTL yet. Its open
decisions are listed there. Where the work stands: [`docs/PROGRESS.md`](docs/PROGRESS.md).

## Layout

```
projects/mnist/      the main design. One Quartus project per projects/<name>/
archive/exercises/   Phase 0 warm-ups: blink, full_adder, counters, keytest
docs/
  PROGRESS.md        build and milestone log (append only)
  LEARNING.md        spaced-repetition quiz cards
  HANDSHAKE.md       how the Claude Code and Cowork sessions share this repo
  TOOLCHAIN.md       build backends, the build archive, programming, gotchas
tools/               build and programmer UIs, Quartus container and VM definitions
resources/           vendor docs: pin tables, schematics, datasheets
backup/              the board's factory flash image. Irreplaceable, do not delete
```

## Daily loop

```sh
./lint.sh       # syntax check with iverilog + verilator, ~40 ms
./build.sh      # pick a project, compile with Quartus (~25 s)
./upload.sh     # pick a build, program the board (~2 s). Board must be powered
```

Everything else about the toolchain is in [`docs/TOOLCHAIN.md`](docs/TOOLCHAIN.md):
where Quartus runs, the build archive and its staleness guard, SRAM vs flash, and
the traps already paid for.

## The part

| Resource | EP4CE6 has |
|---|---|
| Logic elements | 6,272 |
| Registers | 6,272 |
| M9K memory bits | 276,480 |
| 9-bit multiplier elements | 30 (= 15 × 18×18) |
| Usable I/O pins | 92 |

The project's working rules are in [`CLAUDE.md`](CLAUDE.md).
