#!/usr/bin/env python3
"""Remove every leftover of a review whose PR is merged or closed.

Usage:
  cleanup_state.py                       # list what would go
  cleanup_state.py --delete              # remove it
  cleanup_state.py --repo-path ~/src/k6  # sweep this clone too
  cleanup_state.py --scratch-root /tmp   # sweep this scratch root too
  cleanup_state.py --pr 6257             # limit to one PR number

A review litters in four places: the state-store directory, the throwaway
worktrees, the PR branch, and whatever the subagents dropped beside their
worktrees (built binaries, probe scripts, patches). This removes all four for
every PR that is no longer OPEN.

It works from two sources. The manifest, $STATE/created.jsonl, is the exact
record every `scratch.py` command appends as it creates something; anything
listed there is removed by name, wherever it lives. The sweep is the safety
net for what predates the manifest or was made by hand: it looks for
pr-<number> and pr-<number>-<suffix> under the scratch roots, in the clones'
worktrees, and in the clones' branches.

Clones are discovered from the manifest, from the worktrees themselves, and
from review.json, so a bare run usually finds everything. Each leftover is
judged against its own clone's repo, so a merged PR goes even when another
clone has an open PR of the same number.

An OPEN PR is never touched, and neither is anything whose state gh cannot
read, nor a swept entry no clone can be pinned to while the clones disagree
about that number.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Only ever consider the names a review itself creates: pr-<number>, and
# pr-<number> with an agent suffix. Anything else stays.
PR_NAME = re.compile(r"^pr-(\d+)(?:[-._].*)?$", re.ASCII)

ORDER = {
    "worktree": 0,
    "orphan worktree": 1,
    "orphan dir": 2,
    "dir": 2,
    "loose file": 3,
    "file": 3,
    "state dir": 4,
    "branch": 5,  # after its worktrees, or git refuses to drop a checked-out branch
}

_states = {}


def run(args, cwd=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def git(args, cwd):
    return run(["git", *args], cwd=cwd)


def pr_state(repo, pr):
    """OPEN, MERGED, CLOSED, or None when gh cannot read it."""
    key = (repo, pr)
    if key not in _states:
        out = run(["gh", "pr", "view", str(pr), "-R", repo, "--json", "state", "-q", ".state"])
        _states[key] = out.stdout.strip() if out.returncode == 0 else None
    return _states[key]


def repo_slug(clone):
    """owner/repo from the clone's origin remote, without touching the network."""
    url = git(["remote", "get-url", "origin"], clone).stdout.strip()
    if not url:
        return None
    parts = [p for p in re.split(r"[/:]", re.sub(r"\.git$", "", url)) if p]
    return "/".join(parts[-2:]) if len(parts) >= 2 else None


def clone_of(path):
    """The clone behind a worktree directory, whether it is still registered."""
    dotgit = Path(path) / ".git"
    if not dotgit.is_file():
        return None  # a directory with .git/ is a clone, not a worktree
    m = re.match(r"gitdir:\s*(.+)", dotgit.read_text().strip())
    if not m:
        return None
    gitdir = Path(m.group(1))
    if "worktrees" not in gitdir.parts:
        return None
    # <clone>/.git/worktrees/<name> -> <clone>
    return Path(*gitdir.parts[: gitdir.parts.index("worktrees")]).parent


def size_of(path):
    p = Path(path)
    if p.is_symlink():
        return 0
    if p.is_file():
        try:
            return p.stat().st_size
        except OSError:
            return 0
    total = 0
    for root, _, files in os.walk(p, onerror=lambda _: None):
        for f in files:
            try:
                total += (Path(root) / f).stat().st_size
            except OSError:
                pass
    return total


def fmt_size(n):
    for unit, div in (("G", 1 << 30), ("M", 1 << 20), ("K", 1 << 10)):
        if n >= div:
            return f"{n / div:.1f}{unit}"
    return f"{n}B"


def state_root():
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(base) / "git-pr-review"


def scratch_roots(extra):
    roots = list(extra)
    if not roots:
        roots = [Path("/tmp")]
        if os.environ.get("TMPDIR"):
            roots.append(Path(os.environ["TMPDIR"]))
    seen, out = set(), []
    for r in roots:
        try:
            real = r.resolve()
        except OSError:
            continue
        if real.is_dir() and real not in seen:
            seen.add(real)
            out.append(real)
    return out


def within(path, roots):
    """True when path sits inside one of roots, symlinks resolved."""
    try:
        real = Path(path).resolve()
    except OSError:
        return False
    return any(real == r or r in real.parents for r in roots)


