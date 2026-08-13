# Pattern catalogue

Every tell, grouped by category, with the fix. LLMs guess what should come next, so the output tends toward the most statistically likely result that applies to the widest variety of cases. These patterns are what "most likely, widest variety" looks like on the page.

A note before hunting: a single hit is a candidate, not a conviction. Real writers use transitions, short sentences, and the occasional intensifier. See `guardrails.md` for what not to flag. Clusters convict.

## Contents

1. [Openers and filler](#1-openers-and-filler)
2. [Formulaic structures](#2-formulaic-structures)
3. [Word-level tells](#3-word-level-tells)
4. [Content-level tells](#4-content-level-tells)
5. [Voice and stance](#5-voice-and-stance)
6. [Analogies and metaphors](#6-analogies-and-metaphors)
7. [Formatting and mechanics](#7-formatting-and-mechanics)
8. [What the detector script catches](#8-what-the-detector-script-catches)

## 1. Openers and filler

### Throat-clearing openers

Announcement phrases before the point. Cut them and state the point.

- "Here's the thing:" and any "here's ..." announcement ("here's what", "here's why", "here's the problem though")
- "The uncomfortable truth is", "The truth is,", "The real [X] is"
- "It turns out"
- "Let me be clear", "I'll say it again:", "I'm going to be honest"
- "Can we talk about", "Here's what I find interesting"

### Fake-candid hooks

A theatrical pause to manufacture intimacy before an ordinary claim: "Honestly?", "Look,", "Let's be honest", "Let's be real", "Real talk", "Truth be told". Manufactured sincerity belongs here too: "I promise", "They exist, I promise". A person being honest just says the thing. The word "honestly" mid-sentence in casual prose is fine; the standalone opener is the tell.

**Before:** "Is it worth the price? Honestly? It depends on how often you'll use it."

**After:** "Whether it's worth the price depends on how often you'll use it."

### Signposting and announcements

Announcing what the text is about to do instead of doing it: "Let's dive in", "let's explore", "let's break this down", "here's what you need to know", "without further ado", "buckle up", "stay tuned", "read on".

**Before:** "Let's dive into how caching works in Next.js. Here's what you need to know: Next.js caches data at multiple layers, including request memoization, the data cache, and the router cache."

**After:** "Next.js caches data at multiple layers: request memoization, the data cache, and the router cache."

### Meta-commentary

The text narrating its own structure: "Plot twist:", "Spoiler:", "Hint:", "Let me walk you through", "In this section, we'll", "As we'll see", "I want to explore", "The rest of this essay explains", "But that's another post", "You already know this, but", "X is a feature, not a bug", "dressed up as". Delete; let the text move.

### Emphasis crutches

Telling the reader something matters instead of showing it: "Full stop.", "Period.", "Let that sink in.", "Make no mistake", "This matters because", "Here's why that matters", "This is genuinely hard", "This is what X actually looks like".

### Filler phrases

Longer forms of shorter words. Compress them.

| Before | After |
|---|---|
| In order to achieve this goal | To achieve this |
| Due to the fact that it was raining | Because it was raining |
| At this point in time | Now |
| In the event that you need help | If you need help |
| The system has the ability to process | The system can process |
| The migration finished with no issues | The migration finished without issues |
| It is important to note that the data shows | The data shows |
| When it comes to X | (name X directly) |
| At the end of the day / The reality is | (cut) |

### Empty hedging and stacked hedges

Hedges that avoid committing: "it's worth noting", "it's important to remember", "that said", "needless to say", "arguably", "of course". Stacked qualifiers where zero or one belong: "might possibly", "could potentially perhaps".

**Before:** "It could potentially possibly be argued that the policy might have some effect on outcomes."

**After:** "The policy may affect outcomes."

### Filler intensifiers

Adverbs as flavor: "just", "truly", "genuinely", "honestly", "literally", "simply", "basically", "essentially", "actually", "undoubtedly", "certainly", "definitely", "deeply", "inherently", "inevitably", "interestingly", "importantly", "crucially". Cut these when they add no meaning. (For "honestly", see Fake-candid hooks.) Degree intensifiers ("very old browsers", "really slow") are often legitimate; judge those by whether they carry information.

### Manufactured stakes

Borrowed urgency the content did not earn: "In today's fast-paced world", "in today's digital landscape", "now more than ever", "more important than ever", "In a world where", "The stakes have never been higher".

### Vague quantifiers

A quantity word standing in for a real list or number: "a wide variety of", "a broad range of", "numerous", "countless", "myriad", "a host of", "a plethora of", "various different". If the source names the items, name them. If it never does, the quantifier is concealing that there is no list; that span may be hollow.

### Listicle stems

Announcing structure instead of making a point: "There are several key factors to consider", "Here are a few things to keep in mind". If the factors arrive in the next sentence, delete the stem and lead with them. If they never arrive, the span is hollow.

### Dead transitions

"Moreover", "Furthermore", "In addition", "Additionally" gluing together sentences that do not advance an argument. One transition in real prose is fine; the tell is transitions between non-claims, or several piled up. After cutting one, start the next sentence with its noun or verb; if the sentences no longer connect, the transition was hiding that.

### Wrap-up scaffolding and generic conclusions

"In conclusion", "To sum up", "In summary", "All in all", "the key takeaway is". And the vague upbeat ending: "The future looks bright", "Exciting times lie ahead", "a major step in the right direction". End on the last concrete fact instead of a send-off. If the source states real plans, use those.

### Lead-in labels and false headings

A label where a sentence should be: "Bottom line:", "Key insight:", "The result:", "Net-net:", "TL;DR:" in running prose, or a bolded line acting as a heading for one sentence. Cut the label and state the point. A real heading introduces a section, and bold that names a list item or a process step ("**0. Scope.**") is structure; the tell is bold standing in front of a lone prose sentence that can speak for itself.

### Truisms

Statements everyone already accepts: "navigation is fundamental", "testing is important", "communication is key". If no reader could disagree, the sentence carries no information. Cut it or replace it with the specific point it was standing in front of.

### Redundancy

The same point restated in different words across neighboring sentences or paragraphs. Restating feels thorough and reads as padding. Say it once, in the strongest spot, and move on.

## 2. Formulaic structures

### Binary contrasts and reframes

The telegraphed reversal: dismiss, minimize, or question X, then assert Y as the reveal. This is a hard ban; do not invent a weaker idea just to correct it, and do not use contrast as a shortcut to sound decisive.

| Pattern | Problem |
|---|---|
| "Not because X. Because Y." | Telegraphed reversal |
| "[X] isn't the problem. [Y] is." | Formulaic reframe |
| "The answer isn't X. It's Y." | Predictable pivot |
| "It feels like X. It's actually Y." | Setup and reveal cliche |
| "The question isn't X. It's Y." | Rhetorical misdirection |
| "stops being X and starts being Y" | False transformation arc |
| "is about X but not Y" | False distinction |
| "Forget X. Focus on Y." / "Less X, more Y." | Reframe shortcut |
| "X is dead. Y is the future." | Fake obsolescence |
| "It was never about X. It was always about Y." | Retroactive reveal |
| "No X. Just Y." | Dismissal fragment |

The reframe fails with or without the word "not", and at every size. Across sentence boundaries: "Most teams think they have a hiring problem. They have a standards problem." As a rhetorical question: "Is this a productivity problem? No. It's an attention problem." As a heading: "Not a tool. A system.", "From chaos to clarity", "What actually matters". Soft setups are the same move: "While X may seem...", "At first glance...", "On the surface...", "Most people think...", "The common assumption is...", "Conventional wisdom says...", "X gets all the attention...". The pivot words that perform it ("but", "yet", "actually", "instead", "in reality", "the truth is", "what matters is", "the real/deeper/hidden/overlooked X") are fine in normal writing and fail only when they flip a strawman.

**Fix:** delete the rejected half, then sharpen the surviving claim into a direct sentence. "It is not about the prompt. It is about the context." becomes "It is about the context.", which becomes "Context controls the output."

**Allowed contrast:** correcting a specific factual mistake, scope, date, number, or name. "The meeting is on Tuesday, not Thursday." "The file is 12 MB, not 12 GB." Contrast for drama, persuasion, or manufactured insight is not.

### Negative parallelism and tailing negations

"Not only X but also Y" inflates one idea into two. "It's not just X, it's Y" is the same rhythm. Tailing-negation fragments ("no guessing", "no wasted motion") tacked onto a sentence instead of written as a real clause belong here too. Prefer the "X without Y" form ("stays fresh without rebuilding") over the "X. No Y. No Z." form.

**Before:** "The options come from the selected item, no guessing."

**After:** "The options come from the selected item without forcing the user to guess."

### Negative listing

Listing what something is not before revealing what it is: "It wasn't X. It wasn't Y. It was Z." A rhetorical striptease. State Z; the reader does not need the runway.

### Rule of three

Forcing ideas into groups of three to appear comprehensive: "fast, reliable, and scalable", "innovation, inspiration, and industry insights". Two items usually beat three. Use the number of items the content has.

**Before:** "The event features keynote sessions, panel discussions, and networking opportunities. Attendees can expect innovation, inspiration, and industry insights."

**After:** "The event has keynote talks and panels, with time to network."

### False ranges

"From X to Y" where X and Y are not on a meaningful scale: "from the singularity of the Big Bang to the enigmatic dance of dark matter". List the actual topics.

### Dramatic fragmentation and manufactured punchlines

Stacked short fragments for manufactured drama: "[Noun]. That's it. That's the [thing].", "X. And Y. And Z.", "It had no preference. No aesthetic prior. No nostalgia." One short sentence lands a point; a run of them sounds engineered. "Not always. Not perfectly." is the same shape doing double duty: hedging disguised as reassurance. The same goes for pull-quote sentences: if it sounds like a quotable, rewrite it as a working sentence.

Kickers belong here too: state the fact once and never add a punchy closer for drama. And marketing slogans posing as summaries ("Smaller, faster, fresher", "built for scale") summarize nothing; cut them. Stacked one-line paragraphs engineered to look profound (or to trip a feed's "see more" fold), and a final line isolated for effect, are the paragraph-scale version; fold them back into working prose.

### Transformation chains

"X becomes Y. Y becomes Z." False momentum through repeated conversion: "Friction becomes flow. Flow becomes speed."

### Corrective reveals

"You've been told X. Here's the truth: ..." Contrarian posturing that frames an ordinary point as forbidden knowledge.

### Forced cohesion

Manufactured profundity binding two ideas: "You can't have one without the other."

### Aphorism formulas

Reusable profundity templates: "X is the language of Y", "X is the currency of Z", "X is not a tool but a mirror", "X becomes a trap". Replace the formula with the concrete claim it gestures at.

**Before:** "Symmetry is the language of trust."

**After:** "Symmetric layouts often feel more predictable to users."

### Engagement-bait formulas

Feed-ready templates that manufacture insight: a strawman or a cinematic frame, then a vague virtue as the reveal. The fix is the same for all of them: state the specific claim, or cut the line if there is none.

| Formula | Example |
|---|---|
| "In a world where [change], [virtue] becomes [advantage]." | "In a world where everyone has AI, taste becomes the only edge." |
| "Most people [lazy thing]. The few who win [disciplined thing]." | "Most people use AI to move faster. The few who win use it to think deeper." |
| "Stop [old habit]. Start [new habit]." | "Stop collecting prompts. Start building workflows." |
| "It's not [X]. It's not [Y]. It's [Z]." | "It's not speed. It's not talent. It's consistency with feedback." |
| "If you're not [doing X], you're already [behind]." | "If you're not using AI to review your work, you're already behind." |
| "The real [work] isn't [what everyone sees]. It's [what masters do]." | "The real AI work isn't typing prompts. It's deciding which answers to keep." |
| "You don't need more [resources]. You need [virtue]." | "You don't need more AI tools. You need one process you repeat." |
| "It's never been easier to [X]. It's never been harder to [Y]." | "It's never been easier to create content. It's never been harder to be remembered." |
| "Here's the truth: [obvious statement]." | "Here's the truth: AI won't fix a boring offer." |
| "What nobody tells you is [obvious statement]." | "What nobody tells you is that AI amplifies the work you were avoiding." |

The two-part versions of several of these have their own entries: the pivot in Binary contrasts, the "It wasn't X. It wasn't Y." striptease in Negative listing, and the truth-reveal in Corrective reveals.

### Formulaic constructions

Narrative and indirection templates. "By the time X, I was Y." reads as a storytelling template. "X that isn't Y" dodges the direct claim: say "the process is broken" instead of "a process that isn't working".

### Rhetorical setups

"What if I told you", "Ever wondered why", "Have you ever", "Think about it:", "Here's what I mean:", "And that's okay." Questions as engagement bait, previews that repeat the point, permission the reader did not ask for. Make the point and let readers draw conclusions. The question-then-instant-answer fragment ("The result? A better team.", "The best part? It's free.") is the compressed form; write the claim as a sentence.

### Persuasive authority tropes

Pretending to cut through noise to a deeper truth: "The real question is", "at its core", "in reality", "what really matters", "fundamentally", "the deeper issue", "the heart of the matter". The sentence that follows usually restates an ordinary point with extra ceremony.

### Vague declaratives

Announcing importance without naming the thing: "The reasons are structural", "The implications are significant", "The stakes are high", "This is the deepest problem". Replace with the specific reason, implication, or stake, or cut. Vague outcomes are the same tell with the object missing: "more dependable results", "less manual maintenance", "better decisions" say nothing until they name what became dependable, whose work changed, or which decision improved. The same goes for effects without causes: soft causal verbs ("drives", "shapes", "underpins", "fuels") assert a connection without describing it; name the mechanism or drop the claim.

## 3. Word-level tells

### AI vocabulary

Words that spike in post-2023 text, especially when they co-occur: delve, tapestry (abstract), testament, realm, landscape (abstract), pivotal, crucial, key (adjective), vibrant, showcase, underscore (verb), highlight (verb), interplay, intricate/intricacies, foster, garner, enduring, enhance, align with, valuable, emphasizing. None of these is banned alone; a cluster is a confession.

**Before:** "An enduring testament to Italian colonial influence is the widespread adoption of pasta in the local culinary landscape."

**After:** "Pasta dishes, adopted under Italian colonial influence, remain common."

### Business jargon

| Avoid | Use instead |
|---|---|
| Navigate (challenges) | Handle, address |
| Unpack (analysis) | Explain, examine |
| Lean into | Accept, embrace |
| Landscape (context) | Situation, field |
| Game-changer | Significant |
| Double down | Commit, increase |
| Deep dive | Analysis, examination |
| Take a step back | Reconsider |
| Moving forward | Next, from now on |
| Circle back | Return to |
| Move the needle | Improve results |
| Low-hanging fruit | Easy wins |
| On the same page | Aligned, agreed |

### Marketing register

Words that almost never appear in honest prose: "empower", "seamless", "frictionless", "synergy", "cutting-edge", "state-of-the-art", "best-in-class", "world-class", "supercharge", "turnkey", "paradigm shift", "next-generation". These convict on their own. Ambiguous rider words ("leverage", "robust", "unlock", "harness", "streamline", "elevate") are common in real engineering writing ("we leverage connection pooling", "robust error handling") and only count when they share a sentence with the marketing register. Fix by keeping the mechanism and peeling off the uplift.

**Before:** "Our platform empowers teams to leverage cutting-edge tooling for a seamless workflow. It runs your existing CI config and caches build artifacts across branches."

**After:** "The platform runs your existing CI config and caches build artifacts across branches."

### Copula avoidance

Elaborate substitutes for "is", "are", "has": "serves as", "stands as", "boasts", "features", "offers", "represents", "marks", "plays a role in", "helps to", "aims to", "seeks to". Use the plain verb: is, has, uses, gives, shows, causes, changes, removes, adds.

**Before:** "Gallery 825 serves as LAAA's exhibition space and boasts over 3,000 square feet."

**After:** "Gallery 825 is LAAA's exhibition space and has over 3,000 square feet."

### Elegant variation (synonym cycling)

Rotating synonyms to avoid repetition: "The protagonist... The main character... The central figure... The hero..." Pick one name and repeat it; repetition of the right word is not a flaw.

### Hyphenated pair overuse

AI hyphenates compounds uniformly, including after the noun ("the report is high-quality"). Humans keep the hyphen when the compound comes before the noun ("a high-quality report") and usually drop it otherwise ("the report is high quality"). The usual suspects: third-party, cross-functional, client-facing, data-driven, decision-making, well-known, high-quality, real-time, long-term, end-to-end.

Coined compounds and borrowed metaphors are worse: shorthand you would not say out loud makes the reader decode instead of read. Unpack them into plain clauses:

| Coined | Plain |
|---|---|
| "load-bearing" | "things break without this check" |
| "retry-safe" | "safe to run twice" |
| "cache-backed" | "reads from the cache first" |
| "a non-issue" | "not a problem" |

If you wouldn't say it out loud to a teammate, rewrite it.

### Nominalizations

A verb frozen into a noun plus a filler verb: "make a decision" (decide), "perform an analysis" (analyze), "provide an explanation" (explain), "conduct a review" (review), "achieve a reduction" (reduce). Use the verb.

### Report register

Prose that records events the way a report files them, not the way a person tells them. Every number can check out and the line still reads as machine output; density of facts does not excuse the wording. Five habits give it away.

**Formal verbs.** Prefer the verb you would say to a teammate:

| Report | Spoken |
|---|---|
| performed the migration | ran the migration |
| discarded the initial approach | dropped the first approach |
| demonstrated | showed |
| conducted the review | did the review |
| verified against | tested against |
| secured buy-in from the teams | got the teams on board |
| identified the root cause | found the cause |
| restored service | brought it back up |

**Records instead of events.** "The job shows 6 recorded failures" describes the database row; "the job failed six times" describes what happened. "Zero regressions are on record for the quarter" hides the same event: "nothing regressed all quarter." The tell is the record standing in for the event, not a qualifier that scopes a count: "25 recorded incidents" limits the claim to what the record shows; keep it.

**Process nouns instead of people.** "Documented the workaround for the onboarding process" hands the work to an abstraction; "for the next engineer who joins" hands it to a person. False agency in section 5 is the same pattern seen from the actor's side.

**The artifact instead of the action.** "Validated the parser with a fuzzing harness" names the artifact; "fuzzed the parser" says what was done. Keep the artifact's name only when the reader needs to go find it.

**Packed noun phrases.** An event compressed into a compound label: "a 90-item defect backlog" packs the events and their unnamed unit into one modifier; "an integration gap" hides the missing feature behind it. Unpack the label into the event, and when the source never names what the label counts or stands for, flag it and ask (see guardrails.md).

### Noun stacks and stacked modifiers

Three or more nouns piled into one phrase ("customer feedback response time improvement plan") force the reader to parse backward. Unpack with prepositions and verbs: "a plan to respond to customer feedback faster". The same goes for three adjectives stacked before one noun; keep the one that matters.

### Acronym soup and specialist jargon

Acronyms and domain terms a reader outside the specialty cannot expand make the text unreadable to anyone but the author's team. "Huge stack trace" beats "SIGSEGV stack trace". Expand an acronym on first use or pick the plain word; keep a term only when the audience demonstrably shares it.

### Scare quotes

Quotation marks used to signal distance or irony rather than quotation: the "fix", their "process". Either mean the word, and drop the quotes, or say what you mean instead. Quoting an actual phrase someone used is fine.

### Lazy extremes

"every", "always", "never", "everyone", "nobody" doing vague work. False authority. Use the specific scope you can defend.

## 4. Content-level tells

### Inflated significance

Puffing up importance with claims about legacy and broader trends: "marking a pivotal moment", "underscores its importance", "reflects broader trends", "setting the stage for", "an indelible mark", "key turning point", "symbolizing its enduring legacy", "a vital role", "a focal point", "deeply rooted", "stands as a reminder", "the evolving landscape".

**Before:** "The institute was officially established in 1989, marking a pivotal moment in the evolution of regional statistics."

**After:** "The institute was established in 1989."

### Notability name-dropping

Hitting the reader over the head with claims of coverage: "cited in The New York Times, BBC, Financial Times, and The Hindu", "maintains an active social media presence". Keep the citation that has real context; drop the list.

### Superficial -ing analyses

Present-participle phrases tacked on for fake depth: "...highlighting the region's diversity", "...ensuring reliability", "...showcasing the community's deep connection to the land". Watch the stems: highlighting, underscoring, emphasizing, ensuring, reflecting, symbolizing, contributing to, cultivating, fostering, encompassing, showcasing. Cut the tack-on or turn the real content into its own plain sentence.

### Promotional language

Advertisement adjectives in what should be neutral prose: "nestled", "breathtaking", "stunning", "vibrant", "rich cultural heritage", "renowned", "must-visit", "groundbreaking", "profound", "exemplifies", "commitment to", "natural beauty", "in the heart of".

**Before:** "Nestled within the breathtaking region of Gonder, the town stands as a vibrant community with a rich cultural heritage."

**After:** "The town is in the Gonder region."

### Weasel attributions

Opinions attributed to vague authorities: "Experts argue", "Industry reports suggest", "Observers have cited", "Some critics argue". If a real source exists, name it. Never invent one; an unsupported claim gets cut, not decorated.

### Unclear referents

"This", "it", "the system", "the result", "the change" where the reader could ask "which one?". Generated prose leans on pronouns because it already knows the referent; a cold reader does not. Name the product, workflow, person, or outcome, and repeat the name instead of rotating substitutes.

### Detail dumps

Listing implementation or process detail because the source had it, not because the reader needs it. A detail earns its place when it explains a result, a constraint, a design choice, a risk, or a cost; plumbing that explains nothing is padding with a technical accent. Uniform depth is the same failure at document scale: every item gets equal coverage regardless of importance. Compress the routine, dwell on what mattered.

### Formulaic challenges sections

"Despite its X, [subject] faces several challenges... Despite these challenges, [subject] continues to thrive." Keep the concrete problems, cut the arc.

### Over-delivery

Answering more than was asked. Machine thoroughness produces unsolicited evidence, extra sections, a conclusion added because documents conventionally have one, and detail past the requested level; a human answers the question.

### Activity without consequence

Actions and artifacts listed without what changed because of them: a report of effort shaped like a result. Ask "so what?" until the sentence reaches a real effect, what a reader, user, or team can now do. If no effect exists in the source, the span is hollow, not rewordable.

### Cutoff disclaimers and speculative gap-filling

Two related tells. Hard disclaimers left in the text: "as of my last update", "based on available information". And gap-filling, where the model writes a paragraph about not finding a source and then invents plausible filler: "maintains a low profile", "keeps personal details private", "likely grew up in". Say what is not known, or cut the sentence. Never dress a guess up as fact.

## 5. Voice and stance

### Passive voice and subjectless fragments

"Mistakes were made", "The decision was reached", "No configuration file needed", "The results are preserved automatically". Find the actor and put them at the front: "You do not need a configuration file. The system preserves the results."

### False agency

Inanimate things doing human verbs, which lets the writer avoid naming the actor: "the complaint becomes a fix", "the decision emerges", "the culture shifts", "the data tells us", "the market rewards". Name the human. "The team fixed it that week" beats "the complaint becomes a fix". If no specific person fits, "you" puts the reader in the seat.

### Narrator-from-a-distance

Floating above the scene: "Nobody designed this.", "People tend to...", "This happens because...". Put the reader in the room: "You don't sit down one day and decide to..." beats "Nobody designed this."

### Sycophancy

"Great question!", "You're absolutely right!", "That's an excellent point". Cut the flattery; respond to the content.

### Chat artifacts

Chatbot correspondence pasted as content: "I hope this helps!", "Certainly!", "Would you like me to expand on any section?", "Let me know if...", "I'd be happy to help", "I hope this email finds you well". Delete; keep only the content.

### Self-reference

Text referring to itself instead of its subject: "This PR adds...", "This doc explains...", "This change fixes...", "it does...", "this section covers...". Describe the thing: not "This PR adds retry logic" but "Retries now use exponential backoff". The reader is already looking at the text; tell them about the subject. Instructions that must point at themselves ("this rubric assigns the band") are scope statements, not tells.

## 6. Analogies and metaphors

Default: none. Generated prose reaches for imagery when the claim is thin; the literal sentence is usually shorter and clearer. Do not explain ordinary ideas through metaphor, decorate clear points with imagery, or use metaphors as personality.

### The permission test

Use an analogy only when all five hold: the subject is unfamiliar, abstract, or technical; the analogy makes it easier to understand; it is shorter than the literal explanation; it is exact enough not to mislead; and the sentence still sounds normal aloud. If any test fails, write literally.

### The budget

Zero analogies under 800 words. At most one from 800 to 1,500 words, and one per 1,500 words beyond that, always subject to the permission test. Never more than one in a section, never stacked, never extended across paragraphs unless the user asked for that style.

### Banned setups

"Think of it as", "imagine", "picture", "it's like", "it's kind of like", "as if", "as though", "the X of Y", "works like", "acts like", "functions as", "a bridge between", "a lens for", "a mirror of", "a roadmap for", "the engine of", "the fuel for", "the backbone of", "the foundation of", "the fabric of", "the heartbeat of", "the DNA of", "the glue that holds".

### Banned metaphor families

Unless the subject is literal: journeys for growth, battlefields for work, machines for people, architecture for ideas, ecosystems for business, engines or fuel for motivation, maps or compasses for strategy, signal and noise outside actual signals, toolboxes, icebergs, bridges, north stars, flywheels, scaffolding, plumbing, gardening, chess, sports, puzzles.

### Metaphor verbs for abstract work

Do not use these for ideas, writing, strategy, products, decisions, organizations, or emotions: sanded down, bolted on, stripped back, stitched together, woven, layered, carved out, baked in, injected, fueled, sparked, anchored, framed, mapped, distilled, unpacked, crystallized, sharpened, surfaced, amplified, channeled, threaded, sculpted, molded, cemented, bridged. Use the literal verb: cut, added, removed, changed, joined, caused, showed, explained, reduced, clarified, fixed, named, listed, compared, chose, rejected.

### The audit

Before delivering, search the text for: like, as if, as though, imagine, picture, works like, acts like, functions as, serves as, lens, bridge, roadmap, engine, fuel, foundation, fabric, glue. Every hit either passes the permission test or gets rewritten literally.

**Before:** "Your onboarding is a leaky bucket."

**After:** "Users leave during onboarding." (Sharper still when the source has the data: "42% of users leave on step 2.")

## 7. Formatting and mechanics

### Em and en dashes

The best-known tell. As evidence that text is AI-written, dashes count only in clusters with other tells (see guardrails.md). The style rule stands on its own: the final text contains no em dashes (—) or en dashes (–). Replace each, in rough order of preference: a period (new sentence), a comma (tight aside), a colon (introducing an explanation), parentheses (a true aside), or restructure. Catch spaced dashes (` — `) and double hyphens (` -- `) too. Scan the final text for `—` and `–` before delivering. The one exception: a user writing sample that uses them (see voice calibration in SKILL.md).

**Before:** "The new policy — announced without warning — affects thousands of workers."

**After:** "The new policy, announced without warning, affects thousands of workers."

### Boldface overuse

Mechanical emphasis on phrases: "**OKRs**, **KPIs**, and the **Business Model Canvas**". Unbold; the words carry the meaning.

### Inline-header bullet lists

Bullets that start with a bolded label and a colon, restating the label in the sentence: "- **Performance:** Performance has been enhanced...". Merge into prose or write real list items.

### Title Case in headings

"## Strategic Negotiations And Global Partnerships" reads as generated. Use sentence case.

### Emojis as decoration

Emojis on headings and bullets (🚀, 💡, ✅) are chatbot varnish. Remove them.

### Curly quotation marks

Curly quotes (“...”) instead of straight quotes ("...") in plain-text or markdown contexts. Weak alone (many editors auto-curl); counts inside a cluster.

### Fragmented headers

A heading followed by a one-line warm-up that restates it ("## Performance" then "Speed matters.") before the real content. Delete the warm-up.

### Diff-anchored writing

Docs or comments narrating a change instead of describing the thing as it is: "This function was added to replace the previous approach...". Unless the document is version-scoped (changelog, release notes, migration guide), describe the present: "This function uses a hash map for O(1) lookups."

### Sentence starters

Sentences opening with What/When/Where/Which/Who/Why/How as a crutch ("What makes this hard is...") read as templates; lead with the subject ("The constraint is..."). Paragraphs starting with "So", sentences starting with "Look,": cut. Occasional Wh- openers are normal; the tell is the habit.

### Rhythm

Three consecutive sentences of the same length read as metronomic; break one. Every paragraph ending on a punchy one-liner reads as engineered; vary endings. (For question-then-instant-answer, see Rhetorical setups.)

### Markdown separators

Horizontal rules (`---`) between sections are decoration; headings and paragraphs already carry the structure. Remove them. Two exceptions are syntax, not separators: frontmatter delimiters, and a hyphen line directly under a title (a setext heading). Leave those, or convert the setext form to a `#` heading.

### Telegraphic headlinese

Compressed headline grammar in prose or headings: "Fix: cache bug resolved", "Update: latency down". Dropped articles and verbs read as a changelog fragment, not a sentence. Write the sentence: "The cache bug is fixed."

### Nested parentheticals and dense sentences

An aside inside an aside ("the retry logic (added last sprint (by the infra team)) handles this") crams three thoughts into one sentence. One parenthetical is a tool; nested ones are a queue. The same crowding happens without parentheses: three clauses and two qualifiers packed into one sentence. Unpack into sentences.

### Paragraph flow

Context, problem, and impact that belong together read best as one narrative paragraph. Splitting them into three one-line paragraphs for scannability produces choppy fragments that each say too little. Merge connected thoughts; keep unrelated paragraphs short.

### Code identifiers

In technical prose, backtick every symbol, type, function, path, flag, and environment variable (`shipper.yaml`, `GOMAXPROCS`, `Retry()`). Prose case for prose, code formatting for code; mixing them makes both harder to scan.

### Numbers in prose

In running prose, spell out counts below ten: "the job failed six times", "two reviewers". Keep numerals for 10 and up, for measurements and versions ("90ms", "v2"), and for data-dense spans where the numbers do the work ("45 tickets across 12 services"). A digit inside a spoken sentence ("retried 4 times") reads as a log line; "retried four times" reads as a person.

Translate a precise count into human meaning when that is clearer: "about a third", "roughly half", "more than half", followed by what that changed. Never leave a naked metric that makes the reader ask "of what?" or "why does that matter?"; every number carries its base and its consequence.

**Before:** "Answered 58 of the 170 support escalations."

**After:** "Handled about a third of the support escalations, which freed the on-call engineer for incident work."

Precision stays when the number itself is the point (a benchmark, a budget, an SLO). The translation is for impact statements, where the proportion is what the reader keeps. Dates and durations follow the same rule: keep them when they explain a contrast, foresight, or durability; drop them when they are only color.

### Artificial line breaks

Hard-wrapping prose at a fixed column puts single newlines inside paragraphs. Renderers usually hide them, but diffs, editors, and plain-text readers do not, and a reflowed edit churns every following line. One paragraph, one line; let the editor wrap.

## 8. What the detector script catches

`scripts/flag_patterns.py` has regexes for the lexical tells: hedge stems, listicle openers, dead transitions, manufactured stakes, performed candor, rhetorical openers, not-only-but-also, filler and degree intensifiers, vague quantifiers, negative parallelism, AI vocabulary, wrap-up scaffolding, marketing register (sentence-aware), rule-of-three triplets, calls to action, dash density, throat-clearing, emphasis crutches, meta-commentary, binary contrasts, negative listing, business jargon, sycophancy, transformation chains, corrective reveals, forced cohesion, copula inflation, stacked hedges, lead-in labels, self-reference ("this PR adds..."), record-keeping phrases ("7 recorded occurrences", "is on record"), markdown separator rules, and every term in `scripts/blocklist.txt` (AI vocabulary and agent-era tells like "production ready", "hygiene", "prose"; edit that file to grow the list). `--profile strict` adds aggressive opt-in rules (every -ly adverb, any Wh- opener, any em dash) that stay off by default because a lone adverb or dash is normal in honest prose.

Not every tell weighs the same. The script weights them: listicle stems and manufactured stakes count most, a lone degree intensifier least, and only clusters accumulate enough weight to drag a paragraph's band down.

The detector is blind to everything semantic; never mistake a quiet run for clean prose:

- **Hollowness**: a paragraph that makes no claim at all. Only the removal test catches it.
- **Fabricated stance**: a contrarian hot take in plain words trips no trigger.
- **Smooth-but-empty specificity**: "modern technologies that ensure reliability" reads specific and says nothing.
- **Plausible-but-wrong claims**: fidelity is not a surface property.

The score means "how many surface tells", never "how good the writing is".
