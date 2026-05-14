---
name: git-split
description: Split a big commit into smaller, atomic commits. Use when the user asks to split commits, break up a large commit, decompose changes into logical units, or create atomic commits from staged/unstaged changes.
---

# Git Split

Construct a clean, reviewable history from a large diff.

The goal is not to carve one final diff into smaller pieces. The goal is to build a sequence of
commits where each commit is a coherent, green historical state.

## When to Use

Use this skill when the user asks to:
- Split a big commit into smaller ones
- Break up a large diff into atomic commits
- Decompose changes into logical units
- Create well-structured commit history from a batch of changes

Good real-life split example to follow:
`references/good-real-life-split-example.md`

## Core Standard

- Historical coherence beats diff neatness.
- One commit = one primary reason to change, review, and revert.
- Every commit must make sense to a reviewer who only sees that commit and its parent.
- Keep each commit as close to its parent as possible outside the behavior being changed. Do not
  rename stable symbols, rewrite comments, reformat code, reorder nearby code, or move helpers
  around unless that change is required for the commit's actual purpose.
- User-provided constraints override the skill's generic defaults. Turn them into explicit active
  rewrite rules and keep applying them for the rest of the split.
- Every commit must pass the repo's formatter, linter, and relevant tests on its own.
- Tests and wiring belong with the behavior they validate. Do not push tests to the end by default.
- Shared helpers and test scaffolding are part of the feature boundary. Do not introduce future-only
  seams early just because they are convenient.
- Avoid convenience cleanup. If a change does not help the current commit's behavior, proof, or
  mechanical extraction, leave it out.
- If a commit removes or modifies existing code, behavior, or functionality, the rationale must
  explain why that change is correct and what replaces it, if anything.
- If a commit only works because of a later commit, the split is wrong.

## Workflow

### 1. Normalize the Starting Point

First, identify exactly what is being split:
- Uncommitted changes
- Staged changes
- The most recent commit
- A short range of recent commits that will be rebuilt

Inspect the current state:

```bash
# Current state
git status --short --branch
git log --oneline --decorate -10

# If splitting the most recent commit
git --no-pager diff --no-ext-diff HEAD~1 --stat
git --no-pager diff --no-ext-diff HEAD~1

# If splitting uncommitted changes
git --no-pager diff --no-ext-diff --stat
git --no-pager diff --no-ext-diff
git --no-pager diff --no-ext-diff --cached --stat
git --no-pager diff --no-ext-diff --cached
```

Then answer these questions before planning:
- What is the green parent or base state?
- Does that base already pass the repo's normal gate?
- Are there unrelated local changes that must be isolated first?
- Which files are touched by multiple future commits?
- Which names, comments, layout choices, and helper locations from the parent should remain intact
  unless a commit truly needs to change them?
- What user instructions from this conversation must persist across all later commits?

If the base state does not pass lint or tests, fix that first or explicitly fold that fix into the
base before splitting. Do not build a split on top of a known-broken base unless the user explicitly
accepts that.

### 2. Back Up Before Any Rewrite

If the split will use `reset`, `rebase`, `cherry-pick`, or any other history rewrite, create a
backup first.

Minimum backup:

```bash
stamp=$(date +%Y%m%d-%H%M%S)
git branch "backup/<topic>-$stamp" HEAD
```

Recommended backup for risky or lengthy rewrites:

```bash
mkdir -p "/tmp/git-split-$stamp"
git status --short --branch > "/tmp/git-split-$stamp/status.txt"
git log --oneline --decorate -20 > "/tmp/git-split-$stamp/log.txt"
git diff --no-ext-diff > "/tmp/git-split-$stamp/working.patch"
git diff --no-ext-diff --cached > "/tmp/git-split-$stamp/index.patch"
git format-patch --stdout <base>..HEAD > "/tmp/git-split-$stamp/series.patch"
git bundle create "/tmp/git-split-$stamp/repo.bundle" <base>..HEAD
```

Do not start rewriting until the backup exists.

