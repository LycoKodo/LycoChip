#!/usr/bin/env bash
# Run a project's testbenches in Icarus Verilog and report PASS / FAIL.
#
#   ./sim.sh mnist             every testbench in projects/mnist/tb/
#   ./sim.sh mnist tb_mac      one (file tb/tb_mac.v, module tb_mac)
#   WAVE=1 ./sim.sh mnist tb_mac   ...then open the waveform in surfer
#
# Conventions (so the runner needs nothing from the testbench but its verdict):
#
#   - tb/<name>.v holds one top module called <name>.
#   - rtl/<module>.v holds module <module>; the testbench finds it by name
#     (iverilog -y), so a testbench never lists the files it needs.
#   - the testbench prints a line that is exactly PASS or FAIL, then $finish.
#
# The verdict is strict, because a testbench that says nothing has proved
# nothing (CLAUDE.md, Article IV). A testbench FAILS if it:
#   does not compile · uses an implicit net · runs longer than SIM_TIMEOUT seconds (default 60) ·
#   prints FAIL anywhere · never prints PASS · never reaches $finish.
#
# The simulation runs with the project directory as its CWD -- the same CWD
# Quartus compiles in -- so a $readmemh("model/export/w1.hex", ...) path
# means the same file in simulation and in synthesis.
#
# Waveforms are dumped for every run without touching the testbench (a small
# generated module calls $dumpvars on it) to ~/.lycochip-build/sim/<proj>/,
# outside the repo like every other build output.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

command -v iverilog >/dev/null || { echo "iverilog not installed:  brew install icarus-verilog" >&2; exit 1; }

PROJ=${1:-}
[ -n "$PROJ" ] || { echo "usage: $0 <project> [testbench ...]" >&2; exit 1; }
shift
# A path is accepted as well as a project name (used to test this script).
if [ -d "$PROJ" ]; then PDIR=$(cd "$PROJ" && pwd); else PDIR="$HERE/projects/$PROJ"; fi
[ -d "$PDIR" ] || { echo "no such project: $PDIR" >&2; exit 1; }
[ -d "$PDIR/tb" ] || { echo "no testbenches: $PDIR/tb/ does not exist" >&2; exit 1; }
NAME=$(basename "$PDIR")
OUT="$HOME/.lycochip-build/sim/$NAME"
mkdir -p "$OUT"
TIMEOUT=${SIM_TIMEOUT:-60}

if [ $# -gt 0 ]; then
    tbs="$*"
else
    tbs=$(ls "$PDIR"/tb/*.v 2>/dev/null | xargs -n1 basename 2>/dev/null | sed 's/\.v$//')
    [ -n "$tbs" ] || { echo "no testbenches in $PDIR/tb/" >&2; exit 1; }
fi

fail=0
for tb in $tbs; do
    tb=${tb%.v}
    src="$PDIR/tb/$tb.v"
    printf '── %-24s ' "$tb"
    if [ ! -f "$src" ]; then echo "FAIL  (no file tb/$tb.v)"; fail=1; continue; fi
    if ! grep -qE "^[[:space:]]*module[[:space:]]+$tb\b" "$src"; then
        echo "FAIL  (tb/$tb.v does not define module $tb)"; fail=1; continue
    fi

    cat > "$OUT/$tb.dump.v" <<EOF
module lycochip_dump;
    initial begin
        \$dumpfile("$OUT/$tb.fst");
        \$dumpvars(0, $tb);
    end
endmodule
EOF
    rtl=()
    [ -d "$PDIR/rtl" ] && rtl=(-y "$PDIR/rtl" -I "$PDIR/rtl")
    if ! err=$(iverilog -g2012 -Wall -o "$OUT/$tb.vvp" -s "$tb" -s lycochip_dump \
                 "${rtl[@]}" -I "$PDIR/tb" "$src" "$OUT/$tb.dump.v" 2>&1); then
        echo "FAIL  (does not compile)"
        echo "$err" | sed 's/^/     /'
        fail=1; continue
    fi
    # The generated dump module has no delays, so the timescale it inherits
    # from a testbench is irrelevant. Drop that two-line warning only.
    err=$(echo "$err" | awk '/timescale for lycochip_dump inherited/ {skip=1; next}
                             skip && /inherited timescale is here/ {skip=0; next}
                             {skip=0; print}')
    # An implicit net compiles and can even PASS -- a typo'd name becomes a
    # fresh 1-bit wire. Refuse it here rather than trust the verdict.
    if echo "$err" | grep -q "implicit definition"; then
        echo "FAIL  (implicit net: an undeclared name was used)"
        echo "$err" | grep "implicit definition" | sed 's/^/     /'
        fail=1; continue
    fi
    [ -n "$err" ] && echo "$err" | sed 's/^/     /' && printf '   %-24s ' ""

    # perl's alarm is the portable timeout: macOS ships no timeout(1).
    log="$OUT/$tb.log"
    # The trailing exit keeps the subshell alive to report the alarm into the
    # log, rather than onto the terminal.
    (cd "$PDIR" && perl -e 'alarm shift; exec @ARGV' "$TIMEOUT" \
        vvp -n "$OUT/$tb.vvp" -fst; exit $?) >"$log" 2>&1
    rc=$?

    why=""
    if   [ $rc -eq 142 ];                     then why="timed out after ${TIMEOUT}s (no \$finish?)"
    elif grep -qE '^[[:space:]]*FAIL\b' "$log"; then why="testbench printed FAIL"
    elif ! grep -qE '^[[:space:]]*PASS[[:space:]]*$' "$log"; then why="testbench never printed PASS"
    elif ! grep -qE '\$finish called|finish called at' "$log"; then why="did not reach \$finish (exit $rc)"
    fi
    if [ -z "$why" ]; then
        echo "PASS"
    else
        echo "FAIL  ($why)"
        grep -vE 'FST info|dumpfile' "$log" | tail -15 | sed 's/^/     /'
        fail=1
    fi
    echo "     log $log"
    echo "     wave $OUT/$tb.fst"
done

if [ -n "${WAVE:-}" ] && command -v surfer >/dev/null; then
    surfer "$OUT/${tb%.v}.fst" >/dev/null 2>&1 &
fi
exit $fail
