---
name: euv-engine-renderer-api
description: Use when adding or changing euv-engine renderer methods — WebGPU/WebGL, descriptors, readback, error scopes.
version: 1.3.0
license: MIT
metadata:
  hermes:
    related_skills: [euv, rust-standards]
---

# euv-engine renderer changes

Use for renderer contracts and backend implementations, not page CSS or Signal
reactivity. Load `rust-standards`; read the selected package's real source before
using cached API references. `engine/src/renderer/mod.rs` routes to backend,
descriptor and status modules; do not assume a flat `renderer/impl.rs` exists.
## Index

§1 Shared renderer contract · §2 Lombok getter shape · §3 Public API belongs on the owning type · §4 WebGPU upload and binding contract · §5 Refactoring safety


## 1. Shared renderer contract

1. Locate the owning backend, descriptor, status and current call sites. Compare
   the exact signatures on WebGPU and WebGL, including typed enums, offsets,
   default/optional fields and error behavior; do not guess from method names.
2. Reuse existing types (`Color`, descriptors and typed operations). Extend the
   smallest existing abstraction rather than add a synonymous type or a long
   positional parameter list. Omit optional JavaScript fields only when the
   selected API's semantics require it; zero is not universally equivalent to absent.
3. Propagate device/promise/map errors through the public contract and handle
   them at callers. A launched async task or an ignored result is not a completed
   readback. Await the appropriate boundary and keep the wasm executor unblocked.
4. Verify backend parity by behavior. Explicitly report an unsupported backend
   instead of pretending a stub has equivalent behavior.
5. For readback, validate byte offsets, requested range, usage/map flags, row
   alignment and returned byte length. Test actual data, not only allocation or
   a fulfilled promise; unmap/release owned GPU resources on failure as well.

## 2. Lombok getter shape

Inspect the exact field attributes, derive mode and generated accessor before
assuming a getter returns a reference, copied scalar or cloned value. Bare
`#[get]` can expose an accessor beyond field visibility; do not infer its
visibility solely from the field or widen it for an integration test.

When source search cannot see a generated public method, use expanded/generated
API output rather than invent a wrapper. Preserve externally consumed APIs and
use the governing visibility verifier plus `cargo check --workspace --all-targets`
to validate narrowing. A local lack of callers does not prove an exported API dead.

## 3. Public API belongs on the owning type

Place methods on the type that owns the data. A free function is externally
visible only through its actual visibility and export path: inspect each relevant
`mod.rs`/crate-root re-export, not just `grep '^pub fn'`. A namespace-only wrapper
is not automatically a better design.

Before removing or merging a type/function, establish its public contract,
downstream use, generated consumers and tests. Preserve unique behavior and
search old names in code, docs, shaders and examples. Do not delete merely because
only its definition/impl appears in one repository.

## 4. WebGPU upload and binding contract

`write_texture` sizes the copy from the **destination texture**, never from the
byte stride or the payload length. `texture_write_extent` reads the texture's
`width`/`height`/`depthOrArrayLayers` and `mipLevelCount`, shrinks the spatial
axes by the selected mip level, keeps 2D array-layer counts unshrunk, subtracts
the origin, and returns `None` for an invalid dimension, an out-of-range mip or an
origin past the edge — an invalid upload is skipped, not submitted. Never
recompute the extent from `bytes_per_row`; a stride is a byte count, not a texel
width, and the two disagree on every padded row.

`bytes_per_row` and `rows_per_image` are byte/row strides that include padding.
No 256-byte alignment is required by `queue.writeTexture`. A zero stride omits
the optional field instead of sending `0`; a multi-image upload needs a positive
`rows_per_image`.

`flip_y` on `TextureWriteDescriptor` is retained for compatibility and **performs
no transformation** — raw-byte uploads keep the source row order, so a caller
that needs a vertical flip must flip the bytes itself.

A bind group entry's `resource` is the texture view or sampler **itself**, not a
`{ textureView: … }` / `{ sampler: … }` wrapper; only a buffer entry is a
`{ buffer, … }` object. The wrapper shape produced a resource the browser
rejected at bind-group creation.

## 5. Refactoring safety

- Split parallel edits by disjoint files and freeze ownership; keep every caller
  compiling while declarations change. Never silently overwrite another agent's work.
- Use a Rust parser for source transformations; raw-string shader contents must
  not be altered by a textual visibility/rename sweep.
- Test ordinary, boundary and failure cases on the correct backend. Bind visual
  evidence to the actual binary/build and visible page; headless throttling or a
  hidden tab is not proof a GPU algorithm failed.
- Publishable code changes bump only the root `Cargo.toml` version; CI owns
  dependency/member synchronization. No manual dependency version edits.

## Verification

Run the selected repository's full required gates, including the public API
surface, macro-aware formatting and tests. For renderer changes include:

```bash
cargo check -p euv-engine --target wasm32-unknown-unknown
cargo check -p euv-example --target wasm32-unknown-unknown
cargo clippy -p euv-engine --all-targets --target wasm32-unknown-unknown
crate fmt --check
cargo test -p euv-engine
```

**CI does not run the engine's wasm suites.** `engine/tests/webgpu_regressions/`
is gated on `#[cfg(target_arch = "wasm32")]`, and the workflow's wasm step runs
`wasm-pack test --node` from the `ui/` directory only — so a WebGPU change can
pass CI without any of that regression running. Run the wasm tests locally in
`engine/` (`wasm-pack test --node`) before trusting a green build.

Exercise the changed GPU path in a real browser and assert data/frame results;
compiler success is not render parity. Register every temporary browser/tab,
server, process and GPU allocation, then release and read back their exact state
on success, failure, timeout and cancellation. Do not close borrowed resources.
