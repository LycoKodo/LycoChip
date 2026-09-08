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

// GOAL - Make the buttons as inputs for the addder, while have LEDs as output. 

// Questions
    // why is verilog array syntax in reverse? why is verilog array index first, then variable? 
    // what is reg, and wire, and why  is this not required in this case?

module clock_counter (
    input key,
    input wire clk,
    output reg [3:0] led
);
    wire rst;

    assign rst = !key;

    reg [3:0] data;
    reg [24:0] count;

    // next procedure at rising edge, (positive edge) | or reset. 
    always @ (posedge clk or posedge rst) begin
        // 1 bit wide, binary, 1 "1'b1"
        if (rst == 1'b1) begin
            data <= 4'b0000;
            count <= 25'b0;
            led <= ~data;
        end else begin
            if (count == 25'h1FFFFFF && data == 4'b1111) begin // what if counter and data reach at same time
                // RESET or COUNTER FULL
                data <= 4'b0000;
                count <= 25'b0;
                led <= ~data;
            end else if (count == 25'h1FFFFFF) begin // counter reach limit, data not
                count <= 25'b0;
                data <= data + 1'b1;
                led <= ~data;
            end else begin
                count <= count + 1'b1;
            end
        end
    end

endmodule
