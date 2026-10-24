#!/usr/bin/env bash
# Repair the links in already-vendored reference pages.
#
# The vendored copies were synced before the sync script learned to re-point
# upstream-relative links, so they still carry the upstream paths. This runs
# the same rewriter the sync script uses, driven by each file's
# `synced_from` header, so the result matches what a fresh sync produces.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

MAPPING="$SCRIPT_DIR/sync-references.mapping"
SITE_BASE="${DOCS_SITE_BASE:-https://ltpp.vip}"

changed=0
while IFS= read -r file; do
    src_rel="$(sed -n 's|^synced_from: docs-pages/\(.*\)@.*$|\1|p' "$file" | head -1)"
    if [[ -z "$src_rel" ]]; then
        echo "  ⤼ SKIP (no synced_from): $file" >&2
        continue
    fi
    tmp="$(mktemp "${TMPDIR:-/tmp}/relink-XXXXXX")"
    python3 "$SCRIPT_DIR/rewrite_reference_links.py" \
        --mapping "$MAPPING" --source "$src_rel" --dest "$file" \
        --site-base "$SITE_BASE" < "$file" > "$tmp"
    if cmp -s "$tmp" "$file"; then
        rm -f "$tmp"
        echo "  = unchanged: $file"
    else
        mv "$tmp" "$file"
        echo "  ✓ rewritten: $file"
        changed=$((changed + 1))
    fi
done < <(git ls-files 'skills/*/references/*.md')

echo
echo "  rewritten: $changed"
