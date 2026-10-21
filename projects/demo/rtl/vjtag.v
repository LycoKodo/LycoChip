// vjtag -- the FPGA end of a Virtual JTAG port (Altera sld_virtual_jtag).
//
// Contract: projects/demo/ARCHITECTURE.md, "vjtag". Authored by Claude
// (projects/demo/ override; not Alex's work).
//
// The Virtual JTAG hub shares the chip's real JTAG pins with the programmer:
// the host selects this instance (index 0) and shifts a 2-bit virtual IR and
// any-length DRs into it with quartus_stp. Everything here is in the tck
// domain. cdr / sdr are high only while this instance is the one selected.
//
// sld_virtual_jtag exists only inside Quartus. Icarus and Verilator get an
// idle stub instead (tck never ticks, no state is ever active), so demo_top
// still simulates and lints unchanged; jtag_link has its own testbench that
// drives these signals directly.
`default_nettype none

`ifdef __ICARUS__
`define VJTAG_STUB
`endif
`ifdef VERILATOR
`define VJTAG_STUB
`endif

module vjtag (
    output wire       tck,
    output wire       tdi,
    input  wire       tdo,
    output wire [1:0] ir_in,
    output wire       cdr,
    output wire       sdr
);

`ifdef VJTAG_STUB
    assign tck   = 1'b0;
    assign tdi   = 1'b0;
    assign ir_in = 2'b00;
    assign cdr   = 1'b0;
    assign sdr   = 1'b0;
    /* verilator lint_off UNUSED */
    wire unused_tdo = tdo;
    /* verilator lint_on UNUSED */
`else
    sld_virtual_jtag #(
        .sld_auto_instance_index ("NO"),
        .sld_instance_index      (0),
        .sld_ir_width            (2)
    ) u_sld_virtual_jtag (
        .tck               (tck),
        .tdi               (tdi),
        .tdo               (tdo),
        .ir_in             (ir_in),
        .ir_out            (2'b00),
        .virtual_state_cdr (cdr),
        .virtual_state_sdr (sdr)
    );
`endif

endmodule

`undef VJTAG_STUB
`default_nettype wire
