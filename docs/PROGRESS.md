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

---

## 2026-09-21 — Local synthesis on the Mac, in an emulated x86-64 VM

**Phase:** 1 — combinational fundamentals. Toolchain only; no RTL of Alex's changed.
**Built:** No new RTL. `tools/quartus-vm/lima.yaml` — a full-system x86-64 Ubuntu
24.04 VM running Quartus Prime Lite 20.1.1 on the Mac. `build.sh` and
`tools/buildui.py` gained a backend switch (`BACKEND=local|remote`, default: use
lyco-server if it answers, otherwise the local VM). Motivation: Alex is taking the
board to his AI club, where Tailscale is blocked and outbound SSH to GCP is too, so
the existing build path is unreachable.
**Verified:** Not on hardware. Verified instead by byte-for-byte comparison against
the server: `clock_counter` and `full_adder` were compiled on lyco-server and in the
VM from *identical* sources (same `source_sha256`), and both `.rbf` bitstreams match
exactly — `08958f2b…` and `d7f6bcdc…`. The `clock_counter` `.rbf` also matches the
2026-09-08 build, so that bitstream is now reproducible across three compiles on two
machines. **Caveat, explicitly unverified:** the `.sof` and `.svf` do *not* match,
because both embed a build timestamp, and `.svf` is what `program.sh sram` actually
loads. A VM-built `.svf` has never been put on the board. That must be tested on
hardware before it is trusted.
**Resources:** unchanged, which is the point — they are the control, not a result.
`clock_counter` 51 / 6,272 LEs · 33 / 6,272 registers · 0 / 276,480 memory bits ·
0 / 30 9-bit multiplier elements · 6 / 92 pins · worst-case slack −3.666 ns.
`full_adder` 2 / 6,272 LEs · 0 registers · 5 / 92 pins. Read from the VM's own
`clock_counter.fit.summary`, and identical to the numbers lyco-server reports.
**Learned:** Nothing of Alex's — this is Article I "toolchain" work, and he wrote no
RTL today. The decision that was his: he ruled out bringing lyco-server to the club
and asked for local synthesis specifically, which is what forced the VM route rather
than a network workaround.
**Stuck on:**
- The VM-built `.svf` is unproven on hardware (above). First thing to check.
- Quartus 20.1 **cannot** run under user-mode emulation, which is why this is a
  whole VM and not a container. Both paths were tried and both fail: under Rosetta
  glibc aborts with `mremap_chunk(): invalid pointer`; under `qemu-x86_64` it
  segfaults in `PDB_SEGMENT_READER::xfr_stl_ptr` at `0xffffffff85f03f20` — a
  sign-extended 32-bit pointer — while loading the Cyclone IV device database.
  Recorded so nobody spends another evening rediscovering it.
- The VM is ~3.6× slower than the server: 118 s vs 33 s for `clock_counter`. Fine
  at this design size; worth re-measuring when the accelerator gets big.
- Compiling in the repo is now avoided deliberately: an early attempt ran Quartus
  directly on `projects/clock_counter/` and it silently appended
  `LAST_QUARTUS_VERSION` and `RESERVE_ALL_UNUSED_PINS_NO_OUTPUT_GND` to the `.qsf`,
  changing the source hash and so the staleness guard. Both backends now copy the
  project out of the repo before building.
- Still undrained from before: `docs/QUIZ-INBOX.md`, including the latch inference
  in `clock_counter` that the fitter has on record and Alex has not yet seen.

---

## 2026-09-21 — Trying to make the emulated build faster, and failing

**Phase:** 1 — toolchain. No RTL changed.
**Built:** Nothing new. Three attempts to speed up the VM build, and the honest
result of each. Also fixed the build UI, which was reporting the wrong machine.
**Verified:** By measurement, compiling `clock_counter` on an M4 Pro (8 P-cores):

| config | elapsed |
|---|---|
| 6 vCPU · `NUM_PARALLEL_PROCESSORS 4` | **111–114 s** |
| 8 vCPU · `NUM_PARALLEL_PROCESSORS 4` | 118 s |
| 8 vCPU · `NUM_PARALLEL_PROCESSORS 8` | 124 s |

