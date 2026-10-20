// mac -- multiply-accumulate for one neuron's dot product.
//
// Authored by Claude for projects/demo/ (see README.md: Article I override,
// this directory only). Contract: ARCHITECTURE.md, "mac".
//
//   load (priority): acc <= load_val          (the bias, before a neuron starts)
//   else en:         acc <= acc + w * x       (w signed 4-bit, x unsigned 8-bit)
//   else:            acc holds
//
// Registered: inputs sampled on posedge clk, new acc visible after that edge.
`default_nettype none

// The power-up value of acc comes from its declaration initialiser, as the
// contract requires (Quartus honours it on Cyclone IV; this module has no rst
// port). Verilator flags initialiser + procedural write as PROCASSINIT; that
// combination is intended here.
/* verilator lint_off PROCASSINIT */
module mac (
    input  wire               clk,
    input  wire               load,
    input  wire signed [23:0] load_val,
    input  wire               en,
    input  wire signed  [3:0] w,
    input  wire         [7:0] x,
    output reg  signed [23:0] acc
);

    // Power-up values of output ports. Not in the port list: Quartus 20.1
    // silently ignores an initialiser there (see uart_tx.v).
    initial acc = 24'sd0;
/* verilator lint_on PROCASSINIT */

    // x is unsigned, w is signed. Verilog makes a mixed expression entirely
    // unsigned, so a bare `w * x` would treat w = -1 as 15. Prepending a zero
    // bit gives x a 9-bit signed form (0..255) with the same value, and the
    // signed x signed product of 4 + 9 bits fits 13 bits exactly
    // (range -8*255 = -2040 .. 7*255 = 1785).
    wire signed  [8:0] x_s  = {1'b0, x};
    wire signed [12:0] prod = w * x_s;

    // Explicit sign extension to the accumulator width, so the add is the
    // same 24-bit signed add whatever the tool's expression-sizing rules do.
    wire signed [23:0] prod_ext = {{11{prod[12]}}, prod};

    always @(posedge clk) begin
        if (load)
            acc <= load_val;
        else if (en)
            acc <= acc + prod_ext;
    end

endmodule

`default_nettype wire
