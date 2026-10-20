// tb_mac -- self-checking testbench for rtl/mac.v.
//
// Authored by Claude for projects/demo/ (see README.md). Contract:
// ARCHITECTURE.md, "mac".
//
// The reference accumulator is a 32-bit integer computed from integer w and x,
// never from the DUT's port types, so a signedness bug in the DUT cannot be
// mirrored in the reference. acc is compared after every clock edge.
//
// Sections:
//   0. power-up: acc is 0 before any edge (declaration initialiser), holds
//      with neither load nor en, and accumulates from it without a load
//   1. exhaustive single products: every w in -8..7, every x in 0..255
//   2. load priority over en, and hold when neither is high
//   3. worst-case dot products (784 x 255 x {7, -7, -8} plus bias)
//   4. random long sequences (784 steps, random en / load / hold mixed in)
//
// Whenever load is low, load_val is driven with random junk (its own seed),
// as it is in demo_top, where it is bias_rom.q and never returns to 0. A DUT
// that leaks load_val into the accumulate or hold path is then caught.
//
// The number of checks is known in advance; fewer means something was
// skipped, which FAILs (a testbench that checked nothing proved nothing).
//
// No `timescale: the RTL has none, and delays here are only relative.
`default_nettype none

module tb_mac;

    localparam integer N_IN    = 784;       // layer-1 dot-product length
    localparam integer N_RAND  = 40;        // random sequences
    localparam integer MAXSHOW = 10;        // mismatches printed in full

    // Expected number of checks, section by section.
    localparam integer CHK_PWR  = 1 + 2;                 // see section 0
    localparam integer CHK_EXH  = 16 * 256 * 2;          // load-0 check + product check
    localparam integer CHK_PRIO = 8 + 8;                 // see section 2
    localparam integer CHK_WC   = 4 * (1 + N_IN);        // load + 784 accumulates, x4 cases
    localparam integer CHK_RAND = N_RAND * (1 + N_IN);   // load + 784 random steps
    localparam integer CHK_ALL  = CHK_PWR + CHK_EXH + CHK_PRIO + CHK_WC + CHK_RAND;

    reg               clk = 1'b0;
    reg               load = 1'b0;
    reg signed [23:0] load_val = 24'sd0;
    reg               en = 1'b0;
    reg signed  [3:0] w = 4'sd0;
    reg         [7:0] x = 8'd0;
    wire signed [23:0] acc;

    mac dut (
        .clk(clk), .load(load), .load_val(load_val),
        .en(en), .w(w), .x(x), .acc(acc)
    );

    always #5 clk = ~clk;

    integer ref_acc = 0;     // reference, wider than the DUT
    integer errors  = 0;
    integer checks  = 0;
    integer seed    = 32'h1DEA5EED;
    integer jseed   = 32'h0BADF00D;  // junk load_val only; keeps `seed`'s stream unchanged
    integer wi, xi, s, k, r, bias, junk;
    reg [8*24-1:0] where;    // label for mismatch messages

    // One clock: drive inputs away from the edge, step the reference exactly
    // as the contract says, clock, then compare.
    task step(input l, input integer lv, input e, input integer wv, input integer xv);
        begin
            @(negedge clk);
            load     = l;
            junk     = $random(jseed);
            load_val = l ? lv[23:0] : junk[23:0];
            en       = e;
            w        = wv[3:0];
            x        = xv[7:0];
            if (l)       ref_acc = lv;
            else if (e)  ref_acc = ref_acc + wv * xv;
            @(posedge clk);
            #1;
            checks = checks + 1;
            // The reference must fit 24 signed bits, or the test itself is
            // outside the contract's range and the comparison means nothing.
            if (ref_acc > 8388607 || ref_acc < -8388608) begin
                errors = errors + 1;
                $display("tb error [%0s]: reference %0d out of 24-bit range", where, ref_acc);
            end else if (acc !== ref_acc[23:0]) begin
                errors = errors + 1;
                if (errors <= MAXSHOW)
                    $display("mismatch [%0s] t=%0t load=%b load_val=%0d en=%b w=%0d x=%0d: acc=%0d expected %0d",
                             where, $time, l, load_val, e, wv, xv, acc, ref_acc);
            end
        end
    endtask

    // Random helpers. $random(seed) is signed; take a non-negative modulus.
    function integer urand(input integer n);
        integer t;
        begin
            t = $random(seed);
            if (t < 0) t = -t;
            if (t < 0) t = 0;            // -2^31 stays negative after negation
            urand = t % n;
        end
    endfunction

    initial begin
        // ------------------------------------------------------------ 0
        // Power-up value, before the first clock edge (clk rises at t=5).
        // The contract takes power-up values from declaration initialisers;
        // the reference starts at 0, so 0 is what is required here. An
        // X here means the initialiser is missing.
        where = "power-up";
        #1;
        checks = checks + 1;
        if (acc !== 24'sd0) begin
            errors = errors + 1;
            $display("mismatch [%0s] t=%0t: acc=%0d (%b) expected 0", where, $time, acc, acc);
        end
        step(1'b0, 0, 1'b0, 7, 255);       // hold from power-up
        step(1'b0, 0, 1'b1, -3, 77);       // accumulate from power-up: -231

        // ------------------------------------------------------------ 1
        where = "exhaustive";
        for (wi = -8; wi <= 7; wi = wi + 1)
            for (xi = 0; xi <= 255; xi = xi + 1) begin
                step(1'b1, 0, 1'b0, 0, 0);     // load 0
                step(1'b0, 0, 1'b1, wi, xi);   // acc = w * x
            end

        // ------------------------------------------------------------ 2
        // Load with en also high: load wins, the product is discarded.
        // Values chosen so that "load_val + w*x" differs from "load_val".
        where = "load priority";
        step(1'b1,  1000, 1'b1, -8, 255);
        step(1'b1, -1000, 1'b1,  7, 255);
        step(1'b1,  8388607, 1'b1,  7, 255);  // full-width positive load
        step(1'b1, -8388608, 1'b1, -8, 255);  // full-width negative load
        step(1'b1,  12345, 1'b0,  3,  9);     // load alone
        step(1'b1, -54321, 1'b1,  1,  1);
        step(1'b1,  0, 1'b1, -1, 255);
        step(1'b1,  1228, 1'b1,  7, 200);
        // Neither load nor en: acc holds while w, x and load_val (junk,
        // driven by step) change underneath.
        where = "hold";
        for (k = 0; k < 8; k = k + 1)
            step(1'b0, 777 + k, 1'b0, (k % 16) - 8, 255 - k * 31);

        // ------------------------------------------------------------ 3
        // Worst cases the network can produce (ARCHITECTURE.md bounds), and
        // the -8 weight code, which the 4-bit type allows even if unused.
        where = "worst +7";
        step(1'b1, 1228, 1'b0, 0, 0);
        for (k = 0; k < N_IN; k = k + 1) step(1'b0, 0, 1'b1,  7, 255);
        where = "worst -7";
        step(1'b1, -757, 1'b0, 0, 0);
        for (k = 0; k < N_IN; k = k + 1) step(1'b0, 0, 1'b1, -7, 255);
        where = "worst -8";
        step(1'b1, -1228, 1'b0, 0, 0);
        for (k = 0; k < N_IN; k = k + 1) step(1'b0, 0, 1'b1, -8, 255);
        where = "worst +7 -bias";
        step(1'b1, -1228, 1'b0, 0, 0);
        for (k = 0; k < N_IN; k = k + 1) step(1'b0, 0, 1'b1,  7, 255);

        // ------------------------------------------------------------ 4
        // Long random sequences: random bias, then 784 steps of which about
        // 80% accumulate, 15% hold and 5% reload mid-sequence. Reloads use a
        // small value so the sequence stays inside the 24-bit range.
        where = "random";
        for (s = 0; s < N_RAND; s = s + 1) begin
            bias = urand(2 * 1229) - 1228;
            step(1'b1, bias, 1'b0, 0, 0);
            for (k = 0; k < N_IN; k = k + 1) begin
                r  = urand(100);
                wi = urand(16) - 8;
                // Half the sequences use realistic sparse images (mostly 0
                // or 255), half uniform 0..255.
                xi = (s % 2) ? urand(256)
                             : ((urand(4) == 0) ? 255 : ((urand(4) == 0) ? urand(256) : 0));
                if (r < 5)
                    step(1'b1, urand(2001) - 1000, 1'b1, wi, xi);
                else if (r < 20)
                    step(1'b0, 0, 1'b0, wi, xi);
                else
                    step(1'b0, 0, 1'b1, wi, xi);
            end
        end

        // ------------------------------------------------------------ verdict
        $display("tb_mac: %0d checks (expected %0d), %0d errors", checks, CHK_ALL, errors);
        if (checks != CHK_ALL) begin
            $display("tb_mac: wrong number of checks performed");
            errors = errors + 1;
        end
        if (errors == 0) $display("PASS");
        else             $display("FAIL");
        $finish;
    end

endmodule

`default_nettype wire
