# demo -- timing constraints. Authored by Claude (projects/demo/ override).

# 50 MHz board oscillator on PIN_23.
create_clock -name clk -period 20.000 [get_ports clk]
derive_clock_uncertainty

# Asynchronous inputs: rst_n (the RESET key) and uart_rx (the RS-232 line) are
# not related to clk at all. Each goes through a 2-FF synchroniser in the RTL
# (demo_top for rst_n, uart_rx for the serial line), so there is no meaningful
# input delay to time against; the synchroniser handles the metastability.
set_false_path -from [get_ports {rst_n uart_rx}]

# Slow outputs: the UART line changes every 434 clocks and is sampled by the
# host mid-bit; LEDs and the 7-segment display are read by eye. A few ns of
# clock-to-pin delay cannot matter for any of them, so they are not timed.
set_false_path -to [get_ports {uart_tx led_n[*] seg_n[*] dig_n[*]}]
