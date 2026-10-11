# Learning log

Spaced-repetition cards, governed by **Article III** of `CLAUDE.md`.
Claude maintains this file. Alex does not need to touch it.

**Session count: 1**  ← increment at the start of each working session

Boxes: 1 = new/wrong (next session) · 2 = +2 · 3 = +4 · 4 = +8 · 5 = retired.
A wrong answer, or the confusion resurfacing in code, sends a card straight back to box 1.

---

## Due now

### `pin-assignment-shape` — when the .qsf and the port list disagree
- **Box:** 1 · **Due:** next session
- **Raised:** 2026-09-22 — `keytest.v` declares `output wire led` (a scalar) while
  `keytest.qsf` says `set_location_assignment PIN_87 -to led[0]`. Quartus emitted
  `Warning (12069): Ignored assignment(s) for "led[0]" because "led" is not a bus`,
  then `Critical Warning (169085): No exact pin location assignment(s) for 1 pins of 3`.
  The design still lit the right LED — `keytest.pin` shows `led : 87 : ... : N`, so
  the fitter picked PIN_87 on its own and happened to pick the one he wanted. The
  I/O standard assignment was dropped with it: `led` came out at **2.5 V**, not the
  3.3-V LVTTL the board wants. This is the same trap Cowork already flagged on
  `key[0]` in `QUIZ-INBOX.md`, now resurfaced in different code.
- **Ask:** Your `.qsf` assigns `PIN_87 -to led[0]`, and the LED lit up correctly.
  But `keytest.pin` records that pin as `User Assignment: N`. What does `N` mean
  there, and if your assignment was ignored, why did the right LED still light?
  Then: what would you expect to change in `keytest.pin` if you added a third key
  to the port list but forgot to give it a location?
- **Passing answer contains:**
  - the `.qsf` refers to pins **by port name**, so `led[0]` matches nothing when the
    port is a scalar `led` — the assignment is discarded, not applied.
  - `User Assignment: N` means **the fitter chose that pin**, not him. PIN_87 was
    luck, and a later recompile is free to choose differently.
  - the `IO_STANDARD` line was keyed to `led[0]` too, so it went as well — hence
    2.5 V instead of 3.3-V LVTTL.
  - a missing pin location is **not an error** (Article V): the only way to know is
    to read the `User` column in `<name>.pin`, not to press buttons and see if it
    looks right.
- **Links:** [[vector-declaration-syntax]], [[implicit-nets]]
- **History:**
  - 2026-09-08 — Cowork posed the `key[0]` version: which physical button is his reset,
    proven from the build outputs (QUIZ-INBOX). Unanswered.
  - 2026-09-22 — raised from live evidence in `keytest`, not yet quizzed.
  - 2026-10-12 — still live: `clock_counter.qsf` assigns `PIN_88 -to key[0]`, and
    `clock_counter.v` declares a scalar `input key`.

### `wire-vs-reg` — the two storage classes
- **Box:** 1 · **Due:** session 2
- **Raised:** 2026-09-05 — asked directly in a comment in `full_adder.v`:
  *"what is reg, and wire, and why is this not required in this case?"*
- **Ask** *(replaced 2026-10-12: the 2026-09-08 outside chat gave him the old rubric
  verbatim, so the old Ask now tests recall)*: Here is `reg [3:0] y;`, assigned only
  inside an `always @(*)` that covers every case. How many flip-flops does Quartus
  build for `y`, and why? Then make the smallest change that turns `y` into four
  real flip-flops. What did you change, and why wasn't it the keyword?
- **Passing answer contains:**
  - a `wire` is continuously driven — it must have something driving it at all times
    (an `assign`, or a module output). It has no memory.
  - a `reg` holds its value until procedurally reassigned, and may only be assigned
    inside `always`/`initial`.
  - **the trap:** `reg` does not mean flip-flop. A `reg` assigned in `always @(*)`
    synthesises to plain combinational logic.
  - what actually creates a flip-flop is the *clock edge* (`always @(posedge clk)`),
    not the keyword.
- **History:**
  - 2026-09-05 — raised, not yet quizzed.
  - 2026-09-08 — rubric handed to him in full in an outside chat (QUIZ-INBOX, Cowork).
    Not gradeable as asked; kept at box 1.
  - 2026-10-12 — Ask replaced with an application case, as Cowork suggested.

### `implicit-nets` — why it compiled anyway
- **Box:** 1 · **Due:** session 2
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

### `vector-declaration-syntax` — `[2:0]` and where it goes
- **Box:** 1 · **Due:** session 2
- **Raised:** 2026-09-05 — asked in `full_adder.v`: *"why is verilog array syntax in
  reverse? why is verilog array index first, then variable?"*
- **Ask** *(replaced 2026-10-12: the old rubric was handed over verbatim on
  2026-09-08)*: Two declarations, both 8,192 bits: `reg [7:0] m [0:1023];` and
  `reg [8191:0] m;`. On an EP4CE6, which resource does each one land in, and does
  each one fit? Which bracket made the difference?
- **Passing answer contains:**
  - the leading `[2:0]` is part of the **type** — a width. It declares one 3-bit bus,
    which is why it sits where a type would.
  - a dimension written *after* the name is an **unpacked array**: many separate
    elements, i.e. a memory. So `m [0:1023]` is 1024 separate 8-bit words, which
    Quartus can place in **M9K block RAM** (about one block; ~3% of 276,480 bits)
    *if* it is accessed like a RAM.
  - `reg [8191:0]` is **one** 8,192-bit bus, so it becomes **flip-flops**: more than
    the 6,272 registers the part has. It does not fit.
  - `[2:0]` vs `[0:2]` is bit ordering — which end is most significant. Both are legal;
    the convention is MSB-first.
