# flexHEG Part II — study notes for LycoChip

**Paper:** James Petrie & Onni Aarne, *Technical Options for Flexible
Hardware-Enabled Guarantees*. arXiv:2506.03409, cs.CR. v1 was posted
3 Jun 2025; v3 (18 Jun 2025) is the current version. The PDF cover reads
"Flexible Hardware-Enabled Guarantees — Part II", April 2025, commissioned by
ARIA. It is 59 pages.

**How these notes were made.** The full v3 text was read. Key quotes and page
numbers were then re-checked against the extracted text. Page numbers are the
**printed** page numbers of v3, and the paper has no numbered sections, so cite
it as *heading + page*. Anything marked **[note]** is commentary, not the paper.

**What this is not.** It explains the paper and asks questions about
LycoChip. It does not design your meter or your Interlock. Those are yours
(Article I), and the open questions at the end are written to stay open.

---

## 1. The series

| Part | Title | arXiv |
|---|---|---|
| I | *Flexible Hardware-Enabled Guarantees for AI Compute*. Petrie, Aarne, Ammann, Dalrymple | 2506.15093 |
| **II** | ***Technical Options for Flexible Hardware-Enabled Guarantees*. Petrie, Aarne** | **2506.03409** |
| III | *International Security Applications of Flexible Hardware-Enabled Guarantees*. Aarne, Petrie | 2506.15100 |

- **Part I** is the *why*: the motivation, and the governance mechanisms
  flexHEG enables.
- **Part III** is the *who decides*: treaties, update governance, and the
  "baseline rulesets" that can never be revoked.
- **Part II** is the *how*, and the one that matters most for hardware.

## 2. The argument in one paragraph

AI developers make claims about how they use compute that outsiders can't
check. flexHEG puts a small, **auditable Guarantee Processor** next to (or
inside) the accelerator. It watches what the accelerator does and checks that
against rules. It then emits **signed certificates** saying a rule was met,
and the underlying data never leaves the device. A **Secure Enclosure**
protects it physically. The two are deliberately separable, so that different
parties can build them. The guarantees are **flexible**: the rules can be
updated, but only with many independent parties signing off. The paper's
favoured shape for near-term hardware is the **Interlock**, a guarantee
component sitting on the data path, so that everything in and out must pass
through it.

## 3. Fuller summary, in the paper's order

### 3.1 Design goals (Table 1, p.5–7)

Six goals, broken into 25 requirements:

1. **Guarantees about past and future workloads.** This needs general-purpose
   logic, access to workload data, accurate timekeeping, the ability to control
   usage, and automated checking.
2. **Security.** Protection against non-invasive attacks, resistance to
   invasive ones, confidential and authenticated communication, and
   confidential storage.
3. **Updates.** A secure update process.
4. **No backdoors.** No surveillance or control backdoors, no intentional
   flaws, and third-party verifiability.
5. **Low burden.** Cost, power, cooling, rack fit, latency and throughput, rare
   false positives, reliability, and minimal disruption to how people work.
6. **Deployment.** At scale by 2027, across accelerator types, and on short
   notice.

A footnote sizes "significant burden" at roughly 1–2% cost, or about 5% if
regulation requires it.

### 3.2 Where to modify the accelerator — the four integration options (p.7–12)

| Option | Strength | Weakness |
|---|---|---|
| **Integrated hardware** (on the die or board) | Best security and data access. Signals are hard to tamper with. | Needs the chip vendor and takes years. Estimated 3.7–7.9 years to displace non-flexHEG accelerators. |
| **Retrofitted hardware** | Faster, and less reliance on the vendor. Options: an external measurement device, a PCIe-slot card, or replacing the NIC or BMC. | Easier to decouple, so it needs its own enclosure. Its readings can be spoofed. |
| **Firmware** (Secure Boot, rollback protection) | Runs on-chip, and can require periodic authorisation. | Needs the vendor, and proprietary firmware is hard to audit. **Voltage glitching during the signature check** is the classic bypass. |
| **Software / TEE** | Fastest, and open to third parties. | *"software-based solutions could enable verification about how hardware has been used, but would not be able to enforce that the hardware cannot be used in guarantee-breaking ways"* (p.12). |

**Verification versus enforcement** is the distinction to carry through the
rest of the paper.

### 3.3 Accelerator measurements (p.12–13)

The candidate sources of truth are:

