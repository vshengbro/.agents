# Boolean safety

## The failure

A Blender `BOOLEAN` modifier with `operation='DIFFERENCE'` and `solver='EXACT'`
can return an **empty mesh** and raise nothing. `bpy.ops.object.modifier_apply()`
succeeds, the `.blend` saves, and the object is simply gone by the next line.

The trigger is **degenerate input geometry in the cutter**: two cutter solids
that share a face plane exactly, or one that overlaps another. The EXACT solver
cannot resolve a zero-thickness or self-intersecting configuration and bails to
nothing.

**Why it costs so much time:** the script runs clean, the exit code is 0, and the
symptom surfaces much later as "the model is invisible" — which reads as a
rendering or camera problem, not a geometry one.

## The quieter failure: a boolean that succeeds and cuts nothing

The emptied-target failure above is loud enough to find. **A DIFFERENCE boolean
can also apply cleanly, leave the target intact, and remove nothing at all.**
Three cutter placements, none of them an error:

| cutter position | result | loud? |
|---|---|---|
| tangent to the skin (touches, does not cross) | no cut | **no** |
| entirely inside the target (never reaches the surface) | no cut | **no** |
| proud of the skin (crosses it) | cuts; the part outside survives as new geometry | yes, via bbox |

Only the third is visible, and only as a bbox that grew by the overshoot
(measured: a cutter 0.40 mm proud inflated the box by exactly 1.16 mm).

**Why this is expensive:** the two quiet cases still pass an envelope check.
The bbox is unchanged, nothing raises, and the render simply shows a smooth
unfeatured face — which reads as a lighting or camera problem, so you go
re-tune the render instead of the geometry. On a recessed band this burned
roughly a dozen render iterations before a ray probe found it.

**Rule: for any recess, boolean, or cutout, assert the cut happened** — never
infer it from "the modifier applied without error".

```python
# Ray-cast across the feature. A real recess makes the hit distance VARY.
dg = bpy.context.evaluated_depsgraph_get()
hits = []
for i in range(-6, 7):
    o = Vector((x0, far, z_lo + i * step))
    hit, loc, nrm, idx, obj, mtx = bpy.context.scene.ray_cast(dg, o, d)
    if hit:
        hits.append(((loc - o).length, obj.name))
spread = max(d for d, _ in hits) - min(d for d, _ in hits)
assert spread > tol, f"surface is flat across the feature: spread {spread:.3f}"
```

A constant hit distance over the feature's full extent means nothing was cut,
whatever the modifier reported. Also print `len(target.data.vertices)` before
and after each cut — a no-op cut leaves it *unchanged*, which is a one-line tell
in a stage-by-stage trace.

## Model recesses in the loft; reserve booleans for real cutouts

A recess that follows the same profile as the body — a band, a groove, a
perimeter step — is cheaper and safer as an extra per-level inset in the loft:

```python
def recess(z, front_factor=1.0):
    if BAND_Z0 - 1e-6 <= z <= BAND_Z1 + 1e-6:
        return DEPTH * front_factor
    return 0.0

for z in levels:
    base = fillet_inset(z, z_lo, z_hi)
    prof = rounded_rect(hx - base, hy - base, R_VERT - base)
    for px, py in prof:
        d = base + recess(z, mask(py))     # mask -> smoothstep, position-aware
        verts.append((px / (hx - base) * (hx - d), py / (hy - base) * (hy - d), z))
```

Two rules that make it work:

- **The inset must be a function of position around the perimeter, not only of
  height**, when the feature wraps partway. A mask that is 1.0 on the rear and
  0.0 on the front is what keeps one face solid while the other three are
  recessed — **but the taper must be short.** A mask that smoothsteps across the
  whole perimeter is the trap, and it is worse than having no mask at all: the
  side faces land at 0.5 of full depth, so a recess that should be 0.15 units
  deep is 0.075, and anything cut to full depth is now inside solid material.
  Ramp to full depth over a short arc (measured from the far end of the front
  gap) and hold it for the rest of the perimeter, so only the corner beside the
  panel you are keeping solid tapers.
