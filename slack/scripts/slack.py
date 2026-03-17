"""All Slack-specific functionality lives here: CDP, agent-browser, DOM, selectors,
snapshots, navigation, parsing. Scripts are pure workflow — they call these
primitives and never import or use any Slack-specific internals.
New Slack capability? Add a primitive here. New workflow? Add a script.
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


def _open_search_bar(cdp: int) -> str | None:
    """Open the Slack search bar and return the combobox ref.

    Handles both fresh open (via Search button) and already-open states.
    """
    snapshot = ab("snapshot", "-i", cdp=cdp)
    input_ref = find_ref(snapshot, r'combobox')
    if input_ref:
        return input_ref

    search_ref = find_ref(snapshot, r'button "Search"') or find_ref(snapshot, r'button "Clear')
    if not search_ref:
        return None
    ab("click", f"@{search_ref}", cdp=cdp)
    time.sleep(1)
    snapshot = ab("snapshot", "-i", cdp=cdp)
    return find_ref(snapshot, r'combobox')


def navigate_to(target: str, cdp: int) -> bool:
    """Navigate to a channel, DM, or view via the Slack search bar.

    Opens the search bar, types the target, and picks the first non-search
    option from the dropdown (i.e. the channel/DM/view, not "Search for: …").
    """
    ab("press", "Escape", cdp=cdp)
    time.sleep(0.3)

    input_ref = _open_search_bar(cdp)
    if not input_ref:
        return False

    ab("fill", f"@{input_ref}", target, cdp=cdp)
    time.sleep(1)

    snapshot = ab("snapshot", "-i", cdp=cdp)
    # Pick the first channel/DM option, skipping "Search for:" options
    for line in snapshot.splitlines():
        if re.search(r'option', line, re.IGNORECASE) and 'Search for:' not in line:
            m = re.search(r'\bref=(e\d+)', line)
            if m:
                ab("click", f"@{m.group(1)}", cdp=cdp)
                time.sleep(1)
                return True
    return False


# ---------------------------------------------------------------------------
# Message ID parsing
# ---------------------------------------------------------------------------

def _resolve_channel_name(name: str, cdp: int) -> str:
    """Look up a channel ID by name from the sidebar, or navigate and read from URL."""
    ensure_clean_state(cdp)
    # Try sidebar first (fast path)
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
    # Fallback: navigate to channel and extract ID from URL
    if not navigate_to(name, cdp):
        return ""
    url = ab_eval("window.location.href", cdp=cdp)
    m = re.search(r'/([A-Z][A-Z0-9]{7,})', url)
    return m.group(1) if m else ""


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

    SCROLL_DOWN_JS = r"""(() => {
        const panel = document.querySelector('.p-flexpane, [data-qa="thread_view"]');
        if (!panel) return false;
        const msgs = panel.querySelectorAll('[data-qa="message_container"]');
        if (!msgs.length) return false;
        msgs[msgs.length - 1].scrollIntoView({block: 'start'});
        return true;
    })()"""

    SCROLL_UP_JS = r"""(() => {
        const panel = document.querySelector('.p-flexpane, [data-qa="thread_view"]');
        if (!panel) return false;
        const msgs = panel.querySelectorAll('[data-qa="message_container"]');
        if (!msgs.length) return false;
        msgs[0].scrollIntoView({block: 'end'});
        return true;
    })()"""

    def _collect_and_scroll(scroll_js: str) -> dict[str, str]:
        msgs: dict[str, str] = {}
        for _ in range(60):
            raw = ab_eval(COLLECT_JS, cdp=cdp)
            batch = decode_ab_json(raw)
            if not isinstance(batch, dict):
                break
            before = len(msgs)
            msgs.update(batch)
            if len(msgs) == before:
                break
            ab_eval(scroll_js, cdp=cdp)
            time.sleep(0.5)
        return msgs

    # Scroll up first to reach the beginning, then down to the end
    all_msgs = _collect_and_scroll(SCROLL_UP_JS)
    all_msgs.update(_collect_and_scroll(SCROLL_DOWN_JS))
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


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def ts_to_iso(ts: str) -> str:
    """Convert a Slack message timestamp to ISO 8601 UTC string."""
    dt = datetime.datetime.fromtimestamp(float(ts.split(".")[0]), datetime.timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Search primitives
# ---------------------------------------------------------------------------

_SEARCH_EXTRACT_JS = r"""
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

