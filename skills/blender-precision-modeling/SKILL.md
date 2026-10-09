---
name: blender-precision-modeling
description: 'Model real-world objects in Blender headless with bpy to a measured quality bar: millimetre-accurate dimensions, watertight topology, calibrated exposure, and a score-gated verify/iterate loop. Ships a 716-item world-object catalog across 42 domains, a bkit construction toolkit, a bounded-concurrency batch runner, and a deterministic + vision scoring harness. **Any task that asks to model, render, or review a 3D object in Blender — or to build a catalog of objects — must load this skill before writing the first line of bpy code.** Keywords: blender, bpy, 3d model, procedural model, mesh, lathe, loft, render, studio lighting, watertight, manifold, model catalog, 3d asset, product render.'
---

# Blender Precision Modeling

Build an object so that it is **dimensionally right, topologically sound, and
worth looking at**, then prove it with numbers and renders instead of asserting
it. The catalog of what to build is enumerated here: **716 objects in 42
domains**.

## When this applies

- Modelling any real-world object in Blender, headless or otherwise
- Building or extending a library of 3D models
- Setting up product/technical renders that have to look consistent
- Auditing an existing model for dimensional or mesh defects

If you only need a one-line bpy reminder (socket renames, `bmesh.ops` gotchas),
the older `blender-3d-modeling` skill is enough. This skill is for work where the
result has to be **verifiably** correct.


## Status of the shipped catalog

| | |
|---|---|
| Catalog | 717 items / 42 domains, all present and indexed |
| Objective gate (55 pts, deterministic) | ~99% at 55/55 |
| Vision gate (45 pts, judged) | **0 models at 45/45** — mean 28.5, best 36 |
| Regression tests | 30 in `scripts/test_bkit.py` |

**"All models exist" is not "all models pass."** Existence is tracked from the
filesystem; the objective half is measured by `scripts/score.py`; the vision half
is judged from renders against `references/vision-scoring.md`, and nothing has
cleared it.

### The first four vision rounds were scored against stale renders

Four rounds judged **698 of 716 renders made by a superseded toolkit** — every
fix had landed in `bkit.py` after the images were made, so each round re-scored
code that no longer existed and the mean never moved. A directory of PNGs
carries no version, and file dates do not answer the question.

Every `report.json` now carries a `bkit_sha`, and:

```sh
python3 scripts/check_freshness.py <render_root>   # exit 0 only if all current
```

**Check freshness before scoring anything.** It is one command and cheaper than
one wasted round. See `references/render-freshness.md`.

## The loop

Everything in this skill is built around one cycle. Do not skip the render and
the score — a model that was never looked at has not been modelled.

```
 1. PICK     catalog.py next --limit 20        # or search/show
 2. SPEC     write real dimensions in millimetres + declare CHECKS
 3. BUILD    bkit recipes only; build() returns the spec
 4. RUN      blrun.py <model.py> --outdir ...
 5. SCORE    score.py <outdir>                 # objective 55, deterministic
 6. LOOK     read the rendered PNGs, judge the 45 subjective points
 7. FIX      smallest change that moves the weakest dimension
 8. repeat from 4 until objective == 55 AND vision == 45/45
```

A model ships only at **100/100**. Anything less is in-flight, not done.

## Index — load only what the task needs

| Need | Read |
|---|---|
| Write a model script | `references/authoring-a-model.md` |
| Pick construction geometry | `references/recipes.md` |
| Lighting, camera, exposure | `references/staging.md` |
| Materials that read correctly | `references/materials.md` |
| Score, and fix a low score | `references/quality-gate.md` |
| Grade renders by eye (the 45 subjective points) | `references/vision-scoring.md` |
| Run many models at once | `references/concurrency.md` |
| Check renders match the current toolkit | `references/render-freshness.md` |
| Blender crashes at startup / no GPU | `references/blender-environment.md` |
| Per-domain modelling notes | `references/domains/*.md` |

## Scripts

