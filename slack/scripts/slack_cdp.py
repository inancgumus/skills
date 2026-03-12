"""Shared helpers for Slack CDP automation scripts.

All scripts in this directory use agent-browser to control the Slack desktop
app via Chrome DevTools Protocol (CDP). This module holds the common utilities
so fixes and improvements only need to happen in one place.
"""

from __future__ import annotations

import json
import re
import subprocess
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
# Snapshot helpers
# ---------------------------------------------------------------------------

def find_ref(snapshot: str, label_pattern: str) -> str | None:
    """Find the first [ref=eN] whose line matches *label_pattern* (case-insensitive)."""
    for line in snapshot.splitlines():
        if re.search(label_pattern, line, re.IGNORECASE):
            m = re.search(r'\[ref=(e\d+)\]', line)
            if m:
                return m.group(1)
    return None


def find_all_refs(snapshot: str, label_pattern: str) -> list[str]:
    """Find ALL [ref=eN] whose line matches the pattern."""
    refs = []
    for line in snapshot.splitlines():
        if re.search(label_pattern, line, re.IGNORECASE):
            m = re.search(r'\[ref=(e\d+)\]', line)
            if m:
                refs.append(m.group(1))
    return refs


# ---------------------------------------------------------------------------
# Workspace detection
# ---------------------------------------------------------------------------

_workspace_domain: str | None = None


def get_workspace_domain(cdp: int = 9222) -> str:
    """Auto-detect the Slack workspace domain from the running app.

    Queries the DOM for workspace-specific links (e.g. *.slack.com) and caches
    the result for the lifetime of the process.
    """
    global _workspace_domain
    if _workspace_domain:
        return _workspace_domain

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
        _workspace_domain = domain
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
    if find_ref(snapshot, r'treeitem "Unreads"') or find_ref(snapshot, r'treeitem "Threads"'):
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
        if find_ref(snapshot, r'treeitem "Unreads"') or find_ref(snapshot, r'treeitem "Threads"'):
            return snapshot

    return snapshot  # best effort


def navigate_to(target: str, cdp: int) -> bool:
    """Use Cmd+K (quick switcher) to navigate to a channel or DM by name."""
    ab("press", "Meta+k", cdp=cdp)
    time.sleep(1)

    snapshot = ab("snapshot", "-i", cdp=cdp)
    input_ref = find_ref(snapshot, r'(combobox|textbox|input)')
    if not input_ref:
        return False

    ab("fill", f"@{input_ref}", target, cdp=cdp)
    time.sleep(1)

    snapshot = ab("snapshot", "-i", cdp=cdp)
    first_option = find_ref(snapshot, r'(option|listitem)')
    if first_option:
        ab("click", f"@{first_option}", cdp=cdp)
    else:
        ab("press", "Enter", cdp=cdp)

    time.sleep(1)
    return True


def navigate_to_message(channel_id: str, message_ts: str, cdp: int) -> None:
    """Navigate to a specific message via its Slack deep link (through CDP)."""
    domain = get_workspace_domain(cdp)
    ts_for_url = "p" + message_ts.replace(".", "")
    url = f"https://{domain}/archives/{channel_id}/{ts_for_url}"
    ab("open", url, cdp=cdp)
    time.sleep(2)


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def decode_ab_json(raw: str):
    """Decode JSON output from agent-browser (may be double-quoted)."""
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw
