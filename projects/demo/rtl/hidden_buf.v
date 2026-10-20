`default_nettype none
// hidden_buf -- the 16 layer-1 activations, 16 x 8, simple dual-port.
//
// Written once per hidden neuron (on post_done, at waddr = j) during layer 0, and read
// back as the x operand of every layer-1 MAC. The read is registered, so the latency is
// one cycle: raddr in cycle c, rdata valid during cycle c+1. That is the same latency as
// image_buf, so the layer mux in demo_top needs no alignment stage.
//
// A read and a write to the same address in the same cycle return the OLD contents
// (both are non-blocking assignments to/from the array). The controller never does
// this: hidden_buf is only written in layer 0 and only read in layer 1.
//
// The array has no initialiser: Verilog-2001 has no array initialiser syntax, and the
// controller reads no word it has not first written. Unwritten words read as X in sim.
//
// rdata has no power-up initialiser either: before the first write it holds nothing
// meaningful, and an initial value on a RAM output register can stop Quartus inferring
// the RAM. It is X in simulation until the first clock edge.
module hidden_buf (
    input  wire       clk,
    input  wire       we,
    input  wire [3:0] waddr,
    input  wire [7:0] wdata,
    input  wire [3:0] raddr,
    output reg  [7:0] rdata
);

    reg [7:0] mem [0:15];

    always @(posedge clk) begin
        if (we)
            mem[waddr] <= wdata;
        rdata <= mem[raddr];
    end

endmodule
`default_nettype wire
