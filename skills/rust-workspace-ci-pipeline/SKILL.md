---
name: rust-workspace-ci-pipeline
description: "Use when adding or fixing Rust workspace CI workflows."
version: 1.0.0
author: local
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [rust, github-actions, ci, workspace, crates-io, publish]
    related_skills: [github-actions-deploy-pipelines, crates-cli-usage, rust-workspace-release]
---

# Rust workspace CI pipelines

Adding or repairing the GitHub Actions workflow for a multi-crate Rust workspace.
Existing templates (euv `rust.yml`) are a starting point, not something to paste
unmodified — a copied job graph silently inherits the donor repo's crate names,
branch name, and package layout.

For generic Actions mechanics — triggers, concurrency, artifact races, secret
diagnostics, cross-repo pushes — use `github-actions-deploy-pipelines`. This skill
covers only the Rust/workspace specifics.

## When to Use

- Adding a GitHub Actions workflow to a multi-crate Rust workspace, or copying an
  existing pipeline (`rust.yml`) from another repo of the user's.
- A workspace CI is red, stuck, or silently skipping jobs on pull requests.
- Deciding how a workspace should version-sync, build for wasm32, and publish to
  crates.io.
- Diagnosing a `publish` job that fails on `CARGO_REGISTRY_TOKEN` or `cargo login`.

Not for single-crate projects (drop the sync and wasm32 jobs entirely), and not for
generic Actions mechanics — see `github-actions-deploy-pipelines`.

## 1. Establish the facts before writing a line of YAML

The template cannot be correct until these are known, and each has bitten:

```bash
# Every member's version field — inline or inherited?
for f in core server client example-server example-wasm; do
  printf "%-16s " "$f"; grep -E '^version' $f/Cargo.toml
done
grep -n -A3 '^\[workspace.package\]' Cargo.toml

# Which members are actually publishable?
grep -n "publish" */Cargo.toml        # publish = false is the exclusion marker

# What does the donor template assume that may not exist here?
grep -nE 'docs|euv-cli|--exclude|cd ' <donor>/.github/workflows/rust.yml
```

**Read the version-field shape before copying any version-reading step.** Where
members carry `version.workspace = true`, a donor template's
`grep -E '^version = ' Cargo.toml | head -1` does not read the root `[package]` — it
falls through to the `[workspace.package]` block further down. It returns the right
number today, which is what makes it dangerous: the day a literal `version = "…"`
appears in the root `[package]`, it silently starts answering from the wrong block.
Resolve inheritance for real:

```yaml
VERSION=$(cargo metadata --no-deps --format-version=1 | jq -r '.packages[] | select(.name=="<pkg>") | .version')
```

## 2. Job graph

```
setup → check / tests / clippy / build / audit → publish → release
```

- Every gate job needs
  `if: always() && (github.event_name == 'pull_request' || (github.event_name == 'push' && needs.setup.result == 'success'))`.
  Without `always()`, a `setup` skipped on PR skips everything downstream and CI
  looks green while verifying nothing.
- `publish` and `release` additionally require
  `github.event_name == 'push' && github.ref_name == 'master'`. PR tokens are
  read-only, so a publish job that runs on a PR has no secret to read.
- Add `workflow_dispatch:`. Without it `gh workflow run` returns
  `HTTP 422: Workflow does not have 'workflow_dispatch' trigger`, leaving no way to
  force a re-run short of an empty commit.

`release` must depend on `publish`, not merely run beside it — a GitHub Release for a
version that never landed on crates.io is worse than no release.

## 3. wasm32 and host builds are two different jobs' work

A workspace that ships a browser client and a server cannot build for one target.
Split them rather than excluding members ad hoc inside one command:

```yaml
- name: Build wasm32
  run: cargo build --release --workspace --target wasm32-unknown-unknown \
    --exclude <server-crate> --exclude <example-crate>
- name: Build host
  run: cargo build --release --workspace
```

