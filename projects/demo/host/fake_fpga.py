"""A stand-in for the demo board, for testing the host side without hardware.

    python projects/demo/host/fake_fpga.py            prints the pty path, serves until ^C
    python projects/demo/host/fake_fpga.py --perturb 5    corrupts score[0] of frame 5 by +1

It opens a pseudo-terminal and answers frames exactly per ARCHITECTURE.md,
computing the reply with golden.Model. Frame reception copies frame_rx:
HUNT1 -> HUNT2 on A5; in HUNT2, 5A -> DATA, A5 stays, anything else -> HUNT1;
784 data bytes; a gap longer than TIMEOUT in HUNT2/DATA drops back to HUNT1.

Importable:
    with FakeFpga() as fake:
        link = FpgaLink(fake.port)
"""
import argparse
import os
import select
import struct
import sys
import threading
import time
import tty

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from golden import Model  # noqa: E402

N = 784
# frame_rx's TIMEOUT = 2,500,000 cycles at 50 MHz.
GAP_TIMEOUT = 2_500_000 / 50e6

HUNT1, HUNT2, DATA = "HUNT1", "HUNT2", "DATA"


class FakeFpga:
    def __init__(self, model=None, perturb_frame=None, log=None):
        """perturb_frame: index (0-based) of a received frame whose reply gets
        score[0] += 1, to prove a checker can fail. None = honest."""
        self.model = model or Model()
        self.perturb_frame = perturb_frame
        self.log = log
        self.master, self.slave = os.openpty()
        # Raw: no echo, no CR/LF translation, no ^C/^S interpretation.
        tty.setraw(self.slave)
        tty.setraw(self.master)
        self.port = os.ttyname(self.slave)
        self.frames = 0
        self._stop = threading.Event()
        self._thread = None

    # The same three states as frame_rx.
    def _serve(self):
        state, addr, last = HUNT1, 0, time.monotonic()
        image = bytearray(N)
        while not self._stop.is_set():
            r, _, _ = select.select([self.master], [], [], 0.01)
            now = time.monotonic()
            if state != HUNT1 and now - last > GAP_TIMEOUT:
                state = HUNT1  # half-received frame: never starts an inference
            if not r:
                continue
            try:
                data = os.read(self.master, 4096)
            except OSError:
                return
            last = time.monotonic()
            for b in data:
                if state == HUNT1:
                    if b == 0xA5:
                        state = HUNT2
                elif state == HUNT2:
                    if b == 0x5A:
                        state, addr = DATA, 0
                    elif b != 0xA5:
                        state = HUNT1
                else:
                    image[addr] = b
                    addr += 1
                    if addr == N:
                        self._reply(image)
                        state = HUNT1

    def _reply(self, image):
        _, scores, digit = self.model.forward(list(image))
        if self.perturb_frame is not None and self.frames == self.perturb_frame:
            scores = list(scores)
            scores[0] += 1
        if self.log:
            self.log(f"frame {self.frames}: digit {digit}")
        self.frames += 1
        msg = bytes([0xC3, digit]) + struct.pack("<10h", *scores)
        os.write(self.master, msg)

    def start(self):
        self._thread = threading.Thread(target=self._serve, name="fake_fpga", daemon=True)
        self._thread.start()
        return self

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(1.0)
        for fd in (self.master, self.slave):
            try:
                os.close(fd)
            except OSError:
                pass

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--perturb", type=int, metavar="FRAME",
                    help="add 1 to score[0] in the reply to frame FRAME (0-based)")
    args = ap.parse_args()
    fake = FakeFpga(perturb_frame=args.perturb,
                    log=lambda s: print(s, file=sys.stderr, flush=True)).start()
    print(fake.port, flush=True)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        fake.stop()


if __name__ == "__main__":
    main()