- **HBM contents**;
- **kernels/instructions**;
- **network traffic**;
- **performance counters** — "FLOP counts, memory access patterns…";
- **power**.

A measurement is more trustworthy when it is taken **inside the enclosure**
and relies on fewer components that could be compromised. Power is
"difficult to falsify without physical modifications". Combining several
independent sources makes falsification harder.

### 3.4 The two components (p.13–21)

**Guarantee Processor.** It is meant to be "smaller, simpler, less performance
sensitive" than the accelerator, so it can be audited and open-sourced without
exposing trade secrets. It needs:

- side-channel-free cryptography;
- public-key operations to verify updates and sign certificates, "ideally
  quantum secure";
- a reliable clock;
- a secure random number generator;
- glitch defence.

**The paper's FPGA argument (p.15).** Against hidden backdoors, it suggests
*"Using FPGAs to execute some or all of the guarantee logic, because they can
have their configurations publicly audited, might be easier to check for
physical inconsistencies because of their more uniform structure, and can use
variants of configurations with equivalent logic to make many hardware trojans
impractical."* It also suggests open-sourcing plus scanning random chips, and
lockstep processors from several vendors.

**Secure Enclosure (p.18–21).** Two kinds:

- **Tamper-evident:** you can tell afterwards that it was opened. This is
  "sufficient" for verification (p.3), and deters *covert* cheaters.
- **Tamper-responsive:** it reacts to tampering by wiping keys or disabling
  the accelerator. It is needed for guarantees about *future* use against
  *overt* adversaries.

A **PUF inside the enclosure** sits in between: tampering destroys the
measurements the key is derived from. The paper is frank that "nation-state
attackers can likely compromise the best current secure enclosures".

### 3.5 The Interlock (p.23–24)

*"We refer to a flexHEG component sitting on the data path as an
'Interlock.'"* (p.23)

- **Why on the path.** It is *"the only path for data and instructions to
  enter the accelerator"*, so it can robustly monitor and/or control that flow.
- **Black box.** It *"can treat the accelerator as a black box, with less need
  to understand or trust internals"*. That makes it faster to adapt to new
  chips, and the vendor has to share less.
- **The ideal.** Direct access to "a simple part of the data path, like a
  buffer", and direct control over the crypto hardware. The easier version
  "just be able to read the buffer".
- **Figure 4.** The accelerator and the Interlock sit inside one enclosure.
  The Interlock contains an internal buffer, a secure processor, crypto
  hardware and an external buffer.
- **Where it could live.** As an IP block on the die, as a nearby chiplet, as
  part of the HBM, or as a separate network relay or switch.
- **The cost.** The closer it sits to the die, the harsher the throughput and
  latency demands.
- **The NIC as a retrofit point.** It is external and swappable, it has
  precedent (AWS Nitro), and it already has inline crypto and DMA. The paper
  calls it *"the most promising component that third parties could modify"*
  (p.39).

### 3.6 Encrypted cluster formation (p.25–26)

Each Guarantee Processor declares which devices it will send data to. It then
gets keys (from a governance service or a local table) and sets up a
per-source AES-GCM session key. Because the Interlock controls key exchange,
it **sees the cluster's shape**: who is talking to whom.

### 3.7 The FLOP-counting example (p.33–35) — the closest thing to your meter

- **The threat.** Mislabelling compute: for example, claiming 80% inference
  and 20% training when it is all training. Or splitting one big training run
  into "unrelated" sequential runs. Or **laundering** compute through
  "external data".
- **The quantity.** The FLOPs that *could have causally contributed* to an
  output. That is local FLOPs plus the FLOPs of every upstream accelerator
  whose data was used.
- **The assumption.** *"We assume that the Interlock is able to keep an
  up-to-date log of the FLOPs performed by the local accelerator after it is
  powered on"*, via performance counters, kernel scanning or power (p.33).
  **[note] The paper never builds the local counter. That assumed component
  is exactly what your MAC counter would be.**
- **The protocol, "On-the-fly distributed FLOP counting" (p.35):**
  1. At initialisation each accelerator is **power-cycled**, long enough for
     RAM to clear.
  2. The Interlock generates a **new session ID** and sets that session's
     counter to 0.
  3. Outgoing data carries a **prefix containing the entire FLOP log**.
  4. On input, the receiver adds new sources and keeps the **maximum**
     value per source.
