// seg7 -- shows the recognised digit on the board's 4-digit 7-segment display.
//
// Combinational, active low (a 0 lights a segment / enables a digit).
// Bit order is the vendor sled.v example's, so the pin table in ARCHITECTURE.md
// (SEG0..SEG7) lines up: seg_n[0..6] = segments a..g, seg_n[7] = dp.
//
//        a
//       ---
//    f |   | b
//       -g-
//    e |   | c
//       ---
//        d
//
// !valid shows a single dash (only g lit, 8'hBF): "no result yet" must look
// different from any digit, including 8.
//
// valid with digit 10..15 is outside the contract (argmax only produces 0..9).
// It shows blank (8'hFF) rather than a hex letter, so a controller bug that
// leaks an out-of-range index is visible as a dark display instead of a
// plausible-looking character.
//
// dig_n is tied to all-enabled: every digit shows the same character, so the
// display needs no multiplexing (no scan counter, no clock) and digit order
// cannot be wrong.
//
// seg_n is a continuous assign of a function, not an always @(*) block, so
// that simulation agrees with the hardware at time 0. With `iverilog -g2012`
// an always @(*) does not run until an input changes, and declaration
// initialisers are not events; in demo_top digit/valid hold their power-up
// values until the first result, so the always @(*) version left seg_n at X
// (instead of the dash) in tb_demo. The gates are the same either way.
`default_nettype none

module seg7 (
    input  wire [3:0] digit,
    input  wire       valid,
    output wire [7:0] seg_n,
    output wire [3:0] dig_n
);

    assign dig_n = 4'b0000;

    // Every path assigns pattern (default included): pure logic, no latch.
    function [7:0] pattern(input v, input [3:0] d);
    begin
        if (!v)
            pattern = 8'hBF;                  // dash: g only
        else
            case (d)
                4'd0:    pattern = 8'hC0;     // a b c d e f
                4'd1:    pattern = 8'hF9;     // b c
                4'd2:    pattern = 8'hA4;     // a b d e g
                4'd3:    pattern = 8'hB0;     // a b c d g
                4'd4:    pattern = 8'h99;     // b c f g
                4'd5:    pattern = 8'h92;     // a c d f g
                4'd6:    pattern = 8'h82;     // a c d e f g
                4'd7:    pattern = 8'hF8;     // a b c
                4'd8:    pattern = 8'h80;     // all but dp
                4'd9:    pattern = 8'h90;     // a b c d f g
                default: pattern = 8'hFF;     // 10..15: blank (see header)
            endcase
    end
    endfunction

    assign seg_n = pattern(valid, digit);

endmodule

`default_nettype wire
