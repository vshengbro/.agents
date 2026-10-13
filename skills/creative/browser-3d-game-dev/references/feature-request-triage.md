# Triage a large feature list before spending the budget

For requests that name many systems at once ("add tanks, planes, mountains,
grass, flowers, animals, ocean, lake, cruise ship, sailboat, warship, aircraft,
melee weapons, sports cars, and make every building enterable with stairs").

The failure mode is treating the list as a queue of N greenfield items and
dispatching N workers. The list is a **diff against what already exists**, and one
of its items is a subsystem rewrite that will consume the rest of the budget.

## Step 1 — Audit, do not estimate (one tool call)

Enumerate the asset manifest and the module list, then map every requested noun to
an existing id:

```bash
ls assets/*.json | wc -l
python3 -c "import json;d=json.load(open('assets/manifest.json'));print([a['id'] for a in d['assets']])"
grep -rn "pub fn \|^fn " src/*.rs | head -40
```

Typical result: a list of 15 becomes "8 exist, 4 are a new builder module, 3 are
core-system work". Report that reframing — the user's list was a wish list, not a
spec, and the honest diff is more useful to them than a silent re-scope.

## Step 2 — Rank by blast radius, not visibility

The visible item ("make the ocean look nice") is often cheaper than the invisible
one ("buildings must be enterable"). Sort on what a change *invalidates*:

| Tier | Requested item | What it actually costs | Risk |
|---|---|---|---|
| 1 | New mesh + placement entry | New builder module; reuse existing batch/instance path | Low, parallelizes cleanly |
| 2 | Multi-instance new geometry family | Same, plus face-count and culling budget | Low–medium |
| 3 | Displaces the ground (mountains, terrain) | Invalidates camera, shadow frustum, ground mesh, physics | Global |
| 4 | Requires vertical collision (interiors, floors) | The collision system may be 2D-only | New subsystem |
| 5 | Changes the shared vertex/interleave format | Every GPU upload path and every consumer | Highest |

Tier 3–5 items are decisions, not work items. Surface them before dispatch.

## Step 3 — Give a recommendation, then take the decision

Show the table, name the item that will eat the budget, propose the cheaper
alternative for it, and ask once. Two questions are enough:

- Will the displaced-terrain item displace the ground mesh, or stay peripheral
  assets around the existing flat area?
- All buildings, or a small number of showcase buildings to prove the mechanism?

Typical recommendation that preserves the user's intent at a fraction of the cost:
keep the centre flat and place terrain as peripheral assets; build 2–3 showcase
buildings with the real mechanism rather than N with a thin imitation.

When the user replies "you decide" / "你自己决策", that is authorisation to
proceed — **not** licence to skip the plan. State the three decisions you made and
the reason in one short paragraph, then execute. Re-asking after being handed the
decision is the failure this step prevents.

## Step 4 — Partition workers by file ownership

- One builder module per worker, each owning exactly one new file.
- Exactly one worker owns shared wiring (the manifest / registry file), or the
  parent does it after collecting results. Multiple workers editing one registry
  file collide non-deterministically.
- Brief the consumer-side worker to keep building when producer files are absent.
- Put the shared environment facts (build command, wasm output path, verification
  tooling, already-paid-for pitfalls) verbatim in **every** brief.
- Give a numeric budget derived from the current baseline, and require workers to
  name what they did not finish.

## Step 5 — 2D collision cannot become vertical by adding shapes

If the collision API is `resolve(point: Vec2) -> Vec2` over a flat shape list, then
there is no Y anywhere in it, and the player position's Y component is never
written. Enterable interiors therefore need all of:

- A **separate** world for vertical geometry (slabs and Y-ranged walls). Do not add
  Y to the existing one — every traffic and vehicle caller depends on it.
- `support_height(point_xz, from_y) -> Option<f32>`: the highest walkable slab at
  or below `from_y + step_up_tolerance`. This single query is what makes stairs
  work; a separate stair-collider type is not needed.
- Stair rise must be **under** the step-up tolerance (≈0.3 m rise, ≈0.45 m
  tolerance) or the player stutters on every step.
- Horizontal push-out that considers only geometry overlapping the player's
  **body span** in Y — a slab above the head must not block, a wall at torso height
  must.
- Gravity integration, landing snap, and an upward push-out if the player ends up
  under a slab (anti-tunnelling).
- A camera that does not clip through the interior walls: the occlusion probe must
  query the same interior geometry the player collision does.

## Step 6 — Report honestly at the boundary

If the budget runs out mid-list, say which tiers shipped, which were reclassified
as already-present, and which are not started. Do not report a partially-built
feature as delivered, and do not describe an unverified build as working.
