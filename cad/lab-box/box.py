"""Agent Lab Box MVP: the real parametric CAD (DESIGN.md v0.1, simple-first + §3 amendments).

Contract with make.py:
  PARTS             {name: fn() -> cq.Shape}  printable parts in PRINT orientation (z >= 0)
  ASSEMBLY()        -> list[Item] in the box frame (world coordinates, see below)
  ALLOWED_OVERLAPS  intended volumetric contact (kept empty: contacts are modelled as faces)
  SECTIONS          {name: (origin, normal)} in world coordinates

Frames. params.py uses the box frame of DESIGN.md §4 (X east, Y SOUTH, Z up). Box Y south
makes that frame left-handed, so every solid here is built directly in a right-handed world
frame with world = (X, -Y, Z): north is +y, the renderer's "top" view has N up and E right,
and "front" looks from the S (visitor) face. Positions are converted, solids are never
mirrored, so engraved text reads correctly in every part and every render.

    .venv/Scripts/python.exe box.py      # writes the bar-part DXF drawings into parts/
"""
from __future__ import annotations

import functools
import math
import os
from dataclasses import dataclass

import cadquery as cq

import params as P
from params import (BAR_T, BAR_W, BOARD_X0, BOARD_Y0, BOX_X, BOX_Y, ENGRAVE, FLOOR_T, FONT, FX, FY,
                    INSERT_D, INSERT_DEPTH, M3_CLEAR, PCB_BOT, PCB_TOP, PITCH, PKG_TOP, TUB_H, WALL_T,
                    W_WALL_T)

HERE = os.path.dirname(os.path.abspath(__file__))

# ====================================================================== colours
PETG = (0.55, 0.62, 0.72)
PETG_SMALL = (0.95, 0.55, 0.15)
AL = (0.78, 0.79, 0.82)
STEEL = (0.52, 0.54, 0.58)
BRASS = (0.80, 0.65, 0.30)
NYLON = (0.95, 0.94, 0.88)
PCB_C = (0.10, 0.35, 0.15)
BLACK = (0.12, 0.12, 0.13)
RED = (0.85, 0.20, 0.12)
KAPTON = (0.95, 0.60, 0.10)
ACRYLIC = (0.60, 0.80, 1.00)
FR4 = (0.75, 0.70, 0.35)
GREY = (0.45, 0.45, 0.48)


@dataclass
class Item:
    name: str
    shape: object
    color: tuple
    kind: str                 # "printed" | "bought" | "reference"
    opacity: float = 1.0
    is_lid: bool = False


# ====================================================================== geometry helpers
# All helpers take BOX-frame coordinates (Y south) and return world solids.

def V(x, y, z=0.0):
    return cq.Vector(x, -y, z)


def B(x0, x1, y0, y1, z0, z1):
    x0, x1 = sorted((x0, x1))
    y0, y1 = sorted((y0, y1))
    z0, z1 = sorted((z0, z1))
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, -y1, z0))


def BC(xc, yc, sx, sy, z0, z1):
    return B(xc - sx / 2, xc + sx / 2, yc - sy / 2, yc + sy / 2, z0, z1)


def CZ(x, y, z0, z1, d):
    return cq.Solid.makeCylinder(d / 2, z1 - z0, V(x, y, z0), cq.Vector(0, 0, 1))


def CX(x0, x1, y, z, d):
    return cq.Solid.makeCylinder(d / 2, x1 - x0, V(x0, y, z), cq.Vector(1, 0, 0))


def CY(y0, y1, x, z, d):
    return cq.Solid.makeCylinder(d / 2, y1 - y0, V(x, y0, z), cq.Vector(0, -1, 0))


def HEX(x, y, z0, z1, af):
    return (cq.Workplane("XY").workplane(offset=z0).center(x, -y)
            .polygon(6, af / math.cos(math.pi / 6)).extrude(z1 - z0).val())


def SPH(x, y, z, d):
    return cq.Solid.makeSphere(d / 2, V(x, y, z), angleDegrees1=-90, angleDegrees2=90)


def TUBE(x, y, z0, z1, od, idia):
    return CZ(x, y, z0, z1, od).cut(CZ(x, y, z0 - 1, z1 + 1, idia))


def OBX(x0, x1, y, z, w, h):
    """Obround hole along X: w along Y, h along Z (w >= h)."""
    r = h / 2
    s = max(w - h, 0.0)
    out = CX(x0, x1, y - s / 2, z, h).fuse(CX(x0, x1, y + s / 2, z, h))
    if s > 0:
        out = out.fuse(B(x0, x1, y - s / 2, y + s / 2, z - r, z + r))
    return out


def fuse(first, *rest):
    out = first
    if rest:
        out = out.fuse(*rest)
    return out.clean()


def comp(*shapes):
    flat = []
    for s in shapes:
        flat.extend(s.Solids() if hasattr(s, "Solids") else [s])
    return cq.Compound.makeCompound(flat)


# world direction vectors
UP = (0, 0, 1)
E_ = (1, 0, 0)
W_ = (-1, 0, 0)
N_ = (0, 1, 0)       # box -Y
S_ = (0, -1, 0)      # box +Y


def TEXT(txt, size, at, normal, xdir, depth=ENGRAVE, halign="center", valign="center"):
    """Engraving tool: a text solid whose face lies on the plane through `at` (box coords)
    with outward `normal` (world); `xdir` is the reading direction seen from outside."""
    n = cq.Vector(*normal).normalized()
    pl = cq.Plane(origin=V(*at) + n * 0.02, xDir=cq.Vector(*xdir), normal=n)
    wp = cq.Workplane(pl).text(txt, size, -(depth + 0.02), combine=False, fontPath=FONT,
                               halign=halign, valign=valign)
    return wp.val()


# ====================================================================== clamp line geometry
R_HEX_LEG = P.LEG_AF / math.cos(math.pi / 6) / 2
FAN_Y0, FAN_Y1 = P.FAN_YC - P.FAN / 2, P.FAN_YC + P.FAN / 2


def _solve_theta():
    """Skew of the bridge/keel line so the W leg pair sits S of the fan frame [D #24]."""
    th = 0.3
    for _ in range(60):
        need = FAN_Y1 + P.FAN_LEG_CLEAR + P.LEG_PAIR * math.cos(th) + R_HEX_LEG - FY
        th = math.atan(need / (FX - P.LEG_W_X))
    return th


THETA = _solve_theta()
TH_DEG = math.degrees(THETA)
U_W = -(FX - P.LEG_W_X) / math.cos(THETA)
U_E = (P.LEG_E_X - FX) / math.cos(THETA)
BAR_U0, BAR_U1 = U_W - P.BAR_END, U_E + P.BAR_END_E
BAR_LEN = BAR_U1 - BAR_U0
LEG_UV = [(U_W, -P.LEG_PAIR), (U_W, P.LEG_PAIR), (U_E, -P.LEG_PAIR), (U_E, P.LEG_PAIR)]
KEEL_SCREW_UV = [(U_W + P.KEEL_SCREW_IN, 0.0), (U_E - P.KEEL_SCREW_IN, 0.0)]


def uv_to_box(u, v):
    """Bar-local (u along the bar W->E, v to its left = northish) -> box X, Y."""
    xw = u * math.cos(THETA) - v * math.sin(THETA)
    yw = u * math.sin(THETA) + v * math.cos(THETA)
    return FX + xw, FY - yw


def box_to_uv(X, Y):
    xw, yw = X - FX, -(Y - FY)
    return (xw * math.cos(THETA) + yw * math.sin(THETA), -xw * math.sin(THETA) + yw * math.cos(THETA))


POST_UV = [box_to_uv(FX + dx, FY + dy) for dx, dy in P.POST_SITES]


def to_bar(local: cq.Shape) -> cq.Shape:
    """Place a solid built in bar-local world coords (u = world x, v = world y, origin at the
    FPGA centre) onto the skewed clamp line."""
    return local.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), TH_DEG).translate(cq.Vector(FX, -FY, 0))


def LB(u0, u1, v0, v1, z0, z1):
    return cq.Solid.makeBox(u1 - u0, v1 - v0, z1 - z0, cq.Vector(u0, v0, z0))


def LCZ(u, v, z0, z1, d):
    return cq.Solid.makeCylinder(d / 2, z1 - z0, cq.Vector(u, v, z0), cq.Vector(0, 0, 1))


def bridge_y_band(X):
    """Plan band (box Y min, max) covered by the 20 mm bridge at box X."""
    yc = FY + (FX - X) * math.tan(THETA)
    half = BAR_W / 2 / math.cos(THETA)
    return yc - half, yc + half


# ====================================================================== header pin maps
P1_X = BOARD_X0 + P.P1_BX
P2_X = BOARD_X0 + P.P2_BX
P1_Y_N = BOARD_Y0 + P.P1_BY_N
P2_Y_N = BOARD_Y0 + P.P2_BY_N
P3_Y = BOARD_Y0 + P.P3_BY
P3_X_W = BOARD_X0 + P.P3_BX_W


def p1_row_of_pair(k):
    """Row index from the N end (1-based) of P1 pin pair k (pins 2k-1, 2k)."""
    return k if P.P1_PIN1_END == "N" else P.P1_ROWS + 1 - k


def p1_row_y(r):
    return P1_Y_N + (r - 0.5) * PITCH


def p1_pin_xy(pin):
    k = (pin + 1) // 2
    even = pin % 2 == 0
    col_e = (P.P1_EVEN_COL == "E") == even
    return P1_X + (PITCH / 2 if col_e else -PITCH / 2), p1_row_y(p1_row_of_pair(k))


CLK_PAIRS = (16, 17, 18, 19)                    # pins 31..38 under the CLK-IN shroud [D #27]
CLK_ROWS = sorted(p1_row_of_pair(k) for k in CLK_PAIRS)


def la_reserved():
    """Rows reserved for logic-analyser clips: N-most rows outside the bridge band and the
    CLK shroud [D #28]. Returns (p1_rows, p2_rows, text lines)."""
    b0, _ = bridge_y_band(P1_X)
    p1 = [r for r in range(1, P.P1_ROWS + 1) if p1_row_y(r) + PITCH / 2 < b0 - 0.5 and r not in CLK_ROWS][:8]
    b0, _ = bridge_y_band(P2_X)
    p2 = [r for r in range(1, P.P2_ROWS + 1) if P2_Y_N + (r - 0.5) * PITCH + PITCH / 2 < b0 - 0.5][:3]
    pins = []
    for r in p1:
        k = r if P.P1_PIN1_END == "N" else P.P1_ROWS + 1 - r
        pins += [2 * k - 1, 2 * k]
    pins.sort()
    lines = [f"P1 PINS {pins[0]}-{pins[-1]}" if pins else "P1: NONE FREE",
             f"P2 ROWS {p2[0]}-{p2[-1]} FROM N" if p2 else "P2: NONE FREE"]
    return p1, p2, lines


# ====================================================================== shared positions
PX0 = (P.GROOVE_X[0] + P.GROOVE_X[1]) / 2 - P.PANEL_T / 2     # panel outer face
PX1 = PX0 + P.PANEL_T                                          # panel inner face
PANEL_Y = (5.2, BOX_Y - 5.2)
PLATE_Z1 = P.PLATE_Z0 + P.PLATE_T
PICO_X0 = PX1 + 0.3 + P.PICO_USB_OVERHANG + 1.0
PICO_Z0 = PLATE_Z1 + P.PICO_SO
PICO_YC = P.PICO_Y0 + P.PICO[1] / 2
LA_X0 = PX1 + 0.3
LA_YC = P.LA_Y0 + P.LA[1] / 2
LA_USB_ZC = PLATE_Z1 + P.LA_USB_Z
PICO_USB_ZC = PICO_Z0 + P.PICO[2] + 1.36
FAN_X0 = PX1 + P.DUCT_L
SI_POS = {}
for _end in ("N", "S"):
    _k = 17
    _r = _k if _end == "N" else P.P1_ROWS + 1 - _k
    SI_POS[_end] = p1_row_y(_r)                                # Si5351 centre Y follows P1-34
SI_X1 = P.PLATE_X[1] - 0.1
SI_X0 = SI_X1 - P.SI5351[1]
# The Si5351 stands on edge (board plane parallel to the jet), header edge facing E, CLK0 near the
# top, on a printed wall just outside the fan jet on the side of P1-34 [D #27]. That puts CLK0 at
# the height where the P1-34 Dupont wire exits, which is what keeps the lead short.
SI_Z0 = PLATE_Z1 + 0.5
SI_Z1 = SI_Z0 + P.SI5351[0]
SI_SPACER = 4.0
SI_WALL_T = 2.0
_jet_n, _jet_s = P.FAN_YC - P.FAN / 2, P.FAN_YC + P.FAN / 2
SI_WALL = {"N": (_jet_s + 0.5, _jet_s + 0.5 + SI_WALL_T),            # pin 1 at N: P1-34 is S of the jet centre
           "S": (_jet_n - 0.5 - SI_WALL_T, _jet_n - 0.5)}
