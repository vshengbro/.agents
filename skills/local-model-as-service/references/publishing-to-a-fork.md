# Publishing a wrapper to a fork of someone else's repo

The mechanics of contributing a service layer to a repo you do not own: what
to write, what the fork's PR flow looks like, and the API-layer failures that
cost a turn on a fresh fork.

## 1. Confirm the license, then fork

Forks require a permissive license. Check before forking, not after:

```bash
gh api repos/<upstream>/<repo> --jq '{license:.license.spdx_id,archived:.archived}'
# Apache-2.0 / MIT / BSD → fork is fine
```

```bash
gh repo fork <upstream>/<repo> --clone=false
gh api repos/<you>/<repo> --jq '{fork:.fork,parent:.parent.full_name}'
```

**A 404 on the fork immediately after creating it is propagation lag, not
failure.** Re-query after a second or two before concluding anything. Verify
`parent` is actually populated — a repo created with `gh repo create` is
independent, and `parent` is never set retroactively.

Clone with both remotes so the fork can be synced later:

```bash
gh repo clone <you>/<repo> <dir>
git -C <dir> remote add upstream git@github.com:<upstream>/<repo>.git
```

## 2. Write the code as a subpackage, not a loose script

A wrapper that lives beside the project as a standalone file gets ignored by
that project's maintainers and never enters its test suite. Match the host
project's own conventions — read two or three of its modules first and copy its
style, its dependency posture (a stdlib-only project must get a stdlib-only
wrapper), its module layout, and its docstring voice.

Register any new console script in the project's own entry-point table, and put
tests in the project's existing test directory so `pytest` picks them up with
no configuration change.

## 3. Inherited tests can fail on your hardware

Running the host project's full suite after your change will surface failures
that have nothing to do with you — a precision-sensitive assertion, a device
default, a timing assumption. **Establish the baseline before attributing
anything:**

```bash
git stash -u          # including untracked, so your new files vanish
pytest <failing-test> # still fails? pre-existing, not yours
git stash pop
```

Report it as an upstream issue with the control result attached. Do not fix it
in a wrapper PR — that mixes scopes and the maintainer will not want it.

Watch for the same trap in the other direction: a test may pass locally only
because you ran it without the CI's environment. Re-run with CI's exact env
vars before claiming a pass.

## 4. `gh pr create` and `gh pr merge` fail on a fresh fork

Symptom on a fork created minutes ago, with the branch provably pushed:

```
GraphQL: Head sha can't be blank, Base sha can't be blank,
No commits between main and feat/thing, Head ref must be a branch
GraphQL: Could not resolve to a PullRequest with the number of 1
```

The branch is fine. `gh api repos/<o>/<r>/branches` lists it,
`gh api repos/<o>/<r>/git/refs/heads` shows its SHA, and
`gh api repos/<o>/<r>/compare/<base>...<head>` returns `ahead_by: 1`. GitHub's
GraphQL layer has not indexed the new fork's refs while REST has. Do not
re-push, re-branch, or wait it out.

Use REST for both operations:

```python
import json, os, urllib.request, urllib.error

def call(path, payload=None, method="GET"):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{OWNER}/{REPO}{path}",
        data=None if payload is None else json.dumps(payload).encode(),
        method=method,
        headers={"Authorization": f"Bearer {os.environ['GH_TOKEN']}",
                 "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8", "replace"))

# open
_, pr = call("/pulls", {
    "title": "feat(scope): short subject",
    "head": "<branch>",          # unqualified — the branch is in this same repo
    "base": "main",
    "body": open("/tmp/pr-body.md").read(),
}, "POST")
print(pr["number"], pr["html_url"])

# merge
status, result = call(f"/pulls/{pr['number']}/merge", {
    "merge_method": "squash",
    "delete_branch_on_merge": True,   # works even if the repo default is off
}, "PUT")
print(status, result.get("merged"))
```

Passing `delete_branch_on_merge: true` in the merge payload does not depend on
the repo-level setting, which is what makes this preferable to the CLI flag when
that setting is off. Check the outcome rather than the exit status: read
`merged: true` back, then confirm the branch is gone from
`gh api repos/<o>/<r>/branches` and that the default branch's SHA actually moved.

After a squash merge, delete the local branch with `git branch -D`, not `-d` —
the squashed commits are not ancestors of the new tip, so `-d` refuses.

## 5. A fresh fork's CI does not run

GitHub disables Actions on newly created forks. Both of these return zero for
a branch you just pushed, which looks identical to "CI passed instantly":

```bash
gh api "repos/<o>/<r>/actions/runs?per_page=5" --jq .total_count     # 0
gh api "repos/<o>/<r>/commits/<sha>/check-suites" --jq .total_count  # 0
```

Neither absence is a pass. Read the workflow file, reproduce its steps locally
with its exact environment variables, and report that. Enabling Actions for the
fork is a manual settings-page click you cannot perform for the user.

## 6. Squash merge replaces the author with the account profile

A squash merge stamps the merged commit with the **account profile's** name and
email, discarding the branch commit's author. A commit that satisfies your
identity convention on the branch can land on the default branch under a
different name entirely.

Diagnose with three reads — profile, branch commit, merged commit — and if only
the merged one diverges, the cause is the profile, not your commit. Fixes are
account-level (edit the profile name, or use `--merge` instead of `--squash`),
so report it as the user's decision.

## 7. Verify the merged result, not the API response

A `merged: true` response means the call was accepted, not that the merge is
usable. Prove it from a clean checkout:

```bash
gh repo clone <you>/<repo> /tmp/verify -- --depth 1
cd /tmp/verify && pytest tests/<yours>.py -q && ruff check .
rm -rf /tmp/verify
```

This is the only check that catches a merge that dropped a file, resolved a
conflict badly, or landed without the entry point you registered.
