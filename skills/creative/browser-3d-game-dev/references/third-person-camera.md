# Third-Person Camera: Occlusion, Framing, and Proving the Character Is On Screen

A third-person camera is a separate system from the character, and it has two failure
modes that look identical from the outside: the camera ends up **inside geometry** (the
user sees a wall filling the frame and calls it "clipping" / 穿模 / "models not
showing"), or the camera is **mis-framed** (the character is a few pixels in a corner).
Fix them separately — tuning the follow distance does nothing for occlusion, and adding
occlusion avoidance does nothing for framing.

## 1. Camera occlusion pull-in

**The rule:** the camera's desired position is the maximum distance along the
player→camera ray that is not inside a collider. Compute it, then damp toward it.

Reuse the *same* collider set the player collision already uses. A second, parallel
collider representation for the camera is a guaranteed source of disagreement.

```
desired = player + offset(yaw, pitch, desiredDistance)
// cast toward the desired eye, take the tightest hit across all probes
allowed = min(desiredDistance, min over probes of (hitT - skin))
current = approach(current, allowed, damping * dt)   // never snap
```

Four things that decide whether this actually works:

- **Damp, don't snap.** A one-frame jump reads as a jolt every time the player rounds
  a corner. `approach` toward the target each frame; on occlusion it pulls in fast
  (the alternative is a frame of wall in the player's face), and returns slowly.
- **Probe more than the center line.** A building at the frame edge leaves the center
  ray clear while still occupying a third of the screen. Cast center plus the two
  frustum-edge directions, and take the **tightest** result. Width each offset by a
  fraction of `tan(fov/2)` — full-width probes are too aggressive and pin the camera
  to the player's head.
- **Reject boxes *behind* the ray.** The classic sign bug: a box behind the origin
  yields a negative-or-zero `t`, which you must reject rather than treat as a hit at
  `t = 0`. Left unfixed, the pull-in computes a negative distance and shoves the
  camera **behind the player** every time they face away from a building — which the
  user experiences as the camera flipping wildly. Write a unit test that places a box
  behind the ray origin and asserts the result is a miss.
- **Verify with numbers, not adjectives.** Read the actual camera distance at three
  states and report them: open ground, occluded, and recovered.

  | state | distance | occluded flag | clearance |
  |------|----------|---------------|-----------|
  | open | 8.20 | false | 8.24 |
  | occluded | 7.40 | true | 0.99 |
  | recovered | 8.18 | false | 2.91 |

  A 0.8 m reduction proves the branch fires. "Looks like the camera avoids walls"
  proves nothing. Sweep the yaw (e.g. 10 angles at spawn) and report the fraction that
  pulls in — if *every* angle shortens, you built a constant shrink, not avoidance.

## 2. Near-cull is part of the camera, not a constant

A hardcoded near-cull radius tuned for a wide establishing shot **deletes the entire
street** at third-person range, and the frame goes empty while the triangle counter
still climbs. Make the cull radius a function of camera mode (first-person vs
follow) or camera distance, and check the triangle count across both modes: a jump
like 465k → 482k after a "near-cull" change is a strong signal the radius moved.

## 3. Framing

Target: character clearly readable, roughly 5–20% of frame height, positioned near
centre and slightly below. Estimate it analytically before touching anything — at
`FOV_Y` in radians, a character of height `h` at distance `d` occupies
`h / (2·d·tan(FOV_Y/2))` of frame height. Use that to set the default distance, then
confirm with the pixel probe below.

Keep the character off the frame edge: derive the camera's look target from the
player's position plus a fixed offset, so player rotation slides the view smoothly
instead of flipping the character across the screen.

## 4. Proving the character is actually drawn

"A HUD says third-person" is not evidence, and neither is a screenshot that a vision
model describes without mentioning a person. Vision models miss small characters
constantly. Quantify it:

- **Pixel probe.** With the character standing still, sample a bounding box around
  its expected screen position and count pixels that differ from the background.
  That count must be **> 0**. Report the number, plus a sampled colour from the
  character's body region.
- **Batch-hide differential.** If the engine supports a `?hide=<batch-index>` query
  parameter, hide the character's limb batches and diff the pixel region against the
  the unhidden frame. A **zero**-pixel diff is decisive proof the batches never reached
  a draw call, and it localises the bug to upload/batching rather than to shading or
  framing. This is the single highest-value probe in this whole class of work.
- **Isolate-one-batch A/B.** Hiding everything *except* one limb batch and measuring
  its screen bounding box distinguishes the three failure families in one shot: a
  correct small box means the mesh is fine and the defect is in how batches combine;
  a huge box means this batch's binding is wrong; a zero box means it never drew.
  Compare the isolated box against the same batch's box in the full scene — a
  single batch measured only inside a merged scene conflates "wrong mesh" with
  "right mesh, wrong index".

## 5. The invisible entity: index aliasing, not the swallowed error

When an entity is missing while every count looks healthy, the first hypothesis is
almost always **wrong**. The tempting one — an error swallowed at the upload boundary
— is worth logging anyway, but logging it is not diagnosing it, and treating it as
the root cause sends you into a fix that changes nothing.

```rust
// WRONG — failure is silent, so the real reason stays invisible...
let _ = webgl.upload_mesh(mesh);
```

```rust
// ...but logging it tells you the *upload* succeeded; the defect is elsewhere
if let Err(e) = webgl.upload_mesh(mesh) {
    console.log(&format!("{PREFIX_UPLOAD_FAIL}{e}"));
}
```

**The dominant cause is index aliasing from a push-semantics registration call.**
If `upload_mesh` appends and returns `len - 1`, calling it once per build pass and
again per entity doubles the GPU-side table: batches index `0..N` while the table
holds `2N` entries, so late batches resolve to whatever mesh happens to sit at that
index. A character rig then renders *something* — typically large world geometry
drawn with the character's tiny model matrix, i.e. a screen-filling block instead of
a person, or in the strict case nothing at all. The counts stay healthy because the
draw call is issued; only the *binding* is wrong.

- **Register each mesh exactly once**, at one call site, and comment the invariant so
  a later edit does not reintroduce a second pass.
- **Prove which mesh a batch actually resolves to.** A single batch rendered in
  isolation shows its true size (e.g. a 28×45 px human); the same batch inside the
  full scene covering 130,000 px is index aliasing, and that A/B is the fastest
  localisation available. Compare the isolated and merged renders before theorising.

**Never report an entity feature as delivered on the strength of the rig being
"built".** A rig with 13 limb batches bound to the wrong meshes is not a character.
Gate on `pixelsPainted > 0` and on that pixel count being a plausible human size.
