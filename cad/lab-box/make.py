"""Regenerate every Lab Box output from params.py + box.py, and check it.

    .venv/Scripts/python.exe make.py            # export + check + render
    .venv/Scripts/python.exe make.py --no-render

What it does, in order:
  1. export   each printable part -> parts/<name>.step and parts/<name>.stl
  2. check    every STL is watertight (one closed shell, positive volume)
              every printable part fits the print bed with margin
              no two assembly items overlap, except pairs box.py declares
              as intended contact (ALLOWED_OVERLAPS)
  3. render   renders/<part>.png per part, plus assembly views
  4. report   the MEASURE placeholders still in use (params.py)

The exit code is non-zero if any check fails. An exit code of 0 is still
not evidence that the box fits the real board: every MEASURE value in
params.py is an estimate until Alex measures it.

Contract with box.py:
  PARTS          {name: fn() -> cq.Workplane | cq.Shape}  printable, in PRINT orientation
  ASSEMBLY       fn() -> list of Item(name, shape, color, kind) in the BOX frame
                 kind is "printed", "bought" or "reference"
  ALLOWED_OVERLAPS  set of frozenset({name_a, name_b}) that may touch/overlap
                    (screw in insert, spreader on package, ...)
  SECTIONS       optional {name: (origin xyz, normal xyz)} section views to render
"""
from __future__ import annotations

import argparse
import itertools
import math
import os
import sys
import time

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import params  # noqa: E402
from render import as_shape, render  # noqa: E402
import box  # noqa: E402

PARTS_DIR = os.path.join(HERE, "parts")
RENDERS_DIR = os.path.join(HERE, "renders")

OVERLAP_TOL_MM3 = 1.0  # boolean noise below this volume is not a collision


# ---------------------------------------------------------------- export + mesh checks

def export_parts(results: list) -> dict:
    os.makedirs(PARTS_DIR, exist_ok=True)
    shapes = {}
    for name, fn in box.PARTS.items():
        t0 = time.time()
        shape = as_shape(fn())
        shapes[name] = shape
        step = os.path.join(PARTS_DIR, f"{name}.step")
        stl = os.path.join(PARTS_DIR, f"{name}.stl")
        cq.exporters.export(shape, step)
        cq.exporters.export(shape, stl, tolerance=0.05, angularTolerance=0.2)
        print(f"  exported {name:<24} {time.time() - t0:5.1f} s")
    return shapes


def check_meshes(shapes: dict, results: list) -> None:
    import trimesh

    bed_x, bed_y, bed_z = params.BED_X, params.BED_Y, params.BED_Z
    margin = params.BED_MARGIN
    for name, shape in shapes.items():
        mesh = trimesh.load(os.path.join(PARTS_DIR, f"{name}.stl"), force="mesh")
        bodies = mesh.split(only_watertight=False)
        ok_wt = bool(mesh.is_watertight) and mesh.volume > 0
        results.append((ok_wt, f"{name}: watertight={mesh.is_watertight} "
                               f"bodies={len(bodies)} volume={mesh.volume / 1000:.1f} cm3"))
        bb = shape.BoundingBox()
        dims = sorted([bb.xlen, bb.ylen])  # part may be rotated on the bed
        fits = (dims[0] <= min(bed_x, bed_y) - 2 * margin and dims[1] <= max(bed_x, bed_y) - 2 * margin
                and bb.zlen <= bed_z)
        results.append((fits, f"{name}: bbox {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm "
                              f"vs bed {bed_x} x {bed_y} x {bed_z} (margin {margin})"))
        if len(bodies) > 1:
            results.append((False, f"{name}: {len(bodies)} separate bodies in one part file "
                                   f"(floating geometry?)"))


# ---------------------------------------------------------------- interference

