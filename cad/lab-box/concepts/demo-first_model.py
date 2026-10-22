"""Massing sketch of Lab Box concept 'demo-first' (Glass-Top Lab Bench).

A visual sketch, not the design: plain boxes and cylinders at the positions and
sizes the concept (demo-first.md) states. Every board position is a photo-estimate.

    .venv/Scripts/python.exe concepts/demo-first_model.py

Frame: the concept's own (X east from the board W edge, Y SOUTH from the board N
edge, Z up from the inside floor). That frame is left-handed, so every helper here
maps it to a right-handed world (x = X, y = -Y, z = Z). Renders are therefore not
mirrored: the top view has N up and E right, the 'front' camera stands at the S
face where the visitor stands.
"""
from __future__ import annotations

import math
import os
import sys

import cadquery as cq

LAB = r"C:/Users/Alex/Documents/GitHub/LycoChip/cad/lab-box"
sys.path.insert(0, LAB)
from render import as_shape, render  # noqa: E402

OUT = os.path.join(LAB, "concepts", "renders")
NAME = "demo-first"

# ----------------------------------------------------------------- colours
PETG = (0.55, 0.62, 0.72)
PLATE = (0.66, 0.72, 0.82)      # I/O plates: PETG, lighter so they read as separate
ASA = (0.95, 0.50, 0.15)
METAL = (0.75, 0.75, 0.78)
ALU2 = (0.62, 0.64, 0.70)       # the angle, a shade darker than the foot
BRASS = (0.80, 0.65, 0.30)
PCB = (0.10, 0.35, 0.15)
BLACK = (0.10, 0.10, 0.10)
BEZEL = (0.16, 0.16, 0.19)
ACRYL = (0.60, 0.80, 1.00)
DUCT = (0.25, 0.50, 0.92)
KAPTON = (0.80, 0.45, 0.05)
HS10C = (0.92, 0.78, 0.25)
FR4 = (0.78, 0.80, 0.50)
NYLON = (0.95, 0.95, 0.92)
RIBBON = (0.82, 0.82, 0.86)
RED = (0.90, 0.12, 0.12)
MOD = {  # modules: distinct saturated colours
    "Pico 2 CONTROL": (0.30, 0.80, 0.30),
    "Logic analyser": (0.55, 0.25, 0.75),
    "Si5351 CLOCK": (0.95, 0.80, 0.10),
    "MAX31855 CHIP TEMP": (0.90, 0.15, 0.15),
    "D4184 HEAT DRIVE": (0.10, 0.70, 0.70),
    "Star GND block": (1.00, 0.50, 0.75),
    "AO3400 AIR DRIVE": (0.60, 0.85, 0.20),
    "INA226 BOARD POWER": (0.20, 0.35, 0.90),
    "BME280 AIR TEMP": (0.85, 0.20, 0.60),
}

# ----------------------------------------------------------------- geometry helpers (concept frame in, world out)

def W(p):
    return cq.Vector(p[0], -p[1], p[2])


def B(x0, x1, y0, y1, z0, z1):
    """Axis-aligned box from concept-frame extents."""
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, -y1, z0))


def CZ(x, y, d, z0, z1):
    """Vertical cylinder."""
    return cq.Workplane("XY").circle(d / 2).extrude(z1 - z0).translate((x, -y, z0))


def ROD(p0, p1, d):
    """Cylinder between two concept-frame points."""
    a, b = W(p0), W(p1)
    v = b - a
    return cq.Workplane("XY").add(cq.Solid.makeCylinder(d / 2, v.Length, a, v.normalized()))


def HEX(x, y, af, z0, z1):
    return cq.Workplane("XY").polygon(6, af / math.cos(math.pi / 6)).extrude(z1 - z0).translate((x, -y, z0))


def SPH(p, r):
    return cq.Workplane("XY").sphere(r).translate(W(p))


PARTS = []  # (name, shape, colour, opacity, group)


def add(name, wp, colour, opacity=1.0, group="box"):
    PARTS.append((name, as_shape(wp), colour, opacity, group))


# ----------------------------------------------------------------- key numbers (demo-first.md §1, §4)
PCB_BOT, PCB_T = 16.0, 1.6
PCB_TOP = PCB_BOT + PCB_T                       # 17.6
FX, FY = 57.5, 86.0                             # FPGA centre
HOLES = [(5, 5), (101, 5), (5, 131), (101, 131)]
LID_UNDER = 70.6

# ================================================================= base enclosure (PETG)
base = B(-79, 117, -9, 169, -3, LID_UNDER).cut(B(-76, 114, -6, 166, 0, 90))
for x, y in HOLES:                                              # board bosses Ø8 x 6
    base = base.union(CZ(x, y, 8, 0, 6))
for x, y in [(-71, 0), (-14, 0), (-55, 55), (-14, 108), (-71, 160), (-14, 160)]:
    base = base.union(CZ(x, y, 6, 0, 5))                        # tray bosses, 5 mm
LID_BOSSES = [(-72, -2), (110, -2), (-72, 162), (110, 162), (19, -2), (19, 162)]
for x, y in LID_BOSSES:                                         # hanging lid bosses Ø8 x 10
    base = base.union(CZ(x, y, 8, 60.6, LID_UNDER))
