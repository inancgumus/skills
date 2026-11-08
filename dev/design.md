# Design

Shape new code, or improve existing code, so that future changes stay in one place. Produces a decision and checks, with no production code changes.

## Steps

### Load the rules

Read `design/rules.md`.

**Move on when** you can name the rules that bear on this work.

### Choose where to look

Start from what the developer named, or the code new work will sit beside. Otherwise use the files that change most:

```bash
git log --since="6 months ago" --name-only --format= | sort | uniq -c | sort -rn | head -30
```

**Move on when** the developer has seen the area and why.

### Find what hurts

New code skips this step and the next. Send a subagent through the area for file and line evidence:

- How many files must you bounce between to understand one idea?
- What does each module know about its callers?
- If you rewrote a module's insides, which other files would change?
- Which arrows point upward or sideways?
- Does a shared loop or config object grow with each feature?
- Does control flow hide in events or `phase` variables?
- What can you only test by reaching past the public interface?
- If you deleted a module, would the complexity vanish or reappear in every caller?

**Move on when** each problem has evidence.

### Show the options

For each: files, problem, change, ripple count before and after, a before and after diagram, and a verdict of *Do it*, *Maybe*, or *Long shot*. Flag any that contradict a past decision. Recommend one. Hold back interfaces until the developer picks.

For more than three options, or a system design, put this in a self-contained HTML report outside the repo, or an artifact if the tool offers one. Give each option a card, and end with your top recommendation.

**Move on when** the developer picks one or rejects them all.

### Compare designs

Unless the design is obvious, send 3 subagents the same facts with different goals: the smallest interface, the easiest common call, and the widest range of uses. Each returns the interface with its errors and ordering rules, a usage example, what it hides, and its weak spots. Compare ripple count, what callers must know, and how tests reach the behavior, then recommend.

**Move on when** the developer has seen your recommendation.

### Settle the design

Follow `align/questions.md`.

**Move on when** nothing about the design is open.

### Decide how it will be tested

Sort each dependency using `build/tests.md`. Mark existing tests that reach hidden pieces for replacement.

**Move on when** every dependency and affected test is sorted.

### Turn the rules into checks

Write a check per rule, in a lint or dependency tool where possible. Prove each can fail: pass, break the rule, fail, revert, pass. Save the decision, tests to replace, and checks where tickets live.

**Move on when** the design is saved and the developer has seen it.
