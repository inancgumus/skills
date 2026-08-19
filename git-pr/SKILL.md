---
name: git-pr
description: Use when drafting or revising PR descriptions, including when the user asks for adding or updating a PR title or description.
---

# PR Description Writing

Write PR descriptions like an experienced engineer talking to another engineer.

Write like a human, not like a robot.

Most PRs are one sentence for What and one for Why. Start there every time.

A complex PR may earn a second paragraph, but only when that paragraph makes the purpose clearer to a reader who does not know the code. Size of the diff is not the test. Purpose is. A migration across forty files with an obvious purpose stays at two sentences, and a three-line change with a purpose nobody would guess may need a paragraph.

Never put diffstat numbers, line counts, file counts, or benchmark figures in it. A reader cannot act on a number they cannot check.

## Workflow

1. Gather context: read the diff, commit history, related issues and PRs. Use `gh` for all GitHub reads (PRs, issues, example PRs). Never use `fetch_content` on GitHub URLs.
2. Summarize what you learned to the user in a few sentences. What the change does, how big it is, what areas it touches.
3. Ask the user what to emphasize, what tone they want, anything they want called out or omitted.
4. Write the title and body inline, formatted exactly as it will appear on GitHub. Do not create the PR yet.
5. Wait for the user to say "post", "ship it", "lgtm", or similar before touching git. If they give feedback, revise and show the updated draft inline again.
6. Push the branch and create the PR with `gh pr create`.

Do not skip step 3 unless the user explicitly says to write without asking. The user knows what matters to reviewers better than you do.

## Posting

Only after the user confirms:

```bash
git push origin <branch>
printf '%s' "$BODY" > /tmp/pr-body.md   # or use the write tool directly
gh pr create --title '<title>' --body-file /tmp/pr-body.md
```

Always write the body to a file and pass `--body-file`. Never inline the body with `--body "..."` or `--body "$(cat <<'EOF' ... EOF)"`. PR descriptions almost always contain backticks (code spans, command names) and most agent command runners wrap the user's command in something like `bash -c "<command>"` for execution. The outer double-quotes trigger backtick expansion before bash ever sees the heredoc, even though `<<'EOF'` would otherwise protect it. Symptom: backticked commands actually run, bare-backticked words emit `command not found`, and tool output lands in the PR description.

Writing the body to a file and passing `--body-file` bypasses every shell layer between the agent and `gh`.

For the title, single-quoted is safe because nothing expands inside single quotes:

```bash
gh pr create --title 'Add `--format` flag to export command' --body-file /tmp/pr-body.md
```

If the title contains a single quote, write it to a file too or use `$'...'` ANSI-C quoting.

## Structure

Three sections, in this order, and nothing else:

````markdown
## What?

<One sentence. The outcome.>

## Why?

<One sentence. The reason.>

<Optional second paragraph, only when the purpose is not obvious from the sentence above.>

## Related PR(s)/Issue(s)

- #NNN
- org/repo#NNN
````

Omit `Related` when there is nothing to link. Never add a section that is not on this list: no `Note`, no `Out of scope`, no `How to reproduce`, no `Notes`, no `Benchmarks`, no evidence table, no plan or command output, no diagram.

The optional paragraph earns its place only if a reader would otherwise ask "why would anyone want that?". It never explains how the code works.

**Never copy the example sentences. Read them to absorb the tone, then write original text from the actual change.**

### `What` section

One sentence. It names the outcome, not the mechanism.

- Write what the reader gets, not what the code does. If the sentence would fit as a code comment, it is at the wrong level.
- Never name a function, package, type, file path, field, flag, line number, or API call. A reader cannot use a name they cannot open, and it pushes the sentence down to code level.
- Do not put the reason here. That is `Why`.
- One sentence. If you cannot say the outcome in one, the outcome is not yet clear to you.

Good: `Aligns the branch protection of the classic repos with other k6-core repos.`
Bad: `Declares each classic branch protection rule in Terraform with an import block so a follow-up can delete it.`

### `Why` section

One sentence. It names the reason or the gain.

- Say who is better off and how. `Enables Renovate to auto-merge on these classic repos.`
- Do not restate the What in other words.
- Do not describe the mechanism, the investigation, the symptom hunt, the error message, or the earlier attempts.
- Do not describe what the PR does NOT do.
- One sentence, plus a second paragraph only when the purpose needs it.

Good: `Fixes an incorrect workflow reference.`
Bad: `The hourly approval run fails at the token step and has never approved anything, because the app configuration names a workflow that does not run, so no matching Vault role exists.`

### The description is not a scratch pad

It stands on its own. A reviewer opening it cold, months later, with no access to the session that produced it, must get the whole point from two sentences.

So none of this goes in:

- What the session discussed, tried, measured, or ruled out.
- Earlier attempts, abandoned approaches, or a closed PR that came before.
- What a previous PR did, unless a live dependency makes the reviewer act differently.
- What the PR does NOT do, does not change, or leaves untouched.
- Follow-up work, unless a reviewer must not apply this one without it.
- Root cause chains, error output, plan output, commands run, or how you proved it.

Every one of those is real and was worth finding. They belong in the commit message, an issue, or a knowledge base. The reviewer needs the decision, not the journey to it.

### The cut test

Draft the two sentences first, then stop. Before posting, read each remaining sentence and ask whether it changes what the reviewer decides. If it does not, delete it.

Extreme conciseness is not vagueness. Cut sentences, never meaning. `Fixes an incorrect workflow reference.` is short and exact. `Fixes some config issues.` is short and says nothing. If cutting a sentence loses a fact the reviewer needs, the sentence you should have cut is a different one.

## PR Titles

- Keep titles short, under 60 characters is ideal, never exceed 72.
- Name the component/area, then the fix or change in plain terms.
- Every word should earn its place. Cut filler when the description
  already covers it.
- Start holistically. Look at the commit subjects and changed files.
  What single concept does the PR revolve around? The title should name
  that concept. Don't dive into the diff first; you'll get lost in
  mechanism and miss the forest for the trees.
- Dig past the surface. Before writing the title, keep asking "why?" or
  "what does this actually do?" until you reach the core.
  For fixes: name the root cause, not the symptom, and not the mechanism.
  Symptoms are what the user sees (nil response, flaky test, crash).
  Mechanisms are how the bug happens technically (read too early, event
  dispatch timing, snapshot vs live state). Root causes are what the code
  gets wrong conceptually (ordering, binding, lifecycle).
  If your title explains how the bug happens, you're naming the mechanism.
  Zoom out.
  For features: name the capability added, not the implementation.
- Good: `browser: fix frame document ordering`
- Bad: `browser: fix navigation request-document ordering` (mechanism, describes how, not what)
- Bad: `browser: fix race between navigation and network events in response lookup`
- Bad: `browser: fix nil response on navigation` (symptom, not cause)

## How to write good PR descriptions

1. Write in natural, human engineering language.
2. Keep `What` and `Why` separate.
3. Keep claims scoped to what the change set proves.
4. Keep language direct, plain, and specific.
5. No code-like terms in the description. No backticks except for issue references.
6. Format issue references as plain `#1234`.
7. Use only the three sections above.
8. One sentence per section. No bullet lists.
9. Avoid template-style phrasing and rhetorical contrast.
10. No Mermaid diagram. Two sentences replace it.
11. Do NOT hard-wrap paragraphs: GitHub renders a single newline in a PR/issue body as a `<br>`, so keep each paragraph on one physical line (blank lines still separate paragraphs) and let it soft-wrap into a block; verify the raw body with `gh pr view <n> --json body -q .body | cat -A`.

## Tone

- Use practical, clear, engineer-to-engineer phrasing.
- Use active voice. Not "documentation is now fetched" but "fetches documentation".
- Never refer to the PR itself. No "this PR", "this change", "it does", "this adds".
- No technical details. Describe what changed for the user or project, not how the code works. The diff is right there.
- Use direct sentences with concrete nouns and verbs.
- Use neutral confidence: state what is known and ask when uncertain.

## Public Repos: Keep Internal Details Out

On a public repo the title, body, branch name, commit message, and references are all world-visible, so keep every internal-only specific out of them and describe only user-observable behavior.

- No internal service, component, repo, or supervisor names, internal issue/run/test IDs, or signal/timeout/knob names that only mean something inside the company's infra.
- If a sentence only makes sense to someone who knows the internal architecture, it's a leak, cut it.
- The branch name and commit message count too: an internal run ID in a branch name leaks the same as one in the body.
- When unsure whether something is internal, treat it as internal; leaks are hard to undo once public.

- Do NOT list internal refactors (helper functions, mutex renames, type extractions)
  in the description. Those belong in the diff, not the PR summary.
- Do NOT over-explain the mechanism. If the What section already says what changed,
  the Why section should not restate it in different words.
- Do NOT pad with extra sentences. One per section, and a second paragraph only when the purpose needs it.
- Write like you're telling a teammate what you did over chat, not writing a report.
- Do NOT use em dashes (—) as connectors. "X — Y" is an AI writing pattern. Use
  periods, commas, or restructure the sentence instead. If you catch yourself joining
  two clauses with an em dash, split them into separate sentences.
- Do NOT use passive voice. Do NOT refer to the PR itself ("this PR", "this change",
  "it does", "this adds").
- The What first sentence must describe impact/outcome, not mechanism. Bad: "Defers
  response reads until after lifecycle events complete." Good: "Fixes frame navigation
  to return responses reliably." If the sentence describes code flow, you're at the
  wrong level.
