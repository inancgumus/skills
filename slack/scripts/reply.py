#!/usr/bin/env python3
"""Send a message to a channel or thread. Workflow only — calls slack.py primitives, no Slack-specific internals here.

Usage:
  # Channel message (dry-run by default):
  python reply.py "#general" "hey everyone"
  python reply.py "#general" "hey everyone" --send

  # Thread reply:
  python reply.py C0123456789/1234567890.123456 "thread reply" --send
  python reply.py "https://...slack.com/archives/C.../p..." "reply" --send
"""

from __future__ import annotations

import argparse
import json

from slack import ensure_slack_cdp, go_to_channel, reply_in_thread, resolve_ref, send_channel_message


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a message to Slack via CDP")
    parser.add_argument("message_id", help="Channel ID, #name, @DM, CHANNEL_ID/MESSAGE_TS, or Slack URL")
    parser.add_argument("message", help="Message text to send")
    parser.add_argument("--send", action="store_true", help="Actually send (default is dry-run)")
    parser.add_argument("--cdp", type=int, default=9222, help="CDP port (default: 9222)")
    args = parser.parse_args()

    ensure_slack_cdp(args.cdp)

    channel_id, message_id = resolve_ref(args.message_id, args.cdp)

    if not args.send:
        print(json.dumps({
            "status": "dry-run", "target": args.message_id, "message": args.message,
            "note": "Pass --send to send.",
        }))
        return

    if message_id:
        go_to_channel(channel_id, args.cdp)
        ok = reply_in_thread(message_id, args.message, args.cdp)
    else:
        ok = send_channel_message(channel_id, args.message, args.cdp)

    print(json.dumps({
        "status": "sent" if ok else "failed",
        "target": args.message_id, "message": args.message,
    }))


if __name__ == "__main__":
    main()
