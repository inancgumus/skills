"""Shared helpers for Slack CDP automation scripts.

All scripts in this directory use agent-browser to control the Slack desktop
app via Chrome DevTools Protocol (CDP). This module holds the common utilities
so fixes and improvements only need to happen in one place.
"""

from __future__ import annotations

import datetime
import json
import platform
import re
import shutil
import subprocess
import sys
import time


# ---------------------------------------------------------------------------
# Low-level agent-browser wrappers
# ---------------------------------------------------------------------------

def run(cmd: list[str], timeout: int = 15) -> str:
    """Run a command and return stripped stdout."""
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\nstderr: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def ab(*args: str, cdp: int = 9222) -> str:
    """Shorthand for agent-browser --cdp <port> <args…>."""
    return run(["agent-browser", "--cdp", str(cdp), *args])


def ab_eval(js: str, cdp: int = 9222) -> str:
    """Run JS via agent-browser eval --stdin."""
    result = subprocess.run(
        ["agent-browser", "--cdp", str(cdp), "eval", "--stdin"],
        input=js,
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        raise RuntimeError(f"eval failed: {result.stderr.strip()}")
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# Slack process management
# ---------------------------------------------------------------------------

def check_cdp_connection(cdp: int) -> bool:
    """Return True if we can reach Slack via CDP."""
    try:
        out = ab_eval("window.location.href", cdp=cdp)
        return "slack" in out.lower()
    except (RuntimeError, subprocess.TimeoutExpired):
        return False


def is_slack_running() -> bool:
    system = platform.system()
    if system == "Darwin":
        return subprocess.run(["pgrep", "-x", "Slack"], capture_output=True).returncode == 0
    elif system == "Linux":
        return subprocess.run(["pgrep", "-f", "slack"], capture_output=True).returncode == 0
    elif system == "Windows":
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq slack.exe"], capture_output=True, text=True)
        return "slack.exe" in r.stdout.lower()
    return False


def launch_slack_with_cdp(cdp: int) -> str:
    """Return the platform-specific command to (re)launch Slack with CDP enabled.

    Quits Slack first only if it's already running.
    """
    port = str(cdp)
    system = platform.system()
    running = is_slack_running()

    if system == "Darwin":
        if running:
            return (
                'osascript -e \'tell application "Slack" to quit\' && '
                f"sleep 3 && open -a Slack --args --remote-debugging-port={port}"
            )
        return f"open -a Slack --args --remote-debugging-port={port}"
    elif system == "Linux":
        prefix = f"pkill slack 2>/dev/null; sleep 3; " if running else ""
        return f"{prefix}slack --remote-debugging-port={port} &"
    elif system == "Windows":
        prefix = "taskkill /IM slack.exe /F 2>nul & timeout /t 3 >nul & " if running else ""
        return f'{prefix}start "" "%LOCALAPPDATA%\\slack\\slack.exe" --remote-debugging-port={port}'
    else:
        return f"slack --remote-debugging-port={port} &"


def ensure_slack_cdp(cdp: int = 9222) -> None:
    """Ensure agent-browser is available and Slack is running with CDP."""
    if not shutil.which("agent-browser"):
        sys.exit("Error: agent-browser not found on PATH.")
    if check_cdp_connection(cdp):
        return

    cmd = launch_slack_with_cdp(cdp)
    print(json.dumps({"status": "launching_slack", "command": cmd}), file=sys.stderr)
    subprocess.run(cmd, shell=True, capture_output=True, timeout=15)

    for _ in range(15):
        time.sleep(2)
        if check_cdp_connection(cdp):
            return

    print(json.dumps({
        "error": "cannot_connect",
        "message": f"Slack is not reachable via CDP on port {cdp}. Try manually: {cmd}",
    }), file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Snapshot helpers
# ---------------------------------------------------------------------------

def find_ref(snapshot: str, label_pattern: str) -> str | None:
    """Find the first [ref=eN] whose line matches *label_pattern* (case-insensitive)."""
    for line in snapshot.splitlines():
        if re.search(label_pattern, line, re.IGNORECASE):
            m = re.search(r'\bref=(e\d+)', line)
            if m:
                return m.group(1)
    return None


def find_all_refs(snapshot: str, label_pattern: str) -> list[str]:
    """Find ALL [ref=eN] whose line matches the pattern."""
    refs = []
    for line in snapshot.splitlines():
        if re.search(label_pattern, line, re.IGNORECASE):
            m = re.search(r'\bref=(e\d+)', line)
            if m:
                refs.append(m.group(1))
    return refs


# ---------------------------------------------------------------------------
# Workspace detection
# ---------------------------------------------------------------------------

cached_workspace_domain: str | None = None


def getcached_workspace_domain(cdp: int = 9222) -> str:
    """Auto-detect the Slack workspace domain from the running app.

    Queries the DOM for workspace-specific links (e.g. *.slack.com) and caches
    the result for the lifetime of the process.
    """
    global cached_workspace_domain
    if cached_workspace_domain:
        return cached_workspace_domain

    raw = ab_eval(r"""
(() => {
    const links = document.querySelectorAll('a[href*=".slack.com"]');
    for (const a of links) {
        const m = a.href.match(/https:\/\/([^.]+\.slack\.com)/);
        if (m) return m[1];
    }
    const meta = document.querySelector('meta[name="team-domain"]');
    if (meta) return meta.content + '.slack.com';
    return null;
})()
""", cdp=cdp)

    domain = decode_ab_json(raw)
    if domain and isinstance(domain, str) and ".slack.com" in domain:
        cached_workspace_domain = domain
        return domain

    raise RuntimeError(
        "Could not auto-detect Slack workspace domain. "
        "Make sure the Slack desktop app is running and connected via CDP."
    )


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

def ensure_clean_state(cdp: int) -> str:
    """Dismiss overlays / escape search results so the sidebar is visible.

    Returns a fresh snapshot with the sidebar available.
    """
    snapshot = ab("snapshot", "-i", cdp=cdp)
    if find_ref(snapshot, r'button "New message"'):
        return snapshot  # sidebar already visible

    # Try Escape first (dismisses dialogs), then click Home tab (escapes search results)
    for attempt in ("escape", "home"):
        if attempt == "escape":
            ab("press", "Escape", cdp=cdp)
        else:
            home_ref = find_ref(snapshot, r'tab "Home"')
            if home_ref:
                ab("click", f"@{home_ref}", cdp=cdp)
        time.sleep(1)
        snapshot = ab("snapshot", "-i", cdp=cdp)
        if find_ref(snapshot, r'button "New message"'):
            return snapshot

    return snapshot  # best effort


def navigate_to(target: str, cdp: int) -> bool:
    """Navigate to a channel, DM, or Slack view by name via the search bar."""
    snapshot = ab("snapshot", "-i", cdp=cdp)

    # If the search combobox is already open, use it directly
    input_ref = find_ref(snapshot, r'combobox.*Query')
    if not input_ref:
        # Open search — button may be "Search" or "Clear search" (when already active)
        search_ref = find_ref(snapshot, r'button "Search"') or find_ref(snapshot, r'button "Clear')
        if not search_ref:
            return False
        ab("click", f"@{search_ref}", cdp=cdp)
        time.sleep(1)
        snapshot = ab("snapshot", "-i", cdp=cdp)
        input_ref = find_ref(snapshot, r'combobox.*Query')
    if not input_ref:
        return False

    ab("fill", f"@{input_ref}", target, cdp=cdp)
    time.sleep(1)

    snapshot = ab("snapshot", "-i", cdp=cdp)
    option_ref = find_ref(snapshot, r'option')
    if option_ref:
        ab("click", f"@{option_ref}", cdp=cdp)
    else:
        ab("press", "Enter", cdp=cdp)

    time.sleep(1)
    return True


# ---------------------------------------------------------------------------
# Message ID parsing
# ---------------------------------------------------------------------------

def _resolve_channel_name(name: str, cdp: int) -> str:
    """Look up a channel ID by name from the sidebar. Falls back to navigating to it."""
    # Try sidebar first
    raw = ab_eval(f"""(() => {{
        const items = [...document.querySelectorAll('[data-qa-channel-sidebar-channel-id]')];
        const match = items.find(el => {{
            const n = el.querySelector('[data-qa="channel_sidebar_name"]') || el;
            return n.textContent.trim().toLowerCase() === '{name.lower()}';
        }});
        return match ? JSON.stringify(match.getAttribute('data-qa-channel-sidebar-channel-id')) : 'null';
    }})()""", cdp=cdp)
    cid = decode_ab_json(raw)
    if isinstance(cid, str):
        return cid
    # Fallback: navigate to channel so it appears in sidebar, then retry
    navigate_to(name, cdp)
    time.sleep(1)
    raw = ab_eval(f"""(() => {{
        const items = [...document.querySelectorAll('[data-qa-channel-sidebar-channel-id]')];
        const match = items.find(el => {{
            const n = el.querySelector('[data-qa="channel_sidebar_name"]') || el;
            return n.textContent.trim().toLowerCase() === '{name.lower()}';
        }});
        return match ? JSON.stringify(match.getAttribute('data-qa-channel-sidebar-channel-id')) : 'null';
    }})()""", cdp=cdp)
    cid = decode_ab_json(raw)
    return cid if isinstance(cid, str) else ""


def resolve_ref(ref: str, cdp: int = 9222) -> tuple[str, str]:
    """Resolve any channel/message reference to (channel_id, message_id).

    Accepted formats:
      - Channel ID:    C042WNMBYQM                  → ("C042WNMBYQM", "")
      - Message ref:   C042WNMBYQM/1773432901.662159 → ("C042WNMBYQM", "1773432901.662159")
      - Slack URL:     https://…/archives/C…/p…      → parsed
      - Channel name:  #k6-alert-core-team            → sidebar lookup → ("C042WNMBYQM", "")
      - DM by name:    @Inanc Gumus                   → navigate + read DM channel ID from URL

    Channel names MUST start with # and DMs with @ to avoid ambiguity.
    Raises SystemExit if the reference cannot be resolved.
    """
    ref = ref.strip()

    # Slack permalink URL
    if "archives/" in ref:
        parsed = parse_slack_url(ref)
        cid = parsed.get("channel_id", "")
        mid = parsed.get("message_id", "")
        if not cid:
            sys.exit(f"Error: could not parse channel from URL: {ref}")
        return (cid, mid)

    # DM by display name — must start with @
    if ref.startswith("@"):
        name = ref[1:]
        navigate_to(name, cdp)
        time.sleep(1)
        url = ab_eval("window.location.href", cdp=cdp)
        m = re.search(r'/([A-Z][A-Z0-9]{7,})', url)
        if m:
            return (m.group(1), "")
        sys.exit(f"Error: could not navigate to DM with '{name}'.")

    # Channel name — must start with #
    if ref.startswith("#"):
        name = ref[1:]
        cid = _resolve_channel_name(name, cdp)
        if not cid:
            sys.exit(f"Error: channel '{ref}' not found.")
        return (cid, "")

    # Message ref: CHANNEL_ID/MESSAGE_ID
    if "/" in ref:
        parts = ref.split("/", 1)
        if not parts[0].startswith("C") or len(parts[0]) < 9:
            sys.exit(f"Error: invalid message reference: {ref}")
        return (parts[0], normalize_ts(parts[1]))

    # Bare channel ID
    if ref.startswith("C") and len(ref) >= 9:
        return (ref, "")

    sys.exit(f"Error: '{ref}' is not a valid reference. Channel names must start with #.")


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
    message_ts = raw_ts[:10] + "." + raw_ts[10:] if len(raw_ts) > 10 else raw_ts
    thread_ts = None
    tm = re.search(r'thread_ts=([\d.]+)', href)
    if tm:
        thread_ts = tm.group(1)
    return {"channel_id": channel_id, "message_id": message_ts, "thread_id": thread_ts}


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def decode_ab_json(raw: str):
    """Decode JSON output from agent-browser (may be double-quoted)."""
    try:
        decoded = json.loads(raw)
        if isinstance(decoded, str):
            try:
                return json.loads(decoded)
            except (json.JSONDecodeError, TypeError):
                pass
        return decoded
    except (json.JSONDecodeError, TypeError):
        return raw


# ---------------------------------------------------------------------------
# DOM selectors (stable data-qa attributes)
# ---------------------------------------------------------------------------

DOM = {
    "MESSAGE_PANE": '[data-qa="message_pane"]',
    "MESSAGE": '[data-qa="message_container"]',
    "JUMP_TO_DATE": 'button[aria-label="Jump to date"]',
    "MENU_ITEM": '[role="menuitem"]',
    "CAL": "[aria-label='Date picker']",
    "CAL_TITLE": '[data-qa="cal_header_title"]',
    "CAL_PREV_YEAR": '[data-qa="cal_header_previous_year_btn"]',
    "CAL_NEXT_YEAR": '[data-qa="cal_header_next_year_btn"]',
    "CAL_PREV_MONTH": '[data-qa="cal_header_previous_month_btn"]',
    "CAL_NEXT_MONTH": '[data-qa="cal_header_next_month_btn"]',
}


# ---------------------------------------------------------------------------
# Channel & date navigation
# ---------------------------------------------------------------------------


def get_channel_name(channel_id: str, cdp: int = 9222) -> str:
    """Get the display name of a channel from its sidebar item."""
    raw = ab_eval(f"""(() => {{
        const item = document.querySelector('[data-qa-channel-sidebar-channel-id="{channel_id}"]');
        if (!item) return 'null';
        const nameEl = item.querySelector('[data-qa="channel_sidebar_name"]') || item;
        return JSON.stringify(nameEl.textContent.trim().split('\\n')[0].trim());
    }})()""", cdp=cdp)
    name = decode_ab_json(raw)
    return name if isinstance(name, str) else ""


#
# ---------------------------------------------------------------------------

def go_to_channel(name_or_id: str, cdp: int = 9222) -> bool:
    """Navigate to a channel by name or ID. Tries sidebar first, falls back to search.

    Skips navigation if already on the target channel.
    """
    # Check if already on this channel
    current = ab_eval("window.location.href", cdp=cdp)
    if name_or_id in current:
        return True

    # Try sidebar by channel ID attribute (for IDs like C0123456789)
    if name_or_id.startswith("C") and len(name_or_id) >= 9:
        found = ab_eval(f"""(() => {{
            const item = document.querySelector('[data-qa-channel-sidebar-channel-id="{name_or_id}"]')
                      || [...document.querySelectorAll('[role="treeitem"]')].find(el => el.textContent?.includes('{name_or_id}'));
            if (item) {{ item.click(); return 'ok'; }}
            return 'not_found';
        }})()""", cdp=cdp)
        if "ok" in found:
            time.sleep(1)
            return True

    # Try sidebar by name
    found = ab_eval(f"""(() => {{
        const item = [...document.querySelectorAll('[role="treeitem"]')]
            .find(el => el.textContent?.includes('{name_or_id}'));
        if (item) {{ item.click(); return 'ok'; }}
        return 'not_found';
    }})()""", cdp=cdp)
    if "ok" in found:
        time.sleep(1)
        return True

    # Fall back to search bar
    return navigate_to(name_or_id, cdp)


def jump_to_date(year: int, month: int, day: int, cdp: int = 9222) -> bool:
    """Jump to a specific date using the calendar picker.

    Uses data-qa selectors for reliable calendar navigation.
    Returns False if not in a channel view (no Jump to date button available).
    """
    date_str = f"{year}-{month:02d}-{day:02d}"

    # Dismiss overlays
    for _ in range(3):
        ab("press", "Escape", cdp=cdp)
    time.sleep(0.3)

    # Open date picker menu, click last item ("Jump to a specific date")
    raw = ab_eval(f"""(async () => {{
        const btn = document.querySelector('{DOM["JUMP_TO_DATE"]}');
        if (!btn) return 'no_button';
        btn.click();
        await new Promise(r => setTimeout(r, 500));
        const items = document.querySelectorAll('{DOM["MENU_ITEM"]}');
        if (!items.length) return 'no_menu';
        items[items.length - 1].click();
        await new Promise(r => setTimeout(r, 500));
        return 'ok';
    }})()""", cdp=cdp)
    if "no_button" in raw or "no_menu" in raw:
        return False
    time.sleep(0.5)

    # Navigate calendar year/month, then click the day
    ab_eval(f"""(async () => {{
        const cal = document.querySelector("{DOM['CAL']}");
        if (!cal) return;
        const readTitle = () => document.querySelector('{DOM["CAL_TITLE"]}')?.innerText || '';
        const getYear = () => Number(readTitle().split(' ').pop());
        const getMonth = () => new Date(readTitle() + ' 1').getMonth();
        while (getYear() > {year}) {{
            document.querySelector('{DOM["CAL_PREV_YEAR"]}')?.click();
            await new Promise(r => setTimeout(r, 100));
        }}
        while (getYear() < {year}) {{
            document.querySelector('{DOM["CAL_NEXT_YEAR"]}')?.click();
            await new Promise(r => setTimeout(r, 100));
        }}
        while (getMonth() > {month - 1}) {{
            document.querySelector('{DOM["CAL_PREV_MONTH"]}')?.click();
            await new Promise(r => setTimeout(r, 100));
        }}
        while (getMonth() < {month - 1}) {{
            document.querySelector('{DOM["CAL_NEXT_MONTH"]}')?.click();
            await new Promise(r => setTimeout(r, 100));
        }}
        const dayBtn = document.querySelector('[data-qa-date="{date_str}"]');
        if (dayBtn) dayBtn.click();
    }})()""", cdp=cdp)
    time.sleep(1.5)
    return True


# ---------------------------------------------------------------------------
# Message collection & scrolling
# ---------------------------------------------------------------------------

def normalize_ts(ts: str) -> str:
    """Convert any Slack timestamp format to the data-msg-ts format (e.g. 1773418516.710389).

    Handles: '1773418516.710389', 'p1773418516710389', '1773418516710389'
    """
    ts = ts.lstrip("p")
    if "." not in ts and len(ts) > 10:
        ts = ts[:10] + "." + ts[10:]
    return ts


def scroll_to_message(msg_ts: str, cdp: int = 9222) -> bool:
    """Scroll a specific message into the center of the viewport.

    Returns True if the message was found and scrolled to.
    Falls back to jump_to_date when navigating to a channel only loads recent
    messages and the target is not in the current DOM.
    """
    msg_ts = normalize_ts(msg_ts)

    def find_in_dom() -> bool:
        raw = ab_eval(f"""(() => {{
            const msg = [...document.querySelectorAll('{DOM["MESSAGE"]}')]
                .find(el => el.dataset.msgTs === '{msg_ts}');
            if (!msg) return '"not_found"';
            msg.scrollIntoView({{block: 'center'}});
            return '"ok"';
        }})()""", cdp=cdp)
        return "not_found" not in raw

    if find_in_dom():
        time.sleep(0.5)
        return True

    # Message not in current viewport — ensure we're in channel view, then jump to date
    ensure_clean_state(cdp)
    dt = datetime.datetime.fromtimestamp(float(msg_ts.split(".")[0]))
    if not jump_to_date(dt.year, dt.month, dt.day, cdp):
        return False
    if find_in_dom():
        time.sleep(0.5)
        return True

    return False


# ---------------------------------------------------------------------------
# Message actions (emoji, thread reply)
# ---------------------------------------------------------------------------

def find_ts_ref(msg_ts: str, snapshot: str, cdp: int) -> str | None:
    """Find the snapshot ref for a message's timestamp link."""
    labels_raw = ab_eval(f"""(() => {{
        const msg = [...document.querySelectorAll('{DOM["MESSAGE"]}')]
            .find(el => el.dataset.msgTs === '{msg_ts}');
        if (!msg) return '[]';
        const links = msg.querySelectorAll('a[aria-label]');
        return JSON.stringify(Array.from(links).map(a => a.getAttribute('aria-label'))
            .filter(l => /\\d{{1,2}}:\\d{{2}}/.test(l)));
    }})()""", cdp=cdp)
    labels = decode_ab_json(labels_raw)
    if not labels:
        return None
    escaped = re.escape(labels[0])
    return find_ref(snapshot, rf'link "{escaped}"')


def find_ref_after(snapshot: str, anchor_ref: str, pattern: str) -> str | None:
    """Find the first ref matching pattern that appears after anchor_ref in the snapshot."""
    found_anchor = False
    for line in snapshot.splitlines():
        if f"[ref={anchor_ref}]" in line:
            found_anchor = True
        if found_anchor and re.search(pattern, line, re.IGNORECASE):
            m = re.search(r'\bref=(e\d+)', line)
            if m:
                return m.group(1)
    return None


def add_emoji(msg_ts: str, emoji: str, cdp: int = 9222) -> bool:
    """Add an emoji reaction to a message by its timestamp.

    Scrolls to the message, hovers its timestamp link to reveal the toolbar,
    clicks "Add reaction", searches for the emoji, and selects it.
    Accepts any timestamp format (raw, permalink, or with p-prefix).
    """
    msg_ts = normalize_ts(msg_ts)
    if not scroll_to_message(msg_ts, cdp):
        return False

    snapshot = ab("snapshot", "-i", cdp=cdp)
    ts_ref = find_ts_ref(msg_ts, snapshot, cdp)
    if not ts_ref:
        return False

    # Hover timestamp to reveal toolbar
    ab("hover", f"@{ts_ref}", cdp=cdp)
    time.sleep(0.3)

    # Find "Add reaction" after the timestamp ref
    snapshot = ab("snapshot", "-i", cdp=cdp)
    add_ref = find_ref_after(snapshot, ts_ref, r'Add reaction')
    if not add_ref:
        return False

    # Open emoji picker, search, select
    ab("click", f"@{add_ref}", cdp=cdp)
    time.sleep(0.8)
    snapshot = ab("snapshot", "-i", cdp=cdp)
    search_ref = find_ref(snapshot, r'(textbox|combobox).*(search|find|emoji)')
    if not search_ref:
        search_ref = find_ref(snapshot, r'(textbox|combobox)')
    if not search_ref:
        return False
    ab("fill", f"@{search_ref}", emoji, cdp=cdp)
    time.sleep(0.8)
    ab("press", "Enter", cdp=cdp)
    time.sleep(0.3)
    return True


def open_thread(msg_ts: str, cdp: int = 9222) -> bool:
    """Open the thread panel for a message.

    Scrolls to the message and clicks the "X replies" / "Reply to thread"
    button in the reply bar via JS (same approach as go_to_channel sidebar
    navigation). Returns True if a thread button was found and clicked.
    """
    msg_ts = normalize_ts(msg_ts)
    if not scroll_to_message(msg_ts, cdp):
        return False

    raw = ab_eval(f"""(() => {{
        const msg = [...document.querySelectorAll('{DOM["MESSAGE"]}')]
            .find(el => el.dataset.msgTs === '{msg_ts}');
        if (!msg) return '"not_found"';
        const btn = msg.querySelector('[data-qa="reply_bar_view_thread"]') ||
                    msg.querySelector('[data-qa="start_thread"]');
        if (!btn) return '"no_button"';
        btn.click();
        return '"clicked"';
    }})()""", cdp=cdp)
    result = decode_ab_json(raw)
    if result != "clicked":
        return False

    time.sleep(1)
    return True


def close_thread(cdp: int = 9222) -> None:
    """Close the thread panel if open."""
    snapshot = ab("snapshot", "-i", cdp=cdp)
    close_ref = find_ref(snapshot, r'button "Close"')
    if close_ref:
        ab("click", f"@{close_ref}", cdp=cdp)
        time.sleep(0.5)


def get_thread_reply_ids(cdp: int = 9222) -> list[str]:
    """Read reply message timestamps from the open thread panel.

    Returns a list of message_ts strings (excluding the parent message).
    The thread panel must already be open (via open_thread).
    """
    raw = ab_eval(r"""(() => {
        const panel = document.querySelector('.p-flexpane, [data-qa="thread_view"]');
        if (!panel) return '[]';
        const msgs = [...panel.querySelectorAll('[data-qa="message_container"]')];
        return JSON.stringify(msgs.map(m => m.dataset.msgTs).filter(Boolean));
    })()""", cdp=cdp)
    all_ts = decode_ab_json(raw)
    if not isinstance(all_ts, list) or len(all_ts) < 2:
        return []
    # First message is the parent; the rest are replies
    return all_ts[1:]


def find_thread_parent(target_ts: str, cdp: int) -> str | None:
    """Find the parent message ts whose thread contains target_ts.

    Thread replies don't appear in the channel view DOM. We identify the parent
    by finding the message whose reply-bar last-reply timestamp is the tightest
    upper bound on target_ts: i.e. last_reply >= target, minimizing
    (last_reply - target). This avoids false positives from long-running threads
    whose last reply happens to be after the target but whose replies are all later.
    """
    raw = ab_eval(f"""(() => {{
        const target = parseFloat('{target_ts}');
        const msgs = [...document.querySelectorAll('{DOM["MESSAGE"]}')];
        let best = null, bestGap = Infinity;
        for (const msg of msgs) {{
            const msgTs = parseFloat(msg.dataset.msgTs || '0');
            if (msgTs >= target) continue;
            const bar = msg.querySelector('[data-qa="reply_bar_last_reply"]');
            if (!bar) continue;
            const lastReply = parseFloat(bar.dataset.ts || '0');
            if (lastReply >= target) {{
                const gap = lastReply - target;
                if (gap < bestGap) {{ bestGap = gap; best = msg.dataset.msgTs; }}
            }}
        }}
        return best ? JSON.stringify(best) : 'null';
    }})()""", cdp=cdp)
    parent_ts = decode_ab_json(raw)
    return parent_ts if isinstance(parent_ts, str) else None


EXTRACT_MSG_JS = """(msgTs, sel) => {
    const msg = [...document.querySelectorAll(sel)].find(el => el.dataset.msgTs === msgTs);
    if (!msg) return null;
    const userEl = msg.querySelector('[data-qa="message_sender_name"]');
    const user = userEl ? userEl.textContent.trim() : '';
    const dateEl = msg.querySelector('[data-qa="timestamp_label"]');
    const dateLabel = dateEl ? dateEl.textContent.trim() : '';
    const msgEl = msg.querySelector('[data-qa="message-text"]');
    const message = msgEl ? msgEl.innerText.trim() : '';
    // For each reactji in this message, find its global index among all same-emoji reactjis.
    // This lets the caller pick the right nth match from the accessibility snapshot.
    const allReactjis = [...document.querySelectorAll('[data-qa="reactji"]')];
    const reactions = [...msg.querySelectorAll('[data-qa="reactji"]')].map(r => {
        const emojiEl = r.querySelector('[data-stringify-emoji]');
        const emoji = emojiEl ? emojiEl.getAttribute('data-stringify-emoji').replace(/:/g, '') : '';
        const sameEmoji = allReactjis.filter(el => {
            const e = el.querySelector('[data-stringify-emoji]');
            return e && e.getAttribute('data-stringify-emoji').replace(/:/g, '') === emoji;
        });
        return {emoji, idx: sameEmoji.indexOf(r)};
    }).filter(r => r.emoji);
    return {user, dateLabel, message, reactions};
}"""


def parse_reaction_tooltip(tip_text: str, emoji: str) -> list[str]:
    """Parse usernames from a Slack reaction tooltip.

    Handles two formats:
      - Combined: "User1, User2, and User3 reacted with :emoji:"
      - Per-user:  "User1 reacted with :emoji:User2 reacted with :emoji::skin-tone-N:"
        (when users reacted with emoji variants like skin tones)
    """
    if not tip_text:
        return []
    # Split on each "reacted with :...(optional skin-tone):" occurrence
    parts = re.split(r"\s+reacted with\s+:[^:]+:(?::[^:]+:)*", tip_text)
    parts = [p.strip() for p in parts if p.strip()]
    names: list[str] = []
    for part in parts:
        # Remove leading "and " (last item in "User1, User2, and User3" list)
        cleaned = re.sub(r"^\s*and\s+", "", part).strip()
        for name in re.split(r",\s*(?:and\s+)?", cleaned):
            name = name.strip()
            if name:
                names.append(name)
    return names


def read_reaction_users(reactions: list[dict], cdp: int) -> list[dict]:
    """For each reaction, hover the correct reactji button and read the .c-reaction__tip tooltip.

    Uses snapshot -i -C to find cursor-interactive reactji buttons (tabindex=-1).
    Each reaction has {emoji, idx} where idx is the global nth-index of that emoji's button,
    ensuring the right button is targeted even when multiple messages share the same emoji.
    Emoji names with hyphens (e.g. christmas-parrot) match either hyphen or space in aria-labels.
    """
    if not reactions:
        return []
    snapshot = ab("snapshot", "-i", "-C", cdp=cdp)
    results = []
    for r in reactions:
        emoji = r["emoji"]
        idx = r.get("idx", 0)
        # Slack aria-labels may use space instead of hyphen (christmas-parrot → christmas parrot)
        pattern = rf"react with {re.escape(emoji).replace(r'\-', r'[\s\-]')} emoji"
        refs = find_all_refs(snapshot, pattern)
        if idx >= len(refs):
            continue
        ab("hover", f"@{refs[idx]}", cdp=cdp)
        time.sleep(0.3)
        raw = ab_eval("""(() => {
            const tip = document.querySelector('[class*="c-reaction__tip"]');
            return tip ? JSON.stringify(tip.textContent.trim()) : 'null';
        })()""", cdp=cdp)
        tip_text = decode_ab_json(raw)
        if not isinstance(tip_text, str):
            continue
        for name in parse_reaction_tooltip(tip_text, emoji):
            results.append({"user": name, "emoji": emoji})
    return results


def extract_msg(msg_ts: str, cdp: int) -> dict | None:
    """Extract structured message data from the current DOM."""
    raw = ab_eval(
        f"({EXTRACT_MSG_JS})('{msg_ts}', '{DOM['MESSAGE']}')",
        cdp=cdp,
    )
    data = decode_ab_json(raw)
    if not isinstance(data, dict):
        return None
    data["reactions"] = read_reaction_users(data.get("reactions", []), cdp)
    return data


def read_message_content(msg_ts: str, cdp: int = 9222) -> dict | None:
    """Read structured message data (author, date, text, reactions) by timestamp.

    Tries the channel view first (with a jump-to-date fallback for old messages).
    If still not found, assumes it's a thread reply and opens the parent thread.
    Returns None if the message cannot be located.
    """
    msg_ts = normalize_ts(msg_ts)

    if scroll_to_message(msg_ts, cdp):
        return extract_msg(msg_ts, cdp)

    # Not in channel view — may be a thread reply
    parent_ts = find_thread_parent(msg_ts, cdp)
    if not parent_ts or not open_thread(parent_ts, cdp):
        return None
    data = extract_msg(msg_ts, cdp)
    close_thread(cdp)
    return data


def read_thread_messages(cdp: int = 9222) -> dict[str, str]:
    """Read all message content from the open thread panel.

    Scrolls through the virtual list to load all messages.
    Returns {message_ts: content} for every message in the thread
    (including the parent). The thread panel must already be open.
    """
    COLLECT_JS = r"""(() => {
        const panel = document.querySelector('.p-flexpane, [data-qa="thread_view"]');
        if (!panel) return '{}';
        const msgs = [...panel.querySelectorAll('[data-qa="message_container"]')];
        const result = {};
        for (const m of msgs) {
            const ts = m.dataset.msgTs;
            if (ts) result[ts] = m.innerText.trim();
        }
        return JSON.stringify(result);
    })()"""

    SCROLL_JS = r"""(() => {
        const panel = document.querySelector('.p-flexpane, [data-qa="thread_view"]');
        if (!panel) return false;
        const msgs = panel.querySelectorAll('[data-qa="message_container"]');
        if (!msgs.length) return false;
        msgs[msgs.length - 1].scrollIntoView({block: 'start'});
        return true;
    })()"""

    all_msgs: dict[str, str] = {}
    for _ in range(60):
        raw = ab_eval(COLLECT_JS, cdp=cdp)
        batch = decode_ab_json(raw)
        if not isinstance(batch, dict):
            break
        before = len(all_msgs)
        all_msgs.update(batch)
        if len(all_msgs) == before:
            break
        ab_eval(SCROLL_JS, cdp=cdp)
        time.sleep(0.5)

    return all_msgs


def reply_in_thread(msg_ts: str, text: str, cdp: int = 9222) -> bool:
    """Post a thread reply to a message by its timestamp.

    Scrolls to the message, opens its thread, fills the reply box, and sends.
    Accepts any timestamp format (raw, permalink, or with p-prefix).
    """
    if not open_thread(msg_ts, cdp):
        return False

    snapshot = ab("snapshot", "-i", cdp=cdp)
    reply_box = find_ref(snapshot, r'textbox.*Reply')
    if not reply_box:
        reply_box = find_ref(snapshot, r'textbox.*Message')
    if not reply_box:
        return False

    ab("fill", f"@{reply_box}", text, cdp=cdp)
    time.sleep(0.5)

    snapshot = ab("snapshot", "-i", cdp=cdp)
    send_ref = find_ref_after(snapshot, reply_box, r'button "Send now"')
    if not send_ref:
        all_sends = find_all_refs(snapshot, r'button "Send now"')
        send_ref = all_sends[-1] if all_sends else None
    if not send_ref:
        return False
    ab("click", f"@{send_ref}", cdp=cdp)
    time.sleep(1)

    close_thread(cdp)
    return True
