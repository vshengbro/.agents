---
name: edge-bleed-active-fill-geometry
description: "Use when an active row's fill bleeds to an edge."
license: MIT
metadata:
  version: "1.0.0"
  category: frontend
  tags: [css, active-state, sidebar, tree-view, box-model, geometry, verification]
---

# Edge-bleed active fills that do not move the text

Any navigation rail — sidebar, tree view, file tree, list, tab strip —
where the selected row's highlight bleeds to the panel edge or to the
level's guide line, so it reads as one block with the rail rather than a
chip floating in from the edge.

Trigger phrases: "highlight should reach the edge", "active item looks like
a floating chip", "selected row doesn't line up with the guide", "the
background crosses the border", "text jumps when I click", "label shifts
on hover/active", "侧边栏激活背景超出边框", "悬浮/激活时文字有位移".

The whole class turns on **one distinction**: a fill owns two distances,
and a third belongs to the text alone.

```
inactive:  |[margin][padding][ TEXT ............|
active:    |[margin][padding][ TEXT ............|   <- label must land here
           ^^^^^^^^^^                          fill must start here
           |        |
           |        +-- the row keeps its own padding; the fill is
           |            painted behind it, not in place of it
           +-- the pull-back constant is margin + border, NEVER + padding
```

## Derive the pull-back constant from geometry, not arithmetic

The instinctive constant is "however far the row sits from the edge",
which people write as `margin + padding + border`. Padding is not part of
it — that term makes the background overshoot the guide by exactly the
padding, which is the bug this class usually arrives with.

Measure the guide in the browser, build a candidate table, then read every
candidate back at **two nesting depths** — a wrong constant often looks
right at depth 1 and wrong at depth 2, so one depth is not a test:

| `margin-left`     | depth-2 leaf | depth-1 title |
|-------------------|--------------|---------------|
| `-(m+p+b)`        | overshoot **+8px** | overshoot **+8px** |
| `-(m+b)`          | **0**        | **0**         |
| `-m`              | -1px         | -1px          |
| `0`               | -9px         | -9px          |

Take the constant from the row that measures clean, not from the one that
looks most plausible in the stylesheet. Keep it in a token (plus a bare
numeric companion when the CSS needs it inside `calc()`), and **update
every theme definition in the same edit** — a constant correct in light
and stale in dark is the most common way this ships half-fixed.

## Then pay the margin back to the text

Correcting the overshoot still moves the label, because the negative
margin applies to the text too. When the requirement is "hover and active
must not move the text", return the same amount as left padding so the
two cancel:

```css
padding: 12px 12px;                              /* shorthand first */
padding-left: calc(12px + 9px);                  /* then the one longhand */
margin-left: -9px;
width: calc(100% + 9px);
```

### Never write the compensation as a multi-value `padding` shorthand

`padding: calc(A + Bpx) A A A` looks equivalent and is not — when a
value is itself a `calc()` over a token (macro-generated CSS often is),
the shorthand emits malformed output, the other three sides are lost, and
the row **collapses in height**. Set the shorthand, then override the
single longhand. Always assert the row's height after this change; it is
the only thing that catches the mistake.

## Framework constants get duplicated into site overrides

A consumer project that restyles these classes with `!important` usually
hardcodes the same numbers. Editing the framework token does not update
the copy, so the bug is only half-fixed and the rendered result is
explained by neither source. Before declaring done, grep the consuming
project for the literal and update both.

## Verify the text node, not the row box

The row box's `left` is *supposed* to change — that is the fill growing.
Asserting on it reports a false positive on every correct implementation.

```js
const textLeft = (el) => {
  const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
  let n = w.nextNode();
  while (n && !n.textContent.trim()) n = w.nextNode();
  if (!n) return null;                       // wrapper with no text
  const r = document.createRange();
  r.selectNodeContents(n);
  return Math.round(r.getBoundingClientRect().left * 10) / 10;
};
```

Take **before and after inside one page load** — record the baseline,
click to change state, record again. Never compare two separately-loaded
pages: a hash-only navigation is a same-document navigation, so any probe
CSS you injected persists into your own "before" arm.

Three independent assertions, all required:

| Assertion | Expected |
|---|---|
| `text_left`, inactive vs active | **equal** — the no-shift requirement |
| row `left` vs guide `left` | equal, overshoot **0** — the bleed requirement |
| row `height` | **unchanged** — catches the shorthand collapse |

## Hover usually needs no compensation

If the hover state is painted with an inset `box-shadow`, it occupies no
layout space and cannot move text. **Measure it, confirm it, then leave it
alone.** Adding margin or padding compensation for a hover that never
shifted is how you introduce the exact bug you were asked to fix — and
because the symptom is subtle, it survives into review.

The general rule: for every state transition, decide whether the visual
change is painted (shadow / background / colour — free) or laid out
(margin / padding / border / width — costs geometry), and compensate only
the latter.

## Marker bars cover the guide, they don't sit beside it

A hover/active marker strip (`::before`) that lands *adjacent* to the
level's dashed guide reads as misaligned — the expected look is the bar
drawn **over** the guide, hiding it for the bar's height. The offset is
the same pull-back constant as the fill (`margin + border`), so one token
serves both:

```css
.c_row::before { content: ''; position: absolute; top: 0; bottom: 0;
                 width: 5px; left: -9px; }  /* == margin+border → barLeft == guideLeft */
```

Verify with the pseudo-element's computed offset against the guide's
`border-left` x position, at **two depths and both row kinds** — group
titles and leaf links often carry different authored offsets (`-2px` vs
`-8px` is the classic drift), and a fix that corrects only one row kind
ships half-done:

```js
const barLeft = (el) => {
  const r = el.getBoundingClientRect();
  return Math.round((r.left + parseFloat(getComputedStyle(el, '::before').left)) * 10) / 10;
};
// walk up from the row to the ancestor whose borderLeftWidth != '0px' — that is the guide;
// assert barLeft(row) == guide.getBoundingClientRect().left for title rows AND leaf rows
```

When the user supplies a reference screenshot of the correct look, match
the *relationship* (bar overlaps guide vs bar beside guide), not the pixel
count — DPR scaling makes absolute px measured off a crop unreliable.

## Related

- `css-display-contents-flex-items` — when the wrapper between the row and
  its scroll container is `display: contents`, sticky positioning and
  child-count layout both fail in ways that look like unrelated bugs.
- `browser-app-self-verification` — validating that you are measuring the
  build you just made, before trusting any of these numbers.
- `css-edge-cases` — box-model quirks, dropdown width, hash-router anchors.