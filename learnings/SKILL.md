---
name: learnings
description: Use to capture learnings from this session
---

# Learnings

Read `~/.agents/docs/learnings.md` in full before reviewing the session.
`learnings.md` MUST only be updated for engineering principles and decisions.

If the `write` skill is available, read its `SKILL.md` in full and use it to revise candidate lessons before writing them.

Review the complete session, with extra attention to mistakes, rejected approaches, repeated corrections, and the final accepted result. Extract only lessons that would change how a clean-slate agent handles future work.

For each candidate lesson:

- Convert the underlying mistake into one actionable command.
- Keep enough detail to guide a decision, but remove project names, feature names, commands, paths, and other session-specific facts.
- Cover one action only. Split independent actions instead of joining them.
- Compare the trigger, action, boundary, and prevented failure against every existing lesson, not only its wording.
- Skip the lesson when it would lead to the same decision under the same conditions.
- Keep a related lesson only when it adds a distinct trigger, action, boundary, or prevented failure.
- Preserve every existing item exactly. Do not merge, rewrite, reorder, or delete existing lessons.

Add each new lesson under the closest existing Markdown heading. Create a heading only when none fits. Write subjectless imperative bullets. Do not use first person or label-and-explanation bullets such as `**Scope:** ...`.

Ensure sorting new lessons by importance and priority.

If no unique lesson remains, leave the file unchanged and state that the session produced no new lessons.

Before editing the file, show the exact unified diff and stop for explicit user approval. Do not treat the request to use this skill as approval. After approval, read the file again. If it changed or the approved diff no longer applies exactly, show a revised diff and request approval again. Otherwise, apply only the approved diff and report the lessons added.
