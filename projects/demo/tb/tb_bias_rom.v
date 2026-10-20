// tb_bias_rom -- checks bias_rom against mem/bias.hex.
//
// What is checked, and why each check can fail:
//   - every one of the 26 words, read back-to-back (one new address per
//     cycle), forwards and then backwards. All 26 words are distinct, so a
//     ROM with 0 or 2 cycles of latency returns the wrong word.
//   - the address is driven 1 time unit after a rising edge, the way the
//     controller's combinational b_addr changes. q is checked twice per
//     address: 1 unit before the next rising edge it must STILL show the
//     previous word, and 1 unit after that edge it must show the new one.
//     So q may change only at a rising edge. A combinational read, or one
//     clocked on the falling edge (or both edges), fails the first check.
//     Neither check is at the same instant as a clock edge, so the verdict
//     does not depend on how the simulator orders processes that wake on
//     the same edge. (The previous version drove addr on the falling edge,
//     where a negedge-clocked mutant was caught only by Icarus's ordering.)
//   - values are compared as 32-bit integers after sign extension, so a ROM
//     that drops the sign (zero-extends) fails on every negative bias. The tb
//     also requires that some negative words were actually seen.
//   - signedness does not cross a port: this tb's own `wire signed` would
//     re-sign an unsigned DUT output. So q is also read hierarchically
//     (dut.q), which takes the DUT's declaration, enforcing the contract's
//     `output reg signed [23:0] q` for every consumer that reads it as is.
//   - the INIT parameter is honoured: a second instance loads
//     mem/expected.hex (an existing file, whose first 26 words differ from
//     bias.hex) and must return that file's words. A ROM that hardcodes
//     "mem/bias.hex" passes everything else and fails here.
//     Expected noise: Icarus warns "Too many words in the file for the
//     requested range [0:25]" for expected.hex (176 words), once for that
//     instance and once for the tb's own reference copy. Only the first 26
//     words are used.
//   - the number of checks must be exactly N_CHECKS; zero checks is a FAIL.
`default_nettype none

module tb_bias_rom;

    localparam N        = 26;
    localparam N_SEQ    = 2 * N;               // forward pass + backward pass
    // Per instance: one "after the edge" check per address, plus one
    // "before the edge" check per address except the first.
    localparam N_CHECKS = 2 * (N_SEQ + N_SEQ - 1);

    reg               clk  = 1'b0;
    reg        [4:0]  addr = 5'd0;
    wire signed [23:0] q;
    wire signed [23:0] q_alt;

    bias_rom dut (.clk(clk), .addr(addr), .q(q));                // default INIT

    bias_rom #(.INIT("mem/expected.hex")) dut_alt (.clk(clk), .addr(addr), .q(q_alt));

    always #10 clk = ~clk;           // period 20 time units (no `timescale: the RTL has none to match)

    // Reference copies of the same files the DUTs load.
    reg [23:0] ref_mem [0:N-1];
    reg [23:0] ref_alt [0:N-1];

    integer errors    = 0;
    integer checks    = 0;
    integer negatives = 0;
    integer differ    = 0;
    integer k;
    integer i;
    integer exp_i;
    integer got_i;
    integer got_h;
    integer seq [0:N_SEQ-1];         // address order: 0..25, then 25..0

    // Compare one instance's q (which should hold the word at address a)
    // against its file. alt = 0: dut / bias.hex; alt = 1: dut_alt / expected.hex.
    // when = 0: just before a rising edge; 1: just after one.
    task check_word(input integer alt, input integer a, input integer when);
        reg [23:0] r;
        begin
            r = alt ? ref_alt[a] : ref_mem[a];
            // Sign-extend the file's 24-bit pattern by hand, independently of
            // how the DUT declares anything.
            exp_i = {{8{r[23]}}, r};
            if (alt) begin
                got_i = q_alt;
                got_h = dut_alt.q;
            end else begin
                got_i = q;           // via this tb's signed net: checks the bits
                got_h = dut.q;       // via the DUT's own declaration: checks it is signed
            end
            checks = checks + 1;
            if (!alt && exp_i < 0) negatives = negatives + 1;
            if (got_i !== exp_i || got_h !== exp_i) begin
                errors = errors + 1;
                if (errors <= 6)
                    $display("  %0s, %0s edge: expected word %0d = %0d (0x%06h), got %0d (0x%06h), %0s.q as declared %0d",
                             alt ? "dut_alt (INIT=mem/expected.hex)" : "dut (default INIT)",
                             when ? "1 unit after the" : "1 unit before the",
                             a, exp_i, r, got_i, got_i[23:0], alt ? "dut_alt" : "dut", got_h);
            end
        end
    endtask

    initial begin
        $readmemh("mem/bias.hex", ref_mem);
        $readmemh("mem/expected.hex", ref_alt);

        // A missing or short file leaves X in the reference: refuse to run on it.
        for (i = 0; i < N; i = i + 1) begin
            if (^ref_mem[i] === 1'bx) begin
                $display("  reference word %0d is X: mem/bias.hex missing or short", i);
                errors = errors + 1;
            end
            if (^ref_alt[i] === 1'bx) begin
                $display("  reference word %0d is X: mem/expected.hex missing or short", i);
                errors = errors + 1;
            end
            if (ref_alt[i] !== ref_mem[i]) differ = differ + 1;
        end
        // If the two files agreed, the INIT check could not tell them apart.
        if (differ == 0) begin
            $display("  mem/expected.hex and mem/bias.hex agree on all 26 words: the INIT check proves nothing");
            errors = errors + 1;
        end

        for (i = 0; i < N; i = i + 1) begin
            seq[i]     = i;
            seq[N + i] = N - 1 - i;
        end

        // Rising edges at 10, 30, 50, ... Address seq[k] is driven at edge
        // E_k + 1. At E_{k+1} - 1 q must still show seq[k-1]'s word; at
        // E_{k+1} + 1 it must show seq[k]'s, and seq[k+1] is then driven.
        @(posedge clk);
        #1 addr = seq[0][4:0];
        for (k = 0; k < N_SEQ; k = k + 1) begin
            #18;                                     // E_{k+1} - 1
            if (k > 0) begin
                check_word(0, seq[k-1], 0);
                check_word(1, seq[k-1], 0);
            end
            #2;                                      // E_{k+1} + 1
            check_word(0, seq[k], 1);
            check_word(1, seq[k], 1);
            if (k + 1 < N_SEQ) addr = seq[k+1][4:0];
        end

        if (negatives == 0) begin
            $display("  no negative bias was checked: the signedness test proved nothing");
            errors = errors + 1;
        end
        if (checks != N_CHECKS) begin
            $display("  performed %0d checks, expected %0d", checks, N_CHECKS);
            errors = errors + 1;
        end

        $display("  %0d checks (%0d on negative words, %0d on the INIT=expected.hex instance), %0d errors",
                 checks, negatives, N_CHECKS / 2, errors);
        if (errors == 0) $display("PASS");
        else             $display("FAIL");
        $finish;
    end

endmodule

`default_nettype wire
