// tb_weight_rom -- self-checking testbench for rtl/weight_rom.v.
//
// Authored by Claude for projects/demo/ (Article I override, see README.md).
// Contract: ARCHITECTURE.md, "weight_rom".
//
// The expected contents are read from mem/weights.hex with $fscanf, not a
// second $readmemh, so the reference does not share the DUT's loading path.
//
// Checks, for every one of the 12,704 addresses (in order) and then for
// NRAND pseudo-random addresses (so a wrong latency cannot hide behind runs of
// equal neighbouring weights):
//   value   q one cycle after addr is presented equals the file's weight,
//           read as signed (-8..7)
//   latency q has NOT already changed when addr changes (catches a
//           combinational read); a 2-cycle read fails the value check
//   sign    the DUT's own q, read hierarchically, is < 0 exactly when the
//           hex digit is 8..F (catches q or the memory declared unsigned:
//           the tb's own wire is signed, so only dut.q can expose that)
// Every check is counted and the total must match what was planned, so a run
// that checks nothing (empty file, loop skipped) cannot print PASS.
//
// No `timescale: the RTL has none either, and delays here are only ordering
// (#1 = "just after the edge"), so absolute units do not matter.
`default_nettype none

module tb_weight_rom;

    localparam DEPTH = 12704;
    localparam NRAND = 4000;
    localparam MAXSHOW = 8;           // mismatch lines printed before going quiet

    reg               clk  = 1'b0;
    reg  [13:0]       addr = 14'd0;
    wire signed [3:0] q;

    weight_rom #(.DEPTH(DEPTH), .INIT("mem/weights.hex")) dut (
        .clk  (clk),
        .addr (addr),
        .q    (q)
    );

    // Second instance with NO parameter overrides, the way demo_top will
    // instantiate it. The explicit overrides above prove the parameter names;
    // this one proves the default values (a wrong default DEPTH or INIT
    // passes every check on `dut`, because the overrides hide it).
    wire signed [3:0] q_def;
    weight_rom dut_def (
        .clk  (clk),
        .addr (addr),
        .q    (q_def)
    );

    always #10 clk = ~clk;            // period 20 units (50 MHz if 1 unit = 1 ns)

    integer exp_w [0:DEPTH-1];        // expected weight, signed, -8..7
    integer fd, r, v, n_lines, n_neg_file;
    integer errors, n_value, n_hold, n_sign, n_neg_seen, n_def;
    integer k, a, prev_a;
    reg [15:0] lfsr;

    // One read: present a at a negedge, check q has not moved yet, then check
    // it just after the next posedge.
    task read_check(input integer a_now, input integer a_prev);
        begin
            @(negedge clk);
            addr = a_now[13:0];
            #1;
            if (a_prev >= 0) begin
                n_hold = n_hold + 1;
                if (q !== exp_w[a_prev][3:0]) begin
                    errors = errors + 1;
                    if (errors <= MAXSHOW)
                        $display("  mismatch: q changed before the clock edge (addr %0d -> %0d): q=%0d, still expected %0d",
                                 a_prev, a_now, q, exp_w[a_prev]);
                end
            end
            @(posedge clk);
            #1;
            n_value = n_value + 1;
            if (q !== exp_w[a_now][3:0] || $signed(q) != exp_w[a_now]) begin
                errors = errors + 1;
                if (errors <= MAXSHOW)
                    $display("  mismatch: addr %0d: q=%0d (4'h%h), expected %0d",
                             a_now, q, q, exp_w[a_now]);
            end
            n_sign = n_sign + 1;
            if ((dut.q < 0) != (exp_w[a_now] < 0)) begin
                errors = errors + 1;
                if (errors <= MAXSHOW)
                    $display("  mismatch: addr %0d: dut.q < 0 is %0d, expected %0d (dut.q declared unsigned?)",
                             a_now, (dut.q < 0), (exp_w[a_now] < 0));
            end
            if (dut.q < 0) n_neg_seen = n_neg_seen + 1;
            n_def = n_def + 1;
            if (q_def !== exp_w[a_now][3:0] || (dut_def.q < 0) != (exp_w[a_now] < 0)) begin
                errors = errors + 1;
                if (errors <= MAXSHOW)
                    $display("  mismatch: default-parameter instance, addr %0d: q=%0d (4'h%h), expected %0d",
                             a_now, q_def, q_def, exp_w[a_now]);
            end
        end
    endtask

    initial begin
        errors = 0; n_value = 0; n_hold = 0; n_sign = 0; n_neg_seen = 0; n_def = 0;

        // ---- port widths and default parameters, exactly as the contract ----
        // A wider port only draws a padding warning from iverilog (sim.sh does
        // not fail on it) and still reads correctly here, so check widths
        // directly: addr [13:0], q [3:0].
        if ($bits(dut.addr) != 14 || $bits(dut_def.addr) != 14) begin
            $display("addr is %0d bits, contract says [13:0]", $bits(dut.addr));
            errors = errors + 1;
        end
        if ($bits(dut.q) != 4 || $bits(dut_def.q) != 4) begin
            $display("q is %0d bits, contract says signed [3:0]", $bits(dut.q));
            errors = errors + 1;
        end
        if (dut_def.DEPTH != 12704) begin
            $display("default DEPTH is %0d, contract says 12704", dut_def.DEPTH);
            errors = errors + 1;
        end

        // ---- reference: parse the hex file independently ----
        n_lines = 0; n_neg_file = 0;
        fd = $fopen("mem/weights.hex", "r");
        if (fd == 0) begin
            $display("cannot open mem/weights.hex (cwd must be projects/demo/)");
            errors = errors + 1;
        end else begin
            while (!$feof(fd)) begin
                r = $fscanf(fd, " %h", v);
                if (r == 1) begin
                    if (n_lines < DEPTH) begin
                        if (v < 0 || v > 15) begin
                            $display("weights.hex line %0d: value %0d is not one hex digit", n_lines + 1, v);
                            errors = errors + 1;
                        end
                        exp_w[n_lines] = (v >= 8) ? v - 16 : v;
                        if (v >= 8) n_neg_file = n_neg_file + 1;
                    end
                    n_lines = n_lines + 1;
                end else if (r == 0) begin
                    // Icarus returns 0, not EOF, when only trailing whitespace
                    // is left; anything else here is real junk in the file.
                    r = $fgetc(fd);       // consume it so the loop cannot spin
                    if (r != -1) begin
                        $display("weights.hex: unparseable character 0x%h after %0d values", r[7:0], n_lines);
                        errors = errors + 1;
                    end
                end
            end
            $fclose(fd);
        end
        if (n_lines != DEPTH) begin
            $display("weights.hex has %0d values, expected %0d", n_lines, DEPTH);
            errors = errors + 1;
        end
        if (n_neg_file == 0) begin
            $display("weights.hex has no negative weights: the sign check would prove nothing");
            errors = errors + 1;
        end

        // ---- sequential sweep of every address ----
        if (n_lines == DEPTH) begin
            prev_a = -1;
            for (a = 0; a < DEPTH; a = a + 1) begin
                read_check(a, prev_a);
                prev_a = a;
            end

            // ---- pseudo-random addresses (16-bit maximal LFSR) ----
            lfsr = 16'hACE1;
            for (k = 0; k < NRAND; k = k + 1) begin
                lfsr = {lfsr[14:0], lfsr[15] ^ lfsr[13] ^ lfsr[12] ^ lfsr[10]};
                a = lfsr % DEPTH;
                read_check(a, prev_a);
                prev_a = a;
            end
        end

        $display("weight_rom: %0d value checks, %0d hold checks, %0d sign checks, %0d default-instance checks, %0d negative reads, %0d errors",
                 n_value, n_hold, n_sign, n_def, n_neg_seen, errors);

        // Plan: every address once plus NRAND random reads; the hold check
        // runs on every read but the first.
        if (n_value != DEPTH + NRAND || n_sign != DEPTH + NRAND || n_def != DEPTH + NRAND ||
            n_hold != DEPTH + NRAND - 1 || n_neg_seen < n_neg_file) begin
            $display("check count is wrong: the testbench did not do what it planned");
            errors = errors + 1;
        end

        if (errors == 0) $display("PASS");
        else             $display("FAIL");
        $finish;
    end

endmodule

`default_nettype wire
