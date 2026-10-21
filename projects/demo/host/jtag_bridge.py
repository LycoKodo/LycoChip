"""JTAG link to the demo FPGA, for a host with no RS-232 port.

Protocol: projects/demo/ARCHITECTURE.md, "Over JTAG instead". Authored by Claude
(projects/demo/ override; not Alex's work).

Same interface as fpga_link.FpgaLink, so check_board.py and draw.py take either
(fpga_link.open_link picks this one for a port named "JTAG ..."):

    from jtag_bridge import JtagLink
    with JtagLink() as link:
        digit, scores, ms = link.infer(pixels)

It keeps one `quartus_stp` (the Quartus Tcl shell that drives the USB-Blaster)
running, so its start-up is paid once. Commands and answers go over a loopback
TCP socket, not stdin/stdout: on Windows quartus_stp holds back everything it
prints to a pipe until it exits, even after `flush stdout` (measured).

    WRITE  virtual IR 1, one 6,288-bit DR scan: A5 5A + 784 pixels, byte 0 in
           the least significant bits (shifted first)
    READ   virtual IR 2, 184-bit DR scans until the reply count (low byte) is
           22, then until two reads in a row agree

quartus_stp is found via $QUARTUS_STP, then PATH, then the usual install
folders (C:\\altera_lite\\*, C:\\intelFPGA_lite\\*). The design on the board
must contain jtag_link (any demo build from 2026-10-20 on); with anything else
loaded, the first transfer fails with an error naming the instance.

    python jtag_bridge.py      open the cable and print what it found
"""
import glob
import os
import re
import shutil
import socket
import struct
import subprocess
import tempfile
import time

from fpga_link import BadReply, LinkError, N_PIXELS, FRAME_HEADER, REPLY_HEADER, REPLY_LEN, \
    REPLY_TIMEOUT, ReplyTimeout

JTAG = "JTAG (USB-Blaster)"
STARTUP_TIMEOUT = 60.0  # seconds; quartus_stp takes a few to start

# Runs inside quartus_stp. Connects back to the Python side on the port given
# as its argument, reads one Tcl command per line, and answers each with
# exactly one line, "@@ <rc> <result>".
TCL_SERVER = r'''
set lc_sock [socket 127.0.0.1 [lindex $quartus(args) 0]]
fconfigure $lc_sock -buffering line -translation lf

proc lc_open {} {
    set hw ""
    foreach h [get_hardware_names] {
        if {[string match "*Blaster*" $h]} { set hw $h; break }
    }
    if {$hw eq ""} { error "no USB-Blaster: get_hardware_names returned {[get_hardware_names]}" }
    set dev [lindex [get_device_names -hardware_name $hw] 0]
    open_device -hardware_name $hw -device_name $dev
    return "$hw / $dev"
}

proc lc_count {v} {
    scan [string range $v end-1 end] %x c
    return $c
}

proc lc_infer {hex timeout_ms} {
    device_lock -timeout 10000
    set rc [catch {
        device_virtual_ir_shift -instance_index 0 -ir_value 1 -no_captured_ir_value
        device_virtual_dr_shift -instance_index 0 -length 6288 -dr_value $hex -value_in_hex -no_captured_dr_value
        device_virtual_ir_shift -instance_index 0 -ir_value 2 -no_captured_ir_value
        set t0 [clock milliseconds]
        set prev ""
        while {1} {
            set v [device_virtual_dr_shift -instance_index 0 -length 184 -value_in_hex]
            if {[lc_count $v] == 22 && $v eq $prev} { break }
            set prev $v
            if {[clock milliseconds] - $t0 > $timeout_ms} {
                error "no complete reply within $timeout_ms ms (last READ $v)"
            }
        }
        set v
    } r]
    device_unlock
    if {$rc} { error $r }
    return $r
}

puts $lc_sock "@@ 0 ready"
while {[gets $lc_sock line] >= 0} {
    set rc [catch {uplevel #0 $line} r]
    puts $lc_sock "@@ $rc [string map {"\n" " " "\r" ""} $r]"
}
catch close_device
'''


def find_quartus_stp():
    """Path to quartus_stp, or None."""
    env = os.environ.get("QUARTUS_STP")
    if env and os.path.isfile(env):
        return env
    found = shutil.which("quartus_stp")
    if found:
        return found
    for pattern in (r"C:\altera_lite\*\quartus\bin64\quartus_stp.exe",
                    r"C:\intelFPGA_lite\*\quartus\bin64\quartus_stp.exe",
                    os.path.expanduser("~/intelFPGA_lite/*/quartus/bin/quartus_stp")):
        hits = sorted(glob.glob(pattern))
        if hits:
            return hits[-1]
    return None


