# euv Framework Pitfall Quick Reference (symptom → cause index)

Symptom-first lookup. Each row names the symptom you observed and the cause or
the place to look. Every "where" below is a real path in the repo — this file
carries no links to documents that don't exist.

## Symptom Index

| Symptom | Cause / where to look |
|---|---|
| reactive `if` switches arms, but the click handler of the new arm does not respond | The handler is not rebound along with the arm; check the event registration path in `core/src/renderer/`, or use a class toggle instead of that shape |
| `Signal` state lingers across arms / routes, overlay is misaligned | Component state is not cleaned up on unmount; check whether the hook's cleanup is registered |
| iOS Safari treats a tap on a `<div>` as a scroll, so delegated `onclick` silently stops working | Touch-vs-scroll detection is left to the browser; use a real `<button>` for clickable elements |
| A canvas with a fixed aspect ratio is stretched into an ellipse inside a fullscreen container | The container does not lock the aspect ratio; add `aspect-ratio` to the container |
| A large dead blank area appears at the top of the header/drawer | Wrong use of `env(safe-area-inset-top)`; see the `--euv-mobile-safe-top` variable contract in `euv-ui-standards` §2.3 |
| `euv fmt` and `cargo fmt --check` disagree | `cargo fmt` does not reflow macro bodies; always use the macro-aware `euv fmt` for `class!`/`html!` |
| A downstream crate writing `euv = "*"` ends up with mismatched CSS / API | Dependency drift; the version is decided only by the root `[workspace.package]`, pin it to the same version |
| After a bump the sub-crate version is stale, or the master push fails | Check the root version commit, the sync pipeline and its result; member/dependency versions are synced by CI, do not run a separate local version-bump path |
| `use_async` still fires after the component unmounts | The async hook lacks cleanup (`use_async` lives in `ui/src/hook/`) |
| A profiler hook on the hot path slows down production builds | Measurement code leaked into the release path (`use_profiler`) |
| Signal subscription lifetime does not match the DOM node → memory grows | The subscription is not unbound when the node is destroyed |
| `use_node_ref` mixes up ids when there are multiple render roots | A NodeRef is reused across roots; take one per root (`core/src/app/impl.rs`) |
| Some cases of the signal re-render path do not take effect | The `patch_attributes` fast-path is not reached; check `core/src/renderer/render/impl.rs` |
| css reset / keyframes conflict with page CSS in specificity | Injection order: `inject_app_global_css` (`ui/src/style/css/fn.rs`); raise specificity with an `html body` prefix |
| The internal CSS minify / inline pipeline blows the stack on some inputs | Macro output size or nesting depth; see the flattening selector rule in `euv-ui-standards` §3.G |
| Wrong crates.io publish order at release time → path-dep resolution failure | Check against the real dependency graph and the publish pipeline; the order in which workspace members are listed is not itself proof of a topological order |
| Downstream `cargo add euv-chart` reports "could not be found in registry index" | The crate is published, so the consumer's index/lockfile is stale; run `cargo update` / refresh the index, and check the registry for the version that actually exists |
| After writing `euv-chart = "0.32"` cargo cannot resolve it | Repository version ≠ published version; ask the registry which version exists (`curl -s -H 'User-Agent: skill-sync-audit/1.0' https://crates.io/api/v1/crates/euv-chart` — a bare `curl` is refused with 403) instead of reading `Cargo.toml` |
| Expecting `use euv::*` to give you the chart types | The `euv` root crate does not re-export chart; get the chart types from `euv_chart::*` |
| The chart renders blank but reports no error | First confirm which backend was selected: `BackendKind::name()` returns `webgpu` / `webgl2` / `canvas2d` |
| The chart animation does not move | The animation is advanced by `Chart::advance(delta)`; without calling it only the first frame is drawn |
| `euv run --all` (or `--platforms`) is rejected | The native flags select a native build, which the run mode cannot perform; use `euv build` instead |
| The docs locale dropdown stops responding after a route change | Its trigger must be the shared `euv_dropdown_trigger` inside `euv_dropdown`, rendered in its **own** `VirtualNode::create_dynamic` hook lifecycle (`docs/src/component/layout/view/fn.rs`); a document-level listener registered in the shell root loses its callbacks when the route re-renders |
| A docs page is served with the wrong `<html lang>` | The language is bound to the **locale label**, not to the frontmatter `lang:` key: `document_language_for_label` writes `.deploy/document-lang.txt`, and `localize_document_output` rewrites `index.html` and copies it to `404.html` (`docs/src/document_html/`) |
| An absolute `https://` badge is rewritten to a broken `../https://…` URL in a non-default locale bundle | `rebase_asset_url` skips `https://` as well as `http://`; a relative asset is the only thing it rebases |
| A cargo feature named `theme-custom` no longer resolves | It was deleted from `euv-ui`, `euv-example` and `euv-docs`; `git grep theme-custom origin/master` is empty. Use `theme-shadcn` when a test needs one concrete theme — the generic custom-attribute API is unrelated and still exists |
| A removed theme reappears in a release build | `build_theme_variants.sh` prunes retired themes from `example/www/themes/` and `native/tauri/.cache/themes/*.sha256` and asserts the output set equals the current features; if a stale variant survives, the cache was restored from outside the script |
| The release output contains the `__euv_reload` bootstrap | A development build leaked into the release tree; the theme script and the publication validator both refuse such an output |
| The docs mobile drawer keeps focus in the page behind it | The drawer is a modal: `use_docs_drawer_modal` installs the `focusin`/`keydown` listeners and `sync_docs_drawer_focus` sets `inert` on `.c_mobile_header, .c_mobile_main` (`docs/src/component/layout/drawer/`) |
| Closing the docs drawer does not return focus to the menu button | Focus is restored only when the saved opener is still `docs-mobile-drawer-trigger` **and** still available (not hidden, inert, disabled or `visibility: hidden`) |
| `Escape` closes the docs drawer while the locale menu is open | `Escape` dismisses the innermost surface: the nested locale menu first, the drawer only when nothing else is open |
| The docs shell leaks listeners when the viewport crosses the mobile breakpoint | `use_docs_responsive_scope` must unsubscribe and call `HookContext::switch_arm(1)` when the responsive mode stops matching the owner |
| The docs search placeholder or status text is still English | The hardcoded `HEADER_SEARCH_*` and `THEME_TOGGLE_TITLE` constants were deleted; the strings come from `locale_text(route, DOCS_KEY_SEARCH_*)` in `docs/src/locale/const.rs` |
| The website release is published twice, or an old release replaces a newer one | Publication is manual (`pages.yml` `workflow_dispatch` with `source_run_id`); `publish_release.py` refuses to replace a newer live release and verifies every published byte |
| A `<p>`'s text keeps its old value while the element's siblings change | `{ expr }` as an element child is **always** a `VirtualNode::Dynamic` (`macros/src/html/impl.rs`), and the renderer keeps the old node for a `(Dynamic, Dynamic)` patch (`core/src/renderer/render/impl.rs`). Bind the text to a `Signal<String>` and read `signal.get()` so the text node is signal-bound — this is what `docs/src/component/password_gate/view/fn.rs` does with `error_signal.get()`. A `key:` on the element does **not** help |
| A component's body never re-renders when a signal it read changes | A component body renders **once**; wrap it in `VirtualNode::create_dynamic(move \|ctx\| {...})` so a signal read inside it registers the dependency and re-renders it (`docs/src/component/layout/view/fn.rs`, `docs/src/component/header/view/fn.rs`) |
| The docs home page shows no catalog, or the catalog card never appears | The catalog request goes through `core/src/fetch/`, which is `#[cfg(target_arch = "wasm32")]`. A **host** build has no page to fetch from, so it renders the failure state on purpose (`docs/src/component/catalog/view/fn.rs`); the request is issued only in a wasm build |
| The catalog card renders but its labels are the raw keys | The six `docs.catalog.*` keys must be present in **all four** locale tables (`docs/src/locale/const.rs`), each `[(&str, &str); 21]`; `locale_text` falls back to the English table and then to the key itself, so a missing entry shows the key |
| The catalog request fires twice, or the retry button sends a second request on the first render | The component owns the request: it is issued from the loading state, and the retry button re-enters that state — so exactly one request goes out per state entry, not per render |
| A `core` change compiles on the host but breaks the wasm build | The crate's test module is `#[cfg(target_arch = "wasm32")]`, so a host-only `cargo check` never compiles it. CI runs `wasm-pack test --node` from `core/`; run it locally the same way |
| A published locale bundle is rejected by the artifact service (8 MiB per-file ceiling) | The browser bundle links a heavy engine. A ```mermaid diagram is a **build-time** dependency of `euv-docs` (`[build-dependencies] merman`), so the bundle carries the finished SVG and no engine (`docs/diagram/`, `docs/Cargo.toml`) |
| A diagram renders in one theme but not the other | The engine's default theme paints the boxes with an inline `style`, and an inline style beats every stylesheet rule. Compile a **preset** theme instead (`ThemePreset::EditorLight` in `docs/diagram/fn.rs`); the scoped stylesheet then decides the colours from the docs theme tokens |
| The mermaid diagram's actor labels are invisible in dark mode | The theme sheet used to be handed to the engine as a caller-supplied `scoped_css`, and that never reached the rendered output. `apply_theme_sheet` appends it to the **finished SVG**, `scope_theme_sheet` prefixes every selector with `#docs-mermaid-<ordinal>`, and it lands **after** the engine's own `<style>` so it wins on source order. `SvgOutputPolicy::scoped_css` stays `None`; `CssOverridePolicy::StripExistingImportant` stays, because an `!important` beats a later rule of any specificity (`docs/diagram/fn.rs`) |
| The docs home page shows the catalog's failure state and a retry button, with no projects | `parse_catalog` refused a **qualified** `org/repo` name before 0.37.15, so the whole payload failed to parse. `is_safe_artifact_name` accepts one safe segment **or** two joined by `/` (`ORG_REPO_SEPARATOR`); each segment must still be safe on its own, and a third segment is refused (`docs/src/component/catalog/view/fn.rs`) |
| A sidebar row reserves far more height than its content needs, pushing the list past a screen | `nav-row-height` / `nav-row-padding` are the binding minimum, not decoration: since 0.37.15 they are `calc(control-height + space-xs)` and `space-sm-md` in **both** scheme blocks (40px reserved, was 52px). They are consumed by `c_nav_item_active` / `c_nav_item_inactive` (`ui/src/style/class/shell/fn.rs`) and pinned by `ui/tests/theme/fn.rs` plus `ui/tests/spacing_contract/fn.rs` |
| A mermaid fence shows up as a plain code block | The engine could not lay the diagram out; `render_diagram` returns `None` and the build deliberately keeps the ordinary code block so the source stays readable. The engine names the missing Cargo feature in its error |
| A caret sits on top of a long trigger label, or the label pushes the caret away | The gap is the shared `gap-caret` token (`8px`), declared in both theme blocks; every caret-bearing trigger declares it and reserves a 16px box that refuses to shrink (`ui/src/style/class/forms/fn.rs`) |
| The trigger's label shows no ellipsis after the control is cleared | The **placeholder** class needs the same ellipsis contract as the value class (`flex: 1`, `min-width: 0`, `overflow: hidden`, `text-overflow: ellipsis`, `white-space: nowrap`) — the ellipsis used to vanish with the selection |
| The release upload fails on a large artifact | The publisher is **per file**, not one archive: `MAX_FILE_BYTES` is 8 MiB per file, `MAX_FILE_COUNT` 8192 files and `MAX_TOTAL_BYTES` 512 MiB in total, all checked before any upload (`example/scripts/publish_release.py`). The chunked archive protocol is gone — there is no `X-Chunk-SHA256` |
| The published site shows a different version than the one that was built | The publisher verifies the commit receipt, the public catalog entry and every live release byte after the commit, and refuses to replace a newer live release; the artifact is published under `<org>/<repo>` (`--org` / `--repo`), served from `/pages/<org>/<repo>/` with the legacy `/pages/<repo>/` alias still resolving |

