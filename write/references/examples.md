# Judged examples

Before-and-after pairs showing each move. Study the reasoning, not just the rewrite: the judgment of rewordable vs. hollow is the whole skill.

Fidelity rule for every "After" below: no new claim, number, name, or mechanism that was not already in the "Before" (or its quoted surrounding context). Pure subtraction is the default. If a rewrite needs a specific (Postgres, microseconds, JSON/CSV), the surrounding text must already supply it; otherwise flag the span as hollow.

## Rewordable: empty hedging (pure subtraction)

**Before** (weak; hedging buries a real claim):
> It's worth noting that, in many cases, caching can often lead to significant improvements in performance for a wide variety of applications.

**After** (strong; the claim, stated, with only padding removed):
> Caching improves performance for many applications.

Why: the source had a claim (caching improves performance). "It's worth noting", "in many cases", "often", "significant", "a wide variety of" add no meaning. Subtract them. Do not invent hit/miss latencies or a mechanism the source never named.

## Rewordable: throat-clearing plus binary contrast

**Before:**
> Here's the thing: building products is hard. Not because the technology is complex. Because people are complex. Let that sink in.

**After:**
> Building products is hard. The technology is manageable; the people are not.

Why: the opener, the telegraphed reversal, and the emphasis crutch all go. The claim (people, not technology, make it hard) was already there and survives intact.

## Rewordable: listicle stem (only when context supplies the factors)

**Before** (weak stem, but a claim arrives in the next sentence):
> There are several important factors to consider when choosing a database. A document store buys flexible schemas at the cost of joins; a relational store trades the reverse.

**After** (strong; stem gone, existing tradeoff kept):
> Choosing a database means choosing what you give up: a document store buys flexible schemas at the cost of joins; a relational store trades the reverse.

Why: the tradeoff was already in the source. If the source never names a single factor, the stem alone is hollow (see below). Do not invent document vs. relational when only the stem exists.

## Flag, don't fabricate: transition gluing non-claims

**Before** (weak; "moreover" glues two non-claims):
> The system is designed to be scalable. Moreover, it is built with modern technologies that ensure reliability and performance.

**Correct response** (flag it; do not invent architecture):
> FLAG (hollow): "Scalable" and "modern technologies" name no mechanism. Deleting the paragraph loses nothing. Needs a real claim (how it scales, what the stack is), not rewording.

**Wrong response** (fabricating stack details, a failure):
> ✗ "The system scales horizontally with stateless workers behind a queue; state lives in Postgres..." This invents workers, queues, and Postgres the source never mentioned.

## Flag, don't fabricate: a hollow paragraph

**Before** (hollow; nothing is being claimed):
> In today's fast-paced digital landscape, leveraging the right tools is more important than ever. Organizations must adapt to stay ahead.

**Correct response:**
> FLAG (hollow): This paragraph makes no claim. "The right tools matter" and "organizations must adapt" survive no removal test. It needs a real point (which tools, what adaptation, why now), not rewording.

**Wrong response** (fabricating a stance, a failure):
> ✗ "Most companies pick tools to look modern, not to solve a problem, and it shows in their bloated stacks." This invents a contrarian claim the source never made. Slop replaced with edgy slop.

## Over-correction: sharpening (PASS) vs. edgy slop (FAIL)

**Before** (has a claim: testing helps quality in development):
> Testing is an important part of the development process that helps ensure quality.

**PASS** (subtract and lightly sharpen; no new domain facts):
> Testing helps ensure quality in development.

**FAIL** (manufactured voice plus a stance the source never had):
> ✗ "Let's be honest: if you're not testing, you're not really an engineer; you're just typing and hoping." Performed candor, a hot take, and an insult the source never implied. Louder, still slop.

**Also FAIL** (invented concreteness the source did not earn):
> ✗ "Tests are the only reason you can change code you wrote six months ago without re-reading all of it." Crisp writing, but it adds a claim the before never made. Prefer the lean PASS unless the surrounding draft already argues that.

## Over-correction: a second PASS/FAIL pair

**Before:**
> Documentation is an essential part of any software project.

