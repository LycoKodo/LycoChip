"""Draw a digit, send it to the FPGA, and check the answer against the golden model.

    python projects/demo/host/draw.py            the app
    python projects/demo/host/draw.py --fake     adds a fake board (pty) to the port list
    python projects/demo/host/draw.py --smoke    build the window, draw a synthetic 7, recognise
                                                 it (simulated, or the fake board with --fake),
                                                 close after ~1 s; fails unless the answer is 7
                                                 (and, on a board, the scores match golden)

Port "Simulate (no board)" runs golden.Model on the Mac. "JTAG (USB-Blaster)"
sends the frame through the programming cable (jtag_bridge.py); any other port
sends it over RS-232 (fpga_link.py). Either way the board's 10 scores are
compared with golden.Model's, bit for bit.

The drawing is kept in a PIL image alongside the canvas (the canvas is never
screenshotted) and preprocessed the way MNIST was made: crop to the ink,
scale the longer side to 20 px (antialiased), and place it in 28 x 28 so its
centre of mass is at (14, 14).
"""
import argparse
import os
import queue
import sys
import threading
import time

import numpy as np
from PIL import Image, ImageDraw, ImageTk

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from golden import Model  # noqa: E402

SIZE = 280          # drawing canvas, px
BRUSH = 18          # brush diameter, px
SIMULATE = "Simulate (no board)"
PREVIEW_SCALE = 5   # 28 x 28 shown at 140 x 140


