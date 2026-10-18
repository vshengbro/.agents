---
name: euv
description: "Use when implementing or debugging an euv reactive Rust UI: components, signals, macros, mounting and routing. Renderer backends use euv-engine-renderer-api; euv design tokens use euv-ui-standards."
license: MIT
metadata:
  hermes:
    related_skills: [rust-standards, euv-ui-standards, euv-engine-renderer-api]
---

# euv framework entry

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
| WebGPU/WebGL renderer contracts and readback | [Renderer workflow](euv-engine-renderer-api/SKILL.md) |
| euv UI layout, class registry and visual verification | [UI standards](../euv-ui-standards/SKILL.md) |
| Symptom-first diagnosis | [Pitfalls](references/pitfalls.md) |

Reference pages are cached documentation, **not authority over the selected source
or compiler**. Verify uncertain signatures and source paths before use; generated
lombok accessors may not appear in `.rs` text. Load a single topical tutorial from
`references/` when the signature alone is insufficient.

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
