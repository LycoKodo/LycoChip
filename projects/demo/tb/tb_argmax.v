// tb_argmax -- self-checking testbench for rtl/argmax.v.
//
// Authored by Claude for projects/demo/ (see README.md). Contract:
// ARCHITECTURE.md, "argmax".
//
// Two independent references:
//   - per cycle: an integer model of the contract (clear forgets; first en
//     taken; later ones only if strictly greater), checked after every edge,
//     including the idle cycles where en is low and idx/score carry garbage.
//   - per set: np.argmax computed the other way round (find the maximum value,
//     then the lowest index holding it), checked once the set is complete.
// Scores are held as integers, never in the DUT's port type, so a signedness
// bug in the DUT cannot be mirrored in the reference.
//
// Sections 1 and 2 present every set as the controller does: clear, then
// idx = 0..9 in order. Sections:
//   0. power-up state: best_idx = 0 before any clear, first en ever taken
//   1. directed sets: all equal (several values), ties, negatives, extremes,
//      max at every position, a set after one with a large max (catches a
//      missing clear), a set aborted half way by clear
//   2. random sets: heavy ties (scores -3..3), realistic range (|s| <= 14,243,
//      ARCHITECTURE.md bound), full 16-bit range
//   3. idx in arbitrary order over 0..15 with ties and en gaps (per-cycle
//      model only): pins "take only if strictly greater", which ascending
//      idx cannot tell apart from a tie-break on idx
//
// The number of checks is counted and compared with the number the sequence
// must produce; fewer means something was skipped, which FAILs.
//
// No `timescale: the RTL has none, and delays here are only relative.
`default_nettype none

module tb_argmax;

    localparam integer N_DIR   = 24;        // directed sets in section 1
    localparam integer N_RAND  = 600;       // random sets in section 2
    localparam integer N_ORD   = 300;       // random-order sequences in section 3
    localparam integer MAXSHOW = 10;        // mismatches printed in full

    reg               clk   = 1'b0;
    reg               clear = 1'b0;
    reg               en    = 1'b0;
    reg         [3:0] idx   = 4'd0;
    reg signed [15:0] score = 16'sd0;
    wire        [3:0] best_idx;

    argmax dut (
        .clk(clk), .clear(clear), .en(en), .idx(idx), .score(score),
        .best_idx(best_idx)
    );

    always #5 clk = ~clk;

    // Per-cycle reference.
    integer ref_have  = 0;
    integer ref_idx   = 0;
    integer ref_score = 0;

    integer errors     = 0;
    integer cyc_checks = 0;
    integer cyc_expect = 0;     // cycles the sequence must check, tallied as sets are built
    integer set_checks = 0;
    integer seed       = 32'h0A26A7A5;
    integer s, k, mode, gap, g;
    integer sc [0:9];           // the current set's scores
    reg [8*20-1:0] where;       // label for mismatch messages

    function integer urand(input integer n);
        integer t;
        begin
            t = $random(seed);
            if (t < 0) t = -t;
            if (t < 0) t = 0;            // -2^31 stays negative after negation
            urand = t % n;
        end
    endfunction

    // One clock: drive inputs away from the edge, step the reference exactly
    // as the contract says, clock, then compare best_idx.
    task step(input c, input e, input integer iv, input integer sv);
        begin
            @(negedge clk);
            clear = c;
            en    = e;
            idx   = iv[3:0];
            score = sv[15:0];
            if (c) begin
                ref_have = 0;
                ref_idx  = 0;
            end else if (e && (ref_have == 0 || sv > ref_score)) begin
                ref_have  = 1;
                ref_idx   = iv;
                ref_score = sv;
            end
            @(posedge clk);
            #1;
            cyc_checks = cyc_checks + 1;
            if (best_idx !== ref_idx[3:0]) begin
                errors = errors + 1;
                if (errors <= MAXSHOW)
                    $display("mismatch [%0s] t=%0t clear=%b en=%b idx=%0d score=%0d: best_idx=%0d expected %0d",
                             where, $time, c, e, iv, sv, best_idx, ref_idx);
            end
        end
    endtask

    // Idle cycle: en low, idx and score carry values that would win if en
    // were ignored (score 32767, an index that is not the current best).
    task idle;
        begin
            step(1'b0, 1'b0, urand(16), (urand(2) == 0) ? 32767 : urand(65536) - 32768);
        end
    endtask

    // Present sc[0..9] as the controller does: clear, then idx 0..9, with
    // `gp` idle cycles after each en (the real controller has hundreds), then
    // compare against np.argmax computed independently.
    task run_set(input integer gp);
        integer i, j, mx, want;
        begin
            step(1'b1, 1'b0, 0, 0);
            for (i = 0; i < 10; i = i + 1) begin
                step(1'b0, 1'b1, i, sc[i]);
                for (j = 0; j < gp; j = j + 1) idle;
            end
            cyc_expect = cyc_expect + 1 + 10 * (1 + gp);
            // np.argmax: the maximum value, then the lowest index holding it.
            mx = sc[0];
            for (i = 1; i < 10; i = i + 1) if (sc[i] > mx) mx = sc[i];
            want = -1;
            for (i = 9; i >= 0; i = i - 1) if (sc[i] == mx) want = i;
            set_checks = set_checks + 1;
            if (best_idx !== want[3:0]) begin
                errors = errors + 1;
                if (errors <= MAXSHOW)
                    $display("set mismatch [%0s] scores %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d: best_idx=%0d, np.argmax=%0d",
                             where, sc[0], sc[1], sc[2], sc[3], sc[4], sc[5], sc[6], sc[7], sc[8], sc[9],
                             best_idx, want);
            end
        end
    endtask

    task fill(input integer v);
        integer i;
        begin
            for (i = 0; i < 10; i = i + 1) sc[i] = v;
        end
    endtask

    initial begin
        // ------------------------------------------------------------ 0
        // Power-up state, before any clear (ARCHITECTURE.md: power-up values
        // come from declaration initialisers). best_idx must be 0, not X, and
        // the first en with no clear ever seen must be taken, even at the
        // minimum score (catches have_best initialised to 1, or a missing
        // initialiser). The posedge at t=5 has clear=en=0: still power-up.
        where = "power-up";
        #1;
        if (best_idx !== 4'd0) begin
            errors = errors + 1;
            $display("mismatch [power-up] t=%0t: best_idx=%b before any clock, expected 0", $time, best_idx);
        end
        @(posedge clk); #1;
        if (best_idx !== 4'd0) begin
            errors = errors + 1;
            $display("mismatch [power-up] t=%0t: best_idx=%b after an idle edge, expected 0", $time, best_idx);
        end
        step(1'b0, 1'b1, 7, -32768);     // first en ever: taken
        step(1'b0, 1'b1, 3, -32768);     // tie: kept at 7
        step(1'b0, 1'b1, 2, -32767);     // strictly greater: taken
        cyc_expect = cyc_expect + 3;

        // ------------------------------------------------------------ 1
        // 24 directed sets (N_DIR); gap alternates 0 / 2 idle cycles.
        where = "all equal";
        fill(0);       run_set(0);
        fill(-32768);  run_set(2);   // the first en must be taken even at the minimum
        fill(32767);   run_set(0);
        fill(-5);      run_set(2);
        fill(777);     run_set(0);

        where = "increasing";
        for (k = 0; k < 10; k = k + 1) sc[k] = -14000 + k * 3000;
        run_set(2);
        where = "decreasing";
        for (k = 0; k < 10; k = k + 1) sc[k] = 14000 - k * 3000;
        run_set(0);

        // Max at each position k, every other score lower; k = 0 and 9 are
        // the edges. Values straddle zero so a sign bug picks the wrong one.
        where = "max at k";
        for (s = 0; s < 10; s = s + 1) begin
            for (k = 0; k < 10; k = k + 1) sc[k] = (k == s) ? 1 : -1 - k;
            run_set(s % 2 ? 2 : 0);
        end

        where = "tie 3 and 7";
        fill(-100); sc[3] = 50; sc[7] = 50;
        run_set(0);
        where = "tie 0 and 9";
        fill(-1); sc[0] = 0; sc[9] = 0;
        run_set(2);
        where = "all negative";
        for (k = 0; k < 10; k = k + 1) sc[k] = -14243 + k * k;   // max at 9
        sc[4] = -1;                                               // except 4
        run_set(0);
        where = "extremes";
        fill(-32768); sc[6] = 32767; sc[8] = 32767;
        run_set(2);
        // -1 vs +1: as unsigned, -1 (0xFFFF) would win.
        where = "minus one";
        fill(1); sc[2] = -1; sc[5] = 2;
        run_set(0);

        // A set whose max is below the previous set's max: without the clear
        // the old best would survive and nothing in this set would be taken.
        where = "after big max";
        fill(-20000); sc[1] = -19000;
        run_set(2);

        // A partial set (no run_set, so tallied here), then clear and a full
        // set whose values are all lower than the partial set's.
        where = "aborted set";
        step(1'b1, 1'b0, 0, 0);
        step(1'b0, 1'b1, 0, 30000);
        step(1'b0, 1'b1, 1, 31000);
        step(1'b0, 1'b1, 2, 29000);
        idle;
        cyc_expect = cyc_expect + 5;
        fill(-30000); sc[8] = -29999;
        run_set(0);

        // ------------------------------------------------------------ 2
        where = "random";
        for (s = 0; s < N_RAND; s = s + 1) begin
            mode = s % 3;
            for (k = 0; k < 10; k = k + 1)
                case (mode)
                    0: sc[k] = urand(7) - 3;                  // ties almost certain
                    1: sc[k] = urand(2 * 14243 + 1) - 14243;  // realistic scores
                    default: sc[k] = urand(65536) - 32768;    // full 16-bit range
                endcase
            gap = urand(4);
            run_set(gap);
        end

        // ------------------------------------------------------------ 3
        // idx in arbitrary order, any of 0..15, repeats allowed, en sometimes
        // low. The contract's rule is "take only if strictly greater"; ascending
        // idx alone cannot tell that apart from a rule that breaks ties by
        // comparing indices (score == best && idx < best_idx), which the
        // contract does not allow. Checked by the per-cycle model only.
        where = "tie, idx descending";
        step(1'b1, 1'b0, 0, 0);
        step(1'b0, 1'b1, 9, 50);        // taken (first)
        step(1'b0, 1'b1, 4, 50);        // tie with a lower idx: NOT taken
        step(1'b0, 1'b1, 0, 50);        // same
        step(1'b0, 1'b1, 15, 49);       // lower: not taken
        step(1'b0, 1'b1, 12, 51);       // greater, idx above 9: taken
        cyc_expect = cyc_expect + 6;

        where = "random order";
        for (s = 0; s < N_ORD; s = s + 1) begin
            step(1'b1, 1'b0, urand(16), urand(65536) - 32768);   // clear ignores idx/score
            cyc_expect = cyc_expect + 1;
            for (k = 0; k < 12; k = k + 1) begin
                step(1'b0, (urand(4) != 0), urand(16),
                     (s % 2) ? (urand(5) - 2) : (urand(65536) - 32768));
                cyc_expect = cyc_expect + 1;
            end
        end

        // Hold after the last set: best_idx must not move with en low.
        where = "final hold";
        for (g = 0; g < 8; g = g + 1) idle;
        cyc_expect = cyc_expect + 8;

        // ------------------------------------------------------------ verdict
        $display("tb_argmax: %0d cycle checks (expected %0d), %0d set checks (expected %0d), %0d errors",
                 cyc_checks, cyc_expect, set_checks, N_DIR + N_RAND, errors);
        if (cyc_checks != cyc_expect || set_checks != N_DIR + N_RAND || cyc_checks == 0) begin
            $display("tb_argmax: wrong number of checks performed");
            errors = errors + 1;
        end
        if (errors == 0) $display("PASS");
        else             $display("FAIL");
        $finish;
    end

endmodule

`default_nettype wire
