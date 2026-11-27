#!/usr/bin/env bash
# Sync the vendored "minimax-skills" set from MiniMax-AI/skills.
#
# What it does
# ------------
#   1. Fetches https://github.com/MiniMax-AI/skills (default ref: main)
#      into a cache clone outside the repo.
#   2. Copies every skill folder under upstream skills/ into
#      skills/minimax-skills/<skill-name>/.
#   3. Renames a folder whose upstream frontmatter `name` differs from the
#      upstream folder name, so the folder always matches the skill name
#      (upstream ships minimax-multimodal-toolkit/ with name `mmx-cli`).
#   4. Skips the skills listed in SKIP_SKILLS, with the reason recorded in
#      skills/minimax-skills/UPSTREAM.md.
#   5. Copies the upstream LICENSE, LICENSES/ and CREDITS.md next to the
#      vendored skills for attribution.
#   6. Writes skills/minimax-skills/UPSTREAM.md with the upstream commit,
#      the sync date and the skip list.
#   7. Records each vendored skill in .skill-lock.json with its upstream
#      provenance (source, ref, subpath, upstreamCommit).
#
# Usage
# -----
#   bash scripts/sync-minimax-skills.sh                 # sync from upstream main
#   bash scripts/sync-minimax-skills.sh --ref v1.2.3     # sync a tag/branch
#   bash scripts/sync-minimax-skills.sh --source-dir DIR # reuse an existing clone
#   bash scripts/sync-minimax-skills.sh --dry-run        # show what would change
#   bash scripts/sync-minimax-skills.sh --check          # verify vendored copy
#                                                        # matches upstream
#
# Exit codes
# ----------
#   0  synced / in sync / dry-run ok
#   1  drift detected (--check) or the sync failed
#   2  usage error

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UPSTREAM_REPO="https://github.com/MiniMax-AI/skills.git"
UPSTREAM_REF="main"
SOURCE_DIR=""
DRY_RUN=0
CHECK=0
CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/agents-sync/minimax-skills"

# Upstream skills that are not vendored, and why.
#
# android-native-dev: this library already carries a curated, narrowed
#   version of the same upstream skill (skills/android-native-dev/, with
#   one extra local reference). Two skills may not share a name, so the
#   upstream copy is not vendored.
# Skills dropped from the vendored set on 2026-11-27 after a cross-profile
# usage audit (18 .usage.json files) showed zero recorded uses; the local
# copies were removed. android-native-dev is skipped because the local
# skills/android-native-dev/ already provides it.
SKIP_SKILLS="android-native-dev buddy-sings flutter-dev fullstack-dev gif-sticker-maker minimax-docx minimax-music-gen minimax-music-playlist minimax-pdf minimax-xlsx mmx-cli pptx-generator react-native-dev shader-dev"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --ref)        UPSTREAM_REF="${2:?--ref needs a value}"; shift 2 ;;
        --source-dir) SOURCE_DIR="${2:?--source-dir needs a value}"; shift 2 ;;
        --dry-run)    DRY_RUN=1; shift ;;
        --check)      CHECK=1; shift ;;
        -h|--help)    sed -n '2,38p' "${BASH_SOURCE[0]}"; exit 0 ;;
        *) echo "ERROR: unknown argument: $1" >&2; exit 2 ;;
    esac
done

DEST_ROOT="$REPO_ROOT/skills/minimax-skills"
UPSTREAM_SKILLS_DIR="skills"

# --- fetch ------------------------------------------------------------------

if [[ -n "$SOURCE_DIR" ]]; then
    SOURCE_DIR="$(cd "$SOURCE_DIR" && pwd)"
    echo "→ Using local clone: $SOURCE_DIR"
