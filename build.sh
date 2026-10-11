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
# PY, LYCO_WINDOWS, QBIN_NATIVE -- a no-op on the Mac apart from PY=python3.
. "$HERE/tools/hostenv.sh"

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
    echo "available: $("$PY" tools/artifacts.py list-projects 2>/dev/null | tr -d '\r' | tr '\n' ' ')" >&2
    exit 1
fi

# No project named + a terminal -> the selection page in buildui.py.
# The TUI needs termios, which Windows Python lacks, so it is tested by import.
if [ -t 1 ] && [ -z "${PLAIN:-}" ] && py_has_tui; then
    exec "$PY" "$HERE/tools/buildui.py" "$PROJ"
fi

# No TUI available (Windows), nothing named, and someone at the keyboard:
# a numbered menu rather than silently building blink.
if [ -z "$PROJ" ] && [ -t 0 ] && [ -t 1 ] && [ -z "${PLAIN:-}" ]; then
    mapfile -t _projs < <("$PY" tools/artifacts.py list-projects 2>/dev/null | tr -d '\r')
    if [ ${#_projs[@]} -gt 0 ]; then
        PS3="build which project? "
        select PROJ in "${_projs[@]}"; do [ -n "$PROJ" ] && break; done
    fi
fi

PROJ=${PROJ:-blink}

# ---- backend selection ----------------------------------------------------
# Three places Quartus can run, fastest first:
#
#   local   a Rosetta container on this Mac. ~22 s for clock_counter -- faster
#           than the server, and needs no network whatsoever. This is what
#           makes the build loop work on a school network.
#   remote  lyco-server over ssh. Native x86-64, ~33 s.
#   vm      the emulated Lima VM (tools/quartus-vm/lima.yaml). ~115 s. Kept
#           only as a fallback if Rosetta ever breaks; see that file.
#   native  Quartus installed on this machine -- the Windows workstation,
#           from Git Bash. Found by tools/hostenv.sh (QUARTUS_BIN overrides).
#           Only ever detected on Windows, so the Mac never considers it.
#
# auto prefers native, then local: both are quick and work offline.
#
#   BACKEND=native|local|remote|vm   force one
DIMAGE=lycochip-quartus:centos7
QTREE="$HOME/intelFPGA_lite/20.1"
DBUILD="$HOME/.lycochip-build/projects"   # build scratch, deliberately outside the repo
VM=quartus
VMQBIN='$HOME/intelFPGA_lite/20.1/quartus/bin'
VMDIR='$HOME/lycochip-build'
# Quartus parallelism in the emulated VM only. 4 measured fastest there;
# raising it to 8 made that build slower. See tools/quartus-vm/lima.yaml.
VMJOBS=${VMJOBS:-4}

IMGTAR="$HOME/.lycochip-build/quartus-image.tar"

# The image has gone missing once already, and rebuilding it needs the network
# to pull centos:7 -- precisely what is missing when this backend matters. So
# fall back to reloading the saved copy, which works offline.
docker_ready() {
    [ -d "$QTREE" ] || return 1
    if ! docker info >/dev/null 2>&1; then
        # No daemon. colima is preferred over Docker Desktop: plain CLI, no
        # app to leave running, and it does Rosetta the same way.
        command -v colima >/dev/null 2>&1 || return 1
        echo "==> starting colima (no Docker Desktop needed; ~40 s)" >&2
        colima start >/dev/null 2>&1 || return 1
        docker info >/dev/null 2>&1 || return 1
    fi
    [ -n "$(docker images -q "$DIMAGE" 2>/dev/null)" ] && return 0
    [ -f "$IMGTAR" ] || return 1
    docker load -i "$IMGTAR" >/dev/null 2>&1
    [ -n "$(docker images -q "$DIMAGE" 2>/dev/null)" ]
}
vm_status() { limactl list "$VM" --format '{{.Status}}' 2>/dev/null; }
lyco_up()   { ssh -o BatchMode=yes -o ConnectTimeout=3 "$REMOTE" true 2>/dev/null; }

native_ready() { [ -n "${QBIN_NATIVE:-}" ]; }

BACKEND=${BACKEND:-auto}
if [ "$BACKEND" = auto ]; then
    if   native_ready;          then BACKEND=native
    elif docker_ready;          then BACKEND=local
    elif lyco_up;               then BACKEND=remote
    elif [ -n "$(vm_status)" ]; then BACKEND=vm
    else
        echo "no build backend available." >&2
        if [ -n "$LYCO_WINDOWS" ]; then
        echo "  native: no Quartus found under C:\\intelFPGA_lite or C:\\altera_lite." >&2
        echo "          install Quartus Prime Lite $QUARTUS_REPO_VERSION, or point at it:" >&2
        echo "            QUARTUS_BIN='C:\\path\\to\\quartus\\bin64' ./build.sh $PROJ" >&2
        fi
        echo "  local:  Docker is not running, or $DIMAGE is missing." >&2
        echo "          build it:  docker build --platform linux/amd64 \\" >&2
        echo "                       -t $DIMAGE tools/quartus-docker" >&2
        echo "  remote: lyco-server did not answer." >&2
        echo "  vm:     no '$VM' VM (limactl start --name=$VM tools/quartus-vm/lima.yaml)" >&2
        exit 1
    fi
fi

# Forcing BACKEND=local skips the detection above, so the runtime still has to
# be brought up here -- otherwise an explicit choice fails instantly while an
# automatic one works, which is backwards.
if [ "$BACKEND" = local ] && ! docker_ready; then
    echo "the local backend needs a container runtime, and none could be started." >&2
    echo "  try:  colima start" >&2
    echo "  or pick another backend:  BACKEND=remote ./build.sh $PROJ" >&2
    exit 1
fi

if [ "$BACKEND" = native ]; then
    if ! native_ready; then
        echo "BACKEND=native, but no Quartus install was found on this machine." >&2
        echo "  set QUARTUS_BIN to its bin64 directory, or pick another backend." >&2
        exit 1
    fi
    # A different Quartus still builds, but its bitstreams cannot be compared
    # byte-for-byte with the Mac and lyco-server builds. Say so every time,
    # rather than let a version drift pass unnoticed.
    QV=$(quartus_native_version)
    echo "==> quartus: ${QV:-unknown version} at $QBIN_NATIVE"
    if [ "$QV" != "$QUARTUS_REPO_VERSION" ]; then
        echo "!!  the repo's builds use Quartus $QUARTUS_REPO_VERSION; this is ${QV:-unknown}." >&2
        echo "    Bitstreams will not be byte-comparable with the other backends." >&2
    fi
fi

if [ "$BACKEND" = vm ] && [ "$(vm_status)" != "Running" ]; then
    echo "==> starting the $VM VM (emulated; first boot takes ~7 min)"
    limactl start "$VM" >/dev/null 2>&1 || { echo "could not start the $VM VM" >&2; exit 1; }
fi

echo "==> backend: $BACKEND"

# Run a Quartus command in the Rosetta container, against the scratch copy.
drun() {
    docker run --rm --platform linux/amd64 \
      -e LANG=C -e LC_ALL=C \
      -v "$QTREE:/opt/intelFPGA_lite/20.1:ro" \
      -v "$DBUILD/$PROJ:/work" \
      -w /work "$DIMAGE" bash -c "$1"
}

# Quartus is always run against a COPY of the project, never the repo: it
# rewrites the .qsf (appending LAST_QUARTUS_VERSION and friends) and drops a
# db/ beside it. Letting it do that in place would move the source hash and so
# break program.sh's staleness guard under an already-archived build.
#
# The include/exclude set is the same everywhere: --delete does not remove
# *excluded* files, so db/ and *.rpt survive between builds and Quartus can
# compile incrementally.
SRCSYNC="--include=*/ --include=*.v --include=*.sv --include=*.vhd --include=*.qsf --include=*.qpf --include=*.sdc --include=*.tcl --exclude=*"

# The same mirror for hosts without rsync (Git for Windows ships none):
# copy the source extensions above, remove copies whose original has gone,
# and leave everything else -- db/, reports, bitstreams -- untouched.
mirror_sources() {
    local src=$1 dst=$2 f
    local find_src=(-type f \( -name '*.v' -o -name '*.sv' -o -name '*.vhd' -o -name '*.qsf'
                    -o -name '*.qpf' -o -name '*.sdc' -o -name '*.tcl' \))
    mkdir -p "$dst"
    (cd "$dst" && find . "${find_src[@]}") | while IFS= read -r f; do
        [ -f "$src/$f" ] || rm -f "$dst/$f"
    done
    (cd "$src" && find . "${find_src[@]}") | while IFS= read -r f; do
        mkdir -p "$dst/$(dirname "$f")"
        cp -p "$src/$f" "$dst/$f"
    done
}

# Run a Quartus tool natively, inside the scratch copy of the project.
nrun() { (cd "$DBUILD/$PROJ" && "$QBIN_NATIVE/$1" "${@:2}"); }

q_sync() {
    case "$BACKEND" in
      remote)
        ssh "$REMOTE" "mkdir -p ~/$RDIR/projects"
        rsync -az --delete $SRCSYNC projects/ "$REMOTE:$RDIR/projects/" ;;
      local)
        mkdir -p "$DBUILD/$PROJ"
        rsync -a --delete $SRCSYNC "projects/$PROJ/" "$DBUILD/$PROJ/" ;;
      native)
        mirror_sources "projects/$PROJ" "$DBUILD/$PROJ" ;;
      vm)
        limactl shell "$VM" -- bash -c "mkdir -p $VMDIR/projects/$PROJ && rsync -a --delete $SRCSYNC '$HERE/projects/$PROJ/' $VMDIR/projects/$PROJ/"
        limactl shell "$VM" -- bash -c "f=$VMDIR/projects/$PROJ/$PROJ.qsf; if grep -q NUM_PARALLEL_PROCESSORS \$f; then sed -i 's/^set_global_assignment -name NUM_PARALLEL_PROCESSORS .*/set_global_assignment -name NUM_PARALLEL_PROCESSORS $VMJOBS/' \$f; else echo 'set_global_assignment -name NUM_PARALLEL_PROCESSORS $VMJOBS' >> \$f; fi" ;;
    esac
}

