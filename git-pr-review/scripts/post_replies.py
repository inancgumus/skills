#!/usr/bin/env python3
"""Post approved replies into review-comment threads and record the outcomes.

Usage:
  post_replies.py <owner/repo> <pr_number> <replies.json>

replies.json is a JSON array of objects:
  {"in_reply_to": 123, "body": "...", "take": "resolved", "note": "why"}
  - in_reply_to is the id of OUR root comment in the thread.
  - take defaults to "resolved", note to "".

Replies publish immediately (there is no draft state for replies), so run
this only with user-approved bodies. Each posted reply is appended to
$STATE/notes.jsonl as {comment_id, take, note, reply_id}.
"""
import json
import os
import subprocess
import sys
from pathlib import Path


def gh(args, stdin=None):
    out = subprocess.run(["gh", *args], input=stdin, capture_output=True)
    if out.returncode != 0:
        sys.exit(f"gh {' '.join(args)} failed:\n{out.stderr.decode()}")
    return out.stdout


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__.strip())
    repo, pr, path = sys.argv[1], sys.argv[2], sys.argv[3]
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    store = Path(base) / "git-pr-review" / f"{repo.replace('/', '-')}-{pr}"
    if not store.is_dir():
        sys.exit(f"no state store at {store}; run the review first")

    replies = json.loads(Path(path).read_text())
    for r in replies:
        if not r.get("in_reply_to") or not r.get("body", "").strip():
            sys.exit(f"reply needs in_reply_to and a non-empty body: {r}")

    with open(store / "notes.jsonl", "a") as notes:
        for r in replies:
            posted = json.loads(gh(
                ["api", f"repos/{repo}/pulls/{pr}/comments/{r['in_reply_to']}/replies",
                 "--input", "-"],
                stdin=json.dumps({"body": r["body"]}).encode(),
            ))
            notes.write(json.dumps({
                "comment_id": r["in_reply_to"],
                "take": r.get("take", "resolved"),
                "note": r.get("note", ""),
                "reply_id": posted["id"],
            }) + "\n")
            print(f"replied in {r['in_reply_to']}: {posted['html_url']}")

    print(f"posted {len(replies)}, recorded in {store / 'notes.jsonl'}")


if __name__ == "__main__":
    main()
