---
name: write
description: 'Write prose that does not read like AI, and strip AI tells from existing text without changing what it says. Use whenever drafting prose a human will read (docs, posts, announcements, emails, reports) and whenever asked to humanize text, make it sound less like AI or ChatGPT, remove AI slop, or give generated prose a quality pass, even when the request is just "clean this up" or "does this read like AI?". Detects the tells, rewrites only what has a real point, flags hollow spans instead of inventing claims, and self-scores against a rubric before delivering.'
---

# Write

Make prose that survives a hostile editor's red pen and does not read like it came from a chatbot. One standard, two jobs:

- **Drafting.** Write new text with the pattern catalogue in mind, then run the loop below on your own draft before delivering it.
- **Editing.** Remove AI tells from existing text while preserving exactly what it says.

## Two hard rules (read first)

1. **Fidelity over flair.** Preserve the original meaning and claims exactly. Subtract hedging and filler, sharpen what is already there. Never inject stance, edginess, dash theatrics, or first-person personality the content did not earn. The rewrite must not state any fact, name, number, date, quote, or citation that is not in the source or supplied by the user. Swapping AI slop for edgy slop is a failure, not a fix. (In fiction, invented detail is the job. This rule governs everything else.)
2. **Flag hollow spans, don't fabricate.** Some prose is weak because it has no point to make, and rewording cannot save it. Flag those spans and say what they need (a real claim, a source, a number). Do not invent one.

## The loop

Run this on any text you are editing.

**0. Scope.** Work paragraph by paragraph. Skip code blocks, blockquotes, headings, data, and genuine lists (headings and lists still get the formatting sweep in `references/patterns.md`, section 7). In files, leave frontmatter and link targets alone.

**1. Pre-flag (optional; for whole files and long drafts).** Skip this step for short texts: under a few hundred words you can see every tell yourself. For long texts, run the deterministic pass to narrow attention:

```
python3 scripts/flag_patterns.py <file>     # or: cat text | python3 scripts/flag_patterns.py
python3 scripts/flag_patterns.py --score <file>   # per-paragraph band
```

It returns JSON spans (hedge stems, listicle openers, dash density, filler intensifiers, and so on). These are candidates, not verdicts. The score measures surface tells only, never whether a real claim is present, so a quiet detector never excuses step 2: a clean-looking paragraph can still be hollow.

**2. Judge.** Score each paragraph `strong | moderate | weak | fail`, with a one-line reason. The bar is the hostile-editor test: would this survive a red pen? Does removing it lose anything? When a band or triage call is not obvious, load `references/rubric.md` for the full bands and judgment angles.

**3. Triage** each paragraph below strong:

- **Rewordable**: a real claim is buried under hedging or filler. Rewrite it.
- **Hollow**: weak because there is no actual point. Flag it, don't fabricate.

**4. Rewrite** the rewordable spans, keeping to `references/guardrails.md` (fidelity, over-correction, what not to flag). For a short passage, the two hard rules plus the style defaults below cover the common tells; load `references/patterns.md` when the text is long, when it reports work (reviews, status updates, incident notes: the Report register entry there carries the verb table), or when you sense a tell you cannot name.

**5. Self-score.** Ask two questions of the rewrite: "What still makes this read as AI?" and "Does it state anything not in the source?" Check that it reads naturally when spoken aloud. Scan for reframes that survived across sentence boundaries ("They don't have a hiring problem. They have a standards problem.") and for analogies that fail the permission test (`references/patterns.md`, section 6). Score it against the rubric again.

- Reached strong: lock it in.
- Still below: iterate (back to step 4). Maximum 3 passes total.
- After 3 passes still not strong: keep the best version and flag it ("couldn't reach strong; may need a real claim, not better words").

**6. Deliver** per the mode below. Never quietly polish over a flag: hollow and capped spans are always surfaced, in every mode. Prose that already scores strong is returned unchanged, and a second run on the output must return the same text and the same flags, not new variations.

## Voice calibration

If the user provides a writing sample (their own previous writing), read it before rewriting. Note its sentence lengths, vocabulary, paragraph openings, punctuation, recurring phrases, and transitions, and match those habits instead of merely deleting AI patterns. Do not upgrade casual words or regularize deliberate quirks. A sample outranks this skill's style defaults, including the dash rule: if the sample uses em dashes, keep them at roughly the sample's frequency. Matching the author beats scrubbing the tell.

