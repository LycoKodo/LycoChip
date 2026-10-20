# projects/demo — handoff notes for Claude (and Alex)

Read the repo-root `CLAUDE.md` first; it still applies. This file adds what is specific to
`projects/demo/`, and the state as of 2026-10-20, written for picking the work up on Alex's
Windows machine.

## What this directory is

A complete MNIST demo **authored by Claude**: draw a digit on the computer, send it over
RS-232 to the EP4CE6, run the 784 → 16 → 10 integer network in RTL, and get the digit and
all 10 scores back, plus the digit on the 7-segment display.

- **The Article I override covers this directory only.** Alex asked for it on 2026-10-20
  after the conflict was stated to him. The record is in `README.md` and in
  `docs/PROGRESS.md` ("Article I override …"). Here, Claude writes RTL, testbenches and host
  code.
- **`projects/mnist/` stays Alex's.** Nothing here writes to it. Do not copy demo RTL there,
  and do not count anything here as his work in `docs/LEARNING.md`.
- The contract for every module (ports, cycle timing, pins, protocol) is `ARCHITECTURE.md`.
  To change behaviour, change it there first.

## State at handoff (all from commands run on the Mac, 2026-10-20)

| Check | Result |
|---|---|
| `./lint.sh demo` | 14 RTL files: iverilog ok, verilator clean |
| `./sim.sh demo` | 14/14 testbenches PASS. `tb_demo`: 16 of 16 images matched `mem/expected.hex` bit for bit (digit + all 10 scores), after a garbage half-frame that had to be discarded |
| `host/check_board.py --fake` | 16/16, PASS. This tests the host code against the golden model, **not the board** |
| `host/draw.py --smoke` | OK (fails unless a synthetic 7 is recognised as 7) |
| `host/test_make_mem.py` | PASS |
| Quartus 20.1.1, build `builds/20261020-154210-demo-b3a6f1b1` | Full compilation successful, 0 errors, 15 warnings, 0 critical warnings |
| Fitter | 882 / 6,272 LEs (14 %) · 549 registers · 57,216 / 276,480 memory bits (21 %) · 7 / 30 9-bit multiplier elements · 20 / 92 pins |
| Timing | worst setup slack +5.516 ns (Slow 1200mV 85C), worst hold +0.108 ns (Fast 0C); Fmax 69.04 MHz vs 50 MHz needed |
| Pins | all 20 ports `User Assignment = Y` in `demo.pin`, on the pins in `ARCHITECTURE.md` |

**Not yet verified: anything on hardware.** No bitstream from this directory has been
loaded on the board, and no USB-to-RS-232 adapter has been connected. The board test is
`check_board.py` against the real port (below), and nothing else stands in for it.

Each module's testbench was proven able to fail: the module was deliberately broken in a
scratch copy and the testbench reported FAIL. `tb_demo` FAILs if the rounding in `post` is
dropped, if the mux inputs are swapped, or if `w_addr` is reset between layers.

## Moving to Windows

### 1. Get the files across

None of this is committed yet. On the Mac, commit and push, or copy the folder. What is
needed:

- **All of `projects/demo/`**, including `mem/` (the generated ROM contents and test
  vectors). Leave out `host/__pycache__/`.
- `projects/mnist/model/export/` only if you will re-run `host/make_mem.py`. `mem/` is
  already generated from the current 4-bit export.
- Root `sim.sh` and `lint.sh` only if you will run them under a bash shell (see 4).

Line endings: if git rewrites `.hex` / `.qsf` / `.v` to CRLF on Windows, tools should still
read them, but that is **unverified**. Safest is `git config core.autocrlf false` before
cloning.

### 2. Build with Quartus (native on Windows)

`build.sh`, `upload.sh` and `tools/*.py` are **Mac-only**: they drive Docker/colima, the Lima
VM, ssh to lyco-server, and openFPGALoader. Do not use them on Windows. Use Quartus Prime Lite
**20.1** (the version this was built with) directly:

- GUI: open `projects\demo\demo.qpf`, then Processing → Start Compilation.
- or a shell in `projects\demo`: `quartus_sh --flow compile demo`

Quartus must run with `projects\demo` as its project directory, because `$readmemh("mem/…")`
paths are relative to it. After the build, check it as the Mac did:

- `demo.fit.summary` matches the table above;
- the RAM summary in `demo.fit.rpt` lists `weight_rom` as M9K ROM, 12704 × 4, with a MIF
  (a ROM initialised to zeros would still "work" and give wrong answers);
- every port in `demo.pin` is `Y`;
- no critical warnings.

### 3. Program the board

On Windows, use the **Quartus Programmer** with the USB-Blaster (driver in
`<quartus>\drivers\usb-blaster`). Use JTAG mode, add `output_files\demo.sof`, then Start. The
`.svf`-only trap in the root `CLAUDE.md` is about openFPGALoader on the Mac. The Quartus
Programmer has not been tried on this board, so verify the load by behaviour:

- **Load check:** a dash on all four 7-segment digits, LED1–3 dark, LED4 blinking about
  1.5 Hz. The `blink` design in the flash also blinks LED4, but it leaves the display dark,
  so the dashes are the evidence that the new design loaded.
- Writing the config flash (W25Q16, not an Altera EPCS part) from Windows is **untested**.
  Use SRAM (`.sof`) loads.

