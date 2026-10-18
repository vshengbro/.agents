---
name: github-code-review
description: 'Use when reviewing a pull request or a local diff: fetch the PR, apply a correctness/security/testing checklist, then post inline or formal review comments via gh or REST.'
license: MIT
---
# github-code-review

Reviewing code, not shipping it: `gh-pr-creation-workflow` owns the PR
lifecycle, this owns the judgement and the review comments. Auth is
`github-auth`.

## Local diff (no API needed)

```bash
git diff main...HEAD --stat              # scope
git diff main...HEAD                     # content
git diff main...HEAD -- path/to/file.py # per file
git diff --staged                        # what a commit would contain
```

Scan for the usual residue before reading closely:

```bash
git diff main...HEAD | grep -nE 'print\(|console\.log|TODO|FIXME|HACK|debugger'
git diff main...HEAD | grep -inE 'password|secret|api_key|token *=|private_key'
git diff main...HEAD | grep -nE '^(<<<<<<<|>>>>>>>|=======)'
```

Report in Critical / Warnings / Suggestions / Looks Good, with
`file:line` and a concrete fix per finding; the fill-in skeleton and severity
guide are in `references/review-output-template.md`. Present it as a message to
the user — no PR is involved in a local review.

## Review a PR

```bash
source "${HERMES_HOME:-$HOME/.hermes}/skills/github/github-auth/scripts/gh-env.sh"

gh pr view <N> --json number,title,author,headRefOid,baseRefName,additions,deletions,changedFiles
gh pr diff <N> --name-only
gh pr checks <N>                       # is CI already failing?
git fetch origin pull/<N>/head:pr-<N> && git checkout pr-<N>   # or: gh pr checkout <N>
git diff <base>...HEAD                 # read it locally, with real context
```

Check out the PR before reviewing it — a diff alone hides defects that only
appear in surrounding code, and it lets you run the tests.

## Checklist

- **Correctness** — does it do what it claims; empty/null/large/concurrent inputs; error paths.
- **Security** — hardcoded secrets, input validation, injection, authz on new endpoints, path traversal.
- **Quality** — naming, unnecessary complexity, duplication, single-responsibility functions.
- **Testing** — new paths covered, happy path *and* error cases, assertions that could actually fail.
- **Performance** — N+1 queries, blocking calls in async code, missing cache on a hot path.
- **Docs** — public API documented, README updated when behaviour changed.

Pick the verdict from the findings: **approve** with only suggestions,
**request changes** on any critical or warning, **comment** when unsure or the
PR is a draft.

## Post the review

```bash
# formal review
gh pr review <N> --approve --body "…"
gh pr review <N> --request-changes --body "See inline comments."
gh pr review <N> --comment --body "Suggestions, nothing blocking."

# one inline comment — line is the line number in the NEW file
HEAD_SHA=$(gh pr view <N> --json headRefOid --jq .headRefOid)
gh api repos/<owner>/<repo>/pulls/<N>/comments --method POST \
  -f body="Could be simplified with a list comprehension." \
  -f path="src/auth/login.py" -f commit_id="$HEAD_SHA" -f line=45 -f side=RIGHT

# summary comment
gh pr comment <N> --body-file /tmp/review.md
```

Atomic multi-comment review (one request, all inline comments attached):
`POST repos/<o>/<r>/pulls/<N>/reviews` with `commit_id`, `event` (`APPROVE` |
`REQUEST_CHANGES` | `COMMENT`), `body`, and a `comments[]` of `{path, line,
body}`. Use `"side": "LEFT"` for deleted lines.

To reply **inside** an existing review thread, post to
`POST …/pulls/<N>/comments/<comment-id>/replies` — `gh pr comment` opens a new
top-level comment and fragments the thread.

```bash
git checkout <base> && git branch -D pr-<N>    # clean up the review branch
```

## Pitfalls

1. Reviewing from the diff alone instead of checking out the branch.
2. Bulk `git comment` replies where a threaded reply was expected.
3. `line` numbers taken from the old file — the field is the *new* file's line.
4. `gh pr view <N>` printing nothing with a restricted token — use
   `--json …` or `gh api repos/<o>/<r>/pulls/<N>`.
5. Approving on a red PR, or calling it green without reading `gh pr checks`.
6. Leaving the `pr-<N>` branch checked out or un-deleted.
