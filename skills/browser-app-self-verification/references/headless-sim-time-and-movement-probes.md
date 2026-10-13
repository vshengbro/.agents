# Driving a real-time simulation from a headless harness

Depth for the case where the app under test *is* a running simulation —
game loop, physics, streaming world — and the harness has to drive it and
read it back. The recurring trap is that a headless browser runs the loop at
a small fraction of real speed, so every wall-clock-based wait in the harness
is wrong, and the resulting symptom looks exactly like a game bug.

> **Companion:** `cdp-round-trip-cost.md` covers the *other* half of the
> budget — a harness that waits correctly for the simulation can still be
> slow because the round trips themselves dominate. Read both before
> concluding a slow run is a slow frame rate.

## Measure the time scale before writing any wait

A tab in the background throttles `requestAnimationFrame` to near zero, and
most engines additionally clamp the per-frame delta so one long frame cannot
tunnel the physics (`MAX_FRAME_TIME`, `dt.min(fixed * k)`). Together these
make the simulation advance a *fraction* of wall-clock seconds per second.

The number is not guessable — measure it:

```python
before = await st()                       # pos, vel, frames
await ev("window.__app.press('forward')")
await asyncio.sleep(1.5)
after = await st()
print(after["pos"] - before["pos"], after["vel"], after["frames"] - before["frames"])
```

A velocity of `2.8 m/s` with a displacement of `0.19 m` over 1.5 s is the
signature: **the simulation advanced about 0.07 s of simulated time in 1.5 s
of wall clock.** Nothing is wrong with the movement code.

**Rule: drive the harness on simulated displacement, never on wall-clock
sleeps.** Poll until the measured position has moved the distance the step
was supposed to cover:

```python
async def step_until(d, want_move, cap=26):
    s0 = await d.st()
    x0, z0 = s0["px"], s0["pz"]
    for _ in range(cap):
        await asyncio.sleep(0.12)          # poll fast, threshold decides
        s = await d.st()
        if math.hypot(s["px"] - x0, s["pz"] - z0) >= want_move:
            return s
    return await d.st()
```

`cap` is the real time budget — `cap × poll_interval` — so it has to be set
deliberately, and a cap that is too large is what turns one stuck leg into a
fifteen-minute hang.

### Fix the browser before you compensate for it in the app

Every recipe on this page assumes a throttled clock. **The throttle is
frequently a broken browser session rather than a property of the engine**,
and it is removable — after which every compensation below becomes wrong.
Establish the real frame rate before writing any of them, because the correct
harness shape is different on each side of 60 Hz:

| | ~1-5 fps | real 60 Hz |
|---|---|---|
| how to advance a leg | `step_until(distance)` | `step_until(distance)` or a fixed poll count |
| arrival radius | needs a big multiple of the poll displacement | any sane body-width value |
| stall threshold | must be *below* one poll's displacement, or every moving walker reads as stuck | a fraction of a body width |
| time-scale multiplier | may be worth adding | **harmful — see below** |

See `chrome-devtools-protocol` § "When a headless page runs at 1-5 fps" for the
launch flags that get a real 60 Hz and for the one-variable-per-run discipline
that keeps the measurement honest.

**At 60 Hz a time-scale multiplier becomes a tunnelling bug.** A multiplier
added to compensate for 1 fps advances 4 s of simulation per 16 ms frame, which
is 18 m of travel at walking speed against a 0.2 m wall — the agent passes
clean through the facade and the run then reports a collision failure in a
building whose geometry is correct. Delete the multiplier the moment real
frames arrive; it is scaffolding for a condition that no longer holds. The same
applies to stall thresholds tuned against a 1-fps poll: `0.12 m` is below one
60 Hz poll's displacement, so a walker merely grazing a jamb reads as "moving
backwards", gets recovered, and is thrown down the street.

**Poll-count waits survive the transition; distance waits do not always.** A
fixed `settle(polls=n)` is a unit that means the same thing at any frame rate,
so prefer it where the leg is short. But when the time scale is *raised*, one
rendered frame can cover the whole leg, so `step_until(want_move)` returns on
its first poll and the leg never happens at all — the shape of that failure is
a leg that reports success having covered nothing.

