# Harvesting reference images from a vendor product page

For 1:1 work the reference set decides the outcome. The goal is not "some
product shots" but a set that lets you **measure** the real thing.

## What to collect, in priority order

1. **Hardware diagrams** (`hw_*`, "connectivity", "ports", "in detail") —
   straight-on, evenly lit, no perspective. These are the only images from
   which a feature's position can be read as a percentage of panel width.
2. **Straight-on elevations** — front, rear, side, top, bottom. Used for the
   band/zone profile (below).
3. **3/4 product shots** — for material and edge-break feel only. Never for
   position: perspective and the studio's angle choice make them unusable as a
   ruler.
4. **x-ray / exploded diagrams** — surprisingly good for the underside. They
   often show the bottom vent panel edge-on when no face-on bottom shot exists.

**Product-page scrolling is low yield.** A 42000px page scrolled in viewport
steps produced 46 screenshots and exactly one usable new angle; the views that
actually mattered were already sitting in the DOM as separate image files.
Scroll only when the user explicitly asks for the scroll narrative — and when
they do, say up front that the hardware diagrams are where the measurements
come from, so an unproductive scroll pass is not mistaken for a dead end.

When scrolling *is* requested, drive it with CDP rather than `--screenshot`,
which captures only the first viewport:

- `Page.enable` + `Emulation.setDeviceMetricsOverride` to fix the viewport, so
  the frame count is deterministic.
- `Page.navigate`, then poll `document.readyState === "complete"` and sleep
  before the first shot — a too-early capture gets a half-hydrated page.
- Per step: `Page.captureScreenshot`, then `Runtime.evaluate` to scroll by
  `innerHeight * 0.92` and pause ~1.8 s for lazy-loaded images.
- Stop on `scrollY + innerHeight >= scrollHeight`, and write the image
  manifest (`document.images` with `naturalWidth`) alongside the frames.
- Build a contact sheet of every Nth frame and read *that* with vision to pick
  which full frames deserve a look. One contact sheet costs one vision call;
  reading 46 frames costs 46.

Note that a scroll pass frequently surfaces x-rays and thermal diagrams rather
than new elevations — useful for the underside, useless as a ruler.

## Method

Static first, browser second:

```bash
curl -sSL -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15" \
  "$PAGE" -o /tmp/page.html
grep -oE 'https://[^"]*\.(jpg|webp|png)' /tmp/page.html | sort -u
```

If that yields nothing useful, the page is script-rendered. Drive headless
Chrome over CDP (`--remote-debugging-port`, then `Page.navigate` +
`Runtime.evaluate`) and read the live DOM:

```js
Array.from(document.images)
  .map(i => ({src: i.currentSrc || i.src, w: i.naturalWidth, h: i.naturalHeight}))
  .filter(i => i.w >= 500)
```

**Dedup by filename stem.** The same asset appears at several sizes and in
several sections; key on the stem before the size/hash suffix, or you download
the same diagram five times under different names.

**Try the vendor's own size ladder, but expect it to be capped.** Replacing
`/large.` with `/xlarge.` or `/xxlarge.` often works and sometimes returns
nothing larger. Do not treat the 650x322 diagram as a failure — upscaling
helps no measurement, and at 3x with LANCZOS the vision model reads positions
off it fine.

## Measuring from a diagram

### Feature positions along a panel

Read each feature's centre as a percentage of the panel width, then convert:

- front elevation (camera looks from `-Y`): image-left is model `+X`, so
  `x = W/2 - (pct/100) * W`
- rear elevation (camera looks from `+Y`): mirrored, `x = W/2 + (pct/100) * W`

Keep the percentages in the source as named constants next to the derived
coordinates, with the diagram filename in the comment. The comment is what
stops a future edit from re-introducing a guess.

### Zone profile across a face

Sample dark-pixel share in horizontal bands across the chassis. It reads a
ventilation layout off a flat product image with no vision call at all:

```python
mask = a > 150                                    # metal
y0, y1 = rows where the chassis is, likewise columns
body = a[y0:y1+1, x0:x1+1]
dark = body < 95
for i in range(20):
    seg = dark[int(H*i/20):int(H*(i+1)/20)]
    print(i*5, seg.mean()*100)
```

Typical read on a rear panel: a big high-dark region, a near-zero band, then
another high-dark region gives "perforated field / solid port band /
perforated field" with the band edges as numbers. Compare that against the
same statistic computed from your render and the difference is actionable
("the band should be 55-70%, yours is 27-47%"), which a vision description
never gives you.

**Always print the chassis `h/w` alongside.** It is a free proportion check
against the published size, and it is the fastest way to detect that your own
crop failed (see below) — a 19.7 x 9.5 cm part reading 1.00 means the crop
grabbed the frame, not the object.

### The chassis envelope itself

A dimension with no check is invisible however wrong it is. A 10 mm error in
depth passed every check in the suite, because twenty port positions, a
perforated field and five glyphs are laid out on the *face* and none depends on
how deep the machine is. The calibration constants every other measurement
divides by were literals nothing held the model against.

Measuring the box off the reference photograph took three attempts, and each
produced a plausible-looking wrong number — which is why the shape of the
measurement matters more than the result:

| method | measured | why it is wrong |
|---|---:|---|
| strongest column gradient | **0.0 mm** | 3,000 perforations out-contrast one 197 mm edge; the two top columns land 9 px apart |
| Otsu over the whole frame | **40–65 mm** | splits *page from metal*, not machine from page — thr 117, eta 0.88, a clean split of the wrong two populations |
| any metal/page threshold | **172.85 mm** | the outer ~12 mm each side is a bright bevel on the page side of *any* such split; the real box is 197.00 |

The form that works is a **share of the box, with the silhouette's own trim
stated** — 12.1 mm a side in X, 2.0 mm a side in Y. The axes are not symmetric,
and applying one constant to both is what made the first two attempts fail. The
floor is a constant, so a change in either the photograph or the model still
moves the number; a threshold fitted until it reads 197.00 is a constant wearing
a measurement's clothes.

Two details that cost a round each:

- **Normalise before the existing threshold helper.** Otsu implementations here
  take 0–1 input; handing them 0–255 returns `thr=0.0, eta=0.000` and trips the
  separability guard. Match the convention the file's other callers use.
- **Verify per axis, by mutation.** A depth that no feature depends on will not
  be caught by any check that only measures features, so mutate each dimension
  independently and confirm the gate names the one you changed.

## Never commit vendor imagery

Reference material is licensed to the vendor. Keep it under an ignored
directory (`reference/`) and gitignore it. Confirm with
`git check-ignore -v reference/<file>` rather than assuming the pattern
matched.

**Force-adding vendor imagery and then running `git reset --hard` deletes the
local copies.** `git reset --hard` rewrites the working tree to the commit, so
a file that was `git add -f`-ed into a commit and then removed by the reset is
gone from disk even though the directory is gitignored. Re-derive the set from
the manifest you already wrote (the image list is a file — keep it outside the
git reset path or in a separate scratch dir) rather than re-scraping the page.

Prefer not creating that situation at all: the correct order is gitignore
first, then download. If a commit does slip through, reset and force-push
rather than amending history into a public branch.