_SEARCH_SCROLL_JS = r"""
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

_SEARCH_SCROLL_TOP_JS = r"""
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

_SEARCH_PAGE_INFO_JS = r"""
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


def get_search_state(cdp: int = 9222) -> tuple[str, int]:
    """Return (query, current_page) if Slack is showing search results, else ('', 0)."""
    js = r"""(() => {
        const btns = [...document.querySelectorAll('button')];
        const sb = btns.find(b => /^Search:\s/.test(b.textContent.trim()));
        if (!sb) return JSON.stringify({q: '', p: 0});
        const q = sb.textContent.trim().replace(/^Search:\s*/, '');
        if (!document.querySelectorAll('[data-qa="search_result"]').length)
            return JSON.stringify({q: '', p: 0});
        const active = document.querySelector('[data-qa*="pagination_page_btn"][aria-current="page"]');
        const p = active ? parseInt(active.textContent.trim()) : 1;
        return JSON.stringify({q, p});
    })()"""
    raw = ab_eval(js, cdp=cdp)
    state = decode_ab_json(raw)
    if not isinstance(state, dict):
        return ("", 0)
    return (state.get("q", ""), state.get("p", 0))


def execute_search(query: str, cdp: int = 9222) -> None:
    """Open search bar, type query, click 'Search for:' option to trigger message search."""
    ensure_clean_state(cdp)

    query_ref = _open_search_bar(cdp)
    if not query_ref:
        sys.exit("Error: could not find the search input.")

    ab("fill", f"@{query_ref}", query, cdp=cdp)
    time.sleep(1)
    snapshot = ab("snapshot", "-i", cdp=cdp)

    search_option = find_ref(snapshot, r'option "Search for:')
    if not search_option:
        sys.exit("Error: 'Search for:' option not found in dropdown.")
    ab("click", f"@{search_option}", cdp=cdp)
    time.sleep(3)


def goto_search_page(page: int, cdp: int = 9222) -> bool:
    """Navigate to a specific search results pagination page."""
    def _current() -> int:
        js = r"""(() => {
            const active = document.querySelector('[data-qa*="pagination_page_btn"][aria-current="page"]');
            return active ? active.textContent.trim() : '0';
        })()"""
        raw = ab_eval(js, cdp=cdp).strip().strip('"').strip("'")
        try:
            return int(raw)
        except ValueError:
            return 0

    for _ in range(15):
        js = f"""(() => {{
            const btn = document.querySelector('[data-qa="c-pagination_page_btn_{page}"]');
            if (btn) {{ btn.click(); return '"clicked"'; }}
            return '"not_visible"';
        }})()"""
        if decode_ab_json(ab_eval(js, cdp=cdp)) == "clicked":
            time.sleep(3)
            return True

        current = _current()
        if current == page:
            return True
        if current == 0:
            return False

        btn_qa = "c-pagination_forward_btn" if page > current else "c-pagination_back_btn"
        js = f"""(() => {{
            const btn = document.querySelector('[data-qa="{btn_qa}"]');
            if (btn && !btn.classList.contains('c-button--disabled')) {{
                btn.click(); return '"ok"';
            }}
            return '"blocked"';
        }})()"""
        if decode_ab_json(ab_eval(js, cdp=cdp)) == "blocked":
            return False
        time.sleep(3)

    return False


def get_search_page_info(cdp: int = 9222) -> dict:
    """Return {results: int, pages: int} for the current search."""
    raw = ab_eval(_SEARCH_PAGE_INFO_JS, cdp=cdp)
    info = decode_ab_json(raw)
    if isinstance(info, str):
        info = decode_ab_json(info)
    if not isinstance(info, dict):
        return {"results": 0, "pages": 0}
    return info


def extract_visible_search_results(cdp: int = 9222) -> list[dict]:
    """Read currently visible search results from the DOM.

    Returns list of {user, time, href, message, channel_id, message_id, thread_id}.
    """
    raw = ab_eval(_SEARCH_EXTRACT_JS, cdp=cdp)
    batch = decode_ab_json(raw)
    if isinstance(batch, str):
        batch = decode_ab_json(batch)
    if not isinstance(batch, list):
        return []
    for r in batch:
        href = r.get("href", "")
        if href:
            r.update(parse_slack_url(href))
    return batch


def scroll_search_down(cdp: int = 9222) -> dict:
    """Scroll the search results list down. Returns {scrolled: bool, atBottom: bool}."""
    raw = ab_eval(_SEARCH_SCROLL_JS, cdp=cdp)
    result = decode_ab_json(raw)
    if isinstance(result, dict):
        return result
    return {"scrolled": False, "atBottom": True}


def scroll_search_to_top(cdp: int = 9222) -> None:
    """Scroll search results to the top."""
    ab_eval(_SEARCH_SCROLL_TOP_JS, cdp=cdp)
    time.sleep(0.5)


def click_search_result_link(n: int, cdp: int = 9222) -> None:
    """Click the Nth search result's archive link (1-based). Opens the message."""
    js = f"""(() => {{
        const items = document.querySelectorAll('[data-qa="search_result"]');
        const item = items[{n - 1}];
        if (!item) return '"not_found"';
        const link = item.querySelector('a[href*="/archives/"]');
        if (link) {{ link.click(); return '"clicked"'; }}
        return '"no_link"';
    }})()"""
    ab_eval(js, cdp=cdp)
    time.sleep(2)


