---
name: euv-ui-html-macro-gotchas
description: Use when writing euv html! markup in euv-ui components.
---

# euv `html!` macro gotchas (verified by the compiler, not inferred)

## 1. `key: <bare_ident>` fails with E0574

The `html!` macro parses a bare identifier in an attribute value as the start
of a **struct literal**, so `key: label` expands as struct construction and
fails with:

```
error[E0574]: expected struct, variant or union type, found local variable `label`
```

The same applies to any attribute whose value is a local binding: `key: x`,
`class: my_string`, `style: style_ref`.

**Fix:** wrap the expression in braces — `key: { label }`. The braces mark it
as an expression block rather than a literal path. (A *call* expression is
fine unbraced: `class: base_class()` and `class: c_foo()` work.)

This is the real cause of the `E0574 ... not a struct` errors seen in
`avatar/view/fn.rs` (`class: class_name`) and `icon/view/fn.rs`
(`style: style_ref`) — the same bug, not a missing `Into` impl.

## 2. A green `cargo check` may mean your file was never compiled

When the crate has other in-flight compile errors, an edited file can appear
to be unchecked: append a deliberate type error, rebuild, and if nothing
appears, the build silently skipped the file. Run `touch <file>` before
`cargo check` to force the rebuild.

Never trust a green build until a deliberately broken probe in the target file
is proven to FAIL. That is the only way to separate "my code compiles" from
"my code was never compiled".

## 3. `key:` consumes its value, so it cannot share an owned `String` with a child

`VirtualNode: From<String>` is a move, and `key:` also takes the value. Using
one `String` for both `key:` and the element text yields
`E0382: use of moved value`. Bind the key separately
(`key: { day_number.to_string() }`) or pass a `&str` the macro copies.

## 4. Reactive `if { ... }` around a `Vec` of nodes → E0507

A reactive `if` that wraps a `Vec<VirtualNode>` moves the vec into the closure
and fails to borrow (`VirtualNode` is not `Copy`). Keep children
always-mounted and toggle visibility by reactive class switching — see
`euv_dropdown`, `euv_drawer`, and the `c_*_open` / `c_*_closed` class pairs.

## 5. Braces mean "reactive" — only brace conditions that read a signal

The braces in `if { cond }` are not decoration; they set `is_inline = false`,
which is what makes the macro emit `AttributeValue::reactive(...)` and route
the condition through `auto_get_expr_tokens`. Two distinct failure modes fall
out of that one flag:

**Reactive position (`if { cond }`) — cond must be a signal.** A bare
single-segment ident is auto-`.get()`-ed, so:

```rust
if { flag }          // flag: Signal<bool>  ✅ becomes flag.get()
if { flag }          // flag: bool         ❌ E0599 no method named `get`
if { flag == true }  // flag: bool         ⚠️ works, but clippy flags it
if flag              // flag: bool         ✅ inline — heuristic never runs
```

**Static position (`if cond`) — cond must NOT be a signal.** Inline sets
`is_inline = true`, which passes the expression through untouched, so a
`Signal` written inline will not compile the way you expect either.

The rule in one line: **braces if and only if the condition reads a
`Signal`.** Never write `x == true` or `x & true` to dodge the heuristic —
just drop the braces, which is the correct form for a plain value and reads
better than either workaround.

```rust
if { open_keys.get().iter().any(|e: &String| e == key) } { }   // ✅ reactive
if !feature.icon.is_empty() { }                               // ✅ static
```

## 5b. A reactive position also needs a signal-bearing expression, not just a Signal

A braced condition must be *re-evaluable*: it is evaluated inside a
`FnMut`/`Fn` closure on every signal write. Capturing a non-`Copy` local by
value therefore fails:

```rust
if { selected == option.value }   // ❌ E0507 cannot move out of `selected`
```

Keep the comparison outside and capture a `bool`, or clone/`&` as needed.


## 6. `class!` attribute keys must be kebab-case

`macros/src/ident/fn.rs::reconstruct_ident_from_tokens` rebuilds the ident and
preserves underscores verbatim, so a snake_case key lands in the CSS as-is:

```rust
font_size: var!(font-base);   // ❌ emits `font_size:` — invalid CSS, browser drops the declaration
font-size: var!(font-base);   // ✅
```

Baseline: the existing `ui/src/style/class/fn.rs` has 364 classes and **zero**
snake_case property keys. Any new `class!` file must match that.

## 7. `style:` takes a prebuilt `String`/`&str`; the braced form is a macro bug

```rust
let fill_style: String = format!("width: {clamped}%;");
let fill_style_ref: &str = fill_style.as_str();
html! { div { class: c_x() style: fill_style_ref } }   // ✅
html! { div { style: { width: width } } }              // ❌ E0308
```

The braced form codegens a `String` where `style` expects `AttributeValue`.
This is a real limitation of the macro, not a usage error — work around it with
the prebuilt-string pattern used by `virtual_list`, `icon`, and `rating`. Worth
filing as an upstream fix.

## 8. Tuple-closure parameter type annotations go on the whole pattern

```rust
|(a: usize, b: X)| { ... }        // ❌ parse error
|(a, b): (usize, X)| { ... }      // ✅
```

## 9. A `for` over a local `Vec` holding a reactive `class:` → E0597

Different from gotcha 4 (that is a reactive `if` around a `Vec`; this is a
`for` loop):

```rust
let nodes: Vec<VirtualNode> = items.iter().map(...).collect();   // ✅ build first
```

`AttributeValue::reactive` takes a `+ 'static` closure, so
`for x in items.iter() { button { class: if { s } { a() } else { b() } } }`
borrows the local vec and fails. Same fix as `euv_dropdown`: collect in Rust
first, then emit.

## 10. Nested attributes inside `if { ... }` are silently dropped

`parse_html_children` (fn.rs:881) `break`s on the attr-key pattern, so a
`style:` placed inside a conditional block just disappears — no error, no
warning. Build the full style string in Rust and pass it in.

## 11. A dynamic tag pulls in EVERY registered component

`HtmlDynamicTag::to_tokens` (html/impl.rs:766) emits one match arm per
registered `#[component]`. Consequence: **adding a component can break a
downstream crate that never uses it.**

2026-09 instance: adding `euv_progress` made `euv-example`'s `dynamic` page fail
with `cannot find type EuvProgressProps`. Root cause was that `mod progress;`
was missing from `ui/src/component/mod.rs` — the component directory existed but
was never registered, i.e. dead code, while the registry still scanned its
`#[component]` attribute.

**Rule:** after creating a component directory, immediately confirm
`ui/src/component/mod.rs` has both `mod xxx;` and `xxx::*`. Directory alone = dead
code that still poisons the registry.

## 12. The registry scan is cached

Scan results live in the build script's `OUT_DIR/euv_component_registry_cache`,
keyed on `path;mtime`. If a component behaves inexplicably after an edit:

```bash
find /Users/sqs/Library/Caches/cargo-target -name euv_component_registry_cache -delete
```

## 13. `class!` pseudo rules are attached to the class itself

`{ :hover { ... } }` inside a `class!` block emits `.my-class:hover { ... }` —
it styles the element carrying that class. There is no way to target a
*descendant* (e.g. `.wrapper:hover .bubble { ... }`) through `class!`, so a
pure-CSS "show child on parent hover" needs the child to carry its own class
and rely on CSS written elsewhere, or the reveal to be JS-driven.
