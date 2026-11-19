# euv-docs site build

Source of truth: `origin/master` of `euv-dev/euv`, read from the committed
tree (`docs/build.rs`, `docs/src/bin/docs/`, `docs/src/document_html/`,
`docs/src/document_language/`), not from a local branch.

## The multi-locale build

`euv-docs` is a multi-locale static site.

- `docs/build.rs` reads `docs/README.md` frontmatter: a `site:` block plus a
  `locales:` **sequence** of `[[locales]]` entries. Each entry declares
  `prefix` (URL prefix), `dir` (content directory under `docs/docs/`) and
  `label` (the human name in the language dropdown).
- `prefix`, `dir` and `label` are all **required**. The build refuses to
  guess a locale's content directory and fails loudly on an empty
  `locales:` list instead of emitting a one-page site — an empty list used to
  reach codegen, emit `locales: &[]`, and make the runtime router index
  `site.locales[0]` on an empty slice.
- `docs/src/bin/docs/` drives the CLI build (`euv build`) once per locale.
  The **default (root-prefix) bundle is built first** and writes
  `.deploy/locales.tsv`; the remaining locales are then built into
  `<out>/<dir>` from that manifest. A `--locale` argument pins one bundle and
  skips the loop.
- The environment variables `EUV_DOCS_SRC_DIR`, `EUV_DOCS_OUT_DIR` and
  `EUV_DOCS_LOCALE` select the content root, the output root and the pinned
  locale.

## Document language

The language of a served document is bound to the **locale label**, not to a
frontmatter `lang:` key — the frontmatter `lang:` key is not read by the
build at all.

- `document_language_for_label` (`docs/src/document_language/`) maps the four
  locale labels to BCP-47 tags: `简体中文` → `zh-CN`, `English` → `en-US`,
  `日本語` → `ja-JP`, `한국어` → `ko-KR`. An unknown label falls back to
  `en-US`.
- `build.rs` writes that tag to `.deploy/document-lang.txt`.
- `localize_document_output` (`docs/src/document_html/`) then reads the tag
  back and rewrites `<html lang="…">` in `index.html`, and copies the
  localized `index.html` to `404.html` so a static host serves the same
  language on an unknown path.
- `localize_document_html` replaces the language attribute without touching
  the other attributes: it survives a single-quoted value, a spaced `LANG =`
  attribute, an existing `lang`, and an attribute value containing `>`.

## Asset rebasing

Assets are hosted exactly once: only the root bundle copies `public/`, and a
non-default locale bundle references the root copies through rebased `../`
URLs.

- `rebase_asset_url` rebases a **relative** asset (`./img/a.png` →
  `../img/a.png`) and leaves everything else alone. It skips a value that is
  empty, starts with `../` or `/`, or carries an absolute scheme.
- The skip list is `http://`, `https://`, `data:` and `blob:`. `https://` was
  added to it in `0.36.2`: before that, an absolute `https://` badge was
  rewritten into a broken `../https://…` URL in every non-default bundle.
- Rebasing is applied once and is idempotent — `rebase_asset_url` applied
  twice yields the same result.

## The locale dropdown

The language switcher is the shared `euv_dropdown` component with the shared
`euv_dropdown_trigger` as its trigger; it is not a hand-rolled button.

- The trigger row is rendered inside `euv_dropdown`, and the row itself is
  rendered in its **own** `VirtualNode::create_dynamic` hook lifecycle
  (`docs/src/component/layout/view/fn.rs`). A document-level outside-press
  listener registered in the shell root lost its callbacks when the route
  re-rendered, which is why the shared dropdown's own dismissal is used.
- The trigger keeps the nav styling through the `class` attribute and the
  `语言` tooltip, both attached as attributes rather than as a nested
  element.
- The mobile drawer identifies itself as the owning sheet through
  `data-slot="sheet-content"`, so a portaled dropdown stays inside it.

## The runtime regression harness

`docs/scripts/validation/runtime.py` exercises the **public** docs WASM
entrypoint against a real headless Chrome, without changing browser
ownership or artifacts.

- It serves the built site on a local HTTP server, proxies
  `/api/page-artifacts` to a public catalog, and drives the locale menu and
  the route transitions through Playwright.
- It asserts the **measured** locale-menu geometry: a registered trigger, a
  measured panel inside the viewport, four pointer-reachable options, the
  trigger controlling the panel, and a trusted selection that closes the menu
  without reloading the document.
- It is a local harness, not a CI job: nothing in `.github/workflows/`
  invokes `docs/scripts/validation/runtime.py`. Run it yourself with
  `python3 docs/scripts/validation/runtime.py <dir> <output.json>`; it needs
  Playwright and a local Chrome.
