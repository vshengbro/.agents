# Annotating a bulk `let` slice: the by-hand half

`scripts/harvest_let_types.py` settles the mechanical sites. It cannot settle
closures, elided generics, or bindings whose type is inferred at the use site
— and those are a large share of a whole-repo §5.1 finding. This is the
procedure for that remainder, plus the two ways a correct-looking annotation
still fails to compile.

## Start from the verifier, not from the harvester's leftovers

Re-run the verifier to get the authoritative list. A harvest taken against an
older tree is stale the moment you apply the first batch, because annotating a
line does not change any *other* line's number — but it does once `crate fmt`
re-wraps the file:

```bash
python3 <skills>/scripts/verify_let_type_annotations.py <repo>
```

Bucket the result before touching anything:

| Bucket | Fix |
|---|---|
| typed by the harvester | mechanical, apply bottom-up per file so earlier line numbers stay valid |
| `found closure` | by hand — see below |
| elided (`...`) or inferred-at-use-site | by hand, after reading the declaration |

Applying bottom-up per file matters: the harvester keys on `file:line`, and
inserting an annotation on line 40 shifts nothing above it but a subsequent
naive top-down pass would annotate the wrong bindings.

## A closure's type is whatever the consumer accepts

A closure has no nameable type, so the annotation is not derivable from the
closure — it is the **bound at the call site**. Find the bound first:

```bash
grep -rn 'impl<F> From<EventNamedAdapter' --include=*.rs <repo>
# -> where F: FnMut(Event) + 'static
```

Three plausible spellings fail, each for its own reason:

| Attempt | Fails with | Why |
|---|---|---|
| `let h: impl Fn(Event) = move \|..\|` | `E0562: impl Trait is not allowed in the type of variable bindings` | legal only in return / parameter position |
| `let h: Rc<dyn Fn(Event)> = move \|..\|` | `E0308: expected Rc<dyn Fn(Event)>, found closure` | a trait object needs an explicit `Rc::new(..)` |
| `let h: fn(Event) = move \|..\|` | `E0308: expected fn pointer, found closure` | a `move` closure capturing anything is not a fn item |

The form that works is a trait-object box matching the discovered bound:

```rust
let on_clear_click: Box<dyn FnMut(Event)> = Box::new(move |_: Event| {
    Console::clear();
});
```

Which trait object depends on what the consumer needs, and these are not
interchangeable:

- `html!` event attributes require `F: FnMut(Event) + 'static` → `Box<dyn FnMut(Event)>`.
  `Rc<dyn Fn(Event)>` is **wrong here** and fails with
  `the trait bound AttributeValue: From<EventNamedAdapter<Rc<dyn Fn(Event)>>>` — the macro's
  `From` impl is bounded on a bare `FnMut`, not on an `Rc`.
- A closure that is both **called and subscribed** needs `Arc`, not `Box`:
  `handler(); route_signal.subscribe(handler);` fails on a `Box` (moved after
  the call), and `subscribe`'s `F: FnMut() + 'static` rejects a bare
  `Arc<dyn Fn()>` as a *trait object that is itself not `Fn`*. The
  `Arc::new(move || { .. })` form works for both.

## A declared return type is a better annotation — and has two traps

`|item: &SideItem| -> i64 { .. }` can be annotated from itself:

```rust
let order_of: Box<dyn Fn(&SideItem) -> i64> = Box::new(|item: &SideItem| -> i64 {
```

Two traps when editing this shape:

- **In a type position, parameters are types, not names.** `Fn(item: &SideItem)`
  does not compile — strip the parameter name, keep the type.
- **Do not drop the trailing `{`.** Several of these closures put the body on
  the *next* line, so a `-> T` that ends the line looks like the closure ends
  there. Deleting the brace makes the next line's body a syntax error
  reported two statements later, in a file you are no longer editing. Read the
  line *and* the one after it before rewriting the signature.

## An alias belongs in `type.rs`, and a long annotation is the signal for one

The same long type repeated across N bindings is a §1.3 keyword-file
violation the moment you put it in `impl.rs` or `fn.rs`. Type aliases go in
the module's **`type.rs`**, registered in `mod.rs` and re-exported:

```rust
// core/src/vdom/attribute/type.rs
/// The write guard over [`INJECTED_CLASSES`] held while recording a class.
pub(crate) type InjectedClassesWriteGuard<'a> = std::sync::RwLockWriteGuard<'a, HashSet<String>>;
```

Then check the `mod.rs` wiring has both halves — `mod r#type;` **and** the
`pub(crate) use r#type::*;` that makes the alias visible to sibling modules.
A new module file without the `use` line fails as
`cannot find type X in this scope`, which reads like a missing import rather
than an unfinished registration.

Two smaller things the same slice tends to expose:

- A `let _ = expr;` whose value is discarded still needs an annotation
  (`let _: Result<i32, JsValue> = ...;`). It is not exempt because nothing
  reads it.
- A type alias with a lifetime is written `Alias<'_>` at the use site. Bare
  `Alias` is `E0107: struct takes 1 generic argument`, and
  `E0658: inherent associated types are unstable` when it is nested wrongly.

## Report the count you measured, and the residual

The score does not move until the residue is zero, so report both numbers
separately. A slice that ends at 0 has converted a FAIL into a PASS; one that
ends at 91 has not, no matter how much of it was mechanical.
