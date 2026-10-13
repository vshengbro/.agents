# Shipping a Static Site to a Per-File CDN

Covers the deploy half of the loop: the local build is verified, and now it
must run from a public URL where every reference is an absolute URL to a
different origin. `scripts/deploy-site.js` implements the whole procedure —
this file is the reasoning behind its two non-obvious choices.

## Why the naive order breaks

A single-file uploader gives each file an independent URL under a hashed path.
Local relative references (`./js/main.js`, `import './world.js'`,
`url(../fonts/x.woff2)`) are therefore all dead on arrival — each resolves
against the *referencing file's* URL, not the site root. So references must be
rewritten to absolute URLs, and a file's rewrite is only possible **after**
its dependencies have URLs. That forces the order: leaves first, entry last.

## Pitfall 1 — an importmap is a dependency edge no scanner sees

```html
<script type="importmap">{"imports":{"three":"./lib/three.module.js"}}</script>
```
```js
import * as THREE from 'three';   // bare specifier, no file named "three"
```

A regex scan of the JS reports `three` as a **missing file** (nothing on disk
is named that), and the importmap's own value is a perfectly ordinary-looking
relative path that a scanner keyed on `src=`/`import from` never examines. Two
failure modes, both bad:

- treat it as missing → warn about a nonexistent file, or skip the importmap
- skip it → the 1 MB vendor bundle sorts *after* the modules importing it, so
  every module 404s and the page renders blank with no obvious cause

Fix: parse the importmap JSON, add `specifier → value` as a real edge, and
rewrite the importmap's **value** to the final URL. The bare specifier in each
importing file then resolves correctly and needs no edit. Verify:

```bash
grep -c 'ltpp.vip/upload/file' <uploaded main.js>   # expect == # of modules using the bare name
```

Same trap for bundler-style alias maps in a `package.json`/`vite.config` —
treat any specifier→path indirection as an edge, not a string.

## Pitfall 2 — upload stdout is not JSON

The uploader prints a banner, per-file `OK:` / `verify attempt` / `✓ Verified`
lines and a `=== RESULTS ===` header, then the JSON array — all on **stdout**.
`JSON.parse(stdout)` therefore throws on a completely successful upload, and
the run aborts *after* the file is already live on the server. That produces
the worst outcome: a real URL nobody has, plus a confusing crash.

```js
const raw = out.trim();
const start = raw.lastIndexOf('[\n  {');
const arr = JSON.parse(start >= 0 ? raw.slice(start) : raw.slice(raw.lastIndexOf('[')));
```

Judge failure by `entry.error` / missing `url`, never by the parse throwing.
The `✓ Verified: <name> (<bytes> bytes, md5 OK)` line is ground truth when the
two disagree.

## Pitfall 3 — a partial run still left live files

Because each file is an independent registration, an aborted loop leaves the
already-uploaded files live but unreferenced. Re-run the **whole** deploy
rather than resuming: every file gets a fresh URL, and a half-set of URLs is
worse than none because it looks complete. These orgs have no public delete
API, so orphans accumulate — harmless, but never report them as the result.

## Pitfall 4 — temp files must keep their extension

Rewritten content goes to a temp dir so the user's source stays untouched. The
server infers MIME from the extension, so flatten to `name__path.js`, not
`name__path` — a stripped extension yields a download/garbage content type and
a module that refuses to execute.

## Verifying the deploy (non-negotiable)

Open `entry_url` and repeat the app's own checks there: readiness flag, state
read back through the console, one real input event, one screenshot. A correct
local build says nothing about whether the rewrites landed — the deployed page
fails in ways the local one cannot, and a blank canvas is the usual symptom.
Confirm the graph decision was right by checking the entry HTML's references
are absolute:

```bash
curl -s "$ENTRY_URL" | grep -oE '(src|href)="[^"]*"' | grep -v '^\(src\|href\)="https\?:'   # want: no relative hits
```

If a relative one shows up, that file's rewrite silently did not fire — most
often because its reference was matched in a form your scanner skipped.
