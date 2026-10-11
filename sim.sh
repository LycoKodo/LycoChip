#!/usr/bin/env bash
# Run testbenches with Icarus Verilog.
#
#   ./sim.sh               every project that has a tb/ directory
#   ./sim.sh full_adder    one project
#
# Convention (change it if you want a different one -- it is only plumbing):
#
#   projects/<name>/tb/<anything>_tb.v    one testbench per file, compiled
#                                          together with projects/<name>/rtl/*.v
#
# A testbench PASSES only if vvp exits 0, its output contains a line with
# PASS, and no line contains FAIL. Requiring an explicit PASS is deliberate
# (Article IV): a testbench that checks nothing, or dies before its checks,
# prints nothing -- and nothing must not count as success.
#
# Waveforms: if the testbench calls $dumpfile("x.vcd"), the file lands in
# sim_out/<name>/ (vvp runs there). Open it with:  gtkwave sim_out/<name>/x.vcd
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
. "$HERE/tools/hostenv.sh"

command -v iverilog >/dev/null && command -v vvp >/dev/null || {
    echo "iverilog/vvp not installed (Mac: brew install icarus-verilog;" \
         "Windows: OSS CAD Suite in ~/oss-cad-suite)" >&2; exit 1; }

if [ -n "${1:-}" ]; then
    projs=$1
    [ -d "projects/$projs" ] || { echo "no such project: projects/$projs" >&2; exit 1; }
else
    projs=$(for d in projects/*/tb; do [ -d "$d" ] && basename "$(dirname "$d")"; done)
fi

rc=0; ran=0
for p in $projs; do
    tbs=$(ls projects/"$p"/tb/*_tb.v projects/"$p"/tb/*_tb.sv 2>/dev/null) || true
    if [ -z "$tbs" ]; then
        echo "── $p: no testbenches (projects/$p/tb/*_tb.v)"; continue
    fi
    out="sim_out/$p"; mkdir -p "$out"
    for tb in $tbs; do
        name=$(basename "${tb%.*}"); ran=$((ran + 1))
        echo "── $tb"
        # -g2012 so SystemVerilog-isms in a testbench ($fatal, logic) work;
        # -Wall because a testbench warning is often the bug.
        if ! cerr=$(iverilog -g2012 -Wall -o "$out/$name.vvp" "$tb" projects/"$p"/rtl/*.v 2>&1); then
            echo "   compile    FAILED"; echo "$cerr" | sed 's/^/     /'; rc=1; continue
        fi
        [ -n "$cerr" ] && echo "$cerr" | sed 's/^/     /'
        log=$( (cd "$out" && vvp -n "$name.vvp") 2>&1 ); vrc=$?
        echo "$log" > "$out/$name.log"
        if [ $vrc -ne 0 ];                   then verdict="FAIL (vvp exit $vrc)"
        elif grep -q 'FAIL' <<<"$log";       then verdict="FAIL"
        elif ! grep -q 'PASS' <<<"$log";     then verdict="NO VERDICT (testbench never printed PASS)"
        else                                      verdict="pass"; fi
        echo "   $verdict    log: $out/$name.log"
        [ "$verdict" = pass ] || { rc=1; tail -n 15 <<<"$log" | sed 's/^/     /'; }
    done
done
[ $ran -gt 0 ] || echo "no testbenches found anywhere yet."
exit $rc
