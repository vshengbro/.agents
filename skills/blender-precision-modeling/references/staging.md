# Staging: lights, camera, exposure

The harness stages every model identically, which is what makes two renders
from different days comparable. You do not normally call any of this directly —
`run_model.py` does it from the model's own bounding radius.

## Tested and rejected: a small hard specular light

The four-large-soft-light rig looks under-defined, so the obvious product-
photography move is a small hard source for a crisp highlight. Measured, and it
loses:

| surface | bright-pixel fraction | local edge |
|---|---|---|
| ceramic | 0.428 -> 0.467 | 0.037 -> 0.030 |
| steel | **0.211 -> 0.087** | 0.022 -> 0.026 |
| rubber | 0.000 -> 0.042 | 0.025 -> 0.028 |

Visually the steel lost its per-face gradient and the floor picked up a harsh
hotspot. The small source raises the calibration ball's reading, so
auto-exposure pulls back and darkens everything; the highlight it adds is
smaller than the exposure cost.

**The soft rig stays.** If a render reads as matte or plastic, the fix is the
model's material — a higher-contrast pair of materials, a lower roughness on
the part that should be glossy — not the studio. Do not add a hard light.


## The six views do not share one backdrop

Measured across 40 models, backdrop luminance is a pure function of the shot
angle, not of the model:

| shot | backdrop |
|---|---|
| side, front | 0.220 |
| hero | 0.325 |
| top | 0.339 |
| **rear** | **0.701** |

The floor is a plain diffuse plane, so which lamps reach the patch of it that
fills the frame changes with the camera. The `rear` view looks straight into the
key's lit region.

This is physically correct and it is also a presentation problem: a six-angle
set should read as one shoot. A vision scorer capped every presentation score at
4/5 because of it.

**Fix, when the staging changes anyway:** give the floor a little self-emission
so it is dominated by its own output rather than by whichever lamps reach it:

```python
assign(g, pbr("StudioFloor", base=(0.19, 0.195, 0.205), rough=0.45,
              emission=(0.19, 0.195, 0.205), emission_strength=0.6))
```

It is deferred rather than applied because it is worth about one presentation
point per model, and changing global staging invalidates every render already
scored. Do it in the same pass as the materials change, not on its own.


## Auto-exposure cancels the rig's absolute brightness

This is counter-intuitive and it cost two wrong fixes, so it is worth stating
plainly:

**The grey ball sits inside the same environment as the subject.** So raising
the world's brightness raises the ball too, auto-exposure pulls back equivalent
EV, and the render comes out unchanged — it only gets *flatter*, because the
extra energy arrives as ambient rather than as shaping light.

Measured on the coffee mug:

| change | ball reads at EV 0 | exposure applied | result |
|---|---|---|---|
| baseline world | 0.25 | −0.48 EV | — |
| world bright end 0.85→1.00, strength 0.55→0.95 | 1.34 | −1.57 EV | **no visible change** |
| exposure_target 0.45 → 0.85 | 2.01 | −1.01 EV | p50 0.33→0.42, p90 0.55→0.66, 0% clipped |

The ball reading 1.34 means the probe was **clipped** — another reminder that a
calibration reading must be taken underexposed.

**Consequences:**

- **Do not chase "everything renders dark" by adding light.** It cannot work.
- The only lever that survives auto-exposure is `exposure_target`.
- A *ratio* change does survive: light ratios, and contrast between the bright
  and dark ends of the environment, still shape the image. Absolute level does
  not.
- If a metal still reads black, the fix is its **material** (lower metalness,
  lower roughness, lighter base), not the rig.


## Scale awareness

A catalog spanning 0.2 mm contacts to 40 m bridges cannot be lit by fixed
numbers. `bkit.studio(radius_m)` sizes the lights from the subject's bounding
radius and scales **power with r²**, so irradiance at the subject is constant
across every scale in the catalog.

## Before you call a render underexposed, convert

A builder agent reported all 18 of its renders were "0.5 EV underexposed", having
measured a median near 33/255. That was a measurement error, not a harness bug:

- `image.pixels` returns **linear** values
- a PNG on disk is **sRGB-encoded**

