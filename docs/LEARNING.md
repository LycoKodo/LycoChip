# Learning log

Spaced-repetition cards, governed by **Article III** of `CLAUDE.md`.
Maintained by whichever Claude session is working: Claude Code in the repo, or Cowork
when linked to this Mac (see `docs/HANDSHAKE.md`, amendment 2026-09-23). Read it fresh
before writing; never rewrite another session's history lines. Alex does not need to
touch it.

**Session count: 3**  ← increment at the start of each working session

**Paths:** since 2026-10-20 the exercise projects these cards cite (`full_adder`,
`keytest`, `clock_counter`, `blink`, `button_counter`) live in `archive/exercises/`,
not `projects/`. The files themselves are unchanged.

Boxes: 1 = new/wrong (next session) · 2 = +2 · 3 = +4 · 4 = +8 · 5 = retired.
A wrong answer, or the confusion resurfacing in code, sends a card straight back to box 1.

**Quiz order** (at most two per session, per Article III): `logical-vs-bitwise` and
`pin-assignment-shape` first, since both are in code he touched on 2026-09-22. Then
`latch-inference` + `blocking-vs-nonblocking` (same file, same bug). Then the rest.

---

## Due now

### `logical-vs-bitwise` — `&&` vs `&`
- **Box:** 1 · **Due:** next session
- **Raised:** 2026-09-05 — `full_adder.v` uses `&&` and `!` where `&` and `~` are meant.
  Correct for 1-bit operands, so the design works. Question posed, not yet answered.
- **Ask:** If `a` and `b` were 4-bit buses holding `4'b0101` and `4'b1010`, what does
  `a && b` give, and what does `a & b` give? Why did using `&&` not break your adder?
- **Passing answer contains:**
  - `&&`, `||`, `!` are **logical**: they reduce each operand to a single true/false.
    `4'b0101 && 4'b1010` → `1'b1` (both are nonzero).
  - `&`, `|`, `~` are **bitwise**: they act per bit. `4'b0101 & 4'b1010` → `4'b0000`.
  - for 1-bit operands the two are indistinguishable, which is exactly why the adder
    works and why the habit is dangerous — it breaks silently the first time the
    signals widen.
- **History:**
  - 2026-09-05 — raised, question asked, awaiting answer.
  - 2026-09-22 — resurfaced in `keytest.v`: `assign led = key[0] && key[1];`. Still
    correct at 1 bit, still the habit. Stays box 1.

### `pin-assignment-shape` — `.qsf` lines the tool silently ignores
- **Box:** 1 · **Due:** next session
- **Raised:** 2026-09-08 — `clock_counter.qsf` assigns `key[0]` while the port is scalar
  `key`: `Warning (12069)` ×5, then `Critical Warning (169085)` — the fitter chose the
  reset pin itself. Resurfaced twice on 2026-09-22 in `keytest`: first the same shape
  mismatch (`led[0]` vs scalar `led`; `keytest.pin` recorded `User Assignment: N`); then,
  after he renamed the ports correctly, `led_n`'s `IO_STANDARD` line was **still**
  dropped. It is the last line of `keytest.qsf`, which has no trailing newline. The
  fitter's 3.3-V LVTTL list names only `key_n[0]` and `key_n[1]`, and
  `Warning (15714): Some pins have incomplete I/O assignments` is in
  `builds/20260922-112233-keytest-995b65b2/build.log`. The LED ran at the Cyclone IV E
  default, 2.5 V.
- **Ask:** Your `.qsf` line setting `led_n` to 3.3-V LVTTL looks correct, but the fitter
  never applied it. Where did it go, and what one line in the build log would have told
  you before you programmed the board? (Follow-up, other file: in `clock_counter`, which
  physical button is your reset right now, and how do you prove it from the build outputs
  rather than by pressing buttons?)
- **Passing answer contains:**
  - a `.qsf` assignment can be silently discarded for at least three reasons: the name
    doesn't match the port's declared shape (`led[0]` vs scalar `led`), a trailing
    `; # comment` on the line, or the line being last in a file with no trailing newline.
    None of them is an error.
  - the `.qsf` refers to pins by port name, so a mismatch discards the location *and* the
    I/O standard keyed to that name.
  - `User Assignment: N` in `<name>.pin` means the fitter chose the pin. The right LED
    lighting was luck, and a recompile is free to choose differently.
  - the evidence is in the tool's own output: `Critical Warning (169085)` for locations,
    `Warning (15714)` and the I/O-standard table for standards, the `User` column of the
    `.pin` file. Pressing buttons cannot show 2.5 V vs 3.3 V.
