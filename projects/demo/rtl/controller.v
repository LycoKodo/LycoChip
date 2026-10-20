// controller -- the one FSM that sequences a whole inference.
//
// Authored by Claude for projects/demo/ (see README.md: Article I override,
// this directory only). Contract: ARCHITECTURE.md, "controller".
//
// For each neuron (16 hidden in layer 0, then 10 outputs in layer 1):
//
//   BIAS   b_addr = layer ? 16+j : j      bias_rom registers it this edge
//   LOAD   mac_load (acc <= bias)         bias_rom.q is valid this cycle
//   RUN    x_raddr = i, w_addr, N cycles  memories register them this edge
//   DRAIN                                 last product accumulates (mac_en)
//   POST   layer 0: post_start            acc is final this cycle
//          layer 1: sc_we, am_en
//   PWAIT  (layer 0) until post_done      demo_top writes h to hidden_buf[j]
//   NEXT   j++, or layer 0 -> 1, or SEND
//
// then SEND (send) and TXWAIT (until result_tx is idle again) -> IDLE.
//
// Memory reads take one cycle, so the product of the address presented in RUN
// cycle c reaches the mac in cycle c+1. mac_en is therefore (state == RUN)
// delayed by one register: it is high for the 2nd..Nth RUN cycles and in DRAIN,
// N cycles in total. DRAIN exists only to let that last product land.
//
// w_addr is one counter for both layers (weight_rom layout: 12,544 x layer +
// neuron x n_inputs + input). It is zeroed on start and never between layers:
// it reaches 12,544 exactly as layer 1 begins and 12,704 at the end.
//
// Strobes are combinational decodes of the state register (am_clear also of
// start), so each is high for exactly the one cycle its state lasts.
//
// Power-up values come from declaration initialisers (ARCHITECTURE.md
// conventions), so the FSM starts in IDLE without rst. Verilator calls an
// initialiser plus a procedural write PROCASSINIT; that is intended here.
`default_nettype none

/* verilator lint_off PROCASSINIT */
module controller (
    input  wire        clk,
    input  wire        rst,          // synchronous, active high
    input  wire        start,        // frame_rx.done: a full image is in image_buf
    input  wire        post_done,
    input  wire        tx_busy,      // result_tx.busy

    output wire        frame_enable, // frame_rx may accept a new frame (IDLE only)
    output wire        busy,
    output reg         layer,
    output wire  [9:0] x_raddr,
    output reg  [13:0] w_addr,
    output wire  [4:0] b_addr,
    output wire        mac_load,
    output reg         mac_en,
    output wire        post_start,
    output reg   [3:0] j,
    output wire        sc_we,
    output wire        am_clear,
    output wire        am_en,
    output wire        send
);

    // Power-up values of output ports. Not in the port list: Quartus 20.1
    // silently ignores an initialiser there (see uart_tx.v).
    initial layer  = 1'b0;
    initial w_addr = 14'd0;
    initial mac_en = 1'b0;
    initial j      = 4'd0;
/* verilator lint_on PROCASSINIT */

    localparam [3:0] S_IDLE   = 4'd0,
                     S_BIAS   = 4'd1,
                     S_LOAD   = 4'd2,
                     S_RUN    = 4'd3,
                     S_DRAIN  = 4'd4,
                     S_POST   = 4'd5,
                     S_PWAIT  = 4'd6,
                     S_NEXT   = 4'd7,
                     S_SEND   = 4'd8,
                     S_TXWAIT = 4'd9;

    // Last input index and last neuron index of the current layer.
    localparam [9:0] I_LAST_L0 = 10'd783,  I_LAST_L1 = 10'd15;
    localparam [3:0] J_LAST_L0 = 4'd15,    J_LAST_L1 = 4'd9;

    /* verilator lint_off PROCASSINIT */
    reg [3:0] state = S_IDLE;
    reg [9:0] i     = 10'd0;    // input index within the current neuron
    /* verilator lint_on PROCASSINIT */

    wire       go     = (state == S_IDLE) && start;
    wire [9:0] i_last = layer ? I_LAST_L1 : I_LAST_L0;
    wire [3:0] j_last = layer ? J_LAST_L1 : J_LAST_L0;

    // ---- outputs -------------------------------------------------------------
    assign frame_enable = (state == S_IDLE);
    assign busy         = (state != S_IDLE);

    // i is 0..783, so it is the image address as is; in layer 1 the hidden
    // buffer uses x_raddr[3:0] (i is 0..15 there).
    assign x_raddr = i;

    // Combinational and valid in every state; it only matters in BIAS, where
    // bias_rom registers it so that q is ready in LOAD.
    assign b_addr = layer ? (5'd16 + {1'b0, j}) : {1'b0, j};

    assign am_clear   = go;
    assign mac_load   = (state == S_LOAD);
    assign post_start = (state == S_POST) && !layer;
    assign sc_we      = (state == S_POST) &&  layer;
    assign am_en      = (state == S_POST) &&  layer;
    assign send       = (state == S_SEND);

    // ---- mac_en: RUN delayed one cycle, to line up with the 1-cycle reads ----
    always @(posedge clk)
        mac_en <= (state == S_RUN);

    // ---- state and counters ----------------------------------------------------
    always @(posedge clk) begin
        if (rst) begin
            state  <= S_IDLE;
            layer  <= 1'b0;
            j      <= 4'd0;
            i      <= 10'd0;
            w_addr <= 14'd0;
        end else begin
            case (state)
                S_IDLE:
                    if (start) begin
                        layer  <= 1'b0;
                        j      <= 4'd0;
                        w_addr <= 14'd0;
                        state  <= S_BIAS;
                    end

                S_BIAS:
                    state <= S_LOAD;

                S_LOAD: begin
                    i     <= 10'd0;
                    state <= S_RUN;
                end

                S_RUN: begin
                    // This cycle presents x_raddr = i and w_addr; both advance.
                    w_addr <= w_addr + 14'd1;
                    i      <= i + 10'd1;
                    if (i == i_last)
                        state <= S_DRAIN;
                end

                S_DRAIN:
                    state <= S_POST;

                S_POST:
                    state <= layer ? S_NEXT : S_PWAIT;

                // j must not change until post_done: demo_top writes post.h to
                // hidden_buf[j] in the post_done cycle.
                S_PWAIT:
                    if (post_done)
                        state <= S_NEXT;

                S_NEXT:
                    if (j == j_last) begin
                        j <= 4'd0;
                        if (!layer) begin
                            layer <= 1'b1;
                            state <= S_BIAS;
                        end else begin
                            state <= S_SEND;
                        end
                    end else begin
                        j     <= j + 4'd1;
                        state <= S_BIAS;
                    end

                S_SEND:
                    state <= S_TXWAIT;

                // result_tx raises busy the cycle after send, i.e. in the first
                // TXWAIT cycle, so "low" here can only mean the reply is finished.
                S_TXWAIT:
                    if (!tx_busy)
                        state <= S_IDLE;

                default:
                    state <= S_IDLE;
            endcase
        end
    end

endmodule

`default_nettype wire
