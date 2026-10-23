# Choosing the delivery route: the repository decides, not the diff

The classifier routes by what the diff CONTAINS. The delivery route is a
property of the REPOSITORY, and it outranks the classifier's verdict: a repo
whose release path consumes the default branch directly has no use for a PR,
whatever the diff contains.

## Read the repo's own release topology before routing

```bash
git remote -v; git branch --show-current
git log --oneline --merges origin/<default> -10     # do merges ever land there?
git log --first-parent --oneline origin/<default> -10   # or direct commits?
```

Three facts settle it:

- **What the deploy path pulls.** If the release host or script runs
  `git pull --ff-only origin master`, then `master` IS the release path and a PR
  is a detour that lands one merge later. A private repo on a plan without
  branch protection has no enforcement either — `gh api repos/<owner>/<repo>/branches/<default>/protection`
  answers 403 with an upgrade message, which is the repository telling you
  protection is not available, not that the rule was skipped.
- **What the history looks like.** A default branch whose recent first-parent
  chain is direct commits, with no merge commits at all, is a repository whose
  convention is direct delivery. The classifier's `NEEDS_PR` is a default for
  repositories it has never seen.
- **Whether a reviewer exists.** A single-maintainer repository with no open
  PRs has no reviewer to route to; a PR there waits for nobody.

## When these say direct-push, direct-push

Say in the delivery text that the classifier said `NEEDS_PR` and why the
repository's topology decided otherwise, so the routing is reviewable rather
than silent. The rule being narrowed is the classifier's default, not a user
rule, and the concrete mismatch still has to be shown.

The reverse also holds: a repository that merges PRs, has a protected default
branch, or ships from a release branch gets a PR, and the fact that the change
is small is not a reason to skip it.
