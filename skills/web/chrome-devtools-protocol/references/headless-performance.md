# Headless throttling, polling, and software-rasterized WebGL

Depth notes for pitfalls 8–9 of SKILL.md. Read when a CDP harness is slow, when
a state probe races the app's loop, or when a WebGL canvas comes back black or
wrong-looking.

## 1. Poll a state predicate; never sleep

Headless Chrome can hold `requestAnimationFrame` near 1 fps, so a request that
mutates state takes seconds of wall time to become observable. Two tempting waits
are wrong for *different* reasons:

```python
# WRONG: the loop may not have ticked at all in 2 s
await asyncio.sleep(2.0); st = await d.st()
# WRONG, and worse: `frames` is read AFTER the request already landed,
# so start+n is satisfied on the first poll and you sample pre-rebuild state
start = (await d.st())["frames"]; await asyncio.sleep(1)
```

Poll the predicate you actually care about, with a generous cap:

```python
async def until(d, pred, cap=40, step=0.3):
    for _ in range(cap):
        await asyncio.sleep(step)
        st = await d.st()
        if st and pred(st):
            return st
    return await d.st()
```

Pick a predicate that can only be true *after* the work completed, not merely
after the request was sent: "the world-generation centre is now a multiple of the
tile pitch" proves a rebuild ran; "the frame counter advanced" proves only that
time passed.

## 2. One variable per run, and a measurement that can say "spinning"

The most expensive mistake when hunting a performance cause is bundling a fix
with an experiment. Adding `--disable-frame-rate-limit` *and* keeping an
application time-scale multiplier produced a 403 fps reading that was pure
spinning — no vsync, no work done — and it read as a solved problem.

Rule: **one variable per run, and a measurement that can distinguish "faster"
from "spinning".** Frame count alone is not a performance measurement — a
browser that never yields does not advance the simulation. Sample frames *and*
a value the app only changes by doing work, across the same interval:

```python
f0 = await ev("String(__app.frames)"); p0 = (await st())["pos"]
await asyncio.sleep(2.0)
f1 = await ev("String(__app.frames)"); p1 = (await st())["pos"]
print(f"fps~{(float(f1)-float(f0))/2:.1f}  work_done={p1 != p0}")
```

A high fps with no work is the spinning case and is worth nothing.

**Corollary: once a real 60 Hz is achieved, delete every compensation for the
throttle.** A `time_scale` multiplier, a `step_until(distance)` wait, and poll
caps sized for 1 fps are all now wrong, and the multiplier is actively harmful —
at 8x a single 16 ms frame advances 8 s of simulation, which is enough travel to
tunnel straight through a thin wall. The tunneling reads as a collision bug and
sends the search after geometry that is fine. Distance-based waits become correct
again only at 60 Hz; a fixed-poll-count wait is the unit that stays correct at
both.

## 3. The SwiftShader launch flags

Software-rasterized WebGL under `--headless=new` is the normal case, and it is
frequently 60–400x slower than the same page in a real browser. Read the
browser's own log before guessing at flags — a line like
`GL Driver Message (...): GPU stall due to ReadPixels` repeated every frame
identifies the cost: the app reads the drawing buffer back once per frame and
the stall dominates. That is fixed by a launch flag, not by editing the app.

```bash
"$CHROME" --headless=new --no-sandbox --disable-gpu \
  --use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader \
  --disable-accelerated-2d-canvas \       # <- the fix; 2D canvas hits a slow
                                          #    path that stalls on readback
  --remote-debugging-port=9223 --remote-allow-origins='*' \
  --disable-background-timer-throttling --disable-renderer-backgrounding \
  --user-data-dir=<scratch>/profile --hide-scrollbars --window-size=1280,800 \
  about:blank
```

`--remote-allow-origins='*'` is not optional on recent Chrome: without it
`/json/version` can answer while `/json/list` and `/json/new` return empty,
which looks exactly like a crashed browser.

`HeadlessExperimental.beginFrame` — the textbook way to decouple simulation time
from render throughput — **no longer exists**: the domain was removed in Chrome
154, and an `except: return` around the call makes it fail silently. Check the
domain exists before building a harness on it:

```python
r = await cmd("HeadlessExperimental.enable")
if "error" in r: ...   # -32601 "wasn't found" means the plan is dead
```

## 4. WebGL: read the state that is actually there

A black or wrong-looking canvas is the hardest thing to debug through CDP,
because almost every WebGL query returns a plausible value even when you are
asking the wrong question.

