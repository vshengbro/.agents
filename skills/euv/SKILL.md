---
name: euv
description: "Use when implementing or debugging an euv reactive Rust UI: components, signals, macros, mounting and routing, or packaging its native clients with the euv CLI. Renderer backends use euv-engine-renderer-api."
license: MIT
metadata:
  hermes:
    related_skills: [rust-standards, euv-ui-standards, euv-engine-renderer-api]
---

# euv framework entry

## Index

Shortest path · Load by task · Workspace shape · Docs-site build · Native builds · CI · Delivery

## Shortest path

1. Resolve the target dependency version and actual workspace with `cargo metadata
   --no-deps --format-version 1`; do not assume unreleased local APIs exist in a
   published package. Read the component and mount entry before editing.
2. Load `rust-standards` plus exactly the relevant row below, not the whole API corpus.
3. Use current public APIs; keep component state in the framework hook lifecycle.
   `App::use_signal(init)` is an **associated method**, not a free `use_signal`;
   `App::mount(selector, render_fn)` takes a closure returning `VirtualNode`.
   Confirm both in `core/src/app/impl.rs`, and read the wasm entry in
   `example/src/lib.rs` rather than an uncompiled demo.
4. Follow an existing neighboring macro shape. Check `macros/src/lib.rs` and the
   specific implementation when syntax is uncertain; never invent JSX props,
   inheritance syntax or handler signatures from another UI framework.
5. Run the project's real formatting, compiler, lint and tests. For UI changes,
   verify the rendered path and the bytes/build it loaded, not only a unit test
   or a cache-busted URL. Preserve user work; reclaim temporary resources.

## Load by task

| Task | Reference |
|---|---|
| Components, html/class/vars/watch/computed macros | [Macro API](references/api-macros.md) |
| Signal, VirtualNode, events, hooks, node references | [Core API](references/api-core.md) |
| UI components, router, theme, i18n | [UI API](references/api-ui.md) |
| Game/scene/physics and engine abstractions | [Engine API](references/api-engine.md) |
| Charting: option model, display list, chart backends | [Chart API](references/api-chart.md) |
| CLI: run/build/fmt modes and native bundle planning | [CLI API](references/api-cli.md) |
| Docs-site components, locale tables | [Docs API](references/api-docs.md) |
| Docs-site build: locale bundles, document language, asset rebasing | [Docs build](references/docs-build.md) |
| Native release themes and the website update channel | [Native release](references/native-release.md) |
| WebGPU/WebGL renderer contracts and readback | [Renderer workflow](euv-engine-renderer-api/SKILL.md) |
| euv UI layout, class registry and visual verification | [UI standards](../euv-ui-standards/SKILL.md) |
| Symptom-first diagnosis | [Pitfalls](references/pitfalls.md) |

Reference pages are cached documentation, **not authority over the source or compiler**:
verify uncertain signatures; lombok accessors may not appear in `.rs` text.

## Workspace shape

`cargo metadata` is authoritative for membership and paths; the workspace holds
eleven packages: `euv` (root), `euv-core`, `euv-macros`, `euv-ui`, `euv-engine`,
`euv-cli`, `euv-docs`, `euv-example`, `euv-chart`, `euv-automation` and
`euv-performance` (the last two are tool crates).

`euv-chart` is the ECharts-compatible crate: an option model, a display list
built from it, and three interchangeable backends (WebGPU, WebGL2, Canvas2D)
behind one API. It depends on `euv-core` for `Signal` and on `euv-engine` for
`Tween`/`Easing`, and it does **not** re-export through the `euv` root crate, so
`use euv::*` misses chart types — see [references/api-chart.md](references/api-chart.md).

**Check the registry before pinning a version.** The repository's version is not
the published version: CI syncs member and dependency versions and then
publishes the workspace members one crate at a time, so a crate added to the
workspace is not installable by version until its own publish step has run.
Resolve what a consumer can actually install from the registry, not from
`Cargo.toml`: `cargo add euv-chart@<version>`, or
`curl -s -H 'User-Agent: skill-sync-audit/1.0' https://crates.io/api/v1/crates/euv-chart`
(the registry answers **403** without a `User-Agent`). The committed tree and
the registry agree right now: `origin/master` is at `0.36.2` and every workspace
member above is published at `0.36.2`, so the whole workspace is installable
in lockstep. CI owns the member versions.

## Docs-site build

`euv-docs` is a multi-locale static site: `docs/build.rs` reads `docs/README.md`
frontmatter (`site:` plus a `locales:` sequence of `prefix`/`dir`/`label`).

