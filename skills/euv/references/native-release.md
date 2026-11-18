# Native release themes and the website update channel

Source of truth: `origin/master` of `euv-dev/euv`. Everything below was read
from the committed tree, not from a local branch.

## Release theme variants

`example/scripts/build_theme_variants.sh` builds every release variant as an
independent example build:

- The variant list comes from `cargo metadata --no-deps --format-version 1`:
  `default` plus every `theme-*` feature of `euv-example` — **19 in total**
  (18 theme features + `default`). The list is read from metadata, not hardcoded.
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

## The release manifest

`example/scripts/write_release_manifest.py` writes `example/www/euv-release.json`
— the website-owned inventory the native client trusts:

```json
{ "format": 1, "version": "0.36.0", "files": [ { "path": "...", "sha256": "...", "size": 0 } ] }
```

- The version comes from the `euv-example` manifest, and must be a plain
  numeric semantic version.
- Symlinks, unsafe path segments, non-regular files and reserved names
  (`euv-release.json`, `__euv_local_bundle__.json`, `_manifest.json`, `.empty`,
  `active`) are rejected.
- A non-empty `index.html` must be present, or the manifest is not written.

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
  base fails with `ReleaseOriginMismatch`.
- `activate_release` stages the bytes, verifies them, and only then renames a
  temporary pointer file over `active`. On failure it removes the staged
  directory and the temporary pointer, so a partial update never goes live.

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
