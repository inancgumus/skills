---
name: git-pr
description: Use when drafting or revising PR descriptions, including when the user asks for adding or updating a PR title or description.
---

# PR Description Writing

Write PR descriptions like an experienced engineer talking to another engineer.

Write like a human, not like a robot.

Be extremely concise. Cut every sentence that doesn't help the reviewer. Empty sections should be omitted, not padded. But match the description to the scope of the work. A big change deserves a description that reflects it. Look at what changed to understand the scope, but never put diffstat numbers, line counts, or file counts in the description.

## Workflow

1. Gather context: read the diff, commit history, related issues and PRs. Use `gh` for all GitHub reads (PRs, issues, example PRs). Never use `fetch_content` on GitHub URLs.
2. Summarize what you learned to the user in a few sentences. What the change does, how big it is, what areas it touches.
3. Ask the user what to emphasize, what tone they want, anything they want called out or omitted.
4. Write the title and body inline, formatted exactly as it will appear on GitHub. Do not create the PR yet.
5. Wait for the user to say "post", "ship it", "lgtm", or similar before touching git. If they give feedback, revise and show the updated draft inline again.
6. Push the branch and create the PR with `gh pr create`.

Do not skip step 3 unless the user explicitly says to write without asking. The user knows what matters to reviewers better than you do.

## Posting

Only after the user confirms:

```bash
git push origin <branch>
printf '%s' "$BODY" > /tmp/pr-body.md   # or use the write tool directly
gh pr create --title '<title>' --body-file /tmp/pr-body.md
```

Always write the body to a file and pass `--body-file`. Never inline the body with `--body "..."` or `--body "$(cat <<'EOF' ... EOF)"`. PR descriptions almost always contain backticks (`` `k6 x` ``, code spans, command names) and most agent command runners wrap the user's command in something like `bash -c "<command>"` for execution. The outer double-quotes trigger backtick expansion before bash ever sees the heredoc, even though `<<'EOF'` would otherwise protect it. Symptom: the backticked tool actually runs (e.g. `k6 x` provisioning logs appear), bare-backticked words emit `command not found`, and tool output lands in the PR description.

Writing the body to a file and passing `--body-file` bypasses every shell layer between the agent and `gh`.

For the title, single-quoted is safe because nothing expands inside single quotes:

```bash
gh pr create --title 'Discover subcommands in `k6 x`' --body-file /tmp/pr-body.md
```

If the title contains a single quote, write it to a file too or use `$'...'` ANSI-C quoting.

## Structure

Use only what helps the reviewer. Include only sections that add value.

**Never copy the example sentences. Read it to absorb the tone and structure, then write original text based on the actual changes.**

````markdown
## What?

<Standalone summary sentence. What the PR does in plain terms.>

## Why?

<Broad impact first. How does this improve things for the user?>

<Optional narrowing. The specific symptom or trigger that made this visible.>

## Note

<Optional. Dependencies, migration steps, or anything reviewers need to know upfront.>

## Related PR(s)/Issue(s)

Depends on #NNN
Closes #NNN
````

### `What` section

- Start with a single standalone sentence that says what the PR does in plain terms. This first sentence should work on its own as a summary. It should describe the impact or outcome, not the implementation mechanism.
- The first sentence is the most important line in the PR. Get it right before writing anything else. If it reads like a code comment ("defers X until after Y", "moves the read to after Z"), you're describing mechanism, not impact. Zoom out.
- If the summary names a package, function, or internal component, you're at the wrong level. Describe what the consumer or user gets, not what the code does internally.
- Never include technical references like function names, package names, method names, or API calls.
- If the summary covers the impact, stop.
- For larger PRs, follow the summary with a bullet list of concrete changes. Each bullet should describe a user-visible behavior, not an implementation detail.
- Write like you're telling a colleague what you worked on, not writing a report.
- Do NOT name specific functions, packages, mutexes, or helpers. Ever.
- Do NOT mix in "why" (the reason, the bug, the symptoms). Keep that in the Why section.

### `Why` section

