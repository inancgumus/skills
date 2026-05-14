---
name: git-pr-review
description: Review GitHub pull requests with verification. Reproduces claims, tests locally when possible, and posts inline review comments via `gh`. Use when the user asks to review a PR, gives a PR URL, or says "review this".
user_invocable: true
command: pr-review
---

# PR Review

Review GitHub PRs by verifying claims, not skimming diffs.

## Workflow

### 1. Load skills

Use the `stop-slop` skill when writing or replying. Use `go` and `go-patterns` skills for reviewing Go code.

### 2. Gather context

```bash
gh pr view <number> --repo <owner/repo> --json title,body,author,state,baseRefName,headRefName,additions,deletions,files,labels,reviews,comments,statusCheckRollup
gh pr diff <number> --repo <owner/repo>
```

Read the PR description carefully. Extract every testable claim from the body (test plans, behavioral assertions, config correctness, compatibility statements).

If the diff touches files you need surrounding context for, read those files from the repo.

### 3. Verify claims

This is the core of the review. Do not skip it.

Verify every claim independently. Do not stop at the first bug. A PR can have multiple incorrect claims, wrong assumptions, or mismatched behavior. Test each one to completion. Collect all findings.

For each claim in the PR description or commit messages:

- **Config/infra PRs** (CI, Renovate, Terraform, Docker): reproduce locally. Use Docker containers, dry-run tools, or local validation commands. Run against the PR author's actual repo and branch to confirm the config does what the PR claims.
- **Code PRs**: trace the code paths the PR changes. Read callers, check edge cases, verify error handling. Try the PR author's changes in an exact setup using their code to see if what they claim matches the expected behavior. Run tests if the repo is local. For Go code, run `go vet`, `golangci-lint`, and `go test` on affected packages.
- **Docs PRs**: verify technical accuracy of claims. Check linked references. Confirm code examples compile or run.

Not every PR needs Docker reproduction. Use judgment:

- Config that references external APIs or services: verify the API exists and behaves as assumed.
- Pure code refactors with passing CI: trace the logic, check tests cover the change.
- New features: verify the test plan covers the claimed behavior.

Never assume. If you lack the information to verify a claim, run code, do experiments, search docs or the web. If you still cannot verify after exhausting those, say so explicitly in the posted inline review.

### 4. Find unclaimed problems

After verifying all claims, inspect the diff for problems the PR author didn't mention: wrong defaults, missing edge cases, conflicts with existing config or code, silent failures, incorrect assumptions. Continue until you've found every problem with the PR.

### 5. Check CI status

Check for CI failures or skips. If all green, move on.

### 6. Write inline reviews

Each finding becomes an inline review targeting a specific line or range in the diff.

Rules:

- Keep it short. One or two sentences max for the explanation. The PR author is an engineer, not a reader.
- Do not narrate your investigation process. No "I ran X and saw Y" or "Confirmed via Z". State the problem and the fix.
- When suggesting a code change, use a `suggestion` block (GitHub's format). Prefer these. They let the PR author apply the fix in one click.
- No line numbers in the review text. The inline review is already attached to the right line.
- Use backticks for technical terms: datasource names, function names, file paths, CLI flags, config keys, error messages.
- No filler, no hedging, no "I think", no "consider". State facts.

### 7. Present findings to user

Do not post anything to GitHub yet. Show each inline review exactly as it would be sent to GitHub. Do not add extra commentary for the user. The user must see what would be sent to GitHub for each finding, including all formatting, markdown, and `suggestion` blocks. The user decides which to post, edit, or drop.

You must directly show the markdown for each inline review to the user without any additional commentary or formatting.

Wait for explicit confirmation before posting.

### 8. Post the review

Only after user says to post ("send", "post", "ship", "lgtm", or similar).

Submit all inline reviews in one GitHub review. Build the JSON payload with `jq` to avoid shell escaping:

```bash
jq -n \
  --arg body "" \
  --arg event "COMMENT" \
  --slurpfile comments /tmp/review-comments.json \
  '{body: $body, event: $event, comments: $comments[0]}' \
  > /tmp/review-payload.json

gh api repos/{owner}/{repo}/pulls/{number}/reviews \
  --method POST \
  --input /tmp/review-payload.json
```

Each object in the JSON array:

- `path`: file path relative to repo root
- `line`: line number in the new version of the file (not the diff position)
- `side`: `RIGHT` for new code
- `body`: the inline review text with `suggestion` blocks if applicable

For multi-line inline reviews, add `start_line` and `start_side` to target a range.


### 9. Clean up

Remove local clones, temp files, and Docker containers created during verification.

## Comment format

One sentence that explains the issue. Add evidence or fix after if needed.

When a concrete fix exists, add a `suggestion` block after the paragraph. The block replaces the lines the comment targets (the `line` and optional `start_line` in the review API). Content inside must be exact replacement text, matching the file's indentation. GitHub renders it as a one-click "Apply suggestion" button.

## What makes a good inline review

- States a fact the PR author can verify. Not opinion.
- Gives a concrete fix via `suggestion` block, or names the specific question.
- Short. The PR author should understand the problem in seconds.

## What to avoid

- Style issues. Review behavior, not style.
- Restating what the diff already shows ("I see you added X").
- Praise ("nice work", "clever approach").
- Hedging ("you might want to consider").
- Multiple paragraphs when one sentence covers it.
- Reviewing things outside the diff scope.
