# ctares workspace facts (verified 2026-10-23)

Reference for the `ctares` Rust workspace, which is the reference repository this
skill is calibrated against. Every number below was read out of the live repo at
`/Users/sqs/code/ctares` on 2026-10-23; re-verify with the commands given when a
claim matters.

## Shape

| Fact | Value | How to re-check |
|---|---|---|
| Workspace members | 27 packages | `cargo metadata --no-deps --format-version 1` |
| Root manifest | virtual workspace — **no `[package]`** at the root | `grep -c '^\[package\]' Cargo.toml` → `0` |
| `[workspace.package].version` | `10.2.11` (snapshot; bumped often — re-read, don't hard-code) | `grep -A4 '^\[workspace.package\]' Cargo.toml` |
| `edition` | `2024` | same |
| `resolver` | `"2"` | `grep -n resolver Cargo.toml` |
| `Cargo.lock` | **not committed** (`.gitignore` has `/Cargo.lock`) | `git ls-files Cargo.lock` → empty |
| `rustfmt.toml` | none in the repo | `find . -name rustfmt.toml` |
| `rust-standards.toml` | present at the root | `cat rust-standards.toml` |
| `crate-cli/tmp/` | 26 generated scratch crates, git-ignored | `ls crate-cli/tmp \| wc -l` |

Member list (2026-10-23): `bin-encode-decode`, `china_identification_card`,
`clonelicious`, `chunkify`, `color-log`, `color-output`, `compare_version`,
`crate-cli`, `file-operation`, `future-fn`, `hot-restart`, `instrument-level`,
`jwt-service`, `lombok-macros`, `recoverable-spawn`, `recoverable-thread-pool`,
`server-manager`, `std-macro-extensions`, `stripe-pay-client`,
`stripe-pay-core`, `stripe-pay-server`, `system-time`, `tcplane`, `tokio-broadcast`,
`udp`, `udp-request`.

Note the `ctares` **root is a virtual workspace**, so `cargo fmt` at the root
reaches every member (see the `crate fmt` scope note in SKILL.md §13).

## Audit baseline

`ctares` passes the full audit:

```
python3 ~/.agents/skills/rust-standards/scripts/audit_rust_standards.py /Users/sqs/code/ctares
→ === SUMMARY: 54/54 PASS ===
```

Re-measured 2026-10-23. The older hit counts recorded in SKILL.md for this repo
(allow-lints 4, keyword-file-purity 16, lombok accessor contract 99, pub-group
order 7-in-2, no-pub-in-tests 6) are **2026-09/10 baselines that have since been
cleared** — do not expect them to reproduce. Two specific file:line citations
from those baselines (`udp/src/attribute/type.rs:13`,
`tcplane/src/handler/trait.rs:58`) were fixed upstream and no longer exist.

## Version bumping and dependency sync

Two different mechanisms, and the split matters:

- **`crate bump`** writes the root `[workspace.package].version` — a human
  decision, always made in a commit, never in CI.
- **`crate sync`** rewrites the `version = "..."` requirement inside each
  `[workspace.dependencies]` path-dependency entry so it matches the root
  version. It does **not** choose a version.

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
  (changed 2026-10-23, `style(ci): separate workflow name from trigger block`).

## `crate fmt` behaviour (verified against crate-cli 10.2.9 source)

The `crate-cli` crate in this workspace is the implementation of the `crate fmt`
command the skill tells you to run. Its real behaviour differs from the old
skill text in three ways that were re-verified on 2026-10-23:

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

## Lombok

`lombok-macros` is a workspace member here and is the crate that implements the
`Getter` / `GetterMut` / `Setter` / `New` / `Data` derives described in
[17-lombok-derives.md](17-lombok-derives.md). The 2026-10-23 re-check against
the 10.2.9 source confirmed every signature claim in that file still holds:
`Data` is still the trio (all four derives call `inner_lombok_data` with
differing bools), `type(copy)` still yields the field type rather than `&T`,
`skip` flags are still merged across attributes before generation, and
`Visibility` still defaults to `Public`.
