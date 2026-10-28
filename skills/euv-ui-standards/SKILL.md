---
name: euv-ui-standards
description: 'Write or review euv-ui pages, components and class! blocks. Design tokens, class registry layout, page templates, and the CSS rules that silently break in the browser. euv UI 页面/组件/样式, class!, vars!, euv_header, design token.'
license: MIT
metadata:
  hermes:
    tags:
      - euv
      - euv-ui
      - css
      - design-system
    related_skills:
      - euv
      - rust-standards
---

# euv UI design system

Rules for euv-ui pages, components and styles. Not for: pure Rust logic, `Signal` reactivity or renderer work — those have their own skills. No count is printed here; each number comes from the command beside it.

## Index

§0 Source of Truth · §1 Design Tokens · §2 Global Skeleton · §3 Core Component HTML Templates · §4 Home / Hero Page Spec · §5 Class Naming Conventions · §6 Responsive / Breakpoints · §7 Accessibility / Touch · §8 New Page Standard Template · §9 Quick Notes / Anti-Patterns

Design and API detail lives in three topical references, loaded on demand: `references/design-tokens.md` (token values, scales, overlay alpha, global reset), `references/component-templates.md` (component HTML + props, site shell, `Css::inject_css` recipes), `references/euv-tag-wrap-recipe.md` (inline-flex → inline-block fix, with before/after rects).

## 0. Source of Truth

