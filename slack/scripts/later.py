#!/usr/bin/env python3
"""Fetch Slack "Later" (saved/remind-me-later) items via the desktop app's CDP interface.

Requires:
  - Slack desktop app running with --remote-debugging-port=9222
  - agent-browser CLI on PATH

Usage:
  python later.py                           # all in-progress items
  python later.py --json                    # structured JSON
  python later.py --tab archived            # show archived items
  python later.py --tab completed           # show completed items
  python later.py --limit 5                 # cap results
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time

from slack_cdp import ab, ab_eval, decode_ab_json, find_ref


def parse_later_items(text: str, limit: int) -> list[dict]:
    """Parse the Later view innerText into structured items.

    Each item follows this pattern:
      Status line (e.g. "Overdue by 3 days", "Due in 2 hours", "No due date")
      Channel/DM name
      Author name
      Message snippet (may be multiline, ends at next status line)
    """
    items: list[dict] = []
    lines = text.splitlines()
    i = 0

    # Skip header lines until we hit the first status line
    status_pattern = re.compile(
        r'^(Overdue by .+|Due in .+|Due today|No due date|Completed .+|Archived .+)',
        re.IGNORECASE,
    )

    while i < len(lines) and len(items) < limit:
        line = lines[i].strip()

        if not status_pattern.match(line):
            i += 1
            continue

        status = line

        # Next non-empty line is channel/DM
        i += 1
        while i < len(lines) and not lines[i].strip():
            i += 1
        if i >= len(lines):
            break
        channel = lines[i].strip()

        # Next non-empty line is author
        i += 1
        while i < len(lines) and not lines[i].strip():
            i += 1
        if i >= len(lines):
            items.append({"status": status, "channel": channel, "author": "", "text": ""})
            break
        author = lines[i].strip()

        # Collect message body until next status line or end
        i += 1
        body_lines: list[str] = []
        while i < len(lines):
            peek = lines[i].strip()
            if status_pattern.match(peek):
                break
            if peek:
                body_lines.append(peek)
            i += 1

        items.append({
            "status": status,
            "channel": channel,
            "author": author,
            "text": " ".join(body_lines) if body_lines else "",
        })

    return items[:limit]


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Slack Later items via CDP")
    parser.add_argument(
        "--cdp", type=int, default=9222, help="CDP port (default: 9222)"
    )
    parser.add_argument(
        "--json", action="store_true", dest="as_json", help="Output as JSON"
    )
    parser.add_argument(
        "--tab", choices=["in-progress", "archived", "completed"], default="in-progress",
        help="Which tab to show (default: in-progress)",
    )
    parser.add_argument(
        "--limit", type=int, default=50, help="Max items to return (default: 50)"
    )
    args = parser.parse_args()

    if not shutil.which("agent-browser"):
        sys.exit("Error: agent-browser not found on PATH.")

    # 1. Click the Later tab (always visible in top tab bar)
    snapshot = ab("snapshot", "-i", cdp=args.cdp)
    later_ref = find_ref(snapshot, r'tab "Later"')
    if not later_ref:
        sys.exit("Error: could not find the Later tab.")

    ab("click", f"@{later_ref}", cdp=args.cdp)
    time.sleep(2)

    # 2. Click the sub-tab if not in-progress (which is the default)
    if args.tab != "in-progress":
        snapshot = ab("snapshot", "-i", cdp=args.cdp)
        tab_label = args.tab.capitalize()  # "Archived" or "Completed"
        tab_ref = find_ref(snapshot, rf'tab "{tab_label}')
        if tab_ref:
            ab("click", f"@{tab_ref}", cdp=args.cdp)
            time.sleep(1)

    # 3. Extract text content
    raw = ab_eval(r"""
(() => {
    const all = document.querySelectorAll('div');
    let best = null, bestLen = 0;
    for (const d of all) {
        const t = d.innerText || '';
        if (t.length > bestLen && (t.includes('Overdue') || t.includes('Due') || t.includes('Completed') || t.includes('Archived')) && t.includes('progress')) {
            bestLen = t.length;
            best = d;
        }
    }
    return best ? best.innerText.substring(0, 15000) : '';
})()
""", cdp=args.cdp)

    raw = decode_ab_json(raw)

    if not raw:
        print("No later items found.")
        return

    items = parse_later_items(raw, args.limit)

    if not items:
        print("No later items found.")
        return

    if args.as_json:
        print(json.dumps(items, indent=2, ensure_ascii=False))
        return

    # Pretty-print
    for item in items:
        status = item["status"]
        channel = item["channel"]
        author = item["author"]
        text = item["text"]
        if len(text) > 150:
            text = text[:150] + "..."
        print(f"  [{status}] #{channel}")
        print(f"    {author}: {text}")
        print()


if __name__ == "__main__":
    main()
