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
  - 2026-09-22 — raised from live evidence in `keytest`, not yet quizzed.

### `wire-vs-reg` — the two storage classes
- **Box:** 1 · **Due:** session 2
- **Raised:** 2026-09-05 — asked directly in a comment in `full_adder.v`:
  *"what is reg, and wire, and why is this not required in this case?"*
- **Ask:** You wrote a working full adder without declaring `wire` or `reg` anywhere.
  What are those two things actually for, and which one did your design end up using?
  Then: if you wanted `S` to hold its value until the next clock edge instead of
  following its inputs immediately, what would have to change?
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
- **Ask:** In `input [2:0] key`, why does the `[2:0]` come before the name? And what
  would `reg [7:0] mem [0:1023]` be — why are there two brackets, and are they the
  same kind of thing?
- **Passing answer contains:**
  - the leading `[2:0]` is part of the **type** — a width. It declares one 3-bit bus,
    which is why it sits where a type would.
  - a dimension written *after* the name is an **unpacked array**: many separate
    elements, i.e. a memory. So `mem` is 1024 separate 8-bit words.
  - `[2:0]` vs `[0:2]` is bit ordering — which end is most significant. Both are legal;
    the convention is MSB-first.
- **History:**
  - 2026-09-05 — raised, not yet quizzed.

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

---

## Retired

*(nothing yet — a card lands here at box 5, once Alex has explained it correctly and
applied it to a case he had not seen before)*