- **The mask takes the point's own `(px, py)` and the profile's half-extents,
  never a single axis and never a bare arc length.** `mask(py)` cannot separate
  the rear panel from a side panel: on a rounded square both span the same range
  of the other axis, so a `py` mask lights up the sides and leaves the back
  bare. Arc length separates them only after rescaling the *inset* profile's arc
  onto the *reference* outline, and half a centimetre of error there (measured:
  0.56) moves the field onto the side panels. Ask directly instead:

  ```python
  def panel_mask(px, py, half_x, half_y, fade_arc):
      """1.0 on the rear panel, 0.0 on every other face."""
      if py <= 0.0:                 # the FRONT corners share the rear |px|
          return 0.0
      t = (half_y - py) / (2.0 * half_y)       # 0 at the rear face, 0.5 at a side
      flat = max(0.0, half_x - R_VERT)         # rear panel's straight width
      if px > flat:                            # on the corner arc
          u = min(1.0, (px - flat) / R_VERT)
          t = 0.5 * u
      if t <= 0.0:
          return 1.0
      span = fade_arc / (2.0 * half_y)
      if t >= span:
          return 0.0
      v = 1.0 - t / span
      return v * v * (3.0 - 2.0 * v)           # smoothstep
  ```

  The `py <= 0.0` guard is not decoration. Without it the front corners match the
  `px > flat` test at the same `|px|` as the rear ones and come back at full
  depth, which plants a cluster of grille vertices on the front panel (measured:
  96, at x +8.73..8.87).
- **The recess and the hole placement must call the same mask function.** Two
  copies of this logic — one inline in the loft, one in the hole builder —
  guaranteed to drift. Change one and the other keeps the old behaviour, and the
  result is a model where the recess is shallower than the holes on exactly the
  faces you did not re-verify. Extract one function and have both call sites use
  it. When you change its signature, **grep every caller** — the hole builder
  receives it through an adapter closure, so a shape change there fails at build
  time with a `TypeError` naming the closure, not the mask.
- **Apply the same cut-off threshold to the recess and to the holes.** Both call
  sites drop the field below one factor (0.5 here) and zero it. Without a shared
  threshold the recess runs wider than the holes, leaving a shallow unperforated
  channel off the back onto the sides — invisible from head-on, obvious in
  raking light.
- **Sort and dedupe the level list.** A band's top edge often lands above the
  midpoint; appending its levels before the straight band and the top fillet
  leaves the list out of order, the loft folds through itself, and the only
  symptom is a bounding box several centimetres short in Z — no exception.

## Probing a recessed perforated field: the probe has the same arithmetic

A ray probe is only as correct as the surface it aims at, and a recess makes the
nominal face plane the wrong target. Four rules, each of which independently
turns a healthy field into a reported 0 %:

**Aim at the recessed surface, not at `±D/2`.** The loft steps the skin back by
the recess, so the material a ray must enter is at `half - recess`. Firing from
`±D/2` with a short reach stops in air and reports the field closed. When a
recess constant changes, the probe's origin and reach must change with it, and
the reach should be `recess + WALL` plus a margin — not a fixed length.

**Use a bounded segment, never an infinite ray.** `scene.ray_cast` with no
distance is wrong in both directions: a ray that stops in the groove floor calls
an open hole closed, and a ray that clears an open hole continues and hits the
**opposite inner wall**, which calls it closed a second time. Start a small
standoff outside the surface, march in, and stop at `recess + WALL`.

**Sample the builder's hole centres, never a uniform grid.** A 21×21 grid across
a 17 cm panel steps ~8 mm against a 1.86 mm hole pitch, so it lands between
holes and reports 0 % for geometry that is fully open. Import or re-derive the
lattice — pitch, stagger, and the row count — and fire at the centres. For an
obround aperture, sample a small 2-D patch per hole: the openings are ~0.53 mm
tall and a single scanline can pass between two rows and between two edges,
missing the void entirely.

**Fire into the wall along the local normal, on each face's own axis.** A
rear-face ray is along `±Y`; a side-face ray is along `±X`. A helper that
measures the hit's Y on a side ray finds only the corner it grazed and concludes
the face is sealed.

```python
DEPTH   = WALL - recess                    # the metal actually left
reach   = recess + WALL + 0.02              # from just outside the skin
origin  = half - recess + 0.01              # standoff, along that face's axis
opened  = sum(1 for c in hole_centres if not blocked(origin(c), axis, reach))
assert opened > 0.5 * len(hole_centres), f"{opened} of {len(hole_centres)} open"
```

The design duty cycle is `pi * r^2 / pitch^2` for a round hole; compare the
measured open share against it rather than against a round number, and expect
the measurement to land a few points under the design value because the tube's
own rim occupies part of each aperture.

## Before blaming depth: census the lattice, because the mask hides a sparse walk

A probe reporting ~0 % open is consistent with four unrelated causes — holes
buried, probe aimed at the wrong plane, holes too small, or **holes never
placed**. The last is the most expensive because the hole *count* looks
correct, and it masquerades as a depth problem for as long as you keep tuning
depth.

Holes are placed by walking the perimeter and dropping one every `pitch` of
arc length. If that walk returns the nearest **vertex** instead of interpolating
within the segment, every hole snaps to the outline's existing vertices — and a
rounded-rect outline subdivides only its corner arcs, so its straight runs are
long single segments. A 100-point walk around a 76.9 cm perimeter places holes
at 100 positions no matter what the pitch says.

