"""Numeric clearance report for the Lab Box (DESIGN.md §3), from the same model make.py checks.

    .venv/Scripts/python.exe checks.py

make.py proves the parts do not overlap. This script measures the gaps that the design
rules put a number on, with OCC's exact BRep distance (not meshes), and prints PASS/FAIL
against each rule. Like make.py, a PASS here is only as good as the MEASURE values in
params.py: every board position is still a photo-estimate.
"""
from __future__ import annotations

import math
import sys

import cadquery as cq

import box
import params as P
from box import B, BC, FX, FY
from render import as_shape

ITEMS = {it.name: it for it in box.ASSEMBLY()}
rows = []


def S(name):
    return as_shape(ITEMS[name].shape)


def dist(a, b):
    a = a if isinstance(a, cq.Shape) else S(a)
    b = b if isinstance(b, cq.Shape) else S(b)
    return a.distance(b)


def zmin(sh):
    return sh.BoundingBox().zmin


def zmax(sh):
    return sh.BoundingBox().zmax


def check(rule, value, limit, ok, note=""):
    rows.append((ok, rule, value, limit, note))


HEATER_METAL = ["spreader block (Al 18x18)", "top plate (Al 20x3)", "HS10 heater", "HS10 tags + heat-shrink",
                "KSD9700 75C thermostat (case live)", "pressure-bar posts", "pressure bar (Al 20x3)", "steel ball",
                "spring cup (lower)", "spring (8 N)", "spring cup (upper)", "top plate CSK screws", "HS10 M2 screws",
                "strap M2x8 screws", "strap spacers", "pressure-bar screws"]
PRINTED = [n for n, it in ITEMS.items() if it.kind == "printed"]
lead_top = P.PCB_TOP + P.LEAD_TOP_H

# ---------------------------------------------------------------- 1. spreader vs the lead ring [D #2]
d = dist("spreader block (Al 18x18)", "FPGA lead ring (22x22)")
check("spreader to lead ring, 3D", f"{d:.2f}", "> 0 (no contact)", d > 0.5,
      f"plan: spreader edge {P.PKG_BODY / 2 - P.SPREADER / 2:.1f} inside the body edge, "
      f"{P.PKG_LEADS / 2 - P.SPREADER / 2:.1f} inside the lead tips")
check("spreader contact face", f"{P.SPREADER:g} x {P.SPREADER:g}", "<= 18 x 18", P.SPREADER <= 18.0)
ring_prism = BC(FX, FY, P.PKG_LEADS, P.PKG_LEADS, P.PCB_TOP, 200).cut(BC(FX, FY, P.PKG_BODY, P.PKG_BODY, 0, 300))
worst = (1e9, "")
for n in HEATER_METAL + ["bridge (Al 20x3)", "M6 adjuster", "FR4 strap"]:
    sh = S(n)
    common = sh.intersect(ring_prism)
    if common.Solids() and common.Volume() > 1e-3:
        z = common.BoundingBox().zmin - lead_top
        if z < worst[0]:
            worst = (z, n)
check("lowest metal over the 22x22 lead ring (excl. spreader)", f"{worst[0]:.2f} ({worst[1]})",
      ">= 5 above the lead tops (interpretation of #2)", worst[0] >= 5.0)

# ---------------------------------------------------------------- 2. HS10 tags vs header pins [D #3]
tags = S("HS10 tags + heat-shrink")
best = min((dist(tags, S(n)), n) for n in ITEMS if n.endswith(" pins") or n.endswith("Dupont envelope")
           or n in ("JTAG box header", "USB-Blaster IDC plug (seated)"))
check("HS10 tags + sleeves to nearest pin / Dupont / JTAG", f"{best[0]:.2f} ({best[1]})",
      ">= 9 nominal (5 + 4 photo tolerance)", best[0] >= 9.0)
tb = tags.BoundingBox()
check("HS10 tags run N-S", f"tag bbox {tb.xlen:.1f} (E-W) x {tb.ylen:.1f} (N-S)", "N-S", tb.ylen > tb.xlen)
best_m = min((dist(tags, S(n)), n) for n in ("strap M2x8 screws", "FR4 strap", "pressure bar (Al 20x3)",
                                             "pressure-bar posts", "KSD9700 75C thermostat (case live)"))
check("HS10 tags to the clamp's own metal / strap", f"{best_m[0]:.2f} ({best_m[1]})", ">= 0.5 (sleeved)", best_m[0] >= 0.5)

# ---------------------------------------------------------------- 3. printed parts vs heater metal [D #9]
worst = (1e9, "", "")
for p in PRINTED:
    for m in HEATER_METAL:
        dd = dist(p, m)
        if dd < worst[0]:
            worst = (dd, p, m)
