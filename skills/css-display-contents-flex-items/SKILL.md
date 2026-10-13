---
name: css-display-contents-flex-items
description: 'Use when a gap sits between zero-margin sibling elements.'
license: MIT
metadata:
  version: "1.0.0"
  category: frontend
---

# `display: contents` breaks parent child-count assumptions

## When this applies

A gap or stray whitespace opens between two elements that are adjacent
siblings in the DOM, and neither one has any margin, padding or gap
contributing to it. Both report `margin: 0px` / `padding: 0px`, and
adjusting spacing values changes nothing. Or a `flex: 1` child, a
`justify-content: space-between` distribution, or a `:nth-child` style
lands on the wrong element.

Trigger phrases: "big blank between the title and the body", "标题和正文之间大片空白", "the gap is not a margin", "space-between puts the gap in the wrong place", "flex column has the wrong number of children".

## Root cause

`display: contents` removes the wrapper's own box and **promotes its
children to become children of the parent box**. If the parent is a flex
or grid container, the grandchildren become independent items. Component
frameworks that project children through a slot/wrapper with
`display: contents` therefore hand the parent N+1 items, not N.

```jsx
<div style={{display:'flex', flexDirection:'column', justifyContent:'space-between'}}>
  <slot />          {/* display: contents — the <h1> and <article>
                       become TWO separate flex items of this column */}
  <div class="tail">…</div>
</div>
```

The author wrote this as "two children, tail pinned to the bottom". On a
657px column holding a 54px heading, a 231px article and a 188px tail,
free space is `657 - 473 = 184px`. `space-between` splits it into two
92px gaps — one landing directly under the heading. That 92px is the
blank the user reports.

## The one probe that finds it

Reading `parent.children` shows one zero-height wrapper and appears to
prove nothing sits between the two elements. **It lies** — the wrapper
has no box, so the gap belongs to no element at all.

Flatten the subtree through every transparent node and count the real
boxes; that count is the item count:

```js
(() => {
  const col = document.querySelector('.flex-column');
  const flat = [];
  const walk = (el) => {
    if (getComputedStyle(el).display !== 'contents') {
      const b = el.getBoundingClientRect();
      flat.push({tag: el.tagName, cls: el.className,
                 top: Math.round(b.top), h: Math.round(b.height)});
    }
    for (const k of el.children) walk(k);
  };
  walk(col);
  return JSON.stringify(flat);
})()
```

Bug present when two elements that should be flush appear as separate
entries. **Start here** — skipping the descent costs several rounds of
chasing margins that are all `0`. Toggling `justify-content`,
`align-self` on the wrapper, or `margin-top` on the inner elements is the
reliable way to burn those rounds: a no-op on all three is itself the
signal that the distribution, not the spacing, is at fault.

## Fix

Wrap the projected children in a **real element** so the parent gets the
item count it was written for:

```jsx
<div class="flex-column">
  <div class="body">{children}</div>
  <div class="tail">…</div>
</div>
```
```css
.body { display: flex; flex-direction: column; flex: 0 0 auto; min-width: 0; }
```

`flex: 0 0 auto` keeps the body at its natural height; only the tail is
pushed to the far end. `min-width: 0` stops a wide child (code block,
table) from forcing horizontal overflow.

The wrapper must be a real box. Leaving it as `display: contents`
reproduces the bug exactly — hoisting is that property's documented
behaviour, not a browser quirk.

Then give the two former siblings an explicit small gap, because once
the flex distribution no longer separates them they sit flush and read
as one block.

## Do not fake it

**Do not switch `space-between` to `flex-start`.** That removes the gap
but also removes the bottom-pinning the `space-between` existed for, so a
footer that should sit at the bottom of a short viewport now floats
mid-page. The distribution was right; the child count was wrong.

Generalise the reflex: reach for the child count first, and only change
the distribution if the count was already correct.

## Percentage heights and this layout

A bottom-pinned tail needs the parent column to have a definite height.

A viewport unit is wrong when the column lives inside a scroll container
(`overflow: auto`) rather than the window: `100vh` measures the whole
window including any app header, so the column overshoots and pushes the
tail past the fold. Use a percentage — but only where it resolves. A
percentage resolves solely against a containing block with a definite
height; one level deeper, behind an auto-height flex row, `100%`
silently degrades to `auto` and the tail floats back up mid-page with no
error anywhere. Put it on the element that is a direct child of the
scroll container.

Acceptance, all together:

| Check | Expected |
|---|---|
| Flattened items in the column | exactly the count the CSS was written for |
| Gap between former siblings | the explicit small value, not a leftover distribution share |
| Short page: tail bottom vs column bottom | flush with the visible bottom, `position: static` |
| Long page: scroll to bottom | tail sits after the body, page scrolls normally |

The last two pull in opposite directions and both must hold at once: a
short body pins the tail to the bottom of the *visible* area without
`position: fixed`/`sticky`, and a long body lets it flow after the body.
Any fix satisfying only one is incomplete.

## Never widen one side by rewriting the shorthand

Writing the compensation into the `padding` shorthand's four-value form
(`padding: <left> <right> <bottom> <top>` with only the first slot
filled by the new value) silently emits `padding: 0px 0px 0px 21px` and
**drops the other three sides**, collapsing the element's height. The
shorthand is not a partial override; it is a full reset of all four sides.

