---
name: git-commit
description: Write commit messages, create commits, and rewrite Git history safely. Use before drafting any commit message, running git commit, creating fixup commits, rebasing, squashing, amending, cherry-picking, or otherwise changing commit history.
---

# Git Commit

Read the repository instructions, status, diff, and recent commit history before changing Git state. Preserve unrelated work and use the repository's existing message style.

Create commits only when the user asks. Use the configured Git author without overrides.

## Commit boundaries

- Give each commit one independently useful behavior and one reason to review or revert it.
- Keep each commit understandable without knowledge of neighboring commits.
- Exclude cleanup, renames, comments, helpers, and tests that do not serve that commit.
- Follow explicit test-placement requirements. Otherwise, keep a test with the behavior it protects.
- Keep every commit buildable and passing its relevant tests and linters.

Use the `git-split` skill as well when splitting or rebuilding a series of commits.

## Commit messages

- Start the title with a concise imperative verb that states the benefit.
- Keep the title within 50 characters.
- Wrap each body line at 72 characters.
- Explain the reason in the body when the title cannot carry it.
- Describe the previous behavior and what improved without listing changed files.
- Do not mention neighboring commits, verification activity, or implementation trivia.
- Do not add AI attribution.

## Creating commits

- Stage explicit files and inspect the staged diff before committing.
- Never use interactive Git operations. Set `GIT_SEQUENCE_EDITOR=true` and `GIT_EDITOR=true` for commands that would open an editor.
- Run the relevant formatter, tests, and linter before committing.
- Inspect the resulting commit and working tree after committing.

## Rewriting history

- Confirm the exact commit range and create a backup branch before rewriting it.
- Prefer `fixup!` commits followed by one non-interactive autosquash rebase.
- Do not use rerere or amend while resolving a rebase.
- Do not rewrite shared history or force-push unless the user explicitly authorizes it and repository rules allow it.