Measured properly, a lit white-plastic face reads linear 0.281 = **sRGB 145/255**,
against linear 0.18 = sRGB 118/255. The render was correctly exposed.

```python
lin_to_srgb(c) = c * 12.92                     if c <= 0.0031308
               = 1.055 * c ** (1/2.4) - 0.055  otherwise
```

Comparing an sRGB byte value against the linear 0.18 target makes every correct
render look a stop and a half dark, and the obvious "fix" is to inflate model
albedos -- which ruins the materials on the next pass.


## The key/fill ratio is the whole look

An early rig had fill at 0.5 of key. Every object rendered as a flat white
cutout with no readable form. The key is now roughly 4x the fill, which is what
produces a visible shadow side. If a render looks flat, look here first.

## Exposure is measured, not guessed

`bkit.auto_exposure()` renders an **18% grey calibration ball** alone against a
transparent film, samples it, and solves `exposure = log2(target / measured)`.

Three details make it work:

- **Ball, not subject.** Exposing on the subject forces a black rubber tyre to
  render mid-grey, destroying the albedo the model exists to communicate.
  Exposing on a known grey card fixes the *lighting* instead.
- **Probed underexposed.** It tries −9, −5 and 0 EV and takes the first reading
  inside the linear range. A ball that reads exactly 1.0000 has clipped and
  tells you nothing.
- **Placed at the camera's aim point.** Anywhere else it falls outside the
  framed view and the probe comes back empty — which is reported as
  "unreadable", never silently applied.

Light constants are calibrated so the ball reads ≈0.18 at exposure 0, leaving
auto-exposure only a small correction.

## Metals need an environment

`metallic = 1.0` has **no diffuse term at all**. Against a near-black world,
steel and chrome render as black holes regardless of how much light you add. The
world gradient therefore runs from near-black to a bright top: that bright end
is the bounce card a product photographer would place opposite the key, and it
is the entire reason metal reads as metal.

## Camera

- Spherical orbit (`azimuth`, `elevation` in degrees) rather than hand-rolled
  Euler. It cannot gimbal at the poles and stays readable while iterating.
- `frame()` dollies the camera back until the subject fits, fitting **each
  projected axis against its own field of view** and taking whichever demands
  more distance.
- Six standard angles: `hero`, `three_quarter`, `side`, `top`, `rear`, `front`.
  The set is chosen to expose silhouette, symmetry, proportion and top detail —
  the four ways a model is usually wrong.

### Fit each axis against its own FOV

The obvious implementation — measure one extent, fit it against the narrower
field — is wrong, and wrong in a way that only shows up on wide subjects.

`projected_extent()` returns `(half_r, half_u)`: how far the subject reaches
along the camera's own right and up axes. Collapsing those to a single scalar
throws away *which* axis was wide. Landscape output makes the vertical FOV the
narrower one, so a wide subject then gets fitted **sideways into the vertical
field** and is pushed away until it fits — a 60 m airliner's front view filled
about 15% of frame while an apron filled 90%, from the same code.

```python
need = max(half_r * margin / math.tan(half_h),      # wide subject, wide field
           half_u * margin / math.tan(half_v))      # tall subject, tall field
```

`projected_radius()` still exists for callers that genuinely only need a "how
big is this" number (light sizing, clip planes). Camera fitting must not use it:
it cannot tell the two axes apart, and that difference is the whole bug.

Both directions are pinned by regression tests — a wide subject fills the
*width* it is wide in, a tall subject fills the *height* it is tall in — because
a fix that only handles one of them reads as a fix.

A related detail: the near plane must scale with the shot. Blender's default is
0.1 m, so a 19 mm subject framed closer than that sits entirely inside it and
every shot renders empty.

## The backdrop trap

The studio floor is an opaque plane at `z = 0`. Any model authored hanging
below the origin is **buried**: it still reports a perfect bounding box and a
clean mesh while the camera sees only what pokes above the floor. `run_model`
calls `bkit.sit_on_floor()` before measuring or rendering, and the harness
recomputes the bbox after moving objects — `matrix_world` is cached, so without
that refresh the camera aims at the stale centre.
