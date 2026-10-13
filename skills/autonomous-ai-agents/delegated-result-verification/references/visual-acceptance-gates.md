# Gates that the background can satisfy by itself

Applies to any acceptance run that looks at a rendered frame: a bounding-box content
check, a luma/contrast check, an area threshold, a "is the subject visible" statistic.

## The sky passes a content gate

A worker scored "the subject's bounding box contains something" as
`luma range > 40` and `non-black pixels > 15%`. It passed on a frame where the
subject was **invisible**. An open sky is a gradient: large luma range, not black
anywhere. Both conditions hold with no subject present.

**A gate the background can satisfy on its own is not a gate.** Before trusting any
brightness or contrast statistic, read the same numbers on the region *outside* the
subject:

```
inside  mean 193.6  stddev 38.5
outside mean 193.3  stddev 39.0     -> difference 0.3
```

Indistinguishable inside and outside means the check separated nothing, whatever it
returned. Two honest replacements:

- **Comparative criterion** — the subject region must differ from its immediate
  surroundings by more than the background's own noise, not merely be non-uniform.
- **No numeric gate** — capture the frame and describe it. For a small dark subject
  against a bright sky, statistics will not separate them; only a look will.

The numeric version survives because it is cheap and its output is a clean boolean.
The perceptual check is the one that catches the defect the number was invented to
catch.

## A box that collapsed is measuring the bug, not the subject

A 3-pixel-wide box cannot contain enough pixels to clear a 5000-pixel area gate no
matter how well the subject renders. Lowering the threshold to make it pass hides the
real defect. Two distinct causes showed up for the same symptom:

- The projection returned a **two-point** box (feet, crown), so a subject facing the
  camera has `feet.x == crown.x` and the width is structurally zero. That is a
  harness data-shape bug.
- The subject's geometry was fragmented, so the bounding box legitimately did not
  span a body. That is an application defect.

They are indistinguishable from the threshold, and the fix is different for each, so
resolve the shape before tuning the number.

## Re-run a parked gate after the render fix; do not re-tune it

Once the renderer is fixed, a projection that was degenerate because the geometry was
broken may become well-formed on its own. A gate correctly parked as "not an
application defect, pending re-test" should get a **fresh measurement at the original
threshold**, and only then a decision about the threshold.

This bit in the opposite direction too: a reported `3px` box width became `45x88px`
after the render fix, deleting the defect from the board without anyone touching the
harness. Re-test before carrying a parked item into the next dispatch — a carried
phantom becomes a rewrite of working code.

## The perceptual check, when to insist on it

Insist on `vision_analyze` — your own read of the image — when:

- the metric is one a broken output can satisfy (stddev, colour-bin count, instance
  count, triangle count, non-uniformity, non-black fraction)
- the subject is small relative to the frame, so its statistics are within noise of
  the background's
- the fix changed **geometry, orientation, or assembly** rather than a value — a
  bounding-box adjacency check can be perfect while a figure renders as disconnected
  fragments, because fragments *are* adjacent

Ask "what do you see", not "is this blank". The second question invites the yes/no the
worker already reported. Read the same frame the worker wrote its verdict from; a
before/after A/B is what turns "looks different" into "was fragments, is a figure".

## Establish which renderer is actually running, and say what it costs

A rendering question ("is this WebGPU?") is answered by the app's **runtime
selection**, not by what the dependency graph could support. Three sources settle it,
in this order:

1. The app's own reported string — a status line that names the context it obtained
   is the strongest single reading, because the app cannot print the wrong backend
   without having obtained the wrong one.
2. The context-acquisition call site in the source. A `dyn_into_webgl` downcast
   resolving `WebGl2RenderingContext` is a path that *cannot* produce a WebGPU
   device, whatever else is linked.
3. A dependency capable of both backends, which proves nothing on its own — the
   framework supporting WebGL2 and WebGPU says only that the project picked one.

**A migration plan in the repo is not evidence of a migration in progress.** A
design document, an engine flag, a dependency with both backends compiled in — all
read as "probably migrating". Grep the application source for the *other* backend's
identifier: a project that has never been ported usually has zero hits for it, and
that absence plus a positive hit on one backend's context type is a complete answer
in two commands. State the answer as the runtime string plus the acquisition site, and
note any untracked plan document as a separate workstream so it is not mistaken for a
shipped state.

**Then say what the environment means for every number already collected.** Software
rendering (`--use-gl=angle --use-angle=swiftshader`, or a headless host with no GPU)
is not a detail of the harness — it invalidates the timing class of result outright.
Frame rates measured under a software rasteriser describe the rasteriser. Before
relocating any displacement, latency, or frame-count figure as a performance finding,
state the backend and the renderer in the same breath as the number, and say plainly
that the figure does not transfer to a real browser on a real GPU. The same caveat
governs frame-time caps: software rendering is what drove the cap to be hit in every
single frame, which is in turn what made two movement modes arithmetically
indistinguishable.
