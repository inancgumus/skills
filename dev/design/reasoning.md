# Why the rules

The examples below use terms from several languages. Apply each idea in the repo's own language.

Everything here follows from one idea: deep modules. Every other principle is either a consequence of it, a trap that violates it, or a practice that protects it.

## Deep modules

A deep module is one you can change without affecting anything else. That's the definition — not "big implementation behind small interface." A small interface helps, but it's a mechanism, not the goal. The goal is change isolation.

The test: can you rewrite every line of a module's implementation and no other file needs an edit? If yes, it's deep. If not, something is leaking.

For each module, list what it knows about its callers. If the answer is anything other than "nothing," it's not deep enough. Push caller-specific knowledge out. Return raw data. Use generic names. The module should work identically whether it has one caller or fifty, and it shouldn't care which ones exist.

**Shallow modules earn their existence** when they're the single owner of a design decision that would otherwise leak. A 30-line module that owns the wire protocol format is justified — without it, that knowledge scatters across every feature. Depth isn't measured in lines of code. It's measured in how many places would need to change if that decision evolved.

## Separation

Every module is someone else's code. Even if it lives in your repo, you wrote it, and you can open the file — treat it as a third-party service. You call its public API. You can't change its internals. It doesn't know you exist.

This isn't a metaphor. It's how you should literally think when writing and reviewing code. If you're about to reach into a module's internal state, cast to access an unexported field, or import a helper that isn't part of the public interface — you're violating the boundary. If you need something a module doesn't expose, extend its public API. Don't bypass it.

Dependencies flow downward only. High-level modules import low-level ones, never the reverse. No cycles. Features never import each other. Infrastructure never imports the features that use it. If two features need to communicate, they share a lower-level module or the entry point coordinates them. Any arrow pointing upward or sideways in the dependency graph is a bug.

## No ripple effects

This is the consequence of deep modules and strict separation. When you change one module, nothing else changes. Not "usually nothing." Nothing.

Before adding a function to a module, ask: if I change this function's internals tomorrow, who updates? If the answer is "just this file," good. If it's "every caller," the abstraction is wrong — you're exposing implementation, not hiding it.

Before changing a module's public interface, ask: how many files need to update? If more than two or three, the interface was too wide or too specific to begin with. Narrow it. Return stable types. Accept broad inputs.

The ripple effect test is the fastest way to evaluate any design decision. Proposed refactor? Count the ripples. New abstraction? Count the ripples. "Clever" shared utility? Count the ripples. If ripples increase, the design got worse regardless of how clean it looks.

## Features own their full flow

Each top-level feature is a complete, self-contained pipeline. It calls infrastructure, reads results, decides what's next. Start to finish. The feature decides which tools to use, in what order, with what parameters. Nobody tells it what to do from outside — it owns its entire flow.

The entry point creates features and routes input to them. That's all. If the entry point contains logic beyond routing, it's absorbing work that belongs to the features.

The test: can you add a new feature by creating one new file and adding one line to the router? If yes, the architecture is right. If you also have to teach a shared module about the new feature's shape, something has gone wrong.

## Two traps that look like depth but aren't

### God orchestrators

A shared orchestrator with a clean `start/stop/onEvent` interface looks deep — lots of logic behind three methods. But if it knows every feature's shape internally, it's the single point of coupling disguised as the single point of abstraction. Every new feature forces it to grow a new branch. Every feature change ripples through the shared loop.

Kill it. Let each feature run its own loop.

### Config and hook objects

`FeatureConfig { onComplete, getNextStep, shouldRetry }` looks like decoupling — the orchestrator is "generic" because it's parameterized. But the config type mirrors each feature's exact needs. Change the feature, change the config, change every place that constructs the config. Same coupling, different syntax.

If you're about to describe a feature's logic as a data structure instead of code — stop. Let the feature own that logic as actual control flow. Reserve interfaces for genuinely stable abstractions where multiple implementations make sense, not for parameterizing a single feature's behavior.

## Infrastructure

### Generic and ignorant of callers

