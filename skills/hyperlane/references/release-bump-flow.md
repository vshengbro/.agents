# Release Bump Flow (hyperlane monorepo)

Cycle for bumping the shared version of all workspace members in the monorepo.
Modeled on euv §17 + the 2026-09-13 PR #220 sync regression lesson.

## The invariant

**29 packages, 1 version number.** The workspace has the root `hyperlane`
package plus 28 members: `http-compress`, `http-constant`, `http-type`,
`http-request`, `hyperlane-core`, `hyperlane-macros`, `hyperlane-cli`, the
twenty `plugin/*` crates and `hyperlane-performance`. All resolve to the same
`<X.Y.Z>` through `version.workspace = true`. Verify with:

```bash
cargo metadata --no-deps --format-version 1 \
  | python3 -c 'import json,sys; print({p["name"]:p["version"] for p in json.load(sys.stdin)["packages"]})'
```

Every version must be identical. There is no second workspace and no second
`Cargo.lock`: the harness crate `hyperlane-performance` is an ordinary member
and its version is part of this invariant.

The current workspace version at `origin/master` (`04dee24`) is **`22.13.0`**,
and all twenty-nine packages resolve to it. The `22.7.0` release commit
(`91dfabc`) bumped only the root `Cargo.toml`; the follow-up commit
(`35d6562`) synced the member path-dependency pins and applied the crate
format. The `22.8.0` bump came with the public-field narrowing in
(`3495f37`). The `22.8.1` bump (`1264060`) was a dependency upgrade only —
no source file changed between `4d22b46` and `5637ac1`. The `22.8.2` bump
(`a1846f6`) added the `plugin/negotiate` crate and the `Accept-Encoding`
negotiation API in `http-compress`. Since then the tree grew a lot:
`02a26b8` reworked the request path and the HTTP/2 and HTTP/3 read paths,
`9e5b0fc` added `hyperlane fmt`, `24fbfc2` aligned `rust-standards` and the
`ctares` pins, `3b040ba` standardized the READMEs and this skill for
`22.12.0`, and `04dee24` bumped to `22.13.0` with `ctares` `10.9.0`.

## Manual flow (what a developer does)

```bash
cd /path/to/hyperlane
NEW_VER="22.13.0"
OLD_VER="22.12.0"

# 1. edit ONLY the root Cargo.toml
sed -i "s/^version = \"$OLD_VER\"$/version = \"$NEW_VER\"/" Cargo.toml

# 2. verify diff is exactly 1 file, +1/-1
git diff --stat
# expected:  Cargo.toml | 2 +-
git diff
# expected:  exactly one line in the version field

# 3. commit
git add Cargo.toml
git commit -m "chore: bump version to $NEW_VER"

# 4. push branch, open PR against hyperlane-dev/hyperlane
git push -u origin chore/bump-$NEW_VER
```

## What you must NOT do

- ❌ `sed -i "s/version = \"$OLD_VER\"/version = \"$NEW_VER\"/" */Cargo.toml`
- ❌ Edit `core/Cargo.toml` / `macros/Cargo.toml` / `type/Cargo.toml` /
  `cli/Cargo.toml` / any `plugin/*/Cargo.toml` version field manually
- ❌ Edit `[workspace.dependencies]` path-dep `version` field manually
- ❌ Edit any non-root `Cargo.toml` in the same PR

Doing any of these produces a multi-file diff that the maintainer will reject
because:

1. The CI sync job will overwrite those edits anyway.
2. They suggest the developer doesn't understand §17.
3. PR review at euv confirmed this is a hard reject signal.

## What the CI does (master merge only)

When a PR with a version bump is merged to master, the `publish` job runs a
step named **"Sync workspace dependency references"** (`if:
github.event_name == 'push' && github.ref_name == 'master'`). It:

1. Runs `crate sync` (from the external `crate-cli`) to bring every member's
   `[package].version` and every `[workspace.dependencies.<name>]` version pin
   in line with the root version.
