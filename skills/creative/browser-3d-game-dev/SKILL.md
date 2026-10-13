---
name: browser-3d-game-dev
description: Build real-time 3D browser games and simulations.
license: MIT
author: Hermes Agent
version: 1.0.0
metadata:
  hermes:
    tags: [game-dev, threejs, webgl, voxel, physics, browser-verification]
    related_skills: [p5js, hyperlane-upload, dogfood]
---

# Browser 3D Game / Real-Time Simulation Development

## When to use

- Voxel / block worlds, Minecraft-style clones, sandbox builders
- Three.js (or WebGL) scenes with custom physics, controllers, or streaming data
- Anything where a *simulation step* runs per frame and correctness is judged by feel
  (movement, collision, camera, fluids, entity AI)
- Projects that generate their own models offline (Blender/bpy or a modeling script) and
  consume them at runtime — see the asset-pipeline section below

Triggers: "make a Minecraft clone in the browser", "build a voxel game", "3D browser
game", "webgl game with physics", "web simulation with a player controller", "model the
assets in Blender and use them in a web game".

Not for: p5.js generative sketches (use `p5js`), landing pages (use `frontend-dev`),
QA report-writing over an existing app (use `dogfood`).

## The governing rule

**A control that is not measured is unverified.** The dominant failure mode in this
class of work is code that *looks* implemented but whose branch is never reached:
a flight mode that integrates no horizontal velocity, a fluid sim gated behind a
condition that is never true, a damage calculation that reads pre-integration state.
None of these are visible by reading the code. All of them are trivially caught by
driving the simulation with synthetic input and asserting an invariant.

So: build the assertion harness **before** you claim anything works. See
`references/browser-verification-harness.md`.

**Corollary — an entity that reports itself present is not an entity on screen.**
A rig with N limb batches, a HUD reading "third-person", a climbing triangle count
and zero console errors are all consistent with geometry that never reaches a draw
call. Establish visibility with a **pixel count in the entity's screen region** (> 0)
and, if the engine supports batch hiding, a **hide-and-diff** over that region (a
zero-pixel diff proves the batches never drew and localises the bug immediately).
Gate the feature on that number, never on the rig being "built". See
`references/third-person-camera.md` §4.

