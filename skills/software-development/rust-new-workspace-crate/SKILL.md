---
name: rust-new-workspace-crate
description: "Use when creating or extracting a workspace crate."
version: 0.1.0
author: Hermes Agent (curator)
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [rust, cargo, workspace, crate, scaffold, extraction]
    category: software-development
    related: [rust-workspace-subpackage-onboarding, rust-standards]
---

# Create a new crate in a Cargo workspace (incl. extraction from an existing crate)

## When to Use

- The user asks to 新建子包 / add a new member to a Cargo workspace.
- The user asks to 抽离 (extract) commands/modules from an existing crate into a new standalone crate — possibly in a different repo's workspace.

Covers crates.io name pre-check, manifest conventions, extraction trim order, test porting, and commit hygiene. For onboarding an EXISTING upstream crate as a subpackage, use `rust-workspace-subpackage-onboarding` instead.

## Procedure

1. **Verify the crate name is free on crates.io BEFORE writing anything, when the crate may ever be published.** crates.io names are permanent once published. Query each candidate with a browser UA (bare curl gets 403):
   ```bash
   UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15'
   curl -s -o /dev/null -w "%{http_code}" -A "$UA" "https://crates.io/api/v1/crates/NAME"
   # 404 = available, 200 = taken
   ```
   Check a batch of candidates in one loop, present the available ones, let the user pick (or proceed with the recommended one if they don't answer). Sleep ~1s between API calls.

2. **Read the target workspace's conventions first** (`root Cargo.toml` + one existing member's `Cargo.toml`):
   - Member layout: top-level (`core/`) vs nested (`crates/<name>/`) — follow the existing `members` array exactly; don't introduce the other layout.
   - `[workspace.package].edition`: if it's `2021` but the code uses let-chains (`if let ... && let ...`), the new crate MUST set `edition = "2024"` literally in its own manifest — let-chains are edition-gated, and workspace inheritance would silently break the build.
   - If the workspace has NO `[workspace.dependencies]` table, write explicit crates.io versions in the new member's own `[dependencies]`; don't invent a workspace table the repo doesn't use.

3. **For extraction: copy module dirs, then write the new crate's own files.** `cp -r src/<mod1> src/<mod2> <newcrate>/src/` for the modules that move as-is, then write fresh `Cargo.toml`, `src/lib.rs`, `src/main.rs`, and any module that needs trimming (config/command/help).
   - Pitfall: `write_file` REFUSES to overwrite files that were created by `cp` and never read at their new path (stale-write guard). Either `rm` the copied file before `write_file`, or `patch` it in place. `rm`-then-write is faster for full rewrites.

4. **Trim centralized imports with a usage map, never by guessing.** This user's crates centralize imports as `pub(crate) use` in `lib.rs`. Before removing entries, grep every import token across ONLY the modules that remain:
   ```bash
   for tok in "Value" "Regex" "which" "Stdio" "Command" "create_dir_all" "read_to_string"; do
     echo "== $tok"; grep -l "$tok" src/remaining1/*.rs src/remaining2/*.rs
   done
   ```
   An entry with zero remaining users comes out; anything else stays. Missing one produces an E0425 cascade ("cannot find type `Path`") on first compile.

5. **Grep for cross-module references BEFORE deleting a module in the source crate.** `grep -rn "crate::<module>\|<module>::" src/` finds survivors — e.g. a `format_path` helper in the `fmt` module called by `template`. Inline such helpers as private fns in the caller's module; don't delete the module and discover the breakage at compile time, and don't keep a whole extracted module alive for one helper.

6. **Port the tests, and immediately gitignore fixture residue.** Ported tests that write fixtures to `./tmp/` (relative to the crate dir) leave residue inside the NEW crate. Add a `.gitignore` with `/tmp/` to the new crate up front, and check `git status --short` for `tmp/` or fixture dirs before `git add crates/<name>` — a blanket add sweeps residue into the commit. If it lands anyway: `git rm -r` the residue, add the gitignore, `commit --amend --no-edit`.

7. **Verify the new crate in isolation:**
   ```bash
   cargo test -p <name>
   cargo fmt -p <name> -- --check
   cargo clippy -p <name> --all-targets   # zero warnings
   cargo run -p <name> -- --help          # binary smoke test
   cargo run -p <name> -- --version
   ```
   For clippy, filter output to the new crate's paths — a monorepo may emit pre-existing warnings for other members (e.g. "profiles for the non root package will be ignored"), which are not yours to fix in this task.

8. **Source-crate removal (extraction only), in this order:** `git rm -r` the moved modules (src + tests) → trim `lib.rs` mod list + imports (step 4) → remove dispatch arms in `main.rs` → remove enum variants → remove `Args` fields + their parse arms → rewrite help text → remove the member's now-unused deps from its `Cargo.toml` → grep each ROOT `[workspace.dependencies]` entry across `*/Cargo.toml` and delete entries no member references anymore → `cargo test -p <source-cli>` + fmt + clippy + whole-workspace `cargo check`.

9. **Rewire consumers and respect push order.** If another repo's CI calls the extracted commands, switch it to `cargo install --git https://github.com/ORG/MONOREPO.git <crate>` (installs a named crate from a monorepo's default branch; omit `--locked` when the monorepo doesn't commit `Cargo.lock`) followed by bare `<crate> <cmd>` invocations. The tool's repo MUST be pushed before the consumer repo — the consumer's CI installs from the remote master, so pushing the consumer first breaks its own pipeline. Report the required push order explicitly.

## Pitfalls

- **`cargo test -p <pkg>` still resolves the ENTIRE workspace.** One unrelated member whose dep metadata isn't fetchable (network/offline) fails the whole command with `failed to get `X` as a dependency of package `Y``. This is a resolution-phase failure, not a problem in `<pkg>` — fix index access (see `rust-cargo-mirror-setup`) rather than debugging the new crate.
- **Don't commit a project-local cargo mirror config.** When a regional mirror is needed to build (`.cargo/config.toml` with `source.crates-io replace-with`), keep it untracked in a public repo — committing it forces that mirror on every consumer and CI runner.
- **Match the user repo's existing commit/test conventions instead of inventing new ones.** Copy the module layout (`mod.rs` + `r#fn.rs` style), the tests/mod.rs prelude pattern, and the `[package]` field order from an existing member; the user reviews diffs against house style.
- **Help text and defaults drift during extraction.** When trimming options, re-check actual defaults in the parse code (e.g. a retry default of 8 documented as 3) — extraction is the right moment to fix stale help text, not copy it.
- **Version-field expectations differ per workspace.** Some workspaces use `version.workspace = true`; others expect a literal `version = "0.1.0"` per crate. Follow the target workspace's existing members, not the source project's.