Helpers do one thing without knowing who calls them or why. No caller-specific terminology, formatting, or decisions. If a helper says "for the review phase" or "when in manual mode" anywhere in its code or naming, it's leaked.

Read every function name and parameter name. If you see domain terms from a single caller, rename to generic equivalents. `sendAsReviewer(prompt)` becomes `setModel(model)` + `send(prompt)`. `formatForPrompt(files)` becomes `readFiles(paths)`. Return raw data, let callers format.

### Survives feature churn

Helpers must be resilient to the full lifecycle of the features that use them. Run three thought experiments for every helper:

1. **Add:** A new feature that doesn't exist yet uses this helper. Does it work as-is, without adding a branch or parameter?
2. **Modify:** An existing feature rewrites its core logic. Does the helper still work without edits?
3. **Remove:** A feature gets deleted. Does the helper still compile? Does every remaining function still have at least one caller?

If any answer is no, the helper knows too much about a specific caller.

### Callers decide, helpers execute

Infrastructure returns raw data and performs raw operations. The caller interprets meaning, makes decisions, formats output.

A file reader returns `{path, content}` — not markdown. A timer returns elapsed milliseconds — not a formatted status string. A parser returns `"approved" | "rejected" | null` — it doesn't decide what to do about it. When you're about to add an `if` branch inside a helper that handles different callers differently, move that `if` to the caller.

## No event-driven architecture

Event-driven architecture is the most reliable way to make code impossible to follow, impossible to debug, and impossible to change safely.

An event fires. A handler somewhere reacts. That handler mutates state. Another handler checks that state. A third handler defers work because the state isn't ready yet. You're now debugging a system where control flow is invisible, state is scattered across handlers, and the only way to understand what happens is to mentally simulate every possible event ordering.

The fix is simple: call a function, await the result, decide what's next. Top to bottom. The position in the code IS the current state. No `phase = "waiting"` variables. No `if (phase === "waiting") doX()` dispatch. No deferred execution queues. Just `const result = await doX()`.

If the platform is event-driven (callbacks, listeners, message queues), absorb that in one infrastructure module. Store a pending promise resolver. When the event fires, resolve it. Expose an `async` function that creates the promise, triggers the operation, returns the result. Handle edge cases (abort, timeout, double-fire) inside — callers never see them. One module owns the async complexity. Everyone else writes straight-line code.

Cancellation works the same way. When a stop signal arrives, reject the pending promise with a typed error. The caller's `await` throws, the `catch` block cleans up, done. No `if (stopped) return` sprinkled in 15 places. The error propagates naturally through the call stack.

## Duplication

### Single owner for every shared piece

If two modules need the same logic, exactly one module owns it. The other imports it. Never two copies. Before writing a function, search for it. If it exists in the wrong module, move it first. After every refactor, search for duplicated function bodies.

### Coincidental similarity is not duplication

Code that looks similar but varies in intent, branching, or surrounding context is not worth extracting. Extracting it creates a module that serves two masters and grows `if` branches for each.

Before extracting "shared" code, list the differences. If they differ in 3+ places, or the differences are about *decisions* not values, they're coincidentally similar. The truly shared part might be 10 lines inside a 50-line block — extract only those 10. A `while` loop that calls the same utilities in each feature is not duplication if the loop body makes different decisions.

## Verification

### Test through public APIs

Test through the public API so internals can be restructured freely. A test that imports an internal function is coupling disguised as coverage — it blocks every refactor.

Build a test harness that exercises modules through public entry points. Mock external dependencies at the boundary, not deep inside. If a behavior is only testable by importing a private function, that's a signal: either the behavior should be a module with its own public API, or it's an implementation detail that doesn't need a dedicated test.

### Hard gates, not carve-outs

No "acceptable for now" exceptions. Every principle has a verifiable check. Exceptions compound — one becomes three becomes permanent.

Define a concrete check for each principle. Dependency direction: no upward imports. Test coupling: grep for internal imports returns nothing. Generic helpers: no caller-specific terms in function names. Run these after every step. Fail the step if any check fails. Never proceed with a known violation and a plan to fix it later — fix it now or change the plan.
