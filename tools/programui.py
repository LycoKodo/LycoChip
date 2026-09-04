#!/usr/bin/env python3
"""
LycoChip programmer -- browse archived builds and flash one to the board.

  ^ v / j k   choose a build          < > / h l   choose SRAM or FLASH
  enter       program                 q / esc     quit

Every entry comes from builds/, so you always know exactly which sources the
bitstream you are flashing was built from.
"""
import os, re, subprocess, sys, threading, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artifacts
from theme import (fg, RESET, BOLD, CYAN, ICE, PINK, VIOLET, DEEP, MUTED,
                   PAPER, AMBER, ROSE, GREEN, bar, rule)

CABLE = "usb-blaster"
PART  = "ep4ce622"
SPIN  = "◜◝◞◟"

TARGETS = [
    ("SRAM",  "volatile · ~2s",     "svf"),
    ("FLASH", "permanent · ~3min",  "rbf"),
]


from tui import Raw, getkey, paint


# ---- programming ---------------------------------------------------------
class Programmer(threading.Thread):
    daemon = True

    def __init__(self, build, target):
        super().__init__()
        self.build, self.target = build, target
        self.phase, self.pct = "starting", 0.0
        self.lines, self.done, self.ok = [], False, False
        self.proc = None

    def run(self):
        proj = self.build["project"]
        name, _, ext = TARGETS[self.target]
        path = os.path.join(self.build["_dir"], f"{proj}.{ext}")
        if not os.path.exists(path):
            self.lines.append(f"missing artifact: {path}")
            self.done = True
            return
        if name == "SRAM":
            cmd = ["openFPGALoader", "-c", CABLE, "--file-type", "svf", path]
        else:
            cmd = ["openFPGALoader", "-c", CABLE, "-f", "--fpga-part", PART,
                   "--verify", path]
        try:
            self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT, text=True,
                                         bufsize=0)
            buf = ""
            while True:
                c = self.proc.stdout.read(1)
                if not c:
                    break
                if c in "\r\n":
                    self._line(buf); buf = ""
                else:
                    buf += c
            if buf:
                self._line(buf)
            self.ok = self.proc.wait() == 0
        except FileNotFoundError:
            self.lines.append("openFPGALoader not found -- brew install openfpgaloader")
        except Exception as e:
            self.lines.append(str(e)[:120])
        self.done = True

    def _line(self, ln):
        ln = ln.strip()
        if not ln:
            return
        m = re.search(r"([\d.]+)\s*%", ln)
        if m:
            self.pct = float(m.group(1))
            head = ln.split(":")[0].strip()
            if head and len(head) < 24:
                self.phase = head
            return
        if "end of SVF file" in ln:
            self.phase, self.pct = "configured", 100.0
        self.lines.append(ln[:110])
        if len(self.lines) > 8:
            self.lines.pop(0)


