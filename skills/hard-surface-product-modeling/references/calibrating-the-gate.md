# Calibrating the gate before believing it

A verification script that has never been run against a case whose answer is
known cannot distinguish "the model is right" from "my measurement is right
by accident". On a perforated panel this is not a theoretical worry: three
different gates each returned a confident, plausible, and wrong answer, and
two of them were reported to the user as passes.

## The three failures

**Ray depth tests cannot tell a bore from the bridge beside it.** A bore's lip
is coplanar with the skin around it, so a single `ray_cast` hit carries no
information about whether that hit is a hole wall or solid metal. Every variant
fails differently, and each one is plausible:

| test | reading on a SHUT panel | why |
|---|---|---|
| first hit deeper than the skin | 0 % | the skin's own triangles are tilted a few um by the boolean, so their centres read as deeper than the plane |
| first hit is not the shell | 100 % | a ray through a hole also crosses the panel's inner face, which is also the shell |
| any hit deeper than the wall | drifts with the sample | depends on where the sample lands relative to the bridge |

Measured spreads from these: 0.0 %, 0.1 %, 16.5 %, 23.1 %, 25.4 %, 31.1 %,
35.0 %, 38.2 % — for the same model, as the criterion was tuned. A number that
moves 30 points when you change the predicate is not measuring the thing.

**Area is meaningless for a field of small holes.** A 1.42 mm hole is 0.09 % of
a 16 cm² face, so a panel with exactly one good hole still reads 99.9 % intact.
Calibrated on a slab: 0 holes -> 1 loop, 1 hole -> 2 loops, and the surviving
skin is 15.985 of 16.000 cm². Any area-based "percent open" figure for a field
of thousands of sub-millimetre holes is dominated by the bridges and says
nothing about the holes.

**Boundary-loop counting has a ceiling that a small test will not reveal.** A
sheet with N holes has N+1 boundary loops, which is exact in principle. Measured
on a slab with a known lattice: 0 holes -> 1 loop, 1 -> 2, 25 -> 26 (exact),
625 -> 442 (expected 626). It is exact at 25 and silently wrong at 625. A test
that only ever exercises a handful of holes will pass forever.

## Calibrate on a mesh whose answer is known by construction

Do this before trusting the gate on the real model. It takes one minute and it
is the difference between a gate and a coin flip.

```python
# A 10x10 quad sheet with 3 squares removed has exactly 4 boundary loops.
HOLES = {(2,2), (5,5), (7,1)}
vmap, verts, faces = {}, [], []
def vid(i, j):
    if (i, j) in vmap: return vmap[(i, j)]
    vmap[(i, j)] = len(verts); verts.append((i, j, 0)); return vmap[(i, j)]
for j in range(10):
    for i in range(10):
        if (i, j) in HOLES: continue
        faces.append((vid(i,j), vid(i+1,j), vid(i+1,j+1), vid(i,j+1)))
```

**The vertices must be shared between cells.** Building each cell with its own
four corners gives 194 faces, 388 boundary edges and 97 loops for a mesh that
should have 4 — the algorithm looks broken because nothing is welded. Sharing
via a vertex map gives 97 faces, 52 boundary edges and exactly 4 loops. If your
loop counter reports roughly one loop per face, you are reading a mesh whose
neighbouring faces do not share vertices.

Then extend the same control to the density you actually have — 25 holes passes,
625 does not, so the control has to reach the real order of magnitude before
the gate is trusted.

## The test that has no threshold to tune

For a skin cut by holes, ask whether any triangle covers a hole centre. A
1.42 mm hole cannot contain a whole triangle, so if the skin is continuous there
will be a face centre within a fraction of the hole radius; if the hole is open
there will not be. Bucket the skin face centres into a 2-D grid and test each
lattice position against the cells it could fall in:

```python
CELL = 0.05
grid = defaultdict(list)
for p in skin_polys:
    grid[(int(p.center.x/CELL), int(p.center.z/CELL))].append(p)

def covered(px, pz, r):
    for i in range(int((px-r)/CELL), int((px+r)/CELL)+1):
        for j in range(int((pz-r)/CELL), int((pz+r)/CELL)+1):
            if any((x-px)**2 + (z-pz)**2 <= r*r for (x, z) in grid.get((i, j), ())):
                return True
    return False

blocked = sum(covered(x, z, r * 0.5) for (x, z) in hole_centres)
print(f"{blocked}/{len(hole_centres)} still covered -> "
      f"{100*blocked/len(hole_centres):.1f}% blocked")
```

