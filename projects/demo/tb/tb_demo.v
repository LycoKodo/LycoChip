// tb_demo -- end-to-end test of demo_top, through its pins only.
//
// Authored by Claude for projects/demo/ (README.md: Article I override, this
// directory only). Contract: ARCHITECTURE.md, "demo_top" and "Verification".
//
// The testbench is the host: it drives rst_n and the uart_rx line bit by bit,
// and decodes uart_tx with its own UART receiver (written here, sharing no code
// with rtl/uart_rx.v). The expected results come from mem/expected.hex
// (host/make_mem.py, from the Python golden model), never from the RTL.
//
//   1. Power-up/reset: uart_tx idles high, display shows the dash (8'hBF),
//      led_n[2] (result_valid) is off, nothing is busy.
//   2. A garbage partial frame (A5 5A + 100 bytes), then silence longer than
//      TIMEOUT. It must be discarded: no reply, no inference (led_n[1] stays
//      off), receiving drops when the timeout expires. If it were not
//      discarded the first real frame would be mis-aligned and image 0 fails.
//   3. The 16 images of mem/test_images.hex, each A5 5A + 784 bytes. For each:
//      wait (with a watchdog) for exactly 22 reply bytes; compare 0xC3, the
//      digit and all 10 int16 scores with mem/expected.hex; check seg_n shows
//      the digit, dig_n = 0, led_n[2] on, led_n[1] off once the reply is out.
//   4. No stray bytes after the last reply.
//   5. Heartbeat: led_n[3] = ~counter[24]. 2^24 cycles is too long to wait
//      for, so the counter is preset just below the bit-24 edge (the one
//      hierarchical poke in this file) and the LED must turn on.
//   6. rst_n pressed again: display back to the dash, led_n[2] off.
//
// Small CLKS_PER_BIT (8) and TIMEOUT (4000) keep the run short; the logic is
// the same at 434 and 2,500,000 (unit tests cover those values).
`timescale 1ns/1ps
`default_nettype none

