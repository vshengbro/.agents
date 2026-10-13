---
name: spec-accurate-product-modeling
description: Model a real product 1:1 from vendor specs, prove it.
version: 1.0.0
license: MIT
author: hermes-curator
metadata:
  tags: [modeling, 3d, verification, product-design, bpy]
  related_skills: [blender-3d-modeling]
---

# Modeling a Real Product 1:1 and Proving It

## When to Use

Reach for this when the ask is to model a **real, existing, dimensioned product**
to scale — a device, an enclosure, a vehicle, a piece of hardware — and the
user wants proof of accuracy ("1:1", "ensure it matches", "verify with
screenshots"). Not for original or fantasy design, where there is no published
dimension to match.

It composes with a tool skill: use this one for the workflow and the
verification gates, and the tool skill (`blender-3d-modeling`, or an
equivalent) for that modeller's own API pitfalls.

The deliverable is not a plausible-looking render. It is a model whose measured
dimensions match the vendor's published numbers, and screenshots checked against
reference photos. This skill is tool-agnostic and applies to any CAD/mesh tool
(bpy, OpenSCAD, etc.).

## Procedure

### 1. Get dimensions from the vendor, never from the brief or memory
Product generations change dimensions while keeping the product name, so a
brief written from memory or from a prior generation is wrong in ways that are
invisible until the final assert.

```bash
curl -sSL -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) \
AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15" \
  "https://www.vendor.com/product/specs/" -o /tmp/specs.html
```
Then strip tags and read the Size and Weight block, plus the port list. Record
the source URL alongside the numbers in the project README — the numbers are
only meaningful with their provenance.

**Pitfall:** cross-check at least two independent sources when the vendor page
is thin, and record which figure disagrees. Prefer the vendor's own spec page
over third-party reviews.

### 2. Save reference photos of the real product
Fetch front, rear, bottom, 3/4, top, and a port closeup. These are the ground
truth every later check is measured against — without them you are grading
your own render against your own assumptions. Downscale each to ≤1400px on
first write; oversized images time out downstream.

**Do not settle for the brief's word "reference photos".** For a product whose
vendor ships a dedicated hardware section, the `hw_*` diagrams are worth more
than any product shot: they are straight-on, evenly lit, and dimensionally
clean, so a feature's centre can be *measured* as a percentage of the panel
width rather than eyeballed. Scrolling a product page for pretty 3/4 views is
usually wasted effort — the angles that matter live in the hardware diagrams,
not in the scroll narrative. Harvest the DOM image list first:

```bash
curl -sSL -A "Mozilla/5.0 ... Safari/605.1.15" "$VENDOR/product/" \
  | grep -oE 'https://[^"]*\.(jpg|webp|png)' | sort -u
```

If the page is script-rendered, drive a headless Chrome over CDP, evaluate
`Array.from(document.images).map(i => i.currentSrc || i.src)`, and download
the ones above a width threshold. See `references/harvesting-references.md`.

**Record feature positions as fractions, not as offsets.** A vendor diagram
read at 16.5% / 24.0% / 37.7% / 83.5% of the panel width converts to model
coordinates by `x = W/2 - (pct/100)*W` for a front elevation (image-left is
model `+X` when the camera looks from `-Y`), and the reverse for a rear
elevation. Store the percentages next to the code so the next edit is a
constant change, not a re-measurement.

**Pitfall — the vendor's own page is the primary source for *function*, and
second-hand sources are the usual source of *invention*.** A prior-generation
part or a hallucinated "status LED" is invisible in a render: the geometry is
plausible and nobody can tell. This session the model carried an emissive
front-panel LED that the vendor diagram plainly shows is a 3.5 mm headphone
jack, and a Thunderbolt-first rear row that the diagram shows is
USB-C-first. Both were caught only by looking at the vendor's own front and
rear diagrams; neither was visible as an error in the render. When the brief
does not enumerate a panel's features, get them from the diagram, not from
memory of the product line.

### 3. Build in vendor units, and pick ONE unit system
Set the scene to the vendor's unit (cm) and state `scale_length=1.0`. Mixing a
mm-domain number into a cm scene is a silent 10× error that still "looks fine".

### 4. Assert the bounding box before rendering anything
This is the gate. Print the evaluated (not raw) bounds of every mesh, compute
per-axis delta against target, and print a clear FAIL past tolerance. **Ship
this as a runnable script** so it can be re-run after every edit — see
`scripts/verify_bbox.py`.

```
  X  got   19.7000 cm  want   19.7000 cm  delta +0.000 mm  ok
  Y  got   19.7000 cm  want   19.7000 cm  delta +0.000 mm  ok
  Z  got    9.5000 cm  want    9.5000 cm  delta +0.000 mm  ok
VERIFY_OK
```

**Pitfall:** measure the *evaluated* object (`obj.evaluated_get(depsgraph)`),
not `obj.dimensions` on a base mesh with live modifiers — the two disagree and
only the evaluated one is what renders.

**Pitfall:** exclude set dressing (floor, backdrop, bounce cards, lights-as-mesh)
from the measurement. A 40cm-wide bounce card in the scene makes a correct model
measure wrong, and you will chase a bug that does not exist. Keep one `EXCLUDE`
set shared by the builder, the renderer, and the verifier.

**Pitfall — measure the part, not the scene, and make the gate measure the
part too.** A status LED standing 0.70 mm proud of the front skin and a button
glyph 0.15 mm into the rear are *designed* protrusions, so the scene envelope
is legitimately 0.85 mm deeper than the chassis. A gate comparing whole-scene
bounds against the chassis dimension reports FAIL on correct geometry forever,
and a gate that fails on correct geometry gets disabled — taking with it the
real thing it was looking for, a cutter's outer half merged into the shell.

Size the named part (`Body`) for the verdict and print the scene envelope as
informational:

```python
blo, bhi = bounds(body)
bsize = bhi - blo
print("scene SIZE %.4f %.4f %.4f   (informational)" % tuple(size))
print("shell SIZE %.4f %.4f %.4f   (the verdict)" % tuple(bsize))
```

Keep the list of legitimate offenders **printed but not judged**, and say why
in the code — the LED and the glyph are supposed to be on that list, so a gate
that fails on them is a gate waiting to be switched off. Read the check's own
docstring for what it is *for*; a file that says it hunts a cutter merged into
the shell is describing `Body`, not the scene.

**Pitfall — an unmeasured dimension is the gap nobody notices.** Every check
passed while the chassis depth was wrong by 10 mm, because every feature in the
model is laid out on the *face* and none of them depends on how deep the machine
is. Gate the envelope against the same calibration the rest of the suite uses,
and mutation-test it **per axis** — a depth no feature depends on cannot be
caught by any check that only measures features. The recipe for measuring the
box off a reference photograph, and the three wrong methods that each produced a
plausible number first, are in `references/harvesting-references.md` § "The
chassis envelope itself".

**Pitfall — boolean failures present exactly like bbox failures.** A BOOLEAN
modifier can apply with no error and still *grow* the bbox by merging the
cutter's outer half into the shell. The most common cause is non-planar n-gon
caps on a `from_pydata` loft: the EXACT solver mis-resolves their winding.
Triangulate the target before the first boolean and keep it triangulated. Guard
with `all(len(p.vertices) == 3 for p in obj.data.polygons)` — never guard on
`len(obj.data.loop_triangles)`, that cache is lazily filled and the "already
triangulated" check silently fails. Also: cutters must straddle the skin (extend
clearly outside, reach `depth` inside), and any bevel must be clamped to
`0.45 * min(sx, sy, sz)` or it self-intersects. When a cut misbehaves, print the
target's bounds after *each* cut in a stage-by-stage trace rather than
re-rendering to find out.