`r * 0.5` is not a fitted threshold: a hole is open if a triangle overlaps even
its inner half, so the choice between `0.5r` and `0.9r` cannot flip a genuinely
open field. That property — the answer does not depend on the knob — is what
makes it worth having, and it is what none of the depth tests above had.

## The gate can be sound and still probe the wrong points

The threshold-free hole-centre probe above is the right idea, and it still
produced four consecutive wrong answers on one panel — two as "shut", two as
"open" — because the **coordinates were not the builder's**.

The builder lays its columns from `x0 = -(cols - 1) * pitch / 2`, not from the
origin, and offsets alternate rows by half a pitch for a stagger. A probe
firing at `k * pitch` from the origin therefore lands in the **bridges between
the holes**, and "is a skin face covering this point?" is a sound question whose
answer is always yes on a panel with 2,760 holes in it. Recomputing the
lattice from the builder's own expressions and probing all 2,760 centres read
100 % open on a model that had been open the entire time.

**Recompute the probe's sample points from the same expressions the builder
uses, in the same order, including the stagger and the edge clamp.** If the
builder has a `max_holes` cap or an inset that drops points, the probe must
reproduce the drop or it will sample points that were never cut.

**A "0 % blocked" result on a feature you can see is a probe bug until proven
otherwise.** Three of the four wrong readings came from probes that had never
been pointed at a real hole. Before changing geometry, verify the probe can
distinguish a panel that is known-open from one that is known-shut — the
slab control above is exactly that, and it takes a minute.

## A measurement needs a second, independent half

Every reading in this file measures *openness*. None of them measure whether
the **shell still exists**, so each one can be satisfied by a model that has
lost the panel entirely — the degenerate case that read "100 % open" on a body
whose Z extent was 3.7 mm short and whose skin had dropped 80 %.

Make the gate a **conjunction and report both halves in every run**:

```
1. ENVELOPE   X/Y/Z within tolerance, spans printed
2. OPENNESS   N/M hole centres covered -> percent open
3. VERDICT    PASS only when both hold
```

Give the verdicts distinct names so a mislabelled result cannot be quoted as a
pass: `PASS` (intact and open), `SHUT` (intact, every centre covered), `VOID`
(damaged envelope, centres uncovered — the holes read open only because the
panel is gone), `DAMAGED` (damaged and shut). **A gate that mislabels its own
result is worse than no gate, because the label is what gets quoted.**

The conjunction also reverses the order of the first two rounds of debugging:
a "100 % open" reading on a damaged shell and a "0 % open" reading on a healthy
shell look like opposite problems, but they are the same class — half of a
conjunction reported alone.

Two numbers in the same report are red flags when they contradict each other,
and one of them is always wrong:

- skin area covering **205 %** of the band is impossible. A tolerance wide
  enough to leave the plane has swept in the side panels' fillets, and every
  reading taken at that tolerance is void. Print the coverage, and **mark the
  row VOID rather than reporting it**, because a number that can silently walk
  out of its own domain is how a false pass gets through.
- a hole count near the design but an envelope that says otherwise means the
  count came from a selection that was not the surface you thought.

## A control that does not reproduce the bug has refuted the hypothesis

The obvious suspect for a shut panel was the cutter's front cap sitting exactly
coplanar with the skin. Testing `start = 0.0` against `start = -0.02` on a
slab: both cut cleanly, 2 boundary loops, 15.985 of 16.000 cm² of skin
surviving. **The control did not reproduce the failure**, so the coplanarity
was not established as the cause — yet the comment written in the source
already asserted "this is the whole bug".

When a control does not reproduce, the hypothesis is refuted and the next
measurement has to go somewhere else. Write the source comment as UNVERIFIED
and commit it as `wip:`, not as a fix. A plausible mechanism plus a real
number makes a claim that survives into the next session as fact.

## When the boolean is not the bug, test the boolean alone

Before debugging a 18-minute build, reproduce the cut on a slab: a 4x4 cm box
0.15 cm thick, one 1.42 mm ten-sided prism through it, EXACT solver, applied.
It gives exactly 2 boundary loops and 15.985 of 16.000 cm² of surviving skin.
The boolean, the solver, the winding and the cap geometry are all fine, which
localises the fault to the real build path — the placement, the batching, or
the order of operations. One minute of slab work removes an entire class of
suspects, and a build that is correct in isolation but wrong in the full script
is the normal case rather than the surprising one.
