# Plan

Turn what we agreed into a plan and tickets that each fit one fresh session. If a plan is already in *Decide first*, go there.

## Steps

### Gather what we agreed

Use the conversation, any saved design, and any linked ticket. Read `tickets.md`.

**Move on when** you can state the problem and goal.

### Check whether we can cut tickets yet

| Where we are | Do |
|---|---|
| A few decisions are open | Run `align`, then continue. |
| Too many, or they depend on answers we lack | Go to *Decide first*. |
| The way is clear | Continue. |

**Move on when** the developer agrees.

### Agree where to test

Skip this with no code. See `build/tests.md`.

**Move on when** the developer confirms.

### Write the plan

Describe behavior, not file paths.

```markdown
# <Feature>
## Problem
## Solution
## Behavior
Numbered, with edge cases.
## Decisions
Modules, interfaces, data changes, and why. Link demo branches.
## Testing
Entry points, tests to copy, tests to replace.
## Out of scope
```

**Move on when** every agreed behavior and decision is in it.

### Cut the work into tickets

Each ticket is one narrow path through every layer that you can demo alone, never one layer. Refactors that ease the work come first. Keep only dependencies that truly gate a ticket. Mark an owner *human* for judgment or access an agent lacks.

For a mechanical change everywhere, such as a rename: add the new form, move callers in batches, then delete the old form.

**Move on when** every behavior belongs to a ticket.

### Check the tickets with the developer

Show a table of title, waits for, what works afterward, owner, and finish. Ask about size, dependencies, and owners.

**Move on when** the developer approves.

### Write the tickets

Follow `tickets.md`, starting with those others wait for.

**Move on when** every approved ticket exists.

## Decide first

For work too foggy to cut up. This produces decisions, not code.

### Start the plan

Settle the goal with `align`, then ask broadly across the whole space. Save:

```markdown
# <Feature>
## Goal
## Decisions so far
One line each, linking the ticket that holds the detail.
## Not clear yet
Questions we cannot phrase precisely yet.
## Out of scope
```

Create a ticket for each decision you can phrase now, even if it must wait. Once approved, start subagents on research tickets, record their answers, and end the session.

**Move on when** the plan and tickets exist.

### Settle one decision per session

Pick up the next ticket, and settle it by what it needs:

| It needs | Use |
|---|---|
| A conversation | `align` |
| An outside fact | A background subagent. These can run alongside another ticket. |
| To see it work | `align/demos.md` |
| Manual work first | Do it, or see `situations.md` |

Write the answer on the ticket, close it here, and add a line to *Decisions so far*. Turn anything now clear into tickets. Fix or delete tickets the answer changed, and close any beyond the goal with a line under *Out of scope*.

**Move on when** no decision tickets are open and *Not clear yet* is empty. Then rerun `plan`, whose plan replaces this one.
