# Voxel Worlds and AABB Character Physics

The four bug classes that made a working-looking voxel game unplayable. All
four passed code review and were caught only by reading state back from a live
browser. Each one produces a *plausible* screenshot, which is why they are so
easy to ship broken.

## 1. Collision predicates fail *open* by default

```js
// broken: definitions only ever set solid:false, so this is false for every block
isSolid: id => id !== AIR && !!def.solid
```

The player falls straight through the world and every block is invisible to
collision. The world still generates, chunks still mesh, the render loop still
reports 60 FPS — the screenshot shows terrain, so it reads as fine.

Either mark `solid: true` on every solid block definition, or invert the
default so an undeclared block is solid:

```js
isSolid(id) {
  if (id === AIR) return false;
  const d = BLOCKS[id];
  if (!d) return false;
  if (d.liquid) return false;
  return d.solid !== false;      // undeclared ⇒ solid
}
```

**Why it matters generally:** a predicate that returns falsy for unknown input
fails open — it permits motion through geometry. For any collision/visibility
predicate, decide deliberately which way unknown input goes, and prefer
*closed* (treat unknown as blocking) for collision.

**Assert it, don't assume:** `console.log(isSolid(GRASS))` must be `true`.
A one-line check that would have caught this before any 3D work.

## 2. Snap to the position you *computed*, not the one you started from

Axis-separated AABB resolution looks like this — and is wrong on the Y axis:

```js
const ny = p.y + dy;
if (!collides(p.x, ny, p.z)) p.y = ny;
else if (dy < 0) p.y = Math.floor(p.y) + 1 + EPS;   // ← uses OLD p.y
```

`Math.floor(p.y)` is the pre-move position, so every frame the player is
lifted by up to one block. Symptoms: the entity never rests, `onGround` stays
false, jumping and impact damage silently never fire — while the visuals are
perfect, because the entity hovers just above the floor instead of sinking.

```js
p.y = Math.floor(ny) + 1 + EPS;   // correct: the new position
```

**Rule:** in collision resolution, every derived coordinate comes from the
*new* position, never the old one. Grep the resolver for `Math.floor(this.pos`
or `Math.floor(p.pos` and confirm each one is operating on the just-computed
value.

## 3. State-order-of-operations: compute *after* the mutation that produces it

Damage/impact logic placed before the movement step reads the **previous**
frame's `onGround` and `pos.y`, so a landing is never detected and the effect
never applies:

```js
// wrong: this.onGround is still last frame's value here
if (this.onGround && this.fallStart !== null) { ...apply damage... }
this.moveAxis(...);            // ← sets onGround / corrects pos.y
```

Move the whole block after the mutation, and capture the pre-move value
explicitly when the post-move value is what you need to *compare against*:

```js
const prevY = this.pos.y, wasOnGround = this.onGround;
this.onGround = false;
this.moveAxis(...);            // sets onGround, snaps pos.y
if (this.onGround && this.fallStart !== null) {
  const drop = this.fallStart - this.pos.y;   // needs both: start vs landing
  ...
}
```

**Rule:** any logic keyed on a flag that the same tick mutates must run after
that mutation. If it also needs the pre-mutation value, capture it before.

**Test the negative case too:** a physics fix that reports "impact damage now
works" is unproven until a 2-block drop *and* a normal jump both still report
zero damage. Only checking the positive case lets a fix that damages on every
step pass.

## 4. Spawn validation must read the world, not the height function

Selecting a spawn by sampling a terrain-height function puts the player inside
caves (the height function doesn't know caves were carved out), above water,
or inside a tree. Generate first, then validate against **real blocks**:

```js
// broken: called before any chunk exists, so every lookup returns void
spawnPlayer();                       // ← always hits the fallback
for (...) generate(preloadChunks);   // too late
```

```js
// right: generate the area, then require solid ground + clear headroom
for (...) this.world.generate(...);
spawnPlayer();   // validates via world.getBlock, not heightAtTerrain
```

```js
const isFree = (x,y,z) => { for (let d=0; d<4; d++) if (isSolid(w.getBlock(x,y+d,z))) return false; return true; };
if (!w.getChunk(x>>4, z>>4)) continue;          // must be generated
if (!isSolid(w.getBlock(x, h, z))) continue;   // ground exists
if (!isFree(x, h+1, z)) continue;              // 4 blocks of headroom
```

**Assert it:** after spawn settles, log `onGround` **and** the block directly
beneath the player's feet — a spawn that reports `onGround: true` while the
supporting block is `0` (air) is standing on nothing.

## Debugging order that worked

Trace the frame, don't reason about the class. Dumping per-frame state through
`Runtime.evaluate` while stepping a physics tick locates each of these in one
pass:

```
52 y=29.00 vy=0.00 og=true fs=40 hp=20   ← landed, but fallStart never cleared
```

That single line showed the value was captured in the wrong order (bug 3);
`og` flipping with `fs` stuck proved the reset branch was unreachable. Asserting
on a *pair* of related values is what makes the frame legible — a single
number ("no damage") points at a dozen causes.
