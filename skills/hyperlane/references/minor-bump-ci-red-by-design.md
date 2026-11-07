# A bump that leaves the old caret range is red by design

> Verified by bumping the root `Cargo.toml` of a scratch copy of each repository
> and running `cargo metadata` (full resolution) on it. The hyperlane rows were
> re-measured against the current `22.2.0` pins; the euv rows against the
> current `0.34.2` pins:
>
> | repo | old pin | bumped to | result |
> |---|---|---|---|
> | hyperlane | `^22.2.0` | `22.2.1` | resolves |
> | hyperlane | `^22.2.0` | `22.3.0` | **resolves** |
> | hyperlane | `^22.2.0` | `23.0.0` | fails: `failed to select a version for the requirement `http-compress = "^22.2.0"`` |
> | euv | `^0.34.2` | `0.34.3` | resolves |
> | euv | `^0.34.2` | `0.35.0` | fails: `failed to select a version for the requirement `euv-core = "^0.34.2"`` |
> | euv | `^0.34.2` | `1.0.0` | fails: same requirement error |
>
> **The rule is not "a minor bump breaks".** A caret requirement `^X.Y.Z` means
> `>=X.Y.Z, <(X+1).0.0` when `X >= 1`, but `>=X.Y.Z, <X.(Y+1).0` when `X == 0`.
> So a **minor** bump breaks a `0.x` repository (euv: `0.34.2` → `0.35.0`) and
> leaves a `1.x`-or-higher repository alone (hyperlane: `22.2.0` → `22.3.0`).
> Only a bump that crosses the caret's upper bound fails. A **major** bump
> always crosses it.
>
> **The sections below that mention `euv`, `Signal::subscribe`, the wasm32 target
> or `GH_TOKEN` were recorded against the euv repository. They are kept as
> transferable CI lessons, not as hyperlane facts** — the hyperlane workflow has
> no wasm32 build job and no post-publish curl verification.

## The phenomenon

After the root `Cargo.toml` version is bumped past the range the member
`[workspace.dependencies]` path-dep pins still carry:

- the member pins still carry the old range (`^22.2.0` in hyperlane, `^0.34.2`
  in euv);
- cargo fails during **version resolution**, before any compilation;
- the error looks like `failed to select a version for the requirement ...`;
- **the diff is one line in the root `Cargo.toml`. This is not a code problem, so
  do not "fix" the code.**

A bump that stays inside the old range resolves and the checks run normally.
For hyperlane that includes every `22.x` version; for euv it stops at the next
`0.35.0`.

## Telling a designed-in red from a real problem

| Signal | Designed-in red | A real problem |
|---|---|---|
| Which jobs fail | build, clippy and tests together | any single one |
| Job lifetime | seconds (version resolution) | through compilation or the test phase |
| The error text | `failed to select a version` | a concrete compile error |
| The PR diff | one line in the root `Cargo.toml` | contains code changes |

## Merge path

A bump PR whose checks are red for the designed-in reason is merged with
`gh pr merge --admin --squash` without waiting for green. After the merge, the
CI `publish` job runs `crate sync` + `crate fmt` on the master push and commits
the synchronised versions.

**A green run does not mean "it was really a patch bump".** It means the bumped
version stayed inside the caret range of the old pins — true for every `22.x`
version in hyperlane, false for the first `0.35.0` in euv. Read the failing
requirement in the error text to tell which case you are in.

**Always verify after the merge that the sync commit carries the new version
number.** A sync job has written a stale root version before, needing a manual
fix commit.

## Verifying a minor-bump working tree locally (and rolling it back)

With the root bumped and the member pins not yet synchronised, `cargo check`
fails. To verify locally:

1. temporarily point every version at the target number (the root plus the member
   `Cargo.toml` files; lock the `[workspace.dependencies]` path-dep lines with a
   grep first, so a non-path-dep line such as `compare_version = "2.0.14"` is not
   caught);
2. run `cargo check` / `cargo test`;
3. **roll back file by file with `git checkout HEAD --`, leaving only the root
   version line**, then commit.

Not rolling back breaks the "change one line only" rule.

## The old "reproduce the CI sync locally and commit it" approach is withdrawn

Reproducing the CI sync's `sed` locally and committing the result alongside the
PR was the wrong approach in the 0.15.x era; it was reverted and redone. The
correct flow is the one above: change only the root line, merge with an admin
squash, and let the CI sync fill the rest in.

## Check for a version-number collision before opening a bump PR

List the open PRs and look for an in-flight bump. If one is already open for the
next number, the following PR's version has to wait for it to land and then
start a patch bump from the new master; opening two bump numbers in parallel
collides or reverses their order.

## An exhaustive sweep is required when a subscription id type changes (recorded on the euv repository)

When the type of the subscription id returned by `Signal::subscribe` changes
(this was `u64` to `usize`):

**search for more than the direct calls**:

