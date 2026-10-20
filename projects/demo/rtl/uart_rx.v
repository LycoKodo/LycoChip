// uart_rx -- 8N1 serial receiver, LSB first.
//
// Contract: projects/demo/ARCHITECTURE.md, "uart_rx". Authored by Claude
// (projects/demo/ override; not Alex's work).
//
//   rx     asynchronous serial line, idles high
//   data   last good byte; changes only in the cycle `valid` is high, then holds
//   valid  one-cycle pulse per byte whose stop bit was high
//
// Timing: the falling edge of the start bit is seen (after the 2-FF
// synchroniser) at some cycle t0. The start bit is re-checked HALF cycles
// later, i.e. near its middle; every following sample is exactly
// CLKS_PER_BIT cycles after the previous one, so each data bit and the stop
// bit are sampled near their middles too. `valid` rises the cycle after the
// stop-bit sample: about 9.5 bit periods after the start edge, i.e. before the
// stop bit has ended, so back-to-back bytes are never missed.
`default_nettype none

// Power-up values come from declaration initialisers (ARCHITECTURE.md
// conventions; Quartus honours them on Cyclone IV). Verilator flags every such
// register as PROCASSINIT because it expects a reset instead; that is the
// intended design here, so only that one warning is silenced.
/* verilator lint_off PROCASSINIT */
module uart_rx #(
    parameter CLKS_PER_BIT = 434        // 50 MHz / 115,200 baud = 434.03
) (
    input  wire       clk,
    input  wire       rx,
    output reg  [7:0] data,
    output reg        valid
);

    // Power-up values of output ports. Not in the port list: Quartus 20.1
    // silently ignores an initialiser there (see uart_tx.v).
    initial data  = 8'h00;
    initial valid = 1'b0;

    // Counter wide enough for 0 .. CLKS_PER_BIT-1.
    localparam CW = $clog2(CLKS_PER_BIT);
    // Comparison constants as CW-bit values, so the compares are width-exact.
    localparam integer LAST_I = CLKS_PER_BIT - 1;        // one full bit period
    localparam integer HALF_I = (CLKS_PER_BIT - 1) / 2;  // to the middle of the start bit
    localparam [CW-1:0] LAST = LAST_I[CW-1:0];
    localparam [CW-1:0] HALF = HALF_I[CW-1:0];

    localparam [2:0] S_IDLE  = 3'd0,    // line high, waiting for a falling edge
                     S_START = 3'd1,    // counting to the middle of the start bit
                     S_DATA  = 3'd2,    // sampling the 8 data bits
                     S_STOP  = 3'd3,    // sampling the stop bit
                     S_BREAK = 3'd4;    // stop bit was low: wait for the line to go high

    // 2-FF synchroniser. Initialised high (the idle level) so power-up is not
    // mistaken for a start bit.
    reg rx_meta = 1'b1;
    reg rx_s    = 1'b1;
    always @(posedge clk) begin
        rx_meta <= rx;
        rx_s    <= rx_meta;
    end

    reg [2:0]    state = S_IDLE;
    reg [CW-1:0] cnt   = {CW{1'b0}};
    reg [2:0]    nbit  = 3'd0;          // index of the data bit being sampled
    reg [7:0]    shift = 8'h00;

    always @(posedge clk) begin
        valid <= 1'b0;                  // a pulse: high only where set below

        case (state)
            S_IDLE: begin
                cnt <= {CW{1'b0}};
                if (!rx_s)
                    state <= S_START;
            end

            S_START: begin
                if (cnt == HALF) begin
                    cnt <= {CW{1'b0}};
                    nbit <= 3'd0;
                    // A low pulse shorter than half a bit is noise, not a start bit.
                    state <= rx_s ? S_IDLE : S_DATA;
                end else
                    cnt <= cnt + 1'b1;
            end

            S_DATA: begin
                if (cnt == LAST) begin
                    cnt   <= {CW{1'b0}};
                    shift <= {rx_s, shift[7:1]};    // LSB arrives first
                    if (nbit == 3'd7)
                        state <= S_STOP;
                    else
                        nbit <= nbit + 1'b1;
                end else
                    cnt <= cnt + 1'b1;
            end

            S_STOP: begin
                if (cnt == LAST) begin
                    cnt <= {CW{1'b0}};
                    if (rx_s) begin
                        data  <= shift;
                        valid <= 1'b1;
                        // Back to IDLE at mid-stop-bit: the line is high here,
                        // so the next start edge is caught as soon as it comes.
                        state <= S_IDLE;
                    end else
                        // Framing error: drop the byte. Going straight to IDLE
                        // would treat the rest of this low stop bit as a new
                        // start bit, so wait for the line to recover first.
                        state <= S_BREAK;
                end else
                    cnt <= cnt + 1'b1;
            end

            S_BREAK: begin
                cnt <= {CW{1'b0}};
                if (rx_s)
                    state <= S_IDLE;
            end

            default: state <= S_IDLE;
        endcase
    end

endmodule
/* verilator lint_on PROCASSINIT */

`default_nettype wire