**Resources:** unchanged (51 / 6,272 LEs, 33 registers, 6 / 92 pins). The `.rbf`
stayed `08958f2b…` through every one of these runs, including at parallelism 8 —
so Quartus's thread count really does change only compile time, not results.
**Learned:** Nothing of Alex's; this is toolchain. The instructive part is the
negative result: **adding cores makes emulated compilation slower.** Multi-threaded
TCG pays more in cross-thread synchronisation than it wins in parallelism, so the
intuition "more cores = faster" inverts here. The stage breakdown says where the
time actually is: `quartus_map` 43 s, `quartus_fit` 27 s, `quartus_asm` 5 s,
`quartus_sta` 8 s, and ~23 s of process startup across four separate tool
launches. Roughly 110 s is the floor for a full compile at this design size.
Preserving `db/` between builds (so Quartus can compile incrementally) was worth
only ~5 s at this size, though it is still the correct behaviour and matches what
the remote path has always done.
**Stuck on:**
- No further speedup found. If this becomes painful when the accelerator is large,
  the lever is *fewer full compiles*, not a faster VM — `quartus_map` alone is 43 s
  and answers "does it synthesise, and how many LEs", without fitting or assembling.
- The build UI was showing `lyco-server · i5-6300U · 6 threads` while building in
  the VM, and printing `0.0 °C` / `0.00 GHz` for sensors that do not exist there.
  Both now read from whichever backend is actually building, and absent sensors
  print `n/a` instead of a number that looks like a measurement.
- Still unverified, unchanged from the previous entry: no VM-built `.svf` has been
  put on the board.

---

## 2026-09-21 — Rosetta works after all; the Mac is now faster than the server

**Phase:** 1 — toolchain. No RTL changed.
**Built:** `tools/quartus-docker/Dockerfile` — Quartus running under **Rosetta**, which
two entries ago was written off as impossible. `build.sh` and `tools/buildui.py` now
pick between three backends: `local` (Rosetta, default), `remote` (lyco-server), `vm`
(the emulated VM, kept only as a fallback).
**Verified:** All five projects rebuilt under Rosetta and compared against the
lyco-server builds of the same sources. **Every `.rbf` matches byte-for-byte** —
blink `4bc59c4a…`, full_adder `d7f6bcdc…`, keytest `19e58032…`, button_counter
`abf4ef99…`, clock_counter `08958f2b…`. Also verified on hardware, by accident and
before any of this: the blink Alex programmed earlier was the 19:56 build, and its
log paths are `/home/arona.guest/` — the VM. So a locally-built `.svf` has been on
the board and works. That closes the caveat left open in the first entry.

| backend | clock_counter | all five |
|---|---|---|
| Rosetta container (local) | **22 s** | 109 s |
| lyco-server (native x86-64) | 33 s | ~165 s |
| emulated VM (TCG) | 111–118 s | — |

**Resources:** unchanged (clock_counter 51 / 6,272 LEs · 33 registers · 6 / 92 pins).
**Learned:** Nothing of Alex's; toolchain. The lesson for me is about diagnosis. Two
entries ago I concluded "Quartus cannot run under user-mode emulation" from two
crashes, and that conclusion was **wrong** — it was one fixable bug wearing different
masks. What was missing was a *stack trace*. `mremap_chunk(): invalid pointer` and
`realloc(): invalid pointer` look like generic heap corruption; on centos:7 the same
crash prints a backtrace and names the culprit outright:

    double free or corruption ... libudev.so.1(udev_device_unref)
                                  libudev.so.1(udev_enumerate_scan_devices)
                                  libsys_cpt.so   <- Quartus

Quartus inventories system devices at startup, and libudev double-frees under Rosetta.
Nothing in the compile flow needs it, and Quartus `dlopen`s libudev by name — probing
both `libudev.so.0` and `libudev.so.1`, so it already tolerates absence. Deleting it
from the image fixes it. Two things were needed together, which is why neither showed
up alone: **centos:7** for glibc 2.17 (modern glibc's malloc checks abort on Quartus's
allocation patterns under Rosetta), and **no libudev**.
**Stuck on:**
- The `local` backend needs Docker Desktop running. If it is not, `build.sh` falls
  through to lyco-server, then to the VM, and says which it chose.
- `centos:7` is EOL. Acceptable here only because nothing is installed into it and it
  never touches the network — it is a frozen ABI, not a maintained system.
