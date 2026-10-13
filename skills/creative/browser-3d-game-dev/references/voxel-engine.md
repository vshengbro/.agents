# Voxel Engine: Chunking, Meshing, Textures, Atmosphere

Implementation notes for a browser voxel world on Three.js. Covers the parts that
generalise beyond one project.

## Chunk storage

16×16 columns, world height ~48. Per chunk:

```js
class Chunk {
  blocks    = new Uint8Array(CHUNK * WORLD_H * CHUNK);  // id per voxel
  heightMap = new Uint8Array(CHUNK * CHUNK);            // topmost non-air y
  generated = false;  dirty = true;
}
```

- `Uint8Array` keeps 16×48×16 = 12,288 blocks at 12 KB per chunk; 177 loaded chunks
  ≈ 2 MB. Fine.
- Keep `heightMap` updated on every `set` — it makes spawn placement and entity
  ground-finding O(1) instead of a column scan.
- Address voxels with `x + z*CHUNK + y*CHUNK*CHUNK` (y-major) so a vertical column is
  a contiguous stride and a horizontal slab is not.
- Tag coordinates with `x >> 4` / `x & 15`; works for negatives via two's complement.

Return `AIR` for ungenerated chunks rather than throwing — it makes mesher boundary
code total, and get a real result once the chunk streams in.

## Terrain generation

Layer fBm by feature rather than one big noise call, so each biome characteristic is
independently tunable:

```
continent  = fbm(x/220, z/220)              // ocean vs land
hill       = fbm(x/42,  z/42)               // local relief
mountain   = pow(max(0, fbm(x/130, z/130) - 0.52) / 0.48, 1.6)   // ridge mask
height     = SEA + 1 + (continent-.5)*26 + (hill-.5)*9 + mountain*22
```

**Set the thresholds from the noise's measured distribution, not by intuition.** Value
noise fBm concentrates around 0.5, so a remap centred there (`smoothstep(.30,.72,n)`)
splits the world almost exactly in half — which for a continent mask means ~50% ocean,
and for a mountain mask means it is zero nearly everywhere. Lower the remap window
(e.g. `smoothstep(.22,.60,n)`) until the layer histogram shows the split you intended,
and re-check the biome counts afterwards. Both failures present identically as
"the map generator is bad".

**Fold the mountain octaves (ridged noise) rather than summing them.** Summing plain
fBm gives rounded hills; `n = 1 - abs(2n-1)`, squared, and multiplied by the previous
octave's result gives sharp ridges that only appear where the low frequency already has
mass. This is the difference between "hills" and "mountains".

**Aim for real relief, not a bigger max.** A single 32-block peak on an otherwise flat
plain is not interesting terrain. Target the spread between p25 and p75 and the fraction
of local samples that are flat — measure both, they are the numbers that improve.

Deterministic hash noise (integer hash → float in [0,1)) is preferable to `Math.random()`
for worldgen: the same seed must reproduce the same world, and cross-chunk decoration
(trees) must not depend on generation order. A tree straddling a chunk border is decided
by a hash of its *world* coordinates, so it appears the same regardless of which chunk
generated it first.

Caves: 3D value noise thresholded, with two decorrelated noise fields ANDed so tunnels
are spaghetti-like rather than blobby.

Ores: depth-gated hash thresholds — deeper = rarer and more valuable. Order the
conditions cheapest/most-likely first so the common case (stone) short-circuits.

Sea level fill: after the column loop, fill air up to `SEA` where terrain is below it.

## Trees and decoration

Place decoration inside the column loop but keyed on world coords. A tree at a chunk
border must have its canopy clipped to the chunk (`if (ax<0||ax>=CHUNK) continue`) — the
neighbouring chunk will grow the other half from its own deterministic hash, producing
a symmetric tree instead of a clipped one.

Classic canopy: 4–6 trunk, then a 2-wide ring for two layers, then 1-wide, with random
corner removal so the silhouette is not a cube.

## Meshing

**Per-face culling beats greedy meshing for a first build.** Greedy merging requires
neighbour-aware run detection along all three axes and breaks transparency ordering;
per-face culling is straightforward and correct. 177 chunks × ~16k triangles renders
at 60 FPS.

Cull rule:
- opaque block + any solid neighbour → skip face
- transparent block + same-type neighbour → skip
- transparent block + different-type or air → draw

For each visible face emit 4 vertices + 6 indices. Push per-vertex colour = face
brightness × AO so a single material can carry both face shading and occlusion.

**Chunk seams need neighbour data.** When meshing chunk (cx,cz), read out-of-range
x/z through the world accessor, not through the local array — otherwise boundary faces
are culled against phantom air and you get visible walls at every chunk edge.

### Per-vertex ambient occlusion

Standard 3-neighbour sampling per vertex: two edge neighbours and one corner. Both edges
solid → fully occluded; otherwise `ao = 3 - (side1 + side2 + corner)`, normalized to
[0,1] and multiplied into the vertex colour.

Precompute the sample offsets per face per corner once — deriving them from the corner
positions at runtime is error-prone and slow. Build an offset table at module load:

```js
// per face, the two axes perpendicular to the normal
const axes = [0,1,2].filter(i => dir[i] === 0);
const [a1, a2] = axes;
// per corner, signs along those two axes give the three sample offsets
```

