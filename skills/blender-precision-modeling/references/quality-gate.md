# The quality gate

A model is **not finished** until it scores 100/100. There are two halves and
neither is optional.

## A gate that has never executed is not a gate

`score.py` computes 55 points and merges a vision verdict for the other 45.
The merge had been written, documented and wired into the CLI — and had **never
been run**, because no vision verdict existed yet. The first live run raised
`AttributeError` immediately: the documented verdict format is a JSON *array* of
per-item results, and the code called `.get()` on it as though it were a single
object.

It surfaced only because a smoke test ran the merge against a synthetic verdict
*before* the real scorers were dispatched:

```sh
python3 scripts/score.py <model_dir> --vision verdicts.json
# 55/55 + 45/45 -> 100.00 PASS
# 55/55 + 35/45 ->  90.00 FAIL
```

**Run every gate once, end to end, against a known-good and a known-bad input,
before you rely on it.** A gate's first real invocation is not the time to find
out whether it runs at all — and it is exactly the kind of code that is never
exercised until everything else already works, because until then there is
nothing to check.

The same shape as a verifier that only builds its binary when the file is
missing: both look complete, both are untested, both fail on first use.


## A report is evidence only for the source that produced it

`report.json` and the `.png` files are a **snapshot**. If the model file has been
edited since, the report is stale and scoring it measures the wrong thing.

This produced two false failures in wave 2: `wrench` and `spanner_socket` scored
45/55 and 48/55 because the reports predated the agents' own corrections — both
pass 55/55 on a fresh run, against byte-identical geometry.

```sh
# authoritative: re-run, then score. Never score a directory you did not just build.
python3 scripts/blrun.py <model.py> --outdir <fresh> && python3 scripts/score.py <fresh>/<item>
```

If a score looks wrong, suspect staleness before you suspect the geometry. The
cheap check is to re-run one model and compare.


## Objective — 55 points, computed by `scripts/score.py`

| Dimension | Points | What it measures |
|---|---|---|
| mesh integrity | 20 | builds, watertight, no loose verts, no inverted normals, every part materialised |
| dimensional fidelity | 25 | declared `CHECKS` within tolerance, size class plausible |
| scene hygiene | 10 | geometry present, parts named, seated on the floor |

This half is deterministic. The same model scores the same twice, so a drop from
last week is a real regression and not renderer noise.

## Counting what you actually built

Never track progress by rewriting a shared index file. `catalog.py mark` once
did read-modify-write on `catalog.json`; with four agents marking at the same
time the last writer reverted everyone else's work, and **69 finished models
reported as 0 built**.

Status is now **derived from the filesystem** -- `catalog/<domain>/<id>.py`
existing *is* the fact -- and `mark` writes one small file per item, so
concurrent marks cannot clobber each other.

```sh
python3 scripts/catalog.py stats      # self-heals against the disk
```


## Subjective — 45 points, judged from the renders

| Dimension | Points | Ask |
|---|---|---|
| form plausibility | 15 | At a glance, is this the named object? |
| proportion | 15 | Are the internal ratios right, and does the silhouette read? |
| surface | 10 | Do materials and shading look like the real thing? |
| presentation | 5 | Is it exposed, framed, unclipped? |

Look at `hero`, `three_quarter`, `side`, `top`, `rear`, `front`. One angle is
not evidence — silhouette errors hide in the view you skipped.

## Reading a failure

`score.py` prints only the dimensions that lost points, with the actual value:

```
hex_bolt  objective 34.0/55
  - watertight_nonmanifold    0.00/6.0   1830 edges
  - spec_dimensions           0.00/20.0  1/2 checks: head_across_flats ok,
                                    shank_length_total want 97.5 got 98.2!
```

Fix the **dimension that lost the most points first**, and fix the cause, not
the symptom. In the example above the 1830 non-manifold edges come from a part
that was left open, not from the dimension check.

| Symptom | Usual cause |
|---|---|
| model renders as a stump | built below z=0 and buried by the backdrop |
| renders pure white, no form | clipped exposure; check `auto_exposure` actually ran |
| metal renders black | `metallic=1` with a dark world; the gradient needs a bright end |
| whole body vanished after a boolean | coincident faces from hand-placed layout |
| reports a perfect bbox but looks wrong | you checked the box, not `CHECKS` |

## Recording the result

```sh
python3 scripts/catalog.py mark <item_id> --status scored --score 100
```

`status` moves `todo -> building -> built -> scored`, with `failed` for anything
that could not be rescued. A catalog item only counts as covered at `scored`.
