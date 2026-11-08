# Review

Check a diff two separate ways: does it follow the rules, and does it do what we agreed?

## Steps

### Pin the diff

Use the base the developer names, or the merge base. Include uncommitted and untracked files.

**Move on when** the base resolves and the diff is not empty.

### Find what we agreed

Check the conversation, then references, commit messages, and tickets. If there is no record, skip the request check and say so.

**Move on when** you have the request, or know there is none.

### Find the rules

List contributing guides, coding standards, agent instructions, past decisions, `design/rules.md`, and any saved checks.

**Move on when** you have the paths.

### Run both checks

Start two subagents at once with the briefs below. Each verifies its findings and stays under 400 words.

**Move on when** both have reported.

### Report

Show the two reports separately, without merging or reranking, with counts and the worst of each.

**Move on when** the developer has seen both.

### Fix what the developer picks

Refactoring belongs here. Rerun the tests, lint, and checks afterward.

**Move on when** the checks pass and each finding is fixed or dismissed.

## Briefs

### Rules check

Compare the diff with these rules. Give file, line, and rule, marked as a violation or a judgment call. Skip what tools enforce. Repo rules override this list, and items here are always judgment calls: names that hide meaning, repeated logic, a method using another type's data, fields that travel together, a string standing in for a type, repeated switches, one change forcing edits in many files, a file changed for unrelated reasons, unneeded abstractions, long call chains, functions that only pass calls through, ignored inheritance, and old tests reaching into hidden code.

### Request check

Compare the diff with the request, quoting it. Report what is missing or partial, what was not asked for, and what looks done but behaves wrongly.
