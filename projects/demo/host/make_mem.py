"""Snapshot the trained model into the demo's memory files.

    python projects/demo/host/make_mem.py

Reads projects/mnist/model/export/ (never writes to it) and writes:

    mem/weights.hex      w1 (16 x 784) then w2 (10 x 16), one 4-bit word per line.
                         Address = 12,544 * layer + neuron * n_inputs + input, so one
                         counter walks every weight of both layers in order.
    mem/bias.hex         b1 (16) then b2 (10), 24-bit words
    mem/model.json       requantisation constants, and the sha256 of the export used
    mem/test_images.hex  the 16 exported test images, 8-bit pixels
    mem/expected.hex     per test image: digit, then its 10 scores (16-bit words)
    rtl/quant_params.vh  M, SHIFT and QMAX for post.v

The snapshot is the point: re-exporting from the notebook does not change the
demo until this script is run again.

All or nothing: every check below runs before anything in mem/ or rtl/ is
touched. The files are first written to a staging directory, the golden model
is run on that staging copy and compared with the notebook's expected.json, and
only then are they copied into place. A failing export leaves the demo as it was.

The checks are worst cases over every possible input, not just the 16 test
images, because the RTL widths are fixed (ARCHITECTURE.md, "Numeric bounds"):

    layer 1, per neuron j:  b1[j] + 255 * sum(min(w,0)) .. b1[j] + 255 * sum(max(w,0))
                            must fit mac.acc, 24-bit signed
    layer 2, per neuron k:  b2[k] + QMAX * sum(min(w,0)) .. b2[k] + QMAX * sum(max(w,0))
                            must fit acc[15:0], 16-bit signed (demo_top takes the score
                            as acc[15:0] with no saturation, and argmax and the reply
                            both use it)

A running partial sum is always inside the same range (each step adds a term
between its own min and max), so bounding the final sum bounds every cycle.
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEMO = os.path.normpath(os.path.join(HERE, ".."))
EXPORT = os.path.normpath(os.path.join(DEMO, "..", "mnist", "model", "export"))
BIAS_BITS = 24      # bias_rom.q and mac.acc
ACC_BITS = 24       # mac.acc
SCORE_BITS = 16     # demo_top: score = acc[15:0]; argmax.score; result_tx.wscore
M_BITS = 24         # post.v: QM is localparam [23:0]
PIXEL_MAX = 255
N_IN, N_HID, N_OUT = 784, 16, 10


class ExportRejected(Exception):
    """The export does not fit the demo's fixed RTL widths."""


def words(path):
    return [line.strip() for line in open(path) if line.strip()]


def signed(h, bits):
    v = int(h, 16)
    return v - (1 << bits) if v >= 1 << (bits - 1) else v


def fits(v, bits):
    return -(1 << (bits - 1)) <= v < (1 << (bits - 1))


def write_hex(path, values, bits):
    digits = (bits + 3) // 4
    mask = (1 << bits) - 1
    for v in values:
        if not fits(v, bits):
            raise ExportRejected(f"{v} does not fit {bits} bits ({os.path.basename(path)})")
    with open(path, "w") as f:
        f.write("\n".join(f"{v & mask:0{digits}X}" for v in values) + "\n")


def worst_case(weights, bias, n_in, x_max):
    """Per neuron: (min, max) of bias + sum(w * x) over every x in 0..x_max."""
    out = []
    for j, b in enumerate(bias):
        row = weights[j * n_in:(j + 1) * n_in]
        out.append((b + x_max * sum(w for w in row if w < 0),
                    b + x_max * sum(w for w in row if w > 0)))
    return out


def check_export(meta, w1, w2, b1, b2):
    """Raise ExportRejected unless every RTL width holds for every input.
    Returns the worst-case ranges, for the summary line."""
    if meta["weight_bits"] != 4:
        raise ExportRejected(f"export has {meta['weight_bits']}-bit weights; the demo RTL is built for 4")
    if meta["act_bits"] != 8:
        raise ExportRejected(f"export has {meta['act_bits']}-bit activations; the demo RTL is built for 8")
    if len(w1) != N_HID * N_IN or len(w2) != N_OUT * N_HID or len(b1) != N_HID or len(b2) != N_OUT:
        raise ExportRejected(f"shapes: w1 {len(w1)}, w2 {len(w2)}, b1 {len(b1)}, b2 {len(b2)}; "
                             f"expected {N_HID * N_IN}, {N_OUT * N_HID}, {N_HID}, {N_OUT}")
    M, shift, qmax = meta["M"], meta["shift"], meta["qmax_act"]
    if not 0 <= M < 1 << M_BITS:
        raise ExportRejected(f"M = {M} does not fit post.v's {M_BITS}-bit unsigned QM")
    # post.v: q = rounded[47:QSHIFT] must keep at least 8 bits for the clamp compare.
    if not 1 <= shift <= 39:
        raise ExportRejected(f"shift = {shift}; post.v supports 1..39")
    if not 1 <= qmax <= 255:
        raise ExportRejected(f"qmax_act = {qmax}; hidden values are 8-bit unsigned")
    for name, bs in (("b1", b1), ("b2", b2)):
        for j, b in enumerate(bs):
            if not fits(b, BIAS_BITS):
                raise ExportRejected(f"{name}[{j}] = {b} does not fit the {BIAS_BITS}-bit bias ROM")

    l1 = worst_case(w1, b1, N_IN, PIXEL_MAX)
    l2 = worst_case(w2, b2, N_HID, qmax)
    for name, ranges, bits, where in (("layer-1 accumulator", l1, ACC_BITS, "mac.acc"),
                                      ("layer-2 score", l2, SCORE_BITS, "acc[15:0]")):
        for j, (lo, hi) in enumerate(ranges):
            if not (fits(lo, bits) and fits(hi, bits)):
                raise ExportRejected(
                    f"{name} of neuron {j} can reach {lo}..{hi} for some input, which does not fit "
                    f"{bits}-bit signed {where} (-{1 << (bits - 1)}..{(1 << (bits - 1)) - 1}). "
                    "The hardware would wrap where the golden model does not.")
    return l1, l2


