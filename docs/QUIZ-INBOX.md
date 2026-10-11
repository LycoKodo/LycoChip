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

---

> **Appended by Claude Code on 2026-10-12, at Alex's direct request.** This
> breaks the Cowork-only convention in `docs/HANDSHAKE.md`. These five are
> *questions to ask*, not graded answers: nothing below has been put to him
> yet. Source for all five: `docs/research/flexheg.md` and Petrie & Aarne,
> arXiv:2506.03409 (printed page numbers, v3). Each one asks him to *apply*
> the idea to LycoChip, because reciting a definition is not a pass
> (Article III). The rubric is folded away so the question can be read
> without the answer.

## flexheg-verify-vs-enforce — 2026-10-12 — NEW CARD PROPOSED
**Source:** paper p.12 (software/TEE "could enable verification … but would not be able to enforce"); flexheg.md §3.2.
**Ask:** Your board runs the metered bitstream and honestly reports 10,000 MACs. That night someone reloads the FPGA over JTAG with a bitstream that has no meter, runs ten million MACs, then reloads yours. Which of the paper's four integration options does this failure most resemble? What did your meter *verify*, and what could it not *enforce*? What would have to be true of the hardware for the second run to be **impossible**, rather than just unreported?
**He said:** not yet asked
**Verdict:** pending
<details><summary>Passing answer contains</summary>

- **Verification** records how the hardware *was* used. **Enforcement** prevents guarantee-breaking use. The meter verified only the sessions in which it was loaded.
- The JTAG reload is the FPGA version of the paper's software/TEE weakness: the operator can simply run something *else* that has no guarantees in it.
- Making it impossible needs the guarantee logic to be **unbypassable**. That means:
  - it sits on the only path, *and*
  - the configuration can't be swapped unnoticed: authenticated or secure boot of the configuration, and an enclosure that is tamper-evident (to detect) or tamper-responsive (to prevent).
- Bonus: the report should attest *which configuration ran*, not just the count. Otherwise a missing report is indistinguishable from an idle board.
</details>

**Drained:** no

## flexheg-interlock-placement — 2026-10-12 — NEW CARD PROPOSED
**Source:** paper p.23–24 (Interlock, "black box"), p.12–13 (trust in measurements); flexheg.md §3.3, §3.5.
**Ask:** Two meters for the same accelerator. **(a)** A counter that watches the multiplier's enable signal. **(b)** A module that every weight and input byte must pass through on the way in, and every result on the way out. Using the paper's Interlock argument: what can (b) guarantee that (a) can't? What does (b) cost? And why does the paper count "treating the accelerator as a black box" as a *benefit*?
**He said:** not yet asked
**Verdict:** pending
<details><summary>Passing answer contains</summary>

- (b) is on the **only** path for data and instructions, so it can't be routed around. It can hash what comes in and attach its log to what goes out.
- (a) trusts an *internal* signal. A modified or faulty accelerator could do work without asserting it. The paper ranks a measurement's trustworthiness by how much it relies on components that could be compromised.
- **Black box:** (b) needs no knowledge of, or trust in, the accelerator's internals. It adapts to new accelerators, and the vendor shares less.
- **Cost:** (b) must keep up with the full throughput and latency of the path. That is harsher the closer it sits to the compute, and costs more area. The paper's cheaper variant just *reads* the buffer instead of gating it.
- Not passing: "(b) is more secure" with no mechanism.
</details>

**Drained:** no

## flexheg-max-merge — 2026-10-12 — NEW CARD PROPOSED
**Source:** paper p.35 (on-the-fly distributed FLOP counting, footnote 12); flexheg.md §3.7.
**Ask:** Four units, each with an Interlock and its own session ID.
- A does 500 MACs and sends the result to both B and C.
- B does 300 MACs on A's data and sends the result to C.
- D works independently, does 400 MACs and sends to C.

What does C's log hold, per source? What total could have contributed to C's data? Then give the wrong answer C would compute (a) if it **summed** the totals in incoming messages, and (b) if it kept only the **single largest** incoming total.
**He said:** not yet asked
**Verdict:** pending
<details><summary>Passing answer contains</summary>

- C's log is `{A:500, B:300, D:400}`, so 1,200 could have contributed.
- (a) Summing incoming totals: A→C says 500, B→C says 800 (A's 500 + B's 300), D→C says 400. That gives **1,700**, because A's work is counted twice.
- (b) A single maximum gives **800**, because it loses D, which is an independent source.
- Hence: keep **per-source** values, take the **max per source**, and only then sum across distinct sources. The **session ID** is what makes the "same source" check possible.
- Bonus: why max rather than latest? Logs arrive out of order. A count only grows within a session, so the max is the freshest *known* value.
</details>

**Drained:** no

## flexheg-laundering — 2026-10-12 — NEW CARD PROPOSED
**Source:** paper p.33–34 ("FLOP laundering", hashing and delaying external data); flexheg.md §3.7.
**Ask:** Your board only ever runs small MNIST inferences, and your meter counts every MAC honestly. Explain how someone could still "launder" a very large amount of compute *through your board's weight-load port*, in the paper's sense. What are the paper's two defences for external data? Which part of one defence could your board do entirely on its own, and what would it still need from someone outside the board for that to mean anything?
**He said:** not yet asked
**Verdict:** pending
<details><summary>Passing answer contains</summary>

- **Weights are external data.** They can embody any amount of compute done elsewhere: training runs, previous sessions, parallel boards. A meter that counts only local MACs is blind to it. Laundering means hiding prior or parallel compute inside "external" data, so it is never counted.
- **Defence 1, audited explanation:** hash the incoming data and log the hash plus the amount. An auditor later attests what that hash *is* (for example, human-generated, or known provenance).
- **Defence 2, delay:** an auditor or a public ledger attests the hash existed some time *T* earlier. This makes chaining runs slow: months for sequential runs, seconds can be enough for parallel ones.
- The board alone can **hash and log** (hash + byte count in its report). The *meaning* of that hash needs someone outside to attest it.
- Small unexplained inputs may be allowed, but must be **logged and bounded** so they can't accumulate.
</details>

**Drained:** no

## flexheg-k-of-n — 2026-10-12 — NEW CARD PROPOSED
**Source:** paper p.36–38 (Algorithm 1, licences, minimal guarantee version); flexheg.md §3.8.
**Ask:** Five stakeholders can sign updates to LycoChip's meter logic. Walk the threshold: what goes wrong at k=1, and what goes wrong at k=5? The paper suggests *different* thresholds for different kinds of change — give one LycoChip change that deserves a low k and one that deserves a high k, and say why. Finally: why can a voluntary update support *attestation* but not *enforcement*?
**He said:** not yet asked
**Verdict:** pending
<details><summary>Passing answer contains</summary>

- **k=1:** any single party, or a thief of any single key, can push a malicious update. Safety fails.
- **k=5:** any single party can veto, including a vital security fix. Liveness fails. The threshold trades the two against each other.
- **Low k:** a parameter tweak within pre-agreed bounds (for example, a reporting interval). **High k:** a change to what is counted, or to the update rules themselves (the paper allows updates to change the update rules).
- **Voluntary updates:** a device that skips an update still truthfully *reports* its version, which supports attestation. To *force* updates you need something like a **licence** carrying a minimum version, expiring on a trusted clock or cycle counter.
- Bonus: the unrevocable minimal guarantee version is the floor no update can remove, and it can never be patched.
</details>

**Drained:** no