**Pitfall — sign conventions in sub-geometry helpers bake direction into the
arithmetic.** A helper placing a socket relative to a surface plane needs an
explicit direction parameter; front panel at `-Y` and rear panel at `+Y` need
opposite signs, and a helper written for one silently builds the other *outside*
the enclosure, inflating the bbox while every part looks individually plausible.
The tell: sub-geometry bounds stick out past the shell by roughly `depth`, in
one axis only.

### 4b. Gate every cut with a ray, never with a face-area census

A bbox of exactly the right size is compatible with a port that was never cut.
The only gate that can tell is a ray cast down the middle of each feature,
swept on a grid over the feature's own footprint:

```python
hit, loc, nrm, idx, obj, mtx = scene.ray_cast(dg, origin, direction)
depth_mm = (face - loc.y) * 10.0
```

Three rules, each of which cost a wrong verdict when missed:

- **A face-area census is not a cut test.** A boolean leaves the skin fragmented
  into thousands of small faces, so their summed area falls below the footprint
  while the surface is still 88-97% covered. "Fragmented" is not "open".
- **Never let a cutter cap coincide with the skin plane.** Centring a cutter of
  total depth `D` at `face - D/2` places its outer cap on `face` by
  construction, and EXACT reads that as a pocket, not a hole. Overshoot both
  ends: free air outside, empty cavity past the wall. A comment saying "neither
  cap lands on a face" above a span written `face - span .. face` is describing
  the opposite of the code — do the arithmetic, do not trust the comment.
