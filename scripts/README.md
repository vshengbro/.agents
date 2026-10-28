# scripts/

Utility scripts for maintaining this repository.

## `audit_skills.py` — offline structural audit of the skill library

Walks every real `skills/**/SKILL.md` (recursive, so category folders and nested
children are included) and checks structure only. It never touches the network,
never invokes an LLM, and never writes inside the repository.

Checks: frontmatter parses as a YAML mapping; `name` equals the folder; names are
globally unique; `description` is non-empty, ≤240 chars and not a keyword dump;
non-protected entries are within the line budget (default 160); fenced blocks
balance; relative links and heading anchors resolve (GitHub slug rules, Unicode +
percent-decoding, duplicate-heading `-1`/`-2` suffixes). External URLs, `mailto:`
and placeholder paths are excluded — placeholders are *reported* under `skipped`,
never silently dropped. Against `--baseline` it also diffs the protected subtree
by exact file set + sha256 (addition / deletion / modification), reports
before→after byte and line counts, and flags references left dangling by a
deleted skill.

It also runs the **history-debt checker** over the protected subtree
(`skills/rust-standards/scripts/verify_no_history_debt.py`): that skill must
state only the current rules, so a dated provenance marker, an iteration
label, a PR reference, a withdrawn-rule marker or a superseded-rule table
fails the audit. The checker ships with the skill it polices; a tree without
the protected skill skips the check instead of failing on its absence.

```shell
python3 scripts/audit_skills.py \
  --baseline /path/baseline.json \
  --protected-prefix skills/rust-standards/ \
  --json "$TMPDIR/audit.json"

# tighten or relax the entry budget
python3 scripts/audit_skills.py --max-entry-lines 120

# compare independently obtained intent selections with expected cases
python3 scripts/audit_skills.py --route-cases cases.json --route-results selections.json
```

Exit codes: `0` clean · `1` at least one failure · `2` usage/IO error.

`skills/rust-standards/` is protected by default — it is the frozen Rust
reference and stays long-form on purpose, so the entry-point budget does not
apply to it. `--protected-prefix` adds further prefixes on top. Without
`--baseline` there is no reference set to compare the protected tree against,
so the fingerprint check is skipped and reported as `not compared`; a
protected file is never reported as newly added in that case.

**Intent regression checks.** Cases contain `id`, `prompt`, and `expected`
(one primary skill name, or `null` when none applies). Give a reviewer only the
current descriptions and prompts, without the expected labels; capture their
`id`/`selected` records in a separate results file. The audit compares every ID
exactly once and fails on missing results, duplicate IDs, unknown skills or
mismatches. It does not invent a keyword router or claim live routing accuracy
(`route_checks.is_live_routing_measurement: false`). Fix ambiguous triggers and
repeat blind selection after edits; do not rewrite expected labels to pass.

### Preserving the frozen Rust subtree

For a run excluding `skills/rust-standards/`, `update_skill_lock.py` supports
`--preserve-prefix` to leave existing lock records under a prefix untouched
(no additions for missing protected entries), so an entry point a frozen file
links to cannot silently disappear from `.skill-lock.json`:

```shell
python3 scripts/update_skill_lock.py --preserve-prefix skills/rust-standards/
```

The prefix is component-bounded: `skills/rust-standards/` does **not** match
`skills/rust-standards-extra/`. `audit_skills.py` separately fails on
`protected_incoming.*` when a frozen file links into a mutable skill whose target
or anchor no longer exists.

## `test_update_skill_lock.py` — regression tests

Fixture-based tests for `update_skill_lock.py` and `audit_skills.py`. Each test
builds a throwaway tree under `~/.hermes/cache/scratch` (`TemporaryDirectory`), points
the module's `SKILLS_DIR`/`LOCK_PATH` at it via `importlib`, and restores
`sys.argv` afterwards — the real repository is never written to. Covers recursive
parent+child discovery, duplicate-name rejection, `--check`/`--diff` exit values,
byte-identical idempotence, provenance/top-level metadata retention, and
`--preserve-prefix` boundary + exact-entry preservation.