# --------------------------------------------------------------------------
# Preprocessing (importable without opening a window)
# --------------------------------------------------------------------------
def preprocess(img, resample=Image.BOX):
    """PIL 'L' image, ink high (any size) -> 784 ints 0..255, row-major, or
    None if there is no ink. MNIST's recipe: crop to the ink bounding box,
    scale so the longer side is 20 px keeping the aspect ratio (antialiased:
    box filter, i.e. area averaging),
    then paste into 28 x 28 with the centre of mass at pixel (14, 14)."""
    bbox = img.getbbox()
    if bbox is None:
        return None
    crop = img.crop(bbox)
    w, h = crop.size
    s = 20.0 / max(w, h)
    nw, nh = max(1, int(round(w * s))), max(1, int(round(h * s)))
    small = np.asarray(crop.resize((nw, nh), resample), dtype=np.float64)
    mass = small.sum()
    if mass <= 0:
        return None
    ys, xs = np.indices(small.shape)
    cy, cx = (ys * small).sum() / mass, (xs * small).sum() / mass
    oy, ox = int(np.floor(14 - cy + 0.5)), int(np.floor(14 - cx + 0.5))
    out = np.zeros((28, 28))
    y0, x0, y1, x1 = max(oy, 0), max(ox, 0), min(oy + nh, 28), min(ox + nw, 28)
    out[y0:y1, x0:x1] = small[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    return [int(v) for v in np.clip(np.rint(out), 0, 255).astype(int).ravel()]


# --------------------------------------------------------------------------
# The app
# --------------------------------------------------------------------------
class App:
    BG, PANEL, FG, DIM = "#1e1f24", "#2a2c33", "#e8e8ea", "#9a9ca3"
    GREEN, RED, ACCENT, BAR = "#3fb950", "#f85149", "#58a6ff", "#5d6170"

    def __init__(self, root, fake=None):
        import tkinter as tk
        from tkinter import ttk
        self.tk, self.root = tk, root
        self.model = Model()
        self.fake = fake
        self.link = None
        self.results = queue.Queue()
        self.pending = False
        self.errors = []
        self.last_result = None

        root.title("LycoChip demo: draw a digit")
        root.configure(bg=self.BG)
        root.resizable(False, False)
        font = ("Helvetica", 13)

        left = tk.Frame(root, bg=self.BG)
        left.grid(row=0, column=0, padx=16, pady=16, sticky="n")
        right = tk.Frame(root, bg=self.BG)
        right.grid(row=0, column=1, padx=(0, 16), pady=16, sticky="n")

        # Drawing canvas, with the PIL image kept in step with it.
        self.canvas = tk.Canvas(left, width=SIZE, height=SIZE, bg="black",
                                highlightthickness=1, highlightbackground="#555", cursor="crosshair")
        self.canvas.pack()
        self.image = Image.new("L", (SIZE, SIZE), 0)
        self.draw = ImageDraw.Draw(self.image)
        self.last = None
        self.canvas.bind("<ButtonPress-1>", lambda e: self.pen_down(e.x, e.y))
        self.canvas.bind("<B1-Motion>", lambda e: self.pen_move(e.x, e.y))
        self.canvas.bind("<ButtonRelease-1>", lambda e: self.pen_up())

        buttons = tk.Frame(left, bg=self.BG)
        buttons.pack(fill="x", pady=(10, 0))
        tk.Button(buttons, text="Clear", command=self.clear, font=font, width=10,
                  highlightbackground=self.BG).pack(side="left")
        tk.Button(buttons, text="Recognise", command=self.recognise, font=font, width=12,
                  highlightbackground=self.BG).pack(side="right")
        tk.Label(left, text="Enter / space: recognise   Esc / Backspace: clear",
                 bg=self.BG, fg=self.DIM, font=("Helvetica", 11)).pack(pady=(6, 0))
        root.bind("<Return>", lambda e: self.recognise())
        root.bind("<space>", lambda e: self.recognise())
        root.bind("<Escape>", lambda e: self.clear())
        root.bind("<BackSpace>", lambda e: self.clear())

        # Port selector.
        row = tk.Frame(right, bg=self.BG)
        row.pack(fill="x")
        tk.Label(row, text="Port", bg=self.BG, fg=self.DIM, font=font).pack(side="left")
        self.port_var = tk.StringVar(value=SIMULATE)
        self.port_box = ttk.Combobox(row, textvariable=self.port_var, state="readonly", width=30,
                                     postcommand=self.refresh_ports)
        self.port_box.pack(side="left", padx=(8, 0))
        self.refresh_ports()
        from jtag_bridge import JTAG
        if JTAG in self.port_box["values"]:
            self.port_var.set(JTAG)
        if fake is not None:
            self.port_var.set(fake.port)

        # Preview of exactly what is sent, and the answer.
        mid = tk.Frame(right, bg=self.BG)
        mid.pack(fill="x", pady=(14, 0))
        pv = tk.Frame(mid, bg=self.BG)
        pv.pack(side="left")
        tk.Label(pv, text="Sent (28 x 28)", bg=self.BG, fg=self.DIM, font=("Helvetica", 11)).pack(anchor="w")
        self.preview = tk.Label(pv, bg="black", bd=0)
        self.preview.pack()
        self.show_preview(None)
        ans = tk.Frame(mid, bg=self.BG)
        ans.pack(side="left", padx=(24, 0), fill="y")
        tk.Label(ans, text="Digit", bg=self.BG, fg=self.DIM, font=("Helvetica", 11)).pack(anchor="w")
        self.digit_label = tk.Label(ans, text="-", bg=self.BG, fg=self.FG,
                                    font=("Helvetica", 96, "bold"), width=2)
        self.digit_label.pack()

        tk.Label(right, text="Scores", bg=self.BG, fg=self.DIM,
                 font=("Helvetica", 11)).pack(anchor="w", pady=(10, 0))
        self.chart = tk.Canvas(right, width=330, height=10 * 20 + 6, bg=self.PANEL, highlightthickness=0)
        self.chart.pack()
        self.draw_chart(None, None)

        # Status line.
        status = tk.Frame(root, bg=self.BG)
        status.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 14))
        self.status = tk.Label(status, text="Draw a digit, then press Recognise.", bg=self.BG,
                               fg=self.FG, font=font, anchor="w", justify="left", wraplength=560)
        self.status.pack(side="left", fill="x", expand=True)
        self.timing = tk.Label(status, text="", bg=self.BG, fg=self.DIM, font=font)
        self.timing.pack(side="right")

        root.report_callback_exception = self.on_error
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.after(30, self.poll_results)

    # --- drawing -----------------------------------------------------------
    def _dot(self, x, y):
        r = BRUSH / 2
        self.canvas.create_oval(x - r, y - r, x + r, y + r, fill="white", outline="white")
        self.draw.ellipse([x - r, y - r, x + r, y + r], fill=255)

    def pen_down(self, x, y):
        self.last = (x, y)
        self._dot(x, y)

    def pen_move(self, x, y):
        if self.last is None:
            return self.pen_down(x, y)
        x0, y0 = self.last
        self.canvas.create_line(x0, y0, x, y, fill="white", width=BRUSH,
                                capstyle=self.tk.ROUND, joinstyle=self.tk.ROUND, smooth=True)
        self.draw.line([x0, y0, x, y], fill=255, width=BRUSH)
        self._dot(x, y)  # round joints in the PIL copy too
        self.last = (x, y)

    def pen_up(self):
        self.last = None

    def clear(self):
        self.canvas.delete("all")
        self.draw.rectangle([0, 0, SIZE, SIZE], fill=0)
        self.show_preview(None)
        self.digit_label.config(text="-", fg=self.FG)
        self.draw_chart(None, None)
        self.set_status("Draw a digit, then press Recognise.", self.FG)
        self.timing.config(text="")

    # --- ports -------------------------------------------------------------
    def refresh_ports(self):
        from fpga_link import list_ports
        ports = list_ports()
        if self.fake is not None:
            ports = [self.fake.port] + ports
        self.port_box["values"] = [SIMULATE] + ports

    def get_link(self, port):
        from fpga_link import open_link
        if self.link is not None and self.link.port != port:
            self.link.close()
            self.link = None
        if self.link is None:
            self.link = open_link(port)
        return self.link

    # --- recognition -------------------------------------------------------
    def recognise(self):
        if self.pending:
            return
        pixels = preprocess(self.image)
        if pixels is None:
            self.set_status("Nothing drawn yet.", self.DIM)
            return
        self.show_preview(pixels)
        port = self.port_var.get()
        if port == SIMULATE:
            t0 = time.perf_counter()
            _, scores, digit = self.model.forward(pixels)
            ms = (time.perf_counter() - t0) * 1000
            self.show_result(digit, scores)
            self.set_status("Simulated: golden model on the Mac, no board.", self.DIM)
            self.timing.config(text=f"{ms:.1f} ms")
            self.last_result = ("sim", digit, scores, True)
            return
        self.pending = True
        self.set_status(f"Sending to {port} ...", self.DIM)

        def work():
            try:
                link = self.get_link(port)
                res = link.infer(pixels)
                self.results.put(("ok", pixels, res))
            except Exception as e:  # shown in the status line, not lost
                self.results.put(("err", pixels, e))
        threading.Thread(target=work, daemon=True).start()

    def poll_results(self):
        try:
            while True:
                kind, pixels, res = self.results.get_nowait()
                self.pending = False
                if kind == "err":
                    if self.link is not None:
                        self.link.close()
                        self.link = None
                    self.set_status(f"Board error: {res}", self.RED)
                    self.timing.config(text="")
                    self.last_result = ("err", None, None, False)
                    continue
                digit, scores, ms = res
                _, g_scores, g_digit = self.model.forward(pixels)
                self.show_result(digit, scores)
                diffs = [f"score[{k}] FPGA {s} vs golden {g}"
                         for k, (s, g) in enumerate(zip(scores, g_scores)) if s != g]
                if digit != g_digit:
                    diffs.insert(0, f"digit FPGA {digit} vs golden {g_digit}")
                if diffs:
                    self.set_status("Mismatch with the golden model: " + "; ".join(diffs), self.RED)
                else:
                    self.set_status("FPGA scores match the golden model bit for bit", self.GREEN)
                self.timing.config(text=f"round trip {ms:.1f} ms")
                self.last_result = ("board", digit, scores, not diffs)
        except queue.Empty:
            pass
        self.root.after(30, self.poll_results)

    # --- display -----------------------------------------------------------
    def set_status(self, text, colour):
        self.status.config(text=text, fg=colour)

    def show_preview(self, pixels):
        arr = np.zeros((28, 28), np.uint8) if pixels is None else np.array(pixels, np.uint8).reshape(28, 28)
        img = Image.fromarray(arr, "L").resize((28 * PREVIEW_SCALE, 28 * PREVIEW_SCALE), Image.NEAREST)
        self._preview_img = ImageTk.PhotoImage(img)  # keep a reference
        self.preview.config(image=self._preview_img)

    def show_result(self, digit, scores):
        self.digit_label.config(text=str(digit), fg=self.ACCENT)
        self.draw_chart(scores, digit)

    def draw_chart(self, scores, best):
        c = self.chart
        c.delete("all")
        W, row = int(c["width"]), 20
        lab, val = 22, 52                      # digit label column, value column
        x_lo, x_hi = lab + 4, W - val
        if scores is None:
            for k in range(10):
                c.create_text(lab / 2 + 2, 3 + k * row + row / 2, text=str(k), fill=self.DIM,
                              font=("Helvetica", 12))
            return
        lo, hi = min(min(scores), 0), max(max(scores), 0)
        span = max(hi - lo, 1)
        x0 = x_lo + (x_hi - x_lo) * (-lo) / span   # zero axis
        for k, s in enumerate(scores):
            y = 3 + k * row
            x1 = x_lo + (x_hi - x_lo) * (s - lo) / span
            colour = self.ACCENT if k == best else self.BAR
            c.create_rectangle(min(x0, x1), y + 3, max(x0, x1), y + row - 3, fill=colour, outline="")
            c.create_text(lab / 2 + 2, y + row / 2, text=str(k),
                          fill=self.FG if k == best else self.DIM, font=("Helvetica", 12, "bold" if k == best else "normal"))
            c.create_text(W - 4, y + row / 2, text=str(s), anchor="e",
                          fill=self.FG if k == best else self.DIM, font=("Menlo", 11))
        c.create_line(x0, 2, x0, 3 + 10 * row, fill=self.DIM)

    # --- lifecycle ---------------------------------------------------------
    def on_error(self, exc, val, tb):
        import traceback
        traceback.print_exception(exc, val, tb)
        self.errors.append(val)

    def close(self):
        if self.link is not None:
            self.link.close()
        self.root.destroy()


