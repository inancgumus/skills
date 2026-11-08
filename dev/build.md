# Build

One behavior at a time, each proven by a test that failed first. For several tickets at once, see `build/parallel.md`.

## Steps

### Load the context

Read the ticket and any saved design.

| The ticket | Do |
|---|---|
| Waits for others | Offer the next ready one. |
| Holds a question | Settle it with `align`, then `ship`. |
| Has a human owner | Say what they must do. When done, check its criteria and mark it done. |
| Is ready | Pick it up, per `tickets.md`, on its branch if it has one. |

Read `design/rules.md`. Run the tests once to see what already fails.

**Move on when** you can name the goal, the commands, and what already fails.

### Agree where to test

Unless the plan settled it, see `build/tests.md`.

**Move on when** the developer confirms. For a tiny change, say which test you will add.

### Repeat: fail, pass

1. Write one test through the public interface.
2. Watch it fail for the reason you expect.
3. Write the least code that passes.
4. Run it and the nearby tests.

Tidying waits for `review`. A refactor has no new behavior, so make sure tests cover it and keep them passing.

**Move on when** every behavior has a test that failed and now passes, or a refactor's tests still pass.

### Check the whole change

Delete tests the design marked for replacement. Run the full suite, lint, and the design's checks. Fix each failure now.

**Move on when** every check passes.

### Hand over

Show what changed and the final test output. Leave it uncommitted for `ship`.

**Move on when** the developer has seen it.