```bash
# direct: any local that stores or uses a subscribe() result
grep -rn 'let [a-z_]*id.*= .*\.subscribe(\|let subscription_id.*signal\.subscribe(' \
  --include='*.rs' core/ macros/ ui/ engine/

# indirect: closure capture, Cell/RefCell/Rc/Arc wrappers
grep -rn 'Cell<u\|Cell<\?usize\?>\|RefCell<u\|Rc<Cell\|Arc<Cell' \
  --include='*.rs' core/ macros/ ui/ engine/

# indirect: an unsubscribe(id_value) inside a closure body
grep -rn 'unsubscribe(' --include='*.rs' core/ macros/ ui/ engine/
```

`core/src/vdom/cast/impl.rs:251-259` matched the pattern "an `Rc<Cell<u64>>`
holds the id inside a closure, and the subscribe closure body calls
`source.unsubscribe(listener_id.get())` back, re-entrant self-unsubscribe". Such
an indirect binding is not covered by the direct grep. Changing the id type has to
take it along, or the build reports E0308.

**CI builds for release on the wasm32 target** (the euv build job runs
`cargo check --release --all-features --target wasm32-unknown-unknown --workspace
--exclude euv-cli`). **A local `cargo check --workspace --all-targets`** (the
default dev profile, host target) **misses a wasm-only type mismatch** like this
one. A pre-commit `cargo check --workspace --all-targets` that exits 0 does not
prove the PR is clean, so add this to the pre-submit checklist:

```bash
cargo check --release --all-features --target wasm32-unknown-unknown --workspace --exclude euv-cli
```

**This is an euv fact, not a hyperlane one.** The hyperlane workflow's build job
runs `cargo check --release --workspace --all-features` on the host target, with
no wasm32 job.

## Admin fallback when the version-sync push fails (recorded on the euv repository)

When the version-sync GitHub Action commits `chore: sync all package versions
to X.Y.Z` on a master push and then fails to `git push`, the usual causes are:

- the CI token lacks the `workflow` / `contents: write` scope;
- a branch protection rule rejects the push (it requires review or a status check);
- a race on master, where the sync job's ref is older than the current HEAD.

When the CI log reports `remote rejected` / `failed to push some refs`, an admin
can reproduce the sync commit and push it to master directly:

```bash
cd ~/github/euv-dev/euv
git fetch euv-dev master
git checkout -b tmp-sync-$NEW_VER euv-dev/master
# replace the root Cargo.toml [package].version + the 6 path-dep lines
for d in cli core engine example macros ui; do
  sed -i "s/^version = \"$OLD_VER\"\$/version = \"$NEW_VER\"/" $d/Cargo.toml
done
# in the workspace.dependencies section: grep-lock the lines before sedding, so a
# non-path-dep line such as 'compare_version = "2.0.14"' is not caught
sed -i "s/version = \"$OLD_VER\"\$/version = \"$NEW_VER\"/g" Cargo.toml
git diff --stat   # expected: 7 files changed, 14 insertions(+), 14 deletions(-)
# keep the commit author identical to the sync job's, so git log --author=... still works
git -c user.name='eastspire' -c user.email='root@ltpp.vip' commit -m "chore: sync all package versions to $NEW_VER"
git push euv-dev tmp-sync-$NEW_VER:master   # admin pushes master directly
# verify: master HEAD carries this commit and every version agrees
git fetch euv-dev master
git show euv-dev/master:Cargo.toml | head -3
for d in cli core engine example macros ui; do
  echo -n "$d: "; git show euv-dev/master:$d/Cargo.toml | grep '^version' | head -1
done
```

**Important**: after the push, master triggers the sync job once more; seeing it
write the same version (a no-op or an empty commit) confirms the state has
converged.

**For hyperlane, prefer `crate sync`.** The hyperlane workflow runs `crate sync`
+ `crate fmt` inside its `publish` job, so a manual sed loop is only the fallback
when that job's own push fails.

## A corner case: `cargo fmt --check` still fails after a rebase conflict

In a three-way merge (`<<<<<<< HEAD` / `=======` / `>>>>>>> branch`), deleting
only the middle conflict block easily leaves the two sides' identical comment
lines duplicated, with one of them at the wrong indentation. `cargo check` passes
(`cargo fmt` does not take part in compilation), but `cargo fmt --check` fails, so
the CI `Format check` job fails.

The typical example (`engine/src/renderer/impl.rs:3134-3135`):

```rust
        // OPT 2b: cached `pass.setIndexBuffer(buffer, format)`.
// OPT 2b: cached `pass.setIndexBuffer(buffer, format)`.   // <- 8 spaces short, fmt rejects it
        // The two spec formats hit the thread-local ...
```

Both `// OPT 2b: ...` lines were merged and one side's comment was picked, but
the pick landed in the wrong context — an orphan moved down from the previous
line, with its original indentation lost.

**Prevention**:
1. after a rebase and before amending the commit, **run `cargo fmt --all -- --check`
   directly**; if it exits non-zero, run `cargo fmt` and fix it before continuing.
2. before force-pushing a PR head, **always run** `cargo fmt --all -- --check`
   plus the release check from the previous section.
3. if CI has already failed (`Format check`), open a PR that fixes the comment
   (1 file / 1 line / 1 commit) instead of reverting the whole PR — the PR may
   carry other legitimate changes.

## A CI publish job that fails although the publish succeeded (recorded on the euv repository)

