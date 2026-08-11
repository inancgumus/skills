---
name: claude-sessions
description: List recent Claude Code sessions (name, last message date, working directory, last prompt) and resume any of them in new iTerm tabs. Use this whenever the user asks about their past or recent Claude sessions, wants to see or page through their session history, asks what they were working on in another session, or wants to reopen, resume, or "bring up" one session or the last N sessions — in a new tab or a new window — even if they never say the word "session".
---

# Claude sessions

The bundled script reads the local session transcripts, so it works without any
network calls. Run it from this skill's directory:

```bash
scripts/cc-sessions list          # 10 most recent sessions
scripts/cc-sessions open 1 2 3    # resume those three, one new iTerm tab each
```

## Listing

```bash
scripts/cc-sessions list -n 5                 # 5 most recent
scripts/cc-sessions list -n 5 --offset 5      # next page
scripts/cc-sessions list --all                # everything
scripts/cc-sessions list --cwd ~/grafana/k6   # only sessions started under a path
scripts/cc-sessions list --exclude vivid-cobra --exclude rapid-badger
scripts/cc-sessions list --skip-live          # hide sessions already open in a tab
scripts/cc-sessions list --json               # same data, machine-readable
```

Columns: index, session name, last message date (local time), state, working
directory, session id, last prompt typed. The session running the command is
dropped from the list; add `--include-current` to keep it.

Report the output as a markdown table, keeping the index numbers, because the
user selects sessions by index. Keep the session name and the last message date
in the table: those are how the user recognizes a session. When there are more
pages, say so and offer the next page instead of dumping everything.

A `~` after the date means the session has no message timestamps and the date
comes from the file's modification time. An empty state column means the session
is not running; anything else (`idle`, `busy`, `shell`, ...) is the live status
Claude Code reports for a session that is open in some tab right now.

`--pager` pipes the output through `$PAGER` (default `less -SRFX`). That only
helps a human at a terminal, so use `--offset` for paging instead.

## Resuming

```bash
scripts/cc-sessions open 2                       # one session, new tab
scripts/cc-sessions open 1-3 7                   # ranges and single indexes mix
scripts/cc-sessions open golden-orca             # by name
scripts/cc-sessions open 10951267                # by session id or id prefix
scripts/cc-sessions open -n 5 --skip-live        # the 5 most recent not already open
scripts/cc-sessions open 1 2 --window            # one new window, a tab per session
scripts/cc-sessions open 1 --dry-run             # print the commands, open nothing
```

Each tab runs `cd <the session's working directory> && claude --resume <id>`.

Indexes come from the same ordering `list` produces, and that ordering shifts
whenever a session receives a new message. If minutes passed since the last
`list`, or if the user's request needs to be exact, pass session ids instead of
indexes.

`open` refuses to resume a session that is already running in another tab, since
two live copies of one session write to the same transcript. Tell the user the
session is already open rather than passing `--force`, unless they ask for it.

## Where the data comes from

Both commands read `~/.claude/projects/<project>/<session-id>.jsonl`, the
transcript Claude Code appends to. Session names come from the `custom-title`
records inside it, so a session that never got a name shows `-`. Sessions
running right now are matched against `~/.claude/sessions/*.json`, which holds
one file per live process; the script checks the recorded pid is still alive, so
stale files do not show up as live.

Subagent transcripts live in subdirectories and are never listed as sessions.

## Requirements

macOS with iTerm2 (tabs are created through AppleScript) and python3.