for i in range(10):                                             # intake: W wall, 10 slots 3 x 56
    y0 = 62 + i * (50 - 3) / 9
    base = base.cut(B(-80, -75, y0, y0 + 3, 8, 64))
for i in range(14):                                             # exhaust: E wall, 14 slots 3 x 46
    y0 = 50 + i * (70 - 3) / 13
    base = base.cut(B(113, 118, y0, y0 + 3, 20, 66))
APERTURES = {  # N wall I/O plates: (x0, x1, z0, z1)
    "POWER plate": (-62, -6, 38, 62),
    "DATA plate": (-74, -20, 6, 24),
    "RS-232/VGA blank": (24, 90, 14, 34),
    "JTAG plate": (104, 114, 2, 18),
}
for x0, x1, z0, z1 in APERTURES.values():
    base = base.cut(B(x0, x1, -10, -5, z0, z1))
base = base.cut(B(46.5, 68.5, 75, 97, -4, 0.5))                 # post access hole 22 x 22
add("base", base, PETG)
add("floor plug CLAMP POST ADJ", B(46.5, 68.5, 75, 97, -3, 0), PLATE)
for x, y in [(-73, -4), (113, -4), (-73, 164), (113, 164)]:
    add("foot", CZ(x, y, 10, -6.4, -3), BLACK)

# I/O plates, 2.5 thick, flush with the outside
for name, (x0, x1, z0, z1) in APERTURES.items():
    p = B(x0, x1, -9, -6.5, z0, z1)
    if name == "POWER plate":
        p = p.cut(B(-52.5, -43.5, -10, -6, 48.25, 51.75)).cut(ROD((-18, -10, 50), (-18, -5, 50), 11))
    if name == "DATA plate":
        p = p.cut(B(-68, -59, -10, -6, 12, 17)).cut(B(-42, -30, -10, -6, 13, 21))
    if name == "JTAG plate":
        p = p.cut(ROD((110, -10, 5), (110, -5, 5), 5))
    add(name, p, PLATE)
add("USB-C 5V inlet", B(-53, -43, -6.5, 8, 46.5, 53.5), METAL)
add("12V barrel jack", ROD((-18, -9, 50), (-18, 12, 50), 10.8), BLACK)

# ================================================================= lid (ring + acrylic + bezel)
ring = B(-79, 117, -9, 169, LID_UNDER, 75.6).cut(B(-67, 105, 3, 157, 60, 90)).cut(
    B(-73.3, 111.3, -3.3, 163.3, 72.4, 80))
add("lid ring", ring, PETG, group="lid")
skirt = B(-75.6, 113.6, -5.6, 165.6, 67.6, LID_UNDER).cut(B(-73.6, 111.6, -3.6, 163.6, 60, 80))
add("lid skirt", skirt, PETG, group="lid")
add("acrylic window", B(-73, 111, -3, 163, 72.4, 75.4), ACRYL, 0.25, group="lid")
add("bezel", B(-79, 117, -9, 169, 75.6, 78.6).cut(B(-67, 105, 3, 157, 60, 90)), BEZEL, group="lid")
for x, y in LID_BOSSES:                                         # 6 x M3 x 16 at the boss axes
    add("lid screw", CZ(x, y, 3, 62.6, 78.6).union(CZ(x, y, 5.5, 78.6, 80.2)), METAL, group="lid")

# ================================================================= FPGA board dummy
for x, y in HOLES:
    add("standoff", HEX(x, y, 5.5, 6, PCB_BOT), BRASS)
    add("board screw", CZ(x, y, 5.5, PCB_TOP, PCB_TOP + 2.5), METAL)
pcb = B(0, 106, 0, 136, PCB_BOT, PCB_TOP)
for x, y in HOLES:
    pcb = pcb.cut(CZ(x, y, 3.2, 10, 20))
add("PCB", pcb, PCB)
add("FPGA", B(FX - 10, FX + 10, FY - 10, FY + 10, PCB_TOP, PCB_TOP + 1.55), BLACK)
add("FPGA leads", B(FX - 11, FX + 11, FY - 11, FY + 11, PCB_TOP, PCB_TOP + 0.4).cut(
    B(FX - 10, FX + 10, FY - 10, FY + 10, 0, 30)), METAL)

PIN_TOP = PCB_TOP + 2.54 + 5.97                                 # 26.1, 3M mating length (listing)


def header(name, axis, c, a0, rows):
    """2-row 2.54 header: black body + two pin-row bars. axis 'NS' runs along Y."""
    L = rows * 2.54
    if axis == "NS":
        add(name, B(c - 2.54, c + 2.54, a0, a0 + L, PCB_TOP, PCB_TOP + 2.54), BLACK)
        for dx in (-1.27, 1.27):
            add(name + " pins", B(c + dx - 0.32, c + dx + 0.32, a0 + 0.95, a0 + L - 0.95, PCB_TOP + 2.54, PIN_TOP), BRASS)
    else:
        add(name, B(a0, a0 + L, c - 2.54, c + 2.54, PCB_TOP, PCB_TOP + 2.54), BLACK)
        for dy in (-1.27, 1.27):
            add(name + " pins", B(a0 + 0.95, a0 + L - 0.95, c + dy - 0.32, c + dy + 0.32, PCB_TOP + 2.54, PIN_TOP), BRASS)


