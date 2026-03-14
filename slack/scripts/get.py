#!/usr/bin/env python3
"""Get message content from Slack by message ID(s).

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
import datetime
import json
import re
import sys

from slack import (
    ensure_slack_cdp,
    get_channel_name,
    go_to_channel,
    resolve_ref,
    read_message_content,
)


def ts_to_iso(ts: str) -> str:
    dt = datetime.datetime.fromtimestamp(float(ts.split(".")[0]), datetime.timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def to_json_record(channel_id: str, channel: str, ts: str, data: dict | None) -> dict:
    if data is None:
        return {"channel_id": channel_id, "channel": channel, "message_id": ts, "error": "not found"}
    return {
        "channel_id": channel_id,
        "channel": channel,
        "message_id": ts,
        "date": ts_to_iso(ts),
        "user": data.get("user", ""),
        "message": data.get("message", ""),
        "reactions": data.get("reactions", []),
    }


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
        cid, ts = resolve_ref(mid, args.cdp)
        if ts == "":
            print("Error: message_id must reference a specific message, not just a channel.", file=sys.stderr)
            sys.exit(1)
        by_channel.setdefault(cid, []).append(ts)

    results: list[tuple[str, str, str, dict | None]] = []
    for channel_id, timestamps in by_channel.items():
        go_to_channel(channel_id, args.cdp)
        channel = get_channel_name(channel_id, args.cdp)
        for ts in timestamps:
            data = read_message_content(ts, args.cdp)
            results.append((channel_id, channel, ts, data))

    if args.as_json:
        records = [to_json_record(cid, ch, ts, data) for cid, ch, ts, data in results]
        out = records[0] if len(records) == 1 else records
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return

    for channel_id, channel, ts, data in results:
        if not data:
            print(f"{channel_id}/{ts}: (not found)")
            continue
        user = data.get("user", "?")
        date_label = data.get("dateLabel", "")
        message = data.get("message", "")
        reactions = data.get("reactions", [])

        m = re.search(r"\d{1,2}:\d{2}", date_label)
        time_str = m.group() if m else date_label
        print(f"{user} ({time_str}):")
        print(message)
        if reactions:
            print("--")
            print("Reactions:")
            for r in reactions:
                print(f"- {r['user']}: :{r['emoji']}:")


if __name__ == "__main__":
    main()
