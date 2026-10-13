#!/usr/bin/env bash
# audit_baseline_diff.sh — prove a change introduced ZERO new rust-standards violations.
#
#   bash scripts/audit_baseline_diff.sh <repo> <changed-file> [changed-file...]
#
# Stashes the given files, runs the audit on clean HEAD (BEFORE), restores them,
# runs the audit again (AFTER), then diffs per-check hit counts — not just the
# total, because an equal total can hide one check gaining what another lost.
#
# Exit 0 = identical, safe to report "历史债,零新增".
# Exit 1 = drift; the differing checks are printed.
# Exit 2 = setup problem (missing repo, audit script, or a failed git op).
#
# Override the audit script with AUDIT_SCRIPT=<path>.
#
# NOTE: after this runs, the changed files are back but UNSTAGED (git stash pop
# drops them out of the index). Re-run `git add` before committing.

set -uo pipefail

REPO="${1:-}"
shift || true
FILES=("$@")

if [[ -z "$REPO" || ${#FILES[@]} -eq 0 ]]; then
  echo "usage: $0 <repo> <changed-file> [changed-file...]" >&2
  exit 2
fi
if ! git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1; then
  echo "not a git repo: $REPO" >&2
  exit 2
fi

AUDIT="${AUDIT_SCRIPT:-$HOME/.hermes/skills/rust-standards/scripts/audit_rust_standards.py}"
if [[ ! -f "$AUDIT" ]]; then
  AUDIT="$HOME/.agents/skills/rust-standards/scripts/audit_rust_standards.py"
fi
if [[ ! -f "$AUDIT" ]]; then
  echo "audit script not found; set AUDIT_SCRIPT=<path>" >&2
  exit 2
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

snapshot() { # $1 = output file
  python3 "$AUDIT" "$REPO" 2>&1 | grep -oE 'FAIL: [0-9]+\. .*' \
    | sed -E 's/FAIL: ([0-9]+)\. ([^:]+): ([0-9]+) hits.*/\1\t\2\t\3/' \
    > "$1"
}

git -C "$REPO" stash push -q -- "${FILES[@]}" || { echo "stash failed" >&2; exit 2; }
snapshot "$TMP/before"
git -C "$REPO" stash pop -q || {
  echo "stash pop FAILED — restore your work manually: git -C $REPO stash list" >&2
  exit 2
}
snapshot "$TMP/after"

before_total=$(awk -F'\t' '{s+=$3} END {print s+0}' "$TMP/before")
after_total=$(awk -F'\t' '{s+=$3} END {print s+0}' "$TMP/after")

echo "BEFORE total: $before_total"
echo "AFTER  total: $after_total"

if diff -u "$TMP/before" "$TMP/after" > "$TMP/diff.txt"; then
  echo "PER-CHECK DIFF: none — zero new violations"
  echo "report: 历史债,零新增 (pre-existing debt, zero new violations)"
  echo "remember: files are now UNSTAGED — re-run git add before committing"
  exit 0
fi

echo "PER-CHECK DIFF (check<TAB>title):"
grep -E '^[+-][0-9]' "$TMP/diff.txt" || cat "$TMP/diff.txt"
echo "report: this change DID alter violation counts — inspect the lines above"
exit 1