- **History:**
  - 2026-09-05 — raised, not yet quizzed.
  - 2026-09-08 — rubric handed over in full in an outside chat (QUIZ-INBOX, Cowork).
    Not gradeable as asked; kept at box 1.
  - 2026-10-12 — Ask replaced with the cost-on-an-EP4CE6 case Cowork suggested.
    **Unverified:** the M9K-vs-registers outcome is the expected synthesis result. It
    has not been run through Quartus here, so confirm it with a build before grading
    against it.

### `logical-vs-bitwise` — `&&` vs `&`
- **Box:** 1 · **Due:** session 2
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
  - 2026-09-08 — Cowork asked it again (QUIZ-INBOX); still unanswered. This is the
    same asking, not a second card.

### `sized-literals` — `25'b1` is one, not all ones
- **Box:** 1 · **Due:** next session
- **Raised:** 2026-09-08 (QUIZ-INBOX, Cowork). He changed a divider threshold from
  `27'b1` to `25'b1`, believing the value changed. Only the container did. Once
  prompted, he wrote *"oh so 25'b1 isnt 11111.... its 000...1?"*. That was correct,
  but he then used `25'h1FFFFFF` as the threshold without saying why.
- **Ask:** A counter must wrap after exactly 2²⁵ cycles. A friend writes
  `if (cnt == 25'b1)`, and you write `if (cnt == {25{1'b1}})`. How many cycles does
  each one actually wait? Then: what does `8'b101` hold, and why is zero the right
  thing to fill with?
- **Passing answer contains:**
  - `WIDTH'BASE_VALUE`: the width is the container, and the value is written normally
    in the named base. `25'b1` is **1**; `{25{1'b1}}` (= `25'h1FFFFFF`) is
    **33,554,431**.
  - a narrower literal **zero-extends** on the left, so `8'b101` is `8'b0000_0101`.
    That keeps the *number* the same; `x`/`z` extend with `x`/`z`, and signed
    literals sign-extend.
  - which one a wrap threshold wants, and the off-by-one that comes with it: wrapping
    *at* all-ones versus counting 2²⁵ cycles.
- **History:**
  - 2026-09-08 — partial (self-corrected once shown the symptom; has not yet applied
    it to a new case). Folded in from QUIZ-INBOX on 2026-10-12.

### `non-blocking-rhs` — `<=` samples the old value; a reset that assigns a variable makes a latch
- **Box:** 1 · **Due:** next session
- **Raised:** 2026-09-08 (QUIZ-INBOX, Cowork), and still live in
  `projects/clock_counter/rtl/clock_counter.v` as of 2026-10-12.
  - `led <= ~data` sits beside `data <= data + 1'b1` in the same edge, so `led` shows
    the *previous* count.
  - The async-reset branch assigns `led <= ~data`, which is not a constant. The fitter
    recorded `Warning (13310)`: `led[0..3]~reg0` was converted into an equivalent
    circuit using a register and a latch.
  - `lint.sh` (iverilog + Verilator) reports this file **clean**. Lint does not see it.
- **Ask:** In your `clock_counter`, the reset branch sets `data <= 0` and
  `led <= ~data` on the same edge. Straight after reset is released, what do the LEDs
  show, and why? Then: why did the fitter need a latch for `led`, but not for `data`?
- **Passing answer contains:**
  - non-blocking assignments all sample their right-hand sides **before** any of them
    update. So `led <= ~data` sees the old `data`, and `led` is one count behind.
  - an **async** reset must load a value the flip-flop can force *without a clock*. A
    constant can be built into the flop's preset or clear. `~data` is a moving signal,
    so the tool emulates it with a register plus a latch.
  - `data`'s reset value is a constant (`0`), so a plain flop with an async clear
    suffices.
  - the cure is a design choice: make `led` a function of `data`
    (`assign led = ~data`), or give it a constant reset value.
- **Links:** [[wire-vs-reg]]
- **History:**
  - 2026-09-08 — explained to him twice in an outside chat; the code was unchanged
    afterwards. Folded in from QUIZ-INBOX 2026-10-12, not yet quizzed.

### `counting-flip-flops` — where do blink's 29 registers come from?
- **Box:** 1 · **Due:** +2 sessions
- **Raised:** 2026-09-08. Cowork asked him to derive `blink`'s 29 registers, given that
  it declares only two `reg`s. Unanswered.
- **Ask:** A design declares `reg [24:0] cnt;` and `reg [3:0] value;`, both assigned
  under `always @(posedge clk)`. How many flip-flops do you expect? Then: you add
  `reg [3:0] shadow;`, assigned only in `always @(*)`. Does the count change?
- **Passing answer contains:**
  - a clocked `reg` costs one flip-flop **per bit**: 25 + 4 = **29**. The number of
    `reg` declarations is irrelevant; widths are what count.
  - `shadow` in `always @(*)` adds **zero** flops (combinational), which links back to
    `wire-vs-reg`.
  - the fitter report is where the real count is read (Article IV). Synthesis can also
    remove flops it proves constant, or duplicate them.
- **Links:** [[wire-vs-reg]], [[vector-declaration-syntax]]
- **History:**
  - 2026-09-08 — asked by Cowork, unanswered. Folded in 2026-10-12.

---

## Retired

*(nothing yet — a card lands here at box 5, once Alex has explained it correctly and
applied it to a case he had not seen before)*
