#!/usr/bin/env python3
"""
Build archive + provenance for LycoChip.

Every compile is archived under builds/<stamp>-<proj>-<srchash8>/ together with
a manifest recording exactly which sources produced it. Programming always
selects an archived build, so a stale or failed build can never be flashed by
accident.

  python3 tools/artifacts.py hash    <proj>
  python3 tools/artifacts.py archive <proj> <status> [duration]
  python3 tools/artifacts.py list
"""
import hashlib, json, os, shutil, subprocess, sys, time

OUT    = "output_files"
BUILDS = "builds"
PROJ_D = "projects"
EXTS   = ("sof", "rbf", "svf")
KEEP   = 25          # archived builds retained before pruning


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def project_dir(proj):
    return os.path.join(PROJ_D, proj)


def list_projects():
    if not os.path.isdir(PROJ_D):
        return []
    return sorted(d for d in os.listdir(PROJ_D)
                  if os.path.exists(os.path.join(PROJ_D, d, f"{d}.qsf")))


def source_files(proj):
    """Every input that can change the bitstream, in stable order.

    Raises if the project is missing or empty. Returning an empty list would
    silently produce a hash over nothing, which would disable the staleness
    guard rather than trip it.
    """
    d = project_dir(proj)
    if not os.path.isdir(d):
        raise ValueError(f"no such project: {d} (have: {', '.join(list_projects()) or 'none'})")
    files = []
    for root, _, names in os.walk(d):
        for n in sorted(names):
            if n.endswith((".v", ".sv", ".vhd", ".qsf", ".qpf", ".sdc", ".tcl")):
                files.append(os.path.join(root, n))
    if not files:
        raise ValueError(f"project '{proj}' contains no source files")
    return sorted(files)


def source_hash(proj):
    h = hashlib.sha256()
    for p in source_files(proj):
        h.update(p.encode())
        h.update(_sha(p).encode())
    return h.hexdigest()


def _git():
    def run(*a):
        try:
            return subprocess.run(a, capture_output=True, text=True, timeout=5).stdout.strip()
        except Exception:
            return ""
    return {"commit": run("git", "rev-parse", "--short", "HEAD"),
            "dirty":  bool(run("git", "status", "--porcelain"))}


def archive(proj, status, stats=None, duration=None):
    """Snapshot the just-built artifacts into builds/. Returns the manifest."""
    os.makedirs(BUILDS, exist_ok=True)
    sh    = source_hash(proj)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    d     = os.path.join(BUILDS, f"{stamp}-{proj}-{sh[:8]}")
    os.makedirs(d, exist_ok=True)

    arts = {}
    if status == "ok":
        for e in EXTS:
            src = os.path.join(OUT, f"{proj}.{e}")
            if os.path.exists(src):
                dst = os.path.join(d, f"{proj}.{e}")
                shutil.copy2(src, dst)
                arts[e] = {"sha256": _sha(dst), "bytes": os.path.getsize(dst)}

    m = {"project": proj, "device": "EP4CE6E22C8", "status": status,
         "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "built_epoch": time.time(),
         "duration": duration, "source_sha256": sh, "sources": source_files(proj),
         "git": _git(), "artifacts": arts, "stats": stats or {}}
    json.dump(m, open(os.path.join(d, "manifest.json"), "w"), indent=2)
    _prune()
    return m


def _prune():
    try:
        dirs = sorted(d for d in os.listdir(BUILDS)
                      if os.path.isdir(os.path.join(BUILDS, d)))
        for old in dirs[:-KEEP]:
            shutil.rmtree(os.path.join(BUILDS, old), ignore_errors=True)
    except Exception:
        pass


def list_builds(proj=None):
    out = []
    if not os.path.isdir(BUILDS):
        return out
    for name in os.listdir(BUILDS):
        mp = os.path.join(BUILDS, name, "manifest.json")
        if not os.path.exists(mp):
            continue
        try:
            m = json.load(open(mp))
        except Exception:
            continue
        m["_dir"] = os.path.join(BUILDS, name)
        if proj and m.get("project") != proj:
            continue
        out.append(m)
    return sorted(out, key=lambda m: m.get("built_epoch", 0), reverse=True)


def ago(epoch):
    d = max(0, time.time() - epoch)
    if d < 10:    return "just now"
    if d < 60:    return f"{int(d)} seconds ago"
    if d < 3600:
        n = int(d // 60);    return f"{n} minute{'' if n == 1 else 's'} ago"
    if d < 86400:
        n = int(d // 3600);  return f"{n} hour{'' if n == 1 else 's'} ago"
    n = int(d // 86400);     return f"{n} day{'' if n == 1 else 's'} ago"


def verify(m):
    """Check an archived build is intact and matches the current sources."""
    problems, warnings = [], []
    if m.get("status") != "ok":
        problems.append("this build did not succeed")
        return problems, warnings
    for e, rec in m.get("artifacts", {}).items():
        p = os.path.join(m["_dir"], f"{m['project']}.{e}")
        if not os.path.exists(p):
            problems.append(f"{os.path.basename(p)} missing from archive")
        elif _sha(p) != rec["sha256"]:
            problems.append(f"{os.path.basename(p)} corrupted since archiving")
    try:
        if source_hash(m["project"]) != m.get("source_sha256"):
            warnings.append("sources on disk differ from this build")
    except Exception:
        pass
    return problems, warnings


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    cmd = sys.argv[1]
    if cmd == "hash":
        print(source_hash(sys.argv[2]))
    elif cmd == "archive":
        proj, status = sys.argv[2], sys.argv[3]
        dur = float(sys.argv[4]) if len(sys.argv) > 4 else None
        print(archive(proj, status, duration=dur)["status"])
    elif cmd == "resolve":
        proj = sys.argv[2] if len(sys.argv) > 2 else None
        good = [m for m in list_builds(proj) if m.get("status") == "ok"]
        if not good:
            print("ERR\tno successful build archived"); sys.exit(1)
        m = good[0]
        probs, warns = verify(m)
        if probs:
            print("ERR\t" + "; ".join(probs)); sys.exit(1)
        print("\t".join([m["_dir"], m["project"], ago(m.get("built_epoch", 0)),
                          "; ".join(warns)]))
    elif cmd == "list":
        for m in list_builds():
            print(f"{m['project']:10s} {m['status']:8s} {ago(m.get('built_epoch',0)):20s} {m['_dir']}")
    else:
        print(__doc__); sys.exit(2)


if __name__ == "__main__":
    main()