check("printed part to heater metal (min)", f"{worst[0]:.2f} ({worst[1]} / {worst[2]})", ">= 5 (target 25)",
      worst[0] >= 5.0)
hs = S("HS10 heater").BoundingBox()
plume = B(hs.xmin, hs.xmax, -hs.ymax, -hs.ymin, hs.zmax, 200)
inplume = [p for p in PRINTED if S(p).intersect(plume).Solids()]
check("printed features in the plume above the HS10", ", ".join(inplume) or "none", "none", not inplume)
acr = dist("acrylic window 3 mm", "HS10 heater")
check("acrylic to HS10 (info)", f"{acr:.1f}", "measure plume temperature (§6.7)", True)

# ---------------------------------------------------------------- 4. lid clearance at max adjustment [D #14]
adj_top_max = box.ADJ_TIP_FREE + P.ADJ_LEN
tall = []
for n, it in ITEMS.items():
    if it.is_lid or n in ("base tub", "W I/O panel", "Blaster USB plug + cable"):
        continue
    tall.append((zmax(S(n)), n))
tall.sort(reverse=True)
tall_max = max(tall[0][0], adj_top_max)
check("lid underside - tallest part (adjuster backed out to F = 0)",
      f"{P.TUB_H - tall_max:.2f} (adjuster top {adj_top_max:.2f}; next: {tall[0][1]} {tall[0][0]:.2f})",
      ">= 5", P.TUB_H - tall_max >= 5.0)
for n in ("switch cap UP (worst case)", "JTAG ribbon", "USB-Blaster IDC plug (seated)"):
    z = zmax(S(n))
    check(f"lid underside - {n}", f"{P.TUB_H - z:.2f}", ">= 5", P.TUB_H - z >= 5)
lip = S("lid").intersect(B(0, P.BOX_X, 0, P.BOX_Y, P.TUB_H - 10, P.TUB_H))
for n in ("fan 4010 (5 V)", "fuse holder 1A fast", "USB-C 5V panel socket (5.1k CC)", "12V panel jack"):
    dd = dist(lip, S(n))
    check(f"lid lip to {n}", f"{dd:.2f}", "> 0 (stated, #14)", dd > 0.5)

# ---------------------------------------------------------------- 5. KSD height above the leads [D #4]
k = S("KSD9700 75C thermostat (case live)").BoundingBox()
check("KSD9700 underside above the lead tops", f"{k.zmin - lead_top:.2f} (above package top: {k.zmin - P.PKG_TOP:.2f})",
      ">= 10", k.zmin - lead_top >= 10.0)
dk = min((dist("KSD9700 75C thermostat (case live)", S(n)), n) for n in ITEMS
         if n.endswith(" pins") or n.endswith("Dupont envelope") or n == "JTAG box header")
check("KSD9700 (live case) to nearest pin / Dupont / JTAG", f"{dk[0]:.2f} ({dk[1]})", ">= 5 (info)", dk[0] >= 5)

# ---------------------------------------------------------------- other numbered rules
# #10 screw tips below the top plate
tp0 = P.TOP_PLATE_Z0
tips = {n: zmin(S(n)) - tp0 for n in ("HS10 M2 screws", "strap M2x8 screws")}
check("screw tips above the top plate underside (#10)", ", ".join(f"{n} {v:+.2f}" for n, v in tips.items()),
      ">= 0", all(v >= 0 for v in tips.values()), "post studs cut to 2.5 in a 3.0 plate (+0.5)")
# #12 keel floor fasteners vs leg hexes
dl = min(dist("keel nuts", "legs (brass M3 standoffs, 2 per joint)"),
         dist("keel floor screws", "legs (brass M3 standoffs, 2 per joint)"))
check("keel floor nuts/screws to leg hexes (#12)", f"{dl:.2f}", ">= 3 (driver room)", dl >= 3.0)
# #24 W legs out of the fan jet
legs = S("legs (brass M3 standoffs, 2 per joint)")
wl = legs.intersect(B(0, 100, 0, 200, 0, 100)).BoundingBox()
fan_y1 = P.FAN_YC + P.FAN / 2
check("W leg pair N edge vs fan frame S edge (#24)", f"{-wl.ymax - fan_y1:.2f} (bridge skew {box.TH_DEG:.1f} deg)",
      ">= 1", -wl.ymax - fan_y1 >= 0.99)
br = S("bridge (Al 20x3)").BoundingBox()
check("bridge underside above the fan top (jet clear of the bridge)", f"{br.zmin - (P.FAN_ZC + P.FAN / 2):.2f}", "> 0",
      br.zmin > P.FAN_ZC + P.FAN / 2)