- **Links:** [[vector-declaration-syntax]], [[implicit-nets]]
- **History:**
  - 2026-09-08 — raised by Cowork from `clock_counter`'s build log; asked, unanswered.
  - 2026-09-22 — carded by Claude Code from `keytest` (shape mismatch). Same day, the
    symptom survived the fix for a new cause (no trailing newline). Stays box 1.
  - 2026-10-20 — asked by Claude Code (first question, the `led_n` one), at the start
    of `projects/mnist/`, whose `.qsf` he is about to write. Awaiting answer.

### `latch-inference` — why `led` got a latch and `data` didn't
- **Box:** 1 · **Due:** next session
- **Raised:** 2026-09-08 — `clock_counter` build: `Warning (13310)` ×4, `Register
  "led[0]~reg0" is converted into an equivalent circuit using register ... and latch ...`
  (line 42). Four latches inferred. He has not seen the warning.
- **Ask:** In `clock_counter`, `data` and `led` are both assigned in the reset branch, on
  the same edge. Quartus built `data` as plain flip-flops but needed a latch for `led`.
  What is different about what each one is reset *to*?
- **Passing answer contains:**
  - a flip-flop's asynchronous clear/preset can only force a **constant**.
  - `data <= 4'b0000` is a constant, so it maps straight onto the clear input.
  - `led <= ~data` in the async-reset branch asks the register to load a value that
    *depends on another signal*, asynchronously. No flip-flop has that input, so Quartus
    emulates it with a register plus a latch.
  - fix: reset `led` to a constant, or drive `led` combinationally from `data` instead of
    giving it its own register. The warning is the tool saying it built something he
    didn't ask for.
- **Links:** [[blocking-vs-nonblocking]], [[wire-vs-reg]]
- **History:**
  - 2026-09-08 — raised by Cowork from the build log; posed as a question, unanswered.

### `blocking-vs-nonblocking` — `<=` reads every right-hand side first
- **Box:** 1 · **Due:** next session
- **Raised:** 2026-09-08 — `clock_counter.v` has `data <= data + 1'b1;` and
  `led <= ~data;` in the same branch. Explained to him twice in an outside chat; the code
  on disk still has it in all three branches. This is Unit 1's core objective and has
  never been asked back.
- **Ask:** In `clock_counter`, `data` goes from 4 to 5 on this clock edge. What do the
  LEDs show after the edge, and why? Then: write a 3-stage shift register in your head
  with `=` instead of `<=`, lines in the natural top-to-bottom order. What does it
  actually become?
- **Passing answer contains:**
  - non-blocking assignments in one `always` block all read their right-hand sides
    **before** any left-hand side updates; the updates land together.
  - so `led <= ~data` reads the **old** `data`: the display is permanently one count
    behind.
  - that is why `<=` exists: it models flip-flops that all sample on the same edge. With
    `=` in top-to-bottom order, `b = a; c = b;` gives every stage `a` on the same edge,
    so the shift register collapses.
  - rule of thumb: `<=` in clocked blocks, `=` in combinational ones.
- **Links:** [[latch-inference]], [[wire-vs-reg]]
- **History:**
  - 2026-09-08 — raised. Answer given in the outside chat, not yet asked back.

### `unconstrained-timing` — negative slack with no `.sdc`
- **Box:** 1 · **Due:** next session
- **Raised:** 2026-09-08 — `clock_counter.sdc` is empty and `keytest` has none
  (`Critical Warning (332012)`). The `clock_counter` log says `Info (332142): No user
  constrained base clocks found in the design. Calling "derive_clocks -period 1.0"` and
  reports worst-case setup slack **−3.666 ns**.
- **Ask:** `clock_counter` "fails timing" by 3.666 ns. Against what clock period? Does
  it actually fail on your 50 MHz board, and what one line would make the number mean
  something?
- **Passing answer contains:**
  - with no `create_clock`, the Timing Analyzer assumes a **1 ns (1 GHz)** period, and
    says so in the log.
  - so the slowest path is about 4.7 ns. Against the real 20 ns period it has comfortable
    positive slack (`blink`, a similar design with a real constraint, reports +13.7 ns).
    The negative number was an artefact.
  - `create_clock -period 20 [get_ports clk]` in the `.sdc`. Every clock needs one, or
    slack and Fmax mean nothing and the fitter optimises for the wrong target.
- **History:**
  - 2026-09-08 — raised in Cowork's learning log; not yet asked.

### `sized-literals` — `25'b1` is 1, not all ones
- **Box:** 1 · **Due:** next session
- **Raised:** 2026-09-08 (outside chat) — set the divider threshold to `27'b1`, then
  "fixed" it to `25'b1`, believing the value changed. Self-corrected once shown:
  *"oh so 25'b1 isnt 11111.... its 000...1?"* Then used `25'h1FFFFFF` as the threshold;
  the header comment still claims 2 Hz.