- The emulated VM (~10 GB) is now redundant. Kept as a fallback; `limactl delete
  quartus` reclaims the space whenever that is wanted.
- Still undrained: `docs/QUIZ-INBOX.md`, including the latch inference in
  `clock_counter` that the fitter has on record and Alex has not yet seen.

---

## 2026-09-21 — A backend picker, after auto-detection picked wrong silently

**Phase:** 1 — toolchain. No RTL changed.
**Built:** A **BACKEND selection page** in `tools/buildui.py`, offered before the build
starts: Rosetta (~22 s) · lyco-server (~33 s) · QEMU (~115 s), each with a live status.
Alex asked for it after running `./build.sh` and watching it grind through a ~2 minute
synthesis on QEMU without ever saying why.
**Verified:** `./build.sh` with nothing forced now reports `backend: local` and finishes
`clock_counter` in 23 s, `.rbf` still `08958f2b…`. The picker renders correctly with
Rosetta ready, lyco-server shown as needing the network, and QEMU ready.
**Learned:** Nothing of Alex's; toolchain. Two failures worth recording, both mine:

1. **The Rosetta image had silently disappeared** from Docker, so `docker_ready()`
   returned false and auto-detection fell all the way through to QEMU. The build
   still worked, just 5× slower, and said nothing about the demotion. A fallback
   that does not announce itself is indistinguishable from a bug — which is the
   Article IV lesson again, in a new costume.
2. **Rebuilding that image needs the network**, to pull `centos:7`. That is exactly
   what is missing on the network this whole backend exists for. Now `docker save`s
   to `~/.lycochip-build/quartus-image.tar` (73 MB) and both `build.sh` and the UI
   reload from it automatically when the image is absent. Tested by deleting the
   image: restored in 0.8 s with no network.

The picker also does no network probing, so it appears instantly instead of waiting
on an ssh timeout, and it starts on a backend that is *ready* rather than merely
plausible. Picking Rosetta with Docker stopped now starts Docker rather than failing.
**Stuck on:**
- Docker Desktop still has to be running for the fast path. The page says so plainly
  now, which is the point.
- Still undrained: `docs/QUIZ-INBOX.md`.

---

## 2026-09-21 — colima, so the build loop needs no Docker Desktop

**Phase:** 1 — toolchain. No RTL changed.
**Built:** The Rosetta backend now runs on **colima** — a CLI-managed Linux VM with
Rosetta via Apple's virtualisation framework — instead of Docker Desktop. `build.sh`
and the build UI start it on demand, so nothing has to be left running in the menu bar.
**Verified:** Docker Desktop quit *and* colima stopped, then `./build.sh clock_counter`
with nothing started by hand: it printed `starting colima`, brought the VM up, and
compiled. 45 s cold (≈19 s of that is the VM), **24 s warm**, `.rbf` still `08958f2b…`.
Docker Desktop stayed shut the whole time.

| runtime | clock_counter |
|---|---|
| colima, warm | 24 s |
| colima, cold (VM boot included) | 45 s |
| Docker Desktop | 22–23 s |

**Learned:** Nothing of Alex's; toolchain. The bug worth recording is mine and it was
backwards-shaped: forcing `BACKEND=local` *skipped* the detection branch that brings the
runtime up, so an **explicit** choice failed instantly while the automatic one worked.
Start-up belongs after the backend is resolved, not inside the code that guesses it.
**Stuck on:**
- colima must be started once per boot; `build.sh` does it automatically (~19 s), so
  the only cost is that one build per session is slower.
- Docker Desktop can now be uninstalled if wanted, but not for free: `brew install
  docker` put a standalone CLI in the Cellar (verified working against colima),
  yet Homebrew did not symlink it into PATH. `brew link docker` is needed first,
  or removing Desktop takes the `docker` command with it.
- Still undrained: `docs/QUIZ-INBOX.md`.

---

## 2026-10-20 — Exercises archived; repo reorganised around the MNIST design

