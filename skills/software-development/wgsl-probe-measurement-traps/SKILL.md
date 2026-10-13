---
name: wgsl-probe-measurement-traps
description: "Probe WebGPU pixels without measuring the wrong surface."
---

# Measuring WebGPU pixel output honestly

A CDP probe that reads a canvas can be perfectly correct and still measure
the wrong thing. Every trap below produced a confidently wrong number in
one session; all six were caught only by reading `world.y` back out of the
GPU, not by inspecting code.

## 1. The sample line may be occluded, not the ground

Projecting a world point to a pixel assumes that pixel *shows* that point.
It often does not.

**Signature:** measured values that make no sense for the surface you
think you sampled. Here, ground points at `y=0.16` reported `world.y ≈ 1.34`
— the samples were the building wall standing in front of them.

**Proof technique:** encode `world.y` into greyscale, build, shoot, invert
the sRGB encode, read it back. Five minutes; it converts a guess into a
measurement.

```
// vertex: return (world.y + 1.0) / 6.0;   fragment: emit the varying directly
world.y = srgb_to_linear(byte) * 6.0 - 1.0
```
Note the probe's own line said it walked *away* from the building — the
geometry claim was right, the *visibility* claim was never checked.

## 2. The player character sits exactly where a centre-column probe samples

`charBox = [640, 754.8, 640, 329.5, 0.8]` — the body spans screen x=640
from py 330 to py 755. A probe sampling the frame centre measures **the
character**, every sample, silently.

Always project the intended point first and check its px/py against
`charBox`. Sample off-centre (e.g. `x = axis + 2.0` metres) and reject any
sample within ~70 px of the character.

## 2b. The reject guard can silently delete the band you came to measure

Guard #2 pushes the sample column further from the frame centre the closer
the ground point is — off-axis points near the camera project *toward*
centre. So the samples nearest the thing under test are the ones the guard
kills. A run asked for "luma within 1.5 m of the wall" got **zero** such
samples and the contrast came back `nan`; nothing errored.

**Rule:** print attempted-vs-kept per band *before* computing any stat, and
treat an empty band as a failed measurement, not a zero. Reject-safely by
moving the sample column (`SAMPLE_X` 25 → 27 → 29), never by reporting the
gap.

## 2c. Slope sign flipping across nearby columns ⇒ you crossed an object

A ground "distance gradient" measured along one column is really a
projection of every occluder (shadows, parked cars) that column happens to
pass through. Measured at noon: slope `-6.7` luma/m at x=25 but `+4.6`
luma/m at x=27, two metres away. A true ground falloff cannot invert.

**Rule:** fit the slope at ≥2 sample columns before reporting it. Sign
agreement is the check. Also inspect luma *across* the row, not just along
it — a real gradient is smooth across x, a shadow is a step (here 122→43
between adjacent 10-px columns) or high-frequency speckle.

## 3. No cache-buster on the wasm URL → you measure the previous build

`index.html` has `?cb=<pid>`, but the wasm is loaded via
`new URL('./pkg/…wasm', import.meta.url)` with no query. Chrome serves the
**disk-cached** wasm.

**Signature:** a code change provably reaches the binary (sha256 differs on
disk) yet the readings are byte-identical to the last run.

```python
await d.cmd("Network.enable")
await d.cmd("Network.setCacheDisabled", {"cacheDisabled": True})
```
Always shasum the deployed wasm before and after a run.

## 4. One `CARGO_TARGET_DIR` shared by A/B worktrees is not an A/B

Two worktrees sharing a target dir can reuse each other's artifacts. Give
each build its own (`wg-before`, `wg-after`) and re-verify the BEFORE wasm
hash matches the original BEFORE build before trusting any comparison.

## 5. A black screen is a WGSL compile error, not a rendering bug

Missing a struct field → shader compile failure → invalid pipeline → black.
`cargo test` and `cargo check` are **green**; they never parse the string.

Also: a *silent* variant where the vertex and fragment copies of the same
uniform struct differ. WGSL computes uniform offsets from **each struct's
own declaration order**, so a vertex copy that omits blocks it does not
read will read the wrong bytes. Here the height floor silently became the
shadow strength (1.0) instead of 0.30 — no error, just wrong pixels.

Pin both copies against the Rust-side field list in a test that compares
the **field-name sequence**, not substring presence.

## 6. Inference chains hide the bug; bisect instead

I spent several cycles deriving what input could produce a measured 0.898,
never testing it. The decisive moves were cheap and dumb:

- **Ablate**: force the term to a constant, measure. Isolates formula from plumbing.
- **Hardcode the constants**: removes every uniform read. If behaviour is unchanged, the plumbing is innocent.
- **Read the value back**: encode the scalar you are reasoning about into colour.

Each is a 3-minute build. Each one ended a hypothesis loop that reasoning had not.

## Guard against clipping

Diagnostics packed into RGB get clipped to 1.0 and carry zero information
(three "measurements" all read 1.0). Choose scales so every channel stays
well inside [0,1], and if a channel saturates, treat the reading as void.

## What a correct result looks like

When a *uniform* darkening is removed, the per-pixel ratio across the whole
band is a **near-constant** (here 1.4209 ± 0.009). That is the signature of
having fixed the right thing. If instead you add a proximity term, expect a
gradient. Check which one you got before claiming success — and read the
pixels yourself; a subagent's number is a claim, not a verification.

## Scene facts worth reusing

- LOFT sample building: centre `(23, 30)`, half `[6, 5]`, yaw `= π/2`;
  AABB `x∈[18,28] z∈[25,35]`; **south wall at `z = 35`**.
- Ground mesh heights (`game.rs::build_ground_near`): road `0.0`,
  sidewalk `0.14`, lot `0.16` — so a contact-AO height floor must exceed
  `0.16` to structurally exclude the ground.
