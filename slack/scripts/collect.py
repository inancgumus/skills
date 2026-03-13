#!/usr/bin/env python3
"""Collect message IDs for a specific date from a Slack channel.

Uses Slack search to find all messages, returning their IDs
(channel_id/message_ts). Use get.py to retrieve message content.

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
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

from slack import (
    close_thread,
    ensure_slack_cdp,
    get_thread_reply_ids,
    go_to_channel,
    open_thread,
)


def search_ids(channel: str, date_str: str, limit: int, cdp: int) -> list[dict]:
    """Run search.py and return results with IDs."""
    script = os.path.join(os.path.dirname(__file__), "search.py")
    query = f"in:#{channel} on:{date_str}"

    result = subprocess.run(
        [sys.executable, script, query, "--json", "--limit", str(limit), "--cdp", str(cdp)],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        print(f"search.py failed: {result.stderr}", file=sys.stderr)
        return []

    try:
        messages = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

    return [m for m in messages if m.get("message_ts") and m.get("channel_id")]


def collect_reply_ids(messages: list[dict], cdp: int) -> dict[str, list[str]]:
    """For each message, open its thread and collect reply timestamps.

    Returns {message_ts: [reply_ts, ...]} for messages that have replies.
    """
    replies: dict[str, list[str]] = {}
    if not messages:
        return replies

    # Navigate to the channel once
    channel_id = messages[0]["channel_id"]
    go_to_channel(channel_id, cdp)

    for msg in messages:
        msg_ts = msg["message_ts"]
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

    channel = args.channel.lstrip("#")
    messages = search_ids(channel, args.date, args.limit, args.cdp)

    replies: dict[str, list[str]] = {}
    if args.replies and messages:
        replies = collect_reply_ids(messages, args.cdp)

    if args.as_json:
        out = []
        for m in messages:
            mid = f"{m['channel_id']}/{m['message_ts']}"
            entry: dict = {"message_id": mid}
            if args.replies:
                r = replies.get(m["message_ts"], [])
                entry["reply_ids"] = [f"{m['channel_id']}/{ts}" for ts in r]
            out.append(entry)
        print(json.dumps(out, indent=2))
        return

    print(f"Found {len(messages)} messages for {args.date}:\n")
    for m in messages:
        mid = f"{m['channel_id']}/{m['message_ts']}"
        print(f"  {mid}")
        if args.replies:
            r = replies.get(m["message_ts"], [])
            for rts in r:
                print(f"    reply: {m['channel_id']}/{rts}")


if __name__ == "__main__":
    main()