SI_BOARD = {"N": (SI_WALL["N"][1] + SI_SPACER, SI_WALL["N"][1] + SI_SPACER + 1.6),
            "S": (SI_WALL["S"][0] - SI_SPACER - 1.6, SI_WALL["S"][0] - SI_SPACER)}
SI_HOLES_XZ = [(SI_X1 - 2.54, SI_Z0 + 2.54), (SI_X1 - 2.54, SI_Z0 + 27.94)]
SI_CLK0_XZ = (SI_X1 - 2.54, SI_Z1 - 7.62)
RIBBON_Y = (BOARD_Y0 + P.BOARD_L + 4.0, BOARD_Y0 + P.BOARD_L + 5.0)   # ribbon on edge, S of the board
PORT = dict(usbc=(126.0, P.PANEL_PORT_Z), fuse=(148.0, P.PANEL_PORT_Z), jack=(166.0, P.PANEL_PORT_Z))
BLASTER_Y0 = RIBBON_Y[1] + 3.5                                  # dongle on its side, just S of the ribbon
BLASTER_Y1 = BLASTER_Y0 + P.BLASTER[2]
BLASTER_YC = (BLASTER_Y0 + BLASTER_Y1) / 2
BLASTER_X1 = P.BLASTER_X0 + P.BLASTER[0]
PED_X0 = BLASTER_X1 + P.BLASTER_PLUG_L + 1.0
PED_TOP = P.CABLE_Z - 1.0                                      # groove 1 mm deep: no tangent faces
CLAMP_Z0 = PED_TOP + 0.5                                       # 0.5 gap so the clamp grips the cable
CLAMP_Y = (BLASTER_YC - 7.0, BLASTER_YC + 7.0)
CLAMP_HOLES = [(PED_X0 + (BOX_X - WALL_T - PED_X0) / 2, BLASTER_YC - 4.5),
               (PED_X0 + (BOX_X - WALL_T - PED_X0) / 2, BLASTER_YC + 4.5)]   # M3 self-tapping, 2.5 pilot
COMB_BOSSES = [(66.5, 58.0), (66.5, 80.0)]
COMB_UP_X = (70.5, 73.5)
BME_SO = 9.0
RIBBON_CLIP_BOSS = (120.0, BOARD_Y0 + P.BOARD_L - 1.5)
JTAG_X, JTAG_Y = BOARD_X0 + P.JTAG_BX, BOARD_Y0 + P.JTAG_BY
USBB_Y = BOARD_Y0 + P.USBB_BY
USBB_X0 = BOARD_X0 - P.USBB_OVERHANG
USBB_ZC = PCB_TOP + P.USBB_SHELL[1] / 2

# clamp stack heights (params derives the long chain)
SPREADER_Z0 = PKG_TOP + P.PAD_T
TOP_Z0, TOP_Z1 = P.TOP_PLATE_Z0, P.TOP_PLATE_Z1
HS10_Y = FY + P.HS10_SHIFT_S
SPRING_L = P.SPRING_L0 - P.SPRING_F / P.SPRING_K
SPRING_Z1 = P.SPRING_Z0 + SPRING_L
ADJ_TIP = SPRING_Z1 + P.WASHER[1]
ADJ_TIP_FREE = P.SPRING_Z0 + P.SPRING_L0 + P.WASHER[1]      # spring just unloaded
KSD_Y0 = FY + 21.75
KSD_Y1 = KSD_Y0 + P.KSD[1]
STRAP_SCREWS = [(FX + P.STRAP_SCREW_X, KSD_Y0 - 2.25), (FX + P.STRAP_SCREW_X, KSD_Y1 + 2.25)]
POSTS = [(FX + P.POST_XY[0], FY + P.POST_XY[1]), (FX - P.POST_XY[0], FY - P.POST_XY[1])]
HS10_EARS = [(FX + P.HS10["F"] / 2, HS10_Y - P.HS10["G"] / 2), (FX - P.HS10["F"] / 2, HS10_Y + P.HS10["G"] / 2)]
TP_CSK = [(FX, FY - 5.0), (FX, FY + 5.0)]
WIN = P.WIN
ACR = (WIN[0] - P.ACRYLIC_MARGIN, WIN[1] + P.ACRYLIC_MARGIN, WIN[2] - P.ACRYLIC_MARGIN, WIN[3] + P.ACRYLIC_MARGIN)
ACR_HOLES = [(ACR[0] + P.ACRYLIC_HOLE_IN, ACR[2] + P.ACRYLIC_HOLE_IN), (ACR[1] - P.ACRYLIC_HOLE_IN, ACR[2] + P.ACRYLIC_HOLE_IN),
             (ACR[0] + P.ACRYLIC_HOLE_IN, ACR[3] - P.ACRYLIC_HOLE_IN), (ACR[1] - P.ACRYLIC_HOLE_IN, ACR[3] - P.ACRYLIC_HOLE_IN)]
LID_TOP = TUB_H + P.LID_T
SCALE_U = 9.0                                                   # scale clip position along the bridge
SCALE_Z0 = P.PBAR_Z1 + 5.5                                     # spring scale tongue bottom (>= 5 above heater metal)


# ====================================================================== printed: base tub
def _tub_labels():
    cuts = []
    # E wall: exhaust + Blaster exit [D #29]
    cuts.append(TEXT("AIR OUT", 6, (BOX_X, FY, 67), E_, N_))
    cuts.append(TEXT("USB-BLASTER / JTAG", 3.5, (BOX_X, 160, 31), E_, N_))
    cuts.append(TEXT("DO NOT UNPLUG JTAG", 3.0, (BOX_X, 160, 26), E_, N_))
    cuts.append(TEXT("WHILE POWERED", 3.0, (BOX_X, 160, 21.5), E_, N_))
    # visitor face: nameplate [D #30], unit-ID plate [D #31]
    if P.VISITOR_FACE == "S":
        y, nrm, xd = BOX_Y, S_, E_
    else:
        y, nrm, xd = 0.0, N_, W_
    cuts.append(TEXT("LYCOCHIP · AGENT LAB BOX", 7, (BOX_X / 2, y, 72), nrm, xd))
    cuts.append(TEXT("KNOBS: HEAT · AIR · CLOCK", 5, (BOX_X / 2, y, 58), nrm, xd))
    cuts.append(TEXT("EYES: CHIP TEMP · AIR TEMP · POWER · LOGIC", 5, (BOX_X / 2, y, 49), nrm, xd))
    cuts.append(TEXT("UNIT ID", 4, (BOX_X / 2 - 38, y, 30), nrm, xd))
    cuts.append(TEXT("CAL", 4, (BOX_X / 2 + 22, y, 30), nrm, xd))
    return cuts


@functools.lru_cache(maxsize=None)
def tub_assembly() -> cq.Shape:
    t = B(0, BOX_X, 0, BOX_Y, 0, TUB_H).cut(B(W_WALL_T, BOX_X - WALL_T, WALL_T, BOX_Y - WALL_T, FLOOR_T, TUB_H + 1))
    # W wall frame: opening for the drop-in panel, groove in the corner posts and the sill
    t = t.cut(B(-1, W_WALL_T + 0.01, 8.0, BOX_Y - 8.0, P.SILL_Z, TUB_H + 1))
    t = t.cut(B(P.GROOVE_X[0], P.GROOVE_X[1], 5.0, BOX_Y - 5.0, FLOOR_T, TUB_H + 1))
    adds = [CZ(x, y, FLOOR_T - 0.01, TUB_H, P.INSERT_BOSS_D) for x, y in P.LID_BOSS]
    # floor bosses: module plate [D #16], comb, ribbon clip (inserts from the top)
    for x, y in list(P.PLATE_BOSSES) + [RIBBON_CLIP_BOSS]:
        adds.append(CZ(x, y, FLOOR_T - 0.01, P.PLATE_Z0, P.INSERT_BOSS_D))
    for x, y in COMB_BOSSES:
        adds.append(CZ(x, y, FLOOR_T - 0.01, P.PLATE_Z0, 8.0))
    # Blaster cable clamp pedestal, fused to the E wall
    adds.append(B(PED_X0, BOX_X - WALL_T + 0.01, CLAMP_Y[0], CLAMP_Y[1], FLOOR_T - 0.01, PED_TOP))
    # Blaster cradle rails (dongle on its side) [D #21]
    adds.append(B(P.BLASTER_X0 + 2, BLASTER_X1 - 2, BLASTER_Y0 - 1.5, BLASTER_Y0, FLOOR_T - 0.01, FLOOR_T + 5))
    adds.append(B(P.BLASTER_X0 + 2, BLASTER_X1 - 2, BLASTER_Y1, BLASTER_Y1 + 1.5, FLOOR_T - 0.01, FLOOR_T + 5))
    t = t.fuse(*adds)
    cuts = []
    for x, y in P.LID_BOSS:
        cuts.append(CZ(x, y, TUB_H - INSERT_DEPTH, TUB_H + 1, INSERT_D))
    for x, y in list(P.PLATE_BOSSES) + COMB_BOSSES + [RIBBON_CLIP_BOSS]:
        cuts.append(CZ(x, y, P.PLATE_Z0 - INSERT_DEPTH, P.PLATE_Z0 + 1, INSERT_D))
    for x, y in CLAMP_HOLES:
        cuts.append(CZ(x, y, FLOOR_T + 0.5, PED_TOP + 1, 2.5))
    cuts.append(CX(PED_X0 - 1, BOX_X + 1, BLASTER_YC, P.CABLE_Z, P.BLASTER_CABLE_D))  # cable groove
    for x, y in P.BOARD_HOLES:                                  # board standoff screws (from below)
        cuts.append(CZ(x, y, -1, FLOOR_T + 0.01, M3_CLEAR))
    for u, v in KEEL_SCREW_UV:                                  # keel slots: clamp line slides +-10 in Y
        x, y = uv_to_box(u, v)
        cuts.append(B(x - M3_CLEAR / 2, x + M3_CLEAR / 2, y - P.KEEL_SLOT / 2, y + P.KEEL_SLOT / 2, -1, FLOOR_T + 0.01))
        cuts.append(CZ(x, y - P.KEEL_SLOT / 2, -1, FLOOR_T + 0.01, M3_CLEAR))
        cuts.append(CZ(x, y + P.KEEL_SLOT / 2, -1, FLOOR_T + 0.01, M3_CLEAR))
    ex = P.EXHAUST                                              # vertical exhaust slots [D #17, #26]
    for k in range(ex["n"]):
        yc = FY + (k - (ex["n"] - 1) / 2) * ex["pitch"]
        cuts.append(B(BOX_X - WALL_T - 1, BOX_X + 1, yc - ex["w"] / 2, yc + ex["w"] / 2, ex["z0"], ex["z1"]))
    cuts.append(OBX(BOX_X - WALL_T - 1, BOX_X + 1, BLASTER_YC, P.CABLE_Z, 12.0, 9.0))  # Blaster cable exit
    # unit-ID / CAL label fields on the visitor face [D #31]
    yv = BOX_Y if P.VISITOR_FACE == "S" else 0.0
    sgn = 1 if P.VISITOR_FACE == "S" else -1
    for x0, x1 in ((BOX_X / 2 - 29, BOX_X / 2 + 12), (BOX_X / 2 + 28, BOX_X / 2 + 70)):
        xa, xb = (x0, x1) if sgn > 0 else (BOX_X - x1, BOX_X - x0)
        cuts.append(B(xa, xb, yv - sgn * 0.4, yv + sgn * 1, 26, 34))
    cuts += _tub_labels()
    t = t.cut(*cuts).clean()
    return t


def _tub_split():
    """Optional split at SPLIT_X [D #17]: two parts joined by internal flanges, 4 x M3."""
    t = tub_assembly()
    sx = P.SPLIT_X
    ribs = [B(sx - 4, sx + 4, 15, 50, FLOOR_T - 0.01, 7.5),
            B(sx - 4, sx + 4, WALL_T - 0.01, WALL_T + 6, 20, 80),
            B(sx - 4, sx + 4, BOX_Y - WALL_T - 6, BOX_Y - WALL_T + 0.01, 20, 80)]
    t = t.fuse(*ribs)
    holes = [CX(sx - 5, sx + 5, 25, 5.2, M3_CLEAR), CX(sx - 5, sx + 5, 42, 5.2, M3_CLEAR),
             CX(sx - 5, sx + 5, WALL_T + 3, 50, M3_CLEAR), CX(sx - 5, sx + 5, BOX_Y - WALL_T - 3, 50, M3_CLEAR)]
    t = t.cut(*holes)
    w = t.intersect(B(-5, sx, -5, BOX_Y + 5, -5, TUB_H + 5)).clean()
    e = t.intersect(B(sx, BOX_X + 5, -5, BOX_Y + 5, -5, TUB_H + 5)).clean()
    return w, e


