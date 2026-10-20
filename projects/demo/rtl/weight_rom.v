// weight_rom -- every weight of both layers, 4-bit signed, one per address.
//
// Authored by Claude for projects/demo/ (Article I override, see README.md).
// Contract: ARCHITECTURE.md, "weight_rom".
//
//   address = 12,544 * layer + neuron * n_inputs + input
//
// so the controller walks all 12,704 weights with one counter that is never
// reset between layers (layer 0: 16 x 784 = 12,544 words, layer 1: 10 x 16 = 160).
//
// Timing: 1-cycle read. addr presented in cycle c, q valid during cycle c+1.
//
// 12,704 x 4 = 50,816 bits. The read is registered and there is no reset on q,
// which is the shape Quartus needs to map this into M9K blocks as a ROM; an
// asynchronous read or a reset on q would force it into logic elements.
`default_nettype none

module weight_rom #(
    parameter DEPTH = 12704,
    parameter INIT  = "mem/weights.hex"
) (
    input  wire               clk,
    input  wire [13:0]        addr,
    output reg  signed [3:0]  q
);

    // Signed storage, so q is the two's-complement weight directly: hex digit
    // 8..F reads back as -8..-1, and the mac's signed multiply needs no cast.
    (* romstyle = "M9K" *)
    reg signed [3:0] mem [0:DEPTH-1];

    // The only initial block: ROM contents. Quartus turns this into the M9K
    // initialisation (.mif) at synthesis; the path is relative to projects/demo/.
    initial $readmemh(INIT, mem);

    always @(posedge clk)
        q <= mem[addr];

endmodule

`default_nettype wire
