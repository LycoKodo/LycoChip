"""Serial link to the demo FPGA (protocol in projects/demo/ARCHITECTURE.md).

    Mac -> FPGA:  A5 5A, then 784 pixel bytes, row-major, 0 = background, 255 = ink
    FPGA -> Mac:  C3, digit (0..9), then 10 x int16 little-endian scores (22 bytes)

115,200 baud, 8N1. The board's UART goes through a MAX3232 to an RS-232
connector, so the Mac needs a USB-to-RS-232 adapter, not a 3.3 V TTL one.
The board's DB9 is wired DCE (transmits on pin 2, receives on pin 3), so the
adapter needs a straight-through cable or a direct plug; a null-modem cable
connects TX to TX and the only symptom is a reply timeout.

    from fpga_link import FpgaLink, list_ports
    with FpgaLink("/dev/cu.usbserial-XXXX") as link:
        digit, scores, ms = link.infer(pixels)
"""
import struct
import time

import serial
import serial.tools.list_ports

BAUD = 115200
N_PIXELS = 784
FRAME_HEADER = bytes([0xA5, 0x5A])
REPLY_HEADER = 0xC3
REPLY_LEN = 22
REPLY_TIMEOUT = 2.0  # seconds, overall, from the call to read_reply()


class LinkError(Exception):
    """Anything that went wrong talking to the board."""


class ReplyTimeout(LinkError):
    """No complete, well-formed reply arrived in time."""


class BadReply(LinkError):
    """Bytes arrived, but they are not a reply."""


def list_ports():
    """Serial device paths, /dev/cu.* first (on macOS the cu.* node is the one
    to open: tty.* blocks waiting for carrier detect)."""
    devs = [p.device for p in serial.tools.list_ports.comports()]
    return sorted(devs, key=lambda d: (not d.startswith("/dev/cu."), d))


class FpgaLink:
    def __init__(self, port, baud=BAUD, timeout=REPLY_TIMEOUT):
        self.port = port
        self.timeout = timeout
        try:
            self.ser = serial.Serial(port, baudrate=baud, bytesize=serial.EIGHTBITS,
                                     parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                                     timeout=0.05, write_timeout=timeout,
                                     xonxoff=False, rtscts=False, dsrdtr=False)
        except serial.SerialException as e:
            raise LinkError(f"cannot open {port}: {e}") from e

    def close(self):
        self.ser.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def send_frame(self, pixels):
        """Send one image: 784 ints 0..255, row-major."""
        px = list(pixels)
        if len(px) != N_PIXELS:
            raise ValueError(f"need {N_PIXELS} pixels, got {len(px)}")
        if any(not 0 <= int(p) <= 255 for p in px):
            raise ValueError("pixels must be 0..255")
        # Drop anything stale (a late reply to an earlier frame) so it cannot
        # be mistaken for the reply to this one.
        self.ser.reset_input_buffer()
        try:
            self.ser.write(FRAME_HEADER + bytes(int(p) for p in px))
            self.ser.flush()
        except serial.SerialTimeoutException as e:
            raise LinkError(f"write to {self.port} timed out") from e

    def read_reply(self, timeout=None):
        """Wait for one reply. Returns (digit, scores), scores a list of 10
        signed ints. Bytes before a C3 header are discarded; a C3 followed by
        a digit outside 0..9 is treated as a false header and skipped."""
        deadline = time.monotonic() + (self.timeout if timeout is None else timeout)
        buf = bytearray()
        discarded = 0
        while True:
            # Resynchronise: drop everything before the first plausible header.
            while buf:
                i = buf.find(REPLY_HEADER)
                if i < 0:
                    discarded += len(buf)
                    buf.clear()
                elif i > 0:
                    discarded += i
                    del buf[:i]
                elif len(buf) >= 2 and buf[1] > 9:
                    discarded += 1  # C3 then a non-digit: not a header
                    del buf[:1]
                else:
                    break
            if len(buf) >= REPLY_LEN:
                digit = buf[1]
                scores = list(struct.unpack("<10h", bytes(buf[2:REPLY_LEN])))
                return digit, scores
            left = deadline - time.monotonic()
            if left <= 0:
                break
            chunk = self.ser.read(max(1, REPLY_LEN - len(buf)))
            buf += chunk
        if buf:
            raise ReplyTimeout(f"reply incomplete after {self.timeout:.1f} s: got {len(buf)} of "
                               f"{REPLY_LEN} bytes after the C3 header ({buf.hex(' ')})")
        if discarded:
            raise BadReply(f"no valid reply header (C3 + digit 0..9) in {discarded} bytes "
                           f"received within {self.timeout:.1f} s")
        raise ReplyTimeout(f"no reply from {self.port} within {self.timeout:.1f} s "
                           "(board programmed? RS-232 adapter, not TTL? straight-through cable, "
                           "not null-modem? cable on the right port?)")

    def infer(self, pixels):
        """send_frame + read_reply. Returns (digit, scores, round_trip_ms)."""
        t0 = time.perf_counter()
        self.send_frame(pixels)
        digit, scores = self.read_reply()
        return digit, scores, (time.perf_counter() - t0) * 1000.0


if __name__ == "__main__":
    for d in list_ports():
        print(d)
