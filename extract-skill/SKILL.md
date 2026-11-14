---
name: extract-skill
description: Mine past agent session logs (Claude Code, Codex, opencode, pi) to find how agents really used a tool or workflow, then write a skill that makes a fresh agent succeed the first time. Use when the user wants to turn past sessions or logs into a skill, asks what agents keep getting wrong with a tool, or says "extract a skill".
---

# Extract a skill from agent logs

Past sessions show what a fresh agent can't know: the commands that work, the errors that waste time, and the corrections the user had to make. Mine them, verify what you find, and write a skill that gives a clean-slate agent only that.

## 0. Ask first

Before reading any log, run `scripts/mine.py agents`. It lists the agents that have logs on this machine, with session counts. Then ask the user which agents to read (multi-select, one option per agent with sessions) and what topic to extract (a tool, command, or workflow). Don't read logs from agents the user didn't pick. If an agent shows 0 sessions, say so and leave it out. If you can't ask (a headless run), say which agents and topic you assumed, and go on.

## 1. Find the evidence

`scripts/mine.py` reads the chosen agents' logs. TOPIC is a regex, for example `'vmctl|ghostvm'`. Pass `--agent <name>` once per chosen agent. Pass `--skip <session-id>` for the current session, so you don't mine your own work.

```sh
mine() { python3 <this skill's dir>/scripts/mine.py "$@"; }   # a function works in bash and zsh
mine sessions 'TOPIC' --agent claude --agent codex   # which sessions touched it
mine calls    'TOPIC' --agent claude                 # most repeated commands
mine fails    'TOPIC' --agent claude                 # failures, grouped by error
mine talk     'TOPIC' --agent claude                 # user corrections, agent notes, saved memory notes, prompt history
mine show     SESSION_ID --agent claude > /tmp/s.txt # one session as a compact conversation
```

Repeat `--agent` for each agent. Don't put the flags in a variable, because zsh won't split it. `--skip` and `show` match the start of a session id. Redirect `show` to a file and read it in pieces, because long output gets truncated. `sessions` lists subagent runs and `history` too. Pass `--skip agent-` to leave out subagent runs, or `--skip history` to leave out prompt history.

Read the output this way:

| Output | What it tells you |
|---|---|
| `calls`: the same `--help`, `which`, or `ls` many times | A fresh agent wastes calls discovering this. Put the answer in the skill. |
| `calls`: many near-identical long pipelines | Agents rebuild the same helper. Bundle it as `scripts/` and test it. |
| `fails`: an error across several sessions | A specific symptom needs its own fix in the skill. |
| `talk`: the user saying "don't", "why did you", "I told you" | A hard rule. Put it first. |

Then run `show` on the few sessions with the most failures to learn the cause and the fix. The tool output alone is not enough. `talk` also reads saved memory notes and prompt history. Rules the user gave and facts agents saved often live there, not in a transcript: search them for each symptom you found (a black screen, no network, a stuck dialog). Codex shell calls appear wrapped in JavaScript, so match on the command text inside.

## 2. Verify before you write

Run every command and fix you plan to include against the real tool, if it is available. A fix that appears in a note or another session counts as evidence, but run it too. Drop what you can't confirm, or label it *unconfirmed*. A log shows what an agent did, not that it was right.

## 3. Write the skill

Write it for an agent that has never seen the tool.

* Give instructions, not history. Never write "agents spent time on X". Write what to do.
* Assume setup is done and the tool is running. Run the task, and diagnose only when a call fails.
* Put the user's hard rules in one *Never* list at the top.
* Order sections by the workflow: run, move files, do the task, fix failures.
* Give each failure its own heading with the exact error text and its fix. A catch-all table lets agents skip the one that matters.
* Name the cheapest correct path: the right flag, the compact output, the one-line check. Save the agent's tokens.
* Bundle a script when agents kept writing the same code. Run it on a real task, and check that it returns small output and finishes well inside the tool timeout.
* Keep one-time human setup in its own short section, and tell agents not to redo or verify it.
* Keep only what holds for any user of the tool. Replace names, paths, machine names, default values, and project names with `<VM>`-style placeholders. A rule that belongs to one project (for example, how that project names its app) stays out.
* Keep the description to one line: what it does and when to use it.

## 4. Check the result

Compare the skill against your findings. Every repeated failure, user rule, and wasted call must appear, or be dropped on purpose. Then test the skill on a fresh agent with a real task, and fix what it gets wrong.
