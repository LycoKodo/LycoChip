"""Shared terminal input handling for the LycoChip TUIs.

Two non-obvious details are baked in here so they are fixed in one place:

* cbreak, not raw -- tty.setraw() disables OPOST, which makes "\\n" a bare
  line-feed that does not return the cursor to column 0. Frames then stagger
  and cursor-up arithmetic breaks.
* os.read on the raw fd, not sys.stdin.read -- an arrow key arrives as three
  bytes and Python's buffered reader swallows the tail, leaving select() to
  report an empty fd on the follow-up poll.
"""
import os, select, sys, termios, tty

from theme import RESET

KEYMAP = {"j": "down", "k": "up", "h": "left", "l": "right",
          "\r": "go", "\n": "go", " ": "go",
          "q": "quit", "\x03": "quit"}
ARROWS = {b"A": "up", b"B": "down", b"C": "right", b"D": "left"}


class Raw:
    """cbreak mode with the cursor hidden, restored on exit."""

    def __enter__(self):
        self.fd = sys.stdin.fileno()
        self.old = termios.tcgetattr(self.fd)
        tty.setcbreak(self.fd)
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()
        return self

    def __exit__(self, *a):
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)
        sys.stdout.write("\033[?25h" + RESET)
        sys.stdout.flush()


def getkey(timeout=0.15):
    fd = sys.stdin.fileno()
    r, _, _ = select.select([fd], [], [], timeout)
    if not r:
        return None
    try:
        data = os.read(fd, 32)
    except OSError:
        return None
    if not data:
        return None
    if data[:2] == b"\x1b[":
        return ARROWS.get(data[2:3])
    if data == b"\x1b":
        return "quit"
    return KEYMAP.get(data[:1].decode("utf-8", "ignore"))


def paint(lines, prev):
    """Repaint a frame in place. Returns the new 'prev' line count."""
    out = (f"\033[{prev}A" if prev else "")
    for ln in lines:
        out += "\r\033[2K" + ln + "\r\n"
    for _ in range(max(0, prev - len(lines))):
        out += "\r\033[2K\r\n"
    sys.stdout.write(out)
    sys.stdout.flush()
    return max(prev, len(lines))
