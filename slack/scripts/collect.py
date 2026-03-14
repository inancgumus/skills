#!/usr/bin/env python3
"""Collect message IDs for a specific date from a Slack channel.

Navigates to the channel, jumps to the date, and reads message timestamps
directly from the DOM. This is more reliable than search — the channel pane
only shows top-level messages, so thread replies are excluded automatically,
and bot/integration messages are included.

Requires:
  - Slack desktop app running with --remote-debugging-port=9222
  - agent-browser CLI on PATH

Usage:
  python collect.py "#general" 2026-03-09
  python collect.py "#general" 2026-03-09 --json
  python collect.py "#general" 2026-03-09 --replies
  python collect.py "#general" 2026-03-09 --replies --json
  python collect.py "#general" 2026-03-09 --limit 10
  python collect.py "#general" 2026-03-09 --cdp 9333
  python collect.py "C042WNMBYQM" 2026-03-09
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
import time

from slack import (
    DOM,
    ab_eval,
    close_thread,
    decode_ab_json,
    ensure_slack_cdp,
    get_channel_name,
    get_thread_reply_ids,
    go_to_channel,
    jump_to_date,
    open_thread,
    resolve_ref,
)


def collect_top_level_ids(channel_id: str, date_str: str, limit: int, cdp: int) -> list[dict]:
    """Navigate to the channel, jump to date, collect top-level message IDs from DOM.

    The channel message pane only renders top-level messages, so no filtering
    is needed to exclude thread replies.
    """
    year, month, day = (int(p) for p in date_str.split("-"))
    day_start = datetime.datetime(year, month, day).timestamp()
    day_end = datetime.datetime(year, month, day, 23, 59, 59).timestamp()

    go_to_channel(channel_id, cdp)
    if not jump_to_date(year, month, day, cdp):
        return []

    COLLECT_JS = f"""(() => {{
        const msgs = [...document.querySelectorAll('{DOM["MESSAGE"]}')];
        return JSON.stringify(msgs.map(m => m.dataset.msgTs).filter(Boolean));
    }})()"""

    SCROLL_JS = f"""(() => {{
        const msgs = document.querySelectorAll('{DOM["MESSAGE"]}');
        if (!msgs.length) return false;
        msgs[msgs.length - 1].scrollIntoView({{block: 'start'}});
        return true;
    }})()"""

    seen: set[str] = set()
    results: list[dict] = []

    for _ in range(60):
        raw = ab_eval(COLLECT_JS, cdp=cdp)
        all_ts = decode_ab_json(raw)
        if not isinstance(all_ts, list):
            break

        past_end = False
        for ts in all_ts:
            if ts in seen:
                continue
            try:
                unix = float(ts)
            except ValueError:
                continue
            if unix > day_end:
                past_end = True
                continue
            if unix < day_start:
                continue
            seen.add(ts)
            results.append({"channel_id": channel_id, "message_id": ts})
            if len(results) >= limit:
                return results

        if past_end:
            break

        ab_eval(SCROLL_JS, cdp=cdp)
        time.sleep(0.5)

    return results


def collect_reply_ids(messages: list[dict], cdp: int) -> dict[str, list[str]]:
    """For each message, open its thread and collect reply timestamps.

    Returns {message_id: [reply_ts, ...]} for messages that have replies.
    """
    replies: dict[str, list[str]] = {}
    if not messages:
        return replies

    channel_id = messages[0]["channel_id"]
    go_to_channel(channel_id, cdp)

    for msg in messages:
        msg_ts = msg["message_id"]
        if not open_thread(msg_ts, cdp):
            continue
        reply_ids = get_thread_reply_ids(cdp)
        if reply_ids:
            replies[msg_ts] = reply_ids
        close_thread(cdp)

    return replies


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect message IDs for a date from a Slack channel")
    parser.add_argument("channel", help="Channel name (e.g. 'general')")
    parser.add_argument("date", help="Date in YYYY-MM-DD format")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output as JSON")
    parser.add_argument("--replies", action="store_true", help="Also collect reply IDs for each message")
    parser.add_argument("--limit", type=int, default=50, help="Max messages (default: 50)")
    parser.add_argument("--cdp", type=int, default=9222, help="CDP port (default: 9222)")
    args = parser.parse_args()

    ensure_slack_cdp(args.cdp)

    channel_id, _ = resolve_ref(args.channel, args.cdp)

    messages = collect_top_level_ids(channel_id, args.date, args.limit, args.cdp)

    replies: dict[str, list[str]] = {}
    if args.replies and messages:
        replies = collect_reply_ids(messages, args.cdp)

    if args.as_json:
        out = []
        for m in messages:
            mid = f"{m['channel_id']}/{m['message_id']}"
            entry: dict = {"message_id": mid}
            if args.replies:
                r = replies.get(m["message_id"], [])
                entry["reply_ids"] = [f"{m['channel_id']}/{ts}" for ts in r]
            out.append(entry)
        print(json.dumps(out, indent=2))
        return

    print(f"Found {len(messages)} messages for {args.date}:\n")
    for m in messages:
        mid = f"{m['channel_id']}/{m['message_id']}"
        print(f"  {mid}")
        if args.replies:
            r = replies.get(m["message_id"], [])
            for rts in r:
                print(f"    reply: {m['channel_id']}/{rts}")


if __name__ == "__main__":
    main()
