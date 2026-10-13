---
name: browser-3d-renderer-backend-migration
description: 'Use when porting a WebGL2 renderer to WebGPU in the browser.'
---

# Migrating a browser renderer to WebGPU

Applies to porting an existing hand-written WebGL2 / Canvas2D renderer onto
WebGPU in Rust→WASM or any wasm/browser stack.

## Step 1: audit the engine's WebGPU surface BEFORE designing anything

**Check what is actually public, not what is documented.** In Rust this is the
decisive question and it is answerable in one grep:

```bash
CRATE=<engine source dir>
grep -n "pub(crate) fn" $CRATE/renderer/webgpu/impl.rs   # invisible to consumers
grep -n "pub fn"           $CRATE/renderer/webgpu/impl.rs
grep -n "#\[get" $CRATE/renderer/webgpu/struct.rs          # generated accessors
```

A `pub(crate)` `create_command_encoder` / `begin_render_pass` / `set_pipeline` /
`end_render_pass` / `finish_command_encoder` / `set_bind_group`, plus `pub(crate)`
`device` / `queue` / `context` fields with **no `#[get]` attribute**, means there
is no public route to the raw `GPUDevice` at all. The only public frame entry
points are typically `render_frame` / `render_frame_with_bind_group`, and each
does exactly: create encoder → begin ONE pass → set ONE pipeline → draw ONE
call → end pass → submit.

**That is a triangle demo. It cannot express a multi-pass deferred pipeline**
(shadow map → gbuffer → main → post), which needs several passes, several
pipelines, render targets and depth attachments inside one submit.

Verified on euv-engine 0.28.13 and on its upstream `master` (0.28.15) — the
limitation survived a release, so check master too, not just the tag you depend
on. An earlier version of this guidance (which described that same API as
publicly usable) was true of an older release and silently stopped being true.

**If the audit says no: write the layer in-repo.** Hold each WebGPU object as a
`JsValue` and drive it with `js_sys::Reflect::get`/`set` plus a `JsCast` to
`js_sys::Function` for method calls. This needs no new dependency and no
unstable cfg.

```rust
fn call1(obj: &JsValue, method: &str, arg: &JsValue) -> Result<JsValue, JsValue> {
    js_sys::Reflect::get(obj, &JsValue::from_str(method))?
        .dyn_into::<js_sys::Function>()
        .map_err(|_| JsValue::from_str(method))?
        .call1(obj, arg)
}
```

Acquisition is Promise-based (`requestAdapter` → `requestDevice` →
`configure`), so **the renderer constructor must become async**. A synchronous
`boot()` has to be restructured to attempt WebGPU in `spawn_local` and install
the backend when it resolves. Budget for this; it is the one invasive step.

### Do not reach for web-sys `Gpu*` bindings

All 136 are generated behind `#[cfg(web_sys_unstable_apis)]`, and
`GPUTextureUsage` / `GPUBufferUsage` bitmask constants are not exposed at all:

```bash
grep -A3 'extern "C"' ~/.cargo/registry/src/*/web-sys-0.3.*/src/features/gen_GPUTexture.rs | head
```

Using them forces `RUSTFLAGS=--cfg=web_sys_unstable_apis` through every CI job
and local build. Bad trade against hand-rolled `Reflect` calls.

### A canvas has exactly one context type, forever

After `getContext("2d")`, `getContext("webgpu")` returns `null` permanently, and
vice versa. Whichever backend you want to win **must claim the canvas first**;
gate any fallback behind a URL param rather than letting it initialise by default
and stranding WebGPU.

## Step 2: the "clean validation, blank screen" ladder

A clean error scope means descriptors, layouts and bindings are fine. It says
**nothing** about whether anything was submitted. When the canvas is blank with a
clean scope, work top-down:

1. **Anything submitted at all?** Instrument draw-call count and total instance
   count per frame. Zero instances ⇒ the bug is in scene/batch data, not the
   GPU. Streamed worlds rebuild their batch table on a centre crossing, and an
   empty instance array at boot is a known failure mode.
2. **Uniform buffer written before submit?** An unwritten, stale or NaN matrix
   collapses every vertex into clip space and culls silently — no validation
   error. Log the actual 16 floats.
3. **`getCurrentTexture()` per frame, and is ITS view the attachment?** Rendering
   into an offscreen view nobody presents gives a perfectly clean report and a
   blank canvas.
4. **Configured size vs backing store.** `configure()` captures width/height; if
   the canvas resizes afterwards the surface can come up empty. Re-configure on
   resize.
5. **Depth attachment actually created and attached?** Some drivers render
   nothing, with no error, when depth is expected and absent.

