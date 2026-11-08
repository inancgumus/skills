---
name: dev
description: Step-by-step guide through software work in any language. Use for /dev, questioning an idea or request (align), shaping or improving code structure (design), splitting big work into tickets (plan), test-first building (build), debugging something broken, flaky, or slow (hunt), checking your own diff (review), or finishing work (ship). For someone else's PR, use git-pr-review.
---

# dev

The developer decides. You find the facts and always say what comes next.

```text
idea or request ─► align ─► design ─► plan ─► build ─► review ─► ship
bug or report ───► hunt ────────────────────────────┘
code that hurts ─► design ─► ...
```

With no request, show this route and recommend a workflow. Small work skips workflows, so say what you skip.

## Workflows

Each workflow is a file holding its steps. Its folder, if it has one, holds the reference material those steps use.

| Workflow | Use when | Then suggest |
|---|---|---|
| `align.md` | An idea is fuzzy, someone made a request, or a plan needs questioning | `design` if the code's shape is unclear, `plan` if it needs several sessions, `build` if it fits one, `ship` if the decision is the whole result |
| `design.md` | New code needs a shape, or existing code hurts to change | `plan` if it needs several sessions, `build` if it fits one |
| `plan.md` | The work is too big for one session, or too foggy to cut up | `build` on the first ready ticket |
| `build.md` | We know what to build | `review` |
| `hunt.md` | Something is broken, flaky, or slow, or someone reported it | `review` |
| `review.md` | A diff is ready for a check | `ship` |
| `ship.md` | The review passed, or a ticket with no code has its answer | `build` on the next ready ticket |

`tickets.md` is what a ticket is in this project, and how to write, pick up, or move one. `situations.md` is how to handle a lost developer, a human-only step, a merge conflict, work that must wait, and the end of a workflow.

Steps are the `###` headings under `## Steps`. Show progress, such as *Step 2 of 5: Confirm and shrink*. Finish a step only when its *Move on when* holds.

## Rules

- Look up facts yourself. Ask the developer only for decisions, with your recommendation, so that "yes" accepts it.
- Back claims with a file and line, or a command and its output, including the developer's claims.
- Ask before anything others can see or that is hard to undo.
- Start subagents fresh, with a narrow brief and without your conclusion.
- Write `<REDACTED>` in place of secrets.
- Use an installed skill when it owns a step, such as `git-pr` or `git-split`.
- Use the `write` skill for all text people read: tickets, commit messages, PR bodies, replies, and docs.
