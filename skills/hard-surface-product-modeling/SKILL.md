---
name: hard-surface-product-modeling
description: Use when modeling a real product 1:1 in Blender.
version: 1.0.0
author: hermes-curator
metadata:
  hermes:
    tags: [blender, 3d, product-modeling, booleans, verification, rendering]
    related_skills: [blender-3d-modeling, vision-analysis]
license: MIT
---

# Dimensionally-exact hard-surface product modeling in Blender

## When to Use

Load this when the request is to model a **real, existing product** to **1:1 /
true-scale** fidelity in Blender and to prove it with renders — enclosures,
appliances, hardware, packaging. Triggers: "建模", "model a Mac Studio / iPhone /
a real device", "1:1 还原", "match the real dimensions", "screenshot 验证",
"make it look exactly like the real one".

Do NOT load for fictional/organic shapes, car-body lofting, or general Blender
API trivia — the sibling `blender-3d-modeling` holds the BSDF socket renames,
`bmesh.ops` signatures and camera-Euler notes. Read that for those; read this
for the workflow and the failure modes below.

## The class-level rule

**Numeric dimension checks prove size. Only a render proves the model is right.**
A model can be exactly 197x197x95 mm and still have its port row mirrored, its
logo invisible, and its exposure blown to white. Every deliverable therefore ends
with: render → downscale → read back → compare against the reference → fix →
re-render. Do not report completion off a bbox audit alone.

**Nor does the object existing prove it is visible.** A perforation field can
carry tens of thousands of vertices and be completely invisible because the
shell's recess is shallower than the holes are deep — the tubes are cut, they
sit inside solid metal, and the face reads as smooth. A vertex count is a
statement about the scene graph, not about what a ray from outside meets. The
assertion that carries meaning is *a ray fired at the face returns the
feature*, and it has to be run per face, because a feature can be correctly
buried on one face and correctly open on another.

**"Every face" means every face, in the evidence — not just the render you
happened to take.** A feature that wraps a chassis, or that exists on more than
one face, has to be checked once per face by the same probe, and a pass on the
two faces you rendered is not a pass on the model. Users notice the face you
did not look at, and they are right to: a clean report on the rear plus a
silent skip of the sides is what a believable-looking excuse for an unchecked
model looks like. State per-face results, and if a face was not checked, say so
instead of implying the model as a whole passed.

**The user's stated topology wins over the reference photograph, and the conflict
gets surfaced once, not litigated.** A vendor diagram can and will show a
feature the user does not want. Confirm it once with the evidence — a magnified
crop plus a pixel statistic is enough — present the conflict, and take their
answer. Then delete the feature, including its support geometry and its
verifier assertions, and say plainly in the report which faces now deviate from
the vendor's published view.

**Why this matters procedurally:** a deleted feature leaves three things behind
that each fail a later gate on their own — a ray-probe threshold that now
asserts the old behavior, a section of prose describing the deleted feature,
and a render script whose view names still refer to it. Grep for the feature's
name across the model script, every verifier, the site copy and the render list
in the same pass you delete it.

**Zero-assertions are the right assertions here.** A face the user declared solid
does not get a low threshold; it gets `0.0`, and the probe reports the count so
a regression to "a little perforated" fails loudly instead of passing as parity.

## Workflow, in order

1. **Source the real dimensions from the manufacturer first.** Manufacturer spec
   pages are authoritative and usually state the three envelope axes. Do not
   trust a wiki/aggregator when the vendor states it. Note the source in the
   model script header so the next session can re-verify.
2. **Get real reference photographs** for layout (port order, feature placement).
   Public product photography is enough; you need a view of each face. Keep them
   in `refs/` next to the model.
   **Dig the vendor's own asset paths out of the product page** — the annotated
   hardware diagrams live there and answer layout questions no spec page does.
   The page is JS-rendered, so `web_extract` returns two images; grep the raw
   HTML for the versioned asset directory instead:
   ```bash
   curl -sSL -A "Mozilla/5.0 ... Safari/605.1.15" https://vendor.com/product/ \
     | grep -oE '/v/[a-z-]+/[\w/.-]+\.(png|jpg|webp)' | sort -u
   ```
   What to pull: front and rear hardware diagrams, a straight-on elevation, and
   anything under a `design/`, `internals/`, or `thermals/` path.
3. **Read the layout off the photos** and record the order you observed,
   including which direction is "left" from the viewer's position.
   **Overlay a percentage grid on the reference and read positions as
   fractions.** Feature extents expressed as "the solid band runs 50 %..80 % down
   from the top" transfer to the model as proportions of height, and they make a
   wrong guess obvious — an eyeballed "upper half" is unfalsifiable, whereas a
   measured split contradicts a 43 %-tall band immediately.
   ```python
   from PIL import ImageDraw
   im = Image.open(ref).convert("RGB").crop(chassis_bbox)
   d = ImageDraw.Draw(im)
   for i in range(1, 10):                       # 10 % intervals
       d.line([(0, i * im.size[1] / 10), im.size], fill=(255, 0, 0))
   ```
4. **Build the chassis as a lofted rounded-square sweep** (see below).
5. **Compute every feature position, never hand-place it.** Widths plus a fixed
   gap, walked in a direction derived from the camera side.
6. **Boolean the cavities, then assert.** See `references/boolean-safety.md`.
7. **Run a numeric acceptance test** before rendering — envelope vs spec, mesh
   health, feature order, minimum gaps, material assignment. For a recessed or
   perforated surface, a ray-cast probe across the feature (see
   `references/boolean-safety.md`) is part of this gate, not an extra.
   `scripts/acceptance_test.py` is the template and already asserts
   `CONNECTOR_H` aspect orientation and `RECESS_OBJECTS` ray spread — wire those
   two dicts in, because a transposed port and a no-op cut both pass the
   envelope check untouched.
   For any surface that is perforated on **more than one face**, add a per-face
   ray grid that reports the share of rays reaching the feature and assert a
   minimum per face. `scripts/verify_ventilation.py` is the probe. Set each
   face's threshold from the reference — or, when the user has stated the
   topology themselves, from their statement, in which case a face they called
   solid gets `0.0` rather than a token value. A product whose front panel is
   solid above the base band must fail a "front matches rear" assertion even when
   the model is perfect. See `references/per-face-features.md` before acting on
   a small non-zero residual: a ray fired at a side face can graze the
   neighbouring corner and report hits that are not a leak.