# ====================================================================== printed: W I/O panel
@functools.lru_cache(maxsize=None)
def panel_assembly() -> cq.Shape:
    p = B(PX0, PX1, PANEL_Y[0], PANEL_Y[1], P.PANEL_Z0, TUB_H)
    fy, fz = P.FAN_YC, P.FAN_ZC
    # intake duct: square tube from the grille to the fan, corner bosses with inserts [D #25]
    o = P.FAN / 2 + P.DUCT_WALL
    duct = B(PX1 - 0.01, FAN_X0, fy - o, fy + o, fz - o, fz + o).cut(
        B(PX1 - 1, FAN_X0 + 1, fy - P.FAN / 2, fy + P.FAN / 2, fz - P.FAN / 2, fz + P.FAN / 2))
    hp = P.FAN_HOLE_PITCH / 2
    bosses = [CX(PX1 - 0.01, FAN_X0, fy + sy * hp, fz + sz * hp, 8.6) for sy in (-1, 1) for sz in (-1, 1)]
    # BME280 bosses on the duct's N inner wall (board vertical, parallel to the flow)
    bme_wall_y = fy - P.FAN / 2
    # (piers run from the panel face along the duct axis, so they print standing up, no support)
    bme_b = [B(PX1 - 0.01, PX1 + 1.0 + hy + 2.5, bme_wall_y - 0.01, bme_wall_y + BME_SO,
               fz - P.BME[0] / 2 + hx - 2.5, fz - P.BME[0] / 2 + hx + 2.5) for hx, hy in P.BME_HOLES]
    # USB-C socket screw bosses are just holes; tie-anchor bars are what is left between slots
    p = p.fuse(duct, *bosses, *bme_b)
    cuts = []
    cuts += [CX(PX1 + P.DUCT_L - INSERT_DEPTH, FAN_X0 + 1, fy + sy * hp, fz + sz * hp, INSERT_D)
             for sy in (-1, 1) for sz in (-1, 1)]
    cuts += [CY(bme_wall_y - 1, bme_wall_y + BME_SO + 0.5, PX1 + 1.0 + hy, fz - P.BME[0] / 2 + hx, P.M25_PILOT)
             for hx, hy in P.BME_HOLES]
    cuts.append(CX(PX0 - 1, PX1 + 0.01, fy, fz, P.GRILLE_D))
    # ports [D #18-22]
    cuts.append(OBX(PX0 - 1, PX1 + 1, PICO_YC, PICO_USB_ZC, *P.PICO_USB_CUT))
    cuts.append(OBX(PX0 - 1, PX1 + 1, LA_YC, LA_USB_ZC, *P.LA_USB_CUT))
    y, z = PORT["usbc"]
    cuts.append(BC(0, y, 20, P.USBC_CUT[0], z - P.USBC_CUT[1] / 2, z + P.USBC_CUT[1] / 2))
    cuts += [CX(PX0 - 1, PX1 + 1, y + s * P.USBC_SCREWS, z, M3_CLEAR) for s in (-1, 1)]
    y, z = PORT["fuse"]
    cuts.append(CX(PX0 - 1, PX1 + 1, y, z, P.FUSE_HOLE))
    y, z = PORT["jack"]
    cuts.append(CX(PX0 - 1, PX1 + 1, y, z, P.JACK12_HOLE))
    # external tie anchors: two slots each, the bar between them takes the tie [D #22]
    for ya, za in ((P.PICO_Y0 + P.PICO[1] + 2.5, PICO_USB_ZC), (P.LA_Y0 + P.LA[1] + 2.5, LA_USB_ZC)):
        cuts.append(BC(0, ya, 20, 3.0, za + 1.0, za + 3.0))
        cuts.append(BC(0, ya, 20, 3.0, za - 3.0, za - 1.0))
    p = p.cut(*cuts)
    # grille rings and spokes inside the Ø38 opening
    g = [CX(PX0, PX1, fy, fz, d0).cut(CX(PX0 - 1, PX1 + 1, fy, fz, d1)) for d0, d1 in ((30, 26), (18, 14))]
    g += [B(PX0, PX1, fy - 19.5, fy + 19.5, fz - 1, fz + 1), B(PX0, PX1, fy - 1, fy + 1, fz - 19.5, fz + 19.5)]
    p = p.fuse(*g)
    # labels on the outer face [D #29]
    t = []
    ln = lambda s, sz, y, z: t.append(TEXT(s, sz, (PX0, y, z), W_, S_))  # noqa: E731
    ln("PICO USB", 4, PICO_YC, PICO_USB_ZC + 9)
    ln("LOGIC ANALYSER", 3.5, LA_YC, LA_USB_ZC - 9)
    ln("AIR IN", 6, fy, fz + 26)
    y, z = PORT["usbc"]
    ln("FPGA 5V IN", 3, y, z - 7)
    ln("(USB-C,", 3, y, z - 11.5)
    ln("METERED)", 3, y, z - 16)
    y, z = PORT["fuse"]
    ln("FUSE 1A", 3, y, z - 11)
    y, z = PORT["jack"]
    ln("HEATER", 3, y, z - 7)
    ln("12V IN", 3, y, z - 11.5)
    return p.cut(*t).clean()


# ====================================================================== printed: module plate
@functools.lru_cache(maxsize=None)
def plate_assembly() -> cq.Shape:
    z0, z1 = P.PLATE_Z0, PLATE_Z1
    pl = B(*P.PLATE_X, *P.PLATE_Y, z0, z1)
    pl = pl.cut(*[CZ(x, y, z0 - 1, z1 + 1, P.INSERT_BOSS_D + 2) for x, y in P.LID_BOSS if x < 50])
    adds = []
    # Pico standoffs (M2 pilot; Ø3.6 so they clear the 2.54 header strips)
    for hx in (2.0, P.PICO[0] - 2.0):
        for hy in (4.8, 16.2):
            adds.append(CZ(PICO_X0 + hx, P.PICO_Y0 + hy, z1 - 0.01, PICO_Z0, 3.6))
    # Pico backstop rib behind its far end [D #22]
    pe = PICO_X0 + P.PICO[0]
    adds.append(B(pe + 0.2, pe + 2.2, P.PICO_Y0 + 3, P.PICO_Y0 + P.PICO[1] - 3, z1 - 0.01, PICO_Z0 + 1.0))
    # LA: side rails + two backstop ribs at the corners of its far (probe) end [D #22]
    la_e = LA_X0 + P.LA[0]
    adds.append(B(P.PLATE_X[0], 24.0, P.LA_Y0 - 1.2, P.LA_Y0 - 0.2, z1 - 0.01, z1 + 3))   # split around plate screw A
    adds.append(B(36.0, la_e - 3, P.LA_Y0 - 1.2, P.LA_Y0 - 0.2, z1 - 0.01, z1 + 3))
    adds.append(B(P.PLATE_X[0], la_e - 3, P.LA_Y0 + P.LA[1] + 0.2, P.LA_Y0 + P.LA[1] + 1.2, z1 - 0.01, z1 + 3))
    for ya, yb in ((P.LA_Y0, P.LA_Y0 + 3), (P.LA_Y0 + P.LA[1] - 3, P.LA_Y0 + P.LA[1])):
        adds.append(B(la_e + 0.2, la_e + 2.2, ya, yb, z1 - 0.01, z1 + 6))
    # module bosses (3 mm, M2 / M2.5 pilots)
    mb = []
    mx0, my0 = 7.0, 125.0                                        # MAX31855 (terminal edge faces E)
    for hy in (2.54, 17.78):
        mb.append((mx0 + P.MAX31855[1] - 2.54, my0 + hy, P.M2_PILOT))
    ix0, iy0 = 30.0, 137.0                                       # INA226 (holes MEASURE: 2.5 in from corners)
    for hx in (2.5, P.INA226[0] - 2.5):
        for hy in (2.5, P.INA226[1] - 2.5):
            mb.append((ix0 + hx, iy0 + hy, P.M2_PILOT))
    dx0, dy0 = 26.0, 159.0                                       # D4184: 2 holes 12 apart at the signal (W) end
    for hy in (-6.0, 6.0):
        mb.append((dx0 + 3.0, dy0 + P.D4184[1] / 2 + hy, P.M2_PILOT))
    for x, y, _d in mb:
        adds.append(CZ(x, y, z1 - 0.01, z1 + 3.0, 5.0))
    for end, (w0, w1) in SI_WALL.items():                       # Si5351 walls, both P1_PIN1_END positions
        adds.append(B(SI_X0, SI_X1, w0, w1, z1 - 0.01, SI_Z1 + 1.0))
    pl = pl.fuse(*adds)
    cuts = [CZ(x, y, z0 - 1, z1 + 1, M3_CLEAR) for x, y in P.PLATE_BOSSES]
    cuts += [CZ(x, y, z1 - 2, z1 + 3.5, d) for x, y, d in mb]
    for hx in (2.0, P.PICO[0] - 2.0):
        for hy in (4.8, 16.2):
            cuts.append(CZ(PICO_X0 + hx, P.PICO_Y0 + hy, z1, PICO_Z0 + 1, 1.6))
    # strap slots for the logic analyser (hook-and-loop) [C §8]
    cuts += [B(40, 43, P.LA_Y0 - 4.6, P.LA_Y0 - 1.6, z0 - 1, z1 + 1),
             B(40, 43, P.LA_Y0 + P.LA[1] + 1.6, P.LA_Y0 + P.LA[1] + 4.6, z0 - 1, z1 + 1)]
    for end, (w0, w1) in SI_WALL.items():                       # M2.5 through the wall, nut on the far side
        cuts += [CY(w0 - 1, w1 + 1, x, z, 2.7) for x, z in SI_HOLES_XZ]
    # labels on the wall faces away from the Si5351 board
    cuts.append(TEXT("Si5351 IF P1-1 N", 2.0, ((SI_X0 + SI_X1) / 2 - 1, SI_WALL["N"][0], 27.0), N_, W_))
    cuts.append(TEXT("Si5351 IF P1-1 S", 2.0, ((SI_X0 + SI_X1) / 2 - 1, SI_WALL["S"][1], 27.0), S_, E_))
    return pl.cut(*cuts).clean()


# ====================================================================== printed: lid
@functools.lru_cache(maxsize=None)
def lid_assembly() -> cq.Shape:
    z0, z1 = TUB_H, LID_TOP
    lid = B(0, BOX_X, 0, BOX_Y, z0, z1)
    o = W_WALL_T + 0.3, BOX_X - WALL_T - 0.3, WALL_T + 0.3, BOX_Y - WALL_T - 0.3
    lip = B(o[0], o[1], o[2], o[3], z0 - P.LID_LIP_H, z0 + 0.01).cut(
        B(o[0] + P.LID_LIP_T, o[1] - P.LID_LIP_T, o[2] + P.LID_LIP_T, o[3] - P.LID_LIP_T, z0 - 10, z0 + 1))
    lip = lip.cut(*[CZ(x, y, z0 - 10, z0 + 1, P.INSERT_BOSS_D + 2) for x, y in P.LID_BOSS])
    lid = lid.fuse(lip)
    cuts = [B(WIN[0], WIN[1], WIN[2], WIN[3], z0 - 1, z1 + 1),
            B(ACR[0] - 0.5, ACR[1] + 0.5, ACR[2] - 0.5, ACR[3] + 0.5, z0 - 1, z0 + P.REBATE)]
    for x, y in P.LID_BOSS:          # captive thumbscrews: Ø3.4 bore, Ø2.6 thread-through collar [D #13]
        cuts.append(CZ(x, y, z0 + 1.0, z1 + 1, M3_CLEAR))
        cuts.append(CZ(x, y, z0 - 1, z0 + 1.01, 2.6))
    cuts += [CZ(x, y, z0 - 1, z1 + 1, M3_CLEAR) for x, y in ACR_HOLES]   # screws through the acrylic [D #15]
    # top-face engraving [D §3.7]
    t = cuts
    t.append(TEXT("LYCOCHIP · AGENT LAB BOX", 6, (127, 172, z1), UP, E_))
    t.append(TEXT("PWR SEL: UP = DC", 3, (73.0, 133.0, z1), UP, N_))
    t.append(TEXT("12V → FUSE 1A → THERMOSTAT 75°C → MOSFET → HEATER", 4, (58.5, 95, z1), UP, N_))
    t.append(TEXT("I²C  0x40 INA226 · 0x60 Si5351 · 0x77 BME280", 3.5, (51.5, 95, z1), UP, N_))
    legend = [("PICO 2", PICO_YC), ("LOGIC ANALYSER", LA_YC), ("FAN + BME280 · AIR IN", P.FAN_YC - 8),
              ("AO3400 · LOAD SW", P.FAN_YC + 8), ("Si5351 → P1-34", SI_POS[P.P1_PIN1_END]),
              ("MAX31855", 137.0), ("INA226", 149.0), ("STAR GND", 161.0), ("D4184 HEATER FET", 170.5)]
    for s, y in legend:
        t.append(TEXT(s, 3, (26.0, y, z1), UP, E_))
    return lid.cut(*t).clean()


# ====================================================================== printed: small parts
@functools.lru_cache(maxsize=None)
def usb_b_blank_assembly() -> cq.Shape:
    """Printed plug in the board USB-B with a pull tab below the jet [D #19]."""
    x_m = USBB_X0
    plug = B(x_m - 0.01, x_m + 9.0, USBB_Y - 4.0, USBB_Y + 4.0, USBB_ZC - 3.65, USBB_ZC + 3.65)
    plate = fuse(B(x_m - 2.0, x_m, USBB_Y - 7.0, USBB_Y + 7.0, 7.0, USBB_ZC + 6.0),
                 B(x_m - 2.0, x_m, FY - 15.0, USBB_Y + 7.0, 7.0, PCB_BOT - 0.5))
    s = fuse(plate, plug)
    t = [TEXT("NOT USED — 5 V ARRIVES", 2.5, (x_m - 2.0, FY + 2.5, 14.0), W_, S_),
         TEXT("METERED VIA DC JACK", 2.5, (x_m - 2.0, FY + 2.5, 10.0), W_, S_)]
    return s.cut(*t).clean()