**Phase:** 0 — foundations. Repo structure only; no RTL changed.
**Built:** No RTL. The five Phase 0 exercises (`blink`, `full_adder`, `button_counter`,
`clock_counter`, `keytest`) moved unchanged from `projects/` to `archive/exercises/`.
`projects/mnist/` created, holding only a `README.md` that lists the open design
decisions. The old toolchain `README.md` is now `docs/TOOLCHAIN.md`; the new root
`README.md` is about the chip. Retired `docs/QUIZ-INBOX.md` moved to `archive/docs/`.
`build.sh` and `tools/buildui.py` no longer fall back to `blink` when no project is named.
**Verified:** No sim, no hardware, no synthesis. The tooling was checked by running it:
`./lint.sh` reports no RTL and exits 0; `PLAIN=1 ./build.sh` with no name, and with
`keytest`, both refuse and print the available list; `artifacts.py resolve keytest`
still finds `builds/20260922-112233-keytest-995b65b2`, so `./upload.sh` can still
program it. In a scratch copy with `keytest` put back under `projects/`, discovery lists
it and its source hash is `995b65b2…`, the same as that archived build. Moving an
exercise back with `git mv` restores it exactly.
**Resources:** none, since nothing was synthesised.
**Learned:** Nothing of Alex's was demonstrated this session. The decision that was his
is the target system: the Mac sends a handwritten digit, the FPGA runs the inference,
and the answer comes back. He suggested VGA for the image. The board's VGA port is
output only (HSYNC/VSYNC plus one bit each of R/G/B, PIN_101/103–106, per the vendor pin
table and schematic V2.1), so how the image gets in is still an open decision.
**Stuck on:**
- The input link. What the board can actually receive: RS-232 through the MAX3232
  (UART PIN_114/115, which needs a USB-to-RS-232 adapter on the Mac), PS/2, the keys,
  and JTAG. Listed in `projects/mnist/README.md` with the other open decisions.
- `9b45dc7` committed `build.sh` and `upload.sh` with mode 100644, down from 100755, so
  `./build.sh` failed with `permission denied` at HEAD. Most likely a non-mode-preserving
  rewrite of both files on 2026-09-23. Mode restored to 755 in the working tree;
  not yet committed.
- The Phase 0 roadmap items still owed: debouncer, FSM, first testbench. No testbench
  exists anywhere in the repo. Every `LEARNING.md` card is still at box 1.
  `pin-assignment-shape` was asked today; awaiting his answer.

## 2026-10-20 — First trained model, 4-bit weights exported

**Phase:** 3 — Python golden model and quantisation
**Built:** `projects/mnist/model/train.ipynb` (PyTorch, env `LC-MNIST`): a 784 → 16 → 10 network with ReLU, trained 5 epochs on MNIST. `quantise()` and an accuracy harness, then an export cell writing `export/w1.hex`, `export/w2.hex` and `export/meta.json`. `environment.yml` pins the env.
**Verified:** Python only; no RTL, no sim, no hardware. The exported `.hex` files were read back from disk and decoded in a separate process, then run through a fresh float model with the original biases. That gave 0.9265, the same as the notebook's own 4-bit figure. Float baseline is 0.9349. Weights only are quantised: biases, activations and accumulators are still float.
**Resources:** none, since nothing was synthesised. For budgeting: 12,704 weights × 4 bits = 50,816 bits, against 276,480 bits of M9K.
**Learned:** Nothing of Alex's was demonstrated. The decisions that were his: hidden layer of 16 neurons (he tried 64 first, which needs more than 276,480 bits at 8 bits per weight), and 4-bit weights. The reasons are not yet written in `projects/mnist/README.md`. `quantise()` was written by Claude at his request after he was offered the derivation; he has not yet explained it (card `symmetric-quantisation`).
**Stuck on:**
- Bias, activation and accumulator formats are undecided; the export leaves biases in float (`meta.json`).
- Word layout is row-major (index = neuron × n_inputs + input), chosen by Claude as a default. It decides how the control FSM addresses the ROM, so it is his to confirm or change.
- With a symmetric scale 4 bits use −7…7, so the code for −8 is never used.

## 2026-10-20 — Integer-only inference check, int8 to int64

