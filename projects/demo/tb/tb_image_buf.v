// tb_image_buf -- self-checking testbench for rtl/image_buf.v.
//
// What it proves (ARCHITECTURE.md, image_buf):
//   1. Every one of the 784 addresses stores its own byte (no aliasing between
//      addresses), using two different data patterns so a stale or stuck word shows.
//   2. Read latency is exactly one cycle: the value checked after edge c+1 must be
//      mem[raddr presented in cycle c] (catches 2-cycle reads), and rdata must NOT
//      change when raddr changes between edges (catches a combinational read).
//   3. A read and a write to different addresses in the same cycle both work.
//   4. A word written at edge c is returned by a read captured at edge c+1.
//   5. A long random mix of reads and writes agrees with a reference model.
//   6. we = 0 really blocks the write (the write port is aimed at the next word to be
//      read, with wrong data, while we is low).
//   7. Same-address read-during-write returns the OLD word, and the new word one cycle
//      later. ARCHITECTURE.md does not specify this case. It is checked because Quartus
//      20.1 maps this RTL to altsyncram with READ_DURING_WRITE_MODE_MIXED_PORTS =
//      OLD_DATA (quartus_map report, 2026-10-20 review), so this pins simulation to what
//      the silicon does. A bypass, a blocking write or a write that is not edge-triggered
//      breaks it.
//
// Timing discipline (no `timescale; delays are in relative units; clock period 10):
//   +1  inputs go to GARBAGE (random we/addresses/data), as upstream combinational
//       logic may glitch after an edge. A correct design ignores everything except
//       the values present at the rising edge.
//   +2  hold check 1: rdata unchanged (catches a combinational or latch read).
//   +6  inputs settle to the real values (after the falling edge at +5, so a
//       negedge-sampled write or read sees garbage and fails).
//   +9  hold check 2: rdata still unchanged at the end of the cycle, where a consumer
//       samples it (catches a read clocked on the falling edge).
//   +11 read check: rdata equals the word at the address settled before the edge.
//
// Cannot pass vacuously: read checks and hold checks are counted and must equal the
// numbers this stimulus is built to perform.
`default_nettype none

module tb_image_buf;

    localparam N          = 784;
    localparam N_WR_PAIRS = 16;
    localparam N_RANDOM   = 4000;
    localparam N_RDW      = 16;
    // read checks: read-back A + simultaneous pass B + write-then-read
    //              + same-address RDW (old, then new) + random + final
    localparam EXP_READ_CHECKS = N + N + N_WR_PAIRS + 2*N_RDW + N_RANDOM + N;
    // steps: write A + read A + pass B + 2 per pair + 2 per RDW + random + final
    localparam N_STEPS = N + N + N + 2*N_WR_PAIRS + 2*N_RDW + N_RANDOM + N;
    // two hold checks per step (+2 and +9)
    localparam EXP_HOLD_CHECKS = 2 * N_STEPS;

    reg        clk = 1'b0;
    reg        we = 1'b0;
    reg  [9:0] waddr = 10'd0;
    reg  [7:0] wdata = 8'd0;
    reg  [9:0] raddr = 10'd0;
    wire [7:0] rdata;

    image_buf dut (
        .clk(clk), .we(we), .waddr(waddr), .wdata(wdata),
        .raddr(raddr), .rdata(rdata)
    );

    always #5 clk = ~clk;

    reg [7:0] model [0:N-1];   // what the buffer should hold

    integer errors = 0;
    integer read_checks = 0;
    integer hold_checks = 0;
    integer seed = 32'h1CE5EED;
    integer gseed = 32'h0BADF00D;  // garbage stimulus; separate so phase 5 is unchanged

    // Pattern A: low address byte XOR the top two address bits replicated. Linear in
    // the address bits, so any two addresses differing in one address bit get
    // different data -> a dropped or stuck address bit shows up as aliasing.
    function [7:0] pat_a;
        input [9:0] a;
        pat_a = a[7:0] ^ {4{a[9:8]}};
    endfunction

    // Pattern B: non-linear and different from A at most addresses, so pass B
    // overwriting A is visible, and so aliases A cannot see are covered too.
    function [7:0] pat_b;
        input [9:0] a;
        reg [15:0] t;
        begin
            t     = a * 16'd37 + {6'd0, a[9:8], 8'd0} + 16'h5C;
            pat_b = t[7:0] ^ t[15:8] ^ 8'hA6;
        end
    endfunction

    // One clock cycle.
    //   w/wa/wd : write port for this cycle (settled value)
    //   ra      : read address presented this cycle (settled value)
    //   chk     : compare rdata after the next edge against model[ra]
    // The hold checks: rdata was sampled just after the previous edge; it must not
    // move again until the next rising edge, whatever the inputs do in between.
    reg [7:0] held;
    reg [7:0] expv;
    reg       expect_on;
    integer   g;
    task step;
        input       w;
        input [9:0] wa;
        input [7:0] wd;
        input [9:0] ra;
        input       chk;
        begin
            held = rdata;
            // +1: garbage. we is driven high half the time, so anything that writes
            // outside the rising edge corrupts a word.
            g = $random(gseed); we    = g[0];
            g = $random(gseed); waddr = (g & 32'h7FFFFFFF) % N;
            g = $random(gseed); wdata = g[7:0];
            g = $random(gseed); raddr = (g & 32'h7FFFFFFF) % N;
            #1;  // +2
            hold_checks = hold_checks + 1;
            if (rdata !== held) begin
                errors = errors + 1;
                if (errors <= 8)
                    $display("  hold   t=%0t raddr=%0d: rdata changed %02h -> %02h between edges (read not registered)",
                             $time, ra, held, rdata);
            end
            #4;  // +6: after the falling edge, settle to the real values
            we = w; waddr = wa; wdata = wd; raddr = ra;
            #3;  // +9: end of the cycle, where a consumer samples rdata
            hold_checks = hold_checks + 1;
            if (rdata !== held) begin
                errors = errors + 1;
                if (errors <= 8)
                    $display("  hold   t=%0t raddr=%0d: rdata changed %02h -> %02h mid-cycle (not held for the whole cycle)",
                             $time, ra, held, rdata);
            end
            // Expected value is the memory as it stands BEFORE this edge's write: for
            // ra != wa the order is moot; for ra == wa this is old-data read-during-
            // write, which is what Quartus builds from this RTL (see header).
            expect_on = chk;
            expv      = model[ra];
            if (w) model[wa] = wd;
            @(posedge clk); #1;
            if (expect_on) begin
                read_checks = read_checks + 1;
                if (rdata !== expv) begin
                    errors = errors + 1;
                    if (errors <= 8)
                        $display("  read   t=%0t raddr=%0d: got %02h, expected %02h", $time, ra, rdata, expv);
                end
            end
        end
    endtask

    integer a, k, r;
    reg [9:0] rw, rr;
    reg       rwe;

    initial begin
        // Align to just after a rising edge, the point every step starts from.
        @(posedge clk); #1;

        // 1. Write pattern A to all 784 addresses (no reads checked: nothing written yet).
        for (a = 0; a < N; a = a + 1)
            step(1'b1, a[9:0], pat_a(a[9:0]), 10'd0, 1'b0);

        // 2. Read every address back in order. Consecutive words differ, so a
        //    2-cycle read returns the previous address's byte and fails here.
        //    The write port, with we LOW, points at the NEXT word to be read with
        //    inverted data: if we is ignored, the next read returns the wrong byte.
        for (a = 0; a < N; a = a + 1)
            step(1'b0, ((a + 1) % N), ~model[(a + 1) % N], a[9:0], 1'b1);

        // 3. Overwrite with pattern B while reading the address 392 away in the same
        //    cycle. For a < 392 the read address is not yet rewritten (expects A);
        //    for a >= 392 it was rewritten 392 cycles earlier (expects B).
        for (a = 0; a < N; a = a + 1)
            step(1'b1, a[9:0], pat_b(a[9:0]), ((a + N/2) % N), 1'b1);

        // 4. Write at edge c, read it with the address captured at edge c+1.
        for (k = 0; k < N_WR_PAIRS; k = k + 1) begin
            a = (k * 97 + 5) % N;
            step(1'b1, a[9:0], ~model[a] ^ k[7:0], ((a + 1) % N), 1'b0);
            step(1'b0, 10'd0, 8'd0, a[9:0], 1'b1);
        end

        // 4b. Same-address read-during-write: write a new byte to address a while
        //     reading a in the same cycle (expects the OLD byte), then read a again
        //     (expects the NEW byte).
        for (k = 0; k < N_RDW; k = k + 1) begin
            a = (k * 211 + 17) % N;
            step(1'b1, a[9:0], ~model[a] ^ (8'h3C + k[7:0]), a[9:0], 1'b1);
            step(1'b0, 10'd0, 8'd0, a[9:0], 1'b1);
        end

        // 5. Random mix. Every address has been written, so every read is checkable.
        for (k = 0; k < N_RANDOM; k = k + 1) begin
            r   = $random(seed);
            rwe = r[0];
            r   = $random(seed); rw = (r & 32'h7FFFFFFF) % N;
            r   = $random(seed); rr = (r & 32'h7FFFFFFF) % N;
            if (rwe && rr == rw) rr = (rr + 1) % N;
            r   = $random(seed);
            step(rwe, rw, r[7:0], rr, 1'b1);
        end

        // 6. Final full read-back of the state the random phase left.
        for (a = 0; a < N; a = a + 1)
            step(1'b0, 10'd0, 8'd0, a[9:0], 1'b1);

        $display("tb_image_buf: %0d read checks (expected %0d), %0d hold checks (expected %0d), %0d errors",
                 read_checks, EXP_READ_CHECKS, hold_checks, EXP_HOLD_CHECKS, errors);
        if (errors == 0 && read_checks == EXP_READ_CHECKS && hold_checks == EXP_HOLD_CHECKS)
            $display("PASS");
        else
            $display("FAIL");
        $finish;
    end

endmodule

`default_nettype wire
