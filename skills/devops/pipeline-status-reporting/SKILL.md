---
name: pipeline-status-reporting
description: 'Use when reporting CI/pipeline status across repos.'
---

# Pipeline status reporting

How to answer "流水线怎么样了 / what do the pipelines say" for a user who owns
many repos. The failure this prevents is a status report assembled from
per-repo command invocations that were each correct and jointly misleading.

## Procedure

1. **Enumerate the repos from the API, never from a hardcoded list.** A
   hardcoded list is a snapshot: a repo created tomorrow is missing, and a
   repo renamed or deleted stays in it reporting 404 forever. Both failures
   look identical in the output, which is how a stale list goes unnoticed.
   Personal repos come from `/user/repos?per_page=100&affiliation=owner`;
   org repos from `/user/orgs` then `orgs/<org>/repos`.
2. **Fetch the latest workflow run per repo** and render one row each:
   repo, workflow, event, branch, short sha, status, conclusion, run URL.
3. **Filter to repos that have runs.** The account typically owns 100+ repos,
   most of them forks of upstream projects that never run CI. Those rows are
   pure noise. Keep an opt-in flag for the full list.
4. **Report ERROR as a row, not as an omission.** A silent gap in a status
   table reads as "fine", which is the one direction a report must never fail
   in. A repo the API cannot answer for gets a visible ERROR row.
5. **Before quoting a version, confirm it is not already published.** A
   version bump that CI already shipped is a duplicate, not a new release.
   Check the registry API, not the local manifest.

## Pitfalls

- **`/users/<account>/orgs` returns only public memberships.** The private
  orgs — the ones this report exists to cover — are missing, and the output
  still looks complete. Use `/user/orgs`, which needs `read:org`.
- **A successful API response is a dict; an error response is also a dict.**
  Testing `isinstance(response, dict)` to detect failure makes every
  successful call report as an error, which reads as "everything is broken"
  rather than "the check is wrong". Detect the error marker key.
- **A run's `source_sha` in a deploy artifact can refer to a *different*
  repo's commit than the one that shaped the build.** Workflows that
  `cargo install` a dependency from its default branch at build time produce
  different artifacts from an identical `source_sha`. Two runs with the same
  `source_sha` and different artifact sizes are not a contradiction. When
  debugging "the deploy didn't take", diff the artifact bytes across recent
  runs, not just the recorded sha.
- **A mirror/CDN serving the previous deploy can look like a failed deploy.**
  Compare served bytes against the artifact repo, and if they differ, check
  whether the served bytes match an *earlier* run. When they do, the deploy
  succeeded and the mirror is lagging. Re-trigger sync and poll; the lag
  window is minutes, not a failure.

## Re-verify PR state at the moment of reporting

A PR open when you pushed it may be **merged** by the time you report on it,
often by the user from another client. Symptoms: the API serves a stale
`headRefOid` while the branch ref already points at your commit, and
subsequent pushes land on a branch no PR tracks.

Before writing any status line about a PR, re-read the PR's `state` and
`merged_at` **after** the pushes, not from memory of the earlier step. If
work remains unmerged and the original PR is closed, branch the follow-up
from the **current default branch** and cherry-pick only the commits that
are not yet on it — the base branch has by then absorbed the earlier ones,
so a plain rebase produces conflicts on already-applied changes.

## Files

- `scripts/pipeline_digest.py` — enumerates owned repos, fetches the latest
  run for each, renders the aggregated table. `--repos` to override the set,
  `--include-quiet` to keep repos with no runs, `--format md|text`.