q_compile() {
    case "$BACKEND" in
      remote) ssh "$REMOTE" "cd ~/$RDIR/projects/$PROJ && PATH=$QBIN:\$PATH quartus_sh --flow compile $PROJ" 2>&1 ;;
      local)  drun "quartus_sh --flow compile $PROJ" 2>&1 ;;
      native) nrun quartus_sh --flow compile "$PROJ" 2>&1 ;;
      vm)     limactl shell "$VM" -- bash -c "cd $VMDIR/projects/$PROJ && PATH=$VMQBIN:\$PATH quartus_sh --flow compile $PROJ" 2>&1 ;;
    esac
}

q_svf() {
    CPF="quartus_cpf -c -q 12.0MHz -g 3.3 -n p $PROJ.sof $PROJ.svf"
    case "$BACKEND" in
      remote) ssh "$REMOTE" "cd ~/$RDIR/projects/$PROJ && PATH=$QBIN:\$PATH $CPF" >/dev/null 2>&1 ;;
      local)  drun "$CPF" >/dev/null 2>&1 ;;
      native) nrun $CPF >/dev/null 2>&1 ;;
      vm)     limactl shell "$VM" -- bash -c "cd $VMDIR/projects/$PROJ && PATH=$VMQBIN:\$PATH $CPF" >/dev/null 2>&1 ;;
    esac
}