The mask hides it: the walk drops holes across the whole perimeter, the mask
discards the off-target ones, and a sparse walk still yields a plausible total
after filtering. So **count before believing the count** — hole count is not
evidence of lattice density, and a healthy total is exactly what a broken walk
produces.

```python
# 1. Holes placed vs holes the panel admits.
expected = 2 * half_width / pitch
actual   = len(grille.data.vertices) / (4 * ring_segments)
assert 0.8 < actual / expected < 1.2, f"{actual} placed, expected ~{expected}"

# 2. The measurement that localises the bug: distinct positions per row.
xs = sorted({round(v.co.x, 3) for v in grille.data.vertices if same_row(v)})
spacings = [round(xs[i+1] - xs[i], 3) for i in range(len(xs) - 1)]
```

Read the spacings with the rim geometry in mind: one hole contributes **two**
x values `2*hole_r` apart, so a spacing list alternating `2*hole_r` with a much
larger jump is the signature of a row holding only a few holes. Measured here:
a 1.86 mm pitch resolving to 3.35 cm between positions, 20 holes per row where
92 fit, and 1.1 % open against a 54.2 % design — with a flawless 123,360-vertex
mesh and a build log reporting 3,084 holes.

Order the diagnosis **density, then depth, then the probe's aim**. Depth
corrections applied to a sparse lattice produce a real hole count and a still
sealed panel, and each one costs a full rebuild.

## Recessed but entombed: the failure this prevents

A perforation field cut to a fixed depth and a recess lofted to a fixed depth
are two independent numbers. If the recess is the shallower one at any position
around the perimeter, the holes at that position are **inside the shell** — the
field object carries its full vertex count, the envelope is exactly right, and
the face renders as smooth bare metal.

**The inverse error is the one that looks safe.** A recess *deeper* than the wall
`WALL` lands the skin exactly on the cavity face, erasing the shell; the hole
tube, sized `WALL` from the nominal surface, then starts in air and reaches
nothing. The self-check that requires `recess >= WALL` — reasoning that a hole
cannot then be blind — is what enforces this. The correct relation is
`tube_depth = WALL - recess`, and it must be asserted as a **range**
(`0 < recess < WALL`), not as a lower bound on the recess alone. Measured here:
a band set to `recess = WALL` produced tubes spanning -9.850 to -9.775 against a
cavity face at -9.700, leaving 0.075 cm of metal never cut, and a field that had
been passing at 53.2 % open dropped to 0.6 % the moment the same value was
applied to the rear field.

Diagnose it by measuring rather than by reading: print the tube's min/max extent
along the normal, the skin position, and the cavity face, then subtract. A tube
that stops 0.075 cm short of the cavity is not too long, it is 0.075 cm too
**short** — the opposite of the intuition that "the holes are too deep".

A measurement taken through a neighbouring hole is not a wall measurement. When
probing thickness, pick sample points that miss the lattice, or a tube standing
in the path returns the tube's own face and inflates the apparent wall.

Nothing in the graph, the bbox, or a render at a glance catches it. The probe
that does is a ray grid fired at each face, counting how many rays return the
feature object:

```python
for label, org, d, axis in FACES:              # one entry per face
    d = Vector(d); total = grille = 0
    for iz in range(21):
        z = Z_LO + (Z_HI - Z_LO) * iz / 20
        for ia in range(21):
            a = -9.4 + 18.8 * ia / 20
            o = (Vector((a, org[1], z)) if axis == "x" else Vector((org[0], a, z)))
            hit, loc, nrm, idx, obj, mtx = sc.ray_cast(dg, o, d)
            if hit:
                total += 1
                if "Grille" in obj.name: grille += 1
    print(label, grille, "/", total)
```

Two things make the difference between this probe and a pixel scan of a render:

- **Report the object each ray hit, not a dark-pixel count.** A dark-pixel
  threshold on a shaded render cannot tell a hole from a shadow, and on a side
  face the holes are seen edge-on so they do not darken much at all.
- **Hide the studio objects first, and shoot from outside the scene.** Bounce
  cards sitting between the camera and the subject absorb every ray and the
  face reports 0% — which looks identical to the real bug and sends you hunting
  in the geometry again.

**A ray grid fired normal to a side face grazes the rear corner arc and reports
hits that belong to the rear panel.** A 2-3% residual on a face you believe is
solid is usually this, not a leak: every hit sat at y = 8.46..9.40, i.e. inside
the rear panel's own extent, reached past the corner. **Print the hit
coordinates, not just the count** — the count alone cannot tell a 3% leak from a
3% graze, and acting on it sends you re-tuning a mask that is already correct:

```python
for label, org, d, axis in FACES:
    for iz in range(GRID):
        for ia in range(GRID):
            ...
            if hit and FEATURE_SUBSTR in obj.name:
                print("    %-9s y=%6.2f z=%5.2f  %s" % (label, loc.y, loc.z, obj.name))
```

