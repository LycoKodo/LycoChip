# Overnight, 11–12 October 2026

Claude Code, running unattended on branch `reckoning-safety-path`. No Verilog was
written or edited, and no design decisions were made.

**Start here:** the video,
`C:\Users\Alex\lycochip-overnight-video\out\LycoChip-while-you-slept.mp4`.
- 6:21, 1080p30, 27.5 MB, with soft English subtitles.
- Checked with ffprobe for streams and duration, an audio level check (narration
  mean −19.6 dB), and frames pulled straight from the file.
- Made with your `tpu-explainer` pipeline in a separate folder. Nothing in
  `tpu-explainer` was changed.

## Done

- **Windows audit.** Results are in `docs/WINDOWS.md`.
  - Present: Core Ultra 5 250KF, RTX 5060 (sm_120), driver 617.14 / CUDA 13.4,
    git 2.55, Git Bash, Python 3.12.10, Docker CLI, WSL 2 (Ubuntu).
  - Absent: rsync, `~/.ssh`, Quartus, and the USB-Blaster.
- **`build.sh` / `upload.sh` run natively from Git Bash.** New `native` backend:
  Quartus `bin64` is auto-detected and 20.1 is preferred. It warns when the
  version isn't 20.1.1. `quartus_pgm` loads the `.sof`, `jtagconfig` detects and
  checks the EP4CE6 IDCODE, and flash is refused on this path. Mac, Docker, VM and
  lyco-server paths are unchanged.
  *Tested against stub Quartus binaries only.*
- **Cross-platform source hash, fixed and verified.** Sources are pinned to LF, and
  paths are hashed with `/`. Windows Python and WSL `python3` now agree on all
  five projects.
- **OSS CAD Suite, native Windows** at `~/oss-cad-suite` (not WSL; reasons in
  `docs/WINDOWS.md`). `lint.sh` runs, and found:
  - `blink.v:32` width mismatch — my bring-up code;
  - `full_adder.v`: iverilog fails on undeclared `S` and `c_out`, plus 8 ×
    `IMPLICIT`;
  - `clock_counter.v`: lint-clean, despite the fitter's latch warning on record.

  None of them was fixed.
- **`sim.sh`**: a testbench runner that requires an explicit `PASS`. There are
  no testbenches yet, so there was nothing real to run.
- **GPU venv** at `.venv/`: torch 2.14.1+cu130. `tools/gpu_check.py` **PASS**
  (2048² fp32 matmul vs a float64 CPU reference, relative error 8.6e-7).
- **`docs/research/flexheg.md`**: the full paper summary, the single-FPGA
  mapping, hash reading pointers and 14 open questions. Also **5 flexHEG
  questions** in `QUIZ-INBOX.md`.
- **Docs.** Small, marked edits to `CLAUDE.md` (Article V, plus a direction
  note) and a `PROGRESS.md` entry.
- **Your PowerShell** (done by a helper agent, all per-user, no admin):
  - Oh My Posh 31.7.0 prompt;
  - PSReadLine 2.4.5 predictive ListView, with Tab as a menu;
  - Terminal-Icons and posh-git;
  - the Meslo Nerd Font, set in Windows Terminal and VS Code;
  - execution policy CurrentUser → RemoteSigned (it was Undefined).

  The profile skips all of it in non-interactive shells. Undo steps are below.

## Failed or not done

- **No real Quartus run.** It isn't installed, so there is no `.sof` and no
  device-support check. Everything Quartus-shaped is unverified.
- **No JTAG test.** The board and USB-Blaster weren't connected.
- **Not pushed.** `git push` opened a Git Credential Manager "Connect to GitHub"
  window, which needs you. I stopped it rather than retry, so **all 12 of tonight's commits are
  local only**. Sorry if you saw that window flash up.
- **A correction to my own entry.** The `PROGRESS.md` entry says LF pinning
  makes Windows hashes match the Mac. It was only half the cause: path
  separators were the other half. That is fixed in `f1e8169`. `PROGRESS.md` is
  append-only, so the correction lives here and in `docs/WINDOWS.md`.
- *(Late in the night, now done.)* **`QUIZ-INBOX.md` is drained** into
  `LEARNING.md`:
  - `wire-vs-reg` and `vector-declaration-syntax` have new application Asks, since
    their old rubrics had been handed to you;
  - three new box-1 cards: `sized-literals`, `non-blocking-rhs` (still live in
    `clock_counter.v`) and `counting-flip-flops`.

  The five flexHEG questions stay undrained until someone actually asks them.
- **PowerShell 7 not installed.** It needs elevation and a licence click, both
  yours.

## Needs you — in this order

- [ ] **Watch the video** (6 min). It ends with three questions.
- [ ] **Push the branch.** In GitHub Desktop: *Push origin*. Or sign in, then run
  `git push origin reckoning-safety-path`.
- [ ] **Install Quartus Prime Lite 20.1.1** with **Cyclone IV** device support,
  at the default `C:\intelFPGA_lite\20.1`. If you choose a newer version, that's
  a decision: say so, and it gets logged.
- [ ] **Plug in and power the board**, then run, in PowerShell as
  **administrator**:
  `powershell -ExecutionPolicy Bypass -File tools\windows\install-usb-blaster-driver.ps1`.
  If Device Manager then shows Code 39 or 52 with Memory integrity on, the
  options are in `docs/WINDOWS.md`, and the choice is yours.
- [ ] In Git Bash, run `tools/windows/check-quartus.sh`. It covers version,
  device support, a real `clock_counter` build, the `.rbf` hash against
  `08958f2b…`, and JTAG.
- [ ] **Do the load test.** Power-cycle the board, then
  `./build.sh full_adder && ./upload.sh sram full_adder`. Nothing may animate.
  Then walk the 8-row truth table, which has been outstanding since 5 September.
- [ ] Restart Windows Terminal to see the new prompt. Optional: turn off the
  `python3` Store alias (Settings → Apps → Advanced app settings → App execution
  aliases).
- [ ] **Read `docs/research/flexheg.md` §7.** Which of the 14 questions change
  the RTL first?
- [ ] **Model and number-format decisions** — yours. The GPU is ready.
  - What network: an MLP? How many layers and units, against 30 multiplier
    elements and 276,480 memory bits?
  - Which number format: int8, fixed-point Qm.n, or per-layer scaling? How many
    bits for the accumulator?
  - What accuracy is enough, and what is it allowed to cost in LEs?
  - How do the weights reach the board, and through which path? This matters
    for the meter, because the weights are "external data".
- [ ] **Quiz.** Five flexHEG questions are in `QUIZ-INBOX.md`. `LEARNING.md` has
  due cards, `pin-assignment-shape` first.
- [ ] **Optional.** Article I's purpose sentence names only the accelerator.
  Amend it if the governance direction is now part of the point. That is your
  wording, not mine.

### Undo for the PowerShell changes

1. Remove the `# >>> nicer-shell` block from
   `Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1`.
2. Restore Windows Terminal from `settings.json.bak-20261012` (in its
   `LocalState` folder).
3. Delete `%APPDATA%\Code\User\settings.json` (it was new).
4. Run `Uninstall-Module PSReadLine,Terminal-Icons,posh-git -AllVersions`.
5. Delete `~\.local\bin\oh-my-posh.exe` and `~\.config\oh-my-posh`.
6. Run `Set-ExecutionPolicy -Scope CurrentUser Undefined`.
