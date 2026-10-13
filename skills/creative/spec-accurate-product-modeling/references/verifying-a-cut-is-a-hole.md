# Proving a cut is a hole, not a pocket or a decal

A port that is not cut is the single most expensive silent failure in this kind
of model. The render shows a dark recess, the bbox is exact, no boolean
raised, and the feature is a painted-on decal. This file is the ladder that
separates those three states, and the arithmetic that causes the middle one.

## 1. A face-area census is not a cut test

The obvious cheap check: sum the skin faces inside the feature's footprint,
compare with the footprint area, call it CUT when the total comes out lower.

**Fragmented is not open.** A boolean leaves the skin shattered into thousands
of small faces, so the total *does* fall below the footprint while the surface
is still completely covered. Measured on a real 1.5 mm panel:

| port | skin coverage | census verdict | ray verdict |
|---|---|---|---|
| USBC_1 | 88.1% | CUT | capped at 0.00 mm |
| USBC_2 | 88.2% | CUT | capped at 0.00 mm |
| SDXC | 97.3% | CUT | capped at 0.00 mm |

"Open" is a claim about what lies *behind* the surface. Only a ray answers it.
Keep the census as a diagnostic — the coverage percentage is genuinely useful
even when the verdict is not in doubt — but never let it produce the verdict.

## 2. A coincident cap is read as a pocket

The subtlest way a boolean silently does nothing. When a cutter's cap lands
**exactly** in the plane of the face it cuts, EXACT keeps that face and yields a
shallow pocket rather than a through-cut. The cutter looks right, the bbox does
not move, the vertex count barely changes, and the render shows a recess with a
skin still across it.

This is arithmetic, not tolerance. Centring a cutter of total depth `D` at
`face - D/2` puts its outer cap on `face` **by construction**:

```python
# WRONG: spans face-span .. face, so the OUTER cap sits exactly on the skin
span_in = WALL + 0.45
cy      = y_face - span_in / 2.0        # -> outer cap lands on y_face

# RIGHT: free air in front, empty cavity past the wall; neither cap can coincide
OUTSIDE, CAVITY = 0.45, 0.45
span = OUTSIDE + WALL + CAVITY
cy   = face + (OUTSIDE - (WALL + CAVITY)) / 2.0
```

The tell is a comment that describes the opposite of the code — "neither cap
lands on a face" written directly above a span of `face - span .. face`. **Do
the arithmetic before trusting the comment**: print the cutter's real span and
compare it with the skin plane. And if a sibling helper in the same file already
solves this for a different feature, that is your proof of the required
arrangement — read it before writing a new one.

## 3. An isolated repro that does not reproduce is a disproof

Before blaming the coincidence, build the smallest case that should exhibit it:
one slab, one cut, one ray. A coincident cap opens a **clean solid panel**
perfectly well — which is exactly why the theory survives two rounds of argument
against a real model. When the isolated repro does not reproduce the failure,
the coincidence is not the cause.

Do not keep arguing the mechanism. Name the blocker instead — this is the step
that ends the search:

```python
hit, loc, nrm, idx, obj, mtx = scene.ray_cast(dg, origin, direction)
print(obj.name, loc, [me.vertices[i].co for i in me.polygons[idx].vertices])
```

Printing the stopper's **object name** and its plane settles in one call what
an hour of mechanism-guessing does not. Two cautions:

- **Blender's `Polygon.area` is already in cm² for a cm scene.** Dividing it by
  100 again produced impossible "166 cm²" blocker faces and sent the search
  after geometry that does not exist.
- A tiny blocker area is the real signature — the offending face was ~0.017 cm²,
  a sliver lying in the skin plane across the opening.

## 4. A gate that cannot tell a socket from a lid is measuring itself

Ray gates inherit the census's failure one level deeper. "Did the ray meet
*anything* metal?" calls a correctly built connector 38–43% capped, because a
socket's walls sit **inside** the port's own footprint. That is a socket, not a
lid.

Several legitimate depths live inside a correct opening, so name the threshold
for the specific defect you are hunting:

| depth behind the skin | what it is | verdict |
|---|---|---|
| ~0.0 mm | the panel's own skin | **capped** — the defect |
| ~1.0 mm | the socket's walls, by design | correct |
| ~2.4 mm | the tongue / back plate | fully open |

Three rules follow:

- **Filter on object name AND depth.** Name-matching alone misses a stray skin
  sliver; depth alone calls every socket a lid.
- **Sample over the feature's own footprint, never the cutter's rectangle.** A
  cutter is typically oversized ~1 mm per side and bevelled, so the aperture is
  larger than the port. Reading that bevelled lip as "capped" manufactures a
  6–13% failure on a panel that is fully open.
