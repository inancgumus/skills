# Roster: schema, building, caching

A roster is the list of people to research, each with the identifiers the recipe needs. Build it once per team, cache it, and reuse it.

## Schema

| Field | How it's used | How to get it |
|---|---|---|
| Name | Display + Drive/Calendar text search | given |
| Role | Display only | `slackcli get user <id> --json` (`title`) |
| Slack user ID | Channel-history fallback filter | `slackcli get user <id>` / message `user` field |
| Email | Slack `from:` search, Gmail search | `slackcli get user <id> --json` (`email`) |
| GitHub handle | All GitHub queries | resolve + verify (below) |

Also record the team's main Slack channel ID(s) — used for the channel-history fallback.

## Cache location

`~/.cache/heartbeat/roster.md` (and `channels.txt` for channel IDs). Write the roster here after building it, and read it on later runs. Refresh when it looks stale or the user names a different team.

## Building a roster

Preferred source — the GitHub team (gives verified handles and the full membership):

1. Members: `gh api orgs/<org>/teams/<slug>/members --jq '.[].login'`.
2. For each login, get the full name (`gh api users/<login> --jq .name`) and resolve the Slack ID + email by searching that name: `slackcli search users "<name>" --json` (returns `user_id`, `email`, `title`). Match on full name.
3. Find the team's main Slack channel for the channel-history fallback: `slackcli search channels <team-keyword> --json`; record its ID.
4. Drop bots and alumni. Write the result to the cache path above.

Alternate source — a Slack channel (when there is no GitHub team):

1. Pull recent authors: `slackcli list messages <channel-id> --limit 150 --json` → unique `user` IDs → resolve each with `slackcli get user <id> --json` (full name, title, email).
2. For each, resolve the GitHub handle by **verifying** candidates: `gh api users/<handle> --jq .name` and confirm the name matches. A wrong handle is the number-one cause of missed work.
3. Drop bots and alumni; write to the cache path.

## Verifying / refreshing

- Slack ID: `slackcli get user <id> --json` (returns full_name, title, email).
- GitHub handle: `gh api users/<handle> --jq .name`.
- Emails often follow `first.last@<company-domain>`, but do not assume — confirm via `slackcli get user`.
