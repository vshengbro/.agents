# Scene graph, build context and events

Source: `core/src/scene/` at `origin/master` (`aac1c450d6e8317c50c01dd6225dea7a29265495`, version 0.39.1).

There is **no virtual DOM**. `view!` emits `BuildContext` calls that create
nodes in a flat, retained scene graph; only the changed nodes are re-laid-out
and re-painted (clean-subtree caching, ~23 ns for a cached pass).

## `NodeKind`

`View`, `Text(String)`, `Image(ImageBuffer)`, `Canvas`, `Input(InputNodeState)`,
`ScrollView`, `Portal`, `Fragment`.

## `BuildContext`

`view!` opens one implicitly via `current_build_context()`; `App::mount`
binds it for the whole root closure. Construction API (each returns `NodeId`):

| method | node |
|---|---|
| `create_node(kind, style)` | explicit kind |
| `create_view(style)` / `view(style)` | generic box |
| `create_text(text, style)` / `text(text, style)` | text run |
| `reactive_text(style, producer)` | text bound to a signal |
| `create_input(state, style)` / `input(state, style)` | editable input |
| `create_image(buffer, style)` / `image(buffer, style)` | bitmap |
| `create_canvas(style, painter)` / `canvas(style, painter)` | vector surface |
| `create_scroll_view(style)` / `scroll_view(style)` | clipped scroll container |
| `create_portal(style)` / `portal(style)` | overlay layer |
| `create_fragment()` | logical grouping, no box |

Structure: `append_child` / `append`, `replace_children`, `dispose_subtree`,
`get_node`, `get_node_mut`, `live_node_count`.

Per-node state: `set_style`, `set_text`, `set_scroll_offset`,
`set_virtual_scroll`, `node_screen_bounds`, `mark_dirty`, `is_node_visible`,
`update_focus`, `attach_scope`, `collect_paint_damage`.

Reactive bridges: `bind_text(node, producer) -> Effect`,
`bind_style(node, producer) -> Effect`, `bind_children(parent, builder)`.

Threading helpers: `with_build_context(ctx, op)`, `has_build_context()`,
`current_platform()`.

## `SceneHandle`

A cloneable handle to the tree shared with the `App`:
`SceneHandle::new_tree()`, `with_read(op, fallback)`, `with_write(op, fallback)`,
`bind_text`, `bind_style`, `node_screen_bounds`, `set_virtual_scroll`,
`start_transition`, `mark_dirty`, `has_active_transitions`. The read/write
entry points exist so non-UI threads (services, OTA fetchers) can touch the
tree without holding a borrow across a callback.

## Events

Handlers are attached per node, not delegated from a root:
`on_click`, `on_change`, `on_scroll`, `on_pointer_down`, `on_pointer_move`,
`on_pointer_up`, `on_hover`, `on_key`, plus `set_a11y(node, A11yProps)`.

`view!` props (`on_click: move |_: &UiEvent| { … }`) expand to exactly these
calls. `UiEventHandler` and `UiEvent` are the concrete event types;
`InputState` (polled keyboard/pointer/scroll) is the game-loop path, driven by
`App::step_game_frame`.

## Transitions

`NodeTransition` + `Easing` (`Linear`, `EaseOutCubic`, `EaseInOutCubic`,
`EaseOutBack`) drive animated property changes; `start_transition`,
`tick_transitions(dt)` and `has_active_transitions()` advance them, and
`App::has_active_animations()` reports whether the frame loop must keep
rendering.

## Dynamic (OTA) slots

`core/src/dynamic/` provides component-level and page-level live updates:
`DynamicUpdateHub` with `routes_signal()`, the `WasmDynamicManager` /
`RegistryWasmFetcher` / `WasmSandboxConfig` triple for hot-swapping wasm
modules, and the `slot { id: "…" }` / `page_slot { route: "/…" }` elements that
mount the current bundle with an optional `fallback` builder. The CLI's dev
server publishes the matching manifest (`/__euv_ota/manifest.json`).
