# GitHub Pull Request Workflow

Complete guide for managing the PR lifecycle. Each section shows the `gh` way first, then the `git` + `curl` fallback for machines without `gh`.

## Prerequisites

- Authenticated with GitHub (see `github-auth` skill)
- Inside a git repository with a GitHub remote

### Quick Auth Detection

```bash
# Determine which method to use throughout this workflow
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  # Ensure we have a token for API calls
  if [ -z "$GITHUB_TOKEN" ]; then
    if _hermes_env="${HERMES_HOME:-$HOME/.hermes}/.env"; [ -f "$_hermes_env" ] && grep -q "^GITHUB_TOKEN=" "$_hermes_env"; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" "$_hermes_env" | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(uv run python "${HERMES_HOME:-$HOME/.hermes}/skills/github/github-auth/scripts/git-credential-token.py")
    fi
  fi
fi
echo "Using: $AUTH"
```

### When Auth Detection Yields Nothing

If `gh` is missing AND `GITHUB_TOKEN` is empty AND `~/.git-credentials` has no GitHub entry, both `gh` and `curl` paths are blocked for PR creation — SSH can still push, but the REST API needs a token. Do NOT pretend the PR is created. Instead:

1. Push the branch with SSH (works with a loaded `ssh-agent` key):
   ```bash
   git push -u origin HEAD
   ```
2. Read the "Create a pull request for `<branch>` on GitHub" hint GitHub prints on push — that URL has the `compare`/`expand=1` query params pre-filled.
3. Construct the canonical compare URL yourself if the hint is missing:
   ```bash
   BRANCH=$(git branch --show-current)
   OWNER=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||' | cut -d/ -f1)
   REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||' | cut -d/ -f2)
   echo "https://github.com/$OWNER/$REPO/compare/${DEFAULT_BRANCH:-master}...${BRANCH}?expand=1"
   ```
4. Open that URL via `browser_exec` or `agent-browser open`. If the user isn't signed in to GitHub in the browser session, the page will render the diff but the "Create pull request" button will be replaced with "Sign in" / "Sign up" — surface that in the reply so the user knows to authenticate before they can complete the PR.
5. If the user provides a `repo` scope token later (e.g. via env or paste), re-run the `gh pr create` or `curl` path from Section 3 to finish programmatically.

The wrong move: claim "PR is up" when only the branch was pushed. Reviewers will not see the branch in their PR queue, and the user will assume the PR was created.

### Extracting Owner/Repo from the Git Remote

Many `curl` commands need `owner/repo`. Extract it from the git remote:

```bash
# Works for both HTTPS and SSH remote URLs
REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
echo "Owner: $OWNER, Repo: $REPO"
```

---

## 1. Branch Creation

This part is pure `git` — identical either way:

```bash
# Make sure you're up to date
git fetch origin
git checkout main && git pull origin main

# Create and switch to a new branch
git checkout -b feat/add-user-authentication
```

Branch naming conventions:
- `feat/description` — new features
- `fix/description` — bug fixes
- `refactor/description` — code restructuring
- `docs/description` — documentation
- `ci/description` — CI/CD changes

## 2. Making Commits

Use the agent's file tools (`write_file`, `patch`) to make changes, then commit:

```bash
# Stage specific files
git add src/auth.py src/models/user.py tests/test_auth.py

# Commit with a conventional commit message
git commit -m "feat: add JWT-based user authentication

- Add login/register endpoints
- Add User model with password hashing
- Add auth middleware for protected routes
- Add unit tests for auth flow"
```

Commit message format (Conventional Commits):
```
type(scope): short description

Longer explanation if needed. Wrap at 72 characters.
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `ci`, `chore`, `perf`

## 3. Pushing and Creating a PR

### Push the Branch (same either way)

```bash
git push -u origin HEAD
```

**If the push is rejected with `non-fast-forward`** — origin has moved since
your last `fetch` (another agent or user pushed to the same base branch). Do
not force-push a branch you have not yet shared; rebase first:

```bash
git fetch origin
git rebase origin/${DEFAULT_BRANCH:-master}
# Resolve any conflicts, then:
git push -u origin HEAD
```

If the branch was already public (e.g. force-pushed once), use
`--force-with-lease` instead of `--force` so the push fails fast if a parallel
write landed during your rebase:

```bash
git push --force-with-lease origin HEAD
```

### Create the PR

**With gh:**

```bash
gh pr create \
  --title "feat: add JWT-based user authentication" \
  --body "## Summary
