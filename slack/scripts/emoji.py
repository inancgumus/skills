#!/usr/bin/env python3
"""Add an emoji reaction to a Slack message via the desktop app's CDP interface.

Requires:
  - Slack desktop app running with --remote-debugging-port=9222
  - agent-browser CLI on PATH

Usage:
  # By message ID (channel_id/message_ts):
  python emoji.py EMOJI CHANNEL_ID/MESSAGE_TS
  python emoji.py thumbsup C0123456789/1234567890.123456

  # Shortcut for the last message in a channel/DM:
  python emoji.py --last "#general" thumbsup
  python emoji.py --last "#random" ":fire:"
  python emoji.py --last "Jane Smith" eyes
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time

from slack import (
    ab,
    add_emoji,
    ensure_clean_state,
    ensure_slack_cdp,
    find_all_refs,
    find_ref,
    go_to_channel,
    navigate_to,
    parse_message_id,
)


def find_existing_reaction(snapshot: str, emoji: str) -> str | None:
    """Find a reaction button matching the emoji name (last match = most recent message)."""
    pattern = re.compile(rf'react with {re.escape(emoji)}[\s_-]*(emoji)?', re.IGNORECASE)
    last_ref = None
    for line in snapshot.splitlines():
        if pattern.search(line):
            m = re.search(r'\[ref=(e\d+)\]', line)
            if m:
                last_ref = m.group(1)
    return last_ref


def add_reaction_via_picker(snapshot: str, emoji: str, cdp: int) -> dict:
    """Open the reaction picker on the last visible message and add an emoji."""
    add_refs = find_all_refs(snapshot, r'Add reaction')
    add_ref = add_refs[-1] if add_refs else None

    if not add_ref:
        ts_refs = find_all_refs(snapshot, r'link ".*at \d{1,2}:\d{2}')
        if not ts_refs:
            ts_refs = find_all_refs(
                snapshot,
                r'link ".*(Today|Yesterday|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec).*\d{1,2}:\d{2}',
            )
        if not ts_refs:
            sys.exit("Error: could not find any message timestamps to hover over.")
        ab("hover", f"@{ts_refs[-1]}", cdp=cdp)
        time.sleep(0.5)
        snapshot = ab("snapshot", "-i", cdp=cdp)
        add_ref = find_ref(snapshot, r'Add reaction')

    if not add_ref:
        sys.exit("Error: could not find 'Add reaction' button.")

    ab("click", f"@{add_ref}", cdp=cdp)
    time.sleep(1)
    snapshot = ab("snapshot", "-i", cdp=cdp)
    search_ref = find_ref(snapshot, r'(textbox|input|combobox).*(search|find|emoji)')
    if not search_ref:
        search_ref = find_ref(snapshot, r'(textbox|input|combobox)')
    if not search_ref:
        sys.exit("Error: could not find search input in emoji picker.")

    ab("fill", f"@{search_ref}", emoji, cdp=cdp)
    time.sleep(1)
    ab("press", "Enter", cdp=cdp)
    return {"status": "added", "emoji": emoji}


def main() -> None:
    parser = argparse.ArgumentParser(description="Add an emoji reaction to a Slack message via CDP")
    parser.add_argument("emoji", help="Emoji name (e.g. 'thumbsup', ':fire:', '+1')")
    parser.add_argument("message_id", nargs="?", default=None, help="CHANNEL_ID/MESSAGE_TS")
    parser.add_argument("--last", metavar="TARGET", help="React to the last message in a channel or DM")
    parser.add_argument("--cdp", type=int, default=9222, help="CDP port (default: 9222)")
    args = parser.parse_args()

    if not args.message_id and not args.last:
        parser.error("Provide either a message_id or --last TARGET")
    ensure_slack_cdp(args.cdp)

    emoji = args.emoji.strip(":")

    # Targeted mode: use data-msg-ts to find and react to a specific message
    if args.message_id:
        channel_id, message_ts = parse_message_id(args.message_id)
        if not channel_id:
            sys.exit("Error: message_id must be CHANNEL_ID/MESSAGE_TS")

        go_to_channel(channel_id, args.cdp)
        ok = add_emoji(message_ts, emoji, args.cdp)
        print(json.dumps({"status": "added" if ok else "failed", "target": args.message_id, "emoji": emoji}))
        return

    # --last mode: react to last message in a channel/DM
    ensure_clean_state(args.cdp)
    target = args.last.lstrip("#")
    if not navigate_to(target, args.cdp):
        sys.exit(f"Error: could not navigate to '{target}'.")
    time.sleep(1)

    snapshot = ab("snapshot", "-i", cdp=args.cdp)
    existing_ref = find_existing_reaction(snapshot, emoji)
    if existing_ref:
        ab("click", f"@{existing_ref}", cdp=args.cdp)
        print(json.dumps({"status": "toggled", "target": target, "emoji": emoji}))
        return

    result = add_reaction_via_picker(snapshot, emoji, args.cdp)
    result["target"] = target
    print(json.dumps(result))


if __name__ == "__main__":
    main()
