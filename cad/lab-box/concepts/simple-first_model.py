"""Massing sketch of Lab Box concept 'simple-first' (one PETG tub + all-metal C-frame clamp).

NOT the final CAD. It exists so the concept can be seen. Every number comes from
concepts/simple-first.md (and board-mechanical.md for parts the concept does not place).

Frames
  box frame   : origin at the outer NW bottom corner, X east, Y south, Z up (as in the concept).
  world frame : box frame with Y flipped (world y = -box y), so north is up in the top view
                and the renderer's "iso" camera looks from the SE, "iso_back" from the NW.
  Every helper below takes BOX coordinates.

Run:  .venv/Scripts/python.exe concepts/simple-first_model.py
"""
from __future__ import annotations

import math
import os
import sys

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from render import render  # noqa: E402

OUT = os.path.join(HERE, "renders")
TAG = "Concept 'simple-first' - massing sketch, not final"

# ------------------------------------------------------------------ colours
PETG = (0.55, 0.62, 0.72)
METAL = (0.75, 0.75, 0.78)
STEEL = (0.55, 0.57, 0.62)
BRASS = (0.8, 0.65, 0.3)
PCB = (0.1, 0.35, 0.15)
BLACK = (0.1, 0.1, 0.1)
NYLON = (0.95, 0.94, 0.88)
ACRYLIC = (0.6, 0.8, 1.0)
HEATER = (0.85, 0.2, 0.12)
KAPTON = (0.95, 0.6, 0.1)
GREY = (0.45, 0.45, 0.48)

# ------------------------------------------------------------------ geometry helpers (box frame in)


def V(x, y, z):
    return cq.Vector(x, -y, z)


def B(x0, x1, y0, y1, z0, z1):
    """Axis-aligned box from box-frame ranges."""
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, -y1, z0))


def CZ(x, y, z0, z1, d):
    return cq.Solid.makeCylinder(d / 2, z1 - z0, V(x, y, z0), cq.Vector(0, 0, 1))


def CX(x0, x1, y, z, d):
    return cq.Solid.makeCylinder(d / 2, x1 - x0, V(x0, y, z), cq.Vector(1, 0, 0))


def CY(y0, y1, x, z, d):
    return cq.Solid.makeCylinder(d / 2, y1 - y0, V(x, y0, z), cq.Vector(0, -1, 0))


def HEX(x, y, z0, z1, af):
    """Hex prism, flats `af` across, axis vertical (standoffs, nuts)."""
    return (cq.Workplane("XY").workplane(offset=z0).center(x, -y)
            .polygon(6, af / math.cos(math.pi / 6)).extrude(z1 - z0).val())


def BALL(x, y, z, d):
    return cq.Solid.makeSphere(d / 2, V(x, y, z), angleDegrees1=-90, angleDegrees2=90)


def WIRE(pts, d):
    """Polyline cable through box-frame points."""
    segs = []
    for p, q in zip(pts, pts[1:]):
        a, b = V(*p), V(*q)
        segs.append(cq.Solid.makeCylinder(d / 2, (b - a).Length, a, (b - a).normalized()))
    segs += [BALL(*p, d) for p in pts[1:-1]]
    return cq.Compound.makeCompound(segs)


# ------------------------------------------------------------------ parts registry
PARTS = []  # (group, name, shape, rgb, opacity)


def add(group, name, shape, rgb, op=1.0):
    PARTS.append((group, name, shape, rgb, op))


# ------------------------------------------------------------------ key numbers (concept §1-§5)
BOSSES = [(8, 8), (192, 8), (8, 176), (192, 176)]          # lid bosses, inside corners
STANDOFFS = [(81, 20), (177, 20), (81, 146), (177, 146)]   # board holes, box frame
FX, FY = 133.5, 101.0                                      # FPGA centre
PCB_BOT, PCB_TOP = 18.0, 19.6
PKG_TOP = 21.25                                            # max A = 1.65
LEGS_X = (68.5, 189.5)
BAR_X0, BAR_X1 = 62.5, 195.5                               # 133 long, holes at 6/127
BAR_Y0, BAR_Y1 = 91.0, 111.0                               # 20 wide, centred on FPGA Y

