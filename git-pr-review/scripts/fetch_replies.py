#!/usr/bin/env python3
"""Fetch the author's replies to an already-submitted review.

Usage:
  fetch_replies.py <owner/repo> <pr_number>

Reads the state store (comment_ids.json, review.json), fetches every review
comment on the PR, and pairs replies to our threads by in_reply_to_id. Writes
$STATE/replies.json and prints a per-thread summary, plus a warning when the
PR head no longer matches the SHA the review was made against.
"""
import json
import os
import subprocess
import sys
from pathlib import Path


def gh(args):
    out = subprocess.run(["gh", *args], capture_output=True)
    if out.returncode != 0:
        sys.exit(f"gh {' '.join(args)} failed:\n{out.stderr.decode()}")
    return out.stdout


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__.strip())
    repo, pr = sys.argv[1], sys.argv[2]
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    store = Path(base) / "git-pr-review" / f"{repo.replace('/', '-')}-{pr}"
    if not (store / "comment_ids.json").is_file():
        sys.exit(f"no state store at {store}; run the review first")
    ours = {c["id"]: c for c in json.loads((store / "comment_ids.json").read_text())}
    reviewed_sha = json.loads((store / "review.json").read_text()).get("head_sha", "")

    head = gh(["api", f"repos/{repo}/pulls/{pr}", "--jq", ".head.sha"]).decode().strip()
    comments = json.loads(gh(["api", "--paginate", f"repos/{repo}/pulls/{pr}/comments"]))

    threads = {
        cid: {"path": c["path"], "line": c.get("line"), "root_body": "", "replies": []}
        for cid, c in ours.items()
    }
    for c in comments:
        if c["id"] in threads:
            threads[c["id"]]["root_body"] = c["body"]
        elif c.get("in_reply_to_id") in threads:
            threads[c["in_reply_to_id"]]["replies"].append({
                "id": c["id"],
                "user": c["user"]["login"],
                "created_at": c["created_at"],
                "body": c["body"],
            })

    (store / "replies.json").write_text(json.dumps({
        "head_sha": head,
        "reviewed_sha": reviewed_sha,
        "rebased": head != reviewed_sha,
        "threads": threads,
    }, indent=1))

    flag = "  <-- head moved since the review, verify claims by content" if head != reviewed_sha else ""
    print(f"head {head[:9]}, reviewed at {reviewed_sha[:9]}{flag}")
    answered = sum(1 for t in threads.values() if t["replies"])
    print(f"threads {len(threads)}: {answered} replied, {len(threads) - answered} unanswered")
    for cid, t in threads.items():
        if t["replies"]:
            users = ",".join(sorted({r["user"] for r in t["replies"]}))
            print(f"  {cid} {t['path']}: {len(t['replies'])} from {users}")
        else:
            print(f"  {cid} {t['path']}: no reply")
    print(f"wrote {store / 'replies.json'}")


if __name__ == "__main__":
    main()
