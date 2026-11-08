# Parallel builds

Only when the developer asks.

1. Create a shared branch. If the project wants one PR per ticket, stack branches instead.
2. For each ready agent-owned ticket, start a background subagent in its own worktree. It sets up dependencies and ignored files, follows `build.md` through `Check the whole change`, commits, merges the shared branch into its own, and resolves conflicts. If intents clash, it stops and you ask the developer.
3. Merge each finished branch into the shared one, and start the tickets this frees.
4. When none can start, remove the worktrees, list human tickets, and run `review`.

Give subagents absolute paths, because worktrees have no `.notebook/`.

**Finish when** every runnable ticket is merged and the worktrees are gone.