def scan_scratch(roots):
    """Every pr-<n>* entry under the scratch roots, with the clone behind it."""
    found = []
    for root in roots:
        try:
            entries = sorted(root.iterdir())
        except OSError:
            continue
        for e in entries:
            m = PR_NAME.match(e.name)
            if m:
                found.append((e, int(m.group(1)), clone_of(e)))
    return found


def worktrees_of(clone):
    """(path, branch) per registered worktree, main one excluded."""
    trees, cur = [], None
    for line in git(["worktree", "list", "--porcelain"], clone).stdout.splitlines():
        if line.startswith("worktree "):
            if cur:
                trees.append(cur)
            cur = {"path": Path(line[len("worktree "):]), "branch": None}
        elif line.startswith("branch ") and cur:
            cur["branch"] = line[len("branch "):].replace("refs/heads/", "", 1)
    if cur:
        trees.append(cur)
    return [(t["path"], t["branch"]) for t in trees[1:]]


def pr_branches(clone):
    out = git(["for-each-ref", "--format=%(refname:short)", "refs/heads/"], clone).stdout
    return [b for b in out.split() if PR_NAME.match(b)]


def parse_args(argv):
    if "-h" in argv or "--help" in argv:
        sys.exit(__doc__.strip())
    opts = {"delete": "--delete" in argv, "repos": [], "roots": [], "prs": set()}
    flags = {"--repo-path": "repos", "--scratch-root": "roots", "--pr": "prs"}
    for i, a in enumerate(argv):
        if a not in flags or i + 1 >= len(argv):
            continue
        val = argv[i + 1]
        if a == "--pr":
            if not val.isdigit():
                sys.exit(f"--pr wants a number, got {val!r}")
            opts["prs"].add(int(val))
        else:
            opts[flags[a]].append(Path(val).expanduser())
    return opts


def manifest(state_dir):
    """What scratch.py recorded for this review: [(kind, target, clone)]."""
    path = Path(state_dir) / "created.jsonl"
    if not path.is_file():
        return []
    out = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except ValueError:
            continue
        kind = e.get("kind")
        target = e.get("name") if kind == "branch" else e.get("path")
        if not kind or not target or kind not in ORDER:
            continue
        clone = Path(e["clone"]) if e.get("clone") else None
        out.append((kind, target if kind == "branch" else Path(target), clone))
    return out


def clones_from_state(store):
    """Clones named in review.json or in a manifest, for when only a branch is left."""
    out = []
    if not store.is_dir():
        return out
    for review in sorted(store.glob("*/review.json")):
        try:
            path = json.loads(review.read_text()).get("repo_path")
        except (OSError, ValueError):
            continue
        if path and Path(path).expanduser().is_dir():
            out.append(Path(path).expanduser())
    for d in sorted(p for p in store.iterdir() if p.is_dir()):
        for _, _, clone in manifest(d):
            if clone and clone.is_dir():
                out.append(clone)
    return out


def find_clones(asked, scratch, store):
    """Clones to sweep: the ones asked for, the ones worktrees and state point at, the cwd."""
    clones = {p.resolve(): None for p in asked}
    for _, _, clone in scratch:
        if clone and clone.is_dir():
            clones.setdefault(clone.resolve(), None)
    for p in clones_from_state(store):
        clones.setdefault(p.resolve(), None)
    common = git(["rev-parse", "--path-format=absolute", "--git-common-dir"], Path.cwd()).stdout.strip()
    if common:
        clones.setdefault(Path(common).parent.resolve(), None)
    return {c: repo_slug(c) for c in clones}


def too_precious(real):
    """Refuse a target no review could ever have created."""
    if real == Path(real.root) or real == Path.home().resolve():
        return "it is the filesystem root or your home directory"
    if len(real.parts) <= 2:
        return "it is too close to the filesystem root"
    if (real / ".git").is_dir():
        return "it is a git clone, not a worktree"
    return None