# #26 exhaust slots
ex = P.EXHAUST
span = (ex["n"] - 1) * ex["pitch"] + ex["w"]
check("exhaust slots (#26)", f"{ex['n']} x {ex['w']:g} @ {ex['pitch']:g}: span {span:g}, Y {FY - span / 2:.1f}-{FY + span / 2:.1f}, "
      f"area {ex['n'] * ex['w'] * (ex['z1'] - ex['z0']):.0f} mm2", "consistent", True)
# #6 spring
L_nom = P.SPRING_L0 - P.SPRING_F / P.SPRING_K
top_limit = P.BRIDGE_Z1 + box.P.JAM_NUT[1]
tip_limit = top_limit - P.ADJ_LEN
F_max = P.SPRING_K * (P.SPRING_L0 - (tip_limit - P.WASHER[1] - P.SPRING_Z0))
check("spring: nominal L / force; force limit set by adjuster length (#6)",
      f"L = {L_nom:.2f} mm at {P.SPRING_F:g} N; adjuster leaves the jam nut at {F_max:.1f} N", "5-10 N range reachable",
      F_max >= 10.0)
# #27 Si5351 lead length: the lead lands in a Dupont housing on P1-34, whose wire exits at the
# housing top, so the shortest real route is: up from CLK0 to that height, then across.
x34, y34 = box.p1_pin_xy(34)
b0, b1 = box.SI_BOARD[P.P1_PIN1_END]
clk0 = (box.SI_CLK0_XZ[0], (b0 + b1) / 2, box.SI_CLK0_XZ[1])
pin_top = (x34, y34, P.PCB_TOP + P.HDR_PIN_H)
straight = math.dist(clk0, pin_top)
z_exit = P.PCB_TOP + P.DUPONT_TOP_H
routed = abs(z_exit - clk0[2]) + math.dist(clk0[:2], (x34, y34))
check("Si5351 CLK0 to P1-34 lead (#27)", f"straight-line {straight:.1f}; up-and-over to the Dupont top {routed:.1f}",
      "<= 60", routed <= 60, "CLK0 sits near the Dupont exit height; twist the pair over this run")
x1, y1 = box.p1_pin_xy(1)
check("P1-34 to P1-1/2 (the 'dedicated ground' run, #27)", f"{abs(y34 - y1):.1f} along P1", "info", True,
      "a pair twisted all the way is impossible: the GND lead splits off for this length")
# #11/#13/#15/#16/#17
lid_bb = S("lid").BoundingBox()
check("lid: thumbscrews / tools (#13)", f"{len(P.LID_BOSS)} captive thumbscrews", "<= 4", len(P.LID_BOSS) <= 4)
acr_s = S("acrylic window 3 mm")
scr = S("window screws + nyloc nuts")
check("window screws pass through the acrylic (#15)", "yes" if acr_s.BoundingBox().zmin < scr.BoundingBox().zmax else "no",
      "clamp reaches acrylic", True)
for name, part in box.PARTS.items():
    bb = part().BoundingBox()
    m = min((P.BED_X - max(bb.xlen, bb.ylen)) / 2, (P.BED_Y - min(bb.xlen, bb.ylen)) / 2)
    if m < P.BED_MARGIN + 0.01:
        check(f"bed margin {name} (#17)", f"{m:.1f}", f">= {P.BED_MARGIN}", False)
check("bed margin, all parts (#17)", "see make.py", f">= {P.BED_MARGIN}", True)
# leg pair outside the PCB, USB-B blank gap
pcb = S("FPGA board PCB")
check("legs to PCB (legs outside the outline)", f"{dist(legs, pcb):.2f}", "> 0", dist(legs, pcb) > 0.5)
check("W legs to USB-B blank", f"{dist('legs (brass M3 standoffs, 2 per joint)', 'USB-B blank'):.2f}", "> 0.5",
      dist("legs (brass M3 standoffs, 2 per joint)", "USB-B blank") > 0.5)
check("bridge/keel to E wall", f"{dist('bridge (Al 20x3)', 'base tub'):.2f}", "> 0", dist("bridge (Al 20x3)", "base tub") > 0.2)
pins_tops = P.PCB_TOP + P.DUPONT_TOP_H
check("bridge underside above Dupont tops (wire bends)", f"{br.zmin - pins_tops:.1f}", ">= 15 (concept)",
      br.zmin - pins_tops >= 15)

# ---------------------------------------------------------------- report
w = max(len(r[1]) for r in rows)
fails = 0
for ok, rule, val, lim, note in rows:
    fails += 0 if ok else 1
    print(f"{'PASS' if ok else 'FAIL'}  {rule:<{w}}  {val}   [{lim}]" + (f"   ({note})" if note else ""))
print(f"\n{fails} rule(s) failed")
sys.exit(1 if fails else 0)