- **Add controls, and keep them off the helper under test.** One must be solid
  (a proud status LED, blank panel), one must be open. A control that flips is a
  finding about the *gate*. Controls that share the predicate under test
  inherit its bug, so give them a depth-only check.

## 6. A 0.0% open reading: take a section before you reason about booleans

Sections 1–5 cover a *port* that was not cut. A **perforated field or band
reading exactly 0.0% open** is a different failure with a different cost, and
the expensive mistake is spending hours on boolean winding when the answer is
one loop over the mesh.

The ladder, in the order to run it — each rung rules out the comfortable
explanation before you are allowed to blame the geometry:

| suspect | test | outcome when it is not the cause |
|---|---|---|
| stale build artifact | full rebuild, re-run the gate | identical numbers — ruled out |
| probe samples a range the builder never used | diff the two files' arithmetic | real, and fixing it changed nothing |
| sample grid steps over the hole rows | compare grid step to the *measured* row pitch | most samples land inside a row — cannot explain 0.0% |
| the surface helper measures an interior point over a hole | print its walk | returns the nominal skin at every row — correct |
| the feature sits on a surface nobody aims at | **take a section** | **it does** |

**The section is the step that ends the search.** Bucket the mesh's polygon
centres by the axis perpendicular to the view, and compress the sorted values
into runs:

```python
zs = sorted({round(abs((me @ poly.center).y), 2) for poly in mesh.polygons
             if abs((me @ poly.center).x) < 0.3})
# compress to runs, then read: a continuous run where holes should be is slab
```

A run reading |y| 9.60 → 9.90 where the perforations are is 3 mm of solid
metal. No theory, no `ray_cast` interpretation, and it names the number the
fix has to move.

### Two ways a feature is closed, which the open fraction cannot distinguish

- **Blind pockets** — the cutter ran, leaving dense geometry on a face set
  *back* from the skin, and the wall behind it was never pierced. Polygon
  density on the feature's row is high and the opening is still zero.
- **Nothing built** — the mesh is sparse where the feature should be.

High polygon density on a feature's row proves the cutter ran; it does not
prove it passed through. Only the section or a ray through the hole's own
footprint separates the two. Read the two depths against the surfaces you
printed: holes at |y| 9.55, skin at 9.85, and a declared recess of 0.075 cm
means the 0.30 cm offset is not the intended recess and something else placed
that field.

### Verify the expected value was derived from what was built

A gate whose target is a duty cycle computed from the spec's row pitch fails a
*correct* probe when the built lattice's real pitch differs. Here 1.39 mm was
built against 0.906 mm specified, so the expected 7.5% should have been 4.9% —
outside the tolerance, so the row could not have passed even with the geometry
fixed. Before concluding a measurement is wrong because it misses its target,
confirm the target came from the built artifact.

### Two files holding one quantity is a defect, not a style choice

A builder and its verifier each kept their own arithmetic for a feature's
position; the builder drilled above a fillet and the verifier sampled the
photographic range, so 11 of 14 samples landed on solid metal by design. Lift
the value into the shared spec and have both sides import it — **never
recompute it in the verifier**, which is a third copy and a fresh drift. Keep
the vendor's measured value next to the modelled one rather than overwriting
it: the disagreement is the finding, and deleting the measured constant
destroys it.

## 7. Close the loop on the asset, not the source

The source `.blend` and the shipped `.glb` are different artifacts and the
page loads the second one. Two traps:

- **Rebuilding is not exporting.** A fixed builder that was never run through
  the exporter leaves the site serving the old geometry with the new source
  committed. Compare mtimes of the source and the shipped asset, and re-run the
  export before any page-level or deployed verification.
- **Draco-compressed GLB cannot be vertex-read directly.** Accessor min/max on
  a compressed primitive is a decode hint, not real geometry. The **JSON chunk
  is uncompressed**, though, which is enough to assert conventions, node
  hierarchy, and bounding envelope without a browser and without a decoder:

  ```python
  d = open(asset, "rb").read()
  off = 12
  while off < len(d):
      ln, ty = struct.unpack_from("<II", d, off); off += 8
      chunk = d[off:off + ln]; off += ln
      if ty == 0x4E4F534A:      # b'JSON'
          print(json.loads(chunk)["nodes"][0]["translation"]); break
  ```

  That is how the front-face axis convention gets settled from the artifact
  instead of from a comment — and why the same convention must be checked in
  *every* file that touches a face, since it gets written backwards more than
  once.