```shell
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_update_skill_lock.py
```

## `sync-references.sh` — sync skill `references/` from upstream docs-pages

Several skills (currently `euv/`, `hyperlane/`) vendor a curated subset of pages from the private [docs-pages](https://github.com/docs-pages/docs) repo. The pages live flat under `skills/<skill>/references/` so a tool can `read_file` them without going through the network.

When upstream docs-pages changes, run the sync script to refresh the vendored copies. The script:

1. Shallow-clones docs-pages (or reuses a clone via `--source-dir`).
2. For each line in `sync-references.mapping`, copies the source `.md` into the destination, strips VuePress-only frontmatter (`head`, `icon`, `order`, `dataset`, `index`, `keywords`), and prepends a normalized header with `synced_from` / `sync_method` / `sync_date` so it's clear where the content came from.
3. Re-points the page's relative links. Upstream is nested (`src/euv/macros/class.md`) while the vendored copies are flat (`skills/euv/references/class.md`), so an upstream link such as `../macros/css-vars.md` would otherwise point at a path that does not exist in the skill tree. A link to a page the mapping vendors becomes a sibling file name; a link to a page it does not vendor becomes that page's published URL on the docs site.
4. For lines tagged `# manual override:`, leaves the existing dest file alone (and warns if no dest exists yet).

### Usage

```shell
# Full sync — clones docs-pages into a temp dir, then exits
bash scripts/sync-references.sh

# Reuse an existing clone (faster, no network)
bash scripts/sync-references.sh --source-dir /path/to/docs-pages

# Preview what would change
bash scripts/sync-references.sh --dry-run

# Override the manual-override skips (NOT recommended — you'll lose local edits)
bash scripts/sync-references.sh --force
```

### Adding a new file

Append a line to `sync-references.mapping`:

```
skills/euv/references/foo.md<TAB>src/euv/usage-introduction/foo.md
```

(tab-separated; the third column is an optional note). Then re-run the script.

### Pinning a custom version of a file

If you need to hand-edit a vendored page (e.g. add a section that's not yet in upstream), append `# manual override:` to its mapping line. The script will then skip it on every run. The dest file will keep a `synced_from` header from the last successful sync so you can tell how stale it is.

### Repairing the links in already-vendored pages

Pages vendored before the script learned to re-point links still carry the
upstream paths. `relink-references.sh` runs the same rewriter over the
existing copies, driven by each file's `synced_from` header, so the result
matches what a fresh sync produces:

```shell
bash scripts/relink-references.sh
```

It reports `unchanged` for a page with nothing to fix and `rewritten` for one
it changed, and leaves hand-written pages (no `synced_from` header) alone.

### Verifying

```shell
# Show which files changed since HEAD, plus any drift/orphans
bash scripts/verify-references.sh

# Same, but also exit non-zero on drift
bash scripts/verify-references.sh --strict

# Compare against a different ref (e.g. main, or a tag)
bash scripts/verify-references.sh --against main
```

`verify-references.sh` will additionally check for **mapping drift** (source paths in the mapping that don't exist upstream anymore) if you point it at a clone via `DOCS_PAGES_DIR`:

```shell
DOCS_PAGES_DIR=/path/to/docs-pages bash scripts/verify-references.sh
```

## `sync-mcode-stack.sh` — vendor the MiniMax Code stack (`MiniMax-AI/mcode-stack`)

`skills/mcode-stack/` holds the `ronny` stack from
[MiniMax-AI/mcode-stack](https://github.com/MiniMax-AI/mcode-stack) — 15
engineering / agent-harness workflow skills, vendored verbatim.

The script fetches upstream, copies each skill folder to
`skills/mcode-stack/<skill-name>/`, copies the stack-level assets the skills
point at (`NOTICE.md`, `checklists/`), and rewrites the two path families
that were relative to the upstream stack root so they resolve from the
vendored layout:

| upstream | vendored |
| --- | --- |
| `../../NOTICE.md` | `../NOTICE.md` |
| `checklists/x.md` | `../checklists/x.md` |

It also refreshes `.skill-lock.json`: the vendored skills are recorded with
`source: MiniMax-AI/mcode-stack`, `ref`, `subpath` and `upstreamCommit`, so
the lock file always states which upstream revision is installed.

```shell
bash scripts/sync-mcode-stack.sh                 # sync from upstream main
bash scripts/sync-mcode-stack.sh --ref v1.2.3     # sync a tag/branch
bash scripts/sync-mcode-stack.sh --source-dir DIR # reuse an existing clone
bash scripts/sync-mcode-stack.sh --dry-run        # show what would change
bash scripts/sync-mcode-stack.sh --check          # verify vendored == upstream
```

`--check` compares the vendored tree against a freshly rewritten copy of
upstream and exits 1 on any drift — it is the "is the vendored copy still
current?" gate.

**Do not hand-edit `skills/mcode-stack/<skill>/`** — the next sync overwrites
it. Local edits belong in a separate skill.

Because the upstream text belongs to the upstream author, `audit_skills.py`
waives the description-length and keyword-dump budgets for this subtree
(`DEFAULT_VENDORED_PREFIXES` in `scripts/audit_skills.py`); every other check
— frontmatter shape, name/folder match, global name uniqueness, relative
links, line budget — still applies.

## `sync-minimax-skills.sh` — vendor the MiniMax skill library (`MiniMax-AI/skills`)

`skills/minimax-skills/` holds the skill library from
[MiniMax-AI/skills](https://github.com/MiniMax-AI/skills) — 16 skills
vendored verbatim, plus the upstream `LICENSE`, `LICENSES/` and `CREDITS.md`
for attribution.

The script fetches upstream, copies each folder under the upstream `skills/`
directory to `skills/minimax-skills/<skill-name>/`, and renames a folder when
the upstream frontmatter `name` differs from the upstream folder name (upstream
ships `minimax-multimodal-toolkit/` with the skill name `mmx-cli`), so the
folder always matches the skill name.

`android-native-dev` is **not** vendored: this library already carries a
curated, narrowed version of the same upstream skill under
`skills/android-native-dev/`, and skill names must be unique. The skip and
its reason are recorded in `skills/minimax-skills/UPSTREAM.md`.

```shell
bash scripts/sync-minimax-skills.sh                 # sync from upstream main
bash scripts/sync-minimax-skills.sh --ref v1.2.3     # sync a tag/branch
bash scripts/sync-minimax-skills.sh --source-dir DIR # reuse an existing clone
bash scripts/sync-minimax-skills.sh --dry-run        # show what would change
bash scripts/sync-minimax-skills.sh --check          # verify vendored == upstream
```

It also refreshes `.skill-lock.json`: the vendored skills are recorded with
`source: MiniMax-AI/skills`, `ref`, `subpath` and `upstreamCommit`.

`--check` compares every vendored skill against a freshly rewritten copy of
upstream and exits 1 on drift; it also flags vendored folders that no longer
exist upstream.

**Do not hand-edit `skills/minimax-skills/<skill>/`** — the next sync
overwrites it. Local edits belong in a separate skill.

Upstream text is not ours to rewrite, so `audit_skills.py` waives the
description budgets, the entry line budget and the relative-link / anchor
checks for this subtree; frontmatter shape, name/folder match and global
name uniqueness still apply.

## Why a custom script instead of git submodules / symlinks?

docs-pages is a **private** VuePress monorepo with hundreds of pages, nested subdirs, and VuePress-specific frontmatter. Submodules drag in the whole tree; symlinks break on Windows + confuse the `read_file` tool. A flat curated list under each skill:

- keeps the skill repo small and reviewable
- lets each skill pick exactly the pages it needs
- survives docs-pages' upstream restructuring (just update the mapping)
- makes the relationship explicit (the `synced_from` line in every synced file)
