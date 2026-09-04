# LycoChip

FPGA work targeting an **OMDAZZ Altera Cyclone IV board V3.0** (`EP4CE6E22C8N`).

## The two machines

Compiling and programming happen on different computers, because Quartus has no
macOS build and your JTAG cable is plugged into the Mac.

| | Where | Does what |
|---|---|---|
| **Mac** (this repo) | `~/Desktop/LycoChip` | Edit Verilog, run the scripts, program the board over USB-Blaster |
| **lyco-server** | `~/lycochip-build` | Runs Quartus. Reached over Tailscale as `ssh lyco` |

**You type every command on the Mac, from this directory.** The scripts SSH to the
server for you; you never need to log in manually. Only the bitstream (~100 KB)
travels back.

## Daily loop

```sh
vim rtl/blink.v      # 1. edit
./build.sh blink     # 2. compile on the server (~25 s)
./program.sh         # 3. load onto the board (~2 s)
```

The board must be **powered on** before step 3.

## build.sh — compile

```sh
./build.sh [project]     # default: blink
```

1. `rsync` your `rtl/`, `*.qsf`, `*.qpf`, `*.sdc` up to `lyco:~/lycochip-build`
2. `quartus_sh --flow compile <project>` — synthesis, fit, assemble, timing
3. `quartus_cpf` converts the `.sof` into a `.svf` (the load format that works)
4. `rsync` the `.sof`, `.rbf` and `.svf` back into local `output_files/`

Doing it by hand:

```sh
rsync -az rtl blink.qsf blink.qpf blink.sdc lyco:lycochip-build/
ssh lyco
  cd ~/lycochip-build
  export PATH=$HOME/intelFPGA_lite/20.1/quartus/bin:$PATH
  quartus_sh --flow compile blink
  quartus_cpf -c -q 12.0MHz -g 3.3 -n p blink.sof blink.svf
  exit
rsync -az lyco:lycochip-build/blink.{sof,rbf,svf} output_files/
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
  Or override:  FORCE=1 ./program.sh sram
```

## program.sh — write the chip

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
./program.sh sram            # volatile, ~2s
./program.sh flash           # permanent, ~3min
./program.sh detect          # just check the JTAG chain
./program.sh sram keytest    # a project other than blink
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

Three files, then build. Copy `blink.*` as a starting point:

- `rtl/<name>.v` — the Verilog
- `<name>.qsf` — device, top-level entity, source files, **pin assignments**
- `<name>.qpf` — two lines naming the revision

```sh
./build.sh mydesign && ./program.sh sram mydesign
```

## Board facts worth remembering

- 50 MHz oscillator on **PIN_23**; RESET button on **PIN_25**
- LEDs on PIN_84-87, keys on PIN_88-91 — **all active LOW** (drive `0` to light)
- The LED silkscreen numbering is **reversed** vs the vendor pin table:
  PIN_84 is physically LED1, PIN_87 is LED4
- Reports live on the server: `blink.fit.summary` (resource use),
  `blink.sta.summary` (timing), `blink.pin` (final pin-out)

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
