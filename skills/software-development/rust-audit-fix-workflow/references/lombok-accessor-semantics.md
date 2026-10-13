# lombok-macros accessor semantics that the docs understate

`lombok-macros` is the workspace's own derive crate (`ctares/lombok-macros`). Its
README documents the attribute syntax; it does not document the behaviours below, and
each one costs a compile cycle to discover.

## The derive generates for EVERY field, not only annotated ones

`#[derive(Getter)]` / `Setter` / `Data` walk **all** fields of a named struct and emit an
accessor for each, using the macro's default visibility. An attribute does not *enable*
generation — it **configures** an accessor that is generated regardless.

```rust
#[derive(Getter)]
struct PaymentIntent {
    #[get(pub)]      id: String,        // configured
    amount: i64,                       // STILL generates `pub fn get_amount`
}
```

So the only way to withhold an accessor is `#[get(skip)]` / `#[set(skip)]`. Omitting the
attribute is not omission.

**This matters most for fields that must stay bundled.** A minor-unit `amount` and its
`currency` are only meaningful together; a generated `get_amount() -> i64` lets a caller
read one half and pair it with a different currency. Mark both `#[get(skip)]` and hand-write
one method that returns the pair.

## `Option` fields generate a `get_*` that unwraps — read them with `try_get_*`

For a field of type `Option<T>` the derive emits **two** accessors, and only one of
them is safe:

```rust
pub fn get_view(&self) -> &JsValue   { &self.view.clone().unwrap() }  // panics on None
pub fn try_get_view(&self) -> &Option<JsValue> { &self.view }         // safe
```

`grep -rn 'unwrap()' <dir>/` returns **0 hits** — the panic lives in the expansion, and
the reported `file:line` points at the *call site*, not the unwrap. So this class of
defect is invisible to source scanning and to the audit's `unwrap/expect/panic` check,
which greps committed diff text for those literal tokens.

**Rule: any `Option<T>` field is read through `try_get_*`.** `get_*` is legal only on a
non-`Option` field, or where the caller has already proved the value is `Some`.

### Establish ground truth by expanding the macro, not by reading field names

Whether a given `get_x()` actually panics is a property of the *accessor's declared
return type*, not of the field type alone. Ask the compiler:

```bash
RUSTC_BOOTSTRAP=1 cargo rustc -p <crate> --lib --offline \
  --target wasm32-unknown-unknown -- -Zunpretty=expanded > /tmp/exp.rs
```

then read the generated body:

| Emitted body | Verdict |
|---|---|
| `self.x.clone().unwrap()` (accessor declared `-> T`, the bare inner type) | **panics** |
| `self.x.clone()` (accessor declared `-> Option<T>`) | safe |

An accessor whose declared return type is already `Option<T>` is not a violation, and
the expansion is the only reliable way to tell the two apart.

**Field names collide across unrelated types, so name-based matching is not a
verifier.** `get_min()` exists on a type whose `min` is `Option<i32>` (panics) and on
another whose `min` is `Vector3D` (safe); `get_value()` is both an `Option` accessor and
a `Signal<bool>` setter. A scan that matches bare `get_<field>()` names reports on the
order of a hundred false hits. Resolve **struct declaration → receiver type →
Option-consumption shape** before reporting; a call site is safe when it already
consumes an `Option` (`match e.get_f() { Some(..) => .. }`, `let x: Option<T> =
e.get_f()`, `.as_ref()`, `.unwrap_or(..)`).

Note that `.clone()` at a call site is **not** evidence of safety — a panicking
`get_x() -> T` is routinely `.clone()`-d, so it must not be in the safety filter.
A bare `Option<` anywhere in the surrounding lines is not evidence either, because the
enclosing fn's own return type is often `Option<..>`; only the text **before the call on
the same statement** counts.

### When the panic is an invariant, remove the unwrap at the source — keep the derive

When a hand-written accessor unwraps to enforce "this is always set", the fix is not to
keep the `.expect()` (check 3) and not to delete the derive. Ask whether the value is
genuinely fallible *upstream*:

- **Genuinely fallible** (`HtmlImageElement::new().ok()?`) → keep `Option<T>`, keep the
  derive, and switch the caller to `try_get_*`.
- **Guaranteed present** — the constructor already holds the value, so the accessor is
  re-deriving something the type already had → **store it as a non-`Option` field** and
  let the derive generate a panic-free `get_*`. Every existing call site keeps working
  unchanged, which is what makes this the cheap branch.

Deleting the now-unused assertion-message const is part of the same edit; a const left
behind with its doc comment but no value is a parse error that surfaces as a cascade of
unrelated `E0425`s on sibling items.

## Redundancy rules forbid two successive spellings

| Form | Verdict |
|---|---|
| `#[get(pub, type(copy))]` | redundant `pub` — the macro already defaults to `Public` |
| `#[get]` bare, no arguments | redundant — the derive emits the accessor anyway |
| **the attribute line removed entirely** | the only compliant form |

Deleting the visible `pub` lands on the bare form, which the *next* check forbids. The
destination is the minimal legal form, not the next spelling down. Note the bare form
appears in two positions: on its own line, and **inline before the field type** in a tuple
struct (`TuplePtr(#[get] #[set] *mut dyn FnMut())`). A rewriter matching only whole lines
fixes the first and misses the second.

## `type(...)` return modes and the borrow they force

| Mode | Emits | Breaks when |
|---|---|---|
| default | `&T` for plain, owned `T` for `Option`/`Result` | needs a borrow out of an owned value |
| `clone` | owned `T` | caller needs a reference into it — `E0716` temporary dropped while borrowed |
| `copy` | `T` by copy | field is not `Copy` |
| `deref` | dereferenced `T` | coexists with `GetterMut` on the same field — `E0308` signature mismatch |

A field needing **read-only slice + mutable view at once** (`Vec<T>` with a `sort` that
borrows) has no working mode: `clone` cannot lend, `deref` breaks the `GetterMut` impl.
Hand-write both accessors and say so in the type's doc comment, so the next session does
not re-attempt the modes.

## Generated names

- `get_<field>`, `get_mut_<field>`, `set_<field>` — the mut prefix is `get_mut_`, **not**
  `get_<field>_mut`. `self.get_fields_mut()` does not exist; it is `self.get_mut_fields()`.
- Visibility attributes accept `pub`, `pub(crate)`, `pub(super)`, `private`.

A `private` mut accessor generated in `struct.rs` is **not reachable from a sibling
`impl.rs`** — the generated method lands in the struct's own module. Use `pub(crate)`
when the maintaining code lives in a sibling file, keeping it invisible outside the crate.

## Redundancy removals can be defeated by the baseline

An audit check may report **zero** hits for files that are exempt, while a file with an
identical construct is reported. A check that never fired on your own files still needs
its rule applied: the exemption is a gap, not a pass. Prove the fix by counting the
pattern in the source before and after, not by trusting the check's verdict.

## Verification loop for accessor work

```bash
cargo build -p <crate>                       # after each shape change
cargo test -p <crate>                        # return-type changes break assertions
python3 <skills>/scripts/verify_no_self_field_access.py .
```

Accessor return types are part of the public API. A `&str` → `String` change is not
internal; assert with `.as_deref()` at call sites rather than loosening the test.
