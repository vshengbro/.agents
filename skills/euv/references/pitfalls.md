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
