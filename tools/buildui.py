#!/usr/bin/env python3
"""
LycoChip remote build monitor.

Drives the Quartus build on lyco-server and renders live server telemetry
(per-core CPU, history graph, memory, package temperature) plus pipeline
progress. Colours only -- no background fill -- so terminal transparency
shows through.
"""
import os, re, sys, time, shutil, threading, subprocess
from collections import deque

REMOTE = "lyco"
RDIR   = "lycochip-build"
QBIN   = "$HOME/intelFPGA_lite/20.1/quartus/bin"

from theme import (fg, RESET, BOLD, DIM, CYAN, ICE, PINK, VIOLET, DEEP,
                   MUTED, PAPER, AMBER, ROSE, GREEN, BLOCKS,
                   lerp, heat, bar, graph)

# ---- remote telemetry ----------------------------------------------------
STAT_CMD = r"""
CT=""; for h in /sys/class/hwmon/hwmon*; do
  [ "$(cat $h/name 2>/dev/null)" = coretemp ] && CT=$h && break; done
while :; do
  echo "@@S"
  grep '^cpu' /proc/stat
  grep -E '^(MemTotal|MemAvailable):' /proc/meminfo
  echo "T $(cat $CT/temp1_input 2>/dev/null || echo 0)"
  echo "F $(cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq 2>/dev/null | paste -sd' ' -)"
  echo "@@E"
  sleep 0.4
done
"""

class Telemetry(threading.Thread):
    daemon = True
    def __init__(self):
        super().__init__()
        self.lock  = threading.Lock()
        self.cores, self.total = [], 0.0
        self.mem_used = self.mem_total = 0.0
        self.temp, self.freq = 0.0, 0.0
        self.hist  = deque(maxlen=240)
        self._prev = {}
        self.alive = True

    def run(self):
        p = subprocess.Popen(["ssh", REMOTE, STAT_CMD], stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, text=True, bufsize=1)
        block = []
        for line in p.stdout:
            line = line.strip()
            if line == "@@S":
                block = []
            elif line == "@@E":
                self._parse(block)
            else:
                block.append(line)
        self.alive = False

    def _parse(self, block):
        cores, tot, mt, ma, tmp, frq = [], None, 0, 0, 0.0, 0.0
        for ln in block:
            if ln.startswith("cpu"):
                f = ln.split()
                if len(f) < 5: continue
                key  = f[0]
                vals = [int(x) for x in f[1:]]
                idle = vals[3] + (vals[4] if len(vals) > 4 else 0)
                busy = sum(vals) - idle
                pi, pb = self._prev.get(key, (0, 0))
                di, db = idle - pi, busy - pb
                self._prev[key] = (idle, busy)
                pct = 0.0 if (di + db) <= 0 else 100.0 * db / (di + db)
                if key == "cpu": tot = pct
                else: cores.append(pct)
            elif ln.startswith("MemTotal:"):     mt = int(ln.split()[1])
            elif ln.startswith("MemAvailable:"): ma = int(ln.split()[1])
            elif ln.startswith("T "):
                try: tmp = int(ln.split()[1]) / 1000.0
                except Exception: pass
            elif ln.startswith("F "):
                nums = [int(x) for x in ln.split()[1:] if x.isdigit()]
                if nums: frq = sum(nums) / len(nums) / 1e6
        with self.lock:
            if cores: self.cores = cores
            if tot is not None:
                self.total = tot
                self.hist.append(tot)
            if mt:
                self.mem_total = mt / 1048576.0
                self.mem_used  = (mt - ma) / 1048576.0
            if tmp: self.temp = tmp
            if frq: self.freq = frq