def check_interference(items: list, results: list) -> None:
    allowed = getattr(box, "ALLOWED_OVERLAPS", set())
    solids = []
    for it in items:
        s = as_shape(it.shape)
        parts = s.Solids()
        if not parts:
            results.append((False, f"interference: {it.name} has no solid (only faces/shells?)"))
            continue
        solids.append((it.name, parts, s.BoundingBox()))
    n_checked = 0
    for (na, sa, ba), (nb, sb, bb) in itertools.combinations(solids, 2):
        if (ba.xmax < bb.xmin or bb.xmax < ba.xmin or ba.ymax < bb.ymin or bb.ymax < ba.ymin
                or ba.zmax < bb.zmin or bb.zmax < ba.zmin):
            continue
        n_checked += 1
        try:
            # Solid against solid only. OCC's common() of a Compound with a solid
            # returns faces, not the overlap (found 2026-10-23: a planted 300 mm3
            # collision read 200 "mm3" of faces, then 0). Touching parts intersect
            # in a face, which is not a volume, so only solid results count.
            vol = sum(r.Volume() for a in sa for b in sb for r in a.intersect(b).Solids())
        except Exception as e:  # noqa: BLE001
            results.append((False, f"interference {na} x {nb}: boolean failed ({e})"))
            continue
        if vol > OVERLAP_TOL_MM3:
            pair = frozenset({na, nb})
            if pair in allowed:
                print(f"  allowed overlap {na} x {nb}: {vol:.1f} mm3")
            else:
                results.append((False, f"COLLISION {na} x {nb}: {vol:.1f} mm3"))
    results.append((True, f"interference: {len(solids)} items, {n_checked} bbox-overlapping pairs tested"))


# ---------------------------------------------------------------- rendering

def render_all(shapes: dict, items: list) -> None:
    os.makedirs(RENDERS_DIR, exist_ok=True)
    for name, shape in shapes.items():
        render([(shape, (0.35, 0.55, 0.80), 1.0)], os.path.join(RENDERS_DIR, f"part_{name}.png"),
               "iso", title=f"{name} (print orientation)")
        print(f"  rendered part_{name}.png")
    spec = [(as_shape(it.shape), it.color, getattr(it, "opacity", 1.0)) for it in items]
    for view in ("iso", "iso_back", "top", "front", "left"):
        render(spec, os.path.join(RENDERS_DIR, f"assembly_{view}.png"), view, title=f"assembly - {view}")
        print(f"  rendered assembly_{view}.png")
    # without the lid (and anything box.py marks as lid-like) to see inside
    lidless = [(as_shape(it.shape), it.color, getattr(it, "opacity", 1.0)) for it in items
               if not getattr(it, "is_lid", False)]
    for view in ("iso", "top"):
        render(lidless, os.path.join(RENDERS_DIR, f"assembly_open_{view}.png"), view, title=f"lid off - {view}")
        print(f"  rendered assembly_open_{view}.png")
    for name, (origin, normal) in getattr(box, "SECTIONS", {}).items():
        render(spec, os.path.join(RENDERS_DIR, f"section_{name}.png"),
               "front" if abs(normal[1]) > 0.5 else "left", title=f"section {name}", clip=(origin, normal))
        print(f"  rendered section_{name}.png")


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--no-interference", action="store_true")
    args = ap.parse_args()

    results: list = []
    print("export:")
    shapes = export_parts(results)
    print("mesh + bed checks:")
    check_meshes(shapes, results)
    items = box.ASSEMBLY()
    if not args.no_interference:
        print("interference:")
        check_interference(items, results)
    if not args.no_render:
        print("render:")
        render_all(shapes, items)

    print("\nRESULTS")
    failed = 0
    for ok, msg in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {msg}")
        failed += 0 if ok else 1
    measures = params.measure_report()
    print(f"\nMEASURE placeholders still in use: {len(measures)}")
    for line in measures:
        print(f"  - {line}")
    print(f"\n{'FAIL' if failed else 'PASS'}: {failed} check(s) failed. "
          f"(PASS means the model is self-consistent; it does not mean it fits the real board "
          f"until the MEASURE values are measured.)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
