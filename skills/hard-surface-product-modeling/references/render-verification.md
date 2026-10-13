# Render-based verification

Numeric audits confirm the envelope. Renders confirm the model. Always both.

## Studio setup

- `view_transform = 'Standard'` with an explicit negative `exposure`. Filmic/AgX
  names and defaults shift between Blender versions; Standard plus a number you
  tuned is reproducible.
- **Area-light watts are meaningless without size and distance.** A 0.30 m
  softbox at 14 W a hand-span from a 197 mm object blows it to pure white. Start
  around `size=0.30, energy=38` for a subject ~0.6 m away, then correct from the
  measurement, not from feel.
- Four lights for a polished metal body: key, fill, rim, and a thin top strip for
  the top-edge highlight. A raking light across the top is what makes a shallow
  relief or an etched mark read at all.
- Dark backdrop + dark world. A bright world makes polished aluminium read as
  white paper.
- **Light must be on the same side as the camera.** A key light behind or inside
  the subject renders it black — this is a closeup-specific trap, because the
  wide product shots looked fine while every detail crop came out unlit.

## Fit the camera, never hardcode distance

```python
def fit_camera(cam, target, radius, margin=1.28):
    aspect = res_x / res_y
    sensor = cam.data.sensor_width / 1000.0
    f = cam.data.lens / 1000.0
    hfov = 2.0 * math.atan(sensor / (2.0 * f))
    vfov = 2.0 * math.atan((sensor / aspect) / (2.0 * f))
    need = radius * margin / math.tan(min(hfov, vfov) / 2.0)
    if (cam.location - target).length < need:
        cam.location = target + (cam.location - target).normalized() * need
    cam.rotation_euler = (target - cam.location).normalized() \
        .to_track_quat('-Z', 'Y').to_euler()
```

Use **both** FOVs. Checking only the horizontal one clips the subject on tall
framings; the bound must be the tighter of the two.

## Compute the camera basis before trusting a left/right reading

A vision answer about which side a feature is on is a claim about the camera,
not about the model. Derive the basis and check the claim against it before
acting on it:

```python
# camera at -Y looking toward +Y, up +Z
import mathutils
forward = mathutils.Vector((0,  1, 0))
up      = mathutils.Vector((0, 0, 1))
right   = forward.cross(up)          # right-handed: screen-right of the view
```

For a front view this makes **model +X render on the screen LEFT**. A model
whose front-panel ports sit at `x = +7.40` is therefore on the *left* of the
photo, and a vision call saying "the ports are on the right" is wrong about the
image, not about the model.

**Do not re-derive this by hand, twice.** In this session the same basis was
computed with the cross product in one order and the other within a few
minutes, giving two opposite answers. Compute it once per session, write the
number down, and reuse it.

**A low-resolution oblique view is not evidence of side.** A 4-degree-elevated
thumbnail is small enough that a whole port row reads as one dark smear, and
"they're all in the corner" is what you get. Re-render the face flat-on at
elevation 0 before asking a sidedness question. Apple's own product shots are
near-orthographic at eye level — match that for comparisons, because a steep
elevation foreshortens the panel and hides exactly the features under review.

## Face flatness: measure it, don't look at it

"Does anything protrude in the middle" is answerable numerically. Sweep rays
across each face and report the hit distance:

```python
dev = []
for i in range(25):
    t = -9.0 + 18.0 * i / 24
    for z in (1.0, 2.55, 4.0, 5.5, 7.0, 8.5):
        o = Vector((t, -30, z)); d = Vector((0, 1, 0))
        hit, loc, nrm, idx, ob, mtx = scene.ray_cast(dg, o, d)
        if hit: dev.append(((loc - o).length, ob.name, t, z))
med = sorted(d for d, _, _, _ in dev)[len(dev) // 2]
odd = [x for x in dev if abs(x[0] - med) > 0.06]
```

Group `odd` by hit object and by height: what comes back is a list of
*intentional* features (a port bay, a grille edge, a connector tongue), not a
protrusion. Six flat faces of a box report 0 deviations on the top and one or
two elsewhere, and that is how you can say "nothing protrudes" as a measurement
rather than a claim. A silhouette bump in a render is usually a **top-face
specular highlight**, not geometry.

## Two kinds of verification render

**Silhouette / dimensions** — orthographic camera, `film_transparent = True`,
`color_mode = 'RGBA'`, then threshold alpha:

```python
a = np.asarray(Image.open(path).convert("RGBA"))
m = a[..., 3] > 128          # pixel-exact, independent of lighting and material
```

Thresholding a **shading** render on a flat grey material is unreliable and will
misreport the bounding box entirely. Alpha is exact.

**Detail** — tight orthographic closeups (`ortho_scale` 30-75 mm) for ports,
perforations and marks, with the key light on the camera side.

## Read a render numerically when vision is unavailable or contradicts geometry

The vision endpoint is not a reliable narrator, and this session it was wrong
twice — once about which side a port was on, once about whether a perforated
field existed at all, in both cases contradicting a ray probe. When the two
disagree, **the ray probe wins and the render question is re-asked with better
framing**; do not re-cut geometry to satisfy a misread thumbnail.

Perforation and recess presence can be settled by a **vertical statistics
profile** — mean and standard deviation of luminance in horizontal bands down
the face:

```python
for band in range(6, 17):
    row = a[band * H // 18:(band + 1) * H // 18]
    print(f"band {band:2d}  mean {row.mean():6.1f}  std {row.std():5.1f}")
```

A perforated region has high spatial variance (bright metal alternating with
dark holes); a flat metal band has low variance; a recess is uniformly dark.
Three distinct regimes in the profile is a positive detection of a three-zone
layout, and it is more persuasive than a vision verdict that says "I don't see
the holes."

## Numeric exposure triage

Before looking at any render, check it:

```python
a = np.asarray(Image.open(p).convert("RGB")).astype(float)
print(a.mean(), (a >= 252).all(axis=2).mean() * 100, np.percentile(a, 99))
```

- mean ≈ 255 with ~100 % clipped = the model is missing or the scene is blown.
- mean 120-190 with <20 % clipped = usable.
- A closeup that is 100 % clipped and another that is fine usually means the
  light was moved, not the exposure.

## Readback loop

1. Render.
2. Downscale to ≤640 px (`sips -Z 640 in.png --out out.png`) — large images
   time out the vision endpoint.
3. Ask a **specific** question: *"Reading left to right as a viewer, what
   openings appear and in what order?"* beats *"does this look right?"*, which
   returns vague praise.
4. Compare against the reference photo and fix.

Two practical notes: multi-panel contact sheets and extreme aspect-ratio crops
time out far more often than single square images — compare pairs individually
instead. And when the vision endpoint returns timeouts, that is transient; fall
back to the numeric checks and retry rather than rewriting the pipeline around
it.

## What vision catches that numbers cannot

- mirrored feature order
- relief too shallow to register
- a face blown out or a subject clipped
- "pillowy" corner radii — correct dimensions, wrong feel
- decal-flat port cavities
