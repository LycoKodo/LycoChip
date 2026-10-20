// tb_uart_tx -- self-checking testbench for uart_tx (CLKS_PER_BIT = 16).
//
// Authored by Claude (projects/demo/ override; not Alex's work). Contract:
// projects/demo/ARCHITECTURE.md, "uart_tx".
//
// Two independent checkers watch the DUT's outputs:
//
//   1. A cycle-exact model of the contract. Every cycle it predicts `tx` and
//      `busy` from nothing but the testbench's own record of which `start` it
//      should have accepted: `start` in cycle c with the model idle -> start bit
//      in c+1 .. c+16, data bit k (LSB first) in the next 16-cycle slots, stop
//      bit in c+145 .. c+160, `busy` high in exactly c+1 .. c+160, and `tx`
//      high whenever idle. Any off-by-one in bit length, bit order, busy
//      timing, or an accepted start-while-busy shows up as a mismatch.
//
//   2. A UART decoder like a real receiver's: finds the falling edge of the
//      start bit and samples every bit at its middle. It checks start = 0 and
//      stop = 1 and compares the byte with the one the model says was sent.
//      It also checks that the falling edge comes exactly one cycle after the
//      accepted `start`.
//
// Stimulus:
//   A. All 256 byte values, one frame each. Each frame starts after a
//      pseudo-random idle gap, sometimes 0: `start` in the first cycle busy is
//      low. During each frame, `data` changes every cycle (the DUT must have
//      latched it) and one extra `start` pulse lands while busy, sometimes in
//      the very last busy cycle. That pulse must be ignored.
//   B. `start` held high for N_BACK frames with `data` changing every cycle:
//      frames must follow back to back, each sending the byte present in its
//      accepting cycle.
//   Then 3 frame-lengths of silence: nothing more may be sent.
//
// Also checked: `tx` only ever changes at a rising clock edge (a registered
// output, not a combinational path from `start`).
//
// Not vacuous: PASS requires exactly the expected number of accepted, decoded
// and ignored starts, every byte value 0..255 decoded in phase A, and at least
// a frame's worth of per-cycle checks for every frame.
//
// Other bit lengths (module tb_uart_tx_cpb, below, run in parallel): 16 is a
// power of two, so at 16 a bit counter that just wraps at 2^CW is
// indistinguishable from one that compares against CLKS_PER_BIT-1 -- and at
// the real 434 that wrong counter gives 512-cycle bits (97.7 kbaud, 15 % off).
// The same cycle-exact model is therefore also run against its own DUT at
//   - 434 with NO parameter override (the real default, 115,200 baud),
//   - 13 and 3 (not powers of two), and 2 (the documented minimum),
// each with fixed and random bytes, ignored starts (half of them in the last
// busy cycle, followed by a start in the very next cycle) and back-to-back
// frames with `start` held high.
// No `timescale: the RTL has none, and delays here are only relative.
`default_nettype none

module tb_uart_tx;

    localparam integer CPB      = 16;
    localparam integer FRAME    = 10 * CPB;     // cycles from start bit to end of stop bit
    localparam integer N_A      = 256;
    localparam integer N_BACK   = 8;
    localparam integer N_FRAMES = N_A + N_BACK;
    localparam integer MAX_SHOW = 8;            // mismatches printed in full

    reg        clk   = 1'b0;
    reg  [7:0] data  = 8'h00;
    reg        start = 1'b0;
    wire       tx;
    wire       busy;

    always #10 clk = ~clk;                      // period 20 time units

    uart_tx #(.CLKS_PER_BIT(CPB)) dut (
        .clk(clk), .data(data), .start(start), .tx(tx), .busy(busy)
    );

    // Other bit lengths, each with its own DUT and model (see header).
    tb_uart_tx_cpb #(.CPB(434), .DEFAULT(1)) h434 (.clk(clk));
    tb_uart_tx_cpb #(.CPB(13))               h13  (.clk(clk));
    tb_uart_tx_cpb #(.CPB(3))                h3   (.clk(clk));
    tb_uart_tx_cpb #(.CPB(2))                h2   (.clk(clk));

    integer errors = 0;
    integer checks = 0;                         // per-cycle tx+busy comparisons
    integer phase  = 0;                         // 0 = initial idle, 1 = A, 2 = B, 3 = tail

    // ---- shared record: what the model accepted, in order ------------------
    reg [7:0] sent_byte [0:N_FRAMES+16];
    integer   sent_cyc  [0:N_FRAMES+16];        // cycle in which `start` was accepted
    integer   accepted  = 0;
    integer   ignored_a = 0;                    // phase-A starts that arrived while busy

    // ---- 1. cycle-exact model ----------------------------------------------
    // Runs at the rising edge, so `tx`/`busy` read here are their values during
    // the cycle that is ending (the DUT's nonblocking updates land after), and
    // `start`/`data` are what the DUT samples at this same edge.
    integer   n      = 0;                       // index of the cycle now ending
    reg       m_act  = 1'b0;
    integer   m_t0   = 0;
    reg [7:0] m_byte = 8'h00;
    reg       exp_busy, exp_tx;
    integer   k;

    // ---- 2. independent decoder state ---------------------------------------
    reg       d_prev    = 1'b1;
    reg       d_hunting = 1'b1;
    integer   d_fall    = 0;                    // first low cycle of the start bit
    integer   d_bit     = 0;                    // next bit to sample, 0 = start .. 9 = stop
    reg [9:0] d_bits    = 10'h000;
    integer   decoded   = 0;
    reg [255:0] seen    = 256'd0;               // byte values decoded in phase A

    always @(posedge clk) begin
        // -- model prediction for cycle n
        exp_busy = m_act && (n > m_t0) && (n <= m_t0 + FRAME);
        if (!exp_busy) begin
            exp_tx = 1'b1;
        end else begin
            k = (n - m_t0 - 1) / CPB;           // 0 start, 1..8 data, 9 stop
            if (k == 0)      exp_tx = 1'b0;
            else if (k == 9) exp_tx = 1'b1;
            else             exp_tx = m_byte[k-1];
        end
        checks = checks + 1;
        if (tx !== exp_tx || busy !== exp_busy) begin
            errors = errors + 1;
            if (errors <= MAX_SHOW)
                $display("  mismatch cycle %0d: tx=%b busy=%b, expected tx=%b busy=%b (frame byte %02h accepted in cycle %0d)",
                         n, tx, busy, exp_tx, exp_busy, m_byte, m_t0);
        end

        // -- model acceptance: the DUT samples `start` at this edge
        if (start === 1'b1) begin
            if (!exp_busy) begin
                if (accepted <= N_FRAMES + 16) begin
                    sent_byte[accepted] = data;
                    sent_cyc[accepted]  = n;
                end
                accepted = accepted + 1;
                m_act  = 1'b1;
                m_t0   = n;
                m_byte = data;
            end else if (phase == 1) begin
                ignored_a = ignored_a + 1;
            end
        end

        // -- independent decoder: knows only CPB and the line
        if (d_hunting) begin
            if (d_prev === 1'b1 && tx === 1'b0) begin
                d_hunting = 1'b0;
                d_fall    = n;
                d_bit     = 0;
            end
        end else if (n == d_fall + CPB/2 + d_bit*CPB) begin
            d_bits[d_bit] = tx;
            if (d_bit == 9) begin
                d_hunting = 1'b1;
                if (decoded >= accepted || decoded > N_FRAMES + 16) begin
                    errors = errors + 1;
                    if (errors <= MAX_SHOW)
                        $display("  decoder: frame %0d (byte %02h) seen on tx but no start was accepted for it",
                                 decoded, d_bits[8:1]);
                end else begin
                    if (d_bits[0] !== 1'b0 || d_bits[9] !== 1'b1 ||
                        d_bits[8:1] !== sent_byte[decoded] ||
                        d_fall != sent_cyc[decoded] + 1) begin
                        errors = errors + 1;
                        if (errors <= MAX_SHOW)
                            $display("  decoder: frame %0d start=%b byte=%02h stop=%b edge@%0d, expected start=0 byte=%02h stop=1 edge@%0d",
                                     decoded, d_bits[0], d_bits[8:1], d_bits[9], d_fall,
                                     sent_byte[decoded], sent_cyc[decoded] + 1);
                    end
                    if (decoded < N_A) seen[d_bits[8:1]] = 1'b1;
                end
                decoded = decoded + 1;
            end else begin
                d_bit = d_bit + 1;
            end
        end
        d_prev = tx;

        n = n + 1;
    end

    // ---- registered-output check -------------------------------------------
    time t_edge = 0;
    always @(posedge clk) t_edge = $time;
    always @(tx) begin
        if ($time != 0 && $time != t_edge) begin
            errors = errors + 1;
            if (errors <= MAX_SHOW)
                $display("  tx changed at %0t, not on a rising clock edge (combinational path?)", $time);
        end
    end

    // ---- stimulus (driven on falling edges) ---------------------------------
    integer seed = 32'h1234_5678;
    integer v, r, gap, waited, tail_start;

    // Wait (bounded) for the DUT's busy to be low at a falling edge.
    task wait_idle;
        begin
            waited = 0;
            while (busy !== 1'b0 && waited < 4 * FRAME) begin
                @(negedge clk);
                data   = $random(seed);
                waited = waited + 1;
            end
            if (busy !== 1'b0) begin
                errors = errors + 1;
                $display("  busy never fell (waited %0d cycles)", waited);
            end
        end
    endtask

    initial begin
        // Idle after power-up: the model expects tx high and busy low.
        repeat (40) @(negedge clk);

        // ---- phase A: every byte value, plus one ignored start per frame
        phase = 1;
        for (v = 0; v < N_A; v = v + 1) begin
            wait_idle;
            r   = $random(seed);
            gap = (v % 5 == 0) ? 0 : ((r & 32'h7fff_ffff) % 23);
            repeat (gap) begin
                @(negedge clk);
                data = $random(seed);
            end
            data  = v[7:0];
            start = 1'b1;
            @(negedge clk);                     // now in the first busy cycle
            start = 1'b0;
            data  = $random(seed);
            // Spurious start somewhere in the busy window; every 4th frame,
            // exactly the last busy cycle (the end-of-stop-bit boundary).
            r = $random(seed);
            if (v % 4 == 3) r = FRAME - 1;
            else            r = (r & 32'h7fff_ffff) % FRAME;
            repeat (r) begin
                @(negedge clk);
                data = $random(seed);
            end
            data  = ~v[7:0];
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;
            data  = $random(seed);
        end

        // ---- phase B: start held high, data changing every cycle
        wait_idle;
        phase = 2;
        start = 1'b1;
        waited = 0;
        while (accepted < N_FRAMES && waited < (N_BACK + 2) * (FRAME + 2)) begin
            @(negedge clk);
            data   = $random(seed);
            waited = waited + 1;
        end
        start = 1'b0;

        // ---- tail: let the last frame finish, then silence
        phase = 3;
        wait_idle;
        tail_start = n;
        repeat (3 * FRAME) @(negedge clk);

        // ---- the other bit lengths must have finished too
        wait (h434.done && h13.done && h3.done && h2.done);

        // ---- verdict
        $display("uart_tx: %0d cycle checks, %0d starts accepted (want %0d), %0d frames decoded (want %0d), %0d busy starts ignored (want %0d), %0d/256 byte values seen, %0d errors",
                 checks, accepted, N_FRAMES, decoded, N_FRAMES, ignored_a, N_A,
                 count_seen(seen), errors);
        if (errors == 0 && accepted == N_FRAMES && decoded == N_FRAMES &&
            ignored_a == N_A && count_seen(seen) == 256 &&
            checks >= N_FRAMES * FRAME && n - tail_start >= 3 * FRAME &&
            h434.ok && h13.ok && h3.ok && h2.ok)
            $display("PASS");
        else
            $display("FAIL");
        $finish;
    end

    function integer count_seen(input [255:0] s);
        integer i;
        begin
            count_seen = 0;
            for (i = 0; i < 256; i = i + 1)
                count_seen = count_seen + s[i];
        end
    endfunction

    // Watchdog: a hung DUT or testbench fails rather than timing out silently.
    initial begin
        #(20 * 400_000);
        $display("  watchdog: simulation did not finish");
        $display("FAIL");
        $finish;
    end

endmodule

// ---- the same cycle-exact model at another CLKS_PER_BIT ------------------
// Instantiated by tb_uart_tx only. DEFAULT=1 builds the DUT with no parameter
// override, so it checks the module's own default against CPB (434).
module tb_uart_tx_cpb #(
    parameter integer CPB     = 13,
    parameter integer DEFAULT = 0,
    parameter integer NF      = 10,     // single frames, each followed by an ignored start
    parameter integer NB      = 3       // then back-to-back frames, start held high
) (
    input wire clk
);
    localparam integer FRAME = 10 * CPB;

    reg  [7:0] data  = 8'h00;
    reg        start = 1'b0;
    wire       tx;
    wire       busy;

    generate
        if (DEFAULT != 0) begin : g_dut
            uart_tx dut (
                .clk(clk), .data(data), .start(start), .tx(tx), .busy(busy)
            );
        end else begin : g_dut
            uart_tx #(.CLKS_PER_BIT(CPB)) dut (
                .clk(clk), .data(data), .start(start), .tx(tx), .busy(busy)
            );
        end
    endgenerate

    integer errors   = 0;
    integer checks   = 0;
    integer accepted = 0;
    integer ignored  = 0;                   // starts while busy, single-frame part only
    integer n        = 0;
    reg     single   = 1'b1;
    reg     done     = 1'b0;
    reg     ok       = 1'b0;

    reg       m_act  = 1'b0;
    integer   m_t0   = 0;
    reg [7:0] m_byte = 8'h00;
    reg       exp_busy, exp_tx;
    integer   k;

    always @(posedge clk) begin
        exp_busy = m_act && (n > m_t0) && (n <= m_t0 + FRAME);
        if (!exp_busy) begin
            exp_tx = 1'b1;
        end else begin
            k = (n - m_t0 - 1) / CPB;       // 0 start, 1..8 data, 9 stop
            if (k == 0)      exp_tx = 1'b0;
            else if (k == 9) exp_tx = 1'b1;
            else             exp_tx = m_byte[k-1];
        end
        checks = checks + 1;
        if (tx !== exp_tx || busy !== exp_busy) begin
            errors = errors + 1;
            if (errors <= 4)
                $display("  [CPB=%0d%0s] mismatch cycle %0d: tx=%b busy=%b, expected tx=%b busy=%b (byte %02h accepted in cycle %0d)",
                         CPB, (DEFAULT != 0) ? ", default" : "", n, tx, busy,
                         exp_tx, exp_busy, m_byte, m_t0);
        end
        if (start === 1'b1) begin
            if (!exp_busy) begin
                accepted = accepted + 1;
                m_act    = 1'b1;
                m_t0     = n;
                m_byte   = data;
            end else if (single) begin
                ignored = ignored + 1;
            end
        end
        n = n + 1;
    end

    integer seed, f, r, w;

    task wait_idle;
        begin
            w = 0;
            while (busy !== 1'b0 && w < 4 * FRAME) begin
                @(negedge clk);
                data = $random(seed);
                w    = w + 1;
            end
            if (busy !== 1'b0) begin
                errors = errors + 1;
                $display("  [CPB=%0d] busy never fell (waited %0d cycles)", CPB, w);
            end
        end
    endtask

    initial begin
        seed = 1000 + CPB + DEFAULT;
        repeat (3) @(negedge clk);
        for (f = 0; f < NF; f = f + 1) begin
            wait_idle;
            repeat (f % 3) begin            // gap 0 straight after a last-cycle ignored start
                @(negedge clk);
                data = $random(seed);
            end
            case (f)
                0: data = 8'h00;
                1: data = 8'hFF;
                2: data = 8'h55;
                3: data = 8'hAA;
                4: data = 8'h01;
                5: data = 8'h80;
                default: data = $random(seed);
            endcase
            start = 1'b1;
            @(negedge clk);                 // first busy cycle
            start = 1'b0;
            data  = $random(seed);
            if (f % 2 == 0) begin
                r = FRAME - 1;              // the last busy cycle
            end else begin
                r = $random(seed);
                r = (r & 32'h7fff_ffff) % FRAME;
            end
            repeat (r) begin
                @(negedge clk);
                data = $random(seed);
            end
            data  = ~data;
            start = 1'b1;                   // must be ignored
            @(negedge clk);
            start = 1'b0;
            data  = $random(seed);
        end

        wait_idle;
        single = 1'b0;
        start  = 1'b1;
        w      = 0;
        while (accepted < NF + NB && w < (NB + 2) * (FRAME + 2)) begin
            @(negedge clk);
            data = $random(seed);
            w    = w + 1;
        end
        start = 1'b0;
        wait_idle;
        repeat (2 * FRAME) @(negedge clk);

        ok = (errors == 0 && accepted == NF + NB && ignored == NF &&
              checks >= (NF + NB) * FRAME);
        $display("uart_tx CPB=%0d%0s: %0d cycle checks, %0d starts accepted (want %0d), %0d busy starts ignored (want %0d), %0d errors",
                 CPB, (DEFAULT != 0) ? " (default parameter)" : "", checks,
                 accepted, NF + NB, ignored, NF, errors);
        done = 1'b1;
    end
endmodule

`default_nettype wire
