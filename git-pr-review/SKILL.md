---
name: git-pr-review
description: Review a GitHub pull request. Use when asked to review a PR, given a PR URL, told to "review this", asked to annotate a diff or leave draft comments without sending a review, or asked to handle the author's replies to an earlier review.
user_invocable: true
command: pr-review
---

# git-pr-review

Review a GitHub PR for functional issues that block merge, leave the feedback as inline draft comments, and never send it unless the user says so.

- If the user hasn't named a PR, ask which one.
- Ask what else they want you to check beyond the basics, since it changes per review: parity with a reference implementation, a particular concern, an area to focus on or skip. Take the answer as your standing instructions for this review, on top of the fixed scope below: this skill posts functional blockers only.
- Draft only. Build a pending review; submit or discard only when the user says so.
- Every reviewer, judge, fix-verifier, and proofreader subagent runs at the highest-intelligence model and the highest reasoning effort available. Sonnet or haiku is for exploration only (fetching a reference, skimming a file); never let one of them find, judge, verify, or proofread.
- Report to the user, never to the PR author. Even an "LGTM" is for the user.
- Besides the findings, make the user understand the change itself: open the report to the user with a plain-terms explanation of what the PR does and why, as a short scenario (what the user of the software gets, before and after). No internals, no jargon; the user should get it without reading the diff. This explanation is for the user alone. It stays in the report you write here and never lands on the PR: not in a comment, not in the review summary body, nowhere the author can see it.

## The review

Run this as a reviewer/judge workflow (the Workflow tool): reviewer subagents find the issues, then an independent judge tries to refute each one before it survives. Demand evidence, not conclusions, and re-verify the survivors yourself.

Every `agent()` call that finds or judges a finding sets `model: 'opus', effort: 'max'`, the highest-intelligence model and reasoning effort Workflow offers. Never leave a reviewer or judge at an inherited or default model; that's for exploration subagents only (fetching a linked doc, skimming an unrelated file), not for anything that decides whether the code is right.

Each reviewer and judge writes its full work to `$STATE/evidence/<agent>.md` before returning, and returns that path with its findings. Tell every subagent, in its prompt, that this file takes everything raw and nothing summarized:

- Every code path it traced, quoted verbatim with `file:line`, not described.
- Every experiment and test it ran: the complete test or script source, the exact command line, the working directory and any overlay or setup, and the full unedited output, failures and passes alike.
- Every dead end and refuted theory, with why the evidence killed it.
- What it never checked, so the next reader doesn't mistake silence for coverage.

Length is not a concern here and paraphrase is the failure mode. The returned findings are the summary; the file is the raw record that lets you re-verify, re-anchor, reword, or defend any comment weeks later without running the review again. Anything only in a subagent's head is lost the moment it returns, so if an agent returns without its file, or with a thin one, send it back to write the full version before you use its findings.

Check that the change is idiomatic, simple, and correct, and that it fully solves the linked issue. Read the linked issue(s) and anything the user asked you to check against (a reference implementation, a spec), and confirm the behavior matches.

This review posts only functional issues that block merge: a correctness bug, data loss, a crash, a hang, a race, a security hole, a regression, or the change not actually solving what it set out to. Everything else stays off the PR. Naming, style, formatting, simplifications, structure and design preferences, and optional "nice to have" suggestions are not review comments here, however correct they are. Read for whether the code is idiomatic and simple so you understand it and find the functional problems, not so you can file taste. When a non-blocker is worth saying, it goes in your report to the user, never on the PR. On a clean PR the review is a one-line approval; never manufacture findings to look thorough.

Verify, don't skim. Isolate the PR in a throwaway worktree (`git fetch origin pull/<pr>/head:pr-<pr>` then `git worktree add /tmp/pr-<pr> pr-<pr>`; remove it after), run the affected tests there, and trace the call paths. Never call something broken or correct without checking it; "probably" means you haven't verified yet. A hazard you can reason through but can't trigger isn't a dead end: raise it as the open question it is, don't drop it for want of a repro.

Leave the feedback as inline draft comments, each anchored to the line it's about. Keep the review pending/draft. Never send it to the PR unless the user tells you to.