header("P1", "NS", 35.5, 62.63, 19)          # 2x19, X 35.5, Y 62.6..110.9
header("P2", "NS", 81.5, 56.05, 22)          # 2x22, X 81.5, Y 56..112
header("P3", "EW", 59.5, 45.8, 10)           # 2x10, Y 59.5, X 45.8..71.2
# P1 pin 1 assumed at S (P1-34 at Y 69): Si5351 N site active, CLK-IN shroud on P1-31..38
add("CLK IN shroud (ASA)", B(32.0, 39.0, 61.7, 73.7, PCB_TOP + 2.54, PCB_TOP + 2.54 + 9), ASA)

# N edge: PS/2, DB9, VGA (D-sub flange at the PCB edge, shell out ~6 mm)
add("PS/2", B(8, 22, -1, 12, PCB_TOP, PCB_TOP + 13), METAL)
for nm, x0, col in [("DB9", 24.1, BLACK), ("VGA", 58.6, (0.15, 0.30, 0.75))]:
    add(nm, B(x0 + 0.8, x0 + 30.0, 0, 10, PCB_TOP, PCB_TOP + 12.0), col)
    add(nm + " flange", B(x0, x0 + 30.8, -1, 0, PCB_TOP, PCB_TOP + 12.6), METAL)
    add(nm + " shell", B(x0 + 7, x0 + 23.8, -6, -1, PCB_TOP + 2.2, PCB_TOP + 10.4), METAL)
add("IR receiver", B(98, 102, 13, 19, PCB_TOP, PCB_TOP + 5), BLACK)
# W edge: LCD socket, USB-B (blanked), power switch; S edge: DC jack
add("LCD 1x20 socket", B(0.5, 3.0, 36, 86.8, PCB_TOP, PCB_TOP + 8.5), BLACK)
add("USB-B (power only)", B(0, 16, 99, 111, PCB_TOP, PCB_TOP + 10.6), METAL)
add("USB-B blank + pull tab", B(-0.5, 0, 100, 110, PCB_TOP + 1, PCB_TOP + 9.6).union(
    B(-0.5, 0, 102.5, 107.5, PCB_TOP + 9.6, PCB_TOP + 17)), PLATE)
add("power switch", B(1, 9, 113, 123, PCB_TOP, PCB_TOP + 8.5), BLACK)
add("power switch cap (UP = DC)", CZ(5, 118, 6, PCB_TOP + 8.5, PCB_TOP + 20), RED)
add("DC jack (faces S)", B(9, 19, 117, 136, PCB_TOP, PCB_TOP + 11), BLACK)
add("DC right-angle plug", B(9.5, 18.5, 136, 146, PCB_TOP + 1, PCB_TOP + 10), BLACK)
add("5V pigtail", ROD((14, 146, PCB_TOP + 5.5), (14, 152, PCB_TOP + 5.5), 4).union(
    ROD((14, 152, PCB_TOP + 5.5), (-9, 152, 12), 4)), BLACK)
# top-side parts the visitor sees
add("7-seg display", B(5, 20, 19, 50, PCB_TOP, PCB_TOP + 7.2), BLACK)
add("7-seg face", B(5.8, 19.2, 20, 49, PCB_TOP + 7.2, PCB_TOP + 7.5), RED)
for y in (22.5, 31.5, 40, 48.5):
    add("key", B(95, 101, y - 3, y + 3, PCB_TOP, PCB_TOP + 3.5).union(CZ(98, y, 3.5, PCB_TOP + 3.5, PCB_TOP + 5)), BLACK)
for y in (54.5, 56.5, 58.5, 60.5):
    add("LED", B(91.5, 93.5, y - 0.6, y + 0.6, PCB_TOP, PCB_TOP + 0.8), (1.0, 0.2, 0.1))
add("buzzer", CZ(40, 41, 12, PCB_TOP, PCB_TOP + 9.5), BLACK)
add("DIP switch", B(67, 77, 38, 44, PCB_TOP, PCB_TOP + 4), RED)
add("SDRAM", B(88, 98, 73, 103, PCB_TOP, PCB_TOP + 1.2), BLACK)
add("RESET key", B(87, 93, 125, 131, PCB_TOP, PCB_TOP + 5), BLACK)
# AS and JTAG 2x5 box headers (9.3 tall, listing), IDC plug in JTAG
for nm, xc in [("AS box header", 40.0), ("JTAG box header", 66.0)]:
    add(nm, B(xc - 10, xc + 10, 124, 132, PCB_TOP, PCB_TOP + 9.3).cut(
        B(xc - 8.8, xc + 8.8, 125.2, 130.8, PCB_TOP + 2.4, 40)), BLACK)
add("USB-Blaster IDC plug", B(57.4, 74.6, 125.4, 130.6, PCB_TOP + 2.4, PCB_TOP + 17.5), (0.30, 0.30, 0.33))
ribbon = B(59.65, 72.35, 127.5, 128.5, PCB_TOP + 17.5, PCB_TOP + 29).union(
    B(59.65, 72.35, 127.5, 142, PCB_TOP + 29, PCB_TOP + 30)).union(
    B(59.65, 72.35, 141, 142, 14, PCB_TOP + 29))