- The document language is bound to the **locale label**, not the frontmatter
  `lang:` key: `localize_document_output` sets `<html lang="…">` on `index.html`
  and copies it to `404.html`.
- Assets are hosted once: only the root bundle copies `public/`; a non-default
  bundle references it through rebased `../` URLs, and `rebase_asset_url` skips
  `http://` **and** `https://`.
- The locale dropdown is the shared `euv_dropdown_trigger` inside `euv_dropdown`,
  in its own dynamic hook lifecycle.

Details: [references/docs-build.md](references/docs-build.md).

## Native builds

The CLI's `bundle` module (`cli/src/bundle/`) adds a native build surface to `euv build`:

- `--all` builds every native deliverable **this host** can produce — not
  cross-compilation. A macOS host builds macOS, iOS device, iOS simulator and
  Android; a Linux host builds Linux and Android; a Windows host builds Windows
  only. An unsupported platform fails **before** compilation, not silently.
- `--platforms macos,android` names an explicit subset; `--plan` prints the
  resolved plan without building; `--native-path` points at another native
  project directory and requires `--all` or `--platforms`. The CLI refuses
  `--all` combined with `--platforms`.
- The native flags are **refused in `run` mode**: it serves pages in a browser
  and has no native deliverable.
- The web build runs **once**; its output directory and the build mode reach every
  native builder through `EUV_WEB_DIST` and `EUV_NATIVE_MODE`. Builds are sequential
  and a failing target stops the pipeline; `--dev`/`--profiling` stay web-only.
- The client lives in `native/tauri/` and keeps an **independent Cargo
  workspace** (the root `Cargo.toml` excludes `native/tauri/src-tauri`), so
  Android and desktop dependencies never enter the web workspace. Its tooling
  is grouped under `native/tauri/scripts/`, and the CLI resolves the script
  paths from `cli/src/bundle/const.rs`; the window is borderless and requests
  the per-display maximum refresh rate (`native/tauri/src-tauri/apple/display.m`).

**Release themes and the update channel.** `build_theme_variants.sh` builds all 19
release variants and writes `example/www/euv-release.json`; the native client
verifies that manifest before it flips the `active` pointer — see
[references/native-release.md](references/native-release.md).

## What CI runs

`.github/workflows/rust.yml` defines the jobs; knowing which covers a change saves a
failed local guess. Every job runs `crate sync` first.

- **tests** — `cargo test -p euv-ui` (plus `--no-default-features` and
  `--features theme-custom`), then `cargo test --all-features --workspace`, then
  the performance crate separately. The wasm tests are `wasm-pack test --node`
  run **from the `ui/` directory only**, so the engine's wasm-gated suites
  (`engine/tests/webgpu_regressions/`) are **not** executed by CI. A WebGPU fix
  needs a local `wasm-pack` run in `engine/` or a real browser check.
- **clippy** — `cargo clippy --all-features --workspace --all-targets -- -D warnings`.
- **build** — `cargo check --release --all-features --target wasm32-unknown-unknown
  --workspace` (excluding `euv-cli`/`euv-performance`), plus `cargo test --all-features -p euv-cli`.
- **automation** — runs `cargo run -p euv-automation` against a real Chrome and a
  matching driver, asserting a failing probe is **not** reported as success.
- **native clients** — `build-apk.yml` and `build-clients.yml` share one entry
  point: `cargo run -p euv-cli -- build --platforms <platform> --release
  --crate-path ./example` (Android in the APK workflow; `macos` and
  `ios,ios-simulator` in the client workflow). `build-clients.yml` builds the
  shared release web and its theme variants once on Linux; the Apple jobs verify
  that artifact — root layout, source stamps, manifest hashes — before the
  native CLI, on `macos-15-intel` with Xcode 16.4.
- **publish / release** — a tagged `master` push, after `check`, `tests`, `clippy`,
  `build` and `automation` all pass; they run `crate sync` themselves.

## Delivery constraints

- Code changes in a publishable workspace include a version increment. Change
  only the root `Cargo.toml` version; CI synchronizes member/dependency versions,
  so never hand-edit dependency pins or run a second local version-sync path.
- Use existing public APIs for integration tests; never widen visibility solely
  for tests. Use constant-based paths/selectors instead of inlining literals.
- Use `crate fmt` / `crate fmt --check` where the governing standards require it;
  generic rustfmt is not proof that macro bodies are correctly formatted.
- Follow [Git policy](../git-standards/SKILL.md) for delivery. Pure Git, generic
  Rust or Hyperlane work with no euv UI implementation is not this entry point.
