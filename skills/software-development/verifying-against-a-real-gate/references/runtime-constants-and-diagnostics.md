# Reading runtime ground truth before trusting a constant

Depth for the "compare nothing you did not read at runtime" rule in SKILL.md.
Cases where a value a guard depends on disagrees with the function producing
it, or where a diagnostic is real but filtered out of view.

## The web-sys framebuffer numbering trap

`WebGl2RenderingContext::FRAMEBUFFER_COMPLETE` is **36053** — the WebGL 1
value. `checkFramebufferStatus` in a WebGL 2 context returns **36054** for a
genuinely complete framebuffer. Same condition; numbering off by one.

A guard of the form

```rust
let status: u32 = context.check_framebuffer_status(TARGET) as u32;
status == WebGl2RenderingContext::FRAMEBUFFER_COMPLETE as u32
```

is therefore **always false**. Every render target is declared broken; the app
falls back to software rendering (or to nothing) and the canvas is black —
while allocation logs read healthy, because allocation genuinely succeeded.

```rust
// Accept both schemes; name the second rather than inlining the number.
const FRAMEBUFFER_COMPLETE_WEBGL2_OFFSET: u32 = 36054;
let ok = status == WebGl2RenderingContext::FRAMEBUFFER_COMPLETE as u32
    || status == FRAMEBUFFER_COMPLETE_WEBGL2_OFFSET;
```

Symptom worth memorising: the app logs an incomplete-framebuffer error **every
frame** while a probe shows the *default* framebuffer healthy. Per-frame
repetition plus a healthy default target is this bug, not a driver issue.

## Prove the probe before trusting the probe

The costly mistake is a decoder table written from the spec rather than from
the runtime: `36053 -> COMPLETE` in a hand-rolled name map, so every genuine
`INCOMPLETE_*` code is reported as COMPLETE, the app looks healthy, and you
conclude the application is fine while its own log says otherwise. Several
rounds were spent bisecting the wrong subsystem this way.

Read both sides of any comparison from the running system:

```js
const gl = document.createElement('canvas').getContext('webgl2');
({
  complete: gl.FRAMEBUFFER_COMPLETE,   // 36053
  status: gl.checkFramebufferStatus(gl.FRAMEBUFFER),
});
```

Hook the real method rather than reasoning about what it returns, and log the
attachments too — status alone cannot distinguish "no colour attachment" from
"bad texture dimensions":

```js
const orig = WebGL2RenderingContext.prototype.checkFramebufferStatus;
WebGL2RenderingContext.prototype.checkFramebufferStatus = function (t) {
  const st = orig.call(this, t);
  if (st !== this.FRAMEBUFFER_COMPLETE) {
    console.log(st, !!this.getParameter(this.COLOR_ATTACHMENT0_BINDING),
                   !!this.getParameter(this.DEPTH_ATTACHMENT_BINDING));
  }
  return st;
};
```

Install it with `Page.addScriptToEvaluateOnNewDocument` so it exists before the
app boots; hooking after boot misses the initialisation-time calls, which are
usually the ones that matter.

## Triangles drawn is not pixels on screen

A non-zero submitted-triangle counter proves geometry reached the pipeline, not
that any of it was rasterised. To separate "dim but real" from "HUD over an
empty canvas", measure the screenshot instead of judging it:

```python
from PIL import Image
im = Image.open(path).convert("RGB"); px = im.load(); w, h = im.size
nonblack = total = mx = 0
for y in range(0, h, 3):
    for x in range(0, w, 3):
        v = max(px[x, y]); total += 1; nonblack += v > 10; mx = max(mx, v)
print(f"nonBlack={100*nonblack/total:.2f}%  meanMax={mx}")
```

The HUD is drawn over the canvas, so a small non-black fraction is the
expected floor. The question is whether the *world region* contains anything,
and only a number settles it.

Two more corollaries from the same investigation:

- **Filter console output by content, not by severity.** Shader-compile and
  framebuffer-rejection diagnostics arrive as plain `[log]`-level entries.
  Collecting only `error` / `warning` types discards the one line that explains
  the symptom, and the run looks suspiciously clean.
- **A published status string is the cheapest branch selector available.** A
  HUD field naming the live backend (`WebGL2` vs `init` vs a fallback message)
  narrows the search space before any other tool is picked up.

## Four dead channels that read as specific, actionable defects

Each of these produced a clean number, a confident root cause, and a dispatched
fix for a bug that did not exist. The common shape is a diagnostic field that
nothing in the path under test writes, so the probe reports a constant and the
constant is interpreted as behaviour.

**A multiplier field that is really a time-warp scale.** A debug channel
exposed `{speed: N}`. Read as "walk at N×", it showed 1× and 8× moving within
4% of each other — a precise, reproducible "sprint does nothing" defect, with
a plausible physics explanation attached. The field was assigned at one site,
initialised at another, and read at neither. The real speed was measured at
`run/walk = 1.8261` against a `8.4/4.6` constant pair — exact to four decimals.

> **The tell:** two inputs that must differ produced bit-identical output
> (`0.61331` vs `0.61331`, ratio exactly `1.0`). That is not a weak effect, it
> is an absent one. Confirm the field is read before scaling anything by it.

**A counter published on an interval reads as a stall.** A debug object
rewritten every third frame was sampled by frame-count waits, so 8 of 24
samples returned a stale value. Two "walk two frames, freeze one" failures
appeared; a per-frame sampler with a contiguous frame sequence showed a
constant 0.60 m/frame and zero zero-displacement steps. Autocorrelation at lag 3
would have separated the two cases outright — a genuine stutter peaks there, a
sampling artifact does not.

> **The tell:** suspected periodicity (exactly N frames on, M off) in a
> throttled environment is the signature of the throttle, not of the loop.
> Report the frame-number sequence as part of the evidence; non-contiguous
> indices invalidate the whole segment.

**An interaction radius the test never entered.** A vehicle-entry check
reported `ENTER FAILED` at a spawn point 12.34 m from the nearest vehicle.
The keybind was wired correctly in three places; the actor was simply outside
the range. Re-running the same scenario after a teleport produced
`vehicle_never_null: true`, `player_follows_car: true`, and a collision reading
of `car_surface_gap = -0.00` with `speed ≈ 0` at a wall face.

> **The tell:** an interaction that reports "did not engage" is ambiguous between
> "not implemented" and "not in range". Log the distance to the interactable in
> the same run — one number converts a mystery into a precondition check.

**An input event bound to a different device than the test sends.** A weapon
whose trigger is a canvas `mousedown` was exercised with keyboard events routed
through the tracked-keys path. 14 shots, target health `100.0 → 100.0`,
magazine `12 → 12` — a clean "player fire is dead" defect. The source carried a
comment naming the whole failure: the headless mousedown listener reads the flag
as permanently false. Zero damage was registered because nothing fired.

> **The tell:** grep the *source* for the event the app binds, not the one the
> harness sends. `fire_held` false after injecting `Digit2` says the injection
> went to the wrong channel, not that firing is broken. Also: prefer a field the
> effect lands on (`enemies[].hp`, `kills`) over an intermediate
> (`magazine`), which may itself be throttled or never decremented.

### Reading a derived diagnostic honestly

Several runs of one scenario produced `outBy=+1.969` (5 of 8 angles out of
bounds), then `d` wandering `2.4→4.3`, then three bit-identical segments at
`d=2.536`. Three pictures of one scenario is a metric that is not measuring a
stable fact — here the bound being tested came from a probe-chosen collider,
which varies with where the actor was pinned. The remedy is not a fourth run: it
is to read the authoritative geometry out of the source, re-derive the
predicate from that, and only then report. Until the source-derived baseline
exists, the state is "not qualified", and it is a different state from FAIL.

