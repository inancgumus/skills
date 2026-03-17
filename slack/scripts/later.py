#!/usr/bin/env python3
"""Fetch Later (saved) items. Workflow only — calls slack.py primitives, no Slack-specific internals here.

Usage:
  python later.py --json
  python later.py --tab archived --json
  python later.py --tab completed --json
  python later.py --limit 10 --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys

from slack import (
    ensure_slack_cdp,
    extract_visible_later_items,
    go_to_later,
    parse_saved_item,
    scroll_later_down,
    scroll_later_to_top,
)


def fetch_items(limit: int, cdp: int) -> list[dict]:
    """Scroll the Later virtual list, collecting parsed items."""
    items: list[dict] = []
    seen_keys: set[str] = set()

    scroll_later_to_top(cdp)

    for _ in range(40):
        batch = extract_visible_later_items(cdp)
        if not batch:
            break

        new_count = 0
        for entry in batch:
            key = entry["key"]
            if key in seen_keys:
                continue
            seen_keys.add(key)
            item = parse_saved_item(entry["lines"])
            # Extract channel_id and message_ts from data-item-key
            parts = key.split("-", 1)
            if len(parts) == 2:
                item["channel_id"] = parts[0]
                item["message_id"] = parts[1].split("_", 1)[0]
            items.append(item)
            new_count += 1

        if new_count == 0 or len(items) >= limit:
            break
        scroll_later_down(cdp)

    return items[:limit]


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Slack Later items via CDP")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output as JSON")
    parser.add_argument("--tab", choices=["in-progress", "archived", "completed"],
                        default="in-progress", help="Which tab to show (default: in-progress)")
    parser.add_argument("--limit", type=int, default=50, help="Max items to return (default: 50)")
    parser.add_argument("--ids", action="store_true", help="Show message IDs (channel_id/message_ts)")
    parser.add_argument("--cdp", type=int, default=9222, help="CDP port (default: 9222)")
    args = parser.parse_args()

    ensure_slack_cdp(args.cdp)

    if not go_to_later(args.tab, args.cdp):
        sys.exit("Error: could not find the Later tab.")

    items = fetch_items(args.limit, args.cdp)

    if not items:
        print("No later items found.")
        return

    if args.as_json:
        print(json.dumps(items, indent=2, ensure_ascii=False))
        return

    # Group by status category
    groups: dict[str, list[dict]] = {}
    for item in items:
        status = item["status"]
        if status.startswith("Due"):
            group = status
        elif status.startswith("Overdue"):
            group = "Overdue"
        else:
            group = "Bookmarked"
        groups.setdefault(group, []).append(item)

    def sort_key(group_name: str) -> tuple:
        if group_name == "Due today":
            return (0, 0)
        if group_name.startswith("Due in"):
            n = re.search(r'\d+', group_name)
            return (0, int(n.group()) if n else 99)
        if group_name == "Overdue":
            return (1, 0)
        return (2, 0)

    for group in sorted(groups, key=sort_key):
        print(f"{group}:")
        for item in groups[group]:
            ch = item["channel"]
            text = item["message"]
            if len(text) > 120:
                text = text[:120] + "..."
            msg_id = f" [{item.get('channel_id','')}/{item.get('message_id','')}]" if args.ids else ""
            print(f"  - #{ch}: {item['user']}: {text}{msg_id}")
        print()


if __name__ == "__main__":
    main()
