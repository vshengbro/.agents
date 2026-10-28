#!/usr/bin/env bash
# Sync the vendored "mcode-stack" skills from MiniMax-AI/mcode-stack.
#
# What it does
# ------------
#   1. Fetches https://github.com/MiniMax-AI/mcode-stack (default ref: main)
#      into a cache clone outside the repo.
#   2. Copies the selected stack's skill folders into
#      skills/mcode-stack/<skill-name>/ (upstream layout is flattened:
#      one directory per skill, so the skills stay discoverable one level
#      below the category directory).
#   3. Copies the stack-level assets the skills point at
#      (NOTICE.md, checklists/) to skills/mcode-stack/.
#   4. Rewrites the two path families that were relative to the upstream
#      stack root, so they resolve from the vendored layout:
#        ../../NOTICE.md   -> ../NOTICE.md
#        checklists/X.md   -> ../checklists/X.md
#   5. Writes skills/mcode-stack/UPSTREAM.md with the upstream commit and
#      the sync date.
#
# Usage
# -----
#   bash scripts/sync-mcode-stack.sh                 # sync from upstream main
#   bash scripts/sync-mcode-stack.sh --ref v1.2.3     # sync a tag/branch
#   bash scripts/sync-mcode-stack.sh --source-dir DIR # reuse an existing clone
#   bash scripts/sync-mcode-stack.sh --dry-run        # show what would change
#   bash scripts/sync-mcode-stack.sh --check          # verify vendored copy
#                                                        # matches upstream
#
# Exit codes
# ----------
#   0  synced / in sync / dry-run ok
#   1  drift detected (--check) or the sync failed
#   2  usage error

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UPSTREAM_REPO="https://github.com/MiniMax-AI/mcode-stack.git"
UPSTREAM_REF="main"
STACK="ronny"
SOURCE_DIR=""
DRY_RUN=0
CHECK=0
CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/agents-sync/mcode-stack"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --ref)        UPSTREAM_REF="${2:?--ref needs a value}"; shift 2 ;;
        --stack)      STACK="${2:?--stack needs a value}"; shift 2 ;;
        --source-dir) SOURCE_DIR="${2:?--source-dir needs a value}"; shift 2 ;;
        --dry-run)    DRY_RUN=1; shift ;;
        --check)      CHECK=1; shift ;;
        -h|--help)    sed -n '2,40p' "${BASH_SOURCE[0]}"; exit 0 ;;
        *) echo "ERROR: unknown argument: $1" >&2; exit 2 ;;
    esac
done

DEST_ROOT="$REPO_ROOT/skills/mcode-stack"
UPSTREAM_SKILLS_DIR="stacks/$STACK/skills"

if [[ -z "$SOURCE_DIR" ]]; then
    SOURCE_DIR="$CACHE_DIR"
    mkdir -p "$SOURCE_DIR"
    if [[ ! -d "$SOURCE_DIR/.git" ]]; then
        echo "→ Cloning $UPSTREAM_REPO into $SOURCE_DIR ..."
        git clone --quiet "$UPSTREAM_REPO" "$SOURCE_DIR"
    fi
    echo "→ Fetching $UPSTREAM_REF ..."
    git -C "$SOURCE_DIR" fetch --quiet --depth 1 origin "$UPSTREAM_REF"
    git -C "$SOURCE_DIR" checkout --quiet --force FETCH_HEAD
fi

if [[ ! -d "$SOURCE_DIR/$UPSTREAM_SKILLS_DIR" ]]; then
    echo "ERROR: $SOURCE_DIR/$UPSTREAM_SKILLS_DIR not found (wrong stack name?)" >&2
    exit 2
fi

COMMIT="$(git -C "$SOURCE_DIR" rev-parse HEAD 2>/dev/null || echo unknown)"

# ---------------------------------------------------------------- helpers ---

