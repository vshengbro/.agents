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
  now `[(&str, &str); 21]` — they were password-gate-only tables of 6 entries
  before, and now also carry the drawer, theme-toggle, locale-title, search and
  catalog strings.
- The keys are `docs.drawer.open`, `docs.drawer.close`, `docs.drawer.title`,
  `docs.theme.toggle`, `docs.locale.title`, `docs.search.label`,
  `docs.search.empty`, `docs.search.none`, `docs.search.placeholder`,
  `docs.search.count` (the last one carries the `{count}` token
  `DOCS_SEARCH_COUNT_TOKEN`), and the six catalog keys
  `docs.catalog.loading`, `docs.catalog.error`, `docs.catalog.files`,
  `docs.catalog.size`, `docs.catalog.updated` and `docs.catalog.retry`.
- `locale_text(route, key)` (`docs/src/locale/fn.rs`) resolves the active
  locale's table, then the English table, then falls back to the key itself.
- The hardcoded English constants `HEADER_SEARCH_LABEL`,
  `HEADER_SEARCH_EMPTY`, `HEADER_SEARCH_NONE`,
  `HEADER_SEARCH_PLACEHOLDER`, `THEME_TOGGLE_TITLE` and
  `LOCALE_TRIGGER_TITLE` were **deleted**; the search field's `aria-label`,
  `placeholder`, status announcement, the drawer's `aria-label`/`title`, the
  theme toggle's label and the language control's title now all come from
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

## The public catalog

`docs/src/component/catalog/` renders the public catalog of stored projects in
Rust. It replaced a hand-written script and a hand-written stylesheet, so the
site ships no catalog script and no catalog stylesheet of its own.

- `docs_catalog(node)` is the component; `parse_catalog(bytes)` is the public
  parser, and `docs/src/component/catalog/view/struct.rs` holds
  `DocsCatalogArtifact` (name, file count, total bytes, SHA-256, update time)
  and `DocsCatalog`.
- The request goes through the framework's own `fetch` primitive
  (`core/src/fetch/`) against `CATALOG_URL` = `/api/page-artifacts`. That
  primitive is `#[cfg(target_arch = "wasm32")]`, so a host build has no page to
  fetch from and renders the failure state instead of spawning a browser
  future.
- The card carries the framework's own `c_catalog*` classes **and** the
  `docs-catalog-card` class, which is the contract the documentation runtime
  validator asserts on.
- The component owns the request: it renders the localized loading message,
  the localized failure message and a retry button, and issues the request
  exactly once on the first render and once per retry.

## The build-time diagram

A ```mermaid fence is rendered **at build time** into inline SVG. The engine is
`merman`, a pure-Rust mermaid implementation, and it is a
**`[build-dependencies]`** entry of `euv-docs` — it is **not** a normal
dependency, so the published browser bundle links no diagram engine, no parser
and no embedded font stack.

- `docs/diagram/` holds the renderer: `render_diagram(lang, code, ordinal)`
  returns `None` for any fence that is not a mermaid fence, and
  `render_mermaid(source, ordinal)` returns `None` when the engine cannot lay
  the diagram out. A fence that yields `None` stays an **ordinary code block**,
  so the source remains readable.
- `docs/build.rs` parses the markdown into `AstBlock::Diagram { svg }` and emits
  it as `euv_ui::EuvMdBlock::Diagram { svg }`. The `ui` crate's
  `EuvMdBlock` gained a **`Diagram { svg: &'static str }`** variant for this.
- A diagram is numbered per page (`docs-mermaid-<ordinal>`), so two diagrams on
  one page never share a marker id or a scoped CSS selector.
- The colours come from a **scoped stylesheet** the engine appends to the SVG.
  Every colour it names is a docs theme token, and CSS custom properties
  inherit into an inline SVG, so the diagram follows the root theme class.
- The engine's own default theme is **not** used: it paints the boxes with an
  inline `style`, and an inline style beats every stylesheet rule, so the
  diagram would ignore the page's tokens. A **preset** theme
  (`ThemePreset::EditorLight`) is compiled instead, because a preset paints the
  same boxes from the stylesheet.
- `docs/src/component/mermaid/` is the runtime component: `docs_mermaid` renders
  a `<figure>` with a frame class and a sideways-scrolling inner frame, and
  writes the finished SVG through an `inner_html` attribute.
- `core/src/vdom/attribute/impl.rs` gained `AttributeEntry::inner_html_value()`,
  because `text_value()` does not report an `inner_html` payload — that
  attribute carries markup the renderer writes into the element, not text a
  reader sees. `inner_html_value()` returns `Some(markup)` for both
  `AttributeValue::InnerHtml` and `AttributeValue::InnerHtmlSignal`.

**The size ceiling is why this is a build step.** The artifact service rejects
any file above 8 MiB, and linking the engine into the browser bundle tripled
every locale bundle (the 0.37.9 build produced ~15.3 MB per locale against
that ceiling). Rendering at build time brought each locale back to ~4.5–5.2 MB.

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

`docs/scripts/validation/control_titles.py` (new) asserts that every shell
control's accessible title matches the locale it renders in: the language
dropdown's title must be the `docs.locale.title` value of the route's own
locale, not one hardcoded string.

`docs/scripts/validation/focus_ring.py` (new) asserts the search field's
focus ring: the computed `box-shadow` carries the ring, the focused box and
the text position are identical to the unfocused state, and the colour is the
scheme's own `--ring`. The field used to swap its transparent 1px border for
the ring colour, which is a layout change — the box grew by a pixel and the
text moved with it — and the `--ring-width` / `--ring-offset` tokens were
never consulted.

## The code block palette

The docs code block paints the **editor theme's own palette**, not the site
chrome tokens: the light palette is the reference editor theme's light face and
the dark palette is the same theme's dark face. The two are never collapsed
into one — a colour that reads as a keyword on the light surface is unreadable
on the dark one, and the editor's answer is a second palette, not a compromise.

- `docs/src/highlight/const.rs` holds `CODE_CSS`: a `:root` block with the
  light palette and a `.c_theme_dark` block with the dark one. Both are read
  through `var(--docs-code-…)`, so switching the theme switches the palette
  without a second stylesheet.
- **Twelve** custom properties in `:root` (the nine token classes
  `--docs-code-keyword`, `-string`, `-number`, `-comment`, `-function`, `-type`,
  `-attribute`, `-tag`, `-variable`, plus `--docs-code-surface`,
  `--docs-code-foreground` and `--docs-code-font-family`) and **eleven** in
  `.c_theme_dark` — the dark block repaints the eleven colours and leaves the
  font stack to `:root`, which is mode-independent.
- The code surface paints `--docs-code-surface` / `--docs-code-foreground` and
  the editor's own monospace stack, not `var(--muted)` and
  `var(--font-family-mono)`. The frame's fill is the editor surface too, so the
  page and the editor share one background.
- The keyword and function tokens carry the **bold** face the editor gives them,
  and only the comment class is italic.
- `docs/tests/code_palette/` pins the contract per mode and is fail-closed:
  breaking one part of it turns the suite red.
