#!/usr/bin/env python3
"""
LycoChip demo on the Windows PC: program the board, check it and draw, from one menu.

  demo.cmd                   the menu (arrows or j k, Enter, q)
  demo.cmd go                program the newest build, run the board check, open the drawing app
  demo.cmd program|check|draw|build|detect
  demo.cmd program --force   program even if the sources changed since that build
  demo.cmd program --dry-run print the quartus_pgm command instead of running it

This is the Windows counterpart of build.sh + upload.sh, for projects/demo only
(CLAUDE.md Article V). Quartus Prime Lite 25.1std builds in a copy of the project
under ~/.lycochip-build/projects/demo, never in the repo. Every build is archived in
builds/ by tools/artifacts.py, and programming refuses a build whose sources differ
from the repo, the same guard as upload.sh.
"""
import os, re, shutil, subprocess, sys, time

HOST = os.path.dirname(os.path.abspath(__file__))
PROJ_DIR = os.path.dirname(HOST)
REPO = os.path.dirname(os.path.dirname(PROJ_DIR))
PROJ = "demo"
QBIN = os.environ.get("LYCO_QUARTUS", r"C:\altera_lite\25.1std\quartus\bin64")
CABLE = os.environ.get("LYCO_CABLE", "USB-Blaster [USB-0]")
BUILD = os.path.join(os.path.expanduser("~"), ".lycochip-build", "projects", PROJ)

sys.path.insert(0, os.path.join(REPO, "tools"))
import artifacts  # noqa: E402  (builds/ archive and the staleness guard)
from theme import fg, RESET, BOLD, CYAN, ICE, VIOLET, MUTED, PAPER, AMBER, ROSE, GREEN, DEEP  # noqa: E402

os.chdir(REPO)  # artifacts.py works relative to the repo root

# The files Quartus reads, as build.sh's SRCSYNC: tb/ never goes to Quartus, and db/ and
# incremental_db/ are Quartus's own (they hold .mif files it generates for inferred ROMs,
# which a mirror must not delete: Error 286034, 2026-10-20).
EXTS = (".v", ".vh", ".sv", ".vhd", ".qsf", ".qpf", ".sdc", ".tcl", ".hex", ".mif")
SKIP = {"tb", "db", "incremental_db"}


def say(s): print(f"{fg(CYAN)}==>{RESET} {s}")
def good(s): print(f"{fg(GREEN)}{BOLD}OK{RESET}  {s}")
def bad(s): print(f"{fg(ROSE)}{BOLD}!!{RESET}  {s}")
def warn(s): print(f"{fg(AMBER)}!!{RESET}  {s}")
def q(tool): return os.path.join(QBIN, tool + ".exe")


def run(cmd, cwd=REPO):
    """Run a command with its output streaming to the console. Returns the exit status."""
    try:
        return subprocess.run(cmd, cwd=cwd).returncode
    except FileNotFoundError:
        bad(f"not found: {cmd[0]}")
        return 127


def sources(root):
    out = {}
    for d, dirs, names in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP]
        for n in names:
            if n.endswith(EXTS):
                p = os.path.join(d, n)
                out[os.path.relpath(p, root)] = p
    return out