- Be scenario-driven. Paint the situation: what the user does, what happens, why it's bad. "When a test uses X, the agent does Y. That takes minutes. While it runs, every other Z waits." The reader should understand the problem without knowing any code.
- Zero technical implementation details. No locks, mutexes, goroutines, channels, counters, map writes, signal names, error codes. If you could only explain it to a product manager, that's the right level. The diff shows the how.
- Explain the intended behavior before the problem. Don't open with what's broken. First say what the change enables, then why it's currently not working. The reviewer needs a mental model before the problem statement lands.
- Lead with the broad impact: how does this improve things for the end user? Not the codebase, not the team, the person using this. Ask yourself: who benefits and how?
- For larger PRs, follow the summary with a bullet list of specific gains. Use the "X without Y" form ("stays fresh without rebuilding") instead of the "X. No Y. No Z." form.
- Then, optionally, narrow to the specific symptom or trigger that made this visible. This grounds the broad impact in something concrete. ("Before this, X happened because Y.")
- Let the Why flow as one narrative when context, problem, and impact are closely connected. One paragraph that builds naturally reads better than three choppy ones. Don't fragment into separate paragraphs for the sake of "scannability."
- Use parenthetical examples for simple cases: "(e.g., a user on 2.0 gets 2.2 docs)" keeps flow. Save full-sentence examples for complex scenarios that need setup.
- Cover both directions of impact. When something drifts, say what's extra AND what's missing. Don't describe only one side.
- One sentence is enough for secondary impact. If the primary problem is clear, secondary effects don't need a dramatic paragraph. Don't spiral into storytelling.
- Group related things naturally. "Like X, Y is also..." instead of describing each separately when they share the same role.
- Do NOT start with the specific symptom. Start broad, then narrow.
- Do NOT badmouth the old approach. Sell the new one.
- Do NOT pad with obvious statements ("navigation is fundamental"). If everyone knows it, don't say it.
- Do NOT repeat the mechanism or root cause already covered in What.
- Do NOT use marketing slogans as summaries ("Smaller, faster, fresher", "at scale").
- Stay behavioral. Describe what the user experiences, not how the code works. Internal mechanisms belong in code, not PR descriptions.
- If you catch yourself writing implementation details (lock names, data structures, concurrency primitives), delete the sentence and describe the observable effect instead.

### Separation rule

- `What` = problem solved + behavior change.
- `Why` = why now / what prompted this.

## PR Titles

- Keep titles short, under 60 characters is ideal, never exceed 72.
- Name the component/area, then the fix or change in plain terms.
- Every word should earn its place. Cut filler when the description
  already covers it.
- Start holistically. Look at the commit subjects and changed files.
  What single concept does the PR revolve around? The title should name
  that concept. Don't dive into the diff first; you'll get lost in
  mechanism and miss the forest for the trees.
- Dig past the surface. Before writing the title, keep asking "why?" or
  "what does this actually do?" until you reach the core.
  For fixes: name the root cause, not the symptom, and not the mechanism.
  Symptoms are what the user sees (nil response, flaky test, crash).
  Mechanisms are how the bug happens technically (read too early, event
  dispatch timing, snapshot vs live state). Root causes are what the code
  gets wrong conceptually (ordering, binding, lifecycle).
  If your title explains how the bug happens, you're naming the mechanism.
  Zoom out.
  For features: name the capability added, not the implementation.
- Good: `browser: fix frame document ordering`
- Bad: `browser: fix navigation request-document ordering` (mechanism, describes how, not what)
- Bad: `browser: fix race between navigation and network events in response lookup`
- Bad: `browser: fix nil response on navigation` (symptom, not cause)

## How to write good PR descriptions

1. Write in natural, human engineering language.
2. Keep `What` and `Why` separate.
3. Keep claims scoped to what the change set proves.
4. Keep language direct, plain, and specific.
5. No code-like terms in the description. No backticks except for issue references.
6. Format issue references as plain `#1234`.
7. Include only sections that help reviewers.
8. Keep paragraphs short and scannable.
9. Avoid template-style phrasing and rhetorical contrast.
10. Only add a Mermaid diagram when the interaction is genuinely hard to explain in
    words (e.g., multi-party protocols, complex state machines). If two sentences
    can explain it, skip the diagram.
