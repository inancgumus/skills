#!/usr/bin/env python3
"""Create a review's worktrees, branches and scratch, and record every one.

Usage:
  scratch.py fetch    <owner/repo> <pr> [--clone D]
  scratch.py worktree <owner/repo> <pr> [suffix] [--at REV] [--clone D] [--root D]
  scratch.py dir      <owner/repo> <pr> <suffix> [--root D]
  scratch.py track    <owner/repo> <pr> <worktree|branch|dir|file> <target> [--clone D]
  scratch.py list     <owner/repo> <pr>

Make everything through this and `cleanup_state.py` can delete all of it later
by name, with no guessing. Each command appends a line to $STATE/created.jsonl
and prints the path it made, so the caller can cd into it.

  scratch.py fetch grafana/k6 6257              # branch pr-6257
  scratch.py worktree grafana/k6 6257           # /tmp/pr-6257 at pr-6257
  scratch.py worktree grafana/k6 6257 judge-a   # /tmp/pr-6257-judge-a, detached
  scratch.py dir grafana/k6 6257 probe          # /tmp/pr-6257-probe
  scratch.py track grafana/k6 6257 file /tmp/pr-6257-out.log

`--clone` defaults to the current repository, `--root` to $GIT_PR_REVIEW_ROOT
or /tmp. `track` is the escape hatch for something already made; prefer the
commands that create and record in one step.
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

KINDS = ("worktree", "branch", "dir", "file")


def die(msg):
    sys.exit(f"scratch.py: {msg}")


def run(args, cwd=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def store_for(repo, pr):
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    d = Path(base) / "git-pr-review" / f"{repo.replace('/', '-')}-{pr}"
    (d / "evidence").mkdir(parents=True, exist_ok=True)
    return d


def record(repo, pr, kind, target, clone=None):
    """Append one artifact to the manifest, skipping an exact duplicate."""
    if kind not in KINDS:
        die(f"kind must be one of {', '.join(KINDS)}, got {kind!r}")
    store = store_for(repo, pr)
    entry = {"kind": kind, "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if kind == "branch":
        entry["name"] = str(target)
    else:
        entry["path"] = str(Path(target).resolve())
    if clone:
        entry["clone"] = str(Path(clone).resolve())

    manifest = store / "created.jsonl"
    for line in read_manifest(store):
        same_kind = line.get("kind") == entry["kind"]
        same_thing = line.get("path") == entry.get("path") and line.get("name") == entry.get("name")
        if same_kind and same_thing:
            return entry
    with manifest.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")
    return entry


def read_manifest(store):
    path = Path(store) / "created.jsonl"
    if not path.is_file():
        return []
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def this_clone(explicit):
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if not (p / ".git").exists():
            die(f"{p} is not a git clone")
        return p
    common = run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"]).stdout.strip()
    if not common:
        die("not inside a git repository; pass --clone")
    return Path(common).parent.resolve()


def scratch_root(explicit):
    root = Path(explicit or os.environ.get("GIT_PR_REVIEW_ROOT") or "/tmp").expanduser()
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def note_repo_path(repo, pr, clone):
    """Keep review.json's repo_path in step, so cleanup can find the clone."""
    path = store_for(repo, pr) / "review.json"
    try:
        data = json.loads(path.read_text()) if path.is_file() else {}
    except ValueError:
        return
    if data.get("repo_path") == str(clone):
        return
    data["repo_path"] = str(clone)
    path.write_text(json.dumps(data, indent=1) + "\n")


def parse(argv):
    """Split argv into positionals and --flags."""
    pos, flags, i = [], {}, 0
    while i < len(argv):
        a = argv[i]
        if a.startswith("--"):
            if i + 1 >= len(argv):
                die(f"{a} needs a value")
            flags[a[2:]] = argv[i + 1]
            i += 2
        else:
            pos.append(a)
            i += 1
    return pos, flags


def cmd_fetch(repo, pr, flags):
    clone = this_clone(flags.get("clone"))
    branch = f"pr-{pr}"
    out = run(["git", "fetch", "origin", f"pull/{pr}/head:{branch}"], clone)
    if out.returncode != 0:
        die(f"fetch failed:\n{out.stderr.strip()}")
    record(repo, pr, "branch", branch, clone)
    note_repo_path(repo, pr, clone)
    print(branch)


def cmd_worktree(repo, pr, suffix, flags):
    clone = this_clone(flags.get("clone"))
    root = scratch_root(flags.get("root"))
    name = f"pr-{pr}-{suffix}" if suffix else f"pr-{pr}"
    path = root / name
    if path.exists():
        die(f"{path} already exists")
    rev = flags.get("at") or (f"pr-{pr}" if not suffix else "HEAD")
    args = ["worktree", "add", "-q"]
    # The named worktree checks out the PR branch; every extra one is detached,
    # so parallel agents never fight over the same ref.
    args += [str(path), rev] if not suffix else ["--detach", str(path), rev]
    out = run(["git", *args], clone)
    if out.returncode != 0:
        die(f"worktree add failed:\n{out.stderr.strip()}")
    record(repo, pr, "worktree", path, clone)
    note_repo_path(repo, pr, clone)
    print(path)


def cmd_dir(repo, pr, suffix, flags):
    if not suffix:
        die("dir needs a suffix, e.g. `dir grafana/k6 6257 probe`")
    path = scratch_root(flags.get("root")) / f"pr-{pr}-{suffix}"
    path.mkdir(parents=True, exist_ok=True)
    record(repo, pr, "dir", path)
    print(path)


def cmd_track(repo, pr, kind, target, flags):
    clone = None
    if kind in ("worktree", "branch"):
        clone = this_clone(flags.get("clone"))
    elif flags.get("clone"):
        clone = Path(flags["clone"]).expanduser().resolve()
    if kind != "branch" and not Path(target).exists():
        die(f"{target} does not exist")
    entry = record(repo, pr, kind, target, clone)
    print(entry.get("path") or entry.get("name"))


def cmd_list(repo, pr):
    store = store_for(repo, pr)
    entries = read_manifest(store)
    if not entries:
        print(f"nothing recorded for {repo}#{pr} in {store}")
        return
    for e in entries:
        clone = f"  (clone {e['clone']})" if e.get("clone") else ""
        print(f"{e['kind']:<9} {e.get('path') or e.get('name')}{clone}")
    print(f"{len(entries)} recorded in {store / 'created.jsonl'}")


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        sys.exit(__doc__.strip())
    pos, flags = parse(argv)
    if len(pos) < 3:
        sys.exit(__doc__.strip())
    cmd, repo, pr = pos[0], pos[1], pos[2]
    if not re.fullmatch(r"[^/\s]+/[^/\s]+", repo):
        die(f"expected <owner/repo>, got {repo!r}")
    if not pr.isdigit():
        die(f"expected a PR number, got {pr!r}")
    rest = pos[3:]

    if cmd == "fetch":
        cmd_fetch(repo, pr, flags)
    elif cmd == "worktree":
        cmd_worktree(repo, pr, rest[0] if rest else "", flags)
    elif cmd == "dir":
        cmd_dir(repo, pr, rest[0] if rest else "", flags)
    elif cmd == "track":
        if len(rest) < 2:
            die("track needs a kind and a target")
        cmd_track(repo, pr, rest[0], rest[1], flags)
    elif cmd == "list":
        cmd_list(repo, pr)
    else:
        die(f"unknown command {cmd!r}")


if __name__ == "__main__":
    main()
