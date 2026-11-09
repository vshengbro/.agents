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

Shortest path · Load by task · Workspace shape · Native builds · What CI runs · Delivery constraints

## Shortest path

1. Resolve the target dependency version and actual workspace with `cargo metadata
   --no-deps --format-version 1`; do not assume local unreleased APIs exist in a
   published package. Read the existing component and mount entry before editing.
2. Load `rust-standards` plus exactly the relevant row below, not the whole API corpus.
3. Use current public APIs; keep component state in the framework hook lifecycle.
   `App::use_signal(init)` is an **associated method**, not a free `use_signal`.
   `App::mount(selector, render_fn)` takes a closure returning `VirtualNode`.
   Confirm these in `core/src/app/impl.rs`; see the actual wasm entry in
   `example/src/lib.rs` and its `app` component rather than copying an uncompiled demo.
4. Follow an existing neighboring macro shape. Check `macros/src/lib.rs` and the
   specific macro implementation when syntax is uncertain; do not invent JSX props,
   inheritance syntax or handler signatures from another UI framework.
5. Run the project's real formatting, compiler, lint and tests. For UI changes,
   verify the rendered path and the bytes/build it loaded, not only a unit test
   or a cache-busted URL. Preserve user work and reclaim temporary verification resources.

## Load by task

| Task | Reference |
|---|---|
| Components, html/class/vars/watch/computed macros | [Macro API](references/api-macros.md) |
| Signal, VirtualNode, events, hooks, node references | [Core API](references/api-core.md) |
| UI components, router, theme, i18n | [UI API](references/api-ui.md) |
| Game/scene/physics and engine abstractions | [Engine API](references/api-engine.md) |
| Charting: option model, display list, chart backends | [Chart API](references/api-chart.md) |
| CLI: run/build/fmt modes and native bundle planning | [CLI API](references/api-cli.md) |
| WebGPU/WebGL renderer contracts and readback | [Renderer workflow](euv-engine-renderer-api/SKILL.md) |
| euv UI layout, class registry and visual verification | [UI standards](../euv-ui-standards/SKILL.md) |
| Symptom-first diagnosis | [Pitfalls](references/pitfalls.md) |

Reference pages are cached documentation, **not authority over the selected source
or compiler**. Verify uncertain signatures and source paths before use; generated
lombok accessors may not appear in `.rs` text. Load a single topical tutorial from
`references/` when the signature alone is insufficient.

## Workspace shape

`cargo metadata` is authoritative for membership and paths; the workspace holds
eleven packages: `euv` (root), `euv-core`, `euv-macros`, `euv-ui`, `euv-engine`,
`euv-cli`, `euv-docs`, `euv-example`, `euv-chart`, `euv-automation` and
`euv-performance`. The last two are tool crates, not library surface:
`euv-automation` drives real Chrome against a fixture, `euv-performance` runs
reproducible CPU and allocation benchmarks.

`euv-chart` is the ECharts-compatible crate: an option model, a display list
built from it, and three interchangeable backends (WebGPU, WebGL2, Canvas2D)
behind one API. It depends on `euv-core` for `Signal` and on `euv-engine` for
`Tween`/`Easing`; it does **not** re-export through the `euv` root crate, so
`use euv::*` does not reach chart types. Read
[references/api-chart.md](references/api-chart.md) before using it.

**Check the registry before pinning a version.** The repository's version is not
the published version: CI syncs member and dependency versions and then
publishes the workspace members one crate at a time, so a crate added to the
workspace is not installable by version until its own publish step has run.
Resolve what a consumer can actually install from the registry, not from
`Cargo.toml`: `cargo add euv-chart@<version>`, or
`curl -s https://crates.io/api/v1/crates/euv-chart`.

Three versions now differ and only the last is installable: the committed tree is
at `0.34.7`, the local worktree is at `0.34.16` (uncommitted), and every member
is published at `0.34.2` — `0.34.3` and later are not on crates.io. The committed
root `Cargo.toml` still pins its `[workspace.dependencies]` members at `0.34.2`.
Re-check the registry rather than trusting this paragraph when it matters.

## Native builds

