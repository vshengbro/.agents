---
name: reveal-on-navigation-trigger-discipline
description: Use when an active item must be scrolled into view.
license: MIT
metadata:
  version: "1.0.0"
  category: frontend-dev
  related_skills:
    - euv-docs-sidebar-and-layout-fixes
    - browser-app-self-verification
    - css-layout-fix-verification
---

# Reveal-on-navigation: trigger discipline and minimum-move scroll

Two independent defects that ship together in every "scroll the active item
into view" feature — a nav rail, tree sidebar, TOC, or tab strip. Both are
invisible in code review and both are immediately visible to a user.

Trigger phrases: "sidebar scrolls on theme switch", "scroll is too abrupt",
"侧边栏滚太多", "切换主题侧边栏跳了", "just show the active item", "don't
scroll more than needed".

## 1. Bind the effect to the VALUE, not to the subscribe call

A reactive effect runs when its **signal fires**, not when the thing you care
about changed. Any re-render of the shell — theme toggle, locale switch,
resize, drawer open — re-enters the hook and fires the subscriber again with
the route unchanged, throwing the reader's scroll position back to the
active entry mid-page.

Measured: a theme toggle fired **2 scroll events** on a nav rail that was
already correctly positioned.

```rust
// wrong: fires on every set, including re-renders that changed nothing
route_signal.subscribe(move || reveal(route_signal));

// right: compare against the value last acted on
let seen: Signal<String> = App::use_signal(Router::current_route);
route_signal.subscribe(move || {
    if seen.get() == route_signal.get() { return; }   // route did not move
    seen.set(route_signal.get());
    reveal(route_signal);
});
```

Use a **framework signal** for the remembered value rather than an
`Rc<RefCell<..>>`. It keeps the module's import surface unchanged, and in a
workspace whose lints centralise imports (`use super::*;` only in keyword
files, nothing in `mod.rs`) a bare `use std::cell::RefCell;` fails audit
rules 26 and 28 — three build iterations to find out. Derive the initial
value from the same source as the live signal, not from `.get()` at a
different time.

**Enumerate the triggers that should fire, and no others.** Write them down
before coding: first mount, real navigation, container becoming visible
(drawer open). Everything else — restyle, relocalise, resize — must be a
no-op.

## 2. Scroll the minimum that reveals, not to centre

The reflexive formula centres the entry:

```
target = scrollTop + (entry.top - container.top) - (container.height - entry.height) / 2
```

Centring overshoots by construction: it moves up to half the container
height when the entry was only slightly out of view, and it throws the whole
tree to its end on the last item. Measured cold on a 7884px rail with a
682px viewport, the entry needed **0px** and the centring formula targeted
**265px**.

Move by whichever edge distance is smaller, plus a small gap:

```
above = entry.top - container.top        // positive => entry is above the view
below = entry.bottom - container.bottom  // positive => entry is below the view
delta = above <= below ? -(above + GAP) : (below + GAP)
scrollTop = clamp(scrollTop + delta, 0, scrollHeight - clientHeight)
```

Clamp **both** ends. Clamping only to zero overscrolls past the end of a
short list and can leave the entry off-view in the other direction.

`GAP` is a token, not a literal — `0` parks the entry flush against the edge
and reads as clipped rather than revealed, and a large value reintroduces
the drift the minimum move removed.

## 3. Verify the trigger and the distance separately

Two probes, because a fix that corrects one leaves the other unproven.

**Trigger.** Attach a counter to the container and drive each interaction:

```js
window.__n = 0;
container.addEventListener('scroll', () => window.__n++, { passive: true });
```

| Interaction | Expected scroll events |
|---|---|
| cold load of a deep route | >= 1 (the reveal itself) |
| navigation to another route | >= 1 |
| theme toggle | **0** |
| locale switch | **0** |
| drawer open | >= 1 |

**Distance.** Read geometry once per route and compute both candidates
arithmetically — do not measure one formula by running it, because the
page's own reveal has already moved `scrollTop` and the second reading is
taken from the first one's result. Cold-load each route so `scrollTop`
starts at 0.

```js
const above = entry.top - cr.top, below = entry.bottom - cr.bottom;
const oldT = Math.max(0, above - (cr.height - ar.height) / 2);
const newT = Math.max(0, above <= below ? -(above + GAP) : (below + GAP));
```

Report old vs new side by side. "0 vs 265px" is the evidence the user is
asking for; "made it smoother" is not.

If scroll-event listeners report nothing, do not conclude the app is broken —
see pitfall 25 in `browser-app-self-verification`. Set `scrollTop` and read
the resulting DOM instead.

## 4. A re-render is not a re-entry of intent

The same distinction generalises past scroll: any effect with a visible
consequence — focus, expansion, animation, a measured cache — needs the
same value check. A theme switch re-rendering the shell does not mean the
route changed, the user's collapsed groups were restored, or their focus
moved. Ask what the effect *means* to react to, then assert the input it
reads actually changed before letting it run.

## Related

- `euv-docs-sidebar-and-layout-fixes` — the euv-docs shell specifically
  (linkless sidebar groups, footer pinning); **this skill was written because
  that one refused a write while the index mismatch was unresolved**.
- `browser-app-self-verification` — proving you measured the build you just
  made, and the scroll-event-channel pitfall.