11. Do NOT hard-wrap lines in PR descriptions. Let each sentence or logical phrase flow as a single line. GitHub renders markdown with its own wrapping, so hard line breaks mid-paragraph look broken on GitHub.

## Tone

- Use practical, clear, engineer-to-engineer phrasing.
- Use active voice. Not "documentation is now fetched" but "fetches documentation".
- Never refer to the PR itself. No "this PR", "this change", "it does", "this adds".
- No technical details. Describe what changed for the user or project, not how the code works. The diff is right there.
- Use direct sentences with concrete nouns and verbs.
- Use neutral confidence: state what is known and ask when uncertain.

## Common Mistakes to Avoid

- Do NOT list internal refactors (helper functions, mutex renames, type extractions)
  in the description. Those belong in the diff, not the PR summary.
- Do NOT over-explain the mechanism. If the What section already says what changed,
  the Why section should not restate it in different words.
- Do NOT pad with extra sentences. Use only as many as the change needs.
- Do NOT default to adding Mermaid diagrams. Most PRs don't need them.
- Write like you're telling a teammate what you did over chat, not writing a report.
- Do NOT use em dashes (—) as connectors. "X — Y" is an AI writing pattern. Use
  periods, commas, or restructure the sentence instead. If you catch yourself joining
  two clauses with an em dash, split them into separate sentences.
- Do NOT use passive voice. Do NOT refer to the PR itself ("this PR", "this change",
  "it does", "this adds").
- The What first sentence must describe impact/outcome, not mechanism. Bad: "Defers
  response reads until after lifecycle events complete." Good: "Fixes frame navigation
  to return responses reliably." If the sentence describes code flow, you're at the
  wrong level.
- Use plain language. Don't write signal names, error codes, or runtime internals when
  a plain description works. "Huge stack trace" beats "SIGSEGV stack trace". If a
  non-Go engineer wouldn't understand the term, rephrase it.

## Backticks and References