**Phase:** 3 — Python golden model and quantisation
**Built:** In `projects/mnist/model/train.ipynb`, replaced the float-simulated quantisation (fake-quant harness and the 4-bit `.hex` export) with a real integer pipeline, `int_inference(bits)`. Training is still float. The trained weights are quantised symmetrically to N bits, then pixels → accumulate → bias → ReLU → rescale by integer multiply and shift → accumulate → argmax are all integer operations. Python big ints where int64 could overflow.
**Verified:** Python only; no RTL, no sim, no hardware. Test accuracy on the 10,000 MNIST test images, 784 → 16 → 10, rescale calibrated on 5,000 train images: float32 0.9349, int8 0.9343, int16 0.9349, int32 0.9349, int64 0.9349. Compared by accuracy only, not prediction-by-prediction. Biases quantised at the accumulator's scale; activations quantised to the same N.
**Resources:** none, since nothing was synthesised.
**Learned:** Nothing of Alex's was demonstrated. He directed the approach: train in float, then test integer accuracy from 8 to 64 bits. The integer pipeline was written by Claude at his request.
**Stuck on:**
- Accumulator width observed on the test set: layer 1 needs 22 bits at int8 (30 at int16); layer 2 needs 16 at int8. These are observed maxima, not worst-case bounds. At int32 and int64 the layer-2 accumulator needs 64 and 128 bits, so a machine int64 would overflow at int64.
- 4-bit and other widths below 8 are not tested in this pipeline yet (one-line change: add the width to the loop). The earlier 4-bit result (0.9265) came from the float-simulated harness, now removed. The stale `export/` directory and `weights_float.npz` are still on disk and are no longer written by the notebook.

## 2026-10-20 — int8 integer model exported with test vectors

**Phase:** 3 — Python golden model and quantisation
**Built:** `train.ipynb` now builds the integer network in `build_int_net(bits)` and exports the int8 version to `projects/mnist/model/export/`: `w1.hex` (16 × 784) and `w2.hex` (10 × 16) as 8-bit two's complement, `b1.hex` and `b2.hex` as 32-bit words, `test_images.hex` (16 raw-pixel images), `expected.json` (layer-1 accumulators, hidden activations, scores and predictions for those 16) and `meta.json` (shift, multiplier `M`, scales, layout). This replaces the stale 4-bit export of earlier today.
**Verified:** Python only; no RTL, no sim, no hardware. A separate process read only `export/` and the raw test set, reimplemented the integer forward pass in int64, and got 0.9343 on all 10,000 test images, the same as the notebook's int8 figure. It reproduced `expected.json` exactly (scores, hidden activations and predictions for all 16 vectors), and `test_images.hex` equals the first 16 test images. 15 of those 16 are classified correctly.
**Resources:** none, since nothing was synthesised. For budgeting: 12,704 weights × 8 bits = 101,632 bits against 276,480 bits of M9K, plus 26 bias words.
**Learned:** Nothing of Alex's was demonstrated; the pipeline and export were written by Claude at his request.
**Stuck on:**
- The rescale between layers is `(acc1 × M + 2^31) >> 32` with `M` = 493,047 (19 bits) and a 21-bit non-negative accumulator, so the product is 40 bits. That is a wide multiply for this part, and `SHIFT` is a free parameter. Choosing it (or a power-of-two scale so the multiply becomes a shift) is a design decision that has not been made.
- Word layout (row-major) and the choice of int8 for the first hardware target are defaults, not decisions he made.

## 2026-10-20 — HDL scaffold for projects/mnist, sim runner

**Phase:** 0 → 1 (tooling for the first testbench and the MAC)
**Built:** Toolchain only, no RTL. `projects/mnist/` now has `mnist.qpf`, `mnist.sdc` (50 MHz on `clk`) and `mnist.qsf` (device and globals, top `top`; file list and pin block left empty for Alex). New `sim.sh` runs `tb/*.v` in Icarus with a strict verdict. `lint.sh` resolves submodules from `rtl/` (`-y`). `build.sh`, `buildui.py` and `artifacts.py` now sync and hash `.hex`/`.mif` (ROM contents are part of the bitstream; before this a `$readmemh` file would never have reached Quartus) and exclude `tb/`.
**Verified:** The runner was checked against six throwaway testbenches in a scratch dir: it passed the correct one (which also read a `.hex` by a project-relative path), and failed one that printed FAIL, one that printed FAIL then PASS, one that never printed PASS, one that never finished (timeout), and one that compiled only because of an implicit net. That last one *passed* on the first version of the runner, which now rejects iverilog's `implicit definition` warning. The rsync filter was run on the real project: the `.hex` files go, `tb/` does not. Old `lint.sh` failed on a file instantiating a sibling module (rc 2); with `-y` it passes in both iverilog and verilator. No Quartus build of `mnist` (nothing to build).
**Resources:** none, since nothing was synthesised.
**Learned:** Nothing of Alex's was demonstrated; this was plumbing.
**Stuck on:**
- **The export does not match the spec.** Design Spec v0.1 lists 4-bit weights as Decided. `model/export/` is int8: `meta.json` says `weight_bits: 8`, `w1.hex` is 12,544 lines of 2 hex digits with values −127…118, `w2.hex` 160 lines −127…85. The notebook (`EXPORT_BITS = 8`) has never run 4-bit through the integer pipeline, so there is no integer 4-bit accuracy number yet. Either the spec or the export has to change.
- Observed ranges in `expected.json` (16 images, int8): layer-1 accumulator after ReLU up to 690,580; hidden activations 0…79 (clamp 127); scores −14,966…7,024. `b1` fits in 16 signed bits and `b2` in 10, though stored as 32-bit words. All observed, not worst-case.
- `test_images.hex` is simulation data but lives beside the weights, so it is hashed as a source; changing it would mark a build stale. Harmless; noted.