SMOKE_DIGIT = 7


def synthetic_seven(app):
    """Draw a 7 (SMOKE_DIGIT) through the same pen handlers a mouse uses."""
    pts = [(80, 70), (130, 66), (205, 64), (180, 120), (155, 175), (135, 230)]
    app.pen_down(*pts[0])
    for p in pts[1:]:
        app.pen_move(*p)
    app.pen_up()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--fake", action="store_true", help="add a fake board (fake_fpga.py pty) to the ports")
    ap.add_argument("--smoke", action="store_true",
                    help="draw a synthetic 7, recognise it, close after ~1 s; fail unless the answer is 7")
    args = ap.parse_args()

    import tkinter as tk
    fake = None
    if args.fake:
        from fake_fpga import FakeFpga
        fake = FakeFpga().start()
    root = tk.Tk()
    app = App(root, fake=fake)

    if args.smoke:
        if not args.fake:
            app.port_var.set(SIMULATE)

        def go():
            synthetic_seven(app)
            app.recognise()
            root.after(1000, finish)

        def finish():
            r = app.last_result
            if r is None:
                app.errors.append("no result within 1 s")
            else:
                mode, digit, scores, ok = r
                print(f"smoke: mode={mode} digit={digit} scores={scores} match={ok}")
                print(f"smoke: status line: {app.status.cget('text')!r}  {app.timing.cget('text')}")
                if not ok:
                    app.errors.append("board scores differ from the golden model")
                # The drawing is a 7. Checking the digit is what makes this test
                # able to fail on a broken preprocess: in Simulate mode `ok` is
                # always True, and with --fake the board is golden.Model too, so
                # a wrong 28 x 28 image changes both sides the same way.
                if digit != SMOKE_DIGIT:
                    app.errors.append(f"recognised {digit}, drew {SMOKE_DIGIT}")
            app.close()
        root.after(200, go)

    root.mainloop()
    if fake is not None:
        fake.stop()
    if args.smoke:
        for e in app.errors:
            print(f"smoke: error: {e}")
        print("smoke: FAIL" if app.errors else "smoke: OK")
        return 1 if app.errors else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