add("JTAG ribbon (to PCB+30)", ribbon, RIBBON)
add("USB-Blaster dongle (size MEASURE)", B(40, 100, 142, 163, 0, 14), (0.22, 0.22, 0.26))
add("dongle USB cable", ROD((100, 152, 5), (112, 152, 5), 4).union(SPH((110, 152, 5), 2)).union(
    ROD((110, 152, 5), (110, -20, 5), 4)), BLACK)

# ================================================================= heater stack (§5), Z = PCB top + offsets
Z_INS = PCB_TOP + 2.15         # top of Kapton/paste
Z_FOOT = PCB_TOP + 7.65        # top of Al foot
Z_ANG = PCB_TOP + 9.65         # top of angle's horizontal leg = HS10 base
Z_VLEG = PCB_TOP + 20.65       # vertical leg top
Z_CAP = PCB_TOP + 19.95        # cap top
add("Kapton + paste", B(FX - 9, FX + 9, FY - 9, FY + 9, PCB_TOP + 1.55, Z_INS), KAPTON)
add("Al foot 18x18x5.5", B(FX - 9, FX + 9, FY - 9, FY + 9, Z_INS, Z_FOOT), METAL)
angle = B(FX - 10, FX + 10, FY - 14, FY + 14, Z_FOOT, Z_ANG).union(
    B(FX + 8, FX + 10, FY - 14, FY + 14, Z_ANG, Z_VLEG))
add("Al angle 20x20x2", angle, ALU2)
hs = B(49.4, 65.3, 78, 94, Z_ANG, Z_ANG + 1.5).union(ROD((57.35, 78, Z_ANG + 4.4), (57.35, 94, Z_ANG + 4.4), 8.5))
for xf in (49.4, 52.1, 61.4, 64.1):
    hs = hs.union(B(xf, xf + 1.2, 78, 94, Z_ANG, Z_CAP - 1.5))
add("HS10 18-22R", hs, HS10C)
for y0, y1 in [(71, 78), (94, 101)]:
    add("HS10 lug", B(56.3, 58.3, y0, y1, Z_ANG + 3.5, Z_ANG + 4.3), METAL)
add("Kapton (KSD)", B(67.5, 68.0, 80, 92, PCB_TOP + 12.5, PCB_TOP + 21), KAPTON)
add("KSD9700 75C", B(68.0, 71.7, 81, 91, PCB_TOP + 13, PCB_TOP + 20.5), BLACK)
add("FR4 strap", B(71.7, 73.3, 73, 99, PCB_TOP + 13.75, PCB_TOP + 19.75), FR4)
cap = B(FX - 8, FX + 8, FY - 8, FY + 8, Z_CAP - 1.5, Z_CAP).cut(
    # 90 deg countersink, Ø3 at the top face; frustum (not an apex) so the boolean stays valid
    cq.Workplane("XY").add(cq.Solid.makeCone(0.3, 1.6, 1.3, W((FX, FY, Z_CAP - 1.2)), cq.Vector(0, 0, 1))))
add("Al pressure cap", cap, METAL)

# ================================================================= clamp frame + arm (§6, §7), ASA
frame = B(-43, -8, 76, 96, 0, 8)                                  # foot
frame = frame.union(B(-36, -8, 78, 94, 8, 47.6))                  # mast fin, 16 thick
frame = frame.union(B(-36, -8, 82, 90, 47.6, 59.6))               # fin above shoulders, 8 thick
frame = frame.union(B(-8, 66, 71, 101, 0, 8))                     # sole under the PCB
for dx, dy in [(0, 0), (6, 0), (-6, 0), (0, 6), (0, -6)]:          # 5 insert sites
    frame = frame.cut(CZ(FX + dx, FY + dy, 3.0 if (dx, dy) == (0, 0) else 4.0, -1, 9))
HINGE, LATCH, ZPIN = -32.0, -14.0, 53.6
for xp in (HINGE, LATCH):
    frame = frame.cut(ROD((xp, 70, ZPIN), (xp, 102, ZPIN), 3.4))
add("clamp frame (foot+mast+sole)", frame, ASA)

ARM_LO, ARM_HI = 47.6, 59.6
arm = B(-8, 64.5, 78, 94, ARM_LO, ARM_HI)
arm = arm.union(B(-38, -8, 78, 82, ARM_LO, ARM_HI)).union(B(-38, -8, 90, 94, ARM_LO, ARM_HI))   # forked root
arm = arm.union(CZ(FX, FY, 14, 41.6, 60.0))                                                   # plunger barrel
arm = arm.cut(CZ(FX, FY, 6.0, 43.1, 61))                                                      # bore
arm = arm.cut(CZ(FX, FY, 3.4, 41, 43.2))                                                      # lip hole
arm = arm.cut(B(FX - 1.5, FX + 1.5, FY, FY + 9, 50, 58))                                      # force window, S side
arm = arm.cut(HEX(FX, FY, 5.7, 56.8, 59.4))                                                   # captive nut pocket
for xp in (HINGE, LATCH):
    arm = arm.cut(ROD((xp, 70, ZPIN), (xp, 102, ZPIN), 3.4))
add("heater arm + barrel", arm, ASA)
add("hinge pin M3x20", ROD((HINGE, 76, ZPIN), (HINGE, 96, ZPIN), 3.0), METAL)
add("latch pin (knurled)", ROD((LATCH, 76, ZPIN), (LATCH, 98, ZPIN), 3.0).union(
    ROD((LATCH, 98, ZPIN), (LATCH, 102, ZPIN), 8)), METAL)

