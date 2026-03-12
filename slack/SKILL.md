---
name: slack
description: >
  Read, navigate, search, and send messages in Slack via the local desktop app.
  Use when the user mentions Slack, a *.slack.com URL, or a channel name.
  Provides scripts for checking unreads, searching messages, sending replies,
  adding emoji reactions, and viewing saved-for-later items.
compatibility: Requires agent-browser CLI and Slack desktop app running with --remote-debugging-port=9222
metadata:
  author: inancgumus
---

# Slack Desktop App Control

Connect to the running Slack desktop app via `agent-browser --cdp 9222`.

**Every command must include `--cdp 9222`** — without it, agent-browser launches its own browser.

The only way to access Slack is through `agent-browser --cdp 9222` connecting to the desktop app.

## Read messages

Snapshots only show interactive elements, not message text. Use eval to extract text:

```bash
agent-browser --cdp 9222 eval --stdin <<'EVALEOF'
(() => {
    const panel = document.querySelector('.p-flexpane') ||
                  document.querySelector('[data-qa="message_pane"]') ||
                  document.querySelector('.c-virtual_list__scroll_container');
    return panel ? panel.innerText : 'No message content found';
})()
EVALEOF
```

`.p-flexpane` is the thread side-panel. The other selectors are the main channel view.

## Interact

```bash
agent-browser --cdp 9222 snapshot -i          # see refs (@e1, @e2, ...)
agent-browser --cdp 9222 click @eN            # click (thread, channel, button)
sleep 1 && agent-browser --cdp 9222 snapshot -i  # always re-snapshot after clicks
```

## Search

```bash
agent-browser --cdp 9222 click @eN            # click Search button
agent-browser --cdp 9222 fill @eN "query" && agent-browser --cdp 9222 press Enter
sleep 2 && agent-browser --cdp 9222 snapshot -i
```

## Send a message

**Always confirm with the user before sending.**

```bash
agent-browser --cdp 9222 fill @eN "message text"
# Show the user what will be sent and wait for confirmation
agent-browser --cdp 9222 press Enter          # only after user approves
```

## Scroll

```bash
agent-browser --cdp 9222 scroll up 500        # older messages
agent-browser --cdp 9222 scroll down 500      # newer messages
```

## Scripts

### `scripts/unreads.py` — Fetch unread messages

A standalone Python script that connects to the Slack desktop app via CDP, navigates to the Unreads view, and extracts all unread messages. No pip dependencies — only requires `agent-browser` on PATH.

When the user asks to check unread Slack messages, run this script instead of doing it manually:

```bash
python3 <skill-path>/scripts/unreads.py              # pretty-print
python3 <skill-path>/scripts/unreads.py --json        # structured JSON
python3 <skill-path>/scripts/unreads.py --cdp 9333    # custom CDP port
```

### `scripts/search.py` — Search messages

Searches Slack and returns structured results with message IDs (`channel_id`, `message_ts`, `thread_ts`) so an agent can navigate to specific conversations. The workspace domain is auto-detected from the running Slack app.

```bash
python3 <skill-path>/scripts/search.py "query"               # pretty-print
python3 <skill-path>/scripts/search.py "query" --json         # JSON with message IDs
python3 <skill-path>/scripts/search.py "query" --limit 5      # cap results (default: 20)
python3 <skill-path>/scripts/search.py "query" --cdp 9333     # custom CDP port
```

### `scripts/reply.py` — Send a message

Navigates to a channel or DM using Slack's quick switcher (Cmd+K), fills the message box, and optionally sends. Uses the "Send now" button (not Enter) for reliable delivery.

**Always confirm with the user before passing `--send`.**

```bash
python3 <skill-path>/scripts/reply.py "Inanc Gumus" "hello"            # dry-run (fills, does not send)
python3 <skill-path>/scripts/reply.py "#ai-random" "hey" --send        # actually send
python3 <skill-path>/scripts/reply.py "inanctest" "test msg" --send    # channel or DM by name
```

### `scripts/emoji.py` — React to a message

Adds an emoji reaction to a message. If the emoji is already on the message, clicks the existing reaction button (toggles it) instead of adding a duplicate.

Accepts a message ID (from search.py output) or `--last` as a shortcut for the most recent message in a channel/DM.

```bash
python3 <skill-path>/scripts/emoji.py thumbsup C0587R32AM9/1772100390.731669   # by message ID
python3 <skill-path>/scripts/emoji.py ":fire:" --last inanctest                 # last msg in channel
python3 <skill-path>/scripts/emoji.py eyes --last "Inanc Gumus"                 # last msg in DM
```

### `scripts/later.py` — Fetch "Later" (saved) items

Lists messages saved for later, including their overdue/due status, channel, author, and message snippet. Supports the In progress, Archived, and Completed tabs.

```bash
python3 <skill-path>/scripts/later.py                           # all in-progress items
python3 <skill-path>/scripts/later.py --json                    # structured JSON
python3 <skill-path>/scripts/later.py --tab archived            # show archived items
python3 <skill-path>/scripts/later.py --tab completed           # show completed items
python3 <skill-path>/scripts/later.py --limit 10                # cap results (default: 50)
```
