# Reactivity: Signal, Memo, Effect, Scope, Selector, batch

Source: `core/src/reactive/` at `origin/master` (`aac1c450d6e8317c50c01dd6225dea7a29265495`, version 0.39.1).

The runtime is an **arena of generation-indexed slots**; every handle is a
`Copy` id plus a `PhantomData<fn() -> T>` marker. There is no `Rc<RefCell<…>>`
in user code and no context/hook lookup: `Signal::new(0)` is a plain
constructor, and reading inside an `Effect`/`Memo`/`reactive_text` closure
records the dependency automatically.

## Handles

| handle | construction | key methods |
|---|---|---|
| `Signal<T>` (`T: 'static`) | `Signal::new(v)`, `Signal::new_detached(v)` | `get`, `get_untracked`, `try_get`, `try_get_untracked`, `with`, `set`, `set_if_changed`, `update`, `track`, `id`, `dispose` |
| `Memo<T>` | `Memo::new(f)` / `computed!(…)` | `get`, `try_get`, `id`, `dispose` |
| `Effect` | `Effect::new(f)` / `watch!(…)` | `id`, `dispose` |
| `Scope` | `Scope::run(\|scope\| …)` → `(Scope, R)` | `enter`, `id`, `dispose` |
| `Selector<K>` (`K: Clone + Eq + Hash`) | `Selector::new(source)` | `is_selected(key)`, `dispose` |

Rules that bite:

- **`get` tracks, `get_untracked` does not.** Use `get_untracked` inside event
  handlers and one-shot reads (`state.get_route().get_untracked()`), otherwise a
  click handler re-runs forever.
- `set` / `update` return `bool` — `true` when the value actually changed.
  Bind with `let _: bool = sig.set_if_changed(v);` so the `#[must_use]`-style
  contract is visible at the call site.
- `Signal::new_detached` creates a slot that no scope owns; it is **not**
  disposed with its parent scope.
- `Selector<K>` notifies only the previously and newly selected keys — O(1)
  switch instead of O(n) — and its source closure must return the active key.
- `Scope::run` returns the scope together with the closure result, so
  `let (scope, effect): (Scope, Effect) = Scope::run(|_| Effect::new(…));` is
  the idiomatic pairing. `ctx.attach_scope(node_id, scope)` ties node lifetime
  to effect lifetime; unmounting the node disposes the scope.

## Free functions (`reactive::runtime`)

- `batch(|| …)` — group writes so dependents run once at the end.
- `untracked(|| …)` — read without recording dependencies.
- `on_cleanup(|| …)` — register a cleanup for the current scope.
- `flush_effects()` — drain the pending queue synchronously (tests).
- `reactive_stats()` / `reset_reactive_runtime()` — telemetry and test reset.

## Binding scene nodes

`BuildContext` / `SceneHandle` expose the two reactive bridges:

```rust
ctx.bind_children(host, move || { /* rebuild subtree on dependency change */ });
let _: Effect = ctx.bind_text(node_id, move || format!("{}", count.get()));
let _: Effect = ctx.bind_style(node_id, move || if dark.get() { dark_style() } else { light_style() });
```

`view!`'s closure child form is sugar for `reactive_text`, and a `text { … }`
child closure re-runs whenever a signal it read changes. Reach for
`bind_children` when the *structure* changes (route, theme, viewport), not just
the string.

## Pitfalls

| Symptom | Cause |
|---|---|
| effect re-runs in a loop | a `get()` (tracking) read inside the effect writes the same signal |
| state survives a route change | signal created outside the scope that owns the route's nodes; attach the scope with `attach_scope` |
| derived value is stale | `Memo` reads with `get_untracked`, or the memo captured a `Signal` by copy before it was reassigned |
| list of 1000 rows stutters | per-row `Effect`s; use a `Selector` or bind the container once with `bind_children` |
