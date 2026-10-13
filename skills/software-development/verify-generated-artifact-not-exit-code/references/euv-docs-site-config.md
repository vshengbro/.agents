# Site config contract — README.md frontmatter, not config.toml

Applies to euv-docs sites built from the `euv` workspace `docs` member (e.g.
`docs-pages/docs`). Its `locales:` block lives in the frontmatter of
`<SRC_DIR>/../README.md`, NOT in `docs/config.toml`. A tree whose README.md has a
`site:` block but no `locales:` sequence — or whose entries are malformed —
silently ships a site that PANICS IN THE BROWSER on first load.

## Failure signature

```
euv_docs.js:121 panicked at docs/src/router/fn.rs:79:21:
index out of bounds: the len is 0 but the index is 0
...
euv_docs_bg.wasm:0x238e2 Uncaught RuntimeError: unreachable
```

The `Unreachable` is the poisoned-instance echo of the same panic — one bug, two
console lines. `router/fn.rs` `locale_of()` ends in `.unwrap_or(&site.locales[0])`;
`len is 0` means the generated `SITE.locales` array is empty.

## Why an empty array ships at all

The parse chain in `build.rs`:

1. `parse_locale_config` returns `Option<LocaleConfig>`; a required field read with
   `?` (e.g. `dir: yaml_str(yaml, "dir")?`) yields `None` for a malformed entry.
2. `load_config_from_readme` collects with `.filter_map(parse_locale_config)` —
   every malformed entry is discarded, silently.
3. `resolve_locale_roots` iterates `config.locales`. If the list is EMPTY, its two
   loud guards ("declares dir X but is not a directory", "contains no .md files")
   never execute — correct, but unreachable on an empty input.
4. Codegen emits `locales: &[]` into `docs_gen.rs`; the runtime indexes `[0]`.

This is the concrete instance of the general silent-drop pattern described in
SKILL.md; the engine's own comments note that the old hardcoded-`zh` fallback was
removed precisely because it "produced a site with one page and no error at all".

## Required locale fields

`parse_locale_config` reads these with `?` — any missing one drops the entry:

- `prefix` — URL prefix, e.g. `/`, `/en/`, `/zh/`
- `dir` — content directory under `<SRC_DIR>`, e.g. `en`, `zh`
- `label` — dropdown label

Optional (defaulted later in codegen): `title`, `footer`, `toc_label`,
`prev_label`, `next_label`, `navbar`.

`dir` is the one people miss: it decouples content location from URL prefix, so a
locale may live in `en/` and serve at `/`, and vice-versa. There is NO
prefix-derived fallback and NO default — the engine deliberately refuses to guess.
Never reintroduce a fallback; add `dir` to the config instead.

## Route derivation (read before predicting URLs)

`route_for(segments, locale)`:
- `README.md` / `index.md` → directory route with trailing slash
- `foo.md` → `/foo.html`

`process_page` resolves the owning locale by matching the FIRST path component
against each locale's `dir`, then strips it and prefixes the locale's `prefix`.
A markdown file sitting directly under `<SRC_DIR>` (outside every locale dir)
matches no locale, falls back to `strip_path_prefix`, and gets `locale = "/"`.

**Consequence**: once `/` maps to a real `dir`, any stray root-level `.md` file
emits a route that collides with that locale's content (a root `README.md` and
`docs/zh/README.md` both want `/`). Audit before/after any locale remap:

```bash
git ls-files 'docs/*.md'      # anything here is outside every locale dir
```

To keep two URL families for one content dir, declare the dir twice with
different prefixes — `/` → `dir: zh` and `/zh/` → `dir: zh`. Valid, and it
intentionally emits the same routes twice (duplicate sidebar is the accepted
tradeoff). Treat it as a URL-compatibility decision, never a default.

## Verifying the generated site

The generated Rust lands in cargo's `OUT_DIR` as `docs_gen.rs`. Find the newest
copy rather than assuming a fixed path:

```bash
find "$(cargo metadata --format-version 1 --no-deps | python3 -c \
  'import json,sys; print(json.load(sys.stdin)["target_directory"])')" \
  -name docs_gen.rs -newer <your-config-file>
```

Then check the `locales: &[...]` array is non-empty, contains every prefix you
configured, and emits both `/x` and `/zh/x` if you chose the dual-family layout.
A green build is not evidence — the bug lives in the gap between "build succeeded"
and "generated array is non-empty".

## Browser check

Serve the output (`python3 -m http.server`) and load it. The regression guarded
against is a CONSOLE panic, so a 200 on `index.html` proves nothing — assert the
console is free of `index out of bounds` and `Uncaught RuntimeError: unreachable`.