## euv-chart Deep Dive

`euv-chart` is a standalone crate (`chart/`), not re-exported through the `euv`
root crate; when verifying, look directly at `chart/src/`:

| Point | Location |
|---|---|
| crate root export list | `chart/src/lib.rs` |
| three backends + shared trait | `chart/src/backend/{webgpu,webgl,canvas2d,common}/` |
| option model (ECharts compatible) | `chart/src/option/` |
| display list and draw commands | `chart/src/display/` |
| chart instance and command channel | `chart/src/chart/` (`Chart` / `ChartHandle` / `ChartCommand`) |
| typesetting and text measurement | `chart/src/geom/`, `chart/src/text/` |

- `Chart::create(canvas)` is **async** and returns `Option<Chart>`; it is `None`
  when the host has no DOM, not a panic.
- Commands are passed through `euv_core::Signal<Vec<ChartCommand>>`; `ChartHandle` is `Copy`,
  and a copy still points at the same chart.
- The backend has a fixed fallback chain: WebGPU → WebGL2 → Canvas2D. `BackendKind::is_gpu()` tells you
  whether the GPU path is used.
- That crate does have a test directory (`chart/tests/`), wired into the library by a
  `#[cfg(test)] #[path = "../tests/mod.rs"] mod tests;` line in `chart/src/lib.rs`; the
  host suites cover scale and extent maths, while the rendering still needs a real browser.

## Division of Labor Between Tools

| Tool | Provides | Does not provide |
|---|---|---|
| `euv` (euv-cli) | `run` / `build` / `fmt` / `help` | `bump` / `sync` / `publish` |
| `crate-cli` (`~/.cargo/bin/crate`) | `bump` / `sync` / `fmt` / `publish` | dev server / template generation |
| `cargo fmt` | impl code | reordering `class!` / `html!` macro bodies |

## Keyword Quick Reference

- **click does not respond** → reactive `if` arm-switch row / iOS delegated row
- **state misaligned** → unmount-without-cleanup row / `use_node_ref` cross-root row
- **style fallback** → dependency-drift row / `inject_app_global_css` specificity row
- **build / publish failure** → `euv fmt` row / bump sync row / publish order row
- **theme feature missing** → `theme-custom` removal row
- **catalog shows the failure state** → qualified `org/repo` name row
- **diagram invisible in dark mode** → diagram theme-sheet row
- **sidebar row too tall** → `nav-row-height` / `nav-row-padding` row
- **focus lost in the docs drawer** → drawer focus containment / restoration rows
- **stale release bytes** → retired-theme pruning row / `__euv_reload` row
