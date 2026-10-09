#!/usr/bin/env bash
# Verify R14.7: tests/<sub>/fn.rs may contain ONLY `use super::*;` as a use.
# All other imports (wasm_bindgen_test, std::xxx, web_sys::xxx) must be
# re-exported by the parent tests/mod.rs via a plain `use` (§18 tests
# clause: pub-marked use is BANNED in tests/; plain use reaches
# descendants through the glob chain).
#
# Workspace-aware since 2026-10-02. The previous version globbed only
# "$REPO_ROOT"/tests/*/fn.rs, i.e. a test tree directly at the repository
# root. In a multi-crate workspace the test tree lives at <crate>/tests/,
# so the glob matched nothing: euv has 65 such files spread over engine/,
# cli/, core/, ui/ and macros/, and the script reported "OK: 0
# tests/<sub>/fn.rs files (R14.7 not applicable)" on a tree that still held
# `use euv_engine::*;` in engine/tests/renderer/fn.rs. A rule that scans
# zero files passes forever and looks identical to a clean tree, which is
# what made this one worth rewriting rather than trusting.
#
# Usage: bash verify_test_imports_centralized.sh <repo_root>
# Exit 0 if all test fn.rs files comply; non-zero with list of violations otherwise.

set -u

if [ $# -lt 1 ]; then
    echo "Usage: $0 <repo_root>"
    exit 2
fi

REPO_ROOT="$1"

if [ ! -d "$REPO_ROOT" ]; then
    echo "error: $REPO_ROOT is not a directory" >&2
    exit 2
fi

matches=()
while IFS= read -r -d '' f; do
    matches+=("$f")
done < <(find "$REPO_ROOT" \
    -path '*/target*' -prune -o \
    -path '*/.git' -prune -o \
    -type f -path '*/tests/*/fn.rs' -print0 2>/dev/null)

checked=${#matches[@]}
if [ "$checked" -eq 0 ]; then
    echo "OK: 0 tests/<sub>/fn.rs files (R14.7 not applicable)"
    exit 0
fi

violations=0

# `^[[:space:]]*use ` rather than `^use `: a function-local
# `use std::sync::LazyLock;` inside a `#[test]` body is the same rule --
# the import belongs at the top of the test tree -- and core/tests/vdom/fn.rs
# carried two of them until 2026-10-02, both invisible to a column-0 match.
# `grep -v -F 'use super::*;'` then strips the one allowed spelling, whether
# it is indented or not.
for f in "${matches[@]}"; do
    bad=$(grep -n '^[[:space:]]*use ' -- "$f" | grep -v -F 'use super::*;' || true)
    if [ -n "$bad" ]; then
        echo "VIOLATION: $f has non-super use lines:"
        echo "$bad" | sed 's/^/    /'
        violations=$((violations + 1))
    fi
done

if [ "$violations" -gt 0 ]; then
    echo ""
    echo "FAIL: ${violations} file(s) violate R14.7 (test fn.rs may only have use super::*;)"
    echo "Move those 'use' lines into tests/mod.rs as plain 'use std::xxx;' / 'use wasm_bindgen_test::wasm_bindgen_test;' etc. (pub use is BANNED in tests/, §18 tests clause)"
    exit 1
fi

echo "OK: $checked tests/<sub>/fn.rs file(s) all have only 'use super::*;' (R14.7)"
exit 0