# ---- render --------------------------------------------------------------
def draw(builds, sel, target, prog, note, width):
    W  = max(58, min(width - 2, 84))
    IW = W - 4
    L  = []
    a  = L.append

    a(fg(CYAN) + "╭" + "─" * (W - 2) + "╮" + RESET)
    head = f"{fg(PINK)}◆{RESET} {fg(ICE)}{BOLD}LYCOCHIP{RESET} {fg(DEEP)}░▒▓{RESET} {fg(PAPER)}PROGRAM{RESET}"
    a(fg(CYAN) + "│ " + RESET + head + " " * max(1, W - 24 - 13)
      + fg(MUTED) + "EP4CE6E22C8" + fg(CYAN) + " │" + RESET)
    a(fg(CYAN) + "╰" + "─" * (W - 2) + "╯" + RESET)
    a("")

    a(rule("BUILDS", IW))
    if not builds:
        a(f"   {fg(ROSE)}no builds archived yet -- run ./build.sh first{RESET}")
    for i, m in enumerate(builds[:9]):
        cur  = i == sel
        st   = m.get("status")
        badge = (fg(GREEN) + "✓") if st == "ok" else (fg(ROSE) + "✗")
        stats = m.get("stats") or {}
        le    = stats.get("le")
        le_s  = f"{le[0]:>5} LE" if isinstance(le, (list, tuple)) else ("failed" if st != "ok" else "")
        sl    = stats.get("slack")
        sl_s  = f"{sl:+.2f}ns" if isinstance(sl, (int, float)) else ""
        g     = (m.get("git") or {}).get("commit", "")
        dirty = "+" if (m.get("git") or {}).get("dirty") else ""
        when  = artifacts.ago(m.get("built_epoch", 0))
        mark  = f"{fg(PINK)}▸{RESET}" if cur else " "
        namec = fg(ICE) + BOLD if cur else fg(PAPER)
        a(f"  {mark} {namec}{m.get('project','?'):<9}{RESET}"
          f"{fg(MUTED) if not cur else fg(PAPER)}{when:<17}{RESET}"
          f"{badge}{RESET} {fg(MUTED)}{le_s:<9}{sl_s:<10}{g}{dirty}{RESET}")
    a("")

    a(rule("TARGET", IW))
    seg = "  "
    for i, (name, desc, _) in enumerate(TARGETS):
        if i == target:
            seg += f" {fg(PINK)}▸{RESET} {fg(ICE)}{BOLD}{name}{RESET} {fg(MUTED)}{desc}{RESET}   "
        else:
            seg += f"   {fg(DEEP)}{name} {desc}{RESET}   "
    a(seg)
    a("")

    if note:
        a(f"  {fg(AMBER)}⚠ {note}{RESET}")
        a("")

    if prog:
        a(rule("PROGRAMMING", IW))
        spin = SPIN[int(time.time() * 8) % 4]
        icon = spin if not prog.done else ("✓" if prog.ok else "✗")
        col  = PINK if not prog.done else (GREEN if prog.ok else ROSE)
        a(f"   {fg(col)}{icon}{RESET} {fg(PAPER)}{prog.phase}{RESET}")
        a(f"   {bar(prog.pct, IW - 10)} {fg(PAPER)}{prog.pct:5.1f}%{RESET}")
        for ln in prog.lines[-4:]:
            a(f"     {fg(DEEP)}{ln[:W-8]}{RESET}")
        if prog.done:
            a("")
            if prog.ok:
                a(f"  {fg(GREEN)}{BOLD}✓ PROGRAMMED{RESET}  "
                  f"{fg(MUTED)}{'power-cycle to confirm it boots from flash' if TARGETS[target][0]=='FLASH' else 'running now (lost on power-off)'}{RESET}")
            else:
                a(f"  {fg(ROSE)}{BOLD}✗ FAILED{RESET}  {fg(MUTED)}board powered? cable seated?{RESET}")
        a("")

    keys = [("↑↓", "build"), ("←→", "target"), ("⏎", "program"), ("q", "quit")]
    a("  " + "   ".join(f"{fg(PINK)}{k}{RESET} {fg(MUTED)}{v}{RESET}" for k, v in keys))
    return L


def main():
    proj = None
    for a_ in sys.argv[1:]:
        if not a_.startswith("-"):
            proj = a_
    builds = artifacts.list_builds(proj)
    if not builds:
        print("no archived builds -- run ./build.sh first")
        sys.exit(1)

    sel, target, prog, prev = 0, 0, None, 0
    import shutil
    with Raw():
        while True:
            m = builds[sel]
            note = None
            if m.get("status") == "ok":
                probs, warns = artifacts.verify(m)
                if probs:  note = probs[0]
                elif warns: note = warns[0]
            else:
                note = "this build failed -- it has no artifacts to program"

            w = shutil.get_terminal_size((80, 24)).columns
            lines = draw(builds, sel, target, prog, note, w)
            prev = paint(lines, prev)

            try:
                k = getkey()
            except KeyboardInterrupt:
                k = "quit"
            if k == "quit":
                if prog and not prog.done and prog.proc:
                    prog.proc.terminate()
                break
            if prog and not prog.done:
                continue
            if   k == "up":    sel = (sel - 1) % len(builds); prog = None
            elif k == "down":  sel = (sel + 1) % len(builds); prog = None
            elif k == "left":  target = (target - 1) % len(TARGETS); prog = None
            elif k == "right": target = (target + 1) % len(TARGETS); prog = None
            elif k == "go":
                if m.get("status") == "ok":
                    prog = Programmer(m, target); prog.start()
    print()


if __name__ == "__main__":
    main()