Log all five as **one line per frame** and read it back. One run localises the
bug; five separate shader experiments do not.

### The constant-colour fragment shader is the fastest bisect

Force the fragment shader to `return vec4(1.0, 0.0, 1.0, 1.0)` with no inputs.

- **No magenta** ⇒ the fragment stage never executed; the bug is upstream in
  submit or draw setup. Stop reading WGSL.
- **Magenta appears** ⇒ pipeline and submit are fine; the bug is in vertex data
  or uniforms.

Never bisect a blank frame by repeatedly editing WGSL — shader edits cannot
distinguish "wrong shader" from "shader never ran". A constant output does, in
one step. Same principle as rendering a debug colour to isolate a pipeline
stage: it answers "did this stage run", not "is this stage right".

This session lost ~90 minutes to bisecting shader source before the constant
colour was tried. Reach for it on the first blank frame.

## Step 3: column-major indexing — the depth remap that silently squashes the world

Adapting an OpenGL `view_proj` for WebGPU needs `z' = 0.5·z + 0.5·w`. Folding
that into the matrix looks like a two-line change and is the single most likely
way to produce a **flat field with a thin horizontal band** — geometry squashed
toward the screen centre, clean validation scope, no error anywhere.

Most Rust `Mat4` types here are **column-major** (confirm from a constructor that
ends in `Mat4::from_column_major`). In column-major,
`elements[col * 4 + row]`, which means:

| logical | actual indices |
|---|---|
| row 0 | 0, 4, 8, 12 |
| row 1 | 1, 5, 9, 13 |
| **row 2 (z)** | **2, 6, 10, 14** |
| **row 3 (w)** | **3, 7, 11, 15** |
| column 2 | 8, 9, 10, 11 |
| column 3 | 12, 13, 14, 15 |

Iterating `8 + c` and `12 + c` walks **columns** 2 and 3 — it edits one element
in each of the four rows instead of four elements in rows 2 and 3. For a
standard proj×view matrix (w-column `(0,0,0,1)`) that halves `clip.x` and
`clip.y` and leaves `clip.w` otherwise untouched, which squashes the whole scene
into a centre line. **It also explains why a constant-colour fragment shader
appears to do nothing** — the geometry is degenerate before rasterisation, so
almost no fragments exist to colour.

Correct form, per column:

```rust
for column in 0..4usize {
    let z_row: usize = 2 + column * 4;   // row 2
    let w_row: usize = 3 + column * 4;   // row 3
    out[z_row] = 0.5 * source[z_row] + 0.5 * source[w_row];
}
```

**Write the regression test before you trust the fix**, and make it assert
*negative* properties, not just the remapped values — otherwise a compile-only
test passes and the bug survives:

- rows 0 and 1 are **bit-identical** to the source;
- row 2 equals `0.5·src[row2] + 0.5·src[row3]` elementwise;
- row 3 is unchanged;
- the projection sign survives — a perspective matrix has `M[3][2] = -1`, and
  that entry must be preserved verbatim.

If the doc comment above a buggy loop describes the *intended* row behaviour
while the code walks columns, the comment was written from the maths and never
checked against the layout. Fix the comment too, and state the column-major
index table in it.

## Step 4: three failed hypotheses with one identical symptom means stop and escalate

When shader content, then the projection matrix, then a buffer-usage flag each
produced **the same blank canvas**, the fault was upstream of all three: the draw
call was never issued. Symptom-identical failures are evidence about the *layer*,
not about the layer you are editing.

Two signals that the fragment stage never ran, each decisive on its own:

- a fragment shader forced to constant magenta paints nothing;
- a **hardcoded clip-space triangle** — literal NDC coordinates, no buffers, no
  instances, no matrices, no scene — also paints nothing.

The second is the real escalation point, because it is impossible to explain
away by any data, uniform or shader defect. It localises the fault to pass
creation, context configuration or presentation. When three hypotheses have
failed identically, stop tuning and run the hardcoded-triangle bypass; do not
let a subagent spend another hour bisecting source that is provably not reached.

## Steer the worker out of a bisect loop; do not relay its progress

A graphics worker left alone will happily spend 90+ minutes bisecting shader
source for a blank canvas, re-running the same class of experiment after each
failure, and reporting each hop as progress. Three symptom-identical failures
across three different layers is a **routing signal for the main agent**, not
more work for the worker.

The main agent is holding something the worker cannot: the file the worker just
read. Reading the same function and noticing `out[8+column]` walks column 2
where the comment claims row 2 takes two minutes, versus an hour of
experiment. **When a worker enters a loop of same-symptom failures, stop it and
look at the code yourself** — do not forward its "still investigating" status.

