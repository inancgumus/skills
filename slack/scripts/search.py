#!/usr/bin/env python3
"""Search Slack messages. Workflow only — calls slack.py primitives, no Slack-specific internals here.

Slack search syntax:
  in:#channel, from:@user, after:YYYY-MM-DD, before:YYYY-MM-DD, has:reaction, has:file

Usage:
  python search.py "deployment failed" --json
  python search.py "in:#ops-alerts query" --json
  python search.py "query" --page 2 --json
  python search.py "query" --click 3 --json
"""

from __future__ import annotations

import argparse
import json
import sys

from slack import (
    click_search_result_link,
    ensure_slack_cdp,
    execute_search,
    extract_visible_search_results,
    get_search_page_info,
    get_search_state,
    goto_search_page,
    read_thread_messages,
    scroll_search_down,
    scroll_search_to_top,
)


def collect_results(cdp: int, limit: int) -> list[dict]:
    """Scroll through search results, collecting up to limit unique results."""
    seen_hrefs: set[str] = set()
    results: list[dict] = []

    scroll_search_to_top(cdp)

    for _ in range(40):
        for r in extract_visible_search_results(cdp):
            href = r.get("href", "")
            if not href or href in seen_hrefs:
                continue
            seen_hrefs.add(href)
            results.append(r)

        if len(results) >= limit:
            break

        scroll = scroll_search_down(cdp)
        if scroll.get("atBottom") or not scroll.get("scrolled"):
            break

    return results[:limit]


def main() -> None:
    parser = argparse.ArgumentParser(description="Search Slack messages via CDP")
    parser.add_argument("query", help="Search query string")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output as JSON with message IDs")
    parser.add_argument("--page", type=int, default=1, help="Result page to fetch (default: 1)")
    parser.add_argument("--click", type=int, default=0, help="Click on the Nth result (1-based) to navigate there")
    parser.add_argument("--cdp", type=int, default=9222, help="CDP port (default: 9222)")
    args = parser.parse_args()

    ensure_slack_cdp(args.cdp)

    # Reuse existing search results if the query matches
    existing_query, current_page = get_search_state(args.cdp)
    on_right_page = False

    if existing_query.lower() == args.query.lower() and current_page > 0:
        on_right_page = current_page == args.page or goto_search_page(args.page, args.cdp)

    if not on_right_page:
        execute_search(args.query, args.cdp)
        if args.page > 1:
            if not goto_search_page(args.page, args.cdp):
                msg = f"Error: could not navigate to page {args.page}."
                if args.as_json:
                    print(json.dumps({"error": msg, "results": 0, "pages": 0, "messages": []}))
                else:
                    print(msg, file=sys.stderr)
                sys.exit(1)

    info = get_search_page_info(args.cdp)
    messages = collect_results(args.cdp, 20)

    if not messages:
        if args.as_json:
            print(json.dumps({"results": 0, "pages": 0, "messages": []}))
        else:
            print("No results found.")
        return

    # --click: open a specific result's thread
    if args.click:
        n = args.click
        if n < 1 or n > len(messages):
            print(f"Error: --click {n} out of range (1-{len(messages)}).", file=sys.stderr)
            sys.exit(1)
        scroll_search_to_top(args.cdp)
        click_search_result_link(n, args.cdp)
        thread = read_thread_messages(args.cdp)
        msg = messages[n - 1]
        if args.as_json:
            replies = [{"message_id": ts, "message": txt} for ts, txt in thread.items()]
            print(json.dumps({"clicked": n, "href": msg.get("href", ""), "thread": replies}, ensure_ascii=False))
        else:
            print(f"Clicked result {n}: {msg.get('user', '?')} ({msg.get('time', '?')})")
            for ts, txt in thread.items():
                print(f"\n{txt}")
        return

    results = info.get("results", 0)
    pages = info.get("pages", 0)

    if args.as_json:
        print(json.dumps({"results": results, "pages": pages, "messages": messages},
                         indent=2, ensure_ascii=False))
        return

    print(f"{results:,} results, {pages} pages")
    for i, msg in enumerate(messages, 1):
        text = msg.get("message", "")
        cid = msg.get("channel_id", "")
        ts = msg.get("message_id", "")
        print(f"\n[{i}] {msg.get('user', '?')} ({msg.get('time', '?')})")
        if cid and ts:
            print(f"    id: {cid}/{ts}")
        if len(text) > 200:
            text = text[:200] + "..."
        print(f"    {text}")
    print(f"\n({len(messages)} shown, {results:,} results, {pages} pages)")


if __name__ == "__main__":
    main()
