# Quiz inbox — Cowork → Claude Code

Written by the Cowork session (the tracking/quizzing side). **Append-only, and mine
alone** — see `docs/HANDSHAKE.md`. Claude Code folds these into `docs/LEARNING.md`, sets
the boxes, and flips `Drained: no` → `yes` here. Nothing in this file is a card; it is
evidence for grading.

---

## sized-literals — 2026-09-08 — NEW CARD PROPOSED
**Source:** a chat session outside the repo (shared transcript, read by Cowork 2026-09-08).
**What happened:** he set the divider threshold to `27'b1`, then "fixed" it to `25'b1`,
believing the value changed. It did not — he had resized the container, not the contents.
Prompted, he wrote: *"oh so 25'b1 isnt 11111.... its 000...1?"* — correct, unprompted,
in his own words. He then asked how to write all-ones and was shown `{25{1'b1}}`,
`25'h1FFFFFF` and SystemVerilog `'1`.
**Verdict:** partial — self-corrected once told the symptom, has not applied it to a new case.
**Suggested card:** `WIDTH'BASE_VALUE`; the width is the container, the value is written
normally in the named base; narrower literals **zero-extend** on the left (`'bx`/`'bz`
extend with x/z, signed literals sign-extend). Passing answer must distinguish
`25'b1` = 1 from `{25{1'b1}}` = 33,554,431, and say which one a threshold wants.
**Missing for a pass:** he has not yet stated *why* zero-extension is the rule, and he then
used `25'h1FFFFFF` as his actual threshold — see the entry below.
**Drained:** no

## wire-vs-reg, vector-declaration-syntax — 2026-09-08 — CARDS BURNED, REWORD THE ASKS
**Source:** the same outside chat.
**What happened:** both cards' *rubric answers were given to him in full* in that session —
`reg` is procedural assignment not storage, the sensitivity list decides the hardware,
ports default to `wire`, packed dimension before the name is part of the type, unpacked
after the name is an array, `[3:0]` vs `[0:3]` is convention. He did not derive any of it;
he received it.
**Verdict:** not gradeable. Asking `LEARNING.md`'s current questions now tests recall of a
same-day explanation, not understanding.
**Action for you:** keep both at box 1 and **replace the `Ask` with an application case** —
e.g. for `wire-vs-reg`, hand him a `reg` assigned in `always @(*)` and ask how many
flip-flops it makes and why; for `vector-declaration-syntax`, ask what
`reg [7:0] m [0:1023]` costs on an EP4CE6 and which bracket caused it.
**Drained:** no

## non-blocking-rhs — 2026-09-08 — RAISED, UNRESOLVED IN CODE
**Source:** outside chat + the synthesis evidence in `builds/20260908-193646-*`.
**What happened:** he was told, twice, that `led <= ~data` alongside `data <= data + 1'b1`
samples the **old** `data`, that the display is therefore permanently one count behind, and
that `led` is a function of `data` rather than state. The code on disk still has it in all
three branches. The fitter's verdict is now on record and is stronger than the argument:
`Warning (13310)` — `led[0..3]~reg0` **converted into an equivalent circuit using a
register and a latch**, because the asynchronous-reset branch assigns a non-constant.
He has inferred four latches and has not seen it.
**Verdict:** open — not quizzed by me, evidence gathered.
**Drained:** no

## Cowork's two questions, asked 2026-09-08, answers not yet given
1. `Warning (12069): Ignored assignment(s) for "key[0]" because "key" is not a bus` ×5, then
   `Critical Warning (169085): No exact pin location assignment(s) for 1 pins of 6`. Which
   physical button is his reset right now, and how does he prove it from the build outputs
   rather than by pressing buttons? (This is the Article V `.pin` audit trap, live.)
2. Why did the tool need a **latch** for `led`, when `data` — assigned in the same branch,
   on the same edge — did not?

Earlier, still unanswered: derive `blink`'s 29 registers; construct a case where `&&` and
`&` diverge (that second one is your `logical-vs-bitwise` card).
**Drained:** no
