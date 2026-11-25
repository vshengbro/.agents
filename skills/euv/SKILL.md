---
name: euv
description: "Use when implementing or debugging an euv reactive Rust UI: components, signals, macros, mounting and routing, or packaging its native clients with the euv CLI. Renderer backends use euv-engine-renderer-api."
license: MIT
metadata:
  hermes:
    related_skills: [rust-standards, euv-ui-standards, euv-engine-renderer-api]
---

# euv framework entry

## Shortest path

1. Resolve the target dependency version and actual workspace with `cargo metadata
   --no-deps --format-version 1`; do not assume unreleased local APIs exist in a
   published package. Read the component and mount entry before editing.
2. Load `rust-standards` plus exactly the relevant row below, not the whole API corpus.
3. Use current public APIs; keep component state in the framework hook lifecycle.
   `App::use_signal(init)` is an **associated method**, not a free `use_signal`;
   `App::mount(selector, render_fn)` takes a closure returning `VirtualNode`
   (confirm both in `core/src/app/impl.rs`).
4. Follow an existing neighboring macro shape. Check `macros/src/lib.rs` and the
   specific implementation when syntax is uncertain; never invent JSX props,
   inheritance syntax or handler signatures from another framework.
5. Run the project's real formatting, compiler, lint and tests. For UI changes,
   verify the rendered path and the bytes/build it loaded, not only a unit test.
   Preserve user work; reclaim temporary resources.
6. A `#[cfg(target_arch = "wasm32")]` module compiles on **neither** path of a
   host-only check (`core/src/fetch/` is wasm-only) — run `wasm-pack test --node` there.

## Load by task

| Task | Reference |
|---|---|
| Components, html/class/vars/watch/computed macros | [Macro API](references/api-macros.md) |
| Signal, VirtualNode, events, hooks, node references, fetch | [Core API](references/api-core.md) |
| UI components, router, theme, i18n | [UI API](references/api-ui.md) |
| Game/scene/physics and engine abstractions | [Engine API](references/api-engine.md) |
| Charting: option model, display list, chart backends | [Chart API](references/api-chart.md) |
| CLI: run/build/fmt modes and native bundle planning | [CLI API](references/api-cli.md) |
| Docs-site components, locale tables and the multi-locale build | [Docs API](references/api-docs.md) · [Docs build](references/docs-build.md) |
| Native release themes and the website update channel | [Native release](references/native-release.md) |
| WebGPU/WebGL renderer contracts and readback | [Renderer workflow](euv-engine-renderer-api/SKILL.md) |
| euv UI layout, class registry and visual verification | [UI standards](../euv-ui-standards/SKILL.md) |
| Symptom-first diagnosis | [Pitfalls](references/pitfalls.md) |

Reference pages are cached documentation, **not authority over the source or compiler**.

## Workspace shape

`cargo metadata` is authoritative for membership and paths; the workspace holds
eleven packages: `euv` (root), `euv-core`, `euv-macros`, `euv-ui`, `euv-engine`,
`euv-cli`, `euv-docs`, `euv-example`, `euv-chart`, `euv-automation` and `euv-performance` (the last two are tool crates).

`euv-chart` is the ECharts-compatible crate: an option model, a display list
built from it, and three interchangeable backends (WebGPU, WebGL2, Canvas2D)
behind one API. It does **not** re-export through the `euv` root crate, so `use
euv::*` misses chart types — see [references/api-chart.md](references/api-chart.md).

**Check the registry before pinning a version.** The repository's version is not
the published version: CI syncs member and dependency versions, then publishes
each member separately, so a new member is not installable until its own publish
step ran. Resolve what a consumer can install with `cargo add euv-chart@<version>`
or `curl -s -H 'User-Agent: skill-sync-audit/1.0'
https://crates.io/api/v1/crates/euv-chart` (the registry answers **403** without a
`User-Agent`). The committed tree and the registry agree right now: `origin/master`
is at `0.37.15` and all eleven members are published at `0.37.15` (crates.io API,
checked one by one). There is **no `theme-custom` feature** — it was deleted from
`euv-ui`, `euv-example` and `euv-docs` (`git grep theme-custom origin/master`
returns nothing); `euv-ui` ships 17 `theme-*` features plus `default`, and
`theme-shadcn` is the one to use when a test needs a concrete theme.

## Docs-site build

`euv-docs` is a multi-locale static site: `docs/build.rs` reads `docs/README.md`
frontmatter (`site:` plus a `locales:` sequence of `prefix`/`dir`/`label`).

- The document language is bound to the **locale label**, not the frontmatter
  `lang:` key: `localize_document_output` rewrites the document's `lang`
  attribute on `index.html` and copies it to `404.html`.
- Assets are hosted once: only the root bundle copies `public/`; a non-default
  bundle references it through rebased `../` URLs, and `rebase_asset_url` skips
  `http://` and `https://`.
- The locale dropdown is the shared `euv_dropdown_trigger` inside `euv_dropdown`,
  in its own dynamic hook lifecycle. The mobile drawer is a **modal dialog**:
  `docs/src/component/layout/drawer/` owns focus containment and restoration, the
  `inert` boundary, and `Escape` handling that closes a nested locale menu first.
- Shell strings come from the locale tables in `docs/src/locale/const.rs` (21 keys
  × 4 locales), not from hardcoded English; the search field paints its focus ring
  as a `box-shadow` over `--ring-width` / `--ring-offset` / `--ring`. The nav row
  is **compact** since 0.37.15: `nav-row-height: calc(control-height + space-xs)`
  with `nav-row-padding: space-sm-md` in both scheme blocks.