8. **Render and read it back.** See `references/render-verification.md`.

## Units: convert exactly once

Author every length in millimetres; convert with a single `MM = 0.001` at the
moment a coordinate is written into a vertex buffer. Ring builders and prism
helpers then operate in metres only.

**Why:** mixing domains inside one builder yields objects that are silently 1000x
off — a 44 mm grille became 2 m tall, an interior block 180 m across — and the
error only surfaces in the final audit, long after the geometry looked plausible
in isolation.

Add a named constant per authored length (`CORNER_R = 16.0`, `GRILLE_Z1 = 87.0`)
so the script reads as a spec sheet, and a `mesh_bbox_mm()` audit that prints
every object's world-space bbox in millimetres.

## Connector shape is not a free parameter

A connector is transposed silently. `width` and `height` are the same two
numbers in the same order in the source, and the row still looks like a row of
ports. Assert the aspect ratio per connector class instead of eyeballing it:

```python
for name, w, h, kind in LAYOUT:
    if kind in ("usbc", "tb5", "usba"):        # vertical openings
        assert h > w, f"{name} is {w}x{h}: should be a vertical slot"
    if kind in ("hdmi", "rj45"):               # wider than tall
        assert w > h, f"{name} is {w}x{h}"
```

Real-world magnitudes worth knowing: USB-C and Thunderbolt shells are roughly
**0.38 x 0.90 units** — taller than wide, a vertical rounded slot. Modelling
them at 0.92 x 0.30 is the transposed version and reads as a letter slot.
HDMI is trapezoidal, RJ45 is an octagon with a latch cutout, and an AC inlet is
a three-lobed cloverleaf. If the class has a distinctive outline, cut that
outline; a rounded rectangle for all of them is the tell that nobody looked.

**Mirror geometry across faces deliberately.** Getting the port order right
while a connector's width and height are swapped between the front and rear
rows is a real failure mode — the two rows end up disagreeing about the same
connector type. Derive both from one shared constant.

## Layout handedness

A layout list authored "in the order a viewer sees it" walks world coordinates
in **opposite directions on opposite faces**:

- Camera at **-Y** (front face) → world **+X is the viewer's right** → the first
  list entry must land at the **smallest** X (walk upward from `-total/2`).
- Camera at **+Y** (rear face) → world **+X is the viewer's left** → the first
  entry lands at the **largest** X (walk downward from `+total/2`).

**Why:** copying one face's convention to the other mirrors the layout with no
error anywhere. A cross-product settles it mechanically — `right = forward × up`
— but trust the render over the math: re-deriving the handedness by hand is
reliable only to about even odds, and a wrong answer applies without complaint.
Render the face, read the order back, confirm it against the reference.

## Lofting a rounded-square chassis

Sweep a rounded-rectangle ring up through the height and loft the rings:

- **Constant vertex count per ring.** Build with fixed `na` arc points and `ns`
  straight-segment points per side, and `assert all(len(r) == n for r in rings)`.
  Variable counts silently corrupt face indices.
- **Real quarter-round on the top edge**, not one chamfer ring:
  `a = (A - SHR) + SHR*cos(th)`, `z = (H - SHR) + SHR*sin(th)`. Shrink the
  half-extent *and* the corner radius (`R - SHR`) together so the shoulder stays
  tangent to the sidewall.
- **Tapered plinth** as two or three extra low rings at reduced half-extent, then
  step out to full width. A real tapered base is why an orthographic silhouette
  ratio lands slightly under naive W/H — **1.986 against a spec 2.074 is correct
  behavior, not an error.** Do not "fix" it.
- **Watertightness gate:** 0 non-manifold edges and positive
  `bmesh.calc_volume(signed=True)`.

## Port and cavity depth

Cut cavities ~10-12 mm deep and back them with a dark interior block whose face
sits just behind the port floor. **Shallow ports render as decals, not holes** —
a flat dark slit with no interior wall, no shadow, no rim. This is the single
most common reason a ported model looks wrong despite correct dimensions.

## A cutter is a CENTRE plus a TOTAL depth — check the extent, not the offset

Boolean helpers take the cutter's **centre**, and the depth argument is its
**full extent**, not an overshoot past the surface. Get this wrong and the
cutter never crosses the wall, which produces no opening and no error: the
socket geometry then sits just inside a closed skin and the ports render as
flat plates with a bright edge.

```python
# WRONG — centre 0.20 past the skin, total depth 0.60
#        cutter occupies y 9.75..10.35 against a 1.5 mm wall at y = 9.85:
#        0.10 mm of penetration, a tenth of what is needed
cut_from_body(body, name, x, y_face + 0.20, z, w, 0.60, h)

# RIGHT — span from outside the skin to past the wall, centre at the midpoint
span_in = WALL + 0.45
cut_from_body(body, name, x, y_face - span_in / 2.0, z, w, span_in, h)
```

**The same offset is correct on the opposite face, by accident.** With
`y_face = -9.85` the identical `+ 0.20` moves *outward*, and outward is the
direction that crosses the wall — so the rear row was right and the front row
was not, from one shared line of code. Never let correctness on one face rest
on the sign of a constant another face inverts. Derive the span from `WALL` at
every call site.

**Assert the panel was actually cut, from the built mesh.** Envelope checks and
hole-count checks both pass on an uncut panel. Measure the skin in the feature's
strip: an intact panel shows a face larger than the feature and a total area
*greater* than the strip; a cut panel shows the opposite on both.

```
before   200 faces, biggest 4.825 cm2, total 8.53 cm2   (strip 7.15) -> sealed
after   1593 faces, biggest 0.737 cm2, total 5.62 cm2   (strip 7.15) -> cut
```