**PASS:**
> Documentation is essential in software projects.

**FAIL** (manufactured stakes plus an accusation the source never made):
> ✗ "In today's ship-or-die world, undocumented code isn't just lazy. It's sabotage." Manufactured stakes, a corrective-reveal rhythm, and an accusation from nowhere. Louder, still slop.

## Rewordable: AI vocabulary (delve / tapestry / realm)

**Before** (weak lexicon and a named set of options in the same block):
> Let's delve into the rich tapestry of options available in the realm of modern caching strategies: cache-aside, write-through, and write-behind.

**After** (strong; lexicon gone, named options kept):
> Caching strategies split three ways: cache-aside, write-through, and write-behind.

Why: rewrite this way only because the source names those strategies. If "options" referred to nothing concrete, the span would be hollow. The delve/tapestry vocabulary is never the problem by itself; the absence of a named option is.

## Rewordable: marketing register (keep the mechanism)

**Before** (buzzwords and a stated mechanism in the same block):
> Our platform empowers teams to leverage cutting-edge tooling for a seamless, robust workflow. It runs your existing CI config and caches build artifacts across branches.

**After** (strong; mechanism kept, marketing peeled off):
> The platform runs your existing CI config and caches build artifacts across branches.

Why: marketing words ("empowers", "seamless", "cutting-edge") flag on their own; riders ("leverage", "robust") flag because they share that register. Keep the mechanism, drop the uplift. With no mechanism to keep, the span is hollow. Do not flag standalone "we leverage connection pooling" in honest technical prose.

## Rewordable: vague quantifier

**Before** (vague opener, specific formats already named):
> The library supports a wide variety of formats for a number of use cases: JSON, CSV, and Parquet, read and write.

**After** (strong; the actual list, quantifier gone):
> The library reads and writes JSON, CSV, and Parquet.

Why: rewrite only because the source names the formats. If it never did, "a wide variety of" would be concealing that there is no real list: hollow. Do not invent JSON/CSV/Parquet to fill the hole.

## Rewordable: content puffery

**Before:**
> The Statistical Institute of Catalonia was officially established in 1989, marking a pivotal moment in the evolution of regional statistics in Spain. This initiative was part of a broader movement across Spain to decentralize administrative functions and enhance regional governance.

**After:**
> The Statistical Institute of Catalonia was established in 1989, part of a wider decentralization of administrative functions in Spain.

Why: "marking a pivotal moment in the evolution of" is inflated significance; the decentralization fact was in the source and survives.

## Flag, don't fabricate: speculative gap-filling

**Before:**
> Information about her early life is not publicly available, suggesting she maintains a low profile and keeps personal details private. She likely grew up in a middle-class household, which shaped her later interest in education reform.

**After:**
> Her early life is not documented in the available sources.

Why: "maintains a low profile" and "likely grew up" are guesses dressed as facts. Say what is not known, or omit the section. State a childhood only if a source provides one.

## The hard judgment call: REWORDABLE vs. HOLLOW on near-identical prose

These two look almost the same. The difference is whether a claim exists in the surrounding context, not in the stem alone.

**Case A, REWORDABLE** (the next sentence supplies the point):
> There are several factors to weigh when picking a queue. Throughput, ordering guarantees, and redelivery semantics each pull in different directions, and most brokers force you to pick two.

Subtract the stem:
> Picking a queue means trading off throughput, ordering, and redelivery; most brokers let you optimize two of the three.

**Case B, HOLLOW** (identical stem, no point ever arrives):
> There are several factors to weigh when picking a queue. It's important to consider your needs carefully and choose the option that's right for you.

> FLAG (hollow): the stem promises factors; none are named. "Consider your needs" and "choose what's right" survive no removal test. This needs a real claim (which factors, what tradeoff), not rewording.

Do not carry the tradeoff from Case A over to rescue Case B; that is fabrication.

## Idempotence: already-strong prose

**Before** (already strong):
> A cache miss is not free: it costs the full computation plus the bookkeeping of storing the result. Caches win only when hits outnumber misses enough to pay that tax back.

**Correct response:** return unchanged. Score = strong. Nothing to do.
