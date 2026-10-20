// uart_tx -- 8N1 serial transmitter, LSB first.
//
// Contract: projects/demo/ARCHITECTURE.md, "uart_tx". Authored by Claude
// (projects/demo/ override; not Alex's work).
//
//   data   byte to send; sampled together with `start`, then free to change
//   start  sampled only while `busy` is low
//   tx     serial line, registered, idles high
//   busy   high from the cycle after an accepted `start` to the last cycle of
//          the stop bit, inclusive
//
// Timing: `start` accepted in cycle c. The start bit is on `tx` in cycles
// c+1 .. c+CLKS_PER_BIT, data bit k in the following CLKS_PER_BIT cycles, and
// the stop bit in c+1+9*CLKS_PER_BIT .. c+10*CLKS_PER_BIT. `busy` is high in
// exactly those 10*CLKS_PER_BIT cycles and low again in c+10*CLKS_PER_BIT+1,
// so a `start` held high sends back to back frames with one extra idle
// (high) cycle between them -- harmless, it only lengthens the stop bit.
//
// Requires CLKS_PER_BIT >= 2 (a 1-bit counter at minimum).
`default_nettype none

// Power-up values come from declaration initialisers (ARCHITECTURE.md
// conventions; Quartus honours them on Cyclone IV), except `tx`, which is an
// output port and needs an `initial` (see below). Verilator flags every such
// register as PROCASSINIT because it expects a reset instead; that is the
// intended design here, so only that one warning is silenced, for this module.
/* verilator lint_off PROCASSINIT */
module uart_tx #(
    parameter CLKS_PER_BIT = 434        // 50 MHz / 115,200 baud = 434.03
) (
    input  wire       clk,
    input  wire [7:0] data,
    input  wire       start,
    output reg        tx,
    output wire       busy
);

    // tx must power up HIGH (idle line). Not `output reg tx = 1'b1` in the
    // port list: Quartus 20.1 silently ignores an initialiser there, while
    // Icarus honours it. Checked on 2026-10-20 with quartus_map + quartus_fit
    // + quartus_eda: with the port initialiser the post-fit netlist had
    // tx~reg0 power_up "low" driving the pin directly, and a gate-level sim
    // showed tx=0 when idle (a break on the RS-232 line that corrupts the first reply).
    // With this initial block, Quartus inverts tx~reg0 and the pin idles at 1.
    // Quartus treats a constant `initial` like a declaration initialiser.
    initial tx = 1'b1;

    // Counter wide enough for 0 .. CLKS_PER_BIT-1.
    localparam CW = $clog2(CLKS_PER_BIT);
    localparam integer LAST_I = CLKS_PER_BIT - 1;
    localparam [CW-1:0] LAST = LAST_I[CW-1:0];

    reg          busy_r = 1'b0;
    reg [CW-1:0] cnt    = {CW{1'b0}};   // cycles elapsed in the current bit
    // Bits still to put on the line after the one now on `tx`: data[0..7]
    // then the stop bit. Shifting the frame out of a register (rather than
    // indexing `data`) is what lets `data` change while busy.
    reg [8:0]    shreg  = 9'h1FF;
    reg [3:0]    left   = 4'd0;         // 9 after the start bit, 0 during stop

    assign busy = busy_r;

    always @(posedge clk) begin
        if (!busy_r) begin
            if (start) begin
                tx     <= 1'b0;         // start bit
                shreg  <= {1'b1, data}; // stop bit sits above data[7]
                left   <= 4'd9;
                cnt    <= {CW{1'b0}};
                busy_r <= 1'b1;
            end
        end else if (cnt != LAST) begin
            cnt <= cnt + 1'b1;
        end else begin
            cnt <= {CW{1'b0}};
            if (left != 4'd0) begin
                tx    <= shreg[0];
                // Shift ones in: once the stop bit is out, tx stays high.
                shreg <= {1'b1, shreg[8:1]};
                left  <= left - 1'b1;
            end else begin
                // Last cycle of the stop bit has just ended; tx is already 1.
                busy_r <= 1'b0;
            end
        end
    end

endmodule
/* verilator lint_on PROCASSINIT */

`default_nettype wire
