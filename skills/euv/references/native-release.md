# Native release themes and the website update channel

Source of truth: `origin/master` of `euv-dev/euv`. Everything below was read
from the committed tree, not from a local branch.

## Release theme variants

`example/scripts/build_theme_variants.sh` builds every release variant as an
independent example build:

- The variant list comes from `cargo metadata --no-deps --format-version 1`:
  `default` plus every `theme-*` feature of `euv-example` — **18 in total**
  (17 theme features + `default`). The list is read from metadata, not
  hardcoded. `theme-custom` was removed, so the count dropped from 19 to 18.
- Each variant is one `cargo run -p euv-cli -- build --crate-path ./example
  --release --www-dir www/themes/<feature> -- --no-default-features [--features
  <theme>]` call.
- The script requires only `cargo` and `python3` on `PATH` (it also honours
  `WASM_BINDGEN_BIN_DIR`). It deliberately does **not** require a global
  `wasm-bindgen` binary: the CLI uses wasm-pack's own private wasm-bindgen
  installation, so requiring one rejects otherwise valid environments.
- Output goes to `example/www/themes/<feature>/` and must contain a non-empty
  `index.html` and `pkg/euv_example_bg.wasm` or the build fails.
- A source fingerprint (sha256 over `Cargo.toml`, `Cargo.lock`,
  `example/index.html`, the theme script and the `src/` trees of the root,
  `core`, `macros`, `ui`, `engine`, `cli` and `example`) is written to
  `native/tauri/.cache/themes/<theme>.sha256`. A matching stamp plus intact
  artifacts skip the rebuild.
- A failed build prints the compiler output (not just the log path) to stderr.
- **Retired themes are pruned.** Before building, the script removes any
  directory in the output tree and any `*.sha256` stamp in the cache whose name
  is not a current feature (`Removed retired theme output: …` /
  `Removed retired theme stamp: …`). A symlinked output or cache directory is
  refused. After the build it asserts the output set equals the current feature
  set and that **no** release artifact contains the `__euv_reload` development
  bootstrap. This is what stops a removed theme from surviving a restored
  release-output cache; `native/tauri/scripts/tests/theme-build.test.js` covers
  the cold and warm paths and runs in the CI `check` job.

## The release manifest

`example/scripts/write_release_manifest.py` writes `example/www/euv-release.json`
— the website-owned inventory the native client trusts:

```json
{ "format": 1, "version": "0.36.4", "files": [ { "path": "...", "sha256": "...", "size": 0 } ] }
```

- The version comes from the `euv-example` manifest (or `--version`), and must
  be a plain numeric semantic version.
- Symlinks, unsafe path segments, non-regular files and reserved names
  (`euv-release.json`, `__euv_local_bundle__.json`, `_manifest.json`, `.empty`,
  `active`) are rejected.
- A non-empty `index.html` must be present, or the manifest is not written.

## Publishing the release to the website

`example/scripts/publish_release.py` (new) publishes the built `example/www`
tree through the page-artifact API. `example/scripts/test_publish_release.py` is
its regression suite.

- CLI: `publish_release.py <directory> --version <X.Y.Z> --receipt <path.json>`.
  `PAGE_ARTIFACT_API_KEY` must be set in the environment.
- `validate_directory` refuses symlinks anywhere, requires the on-disk file set
  to equal the manifest set exactly, verifies each file's size and sha256, and
  requires every `themes/<t>/` to hold an `index.html` and a `.wasm`. A path
  segment that is empty, `.` or `..`, or a path containing `\ : ? #` or control
  characters, is rejected before any upload.
- Uploads are chunked: the archive is POSTed, each chunk is PUT with an
  `X-Chunk-SHA256` header, then the upload is committed. Redirects are
  rejected (a `NoRedirect` opener) and the live catalog and every published
  file are re-read and re-verified afterwards.
- A **newer live release is never replaced**; the candidate's semver is
  compared against the live manifest first.
- The receipt records `version`, `archive_sha256`, `archive_bytes`,
  `manifest_sha256`, the per-file inventory, the public base and the
  `publication_route` (`page-artifacts API only; no GitHub Pages sync`).
- `.github/workflows/pages.yml` drives this and is **manual**: `workflow_dispatch`
  with a required `source_run_id` naming a successful `build-clients.yml` master
  run. It downloads that run's `euv-native-web-<sha>` artifact instead of
  rebuilding, refuses a release that a newer master has superseded, asserts the
  artifact's theme set equals `{default} ∪ {theme-* features of euv-example}`,
  and only then publishes. There is no GitHub Pages deployment and no
  `github/pages/sync` call any more.

## Client-side verification and activation

`native/tauri/src-tauri/src/release/` owns the update protocol; the constants
live in `release/const.rs`.

- `RELEASE_BASE` is the update origin; `RELEASE_NAME` is the manifest file
  name; `RELEASE_POINTER` is the `active` pointer file; `RELEASE_PREFIX`
  (`v_`) prefixes a snapshot directory name.
- `parse_release` parses the canonical numeric version and rejects an
  ambiguous one; `safe_release_path` rejects traversal, encoded separators,
  native markers and URL-shaped paths.
- `verify_release_file` checks the exact original bytes (size and sha256)
  before they can become a native snapshot; `verified_release` re-verifies a
  persisted snapshot including every manifest-listed resource.
- `stage_release` downloads exactly one URL per file and rejects a redirect
  away from its identity; a file whose URL origin or path leaves the release
  base fails with `ReleaseOriginMismatch`. The base path must also end with
  `/` — an unconfined base is rejected outright rather than being matched
  prefix-wise.
- `activate_release` stages the bytes, verifies them, and only then renames a
  temporary pointer file over `active`. The temporary pointer is created with
  `create_new(true)`, so a planted symlink or pre-existing file at that path
  cannot be written through; the file is removed on failure only if it was
  actually created. A partial update never goes live.
- Digest hex is validated with the `RELEASE_HEX_LETTER_START`/
  `RELEASE_HEX_LETTER_END` constants, and snapshot names are split on
  `RELEASE_SNAPSHOT_SEPARATOR` (`_`).

`native/tauri/src-tauri/src/snapshot/` owns the local document view:
`complete_snapshot` checks that the entry page and every required resource are
non-empty files, `snapshot_paths` lists the independently navigable documents
absent from the root resource graph (theme entry points are selected from WASM
rather than HTML links), and `local_document` rebases a document's `<base>` onto
its own local directory so a theme page does not resolve its WASM against the
root page.

`native/tauri/src-tauri/src/cache/fn.rs` is the caller: it reads the active
pointer, verifies the snapshot, fetches a full snapshot when needed and calls
`activate_release` to commit the switch.
