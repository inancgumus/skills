"""Shared helpers for Slack CDP automation scripts.

All scripts in this directory use agent-browser to control the Slack desktop
app via Chrome DevTools Protocol (CDP). This module holds the common utilities
so fixes and improvements only need to happen in one place.
"""

from __future__ import annotations

import json
import platform
import re
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

def _check_cdp_connection(cdp: int) -> bool:
    """Return True if we can reach Slack via CDP."""
    try:
        out = ab_eval("window.location.href", cdp=cdp)
        return "slack" in out.lower()
    except (RuntimeError, subprocess.TimeoutExpired):
        return False


def _is_slack_running() -> bool:
    system = platform.system()
    if system == "Darwin":
        return subprocess.run(["pgrep", "-x", "Slack"], capture_output=True).returncode == 0
    elif system == "Linux":
        return subprocess.run(["pgrep", "-f", "slack"], capture_output=True).returncode == 0
    elif system == "Windows":
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq slack.exe"], capture_output=True, text=True)
        return "slack.exe" in r.stdout.lower()
    return False


def _launch_slack_with_cdp(cdp: int) -> str:
    """Return the platform-specific command to (re)launch Slack with CDP enabled.

    Quits Slack first only if it's already running.
    """
    port = str(cdp)
    system = platform.system()
    running = _is_slack_running()

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
    """Ensure Slack is running with CDP. Relaunches it automatically if needed."""
    if _check_cdp_connection(cdp):
        return

    cmd = _launch_slack_with_cdp(cdp)
    print(json.dumps({"status": "launching_slack", "command": cmd}), file=sys.stderr)
    subprocess.run(cmd, shell=True, capture_output=True, timeout=15)

    for _ in range(15):
        time.sleep(2)
        if _check_cdp_connection(cdp):
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


def search_and_select(query: str, cdp: int) -> bool:
    """Open the Search bar, type a query, and select the first suggestion.

    Works for navigating to Slack views like Unreads, Threads, etc.
    that may not appear as the first suggestion for short names.
    """
    snapshot = ab("snapshot", "-i", cdp=cdp)
    search_ref = find_ref(snapshot, r'button "Search"')
    if not search_ref:
        return False

    ab("click", f"@{search_ref}", cdp=cdp)
    time.sleep(1)

    snapshot = ab("snapshot", "-i", cdp=cdp)
    input_ref = find_ref(snapshot, r'combobox.*Query')
    if not input_ref:
        return False

    ab("fill", f"@{input_ref}", query, cdp=cdp)
    time.sleep(1)

    snapshot = ab("snapshot", "-i", cdp=cdp)
    option_ref = find_ref(snapshot, r'option')
    if option_ref:
        ab("click", f"@{option_ref}", cdp=cdp)
    else:
        ab("press", "Enter", cdp=cdp)

    time.sleep(1)
    return True


def navigate_to(target: str, cdp: int) -> bool:
    """Navigate to a channel, DM, or Slack view by name via the search bar."""
    return search_and_select(target, cdp)


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
