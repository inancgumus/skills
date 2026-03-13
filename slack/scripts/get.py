#!/usr/bin/env python3
"""Get message content from Slack by message ID(s).

Same navigation pattern as reply.py — navigates to the channel,
scrolls to the message, and extracts its full text content.

Requires:
  - Slack desktop app running with --remote-debugging-port=9222
  - agent-browser CLI on PATH

Usage:
  python get.py C0123456789/1234567890.123456
  python get.py C0123456789/1234567890.123456 C0123456789/1234567891.456789
  python get.py C0123456789/1234567890.123456 --json
  python get.py C0123456789/1234567890.123456 --cdp 9333
"""

from __future__ import annotations

import argparse
import json
import sys

from slack import (
    ensure_slack_cdp,
    go_to_channel,
    parse_message_id,
    read_message_content,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Get message content by ID(s)")
    parser.add_argument("message_ids", nargs="+", help="CHANNEL_ID/MESSAGE_TS (one or more)")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output as JSON")
    parser.add_argument("--cdp", type=int, default=9222, help="CDP port (default: 9222)")
    args = parser.parse_args()

    ensure_slack_cdp(args.cdp)

    # Group by channel to minimize navigation
    by_channel: dict[str, list[str]] = {}
    for mid in args.message_ids:
        cid, ts = parse_message_id(mid)
        if not cid:
            print(f"Invalid message ID: {mid}", file=sys.stderr)
            continue
        by_channel.setdefault(cid, []).append(ts)

    results: dict[str, str] = {}
    for channel_id, timestamps in by_channel.items():
        go_to_channel(channel_id, args.cdp)
        for ts in timestamps:
            mid = f"{channel_id}/{ts}"
            content = read_message_content(ts, args.cdp)
            results[mid] = content

    if args.as_json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return

    for mid, content in results.items():
        print(f"\n--- {mid} ---")
        if content:
            print(content[:500] + ("..." if len(content) > 500 else ""))
        else:
            print("(not found)")


if __name__ == "__main__":
    main()
