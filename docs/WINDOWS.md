# The Windows workstation

From October 2026 this PC is the main LycoChip bench. The board stays plugged in
here, and builds and programming happen here. The Mac stays for editing and
simulation. Everything below was read off this machine with commands on
2026-10-11/12; nothing is from memory.

## What is installed (audit, 2026-10-11)

| | Found | Notes |
|---|---|---|
| OS | Windows 11 Pro 10.0.26300 | 32 GB RAM |
| CPU | Intel Core Ultra 5 250KF Plus | x86-64, so Quartus runs natively — no Rosetta, no VM |
| GPU | NVIDIA GeForce RTX 5060, 8 GB | Blackwell, compute capability **sm_120** |
| NVIDIA driver | 617.14 (CUDA UMD 13.4) | |
| CUDA toolkit | 13.4 (`nvcc` V13.4.59) | not needed by PyTorch wheels, which bundle their own runtime |
| git | 2.55.0.windows.5 | `core.autocrlf=true` system-wide — see *Line endings* |
| Git Bash | bash 5.3.15, MINGW64 | the shell all the `.sh` scripts run in |
| Python | 3.12.10 (`python`, `py`) | `python3` is the **Microsoft Store stub**: it exists, and fails when run |
| Docker | CLI 29.8.2, Docker Desktop installed | daemon not running at audit time; not needed here |
| WSL | WSL 2, `Ubuntu` (stopped), `docker-desktop` | not used by LycoChip — see *Simulation* |
| Node | v24.19.0 / npm 11.17.0 | used by the explainer-video pipeline, not by LycoChip |
| VS Code | 1.140.0 | |
| Tailscale | 1.102.4 | |
| rsync, 7-Zip | **absent** | `build.sh`'s native backend copies without rsync |
| `~/.ssh` | **absent** | so the `lyco` alias, and the `remote` backend, do not exist here |
| Quartus | **not installed** (at audit) | yours to install — see below |
| USB-Blaster | **not plugged in** (no USB device with Altera vendor ID `09FB`) | |

Unrelated, but visible in the same scan: five Intel PCI devices (SM Bus
controller, a signal-processing controller, three "PCI Device") have no driver.
That is the motherboard chipset/INF package, not anything LycoChip needs.

## Quartus

**The repo builds with Quartus Prime Lite 20.1.1.** `build.sh`, the Docker image
and the VM all point at `intelFPGA_lite/20.1`, and the bitstream-reproducibility
evidence in `PROGRESS.md` (`clock_counter.rbf` = `08958f2b…` on three machines)
is 20.1.1 output.

- **Install 20.1.1 to match.** Then a Windows build of an unchanged project can
  be compared byte-for-byte with the Mac's, which is the cheapest cross-check
  the project has.
- A newer Lite (Intel's 2026 documentation still lists Cyclone IV in the Lite
  edition) will build fine, but its bitstreams won't be comparable, and
  `build.sh` says so on every build. If you go newer, that is a decision — log it.
