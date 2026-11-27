# Platforms, window and OS integration

Source: `core/src/platform/`, `core/src/window/`, `core/src/system/` at
`origin/master` (`aac1c450d6e8317c50c01dd6225dea7a29265495`, version 0.39.1).
Re-verified against `origin/master` (`6ccb8599`, euv 0.43.0) on 2026-11-27: every declared API name below still resolves in that tree.

euv talks to the OS **directly** — no WebView, no browser shell, no Tauri. One
`euv-core` runtime compiles for all seven targets and swaps only the
`PlatformBackend` implementation.

## `PlatformKind` and the backends

| `PlatformKind` | triple | backend / API |
|---|---|---|
| `Web` | `wasm32-unknown-unknown` | DOM Canvas 2D / WebGPU / WebGL2 via `web-sys` |
| `Android` | `aarch64-linux-android` | NDK `ANativeWindow` + `AInput`, Vulkan / GLES |
| `Ios` | `aarch64-apple-ios` | `libobjc` + UIKit, Metal |
| `IpadOs` | `aarch64-apple-ios` | UIKit + Stage Manager / Apple Pencil, Metal |
| `MacOs` | `aarch64-apple-darwin`, `x86_64-apple-darwin` | `libobjc` + AppKit `NSWindow`, CoreGraphics, `CAMetalLayer` |
| `Windows` | `x86_64-pc-windows-msvc`, `aarch64-pc-windows-msvc` | Win32 `user32`/`gdi32`/`kernel32`, Direct3D 12/11 |
| `Linux` | `x86_64-unknown-linux-gnu`, `aarch64-unknown-linux-gnu` | runtime `dlopen` of Wayland and X11, Vulkan / OpenGL |
| `Headless` | any | deterministic offscreen surface for parity tests and benchmarks |

`DeviceFormFactor` (`Desktop`, `Tablet`, `Phone`, `Browser`, `Headless`) drives
adaptive layout; on iPadOS the UIKit idiom is detected through
`UIDevice.userInterfaceIdiom`.

## Window handles

`App::raw_window_handle()` returns a `RawWindowHandle` — `AppKit { ns_window,
ns_view, metal_layer }`, `UiKit { ui_window, ui_view, metal_layer, is_ipad }`,
`Win32 { hwnd, hinstance }`, `Xlib { window, display }`, `Wayland { surface,
display }`, `AndroidNdk { native_window }`, `WebCanvas { canvas_id }` or
`Headless`. It exists so a caller can create its own GPU surface; it is **not**
a raw-window-handle crate dependency.

## `AppConfig` / `WindowConfig` / `WindowState`

```rust
let mut window: WindowConfig = WindowConfig::default();
window
    .set_title("Hello euv".to_string())
    .set_size(1024, 720)
    .set_render(RenderConfig::default());
let mut config: AppConfig = AppConfig::default();
config.set_window(window);
let mut app: App = App::new(config)?;          // native host backend
let mut app: App = App::headless(config)?;     // deterministic offscreen
let mut app: App = App::with_platform(config, Box::new(HeadlessPlatform::emulating(
    PlatformKind::Android, 1.0, SafeAreaInsets::default(),
)))?;                                          // emulate another platform
```

`WindowConfig` carries `title`, `width`/`height`, `min_size`/`max_size`,
`position`, `resizable`, `decorations`, `transparent`, `always_on_top`,
`fullscreen: FullscreenMode`, `immersive`, `visible`, `render: RenderConfig`,
`orientation: OrientationLock`, `status_bar: StatusBarStyle`,
`preferred_theme: Option<ThemeMode>`, `icon`/`icon_path`. Setters are generated
by `lombok-macros` and return `&mut Self` for chaining.

`App` exposes live state through the same generated getters:
`get_window_state()`, `platform_kind()`, `platform_capabilities()`,
`get_running()`, `get_last_rendered_revision()`, `get_deep_link()`,
`get_scene()`, `get_renderer()`, `get_context()`, `get_input_state()`.

## Imperative window commands

`App::queue_window_command(WindowCommand)` defers OS work to the frame loop
(never mutate the OS window from inside a render closure):

`SetTitle`, `SetSize`, `SetPosition`, `SetResizable`, `SetDecorations`,
`SetAlwaysOnTop`, `SetFullscreen`, `SetVisible`, `SetCursor`, `SetIme`,
`SetStatusBarStyle`, `RequestRedraw`, `SetRenderMode`, `Close` — each takes the
target `WindowId`.

## Services and system integration

`core/src/system/` holds `a11y` (`A11yTree`, `A11yProps`, `A11yRole`),
`capabilities`, `permissions` and `protocol` (custom scheme / universal link
registration). `App::a11y_tree()` snapshots the semantic tree, and incoming
deep links arrive on the `deep_link` signal.

`PlatformServiceHub` covers the platform-native extras: Dynamic Island,
haptics, tray, protocol registration and permission prompts.

## Safe areas and DPI

`SafeAreaInsets` and `DisplayInfo` ride on `WindowState`; `euv-ui`'s
`use_window()` hook returns `(Signal<SafeAreaInsets>, Signal<ThemeMode>)` so a
view can pad itself without reading the platform directly. DPI scaling is
applied by the layout engine — pass **logical** pixels to `set_size`.
