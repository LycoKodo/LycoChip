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

## 2026-10-12 — Windows bench prepared overnight; direction set toward hardware-enabled governance

**Phase:** 1 — toolchain. No RTL changed. A direction decision of Alex's is recorded
below.

**Built:** No RTL. Toolchain only (all work on branch `reckoning-safety-path`):
- **`native` build backend.** `build.sh` and `upload.sh` gained it for a Windows PC:
  Quartus from `bin64`, programming with `quartus_pgm` and the `.sof`. It is
  auto-detected only on Windows, so the Mac, Docker, VM and lyco-server paths are
  unchanged. The host-specific logic lives in `tools/hostenv.sh`.
- **OSS CAD Suite** (Windows-native build, 2026-10-11) at `~/oss-cad-suite`, and
  `lint.sh` working on it.
- **`sim.sh`**, a testbench runner. A testbench must print `PASS` to pass.
- **GPU venv**: `torch 2.14.1+cu130`.
- **Docs and scripts**: `docs/WINDOWS.md`, the morning scripts in `tools/windows/`,
  and `docs/research/flexheg.md`.

**Verified:**
- **Build/upload plumbing: stubs only.** Tested against *stub* Quartus binaries in a
  scratch copy of the repo. That covered the source mirror, db/ surviving, the
  failure archive, the version-mismatch warning, detect, SRAM load, flash refusal and
  the staleness guard.
- **Real Quartus: unverified.** It is not installed.
- **Hardware: unverified.** No USB-Blaster was connected (no USB device with vendor
  ID `09FB`).
- **lint.sh: real run.** iverilog 14.0 and Verilator 5.053 on the existing RTL.
- **GPU: real run.** A fp32 2048² matmul on the RTX 5060 (sm_120) matched a float64
  CPU reference at 8.6e-7 relative error.
- **OSS CAD Suite download:** its SHA-256 matched the digest GitHub publishes.

**Resources:** No synthesis run, so no new numbers. For scale only, *not* our
measurement: the open-source secworks SHA-256 core reports, in its own README,
3,882 LEs / 1,813 registers on an EP4CE6 (Quartus II 13.1). If that holds, one
off-the-shelf SHA-256 is ~62% of this part.

**Learned:** Nothing of Alex's tonight — toolchain and reading, done while he slept.
- **His decision (2026-10-11):** take LycoChip toward hardware-enabled AI governance,
  prompted by *The Social Reckoning* and the flexHEG papers. The shape:
  1. finish the MNIST accelerator;
  2. a usage meter on the datapath the host can't reset;
  3. attestation of a hash of the weights plus the count;
  4. a write-up as a toy Interlock.

  The design is his. `docs/research/flexheg.md` §7 lists the questions it raises,
  unanswered.
- **Three Windows failures that are silent rather than loud**, the Article IV pattern
  again:
  - `python3` is found on PATH but is the Microsoft Store stub, so
    `command -v python3` lies.
  - `core.autocrlf=true` changes source bytes, and so `source_sha256`. Restoring
    `clock_counter.v` from git moved its hash from `1e469aff` to `4a5aa245` in the
    test copy with no content change.
  - Git for Windows has no rsync.
- **Lint findings on existing code, reported and not fixed:**
  - `blink.v:32`: `WIDTHEXPAND` (25-bit `cnt` compared at 32 bits).
  - `full_adder.v`: iverilog *fails* on use-before-declaration of `S` and `c_out`,
    and Verilator reports 8 × `IMPLICIT`. That is the `implicit-nets` card, live.
  - `clock_counter.v`: lint-clean. Yet the fitter's latch warning (13310) recorded in
    `QUIZ-INBOX.md` comes from code that is still there. **Lint-clean is not
    synthesis-clean**, and that is worth a question.

**Stuck on:**
- **Quartus is not installed** (Alex's to do). The repo is on 20.1.1, so installing
  that keeps bitstreams comparable with the Mac. Then: the USB-Blaster driver
  (admin), the Windows 11 Memory-integrity trap, `tools/windows/check-quartus.sh`,
  and the `full_adder` load test. All in `docs/WINDOWS.md`.
- **The branch is not pushed.** Git Credential Manager wanted an interactive GitHub
  sign-in, so every commit from tonight is local only. Push from GitHub Desktop, or `git push origin reckoning-safety-path` once signed in.
- **No testbenches exist yet.** `sim.sh` is ready for the first one.
- **`docs/QUIZ-INBOX.md` is still undrained,** now with 5 more questions (flexHEG).
