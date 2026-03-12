#!/usr/bin/env python3
"""Fetch unread Slack messages via the Slack desktop app's CDP interface.

Requires:
  - Slack desktop app running with --remote-debugging-port=9222
  - agent-browser CLI on PATH (https://github.com/anthropics/agent-browser)

Usage:
  python unreads.py [--channel NAME ...] [--cdp PORT]
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time

from slack_cdp import ab, ab_eval, decode_ab_json, ensure_clean_state, find_ref


def parse_unreads(text: str) -> list[dict]:
    """Parse the raw innerText of the unreads view into structured messages."""
    messages: list[dict] = []
    current_channel = None
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip empty / UI-only lines
        if not line or line in (
            "Mark as Read",
            "Mark All Messages Read",
            "Press Esc to Mark as Read",
        ):
            i += 1
            continue

        # Channel header: line followed by "N message(s)"
        if i + 1 < len(lines) and re.match(r'^\d+ messages?$', lines[i + 1].strip()):
            current_channel = line
            i += 2  # skip the "N message(s)" line
            continue

        # Author + timestamp pattern: name on one line, HH:MM on the next
        if i + 1 < len(lines) and re.match(r'^\d{1,2}:\d{2}$', lines[i + 1].strip()):
            author = line
            timestamp = lines[i + 1].strip()
            # Collect message body (all lines until next author/channel/end)
            i += 2
            body_lines: list[str] = []
            while i < len(lines):
                peek = lines[i].strip()
                if not peek or peek in ("Mark as Read", "Press Esc to Mark as Read"):
                    i += 1
                    continue
                # Next author (followed by timestamp)?
                if (
                    i + 1 < len(lines)
                    and re.match(r'^\d{1,2}:\d{2}$', lines[i + 1].strip())
                ):
                    break
                # Next channel header?
                if (
                    i + 1 < len(lines)
                    and re.match(r'^\d+ messages?$', lines[i + 1].strip())
                ):
                    break
                if peek == "Mark All Messages Read":
                    break
                body_lines.append(peek)
                i += 1
            messages.append(
                {
                    "channel": current_channel,
                    "author": author,
                    "time": timestamp,
                    "text": "\n".join(body_lines) if body_lines else "(no text / attachment)",
                }
            )
            continue

        i += 1

    return messages


def main() -> None:
    parser = argparse.ArgumentParser(description="Show unread Slack messages via CDP")
    parser.add_argument(
        "--cdp", type=int, default=9222, help="CDP port (default: 9222)"
    )
    parser.add_argument(
        "--json", action="store_true", dest="as_json", help="Output as JSON"
    )
    parser.add_argument(
        "--channel", action="append", default=[], metavar="NAME",
        help="Only show unreads from these channels (can be repeated)",
    )
    parser.add_argument(
        "--names-only", action="store_true",
        help="Only list channel names with unreads (skip message extraction)",
    )
    args = parser.parse_args()
    # Normalize: strip leading # and lowercase for comparison
    args.channel = [ch.lstrip("#").lower() for ch in args.channel]

    if not shutil.which("agent-browser"):
        sys.exit("Error: agent-browser not found on PATH.")

    # 1. Ensure clean state so the sidebar is visible, then find Unreads.
    snapshot = ensure_clean_state(args.cdp)
    unreads_ref = find_ref(snapshot, r'"?Unreads"?')
    if not unreads_ref:
        sys.exit("Error: could not find the Unreads button in Slack sidebar.")

    # 2. Click Unreads
    ab("click", f"@{unreads_ref}", cdp=args.cdp)
    time.sleep(2)

    # 2b. --names-only: parse channel names from snapshot (fast, no JS eval needed)
    #     The unreads view shows buttons like: button "#ai-random section"
    if args.names_only:
        snap = ab("snapshot", "-i", cdp=args.cdp)
        channels = re.findall(r'button "#(.+?) section"', snap)
        if not channels:
            print("No unread messages.")
            sys.exit(0)
        if args.as_json:
            print(json.dumps(channels))
        else:
            for ch in channels:
                print(ch)
        return

    # 3. Extract message text from the main content area
    js = """\
(() => {
    const el = document.querySelector('.p-unreads_view')
            || document.querySelector('[data-qa="unreads_view"]')
            || document.querySelector('.p-workspace__primary_view')
            || document.querySelector('[role="main"]');
    return el ? el.innerText : '';
})()"""
    raw = ab_eval(js, cdp=args.cdp)

    # agent-browser wraps output in quotes and escapes newlines
    raw = decode_ab_json(raw)

    if not raw:
        print("No unread messages.")
        return

    messages = parse_unreads(raw)

    # Filter by channel name if requested
    if args.channel:
        messages = [
            m for m in messages
            if m.get("channel", "").lower() in args.channel
        ]

    if not messages:
        print("No unread messages.")
        return

    if args.as_json:
        print(json.dumps(messages, indent=2, ensure_ascii=False))
        return

    # Pretty-print
    current_ch = None
    for msg in messages:
        if msg["channel"] != current_ch:
            current_ch = msg["channel"]
            print(f"\n#{current_ch}")
            print("-" * (len(current_ch) + 1))
        print(f"  {msg['author']} ({msg['time']}): {msg['text']}")

    print()


if __name__ == "__main__":
    main()
