---
name: git-pr-review
description: Review GitHub pull requests with verification. Reproduces claims, tests locally when possible, and posts inline review comments via `gh`. Use when the user asks to review a PR, gives a PR URL, or says "review this".
user_invocable: true
command: pr-review
---

# PR Review

Verify claims, not skim diffs.

## Gathering context

Before analysis, build full context:

1. Read PR description, diff, all comments (`gh pr view --comments`, `gh pr diff`).
2. Extract every linked reference: issue URLs, PR URLs, doc links, commit SHAs.
3. Check existing review comments (`gh api repos/{owner}/{repo}/pulls/{number}/reviews` and `/comments`).
4. Dispatch subagents parallel — one per linked reference. Subagent reads full content (issue body, comments, linked PRs, docs), returns raw unabridged. No summarize. Follow nested references one level deep.
5. Study every subagent response full. No skim.

Now know: problem PR solves, what tried before, constraints, what reviewers said. Then analyze.

## Finding bugs

Extract every testable claim from PR description (test plans, behavioral assertions, config correctness).

Verify each independently. No stop at first bug. Never assume. Lack info? Run code, experiment, search docs/web.

Chase root cause. Trace every symptom to root. Exhaust all WHY chains. Fix = root cause only. Never suggest symptom patch.

- **Config/infra**: reproduce locally. Docker, dry-run, validation. Run against PR author's actual repo/branch.
- **Code**: trace paths. Callers, edge cases, error handling. Run PR author's changes exact setup. Go: `go vet`, `golangci-lint`, `go test` affected packages.
- **Docs**: verify accuracy. Check references. Confirm examples compile/run.

After claims verified, inspect diff for unmentioned problems: wrong defaults, missing edge cases, conflicts, silent failures, bad assumptions. Find every problem.

Check CI failures/skips. All green, move on.

## Writing inline reviews

One finding, one line. Problem, then fix. `suggestion` blocks for concrete fixes.

Prioritize internally (broken > fragile > minor). No severity labels in output.

**Drop:** "I noticed...", "It seems...", "You might want...", "suggestion but...", "Great work!", investigation narration, restating diff, hedging, praise, filler, style nits.

**Keep:** exact symbols in backticks, concrete fix, *why* if not obvious.

## Examples

❌ "I noticed that on line 42 you're not checking if the error is nil before accessing the response body. This could potentially cause a nil pointer dereference if the request fails. You might want to add an error check here."

✅ `err` unchecked before `resp.Body` access. `nil` pointer on failed request.

❌ "It looks like this function is doing a lot of things and might benefit from being broken up into smaller functions for readability."

✅ 50-line function does 4 things. Extract validate/normalize/persist.

❌ "Have you considered what happens if the API returns a 429? I think we should probably handle that case."

✅ No retry on 429.

```suggestion
	resp, err := withBackoff(3, func() (*http.Response, error) {
		return client.Do(req)
	})
```

## Presenting to user

Do not post to GitHub yet. User decides post/edit/drop. Wait explicit confirmation. MUST: Recheck all findings follow this skill's rules before presenting. Show each finding to the user in ` ```markdown ` fence: raw markdown sent to GitHub (including `suggestion` blocks).

## Posting

Only after user confirms ("send", "post", "ship", "lgtm").

Submit all inline reviews one GitHub review via `gh api`:

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

Each object: `path` (file), `line` (new file line, not diff position), `side` (`RIGHT`), `body` (review text + `suggestion` blocks). Ranges: add `start_line`, `start_side`. `suggestion` blocks must target exact code line they replace — wrong line = PR author applies fix wrong place.

After posting, remove local clones, temp files, Docker containers.
