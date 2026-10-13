# The safe-area token is a trust gate, and env() lies on all four sides

A design-token migration can make every consumer *agree* and still leave the
page wrong, when the token's value itself is untrustworthy. `env(safe-area-inset-*)`
is the canonical case: it is a **claim by the host browser**, and some hosts
report non-zero insets for a page that is demonstrably not laid out edge-to-edge.

## The bug class

The shell consumes one inset token per edge, through several different
components: the top header, the mobile drawer, the root's `padding-bottom`,
the sidebar footer, the floating action button. Teams usually apply a trust
gate to **one** edge — the one that got reported — and leave the rest reading
`env()` directly.

The same lying value then returns through a different door, and the report
reads as a *new* bug in an unrelated place ("the bottom of the sidebar is
now a huge blank band"). It is not a new bug. It is the original bug's second
exit.

| edge | the value is consumed by | reported symptom |
|---|---|---|
| top | mobile header / drawer `padding-top` | "big blank above the navbar" |
| bottom | shell root `padding-bottom`, sidebar footer, FAB | "huge blank under the sidebar" |
| left/right | mobile shell `padding` | content hugs or avoids the wrong edge |

**Rule: the trust gate covers every edge or none.** Grep the token layer for
`env(` before deciding the migration is finished — and remember a theme file
usually declares the same tokens twice (light + dark), so one grep hit is
often two.

## The gate shape that works

Do not decide trust inside CSS. Decide it in script, measure, then publish:

1. **Host declares intent, if it knows.** A `window.<FLAG> = true` or a
   `<meta name="…-immersive">` tag lets a host that genuinely runs edge-to-edge
   say so. This is the only *positive* evidence available.
2. **Otherwise infer letterboxing.** `screen.height - window.innerHeight` being
   large means the browser already laid the page out below the system chrome —
   the page is letterboxed, so every inset it reports is dead space. Measured
   on-device; a desktop headless run cannot substitute.
3. **Only then write the measured pixels** into a custom property on the root
   element, defaulting to `0`.
4. **CSS consumes only that property** (default `0`), never `env()`.

Keep it a **pure, testable function** — the host-intent check, the
letterbox-gap arithmetic and the final inset choice should be unit-testable
off-device, since the values they consume are plain numbers.

**Fix the token definition, not the consumers.** One definition change covers
every current and future consumer; per-consumer fixes drift, and each one you
skip is another blank band the user finds later.

## A trap that follows from point 3

The measurement path is often also used to repair state after an event (a
fullscreen exit on Android invalidates `env()`; a cached value gets replayed).
Whatever you add must run on **that** path too, not just at first load — a
variable correctly defaulted at startup but never refreshed still shows a
blank band after the user leaves fullscreen.

## The assumption you must not carry between projects

"Project A's template has no `viewport-fit=cover`, so its insets are always
zero" is **not** transferable. Different sites of the same framework choose
differently: a demo template may drop cover and let the system letterbox, while
a site template keeps it because its immersive host genuinely needs it. Before
reasoning about inset behaviour:

```bash
# the shipped template(s) — and the builder's constant file often holds a
# second and third viewport meta that will override or duplicate it
grep -rn "viewport-fit" <site>/ <framework>/  --include=*.html --include=*.rs
```

Getting this backwards inverts the whole conclusion: you either delete cover
from a host that needs it, or keep it and assume zero insets on a browser that
fills the screen.

## Probing

Ask for all four insets plus the letterbox gap in one call — a probe that
reports only the top edge cannot distinguish "fixed" from "moved the problem":

```js
const d = document.createElement('div');
d.style.cssText = 'position:absolute;visibility:hidden;' +
  'padding-top:env(safe-area-inset-top);padding-right:env(safe-area-inset-right);' +
  'padding-bottom:env(safe-area-inset-bottom);padding-left:env(safe-area-inset-left)';
document.body.appendChild(d);
const cs = getComputedStyle(d);
JSON.stringify({
  insets: ['paddingTop','paddingRight','paddingBottom','paddingLeft'].map(k => cs[k]),
  letterboxGap: screen.height - window.innerHeight,
  viewport: document.querySelector('meta[name=viewport]')?.content,
});
d.remove();
```

`insets` non-zero **and** `letterboxGap` large is the lying host: report every
edge as `0`. Small gap with non-zero insets is the real thing: keep them.

## The sibling bug: a wrapping button row sized by its content

Same shape, different trigger — a container of `flex-wrap: wrap` buttons whose
children are `inline-flex` and content-sized. Different label lengths produce
different widths, so the row looks ragged the moment it wraps, and the reported
symptom ("the homepage buttons are misaligned") reads as a data problem.

Fix it in the **one** breakpoint the design system uses, giving every button in
the group the same basis so they divide the row evenly. A group whose buttons
differ in width *by design* (a primary CTA next to a quiet link) is a different
case: do not equalise it.

Verification is a rect comparison, not a screenshot: read the buttons'
`getBoundingClientRect().width` in one breakpoint and assert they match.