Every comment MUST use the voice in [§ Voice](#voice); there is no plain mode and no skipping it: concise, casual, like a coworker, what and why, super clear. Ask a question instead of a directive where it fits, but don't overdo it. One finding per comment, and every comment is a functional blocker, never a nit or a preference. No titles, no labels like `test (nit):` or `naming:`. Backtick repo names, code, symbols, and paths. Clean markdown. Apply the `humanizer` and `stop-slop` skills.

## Gather

- `gh pr view <pr> --comments`, `gh pr diff <pr>`, and `gh api repos/{owner}/{repo}/pulls/{pr}/files` for the patches.
- Read the linked issue(s) and any reference the PR or the user points you at. Follow links one level deep; for a heavy reference, send a subagent and read its full return.
- Read prior reviews and comments so you don't repeat them: `gh api repos/{owner}/{repo}/pulls/{pr}/reviews` and `.../comments`.

## State store

- `STATE=${XDG_STATE_HOME:-$HOME/.local/state}/git-pr-review/<owner>-<repo>-<pr>/`. Your scratchpad, not a copy of the PR; keep only what GitHub doesn't (your reasoning and the user's instructions).
- `review.json`: review id, last-seen head SHA, last comment cursor, and the user's standing instructions for this review.
- `notes.jsonl`, keyed by the GitHub review-comment id: why you flagged it, the judge verdict, your current take (`open`/`resolved`/`dropped`), and what the author's replies changed.
- `evidence/<agent>.md`: one file per reviewer/judge subagent, raw and unsummarized: quoted code with `file:line`, full test sources, exact commands, unedited output, dead ends, and what went unchecked. Written by the subagent itself, complete enough that someone else can reproduce every claim from the file alone. Keep these; they outlive the subagents.
- `replies.json` (written by `fetch_replies.py`) and `replies-out.json` (drafts for `post_replies.py`): the follow-up round's input and output.
- No tokens, no secrets.

## Post the draft (private)

