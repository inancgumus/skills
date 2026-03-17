---
name: slack
description: >
  Read, navigate, search, and send messages in Slack via the local desktop app.
  Use when the user mentions Slack, a *.slack.com URL, or a channel name.
compatibility: Requires agent-browser CLI and Slack desktop app (auto-launched with CDP if needed)
metadata:
  author: inancgumus
---

# Slack Desktop App Control

Connects to the Slack desktop app via CDP. If Slack isn't running with CDP enabled, it's automatically (re)launched. The workspace is auto-detected — no configuration needed.

All scripts share the same Slack desktop app, so run them sequentially from a single process. Use the scripts below instead of manual `agent-browser` commands. They handle navigation, state recovery, and parsing reliably.

## Reference formats

Every script that takes a message or channel accepts any of these:

| Format | Example | Resolves to |
|---|---|---|
| Channel ID | `C042WNMBYQM` | that channel |
| Channel name | `#k6-alert-core-team` | channel (sidebar lookup) |
| DM by name | `@Inanc Gumus` | that DM conversation |
| Message ref | `C042WNMBYQM/1773432901.662159` | specific message |
| Slack URL | `https://…/archives/C042…/p177…` | specific message |

Channel names must start with `#`, DM names with `@`.

Always pass hrefs as-is. Never strip or reconstruct them — query parameters are required for Slack to work.

---

### `scripts/unreads.py` — Fetch unread messages

```bash
python3 <skill-path>/scripts/unreads.py              # pretty-print
python3 <skill-path>/scripts/unreads.py --json        # structured JSON
python3 <skill-path>/scripts/unreads.py --channel NAME  # filter by channel
python3 <skill-path>/scripts/unreads.py --cdp 9333
```

### `scripts/search.py` — Search messages

Returns up to 20 results per page with `channel_id`, `message_id`, `thread_id`. Output includes `results` (total count) and `pages` (visible pages).

```bash
python3 <skill-path>/scripts/search.py "query"
python3 <skill-path>/scripts/search.py "in:#channel query" --json
```

**Pagination:** `--page N` fetches a specific result page. Repeated calls with the same query reuse the existing results. Slack loads pages dynamically — navigating to the last visible page may reveal more pages. Sometimes a more specific search term is better than paging. But when thoroughness matters, paging through results is important to collect more data.

```bash
python3 <skill-path>/scripts/search.py "query" --page 2
python3 <skill-path>/scripts/search.py "query" --page 3
```

Slack search syntax: `in:#channel`, `from:@user`, `after:YYYY-MM-DD`, `before:YYYY-MM-DD`, `has:reaction`, `has:file`

### `scripts/reply.py` — Send a message

Pass a channel/DM ref to post a new message, or a message ref to reply in its thread.

```bash
python3 <skill-path>/scripts/reply.py "#general" "hey" --send          # channel message
python3 <skill-path>/scripts/reply.py "@Inanc Gumus" "hello" --send    # DM
python3 <skill-path>/scripts/reply.py C042WNMBYQM/1773432901.662159 "reply" --send  # thread reply
```

Default is dry-run — add `--send` to actually send.

### `scripts/emoji.py` — React to a message

```bash
python3 <skill-path>/scripts/emoji.py C0123456789/1234567890.123456 thumbsup
python3 <skill-path>/scripts/emoji.py "https://…/archives/C…/p…" fire
```

### `scripts/get.py` — Get message content

```bash
python3 <skill-path>/scripts/get.py C0123456789/1234567890.123456
python3 <skill-path>/scripts/get.py "https://…/archives/C…/p…" --json
python3 <skill-path>/scripts/get.py C0123456789/111.1 C0123456789/222.2  # multiple
```

### `scripts/later.py` — Fetch "Later" (saved) items

```bash
python3 <skill-path>/scripts/later.py                           # all in-progress items
python3 <skill-path>/scripts/later.py --json
python3 <skill-path>/scripts/later.py --tab archived
python3 <skill-path>/scripts/later.py --tab completed
python3 <skill-path>/scripts/later.py --limit 10
```

### `scripts/collect.py` — Collect message IDs for a date

Navigates the channel directly (not search), so bot and integration messages are included.
Returns top-level messages only (not thread replies).

```bash
python3 <skill-path>/scripts/collect.py "#general" 2026-03-09
python3 <skill-path>/scripts/collect.py C042WNMBYQM 2026-03-09 --json
python3 <skill-path>/scripts/collect.py "#general" 2026-03-09 --replies --json
python3 <skill-path>/scripts/collect.py "#general" 2026-03-09 --limit 10
```

## Processing multiple messages

```bash
# Collect IDs then read each message:
python3 <skill-path>/scripts/collect.py "#channel" 2026-03-09 --json | \
  python3 -c "import json,sys,subprocess; [subprocess.run(['python3','get.py',m['message_id']]) for m in json.load(sys.stdin)]"

# Add emoji to a batch of messages:
for id in C042.../111 C042.../222; do
  python3 <skill-path>/scripts/emoji.py "$id" thumbsup
done
```

## Manual commands

For anything the scripts don't cover, use `agent-browser --cdp 9222` directly. Navigate within the app using DOM clicks — do not use `agent-browser open URL` as it disrupts the Electron app's state.

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
