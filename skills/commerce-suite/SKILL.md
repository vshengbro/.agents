---
name: commerce-suite
description: "Use when maintaining commerce-suite: Hyperlane backend workspace, legacy euv frontend isolation, page-artifact security contracts, self-hosted CI releases, and doc governance."
license: MIT
metadata:
  hermes:
    related_skills: [rust-standards, hyperlane, git-standards]
---

# commerce-suite standards and workflow

## Mandatory Standards

1. Load `rust-standards` and `hyperlane` before modifying backend Rust or Cargo files.
2. Respect the strict backend-vs-frontend workspace boundary:
   - Root Cargo workspace manages backend members ONLY: `resources`, `config`, `plugin`, `application`, `bootstrap`.
   - `frontend/` is explicitly excluded from the root Cargo workspace and pins its legacy WebAssembly `euv` dependency; NEVER upgrade `frontend/`'s `euv` version during backend dependency cascades unless explicitly executing a dedicated frontend migration.
3. Enforce backend layer separation:
   - `config/` (`hyperlane_config`): typed configuration schemas only.
   - `resources/` (`hyperlane_resources`): env templates (`resources/env/*/server.env.example`), SQL, Nginx, legal, and navigation assets; never commit real secrets (`server.env`).
   - `plugin/` (`hyperlane_plugin`): infrastructure adapters (`mysql`, `postgresql`, `redis`, `credential_isolation`, `message_queue`, `file_logger`, `shutdown`).
   - `application/` (`hyperlane_application`): domain, services, repositories, controllers, middleware, views, OpenAPI, and upload/page-artifact handlers.
   - `bootstrap/` (`hyperlane_bootstrap`): runtime wiring and startup orchestration.
4. Preserve security invariants:
   - `PAGE_ARTIFACT_API_KEY` uploads must fail closed when unset and accept keys only via header/environment, never URL/CLI args.
   - Preserve Stripe webhook signature verification, OAuth/JWT secret guards, and credential isolation.
5. Keep all code, comments, commit messages, docs, and skills strictly English-only.

## Verification Workflow

Run every gate locally before committing or pushing:

```sh
crate fmt
crate fmt --check
cargo fmt --all -- --check
cargo clippy --workspace --all-features --all-targets -- -D warnings
cargo test --workspace --all-features
cargo check --release --workspace --all-features
python3 ~/.agents/skills/rust-standards/scripts/staged_file_gate.py .
python3 ~/.agents/skills/rust-standards/scripts/verify_dep_order.py .
```

Do not disturb unrelated feature worktrees or branches (e.g., use a clean `git worktree` off `master` when releasing while another branch is checked out).

## Dependency & Release Workflow

`commerce-suite` is **Tier 3** (depends on published `ctares` and `hyperlane`):

1. Wait until upstream `ctares` and `hyperlane*` versions are live on `crates.io`.
2. Upgrade backend `ctares` crates (`chunkify`, `color-output`, `lombok-macros`, `instrument-level`, `bin-encode-decode`) and `hyperlane*` crates (`hyperlane`, `hyperlane-core`, `hyperlane-macros`, `hyperlane-plugin-*`) in root `Cargo.toml` while preserving `verify_dep_order.py` order.
3. Bump `[package].version` and internal member pins, run all local verification gates (including contract tests under `tests/`), validate commit text via `verify_english_only.py`, push to `master`, and wait until `.github/workflows/rust.yml` finishes green.

## Documentation & Skill Governance

- Update root `README.md`, `<member>/README.md`, and `AGENTS.md` whenever changing workspace members, configuration env keys, security contracts, page-artifact APIs, or release steps.
- Keep `.agents/skills/commerce-suite/SKILL.md` and `~/.agents/skills/commerce-suite/SKILL.md` synchronized and strictly limited to standards, requirements, and workflows (`<= 160` lines).
- After updating any skill, run `python3 ~/.agents/scripts/audit_skills.py` and `python3 ~/.agents/scripts/update_skill_lock.py`.