# Rewrite the two upstream-relative path families so they resolve from the
# vendored layout (skills/mcode-stack/<skill>/...).
rewrite_paths() {
    python3 - "$1" "$STACK" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
stack = sys.argv[2]
text = path.read_text(encoding="utf-8")
text = text.replace("](../../NOTICE.md)", "](../NOTICE.md)")
text = text.replace("`checklists/", "`../checklists/")
# NOTICE.md sits next to the vendored skill folders, so its "skills/" link
# has no local target any more; point it at the upstream stack instead.
text = text.replace(
    "](skills/)",
    f"](https://github.com/MiniMax-AI/mcode-stack/tree/main/stacks/{stack}/skills)")
path.write_text(text, encoding="utf-8")
PY
}

# The vendored copy is "upstream files + the two rewrites above". Compare
# against a freshly rewritten copy instead of raw upstream bytes.
compare_tree() {
    local upstream_dir="$1" dest_dir="$2" name="$3" tmp
    tmp="$(mktemp -d "${TMPDIR:-/tmp}/mcode-sync-XXXXXX")"
    trap 'rm -rf "$tmp"' RETURN
    if [[ -d "$upstream_dir" ]]; then
        cp -R "$upstream_dir/." "$tmp/"
    else
        cp "$upstream_dir" "$tmp/$(basename "$upstream_dir")"
    fi
    find "$tmp" -name '*.md' -print0 | while IFS= read -r -d '' f; do
        rewrite_paths "$f"
    done
    if ! diff -ru "$tmp" "$dest_dir" >/dev/null 2>&1; then
        echo "  ✗ $name differs from upstream"
        diff -ru "$tmp" "$dest_dir" | head -40 || true
        return 1
    fi
    return 0
}

# ------------------------------------------------------------------- main ---

if [[ $CHECK -eq 1 ]]; then
    echo "→ Checking vendored copy against upstream $COMMIT (stack: $STACK)"
    DRIFT=0
    for upstream_skill in "$SOURCE_DIR/$UPSTREAM_SKILLS_DIR"/*/; do
        name="$(basename "$upstream_skill")"
        dest="$DEST_ROOT/$name"
        if [[ ! -d "$dest" ]]; then
            echo "  ✗ missing: skills/mcode-stack/$name"
            DRIFT=1
            continue
        fi
        if ! compare_tree "$upstream_skill" "$dest" "$name"; then
            DRIFT=1
        fi
    done
    for dest in "$DEST_ROOT"/*/; do
        [[ -f "$dest/SKILL.md" ]] || continue   # not a skill dir (checklists/)
        name="$(basename "$dest")"
        if [[ ! -d "$SOURCE_DIR/$UPSTREAM_SKILLS_DIR/$name" ]]; then
            echo "  ✗ orphaned (not in upstream): skills/mcode-stack/$name"
            DRIFT=1
        fi
    done
    # stack-level assets
    for asset in NOTICE.md checklists; do
        src="$SOURCE_DIR/stacks/$STACK/$asset"
        [[ -e "$src" ]] || continue
        if ! compare_tree "$src" "$DEST_ROOT/$asset" "$asset"; then
            DRIFT=1
        fi
    done
    if [[ $DRIFT -ne 0 ]]; then
        echo "DRIFT: vendored copy is out of sync with upstream" >&2
        exit 1
    fi
    echo "OK: vendored copy matches upstream $COMMIT"
    exit 0
fi

echo "→ Syncing stack '$STACK' from upstream $COMMIT"
mkdir -p "$DEST_ROOT"

