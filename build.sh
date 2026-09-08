#!/usr/bin/env bash
# Compile a project on lyco-server and pull the bitstreams back.
#
#   ./build.sh [project]     default: blink
#   PLAIN=1 ./build.sh       force plain output (no TUI)
#
# Projects live in projects/<name>/ and are self-contained: <name>.qpf,
# <name>.qsf, <name>.sdc and rtl/. Quartus runs with that directory as CWD,
# so paths inside the .qsf stay relative to the project.
set -euo pipefail

PROJ=${1:-}
REMOTE=lyco
RDIR=lycochip-build
QBIN='$HOME/intelFPGA_lite/20.1/quartus/bin'
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

# Projects are discovered, not listed: any projects/<name>/<name>.qsf shows up.
# The directory name and the .qsf basename must agree -- Quartus keys the
# revision and every output file off the .qsf, while the build, archive and
# programming paths key off the directory.
if [ -n "$PROJ" ] && [ ! -f "projects/$PROJ/$PROJ.qsf" ]; then
    echo "no such project: projects/$PROJ/$PROJ.qsf" >&2
    if [ -d "projects/$PROJ" ]; then
        other=$(ls "projects/$PROJ"/*.qsf 2>/dev/null | head -1)
        if [ -n "$other" ]; then
            b=$(basename "$other" .qsf)
            echo "  the directory holds $b.qsf -- rename projects/$PROJ to '$b'," >&2
            echo "  or rename its .qsf/.qpf/.sdc (and PROJECT_REVISION) to '$PROJ'" >&2
        fi
    fi
    echo "available: $(python3 tools/artifacts.py list-projects 2>/dev/null | tr '\n' ' ')" >&2
    exit 1
fi

# No project named + a terminal -> the selection page in buildui.py.
if [ -t 1 ] && [ -z "${PLAIN:-}" ] && command -v python3 >/dev/null; then
    exec python3 "$HERE/tools/buildui.py" "$PROJ"
fi

PROJ=${PROJ:-blink}

# ---- plain fallback -------------------------------------------------------
RPROJ="$RDIR/projects/$PROJ"

echo "==> syncing projects/ to $REMOTE:~/$RDIR"
ssh "$REMOTE" "mkdir -p ~/$RDIR/projects"
# Source files only. --delete does not remove *excluded* files, so Quartus
# outputs (db/, *.rpt, *.pin, *.sof) survive on the server -- that keeps
# incremental compilation working and preserves the .pin audit file.
rsync -az --delete \
  --include='*/' \
  --include='*.v' --include='*.sv' --include='*.vhd' \
  --include='*.qsf' --include='*.qpf' --include='*.sdc' --include='*.tcl' \
  --exclude='*' \
  projects/ "$REMOTE:$RDIR/projects/"

echo "==> compiling $PROJ"
# Tee rather than pipe: the transcript is kept whole for the archive, and the
# exit status must come from quartus_sh, not from tee.
LOG=$(mktemp -t "lycochip-$PROJ")
set -o pipefail
if ! ssh "$REMOTE" "cd ~/$RPROJ && PATH=$QBIN:\$PATH quartus_sh --flow compile $PROJ" 2>&1 | tee "$LOG"; then
    set +o pipefail
    D=$(python3 tools/artifacts.py archive "$PROJ" failed "" "$LOG" 2>/dev/null) || true
    echo "" >&2
    echo "==> BUILD FAILED (archived as failed; previous builds remain selectable)" >&2
    echo "" >&2
    grep -nE "^\s*Error|Error \(" "$LOG" >&2 || echo "   (quartus reported no Error lines)" >&2
    echo "" >&2
    if [ -n "$D" ] && [ -f "$D/build.log" ]; then
        echo "   full transcript: $D/build.log" >&2
    else
        echo "   full transcript: $LOG" >&2
    fi
    exit 1
fi
set +o pipefail

echo "==> generating SVF"
ssh "$REMOTE" "cd ~/$RPROJ && PATH=$QBIN:\$PATH quartus_cpf -c -q 12.0MHz -g 3.3 -n p $PROJ.sof $PROJ.svf" >/dev/null

echo "==> fetching bitstreams"
mkdir -p output_files
for ext in sof rbf svf; do
  rsync -az "$REMOTE:$RPROJ/$PROJ.$ext" output_files/ 2>/dev/null || echo "   (no .$ext)"
done

# Archive so the build is visible to ./program.sh and can never go stale
# silently -- the TUI path does this too.
python3 tools/artifacts.py archive "$PROJ" ok "" "$LOG" >/dev/null
ls -lh output_files/ 2>/dev/null
echo "==> done. Program with: ./program.sh"
