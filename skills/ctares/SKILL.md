---
name: ctares
description: "Use when maintaining the ctares 24-crate Rust workspace, crate-cli unified formatter, lombok-macros, or coordinating Tier 1 dependency-ordered releases."
license: MIT
metadata:
  hermes:
    related_skills: [rust-standards, git-standards]
---

# ctares workspace standards and workflow

## Mandatory Standards

1. Load `rust-standards` before editing any `.rs` or `Cargo.toml` file in `ctares`.
2. Respect the 24-crate dependency order declared in root `Cargo.toml` (`[workspace] members`). Never introduce cyclic workspace dependencies.
3. Keep all unified multi-format text formatting logic (`.md`, `.yml`/`.yaml`, `.json`/`.jsonc`, `.toml`, plain text, `#[derive(...)]` sorting, `cargo fmt`) inside `crate-cli/src/fmt/`.
4. Preserve exact VS Code Prettier 3.7.4 parity in `crate-cli`: `tabWidth: 2`, `singleQuote: true`, `semi: true`, `endOfLine: "lf"`, `printWidth: 80`, `proseWrap: "preserve"`, `bracketSpacing: true`.
5. Keep all public APIs backward-compatible within the same major version; export library entry points (`execute_unified_fmt`, `format_workspace_text_files`, `format_text_by_path`) cleanly for downstream CLIs (`euv-cli`, `hyperlane-cli`).
6. Keep all code, comments, commit messages, PR descriptions, docs, and skills strictly English-only.

## Verification Workflow

Run every gate locally before committing or pushing:

```sh
cargo run -p crate-cli -- fmt
cargo run -p crate-cli -- fmt --check
cargo fmt --all -- --check
cargo clippy --workspace --all-features --all-targets -- -D warnings
cargo test --workspace --all-features
cargo check --release --workspace --all-features
python3 ~/.agents/skills/rust-standards/scripts/staged_file_gate.py .
python3 ~/.agents/skills/rust-standards/scripts/verify_dep_order.py .
```

When changing `crate-cli/src/fmt/`, also verify differential parity against the installed VS Code Prettier bundle across representative `.md` and `.yml`/`.yaml` files and add regression tests in `crate-cli/tests/fmt/`.

## Release & Downstream Cascade Workflow

`ctares` is **Tier 1** in the ecosystem dependency graph:

1. Bump `[workspace.package].version` and internal `[workspace.dependencies]` pins in root `Cargo.toml`.
2. Verify all local gates pass and `.github/workflows/*.yml` are formatted with `crate fmt` so CI's `publish` step never attempts to push workflow edits via `GITHUB_TOKEN`.
3. Validate commit/PR text with `~/.agents/skills/git-standards/scripts/verify_english_only.py`.
4. Merge/push to `master` and wait until `.github/workflows/rust.yml` (`setup`, `check`, `tests`, `clippy`, `build`, `publish`, `release`) finishes green and the new version is live on `crates.io`.
5. Cascade upgrades in strict order:
   - Tier 2: `euv` (`crate-cli`, `lombok-macros`) and `hyperlane` (`crate-cli`, `color-output`, `lombok-macros`, `tokio-broadcast`).
   - Tier 3: `hyperlane-quick-start` and `commerce-suite`.
   - Tier 4: `web-frameworks`.

## Documentation & Skill Governance

- Update root `README.md`, `<crate>/README.md`, and `AGENTS.md` in the same commit whenever adding/removing crates, changing `crate-cli` commands/flags, altering public APIs, or updating CI gates.
- Keep `.agents/skills/ctares/SKILL.md` and `~/.agents/skills/ctares/SKILL.md` identical and strictly limited to standards, requirements, and workflows (`<= 160` lines).
- After updating any skill, run `python3 ~/.agents/scripts/audit_skills.py` and `python3 ~/.agents/scripts/update_skill_lock.py`.