- **Why per-source maximums, not one running total (footnote 12).** A does
  2,000 FLOPs and sends the result to B. B does 1,000 and sends back "3,000".
  A single running counter would record 5,000; the truth is 3,000.
- **External data.** Either hash it, logging the hash and the amount so an
  auditor can later attest what it was, or delay it. For sequential runs the
  delay is on the order of months: with a 10²⁶ cap and a 3-month delay, it
  takes 10 restarts and at least 30 months to reach 10²⁷.
- **Streaming caveat.** If the prefix is sent before all the output is
  staged, include a local-FLOP allowance, and halt if it is exceeded.
- **Export.** Exported data carries a **signed certificate** with the
  detailed log, so chunks can be combined later without double counting.

### 3.8 Updates (p.36–38)

**k-of-n signatures** (Algorithm 1, p.37): hash the firmware, count the
distinct authorised valid signers, and accept the update if there are at
least *k*.

- Higher thresholds for big changes; lower ones for in-range parameter
  changes.
- Post-quantum signatures are preferred.
- **Voluntary updates are enough for attestation, but not for enforcement.**
  Enforcement uses **licences** carrying a minimum version number, timed by a
  secure clock or a cycle counter. A cycle counter lets an operator "save up"
  usage time by leaving the chip idle (footnote 14).
- A **minimal guarantee version** that can never be revoked gives a floor.
  Its downside: it can never be patched.

### 3.9 Threat model (Appendix B)

**Attacks:**
- firmware bugs;
- mis-specified guarantee logic;
- physical tampering, *"e.g., resetting a FLOP counter"*;
- backdoors in design or manufacturing;
- secret changes to the cluster;
- theft of authorisation keys.

**Scenarios**, from weakest to strongest adversary:
- domestic oversight, against covert developers;
- treaty verification, against covert states;
- treaty enforcement, against overt states with thousands of experts.

**The bar is economic:** *secure enough that the cost of circumvention
outweighs the benefits*. Technical measures sit alongside inspections and
whistleblowers.

### 3.10 Roadmap (p.38–46)

| Project | What | Note |
|---|---|---|
| 1 | Tamper-evident Secure Enclosure | 1–3 years to deploy |
| 2 | Trustworthy Guarantee Processor | Analyse existing NICs, then an open-source IP block. Its listed features include "FPGA and/or general-purpose processor capability", secure boot, a secure RNG and glitch protection |
| **3** | **Accurate Compute Graph** | Logging what workloads actually do. Its claim protocol *"could be prototyped using user-programmable logic on an existing smartNIC or FPGA attached to a leading accelerator (with security and auditability requirements skipped until later)"* (p.43) |
| 4 | Automated Guarantee Checking | Classifiers over compute graphs |

**[note] A small correction to the brief:** Project 3's *goal* is dynamic
compute-graph logging. The smartNIC/FPGA is its suggested *prototyping
platform*, with security deliberately deferred. That framing — logic first,
security later — matches what an EP4CE6 can honestly show.

### 3.11 Read it critically

It is a v3 of a commissioned report, and some draft seams show:

- Two unresolved citations, "[Leonie]" and "[EU AI act, diffusion rule]"
  (p.33).
- A cross-reference to a section that doesn't exist (p.27).
- Some reference numbers in the enclosure section point at the wrong entries.
- A PCIe arithmetic slip on p.27.
- The measurements table is garbled (p.12–13).

None of this changes the argument. It does mean you should cite the original
sources rather than the paper's citations of them.

---

## 4. Key terms

| Term | Meaning in the paper |
|---|---|
| **flexHEG** | Flexible Hardware-Enabled Guarantees. The whole system: a Guarantee Processor plus a Secure Enclosure. |
| **Guarantee Processor** | The auditable component that monitors the accelerator, checks it against rules and signs certificates (p.3, p.14). |
| **Secure Enclosure** | Physical tamper protection. It can be the size of a chip, board, tray or rack. |
| **Tamper-evident / tamper-responsive** | Shows that tampering happened / reacts to tampering (wipe, disable). |
| **Interlock** | A flexHEG component *on the data path* (p.23). |
| **Integrated / retrofit / firmware / software (TEE)** | The four ways to modify an accelerator (p.7–12). |
| **Verification vs enforcement** | Checking how hardware *was* used, versus preventing it from being *misused*. Software/TEE can only do the first (p.12). |
| **Certificate** | A signed statement from the Guarantee Processor: a rule was met, a cluster was approved, or the FLOP log on exported data. |
| **Session ID** | A fresh identifier per power-on, which keys that session's FLOP count (p.35). |
| **FLOP laundering** | Hiding prior or parallel compute inside "external data" so it isn't counted (p.34). |
| **Covert vs overt adversary** | One who avoids detection, versus one who openly breaks commitments (Appendix B). |
| **k-of-n** | An update needs valid signatures from at least *k* of *n* authorised parties (p.36–37). |
| **Licence** | A periodic authorisation an accelerator needs to keep running. It carries a minimum firmware version (p.38). |
| **Minimal guarantee version** | A floor of rules that can't be revoked. In Parts I/III, "baseline rulesets". |
| **PUF** | A physically unclonable function: a key derived from manufacturing variation, so it is not stored anywhere. |

