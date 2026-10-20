// tb_seg7 -- exhaustive check of seg7 against the ARCHITECTURE.md table.
//
// What is checked, and why each check can fail:
//   - every one of the 32 input combinations {valid, digit}: seg_n and dig_n.
//     Compared with !==, so an X or Z output (e.g. a missing case arm) fails.
//   - valid=1, digit 0..9: the contract's hex table (C0 F9 A4 B0 99 92 82 F8 80 90).
//   - valid=0, any digit: 8'hBF. All 16 digits are tried, so a decoder that
//     ignores valid for some digits fails.
//   - valid=1, digit 10..15: 8'hFF (blank). This is seg7.v's own choice; the
//     contract leaves it open. Checking it pins the behaviour so it cannot
//     drift silently.
//   - dig_n == 4'b0000 in every combination.
//   - seg7 is combinational: there is no clock here, outputs are sampled 1 time
//     unit after the inputs change. A registered implementation cannot pass.
//   - the contract's hex table is cross-checked against a segment-by-segment
//     description of each digit (a..g, active low, dp off), built here without
//     reference to the hex values. If the two disagree the tb itself is wrong
//     and it FAILs.
//   - valid toggled on its own with digit held (1 -> 0 -> 1, for all 16
//     digits). The sweep above always changes digit in the same step as
//     valid, so a decoder sensitive only to digit (`always @(digit)`, which
//     Quartus would build correctly but Icarus would not) passed it whenever
//     the tb's initial digit was not 0. In the real design this case happens:
//     rst clears result_valid while the latched digit stays put.
//   - the number of DUT checks must be exactly 160 (64 from the sweep +
//     96 from the valid toggles); zero checks is a FAIL.
`default_nettype none

module tb_seg7;

    localparam N_CHECKS = 160;

    reg  [3:0] digit = 4'd0;
    reg        valid = 1'b0;
    wire [7:0] seg_n;
    wire [3:0] dig_n;

    seg7 dut (.digit(digit), .valid(valid), .seg_n(seg_n), .dig_n(dig_n));

    // The contract's table, typed from ARCHITECTURE.md.
    reg [7:0] table_hex [0:9];

    // The same digits described by which segments are lit. Bit k = segment
    // a..g for k = 0..6; 1 = lit (active high here, inverted when compared).
    reg [6:0] lit [0:9];

    integer errors     = 0;
    integer checks     = 0;
    integer tb_errors  = 0;
    integer v;
    integer d;
    reg [7:0] exp_seg;

    // Segment bit positions, for readability.
    localparam A = 0, B = 1, C = 2, D = 3, E = 4, F = 5, G = 6;

    // Wait 1 time unit, then compare seg_n and dig_n with the contract for the
    // current {valid, digit}. Two checks per call.
    task check_now;
        begin
            #1;
            if (!valid)          exp_seg = 8'hBF;
            else if (digit < 10) exp_seg = table_hex[digit];
            else                 exp_seg = 8'hFF;

            checks = checks + 1;
            if (seg_n !== exp_seg) begin
                errors = errors + 1;
                if (errors <= 5)
                    $display("  mismatch: valid=%0d digit=%0d seg_n=%02h expected %02h",
                             valid, digit, seg_n, exp_seg);
            end

            checks = checks + 1;
            if (dig_n !== 4'b0000) begin
                errors = errors + 1;
                if (errors <= 5)
                    $display("  mismatch: valid=%0d digit=%0d dig_n=%b expected 0000",
                             valid, digit, dig_n);
            end
        end
    endtask

    initial begin
        table_hex[0] = 8'hC0; table_hex[1] = 8'hF9; table_hex[2] = 8'hA4;
        table_hex[3] = 8'hB0; table_hex[4] = 8'h99; table_hex[5] = 8'h92;
        table_hex[6] = 8'h82; table_hex[7] = 8'hF8; table_hex[8] = 8'h80;
        table_hex[9] = 8'h90;

        lit[0] = (7'd1 << A) | (7'd1 << B) | (7'd1 << C) | (7'd1 << D) | (7'd1 << E) | (7'd1 << F);
        lit[1] = (7'd1 << B) | (7'd1 << C);
        lit[2] = (7'd1 << A) | (7'd1 << B) | (7'd1 << D) | (7'd1 << E) | (7'd1 << G);
        lit[3] = (7'd1 << A) | (7'd1 << B) | (7'd1 << C) | (7'd1 << D) | (7'd1 << G);
        lit[4] = (7'd1 << B) | (7'd1 << C) | (7'd1 << F) | (7'd1 << G);
        lit[5] = (7'd1 << A) | (7'd1 << C) | (7'd1 << D) | (7'd1 << F) | (7'd1 << G);
        lit[6] = (7'd1 << A) | (7'd1 << C) | (7'd1 << D) | (7'd1 << E) | (7'd1 << F) | (7'd1 << G);
        lit[7] = (7'd1 << A) | (7'd1 << B) | (7'd1 << C);
        lit[8] = 7'h7F;
        lit[9] = (7'd1 << A) | (7'd1 << B) | (7'd1 << C) | (7'd1 << D) | (7'd1 << F) | (7'd1 << G);

        // Sanity of the tb's own reference: dp off (bit 7 = 1), segments inverted.
        for (d = 0; d < 10; d = d + 1)
            if (table_hex[d] !== {1'b1, ~lit[d]}) begin
                tb_errors = tb_errors + 1;
                $display("  tb reference disagrees for digit %0d: table %02h, segments give %02h",
                         d, table_hex[d], {1'b1, ~lit[d]});
            end

        // Exhaustive sweep. Order valid=1 first, then 0, so the first
        // transition into !valid is also exercised from a lit digit.
        for (v = 1; v >= 0; v = v - 1)
            for (d = 0; d < 16; d = d + 1) begin
                valid = v[0];
                digit = d[3:0];
                check_now;
            end

        // valid alone changes, digit held: 1 -> 0 -> 1 for every digit.
        for (d = 0; d < 16; d = d + 1) begin
            digit = d[3:0];
            valid = 1'b1;
            check_now;
            valid = 1'b0;           // only valid changes here...
            check_now;
            valid = 1'b1;           // ...and here
            check_now;
        end

        $display("tb_seg7: %0d checks, %0d errors, %0d tb reference errors",
                 checks, errors, tb_errors);
        if (checks != N_CHECKS)
            $display("  expected exactly %0d checks", N_CHECKS);

        if (errors == 0 && tb_errors == 0 && checks == N_CHECKS)
            $display("PASS");
        else
            $display("FAIL");
        $finish;
    end

endmodule

`default_nettype wire
