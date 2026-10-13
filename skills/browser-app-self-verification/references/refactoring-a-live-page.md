# Refactoring a live page without breaking it

Removing a control from a page that is already deployed is a small edit with a
large blast radius: the control is usually wired to state, to a classification
pass, and to a keyboard handler, and the region of source around it can hold
helpers that have nothing to do with the control at all.

The failure is silent at every static gate. This file is the gate that is not
silent.

## Cut by named construct, not by anchor-to-anchor range

The tempting edit is "delete from the line before the control to the line after
it". That is a range delete, and a range delete takes everything between the
anchors — including functions defined just above or just below the control that
are used elsewhere in the file.

Concrete shape of the bug: a `VIEWS` table of camera presets was removed, and
the edit spanned the framing helper defined immediately above it and the render
loop's tween state immediately below it. Both were still called from the parts
of the file that survived:

- a `setView()` function invoked on load called the deleted framing helper, so
  the page threw on the first frame and never drew anything;
- the render loop read a deleted `tween` binding on every frame, so it threw
  again the moment the first was fixed.

Two errors from one edit, revealed one at a time, because the first one masked
the second.

**Enumerate the dependency edge before cutting.** For each function you intend to
remove, find every call site; for each helper that remains, find its
definition. The check is mechanical:

```
# what still calls it
search the file for each name being removed
# does it still have a definition
search the file for each name a surviving line calls
```

Do the second one over the names the first one finds, transitively. A name
that is called and has no definition is the whole bug class.

**Keep helpers that surviving code needs, and say in the commit that they
stay.** The commit message for a removal should list what was kept as well as
what went, because the next reader's first question is exactly "was this
surgical". Write that sentence only after verifying it — see the reporting
rule in SKILL.md pitfall 15.

## Sequence a control removal

Removing a control has three layers, and the middle one is the one that rots:

1. **Markup** — the HTML block and its event binding.
2. **Data path** — the state array, the classification branch that fills it,
   and the load counter. A checkbox that hides a part is keyed on a *name
   pattern*; if the feature has become real geometry rather than a separate
   object, the toggle now removes part of the body rather than revealing a
   view.
3. **Side effects at init** — anything the control's initial state changed on
   startup. A control that starts hidden often has a line in the reset path
   that hides something else as a side effect, and that line survives the
   markup removal and keeps its target invisible.

After the edit, the dead layer 2 and layer 3 references are harmless today and
actively misleading in six months, when someone re-adds a checkbox and the
branch quietly half-works. Remove all three, or none.

**Deleting a preset table does not mean deleting the maths.** Camera framing
still needs a distance on the opening shot. Substitute literals for the table
lookups and keep the derived-framing helper, which is the part that adapts to
a re-export at a different scale.

**Give the surviving shot named constants, and use them at every call site.** A
preset table goes away, the literal tuple is pasted in at two places, and the two
drift. Here the opening shot existed as a literal in the init path and again in
the reset handler, where a third argument was pasted from the deleted table's
**metric distance** into a parameter that had been converted to a relative
**zoom factor** — so the reset button zoomed the camera to 42% of the opening
framing. The bug is invisible in both places: each call site reads plausibly.

The rule is that a magic number appearing in two places is already a defect, and
a number whose *unit* changed during the edit is a trap. Name it once:

```js
const OPENING_AZ = 215, OPENING_EL = 28, OPENING_FIT = 1.00;
setViewImmediate(OPENING_AZ, OPENING_EL, OPENING_FIT);   // init AND reset
```

Then assert on the **shared** constant, not on each literal: a static gate that
greps for `1.00` twice is checking two independent strings, while one that
requires both call sites to name `OPENING_FIT` also catches a call site that
reverts to a literal. And scan **code lines only** — matching whole-file text
trips the gate on the comment that explains the old bug, which teaches the next
reader that the gate is unreliable.

**Assert units at the boundary where they are defined.** Any function that takes
a distance, a factor, or a multiplier should say which it is in its own name or
docstring (`fitDistance` vs `distanceTo`). A parameter whose unit is only
implied by its call sites is a unit-mixing bug waiting for the first caller
whose mental model differs.

## The gate: serve it and load it

One call, no new harness. Serve the output directory over a local static server
on a port nothing else is using, load the entry page, and assert the three
things a static check cannot reach:

```python
goto_url("http://127.0.0.1:PORT/viewer.html")
wait_for_load()

# 1. no exception on load or on the first frames
print(js("window.__errors || 'none'"))

# 2. the app reached its own ready state
print(js("document.getElementById('loading')?.textContent"))

# 3. something is actually drawn — a blank frame has no variance
#    (read GPU canvases inside requestAnimationFrame)
```

The third assertion is the one that catches a page which loads cleanly and
renders nothing — the failure mode where the DOM is fine, no error is logged,
and the user sees an empty box. Mean luminance and a variance check distinguish
it from a real render:

```js
// downscale the canvas into a 2D context and read it back
const t = document.createElement('canvas'); t.width = 120; t.height = 60;
const g = t.getContext('2d');
g.drawImage(glCanvas, 0, 0, 120, 60);
const d = g.getImageData(0, 0, 120, 60).data;
// min/max/mean over RGB, then assert (max - min) > 200
```

Serve from a copy, not the working tree, and never the deployed origin: the
deployed origin is a separate proof (it has its own rewrite and cache failure
modes) and it is the wrong place to discover a local regression.

Run this before committing, every time a page's source changes. It costs about
a minute and it is the only check in the loop that can see a name which is
called but no longer defined.

## When the user reports something the gates all passed

Do not re-run the gates, and do not restate that they passed. The disagreement
*is* the result, and it is worth more than the checks.

Go and look at the artifact. Then report which side you checked and what you
found, in one line. Two sub-cases worth naming in the write-up:

- **The checks were blind** — the thing is outside what they measure (a
  geometry cut, a rendered face, a control's initial side effect).
- **The user is looking at a different artifact than you are** — a stale
  deploy, a cache, a build that did not run. Establish that before
  re-verifying anything, because every check you run is then about the wrong
  bytes.

The one thing not to do is choose a side silently. "All checks pass" in a
report whose user is looking at a broken page is a statement that is worse than
no information, because it invites the reader to distrust every other number in
the same message.
