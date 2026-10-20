// result_tx -- holds the 10 layer-2 scores and sends the 22-byte result
// message through uart_tx.
//
// Contract: projects/demo/ARCHITECTURE.md, "result_tx". Authored by Claude
// (projects/demo/ override; not Alex's work).
//
//   we/widx/wscore  store wscore as score[widx]; widx 10..15 is ignored (there
//                   are only 10 slots, and aliasing would corrupt a real one)
//   send            accepted only while `busy` is low; latches `digit`
//   tx_start        one-cycle pulse to uart_tx, with tx_data valid in the
//                   same cycle
//   tx_busy         uart_tx.busy
//   busy            high from the cycle after an accepted `send` until the
//                   last byte has left the wire
//
// Message: 0xC3, digit, then score[0] lo, score[0] hi, ... score[9] hi
// (int16 little endian, two's complement).
//
// Handshake, per byte:
//   GAP   wait until tx_busy is low, then raise tx_start with tx_data
//   WHI   tx_start back low; wait for tx_busy to rise (uart_tx raises it the
//         cycle after it accepts start)
//   WLO   wait for tx_busy to fall: the stop bit has finished
// GAP checks tx_busy before every byte, including the first. That costs one
// cycle per byte, and it means a `send` right after `rst` cannot lose its
// first byte to a uart_tx still finishing the byte `rst` interrupted.
//
// Timing with a uart_tx whose busy lasts B cycles: a byte every B+3 cycles.
// `busy` falls one cycle after tx_busy falls for the 22nd byte (the first
// cycle the FSM can have seen it low).
//
// rst aborts a message: back to IDLE, tx_start low. A byte uart_tx already
// accepted still goes out. Scores are not cleared (the controller rewrites
// all 10 before every `send`).
`default_nettype none

// Power-up values come from declaration initialisers (ARCHITECTURE.md
// conventions; Quartus honours them on Cyclone IV). Verilator flags those
// registers as PROCASSINIT; that is the intended design, so only that one
// warning is silenced, for this module.
/* verilator lint_off PROCASSINIT */
module result_tx (
    input  wire               clk,
    input  wire               rst,
    input  wire               we,
    input  wire         [3:0] widx,
    input  wire signed [15:0] wscore,
    input  wire               send,
    input  wire         [3:0] digit,
    input  wire               tx_busy,
    output reg                tx_start,
    output reg          [7:0] tx_data,
    output wire               busy
);

    // Power-up values of output ports. Not in the port list: Quartus 20.1
    // silently ignores an initialiser there (see uart_tx.v).
    initial tx_start = 1'b0;
    initial tx_data  = 8'h00;

    localparam [1:0] S_IDLE = 2'd0,
                     S_GAP  = 2'd1,
                     S_WHI  = 2'd2,
                     S_WLO  = 2'd3;

    localparam [7:0] SYNC      = 8'hC3;
    localparam [4:0] LAST_BYTE = 5'd21;     // bytes 0..21

    // 10 x 16 bits. Small enough for registers, and the byte mux below reads
    // it without a clock, which an M9K could not do. Declared 16 deep, the
    // full range of the 4-bit index: declared [0:9], Quartus sizes it by the
    // index anyway and raises Critical Warning 127005 (16 vs 10 words) on the
    // initial block below (first synthesis, 2026-10-20). Slots 10..15 are
    // never written (see the write guard) and stay 0.
    reg [15:0] score [0:15];

    // Power-up value 0 for every slot. Verilog-2001 has no array initialiser,
    // so this is the one initial block; Quartus turns it into register
    // power-up values. Without it a `send` before any write sends X in
    // Icarus, and on the part whatever "Power-Up Don't Care" picked.
    integer s;
    initial
        for (s = 0; s < 16; s = s + 1)
            score[s] = 16'd0;

    reg [1:0] state   = S_IDLE;
    reg [4:0] n       = 5'd0;               // index of the byte being sent
    reg [3:0] digit_l = 4'd0;

    assign busy = (state != S_IDLE);

    always @(posedge clk)
        if (we && widx < 4'd10)
            score[widx] <= wscore;

    // Byte n of the message. For n >= 2, m = n - 2 counts score bytes:
    // m[4:1] is the score, m[0] picks high (1) or low (0) byte. For n = 0, 1
    // m wraps and the score read is meaningless, but it is not selected.
    wire [4:0]  m  = n - 5'd2;
    wire [15:0] sc = score[m[4:1]];
    reg  [7:0]  byte_n;
    always @(*) begin
        if (n == 5'd0)      byte_n = SYNC;
        else if (n == 5'd1) byte_n = {4'd0, digit_l};
        else                byte_n = m[0] ? sc[15:8] : sc[7:0];
    end

    always @(posedge clk) begin
        if (rst) begin
            state    <= S_IDLE;
            tx_start <= 1'b0;
            n        <= 5'd0;
        end else begin
            case (state)
                S_IDLE:
                    if (send) begin
                        digit_l <= digit;
                        n       <= 5'd0;
                        state   <= S_GAP;
                    end
                S_GAP:
                    if (!tx_busy) begin
                        tx_start <= 1'b1;
                        tx_data  <= byte_n;
                        state    <= S_WHI;
                    end
                S_WHI: begin
                    tx_start <= 1'b0;
                    if (tx_busy) state <= S_WLO;
                end
                S_WLO:
                    if (!tx_busy) begin
                        if (n == LAST_BYTE) begin
                            state <= S_IDLE;
                        end else begin
                            n     <= n + 5'd1;
                            state <= S_GAP;
                        end
                    end
            endcase
        end
    end

endmodule
/* verilator lint_on PROCASSINIT */

`default_nettype wire
