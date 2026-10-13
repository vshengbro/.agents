---
name: wasm-gpu-mesh-index-alignment
description: Use when a WebGL2 batch draws the wrong asset.
---

# WebGL2 mesh upload must be 1:1 with the scene mesh list

## The trap

`WebGlRenderer::upload_mesh(&mut self, mesh) -> Result<usize, String>` returning
`self.meshes.len() - 1` has **push semantics**: every call appends a `GlMesh`.

`SceneBatch::mesh_index` is a `Scene::meshes` index, and `draw_batch` uses it to
index the renderer's list **directly** (`self.get_meshes().get(mesh_index)`).

So the two lists only agree if every mesh is uploaded **exactly once, in
`Scene::meshes` order**. Ignore the returned index and upload in a single loop =
fine. Upload in two places (e.g. "upload after build_scene" AND "upload again
after spawning the player rig") and the renderer's list grows to `n + m` entries
while batches still index `0..n` — every batch past the first loop's length
silently renders **some other asset**.

Real instance: limb batches (scene meshes 31..43, the character) resolved to
assets #1..#13 of the second pass — three 30 m buildings drawn with a 1.75 m
human's model matrix. Painted 108,234 px; the character itself was never drawn.
The submitted triangle count was the only tell: 482,420 -> 454,612 after the fix.

## Rules

1. **Upload once.** Put the single `upload_mesh` loop after every code path that
   can add to `scene.meshes` (procedural ground, per-part character rigs, etc.).
   Comment the invariant at each site.
2. **Never `let _ = webgl.upload_mesh(..)`.** A swallowed failure desyncs the
   lists and the symptom is "geometry is there but the wrong thing renders" —
   hours of wasted debugging. Log every `Err`, capped to N lines.
3. **Assert the counts.** `scene.meshes.len() == renderer.meshes.len()` after
   upload. A mismatch is a hard error, not a log line.
4. **Tri count is a diagnostic.** If a fix changes the submitted triangle total,
   the bug was in *what got drawn*, not in shading.

## Bisecting "geometry renders but wrong / absurdly sized"

Cheapest decisive order:

1. `?hide=<batch indices>` URL param (if the app has one) to isolate one batch.
2. `gl.readPixels` the **bounding box of non-background pixels** — a number, not
   a judgement call. Then compare against the app's own projection of the same
   object. If the two disagree, the fault is between vertex data and instance
   matrix, NOT in the camera/projection.
3. Dump the live instance `model` matrix and the asset's own `bounds`. Both
   correct + wrong pixels = the mesh the GPU holds is not the mesh you think.
4. `upload_mesh` alignment (this skill).

**Do not** spend time on near/far planes, depth func, blend state, or
`bind_vertex_array` ordering when the object's own projected position is already
correct — those change *what survives the depth test*, not *which mesh is drawn*.

## Rust-specific traps that cost real time

- `scene.meshes.get(i).map(gpu_mesh_extent)` — `get` returns `Option<&T>`;
  `.map(gpu_mesh_extent)` where the fn takes `&T` **copies the whole mesh**.
  Use `.map(|m: &T| helper(m))`.
- A debug probe over every mesh every tick stalls the render loop and looks
  like "the page never booted". Publish once at boot, or throttle.
- Hand-written JSON debug channels: `{:?}` on `Option<T>` emits `Some([1.0, 2.0])`,
  which is not valid JSON and silently kills the whole `JSON.parse` — the page
  then looks un-booted. Write `null` explicitly.