- The public catalog is **rendered in Rust**: `docs/src/component/catalog/`
  fetches `/api/page-artifacts` through the framework's own `fetch` primitive
  and paints one card per stored project — the site ships no catalog script and
  no catalog stylesheet of its own. `parse_catalog` accepts a bare segment **or**
  two safe segments joined by `/` (`ORG_REPO_SEPARATOR`); a third is refused.
- A ```mermaid fence is **rendered at build time** into inline SVG by `merman`, a
  `[build-dependencies]` entry of `euv-docs`; the bundle links no diagram engine.
  The theme sheet is **appended to the finished SVG**, each selector scoped to the
  diagram id and after the engine's stylesheet, so it wins on source order.

Details: [references/docs-build.md](references/docs-build.md).

## Native builds

The CLI's `bundle` module (`cli/src/bundle/`) adds a native build surface to `euv build`:

- `--all` builds every native deliverable **this host** can produce — not
  cross-compilation. macOS builds macOS, iOS device, iOS simulator and Android;
  Linux builds Linux and Android; Windows builds Windows only. An unsupported
  platform fails **before** compilation, not silently.
- `--platforms macos,android` names an explicit subset; `--plan` prints the
  resolved plan without building; `--native-path` points at another native
  project directory and requires `--all` or `--platforms`. The CLI refuses
  `--all` combined with `--platforms`.
- The native flags are **refused in `run` mode**: it serves pages in a browser,
  with no native deliverable.
- The web build runs **once**; its output directory and the build mode reach every
  native builder through `EUV_WEB_DIST` and `EUV_NATIVE_MODE`. Builds are
  sequential and a failing target stops the pipeline; `--dev`/`--profiling` stay web-only.
- The client lives in `native/tauri/` and keeps an **independent Cargo
  workspace** (the root `Cargo.toml` excludes `native/tauri/src-tauri`), so its
  Android and desktop dependencies never enter the web workspace.

**Release themes and the update channel.** `build_theme_variants.sh` builds all 18
release variants (17 `theme-*` features plus `default`) and writes
`example/www/euv-release.json`; the native client verifies that manifest before it
flips the `active` pointer. The script **prunes retired themes** and refuses an
output still carrying the `__euv_reload` bootstrap. The website copy is published
per file by `example/scripts/publish_release.py` — see [references/native-release.md](references/native-release.md).

## What CI runs

`.github/workflows/rust.yml` defines the jobs; knowing which covers a change saves a
failed local guess. Every job runs `crate sync` first.

| Job | What it runs |
|---|---|
| **check** | `cargo fmt --all -- --check`; `example/scripts/validation/source.py` (live route/theme inventory, removed-feature wiring); `python3 example/scripts/test_publish_release.py` (publication protocol regressions — the publisher is the only path that writes the public release, so its contract is gated on every change); `node --test native/tauri/scripts/tests/theme-build.test.js` (retired-theme cache) |
| **tests** | `cargo test -p euv-ui` (plus `--no-default-features` and `--features theme-shadcn`), `cargo test --all-features --workspace`, then the performance crate separately. The wasm tests are `wasm-pack test --node` run from the `ui/` **and** `core/` directories — `core/` is a separate step because that crate's test module is `#[cfg(target_arch = "wasm32")]`, so the host run never compiles it. The engine's wasm-gated suites (`engine/tests/webgpu_regressions/`) are still **not** executed by CI — a WebGPU fix needs a local `wasm-pack` run in `engine/` or a real browser check |
| **clippy** | `cargo clippy --all-features --workspace --all-targets -- -D warnings`, plus a `--no-default-features` `euv-ui` pass and the performance crate |
| **build** | `cargo check --release --all-features --target wasm32-unknown-unknown --workspace` (excluding `euv-cli`/`euv-performance`), plus `cargo test --all-features -p euv-cli` |
| **automation** | `cargo run -p euv-automation` against a real Chrome and a matching driver, asserting a failing probe is **not** reported as success; then a **pinned `wasm-pack 0.15.1`**, the release example build and `example/scripts/validation/runtime.py` over every route |
| **native clients** | `build-apk.yml` and `build-clients.yml` share one entry point: `cargo run -p euv-cli -- build --platforms <platform> --release --crate-path ./example`. `build-clients.yml` builds the shared release web and its theme variants once on Linux; the Apple jobs verify that artifact (root layout, source stamps, manifest hashes) before the native CLI, on `macos-15-intel` with Xcode 16.4 |
| **publish / release** | a tagged `master` push, after `check`, `tests`, `clippy`, `build` and `automation` pass; they run `crate sync` themselves |
| **pages** | `pages.yml` is **manual only** (`workflow_dispatch` with a required `source_run_id`). It consumes the shared artifact from a successful `build-clients.yml` master run, rejects a release superseded by a newer master, verifies every release byte and publishes through the page-artifact API — it no longer deploys to GitHub Pages |

## Delivery constraints

- Code changes in a publishable workspace include a version increment. Change only
  the root `Cargo.toml` version; CI synchronizes member/dependency versions, so
  never hand-edit dependency pins or run a second local version-sync path.
- Use existing public APIs for integration tests; never widen visibility solely
  for tests. Use constant-based paths/selectors instead of inlining literals.
- Use `crate fmt` / `crate fmt --check` where the governing standards require it;
  generic rustfmt is not proof that macro bodies are correctly formatted.
- Follow [Git policy](../git-standards/SKILL.md) for delivery. Pure Git, generic
  Rust or Hyperlane work with no euv UI implementation is not this entry point.
