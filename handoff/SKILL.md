---
name: handoff
description: >
  Session handoff tool. Writes or loads a HANDOFF.md file to preserve and
  restore session state across agent sessions.
---

## How a new agent session works

A new agent session starts with nothing. The goal, the approach, what was tried, what failed, what the user asked for — all gone. The only way any of it survives is if you write it down here.

---

## /handoff — write

Steps:
1. `git status`. Uncommitted changes? Ask to commit or note as WIP.
2. Read back through the full conversation history before writing anything. Every message, tool call, result, correction. Don't filter on what you think the next agent will need. It can't ask you. If it's not written down, it's gone.
3. Write `HANDOFF.md` to the current directory.
4. Give the user the Resume Prompt, exact text, ready to paste.

### HANDOFF.md format

The agent reading this should know everything you know right now. If you couldn't continue the work from this document cold, it needs more.

```markdown
---
created: <ISO 8601 timestamp>
---

## Goal
<What we're trying to accomplish and why. Include the motivation, not just the task.>

## Context
<Everything the next agent needs to know: domain knowledge surfaced during the session,
constraints, background, what was researched and found, how things fit together.>

## Progress
<What was completed, chronological, with enough detail that the next agent knows exactly what state things are in.>

## Decisions
<Every non-obvious decision made and why. Include alternatives that were considered and rejected.>

## Pitfalls
<What didn't work, dead ends, gotchas. Be specific so the next agent doesn't repeat them.>

## Assumptions
<Things taken as true without verification. Treat these as risks, not facts.>

## Open Questions
<Things noticed but not investigated, hypotheses not yet tested, signals that felt important but weren't pursued.
The next agent should know these exist and decide whether to chase them.>

## Ruled Out
<Approaches explicitly decided against and why. Prevents the next agent from re-proposing them.>

## Environment
<CWD, running processes and ports, active virtualenv/shell, key env vars discovered during the session.
Anything the next agent needs to orient itself practically.>

## User Preferences
<Behavioral preferences the user expressed: communication style, formatting, what to avoid, tone, level of detail,
anything the user corrected or asked to do differently. The next agent must honor these from the start.>

## Skills Used
<Skills invoked during this session, one per line. The next agent must load these before starting work.
Format: `skill-name` — why it was relevant>

## Tool Activity
<Every tool call made during the session, one per line, from your perspective: what you did and what you found.
Meaningful takeaway, not verbatim output. Include reads, writes, edits, bash commands, web fetches, searches, agent spawns.
Format: [tool] `target` — what was learned or done>

## Next Steps
<Ordered list. First item = immediate next action, specific enough to just do it.>

## Resume Prompt
> Continue [task]. [2-3 sentences of context]. Run `/handoff continue` to load full state. Start by [first concrete action].
```

Always write a fresh `HANDOFF.md`. If one exists, overwrite it.

---

## /handoff continue — resume

1. Read `HANDOFF.md`.
2. Load every skill listed under **Skills Used** before anything else.
3. Re-read every file listed under **Tool Activity** that was a Read or Write, to restore the file context the previous agent had.
4. Delete `HANDOFF.md`.
5. Tell the user: "Resuming from [date]. Next step: [first item in Next Steps]. Shall I start?"
6. Wait for confirmation.