## 2026-10-20 — Export switched to 4-bit weights

**Phase:** 3 — Python golden model and quantisation
**Built:** At Alex's direction, the int8 export was deleted and `train.ipynb` now exports 4-bit weights. `build_int_net` takes `w_bits` and `a_bits` separately: one `bits` used to set both the weight width and the hidden-activation clamp, so going to 4 would have silently clamped hidden values to 0…7. Export: `WEIGHT_BITS = 4`, `ACT_BITS = 8` (unchanged; open decision #1). The export cell now empties `export/` first, so a width change leaves nothing stale. Notebook re-run end to end with the `lc-mnist` kernel.
**Verified:** Python only; no RTL, no sim, no hardware. A separate process read only `export/` and the raw MNIST test files, and redid the integer forward pass from `meta.json`. It got 0.9275 on all 10,000 test images, matching the notebook, and reproduced `expected.json` exactly (accumulators, hidden values, scores, predictions); `test_images.hex` equals the first 16 test images. Retraining reproduced float 0.9349 and w8/a8 0.9343, the same as before the refactor.
**Accuracy (10,000 test images):** float 0.9349 · w4/a8 **0.9275** · w4/a4 0.9019 · w8/a8 0.9343 · w16+ 0.9349.
**Resources:** none synthesised. Weights now 12,704 × 4 = 50,816 bits (18% of 276,480).
**Learned:** Nothing demonstrated. Alex's decision: 4-bit weights, per Design Spec v0.1. Reason not yet written down.
**Stuck on:**
- New ranges over the full test set: layer-1 accumulator (after ReLU) up to 65,478; `b1` −757…1,228, `b2` −19…12 (still stored as 32-bit words); scores −1,174…759; hidden values reach the 127 clamp. Observed, not worst-case.
- The requantisation multiplier grew: `M` = 9,065,027 is 24 bits (it was 19), because the accumulator range shrank. A 17-bit × 24-bit product.
- Weights span −7…6 in `w1` and −7…5 in `w2`; the −8 code is never used (symmetric scale).
- Layout is still the row-major default, not decision #6.

## 2026-10-20 — Article I override: Claude builds a reference demo in projects/demo/

**Phase:** side project (not on the roadmap)
**Built:** Started. `projects/demo/` holds a complete MNIST demo built by Claude: Mac drawing app, UART, and RTL. `README.md` and `ARCHITECTURE.md` record the override and the contract. Model snapshotted from `projects/mnist/model/export/` by `host/make_mem.py`, checked against `expected.json`.
**Verified:** not yet (in progress; a later entry will report sim, synthesis and hardware status).
**Resources:** not yet.
**Learned:** Nothing of Alex's. Claude stated the conflict with Article I (a finished answer key for the modules he is about to write) and offered the Mac app with a Python stand-in for the FPGA. Alex chose the full demo including RTL, to run on his board. The override covers `projects/demo/` only; `projects/mnist/` stays his.
**Stuck on:** nothing yet.

## 2026-10-20 — demo (Claude-authored) passes sim and synthesis

