# Questions

## Ask in batches

Ask everything answerable now in one message, then wait. A question that depends on an open answer waits for a later batch. Send a subagent for facts, and hold back only the questions that need them.

```text
Q1. Should a cancelled order refund automatically?
Recommended: yes, because support refunds them all by hand today (cancel handler, line 42).
```

Between batches, challenge vague words, invent an edge case that forces a choice, and check answers against the code.

## Questions for someone else

Ask the developer who it goes to and what they must be able to decide. Then write `.notebook/questions-<person>.md`: why you ask, a paragraph of context, the deadline, then one question at a time, most important first, ending with *Anything else?*. "I don't know" is a useful answer.
