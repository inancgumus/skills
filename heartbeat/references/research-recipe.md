# Research recipe (per member)

Follow every section. Each source has a primary query and a fallback — run the fallback whenever the primary returns nothing. Keep only items dated on/after `since`. Slack timestamps are Unix epoch floats; convert and compare against `since_epoch`. Parse all JSON with `python3`.

The window bounds which work to report, not how long someone has been on the team. Base any joined/left/tenure claim on explicit evidence — a welcome or removal message, or commit/PR history outside the window (`gh search prs --author <handle> --created <older-range>`). The earliest item inside the window tells you nothing about when they joined.

Inputs you are given: `name`, `role`, `slack_id`, `email`, `gh_handle`, `org` (the team's GitHub org), `since` (YYYY-MM-DD), `since_epoch`, and the path to `scripts/gh_activity.sh`.

## 1. GitHub (usually the richest source)

Run the helper. In one pass it pulls the person's **full** GitHub activity for the window — PRs they authored and worked on (including ones opened before the window but still active), issues, issues/PRs they commented on, and direct commits that landed without a PR — across every repo they touched. Pass the org to scope the search:

```bash
bash <path>/scripts/gh_activity.sh <gh_handle> <since> <org>
```

Work the output top-down:

- **Start from the repo map.** The first section lists every repo the person touched, most-active first. This is your coverage checklist — walk it and account for each repo in the report. A repo with one PR or a few commits (docs, a skill, `ai-kit`, a one-off tool) is real work; give it its own artifact line rather than absorbing it into a bigger theme.
- **Read every section, including commits.** Commit-only contributions (skills, `ai-kit`, docs, scripts) appear under *Direct commits* and nowhere else — cover them like PRs.
- The dump is scoped to the org (passed as the third arg), so every item belongs to the org. Report only what it returns.
- A PR opened before the window but still worked on during it appears under *Authored PRs* (the query is by last-updated) — it counts; mention it.

## 2. Slack (slackcli, read-only) — scan the whole workspace

Skip this section entirely if you were told the Slack source is out of scope (`slackcli` not authenticated for this workspace). Otherwise:

Run the helper. It prints a **channel map** (every channel the person posted in, busiest first) and then every message with date, channel, a content snippet, and a ready permalink:

```bash
bash <path>/scripts/slack_activity.sh <username> <since> <slack_id>
```

`<username>` is the Slack `name` field (e.g. `inanc.gumus`, the bare username, **not** the email) — get it from `slackcli get user <slack_id> --json`. The bare-email form does not resolve a person; the username does. Passing `<slack_id>` lets the helper retry with the member-ID form automatically when the username search is empty. A `!! slack query error` line means the query itself failed — fix it rather than treating it as no activity.

Work from the channel map down: treat **every** channel as in scope — the squad's own channels *and* the company-wide and community channels they show up in (engineering-wide, project, topic, hackathon, and social channels). These cross-team channels are where initiative, influence, and side projects surface, so report what you find there alongside the squad work.

Dig into what matters: follow notable threads with `slackcli list threads <channel_id> <thread_ts> --json`, and scan a channel's wider history for context with `slackcli list messages <channel_id> --limit 200 --json` (keep messages where `user == "<slack_id>"` and `float(ts) >= <since_epoch>`). Harvest any PR/issue/doc URLs out of each message's `content`. Judge for yourself what reflects the member's work and standing.

**Always link the conversation.** Every notable Slack item in the output must be a markdown link to the message:
- `slackcli search messages` results include a ready `permalink` field — use it directly (this is the easiest source of correct links).
- `slackcli list messages` results have no permalink; build one as `https://<workspace>.slack.com/archives/<channel_id>/p<ts-without-the-dot>` (e.g. ts `1782389230.011689` → `…/p1782389230011689`). For a thread reply, append `?thread_ts=<parent_ts>&cid=<channel_id>`. Get `<workspace>` from any `search` permalink or from `slackcli auth status`.
- `slackcli resolve <url>` does the reverse if you need to confirm a link points where you think.
- Point every link at a real message (its `permalink`, or one built from its `channel_id` and `ts`). When a point has no backing message, link the message you inferred it from, or leave it unlinked.

## 3. Google Workspace (gws)

You run as the user's own account, so you see docs **shared with the user** and the user's own mail/calendar — not the teammate's private items. Still valuable for shared context.

Run the helper. In one pass it prints three sections — Drive docs the teammate authored or edited (title, owner, link), Gmail threads you exchanged (subject, date, link), and shared Calendar events (title, link) — each filtered to the window:

```bash
bash <path>/scripts/gws_activity.sh <first_name> <email> <since>
```

Then dig in: for a Drive doc whose title alone does not tell you what the member added, open it (`gws docs documents get` / Drive). Try the surname too (`gws_activity.sh <surname> <email> <since>`) when the first name is common or returns little. For a notable mail thread, read it with `gws gmail users messages get`. Report what the member actually contributed, not just that a doc or meeting exists.

## Output shape

Return markdown:

```
### <Name> (<role>)
<1-3 theme bullets describing the main work>

Artifacts
- [<title>](<url>) — one-line TLDR of what it is and why it matters, then where it stands now (merged / in review / blocked on X / commented to push Y)
- ...

Notable
- <point> ([slack](<message permalink>))
```

The theme bullets summarize the headline work; the Artifacts list preserves the **breadth**. Give every distinct repo or project its own artifact line, even small ones (a docs PR, a single skill, a one-off tool, a few commits to `ai-kit`) — they show range, so let them stand on their own rather than folding them into the dominant theme. Aim to cover every repo from your GitHub repo map and every channel from your Slack scan.

Give every item a quick TLDR — its significance and current situation — not just the title and state. Read the PR/issue/doc when the title alone does not tell you what it is or where it stands. Keep each to one tight line: signal, not noise. Every PR/issue/doc/Slack item is a markdown link. State only what the sources show.

## Completeness checklist (orchestrator runs this before finalizing)

For each member, confirm every in-scope dumper ran and the report covers their breadth. Check that:
1. The report's repos match `gh_activity.sh`'s repo map — every repo with PRs, and every repo from the *Direct commits* section, appears as an artifact, including the small ones. If the summary names fewer projects than the map, send it back for the missing ones.
2. If Slack is in scope, the Slack section reflects `slack_activity.sh`'s channel map — community and company-wide channels are covered, not only the squad channels. If the dump printed "No messages", confirm the member-ID fallback (`from:<@<slack_id>>`) was run.
3. The GWS section reflects `gws_activity.sh` — shared docs the member owns or edited are accounted for, not just meeting notes.

If a member is empty or suspiciously thin, re-verify the handle (`gh api users/<gh_handle> --jq .name`) and re-run the in-scope dumpers (try the surname for `gws_activity.sh`). Only after these report nothing may you write "no tracked activity this window".