# ---------------------------------------------------------------------------
# Message collection primitives
# ---------------------------------------------------------------------------

def collect_visible_message_ts(cdp: int = 9222) -> list[str]:
    """Read message timestamps from the current channel view DOM."""
    js = f"""(() => {{
        const msgs = [...document.querySelectorAll('{DOM["MESSAGE"]}')];
        return JSON.stringify(msgs.map(m => m.dataset.msgTs).filter(Boolean));
    }})()"""
    raw = ab_eval(js, cdp=cdp)
    result = decode_ab_json(raw)
    return result if isinstance(result, list) else []


def scroll_channel_down(cdp: int = 9222) -> None:
    """Scroll the channel message pane down by one viewport."""
    js = f"""(() => {{
        const msgs = document.querySelectorAll('{DOM["MESSAGE"]}');
        if (!msgs.length) return false;
        msgs[msgs.length - 1].scrollIntoView({{block: 'start'}});
        return true;
    }})()"""
    ab_eval(js, cdp=cdp)
    time.sleep(0.5)


# ---------------------------------------------------------------------------
# Channel messaging
# ---------------------------------------------------------------------------

def send_channel_message(target: str, text: str, cdp: int = 9222) -> bool:
    """Send a message to a channel (not a thread). Returns True if sent."""
    ensure_clean_state(cdp)
    if not navigate_to(target, cdp):
        return False

    def _find_msg_box() -> str | None:
        snapshot = ab("snapshot", "-i", cdp=cdp)
        for line in snapshot.splitlines():
            if re.search(r'textbox "Message', line, re.IGNORECASE):
                m = re.search(r'\[ref=(e\d+)\]', line)
                if m:
                    return m.group(1)
        return None

    msg_ref = _find_msg_box()
    if not msg_ref:
        time.sleep(1)
        msg_ref = _find_msg_box()
    if not msg_ref:
        return False

    ab("fill", f"@{msg_ref}", text, cdp=cdp)

    snapshot = ab("snapshot", "-i", cdp=cdp)
    send_ref = find_ref(snapshot, r'button "Send now"')
    if send_ref:
        ab("click", f"@{send_ref}", cdp=cdp)
    else:
        ab("click", f"@{msg_ref}", cdp=cdp)
        time.sleep(0.3)
        ab("press", "Enter", cdp=cdp)
    time.sleep(1)
    return True


# ---------------------------------------------------------------------------
# Unreads primitives
# ---------------------------------------------------------------------------

def go_to_unreads(cdp: int = 9222) -> bool:
    """Navigate to the Unreads view via the sidebar."""
    snapshot = ensure_clean_state(cdp)

    ref = find_ref(snapshot, r'treeitem "Unreads')
    if not ref:
        more_ref = find_ref(snapshot, r'button "More unreads"')
        if more_ref:
            ab("click", f"@{more_ref}", cdp=cdp)
            time.sleep(1)
            snapshot = ab("snapshot", "-i", cdp=cdp)
            ref = find_ref(snapshot, r'treeitem "Unreads')

    if not ref:
        return False
    ab("click", f"@{ref}", cdp=cdp)
    time.sleep(2)
    return True


