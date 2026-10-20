# demo — architecture contract

Authored by Claude (see `README.md`). This file is the contract every module is built
and tested against. Port names, widths and cycle timing are exact. If a module cannot
meet them, change this file first, then every module it touches.

## System

```
Mac app ──RS-232──▶ uart_rx ─▶ frame_rx ─▶ image_buf ─┐
 (host/draw.py)                                       ├─ mux(layer) ─▶ mac ─▶ post ─▶ hidden_buf ─┘(back to mux)
                         weight_rom ─────────────────▶┘               │  ▲
                         bias_rom  ─────────────────────── (load) ────┘  │
                                                         layer 2: acc ─▶ argmax + result_tx ─▶ uart_tx ──RS-232──▶ Mac
                                                                          └▶ digit latch ─▶ seg7
controller: one FSM, drives every address and every mac/post/argmax/result_tx strobe.
```

Network: 784 → 16 (ReLU, requantise) → 10, from `projects/mnist/model/export/` via
`host/make_mem.py`. 4-bit signed weights, 8-bit unsigned pixels, 8-bit unsigned hidden
values (0..127), 24-bit biases.

## Conventions (every RTL file)

- One module per file, file name = module name, in `rtl/`.
- First line of code `` `default_nettype none ``, last line `` `default_nettype wire ``.
- Verilog-2001/2005 only (Quartus Prime Lite 20.1; Icarus `-g2012`). No SystemVerilog.
- One clock, `clk`, 50 MHz, everything `posedge clk`. No derived clocks, no latches.
- Power-up values come from declaration initialisers (`reg x = 0;`), which Quartus
  honours on Cyclone IV. `rst` (active high, synchronous, already synchronised by
  `demo_top`) only where a port lists it.
- Memories with "1-cycle read" register their output: address presented in cycle c,
  data valid during cycle c+1.
- `$readmemh` paths are relative to `projects/demo/` (Quartus and `sim.sh` both run
  there).

## Numeric bounds (why the widths are enough)

- Layer-1 accumulator: |acc| ≤ 784 × 255 × 7 + 1,228 = 1,400,668 < 2²¹ → 24-bit signed.
- After ReLU, acc < 2²³; × QM (< 2²⁴) < 2⁴⁷ → 48-bit product is exact.
- Layer-2 score: |s| ≤ 16 × 127 × 7 + 19 = 14,243 < 2¹⁵ → `acc[15:0]` is exact.
- The constants 1,228 and 19 are the current export's largest |b1| and |b2|. They are not
  enforced here: `host/make_mem.py` computes the exact per-neuron worst case
  (bias + Σ min/max(w, 0) × 255 for layer 1, × QMAX for layer 2) and refuses an export
  that does not fit 24 / 16 bits, before writing anything. Current snapshot: layer-1
  −116,038..149,875, score −3,671..3,056.

## Modules and ports

### `uart_rx #(parameter CLKS_PER_BIT = 434)`
`input clk, input rx, output reg [7:0] data, output reg valid`
8N1, LSB first. `rx` through a 2-FF synchroniser. Start bit re-checked at its middle
(still low or ignored); bits sampled mid-period; byte delivered only if stop bit is high.
`valid` is a one-cycle pulse; `data` holds until the next byte.

### `uart_tx #(parameter CLKS_PER_BIT = 434)`
`input clk, input [7:0] data, input start, output reg tx, output busy`
8N1, LSB first, `tx` idles high and is a registered output. `start` is sampled only when
`busy` is low; `busy` is high from the cycle after `start` until the end of the stop bit.

### `frame_rx #(parameter N = 784, parameter TIMEOUT = 2500000)`
`input clk, input rst, input enable, input [7:0] rx_data, input rx_valid,`
`output reg wr_en, output reg [9:0] wr_addr, output reg [7:0] wr_data, output reg done, output receiving`
States HUNT1 → HUNT2 → DATA. In HUNT1 a byte `0xA5` while `enable` is high moves to
HUNT2. In HUNT2: `0x5A` → DATA (next address 0); `0xA5` stays in HUNT2; anything else →
HUNT1. In DATA every `rx_valid` byte produces one registered write (`wr_en` high for one
cycle, the cycle after `rx_valid`) to addresses 0, 1, … N−1. `done` pulses for one cycle,
the cycle after the final `wr_en`, then back to HUNT1. If in HUNT2 or DATA and no
`rx_valid` arrives for TIMEOUT cycles, return to HUNT1 (a half-received frame never
starts an inference). `receiving` = state is DATA. `rst` → HUNT1.