# ---- build ------------------------------------------------------------------
def sync():
    """Mirror the repo's Quartus inputs into BUILD, deleting ones the repo no longer has."""
    want = sources(PROJ_DIR)
    copied = removed = 0
    for rel, src in want.items():
        dst = os.path.join(BUILD, rel)
        if not os.path.exists(dst) or artifacts._sha(dst) != artifacts._sha(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            copied += 1
    for rel, p in sources(BUILD).items():
        if rel not in want:
            os.remove(p)
            removed += 1
    return copied, removed


def resources():
    """Resource numbers from the fitter summary and Fmax from the timing report, as Quartus wrote them."""
    st = {}
    try:
        for ln in open(os.path.join(BUILD, f"{PROJ}.fit.summary"), errors="replace"):
            k, _, v = ln.partition(" : ")
            if k.strip() in ("Total logic elements", "Total registers", "Total pins",
                             "Total memory bits", "Embedded Multiplier 9-bit elements"):
                st[k.strip()] = v.strip()
    except OSError:
        pass
    try:
        rpt = open(os.path.join(BUILD, f"{PROJ}.sta.rpt"), errors="replace").read()
        m = re.search(r"Slow 1200mV 85C Model Fmax Summary.*?\n(?:[+;].*\n){3}; ([\d.]+ MHz) ;[^;]*; (\S+)", rpt)
        if m:
            st["Fmax"] = f"{m.group(1)} ({m.group(2)}, slow 85C model)"
    except OSError:
        pass
    return st


def show_resources(st):
    for k, v in st.items():
        print(f"    {fg(MUTED)}{k:<36}{RESET}{v}")


def stage_outputs():
    """Copy this build's bitstreams to output_files/, where artifacts.archive() picks them up.
    A stale file from an older build is removed rather than archived under this one."""
    os.makedirs("output_files", exist_ok=True)
    for e in ("sof", "rbf"):
        src, dst = os.path.join(BUILD, f"{PROJ}.{e}"), os.path.join("output_files", f"{PROJ}.{e}")
        if os.path.exists(src):
            shutil.copy2(src, dst)
        elif os.path.exists(dst):
            os.remove(dst)


def build():
    t0 = time.time()
    os.makedirs(BUILD, exist_ok=True)
    c, r = sync()
    say(f"sources -> {BUILD}  ({c} copied, {r} removed)")
    log = os.path.join(BUILD, "build.log")
    say("compiling with Quartus Prime Lite 25.1std (a few minutes)")
    try:
        p = subprocess.Popen([q("quartus_sh"), "--flow", "compile", PROJ], cwd=BUILD, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    except FileNotFoundError:
        bad(f"Quartus not found at {QBIN} (set LYCO_QUARTUS to its bin64 folder)")
        return False
    with open(log, "w", encoding="utf-8") as lf:
        for ln in p.stdout:
            lf.write(ln)
            m = re.match(r"Info: Running Quartus Prime (.+)", ln)
            if m and m.group(1).strip() != "Shell":
                print(f"    {fg(MUTED)}{time.time() - t0:5.0f} s{RESET}  {m.group(1).strip()}")
            elif artifacts.ERR_RE.search(ln):
                print(f"    {fg(ROSE)}{ln.rstrip()}{RESET}")
    rc = p.wait()
    dur = round(time.time() - t0, 1)
    if rc != 0:
        m = artifacts.archive(PROJ, "failed", duration=dur, log=log)
        bad(f"BUILD FAILED after {dur:.0f} s. Earlier builds stay programmable.")
        for e in m["errors"][:20]:
            print("    " + e)
        print(f"    full transcript: {os.path.join(m['_dir'], 'build.log')}")
        return False
    stage_outputs()
    st = resources()
    m = artifacts.archive(PROJ, "ok", stats=st, duration=dur, log=log)
    good(f"built in {dur:.0f} s, archived as {os.path.relpath(m['_dir'])}")
    show_resources(st)
    return True


def adopt():
    """First run on this PC: archive the build already in BUILD, but only if its SOURCES.sha256
    shows it was compiled from exactly the sources now in the repo."""
    lst, sof = os.path.join(BUILD, "SOURCES.sha256"), os.path.join(BUILD, f"{PROJ}.sof")
    if not (os.path.exists(lst) and os.path.exists(sof)) or os.path.getmtime(sof) < os.path.getmtime(lst):
        return False
    listed = {}
    for ln in open(lst):
        h, _, p = ln.strip().partition(" *")
        if p.endswith(EXTS):
            listed[os.path.normpath(p)] = h
    current = {rel: artifacts._sha(p) for rel, p in sources(PROJ_DIR).items()}
    if listed != current:
        return False
    stage_outputs()
    m = artifacts.archive(PROJ, "ok", stats=resources(), log=os.path.join(BUILD, "build.log"))
    say(f"adopted the existing build in {BUILD}: its {len(listed)} source files match the repo exactly")
    say(f"archived as {os.path.relpath(m['_dir'])}")
    return True


# ---- board ------------------------------------------------------------------
def newest():
    ok = [m for m in artifacts.list_builds(PROJ) if m.get("status") == "ok"]
    return ok[0] if ok else None


def status_line():
    m = newest()
    if not m:
        return f"{fg(AMBER)}no build archived yet{RESET}"
    probs, warns = artifacts.verify(m)
    when = artifacts.ago(m.get("built_epoch", 0))
    sha = m.get("artifacts", {}).get("sof", {}).get("sha256", "")[:8]
    if probs:
        return f"{fg(ROSE)}newest build unusable: {'; '.join(probs)}{RESET}"
    if warns:
        return f"build {when} · sof {sha} · {fg(AMBER)}sources changed since: build again{RESET}"
    return f"build {when} · sof {sha} · {fg(GREEN)}matches the sources{RESET}"


def program(force=False, dry=False, interactive=False):
    m = newest()
    if not m and adopt():
        m = newest()
    if not m:
        bad("no build of the demo is archived on this PC: run Build first")
        return False
    probs, warns = artifacts.verify(m)
    if probs:
        bad("refusing to program: " + "; ".join(probs))
        return False
    say(f"build {os.path.basename(m['_dir'])}, {artifacts.ago(m.get('built_epoch', 0))}")
    if warns and not force:
        warn("the sources on disk differ from this build, so the board would run logic")
        warn("that does not match your source tree.")
        if not interactive:
            bad("refusing to program: build again, or pass --force")
            return False
        k = ask("b = build now, then program    f = program this build anyway    other = cancel")
        if k == "b":
            return build() and program(dry=dry)
        if k != "f":
            return False
    cmd = [q("quartus_pgm"), "-c", CABLE, "-m", "JTAG", "-o", f"p;{PROJ}.sof"]
    if dry:
        print("    " + subprocess.list2cmdline(cmd) + f"\n    (run in {m['_dir']})")
        return True
    if not detect(quiet=True):
        return False
    say("loading the bitstream into the FPGA's SRAM over JTAG")
    if run(cmd, cwd=m["_dir"]) != 0:
        bad("quartus_pgm failed. Close any open drawing window: it holds the USB-Blaster.")
        bad("If Detect shows no device, the board is unpowered or the cable is out.")
        return False
    good("loaded. It is lost at power-off. A success message is not proof: Check confirms it.")
    return True


def check():
    say("sending the 16 test images over JTAG and comparing every digit and score")
    if run([sys.executable, os.path.join(HOST, "check_board.py"), "JTAG"]) == 0:
        good("board check passed")
        return True
    bad("board check failed (see above)")
    return False


def draw():
    say("drawing app open (port: JTAG). Close its window to come back here.")
    return run([sys.executable, os.path.join(HOST, "draw.py")]) == 0


def detect(quiet=False):
    """jtagconfig exits 0 even when it reports "JTAG chain broken", so judge by its device list."""
    try:
        out = subprocess.run([q("jtagconfig")], capture_output=True, text=True, errors="replace").stdout
    except FileNotFoundError:
        bad(f"jtagconfig not found in {QBIN}")
        return False
    if quiet and re.search(r"^\s+020F10DD\s", out, re.M):
        return True
    print(out.rstrip())
    if re.search(r"^\s+020F10DD\s", out, re.M):
        good("the EP4CE6 is on the chain (IDCODE 020F10DD; Quartus names it 10CL006/10CL010, same die)")
        return True
    if "broken" in out.lower():
        bad("JTAG chain broken: the board is unpowered, or the cable is not on its JTAG header")
    else:
        bad("no EP4CE6 on the chain")
    return False


def go(force=False, interactive=False):
    if not program(force=force, interactive=interactive):
        return False
    if not check():
        bad("not opening the drawing app: the board did not pass its check")
        return False
    return draw()


# ---- the menu ---------------------------------------------------------------
ITEMS = [
    ("go", "Program, check, draw", "load the newest build, run the 16-image check, open the drawing app"),
    ("program", "Program", "load the newest build into the FPGA (SRAM: lost at power-off)"),
    ("check", "Check board", "send the 16 test images over JTAG and compare every score"),
    ("draw", "Draw", "open the drawing app"),
    ("build", "Build", "compile the repo's sources with Quartus 25.1 and archive the result"),
    ("detect", "Detect", "is the board on the JTAG chain?"),
    ("quit", "Quit", ""),
]


def getkey():
    import msvcrt
    ch = msvcrt.getwch()
    if ch in ("\x00", "\xe0"):
        return {"H": "up", "P": "down"}.get(msvcrt.getwch())
    return {"\r": "go", " ": "go", "k": "up", "j": "down", "q": "quit", "\x1b": "quit", "\x03": "quit"}.get(ch.lower())


def ask(prompt):
    import msvcrt
    print(f"\n  {fg(ICE)}{prompt}{RESET}")
    return msvcrt.getwch().lower()


def frame(sel):
    out = ["\033[2J\033[H",
           f"  {fg(VIOLET)}▚{RESET} {BOLD}{fg(ICE)}LYCOCHIP DEMO{RESET}  {fg(MUTED)}EP4CE6 · USB-Blaster · Quartus 25.1std{RESET}",
           f"  {fg(DEEP)}{'┈' * 66}{RESET}",
           f"  {status_line()}", ""]
    for i, (_, name, hint) in enumerate(ITEMS):
        if i == sel:
            out.append(f"  {fg(CYAN)}▸ {BOLD}{name:<22}{RESET}{fg(PAPER)}{hint}{RESET}")
        else:
            out.append(f"    {fg(MUTED)}{name:<22}{RESET}{fg(DEEP)}{hint}{RESET}")
    out += ["", f"  {fg(MUTED)}↑↓ or j k to choose · Enter to run · q to quit{RESET}"]
    return "\n".join(out)


def menu():
    sel = 0
    while True:
        sys.stdout.write("\033[?25l" + frame(sel))
        sys.stdout.flush()
        k = getkey()
        if k == "up":
            sel = (sel - 1) % len(ITEMS)
        elif k == "down":
            sel = (sel + 1) % len(ITEMS)
        elif k == "quit" or (k == "go" and ITEMS[sel][0] == "quit"):
            break
        elif k == "go":
            sys.stdout.write("\033[?25h\033[2J\033[H")
            name = ITEMS[sel][0]
            print(f"  {BOLD}{fg(ICE)}{ITEMS[sel][1]}{RESET}\n")
            try:
                {"go": lambda: go(interactive=True), "program": lambda: program(interactive=True), "check": check,
                 "draw": draw, "build": build, "detect": detect}[name]()
            except KeyboardInterrupt:
                bad("interrupted")
            print(f"\n  {fg(MUTED)}press any key for the menu{RESET}")
            getkey()
    sys.stdout.write("\033[?25h\033[2J\033[H" + RESET)


def console():
    """Turn on ANSI colours and UTF-8 output in the Windows console."""
    if os.name == "nt":
        import ctypes
        k = ctypes.windll.kernel32
        h, mode = k.GetStdHandle(-11), ctypes.c_uint32()
        if k.GetConsoleMode(h, ctypes.byref(mode)):
            k.SetConsoleMode(h, mode.value | 0x0004)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def main():
    console()
    a = sys.argv[1:]
    force, dry = "--force" in a, "--dry-run" in a
    a = [x for x in a if not x.startswith("--")]
    if not a:
        if os.name != "nt" or not sys.stdin.isatty():
            print(__doc__)
            return 2
        menu()
        return 0
    acts = {"go": lambda: go(force=force), "program": lambda: program(force=force, dry=dry),
            "check": check, "draw": draw, "build": build, "detect": detect,
            "status": lambda: print(status_line()) or True}
    if a[0] not in acts:
        print(__doc__)
        return 2
    return 0 if acts[a[0]]() else 1


if __name__ == "__main__":
    sys.exit(main())
