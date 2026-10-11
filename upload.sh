#!/usr/bin/env bash
# Program the Cyclone IV over the local USB-Blaster.
# (This was program.sh until the rename to upload.sh.)
#
#   ./upload.sh                 interactive build picker (arrow keys)
#   ./upload.sh sram  [proj]    latest good build -> FPGA SRAM (volatile)
#   ./upload.sh flash [proj]    latest good build -> EPCS flash (permanent)
#   ./upload.sh detect          just check the JTAG chain
#
# Bitstreams always come from builds/, never from a mutable scratch directory,
# so a failed or stale build can never be flashed by accident.
#
# Two programmers:
#   openfpgaloader  the Mac. Loads the .svf -- never the .rbf, see Article V.
#   quartus         Windows, with Quartus installed. Loads the .sof through
#                   Quartus's own quartus_pgm and the Altera USB-Blaster
#                   driver. Picked automatically there; PROGRAMMER= overrides.
set -euo pipefail

CABLE=usb-blaster
PART=ep4ce622
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
. "$HERE/tools/hostenv.sh"

# quartus_pgm's name for the cable. "USB-Blaster" matches the first one
# found; with several attached, use the exact name jtagconfig prints, e.g.
# QCABLE="USB-Blaster [USB-0]".
QCABLE=${QCABLE:-USB-Blaster}
# EP4CE6's JTAG IDCODE. jtagconfig prints it when the chip answers on the
# chain -- a reply from the silicon, not a message from the tool.
EP4CE6_IDCODE=020F10DD

if [ -z "${PROGRAMMER:-}" ]; then
    if [ -n "$LYCO_WINDOWS" ] && [ -n "${QBIN_NATIVE:-}" ]; then PROGRAMMER=quartus
    else PROGRAMMER=openfpgaloader; fi
fi

# No arguments + a real terminal -> the picker. It drives openFPGALoader and
# needs termios, so it is the Mac path only.
if [ $# -eq 0 ] && [ -t 0 ] && [ -t 1 ] && [ "$PROGRAMMER" = openfpgaloader ] && py_has_tui; then
    exec "$PY" tools/programui.py
fi

MODE=${1:-sram}
PROJ=${2:-}

if [ "$MODE" = "detect" ]; then
    if [ "$PROGRAMMER" = quartus ]; then
        out=$("$QBIN_NATIVE/jtagconfig" 2>&1) || true
        echo "$out"
        if grep -qi "$EP4CE6_IDCODE" <<<"$out"; then
            echo "==> EP4CE6 answered on the JTAG chain (IDCODE $EP4CE6_IDCODE)"
        else
            echo "!!  no EP4CE6 on the chain. No cable listed -> driver or USB;" >&2
            echo "    cable listed but no device -> the board is probably unpowered." >&2
            exit 1
        fi
        exit 0
    fi
    exec openFPGALoader -c "$CABLE" --detect
fi

# Resolve the newest verified build, refusing anything stale or corrupt.
# tr: Windows Python ends its lines with \r\n.
if ! INFO=$("$PY" tools/artifacts.py resolve $PROJ | tr -d '\r'); then
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

if [ "$PROGRAMMER" = quartus ]; then
    case "$MODE" in
      sram)
        echo "==> loading $NAME.sof into FPGA SRAM over JTAG (volatile)"
        "$QBIN_NATIVE/quartus_pgm" -c "$QCABLE" -m JTAG -o "p;$DIR/$NAME.sof@1"
        # Article IV: quartus_pgm's "successful" is the tool grading itself.
        echo "==> quartus_pgm reported success. That is not evidence the load took --"
        echo "    check the board does something the previous design could not."
        ;;
      flash)
        # Deliberately not wired up. Writing the W25Q16 through quartus_pgm
        # needs a .jic and the serial flash loader, and nothing here has been
        # proven on this board. The Mac path is the verified one.
        echo "refusing: the config flash is not programmable from the quartus path yet." >&2
        echo "  Use the Mac (openFPGALoader), or PROGRAMMER=openfpgaloader if you" >&2
        echo "  have deliberately set that up here." >&2
        exit 1 ;;
      *)
        echo "usage: $0 [sram|flash|detect] [project]" >&2; exit 1 ;;
    esac
    exit 0
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
