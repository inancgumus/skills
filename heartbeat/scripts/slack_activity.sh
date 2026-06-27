#!/usr/bin/env bash
# Dump a Slack user's messages since a date: a channel map first, then every
# message with date, channel, a content snippet, and a permalink. The reader
# then digs into the channels and threads that matter.
#
# A failed query is surfaced as an error, never silently reported as "no
# messages". When the username search comes back empty and a member ID is given,
# it retries automatically with the member-ID form.
#
# Usage: slack_activity.sh <username> <since YYYY-MM-DD> [slack_id] [limit]
#   username — the Slack `name` field (e.g. inanc.gumus), NOT the full email.
#   slack_id — the member's Slack ID (e.g. U02…); auto-fallback when empty.
#   limit    — max messages to pull (default 100).
set -euo pipefail

user="${1:?usage: slack_activity.sh <username> <since YYYY-MM-DD> [slack_id] [limit]}"
since="${2:?usage: slack_activity.sh <username> <since YYYY-MM-DD> [slack_id] [limit]}"
slack_id="${3:-}"
limit="${4:-100}"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# Run a search into a file; non-zero exit means slackcli itself failed.
run_search() {  # <outfile> <query>
  slackcli search messages "$2" --limit "$limit" --sort timestamp --json >"$1" 2>"$tmp/err"
}
count() {  # <jsonfile> -> number of results (0 for null/empty)
  python3 -c "import json,sys;d=json.load(open(sys.argv[1]));print(len(d) if isinstance(d,list) else 0)" "$1" 2>/dev/null || echo 0
}

query="from:@$user after:$since"
if ! run_search "$tmp/out.json" "$query"; then
  echo "  !! slack query error: $(head -c 200 "$tmp/err")"
  exit 0
fi

# Empty with the username form? Retry with the member-ID form before giving up.
if [ "$(count "$tmp/out.json")" = "0" ] && [ -n "$slack_id" ]; then
  query="from:<@$slack_id> after:$since"
  if ! run_search "$tmp/out.json" "$query"; then
    echo "  !! slack query error: $(head -c 200 "$tmp/err")"
    exit 0
  fi
fi

python3 - "$tmp/out.json" "$query" <<'PY'
import json, sys, datetime
from collections import Counter

data = json.load(open(sys.argv[1]))
if not isinstance(data, list):
    data = []
if not data:
    print(f"No messages found for: {sys.argv[2]}")
    sys.exit(0)

# Channel map — the coverage checklist. Community/company-wide channels count too.
counts = Counter((m.get("channel_name") or "(dm/private)") for m in data)
print("## Channel map — where they posted (cover each, incl. community channels)")
for ch, n in counts.most_common():
    print(f"  {n:3}  {ch}")

print()
print(f"## Messages ({len(data)} total, newest first)")
for m in sorted(data, key=lambda x: float(x.get("message_ts", 0)), reverse=True):
    day = datetime.datetime.utcfromtimestamp(float(m.get("message_ts", 0))).strftime("%Y-%m-%d")
    ch = m.get("channel_name") or "(dm/private)"
    text = " ".join((m.get("content") or "").split())
    if len(text) > 160:
        text = text[:157] + "..."
    print(f"- {day} #{ch} :: {text} :: {m.get('permalink')}")
PY
