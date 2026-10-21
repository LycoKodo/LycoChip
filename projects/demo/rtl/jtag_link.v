// jtag_link -- frames in and replies out over the USB-Blaster, for a host with
// no RS-232 port.
//
// Contract: projects/demo/ARCHITECTURE.md, "jtag_link". Authored by Claude
// (projects/demo/ override; not Alex's work).
//
// Two virtual instructions, shifted by host/jtag_bridge.py through vjtag:
//
//   IR = 1  WRITE  every 8 bits shifted into DR (LSB first) become one byte,
//                  handed to frame_rx exactly as uart_rx would hand it over.
//                  The bit count restarts at Capture-DR, so a partial byte at
//                  the end of a scan is dropped. A whole frame (A5 5A + 784
//                  pixels = 6,288 bits) goes in one scan.
//   IR = 2  READ   Capture-DR loads {reply[21], ..., reply[0], 3'b0, count}:
//                  how many reply bytes have been captured (0..22), then the
//                  bytes, all shifted out LSB first.
//
// The reply is tapped from result_tx's tx_start / tx_data, i.e. the same bytes
// uart_tx sends, so both links carry an identical reply. Every byte arriving
// over JTAG clears count, so after sending a frame the host polls READ until
// count is 22.
//
// Clock crossing. tck (from the cable) and clk are unrelated.
//   tck -> clk  a finished byte is held in wbyte and announced by flipping
//               wtoggle. clk sees the flip through two flip-flops and only
//               then copies wbyte, which by that time has been stable for at
//               least two clk cycles and does not change for 8 more tck
//               cycles (works for any tck below ~130 MHz).
//   clk -> tck  the READ capture copies count and reply unsynchronised. They
//               change once per byte of a reply, ~87 us apart, and count goes
//               up the cycle after its byte is stored; the host reads twice
//               and requires both reads to agree.
`default_nettype none

/* verilator lint_off PROCASSINIT */
module jtag_link (
    input  wire       clk,
    output reg  [7:0] rx_data,
    output reg        rx_valid,
    input  wire       tx_start,
    input  wire [7:0] tx_data,
    input  wire       tck,
    input  wire       tdi,
    output wire       tdo,
    input  wire [1:0] ir_in,
    input  wire       cdr,
    input  wire       sdr
);

    // Power-up values of output ports. Not in the port list: Quartus 20.1
    // silently ignores an initialiser there (see uart_tx.v).
    initial rx_data  = 8'h00;
    initial rx_valid = 1'b0;

    localparam [1:0] IR_WRITE = 2'd1,
                     IR_READ  = 2'd2;
    localparam       N_REPLY  = 22;

    // ---- clk domain: the captured reply -------------------------------------
    reg [8*N_REPLY-1:0] reply = {8*N_REPLY{1'b0}};
    reg           [4:0] count = 5'd0;
    reg                 bump  = 1'b0;

    // ---- tck domain -------------------------------------------------------------
    reg        [2:0] bitcnt  = 3'd0;
    reg        [6:0] wsr     = 7'd0;    // the first 7 bits of the byte in flight
    reg        [7:0] wbyte   = 8'h00;
    reg              wtoggle = 1'b0;
    reg [8*N_REPLY+7:0] rsr  = {(8*N_REPLY+8){1'b0}};

    always @(posedge tck) begin
        if (cdr) begin
            bitcnt <= 3'd0;
            rsr    <= {reply, 3'b000, count};
        end else if (sdr) begin
            if (ir_in == IR_WRITE) begin
                wsr    <= {tdi, wsr[6:1]};
                bitcnt <= bitcnt + 3'd1;
                if (bitcnt == 3'd7) begin
                    wbyte   <= {tdi, wsr};
                    wtoggle <= ~wtoggle;
                end
            end
            if (ir_in == IR_READ)
                rsr <= {tdi, rsr[8*N_REPLY+7:1]};
        end
    end

    assign tdo = rsr[0];

    // ---- tck -> clk: one rx_valid per finished byte ---------------------------
    reg  [2:0] wsync = 3'd0;
    wire       wnew  = wsync[2] ^ wsync[1];

    always @(posedge clk) begin
        wsync    <= {wsync[1:0], wtoggle};
        rx_valid <= wnew;
        if (wnew)
            rx_data <= wbyte;
    end

    // ---- reply capture ------------------------------------------------------------
    always @(posedge clk) begin
        bump <= 1'b0;
        if (rx_valid) begin
            count <= 5'd0;
        end else if (bump) begin
            count <= count + 5'd1;
        end else if (tx_start && count < N_REPLY) begin
            reply[count*8 +: 8] <= tx_data;
            bump <= 1'b1;
        end
    end

endmodule
/* verilator lint_on PROCASSINIT */

`default_nettype wire