def extract_unreads_text(cdp: int = 9222) -> str:
    """Read the raw text content of the Unreads view."""
    js = r"""(() => {
        const el = document.querySelector('.p-unreads_view')
                || document.querySelector('[data-qa="unreads_view"]')
                || document.querySelector('.p-workspace__primary_view')
                || document.querySelector('[role="main"]');
        return el ? el.innerText : '';
    })()"""
    raw = ab_eval(js, cdp=cdp)
    result = decode_ab_json(raw)
    return result if isinstance(result, str) else ""


def parse_unreads(text: str) -> list[dict]:
    """Parse the raw innerText of the unreads view into structured messages."""
    messages: list[dict] = []
    current_channel = None
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if not line or line in (
            "Mark as Read",
            "Mark All Messages Read",
            "Press Esc to Mark as Read",
        ):
            i += 1
            continue

        if i + 1 < len(lines) and re.match(r'^\d+ messages?$', lines[i + 1].strip()):
            current_channel = line
            i += 2
            continue

        if i + 1 < len(lines) and re.match(r'^\d{1,2}:\d{2}$', lines[i + 1].strip()):
            user = line
            timestamp = lines[i + 1].strip()
            i += 2
            body_lines: list[str] = []
            while i < len(lines):
                peek = lines[i].strip()
                if not peek or peek in ("Mark as Read", "Press Esc to Mark as Read"):
                    i += 1
                    continue
                if (i + 1 < len(lines)
                        and re.match(r'^\d{1,2}:\d{2}$', lines[i + 1].strip())):
                    break
                if (i + 1 < len(lines)
                        and re.match(r'^\d+ messages?$', lines[i + 1].strip())):
                    break
                if peek == "Mark All Messages Read":
                    break
                body_lines.append(peek)
                i += 1
            messages.append({
                "channel": current_channel,
                "user": user,
                "time": timestamp,
                "message": "\n".join(body_lines) if body_lines else "(no text / attachment)",
            })
            continue

        i += 1

    return messages


# ---------------------------------------------------------------------------
# Later primitives
# ---------------------------------------------------------------------------

LATER_STATUS_RE = re.compile(
    r'^(Overdue by .+|Due in .+|Due today|No due date|Completed .+|Archived .+)',
    re.IGNORECASE,
)


def parse_saved_item(lines: list[str]) -> dict:
    """Parse text lines from a single .p-saved_item element."""
    lines = [ln for ln in lines
             if ln not in ("•", "Mark complete", "Edit reminder", "More actions")]

    i = 0
    status = ""
    if lines and LATER_STATUS_RE.match(lines[0]):
        status = lines[0]
        i = 1

    channel = lines[i] if i < len(lines) else ""
    user = lines[i + 1] if i + 1 < len(lines) else ""
    body = " ".join(lines[i + 2:]) if i + 2 < len(lines) else ""

    return {"status": status or "No due date", "channel": channel, "user": user, "message": body}


def go_to_later(tab: str = "in-progress", cdp: int = 9222) -> bool:
    """Navigate to the Later view, optionally selecting a sub-tab."""
    snapshot = ab("snapshot", "-i", cdp=cdp)
    later_ref = find_ref(snapshot, r'tab "Later"')
    if not later_ref:
        return False

    ab("click", f"@{later_ref}", cdp=cdp)
    time.sleep(2)

    if tab != "in-progress":
        snapshot = ab("snapshot", "-i", cdp=cdp)
        tab_label = tab.capitalize()
        tab_ref = find_ref(snapshot, rf'tab "{tab_label}')
        if tab_ref:
            ab("click", f"@{tab_ref}", cdp=cdp)
            time.sleep(1)
    return True


def extract_visible_later_items(cdp: int = 9222) -> list[dict]:
    """Read currently visible Later items from the virtual list.

    Returns list of {key: str, lines: list[str]}.
    """
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
""", cdp=cdp)
    batch = decode_ab_json(raw)
    return batch if isinstance(batch, list) else []


def scroll_later_to_top(cdp: int = 9222) -> None:
    """Scroll the Later virtual list to the top."""
    ab_eval(r"""(() => {
        const sc = document.querySelector('.c-virtual_list__scroll_container');
        if (!sc) return;
        let el = sc.parentElement;
        while (el) {
            if (el.scrollHeight > el.clientHeight + 10) { el.scrollTop = 0; return; }
            el = el.parentElement;
        }
    })()""", cdp=cdp)
    time.sleep(0.5)


def scroll_later_down(cdp: int = 9222) -> None:
    """Scroll the Later virtual list down by half a viewport."""
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
    })()""", cdp=cdp)
    time.sleep(0.5)
