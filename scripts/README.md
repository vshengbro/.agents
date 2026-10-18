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
3. For lines tagged `# manual override:`, leaves the existing dest file alone (and warns if no dest exists yet).

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

## Why a custom script instead of git submodules / symlinks?

docs-pages is a **private** VuePress monorepo with hundreds of pages, nested subdirs, and VuePress-specific frontmatter. Submodules drag in the whole tree; symlinks break on Windows + confuse the `read_file` tool. A flat curated list under each skill:

- keeps the skill repo small and reviewable
- lets each skill pick exactly the pages it needs
- survives docs-pages' upstream restructuring (just update the mapping)
- makes the relationship explicit (the `synced_from` line in every synced file)
