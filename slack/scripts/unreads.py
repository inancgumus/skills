#!/usr/bin/env python3
"""Fetch unread messages. Workflow only — calls slack.py primitives, no Slack-specific internals here.

Usage:
  python unreads.py --json
  python unreads.py --channel general --json
  python unreads.py --names-only --json
"""

from __future__ import annotations

import argparse
import json
import re

from slack import ensure_slack_cdp, extract_unreads_text, go_to_unreads, parse_unreads


def main() -> None:
    parser = argparse.ArgumentParser(description="Show unread Slack messages via CDP")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output as JSON")
    parser.add_argument("--channel", action="append", default=[], metavar="NAME",
                        help="Only show unreads from these channels (can be repeated)")
    parser.add_argument("--names-only", action="store_true",
                        help="Only list channel names with unreads (skip message extraction)")
    parser.add_argument("--cdp", type=int, default=9222, help="CDP port (default: 9222)")
    args = parser.parse_args()

    ensure_slack_cdp(args.cdp)

    if not go_to_unreads(args.cdp):
        print("No unread messages.")
        return

    if args.names_only:
        text = extract_unreads_text(args.cdp)
        messages = parse_unreads(text)
        channels = sorted({m["channel"] for m in messages if m.get("channel")})
        if not channels:
            print("No unread messages.")
            return
        if args.as_json:
            print(json.dumps(channels))
        else:
            for ch in channels:
                print(ch)
        return

    text = extract_unreads_text(args.cdp)
    messages = parse_unreads(text)

    # Filter by channel
    if args.channel:
        normalized = [ch.lstrip("#").lower() for ch in args.channel]
        messages = [m for m in messages if m.get("channel", "").lower() in normalized]

    if not messages:
        print("No unread messages.")
        return

    if args.as_json:
        print(json.dumps(messages, indent=2, ensure_ascii=False))
        return

    current_ch = None
    for msg in messages:
        if msg["channel"] != current_ch:
            current_ch = msg["channel"]
            print(f"\n#{current_ch}")
            print("-" * (len(current_ch) + 1))
        print(f"  {msg['user']} ({msg['time']}): {msg['message']}")
    print()


if __name__ == "__main__":
    main()
