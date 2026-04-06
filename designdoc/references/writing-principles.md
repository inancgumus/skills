# Writing principles for design docs

These rules apply to the prose inside a design doc. They come from Amazon's writing culture, Strunk's Elements of Style, and patterns observed in strong technical writing at Google, Uber, and other doc-heavy orgs.

## Sentences

Use fewer than 30 words per sentence. Short sentences force clarity.

Use Subject-Verb-Object structure. Name the actor and their action.

One idea per sentence. One idea per paragraph. Each paragraph should compress to one sentence in the reader's memory.

## Replace adjectives with data

"Sales increased significantly" becomes "Sales increased by 30%."

"Performance is much faster" becomes "Reduced TP90 latency from 10ms to 1ms."

"Nearly all customers" becomes "87% of Prime members."

## Eliminate weasel words

These phrases are banned:

- "would help the solution"
- "might bring clarity"
- "should result in benefits"
- "significantly better"
- "arguably the best"

Replace hedges (would, might, should, significantly, arguably) with specific claims or drop them.

## Simplify

| Replace | With |
|---------|------|
| due to the fact that | because |
| totally lack the ability to | could not |
| in order to | to |
| at this point in time | now |
| has the ability to | can |
| it is important to note that | (cut it, state the thing) |

## Use "is" and "are"

Do not substitute elaborate constructions for simple copulas.

| Avoid | Use |
|-------|-----|
| serves as | is |
| stands as | is |
| represents | is |
| boasts | has |
| features | has |

## Active voice

Every sentence needs a subject doing something. Passive voice hides the actor and drains energy.

| Avoid | Use |
|-------|-----|
| "The service was designed to..." | "The team designed the service to..." |
| "It is believed that..." | Name who believes it |
| "The decision was reached..." | Name who decided |

## Avoid AI writing patterns

Do not use:

- em dashes (use commas or periods)
- rule-of-three lists when two items suffice
- "not X, but Y" contrasts (state Y directly)
- throat-clearing openers ("Here's the thing:", "It turns out")
- emphasis crutches ("Let that sink in", "Full stop")
- vague declaratives ("The implications are significant")
- meta-commentary ("In this section, we'll...")
- false agency ("the decision emerges", "the data tells us")
- sycophantic tone ("Great question!")

## Spell out acronyms

On first use: "Non-Disclosure Agreement (NDA)." Then use the acronym.

## The "so what" test

After writing a statement, read it as the reader. Does it help them make a better decision? If the answer is no, cut it.

## Show, do not tell

Use real examples: scripts, configs, commands and output, API requests and responses, user flows, UI states, diagrams.

A concrete artifact is always clearer than a summary sentence. A failing command is clearer than a bullet describing the failure.

## Every sentence earns its place

Before writing a sentence, ask: is this needed to follow the argument?

"Because it's true" or "because it's how things work internally" are not reasons to include something. A sentence connects to what users experience, what goes wrong, or what changes with the proposal. Otherwise cut it or move it to a link.

## Context before claims

A claim that arrives without setup forces guessing. If a sentence refers to something not yet introduced, add one sentence of context first. What it is, why it exists, then the claim.

## Follow the causal chain

Write cause before effect. If something was attempted and failed, say what was attempted, then what went wrong, then what the consequence is today.

Do not state the conclusion and then walk it back. A first sentence that says something works followed by a second sentence that says it does not is misleading.

## Do not overstate

If something happens in some cases, do not write it as if it always happens. "Generates unexpected costs" claims every instance causes costs. "Can generate unexpected costs" claims what becomes possible. The first is wrong if even one case does not cause costs.

Same for pros. "Team X replaces the workaround" states they will. "Team X can replace the workaround" states what becomes possible. Pros describe what a proposal enables, not what will definitely happen after shipping.

## Show conclusions, not the research path

The doc shows what someone needs to decide. Not every detail discovered along the way. If you investigated an internal mechanism to understand a problem, the doc should state the problem and its consequence. The mechanism belongs in a link.

## Claims need evidence

If a claim describes current behavior, prove it with source code, docs, or a runnable example.

If a claim describes product intent, label it as product intent.

If a claim is unproven, weaken it or source it.

Do not rely on issue links to explain the design. The doc must stand on its own.
