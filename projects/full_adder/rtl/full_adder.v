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

module full_adder (
    input [2:0] key,
    
    output [1:0] led
);
    assign a = !(key[0]);
    assign b = !(key[1]);
    assign c_in = !(key[2]);

    assign led[0] = !(S);
    assign led[1] = !(c_out);

    // Alphas
    assign alpha = a ^ b;
    assign beta = a && b;
    assign gamma = alpha && c_in;

    assign S = alpha ^ c_in;
    assign c_out = gamma | beta;
endmodule