# ------------------------------------------------------------------ base tub (PETG)
tub = B(0, 200, 0, 184, 0, 70).cut(B(4, 197, 3, 181, 3, 71))     # W wall 4, others 3, floor 3
tub = tub.fuse(*[CZ(x, y, 3, 70, 9) for x, y in BOSSES])
cuts = [CZ(x, y, 63.3, 71, 4.0) for x, y in BOSSES]                # insert holes 4.0 x 6.7
cuts += [B(-1, 5, 14, 170, 6, 71), B(0.5, 3.5, 10, 174, 6, 71)]    # W panel opening 156x64 + groove
cuts += [B(196, 201, FY + 6 * k - 1.5, FY + 6 * k + 1.5, 24, 60) for k in range(-6, 7)]  # 13 E slots
cuts += [B(130, 154, 180, 185, 40, 71)]                            # S JTAG notch
cuts += [CZ(x, y, -1, 4, 9) for x, y in STANDOFFS]                 # dia 9 floor holes (slide)
cuts += [B(x - 1.7, x + 1.7, 91, 111, -1, 4) for x in (74.5, 174.5)]  # keel slots 3.4 x 20
add("tub", "base tub", tub.cut(*cuts).clean(), PETG)
for x, y in [(12, 12), (188, 12), (12, 172), (188, 172)]:  # clear of fender washers + keel screws
    add("in", "rubber foot", CZ(x, y, -5, 0, 12), BLACK)

# ------------------------------------------------------------------ W I/O panel (PETG) + its hardware
panel = B(0.5, 3.5, 10.2, 173.8, 6, 70)
pc = [B(-1, 5, 22.5, 34.5, 13.9, 22.9)]                                    # PICO USB 12x9
pc += [CX(-1, 5, 54, 13, 8), CX(-1, 5, 60, 13, 8), B(-1, 5, 54, 60, 9, 17)]  # LA grommet 14x8
pc += [CX(-1, 5, FY, 39.6, 38)]                                            # AIR IN grille
pc += [CX(-1, 5, y, z, 3.4) for y in (85, 117) for z in (23.6, 55.6)]      # fan screws
pc += [B(-1, 5, 126, 138, 19, 25)]                                         # FPGA 5V IN (USB-C)
pc += [CX(-1, 5, 148, 46, 12.5), CX(-1, 5, 162, 22, 8.0)]                  # fuse, 12 V jack
panel = panel.cut(*pc)
grille = [CX(0.5, 3.5, FY, 39.6, d0).cut(CX(0, 4, FY, 39.6, d1)) for d0, d1 in ((30, 26), (18, 14))]
grille += [B(0.5, 3.5, FY - 19, FY + 19, 38.6, 40.6), B(0.5, 3.5, FY - 1, FY + 1, 20.6, 58.6)]
add("panel", "W I/O panel", panel.fuse(*grille).clean(), PETG)

fan = B(3.5, 13.5, 81, 121, 19.6, 59.6).cut(CX(3, 14, FY, 39.6, 37)).fuse(CX(3.5, 13.5, FY, 39.6, 17))
add("in", "fan 4010", fan, (0.18, 0.18, 0.2))
add("in", "USB-C 5V socket", B(3.5, 16, 127, 137, 19.5, 24.5).fuse(B(-1.5, 0.5, 125, 139, 17, 27)), METAL)
add("in", "fuse holder", CX(3.5, 44, 148, 46, 12).fuse(CX(-14, 0.5, 148, 46, 15)), BLACK)
add("in", "12V jack", CX(3.5, 18, 162, 22, 9.5).fuse(CX(-2.5, 0.5, 162, 22, 11)), (0.25, 0.25, 0.27))

