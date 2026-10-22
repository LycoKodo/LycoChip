"""Every dimension of the Agent Lab Box, in one place.

Units: mm. Frames (as DESIGN.md §4 and concepts/simple-first.md §1):

  board frame  bx from the board's W (USB-B/LCD) edge, by from its N (DB9/VGA) edge.
  box frame    origin at the tub's outer NW bottom corner; X east, Y SOUTH, Z up from
               the underside of the floor.  box = board + (BOARD_X0, BOARD_Y0).

Sources are abbreviated to the research note that holds them:
  [BM] docs/lab-box/research/board-mechanical.md     [TM] .../modules-thermal-mech.md
  [ME] .../modules-electronics.md                     [TS] .../thermal-safety.md
  [CP] .../clock-pins.md   [BP] .../board-power.md   [SU] .../suppliers-au.md
  [D]  cad/lab-box/DESIGN.md (section number)        [C]  concepts/simple-first.md

Anything that comes from a photo-estimate, a listing for a part not yet bought, or a
choice that depends on the real part goes through MEASURE(). make.py prints the list.
Nothing here has been measured on Alex's hardware (2026-10-23).
"""
from __future__ import annotations

import inspect
import math
import re

_MEASURES: list = []


def MEASURE(value, what, how=""):
    """Register a placeholder that must be measured on the real part; return value."""
    name = "?"
    try:
        ctx = inspect.stack()[1].code_context
        if ctx:
            m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=", ctx[0])
            if m:
                name = m.group(1)
    except Exception:  # noqa: BLE001
        pass
    _MEASURES.append((name, what, value, how))
    return value


def measure_report() -> list:
    return [f"{n}/{w} = {v!r} — {h}" if h else f"{n}/{w} = {v!r}" for n, w, v, h in _MEASURES]


# =============================================================== printer
BED_X = 220            # [D §9.1] CAD default until Alex names the printer
BED_Y = 220
BED_Z = 250
BED_MARGIN = 5         # [D §3.3 #17] every part >= 5 mm inside the bed
SPLIT_BASE = False     # [D #17] split the tub at SPLIT_X when the bed is too small
SPLIT_X = 64.0         # just E of the module bay (bay X 6-63)

# =============================================================== fasteners and print fits
INSERT_D = 4.0         # [TM] CNC Kitchen / ruthex M3 x 5.7 insert: hole 4.0
INSERT_DEPTH = 6.7     # [TM] L 5.7 + 1 mm
INSERT_BOSS_D = 9.0    # [TM] >= 4.0 + 2 x 1.6 = 7.2; 9 gives 2.5 mm wall
M3_CLEAR = 3.4         # [TM] ISO 273 medium
M3 = 3.0
M2_CLEAR = 2.4
M2_PILOT = 1.7         # self-tapping M2 into PETG (coupon tests 1.5/1.7/1.9)
M25_PILOT = 2.1
M3_NUT_AF = 5.5        # [TM] ISO 4032
M3_NUT_H = 2.4
M3_HEAD_D = 5.5        # [TM] ISO 4762 / button head
FIT = 0.3              # [TM] sliding fit 0.2-0.3
ENGRAVE = 0.6          # task brief: text cut ~0.6 deep
FONT = "C:/Windows/Fonts/arialbd.ttf"   # checked 2026-10-23: renders → ° · ² — on this PC

# =============================================================== the FPGA board  [BM]
BOARD_W = MEASURE(106.0, "PCB width E-W", "calipers, acrylic off [BM caption 136x106, unverified]")
BOARD_L = MEASURE(136.0, "PCB length N-S", "calipers [BM]")
PCB_T = MEASURE(1.6, "PCB thickness", "calipers at an edge [BM: unknown, FR-4 default]")
BOARD_CORNER_R = MEASURE(2.5, "PCB corner radius", "radius gauge [BM photo 2-3]")
HOLE_INSET = MEASURE(5.0, "mounting-hole centre inset from W and N edges", "edge to hole edge + r [BM 4.5-6]")
HOLE_PITCH_X = MEASURE(96.0, "hole pitch E-W", "calipers across hole edges [BM: derived from caption, UNVERIFIED]")
HOLE_PITCH_Y = MEASURE(126.0, "hole pitch N-S", "calipers [BM: UNVERIFIED, most likely to ruin a print]")
HOLE_D = MEASURE(3.0, "mounting hole diameter", "pin gauge [BM ~3]")
BOARD_STANDOFF = MEASURE(15.0, "floor-to-PCB standoff length", "choose from stock [C §1]")
STANDOFF_AF = MEASURE(5.5, "brass standoff across flats", "calipers [TM Harwin 5.0 or 5.5]")

