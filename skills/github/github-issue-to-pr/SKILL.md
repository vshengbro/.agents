---
name: github-issue-to-pr
description: 'Use when taking a GitHub issue to a verified PR: validate the premise, sweep duplicates, prove the regression test bites, then shepherd CI honestly.'
license: MIT
---
# github-issue-to-pr

The end-to-end discipline for "fix issue #N and open a PR". It owns the
*process*; `github-issues` owns the issue mechanics and
`gh-pr-creation-workflow` owns the PR mechanics.

## 1. Read the live issue

`gh issue view <N> --comments` plus the repo's `AGENTS.md` / contributing docs.
Done when the currently requested behaviour, the non-goals and any unanswered
questions are known — the body alone is a snapshot from filing time.

## 2. Sweep for existing work

```bash
gh pr list --search "#<N>" --state all
gh pr list --search "<subsystem> <symptom>" --state open   # ≥2 keyword variants
git log --oneline -20 -- <relevant files>
```

Popular issues attract multiple independent fixes. Done when you know every
open PR and recent commit that touches this issue, or that none exist.

## 3. Validate the premise — and the design intent

Reproduce the bug (or demonstrate the missing behaviour) on the current
default branch with a failing test or fixture. Then check the second question:
is it a deliberate design? `git log -p -S "<symbol>"` on the code the issue
wants changed often shows the restriction *is* the feature. Challenge stale or
flawed issue prose instead of implementing it blindly.

## 4. Define acceptance and risk

Criteria, interfaces, migrations, compatibility, security/privacy, rollout,
rollback — each mapped to a test or an explicit verification step. Review needs
a finite contract.

## 5. Implement the smallest complete change, then fix the class

Regression test first, then the fix. Then search for the same bug shape at
sibling call sites and fix them **in this PR** — an incomplete fix that leaves
known siblings broken is worse than none. Every changed line traces to the
issue; no drive-by cleanup.

## 6. Prove the regression test bites

Temporarily restore the old behaviour of the exact function under test, run the
new test, confirm it **FAILS**, then restore the fix and confirm it passes. A
regression test that passes with and without the fix proves nothing.

## 7. Run the repo gates, then open the PR immediately

Formatter, lint, typecheck, canonical test entrypoint. Then push and open the
PR right away — the PR is what dispatches CI, and CI latency is the long pole.
Read it back: head SHA, base, title, files.

## 8. Shepherd CI honestly, then close the loop

`gh pr checks` / `gh run view --log-failed`. Separate failures your diff
introduced from pre-existing or infrastructure failures — reproduce on the
default branch when unsure, rerun once only for genuine flakes. Never say
"green", "merged" or "released" without live evidence of that exact state. When
it lands, comment on the issue with the PR link so the reporter has a traceable
resolution.

## Pitfalls

- Coding before reading the comments, sweeping duplicates, or reading current code.
- "Fixing" behaviour the original commit shows is intentional.
- Fixing one call site while sibling sites keep the same bug.
- Shipping a regression test that also passes without the fix.
- Opening a PR with unrun tests or unrelated formatting churn.
- Claiming the issue is delivered because a PR exists.

## Verification

- [ ] Full issue thread read; newest state reflected in the plan.
- [ ] Duplicate sweep run (issue number + ≥2 keyword variants).
- [ ] Premise reproduced on current code; design intent checked via history.
- [ ] Regression test proven to fail without the fix.
- [ ] Sibling call sites fixed or explicitly ruled out.
- [ ] Every changed line traces to the issue.
- [ ] CI state from live evidence only; issue commented with the PR link.
