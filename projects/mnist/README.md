# mnist — the main design

Recognise a handwritten digit on the EP4CE6:

```
Mac  ──image──▶  FPGA runs the network  ──digit──▶  answer comes back
```

**Status:** no RTL yet. The project shell exists: `mnist.qpf`, `mnist.sdc` (50 MHz on
`clk`) and `mnist.qsf` (device and globals; top-level entity `top`; the RTL file list
and the pin block are empty, to be filled as modules and `top`'s ports exist).

```
mnist.qpf  mnist.qsf  mnist.sdc
rtl/        one module per file, named after the module   (Alex)
tb/         self-checking testbenches, run by ./sim.sh    (Alex)
model/      training notebook and the integer export (export/*.hex)
```

## Open decisions

These are Alex's to make (CLAUDE.md, Article I). Each one changes what gets built. When
one is settled, write the choice **and the reason** here, and log it in
`docs/PROGRESS.md`.

- [ ] **How the image gets in.** It has to be something the board can *receive*.
  Board facts, from `resources/…/Hardware documentation/Development board pin
  information.pdf` and the V2.1 schematic:
  - The VGA connector is **output only**: FPGA to monitor. HSYNC, VSYNC and one bit each
    of R, G, B (PIN_101, 103, 104, 105, 106) through resistors. Nothing on the board
    can sample an incoming video signal.
  - The serial port is UART_TXD PIN_114 / UART_RXD PIN_115 through a **MAX3232** to an
    RS-232 connector. A Mac needs a USB-to-RS-232 adapter for it, not a 3.3 V TTL one.
  - Other inputs on the board: PS/2 (PIN_119/120), the keys, and JTAG through the
    USB-Blaster that is already plugged in.
- [ ] **How the answer comes out.** Over the same link, on the seven-segment display,
  on the LEDs, on a VGA monitor, or a combination.
- [ ] **The network.** Layers and their sizes. The input is 28 × 28.
- [ ] **Number format.** Width and scaling of weights, activations and accumulators.
- [ ] **Where the weights live.** On-chip M9K, or the board's external SDRAM, which
  needs a controller.
- [ ] **How much runs in parallel.** How many multiply-accumulates happen per clock.

## Budget

From CLAUDE.md, Article V. Resource numbers in `docs/PROGRESS.md` come from the fitter
report, never from estimates.

| Resource | EP4CE6 has |
|---|---|
| Logic elements | 6,272 |
| Registers | 6,272 |
| M9K memory bits | 276,480 |
| 9-bit multiplier elements | 30 (= 15 × 18×18) |
| Usable I/O pins | 92 |