FPGA_BX = MEASURE(57.5, "FPGA centre from W edge", "mean of body-edge distances [BM ±4]")
FPGA_BY = MEASURE(86.0, "FPGA centre from N edge", "mean of body-edge distances [BM ±4]")
PKG_BODY = 20.0        # [BM][TM] EQFP-144 D1/E1 datasheet
PKG_LEADS = 22.0       # [BM][TM] D/E datasheet
PKG_A_MAX = 1.65       # [TM] A max (worst case for every height above it)
PKG_A_MIN = 1.45
LEAD_TOP_H = 1.0       # [TM] leads leave mid-body, ~0.5-0.8 below the top: modelled top PCB+1.0

PITCH = MEASURE(2.54, "header pitch", "calipers over 10 pins [CP: not stated in vendor docs]")
HDR_PLASTIC_H = MEASURE(2.5, "header plastic height", "calipers")
HDR_PIN_H = MEASURE(8.5, "header pin top above PCB", "calipers [BM unknown; 3M mating 5.97 + 2.5]")
DUPONT_TOP_H = MEASURE(16.5, "Dupont housing top above PCB", "plastic + 14 mm housing, measure with a lead on")
P1_BX = MEASURE(35.5, "P1 centreline from W edge", "[BM 57.5-22 vs 34: pick by measuring]")
P1_BY_N = MEASURE(63.0, "P1 N end of body", "[BM Y 63-111]")
P1_ROWS = 19           # [BM][CP] 2 x 19
P2_BX = MEASURE(81.5, "P2 centreline from W edge", "[BM ±2.5]")
P2_BY_N = MEASURE(56.0, "P2 N end of body", "[BM Y 56-112]")
P2_ROWS = 22
P3_BY = MEASURE(59.5, "P3 centreline from N edge", "[BM ±2.5]")
P3_BX_W = MEASURE(46.0, "P3 W end of body", "[BM X 46-71]")
P3_COLS = 10
P1_PIN1_END = MEASURE("N", "end of P1 that carries pins 1/2", "silkscreen / square pad [CP §6 item 1]")
P1_EVEN_COL = MEASURE("E", "column (E/W) of P1's even pins", "square pad + continuity [CP]")