class JtagLink:
    def __init__(self, port=JTAG, timeout=REPLY_TIMEOUT):
        self.port = port
        self.timeout = timeout
        stp = find_quartus_stp()
        if stp is None:
            raise LinkError("quartus_stp not found (set QUARTUS_STP to its path)")
        self._proc = self._sock = self._file = None
        fd, self._script = tempfile.mkstemp(prefix="lycochip_jtag_", suffix=".tcl")
        with os.fdopen(fd, "w") as f:
            f.write(TCL_SERVER)
        self._logpath = self._script[:-4] + ".log"
        try:
            srv = socket.socket()
            srv.bind(("127.0.0.1", 0))
            srv.listen(1)
            srv.settimeout(0.5)
            flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            with open(self._logpath, "w") as log:
                self._proc = subprocess.Popen(
                    [stp, "-t", self._script, str(srv.getsockname()[1])],
                    stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                    creationflags=flags)
            deadline = time.monotonic() + STARTUP_TIMEOUT
            while self._sock is None:
                if self._proc.poll() is not None:
                    raise LinkError(f"quartus_stp exited at start-up: {self._log_tail()}")
                if time.monotonic() > deadline:
                    raise LinkError(f"quartus_stp did not connect within {STARTUP_TIMEOUT:.0f} s")
                try:
                    self._sock, _ = srv.accept()
                except socket.timeout:
                    pass
            srv.close()
            self._file = self._sock.makefile("rw", encoding="ascii", errors="replace", newline="\n")
            self._answer("start-up", STARTUP_TIMEOUT)
            self.cable = self._cmd("lc_open", STARTUP_TIMEOUT)
        except Exception:
            self.close()
            raise

    def _log_tail(self):
        try:
            with open(self._logpath, errors="replace") as f:
                lines = [ln.strip() for ln in f if ln.strip() and "TBBmalloc" not in ln]
            return " | ".join(lines[-6:])
        except OSError:
            return "(no log)"

    def _answer(self, what, timeout):
        self._sock.settimeout(timeout)
        try:
            line = self._file.readline()
        except socket.timeout as e:
            raise LinkError(f"quartus_stp: no answer to {what} within {timeout:.0f} s") from e
        if not line:
            raise LinkError(f"quartus_stp exited during {what}: {self._log_tail()}")
        m = re.match(r"@@ (\d+) ?(.*)$", line.rstrip("\r\n"))
        if not m:
            raise LinkError(f"quartus_stp: unexpected answer to {what}: {line!r}")
        if m.group(1) != "0":
            raise LinkError(f"quartus_stp: {what}: {m.group(2)}")
        return m.group(2)

    def _cmd(self, line, timeout):
        try:
            self._file.write(line + "\n")
            self._file.flush()
        except OSError as e:
            raise LinkError(f"quartus_stp is not running: {e}") from e
        return self._answer(line.split()[0], timeout)

    def close(self):
        # Closing the socket ends the Tcl loop, which closes the device and exits.
        for obj in (self._file, self._sock):
            if obj is not None:
                try:
                    obj.close()
                except OSError:
                    pass
        self._file = self._sock = None
        if self._proc is not None and self._proc.poll() is None:
            try:
                self._proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._proc.kill()
                self._proc.wait()
        for path in (self._script, self._logpath):
            try:
                os.remove(path)
            except OSError:
                pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def infer(self, pixels):
        """Send one image, wait for the reply. Returns (digit, scores, round_trip_ms)."""
        px = list(pixels)
        if len(px) != N_PIXELS:
            raise ValueError(f"need {N_PIXELS} pixels, got {len(px)}")
        if any(not 0 <= int(p) <= 255 for p in px):
            raise ValueError("pixels must be 0..255")
        frame = FRAME_HEADER + bytes(int(p) for p in px)
        value = format(int.from_bytes(frame, "little"), f"0{2 * len(frame)}X")
        t0 = time.perf_counter()
        try:
            v = self._cmd(f"lc_infer {value} {int(self.timeout * 1000)}", self.timeout + 15)
        except LinkError as e:
            if "no complete reply" in str(e):
                raise ReplyTimeout(str(e)) from e
            raise
        ms = (time.perf_counter() - t0) * 1000.0
        word = int(v.strip(), 16)
        count = word & 0xFF
        reply = ((word >> 8) & ((1 << (8 * REPLY_LEN)) - 1)).to_bytes(REPLY_LEN, "little")
        if count != REPLY_LEN or reply[0] != REPLY_HEADER or reply[1] > 9:
            raise BadReply(f"READ gave count {count}, reply {reply.hex(' ')}")
        scores = list(struct.unpack("<10h", reply[2:]))
        return reply[1], scores, ms


if __name__ == "__main__":
    print("quartus_stp:", find_quartus_stp())
    with JtagLink() as link:
        print("opened:", link.cable)
