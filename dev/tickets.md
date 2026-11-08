# Tickets

A ticket is one tracked piece of work. It can be a local note, a file in the repo, an issue, a PR, or anything else, and that can change at any time.

## Find what a ticket is here

Read `.notebook/dev.md`. If it is missing, recommend an answer from the repo, ask, and save it. Add `.notebook/` to `.git/info/exclude`. Plans and designs go where tickets live.

```markdown
Ticket: a draft PR per behavior, with the ticket format as its body. Start it with an empty commit.
Waits for: stack the PR on the one it waits for
Plans: docs/plans/
Done: the PR merges
Finish: merge that PR
```

## Write a ticket

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