### 3. Analyze the Full End State

Read the touched files and map the real dependency graph, not just the file list.

For each candidate commit, answer:
- What new behavior starts here?
- What must still stay old here?
- What existing behavior disappears or changes here, if any?
- Why is that removal or modification correct?
- Which tests must change here?
- Which helper or test-helper changes are only needed by later commits and must stay out?
- Which surrounding code should stay textually close to the parent to avoid review noise?
- If old and new implementations temporarily coexist, where is that boundary and how will the
  commit make that handoff obvious without adding fake seams?
- Which previously corrected patterns are now banned for the rest of the rewrite unless there is a
  new, explicit justification?

Important:
- A helper is not "free plumbing". If it exists only to support a later feature, it belongs later.
- A test helper change can bundle features just as easily as production code can.
- Same-file splits are the hardest case. You must think in terms of explicit intermediate file
  versions, not hunks.
- New files are not free either. Do not create a separate file for a tiny helper unless that file is
  clearly justified by the codebase structure, not just by the split.

### 4. Plan the Split

Prefer dependency-first order, but only when each commit is still historically coherent.

Good ordering rules:
1. Pure mechanical commits first, but only if they are genuinely behavior-free and green on their
   own.
2. Add a helper only when it is first required, unless it is a pure extraction that is already green
   and reviewable alone.
3. Wire one caller, path, or feature at a time.
4. Change one behavior contract at a time.
5. Keep the tests that prove a behavior in the same commit as that behavior.

Hard rules:
- No commit may contain two independent reasons to exist.
- Do not mix a pure refactor with a behavior change in the same commit.
- Do not mix one feature's tests with another feature's code.
- Do not create "future scaffolding" commits.
- If a symbol would be dead or unused until a later commit, merge it into the first consumer unless
  it is a pure mechanical extraction that still leaves the tree green.
- Comments, renames, and style edits belong with the commit whose behavior they clarify.
- Do not introduce awkward scope blocks, shadowed variables, temporary aliases, or other
  split-only hacks just to keep commits small. Prefer straightforward code that a maintainer would
  actually write.
- If a commit migrates only part of a path from old to new code, the plan must explicitly name what
  still stays old and why that temporary split is acceptable.

The old default "tests last" is wrong for most real splits. Tests usually belong in the same commit
as the behavior they validate.

Before presenting the plan, write down an active constraint checklist from the user's feedback.
Keep it short and explicit. Example categories:
- naming and comment preservation
- formatting and code-shape preservation
- banned shortcuts or temporary hacks
- boundaries for old/new coexistence
- commit-message style requirements

Treat that checklist as part of the task, not as optional advice.

### 5. Present the Plan

Before making changes, present exact proposed commits as a numbered list. Show the commit title and
body exactly as they will appear in `git log`.

After each commit message, include four short planning notes that are not part of the commit
message:
- `What changes:`
- `Must still stay old here:`
- `Why removal/change is correct:` if the commit removes or modifies existing behavior
- `Verification:`

Use this format:

```text
Planned commits (in order):
1. <title>

   <body line 1>
   <body line 2>

   What changes: <precise description of files, symbols, and paths changed>
   Must still stay old here: <what later behavior must NOT appear yet>
   Why removal/change is correct: <only if this commit removes or modifies existing behavior>
   Verification: <formatter/lint/test commands for this commit>

2. <title>

   <body line 1>
   <body line 2>

   What changes: ...
   Must still stay old here: ...
   Why removal/change is correct: ...
   Verification: ...
```

Wait for user approval before rewriting history.

### 6. Execute the Split

Prefer building the split forward from a green base.

If splitting the most recent commit, a common starting point is:

```bash
git reset --soft HEAD~1
git reset HEAD .
```

Then, for each planned commit:
1. Make only that commit's intended state exist in the working tree.
2. Keep later features out, even if that means temporarily removing already-written code.
3. Stage only that commit's files.
4. Format touched files.
5. Run the repo's gate immediately before committing.
6. Commit with the exact planned message.