# plunger: M3 SHCS head lifted 2 mm off the lip, shank through lip, acorn dome in the cap countersink
Z_HEAD = 43.1 + 2.0
add("plunger head", CZ(FX, FY, 5.5, Z_HEAD, Z_HEAD + 3), METAL)
add("plunger shank", CZ(FX, FY, 3.0, 39.85, Z_HEAD), METAL)
DOME_R = 2.75
dome_c = Z_CAP + math.sqrt(DOME_R ** 2 - 1.5 ** 2)                 # dome seated on the Ø3 countersink rim
acorn = CZ(FX, FY, 5.5, dome_c, 41.3).union(SPH((FX, FY, dome_c), DOME_R).cut(B(40, 75, 70, 100, dome_c, 60)))
add("acorn nut (4.2 tall: the most that fits)", acorn, METAL)
Z_SPR0, Z_SPR1 = Z_HEAD + 3, Z_HEAD + 3 + 6.0                     # installed length L_i ~ 6
helix = cq.Wire.makeHelix(pitch=1.2, height=Z_SPR1 - Z_SPR0, radius=2.4)
spring = cq.Workplane("XZ").center(2.4, 0).circle(0.3).sweep(cq.Workplane("XY").add(helix), isFrenet=True)
add("spring", spring.translate((FX, -FY, Z_SPR0)), (0.35, 0.35, 0.40))
add("spring washer", CZ(FX, FY, 5.6, Z_SPR1, Z_SPR1 + 0.5), METAL)
add("preload screw", CZ(FX, FY, 3.0, Z_SPR1 + 0.5, 62.4).union(CZ(FX, FY, 5.5, 62.4, 65.4)), METAL)
add("captive nut", HEX(FX, FY, 5.5, 57.0, 59.4), METAL)
add("jam nut", HEX(FX, FY, 5.5, 60.0, 62.4), METAL)

# back-support post under the plunger
add("post screw", CZ(FX, FY, 3.0, 0.5, 13.25), BRASS)
add("post jam nut", HEX(FX, FY, 5.5, 8, 10.4).cut(CZ(FX, FY, 3.0, 0, 20)), METAL)
add("post nylon acorn", CZ(FX, FY, 5.5, 11.5, 13.25).union(
    SPH((FX, FY, 13.25), 2.75).cut(B(40, 75, 70, 100, 0, 13.25))), NYLON)

# ================================================================= air path (§8)
duct = B(-76, -66, 62, 114, 0, 65).cut(B(-77, -67, 63, 113, 1, 64))
duct = duct.cut(ROD((-68, 88, 44), (-65, 88, 44), 38))
add("intake duct + shield", duct, DUCT)
fan = B(-66, -56, 68, 108, 24, 64).cut(ROD((-67, 88, 44), (-55, 88, 44), 38))
add("40 mm fan frame", fan, BLACK)
rotor = ROD((-65, 88, 44), (-57, 88, 44), 15)
for k in range(7):
    a = k * 2 * math.pi / 7
    blade = cq.Workplane("XY").box(6, 1.2, 11, centered=(False, True, False)).rotate((0, 0, 0), (1, 0, 0), 25)
    blade = blade.translate((0, 0, 7)).rotate((0, 0, 0), (1, 0, 0), math.degrees(a)).translate((-64, -88, 44))
    rotor = rotor.union(blade)
add("fan rotor", rotor, (0.30, 0.30, 0.34))
add("BME280 card", B(-72, -70.4, 63, 88.4, 2, 27.4), MOD["BME280 AIR TEMP"])
add("BME280 sensor", B(-70.4, -69.4, 74, 77, 13, 16), METAL)

# ================================================================= module tray (§9), plate Z 5..8
tray = B(-75.6, -8.4, -5.6, 165.6, 5, 8)
tray = tray.cut(B(-80, -65.6, 61.6, 114.4, 0, 10)).cut(B(-43.4, -7, 75.6, 96.4, 0, 10))
add("module tray", tray, PETG)
T = 8.0


def board_module(name, x0, x1, y0, y1, colour, h_pcb=3.0, ghost=False):
    op, grp = (0.3, "ghost") if ghost else (1.0, "box")
    add(name, B(x0, x1, y0, y1, T + h_pcb, T + h_pcb + 1.6), colour, op, grp)
    if not ghost:
        for x, y in [(x0 + 2.5, y0 + 2.5), (x1 - 2.5, y0 + 2.5), (x0 + 2.5, y1 - 2.5), (x1 - 2.5, y1 - 2.5)]:
            add(name + " boss", CZ(x, y, 3.5, T, T + h_pcb), PETG)


