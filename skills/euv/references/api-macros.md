# Complete proc_macro Signatures for euv-macros

Source: `macros/src/lib.rs` — 8 proc_macros.

## Full Signatures

| proc_macro | Kind | Signature |
|---|---|---|
| `html` | `#[proc_macro]` | `pub fn html(input: TokenStream)` |
| `class` | `#[proc_macro]` | `pub fn class(input: TokenStream)` |
| `watch` | `#[proc_macro]` | `pub fn watch(input: TokenStream)` |
| `computed` | `#[proc_macro]` | `pub fn computed(input: TokenStream)` |
| `vars` | `#[proc_macro]` | `pub fn vars(input: TokenStream)` |
| `var` | `#[proc_macro]` | `pub fn var(input: TokenStream)` |
| `unsafe_no_inline` | `#[proc_macro]` | `pub fn unsafe_no_inline(input: TokenStream)` |
| `component` | `#[proc_macro_attribute]` | `pub fn component(_attr: TokenStream, item: TokenStream)` |

## Usage Reference

- `html!` — declarative UI node construction (JSX-like), expanded at compile time into a `VirtualNode` tree
- `class!` — nested CSS class definitions, supporting nested `@media` / `@keyframes` / `var!(...)`
- `vars!` — global CSS custom properties (theme tokens)
- `var!` — syntactic sugar for referencing `--name` inside a class
- `watch!` — reactive side effect, runs when a Signal changes
- `computed!` — derived Signal (a function of other Signals)
- `component` — `#[component]` attribute macro, turns a function into a component + automatic Props injection
- `unsafe_no_inline` — internal macro, prevents misuse of `#[inline]` (used inside the framework)
