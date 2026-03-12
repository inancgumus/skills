---
name: slack
description: >
  Read, navigate, search, and send messages in Slack via the local desktop app.
  Use when the user mentions Slack, a *.slack.com URL, or a channel name.
compatibility: Requires agent-browser CLI and Slack desktop app running with --remote-debugging-port=9222
metadata:
  author: inancgumus
---

# Slack Desktop App Control

Connects to the running Slack desktop app via `agent-browser --cdp 9222`. The workspace is auto-detected — no configuration needed.

Use the scripts below instead of manual `agent-browser` commands. They handle navigation, state recovery, and parsing reliably.

### `scripts/unreads.py` — Fetch unread messages

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

## Manual commands

For anything the scripts don't cover, use `agent-browser --cdp 9222` directly. Every command must include `--cdp 9222`.

```bash
agent-browser --cdp 9222 snapshot -i                              # list interactive elements (@e1, @e2, ...)
agent-browser --cdp 9222 click @eN                                # click a button, link, or tab
agent-browser --cdp 9222 hover @eN                                # hover to reveal toolbars
agent-browser --cdp 9222 fill @eN "text"                          # type into an input
agent-browser --cdp 9222 press Enter                              # press a key
agent-browser --cdp 9222 scroll up 500                            # scroll up (older messages)
agent-browser --cdp 9222 scroll down 500                          # scroll down (newer messages)
```

To read message text (snapshots only show interactive elements):

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
