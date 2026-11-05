---
name: euv
description: "Use when implementing or debugging an euv reactive Rust UI: components, signals, macros, mounting and routing. Renderer backends use euv-engine-renderer-api; euv design tokens use euv-ui-standards."
license: MIT
metadata:
  hermes:
    related_skills: [rust-standards, euv-ui-standards, euv-engine-renderer-api]
---

# euv framework entry

## Index

Shortest path · Load by task · Workspace shape · What CI runs · Delivery constraints

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
the published version. CI syncs member and dependency versions and then publishes
the workspace members one crate at a time, so a crate added to the workspace is
not installable by version until its own publish step has run, and the members can
land on different versions for a while. Resolve what a consumer can actually
install from the registry, not from `Cargo.toml`: `cargo add euv-chart@<version>`,
or `curl -s https://crates.io/api/v1/crates/euv-chart`.

As of 2026-11-04 all eleven members are published at `0.34.2` and the working
tree is at the same version — not ahead. An unpublished local version is not what
a consumer can install, so re-check the registry rather than trusting this
paragraph when it matters.

## What CI runs

`.github/workflows/rust.yml` defines the jobs; knowing which one covers a change
saves a failed local guess.

- **tests** — `cargo test -p euv-ui` (plus `--no-default-features` and
  `--features theme-custom`), then `cargo test --all-features --workspace`, then
  the performance crate separately. The wasm tests are `wasm-pack test --node`
  run **from the `ui/` directory only** — the engine's wasm-gated suites
  (`engine/tests/webgpu_regressions/`, gated on `#[cfg(target_arch = "wasm32")]`)
  are therefore **not** executed by CI. A WebGPU fix needs a local
  `wasm-pack` run in `engine/` or a real browser check; a green CI run does not
  cover it.
- **clippy** — `cargo clippy --all-features --workspace --all-targets -- -D warnings`.
- **build** — `cargo check --release --all-features --target wasm32-unknown-unknown
  --workspace`, excluding `euv-cli` and `euv-performance`.
- **automation** — a separate job runs `cargo run -p euv-automation` against a
  real Chrome and a matching driver, and a second step asserts that a failing
  probe is **not** reported as success.

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