- Before any post or repost, spawn a fresh subagent to proofread, same model and effort bar as [§ The review](#the-review): it reads this entire SKILL.md, then the summary body and every comment in `comments.json`, and checks each one against [§ Voice](#voice), its rules, and the [§ Red flags](#red-flags-rewrite-before-posting) checklist. It rewrites every body that trips a red flag down to the question and returns the corrected bodies. A comment that still trips a red flag does not post. No posted body, summary or comment, ever contains the plain-terms change explanation, which is for the user only. Post the corrected version, not your draft.
- Put the comments in `comments.json` and run `scripts/post_pending_review.py <owner/repo> <pr> comments.json [--body "summary"]`. It resolves the head SHA, posts one PENDING review, and checks the drafts aren't public. The `--body` is at most the optional one-line opener; never put the plain-terms change explanation there, it is for the user only.
- Anchor each comment to a diff line (`RIGHT` for added/context, `LEFT` for removed) or GitHub rejects it (422). If the code isn't in the diff, anchor to the nearest changed line and say so. Pull valid lines from the `files` patches. Mechanics: [references/pending-review.md](references/pending-review.md).
- Confirm `state=PENDING` and `published delta: 0`, save the ids, and hand the user the Files-changed URL. Don't submit. To change a draft, delete and repost: `gh api -X DELETE repos/{owner}/{repo}/pulls/reviews/{review_id}`, then rerun.

## Submit (only on the user's say-so)

- Never POST a review event on your own. When the user says to: `gh api -X POST repos/{owner}/{repo}/pulls/{pr}/reviews/{review_id}/events -f event=COMMENT` (or `APPROVE` / `REQUEST_CHANGES`).

## Follow-up (the author replied)

The review already happened; this round checks whether it was answered well. Rebuild the context first: read the earlier findings in `evidence/` and `notes.jsonl`, get a full understanding of the PR itself, and reread every comment we left. Then check each comment against the current head: applied correctly, deferred with a reason, or not addressed. Review the fix commits like any change; a fix can be wrong, half-done, or break something else.

- Start from the state store: `review.json`, `comment_ids.json`, and `evidence/` already hold the reviewed head SHA, the thread roots, the user's standing instructions, and the repros.
- `scripts/fetch_replies.py <owner/repo> <pr>` fetches the replies, pairs them to our threads, writes `$STATE/replies.json`, and warns when the head moved since the review.
- Expect a rebase. Commit SHAs cited in replies may be gone; fetch the current head (`git fetch origin pull/<pr>/head:pr-<pr>`) and verify each claim by content there, matching the cited commits by subject.
- Verify every "fixed in X" claim and review the fix itself; never take the reply's word. Run this as a Workflow too, one subagent per fix area in parallel, each in its own detached worktree (`git worktree add --detach <dir> <head-sha>`, removed after), same model and effort bar as [§ The review](#the-review), each writing `evidence/<agent>.md` as in [§ The review](#the-review). Re-run the repros from `evidence/`: a fixed bug's repro must stop failing, and a new test must pin the fix. Hold each fix commit to the original review's bar (correct, simple, idiomatic, no new bugs); anything it breaks or leaves half-done becomes a new draft comment. Fact-check the excuses too: "predates this PR" means diffing that code against the merge-base; "also affects X" means tracing X's path.
- Report to the user as a checklist first: one row per original comment, marked addressed / deferred with the reason / not addressed, then the questions the author aimed at the user. Verification detail comes after the checklist, never instead of it.
- The author's questions are the user's to answer; wait for their decision. Then draft the reply bodies into `$STATE/replies-out.json`, proofread them with a fresh subagent against [§ Voice](#voice) and the [§ Red flags](#red-flags-rewrite-before-posting) checklist at the same model and effort bar as [§ The review](#the-review), and run `scripts/post_replies.py <owner/repo> <pr> replies-out.json`: it posts into the threads and records each outcome in `notes.jsonl`. Replies publish immediately, so only run it with user-approved bodies.

## Watch loop (only when the user asks)

- Run with the `/loop` skill. Each tick, compare against `review.json`'s last-seen head SHA and comment cursor; no new commits and no new replies means wait.
- On new activity, re-fetch the branch, re-verify any finding the new commits touch, and handle replies per [§ Follow-up](#follow-up-the-author-replied). When a commit moves a line, re-anchor the comment; when the code is gone, mark it `resolved` or re-target it. Delete+repost so a later send lands right.
- Report to the user, not the PR. Draft any reply into the store and get the user's OK before sending. Stop when the user says so, or when the PR merges or closes.

## Voice

This section is mandatory for every body that lands on GitHub: review comments, the summary, and replies in the follow-up round. No body posts without the proofread pass against it.

The comment's whole job is to make the author look at one spot and decide for themselves. It is not there to prove you are right, to teach them how their own code works, or to hand them the fix. However much digging it took to find the spot, none of that goes in the comment. Ask whether the thing you suspect is real, point at the one place, and stop. The author validates, not you.

So the target shape is small and shaped like a question. A long comment is not thorough, it is a mistake you have not caught yet. Big, or explaining, or fixing means you are making your case at the author instead of asking them, and it gets rewritten before it posts (see [§ Red flags](#red-flags-rewrite-before-posting)). Be humble and hand the judgment over. State a doubt as a question the author answers, not as a claim you assert. Say nothing about what you did to find it; a review comment never contains "I traced", "I confirmed", "I checked", or "I think".

Write every comment the way these examples do. They are real review comments, verbatim, from many different PRs. Absorb the register, the hedging, and the shape; never reuse the words. Re-read them before each comment.

A debatable point leads with a question, with a guess attached when there is one:

> Wouldn't this panic if `first()` returns `nil`?

> Is the overwrite (by object keys) here intentional?

> Is this a race condition or a data race? Feels like the latter?

> Why is this `errors.Is` necessary, and what does it do?

> Do we no longer need these?

> Why do we remove this test? Is it no longer required?

> Should this be `0`?

> Forgotten?

A real bug drops the hedges, gets specific, and shows the mechanism or the trace:

> This might fail if Unicode characters are passed. See: https://go.dev/blog/strings.

> I'm not sure what you mean here. We should handle the error because otherwise we might mistakenly put `0` into `idx` if we don't handle the error, as `Atoi` will return zero after a non-`nil` `error`.

> `rs.cancel()` cancels `maxDurationCtx`, but `iterateSteps` uses the parent `ctx`, so `waiter` (the closure that sleeps between steps) never sees the cancellation. After this handler returns, the remaining raw steps keep getting processed. Each re-enters here, `start()` fails and logs again. With a multi-stage config (e.g., 0->2, 2->4 over 1s total), the error is logged many times, and the executor blocks for longer than it should.

> There are race conditions due to the usage of error values. We're probably carrying on some pointers in error values that are shared with Sobek somehow. This could be of because `fmt` funcs might be buffering some values.
>
> Could you check the stack trace, and find the issue?
>
> Other than that it's LGTM!

> `require.NoError` in HTTP handler goroutine → `t.FailNow()` from non-test goroutine is undefined behavior per Go testing docs. Use `assert` and return.

When a fix ships without proof it works, ask for that proof:

> Does this test fail without your fix?

Most approvals are a line or an emoji:

> LGTM functionally.

> I didn't see any issues. LGTM.

> Pretty clean PR 👍

> Nice catch ⚾

The rules these follow:

- Point at the spot, let the author validate; don't prove it to them. You did the digging, the comment doesn't show it. Ask whether the thing you suspect is real, name the one place to look, and stop. The author confirms or refutes it from their own knowledge faster than your proof reads, and a question they answer lands better than a verdict they defend. This holds even after you have confirmed it yourself: a question that makes them look beats a case that makes them read. When in doubt, cut a sentence and ask instead.
- One finding per comment, and every comment is a functional blocker: a bug, data loss, a crash, a hang, a race, a security hole, a regression, or the change not solving what it set out to. Nits, style, naming, simplifications, and design or preference points never post; put them in your report to the user. Let the change set the count: several comments on a buggy PR, a one-line LGTM on a clean one. Don't bundle distinct points into one note, and don't invent findings to look thorough.
- Lead a debatable point (a bug you suspect but aren't sure of, a behavior that looks wrong, a "do we still need this?") with a question, and attach your own guess when you have one. For a clearly-correct functional fix, a terse line is fine.
- Hedge your certainty, not the finding. When you are not sure the problem is real, ask; the question is the humble default. Once you are sure, cut the weasel words ("maybe", "I think", "it seems") and name the spot precisely, still as the question that sends them straight to it (see the first rule). You never hedge because something is "just a preference": a preference does not post at all.
- Keep it short. A nit is one clause; a hazard is the consequence plus the ask. Run longer only for a hard blocker whose consequence has to be spelled out to land. Don't explain the mechanism back to the author past what the question needs. The length tracks the finding, not the effort behind it: a spot you are sure of after long digging is still one question.
- Everyday words over coined ones. Hyphenated compounds and borrowed metaphors you wouldn't say out loud ("load-bearing", "fail-closed", "always-called", "catalog-served", "a non-issue") make the reader decode instead of read. Unpack them: "things break without this check", "skips the send on error", "runs on every call", "a stub the catalog advertises", "not a problem".
- Keep the receipts in your notes, not the comment. The trace, the repro, the before/after, the failing output: those live in the state store so you can defend the point weeks later, not in the comment where the author has to read them to reach the question. The comment carries the question; bring one line of evidence into it only when you must assert a hard blocker or the author has pushed back, and even then show the result, never the narration ("I traced... I confirmed..."). A link to an outside source (a doc, a spec, the failing CI run) is fine, since that points them somewhere rather than proving your case at them.
- Don't hand over a fix before the author agrees the problem is real. Ask first; the fix is a separate, later step, and often theirs to choose. When you do give one, it fixes a confirmed blocker the author has agreed is real, it lives in a `suggestion` block, and it is one you have actually run, never a patch you only reasoned about.
- Never restate an obvious edit; open with the question or the consequence they might have missed.
- Warm and brief by default: an emoji where it fits (🙇 ❤️ 👍 🎉 🚀), and most approvals are just a line or an emoji. Talk to the author as a peer; skip formulaic openers like "thanks for your contribution".
- Link sources: the Go blog, MDN, pkg.go.dev, the failing CI run, a prior discussion thread, a sibling PR. Cross-reference instead of repeating yourself.
- Backtick every symbol, type, path, and env var.
- No headings, titles, verdicts, severity labels (`correctness:`, `test (nit):`), numbered sections, or anchor labels (`RIGHT`/`LEFT`) anywhere in the comment text. Each comment stands alone, never a section in a bundled report. The whole review is those standalone comments plus an optional one-line opener, which you skip entirely when it would only restate a comment; never a "Verdict", "Overall", or "Request changes" block.
- Apply the `humanizer` and `stop-slop` rules: no em dashes, no filler or adverbs, active voice, varied rhythm.

### Red flags (rewrite before posting)

Run this against every comment body before it goes into `comments.json`, and again in the proofread pass. Any hit means the comment is too big or hand-holds the author. Rewrite it down to the question and re-check. These are stop conditions, not style preferences: a comment that trips one does not post. They target comments that are big, explaining, or proving a case. A terse one-line fix for an obvious functional problem is already the smallest useful form; leave it as the plain statement it is.

- **Not a functional blocker.** The finding is a nit, a style or naming point, a simplification, a formatting change, or a design, structure, or preference opinion. It never posts; if it is worth saying at all, it goes in the report to the user. Only a bug, data loss, a crash, a hang, a race, a security hole, a regression, or the change not solving what it set out to earns a comment.
- **More than three sentences.** Most comments are one or two. If you need more, you are explaining, not asking. The only exception is a hard blocker whose mechanism has to be spelled out to be believed, and even then, question first.
- **A block that shows your work.** A before/after, a repro, pasted test or tool output, a step-by-step of what the code does. That is a receipt. It lives in your notes, never in the comment.
- **Any first-person account of your investigation:** "I think", "I'm not sure", "I traced", "I confirmed", "I checked", "it seems to me". State nothing about what you did. Ask the author.
- **A fix, a patch, or a `suggestion` block for a problem the author has not agreed is real.** Ask whether the problem is real first. The fix is a separate, later step, and usually theirs to pick.
- **The mechanism spelled out** past the one clause the question needs (which function calls which, why it fails, what the flag defaults to). Cut it to the question.
- **A verdict:** "this breaks", "this is a bug", "this will fail". Turn it into the question that makes the author reach that conclusion themselves.
- **The comment reads fine with the author's answer already assumed.** If you are not actually waiting for their reply, you are lecturing, not reviewing.

The reflex: the moment a comment feels thorough or complete, treat that as the warning, not the goal. Delete a sentence, turn the claim into a question, and post the smallest version that still points at the spot.
