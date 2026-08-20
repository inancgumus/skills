#!/usr/bin/env python3
"""Remove state-store directories whose PR is merged or closed.

Usage:
  cleanup_state.py            # list what would go
  cleanup_state.py --delete   # remove them

Reads every <owner>-<repo>-<pr> directory under the state store, asks GitHub
for the PR state, and drops the ones that are no longer OPEN. Prints one line
per directory, and the ones it could not resolve.
"""
import shutil
import subprocess
import sys
from pathlib import Path
import os


def pr_state(repo, pr):
    out = subprocess.run(
        ["gh", "pr", "view", pr, "-R", repo, "--json", "state", "-q", ".state"],
        capture_output=True,
    )
    if out.returncode != 0:
        return None
    return out.stdout.decode().strip()


def main():
    delete = "--delete" in sys.argv[1:]
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    root = Path(base) / "git-pr-review"
    if not root.is_dir():
        sys.exit(f"no state store at {root}")

    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        owner, _, rest = d.name.partition("-")
        repo, _, pr = rest.rpartition("-")
        if not pr.isdigit() or not repo:
            print(f"{d.name}: skipped, name is not <owner>-<repo>-<pr>")
            continue
        state = pr_state(f"{owner}/{repo}", pr)
        if state is None:
            print(f"{d.name}: skipped, gh could not read {owner}/{repo}#{pr}")
        elif state == "OPEN":
            print(f"{d.name}: kept, OPEN")
        elif delete:
            shutil.rmtree(d)
            print(f"{d.name}: deleted, {state}")
        else:
            print(f"{d.name}: would delete, {state}")


if __name__ == "__main__":
    main()