Use the already-correct face of the model as the control: after a fix, the two
faces' largest-face and total-area figures should agree.

## Repaint the exterior after EVERY boolean, not once

A boolean difference hands the cutter's faces to the result, so every face a cut
creates inherits the **cutter's** material. A cavity cutter is near-black and
correctly so inside the shell; on the outside it turns a machined panel into a
black plate that no amount of light will fix.

Run the repaint once and the later cuts are missed entirely, because the
function already ran. Measured: a repaint inside `hollow_body` fixed 106 faces
and printed a reassuring line, while the ventilation fields — cut *after*
hollowing — left **73,740 faces over 202 cm² of the floor** wearing the cavity
material, and 318,533 faces once the port cuts were counted too.

**Call the repaint after the last boolean in the build, and make it idempotent
and unconditional.** It is a cheap pass over face centres; the failure mode it
prevents is the whole exterior rendering as a void. Then check the count it
prints: a run in the tens or hundreds after a grille pass is the tell that
something is still uncut.

**Boolean cost scales with body faces x cutter faces, so cut the largest field
first.** Every field a build cuts makes the body bigger for the next one. A
field placed last is cut against a body that has already absorbed every other
field. Ordering is a cost decision, not a cosmetic one: the same build went from
unfinished in 50 minutes to 14 minutes by cutting the biggest grid first and
sizing it down.

## Size a boolean lattice by OPEN FRACTION, not by reusing another field's pitch

The same hole shape and pitch reused on a second face produces a grid **3-4x
larger in face count and a third of the openness**, and a build that never
finishes. Derive the pitch from the area and the target open fraction instead:

```
pitch = sqrt(usable_area / hole_count)
r     = sqrt(open_fraction * pitch**2 / pi)
```

At 45 % open a 359 cm² floor wants a **3.87 mm** pitch with a 2.93 mm hole, not
the 1.96 mm pitch a 0.53 mm slot needs on a 19 cm band. Using the band pitch on
the floor gave 96 x 96 = 9,216 prisms at 13.6 % open against 2,304 at 45 % —
4.8x the cutter faces for a build that had to be killed at 50 minutes and 32 GB.

**Cross-check the total against any published aggregate count.** If the vendor
publishes one number covering several faces, the sum must clear it, and the
per-face split is a free design variable — that constrains the grid far more
cheaply than tuning a boolean does.

**A perimeter walk cannot express a fillet.** A walk that places holes on a
rounded-rectangle ring at a fixed height only reaches surfaces that are
*vertical* at that height, so it cannot put holes on a curved underside at all.
The usual workaround — sliding the field up to where the fillet ends — moves
the feature somewhere the reference does not show it. A flat plane with a known
plane equation needs a **grid and a third axis**, not a perimeter.

## Brand marks

Do not re-draw logos from memory. Pull the real vector art (a public wordmark
SVG), keep only the needed `<path>` elements, and import with
`bpy.ops.import_curve.svg()`. That importer creates **one object per path**, so
convert to mesh, join, and scale from **mesh vertex coordinates — `bound_box` is
stale immediately after import** and yields a wrong scale factor.

**A sub-0.1 mm step in polished metal renders as literally nothing.** A physically
correct 0.12 mm etched mark is invisible at product-shot scale. Make the relief
stand proud of the surface if it must read, and state the deviation in the
report rather than claiming exact fidelity.

## A recess may not eat the wall, and the hole depth is what remains

Two independent numbers describe a perforated recess: how far the **skin** steps
back, and how long the hole **tube** is. They are not the same quantity and
setting them equal is the single most expensive arithmetic error in this
workflow.

A cavity cutter inset by `WALL` puts the shell's inner face at `half - WALL`.
The recess is a *further* inward step of the skin, so the metal actually left
between the groove floor and the cavity is

```
metal_left = WALL - recess
tube_depth = metal_left            # a tube longer than this cuts air
```

Setting `recess = WALL` — "recess at least as deep as the wall, so the holes
cannot be blind" — erases the wall entirely: the skin lands on the cavity face,
the tube then extends into empty space, and every hole reads as **buried**. The
invariant that "feels safe" is the one that breaks it, and it is worth stating
twice because it is seductive: a recess *shallower* than the wall is the correct
and sufficient condition for the holes to open.

**Why the fix that clears one face clears all of them.** Inverting a bad sign on a
per-face mask changes the depth at the sampled point *and* the depth the loft
built, because the loft and the hole builder read the same function. So a
"per-face" symptom — this face is solid, that face reads 0 % — is frequently one
shared-value error, not one bad face. Check the shared value before you start
per-face bisection.

**When a probe says 0 % open, the tube may be aimed at the wrong surface, not
built at the wrong depth.** A verifier that fires at the nominal `±D/2` plane is
measuring the *pre-recess* skin, and after any recess change every ray starts
outside the material and reports 0 % regardless of geometry. Derive the probe's
origin from the same recess value the builder used, and make the ray a
**bounded segment** (standoff → `recess + WALL`) rather than an infinite ray:
an infinite ray that clears an open hole carries on and hits the *opposite* inner
wall, which reports the hole as closed.

**Calibrate the gate against a mesh whose answer is known, BEFORE believing its
reading on the model.** A verification script that has never met a known answer
cannot tell "the model is right" from "my measurement is right by accident", and
on a perforated panel the second case is the common one. Concretely, on one
build: a first-hit depth test read 0 %, a "first hit is not the shell" test
read 100 %, a "some hit is deeper than the wall" test read anything from 0.1 %
to 38.2 % depending on the sample, an area test read 99.4 % intact for both a
sealed panel and a panel with good holes, and a boundary-loop count read 2,611
against a design of 2,760 — a 5 % miss that reads as a pass. The loop count is
exact at 25 holes and wrong at 625 (442, not 626), so a test exercised only on
a few holes passes forever.

