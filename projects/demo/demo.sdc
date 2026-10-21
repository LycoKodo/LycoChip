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

# The Virtual JTAG hub (vjtag / jtag_link) runs on the cable's TCK, which has
# no relation to clk. 10 MHz is above any USB-Blaster's TCK (6 MHz). jtag_link
# crosses between the two domains by handshake (see jtag_link.v), so the
# paths between them are not timed.
create_clock -name altera_reserved_tck -period 100.000 [get_ports {altera_reserved_tck}]
set_clock_groups -asynchronous -group [get_clocks {clk}] -group [get_clocks {altera_reserved_tck}]
