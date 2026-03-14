#!/usr/bin/env python3
"""Send a message to a Slack channel or thread via the desktop app's CDP interface.

Requires:
  - Slack desktop app running with --remote-debugging-port=9222
  - agent-browser CLI on PATH

Usage:
  # Channel message (dry-run by default):
  python reply.py C0123456789 "hello"
  python reply.py "#general" "hey everyone" --send

  # Thread reply:
  python reply.py C0123456789/1234567890.123456 "thread reply" --send
  python reply.py C0123456789/p1234567890123456 "thread reply" --send
  python reply.py https://app.slack.com/archives/C0123456789/p1234567890123456 "reply" --send
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time

from slack import (
    ab,
    ensure_clean_state,
    ensure_slack_cdp,
    find_ref,
    go_to_channel,
    navigate_to,
    resolve_ref,
    reply_in_thread,
)


def find_message_box(snapshot: str) -> str | None:
    """Find the channel message input textbox."""
    for line in snapshot.splitlines():
        if re.search(r'textbox "Message', line, re.IGNORECASE):
            m = re.search(r'\[ref=(e\d+)\]', line)
            if m:
                return m.group(1)
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send a message to a Slack channel, DM, or thread via CDP"
    )
    parser.add_argument("message_id", help="Channel ID, #name, CHANNEL_ID/MESSAGE_TS, or Slack URL")
    parser.add_argument("message", help="Message text to send")
    parser.add_argument("--send", action="store_true", help="Actually send (default is dry-run)")
    parser.add_argument("--cdp", type=int, default=9222, help="CDP port (default: 9222)")
    args = parser.parse_args()

    ensure_slack_cdp(args.cdp)

    channel_id, message_id = resolve_ref(args.message_id, args.cdp)

    if message_id != "":
        # Thread reply mode
        if not args.send:
            print(json.dumps({
                "status": "dry-run", "target": args.message_id, "message": args.message,
                "note": "Pass --send to send the thread reply.",
            }))
            return
        go_to_channel(channel_id, args.cdp)
        ok = reply_in_thread(message_id, args.message, args.cdp)
        print(json.dumps({
            "status": "sent" if ok else "failed",
            "target": args.message_id, "message": args.message,
        }))
        return

    # Channel message mode
    ensure_clean_state(args.cdp)
    target = channel_id
    if not navigate_to(target, args.cdp):
        sys.exit(f"Error: could not navigate to '{target}'.")

    snapshot = ab("snapshot", "-i", cdp=args.cdp)
    msg_ref = find_message_box(snapshot)
    if not msg_ref:
        time.sleep(1)
        snapshot = ab("snapshot", "-i", cdp=args.cdp)
        msg_ref = find_message_box(snapshot)
    if not msg_ref:
        sys.exit("Error: could not find the message input box.")

    ab("fill", f"@{msg_ref}", args.message, cdp=args.cdp)

    if args.send:
        snapshot = ab("snapshot", "-i", cdp=args.cdp)
        send_ref = find_ref(snapshot, r'button "Send now"')
        if send_ref:
            ab("click", f"@{send_ref}", cdp=args.cdp)
        else:
            ab("click", f"@{msg_ref}", cdp=args.cdp)
            time.sleep(0.3)
            ab("press", "Enter", cdp=args.cdp)
        print(json.dumps({"status": "sent", "target": target, "message": args.message}))
    else:
        print(json.dumps({
            "status": "dry-run", "target": target, "message": args.message,
            "note": "Message filled but NOT sent. Pass --send to send.",
        }))


if __name__ == "__main__":
    main()