- Use plain language. Don't write signal names, error codes, or runtime internals when
  a plain description works. "Huge stack trace" beats "SIGSEGV stack trace". If a
  non-Go engineer wouldn't understand the term, rephrase it.

## Backticks and References

- A description names almost nothing. No file paths, no symbols, no line numbers. Backticks are for the few names a reader would actually type or open: a repo, a released version, a user-facing flag or command. The rest belongs in the diff.
- When a name does belong, put it in backticks.
- When referencing a repo at a branch or version, use the `repo@ref` form: `foo@master`, `foo@v2`. Not "foo master" or "foo v2".
- When referencing a specific commit, link it: [`foo@abc123`](https://github.com/org/foo/commit/abc123). Don't say "the previous hash" or "the old commit" without identifying it.
- Cross-repo PR/issue references must include the org/repo prefix: org/repo#123. Bare #NNN only works for the current repo. Don't backtick issue/PR references or GitHub won't auto-link them.
- In the Related section, list each reference on its own line. Don't group with "Depends on" or "Related to" prefixes unless the relationship is genuinely important context.
- Before referencing another repo's issue, check its visibility (`gh repo view <org/repo> --json visibility`): from a public repo a reference into a private/internal repo is world-visible plain text and leaks that repo's name, so confirm it's intended.
- `Closes org/repo#n` from a public repo into a private/internal one won't fill the linked-issues panel or auto-close on merge, so close it from the target repo's side instead.

## Examples

Every one of these is two sentences, from a one-line config change up to a whole subsystem replacement. The shape never changes.

### Config move

**Title:** `config: move validation out of experimental`
```markdown
## What?

Moves config validation into the stable package.

## Why?

Keeps the canonical source in the stable module location.

## Related PR(s)/Issue(s)

- #312
```

### Flag made discoverable

**Title:** `cli: add \`--format\` to help output`
```markdown
## What?

Makes `--format` discoverable in the help output.

## Why?

Users cannot find the flag without reading the docs.

## Related PR(s)/Issue(s)

- #455
```

### Better error message

**Title:** `api: return accurate error on empty name lookup`
```markdown
## What?

Shows "not found" instead of a communication error when a lookup returns nothing.

## Why?

The old message sent users hunting for network problems that were not there.
```

### Concurrency fix

**Title:** `worker: unblock concurrent job creation`
```markdown
## What?

Lets jobs start while another job on the same node downloads its binary.

## Why?

One slow download held up every other job on that node.
```

### Deadlock fix

**Title:** `websockets: fix shutdown deadlock on server pings`
```markdown
## What?

Shuts WebSocket connections down cleanly when the server sends pings during teardown.

## Why?

A ping arriving in that window stalled the process until timeout.

## Related PR(s)/Issue(s)

- #198
```

### Infrastructure alignment

**Title:** `Import k6-core legacy branch protection rules`
```markdown
## What?

Aligns the branch protection of the classic repos with other k6-core repos.

## Why?

Enables Renovate to auto-merge on these classic repos.

## Related PR(s)/Issue(s)

- grafana/k6-pilot#86
```

### One-line config fix

**Title:** `Fix k6-ci auto-approve workflow registration`
```markdown
## What?

Renovate pull requests get approved on `k6-ci` again, so they can merge on their own.

## Why?

Fixes an incorrect workflow reference.

## Related PR(s)/Issue(s)

- grafana/k6-pilot#86
```

### Whole-subsystem replacement

Forty files, a deleted package, a new loading model. The purpose is plain, so two sentences carry it.

**Title:** `docs: always-current documentation, smaller binary`
```markdown
## What?

Loads documentation on demand and refreshes it when it changes, instead of embedding every version in the binary.

## Why?

Stale docs produce wrong code suggestions.

## Related PR(s)/Issue(s)

- #418
```

### When a paragraph earns its place

The purpose here is not guessable from the change, so one paragraph explains it and stops.

**Title:** `renovate: drop the 7-day release age gate`
```markdown
## What?

Lets dependency updates merge as soon as they are green.

## Why?

Security patches waited a week before anyone could merge them.

The gate was there to let a bad release get yanked before it reached us. Renovate now holds a PR until every check passes, which covers the same risk without the wait.

## Related PR(s)/Issue(s)

- grafana/k6-pilot#86
```

### Key patterns

- **Purpose sets the length, not size.** A forty-file migration with an obvious purpose gets two sentences. A three-line change nobody would guess the point of may earn a paragraph.
- **Outcome in What, reason in Why.** If both sentences say the same thing twice, the Why is wrong.
- **Cut, do not compress.** Do not squeeze three facts into one long sentence. Pick the one fact the reviewer needs and drop the rest.
- **The investigation goes elsewhere.** Root cause, error output, plans, comparisons, and rejected approaches belong in the commit message, an issue, or a knowledge base.