- **Name the depth threshold for the defect you are hunting, and match on
  object name too.** ~0.0 mm is the skin (capped); ~1.0 mm is a socket's walls
  (correct); ~2.4 mm is the tongue (fully open). Filtering on name alone misses
  a stray sliver; depth alone calls every connector a lid. Sample the
  feature's own footprint, not the cutter's bevelled rectangle, or the aperture
  lip manufactures a false failure.

Ship it as a runnable script next to the bbox gate and give it **controls**:
one feature that must be solid, one that must be open. A control that flips is
a finding about the gate, not the model. The full ladder — the census-versus-ray
table, the isolated-repro disproof, naming the blocking object to end a search,
and reading the GLB's uncompressed JSON chunk to settle axis conventions
without a browser or a Draco decoder — is in
`references/verifying-a-cut-is-a-hole.md`.

### 5. Derive camera distance; never hand-tune it
Hand-tuned distances are the most common cause of an all-black frame. Fit the
bounding sphere to the narrower image axis instead:

```python
half_fov   = math.atan(0.5 * cam_data.sensor_width / lens)   # horizontal
half_fov_v = math.atan(half_fov * res_y / res_x)             # vertical
dist = radius * margin / math.sin(min(half_fov, half_fov_v))
cam.location = target + dist * unit_vector_from_azimuth_elevation
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
```

**Pitfall:** confirm the azimuth convention against the geometry — which angle
means "front" is arbitrary and silently yields back/front-swapped renders.
For a model with front at `-Y`, azimuth 270° is the front.

### 6. Gate renders on pixel statistics before spending a vision call
Blank or out-of-frame renders look identical in the file listing. Two cheap
statistics catch them:

```python
means = [sum(p)/3 for p in im.resize((80, 60)).getdata()]
# mean=0.0  std=0.00  -> all black: camera inside the model or lighting dead
# mean=160  std=0.25  -> flat background only: model out of frame
# mean=158  std=7.3   -> model present
```
Only send frames with real variance to vision. This caught seven bad frames in
one pass that would otherwise have each cost a vision round-trip.

### 7. Compare against the reference with an ORTHO render, not a framed perspective one

A beauty render is not a measuring instrument. Auto-framing that fits the
projected bounding box picks the wrong extent on a flat-on elevation of a
19.7 x 19.7 x 9.5 cm block and reported that chassis at **h/w 0.75 when the
true ratio is 0.48** — every band, column and proportion read from that frame
was garbage, and it looked like a plausible measurement rather than a broken
one.