board_module("Pico 2 CONTROL", -74, -53, -5.5, 45.5, MOD["Pico 2 CONTROL"], h_pcb=4.0)
add("Pico RP2350", B(-67, -60, 18, 25, 13.6, 14.6), BLACK)
add("Pico micro-B", B(-67.5, -59.5, -5.5, -0.5, 13.6, 16.2), METAL)
add("Logic analyser (clone 20.3 tall)", B(-50, -22, -5.5, 50, T, T + 20.3), MOD["Logic analyser"])
add("analyser probe header", B(-45, -27, 47.5, 50, T + 20.3, T + 23), BLACK)
add("fuse holder 3AG 1A", ROD((-14.5, 0, T + 4.5), (-14.5, 45, T + 4.5), 9), BLACK)
board_module("Si5351 CLOCK (N site, active)", -40, -9.5, 52, 73.6, MOD["Si5351 CLOCK"])
add("Si5351 header", B(-12.5, -10, 54, 71.5, T + 4.6, T + 7), BLACK)
board_module("Si5351 S site (unused)", -40, -9.5, 100, 121.6, MOD["Si5351 CLOCK"], ghost=True)
board_module("MAX31855 CHIP TEMP", -74, -53.7, 116, 138.9, MOD["MAX31855 CHIP TEMP"])
add("MAX31855 terminal", B(-68.5, -59, 116, 123.5, T + 4.6, T + 14), BLACK)
board_module("D4184 HEAT DRIVE", -74, -39, 143, 159, MOD["D4184 HEAT DRIVE"])
add("D4184 terminals", B(-74, -66, 144, 158, T + 4.6, T + 14).union(B(-47, -39, 144, 158, T + 4.6, T + 14)), BLACK)
add("Star GND lever block", B(-50, -30, 125, 138, T, T + 16), MOD["Star GND block"])
board_module("AO3400 AIR DRIVE", -28, -8, 124, 140, MOD["AO3400 AIR DRIVE"])
board_module("INA226 BOARD POWER", -36, -9, 142, 162, MOD["INA226 BOARD POWER"])
add("INA226 shunt", B(-25, -20, 150, 154, T + 4.6, T + 6), BLACK)
add("analyser lead comb (S pos.)", B(-7.5, -0.5, 98, 112, T, T + 25), PLATE)

# ================================================================= collision check (bboxes, then BRep common)
ALLOWED = {  # intended contact / insertion, by name prefix pairs
    ("lid screw", "base"), ("lid screw", "lid ring"), ("lid screw", "bezel"),
    ("P1 pins", "CLK IN shroud (ASA)"), ("standoff", "board screw"),
    ("plunger shank", "acorn nut"), ("preload screw", "captive nut"), ("preload screw", "jam nut"),
    ("post screw", "post nylon acorn"),
}


def allowed(a, b):
    return any((a.startswith(p) and b.startswith(q)) or (a.startswith(q) and b.startswith(p)) for p, q in ALLOWED)


def collisions(parts, tol_mm3=0.5):
    found = []
    solid = [(n, s) for n, s, _, _, g in parts if g != "ghost"]
    for i in range(len(solid)):
        na, sa = solid[i]
        ba = sa.BoundingBox()
        for j in range(i + 1, len(solid)):
            nb, sb = solid[j]
            if allowed(na, nb):
                continue
            bb = sb.BoundingBox()
            if (min(ba.xmax, bb.xmax) - max(ba.xmin, bb.xmin) < 0.05 or
                    min(ba.ymax, bb.ymax) - max(ba.ymin, bb.ymin) < 0.05 or
                    min(ba.zmax, bb.zmax) - max(ba.zmin, bb.zmin) < 0.05):
                continue
            try:
                v = sa.intersect(sb).Volume()
            except Exception:
                continue
            if v > tol_mm3:
                found.append((na, nb, v))
    return found


# ================================================================= legend + renders
LEGEND = [
    ("PETG shell / tray / plates", PETG), ("ASA clamp frame + arm", ASA), ("blue PETG intake duct", DUCT),
    ("Al foot, cap, pins", METAL), ("HS10 heater", HS10C), ("brass standoffs", BRASS),
    ("FPGA board", PCB), ("Kapton", KAPTON), ("acrylic window", ACRYL),
] + [(k, v) for k, v in MOD.items()]


def add_legend(path):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.open(path).convert("RGB")
    pw = 300
    out = Image.new("RGB", (img.width + pw, img.height), (247, 247, 245))
    out.paste(img, (0, 0))
    d = ImageDraw.Draw(out)
    try:
        f = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 17)
    except OSError:
        f = ImageFont.load_default()
    y = 70
    for label, c in LEGEND:
        rgb = tuple(int(255 * v) for v in c)
        d.rectangle([img.width + 12, y, img.width + 34, y + 18], fill=rgb, outline=(40, 40, 40))
        d.text((img.width + 44, y), label, fill=(20, 20, 20), font=f)
        y += 28
    out.save(path)


def specs(groups):
    return [(s, c, o) for n, s, c, o, g in PARTS if g in groups]


def section(parts_groups, y_cut=FY, y_from=-300, xr=(-200, 200), zr=(-50, 150)):
    """Boolean section: keep Y in [y_from, y_cut] (N of the cut) so the cut face looks S at the 'front' camera."""
    keep = as_shape(B(xr[0], xr[1], y_from, y_cut, zr[0], zr[1]))
    out = []
    for n, s, c, o, g in PARTS:
        if g not in parts_groups:
            continue
        bb = s.BoundingBox()
        if (bb.xmax < xr[0] or bb.xmin > xr[1] or bb.zmax < zr[0] or bb.zmin > zr[1]
                or -bb.ymax > y_cut or -bb.ymin < y_from):
            continue
        try:
            cut = s.intersect(keep)
        except Exception:
            continue
        if cut.Volume() > 1e-3:
            out.append((cut, c, o))
    return out


