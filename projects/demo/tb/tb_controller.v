// tb_controller -- self-checking testbench for rtl/controller.v.
//
// Authored by Claude for projects/demo/ (see README.md). Contract:
// ARCHITECTURE.md, "controller".
//
// The testbench plays demo_top around the controller, with behavioural models:
//   weight / image / bias / hidden memories, 1-cycle registered read
//   x mux (layer ? hidden : image), a reference mac (integer arithmetic),
//   a post model (same formula as host/golden.py, done 3 cycles after start,
//   hidden_buf[j] <= h on post_done), and a result_tx stand-in whose busy is
//   high for TXLEN cycles starting the cycle after send.
// Every network is random (seeded), so the scores only come out right if every
// address, strobe and wait lines up; they are compared with a direct
// computation done in the testbench from the same arrays.
//
// A monitor checks, cycle by cycle:
//   - the weight address consumed by each mac_en walks 0..12703 exactly once
//     per inference, in order, and the image/hidden address consumed walks
//     0..N-1 for every neuron (N = 784, then 16)
//   - per neuron: one mac_load with b_addr = 16*layer + j the cycle before, then
//     exactly N mac_en, never overlapping mac_load
//   - 16 post_start (layer 0, j = 0..15, acc already final), each answered by
//     post_done while j is unchanged; 10 sc_we with am_en (layer 1, j = 0..9);
//     one send after all of them, while tx_busy is low
//   - IDLE (frame_enable = 1) returns exactly one cycle after tx_busy falls
//   - frame_enable = !busy always; strobes never fire in IDLE; am_clear only on
//     start in IDLE (start pulses during an inference are ignored)
//   - rst mid-inference (layer 0 RUN, PWAIT, layer 1, TXWAIT) gives IDLE the next
//     cycle, and the following inference is still fully correct
//   - a reset sweep: rst in every other state of both layers (BIAS, LOAD, first
//     RUN cycle, DRAIN, POST, NEXT, SEND), each found from outputs only; and rst
//     together with start (rst wins)
//   - result_tx busy lengths of 1, 2, 3 and 37 cycles, and a post latency of 4
//     and 6 as well as 3, so a controller counting cycles instead of waiting on
//     post_done / tx_busy fails
//   - back to back: a start held across the last TXWAIT cycle and the first
//     IDLE cycle is ignored, then taken, with no gap
//   - hidden values are set to X per network, so a hidden read before its write
//     poisons a score instead of reading the previous network's value
//
// A completed inference counts only if all of its per-inference totals were
// exact; the verdict requires N_FULL completions, N_RST verified resets and
// 10 * N_FULL matching scores, so a run that checked nothing cannot PASS.
`default_nettype none

module tb_controller;

    `include "quant_params.vh"

    localparam integer N_IN    = 784;
    localparam integer N_HID   = 16;
    localparam integer N_OUT   = 10;
    localparam integer NW      = N_HID * N_IN + N_OUT * N_HID;   // 12,704
    localparam integer W2_BASE = N_HID * N_IN;                  // 12,544
    localparam integer NB      = N_HID + N_OUT;                 // 26
    localparam integer MAXSHOW = 10;
    localparam integer N_FULL  = 6;      // inferences that must complete
    localparam integer N_RST   = 16;     // resets that must be verified (4 + 1 + 11)
    localparam integer WAITMAX = 40000;  // cycles; one inference is ~12,900

    // ---- clock, DUT -------------------------------------------------------------
    reg clk = 1'b0;
    always #5 clk = ~clk;

    reg  rst = 1'b0, start = 1'b0;
    wire post_done, tx_busy;
    wire frame_enable, busy, layer, mac_load, mac_en, post_start, sc_we, am_clear, am_en, send;
    wire  [9:0] x_raddr;
    wire [13:0] w_addr;
    wire  [4:0] b_addr;
    wire  [3:0] j;

    controller dut (
        .clk(clk), .rst(rst), .start(start), .post_done(post_done), .tx_busy(tx_busy),
        .frame_enable(frame_enable), .busy(busy), .layer(layer), .x_raddr(x_raddr),
        .w_addr(w_addr), .b_addr(b_addr), .mac_load(mac_load), .mac_en(mac_en),
        .post_start(post_start), .j(j), .sc_we(sc_we), .am_clear(am_clear),
        .am_en(am_en), .send(send)
    );

    // ---- memory models: 1-cycle registered read -------------------------------
    reg signed  [3:0] wmem [0:NW-1];
    reg         [7:0] imem [0:N_IN-1];
    reg signed [23:0] bmem [0:NB-1];
    reg         [7:0] hmem [0:N_HID-1];   // left X until written: reading an
                                          // unwritten hidden value poisons a score

    reg signed  [3:0] w_q;
    reg         [7:0] i_q, h_q;
    reg signed [23:0] b_q;
    // The addresses each read was made with, to check what the mac consumed.
    reg [13:0] w_addr_d  = 14'd0;
    reg  [9:0] x_raddr_d = 10'd0;
    reg  [4:0] b_addr_d  = 5'd0;

    always @(posedge clk) begin
        w_q       <= wmem[w_addr];       // out of range reads X
        i_q       <= imem[x_raddr];
        h_q       <= hmem[x_raddr[3:0]];
        b_q       <= bmem[b_addr];
        w_addr_d  <= w_addr;
        x_raddr_d <= x_raddr;
        b_addr_d  <= b_addr;
    end

    wire [7:0] x = layer ? h_q : i_q;    // demo_top's mux

    // ---- reference mac (integers, independent of the RTL's signed tricks) ------
    function integer prod(input signed [3:0] wv, input [7:0] xv);
        integer a, b;
        begin
            a = wv;      // sign-extended
            b = xv;      // zero-extended
            prod = a * b;
        end
    endfunction

    integer acc = 0;
    always @(posedge clk)
        if (mac_load)    acc <= b_q;
        else if (mac_en) acc <= acc + prod(w_q, x);

    // ---- post model -------------------------------------------------------------
    function [7:0] post_fn(input integer a);
        reg [63:0] p;
        begin
            if (a < 0) p = 64'd0;
            else       p = a;
            p = (p * QM + (64'd1 << (QSHIFT - 1))) >> QSHIFT;
            post_fn = (p > QMAX) ? QMAX : p[7:0];
        end
    endfunction

    // post.v answers exactly 3 cycles after start. plat (changed only between
    // inferences) lets one run use a longer latency: the controller must wait on
    // post_done itself, not on a cycle count that happens to equal 3.
    integer plat = 3;
    reg [15:0] pd = 16'd0;
    reg  [7:0] ph [0:15];
    integer    pk;
    wire [7:0] h_out = ph[plat-1];
    assign post_done = pd[plat-1];
    always @(posedge clk) begin
        pd <= {pd[14:0], post_start};
        if (post_start) ph[0] <= post_fn(acc);
        for (pk = 1; pk < 16; pk = pk + 1) ph[pk] <= ph[pk-1];
        if (post_done) hmem[j] <= h_out;  // demo_top: hidden_buf.we = post_done, waddr = j
    end

    // ---- result_tx stand-in -----------------------------------------------------
    // busy is high for txlen cycles from the cycle after an accepted send, and rst
    // aborts it, like result_tx (busy = state != IDLE, rst -> IDLE). txlen is
    // changed only between inferences; txlen_s is the value at the last send.
    integer txlen = 37, txlen_s = 37;
    integer txcnt = 0;
    always @(posedge clk)
        if (rst)                     txcnt <= 0;
        else if (send && txcnt == 0) txcnt <= txlen;
        else if (txcnt != 0)         txcnt <= txcnt - 1;
    assign tx_busy = (txcnt != 0);

    // ---- direct computation of the expected network ----------------------------
    integer seed = 32'h0C0DE5EE;
    integer acc1_exp [0:N_HID-1];
    reg [7:0] h_exp  [0:N_HID-1];
    integer sc_exp   [0:N_OUT-1];
    integer sc_model [0:N_OUT-1];

    task randomise;
        integer n, k, s, a, b;
        begin
            for (n = 0; n < NW; n = n + 1)   wmem[n] = $random(seed) % 8;   // -7..7, like the model
            for (n = 0; n < N_IN; n = n + 1) imem[n] = $random(seed);       // 0..255
            // Forget the previous network's hidden values, so a hidden value read
            // before this inference wrote it is X (poisons a score), not stale.
            for (n = 0; n < N_HID; n = n + 1) hmem[n] = 8'bx;
            // Mostly positive layer-1 biases, so most hidden values are non-zero
            // and varied (a zero hidden value would hide a wrong hidden address).
            for (n = 0; n < N_HID; n = n + 1) bmem[n] = ($random(seed) % 35000) + 25000;
            for (n = N_HID; n < NB; n = n + 1) bmem[n] = $random(seed) % 2000;
            for (k = 0; k < N_HID; k = k + 1) begin
                s = bmem[k];
                for (n = 0; n < N_IN; n = n + 1) begin
                    a = wmem[k * N_IN + n];  b = imem[n];
                    s = s + a * b;
                end
                acc1_exp[k] = s;
                h_exp[k]    = post_fn(s);
            end
            for (k = 0; k < N_OUT; k = k + 1) begin
                s = bmem[N_HID + k];
                for (n = 0; n < N_HID; n = n + 1) begin
                    a = wmem[W2_BASE + k * N_HID + n];  b = h_exp[n];
                    s = s + a * b;
                end
                sc_exp[k] = s;
            end
        end
    endtask

    // ---- checking -----------------------------------------------------------------
    integer cyc = 0, checks = 0, errors = 0;

    task chk(input [8*40-1:0] what, input integer got, input integer exp);
        begin
            checks = checks + 1;
            if (got !== exp) begin
                errors = errors + 1;
                if (errors <= MAXSHOW)
                    $display("  mismatch @cycle %0d: %0s: got %0d, expected %0d", cyc, what, got, exp);
            end
        end
    endtask

    // Per-inference state, reset by am_clear.
    reg     in_inf = 1'b0;
    integer exp_w = 0, exp_i = 0, ld_count = 0, en_this = 0;
    integer post_count = 0, pd_count = 0, sc_count = 0, send_count = 0, send_cyc = 0;
    integer nidx;
    reg     pend = 1'b0;
    reg [3:0] pend_j = 4'd0;
    integer n_full = 0, n_rst_ok = 0, n_score_ok = 0, n_starts = 0, n_spurious = 0;
    integer rst_cyc = -10, k2;

    // The monitor runs at each posedge and reads the values held during the
    // cycle that just ended (the DUT and the models update non-blocking).
    always @(posedge clk) begin
        chk("frame_enable == !busy", frame_enable, !busy);
        chk("am_clear == IDLE && start", am_clear, frame_enable && start);

        if (frame_enable) begin
            // IDLE: no strobe of an inference. mac_en may be 1 in the single
            // cycle after a reset taken from RUN (it is RUN delayed a cycle).
            chk("mac_load in IDLE",   mac_load,   0);
            chk("post_start in IDLE", post_start, 0);
            chk("sc_we in IDLE",      sc_we,      0);
            chk("am_en in IDLE",      am_en,      0);
            chk("send in IDLE",       send,       0);
            if (cyc != rst_cyc + 1) chk("mac_en in IDLE", mac_en, 0);
        end

        if (cyc == rst_cyc + 1) begin
            chk("IDLE the cycle after rst", frame_enable, 1);
            if (frame_enable === 1'b1 && busy === 1'b0) n_rst_ok = n_rst_ok + 1;
        end

        // ---- completion: the first IDLE cycle after an inference ----
        if (in_inf && frame_enable) begin
            chk("send before return to IDLE", send_count, 1);
            chk("IDLE exactly 1 cycle after tx_busy fell", cyc, send_cyc + txlen_s + 2);
            for (k2 = 0; k2 < N_OUT; k2 = k2 + 1) begin
                chk("final score", sc_model[k2], sc_exp[k2]);
                if (sc_model[k2] === sc_exp[k2]) n_score_ok = n_score_ok + 1;
            end
            if (send_count == 1 && cyc == send_cyc + txlen_s + 2) n_full = n_full + 1;
            in_inf = 1'b0;
        end
        if (in_inf && send_count == 1 && !frame_enable && cyc == send_cyc + txlen_s + 2)
            chk("still busy after tx_busy fell", 1, 0);

        // ---- start of an inference ----
        if (am_clear === 1'b1 && frame_enable) begin
            in_inf = 1'b1;  n_starts = n_starts + 1;
            exp_w = 0;  exp_i = 0;  ld_count = 0;  en_this = 0;
            post_count = 0;  pd_count = 0;  sc_count = 0;  send_count = 0;
            pend = 1'b0;
            for (k2 = 0; k2 < N_OUT; k2 = k2 + 1) sc_model[k2] = 32'bx;
        end
        if (start && !frame_enable) n_spurious = n_spurious + 1;

        if (in_inf && !frame_enable) begin
            if (mac_load && mac_en) chk("mac_load and mac_en together", 1, 0);

            if (mac_load) begin
                if (ld_count > 0)
                    chk("mac_en count of previous neuron", en_this, (ld_count <= N_HID) ? N_IN : N_HID);
                chk("neurons finished before next load", pd_count + sc_count, ld_count);
                chk("b_addr the cycle before mac_load", b_addr_d, ld_count);
                chk("layer at mac_load", layer, (ld_count >= N_HID) ? 1 : 0);
                chk("j at mac_load", j, (ld_count >= N_HID) ? ld_count - N_HID : ld_count);
                ld_count = ld_count + 1;
                exp_i = 0;  en_this = 0;
            end

            if (mac_en) begin
                nidx = ld_count - 1;
                chk("mac_en after a mac_load", ld_count > 0, 1);
                chk("layer during mac_en", layer, (nidx >= N_HID) ? 1 : 0);
                chk("weight address consumed", w_addr_d, exp_w);
                chk("x address consumed", x_raddr_d, exp_i);
                exp_w = exp_w + 1;  exp_i = exp_i + 1;  en_this = en_this + 1;
            end

            if (post_start) begin
                chk("post_start not pending", pend, 0);
                chk("post_start layer", layer, 0);
                chk("post_start j in order", j, post_count);
                chk("post_start j == loaded neuron", j, ld_count - 1);
                chk("mac_en count before post_start", en_this, N_IN);
                if (j < N_HID) chk("layer-1 acc at post_start", acc, acc1_exp[j]);
                pend = 1'b1;  pend_j = j;  post_count = post_count + 1;
            end

            if (post_done) begin
                chk("post_done answers a post_start", pend, 1);
                chk("j unchanged until post_done", j, pend_j);
                chk("hidden value written", h_out, h_exp[pend_j]);
                pend = 1'b0;  pd_count = pd_count + 1;
            end

            if (sc_we || am_en) begin
                chk("sc_we with am_en", sc_we && am_en, 1);
                chk("sc_we layer", layer, 1);
                chk("sc_we j in order", j, sc_count);
                chk("sc_we j == loaded neuron", N_HID + j, ld_count - 1);
                chk("mac_en count before sc_we", en_this, N_HID);
                if (j < N_OUT) begin
                    chk("score at sc_we", acc, sc_exp[j]);
                    sc_model[j] = acc;
                end
                sc_count = sc_count + 1;
            end

            if (send) begin
                chk("one send per inference", send_count, 0);
                chk("scores written before send", sc_count, N_OUT);
                chk("hidden posts before send", post_count, N_HID);
                chk("post_dones before send", pd_count, N_HID);
                chk("loads before send", ld_count, NB);
                chk("weights walked before send", exp_w, NW);
                chk("tx_busy low at send", tx_busy, 0);
                send_count = send_count + 1;  send_cyc = cyc;  txlen_s = txlen;
            end
        end

        // A reset in this cycle: the DUT must be IDLE next cycle (checked above).
        if (rst) begin
            in_inf  = 1'b0;
            rst_cyc = cyc;
        end

        cyc = cyc + 1;
    end

    // ---- stimulus ---------------------------------------------------------------
    task pulse_start;
        begin
            @(negedge clk) start = 1'b1;
            @(negedge clk) start = 1'b0;
        end
    endtask

    task pulse_rst;
        begin
            @(negedge clk) rst = 1'b1;
            @(negedge clk) rst = 1'b0;
        end
    endtask

    task wait_end;  // until the inference completes (or is lost)
        integer t, n_prev;
        begin
            n_prev = n_full;  t = 0;
            while (in_inf && t < WAITMAX) begin @(negedge clk); t = t + 1; end
            chk("inference completed", n_full, n_prev + 1);
        end
    endtask

    task wait_layer1;
        integer t;
        begin
            t = 0;
            while (layer !== 1'b1 && t < WAITMAX) begin @(negedge clk); t = t + 1; end
            chk("reached layer 1", layer, 1);
        end
    endtask

    task wait_post_start;
        integer t;
        begin
            t = 0;
            while (post_start !== 1'b1 && t < WAITMAX) begin @(negedge clk); t = t + 1; end
            chk("saw post_start", post_start, 1);
        end
    endtask

    task wait_tx_busy(input v);
        integer t;
        begin
            t = 0;
            while (tx_busy !== v && t < WAITMAX) begin @(negedge clk); t = t + 1; end
            chk("tx_busy reached level", tx_busy, v);
        end
    endtask

    // ---- reset sweep: rst in a chosen state --------------------------------------
    // Each state is found from outputs only (evaluated at a negedge, i.e. the
    // values of the current cycle); `skip` cycles later rst is raised in that
    // same negedge, so it is sampled at the end of the target cycle.
    //   0 LOAD L0 (mac_load)      1 LOAD L1        2 POST L0 (post_start)
    //   3 post_done (PWAIT end)   4 POST L1 (sc_we) 5 SEND (send)
    //   6 DRAIN L0: mac_en with x_raddr = 784 (i has run past the last input)
    //   7 DRAIN L1: mac_en with x_raddr = 16
    //   8 first cycle with layer = 1 (BIAS of output neuron 0)
    function ev_hit(input integer ev);
        case (ev)
            0: ev_hit = (mac_load === 1'b1) && (layer === 1'b0);
            1: ev_hit = (mac_load === 1'b1) && (layer === 1'b1);
            2: ev_hit = (post_start === 1'b1);
            3: ev_hit = (post_done === 1'b1) && !frame_enable;
            4: ev_hit = (sc_we === 1'b1);
            5: ev_hit = (send === 1'b1);
            6: ev_hit = (mac_en === 1'b1) && (x_raddr === 10'd784) && (layer === 1'b0);
            7: ev_hit = (mac_en === 1'b1) && (x_raddr === 10'd16)  && (layer === 1'b1);
            8: ev_hit = (layer === 1'b1) && !frame_enable;
            default: ev_hit = 1'b0;
        endcase
    endfunction

    task rst_at(input integer ev, input integer skip);
        integer t;
        begin
            t = 0;
            while (!ev_hit(ev) && t < WAITMAX) begin @(negedge clk); t = t + 1; end
            chk("reset sweep found its state", ev_hit(ev), 1);
            repeat (skip) @(negedge clk);
            chk("reset sweep: busy when rst rises", busy, 1);
            rst = 1'b1;
            @(negedge clk) rst = 1'b0;
            repeat (5) @(negedge clk);
        end
    endtask

    initial begin
        repeat (20) @(negedge clk);          // idle, no start: monitor checks quiet

        // A: one clean inference, with result_tx busy for a single cycle (the
        // shortest the contract allows: high only in the first TXWAIT cycle).
        txlen = 1;
        randomise();
        pulse_start();
        wait_end();
        txlen = 37;

        // B: start pulses during layer 0, layer 1 and TXWAIT must be ignored.
        randomise();
        pulse_start();
        repeat (3000) @(negedge clk);
        pulse_start();
        wait_layer1();
        repeat (30) @(negedge clk);
        pulse_start();
        wait_tx_busy(1'b1);
        repeat (5) @(negedge clk);
        pulse_start();
        wait_end();

        // Reset 1: in layer 0 RUN. Then C on the same data must be exact.
        // C uses a post latency of 6 (the controller must wait for post_done)
        // and a 2-cycle result_tx busy.
        txlen = 37;
        randomise();
        pulse_start();
        repeat (5000) @(negedge clk);
        pulse_rst();
        repeat (20) @(negedge clk);
        plat = 6;  txlen = 2;
        pulse_start();
        wait_end();
        plat = 3;  txlen = 37;
        repeat (10) @(negedge clk);

        // Reset 2: in PWAIT (the cycle after post_start).
        randomise();
        pulse_start();
        repeat (2000) @(negedge clk);
        wait_post_start();
        pulse_rst();
        repeat (20) @(negedge clk);

        // Reset 3: in layer 1.
        pulse_start();
        wait_layer1();
        repeat (40) @(negedge clk);
        pulse_rst();
        repeat (20) @(negedge clk);

        // Reset 4: in TXWAIT; let the reply finish before the next frame.
        pulse_start();
        wait_tx_busy(1'b1);
        repeat (5) @(negedge clk);
        pulse_rst();
        wait_tx_busy(1'b0);
        repeat (5) @(negedge clk);

        // E: rst and start in the same cycle. rst wins: still IDLE next cycle
        // (checked by the monitor as "IDLE the cycle after rst").
        @(negedge clk) begin start = 1'b1; rst = 1'b1; end
        @(negedge clk) begin start = 1'b0; rst = 1'b0; end
        repeat (5) @(negedge clk);
        chk("rst + start: no inference started", busy, 0);

        // Reset sweep: rst in every state not covered above (RUN L0, PWAIT, NEXT L1
        // and TXWAIT are). Each is a fresh start on the same network.
        pulse_start();  rst_at(0, 0);   // LOAD   layer 0
        pulse_start();  rst_at(0, 1);   // RUN    layer 0, first cycle
        pulse_start();  rst_at(6, 0);   // DRAIN  layer 0
        pulse_start();  rst_at(2, 0);   // POST   layer 0
        pulse_start();  rst_at(3, 1);   // NEXT   layer 0
        pulse_start();  rst_at(3, 2);   // BIAS   layer 0 (neuron 1)
        pulse_start();  rst_at(8, 0);   // BIAS   layer 1 (neuron 0)
        pulse_start();  rst_at(1, 0);   // LOAD   layer 1
        pulse_start();  rst_at(7, 0);   // DRAIN  layer 1
        pulse_start();  rst_at(4, 0);   // POST   layer 1
        pulse_start();  rst_at(5, 0);   // SEND

        // D: a fresh network after all that.
        randomise();
        pulse_start();
        wait_end();
        repeat (10) @(negedge clk);

        // F: back to back. A start held across the last TXWAIT cycle and the
        // first IDLE cycle: ignored in TXWAIT, taken in IDLE, so the second
        // inference starts in the very cycle the first one returns to IDLE.
        // Post latency 4 and busy 3 for both.
        begin : f_test
            integer t, n_prev;
            plat = 4;  txlen = 3;
            randomise();
            n_prev = n_full;
            pulse_start();
            wait_tx_busy(1'b1);
            wait_tx_busy(1'b0);                 // this negedge: last TXWAIT cycle
            chk("F: still busy in last TXWAIT cycle", busy, 1);
            start = 1'b1;
            @(negedge clk);
            chk("F: IDLE the cycle after tx_busy fell", frame_enable, 1);
            @(negedge clk) start = 1'b0;
            chk("F: second inference started at once", busy, 1);
            t = 0;
            while (n_full < n_prev + 2 && t < WAITMAX) begin @(negedge clk); t = t + 1; end
            chk("F: both inferences completed", n_full, n_prev + 2);
            plat = 3;  txlen = 37;
            repeat (10) @(negedge clk);
        end

        chk("completed inferences", n_full, N_FULL);
        chk("verified resets", n_rst_ok, N_RST);
        chk("matching final scores", n_score_ok, N_OUT * N_FULL);
        chk("ignored start pulses seen", n_spurious > 0, 1);
        $display("tb_controller: %0d checks, %0d errors, %0d inferences completed, %0d resets verified, %0d starts",
                 checks, errors, n_full, n_rst_ok, n_starts);
        if (errors == 0 && checks > 0) $display("PASS");
        else                           $display("FAIL");
        $finish;
    end

    // Watchdog: a hung FSM must FAIL, not just time out.
    initial begin
        #(10 * 600000);
        $display("  watchdog: simulation did not finish");
        $display("FAIL");
        $finish;
    end

endmodule

`default_nettype wire
