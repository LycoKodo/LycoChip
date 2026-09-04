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

if [ -n "$PROJ" ] && [ ! -f "projects/$PROJ/$PROJ.qsf" ]; then
    echo "no such project: projects/$PROJ" >&2
    echo "available: $(ls projects 2>/dev/null | tr '\n' ' ')" >&2
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
if ! ssh "$REMOTE" "cd ~/$RPROJ && PATH=$QBIN:\$PATH quartus_sh --flow compile $PROJ"; then
    python3 tools/artifacts.py archive "$PROJ" failed >/dev/null 2>&1 || true
    echo "==> BUILD FAILED (archived as failed; previous builds remain selectable)" >&2
    exit 1
fi

echo "==> generating SVF"
ssh "$REMOTE" "cd ~/$RPROJ && PATH=$QBIN:\$PATH quartus_cpf -c -q 12.0MHz -g 3.3 -n p $PROJ.sof $PROJ.svf" >/dev/null

echo "==> fetching bitstreams"
mkdir -p output_files
for ext in sof rbf svf; do
  rsync -az "$REMOTE:$RPROJ/$PROJ.$ext" output_files/ 2>/dev/null || echo "   (no .$ext)"
done

# Archive so the build is visible to ./program.sh and can never go stale
# silently -- the TUI path does this too.
python3 tools/artifacts.py archive "$PROJ" ok >/dev/null
ls -lh output_files/ 2>/dev/null
echo "==> done. Program with: ./program.sh"
