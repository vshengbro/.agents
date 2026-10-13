---
name: gl-webgpu-ndc-and-queue-conventions
description: Use when porting GL to WebGPU in Rust/wasm.
---

# GL → WebGPU: the two conventions that silently corrupt a port

Porting a WebGL2 renderer to WebGPU (euv/wasm-bindgen) has **two** traps that
both produce a *clean-validating, submitting* frame with no error anywhere.
Neither shows up in a console check.

## 1. NDC depth needs remapping; NDC **y usually does not**

| | x | y | z |
|---|---|---|---|
| OpenGL NDC | +right | **+up** | −1..+1 |
| WebGPU NDC | +right | **+down** | **0..1** |

Depth is a real, mandatory transform: `z' = 0.5·z + 0.5·w`, applied to rows 2
and 3 of the column-major view-projection before `writeBuffer`.

**The y-flip is the trap.** "WebGPU +Y is down, so negate the y row" is
*usually* wrong here — `Camera::perspective` in this repo already produces a
matrix in WebGPU's convention, so negating y flips the scene upside-down. I
shipped the negation, measured it, and it was inverted. **Do not apply a
GL→WebGPU y flip unless a measurement says the unflipped frame is wrong.**

Flipping y also reverses screen-space winding, so `frontFace` must change in
lockstep (`cw` ↔ `ccw`). Getting one without the other culls every front face.

## 2. `GPUQueue.writeBuffer` is on the *queue* timeline

`writeBuffer(buf, 0, bytes)` executes **before** any command buffer in the
same submit. So this per-batch pattern is wrong:

```rust
for batch in batches {
    queue.write_buffer(&buf, 0.0, &batch_bytes);   // ALL of these run first
    pass.draw_indexed(..., 0);                     // every draw reads the LAST write
}
```

N batches → N writes all complete first → every `drawIndexed` reads the final
batch's transform → the whole city stacks at one point. Symptom: a handful of
huge flat colour blocks (1–2 colour bands per column when you sample pixels).

Correct: concatenate the whole frame's instances into one contiguous buffer,
upload **once**, then draw slices via `drawIndexed(..., firstInstance)`.
Gotcha: `reserve_instances(n)` may **reallocate**, and `setVertexBuffer` binds
the object identity — so bind the instance buffer *after* any growth.

## How to actually measure orientation (do not trust vision alone)

Vision tools will confidently report "upside down" from an inverted-looking
A/B shot, and I twice believed a wrong reading over the data. Calibrate the
metric first: run the **identical** profile code over the **known-good WebGL2
screenshot** and the WebGPU one. Correct = sky% high at top, dark% high at
bottom. Inverted = the mirror of that. Only then conclude.

Counters that actually proved useful: per-column colour bands (flat geometry →
1–2), `alpha0Frac` (opacity), `nDraw` vs `nSetIB` (1:1 = batches intact).

## Related

- [[verify-claimed-defect-before-applying-prescribed-fix]] — this whole class of
  bug is the reason that skill exists; both fixes were *prescribed* and both
  were wrong.
- [[rust-standards]] — keyword filenames (`const.rs`/`fn.rs`/`impl.rs`/
  `struct.rs`) are legal but **pure**, and may only `use super::*;`.