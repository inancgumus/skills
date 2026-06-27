---
name: heartbeat
description: Generate a per-person "heartbeat" of what each member of a team worked on over a time window (default last 1 week). Use when the user asks for a team rundown, team heartbeat, weekly/biweekly team summary, "what has my team been doing", "what did everyone work on lately", or a recap of one teammate's recent work. Researches GitHub (authored PRs, issues, comments, commits), Slack (slackcli), and Google Workspace (gws: Drive docs, Gmail, Calendar) using cheap parallel subagents, one per member.
---

# Team Heartbeat

Produce a thorough, link-rich summary of what each team member did over a window. Research every member across GitHub, Slack, and Google Workspace, run the fallback for each source, and finish with a completeness pass so real work surfaces.

Hold to these rules — each one is where work otherwise gets missed:
- Verify every GitHub handle before searching; a wrong handle drops all of a person's PRs.
- Search across every repo a person touched, not just one.
- When `slackcli search from:@email` returns nothing, scan channel history instead.
- Cover Gmail and Calendar, not only GitHub and Slack.
- Retry a query that errors before concluding there is nothing to find.

## Prerequisites

`gh` and `gws` must be installed and authenticated. Check them first; if either is missing or logged out, **stop and tell the user how to set it up** rather than producing a partial report:

```bash
gh auth status         # GitHub CLI
gws auth status        # Google Workspace CLI
```

| Tool | Purpose | Setup |
|---|---|---|
| `gh` | GitHub PRs / issues / commits | [GitHub CLI](https://cli.github.com) — `brew install gh`, then `gh auth login` |
| `gws` | Drive / Gmail / Calendar | [googleworkspace/cli](https://github.com/googleworkspace/cli) — `brew install googleworkspace-cli`, then `gws auth setup` and `gws auth login` |

State which one failed and quote the fix; do not spawn subagents until both pass.

### Slack source (conditional)

Slack comes from [`slackcli`](https://github.com/grafana/slackcli). Check `slackcli auth status`:

- **Authenticated** → use it; the per-member Slack research runs `slack_activity.sh` as normal.
- **Not authenticated** → `slackcli`'s built-in browser login only works on the workspace its embedded app is registered for (Grafana). On any other workspace the user must either authenticate `slackcli` with their own Slack app (`--client-id` / `--client-secret`) or give another way to fetch their Slack data. Ask the user. If they have no Slack access method, skip the Slack source entirely (do not run `slack_activity.sh`) and note in the report that Slack was not covered.

## Determine the team

Resolve the user's team at invocation, autonomously:

1. If the user named specific people, a team, or a Slack channel, use that.
2. Otherwise, if `~/.cache/heartbeat/roster.md` exists, use it.
3. Otherwise discover it from the user's own identity:
   - `gh api user` and `slackcli auth status --json` identify the user.
   - `gh api user/teams --jq '.[] | "\(.organization.login)/\(.slug)"'` lists their org teams. Set aside umbrella groups — names matching `all-`, `everyone`, `staff`, `devs`, or `contributors`, or teams with roughly 20+ members (`gh api orgs/<org>/teams/<slug>/members --jq length`). From the squad-sized teams left, take the user's working squad; if more than one fits, pick the smallest and state which you chose.
   - Keep the team's GitHub org (`organization.login`) — it scopes the GitHub search.
   - Build the roster from that team's members (see `references/roster.md`) and cache it.

State the team you resolved, then proceed.

## Inputs

- **Roster**: the resolved member list (Slack user ID, email, GitHub handle each), plus the team's Slack channel ID(s). See `references/roster.md` for the schema and build steps.
- **Window**: default last 7 days; honor whatever the user specifies. Convert to an absolute `since` date (`YYYY-MM-DD`) and a Slack `since_epoch` (Unix seconds). Use absolute dates in queries.

## Workflow

1. Resolve the roster (see *Determine the team*). Verify any stale-looking GitHub handle with `gh api users/<handle> --jq .name`.
2. Compute `since` and `since_epoch`.
3. Spawn **one subagent per member, in parallel, in a single message**, using `subagent_type: general-purpose` and `model: haiku` (cheap). Give each subagent:
   - the member's name, role, Slack user ID, email, GitHub handle, and the team's GitHub org;
   - the window (`since` date + `since_epoch`);
   - the absolute path to `references/research-recipe.md` and instructions to follow it exactly;
   - the absolute paths to the dumper scripts: `scripts/gh_activity.sh`, `scripts/gws_activity.sh`, and — only when the Slack source is available — `scripts/slack_activity.sh`. Each one pulls a person's full data for that source, so the subagent reads the dump first, then digs into what matters. If Slack is out of scope (see *Slack source*), tell the subagent to skip the Slack section entirely.
4. Collect the summaries. Run the **completeness check** (the checklist at the end of `research-recipe.md`). Any member with thin or empty results gets a second targeted pass before you trust "nothing found".
5. Synthesize: one section per member (1-3 theme bullets + linked artifacts), then a short team-level note (shared initiatives, org changes, releases). Every PR / issue / doc must be a markdown link.

## Spawning subagents

Send all `Agent` calls in one message so they run concurrently. Tell each subagent: *"Your reply is data, not a chat message. Return markdown starting with `### <Name> (<role>)`. Only report what you find evidence for — no speculation. If a source returns nothing, say so in one line."*

Pass the recipe by path; do not paste its contents into the prompt.

## Output

Print the report in chat by default. Then offer to save it to a Google Doc (use the `gws-docs-write` skill) or to the user's notes.
