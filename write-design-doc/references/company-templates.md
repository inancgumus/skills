# RFC and design doc templates by company

Use these as reference when the user's team follows a specific company's template, or when you need to suggest a structure that fits their organization size and maturity.

Do not copy a template blindly. Tailor the process and structure to the org's needs.

## Table of contents

- [Google (Malte Ubl)](#google-malte-ubl)
- [Google (Ryan Madden)](#google-ryan-madden)
- [Amazon PR/FAQ](#amazon-prfaq)
- [Uber (services)](#uber-services)
- [Uber (mobile)](#uber-mobile)
- [Sourcegraph](#sourcegraph)
- [HashiCorp](#hashicorp)
- [Monzo](#monzo)
- [RazorPay](#razorpay)
- [SoundCloud](#soundcloud)
- [RiskLedger](#riskledger)
- [Rust RFC](#rust-rfc)
- [Kubernetes KEP](#kubernetes-kep)
- [Architecture Decision Records (ADR)](#architecture-decision-records-adr)
- [B.O.O. framework](#boo-framework)

---

## Google (Malte Ubl)

Source: industrialempathy.com/posts/design-docs-at-google

Informal documents created before coding. Outline high-level implementation strategy with emphasis on trade-offs.

Sections:
- Context and scope: rough landscape overview, succinct objective background facts
- Goals and non-goals: short bullet points. Non-goals = things that could be goals but are explicitly excluded
- The actual design: starts with overview, then details. System-context-diagram, APIs (sketch, not formal definitions), data storage (approach, not complete schemas), code/pseudo-code (rare, for novel algorithms only), degree of constraint
- Alternatives considered: list alternatives with trade-offs leading to selected design
- Cross-cutting concerns: security, privacy, observability

Length: 10-20 pages for larger projects. 1-3 page "mini design docs" for incremental improvements.

When NOT to write one: solution is unambiguous, doc would just be an implementation manual without trade-off discussion, or prototyping and rapid iteration are the priority.

Write a design doc if 3+ apply: uncertain about the right design, senior engineer involvement would help, design is ambiguous or contentious, team struggles with cross-cutting concerns, need high-level documentation of legacy systems.

## Google (Ryan Madden)

Source: ryanmadden.net/things-i-learned-at-google-design-docs

Functions: planning (author's notes as they figure out approach), structure (templates prompt consideration of necessary aspects), discussion (teams explore approaches), approval (multi-party gating), record and history (entry points for new engineers, credit for work).

Sections:
- Title: short, descriptive (<6 words), with shortlink and metadata
- Purpose: 1-2 sentences establishing what the doc contains
- Background: 1-2 paragraphs of context/motivation accessible company-wide
- Overview: 1-2 paragraphs summarizing the design with noteworthy details
- Detailed design: core section. Any design or implementation decision that could provoke significant discussion in code review should be explained here.
- Alternatives considered: other options and why not selected
- Secondary sections: testing, deployment, monitoring as needed
- Document history: table of major milestones and dates

## Amazon PR/FAQ

Source: productstrategy.co/working-backwards-the-amazon-prfaq-for-product-innovation

Customer-centric written document describing a product as if launching on a specific future date, before it is built.

PR section:
1. Headline, subtitle, date: "COMPANY ANNOUNCES SERVICE/PRODUCT TO ENABLE TARGET CUSTOMER TO HAVE THIS BENEFIT"
2. Intro paragraph: 3-4 sentences expanding on the solution
3. Problem paragraph: top 2-3 customer problems with negative impact. No solutions.
4. Solution paragraph: how the product solves those problems
5. Company leader quote: manager's manager level, explains why tackling this problem
6. How the product works: customer usage pathway with operational detail
7. Customer quote: imaginary but realistic, representing target persona
8. How to get started: one sentence with URL or access info

FAQ section: Q&A format, split into internal and customer FAQs. Predict stakeholder questions. FAQs grow over time.

Review: "narrative" meetings with silent reading (~20 minutes) followed by discussion. If unclear, must be rewritten and reviewed again before proceeding.

## Uber (services)

Sections: approvers, abstract, architecture changes, service SLAs, service dependencies, load/performance testing, multi data-center concerns, security, testing/rollout, metrics/monitoring, customer support.

## Uber (mobile)

Sections: abstract, UI/UX, architecture changes, network interactions, library dependencies, security, testing/rollout, analytics, customer support, accessibility.

## Sourcegraph

Sections: summary, background, problem, proposal, definition of success.

## HashiCorp

Sections: background, proposal, abandoned ideas, custom sections.

## Monzo

Sections: why solve now vs later, goals/non-goals, client API/platform interactions, new internal tooling, legal/privacy, risks (required), observability/graceful degradation, what we still don't know.

## RazorPay

Sections: summary, motivation, detailed design, drawbacks/constraints, alternatives, adoption strategy, open questions, how do we educate people, references.

## SoundCloud

Sections: header (authors, reviewers, revisit date, state), need, approach, benefits, completion or alternatives.

## RiskLedger

Sections: TL;DR, need, success criteria, approach, awareness, technical design (backend/frontend), milestones, out of scope.

## Rust RFC

When required: semantic/syntactic language changes, removing language features, large std additions.

Pre-submission: seek feedback on Zulip, internals.rust-lang.org, informal "pre-RFC" posts.

Process: fork RFC repo, copy template, complete with attention to motivation and design impact, submit PR, build consensus through discussion.

Decision: "Final Comment Period" (FCP) with disposition: merge, close, or postpone. All sub-team members sign off. FCP lasts 10 calendar days.

## Kubernetes KEP

Stewardship model (DACI): Driver (enhancement owner), Approver (SIG leadership), Contributors (implementers), Informed (community).

When required: user/operator-facing enhancements, technical efforts impacting large sections, multi-SIG impacts, large project-wide changes.

Metadata: title, status (provisional/implementable/implemented/deferred/rejected/withdrawn/replaced), authors, owning-sig, reviewers, approvers, editor, creation-date.

## Architecture Decision Records (ADR)

Lightweight documents stored in repositories alongside code artifacts.

Required elements:
- Title: unique identifier plus decision statement (e.g., "ADR001 - Use AKS for Kubernetes")
- Status: Draft, Proposed, Adopted, Superseded, Retired
- Decision: the choice in a few sentences
- Context: forces and circumstances necessitating the decision
- Options considered: each option with pros/cons
- Consequences: positive and negative ramifications

ADRs document decisions at a point in time. They do not need maintenance. If something changes, write a new ADR that supersedes the old one. The original rationale stays searchable.

Store ADRs in source control alongside code (e.g., `adr/001-use-postgres.md`), not in a wiki, so they stay in sync with the codebase.

## B.O.O. framework

Background, Objective, Overview.

- Background: history lesson for how you got here
- Objective: what you want to fix or change
- Overview: how you will implement the change

Works well for targeted design documents in a culture where you write a design doc for most architecture changes. For larger strategic documents, consider the Good Strategy/Bad Strategy framework: Problem Diagnosis, Guidelines/Assumptions/Requirements, Actions.