**Corollary — a camera is its own system, and "the view is wrong" is ambiguous.**
Users report camera defects as rendering defects ("clipping", "models not
displayed", 一片模型不展示) because the symptom is a wall or an empty frame. Split it
before touching anything: camera **occlusion** (eye inside geometry) and camera
**framing** (character too small / in a corner) are different bugs, and tuning the
follow distance fixes only the second. Measure the camera's actual distance in the
occluded and unoccluded states — a distance that does not change when geometry
intervenes means the avoidance branch never fired.

## Architecture

Vanilla ES modules + importmap. No build step, no bundler — the deliverable is
openable in a browser as-is.

```
index.html          importmap maps bare specifier -> local lib file
lib/<engine>.js     vendored third-party engine (download, don't CDN-reference)
js/blocks.js        data: block registry + procedurally generated textures
js/atlas.js         pack block textures into one atlas -> single material
js/world.js         chunk storage, terrain gen, fluid sim
js/mesher.js        voxels -> BufferGeometry (face culling + AO)
js/player.js        collision, movement modes, survival state
js/main.js          render loop, streaming, input, HUD
```

Rules that keep this stable:

- **Vendor the engine locally.** `curl` it into `lib/`. A CDN reference breaks offline
  and breaks the deploy step (a remote file is not a graph edge you can rewrite).
- **Split by concern, not by feature tier.** A file should be readable in one screen.
  Meshing does not belong in the render loop; fluid sim does not belong in `world.js`'s
  terrain generator.
- **Expose the instance on `window`** (`window.__game = game`). Without it, every
  verification probe has to be injected through the UI, which cannot reach simulation
  internals.

## Build order

Follow this order; each step is independently verifiable.

1. **Data layer** — block registry, procedural textures. Verify: atlas has a UV rect for
   every registered block id.
2. **Terrain** — noise heightmap, chunk storage, biomes. Verify: generated chunk has a
   non-zero block count, and the height field's **relief and flat-fraction** over a wide
   sample match intent (see the terrain distribution probe). A plausible max is not
   evidence of interesting terrain.
3. **Mesher** — face culling + AO. Verify: renders, triangle count is sane, and
   **no unsupported geometry at chunk borders** (a classic seam bug: meshing a chunk
   without reading its neighbours' blocks).
4. **Player physics** — collision, movement modes. Verify with the harness.
5. **Render loop + input + HUD**.
6. **Sky / atmosphere / entities** last. These are the most visible when wrong, and
   useless if the world underneath is broken.

## Verification harness

Drive the real simulation, not a mock. See
`references/browser-verification-harness.md` for the full pattern; the essentials:

```js
// Test a CONTROL, by asserting the invariant it must satisfy.
const p = game.player, idle = {fwd:0,right:0,jump:false,sneak:false,sprint:false};
const out = [];
for (const yaw of [0, Math.PI/4, Math.PI/2, Math.PI, -Math.PI/2, 2.4]) {
  p.flying = true; p.vel.set(0,0,0); p.yaw = yaw; p.pitch = 0;
  p.pos.set(0.5, 60, 0.5);                       // known empty airspace
  for (let i=0;i<15;i++) p.update(idle, 1/60);
  const d = p.lookDirection();                    // the intent
  p.vel.set(0,0,0);
  const x0 = p.pos.x, z0 = p.pos.z;
  for (let i=0;i<25;i++) p.update({...idle, fwd:1}, 1/60);
  const mx = p.pos.x-x0, mz = p.pos.z-z0, L = Math.hypot(mx,mz)||1;
  out.push(+(((mx/L)*d.x + (mz/L)*d.z)).toFixed(2));  // must be 1 at EVERY yaw
}
```

Two rules that make this reliable:

- **Sweep the parameter space, not one value.** A 180° error in a movement basis is
  invisible at `yaw = 0` and obvious at `yaw = π/2`. If you only test the default angle,
  you will ship the bug.
- **Settle into a controlled state first** (empty airspace, zeroed velocity) so the
  measurement reflects the code under test rather than whatever the world was doing.

## Offline asset pipeline: contract the format before the renderer exists

Procedural assets generated in a DCC tool (Blender/bpy, a modeling script) are a
**separate deliverable** from the renderer, and the file format is an interface between
them. Fix the interface first, write it into the schema doc, and only then write the
consumer — schema changes force renderer changes and are the expensive direction.

The format must state, in the file itself, everything a renderer author cannot infer:
units and axis convention (Y-up vs Z-up), origin per asset class, one fixed forward axis,
CCW-from-outside winding, colors as 0..1 with a `face_colors` array parallel to `faces`,
and emissive as a channel separate from base color.

Ship a `manifest.json` (id + category + file per asset) next to a `SCHEMA.md`, so the
renderer enumerates a declared list instead of globbing at startup.

**Assert the export separately from the render.** The render proves the model is visible
and framed; it says nothing about whether indices are in range or winding is right, and
a valid-index file says nothing about whether the camera ended up inside the mesh. Two
different failures, two different assertions. Report the triangle count — a budget
checked only by feel drifts up until the frame rate dies.

Full contract, schema field table, export-time assertions, and the parallel
producer/consumer brief pattern: `references/offline-asset-export-contract.md`.

## Split independent workstreams behind a written interface

When the asset pipeline and the renderer are built as two parallel workers, the schema
**is** the coordination contract: it goes into both workers' briefs verbatim, including
units, axis, winding, origin and color range. A worker that improvises the format
produces a file the other worker cannot parse, and the failure surfaces late as a
confusing runtime bug rather than as a schema mismatch.

Tell the *consumer* worker to degrade gracefully when the producer's files are not
there yet (fall back to a built-in primitive, keep building). Without that, the two
workers serialize on each other for no reason, or one reports a blocking failure for a
file the other was about to write.

The parent verifies the hand-off rather than trusting both self-reports: assert the
emitted files parse and the triangle budget holds, and confirm the renderer actually
renders geometry from the emitted format — not just its own fallback primitive.

### Audit the request against what already exists BEFORE fanning out workers

A large feature list is mostly a **diff against the current asset manifest**, not
N greenfield items. Enumerating the manifest and matching each requested noun to an
existing asset id first takes one tool call and routinely reclassifies two thirds
of the list as already done — reporting a working feature as a gap the user must
fund is a costly error in both directions.

Rank the remainder by **blast radius**, not visibility: a new mesh reuses the
batch/instance path (cheap), while displacing the ground or adding vertical
collision invalidates camera, shadow frustum, culling and physics (global). Show
the user that ranking with your recommendation **before** dispatching. If they
hand the decision back to you ("you decide"), state the calls you made and the
reason in one paragraph, then execute — re-asking after being handed a decision
is the failure this step prevents.

Note the trap that makes "enterable buildings" expensive: a collision system with
no Y axis cannot gain one by adding shapes. Gravity, a
`support_height(point_xz, from_y)` slab query with a step-up tolerance (that
query *is* the staircase), and body-span-aware wall push-out are a new subsystem,
not a parameter change.

Full triage procedure, the cost-ranking table, and the 2D-collision limits:
`references/feature-request-triage.md`.

### Fanning out three workstreams: partition by file ownership, not by feature

When one request contains several large independent concerns (gameplay, assets,
lighting), splitting them across parallel workers works only if the briefs assign
**disjoint file ownership by path** and state it in imperative terms ("only modify
`src/`, never touch `assets/`"). Overlap by concern invites a silent write collision
whose symptom is a nondeterministic build, not a clear conflict.

Put the shared, non-negotiable environment facts **in every brief verbatim** rather than
in one shared document: how to build, where the wasm lands, which verification tooling
exists, and each pitfall already paid for once (dev-server is already running — don't
kill it; the user's real browser is off-limits; keyboard input needs canvas focus;
`curl` may not reach the deploy origin). A worker that has to rediscover any of these
spends its budget on setup and returns with a weaker report.

Assign each worker a numeric **performance budget derived from the current baseline**
("stay at or above N FPS; the scene is currently M triangles at K FPS"), not "don't make
it slow" — an unquantified budget is not enforceable and will be traded away silently
in the last hour of a workstream.

Tell workers to report **before/after numbers and to name what they did not finish**.
Self-reports that omit their own gaps force the parent to re-derive them, which costs
more than asking for them up front.

**Re-run `git status --short` after dispatching, not only at the end.** Parallel
workers plus a concurrent editor (IDE, second agent, background sync) can touch
files no brief mentioned. Untracked source files appearing that no worker owns, or
an existing builder modified without being in any brief, is the signal. Name the
anomaly to the user rather than reconciling it silently — you cannot tell whose
change it is, and silently merging makes both sides unreviewable.

**Watch for context exhaustion mid-workstream.** A long session can hit the
tool-call ceiling mid-edit, leaving the tree further from done than it looks
(shaders written but never compiled; constants added but never wired). Before
claiming anything works, re-run the build and enumerate the remaining errors
rather than trusting the last observed state, and report the pipeline as
*unverified* if it never ran to green after the final edit.

## Name the technique the platform can actually do

A user request names a *look*, not a method. "Add ray tracing" in a WebGL2 project is
a request for ray-traced *appearance*; WebGL2 has no ray tracing and no hardware path to
it, so the honest delivery is real-time approximation under accurate names. Before
dispatching a worker, map each requested visual to what the current graphics API
supports, and put that mapping **in the brief as a table** with an explicit instruction:
label every delivered item with its true technique name and never describe an
approximation as the thing the user asked for.

| Requested look | What a WebGL2 renderer can actually deliver | Say it as |
|---|---|---|
| Hard cast shadows | Depth-map shadow pass with PCF softening, cascaded/frustum-fitted | "shadow map" |
| Contact darkening in corners | Screen-space ambient occlusion (SSAO) | "SSAO", an approximation |
| Wet-ground / paint reflections | Screen-space reflections, or a cubemap probe | "SSR" / "reflection probe" |
| Soft light halos | Multi-pass threshold + separable gaussian bloom | "bloom" |
| Global bounce light | Hemisphere ambient + baked vertex AO | "hemisphere ambient" |

The failure this prevents is reporting an SSAO pass as "ray tracing implemented" and
letting the user believe a different-class result. State the substitution in the final
message too, in one line, with what real ray tracing would require instead — that is
information, not a hedge. If a downstream API swap would be needed (e.g. WebGL2 →
WebGPU), name it and scope it separately rather than quietly approximating forever.

### Post-processing: deferred buffers lag a frame, and degrade must neutral-clear

A pass that **samples** a render target it also **writes** (SSAO reading a
G-buffer, SSR reading scene colour) cannot be ordered inside one frame — the main
pass consumes those textures, but producing them needs geometry the main pass
draws. Ping-pong two targets per effect (correct for a moving camera) or accept
that the main pass samples the **previous frame's** texture (usually invisible,
free). Document which.

When an adaptive tier *skips* a pass, **clear its target to the neutral value
first**. Skipping leaves last frame's texture in place, so the downgrade frame
shows a smear of the effect you just disabled — which reads as a rendering bug,
not a tier change. Neutral is "no occlusion" for AO and "no hit" for reflections.
A tier is **one-way**: upgrading back on leaving a dense block pumps the image and
reads worse than staying low. Keep the smoothed FPS out of the frame-`dt` clamp —
a clamped `dt` after a tab switch computes a bogus 4 fps and fires a spurious
downgrade.

### Never anchor a performance budget to a number measured on a different renderer

Headless SwiftShader (CPU software rasterisation) typically runs a deferred-style
pipeline 5–10× slower than any real GPU, so the baseline FPS you can actually
measure predicts nothing about the user's hardware. Treat it strictly as a
**regression** baseline (new work vs old build, same backend), never as a capacity
estimate. Gate new content on measured triangle count and measured post-change
FPS, and if the new number is unacceptable, report it with the number attached
before stacking more assets on top.

## Third-person camera and character visibility

When the deliverable includes a player character and a follow camera, load
`references/third-person-camera.md` before writing the camera. The short version of
what it prevents, all of which shipped as "verified" bugs at least once:

- **Reuse one collider set.** Camera occlusion must query the same colliders the
  player collision uses; a parallel set disagrees with it.
- **Reject boxes behind the ray.** A box behind the origin returning a hit at `t = 0`
  computes a negative pull-in and flings the camera behind the player.
- **Multi-probe, take the tightest.** Center-line-only probing leaves a building at
  the frame edge filling a third of the screen.
- **Make near-cull a camera parameter.** A constant radius tuned for a wide shot
  deletes the whole street in follow mode while the triangle counter climbs.

Verify by *number*, not adjective: report camera distance in open / occluded /
recovered states, and character pixels painted. "The camera avoids walls" and "I can
see the character" are the two least informative sentences in this class of work.

**A stair tread is a ramp surface, never a box to push out of.** The one rule that
decides whether a vertical-collision system works. A player's body spans, say,
`y ∈ [feet, feet+1.75]`, so while they stand on step *N* their body overlaps steps
*1..N* — and they are inside each of those XZ boxes. A generic
`push_out_aabb` resolves an "inside the box" case by minimum slack, which on a
narrow tread picks the **lateral** axis and fires the player off the side of the
staircase. The symptom is a player who climbs two or three steps, gets teleported
sideways, and falls to the ground floor, with every support-height query returning
correct values the whole time.

Split the roles instead of tuning the box: a `Slab` (floor, tread, landing) provides
**vertical support only** and never participates in horizontal push-out; only a
`Wall` blocks laterally. The guard belongs on the *body span vs slab top*, not on
the whole body AABB: skip a slab whose top is at or above the feet within the
step-up tolerance, because the player is standing on it. Two consequences worth
knowing before you are surprised by them:

- The ground slab also stops pushing laterally, so it no longer acts as an invisible
  retaining wall. That is usually what you want — otherwise a 0.15 m floor plate
  becomes a curb that seals the doorway you just built a gap in.
- A tread narrower than the body can still trap the player between two opposing
  slabs; verify the tread width exceeds the body diameter, or model the flight as
  a ramp.

**A collision bug found by staring at coordinates is usually a missing end-to-end
test, not a new shape.** Per-subsystem unit tests — "support height increases
along the stair", "a wall blocks", "the doorway is passable" — all pass while the
route as a whole is impossible, because none of them ever walks the player through
it. Add one test that drives the *route*: start outside, step through the doorway,
cross the partition gap, touch the first tread, ascend, and assert the final height
reaches the upper slab. The cost is a list of waypoints and a tick loop; the
payoff is that every class of routing defect above becomes a red test instead of a
manual browser session. When such a test fails, **log the per-tick position and
height and read the trace** — the first tick where a coordinate jumps past its
neighbours names the mechanism, and a single-tick lateral discontinuity of roughly
one tread width is the signature of a slab push-out, not of a wrong waypoint.

## Infinite world: infinite coordinates are not streaming

Two claims get conflated, and conflating them ships a \"done\" world that stops
at the old boundary. **Infinite coordinates** means predicates and generators
resolve beyond the old bound (`roadway_at(50000, 50000)` returns a real answer).
**Streaming** means geometry, props and colliders have a load/unload lifecycle
driven by a moving centre. The first is a refactor of coordinate math; the
second is a new subsystem, and it is the part that gets left out — every
screenshot looks correct because the player never left the initial radius.

Two rules decide most of the work. **Never enumerate to answer \"am I on a
street\"** — the old `min` over a fixed array becomes a closed-form nearest-index
round, because an enumeration cannot scale past the array it replaced. And
**rebuild on a distance threshold, not per frame** — a recentre that fires every
frame reallocates and re-uploads a mesh 60 times a second for no visible change.

Continuous surfaces (ground, water) recentre on the player; discrete ones
(buildings, props, colliders) need real chunks. **The collider layer is the one
most often left behind**: a collision world built once at init bounds the player
no matter how far generation reaches.

Hand-placed content must be re-expressed block-relative when the grid pitch
changes — a prop at an absolute coordinate picked against the old grid lands on
a roadway the moment the pitch moves — and procedural generation gets an
explicit footprint exclusion so it cannot build through it.

Write the far-centre test **before** the refactor lands: build ground and water
around a centre thousands of metres out and assert every vertex is within
half-a-block-plus-street-furniture of it, per axis. That single test is what
catches a loop-local binding shadowing the centre parameter, two axes sharing one
enumeration interval, and an interval derived from two unrelated centres — all
invisible at the origin, catastrophic far from it. When it fails, print per-axis
extent plus the derived origin plus the enumerator's actual output; deriving the
geometry by hand gets it wrong.

Full recipe, per-layer table, and the three bug classes with the instrumentation
that localises each: `references/infinite-world-streaming.md`.

## Vehicles: steering is a physics model, and wheels are a *mesh* problem

Two separable problems hide under "make the car drive". Solve the physics first;
it is testable in a unit test with no renderer.

**Separate the two velocity axes or drift is unrepresentable.** A vehicle whose
lateral position is pinned to a lane centre cannot drift, steer, or be pushed —
the pin is a hard constraint, not a force. Track longitudinal and lateral velocity
separately, and let the lateral axis decay toward the body frame rather than
being assigned. Steering input then drives yaw through a wheelbase term (so
turning scales with speed instead of pivoting in place), and the leftover
perpendicular velocity *is* the drift — a slip ratio above the grip limit is the
sliding state, and a drifting car must measure slower than a straight one, which
is the invariant that proves the grip term is wired at all. AI and player vehicles
want different constraints: keep the lane pin for AI, drop it for the player.

**A transform constructor that expresses one axis cannot express a composite
rotation, and approximating it is worse than adding a constructor.** A wheel must
spin about its hub *and* follow the body's yaw — two rotations, one hierarchy.
An `Instance::new(position, yaw, scale, tint)` that builds a Y-rotation matrix
cannot represent that, and the tempting fudge (folding the spin into `yaw`, or
rotating a parent and hoping) makes the wheel steer instead of roll. Add a
constructor that accepts an explicit column-major model matrix; the body keeps
the one-axis path.

**Geometry merged in the asset cannot be animated independently — split it at
the mesh level, and rebase the pivot while you are there.** "Wheels don't roll"
usually means the four wheels are welded into a single mesh part at build time.
A renderer that uploads one mesh per part has no transform to give an individual
wheel, so the split must happen in the upload path: partition the part's
**faces** (real vertex indices, not a flat vertex array — filtering vertices
silently drops every face that references a discarded one), group them by
quadrant, and translate the survivors so the hub sits at the origin. Meshes
shared between instances of the same model must be built once and referenced
many times, or the second car of a model gets no wheels at all.

**Measure mount points and radii from the asset, never from the numbers you
remember.** The same trap as deriving a waypoint route by arithmetic: mount
offsets written from a plausible-looking figure were off by 0.1 m against the
real geometry, on both axes, with no error anywhere. Group the part's vertices
and print the centroid per quadrant — that is the mount point, and the extents
give the radius.

**Prove a rotation by which basis vector changed and which did not.** A spinning
wheel's transform is a claim about axes, and the claim is falsifiable: the axis
you rotate *about* must be invariant while the two perpendicular basis vectors
sweep. Expose one instance's model matrix in the debug channel and read it live —
the Y basis sweeping a full circle with the X basis pinned is positive proof of
a rotation about X, and it distinguishes "rolling" from "yawing" from "the whole
batch is being rebuilt each frame". Screenshots of a car moving cannot separate
these, and a close-up of a black symmetric tyre is not evidence of anything.

## Pitfalls

**Derive a waypoint route by probing the geometry, never by deriving it in your head — and prove each stage of the walk.**

A route through a building (doorway → partition gap → first tread → top of the
stair → upper slab) has one non-obvious rule per segment: which side of an
obstacle the gap is on, which end of a run is the low end, whether the landing is
already floored. Each is a sign or an offset that reads as obvious and is
routinely inverted, and an inverted one produces a **plausible** failure — the
player walks the whole route and stalls at the same leg every time.

Three habits, in the order they matter:

1. **Probe the geometry, do not arithmetic it.** A grid scan that prints the
   support height at every cell answers "where is the stair actually
   mounted?" in one run. Deriving `hx`, `sx0`, `stair_x`, `stair_end` from
   `span` in your head costs several rounds and still gets a sign wrong,
   because the constant you are reasoning about is usually not the constant
   in the code — spans, gaps and leads are per-building and differ between
   the two instances of the same asset class.
2. **A waypoint on an obstacle's boundary will not be reached.** Put it in the
   *middle* of a gap, not on the edge you are trying to get past. The agent has
   a radius; a target that sits on the wall's end face is unreachable by
   construction, and the symptom is a stall at the obstacle with the height
   unchanged, which reads like the movement code is broken.
3. **Report every leg, assert once at the end.** A single final assertion
   makes the divergence invisible, so each retry guesses which leg failed.
   Print `(leg, local position, height, steps taken)` per leg; the report
   names whether the player stalled, overshot, or never moved — three
   mechanisms the final message renders identically. Delete the per-leg
   reporting once it has named the mechanism, and keep the final assertion.

**Two consecutive runs with byte-identical output means your edit is not being
read.** Changing a coordinate and getting the same value, the same final
position, and the same height is not a weak result — it is proof the changed
value never reached the executed path (stale artifact, shadowed binding, a
second copy of the constant, a branch never taken, a target already
saturated). Stop tuning and prove the value at the point of use before the
next attempt; there is no bound on how many plausible variants of a fix you can
write against a value nobody reads.

**Never report a root cause from a probe you have not proved you aimed correctly.**
Three wrong-target readings in one session produced three confident false
diagnoses: sampling a depth-only shadow FBO's colour attachment and reading the
correct all-zero result as a bug; querying `COLOR_ATTACHMENT0_BINDING` at a
different point in the frame than the draw; comparing `checkFramebufferStatus`
against the wrong constant (`FRAMEBUFFER_COMPLETE` is **36053**). Before a
measurement becomes a root cause, state the pass/FBO/program it came from and
confirm the value differs across a deliberate A/B. When a hypothesis survives two
probes, widen to a bisect (swap one attachment format, read pixels) instead of
adding a third probe. A cheap discriminator — force the fragment stage to output an
unconditional constant; black proves the fault is upstream of shading, green
proves it is not. See `chrome-devtools-protocol` § "Probing a WebGL app".

**Revert every diagnostic edit, including helper edits made while bisecting.** A
guarded early-return added to make one case pass becomes a silent behaviour change
once the real cause is found elsewhere, and a compatibility tolerance added on a
wrong hypothesis outlives the investigation. When a fix lands, diff the whole file
against the last good commit and read the diff — speculative walls, widened
tolerances, and early-outs that are not part of the fix are the residue.

**An instanced draw's per-instance stride is a silent, scene-wide corruption.** Writing
19 floats into a 20-float stride does not error — every instance after the first
reads a model matrix shifted by one component, so geometry radiates from the origin as
screen-filling wedges. Compute the resize from the stride constant itself
(`resize(before + FLOATS_PER_INSTANCE)`), never from an arithmetic restatement of it
that can cancel to zero, and comment why the pad is load-bearing. A single-instance
batch never triggers this, so any test scene that renders one object per draw will
pass while the real world is broken. Cover it with a multi-instance scene and assert
each instance's transformed origin.

**A fragment shader that never reads its colour varying renders every surface one
flat grey, while the data pipeline stays perfectly healthy.** Per-vertex albedo and
per-instance tint get uploaded, declared `in`, and wired from the vertex buffers
through to the fragment stage — and then a placeholder (`vec3 base = vec3(0.5)`)
drives the lighting term instead. Nothing errors; colours are correct on disk and in
VRAM. This is reported as "the models have no colour" and gets misdiagnosed as
overexposure, missing gamma, or a lost attribute. When colour is uniformly absent,
grep the shader for where the albedo varying is *consumed* before touching lighting
constants — a placeholder is a one-line find that no amount of exposure tuning will
reveal.

**Tone-map by luma, never per channel.** Per-channel mapping is what turns a
saturated 1.7-luma pink facade into `(1,1,1)`; clamping per channel additionally
bleaches already-pale surfaces. Use a luma-scaled curve
(`f(L) = L·(1 + L/W²)/(1 + L)`, white-point normalised) and rescale RGB proportionally.
Apply it identically in the GPU shader and any CPU/fallback shading path, or the
fallback renders visibly differently from the primary backend. Confirm the colour
space from the asset schema before concluding gamma is missing — assets declared
*linear* with `linear_to_srgb()` already applied at display are correct as written,
and "adding gamma" there makes the scene worse.

**An entity registered twice into a push-semantics mesh table is drawn with the wrong
mesh, not missing.** A second registration pass doubles the GPU table while batches
keep indexing the first half, so a character rig resolves to large world geometry
drawn with a human-sized matrix — a screen-filling block that reads as a broken
screenshot rather than a binding bug, while every count stays healthy because the draw
call is issued and only the binding is wrong. Register each mesh at exactly one call
site, and A/B a single batch in isolation versus in the merged scene: the isolated
render shows its true size and the size mismatch is the diagnosis. Full bisection
order and the Rust-specific traps: `wasm-gpu-mesh-index-alignment`.

**An oscillation phase must go THROUGH the trig call, never be multiplied by it.** A
gait/animation phase accumulates every frame by design, so any expression of the form
`scale.sin() * phase` leaves the accumulation unbounded and the joint spins at a
constant rate instead of oscillating. Transposing one operand is a silent one-character
bug: no error, plausible-looking code, and limbs rotating at (phase rate × constant) —
e.g. a 2.6 rad/m walk phase at 4.6 m/s becomes ~6.9 rad/s, just over one full turn per
second, which reads as "the character is glitching" rather than as bad arithmetic.
Correct shape is `scale * amount * (phase + offset).sin()`: bounded by `scale`, so it
oscillates and settles to 0 when `amount` fades. Any periodic quantity that grows
without bound needs the same audit. Diagnose by evaluating the closed form across time
and checking the result is **bounded** — an angle that exceeds 2π at any point is the
bug, and the per-second turn count tells you the mechanism immediately.

**A stale identifier after a rename throws EVERY frame while the scene keeps animating.** Renaming a per-frame local (typically to make a hot path allocation-free) and missing one reference makes the per-frame handler throw on every call. Nothing looks broken: the entity keeps drifting on its last good velocity, the HUD keeps updating, triangle counts stay healthy, and screenshots look correct — the control is simply dead while the game appears alive. Two tells, both cheap: assert **`exceptionCount === 0`** in the harness (a page can rack up uncaught exceptions by the hundred per second and still render fine), and after any rename `search_files` for the old symbol across the module — the write that renames the declaration is not the write that renames every use. Read the harness's own error list, never just the pass/fail count; a run of bare `'Uncaught'` strings with no message is the signature of a throw inside a rAF callback, where the message is swallowed.

**A steering axis sign is a convention, and a screen-space assertion passes under either one.** Screen-right for a chase camera looking along the entity's heading is `heading x up` — verify it against the camera basis (`up x (-heading)` is the camera's local X) rather than from memory, because getting it backwards inverts the horizontal AND vertical axes silently while every other test stays green. The trap is the assertion, not the bug:

```js
// WRONG: encodes one sign convention, so an inverted axis still passes
check(aYaw < -0.2 && dYaw > 0.2);
// RIGHT: assert the RELATIONSHIP, which no single sign can fake
check(aYaw < -0.2 && dYaw > 0.2 && Math.abs(aYaw + dYaw) < 1e-3);
```

Assert per-key in **world space**, and assert symmetry (opposing keys must produce equal-and-opposite results). A screen-space "yaw must be positive" check is meaningless the moment the heading is not the +X axis. Likewise: the screen-up key conventionally maps to a NEGATIVE axis value, so the world vector needs `-ay` on the vertical term — the same inverted-sign trap one line below the horizontal one.

**Your step harness must run the frame, not just the simulation.** A step hook that calls only `game.update()` silently skips `controls.update()`, so an input test measures zero motion and reports "the key does nothing" for a fully working control. Expose a second hook that mirrors the render loop exactly:

```js
__DEBUG__.frame = (n, dt) => { for (let i=0;i<n;i++){ if(!over){ controls.update(dt); game.update(dt);} } snapCamera(); };
```

If input is consumed anywhere other than the sim step, testing input through the sim step is a measurement artifact, not a finding. When an input test reports zero, verify the harness reaches the input before suspecting the app.

**Removing an input mode is a completeness task, not a deletion.** Deleting the handlers leaves the systems that mode *implicitly covered* uncovered: world-bounds clamping typically lives inside the AI loop, which skips the player, so once a free-look mode is gone the only remaining control drives the entity in a straight line — straight out of the world. When you remove a control mode, re-audit every system it covered: containment, clamping, pause-on-blur, focus handling. Verify the survivors still work AND that the removed input is now inert — dispatch synthetic pointer events at the canvas and assert **zero** state delta, plus a source-level `search_files` for the removed mechanism, so no dead handler survives.

**Keyboard input needs focus on the element that listens.** A correctly dispatched
`Input.dispatchKeyEvent` still does nothing when the page's listener sits on a canvas
that has never been focused, and the result reads as "the control isn't implemented".
Give the target `tabIndex`, call `focus()`, then click it before dispatching keys, and
assert the move actually happened (a position delta) rather than trusting the dispatch.
This compounds with the keydown/keyup-timing pitfall: fix the focus first, then worry
about event timing, or you will misdiagnose a focus bug as a timing bug.

**A negative grep is not proof a feature is absent.** Searching for a guessed keyword
(`grep -i bloom`) and finding nothing does not mean the feature is missing — it often
means the codebase uses different vocabulary for it (`GLOW_FRAGMENT_SHADER`,
`glow_program`, `u_glow_strength`). Before reporting a capability as unimplemented,
search the **concept** with several plausible names and read the code that would call it.
Getting this backwards in both directions is costly: claiming "no bloom" when a bloom
pass exists, and reporting the user's already-working feature as a gap they must
fund. When you have already made such a claim once, correct it explicitly and name the
real symptom ("the glow pass is additive with no blur, so halos have hard edges") rather
than leaving the earlier sentence standing.

**Near-cull and far-cull are camera state.** A radius tuned for an establishing shot
deletes entire streets in follow mode; the frame goes empty while the triangle counter
climbs. Derive both from camera mode/distance and re-read the triangle count in each
mode after any change to them.

**Keep a runtime debug channel alive across refactors — it is your only instrument.**
Exposing a `window.__DEBUG__` object (player position, camera distance, occlusion
flag, entity pixel counts, vehicle positions) is what lets you verify a worker's
numeric claims without re-deriving them. It is also the first thing a later refactor
quietly drops, and once it is gone every claim becomes unfalsifiable prose. Add the
fields you will need up front, and assert the channel still exists
(`typeof window.__DEBUG__ !== "undefined"`) as part of your post-refactor check — a
vanished channel invalidates the evidence chain a previous worker built.

**Stale dev-server cache makes a correct fix look broken.** `python3 -m http.server`
sends `Last-Modified`, so the browser happily serves a cached JS module. You patch the
file, reload, the bug persists, and you "fix" working code. Send no-cache headers in a
tiny custom handler, and confirm the served bytes match disk before believing any
browser result:

```python
class NoCache(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        super().end_headers()
```

Verify: `curl -s <url> | wc -c` equals the on-disk size.

**`requestAnimationFrame` never fires in a background tab, so an `await frame()`
startup sequence hangs forever.** Race rAF against a timer:

```js
function frame() {
  return new Promise(res => { let done = false;
    const fin = () => { if (!done) { done = true; res(); } };
    requestAnimationFrame(fin); setTimeout(fin, 32); });
}
```

Symptoms: `ready` stays false, loader never disappears, and a `js()` probe that awaits
a promise times out at the harness level rather than in your code.

**Default-true boolean semantics silently disable the entire world.** If `isSolid()`
reads `!!def.solid` and only air/water set `solid: false`, every real block is
non-solid: nothing collides, the player falls through the planet, and the scene renders
fine (meshing does not use collision). Prefer opt-out:

```js
function isSolid(id) {
  if (B.AIR === id) return false;
  const d = BLOCKS[id];
  if (!d) return false;
  if (d.liquid) return false;
  return d.solid !== false;     // default solid; opt out explicitly
}
```

**Compute state that depends on movement AFTER integrating it.** Reading
`onGround`/position before the integration step yields the previous frame's values, so
landing detection and fall damage silently never fire. Capture the pre-move snapshot you
need (`prevY`, `wasOnGround`), integrate, then evaluate.

**Snap collision to the NEW position, not the old one.** `Math.floor(oldY)` when
resolving a downward collision ratchets the body up one block per frame instead of
letting it rest — the entity never truly settles.

**Keep the forward basis and the camera looking direction derived from one source.**
Deriving movement from `yaw` independently of `lookDirection()` invites a sign error.
Derive one from the other:

```js
const fwdX = -Math.sin(yaw), fwdZ = -Math.cos(yaw);  // == lookDirection().xz
const rgtX = -fwdZ, rgtZ = fwdX;                    // right = forward rotated -90° in XZ
```

**Sign conventions drift between systems.** A sun sprite placed with `-sin(t)` while
light intensity uses `+sin(t)` puts the sun below the horizon at noon. Derive every
consumer from one shared scalar per frame, and assert it (e.g. sun world Y must be
positive when the day phase is noon).

**Never animate a property of a SHARED resource to animate one consumer of it.** The
classic: an atlas packs every block texture into one image, and a water material that
reuses that same atlas instance. Scrolling `map.offset` to make water flow scrolls *all*
block skins — grass, stone and dirt visibly crawl. Symptom is "every block texture is
moving", reported against the game rather than the feature you just added. Give the
consumer its own texture instance:

```js
// water: its own texture, RepeatWrapping, and UVs remapped to 0..1 in the mesher
this.waterTex = new THREE.CanvasTexture(this.atlas.canvas);
this.waterTex.wrapS = this.waterTex.wrapT = THREE.RepeatWrapping;
```

The general rule: before animating a property of an engine object, ask who else holds a
reference to it. `map`, `material`, `geometry`, `uniform` and shared `Group` are all
aliasing hazards. Assert the fix numerically — read the shared resource's offset before
and after a second; it must not move.

**Entity ground snapping has two opposite failure modes; pick based on the scan depth.**
Both produce "the entity bounces forever" and they need opposite fixes:

```js
// WRONG: snap to Math.floor(newY) + 1  → raises the body a block, it falls again
// WRONG: scan downward for the first solid → over water, sinks to the sea floor
const footBlockY = Math.floor(this.pos.y - 0.02);      // from the PRE-move position
if (solid(this.pos.x, footBlockY, this.pos.z)) {
  ny = footBlockY + 1; this.vel.y = 0; this.onGround = true;
} else { this.onGround = false; }
```

Check exactly one cell, derived from the pre-move position. An open-ended downward scan
is not a fix for the ratchet — it introduces teleporting across water columns.
Entities that cannot swim must be blocked from entering fluid cells horizontally, and
their spawn must reject water-adjacent tiles, or they will walk into the sea.

**Random idle jumps read as "the entity is broken".** `if (Math.random() < 0.012) jump`
on an on-ground entity produces periodic hops that users report as constant bouncing,
interleaved with the real physics bug. Make locomotion-reactive: jump only when the
forward direction is actually blocked by exactly one block of height.

**Fluid sims: three separate ways they silently stall.**
1. Queue only the fluid's *neighbours* → a lone fluid cell never gets processed. Also
   queue the touched cell itself.
2. Gate lateral spread on "the cell below is already fluid" → fluid resting on stone
   never spreads at all. Let lateral spread depend only on the target being enterable.
3. Dedupe with a permanent `Set` → each cell is processed once ever, so a spreading
   front stalls. Use a bounded re-queue (e.g. max N enqueues per cell) that resets
   each tick, and cap work per tick so it converges instead of flooding.

Assert convergence, not just movement: in a sealed basin, a single source should fill
the floor area and the work queue should drain to zero.

**Judge terrain generation by its DISTRIBUTION, not by looking at it.** "The map
generator is bad" is not a diagnosis. Sample the height field over a wide area and
report percentiles plus local relief, then compare to the intent:

```js
const hs=[]; for(let z=-2000;z<2000;z+=23) for(let x=-2000;x<2000;x+=23) hs.push(w.heightAtTerrain(x,z));
hs.sort((a,b)=>a-b);
const n=hs.length, q=f=>+hs[Math.min(n-1,Math.floor(n*f))].toFixed(1);
// relief = q(1)-q(0); also count % of local 2-block steps that are <= 1 (i.e. dead flat)
```

A generator can report a 32-block `max` while `p25..p75` spans only 8 blocks and 100%
of local samples are flat — the range looks fine, the experience is a table. Relief and
flat-fraction are the numbers that actually move when you fix it.

**Threshold remapping must be calibrated against the noise's real distribution, or it
silently inverts the world.** Value-noise fBm centres on 0.5, so
`smoothstep(0.30, 0.72, n)` puts half the world below the midpoint — "coast vs
continent" becomes "50% ocean", and a mountain mask with a high threshold is zero almost
everywhere. Measure the layer before trusting the threshold:

```js
const st=(arr)=>{arr.sort((a,b)=>a-b);const n=arr.length;
  return {p5:+arr[Math.floor(n*.05)].toFixed(2), p50:+arr[Math.floor(n*.5)].toFixed(2),
          p95:+arr[Math.floor(n*.95)].toFixed(2), belowHalf:+(100*arr.filter(v=>v<0.5).length/n).toFixed(1)};};
```

Report `belowHalf` for a continent mask (want well under 50%) and for a mountain mask
(want well under ~90% zero). Re-check the biome histogram after every threshold change —
surface material, decoration and ore veins all sit downstream of it.

**Ridged noise is what makes mountains read as mountains.** Plain fBm gives rounded
hills. Fold each octave and multiply by the previous one so ridges only appear where
the low frequency already has mass:

```js
let prev = 1;
for (let i=0;i<oct;i++) {
  let n = noise2(x*f, y*f, seed + i*271);
  n = 1 - Math.abs(2*n - 1); n = n*n;         // fold -> ridge, sharpen
  sum += n * a * prev; prev = 0.5 + 0.5*n; f *= lac; a *= gain;
}
```

Allow negative terrain heights (deep ocean floor) when the relief demands it, and clamp
the *array index* to 0 while keeping the true height for surface/biome decisions —
otherwise a `-10` seabed indexes backwards.

**Spawn placement must run AFTER chunk generation, and validate real blocks.**
Selecting a spawn from the analytic height function spawns the player inside a cave or
over a void. Generate the surrounding chunks first, then require: block below is solid,
N blocks above are clear, and the chunk actually exists.

**A CSS class check is not a visibility check, and the overlay that never hides
is invisible to every assertion you write.** `.overlay { display:flex; background:... }`
with no `opacity` renders at full opacity from frame one, so a start panel AND a
game-over panel sit on top of the running game. `el.classList.contains('show')`
returns false the whole time — every state check passes, the game is unplayable,
and a screenshot is the only thing that catches it. Assert **measured**
computed style (`getComputedStyle(el).visibility === 'visible'` and
`opacity > 0.95`), never the class. Related: reading a CSS transition's
`opacity` in the same tick it starts lands mid-fade at 0 — poll until it settles
rather than concluding the element is hidden.

**A green assertion suite can still leave the game looking wrong.** Numeric
checks cover rules, growth, death, bounded oscillation — none of them cover
whether the subject is legible or whether the scenery frames it. Look at every
screenshot you capture. The defects that survive a fully green suite are always
proportion problems: scenery taller than the entire cast, or a camera offset in
fixed metres that frames the smallest and largest subject identically. Scale both
scenery and camera offsets to the subject's size, and re-assert with a pixel count
so the improvement is a number rather than an adjective — report the before/after
pair, because "it looks bigger now" is not evidence.

**The probe that reads pixels must use the drawing buffer's coordinate space.**
`canvas.width` is the drawing buffer (x `devicePixelRatio`),
`getBoundingClientRect().width` is CSS pixels, and `readPixels` reads the buffer —
mixing them pushes the sample box off-screen and returns a 0-pixel "invisible"
object. Watch units too: `project()` yields 0..1 while a wrapper returning
0..**100** needs a `/100` before it becomes a pixel offset. When a pixel count
drops from positive to zero after an edit, recheck the coordinate arithmetic
before touching the renderer.

**The chase camera must advance in the same step as the simulation you drive.**
Verification that calls `game.update()` manually measures a camera still inside
the rAF loop — which runs at ~1 fps under SwiftShader — trailing dozens of frames
behind, so the subject projects off the bottom of the screen and a correct entity
reads as invisible. Expose `snap()` (set position/look directly, no exponential
damping tail) plus a hook that steps sim *and* camera. Damping converges
asymptotically, so "wait long enough for the lerp" is not a substitute.

**Two paths to the same outcome means testing both.** The AI chase and the
proximity sweep in `update()` can each end the run; wiring `over` + the death
event in only one leaves a silent death (fish gone, no overlay, `over` false).
When a bug only appears through one path, the other is usually an untested
duplicate — `search_files` for every site that mutates the same terminal state.

**An entity that reports itself present is not an entity on screen.** Image analysis of a rendered
scene produces false positives — it will confidently report "floating detached tree
foliage" and duplicate key bindings that do not exist. Confirm any visual claim with a
targeted probe before you act on it: a DOM query for text, a numeric scan for
unsupported blocks, a direct read of the object's position. Then say so in your report.

**A debug snapshot read twice in the same turn is a stale value, not a frozen
simulation.** Reading a state object immediately after driving input — or twice within
one awaited batch of synthetic key events — routinely returns the pre-input frame,
which reads as "the entity is not moving" and is entirely a measurement artifact.
Sample twice with a real interval between reads, and confirm the frame counter is
advancing across both, before concluding a system is static. When a worker reports
"sprite X moves" and your own probe says it does not, suspect the probe first and
re-measure before you report a regression to the user.

**Dispatch keydown and keyup as separate awaited events with a tick between them.**
Firing both in one `await` batch (or back-to-back with no delay) delivers a press and
release within a single event frame; handlers that advance state on the press and
render on the next frame never observe the intermediate state, and the action appears
to do nothing. A phase toggle then reads as "the key is broken" when it is working
perfectly. Insert a small sleep after keydown, verify the state changed, then release.

**Headless screenshot flags that time out on an animating page prove nothing.**
`--screenshot` with a virtual-time budget can hang indefinitely on a page holding a
`requestAnimationFrame` loop and produce no file. Drive screenshots over CDP
(`Page.captureScreenshot`) on a debug-port browser instead; treat the absence of a
file as "this method does not apply here", never as evidence about the app.

**Pointer lock can't be automated; do not treat that as a broken feature.** Mouse-look
requires a real user gesture, so scripted `movementX` will be ignored headlessly. Verify
mouse-look by driving the yaw/pitch fields directly and asserting the movement invariant
holds at each — that is the part actually under test.

## Delivery

- Ship a no-cache dev server script alongside the project.
- A README with: how to run, controls table, module map, and an explicit
  "known trade-offs" list (no save/load, no mobs, no crafting). Stating gaps prevents
  them from reading as bugs.
- If deploying to a host, deploy the **rewritten** artifacts and re-verify on the live
  URL — local success does not imply the deployed graph resolved. For importmap-based
  ES modules, the bare specifier is a dependency edge that must be rewritten like any
  other (see `hyperlane-upload`).

## References

| File | Contents |
|------|----------|
| `references/browser-verification-harness.md` | Assertion-harness patterns: movement-basis sweep, physics settle/jump/damage, fluid convergence, terrain + noise-layer distribution, shared-resource animation, entity stability, bounded-oscillation probe, CDP synthetic-input focus+timing, sky-lighting assertions, cache-byte verification |
| `references/input-and-frame-hooks.md` | Input-layer probes: the `frame()` vs `settle()` hook split, per-key steering asserted in world space with A/D symmetry, the zero-uncaught-exceptions gate, and the completeness checklist for removing an input mode |
| `references/voxel-engine.md` | Chunking, face-culled meshing, texture atlas, per-vertex AO, day/night, cloud and entity systems |
| `references/third-person-camera.md` | Occlusion pull-in (multi-probe rays, behind-ray sign bug, damping), near-cull as a camera parameter, framing maths, pixel/batch-hide proof the character renders, swallowed-upload-error root cause |
| `references/feature-request-triage.md` | Cost-ranking table for large feature lists, manifest audit before dispatch, 2D-collision limits vs enterable interiors, multi-worker coordination under a shared tree |
| `references/infinite-world-streaming.md` | Fixed map → infinite coordinates + streaming: per-layer table, the two claims that get conflated, closed-form street predicates, block-relative hand-placed content, and the three generator bugs (shadowed centre param, shared axis interval, interval from unrelated centres) with the probe that catches each |

## Quality gates

- [ ] Every player control has an assertion that fails without the feature
- [ ] Page has **zero uncaught exceptions** after a run, and the harness reads the
      error list (not just the pass count) — an exception inside rAF keeps the scene
      animating while the control is dead
- [ ] Every steering key asserted in WORLD space, with A/D symmetry
      (`|yawA + yawD| < 1e-3`); no assertion encodes a single sign convention
- [ ] The input test drives a hook that runs the REAL frame (`controls.update()`
      then `game.update()`), not a sim-only step
- [ ] After removing an input mode: the removed input provably does nothing
      (synthetic events -> zero delta, plus a source `search_files`), and every system it
      implicitly covered (containment, clamping, focus) still runs
- [ ] Synthetic keyboard input is dispatched to a *focused* element and produces a real
      position/state delta (focus before timing; a no-op dispatch is a focus bug, not a
      missing feature)
- [ ] Every periodic/accumulating quantity (gait phase, spin, orbit) is **bounded** when
      evaluated over time, and reaches 0 when its amplitude envelope fades
- [ ] Movement invariant holds at ≥4 yaw angles, not just 0
- [ ] Player character proven visible by pixel count in its screen region (> 0), not
      by HUD text or a rig existing
- [ ] Character pixel count is a plausible human size, and each limb batch's isolated
      box matches its box in the full scene (catches double-registration aliasing)
- [ ] Vertex/instance colour is confirmed *consumed* in the fragment shader, not just
      uploaded; tone mapping is luma-based and identical across GPU and CPU paths
- [ ] Camera occlusion proven by a distance delta between open and occluded states
- [ ] Character occupies a readable fraction of frame height and sits near centre
- [ ] Served file bytes match disk (no stale cache)
- [ ] Startup completes with the tab backgrounded
- [ ] Collision settles to a stable resting state (no per-frame ratchet)
- [ ] Entities are classified, not just range-checked: oscillating (physics bug) vs
      one-off descent over a ledge (correct) are different verdicts
- [ ] Fluid sim converges (queue drains) in a sealed container
- [ ] Sky/light shared-phase consistency asserted
- [ ] Animated materials own their textures; a shared resource's animated property is
      asserted to stay constant
- [ ] Terrain reported as relief + flat-fraction + biome histogram, not a screenshot
- [ ] Noise thresholds validated against a measured layer histogram
- [ ] README lists known trade-offs
- [ ] Any graphics technique the user requested by name is delivered under its true name,
      and every substitution (e.g. requested ray tracing delivered as shadow map + SSAO
      + SSR) is stated explicitly in the final message with what the real thing needs
- [ ] Each requested feature was classified against the existing asset list before any
      worker was dispatched, and the cost-ranking table was shown to the user
- [ ] Slabs/treads provide vertical support only; only walls block laterally, and a
      player standing on a tread is never ejected sideways by it
- [ ] If the world claims to be infinite: a far-centre test builds ground/water
      thousands of metres out and asserts per-axis vertex extent against that
      centre, AND the collider layer has a load/unload lifecycle (a collision
      world built once at init bounds the player regardless of how far
      generation reaches)
- [ ] Streamed surfaces rebuild on a distance threshold, not per frame, and a
      browser run confirms the recentre fires while the player's height stays at
      ground level for the whole run
- [ ] At least one test walks the **whole route** (outside → doorway → partition gap →
      first tread → top of the stair → upper slab) and asserts the final height, not
      just per-subsystem units
- [ ] Any root cause reported was measured on a target the probe was proved to have
      sampled, and every diagnostic edit was reverted — diff the file against the last
      good commit and confirm no speculative wall, widened tolerance or early-out
      remains
- [ ] A skipped post-processing pass neutral-clears its target (no smear of the
      disabled effect on the downgrade frame); any target sampled by the main pass
      documents whether it is same-frame or one-frame-late
- [ ] FPS is compared only against a baseline measured on the same rasteriser, and is
      never extrapolated from a software-rendered headless run to real GPU hardware
- [ ] `git status --short` re-checked after dispatch; concurrent edits by unowned
      files reported rather than silently merged
- [ ] The build was re-run to green **after the final edit**, not just after the last
      change observed mid-session
