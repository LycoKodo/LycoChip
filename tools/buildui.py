#!/usr/bin/env python3
"""
LycoChip remote build monitor.

Drives the Quartus build on lyco-server and renders live server telemetry
(per-core CPU, history graph, memory, package temperature) plus pipeline
progress. Colours only -- no background fill -- so terminal transparency
shows through.
"""
import os, re, sys, time, shutil, tempfile, threading, subprocess
from collections import deque
import textwrap

import artifacts

REMOTE = "lyco"
RDIR   = "lycochip-build"
QBIN   = "$HOME/intelFPGA_lite/20.1/quartus/bin"

# Quartus runs in one of three places, fastest first:
#   local   Rosetta container on this Mac (~22 s) -- also works with no network
#   remote  lyco-server over ssh (~33 s)
#   vm      the emulated Lima VM (~115 s), fallback only
# See build.sh for the full reasoning. BACKEND=local|remote|vm forces one.
DIMAGE = "lycochip-quartus:centos7"
QTREE  = os.path.expanduser("~/intelFPGA_lite/20.1")
DBUILD = os.path.expanduser("~/.lycochip-build/projects")
VM     = "quartus"
VMQBIN = "$HOME/intelFPGA_lite/20.1/quartus/bin"
VMDIR  = "$HOME/lycochip-build"
HERE   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SRCSYNC = ["--include=*/", "--include=*.v", "--include=*.sv", "--include=*.vhd",
           "--include=*.qsf", "--include=*.qpf", "--include=*.sdc",
           "--include=*.tcl", "--exclude=*"]


def _ok(*argv, timeout=10):
    try:
        return subprocess.run(argv, timeout=timeout, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL).returncode == 0
    except Exception:
        return False


# The three places Quartus can run. Order is the order they are offered.
BACKENDS = [
    ("local",  "Rosetta",     "this Mac, x86-64 translated",  "~22 s"),
    ("remote", "lyco-server", "over ssh, native x86-64",      "~33 s"),
    ("vm",     "QEMU",        "this Mac, fully emulated",     "~115 s"),
]

# Friendly names, so BACKEND=rosetta and BACKEND=qemu work too.
ALIAS = {"rosetta": "local", "docker": "local",
         "qemu": "vm", "lima": "vm",
         "lyco": "remote", "server": "remote"}


IMGTAR = os.path.expanduser("~/.lycochip-build/quartus-image.tar")


def _have_image():
    try:
        r = subprocess.run(["docker", "images", "-q", DIMAGE],
                           capture_output=True, text=True, timeout=15)
        return bool(r.stdout.strip())
    except Exception:
        return False


def _daemon_up():
    return _ok("docker", "info", timeout=15)


def _have_colima():
    return shutil.which("colima") is not None


def docker_ready():
    """Is the Rosetta backend usable right now? Never starts anything.

    Kept side-effect free (beyond a fast local image load) because the picker
    calls it to draw a menu -- waiting 40 s for a VM to boot while rendering a
    list would be worse than the problem the picker was added to solve.

    The image has gone missing once already, and rebuilding it needs the
    network to pull centos:7 -- exactly what is absent when this backend
    matters most. So a saved copy is reloaded instead, offline.
    """
    if not os.path.isdir(QTREE) or not _daemon_up():
        return False
    if _have_image():
        return True
    if os.path.exists(IMGTAR):
        _ok("docker", "load", "-i", IMGTAR, timeout=300)
        return _have_image()
    return False


def docker_bring_up():
    """Start a container runtime if none is running. Called after choosing.

    colima is preferred over Docker Desktop: it is a plain CLI VM, so nothing
    has to be left running in the menu bar, and it supports Rosetta through
    Apple's virtualisation framework just as Desktop does.
    """
    if _daemon_up():
        return docker_ready()
    if _have_colima():
        print(f"{fg(MUTED)}starting colima (no Docker Desktop needed; ~40 s){RESET}")
        _ok("colima", "start", timeout=300)
    elif sys.platform == "darwin":
        print(f"{fg(MUTED)}starting Docker Desktop{RESET}")
        _ok("open", "-a", "Docker")
        for _ in range(60):
            if _daemon_up():
                break
            time.sleep(2)
    return docker_ready()


