# Skills

Agent skills for the [open agent skills ecosystem](https://agentskills.io).

## Available Skills

| Skill | Description |
|-------|-------------|
| [slack](slack/) | Read, navigate, search, and send messages in Slack via the desktop app |
| [handoff](handoff/) | Write or load a HANDOFF.md to preserve and restore session state across agent sessions |

## Install

```bash
# Install all skills
npx skills add inancgumus/skills

# Install a specific skill
npx skills add inancgumus/skills --skill slack
```

## Requirements

**slack**
- [agent-browser](https://github.com/anthropics/agent-browser) CLI
- Slack desktop app (auto-launched with CDP if not already running)

**handoff**
- No dependencies