- Use backticks on filenames, commands, branch names, and technical identifiers.
- When referencing a repo at a branch or version, use the `repo@ref` form: `foo@master`, `foo@v2`. Not "foo master" or "foo v2".
- When referencing a specific commit, link it: [`foo@abc123`](https://github.com/org/foo/commit/abc123). Don't say "the previous hash" or "the old commit" without identifying it.
- Cross-repo PR/issue references must include the org/repo prefix: org/repo#123. Bare #NNN only works for the current repo. Don't backtick issue/PR references or GitHub won't auto-link them.
- In the Related section, list each reference on its own line. Don't group with "Depends on" or "Related to" prefixes unless the relationship is genuinely important context.

## Examples

Study these real examples to absorb the tone, scale, and structure. Small PRs get minimal descriptions. Bigger ones earn more detail, but only when it helps the reviewer.

### Small: one-liner PRs

**Title:** `websockets: move source from experimental to k6/websockets`
```markdown
## What?

Moves the websockets source code out of experimental/.

## Why?

Keeps the canonical source in the stable module location rather than leaving it behind.

## Related

Follow-up to #5579
```

**Title:** `` `k6 x explore` in help output ``
```markdown
## What?

Makes `k6 x explore` discoverable by adding it to the `k6` help output.

## Why?

Same gap that #5748 addressed for `k6 x docs`. The `explore` subcommand lets users browse the extension registry from the CLI, but the help output doesn't mention it.

## Related PR(s)/Issue(s)

Closes #5787
Related to #5758
```

### Small: bug fix, scenario-driven Why

**Title:** `agent: unblock concurrent session creation`
```markdown
## What?

Concurrent session creation no longer blocks behind a slow download on the same node.

## Why?

When a test uses a custom k6 binary (e.g., with extensions), the agent downloads it during session creation. That download can take minutes depending on network and binary size. While it runs, every other session creation request on the same node waits for it to finish, even though the downloads are independent.

Observed on cloud alerts 7397015, 7397440.
```

The Why paints the scenario in plain terms. No mention of locks, mutexes, or concurrency primitives. The reader understands when it happens (custom binary download), what goes wrong (other sessions wait), and why it matters (independent work is serialized).

**Title:** `websockets: fix shutdown deadlock on server pings`
```markdown
## What?

Fixes a deadlock where WebSocket connections hang forever during teardown when the server sends pings.

## Why?

WebSocket connections should shut down cleanly when a test ends or the server drops the connection. A server ping arriving during that window could permanently stall the k6 process. Observed on cloud test run 7385826.

## How to reproduce

The included test sends 20 pings in a burst and drops the TCP connection. Without the fix, the test hangs until timeout.

## Related PR(s)/Issue(s)

Closes #4598
```

### Small: bug fix with user-visible impact

**Title:** `cloudapi/v6: return accurate error on empty name lookup`
```markdown
## What?

The user sees "load test not found" instead of "an error occurred communicating with k6 Cloud" when the name query returns no tests.

## Why?

The API responded correctly, but the test just wasn't there. The old message pointed users and support toward network issues when nothing was wrong with communication.
```

### Medium: new feature with code examples

**Title:** `Shell completions for auto-provisioned extensions`
```markdown
## What?

Shell completions now work for auto-provisioned extension subcommands.

\`\`\`bash
$ k6 x docs <TAB>        # provisions and delegates completion
$ k6 x docs <TAB>        # cached docs returns topic completions
best-practices  execution  net-grpc timers  x-mqtt
$ k6 x docs http <TAB>   # deeper completions
get  post  head  options  del  patch  request
\`\`\`

## Why?

Tab completion silently returns nothing for extensions that aren't compiled into the binary. Users who rely on auto-provisioning get no completions even though the extension supports them when bundled.

## Notes

- Partial names (`k6 x d<TAB>`) and registered extensions are unaffected. Cobra handles those natively.
```

### Medium: behavior change with before/after

**Title:** `` `console.log`: Deep object logging ``
```markdown
## What?

Console logging now properly traverses and displays complex JavaScript structures:

\`\`\`js
console.log({ one: class {}, two: function() { } });
// Before: {}
// After:  {"one":"[object Function]","two":"[object Function]"}
\`\`\`

## Why?

Nested properties like functions and classes were silently dropped or marshaled to `{}`, making debugging painful.
```

### Large: architecture change with summary + detail lists

**Title:** `docs: always-current documentation, smaller binary`
```markdown
## What?

Adds on-demand documentation loading with auto-refresh and preloading.

- Switches to a shared doc infrastructure without changing MCP inputs and outputs.
- Lazy-loads documentation files on demand, with multi-version support.
- Automatically refreshes docs when they change (ETag support).
- Adds a `-preload` flag to download all versions at startup.

## Why?

Agents get accurate answers. Stale docs mean wrong code suggestions, outdated API usage, missing features.

- Docs stay fresh without rebuilding or redeploying.
- Smaller binary without the 5MB embed across 19 versions.
- Loads only the requested version instead of all 16K sections at startup.
- `-preload` downloads all versions at startup without embedding them.
- Deletes `internal/sections/` and the doc preparation pipeline.
- No new tradeoffs. The old approach downloaded at build time too.

## Note

The new infra uses a filesystem abstraction. We can still embed docs at build time like the current mcp-k6 does, then let the infra refresh them at runtime. I don't recommend it because it inflates the binary. `-preload` achieves the same benefit more simply (~5s) and leaves the decision to users.
```

The What summary describes the capability (on-demand loading, auto-refresh, preloading), not the implementation ("switches to shared package", "calls NewCatalog()"). Each bullet is a user-visible behavior. The Why summary names the end-user impact (accurate answers) before listing specific gains. Gains use "X without Y" form. The old approach is mentioned once to show there are no new tradeoffs, not to badmouth it.


### Key patterns

- **Scale to the PR.** A small change needs a sentence. A big migration needs a description that reflects the scope. But never put stats in the description.
- **Show, don't explain.** A code example or before/after table beats paragraphs of prose.
- **Tables for comparisons.** When comparing old vs new behavior across multiple cases, use a table.
- **Don't undersell.** If the change removes a whole subsystem, introduces a new architecture, or touches many areas, the description should convey that. Concise doesn't mean short when the work is large.
- **Extra sections only when needed.** Notes, benchmarks, design diagrams are for big PRs where reviewers genuinely need the context.
