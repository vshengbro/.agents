# euv component HTML templates

Props are typed structs in `ui/src/component/<name>/view/struct.rs`; views are
`ui/src/component/<name>/view/fn.rs`. Regenerate the real component list from
source:

```bash
grep -rhoE 'pub fn euv_[a-z_0-9]+' ui/src/ | sort -u
grep -rn 'pub struct Euv[A-Za-z]*Props' ui/src/component/ | sort
```

`euv_button { variant: Primary | Outline, label, onclick }` is the only button.
The component composes **three** classes — `c_euv_button` (the shared box:
`inline-flex`, `nowrap`, `font-sm`, `radius-lg`) + a variant class
(`c_euv_button_primary` / `_default` / `_secondary` / `_destructive` /
`_outline` / `_ghost` / `_link`) + a size class (`c_euv_button_size_default` /
`_small` / `_large` / `_icon` / `_xs` / `_icon_xs` / `_icon_sm` / `_icon_lg`).
`Primary` → `c_euv_button_primary` (`background: primary`,
`color: primary-foreground`, hover → `primary-hover`); `Outline` →
`c_euv_button_outline` (`background: background`, `border: var!(border-width)
solid var!(input)`, `box-shadow: var!(shadow-xs)`, hover → `accent` /
`accent-foreground`). The size class owns the height: `c_euv_button_size_default`
is `var!(control-height-sm)` (32px), `_large` is `var!(control-height)` (36px),
`_small` is `calc(control-height-sm - space-xs)`. `:active` scales by
`press-scale`, `:disabled` drops to `opacity: 0.5` + `pointer-events: none`.