**Any percentage that moves 30 points when you change the predicate is not
measuring the thing.** So before reporting a ventilation figure, run the gate
on a slab with a known answer — a 10×10 quad sheet with 3 squares removed has
exactly 4 boundary loops — and extend the control to the real hole count. Also
mark a reading VOID when it leaves its own domain: a skin covering 205 % of the
band is impossible, and the tolerance that produced it had swept in the side
panels, so every number taken at that tolerance is void. Report those rows as
VOID rather than printing them, because a measurement that can silently walk
out of range is how a false pass gets through.

**The gate that survives is the one whose answer does not depend on its knob.**
Ask whether any skin triangle covers a hole centre: a 1.42 mm hole cannot
contain a whole triangle, so a continuous skin puts a face centre within a
fraction of the hole radius and an open one does not. Bucket the skin face
centres into a 2-D grid and test each lattice position — no ray, no depth, no
percentage, nothing to tune. See `references/calibrating-the-gate.md` for the
three failed gates, the calibration harness, and the point-in-grid probe.

**Test the boolean alone on a slab before debugging an 18-minute build.** A 4×4
cm box 0.15 cm thick with one 1.42 mm ten-sided prism through it, EXACT solver,
gives exactly 2 boundary loops and 15.985 of 16.000 cm² of surviving skin. That
one minute rules out the solver, the winding, the cap geometry and the coplanar
-cap case together, and localises the fault to the real build path. **And when a
control does not reproduce the failure, the hypothesis is refuted, not
confirmed** — write the source comment UNVERIFIED and commit `wip:`, because a
plausible mechanism plus a real number makes a claim that hardens into fact by
the next session.

**Sample hole centres, not a grid over the face.** A 21×21 grid across a 17 cm
panel steps ~8 mm while the hole pitch is 1.86 mm, so the grid is not aligned to
any hole and reports 0 % for perfectly open geometry. Drive the probe from the
**builder's own hole centres** and the stagger offset, and read the same rows.
For an obround or slot aperture, sample a 2-D patch per hole — a single scanline
through a 0.53 mm-tall slot can miss the opening entirely.

**Measure the band against the reference before moving it.** A bottom band that
reads 0 % gets blamed on being in the fillet, and the tempting fix is to slide
it up onto the straight section where geometry is easy. That is wrong: the
luminance profile of the vendor's own elevation puts the band at the very
bottom. Fix the tube placement, not the band's position.

## Land the gates you already earned before starting the next fix

A red gate that you are mid-way through fixing is a reason to commit the rest of
the session's verified work first, not a reason to keep iterating on it. When one
feature is the only thing red and everything else is green, push the green state
before touching the red thing — then the red thing is a cheap, isolated revert
instead of an unwind through hours of unrelated work.

The corollary is the rule that saves the iteration: **never let a fix for a red
check pass while a previously-green check goes red.** Before moving on, re-run
the full suite, not just the check you were aiming at, and compare against the
list you captured when everything was last green. Measured here: a change made
the bottom band measurably worse and simultaneously took the rear perforation
field from 53.2 % to 0.6 % — the only green check in the project. That trade is
invisible if you only re-run the one gate.

**Know the exit when the arithmetic stops moving.** After several rounds of
"change a constant, one gate improves and another regresses", the constants are
not the problem — the model of the feature is. Stop tuning numbers, write down
what is verified and what is not, and ask the user which of the two they want
preserved. Reporting "I fixed A and broke B" with numbers attached is
worth more than a sixth attempt at a plausible-looking constant.

**Offer the revert as an OPTION, never as the recommendation you then pursue
yourself.** The instinct after many failed rounds is to propose reverting to
the last green commit — and when the answer comes back "don't revert, fix it",
the cost is a day of work thrown away by a `git checkout` that was only ever
meant as housekeeping. Reaching for that reflex unprompted is the failure, not
the reverting. Propose it once, with the numbers attached; if the user says
fix it, fix it. See `filesystem-destructive-operation-safety` on why that
checkout is not undoable from inside the repo.

**"Tune a constant" is itself the diagnostic failure.** A constant change that
moves a gate by a fraction of a percent, while the geometry it claims to
control is off by an order of magnitude, means the gate is not sensitive to
the constant. Escalate the *measurement* instead of the value: when a feature
that ought to be obvious reads as absent, enumerate the cause classes and
bisect between them — placement, density, depth, orientation, and what the
probe actually samples — before adjusting any of them again.

**Print a diagnostic from inside the real builder, not a stand-in script.** A
throwaway script that re-derives the geometry and re-implements the mask
drifts from the code under test and can disagree with it about the very thing
being debugged. A temporary `_DUMP` block guarded on one specific coordinate,
injected into the build function itself, reports the values that count. Remove
it by reversing the injection — never with `git checkout`, which takes the real
edits down with it.

## One depth mask, shared by the recess and the holes

When a surface is recessed and then perforated, the recess and the hole
placement must read their depth from **the same function**, and that function
must be at full strength everywhere the holes are — tapering only across the
short arc where the feature actually stops.

Two independent implementations of the same positional logic will drift, and the
drift is silent: the recess comes out at half depth on the side faces while
the tubes are still cut to full depth, so the side faces are solid metal with
holes entombed in them while the rear looks perfect. See
`references/boolean-safety.md` for the mechanism and the assertion that catches
it.

**The mask takes the point's own `(px, py)` and the profile's half-extents — not
a single axis.** This is the single most expensive mistake in this workflow, and
three approaches in a row were tried before one held:

- `mask(py)` — a single axis. On a rounded square the rear panel and each side
  panel span the **same range of the other axis**, so `py` is identical across a
  side panel and the middle of the back. This lights up the sides and leaves the
  back bare, and it is the form the workflow examples here used to show.
- `mask(arc_s, total)` — arc length does separate the panels, but only if the
  arc is rescaled from the *inset* profile the holes are laid along onto the
  *reference* outline. Get that wrong by half a centimetre (measured: 0.56) and
  the field slides onto the side panels while still looking correct on the back.
