#!/usr/bin/env python3
"""Send a message to a Slack channel or DM via the desktop app's CDP interface.

Requires:
  - Slack desktop app running with --remote-debugging-port=9222
  - agent-browser CLI on PATH

Usage:
  python reply.py "Inanc Gumus" "hello from the script"          # dry-run (default)
  python reply.py "Inanc Gumus" "hello from the script" --send   # actually send
  python reply.py "#ai-random" "hey everyone" --send
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time

from slack_cdp import ab, ensure_clean_state, find_ref, navigate_to


def find_message_box(snapshot: str) -> str | None:
    """Find the message input textbox."""
    for line in snapshot.splitlines():
        if re.search(r'textbox "Message', line, re.IGNORECASE):
            m = re.search(r'\[ref=(e\d+)\]', line)
            if m:
                return m.group(1)
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send a message to a Slack channel or DM via CDP"
    )
    parser.add_argument("target", help="Channel name or person name (e.g. '#ai-random' or 'Inanc Gumus')")
    parser.add_argument("message", help="Message text to send")
    parser.add_argument(
        "--send", action="store_true",
        help="Actually send the message (default is dry-run: fills but does not send)",
    )
    parser.add_argument(
        "--cdp", type=int, default=9222, help="CDP port (default: 9222)"
    )
    args = parser.parse_args()

    if not shutil.which("agent-browser"):
        sys.exit("Error: agent-browser not found on PATH.")

    # 1. Ensure we're in a clean state
    ensure_clean_state(args.cdp)

    # 2. Navigate to the target channel/DM using quick switcher
    target = args.target.lstrip("#")
    if not navigate_to(target, args.cdp):
        sys.exit(f"Error: could not open quick switcher to navigate to '{target}'.")

    # 3. Find the message input box
    snapshot = ab("snapshot", "-i", cdp=args.cdp)
    msg_ref = find_message_box(snapshot)
    if not msg_ref:
        # Sometimes need a moment for the channel to load
        time.sleep(1)
        snapshot = ab("snapshot", "-i", cdp=args.cdp)
        msg_ref = find_message_box(snapshot)
    if not msg_ref:
        sys.exit("Error: could not find the message input box.")

    # 4. Fill the message
    ab("fill", f"@{msg_ref}", args.message, cdp=args.cdp)

    if args.send:
        # Click the Send button — pressing Enter doesn't work reliably
        # in Slack's rich text editor via CDP.
        snapshot = ab("snapshot", "-i", cdp=args.cdp)
        send_ref = find_ref(snapshot, r'button "Send now"')
        if send_ref:
            ab("click", f"@{send_ref}", cdp=args.cdp)
        else:
            # Fallback: try clicking the textbox for focus then Enter
            ab("click", f"@{msg_ref}", cdp=args.cdp)
            time.sleep(0.3)
            ab("press", "Enter", cdp=args.cdp)
        print(json.dumps({"status": "sent", "target": target, "message": args.message}))
    else:
        print(json.dumps({
            "status": "dry-run",
            "target": target,
            "message": args.message,
            "note": "Message filled but NOT sent. Pass --send to send.",
        }))


if __name__ == "__main__":
    main()
