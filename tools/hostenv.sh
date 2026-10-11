# Host detection, sourced by build.sh, upload.sh and lint.sh.
#
# On the Mac this sets PY=python3 and nothing else -- every other branch below
# is guarded by LYCO_WINDOWS, so the Mac, Docker, VM and lyco-server paths
# behave exactly as they did before this file existed.
#
# On Windows (Git Bash) it fixes three things that otherwise fail silently:
#
#   1. `python3` is the Microsoft Store alias stub. `command -v python3`
#      succeeds, but running it prints "Python was not found" and exits
#      non-zero. So PY is chosen by *running* a candidate, not by finding it.
#   2. OSS CAD Suite is unpacked to ~/oss-cad-suite rather than installed onto
#      PATH, and its `verilator` wrapper is a Perl script that Git Bash's perl
#      cannot run (no Pod::Usage). verilator_bin works if VERILATOR_ROOT is set.
#   3. Quartus lives somewhere like C:\intelFPGA_lite\20.1\quartus\bin64, which
#      is not on PATH. QBIN_NATIVE is found here; build.sh's `native` backend
#      and upload.sh's quartus_pgm path use it.

case "$(uname -s 2>/dev/null)" in
    MINGW*|MSYS*|CYGWIN*) LYCO_WINDOWS=1 ;;
    *)                    LYCO_WINDOWS= ;;
esac

# ---- python ---------------------------------------------------------------
PY=
for _c in python3 python; do
    if "$_c" -c 'import sys' >/dev/null 2>&1; then PY=$_c; break; fi
done
PY=${PY:-python3}   # keep the old behaviour (and its error) if neither runs

# Can the arrow-key TUIs run here? They need termios, which Windows Python
# does not have. Checked once, by import, rather than by guessing from the OS.
py_has_tui() { "$PY" -c 'import termios' >/dev/null 2>&1; }

# The repo's Quartus version. Builds from any other version still work, but
# their bitstreams are not byte-comparable with the Mac and lyco-server builds.
QUARTUS_REPO_VERSION=20.1.1

if [ -n "$LYCO_WINDOWS" ]; then
    # ---- OSS CAD Suite (simulation + lint) --------------------------------
    OSS_CAD=${OSS_CAD:-$HOME/oss-cad-suite}
    if [ -d "$OSS_CAD/bin" ] && ! command -v iverilog >/dev/null 2>&1; then
        PATH="$OSS_CAD/bin:$OSS_CAD/lib:$PATH"
    fi
    if [ -d "$OSS_CAD/share/verilator" ] && [ -z "${VERILATOR_ROOT:-}" ]; then
        VERILATOR_ROOT=$(cygpath -m "$OSS_CAD/share/verilator")
        export VERILATOR_ROOT
    fi

    # ---- Quartus ----------------------------------------------------------
    # Order: an explicit QUARTUS_BIN, then the QUARTUS_ROOTDIR the installer
    # sets, then the default install roots. Among several installs, 20.1 wins
    # (it matches the repo); otherwise the newest.
    QBIN_NATIVE=
    if [ -n "${QUARTUS_BIN:-}" ]; then
        QBIN_NATIVE=$(cygpath -u "$QUARTUS_BIN")
    elif [ -n "${QUARTUS_ROOTDIR:-}" ] && [ -x "$(cygpath -u "$QUARTUS_ROOTDIR")/bin64/quartus_sh" ]; then
        QBIN_NATIVE="$(cygpath -u "$QUARTUS_ROOTDIR")/bin64"
    else
        # `|| true` throughout: the callers run under `set -euo pipefail`, and
        # "no Quartus here" must not abort the script that sourced this.
        _found=$(ls -d /c/intelFPGA_lite/*/quartus/bin64 /c/intelFPGA/*/quartus/bin64 \
                       /c/altera_lite/*/quartus/bin64 /c/altera/*/quartus/bin64 \
                       /d/intelFPGA_lite/*/quartus/bin64 /d/altera_lite/*/quartus/bin64 \
                       2>/dev/null || true)
        QBIN_NATIVE=$(printf '%s\n' "$_found" | grep '/20\.1/' | head -1 || true)
        [ -n "$QBIN_NATIVE" ] || QBIN_NATIVE=$(printf '%s\n' "$_found" | sort -V | tail -1 || true)
    fi
    [ -n "$QBIN_NATIVE" ] && [ -x "$QBIN_NATIVE/quartus_sh" ] || QBIN_NATIVE=
fi

# "Version 20.1.1 Build 720 11/11/2020 SJ Lite Edition" -> "20.1.1"
quartus_native_version() {
    [ -n "${QBIN_NATIVE:-}" ] || return 1
    "$QBIN_NATIVE/quartus_sh" --version 2>/dev/null \
        | sed -n 's/^Version \([0-9.]*\).*/\1/p' | head -1 || true
}
unset _c _found