- `mask(px, py, half_x, half_y)` — **ask the question directly**: is this point
  on the rear panel? `py` out near `half_y`, `px` inside the rear panel's
  straight width, smoothstep to zero across the corner arc. Immune to profile
  scaling because it reads the point's own coordinates.

**Gate the front corners explicitly.** A test of `px > flat` alone also matches
the *front* corners — they sit at the same `|px|` as the rear ones — and they
come back at full depth, which puts a cluster of grille vertices on the front
panel (measured: 96, at x +8.73..8.87). `if py <= 0: return 0` before any
`px` test closes it.

**When you change a mask's signature, grep every caller.** The mask has at least
three call sites — the body loft, the hole builder, and the wrapper closures
that adapt it — and changing the shape of one leaves the others passing the old
arity, which fails at build time with a `TypeError` naming the closure, not the
mask. Sweep dead constants out at the same time; three of the mask's former
supporting constants had no remaining readers and were misleading precisely
because they looked authoritative.

## State the +Y/-Y sign convention once, and gate on face placement

A box-shaped product has four faces, and a sign error on the axis that
separates them will not crash — it will build a plausible machine with the
wrong parts on the wrong faces. This cost three separate bugs in one session,
each invisible to a source-level check because the code reads fine:

* the perforated field was masked with `py > 0` and built across the **front**
  panel, while the object stayed named `RearField` and the build log printed a
  healthy hole count;
* the entire rear I/O row (AC inlet, 6x Thunderbolt, HDMI, Ethernet, 2x USB-A,
  headphone, power button, engraved icons) was cut at `y_face = +D/2`, i.e. on
  the **front**, above the 2x USB-C and SDXC;
* the ortho render's `VIEWS` list had `front` and `rear` swapped, so a
  front/rear comparison silently compared the wrong two images and the swap
  never surfaced.

What catches it, in order of how early it fires:

1. **Write the convention in the module docstring and at every `y_face`
   assignment** — `+Y = FRONT`, `-Y = REAR` — as a comment. Every later
   reader needs it and nobody remembers it.
2. **Derive `y_face` from one named constant**, never re-typed per call site.
3. **Gate on measured placement from the built blend**, not on the source. A
   per-object bbox audit that prints each object's x/y/z span in mm and flags
   anything outside the envelope finds the whole class: the grille that
   reached `y = +98.5`, the AC pins that stuck out to `-103`, the socket back
   plates 2.4 mm proud. Source review never will — `y_face - depth` looks
   correct in isolation.
4. **Ray-cast each face from outside and assert what is FIRST.** A ray fired
   at the front should hit `Body` and nothing else. This is the single most
   informative test on a model like this: it immediately reported that the
   front skin did not exist and the ray landed on the logic board, the
   heatsink and the centre spine.
5. **Assert that the named render view looks at the face it is named for**,
   computed from the azimuth. `az 90 = +Y = front`, `az 270 = -Y = rear`.
   This is a two-line gate and it catches the category where a *tool* is wrong
   rather than the model.

The related trap is `inward` parameters on socket builders: with the face
sign flipped, every `inward` in the file silently inverts, and the symptom is
a 2-6 mm depth overrun that reads like a modelling tolerance problem. Pass
`inward` explicitly, derive every offset from a single `y_at(d)` closure
rather than writing `y_face + d` and `y_face - d` in different places, and let
the bbox audit be the referee.

## A perforation is a tube along the NORMAL, not a ring in the panel plane

The most expensive silent bug in a from-scratch grille. A hole in a panel is
a circle in the (tangent, up) plane, extruded along the surface normal.
Write it in the other two axes and every "hole" becomes a flat ring lying
tangentially, extruded vertically — which looks plausible in isolation and
renders as a raised ring:

```python
rx, ry = -ty, tx                       # outward normal
# WRONG: ring's first axis on the normal, second on the tangent
verts.append((px + rx*ox + tx*oy, py + ry*ox + ty*oy, z0 + oz))
# RIGHT: ring in (tangent, up), extruded along the normal
verts.append((px + tx*ox + rx*od, py + ty*ox + ry*od, z0 + oz))
```

**How it hid:** the object exists, carries 120,000 vertices, and prints
"3038 holes" in the build log. The only symptom is the envelope — the skin
ring stands proud by exactly `hole_r`, so the field carries the model past
the published depth. Measured here: `RearField y_max` 99.21 mm against a
98.50 mm panel, a 0.7 mm overshoot that reads as a plausible tolerance error
rather than a construction bug.

**Assert the envelope per object after touching a grille, every time.** An
aggregate BBOX line only says "the model is 63 mm too tall" and sends you to
the wrong file; a per-object audit names the offender. The same cut also
breaks the per-face ray probe in a way that reads as "the holes filled with
metal".

## Walk the hole lattice in ARC LENGTH and interpolate — never snap to vertices

A hole lattice is placed by walking the panel's perimeter and dropping a hole
every `pitch` of arc length. Two mistakes in that walk produce a panel that
reports thousands of holes, builds without error, and is **almost entirely
sealed** — and both are invisible unless you count spacing rather than totals.

1. **Binary-search the cumulative-length table, then INTERPOLATE within the
   segment.** Returning `perim[lo]` snaps every hole to the nearest existing
   vertex. A rounded-rect outline subdivides only its corner arcs, so its
   straight runs are long single segments: a walk of 100 points over a 76.9 cm
   perimeter means every hole lands on one of 100 positions regardless of
   what the pitch says.
2. **Close the loop** by appending the final wrap segment's length, or the
   last stretch of the walk has zero length and cannot be interpolated.

Measured: 1.86 mm pitch resolved to **3.35 cm** hole-to-hole spacing, 20 holes
per row where the panel width admits 92, and a 0.2 mm ground-truth sweep
measured **1.1 % open against a 54.2 % design**. The mesh was flawless —
123,360 vertices, exactly `4 rings x 10 x N` — and the build log printed a
healthy "3084 holes". Only the ray probe found it.

