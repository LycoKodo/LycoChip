`default_nettype none
// tb_hidden_buf -- self-checking testbench for hidden_buf (16 x 8, 1-cycle read).
//
// A scoreboard (model[]) mirrors what the buffer should hold. Inputs change on the
// falling edge; each read is checked twice:
//   * just after the falling edge, before the next rising edge: rdata must still hold
//     the PREVIOUS read's word. A combinational (0-cycle) read fails here, because the
//     new raddr is already applied.
//   * just after the rising edge: rdata must equal the word at the raddr presented
//     before that edge. A 2-cycle read fails here.
// Data patterns are distinct per address and flip every bit between pass 1 and pass 2,
// so address-decode, stuck-bit and missed-write bugs all change some checked value.
//
// Phases:
//   1. write all 16 addresses (pass-1 pattern)
//   2. read all 16 in a scrambled order, with we low and waddr/wdata wiggling
//      (proves a write needs we)
//   3. 16 cycles of write addr k (pass-2 pattern) and read a different addr same cycle
//   4. read all 16 back (descending) to prove every phase-3 write landed
//   5. raddr HELD on one address across a write to it: the read the cycle after the
//      write must return the new word, and so must a repeat read of the same address.
//      Phases 2-4 never read one address twice in a row, so a read register that only
//      reloads when raddr changes, or a write that lands a cycle late, passed them.
//      Contract-neutral: the collision cycle itself is not checked here.
//   6. same-address read and write in the same cycle returns the OLD word. The
//      contract does not specify this; the module header documents it, and Quartus
//      20.1 maps this RTL with READ_DURING_WRITE_MODE_MIXED_PORTS = OLD_DATA, so
//      simulation and hardware agree. A new-data bypass, or a registered address with
//      a combinational array read (output not registered), fails here.
//   7. read all 16 back (ascending): phases 5-6 wrote only their own addresses.
module tb_hidden_buf;

    // phases 2, 3, 4, 5 (4 addrs x 5), 6 (3 addrs x 6), 7 (see below)
    localparam integer EXPECTED_CHECKS = 31 + 32 + 32 + 20 + 18 + 32;

    reg        clk   = 1'b0;
    reg        we    = 1'b0;
    reg  [3:0] waddr = 4'd0;
    reg  [7:0] wdata = 8'd0;
    reg  [3:0] raddr = 4'd0;
    wire [7:0] rdata;

    hidden_buf dut (
        .clk  (clk),
        .we   (we),
        .waddr(waddr),
        .wdata(wdata),
        .raddr(raddr),
        .rdata(rdata)
    );

    always #5 clk = ~clk;

    reg  [7:0] model [0:15];
    integer    checks = 0;
    integer    errors = 0;
    integer    k;

    // State carried between reads for the "held until the edge" check.
    reg        have_prev = 1'b0;
    reg  [7:0] prev_want = 8'd0;
    reg  [3:0] prev_addr = 4'd0;

    function [7:0] pat1(input [3:0] a);
        pat1 = {a, ~a};
    endfunction

    function [7:0] pat2(input [3:0] a);
        pat2 = ~{a, ~a};
    endfunction

    // Phase 5 and 6 words: distinct per address, and differ from pat2 at every address
    // (low nibble a^A / a^3 vs a), so old and new words can always be told apart.
    function [7:0] pat3(input [3:0] a);
        pat3 = {a, a} ^ 8'h5A;
    endfunction

    function [7:0] pat4(input [3:0] a);
        pat4 = {a, a} ^ 8'hC3;
    endfunction

    // Phase 5/6 address lists (disjoint, so phase 6's old word is always pat2).
    function [3:0] p5addr(input integer n);
        case (n) 0: p5addr = 4'd2; 1: p5addr = 4'd9; 2: p5addr = 4'd14; default: p5addr = 4'd7; endcase
    endfunction

    function [3:0] p6addr(input integer n);
        case (n) 0: p6addr = 4'd5; 1: p6addr = 4'd0; default: p6addr = 4'd11; endcase
    endfunction

    reg [3:0] a5;

    task check(input [7:0] got, input [7:0] want, input integer is_hold, input [3:0] a);
        begin
            checks = checks + 1;
            if (got !== want) begin
                errors = errors + 1;
                if (errors <= 8)
                    $display("MISMATCH t=%0t %s raddr=%0d: rdata=%h expected %h",
                             $time, is_hold ? "(before edge, previous word held)" : "(after edge)",
                             a, got, want);
            end
        end
    endtask

    // One clock cycle: drive all inputs, check rdata is still the previous word,
    // clock, check rdata is the new word, then commit any write to the model.
    task cycle(input [3:0] ra, input w, input [3:0] wa, input [7:0] wd, input do_read);
        reg [7:0] want;
        begin
            @(negedge clk);
            we = w; waddr = wa; wdata = wd; raddr = ra;
            want = model[ra];
            if (do_read) begin
                #1;
                if (have_prev) check(rdata, prev_want, 1, prev_addr);
            end
            @(posedge clk);
            #1;
            if (do_read) begin
                check(rdata, want, 0, ra);
                prev_want = want; prev_addr = ra; have_prev = 1'b1;
            end
            if (w) model[wa] = wd;
        end
    endtask

    initial begin
        // Phase 1: write every address. No reads checked (memory starts unknown).
        for (k = 0; k < 16; k = k + 1)
            cycle(4'd0, 1'b1, k[3:0], pat1(k[3:0]), 1'b0);

        // Phase 2: 16 reads, 15 hold checks + 16 value checks = 31.
        // Order 3,10,1,8,... (7 is coprime to 16, so every address once).
        // we is low but waddr points at the word being read and wdata is junk.
        for (k = 0; k < 16; k = k + 1)
            cycle((k * 7 + 3) & 15, 1'b0, (k * 7 + 3) & 15, 8'hEE, 1'b1);

        // Phase 3: write addr k while reading addr k+5 (never equal). 32 checks.
        for (k = 0; k < 16; k = k + 1)
            cycle((k + 5) & 15, 1'b1, k[3:0], pat2(k[3:0]), 1'b1);

        // Phase 4: read back 15..0. 32 checks; every word must now be pass-2.
        for (k = 0; k < 16; k = k + 1)
            cycle(4'd15 - k[3:0], 1'b0, 4'd0, 8'd0, 1'b1);

        for (k = 0; k < 16; k = k + 1)
            if (model[k] !== pat2(k[3:0])) begin
                errors = errors + 1;
                $display("TB BUG: model[%0d] = %h, expected pass-2 pattern", k, model[k]);
            end

        // Phase 5: hold raddr on A across a write to A. 5 checks per address.
        for (k = 0; k < 4; k = k + 1) begin
            a5 = p5addr(k);
            cycle(a5, 1'b0, a5, 8'hEE, 1'b1);          // read A (old word): 2 checks
            cycle(a5, 1'b1, a5, pat3(a5), 1'b0);       // write A, raddr still A: unchecked
            have_prev = 1'b0;                          // collision result is phase 6's job
            cycle(a5, 1'b0, a5, 8'h11, 1'b1);          // raddr still A: new word. 1 check
            cycle(a5, 1'b0, 4'd0, 8'h00, 1'b1);        // repeat read of A: 2 checks
        end

        // Phase 6: same-address read and write in one cycle. 6 checks per address.
        // cycle() takes `want` before committing the write, so it expects the OLD word.
        for (k = 0; k < 3; k = k + 1) begin
            a5 = p6addr(k);
            cycle(a5, 1'b0, 4'd0, 8'h00, 1'b1);        // read A: old (pat2)
            cycle(a5, 1'b1, a5, pat4(a5), 1'b1);       // read+write A: still old
            cycle(a5, 1'b0, 4'd0, 8'h00, 1'b1);        // read A: now new (pat4)
        end

        // Phase 7: read back 0..15. 32 checks.
        for (k = 0; k < 16; k = k + 1)
            cycle(k[3:0], 1'b0, 4'd0, 8'd0, 1'b1);

        $display("hidden_buf: %0d checks, %0d errors (expected %0d checks)",
                 checks, errors, EXPECTED_CHECKS);
        if (errors == 0 && checks == EXPECTED_CHECKS)
            $display("PASS");
        else
            $display("FAIL");
        $finish;
    end

endmodule
`default_nettype wire
