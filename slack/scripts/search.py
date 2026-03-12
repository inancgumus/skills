#!/usr/bin/env python3
"""Search Slack messages via the desktop app's CDP interface.

Requires:
  - Slack desktop app running with --remote-debugging-port=9222
  - agent-browser CLI on PATH

Usage:
  python search.py "query"
  python search.py "query" --limit 5
  python search.py "query" --json          # structured output with message IDs
  python search.py "query" --cdp 9333      # custom CDP port
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time

from slack_cdp import ab, ab_eval, decode_ab_json, ensure_clean_state, ensure_slack_cdp, find_ref


# JS that extracts structured search results including permalink hrefs.
# Slack renders each result as a block with an author, timestamp link
# (whose href encodes the channel ID and message timestamp), channel name,
# and a snippet of the message body.
EXTRACT_JS = r"""
(() => {
    // Each search result message lives under a container with this attribute.
    const items = document.querySelectorAll('[data-qa="search_message_result"]');
    if (items.length === 0) {
        // Fallback: scrape from the virtual list
        return JSON.stringify({fallback: true});
    }
    const results = [];
    for (const item of items) {
        const authorEl = item.querySelector('[data-qa="message_sender_name"]');
        const author = authorEl ? authorEl.textContent.trim() : '';

        // Timestamp link carries the permalink
        const tsLink = item.querySelector('a[data-qa="message_timestamp"]')
                    || item.querySelector('a.c-timestamp');
        const href = tsLink ? tsLink.href : '';
        const timeText = tsLink ? tsLink.textContent.trim() : '';

        // Channel name
        const chanEl = item.querySelector('[data-qa="channel_name"]')
                    || item.querySelector('.c-channel_entity__name');
        const channel = chanEl ? chanEl.textContent.trim() : '';

        // Message body
        const bodyEl = item.querySelector('[data-qa="search_message_text"]')
                    || item.querySelector('.p-search_message__body')
                    || item.querySelector('.c-search_message__body');
        const body = bodyEl ? bodyEl.innerText.trim() : '';

        results.push({author, channel, time: timeText, href, body});
    }
    return JSON.stringify({fallback: false, results});
})()
"""

# Fallback JS that parses the full innerText when structured selectors fail.
EXTRACT_TEXT_JS = r"""
(() => {
    const selectors = [
        '.p-search_results',
        '.c-search__results',
        '[data-qa="search_results"]',
        '.p-workspace_layout'
    ];
    for (const sel of selectors) {
        const el = document.querySelector(sel);
        if (el && el.innerText.trim().length > 100)
            return el.innerText.substring(0, 15000);
    }
    // Last resort: biggest div containing the query
    const all = document.querySelectorAll('div');
    let best = null, bestLen = 0;
    for (const d of all) {
        if (d.innerText.length > bestLen && d.className) {
            bestLen = d.innerText.length;
            best = d;
        }
    }
    return best ? best.innerText.substring(0, 15000) : '';
})()
"""

# JS to extract hrefs from timestamp links in search results.
EXTRACT_HREFS_JS = r"""
(() => {
    const links = document.querySelectorAll('a.c-timestamp, a[data-qa="message_timestamp"], a.c-link--secondary');
    const hrefs = [];
    for (const a of links) {
        const h = a.href || '';
        const t = a.textContent.trim();
        if (h && /archives/.test(h)) hrefs.push({href: h, text: t});
    }
    return JSON.stringify(hrefs);
})()
"""


def parse_slack_url(href: str) -> dict:
    """Extract channel_id and message_ts from a Slack permalink.

    Formats:
      /archives/CHANNEL_ID/pTIMESTAMP
      /archives/CHANNEL_ID/pTIMESTAMP?thread_ts=...&cid=...
    """
    m = re.search(r'/archives/([A-Z0-9]+)/p(\d+)', href)
    if not m:
        return {}
    channel_id = m.group(1)
    raw_ts = m.group(2)
    # Slack encodes ts as digits with no dot; the dot goes after the 10th digit
    if len(raw_ts) > 10:
        message_ts = raw_ts[:10] + "." + raw_ts[10:]
    else:
        message_ts = raw_ts
    thread_ts = None
    tm = re.search(r'thread_ts=([\d.]+)', href)
    if tm:
        thread_ts = tm.group(1)
    return {"channel_id": channel_id, "message_ts": message_ts, "thread_ts": thread_ts}


def parse_results_text(raw: str, hrefs: list[dict], limit: int) -> list[dict]:
    """Parse the raw innerText of search results into structured messages.

    Pairs each message block with its corresponding href from the hrefs list
    to provide message IDs for agent navigation.
    """
    messages: list[dict] = []
    href_idx = 0

    # Split into blocks by author lines (Name \n channel-or-DM \n date)
    # We look for patterns like:
    #   AuthorName
    #    channel-name   OR   Direct Message with ...
    #   DateString at HH:MM
    lines = raw.splitlines()
    i = 0
    while i < len(lines) and len(messages) < limit:
        line = lines[i].strip()

        # Skip boilerplate
        if not line or line.startswith("Search:") or line in (
            "Messages", "From", "From:", "In", "In:", "Only my channels",
            "Only include channels I'm in:", "Exclude automations",
            "Exclude apps, bots, and workflows:", "Filters", "Previous page",
            "Next page", "Create new",
        ) or re.match(r'^Sort:', line) or re.match(r'^[\d,]+ results?$', line) or re.match(r'^Page \d+$', line):
            i += 1
            continue

        # Try to detect an author line: a name followed by a channel/DM context
        # and then a date line
        if i + 2 < len(lines):
            maybe_channel = lines[i + 1].strip()
            maybe_date = lines[i + 2].strip()

            is_channel = (
                maybe_channel.startswith('#')
                or maybe_channel.startswith('Direct Message')
                or re.match(r'^[a-z0-9_-]+$', maybe_channel)  # bare channel name
            )
            is_date = bool(re.search(
                r'(Today|Yesterday|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\d{1,2}/\d{1,2})',
                maybe_date,
            ))

            if is_channel and is_date:
                author = line
                channel = maybe_channel.lstrip('#').strip()
                date_str = maybe_date
                i += 3

                # Collect body lines until we hit a reaction, reply count,
                # next author block, or known separator
                body_lines: list[str] = []
                while i < len(lines):
                    peek = lines[i].strip()
                    # Stop signals
                    if not peek:
                        i += 1
                        continue
                    # Reaction line
                    if re.match(r'^\d+ reactions?', peek):
                        i += 1
                        continue
                    # Reply count
                    if re.match(r'^\d+ repl', peek):
                        i += 1
                        # skip "Last reply ..." and "View thread"
                        while i < len(lines) and lines[i].strip() in ("", "View thread") or lines[i].strip().startswith("Last reply"):
                            i += 1
                        break
                    # Next author block lookahead
                    if i + 2 < len(lines):
                        nc = lines[i + 1].strip()
                        nd = lines[i + 2].strip() if i + 2 < len(lines) else ""
                        nc_is_channel = (
                            nc.startswith('#') or nc.startswith('Direct Message')
                            or re.match(r'^[a-z0-9_-]+$', nc)
                        )
                        nd_is_date = bool(re.search(
                            r'(Today|Yesterday|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\d{1,2}/\d{1,2})',
                            nd,
                        ))
                        if nc_is_channel and nd_is_date:
                            break

                    # Skip UI elements
                    if peek in ("Show more", "View reply", "View message", "edited"):
                        i += 1
                        continue
                    if peek.startswith("From a thread in"):
                        i += 1
                        continue

                    body_lines.append(peek)
                    i += 1

                # Match with href
                href = ""
                ids: dict = {}
                if href_idx < len(hrefs):
                    href = hrefs[href_idx].get("href", "")
                    ids = parse_slack_url(href)
                    href_idx += 1

                messages.append({
                    "author": author,
                    "channel": channel,
                    "date": date_str,
                    "text": " ".join(body_lines).strip() if body_lines else "(attachment or empty)",
                    "permalink": href,
                    **ids,
                })
                continue

        i += 1

    return messages[:limit]


def main() -> None:
    parser = argparse.ArgumentParser(description="Search Slack messages via CDP")
    parser.add_argument("query", help="Search query string")
    parser.add_argument(
        "--limit", type=int, default=20, help="Max results to return (default: 20)"
    )
    parser.add_argument(
        "--cdp", type=int, default=9222, help="CDP port (default: 9222)"
    )
    parser.add_argument(
        "--json", action="store_true", dest="as_json", help="Output as JSON with message IDs"
    )
    args = parser.parse_args()

    if not shutil.which("agent-browser"):
        sys.exit("Error: agent-browser not found on PATH.")
    ensure_slack_cdp(args.cdp)

    # 1. Ensure clean state then find the Search button.
    snapshot = ensure_clean_state(args.cdp)
    search_ref = find_ref(snapshot, r'button "Search"')
    if not search_ref:
        sys.exit("Error: could not find the Search button.")

    ab("click", f"@{search_ref}", cdp=args.cdp)
    time.sleep(1)

    # 2. Fill query and submit
    snapshot = ab("snapshot", "-i", cdp=args.cdp)
    query_ref = find_ref(snapshot, r'combobox.*Query')
    if not query_ref:
        # fallback: look for any focused input
        query_ref = find_ref(snapshot, r'(combobox|textbox|input)')
    if not query_ref:
        sys.exit("Error: could not find the search input.")

    ab("fill", f"@{query_ref}", args.query, cdp=args.cdp)
    ab("press", "Enter", cdp=args.cdp)
    time.sleep(3)

    # 3. Try structured extraction first
    raw_json = ab_eval(EXTRACT_JS, cdp=args.cdp)
    data = decode_ab_json(raw_json)
    if isinstance(data, str):
        data = decode_ab_json(data)
    if not isinstance(data, dict):
        data = {"fallback": True}

    if not data.get("fallback") and data.get("results"):
        # Structured extraction worked
        results = data["results"][:args.limit]
        for r in results:
            if r.get("href"):
                r.update(parse_slack_url(r["href"]))
        messages = results
    else:
        # Fallback to text parsing + separate href extraction
        raw_text = ab_eval(EXTRACT_TEXT_JS, cdp=args.cdp)
        raw_text = decode_ab_json(raw_text)

        raw_hrefs = ab_eval(EXTRACT_HREFS_JS, cdp=args.cdp)
        hrefs = decode_ab_json(raw_hrefs)
        if isinstance(hrefs, str):
            hrefs = decode_ab_json(hrefs)
        if not isinstance(hrefs, list):
            hrefs = []

        if not raw_text:
            print("No results found.")
            return

        messages = parse_results_text(raw_text, hrefs, args.limit)

    if not messages:
        print("No results found.")
        return

    if args.as_json:
        print(json.dumps(messages, indent=2, ensure_ascii=False))
        return

    # Pretty-print
    for i, msg in enumerate(messages, 1):
        channel = msg.get("channel", "?")
        author = msg.get("author", "?")
        date = msg.get("date", msg.get("time", "?"))
        text = msg.get("text", msg.get("body", ""))
        cid = msg.get("channel_id", "")
        ts = msg.get("message_ts", "")

        print(f"\n[{i}] #{channel} — {author} ({date})")
        if cid and ts:
            print(f"    id: {cid}/{ts}")
        # Truncate long text for display
        if len(text) > 200:
            text = text[:200] + "..."
        print(f"    {text}")

    print(f"\n({len(messages)} result{'s' if len(messages) != 1 else ''})")


if __name__ == "__main__":
    main()
