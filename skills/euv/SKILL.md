---
name: euv
description: "Use when implementing or debugging an euv cross-platform native Rust UI: view!/style! macros, signals, scene graph, mounting, 7-platform targets and rendering modes, or driving the euv CLI. euv-ui components are a separate crate."
license: MIT
metadata:
  hermes:
    related_skills: [rust-standards, euv-ui-standards, git-standards]
---

# euv framework entry

## Shortest path

1. Resolve the target version and workspace with `cargo metadata --no-deps
   --format-version 1`; do not assume unreleased local APIs exist in a
   published package. `origin/master` is at **0.39.1** (`aac1c450`).
2. Load `rust-standards` plus exactly the relevant row below, not the whole
   API corpus.
3. euv is a **7-platform direct-OS-API framework** since #359: no WebView, no
   DOM, no CSS and no virtual DOM. `view!` builds a retained scene graph;
   `html!`/`class!`/`vars!` no longer exist and HTML tags are a compile error.
4. `App::new(AppConfig)?` / `App::headless(…)` / `App::with_platform(…)` create
   the runtime; `app.mount(|| -> NodeId)` takes a closure returning `NodeId`
   (not a selector string). `Signal::new(v)` is a plain constructor — there is
   no `use_signal` associated method any more.
5. Read the component and `view!` expansion before editing
   (`core/src/scene/tree/impl.rs`, `macros/src/view/`), and follow a
   neighboring shape; never invent props or syntax from another framework.
6. Verify the rendered path, not only a unit test: `cargo run -p euv-example --
   --headless --software` and compare `FrameStats::frame_hash` across platforms.

## Load by task

| Task | Reference |
|---|---|
| `view!`/`style!`/`tokens!`/`watch!`/`computed!`/`euv_main!` syntax | [Macros](references/api-macros.md) |
| Signal, Memo, Effect, Scope, Selector, batch | [Reactivity](references/reactive.md) |
| Scene graph, `BuildContext`, events, dynamic OTA slots | [Scene](references/scene.md) |
| Deterministic layout, `Style`, `Length`, breakpoints | [Layout](references/layout.md) |
| `RenderMode`, backends, frame loop, pixel parity | [Rendering](references/render.md) |
| `PlatformKind`, window config/commands, safe area, services | [Platform](references/platform.md) |
| `euv-ui` schemes, tokens, components, hooks, router | [UI](references/theme.md) |
| Core runtime full pub API | [Core API](references/api-core.md) |
| `euv-ui` full pub API | [UI API](references/api-ui.md) |
| CLI subcommands, targets, dev/OTA server | [CLI API](references/api-cli.md) |
| Docs crate and static site generation | [Docs API](references/api-docs.md) |
| Dev automation and the AI schema protocol | [Automation API](references/api-automation.md) |
| Benchmark suite | [Performance API](references/api-performance.md) |
| Symptom-first diagnosis | [Pitfalls](references/pitfalls.md) |
| euv UI layout, class registry and visual verification | [UI standards](../euv-ui-standards/SKILL.md) |

Reference pages are cached documentation, **not authority over the source or compiler**.

## Workspace shape

`cargo metadata` is authoritative for membership. Nine packages: the root `euv`
facade (`src/lib.rs` = `pub use {euv_core::*, euv_macros::*}`) plus `euv-core`,
`euv-macros`, `euv-ui`, `euv-automation`, `euv-docs`, `euv-cli`, `euv-example`
and `euv-performance`.

- `euv-core` owns the runtime: `app`, `dynamic`, `font`, `game`, `layout`,
  `media`, `platform`, `reactive`, `render`, `scene`, `style`, `system`,
  `window`. It depends only on `serde`, `serde_json`, `lombok-macros` and
  (wasm-only) `js-sys`/`web-sys`/`wasm-bindgen`.
- **`euv-ui` is not re-exported by the root crate** — add it separately.
  It ships 17 `theme-*` features plus `default`; there is no `theme-custom`.
  Features only pick the compile-time default scheme (`active_feature_scheme`);
  all 17 resolve at runtime through `ThemeTokens::resolve`.
- **Gone in 0.39:** the `euv-engine` and `euv-chart` crates (game/3D code now
  lives in `euv_core::game`), the DOM `fetch` module, the `html!`/`class!`/
  `vars!`/`component` macros, the CLI `bundle`/`--all`/`--platforms` surface,
  the multi-locale `docs/build.rs` pipeline, and the lombok re-export from the
  `euv` root.

**Check the registry before pinning a version.** CI publishes each member
separately with `crate publish`, so a new member is not installable until its
own publish step ran. The committed tree and the registry agree right now:
`origin/master` is `0.39.1` and all nine members are published at `0.39.1`
(crates.io API, checked one by one). `euv-chart` and `euv-engine` are frozen at
`0.37.15`.

## CLI and scripts

`cargo run -p euv-cli -- <cmd>`: `run`, `dev`, `docs`, `build`, `check`, `fmt`,
`doctor`, `new`. Targets are `--target <web|android|ios|ipad|macos|windows|
linux|native|all>`; `--render <auto|software|hardware|hybrid>`; every command
that spawns Cargo accepts `--plan` to print the plan instead. `dev` serves HMR
at `/__euv_hmr` and Dynamic-WASM OTA at `/__euv_ota/manifest.json`.

`scripts/` holds the environment and delivery helpers: `env/setup-{rust,web,
apple,android,all}.sh`, `env/doctor.sh`, `build/build-{web,ios-sim,
android-apk}.sh`, `test/e2e-all.sh`, `bench/stress-bench.sh`.

## What CI runs

`.github/workflows/rust.yml` defines the jobs; knowing which covers a change
saves a failed local guess.

| Job | What it runs |
|---|---|
| **setup** | reads the root `Cargo.toml` version and derives the `v<version>` tag |
| **check** | `cargo fmt --all -- --check` |
| **tests** | `cargo test -p euv-ui`, then `--no-default-features`, then `--features theme-shadcn`; `cargo test --all-features --workspace`; the performance crate via its own manifest |
| **clippy** | `cargo clippy -p euv-ui --no-default-features --all-targets -- -D warnings`, `--all-features --workspace --all-targets`, and the performance crate |
| **build** | `RUSTFLAGS="-D warnings" cargo check -p euv-core -p euv -p euv-ui` for all 7 triples, then headless smoke (`euv-example`, `euv-docs`), `euv-cli doctor`, `euv-cli build --target all --plan`, `scripts/bench/stress-bench.sh` and the release benchmark report |
| **package-*** | `build-apk.yml` (Android arm64 APK) and `build-clients.yml` (macOS/Windows/Linux, Web WASM, iOS-Simulator) attach release assets |
| **publish / release** | a tagged `master` push after `check`, `tests`, `clippy`, `build`: `crate publish` in dependency order, then a GitHub release with the multi-platform installers |

## Delivery constraints

- Code changes in a publishable workspace include a version increment. Change
  only the root `Cargo.toml` version; CI synchronizes members and dependencies,
  so never hand-edit dependency pins or run a second local version-sync path.
- Keep host-only checks honest: wasm-gated modules compile only for
  `wasm32-unknown-unknown`, which is one of the 7 triples CI checks.
- Use existing public APIs for integration tests; never widen visibility solely
  for tests. Use constant-based paths, routes and selectors.
- Follow [Git policy](../git-standards/SKILL.md) for delivery. Pure Git, generic
  Rust or Hyperlane work with no euv UI implementation is not this entry point.