else
    mkdir -p "$CACHE_DIR"
    echo "→ Fetching $UPSTREAM_REPO ($UPSTREAM_REF)"
    if ! git -C "$CACHE_DIR" rev-parse --git-dir >/dev/null 2>&1; then
        git clone --quiet "$UPSTREAM_REPO" "$CACHE_DIR"
    fi
    git -C "$CACHE_DIR" fetch --quiet --depth 1 origin "$UPSTREAM_REF"
    git -C "$CACHE_DIR" checkout --quiet --detach "FETCH_HEAD"
    SOURCE_DIR="$CACHE_DIR"
fi

COMMIT="$(git -C "$SOURCE_DIR" rev-parse HEAD)"
[[ -d "$SOURCE_DIR/$UPSTREAM_SKILLS_DIR" ]] || {
    echo "ERROR: $SOURCE_DIR has no $UPSTREAM_SKILLS_DIR/ directory" >&2
    exit 1
}

# --- helpers ----------------------------------------------------------------

# The skill name declared in a SKILL.md frontmatter, or the folder name.
skill_name_of() {
    python3 - "$1" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1]) / "SKILL.md"
text = path.read_text(encoding="utf-8", errors="replace")
if not text.startswith("---"):
    print(path.parent.name)
    raise SystemExit(0)
end = text.find("\n---", 3)
raw = text[3:end if end != -1 else len(text)]
try:
    import yaml
    data = yaml.safe_load(raw) or {}
except Exception:
    data = {}
name = data.get("name")
print(name if isinstance(name, str) and name.strip() else path.parent.name)
PY
}

# Compare a vendored folder against the upstream one (file list + content).
compare_tree() {
    local upstream_dir="$1" dest_dir="$2" name="$3" tmp
    tmp="$(mktemp -d "${TMPDIR:-/tmp}/minimax-sync-XXXXXX")"
    trap 'rm -rf "$tmp"' RETURN
    cp -R "$upstream_dir/." "$tmp/"
    if ! diff -ru "$tmp" "$dest_dir" >/dev/null 2>&1; then
        echo "  ✗ $name differs from upstream"
        diff -ru "$tmp" "$dest_dir" | head -40 || true
        return 1
    fi
    return 0
}

# --- dry run ----------------------------------------------------------------

if [[ $DRY_RUN -eq 1 ]]; then
    echo "→ Would sync $COMMIT into skills/minimax-skills/"
    for src in "$SOURCE_DIR/$UPSTREAM_SKILLS_DIR"/*/; do
        [[ -f "$src/SKILL.md" ]] || continue
        upstream_folder="$(basename "$src")"
        name="$(skill_name_of "$src")"
        if [[ " $SKIP_SKILLS " == *" $upstream_folder "* ]]; then
            echo "  – $upstream_folder (skipped)"
            continue
        fi
        echo "  ✓ $upstream_folder -> $name"
    done
    exit 0
fi

# --- check ------------------------------------------------------------------

if [[ $CHECK -eq 1 ]]; then
    echo "→ Checking vendored copy against upstream $COMMIT"
    DRIFT=0
    for src in "$SOURCE_DIR/$UPSTREAM_SKILLS_DIR"/*/; do
        [[ -f "$src/SKILL.md" ]] || continue
        upstream_folder="$(basename "$src")"
        [[ " $SKIP_SKILLS " == *" $upstream_folder "* ]] && continue
        name="$(skill_name_of "$src")"
        if [[ ! -d "$DEST_ROOT/$name" ]]; then
            echo "  ✗ missing: skills/minimax-skills/$name"
            DRIFT=1
            continue
        fi
        compare_tree "$src" "$DEST_ROOT/$name" "$name" || DRIFT=1
    done
    for dest in "$DEST_ROOT"/*/; do
        [[ -d "$dest" ]] || continue
        [[ -f "$dest/SKILL.md" ]] || continue   # license/asset folders
        name="$(basename "$dest")"
        found=0
        for src in "$SOURCE_DIR/$UPSTREAM_SKILLS_DIR"/*/; do
            [[ -f "$src/SKILL.md" ]] || continue
            [[ "$(skill_name_of "$src")" == "$name" ]] && found=1 && break
        done
        if [[ $found -eq 0 ]]; then
            echo "  ✗ orphaned (not in upstream): skills/minimax-skills/$name"
            DRIFT=1
        fi
    done
    if [[ $DRIFT -eq 0 ]]; then
        echo "OK: vendored copy matches upstream $COMMIT"
        exit 0
    fi
    echo "DRIFT: vendored copy is out of sync with upstream"
    exit 1
