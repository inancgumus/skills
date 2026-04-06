# Skills

Agent skills for the [open agent skills ecosystem](https://agentskills.io).

## Available Skills

| Skill | Description |
|-------|-------------|
| [slack](slack/) | Read, navigate, search, and send messages in Slack via the desktop app |
| [handoff](handoff/) | Write or load a HANDOFF.md to preserve and restore session state across agent sessions |
| [write-design-doc](write-design-doc/) | Write or rewrite technical design docs, RFCs, and proposals for cold readers |
| [flowchart](flowchart/) | Generate flowcharts and architecture diagrams as interactive HTML or Markdown+ASCII |

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

**write-design-doc**
- No dependencies

**flowchart**
- No dependencies (HTML output is a single self-contained file)
- [agent-browser](https://github.com/anthropics/agent-browser) CLI (optional, for auto-opening the HTML output)
