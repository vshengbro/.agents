# Skills deliberately not vendored

Each line is a skill name from the upstream `ronny` stack that is
intentionally **not** vendored into this tree. The sync script skips these
and the `--check` gate reports them as excluded rather than as drift, so a
removal the user asked for does not read as a broken vendored copy — and a
sync does not silently re-add what was removed on purpose.

One skill name per line. Lines starting with `#` are comments.

## Excluded

subagent-split-check
# Removed 2026-11-27: zero recorded uses across all 18 profile .usage.json
# trackers. Their subject matter is covered by the harness skills that are
# still vendored (harness-experiment, independent-review).
context-tax-audit
engineering-review-comments
long-session-check
tool-budget-audit
trajectory-review
# Removed 2026-11-28: bottom usage tier of the whole library (4-16 recorded
# uses, last activity 2026-11-18..11-20, nothing since). The vendored
# engineering-code-review (658), engineering-small-prs (54),
# engineering-review-feedback (72), harness-experiment (148, live) and
# independent-review (234) cover the same PR/change workflow.
engineering-emergency-changes
engineering-change-descriptions
long-command-check
handoff-doc
