"""Hardware test: the board's replies must equal mem/expected.hex bit for bit.

    python projects/demo/host/check_board.py /dev/cu.usbserial-XXXX   (or COM3)
    python projects/demo/host/check_board.py JTAG        (over the USB-Blaster, jtag_bridge.py)
    python projects/demo/host/check_board.py --fake      (in-process stand-in, no board)

Sends the 16 images of mem/test_images.hex and compares each reply, the digit
and all 10 scores, with mem/expected.hex. One line per image, then PASS or
FAIL. Exit status 0 on PASS, 1 otherwise.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fpga_link import LinkError, open_link  # noqa: E402

MEM = os.path.join(HERE, "..", "mem")


def words(path):
    return [int(line, 16) for line in open(path) if line.strip()]


def signed16(v):
    return v - 0x10000 if v >= 0x8000 else v


def load_vectors(mem=MEM):
    px = words(os.path.join(mem, "test_images.hex"))
    exp = [signed16(v) for v in words(os.path.join(mem, "expected.hex"))]
    n = len(px) // 784
    assert len(px) == n * 784 and len(exp) == n * 11, "test_images.hex / expected.hex sizes disagree"
    images = [px[k * 784:(k + 1) * 784] for k in range(n)]
    expected = [(exp[k * 11], exp[k * 11 + 1:k * 11 + 11]) for k in range(n)]
    return images, expected


def run(port):
    images, expected = load_vectors()
    try:
        link = open_link(port)
    except LinkError as e:
        print(e)
        print("FAIL")
        return 1
    bad = 0
    with link:
        for k, (img, (e_digit, e_scores)) in enumerate(zip(images, expected)):
            try:
                digit, scores, ms = link.infer(img)
            except LinkError as e:
                print(f"image {k:2d}: expected {e_digit}  ERROR {e}")
                bad += 1
                continue
            diffs = [f"score[{i}] {s} != {es}" for i, (s, es) in enumerate(zip(scores, e_scores)) if s != es]
            if digit != e_digit:
                diffs.insert(0, f"digit {digit} != {e_digit}")
            if diffs:
                bad += 1
                print(f"image {k:2d}: expected {e_digit} got {digit}  MISMATCH {', '.join(diffs)}  ({ms:.1f} ms)")
            else:
                print(f"image {k:2d}: expected {e_digit} got {digit}  10/10 scores match  ({ms:.1f} ms)")
    print(f"{len(images) - bad}/{len(images)} images match")
    print("PASS" if bad == 0 else "FAIL")
    return 0 if bad == 0 else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("port", nargs="?", help="serial device, e.g. /dev/cu.usbserial-XXXX")
    ap.add_argument("--fake", action="store_true", help="test against fake_fpga in-process, no board")
    args = ap.parse_args()
    if args.fake == bool(args.port):
        ap.error("give exactly one of PORT or --fake")
    if args.fake:
        from fake_fpga import FakeFpga
        with FakeFpga() as fake:
            print(f"fake FPGA on {fake.port} (golden model, not hardware)")
            return run(fake.port)
    return run(args.port)


if __name__ == "__main__":
    sys.exit(main())