def main():
    meta = json.load(open(os.path.join(EXPORT, "meta.json")))
    w1 = [signed(h, 4) for h in words(os.path.join(EXPORT, "w1.hex"))]
    w2 = [signed(h, 4) for h in words(os.path.join(EXPORT, "w2.hex"))]
    bb = meta["bias_bits"]
    b1 = [signed(h, bb) for h in words(os.path.join(EXPORT, "b1.hex"))]
    b2 = [signed(h, bb) for h in words(os.path.join(EXPORT, "b2.hex"))]
    px = [int(h, 16) for h in words(os.path.join(EXPORT, "test_images.hex"))]
    exp = json.load(open(os.path.join(EXPORT, "expected.json")))
    try:
        l1, l2 = check_export(meta, w1, w2, b1, b2)
    except ExportRejected as e:
        sys.exit(f"make_mem: export rejected, nothing written: {e}")

    sha = hashlib.sha256()
    for f in sorted(os.listdir(EXPORT)):
        sha.update(f.encode()); sha.update(open(os.path.join(EXPORT, f), "rb").read())

    outputs = {  # staging name -> final path
        "weights.hex": os.path.join(DEMO, "mem", "weights.hex"),
        "bias.hex": os.path.join(DEMO, "mem", "bias.hex"),
        "model.json": os.path.join(DEMO, "mem", "model.json"),
        "test_images.hex": os.path.join(DEMO, "mem", "test_images.hex"),
        "expected.hex": os.path.join(DEMO, "mem", "expected.hex"),
        "quant_params.vh": os.path.join(DEMO, "rtl", "quant_params.vh"),
    }
    with tempfile.TemporaryDirectory(prefix="make_mem_") as stage:
        try:
            write_hex(os.path.join(stage, "weights.hex"), w1 + w2, 4)
            write_hex(os.path.join(stage, "bias.hex"), b1 + b2, BIAS_BITS)
            with open(os.path.join(stage, "model.json"), "w") as f:
                json.dump({"M": meta["M"], "shift": meta["shift"], "qmax_act": meta["qmax_act"],
                           "bias_bits": BIAS_BITS, "export_sha256": sha.hexdigest()}, f, indent=1)
            with open(os.path.join(stage, "quant_params.vh"), "w") as f:
                f.write("// Generated by host/make_mem.py from model/export/meta.json. Do not edit.\n"
                        f"localparam [23:0] QM     = 24'd{meta['M']};\n"
                        f"localparam        QSHIFT = {meta['shift']};\n"
                        f"localparam [7:0]  QMAX   = 8'd{meta['qmax_act']};\n")

            # Test vectors, re-derived from the staged files and checked
            # against the notebook's own expected.json.
            sys.path.insert(0, HERE)
            from golden import Model
            model = Model(stage)
            if len(px) % N_IN or not px:
                raise ExportRejected(f"test_images.hex has {len(px)} pixels, not a multiple of {N_IN}")
            out = []
            for n in range(len(px) // N_IN):
                h, scores, digit = model.forward(px[n * N_IN:(n + 1) * N_IN])
                if scores != exp["scores"][n] or h != exp["hidden_activations"][n]:
                    raise ExportRejected(f"image {n}: snapshot disagrees with expected.json")
                out += [digit] + scores
            write_hex(os.path.join(stage, "test_images.hex"), [p - 256 if p > 127 else p for p in px], 8)
            write_hex(os.path.join(stage, "expected.hex"), out, SCORE_BITS)
        except ExportRejected as e:
            sys.exit(f"make_mem: export rejected, nothing written: {e}")

        for name, dest in outputs.items():
            shutil.copyfile(os.path.join(stage, name), dest)

    print(f"wrote mem/ and rtl/quant_params.vh from {EXPORT}")
    print(f"  {len(w1) + len(w2)} weights, {len(b1) + len(b2)} biases, M = {meta['M']}, "
          f"{len(px) // N_IN} test images, all matching expected.json")
    print(f"  worst case over all inputs: layer-1 acc {min(lo for lo, _ in l1)}..{max(hi for _, hi in l1)} "
          f"({ACC_BITS}-bit), score {min(lo for lo, _ in l2)}..{max(hi for _, hi in l2)} ({SCORE_BITS}-bit)")


if __name__ == "__main__":
    main()
