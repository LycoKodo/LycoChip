#!/usr/bin/env bash
# Program the Cyclone IV over the local USB-Blaster.
#   ./program.sh                -> load into FPGA SRAM (volatile, lost on power cycle)
#   ./program.sh flash          -> write EPCS/SPI config flash (persists)
#   ./program.sh detect         -> just check the JTAG chain
#   ./program.sh sram keytest   -> act on a project other than "blink"
set -euo pipefail

PROJ=${2:-blink}
PART=ep4ce622          # EP4CE6E22C8N -> EQFP-144
CABLE=usb-blaster

case "${1:-sram}" in
  sram)
    # Use the Quartus-generated SVF. openFPGALoader's native Altera .rbf
    # SRAM path prints "Load SRAM 100% Done" but leaves the device
    # unconfigured on this EP4CE6 -- verified the hard way.
    echo "==> loading $PROJ.svf into FPGA SRAM (volatile)"
    openFPGALoader -c "$CABLE" --file-type svf "output_files/$PROJ.svf"
    ;;
  flash)
    echo "==> writing $PROJ.rbf to config flash via spiOverJtag bridge"
    openFPGALoader -c "$CABLE" -f --fpga-part "$PART" --verify "output_files/$PROJ.rbf"
    ;;
  detect)
    openFPGALoader -c "$CABLE" --detect
    ;;
  *)
    echo "usage: $0 [sram|flash|detect] [project]" >&2; exit 1 ;;
esac