# ------------------------------------------------------------------ module plate + modules (bay X 4-61)
add("in", "module plate", B(4, 60, 15, 169, 3, 6), PETG)
# Pico 2H on 10 mm standoffs, USB end at the panel
add("in", "Pico standoffs", cq.Compound.makeCompound(
    [CZ(x, y, 6, 16, 3.5) for x in (6.5, 53.5) for y in (22.8, 34.2)]), BRASS)
add("in", "Pico 2H", B(4.5, 55.5, 18, 39, 16, 17).fuse(B(26, 33, 25, 32, 17, 18)), (0.2, 0.75, 0.3))
add("in", "Pico headers", B(5, 55, 18.3, 20.8, 13.5, 16).fuse(B(5, 55, 36.2, 38.7, 13.5, 16)), BLACK)
add("in", "Pico micro-B", B(3.4, 8.5, 24.5, 32.5, 17, 19.8), METAL)
add("in", "logic analyser", B(4, 59, 43, 71, 6, 18).fuse(B(54, 59, 47, 67, 18, 24)), (0.85, 0.12, 0.12))
add("in", "star ground", B(5, 25, 75, 89, 6, 14), (0.95, 0.85, 0.15))
add("in", "MAX31855", B(37, 57.3, 75, 98, 9, 10.6), (0.15, 0.35, 0.9))
add("in", "MAX31855 terminal", B(51, 57.3, 80, 93, 10.6, 19), (0.1, 0.55, 0.25))
add("in", "BME280 standoffs", CZ(22, 98, 6, 26, 4).fuse(CZ(22, 115, 6, 26, 4)), BRASS)
add("in", "BME280", B(20, 45.4, 94, 119.4, 26, 27.6), (0.85, 0.2, 0.75))
add("in", "Si5351", B(38, 59.6, 100, 130.5, 9, 10.6).fuse(B(57, 59.6, 103, 127, 10.6, 13)), (0.1, 0.75, 0.85))
add("in", "AO3400", B(5, 30, 131, 146, 6, 10), (0.55, 0.3, 0.85))
add("in", "INA226", B(33, 60, 131, 151, 9, 12), (0.95, 0.45, 0.6))
add("in", "D4184", B(25, 60, 153, 169, 6, 14), (0.3, 0.85, 0.6))

# ------------------------------------------------------------------ FPGA board dummy (board = box - (76, 15))
add("in", "PCB", B(76, 182, 15, 151, PCB_BOT, PCB_TOP), PCB)
for x, y in STANDOFFS:
    add("in", "board standoff", HEX(x, y, 3, PCB_BOT, 5.5), BRASS)
    add("in", "board screws", cq.Compound.makeCompound([
        CZ(x, y, PCB_TOP, 21.3, 5.5), CZ(x, y, -1, 0, 12), CZ(x, y, -2.65, -1, 5.7)]), STEEL)
add("in", "FPGA", B(FX - 10, FX + 10, FY - 10, FY + 10, PCB_TOP, PKG_TOP), BLACK)
add("in", "FPGA leads", B(FX - 11.1, FX + 11.1, FY - 11.1, FY + 11.1, PCB_TOP, 20.1), (0.7, 0.7, 0.72))


def header(name, x0, x1, y0, y1):
    add("in", name, B(x0, x1, y0, y1, PCB_TOP, 22.1), BLACK)                     # plastic 2.5
    add("in", name + " pins", B(x0 + 0.6, x1 - 0.6, y0 + 0.6, y1 - 0.6, 22.1, 28.1), BRASS)  # 8.5 above PCB
    add("in", name + " Dupont envelope", B(x0, x1, y0, y1, 22.1, 36.1), (0.5, 0.5, 0.55), 0.18)