# ----------------------------------------------------------------- labels (orthographic views only)
SIZE = (1400, 1000)


def _mapper(spec, view):
    """World -> pixel for render()'s 'top'/'front' views: ResetCamera fits the bounding sphere, then Zoom(1.15)."""
    bb = cq.Compound.makeCompound([s for s, _, _ in spec]).BoundingBox()
    cx, cy, cz = (bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2, (bb.zmin + bb.zmax) / 2
    radius = 0.5 * math.sqrt(bb.xlen ** 2 + bb.ylen ** 2 + bb.zlen ** 2)
    k = (SIZE[1] / 2) * 1.15 / radius

    def f(p):  # p in the concept frame; (X, Y) for top, (X, any, Z) for front
        w = W(tuple(p) + (0.0,) * (3 - len(p)))
        if view == "top":
            return SIZE[0] / 2 + (w.x - cx) * k, SIZE[1] / 2 - (w.y - cy) * k
        return SIZE[0] / 2 + (w.x - cx) * k, SIZE[1] / 2 - (w.z - cz) * k
    return f


def _font(n):
    from PIL import ImageFont
    try:
        return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", n)
    except OSError:
        return ImageFont.load_default()


def label_on(path, spec, view, labels):
    """Text centred on each target (top view)."""
    from PIL import Image, ImageDraw
    f, fn = _mapper(spec, view), _font(15)
    img = Image.open(path).convert("RGBA")
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    for text, p in labels:
        x, y = f(p)
        l, t, r, b = d.textbbox((0, 0), text, font=fn)
        w, h = r - l, b - t
        d.rectangle([x - w / 2 - 3, y - h / 2 - 3, x + w / 2 + 3, y + h / 2 + 3], fill=(255, 255, 255, 200))
        d.text((x - w / 2, y - h / 2 - t), text, fill=(10, 10, 10, 255), font=fn)
    Image.alpha_composite(img, over).convert("RGB").save(path)


def label_leaders(path, spec, view, left, right):
    """Callouts in the side margins with leader lines to each target (section view)."""
    from PIL import Image, ImageDraw
    f, fn = _mapper(spec, view), _font(15)
    bb = cq.Compound.makeCompound([s for s, _, _ in spec]).BoundingBox()
    x_lo, x_hi = f((bb.xmin, 0, 0))[0], f((bb.xmax, 0, 0))[0]
    img = Image.open(path).convert("RGB")
    d = ImageDraw.Draw(img)
    for side, items in (("L", left), ("R", right)):
        items = sorted(items, key=lambda it: (f(it[1])[1], f(it[1])[0] * (-1 if side == "R" else 1)))
        ys, prev = [], -1e9
        for _, p in items:                      # each label at its target's height, pushed apart
            prev = max(f(p)[1], prev + 26)
            ys.append(prev)
        shift = max(0.0, ys[-1] - (SIZE[1] - 30)) if ys else 0.0
        for i, (text, p) in enumerate(items):
            tx, ty = f(p)
            ly = ys[i] - shift
            l, t, r, b = d.textbbox((0, 0), text, font=fn)
            if side == "R":
                lx = x_hi + 25
                d.line([(tx, ty), (lx - 4, ly)], fill=(30, 30, 30), width=1)
                d.text((lx, ly - (b - t) / 2 - t), text, fill=(10, 10, 10), font=fn)
            else:
                lx = x_lo - 25
                d.line([(tx, ty), (lx + 4, ly)], fill=(30, 30, 30), width=1)
                d.text((lx - (r - l), ly - (b - t) / 2 - t), text, fill=(10, 10, 10), font=fn)
            d.ellipse([tx - 2.5, ty - 2.5, tx + 2.5, ty + 2.5], fill=(200, 20, 20))
    img.save(path)


TOP_LABELS = [
    ("Pico 2", (-63.5, 32)), ("LOGIC 8-CH", (-36, 20)), ("fuse", (-14.5, 47.5)),
    ("Si5351 N", (-25, 62)), ("Si5351 S (alt.)", (-25, 111)), ("MAX31855", (-64, 131)),
    ("D4184", (-56.5, 151)), ("GND", (-40, 131.5)), ("AO3400", (-18, 132)), ("INA226", (-22.5, 146)),
    ("fan", (-61, 88)), ("duct", (-71, 108)), ("heater arm", (8, 86)), ("plunger over FPGA", (57.5, 104)),
    ("P1", (35.5, 116)), ("P2", (81.5, 117)), ("P3", (58.5, 53)), ("7-seg", (12.5, 34)),
    ("DB9", (39.5, 5)), ("VGA", (74, 5)), ("AS", (40, 128)), ("JTAG", (78, 121)),
    ("USB-Blaster dongle", (70, 156)), ("comb", (-4, 116)), ("USB-B", (8, 96)), ("power sw.", (5, 110)),
    ("N (back): I/O plates", (19, -16)), ("S (front): visitor side", (19, 175)),
    ("air in", (-89, 86)), ("air out", (127, 86)),
]
ZOOM_RIGHT = [
    ("preload screw, top Z 65.4", (FX, 0, 64.5)), ("captive nut", (FX + 2.5, 0, 58.2)),
    ("spring, L_i ~ 6", (FX + 2.4, 0, 51.5)), ("plunger head, lifted 2 mm", (FX + 2, 0, 46.6)),
    ("barrel lip 1.5", (FX + 4.5, 0, 42.3)), ("acorn dome (4.2 tall = max)", (FX + 2, 0, 39.5)),
    ("Al pressure cap", (FX + 7, 0, 36.8)), ("HS10 resistor", (FX + 1, 0, 31)),
    ("Al angle, E leg", (FX + 9, 0, 37.5)), ("KSD9700 75 C + FR4 strap", (72.5, 0, 34)),
    ("Al foot 18x18x5.5", (FX + 7, 0, 22.5)), ("FPGA + Kapton", (FX + 9, 0, 18.6)),
    ("PCB", (78, 0, 16.8)), ("back-support post", (FX, 0, 12.5)), ("floor plug (post access)", (FX + 8, 0, -1.5)),
]
ZOOM_LEFT = [
    ("acrylic window (lid)", (-40, 0, 74)), ("hinge pin", (HINGE, 0, ZPIN)), ("latch pin", (LATCH, 0, ZPIN)),
    ("arm, underside PCB+30", (10, 0, 47.8)), ("mast fin (ASA)", (-22, 0, 30)),
    ("sole 30 x 8 (ASA)", (20, 0, 4)), ("P1 (CLK-IN shroud behind)", (35.5, 0, 21.5)), ("tray", (-42, 0, 6.5)),
]

SECTION_LEFT = [
    ("lid screw hits acrylic", (-72, 0, 73.9)), ("intake duct (blue)", (-75.5, 0, 45)),
    ("40 mm fan", (-61, 0, 50)), ("BME280, top above shield", (-71, 0, 26)), ("Pico 2", (-63.5, 0, 12.6)),
    ("logic analyser (top Z 28.3)", (-45, 0, 25)), ("hinge + latch pins", (-32, 0, 53.6)),
]
SECTION_RIGHT = [
    ("bezel / acrylic / lid ring", (95, 0, 77)), ("hanging lid boss", (111, 0, 64)),
    ("arm + plunger barrel", (62, 0, 56)), ("heater stack on FPGA", (57.5, 0, 31)), ("P2 (SDRAM behind)", (81.5, 0, 22)),
    ("brass standoff", (101, 0, 11)), ("dongle cable, E-gap channel", (110, 0, 5)),
    ("floor plug (post access)", (57.5, 0, -1.5)),
]


def checks():
    """Derived numbers quoted in the report (all from the concept's own values)."""
    print("\nderived checks:")
    print(f"  window opening / outer top = {172 * 154 / (196 * 178):.1%}; / interior = {172 * 154 / (190 * 172):.1%}")
    print(f"  ring band outside acrylic pocket: X -79..-73.3 = {79 - 73.3:.1f} mm; boss axis X -72 lies inside the pocket")
    tip = Z_CAP - (DOME_R - math.sqrt(DOME_R ** 2 - 1.5 ** 2))
    print(f"  barrel bottom 41.6 - cap top {Z_CAP:.2f} = {41.6 - Z_CAP:.2f}; dome tip seats at {tip:.2f}"
          f" -> acorn nut must be <= {41.6 - tip:.2f} tall (zero gap)")
    print(f"  BME280 card top 27.4 vs shield top 24 -> {27.4 - 24:.1f} mm above the shield")
    print(f"  logic analyser clone top = {T + 20.3:.1f} (tray 8 + 20.3) vs 'modules <= Z 25'")
    print(f"  P1-34 to P1-1/2 = 16 pitches = {16 * 2.54:.1f} mm (Si5351 GND return)")
    print(f"  clamp foot {35 * 20} mm2; reachable from above beside the fin: {7 * 20 + 2 * 2 * 28} mm2")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print(f"{len(PARTS)} parts")
    t = f"Concept '{NAME}' - massing sketch, not final"
    closed = {"box", "lid", "ghost"}
    opened = {"box", "ghost"}
    jobs = [
        ("iso", specs(closed), "iso", f"{t} - closed, from the front (S) right"),
        ("iso_back", specs(closed), "iso_back", f"{t} - closed, from the back (N): I/O plates, intake"),
        ("open_iso", specs(opened), "iso", f"{t} - lid off"),
        ("open_top", specs(opened), "top", f"{t} - lid off, top view (N up)"),
        ("section", section(closed), "front", f"{t} - section at Y=86 through the FPGA, seen from the front"),
        ("section_zoom", section(closed, y_from=70, xr=(-45, 82), zr=(-4, 82)), "front",
         f"{t} - clamp stack, section Y=86 (slab Y 70..86)"),
    ]
    for tag, spec, view, title in jobs:
        path = os.path.join(OUT, f"{NAME}_{tag}.png")
        render(spec, path, view=view, title=title, size=SIZE)
        if tag == "open_top":
            label_on(path, spec, view, TOP_LABELS)
        if tag == "section":
            label_leaders(path, spec, view, SECTION_LEFT, SECTION_RIGHT)
        if tag == "section_zoom":
            label_leaders(path, spec, view, ZOOM_LEFT, ZOOM_RIGHT)
        add_legend(path)
        print("wrote", path)
    checks()
    print("\ncollisions (> 0.5 mm3):")
    for a, b, v in collisions(PARTS):
        print(f"  {a:40s} x {b:40s} {v:9.1f} mm3")
