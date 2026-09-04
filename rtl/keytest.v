// Decisive load test: PURELY COMBINATIONAL, no clock, no counter.
// This design is physically incapable of animating anything.
// Keys and LEDs are both active low, so led = key means:
//   no button pressed -> all LEDs dark
//   hold KEY1         -> LED1 lights (and so on)
// If the LEDs still animate after loading this, our bitstream is not running.
module keytest(
    input  wire [3:0] key,  // PIN_88/89/90/91, active low
    output wire [3:0] led   // PIN_87/86/85/84, active low
);
    assign led = key;
endmodule