header("P1", 108.96, 114.04, 78, 78 + 19 * 2.54)
header("P2", 154.96, 160.04, 71, 71 + 22 * 2.54)
header("P3", 122, 122 + 10 * 2.54, 71.96, 77.04)
add("in", "7-seg", B(81, 96, 34, 65, PCB_TOP, 26.8), (0.15, 0.15, 0.15))
add("in", "LED1-4", cq.Compound.makeCompound([B(167.5, 169.5, y, y + 1.2, PCB_TOP, 20.4) for y in (70, 72, 74, 76)]),
    (1.0, 0.15, 0.1))
add("in", "keys", cq.Compound.makeCompound(
    [B(171, 177, y - 3, y + 3, PCB_TOP, 23.1).fuse(CZ(174, y, 23.1, 25, 3.5)) for y in (37.5, 46.5, 55, 63.5)]), BLACK)
add("in", "DIP switch", B(143, 153, 53, 59, PCB_TOP, 23.5), (0.85, 0.15, 0.15))
add("in", "IR receiver", B(173.5, 178.5, 28, 34, PCB_TOP, 26), BLACK)  # verifier centre bx 100, by 16
add("in", "DB9", B(100.6, 131.4, 15, 27, PCB_TOP, 32.2).fuse(B(108, 124, 8, 15, 21.5, 30.5)), (0.62, 0.62, 0.66))
add("in", "VGA", B(134.6, 165.4, 15, 27, PCB_TOP, 32.2).fuse(B(142, 158, 8, 15, 21.5, 30.5)), (0.15, 0.3, 0.75))
add("in", "AS header", B(106, 126, 138.5, 147.5, PCB_TOP, 28.9), BLACK)
add("in", "JTAG header", B(132, 152, 138.5, 147.5, PCB_TOP, 28.9), BLACK)
add("in", "USB-Blaster IDC plug", B(133.5, 150.5, 139.5, 146.5, 28.9, 37.5), (0.3, 0.3, 0.33))
add("in", "JTAG ribbon", B(136.6, 149.3, 142.5, 143.5, 37.5, 44).fuse(B(136.6, 149.3, 142.5, 192, 43, 44)),
    (0.72, 0.72, 0.75))
add("in", "notch foam", B(130, 154, 181, 184, 40, 43), BLACK)
add("in", "power switch", B(77, 85, 128, 138, PCB_TOP, 28), BLACK)
add("in", "switch cap (worst case)", CZ(81, 133, 28, 44.6, 6), (0.85, 0.1, 0.1))
add("in", "USB-B (power only)", B(74, 90, 113, 125, PCB_TOP, 30.6), METAL)
add("in", "DC jack", B(85, 95, 132, 151, PCB_TOP, 30.6), BLACK)
add("in", "R/A DC plug", B(86, 94, 151, 176, 21, 29), (0.28, 0.28, 0.3))

# ------------------------------------------------------------------ the C-frame clamp (concept §5)
add("in", "keel (Al 20x3)", B(BAR_X0, BAR_X1, BAR_Y0, BAR_Y1, 3, 6), METAL)
add("in", "bridge (Al 20x3)", B(BAR_X0, BAR_X1, BAR_Y0, BAR_Y1, 51, 54), METAL)
for x in LEGS_X:  # brass M3 25 + 20, keel top Z6 -> bridge underside Z51
    add("in", "leg 25", HEX(x, FY, 6, 31, 5.5), BRASS)
    add("in", "leg 20", HEX(x, FY, 31, 51, 5.5), (0.72, 0.58, 0.26))
    add("in", "bridge screw", CZ(x, FY, 54, 55.65, 5.7), STEEL)
for x in (74.5, 174.5):  # keel-to-floor M3 + nut through the floor slots
    add("in", "keel nut", HEX(x, FY, 6, 8.4, 5.5), STEEL)
    add("in", "keel screw head", CZ(x, FY, -1.9, 0, 5.5), STEEL)