COPIED=0
for upstream_skill in "$SOURCE_DIR/$UPSTREAM_SKILLS_DIR"/*/; do
    name="$(basename "$upstream_skill")"
    dest="$DEST_ROOT/$name"
    if [[ $DRY_RUN -eq 1 ]]; then
        echo "  → would copy $name"
        COPIED=$((COPIED + 1))
        continue
    fi
    rm -rf "$dest"
    mkdir -p "$dest"
    cp -R "$upstream_skill/." "$dest/"
    find "$dest" -name '*.md' -print0 | while IFS= read -r -d '' f; do
        rewrite_paths "$f"
    done
    echo "  ✓ $name"
    COPIED=$((COPIED + 1))
done

# Stack-level assets the skills point at.
for asset in NOTICE.md checklists; do
    src="$SOURCE_DIR/stacks/$STACK/$asset"
    [[ -e "$src" ]] || continue
    if [[ $DRY_RUN -eq 1 ]]; then
        echo "  → would copy $asset"
        continue
    fi
    rm -rf "$DEST_ROOT/$asset"
    cp -R "$src" "$DEST_ROOT/$asset"
    find "$DEST_ROOT/$asset" -name '*.md' -print0 | while IFS= read -r -d '' f; do
        rewrite_paths "$f"
    done
    if [[ -f "$DEST_ROOT/$asset" ]]; then
        rewrite_paths "$DEST_ROOT/$asset"
    fi
    echo "  ✓ $asset"
done

# Drop skills that no longer exist upstream.
if [[ $DRY_RUN -eq 0 ]]; then
    for dest in "$DEST_ROOT"/*/; do
        [[ -f "$dest/SKILL.md" ]] || continue   # not a skill dir (checklists/)
        name="$(basename "$dest")"
        if [[ ! -d "$SOURCE_DIR/$UPSTREAM_SKILLS_DIR/$name" ]]; then
            rm -rf "$dest"
            echo "  ✗ removed $name (gone upstream)"
        fi
    done
fi

if [[ $DRY_RUN -eq 1 ]]; then
    echo "DRY-RUN: nothing written"
    exit 0
fi

cat > "$DEST_ROOT/UPSTREAM.md" <<EOF
# Upstream provenance

These skills are vendored from [MiniMax-AI/mcode-stack]($UPSTREAM_REPO),
stack \`$STACK\`.

- upstream commit: \`$COMMIT\`
- upstream ref: \`$UPSTREAM_REF\`
- last sync: $(date -u +%Y-%m-%d)

Refresh with:

\`\`\`shell
bash scripts/sync-mcode-stack.sh --ref $UPSTREAM_REF
bash scripts/sync-mcode-stack.sh --check
\`\`\`

Do not hand-edit the vendored skill folders: the next sync overwrites them.
EOF

# Record the vendored skills in .skill-lock.json with their upstream
# provenance, then let the reconciler refresh hashes/timestamps.
python3 "$REPO_ROOT/scripts/update_skill_lock.py" --preserve-prefix skills/rust-standards/ >/dev/null
python3 - "$REPO_ROOT/.skill-lock.json" "$COMMIT" "$UPSTREAM_REF" "$STACK" <<'PY'
import json
import sys
from pathlib import Path

lock_path = Path(sys.argv[1])
commit, ref, stack = sys.argv[2], sys.argv[3], sys.argv[4]
lock = json.loads(lock_path.read_text(encoding="utf-8"))
skills = lock.setdefault("skills", {})
for name, entry in skills.items():
    if not entry.get("skillPath", "").startswith("skills/mcode-stack/"):
        continue
    entry["source"] = "MiniMax-AI/mcode-stack"
    entry["sourceType"] = "github"
    entry["sourceUrl"] = "https://github.com/MiniMax-AI/mcode-stack.git"
    entry["ref"] = ref
    entry["subpath"] = f"stacks/{stack}/skills"
    entry["upstreamCommit"] = commit
lock_path.write_text(json.dumps(lock, indent=2, ensure_ascii=False) + "\n",
                     encoding="utf-8")
PY

echo
echo "──── sync summary ────"
echo "  upstream commit:  $COMMIT"
echo "  skills copied:   $COPIED"
echo "  destination:      skills/mcode-stack/"
