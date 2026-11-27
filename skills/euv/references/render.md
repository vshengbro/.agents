# Rendering: modes, backends and parity

Source: `core/src/render/` at `origin/master` (`aac1c450d6e8317c50c01dd6225dea7a29265495`, version 0.39.1).
Re-verified against `origin/master` (`6ccb8599`, euv 0.43.0) on 2026-11-27: every declared API name below still resolves in that tree.

`Renderer` owns one software, one hardware and one hybrid pipeline plus a
reusable `DisplayList`, and resolves `RenderMode::Auto` to a concrete
`GraphicsBackend` at startup.

## `RenderMode`

| mode | pipeline |
|---|---|
| `Auto` (default) | hardware GPU when available, falling back through `Hybrid` to `Software` |
| `Software` | analytical SDF tile rasterizer, dirty-rect damage tracking, deterministic pixel hashing, zero GPU |
| `Hardware` | instanced quad/SDF/glyph batching emitting WGSL, MSL, GLSL or HLSL |
| `Hybrid` | CPU vector rasterization composited by GPU textured quads |

Switch at runtime with `app.set_render_mode(mode)` or by queueing
`WindowCommand::SetRenderMode`. `RenderConfig` has `software()`, `hardware()`,
`hybrid()` and `default()` constructors and carries `hdr` plus the present /
AA / color-space policies (`PresentMode::{VSync, Immediate, Mailbox}`,
`AntialiasingMode::{None, AnalyticalSdf, Msaa4x, Ssaa2x}`,
`ColorSpace::{Srgb, DisplayP3, Linear}`).

## `GraphicsBackend`

`SoftwareCpu`, `Metal`, `Vulkan`, `Direct3D12`, `Direct3D11`, `OpenGlEs`,
`WebGpu`, `WebGl2`, `Canvas2d`, `Headless`.

## Frame loop

`App` drives the loop; there is no hidden scheduler:

- `step_frame() -> Result<FrameStats, PlatformError>` — one UI frame.
- `step_game_frame(dt_secs)` — fixed-timestep game frame (polls `InputState`,
  advances `FrameClock`, forwards OS input to attached `GameEngineHost`s).
- `run_frames(Some(n))` — n frames then stop; `run_frames(None)` runs until
  `get_running()` is false.
- `set_fps_limit(Option<u32>)` / `fps_limit()` — cap the loop; skip rendering
  entirely when the scene revision is unchanged (`last_rendered_revision`).

`FrameStats` reports `frame_index`, `active_mode`, `active_backend`,
`layout_nodes`, `layout_skipped`, `draw_commands`, `draw_batches`,
`pixels_shaded` and `frame_hash` (64-bit FNV-1a over the framebuffer when
software/readback is active).

## Pixel parity

`frame_hash` is **bit-identical across all seven platforms** for the same
scene, which is what makes the headless path a real test: run
`cargo run -p euv-example -- --headless --software` and compare hashes between
platforms instead of eyeballing screenshots. `Renderer.compute_pixel_hash` is
enabled for headless parity runs. The showcase can also dump raw RGBA frames
plus a manifest (`--capture-dir <dir>`).

## Custom drawing

`canvas { painter: |bounds: Rect, dl: &mut DisplayList| { … } }` — or
`ctx.create_canvas(style, painter)` — hands the node a closure that appends
vector commands to a `DisplayList`; the node is rasterized by whichever
pipeline is active, so one painter works on Metal, D3D12, Vulkan, GLES, WebGPU,
WebGL2 and Canvas2D.