**Button variant rule:** default every button to `Primary`. Flip variant only
inside a **mutually exclusive group** where exactly one button represents the
current state (Resolve/Fail, Healthy/Panic) — exactly one `Primary` in the
group. Action buttons (Refetch / Load / Submit) and escape actions (Reset,
Cancel, Back) always stay `Primary`, even beside a flipping group. Never express
hover via variant; that's CSS. Group buttons in `c_button_controls` (`flex;
flex-wrap: wrap; gap: gap-element; margin-top/bottom: gap-component`).

`euv_card { title }` renders `<div class=c_card>` with the title in a
`c_euv_card_header` / `c_card_title` pair — and **only when the title is
non-empty** (`if has_title`), so an untitled card has no empty header row.
`c_card` is a real surface — a `var!(surface-border-width)` solid `var!(border)`
edge, a `var!(card)` fill, `var!(radius-xl)` corners, `var!(shadow-sm)` and
`var!(space-2xl)` padding. It is a `flex` column with `gap: var!(space-2xl)`,
and it zeroes its children's `margin-block` through the `slot` and
`[data-euv-dynamic-id]` boundaries, so the shell owns the rhythm. The block gap
belongs to a **page-level** card only: `margin-top: "0px"` by default, and
`margin-top: var(--page-block-gap)` (20px under 768px) under
`:is(".c_page_container > .c_card, .c_page_container > slot > .c_card, .c_page_container > slot > slot > .c_card")`.
A composed card inherits its parent's gap. `c_card_title` sets type and
spacing, no edge of its own (its margin is `0px`). The heading level is a prop
(`level: Option<EuvHeadingLevel>`, default `H3`).

Form controls:

- `euv_field` — label + input + error in one (see §3.B). Its props are
  `id`, `name`, `label`, `input_type`, `placeholder`, `autocomplete`, `value:
  Signal<String>`, `error: Option<Signal<String>>`, `oninput`.
- `c_euv_input` — 100% width, `min-height: var!(control-height-sm)`,
  `padding: 0 control-pad-inline`, `border: var!(border-width) solid var!(input)`;
  hover/focus swap to `border-color: var!(ring)`. Error state is
  `c_euv_input_error` — `border-color: var!(destructive)` on a
  `var(--error-container)` fill, so the error **is** a colour here. Wrapper
  `c_euv_input_wrapper`; inline row `c_inline_input_row` +
  `c_inline_input_button_wrap` (a `flex-shrink: 0` spacer so the button keeps
  its size when the input grows).
- Textarea `c_textarea_input` (padding `space-md space-lg`, vertical resize,
  word-wrap); counter `c_textarea_counter` / `c_textarea_counter_text`. The
  component `euv_textarea` uses `c_euv_textarea` instead.
- Select `c_select_input` matches the input look; draw the chevron yourself, do
  not rely on the native appearance. The component `euv_select` uses
  `c_euv_select_trigger` + `c_euv_select_panel` instead. There is no
  `euv_native_select` in the shared kit's docs — it does exist in the crate.
- `euv_checkbox` → `c_form_checkbox_row` + `c_form_checkbox` (`space-lg` square)
  + `c_form_checkbox_indicator` / `_checked` + `c_form_checkbox_label`; label
  class `c_form_label` (block, `margin-bottom: space-sm`, `font-base`/medium).

`euv_badge` — `c_euv_badge` (the shared base: `inline-block`, `height: 20px`,
padding `2px space-sm`, `font-xs`/`font-weight-semibold`, `radius-full`) plus a
variant class — `c_euv_badge_default` (`background: var!(primary)`,
`color: var!(primary-foreground)`) / `_secondary` / `_destructive` /
`_outline` (`border-width solid var!(border)`, transparent bg, `color:
foreground`) / `_ghost` / `_link`; a clickable badge adds `c_euv_badge_clickable`.
`EuvBadgeVariant` carries all six, and the historical `outline: bool` prop
still forces the outline variant. Row `c_badge_row` (`gap: gap-inline`, wrap),
hint `c_badge_hint`. A badge is a wrapping atom — it uses the `inline-block`
recipe, not `inline-flex` (§7).

`euv_tag` — four variants `c_euv_tag_{solid,outline}_{black,white}` (all
`font-weight: var!(font-weight-semibold)`, clickable, `radius-sm`; the solid
black tag is `font-sm` with `background: var!(primary)` and
`color: var!(primary-foreground)`, the other three are `font-xs`). **Must be
`inline-block` + `vertical-align: middle` + `text-align: center` +
`line-height: 1` + `box-sizing: border-box`** — see §7 and
`euv-tag-wrap-recipe.md` (same directory).

`euv_alert { variant }` → `AlertVariant` carries `Error` / `Success` /
`Default` / `Destructive`; the first two map to `c_error_box` / `c_success_box`
(`margin: gap-component 0`, `background: var(--destructive)` /
`var(--success)` with the matching `-foreground`, `font-base`,
`padding: space-sm space-lg`, `radius-sm`) and the last two to
`c_euv_alert_default` / `c_euv_alert_destructive`. The two differ in colour
**and** copy.

`euv_info` — `c_info_row` with `c_info_label` (min-width 72, `font-sm`/medium,
muted, `flex-shrink: 0`) and `c_info_value` (`flex:1`, monospace, `font-base`/
semibold, ellipsis injected by `c_text_ellipsis`); link variant `c_info_link`.

`euv_modal { title, onclick }` → `c_modal_overlay` (fixed, `var!(bg-overlay)`, z-index
1000, `euv-fade-in`) wrapping `c_modal_content` (`max-width` 480,
`euv-scale-in-modal` .3s `ease-bounce`; mobile `calc(100% - 32px)`,
`max-height: 85%`, `overflow-y: auto`) with `c_modal_header` +
`c_modal_title` + `c_modal_close_button` (opacity transition), `c_modal_body`.
`c_modal_actions` is the action row, used by the example app's modal page.

`euv_loading` — `c_loading_container` (`display:flex`) / `c_loading_text_col` /
`c_loading_title` / `c_loading_subtitle`; spinner `c_spinner` (40px, `50%`,
`euv-spin .8s linear infinite`); `c_loading_overlay(background: &str)` takes a
background argument.

`euv_logo` — `var(--primary)` square with `color: var(--primary-foreground)`;
`c_euv_logo_nav` 32×32, `c_euv_logo_fab` 36→44 on mobile.

Hand-rolled atoms — tabs, lists and progress have components, so prefer
those: tabs (`euv_tabs` — its `c_euv_tabs_bar` carries the `var!(muted)`
fill and `var!(radius-lg)` corners, and `c_euv_tab_item` is the row; the bare
`c_tab_bar` is only a `var(--border-width)` `var(--border)` bottom border with
`var(--gap-element)` gaps, `c_tab_item_active` / `_inactive` are
`var!(radius-md)` pills), lists
(`euv_list` — the bare `c_list_ul`, `c_list_item`, `c_list_item_text`,
`c_list_item_button` max-width 120px),
drag/drop zones (`c_event_drag_zone` → `c_event_drag_zone_active`, dashed 2px
border, `space-xl` padding; the drop side is `c_event_drop_zone` →
`c_event_drop_zone_active`), counter grid (`c_counter_row` 2-col → 1-col
mobile, `c_counter_value`), progress (`c_progress_container`,
`c_progress_bar_running` with `euv-progress`, `_stopped` static), animation
classes (`c_anim_fade_in`, `c_anim_spin` / `_stopped`, `c_anim_pulse` /
`_stopped`, `c_anim_scale_box`).
`c_anim_scale_shrink` / `c_anim_scale_normal` are **page-local** classes
(`example/src/style/class/application/fn.rs`), not shared kit: the shared scale
effect is the `press-scale` transform on `:active`.

Camera/canvas/game helpers live only in `example/src/style/class/application/fn.rs`
and are named `c_<page>_<element>` (`c_game_stats_bar`, `c_game_canvas_wrapper`,
`c_game_2d_canvas`, `c_game_3d_canvas`, `c_game_loading_overlay`,
`c_keep_alive_tab_visible` / `_hidden`, `c_binding_slider_label_accent`,
`c_binding_color_preview_bg(bg)`, `c_slider_value`, `c_canvas_pixelated`) so they
never pollute the global ui package.


## Site components

Docs/site shells built on the same component style, props typed, class prefix
`c_euv_<name>_*`:

| Component | Key props | Behaviour worth knowing |
|---|---|---|
| `euv_navbar` | `route_signal`, `brand_*`, `items`, `drawer_open` | Fixed top bar; `http…` links auto-open in a new tab; `drawer_open` = `Some` renders the mobile ≡ button |
| `euv_sidebar` | `route_signal`, `collapsed`, `items`, `on_navigate` | Recursive collapsible tree; group titles both toggle *and* navigate, and the inline `<a>` must carry its own handler because window-level delegation only reaches the innermost handler; `on_navigate` can keep the history stack consistent in a drawer |
| `euv_toc` | `title`, `items` | Sticky anchor list; empty items render empty; indent past level 2 |
| `euv_pagination` | `prev/next` labels + `Option` item | Card footer; the absent side renders a spacer to stay aligned |
| `euv_dropdown` | `open`, `items`, `on_select` | Trigger via children; auto-closes on select; stays mounted (see below) |
| `euv_drawer` | `open` | Left drawer + overlay; overlay click closes via the router's overlay stack |
| `euv_hero` | `title`, `subtitle`, `actions` | Renders the `c_home_*` hero; empty subtitle/actions skipped |
| `euv_feature_grid` | `features` | Borderless card grid; empty renders empty |
| `euv_markdown` | `blocks` | md AST → `<article class="md-body">`; AST nodes are `Copy` and `&'static`-friendly; injects `euv_ui::EUV_MD_CSS` once at startup |
| `euv_result` | `code`, `title`, `description` | Status/result page for 404/403/500; empty strings skipped |
| `euv_doc_layout` | toc + pagination + footer | Three-column doc shell; empty toc drops the whole column, hidden below 1100px |

