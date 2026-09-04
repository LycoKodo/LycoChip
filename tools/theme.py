"""Shared cyberpunk palette and drawing primitives for the LycoChip TUIs.

Colours only -- nothing paints a background, so terminal transparency shows
through.
"""

def fg(c): return f"\033[38;2;{c[0]};{c[1]};{c[2]}m"
RESET, BOLD, DIM = "\033[0m", "\033[1m", "\033[2m"

CYAN   = (56, 189, 248)
ICE    = (165, 243, 252)
PINK   = (244, 114, 182)
VIOLET = (167, 139, 250)
DEEP   = (30,  58,  95)      # midnight blue -- unfilled track
MUTED  = (100, 130, 180)
PAPER  = (219, 234, 254)
AMBER  = (251, 191,  36)
ROSE   = (251, 113, 133)
GREEN  = (52,  211, 153)

BLOCKS = " ▁▂▃▄▅▆▇█"


def lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(x + (y - x) * t) for x, y in zip(a, b))


def heat(pct):
    """cyan -> violet -> pink -> rose as a value climbs"""
    if pct < 40: return lerp(CYAN, VIOLET, pct / 40)
    if pct < 75: return lerp(VIOLET, PINK, (pct - 40) / 35)
    return lerp(PINK, ROSE, (pct - 75) / 25)


def bar(pct, width, colour=None):
    pct  = max(0.0, min(100.0, pct))
    fill = int(width * pct / 100)
    if pct > 0 and fill == 0: fill = 1   # never render a live value as empty
    col  = colour or heat(pct)
    return fg(col) + "█" * fill + fg(DEEP) + "─" * (width - fill) + RESET


def graph(hist, width, rows=3):
    vals = list(hist)[-width:]
    vals = [0.0] * (width - len(vals)) + vals
    out = []
    for r in range(rows - 1, -1, -1):
        line = ""
        for v in vals:
            cell = (v / 100.0 * rows * 8) - r * 8
            idx = 0 if cell <= 0 else (8 if cell >= 8 else int(cell))
            line += (fg(DEEP) + "·") if idx == 0 else (fg(heat(v)) + BLOCKS[idx])
        out.append(line + RESET)
    return out


def rule(label, inner, lead="  "):
    return f"{lead}{fg(VIOLET)}▚{RESET} {fg(ICE)}{label}{RESET} {fg(DEEP)}{'┈' * max(0, inner - len(label) - 3)}{RESET}"