JTAG_BX = MEASURE(66.0, "JTAG box header centre bx", "[BM ±5]")
JTAG_BY = MEASURE(128.0, "JTAG box header centre by", "[BM ±3]")
AS_BX = MEASURE(40.0, "AS box header centre bx", "[BM ±5]")
BOXHDR_L = MEASURE(20.0, "2x5 box header length", "[BM DC3-10P listing]")
BOXHDR_W = MEASURE(9.0, "2x5 box header width", "[BM listing]")
BOXHDR_H = MEASURE(9.3, "2x5 box header height above PCB", "[BM 3M 30310 listing]")
IDC_PLUG = MEASURE((17.0, 7.0, 8.5), "IDC plug L x W x height above box top", "with the Blaster cable seated")
RIBBON_W = 12.7        # 10-way 1.27 mm ribbon
USBB_BY = MEASURE(104.5, "board USB-B centre by", "[BM 99-110, ±6]")
USBB_SHELL = (12.04, 10.62, 16.5)   # [BM] Wurth 61400416121 datasheet (part unidentified)
USBB_OVERHANG = MEASURE(0.0, "USB-B mouth past the W edge", "calipers")
DCJ_BX = MEASURE((9.0, 19.0), "board DC jack bx range", "[BM verifier: 9-19]")
DCJ_BY = MEASURE((117.0, 136.0), "board DC jack by range (mouth at S edge)", "[BM: faces S, unverified]")
DCJ_H = MEASURE(11.0, "board DC jack height", "calipers [BM unknown]")
SW_BX = MEASURE((1.0, 9.0), "power switch bx range", "[BM]")
SW_BY = MEASURE((113.0, 123.0), "power switch by range", "[BM]")
SW_BODY_H = MEASURE(9.0, "power switch body height", "calipers")
SW_CAP_UP_H = MEASURE(25.0, "switch cap top above PCB, cap UP (DC)", "[BM 14-25, worst case used]")
SEG7 = MEASURE((5.0, 20.0, 19.0, 50.0, 7.2), "7-seg bx0,bx1,by0,by1,h", "[BM photo]")
SEG7_DIGITS_READ_FROM = MEASURE("S", "edge the 7-seg digits read upright from", "look at it [D #32]")
KEYS_BX = MEASURE(98.0, "key column bx", "[BM]")
KEYS_BY = MEASURE((22.5, 31.5, 40.0, 48.5), "keys S4..S1 by", "[BM verifier]")
RESET_KEY = MEASURE((90.0, 128.0), "RESET key centre", "[BM]")
DIP = MEASURE((72.0, 41.0, 10.0, 6.0), "DIP switch centre + size", "[BM]")
BUZZER = MEASURE((40.0, 41.0, 12.0, 9.5), "buzzer centre, dia, h", "[BM]")
POT = MEASURE((5.0, 13.0, 13.0, 19.0), "contrast pot bx0,bx1,by0,by1", "[BM]")
LCD_SOCKET = MEASURE((1.0, 5.0, 33.0, 84.0, 8.5), "LCD socket bx0,bx1,by0,by1,h", "[BM]")
IR = MEASURE((100.0, 16.0), "IR receiver centre", "[BM verifier]")
LEDS = MEASURE((88.0, 97.0, 54.0, 62.0), "LED1-4 footprint", "[BM]")
DB9_BX = MEASURE((24.0, 56.0), "DB9 body bx", "[BM verifier]")
VGA_BX = MEASURE((57.0, 90.0), "VGA body bx", "[BM verifier]")
PS2_BX = MEASURE((9.0, 23.0), "PS/2 bx", "[BM 7-23; moved 2 E so it clears the NW screw head]")
PS2_DEPTH = MEASURE(12.8, "PS/2 body depth from N edge", "[BM unknown; must end before the pot at by 13]")
DSUB_FLANGE_H = 12.6   # [BM] shell-E flange listing
DSUB_OVERHANG = MEASURE(6.5, "D-sub shell past the N edge", "calipers [C: <= 7]")
PCB_BOTTOM_CLEAR = MEASURE(3.0, "longest bottom-side protrusion", "photo + calipers [BM unknown]")

# =============================================================== box layout  [C §2]
BOX_X = 200.0
BOX_Y = 186.0          # concept 184 + 2: S gap 32 for the internal USB-Blaster [D #21]
FLOOR_T = 3.0
WALL_T = 3.0
W_WALL_T = 6.0         # W wall frame: 1.2 lip + 3.3 groove + 1.5 lip
GROOVE_X = (1.2, 4.5)  # panel groove in the W wall frame
BOARD_X0 = 76.0        # [C §1] box = board + (76, 15)
BOARD_Y0 = 15.0
BAY_X1 = 63.0          # module bay X 6-63
TUB_H = 86.0           # lid underside; set by the spring adjuster backed out + 5 [D #14]
SILL_Z = 6.0           # W wall frame sill top
LID_BOSS = ((10.0, 7.0), (193.0, 7.0), (10.0, 179.0), (193.0, 179.0))  # Ø9 corner bosses

PCB_BOT = FLOOR_T + BOARD_STANDOFF
PCB_TOP = PCB_BOT + PCB_T
FX = BOARD_X0 + FPGA_BX          # FPGA centre, box frame
FY = BOARD_Y0 + FPGA_BY
PKG_TOP = PCB_TOP + PKG_A_MAX


def bxy(bx, by):
    """Board frame -> box frame."""
    return BOARD_X0 + bx, BOARD_Y0 + by


