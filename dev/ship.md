# Ship

Finish work the way this project or ticket finishes. Code passes `review` first.

## Steps

### Check how this work finishes

Read the ticket's *Finish*, then `.notebook/dev.md`. If the work has code, run the tests and lint.

**Move on when** you know how it finishes and the checks pass.

### Make the commits

Skip this with no code, unless marking the ticket done needs a commit. Use the `git-commit` skill. Show any commits subagents already made.

**Move on when** the commits exist.

### Finish it

The project's note wins over this table.

| Finish | Do |
|---|---|
| Local commit | Nothing more. |
| Merge | Ask, merge, and rerun the tests. |
| PR | Use the `git-pr` skill. |
| Decision or doc | Write the answer where the ticket says. |

**Move on when** the work has finished, and you have given any link.

### Update the ticket

Mark it done the way the note says, unless a PR closes it on merge. Draft any reply to a reporter, and list the tickets this freed.

**Move on when** the ticket's status is right.

### Make the next run easier

Suggest fixes to the setup, worst first, or say the session went smoothly.

| What went wrong | Suggest |
|---|---|
| A mechanical mistake | A lint rule, hook, or CI check |
| Nothing runs the checks | Wire up what the repo has |
| A judgment call the review missed | A coding standard |
| Finding a file took too long | A one-line pointer in agent instructions |
| Information was out of reach | Access to logs or test data |
| A costly tool call | A cheaper command |
| An instruction changed nothing | Delete it |

**Move on when** the developer has accepted or declined each.
