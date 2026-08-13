# Rubric

Score a single paragraph on humanness: does this sound like a thinking author with a point of view, or generic AI-flavored prose that could appear in any post on the topic?

## Bands (0-100)

- **strong (80-100):** specific, has a point of view, survives a hostile editor's red pen. A real claim someone could disagree with. Removing it would lose something.
- **moderate (50-79):** readable but generic in spots. A real point is present but softened by hedging or filler.
- **weak (20-49):** pattern-matchable AI prose. Removing it loses nothing. The sentence is shaped like an argument but is not making one.
- **fail (0-19):** pure scaffolding language: listicle stems, empty hedging, transitions with no content between them.

## The two tests

1. **Hostile-editor test:** would a sharp editor leave this sentence on the page, or red-pen it as padding?
2. **Removal test:** if you deleted this sentence, would the reader lose anything? If nothing is lost, the sentence is slop regardless of how polished it sounds.

## Indicators that lower the band

- Empty hedging: "it's worth noting", "that said", "arguably" used to avoid committing.
- Listicle stems with no point of view: "There are several key factors..." followed by the obvious.
- Smooth transitions that hide the absence of a claim: "Moreover", "Furthermore" gluing together sentences that do not advance an argument.
- Generic filler: intensifiers, manufactured stakes ("in today's fast-paced world"), throat-clearing openers.
- Truisms and restatements: a claim no reader could disagree with, or the same point said twice in different words.

For the full taxonomy, see `patterns.md`. The detector surfaces candidates by surface pattern; this rubric assigns the band. Hollowness is invisible to any regex; only the removal test catches it.

## The judgment angles

Surface tells are half the judgment. A paragraph can be mechanically clean, with zero hedging and no buzzwords, and still be slop because it has nothing to say. When the detector is quiet, judge on these angles before passing it:

- **Specificity:** does it commit to a concrete claim (a name, number, mechanism, consequence), or only gesture at one? "Significant improvement" fails; "latency dropped from 340ms to 90ms" passes. A naked metric fails too: a number without its base and consequence ("cut 23 alerts") leaves the reader asking "of what?" and "why does that matter?". Specificity judges the claim, not the wording; check Register before banding strong.
- **Register:** would the author say this line aloud to a teammate? Formal verbs ("executed", "verified"), records instead of events ("has 5 recorded crashes" for "crashed five times"), process nouns instead of people ("the review pipeline"), and artifact names where an action belongs ("a benchmark harness" where "benchmarked it" belongs) read as a report, not a person. Specific but stiff caps at moderate.
- **Consequence:** does the text reach an effect, or stop at activity? "Closed 19 tickets" and "ran the analysis" report effort; ask "so what?" until the sentence says what changed for the user, the reader, or the team because of it. Activity without effect is inventory, not a claim.
- **Restraint:** is the emphasis earned or manufactured? Forced contrast, dramatic fragmentation, and hot takes are negative substance: louder, not stronger.
- **Voice:** is there a thinking author reacting to the facts, or a neutral narrator restating them? Voice is not personality theatrics; it is having a point.
- **Directness:** statements or announcements? Text that keeps introducing itself never gets anywhere.
- **Rhythm:** varied or metronomic? Uniform sentence lengths and identical paragraph endings read as generated.
- **Trust:** does it respect the reader or hand-hold, soften, and justify every step?
- **Density:** is anything cuttable without loss? Padding lowers the band even when each sentence looks fine.

These angles separate moderate from strong.

## Triage rule (for anything below strong)

- **REWORDABLE:** the paragraph has a real claim buried under hedging or filler. The fix is subtraction plus sharpening. Rewrite it.
- **HOLLOW:** the paragraph is weak because it has no actual point to make. Nothing is lost if removed. Rewording cannot fix an absent claim. Flag it; do not invent a claim to fill the hole.

The single most important judgment call this skill makes is rewordable vs. hollow. When unsure, apply the removal test: if deleting the paragraph entirely would cost the reader nothing, it is hollow.