module tb_demo;

    localparam integer CPB      = 8;
    localparam integer TIMEOUT  = 4000;
    localparam integer N_IMG    = 16;
    localparam integer N_PIX    = 784;
    localparam integer N_REPLY  = 22;
    localparam integer WATCHDOG = 40000;    // cycles allowed per reply (needs ~14k + 22*83)

    reg clk     = 1'b0;
    reg rst_n   = 1'b0;
    reg line_rx = 1'b1;                     // host -> FPGA
    wire       line_tx;                     // FPGA -> host
    wire [3:0] led_n;
    wire [7:0] seg_n;
    wire [3:0] dig_n;

    always #10 clk = ~clk;                  // 50 MHz

    demo_top #(.CLKS_PER_BIT(CPB), .TIMEOUT(TIMEOUT)) dut (
        .clk     (clk),
        .rst_n   (rst_n),
        .uart_rx (line_rx),
        .uart_tx (line_tx),
        .led_n   (led_n),
        .seg_n   (seg_n),
        .dig_n   (dig_n)
    );

    // ---- reference data ---------------------------------------------------------
    reg  [7:0] img [0:N_IMG*N_PIX-1];
    reg [15:0] exp_w [0:N_IMG*11-1];        // per image: digit, then 10 scores

    // seg7 patterns (ARCHITECTURE.md "seg7"), tabulated independently of rtl/seg7.v.
    function [7:0] seg_pat(input [3:0] d);
        case (d)
            4'd0: seg_pat = 8'hC0; 4'd1: seg_pat = 8'hF9; 4'd2: seg_pat = 8'hA4;
            4'd3: seg_pat = 8'hB0; 4'd4: seg_pat = 8'h99; 4'd5: seg_pat = 8'h92;
            4'd6: seg_pat = 8'h82; 4'd7: seg_pat = 8'hF8; 4'd8: seg_pat = 8'h80;
            4'd9: seg_pat = 8'h90; default: seg_pat = 8'hXX;
        endcase
    endfunction

    integer errors = 0;
    task automatic err(input [8*120-1:0] msg);
        begin
            errors = errors + 1;
            $display("  ERROR @%0t: %0s", $time, msg);
        end
    endtask

    // ---- independent UART receiver on line_tx ----------------------------------
    // Waits for a falling edge, re-checks the start bit at its middle, samples
    // 8 data bits and the stop bit at their middles. A low stop bit is an error.
    reg [7:0] rx_bytes [0:1023];
    integer   rx_count = 0;
    integer   k;
    reg [7:0] b;
    initial begin : uart_monitor
        forever begin
            @(negedge line_tx);
            repeat (CPB/2) @(posedge clk);
            if (line_tx !== 1'b0) begin
                err("monitor: start bit not low at its middle (glitch on uart_tx)");
            end else begin
                for (k = 0; k < 8; k = k + 1) begin
                    repeat (CPB) @(posedge clk);
                    b[k] = line_tx;
                end
                repeat (CPB) @(posedge clk);
                if (line_tx !== 1'b1)
                    err("monitor: framing error (stop bit not high)");
                if (rx_count < 1024) rx_bytes[rx_count] = b;
                rx_count = rx_count + 1;
            end
        end
    end

    // ---- host-side sender ---------------------------------------------------------
    task automatic send_byte(input [7:0] v);
        integer n;
        begin
            line_rx = 1'b0;                     // start
            repeat (CPB) @(posedge clk);
            for (n = 0; n < 8; n = n + 1) begin
                line_rx = v[n];
                repeat (CPB) @(posedge clk);
            end
            line_rx = 1'b1;                     // stop
            repeat (CPB) @(posedge clk);
        end
    endtask

    // ---- main sequence ------------------------------------------------------------
    integer im, p, s, base, wd, digit_exp, best, seen_busy;
    reg signed [15:0] got_s, exp_s, best_s;
    reg [7:0] lo, hi;
    integer img_ok, n_ok;

    initial begin
        $readmemh("mem/test_images.hex", img);
        $readmemh("mem/expected.hex", exp_w);
        n_ok = 0;

        // Sanity of the reference itself: every expected digit is the argmax
        // (ties to the lower index) of its expected scores.
        for (im = 0; im < N_IMG; im = im + 1) begin
            best = 0; best_s = exp_w[im*11 + 1];
            for (s = 1; s < 10; s = s + 1)
                if ($signed(exp_w[im*11 + 1 + s]) > best_s) begin
                    best = s; best_s = exp_w[im*11 + 1 + s];
                end
            if (best !== exp_w[im*11]) err("expected.hex: digit is not argmax of its scores");
            if (^exp_w[im*11] === 1'bx || ^img[im*N_PIX] === 1'bx || ^img[(im+1)*N_PIX-1] === 1'bx)
                err("reference data not loaded (X in mem/*.hex)");
        end

        // 1. reset ------------------------------------------------------------------
        rst_n = 1'b0;
        repeat (20) @(posedge clk);
        rst_n = 1'b1;
        repeat (20) @(posedge clk);
        if (line_tx !== 1'b1) err("uart_tx not idle high after reset");
        if (seg_n !== 8'hBF)  err("seg_n not the dash before any result");
        if (dig_n !== 4'b0000) err("dig_n not all enabled");
        if (led_n[2] !== 1'b1) err("led_n[2] (result_valid) lit before any result");
        if (led_n[1] !== 1'b1) err("led_n[1] (busy) lit while idle");
        if (led_n[0] !== 1'b1) err("led_n[0] (receiving) lit while idle");
        if (^led_n === 1'bx)   err("led_n has X/Z");
        $display("reset: uart_tx=%b seg_n=%h dig_n=%b led_n=%b", line_tx, seg_n, dig_n, led_n);

        // 2. garbage partial frame, then silence > TIMEOUT -----------------------------
        send_byte(8'hA5);
        send_byte(8'h5A);
        for (p = 0; p < 100; p = p + 1)
            send_byte((p * 37 + 11) & 8'hFF);
        if (led_n[0] !== 1'b0) err("led_n[0] (receiving) not lit during a frame");
        seen_busy = 0;
        for (wd = 0; wd < TIMEOUT + 2000; wd = wd + 1) begin
            @(posedge clk);
            if (led_n[1] === 1'b0) seen_busy = 1;
        end
        if (led_n[0] !== 1'b1) err("partial frame: still receiving after TIMEOUT of silence");
        if (seen_busy)          err("partial frame started an inference (led_n[1] lit)");
        if (rx_count != 0)      err("partial frame produced reply bytes");
        $display("garbage frame (A5 5A + 100 bytes) + %0d idle cycles: receiving=%0d busy_seen=%0d bytes_out=%0d",
                 TIMEOUT + 2000, !led_n[0], seen_busy, rx_count);

        // 3. the 16 images ----------------------------------------------------------------
        for (im = 0; im < N_IMG; im = im + 1) begin
            base = rx_count;
            send_byte(8'hA5);
            send_byte(8'h5A);
            for (p = 0; p < N_PIX; p = p + 1)
                send_byte(img[im*N_PIX + p]);

            wd = 0;
            while (rx_count < base + N_REPLY && wd < WATCHDOG) begin
                @(posedge clk);
                wd = wd + 1;
            end

            img_ok = 1;
            digit_exp = exp_w[im*11];
            if (rx_count != base + N_REPLY) begin
                err("watchdog: reply incomplete");
                $display("  image %0d: %0d of %0d reply bytes after %0d cycles", im, rx_count - base, N_REPLY, wd);
                img_ok = 0;
            end else begin
                if (rx_bytes[base] !== 8'hC3) begin
                    err("bad sync byte"); img_ok = 0;
                    $display("  image %0d: sync %h, expected c3", im, rx_bytes[base]);
                end
                if (rx_bytes[base+1] !== digit_exp[7:0]) begin
                    err("digit mismatch"); img_ok = 0;
                    $display("  image %0d: digit %0d, expected %0d", im, rx_bytes[base+1], digit_exp);
                end
                for (s = 0; s < 10; s = s + 1) begin
                    lo = rx_bytes[base + 2 + 2*s];
                    hi = rx_bytes[base + 3 + 2*s];
                    got_s = {hi, lo};
                    exp_s = exp_w[im*11 + 1 + s];
                    if (got_s !== exp_s) begin
                        err("score mismatch"); img_ok = 0;
                        $display("  image %0d: score[%0d] = %0d, expected %0d", im, s, got_s, exp_s);
                    end
                end
            end
            // The display updates on `send`, before the first byte goes out.
            if (seg_n !== seg_pat(digit_exp[3:0])) begin
                err("seg_n does not show the digit"); img_ok = 0;
                $display("  image %0d: seg_n %h, expected %h", im, seg_n, seg_pat(digit_exp[3:0]));
            end
            if (dig_n !== 4'b0000) begin err("dig_n not all enabled"); img_ok = 0; end
            if (led_n[2] !== 1'b0) begin err("led_n[2] (result_valid) not lit after a result"); img_ok = 0; end
            // The 22nd stop bit is sampled at its middle; busy falls a few
            // cycles after the stop bit ends.
            repeat (CPB) @(posedge clk);
            if (led_n[1] !== 1'b1) begin err("led_n[1] (busy) still lit after the reply"); img_ok = 0; end

            if (img_ok) n_ok = n_ok + 1;
            $display("image %2d: digit %0d (expected %0d), %0d bytes, seg_n=%h  %0s",
                     im, rx_bytes[base+1], digit_exp, rx_count - base, seg_n, img_ok ? "ok" : "MISMATCH");
        end

        // 4. nothing more comes out ------------------------------------------------------
        repeat (20 * 10 * CPB) @(posedge clk);
        if (rx_count != N_IMG * N_REPLY) begin
            err("stray bytes after the last reply");
            $display("  %0d bytes received, expected %0d", rx_count, N_IMG * N_REPLY);
        end

        // 5. heartbeat --------------------------------------------------------------------
        @(negedge clk);
        dut.hb = 25'h0FF_FFF0;              // bit 24 is 0: LED off
        @(posedge clk); #1;
        if (led_n[3] !== 1'b1) err("led_n[3] lit with heartbeat bit 24 = 0");
        repeat (20) @(posedge clk); #1;
        if (led_n[3] !== 1'b0) err("led_n[3] not lit after heartbeat bit 24 rose");
        $display("heartbeat: led_n[3] off below the bit-24 edge, on after it");

        // 6. reset clears the result ------------------------------------------------------
        rst_n = 1'b0;
        repeat (5) @(posedge clk);
        if (seg_n !== 8'hBF)   err("rst_n did not clear the display");
        if (led_n[2] !== 1'b1) err("rst_n did not clear led_n[2] (result_valid)");
        rst_n = 1'b1;
        repeat (5) @(posedge clk);

        $display("%0d of %0d images matched mem/expected.hex bit for bit; %0d error(s)",
                 n_ok, N_IMG, errors);
        if (errors == 0 && n_ok == N_IMG) $display("PASS");
        else                              $display("FAIL");
        $finish;
    end

    // Global watchdog: the whole run is ~1.3M cycles.
    initial begin
        #(64'd20 * 3_000_000);
        $display("global watchdog expired");
        $display("FAIL");
        $finish;
    end

endmodule

`default_nettype wire
