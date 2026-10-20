// tb_uart_rx -- self-checking testbench for uart_rx (ARCHITECTURE.md).
// Authored by Claude (projects/demo/ override; not Alex's work).
//
// Two instances: CLKS_PER_BIT = 16 (fast, used for the exhaustive run) and
// 434 (the real 115,200-baud setting). The serial line is driven in real time
// (ns), not on clock edges, and starts at an odd phase, so edges land between
// clocks as they do on hardware.
//
// What is checked:
//   - all 256 byte values back to back at 16 clocks/bit: each arrives once,
//     in order, with the right value;
//   - all 256 again with the sender 3 % slow, and again 3 % fast. A receiver
//     that samples mid-bit tolerates this easily; one whose sample point or
//     bit period is off by a clock or so (at 16 clocks/bit, 6 %) does not;
//   - a handful of bytes at 434 clocks/bit, including +/-2 % baud error;
//   - a glitch (low for less than half a bit) produces no byte, and the
//     receiver still works afterwards;
//   - a frame whose stop bit is low produces no byte, and the receiver still
//     works afterwards;
//   - `valid` is never high two cycles in a row;
//   - `data` never changes except in a cycle where `valid` is high;
//   - every expected byte has been delivered by the end of its stop bit;
//   - a glitch only just shorter than half a bit (7 of 16 clocks, 216 of 434)
//     and a one-clock glitch are both ignored;
//   - a long break (line held low for many bit times) produces no byte, before
//     or after the line is released, and the receiver works afterwards. A
//     receiver that goes straight back to IDLE after a low stop bit fails
//     this: it keeps framing the held-low line, and when the line is released
//     mid-"frame" the trailing 1s and a high "stop bit" deliver a garbage byte;
//   - the 434 instance uses the module's default CLKS_PER_BIT, and the test
//     checks that default is 434 (the contract value), since a 0.2 % baud
//     error would not show up functionally.
// A scoreboard per instance holds the bytes it should deliver; any extra,
// missing or wrong byte is an error. The number of byte checks must equal
// EXPECTED_CHECKS, so a run that checks nothing cannot PASS.
`timescale 1ns/1ps
`default_nettype none