| Script | Role |
|---|---|
| `scripts/bkit.py` | The toolkit. Units, recipes, materials, studio, camera, health, measurement. Imported by every model. |
| `scripts/run_model.py` | Runs one model: builds, seats it, checks dimensions, renders 6 angles, writes `report.json`. |
| `scripts/blrun.py` | Runs many models concurrently under a global process cap, with per-job temp isolation. |
| `scripts/score.py` | The objective half of the gate (55 pts) plus the merge with a vision verdict. |
| `scripts/catalog.py` | Query the catalog: `stats`, `domains`, `list`, `search`, `show`, `recipes`, `next`, `mark`. |
| `scripts/check_freshness.py` | Are these renders made by the current `bkit.py`? Exit 0 only if all are. |
| `scripts/detached.py` | Finds geometry floating free of the assembly it belongs to. See `references/detached-geometry.md`. |
| `scripts/selftest_detached.py` | Proves `detached.py` against cases with known answers. Run it after editing either. |
| `scripts/lint_rotation.py` | Finds parts rotating about the world origin instead of about themselves. Run before shipping a model. |
| `scripts/shadecheck.py` | Proves `shade_smooth()` actually smooths, rather than returning without doing anything. |
| `scripts/block_slots.py` | Fill a render root's slot pool to cap — the only shutdown path when the host forbids `kill`. |
| `scripts/bootstrap_blender.py` | Patch and re-sign Blender so it starts on a GPU-less host. |
| `scripts/test_bkit.py` | Regression suite. Run it after editing `bkit.py`. |

## Hard rules

These are not style preferences. Each one exists because its violation produced
a specific, expensive failure.

1. **Author in millimetres.** Every dimension in a model script is mm.
   `bkit.v()` converts once, when a coordinate is written. Mixing units is the
   fastest way to get a 197 mm model that is 197 m across.

2. **Declare `CHECKS`.** A model states how each real-world dimension is
   measured (`part` + `how`), and the harness measures the geometry. Without
   declared checks the dimensional score is capped at partial credit, because a
   bounding box cannot prove a wall thickness.

3. **Measure, do not assert.** `SPEC` says what the object *is*; `CHECKS` say
   how to verify it. A model cannot pass its own gate by claiming a number.

4. **Compute repeated layout.** Ports, holes, teeth, slats and spokes come from
   `bkit.lay_out()` / `grid_positions()` with an explicit gap. Hand-placed
   constants produce coincident faces, and the EXACT boolean solver answers
   coincident faces by deleting the body.

5. **Finish watertight.** Every closed recipe ends up clean: `recalc()` for
   normals, `weld()` where a sweep reaches its axis, and `bkit.health()` must
   report zero non-manifold edges before you render.

6. **Seat the model.** `run_model` calls `sit_on_floor()`. A model built
   downward is buried by the studio backdrop and renders as a stump while still
   reporting a perfect bounding box.

7. **Never trust one render angle.** Six angles are standard because silhouette
   errors hide in the one view you did not look at.

8. **Run many models through `blrun.py`,** never by hand. Each job gets its own
   `TMPDIR` and output directory; the cap is global across all invocations. The
   summary reports the concurrency it actually achieved — check `speedup` and
   `peak_concurrency`, because a runner can advertise a cap it never used.

9. **Check the renders are current before scoring them.** `check_freshness.py`.
   Scoring a stale set produces a real number that describes code you no longer
   ship, and it is invisible unless you check.

## A minimal model

```python
"""widget -- one-sentence description of the real object."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))
import bkit

SPEC = dict(body_diameter=84.0, body_height=98.0)   # real millimetres

CHECKS = [
    dict(name="body_diameter", mm=84.0, tol=0.3, how="diameter", part="Body"),
    dict(name="body_height",   mm=98.0, tol=0.3, how="bbox_z",   part="Body"),
]

def build():
    body = bkit.lathe("Body", [(0, 0), (42, 0), (42, 98), (0, 98)],
                      segments=96, mat=bkit.preset("ceramic"))
    return dict(spec=SPEC, parts=1)
```

Then:

```sh
python3 scripts/blrun.py catalog/<domain>/widget.py --outdir /tmp/run --samples 48
python3 scripts/score.py /tmp/run/widget
```

`catalog/<domain>/widget.py` must be named after the catalog item id — that is
how the size class gets attached and how progress is tracked.

## Catalog

```sh
python3 scripts/catalog.py stats                 # progress by domain
python3 scripts/catalog.py next --limit 20       # cheapest unbuilt work
python3 scripts/catalog.py search "thread"       # find an object
python3 scripts/catalog.py show coffee_mug       # full entry
python3 scripts/catalog.py mark coffee_mug --status scored --score 100
```

`catalog/catalog.json` is the index; `catalog/taxonomy.py` is its source. Never
read `catalog.json` end to end — query it.

## Reference model

`catalog/kitchen/coffee_mug.py` is the worked example: real dimensions, a
declared check set, a two-part assembly, per-face materials, and the comments
that explain each non-obvious decision. Read it before writing your first model.