@functools.lru_cache(maxsize=None)
def shroud_assembly() -> cq.Shape:
    """CLK-IN key shroud over P1-31..38; only pin 34 is open [D #27]."""
    ys = [p1_row_y(r) for r in CLK_ROWS]
    z0 = PCB_TOP + P.HDR_PLASTIC_H
    z1 = PCB_TOP + P.HDR_PIN_H + 2.0
    # End wall only at the header's own end; toward the neighbouring row the shroud stops on the
    # pitch line, because a Dupont housing on that row is a full pitch wide.
    w_n = 1.2 if min(CLK_ROWS) == 1 else 0.0
    w_s = 1.2 if max(CLK_ROWS) == P.P1_ROWS else 0.0
    s = B(P1_X - PITCH - 1.2, P1_X + PITCH + 1.2, min(ys) - PITCH / 2 - w_n, max(ys) + PITCH / 2 + w_s, z0, z1)
    cuts = []
    for pin in range(31, 39):
        x, y = p1_pin_xy(pin)
        if pin == 34:
            cuts.append(BC(x, y, 2.7, 2.7, z0 - 1, z1 + 1))
        else:
            cuts.append(BC(x, y, 1.1, 1.1, z0 - 1, PCB_TOP + P.HDR_PIN_H + 0.5))
    x34, y34 = p1_pin_xy(34)
    other_x = P1_X - (x34 - P1_X)
    cuts.append(TEXT("CLK", 2.2, (other_x, (min(ys) + max(ys)) / 2, z1), UP, N_))
    return s.cut(*cuts).clean()


@functools.lru_cache(maxsize=None)
def comb_assembly() -> cq.Shape:
    """Logic-analyser lead comb in the W gap, N of the jet [D #28]."""
    y0, y1 = 55.0, 83.0
    base = B(63.0, 75.5, y0, y1, P.PLATE_Z0, P.PLATE_Z0 + 3)
    up = B(COMB_UP_X[0], COMB_UP_X[1], y0, y1, P.PLATE_Z0 + 3 - 0.01, 34.0)
    s = fuse(base, up)
    cuts = [CZ(x, y, P.PLATE_Z0 - 1, P.PLATE_Z0 + 4, M3_CLEAR) for x, y in COMB_BOSSES]
    for i in range(10):
        ys = (y0 + y1) / 2 + (i - 4.5) * 2.54
        cuts.append(BC(sum(COMB_UP_X) / 2, ys, 5, 1.6, 28.0, 35.0))
    _, _, lines = la_reserved()
    xw = COMB_UP_X[0]
    cuts.append(TEXT("LA: CH0-7 + GND", 2.5, (xw, 69.0, 24.0), W_, S_))
    cuts.append(TEXT(lines[0], 2.5, (xw, 69.0, 20.0), W_, S_))
    cuts.append(TEXT(lines[1], 2.5, (xw, 69.0, 16.0), W_, S_))
    return s.cut(*cuts).clean()


@functools.lru_cache(maxsize=None)
def spring_scale_assembly() -> cq.Shape:
    """Clip-on spring length scale beside the spring, hung from the bridge [D #6]. It slides
    SCALE_U along the bar so no printed feature sits in the plume above the HS10 [D #9]."""
    u0 = SCALE_U
    zb0, zb1 = P.BRIDGE_Z0, P.BRIDGE_Z1
    v_in, v_e, v_out = 6.5, BAR_W / 2, BAR_W / 2 + 1.5
    s = LB(u0 - 5, u0 + 5, v_in, v_out, zb1, zb1 + 2.0)                       # top jaw
    s = s.fuse(LB(u0 - 5, u0 + 5, v_in, v_out, zb0 - 2.3, zb0 - 0.3))          # bottom jaw (0.3 slide fit)
    s = s.fuse(LB(u0 - 5, u0 + 5, v_e + 0.3, v_out + 0.3, SCALE_Z0, zb1 + 2.0)).clean()   # spine + tongue (0.3 off the bar edge)
    cuts = []
    # tick notches on the +u edge: upper-washer top at spring length L (mm)
    for L in range(4, int(P.SPRING_L0) + 1):
        z = P.SPRING_Z0 + L + P.WASHER[1]
        if not SCALE_Z0 + 0.5 < z < zb0 - 2.5:
            continue
        depth = 2.0 if L % 2 == 0 else 1.0
        cuts.append(LB(u0 + 5 - depth, u0 + 5.01, v_e + 0.29, v_out + 0.31, z - 0.2, z + 0.2))
        if L % 2 == 0:
            pl = cq.Plane(origin=cq.Vector(u0, v_out + 0.32, z), xDir=cq.Vector(-1, 0, 0), normal=cq.Vector(0, 1, 0))
            cuts.append(cq.Workplane(pl).text(str(L), 2.2, -0.62, combine=False, fontPath=FONT).val())
    pl = cq.Plane(origin=cq.Vector(u0, v_out + 0.32, zb0 - 0.0), xDir=cq.Vector(-1, 0, 0), normal=cq.Vector(0, 1, 0))
    cuts.append(cq.Workplane(pl).text("L", 2.2, -0.62, combine=False, fontPath=FONT).val())
    s = s.cut(*cuts).clean()
    return to_bar(s)


@functools.lru_cache(maxsize=None)
def cable_clamp_assembly() -> cq.Shape:
    """Top half of the Blaster USB-cable clamp; the lower half is the tub pedestal [D #21]."""
    x0, x1 = PED_X0, BOX_X - WALL_T - 0.3
    y0, y1 = CLAMP_Y
    zt = CLAMP_Z0 + 6.0
    s = B(x0, x1, y0, y1, CLAMP_Z0, zt)
    cuts = [CX(x0 - 1, x1 + 1, BLASTER_YC, P.CABLE_Z, P.BLASTER_CABLE_D)]
    cuts += [CZ(x, y, CLAMP_Z0 - 1, zt + 1, M3_CLEAR) for x, y in CLAMP_HOLES]
    cuts.append(TEXT("NO HOT-PLUG", 1.8, (x0 + 2.5, BLASTER_YC, zt), UP, N_))
    cuts.append(TEXT("JTAG", 1.8, (x1 - 2.5, BLASTER_YC, zt), UP, N_))
    return s.cut(*cuts).clean()


@functools.lru_cache(maxsize=None)
def ribbon_clip_assembly() -> cq.Shape:
    """Strain relief for the JTAG ribbon on its way to the internal Blaster [D #21]."""
    bx, by = RIBBON_CLIP_BOSS
    tab = B(bx - 5, bx + 5, by - 4.5, RIBBON_Y[0] - 2.0, P.PLATE_Z0, P.PLATE_Z0 + 3)
    blk = B(bx - 5, bx + 5, RIBBON_Y[0] - 2.0, RIBBON_Y[1] + 1.5, P.PLATE_Z0, 26.0)
    s = fuse(tab, blk)
    s = s.cut(CZ(bx, by, P.PLATE_Z0 - 1, P.PLATE_Z0 + 4, M3_CLEAR),
              B(bx - 6, bx + 6, RIBBON_Y[0] - 0.1, RIBBON_Y[1] + 0.1, 11.5, 27))
    return s.clean()


# ---------------------------------------------------------------------- fit tools (not in the assembly)
def footprint_gauge() -> cq.Shape:
    """1.2 mm board-footprint gauge: lay it on the real board before printing the tub [D #11].
    Board frame, top view, N up; the part is made in its print orientation directly."""
    W, L, t = P.BOARD_W, P.BOARD_L, 1.2

    def R(bx0, bx1, by0, by1, grow=0.6):   # board rect -> world rect (y = L - by, so N is +y)
        return cq.Solid.makeBox(bx1 - bx0 + 2 * grow, by1 - by0 + 2 * grow, t + 2,
                                cq.Vector(bx0 - grow, L - by1 - grow, -1))

    g = (cq.Workplane("XY").rect(W, L, centered=False).extrude(t).edges("|Z").fillet(P.BOARD_CORNER_R).val())
    # A 5 mm rail just OFF the W edge ties the NW and SW corners on: the photo-estimated edge
    # parts there (LCD socket, pot, switch, DC jack) would otherwise cut them off as islands.
    g = g.fuse(cq.Solid.makeBox(5.0, L, t, cq.Vector(-5.0, 0, 0))).clean()
    cuts = []
    for i in (0, 1):
        for j in (0, 1):
            hx, hy = P.HOLE_INSET + i * P.HOLE_PITCH_X, P.HOLE_INSET + j * P.HOLE_PITCH_Y
            cuts.append(cq.Solid.makeCylinder(P.HOLE_D / 2 + 0.1, t + 2, cq.Vector(hx, L - hy, -1)))
    fx, fy = P.FPGA_BX, P.FPGA_BY
    h = P.PKG_LEADS / 2
    cuts.append(R(fx - h, fx + h, fy - h, fy + h))
    hw = PITCH
    cuts.append(R(P.P1_BX - hw, P.P1_BX + hw, P.P1_BY_N, P.P1_BY_N + P.P1_ROWS * PITCH))
    cuts.append(R(P.P2_BX - hw, P.P2_BX + hw, P.P2_BY_N, P.P2_BY_N + P.P2_ROWS * PITCH))
    cuts.append(R(P.P3_BX_W, P.P3_BX_W + P.P3_COLS * PITCH, P.P3_BY - hw, P.P3_BY + hw))
    for cx in (P.JTAG_BX, P.AS_BX):
        cuts.append(R(cx - P.BOXHDR_L / 2, cx + P.BOXHDR_L / 2, P.JTAG_BY - P.BOXHDR_W / 2, P.JTAG_BY + P.BOXHDR_W / 2))
    cuts.append(R(P.DCJ_BX[0], P.DCJ_BX[1], P.DCJ_BY[0], L + 2))                 # DC jack notch (S edge)
    cuts.append(R(0, P.USBB_SHELL[2], P.USBB_BY - 6.02, P.USBB_BY + 6.02))      # USB-B notch (W edge)
    cuts.append(R(0, P.SW_BX[1], P.SW_BY[0], P.SW_BY[1]))                       # power switch
    s7 = P.SEG7
    cuts.append(R(s7[0], s7[1], s7[2], s7[3]))
    lc = P.LCD_SOCKET
    cuts.append(R(0, lc[1], lc[2], lc[3]))
    cuts.append(R(P.KEYS_BX - 3.5, P.KEYS_BX + 3.5, P.KEYS_BY[0] - 3.5, P.KEYS_BY[-1] + 3.5))
    cuts.append(R(P.IR[0] - 3, P.IR[0] + 3, P.IR[1] - 3, P.IR[1] + 3))
    cuts.append(R(P.DIP[0] - P.DIP[2] / 2, P.DIP[0] + P.DIP[2] / 2, P.DIP[1] - P.DIP[3] / 2, P.DIP[1] + P.DIP[3] / 2))
    bz = P.BUZZER
    cuts.append(cq.Solid.makeCylinder(bz[2] / 2 + 0.6, t + 2, cq.Vector(bz[0], L - bz[1], -1)))
    cuts.append(R(*P.POT))
    cuts.append(R(P.RESET_KEY[0] - 3.5, P.RESET_KEY[0] + 3.5, P.RESET_KEY[1] - 3.5, P.RESET_KEY[1] + 3.5))
    cuts.append(R(P.PS2_BX[0], P.VGA_BX[1], -2, P.PS2_DEPTH))                            # PS/2 + DB9 + VGA notch
    cuts.append(R(*P.LEDS))
    g = g.cut(*cuts)

    def T(s, size, bx, by, rot=False):
        pl = cq.Plane(origin=cq.Vector(bx, L - by, t + 0.02),
                      xDir=cq.Vector(0, 1, 0) if rot else cq.Vector(1, 0, 0), normal=cq.Vector(0, 0, 1))
        return cq.Workplane(pl).text(s, size, -0.52, combine=False, fontPath=FONT).val()

    lab = [T("FPGA", 2.5, fx, fy + h + 2.6), T("P1", 2.5, P.P1_BX - 5.5, P.P1_BY_N + 20, True),
           T("P2", 2.5, P.P2_BX + 5.5, P.P2_BY_N + 20, True), T("P3", 2.5, P.P3_BX_W - 4, P.P3_BY),
           T("JTAG", 2.5, P.JTAG_BX, P.JTAG_BY - 7.5), T("AS", 2.5, P.AS_BX, P.JTAG_BY - 7.5),
           T("DC", 2.5, (P.DCJ_BX[0] + P.DCJ_BX[1]) / 2 + 9, P.DCJ_BY[0] + 4),
           T("FOOTPRINT GAUGE", 2.5, 58, 108), T(f"HOLES {P.HOLE_PITCH_X:g} x {P.HOLE_PITCH_Y:g}", 2.5, 58, 112.5),
           T("N ↑", 3, 58, 103), T("RAIL OFF W EDGE", 2.2, -2.5, 30, True)]
    p1_end_y = P.P1_BY_N - 2.0 if P.P1_PIN1_END == "N" else P.P1_BY_N + P.P1_ROWS * PITCH + 2.0
    lab.append(T("1?", 2.2, P.P1_BX, p1_end_y))
    return g.cut(*lab).clean()