### `image_buf`
`input clk, input we, input [9:0] waddr, input [7:0] wdata, input [9:0] raddr, output reg [7:0] rdata`
784 × 8, simple dual-port, 1-cycle read. Must infer M9K.

### `weight_rom #(parameter DEPTH = 12704, parameter INIT = "mem/weights.hex")`
`input clk, input [13:0] addr, output reg signed [3:0] q`
1-cycle read, contents from `$readmemh(INIT)`. Address = 12,544 × layer + neuron ×
n_inputs + input, so one counter walks every weight of both layers in order. Must infer
M9K.

### `bias_rom #(parameter INIT = "mem/bias.hex")`
`input clk, input [4:0] addr, output reg signed [23:0] q`
26 words: b1[0..15] at 0..15, b2[0..9] at 16..25. 1-cycle read.

### `hidden_buf`
`input clk, input we, input [3:0] waddr, input [7:0] wdata, input [3:0] raddr, output reg [7:0] rdata`
16 × 8, 1-cycle registered read (same latency as `image_buf`, so the mux needs no
alignment).

### `mac`
`input clk, input load, input signed [23:0] load_val, input en, input signed [3:0] w, input [7:0] x, output reg signed [23:0] acc`
`load` (priority): `acc <= load_val`. Else `en`: `acc <= acc + w × x`, with `x`
**unsigned** (0..255) and `w` signed, so the product is 13-bit signed. Else hold.

### `post`
`input clk, input start, input signed [23:0] acc, output reg [7:0] h, output reg done`
`` `include "quant_params.vh" `` (QM, QSHIFT, QMAX; generated). Samples `acc` in the
cycle `start` is high; `done` is high for exactly one cycle, three cycles later; `h` is
valid in that cycle and held after.
`h = min((max(acc, 0) × QM + 2^(QSHIFT−1)) >> QSHIFT, QMAX)`, exactly as `host/golden.py`.
Pipeline: register ReLU'd acc → register product → register clamped result.

### `argmax`
`input clk, input clear, input en, input [3:0] idx, input signed [15:0] score, output reg [3:0] best_idx`
`clear` forgets everything. The first `en` after `clear` is always taken; later ones only
if `score` is **strictly** greater (ties keep the lower index, like `np.argmax`).

### `result_tx`
`input clk, input rst, input we, input [3:0] widx, input signed [15:0] wscore, input send, input [3:0] digit,`
`input tx_busy, output reg tx_start, output reg [7:0] tx_data, output busy`
Stores 10 scores (`we` writes `wscore` at `widx`). `send` (when not busy) latches `digit`
and transmits 22 bytes through `uart_tx`: `0xC3`, `digit`, then for k = 0..9 the score's
low byte then high byte (two's complement). One byte at a time: pulse `tx_start` with
`tx_data` stable, wait for `tx_busy` to rise, then fall. `busy` is high from the cycle
after `send` until the last byte's stop bit has finished.

### `seg7`
`input [3:0] digit, input valid, output reg [7:0] seg_n, output [3:0] dig_n`
Combinational. Active low. `seg_n[0..6]` = segments a..g, `seg_n[7]` = dp (vendor
`sled.v` example: "0" = 8'hC0). 0:C0 1:F9 2:A4 3:B0 4:99 5:92 6:82 7:F8 8:80 9:90;
`!valid` → 8'hBF (a single dash). `dig_n = 4'b0000`: all four digits show the same
character, so digit order does not matter.

### `controller`
Inputs: `clk, rst, start, post_done, tx_busy` (`tx_busy` = `result_tx.busy`)
Outputs: `frame_enable, busy, layer, [9:0] x_raddr, [13:0] w_addr, [4:0] b_addr,
mac_load, mac_en, post_start, [3:0] j, sc_we, am_clear, am_en, send`

`j` is the current neuron (hidden 0..15 in layer 0, output 0..9 in layer 1). `i` counts
inputs (0..783 / 0..15). FSM:

