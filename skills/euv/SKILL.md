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

Shortest path · Load by task · Delivery constraints

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

`cargo metadata` is authoritative for membership and paths; the workspace currently
holds nine packages: `euv` (root), `euv-core`, `euv-macros`, `euv-ui`, `euv-engine`,
`euv-cli`, `euv-docs`, `euv-example`, and `euv-chart`.

`euv-chart` is the newest crate: an ECharts-compatible option model, a display
list built from it, and three interchangeable backends (WebGPU, WebGL2, Canvas2D)
behind one API. It depends on `euv-core` for `Signal` and on `euv-engine` for
`Tween`/`Easing`; it does **not** re-export through the `euv` root crate, so
`use euv::*` does not reach chart types. Read
[references/api-chart.md](references/api-chart.md) before using it.

Two facts about the chart crate that source reading will not tell you:

- **Check the registry before pinning a version.** The repository's version is
  not the published version. CI syncs member and dependency versions and then
  publishes the workspace members one crate at a time, so a crate added to the
  workspace is not installable by version until its own publish step has run,
  and the members can land on different versions for a while. Resolve what a
  consumer can actually install from the registry, not from `Cargo.toml`:
  `cargo add euv-chart@<version>`, or
  `curl -s https://crates.io/api/v1/crates/euv-chart`.
- **`euv-chart` is published and builds from the registry.** As of
  2026-10-25 it is on crates.io at `0.32.6` alongside the rest of the
  workspace, and `cargo add euv-chart` + `cargo build` resolves and compiles
  against the published `euv`, `euv-core` and `euv-engine`. If a consumer
  cannot find it, their lockfile or index is stale — not the crate. The
  working tree is one patch ahead (`0.32.7`), which is **not** on crates.io
  yet: an unpublished local version is not what a consumer can install.

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