**Identify the pass before interpreting anything.** A deferred renderer binds
several framebuffers per frame (shadow, G-buffer, SSAO/SSR/bloom half-res, scene,
then the default framebuffer for the present). A probe that doesn't say which one
it sampled will be read as a bug when it is correct behaviour:

- Reading `COLOR_ATTACHMENT0` on a **depth-only** shadow FBO returns
  `[0,0,0,0]`. That is correct — there is no color attachment — and proves
  nothing about the main pass.
- `getParameter(COLOR_ATTACHMENT0_BINDING)` queried mid-frame can read `false`
  while the attachment is in fact present, because the binding was sampled at a
  different point in the frame than the draw.

Identify the pass by `gl.getParameter(VIEWPORT)` and log which program is
`CURRENT_PROGRAM` at the same instant. Program identity is the cheapest
discriminator: a shadow program legitimately has one uniform and no samplers, so
`samplers: []` there is not a finding. Prefer the authoritative query —
`getFramebufferAttachmentParameter(..., FRAMEBUFFER_ATTACHMENT_OBJECT_NAME)` and
`..._OBJECT_TYPE` (expect `5890` = `TEXTURE_2D`) — over the `*_BINDING` enums,
which are moment snapshots and the usual source of false negatives.

**Framebuffer status codes.** `gl.FRAMEBUFFER_COMPLETE` is **36053**, and
`checkFramebufferStatus` returns 36053 for a complete framebuffer. Do not
"correct" this to 36054 — a probe comparing against 36054 reports every healthy
framebuffer as broken. `getTexLevelParameter` does not exist in WebGL2 (it is
WebGL1); attach a bound texture to a scratch FBO, check status, and
`readPixels` a small region.

**Read pixels, not the status code.** A framebuffer can report
`FRAMEBUFFER_COMPLETE` while every `glClear` is a no-op and every draw is
discarded, because an attachment exists but is not *renderable*. Build scratch
framebuffers in the live context and compare them; a working variant writes the
clear colour back as `[64,128,191,255]`. This is the probe that finds a
non-renderable depth attachment — `R32F` is a *colour* format, renderable only
with `EXT_color_buffer_float`, and attaching it to `DEPTH_ATTACHMENT` is rejected
outright by several implementations (SwiftShader among them). The app-level
symptom is a healthy triangle count, a live frame counter, inconsistent
`FRAMEBUFFER_COMPLETE` reporting, and a uniformly black canvas. Depth-only shadow
maps fail the same way; when the shadow pass compares depth manually
(`texture(map, uv).r` against fragment depth), switching to `DEPTH_COMPONENT24`
needs no change to the sampling code.

**Exonerate the fragment stage with a constant before touching the pipeline.**
Replace the fragment shader's final output with an unconditional literal
(`out_color = vec4(0,1,0,1);`) and rebuild. A still-black screen proves the
fragment stage never executed or its output never landed, eliminating lighting,
textures, uniforms and tone mapping in one edit; a green screen proves the fault
is upstream (vertex transform, instance data, geometry). Revert the whole
experiment afterwards, including helper edits made while bisecting.

**GL errors are sticky — drain them before probing.** `gl.getError()` returns the
*first* error since the last call and keeps returning it until cleared, so a
`1286 INVALID_FRAMEBUFFER_OPERATION` seen "every frame" is frequently left over
from an earlier frame. Loop `while (gl.getError() !== 0) {}` before a
measurement, and read `getError()` *immediately* after the single call you care
about.

**Prove your hook fired.** Monkey-patching
`WebGL2RenderingContext.prototype.framebufferTexture2d` can miss calls entirely
if the code holds a bound function reference, producing an empty event log and
the wrong conclusion ("the attachments are never set"). Assert your hook actually
observed the call before believing a negative result from it. Conversely, hooking
`drawArrays` / `drawElementsInstanced` and keying on
`count === 3 && FRAMEBUFFER_BINDING === null` reliably catches the present pass.

**Under software rasterization, prefer synchronous readback.** With
`--use-angle=swiftshader`, a `requestAnimationFrame` promise used to sequence a
probe can never resolve, and `readPixels` on a large region can stall. Sample a
small region and read synchronously outside rAF. `preserveDrawingBuffer: true` in
the context attributes is what makes a `readPixels` of the default framebuffer
meaningful after the frame ends.

**The general rule: a measurement is only worth the proof that it sampled the
target you intended.** Before reporting a number as a root cause, state which
pass/FBO/program it came from.