Steer with a **diagnosis plus the specific fix**, not a request to investigate:

1. State the root cause and the exact line.
2. Give the corrected expression, not a description of it.
3. Say what to do next and what NOT to chase, explicitly ("stop reading WGSL",
   "do not commit until a screenshot shows geometry").
4. Name the acceptance artefact: a screenshot **you will look at yourself**.

Two more steering rules that saved time here:

- **Verify the worker's environment claims before trusting them.** A brief
  asserted a CDP port had a GPU; `ps aux | grep "[C]hrome"` showed it was
  launched with `--disable-gpu`, and the sibling port was SwiftShader — both
  return a null adapter, so every reading from either was meaningless. Check
  flags, not summaries.
- **If you find the worker repeating a check you already cleared, say so
  explicitly and give the result.** A worker told "I verified X is correct"
  stops re-verifying; one told "check X" spends a turn rediscovering it.

## Verify the pixels yourself before anything is committed

A HUD triangle count is a **static scene constant**, not a frame measurement —
both backends print the same number even when one drew nothing. The agent
reported `WebGPU · 2740048 tris` as success; the canvas was a uniform blue field
with geometry crushed into a horizon sliver, at 72 KB against a 332 KB control.
Nonzero triangles prove submission volume, never output.

Compare **file size as a crude emptiness signal** before opening the image: a
near-empty PNG is a fraction of the control's size and catches "renders nothing"
in one glance. Then call vision on the actual frame and quote it. A backend that
has never produced a visible pixel must not be committed, even with `cargo
check`, the full suite and clippy all green.

If a user asks you to verify something "through the browser yourself", relaying
a subagent's numbers is not verification and has already produced a wrong
"fixed" announcement once. Look at the pixels yourself or say plainly that you
could not.

## When a worker dies on infrastructure, say so and re-dispatch

A subagent can die on provider billing or quota (HTTP 402) with a partial
result. That is **not** a task failure and not a technical blocker — report it
as infrastructure, and re-dispatch. Carry forward whatever completed (here, 198
rendered previews that were reusable), and tell the new worker what already
exists so it does not redo hours of rendering.

Likewise, treat an interrupted worker's partial findings as load-bearing: it had
already measured the asset audit numerically and disproved two of its own
top-ranked "worst assets" by finding a genuine 5 mm part overlap. Keep that
honest self-correction — a worker that retracts its own claim is working well.

## Step 5: silent-failure traps

**Descriptor-layer errors throw synchronously and are NOT caught by error
scopes.** `usage` must be a numeric bitmask; passing a string like
`"RENDER_ATTACHMENT | TEXTURE_BINDING"` throws a `TypeError` at the call site,
which `call1(...).unwrap_or(JsValue::UNDEFINED)`-style code converts into a
silent `undefined`. Error scopes capture *validation* errors only, not WebIDL
type errors. Wrap descriptor construction in `try/catch` and log, or the failure
is invisible. (This exact bug shipped in euv-engine and was later fixed — check
the current source rather than trusting either statement.)

**Depth range differs from OpenGL.** WebGPU NDC z is `[0,1]`, OpenGL is `[-1,1]`.
Reusing an OpenGL `view_proj` unchanged clips everything — `z < 0` is cut by the
near plane, `z > w` by the far plane — giving a clear-colour-only canvas with
**no validation error**. Remap before upload.

**Bind-group usage flags must match the shader's `@binding`.** A mismatch can
return `undefined`, or succeed while the draw emits zero fragments. After every
pipeline/bind-group creation, print each handle's `.is_undefined()`.

**Buffer and texture usage masks are different numeric spaces.** Don't reuse a
buffer constant in a texture descriptor.

**Index format is a WGSL type string, not a Rust type** — `"uint32"` needs
`index_count * 4` bytes. Mismatch is a silent zero-draw.

## Verification discipline

- Never build the verification strategy on GPU readback if the engine's
  `copy_texture_to_buffer` is suspect — check whether it early-returns on a
  field that is always `None` before trusting any readback result. Verify with
  browser screenshots instead.
- A render backend that has never produced a pixel must not be committed, even
  when `cargo check`, the full test suite and clippy are all green. Those prove
  the code compiles, not that it draws.
- Establish the browser has a real GPU **before** trusting any geometry reading.
  Under `--use-angle=swiftshader`, `--enable-unsafe-swiftshader` or
  `--disable-gpu`, `requestAdapter()` returns `null` and the game silently falls
  back to another backend — you then measure the fallback, not your work.