**Phase:** side project, under the Article I override for `projects/demo/` only
**Built:** By Claude through a 37-agent workflow: 14 RTL modules (`demo_top`, `controller`, `uart_rx`/`uart_tx`, `frame_rx`, `image_buf`, `weight_rom`, `bias_rom`, `mac`, `post`, `hidden_buf`, `argmax`, `result_tx`, `seg7`) with a unit testbench each, plus `tb_demo` end to end. Host side: `draw.py` (drawing app), `fpga_link.py`, `check_board.py` (hardware test), `fake_fpga.py`, `golden.py`, `make_mem.py`. Handoff notes in `projects/demo/CLAUDE.md`.
**Verified:** Sim and synthesis only; not on hardware. Re-run by the main session after the workflow: `./lint.sh demo` clean; `./sim.sh demo` 14/14 PASS, with `tb_demo` matching 16 of 16 images bit for bit (digit and all 10 scores) through the UART pins; `check_board.py --fake` 16/16 PASS; `draw.py --smoke` OK. Every testbench was shown to FAIL on deliberately broken copies.
**Resources:** from `~/.lycochip-build/projects/demo/demo.fit.summary`, build `builds/20261020-154210-demo-b3a6f1b1`: 882 / 6,272 LEs · 549 / 6,272 registers · 57,216 / 276,480 memory bits · 7 / 30 9-bit multiplier elements · 20 / 92 pins. Fmax 69.04 MHz (Slow 1200mV 85C), worst setup slack +5.516 ns. All 20 pins `User Assignment = Y`.
**Learned:** Nothing of Alex's (Claude-authored). Toolchain lessons: Quartus 20.1 silently ignores an initialiser on an `output reg` port declaration (Icarus honours it), which made `uart_tx` idle low; it was caught by gate-level sim of the post-fit netlist. Also, `build.sh` was deleting Quartus's own `db/*.mif`, which broke the second build of unchanged sources. Fixed by excluding `db/` and `incremental_db/` from the sync; two consecutive builds then succeeded.
**Stuck on:** Hardware. No USB-to-RS-232 adapter has been connected yet. The board's DB9 is DCE, so it needs a straight-through cable. Bring-up continues on Alex's Windows machine with native Quartus; `build.sh`/`upload.sh` are Mac-only.

## 2026-10-20 — demo (Claude-authored) built on Windows with Quartus 25.1, loaded on the board

