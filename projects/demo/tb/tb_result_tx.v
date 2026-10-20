// tb_result_tx -- self-checking testbench for rtl/result_tx.v.
//
// Authored by Claude for projects/demo/ (see README.md). Contract:
// ARCHITECTURE.md, "result_tx" (and "uart_tx" for the handshake).
//
// result_tx talks to one of two uart stand-ins, chosen by `use_real` (only
// switched while everything is idle):
//   - a behavioural model: accepts `start` only while its busy is low, then
//     holds busy high for `model_len` cycles, starting the cycle after.
//     Run with lengths 1, 3 and 17.
//   - the real rtl/uart_tx.v (CLKS_PER_BIT = 5). Its serial line is also
//     decoded here, so the bytes are checked on the wire as well as at the
//     handshake.
//
// The expected 22 bytes are built from integer scores kept by the testbench
// (never from the DUT's storage), so a sign or byte-order bug in the DUT
// cannot be mirrored in the reference.
//
// A monitor checks every cycle, independent of the stimulus:
//   tx_start never while tx_busy is high (the byte would be dropped), never
//   two cycles running, never while result_tx.busy is low; no X on outputs.
// Every byte uart accepts (tx_start high, tx_busy low) is recorded.
//
// Per message (send_msg): busy high the cycle after send; busy falls only
// after the 22nd byte's tx_busy has fallen, and within 1 cycle of it; exactly
// 22 bytes accepted, none more while idle afterwards; each byte equal to the
// reference. Some messages also pulse `send` (with a different digit) while
// busy, and every message changes `digit` right after send: both must have no
// effect.
//
// Sections:
//   1. power-up: idle, no tx_start, without any rst; then a send before any
//      score write, which must send defined bytes (zeros), not X
//   2. behavioural uart, four busy lengths, extreme / random / rewritten
//      scores; writes to widx 10..15 must not alias into 0..9 (the contract
//      gives only 10 slots); a send in the last busy cycle (ignored) and one
//      in the first idle cycle (a whole new message, digit 15)
//   3. rst: mid-message abort; rst with send in the same cycle; a send right
//      after a mid-message rst while the uart is still busy
//   4. real uart_tx: two messages, checked at the handshake and on the wire
//
// The number of checks is known in advance; fewer means something was
// skipped, which FAILs.
`default_nettype none

module tb_result_tx;

    localparam integer MAXSHOW  = 10;       // messages printed in full
    localparam integer NBYTES   = 22;
    localparam integer CPB_REAL = 5;        // real uart_tx bit period, cycles

    // Expected number of checks.
    localparam integer CHK_POWER = 3;
    localparam integer CHK_MSG   = 1 + 1 + 1 + 1 + NBYTES;   // rise, fall, count, idle, bytes
    localparam integer CHK_WIRE  = 1 + NBYTES;               // wire count + wire bytes
    localparam integer CHK_R1    = 3;
    localparam integer CHK_R2    = 2;
    localparam integer CHK_ALL   = CHK_POWER + CHK_MSG       // section 1
                                 + 5 * CHK_MSG               // section 2
                                 + CHK_R1 + CHK_R2 + CHK_MSG // section 3
                                 + 2 * (CHK_MSG + CHK_WIRE); // section 4

    // ---------------------------------------------------------------- DUT
    reg               clk    = 1'b0;
    reg               rst    = 1'b0;
    reg               we     = 1'b0;
    reg         [3:0] widx   = 4'd0;
    reg signed [15:0] wscore = 16'sd0;
    reg               send   = 1'b0;
    reg         [3:0] digit  = 4'd0;
    wire              tx_start;
    wire        [7:0] tx_data;
    wire              busy;
    wire              tx_busy;

    result_tx dut (
        .clk(clk), .rst(rst), .we(we), .widx(widx), .wscore(wscore),
        .send(send), .digit(digit), .tx_busy(tx_busy),
        .tx_start(tx_start), .tx_data(tx_data), .busy(busy)
    );

    always #5 clk = ~clk;

    // ---------------------------------------------------------------- uarts
    reg     use_real  = 1'b0;
    integer model_len = 1;
    integer model_cnt = 0;
    wire    model_busy = (model_cnt != 0);

    always @(posedge clk) begin
        if (model_cnt != 0)
            model_cnt <= model_cnt - 1;
        else if (!use_real && tx_start)
            model_cnt <= model_len;
    end

    wire real_tx, real_busy;
    uart_tx #(.CLKS_PER_BIT(CPB_REAL)) u_real (
        .clk(clk), .data(tx_data), .start(tx_start & use_real),
        .tx(real_tx), .busy(real_busy)
    );

    assign tx_busy = use_real ? real_busy : model_busy;

    // ---------------------------------------------------------------- bookkeeping
    integer errors = 0;
    integer checks = 0;
    integer seed   = 32'h5C0BE5;

    integer cyc = 0;                 // posedges so far = index of the current cycle
    always @(posedge clk) cyc = cyc + 1;

    reg  [7:0] cap [0:1023];         // bytes uart accepted, in order
    integer    ncap = 0;
    integer    txfall_cyc = -1;      // last cycle tx_busy went 1 -> 0
    reg        prev_start = 1'b0;
    reg        prev_txbusy = 1'b0;

    task proto(input [8*48-1:0] msg);
        begin
            errors = errors + 1;
            if (errors <= MAXSHOW)
                $display("protocol error t=%0t cyc=%0d: %0s", $time, cyc, msg);
        end
    endtask

    // Monitor at negedge: DUT and uart outputs change only at posedge, and
    // stimulus changes at negedge + 1, so these are the settled values of
    // cycle `cyc`.
    always @(negedge clk) begin
        if (^{tx_start, busy, tx_data} === 1'bx)
            proto("X on tx_start, busy or tx_data");
        if (tx_start === 1'b1) begin
            if (busy !== 1'b1)       proto("tx_start while busy is low");
            if (prev_start === 1'b1) proto("tx_start high two cycles running");
            if (tx_busy !== 1'b0)    proto("tx_start while tx_busy high (dropped)");
            else begin
                if (ncap < 1024) cap[ncap] = tx_data;
                ncap = ncap + 1;
            end
        end
        if (prev_txbusy === 1'b1 && tx_busy === 1'b0)
            txfall_cyc = cyc;
        prev_start  = tx_start;
        prev_txbusy = tx_busy;
    end

    // Serial decoder for the real uart_tx: sample the middle of each bit.
    // tx changes just after a posedge; 2 posedges later is mid start bit.
    reg [7:0] wire_b [0:1023];
    integer   nwire = 0;
    integer   bi;
    reg [7:0] sh;
    initial begin : decoder
        forever begin
            @(negedge real_tx);
            repeat (CPB_REAL / 2) @(posedge clk);
            #2;
            if (real_tx !== 1'b0) proto("wire: start bit not low at its middle");
            for (bi = 0; bi < 8; bi = bi + 1) begin
                repeat (CPB_REAL) @(posedge clk);
                #2;
                sh[bi] = real_tx;
            end
            repeat (CPB_REAL) @(posedge clk);
            #2;
            if (real_tx !== 1'b1) proto("wire: stop bit low");
            if (nwire < 1024) wire_b[nwire] = sh;
            nwire = nwire + 1;
        end
    end

    // ---------------------------------------------------------------- reference
    integer   ref_sc [0:9];
    reg [7:0] exp_b  [0:NBYTES-1];

    // One cycle: stimulus goes in at negedge + 1, after the monitor.
    task tick;
        begin
            @(negedge clk);
            #1;
        end
    endtask

    task check(input ok, input [8*48-1:0] what);
        begin
            checks = checks + 1;
            if (!ok) begin
                errors = errors + 1;
                if (errors <= MAXSHOW)
                    $display("mismatch t=%0t cyc=%0d: %0s", $time, cyc, what);
            end
        end
    endtask

    task write_score(input integer idx, input integer val);
        begin
            tick;
            we     = 1'b1;
            widx   = idx[3:0];
            wscore = val[15:0];
            if (idx < 10) ref_sc[idx] = val;
            tick;
            we     = 1'b0;
        end
    endtask

    function integer urand(input integer n);
        integer t;
        begin
            t = $random(seed);
            if (t < 0) t = -t;
            if (t < 0) t = 0;
            urand = t % n;
        end
    endfunction

    // Busy length of whichever uart is selected.
    function integer cur_b(input dummy);
        cur_b = use_real ? 10 * CPB_REAL : model_len;
    endfunction

    // Send one message and check it. `inject` holds send for a second cycle
    // and pulses it again at bytes 10 and 21, all while busy, with a
    // different digit each time; and, if the DUT has a cycle where busy is
    // still high after the 22nd byte's tx_busy fell, pulses it there too
    // (the last busy cycle: send must still be ignored).
    // `b2b_in`: raise send in the current cycle (no leading tick), so a call
    // right after a `b2b_out` call sends in the first cycle busy is low.
    // `b2b_out`: return as soon as busy falls (skip the idle wait).
    task send_msg(input integer d, input integer inject,
                  input integer b2b_in, input integer b2b_out);
        integer base, wbase, k, i, limit, done, xlow, inj10, inj21, idle, ok;
        begin
            exp_b[0] = 8'hC3;
            exp_b[1] = d[7:0];
            for (i = 0; i < 10; i = i + 1) begin
                exp_b[2 + 2*i] = ref_sc[i] & 255;
                exp_b[3 + 2*i] = (ref_sc[i] >> 8) & 255;
            end
            limit = NBYTES * (cur_b(0) + 6) + 50;
            idle  = 3 * (cur_b(0) + 3) + 10;

            if (!b2b_in) tick;
            if (busy !== 1'b0) proto("tb: send_msg called while busy");
            base  = ncap;
            wbase = nwire;
            send  = 1'b1;
            digit = d[3:0];
            tick;
            // The latched digit must be the one from the send cycle.
            digit = d[3:0] ^ 4'hA;
            send  = inject ? 1'b1 : 1'b0;   // busy now, so ignored
            check(busy === 1'b1, "busy not high the cycle after send");

            done = 0; k = 0; inj10 = 0; inj21 = 0;
            while (!done) begin
                tick;
                k    = k + 1;
                send = 1'b0;
                if (busy !== 1'b1 || k > limit) begin
                    done = 1;
                end else if (inject && !inj10 && ncap - base == 10) begin
                    send = 1'b1; digit = ~d[3:0]; inj10 = 1;
                end else if (inject && !inj21 && ncap - base == 21) begin
                    send = 1'b1; digit = d[3:0] ^ 4'h5; inj21 = 1;
                end else if (inject && ncap - base == NBYTES && tx_busy === 1'b0) begin
                    // Last busy cycle (busy still high, uart already idle).
                    send = 1'b1; digit = d[3:0] ^ 4'h3;
                end
            end
            xlow = cyc;
            if (k > limit) proto("busy never fell (hang)");
            if (inject && !(inj10 && inj21)) proto("tb: send-while-busy pulses not all made");

            // Fell only after the 22nd byte's stop bit, and promptly.
            ok = (tx_busy === 1'b0) && (ncap - base == NBYTES)
                 && (xlow - txfall_cyc >= 0) && (xlow - txfall_cyc <= 1);
            check(ok, "busy fell at the wrong time");
            if (!ok && errors <= MAXSHOW)
                $display("   busy low at cyc %0d, tx_busy=%b, last tx_busy fall cyc %0d, bytes %0d",
                         xlow, tx_busy, txfall_cyc, ncap - base);
            check(ncap - base == NBYTES, "byte count when busy fell");

            if (!b2b_out) repeat (idle) tick;
            check(ncap - base == NBYTES, "extra bytes after busy fell");
            if (ncap - base != NBYTES && errors <= MAXSHOW)
                $display("   %0d bytes accepted, expected %0d", ncap - base, NBYTES);

            for (i = 0; i < NBYTES; i = i + 1) begin
                checks = checks + 1;
                if (base + i >= ncap || cap[base + i] !== exp_b[i]) begin
                    errors = errors + 1;
                    if (errors <= MAXSHOW)
                        $display("byte %0d (digit %0d msg): got %h expected %h", i, d,
                                 (base + i < ncap) ? cap[base + i] : 8'hxx, exp_b[i]);
                end
            end

            if (use_real) begin
                check(nwire - wbase == NBYTES, "wire byte count");
                for (i = 0; i < NBYTES; i = i + 1) begin
                    checks = checks + 1;
                    if (wbase + i >= nwire || wire_b[wbase + i] !== exp_b[i]) begin
                        errors = errors + 1;
                        if (errors <= MAXSHOW)
                            $display("wire byte %0d (digit %0d msg): got %h expected %h", i, d,
                                     (wbase + i < nwire) ? wire_b[wbase + i] : 8'hxx, exp_b[i]);
                    end
                end
            end
        end
    endtask

    // Start a message and stop driving it once `nb` bytes have been accepted;
    // the caller then applies rst. Ends in the cycle the nb-th tx_start is
    // seen.
    task start_until(input integer d, input integer nb);
        integer base, k;
        begin
            tick;
            base  = ncap;
            send  = 1'b1;
            digit = d[3:0];
            k = 0;
            tick;
            send = 1'b0;
            while (ncap - base < nb && k < NBYTES * (cur_b(0) + 6)) begin
                tick;
                k = k + 1;
            end
            if (ncap - base < nb) proto("tb: message never reached the rst point");
        end
    endtask

    integer i, n0;

    initial begin
        for (i = 0; i < 10; i = i + 1) ref_sc[i] = 0;

        // ------------------------------------------------------------ 1
        tick;
        check(busy === 1'b0, "power-up: busy not low");
        check(tx_start === 1'b0, "power-up: tx_start not low");
        repeat (20) tick;
        check(ncap == 0, "power-up: bytes sent without send");

        // A send before any score was written: every byte must be defined
        // (score slots power up to 0, the same in Icarus as on the part).
        // Today the controller always writes all 10 first, so this guards a
        // latent sim/hardware divergence, not a live path.
        send_msg(3, 0, 0, 0);

        // ------------------------------------------------------------ 2
        // Extremes: both ends of int16, sign boundaries, byte boundaries.
        model_len = 1;
        write_score(0,  32767);
        write_score(1, -32768);
        write_score(2,     -1);
        write_score(3,      0);
        write_score(4,      1);
        write_score(5,    255);
        write_score(6,    256);
        write_score(7,   -256);
        write_score(8,  16'h1234);
        write_score(9, -14243);
        send_msg(7, 0, 0, 0);

        // Random scores in the network's observed range (and beyond), long
        // uart busy, sends and digit changes while busy.
        model_len = 17;
        for (i = 0; i < 10; i = i + 1)
            write_score(i, urand(2 * 14244) - 14243);
        send_msg(0, 1, 0, 0);

        // Rewrite some, write the same slot twice (last wins), and write
        // junk to 10..15, which must not land in 0..9.
        model_len = 3;
        write_score(3, -129);
        write_score(3, -128);
        write_score(9,  127);
        for (i = 10; i < 16; i = i + 1)
            write_score(i, 16'h7EAD + i);
        send_msg(9, 1, 0, 0);

        // Back to back: the second send is in the first cycle busy is low,
        // and must start a whole new message. Digit 15 (all four bits set;
        // the high nibble of byte 1 must still be 0).
        model_len = 2;
        for (i = 0; i < 10; i = i + 1)
            write_score(i, urand(65536) - 32768);
        send_msg(15, 1, 0, 1);
        send_msg(5,  0, 1, 0);

        // ------------------------------------------------------------ 3
        // rst mid-message: busy and tx_start low the next cycle, and nothing
        // after the byte uart had already accepted.
        model_len = 17;
        start_until(6, 5);
        n0  = ncap;
        rst = 1'b1;
        tick;
        rst = 1'b0;
        check(busy === 1'b0, "rst: busy not low after rst");
        check(tx_start === 1'b0, "rst: tx_start not low after rst");
        repeat (3 * (model_len + 3) + 10) tick;
        check(ncap == n0, "rst: bytes sent after rst");

        // rst and send in the same cycle: rst wins, nothing starts.
        n0    = ncap;
        rst   = 1'b1;
        send  = 1'b1;
        digit = 4'd5;
        tick;
        rst  = 1'b0;
        send = 1'b0;
        check(busy === 1'b0, "rst+send: busy went high");
        repeat (30) tick;
        check(ncap == n0, "rst+send: bytes sent");

        // rst mid-message, then a full send at once, while the uart is still
        // busy with the interrupted byte: the new message must be whole.
        for (i = 0; i < 10; i = i + 1)
            write_score(i, urand(2001) - 1000);
        start_until(1, 3);
        rst = 1'b1;
        tick;
        rst = 1'b0;
        if (tx_busy !== 1'b1) proto("tb: uart not busy after rst (test is moot)");
        send_msg(8, 0, 0, 0);

        // ------------------------------------------------------------ 4
        // Real uart_tx. Switch only with everything idle.
        repeat (3) tick;
        if (model_busy || busy) proto("tb: not idle at uart switch");
        use_real = 1'b1;
        write_score(0,  14243);
        write_score(1, -14243);
        write_score(2,    127);
        write_score(3,   -128);
        write_score(4,    128);
        write_score(5,   -129);
        write_score(6,    759);
        write_score(7,  -1174);
        write_score(8, 16'h00FF);
        write_score(9, 16'h7F00);
        send_msg(4, 1, 0, 0);

        for (i = 0; i < 10; i = i + 1)
            write_score(i, urand(65536) - 32768);
        send_msg(2, 0, 0, 0);

        // ------------------------------------------------------------ verdict
        $display("tb_result_tx: %0d checks (expected %0d), %0d errors", checks, CHK_ALL, errors);
        if (checks != CHK_ALL) begin
            $display("tb_result_tx: wrong number of checks performed");
            errors = errors + 1;
        end
        if (errors == 0) $display("PASS");
        else             $display("FAIL");
        $finish;
    end

endmodule

`default_nettype wire
