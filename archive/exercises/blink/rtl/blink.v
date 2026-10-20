// Verification pattern for the OMDAZZ Cyclone IV board V3.0 (EP4CE6E22C8N).
//
// Deliberately NOT a generic blink/chase, so it cannot be confused with the
// factory demo: a 4-bit binary UP-COUNTER on LED1..LED4, incrementing at 2 Hz.
//
//   LED1 (PIN_87, LSB) toggles every 0.5 s
//   LED2 (PIN_86)      toggles every 1.0 s
//   LED3 (PIN_85)      toggles every 2.0 s
//   LED4 (PIN_84, MSB) toggles every 4.0 s  <- stays lit a full 4 s
//
// Full 0..15 cycle takes 8 s. Holding the RESET button (PIN_25, active low)
// freezes the count at 0000 => all four LEDs DARK; releasing resumes counting.
//
// LEDs and the button are both ACTIVE LOW on this board.
module blink #(
    parameter integer CLK_HZ  = 50_000_000,
    parameter integer TICK_HZ = 2
)(
    input  wire       clk,    // PIN_23, 50 MHz
    input  wire       rst_n,  // PIN_25, RESET button, active low
    output wire [3:0] led     // PIN_87/86/85/84, active low
);
    localparam integer DIV = CLK_HZ / TICK_HZ;

    reg [$clog2(DIV)-1:0] cnt;
    reg [3:0]             value;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt   <= 0;
            value <= 4'd0;
        end else if (cnt == DIV - 1) begin
            cnt   <= 0;
            value <= value + 1'b1;
        end else begin
            cnt <= cnt + 1'b1;
        end
    end

    // Active low: invert so a set counter bit lights its LED.
    assign led = ~value;
endmodule
