# Tests

## Agree where to test

Propose as few public entry points as you can, highest level first, each with what it catches and misses.

## Write a good test

Cover one happy path and the edge cases that matter.

| Good | Bad |
|---|---|
| Reads as behavior | Describes how the code works |
| Survives a rewrite | Breaks on a refactor |
| Expects a known literal | Recomputes the value like the code does |
| Checks through the interface | Inspects a database, private state, or call counts |
| Fakes only the system's edge | Mocks our own modules |
| Written one at a time | Written in a batch up front |

## Handle dependencies

| Dependency | Handle | Test with |
|---|---|---|
| Pure logic or in-memory state | Merge into the module | The public interface |
| Has a local substitute, such as SQLite | Hide inside the module | The substitute |
| Our own remote service | Pass in behind an interface | An in-memory version |
| A third party | Pass in behind an interface | A fake |

Add an interface only when two versions will exist.
