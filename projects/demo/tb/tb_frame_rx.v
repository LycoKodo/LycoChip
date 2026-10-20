// tb_frame_rx -- self-checking testbench for frame_rx.
//
// Contract: projects/demo/ARCHITECTURE.md, "frame_rx". Authored by Claude
// (projects/demo/ override; not Alex's work).
//
// Two instances:
//   dut_a  N = 4,   TIMEOUT = 16   every protocol case, cheap to step through
//   dut_b  N = 784, TIMEOUT = default (2,500,000)  one real-size frame, the
//          pixels of test image 0 from mem/test_images.hex
// rx_valid reaches only the selected instance (`which`); the other must stay
// silent, which the independent pulse counters at the bottom check.
//
// Every step drives one cycle of stimulus at a falling edge and checks every
// output of the selected instance at the next falling edge, i.e. just after
// the rising edge that sampled the stimulus. Expectations are written out per
// scenario, not computed by a model of the DUT.
//
// When rx_valid is low, rx_data carries 0xA5 / 0x5A on purpose: a design that
// looks at rx_data without rx_valid will sync or write when it should not.
//
// Cycle convention (the contract's): rx_valid in cycle c -> wr_en in c+1 ->
// for the final byte, done in c+2. `receiving` is not checked in c+1 and c+2
// of the final byte, because the contract does not say whether the state has
// already left DATA there; it is checked low from c+3. What *is* checked in
// c+1 is that a byte arriving there is never written (the frame had N bytes),
// using a sequence (last byte, A5, A5, 5A) that syncs under either reading.
//
// Added by the adversarial review (each closes a gap a mutant slipped through):
//   power-up without rst  a lone 5A must not sync (state powers up in HUNT1)
//   A5 in HUNT2, enable low   stays in HUNT2 (enable gates HUNT1 only)
//   byte in c+1           never written at address N
//   rst with the last byte / in c+1   no write / no done (the RTL documents
//                         that rst cancels a done in flight)
//   dut_b default TIMEOUT the shipped 2,500,000 is exact on both sides; dut_a's
//                         TIMEOUT = 16 is a power of two and hid a TW off-by-one
// No `timescale: the RTL has none, and delays here are only relative.
`default_nettype none

module tb_frame_rx;

    localparam NA = 4;
    localparam TA = 16;
    localparam NB = 784;
    localparam TB = 2500000;            // the contract's default TIMEOUT (dut_b uses the default)

    // Totals this run must reach. If a scenario is deleted or silently
    // skipped, these no longer match and the run FAILs.
    localparam EXP_CHECKS  = 2007;
    // dut_a: 16 full frames x 4, plus frames with no done: 2 (timeout in
    // DATA), 2 (rst mid-frame), 3 (rst with the last byte), 4 (rst in c+1:
    // all four written, done cancelled) = 64 + 11.
    localparam EXP_A_WR    = 75;
    localparam EXP_A_DONE  = 16;
    localparam EXP_B_WR    = NB + 2;    // the image, then 2 bytes of the timeout frame
    localparam EXP_B_DONE  = 1;

    reg        clk    = 1'b0;
    reg        rst    = 1'b0;
    reg        enable = 1'b1;
    reg        v      = 1'b0;
    reg  [7:0] d      = 8'h00;
    reg        which  = 1'b0;           // 0: dut_a, 1: dut_b

    always #10 clk = ~clk;              // period 20 units

    wire       a_rv = v & ~which;
    wire       b_rv = v &  which;

    wire       a_wr, a_done, a_recv;
    wire [9:0] a_addr;
    wire [7:0] a_data;
    wire       b_wr, b_done, b_recv;
    wire [9:0] b_addr;
    wire [7:0] b_data;

    frame_rx #(.N(NA), .TIMEOUT(TA)) dut_a (
        .clk(clk), .rst(rst), .enable(enable), .rx_data(d), .rx_valid(a_rv),
        .wr_en(a_wr), .wr_addr(a_addr), .wr_data(a_data), .done(a_done),
        .receiving(a_recv)
    );

    frame_rx #(.N(NB)) dut_b (
        .clk(clk), .rst(rst), .enable(enable), .rx_data(d), .rx_valid(b_rv),
        .wr_en(b_wr), .wr_addr(b_addr), .wr_data(b_data), .done(b_done),
        .receiving(b_recv)
    );

    wire       o_wr   = which ? b_wr   : a_wr;
    wire [9:0] o_addr = which ? b_addr : a_addr;
    wire [7:0] o_data = which ? b_data : a_data;
    wire       o_done = which ? b_done : a_done;
    wire       o_recv = which ? b_recv : a_recv;

    // The file holds 16 images x 784; only image 0 (words 0..783) is used.
    reg [7:0] img [0:16*NB-1];
    initial $readmemh("mem/test_images.hex", img);

    integer errors = 0;
    integer checks = 0;
    integer cycle  = 0;
    reg [8*28-1:0] tname = "power-up";
    reg            junk  = 1'b0;

    always @(posedge clk) cycle <= cycle + 1;

    // Independent pulse counters: count every cycle each strobe is high on
    // each instance, whatever the stepper expected.
    integer a_wr_seen = 0, a_done_seen = 0, b_wr_seen = 0, b_done_seen = 0;
    integer a_wr_exp  = 0, a_done_exp  = 0, b_wr_exp  = 0, b_done_exp  = 0;
    always @(posedge clk) begin
        if (a_wr)   a_wr_seen   = a_wr_seen   + 1;
        if (a_done) a_done_seen = a_done_seen + 1;
        if (b_wr)   b_wr_seen   = b_wr_seen   + 1;
        if (b_done) b_done_seen = b_done_seen + 1;
    end

    // Frame payload. seed < 0: test image 0. seed 1: only sync values, so the
    // DATA state is proven not to re-sync on them. Otherwise a cheap hash.
    function [7:0] pix(input integer k, input integer seed);
        begin
            if (seed < 0)       pix = img[k];
            else if (seed == 1) pix = k[0] ? 8'h5A : 8'hA5;
            else                pix = (k * 37 + seed * 101 + 13) & 8'hFF;
        end
    endfunction

    // One cycle: drive (vv, dd) now, check outputs after the next rising edge.
    // erecv: 0 / 1, or 2 = not checked.
    task step(input vv, input [7:0] dd,
              input ew, input [9:0] ea, input [7:0] ed,
              input edone, input integer erecv);
        begin
            v    = vv;
            junk = ~junk;
            d    = vv ? dd : (junk ? 8'hA5 : 8'h5A);
            @(negedge clk);
            checks = checks + 1;
            if (ew)    begin if (which) b_wr_exp   = b_wr_exp   + 1; else a_wr_exp   = a_wr_exp   + 1; end
            if (edone) begin if (which) b_done_exp = b_done_exp + 1; else a_done_exp = a_done_exp + 1; end
            if (o_wr !== ew || (ew && (o_addr !== ea || o_data !== ed)) ||
                o_done !== edone || (erecv != 2 && o_recv !== erecv[0])) begin
                errors = errors + 1;
                if (errors <= 10)
                    $display("  mismatch [%0s] cycle %0d dut_%s: wr_en=%b addr=%0d data=%02h done=%b recv=%b ; expected wr_en=%b addr=%0d data=%02h done=%b recv=%s",
                             tname, cycle, which ? "b" : "a",
                             o_wr, o_addr, o_data, o_done, o_recv,
                             ew, ea, ed, edone,
                             erecv == 2 ? "-" : (erecv[0] ? "1" : "0"));
            end
        end
    endtask

    // A byte that must not be written and must not finish a frame.
    task nowr(input [7:0] b, input integer erecv);
        step(1'b1, b, 1'b0, 10'd0, 8'h00, 1'b0, erecv);
    endtask

    task idle(input integer n, input integer erecv);
        integer i;
        for (i = 0; i < n; i = i + 1)
            step(1'b0, 8'h00, 1'b0, 10'd0, 8'h00, 1'b0, erecv);
    endtask

    // Same as idle(n, erecv) but lean enough for millions of cycles: every
    // cycle is checked (no wr_en, no done, receiving == erecv); the whole run
    // counts as one check and reports its first bad cycle only.
    task hold(input integer n, input erecv);
        integer i, bad;
        begin
            bad = 0;
            v   = 1'b0;
            for (i = 0; i < n; i = i + 1) begin
                junk = ~junk;
                d    = junk ? 8'hA5 : 8'h5A;
                @(negedge clk);
                if (bad == 0 && (o_wr !== 1'b0 || o_done !== 1'b0 || o_recv !== erecv)) begin
                    bad = 1;
                    $display("  mismatch [%0s] cycle %0d dut_%s: idle cycle %0d of %0d: wr_en=%b done=%b recv=%b ; expected 0 0 %b",
                             tname, cycle, which ? "b" : "a", i + 1, n, o_wr, o_done, o_recv, erecv);
                end
            end
            checks = checks + 1;
            errors = errors + bad;
        end
    endtask

    // The data bytes k0 .. n-1 of a frame already in DATA, then done.
    task payload(input integer n, input integer k0, input integer gap, input integer seed);
        integer k;
        begin
            for (k = k0; k < n; k = k + 1) begin
                step(1'b1, pix(k, seed), 1'b1, k[9:0], pix(k, seed), 1'b0,
                     (k == n - 1) ? 2 : 1);
                if (k != n - 1) idle(gap, 1);
            end
            step(1'b0, 8'h00, 1'b0, 10'd0, 8'h00, 1'b1, 2);     // done
            idle(2, 0);                                         // and only once
        end
    endtask

    // n_a5 x 0xA5, 0x5A, then the payload; `gap` idle cycles between bytes.
    task frame(input integer n, input integer gap, input integer seed, input integer n_a5);
        integer i;
        begin
            for (i = 0; i < n_a5; i = i + 1) begin
                nowr(8'hA5, 0);
                idle(gap, 0);
            end
            nowr(8'h5A, 1);
            idle(gap, 1);
            payload(n, 0, gap, seed);
        end
    endtask

    integer k;
    initial begin
        @(negedge clk);

        // Power-up values come from declaration initialisers, no reset yet.
        tname = "power-up";
        idle(3, 0);
        // Still no rst: the state must power up in HUNT1, so a lone 5A (or
        // any byte) neither syncs nor writes, and a real frame works.
        tname = "power-up: lone 5A, no rst";
        nowr(8'h5A, 0); nowr(8'h11, 0); nowr(8'h5A, 0); nowr(8'h12, 0);
        tname = "power-up: frame, no rst";
        frame(NA, 1, 12, 1);

        tname = "rst";
        rst = 1'b1; idle(2, 0); rst = 1'b0;
        idle(2, 0);

        tname = "frame, gap 2";
        frame(NA, 2, 0, 1);
        tname = "frame, back-to-back";
        frame(NA, 0, 1, 1);
        tname = "frame, gap 5";
        frame(NA, 5, 2, 1);

        tname = "A5 A5 5A";
        frame(NA, 0, 3, 2);
        tname = "A5 A5 A5 5A, gaps";
        frame(NA, 3, 4, 3);

        tname = "A5 xx resets hunt";
        nowr(8'hA5, 0); nowr(8'h33, 0); nowr(8'h5A, 0);
        for (k = 0; k < NA + 2; k = k + 1) nowr(k[7:0], 0);
        nowr(8'hA5, 0); nowr(8'h00, 0); nowr(8'h5A, 0);
        nowr(8'hA5, 0); nowr(8'hA5, 0); nowr(8'hFF, 0); nowr(8'h5A, 0);
        nowr(8'h77, 0);
        tname = "lone 5A, then 5A A5 5A";
        nowr(8'h5A, 0); nowr(8'h11, 0);
        nowr(8'h5A, 0);
        frame(NA, 1, 5, 1);

        tname = "enable low ignores sync";
        enable = 1'b0;
        nowr(8'hA5, 0); nowr(8'h5A, 0);
        for (k = 0; k < NA + 2; k = k + 1) nowr(8'hC0 + k[7:0], 0);
        nowr(8'hA5, 0); idle(2, 0); nowr(8'h5A, 0);
        nowr(8'h01, 0);
        tname = "enable only gates HUNT1";
        // High for the A5 alone; the rest of the frame must still be taken.
        enable = 1'b1; nowr(8'hA5, 0);
        enable = 1'b0; idle(1, 0);
        nowr(8'h5A, 1);
        payload(NA, 0, 1, 6);
        nowr(8'hA5, 0); nowr(8'h5A, 0);     // and enable still gates HUNT1
        tname = "A5 in HUNT2, enable low";
        // "0xA5 stays in HUNT2" has no enable condition.
        enable = 1'b1; nowr(8'hA5, 0);
        enable = 1'b0; nowr(8'hA5, 0); nowr(8'hA5, 0);
        nowr(8'h5A, 1);
        payload(NA, 0, 0, 13);
        enable = 1'b1;

        tname = "timeout in DATA";
        nowr(8'hA5, 0); nowr(8'h5A, 1);
        step(1'b1, 8'h21, 1'b1, 10'd0, 8'h21, 1'b0, 1);
        step(1'b1, 8'h22, 1'b1, 10'd1, 8'h22, 1'b0, 1);
        idle(TA - 1, 1);
        idle(1, 0);                         // the TIMEOUT-th idle cycle
        nowr(8'h23, 0); nowr(8'h5A, 0); nowr(8'h24, 0);
        tname = "full frame after timeout";
        frame(NA, 1, 7, 1);

        tname = "no timeout at TIMEOUT-1";
        nowr(8'hA5, 0); nowr(8'h5A, 1);
        step(1'b1, 8'h31, 1'b1, 10'd0, 8'h31, 1'b0, 1);
        idle(TA - 1, 1);
        step(1'b1, 8'h32, 1'b1, 10'd1, 8'h32, 1'b0, 1);
        idle(TA - 1, 1);
        payload(NA, 2, TA - 1, 8);

        tname = "timeout right after 5A";
        nowr(8'hA5, 0); nowr(8'h5A, 1);
        idle(TA - 1, 1);
        idle(1, 0);
        nowr(8'h41, 0);

        tname = "timeout in HUNT2";
        nowr(8'hA5, 0);
        idle(TA, 0);
        nowr(8'h5A, 0);                     // HUNT1 now: no sync
        nowr(8'h42, 0);
        tname = "HUNT2 holds at TIMEOUT-1";
        nowr(8'hA5, 0);
        idle(TA - 1, 0);
        nowr(8'h5A, 1);
        payload(NA, 0, 0, 9);

        tname = "rst mid-frame";
        nowr(8'hA5, 0); nowr(8'h5A, 1);
        step(1'b1, 8'h51, 1'b1, 10'd0, 8'h51, 1'b0, 1);
        step(1'b1, 8'h52, 1'b1, 10'd1, 8'h52, 1'b0, 1);
        rst = 1'b1; nowr(8'h53, 0); rst = 1'b0;   // rst beats rx_valid
        nowr(8'h54, 0); nowr(8'h55, 0);
        tname = "rst in HUNT2";
        nowr(8'hA5, 0);
        rst = 1'b1; idle(1, 0); rst = 1'b0;
        nowr(8'h5A, 0);
        tname = "full frame after rst";
        frame(NA, 0, 10, 1);

        tname = "byte in c+1 after last";
        nowr(8'hA5, 0); nowr(8'h5A, 1);
        for (k = 0; k < NA; k = k + 1)
            step(1'b1, 8'h60 + k[7:0], 1'b1, k[9:0], 8'h60 + k[7:0], 1'b0,
                 (k == NA - 1) ? 2 : 1);
        // c+1: a byte. The frame already had N bytes: no write (at address N
        // or anywhere); done still follows the final wr_en.
        step(1'b1, 8'hA5, 1'b0, 10'd0, 8'h00, 1'b1, 2);
        // c+2: A5 then 5A. Whether or not the c+1 A5 counted, this syncs.
        nowr(8'hA5, 0);
        nowr(8'h5A, 1);
        payload(NA, 0, 0, 14);

        tname = "rst with the last byte";
        nowr(8'hA5, 0); nowr(8'h5A, 1);
        for (k = 0; k < NA - 1; k = k + 1)
            step(1'b1, 8'h70 + k[7:0], 1'b1, k[9:0], 8'h70 + k[7:0], 1'b0, 1);
        rst = 1'b1; nowr(8'h73, 0); rst = 1'b0;   // no write, no done, ever
        idle(3, 0);
        nowr(8'h74, 0);

        tname = "rst in c+1 cancels done";
        // Not in the contract; the RTL documents it ("after a reset nothing
        // may start an inference") and this pins it.
        nowr(8'hA5, 0); nowr(8'h5A, 1);
        for (k = 0; k < NA; k = k + 1)
            step(1'b1, 8'h78 + k[7:0], 1'b1, k[9:0], 8'h78 + k[7:0], 1'b0,
                 (k == NA - 1) ? 2 : 1);
        rst = 1'b1; idle(1, 0); rst = 1'b0;      // c+1: rst -> no done in c+2
        idle(3, 0);
        tname = "full frame after rst in c+1";
        frame(NA, 0, 15, 1);

        // Real size, real pixels; the default TIMEOUT never fires here.
        tname = "N=784, test image 0";
        which = 1'b1;
        idle(2, 0);
        frame(NB, 1, -1, 1);

        // The shipped TIMEOUT, exact on both sides, at real size: its idle
        // counter width (22 bits) is what goes to hardware.
        tname = "N=784: TIMEOUT-1 holds";
        nowr(8'hA5, 0); nowr(8'h5A, 1);
        step(1'b1, 8'h81, 1'b1, 10'd0, 8'h81, 1'b0, 1);
        hold(TB - 1, 1'b1);
        step(1'b1, 8'h82, 1'b1, 10'd1, 8'h82, 1'b0, 1);
        tname = "N=784: TIMEOUT fires";
        hold(TB - 1, 1'b1);
        hold(1, 1'b0);                      // the TIMEOUT-th idle cycle
        nowr(8'h83, 0); nowr(8'h5A, 0); nowr(8'h84, 0);

        which = 1'b0;
        idle(2, 0);

        // --- verdict ---
        if (a_wr_seen != a_wr_exp || a_done_seen != a_done_exp ||
            b_wr_seen != b_wr_exp || b_done_seen != b_done_exp) begin
            errors = errors + 1;
            $display("  pulse counts: a wr %0d/%0d done %0d/%0d, b wr %0d/%0d done %0d/%0d (seen/expected)",
                     a_wr_seen, a_wr_exp, a_done_seen, a_done_exp,
                     b_wr_seen, b_wr_exp, b_done_seen, b_done_exp);
        end
        if (checks != EXP_CHECKS || a_wr_exp != EXP_A_WR || a_done_exp != EXP_A_DONE ||
            b_wr_exp != EXP_B_WR || b_done_exp != EXP_B_DONE) begin
            errors = errors + 1;
            $display("  coverage: checks %0d (want %0d), a writes %0d (want %0d), a done %0d (want %0d), b writes %0d (want %0d), b done %0d (want %0d)",
                     checks, EXP_CHECKS, a_wr_exp, EXP_A_WR, a_done_exp, EXP_A_DONE,
                     b_wr_exp, EXP_B_WR, b_done_exp, EXP_B_DONE);
        end
        $display("  %0d checks, %0d errors; dut_a %0d writes %0d frames, dut_b %0d writes %0d frames",
                 checks, errors, a_wr_seen, a_done_seen, b_wr_seen, b_done_seen);
        if (errors == 0) $display("PASS");
        else             $display("FAIL");
        $finish;
    end

endmodule
`default_nettype wire
