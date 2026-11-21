# ctares workspace facts (verified )

Reference for the `ctares` Rust workspace, which is the reference repository this
skill is calibrated against. Every number below was read out of the live repo at
`~/code/ctares` on the live checkout; re-verify with the commands given when
a claim matters.

## Shape

| Fact | Value | How to re-check |
|---|---|---|
| Workspace members | 24 packages | `cargo metadata --no-deps --format-version 1` |
| Root manifest | virtual workspace — **no `[package]`** at the root | `grep -c '^\[package\]' Cargo.toml` → `0` |
| `[workspace.package].version` | `10.5.0` (snapshot; bumped often — re-read, don't hard-code) | `grep -A4 '^\[workspace.package\]' Cargo.toml` |
| `edition` | `2024` | same |
| `resolver` | `"2"` | `grep -n resolver Cargo.toml` |
| `Cargo.lock` | **not committed** (`.gitignore` has `/Cargo.lock`) | `git ls-files Cargo.lock` → empty |
| `rustfmt.toml` | none in the repo | `find . -name rustfmt.toml` |
| `rust-standards.toml` | **absent** — the file and the `pub_const_exempt` field it held were deleted together with the const-visibility rule; no repository carries a rust-standards configuration file any more | `ls rust-standards.toml` |
| `crate-cli/tmp/` | 26 generated scratch crates, git-ignored | `ls crate-cli/tmp \| wc -l` |

Member list `bin-encode-decode`, `chinese-identification-card`,
`chunkify`, `clonelicious`, `color-log`, `color-output`, `compare_version`,
`crate-cli`, `future-fn`, `instrument-level`, `jwt-service`, `lombok-macros`,
`recoverable-spawn`, `recoverable-thread-pool`, `std-macro-extensions`,
`stripe-pay-client`, `stripe-pay-core`, `stripe-pay-server`, `system-time`,
`tcp-request`, `tcplane`, `tokio-broadcast`, `udp`, `udp-request`.

The tree was slimmed to these 24 on (`chore(ctares): slim the family
down to 24 crates`). `server-manager`, `file-operation` and `hot-restart` left
the workspace, and `china_identification_card` was renamed to
`chinese-identification-card`. **The published crates are not gone** — the
first three stay on crates.io at `10.3.0`, and so does the old
`china_identification_card` name; the renamed `chinese-identification-card`
crate **is** published now, at `10.5.0`. So a consumer can still depend on
`server-manager = "10.3.0"` from the registry while the workspace no longer
builds it. Verify with
`curl -s -H 'User-Agent: skill-sync-audit/1.0' https://crates.io/api/v1/crates/<name> | python3 -c 'import json,sys;print(json.load(sys.stdin)["crate"]["max_stable_version"])'`.
The `User-Agent` is required: without it the registry answers **403** and the
command prints nothing instead of the version.

Note the `ctares` **root is a virtual workspace**, so `cargo fmt` at the root
reaches every member (see the `crate fmt` scope note in SKILL.md §13).

## Audit baseline

The audit grew from 54 to **56 checks** (the macro-body namespace rule and the
qualified-type-path rule joined it). The current result on `origin/master`
(`1fc04d9`) is:

```
python3 ~/.agents/skills/rust-standards/scripts/audit_rust_standards.py ~/code/ctares
→ === SUMMARY: 53/56 PASS ===
```

**Three checks fail on this repository right now**, and they are not stale
baselines:

| Check | Hits | Where |
|---|---|---|
| 54 — macro body must spell full namespace paths, no `use` (§16.5) | 19 | `lombok-macros/src/generate/fn.rs` — the `quote!` bodies write `std::fmt::Display` / `std::fmt::Formatter` / `std::fmt::Result` / `std::clone` without the leading `::`, so they resolve in the **consumer's** scope |
| 55 — qualified type path in a type annotation (§6.7) | 5 | `crate-cli/src/bump/fn.rs` (`&toml_edit::Array` in a closure annotation, twice), `lombok-macros/src/generate/fn.rs` (`proc_macro2::LexError`), `lombok-macros/src/parse/fn.rs` (`proc_macro2::TokenTree`), `udp/tests/server/fn.rs` (`tokio::net::UdpSocket`) |
| 56 — public field of a public struct (§17.18) | 122 | `color-log/src/struct.rs` (`FileLogger` and its siblings) and others — a `pub` field on a `pub` struct freezes the layout into the published API |

Check 56 is the same rule the `hyperlane` workspace just applied to itself
(105 fields across 23 files narrowed to `pub(crate)`, accessors left public).
The fix is identical: narrow the field, keep the accessor public.

Checks 54 and 55 are also the rules `hyperlane` applied in the same window, so
`ctares` is the repository that has not caught up. Do not treat the failing
audit as a broken audit — run it, read the hits, and fix the source.

The **older** hit counts recorded in SKILL.md for this repo (allow-lints 4,
keyword-file-purity 16, lombok accessor contract 99, pub-group order 7-in-2,
no-pub-in-tests 6) are 2026-09/10 baselines that have since been cleared — do
not expect them to reproduce. Two specific file:line citations from those
baselines (`udp/src/attribute/type.rs:13`,
`tcplane/src/handler/trait.rs:58`) were fixed upstream and no longer exist.

## Version bumping and dependency sync

Two different mechanisms, and the split matters:

- **`crate bump`** writes the root `[workspace.package].version` — a human
  decision, always made in a commit, never in CI.
- **`crate sync`** rewrites the `version = "..."` requirement inside each
  `[workspace.dependencies]` path-dependency entry so it matches the root
  version. It does **not** choose a version. As of `crate-cli` 10.5.0 it also
  **renames the dependency alias** when the alias does not match the member's
  `[package].name`, so a sync can change the *name* a member is depended on by,
  not only its version requirement. Read the diff after a sync.

The `publish` job in `.github/workflows/rust.yml` runs `crate sync` then
`crate fmt`, and commits the result as `chore: sync workspace member deps and
apply crate fmt`. That is why the root version and the path-dependency versions
can look out of sync in a fresh clone — CI reconciles them on the next publish.
This is the concrete case behind SKILL.md §13.7's "root version is the single
source of truth" rule.

`verify_ci_no_bump.py` passes on this repo: `crate sync` is not a bump command,
and the workflow never redirects into `Cargo.toml` directly.

## CI workflow

`.github/workflows/rust.yml` — jobs `setup`, `check`, `tests`, `clippy`,
`build`, `publish`, `release`. Two details worth knowing:

- `check` runs `cargo fmt --all -- --check`, i.e. plain rustfmt over the whole
  workspace. It does **not** use `crate fmt --check`, so it does not enforce
  derive ordering (see the `crate fmt` scope note in SKILL.md §13).
- The top-level `name:` and `on:` blocks are separated by a blank line
  (changed , `style(ci): separate workflow name from trigger block`).

## `crate fmt` behaviour (verified against crate-cli 10.5.0 source)

The `crate-cli` crate in this workspace is the implementation of the `crate fmt`
command the skill tells you to run. Its real behaviour differs from the old
skill text in three ways that were re-verified on :

1. **Scope is the cwd package, not the workspace.** `crate fmt` spawns plain
   `cargo fmt` (`crate-cli/src/fmt/fn.rs`, `execute_fmt`:
   `Command::new(CARGO).arg(CARGO_FMT)`) — `--all` is never passed. At the
   workspace root cargo's workspace resolution reaches every member; from a
   member subdirectory only that member is formatted. **Run it from the
   workspace root.**
2. **It sorts `#[derive(...)]` traits, plain `cargo fmt` does not.** Before
   `cargo fmt`, crate-cli runs `format_derive_attributes` →
   `sort_derive_in_line`, sorting trait names by lowercase alphabetical order.
   `#[derive(Setter, Getter, Clone)]` becomes `#[derive(Clone, Getter,
   Setter)]`. Only `src/` trees are scanned (`find_rust_files`); `tests/`
   directories are left alone.
3. **`cargo clippy --fix` runs after `cargo fmt`, not before**
   (`execute_clippy_fix`: `cargo clippy --fix --workspace --all-targets
   --allow-dirty`). Clippy therefore sees the already-formatted code. A failing
   clippy fix makes `crate fmt` exit 1, so "crate fmt failed" can mean a
   compile error rather than a formatting problem.

`crate fmt --check` only spawns `cargo fmt --check` — it does **not** check
derive ordering, so exit 0 does not mean the derive order is compliant.

## The wasm client is no longer a wasm crate

`stripe-pay-client` used to be the workspace's WebAssembly entry point: it
depended on `wasm-bindgen`, `wasm-bindgen-futures`, `wasm-bindgen-serde` and
`js-sys`, and its manifest carried the `wasm` category. As of `10.4.0` those
dependencies are gone and the crate builds as a plain `rlib` — there is no
`[lib] crate-type = ["cdylib", ...]` anywhere in the workspace, so
`verify_no_wasm_inline.py` reports "rule not applicable" here.

The crate still exists and still carries the browser-side Stripe types
(`element`, `host`, `mount`), but it is now a normal library crate. Do not
assume a wasm build target for it, and do not add `wasm-bindgen` back without
a reason that the audit can check.

## Lombok

`lombok-macros` is a workspace member here and is the crate that implements the
`Getter` / `GetterMut` / `Setter` / `New` / `Data` derives described in
[17-lombok-derives.md](17-lombok-derives.md). The re-check against
the in-tree 10.4.0 source confirmed every signature claim in that file still
holds: `Data` is still the trio (all four derives call `inner_lombok_data` with
differing bools), `type(copy)` still yields the field type rather than `&T`
(`generate_return_type` maps `ReturnType::Clone | ReturnType::Copy` to the
normalized field type), `skip` flags are still merged across attributes before
generation, and `Visibility` still defaults to `Public`.

The member is now a **path dependency on the in-tree source**, not a registry
release: the root manifest pins `lombok-macros = { path = "lombok-macros",
version = "10.5.0" }`. The published `lombok-macros` on crates.io is also at
`10.5.0`, so the two agree today — but a claim about "the version ctares uses"
must name the path dependency, because that is what the build actually
resolves.