- **Ask:** Your threshold is `25'h1FFFFFF`. How long is one count on the LEDs at 50 MHz?
  How would you write the threshold for exactly 0.5 s as a sized literal, and why does it
  need 25 bits?
- **Passing answer contains:**
  - `WIDTH'BASE VALUE`: the width is the container, the value is written normally in the
    named base, and a narrower value **zero-extends** on the left (`x`/`z` extend with
    `x`/`z`).
  - `25'b1` = 1. `25'h1FFFFFF` = 2²⁵ − 1 = 33,554,431, about 0.67 s per count, not 0.5 s.
  - 0.5 s is 25,000,000 cycles; counting 0 … N−1 means comparing against
    `25'd24_999_999`. 25 bits because 2²⁴ = 16,777,216 < 25,000,000 ≤ 2²⁵.
- **History:**
  - 2026-09-08 — partial: restated zero-extension in his own words once shown; not yet
    applied to a new case.

### `wire-vs-reg` — `reg` does not mean flip-flop
- **Box:** 1 · **Due:** next session
- **Raised:** 2026-09-05 — asked in `full_adder.v`: *"what is reg, and wire, and why is
  this not required in this case?"* The full answer was given to him in the 2026-09-08
  outside chat, so the definition question is burned. Ask application only.
- **Ask:** `blink.v` declares exactly two `reg`s, yet the fitter reports **29
  registers**. Where do the 29 come from? Then: `reg y; always @(*) y = a & b;` — how
  many flip-flops is that, and why?
- **Passing answer contains:**
  - the fitter counts flip-flops **per bit**: `cnt` is `$clog2(25_000_000)` = 25 bits,
    `value` is 4 bits, so 29.
  - `reg` is a variable assigned procedurally (inside `always`/`initial`), not a storage
    element. A `wire` is continuously driven (`assign`, or a module output).
  - what creates a flip-flop is the **clock edge** (`always @(posedge clk)`). The
    `always @(*)` block is combinational: zero flip-flops, one LUT.
- **History:**
  - 2026-09-05 — raised. 29-register question asked by Cowork the same day; unanswered.
  - 2026-09-08 — definition given in the outside chat (not graded).

### `vector-declaration-syntax` — the bracket before the name vs after it
- **Box:** 1 · **Due:** next session
- **Raised:** 2026-09-05 — asked in `full_adder.v`: *"why is verilog array syntax in
  reverse?"* Definition given in full in the 2026-09-08 outside chat. Ask application
  only.
- **Ask:** What would `reg [7:0] mem [0:1023];` cost on the EP4CE6, in memory bits and as
  a share of what the chip has? Which bracket made it a memory rather than a wider bus?
  And what would a clocked `reg [8191:0] big;` cost instead?
- **Passing answer contains:**
  - the bracket **before** the name is the width (packed, part of the type). The bracket
    **after** is an array of separate elements (unpacked), i.e. a memory.
  - 1,024 × 8 = 8,192 bits, about 3% of 276,480, and a candidate for a single M9K
    (1K × 8 is a native M9K shape).
  - `reg [8191:0]` clocked is 8,192 flip-flops, more than the chip's 6,272 registers.
    Same bits, very different hardware.
  - `[7:0]` vs `[0:7]` is bit ordering; MSB-first is convention.
- **History:**
  - 2026-09-05 — raised. 2026-09-08 — definition given in the outside chat (not graded).

### `implicit-nets` — why it compiled anyway
- **Box:** 1 · **Due:** next session
- **Raised:** 2026-09-05 — `full_adder.v` produced 8 × `Warning (10236): created
  implicit net` for `a b c_in alpha beta gamma S c_out`, unnoticed under "0 errors".
- **Ask:** Quartus created eight nets for you that you never declared, and the build
  still said 0 errors. What would happen if you had typed `gama` instead of `gamma` on
  one of those lines — and what would you see?