def vm_exists():
    try:
        r = subprocess.run(["limactl", "list", VM, "--format", "{{.Status}}"],
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip()
    except Exception:
        return ""


def backend_status(bid):
    """(usable, note) for the picker. Deliberately does no network probing --
    waiting on an ssh timeout just to draw a menu is what this page replaces."""
    if bid == "local":
        if docker_ready():
            return (True, "ready")
        if not _daemon_up():
            # Usable, just not started yet -- selecting it starts it.
            if _have_colima():
                return (True, "colima stopped, will start (~40 s)")
            return (False, "start Docker Desktop, or: brew install colima")
        return (False, "image missing -- see tools/quartus-docker")
    if bid == "vm":
        st = vm_exists()
        if not st:
            return (False, "not created")
        return (True, "ready" if st == "Running" else f"{st.lower()}, will start (~7 min)")
    return (True, "needs the network")


def auto_backend():
    """Used when there is no terminal to ask at. Fastest first."""
    if docker_ready():
        return "local"
    if _ok("ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=3", REMOTE, "true", timeout=6):
        return "remote"
    return "vm" if vm_exists() else "none"


_env = os.environ.get("BACKEND", "").strip().lower()
BACKEND = ALIAS.get(_env, _env if _env in ("local", "remote", "vm") else "")


def set_backend(bid):
    global BACKEND, _BK
    BACKEND = bid
    _BK = None


def qsh(script, proj=None, ctl=True):
    """Argv that runs a bash script on the active Quartus backend."""
    if BACKEND == "remote":
        pre = [] if ctl else ["-o", "ControlMaster=no", "-o", "ControlPath=none"]
        return ["ssh"] + pre + [REMOTE, script]
    if BACKEND == "vm":
        return ["limactl", "shell", VM, "--", "bash", "-c", script]
    argv = ["docker", "run", "--rm", "--platform", "linux/amd64",
            "-e", "LANG=C", "-e", "LC_ALL=C",
            "-v", f"{QTREE}:/opt/intelFPGA_lite/20.1:ro"]
    if proj:
        argv += ["-v", f"{DBUILD}/{proj}:/work", "-w", "/work"]
    argv += [DIMAGE, "bash", "-c", script]
    return argv


def qcd(proj):
    """Prefix that puts a command in the project dir with Quartus on PATH.

    The container already starts in /work with PATH set, so it needs none.
    """
    if BACKEND == "local":
        return ""
    root = f"~/{RDIR}/projects" if BACKEND == "remote" else f"{VMDIR}/projects"
    path = QBIN if BACKEND == "remote" else VMQBIN
    return f"cd {root}/{proj} && export PATH={path}:$PATH && "


_BK = None


def backend_info():
    """Host label, CPU and thread count of whatever is actually building.

    Read from the backend, never hardcoded: this UI drives three different
    machines now, and showing the server's silicon while building elsewhere
    is the kind of quiet lie Article IV exists to stop.
    """
    global _BK
    if _BK is None:
        host = {"remote": "lyco-server",
                "local":  "this Mac · Rosetta",
                "vm":     "local VM (emulated)"}.get(BACKEND, BACKEND)
        cpu, nthr = "unknown CPU", ""
        try:
            r = subprocess.run(
                qsh("grep -m1 '^model name' /proc/cpuinfo | cut -d: -f2-; nproc"),
                capture_output=True, text=True, timeout=30)
            out = [l.strip() for l in r.stdout.splitlines() if l.strip()]
            if out:
                cpu = re.sub(r"\s+", " ", out[0])
            if len(out) > 1:
                nthr = out[1]
        except Exception:
            pass
        _BK = (host, cpu, nthr)
    return _BK


from theme import (fg, RESET, BOLD, DIM, CYAN, ICE, PINK, VIOLET, DEEP,
                   MUTED, PAPER, AMBER, ROSE, GREEN, BLOCKS,
                   lerp, heat, bar, graph, rule, clip, pad)
from tui import Raw, getkey, paint

# ---- remote telemetry ----------------------------------------------------
STAT_CMD = r"""
CT=""; for h in /sys/class/hwmon/hwmon*; do
  [ "$(cat $h/name 2>/dev/null)" = coretemp ] && CT=$h && break; done
n=0
while [ $n -lt 4500 ]; do
  n=$((n+1))
  { echo "@@S"
    grep '^cpu' /proc/stat
    grep -E '^(MemTotal|MemAvailable):' /proc/meminfo
    echo "T $(cat $CT/temp1_input 2>/dev/null || echo 0)"
    echo "F $(cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq 2>/dev/null | paste -sd' ' -)"
    echo "@@E"; } || exit 0
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
        self.proc  = None

    def run(self):
        p = subprocess.Popen(
            qsh(STAT_CMD, ctl=False),
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.proc = p
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

    def stop(self):
        """Daemon threads do not reap child processes; kill the ssh explicitly."""
        p = self.proc
        if p and p.poll() is None:
            for finish in (p.terminate, p.kill):
                try:
                    finish(); p.wait(timeout=2); break
                except Exception:
                    continue

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
        self.logpath = os.path.join(tempfile.gettempdir(),
                                    f"lycochip-{proj}-{os.getpid()}.log")
        self.stats   = {}
        self.failed  = False
        self.finished= False
        self.archived= None
        self.t0[0]   = time.time()

    def _mark(self, i):
        if self.cur < len(PHASES) and self.t0[self.cur] and self.done[self.cur] is None:
            self.done[self.cur] = time.time() - self.t0[self.cur]
        self.cur = i
        if self.t0[i] is None: self.t0[i] = time.time()

    def run(self):
        try:
            if BACKEND == "remote":
                subprocess.run(["ssh", REMOTE, f"mkdir -p ~/{RDIR}/projects"], check=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["rsync", "-az", "--delete"] + SRCSYNC +
                               ["projects/", f"{REMOTE}:{RDIR}/projects/"],
                               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif BACKEND == "local":
                # Build in a scratch copy outside the repo: Quartus rewrites the
                # .qsf and drops db/ beside it, which would move the source hash
                # out from under an already-archived build.
                os.makedirs(f"{DBUILD}/{self.proj}", exist_ok=True)
                subprocess.run(["rsync", "-a", "--delete"] + SRCSYNC +
                               [f"projects/{self.proj}/", f"{DBUILD}/{self.proj}/"],
                               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(qsh(
                    f"mkdir -p {VMDIR}/projects/{self.proj} && rsync -a --delete "
                    + " ".join(SRCSYNC) +
                    f" '{HERE}/projects/{self.proj}/' {VMDIR}/projects/{self.proj}/"),
                    check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._mark(1)

            cmd = (qcd(self.proj) +
                   f"quartus_sh --flow compile {self.proj}; rc=$?; "
                   f"echo '@@CPF'; "
                   f"quartus_cpf -c -q 12.0MHz -g 3.3 -n p {self.proj}.sof {self.proj}.svf >/dev/null 2>&1; "
                   f"echo '@@CPF_DONE'; exit $rc")
            p = subprocess.Popen(qsh(cmd, proj=self.proj), stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, text=True, bufsize=1)
            # Every line goes to the log verbatim. The screen shows a summary;
            # the file is the record, and it is what gets archived.
            log = open(self.logpath, "w")
            after_error = False
            for raw in p.stdout:
                ln = raw.rstrip()
                log.write(raw)
                for key, idx in STARTS.items():
                    if key in ln: self._mark(idx)
                for i, (_, marker) in enumerate(PHASES):
                    if marker and marker in ln and self.done[i] is None and self.t0[i]:
                        self.done[i] = time.time() - self.t0[i]
                if re.search(r"^\s*Error", ln) or "Error (" in ln:
                    self.errors.append(ln.strip())          # no cap, no clipping
                    after_error = True
                elif after_error and re.match(r"^\s*(Info|Warning)\s*\(", ln):
                    # Quartus explains an error in the Info lines that trail it
                    # -- "near text ;" is on the follow-up, not the Error line.
                    self.errors.append("  " + ln.strip())
                elif ln.strip():
                    after_error = False
                m = re.search(r"Total logic elements\s*:\s*([\d,]+)\s*/\s*([\d,]+)", ln)
                if m: self.stats["le"] = f"{m.group(1)} / {m.group(2)}"
            log.close()
            rc = p.wait()
            self.failed = rc != 0 or bool(self.errors)
            self._mark(6)
            if not self.failed:
                os.makedirs("output_files", exist_ok=True)
                for ext in ("sof", "rbf", "svf"):
                    if BACKEND == "remote":
                        subprocess.run(["rsync", "-az", f"{REMOTE}:{RDIR}/projects/{self.proj}/{self.proj}.{ext}",
                                        "output_files/"], stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)
                    elif BACKEND == "local":
                        subprocess.run(["cp", "-f", f"{DBUILD}/{self.proj}/{self.proj}.{ext}",
                                        "output_files/"], stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)
                    else:
                        subprocess.run(qsh(f"cp -f {VMDIR}/projects/{self.proj}/{self.proj}.{ext} "
                                           f"'{HERE}/output_files/'"),
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self._reports()
                self.done[6] = time.time() - self.t0[6]
            # Archive every outcome. A failed build must never leave the
            # previous build's artifacts looking current.
            try:
                self.archived = artifacts.archive(
                    self.proj, "ok" if not self.failed else "failed",
                    stats=self.stats, duration=time.time() - self.t0[0],
                    log=self.logpath, errors=self.errors)
            except Exception as e:
                self.errors.append(f"archive failed: {e}")

        except Exception as e:
            self.failed = True
            self.errors.append(str(e))
        self.finished = True

    def _reports(self):
        """Resource + timing numbers live in the .summary files, not stdout."""
        try:
            r = subprocess.run(qsh(
                    qcd(self.proj) + f"cat {self.proj}.fit.summary {self.proj}.sta.summary 2>/dev/null",
                    proj=self.proj),
                    capture_output=True, text=True, timeout=60)
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
    _host, _cpu, _nthr = backend_info()
    a(f"  {fg(DEEP)}{_host} · {_cpu} · {_nthr or len(cores) or 4} threads{RESET}")
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
    # A VM has no coretemp sensor and no cpufreq. Printing 0.0 C / 0.00 GHz
    # reads as a measurement; "n/a" reads as the absence of one.
    if temp > 0:
        tp = max(0.0, min(100.0, (temp - 30) / 60 * 100))
        tc = GREEN if temp < 60 else (AMBER if temp < 80 else ROSE)
        a(f"   {fg(MUTED)}TMP {RESET}{bar(tp, gw - 6, tc)} {fg(tc)}{temp:4.1f}°C{RESET}")
    else:
        a(f"   {fg(MUTED)}TMP {RESET}{fg(DEEP)}n/a - no sensor on this backend{RESET}")
    if freq > 0:
        a(f"   {fg(MUTED)}CLK {RESET}{fg(PAPER)}{freq:.2f} GHz{RESET}")
    else:
        a(f"   {fg(MUTED)}CLK {RESET}{fg(DEEP)}n/a{RESET}")
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
            # The panel is a fixed height, so it shows a wrapped excerpt and
            # points at the transcript. main() reprints everything in full
            # once the live display is done.
            # A single Quartus error can run past 500 characters, so the
            # budget is spent on wrapped lines and a long first error is cut
            # rather than skipped -- the first one is the one that matters,
            # and the untruncated text follows the panel either way.
            ROOM, used, done = 6, 0, 0
            for e in bld.errors:
                segs = textwrap.wrap(e, W - 8) or [""]
                for j, seg in enumerate(segs):
                    if used >= ROOM:
                        break
                    a(f"    {fg(ROSE)}{'' if j == 0 else '  '}{seg}{RESET}")
                    used += 1
                if used >= ROOM:
                    break
                done += 1
            rest = len(bld.errors) - done
            if rest > 0:
                a(f"    {fg(DEEP)}+{rest} more error line{'' if rest == 1 else 's'}"
                  f" -- full text below{RESET}")
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

def pick_project():
    """Selection page shown when ./build.sh is run without a project name."""
    projs = artifacts.list_projects()
    bad   = artifacts.misnamed_projects()
    if not projs:
        print("no projects found under projects/")
        for d, found in bad:
            print(f"  projects/{d}/ holds {found[0]}.qsf -- rename the directory to "
                  f"'{found[0]}', or rename the .qsf/.qpf/.sdc to '{d}'")
        return None

    info = []
    for pr in projs:
        try:
            n = len(artifacts.source_files(pr))
        except Exception:
            n = 0
        hist = artifacts.list_builds(pr)
        last = hist[0] if hist else None
        if last:
            when  = artifacts.ago(last.get("built_epoch", 0))
            badge = (fg(GREEN) + "\u2713") if last.get("status") == "ok" else (fg(ROSE) + "\u2717")
        else:
            when, badge = "never built", fg(DEEP) + "\u00b7"
        info.append((pr, f"{n} files", when, badge))

    sel, prev = 0, 0
    with Raw():
        while True:
            W  = max(52, min(shutil.get_terminal_size((80, 24)).columns - 2, 84))
            IW = W - 4
            L  = []
            L.append(fg(CYAN) + "╭" + "─" * (W - 2) + "╮" + RESET)
            head = (f"{fg(PINK)}◆{RESET} {fg(ICE)}{BOLD}LYCOCHIP{RESET} "
                    f"{fg(DEEP)}░▒▓{RESET} {fg(PAPER)}BUILD{RESET}")
            L.append(fg(CYAN) + "│ " + RESET + head + " " * max(1, W - 22 - 13)
                     + fg(MUTED) + "EP4CE6E22C8" + fg(CYAN) + " │" + RESET)
            L.append(fg(CYAN) + "╰" + "─" * (W - 2) + "╯" + RESET)
            L.append("")
            # Columns are sized from the data, not hardcoded: a long project
            # name would otherwise push the rest of the row past the panel
            # edge. Everything past the name is fixed-cost, so the name is the
            # column that gives up space (and gets clipped) when it must.
            nw, fw, ww = (max(len(r[i]) for r in info) for i in (0, 1, 2))
            budget = IW - 2                   # "  " + mark + " " already spent 2
            lead   = "built "                 # reads better, but it is the first
            total  = nw + 1 + fw + 3 + len(lead) + ww + 2
            if total > budget:                # thing to go when space is tight
                lead, total = "", total - 6
            if total > budget:                # then the name gives up columns --
                nw = max(6, nw - (total - budget))   # clipping a date is worse
            for i, (pr, files, when, badge) in enumerate(info):
                cur   = i == sel
                mark  = f"{fg(PINK)}▸{RESET}" if cur else " "
                namec = fg(ICE) + BOLD if cur else fg(PAPER)
                stamp = when if when == "never built" else lead + when
                L.append(f"  {mark} {namec}{pad(pr, nw)}{RESET} "
                         f"{fg(MUTED)}{pad(files, fw)}{RESET}   "
                         f"{fg(MUTED) if not cur else fg(PAPER)}"
                         f"{pad(stamp, len(lead) + ww)}{RESET} {badge}{RESET}")
            for d, found in bad:
                why = f"skipped: holds {found[0]}.qsf, not {d}.qsf"
                L.append(f"  {fg(ROSE)}!{RESET} {fg(PAPER)}{pad(d, nw)}{RESET} "
                         f"{fg(MUTED)}{clip(why, budget - nw - 1)}{RESET}")
            L.append("")
            L.append("  " + "   ".join(f"{fg(PINK)}{k}{RESET} {fg(MUTED)}{v}{RESET}"
                                       for k, v in (("↑↓", "select"), ("⏎", "build"), ("q", "quit"))))
            prev = paint(L, prev)
            try:
                k = getkey()
            except KeyboardInterrupt:
                k = "quit"
            if k == "quit":
                return None
            if   k == "up":   sel = (sel - 1) % len(info)
            elif k == "down": sel = (sel + 1) % len(info)
            elif k == "go":   return info[sel][0]


def pick_backend_page():
    """Selection page for where to compile.

    This exists because guessing was wrong in both directions: it picked the
    emulated VM when Docker happened to be down, and it spent seconds waiting
    on an ssh timeout before it could even decide. Choosing is faster than
    detecting, and it is never surprising.
    """
    rows = [(bid, name, why, est) + backend_status(bid)
            for bid, name, why, est in BACKENDS]

    # Land on one that works *right now*: "ready" beats merely usable. With
    # Docker down that means QEMU rather than lyco-server, which is the right
    # default on a network where lyco cannot be reached anyway.
    sel = next((i for i, r in enumerate(rows) if r[5] == "ready"),
               next((i for i, r in enumerate(rows) if r[4]), 0))
    prev = 0
    with Raw():
        while True:
            W  = max(52, min(shutil.get_terminal_size((80, 24)).columns - 2, 84))
            IW = W - 4
            L  = []
            L.append(fg(CYAN) + "\u256d" + "\u2500" * (W - 2) + "\u256e" + RESET)
            head = (f"{fg(PINK)}\u25c6{RESET} {fg(ICE)}{BOLD}LYCOCHIP{RESET} "
                    f"{fg(DEEP)}\u2591\u2592\u2593{RESET} {fg(PAPER)}BACKEND{RESET}")
            L.append(fg(CYAN) + "\u2502 " + RESET + head + " " * max(1, W - 24 - 13)
                     + fg(MUTED) + "EP4CE6E22C8" + fg(CYAN) + " \u2502" + RESET)
            L.append(fg(CYAN) + "\u2570" + "\u2500" * (W - 2) + "\u256f" + RESET)
            L.append("")
            nw = max(len(r[1]) for r in rows)
            ww = max(len(r[2]) for r in rows)
            ew = max(len(r[3]) for r in rows)
            for i, (bid, name, why, est, ok, note) in enumerate(rows):
                cur   = i == sel
                mark  = f"{fg(PINK)}\u25b8{RESET}" if cur else " "
                if not ok:
                    namec = fg(DEEP)
                elif cur:
                    namec = fg(ICE) + BOLD
                else:
                    namec = fg(PAPER)
                notec = fg(GREEN) if ok and note == "ready" else (
                        fg(MUTED) if ok else fg(ROSE))
                L.append(f"  {mark} {namec}{pad(name, nw)}{RESET} "
                         f"{fg(MUTED)}{pad(why, ww)}{RESET}  "
                         f"{(fg(PAPER) if cur else fg(MUTED))}{pad(est, ew)}{RESET}  "
                         f"{notec}{clip(note, max(8, IW - nw - ww - ew - 8))}{RESET}")
            L.append("")
            L.append(f"  {fg(MUTED)}{clip('all three produce byte-identical bitstreams -- verified', IW)}{RESET}")
            L.append("")
            L.append("  " + "   ".join(f"{fg(PINK)}{k}{RESET} {fg(MUTED)}{v}{RESET}"
                                       for k, v in (("\u2191\u2193", "select"),
                                                    ("\u23ce", "use"),
                                                    ("q", "quit"))))
            prev = paint(L, prev)
            try:
                k = getkey()
            except KeyboardInterrupt:
                k = "quit"
            if k == "quit":
                return None
            if   k == "up":   sel = (sel - 1) % len(rows)
            elif k == "down": sel = (sel + 1) % len(rows)
            elif k == "go":   return rows[sel][0]


def main():
    proj = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else None
    if proj is None:
        if not sys.stdin.isatty():
            proj = "blink"
        else:
            proj = pick_project()
            print()
            if proj is None:
                return
    if not BACKEND:
        if sys.stdin.isatty():
            chosen = pick_backend_page()
            print()
            if chosen is None:
                return
            set_backend(chosen)
        else:
            set_backend(auto_backend())
    if BACKEND == "local" and not docker_ready():
        # A stopped runtime silently demoted the build to the slow backend
        # once. Now it is started instead, and said out loud.
        if not docker_bring_up():
            print(f"{fg(ROSE)}could not bring up a container runtime -- "
                  f"pick another backend, or run: colima start{RESET}")
            sys.exit(1)
    if BACKEND == "none":
        print("no build backend available -- start Docker Desktop, or create the "
              f"VM with: limactl start --name={VM} tools/quartus-vm/lima.yaml")
        sys.exit(1)
    if BACKEND == "vm" and vm_exists() not in ("Running",):
        print(f"{fg(MUTED)}starting the {VM} VM (emulated; this takes a few minutes){RESET}")
        subprocess.run(["limactl", "start", VM],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
        tel.stop()
        sys.stdout.write("\033[?25h" + RESET); sys.stdout.flush()

    if bld.failed:
        # The panel above is height-limited; this is not. Everything Quartus
        # said about the failure goes to the terminal in full, unwrapped and
        # copy-pasteable, with the transcript path last so it stays on screen.
        w = max(40, shutil.get_terminal_size((80, 24)).columns - 2)
        print()
        print(f"{fg(ROSE)}{BOLD}{'ERRORS':─<{w}}{RESET}")
        for e in bld.errors:
            print(f"{fg(ROSE)}{e}{RESET}")
        if not bld.errors:
            print(f"{fg(MUTED)}quartus reported no Error lines -- see the "
                  f"transcript for what it did say{RESET}")
        log = os.path.join(bld.archived["_dir"], "build.log") if bld.archived else bld.logpath
        if os.path.exists(log):
            print(f"\n{fg(MUTED)}full transcript:{RESET} {log}")
            print(f"{fg(MUTED)}                less -R {log}{RESET}")

    sys.exit(1 if bld.failed else 0)

if __name__ == "__main__":
    main()
