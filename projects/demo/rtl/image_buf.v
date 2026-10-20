// image_buf -- the 28x28 input image, written by frame_rx and read by the MAC loop.
//
// Contract (ARCHITECTURE.md): 784 x 8, simple dual-port, 1-cycle read, must infer M9K.
//   write: we/waddr/wdata sampled at the clock edge; the word is stored at that edge.
//   read : raddr presented in cycle c, rdata valid during cycle c+1 (registered output).
//
// Why it is written this way:
//   - One clocked block with the write and the registered read is the pattern Quartus
//     recognises as a simple dual-port RAM and maps to M9K (784 x 8 = 6,272 bits, one
//     block). An unregistered read would force the array into logic elements.
//   - No reset and no initialiser on the array or on rdata: M9K contents cannot be
//     reset, and a reset on the output register can stop the inference. Nothing reads
//     the buffer before frame_rx has written a full frame, so power-up contents are
//     irrelevant (and Cyclone IV clears M9K to 0 at configuration anyway).
//   - Read-during-write to the SAME address in the same cycle is not used by the
//     design (a frame is written before the controller starts reading, and
//     frame_enable is low while it runs), so it is left to Quartus' default rather
//     than adding bypass logic. Not tested by tb_image_buf for the same reason.
//   - Addresses 784..1023 are outside the contract; nothing drives them.
`default_nettype none

module image_buf (
    input  wire       clk,
    input  wire       we,
    input  wire [9:0] waddr,
    input  wire [7:0] wdata,
    input  wire [9:0] raddr,
    output reg  [7:0] rdata
);

    localparam DEPTH = 784;

    (* ramstyle = "M9K" *) reg [7:0] mem [0:DEPTH-1];

    always @(posedge clk) begin
        if (we)
            mem[waddr] <= wdata;
        rdata <= mem[raddr];
    end

endmodule

`default_nettype wire
