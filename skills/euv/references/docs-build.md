# euv-docs site build

Source of truth: `origin/master` of `euv-dev/euv`, read from the committed
tree (`docs/build.rs`, `docs/src/bin/docs/`, `docs/src/document_html/`,
`docs/src/document_language/`, `docs/src/locale/`, `docs/src/component/layout/`),
not from a local branch.

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
- The frontmatter `lang:` key is **not read** by the build; it is dead data.
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
  back and rewrites the `lang` attribute of the document element in
  `index.html`, and copies the localized `index.html` to `404.html` so a static
  host serves the same language on an unknown path.
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

## Localized shell strings

The shell's user-facing strings live in the locale tables, not in the
components.

- `docs/src/locale/const.rs` holds four tables (`PW_GATE_MESSAGES_ZH`,
  `PW_GATE_MESSAGES_EN`, `PW_GATE_MESSAGES_JA`, `PW_GATE_MESSAGES_KO`), each
  now `[(&str, &str); 15]` — they were password-gate-only tables of 6 entries
  before, and now also carry the drawer, theme-toggle and search strings.
- The keys are `docs.drawer.open`, `docs.drawer.close`, `docs.drawer.title`,
  `docs.theme.toggle`, `docs.search.label`, `docs.search.empty`,
  `docs.search.none`, `docs.search.placeholder` and `docs.search.count`
  (the last one carries the `{count}` token `DOCS_SEARCH_COUNT_TOKEN`).
- `locale_text(route, key)` (`docs/src/locale/fn.rs`) resolves the active
  locale's table, then the English table, then falls back to the key itself.
- The hardcoded English constants `HEADER_SEARCH_LABEL`,
  `HEADER_SEARCH_EMPTY`, `HEADER_SEARCH_NONE`,
  `HEADER_SEARCH_PLACEHOLDER` and `THEME_TOGGLE_TITLE` were **deleted**; the
  search field's `aria-label`, `placeholder`, status announcement, the drawer's
  `aria-label`/`title` and the theme toggle's label now all come from
  `locale_text`.

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

## The mobile drawer modal

`docs/src/component/layout/drawer/` is the drawer's behaviour layer: it is not
a rendering component (no `html!`), it owns the modal contract that
`docs/src/component/layout/view/fn.rs` renders into.

- `use_docs_drawer_modal(drawer_open, locale_menu_open, mobile)` installs the
  listeners once (through `App::use_cleanup`) instead of on every reactive
  shell render.
- The drawer is a `role="dialog"` element with `aria-modal="true"`, an
  `aria-label` from `docs.drawer.title`, and a `tabindex="-1"`; the opener
  carries `aria-haspopup="dialog"`, `aria-controls` and `aria-expanded`. The
  background (`.c_mobile_header, .c_mobile_main`) gets the `inert` attribute
  while the drawer is open.
- Focus is **contained**: a capture-phase `focusin` handler pulls focus back
  to the drawer if it lands outside, and `Tab`/`Shift+Tab` wrap within the
  drawer's focusable controls.
- Focus is **restored** to the opener on close — but only if the opener is
  still the drawer trigger and still available.
- `Escape` closes a nested locale menu first (restoring focus to the locale
  trigger) and only then dismisses the drawer, which calls
  `Router::overlay_stack_close()` and clears the open signal.
- `use_docs_responsive_scope(context, mobile, owner)` unsubscribes and calls
  `HookContext::switch_arm(1)` when the responsive mode stops matching the
  owner, so switching desktop↔mobile tears down the other shell's native
  listeners instead of reusing them.
- An element counts as *available* only if it is connected, not inside
  `[hidden], [inert], [aria-hidden=true], [disabled]`, and neither zero-height
  nor `visibility: hidden|collapse`.

## The regression harnesses

Both harnesses drive a real headless Chrome through Playwright.

`docs/scripts/validation/runtime.py` exercises the **public** docs WASM
entrypoint without changing browser ownership or artifacts.

- It serves the built site on a local HTTP server, proxies
  `/api/page-artifacts` to a public catalog, and drives the locale menu and
  the route transitions.
- It asserts the **measured** locale-menu geometry: a registered trigger, a
  measured panel inside the viewport, four pointer-reachable options, the
  trigger controlling the panel, and a trusted selection that closes the menu
  without reloading the document.
- It also asserts no WASM runtime panics, no document reload across in-app
  navigation, back/forward history without a reload, and that the SHA-256 of
  every loaded `.wasm` equals the on-disk artifact.
- CLI: `python3 docs/scripts/validation/runtime.py <dir> <output.json>`.

`docs/scripts/validation/accessibility.py` (new) is the accessibility gate for
the shell, using the Chrome DevTools Protocol `Accessibility.getFullAXTree`
and **trusted** keyboard events (`isTrusted` must be true for every keydown).

- CLI: `accessibility.py <directory> <output.json>` with `--catalog-url`,
  `--chrome`, `--locales` (default `zh,en,ja,ko`) and `--widths` (default
  `1280,390`).
- It asserts localized search (`aria-label`, placeholder, the `aria-live=polite`
  + `aria-atomic=true` status, the empty and no-match announcements and the
  `{count}` announcement), the localized drawer and theme-toggle names, the
  dialog ARIA contract, focus containment (forward and reverse `Tab` stay
  inside the drawer), the `inert` background, focus restoration after
  `Escape`/`Enter`/pointer close/history close, the nested locale menu
  behaviour, and that a resize to desktop removes the drawer and the `inert`
  attributes.
- It is a **local harness**: nothing in `.github/workflows/` invokes
  `docs/scripts/validation/accessibility.py`. The CI-wired runtime harness is
  `example/scripts/validation/runtime.py` (the example app, not the docs
  site), which the `automation` job runs at `.github/workflows/rust.yml`.