This is what makes block corners read as rounded rather than flat.

## Texture atlas

Pack every block face into one image, one material, one draw call.

- 16×16 px per tile in an 8-column grid
- Half-pixel inset each UV rect to stop mipmapping bleeding between neighbours
- `magFilter = NearestFilter` (crisp pixels), `minFilter = NearestMipmapNearestFilter`
- `colorSpace = SRGBColorSpace`
- Flip V when building UVs — canvas Y is down, GL texture V is up

**Generate textures procedurally on a `<canvas>`** rather than shipping images: no asset
files to deploy, deterministic, and one noise function covers every block. Keep an
inset border darker on side textures (reads as a bevel) and vary top/side/bottom
separately so grass, log and ore all look right from any angle.

**An animated material must not share the atlas.** A water material that reuses the
atlas texture and scrolls `map.offset` scrolls every block skin in the game, because the
atlas is one image holding grass, stone, dirt and everything else. Give each animated
material its own `CanvasTexture` over the same canvas with `RepeatWrapping`, and remap
that surface's UVs to 0..1 in the mesher so the other faces keep their atlas rects.
Assert it numerically: the atlas offset must stay 0 across time.

The general hazard applies to every engine object: `map`, `material`, `geometry`,
`uniform` and shared `Group`s are all aliasing points. Before animating a property,
ask what else holds a reference to it.

## Raycasting (DDA voxel traversal)

For block targeting, walk the grid:

```js
step = sign(dir); tDelta = abs(1/dir); tMax = distance to first cell boundary per axis;
// each iteration: advance whichever axis has the smallest tMax, and record
// which axis stepped so you know the face normal (for placement offset)
```

Initialize `tMax` per axis from the origin's position *within* its cell, not from zero.
Set the face normal to the negated step direction, so the placement cell is always the
one the player is looking at, not the one behind it.

Guard against division by zero on axes where `dir` is 0 (`tDelta = Infinity`).

## Atmosphere

Derive every sky consumer from ONE shared phase scalar per frame:

```js
const phase = ((t / DAY_LEN) + START_OFFSET) % 1;
const ang = phase * Math.PI * 2;
const elev = Math.sin(ang);                    // 0=midnight, PI=??? -> define once
const daylight = clamp((elev + 0.22) / 0.5, 0, 1);
```

Then sun position, sun/moon sprite placement, star opacity, fog colour and fog distance
all read `ang`/`elev`/`daylight`. A consumer that re-derives the sign differently will
drift from the rest (sun below the horizon at noon is the classic).

Useful cues:
- `warm = max(0, 1 - abs(elev)*2.2)` peaks at sunrise/sunset → tint sun orange then
- fog `near`/`far` tighten at night for mood without changing geometry
- start the cycle offset so the first load is midday, not midnight

### Clouds

Sprites with a procedurally drawn soft blob texture (sum a few gaussians into the alpha
channel). Scatter on a coarse grid around the player, re-anchoring the grid origin to the
player's cell, so clouds exist everywhere without ever storing them. Drift with a slow
per-frame offset and wrap around the player. `depthWrite: false` + `fog: false` keeps
them from z-fighting and from fading into the horizon.

### Shadows

Directional light shadows need the shadow camera to follow the player or the shadow
frustum sits in world space and the player walks out of it:

```js
sun.position.set(cam.x + dx, cam.y + elev*120, cam.z - 50);
sun.target.position.set(cam.x, cam.y, cam.z);
sun.target.updateMatrixWorld();
sun.shadow.camera.left = -80; right = 80; top = 80; bottom = -80;
```

`normalBias` (~0.03) kills shadow acne on blocky geometry more effectively than raw
`bias` does. 2048 map + PCFSoft is affordable alongside per-vertex AO at 60 FPS.

### Entities

Blocky bodies from a few `BoxGeometry` meshes parented to a `Group`, with a tiny
behaviour update: wander timer, gravity, axis-separated collision, leg swing driven by
a walk flag. Spawn on a valid surface within a radius of the player, cap the population,
and despawn beyond a larger radius. Update only entities inside the streaming radius.

Despawning must dispose geometry and materials — a long session otherwise leaks.

Ground snapping has exactly one correct form:

```js
const footBlockY = Math.floor(this.pos.y - 0.02);     // PRE-move position
if (solid(this.pos.x, footBlockY, this.pos.z)) {      // exactly one cell, no scan
  ny = footBlockY + 1; this.vel.y = 0; this.onGround = true;
} else { this.onGround = false; }
```

Two tempting alternatives both read as "the entity bounces forever":
- `Math.floor(ny) + 1` uses the post-move position, so the body is raised a block and
  falls again next frame — an infinite ratchet.
- Scanning downward for the first solid block looks like a fix but walks across a water
  column to the sea floor, teleporting the entity 13 blocks down. Check one cell only.

Entities that cannot swim must also be blocked from moving into a fluid cell
horizontally, and their spawn must reject water-adjacent tiles, or they wander into the
sea and the downward scan hides it. Drop `Math.random()` idle-jump — make the jump
fire only when the forward direction is blocked by a one-block step, so locomotion stays
readable as locomotion.