For any comparison pass, render each face with an **orthographic** camera on an
axis, framed to a fixed half-extent that does not depend on the object:

```python
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cd.ortho_scale = 2 * RADIUS
# camera on a sphere; ortho makes the distance irrelevant
cam.location = (R*cos(el)*cos(az), R*cos(el)*sin(az), R*sin(el) + z_mid)
cam.rotation_euler = (Vector((0,0,z_mid)) - cam.location).to_track_quat('-Z','Y').to_euler()
```

Ortho also removes foreshortening, so a feature at 16.5% of the panel width in
the render is at 16.5% on the machine. Give the comparison pass its own flat
lighting — the studio rig is aimed at beauty shots from 30-80 cm and leaves a
dead-on face nearly unlit, which reads as "the perforations are missing" when
they are simply in shadow.

**Two harness bugs to expect, both of which produce a confident wrong number:**

- *Crop detection.* The two sources disagree about the background: vendor
  diagrams sit on white, your ortho renders on whatever world colour you set.
  "bright = object" captures the entire frame on the second. Decide which side
  the background is on from the border median, then take a narrow luminance
  band on the other side — a wide window around the metal swallowed both (the
  world read 175, the lit aluminium 163, and a 26-level window covers both).
- *Interpreting the result.* Print the chassis `h/w` first, every time. It is
  the canary: if it does not match the published proportion, the crop failed
  and no band number from that run means anything.

Then diff band-by-band against the same statistic computed from the reference
(see `references/harvesting-references.md`). Report the worst deviation as a
number. "My port band reads 68% dark where the reference reads 6%" is
actionable; "the port area looks a bit off" is not.

**Report a ZONE summary as the verdict, per-band as the diagnostic.** A single
band is only a few lattice pitches tall, so its reading depends on where the
band boundary happens to fall relative to the hole rows: at 20 bands over a
9.5 cm chassis each band is 0.475 cm against a 0.20 cm hole pitch, and the same
unchanged model scored 41% / 27% / 36% / 26% in four consecutive bands purely
from sampling phase. Averaging over a whole zone — which spans many pitches —
is phase-independent and is the number the model actually has to get right.
The per-band table is what tells you *where* a zone is wrong. Concretely:

```
zone summary (averaged over the whole zone, phase-independent)
  zone                range          apple    mine     diff
  upper perforated    5-55%          42.8      46.6     +3.9
  port band           55-70%           5.2       0.0     -5.2
  base band           90-100%         23.3      25.0     +1.7
worst zone deviation: 5.2 points
```

**Sizing a perforation lattice from a target open area.** Do not tune hole
radius by eye; solve for it. Open area is `pi * r^2 / pitch^2`, so a lattice
that must read as 42% dark needs `r = pitch * sqrt(0.42 / pi)`. Row pitch must
equal column pitch — deriving `row_dz = (z_hi - z_lo) / (rows - 1)` stretches
rows to whatever count comes out, drifts off the column pitch, and shows up in
the diff as readings that alternate down the field. Use
`rows = int(span / pitch) + 1` with `row_dz = pitch`, and anchor the first row
at the band's top edge: an expression that starts the first row at the band's
*midpoint* silently builds only the lower half of the field, and the tell is
that the perforated zone starts halfway down the panel instead of at the top.

**A recess must be deeper than the hole is wide or the holes do not read as
holes.** At 0.10 cm with a 0.071 cm hole radius, light rakes the far wall and
the openings read as grey dimples — the zone came back 31% where the geometry
opened 40%. Roughly two hole radii (0.15 cm) shadows each opening individually
while leaving the floor between them lit. Going too far overshoots into a
different defect: at 0.22 cm the whole recessed floor fell below the dark
threshold and the zone read 64%. If a perforated zone is too light, check depth
before you enlarge the holes.

**When a field covers only part of a face, scope the exclusion — a shared
taper factor will zero the wrong field.** A smoothstep `front_factor` meant to
keep the *upper* field off the front panel was applied unconditionally, which
also drove the *base* band to zero on the front and left that face solid down
to the feet while the other three were perforated. Gate any position-dependent
factor on which band is being generated at that level.

