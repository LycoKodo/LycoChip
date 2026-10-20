// frame_rx -- finds the 0xA5 0x5A sync, then writes N bytes to image_buf.
//
// Contract: projects/demo/ARCHITECTURE.md, "frame_rx". Authored by Claude
// (projects/demo/ override; not Alex's work).
//
//   enable     gates only the start of a frame (HUNT1 seeing 0xA5). Once the
//              sync has been seen the frame is taken to the end regardless.
//   wr_en      one-cycle pulse, the cycle after the rx_valid it stores
//   wr_addr    0, 1, ... N-1 within a frame; held between writes
//   wr_data    the byte that rx_valid carried; held between writes
//   done       one-cycle pulse, the cycle after the final wr_en
//   receiving  state == DATA
//
// Timing of the last byte (rx_valid in cycle c):
//   c+1  wr_en (address N-1); the state is already HUNT1, so `receiving` is
//        low from here on and a new 0xA5 is accepted in this very cycle
//   c+2  done
// Leaving DATA on the last byte (instead of waiting for done) is why `done`
// needs its own one-cycle delay register, `finishing`.
//
// Timeout: in HUNT2 or DATA, a cycle with no rx_valid counts as idle. After
// rx_valid in cycle c, if cycles c+1 .. c+TIMEOUT are all idle, the state is
// HUNT1 from cycle c+TIMEOUT+1. A byte in cycle c+TIMEOUT is still accepted.
// The default (2,500,000 cycles = 50 ms at 50 MHz) is ~230 byte times at
// 115,200 baud: far longer than any gap inside a frame sent by the host, far
// shorter than the host's 2 s reply timeout.
//
// N must be at most 1024 (wr_addr is 10 bits).
`default_nettype none

// Power-up values come from declaration initialisers (ARCHITECTURE.md
// conventions; Quartus honours them on Cyclone IV). Verilator flags every such
// register as PROCASSINIT because it expects a reset instead; that is the
// intended design here, so only that one warning is silenced.
/* verilator lint_off PROCASSINIT */
module frame_rx #(
    parameter N       = 784,
    parameter TIMEOUT = 2500000
) (
    input  wire       clk,
    input  wire       rst,
    input  wire       enable,
    input  wire [7:0] rx_data,
    input  wire       rx_valid,
    output reg        wr_en,
    output reg  [9:0] wr_addr,
    output reg  [7:0] wr_data,
    output reg        done,
    output wire       receiving
);

    // Power-up values of output ports. Not in the port list: Quartus 20.1
    // silently ignores an initialiser there (see uart_tx.v).
    initial wr_en   = 1'b0;
    initial wr_addr = 10'd0;
    initial wr_data = 8'h00;
    initial done    = 1'b0;

    localparam [1:0] HUNT1 = 2'd0,      // waiting for 0xA5
                     HUNT2 = 2'd1,      // seen 0xA5, waiting for 0x5A
                     DATA  = 2'd2;      // storing pixel bytes

    // Idle counter: counts 0 .. TIMEOUT-1, so it needs ceil(log2(TIMEOUT))
    // bits; +1 keeps TIMEOUT = 1 (and exact powers of two) at a legal width.
    localparam TW = $clog2(TIMEOUT + 1);
    // Slicing before subtracting keeps the arithmetic at the target width
    // (TIMEOUT always fits in TW bits), so no truncation is left to lint.
    localparam [TW-1:0] IDLE_LAST = TIMEOUT[TW-1:0] - 1'b1;
    localparam [9:0]    ADDR_LAST = N[9:0] - 1'b1;

    reg [1:0]    state     = HUNT1;
    reg [9:0]    count     = 10'd0;     // address of the next byte in DATA
    reg [TW-1:0] idle      = {TW{1'b0}};
    reg          finishing = 1'b0;      // the final wr_en is out; done follows

    assign receiving = (state == DATA);

    wire timed_out = (idle == IDLE_LAST);

    always @(posedge clk) begin
        // Defaults: both strobes are single-cycle pulses.
        wr_en     <= 1'b0;
        finishing <= 1'b0;
        done      <= finishing;

        if (rst) begin
            // Abandon everything, including a done still in flight: after a
            // reset nothing may start an inference.
            state <= HUNT1;
            idle  <= {TW{1'b0}};
            done  <= 1'b0;
        end else begin
            // The timer only runs while a frame is in progress, and any byte
            // restarts it. Entering HUNT2 needs a byte, so it starts at 0.
            if (state == HUNT1 || rx_valid)
                idle <= {TW{1'b0}};
            else
                idle <= idle + 1'b1;

            case (state)
                HUNT1:
                    if (rx_valid && enable && rx_data == 8'hA5)
                        state <= HUNT2;

                HUNT2:
                    if (rx_valid) begin
                        if (rx_data == 8'h5A) begin
                            state <= DATA;
                            count <= 10'd0;
                        end else if (rx_data != 8'hA5) begin
                            // A5 A5 5A must still sync, so a repeated A5
                            // stays here; anything else starts the hunt over.
                            state <= HUNT1;
                        end
                    end else if (timed_out) begin
                        state <= HUNT1;
                    end

                DATA:
                    if (rx_valid) begin
                        wr_en   <= 1'b1;
                        wr_addr <= count;
                        wr_data <= rx_data;
                        count   <= count + 1'b1;
                        if (count == ADDR_LAST) begin
                            state     <= HUNT1;
                            finishing <= 1'b1;
                        end
                    end else if (timed_out) begin
                        // Half a frame never reaches done, so it never starts
                        // an inference; the next frame overwrites from 0.
                        state <= HUNT1;
                    end

                default:
                    state <= HUNT1;
            endcase
        end
    end

endmodule
/* verilator lint_on PROCASSINIT */
`default_nettype wire
