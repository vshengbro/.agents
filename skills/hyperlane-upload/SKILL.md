---
name: hyperlane-upload
description: 'Publish a built site or bundle to ltpp.vip and get public URLs. Use when the user names ltpp.vip or picks it as the host. Do NOT use for generic uploads (S3, GitHub, Feishu attachments).'
license: MIT
metadata:
  hermes:
    tags:
      - hyperlane
      - deploy
      - ltpp
    related_skills:
      - hyperlane
---

# Publish to ltpp.vip

Uploads files to `https://ltpp.vip/upload` and returns public URLs.

**Trigger only when the target is ltpp.vip** — the user names it ("上传到
ltpp", "ltpp.vip", "get an ltpp link", "publish to ltpp"), or explicitly
chooses it as the hosting service. "Upload this file", "give me a public link",
"deploy this site", "share this screenshot" on their own do **not** select this
skill — an S3 bucket, a GitHub release, a Feishu/Lark attachment or a docs
sidebar upload are different destinations with different tooling. Ask which host
if it is genuinely unstated.

**This skill performs real external writes.** Every invocation publishes public
URLs. Do not run it "to test the docs", to dry-run the workflow, or while
writing documentation. Read `scripts/upload.js` to learn the interface; run it
only for an actual publish.

## Single file

```bash
node scripts/upload.js <file-path>
```

Prints a JSON array of `{ name, url, size, md5, verified, verifiedSize,
verifiedMd5, verifiedAt, contentType, error }` per file and exits non-zero if any
verification failed. Files inside one invocation upload in parallel and are
assumed independent — the script never scans for internal references.

Read `--help` for `--parallel N` or `--serial`. Keep post-upload verification
enabled; do not use the verification-skipping option to manufacture success.

After a merge the script GETs the returned URL and compares size and md5
against the source, retrying up to 3× with backoff — CDN propagation can lag.
`verified: false` with a populated `error` means the bytes did not round-trip;
report it rather than handing the user the URL as if it worked.

## Multi-file with dependencies

The script does **not** rewrite references. Drive the ordering yourself: build
the graph, upload leaves first, rewrite local references in dependents to the
returned URLs, then upload the rewritten copies.

1. **Scan** each text file for local references, resolved against the
   *referencing* file's directory. Only open text extensions (`.html .htm .js
   .mjs .css .svg .json .txt`) — reading a `.wasm`/`.png`/`.woff2` as UTF-8
   throws. Binary files are always leaves.
   - `.html`: `src` / `href` / `srcset` / `poster` on `script`, `link`, `img`,
     `video`, `audio`, `source`, `iframe`, `use`.
   - `.js`: `import` / `from` / `fetch(` / `new URL(…, import.meta.url)` /
     `WebAssembly.instantiateStreaming(` / `importScripts(` / `new Worker(`.
   - `.css`: `url(…)` (quoted or bare) and `@import`.
   - Skip absolute URLs (`http:`, `https:`, `//`, `data:`, `blob:`, `mailto:`,
     `tel:`), inline `<script>`/`<style>` bodies, and `#anchors`.
   - Use whitespace-tolerant patterns (`\s*` around keywords and parens); a naive
     `fetch\("…"\)` regex misses legal spacing.
2. **Sort topologically** so every file uploads after its dependencies. Use a
   sorted queue for reproducibility. A cycle has no leaf-first ordering: stop
   before publishing and use a bundle or a hosting scheme with stable paths.
   Do not publish dangling placeholders as a purported cycle fix.
3. **Rewrite and upload** in order: read the file, substitute each local
   reference with the final URL from the already-uploaded map, write the result
   to a **temp file** (never mutate the user's source), upload the temp file,
   record `local_path → url`, then delete the temp file.
   Try every reference spelling (`"app.js"`, `"./js/app.js"`, `"../js/app.js"`)
   since the same target appears in different forms. CSS `url(…)` needs its own
   unquoted branch.
4. Resolve references outside the input set during preflight. If the deployed
   entry needs them, include them or establish a valid already-hosted URL;
   unresolved required local references block a completed deployment claim.
5. Report the entry URL plus the full path→URL map, and list anything left
   un-rewritten.

Return the entry URL as the thing to open; the rest live inside the rewritten
entry and don't need sharing.

## Rust / wasm bundles

`wasm-pack` output references its wasm as
`new URL('<crate>_bg.wasm', import.meta.url)`. Once the JS is on ltpp.vip that
resolves against the **JS's** URL and can 404. Upload the wasm first, rewrite the
local JS copy to its final URL, then upload that copy; do not upload a broken JS
version first. Do not assume unwanted public uploads can be deleted. Full recipe and a
post-deploy DOM probe: `references/euv-wasm-bundle-deploy.md`.

## Failure modes

- Non-200 on `register` — preserve the status/body and diagnose before retrying;
  do not guess that renaming a file will solve every failure.
- Missing reference on disk — report the file and path; never invent a URL.
- Network failure mid-upload — re-run `upload.js` for that one file; each
  registration is independent.
- This script uses raw `https`. Reaching for puppeteer means you're on the wrong
  path.