**The mask hides the symptom, so count before you believe the count.** Because
the walk drops holes across the whole perimeter and the mask discards the ones
that land off-target, a sparse walk still yields a plausible total after the
mask: most of the mis-placed holes are silently rejected and a real lattice
looks like a reasonable number. Hole *count* is therefore not evidence of
lattice *density*.

Gate on the count that cannot hide:

```python
expected = 2 * half_width / pitch                  # holes the panel admits
verts = len(grille.data.vertices)
actual = verts / (4 * ring_segments)               # holes actually placed
assert 0.8 < actual / expected < 1.2, f"{actual} holes, expected ~{expected}"
```

Census the **distinct positions per row** and check the spacing directly —
that is the measurement that localises the bug to the walk rather than the
depth or the mask:

```python
xs = sorted({round(v.co.x, 3) for v in grille.data.vertices if row(z)})
spacings = [round(xs[i+1] - xs[i], 3) for i in range(len(xs) - 1)]
# a run of `2*hole_r` spacings is one hole's two rims; anything much larger
# than `pitch` between rims is a walk that never placed holes in between.
```

Note the rims before reading this: a single hole shows up as **two** x values
`2*hole_r` apart, so a spacing list alternating `2*hole_r` with a huge jump is
the signature of a lattice with only a few holes per row.

**Tune depth and mask only after density is right.** When a perforated face
reads near 0 % open, check the three in this order — density, then depth, then
the probe's aim — because a sparse lattice makes depth corrections look like
they work. Depth tuning against a 1.1 % lattice converges on a real hole
count and a still-sealed panel.

## Assign rotation at the primitive, never after `transform_apply`

`bpy.ops.object.transform_apply()` bakes location/rotation/scale into the
mesh and leaves the object origin at the **world origin**. Any later
`obj.rotation_euler = ...` spins the already-baked world-space mesh about
(0,0,0) and throws the part off the machine — silently, no error, and a
perfectly valid-looking object.

```python
# WRONG — applied about the world origin, after the bake
obj = add_cylinder(...)
obj.rotation_euler = vec.to_track_quat("Z", "Y").to_euler()

# RIGHT — hand the rotation to the primitive
obj = add_cylinder(name, mid.x, mid.y, mid.z, r, length, mat,
                   rot=vec.to_track_quat("Z", "Y").to_euler())
```

Measured: five heat-pipe segments ended up 63 mm **below the table**, taking
the model's height from 95 mm to 158 mm, and eleven blades per fan were
flung across the case. Give the primitive a `rot=` parameter and a
cylinder-between-two-points helper; then the bug class is closed rather than
avoided.

## Never trust that a Blender script runs

A `.blend` on disk plus a set of renders does not mean the build script ever
executed. Run it, and expect the first run to fail on something unrelated to
geometry:

- **`--python` does not add the script's own directory to `sys.path`.** A
  sibling spec-module import raises `ModuleNotFoundError` instantly. If the
  file already derives its paths from `__file__`, add that directory to
  `sys.path` before the import.
- **Node sockets change direction between versions.** Linking a node's
  *output* into another node's *input* named `"Vector"` raises `Same
  input/output direction of sockets`. Check whether the target socket is an
  input before linking.
- **A shared data table needs a consumer in every renderer.** A glyph
  primitive the offline rasteriser supports but the bpy builder does not
  fails only when the build reaches it — after the geometry, so it costs a
  full run each time. Two renderers reading one table is a guarantee only
  when both can read *all* of it.

## Frame renders on the object's extent, never on its bounding SPHERE

Fitting the bounding sphere is the standard trick and it is wrong for a
squarish enclosure. A 197 x 197 x 95 mm box has a bounding-sphere radius of
138 mm; framing that distance makes the machine overflow the frame, because
the box is far smaller than the sphere in every direction the camera looks.

Measured: the rear render came out with the object running off the right
edge — 1071 x 704 px, **aspect 1.52 against the true 2.07**. Every band
statistic taken off it was measuring a clipped frame, and the resulting table
read as a catastrophic model failure: a 99.9-point "open area" error in the
top field that was entirely the camera's fault.

Fit `max(half_extent)` and take the larger of the two distances. Then gate on
the render: assert the chassis aspect (2.074) as a canary and assert nothing
touches a frame edge. **Print the canary before any per-band number** — if
the aspect is wrong the crop failed and nothing downstream means anything.
One shared framing check serves both the Blender renderer and the offline
comparison renderer, because they fail this way identically.

## Rendering a perforated panel: three things hide it, and none is the model

Before blaming geometry for a flat-looking field, rule out the render. All
three of these produce a smooth metal panel from perfectly correct holes, and
each was fixed here while the model was still actually broken — which is how a
modelling bug survived underneath a plausible-looking render fix.

**AgX is on by default in Blender 4.x and it rolls off contrast.** It is an
HDR tone mapper: it compresses a lit metal panel and the shadow inside a 1.4 mm
perforation until they read as the same value. Measured with AgX in place,
**87 % of the pixels sat between 20 and 116 with a local spread of 1.0 out of
255** — the panel and all of its holes in one indistinguishable band. Set
`scene.view_settings.view_transform = "Standard"` (what Apple's own product
photography uses) with `look = "None"`. If a micro-feature "cannot be seen in
the render", check the tone map before touching the geometry.

**Hole walls inherit the shell's material, so the holes are polished aluminium
inside and out.** A boolean difference hands the bore walls the target's
material index. Paint them: select the faces in the thin shell part-way through
the panel's thickness — between the outer skin and the inner face, excluding
both — and assign a dark anodised material. Identify by position, not normal:
a bore wall and the panel face are both nearly perpendicular to the view, so a
normal test catches the skin too. Band the paint tightly, because a band that
reaches the skin itself turns the whole panel black.

**Metallic roughness below ~0.25 makes the shell a mirror of a dim room.** At
0.205 the panel reflected the background at nearly the same value as the bores.
Apple's shell is bead-blasted and anodised; 0.34 restores the form.

**Check the framing arithmetic before judging any closeup.** An 85 mm lens at
9 cm sees 3.8 cm across, and the chassis is 19.7 cm wide — the subject falls out
of shot, and a 10-degree elevation puts half the frame in empty background.
Derive the lens from the distance *and* the required coverage (`f = 18 * D / W`
for a 36 mm sensor) rather than picking it from the distance alone. Verify with
a 3×3 ray grid across the frame reporting what each ray hit, and remember that a
normalised image offset is a `tan`, not a length — an offset applied linearly
points the ray metres off target and reports the framing as broken when the
camera is fine.

**Prove the camera is in the render at all.** Under `--background`,
`bpy.context.collection` names a default collection that does not exist, so
linking a camera there silently does nothing, `scene.camera` stays `None`, and
every frame is blank with no error anywhere. Linking into the scene is also not
enough — Blender builds the render from the **view layer's** object list, and a
camera linked after the `.blend` was loaded is absent from the frame. Link to
`scene.collection` explicitly, then `bpy.context.view_layer.update()`, then
assert `cam.name in bpy.context.view_layer.objects` and say so loudly if not.

**Bounce cards that stand just outside the chassis will eclipse a side view.**
Cards at x = ±34 cm with the camera at 46 cm put a solid card between the lens
and a 19.7 cm machine; the subject is simply not there, and a ray probe reports
the card first. Keep them in the light paths and take them out of the camera's
with `visible_camera = False`.

**Project a known feature into the frame and read that pixel.** The
alternative — rendering, eyeballing, then guessing why — burned many iterations.
`world_to_camera_view` gives the pixel of a known hole centre; a 1.86 mm pitch
at 25.4 px, say. Then read the rendered PNG back at those coordinates and check
the local spread. A spread of 3/255 across a row where a 19 px hole sits beside
a 6 px bridge is not a lighting problem to tune, it is a statement that the
feature is not in the render. Decode the PNG in pure Python (`zlib` +
un-filter the scanlines) when PIL/numpy are unavailable.

**A flat emission render cannot show a hole.** An emission material renders
identically for the skin and for the bore walls, so a "is it there" test built
that way answers about the frame, not the geometry. Keep the real materials and
one hard light, and hide the studio so nothing else can be mistaken for the
panel.

## Exporting the model for a web viewer

glTF names its meshes from the **mesh data block**, not the object. Every
primitive created in a script carries a name like `Cube.001` or `Cylinder.004`,
so a viewer that classifies parts by name to drive show/hide, isolation and cut
planes matches nothing and the controls silently do nothing.

```python
for obj in scene.objects:
    if obj.type == "MESH":
        obj.data.name = obj.name       # before export, or names are lost
