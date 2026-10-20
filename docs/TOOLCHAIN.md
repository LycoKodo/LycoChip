# LycoChip toolchain

How code in this repo becomes a configured **OMDAZZ Altera Cyclone IV board V3.0**
(`EP4CE6E22C8N`). The project itself is described in the top-level `README.md`.

The examples below use `blink`, which now lives in `archive/exercises/blink/`. Any
project under `projects/` works the same way.

## Where things run

You type every command on the Mac, from this directory. Quartus has no macOS
build, so `build.sh` runs it in one of three backends (it asks; or set `BACKEND=`):

| Backend | Where | clock_counter |
|---|---|---|
| `local` (default) | Rosetta `centos:7` container on colima, on this Mac. Works offline | ~22 s warm, ~45 s cold |
| `remote` | lyco-server over `ssh lyco` (Tailscale, LAN fallback) | ~33 s |
| `vm` | emulated x86-64 Lima VM (`tools/quartus-vm/`). Fallback only | ~115 s |

The board is always programmed from the Mac over USB-Blaster (`./upload.sh`).

## Layout

Each design is self-contained under `projects/<name>/`:

```
projects/
└── <name>/
    ├── <name>.qpf       project file
    ├── <name>.qsf       device + pin assignments
    ├── <name>.sdc       timing constraints
    ├── rtl/<module>.v   one module per file, file named after the module
    └── tb/<tb>.v        testbenches: simulation only, never sent to Quartus
```

`.hex` and `.mif` files anywhere in the project are memory initialisation
(ROM contents) and count as sources: they are synced to Quartus and included
in the source hash. `tb/` is excluded from both, so editing a testbench never
makes a build look stale.

The directory name and the `.qsf` basename must match, or the build picker skips
the project. Quartus compiles with the project directory as its CWD, so every
path inside a `.qsf` stays relative to that project, and only files under
`projects/<name>/` are copied to the build backend. Nothing floats at the repo root.

Only `projects/` is built. Archived exercises in `archive/exercises/` are complete
projects of the same shape; `git mv` one back into `projects/` to build it again.

## Daily loop

```sh
vim projects/<name>/rtl/<file>.v # 1. edit
./lint.sh <name>                 #    syntax + implicit nets, ~40 ms
./sim.sh <name> [tb]             #    testbenches, PASS/FAIL
./build.sh                       # 2. pick a project, compile (~25 s)
./upload.sh                     # 3. pick a build, load it (~2 s)
```

## sim.sh — simulate

`./sim.sh mnist` runs every `tb/*.v` in Icarus Verilog; `./sim.sh mnist tb_mac`
runs one. `WAVE=1` opens the last waveform in surfer. Conventions: `tb/<tb>.v`
defines module `<tb>`; modules under test are found in `rtl/` by file name, so
a testbench never lists its sources; the testbench prints a line that is
exactly `PASS` or `FAIL` and calls `$finish`.

It reports FAIL if the testbench does not compile, uses an implicit net, prints
FAIL anywhere, never prints PASS, never reaches `$finish`, or runs past
`SIM_TIMEOUT` (60 s). The simulation runs in the project directory, as Quartus
does, so a `$readmemh` path means the same file in both. Waveforms (`.fst`) and
logs go to `~/.lycochip-build/sim/<project>/`, outside the repo.

The board must be **powered on** before step 3.

## build.sh — compile

With no argument in a terminal you get a selection page:

```
  ▚ PROJECTS ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
  ▸ blink       4 files   built 1 minute ago    ✓
    keytest     3 files   built 9 minutes ago   ✓

  ↑↓ select   ⏎ build   q quit
```

Naming a project skips it: `./build.sh keytest`.

Then it (the `remote` backend is shown; `local` and `vm` do the same against a
copy of the project outside the repo):

1. `rsync`es source files only (`.v .vh .sv .vhd .qsf .qpf .sdc .tcl .hex .mif`, not `tb/`) into
   `lyco:~/lycochip-build/projects/`
2. runs `quartus_sh --flow compile` in that project's directory
3. converts the `.sof` into a `.svf` with `quartus_cpf` (the load format that works)
4. pulls `.sof`, `.rbf`, `.svf` into `output_files/` and archives the build

The rsync deliberately filters by extension: `--delete` does not remove
*excluded* files, so Quartus outputs (`db/`, `*.rpt`, `*.pin`) survive on the
server. That keeps incremental compilation working and preserves `blink.pin`.

Doing it by hand:

```sh
rsync -az projects/ lyco:lycochip-build/projects/
ssh lyco
  cd ~/lycochip-build/projects/blink
  export PATH=$HOME/intelFPGA_lite/20.1/quartus/bin:$PATH
  quartus_sh --flow compile blink
  quartus_cpf -c -q 12.0MHz -g 3.3 -n p blink.sof blink.svf
  exit
rsync -az lyco:lycochip-build/projects/blink/blink.{sof,rbf,svf} output_files/
```

