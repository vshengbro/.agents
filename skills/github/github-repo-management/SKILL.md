---
name: github-repo-management
description: 'Use when cloning, creating, forking, configuring or releasing a GitHub repo: remotes, settings, secrets, Actions, releases, gists and Discussions via gh CLI or REST.'
license: MIT
---
# github-repo-management

Repository-level operations. `gh` first; every section names the REST fallback
for when `gh` is missing or its token lacks a scope. Auth setup is
`github-auth`; PR mechanics are `gh-pr-creation-workflow`.

```bash
source "${HERMES_HOME:-$HOME/.hermes}/skills/github/github-auth/scripts/gh-env.sh"
# sets GH_AUTH_METHOD, GH_USER, GH_OWNER/GH_REPO/GH_OWNER_REPO inside a repo
```

Never put a token in a URL — pass it as an `Authorization` header; it ends up in
shell history and the remote URL.
## Index

Clone · Create · Fork · Read repo state · Settings · Branch protection, secrets, variables · Releases · Delete · Actions, gists, CI · Discussions · Pitfalls


## Clone

```bash
gh repo clone owner/repo -- --depth 1     # large repo
git clone --filter=blob:none git@github.com:owner/repo.git
```

On a throttled host, `gh api …/contents/… --jq .content | base64 -d` reads
individual files without cloning; the tarball/Contents-API recipes are in
`gh-pr-creation-workflow/references/network-and-api-fallbacks.md`.

## Create

**New repos are private by default.** Never pass `--public` unless the user
asked for public in that turn.
```bash
gh repo create my-project --private --clone
gh repo create my-org/my-project --private --description "…" --license MIT --clone
gh repo create my-project --source . --private --push      # from an existing dir
```

REST: `POST /user/repos` (personal) or `POST /orgs/<org>/repos` with
`{"private": true}`. A new repo also needs the mirror workflow
(`.github/workflows/mirror.yml`) and the `GITEE_TOKEN` / `GITCODE_TOKEN` secrets
— the workflow hard-fails without them by design, and a private source repo must
get private mirrors (never `"private": false`).

## Fork

```bash
gh repo fork owner/repo --clone          # adds the fork as a remote
git remote add upstream git@github.com:owner/repo.git
gh repo sync owner/repo                  # or: git fetch upstream && git merge upstream/<default>
```

Forking a repo you already own fails (`cannot be forked. A single user account
cannot own both a parent and fork`), and orgs may disable forking entirely
(`POST /repos/<o>/<r>/forks` → 403). With write access, skip the fork and push
the branch to the upstream directly.

## Read repo state

```bash
gh repo view <o>/<r> --json defaultBranchRef,deleteBranchOnMerge,viewerPermission,isFork,parent
gh api repos/<o>/<r> --jq '{private,allow_auto_merge,delete_branch_on_merge,permissions}'
gh repo list --limit 20
gh search repos "query" --sort stars
```

Enumerate **all** branches with `gh api repos/<o>/<r>/git/refs/heads` — the
`/branches` endpoint returns only protected and default branches, so it reports
a false "only master exists" when auditing leftovers.

## Settings

```bash
gh repo edit <o>/<r> --delete-branch-on-merge          # makes gh pr merge --delete-branch work
gh repo edit <o>/<r> --enable-auto-merge               # optional; verify before relying on --auto
gh repo edit <o>/<r> --default-branch main --add-topic rust,wasm
gh api -X PATCH repos/<o>/<r> -f delete_branch_on_merge=true   # REST equivalent
```

REST equivalents: `references/github-api-cheatsheet.md`. Visibility changes need
`--accept-visibility-change-consequences`.

## Branch protection, secrets, variables

Branch protection, the `gh secret` / `gh variable` commands, and the libsodium
`SealedBox` path for setting a secret over REST are in
[references/github-api-cheatsheet.md](references/github-api-cheatsheet.md).

## Releases

```bash
gh release create v1.2.0 --generate-notes
gh release create v1.2.0 ./dist/binary --title "v1.2.0" --notes "…"
gh release list && gh release download v1.2.0 --dir ./downloads
```

REST: `POST /repos/<o>/<r>/releases`, then upload the asset with a
`Content-Type: application/octet-stream` POST to
`uploads.github.com/repos/<o>/<r>/releases/<id>/assets?name=…`.

## Delete

```bash
gh repo delete owner/repo --yes
gh api -X DELETE repos/<o>/<r>
```

**The API needs the `delete_repo` scope** — `repo` alone answers `403` naming
the missing scope, and `gh auth refresh -h github.com -s delete_repo` then
demands a sudo-mode re-auth that is the user's to complete.

Bulk fork cleanup — proving a fork is disposable (no unique commits, no unique
branch, no open PR, no release, no workflow reference), the compare-API and
PR-filter traps, the multi-stage web-UI flow, and the pitfalls below — is in
[references/fork-audit-and-bulk-deletion.md](references/fork-audit-and-bulk-deletion.md).

## Actions, gists, CI
```bash
gh workflow list && gh run list --limit 10
gh run view <RUN_ID> --log-failed
gh run rerun <RUN_ID> --failed
gh workflow run deploy.yml -f environment=staging
```

A specific PR's checks: `gh pr checks <N> --watch` (exit 8 = pending). Without
`gh`, `GET /repos/<o>/<r>/actions/runs/<id>/logs` returns a zip — unzip and read.
Failure triage table: `gh-pr-creation-workflow/references/ci-and-stale-prs.md`.
Gists: `gh gist create script.py --public --desc "…"` (REST `POST /gists`).

## Discussions

A Discussion is for conversation (announcements, Q&A, show-and-tell, roadmap,
polls); an Issue is for work (bugs, features with acceptance criteria). Don't
file benchmark results as issues or reproducible crashes as discussions. The
`gh discussion` commands, the `write:discussion` scope it needs, and the
GraphQL-only path are in
[references/github-api-cheatsheet.md](references/github-api-cheatsheet.md).

## Pitfalls
1. Creating a public repo when private was meant — omit the flag or pass
   `--private`.
2. Forking a repo you already own, or one with forking disabled.
3. Branch audits through `/branches` instead of `/git/refs/heads`.
4. Assuming `gh pr merge --delete-branch` works — it needs the repo's
   `delete_branch_on_merge` setting.
5. Tokens in remote URLs or `curl` query strings.
6. Trusting `gh repo view --json allowAutoMerge` — that field does not exist; use
   `gh api repos/<o>/<r> --jq .allow_auto_merge`.
7. Editing a repo that holds only deployed build output — find the source repo
   first (`gh-pr-creation-workflow/references/network-and-api-fallbacks.md`).
8–11. The fork-deletion traps — the `delete_repo` scope, the owner-only PR
   filter, `/user/repos` missing `parent`, and verifying a delete by `GET`
   rather than by loading the page — are in
   [references/fork-audit-and-bulk-deletion.md](references/fork-audit-and-bulk-deletion.md).