```

Assert it on the exported bytes rather than trusting the exporter — count how
many mesh names still look like Blender defaults, and check that every
primitive actually carries the compression extension you asked for:

```python
prims = [p for m in j["meshes"] for p in m["primitives"]]
draco = [p for p in prims if "KHR_draco_mesh_compression" in p.get("extensions", {})]
assert len(draco) == len(prims), f"{len(prims) - len(draco)} primitives uncompressed"
```

**A bare import specifier in a static check is satisfied by a URL, so a viewer
check written that way is vacuous.** An import map entry of `"three/addons/" →
"https://unpkg.com/three@0.169.0/examples/jsm/"` passes any check that only looks
for the string `three/addons/`, and in an offline or firewalled environment the
page then has no canvas at all — a blank frame that reads as a broken export.
Require the resolved target to be a **local relative path and the file to exist**:

```js
const target = new URL(map[name], importMapBase).href;
if (!target.startsWith('file://') && !target.startsWith(location.origin))
  fail(`"${name}" resolves off-box: ${target}`);
if (!existsSync(fileURLToPath(target))) fail(`"${name}" -> missing ${target}`);
```

**Verify the viewer in a browser, and assert on the loaded scene — not on the
page's title or the absence of errors.** The load path has three failure points
that look identical from outside: modules never execute, the GLB parses but the
camera is mis-framed, and the GLB is empty. One `page_info()` plus a DOM query
settles the first and second; a reported bounding box settles the third.

```python
print(js("({canvas: !!document.querySelector('canvas'),"
         " buttons: document.querySelectorAll('button').length,"
         " loading: document.getElementById('loading')?.textContent})"))
