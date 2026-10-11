"""Prove the GPU Python environment works, rather than take its word for it.

    .venv/Scripts/python tools/gpu_check.py      (Windows)
    .venv/bin/python     tools/gpu_check.py      (elsewhere)

`torch.cuda.is_available()` returning True only says a driver was found. An
RTX 50-series (Blackwell, compute capability 12.0 / sm_120) needs a wheel
built with sm_120 kernels -- CUDA 12.8 or newer. With an older wheel,
is_available() can still say True and the first real kernel then fails with
"no kernel image is available for execution on the device".

So this runs an actual matmul on the GPU and checks the answer against the CPU
in float64. A wrong answer cannot pass by accident.
"""
import sys
import time

import torch

print(f"python      {sys.version.split()[0]}")
print(f"torch       {torch.__version__}  (built for CUDA {torch.version.cuda})")
ok = torch.cuda.is_available()
print(f"cuda        available={ok}")
if not ok:
    sys.exit("FAIL: no CUDA device visible to torch")

dev = torch.device("cuda:0")
cap = torch.cuda.get_device_capability(dev)
arches = torch.cuda.get_arch_list()
print(f"device      {torch.cuda.get_device_name(dev)}  capability sm_{cap[0]}{cap[1]}")
print(f"wheel archs {' '.join(arches)}")
if f"sm_{cap[0]}{cap[1]}" not in arches:
    print(f"WARN: this wheel has no sm_{cap[0]}{cap[1]} kernels; expect failures")

torch.manual_seed(0)
n = 2048
a = torch.randn(n, n, dtype=torch.float32)
b = torch.randn(n, n, dtype=torch.float32)
ref = (a.double() @ b.double())                       # CPU, float64

ga, gb = a.to(dev), b.to(dev)
torch.backends.cuda.matmul.allow_tf32 = False         # full fp32, so the
(ga @ gb); torch.cuda.synchronize()                    # comparison is fair
t0 = time.perf_counter()
reps = 20
for _ in range(reps):
    gc = ga @ gb
torch.cuda.synchronize()
dt = (time.perf_counter() - t0) / reps

err = (gc.double().cpu() - ref).abs().max().item()
scale = ref.abs().max().item()
tflops = 2 * n**3 / dt / 1e12
print(f"matmul      {n}x{n} fp32: {dt*1e3:.2f} ms  ({tflops:.1f} TFLOP/s)")
print(f"check       max |gpu - cpu_f64| = {err:.3e}  (relative {err/scale:.1e})")
if err / scale > 1e-4:
    sys.exit("FAIL: GPU result disagrees with the CPU reference")
print("PASS")
