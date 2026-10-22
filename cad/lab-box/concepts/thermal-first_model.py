"""Massing sketch of Lab Box concept 'thermal-first' (bulkhead + gantry).

NOT the CAD. Simple boxes and cylinders placed at the numbers in
concepts/thermal-first.md, so the concept can be seen and its numbers checked
for collisions. Every board position is a photo-estimate (board-mechanical.md).

Box frame (from the concept): X east from the W wall outer face, Y SOUTH from the
N wall outer face, Z up from the floor underside. Board frame maps X = x + 27,
Y = y + 11. World frame for rendering: (X, -Y, Z), so N is up in the top view.

    .venv/Scripts/python.exe concepts/thermal-first_model.py
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import cadquery as cq  # noqa: E402
from render import render  # noqa: E402

OUT = os.path.join(HERE, "renders")
NAME = "thermal-first"
TITLE = f"Concept '{NAME}' - massing sketch, not final"

PETG = (0.55, 0.62, 0.72)
ASA = (0.95, 0.5, 0.15)
METAL = (0.75, 0.75, 0.78)
STEEL = (0.88, 0.88, 0.92)
BRASS = (0.8, 0.65, 0.3)
PCB = (0.1, 0.35, 0.15)
BLACK = (0.1, 0.1, 0.1)
DARK = (0.28, 0.28, 0.3)
ACRYL = (0.6, 0.8, 1.0)


# ------------------------------------------------------------------ primitives (box frame in)
def V(x, y, z):
    return cq.Vector(x, -y, z)


def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y1, z0))


def cyl(xc, yc, z0, z1, d):  # vertical
    return cq.Solid.makeCylinder(d / 2, z1 - z0, V(xc, yc, z0), cq.Vector(0, 0, 1))


def cylx(x0, x1, yc, zc, d):  # along +X
    return cq.Solid.makeCylinder(d / 2, x1 - x0, V(x0, yc, zc), cq.Vector(1, 0, 0))


def cyly(y0, y1, xc, zc, d):  # along +Y (world -y)
    return cq.Solid.makeCylinder(d / 2, y1 - y0, V(xc, y0, zc), cq.Vector(0, -1, 0))


def hexpost(xc, yc, z0, z1, af=5.5):
    return (cq.Workplane().polygon(6, af / math.cos(math.pi / 6)).extrude(z1 - z0)
            .val().translate(V(xc, yc, z0)))


def pipe(pts, d):
    """Round wire through box-frame points (cylinders + ball joints)."""
    parts = []
    for a, b in zip(pts, pts[1:]):
        pa, pb = V(*a), V(*b)
        v = pb - pa
        parts.append(cq.Solid.makeCylinder(d / 2, v.Length, pa, v.normalized()))
    for p in pts[1:-1]:
        parts.append(cq.Solid.makeSphere(d / 2, V(*p), angleDegrees1=-90, angleDegrees2=90))
    return cq.Compound.makeCompound(parts)


def rect_x(x, yc, zc, wy, wz):  # rectangle wire in a plane X = x
    return cq.Wire.makePolygon([V(x, yc - wy / 2, zc - wz / 2), V(x, yc + wy / 2, zc - wz / 2),
                                V(x, yc + wy / 2, zc + wz / 2), V(x, yc - wy / 2, zc + wz / 2)], close=True)


def fuse(*s):
    return s[0].fuse(*s[1:]).clean() if len(s) > 1 else s[0]


def comp(*s):
    return cq.Compound.makeCompound(list(s))


# ------------------------------------------------------------------ the model
P = []  # (name, shape, rgb, opacity, group)


def add(name, shape, rgb, op=1.0, group="in"):
    P.append((name, shape, rgb, op, group))


def get(n):
    return next(s for nm, s, *_ in P if nm == n)


# --- hot base shell: floor, N/W/S walls, bulkhead (PETG), 164 x 184 x 66
#     (split so the S wall can be drawn see-through in the open views)
hot = fuse(box(0, 164, 0, 184, 0, 3), box(0, 164, 0, 3, 0, 66), box(0, 3, 0, 184, 0, 66),
           box(161, 164, 0, 184, 0, 66))
hot_s = box(3, 161, 181, 184, 0, 66)
cuts = [box(46, 122, -1, 4, 18, 46),                      # D-sub window (blanked)
        box(-1, 4, 138, 162, 26, 34),                     # LA brush slot
        box(160, 165, 77, 117, 16, 56),                   # fan / nozzle bore 40x40
        cyly(180, 185, 150, 15, 8)]                       # Blaster USB gland
cuts += [box(-1, 4, 62, 132, 24 + i * 6.8, 28 + i * 6.8) for i in range(6)]  # exhaust 6 x 4x70
cuts += [cylx(160, 165, y, z, 7) for y, z in [(61, 56), (67, 56), (131, 56), (20, 12)]]
add("hot shell", hot.cut(*cuts), PETG, group="shell")
add("hot S wall", hot_s.cut(*cuts), PETG, group="front")
add("D-sub blanking plate", box(42, 126, -2, 0, 14, 50), (0.45, 0.52, 0.62), group="shell")

# --- annex shell X 164-234 (PETG): floor, N/E/S walls, W perimeter flange
ann = fuse(box(164, 234, 0, 184, 0, 3), box(164, 234, 0, 3, 0, 66),
           box(164, 167, 0, 184, 0, 66).cut(box(163, 168, 8, 176, 8, 60)))
ann_f = fuse(box(167, 234, 181, 184, 0, 66), box(231, 234, 3, 181, 0, 66))
acuts = [box(230, 235, 62, 132, 14 + i * 6.8, 18 + i * 6.8) for i in range(6)]  # intake
acuts += [box(176, 185, -1, 4, 7, 14),                    # Pico USB
          box(207, 215, -1, 4, 7, 12),                    # FPGA 5V IN (USB-C power-only)
          cylx(230, 235, 150, 30, 8), cylx(230, 235, 168, 30, 12)]  # 12 V jack, fuse holder
add("annex shell", ann.cut(*acuts), PETG, group="shell")
add("annex S + E walls", ann_f.cut(*acuts), PETG, group="front")
add("annex cover", box(164, 234, 0, 184, 66, 70), PETG, group="cover")

# --- lid (PETG) 164 x 184 x 20, Z 66-86; acrylic 152x172x3 in a pocket under the 144x164 opening
lid = fuse(box(0, 164, 0, 184, 66, 86).cut(box(3, 161, 3, 181, 65, 82)),
           box(3.4, 160.6, 3.4, 180.6, 62, 66).cut(box(5.4, 158.6, 5.4, 178.6, 61, 67)))  # locating lip
lid = lid.cut(box(10, 154, 10, 174, 81, 87), box(6, 158, 6, 178, 81.9, 85))
add("lid frame", lid, PETG, group="lid")
add("acrylic window", box(6, 158, 6, 178, 82, 85).cut(cyl(32, 129, 81, 86, 10)), ACRYL, 0.25, "lid")
add("window retaining frame", box(4, 160, 4, 180, 78, 82).cut(box(10, 154, 10, 174, 77, 83)), PETG, group="lid")
add("power push-rod", cyl(32, 129, 49.6, 90.6, 8), PETG, group="lid")

# --- ASA cradle: plate Z 3-7, standoff bosses to 13, back-support boss
STANDOFFS = [(32, 16), (128, 16), (32, 142), (128, 142)]
cradle = fuse(box(6, 158, 6, 178, 3, 7), *[cyl(x, y, 6.9, 13, 8) for x, y in STANDOFFS],
              cyl(84.5, 97, 6.9, 13, 8))
add("cradle", cradle, ASA)
add("standoffs", comp(*[hexpost(x, y, 13, 23) for x, y in STANDOFFS]), BRASS)

# --- FPGA board dummy (board frame +27/+11)
add("PCB", box(27, 133, 11, 147, 23, 24.6).cut(*[cyl(x, y, 22, 25, 3.2) for x, y in STANDOFFS]), PCB)
add("FPGA", box(74.5, 94.5, 87, 107, 24.6, 26.15), BLACK)
add("FPGA leads", box(73.5, 95.5, 86, 108, 24.6, 25.3).cut(box(74.5, 94.5, 87, 107, 24, 26)), METAL)


def header(x0, x1, y0, y1, along_y):
    body = box(x0, x1, y0, y1, 24.6, 27.1)
    if along_y:
        xc = (x0 + x1) / 2
        pins = comp(box(xc - 1.59, xc - 0.95, y0 + 0.5, y1 - 0.5, 27.1, 33.1),
                    box(xc + 0.95, xc + 1.59, y0 + 0.5, y1 - 0.5, 27.1, 33.1))
    else:
        yc = (y0 + y1) / 2
        pins = comp(box(x0 + 0.5, x1 - 0.5, yc - 1.59, yc - 0.95, 27.1, 33.1),
                    box(x0 + 0.5, x1 - 0.5, yc + 0.95, yc + 1.59, 27.1, 33.1))
    return body, pins


for nm, args in {"P1": (60, 65, 74, 122.3, True), "P2": (106, 111, 67, 123, True),
                 "P3": (72.8, 98.2, 68, 73, False)}.items():
    b, p = header(*args)
    add(nm, b, BLACK)
    add(nm + " pins", p, (0.55, 0.5, 0.3))
add("P1 Dupont / LA housings", box(60, 65, 74, 110, 27.1, 41.1), DARK)
add("DB9", comp(box(54, 80, 11, 22, 24.6, 36), box(51.1, 81.9, 10, 11, 24.6, 37.2)), BLACK)
add("DB9 shell", box(58.3, 74.7, 4, 10, 26.8, 35.1), METAL)
add("VGA", comp(box(89, 115, 11, 22, 24.6, 36), box(86.6, 117.4, 10, 11, 24.6, 37.2)), (0.2, 0.35, 0.85))
add("VGA shell", box(93.8, 110.2, 4, 10, 26.8, 35.1), METAL)
add("PS/2", box(34, 50, 11, 25, 24.6, 37.6), METAL)
add("7-seg", box(32, 47, 30, 61, 24.6, 31.8), BLACK)
add("LCD socket", box(28, 32, 44, 95, 24.6, 33.1), BLACK)
add("LEDs", comp(*[box(119, 121, y, y + 1.2, 24.6, 25.4) for y in (66, 68.3, 70.6, 72.9)]), (0.95, 0.1, 0.1))
add("keys", comp(*[box(122, 128, y - 3, y + 3, 24.6, 29.6) for y in (33.5, 42.5, 51, 59.5)]), DARK)
add("buzzer", cyl(67, 52, 24.6, 34.1, 12), BLACK)
add("DIP switch", box(94, 104, 47, 57, 24.6, 29.6), (0.85, 0.1, 0.1))
add("SDRAM", box(115, 125, 84, 114, 24.6, 25.8), BLACK)
add("IR + RESET", comp(box(124, 130, 24, 30, 24.6, 31.6), box(114, 120, 136, 142, 24.6, 29.6)), DARK)
add("USB-B socket", box(27, 43, 104, 116, 24.6, 35.2), METAL)
add("USB-B dummy plug", box(22, 27, 103, 117, 24, 36), PETG)
add("power switch", box(28, 36, 124, 134, 24.6, 36), DARK)
add("power switch cap (up)", cyl(32, 129, 36, 49.6, 6), (0.85, 0.15, 0.15))
add("DC jack", box(36, 46, 129, 147, 24.6, 35.6), BLACK)
add("DC plug (aligned to jack)", box(37, 45, 147, 162, 25, 35), DARK)
add("AS box header", box(57, 77, 134.5, 143.5, 24.6, 33.9), BLACK)
add("JTAG box header", box(83, 103, 134.5, 143.5, 24.6, 33.9), BLACK)
add("Blaster IDC plug", box(85, 101, 135.5, 142.5, 30, 43), DARK)
RIB = (0.78, 0.78, 0.8)
add("JTAG ribbon", comp(box(86.65, 99.35, 136, 152.5, 43, 44), box(86.65, 99.35, 151.5, 152.5, 18, 44),
                        box(86.65, 112, 151.5, 164.2, 18, 19)), RIB)
add("Blaster holster", box(110, 160, 151, 178, 7, 15).cut(box(112, 158, 153, 176, 9, 16)), PETG)
add("USB-Blaster", box(112, 158, 153, 176, 9, 27), (0.15, 0.2, 0.5))
add("Blaster USB cable", pipe([(150, 176, 15), (150, 190, 15)], 4), BLACK)

# --- back-support post: M4 set screw + lock nut + ASA cap 8 x 5
add("back-support screw", comp(cyl(84.5, 97, 13, 19, 4), hexpost(84.5, 97, 13, 16.2, 7)), STEEL)
add("back-support cap", cyl(84.5, 97, 18, 23, 8), ASA)

# --- heater stack
ped = box(75.5, 93.5, 88, 106, 26.2, 35.1)
plate = box(74.5, 94.5, 83, 120, 35.1, 38.1).cut(box(74, 77.5, 95, 99, 35, 39), cyl(84.5, 97, 36.1, 39, 6.5))
add("Kapton", box(75.5, 93.5, 88, 106, 26.15, 26.2), (0.9, 0.6, 0.1))
add("Al pedestal 18x18x8.9", ped, METAL)
add("Al top plate 20x37x3", plate, METAL)
BALL_Z = 36.1 - 3.25 + 3 * math.sqrt(2)  # 90 deg cone from the Ø6.5 counterbore floor
add("Ø6 ball", cq.Solid.makeSphere(3, V(84.5, 97, BALL_Z), angleDegrees1=-90, angleDegrees2=90), STEEL)
add("KSD9700", box(76, 91, 84, 91.5, 38.1, 42.1), (0.92, 0.92, 0.85))
add("KSD strap", box(82, 86, 83.2, 92.3, 42.1, 42.6), STEEL)
# HS10 (dims ASSUMED: base 16x16x2.5, body 16 long x 11 wide x 8.5 high, axis E-W)
hs10 = fuse(box(76.5, 92.5, 103, 119, 38.1, 40.6), box(76.5, 92.5, 105.5, 116.5, 38.1, 46.6))
add("HS10 resistor", hs10, (0.85, 0.75, 0.4))
tags = comp(box(74.5, 76.5, 110, 112, 41.6, 42.1), box(92.5, 94.5, 110, 112, 41.6, 42.1),
            box(74.25, 74.75, 110, 112, 41.6, 50), box(94.25, 94.75, 110, 112, 41.6, 50))
add("HS10 tags (bent up)", tags, METAL)
add("heat-shrink", comp(box(73.5, 75.5, 109.5, 112.5, 45, 50.5), box(93.5, 95.5, 109.5, 112.5, 45, 50.5)), BLACK)
add("thermocouple", pipe([(76, 97, 26.8), (75.1, 97, 26.8), (75.1, 97, 46.6), (75.1, 91.5, 46.6),
                          (128, 91.5, 46.6), (136, 55, 47), (158, 55, 50), (160, 61, 56), (166, 61, 56)], 1.2),
    (0.95, 0.85, 0.1))
add("heater harness", comp(
    pipe([(74.5, 111, 50.5), (74.5, 105.8, 57.6), (137, 105.8, 57.6), (137, 140, 50), (157, 140, 50),
          (160, 131, 56), (166, 131, 56)], 1.6),
    pipe([(94.5, 111, 50.5), (94.5, 106, 55.6), (135.5, 106, 55.6), (135.5, 141.5, 48.5),
          (157, 141.5, 48.5), (160, 131.5, 54.5), (166, 131.5, 54.5)], 1.6)), (0.8, 0.1, 0.1))

# --- clamp gantry (one ASA part): W post + beam + E portal
g = fuse(box(9, 21, 90, 104, 7, 62), box(9, 151, 90, 104, 48, 62), box(139, 151, 57, 69, 7, 62),
         box(139, 151, 125, 137, 7, 62), box(139, 151, 57, 137, 52, 62))
cham = cq.Solid.makeLoft([cq.Wire.makePolygon([V(x, 97.9, 47.9), V(x, 104.1, 47.9), V(x, 104.1, 54.1)],
                                              close=True) for x in (70, 100)], True)
g = g.cut(box(133, 151.5, 89.9, 104.1, 47.9, 52), cham, cyl(84.5, 97, 47, 63, 8.4))
add("gantry", g, ASA)
add("guide bush", cyl(84.5, 97, 48, 51, 8.4).cut(cyl(84.5, 97, 47, 52, 4.3)), ASA)
ROD_Z0 = BALL_Z + math.sqrt(9 - 4)  # Ø4 rod rim rests on the Ø6 ball
add("M4 plunger + preload screw", cyl(84.5, 97, ROD_Z0, 76, 4).cut(get("Ø6 ball")), STEEL)
add("spring seat nut + washer", comp(cyl(84.5, 97, 51, 52, 8), hexpost(84.5, 97, 52, 55, 7)), STEEL)
try:
    helix = cq.Wire.makeHelix(1.6, 6.4, 3.25, center=V(84.5, 97, 55), dir=cq.Vector(0, 0, 1))
    s0 = helix.startPoint()
    plane = cq.Plane(origin=s0, xDir=(s0 - V(84.5, 97, s0.z)).normalized(), normal=helix.tangentAt(0))
    spring = cq.Workplane(plane).circle(0.45).sweep(cq.Workplane().add(helix), isFrenet=True).val()
except Exception as e:  # noqa: BLE001
    print("helix failed, using rings:", e)
    spring = comp(*[cyl(84.5, 97, z, z + 0.9, 7.4).cut(cyl(84.5, 97, z - 1, z + 2, 5.6))
                    for z in [55 + 1.6 * i for i in range(4)]])
add("spring (k~1 N/mm, ~8 mm compressed)", spring, STEEL)
add("spring cap", cyl(84.5, 97, 61.4, 62.5, 7.5), STEEL)
car = box(64.5, 104.5, 84, 110, 62, 70).cut(cyl(84.5, 97, 61, 71, 4.5), cyl(70.5, 97, 61, 71, 7),
                                             cyl(98.5, 97, 61, 71, 7))
add("spring carriage", car, ASA)
add("carriage M3 screws", comp(cyl(70.5, 97, 70, 73, 5.5), cyl(98.5, 97, 70, 73, 5.5),
                               cyl(70.5, 97, 55, 70, 3), cyl(98.5, 97, 55, 70, 3)), STEEL)
add("preload knob", cyl(84.5, 97, 70, 78, 18), ASA)
add("Si5351 bracket", box(27, 63, 84, 110, 62, 72), ASA)
add("Si5351", box(32, 58, 88, 106, 72, 73.6), (0.3, 0.2, 0.8))

# --- airflow: nozzle (PETG, hollow loft), 4010 fan on the bulkhead's annex face
w = 1.6
outer = cq.Solid.makeLoft([rect_x(139, 97, 36, 44 + 2 * w, 24 + 2 * w), rect_x(161, 97, 36, 40 + 2 * w, 40 + 2 * w)], True)
inner = cq.Solid.makeLoft([rect_x(138, 97, 36, 44 + 4 / 22, 24 - 16 / 22),
                           rect_x(162, 97, 36, 40 - 4 / 22, 40 + 16 / 22)], True)
nozzle = outer.cut(inner)
add("inlet nozzle", nozzle, PETG)
CLASH = get("inlet nozzle").intersect(get("gantry"))  # spec problem, drawn hot pink
add("CLASH nozzle x portal", CLASH, (1.0, 0.0, 0.45), group="clash")
add("4010 fan", box(164, 174, 77, 117, 16, 56).cut(cylx(163, 175, 97, 36, 38)), BLACK)
add("fan hub", cylx(164.5, 173.5, 97, 36, 16), DARK)
add("bulkhead glands", comp(*[cylx(164, 170, y, z, 8) for y, z in [(61, 56), (67, 56), (131, 56), (20, 12)]]), BLACK)

# --- annex module plate and modules (plate top Z 6)
add("module plate", box(168, 231, 5, 179, 3, 6), PETG)
add("Pico 2H (flipped)", box(170, 191, 5, 56, 12, 13), (0.15, 0.7, 0.3))
add("Pico pins (up)", comp(box(170.5, 173, 6, 55, 13, 21), box(188, 190.5, 6, 55, 13, 21)), BLACK)
add("Pico standoffs", comp(*[cyl(x, y, 6, 12, 3) for x in (174.8, 186.2) for y in (7, 54)]), BRASS)
add("USB-C 5V inlet", box(205, 217, 3, 18, 6, 12), (0.2, 0.2, 0.25))
add("INA226", box(202, 229, 22, 42, 9, 10.6), (0.55, 0.25, 0.75))
add("interface perfboard", box(205, 229, 46, 76, 9, 10.6), (0.85, 0.7, 0.45))
add("MAX31855", box(180, 203, 56, 76, 9, 10.6), (0.85, 0.15, 0.2))
add("module terminals", comp(box(195, 202, 60, 72, 10.6, 18), box(172, 180, 129, 143, 10.6, 20),
                             box(199, 207, 129, 143, 10.6, 20)), (0.1, 0.55, 0.25))
add("D4184 MOSFET module", box(172, 207, 128, 144, 9, 10.6), (0.15, 0.35, 0.9))
add("BME280 mast", box(222, 226, 84, 110, 6, 56), PETG)
add("BME280", box(226, 227.6, 90, 103, 42, 55), (0.1, 0.75, 0.85))
add("12V jack", comp(cylx(212, 231, 150, 30, 8), cylx(234, 236, 150, 30, 11)), BLACK)
add("fuse holder", comp(cylx(196, 231, 168, 30, 12), cylx(234, 244, 168, 30, 14)), BLACK)

# --- logic analyser outside, in a holster on the W wall; leads through the brush slot to P1
add("LA holster", fuse(box(-16, 0, 128, 184, 34, 38), box(-16, -14, 128, 184, 34, 50)), PETG, group="shell")
add("logic analyser", box(-14, -1, 129, 183, 38, 64), (0.95, 0.85, 0.1), group="shell")
add("LA lead bundle", pipe([(62.5, 108, 41), (62.5, 150, 45), (8, 150, 45), (2, 150, 30),
                            (-8, 150, 30), (-8, 150, 38)], 5), (0.35, 0.35, 0.4))


GANTRY = {"gantry", "guide bush", "M4 plunger + preload screw", "spring seat nut + washer", "spring cap",
          "spring (k~1 N/mm, ~8 mm compressed)", "spring carriage", "carriage M3 screws", "preload knob",
          "Si5351 bracket", "Si5351", "CLASH nozzle x portal"}
P[:] = [(n, s, c, o, "gantry" if n in GANTRY else g) for n, s, c, o, g in P]


# ------------------------------------------------------------------ checks (printed, not asserted)
def gap(a, b):
    A, B = get(a), get(b)
    d = A.distance(B)
    if d > 1e-6:
        return f"{d:6.2f} mm clear"
    vol = A.intersect(B).Volume()
    return f"TOUCH/OVERLAP {vol:7.1f} mm3"


CHECKS = [("inlet nozzle", "gantry"), ("HS10 resistor", "gantry"), ("HS10 tags (bent up)", "gantry"),
          ("heat-shrink", "gantry"), ("preload knob", "acrylic window"), ("preload knob", "window retaining frame"),
          ("USB-B dummy plug", "gantry"), ("Si5351 bracket", "spring carriage"),
          ("P1 Dupont / LA housings", "gantry"), ("power switch cap (up)", "gantry"),
          ("Al top plate 20x37x3", "P1"), ("Al top plate 20x37x3", "P2"), ("Al top plate 20x37x3", "P3"),
          ("Al top plate 20x37x3", "JTAG box header"), ("Blaster IDC plug", "gantry"),
          ("LA lead bundle", "DC plug (aligned to jack)"), ("LA holster", "hot shell"),
          ("thermocouple", "inlet nozzle"), ("heater harness", "gantry"), ("thermocouple", "heater harness"),
          ("M4 plunger + preload screw", "Ø6 ball"), ("4010 fan", "hot shell"), ("Si5351 bracket", "acrylic window"),
          ("spring carriage", "window retaining frame")]


def run_checks():
    print("clearances (B-rep distance; 0 = touching or colliding):")
    for a, b in CHECKS:
        print(f"  {a:34s} vs {b:28s} {gap(a, b)}")
    # where along X does the nozzle's top skin reach the portal underside (Z 52)?
    for x in (139, 145, 151):
        top = 36 + (24 + (x - 139) * 16 / 22) / 2
        print(f"  nozzle inner top at X {x}: Z {top:5.2f}  outer Z {top + w:5.2f}  (portal underside Z 52)")
    print(f"  ball centre Z {BALL_Z:.2f}, ball top Z {BALL_Z + 3:.2f}, plunger tip Z {ROD_Z0:.2f}")


# ------------------------------------------------------------------ renders
def scene(groups_off=(), opacity_override=None):
    out = []
    for nm, s, rgb, op, grp in P:
        if grp in groups_off:
            continue
        if opacity_override and grp in opacity_override:
            op = opacity_override[grp]
        out.append((s, rgb, op))
    return out


def section(keep, groups_off=()):
    out = []
    for nm, s, rgb, op, grp in P:
        if grp in groups_off:
            continue
        cut = s.intersect(keep)
        if cut.Volume() > 1e-3:
            out.append((cut, rgb, 1.0 if grp != "lid" or nm != "acrylic window" else 0.5))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    run_checks()
    f = lambda v: os.path.join(OUT, f"{NAME}_{v}.png")  # noqa: E731
    render(scene(), f("iso"), "iso", title=TITLE + " (closed)")
    render(scene(), f("iso_back"), "iso_back", title=TITLE + " (closed, from NW)")
    render(scene(groups_off=("lid", "cover"), opacity_override={"front": 0.18}), f("open_iso"), "iso",
           title=TITLE + " (lid + annex cover off; S and E walls see-through)")
    render(scene(groups_off=("lid", "cover")), f("open_top"), "top",
           title=TITLE + " (top, lid + annex cover off; N up)")
    render(section(box(45, 140, 55, 152, -10, 100), groups_off=("lid", "cover", "gantry")), f("clamp_top"), "top",
           title=TITLE + " (spreader layout from above, gantry + carriage hidden; N up)")
    # section at Y 97 (through the FPGA centre), keep the N half, look N
    ycut = ((0, -97.05, 0), (0, 1, 0))
    render(section(box(-50, 300, -50, 97, -50, 150)), f("section"), "front", clip=ycut,
           title=TITLE + " (section Y 97 through FPGA centre, looking N; pink = clash)")
    render(section(box(55, 160, 60, 97, 18, 90)), f("section_detail"), "front", clip=ycut,
           title=TITLE + " (detail: section Y 97, X 55-160, looking N; pink = clash)")
    # section at X 84.5 (through the FPGA centre), keep the W half, look W (N is to the right)
    xcut = ((84.55, 0, 0), (-1, 0, 0))
    render(section(box(-50, 84.5, -50, 250, -50, 150)), f("section_ns"), "right", clip=xcut,
           title=TITLE + " (section X 84.5 through FPGA centre, looking W; N right)")
    render(section(box(62, 84.5, 66, 150, 18, 90)), f("section_ns_detail"), "right", clip=xcut,
           title=TITLE + " (detail: section X 84.5 looking W; S left, N right)")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
