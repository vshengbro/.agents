---
name: procedural-game-asset-pipeline
description: 'Use when generating game 3D assets procedurally for a renderer.'
version: 1.0.0
author: hermes-curator
metadata:
  hermes:
    tags: [blender, bpy, game-assets, procedural, pipeline, verification, json]
    related_skills: [blender-3d-modeling, hard-surface-product-modeling]
license: MIT
---

# Procedural game-asset pipeline (Blender → JSON → game renderer)

## When to Use

Load when the task is to produce **many** 3D assets **procedurally** for consumption
by a separate program — a game engine, a WASM renderer, a web viewer. Triggers:
"用 blender 建模做游戏资产", "generate a city asset set", "build N low-poly meshes
and export for my engine", "assets/*.json + a preview render for each category".

**Check whether the pipeline actually uses Blender before assuming it does.** A
project can present a `tools/blender/` path while generating every mesh from a
pure-Python geometry kernel with no bpy import at all. Read the builder module's
imports and the build entry point's invocation (a `blender --background --python`
command line means Blender; a bare `python3 build_assets.py` means it does not).
This decides whether new assets can be produced in seconds without launching a DCC
app — which changes both the cost estimate and whether the "Blender exits 0 on an
uncaught exception" trap below applies to you at all.

Sibling skills, deliberately not duplicated here:
- `blender-3d-modeling` — bpy API trivia (BSDF socket renames, `bmesh.ops`
  signatures, camera spherical coords). Read it for those.
- `hard-surface-product-modeling` — modeling a **real product 1:1** and proving it
  against a vendor photo. Read it when fidelity-to-reference is the goal.

The class-level rule that is specific to this pipeline:

**A generated asset library is a contract between two programs.** The Blender
side emits geometry; the renderer side interprets it. A verifier that only lives
on the emitting side proves the build ran, not that the consumer will get what it
expects. Two things carry the weight: a **written handoff schema**, and a
**negative control** proving the verifier can fail.

## Workflow, in order

1. **Fix the schema before writing geometry.** Write `SCHEMA.md` next to the
   output, stating per field: units, up-axis, face winding (CCW as seen from
   outside), colour range, and — critically — **origin convention per category**.
   Origin is not one global rule: ground-centre for buildings and vehicles,
   feet-centre for characters. A renderer that needs a character's feet at y=0 and
   a car's axle mid-body must be told both. Get this wrong and every instance
   floats or sinks, with no error anywhere.
2. **Build a geometry kernel module**, then per-category builder modules on top.
   Assets share primitives (rounded box, cylinder, torus, loft, transform), and
   the bug classes below live in those primitives — fixing them once fixes every
   category. Do not write each category as a standalone script.
3. **Transform eagerly and assert position.** See the immutability trap below.
4. **Verify geometry**: index bounds, winding/CCW consistency, bounds match
   recomputed extents within tolerance, ground assets rest on y=0, total triangle
   budget. Report genuinely open shells rather than hiding them.
5. **Build the negative control.** See below. Non-negotiable.
6. **Render previews per category** and assert non-blank (pixel stddev > 0).
7. **Ship a manifest** (`asset_count`, per-asset `tri_count`, `bounds`, `file`)
   so the consumer can plan memory and culling without parsing every file.

## `blender --background --python` exits 0 on an uncaught exception

The single most expensive defect in this pipeline, because it defeats every
wrapper, CI step and shell check that tests `$?`:

```python
if __name__ == "__main__":
    try:
        build()
    except Exception:
        import traceback, sys
        traceback.print_exc()
        sys.exit(1)
    print("BUILD OK: 58 assets, 68140 triangles")
```

`Blender quit` and exit 0 happen even when the script raised halfway, so a
"successful" run can have emitted half the library. The `BUILD OK` line is as
load-bearing as the `exit(1)`: it is the marker a wrapper greps to tell "finished
the work" from "crashed after most of it". Do the same for the verify and preview
scripts.

## Open surfaces must declare a reference, or the export fails

A closed shell has a signed volume, so outwardness is checkable automatically. An
**open** surface — a sail, a wing, a blade of grass, a water plane, a single-sided
decal — has no interior to measure, and a verifier that skips it silently lets an
inverted surface through. Give every open part an explicit declaration: either
every face normal must point away from a reference interior point, or every normal
must point one declared direction.

This is the most common export failure when adding asset families, and it is
**categorical, not a matter of taste**: the parts that need the declaration are
exactly the ones that read as "thin detail" in the brief (sails, wings, fins,
petals, blades, flat water). Put the rule in the worker brief with a per-asset
list of which parts are open, because discovering it from a traceback one asset at
a time is the slow path. Winding a face the wrong way on an open part is invisible
in a render from one side and correct-looking in every screenshot you take — only
the export check catches it.

Corollary: a large **water/ground plane belongs in the renderer, not the asset
library.** It is open by definition, it is enormous (a 750 m plate costs more
vertex data than the whole rest of the library), and it is usually the only surface
whose extent depends on camera far-plane settings. Generate it alongside the
existing procedural ground mesh and share that code path.

## Per-asset triangle budget is a hard gate, not a guideline

Emit a per-asset cap enforced at export time, and read the **per-category
breakdown** in the report, never just the total. A total that grew while one
requested family contributed nothing still looks like success in the summary line;
only the breakdown shows the gap. When a worker is briefed to add N assets, give it
the expected final manifest count so a family that failed to register is visible in
the output it must quote back.

Low segment counts are the lever, not lower detail: a cylinder at `seg=8` instead
of `seg=24` cuts a large asset's triangle count by two thirds with no silhouette
loss at gameplay distance, and low-poly is the house style anyway.

## The verifier needs a negative control

A passing verifier proves only that the verifier did not crash. It cannot
distinguish "every mesh is correct" from "the verifier checks nothing" — both
print `0 violations`. Write the counter-test as its own script:

```python
for mutate in (invert_faces, collapse_to_degenerate, shift_out_of_bounds, duplicate_part_names):
    assert rejects(verify(mutate(valid_asset))), f"verifier accepted {mutate.__name__}"
```

Report the rejection count. Without it, "verifier passes" is unfalsifiable and a
future session cannot tell a real PASS from a no-op. Re-run the negative control
whenever you edit the verifier, to prove you did not weaken it.

## Outwardness: weld by position, do not reason about winding parity

Two failure modes that both read as "verified":

- **Index-based manifold/outwardness testing sees nothing on flat meshes.** A
  flat sheet has 3 vertices per triangle, so an index-neighbourhood walk finds no
  closed manifold and never evaluates a signed volume — yet a flat sheet is
  exactly what is most likely to be wound wrong. Weld vertices **by position**
  into components first, then compute signed volume per component. In one build
  this took coverage from ~8% of parts to ~99.9%.
- **Parity reasoning about face winding is unreliable.** An odd permutation
  silently inverts every face of a generated shell while the result still renders
  correctly — a torus with negative signed volume looks identical to one with
  positive volume. Measure the four quad windings directly instead of reasoning
  about parity, and assert on the **sign** of signed volume for every closed
  shell.

## Immutability makes "transform" helpers silent no-ops

Helpers that translate/rotate geometry by returning a transformed copy do nothing
when the underlying coordinates are tuples. The asset builds, renders, and passes
a shape check — it is simply in the wrong place (a building 5 mm underground, a
sign floating at head height). Position is the one bug class no volume or normal
test catches, so assert it explicitly: ground assets at `abs(y) < 1e-6`, bounds
equal to recomputed extents within tolerance.

## Preview cameras must respect each asset's authored front

Authoring assets front-facing −Y and rendering from one hard-coded azimuth shows
every asset from behind. A flat sign renders as a blank panel **with healthy
pixel stddev**, so the blank-image assertion does not catch it. Frame relative to
each asset's own front direction, and sanity-check orientation per asset.

Corollary from the sibling skill, worth restating because it bites here too:
`std ≈ 0` means the camera is inside geometry or the frame is empty — that is a
framing bug, not a lighting or material problem.

## Export for instancing, not for one-off drawing

When the consumer renders many copies of one asset, per-instance vertex
duplication is the dominant memory cost. Emit **one geometry set per asset** and
have the renderer send a model matrix (+ tint) per instance. State this in the
schema so the consumer does not bake instances into the data.

Corollary: give every part a unique, meaningful `name`. Duplicate part names
across per-instance copies (1,500 of them in one measured build) make the data
unaddressable — the renderer cannot name, toggle or isolate anything.

## Fan-homage assets: never import the source material

When the brief is "make assets like <commercial game>", the deliverable is a
genre homage with **original** assets. Downloading, tracing, or approximating the
original's models, textures, audio, logos or fonts is not a shortcut — it is the
one thing that makes the result unusable. Generate everything procedurally and use
original naming (signs spell invented words). This constraint belongs in the
dispatch brief to the asset worker, not just in your own head.

## Detail emitted but never VISIBLE is not detail: ray-cast visibility, not presence

A builder can emit thousands of triangles of facade detail that no player ever
sees, and every count-based check will pass. The symptom is a flat, blank-looking
mass; the cause is geometry sealed inside other geometry.

The specific trap: **a big mass drawn as one full-height box while its own
details are placed against a stepped profile.** Windows placed at `scale(z)`
inside a box built at full width are inside the wall forever. The audit that
matters is not "how many triangles" but "what is the FIRST surface a ray hits".

    for each floor: cast a ray at the facade from outside
    owners = which parts own the outermost hit
    assert a glazing part is in owners

**Always sanity-check the instrument against a feature you KNOW exists** before
trusting a negative. A sparse ray grid will miss real windows and report them
hidden; re-run dense and confirm a sample that looked "hidden" actually has
glass behind whatever legitimately occludes it (a sign board, a balcony).

Once the real cause is found, adding more surface detail on top is wasted work
-- it lands on the same wall the player cannot distinguish. Fix the massing
first, measure visibility per floor again, then add detail.

Corollary: when a building's silhouette feature is a **setback**, emit the wall
as one box per band. A single box for the whole tower makes every band above
the first setback full width, and any detail placed at the correct inset is
invisible.

Corollary: when a detail band spans a setback, place **each element at the
scale of its own height**. Sizing the whole band to the narrowest scale it
touches pushes elements inside the wider storey below.

### The massing bug hides under a plausible-sounding surface-level cause

The setback case above is not exotic, and it recurs with a different surface
explanation each time. One pass was briefed with "the upper shaft is missing
detail" — the natural reading of a blank wall — and the real cause was the
opposite: `shaft` was a single `chamfer_box(w, d, total_h)` at **full footprint**
while its windows, courses and balconies were all placed at `scale_at(z)`.
Above the first setback the glazing was emitted at the inset and the wall never
moved, so **every one of those windows was modelled and completely unreachable**.

Measured with the ray-cast probe, per floor from the street:

```
                    before    after
bldg_deco_teal       4/9       9/9
bldg_lilac_tower     6/12     12/12
bldg_white_landmark  5/10     10/10
bldg_pink_terrace    3/7       7/7
```

For every asset declaring a setback, the first glazing-free floor was **exactly
the first floor above the first setback** — a signature that points at massing
rather than at a detail budget. Treat a per-floor visibility curve that is flat
and then drops to zero at one specific height as massing evidence.

Two more leak points in the same family, both worth checking when a tower still
reads flat after its massing is fixed:

- **Details keyed to the base footprint stand proud of a stepped crown.**
  Pilasters and upper walls sized from `w`/`d` rather than the band's own
  `scale_at(z)` poke through the setback above them.
- **Slabs sized as the average of two footprints float inside their walls.**
  A cornice spanning a transition computed as `(w_out + w_in) * 0.5` is narrower
  than the wider storey, so the roof it caps sits in an interior void. Size the
  transition slab to the **wider** of the two, or emit one per storey.

**Judge the result at gameplay distance, and expect the first fix to be partial.**
After the massing fix, vision still reported "the large front-facing shaft
immediately below that crown still reads as a broad, mostly blank wall" on the
tallest assets, with the blank fraction plateauing around 25-30% on every one. A
blank-fraction metric that plateaus is the signal that a second pass is needed
on the mid-shaft, not that the crown fix failed. And report that partial result
honestly — "the crown is fixed, floors 1-7 are not" is more useful to the next
pass than a satisfied summary.

## Report honestly

State asset count, total triangle count against the budget, per-category counts
(the aggregate hides a category that was never built — check the breakdown
against the spec, not the total), the negative-control rejection count, and the
preview paths. Name anything simplified or degraded.

When workers build asset families in parallel, each owning one new builder module,
**exactly one party owns the shared registry/manifest wiring** — otherwise two
workers editing it collide non-deterministically and the collision surfaces as a
build failure neither brief predicted. Also instruct workers to treat existing
builders as read-only and to *report* a suspected bug in one rather than editing
it; two workers independently "fixing" the same kernel primitive is a corruption
no amount of local testing will attribute correctly.
