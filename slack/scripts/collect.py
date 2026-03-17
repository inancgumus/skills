#!/usr/bin/env python3
"""Collect message IDs for a date. Workflow only — calls slack.py primitives, no Slack-specific internals here.

Navigates the channel directly (not search), so bot and integration messages
are included. Returns top-level messages only (not thread replies).

Usage:
  python collect.py "#general" 2026-03-09 --json
  python collect.py "#general" 2026-03-09 --with-replies --json
  python collect.py "#general" 2026-03-09 --limit 10 --json
  python collect.py "C042WNMBYQM" 2026-03-09 --json
"""

from __future__ import annotations

import argparse
import datetime
import json

from slack import (
    close_thread,
    collect_visible_message_ts,
    ensure_slack_cdp,
    get_thread_reply_ids,
    go_to_channel,
    jump_to_date,
    open_thread,
    resolve_ref,
    scroll_channel_down,
)


def collect_for_date(channel_id: str, date_str: str, limit: int, cdp: int) -> list[dict]:
    """Navigate to channel, jump to date, scroll and collect message IDs within that day."""
    year, month, day = (int(p) for p in date_str.split("-"))
    day_start = datetime.datetime(year, month, day).timestamp()
    day_end = datetime.datetime(year, month, day, 23, 59, 59).timestamp()

    go_to_channel(channel_id, cdp)
    if not jump_to_date(year, month, day, cdp):
        return []

    seen: set[str] = set()
    results: list[dict] = []

    for _ in range(60):
        past_end = False
        for ts in collect_visible_message_ts(cdp):
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
        scroll_channel_down(cdp)

    return results


def collect_replies(messages: list[dict], cdp: int) -> dict[str, list[str]]:
    """For each message, open its thread and collect reply timestamps."""
    replies: dict[str, list[str]] = {}
    if not messages:
        return replies

    go_to_channel(messages[0]["channel_id"], cdp)
    for msg in messages:
        if not open_thread(msg["message_id"], cdp):
            continue
        ids = get_thread_reply_ids(cdp)
        if ids:
            replies[msg["message_id"]] = ids
        close_thread(cdp)

    return replies


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect message IDs for a date from a Slack channel")
    parser.add_argument("channel", help="Channel name (e.g. '#general') or ID")
    parser.add_argument("date", help="Date in YYYY-MM-DD format")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output as JSON")
    parser.add_argument("--with-replies", action="store_true", dest="with_replies", help="Also collect reply IDs for each message")
    parser.add_argument("--limit", type=int, default=50, help="Max messages (default: 50)")
    parser.add_argument("--cdp", type=int, default=9222, help="CDP port (default: 9222)")
    args = parser.parse_args()

    ensure_slack_cdp(args.cdp)

    channel_id, _ = resolve_ref(args.channel, args.cdp)
    messages = collect_for_date(channel_id, args.date, args.limit, args.cdp)

    replies: dict[str, list[str]] = {}
    if args.with_replies and messages:
        replies = collect_replies(messages, args.cdp)

    if args.as_json:
        out = []
        for m in messages:
            mid = f"{m['channel_id']}/{m['message_id']}"
            entry: dict = {"message_id": mid}
            if args.with_replies:
                r = replies.get(m["message_id"], [])
                entry["reply_ids"] = [f"{m['channel_id']}/{ts}" for ts in r]
            out.append(entry)
        print(json.dumps(out, indent=2))
        return

    print(f"Found {len(messages)} messages for {args.date}:\n")
    for m in messages:
        mid = f"{m['channel_id']}/{m['message_id']}"
        print(f"  {mid}")
        if args.with_replies:
            r = replies.get(m["message_id"], [])
            for rts in r:
                print(f"    reply: {m['channel_id']}/{rts}")


if __name__ == "__main__":
    main()