def remove(kind, target, clone, roots, store, tracked=False):
    """Delete one leftover. Returns (ok, reason when not)."""
    if kind == "branch":
        out = git(["branch", "-D", target], clone)
        reason = out.stderr.strip().splitlines()[0] if out.stderr.strip() else "failed"
        return out.returncode == 0, reason

    real = Path(target).resolve()
    cwd = Path.cwd().resolve()
    if real == cwd or real in cwd.parents:
        return False, "it is the current directory or an ancestor"
    danger = too_precious(real)
    if danger:
        return False, danger
    if kind == "state dir":
        if not within(real, [store.resolve()]):
            return False, f"outside {store}"
    elif not tracked and not within(real, roots):
        # A swept path was found by name alone, so keep it inside known roots.
        # A tracked one we created ourselves and recorded, wherever it lives.
        return False, "outside the scratch roots"

    if kind == "worktree" and git(["worktree", "remove", "--force", str(target)], clone).returncode == 0:
        return True, ""
    # The admin entry can be gone while the directory remains; drop it by hand.
    try:
        if real.is_dir():
            shutil.rmtree(real)
        else:
            real.unlink()
    except OSError as err:
        return False, str(err)
    if clone:
        git(["worktree", "prune"], clone)
    return True, ""


def main():
    opts = parse_args(sys.argv[1:])
    roots = scratch_roots(opts["roots"])
    store = state_root()
    clones = find_clones(opts["repos"], scan_scratch(roots), store)

    # Reviews often run inside a per-session scratchpad, which a top-level /tmp
    # scan never reaches. The registered worktrees say where those live, so take
    # their parents as scratch roots too and rescan for the litter beside them.
    nested = {p.parent for c in clones for p, _ in worktrees_of(c) if PR_NAME.match(p.name)}
    roots = scratch_roots(list(roots) + sorted(nested))
    scratch = scan_scratch(roots)
    repos = sorted({s for s in clones.values() if s})

    print(f"state store {store}")
    print(f"scratch roots {', '.join(str(r) for r in roots)}")
    for clone, slug in sorted(clones.items()):
        print(f"clone {clone} -> {slug or 'no origin remote'}")
    if not repos:
        print("no clone resolved; worktrees, branches and scratch entries need --repo-path")

    # Attribution is per clone. A leftover whose clone is known is judged against
    # that clone's repo alone, so a merged PR in one repo goes even while another
    # repo has an open PR wearing the same number.
    def resolve(pr, owner_repo=None):
        """(state, repo) for a PR number. AMBIGUOUS when clones disagree."""
        if owner_repo:
            return pr_state(owner_repo, pr), owner_repo
        seen = [(pr_state(r, pr), r) for r in repos]
        seen = [(s, r) for s, r in seen if s]
        if not seen:
            return None, None
        if len({s for s, _ in seen}) > 1:
            return "AMBIGUOUS", ", ".join(f"{r} {s}" for s, r in seen)
        return seen[0]

    plan, kept, unresolved, ambiguous = {}, [], [], []

    def wanted(pr):
        return not opts["prs"] or pr in opts["prs"]

    done, refused, gone = set(), [], 0

    def vet(kind, target, tracked):
        """Reject a target before anything expensive touches it."""
        if kind == "branch":
            return None
        real = Path(target).resolve()
        if not real.exists():
            return "already gone"
        if real == Path.cwd().resolve() or real in Path.cwd().resolve().parents:
            return "it is the current directory or an ancestor"
        precious = too_precious(real)
        if precious:
            return precious
        if any(real == r or real in r.parents for r in roots + [store.resolve()]):
            return "it is a scratch root or the state store, or contains one"
        if kind == "state dir":
            return None if within(real, [store.resolve()]) else f"outside {store}"
        if not tracked and not within(real, roots):
            return "outside the scratch roots"
        return None

    def add(pr, repo, state, kind, target, clone=None, tracked=False):
        nonlocal gone
        key = ("branch", str(clone), target) if kind == "branch" else ("path", str(Path(target).resolve()))
        if key in done:
            return  # the manifest already claimed it; don't plan it twice
        done.add(key)
        why = vet(kind, target, tracked)
        if why == "already gone":
            gone += 1
            return
        if why:
            refused.append(f"{kind} {target}: {why}")
            return
        # Sizing walks the tree, so it happens only after the target is vetted.
        e = plan.setdefault(pr, {"repo": repo, "state": state, "items": []})
        e["repo"] = e["repo"] or repo
        size = 0 if kind == "branch" else size_of(target)
        e["items"].append((kind, target, clone, size, tracked))

    def judge(pr, owner_repo, label, on_gone):
        """Route one leftover by its PR state. on_gone(state, repo) plans the delete."""
        state, repo = resolve(pr, owner_repo)
        if state is None:
            unresolved.append(f"{label}: no clone could resolve #{pr}")
        elif state == "AMBIGUOUS":
            ambiguous.append(f"{label}: #{pr} differs by clone ({repo}), pass --repo-path to pick one")
        elif state == "OPEN":
            kept.append(f"{label}: OPEN")
        else:
            on_gone(state, repo)

    for d in sorted(p for p in store.iterdir() if p.is_dir()) if store.is_dir() else []:
        owner, _, rest = d.name.partition("-")
        repo, _, num = rest.rpartition("-")
        if not num.isdigit() or not repo:
            unresolved.append(f"{d.name}: name is not <owner>-<repo>-<pr>")
            continue
        pr = int(num)
        if not wanted(pr):
            continue
        slug = f"{owner}/{repo}"
        state = pr_state(slug, pr)
        if state is None:
            unresolved.append(f"{d.name}: gh could not read {slug}#{pr}")
        elif state == "OPEN":
            kept.append(f"{d.name}: OPEN")
        else:
            # The manifest first: it names exactly what this review made, so it
            # needs no guessing and reaches paths outside the scratch roots.
            for kind, target, clone in manifest(d):
                add(pr, slug, state, kind, target, clone or None, tracked=True)
            add(pr, slug, state, "state dir", d, tracked=True)

    registered, owners = set(), {}
    for clone, slug in sorted(clones.items()):
        for path, _ in worktrees_of(clone):
            registered.add(path.resolve())
            m = PR_NAME.match(path.name)
            if not m:
                continue
            pr = int(m.group(1))
            # Scratch sits beside its worktree, so this is what tells a bare
            # pr-<pr>-probe directory which repo's PR it came from.
            owners.setdefault((path.parent.resolve(), pr), (clone, slug))
            if wanted(pr):
                judge(pr, slug, str(path), lambda s, r, p=path, c=clone, n=pr: add(n, r, s, "worktree", p, c))
        for b in pr_branches(clone):
            pr = int(PR_NAME.match(b).group(1))
            if wanted(pr):
                judge(pr, slug, f"{clone}: branch {b}",
                      lambda s, r, b=b, c=clone, n=pr: add(n, r, s, "branch", b, c))

    for entry, pr, clone in scratch:
        if not wanted(pr) or entry.resolve() in registered:
            continue  # already planned as a registered worktree
        kind = "orphan worktree" if clone else ("loose file" if entry.is_file() else "orphan dir")
        slug = repo_slug(clone) if clone else None
        if not slug:
            clone, slug = owners.get((entry.parent.resolve(), pr), (clone, None))
        judge(pr, slug, str(entry), lambda s, r, e=entry, c=clone, k=kind, n=pr: add(n, r, s, k, e, c))

    print()
    if not plan:
        print("nothing to remove")
    total = 0
    counts = {True: 0, False: 0}
    for pr in sorted(plan):
        e = plan[pr]
        print(f"#{pr} {e['repo'] or 'unknown repo'} {e['state']}")
        for kind, target, clone, size, tracked in sorted(e["items"], key=lambda i: ORDER[i[0]]):
            total += size
            counts[tracked] += 1
            tag = f" {fmt_size(size)}" if size else ""
            src = "" if tracked else " (swept, not recorded)"
            if not opts["delete"]:
                print(f"  would delete {kind}: {target}{tag}{src}")
                continue
            ok, why = remove(kind, target, clone, roots, store, tracked)
            print(f"  {'deleted' if ok else 'kept'} {kind}: {target}{tag}{src}{'' if ok else f'  ({why})'}")

    if opts["delete"]:
        for clone in clones:
            git(["worktree", "prune"], clone)

    print()
    if kept:
        print(f"kept {len(kept)}:")
        for k in kept:
            print(f"  {k}")
    if refused:
        print(f"refused {len(refused)}, a recorded path that must not be deleted:")
        for r in refused:
            print(f"  {r}")
    if gone:
        print(f"{gone} recorded {'path was' if gone == 1 else 'paths were'} already gone")
    if ambiguous:
        print(f"ambiguous {len(ambiguous)}, left alone:")
        for a in ambiguous:
            print(f"  {a}")
    if unresolved:
        print(f"unresolved {len(unresolved)}, left alone:")
        for u in unresolved:
            print(f"  {u}")
    if plan:
        print(f"{counts[True]} from the manifest, {counts[False]} found by the sweep")
    if total:
        print(f"{'reclaimed' if opts['delete'] else 'would reclaim'} {fmt_size(total)}")
    if plan and not opts["delete"]:
        print("re-run with --delete to remove")


if __name__ == "__main__":
    main()
