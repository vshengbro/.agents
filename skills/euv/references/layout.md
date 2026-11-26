# Layout and style

Source: `core/src/layout/`, `core/src/style/` at `origin/master`
(`aac1c450d6e8317c50c01dd6225dea7a29265495`, version 0.39.1).

Layout is a **deterministic Flexbox/Grid engine** implemented in Rust — there
is no CSS cascade, no selector matching and no style sheet. Every style value
is a typed Rust value; `Style` is a plain builder struct.

## `Style`

`Style::empty()` plus chained setters (all `#[must_use]`, all take `self` by
value and return `Self`):

`display`, `position`, `row`, `column`, `grid(columns)`, `wrap`, `justify`,
`align`, `flex_grow`, `flex_shrink`, `width`, `height`, `min_width`,
`min_height`, `max_width`, `max_height`, `aspect_ratio`, `gap`, `padding`,
`margin`, `overflow`, `z_index`, `inset`, `background`, `gradient`, `border`,
`radius`, `shadow`, `focus_ring`, `opacity`, `cursor`, `pointer_events`,
`color`, `font_size`, `font_weight`, `font_family`, `text_align`,
`text_overflow`, `stop_scroll_propagation`, `stop_event_propagation`,
`resolve(breakpoint)`.

`resolve(breakpoint)` returns the variant for a `Breakpoint` — the mechanism
behind responsive styles (`Style::resolve(Breakpoint::Compact)`).

## Value types

| type | variants |
|---|---|
| `Length` | `Auto`, `Px(f32)`, `Percent(f32)`, `Fraction(f32)` (grid `fr`), `ViewportWidth(f32)` (`vw`), `ViewportHeight(f32)` (`vh`) |
| `Edges` | `Edges::new(t, r, b, l)`, `Edges::all(v)`, `Edges::symmetric(vertical, horizontal)`; `horizontal()`, `vertical()` |
| `CornerRadius` | per-corner, `CornerRadius::all(v)` |
| `Display` | `Flex`, `Block`, `Grid`, `None` |
| `Position` | `Relative`, `Absolute`, `Fixed` |
| `FlexDirection` | `Row`, `Column`, `RowReverse`, `ColumnReverse` |
| `FlexWrap` | `NoWrap`, `Wrap` |
| `JustifyContent` | `Start`, `Center`, `End`, `SpaceBetween`, `SpaceAround`, `SpaceEvenly` |
| `AlignItems` / `AlignSelf` | `Stretch`, `Start`, `Center`, `End` (`AlignSelf` adds `Auto`) |
| `Overflow` | `Visible`, `Hidden`, `Scroll` |
| `Breakpoint` | `Compact`, `Medium`, `Expanded` |
| `FontWeight` | `Light`, `Normal`, `Medium`, `SemiBold`, `Bold` |
| `TextAlign` / `TextOverflow` | `Left`/`Center`/`Right` · `Wrap`/`Clip`/`Ellipsis` |
| `FontFamily` | `Sans`, `Monospace`, `Serif` |

`Color`, `LinearGradient`, `Shadow`, `Border` and `CursorIcon` live in
`core/src/style/` alongside `Rect`, `Size`, `Point` and `Edges`.

## The engine

`LayoutEngine::compute(&mut self, tree: &mut SceneTree, viewport: Size) ->
LayoutStats` is the single entry point: it walks the retained graph, skips
clean subtrees (O(1) cached pass) and fills each node's `LayoutBox`. Damage
tracking is explicit — `BuildContext::collect_paint_damage(scale)` returns the
`DamageRegion` to rasterize, and `FrameStats::pixels_shaded` reports how much
of the framebuffer actually changed.

Consequences worth remembering:

- **Logical pixels everywhere.** DPI scale is applied by the renderer; a
  `width: Length::Px(100.0)` box is 100 logical px on a 2x display.
- **No cascade.** Two rules never "win" over each other; the last builder call
  sets the property. Sharing styles means calling the same `style!`-generated
  constructor.
- **Text measurement is part of layout** (`core/src/font/measurer/`), so a
  text node's intrinsic size is known before paint — no reflow-on-paint.
- Responsive behaviour comes from `Style::resolve` plus the `Breakpoint`
  signal (`use_breakpoint()`), not from media queries.