BOARD_HOLES = [bxy(HOLE_INSET + i * HOLE_PITCH_X, HOLE_INSET + j * HOLE_PITCH_Y)
               for j in (0, 1) for i in (0, 1)]

# =============================================================== lid and window
LID_SKIN = 3.0
ACRYLIC_T = MEASURE(3.0, "acrylic sheet thickness", "calipers [TM: cast sheet varies]")
REBATE = ACRYLIC_T + 0.3
LID_T = LID_SKIN + REBATE        # 6.3 (fixes the concept's 6.2 vs 6.3)
LID_LIP_H = 4.0
LID_LIP_T = 2.0
WIN = (78.0, 178.0, 22.0, 150.0)  # window opening X0, X1, Y0, Y1 (board, clamp, switch, 7-seg, LEDs)
ACRYLIC_MARGIN = 9.5              # acrylic past the opening; screw holes 5 in from its edge
ACRYLIC_HOLE_IN = 5.0
THUMB = MEASURE((10.0, 4.0, 12.0), "knurled M3 thumbscrew head dia, head h, length", "[D #13] buy, then measure")

# =============================================================== clamp stack  [D §3.1]
BAR_W = 20.0                      # [SU] Bunnings 20 x 3 mm aluminium flat bar
BAR_T = MEASURE(3.0, "flat bar thickness", "calipers [SU listing]")
BAR_END = 6.0                     # hole centre to bar end, W
BAR_END_E = 4.5                   # E end shorter so the skewed bar corner clears the E wall
PAD_T = 0.5                       # [TM] Arctic TP-3 0.5 mm, insulating
SPREADER = 18.0                   # [D #2] contact face <= 18 x 18
SPREADER_H = MEASURE(7.0, "spreader block height", "[D §9.2] stock decision; >= 6.4 keeps KSD 10 mm up")
TC_GROOVE = MEASURE((1.2, 1.0), "thermocouple groove width, depth", "[C §5.1] bead dia - 0.15, measure bead")
TOP_PLATE_N = 12.0                # top plate extends from FY-12 ...
TOP_PLATE_S = 34.0                # ... to FY+34 (KSD wing at the S end)
HS10 = dict(A=16.5, B=30.0, C=8.8, D=8.5, E=15.9, F=11.3, G=12.4, L=2.4, K=1.8, H=4.5)  # [TM] Arcol datasheet
HS10_SHIFT_S = 2.0                # HS10 sits 2 mm S of centre so its N tag joint clears P3 by 9 mm [D #3]
HS10_TAG_W = 4.0                  # tag modelled 4 x 0.8 (verify on the part [TM])
HS10_SLEEVE_D = 4.0               # heat-shrink over tag + joint
HS10_SLEEVE_PAST_TIP = 1.5
KSD = (20.5, 7.5, 3.7)            # [TM] XC KSD9700 body datasheet
KAPTON_T = 0.1
STRAP = (10.0, 1.6)               # FR4 strap width, thickness [D #4]
STRAP_SCREW_X = -7.5              # strap M2 screws, relative to FX
POST_XY = (7.25, 1.0)             # pressure-bar posts at (+7.25,-1) and (-7.25,+1) rel. FPGA (clear HS10 ears)
POST_D = MEASURE(5.0, "pressure-bar post dia (round M3 M-F Al spacer, stud cut to 2.5)", "calipers; round so it clears the HS10 body and ears")
POST_H = MEASURE(10.0, "pressure-bar post length", "HS10 C 8.8 + 1.2 clearance; standard length")
PBAR = (22.0, 20.0)               # pressure bar from 20 x 3 bar, 22 long
BALL_D = MEASURE(6.35, "steel ball dia (1/4 in)", "calipers")
CONE_D = 5.0                      # 90 deg countersink top dia in the pressure bar (2.5 deep)
WASHER = (9.0, 1.0)               # M4 washer OD x t under each spring end
SPRING_L0 = MEASURE(12.0, "spring free length", "calipers [D #6]")
SPRING_K = MEASURE(1.5, "spring rate N/mm", "kitchen scale, 3 points [D #6: ~1-2 N/mm]")
SPRING_OD = MEASURE(7.0, "spring outside dia", "calipers")
SPRING_F = 8.0                    # [D #6] target 8 N (5-10)
ADJ_LEN = MEASURE(16.0, "M6 set-screw adjuster length", "sets the hard force limit: screw top leaves the jam nut at ~11.6 N (checks.py)")
JAM_NUT = (10.0, 3.2)             # M6 thin nut AF x h
LEG_LEN = MEASURE(60.0, "leg standoff stack (keel top to bridge)", "30 + 30 brass M3 F-F / M-F")
LEG_AF = MEASURE(5.5, "leg standoff across flats", "calipers [TM 5.5 A/F]")
LEG_PAIR = 5.0                    # two legs per joint at +-5 across the bar = 2 locating pins [D #7]
LEG_W_X = 68.0                    # [C §5.3] W leg pair centre, box X (in the W gap; 0.8 mm off the USB-B blank)
LEG_E_X = 188.5                   # E leg pair centre, box X (skewed bar corner 0.4 off the E wall)
FAN_LEG_CLEAR = 1.0               # W legs >= 1 mm outside the fan frame in plan [D #24]
KEEL_SCREW_IN = 15.0              # keel floor screws 15 mm inboard of each leg pair [D #12]
KEEL_SLOT = 20.0                  # floor slots: clamp line slides +-10 in Y [C §5.3]
POST_SITES = ((0, 0), (6, 0), (-6, 0), (0, 6), (0, -6))   # [D #8] back-support sites rel. FPGA
BACKPOST_SO = MEASURE(6.0, "back-post brass M-F standoff length", "stud in tapped keel")
BACKPOST_SCREW = MEASURE((8.0, 5.5, 2.1), "nylon M3 pan screw length, head d, head h", "[D #8]")

