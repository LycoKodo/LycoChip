#!/usr/bin/env bash
# Sync sources to lyco-server, compile with Quartus, pull the bitstream back.
set -euo pipefail

REMOTE=lyco
RDIR=lycochip-build
PROJ=${1:-blink}
QBIN='$HOME/intelFPGA_lite/20.1/quartus/bin'

echo "==> syncing sources to $REMOTE:~/$RDIR"
ssh "$REMOTE" "mkdir -p ~/$RDIR"
rsync -az --delete \
  --include='rtl/***' --include='*.qsf' --include='*.sdc' --include='*.qpf' \
  --exclude='*' ./ "$REMOTE:$RDIR/"

echo "==> compiling $PROJ (this is the slow step)"
ssh "$REMOTE" "cd ~/$RDIR && PATH=$QBIN:\$PATH quartus_sh --flow compile $PROJ"

# openFPGALoader's own Altera SRAM path reports success but does NOT configure
# this Cyclone IV. Generate an SVF carrying Intel's own JTAG sequence instead.
echo "==> generating SVF (the load path that actually works)"
ssh "$REMOTE" "cd ~/$RDIR && PATH=$QBIN:\$PATH quartus_cpf -c -q 12.0MHz -g 3.3 -n p $PROJ.sof $PROJ.svf" >/dev/null

echo "==> fetching bitstreams"
mkdir -p output_files
for ext in sof rbf svf; do
  rsync -az "$REMOTE:$RDIR/$PROJ.$ext"              output_files/ 2>/dev/null \
    || rsync -az "$REMOTE:$RDIR/output_files/$PROJ.$ext" output_files/ 2>/dev/null \
    || echo "   (no .$ext produced)"
done
ls -lh output_files/ 2>/dev/null

echo "==> done. Program with: ./program.sh"