### 8. Vision-check, then cross-check the critique
Downscale to ~640px before analysis and crop to the region of interest; full
resolution times out. Ask specific, falsifiable questions ("are these ports
recessed with visible inner walls, or flat cutouts?") rather than "is this
good?".

**Pitfall — a vision critique of your own render is evidence, not verdict.**
Compare it against the saved reference photo before acting. In practice a
meaningful fraction of raised issues are wrong: critiques claimed ports should
be rotated 90° (the reference showed them correctly oriented) and demanded a
front-panel jack the vendor spec placed on the rear. Rule: **every "this is
wrong" claim must be checked against a reference photo or the spec sheet
before you change geometry.** Silently applying vision feedback turns a good
model into a wrong one.

**Pitfall — the same applies to a *user's* correction, and over-applying one
is worse than the bug.** A user reporting "the port bay's background is silver,
it should be black" names a real symptom whose cause is often not the thing
implied. The actual defect was a boolean leaving 45 faces on the recess's
back wall carrying the shell material. Painting the entire recess black fixed
the symptom by making the band 74/59/66% dark — and the reference reads 6/0/9%
there, i.e. *solid metal*. The bay is a shallow machined step whose floor and
walls are the same aluminium; only the connector mouths are dark. The band
diff is what caught it, and the worst deviation went from 67.6 to 27.3 only
after the over-correction was reverted.

Rule: **a reported visual defect gets a diagnosis, not a literal patch.**
Measure the reference at the location, decide what the correct value is, then
change geometry to reach it. When a fix pushes a measured number *further*
from the reference, the fix is wrong regardless of how well it answers the
sentence that prompted it.

**Pitfall — a recess cut by boolean inherits the cutter's material.** The
recess walls come back carrying the cutter's material, not the shell's, so
"the inside of this pocket should be metal" fails for a reason that has
nothing to do with the boolean's geometry. Assert the material of the recess
interior directly, and when the real part is one piece of metal, repaint the
whole recess back to the shell material. Verify by counting faces by material
inside the recess volume — not by looking.

### 9. Iterate on the specific defect, re-assert, re-render
Each round: fix the named defect → re-run the bbox gate → re-assert every cut
with the ray gate → re-render only the affected views → re-check. Do not
re-render the full set to look at one port.

**A gate that has been red since a prior commit hides the next bug.** A static
gate left asserting a preset table that a later commit deliberately deleted was
failing continuously, and precisely because it was permanently red nobody ran
it — so the two real bugs it would have caught (a reset button passing a metric
distance as a zoom factor, a port that was never cut) shipped under it. When a
gate fails on something the product decision deliberately removed, **fix the gate
in the same commit that removed the feature**, then mutation-test the repaired
gate: inject the bug it is supposed to catch and confirm it fails. A gate that
has never been seen to fail is not evidence of anything.

Push the defects the user raises into a **regression check** in the verify
script, so the same class of error fails the build next time. Each check should
name the invariant, not the instance: connector spacing ≥ 0.2 cm, USB shells
taller than wide, the bay floor mostly metal, the underside has exactly N
intakes, each feature within 0.35 cm of its measured position.

## Rendering as verification

Flat cutouts read as painted-on decals at any lighting. A recessed opening needs
three separate things or it will not read as depth:
- a real geometric recess (boolean, not a dark decal),
- a **bright chamfer lip** at the mouth to catch the key light,
- a matte dark liner set *deep* inside so the walls fall into shadow.

Metal needs something to reflect. At roughness ≈0.2 the shell is close to a
mirror and bare area lights give it only hotspots; large white bounce cards
off-frame produce the soft gradient streaks that read as machined aluminium.
Above ≈0.35 metal starts reading as matte plastic, the fastest way to look CG.

Edge fillets must be scaled to the *part*, and the two axes are independent.
"Everything looks like a tray with a raised rim" is an **oversized** fillet;
"the middle of the face looks like it bulges" is also an oversized fillet —
the same defect read from the other side. On a 9.5cm-tall, 19.7cm-wide
enclosure a 0.7cm fillet reads as a rimmed tray; 0.35cm reads as raw and
unmachined. The working values are ≈5-6% of the width for the vertical corner
break (1.05 cm on 19.7 cm) and ≈0.4-0.5 cm for the top/bottom edge, which is
the *softer* of the two, not a scaled copy of the vertical radius.

**When a user reports a flat face bulging, prove the geometry is flat before
touching it** — the answer is almost never the mesh. On a 19.7 x 19.7 x 9.5 cm
block, 99 front-face vertices all sat at `y = -9.8500` (spread 0.0000 cm) and
the rendered face held to 163-164 luminance across its interior (std 0.51),
while every elevation read as a pillow. The causes were a vertical corner
radius at 8.1% of the width and a corner arc tessellated at only 8 segments, so
that the fillet was a visible flat-shaded octagon. Both are one-line constants;
neither is a geometry bug.

Emissive status indicators need emission strength ≈5-6 plus a small point light
at the same position; emission alone reads as a white speck with no spill.

**A builder and its verifier must read the same constants, or the check
measures a region the model never built.** Two files each held their own
arithmetic for where a feature sits — the builder drilled a band above the
bottom fillet (a hole cannot be opened where the surface turns away from
vertical) while the verifier sampled the spec's photographic range, so 11 of
14 samples landed on solid metal by design and all four sides read 0.0% open.

The give-away is arithmetic that exists in two places for one quantity. Lift
it into the shared spec module and have both sides import it — **never by
recomputing it in the verifier**, which is a third copy and a new chance to
drift. Keep the vendor's measured value alongside the modelled one rather than
overwriting it: the honest report is "the spec says 0–7.44 mm, the builder puts
it at 5.8–13.05 mm because the fillet forbids the lower rows", and deleting
the measured constant to make the disagreement disappear loses the finding.

**When a ray gate reports exactly 0.0% open, 0.0% is the finding.** Do not open
an investigation into boolean winding: take a cross-section through the feature
and read what material is actually there. Bucket the mesh's polygon centres by
the perpendicular axis and compress into runs — a continuous run from |y| 9.60
to 9.90 where holes should be is 3 mm of solid slab, printed, with no theory
involved. High polygon density on the feature's row proves the cutter *ran*,
not that it passed through, so density alone never exonerates the geometry.
The full ladder — ruling out a stale artifact, a grid stepping over hole rows,
and a surface helper measuring an interior point, before blaming the wall — is
in `references/verifying-a-cut-is-a-hole.md` §6.

**Make the builder stamp its artifact and the gate check it.** A model file is
a build artifact, and a gitignored one (a `.blend` normally is) can be three
edits stale with nothing to say so. Stamp the builder's and the spec's mtimes
into the file at save time and have every gate print `current` / `STALE` on
every run. See `verifying-against-a-real-gate` § "A gate that cannot identify
the artifact it opened".

## References

- `scripts/verify_bbox.py` — runnable per-axis bbox gate with PASS/FAIL, run it
  after every geometry edit.
- `scripts/blender_ortho_faces.py` — six orthographic face renders, the only
  kind of render a measurement pass may use.
- `scripts/face_diff.py` — band/column pixel diff of a face render against a
  vendor reference; prints the chassis aspect canary before any band number.
- `references/harvesting-references.md` — getting a *measurable* reference
  set out of a vendor page, and reading positions and zone profiles off it.
- `references/verifying-a-cut-is-a-hole.md` — proving an opening is a real
  hole: why a face-area census lies, the coincident-cap arithmetic, using an
  isolated repro as a disproof, naming the blocking object to end a search,
  reading a Draco-compressed GLB's JSON chunk to settle axis conventions, and
  §6's ladder for a field that reads 0.0% open.
