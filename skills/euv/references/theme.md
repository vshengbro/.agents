# `euv-ui`: design system, components, hooks and routing

Source: `ui/src/` at `origin/master` (`aac1c450d6e8317c50c01dd6225dea7a29265495`, version 0.39.1).
Re-verified against `origin/master` (`6ccb8599`, euv 0.43.0) on 2026-11-27: every declared API name below still resolves in that tree.

`euv-ui` is a **separate crate** — it is not re-exported by `euv`, so
`use euv::*` does not bring components in. Add it (`cargo add euv-ui`) and
`use euv_ui::*`. It depends only on `euv` and `lombok-macros`, ships zero CSS,
and has 17 `theme-*` features plus `default` (no `theme-custom`).

## Design schemes and tokens

`DesignScheme` — 17 built-in languages, `Shadcn` being the default:
`Shadcn`, `Cupertino`, `Material`, `Fluent`, `AntDesign`, `Bootstrap`,
`DaisyUi`, `Geist`, `HeroUi`, `Linear`, `Mantine`, `Monochrome`, `Notion`,
`Park`, `Radix`, `Stripe`, `Supabase`.

`ThemeTokens::resolve(scheme, ThemeMode)` builds the whole token set
(`ThemePalette` for color, `ThemeGeometry` for radii/control sizes) and
`card_style()` returns a ready `Style`. Spacing constants are plain items in
`ui/src/theme/token/const.rs`: `SPACE_XS` 4, `SPACE_SM` 8, `SPACE_MD` 12,
`SPACE_LG` 16, `SPACE_XL` 20, `SPACE_2XL` 24.

`use_theme(scheme, mode) -> UiThemeState` is the reactive entry point; it is
what a root view reads to pass `tokens` into components.

## Components

16 component groups under `ui/src/component/`: `button`, `card`,
`data_display`, `display`, `form`, `form_extra`, `layout`, `markdown`,
`media`, `nav_extra`, `navigation`, `overlay`, `overlay_extra`,
`shadcn_complete`, `shadcn_extra`, `surface`.

Every component is a **builder that implements `Component`** (declare it with
`#[component]` or hand-write `impl Component`), and mounts through
`Component::mount(self)`:

```rust
let cmd: NodeId = Component::mount(
    EuvCommand::new(cmd_items, cmd_sel, tokens)
        .query(cmd_query)
        .placeholder("Type a route or action..."),
);
```

Inside `view!` the same component is written with named attributes — never
positionally:

```rust
view! {
    EuvButton {
        label: BTN_SAVE
        tokens: tokens
        outline()
    }
}
```

`EuvButton` shows the shape: `EuvButton::new(label, tokens)` then
`on_click(|_: &UiEvent| …)`, `variant(EuvButtonVariant)`, `size(EuvButtonSize)`
or the `secondary()`, `outline()`, `ghost()`, `destructive()`, `link()`,
`sm()`, `lg()`, `icon()`, `disabled(bool)` shorthands, and
`resolved_style() -> Style` for custom composition.

Components are split into **parts** wherever the shadcn/ui reference splits
them — each part is its own `euv_*` constructor with its own props struct — so
a caller composes them the way the reference site does. Overlays go through
`overlay_stack` (a portal layer owned by the app, not by the node), which is
why there is no "portal component": use the `portal` tag or the overlay stack.

## Hooks (`ui/src/hook/`)

| hook | returns |
|---|---|
| `use_theme(scheme, mode)` | `UiThemeState` |
| `use_i18n(locale)` | `I18nCatalog` (`insert`, `t(key)`) |
| `use_breakpoint()` | `Signal<Breakpoint>` |
| `use_viewport_size()` | `Signal<Size>` |
| `use_router(initial_path)` | `Router` (core router: `at`, `path`, `push`, `back`, `forward`, `can_go_back`) |
| `use_gesture()` | `GestureRecognizer` |
| `use_gesture_events()` | `Signal<Option<GestureEvent>>` |
| `use_window()` | `(Signal<SafeAreaInsets>, Signal<ThemeMode>)` |

There is no `use_async`, `use_interval` or `use_window_event` any more: the
old DOM hook set was removed with the rewrite. Timers belong in an `Effect`
plus the frame loop, and async work in a service that writes a `Signal`.

## Routing

`ui/src/router/` declares pages as data: `EuvRouteDef` holds the path pattern,
`EuvRouteMatch` the matched metadata, `EuvRouteBuilder = Rc<dyn Fn(&EuvRouteMatch)
-> NodeId>` builds the page, `EuvRouter` owns the table and `EuvRouterOutlet` /
`EuvLink` mount and navigate. The core `Router` (`core/src/app/router/`) keeps
the history stack and exposes `DEFAULT_ROUTE_PATH`.