Excluding a server crate from the wasm build is required, not an optimization:
`tokio`/`hmac` paths do not compile for wasm32. Verify the exclude list against the
member list from §1 — a member marked `publish = false` still has to compile
somewhere, so it belongs in the host build rather than being dropped from both.

## 4. Call the project's own verifier; never inline a rule

The highest-value rule for a repo that ships lint scripts. A hand-rolled check inside
`run:` is a *second, divergent definition* of a rule that already has an
authoritative implementation — and it fails in the dangerous direction.

Observed concretely: an inline lexicographic dependency-order check reported **5
violations** in a workspace where the real checker reported **0** (§13.7 is LOCAL
first, then alphabetic within each group, with a single blank line only at the
local / third-party boundary — not lexicographic). An inline check that flags a
correct repo teaches the team to disable CI, and is worse than no check at all.

```yaml
- name: Verify dependency order
  run: |
    git clone --depth 1 https://github.com/<org>/<skills-repo> /tmp/skills 2>/dev/null || true
    SCRIPT="/tmp/skills/.../verify_dep_order.py"
    if [ ! -f "$SCRIPT" ]; then
      echo "::warning::verifier unavailable, skipping"
      exit 0
    fi
    python3 "$SCRIPT" .
```

Degrade to a no-op when the asset is missing. A missing verifier must not masquerade
as a violation — that trains people to ignore red CI and hides the real signal that
the skill repo lost a file.

## 5. crates.io publish and version sync

The `crate`-CLI shape (`crate sync` → `crate fmt` → `cargo generate-lockfile` →
conditional commit → `git push`) is the established sequence; see `crates-cli-usage`
for CLI semantics and topological publish ordering.

Two things to decide out loud rather than inherit silently:

- **The sync step pushes to the default branch from CI.** That bypasses review by
  design. It is a legitimate choice, but it is a choice — surface it instead of
  letting a copied template make it.
- **The first-release version is effectively permanent.** Once a version is on
  crates.io, changing it means a new version number. Confirm before first publish.

Verify the publish actually surfaced before reporting success:

```bash
for ((i=1; i<=36; i++)); do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "User-Agent: <repo>" "https://crates.io/api/v1/crates/<pkg>/<version>" || echo "000")
  [ "$CODE" = "200" ] && break
  sleep 5
done
```

Always send `-H "User-Agent: ..."` — crates.io rejects the default `curl` UA.

## 6. Verify on a real run, not by reading YAML

YAML that parses proves nothing about the job graph. Push, then watch:

```bash
gh run list --repo <org>/<repo> --limit 3
gh run view <run-id> --repo <org>/<repo> \
  --json jobs --jq '.jobs[] | "\(.name): \(.conclusion // .status)"'
gh run view <run-id> --repo <org>/<repo> --job <failed-job-id> --log-failed
```

Expect a first run to be red, and read the failure rather than guessing. The
missing-`CARGO_REGISTRY_TOKEN` shape renders as an empty `CARGO_REGISTRY_TOKEN:` on
the log's `env:` line followed by `credential provider 'cargo:token' failed action
'login'`. That is a secret-configuration gap, not a workflow bug, and the two get
confused constantly.

## Pitfalls

- **Pasting the donor template's crate names.** `--exclude euv-cli`, `cd docs && cargo fmt`, a `docs-pages/pages` target — each is silent in a repo lacking that member. Grep the template for repo-specific strings and resolve every one against the actual member list.
- **`cargo clippy` without `-D warnings`.** Warnings do not fail the job, so the gate is decorative. Use `cargo clippy --workspace --all-targets --all-features -- -D warnings`.
- **`cargo fmt -- --check` instead of `--all`.** In a multi-crate workspace the non-`--all` form can miss member crates entirely.
- **Verifying locally then pushing.** Run the exact CI commands locally before the first push — `cargo fmt --all -- --check`, clippy with `-D warnings`, `cargo test --workspace --all-features`, and the wasm32 build with the real exclude list. Far cheaper than a red first run.
