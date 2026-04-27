#!/usr/bin/env python3
"""Get message content by ID(s). Workflow only — calls slack.py primitives, no Slack-specific internals here.

Usage:
  python get.py C0123456789/1234567890.123456 --json
  python get.py C0123456789/1234567890.123456 --with-replies --json
  python get.py C0123456789/111.1 C0123456789/222.2 --json
  python get.py "https://...slack.com/archives/C.../p..." --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys

from slack import (
    close_thread,
    ensure_slack_cdp,
    get_channel_name,
    go_to_channel,
    open_thread,
    parse_slack_url,
    read_message_content,
    read_thread_messages,
    resolve_ref,
    scroll_to_message,
    ts_to_iso,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Get message content by ID(s)")
    parser.add_argument("message_ids", nargs="+", help="CHANNEL_ID/MESSAGE_TS or Slack URL (one or more)")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output as JSON")
    parser.add_argument("--with-replies", action="store_true", dest="with_replies", help="Include thread replies")
    parser.add_argument("--cdp", type=int, default=9222, help="CDP port (default: 9222)")
    args = parser.parse_args()

    ensure_slack_cdp(args.cdp)

    # Resolve and group by channel for efficient navigation.
    # For thread URLs, extract the parent ts so we can open the right thread
    # instead of guessing from visible DOM.
    by_channel: dict[str, list[tuple[str, str | None]]] = {}  # cid -> [(msg_ts, parent_ts)]
    for mid in args.message_ids:
        cid, ts = resolve_ref(mid, args.cdp)
        if ts == "":
            sys.exit("Error: must reference a specific message, not just a channel.")
        parent_ts = None
        if "archives/" in mid:
            parsed = parse_slack_url(mid)
            thread_id = parsed.get("thread_id")
            if thread_id and thread_id != ts:
                parent_ts = thread_id
        by_channel.setdefault(cid, []).append((ts, parent_ts))

    # Read each message
    records: list[dict] = []
    for channel_id, entries in by_channel.items():
        go_to_channel(channel_id, args.cdp)
        channel = get_channel_name(channel_id, args.cdp)
        for ts, parent_ts in entries:
            data = read_message_content(ts, args.cdp, parent_ts=parent_ts)
            if data is None:
                records.append({"channel_id": channel_id, "channel": channel,
                                "message_id": ts, "error": "not found"})
            else:
                records.append({
                    "channel_id": channel_id, "channel": channel,
                    "message_id": ts, "date": ts_to_iso(ts),
                    "user": data.get("user", ""),
                    "message": data.get("message", ""),
                    "reactions": data.get("reactions", []),
                })

    # Read thread replies
    if args.with_replies:
        thread_msgs: dict[str, dict[str, str]] = {}
        for channel_id, entries in by_channel.items():
            go_to_channel(channel_id, args.cdp)
            for ts, parent_ts in entries:
                thread_root = parent_ts or ts
                scroll_to_message(thread_root, args.cdp)
                if open_thread(thread_root, args.cdp):
                    thread_msgs[ts] = read_thread_messages(args.cdp)
                    close_thread(args.cdp)

        for rec in records:
            replies = thread_msgs.get(rec["message_id"], {})
            replies.pop(rec["message_id"], None)
            rec["replies"] = [
                {"message_id": rts, "date": ts_to_iso(rts), "message": txt}
                for rts, txt in replies.items()
            ]

    # Output
    if args.as_json:
        out = records[0] if len(records) == 1 else records
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return

    for rec in records:
        if "error" in rec:
            print(f"{rec['channel_id']}/{rec['message_id']}: ({rec['error']})")
            continue
        m = re.search(r"\d{1,2}:\d{2}", rec.get("date", ""))
        time_str = m.group() if m else rec.get("date", "")
        print(f"{rec.get('user', '?')} ({time_str}):")
        print(rec.get("message", ""))
        reactions = rec.get("reactions", [])
        if reactions:
            print("--\nReactions:")
            for r in reactions:
                print(f"- {r['user']}: :{r['emoji']}:")
        replies = rec.get("replies", [])
        if replies:
            print(f"\n--- {len(replies)} replies ---")
            for reply in replies:
                print(f"\n{reply['message']}")


if __name__ == "__main__":
    main()
