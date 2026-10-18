---
name: gh-pr-creation-workflow
description: "Use when creating, updating, checking or merging a GitHub pull request. Verify the exact head, CI and landed content; follow git-standards for commit policy and direct-push decisions."
license: MIT
---

# GitHub PR lifecycle

First apply [`git-standards`](../git-standards/SKILL.md). `.agents` always pushes
directly to `master`; do not create a PR for it. An explicit current user delivery
instruction overrides generic routing, not hook checks or unrelated scope.

## 1. Resolve the target and authorization

1. Read `git status --short`, branch, remotes and local-ahead commits. Preserve
   unrelated work; do not reset or stash it merely to run a recipe.
2. Resolve the authenticated login and repository live:
   `gh api user --jq .login` and `gh repo view --json nameWithOwner,defaultBranchRef,viewerPermission`.
3. With `WRITE`/`MAINTAIN`/`ADMIN`, push a feature branch to that upstream; do not
   create a needless fork. Without write permission, use a real GitHub fork and
   verify its `parent` before choosing `--head <user>:<branch>`.
4. Resolve an existing PR by exact head branch before creating another. If the
   selected PR already merged, inspect ancestry and open a new PR for the remaining
   delta; do not reuse a squashed branch or reopen a merged PR.

## 2. Create or update

```bash
git fetch origin
gh pr list --repo <owner>/<repo> --head <branch> --state open --json number,headRefOid,baseRefName,url
git push -u <authorized-remote> <branch>
gh pr create --repo <owner>/<repo> --base <default> --head <branch> \
  --title "<type>(<scope>): <subject>" --body-file <scratch>/pr-body.md
gh pr view <number> --repo <owner>/<repo> --json state,headRefOid,baseRefName,title,body,url,changedFiles
```

For a fork, use `<user>:<branch>` and confirm which remote is fork versus source.
For updates, push the existing head and use `gh pr edit --body-file` if text changed.
No history rewriting unless separately authorized; never fall back from a rejected
lease to unconditional `--force`.

Read back title, complete body, base, head SHA and file list. For large diffs use
`gh api --paginate --slurp repos/<owner>/<repo>/pulls/<number>/files?per_page=100`
and reconcile unique filenames with `changedFiles` and the local diff; a truncated
listing is not complete verification.

## PR body 风格

English only; use `--body-file` so shell expansion cannot corrupt backticks or
`${VAR}`. The title follows Conventional Commits and summarizes the whole PR.

```markdown
## Summary
<what and why>

## Changes
- <reviewed change>

## Verification
- <command actually run and result>

## Notes
<trade-offs or remaining blockers; Closes #N when applicable>
```

## 3. Verify CI, then merge only when authorized

- Bind all applicable checks to the **current head SHA**, distinguishing push,
  pull_request and separate workflow runs. Inspect actual required checks and
  allowed merge methods; do not change repository settings to force one merge.
- `gh pr checks <number> --watch` assists waiting, but green old runs, an empty
  required-check list, or enabled auto-merge do not prove every applicable job passed.
- Without user merge authorization, report the PR and stop. With authorization,
  wait for its applicable checks and re-read state/head/checks immediately before
  merging. If the head changed, invalidate the previous verification.

```bash
gh pr view <number> --repo <owner>/<repo> --json state,headRefOid,statusCheckRollup
gh pr merge <number> --repo <owner>/<repo> --squash --match-head-commit <verified-sha> --delete-branch
```

Use the permitted merge strategy; never use administrative bypasses. Native
`--auto` is only a queued request, and its protection policy may not wait for all
running jobs. Do not report it as merged until the remote confirms the merge.

## 4. Prove delivery and clean up

Read the exact PR's `state`, `mergeCommit`, `headRefOid`, and intended base ref.
Verify delivered file blobs/deletions against the merge tree, not just `MERGED`.
If a newer base commit exists, verify the intended content still exists there.

Delete only the authorized, verified-merged head branch; confirm its exact remote
ref is gone. A squash can make `git branch -d` reject: inspect remaining commits
rather than blindly applying `-D`. Do not change repo-wide deletion settings for
one PR or delete somebody else's branch. Leave a dirty current checkout alone.
Close owned temporary worktrees, processes and browser tabs on every exit path;
report identifiers of any resource that could not be reclaimed.

## Specific failures

- [CI, stale PRs and rebase conflicts](references/ci-and-stale-prs.md)
- [Network/API fallbacks and build-output repositories](references/network-and-api-fallbacks.md)
- [Bugfix body template](templates/pr-body-bugfix.md) · [Feature body template](templates/pr-body-feature.md)

Keep one review thread intact: use the review-comment replies endpoint for a reply,
not a new top-level `gh pr comment`. Permission failures require diagnosis, not
repeated writes or an API route that bypasses the user's authorization.
