# Release Bump Flow (hyperlane monorepo)

Cycle for bumping the shared version of all workspace members in the monorepo.
Modeled on euv §17 + the 2026-09-13 PR #220 sync regression lesson.

## The invariant

**14 packages, 1 version number.** The workspace has the root `hyperlane`
package plus 13 members: `http-compress`, `http-constant`, `http-type`,
`http-request`, `hyperlane-core`, `hyperlane-macros`, `hyperlane-cli`,
`hyperlane-plugin-compression`, `hyperlane-plugin-cors`,
`hyperlane-plugin-logger`, `hyperlane-plugin-shutdown`,
`hyperlane-plugin-static-files` and `hyperlane-plugin-websocket`. All resolve
to the same `<X.Y.Z>` through `version.workspace = true`. Verify with:

```bash
cargo metadata --no-deps --format-version 1 \
  | python3 -c 'import json,sys; print({p["name"]:p["version"] for p in json.load(sys.stdin)["packages"]})'
```

Every version must be identical. The `bench/` crates are **not** members of
this workspace: they are a separate Cargo workspace with their own
`Cargo.lock`, and their version is not part of this invariant.

## Manual flow (what a developer does)

```bash
cd /root/github/hyperlane-dev/hyperlane
NEW_VER="21.3.7"
OLD_VER="21.3.6"

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
   `[workspace.members]` and skips every package with `publish = false`.

There is **no** separate `sync_workspace_version` job. The workflow jobs are
`setup`, `check`, `tests`, `clippy`, `build`, `publish` and `release`.

## Sync regression handling

If after merge the auto `chore: sync workspace member deps and apply crate fmt`
commit **does not appear** on master (e.g. the sync step silently used stale
root Cargo.toml content, or a token scope issue), recover with the same tool
the CI uses rather than a hand-written `sed` loop:

```bash
cd /root/github/hyperlane-dev/hyperlane

# 1. the root version is the single source of truth
sed -i "s/^version = \"21.3.6\"$/version = \"21.3.7\"/" Cargo.toml

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

| Bump type | `Cargo.toml` version field | CI behavior |
| --- | --- | --- |
| patch | e.g. `21.3.6` → `21.3.7` | `crate sync` propagates cleanly |
| minor | e.g. `21.3.6` → `21.4.0` | local `cargo check` may fail on path-dep version mismatch (the `[workspace.dependencies]` pins still say `^21.3.6`). Run `crate sync` locally to verify; CI redoes it on the master push. |
| major | e.g. `21.3.6` → `22.0.0` | same as minor |

For minor/major, the PR compile job is expected to FAIL locally -- this is
by design (the path-dep ranges are pinned to the old range and need
`crate sync` to bump them). Don't waste cycles trying to fix local compile;
commit just the root `Cargo.toml` bump, let CI sync do the rest, and verify on
the auto-commit that lands.

The crates that carry `publish = false` (the five newer plugin crates and the
three `bench-*` crates) never reach crates.io, so a version bump does not
publish them. `crate publish` logs `Skipping <name> (publish = false)` for
each of them and continues with the rest.

## Real-world PRs to study

- PR #171: patch bump 0.20.0 → 0.20.1, clean single-commit flow.
- PR #220: patch bump with the `cargo publish` curl-35 post-verify false-alarm
  pitfall. See `references/minor-bump-ci-red-by-design.md` for
  the full story (also applies to hyperlane post-monorepo).
- euv PR #196/197: sync_workspace_version wrote the wrong version because
  it read stale root content -- recovery flow shown above.