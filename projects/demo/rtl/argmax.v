// argmax -- running arg-max over the layer-2 scores, one score per en pulse.
//
// Authored by Claude for projects/demo/ (see README.md: Article I override,
// this directory only). Contract: ARCHITECTURE.md, "argmax".
//
//   clear (priority): forget everything (back to the power-up state)
//   else en:          take (idx, score) if it is the first since clear, or if
//                     score is strictly greater than the best so far
//   else:             hold
//
// Registered: inputs sampled on posedge clk, new best_idx visible after that
// edge. The controller presents idx = 0, 1, ... 9 in order, so "strictly
// greater" makes ties keep the lower index, the same answer as np.argmax.
`default_nettype none

// best_idx's power-up value comes from its declaration initialiser, as the
// contract requires (no rst port). Verilator flags initialiser + procedural
// write as PROCASSINIT; that combination is intended here.
/* verilator lint_off PROCASSINIT */
module argmax (
    input  wire               clk,
    input  wire               clear,
    input  wire               en,
    input  wire         [3:0] idx,
    input  wire signed [15:0] score,
    output reg          [3:0] best_idx
);

    // Power-up values of output ports. Not in the port list: Quartus 20.1
    // silently ignores an initialiser there (see uart_tx.v).
    initial best_idx = 4'd0;

    // have_best is what makes the first en after clear unconditional. Without
    // it, best_score would need a "minus infinity" start value, and -32768 is
    // a legal score: a set of all -32768 would then never be taken.
    reg               have_best  = 1'b0;
    reg signed [15:0] best_score = 16'sd0;
/* verilator lint_on PROCASSINIT */

    // Both operands are declared signed, so this is a signed compare.
    wire better = !have_best || (score > best_score);

    always @(posedge clk) begin
        if (clear) begin
            have_best <= 1'b0;
            best_idx  <= 4'd0;
            // best_score is not cleared: it is never read while have_best is 0.
        end else if (en && better) begin
            have_best  <= 1'b1;
            best_idx   <= idx;
            best_score <= score;
        end
    end

endmodule

`default_nettype wire
