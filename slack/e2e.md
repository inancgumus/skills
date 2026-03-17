# Manual E2E Test Plan

Validates all slack skill script functionality. An agent runs these tests sequentially (Slack can only handle one interaction at a time). The agent creates an ephemeral checklist from these sections and checks items off as it goes.

All commands run from `slack/scripts/`.

## Hard rules

1. **No skipping.** Every test in every section MUST be executed. If a test is blocked by a bug, report the bug, fix it, and retest — do not skip or mark as "blocked".
2. **Fix bugs immediately.** When a test fails, diagnose the root cause, fix the code, and rerun the failing test until it passes. Repeat until all tests pass. No shortcuts.
3. **Both output modes.** Every script that supports `--json` must be tested in **both modes** — JSON first, then text. Verify text output contains the same data as JSON in a human-readable format.

## Setup

1. Check if Slack is already reachable: `agent-browser --cdp 9222 snapshot -i | head -5`
2. If not, launch with CDP: `open -a Slack --args --remote-debugging-port=9222`
3. Test channel: `#inanctest`

## Discovery

Before running tests, the agent discovers real values by running:

1. `python3 collect.py "#inanctest" DATE --json` with a recent date that has messages — find a date that works
2. From the results, pick two message refs for use in later tests
3. `python3 get.py REF --with-replies --json` on a few refs to find one that has thread replies
4. `python3 unreads.py --names-only --json` to find channels with unreads
5. `python3 later.py --json --limit 1` to check if saved items exist

All subsequent tests use the discovered refs, dates, and channel names — nothing is hardcoded.

---

## 1. Help output

Run `--help` for each script. Verify each shows usage and all documented flags:

- `search.py` — `--json`, `--page`, `--click`, `--cdp`
- `get.py` — `--json`, `--with-replies`, `--cdp`
- `collect.py` — `--json`, `--with-replies`, `--limit`, `--cdp`
- `later.py` — `--json`, `--tab`, `--limit`, `--ids`, `--cdp`
- `reply.py` — `--send`, `--cdp`
- `emoji.py` — `--cdp`
- `unreads.py` — `--json`, `--channel`, `--names-only`, `--cdp`

## 2. Channel navigation

Test that `#inanctest`, `inanctest` (bare), and the discovered channel ID all resolve to the same channel:

- `collect.py "#inanctest" DATE --json` — returns messages
- `collect.py "inanctest" DATE --json` — same result (bare name normalized)
- `collect.py CHANNEL_ID DATE --json` — same result (ID format)

## 3. Search

Run each in both JSON and text mode:

- Basic search: returns `messages[]`, `results`, `pages`. Text mode shows numbered list with user, time, preview.
- Pagination: if `pages > 1`, fetch `--page 2` and verify different messages. Keep paging to collect results across multiple pages.
- Click result: `--click 1` — returns `{clicked, href, thread[]}` with full untruncated messages
- Query reuse: repeat the same search, verify it reuses results (fast, no re-search)
- Scoped search: `"in:#inanctest QUERY"` — results only from that channel
- Date-range search: `"after:DATE before:DATE QUERY"`
- No results: nonsense query — `{results: 0, pages: 0, messages: []}`. Text mode says "No results found."
- Out of range click: `--click 999` — error

## 4. Get message

Run each in both JSON and text mode:

- Single message: returns `{channel_id, channel, message_id, date, user, message, reactions}`. Text mode shows user, time, text, reactions.
- With replies: `--with-replies` on a threaded message — `replies[]` present. Text mode shows reply count and each reply. Verify all replies are captured (not just the first few visible ones).
- Batch: two refs — returns array of two records. Text mode shows both.
- Not found: fake timestamp — `{error: "not found"}`
- Channel-only ref: error about needing a specific message

## 5. Collect messages by date

Run each in both JSON and text mode:

- Basic: returns `[{message_id}]` for a date with messages. Text mode lists refs.
- With replies: `--with-replies` — each entry has `reply_ids[]`. Text mode shows indented reply refs.
- Limit: `--limit 3` — at most 3 results
- Thorough scroll test: pick a date with many messages (10+). Run without `--limit` and verify all messages for that day are collected, not just the first screenful.
- Empty date: pick a date with no messages — returns `[]`

## 6. Reply / Send

- Dry-run (no `--send`): prints `{status: "dry-run"}`, nothing sent in Slack
- Channel message: `--send` to `#inanctest` — message appears in channel
- Thread reply: `--send` to a message ref — reply appears in thread
- DM: `--send` to `@CONTACT` — DM sent (pick a safe contact)

## 7. Emoji reaction

- Basic: `thumbsup` on a message — `{status: "added"}`, visible in Slack
- With colons: `:fire:` — colons stripped, reaction added
- Channel-only ref: error about needing a specific message

## 8. Unreads

Run each in both JSON and text mode:

- Full list: returns `[{channel, user, time, message}]` or "No unread messages". Text mode groups by channel.
- Names only: `--names-only` — returns channel name list
- Filter: `--channel NAME` — only that channel's messages
- Multi-filter: `--channel NAME1 --channel NAME2` — both channels included

## 9. Later (saved items)

If saved items exist, run each in both JSON and text mode:

- Default: returns `[{status, channel, user, message, channel_id, message_id}]`. Text mode groups by status category (Due today, Overdue, Bookmarked).
- With IDs: `--ids` — text output includes `[channel_id/message_ts]` per item
- Archived tab: `--tab archived`
- Completed tab: `--tab completed`
- Limit: `--limit 3` — at most 3 items
- Scroll test: if many saved items exist (10+), run without `--limit` and verify all items are returned, not just the first screenful.

## 10. Scroll and pagination depth

These specifically test that virtual list scrolling collects complete data:

- **Search pagination**: find a query with 3+ pages of results. Page through all of them with `--page N`, verify each page returns different messages and the total across pages is consistent with the `results` count.
- **Thread depth**: find a thread with many replies (5+). Use `get.py REF --with-replies` and verify the reply count matches what's visible in Slack.
- **Channel scroll**: find a date in `#inanctest` with many messages. Run `collect.py` without `--limit` and verify the count is correct by cross-referencing with Slack's UI.

---

## Pass criteria

- Every command produces expected output or expected error
- JSON and text output contain the same data in their respective formats
- Bare channel names (`inanctest`) work identically to `#inanctest`
- Scroll/pagination tests collect complete data, not just the first viewport
- No hangs or indefinite waits
