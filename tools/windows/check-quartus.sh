#!/usr/bin/env bash
# Morning check for the Windows workstation, once Quartus is installed.
# Run from Git Bash, in the repo root:   tools/windows/check-quartus.sh
#
# Needs no admin rights. Each step prints PASS / FAIL / SKIP and the evidence
# it is based on -- read the evidence, not just the word (Article IV).
#
#   1. Quartus found, and which version (the repo builds with 20.1.1)
#   2. Cyclone IV E device support: asks Quartus itself for the part list
#   3. A real build of clock_counter through ./build.sh (native backend)
#   4. .rbf compared with the Mac/lyco-server bitstream of the same sources
#   5. The USB-Blaster and the EP4CE6 on the JTAG chain
#
# It never programs the board. That is a separate, deliberate step.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$HERE"
. tools/hostenv.sh

# clock_counter's .rbf from Quartus 20.1.1, identical across lyco-server, the
# emulated VM and Rosetta (docs/PROGRESS.md, 2026-09-21). Only the prefix was
# recorded there, so only the prefix is compared.
RBF_REF=08958f2b

say() { printf '%-6s %s\n' "$1" "$2"; }
fails=0

# ---- 1 ---------------------------------------------------------------------
if [ -z "${QBIN_NATIVE:-}" ]; then
    say FAIL "no Quartus found (looked in C:\\intelFPGA_lite, C:\\altera_lite, \$QUARTUS_ROOTDIR)."
    echo "       Install it, or run with QUARTUS_BIN='C:\\...\\quartus\\bin64'."
    exit 1
fi
QV=$(quartus_native_version)
if [ "$QV" = "$QUARTUS_REPO_VERSION" ]; then
    say PASS "Quartus $QV at $QBIN_NATIVE -- matches the repo"
else
    say WARN "Quartus ${QV:-?} at $QBIN_NATIVE -- the repo uses $QUARTUS_REPO_VERSION."
    echo "       Builds will work; step 4 will not match, and that is expected."
fi

# ---- 2 ---------------------------------------------------------------------
# Asking Quartus for its part list, rather than looking for a directory: a
# family is either installed or it is not, and this is Quartus's own answer.
TCL=$(mktemp "${TMPDIR:-/tmp}/lyco-parts.XXXXXX.tcl")
cat > "$TCL" <<'EOF'
load_package device
if {[catch {get_part_list -family {Cyclone IV E}} parts]} {
    puts "PARTS_ERROR $parts"
} elseif {[lsearch -exact $parts EP4CE6E22C8] >= 0} {
    puts "PARTS_OK [llength $parts]"
} else {
    puts "PARTS_MISSING [llength $parts]"
}
EOF
pout=$("$QBIN_NATIVE/quartus_sh" -t "$(cygpath -m "$TCL")" 2>&1)
rm -f "$TCL"
case "$pout" in
    *PARTS_OK*)      say PASS "Cyclone IV E installed; EP4CE6E22C8 is in Quartus's part list ($(sed -n 's/.*PARTS_OK \([0-9]*\).*/\1/p' <<<"$pout") parts)" ;;
    *PARTS_MISSING*) say FAIL "Cyclone IV E present but EP4CE6E22C8 not listed"; fails=$((fails+1)) ;;
    *)               say FAIL "Cyclone IV E device support not installed (Quartus said: $(grep -m1 -E 'PARTS_ERROR|Error' <<<"$pout"))"
                     echo "       Re-run the Quartus installer and tick 'Cyclone IV' device support."
                     fails=$((fails+1)) ;;
esac

# ---- 3 ---------------------------------------------------------------------
echo "------ building clock_counter (native backend) ------"
if PLAIN=1 BACKEND=native ./build.sh clock_counter > /tmp/lyco-check-build.log 2>&1; then
    FS="$HOME/.lycochip-build/projects/clock_counter/clock_counter.fit.summary"
    if grep -q 'Fitter Status : Successful' "$FS" 2>/dev/null && grep -q 'EP4CE6E22C8' "$FS"; then
        say PASS "compiled; fitter summary:"
        sed 's/^/         /' "$FS"
    else
        say FAIL "build.sh exited 0 but the fitter summary does not show a successful EP4CE6E22C8 fit"
        fails=$((fails+1))
    fi
    [ -s output_files/clock_counter.sof ] && say PASS "clock_counter.sof: $(wc -c < output_files/clock_counter.sof) bytes" \
                                          || { say FAIL "no .sof produced"; fails=$((fails+1)); }
else
    say FAIL "build failed -- transcript in /tmp/lyco-check-build.log"
    grep -E 'Error' /tmp/lyco-check-build.log | head -5 | sed 's/^/         /'
    fails=$((fails+1))
fi

# ---- 4 ---------------------------------------------------------------------
if [ -f output_files/clock_counter.rbf ]; then
    sha=$(sha256sum output_files/clock_counter.rbf | cut -c1-64)
    if [ "${sha:0:8}" = "$RBF_REF" ]; then
        say PASS ".rbf sha256 $sha -- byte-identical to the Mac/lyco-server build"
    else
        say NOTE ".rbf sha256 ${sha:0:16}... vs reference $RBF_REF... -- differs."
        echo "       With Quartus $QUARTUS_REPO_VERSION this would be a finding worth logging; with another version it is expected."
    fi
fi

# ---- 5 ---------------------------------------------------------------------
echo "------ JTAG ------"
if [ -x "$QBIN_NATIVE/jtagconfig" ] || [ -x "$QBIN_NATIVE/jtagconfig.exe" ]; then
    jout=$("$QBIN_NATIVE/jtagconfig" 2>&1)
    sed 's/^/         /' <<<"$jout"
    if grep -qi '020F10DD' <<<"$jout"; then
        say PASS "EP4CE6 answered on the chain (IDCODE 020F10DD)"
    elif grep -qi 'blaster' <<<"$jout"; then
        say FAIL "cable found, no device -- is the board powered? (Article V: 'TDO stuck at 0' = unpowered)"
        fails=$((fails+1))
    else
        say FAIL "no cable -- run tools/windows/install-usb-blaster-driver.ps1 as admin, and check Device Manager"
        fails=$((fails+1))
    fi
else
    say SKIP "no jtagconfig in $QBIN_NATIVE"
fi

echo
[ $fails -eq 0 ] && echo "all checks passed. Next: the load test in docs/WINDOWS.md (it proves the load, not the tool)." \
                 || echo "$fails check(s) failed."
exit $fails
