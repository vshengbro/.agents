# euv pitfalls (symptom → cause)

Verified against `origin/master` (`aac1c450d6e8317c50c01dd6225dea7a29265495`, version 0.39.1).
Re-verified against `origin/master` (`6ccb8599`, euv 0.43.0) on 2026-11-27: every declared API name below still resolves in that tree.
Every "where" is a real path in that tree.

## Compile errors after the 0.39 rewrite

| Symptom | Cause / fix |
|---|---|
| `HTML tag \`div\` is not part of native euv \`view!\`` | The old DOM vocabulary is gone; use `column`/`row`/`view`/`grid`, `text`, or an `euv-ui` component (`macros/src/view/fn.rs`, `legacy_html_tag_error`) |
| `view! manages Context automatically` | The legacy `view!(ctx, …)` form; write `view! { … }` (`ERR_LEGACY_VIEW_CTX`) |
| `unknown property` with a "did you mean" list | Property keywords are checked against `KNOWN_VIEW_PROPS`; values are Rust expressions, not CSS strings |
| `component parameters must be passed as named attributes inside \`Component { prop: value }\` instead of positional \`(...)\` arguments` | A custom component was invoked positionally; derive `Props` on it and use `MyComp { prop: value }` (`ERR_COMPONENT_POSITIONAL_ARGS`) |
| `#[derive(Props)] can only be derived on structs with named fields` | `Props` needs named fields; a tuple struct or enum cannot carry named props (`ERR_PROPS_NAMED_STRUCT_ONLY`) |
| `unsupported #[prop(...)] option; expected \`custom\` or \`default = <expr>\`` | Field-attribute namespace typo inside a `Props` struct (`ERR_PROPS_UNKNOWN_OPTION`) |
| `unresolved import euv::lombok_macros` | 0.39.1 dropped the lombok re-export from the `euv` root (`src/lib.rs`); add `lombok-macros` as a direct dependency |
| `unresolved import euv_chart` / `euv_engine` | Both crates were removed from the workspace in #359; charting has no replacement and the game/3D code now lives in `euv_core::game` |
| `cannot find trait \`Mountable\` in this scope` / `no function or associated item named \`mount_current\` found` | The legacy `Mountable` trait and `Style::empty()` were removed; implement `Component` (or use `#[component]`) and `Style::default()` |
| `use euv::*` does not bring in `EuvButton` | `euv-ui` is a separate crate and is **not** re-exported by the root; `cargo add euv-ui` + `use euv_ui::*` |
| `feature \`theme-custom\` does not exist` | Removed; `euv-ui` ships 17 `theme-*` features plus `default` |

## Reactivity

| Symptom | Cause / fix |
|---|---|
| effect re-runs forever | a tracking `get()` inside the effect writes the signal it reads; use `get_untracked()` in handlers and `batch()` for grouped writes |
| state leaks across routes | the signal was created outside the scope owning the route's nodes; pair `Scope::run` with `ctx.attach_scope(node, scope)` so unmount disposes it |
| text does not update | a plain `ctx.text(...)` instead of `reactive_text` / a closure child; only the reactive forms subscribe |
| 1000-row list stutters | one `Effect` per row; bind the container once with `bind_children`, or use `Selector<K>` for the active row |

## Rendering and platforms

| Symptom | Cause / fix |
|---|---|
| UI is blurry on a HiDPI display | logical pixels were treated as physical; `set_size` takes logical px and the renderer applies the scale factor |
| nothing renders on a non-macOS host | the backend is chosen from `PlatformKind`; verify with `cargo run -p euv-cli -- doctor` and build for the host triple (`cli/src/platform/`) |
| wasm-only code never compiled locally | `core/src/dynamic/wasm/`, `core/src/platform/web/` and parts of `font/system`, `render/software`, `render/gpu`, `game/engine3d/renderer` are `#[cfg(target_arch = "wasm32")]`; CI checks `wasm32-unknown-unknown` among the 7 targets, a host-only `cargo check` does not |
| pixels differ between platforms | compare `FrameStats::frame_hash` (FNV-1a) from `--headless --software` runs; a differing hash is a real divergence, not rounding |

## Build, test and release

| Symptom | Cause / fix |
|---|---|
| `euv build --all` / `--platforms` rejected | The `bundle` surface is gone; use `--target <…>` (`web`, `android`, `ios`, `ipad`, `macos`, `windows`, `linux`, `native`, `all`) and `--plan` to print the plan |
| member version out of sync after a bump | Only the root `[workspace.package]` version is hand-edited; CI publishes each member with `crate publish` in dependency order |
| `cargo test -p euv-ui` fails with no theme | `euv-ui`'s `default` feature set is empty; CI runs `--no-default-features` and `--features theme-shadcn` passes on purpose |
| performance benchmarks missing from the workspace run | `performance` is excluded from the published package and built as its own manifest (`--manifest-path performance/Cargo.toml`) |
| release build contains automation hooks | it must not — every `euv-automation` hook is `#[cfg(not(debug_assertions))]`; if code survives into release, the gate was bypassed |