print(js("window.__bbox"))     # in cm, three decimals, from the loaded BBOX
```

**Derive camera distance from the loaded BBOX; a hardcoded metric distance is
tuned to one model.** An ortho half-height of 0.124 m against a 197 mm cube's
0.139 m half-diagonal crops every view, and the crop is invisible because the
object still occupies the frame — it is simply missing its edges. Store only a
framing **factor** per preset (≈1.0 for elevations, ≈0.62 for a port close-up)
and compute `distance` from `fitDistance(modelRadius(), factor)` at call time, so
a re-export at a different scale reframes itself.

Two things that read as viewer bugs and are not:

- **A metal base colour below ~0.3 renders as near-black** under the viewer's
  lighting. Anodised aluminium wants roughly `(0.385, metallic 1.0, roughness
  0.35)`; a shell authored at 0.115 base reflectance looks like a lighting
  failure and gets "fixed" by raising the light energy instead.
- **The button rig and the render rig are separate files and drift
  independently.** The front/rear azimuth swap appeared in three places before
  being caught — the mask, the ortho `VIEWS`, and the viewer's `const VIEWS`.
  One checker should parse **all three** and fail when it cannot parse any of
  them, so a rename cannot quietly remove it from the gate's scope.

## Degenerate faces are what makes a viewer flicker

Z-fighting in a web viewer is not always coplanar faces. Check for **zero-area
triangles** before hunting for duplicate surfaces: a boolean leaves slivers
whose area is below any sane epsilon, and a sliver has no defined normal, draws
as a line, and still writes depth — so every depth comparison against it is
arbitrary and the arbitrariness resolves differently on every frame.

Two checks settle it, and the negative result is the useful one:

```python
# exactly duplicated face geometry, order-independent vertex triples
# -> ZERO of them is the answer that exonerates coplanarity
# zero-area faces
sum(1 for p in me.polygons if p.area < 1e-8)      # 107,854 of 1,939,757 = 5.6%
```

**Weld first, then delete.** The doubles are separate indices recorded twice by
two different cut operations, so `remove_doubles` alone changes nothing
(1,939,757 in, 1,939,757 out) and deleting alone leaves most of them. Weld at
1 micron, then drop faces under `1e-8 cm2` (a 1-micron edge). The area
distribution has no natural cliff — 56,872 under `1e-9`, 107,854 under `1e-8`,
180,438 under `1e-7` — so the threshold is a judgement, and the judgement is
that a 1-micron edge is invisible at any zoom the viewer offers but still
participates in depth. At `1e-4 cm` on a 197 mm object the weld cannot move a
silhouette.

**Do not empty a small mesh to clean it.** A mesh whose faces would ALL be
deleted becomes an empty mesh that still costs a Draco decode pass; skipping
those instead kept the export from growing 35 % on a first attempt.

## The viewer is a second model with its own failure modes

**An opaque backdrop is a floor the viewer never draws.** `alpha: false` plus
`scene.background = <colour>` plus a matching CSS `background` on the canvas
container is three layers of the same grey. From any angle the space around the
subject is a slab at a fixed distance, so orbiting underneath the machine shows
no ground at all and it reads as floating in a void. For a product viewer,
composite over the page instead: `alpha: true`, `scene.background = null`,
`setClearColor(0x000000, 0)`, and no CSS background on the container.
`scene.environment` stays — that is a lighting source, it does not draw, and a
metal at roughness 0.2 needs something to reflect.

**A render-only control is a feature toggle on a live product.** A control that
hides part names the class the viewer keys on. If the feature is now real
geometry — a field cut into the shell rather than a separate object — the
toggle removes a piece of the body. Delete the control and its whole data path,
not just its checkbox.

## Removing code by anchor-to-anchor deletion takes what is between

Deleting a block from one anchor string to the next removes everything in
between, including helpers that were never named. Two live functions went with
a UI table, the page died with `X is not defined` on load, and the commit
message asserted they had been kept.

**The checks that pass anyway cannot see this class.** `node --check` only
parses, and a deleted function is a runtime failure; a DOM-target check misses
it when the function does not touch the DOM; a "no references to removed
names" check misses it when the removed name is still *called*. The check that
catches it is serving the directory and loading the page:

```python
# page loads, model reaches 100%, canvas is not a blank frame, mouse orbits
luma = canvas.readback(); assert luma.max() - luma.min() > 200
```

Run it against a served copy of the output directory, not by eye, and add it to
the same pass as any static check — this is the gate that would have caught it
on the first attempt.

**When a render-only view table is deleted, keep the framing maths and say the
numbers.** The opening shot still needs a camera distance; write `215/28/1.00`
where the table used to be rather than reintroducing the table.

## Reporting honestly

When the deliverable is 1:1, state what is exact and what is not. The tolerance
of a procedural model versus real machined hardware is finite: a script can match
envelope, port order and feature placement exactly, and still have visibly
pillowy corner radii that would need CAD-aligned bevels to match. Say which
items fall in that second bucket instead of letting "1:1" stand unqualified.

**A commit message is a report. Check the "what this keeps" clause before
pushing.** A "removes X, Y, Z" commit almost always has a sentence about what
stayed, because the next reader needs to know the edit was surgical. That
sentence is where a lie does the most damage: it closes off the question, so
the bug behind it survives a session. Verify each retained name by resolving it
in the file that now exists — search for the definition, not for the call
sites, because the calls are the ones that will not be there to warn you.

**Report the number the check prints, not the intent of the check.** "0 / 2760
hole centres covered" is evidence; "the rear field is open" is a summary that
can be quoted back as a pass when the envelope half of the conjunction was
never evaluated. When a gate has two halves, print both in the commit.

**Contradictory evidence is a finding, not an inconvenience.** If every local
check says the model is right and the user says a feature is missing, the
disagreement IS the result. Do not restate the local checks — they are
already known to pass — go look at the artifact. Every time this bit, the local
checks had passed and the user was describing something the checks cannot see:
a port that was never cut, a page that threw on load, a face drawn on solid
metal. Opening the artifact is one tool call; asserting a check's result again
is zero.

## Support files
- `references/boolean-safety.md` — why a DIFFERENCE boolean silently empties its
  target, how to bisect it, the computed-layout pattern that prevents it, the
  shared-depth-mask rule that keeps a recess from entombing its own holes, the
  geometry-keyed panel mask that actually separates a rear panel from a side
  panel, the `tube_depth = WALL - recess` relation and its range assertion, and
  the four ways a ray probe of a recessed field reports 0 % for healthy
  geometry.
- `references/calibrating-the-gate.md` — the three gates that each returned a
  confident wrong answer on a perforated panel (ray depth predicates, area
  fraction, boundary-loop count), the known-answer slab harness that catches
  them, the threshold-free hole-centre probe, why a control that does not
  reproduce a failure refutes the hypothesis instead of confirming it, why a
  sound probe on the builder's own coordinates still reads 0 % on an open
  panel, and the envelope-and-openness conjunction with the four verdicts.
- `references/per-face-features.md` — telling a real leak from a ray that grazed
  a neighbouring panel, the flat-region vertex census that has no such artifact,
  and the procedure for deleting a feature the vendor's diagram shows but the
  user does not want.
- `references/render-verification.md` — studio lighting/exposure setup, numeric
  exposure triage, and the render→downscale→readback loop.
- `scripts/acceptance_test.py` — a PASS/FAIL harness template for envelope vs
  spec, mesh health, feature order, gap minima, and material assignment.
- `scripts/verify_ventilation.py` — per-face ray grid proving a recessed or
  perforated field is on the faces it belongs to, with per-face thresholds, hit
  coordinates for distinguishing a leak from a corner graze, and the
  flat-region vertex census.
