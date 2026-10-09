# Vision scoring — the other 45 points

`scripts/score.py` computes 55 deterministic points. This file covers the
other **45**, which cannot be measured from the mesh and must be judged by
looking at the renders. Nobody gets to pass on numbers alone: a watertight,
correctly dimensioned cylinder with an unreadable silhouette is still a failure.

## What you are looking at

Six renders per model, in `<outdir>/<item_id>/`:

| shot | what it is for |
|---|---|
| `hero.png` | the first impression — does it read as the object at a glance |
| `three_quarter.png` | form and depth, the standard product angle |
| `side.png` | silhouette and proportions |
| `top.png` | plan symmetry and top-surface detail |
| `rear.png` | hidden features that models usually forget |
| `front.png` | frontal proportion |

Look at **all six**. Silhouette errors hide in the view you skipped, and the
whole point of the set is that they do.

## The rubric — 45 points

| dimension | pts | a full mark means |
|---|---|---|
| **form plausibility** | 15 | At a glance, in any single shot, a viewer would name the object correctly. Not "some kind of cylindrical thing" — the actual object. |
| **proportion** | 15 | Internal ratios are right and the silhouette reads: correct relative sizes of parts, correct stance, nothing visually top-heavy or collapsed. |
| **surface** | 10 | Materials look like the real thing — a steel part reads as steel, ceramic as ceramic. Roughness and specular are believable; no flat plastic look on a metal. |
| **presentation** | 5 | Correctly exposed (detail visible in shadow *and* highlight), framed with margin, nothing clipped, nothing buried in the floor. |

## How to score honestly

- **Award full marks only when it genuinely reads well.** This gate exists to
  find the weak models, not to rubber-stamp them. A catalog of 716 things that
  all score 100 tells you the rubric measures nothing.
- **Judge the object, not the render.** You are grading whether the model is
  right and looks good, not whether you like the angle.
- **A missing feature is a proportion failure, not a form failure.** If a kettle
  has no handle it still reads as a kettle body — that costs proportion points,
  not form points. If it reads as a bucket, that is a form failure.
- **"I cannot tell what this is" is a form-plausibility failure.** That is the
  single most useful signal you can give a builder.

## Output

Write one JSON file per batch:

```json
[{"item": "coffee_mug",
  "form": 15, "proportion": 14, "surface": 9, "presentation": 5,
  "total": 43,
  "verdict": "reads as a mug immediately; handle is thin and sits low",
  "weakest": "proportion",
  "fix": "raise the handle attach point and thicken the tube"}
]
```

`fix` must be one concrete change a builder can make without re-deciding the
whole model. "Improve the model" is not a fix.