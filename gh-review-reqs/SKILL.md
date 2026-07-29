---
name: gh-review-reqs
description: List open GitHub PRs that need my review attention, across all repos. Use when the user asks what PRs await their review, to check their review requests or review queue, which PRs are waiting on them, or what they should review today — even if they don't say "PR" explicitly.
---

# GitHub Review Requests

List the PRs that genuinely need the user's review, not everything GitHub's "review requested" search returns.

Run the bundled script from this skill's directory and present its output as a markdown table (date, linked PR, title, author, tag):

```bash
scripts/gh-needs-my-review
```

## What the script includes

A PR qualifies only when all of these hold:

- The user is in the PR's **active requested reviewers** (`user-review-requested:@me`). GitHub removes a reviewer from that list when they submit a review and re-adds them on re-request, so this alone handles "reviewed but re-requested". Never filter with `-commenter:@me` or `-reviewed-by:@me`: that hides re-requested PRs and PRs where the user only left comments.
- Required approvals are not met yet (`reviewDecision != APPROVED`).
- Nobody else blocks it with changes-requested. The user's own stale changes-requested review does not exclude the PR: a re-request means the author wants them back.
- In repos without required-review rules: nobody else has reviewed it.
- Not a draft. Not authored by a renovate bot; the k6-deps-review skill handles those.

The script tags a PR with `(re-requested)` when the user reviewed it before.

## Why not `review-requested:@me`

`review-requested:@me` also matches lingering team requests. Teams like grafana/k6-core auto-route review requests to specific members; when the routing picks someone else, the leftover team request still matches even though the user is not expected to review. `user-review-requested:@me` matches only PRs where the user personally is in the reviewer list.

## When a result looks wrong

Inspect the PR's actual state before changing the script:

```bash
gh pr view <num> --repo <owner/repo> --json reviewDecision,reviewRequests,latestReviews
gh api repos/<owner/repo>/issues/<num>/timeline --paginate \
  --jq '.[] | select(.event | IN("review_requested","review_request_removed","reviewed"))'
```

The timeline shows team-request routing (team request removed, individuals added), which explains most surprises.
