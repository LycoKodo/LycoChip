"""Integer golden model for the demo, read from the demo's own memory files.

This is the arithmetic the RTL performs, step for step, so the scores it
returns must equal the FPGA's bit for bit:

    acc1[j] = b1[j] + sum_i w1[j][i] * pixel[i]
    h[j]    = min((max(acc1[j], 0) * M + 2**(SHIFT-1)) >> SHIFT, QMAX)
    score[k] = b2[k] + sum_j w2[k][j] * h[j]
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MEM = os.path.join(HERE, "..", "mem")

N_IN, N_HID, N_OUT = 784, 16, 10


def read_hex(path, bits):
    """One two's-complement word per line, as written for $readmemh."""
    vals = [int(line, 16) for line in open(path) if line.strip()]
    return np.array([v - (1 << bits) if v >= 1 << (bits - 1) else v for v in vals], dtype=np.int64)


class Model:
    def __init__(self, mem=MEM):
        meta = json.load(open(os.path.join(mem, "model.json")))
        self.M, self.SHIFT, self.QMAX = meta["M"], meta["shift"], meta["qmax_act"]
        w = read_hex(os.path.join(mem, "weights.hex"), 4)
        b = read_hex(os.path.join(mem, "bias.hex"), meta["bias_bits"])
        self.W1 = w[:N_HID * N_IN].reshape(N_HID, N_IN)
        self.W2 = w[N_HID * N_IN:].reshape(N_OUT, N_HID)
        self.b1, self.b2 = b[:N_HID], b[N_HID:]

    def forward(self, pixels):
        """pixels: 784 ints 0..255. Returns (hidden, scores, digit), all ints."""
        x = np.asarray(pixels, dtype=np.int64)
        assert x.shape == (N_IN,) and x.min() >= 0 and x.max() <= 255
        acc1 = self.W1 @ x + self.b1
        h = np.minimum((np.maximum(acc1, 0) * self.M + (1 << (self.SHIFT - 1))) >> self.SHIFT, self.QMAX)
        scores = self.W2 @ h + self.b2
        # np.argmax returns the first maximum; the RTL's argmax keeps the first too.
        return [int(v) for v in h], [int(v) for v in scores], int(np.argmax(scores))