**Pair the probe with a direct vertex census on the face's flat region.** This is
the check that has no artifacts in it, and it settled the question when the ray
grid was ambiguous — count feature vertices whose other-axis coordinate is inside
the panel's straight width, excluding the corner arcs entirely:

```python
flat = [v for v in feature.data.vertices if abs((M @ v.co).y) < FLAT_HALF]
assert not flat, f"{len(flat)} grille vertices on the side panel's flat face"
```

Do not classify a vertex by "which coordinate is larger" to decide its face.
`abs(x) > abs(y)` calls the rear panel's own corner vertices LEFT, because the
rear panel runs the full width including the corners; the same mistake turns a
correct model into a 2460-vertex false alarm.

Thresholds belong in a dict keyed by face. A face the user declared solid gets
`0.0`, not a token value — the probe still prints the count, so a regression to
"a little perforated" fails loudly instead of passing as parity.

## Detection

**Compute feature positions from real widths plus a fixed gap. Never hand-place
coordinates.**

```python
GAP = 3.2
LAYOUT = [(8.40, 'usbc'), (8.40, 'usbc'), (8.40, 'usbc'), (8.40, 'usbc'),
          (16.0, 'rect'), (18.0, 'ac'), (12.5, 'rect'), (12.5, 'rect'),
          (15.5, 'rect'), (7.60, 'circ'), (8.00, 'circ')]

def positions():                       # left->right as a viewer at +Y sees it
    total = sum(w for w, _ in LAYOUT) + GAP * (len(LAYOUT) - 1)
    x = total / 2.0
    out = []
    for w, kind in LAYOUT:
        out.append((x - w / 2.0, w, kind))
        x -= w + GAP
    return out
```

Then **assert the invariant** in the acceptance test:

```python
edges = sorted((c - w/2, c + w/2) for c, w, _ in positions())
min_gap = min(edges[i+1][0] - edges[i][1] for i in range(len(edges)-1))
assert min_gap > 0.01, f"degenerate port gap: {min_gap}"
```

Hand-placed constants are what create the trap: a 15.5 mm HDMI at X=-57.5 ended
its edge at exactly -65.25, which was also the USB-A edge, and the 8.0 mm power
button at X=-76.5 overlapped the 7.6 mm jack by 0.75 mm. Both are invisible in
source review and fatal to the solver.

**Assert immediately after every boolean**, not in a final audit:

```python
assert len(ob.data.vertices) > 0, f"{ob.name} was emptied by the boolean"
```

Also guard the bbox helper itself so the failure names the object:

```python
def mesh_bbox_mm(ob):
    vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
    if not vs:
        raise RuntimeError(f"{ob.name} has no vertices")
    ...
```

## Bisecting a bad cutter

When a combined cutter empties the target but each group seems fine, bisect by
**cumulatively adding** cutter groups — the interaction often only appears at
scale:

```python
for n in range(1, len(GROUPS) + 1):
    reset_scene()
    body = build_body()
    V, F = [], []
    for _, fn in GROUPS[:n]:
        fn(V, F)
    cut = mesh_from(V, F, "C")
    faces = len(cut.data.polygons)      # capture BEFORE the boolean consumes it
    boolean(body, cut)
    print(n, GROUPS[n-1][0], faces, len(body.data.vertices))
    if not len(body.data.vertices):
        print("culprit:", GROUPS[n-1][0]);  break
```

The last group added before the vertex count drops to 0 is the culprit — and
note it can be a group that passed in isolation, because the failure is in the
*combination*. Also print each cutter's own signed volume and non-manifold edge
count; an island with **negative** signed volume is inverted and will poison any
boolean it enters.

## Hygiene around the boolean call

- `bpy.data.objects.remove()` invalidates every reference to the object, so
  capture `len(ob.data.polygons)` **before** a boolean that consumes the cutter.
  Otherwise the log line itself raises `ReferenceError: StructRNA of type Object
  has been removed`.
- `bpy.ops.wm.read_factory_settings(use_empty=True)` wipes the entire file —
  never call it inside a helper another script imports. Snapshot existing objects
  and import into a scratch collection.
- Guard the entry point with `if __name__ == "__main__":` so a test harness can
  `import` the module without triggering the full build.
- `bpy_prop_collection.__contains__` expects a **string**, not an object, so
  `o not in bpy.data.objects` raises `TypeError`. Snapshot `set(bpy.data.objects)`
  before running an operator instead.
- `hide_viewport = True` is not enough for a ray probe — `scene.ray_cast`
  evaluates the **original** meshes by default. Pass the evaluated object, or
  remove the studio objects, or the bounce card you thought you hid keeps
  answering rays.