Consuming these from a **non-workspace** project (crates.io dependency) needs a
recent enough euv: `html!`'s component registry scans
`$CARGO_HOME/registry/src/*/<name>-<version>/src` from that release onward.
Earlier versions only scanned the current crate plus path dependencies, so a
registry-sourced `euv_*` tag was treated as a native element and failed with an
`AttrValueAdapter` trait error.

**Overlays stay mounted.** `euv_dropdown` menus and `euv_drawer` mount once and
toggle `c_*_open` / `c_*_closed` reactive classes. Do **not** wrap their children
in a reactive `if`: `VirtualNode` is not `Copy`, so the `Vec` borrow escapes the
branch and fails to compile (E0507). For drawer dismissal to work on the system
back gesture, the app root must register the router's overlay history.


## `class!` inheritance and site overrides

A child block reuses a parent by calling it — `c_parent();` inside the child
body. There is no `extends` keyword; same-name properties follow the CSS cascade
(last wins).

A consuming project overrides upstream styles with `Css::inject_css`:

```rust
Css::inject_css(r#"
    html body .c_home_feature_grid .c_feature_card {
        padding: 16px !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-xl) !important;
    }
"#);
```

- **Never open the raw string with `<`.** The stray `<` lands in the generated CSS
  and the parser bails, killing *every* rule after the injection point —
  including rules that previously worked.
- **`html body` prefix raises specificity** so the override beats the upstream
  class.
- **Keep padding when restyling a card** — only change the border and radius, or
  the content ends up flush against the edge.
- **Relative selectors need the structured path.** The legacy runtime CSS
  parser only recognises colon-leading nested rules, so a nested rule that
  starts with a combinator (`>`, `+`, `~`) is now emitted structurally by the
  `class!` macro instead of being parsed back. Lock a deep target with
  `:nth-child()` or `html body …` so the rule survives either path.

A sidebar's dashed child border should sit flush with each level's first
character, so zero out the group padding and indent only the children container:

```css
html body .c_nav_items_scroll .c_euv_sidebar_group { padding-left: 0 !important; }
html body .c_nav_items_scroll .c_euv_sidebar_children {
    margin-left: 20px !important;
    width: calc(100% - 20px) !important;
}
```

When a site omits the locale row, the sidebar's first group title shifts up by
exactly that row's height and misaligns with the main heading; restore it with
`padding-top` on `c_nav_items_scroll`.

Shields.io badges blow up to full width inside `euv_markdown`; constrain them:

```css
.md-body img { max-width: 100%; height: auto; display: inline-block; }
```