# =============================================================== airflow  [C §7] [D §3.5]
FAN = 40.0                        # [TM] Sunon 4010 datasheet
FAN_T = 10.0
FAN_HOLE_PITCH = 32.0
FAN_HOLE_D = MEASURE(4.3, "fan hole dia", "[TM Sunon 4.3; others differ]")
FAN_YC = FY                       # jet aimed at the FPGA
FAN_ZC = PCB_TOP + FAN / 2        # bottom edge level with the PCB top [C §7]
DUCT_L = 20.0                     # intake duct holding the BME280 upstream of the fan [D #25]
DUCT_WALL = 1.5
GRILLE_D = 38.0
EXHAUST = dict(n=13, w=3.0, pitch=6.0, z0=24.0, z1=60.0)   # [D #26] span = 12*6+3 = 75

# =============================================================== modules in the bay  [ME]
PLATE_Z0 = 8.0                    # plate on floor bosses (insert 6.7 deep) [D #16]
PLATE_T = 3.0
PLATE_X = (6.5, 62.5)
PLATE_Y = (4.0, 181.0)
PLATE_BOSSES = ((30.0, 37.0), (30.0, 73.0), (15.0, 121.5), (40.0, 177.5))
PICO = (51.0, 21.0, 1.0)          # [ME] datasheet
PICO_USB_OVERHANG = 1.3
PICO_SO = MEASURE(9.0, "Pico standoff height (header tails below)", "Pico 2H pins: measure")
PICO_Y0 = 13.0
LA = MEASURE((54.7, 27.4, 14.1), "logic analyser case L x W x H", "[SU] Core TOL-18627 listing")
LA_USB_Z = MEASURE(7.0, "LA USB centre above its base", "calipers [D #22: connector may be Mini-B]")
LA_Y0 = 40.0
MAX31855 = (20.32, 22.86)         # [ME] Adafruit 269 Eagle
MAX_TERM_H = MEASURE(8.5, "MAX31855 terminal block height above PCB", "[ME unknown]")
SI5351 = (30.48, 21.59)           # [ME] Adafruit 2045 Eagle
SI5351_H = MEASURE(3.0, "Si5351 tallest part above PCB (wires soldered, no header)", "keep < jet")
INA226 = MEASURE((27.0, 20.0, 4.0), "INA226 CJMCU-226 L x W x H", "[ME listing 20 x 27]")
D4184 = MEASURE((35.0, 16.0, 14.0), "D4184 module L x W x H", "[ME listing]")
AO3400 = MEASURE((25.0, 15.0, 5.0), "AO3400 fan-switch module L x W x H", "[ME unknown]")
LOADSW = MEASURE((20.0, 15.0, 5.0), "5 V load-switch module L x W x H", "[D §9.5 default: include]")
STAR = MEASURE((20.0, 19.0, 9.0), "star-ground lever connector L x W x H", "[C §8]")
BME = MEASURE((25.4, 17.78, 1.57, 4.5), "BME280 board L x W x PCB t x overall t", "[ME] Adafruit 2652; GY clone 15.5 x 11.5")
BME_HOLES = MEASURE(((2.54, 15.24), (22.86, 15.24)), "BME280 mounting holes (board coords)", "[ME 2652]")