Registry `ui/src/style/class/<group>/fn.rs` (groups: data display forms identity overlay page shell) · tokens `ui/src/style/var/theme/fn.rs` (light/dark semantics) + `ui/src/style/var/scheme/<name>/fn.rs` (the UI scheme's role primitives) · reset + keyframes `ui/src/style/css/fn.rs` via `inject_app_global_css()` · views `ui/src/component/<name>/view/fn.rs` · pages `example/src/page/<name>/` · version of record = root `Cargo.toml` `[workspace.package].version`, **bumped at the root only**, never per sub-crate.

**Two token owners, never one.** The mode class (`c_theme_light` / `c_theme_dark`) owns the semantic mapping and the universal structure scale; the scheme class (`c_scheme_<name>`) owns the colour roles, the radius scale, the type ramp and the control heights. The two sets are disjoint by construction, so both can sit on the same root element without either shadowing the other. `ui/tests/theme` fails the build if they ever overlap, if a scheme drops a token, or if the registry reads a token nobody defines.

**Hard constraints — violating any is a review reject.** Every `class!` block lives in the registry; a page's `view/fn.rs` only calls `c_xxx()`. Naming is `c_` + scope + element, snake_case lowercase: reused across pages ⇒ no page name (`c_card`), page-scoped ⇒ `c_<page>_<element>`. Never hardcode a colour or spacing literal in `class!`; always `var!(…)`.

**Registry → render → visibility → test.** `class!` compiles to `pub fn c_xxx() -> Css` and its CSS is never type-checked, so a green `cargo check` proves nothing:

```bash
euv fmt          # 0 files changed; macro-aware (cargo fmt is not)
cargo check -p euv-ui --target wasm32-unknown-unknown
cargo check -p euv-example --target wasm32-unknown-unknown
strings example/www/pkg/euv_example_bg.wasm | grep -o "c_<your_class>[^c]*"
```

Then open the route, read the rule back from `document.styleSheets`, and — if the box has a border — wrap the text and re-check; a renamed class or misspelled token (`var!(accentt)`) is silently ignored by the browser, so that step is the only real proof. Counts always regenerate (`ls -d example/src/page/*/ | wc -l`), never reuse a printed one.

## 1. Design Tokens

Monochrome black/white, light + dark pair in `ui/src/style/var/fn.rs`; values and scales: `references/design-tokens.md`. `bg-overlay` is overlay-only, never the `background` token and never overridden inside a page — on a `#000` page a scrim brighter than black reads as white (~20 RGB units of lift; dark mode needs a white-tinted alpha). Add a token to one theme only and the browser silently falls back; no compiler catches it. A picture is not chrome: a camera feed and a canvas letterbox are `surface-media` (black) and a drawing preview is `surface-drawing` (white) — the same in both themes, so they carry their own tokens instead of a literal in the class.

## 2. Global Skeleton

`c_app_root` (flex, full height, safe-area padding) → `c_app_nav` (desktop sidebar `var!(nav-width)`, `display:none` under 768px) → `c_app_main` (`flex:1`, scrolls, `padding-main-*` tokens). Every page is `c_page_router` → `c_page_container` (`max-width: var!(content-max-width)` 820, centred); cards are separated by `page-block-gap`.

### 2.3 Mobile (< 768px)

Desktop nav hidden; sticky `c_mobile_header` (`mobile-header-height` + `var(--euv-mobile-safe-top, 0px)`, `z-index:100`) holds menu button, logo and theme button. Opening it shows `c_mobile_overlay` (200) + `c_mobile_nav_drawer` (201) sliding via `transform` + `transition` — never toggle a drawer with `display`. The header's `100` is the app-chrome slot (§9): a floating panel (150) covers it, a drawer (201) does not.

**Top safe area is a variable contract, not `env()`.** Header and drawer consume `var(--euv-mobile-safe-top, 0px)`, default `0`: a letterboxed Android browser reports a non-zero `env(safe-area-inset-top)` while the page is *not* under the status bar (dead blank space in light mode), while an immersive WebView genuinely needs it. No static rule separates the hosts, so the layout hook writes the variable only when the host declares immersive mode (`window.__EUV_IMMERSIVE__` or the `euv-immersive` meta tag). **Page and component styles never write `env(safe-area-inset-top)` directly.**

### 2.4 Nav

`c_nav_header` → `c_nav_section_label` → `c_nav_items_scroll` with `c_nav_item_inactive` / `_active` → optional `c_nav_locale_row` → `c_nav_theme_toggle` → `c_nav_footer`. Hover is an inset left border (`box-shadow: inset 4px 0 0 accent`), **not** `border-left-width`: it takes no layout space, and grepping `:hover` for a border change finds nothing.

## 3. Core Component HTML Templates

**Never hand-roll a button** — `euv_button` (`Primary` / `Outline`) is the only one, inside `c_button_controls` for its gap. **Default to `Primary`**, flipping variant only in a mutually exclusive group where exactly one button *is* the current state (action and escape buttons never flip; two `Primary` in a group is a reject). **`euv_card` has no border and no fill** — separate with `c_card_title`'s `1px dashed var!(border)` underline. **Overlays stay mounted**, toggling `c_*_open` / `c_*_closed`; wrapping their children in a reactive `if` fails to compile (`VirtualNode` is not `Copy`). Props, HTML and site components: `references/component-templates.md`.

### 3.B euv_field — label + input + error in one

Replaces the bare label + input pattern; props and error class are in `references/component-templates.md`.

### 3.G Site-level CSS overrides

A consuming project overrides upstream styles with `Css::inject_css`; sidebar, feature-card and badge recipes are in `references/component-templates.md`. Never open the raw string with `<` (the stray char kills every rule after the injection point). **Flatten nested selectors** — a build-time CSS optimiser can collapse `> div >` chains that work locally and fail in CI, so lock the target with an `html body …` prefix or `:nth-child()`.

## 4. Home / Hero Page Spec

`/about` is the only hero page: it skips `euv_header` and composes `c_home()` → `c_home_content()` → badge row → `h1.c_home_title` → `p.c_home_subtitle` → `c_home_actions` (`c_home_btn_primary` / `_secondary`) → `c_home_stats` (4-column grid, 2 mobile) of `c_home_stat_card` → section title/desc → `c_home_feature_grid` of `c_feature_card`. Discriminator: `c_home` in a page's `view/fn.rs` ⇒ it is `about`; `euv_header` ⇒ ordinary page. Never trust memory for the page set: `grep -L euv_header example/src/page/*/view/fn.rs` finds the header-skipping ones. Page-level `Signal` / `watch!` / `use_*` state belongs in a `hook/` subdirectory so the template stays UI-only.

## 5. Class Naming Conventions

Cross-page `c_<component>` (`c_card`) · shell `c_app_*` / `c_page_*` / `c_mobile_*` (`c_app_root`) · page-scoped `c_<page>_<element>` (`c_home_title`) · sub-component `c_<component>_<element>` (`c_euv_input_wrapper`) · state/variant suffix `_active` `_hidden` `_closed` `_primary` `_outline` `_sm` `_md` · parameterised `c_x(arg: &str)` (`c_game_canvas_wrapper(ar)`) · mixin reuse `c_xxx();` inside another block (`c_info_value { c_text_ellipsis(); … }`). Plural and a double prefix are both allowed.

## 6. Responsive / Breakpoints

**One breakpoint: `@media (max-width: 767px)`** — mobile 0–767, desktop ≥768. Standard deltas: nav → drawer · main padding 28→16 · hero title `font-5xl` → `font-4xl`, page title `font-4xl` → `font-3xl` · grids 4→2 and 2→1 · scrollbar hidden · logo and icon sizes grow slightly.

## 7. Accessibility / Touch

The global `:focus-visible { outline: none }`, `prefers-reduced-motion` and `(hover: none) and (pointer: coarse)` blocks come from `inject_app_global_css()` and are never overridden from a custom class (exact text: `references/design-tokens.md`).

**Two recipes for bordered inline elements — never mix them.** Wrapping atom (tag, badge): `inline-block` / `vertical-align: middle` / `line-height: 1` + `text-align: center` + `box-sizing: border-box`. Inline highlight (`<code>`, `<kbd>`, bordered `<span>`): `inline-block` / `baseline` / `1` + `box-decoration-break: clone`. `inline-flex` is an **atomic** box: wrapped lines left-align while the border stays at parent width — a "missing right border" — and `box-decoration-break` cannot rescue it, while `middle` drifts on multi-line fragments and `baseline` holds the prose baseline at any wrap length. Swap to `inline-block` **only** when the box wraps multiple lines *and* has a border; `nowrap` buttons and flex rows are correct as-is — a button or a row declares `white-space: nowrap` and keeps its `inline-flex`. A badge is a wrapping atom, so it uses the first recipe even where it happens to sit in a flex row today. Rects and the diagnosis recipe: `references/euv-tag-wrap-recipe.md`.

**Gesture / touch hooks.** `App::use_window_event(name, FnMut())` is the only window-event registration entry point and it **discards the `Event`**, so a gesture hook cannot reach `TouchEvent.touches()` from there — return an `Option<Rc<dyn Fn(Event)>>` bundle and let the caller wire `ontouchstart` / `ontouchmove` / `ontouchend` / `ontouchcancel` in `html!`. Classify a tap by **both net displacement and total path length** (net displacement alone misreads a "circle back to origin" gesture as a tap), and read hook state through the generated accessors, never `self.field`.

**The focus ring lives in the global stylesheet.** The system is monochrome: `--border`, `--accent` and `--ring` hold the same ink in both themes, so a focus that only changes the border colour changes **nothing** on screen — the focus was invisible on every form control. The ring is an inset shadow (`APP_A11Y_CSS_FOCUS_RING`, next to the pinned `:focus-visible { outline: none }` block), so it takes no space and the text does not shift when the field takes the focus. Its colour is `currentColor` — the colour of the label of the control — so the ring is always the one that contrasts with the surface it sits on: ink on a light field, paper on an ink button. A control whose *box* is a wrapper (the number input) carries the ring on the wrapper through `:focus-within` and suppresses it on the inner field. `ui/tests/class_registry` fails the build if the `ring` token is orphaned again.

## 8. New Page Standard Template

Create `example/src/page/<name>/` with `mod.rs` (`pub mod view;`) and `view/fn.rs`; add `hook/` only if the page needs state hooks. `view/fn.rs` is a `#[component]` returning `VirtualNode`, written entirely in `html!` — **no `class!` block here** (new shared style goes to the §0 registry; a strictly page-local class may go to `example/src/style/class/fn.rs`). Destructure props first, then order the view `c_page_container > euv_header > euv_card …`. `c_card` already carries the block gap (`margin-top: var!(page-block-gap)`, 20px under 768px) — the page adds nothing: a second gap on top of it doubles the space, and a card without one leaves the title's collapsed margin in charge of the rhythm. Register in `example/src/page/mod.rs` (`mod <name>;` + `pub(crate) use <name>::*;`) **and** append the `EuvRouteConfig` consumed by `euv_routes`, or the route is unreachable; list the page in the nav items so the desktop bar and the drawer share it.

```rust
#[component]
pub(crate) fn page_demo(node: VirtualNode<PageDemoProps>) -> VirtualNode {
    let PageDemoProps: PageDemoProps = node.try_get_props().unwrap_or_default();
    html! { div { class: c_page_container()
        euv_header { icon: "🎯" title: "Demo Page" subtitle: "A demo." }
        euv_card { title: "Section A" div { class: c_button_controls()
            euv_button { variant: EuvButtonVariant::Primary
                         label: "Click me" onclick: |_| {} } } } } }
}
```

Props are an empty derive-able struct. Hero pages (§4) skip `euv_header` and compose `c_home*`.

## 9. Quick Notes / Anti-Patterns

❌ Hardcode a colour or spacing in `class!` (use `var!(…)`), declare `class!` in a page's `view/fn.rs`, hand-roll `<button>`, or leave a button row outside `c_button_controls`. Add a shadow, coloured background or corner radius; the system is hard-edged, and the global `:focus-visible { outline: none }` is never changed from a custom class.
❌ Treat `c_card` as a bordered card — it has none; separate with `1px dashed var!(border)`. Write `env(safe-area-inset-top)` directly in header/drawer padding — consume `var(--euv-mobile-safe-top, 0px)` instead (§2.3).
❌ Add a bare `hover { … }` block inside `class!` — without the colon the macro emits the broken selector `.c_xxxhover` and the hover style dies silently. Write `:hover { … }`, then audit the built page's `document.styleSheets` for `hover` not preceded by `:`. Wrap overlay children (`euv_dropdown`, `euv_drawer`) in a reactive `if`, or skip the `EuvRouteConfig` entry when registering a page.
❌ Flip button variant for an action or escape button, or put more than one `Primary` in a mutually exclusive group.
❌ **Comment every CSS property.** Properties are self-documenting; a 6-line rule carrying an 11-line explanation is a reject. Exception: a comment recording a *structural* decision (mobile vs desktop semantics, the `--euv-mobile-safe-top` contract) or a one-line fix pointer. Full rationale goes in the commit body.

✅ Composite spacing tokens over raw scale steps; `1px dashed var!(border)` for separators and card underlines; safe-area tokens on edge-hugging overlays and `--euv-mobile-safe-top` for the top.
✅ Express hierarchy with weight (`var!(accent)` for values, `var!(muted-foreground)` for labels) rather than colour.
✅ z-index budget — one value per layer, low to high: content 1 · loading overlay 5 · affix 10 · app chrome 100 (sticky mobile header, navbar) · nav dropdown 101 · tooltip 140 · floating panels 150 (select, auto-complete, cascader, date-picker, mentions, popconfirm, popover, time-picker, tree-select) · overlay 200 · drawer 201 · back top 900 · modal 1000 · message 1100 · notification 1200 · vconsole fab 9999 · vconsole overlay 10000 · vconsole panel 10001 · fullscreen canvas 10002. Two layers that share a value are ordered by DOM position, not by the design — that is the bug this budget exists to prevent. `ui/tests/zindex_budget` enforces it: a rule that declares a z-index without being registered there fails the build.
✅ `ui/tests/class_registry` enforces the registry rules: no colour literal in a `class!` rule, no `env(safe-area-inset-top)`, no bare `hover { … }` block, a hardcoded spacing literal is either on the scale or carries a comment that records the decision, a bordered inline box is never an atomic `inline-flex` (§7 — it is either the wrapping-atom recipe or `white-space: nowrap`), and the cards are separated by the `page-block-gap` token. A spacing value that is derived from two other lengths — the slider thumb's centring margin, the optically enlarged hit area of the sidebar arrow — has no token to name it, so it stays a literal with the reason next to it.
