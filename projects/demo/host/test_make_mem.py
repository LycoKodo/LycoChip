"""Test make_mem.py on scratch copies of the export. Never touches mem/, rtl/ or the export.

    python projects/demo/host/test_make_mem.py

Builds, in a temporary directory, the same layout make_mem.py expects
(demo/host, demo/mem, demo/rtl, mnist/model/export), then runs make_mem.py there:

  1. the real export: must succeed and, if the export is the one the
     committed snapshot was made from (sha256 in mem/model.json), reproduce
     the committed mem/ and rtl/quant_params.vh byte for byte;
  2. b2[7] + 30008, with expected.json shifted to match, so the 16 test
     images still agree and their scores still fit 16 bits, but the worst-case
     score for neuron 7 does not: must be rejected;
  3. b1[0] = 8,380,000 (fits the 24-bit bias, but the worst-case layer-1
     accumulator does not fit 24 bits): must be rejected;
  4. M = 2^24: must be rejected.

Every rejection must exit non-zero, name the check that caught it (so a case
cannot pass for some other reason), and leave mem/ and rtl/ byte-identical.
Prints PASS or FAIL; exits 0 or 1.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEMO = os.path.normpath(os.path.join(HERE, ".."))
EXPORT = os.path.normpath(os.path.join(DEMO, "..", "mnist", "model", "export"))
OUT_FILES = ["mem/weights.hex", "mem/bias.hex", "mem/model.json", "mem/test_images.hex",
             "mem/expected.hex", "rtl/quant_params.vh"]


def snapshot(demo):
    return {f: open(os.path.join(demo, f), "rb").read() for f in OUT_FILES}


def setup(root):
    demo = os.path.join(root, "demo")
    os.makedirs(os.path.join(demo, "host"))
    for f in ("make_mem.py", "golden.py"):
        shutil.copy(os.path.join(HERE, f), os.path.join(demo, "host", f))
    shutil.copytree(os.path.join(DEMO, "mem"), os.path.join(demo, "mem"))
    os.makedirs(os.path.join(demo, "rtl"))
    shutil.copy(os.path.join(DEMO, "rtl", "quant_params.vh"), os.path.join(demo, "rtl"))
    export = os.path.join(root, "mnist", "model", "export")
    shutil.copytree(EXPORT, export)
    return demo, export


def run(demo):
    p = subprocess.run([sys.executable, os.path.join(demo, "host", "make_mem.py")],
                       capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def set_word(path, idx, value, bits=32):
    lines = [l.strip() for l in open(path) if l.strip()]
    lines[idx] = f"{value & ((1 << bits) - 1):08X}"
    open(path, "w").write("\n".join(lines) + "\n")


def get_word(path, idx, bits=32):
    v = int([l.strip() for l in open(path) if l.strip()][idx], 16)
    return v - (1 << bits) if v >= 1 << (bits - 1) else v


def main():
    errors = []

    # 1. The real export.
    with tempfile.TemporaryDirectory() as root:
        demo, export = setup(root)
        rc, out = run(demo)
        print(f"[real export] rc={rc}\n  " + out.replace("\n", "\n  "))
        if rc != 0:
            errors.append("real export rejected")
        else:
            committed_sha = json.load(open(os.path.join(DEMO, "mem", "model.json")))["export_sha256"]
            sha = hashlib.sha256()
            for f in sorted(os.listdir(EXPORT)):
                sha.update(f.encode()); sha.update(open(os.path.join(EXPORT, f), "rb").read())
            if sha.hexdigest() != committed_sha:
                print("  reproducibility not checked: the export changed since mem/ was snapshotted")
            else:
                new, old = snapshot(demo), snapshot(DEMO)
                diff = [f for f in OUT_FILES if new[f] != old[f]]
                print(f"  reproduces committed snapshot: {'yes' if not diff else 'NO, differs in ' + ', '.join(diff)}")
                if diff:
                    errors.append(f"real export does not reproduce committed files: {diff}")

    # 2-4. Doctored exports that must be rejected without writing anything.
    def doctor_b2(export):
        meta = json.load(open(os.path.join(export, "meta.json")))
        b2 = os.path.join(export, "b2.hex")
        set_word(b2, 7, get_word(b2, 7, meta["bias_bits"]) + 30008, meta["bias_bits"])
        ej = os.path.join(export, "expected.json")
        exp = json.load(open(ej))
        for s in exp["scores"]:
            s[7] += 30008
        # keep 'predicted' consistent too (argmax, first maximum)
        exp["predicted"] = [max(range(10), key=lambda k: (s[k], -k)) for s in exp["scores"]]
        json.dump(exp, open(ej, "w"))
        print(f"  test-image scores for neuron 7 now {min(s[7] for s in exp['scores'])}"
              f"..{max(s[7] for s in exp['scores'])} (fit 16 bits)")

    def doctor_b1(export):
        set_word(os.path.join(export, "b1.hex"), 0, 8_380_000)

    def doctor_m(export):
        mp = os.path.join(export, "meta.json")
        meta = json.load(open(mp))
        meta["M"] = 1 << 24
        json.dump(meta, open(mp, "w"), indent=1)

    for label, doctor, reason in (
            ("b2[7] + 30008", doctor_b2, "layer-2 score of neuron 7 can reach"),
            ("b1[0] = 8380000", doctor_b1, "layer-1 accumulator of neuron 0 can reach"),
            ("M = 2^24", doctor_m, "M = 16777216 does not fit")):
        with tempfile.TemporaryDirectory() as root:
            demo, export = setup(root)
            print(f"[{label}]")
            doctor(export)
            before = snapshot(demo)
            rc, out = run(demo)
            after = snapshot(demo)
            changed = [f for f in OUT_FILES if before[f] != after[f]]
            print(f"  rc={rc}\n  " + out.replace("\n", "\n  "))
            print(f"  files changed: {changed or 'none'}")
            if rc == 0:
                errors.append(f"{label}: accepted")
            elif reason not in out:
                errors.append(f"{label}: rejected, but not by the expected check ({reason!r})")
            if changed:
                errors.append(f"{label}: wrote {changed} despite the bad export")

    for e in errors:
        print("error:", e)
    print("FAIL" if errors else "PASS")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
