#!/usr/bin/env bash
# Program the Cyclone IV over the local USB-Blaster.
#
#   ./program.sh                 interactive build picker (arrow keys)
#   ./program.sh sram  [proj]    latest good build -> FPGA SRAM (volatile)
#   ./program.sh flash [proj]    latest good build -> EPCS flash (permanent)
#   ./program.sh detect          just check the JTAG chain
#
# Bitstreams always come from builds/, never from a mutable scratch directory,
# so a failed or stale build can never be flashed by accident.
set -euo pipefail

CABLE=usb-blaster
PART=ep4ce622
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

# No arguments + a real terminal -> the picker.
if [ $# -eq 0 ] && [ -t 0 ] && [ -t 1 ] && command -v python3 >/dev/null; then
    exec python3 tools/programui.py
fi

MODE=${1:-sram}
PROJ=${2:-}

if [ "$MODE" = "detect" ]; then
    exec openFPGALoader -c "$CABLE" --detect
fi

# Resolve the newest verified build, refusing anything stale or corrupt.
if ! INFO=$(python3 tools/artifacts.py resolve $PROJ); then
    echo "refusing to program: ${INFO#ERR	}" >&2
    echo "run ./build.sh first" >&2
    exit 1
fi
DIR=$(echo "$INFO" | cut -f1); NAME=$(echo "$INFO" | cut -f2)
WHEN=$(echo "$INFO" | cut -f3); WARN=$(echo "$INFO" | cut -f4)

echo "==> $NAME  (built $WHEN)  $DIR"
if [ -n "$WARN" ]; then
    if [ -n "${FORCE:-}" ]; then
        echo "!!  $WARN  (FORCE set, continuing)" >&2
    else
        echo "" >&2
        echo "REFUSING TO PROGRAM: $WARN" >&2
        echo "  The board would run logic that does not match your source tree." >&2
        echo "  Rebuild:            ./build.sh $NAME" >&2
        echo "  Or override:  FORCE=1 $0 $*" >&2
        exit 1
    fi
fi

case "$MODE" in
  sram)
    echo "==> loading $NAME.svf into FPGA SRAM (volatile)"
    openFPGALoader -c "$CABLE" --file-type svf "$DIR/$NAME.svf" ;;
  flash)
    echo "==> writing $NAME.rbf to EPCS config flash (permanent)"
    openFPGALoader -c "$CABLE" -f --fpga-part "$PART" --verify "$DIR/$NAME.rbf" ;;
  *)
    echo "usage: $0 [sram|flash|detect] [project]" >&2; exit 1 ;;
esac
