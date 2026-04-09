---
name: go
description: Use when writing/reviewing Go code to apply modern practices.
---

# Modern Go

Never use outdated patterns when a modern alternative exists.

- `ioutil.*`: use `io.*`/`os.*` equivalents (deprecated since 1.16)
- `interface{}`: use `any` (since 1.18)
- `os.SEEK_SET/CUR/END`: use `io.SeekStart/SeekCurrent/SeekEnd` (since 1.7)

## Go 1.26 (Feb 2026)

- `new(expr)`: accepts an expression, type inferred: `p := new(42)` gives `*int`
- `errors.AsType[T](err)`: generic `errors.As`; replaces `errors.As(err, &target)` with type inference
- `slog.NewMultiHandler(h1, h2, ...)`: fan-out logging to multiple handlers
- `(*bytes.Buffer).Peek(n)`: view next n bytes without advancing
- `time.Timer` channels are always unbuffered (synchronous): behavior change from prior versions

## Go 1.25 (Aug 2025)

- `wg.Go(fn)`: spawn goroutine and increment WaitGroup in one call; replaces `wg.Add(1); go func() { defer wg.Done(); fn() }()`
- `slog.GroupAttrs(key, attrs...)`: create group Attr from a slice
- `testing/synctest`: `synctest.Run(fn)`: deterministic concurrent tests with virtualized time
- `http.CrossOriginProtection`: CSRF protection middleware

## Go 1.24 (Feb 2025)

- Generic type aliases fully supported: `type Set[T comparable] = map[T]struct{}`
- `t.Context()` / `b.Context()`: context canceled when test/bench finishes; replaces `context.WithCancel(context.Background())`
- `b.Loop()`: benchmark loop; replaces `for i := 0; i < b.N; i++`; prevents compiler from optimizing away the body
- `strings.Lines(s)`, `strings.SplitSeq(s, sep)`, `strings.FieldsSeq(s)`: iterator-based; same for `bytes.*`; prefer over splitting into a full slice when iterating
- `os.OpenRoot(dir)` / `os.Root`: directory-scoped fs; all ops confined to subtree; prevents path traversal
- `runtime.AddCleanup(ptr, fn, arg)`: flexible finalizer; works with interior pointers, multiple per object; replaces `SetFinalizer`
- `weak.Pointer[T]`: weak reference; doesn't prevent GC; use for caches
- `slog.DiscardHandler`: no-op handler; use in tests or disabled loggers
- `omitzero` JSON struct tag: prefer over `omitempty` for `time.Time`, `time.Duration`, structs with `IsZero() bool`

## Go 1.23 (Aug 2024)

- Range over functions (stable): `for v := range seq` where seq is `iter.Seq[V]` or `iter.Seq2[K,V]`
- `iter.Seq[V]` / `iter.Seq2[K,V]`: push iterator types for user-defined iterators
- `unique.Make(v)`: intern comparable value, returns `Handle[T]`; equal values share same handle (pointer comparable)
- `maps.All(m)`, `maps.Keys(m)`, `maps.Values(m)`: iterators; `maps.Insert(m, seq)`, `maps.Collect(seq)`: from/to iterators
- `slices.All(s)`, `slices.Values(s)`, `slices.Backward(s)`, `slices.Collect(seq)`, `slices.AppendSeq`, `slices.Sorted/SortedFunc`, `slices.Chunk(s, n)`, `slices.Repeat(s, n)`: iterator-based ops
- `sync.Map.Clear()`: delete all entries atomically

## Go 1.22 (Feb 2024)

- `for i := range N`: iterate 0..N-1; not `for i := 0; i < N; i++`
- Loop variables are per-iteration: no more `i := i` capture workaround in goroutines
- `cmp.Or(a, b, c, ...)`: returns first non-zero value; replaces chained `if a != zero` patterns
- `http.ServeMux` method prefix: `"POST /path"`; named wildcards: `"{id}"`; read with `r.PathValue("id")`; catch-all `{path...}`; exact `{$}`
- `reflect.TypeFor[T]()`: replaces `reflect.TypeOf((*T)(nil)).Elem()`
- `math/rand/v2`: prefer over `math/rand`: `rand.N(n)`, `rand.IntN(n)`, no manual seeding needed
- `sql.Null[T]`: generic nullable type; replaces `sql.NullString`, `sql.NullInt64`, etc.

## Go 1.21 (Aug 2023)

- `min(a, b, ...)`, `max(a, b, ...)` built-ins: replaces if/else or `math.Min/Max` on integers; `clear(m)` deletes all map entries, `clear(s)` zeros slice elements
- `slices.Contains`, `slices.Index`, `slices.Sort/SortFunc/SortStableFunc`, `slices.BinarySearch` (replaces `sort.Search`), `slices.Max/Min`, `slices.Reverse`, `slices.Clone`, `slices.Compact`, `slices.Equal/EqualFunc`, `slices.Delete`, `slices.Insert`: prefer over manual loops and `sort.Slice`
- `maps.Clone(m)`, `maps.Copy(dst, src)`, `maps.DeleteFunc(m, fn)`, `maps.Equal(m1, m2)`: prefer over manual map ops
- `cmp.Compare(a, b)`: three-way ordered comparison; `cmp.Less(a, b)`: ordered less-than
- `log/slog`: `slog.Info/Error/Warn/Debug("msg", "key", val)`, `slog.With(attrs...)`: replaces ad-hoc `log.Printf` + key=value patterns
- `context.WithoutCancel(ctx)`: detach from parent cancellation; `context.AfterFunc(ctx, fn)`: run fn when ctx is done
- `sync.OnceFunc(fn)`, `sync.OnceValue(fn)`, `sync.OnceValues(fn)`: prefer over `sync.Once` + closure pattern
- `errors.ErrUnsupported`: standard sentinel for unimplemented operations