**Recovery must not be able to make the situation worse.** A bounded slide that
ends further from the target than it started has pushed the agent out of the
building, not around the corner, and every leg after it begins from the
street. Give the displacement back before re-attempting:

```python
if math.hypot(tx - nx, tz - nz) > math.hypot(tx - px, tz - pz) + 1.0:
    await teleport(d, px, pz)     # undo the hop, retry from where we were
```

**Invulnerability must be set before the walk starts, not inside the first
leg.** At 60 Hz the agent crosses a street in two seconds and takes fire long
before a helper that enables it on entry to `walk_to` has run; the respawn
lands mid-route and every later leg starts from a hospital. Set it once, right
after the spawn teleport.

## "It did not move" is a four-way ambiguity

`displacement == 0` has four causes that produce identical output from a
position-only probe, and they need different fixes:

| Symptom | Cause | Distinguishing read |
|---|---|---|
| no displacement | headless time throttle (above) | `vel` is non-zero and correct |
| no displacement | the actor is in a vehicle, and "move" is throttle | a `driving`/`vehicle` flag is set |
| no displacement | the walk intent never reached the sim | `vel` is zero *and* the intent is zero |
| intermittent "no displacement" | **the harness is sampling a throttled debug channel** | frame indices have **gaps**; no lag-N peak |

The fourth is the expensive one, because it produces *precise, quantified,
false* readings that read as application bugs. See the next section.

So publish **velocity and the intent alongside position** in the debug
payload, and read all three. A correct velocity with zero displacement is a
harness-timing problem; a zero velocity is a real movement problem. Chasing
the second while the first is true produces dozens of rounds that change
nothing.

## A throttled debug channel fabricates defects

Apps commonly publish harness state on a throttle for debugging:

```js
if (frame % 3 === 0) window.__dbg = snapshot();   // fine at runtime
```

A sampler polling `__dbg` counts **skipped writes** as "the value did not
change". Nothing about the app is wrong; the instrument is lossy, and every
verdict it produces is fabricated with real-looking numbers. One such channel
produced, from the same run: a walk that "stalls" half its frames, a
mouse-look reading eight consecutive zero deltas, and a weapon reporting
"fired 14 times, ammo unchanged" — three separate "bugs", one cause.

**The decisive check is frame-index contiguity**, not any threshold:

```python
frames = [s["frame"] for s in samples]
assert frames == list(range(frames[0], frames[-1] + 1))   # gaps => sampler is the bug
```

Two corroborating reads, both cheap:

- **Print the gap stride next to the claim.** `fromF 57  toF 60  gap 3` shows
  the throttle directly in the data.
- **Autocorrelate the per-step series.** A genuine period-N stall peaks at
  lag N (`lag3` dominant for "move 2, freeze 1"). Throttled sampling of a
  smooth signal peaks at lag 1 and decays monotonically. Measure this before
  concluding periodicity exists.

A **real** stop is contiguous and explainable — zero-step samples arrive as
one consecutive run (frames 128..135) while every other frame advances, with
a wall or boundary named in the neighbourhood query. Artefact and reality are
distinguishable; do not file either before distinguishing.

**Corollary: re-running the same probe with the same sampling method cannot
resolve it.** It manufactures a second, equally false number to argue about.
Re-measure with an unthrottled sampler — parse the on-screen HUD every frame,
or run the sampling loop inside the page against a per-frame hook. Slower per
sample, vastly cheaper than a wrong verdict.

## Under a saturated frame-time cap, two modes measure as identical

When the loop clamps delta time (`MAX_FRAME_TIME`) and the real rAF interval
is longer than the cap, **every** frame is clamped and the sim advances a
fixed number of substeps. Per-frame displacement becomes
`N * speed * cap` and becomes **independent of which mode is measured**:

```
rAF median 0.5833 s   cap 0.25 s   frames over cap: 83/83
speed * cap = 0.3067 m/frame    measured = 0.6133 m/frame  (= 2 substeps)
```

A sprint/walk ratio measured this way reads ~0.95 and looks like "sprint is
slower than walk, or the sprint key is not bound". Neither is true — both
modes are clamped identically.

