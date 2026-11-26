# euv-macros: full syntax reference

Source: `macros/src/` at `origin/master` (`aac1c450d6e8317c50c01dd6225dea7a29265495`, version 0.39.1).

Six proc-macros, all re-exported at the `euv` root (`pub use {euv_core::*,
euv_macros::*}` in `src/lib.rs`), so `use euv::*` is enough:

| macro | expands to |
|---|---|
| `view! { ... }` | `::euv::NodeId` — arena scene-graph construction |
| `style! { ... }` | `#[must_use] fn name() -> ::euv::Style` constructors |
| `tokens! { ... }` | typed `const` design tokens |
| `watch!(...)` | `::euv::Effect::new(...)` |
| `computed!(...)` | `::euv::Memo::new(...)` / `Memo::<T>::new(...)` |
| `euv_main!(bootstrap)` | per-target entry points (`main`, `euv_web_start`, `euv_android_entry`, `euv_ios_entry`) |

There is **no `html!`, `class!`, `vars!`, `var!`, `component` or
`unsafe_no_inline`** any more, and no JSX/HTML vocabulary: `view!` builds a
retained scene graph, not a `VirtualNode` tree.

## `view!`

`view!` manages the `BuildContext` itself (`current_build_context()`), so it
takes **no** context argument — the old `view!(ctx, ...)` form is a compile
error (`ERR_LEGACY_VIEW_CTX`). The body is one root node:

```rust
let root: NodeId = view! {
    column {
        width: Length::Percent(100.0)
        padding: Edges::all(SPACE_LG)
        gap: SPACE_MD
        text { font_size: 18.0 { move || format!("Count: {}", count.get()) } }
        { EuvButton::new("Increment".to_string(), tokens).on_click(move |_: &UiEvent| {
            let _: bool = count.update(|v: &mut i32| *v += 1);
        }) }
    }
};
```

Child forms:

- **element** — `tag { props... children... }`.
- **static string literal** — becomes `ctx.text(String::from(lit), Style::empty())`.
- **closure** — `ctx.reactive_text(Style::empty(), closure)`; re-runs on dependency change.
- **any other expression** — must implement `Mountable`; expands to
  `Mountable::mount(expr, ctx)`. This is how `euv-ui` components compose.

### Tags

| tag | node |
|---|---|
| `view` / `row` / `col` / `column` / `grid` | generic container (`row` = horizontal flex, `column`/`col` = vertical flex, `grid` needs `columns`) |
| `scroll` | clipped scroll container |
| `portal` | top-layer overlay container |
| `text` | text run |
| `input` | editable text input (`value`, `placeholder`) |
| `image` | bitmap node (requires `source: ImageBuffer`) |
| `canvas` | vector surface (requires `painter: |bounds: Rect, dl: &mut DisplayList|`) |
| `slot` | component-level dynamic OTA slot (requires `id: "..."`) |
| `page_slot` | page-level dynamic OTA slot (requires `route: "/..."`) |

### Property keywords

Layout: `style`, `display`, `position`, `width`, `height`, `min_width`,
`min_height`, `max_width`, `max_height`, `aspect_ratio`, `padding`, `margin`,
`gap`, `align`, `justify`, `flex_grow`, `flex_shrink`, `flex_wrap`, `overflow`,
`columns`, `z_index`, `opacity`.

Paint: `background`, `gradient`, `shadow`, `focus_ring`, `cursor`, `color`,
`radius`, `border` (a `(f32, Color)` tuple).

Text: `font_size`, `font_weight`, `font_family`, `text_align`,
`text_overflow`.

Events: `on_click`, `on_change`, `on_scroll`, `on_pointer_down`,
`on_pointer_move`, `on_pointer_up`, `on_hover`, `on_key`.

Element-specific: `value`/`placeholder` (`input`), `source` (`image`),
`painter` (`canvas`), `id` (`slot`), `route` (`page_slot`),
`hub`/`fallback` (`slot`/`page_slot`), `role`/`a11y_label`/`a11y_hint`.

Every property is a **typed method call on `Style`** (`__euv_style =
__euv_style.width(#val)`), so values are Rust expressions (`Length::Px(12.0)`,
`AlignItems::Center`), never CSS strings. Unknown property names produce a
Levenshtein-ranked "did you mean" compile error against `KNOWN_VIEW_PROPS`;
`source:`/`painter:`/`value:`/`id:`/`route:` on the wrong tag are hard errors
(`ERR_SOURCE_ONLY_ON_IMAGE`, `ERR_CANVAS_MISSING_PAINTER`,
`ERR_INPUT_PROP_ONLY_ON_INPUT`, `ERR_ID_ONLY_ON_SLOT`, ...).

**Legacy HTML tags are rejected with a migration hint**:
`div`/`section`/`header`/`ul`/`form` → "`column`, `row`, `view`, or `grid`",
`span`/`p`/`h1`/`label`/`code` → "`text`", `button`/`a` → "`{ EuvButton::new(...) }`
or `view { on_click: ... }`", `img` → "`image { source: ... }`".

## `style!`

Generates one `#[must_use] fn <name>() -> Style` per block. Rules are
`key: value;` and map onto the same `Style` builder methods as `view!` props
(plus `grid`/`columns`, and `border` taking a `(f32, Color)` tuple):

```rust
style! {
    c_action_row {
        direction: row;
        width: Length::Percent(100.0);
        flex_wrap: FlexWrap::Wrap;
        align: AlignItems::Center;
        gap: SPACE_SM;
    }
}
```

`tokens!` generates typed constants — `tokens! { pub const CONTROL_HEIGHT: f32 =
32.0; }` → `pub const CONTROL_HEIGHT: f32 = 32.0;`. The design tokens that
ship with `euv-ui` (`SPACE_XS` … `SPACE_2XL`, control heights, radii) are
ordinary `pub const` items in `ui/src/theme/token/const.rs`, not macro output.

## `watch!` and `computed!`

Both accept an **explicit signal tuple** or an **auto-tracked shorthand**:

```rust
let doubled: Memo<i32> = computed!((counter) -> i32 => move |n: i32| n * 2);
let auto: Memo<i32> = computed!(move || counter.get() * 2);          // auto-tracked
let _eff: Effect = watch!((counter) => move |n: i32| { log(n); });    // explicit
let _auto: Effect = watch!(move || { let _ = counter.get(); });      // auto-tracked
```

With the explicit form the macro emits `Effect::new(move || { cb(sig.get(), …) })`
/ `Memo::new(move || cb(sig.get(), …))`; with the shorthand it forwards the
closure straight to `Effect::new` / `Memo::new`. An empty explicit tuple is a
compile error (`ERR_WATCH_EMPTY_SIGNALS`, `ERR_COMPUTED_EMPTY_SIGNALS`).

## `euv_main!`

`euv_main!(bootstrap)` takes the identifier of a function returning
`Result<App, PlatformError>` and emits the right entry point per target:
`main` on native desktop, `#[wasm_bindgen(start)] pub fn euv_web_start()` on
wasm, and `#[unsafe(no_mangle)] pub extern "C" fn euv_android_entry()` /
`euv_ios_entry()` on Android / iOS. Each body calls `bootstrap()` and steps one
frame.
