# CI, stale PRs and conflicts

## Diagnose the exact failed run

```bash
gh pr view <number> --repo <owner>/<repo> --json headRefOid,statusCheckRollup
gh run list --repo <owner>/<repo> --branch <branch> --limit 10
gh run view <run-id> --repo <owner>/<repo> --log-failed
```

Match run IDs to the current PR head and event before reading a job's verdict.
Fix the demonstrated cause and rerun applicable checks; a queued rerun is not a
passing run. Do not swallow failures, ignore a failing local bug or widen token
permissions merely to obtain green CI. Diagnose credential transport separately
from authorization; fork jobs intentionally lack many secrets.

## A rule changed while PRs were open

1. Enumerate open PRs with pagination and record each head SHA.
2. Create a new owned detached worktree for that exact SHA in scratch, run the
   real verifier, and record its status/output. Register cleanup before use.
3. Check whether the verifier actually scanned the intended files; permanent
   zero counts and excluded fixtures are not proof of compliance.
4. Compare each PR with the base to establish unique remaining work. A verifier
   failure alone does not authorize closing the PR or deleting its branch.
5. With user authorization, update or close superseded PRs with a reason.
   Verify every mutation, then remove the owned worktrees after confirming no
   unpreserved edits remain. Do not use forced removal on somebody else's work.

```bash
git worktree add --detach <new-owned-scratch-path> <exact-head-sha>
python3 <verifier> <new-owned-scratch-path>
git -C <new-owned-scratch-path> status --short
git worktree remove <new-owned-scratch-path>
gh api --paginate 'repos/<owner>/<repo>/branches?per_page=100' --jq '.[].name'
```

The branches endpoint lists all branches when `protected` is omitted; pagination
and explicit filters matter. Do not infer repository completeness from one page.
A cleanup is scoped to the specified repository and branch owners, not to every
fork or organization the account can see.

## Conflicts and superseded work

- Inspect the actual common ancestor and both versions. Newer modification time,
  a later header or a larger file does not decide which content is correct.
- Preserve distinct changes, merge overlapping behavior deliberately, and exercise
  any extracted scripts against their real helper imports.
- Never assume every base-side change wins or every removed file should stay
  removed. Ask only when ownership or intent cannot be resolved from evidence.
- Rebase/history rewriting needs authorization and a clean owned branch. Resolve
  conflicts, rerun checks, then use `--force-with-lease` bound to the known remote
  head if rewriting was authorized; never fall back to unconditional force.
- Re-read PR head/base and checks after any rewrite. A clean mergeability field
  is not a replacement for tests, user merge authorization or exact-head guarding.

Authoritative endpoint semantics: GitHub Docs, REST API endpoints for branches;
merge flags: GitHub CLI manual, `gh pr merge`. Check installed command help when
an option differs; never preserve a failed assumption as an unconditional rule.
