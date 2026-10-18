---
name: github-issues
description: 'Use when creating, searching, triaging or closing GitHub issues: title/body, labels, assignees, comments and bulk operations via gh issue or the REST API.'
license: MIT
---
# github-issues

Issue management. A Discussion is the right surface for conversation and a PR
for review — this skill is for work items with acceptance criteria. Auth is
`github-auth`; PR mechanics are `gh-pr-creation-workflow`.

```bash
source "${HERMES_HOME:-$HOME/.hermes}/skills/github/github-auth/scripts/gh-env.sh"
# GH_OWNER / GH_REPO from the git remote; pass --repo <o>/<r> to override
```

## Read

```bash
gh issue list --state open --label bug --assignee @me
gh issue list --search "authentication error" --state all
gh issue view 42 --json number,title,body,labels,assignees,comments,state
```

**Read the whole thread, not just the body** — `gh issue view 42 --comments`.
The body is a snapshot from filing time; the newest comments carry partial
fixes already merged, new root-cause analysis, and questions that change the
task.

`gh issue view` prints nothing with a restricted token; fall back to
`gh api repos/<o>/<r>/issues/<N>`.

## Create

```bash
gh issue create --title "Login redirect ignores ?next=" \
  --body-file /tmp/issue.md --label "bug,backend" --assignee @me
```

Body templates: `templates/bug-report.md` (description / steps / expected /
actual / environment / error output) and `templates/feature-request.md`
(description / motivation / proposed solution / alternatives / scope).

All GitHub-visible text is English — the same rule commits follow
(`git-standards` §1).

## Manage

```bash
gh issue edit 42 --add-label "priority:high" --remove-label needs-triage
gh issue edit 42 --add-assignee @me
gh issue comment 42 --body "Root cause is in auth middleware; fix in progress."
gh issue close 42 --reason "not planned"
gh issue reopen 42
```

Close keywords go in the **PR body**, not a comment — `Closes #42` /
`Fixes #42` / `Resolves #42` close the issue when the PR merges.

## Triage

1. List the untriaged: `gh issue list --label needs-triage --state open`.
2. Read each in full (body + comments) before labelling.
3. Check for duplicates: `gh issue list --search "<symptom>" --state all`, and
   `gh pr list --search "<symptom>" --state all` — a fix may already be open.
4. Apply labels/priority, assign if the owner is clear, leave a triage note
   only if it adds information.

## Branch from an issue

```bash
gh issue develop 42 --checkout            # creates and checks out a linked branch
gh issue develop --list                   # linked branches for this issue
```

## Bulk

```bash
gh issue list --label wontfix --json number --jq '.[].number' \
  | xargs -I{} gh issue close {} --reason "not planned"
```

## REST equivalents

| Action | Endpoint |
|---|---|
| List / create | `GET`/`POST /repos/{o}/{r}/issues` |
| View / update | `GET`/`PATCH /repos/{o}/{r}/issues/{N}` |
| Labels | `POST /issues/{N}/labels`, `DELETE /issues/{N}/labels/{name}` |
| Assignees | `POST /issues/{N}/assignees` |
| Comments | `POST /issues/{N}/comments` |
| Search | `GET /search/issues?q=…+repo:{o}/{r}` |

`/issues` also returns pull requests — filter `"pull_request" not in item`.

## Pitfalls

1. Acting on the issue body while the newest comment supersedes it.
2. Building a fix a duplicate open PR already covers — sweep first.
3. Closing the issue with a comment instead of `Closes #N` in the PR body.
4. Writing the body inline with `--body "…"` and losing backticks — use
   `--body-file`.
5. Non-English issue/PR text.