## The build archive

Every compile is snapshotted into `builds/<stamp>-<project>-<srchash>/` with a
`manifest.json` recording the exact sources, git commit, resource usage and
timing that produced it. The last 25 are kept.

This exists to kill one specific failure: a build fails, the *previous*
bitstream is still sitting in `output_files/`, and you flash it without
noticing — then debug new code while the board runs old logic.

Every program action therefore resolves a build from `builds/`, verifies the
artifact checksums, and **refuses to run if your sources have changed since**:

```
REFUSING TO PROGRAM: sources on disk differ from this build
  The board would run logic that does not match your source tree.
  Rebuild:            ./build.sh blink
  Or override:  FORCE=1 ./upload.sh sram
```

## upload.sh — write the chip

With no arguments in a terminal you get an interactive picker:

```
  ▚ BUILDS ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
  ▸ blink     2 minutes ago    ✓   50 LE  +13.74ns  3b9700f+
    keytest   25 minutes ago   ✓    8 LE       --   3b9700f
    blink     1 hour ago       ✗  failed

  ↑↓ build   ←→ target   ⏎ program   q quit
```

`↑↓` picks a build, `←→` switches between SRAM and FLASH, `⏎` programs it.
A `+` after the commit means the tree was dirty at build time.

Arguments skip the UI and use the newest good build:

```sh
./upload.sh sram            # volatile, ~2s
./upload.sh flash           # permanent, ~3min
./upload.sh detect          # just check the JTAG chain
./upload.sh sram keytest    # a project other than blink
```

Doing it by hand:

```sh
# check the cable and chip are alive
openFPGALoader -c usb-blaster --detect

# SRAM -- seconds, gone at power-off. Use this while developing.
openFPGALoader -c usb-blaster --file-type svf output_files/blink.svf

# flash -- minutes, survives power-off. Use this when a design is finished.
openFPGALoader -c usb-blaster -f --fpga-part ep4ce622 --verify output_files/blink.rbf

# inspect the flash chip
openFPGALoader -c usb-blaster --detect -f --fpga-part ep4ce622

# dump the whole flash (~3 min)
openFPGALoader -c usb-blaster --fpga-part ep4ce622 \
  --dump-flash --file-size 2097152 -o 0 backup/dump.bin
```

## SRAM vs flash

An FPGA has no fixed circuitry. The bitstream is a wiring diagram that must be
loaded into it on **every** power-up, and it lives in volatile SRAM.

- **SRAM** — the computer pushes the design in over JTAG. Instant. Gone when the
  board loses power. This is what you want while iterating.
- **Flash** — writes the design into the W25Q16 chip on the board, which the FPGA
  reads by itself at power-up. Makes the board standalone. The flash is not on
  the JTAG chain, so a temporary bridge design is loaded into the FPGA first,
  and the data is written *through* the FPGA.

## Adding a new design

Three files under `projects/<name>/`, then build. The archived exercises
(`archive/exercises/blink/` and the rest) show the shape:

- `rtl/<name>.v` — the Verilog
- `<name>.qsf` — device, top-level entity, source files, **pin assignments**
- `<name>.qpf` — two lines naming the revision

```sh
./build.sh mydesign && ./upload.sh sram mydesign
```

## Board facts worth remembering

- 50 MHz oscillator on **PIN_23**; RESET button on **PIN_25**
- LEDs on PIN_84-87, keys on PIN_88-91 — **all active LOW** (drive `0` to light)
- The LED silkscreen numbering is **reversed** vs the vendor pin table:
  PIN_84 is physically LED1, PIN_87 is LED4
- Every build's full log is archived at `builds/<stamp>-<name>-<hash>/build.log`.
  The full reports — `*.fit.summary` (resource use), `*.sta.summary` (timing),
  `*.pin` (final pin-out) — stay in the build directory: `~/.lycochip-build/projects/<name>/`
  for `local`, `~/lycochip-build/projects/<name>/` on lyco-server for `remote`.

## Gotchas

- **Never trust "Load SRAM 100% Done".** openFPGALoader's native Altera `.rbf`
  SRAM path reports success but does not configure this chip. Always load the
  `.svf`. That is why `build.sh` generates one.
- **`TDO is stuck at 0`** while `--scan-usb` still lists the blaster means the
  *board* is unpowered, not a cable fault.
- The `.qsf` parser rejects trailing `; # comment` on assignment lines.
- Quartus writes `.sof`/`.rbf` to the project root, not `output_files/`.

## backup/

`factory_flash_2MB.bin` is the board's original demo image, dumped before we
overwrote it. **It is not downloadable anywhere.** Do not delete it.