**Phase:** side project, under the Article I override for `projects/demo/` only
**Built:** No RTL changed (repo at `ff85d8d`, `projects/demo/` clean). First build on the Windows PC, with Quartus Prime Lite **25.1std** (`C:\altera_lite\25.1std`; 20.1 is not installed there), from a copy of the sources at `C:\Users\Alex\.lycochip-build\projects\demo\` so Quartus cannot rewrite the `.qsf` in the repo. `quartus_sh --flow compile demo`, 26 s, 0 errors, 18 warnings, 0 critical warnings. Programmed to SRAM with `quartus_pgm -c "USB-Blaster [USB-0]" -m JTAG -o "p;demo.sof"` (`demo.sof` sha256 `3b56a34e…`).
**Verified:** Synthesis + load on hardware; **the inference itself is not verified on hardware.** Reports: all 20 ports `User Assignment = Y` in `demo.pin`, at the `ARCHITECTURE.md` pins, all 3.3-V LVTTL; `weight_rom` is an M9K ROM 12,704 × 4. The ROM contents were checked independently of Quartus's own messages: the `.mif` files Quartus generated in `db/` were parsed and compared with `mem/weights.hex` (12,704 words, 0 mismatches) and `mem/bias.hex` (26 words, 0 mismatches; words 26–31 are don't-cares filled with 0). That matters because git's `core.autocrlf=true` on this machine checked every `.hex` out with CRLF line endings. Load check by Alex, by eye: dashes on all four digits and LED4 blinking, a pattern the flash's `blink` cannot produce. `check_board.py COM1` → 0/16 FAIL, no bytes received: **no serial cable is connected** (COM1 is the motherboard UART; there is no USB serial adapter on the PC), so this FAIL says nothing about the design.
**Resources:** from `demo.fit.summary` (25.1std): 882 / 6,272 LEs · 549 / 6,272 registers · 57,216 / 276,480 memory bits · 7 / 30 9-bit multiplier elements · 20 / 92 pins. Fmax 69.04 MHz (Slow 1200mV 85C), worst setup slack +5.516 ns, worst hold +0.108 ns (Fast 0C). Identical to the 20.1 build on the Mac.
**Learned:** Nothing of Alex's (Claude-authored). Toolchain: on this PC `jtagconfig` names the part `10CL006(Y|Z)/10CL010(Y|Z)`. That is the same IDCODE, `020F10DD`, as the EP4CE6 (Cyclone 10 LP is the same die), and the Programmer accepted the EP4CE6 `.sof` against it. Earlier the same session, "JTAG chain broken" with the Blaster listed meant the board was unpowered, the same lesson as the Mac's "TDO stuck at 0".
**Stuck on:** The serial link. The board's DB9 needs an RS-232 connection to the PC: a USB-to-RS-232 adapter (not 3.3 V TTL) and, since the board's DB9 is believed DCE, a straight-through cable. The connector's gender and the DCE pinout are both still unverified by hand. Sim on Windows is also not set up: no iverilog, verilator or perl, and `sim.sh`/`lint.sh` are CRLF in this checkout.

## 2026-10-20 — demo (Claude-authored) runs on the board: 16/16 bit-exact over JTAG

**Phase:** side project, under the Article I override for `projects/demo/` only
**Built:** A second link for the demo, because this PC has no RS-232 port. `rtl/vjtag.v` (Altera `sld_virtual_jtag`, instance 0, 2-bit virtual IR; an idle stub under Icarus/Verilator) and `rtl/jtag_link.v`: virtual IR 1 turns every 8 shifted bits into one byte for `frame_rx`, OR'd with `uart_rx`'s; virtual IR 2 reads back the 22-byte reply, captured from `result_tx` as it goes to `uart_tx`, plus a count. `host/jtag_bridge.py` drives a persistent `quartus_stp` and offers the port `JTAG (USB-Blaster)` to `check_board.py` and `draw.py`, which now selects it by default. `ARCHITECTURE.md` updated first. The UART path is unchanged.
**Verified:** **Sim + hardware.** Sim on Windows (Icarus 12, installed today via winget): all 14 existing testbenches PASS on the CRLF checkout, before and after the change. The new `tb_jtag_link` PASSes, and it FAILs on each of 7 deliberately broken copies of `jtag_link` (no bit-count reset at Capture-DR, MSB-first bytes, count not cleared, no 22-byte limit, count bumped in the same cycle, WRITE on any IR, count not captured). Quartus 25.1std: 0 errors, 0 critical warnings, all 20 user pins `Y`, weight/bias ROM `.mif` = `mem/*.hex` word for word. Programmed (`demo.sof` sha256 `c915e515…`), then `check_board.py JTAG`: **16/16 images, digit and all 10 scores equal to `mem/expected.hex`, PASS**, ~14 ms round trip each. This is the first evidence that the demo's datapath works on silicon. Each image's reply clears the previous one, and every image's expected scores differ, so a stale or partly-wrong design cannot pass. The RS-232 path is still untested on hardware.
**Resources:** from `demo.fit.summary` (25.1std): 1,468 / 6,272 LEs · 1,022 / 6,272 registers · 57,216 / 276,480 memory bits · 7 / 30 9-bit multiplier elements · 20 / 92 pins. Fmax clk 72.37 MHz (Slow 1200mV 85C), altera_reserved_tck 98.39 MHz; worst setup slack +6.182 ns. The JTAG link cost +586 LEs and +473 registers: the reply buffer and its 184-bit read shift register, plus Altera's JTAG hub.
**Learned:** Nothing of Alex's (Claude-authored). Toolchain: on Windows, `quartus_stp` holds back everything it writes to a pipe until it exits, even after `flush stdout`, so a pipe cannot carry a conversation with it. It talks over a loopback TCP socket instead; `quartus_stp -t` is then ready in ~0.25 s.
**Stuck on:** Nothing blocking. Open: Quartus already defines `altera_reserved_tck`, so `demo.sdc`'s `create_clock` for it only produces Warning 332043 (overwriting); it can go at the next rebuild. Building on the Mac now needs `vjtag.v`/`jtag_link.v` (already in `demo.qsf`), and `sim.sh` needs nothing new. SRAM loads are volatile: a power cycle brings back `blink`.
