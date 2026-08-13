# Guardrails

Apply these to every rewrite. The goal is to remove AI tells, not to perform humanness. A rewrite that violates these is a failure even if it scores well.

## Fidelity (the prime rule)

- Preserve the original meaning and claims exactly. The rewrite says the same thing the author meant, only clearer and without padding.
- Preserve the information, not the shape. Every claim in the original survives into the rewrite, but depth does not have to be uniform: compress the dull parts, dwell where a human would, merge or split paragraphs freely. When keeping the information and mirroring the structure pull in different directions, the information wins.
- You may subtract (hedging, filler, dead transitions) and sharpen (make an existing claim concrete, surface the point that was buried).
- You may not add a claim, opinion, statistic, example, or stance that was not already in the source. If the point is not there, that is a hollow span: flag it, don't fill it.
- No invented numbers, names, or mechanisms. If the source never said "microseconds", "Postgres", or "JSON/CSV", you may not put it in the rewrite, even when it would sound sharper. Specificity without source grounding is fabrication. Swapping a vague claim for a specific one is allowed only when the specific comes from the source or from the user.
- Never oversell. The rewrite may not state a claim more strongly than the source does; sharpening surfaces a buried point, it does not upgrade one.
- Stage precision is fidelity. An idea, a proposal, a prototype, a merged change, a release, active use, and broad adoption are different claims; never write a later stage than the source shows.
- Do not undersell either. Needless caveats and defensive disclaimers weaken an accurate claim; write the strongest sentence the source supports and let the stated scope carry the boundary.
- Plain renaming is not fabrication when the claim keeps its strength: "validated with a 200-case regression suite" can become "tested against 200 cases", and "0 outages" can become "no outages". Naming what the source never named (the unit behind "a backlog of 55", the ask behind "a process gap") is fabrication; flag it and ask.
- Opinions and reactions are voice, not facts: where the content calls for voice (see SKILL.md), you may keep or restore stance, but never new factual claims. In fiction, invented detail is the job; this rule governs everything else.

## Over-correction anti-patterns (never inject these)

The classic failure of humanizing tools is trading AI slop for a louder slop. Do not introduce any of:

- **Forced contrarianism and hot takes:** "Everyone says X, but they're wrong" (unless the source argued this).
- **Dash theatrics:** dramatic dashes manufacturing emphasis the content does not earn.
- **Fake first person:** "I've seen this a hundred times", "In my experience" inserted into prose that had no author presence.
- **Performed candor:** "Let's be honest", "let's be real", "here's the thing".
- **Manufactured stakes:** "In a world where...", "Now more than ever", "The stakes have never been higher."
- **Rhetorical-question openers:** "What if I told you...?", "Ever wondered why...?"
- **Intensifier padding:** "genuinely", "truly", "honestly", "literally" as flavor.
- **Staccato drama:** stacked short fragments and manufactured punchlines to sound punchy.
- **Checklist writing:** prose that reads like it is dodging a banned-word list. Do not force jokes or slang to sound human, avoid the exact word when no cleaner substitute exists, or make every sentence punchy and every paragraph one line. Write normally first, then remove what sounds machine-made.

The bar is a thinking author, not a loud one.

## What not to flag (false positives)

A clean human writer can hit several catalogued patterns without any AI involvement. Before rewriting, check you are not gutting legitimate prose. These are not reliable indicators on their own:

- **Perfect grammar and consistent style.** Polish does not equal AI.
- **Mixed casual and formal registers.** Often a person in a technical field, a young writer, or neurodivergent prose habits.
- **Bland prose without specific tells.** Generic dryness is just dry writing.
- **Formal or academic vocabulary.** AI overuses specific fancy words, not all fancy words. Do not flatten "ostensibly" or "constituent".
- **Common transition words in isolation.** "Additionally" and "however" are AI-coded only when piled up.
- **Curly quotes alone.** Most editors auto-curl by default.
- **Letter-style openings and closings.** Salutations and sign-offs predate chatbots by centuries. "I hope this finds you well" in a real email is correspondence, not pasted chatbot output.
- **Em dashes alone in source text.** Many editors and journalists use them. They are evidence only when paired with formulaic rhythm. (The final rewrite still removes them per the style defaults; just do not treat a dash in the source as proof of AI.)
- **Mid-sentence ellipses.** An ellipsis inside a sentence usually marks elided source text; deleting it silently extends the claim to words the source never attested. Leave it unless the user asks.
- **One short emphatic sentence.** Humans land points with clipped sentences. Flag staccato only when several fragments run in a row.
- **"Honestly" or "look" mid-sentence.** Ordinary in casual writing. The tell is the standalone theatrical opener.
- **Unsourced claims.** Most of the web is unsourced.
- **Correct, complex formatting.** Templates produce clean output.
- **Secondhand text.** Never rewrite watched phrases inside quotations, titles, proper names, or examples where the phrase is being discussed rather than used.

When in doubt, look for clusters of tells, not isolated ones. A single em dash means nothing; em dashes plus rule-of-three plus "vibrant tapestry" plus a "Conclusion" section is a confession.

## Signs of human writing (preserve these)

When you see these, lean toward leaving the prose alone. They are evidence of a real person writing, and over-editing destroys what makes the piece sound human:

- **Specific, unusual, hard-to-fabricate detail.** A real address, a weird quote, "the lawyer who used to work upstairs from my dentist". Models round off specifics; humans hoard them.
- **Mixed feelings and unresolved tension.** "I think this is mostly good, but it bothers me, and I can't fully explain why."
- **Dated, era-bound references.** Slang and in-jokes that map to a specific year and subculture.
- **First-person editorial choices the writer can defend.**
- **Variety in sentence length.** Real writing alternates short and long.
- **Genuine asides, parentheticals, and self-corrections.** Models rarely interrupt themselves.
- **Text written before ChatGPT's public launch (November 30, 2022).** With rare exceptions, it is not AI-written.

## Idempotence

- If a paragraph already scores strong, return it unchanged. The skill must do nothing to good prose.
- Running the skill twice on the same text must produce the same result the second time: strong prose stays untouched, and hollow or capped spans surface the same flags instead of getting new rewrites.

## When in doubt

Prefer the smaller edit. The best fix is usually deletion of the hedge plus nothing else. If you cannot improve a sentence without inventing content, you have found a hollow span: flag it and move on.