---

## 5. What matters for a single-FPGA prototype

**What transfers to one EP4CE6, and what is datacentre-only.**

| Paper concept | On one board? | **[note]** |
|---|---|---|
| A local counter of work done | **Yes** | The component the paper assumes (p.33). Yours would count MACs and weight loads. |
| A session ID, and the counter's lifecycle at power-on | **Yes** | The paper resets to 0 *with a new ID*. Compare that with your "host can't reset" goal (question 1 below). |
| Hashing data that enters, logging hash + amount | **Yes** | Weights loaded from the host are "external data" in the paper's sense. |
| A signed certificate on output | **Partly** | Signing needs a key. Where would one live? (questions 6–7) |
| The Interlock *on the path* versus a passive tap | **Yes** | An architecture choice you can actually make in RTL. |
| Figure 4's split: buffer / secure processor / crypto | **Yes** | It suggests module boundaries you could audit separately. |
| The streaming-prefix race | **Yes** | Applies the moment results stream out before the count is final. |
| Per-source max-merging | **Only with two boards, or two logical units** | |
| Secure Enclosure, PUF, tamper response | **No** | Explicitly out of scope: there is no physical protection. |
| NIC retrofit, encrypted cluster formation, licences, k-of-n governance | **No** | Datacentre and governance scale. Worth *describing* in a write-up; not worth building here. |

**[note] Two placement facts to reason with, not conclusions.**

1. If the meter and the accelerator share one FPGA, that is closest to the
   paper's *integrated* option (an IP block on the die), not its NIC retrofit.
2. With no enclosure, anyone with the JTAG cable can load a different
   configuration. Ask what any claim survives — see question 8.

---

## 6. Lightweight hashes: reading pointers only