Typical sequence:

```bash
# Edit files so the working tree matches exactly this commit's intended state
git add <specific-files>

# Format
gofmt -w <changed-go-files>

# Run the repo-specific gate for this commit
make lint
go test ./...

# Commit only after the gate passes
git commit -m "$(cat <<'EOF'
<title>

<body>
EOF
)"
```

Execution notes:
- Avoid interactive git flows such as `git add -p` and interactive rebase unless the user explicitly
  asks for them.
- Prefer explicit file edits and full-file staging.
- If multiple commits touch the same file, construct the exact intermediate version of that file for
  each commit.
- Preserve surrounding parent code unless the commit needs to change it. Favor surgical edits over
  broad reshaping.
- Do not assume later hunks are harmless.
- If unrelated local changes exist, isolate them first with a backup, stash, or worktree.
- If a commit temporarily keeps part of an old implementation alive beside a new one, localize that
  handoff and consider leaving a short code comment at the boundary so later replay work removes the
  right thing.
- Re-check the active constraint checklist before every commit and every amend. A correction made in
  one commit is not local; it usually becomes a rule for the rest of the rewrite.
- If the user rejects a pattern once, assume that pattern is banned for the remainder of the split
  unless you explicitly justify reintroducing it and get agreement.

### 7. Audit the Final History

After all commits are created, do not stop at "the tip is green".

Final audit:
1. Confirm the final tree matches the intended end state.
2. Inspect each commit's diff and verify it has one clear reason to exist.
3. Replay the gate on every final commit SHA, not just `HEAD`.
4. Inspect each commit for review noise: unnecessary renames, comment churn, formatting churn,
   helper moves, tiny extra files, or split-only code hacks.
5. Check the final history against the active constraint checklist, not just against the skill's
   generic rules.

Useful checks:

```bash
git log --oneline -<N>
git diff <expected-final-ref>
```

Commit-by-commit audit loop:

```bash
orig_branch=$(git branch --show-current)
commits=(<oldest-newest-final-shas>)

for c in "${commits[@]}"; do
  git switch --detach "$c"
  make lint
  go test ./...
done

git switch "$orig_branch"
```

If any commit fails the audit, rewrite the history again. Do not paper over the problem with an
extra fixup commit unless the user explicitly wants that.

## Commit Message Format

- **Title**: max 50 chars. State intent, not mechanism. Imperative verb phrase. No file references
  or implementation details.
- Respect any user-required prefix or style.
- **Body**: 1-3 lines, max 72 chars each. Explain rationale only. No file references or
  implementation details.
- If the commit removes or changes existing code, behavior, or functionality, the body must explain
  why that removal or modification is correct. If something replaces the old path, say so.
- No bullets, markdown, change lists, or AI attribution in commit messages.

### Examples

Good:

```text
storage: finish writes before shutdown

Completing in-flight writes prevents data loss when the
process receives a termination signal during active I/O.
```

Bad:

```text
storage: add waitgroup for shutdown

- Added sync.WaitGroup to storage.go
- Modified Close() to call wg.Wait()

Co-Authored-By: ...
```

## Done Criteria

- A backup exists for any rewritten history.
- The base state used for the split is green or has been explicitly normalized first.
- Each commit is atomic, self-contained, and historically coherent.
- Tests and wiring are included in the same commit as the behavior they validate unless the commit
  is a pure mechanical refactor.
- Any commit that removes or modifies existing behavior explains why that change is correct.
- The repo formatter, linter, and relevant tests pass on every final commit.
- The final working tree exactly matches the intended end state.

## Important Notes

- Always ask for user approval of the split plan before executing.
- If history rewrite permission is unclear, ask before using `reset`, `rebase`, or destructive
  branch moves.
- If branch creation or switching fails because the branch is in a worktree, inspect
  `git worktree list` and resolve that first.
- Prefer keeping one good backup branch until the user explicitly asks to remove it.
- A split is finished only after the final commit-by-commit audit passes.
