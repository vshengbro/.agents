# From a fixed map to an infinite, streaming world

Two claims get confused constantly, and conflating them is how a "done" world
ships that stops at the old boundary.

| Claim | What it actually means |
|---|---|
| "The map is infinite" | Coordinates beyond the old bound *resolve* — `roadway_at(50000, 50000)` returns a real answer |
| "The world streams" | There is a **load/unload lifecycle** per chunk for geometry, props and collision, driven by a moving centre |

The first is a refactor of coordinate math. The second is a new subsystem. A
world can have the first and none of the second, and it looks complete in every
screenshot because the player never left the initial generation radius.

## Layer by layer

| Layer | Convert how | Needs lifecycle? |
|---|---|---|
| Coordinate predicates (on-road, on-lane, block lookup) | Closed form — never enumerate | No |
| Buildings, props, colliders | Enumerate indices in a view radius | **Yes** |
| Ground, water, sky dome | One mesh recentred on the player | No — recentre instead of chunking |

Ground and water are continuous, so they recentre; chunking them buys nothing.
Buildings and props are discrete and need a real load/unload pass. Colliders
need one too, and are the layer most often left behind: a collision world built
once at init silently bounds the player no matter how far generation reaches.

## Conversion recipe

1. **Find every hard-coded bound first.** A fixed street array, a `CITY_HALF`
   constant, a `for x in (-150..=150)` loop, a ground plane sized to the initial
   view. Replace the *array* with a formula (`axis(index) = PITCH * index`) and
   keep the pitch as the one source of truth.
2. **Rewrite every "is this point on a street" predicate in closed form.** The
   old version iterated the array and took the min distance. The infinite version
   computes the nearest index directly and rounds. If you keep the iteration
   anywhere, that code cannot scale past the initial array.
3. **Add an index enumerator** over a coordinate interval, and use it wherever
   geometry is placed. Everything downstream of "which street am I on" and
   "how far do I build" must come from the same enumerator.
4. **Parameterise the builders on a centre** `(cx, cz)`, and recentre ground and
   water on that centre.
5. **Rebuild on a threshold, not per frame.** A recentre step that fires every
   frame allocates and uploads a mesh 60 times a second for no visual change.
   Trigger on a distance the player cannot see the popping at.
6. **Relocate hand-placed content as block-relative.** A prop at an absolute
   coordinate chosen against the old grid will land on a roadway the moment the
   pitch changes. Express it as `(block index, offset within block)`.
7. **Make procedural generation avoid the hand-placed content.** New chunk
   generation will happily overlap it; add an explicit footprint test, and assert
   it in the streaming test.

## The three bug classes this refactor produces

All three were found by one test that asserts a mesh built around a far centre
stays near that centre. Write that test **before** the refactor lands — it is
the only thing standing between this refactor and a world that renders garbage
thousands of metres out while the origin looks perfect.

### 1. A loop-local binding shadows the centre parameter

```rust
// the base-face loop computes a cell centre with the SAME name as the parameter
for j in 0..N {
    let cx = (x0 + x1) * 0.5;        // shadows the function's `cx` parameter
    ...
}
// every later stage that reads `cx` now reads the LAST cell's centre
```

Zero errors, plausible geometry, and the whole mesh is displaced. **Rename the
parameter to something a loop will never reuse** (`centre_x` / `centre_z`) so the
next person cannot re-shadow it. The tell is a generator whose output is correct
at the origin and displaced everywhere else.

### 2. Two axes sharing one enumeration interval

```rust
for axis in 0..2 {
    for line in streets_in(centre, radius) {   // `centre` is the SAME for both axes
        let mut t = interval_lo;               // ...and so is this range
        while t < interval_hi { place(t, line) }
    }
}
```

The street *line* for the cross axis and the *extent* to build along the other
axis are two different questions, answered by two different centres. One
enumerator cannot answer both. Split them explicitly:

```rust
let cross = if axis == 0 { centre_x } else { centre_z };   // which streets
let (lo, hi) = along_span(if axis == 0 { centre_z } else { centre_x }, radius); // how far
```

Symptom: only one direction of kerb or lane marking ever appears, and the other
axis's geometry is missing or lands in the wrong place.

### 3. Deriving an interval from two unrelated centres

```rust
let lo = (x.min(y) - radius).floor();     // BUG when x and y are far apart
let hi = (x.max(y) + radius).ceil();
```

Reasonable when both arguments describe the same region; catastrophically wrong
when they are centres of *different* axes. At a centre of `(-6000, 1500)` this
produces a 7750 m wide interval and a mesh whose vertices are thousands of
metres from where they belong. The error is invisible at the origin and enormous
far from it, so only a far-centre test sees it.

## Hand-placed content

When the grid pitch changes, every absolute coordinate chosen against the old
grid is now wrong in a way that looks like a bug in generation. Re-express as
block-relative (`(block_index, offset)`) rather than a raw world coordinate, and
add a footprint exclusion so the procedural pass cannot build through it. Assert
the exclusion in the same far-centre test.

## Verification strategy

**The generator is proved by a unit test at far coordinates; the browser walk is
a bonus, not the proof.** A test that builds ground and water around
`(-6000, 1500)` and around `(3000, 3000)`, and asserts every vertex is within
half-a-block-plus-street-furniture of that centre, settles the question outright
and runs in milliseconds. Assert the **per-axis** extent, not the max radius —
a single max hides an axis that is off by thousands while the other is fine.

When the assertion fails, print more than the failing number:

```
centre=(-6000,1500) dx=7740 dz=7740 zmin=-6240 zmax=1749
derived_origin=(-6240,1260)  street_indices_z=[1020..1500]
```

That triple — per-axis extent, derived origin, and the actual enumerator output —
localises all three bug classes above in a single run. Reasoning about the
geometry by hand does not; I mis-derived it twice before instrumenting it.

Then, in the browser, assert the recentre actually fires and the player stays on
the surface: watch the streamed centre change, and assert height stays at ground
level for the whole run. A `y` that drifts means the player walked off the edge
of a mesh that was never extended — the failure mode where a recentring ground
misses a rebuild threshold.