# back-support post: brass 6 mm F-F standoff + nylon M3x10 pan screw + nylon nut, head top Z 18
add("in", "post standoff", HEX(FX, FY, 6, 12, 5.5), BRASS)
add("in", "post nylon screw+nut", HEX(FX, FY, 12, 14.4, 5.5).fuse(CZ(FX, FY, 14.4, 16, 3), CZ(FX, FY, 16, 18, 5.5)),
    NYLON)
# heater stack
add("in", "pad 0.5", B(FX - 9.5, FX + 9.5, FY - 9.5, FY + 9.5, PKG_TOP, 21.75), KAPTON)
add("in", "spreader block 18x18x14", B(FX - 9, FX + 9, FY - 9, FY + 9, 21.75, 35.75), (0.66, 0.69, 0.76))
hs10 = B(FX - 9, FX + 9, FY - 8.5, FY + 8.5, 35.75, 37.75).fuse(B(FX - 8, FX + 8, FY - 8.25, FY + 8.25, 37.75, 44.55))
add("in", "HS10 resistor", hs10, HEATER)
add("in", "HS10 lugs (N-S)", B(FX - 2, FX + 2, 86, FY - 8.25, 39, 39.8).fuse(B(FX - 2, FX + 2, FY + 8.25, 116, 39, 39.8)),
    METAL)
add("in", "S lug joint sleeve", CY(116, 124, FX, 39.4, 3.5), BLACK)
add("in", "pressure foot 16x16x3", B(FX - 8, FX + 8, FY - 8, FY + 8, 44.55, 47.55), METAL)
add("in", "plunger ball", BALL(FX, FY, 49.05, 3), STEEL)
add("in", "M6 spring plunger", CZ(FX, FY, 49, 65, 6), STEEL)
add("in", "M6 lock nut", HEX(FX, FY, 54, 59, 10), STEEL)
# KSD9700 on the block's S face, long axis E-W, bottom 4.45 up the block
add("in", "KSD9700 thermostat", B(FX - 10.25, FX + 10.25, FY + 9, FY + 12.7, 26.2, 33.7), BLACK)
tie = cq.Compound.makeCompound([
    B(FX - 9.6, FX + 9.6, FY - 9.6, FY - 9, 27.5, 30), B(FX - 9.6, FX - 9, FY - 9.6, FY + 9, 27.5, 30),
    B(FX + 9, FX + 9.6, FY - 9.6, FY + 9, 27.5, 30), B(FX - 10.25, FX + 10.25, FY + 12.7, FY + 13.3, 27.5, 30),
    B(FX - 2, FX + 2, FY - 12.5, FY - 9.6, 27, 30.5)])                       # head on the N face
add("in", "coated SS tie", tie, (0.35, 0.35, 0.4))
# cables: heater pair on the bridge N edge, TC on the S edge, both down the W leg
add("in", "heater wires", WIRE([(FX, 86.5, 39.4), (FX, 89.4, 52.5), (68.5, 89.4, 52.5), (68.5, 89.4, 47),
                                (68.5, 96.3, 45), (68.5, 96.3, 9), (63.5, 96.3, 9), (63.5, 150, 9), (58, 160, 12)],
                               1.8),
    (0.9, 0.1, 0.1))
add("in", "thermocouple", WIRE([(FX, FY, 21.9), (FX - 9, FY, 21.9), (119, FY, 22.5), (119, 112.5, 30),
                                (119, 112.5, 52.5), (68.5, 112.5, 52.5), (68.5, 112.5, 47), (68.5, 105.6, 45),
                                (68.5, 105.6, 13), (63.5, 105.6, 13),
                                (57.3, 90, 15)], 1.2), (0.95, 0.85, 0.1))

