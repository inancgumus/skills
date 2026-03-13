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
import sys
import time

from slack import ab, ab_eval, decode_ab_json, ensure_slack_cdp, find_ref


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


STATUS_RE = re.compile(
    r'^(Overdue by .+|Due in .+|Due today|No due date|Completed .+|Archived .+)',
    re.IGNORECASE,
)


def parse_saved_item(lines: list[str]) -> dict:
    """Parse text lines from a single .p-saved_item element."""
    # Filter out bullet separators and action buttons
    lines = [l for l in lines if l not in ("•", "Mark complete", "Edit reminder", "More actions")]

    i = 0
    status = ""
    if lines and STATUS_RE.match(lines[0]):
        status = lines[0]
        i = 1

    channel = lines[i] if i < len(lines) else ""
    author = lines[i + 1] if i + 1 < len(lines) else ""
    body = " ".join(lines[i + 2:]) if i + 2 < len(lines) else ""

    return {"status": status or "No due date", "channel": channel, "author": author, "text": body}


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
    parser.add_argument(
        "--ids", action="store_true", help="Show message IDs (channel_id/message_ts)"
    )
    args = parser.parse_args()

    ensure_slack_cdp(args.cdp)

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

    # 3. Extract items from .p-saved_item elements inside the virtual list.
    #    Scroll the container from top to bottom to trigger lazy loading.
    items: list[dict] = []
    seen_keys: set[str] = set()

    # Start from top
    ab_eval(r"""(() => {
        const sc = document.querySelector('.c-virtual_list__scroll_container');
        if (!sc) return;
        let el = sc.parentElement;
        while (el) {
            if (el.scrollHeight > el.clientHeight + 10) { el.scrollTop = 0; return; }
            el = el.parentElement;
        }
    })()""", cdp=args.cdp)
    time.sleep(0.5)

    for _ in range(40):
        raw = ab_eval(r"""
(() => {
    const listItems = document.querySelectorAll('[data-qa="virtual-list-item"]');
    if (!listItems.length) return '[]';
    return JSON.stringify([...listItems].map(li => {
        const key = li.getAttribute('data-item-key') || '';
        const saved = li.querySelector('.p-saved_item');
        const lines = saved ? (saved.innerText || '').split('\n').map(l => l.trim()).filter(Boolean) : [];
        return { key, lines };
    }).filter(x => x.key && x.lines.length >= 2));
})()
""", cdp=args.cdp)
        batch = decode_ab_json(raw)
        if not batch or not isinstance(batch, list):
            break

        new_count = 0
        for entry in batch:
            key = entry["key"]
            if key in seen_keys:
                continue
            seen_keys.add(key)
            item = parse_saved_item(entry["lines"])
            # Extract channel_id and message_ts from data-item-key (format: CHANNEL-TS_REMINDER)
            parts = key.split("-", 1)
            if len(parts) == 2:
                item["channel_id"] = parts[0]
                ts_part = parts[1].split("_", 1)[0]
                item["message_ts"] = ts_part
            items.append(item)
            new_count += 1

        if new_count == 0:
            break

        # Scroll incrementally (half a viewport at a time) so the virtual
        # list renders items as they come into view.
        ab_eval(r"""(() => {
            const sc = document.querySelector('.c-virtual_list__scroll_container');
            if (!sc) return;
            let el = sc.parentElement;
            while (el) {
                if (el.scrollHeight > el.clientHeight + 10) {
                    el.scrollTop += Math.floor(el.clientHeight / 2);
                    return;
                }
                el = el.parentElement;
            }
        })()""", cdp=args.cdp)
        time.sleep(0.5)

    if not items:
        print("No later items found.")
        return

    if args.as_json:
        print(json.dumps(items, indent=2, ensure_ascii=False))
        return

    # Group by status category, sorted: Due first, then Overdue, then Bookmarked
    groups: dict[str, list[dict]] = {}
    for item in items:
        status = item["status"]
        if status.startswith("Due"):
            group = status  # "Due in 3 days", "Due today", etc.
        elif status.startswith("Overdue"):
            group = "Overdue"
        else:
            group = "Bookmarked"
        groups.setdefault(group, []).append(item)

    def sort_key(group_name: str) -> tuple:
        if group_name == "Due today":
            return (0, 0)
        if group_name.startswith("Due in"):
            # Extract number for sorting: "Due in 3 days" -> 3
            n = re.search(r'\d+', group_name)
            return (0, int(n.group()) if n else 99)
        if group_name == "Overdue":
            return (1, 0)
        return (2, 0)  # Bookmarked last

    for group in sorted(groups, key=sort_key):
        print(f"{group}:")
        for item in groups[group]:
            ch = item["channel"]
            text = item["text"]
            if len(text) > 120:
                text = text[:120] + "..."
            msg_id = f" [{item.get('channel_id','')}/{item.get('message_ts','')}]" if args.ids else ""
            print(f"  - #{ch}: {item['author']}: {text}{msg_id}")
        print()


if __name__ == "__main__":
    main()
