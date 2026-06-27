#!/usr/bin/env bash
# Dump a teammate's Google Workspace footprint that is shared with you: Drive
# docs they own or that mention them, Gmail threads you exchanged, and Calendar
# meetings you both attend — each with a title and a link. The reader opens what matters.
#
# You run as your own account, so this sees shared docs and your own mail/
# calendar with the teammate, not their private items. A failed query is surfaced
# as an error, never silently reported as "(none)".
#
# Usage: gws_activity.sh <first_name> <email> <since YYYY-MM-DD>
set -euo pipefail

name="${1:?usage: gws_activity.sh <first_name> <email> <since YYYY-MM-DD>}"
email="${2:?usage: gws_activity.sh <first_name> <email> <since YYYY-MM-DD>}"
since="${3:?usage: gws_activity.sh <first_name> <email> <since YYYY-MM-DD>}"
since_slash="${since//-//}"            # 2026-01-01 -> 2026/01/01 (Gmail date form)
today="$(date -u +%F)"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

drive_fields='files(id,name,modifiedTime,webViewLink,owners(displayName))'
# Cover shared drives too, not just the user's own corpus.
drive_extra='"includeItemsFromAllDrives":true,"supportsAllDrives":true,"corpora":"allDrives"'

# --- Drive / Docs -------------------------------------------------------------
# Two signals, unioned: docs they OWN (precise — catches work whose text never
# names them) and docs that MENTION their name (catches edits to others' docs).
echo "## Drive docs owned by or mentioning $name (modified >= $since)"
gws drive files list --params "{\"pageSize\":100,\"orderBy\":\"modifiedTime desc\",\"q\":\"'$email' in owners\",$drive_extra,\"fields\":\"$drive_fields\"}" --format json 2>/dev/null > "$tmp/owned.json" || true
gws drive files list --params "{\"pageSize\":100,\"orderBy\":\"modifiedTime desc\",\"q\":\"fullText contains '$name'\",$drive_extra,\"fields\":\"$drive_fields\"}" --format json 2>/dev/null > "$tmp/mention.json" || true
python3 - "$since" "$tmp/owned.json" "$tmp/mention.json" <<'PY'
import json, sys
since = sys.argv[1]
seen, errs = {}, []
for path in sys.argv[2:]:
    try:
        raw = open(path).read().strip()
        obj = json.loads(raw) if raw else {}
    except Exception as e:
        errs.append(str(e)); continue
    if isinstance(obj, dict) and obj.get("error"):
        errs.append(obj["error"].get("message", "unknown error")); continue
    for f in obj.get("files", []):
        if f.get("modifiedTime", "")[:10] >= since:
            seen[f.get("id")] = f
rows = sorted(seen.values(), key=lambda f: f.get("modifiedTime", ""), reverse=True)
if errs:
    print("  !! query error:", "; ".join(sorted(set(errs))))
if not rows and not errs:
    print("  (none)")
for f in rows:
    owner = (f.get("owners") or [{}])[0].get("displayName", "?")
    print(f"- {f.get('modifiedTime','')[:10]} \"{f.get('name')}\" (owner: {owner}) :: {f.get('webViewLink')}")
PY

# --- Gmail --------------------------------------------------------------------
echo
echo "## Gmail threads with $email (after $since_slash)"
gws gmail users messages list --params "{\"userId\":\"me\",\"q\":\"(from:$email OR to:$email) after:$since_slash\",\"maxResults\":20}" --format json 2>/dev/null > "$tmp/gmail.json" || true
ids="$(python3 - "$tmp/gmail.json" <<'PY'
import json, sys
raw = open(sys.argv[1]).read().strip()
obj = json.loads(raw) if raw else {}
if isinstance(obj, dict) and obj.get("error"):
    print("ERR:" + obj["error"].get("message", "unknown error")); sys.exit()
print("\n".join(m["id"] for m in obj.get("messages", [])))
PY
)"
if [ "${ids#ERR:}" != "$ids" ]; then
  echo "  !! query error: ${ids#ERR:}"
elif [ -z "$ids" ]; then
  echo "  (none)"
else
  for id in $ids; do
    gws gmail users messages get --params "{\"userId\":\"me\",\"id\":\"$id\",\"format\":\"metadata\",\"metadataHeaders\":[\"Subject\",\"Date\"]}" --format json 2>/dev/null \
    | python3 -c "
import json, sys
raw = sys.stdin.read().strip()
d = json.loads(raw) if raw else {}
h = {x['name']: x['value'] for x in d.get('payload', {}).get('headers', [])}
tid = d.get('threadId', '')
print(f\"- {h.get('Date','?')} :: {h.get('Subject','(no subject)')} :: https://mail.google.com/mail/u/0/#all/{tid}\")
"
  done
fi

# --- Calendar -----------------------------------------------------------------
# Filter by attendee email (precise) plus a name match, so meetings they attend
# are caught even when their name is not in the title.
echo
echo "## Calendar events with $name ($since .. $today)"
gws calendar events list --params "{\"calendarId\":\"primary\",\"singleEvents\":true,\"orderBy\":\"startTime\",\"timeMin\":\"${since}T00:00:00Z\",\"timeMax\":\"${today}T23:59:59Z\",\"fields\":\"items(summary,start,htmlLink,attendees(email))\"}" --format json 2>/dev/null > "$tmp/cal.json" || true
python3 - "$email" "$name" "$tmp/cal.json" <<'PY'
import json, sys
email, name, path = sys.argv[1], sys.argv[2].lower(), sys.argv[3]
raw = open(path).read().strip()
obj = json.loads(raw) if raw else {}
if isinstance(obj, dict) and obj.get("error"):
    print("  !! query error:", obj["error"].get("message", "unknown error")); sys.exit()
hits = []
for e in obj.get("items", []):
    att = [a.get("email", "") for a in e.get("attendees", [])]
    if email in att or name in (e.get("summary", "") or "").lower():
        hits.append(e)
if not hits:
    print("  (none)")
for e in hits:
    s = e.get("start", {})
    when = (s.get("dateTime") or s.get("date") or "")[:10]
    print(f"- {when} {e.get('summary','(no title)')} :: {e.get('htmlLink')}")
PY