The `publish` job's post-publish verification curl hit a transient network/TLS
error under `set -e` (curl exit 35 = `CURLE_SSL_CONNECT_ERROR`) -> the script
aborted -> the publish job reported failure -> the release job
(`needs.publish.result == 'success'`) was blocked -> **no `vX.Y.Z` git tag and no
GitHub Release**, even though every crate had already been uploaded to crates.io.

**The symptom**: the CI log shows all 6 crates as
`✅ ... verified on crates.io (HTTP 200)` and then
`##[error]Process completed with exit code 35`. The crates.io API still reports
`max_version=X.Y.Z max_stable=X.Y.Z` — the publish really did succeed.

**The fix in `.github/workflows/rust.yml`** (1 file, +1/-1; add `|| echo "000"` to
the end of the curl):

```diff
- VERIFY_HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "User-Agent: euv" "https://crates.io/api/v1/crates/$PKG_NAME/$VERSION")
+ VERIFY_HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "User-Agent: euv" "https://crates.io/api/v1/crates/$PKG_NAME/$VERSION" || echo "000")
```

The verification is informational — `cargo publish` already exited 0 and the
registry accepted the upload, so the verification must not block the script.

**Recovering an already published version** (the workflow fix only covers the
next run; an already published X.Y.Z has no tag or release):

```bash
# 1. create the tag on that version's master HEAD (usually the sync commit)
git tag -a v0.24.1 <sync-commit-sha> -m "v0.24.1"
git push origin v0.24.1

# 2. create the GitHub Release with gh release create (source zip + tar.gz)
PACKAGE_NAME=euv VERSION=0.24.1 TAG=v0.24.1
git archive --format=zip --prefix="${PACKAGE_NAME}-${VERSION}/" HEAD > "${PACKAGE_NAME}-${VERSION}.zip"
git archive --format=tar.gz --prefix="${PACKAGE_NAME}-${VERSION}/" HEAD > "${PACKAGE_NAME}-${VERSION}.tar.gz"
gh release create "$TAG" \
  --title "[master]($TAG published $(date '+%Y-%m-%d %H:%M:%S'))" \
  --notes "..." \
  --latest
gh release upload "$TAG" "${PACKAGE_NAME}-${VERSION}.zip" "${PACKAGE_NAME}-${VERSION}.tar.gz"
```

**The hyperlane workflow has no such verification step**: its `publish` job runs
`crate publish` and then echoes `ALL PUBLISH SUCCESSFUL`, with no curl and no
`set -e` around a network call. The lesson above therefore does not apply to
hyperlane as it stands.

## When the GH_TOKEN lacks the `read:org` scope, create and merge PRs over REST (recorded on the euv repository)

That repository's GH_TOKEN scopes are `notifications, repo, workflow` (no
`read:org`). `gh pr create` / `gh pr merge` / `gh pr close` go through GraphQL and
are rejected:

```
GraphQL: Something went wrong while executing your query on ...
```

`gh pr view` / `gh pr checks` / `gh api .../pulls/N` use REST and work.

**The workaround** (known to be reliable):

```bash
# create the PR
TOKEN=$GH_TOKEN
python3 -c 'import json,sys;body=open("/tmp/pr-body.md").read();print(json.dumps({"title":"...","head":"eastspire:branch","base":"master","body":body}))' > /tmp/pr-payload.json
curl -sS -X POST https://api.github.com/repos/euv-dev/euv/pulls \
  -H "Authorization: token ***" -H 'Accept: application/vnd.github.v3+json' \
  -H "Content-Type: application/json" -d @/tmp/pr-payload.json | python3 -c 'import json,sys;d=json.loads(sys.stdin.read());print("PR #"+str(d["number"])+":",d["html_url"])'

# merge the PR
curl -sS -X PUT https://api.github.com/repos/euv-dev/euv/pulls/N/merge \
  -H "Authorization: token ***" -H 'Accept: application/vnd.github.v3+json' \
  -d '{"merge_method": "squash", "delete_branch": true}'
```

**The GitHub Actions API occasionally returns 502 Bad Gateway** — the first REST
call can come back `non-200 OK status code: 502 Bad Gateway`, and a retry is
usually a 200. After a merge, `gh pr merge` may also return a GraphQL error, so
use `curl PUT` directly.

`gh pr edit` goes through GraphQL too and is rejected -> change the title and body
over REST:

```bash
curl -sS -X PATCH https://api.github.com/repos/euv-dev/euv/pulls/N \
  -H "Authorization: token ***" \
  -F title="..." -F body=@file.md
```

## A false rustfmt error from the patch tool (let chains, Rust 2024)

The rustfmt bundled with the patch tool is old (< 1.85) and reports
`error: let chains are only allowed in Rust 2024 or later` for Rust 2024 `let
chains` syntax — a false positive, since the edition *is* 2024. A
`lint.status: error` in the patch output does not mean the code is wrong: as long
as the edit is local (the tool says "Pre-existing lint errors — this edit didn't
introduce new ones"), submit it. CI passes with a current rustc. **Rule**: after
a patch error, trust the `cargo check` exit code, not the patch tool's own lint
output.
