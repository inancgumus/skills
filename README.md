# Skills

Agent skills for the [open agent skills ecosystem](https://agentskills.io).

## Available Skills

| Skill | Description |
|-------|-------------|
| [slack](slack/) | Read, navigate, search, and send messages in Slack via the desktop app |
| [handoff](handoff/) | Write or load a HANDOFF.md to preserve and restore session state across agent sessions |
| [designdoc](designdoc/) | Write or rewrite technical design docs, RFCs, and proposals for cold readers |
| [flowchart](flowchart/) | Generate flowcharts and architecture diagrams as interactive HTML or Markdown+ASCII |
| [go](go/) | Modern Go practices |
| [git-pr](git-pr/) | Write PR descriptions in engineer-to-engineer tone |
| [git-pr-review](git-pr-review/) | Review PRs by verifying claims and posting inline reviews via `gh` |
| [git-issue](git-issue/) | Write and file GitHub issues, bug reports and proposals alike, as a case a maintainer will act on |
| [git-split](git-split/) | Split big commits into smaller, atomic ones |
| [gh-review-reqs](gh-review-reqs/) | List open GitHub PRs that need your review attention, across all repos |
| [heartbeat](heartbeat/) | Per-person summary of what each team member worked on over a window, from GitHub, Slack, and Google Workspace |
| [claude-sessions](claude-sessions/) | List recent Claude Code sessions and resume them in new iTerm tabs |
| [writing-style](writing-style/) | Write prose like an experienced engineer talking to another engineer |
| [write](write/) | Write and rewrite prose without AI tells: judge, rewrite, and flag against a rubric without changing meaning |

## Install

```bash
# Install all skills
npx skills add inancgumus/skills

# Install a specific skill
npx skills add inancgumus/skills --skill slack
```

## Development

For local development, symlink the skills from this repo into `~/.agents/skills/` so edits are always in sync:

```bash
git clone git@github.com:inancgumus/skills.git ~/dev/skills
cd ~/dev/skills
./install.sh            # symlink all skills
./install.sh flowchart  # or just one
```

The script is idempotent — run it after cloning on a new machine, or after adding a new skill.

## Requirements

**slack**
- [agent-browser](https://github.com/anthropics/agent-browser) CLI
- Slack desktop app (auto-launched with CDP if not already running)

**handoff**
- No dependencies

**designdoc**
- No dependencies

**flowchart**
- No dependencies (HTML output is a single self-contained file)
- [agent-browser](https://github.com/anthropics/agent-browser) CLI (optional, for auto-opening the HTML output)

**git-pr**
- `gh` CLI

**git-pr-review**
- `gh` CLI
- Docker (for reproducing config/infra PR claims locally)

**git-split**
- No dependencies

**gh-review-reqs**
- `gh` CLI
- `jq`

**heartbeat**
- `gh` CLI
- [`gws`](https://github.com/googleworkspace/cli) (Google Workspace CLI)
- [`slackcli`](https://github.com/grafana/slackcli)

**writing-style**
- No dependencies

**claude-sessions**
- macOS with iTerm2 (new tabs are created through AppleScript)
- `python3`