- Adds login and register API endpoints
- JWT token generation and validation

## Test Plan
- [ ] Unit tests pass

Closes #42"
```

Options: `--draft`, `--reviewer user1,user2`, `--label "enhancement"`, `--base develop`

**With git + curl:**

```bash
BRANCH=$(git branch --show-current)

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$OWNER/$REPO/pulls \
  -d "{
    \"title\": \"feat: add JWT-based user authentication\",
    \"body\": \"## Summary\nAdds login and register API endpoints.\n\nCloses #42\",
    \"head\": \"$BRANCH\",
    \"base\": \"main\"
  }"
```

The response JSON includes the PR `number` — save it for later commands.

To create as a draft, add `"draft": true` to the JSON body.

## 4. Monitoring CI Status

### Check CI Status

**With gh:**

```bash
# One-shot check
gh pr checks

# Watch until all checks finish (polls every 10s)
gh pr checks --watch
```

**With git + curl:**

```bash
# Get the latest commit SHA on the current branch
SHA=$(git rev-parse HEAD)

# Query the combined status
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status \
  | python -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Overall: {data['state']}\")
for s in data.get('statuses', []):
    print(f\"  {s['context']}: {s['state']} - {s.get('description', '')}\")"

# Also check GitHub Actions check runs (separate endpoint)
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/check-runs \
  | python -c "
import sys, json
data = json.load(sys.stdin)
for cr in data.get('check_runs', []):
    print(f\"  {cr['name']}: {cr['status']} / {cr['conclusion'] or 'pending'}\")"
```

### Poll Until Complete (git + curl)

```bash
# Simple polling loop — check every 30 seconds, up to 10 minutes
SHA=$(git rev-parse HEAD)
for i in $(seq 1 20); do
  STATUS=$(curl -s \
    -H "Authorization: token $GITHUB_TOKEN" \
    https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status \
    | python -c "import sys,json; print(json.load(sys.stdin)['state'])")
  echo "Check $i: $STATUS"
  if [ "$STATUS" = "success" ] || [ "$STATUS" = "failure" ] || [ "$STATUS" = "error" ]; then
    break
  fi
  sleep 30
done
```

### When You Have SSH but No Token (browser fallback)

If `gh` is missing and `GITHUB_TOKEN` is empty, the `gh` and `curl` paths above
are both blocked. The GitHub web UI is the fallback — it is publicly readable
for any public repo without auth. Drive it via `agent-browser`:

```bash
# All workflow runs for the repo (most recent first)
agent-browser open "https://github.com/$OWNER/$REPO/actions"
# Drill into one run to see job-by-job status + per-step logs
agent-browser open "https://github.com/$OWNER/$REPO/actions/runs/<RUN_ID>"
# PR-specific checks
agent-browser open "https://github.com/$OWNER/$REPO/pull/<PR_NUMBER>/checks"
```

To find the latest `RUN_ID` from the actions page, parse the rendered list:

```bash
agent-browser eval "
JSON.stringify(
  [...document.querySelectorAll('a[href*=\"/actions/runs/\"]')]
    .map(a => ({href: a.href, text: a.textContent.trim().slice(0, 40)}))
    .filter(a => a.href.includes('/actions/runs/') && !a.href.endsWith('/workflow'))
    .slice(0, 5)
)"
```

Then `agent-browser open <that-href>` for the detail page. Take a screenshot
with `agent-browser screenshot <path>` and use vision to read status icons,
elapsed time, and which step is currently in progress. This is read-only and
works without a GitHub login session; the only thing you cannot do without
login is **re-run** a workflow (use `workflow_dispatch` from the UI as a signed-
in user, or have the user re-push).

Limits: anonymous `api.github.com` calls are rate-limited (60/hr/IP). When
the browser path is the only one available, prefer it over `curl` to avoid
burning the token-less budget.

## 5. Auto-Fixing CI Failures

When CI fails, diagnose and fix. This loop works with either auth method.

### Step 1: Get Failure Details

**With gh:**

```bash
# List recent workflow runs on this branch
gh run list --branch $(git branch --show-current) --limit 5

# View failed logs
gh run view <RUN_ID> --log-failed
```

**With git + curl:**

```bash
BRANCH=$(git branch --show-current)

# List workflow runs on this branch
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/actions/runs?branch=$BRANCH&per_page=5" \
  | python -c "
import sys, json
runs = json.load(sys.stdin)['workflow_runs']
for r in runs:
    print(f\"Run {r['id']}: {r['name']} - {r['conclusion'] or r['status']}\")"

# Get failed job logs (download as zip, extract, read)
RUN_ID=<run_id>
curl -s -L \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/logs \
  -o ~/.hermes/cache/scratch/ci-logs.zip
cd ~/.hermes/cache/scratch && unzip -o ci-logs.zip -d ci-logs && cat ci-logs/*.txt
```

### Step 2: Fix and Push

After identifying the issue, use file tools (`patch`, `write_file`) to fix it:

```bash
git add <fixed_files>
git commit -m "fix: resolve CI failure in <check_name>"
git push
```

### Step 3: Verify

Re-check CI status using the commands from Section 4 above.

### Auto-Fix Loop Pattern

When asked to auto-fix CI, follow this loop:

1. Check CI status → identify failures
2. Read failure logs → understand the error
3. Use `read_file` + `patch`/`write_file` → fix the code
4. `git add . && git commit -m "fix: ..." && git push`
5. Wait for CI → re-check status
6. Repeat if still failing (up to 3 attempts, then ask the user)

## 6. Merging

**With gh:**

```bash
# Squash merge + delete branch (cleanest for feature branches)
gh pr merge --squash --delete-branch

# Enable auto-merge (merges when all checks pass)
gh pr merge --auto --squash --delete-branch
```

**With git + curl:**

```bash
PR_NUMBER=<number>

# Merge the PR via API (squash)
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/merge \
  -d "{
    \"merge_method\": \"squash\",
    \"commit_title\": \"feat: add user authentication (#$PR_NUMBER)\"
  }"

# Delete the remote branch after merge
BRANCH=$(git branch --show-current)
git push origin --delete $BRANCH

# Switch back to main locally
git checkout main && git pull origin main
git branch -d $BRANCH
```

Merge methods: `"merge"` (merge commit), `"squash"`, `"rebase"`

### Enable Auto-Merge (curl)

```bash
# Auto-merge requires the repo to have it enabled in settings.
# This uses the GraphQL API since REST doesn't support auto-merge.
PR_NODE_ID=$(curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER \
  | python -c "import sys,json; print(json.load(sys.stdin)['node_id'])")

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/graphql \
  -d "{\"query\": \"mutation { enablePullRequestAutoMerge(input: {pullRequestId: \\\"$PR_NODE_ID\\\", mergeMethod: SQUASH}) { clientMutationId } }\"}"
```

## 7. Complete Workflow Example

```bash
# 1. Start from clean main
git checkout main && git pull origin main

# 2. Branch
git checkout -b fix/login-redirect-bug

# 3. (Agent makes code changes with file tools)

# 4. Commit
git add src/auth/login.py tests/test_login.py
git commit -m "fix: correct redirect URL after login

Preserves the ?next= parameter instead of always redirecting to /dashboard."

# 5. Push
git push -u origin HEAD

# 6. Create PR (picks gh or curl based on what's available)
# ... (see Section 3)

# 7. Monitor CI (see Section 4)

# 8. Merge when green (see Section 6)
```

**When merging directly to a protected branch** (no PR) — e.g. fast-forward a
fix branch into local master and push — a parallel push to `origin/master`
between your `merge` and your `push origin master` will fail with
`non-fast-forward`. The fix is identical to a branch rebase: rebase local
master onto the new origin tip, then push. If the rebase introduces a commit
that breaks CI (e.g. another contributor's commit did not run `cargo fmt`),
amend the fmt fix INTO that offending commit rather than adding a "fix fmt"
commit on top — keep history bisectable.

## Useful PR Commands Reference

| Action | gh | git + curl |
|--------|-----|-----------|
| List my PRs | `gh pr list --author @me` | `curl -s -H "Authorization: token $GITHUB_TOKEN" "https://api.github.com/repos/$OWNER/$REPO/pulls?state=open"` |
| View PR diff | `gh pr diff` | `git diff main...HEAD` (local) or `curl -H "Accept: application/vnd.github.diff" ...` |
| Add comment | `gh pr comment N --body "..."` | `curl -X POST .../issues/N/comments -d '{"body":"..."}'` |
| Request review | `gh pr edit N --add-reviewer user` | `curl -X POST .../pulls/N/requested_reviewers -d '{"reviewers":["user"]}'` |
| Close PR | `gh pr close N` | `curl -X PATCH .../pulls/N -d '{"state":"closed"}'` |
| Check out someone's PR | `gh pr checkout N` | `git fetch origin pull/N/head:pr-N && git checkout pr-N` |

---

## Resolving "remote:branch" References the User Names

When the user says "use `eastspire:feat/monorepo`", "fetch `acme:main`", or any other `<remote>:<branch>` reference, the left side is almost always the GitHub *user or org that owns a fork* and the right side is the head branch of an open PR. Treat it as a PR-head reference, not a request to add a remote.

### Try the cross-fork `refs/pull/N/head` namespace first

Every PR — even ones from forks — is mirrored under the **base repo's** `refs/pull/N/head` ref. So `origin` (the base repo's remote) is enough to fetch the head, with no fork remote required:

```bash
# 1. Find the PR number whose head is the branch the user named.
gh pr list --state all --search "feat/monorepo" --json number,headRefName,headRepositoryOwner
# or, without gh:
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/pulls?state=all&head=$FORK_OWNER:$BRANCH" \
  | python -c "import sys,json; print(json.load(sys.stdin)[0]['number'])"

# 2. Fetch the head into a local branch from origin's pull namespace.
git fetch origin pull/$PR_NUMBER/head:$LOCAL_BRANCH
git checkout $LOCAL_BRANCH
```

`refs/pull/N/head` works for cross-fork PRs because GitHub keeps a server-side mirror on the base repo, so you don't need read access to the fork. This is the same mechanism `gh pr checkout N` uses internally.

### Sanity-check the SHAs match

If a fork-as-remote *does* exist (locally or because you `git ls-remote`'d it), the SHAs must agree before you trust the ref:

```bash
git ls-remote origin 'refs/pull/N/head'
git ls-remote <fork-remote> 'refs/heads/<branch>'
# both lines must print the same SHA
```

A mismatch means either the PR was force-pushed after opening, or you're looking at a stale ref. Re-fetch and re-check.

### When adding the fork as a remote *is* the right move

Skip it for read-only review; do it when:

- The user wants a **tracking remote** for the local branch (so `git pull` works without a refspec), or
- The user needs to **push back** to the fork (e.g. fixup commits for a PR they own), or
- The fork is private and the base repo's `refs/pull/N/head` mirror isn't visible.

```bash
# Only when actually needed:
git remote add <fork-name> git@github.com:<fork-owner>/<repo>.git
git fetch <fork-name> <branch>
git branch --set-upstream-to=<fork-name>/<branch> <local-branch>
```

Pitfall: do not add the fork as a remote by default. Every extra remote is another push target where secrets can leak and another remote-tracking branch the user has to remember. The `refs/pull/N/head` namespace covers read access for all but the private-fork case.

Pitfall: don't `git checkout --detach` or otherwise move HEAD on a branch the user is actively working on without confirming first. "Replace the local source" usually means "fetch and stage the new ref so I can switch when ready" — not "switch the working tree right now". Leave HEAD where it is and report the new branch name with the verified SHA.
