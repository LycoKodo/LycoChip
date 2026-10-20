// demo_top -- the whole MNIST demo: UART in, inference, UART out, display, LEDs.
//
// Contract: projects/demo/ARCHITECTURE.md, "demo_top". Authored by Claude
// (projects/demo/ override; not Alex's work).
//
// Wiring only, plus the few registers the contract puts here:
//
//   rst      rst_n (KEY RESET, active low, asynchronous) through a 2-FF
//            synchroniser; active high and synchronous everywhere else.
//   x mux    layer 0 reads the image, layer 1 the hidden values. image_buf and
//            hidden_buf both have a 1-cycle registered read, so the mux needs
//            no alignment.
//   digit    on `send`, argmax.best_idx is latched for the display and
//            result_valid is set (cleared only by rst).
//   LEDs     active low: [0] receiving, [1] busy, [2] result_valid,
//            [3] heartbeat (bit 24 of a free-running counter, 50 MHz / 2^25
//            = 1.49 Hz: proves the configuration loaded and the clock runs).
//
// Every register here is internal, with a declaration initialiser, and the
// output ports are plain wires. An initialiser on an `output reg` in the port
// list is ignored by Quartus 20.1 (found on uart_tx.tx, 2026-10-20).
`default_nettype none

/* verilator lint_off PROCASSINIT */
module demo_top #(
    parameter CLKS_PER_BIT = 434,       // 50 MHz / 115,200 baud
    parameter TIMEOUT      = 2500000    // frame_rx idle timeout, cycles (50 ms)
) (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       uart_rx,
    output wire       uart_tx,
    output wire [3:0] led_n,
    output wire [7:0] seg_n,
    output wire [3:0] dig_n
);

    // ---- reset synchroniser --------------------------------------------------
    // Powers up 0, so rst is asserted for the first two cycles after
    // configuration and then follows the key.
    reg rst_s1 = 1'b0;
    reg rst_s2 = 1'b0;
    always @(posedge clk) begin
        rst_s1 <= rst_n;
        rst_s2 <= rst_s1;
    end
    wire rst = ~rst_s2;

    // ---- UART receive and framing -------------------------------------------
    wire [7:0] rx_data;
    wire       rx_valid;

    uart_rx #(.CLKS_PER_BIT(CLKS_PER_BIT)) u_uart_rx (
        .clk   (clk),
        .rx    (uart_rx),
        .data  (rx_data),
        .valid (rx_valid)
    );

    wire       frame_enable;
    wire       img_we;
    wire [9:0] img_waddr;
    wire [7:0] img_wdata;
    wire       frame_done;
    wire       receiving;

    frame_rx #(.N(784), .TIMEOUT(TIMEOUT)) u_frame_rx (
        .clk       (clk),
        .rst       (rst),
        .enable    (frame_enable),
        .rx_data   (rx_data),
        .rx_valid  (rx_valid),
        .wr_en     (img_we),
        .wr_addr   (img_waddr),
        .wr_data   (img_wdata),
        .done      (frame_done),
        .receiving (receiving)
    );

    // ---- controller -----------------------------------------------------------
    wire        post_done;
    wire        res_busy;
    wire        busy;
    wire        layer;
    wire  [9:0] x_raddr;
    wire [13:0] w_addr;
    wire  [4:0] b_addr;
    wire        mac_load;
    wire        mac_en;
    wire        post_start;
    wire  [3:0] j;
    wire        sc_we;
    wire        am_clear;
    wire        am_en;
    wire        send;

    controller u_controller (
        .clk          (clk),
        .rst          (rst),
        .start        (frame_done),
        .post_done    (post_done),
        .tx_busy      (res_busy),
        .frame_enable (frame_enable),
        .busy         (busy),
        .layer        (layer),
        .x_raddr      (x_raddr),
        .w_addr       (w_addr),
        .b_addr       (b_addr),
        .mac_load     (mac_load),
        .mac_en       (mac_en),
        .post_start   (post_start),
        .j            (j),
        .sc_we        (sc_we),
        .am_clear     (am_clear),
        .am_en        (am_en),
        .send         (send)
    );

    // ---- memories ---------------------------------------------------------------
    wire        [7:0] img_q;
    wire        [7:0] hid_q;
    wire signed [3:0] w_q;
    wire signed [23:0] b_q;
    wire        [7:0] h;

    image_buf u_image_buf (
        .clk   (clk),
        .we    (img_we),
        .waddr (img_waddr),
        .wdata (img_wdata),
        .raddr (x_raddr),
        .rdata (img_q)
    );

    hidden_buf u_hidden_buf (
        .clk   (clk),
        .we    (post_done),
        .waddr (j),
        .wdata (h),
        .raddr (x_raddr[3:0]),
        .rdata (hid_q)
    );

    weight_rom u_weight_rom (
        .clk  (clk),
        .addr (w_addr),
        .q    (w_q)
    );

    bias_rom u_bias_rom (
        .clk  (clk),
        .addr (b_addr),
        .q    (b_q)
    );

    // ---- datapath -----------------------------------------------------------------
    wire        [7:0] x = layer ? hid_q : img_q;
    wire signed [23:0] acc;

    mac u_mac (
        .clk      (clk),
        .load     (mac_load),
        .load_val (b_q),
        .en       (mac_en),
        .w        (w_q),
        .x        (x),
        .acc      (acc)
    );

    post u_post (
        .clk   (clk),
        .start (post_start),
        .acc   (acc),
        .h     (h),
        .done  (post_done)
    );

    // Layer-2 scores fit in 16 bits exactly (ARCHITECTURE.md, "Numeric bounds").
    wire signed [15:0] score = acc[15:0];
    wire        [3:0] best_idx;

    argmax u_argmax (
        .clk      (clk),
        .clear    (am_clear),
        .en       (am_en),
        .idx      (j),
        .score    (score),
        .best_idx (best_idx)
    );

    // ---- result out ---------------------------------------------------------------
    wire       tx_busy;
    wire       tx_start;
    wire [7:0] tx_data;

    result_tx u_result_tx (
        .clk      (clk),
        .rst      (rst),
        .we       (sc_we),
        .widx     (j),
        .wscore   (score),
        .send     (send),
        .digit    (best_idx),
        .tx_busy  (tx_busy),
        .tx_start (tx_start),
        .tx_data  (tx_data),
        .busy     (res_busy)
    );

    uart_tx #(.CLKS_PER_BIT(CLKS_PER_BIT)) u_uart_tx (
        .clk   (clk),
        .data  (tx_data),
        .start (tx_start),
        .tx    (uart_tx),
        .busy  (tx_busy)
    );

    // ---- displayed digit ----------------------------------------------------------
    reg [3:0] digit_q      = 4'd0;
    reg       result_valid = 1'b0;
    always @(posedge clk) begin
        if (rst) begin
            result_valid <= 1'b0;
        end else if (send) begin
            digit_q      <= best_idx;
            result_valid <= 1'b1;
        end
    end

    seg7 u_seg7 (
        .digit (digit_q),
        .valid (result_valid),
        .seg_n (seg_n),
        .dig_n (dig_n)
    );

    // ---- heartbeat and LEDs -------------------------------------------------------
    reg [24:0] hb = 25'd0;
    always @(posedge clk)
        hb <= hb + 25'd1;

    assign led_n = {~hb[24], ~result_valid, ~busy, ~receiving};

endmodule
/* verilator lint_on PROCASSINIT */

`default_nettype wire