# =============================================================== W panel connectors  [D §3.4]
PANEL_T = 3.0
PANEL_Z0 = 3.2
USBC_CUT = MEASURE((9.4, 3.8), "USB-C panel socket cut-out", "[D #18] buy, then measure")
USBC_SCREWS = MEASURE(8.0, "USB-C socket flange screw offset +-", "calipers")
USBC_BODY = MEASURE((14.0, 7.0, 18.0), "USB-C socket body behind panel", "calipers")
FUSE_HOLE = MEASURE(12.5, "panel fuse-holder hole", "[TM Jaycar SZ2030 class]")
FUSE_BODY = MEASURE((15.5, 30.0), "fuse holder body dia, depth behind panel", "[D #20] ~40 max")
JACK12_HOLE = MEASURE(8.0, "12 V panel jack hole", "[SU] Altronics P0622 8 mm")
JACK12_BODY = MEASURE((10.0, 15.0), "12 V jack body dia, depth", "calipers")
PICO_USB_CUT = MEASURE((12.0, 9.0), "Pico micro-B plug overmould cut-out", "measure the cable [C §9]")
LA_USB_CUT = MEASURE((13.0, 8.0), "LA USB plug overmould cut-out", "measure the cable [D #22]")
PANEL_PORT_Z = 70.0               # power connectors high on the panel, above the modules

# =============================================================== JTAG / USB-Blaster  [D #21]
BLASTER = MEASURE((60.0, 26.0, 15.0), "USB-Blaster dongle L x W x H", "[D #21] measure before printing the tub")
BLASTER_RIBBON = MEASURE(150.0, "Blaster ribbon length", "[D #21]")
BLASTER_X0 = 104.0                # dongle on its side in the S gap, ribbon end W, USB end E
BLASTER_CABLE_D = MEASURE(4.0, "Blaster USB cable dia", "calipers")
BLASTER_PLUG_L = MEASURE(18.0, "Blaster-side USB plug overmould length", "calipers")
CABLE_Z = 12.0                    # Blaster USB cable height at the E wall
RA_DC_PLUG = MEASURE((25.0, 10.0), "right-angle DC plug length, body dia", "[C §9] <= 25")

# =============================================================== misc
FOOT = MEASURE((12.0, 5.0), "rubber foot dia, height", "[C §4] >= 5 clears screw heads")
VISITOR_FACE = MEASURE("S", "wall that carries the nameplate", "after the 7-seg check [D #32]")

# derived numbers used by more than one module ---------------------------------------
TOP_PLATE_Z0 = PKG_TOP + PAD_T + SPREADER_H
TOP_PLATE_Z1 = TOP_PLATE_Z0 + BAR_T
PBAR_Z0 = TOP_PLATE_Z1 + POST_H
PBAR_Z1 = PBAR_Z0 + BAR_T
BALL_ZC = PBAR_Z1 + (BALL_D / 2) / math.sin(math.radians(45)) - CONE_D / 2 + 0.01
WASHER1_Z0 = BALL_ZC + BALL_D / 2
SPRING_Z0 = WASHER1_Z0 + WASHER[1]
BRIDGE_Z0 = FLOOR_T + BAR_T + LEG_LEN     # keel on the floor, legs on the keel
BRIDGE_Z1 = BRIDGE_Z0 + BAR_T