# ------------------------------------------------------------------ lid (PETG) + acrylic
lid = B(0, 200, 0, 184, 70, 76.2).cut(B(77, 177, 14, 150, 69, 77), B(71.5, 182.5, 8.5, 155.5, 69, 73.3))
lip = B(4.3, 196.7, 3.3, 180.7, 66, 70.01).cut(B(6.3, 194.7, 5.3, 178.7, 65, 71),
                                               *[CZ(x, y, 65, 71, 10.5) for x, y in BOSSES])
lid = lid.fuse(lip, B(130.4, 153.6, 181, 184, 44, 70.01))                # ribbon tongue
lid = lid.cut(*[CZ(x, y, 69, 77, 3.4) for x, y in BOSSES]).clean()
add("lid", "lid frame", lid, PETG)
add("lid", "lid screws", cq.Compound.makeCompound([CZ(x, y, 76.2, 77.9, 5.5) for x, y in BOSSES]), STEEL)
add("acrylic", "acrylic 110x146x3", B(72, 182, 9, 155, 70.3, 73.3), ACRYLIC, 0.25)


# ------------------------------------------------------------------ views
def scene(groups, opacity=None, keep=None):
    """List of (shape, rgb, op) for render(). `keep` = box-frame solid to intersect with (sections)."""
    out = []
    for g, _n, s, rgb, op in PARTS:
        if g not in groups:
            continue
        if keep is not None:
            s = s.intersect(keep)
            if not s.Solids() or s.Volume() < 1e-3:
                continue
        out.append((s, rgb, (opacity or {}).get(g, op)))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    closed = ("tub", "panel", "lid", "acrylic", "in")
    p = lambda v: os.path.join(OUT, f"simple-first_{v}.png")  # noqa: E731
    # Lid-off iso: the near (S and E) walls above Z 8 are drawn as a faint ghost so the inside reads.
    tub = next(s for g, _n, s, _c, _o in PARTS if g == "tub")
    near = B(186.5, 201, -1, 185, 8, 71).fuse(B(-1, 201, 170.5, 185, 8, 71))
    cutaway = [(tub.cut(near), PETG, 1.0), (tub.intersect(near), PETG, 0.12)] + scene(("panel", "in"))
    jobs = [
        (scene(closed), p("iso"), "iso", f"{TAG} - closed, from SE (acrylic window over the board)", None),
        (scene(closed), p("iso_back"), "iso_back", f"{TAG} - closed, from NW (W I/O panel)", None),
        (cutaway, p("open_iso"), "iso", f"{TAG} - lid off, S + E walls ghosted, from SE", None),
        (scene(("tub", "panel", "in")), p("open_top"), "top", f"{TAG} - lid off, top view (N up, W panel left)",
         None),
    ]
    # Sections: solids are cut by boolean so the cut faces are capped; the render clip sits 0.05 mm
    # into the removed half as a guard. E-W cut at the FPGA Y, keep the N half, look N (W left).
    clip = ((0, -FY - 0.05, 0), (0, 1, 0))
    jobs.append((scene(closed, keep=B(-50, 250, -50, FY, -50, 150)), p("section"), "front",
                 f"{TAG} - section at Y {FY:g} through the FPGA centre, looking N", clip))
    jobs.append((scene(closed, keep=B(56, 201, 60, FY, -6, 78)), p("section_clamp"), "front",
                 f"{TAG} - clamp stack, section at Y {FY:g}, looking N (X 56-200)", clip))
    # N-S cut at the FPGA X, keep the E half, look E: N on the left, S on the right. Shows the HS10
    # lugs, the KSD on the block's S face, P3, the JTAG plug + ribbon and the lid tongue in the notch.
    jobs.append((scene(closed, keep=B(FX, 250, -50, 250, -50, 150)), p("section_ns"), "left",
                 f"{TAG} - section at X {FX:g} through the FPGA centre, looking E (N left)",
                 ((FX - 0.05, 0, 0), (1, 0, 0))))
    for spec, path, view, title, cl in jobs:
        render(spec, path, view=view, title=title, clip=cl)
        print("wrote", path)


if __name__ == "__main__":
    main()
