---
name: euv-docs-sidebar-and-layout-fixes
description: Use when fixing an euv-docs sidebar or layout defect.
license: MIT
metadata:
  version: "1.0.0"
  category: frontend-dev
  related_skills:
    - frontend-dev/euv-docs-contribution
    - rust-standards
    - devops/static-site-deploy-verification
---

# euv-docs sidebar + page layout fixes

Two defect classes that recur in the euv-docs shell, plus the traps that make
them expensive to diagnose. Both fixes belong in the framework tree
(`ui/src/style/class/display/fn.rs`, `ui/src/component/sidebar/view/fn.rs`),
not in site-local CSS — the upstream classes are the source of truth.

## Trap: an opaque compiler crash is a `mod.rs` mistake, not your algorithm

Writing `pub use hook::*;` without a matching `mod hook;` makes **rustc 1.98
crash with `SIGBUS: access to undefined memory`** — no `E0412`, no span, no
file name. The signal points at whatever code sits nearby (a recursive helper,
say), so the instinct is to rewrite the algorithm. That wastes the whole
diagnosis.

Method: the clean tree compiles and your one-file edit SIGBUSes. That
combination is the signature. Bisect by reverting **one file at a time** until
it builds — do not reason about the algorithm. Also test whether the crash
survives `RUSTFLAGS="-C codegen-units=1"`: it does, because the malformed
`use` is a front-end error, not a codegen one.

Related: `rust-standards` §1.4 restricts filenames to keyword names, so the
natural `hook.rs` is rejected by audit rule 26 anyway. Put pure helpers in
`fn.rs`. Run `audit_rust_standards.py` **before** the first compile — it
reports the naming rule as a readable message that the missing `mod`
declaration would otherwise hide.

## Footer pinned to the bottom of a scroll area

**Symptom:** on a short page the footer sits directly under the content
instead of at the bottom of the visible column, so it appears to float
mid-screen.

**Cause:** a width-constrained wrapper (`c_page_container`) is a plain block —
the footer has no second flex child to be distributed against.

**Fix:** reuse the doc layout's proven shape, which already exists upstream and
whose comments explain the constraints:

- an outer row filling the scroll area — `min-height: 100%`, **not** `100vh`,
  because the scroll container (`c_app_main`) excludes the app header, so a
  viewport unit overshoots by the header height and pushes the footer one
  header past the fold;
- a content column with `justify-content: space-between`;
- **real** body and tail wrapper elements. A `display: contents` wrapper is
  hoisted out of the flex column, so space-between distributes the slack
  between the title and the first paragraph — the exact blank-band bug the
  wrapper exists to prevent.

`flex-shrink: 0` on the outer row is mandatory: as a flex item of the scroll
column it is otherwise clamped to the `min-height` floor regardless of its
content, which also breaks sticky descendants.

**Verify both directions.** Short page: `footer.bottom == main.bottom` and
`scrollHeight <= clientHeight`. Tall page: content still scrolls and the footer
follows in normal flow (`scrollHeight > clientHeight`, footer bottom well past
the viewport). A fix that only measures the short page has not been verified.

## A sidebar group with `link: None` is not a destination

**Symptom:** clicking a pure directory (`essay/2025`) only toggles the
collapse arrow, and the article column renders empty — the group has no index
page, so the router resolves the route to nothing.

**Fix:** resolve a linkless group to its first readable page — depth-first in
sidebar order, preferring a group's own index over its children, recursing so
nested empty directories are walked until something readable is found. Put the
search in a pure function (`fn.rs`) and unit-test it against a static tree;
keep the click handler thin.

Keep these cases on their existing behaviour:

- a group **with** an index keeps the current rule — navigate when the index is
  inactive, fold only when already on it (folding on navigation is a surprising
  side effect);
- a subtree with nothing readable falls back to folding, rather than navigating
  somewhere arbitrary.

**Verify in the browser, not just in unit tests.** Units prove the resolution
rule; the browser proves the click path. Click the group, assert
`location.hash` changed to a real route, that the article element has
non-zero text, and that the active sidebar row highlights.

## Deploy: the live URL is not the repo name

`https://<owner>.github.io/<repo>/` is a guess and routinely serves a stub
(`#app` never mounts, so every DOM probe returns `null` and reads as
"deploy failed"). Resolve the real URL first:
`gh api repos/<org>/<pages-repo> --jq .homepage`. The Pages repo is usually
distinct from the source repo, so the path carries the **pages** repo name.

When the deploy workflow installs the engine from git at build time
(`cargo install --git ... --branch master euv-docs`), a triggered rebuild
picks up engine fixes with no version bump — confirm that by reading the
workflow file before assuming a redeploy is required.

Verify the deployed behaviour with the same assertions used locally (footer
geometry, click-through navigation), not just a 200. See
`devops/static-site-deploy-verification` for the artifact→URL→fresh-context
chain.