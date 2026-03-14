#!/usr/bin/env python3
"""Add an emoji reaction to a Slack message via the desktop app's CDP interface.

Requires:
  - Slack desktop app running with --remote-debugging-port=9222
  - agent-browser CLI on PATH

Usage:
  python emoji.py MESSAGE_ID EMOJI
  python emoji.py C0123456789/1234567890.123456 thumbsup
  python emoji.py https://workspace.slack.com/archives/C.../p... fire
"""

from __future__ import annotations

import argparse
import json
import sys

from slack import (
    add_emoji,
    ensure_slack_cdp,
    go_to_channel,
    resolve_ref,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Add an emoji reaction to a Slack message via CDP")
    parser.add_argument("message_id", help="Message reference (URL or CHANNEL_ID/TS)")
    parser.add_argument("emoji", help="Emoji name (e.g. 'thumbsup', ':fire:', '+1')")
    parser.add_argument("--cdp", type=int, default=9222, help="CDP port (default: 9222)")
    args = parser.parse_args()

    ensure_slack_cdp(args.cdp)

    emoji = args.emoji.strip(":")
    channel_id, message_id = resolve_ref(args.message_id, args.cdp)

    if message_id == "":
        sys.exit("Error: message_id must reference a specific message, not just a channel.")

    go_to_channel(channel_id, args.cdp)
    ok = add_emoji(message_id, emoji, args.cdp)
    print(json.dumps({"status": "added" if ok else "failed", "target": args.message_id, "emoji": emoji}))


if __name__ == "__main__":
    main()