**Rule: assert mode differences against the constants, never against a
per-frame observation under saturation.** Grep the speed/accel constants and
compare them statically; use the runtime ratio only when the measured frame
interval is below the cap. Check the cap before trusting any speed,
acceleration, cooldown, or "the effect is weaker than expected" verdict from a
headless software-rendered run.

**The corollary is a discipline rule, not just a technique.** A ratio that
*looks* like a deep root cause — `0.945` matching an unrelated
`sprint/walk 0.94` reading, apparently a second manifestation of one bug — is
the most seductive kind of finding in a bug hunt, because it unifies two
observations. **Before building a theory on an unexplained number, establish
that the number was measured under conditions where it could mean anything.**
Here it took three probe rounds to retire a phantom root cause whose
conclusion had already been reported to the user and had to be retracted. When
you retract, correct the record explicitly and say which part was wrong —
concluding the opposite silently is its own failure.

**A missing harness field masquerades as a bug.** Debug JSON is usually
projected through a hand-maintained field map in the harness. Adding a field
in the app without adding it to that map yields `None` every time, which reads
as "the app never set it". When a field you just added always comes back
`None`, check the projection before concluding anything about the app.

## Position readback: record every stage, and name the stage you query

A single final coordinate cannot answer "why is the actor pinned in place",
because the movement step is a **pipeline of position writers**. Static
resolution, an interior/vertical pass, and a dynamic-body pass each write the
position in turn, and the passes are not disjoint in what they can touch: a
stage named for the vertical axis commonly ends in a whole-position write that
overwrites the horizontal ones too.

Publish the position after each stage and diff them. The stage whose output
stops changing is the one holding the actor; everything before it is the
question, everything after it is the consequence.

```
afterStatic  =  <stopped here>     <-- the actor's own collision resolution
afterVertical=  <moved>           <-- fine, it only adjusts height
afterDynamic =  <moved>           <-- fine
```

Two failure modes make the naive version of this probe useless:

- **Containment is not contact.** A boolean "is the actor's centre inside a
  collider" is `false` while the actor is pressed against the *face* of one,
  which is the ordinary case for a blocked walk. Report the **distance to the
  nearest surface** as well; a blocked actor reads as a sub-decimetre distance,
  a fallen-through actor as zero.
- **Query the stage that stopped it, not the final position.** A later stage
  can push the actor to the other side of the obstacle, so a neighbourhood
  query at the final coordinate comes back empty while the two stage readings
  sit centimetres apart — a self-contradictory report that sends the next round
  investigating the wrong side of the wall. Nearest-shape dumps are diagnostic
  output for a specific frame; read them against the stage that produced the
  number they are explaining.

## Two different starts landing on the same point proves a destination

When position evidence contradicts a movement model, the fastest discriminator
is whether repeated runs converge on **one** point:

```
start A (28.30, 26.40)  ->  (33.50, 32.89)
start B (35.02, 25.35)  ->  (33.53, 32.89)
```

Collision resolution never lands two unrelated starts at the same coordinate
to within 3 cm. A spawn point, a respawn anchor, a hospital location, or a
teleport destination does, every time.

**Rule: when a position jump repeats the same endpoint across different
starts, stop reading it as navigation and go looking for a teleport
destination in the app.** The candidate list is short: spawn, respawn, hospital,
checkpoint, level entry, and the harness's own teleport seam.

Restoring health is not enough to stop a respawn. If the health hit zero
before the invulnerability was applied, the death branch has already latched a
respawn timer, and topping health back up leaves the timer running — the next
respawn fires and throws the actor across the map mid-run. Invulnerability has
to clear the *latch*, not just the gauge:

```rust
if game.safe_mode {
    game.hurt.revive();            // clears the pending respawn
    game.player.set_health(PLAYER_MAX_HEALTH);
}
```

## A threshold stricter than the obstacle manufactures a failure

When the actor is stopped by a wall but the harness keeps pushing, the harness
usually decides it is "stuck" by comparing its position to the target. Two
thresholds then matter, and the wrong ratio is self-reinforcing:

- **arrival radius** — if this is tighter than the actor's clearance of the
  obstacle, standing correctly *next to* the target counts as failure, and the
  recovery behaviour fires.