module tb_uart_rx;

    localparam real CLK_NS = 20.0;          // 50 MHz
    localparam integer EXPECTED_CHECKS = (3 * 256 + 1 + 1 + 4)    // CLKS_PER_BIT = 16
                                       + (6 + 4 + 1 + 1 + 3);     // CLKS_PER_BIT = 434

    reg clk = 1'b0;
    always #(CLK_NS / 2.0) clk = ~clk;

    // Two serial lines, two receivers.
    reg        rx16  = 1'b1;
    reg        rx434 = 1'b1;
    wire [7:0] d16,  d434;
    wire       v16,  v434;

    uart_rx #(.CLKS_PER_BIT(16))  u16  (.clk(clk), .rx(rx16),  .data(d16),  .valid(v16));
    // No parameter override: this instance runs at the module's default, which
    // the stimulus checks is the contract's 434.
    uart_rx                       u434 (.clk(clk), .rx(rx434), .data(d434), .valid(v434));

    integer errors = 0;
    integer checks = 0;

    // ---------------------------------------------------------------- scoreboards
    reg [7:0] exp16  [0:1023];
    reg [7:0] exp434 [0:63];
    integer wp16 = 0, rp16 = 0, wp434 = 0, rp434 = 0;

    task report(input [8*64-1:0] msg);
        begin
            errors = errors + 1;
            if (errors <= 10) $display("  ERROR @%0t ns: %0s", $time, msg);
        end
    endtask

    // Previous-cycle values, for the pulse-width and data-hold checks.
    reg       pv16 = 1'b0, pv434 = 1'b0;
    reg [7:0] pd16 = 8'h00, pd434 = 8'h00;

    always @(posedge clk) begin
        #1;   // sample after the DUT's nonblocking updates for this edge

        // -- 16 clocks/bit instance
        if (v16) begin
            if (pv16) report("v16: valid high two cycles in a row");
            if (rp16 >= wp16) begin
                errors = errors + 1;
                if (errors <= 10) $display("  ERROR @%0t ns: v16 unexpected byte %02h (nothing pending)", $time, d16);
            end else begin
                checks = checks + 1;
                if (d16 !== exp16[rp16]) begin
                    errors = errors + 1;
                    if (errors <= 10) $display("  ERROR @%0t ns: v16 byte #%0d got %02h expected %02h",
                                               $time, rp16, d16, exp16[rp16]);
                end
                rp16 = rp16 + 1;
            end
        end else if (d16 !== pd16)
            report("d16: data changed without valid");
        pv16 = v16;
        pd16 = d16;

        // -- 434 clocks/bit instance
        if (v434) begin
            if (pv434) report("v434: valid high two cycles in a row");
            if (rp434 >= wp434) begin
                errors = errors + 1;
                if (errors <= 10) $display("  ERROR @%0t ns: v434 unexpected byte %02h (nothing pending)", $time, d434);
            end else begin
                checks = checks + 1;
                if (d434 !== exp434[rp434]) begin
                    errors = errors + 1;
                    if (errors <= 10) $display("  ERROR @%0t ns: v434 byte #%0d got %02h expected %02h",
                                               $time, rp434, d434, exp434[rp434]);
                end
                rp434 = rp434 + 1;
            end
        end else if (d434 !== pd434)
            report("d434: data changed without valid");
        pv434 = v434;
        pd434 = d434;
    end

    // ---------------------------------------------------------------- line drivers
    task set_line(input integer sel, input val);
        begin
            if (sel == 16) rx16 = val; else rx434 = val;
        end
    endtask

    // One 8N1 frame on line `sel`, each bit `bit_ns` long. stop_hi = 0 sends a
    // low stop bit (framing error); the line is returned high afterwards.
    // A good frame is pushed onto the scoreboard before it is sent.
    task send(input integer sel, input [7:0] b, input stop_hi, input real bit_ns);
        integer i;
        begin
            if (stop_hi) begin
                if (sel == 16) begin exp16[wp16]   = b; wp16  = wp16  + 1; end
                else           begin exp434[wp434] = b; wp434 = wp434 + 1; end
            end
            set_line(sel, 1'b0);                 // start bit
            #(bit_ns);
            for (i = 0; i < 8; i = i + 1) begin  // data, LSB first
                set_line(sel, b[i]);
                #(bit_ns);
            end
            set_line(sel, stop_hi);              // stop bit
            #(bit_ns);
            set_line(sel, 1'b1);
        end
    endtask

    // By the end of a frame's stop bit, every byte sent so far must be out.
    task expect_caught_up(input integer sel);
        begin
            if (sel == 16 && rp16 != wp16) begin
                errors = errors + 1;
                if (errors <= 10) $display("  ERROR @%0t ns: v16 late/missing: %0d of %0d bytes delivered",
                                           $time, rp16, wp16);
                rp16 = wp16;    // resynchronise so one loss is not reported 200 times
            end
            if (sel == 434 && rp434 != wp434) begin
                errors = errors + 1;
                if (errors <= 10) $display("  ERROR @%0t ns: v434 late/missing: %0d of %0d bytes delivered",
                                           $time, rp434, wp434);
                rp434 = wp434;
            end
        end
    endtask

    task send_check(input integer sel, input [7:0] b, input real bit_ns);
        begin
            send(sel, b, 1'b1, bit_ns);
            expect_caught_up(sel);
        end
    endtask

    // A low pulse of `low_ns` then idle for `idle_ns`; must produce nothing.
    task glitch(input integer sel, input real low_ns, input real idle_ns);
        begin
            set_line(sel, 1'b0);
            #(low_ns);
            set_line(sel, 1'b1);
            #(idle_ns);
            expect_caught_up(sel);   // nothing was pushed, so any byte was extra
        end
    endtask

    // ---------------------------------------------------------------- stimulus
    real    b16, b434;
    integer k;
    reg [7:0] pat [0:5];

    initial begin
        b16  = 16.0  * CLK_NS;
        b434 = 434.0 * CLK_NS;
        pat[0] = 8'h00; pat[1] = 8'hFF; pat[2] = 8'h55;
        pat[3] = 8'hAA; pat[4] = 8'hA5; pat[5] = 8'h5A;

        // Odd phase so line edges fall between clock edges; long idle first.
        #(7.3);
        #(20 * b16);

        // ---- 16 clocks/bit: all 256 values, back to back (no idle between frames)
        for (k = 0; k < 256; k = k + 1)
            send_check(16, k[7:0], b16);
        #(3 * b16);

        // ---- 16 clocks/bit, +/-3 % baud error, all 256 values back to back
        for (k = 0; k < 256; k = k + 1)
            send_check(16, k[7:0], b16 * 1.03);
        #(3 * b16);
        for (k = 0; k < 256; k = k + 1)
            send_check(16, k[7:0], b16 * 0.97);
        #(3 * b16);

        // Glitch: low for 6 clocks, shorter than half a bit (8 clocks).
        glitch(16, 6.0 * CLK_NS, 12 * b16);
        send_check(16, 8'h3C, b16);
        #(2 * b16);

        // Low stop bit: frame must be dropped; receiver must still work after.
        send(16, 8'h81, 1'b0, b16);
        #(12 * b16);
        expect_caught_up(16);
        send_check(16, 8'hC3, b16);
        #(2 * b16);

        // Glitches at the edge of the window: 7 clocks (half a bit is 8), and 1.
        glitch(16, 7.0 * CLK_NS, 12 * b16);
        glitch(16, 1.0 * CLK_NS, 12 * b16);
        send_check(16, 8'h99, b16);
        #(2 * b16);

        // Long breaks: line held low, then released. No byte at any point.
        // Two lengths, so the release cannot happen to fall in the short
        // window where a re-framing receiver would reject it at a start check.
        glitch(16, 25.3 * b16, 15 * b16);
        send_check(16, 8'h5A, b16);
        #(2 * b16);
        glitch(16, 31.7 * b16, 15 * b16);
        send_check(16, 8'hA5, b16);
        #(2 * b16);
        // A low-stop frame that runs straight into a break.
        send(16, 8'hF0, 1'b0, b16);
        set_line(16, 1'b0);
        #(20.4 * b16);
        set_line(16, 1'b1);
        #(15 * b16);
        expect_caught_up(16);
        send_check(16, 8'h0F, b16);
        #(2 * b16);

        // ---- 434 clocks/bit
        #(2 * b434);
        for (k = 0; k < 6; k = k + 1)
            send_check(434, pat[k], b434);
        // +/-2 % baud error (sender slow, then fast), back to back.
        send_check(434, 8'h96, b434 * 1.02);
        send_check(434, 8'h69, b434 * 1.02);
        send_check(434, 8'hE7, b434 * 0.98);
        send_check(434, 8'h18, b434 * 0.98);
        #(2 * b434);

        // Glitch: 200 clocks low, shorter than half a bit (217).
        glitch(434, 200.0 * CLK_NS, 12 * b434);
        send_check(434, 8'h42, b434);
        #(2 * b434);

        send(434, 8'h7E, 1'b0, b434);
        #(12 * b434);
        expect_caught_up(434);
        send_check(434, 8'hBD, b434);
        #(2 * b434);

        // Glitch just shorter than half a bit (217 clocks).
        glitch(434, 216.0 * CLK_NS, 12 * b434);
        send_check(434, 8'hDB, b434);
        #(2 * b434);

        // Long breaks.
        glitch(434, 23.4 * b434, 15 * b434);
        send_check(434, 8'h24, b434);
        #(2 * b434);
        glitch(434, 30.6 * b434, 15 * b434);
        send_check(434, 8'h66, b434);
        #(2 * b434);

        // The default CLKS_PER_BIT must be the contract's 434.
        if (u434.CLKS_PER_BIT != 434) begin
            errors = errors + 1;
            $display("  ERROR: uart_rx default CLKS_PER_BIT is %0d, contract says 434", u434.CLKS_PER_BIT);
        end

        // ---- verdict
        if (checks != EXPECTED_CHECKS) begin
            errors = errors + 1;
            $display("  ERROR: %0d byte checks performed, expected %0d", checks, EXPECTED_CHECKS);
        end
        if (wp16 + wp434 != EXPECTED_CHECKS) begin
            errors = errors + 1;
            $display("  ERROR: %0d bytes queued, expected %0d (testbench bug)", wp16 + wp434, EXPECTED_CHECKS);
        end
        $display("tb_uart_rx: %0d byte checks, %0d errors", checks, errors);
        if (errors == 0) $display("PASS");
        else             $display("FAIL");
        $finish;
    end

endmodule

`default_nettype wire