fi

# --- sync -------------------------------------------------------------------

echo "→ Syncing $COMMIT into skills/minimax-skills/"
rm -rf "$DEST_ROOT"
mkdir -p "$DEST_ROOT"

for src in "$SOURCE_DIR/$UPSTREAM_SKILLS_DIR"/*/; do
    [[ -f "$src/SKILL.md" ]] || continue
    upstream_folder="$(basename "$src")"
    if [[ " $SKIP_SKILLS " == *" $upstream_folder "* ]]; then
        echo "  – $upstream_folder (skipped)"
        continue
    fi
    name="$(skill_name_of "$src")"
    cp -R "$src" "$DEST_ROOT/$name"
    echo "  ✓ $upstream_folder -> $name"
done

# Attribution files.
for asset in LICENSE CREDITS.md LICENSES; do
    [[ -e "$SOURCE_DIR/$asset" ]] || continue
    rm -rf "$DEST_ROOT/$asset"
    cp -R "$SOURCE_DIR/$asset" "$DEST_ROOT/$asset"
    echo "  ✓ $asset"
done

# Provenance.
cat > "$DEST_ROOT/UPSTREAM.md" <<EOF
# Upstream provenance

These skills are vendored from [MiniMax-AI/skills]($UPSTREAM_REPO),
directory \`$UPSTREAM_SKILLS_DIR/\`.

- upstream commit: \`$COMMIT\`
- upstream ref: \`$UPSTREAM_REF\`
- last sync: $(date -u +%Y-%m-%d)

Refresh with:

\`\`\`shell
bash scripts/sync-minimax-skills.sh --ref $UPSTREAM_REF
bash scripts/sync-minimax-skills.sh --check
\`\`\`

Do not hand-edit the vendored skill folders: the next sync overwrites them.
Local edits belong in a separate skill.

## Not vendored

- \`android-native-dev\` — this library already carries a curated, narrowed
  version of the same upstream skill under \`skills/android-native-dev/\`.
  Skill names must be unique across the library, so the upstream copy is
  skipped here.

## Licensing

The upstream repository is MIT licensed; its \`LICENSE\`, \`LICENSES/\` and
\`CREDITS.md\` are vendored alongside the skills. Some upstream skills
derive from Apache-2.0 licensed sources credited in \`CREDITS.md\`.
EOF

# Lock file: record the vendored skills with their upstream provenance.
python3 "$REPO_ROOT/scripts/update_skill_lock.py" --preserve-prefix skills/rust-standards/ >/dev/null
python3 - "$REPO_ROOT/.skill-lock.json" "$COMMIT" "$UPSTREAM_REF" <<'PY'
import json
import sys
from pathlib import Path

lock_path = Path(sys.argv[1])
commit, ref = sys.argv[2], sys.argv[3]
lock = json.loads(lock_path.read_text(encoding="utf-8"))
for entry in lock.get("skills", {}).values():
    if not entry.get("skillPath", "").startswith("skills/minimax-skills/"):
        continue
    entry["source"] = "MiniMax-AI/skills"
    entry["sourceType"] = "github"
    entry["sourceUrl"] = "https://github.com/MiniMax-AI/skills.git"
    entry["ref"] = ref
    entry["subpath"] = "skills"
    entry["upstreamCommit"] = commit
lock_path.write_text(json.dumps(lock, indent=2, ensure_ascii=False) + "\n",
                     encoding="utf-8")
PY

echo "✓ synced $COMMIT"