def insert_coupon() -> cq.Shape:
    """Heat-set insert, clearance and pilot test coupon: print FIRST, in the tub's PETG [D #11]."""
    s = cq.Solid.makeBox(64, 26, 9, cq.Vector(0, 0, 0))
    cuts = []
    for i, d in enumerate((3.8, 3.9, 4.0, 4.1, 4.2)):
        x = 7 + i * 12.5
        cuts.append(cq.Solid.makeCylinder(d / 2, INSERT_DEPTH + 0.01, cq.Vector(x, 18.5, 9 - INSERT_DEPTH)))
        cuts.append(_flat_text(f"{d:.1f}", 2.2, x, 12.5, 9))
    for i, d in enumerate((3.2, 3.4, 3.6, 1.5, 1.7, 1.9)):
        x = 6 + i * 10.4
        cuts.append(cq.Solid.makeCylinder(d / 2, 11, cq.Vector(x, 5.0, -1)))
    cuts.append(_flat_text("M3 INSERT", 2.2, 32, 24.0, 9))
    return s.cut(*cuts).clean()


def _flat_text(s, size, x, y, ztop, depth=ENGRAVE):
    pl = cq.Plane(origin=cq.Vector(x, y, ztop + 0.02), xDir=cq.Vector(1, 0, 0), normal=cq.Vector(0, 0, 1))
    return cq.Workplane(pl).text(s, size, -(depth + 0.02), combine=False, fontPath=FONT).val()


def centring_gauge() -> cq.Shape:
    """Spreader centring gauge [D #7]: rests on the package top, its E/W edges touch the P1 and P2
    bodies and its N edge touches P3; the 18.3 window puts the spreader on the package centre.
    Lift it off over the spreader before fitting the top plate. Made in print orientation,
    package-side down, in the board frame with x E and y N."""
    t = 1.2
    xw = P.P1_BX + PITCH + 0.1 - P.FPGA_BX          # P1 body E face, rel. FPGA centre
    xe = P.P2_BX - PITCH - 0.1 - P.FPGA_BX          # P2 body W face
    yn = P.FPGA_BY - (P.P3_BY + PITCH + 0.1)        # P3 body S face, distance N of centre
    g = cq.Solid.makeBox(xe - xw, yn + 14.0, t, cq.Vector(xw, -14.0, 0))
    w = SPREADER_WIN = P.SPREADER + 0.3
    g = g.cut(cq.Solid.makeBox(w, w, t + 2, cq.Vector(-w / 2, -w / 2, -1)))
    g = g.cut(_flat_text("GAUGE", 2.2, (xw + xe) / 2, -12.0, t, depth=0.5))
    return g.clean()


def drill_jig() -> cq.Shape:
    """Drill jig for the bridge + keel clamped as a pair (6.0 mm stack) [C §5.3, D #7, #8, #12].
    Inverted channel: the guide plate lies on the bed when printed; an end stop registers
    the bars' W ends. Guide holes: Ø3.2 for the Ø3.1 pair drill, Ø2.6 for tap drills."""
    L = BAR_LEN
    plate, skirt, inner = 6.0, 2.4, BAR_W + 0.4
    total_w = inner + 2 * skirt
    s = cq.Solid.makeBox(L + 3.0, total_w, plate + 2 * BAR_T + 0.2, cq.Vector(-3.0, -total_w / 2, 0))
    s = s.cut(cq.Solid.makeBox(L + 1, inner, 2 * BAR_T + 1, cq.Vector(0, -inner / 2, plate)))
    cuts = []
    holes = [(u - BAR_U0, v, 3.2, "B+K") for u, v in LEG_UV]
    holes += [(u - BAR_U0, v, 3.6, "K") for u, v in KEEL_SCREW_UV]
    holes += [(u - BAR_U0, v, 2.6, "K" if (abs(u) + abs(v)) > 0.1 else "C") for u, v in POST_UV]
    # The jig is turned over in use (guide plate on top of the bars), which maps print y -> -y,
    # so holes go in at y = -v and the bed-face labels are written to read from above in use.
    for x, v, d, lab in holes:
        cuts.append(cq.Solid.makeCylinder(d / 2, plate + 2, cq.Vector(x, -v, -1)))
    for x, v, d, lab in holes:
        pl = cq.Plane(origin=cq.Vector(x + 3.0, -v, -0.02), xDir=cq.Vector(1, 0, 0),
                      normal=cq.Vector(0, 0, -1))
        cuts.append(cq.Workplane(pl).text(lab, 2.2, -0.62, combine=False, fontPath=FONT, halign="left").val())
    return s.cut(*cuts).clean()


# ====================================================================== print orientation
def _bed(shape, rots=()):
    s = shape
    for axis, deg in rots:
        s = s.rotate(cq.Vector(0, 0, 0), cq.Vector(*axis), deg)
    bb = s.BoundingBox()
    return s.translate(cq.Vector(-(bb.xmin + bb.xmax) / 2, -(bb.ymin + bb.ymax) / 2, -bb.zmin))


def _p_lid():
    return _bed(lid_assembly(), [((1, 0, 0), 180)])               # top face down


def _p_panel():
    return _bed(panel_assembly(), [((0, 1, 0), -90)])             # outer (labelled) face down


def _p_blank():
    return _bed(usb_b_blank_assembly(), [((0, 1, 0), -90)])       # labelled plate on the bed, plug up


def _p_shroud():
    return _bed(shroud_assembly(), [((1, 0, 0), 180)])            # top down, blind pin holes open upward


def _p_scale():
    s = spring_scale_assembly().translate(cq.Vector(-FX, FY, 0)).rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), -TH_DEG)
    return _bed(s, [((1, 0, 0), -90)])                            # spine outer face (+v) down


PARTS = {
    "footprint_gauge": footprint_gauge,
    "insert_coupon": insert_coupon,
    "lid": _p_lid,
    "io_panel": _p_panel,
    "module_plate": lambda: _bed(plate_assembly()),
    "centring_gauge": centring_gauge,
    "usb_b_blank": _p_blank,
    "clk_in_shroud": _p_shroud,
    "la_comb": lambda: _bed(comb_assembly()),
    "spring_scale": _p_scale,
    "cable_clamp": lambda: _bed(cable_clamp_assembly(), [((1, 0, 0), 180)]),
    "ribbon_clip": lambda: _bed(ribbon_clip_assembly()),
    "drill_jig": drill_jig,
}
if P.SPLIT_BASE:
    PARTS["base_tub_w"] = lambda: _bed(_tub_split()[0])
    PARTS["base_tub_e"] = lambda: _bed(_tub_split()[1])
else:
    PARTS["base_tub"] = lambda: _bed(tub_assembly())


# ====================================================================== bought metal: clamp
def bridge_local(keel=False) -> cq.Shape:
    z0 = FLOOR_T if keel else P.BRIDGE_Z0
    s = LB(BAR_U0, BAR_U1, -BAR_W / 2, BAR_W / 2, z0, z0 + BAR_T)
    cuts = [LCZ(u, v, z0 - 1, z0 + BAR_T + 1, 3.1) for u, v in LEG_UV]
    if keel:
        cuts += [LCZ(u, v, z0 - 1, z0 + BAR_T + 1, M3_CLEAR) for u, v in KEEL_SCREW_UV]
        cuts += [LCZ(u, v, z0 - 1, z0 + BAR_T + 1, 3.0) for u, v in POST_UV]
    else:
        cuts.append(LCZ(0, 0, z0 - 1, z0 + BAR_T + 1, 6.0))
    return s.cut(*cuts)


