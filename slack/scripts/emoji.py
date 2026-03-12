#!/usr/bin/env python3
"""Add an emoji reaction to a Slack message via the desktop app's CDP interface.

If the emoji is already on the message, clicks the existing reaction (toggles it).
Otherwise opens the reaction picker and adds it.

Requires:
  - Slack desktop app running with --remote-debugging-port=9222
  - agent-browser CLI on PATH

Usage:
  # By message ID (channel_id/message_ts from search.py):
  python emoji.py CHANNEL_ID/MESSAGE_TS EMOJI
  python emoji.py C0587R32AM9/1772100390.731669 thumbsup

  # Shortcut for the last message in a channel/DM:
  python emoji.py --last "inanctest" thumbsup
  python emoji.py --last "#ai-random" ":fire:"
  python emoji.py --last "Inanc Gumus" eyes
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time

from slack_cdp import (
    ab,
    ensure_clean_state,
    ensure_slack_cdp,
    find_all_refs,
    find_ref,
    navigate_to,
    navigate_to_message,
)


def find_existing_reaction(snapshot: str, emoji: str) -> str | None:
    """Find a reaction button matching the emoji name.

    Returns the LAST match (closest to bottom / most recent message).
    Reaction buttons look like: button "N reaction(s), react with EMOJI_NAME emoji"
    """
    pattern = re.compile(
        rf'react with {re.escape(emoji)}[\s_-]*(emoji)?',
        re.IGNORECASE,
    )
    last_ref = None
    for line in snapshot.splitlines():
        if pattern.search(line):
            m = re.search(r'\[ref=(e\d+)\]', line)
            if m:
                last_ref = m.group(1)
    return last_ref


def add_reaction_via_picker(snapshot: str, emoji: str, cdp: int) -> dict:
    """Open the reaction picker and add an emoji. Returns status dict."""
    # Try to find an "Add reaction…" button (last one = most recent message)
    add_refs = find_all_refs(snapshot, r'Add reaction')
    add_ref = add_refs[-1] if add_refs else None

    if not add_ref:
        # No "Add reaction…" visible — hover over the last timestamp to reveal toolbar
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
            add_ref = find_ref(snapshot, r'button.*(React|emoji|smiley)')

    if not add_ref:
        sys.exit("Error: could not find 'Add reaction' button for the message.")

    # Open emoji picker
    ab("click", f"@{add_ref}", cdp=cdp)
    time.sleep(1)

    # Search for the emoji
    snapshot = ab("snapshot", "-i", cdp=cdp)
    search_ref = find_ref(snapshot, r'(textbox|input|combobox).*(search|find|emoji)')
    if not search_ref:
        search_ref = find_ref(snapshot, r'(textbox|input|combobox)')
    if not search_ref:
        sys.exit("Error: could not find search input in emoji picker.")

    ab("fill", f"@{search_ref}", emoji, cdp=cdp)
    time.sleep(1)

    # Select the first result
    snapshot = ab("snapshot", "-i", cdp=cdp)
    emoji_ref = find_ref(snapshot, rf'button.*{re.escape(emoji)}')
    if not emoji_ref:
        emoji_ref = find_ref(snapshot, r'(option|button ":[^"]+:")')
    if not emoji_ref:
        ab("press", "Enter", cdp=cdp)
        return {"status": "added", "emoji": emoji, "note": "Selected via Enter (first search result)"}

    ab("click", f"@{emoji_ref}", cdp=cdp)
    return {"status": "added", "emoji": emoji}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add an emoji reaction to a Slack message via CDP"
    )
    parser.add_argument("emoji", help="Emoji name (e.g. 'thumbsup', ':fire:', '+1')")
    parser.add_argument(
        "message_id", nargs="?", default=None,
        help="Message ID as CHANNEL_ID/MESSAGE_TS (e.g. C0587R32AM9/1772100390.731669)",
    )
    parser.add_argument(
        "--last", metavar="TARGET",
        help="React to the last message in a channel or DM (e.g. 'inanctest', 'Inanc Gumus')",
    )
    parser.add_argument(
        "--cdp", type=int, default=9222, help="CDP port (default: 9222)"
    )
    args = parser.parse_args()

    if not args.message_id and not args.last:
        parser.error("Provide either a message_id or --last TARGET")

    if not shutil.which("agent-browser"):
        sys.exit("Error: agent-browser not found on PATH.")
    ensure_slack_cdp(args.cdp)

    emoji = args.emoji.strip(":")

    # Ensure clean state
    ensure_clean_state(args.cdp)

    # Navigate to the message
    if args.message_id:
        # Parse CHANNEL_ID/MESSAGE_TS
        parts = args.message_id.split("/")
        if len(parts) != 2:
            sys.exit("Error: message_id must be CHANNEL_ID/MESSAGE_TS (e.g. C0587R32AM9/1772100390.731669)")
        channel_id, message_ts = parts
        navigate_to_message(channel_id, message_ts, args.cdp)
        target = args.message_id
    else:
        target = args.last.lstrip("#")
        if not navigate_to(target, args.cdp):
            sys.exit(f"Error: could not navigate to '{target}'.")
        time.sleep(1)

    snapshot = ab("snapshot", "-i", cdp=args.cdp)

    # Check if the emoji reaction already exists — if so, toggle it
    existing_ref = find_existing_reaction(snapshot, emoji)
    if existing_ref:
        ab("click", f"@{existing_ref}", cdp=args.cdp)
        print(json.dumps({
            "status": "toggled", "target": target, "emoji": emoji,
            "note": "Clicked existing reaction button",
        }))
        return

    # Add via picker
    result = add_reaction_via_picker(snapshot, emoji, args.cdp)
    result["target"] = target
    print(json.dumps(result))


if __name__ == "__main__":
    main()
