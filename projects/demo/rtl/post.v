// post.v -- layer-1 post-processing: ReLU, requantise, clamp.
//
// Authored by Claude for projects/demo/ (see README.md: Article I override,
// this directory only). Contract: ARCHITECTURE.md, section `post`.
//
//   h = min((max(acc, 0) * QM + 2^(QSHIFT-1)) >> QSHIFT, QMAX)
//
// exactly as host/golden.py. Three register stages, fully pipelined:
//
//   cycle c   : start high, acc sampled      -> relu_q  (end of c)
//   cycle c+1 :                                -> prod_q  (end of c+1)
//   cycle c+2 :                                -> h, done (end of c+2)
//   cycle c+3 : done high for one cycle, h valid; h then held until the next result
//
// A new start may arrive every cycle; each produces its own done three cycles later.
//
// Power-up values come from declaration initialisers (ARCHITECTURE.md conventions;
// this port has no rst). Verilator flags initialiser + procedural write as
// PROCASSINIT because it expects a reset instead; that is the intended style here.
`default_nettype none

/* verilator lint_off PROCASSINIT */
module post (
    input  wire               clk,
    input  wire               start,
    input  wire signed [23:0] acc,
    output reg         [7:0]  h,
    output reg                done
);

    // Power-up values of output ports. Not in the port list: Quartus 20.1
    // silently ignores an initialiser there (see uart_tx.v).
    initial h    = 8'd0;
    initial done = 1'b0;
    `include "quant_params.vh"

    // After ReLU the value is 0 .. 2^23-1, so 23 unsigned bits hold it exactly.
    // 23 x 24 bits < 2^47, and adding the rounding half (2^31) stays < 2^48,
    // so a 48-bit sum is exact (ARCHITECTURE.md, "Numeric bounds").
    localparam [47:0] ROUND_HALF = 48'd1 << (QSHIFT - 1);

    // ---- stage 1: ReLU -------------------------------------------------------
    reg [22:0] relu_q  = 23'd0;
    reg        valid_1 = 1'b0;

    always @(posedge clk) begin
        valid_1 <= start;
        // acc[23] is the sign bit; a negative accumulator becomes 0. For a
        // non-negative acc the top bit is 0, so dropping it loses nothing.
        if (start)
            relu_q <= acc[23] ? 23'd0 : acc[22:0];
    end

    // ---- stage 2: multiply by QM (infers an embedded multiplier) --------------
    reg [47:0] prod_q  = 48'd0;
    reg        valid_2 = 1'b0;

    always @(posedge clk) begin
        valid_2 <= valid_1;
        if (valid_1)
            prod_q <= {25'd0, relu_q} * {24'd0, QM};
    end

    // ---- stage 3: round, shift, clamp ----------------------------------------
    // The low QSHIFT bits of the rounded sum are the discarded fraction; only
    // the bits above them are the result, so the low bits are intentionally unread.
    /* verilator lint_off UNUSEDSIGNAL */
    wire [47:0] rounded = prod_q + ROUND_HALF;
    /* verilator lint_on UNUSEDSIGNAL */
    wire [47-QSHIFT:0] q = rounded[47:QSHIFT];

    always @(posedge clk) begin
        done <= valid_2;
        if (valid_2)
            h <= (q > {{(47-QSHIFT-7){1'b0}}, QMAX}) ? QMAX : q[7:0];
    end
endmodule
/* verilator lint_on PROCASSINIT */

`default_nettype wire
