---
name: git-standards
description: "Use when validating Git commit text, personal author identity, hook compliance, or whether a change needs a PR. PR creation and merging use gh-pr-creation-workflow."
license: MIT
---

# Git standards

## 1. Commit and PR text

- All commit subjects/bodies and PR titles/bodies are English, including quoted material.
- Conventional Commit: `<type>(<scope>): <subject>`; subject <=72 characters,
  imperative, lowercase after the prefix, no trailing period or WIP label.
- Types: `feat`, `fix`, `refactor`, `perf`, `docs`, `test`, `build`, `ci`, `chore`, `style`, `revert`.
- Scope names the skill or area, not a file path. Explain what and why in a body
  wrapped at 72 columns; reference issues when relevant.
- PR body sections: `Summary`, `Changes`, `Verification`, `Notes`; use actual
  commands/results, not claimed tests. Chat replies stay in the user's language.

```bash
python3 ~/.agents/skills/git-standards/scripts/verify_english_only.py commit "$HOME/.hermes/cache/scratch/msg.txt" --repo .
python3 ~/.agents/skills/git-standards/scripts/verify_english_only.py pr "<title>" --body "$HOME/.hermes/cache/scratch/pr-body.md"
```

## 2. Choose delivery before branching

**`.agents` always commits and pushes directly to `master`, including scripts.
Do not create a branch, fork or PR for this repository.** This permanent repo
rule overrides the generic classifier result.

For other repositories, obey the user's explicit delivery instruction; otherwise:

```bash
python3 ~/.agents/skills/git-standards/scripts/classify_change.py --staged --json
```

Exit `0` = DIRECT_PUSH, `1` = NEEDS_PR, `2` = classification error: stop and diagnose.
Documentation, config, comments and presentation-only changes ordinarily direct-push;
executable changes and mixed diffs need a PR. Run the classifier rather than infer
from file extensions; host-language style blocks have their own tested rules.
Use [`gh-pr-creation-workflow`](../gh-pr-creation-workflow/SKILL.md) for the PR lifecycle.
If a classifier conflicts with a user rule, show the concrete mismatch; never
silently narrow the rule or bypass a gate. Explicit authorized exceptions must
be recorded in the delivery text.

## 3. Commit only the reviewed scope

1. Read branch, remotes, default branch, status, staged diff and local-ahead commits.
   A dirty shared tree is not permission to stage all of it.
2. Run the applicable project checks and the English-text verifier before committing.
   `route_gate.py --repo .` is a separate routing check; it is not automatically
   wired into the installed hooks. Do not claim otherwise.
3. Stage explicit paths or reviewed hunks, then verify the exact cached path set
   and full payload. Preserve unrelated modified/untracked files.
4. Commit with the global personal identity. Fetch before pushing; inspect
   divergence instead of resetting, discarding work, force-pushing or silently
   rebasing other people's commits.
5. Push only the authorized branch/commits; read the remote ref back and compare
   its SHA and delivered blobs. A successful command alone is not delivery proof.

```bash
git status --short
git diff --cached --check
git diff --cached --stat
git config --global user.name
git config --global user.email
git add -- <reviewed-paths>
git commit -F "$HOME/.hermes/cache/scratch/msg.txt"
git log -1 --format='%an <%ae>'
```

Global author config is the source of truth; do not hardcode a remembered identity
or use per-commit `-c user.*` / `GIT_AUTHOR_*` overrides. If unset, ask the user.
The live GitHub login (`gh api user --jq .login`) is a separate identity.

## 4. Hooks are mandatory

- Never use `--no-verify` or another bypass. Fix the failing check; expose genuine
  blockers instead of hiding them with ignored errors or unconditional success.
- Resolve `git config --get core.hooksPath` and read the actual installed hooks.
  A matching file in a different directory is not evidence a gate runs.
- `guard_no_verify.py --repo .` resolves ownership live; a lookup/API failure is
  not an exemption. Do not hardcode usernames or organization lists.
- Before changing a gate, prove both a compliant and violating fixture. Register
  it in every actual caller required by the governing rule, and test that caller.

## 5. Minimize CI runs: complete the work locally first

Every push to a repository with GitHub Actions consumes paid runner minutes, so
the number of commits and pushes is a cost decision, not a style preference.

- Detect CI before committing: if the repo has `.github/workflows/**`, treat the
  push as billable. Confirm with `ls .github/workflows`.
- Finish the entire change locally first — implementation, refactor, tests,
  formatting, lints — and run the same checks CI runs (build, test, fmt,
  clippy, audit) until they are all green locally.
- Only then commit and push. Do not push intermediate, WIP, "fix CI" or
  one-file-at-a-time commits that each trigger a workflow run.
- If CI fails on the pushed commit, fix locally, verify locally, then push
  again — do not push blind fixes to test the runner.
- Prefer one coherent commit per completed unit of work (or one squashed
  commit for a branch) over a chain of small commits.
- Local verification must actually cover what CI runs. If a CI job cannot be
  reproduced locally (e.g. a release/publish job, a matrix on another
  platform), say so explicitly and let the user decide whether to push.
- A commit is not "done" until its CI run is green; but the push that starts
  CI must be preceded by local green.

## 6. Verify policy helpers

```bash
PYTHONDONTWRITEBYTECODE=1 python3 ~/.agents/skills/git-standards/scripts/classify_change.py --self-test
PYTHONDONTWRITEBYTECODE=1 python3 ~/.agents/skills/git-standards/scripts/style_blocks_test.py
```

Keep temporary messages and probes in scratch, never inside `.agents`; remove
owned temporary processes/resources and verify cleanup before reporting done.
Do not change another profile's skills, plugins, cron jobs or memories.
