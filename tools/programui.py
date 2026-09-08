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
                   PAPER, AMBER, ROSE, GREEN, bar, rule, clip, pad)

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

    rows = []
    for m in builds[:9]:
        st    = m.get("status")
        stats = m.get("stats") or {}
        le    = stats.get("le")
        le_s  = f"{le[0]:>5} LE" if isinstance(le, (list, tuple)) else ("failed" if st != "ok" else "")
        sl    = stats.get("slack")
        sl_s  = f"{sl:+.2f}ns" if isinstance(sl, (int, float)) else ""
        git   = m.get("git") or {}
        rows.append((m.get("project", "?"),
                     artifacts.ago(m.get("built_epoch", 0)),
                     (fg(GREEN) + "\u2713") if st == "ok" else (fg(ROSE) + "\u2717"),
                     le_s, sl_s,
                     git.get("commit", "") + ("+" if git.get("dirty") else "")))

    if rows:
        # Sized from the data rather than hardcoded, so a long project name
        # cannot shove the rest of the row past the panel edge. The tail
        # columns are dropped whole before the name is clipped -- half a
        # resource number would be worse than none.
        nw, ww, lw, sw, gw = (max(len(r[i]) for r in rows) for i in (0, 1, 3, 4, 5))
        budget = IW - 2                      # "  " + mark + " " already spent 2

        def total():
            return (nw + 1 + ww + 1 + 1        # name, when, badge
                    + sum(w + 1 for w in (lw, sw, gw) if w))

        for shed in ("gw", "sw", "lw"):        # git hash, then slack, then LE
            if total() <= budget:
                break
            if shed == "gw":   gw = 0
            elif shed == "sw": sw = 0
            else:              lw = 0
        if total() > budget:                   # nothing left to drop: clip the name
            nw = max(6, nw - (total() - budget))

    for i, (pr, when, badge, le_s, sl_s, g) in enumerate(rows):
        cur   = i == sel
        mark  = f"{fg(PINK)}\u25b8{RESET}" if cur else " "
        namec = fg(ICE) + BOLD if cur else fg(PAPER)
        extra = ""
        if lw: extra += pad(le_s, lw) + " "
        if sw: extra += pad(sl_s, sw) + " "
        if gw: extra += clip(g, gw)
        a(f"  {mark} {namec}{pad(pr, nw)}{RESET} "
          f"{fg(MUTED) if not cur else fg(PAPER)}{pad(when, ww)}{RESET} "
          f"{badge}{RESET} {fg(MUTED)}{extra}{RESET}")
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