### 4. Run the Mac side, on Windows

The host code is plain Python 3.12 with numpy, pyserial, pillow and tkinter (tkinter comes
with the python.org installer):

```
py -m pip install numpy pyserial pillow
py projects\demo\host\fpga_link.py              # lists serial ports: find the adapter's COMn
py projects\demo\host\check_board.py COM3       # THE hardware test: PASS / FAIL, exit 0 / 1
py projects\demo\host\draw.py                   # the drawing app; pick COMn, or "Simulate (no board)"
```

- **`--fake` does not work on Windows.** `fake_fpga.py` uses `os.openpty` and `tty`, which
  are Unix-only. It is imported only when `--fake` is passed, so nothing else is affected.
  "Simulate (no board)" in `draw.py` does work: it calls `golden.py` directly.
- Comments and help text say `/dev/cu.*`; on Windows the port is `COMn`.

Simulation on Windows is **untested**. `sim.sh` and `lint.sh` are bash and use `perl` and
`~/.lycochip-build`. Under Git Bash with Windows builds of iverilog and verilator they may
work. The plain equivalent of one testbench, run in `projects\demo`:
`iverilog -g2012 -o tb_demo.vvp -s tb_demo -y rtl -I rtl tb\tb_demo.v` then `vvp tb_demo.vvp`
(look for the final `PASS` line).

### 5. Cabling

- The board's UART goes PIN_114/115 → MAX3232 → DB9 at RS-232 levels. Use a
  **USB-to-RS-232** adapter. A 3.3 V TTL adapter will not work.
- The board's DB9 is wired DCE (from schematic V2.1, as read by the review agents; not
  re-checked by hand). Use a **straight-through** cable or plug the adapter in directly,
  **not null-modem**. A null-modem cable gives a silent timeout, and `fpga_link`'s timeout
  message suggests checking exactly this.
- 115,200 baud, 8N1. `CLKS_PER_BIT = 434` gives 115,207 baud (+0.007 %).

## Bring-up order, and what each step proves

1. Load check (above): the new design is running.
2. `check_board.py COMn` → PASS: the UART path, the framing, and every multiply in both
   layers are right. All 10 scores must match `golden.py` exactly, so a correct digit by luck
   still fails.
3. `draw.py`: the demo. Its status line repeats the bit-exact comparison on every drawing.

If step 2 times out, check in this order: board powered and loaded (the dashes), TTL vs
RS-232 adapter, null-modem cable, wrong COM port. LED1 (`led_n[0]`) lights while a frame is
being received, and LED2 while it is computing or sending.

## Things learned building it (keep)

- **Quartus 20.1 ignores an initialiser on an `output reg` in the port list.** Icarus
  honours it, so simulation cannot catch this. It made `uart_tx` idle low (a line break) and
  was found by a gate-level simulation of the post-fit netlist. Every output reg here now
  gets its power-up value from an `initial` statement after the port list.
- **An inferred memory whose depth is not 2^address-bits** (26-word bias ROM on a 5-bit
  address, 10 scores on a 4-bit index) raises Critical Warning 127005. Declaring the full
  power-of-two depth removes it.
- **`build.sh` incremental-rebuild bug, fixed:** `rsync --delete` with `--include=*.mif`
  deleted the `.mif` files Quartus generates in its own `db/`, so the second build of
  unchanged sources failed (Error 286034 / 12154). `db/` and `incremental_db/` are now
  excluded. Proven by building twice in a row on the Mac: both succeeded.
- Icarus never evaluates `always @(*)` until an input changes, so `seg7` showed X after reset
  in sim. It is now a function and an `assign`; the gates are the same.
- A UART testbench at 16 clocks per bit (a power of two) cannot catch a counter that wraps
  instead of comparing. The tests now also run at 434, 13, 3 and 2.

## Changes outside projects/demo made in the same session (for context)

- Root `sim.sh` (new: strict PASS/FAIL runner); `lint.sh` (`-y`/`-I` so submodules and
  includes resolve); `build.sh`, `tools/buildui.py`, `tools/artifacts.py` (sync and hash
  `.vh .hex .mif`, exclude `tb/`, `db/`, `incremental_db/`); `docs/TOOLCHAIN.md` and the root
  `CLAUDE.md` build-loop line.
- `projects/mnist/`: `mnist.qpf/.qsf/.sdc` shell (no RTL; Alex's to fill), and
  `model/train.ipynb` now exports 4-bit weights with 8-bit activations (`WEIGHT_BITS = 4`,
  `ACT_BITS = 8`; integer accuracy 0.9275 on the 10,000 test images).

## Open items

- Everything on hardware (above).
- 7 "minor" review notes were not checked or acted on. They are in the workflow journal on
  the Mac (`~/.claude/projects/-Users-arona-Desktop-LycoChip/…/wf_d270746d-478/journal.jsonl`),
  not in the repo. One worth knowing: the bounds in `ARCHITECTURE.md` assume |w| ≤ 7, but a
  4-bit weight can be −8. `make_mem.py` now checks the real worst case per neuron before it
  writes anything, so a future export cannot silently overflow.
- Icarus prints `timescale … inherited` warnings because the RTL files have no
  `` `timescale `` and the testbenches do. They are harmless.
