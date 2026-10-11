#!/usr/bin/env bash
# Check RTL syntax without synthesising.
#
#   ./lint.sh              every project
#   ./lint.sh full_adder   one project
#
# Two tools, because they disagree usefully:
#
#   iverilog -t null      parses and elaborates, emits nothing. Strict about
#                         use-before-declaration, which Quartus is not.
#   verilator --lint-only stricter still: flags implicit nets, width
#                         mismatches, unused and undriven signals.
#
# Both run natively on the Mac in about 40 ms. Quartus takes ~9 s just for
# Analysis & Synthesis, so this is the loop to use while writing, with a real
# build only when it passes.
#
# NOTE: neither tool is Quartus. A clean run here does not guarantee the
# design synthesises, and their warnings are advice, not verdicts -- Quartus
# accepts plenty that verilator complains about. The reverse is what matters:
# something flagged here is usually a genuine bug that Quartus will implement
# silently rather than reject.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
# On Windows: puts ~/oss-cad-suite on PATH and sets VERILATOR_ROOT.
. "$HERE/tools/hostenv.sh"

if [ -n "$LYCO_WINDOWS" ]; then
    HINT="unpack OSS CAD Suite to ~/oss-cad-suite (see docs/WINDOWS.md)"
else
    HINT="brew install icarus-verilog verilator"
fi
command -v iverilog >/dev/null || { echo "iverilog not installed: $HINT" >&2; exit 1; }

# `verilator` is a Perl wrapper around verilator_bin. Git Bash's perl lacks
# Pod::Usage, so on Windows the wrapper dies before doing anything; the binary
# itself works. Use whichever actually runs.
if verilator --version >/dev/null 2>&1; then VERILATOR=verilator
elif verilator_bin --version >/dev/null 2>&1; then VERILATOR=verilator_bin
else echo "verilator not installed: $HINT" >&2; exit 1; fi

PROJ=${1:-}
if [ -n "$PROJ" ]; then
    files=$(ls projects/"$PROJ"/rtl/*.v 2>/dev/null) || true
    [ -n "$files" ] || { echo "no RTL under projects/$PROJ/rtl/" >&2; exit 1; }
else
    files=$(ls projects/*/rtl/*.v 2>/dev/null)
fi

rc=0
for f in $files; do
    echo "── $f"
    if err=$(iverilog -t null "$f" 2>&1); then
        echo "   iverilog   ok"
    else
        echo "   iverilog   FAILED"
        echo "$err" | sed 's/^/     /'
        rc=1
    fi
    # Verilator exits non-zero on any warning under -Wall; that is too strict
    # to gate on, so its findings are reported and the exit status ignored.
    out=$($VERILATOR --lint-only -Wall "$f" 2>&1 | grep -E "^%(Error|Warning)" || true)
    if [ -z "$out" ]; then
        echo "   verilator  clean"
    else
        echo "   verilator  $(echo "$out" | wc -l | tr -d ' ') finding(s)"
        echo "$out" | sed 's/^/     /'
    fi
done
exit $rc
