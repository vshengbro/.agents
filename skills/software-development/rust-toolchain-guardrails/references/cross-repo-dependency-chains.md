# Cross-repo dependency upgrade chains

The user runs dependency upgrades across several sibling workspaces in one
sitting, in dependency order: bottom library first, then its consumer, with a
CI wait between each. The standing instruction is **"follow my order exactly"**
— do not reorder it, and do not silently skip a step because it looks
redundant. Report a step as a no-op *with the evidence* and continue.

## The shape

```
ctares  ->  hyperlane  ->  euv
(libs)     (libs)       (consumer, has a PR)
```

Each step: bump deps → `cargo check` → `cargo test` → commit → push → **wait for
CI green** → next step. Publishing is a separate explicit step, not implied by
bumping.

## Step 0, before any bump: does the next step even exist?

The chain is frequently already satisfied. **Both** the local manifest and the
registry reflect the truth, and a step with nothing to do is the normal case,
not an error:

```bash
git -C ~/code/<repo> rev-parse --abbrev-ref HEAD
git -C ~/code/<repo> status --porcelain | wc -l          # want 0
grep -m1 '^version' ~/code/<repo>/Cargo.toml
curl -s -H 'User-Agent: a' https://crates.io/api/v1/crates/<crate> \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['crate']['max_stable_version'])"
```

If the local version already equals the registry's `max_stable_version` and the
worktree is clean, that step is done — say so, and move to the next. Do not
invent a version bump to have something to do.

## Per-repo: find the actually-used deps first

See `rust-toolchain-guardrails` §1 for the reverse-lookup script. The compact
version of the lesson: **`[workspace.dependencies]` lists intent, not usage.**
A repo can carry a dozen stale declarations that no member crate references.
Bumping those is a no-op that reads as validation.

## Classify before choosing

Query every candidate against crates.io and split the result:

| Kind | Example shape | Action |
|---|---|---|
| patch/minor, actually used | `x 0.3.33 -> 0.3.34` | take it |
| cross-major, actually used | `x 1.1 -> 2.0` | take it and fix the fallout |
| cross-major, **not used** | orphan declaration | revert; it proves nothing |

When the user says "cross-major is fine, just fix the errors", they mean *for
the code that actually compiles*. A cross-major bump on an unused crate
produces no errors to fix, and reporting "no errors, upgraded cleanly" is a
false green — say explicitly which bumps were inert.

## Bump in the real declaration shape

Two forms, and a naive `name = "ver"` regex silently misses the second:

```toml
futures = "0.3.33"                                              # plain
tokio-rustls = { version = "0.26.5", default-features = false,  # table
                 features = ["ring", "tls12"] }
```

Anchor on the name and replace the quoted version *in place*, preserving
features. Verify the replacement count — a `MISS` here means a dependency
silently stayed old, which reads as success.

## Reject semver metadata

A registry `max_stable_version` can carry build metadata
(`0.25.15+spec-1.1.0`). Pasting it into a requirement produces
`semver metadata which will be ignored, removing the metadata is recommended`
and gains nothing — the version without the suffix is identical. Drop it and
keep `0.25.15`.

## Reverting a mistake early

`cargo update` can rewrite more than intended. `Cargo.toml` is cheap to restore
because it is one tracked file:

```bash
cp /tmp/<repo>_Cargo.toml.bak Cargo.toml     # take the backup FIRST
cargo update                                 # then resolve
```

Take the backup before the first edit on any cross-major step. `Cargo.lock` in
a library repo is usually gitignored, so there is often nothing to restore on
that side.

## Before the final push step

The consumer repo usually has an open PR. See `rust-ship-verification` §3a-1
(check whether the branch is already published) and §3a-2 (prove the checkout
still compiles without the dirty worktree). A dependency bump changes
`Cargo.toml`/`Cargo.lock` only, which routes as **config → direct push**, but a
concurrent macro fix on the same branch routes as **code → PR** — and a commit
may legitimately contain both. Split them or state plainly why not.
