---
name: git-issue
description: Write and file GitHub issues, both bug reports and everything else (feature requests, proposals, tech-debt briefs, questions). Use when the user asks to file, open, write, or draft an issue, to report a bug upstream, to turn a finding into a ticket, or to rewrite an existing issue body. Not for pull requests.
---

# Issue Writing

An issue is a case, not a changelog. It exists to make a maintainer who has never seen the problem care about it and know what to do next.

Write it the way you would tell a colleague over coffee: short, plain, no jargon, no proving how much you dug. One reader, one pass, no second read.

## Not a PR

An issue is not a PR description. Never write `## What?` / `## Why?`. Never mention the diff, the branch, the files you touched, or the fix you have in mind.

The fix is the maintainer's call. You may name the constraint the fix must respect. You may not hand over a patch, a code sketch, or a "just change X to Y".

Two exceptions, both one line at most: pointing at the code that causes it (a permalink, never a paste), and linking a PR or issue that already touches it.

## Before you write

1. **Search for duplicates. Always.** `gh issue list --repo <owner/repo> --search "<terms>" --state all --limit 30`. Try the symbol name, the error text, and the plain-English symptom separately, because they find different issues. If one already exists, say so and stop; comment on it instead of filing a second. Filing over an open duplicate is worse than not filing.
2. **Read the repo's templates.** `ls .github/ISSUE_TEMPLATE/`. Use their section headings as your markdown headings so your issue reads like the others. A form template (`.yaml`) does not apply to `gh issue create --body-file`, so you have to write those headings yourself.
3. **Check the labels** other issues of this kind carry, and pass the same ones.

## Voice

- **Lead with what the user loses.** "Reusing one buffer silently encrypts with the wrong `iv`" beats "the parameter aliases the JS-side backing store".
- **One or two sentences per section.** Cut every sentence that does not change the reader's mind.
- **Plain words.** No coined compounds, no borrowed metaphors, no "load-bearing", "fail-closed", "non-trivial". Say the everyday thing.
- **Say it once.** No punchy closing line, no restating the summary at the end.
- **Never narrate your investigation.** No "I traced", "I confirmed", "I ran the race detector and". Show the result, not the hunt.
- **Show, don't tell.** Paste the real output, trimmed to the lines that carry the point. Never a full stack trace when three lines do. Never a screenshot of text.
- **Backtick** every symbol, path, flag, and version. Link every doc, spec, issue, and PR you mention.
- **Numbers only if the reader can check them.** "Not one of 12,800 samples went above `255`" earns its place. "75.1% of bytes" does not, unless you say what you sampled.
- No em dashes. No horizontal rules. Active voice.

## Bug reports

Follow the repo's bug template headings. When it has none, use these.

````markdown
## Brief summary

<What breaks, in the user's terms, and what it costs them. Two sentences at most. Name what is *not* affected if that narrows it usefully.>

## Environment

**Version:** <the released versions you reproduced on, plus how far back the cause goes>

**OS:** <yours, and whether it matters>

## Steps to reproduce the problem

```js
<The smallest script that shows it. No test harness, no helpers the reader has to trust,
no unrelated setup. It must run as pasted.>
```

## Expected behaviour

<One sentence. Cite the spec or another implementation when there is one.>

## Actual behaviour

```
<Real output. The first line should tell the story on its own.>
```

<Optional, one line: the scale of it, or the shipped example that does the wrong thing.>
````

### Reproduce on a release, not on `master`

The version field is a promise. Build the tag and run it:

```bash
git worktree add --detach /tmp/vX <tag> && cd /tmp/vX && go build -o /tmp/bin-vX .
/tmp/bin-vX run /tmp/repro.js
```

Then say what you actually did: "reproduced on `v2.2.0`; the same code is in `v1.8.1`". Never imply you ran a version you only read. If you checked one line by reading the source of another tag, say "the same code is in", not "reproduced on".

Pin how far back it goes with `git log -L <start>,<end>:<file>` and `git tag --contains <sha>`. One clause is enough: "unchanged since WebCrypto landed in `v0.44.0`".

### A crash

Three lines of panic, not thirty. Say plainly what the user loses: whether `try`/`catch` helps, whether the process survives, whether a long run loses the iterations it already finished.

## Everything else

Feature requests, proposals, tech-debt briefs. Five sections, in this order. Most are one short paragraph; a table earns its place only when two things differ across the same columns.

````markdown
## Problem

<What is missing or wrong today, and who notices. State the gap as fact, not as a
complaint and not as a request.>

## Significance

<Why it is worth someone's week. The concrete decisions or workflows it blocks. Real
questions nobody can answer today land better than adjectives.>

## Cost of inaction

<What keeps happening if this stays open. Name what erodes, not "technical debt".>

## Desired state

<The end state a user could observe, in their terms. Not the implementation. Give an
example of acceptable and unacceptable, since a boundary teaches faster than a rule.>

## Out of scope

<The neighbouring things this is not, each with one clause on why. This is what stops
the issue from sprawling in the comments, so do not skip it.>
````

Drop a section only when it would be empty. Never add one that is not on the list: no `Notes`, no `Background`, no `Proposed solution`, no `Acceptance criteria`.

Reference example, in a repo that uses this shape: [grafana/k6#6251](https://github.com/grafana/k6/issues/6251). Match its sections. Do not match its length, and do not match its density of internal detail; it runs long because it is a telemetry brief for maintainers, and most issues should be a third of it.

## Filing

Show the user the full body inline, formatted as it will appear, and wait for their go-ahead before touching `gh`. When they have already said to file, file and then show them what went up so they can edit it.

Always write the body to a file and pass `--body-file`:

```bash
gh issue create --repo <owner/repo> \
  --title '<title>' \
  --label bug --label 'area: foo' \
  --body-file /tmp/issue.md
```

Never `--body "..."` and never `--body "$(cat <<'EOF' ...)"`. Bodies carry backticks, and most command runners wrap the whole thing in `bash -c "..."`, so the outer double quotes expand your code spans before bash reaches the heredoc. Symptom: your backticked commands actually run and their output lands in the issue.

Single-quote the title. If it contains a single quote, write it to a file too.

### Titles

The symptom in the user's words, lowercase after the first word, no trailing period, no `[Bug]` prefix, no component prefix the labels already carry.

Say what happens, not what to do about it:

- `getRandomValues crashes k6 instead of throwing on bad input`
- `subtle.encrypt reads iv and other params after the call returns`
- `Record how users configure tests in the anonymous usage report`

Not `Fix getRandomValues`, not `getRandomValues is broken`, not `[webcrypto] Bug in getRandomValues()`.

### After filing

Hand the user the URL. If several issues came out of one investigation, list them as a small table and say plainly which findings you did **not** file and why: a duplicate you found, something unreachable in practice, something you could not reproduce on a release.
