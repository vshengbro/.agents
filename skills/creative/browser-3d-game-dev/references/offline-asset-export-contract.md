# Offline asset export contract

The interchange format between a DCC tool (Blender/bpy) and a runtime renderer. Use
when a game generates its own models rather than importing them.

## Why this is an interface, not a file format

The exporter and the renderer are written at different times, often by different people
or agents, often in parallel. The schema is the only thing they share. Anything the
renderer has to guess is a bug waiting for its turn: the renderer guesses wrong, the
symptom appears at runtime in a form that looks like a rendering bug rather than a
format mismatch, and the investigation starts in the wrong file.

Concretely: if the schema doesn't say the file is Y-up, the renderer will treat Z-up
geometry as Y-up and the world renders lying on its side — which reads as a camera
problem, so it gets debugged in the camera for a long time before anyone checks the
axes.

## Minimum schema

```json
{
  "id": "car_sedan",
  "category": "vehicle",
  "units": "meters",
  "y_up": true,
  "bounds": { "min": [x,y,z], "max": [x,y,z] },
  "parts": [
    {
      "name": "body",
      "base_color": [r,g,b],
      "emissive": [r,g,b],
      "positions": [[x,y,z], ...],
      "normals":   [[x,y,z], ...],
      "faces":     [[i0,i1,i2], ...],
      "face_colors": [[r,g,b], ...],
      "flat": true
    }
  ]
}
```

Conventions that must be written into `SCHEMA.md` next to the files:

| Field | Contract | Why it is load-bearing |
|---|---|---|
| `positions` | meters, shared per part | vertex count drives the GPU budget |
| `faces` | triangles, CCW seen from **outside** | inverted winding = invisible under back-face culling |
| `face_colors` | parallel to `faces`, 0..1 floats | lets one part carry windows/tires/lights without extra draw calls |
| `emissive` | separate channel from base color | glow without special-casing named parts |
| `y_up` | explicit flag | the single most common silent mismatch |
| origin | buildings/vehicles at ground center, characters at foot center | "at world zero" forces a compensating offset on every instance forever |
| forward | one fixed axis, stated | a per-asset forward axis is a per-asset sign bug in the renderer |

`flat: true` means per-face normals (low-poly look); `false` means the stored normals are
smooth-interpolated. The renderer branches on this to decide whether to average vertex
normals per triangle.

## manifest.json

```json
{ "version": 1, "generator": "tools/build_assets.py",
  "assets": [ {"id": "...", "category": "...", "file": "..."} ] }
```

The renderer enumerates this list instead of globbing the directory at startup. Globbing
means a half-written file appears in the game, and the failure is at load time with no
attribution to which build produced it.

## Export-time assertions

Run these over the emitted JSON, not over the model. A model can look correct in the
viewport and export garbage.

1. **Index range** — every vertex index < `len(positions)`.
2. **Winding** — for each triangle, compute the normal from its own edges
   `cross(v1-v0, v2-v0)` and compare against the stored vertex normal. A systematic
   mismatch means inverted winding; a per-face mismatch means one bad part.
3. **Bounds** — declared `bounds` must equal the actual min/max over all parts'
   `positions`. Off-by-a-epsilon here is how a renderer ends up culling the world.
4. **Budget** — report total triangles. A budget enforced by feel drifts upward until
   the frame rate dies, and nobody notices because each individual model is tiny.

## Export assertions and preview renders are different tests

They fail differently and neither substitutes for the other:

- The **render** proves the model is visible and the camera is outside the mesh. A model
  with perfectly inverted winding still renders fine in a preview.
- The **assertions** prove the data is well-formed. A file with in-range indices and
  correct bounds can still be rendered from inside the camera.

Collapsing them into "it rendered, so it's fine" is how inverted-winding assets reach a
renderer and blank out under back-face culling.

For the render side, verify the output is not a flat image — compute per-pixel mean and
stddev on a downscaled copy. `std ≈ 0` means the camera is inside geometry or the frame
is empty background, which is a framing bug, not a lighting or material problem.

## Parallel producer/consumer

When the exporter and the renderer are built as two concurrent workers, the schema text
above goes **verbatim into both briefs** — units, axis, winding, origin, color range.
A worker that improvises the format produces a file the other cannot parse.

Tell the consumer to degrade gracefully while the producer is still running: fall back
to a built-in primitive and keep building. Without that instruction the two workers
serialize on each other unnecessarily, or one reports a blocking failure for a file the
other was about to write.

## Legal scope

Generating original geometry for a game that takes *inspiration* from a commercial title
is a style homage, not a reproduction. Keep every asset procedurally authored; never
import or trace a shipped game's models, textures, logos, or fonts. Also rename: a
genre-faithful original still shouldn't ship the commercial title's name. Say this in
the producer brief explicitly — "recreate it" and "make an original in this style" are
different instructions and only one of them is safe to hand a worker verbatim.