- Either way, tick **Cyclone IV** device support in the installer. Default
  location: `C:\intelFPGA_lite\20.1\`.

`tools/hostenv.sh` finds Quartus automatically. Lookup order is `QUARTUS_BIN`,
then the installer's `QUARTUS_ROOTDIR`, then `C:\intelFPGA_lite\*` and
`C:\altera_lite\*`, preferring 20.1.

### After installing — the checks, in order

1. **Driver (admin, you).** Plug the board in and power it, open PowerShell
   *as administrator*, and run:
   `powershell -ExecutionPolicy Bypass -File tools\windows\install-usb-blaster-driver.ps1`.
   It shows what it found and asks before installing.
2. **Everything else (no admin).** In Git Bash, at the repo root, run
   `tools/windows/check-quartus.sh`. It checks:
   - the version, against 20.1.1;
   - that Cyclone IV E is installed, by asking Quartus for its part list;
   - a real `clock_counter` build through `./build.sh`, plus the fitter summary;
   - the `.rbf` hash against `08958f2b…`;
   - `jtagconfig`, expecting the EP4CE6 IDCODE `020F10DD`.
3. **The load test — the one that matters.** A tool's own "Successful" is not
   evidence (Article IV), so:
   1. Power-cycle the board. It boots whatever is in the config flash, so note
      what the LEDs are doing.
   2. Run `./build.sh full_adder && ./upload.sh sram full_adder`.
   3. `full_adder` is purely combinational: no clock, no counter. If **anything
      on the board still animates**, the load did not take, whatever
      `quartus_pgm` printed. If the LEDs sit still and follow the keys, it did.
   4. While you're there, walk its 8-row truth table. That is still outstanding
      from 2026-09-05.

**Never write the config flash from this PC yet.** `./upload.sh flash` refuses
on the Quartus path, on purpose. The proven flash path is the Mac's
openFPGALoader route.

### Known Windows 11 trap: Memory integrity

Several reports say the USB-Blaster driver bundled with older Quartus
releases will not load on Windows 11 while **Core Isolation → Memory
integrity** is on. Device Manager then shows Code 39 or 52. The install script
reports whether Memory integrity is on, and **changes nothing**. Your options
are below — each one is a tradeoff, so choosing between them is your call:

- turn Memory integrity off, which weakens a real kernel protection;
- use the driver from a newer Quartus Programmer;
- skip the Altera driver entirely. Use `openFPGALoader` (it ships in OSS CAD
  Suite) with a WinUSB driver installed via Zadig, and load the `.svf` exactly
  as the Mac does.

## How the scripts behave here

| Script | On Windows |
|---|---|
| `./build.sh [proj]` | `native` backend: runs `quartus_sh` from `bin64` against a copy in `~/.lycochip-build/projects/<name>/`, and prints the `.fit.summary` at the end. No arrow-key TUI (Windows Python has no `termios`), so with no project named you get a numbered menu. |
| `./upload.sh detect` | `jtagconfig`, then checks that IDCODE `020F10DD` answered |
| `./upload.sh sram [proj]` | `quartus_pgm -m JTAG` with the archived `.sof`, behind the same staleness guard as the Mac |
| `./upload.sh flash` | **refuses** (see above) |
| `./lint.sh` | iverilog and verilator from OSS CAD Suite |
| `./sim.sh [proj]` | runs `projects/<name>/tb/*_tb.v` |

Overrides:
- `BACKEND=native|local|remote|vm` picks the build backend.
- `QUARTUS_BIN=` points at a specific `bin64` directory.
- `PROGRAMMER=quartus|openfpgaloader` picks the programmer.
- `QCABLE=` names the cable, if `jtagconfig` lists more than one.

The Mac, Docker, VM and lyco-server paths are unchanged.

## Simulation: OSS CAD Suite, native Windows (not WSL)

Installed: `oss-cad-suite-windows-x64-20261011` at `C:\Users\Alex\oss-cad-suite`.
Its SHA-256 matched the digest GitHub publishes for the release. Versions:

- Icarus Verilog 14.0 (devel)
- Verilator 5.053 (devel)
- Yosys 0.69+274
- also GTKWave and openFPGALoader

**Why native rather than WSL:**

- **One shell.** `lint.sh` and `sim.sh` run from the same Git Bash as
  `build.sh` and `upload.sh`, with no `wsl` hop.
- **One filesystem.** WSL reading `/mnt/c` is slow, and paths get translated
  twice.
- **No VM to boot.** Nothing has to be running first.
- **The Windows build ships everything needed:** `iverilog`, `vvp`,
  `verilator_bin`, `gtkwave`, `yosys`.

**The cost:** the `verilator` wrapper is a Perl script that Git Bash's perl
can't run (it lacks `Pod::Usage`). The scripts call `verilator_bin` with
`VERILATOR_ROOT` set instead, which `tools/hostenv.sh` does. This is fine for
`--lint-only`. Full Verilator *simulation* (C++ build) would need a compiler,
and that is the point where WSL becomes the better home. Not needed yet.

**To use the tools in a plain terminal,** the scripts already set things up. In
any other shell, run `~/oss-cad-suite/environment.bat` (cmd) or
`~/oss-cad-suite/environment.ps1` (PowerShell).

**To update,** download a newer `oss-cad-suite-windows-x64-*.tgz` from
`github.com/YosysHQ/oss-cad-suite-build/releases`, then:

```sh
tar -xzf <file> -C ~/
```

## GPU Python environment

`.venv/` in the repo root, gitignored.

- Python 3.12.10
- `torch 2.14.1+cu130`, `torchvision 0.29.1+cu130`, numpy 2.5.2

The cu130 wheels include **sm_120** kernels. The RTX 50-series needs CUDA 12.8 or
newer wheels; older ones fail at the first kernel, even though
`is_available()` says True.

Recreate it:

```sh
python -m venv .venv
.venv/Scripts/python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130
.venv/Scripts/python tools/gpu_check.py
```

`tools/gpu_check.py` runs a real fp32 2048×2048 matmul on the GPU and compares
it with a float64 CPU reference. Result on 2026-10-11:

- 1.26 ms, about 13.7 TFLOP/s
- relative error 8.6e-7
- **PASS**

## Line endings

Git for Windows here has `core.autocrlf=true`, so a checkout turns LF into
CRLF. `tools/artifacts.py` hashes source **bytes**, so the same commit would
get a different `source_sha256` here than on the Mac. Bash would also see the
`\r`.

`.gitattributes` now pins `*.sh *.py *.v *.sv *.vhd *.qsf *.qpf *.sdc *.tcl`
to `eol=lf`.

The bytes were only half of it. `source_hash` also hashes each file's *path*,
and Windows Python spells paths with `\`. So even LF-identical sources hashed
differently: `clock_counter` came out `59f3d1a4…` here and `ff62f512…` under
POSIX Python (WSL), reading the same files. The hash now normalises paths to `/`.
On a POSIX host that is a no-op, so Mac manifests are unchanged.

Verified 2026-10-12, Windows Python against WSL `python3` on the same checkout:
all five projects match (`blink b78a43f6…`, `button_counter 6f86f059…`,
`clock_counter ff62f512…`, `full_adder 94f5f345…`, `keytest 995b65b2…`). Two more traps:

- **Windows Python writes `\r\n` to pipes.** The scripts strip `\r` from
  anything they parse out of `python`.
- **`python3` is the Microsoft Store stub.** The scripts use whichever of
  `python3` / `python` actually runs. To make `python3` work in your own
  terminal, turn off the two "App Installer python" aliases under
  Settings → Apps → Advanced app settings → App execution aliases.
