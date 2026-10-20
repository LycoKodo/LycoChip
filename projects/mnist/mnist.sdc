# The one clock: 50 MHz oscillator on PIN_23. Every other rate in the design
# is an enable tick derived from it, so this is the only create_clock.
create_clock -name clk -period 20.000 [get_ports {clk}]
derive_clock_uncertainty

# NOTE: inputs from outside the clock domain (uart_rx, keys) are not
# constrained here. Timing analysis cannot make an asynchronous input safe.