# ---- build pipeline ------------------------------------------------------
PHASES = [
    ("SYNC",      None),
    ("SYNTHESIS", "Analysis & Synthesis was successful"),
    ("FITTER",    "Fitter was successful"),
    ("ASSEMBLER", "Assembler was successful"),
    ("TIMING",    "Timing Analyzer was successful"),
    ("SVF",       "@@CPF_DONE"),
    ("FETCH",     None),
]
STARTS = {
    "Running Quartus Prime Analysis & Synthesis": 1,
    "Running Quartus Prime Fitter":               2,
    "Running Quartus Prime Assembler":            3,
    "Running Quartus Prime Timing Analyzer":      4,
    "@@CPF":                                      5,
}

class Build(threading.Thread):
    daemon = True
    def __init__(self, proj):
        super().__init__()
        self.proj    = proj
        self.cur     = 0
        self.done    = [None] * len(PHASES)
        self.t0      = [None] * len(PHASES)
        self.errors  = []
        self.stats   = {}
        self.failed  = False
        self.finished= False
        self.t0[0]   = time.time()

    def _mark(self, i):
        if self.cur < len(PHASES) and self.t0[self.cur] and self.done[self.cur] is None:
            self.done[self.cur] = time.time() - self.t0[self.cur]
        self.cur = i
        if self.t0[i] is None: self.t0[i] = time.time()

    def run(self):
        try:
            subprocess.run(["ssh", REMOTE, f"mkdir -p ~/{RDIR}"], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["rsync", "-az", "--delete",
                            "--include=rtl/***", "--include=*.qsf", "--include=*.sdc",
                            "--include=*.qpf", "--exclude=*", "./", f"{REMOTE}:{RDIR}/"],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._mark(1)

            cmd = (f"cd ~/{RDIR} && export PATH={QBIN}:$PATH && "
                   f"quartus_sh --flow compile {self.proj}; rc=$?; "
                   f"echo '@@CPF'; "
                   f"quartus_cpf -c -q 12.0MHz -g 3.3 -n p {self.proj}.sof {self.proj}.svf >/dev/null 2>&1; "
                   f"echo '@@CPF_DONE'; exit $rc")
            p = subprocess.Popen(["ssh", REMOTE, cmd], stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, text=True, bufsize=1)
            for raw in p.stdout:
                ln = raw.rstrip()
                for key, idx in STARTS.items():
                    if key in ln: self._mark(idx)
                for i, (_, marker) in enumerate(PHASES):
                    if marker and marker in ln and self.done[i] is None and self.t0[i]:
                        self.done[i] = time.time() - self.t0[i]
                if re.search(r"^\s*Error", ln) or "Error (" in ln:
                    if len(self.errors) < 6: self.errors.append(ln.strip()[:150])
                m = re.search(r"Total logic elements\s*:\s*([\d,]+)\s*/\s*([\d,]+)", ln)
                if m: self.stats["le"] = f"{m.group(1)} / {m.group(2)}"
            rc = p.wait()
            self.failed = rc != 0 or bool(self.errors)
            self._mark(6)
            if not self.failed:
                os.makedirs("output_files", exist_ok=True)
                for ext in ("sof", "rbf", "svf"):
                    subprocess.run(["rsync", "-az", f"{REMOTE}:{RDIR}/{self.proj}.{ext}",
                                    "output_files/"], stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
                self._reports()
                self.done[6] = time.time() - self.t0[6]

        except Exception as e:
            self.failed = True
            self.errors.append(str(e)[:150])
        self.finished = True

    def _reports(self):
        """Resource + timing numbers live in the .summary files, not stdout."""
        try:
            r = subprocess.run(["ssh", REMOTE,
                    f"cd ~/{RDIR} && cat {self.proj}.fit.summary {self.proj}.sta.summary 2>/dev/null"],
                    capture_output=True, text=True, timeout=20)
            txt = r.stdout
            m = re.search(r"Total logic elements\s*:\s*([\d,]+)\s*/\s*([\d,]+)", txt)
            if m: self.stats["le"] = (m.group(1).strip(), m.group(2).strip())
            m = re.search(r"Total registers\s*:\s*([\d,]+)", txt)
            if m: self.stats["reg"] = m.group(1).strip()
            m = re.search(r"Total pins\s*:\s*([\d,]+)\s*/\s*([\d,]+)", txt)
            if m: self.stats["pin"] = (m.group(1).strip(), m.group(2).strip())
            slacks = []
            blocks = txt.split("Type  :")
            for b in blocks:
                if "Setup" in b.split("\n")[0]:
                    mm = re.search(r"Slack\s*:\s*(-?[\d.]+)", b)
                    if mm: slacks.append(float(mm.group(1)))
            if slacks: self.stats["slack"] = min(slacks)
        except Exception:
            pass

# ---- render --------------------------------------------------------------
SPIN = "◜◝◞◟"

def render(tel, bld, proj, start, width):
    W  = max(58, min(width - 2, 84))
    IW = W - 4
    L  = []
    a  = lambda s="": L.append(s)

    with tel.lock:
        cores  = list(tel.cores); total = tel.total
        mu, mt = tel.mem_used, tel.mem_total
        temp, freq, hist = tel.temp, tel.freq, list(tel.hist)

    el   = time.time() - start
    spin = SPIN[int(el * 8) % 4]

    a(fg(CYAN) + "╭" + "─" * (W - 2) + "╮" + RESET)
    title = f"{fg(PINK)}◆{RESET} {fg(ICE)}{BOLD}LYCOCHIP{RESET} {fg(DEEP)}░▒▓{RESET} {fg(PAPER)}{proj}{RESET}"
    right = f"{fg(MUTED)}EP4CE6E22C8{RESET}"
    pad   = W - 4 - (2 + 8 + 4 + len(proj) + 1) - 11
    a(fg(CYAN) + "│ " + RESET + title + " " * max(1, pad) + right + fg(CYAN) + " │" + RESET)
    a(fg(CYAN) + "╰" + "─" * (W - 2) + "╯" + RESET)
    a(f"  {fg(DEEP)}lyco-server · i5-6300U · {len(cores) or 4} threads{RESET}")
    a()

    a(f"  {fg(VIOLET)}▚{RESET} {fg(ICE)}CPU{RESET} {fg(DEEP)}{'┈' * (IW - 6)}{RESET}")
    gw = IW - 10
    a(f"   {bar(total, gw)} {fg(heat(total))}{total:5.1f}%{RESET}")
    for row in graph(hist, gw, rows=3):
        a("   " + row)
    a()
    half = (IW - 6) // 2
    for i in range(0, len(cores), 2):
        seg = ""
        for j in (i, i + 1):
            if j < len(cores):
                seg += f"  {fg(MUTED)}c{j}{RESET} {bar(cores[j], half - 12)} {fg(heat(cores[j]))}{cores[j]:4.0f}%{RESET}"
        a(" " + seg)
    a()

    a(f"  {fg(VIOLET)}▚{RESET} {fg(ICE)}SYSTEM{RESET} {fg(DEEP)}{'┈' * (IW - 9)}{RESET}")
    mp = (mu / mt * 100) if mt else 0
    a(f"   {fg(MUTED)}MEM {RESET}{bar(mp, gw - 6)} {fg(heat(mp))}{mu:4.2f}{RESET}{fg(DEEP)}/{mt:.2f} GiB{RESET}")
    tp = max(0.0, min(100.0, (temp - 30) / 60 * 100))
    tc = GREEN if temp < 60 else (AMBER if temp < 80 else ROSE)
    a(f"   {fg(MUTED)}TMP {RESET}{bar(tp, gw - 6, tc)} {fg(tc)}{temp:4.1f}°C{RESET}")
    a(f"   {fg(MUTED)}CLK {RESET}{fg(PAPER)}{freq:.2f} GHz{RESET}")
    a()

    a(f"  {fg(VIOLET)}▚{RESET} {fg(ICE)}PIPELINE{RESET} {fg(DEEP)}{'┈' * (IW - 11)}{RESET}")
    for i, (name, _) in enumerate(PHASES):
        if bld.done[i] is not None:
            a(f"   {fg(GREEN)}✓{RESET} {fg(PAPER)}{name:<11}{RESET}{fg(DEEP)}{bld.done[i]:6.1f}s{RESET}")
        elif i == bld.cur and not bld.finished:
            dots = "▪" * (int(el * 3) % 4) + "▫" * (3 - int(el * 3) % 4)
            a(f"   {fg(PINK)}{spin}{RESET} {fg(ICE)}{BOLD}{name:<11}{RESET}{fg(PINK)}{dots}{RESET}")
        else:
            a(f"   {fg(DEEP)}▫ {name}{RESET}")
    a()

    if bld.finished:
        if bld.failed:
            a(f"  {fg(ROSE)}{BOLD}✗ BUILD FAILED{RESET}  {fg(DEEP)}{el:.1f}s{RESET}")
            for e in bld.errors[:4]:
                a(f"    {fg(ROSE)}{e[:W-8]}{RESET}")
        else:
            a(f"  {fg(GREEN)}{BOLD}✓ BUILD OK{RESET}  {fg(DEEP)}{el:.1f}s{RESET}")
            st = bld.stats
            if "le" in st:
                used, tot = st["le"]
                try: pc = 100.0 * int(used.replace(",", "")) / int(tot.replace(",", ""))
                except Exception: pc = 0.0
                a(f"   {fg(MUTED)}LOGIC {RESET}{bar(pc, 18)} {fg(PAPER)}{used}{fg(DEEP)}/{tot}{RESET}"
                  f"  {fg(MUTED)}REG {fg(PAPER)}{st.get('reg','?')}{RESET}")
            if "pin" in st:
                used, tot = st["pin"]
                try: pc = 100.0 * int(used) / int(tot)
                except Exception: pc = 0.0
                a(f"   {fg(MUTED)}PINS  {RESET}{bar(pc, 18)} {fg(PAPER)}{used}{fg(DEEP)}/{tot}{RESET}")
            if "slack" in st:
                sl = st["slack"]
                sc = GREEN if sl > 0 else ROSE
                verdict = "MET" if sl > 0 else "VIOLATED"
                a(f"   {fg(MUTED)}TIMING{RESET} {fg(sc)}{verdict}{RESET} "
                  f"{fg(DEEP)}worst setup slack{RESET} {fg(sc)}{sl:+.3f} ns{RESET}")
            a(f"   {fg(MUTED)}→ output_files/{proj}.{{sof,rbf,svf}}   run {fg(ICE)}./program.sh{RESET}")
    else:
        a(f"  {fg(PINK)}⟩⟩{RESET} {fg(PAPER)}{int(el//60):02d}:{int(el%60):02d}{RESET} {fg(DEEP)}elapsed{RESET}")
    return L

def main():
    proj  = sys.argv[1] if len(sys.argv) > 1 else "blink"
    tel   = Telemetry(); tel.start()
    bld   = Build(proj); bld.start()
    start = time.time()
    prev  = 0
    sys.stdout.write("\033[?25l")
    try:
        while True:
            w = shutil.get_terminal_size((80, 24)).columns
            lines = render(tel, bld, proj, start, w)
            out = ""
            if prev: out += f"\033[{prev}A"
            for ln in lines:
                out += "\033[2K" + ln + "\n"
            sys.stdout.write(out); sys.stdout.flush()
            prev = len(lines)
            if bld.finished:
                time.sleep(0.4)
                lines = render(tel, bld, proj, start, w)
                out = f"\033[{prev}A"
                for ln in lines: out += "\033[2K" + ln + "\n"
                sys.stdout.write(out); sys.stdout.flush()
                break
            time.sleep(0.12)
    finally:
        sys.stdout.write("\033[?25h" + RESET); sys.stdout.flush()
    sys.exit(1 if bld.failed else 0)

if __name__ == "__main__":
    main()
