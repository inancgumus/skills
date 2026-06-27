#!/usr/bin/env python3
"""Create a PENDING (draft) PR review with inline comments. Never submits.

Usage:
  post_pending_review.py <owner/repo> <pr_number> <comments.json> [--body "summary"]

comments.json is a JSON array of objects:
  {"path": "dir/file.go", "line": 42, "body": "...", "side": "RIGHT", "start_line": 40}
  - side defaults to "RIGHT" (use "LEFT" for removed lines).
  - line must fall inside the PR diff or GitHub rejects the whole call (422).

Resolves the PR head SHA, posts one pending review, prints id/state/url, and
verifies the drafts are not publicly visible (pending comments are author-only
until submitted). Exits non-zero if the result is not a private PENDING draft.
"""
import argparse
import json
import subprocess
import sys


def gh(args, stdin=None):
    out = subprocess.run(
        ["gh", *args], input=stdin, capture_output=True
    )
    if out.returncode != 0:
        sys.exit(f"gh {' '.join(args)} failed:\n{out.stderr.decode()}")
    return out.stdout


def published_count(repo, pr):
    data = json.loads(gh(["api", f"repos/{repo}/pulls/{pr}/comments", "--paginate"]))
    return len(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", help="owner/repo")
    ap.add_argument("pr", type=int)
    ap.add_argument("comments", help="path to comments JSON array")
    ap.add_argument("--body", default="", help="review summary (only shown if submitted)")
    a = ap.parse_args()

    with open(a.comments) as fh:
        comments = json.load(fh)
    for c in comments:
        c.setdefault("side", "RIGHT")

    head = gh(["api", f"repos/{a.repo}/pulls/{a.pr}", "--jq", ".head.sha"]).decode().strip()
    payload = {"commit_id": head, "body": a.body, "comments": comments}

    before = published_count(a.repo, a.pr)
    r = json.loads(gh(
        ["api", f"repos/{a.repo}/pulls/{a.pr}/reviews", "--input", "-"],
        stdin=json.dumps(payload).encode(),
    ))
    after = published_count(a.repo, a.pr)

    print(f"review {r.get('id')} state={r.get('state')} ({r.get('user', {}).get('login')})")
    print(r.get("html_url", ""))
    print(f"comments posted: {len(comments)} | published delta: {after - before} (must be 0)")

    if r.get("state") != "PENDING" or after != before:
        sys.exit("ERROR: review is not a private draft, check it on GitHub")


if __name__ == "__main__":
    main()