Voice also has a floor. Sterile, voiceless writing is as obvious as slop. For blog posts, essays, opinion, and personal writing, let the author have opinions, uncertainty, mixed feelings, humor, and uneven rhythm, but never add factual claims to create that personality. For encyclopedic, technical, legal, or reference text, neutral and plain is the correct human voice; do not inject opinions or first person there.

## Delivery modes

- **Pasted text (default).** The user gives text in the conversation. Deliver the final rewrite, a short change log (per changed paragraph: band before and after, what changed), and the flags. The user decides what to accept.
- **File mode.** The user points at a file. Run the loop, rewrite the file in place so it contains only the final text. Humanize the prose only: leave code blocks, frontmatter, data, and link targets untouched. Report a short summary and the flags in the conversation instead of pasting the rewrite.
- **Embedded mode.** Another task is using this skill as one step of a larger job (a PR description, a doc, an email draft). Run the loop internally and output the final text, with any flags as a brief note at the end so the caller can decide. No draft, no change log; the caller wants prose, not ceremony.

In every mode, end the reply after the deliverable, the change log, and the flags. Do not close with offers of optional extras ("Tell me if you want...", "Want me to..."). If information is missing, ask for it as part of the flag; that is the one question the reply may carry.

A correction generalizes. When the user flags one span (a vague metric, a dangling referent, a filler phrase), treat the correction as a rule: find and fix every analogous case in the text, not only the quoted one.

## Style defaults

These settle the conflicts between "be punchy" and "be faithful":

- **No em dashes (—) or en dashes (–) in the final text.** Replace each, in rough order of preference: a period, a comma, a colon, parentheses, or restructure the sentence. Also catch spaced dashes (` — `) and double hyphens (` -- `). Scan the final text before delivering; a hit means it is not done. Only a writing sample that uses them overrides this.
- **Cut filler intensifiers** ("truly", "genuinely", "just", "literally", "simply", "actually" as flavor). "Honestly" and "look" are tells as standalone openers, not mid-sentence. Judge degree adverbs ("very old browsers") case by case; they are often legitimate.
- **Clusters convict, lone tells don't.** One "however" or one short emphatic sentence is normal human writing. Flag when tells pile up in one span.
- **Directness never outranks fidelity.** A punchy rewrite that adds stance or drops a qualifier the author meant is worse than the original.
- **Say each thing once.** No kickers (a punchy closer added for drama), no restating a point in new words, no truisms everyone already accepts.
- **Write for a cold reader.** Assume no context beyond what the text supplies, and never claim more than the data supports.
- **Answer the ask.** Match the requested scope and level of detail. No unsolicited sections, evidence, or extras, and no conclusion added because documents conventionally end with one.
- **Spoken register.** Prefer the wording you would say aloud to a teammate: everyday verbs over formal ones ("kicked off the migration", not "initiated the migration"; "showed", not "demonstrated"), events over records ("timed out three times", not "has 3 recorded timeouts"), people over process nouns ("whoever is on call", not "the incident-response function"), the action over the artifact name ("fuzzed the parser", not "validated the parser with a fuzzing harness"), and "without X" over "with no X" ("finished without issues"). Spell out counts below ten in running prose. Translate a precise count into a proportion when that is clearer ("about half", not "63 of 120"), followed by what it changed; never leave a naked metric without its base and its consequence.
- **Formatting serves structure.** Tables for enumerable facts; italics for a term being defined; backticks for every symbol, path, and env var in technical prose; no `---` separator rules; bold for structure, never for emphasis.
- **No artificial line breaks.** One paragraph, one line; never hard-wrap prose at a fixed column.

## References

Load what the job needs, not everything. For a short text (a paragraph, an announcement, an email), this file alone carries the process and the common tells.

- `references/rubric.md`: the bands, the two tests, the judgment angles, and the rewordable-vs-hollow triage rule. Load it when a band or triage call is not obvious.
- `references/guardrails.md`: fidelity rules, the over-correction anti-patterns, what not to flag, and the human signals to preserve. Load it before rewriting someone else's prose.
- `references/patterns.md`: the full catalogue of AI tells, by category, with fixes. Load it for whole files and long texts, or when you sense a tell you cannot name.
- `references/examples.md`: judged before-and-after cases, including the hard calls. Consult when a rewrite decision is unclear.