Keep the shorthand for the base value and set the single longhand
alongside it, in this order so the longhand wins:

```css
padding: var(--space-md) var(--space-md);                              /* base */
padding-left: calc(var(--space-md) + var(--side-indent-num));          /* override */
```

Verify by reading the **computed** shorthand back, not the authored text:

```js
getComputedStyle(el).padding   // must be e.g. "12px 12px 12px 21px", not "0px 0px 0px 21px"
```

## A negative margin that extends a fill also moves the text

Pulling a highlight/active fill out to a parent guide with
`margin-left: -Npx` moves the row's **text** by `N` as well, because the
text sits inside the shifted box. Any state change driven by that
negative margin therefore shifts every label when it applies.

Compensate the label back with matching padding on the same edge — the
two cancel for the text while the background still reaches the guide:

```css
margin-left: calc(-1 * var(--side-indent-num));
padding-left: calc(var(--space-md) + var(--side-indent-num));
width: calc(100% + var(--side-indent-num));
```

Measure **text** position, not element position. Element rects are
supposed to move; the assertion the user cares about is that the glyphs
do not:

```js
const txt = (a) => { const w = document.createTreeWalker(a, NodeFilter.SHOW_TEXT);
  let n = w.nextNode(); while (n && !n.textContent.trim()) n = w.nextNode();
  const r = document.createRange(); r.selectNodeContents(n);
  return Math.round(r.getBoundingClientRect().left * 10) / 10; };
// compare txt(activeRow) against txt(inactiveSibling) in the same parent
```

Hover states that use inset `box-shadow` paint without touching layout and
so already produce zero shift — leave them alone rather than "fixing"
them, and confirm with the same probe before changing anything.

## Generalises

Anything that depends on "how many children does this have" breaks under
a `display: contents` wrapper:

| Assumes a count | Symptom when wrong |
|---|---|
| `space-between` / `space-around` | free space split into the wrong gaps |
| `:nth-child` styling | style lands on the wrong element |
| `flex: 1` on "the" child | wrong element absorbs the free space |
| `gap` accounting | expected gap count off by one per wrapper |
| **`position: sticky` on a descendant** | **the sticky element silently un-sticks** |

When a gap appears between elements that are adjacent in the DOM, count
the flattened boxes before suspecting margins.

## The same wrapper also kills `position: sticky`

The second failure mode of a `display: contents` wrapper is not layout
distribution — it is **`position: sticky` on anything inside it**. Sticky
positions against its nearest ancestor with a real box; a
`display: contents` wrapper has none, so the sticky child silently falls
back to a shorter ancestor and unpins.

**Symptom.** A sticky side column (TOC, outline, on-page nav) pins for
the first few hundred pixels of scroll, then scrolls away and never
returns — with `position: sticky` and a non-zero `top` both set
correctly. It looks like an offset-tuning problem; it is a
containing-block problem.

**The one probe that names the culprit.** Compare the element's rendered
height against its own content height:

```js
const el = document.querySelector('.the-sticky-column');
({ rendered: Math.round(el.getBoundingClientRect().height),  // ~one viewport
   scroll: el.scrollHeight })                                // an order of magnitude bigger
```

`rendered` pinned to roughly one viewport while `scroll` is huge is the
signature: some ancestor is clamping to roughly one viewport, so the
sticky range ends there. Walk the ancestor chain and read `height`,
`min-height`, **and `flex`** on every row to find which layer clamps:

```js
(() => { let el = document.querySelector(TARGET), out = [];
  while (el && el !== document.documentElement) {
    const s = getComputedStyle(el);
    out.push({ cls: el.className, display: s.display, height: s.height,
               minHeight: s.minHeight, flex: s.flex, flexShrink: s.flexShrink,
               overflowY: s.overflowY,
               box: Math.round(el.getBoundingClientRect().height) });
    el = el.parentElement; }
  return out; })()
```

**The clamp is usually `flex-shrink`, not `height`.** The default
`flex-shrink: 1` lets a flex item be *compressed below its content*
height down to whatever `min-height` allows. A row carrying a
12780px article with `min-height: 100%` therefore renders at exactly
824px — one viewport — while its `scrollHeight` stays 12780. Changing
that row's `height` to `auto` or its `min-height` to something larger
changes **nothing**, because the compression, not the declared size, is
what caps it. Injecting `height: auto !important` and watching the
rendered box stay at 824 is the confirmation. Set `flex-shrink: 0` on
the clamped row and re-measure: the box jumps to the full content
height and the sticky column holds to the bottom of the scroll range.

**Confirm by scrolling, not by reading the property.** A correct rule can
compute to the right values and still not stick. Drive the *actual*
scroll container (the `overflow: auto` ancestor — often not `window`)
through several offsets, including deep past the first viewport, and
assert the column stays in its visible band at each. If it holds at 400
and fails at 1500, that is the clamp — not the `top` value, and not worth
another round of offset tuning.

**Fix, in order:** (1) give the wrapper a real box — the same
`.body { display: flex; … }` fix as the child-count case above;
(2) set `flex-shrink: 0` on any ancestor row that is being compressed
below its content; (3) only then tune the offset. Do not stop at (1):
a `display: contents` wrapper is frequently *not* the clamp, and a
wrapper fixed on its own can leave the column still unpinning.