- **recovery trigger** — the recovery then does something large and wrong,
  moving the actor further away than the problem ever was.

Pick the arrival radius from the geometry (a doorway is narrower than a room),
and gate recovery on *distance remaining* above a floor well clear of the
arrival radius. Give both a short comment saying which number came from
which measurement, because the next session will otherwise re-tune them
against each other.

Recovery that picks a direction must be **bidirectional and length-bounded**:
try both perpendicular senses, re-issue the intent every short hop rather than
one long slide, and stop when progress is real. A single long slide overshoots
at accelerated time scale, and a fixed fan of large angles can carry the actor
through the obstacle it was meant to clear.

## What a navigation harness cannot do, and what to publish instead

A local waypoint list plus reactive wall-avoidance is not a path planner. It
handles a clear approach and a doorway; it does not route through a corridor
that requires choosing a side and then crossing back. When the behaviour under
test is *position-continuous* — stairs, ramps, narrow gaps, floor support —
the honest split is:

- the **app's own verified route** (the one its end-to-end test walks) decides
  *where* to go, and must include the "go deep before turning" waypoint that
  a door pocket requires; and
- the **harness** decides only *how* to cover each leg, and covers every metre
  through the real integration.

Publish the route from the app rather than letting the script re-derive it,
and include the intermediate waypoints the geometry implies. A route missing
the "enter, go deep, then turn" point is not a harness bug — it is a route
that cannot physically be walked, and it will read as broken navigation.

## Derive the route geometry from the transform, do not iterate on it

A waypoint route authored by hand against a rotating asset is a guess with
a long feedback loop. Invert the rotation once and the route becomes
arithmetic — for a yaw of ±π/2, the mapping is simply

```
world X = centre.x + local.z        world Z = centre.z - local.x
```

and every key position (door face, wall line, opening, stair centreline,
stair top) falls out of the local numbers already in the source. Two classes
of bug disappear when you do this rather than re-tuning:

- **Degenerate waypoints.** Two points that differ only in a local axis that
  maps to a *constant* world axis rotate onto the *same world position*, so
  the route spins in place. Assert it: adjacent waypoints must be further
  apart than one body width.
- **Wrong-direction edits.** "Step further into the room" written as
  `part - delta` may step *past* an obstacle sitting at that very local
  coordinate; and after a ±90° swap a constant that reads as "further in"
  actually moves the point *back toward* the door. Assert it: every leg must
  move on exactly one axis, because a diagonal inside a walled interior
  always jams on something.

These are cheap assertions and they catch more than a round of browser runs:

```rust
for pair in route.windows(2) {
    let gap = ((pair[1][0]-pair[0][0]).powi(2) + (pair[1][1]-pair[0][1]).powi(2)).sqrt();
    assert!(gap > 0.9, "{} consecutive waypoints are {gap:.2} m apart", MSG);
    assert!((pair[1][0]-pair[0][0]).abs() < 0.01 || (pair[1][1]-pair[0][1]).abs() < 0.01,
            "{} a leg moves on both axes", MSG);
}
```

**An end-to-end test written entirely in local coordinates cannot see any of
this** — it never touches the transform and never inspects route geometry.
Any invariant that only exists *after* a transform has to be asserted after
the transform too. Prefer a helper that inverts it (`to_local` for a
`to_world` point) over re-deriving the trig in the assertion; the
re-derivation is itself a place to get the sign backwards.

## A repeated endpoint at several time scales is a fixed face, not overshoot

When a leg ends at the same coordinate under several time scales, movement
speed is not the variable — a stable collision face is:

```
1x   -> (29.70, 30.00)  ends (29.19, 30.00)
2x   -> (29.70, 30.00)  ends (29.19, 30.00)
4x   -> (29.70, 30.00)  ends (29.19, 30.00)
```

Before tuning arrival radii or poll intervals, vary the time scale once. If
the endpoint does not move, no amount of threshold tuning will reach the
target, and the remaining question is purely geometric: which surface is
this? Sample the path *between* the endpoints — a trace like
`29.70 → 28.67 → 26.83 → 26.46 → 28.27` says the actor passed the goal
comfortably and was thrown back by something past it, which is a different
diagnosis from "cannot get there" and names the obstacle.