| State | Does | Next |
|---|---|---|
| IDLE | `frame_enable`=1. On `start`: layer←0, j←0, w_addr←0, `am_clear`=1 | BIAS |
| BIAS | `b_addr` = layer ? 16+j : j (combinational, so the ROM output is valid next cycle) | LOAD |
| LOAD | `mac_load`=1 (acc ← bias); i←0 | RUN |
| RUN  | present `x_raddr`=i, `w_addr`; i++, w_addr++; leave after i = N−1 | DRAIN |
| DRAIN | last product accumulates this cycle | POST |
| POST | layer 0: `post_start`=1 → PWAIT. layer 1: `sc_we`=`am_en`=1 → NEXT | |
| PWAIT | wait `post_done` (top writes `post.h` to `hidden_buf[j]` on `post_done`) | NEXT |
| NEXT | last j? layer 0 → layer←1, j←0 → BIAS; layer 1 → SEND. Else j++ → BIAS | |
| SEND | `send`=1 | TXWAIT |
| TXWAIT | wait until `tx_busy` is low (it is high from the cycle after SEND) | IDLE |

`mac_en` is `(state == RUN)` delayed one cycle by a register, to match the 1-cycle
memory read. `busy` = state ≠ IDLE. `rst` → IDLE. N = 784 in layer 0, 16 in layer 1.
`w_addr` is never reset between layers: it reaches 12,544 exactly when layer 1 starts.

### `demo_top #(parameter CLKS_PER_BIT = 434, parameter TIMEOUT = 2500000)`
Ports (these are the `.qsf` pin names): `input clk, input rst_n, input uart_rx,`
`output uart_tx, output [3:0] led_n, output [7:0] seg_n, output [3:0] dig_n`.
Wiring only, plus: `rst_n` 2-FF synchronised → `rst`; x mux `x = layer ? hid_q : img_q`;
`hidden_buf.we = post_done`, `.waddr = j`, `.wdata = post.h`, `.raddr = x_raddr[3:0]`;
`result_tx.we = sc_we`, `.widx = j`, `.wscore = acc[15:0]`; `argmax.en = am_en`,
`.idx = j`, `.score = acc[15:0]`; on `send` latch `argmax.best_idx` into the displayed
digit and set `result_valid` (cleared by `rst`).
LEDs (active low): `led_n[0]` = ~receiving, `led_n[1]` = ~busy, `led_n[2]` =
~result_valid, `led_n[3]` = ~heartbeat (bit 24 of a free-running counter, ~1.5 Hz: proves
the clock runs). The heartbeat alone does not prove a load: the flash's `blink` also
toggles PIN_87. The load check is the power-up pattern only this design produces: a dash
on all four digits, LED1-LED3 dark, LED4 blinking (README step 3).

## Pins (OMDAZZ V3.0; vendor pin PDF and example `.qsf`)

| Port | Pin(s) |
|---|---|
| clk | 23 |
| rst_n | 25 |
| uart_rx | 115 (UART_RXD) |
| uart_tx | 114 (UART_TXD) |
| led_n[0..3] | 84, 85, 86, 87 |
| seg_n[0..7] | 128, 121, 125, 129, 132, 126, 124, 127 (SEG0..SEG7) |
| dig_n[0..3] | 133, 135, 136, 137 (DIG1..DIG4) |

All `3.3-V LVTTL`. The `.qsf` carries no trailing `; #` comments and ends with a newline.

## Host protocol (115,200 baud, 8N1, through the board's MAX3232: needs a USB-to-RS-232 adapter)

The board's DB9 is DCE (transmits on pin 2): a straight-through cable, not null-modem.

- Mac → FPGA: `0xA5 0x5A` then 784 pixel bytes, row-major, 0 = background, 255 = ink
  (MNIST convention).
- FPGA → Mac: 22 bytes: `0xC3`, digit (0..9), then 10 × int16 little-endian scores.
- The Mac waits for the reply (or a 2 s timeout) before sending another frame. The host
  checks the scores against `host/golden.py` bit for bit; a match is the hardware test.

## Verification

- `./sim.sh demo` runs every `tb/*.v`. Each prints exactly `PASS` or `FAIL`.
- `tb/tb_demo.v` is end to end: the 16 test images over the UART pins (small
  CLKS_PER_BIT), 22-byte replies compared against `mem/expected.hex` (digit + all 10
  scores per image).
- Every testbench is proven able to fail by breaking its module on purpose in a scratch
  copy (never in `projects/demo/`).
