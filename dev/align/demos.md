# Demos

A demo is marked throwaway code that answers one question, stated at its top. It runs with one command, keeps state in memory, shows state after each action, and has no tests.

## Logic demo

Put the logic in one pure module that can later lift into the real code. Wrap it in one HTML file a non-developer can open, with domain words, one button per action, and tabbed scenarios that step through a happy path, an edge case, and something illegal.

## UI variants

Build 3 to 5 inside the real page, switched by `?variant=`, with a small switcher hidden from production. They must differ in structure, not color.

## Afterward

Record the verdict on the ticket. Commit the demo to an unmerged side branch and link it. The main branch gets only the decision, rewritten properly.