def clamp_items() -> list:
    it = []
    it.append(Item("keel (Al 20x3)", to_bar(bridge_local(True)), AL, "bought"))
    it.append(Item("bridge (Al 20x3)", to_bar(bridge_local(False)), AL, "bought"))
    legs, scr, nuts, kscr = [], [], [], []
    for u, v in LEG_UV:
        x, y = uv_to_box(u, v)
        legs.append(HEX(x, y, FLOOR_T + BAR_T, P.BRIDGE_Z0, P.LEG_AF).cut(CZ(x, y, 0, 100, 3.0)))
        scr.append(fuse(CZ(x, y, P.BRIDGE_Z1, P.BRIDGE_Z1 + 1.65, 5.7), CZ(x, y, P.BRIDGE_Z0 - 5, P.BRIDGE_Z1, 3.0)))
    for u, v in KEEL_SCREW_UV:
        x, y = uv_to_box(u, v)
        nuts.append(HEX(x, y, FLOOR_T + BAR_T, FLOOR_T + BAR_T + P.M3_NUT_H, P.M3_NUT_AF).cut(CZ(x, y, 0, 20, 3.0)))
        kscr.append(fuse(CZ(x, y, -1.65, 0, 5.7), CZ(x, y, 0, FLOOR_T + BAR_T + P.M3_NUT_H, 3.0)))
    it.append(Item("legs (brass M3 standoffs, 2 per joint)", comp(*legs), BRASS, "bought"))
    it.append(Item("bridge screws (close-fit = locating pins)", comp(*scr), STEEL, "bought"))
    it.append(Item("keel nuts", comp(*nuts), STEEL, "bought"))
    it.append(Item("keel floor screws", comp(*kscr), STEEL, "bought"))
    # back-support post [D #8]: M-F standoff (stud flush in the tapped keel) + nylon screw + nylon nut
    z = FLOOR_T + BAR_T
    so = HEX(FX, FY, z, z + P.BACKPOST_SO, 5.5).cut(CZ(FX, FY, z + 1, z + 20, 3.0))
    sl, hd, hh = P.BACKPOST_SCREW
    head_top = PCB_BOT
    it.append(Item("back post standoff", so, BRASS, "bought"))
    nyl = fuse(CZ(FX, FY, head_top - hh, head_top, hd), CZ(FX, FY, head_top - hh - sl, head_top - hh, 3.0))
    nut = HEX(FX, FY, z + P.BACKPOST_SO, z + P.BACKPOST_SO + 2.4, 5.5).cut(CZ(FX, FY, 0, 40, 3.0))
    it.append(Item("back post nylon screw (tip)", nyl, NYLON, "bought"))
    it.append(Item("back post nylon nut", nut, NYLON, "bought"))
    # heater stack [D #1-5]
    it.append(Item("pad 0.5 (insulating)", BC(FX, FY, P.SPREADER, P.SPREADER, PKG_TOP, PKG_TOP + P.PAD_T), KAPTON, "bought"))
    sp = BC(FX, FY, P.SPREADER, P.SPREADER, SPREADER_Z0, TOP_Z0)
    gw, gd = P.TC_GROOVE
    sp = sp.cut(B(FX, FX + P.SPREADER, FY - gw / 2, FY + gw / 2, SPREADER_Z0 - 1, SPREADER_Z0 + gd))
    sp = sp.cut(*[CZ(x, y, TOP_Z0 - 6, TOP_Z0 + 1, 3.0) for x, y in TP_CSK])
    it.append(Item("spreader block (Al 18x18)", sp, (0.66, 0.69, 0.76), "bought"))
    it.append(Item("thermocouple bead + lead (in groove)", CX(FX - 0.5, FX + P.SPREADER / 2, FY, SPREADER_Z0 + gd / 2, 0.9),
                   (0.95, 0.85, 0.1), "bought"))
    tp = B(FX - BAR_W / 2, FX + BAR_W / 2, FY - P.TOP_PLATE_N, FY + P.TOP_PLATE_S, TOP_Z0, TOP_Z1)
    tp = tp.cut(*[CZ(x, y, TOP_Z0 - 1, TOP_Z1 + 1, 3.0) for x, y in TP_CSK])
    tp = tp.cut(*[cq.Solid.makeCone(1.5, 3.2, 1.7, V(x, y, TOP_Z1 - 1.7)) for x, y in TP_CSK])
    tp = tp.cut(*[CZ(x, y, TOP_Z0 - 1, TOP_Z1 + 1, 2.0) for x, y in HS10_EARS + STRAP_SCREWS])
    tp = tp.cut(*[CZ(x, y, TOP_Z0 - 1, TOP_Z1 + 1, 3.0) for x, y in POSTS])
    it.append(Item("top plate (Al 20x3)", tp, AL, "bought"))
    it.append(Item("top plate CSK screws", comp(*[fuse(cq.Solid.makeCone(1.5, 3.0, 1.5, V(x, y, TOP_Z1 - 1.5)),
                                                         CZ(x, y, TOP_Z1 - 8, TOP_Z1 - 1.5, 3.0)) for x, y in TP_CSK]),
                   STEEL, "bought"))
    # HS10 (Arcol datasheet outline), lugs N-S [D #3]
    h = P.HS10
    body = BC(FX, HS10_Y, h["D"], h["E"], TOP_Z1, TOP_Z1 + h["C"])
    ears = []
    for x, y in HS10_EARS:
        sx = 1 if x > FX else -1
        ears.append(B(FX + sx * h["D"] / 2 - sx * 0.01, x + sx * 2.2, y - 2.2, y + 2.2, TOP_Z1, TOP_Z1 + h["K"])
                    .cut(CZ(x, y, TOP_Z1 - 1, TOP_Z1 + 3, h["L"])))
    it.append(Item("HS10 heater", fuse(body, *ears), RED, "bought"))
    zl = TOP_Z1 + h["H"]
    tags = []
    for sgn in (-1, 1):
        y_end = HS10_Y + sgn * h["E"] / 2
        y_tip = HS10_Y + sgn * h["B"] / 2
        tags.append(B(FX - P.HS10_TAG_W / 2, FX + P.HS10_TAG_W / 2, y_end, y_tip, zl - 0.4, zl + 0.4))
        tags.append(CY(min(y_end + sgn * 0.5, y_tip + sgn * P.HS10_SLEEVE_PAST_TIP),
                       max(y_end + sgn * 0.5, y_tip + sgn * P.HS10_SLEEVE_PAST_TIP), FX, zl, P.HS10_SLEEVE_D))
    tag_shape = tags[0].fuse(*tags[1:]).clean()
    it.append(Item("HS10 tags + heat-shrink", tag_shape, BLACK, "bought"))
    it.append(Item("HS10 M2 screws", comp(*[fuse(CZ(x, y, TOP_Z1 + h["K"], TOP_Z1 + h["K"] + 1.3, 2.8),
                                                  CZ(x, y, TOP_Z1 + h["K"] - 4, TOP_Z1 + h["K"], 2.0)) for x, y in HS10_EARS]),
                   STEEL, "bought"))
    # KSD9700 on the S wing, over Kapton, under a screwed FR4 strap [D #4]
    kx = P.KSD[0] / 2
    it.append(Item("Kapton under KSD", B(FX - kx, FX + kx, KSD_Y0, KSD_Y1, TOP_Z1, TOP_Z1 + P.KAPTON_T), KAPTON, "bought"))
    kz0 = TOP_Z1 + P.KAPTON_T
    it.append(Item("KSD9700 75C thermostat (case live)", B(FX - kx, FX + kx, KSD_Y0, KSD_Y1, kz0, kz0 + P.KSD[2]),
                   GREY, "bought"))
    sz0 = kz0 + P.KSD[2]
    it.append(Item("strap spacers", comp(*[TUBE(x, y, TOP_Z1, sz0, 4.0, 2.0) for x, y in STRAP_SCREWS]), STEEL, "bought"))
    sw, st = P.STRAP
    strap = B(FX + P.STRAP_SCREW_X - sw / 2, FX + P.STRAP_SCREW_X + sw / 2, STRAP_SCREWS[0][1] - 2.5,
              STRAP_SCREWS[1][1] + 2.5, sz0, sz0 + st)
    strap = strap.cut(*[CZ(x, y, sz0 - 1, sz0 + 3, 2.0) for x, y in STRAP_SCREWS])
    it.append(Item("FR4 strap", strap, FR4, "bought"))
    it.append(Item("strap M2x8 screws", comp(*[fuse(CZ(x, y, sz0 + st, sz0 + st + 1.3, 3.8),
                                                     CZ(x, y, sz0 + st - 8, sz0 + st, 2.0)) for x, y in STRAP_SCREWS]),
                   STEEL, "bought"))
    # posts + pressure bar + ball + spring + adjuster [D #1, #6]
    it.append(Item("pressure-bar posts", comp(*[TUBE(x, y, TOP_Z1, P.PBAR_Z0, P.POST_D, 3.0) for x, y in POSTS]),
                   AL, "bought"))
    pb = BC(FX, FY, *P.PBAR, P.PBAR_Z0, P.PBAR_Z1)
    pb = pb.cut(*[CZ(x, y, P.PBAR_Z0 - 1, P.PBAR_Z1 + 1, M3_CLEAR) for x, y in POSTS])
    pb = pb.cut(cq.Solid.makeCone(0, P.CONE_D / 2 + 0.01, P.CONE_D / 2 + 0.01, V(FX, FY, P.PBAR_Z1 - P.CONE_D / 2)))
    it.append(Item("pressure bar (Al 20x3)", pb, AL, "bought"))
    it.append(Item("pressure-bar screws", comp(*[fuse(CZ(x, y, P.PBAR_Z1, P.PBAR_Z1 + 1.65, 5.7),
                                                       CZ(x, y, P.PBAR_Z1 - 6, P.PBAR_Z1, 3.0)) for x, y in POSTS]),
                   STEEL, "bought"))
    it.append(Item("steel ball", SPH(FX, FY, P.BALL_ZC, P.BALL_D), STEEL, "bought"))
    it.append(Item("spring cup (lower)", CZ(FX, FY, P.WASHER1_Z0, P.SPRING_Z0, P.WASHER[0]), STEEL, "bought"))
    it.append(Item("spring (8 N)", TUBE(FX, FY, P.SPRING_Z0, SPRING_Z1, P.SPRING_OD, P.SPRING_OD - 1.4), STEEL, "bought"))
    it.append(Item("spring cup (upper)", CZ(FX, FY, SPRING_Z1, ADJ_TIP, P.WASHER[0]), STEEL, "bought"))
    it.append(Item("M6 adjuster", CZ(FX, FY, ADJ_TIP, ADJ_TIP + P.ADJ_LEN, 6.0), STEEL, "bought"))
    it.append(Item("M6 jam nut", HEX(FX, FY, P.BRIDGE_Z1, P.BRIDGE_Z1 + P.JAM_NUT[1], P.JAM_NUT[0])
                   .cut(CZ(FX, FY, 0, 100, 6.0)), STEEL, "bought"))
    return it


# ====================================================================== reference: FPGA board
def board_items() -> list:
    it = []
    x0, y0 = BOARD_X0, BOARD_Y0
    pcb = B(x0, x0 + P.BOARD_W, y0, y0 + P.BOARD_L, PCB_BOT, PCB_TOP)
    pcb = pcb.cut(*[CZ(x, y, PCB_BOT - 1, PCB_TOP + 1, P.HOLE_D) for x, y in P.BOARD_HOLES])
    it.append(Item("FPGA board PCB", pcb, PCB_C, "reference"))
    it.append(Item("FPGA EP4CE6 package", BC(FX, FY, P.PKG_BODY, P.PKG_BODY, PCB_TOP, PKG_TOP), BLACK, "reference"))
    ring = BC(FX, FY, P.PKG_LEADS, P.PKG_LEADS, PCB_TOP, PCB_TOP + P.LEAD_TOP_H).cut(
        BC(FX, FY, P.PKG_BODY, P.PKG_BODY, PCB_TOP - 1, PCB_TOP + 5))
    it.append(Item("FPGA lead ring (22x22)", ring, (0.72, 0.72, 0.75), "reference"))
    so, sc = [], []
    for x, y in P.BOARD_HOLES:
        so.append(HEX(x, y, FLOOR_T, PCB_BOT, P.STANDOFF_AF).cut(CZ(x, y, 0, 40, 3.0)))
        sc.append(fuse(CZ(x, y, -1.65, 0, 5.7), CZ(x, y, 0, FLOOR_T + 6, 3.0)))
        sc.append(fuse(CZ(x, y, PCB_TOP, PCB_TOP + 1.65, 5.7), CZ(x, y, PCB_TOP - 6, PCB_TOP, 3.0)))
    it.append(Item("board standoffs", comp(*so), BRASS, "bought"))
    it.append(Item("board screws", comp(*sc), STEEL, "bought"))

    zt = PCB_TOP
    zp = zt + P.HDR_PLASTIC_H
    zpin = zt + P.HDR_PIN_H
    zd = zt + P.DUPONT_TOP_H

    def header(name, cols, rows, skip_rows=()):
        """cols/rows: lists of pin centre X and Y."""
        xs0, xs1 = min(cols) - PITCH / 2, max(cols) + PITCH / 2
        ys0, ys1 = min(rows) - PITCH / 2, max(rows) + PITCH / 2
        it.append(Item(f"{name} header", B(xs0, xs1, ys0, ys1, zt, zp), BLACK, "reference"))
        pins = [BC(x, y, 0.64, 0.64, zp, zpin) for x in cols for y in rows]
        it.append(Item(f"{name} pins", comp(*pins), BRASS, "reference"))
        envs = []
        for y in rows:
            if any(abs(y - s) < 0.1 for s in skip_rows):
                continue
            e = B(xs0, xs1, y - PITCH / 2, y + PITCH / 2, zp, zd)
            envs.append(e.cut(*[BC(x, y, 1.0, 1.0, zp - 1, zd + 1) for x in cols]))
        if envs:
            it.append(Item(f"{name} Dupont envelope", comp(*envs), (0.5, 0.5, 0.55), "reference", 0.18))

    p1_rows = [p1_row_y(r) for r in range(1, P.P1_ROWS + 1)]
    header("P1", [P1_X - PITCH / 2, P1_X + PITCH / 2], p1_rows, skip_rows=[p1_row_y(r) for r in CLK_ROWS])
    header("P2", [P2_X - PITCH / 2, P2_X + PITCH / 2], [P2_Y_N + (r - 0.5) * PITCH for r in range(1, P.P2_ROWS + 1)])
    header("P3", [P3_X_W + (c - 0.5) * PITCH for c in range(1, P.P3_COLS + 1)], [P3_Y - PITCH / 2, P3_Y + PITCH / 2])
    for nm, cx in (("JTAG", P.JTAG_BX), ("AS", P.AS_BX)):
        it.append(Item(f"{nm} box header", BC(x0 + cx, JTAG_Y, P.BOXHDR_L, P.BOXHDR_W, zt, zt + P.BOXHDR_H), BLACK, "reference"))
    il, iw, ih = P.IDC_PLUG
    zi = zt + P.BOXHDR_H
    it.append(Item("USB-Blaster IDC plug (seated)", BC(JTAG_X, JTAG_Y, il, iw, zi, zi + ih), GREY, "reference"))
    # ribbon: up from the plug, S over the board edge, down, W on edge through the clip, into the dongle
    rw = P.RIBBON_W
    zr = zi + ih
    ry0, ry1 = RIBBON_Y
    rib = [B(JTAG_X - rw / 2, JTAG_X + rw / 2, JTAG_Y - 0.5, JTAG_Y + 0.5, zr, zr + 7.0),
           B(JTAG_X - rw / 2, JTAG_X + rw / 2, JTAG_Y - 0.5, ry1, zr + 6.0, zr + 7.0),
           B(JTAG_X - rw / 2, JTAG_X + rw / 2, ry0, ry1, 12.0 + rw, zr + 6.0),
           B(P.BLASTER_X0 - 6.0, JTAG_X + rw / 2, ry0, ry1, 12.0, 12.0 + rw),
           B(P.BLASTER_X0 - 6.0, P.BLASTER_X0 - 5.0, ry1, BLASTER_YC + 0.5, 12.0, 12.0 + rw),
           B(P.BLASTER_X0 - 5.0, P.BLASTER_X0, BLASTER_YC - 0.5, BLASTER_YC + 0.5, 12.0, 12.0 + rw)]
    it.append(Item("JTAG ribbon", rib[0].fuse(*rib[1:]).clean(), (0.72, 0.72, 0.75), "reference"))
    # other board parts (photo-estimates, [BM])
    dsub = []
    for bx0, bx1 in (P.DB9_BX, P.VGA_BX):
        cx = x0 + (bx0 + bx1) / 2
        dsub.append(fuse(B(x0 + bx0, x0 + bx1, y0, y0 + 12.0, zt, zt + P.DSUB_FLANGE_H),
                         B(cx - 8, cx + 8, y0 - P.DSUB_OVERHANG, y0, zt + 2.0, zt + 10.5)))
    it.append(Item("DB9 + VGA", comp(*dsub), (0.62, 0.62, 0.66), "reference"))
    it.append(Item("PS/2", B(x0 + P.PS2_BX[0], x0 + P.PS2_BX[1], y0, y0 + P.PS2_DEPTH, zt, zt + 13), (0.6, 0.6, 0.6), "reference"))
    s7 = P.SEG7
    it.append(Item("7-segment", B(x0 + s7[0], x0 + s7[1], y0 + s7[2], y0 + s7[3], zt, zt + s7[4]), BLACK, "reference"))
    lc = P.LCD_SOCKET
    it.append(Item("LCD socket", B(x0 + lc[0], x0 + lc[1], y0 + lc[2], y0 + lc[3], zt, zt + lc[4]), BLACK, "reference"))
    keys = [fuse(BC(x0 + P.KEYS_BX, y0 + ky, 6, 6, zt, zt + 3.5), CZ(x0 + P.KEYS_BX, y0 + ky, zt + 3.5, zt + 5.0, 3.5))
            for ky in P.KEYS_BY]
    keys.append(fuse(BC(x0 + P.RESET_KEY[0], y0 + P.RESET_KEY[1], 6, 6, zt, zt + 3.5),
                     CZ(x0 + P.RESET_KEY[0], y0 + P.RESET_KEY[1], zt + 3.5, zt + 5.0, 3.5)))
    it.append(Item("keys + RESET", comp(*keys), BLACK, "reference"))
    it.append(Item("IR receiver", BC(x0 + P.IR[0], y0 + P.IR[1], 5, 6, zt, zt + 6.5), BLACK, "reference"))
    it.append(Item("DIP switch", BC(x0 + P.DIP[0], y0 + P.DIP[1], P.DIP[2], P.DIP[3], zt, zt + 4), RED, "reference"))
    bz = P.BUZZER
    it.append(Item("buzzer", CZ(x0 + bz[0], y0 + bz[1], zt, zt + bz[3], bz[2]), BLACK, "reference"))
    po = P.POT
    it.append(Item("contrast pot", B(x0 + po[0], x0 + po[1], y0 + po[2], y0 + po[3], zt, zt + 5), (0.2, 0.3, 0.8), "reference"))
    le = P.LEDS
    it.append(Item("LED1-4", B(x0 + le[0], x0 + le[1], y0 + le[2], y0 + le[3], zt, zt + 0.8), (1.0, 0.2, 0.1), "reference"))
    sh = P.USBB_SHELL
    usbb = B(USBB_X0, USBB_X0 + sh[2], USBB_Y - sh[0] / 2, USBB_Y + sh[0] / 2, zt, zt + sh[1]).cut(
        B(USBB_X0 - 1, USBB_X0 + 10, USBB_Y - 4.225, USBB_Y + 4.225, USBB_ZC - 3.89, USBB_ZC + 3.89))
    it.append(Item("USB-B socket (power only)", usbb, (0.75, 0.75, 0.78), "reference"))
    dj0, dj1 = x0 + P.DCJ_BX[0], x0 + P.DCJ_BX[1]
    it.append(Item("board DC jack", B(dj0, dj1, y0 + P.DCJ_BY[0], y0 + P.DCJ_BY[1], zt, zt + P.DCJ_H), BLACK, "reference"))
    pl_, pd_ = P.RA_DC_PLUG
    jy1 = y0 + P.DCJ_BY[1]
    it.append(Item("R/A DC plug (metered 5V pigtail)", B((dj0 + dj1) / 2 - pd_ / 2, (dj0 + dj1) / 2 + pd_ / 2, jy1, jy1 + pl_,
                                                         zt + 0.5, zt + 0.5 + pd_), (0.28, 0.28, 0.30), "reference"))
    swx = (x0 + P.SW_BX[0], x0 + P.SW_BX[1])
    swy = (y0 + P.SW_BY[0], y0 + P.SW_BY[1])
    it.append(Item("power switch (DPDT)", B(*swx, *swy, zt, zt + P.SW_BODY_H), BLACK, "reference"))
    it.append(Item("switch cap UP (worst case)", CZ(sum(swx) / 2, sum(swy) / 2, zt + P.SW_BODY_H, zt + P.SW_CAP_UP_H, 6.0),
                   RED, "reference"))
    return it


