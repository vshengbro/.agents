# Detached geometry — "floating" is not the same as "not touching"

A model can be watertight, correctly dimensioned, fully materialled and score a
perfect 55/55 on the objective gate while carrying a chip of geometry floating
in mid-air beside it. Every objective check is per-object, so a stray part that
is itself clean is invisible to all of them. It shows up only as something that
reads as dirt on a render.

```sh
blender -b --factory-startup --python scripts/detached.py -- catalog/<domain>/<id>.py
# or a batch, which is how the catalog is swept:
blender -b --factory-startup --python scripts/detached.py -- --batch list.txt
```

## What it measures

1. Split the built scene into connected components (union-find over welded
   vertices).
2. Group components into **assemblies** by bounding-box proximity, transitively.
3. Report any assembly that is small relative to the whole model and separated
   from every other assembly by more than the touch threshold.

## Why step 2 exists — the mistake this file exists to prevent

The first version flagged every component that did not share a vertex with a
larger one. On the catalog that produced **over 500 findings**, including every
single key, button and grille of an accordion. All of them were correct models.

The flaw is a category error: **"not touching" is how real objects are built.**
A padlock hangs from a rod and the two share no vertices. A keyboard's keys sit
on a panel and connect to nothing. A piano's strings are separate. Nothing about
a real assembly requires its parts to be one welded manifold.

What marks a defect is not a part being unconnected — it is a part being
isolated from *every other part*, sitting in its own pocket of space. So
components are gathered into assemblies first, and only whole assemblies are
judged. That change took the accordion from 294 false positives to zero.

## Thresholds, and why they are relative

- **Touch** = `max(0.15 mm, 0.4% of the body diagonal)`. An absolute threshold
  cannot work: 0.1 mm is invisible on a 40 mm part and a visible float on a
  5 mm part. Anything at or below the threshold is attached.
- **Small** = under 6% of the model's vertices. A large island is a modelling
  error of a different kind — a whole mis-placed section — and needs a different
  fix, so it is not mixed into this list.

The first draft of this file wrote those constants as `0.30` and `0.02` while
comparing them against distances in **metres**, which made a 300 mm gap count as
touching and welded everything within 20 mm. It then reported an astrolabe with
a visibly hanging padlock as clean. The names now carry their unit, and
`selftest_detached.py` exists so that a units mistake here cannot be silent
again.

## The self-test is not optional

`selftest_detached.py` builds six fixtures at known distances and asserts the
answer for each — touching and 0.1 mm are clean, 1 mm / 40 mm / 200 mm are
flagged, and a deliberately huge island is *not* flagged because it is a
different defect. A detector that reports "clean" on everything is
indistinguishable from one that does not work, and this one did exactly that
before the units were fixed.

Run it after touching either file:

```sh
blender -b --factory-startup --python scripts/selftest_detached.py
```

## A flagged island is a lead, not a verdict

Across the 717-model catalog the check finds 71 flagged models. A large share of
those are deliberate: ground haze under a rainbow, rain streaks, fountain jets,
launch-pad deluge headers, repeated elements at a correct offset. Some are
unambiguous defects: a clock's hour hand clear of its dial, a building portico
standing 480 mm from the building it shelters.

So the output is triage input, not an automatic failure list. The judgement call
— does this part *belong* to this object — is made by reading the model's source
and looking at the render, not by the geometry check. Automating the verdict
would mean encoding an intent the geometry does not contain.

## The version trap in this file's constants

`TOUCH_REL`, `SMALL_FRAC` and `WELD_M` were each wrong at least once during
development, in opposite directions, and every wrong value produced *plausible*
output rather than an error. When a check reports a number rather than raising,
a wrong constant is indistinguishable from a right one. The self-test is the
only thing standing between those two cases.