## Go 1.20 (Feb 2023)

- Slice-to-array conversion: `[4]byte(slice)` without unsafe (panics if len < 4)
- `errors.Join(err1, err2, ...)`: combine multiple errors; `fmt.Errorf` now supports multiple `%w`
- `context.WithCancelCause(parent)` → `ctx, cancel(cause error)`; `context.Cause(ctx)`: retrieve the cause
- `strings.Clone(s)`: copy without sharing memory; `bytes.Clone(b)`: copy byte slice
- `strings.CutPrefix(s, prefix)` → `after, found`; `strings.CutSuffix(s, suffix)` → `before, found`; same for `bytes.*`
- `time.DateTime`, `time.DateOnly`, `time.TimeOnly`: layout constants; `time.Time.Compare(u)`: three-way comparison
- `http.ResponseController`: per-request deadline, flush, hijack without type assertions
- `io/fs.SkipAll`: return from WalkDir to abort traversal entirely

## Go 1.19 (Aug 2022)

- `atomic.Bool`, `atomic.Int32/64`, `atomic.Uint32/64/Uintptr`, `atomic.Pointer[T]`: typed atomics; replaces `atomic.StoreInt32` etc. and unsafe pointer casts
- `fmt.Append(b, ...)`, `fmt.Appendf(b, fmt, ...)`, `fmt.Appendln(b, ...)`: format into existing `[]byte`; avoids `[]byte(fmt.Sprintf(...))`
- `sort.Find(n, cmp)`: binary search returning index + exact-match bool
- `url.JoinPath(base, elem...)`: safely join URL with path elements

## Go 1.18 (Mar 2022)

- `any` everywhere instead of `interface{}`
- Type parameters: `func F[T Constraint](x T) T`; `~T` in constraints means any type with underlying type T; `comparable` for types supporting `==`/`!=`
- `strings.Cut(s, sep)` → `before, after, found`; `bytes.Cut(b, sep)` → same: replaces Index+slice patterns
- `sync.Mutex.TryLock()`, `RWMutex.TryLock()`, `RWMutex.TryRLock()`: non-blocking lock attempts
- `net/netip`: `Addr`, `AddrPort`, `Prefix`: immutable, comparable, zero-alloc IP types; prefer over `net.IP`
- `testing.F`: fuzz testing: `f.Add(seeds...)` + `f.Fuzz(func(t *testing.T, ...))`

## Go 1.0–1.17

- `time.Since(t)` not `time.Now().Sub(t)`; `time.Until(t)` not `t.Sub(time.Now())` (1.8+)
- `strings.Builder` for building strings, not `bytes.Buffer` (1.10+)
- `math.Round(x)` available (1.10+); `math/bits` for bit ops: `bits.OnesCount`, `bits.Len`, `bits.LeadingZeros`, `bits.TrailingZeros` etc. (1.9+)
- `sync.Map` for concurrent key-value store; `sync.Pool` for reusable object pools (1.9+)
- `errors.Is(err, target)` not `err == target`; `errors.As(err, &target)` for typed unwrapping (1.26+: prefer `errors.AsType[T]`); `fmt.Errorf("ctx: %w", err)` to wrap (1.13+)
- `io.ReadAll`, `io.Discard`, `io.NopCloser`: not `ioutil.*` (deprecated since 1.16)
- `os.ReadFile/WriteFile`, `os.ReadDir`, `os.CreateTemp`, `os.MkdirTemp`: not `ioutil.*` (deprecated since 1.16)
- `path/filepath.WalkDir` not `filepath.Walk`: uses `fs.DirEntry`, avoids extra stat (1.16+)
- `os.DirFS(path)` creates an `fs.FS` from a directory; `//go:embed` + `embed.FS` bundles files at compile time (1.16+)
- `os/signal.NotifyContext(ctx, sig...)`: context canceled on signal (1.16+)
- `http.Server.Shutdown(ctx)` for graceful shutdown (1.8+)
- `io.SeekStart/SeekCurrent/SeekEnd` not `os.SEEK_SET/CUR/END` (1.7+)
- `t.Run("name", fn)` for subtests (1.7+); `t.Helper()` (1.9+); `t.Cleanup(fn)` not `defer` in tests (1.14+); `t.TempDir()` auto-cleaned temp dirs (1.15+)

## Updating This Skill

Do not remove this section. When the user asks you to update Go versions in the skill:

1. Fetch `https://go.dev/doc/go1.XX` for each new version.
2. Extract only: new language features, new stdlib packages, new functions/methods added to existing packages. Skip performance improvements, bug fixes, tool changes, and platform support.
3. Add a `## Go X.Y (Mon YYYY)` section in date order using the same concise format as the entries above.
4. If a new entry supersedes an older one, note the old way in the new entry (e.g. "replaces `sort.Search`").