# ====================================================================== bought + reference: bay, panel, Blaster
def bay_items() -> list:
    it = []
    z1 = PLATE_Z1
    # plate screws
    it.append(Item("module-plate screws", comp(*[fuse(CZ(x, y, z1, z1 + 1.65, 5.5), CZ(x, y, z1 - 6, z1, 3.0))
                                                 for x, y in P.PLATE_BOSSES]), STEEL, "bought"))
    # Pico 2H on printed standoffs, header strips below
    px, py, pz = PICO_X0, P.PICO_Y0, PICO_Z0
    pico = B(px, px + P.PICO[0], py, py + P.PICO[1], pz, pz + P.PICO[2])
    pico = pico.fuse(B(px - P.PICO_USB_OVERHANG, px + 4.4, PICO_YC - 3.79, PICO_YC + 3.79, pz + P.PICO[2], pz + P.PICO[2] + 2.73))
    hdr = [B(px + 1.0, px + P.PICO[0] - 1.0, py + yy - 1.27, py + yy + 1.27, pz - 2.5, pz) for yy in (1.61, P.PICO[1] - 1.61)]
    hdr += [B(px + 1.0, px + P.PICO[0] - 1.0, py + yy - 0.32, py + yy + 0.32, z1 + 0.5, pz - 2.5) for yy in (1.61, P.PICO[1] - 1.61)]
    it.append(Item("Pico 2H", pico.clean(), (0.20, 0.75, 0.30), "reference"))
    it.append(Item("Pico header strips", comp(*hdr), BLACK, "reference"))
    la = B(LA_X0, LA_X0 + P.LA[0], P.LA_Y0, P.LA_Y0 + P.LA[1], z1, z1 + P.LA[2])
    it.append(Item("logic analyser (TOL-18627)", la, (0.85, 0.12, 0.12), "reference"))
    it.append(Item("AO3400 fan switch", B(7.0, 7.0 + P.AO3400[0], 82.0, 82.0 + P.AO3400[1], z1, z1 + P.AO3400[2]),
                   (0.55, 0.30, 0.85), "reference"))
    it.append(Item("5V load switch", B(7.0, 7.0 + P.LOADSW[0], 102.0, 102.0 + P.LOADSW[1], z1, z1 + P.LOADSW[2]),
                   (0.40, 0.55, 0.85), "reference"))
    end = P.P1_PIN1_END
    b0, b1 = SI_BOARD[end]
    w0, w1 = SI_WALL[end]
    toward = -1 if end == "N" else 1                            # components face the wall
    comp_y = (b0 - P.SI5351_H, b0) if end == "N" else (b1, b1 + P.SI5351_H)
    si = fuse(B(SI_X0, SI_X1, b0, b1, SI_Z0, SI_Z1), B(SI_X0 + 4, SI_X1 - 5, *comp_y, SI_Z0 + 6, SI_Z1 - 6))
    it.append(Item("Si5351 (active position, on edge)", si, (0.10, 0.75, 0.85), "reference"))
    sp_y = (w1, b0) if end == "N" else (b1, w0)
    it.append(Item("Si5351 M2.5 spacers + screws", comp(*[fuse(CY(sp_y[0], sp_y[1], x, z, 4.5).cut(CY(sp_y[0] - 1, sp_y[1] + 1, x, z, 2.5)))
                                                           for x, z in SI_HOLES_XZ]), BRASS, "bought"))
    mx0, my0 = 7.0, 125.0
    mz = z1 + 3.0
    mx = fuse(B(mx0, mx0 + P.MAX31855[1], my0, my0 + P.MAX31855[0], mz, mz + 1.6),
              B(mx0 + 15.5, mx0 + P.MAX31855[1], my0 + 5.0, my0 + 15.3, mz + 1.6, mz + 1.6 + P.MAX_TERM_H))
    it.append(Item("MAX31855", mx, (0.15, 0.35, 0.90), "reference"))
    ix0, iy0 = 30.0, 137.0
    it.append(Item("INA226 (CJMCU-226)", B(ix0, ix0 + P.INA226[0], iy0, iy0 + P.INA226[1], z1 + 3.0, z1 + 3.0 + P.INA226[2]),
                   (0.95, 0.45, 0.60), "reference"))
    dx0, dy0 = 26.0, 159.0
    it.append(Item("D4184 heater MOSFET", B(dx0, dx0 + P.D4184[0], dy0, dy0 + P.D4184[1], z1 + 3.0, z1 + 3.0 + P.D4184[2]),
                   (0.30, 0.85, 0.60), "reference"))
    it.append(Item("star ground (lever block)", B(6.5, 6.5 + P.STAR[1], 150.0, 150.0 + P.STAR[0], z1, z1 + P.STAR[2]),
                   (0.95, 0.85, 0.15), "reference"))
    # BME280 in the intake duct, board vertical, parallel to the flow [D #25]
    by0 = P.FAN_YC - P.FAN / 2 + BME_SO
    bme = B(PX1 + 1.0, PX1 + 1.0 + P.BME[1], by0, by0 + P.BME[2], P.FAN_ZC - P.BME[0] / 2, P.FAN_ZC + P.BME[0] / 2)
    bme = bme.fuse(B(PX1 + 4, PX1 + 12, by0 + P.BME[2], by0 + P.BME[3], P.FAN_ZC - 4, P.FAN_ZC + 4))
    it.append(Item("BME280 (intake)", bme.clean(), (0.85, 0.20, 0.75), "reference"))
    # fan
    fy, fz = P.FAN_YC, P.FAN_ZC
    hp = P.FAN_HOLE_PITCH / 2
    fan = B(FAN_X0, FAN_X0 + P.FAN_T, fy - P.FAN / 2, fy + P.FAN / 2, fz - P.FAN / 2, fz + P.FAN / 2)
    fan = fan.cut(CX(FAN_X0 - 1, FAN_X0 + P.FAN_T + 1, fy, fz, 37.0))
    fan = fan.cut(*[CX(FAN_X0 - 1, FAN_X0 + P.FAN_T + 1, fy + sy * hp, fz + sz * hp, P.FAN_HOLE_D)
                    for sy in (-1, 1) for sz in (-1, 1)])
    hub = CX(FAN_X0 + 1, FAN_X0 + P.FAN_T, fy, fz, 17.0)
    it.append(Item("fan 4010 (5 V)", comp(fan, hub), (0.18, 0.18, 0.20), "bought"))
    it.append(Item("fan screws", comp(*[fuse(CX(FAN_X0 + P.FAN_T, FAN_X0 + P.FAN_T + 1.65, fy + sy * hp, fz + sz * hp, 5.5),
                                             CX(FAN_X0 + P.FAN_T - 16, FAN_X0 + P.FAN_T, fy + sy * hp, fz + sz * hp, 3.0))
                                        for sy in (-1, 1) for sz in (-1, 1)]), STEEL, "bought"))
    # panel hardware
    y, z = PORT["usbc"]
    usbc = fuse(B(PX0, PX1, y - P.USBC_CUT[0] / 2 + 0.05, y + P.USBC_CUT[0] / 2 - 0.05, z - P.USBC_CUT[1] / 2 + 0.05,
                  z + P.USBC_CUT[1] / 2 - 0.05),
                B(PX1, PX1 + 1.5, y - 11, y + 11, z - 4.5, z + 4.5).cut(*[CX(PX1 - 1, PX1 + 3, y + s * P.USBC_SCREWS, z, 3.0)
                                                                         for s in (-1, 1)]),
                BC(PX1 + 1.5 + P.USBC_BODY[2] / 2, y, P.USBC_BODY[2], P.USBC_BODY[0], z - P.USBC_BODY[1] / 2, z + P.USBC_BODY[1] / 2))
    it.append(Item("USB-C 5V panel socket (5.1k CC)", usbc, (0.70, 0.70, 0.74), "bought"))
    y, z = PORT["fuse"]
    fh = fuse(CX(PX0, PX1, y, z, P.FUSE_HOLE - 0.1), CX(PX1, PX1 + P.FUSE_BODY[1], y, z, P.FUSE_BODY[0]),
              CX(PX0 - 10, PX0, y, z, 15.0))
    it.append(Item("fuse holder 1A fast", fh, BLACK, "bought"))
    y, z = PORT["jack"]
    jk = fuse(CX(PX0, PX1, y, z, P.JACK12_HOLE - 0.1), CX(PX1, PX1 + P.JACK12_BODY[1], y, z, P.JACK12_BODY[0]),
              CX(PX0 - 2.0, PX0, y, z, 12.0))
    it.append(Item("12V panel jack", jk, (0.25, 0.25, 0.27), "bought"))
    # USB-Blaster inside, cable through the clamp [D #21]
    bl = B(P.BLASTER_X0, BLASTER_X1, BLASTER_Y0, BLASTER_Y1, FLOOR_T, FLOOR_T + P.BLASTER[1])
    it.append(Item("USB-Blaster dongle", bl, (0.15, 0.30, 0.70), "reference"))
    plug = B(BLASTER_X1, BLASTER_X1 + P.BLASTER_PLUG_L, BLASTER_YC - 4.0, BLASTER_YC + 4.0, P.CABLE_Z - 3.5, P.CABLE_Z + 3.5)
    cab = CX(BLASTER_X1 + P.BLASTER_PLUG_L, BOX_X + 15, BLASTER_YC, P.CABLE_Z, P.BLASTER_CABLE_D)
    it.append(Item("Blaster USB plug + cable", fuse(plug, cab), BLACK, "reference"))
    it.append(Item("clamp + clip screws", comp(*[fuse(CZ(x, y, CLAMP_Z0 + 6, CLAMP_Z0 + 7.65, 5.5), CZ(x, y, PED_TOP - 5, CLAMP_Z0 + 6, 2.5))
                                                for x, y in CLAMP_HOLES],
                                              *[fuse(CZ(x, y, P.PLATE_Z0 + 3, P.PLATE_Z0 + 4.65, 5.5), CZ(x, y, P.PLATE_Z0 - 5, P.PLATE_Z0 + 3, 3.0))
                                                for x, y in COMB_BOSSES + [RIBBON_CLIP_BOSS]]), STEEL, "bought"))
    # rubber feet
    it.append(Item("rubber feet", comp(*[CZ(x, y, -P.FOOT[1], 0, P.FOOT[0]) for x, y in
                                         ((12, 12), (BOX_X - 12, 12), (12, BOX_Y - 12), (BOX_X - 12, BOX_Y - 12))]), BLACK, "bought"))
    return it