**Log every sub-sample of a leg, not just its endpoints.** A trace line
per `step_until` is the cheapest diagnostic in this whole file: the two
cases above are indistinguishable from endpoints alone and obvious from a
trace.

## Do not let recovery leave the actor worse off than the problem

A recovery that fires on "stuck" and then throws the actor across the room
makes the *next* leg start from somewhere unrelated, so one bad leg
contaminates every leg after it. The failure is subtle because the run keeps
producing plausible-looking positions.

- **Re-issue, do not declare victory.** On stall, re-read the position and
  restart the leg from where the actor actually is. Returning a position
  several metres from the target because "we made progress" is what turns a
  one-leg problem into a whole-route failure.
- **Scope each correction to the case that needs it.** Squaring up on the
  doorway axis is what lets a 1.6 m opening accept a 0.3 m offset — but
  applying that alignment to *every* leg pushed the actor back out onto the
  street, further from the goal than the unaligned version was. Globalising
  a local correction is a regression that still passes the eye test.
- **Clear stale intents before sampling.** A walk/seam request left set
  from a previous run keeps pushing after a teleport, and the first sample
  then describes the leftover intent, not the current leg. Zero the request
  and let it be consumed before the first position read.

## A correction that moves an already-passing leg is not a fix

Multi-step routes make local fixes deceptively expensive: the leg you fixed
and the leg before it share a starting position, so tightening or loosening
anything perturbs both. Re-run the legs that already passed after every
change, and keep the harness cheap enough (a route-only probe, separate from
the full suite) that this is a two-minute check rather than a twenty-minute
one.

Split the harness so a subset can be driven alone. Extract the shared
helpers into an importable module and have the route probe drive just the
route; importing a script whose body runs a whole suite at import time makes
every focused re-run a full run.

## A stale artifact after an incremental build

`cargo build` printing `Finished ... in 0.03s` means **nothing was
recompiled**, so re-running the binding generator emits the previous artifact
and the new debug field is simply absent — indistinguishable from a field the
app never sets. `touch` the source before a build you expect to change, and
confirm the field landed in the emitted artifact:

```bash
touch src/game.rs && cargo build --release --target wasm32-unknown-unknown
wasm-bindgen --target web --no-typescript --out-dir www/pkg --out-name app \
  target/wasm32-unknown-unknown/release/app.wasm
grep -c 'newFieldName' www/pkg/app_bg.wasm   # 0 means the artifact is old
```

## A geometry seam that unit tests cannot see

When an interior walk route, a doorway, or a walkable region is declared in
two places — the collision world and the interior/floor world — the unit tests
routinely use **both declarations from the same side** and stay self-consistent
while the browser disagrees. The classic shape: a door placed on the
*interior* clear-span boundary while the wall sits one wall-thickness further
out, so the "1.5 m outside the door" waypoint lands in the pocket **between**
the two walls.

The symptom is precise and worth recognising on sight: the actor enters the
doorway, cannot be pushed further in, and is pushed back out — repeatedly,
along one axis.

**Rule: for every place the app publishes as geometry, derive the value once
and derive the collision from it.** A named constant in one module beats the
same literal appearing in the wall builder and the doorway helper, and it is
the only form a test can pin:

```rust
pub const SHOWCASE_WALL_THICKNESS: f32 = 0.2;

pub fn showcase_door_center(index: usize) -> Vec2 {
    // door on the OUTER wall face, not the interior clear span
    showcase_to_world(index, [0.0, half[1] + SHOWCASE_WALL_THICKNESS])
}
```

Then write the test that would have caught it — invert the transform and
assert the local coordinate lands on the outer face, for **every** instance
with differing geometry, not just the first:

```rust
let local = showcase_to_local(index, showcase_door_center(index));
assert!((local[1] - (spec.half[1] + SHOWCASE_WALL_THICKNESS)).abs() < 1e-3);
```

The general rule: **when a browser probe and the unit tests disagree about
geometry, the tests are probably reading the same declaration the app
collides with, and the seam between the two is where the bug is.** The
browser is the only side that sees both.
