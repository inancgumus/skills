#!/usr/bin/env bash
# Dump a GitHub user's FULL activity since a date, across every repo and every
# event type, then map the repos so each project gets discovered.
#
# The idea: capture everything first (PRs authored, issues, comments, direct
# commits — anything active in the window), print a repo map as a coverage
# checklist, then read each section. Breadth over brevity — one PR is real work.
#
# Usage: gh_activity.sh <handle> <since YYYY-MM-DD> [org]
#   org (optional) narrows the search to one org.
set -euo pipefail

handle="${1:?usage: gh_activity.sh <handle> <since YYYY-MM-DD> [org]}"
since="${2:?usage: gh_activity.sh <handle> <since YYYY-MM-DD> [org]}"
org="${3:-}"

# Confirm the handle resolves before searching, so a typo fails loudly
# instead of silently returning "no work".
if ! gh api "users/$handle" --jq '.login' >/dev/null 2>&1; then
  echo "ERROR: GitHub handle '$handle' not found — verify it before trusting empty results." >&2
  exit 2
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# --- Gather every kind of activity into the window ----------------------------
# Scope every search to the org so only org work is reported, not personal repos.
owner_flag=""
[ -n "$org" ] && owner_flag="--owner $org"

# PRs the person authored that were active in the window. --updated (not --created)
# also catches PRs they opened before the window and are still working on.
gh search prs --author "$handle" --updated ">=$since" $owner_flag --limit 100 \
  --json title,url,state,repository,createdAt,closedAt > "$tmp/authored.json"

# Issues the person authored that were active in the window.
gh search issues --author "$handle" --updated ">=$since" $owner_flag --limit 100 \
  --json title,url,state,repository,createdAt,isPullRequest > "$tmp/issues.json"

# Issues/PRs they commented on (others' work in progress).
gh search issues --commenter "$handle" --updated ">=$since" $owner_flag --limit 100 \
  --json title,url,state,repository,author,isPullRequest > "$tmp/commented.json"

# Direct commits — catches work that landed without a PR (skills, ai-kit, docs).
commit_q="author:$handle committer-date:>=$since"
[ -n "$org" ] && commit_q="$commit_q org:$org"
gh api -X GET search/commits -f q="$commit_q" -f per_page=100 \
  --jq '.items // []' > "$tmp/commits.json" 2>/dev/null || echo '[]' > "$tmp/commits.json"

# --- Repo map: every repo touched, most-active first (coverage checklist) ------

echo "## Repo map — every repo touched since $since (cover each one below)"
{
  jq -r '.[].repository.nameWithOwner' \
    "$tmp/authored.json" "$tmp/issues.json" "$tmp/commented.json"
  jq -r '.[].repository.full_name' "$tmp/commits.json"
} | sort | uniq -c | sort -rn | sed 's/^/  /'

echo
echo "## Authored PRs (active >= $since — opened or worked on in the window)"
jq -r '.[] | "- [\(.repository.nameWithOwner)] \(.title) :: \(.state) :: \(.url)"' "$tmp/authored.json"

echo
echo "## Authored issues (active >= $since)"
jq -r '.[] | select(.isPullRequest | not) | "- [\(.repository.nameWithOwner)] \(.title) :: \(.state) :: \(.url)"' "$tmp/issues.json"

echo
echo "## Commented on / involved (updated >= $since, authored by others)"
jq -r --arg me "$handle" '.[] | select(.author.login != $me) | "- [\(.repository.nameWithOwner)] \(if .isPullRequest then "PR" else "issue" end) \(.title) :: \(.state) :: \(.url)"' "$tmp/commented.json"

echo
echo "## Direct commits (committed >= $since — work that landed without a PR)"
jq -r '.[] | "- [\(.repository.full_name)] \(.commit.message | split("\n")[0]) :: \(.html_url)"' "$tmp/commits.json"
