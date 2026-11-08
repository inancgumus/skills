# Hunt

Get a failing command before you form a theory. Then the rest is mechanical.

## Steps

### Get a failing command

Use a test, a script against a server, a fixture compared to known output, a browser script, a replayed payload, a small harness, random inputs, `git bisect run`, or old and new versions compared. As a last resort, script a person through the steps. Make it fast and deterministic, and check the exact symptom. Loop a flaky bug until it fails often.

If nothing fails:

| You found | Do |
|---|---|
| It works as designed | Tell the developer, and offer `align`. |
| The latest code passes | Find the fix, and draft any reply. |
| The report lacks detail | Draft specific questions, and wait. |
| Only one environment fails | Ask for access, a redacted log, or approved logging, then wait. |

**Move on when** you have shown the output of a command that is exact, repeatable, fast, and unattended.

### Confirm and shrink

Check it matches the report. Remove inputs and steps one at a time.

**Move on when** removing anything else makes the failure disappear.

### List theories

Write 3 to 5, ranked, each with a prediction: *If the cache key ignores the tenant, adding it makes the failure disappear.* Show the developer, and carry on if they are away.

**Move on when** the list exists.

### Test one theory at a time

Change one thing per probe. Prefer a debugger, then targeted logs tagged with a prefix such as `[tmp-a4f2]`. For a slowdown, measure a baseline, then bisect.

**Move on when** you can explain the symptom, citing file and line.

### Fix it and lock it in

Turn the shrunken case into a regression test at a level where the real failure can occur. Watch it fail, fix, watch it pass, then rerun the original command. If no such level exists, say so and suggest `design`.

**Move on when** the original command passes.

### Clean up

Remove the tagged logs and throwaway harnesses. Note the cause for the commit message.

**Move on when** a search for the prefix finds nothing.
