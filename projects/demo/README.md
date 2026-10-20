# demo — Claude's reference build of the MNIST accelerator

**Authored by Claude, not Alex.** On 2026-10-20 Alex asked for a complete, working
version of the accelerator: Mac app, UART, and RTL, as a demo of how the system could
work. Claude stated the conflict with CLAUDE.md Article I first: this is a finished
answer key for the modules Alex is about to write. Alex chose to override it (Article
VI allows this). The override covers **this directory only**.

Rules for this directory:

- Nothing here counts as Alex's work, and nothing here is evidence for a `LEARNING.md`
  promotion.
- `projects/mnist/` is Alex's design. Nothing in this directory writes to it. The model
  is read from `projects/mnist/model/export/` once, by `host/make_mem.py`, and
  snapshotted into `mem/`.

The architecture, port lists and protocol are in `ARCHITECTURE.md`.

## Running it

All commands from the repo root. `PY=/opt/anaconda3/envs/LC-MNIST/bin/python`.

1. **Snapshot the model** (only after re-exporting from the notebook; `mem/` is committed):
   `$PY projects/demo/host/make_mem.py`. It refuses, before writing anything, an export
   whose worst case over all inputs would overflow the RTL's 24-bit accumulator or
   16-bit score. `$PY projects/demo/host/test_make_mem.py` checks that refusal on
   doctored copies of the export, and that the real export reproduces `mem/` exactly.
2. **Build:** `./build.sh demo`
3. **Program:** `./upload.sh sram demo` (volatile) or `./upload.sh flash demo` (permanent).
   **Load check:** right after programming, all four 7-segment digits show a single
   dash (segment g only), LED1-LED3 are dark, and LED4 (`led_n[3]`, PIN_87) blinks about
   1.5 times a second. The heartbeat alone is *not* the check: the last design
   docs/PROGRESS.md records in the config flash is `blink`, which also toggles PIN_87
   (every 4 s) and animates the other three LEDs, so a silently failed SRAM load
   (CLAUDE.md Article IV) still blinks LED4. `blink` leaves the display pins tri-stated,
   so it cannot show the dashes. This check cannot tell one demo build from another:
   `check_board.py` (step 5) is the test that the design behaves, and `upload.sh`'s
   manifest guard only ensures the build being programmed matches the sources on disk.
4. **Connect:** the board's UART goes through a MAX3232 to an RS-232 connector, so the
   Mac needs a **USB-to-RS-232 adapter**. A 3.3 V TTL adapter will not work. The board's
   DB9 is wired as DCE (it transmits on pin 2, receives on pin 3; schematic V2.1, RS232
   section), so use a **straight-through** cable or plug the adapter in directly. A
   null-modem (crossed) cable joins TX to TX: nothing arrives at either end and the host
   only reports a timeout. Find the adapter with
   `$PY projects/demo/host/fpga_link.py` (lists ports); use the `/dev/cu.*` node.
5. **Hardware test:** `$PY projects/demo/host/check_board.py /dev/cu.<adapter>`
   sends the 16 test images and requires the digit and all 10 scores of every reply to
   equal `mem/expected.hex`. It prints PASS or FAIL and exits 0 or 1.
   `check_board.py --fake` runs the same test against `host/fake_fpga.py` (the golden
   model behind a pseudo-terminal). That tests the host code only, not the board.
6. **Draw:** `$PY projects/demo/host/draw.py`. Pick the adapter in the port menu, or
   "Simulate (no board)" to run the golden model on the Mac. With a board, the status
   line says whether the FPGA's scores match the golden model bit for bit, and shows the
   round-trip time. `--fake` adds the fake board to the menu.