The CLI's `bundle` module (`cli/src/bundle/`) adds a native build surface to
`euv build`:

- `--all` builds every native deliverable **this host** can produce — not
  cross-compilation. A macOS host builds macOS, iOS device, iOS simulator and
  Android; a Linux host builds Linux and Android; a Windows host builds Windows
  only, because the Android helper needs macOS or Linux.
- `--platforms macos,android` names an explicit subset; `--plan` prints the
  resolved plan and exits without building; `--native-path` points at another
  native project directory and requires `--all` or `--platforms`.
- The native flags are **refused in `run` mode**: it serves pages in a browser
  and has no native deliverable to produce.
- The web build runs **once**; its output directory reaches every native builder
  through the `EUV_WEB_DIST` environment variable. Builds are sequential and a
  failing target stops the pipeline with its own exit status. `--dev` and
  `--profiling` stay web-only; native packaging is release-only.
- Requesting a platform this host cannot build fails **before** compilation
  instead of being silently omitted.
- The client lives in `native/tauri/` and keeps an **independent Cargo
  workspace** (the root `Cargo.toml` excludes `native/tauri/src-tauri`), so
  Android and desktop dependencies never enter the web framework workspace.
- The client also gained immersive borderless windows and per-display
  maximum-refresh-rate requests (`native/tauri/src-tauri/apple/display.m`).
- The client tooling is grouped by responsibility under
  `native/tauri/scripts/` (`build/`, `cache/`, `config/`, `toolchain/`,
  `validation/`, `benchmark/`, `tests/`). The CLI resolves the two script
  paths from `cli/src/bundle/const.rs` — `ANDROID_BUILD_SCRIPT_PATH` is
  `scripts/build/build.sh` and `BUILD_CLIENT_SCRIPT_PATH` is
  `build/build-client.js` — so a moved script is a constant change, not a
  silent failure.

## What CI runs

`.github/workflows/rust.yml` defines the jobs; knowing which one covers a change
saves a failed local guess.

- **tests** — `cargo test -p euv-ui` (plus `--no-default-features` and
  `--features theme-custom`), then `cargo test --all-features --workspace`, then
  the performance crate separately. The wasm tests are `wasm-pack test --node`
  run **from the `ui/` directory only** — the engine's wasm-gated suites
  (`engine/tests/webgpu_regressions/`, gated on `#[cfg(target_arch = "wasm32")]`
  in `engine/tests/mod.rs`) are therefore **not** executed by CI. A WebGPU fix
  needs a local `wasm-pack` run in `engine/` or a real browser check; a green CI
  run does not cover it.
- **clippy** — `cargo clippy --all-features --workspace --all-targets -- -D warnings`.
- **build** — `cargo check --release --all-features --target wasm32-unknown-unknown
  --workspace`, excluding `euv-cli` and `euv-performance`, plus a host-side
  `cargo test --all-features -p euv-cli`.
- **automation** — a separate job runs `cargo run -p euv-automation` against a
  real Chrome and a matching driver, and a second step asserts that a failing
  probe is **not** reported as success.
- **native clients** — two further workflows, `build-apk.yml` and
  `build-clients.yml`, share one entry point: `cargo run -p euv-cli -- build
  --platforms <platform> --release --crate-path ./example` (Android in the APK
  workflow; `macos`, and `ios,ios-simulator`, in the client workflow). The old
  two-step "build the web pages, then run `node scripts/build-client.js`" is
  gone: one CLI command builds the web snapshot and the client embedding it.

## Delivery constraints

- Code changes in a publishable workspace include a version increment. Change
  only the root `Cargo.toml` version; CI synchronizes member/dependency versions.
  Do not hand-edit dependency pins or run a second local version-sync path.
- Use existing public APIs for integration tests; never widen visibility solely
  for tests. Respect constant-based paths/selectors instead of inlining literals.
- Use `crate fmt` / `crate fmt --check` where required by the governing standards;
  generic rustfmt is not proof that framework macro bodies are correctly formatted.
- Follow [Git policy](../git-standards/SKILL.md) for delivery. Pure Git, generic
  Rust or Hyperlane work with no euv UI implementation is not this entry point.