**The budget, in numbers somebody else measured.** The open-source
[secworks/sha256](https://github.com/secworks/sha256) core (BSD-2-Clause)
reports, in its own README, built with Quartus II 13.1:

- an **EP4CE6** (the same die as yours, F17 package);
- **3,882 LEs**, **1,813 registers**, 74 MHz, 66 cycles per block.

That is about **62% of your 6,272 LEs** for one off-the-shelf SHA-256 —
*reported by its author, not synthesised here*. It is the yardstick for
everything below. Whether a hash fits is a question for the fitter report,
not for a paper's area table.

Reading list, roughly in the order worth reading:

1. **Ascon** — NIST **SP 800-232**, *Ascon-Based Lightweight Cryptography
   Standards for Constrained Devices* (final, 13 Aug 2025).
   - It defines Ascon-AEAD128, **Ascon-Hash256**, Ascon-XOF128 and
     Ascon-CXOF128, all from one 320-bit permutation.
   - Read the permutation description, and think about how one primitive
     could give you both a hash *and* keyed authentication.
   - csrc.nist.gov/pubs/sp/800/232/final
2. **FPGA benchmarking of the NIST LWC candidates** — Mohajerani, Haeussler,
   Nagpal, Farahmand, Abdulgadir, Kaps, Gaj, *FPGA Benchmarking of Round 2
   Candidates in the NIST Lightweight Cryptography Standardization Process*,
   IACR ePrint 2020/1207.
   - Real FPGA area and throughput numbers across Xilinx, Intel and Lattice
     tools, from GMU's CERG group.
   - Check which Intel device they targeted, and how close its logic element
     is to a Cyclone IV E's 4-input LUT.
3. **The SHA-256 core above** — the spec is FIPS 180-4. Read the README's
   results table, and its explanation of why the core takes 66 cycles.
4. **SPONGENT** — Bogdanov, Knežević, Leander, Toz, Varıcı, Verbauwhede,
   *SPONGENT: A Lightweight Hash Function*, CHES 2011. A sponge built for
   tiny area.
5. **PHOTON** — Guo, Peyrin, Poschmann, *The PHOTON Family of Lightweight
   Hash Functions*, CRYPTO 2011.
6. **Quark** — Aumasson, Henzen, Meier, Naya-Plasencia, *Quark: A Lightweight
   Hash*, CHES 2010.
7. **Keccak at reduced width** — the Keccak team's reference documents
   (keccak.team) on the Keccak-f[200]/[400] permutations. SHA-3's structure
   scales down; see how much security the smaller widths give up.
8. **BLAKE2s** — RFC 7693. An ARX design with 32-bit words, a useful contrast
   to the bit-oriented sponges.

**Concepts to understand before choosing any of them:**

- **The area-versus-throughput lever.** The same algorithm can be built
  unrolled, iterative (one round per cycle) or bit/byte-serial. Area and
  throughput trade almost one-for-one. Which one does your meter actually
  need, given how fast weights arrive?
- **Hash vs MAC vs signature.** A hash alone proves integrity *only to
  someone who already trusts where the hash came from*. A MAC (HMAC, RFC 2104,
  or a keyed Ascon mode) needs the verifier to hold the same secret. A
  signature lets anyone verify with a public key, and costs far more area.
  The paper asks for public-key signing, "ideally quantum secure" (p.14).
- **Where a key lives on this part.** The paper's answers are secure memory,
  a PUF or an enclosure. I have **not** checked what the EP4CE6 offers here
  (for example, whether Cyclone IV E supports bitstream encryption) — read the
  configuration chapter of the *Cyclone IV Device Handbook* in `resources/`.

---

## 7. Open questions — yours to decide

None of these is answered here. They are ordered roughly by how early they
would change the RTL.

1. **What exactly can't the host do to the counter?** The paper's counter
   *does* reset — at power-on, with a new session ID — and its integrity comes
   from that ID plus max-merging and signed logs, not from being unresettable.
   Is "the host can't reset it" the property you want, or "every reset is
   visible"? What would a verifier need to see to tell them apart?
2. **What is your FLOP?** MACs, weight loads, inferences, bytes in? Which of
   these could a dishonest host inflate or hide, and which one does the
   datapath see directly rather than being told?
3. **Meter on the path, or tap beside it?** If the meter merely *observes*,
   what stops the accelerator doing work it never sees? If it *gates* the data
   (an Interlock), what does it cost in latency, and in LEs?
4. **"The weights it ran" — hashed when, and where?** As the bytes stream in
   through the datapath, or by reading memory afterwards? What is the gap
   between "the weights that were loaded" and "the weights that were used"?
5. **Freshness.** What stops someone replaying yesterday's honest report
   today? Who supplies the challenge, and where does it enter the hash?
6. **Hash, MAC or signature?** Who verifies the report, and what must they
   hold? If the key sits in a public, auditable bitstream, what does a correct
   MAC prove?
7. **Where would a secret live on an EP4CE6** — if anywhere? If nowhere, what
   is the honest claim for a "toy Interlock", and is that still worth
   demonstrating? (The paper's Project 3 suggests yes: logic first, security
   later.)
8. **Threat model, in writing.** Host software? Someone with the USB-Blaster?
   Someone with a soldering iron? Which ones are in scope, and which are
   explicitly out?
9. **Budget split.** Of 6,272 LEs and 30 multiplier elements, how much goes to
   the accelerator and how much to the guarantees? One SHA-256 core is
   reported at 3,882 LEs on this die. What does that force?
10. **Counter width and overflow.** At your MNIST throughput, how many bits
    before it wraps, and what *should* happen when it does — wrap, saturate,
    or halt?
11. **The report's way out.** UART, the 7-segment display, JTAG? The Interlock
    idea says all I/O passes through the guarantee component. Does yours?
12. **Module boundary.** Should the meter be a separate module with a narrow,
    auditable interface? The paper's whole argument is that the guarantee part
    is small enough to audit apart from the accelerator.
13. **The test that cannot pass by accident.** What experiment would show the
    meter can't be fooled by the host — the Article IV standard, applied to
    your own claim?
14. **Two units?** Is demonstrating per-source max-merging worth a second
    board, or two logical units on one?
