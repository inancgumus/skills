# Architecture rules

A module is deep when you can change it without affecting anything else. Everything below follows from that. `reasoning.md` explains each rule.

| Rule | Test |
|---|---|
| Deep modules | Rewrite a module's insides, and no other file changes. |
| Separation | Dependencies point downward. Features never import each other. |
| No ripple effects | More files touched per change means a worse design. |
| Features own their flow | A new feature is one new file plus one router line. |
| No god orchestrators | A new feature adds no branch to a shared loop. |
| No config as logic | Feature logic is code, not a data structure of hooks. |
| Helpers ignore callers | No caller's terms in helper names or code. |
| Helpers survive churn | No helper edit when a feature is added, rewritten, or removed. |
| Callers decide | Helpers return raw data. |
| Straight-line flow | Call, await, decide. No `phase` variables or hidden handlers. |
| One owner | Shared logic has one home and no copies. |
| Similar is not duplicate | Code making different decisions stays apart. |
| Public APIs only | No test imports an internal. |
| Hard gates | Every rule has a check, and a failed check stops the step. |
