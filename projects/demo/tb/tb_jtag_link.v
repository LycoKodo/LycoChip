// tb_jtag_link -- self-checking testbench for jtag_link.
//
// Contract: projects/demo/ARCHITECTURE.md, "jtag_link". Authored by Claude
// (projects/demo/ override; not Alex's work).
//
// The Virtual JTAG hub is not simulated: the testbench plays its part,
// driving ir_in / cdr / sdr / tdi and pulsing tck the way sld_virtual_jtag
// does for one DR scan (one Capture-DR edge, n Shift-DR edges, one edge in
// Exit1/Update). tdo is sampled just before each shifting edge, as the cable
// does. tck runs unrelated to clk, at three speeds, one of them faster than
// clk.
//
// Checked:
//   WRITE  every byte arrives once, in order, LSB-first assembly, at slow,
//          medium and faster-than-clk tck; a partial byte at the end of a scan
//          is dropped and the next scan starts a fresh byte; scans with IR 0,
//          2 or 3 deliver nothing; rx_valid is never high two cycles running.
//   READ   count 0 at power-up; count and bytes after 5 of 22 reply bytes and
//          after all 22; a 23rd tx_start is ignored; bits [7:5] are zero; any
//          byte over JTAG clears count; a second reply replaces the first.
// No `timescale: the RTL has none, and delays here are only relative.
`default_nettype none

module tb_jtag_link;

    localparam [1:0] IR_WRITE = 2'd1,
                     IR_READ  = 2'd2;

    reg clk = 1'b0;
    always #10 clk = ~clk;

    reg       tck      = 1'b0;
    reg       tdi      = 1'b0;
    reg       cdr      = 1'b0;
    reg       sdr      = 1'b0;
    reg [1:0] ir       = 2'd0;
    reg       tx_start = 1'b0;
    reg [7:0] tx_data  = 8'h00;
    wire [7:0] rx_data;
    wire       rx_valid;
    wire       tdo;

    jtag_link dut (
        .clk      (clk),
        .rx_data  (rx_data),
        .rx_valid (rx_valid),
        .tx_start (tx_start),
        .tx_data  (tx_data),
        .tck      (tck),
        .tdi      (tdi),
        .tdo      (tdo),
        .ir_in    (ir),
        .cdr      (cdr),
        .sdr      (sdr)
    );

    integer errors = 0;
    integer th     = 70;        // tck half period (clk half period is 10)

    // ---- everything frame_rx would receive ---------------------------------------
    reg [7:0] got [0:1023];
    integer   ngot       = 0;
    reg       prev_valid = 1'b0;
    always @(negedge clk) begin
        if (rx_valid) begin
            if (ngot < 1024) got[ngot] = rx_data;
            ngot = ngot + 1;
            if (prev_valid) begin
                $display("ERROR: rx_valid high two cycles running (byte %0d)", ngot - 1);
                errors = errors + 1;
            end
        end
        prev_valid = rx_valid;
    end

    // ---- one DR scan, as the hub presents it ----------------------------------------
    reg [8191:0] out;
    task scan(input [1:0] irv, input integer n, input [8191:0] bits);
        integer k;
        begin
            ir  = irv;
            cdr = 1'b1;
            #(th) tck = 1'b1;
            #(th) tck = 1'b0;
            cdr = 1'b0;
            out = 0;
            sdr = 1'b1;
            for (k = 0; k < n; k = k + 1) begin
                tdi = bits[k];
                #(th);
                out[k] = tdo;
                tck = 1'b1;
                #(th) tck = 1'b0;
            end
            sdr = 1'b0;
            tdi = 1'b0;
            #(th) tck = 1'b1;
            #(th) tck = 1'b0;
            repeat (8) @(negedge clk);
        end
    endtask

    // WRITE scan of wb[0..n-1], byte 0 in the low bits (shifted first).
    reg [7:0]    wb [0:1023];
    reg [8191:0] v;
    task write_bytes(input integer n);
        integer k;
        begin
            v = 0;
            for (k = 0; k < n; k = k + 1) v[8*k +: 8] = wb[k];
            scan(IR_WRITE, 8*n, v);
        end
    endtask

    // got[from .. from+n-1] must equal wb[0 .. n-1], and nothing else arrived.
    task expect_got(input integer from, input integer n, input [8*24-1:0] what);
        integer k;
        begin
            if (ngot != from + n) begin
                $display("ERROR: %0s: %0d bytes delivered, expected %0d", what, ngot - from, n);
                errors = errors + 1;
            end
            for (k = 0; k < n && from + k < ngot; k = k + 1)
                if (got[from + k] !== wb[k]) begin
                    $display("ERROR: %0s: byte %0d = %h, expected %h", what, k, got[from + k], wb[k]);
                    errors = errors + 1;
                end
        end
    endtask

    // One reply byte from result_tx, as a one-cycle tx_start.
    task tx_byte(input [7:0] b);
        begin
            @(negedge clk);
            tx_data  = b;
            tx_start = 1'b1;
            @(negedge clk);
            tx_start = 1'b0;
            tx_data  = 8'h00;
            repeat (6) @(negedge clk);
        end
    endtask

    // READ scan; check count, bits [7:5], and reply bytes 0..n-1 against rb[].
    reg [7:0] rb [0:21];
    task expect_reply(input integer n_count, input integer n_check, input [8*24-1:0] what);
        integer k;
        begin
            scan(IR_READ, 184, 0);
            if (out[4:0] !== n_count[4:0] || out[7:5] !== 3'b000) begin
                $display("ERROR: %0s: count byte %h, expected %h", what, out[7:0], n_count[7:0]);
                errors = errors + 1;
            end
            for (k = 0; k < n_check; k = k + 1)
                if (out[8 + 8*k +: 8] !== rb[k]) begin
                    $display("ERROR: %0s: reply byte %0d = %h, expected %h", what, k,
                             out[8 + 8*k +: 8], rb[k]);
                    errors = errors + 1;
                end
        end
    endtask

    integer i, base;

    initial begin
        repeat (5) @(negedge clk);

        // ---- power-up ----
        expect_reply(0, 0, "power-up");
        if (ngot != 0) begin
            $display("ERROR: power-up: %0d bytes delivered by a READ scan", ngot);
            errors = errors + 1;
        end

        // ---- WRITE at three tck speeds ----
        wb[0] = 8'hA5; wb[1] = 8'h5A; wb[2] = 8'h00; wb[3] = 8'hFF;
        wb[4] = 8'h01; wb[5] = 8'h80; wb[6] = 8'h55; wb[7] = 8'hAA;
        for (i = 8; i < 40; i = i + 1) wb[i] = (i * 37 + 3) & 8'hFF;

        th = 70; base = ngot;                    // tck 7x slower than clk
        write_bytes(40);
        expect_got(base, 40, "slow tck");

        for (i = 0; i < 40; i = i + 1) wb[i] = ~wb[i];
        th = 15; base = ngot;                    // tck a bit slower than clk
        write_bytes(40);
        expect_got(base, 40, "medium tck");

        for (i = 0; i < 40; i = i + 1) wb[i] = (i * 91 + 17) & 8'hFF;
        th = 7; base = ngot;                     // tck faster than clk
        write_bytes(40);
        expect_got(base, 40, "fast tck");

        // ---- partial byte dropped, next scan starts fresh ----
        th = 40; base = ngot;
        v = 0;
        v[7:0]  = 8'h3C;
        v[12:8] = 5'b10101;
        scan(IR_WRITE, 13, v);
        wb[0] = 8'h3C;
        expect_got(base, 1, "13-bit scan");
        base = ngot;
        wb[0] = 8'hC3;
        write_bytes(1);
        expect_got(base, 1, "scan after partial");

        // ---- other instructions deliver nothing ----
        base = ngot;
        v = {8192{1'b1}};
        scan(2'd0, 64, v);
        scan(IR_READ, 64, v);
        scan(2'd3, 64, v);
        expect_got(base, 0, "IR 0/2/3 scans");

        // ---- reply: count is 0 after the bytes above ----
        for (i = 0; i < 22; i = i + 1) rb[i] = (i * 53 + 11) & 8'hFF;
        rb[0] = 8'hC3;
        expect_reply(0, 0, "before reply");
        for (i = 0; i < 5; i = i + 1) tx_byte(rb[i]);
        expect_reply(5, 5, "5 of 22");
        for (i = 5; i < 22; i = i + 1) tx_byte(rb[i]);
        expect_reply(22, 22, "22 of 22");
        tx_byte(8'hEE);                          // a 23rd byte: ignored
        expect_reply(22, 22, "23rd tx_start");
        expect_reply(22, 22, "second read");     // READ is non-destructive

        // ---- a byte over JTAG clears count; a new reply replaces the old ----
        wb[0] = 8'h00;
        write_bytes(1);
        expect_reply(0, 0, "after JTAG byte");
        for (i = 0; i < 22; i = i + 1) rb[i] = (i * 29 + 200) & 8'hFF;
        for (i = 0; i < 22; i = i + 1) tx_byte(rb[i]);
        expect_reply(22, 22, "second reply");

        if (errors == 0) $display("PASS");
        else             $display("FAIL");
        $finish;
    end

    initial begin
        #50000000;
        $display("ERROR: watchdog");
        $display("FAIL");
        $finish;
    end

endmodule

`default_nettype wire