2. Runs `crate fmt`.
3. Commits the result as `github-actions[bot] <github-actions[bot]@users.noreply.github.com>`
   with the message `chore: sync workspace member deps and apply crate fmt`
   and pushes to master, then re-reads the root version to derive the tag.
4. Runs `crate publish`, which resolves the publish order from
   `[workspace.members]` and skips any package with `publish = false`.

There is **no** separate `sync_workspace_version` job. The workflow jobs are
`setup`, `check`, `tests`, `clippy`, `build`, `publish` and `release`.

## Sync regression handling

If after merge the auto `chore: sync workspace member deps and apply crate fmt`
commit **does not appear** on master (e.g. the sync step silently used stale
root Cargo.toml content, or a token scope issue), recover with the same tool
the CI uses rather than a hand-written `sed` loop:

```bash
cd /path/to/hyperlane

# 1. the root version is the single source of truth
sed -i "s/^version = \"22.12.0\"$/version = \"22.13.0\"/" Cargo.toml

# 2. let crate-cli propagate it to every member and path-dep pin
crate sync
crate fmt

# 3. confirm the versions now agree
cargo metadata --no-deps --format-version 1 \
  | python3 -c 'import json,sys; print({p["name"]:p["version"] for p in json.load(sys.stdin)["packages"]})'

git add -A
git commit -m "chore: sync workspace member deps and apply crate fmt"
git push origin master
```

A hand-written `sed` over the member files is the thing that goes wrong: it
misses the `[workspace.dependencies]` pins and the `plugin/*` members, and it
produces a diff the sync step would immediately rewrite. Use `crate sync`.

## Patch vs minor/major bump

The path-dep pins are caret requirements (`version = "22.12.0"` means
`^22.12.0`), and a caret requirement for a `1.x`-or-higher crate allows every
`22.x` version. So the deciding factor is **which side of the caret's upper
bound the new version falls on**, not the bump label.

| Bump type | `Cargo.toml` version field | CI behavior |
| --- | --- | --- |
| patch | e.g. `22.12.0` → `22.13.0` | inside the range; `crate sync` propagates cleanly |
| minor | e.g. `22.12.0` → `22.14.0` | still inside the range for a `22.x` workspace — **resolves, the checks run** (the caret rule, unchanged; see [minor-bump-ci-red-by-design.md](minor-bump-ci-red-by-design.md)). It only breaks in a `0.x` workspace, where `^0.32.6` stops at `0.33.0`. |
| major | e.g. `22.12.0` → `23.0.0` | outside the range: `failed to select a version for the requirement `http-compress = "^22.12.0"`` |

Measured on 2026-11-07 with `cargo metadata` (full resolution) on a scratch
copy of each repository — see
[minor-bump-ci-red-by-design.md](minor-bump-ci-red-by-design.md) for the table
and the signal that tells a designed-in red from a real failure.

When the bump does cross the bound, the PR compile job is expected to FAIL
locally -- this is by design (the path-dep ranges are pinned to the old range
and need `crate sync` to bump them). Don't waste cycles trying to fix local
compile; commit just the root `Cargo.toml` bump, let CI sync do the rest, and
verify on the auto-commit that lands.

Every member of this workspace carries `publish = true`, so a version bump
publishes all twenty-nine crates — including the harness crate
`hyperlane-performance`, which the release job's package list names last, and
the twenty plugin crates, which sit between the facade and the harness. A
package with `publish = false` would be skipped instead, with `crate publish`
logging `Skipping <name> (publish = false)` and continuing with the rest.

## Real-world PRs to study

- PR #171: patch bump 0.20.0 → 0.20.1, clean single-commit flow.
- PR #220: patch bump with the `cargo publish` curl-35 post-verify false-alarm
  pitfall. See `references/minor-bump-ci-red-by-design.md` for
  the full story (also applies to hyperlane post-monorepo).
- euv PR #196/197: sync_workspace_version wrote the wrong version because
  it read stale root content -- recovery flow shown above.