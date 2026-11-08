# Situations

## The developer is lost

Explain your last message again in plain words, with the missing context.

## Only a human can do this

Give steps a stranger could follow: which page, what to click, what to bring back. Check the docs rather than inventing steps. Secrets go in the environment, never the chat. Check that it worked afterward.

For a long procedure, write a script with one stage per task. It opens each URL, hides secret entry, saves each value, and confirms before anything irreversible. Trace it by reading, since it waits on a person.

## Git stops on a conflict

Read the commits and tickets behind each side, because you are choosing between two intentions. Keep both where they fit. If they clash, ask which wins. Use `--ours` or `--theirs` only when you know what they drop.

## The work must wait

Save what we know, what we wait for, the branch, and the step to resume from in a ticket, with status *waiting*. Note any conflict resolutions, then abort a merge in progress. On return, set it to *taken* and resume without asking again.

## A workflow ended

Recommend the first that fits:

| Situation | Recommend |
|---|---|
| The next workflow needs this conversation | Stay |
| Nothing here matters to what comes next | A new session, with the exact command |
| The work moves to another person, directory, or tool | The `handoff` skill |
| It can run without the developer | A subagent |
| Otherwise | Compact, saying what to keep |
