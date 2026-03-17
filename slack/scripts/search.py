#!/usr/bin/env python3
"""Search Slack messages via the desktop app's CDP interface.

Requires:
  - Slack desktop app running with --remote-debugging-port=9222
  - agent-browser CLI on PATH

Slack search syntax:
  in:#channel       search within a channel
  from:@user        messages from a user
  after:YYYY-MM-DD  messages after a date
  before:YYYY-MM-DD messages before a date
  has:reaction      messages with any reaction
  has:file          messages with attachments

Usage:
  python search.py "deployment failed"
  python search.py "in:#ops-alerts deployment failed"
  python search.py "from:@alice has:file after:2024-01-01"
  python search.py "standup in:#general before:2024-06-01" --limit 5
  python search.py "error has:reaction" --json
  python search.py "query" --page 2
  python search.py "query" --cdp 9333
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time

from slack import ab, ab_eval, decode_ab_json, ensure_clean_state, ensure_slack_cdp, find_ref, parse_slack_url


# Extract structured data from [data-qa="search_result"] elements.
EXTRACT_JS = r"""
(() => {
    const items = document.querySelectorAll('[data-qa="search_result"]');
    const results = [];
    for (const item of items) {
        const userEl = item.querySelector('[data-qa="message_sender_name"]');
        const user = userEl ? userEl.textContent.trim() : '';

        const tsEl = item.querySelector('[data-qa="timestamp_label"]');
        const timeText = tsEl ? tsEl.textContent.trim() : '';

        const archiveLink = item.querySelector('a[href*="/archives/"]');
        const href = archiveLink ? archiveLink.href : '';

        const msgEl = item.querySelector('[data-qa="message-text"]');
        const message = msgEl ? msgEl.innerText.trim() : '';

        results.push({user, time: timeText, href, message});
    }
    return JSON.stringify(results);
})()
"""

# Scroll the search results virtual list down by half a viewport.
# Walks up from a search result to find the scrollable parent.
SCROLL_JS = r"""
(() => {
    const result = document.querySelector('[data-qa="search_result"]');
    if (!result) return '"no_results"';
    let el = result.closest('.c-virtual_list__scroll_container');
    if (!el) el = result.parentElement;
    let scroller = el;
    while (scroller) {
        if (scroller.scrollHeight > scroller.clientHeight + 10) {
            const before = scroller.scrollTop;
            scroller.scrollTop += Math.floor(scroller.clientHeight / 2);
            const atBottom = scroller.scrollTop + scroller.clientHeight >= scroller.scrollHeight - 5;
            return JSON.stringify({scrolled: scroller.scrollTop > before, atBottom});
        }
        scroller = scroller.parentElement;
    }
    return '"no_scroller"';
})()
"""

# Scroll to top of the search results.
SCROLL_TOP_JS = r"""
(() => {
    const result = document.querySelector('[data-qa="search_result"]');
    if (!result) return;
    let el = result.closest('.c-virtual_list__scroll_container');
    if (!el) el = result.parentElement;
    let scroller = el;
    while (scroller) {
        if (scroller.scrollHeight > scroller.clientHeight + 10) {
            scroller.scrollTop = 0;
            return;
        }
        scroller = scroller.parentElement;
    }
})()
"""


PAGE_INFO_JS = r"""
(() => {
    let results = 0;
    const rc = document.querySelector('[class*="resultCounts"]');
    if (rc) {
        const m = rc.textContent.match(/([\d,]+)\s*results?/i);
        if (m) results = parseInt(m[1].replace(/,/g, ''));
    }
    let pages = 0;
    const btns = document.querySelectorAll('[data-qa*="pagination_page_btn"]');
    btns.forEach(b => { const n = parseInt(b.textContent); if (n > pages) pages = n; });
    return JSON.stringify({results, pages});
})()
"""


def goto_page(cdp: int, page: int) -> bool:
    js = f"""
    (() => {{
        const btn = document.querySelector('[data-qa="c-pagination_page_btn_{page}"]');
        if (btn) {{ btn.click(); return '"clicked"'; }}
        const fwd = document.querySelector('[data-qa="c-pagination_forward_btn"]');
        if (fwd && !fwd.classList.contains('c-button--disabled')) {{ fwd.click(); return '"next"'; }}
        return '"not_found"';
    }})()
    """
    raw = ab_eval(js, cdp=cdp)
    status = decode_ab_json(raw)
    if status == "not_found":
        return False
    time.sleep(3)
    if status == "next":
        current = _current_page(cdp)
        if current < page:
            return goto_page(cdp, page)
    return True


def _current_page(cdp: int) -> int:
    js = r"""(() => {
        const active = document.querySelector('[data-qa*="pagination_page_btn"][aria-current="page"]');
        return active ? active.textContent.trim() : '0';
    })()"""
    raw = ab_eval(js, cdp=cdp).strip().strip('"').strip("'")
    try:
        return int(raw)
    except ValueError:
        return 0


def get_page_info(cdp: int) -> dict:
    raw = ab_eval(PAGE_INFO_JS, cdp=cdp)
    info = decode_ab_json(raw)
    if isinstance(info, str):
        info = decode_ab_json(info)
    if not isinstance(info, dict):
        return {"results": 0, "pages": 0}
    return info


def extract_and_scroll(cdp: int, limit: int) -> list[dict]:
    """Scroll through the search results virtual list, collecting all results."""
    seen_hrefs: set[str] = set()
    results: list[dict] = []

    # Scroll to top first
    ab_eval(SCROLL_TOP_JS, cdp=cdp)
    time.sleep(0.5)

    for _ in range(40):
        raw = ab_eval(EXTRACT_JS, cdp=cdp)
        batch = decode_ab_json(raw)
        if isinstance(batch, str):
            batch = decode_ab_json(batch)
        if not isinstance(batch, list):
            break

        new_count = 0
        for r in batch:
            href = r.get("href", "")
            if not href or href in seen_hrefs:
                continue
            seen_hrefs.add(href)
            r.update(parse_slack_url(href))
            results.append(r)
            new_count += 1

        if len(results) >= limit:
            break
        if new_count == 0:
            break

        scroll_raw = ab_eval(SCROLL_JS, cdp=cdp)
        scroll = decode_ab_json(scroll_raw)
        if isinstance(scroll, dict) and scroll.get("atBottom"):
            break
        time.sleep(0.5)

    return results[:limit]


def main() -> None:
    parser = argparse.ArgumentParser(description="Search Slack messages via CDP")
    parser.add_argument("query", help="Search query string")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output as JSON with message IDs")
    parser.add_argument("--limit", type=int, default=20, help="Max results to return (default: 20)")
    parser.add_argument("--page", type=int, default=1, help="Result page to fetch (default: 1)")
    parser.add_argument("--cdp", type=int, default=9222, help="CDP port (default: 9222)")
    args = parser.parse_args()

    ensure_slack_cdp(args.cdp)

    # 1. Ensure clean state then open search via the Search button.
    snapshot = ensure_clean_state(args.cdp)

    # Clear any previous search first so clicking Search opens a fresh combobox.
    clear_btn = find_ref(snapshot, r'button "Clear search"')
    if clear_btn:
        ab("click", f"@{clear_btn}", cdp=args.cdp)
        time.sleep(0.5)
        snapshot = ab("snapshot", "-i", cdp=args.cdp)

    search_btn = find_ref(snapshot, r'button "Search"')
    if not search_btn:
        sys.exit("Error: could not find the Search button.")
    ab("click", f"@{search_btn}", cdp=args.cdp)
    time.sleep(1)

    # 2. Fill query and submit
    snapshot = ab("snapshot", "-i", cdp=args.cdp)
    query_ref = find_ref(snapshot, r'combobox.*Query')
    if not query_ref:
        sys.exit("Error: could not find the search input.")

    ab("fill", f"@{query_ref}", args.query, cdp=args.cdp)
    time.sleep(1)
    snapshot = ab("snapshot", "-i", cdp=args.cdp)
    search_option = find_ref(snapshot, rf'option "Search for: {re.escape(args.query)}"')
    if search_option:
        ab("click", f"@{search_option}", cdp=args.cdp)
    else:
        ab("press", "Enter", cdp=args.cdp)
    time.sleep(3)

    if args.page > 1:
        if not goto_page(args.cdp, args.page):
            sys.exit(f"Error: could not navigate to page {args.page}.")

    info = get_page_info(args.cdp)
    messages = extract_and_scroll(args.cdp, args.limit)

    if not messages:
        print("No results found.")
        return

    results = info.get("results", 0)
    pages = info.get("pages", 0)

    if args.as_json:
        print(json.dumps({
            "results": results,
            "pages": pages,
            "messages": messages,
        }, indent=2, ensure_ascii=False))
        return

    print(f"{results:,} results, {pages} pages")

    for i, msg in enumerate(messages, 1):
        user = msg.get("user", "?")
        date = msg.get("time", "?")
        text = msg.get("message", "")
        cid = msg.get("channel_id", "")
        ts = msg.get("message_id", "")

        print(f"\n[{i}] {user} ({date})")
        if cid and ts:
            print(f"    id: {cid}/{ts}")
        if len(text) > 200:
            text = text[:200] + "..."
        print(f"    {text}")

    print(f"\n({len(messages)} shown, {results:,} results, {pages} pages)")


if __name__ == "__main__":
    main()