def lid_items() -> list:
    it = []
    z0 = TUB_H
    acr = B(*ACR, z0 + 0.3, z0 + 0.3 + P.ACRYLIC_T).cut(*[CZ(x, y, z0 - 1, z0 + 10, 3.5) for x, y in ACR_HOLES])
    it.append(Item("acrylic window 3 mm", acr, ACRYLIC, "bought", 0.28, True))
    hd, hh, ln = P.THUMB
    th = [fuse(CZ(x, y, LID_TOP, LID_TOP + hh, hd), CZ(x, y, z0, LID_TOP, 2.4), CZ(x, y, LID_TOP - ln, z0, 3.0))
          for x, y in P.LID_BOSS]
    it.append(Item("captive knurled thumbscrews", comp(*th), STEEL, "bought", 1.0, True))
    sc = [fuse(CZ(x, y, LID_TOP, LID_TOP + 1.65, 5.7), CZ(x, y, LID_TOP - 10, LID_TOP, 3.0)) for x, y in ACR_HOLES]
    nu = [HEX(x, y, z0 + 0.3 - 4.0, z0 + 0.3, 5.5).cut(CZ(x, y, 0, 200, 3.0)) for x, y in ACR_HOLES]
    it.append(Item("window screws + nyloc nuts", comp(*sc, *nu), STEEL, "bought", 1.0, True))
    return it


# ====================================================================== the assembly
def ASSEMBLY() -> list:
    items = []
    if P.SPLIT_BASE:
        w, e = _tub_split()
        items += [Item("base tub W", w, PETG, "printed"), Item("base tub E", e, PETG, "printed")]
    else:
        items.append(Item("base tub", tub_assembly(), PETG, "printed"))
    items.append(Item("W I/O panel", panel_assembly(), PETG, "printed"))
    items.append(Item("module plate", plate_assembly(), PETG, "printed"))
    items.append(Item("lid", lid_assembly(), PETG, "printed", 1.0, True))
    items.append(Item("USB-B blank", usb_b_blank_assembly(), PETG_SMALL, "printed"))
    items.append(Item("CLK-IN shroud", shroud_assembly(), PETG_SMALL, "printed"))
    items.append(Item("LA comb", comb_assembly(), PETG_SMALL, "printed"))
    items.append(Item("spring scale", spring_scale_assembly(), PETG_SMALL, "printed"))
    items.append(Item("Blaster cable clamp", cable_clamp_assembly(), PETG_SMALL, "printed"))
    items.append(Item("ribbon clip", ribbon_clip_assembly(), PETG_SMALL, "printed"))
    items += clamp_items()
    items += board_items()
    items += bay_items()
    items += lid_items()
    return items


# Intended volumetric contact. Every contact in this model is built face-to-face (screws in
# clearance or screw-sized holes, parts resting on parts), so none is needed. Add a pair
# here only with a comment saying why the overlap is real.
ALLOWED_OVERLAPS: set = set()

# Sections through the FPGA centre (world coordinates; world y = -box Y).
SECTIONS = {
    "clamp_ew": ((FX, -FY + 0.05, 0.0), (0.0, 1.0, 0.0)),   # keep the N half, look N from the S face
    "clamp_ns": ((FX - 0.05, -FY, 0.0), (1.0, 0.0, 0.0)),   # keep the E half, look E from the W face
}


# ====================================================================== DXF drawings of the bar parts
def export_dxf(out_dir=os.path.join(HERE, "parts")) -> list:
    import ezdxf

    os.makedirs(out_dir, exist_ok=True)
    written = []

    def new(title, notes):
        doc = ezdxf.new("R2010", setup=True)
        doc.units = ezdxf.units.MM
        for name, col in (("OUTLINE", 7), ("HOLES", 1), ("TEXT", 3), ("DIM", 5), ("HIDDEN", 8)):
            doc.layers.add(name, color=col)
        msp = doc.modelspace()
        return doc, msp, title, notes

    table = []

    def finish(doc, msp, title, notes, fname, ytext, xtab=0.0, ytab=None):
        y = ytext
        msp.add_text(title, height=3.5, dxfattribs={"layer": "TEXT"}).set_placement((0, y))
        for n in notes:
            y -= 5
            msp.add_text(n, height=2.5, dxfattribs={"layer": "TEXT"}).set_placement((0, y))
        y = ytab if ytab is not None else y - 7
        msp.add_text("HOLE TABLE (mm, same origin and axes as the drawing):", height=2.5,
                     dxfattribs={"layer": "TEXT"}).set_placement((xtab, y))
        for i, (x, yy, d, lab) in enumerate(table, 1):
            y -= 4
            msp.add_text(f"{i:>2}  x {round(x, 2) + 0.0:8.2f}   y {round(yy, 2) + 0.0:7.2f}   dia {d:4.1f}   {lab}",
                         height=2.2, dxfattribs={"layer": "TEXT"}).set_placement((xtab, y))
        table.clear()
        p = os.path.join(out_dir, fname)
        doc.saveas(p)
        written.append(p)

    def rect(msp, x0, y0, x1, y1, layer="OUTLINE"):
        msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={"layer": layer})

    def hole(msp, x, y, d, label=""):
        table.append((x, y, d, label))
        msp.add_circle((x, y), d / 2, dxfattribs={"layer": "HOLES"})
        msp.add_line((x - d, y), (x + d, y), dxfattribs={"layer": "HIDDEN"})
        msp.add_line((x, y - d), (x, y + d), dxfattribs={"layer": "HIDDEN"})
        msp.add_text(str(len(table)), height=1.6, dxfattribs={"layer": "TEXT"}).set_placement((x + d / 2 + 0.6, y + 0.6))

    def dim(msp, p1, p2, base, angle=0):
        # explicit text: the EZDXF style drops the decimal point in this ezdxf version (77.53 -> "7753")
        val = abs(p2[1] - p1[1]) if angle == 90 else abs(p2[0] - p1[0])
        msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=angle, dimstyle="EZDXF", text=f"{val:.2f}",
                           override={"dimtxt": 2.0, "dimasz": 1.5},
                           dxfattribs={"layer": "DIM"}).render()

    # bridge and keel: local u from the W end, v across
    for keel in (False, True):
        nm = "keel" if keel else "bridge"
        doc, msp, title, notes = new(
            f"LAB BOX {nm.upper()} - Al flat bar 20 x {BAR_T:g}, {BAR_LEN:.1f} long (cut from the 1 m bar)",
            ["Drill bridge + keel CLAMPED AS A PAIR through the printed drill_jig (holes marked B+K).",
             "Leg holes: drill 3.1 close-fit through both (the screws are the locating pins, DESIGN #7).",
             "Bridge only: centre hole tap M6 (5.0 drill)." if not keel else
             "Keel only: countersink the 4 leg holes from BELOW (M3 CSK, flush); floor-screw holes 3.4;",
             "" if not keel else "post sites (centre C and 4 x K): tap M3 (2.5 drill), centre site used first (DESIGN #8).",
             f"Bar skew in the box: {TH_DEG:.1f} deg (W end south) so the W legs clear the fan jet (DESIGN #24).",
             "All positions are from params.py MEASURE values: re-export after measuring the board."])
        rect(msp, 0, -BAR_W / 2, BAR_LEN, BAR_W / 2)
        for u, v in LEG_UV:
            hole(msp, u - BAR_U0, v, 3.1, "3.1 B+K" + (" CSK" if keel else ""))
        if keel:
            for u, v in KEEL_SCREW_UV:
                hole(msp, u - BAR_U0, v, M3_CLEAR, "3.4 K")
            for u, v in POST_UV:
                hole(msp, u - BAR_U0, v, 2.5, "M3")
        else:
            hole(msp, -BAR_U0, 0, 6.0, "M6")
        xs = sorted({round(u - BAR_U0, 2) for u, _ in LEG_UV} | ({round(u - BAR_U0, 2) for u, _ in KEEL_SCREW_UV} if keel else set())
                    | {round(-BAR_U0, 2)})
        for x in xs:
            dim(msp, (0, -BAR_W / 2), (x, -BAR_W / 2), (0, -BAR_W / 2 - 8 - 4 * xs.index(x)))
        dim(msp, (0, -BAR_W / 2), (0, BAR_W / 2), (-8, 0), 90)
        finish(doc, msp, title, [n for n in notes if n], f"{nm}.dxf", BAR_W / 2 + 36, xtab=BAR_LEN + 12, ytab=BAR_W / 2 + 4)

    # top plate: local x E, y N, origin at the FPGA centre
    doc, msp, title, notes = new(
        f"LAB BOX TOP PLATE - Al 20 x {BAR_T:g} bar, {P.TOP_PLATE_N + P.TOP_PLATE_S:g} long (N-S)",
        ["Origin = FPGA centre. +y = NORTH. The HS10 sits 2 mm S of centre; KSD9700 on the S wing.",
         "CSK: M3 countersunk, flush, into the spreader (tap spreader M3 x 6 blind).",
         "HS10 + strap holes: tap M2 through; screws must not protrude below the plate (DESIGN #10).",
         "Post holes: tap M3 through; M-F spacer studs cut to 2.5 mm."])
    rect(msp, -BAR_W / 2, -P.TOP_PLATE_S, BAR_W / 2, P.TOP_PLATE_N)
    for x, y in TP_CSK:
        hole(msp, x - FX, -(y - FY), 3.0, "M3 CSK")
    for x, y in HS10_EARS:
        hole(msp, x - FX, -(y - FY), 1.6, "M2 HS10")
    for x, y in STRAP_SCREWS:
        hole(msp, x - FX, -(y - FY), 1.6, "M2 strap")
    for x, y in POSTS:
        hole(msp, x - FX, -(y - FY), 2.5, "M3 post")
    rect(msp, -P.KSD[0] / 2, -(KSD_Y1 - FY), P.KSD[0] / 2, -(KSD_Y0 - FY), layer="HIDDEN")
    rect(msp, -P.SPREADER / 2, -P.SPREADER / 2, P.SPREADER / 2, P.SPREADER / 2, layer="HIDDEN")
    dim(msp, (-BAR_W / 2, -P.TOP_PLATE_S), (-BAR_W / 2, P.TOP_PLATE_N), (-BAR_W / 2 - 8, 0), 90)
    finish(doc, msp, title, notes, "top_plate.dxf", P.TOP_PLATE_N + 25, xtab=BAR_W / 2 + 12, ytab=P.TOP_PLATE_N)

    # spreader
    doc, msp, title, notes = new(
        f"LAB BOX SPREADER - Al {P.SPREADER:g} x {P.SPREADER:g} x {P.SPREADER_H:g} (20 sq bar filed to 18, DESIGN 9.2)",
        ["Contact face (bottom) flat, edges broken; Kapton on edges (DESIGN #2).",
         f"TC groove in the CONTACT face: {P.TC_GROOVE[0]:g} wide x {P.TC_GROOVE[1]:g} deep, centre to the E face, Kapton-lined (DESIGN #5).",
         "Top face: 2 x M3 blind tapped 6 deep for the top-plate CSK screws.",
         "Top view, origin = FPGA centre, +x = EAST, +y = NORTH."])
    h = P.SPREADER / 2
    rect(msp, -h, -h, h, h)
    for x, y in TP_CSK:
        hole(msp, x - FX, -(y - FY), 2.5, "M3x6 blind")
    gw = P.TC_GROOVE[0] / 2
    rect(msp, 0, -gw, h, gw, layer="HIDDEN")
    dim(msp, (-h, -h), (h, -h), (0, -h - 8))
    finish(doc, msp, title, notes, "spreader.dxf", h + 25, xtab=h + 12, ytab=h)

    # pressure bar
    doc, msp, title, notes = new(
        f"LAB BOX PRESSURE BAR - Al 20 x {BAR_T:g} bar, {P.PBAR[0]:g} long (E-W)",
        [f"Centre: 90 deg countersink, {P.CONE_D:g} top dia, for the {P.BALL_D:g} ball (cone seat, DESIGN #1).",
         "2 x 3.4 holes onto the posts (M3 button heads).", "Origin = FPGA centre, +x = EAST, +y = NORTH."])
    rect(msp, -P.PBAR[0] / 2, -P.PBAR[1] / 2, P.PBAR[0] / 2, P.PBAR[1] / 2)
    hole(msp, 0, 0, P.CONE_D, "CSK 90")
    for x, y in POSTS:
        hole(msp, x - FX, -(y - FY), M3_CLEAR, "3.4")
    finish(doc, msp, title, notes, "pressure_bar.dxf", P.PBAR[1] / 2 + 25, xtab=P.PBAR[0] / 2 + 12, ytab=P.PBAR[1] / 2)
    return written


if __name__ == "__main__":
    for p in export_dxf():
        print("wrote", p)