q_fetch() {
    mkdir -p output_files
    for ext in sof rbf svf; do
      case "$BACKEND" in
        remote) rsync -az "$REMOTE:$RDIR/projects/$PROJ/$PROJ.$ext" output_files/ 2>/dev/null || echo "   (no .$ext)" ;;
        local|native) cp -f "$DBUILD/$PROJ/$PROJ.$ext" output_files/ 2>/dev/null || echo "   (no .$ext)" ;;
        vm)     limactl shell "$VM" -- bash -c "cp -f $VMDIR/projects/$PROJ/$PROJ.$ext '$HERE/output_files/'" 2>/dev/null || echo "   (no .$ext)" ;;
      esac
    done
}

# ---- plain build ----------------------------------------------------------
echo "==> syncing sources"
q_sync

echo "==> compiling $PROJ"
# Tee rather than pipe: the transcript is kept whole for the archive, and the
# exit status must come from quartus_sh, not from tee.
# An explicit template, not `mktemp -t prefix`: BSD mktemp accepts a bare
# prefix, GNU mktemp (Git Bash, Linux) rejects it as "too few X's".
LOG=$(mktemp "${TMPDIR:-/tmp}/lycochip-$PROJ.XXXXXX")
set -o pipefail
if ! q_compile | tee "$LOG"; then
    set +o pipefail
    D=$("$PY" tools/artifacts.py archive "$PROJ" failed "" "$LOG" 2>/dev/null | tr -d '\r') || true
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
q_svf

echo "==> fetching bitstreams"
q_fetch

# Archive so the build is visible to ./upload.sh and can never go stale
# silently -- the TUI path does this too.
"$PY" tools/artifacts.py archive "$PROJ" ok "" "$LOG" >/dev/null
ls -lh output_files/ 2>/dev/null

# Article II wants resource numbers read from the fitter's own report. On the
# backends whose scratch copy is on this machine, print it rather than make
# anyone go looking.
if [ "$BACKEND" = native ] || [ "$BACKEND" = local ]; then
    FS="$DBUILD/$PROJ/$PROJ.fit.summary"
    [ -f "$FS" ] && { echo "==> $FS"; sed 's/^/    /' "$FS"; }
fi
echo "==> done. Program with: ./upload.sh"
