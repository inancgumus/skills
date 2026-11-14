# Tickets

A ticket is one tracked piece of work. The developer decides what it is: a local file, a file in the repo, an issue, a PR, or anything else. They can change that at any time, and work can stay fully local.

## Find what a ticket is here

Read `.notebook/dev.md`. If it is missing, ask the developer, recommending local files, and save their answer in plain lines. Add `.notebook/` to `.git/info/exclude`. Plans and designs go in `.notebook/<feature>/` unless the note says otherwise.

```markdown
Tickets: local files in .notebook/<feature>/
Finish: local commit
```

## Write a ticket

For a ticket in a file, use this format. Anywhere else, use that place's own form, such as the `git-issue` skill for GitHub issues or `git-pr` for PRs, and keep what it has no room for in `.notebook/`.

```markdown
# NN: <Title>

**Build:** The behavior this makes work, or the question it answers.
**Waits for:** Other tickets, or none.
**Status:** open, taken, waiting, or done
**Owner:** agent, or human
**Finish:** Only if it differs from the project's.

- [ ] A checkable criterion

**Out of scope:** Nearby work to leave alone.
```

Describe behavior and interfaces, not file paths, which go stale. For someone else's report, add current and wanted behavior. Refer to tickets by title.

## Pick up a ticket

A ticket is ready when it is open and everything it waits for is done. Mark it *taken* before any work.

## See what needs attention

Show, oldest first: new reports and outside PRs with no reply from us, *waiting* tickets whose answer has arrived, and ready tickets by owner. A bug goes to `hunt`. A request or outside PR goes to `align`, then `git-pr-review` if we want the PR.

## Change what a ticket is

Update the note. To move tickets, ask first. Move the plan and every ticket not done, then fix links once all have ids, and link old to new.
