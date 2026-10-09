# Construction recipes

All dimensions are millimetres. Every closed recipe produces watertight output;
call `recalc()` if normals are wrong and `weld()` if a sweep reaches its axis.

## The core primitives

| Call | Use for |
|---|---|
| `box(name, sx, sy, sz)` | axis-aligned block |
| `rounded_box(name, …, r=, segments=)` | anything with soft edges — **almost always better than `box`** |
| `cylinder(name, r, h, r2=None)` | cylinder, cone, disc, pillar |
| `tube(name, r_out, r_in, h)` | pipe, washer, ring — with real wall thickness |
| `sphere(name, r)` / `uv_sphere` | ball, knob, dome (aliases of the same function) |
| `torus(name, R, r)` | full ring; note `bmesh.ops.create_torus` does not exist |
| `arc_torus(name, R, r, a0, a1, plane=, centre=, caps=)` | handles, hooks, arches, brackets |
| `lathe(name, profile)` | any circular silhouette: vessels, bottles, wheels, shades |
| `loft(name, sections)` | anything whose cross-section changes along its length |
| `extrude_profile(name, poly, h)` | a flat plate cut from a 2D outline |
| `gear(name, teeth, module, thickness, bore)` | spur gear |
| `thread(name, r, pitch, length)` | bolts, screws, threaded rods |
| `perforated_panel(name, cols, rows, …)` | grilles and speaker mesh, in one mesh, no booleans |

## Three ways a boolean quietly produces a non-manifold mesh

All three cost wave 2 real debugging time. Check the mesh after **every** cut.

**1. Coincident facets.** A cutter coaxial with a host surface that uses the
*same* segment count puts vertices exactly on top of each other. The EXACT
solver returns 7 bad edges where intuition says zero. Use `bkit.bore()`, which
deliberately picks `host_segments + 7`:

```python
bkit.bore(disc, r=16, depth=40, host_segments=64)   # clean
bkit.cylinder("_c", 16, 40, segments=64)             # dirty if the host is 64
```

**2. Tangency.** A part that ends *exactly* flush with a surface — a boss the
same width as the wall it meets, a counterbore exactly as wide as a rail's foot
— produces 3–10 bad edges because the two surfaces touch along an edge instead
of crossing. **Overlap by at least 1 mm.**

**3. Coincident volumes.** Two solids whose outer surfaces coincide (a hub
unioned onto a cylinder of the same radius) defeat the solver. Bore first, then
union the hub with a small clearance.

## Radial arrays

`bkit.array_radial(obj, count=6)` sweeps the object around the Z axis in equal
steps. Place `obj` at the radius you want first — the sweep centres on the
real axis. The offset empty carries the angular step, which is what makes
Blender's object offset a rotation instead of a translation.


## Two traps that cost real debugging time

**`obj.location` is metres.** Every number in a model script is millimetres;
Blender's own object transform is not. `obj.location = (5, 0, 8)` puts a part at
5000 mm and silently inflates the scene bounding box by three orders of
magnitude -- the model still "builds", and the render is wrong. Use
`bkit.move(obj, dx_mm, dy_mm, dz_mm)`, which also refreshes the cached
`matrix_world` so the next `bbox()`/`measure()` call sees the new position.

**`matrix_world` is cached.** After moving anything, call
`bpy.context.view_layer.update()`. `bkit.move()` and `bkit.sit_on_floor()` do it
for you. Skipping it makes a move look like it did nothing, and makes the camera
aim at the model's old centre.

## Sections and lofts

`rounded_rect_section` and `superellipse_section` return **2D** rings.
`loft()` accepts either 2D or 3D points, so a hand-written ring and an explicit
3D section both compose with it:

```python
bkit.loft("Body", [[(x, y, z) for (x, y) in ring] for z in heights])
bkit.loft("Body", [[(x, y, 0.0) for (x, y, _z) in ring] for ring in rings])
```

Do not "tidy" the helpers into returning 3D without checking what already
unpacks them: it is a breaking change to every shipped model that does.


## Sections for lofts

- `rounded_rect_section(sx, sy, r, per_corner=)` — the default. Boxes with
  rounded corners, so a lofted body does not show a hard vertical edge.
- `superellipse_section(sx, sy, n=, steps=)` — `n=2` ellipse, `n≈3` car-like,
  `n≈4` squircle, `n>8` nearly rectangular. One function covers a whole family.

## Measured layout — the anti-hand-placing rule

Repeated features are computed from real feature widths plus an explicit gap:

```python
for (x, w) in bkit.lay_out([9, 9, 26, 12, 14], gap=6):
    cut = bkit.cylinder("port", 5, depth, centre=(x, 0, 0), axis="Y")
    bkit.boolean(body, cut)
```

```python
for (x, y) in bkit.grid_positions(cols=8, rows=6, pitch_x=14, pitch_y=14):
    ...
```

Two hand-placed features that land on the same coordinate produce coincident
boolean faces, and the EXACT solver answers that by deleting the entire body —
with no error message. This failure cost a whole chassis once.

## Working with the result

```python
bkit.bevel(obj, width_mm=0.9, segments=2)   # edge break, reads as manufactured
bkit.mirror(obj, "X")                       # symmetry
bkit.array_linear(obj, count=5, offset_mm=(12, 0, 0))
bkit.join([head, shank, thread], name="Bolt")
bkit.assign_faces_by(body, glaze, lambda c, n: c.z < 40)   # second material
```

`assign_faces_by` is the right way to give one solid two surfaces. The obvious
alternative — a second object shaped like the inside — z-fights with the wall
and leaves both objects non-manifold.

## Extending bkit

New recipes go **in `bkit.py`**, not in the model script, so all 716 items can
use them. A new recipe must:

- take and return millimetres,
- call `recalc()` if it builds a closed solid,
- call `weld()` if it reaches an axis or seam,
- have a case in `scripts/test_primitives.py` asserting it is watertight.

Then re-run the regression test before using it on the catalog.
