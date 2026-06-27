# Pending (draft) PR reviews via `gh`

A pending review holds inline comments that only the author sees until they submit. Omitting `event` is what keeps it pending. Never submit on the human's behalf.

## Create

POST the review with comments and no `event`:

```bash
gh api repos/{owner}/{repo}/pulls/{pr}/reviews --input payload.json
```

`payload.json`:

```json
{
  "commit_id": "<pr head sha>",
  "body": "optional summary, shown only if submitted",
  "comments": [
    {"path": "dir/file.go", "line": 42, "side": "RIGHT", "body": "..."}
  ]
}
```

- No `event` field gives `state: "PENDING"`. `event` of `COMMENT`, `APPROVE`, or `REQUEST_CHANGES` publishes immediately, so never set it.
- `commit_id`: the PR head SHA (`gh api repos/{owner}/{repo}/pulls/{pr} --jq .head.sha`) so your line numbers match the diff you read.

## Anchor a comment

- `path` + `line` + `side`. `side` is `RIGHT` for added/context lines, `LEFT` for removed. GitHub maps `line` to a diff position itself, so you don't compute offsets.
- `line` must fall inside a diff hunk, or the whole call returns 422. Pull valid lines from the patches:

```bash
gh api repos/{owner}/{repo}/pulls/{pr}/files --paginate
```

Added (`+`) and context lines on the new side are valid `RIGHT` anchors; removed lines are `LEFT`.

- Multi-line: add `start_line` (and `start_side`) alongside `line`.

## Suggested change

A comment body can carry a ` ```suggestion ` fenced block; its contents replace the exact line(s) the comment anchors to, and the author applies it in one click. Match the anchor to the lines being replaced (`start_line`..`line` for multi-line). Keep it to a line or two, see SKILL.md § Voice.

## Verify it's a private draft

- `gh api repos/{owner}/{repo}/pulls/{pr}/reviews` → your review's `state` is `PENDING`.
- `gh api repos/{owner}/{repo}/pulls/{pr}/comments --paginate` must NOT contain your comments. Pending comments stay author-only until submitted.
- Pending comments report `line: null` and only a `position` until submitted. That's expected, not a failed anchor.

## Edit or discard

- Replace all comments: delete the review and repost. `gh api -X DELETE repos/{owner}/{repo}/pulls/reviews/{review_id}`, then create again. This is the simplest way to iterate on wording.
- One comment: `gh api -X PATCH repos/{owner}/{repo}/pulls/comments/{comment_id} -f body="..."`.
- Submitting (Finish your review) and discarding (Delete pending review) happen in the human's Files-changed tab. Don't do either for them.