- **Passing answer contains:**
  - an undeclared identifier in a continuous assignment silently becomes an implicit
    **1-bit** wire.
  - a typo therefore creates a *new, undriven* net instead of an error — the design
    still compiles and the logic is silently wrong.
  - the implicit net is always 1 bit, so it also truncates if you meant a vector.
  - the fix is `` `default_nettype none `` at the top of the file, which turns all of
    that into a compile error.
- **Links:** [[wire-vs-reg]]
- **History:**
  - 2026-09-05 — raised, not yet quizzed.

### `layer-as-matmul` — what `Linear` and `ReLU` compute, and what the chip must do
- **Box:** 1 · **Due:** next session
- **Raised:** 2026-10-20 — asked how `nn.Sequential(nn.Flatten(), nn.Linear(784, 64),
  nn.ReLU(), nn.Linear(64, 10))` in `projects/mnist/model/train.ipynb` works. Explained
  in chat on request; not graded.
- **Ask:** How many multiply-accumulates does one image cost through 784 → 64 → 10?
  If the chip had a single multiplier running at 50 MHz, how long would one image take?
  And what would happen to the network if you deleted the `ReLU`?
- **Passing answer contains:**
  - `Linear(n, m)` computes `y = W·x + b`: each of the m outputs is a dot product of the
    n inputs with one row of W, i.e. n multiply-accumulates. So 784 × 64 + 64 × 10 =
    50,816 MACs per image (biases are additions, not MACs).
  - one MAC per clock → 50,816 cycles ≈ 1.0 ms at 50 MHz. More multipliers divide that
    down; this is the "how much runs in parallel" decision.
  - without `ReLU`, two linear layers compose into one linear layer (`W₂(W₁x) = (W₂W₁)x`),
    so the hidden layer adds nothing. The nonlinearity is what makes it a network.
  - `Flatten` moves no arithmetic: it just reads the 28 × 28 image as 784 numbers in
    row order, so it is an addressing decision in hardware.
- **History:**
  - 2026-10-20 — raised and explained in chat; not yet asked back.

### `layers-weights-biases` — what counts as a layer, and why `Linear` has two parameters
- **Box:** 1 · **Due:** next session
- **Raised:** 2026-10-20 — asked whether `784 → 64 → 10` is a 2- or 3-layer network, why
  each `Linear` has two parameters, and whether one `Linear` is one layer. Explained in
  chat on request; not graded.
- **Ask:** You change the network to `784 → 32 → 32 → 10`. How many `Linear` layers, how
  many hidden layers, and how many parameters in total? Which of those numbers does the
  bias account for, and does it need a multiplier on the chip?
- **Passing answer contains:**
  - one `Linear` = one weight matrix `W` plus one bias vector `b` = one layer. `Flatten`
    and `ReLU` have no parameters and are not layers.
  - 3 `Linear` layers, 2 hidden layers. Parameters: 784×32 + 32 + 32×32 + 32 + 32×10 + 10
    = 25,088 + 32 + 1,024 + 32 + 320 + 10 = 26,506, of which 74 are biases.
  - the bias has one entry per output neuron (shape `[m]`, not `[m, n]`); it shifts when
    that neuron switches on.
  - in hardware the bias is the accumulator's starting value: an add, not a multiply, so
    it costs memory but no multiplier.
  - "2-layer" vs "3-layer" is a counting convention (layers that compute vs rows of
    neurons); a good answer states which one it is using.
- **Links:** [[layer-as-matmul]]
- **History:**
  - 2026-10-20 — raised and explained in chat; not yet asked back.
  - 2026-10-20 — resurfaced: asked the difference between `b1`/`b2` and `w1`/`w2` in the
    export. Explained (layer number vs parameter kind; per-connection vs per-neuron; bias
    at the accumulator's scale). Not yet asked back. Stays box 1.

### `symmetric-quantisation` — turning float weights into n-bit integers plus one scale
- **Box:** 1 · **Due:** next session
- **Raised:** 2026-10-20 — asked how to go to 8-bit weights. He was given three smaller
  questions to work out `quantise()` himself, then asked Claude to write it; Claude wrote
  it (override per Article VI), so he has **not** yet derived it. Ask application, not
  recitation.
- **Ask:** In `train.ipynb`, `int_inference` (which replaced `quantise` on 2026-10-20) uses
  `sw1 = max|w| / qmax` with `qmax = 2**(bits-1) - 1`, i.e. 127 at 8 bits. Why 127 and not 128?
  What breaks if you instead pick a `scale` ten times smaller? And why does accuracy hold
  up at 8 and 6 bits but collapse at 2?
- **Passing answer contains:**
  - signed `n`-bit integers span −2^(n−1) … 2^(n−1)−1; a symmetric scheme uses ±(2^(n−1)−1)
    so zero stays at zero and the range is balanced. 127 is the largest positive 8-bit value.
  - `w ≈ ints × scale`: the ROM stores `ints`; `scale` is one number per matrix, applied
    once after the accumulator (or folded into the next layer's scale), not once per weight.
  - a scale too small makes `w / scale` exceed 127: the ints overflow (the harness's
    `assert`); too large wastes range, so weights collapse onto few integer values.
  - rounding is the only lossy step; fewer bits means a coarser grid. At 2 bits there are
    only 3 usable levels (−1, 0, 1), so most of the structure is gone.
- **Links:** [[layers-weights-biases]]
- **History:**
  - 2026-10-20 — raised; implementation written by Claude at his request, not derived.

### `integer-only-inference` — carrying a scale instead of converting back to float
- **Box:** 1 · **Due:** next session
- **Raised:** 2026-10-20 — asked whether an integer-only network is possible and how it
  would work. Explained in chat on request; not graded.
- **Ask:** In layer 1 the weights are 4-bit with scale `s_w`, the pixels are integers
  0–255 with scale `1/255`. What scale does the accumulator carry, and so what scale must
  a bias be stored in? Why does the final layer never need converting back to float?
- **Passing answer contains:**
  - `(w_int·s_w)(x_int·s_x) = (w_int·x_int)·(s_w·s_x)`: the integer product is exact and the
    accumulator carries the scale `s_w · s_x`.
  - a bias is added straight into the accumulator, so it is stored as
    `round(b / (s_w·s_x))`; that scale is tiny, which is why biases are wide integers.
  - the output scale is a positive constant, so the argmax of the integer scores equals
    the argmax of the real ones.
  - between layers the wide accumulator is rescaled to a narrow activation by
    `(acc × M) >> n`, with a clamp; `M` stands in for a ratio of scales.
  - worst-case accumulator = `n_inputs × max|w| × max|x|`; the width must cover it.
- **Links:** [[symmetric-quantisation]]
- **History:**
  - 2026-10-20 — raised and explained in chat; not yet asked back.
  - 2026-10-20 — the pipeline was then written by Claude (`int_inference` in `train.ipynb`)
    at his request, so he has not derived it. Ask application, not recitation.

### `rom-hex-layout` — one line is one memory word, and the line number is the address
- **Box:** 1 · **Due:** next session
- **Raised:** 2026-10-20 — asked how the exported `.hex` files work and why the bias files
  have 16 lines while the weight files have ~12,000. Explained in chat; not graded.
- **Ask:** In `w2.hex` (10 × 16, row-major), at which line is the weight from hidden
  neuron 5 to output neuron 3? And if the FSM walks output neuron 3's weights in order,
  what address does the counter start at and what does it count to?
- **Passing answer contains:**
  - one line = one word; the address is the line number minus 1 (editors count from 1).
  - address = `neuron × n_inputs + input`, so output 3, input 5 is `3 × 16 + 5 = 53`, line 54.
  - neuron 3's weights are addresses 48 … 63: a counter that starts at `3 × 16` and counts
    up by one for `n_inputs` steps.
  - the line count is the number of weights or biases (one per connection, one per
    neuron), and the word width is the digit count × 4 bits.
  - two's complement: the top bit of the word is the sign (`FF` = −1 at 8 bits).
- **Links:** [[vector-declaration-syntax]], [[layers-weights-biases]]
- **History:**
  - 2026-10-20 — raised and explained in chat; not yet asked back.

---

### `plastic-heat-creep` — why parts near the heater can't be PLA or PETG
- **Box:** 1 · **Due:** next session
- **Raised:** 2026-10-23 — asked "what's an ASA arm?" about the Lab Box clamp concepts
  (`cad/lab-box/concepts/`). Explained: ASA is a printing plastic with a heat-deflection
  temperature of ~93–100 °C vs PETG ~68 °C and PLA ~57 °C (filament makers' data sheets,
  via `docs/lab-box/research/modules-thermal-mech.md`), and a loaded part near its
  softening point creeps.
- **Ask:** The clamp arm holds the heater on the FPGA with a spring, a few cm above a
  65 °C spreader. You print it in PETG. On day one every run is fine. What do you expect
  to see in the shmoo data after a week of runs, and why? Name two different fixes.
- **Passing answer contains:**
  - heat-deflection temperature is where a loaded bar bends a set amount; well below it
    a plastic under constant load still **creeps** (deforms slowly), faster the closer
    it is to that temperature.
  - creep lowers the clamp force → worse thermal contact → the same heater power gives a
    lower package temperature → runs drift and stop being repeatable. A slow drift, not
    a visible failure.
  - fixes: a material with margin (ASA, or metal), or keep plastic out of the hot load
    path entirely (concept 3's metal C-frame); a spring keeps force roughly constant as
    parts move.
- **History:**
  - 2026-10-23 — raised (conceptual question), explained on request. Not yet quizzed.

## Retired

*(nothing yet — a card lands here at box 5, once Alex has explained it correctly and
applied it to a case he had not seen before)*
