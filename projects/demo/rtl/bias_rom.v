// bias_rom -- the 26 biases of both layers, 24-bit signed, 1-cycle read.
//
// Layout (ARCHITECTURE.md): b1[0..15] at addresses 0..15, b2[0..9] at 16..25.
// The controller presents b_addr in BIAS and pulses mac_load in LOAD, the next
// cycle, so the registered output is exactly on time for the accumulator.
//
// Addresses 26..31 are not part of the contract and are never driven by the
// controller; their read value is undefined (X in simulation, 0 on the part).
//
// The array is declared 32 deep, the full range of the 5-bit address, and the
// file fills only 0..25. Declared [0:25], Quartus still builds a 32-word ROM
// (the address width sets the depth) from a 26-word .mif and raises Critical
// Warning 127005 about the mismatch (first synthesis, 2026-10-20). Harmless,
// but a critical warning that is always there hides the one that matters.
`default_nettype none

module bias_rom #(
    parameter INIT = "mem/bias.hex"     // relative to projects/demo/ (Quartus and sim.sh CWD)
) (
    input  wire               clk,
    input  wire        [4:0]  addr,
    output reg  signed [23:0] q
);

    // Declared signed so that q, and anything that reads it, sees two's
    // complement: the file holds e.g. FFFD0B for -757, not 16,776,459.
    reg signed [23:0] mem [0:31];

    // ROM initialisation; Quartus turns this into the memory's contents.
    // Explicit range: the file holds exactly 26 words (0..25).
    initial $readmemh(INIT, mem, 0, 25);

    // Registered read: address in cycle c, data valid in cycle c+1.
    always @(posedge clk)
        q <= mem[addr];

endmodule

`default_nettype wire
