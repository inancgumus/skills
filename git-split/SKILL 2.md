---
name: git-split
description: Split a big commit into smaller, atomic commits. Use when the user asks to split commits, break up a large commit, decompose changes into logical units, or create atomic commits from staged/unstaged changes.
---

# Git Split

Split a large commit (or set of uncommitted changes) into smaller, atomic commits that each pass lint, build, and tests independently.

## When to Use

Use this skill when the user asks to:
- Split a big commit into smaller ones
- Break up a large diff into atomic commits
- Decompose changes into logical units
- Create well-structured commit history from a batch of changes

Good real-life split example to follow:
`references/good-real-life-split-example.md`

## Workflow

### 1. Analyze the Changes

First, understand the full scope of changes to split:

```bash
# If splitting an existing commit (most recent):
git --no-pager diff --no-ext-diff HEAD~1 --stat
git --no-pager diff --no-ext-diff HEAD~1

# If splitting uncommitted changes:
git --no-pager diff --no-ext-diff --stat
git --no-pager diff --no-ext-diff
git --no-pager diff --no-ext-diff --cached --stat
git --no-pager diff --no-ext-diff --cached
```

Read any files that need more context to understand the dependency relationships between changes.

### 2. Plan the Split

Determine the commit order using these rules:

**Commit ordering (dependency-first):**
1. **Rename-only commits** — pure symbol/field/method renames, no behavior. Group ALL renames into a single commit. A rename commit must ONLY rename — no adding parameters, no changing method/function bodies, no other code changes.
2. **Code-move-only commits** — move code without changing behavior. Each code move should be a separate commit.
3. **Method extraction commits** — extract inner methods (e.g. calling `contentFrame(ctx, ..)` from `ContentFrame()`) in a single commit. Create the new internal method AND call it from the parent method in the same commit. Group all such extractions together.
4. **Helper addition commits** — one helper per commit when possible.
5. **Caller wiring commits** — one caller/path wired per commit.
6. **Behavior change commits** — one behavioral contract change per commit. Group closely related behavior changes that highlight a single fix (e.g. a new wrapper + its renamed inner method) in one commit to keep the fix visible.
7. **Tests last** — one distinct failure mode per test commit.
8. **Repeat and resplit** until every commit has one clear reason.

**Hard rules:**
- One commit = one primary reason to change, revert, and review.
- NO mixing of refactors, tests, new primitives/helpers, fixes, and behavior changes in the same commit.
- If a planned commit still has two reasons, split it again before coding.
- If a helper bundle has separable helpers, split into one helper per commit.
- If a new symbol is unused until a later commit but still lints cleanly, keep it separate. If it fails lint, merge it with the first consumer.
- Inner components before outer components.
- Provider changes before caller changes.
- Refactors separate from behavior changes.
- Tests last. One commit per distinct failure mode.
- Comments and style edits belong with the behavior commit they support.

### 3. Present the Plan

Before making any changes, present exact proposed commits as a numbered list. Show the commit title and body exactly as they will appear in `git log`. After each commit, add an indented explanation (NOT part of the commit message) describing what changes and how, so the user can understand the scope:

```
Planned commits (in order):
1. <title>

   <1-2 sentence rationale body draft>

   > What changes: <description of what files/methods/symbols change and how,
   > so the user can evaluate the split without reading the diff>

2. <title>

   <1-2 sentence rationale body draft>

   > What changes: <description of what files/methods/symbols change and how>
...
```

Wait for user approval before proceeding.

### 4. Execute the Split

If splitting an existing commit, first soft-reset it:

```bash
git reset --soft HEAD~1
git reset HEAD .
```

Then, for each planned commit:

```bash
# Stage only the files for this commit
git add <specific-files>
# For same-file splits, apply only the intended hunks non-interactively
# (e.g. via apply_patch/editing), then stage the full file.

# Verify before commit
gofmt -w <changed-go-files>
make lint

# Commit with a well-formed message
git commit -m "$(cat <<'EOF'
<title>

<body>
EOF
)"

# Verify after commit so every commit is independently clean
make lint
gofmt -w <changed-go-files>
```

### 5. Verify

After all commits are created:

```bash
# Confirm the final state matches the original
git log --oneline -<N>  # where N = number of new commits
git diff <original-ref>  # should be empty if splitting an existing commit
```

## Commit Message Format

- **Title**: max 50 chars. State intent, not mechanism. Imperative verb phrase. No file references or implementation details.
- Respect any user-required prefix/style (for example: `browser: <verb> ...`).
- **Body**: 1-3 lines, max 72 chars each. Explain rationale only. No file references or implementation details.
- Do not prefix lines with labels like `Why:`. Write natural prose.
- No bullets, lists, markdown, change lists, or AI attribution.
- NEVER add a change list or AI attribution in the commit message.

### Examples

Good:
```
storage: finish writes before shutdown

Completing in-flight writes prevents data loss when the
process receives a termination signal during active I/O.
```

Bad:
```
storage: add waitgroup for shutdown

- Added sync.WaitGroup to storage.go
- Modified Close() to call wg.Wait()

Co-Authored-By: ...
```

## Done Criteria

- Each commit passes repo lint/format/build checks on its own.
- Each commit is atomic and self-contained, with no mixing of refactors, tests, new primitives/helpers, fixes, and behavior changes.
- Commit titles and bodies match user-specified style constraints.
- The final working tree EXACTLY matches the original state before splitting.

## Important Notes

- Always ask for user approval of the split plan before executing.
- Avoid interactive git flows for splitting (`git add -p`, interactive rebase).
  Prefer non-interactive staging and explicit file edits per commit.
- If branch creation/switching fails because it's checked out in a worktree,
  inspect `git worktree list` and resolve that before continuing.
- If a commit would fail lint due to unused symbols, merge it with the first consumer commit.
- Use `git stash` to temporarily save unrelated changes if needed.
