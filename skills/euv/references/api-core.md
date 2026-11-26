# euv-core full pub API

Source: `core/src/` at `origin/master` (`aac1c450d6e8317c50c01dd6225dea7a29265495`, version 0.39.1), extracted from
`pub` declarations in the committed tree.

`euv-core` is re-exported at the `euv` crate root (`pub use {euv_core::*,
euv_macros::*}` in `src/lib.rs`), so every item below is reachable as
`euv::<name>`. `euv-core` itself depends only on `serde`, `serde_json`,
`lombok-macros` and (on wasm) `js-sys`/`web-sys`/`wasm-bindgen`.

Top-level modules: `app`, `dynamic`, `font`, `game`, `layout`, `media`,
`platform`, `reactive`, `render`, `scene`, `style`, `system`, `window`.

There is no `fetch` module any more: network access is not part of the core
runtime, and the wasm-only `web-sys` surface is limited to the platform,
render and font backends.

### app
- (mod) pub use {router::*, runner::*, service::*};

### app::router
- (const) pub const DEFAULT_ROUTE_PATH: &str = "/";
- (impl) pub fn at(initial_path: String) -> Self {
- (impl) pub fn path(&self) -> String {
- (impl) pub fn push(&mut self, path: String) {
- (impl) pub fn back(&mut self) -> bool {
- (impl) pub fn forward(&mut self) -> bool {
- (impl) pub fn can_go_back(&self) -> bool {
- (mod) pub use {r#const::*, r#struct::*};
- (struct) pub struct Router {

### app::runner
- (impl) pub fn new(config: AppConfig) -> Result<Self, PlatformError> {
- (impl) pub fn headless(config: AppConfig) -> Result<Self, PlatformError> {
- (impl) pub fn with_platform( config: AppConfig, mut platform: Box<dyn PlatformBackend>, ) -> Result<Self, PlatformError> {
- (impl) pub fn set_fps_limit(&mut self, limit: Option<u32>) {
- (impl) pub fn fps_limit(&self) -> Option<u32> {
- (impl) pub fn attach_game_host(&mut self, host: GameEngineHost) {
- (impl) pub fn has_active_animations(&self) -> bool {
- (impl) pub fn mount<F, M>(&mut self, builder: F) -> NodeId where F: FnOnce() -> M, M: Mountable, {
- (impl) pub fn platform_kind(&self) -> PlatformKind {
- (impl) pub fn platform_capabilities(&self) -> PlatformCapabilities {
- (impl) pub fn raw_window_handle(&self) -> RawWindowHandle {
- (impl) pub fn a11y_tree(&self) -> A11yTree {
- (impl) pub fn set_render_mode(&mut self, mode: RenderMode) {
- (impl) pub fn queue_window_command(&mut self, command: WindowCommand) {
- (impl) pub fn set_exact_physical_viewport(&mut self, phys_w: u32, phys_h: u32, scale: f32) {
- (impl) pub fn dispatch_window_event(&mut self, event: WindowEvent) {
- (impl) pub fn step_frame(&mut self) -> Result<FrameStats, PlatformError> {
- (impl) pub fn step_game_frame(&mut self, dt_secs: f32) -> Result<FrameStats, PlatformError> {
- (impl) pub fn run_frames(&mut self, max_frames: Option<u64>) -> Result<FrameStats, PlatformError> {
- (impl) pub fn cancel_all_active_pointers(&mut self) {
- (impl) pub fn reconcile_active_touch_ids(&mut self, live_ids: &[u64]) {
- (mod) pub use r#struct::*;
- (struct) pub struct AppConfig {
- (struct) pub struct App {

### app::service
- (impl) pub fn set_item(&mut self, key: String, value: String) {
- (impl) pub fn get_item(&self, key: &str) -> Option<String> {
- (impl) pub fn remove_item(&mut self, key: &str) -> Option<String> {
- (impl) pub fn len(&self) -> usize {
- (impl) pub fn is_empty(&self) -> bool {
- (mod) pub use r#struct::*;
- (struct) pub struct StorageStore {

### dynamic::hub
- (const) pub const DYNAMIC_CARD_BG_HEX: u32 = 0xFFFFFF;
- (const) pub const DYNAMIC_CARD_BORDER_HEX: u32 = 0xE2E8F0;
- (const) pub const DYNAMIC_BUTTON_BG_HEX: u32 = 0x2563EB;
- (const) pub const DYNAMIC_BUTTON_FG_HEX: u32 = 0xFFFFFF;
- (const) pub const DYNAMIC_BADGE_BG_HEX: u32 = 0xDBEAFE;
- (const) pub const DYNAMIC_BADGE_FG_HEX: u32 = 0x1D4ED8;
- (const) pub const DYNAMIC_TEXT_FG_HEX: u32 = 0x0F172A;
- (const) pub const DYNAMIC_DIVIDER_HEX: u32 = 0xCBD5E1;
- (const) pub const DYNAMIC_DEFAULT_CARD_PADDING: f32 = 16.0;
- (const) pub const DYNAMIC_DEFAULT_CARD_GAP: f32 = 10.0;
- (const) pub const DYNAMIC_DEFAULT_CARD_RADIUS: f32 = 10.0;
- (const) pub const DYNAMIC_DEFAULT_BUTTON_HEIGHT: f32 = 34.0;
- (const) pub const DYNAMIC_DEFAULT_BUTTON_RADIUS: f32 = 8.0;
- (const) pub const DYNAMIC_DEFAULT_BADGE_RADIUS: f32 = 6.0;
- (const) pub const DYNAMIC_DEFAULT_FONT_SIZE: f32 = 14.0;
- (const) pub const DYNAMIC_DEFAULT_GRID_COLUMNS: u16 = 2;
- (enum) pub enum DynamicNodeKind {
- (enum) pub enum DynamicUpdateScope {
- (enum) pub enum DynamicUpdateError {
- (fn) pub fn current_dynamic_hub() -> DynamicUpdateHub {
- (fn) pub fn normalize_dynamic_route(route: &str) -> String {
- (fn) pub fn compute_spec_checksum(spec: &DynamicNodeSpec) -> u64 {
- (fn) pub fn mount_dynamic_spec( spec: &DynamicNodeSpec, source_id: &str, hub: &DynamicUpdateHub, ) -> NodeId {
- (impl) pub fn width_px(&self) -> Option<f32> {
- (impl) pub fn height_px(&self) -> Option<f32> {
- (impl) pub fn padding_px(&self) -> Option<f32> {
- (impl) pub fn gap_px(&self) -> Option<f32> {
- (impl) pub fn radius_px(&self) -> Option<f32> {
- (impl) pub fn font_size_px(&self) -> Option<f32> {
- (impl) pub fn background_hex_value(&self) -> Option<u32> {
- (impl) pub fn color_hex_value(&self) -> Option<u32> {
- (impl) pub fn border_width_px(&self) -> Option<f32> {
- (impl) pub fn border_hex_value(&self) -> Option<u32> {
- (impl) pub fn apply_to(&self, mut base: Style) -> Style {
- (impl) pub fn column() -> Self {
- (impl) pub fn row() -> Self {
- (impl) pub fn grid(columns: u16) -> Self {
- (impl) pub fn card(title: String) -> Self {
- (impl) pub fn text(content: String) -> Self {
- (impl) pub fn button(label: String, action: String) -> Self {
- (impl) pub fn badge(label: String) -> Self {
- (impl) pub fn divider() -> Self {
- (impl) pub fn action_name(&self) -> Option<&str> {
- (impl) pub fn child(mut self, child: Self) -> Self {
- (impl) pub fn checksum(&self) -> u64 {
- (impl) pub fn sign(&mut self) -> &mut Self {
- (impl) pub fn to_json(&self) -> Result<String, DynamicUpdateError> {
- (impl) pub fn from_json(raw: &str) -> Result<Self, DynamicUpdateError> {
- (impl) pub fn sign(&mut self) -> &mut Self {
- (impl) pub fn to_json(&self) -> Result<String, DynamicUpdateError> {
- (impl) pub fn from_json(raw: &str) -> Result<Self, DynamicUpdateError> {
- (impl) pub fn push_component(mut self, update: DynamicComponentUpdate) -> Self {
- (impl) pub fn push_page(mut self, update: DynamicPageUpdate) -> Self {
- (impl) pub fn to_json(&self) -> Result<String, DynamicUpdateError> {
- (impl) pub fn from_json(raw: &str) -> Result<Self, DynamicUpdateError> {
- (impl) pub fn new() -> Self {
- (impl) pub fn apply_component( &self, update: DynamicComponentUpdate, ) -> Result<u64, DynamicUpdateError> {
- (impl) pub fn apply_component_json(&self, json: &str) -> Result<u64, DynamicUpdateError> {
- (impl) pub fn swap_component_builder<F>( &self, id: String, version: u64, builder: F, ) -> Result<u64, DynamicUpdateError> where F: Fn() -> NodeId + 'static, {
- (impl) pub fn rollback_component(&self, id: &str) -> Result<u64, DynamicUpdateError> {
- (impl) pub fn apply_page(&self, update: DynamicPageUpdate) -> Result<u64, DynamicUpdateError> {
- (impl) pub fn apply_page_json(&self, json: &str) -> Result<u64, DynamicUpdateError> {
- (impl) pub fn swap_page_builder<F>( &self, route: String, title: String, version: u64, builder: F, ) -> Result<u64, DynamicUpdateError> where F: Fn() -> NodeId + 'static, {
- (impl) pub fn rollback_page(&self, route: &str) -> Result<u64, DynamicUpdateError> {
- (impl) pub fn apply_bundle( &self, bundle: DynamicUpdateBundle, ) -> Result<DynamicTelemetry, DynamicUpdateError> {
- (impl) pub fn apply_bundle_json(&self, json: &str) -> Result<DynamicTelemetry, DynamicUpdateError> {
- (impl) pub fn on_action<F>(&self, handler: F) where F: FnMut(&DynamicActionEvent) + 'static, {
- (impl) pub fn dispatch_action(&self, event: DynamicActionEvent) {
- (impl) pub fn component_revision_signal(&self, id: &str) -> Signal<u64> {
- (impl) pub fn page_revision_signal(&self, route: &str) -> Signal<u64> {
- (impl) pub fn component_version(&self, id: &str) -> u64 {
- (impl) pub fn component_history_len(&self, id: &str) -> usize {
- (impl) pub fn page_version(&self, route: &str) -> u64 {
- (impl) pub fn page_title(&self, route: &str) -> Option<String> {
- (impl) pub fn has_dynamic_page(&self, route: &str) -> bool {
- (impl) pub fn registered_routes(&self) -> Vec<String> {
- (impl) pub fn routes_signal(&self) -> Signal<u64> {
- (impl) pub fn telemetry(&self) -> Signal<DynamicTelemetry> {
- (impl) pub fn last_action(&self) -> Signal<Option<DynamicActionEvent>> {
- (impl) pub fn mount_component_or_fallback(&self, id: &str, fallback: &DynamicBuilderFn) -> NodeId {
- (impl) pub fn mount_page_or_fallback(&self, route: &str, fallback: &DynamicBuilderFn) -> NodeId {
- (mod) pub use {r#const::*, r#enum::*, r#fn::*, r#struct::*, r#type::*};
- (struct) pub struct DynamicStyleSpec {
- (struct) pub struct DynamicNodeSpec {
- (struct) pub struct DynamicComponentUpdate {
- (struct) pub struct DynamicPageUpdate {
- (struct) pub struct DynamicUpdateBundle {
- (struct) pub struct DynamicActionEvent {
- (struct) pub struct DynamicTelemetry {
- (struct) pub struct DynamicUpdateHub {
- (struct) pub struct DynamicComponentSlot {
- (struct) pub struct DynamicPageSlot {
- (struct) pub struct DynamicPageOutlet {
- (type) pub type DynamicBuilderFn = Rc<dyn Fn() -> NodeId>;
- (type) pub type DynamicRouteFallbackFn = Rc<dyn Fn(&str) -> NodeId>;
- (type) pub type DynamicActionCallback = Rc<RefCell<dyn FnMut(&DynamicActionEvent)>>;

### dynamic
- (mod) pub use {hub::*, wasm::*};

### dynamic::wasm
- (const) pub const WASM_BINARY_MAGIC: &[u8] = &[0x00, 0x61, 0x73, 0x6D];
- (const) pub const WASM_BINARY_VERSION: &[u8] = &[0x01, 0x00, 0x00, 0x00];
- (const) pub const WASM_ABI_VERSION: u32 = 1;
- (const) pub const WASM_DEFAULT_MAX_BINARY_BYTES: usize = 8 * 1024 * 1024;
- (const) pub const WASM_DEFAULT_MAX_MEMORY_BYTES: usize = 4 * 1024 * 1024;
- (const) pub const WASM_DEFAULT_MAX_FUEL: u64 = 100_000;
- (const) pub const WASM_DEFAULT_TIMEOUT_MS: u64 = 15_000;
- (const) pub const WASM_DEFAULT_MAX_RETRIES: u32 = 2;
- (const) pub const WASM_PAGE_BYTES: usize = 65_536;
- (const) pub const WASM_EXPORT_RENDER: &str = "euv_render";
- (const) pub const WASM_EXPORT_ON_EVENT: &str = "euv_on_event";
- (const) pub const WASM_EXPORT_ABI: &str = "euv_abi_version";
- (const) pub const WASM_IMPORT_EMIT_UI: &str = "euv_emit_ui";
- (const) pub const WASM_IMPORT_EMIT_BUNDLE: &str = "euv_emit_bundle";
- (const) pub const WASM_IMPORT_LOG: &str = "euv_log";
- (const) pub const WASM_IMPORT_MODULE_ENV: &str = "env";
- (const) pub const WASM_GLOBAL_ROOT_SLOT: &str = "__euv_global_wasm_root__";
- (const) pub const WASM_CUSTOM_META_SECTION: &str = "euv.wasm.meta";
- (enum) pub enum WasmDynamicScope {
- (enum) pub enum WasmLoadState {
- (enum) pub enum WasmDynamicError {
- (enum) pub enum WasmFaultKind {
- (fn) pub fn compute_wasm_checksum(bytes: &[u8]) -> u64 {
- (fn) pub fn compute_wasm_signature(bytes: &[u8], version: u64, signing_key: &str) -> String {
- (fn) pub fn parse_wasm_binary( bytes: &[u8], config: &WasmSandboxConfig, ) -> Result<WasmParsedModule, WasmDynamicError> {
- (fn) pub fn execute_wasm_export( module: &WasmParsedModule, export_name: &str, args: &[i32], config: &WasmSandboxConfig, ) -> Result<WasmExecutionOutput, WasmDynamicError> {
- (fn) pub fn build_partial_widget_wasm(title: &str, version: u64, accent_hex: u32) -> Vec<u8> {
- (fn) pub fn build_global_app_wasm(title: &str, version: u64) -> Vec<u8> {
- (fn) pub fn build_faulty_wasm(fault: WasmFaultKind) -> Vec<u8> {
- (impl) pub fn key(&self) -> String {
- (impl) pub fn partial(url: String, slot_id: String, version: u64) -> Self {
- (impl) pub fn global(url: String, version: u64) -> Self {
- (impl) pub fn with_checksum(mut self, checksum: u64) -> Self {
- (impl) pub fn with_signature(mut self, signature: String) -> Self {
- (impl) pub fn with_allow_downgrade(mut self, allow: bool) -> Self {
- (impl) pub fn resolved_cache_key(&self) -> &str {
- (impl) pub fn emitted_spec(&self) -> Option<&DynamicNodeSpec> {
- (impl) pub fn emitted_bundle(&self) -> Option<&DynamicUpdateBundle> {
- (impl) pub fn spec_ref(&self) -> Option<&DynamicNodeSpec> {
- (impl) pub fn bundle_ref(&self) -> Option<&DynamicUpdateBundle> {
- (impl) pub fn partial_spec(spec: &DynamicNodeSpec) -> Self {
- (impl) pub fn global_bundle(bundle: &DynamicUpdateBundle) -> Self {
- (impl) pub fn with_alt_spec(mut self, alt: &DynamicNodeSpec) -> Self {
- (impl) pub fn with_alt_bundle(mut self, bundle: &DynamicUpdateBundle) -> Self {
- (impl) pub fn with_log(mut self, message: String) -> Self {
- (impl) pub fn with_abi_version(mut self, abi: u32) -> Self {
- (impl) pub fn without_render_export(mut self) -> Self {
- (impl) pub fn with_fault(mut self, fault: WasmFaultKind) -> Self {
- (impl) pub fn build(&self) -> Vec<u8> {
- (impl) pub fn register(&self, url: String, bytes: Vec<u8>, etag: String, fault: WasmFaultKind) {
- (impl) pub fn set_offline(&self, is_offline: bool) {
- (impl) pub fn is_offline(&self) -> bool {
- (impl) pub fn new( hub: DynamicUpdateHub, fetcher: Rc<dyn WasmFetcher>, config: WasmSandboxConfig, ) -> Self {
- (impl) pub fn state_signal(&self, scope: &WasmDynamicScope) -> Signal<WasmLoadState> {
- (impl) pub fn global_version_signal(&self) -> Signal<u64> {
- (impl) pub fn telemetry(&self) -> Signal<WasmDynamicTelemetry> {
- (impl) pub fn last_logs(&self) -> Signal<Vec<String>> {
- (impl) pub fn cache_len(&self) -> usize {
- (impl) pub fn cancel_scope(&self, scope: &WasmDynamicScope) -> u64 {
- (impl) pub fn load_and_mount( &self, request: WasmDownloadRequest, signing_key: &str, ) -> Result<u64, WasmDynamicError> {
- (impl) pub fn dispatch_wasm_event( &self, scope: &WasmDynamicScope, action_code: i32, ) -> Result<i32, WasmDynamicError> {
- (impl) pub fn rollback_partial(&self, slot_id: &str, reason: &str) -> Result<u64, WasmDynamicError> {
- (impl) pub fn unmount_partial(&self, slot_id: &str) {
- (impl) pub fn rollback_global(&self, reason: &str) -> Result<u64, WasmDynamicError> {
- (impl) pub fn restore_native_global(&self) {
- (mod) pub use {r#const::*, r#enum::*, r#fn::*, r#struct::*, r#trait::*};
- (struct) pub struct WasmSandboxConfig {
- (struct) pub struct WasmDownloadRequest {
- (struct) pub struct WasmFetchedPayload {
- (struct) pub struct WasmFuncSignature {
- (struct) pub struct WasmImportEntry {
- (struct) pub struct WasmDataSegment {
- (struct) pub struct WasmParsedFunction {
- (struct) pub struct WasmParsedModule {
- (struct) pub struct WasmExecutionOutput {
- (struct) pub struct WasmCachedEntry {
- (struct) pub struct WasmMountedSnapshot {
- (struct) pub struct WasmDynamicTelemetry {
- (struct) pub struct RegistryWasmRecord {
- (struct) pub struct RegistryWasmFetcher {
- (struct) pub struct HttpWasmFetcher {
- (struct) pub struct WasmDynamicManager {
- (struct) pub struct WasmModuleBuilder {
- (trait) pub trait WasmFetcher {

### font::atlas
- (impl) pub fn get_or_rasterize(&mut self, key: GlyphKey) -> &RasterizedGlyph {
- (impl) pub fn len(&self) -> usize {
- (impl) pub fn is_empty(&self) -> bool {
- (impl) pub fn get_or_rasterize_with( &mut self, key: GlyphKey, provider: &dyn SystemFontProvider, ) -> &RasterizedGlyph {
- (impl) pub fn pack_rgba_atlas(&self) -> PackedGlyphAtlas {
- (impl) pub fn clear(&mut self) {
- (mod) pub use r#struct::*;
- (struct) pub struct GlyphAtlas {

### font::glyph
- (const) pub const BITMAP_GLYPH_WIDTH: usize = 5;
- (const) pub const BITMAP_GLYPH_HEIGHT: usize = 7;
- (const) pub const PROPORTIONAL_ADVANCE_RATIO: f32 = 0.58;
- (const) pub const MONOSPACE_ADVANCE_RATIO: f32 = 0.62;
- (fn) pub fn glyph_bitmap_rows(ch: char) -> [u8; BITMAP_GLYPH_HEIGHT] {
- (fn) pub fn measure_char_advance(ch: char, style: TextStyle) -> f32 {
- (fn) pub fn rasterize_glyph(key: GlyphKey) -> RasterizedGlyph {
- (impl) pub fn from_style(codepoint: char, physical_size: f32, weight: FontWeight) -> Self {
- (mod) pub use {r#const::*, r#fn::*, r#struct::*};
- (struct) pub struct GlyphKey {
- (struct) pub struct RasterizedGlyph {

### font::measurer
- (mod) pub use {r#struct::*, r#trait::*};
- (struct) pub struct TextLine {
- (struct) pub struct TextLayoutResult {
- (struct) pub struct DeterministicTextMeasurer;
- (trait) pub trait TextMeasurer {

### font
- (mod) pub use {atlas::*, glyph::*, measurer::*, system::*};

### font::system
- (const) pub const FONT_FAMILY_DETERMINISTIC: &str = "euv-deterministic";
- (const) pub const FONT_FAMILY_APPLE_SYSTEM: &str = "SF Pro / PingFang SC";
- (const) pub const FONT_FAMILY_WINDOWS_SYSTEM: &str = "Segoe UI / Microsoft YaHei";
- (const) pub const FONT_FAMILY_LINUX_SYSTEM: &str = "DejaVu Sans / Noto Sans";
- (const) pub const FONT_FAMILY_ANDROID_SYSTEM: &str = "Roboto / Noto Sans CJK";
- (const) pub const FONT_FAMILY_WEB_SYSTEM: &str = "Inter, -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, sans-serif";
- (enum) pub enum FontRenderBackend {
- (fn) pub fn is_wide_unicode(ch: char) -> bool {
- (fn) pub fn rasterize_unicode_deterministic(key: GlyphKey) -> RasterizedGlyph {
- (fn) pub fn probe_system_font() -> SystemFontInfo {
- (fn) pub fn register_external_glyph_rasterizer(rasterizer: ExternalGlyphRasterizer) {
- (fn) pub fn rasterize_native_glyph(key: GlyphKey) -> Option<RasterizedGlyph> {
- (impl) pub fn system() -> Self {
- (impl) pub fn deterministic() -> Self {
- (mod) pub use {r#const::*, r#enum::*, r#fn::*, r#struct::*, r#trait::*, r#type::*};
- (struct) pub struct SystemFontInfo {
- (struct) pub struct NativeSystemFont {
- (struct) pub struct PackedGlyphAtlas {
- (trait) pub trait SystemFontProvider {
- (type) pub type ExternalGlyphRasterizer = fn(GlyphKey) -> Option<RasterizedGlyph>;

### game::audio
- (enum) pub enum SoundCue {
- (impl) pub fn play(&mut self, cue: SoundCue, volume: f32, pan: f32, pitch: f32) {
- (impl) pub fn drain(&mut self) -> Vec<AudioCommand> {
- (impl) pub fn play_spatial_3d(&mut self, listener: &AudioListener3D, source: &SpatialAudioSource3D) {
- (impl) pub fn from_camera(camera: &Camera3D, velocity: Vec3) -> Self {
- (impl) pub fn new(cue: SoundCue, position: Vec3) -> Self {
- (impl) pub fn with_velocity(mut self, velocity: Vec3) -> Self {
- (impl) pub fn with_range(mut self, volume: f32, min_distance: f32, max_distance: f32) -> Self {
- (mod) pub use {r#enum::*, r#struct::*};
- (struct) pub struct AudioCommand {
- (struct) pub struct AudioBus {
- (struct) pub struct AudioListener3D {
- (struct) pub struct SpatialAudioSource3D {

### game::camera
- (impl) pub fn at(center: Point, zoom: f32) -> Self {
- (impl) pub fn add_trauma(&mut self, amount: f32) {
- (impl) pub fn follow(&mut self, target: Point, responsiveness: f32, dt_secs: f32, viewport: Size) {
- (impl) pub fn shake_offset(&self) -> Point {
- (impl) pub fn world_to_screen(&self, world: Point, viewport: Size) -> Point {
- (impl) pub fn screen_to_world(&self, screen: Point, viewport: Size) -> Point {
- (impl) pub fn visible_world_rect(&self, viewport: Size) -> Rect {
- (mod) pub use r#struct::*;
- (struct) pub struct Camera2D {

### game::clock
- (impl) pub fn tick(&mut self, raw_dt_secs: f32) -> u32 {
- (mod) pub use r#struct::*;
- (struct) pub struct FrameClock {

### game::ecs
- (enum) pub enum BodyKind {
- (enum) pub enum ColliderShape {
- (enum) pub enum EntityVisualShape {
- (enum) pub enum EntityTag {
- (impl) pub fn dynamic(mass: f32, restitution: f32, linear_drag: f32) -> Self {
- (impl) pub fn static_body(restitution: f32) -> Self {
- (impl) pub fn kinematic() -> Self {
- (impl) pub fn circle(radius: f32, layer: u32, mask: u32, is_trigger: bool) -> Self {
- (impl) pub fn aabb(width: f32, height: f32, layer: u32, mask: u32, is_trigger: bool) -> Self {
- (impl) pub fn world_aabb(&self, center: Point) -> Rect {
- (impl) pub fn body_component(&self) -> Option<RigidBody2D> {
- (impl) pub fn collider_component(&self) -> Option<Collider2D> {
- (impl) pub fn sprite_component(&self) -> Option<Sprite2D> {
- (impl) pub fn ttl_value(&self) -> Option<f32> {
- (impl) pub fn world_bounds(&self) -> Rect {
- (impl) pub fn with_capacity(capacity: usize) -> Self {
- (impl) pub fn spawn(&mut self, tag: EntityTag, position: Point) -> EntityId {
- (impl) pub fn despawn(&mut self, id: EntityId) -> bool {
- (impl) pub fn is_alive(&self, id: EntityId) -> bool {
- (impl) pub fn get_entity(&self, id: EntityId) -> Option<&EntityRecord> {
- (impl) pub fn get_entity_mut(&mut self, id: EntityId) -> Option<&mut EntityRecord> {
- (impl) pub fn tick_lifetimes(&mut self, dt_secs: f32) -> usize {
- (impl) pub fn clear(&mut self) {
- (impl) pub fn count_by_tag(&self, tag: EntityTag) -> usize {
- (mod) pub use {r#enum::*, r#struct::*};
- (struct) pub struct EntityId {
- (struct) pub struct EntityTransform {
- (struct) pub struct Velocity2D {
- (struct) pub struct RigidBody2D {
- (struct) pub struct Collider2D {
- (struct) pub struct Sprite2D {
- (struct) pub struct EntityRecord {
- (struct) pub struct GameWorld {

### game::engine3d::animation
- (impl) pub fn new(name: &str, parent: Option<usize>, rest_transform: Transform3D) -> Self {
- (impl) pub fn parent_index(&self) -> Option<usize> {
- (impl) pub fn new(joint_index: usize, mut keyframes: Vec<Keyframe3D>) -> Self {
- (impl) pub fn sample(&self, time_secs: f32, fallback: Transform3D) -> Transform3D {
- (impl) pub fn new(name: &str, duration_secs: f32, looping: bool) -> Self {
- (impl) pub fn with_track(mut self, track: JointTrack3D) -> Self {
- (impl) pub fn normalize_time(&self, time_secs: f32) -> f32 {
- (impl) pub fn add_joint( &mut self, name: &str, parent: Option<usize>, rest_transform: Transform3D, ) -> usize {
- (impl) pub fn sample_world_matrices( &self, clip: &AnimationClip3D, time_secs: f32, root_world: Transform3D, ) -> Vec<Mat4> {
- (mod) pub use r#struct::*;
- (struct) pub struct Keyframe3D {
- (struct) pub struct SkeletonJoint3D {
- (struct) pub struct JointTrack3D {
- (struct) pub struct AnimationClip3D {
- (struct) pub struct SkeletonRig3D {

### game::engine3d::bvh
- (impl) pub fn from_points(v0: Vec3, v1: Vec3, v2: Vec3, material: PbrMaterial) -> Self {
- (impl) pub fn intersect(&self, ray: &Ray3D, t_min: f32, t_max: f32) -> Option<f32> {
- (impl) pub fn build(triangles: Vec<BvhTriangle>) -> Self {
- (impl) pub fn trace_any_shadow_cached( &self, origin: Vec3, dir: Vec3, inv_dir: Vec3, t_min: f32, t_max: f32, cached_tri: &mut u32, ) -> bool {
- (impl) pub fn trace_any_shadow(&self, ray: &Ray3D, t_min: f32, t_max: f32) -> bool {
- (impl) pub fn trace_closest_raw( &self, origin: Vec3, dir: Vec3, inv_dir: Vec3, t_min: f32, t_max: f32, ) -> Option<(f32, usize)> {
- (impl) pub fn trace_closest(&self, ray: &Ray3D, t_min: f32, t_max: f32) -> Option<RayHit3D> {
- (mod) pub use r#struct::*;
- (struct) pub struct BvhTriangle {
- (struct) pub struct BvhNode3D {
- (struct) pub struct RayHit3D {
- (struct) pub struct Bvh3D {

### game::engine3d::math
- (impl) pub const fn zero() -> Self {
- (impl) pub const fn splat(v: f32) -> Self {
- (impl) pub fn scale(self, s: f32) -> Self {
- (impl) pub fn dot(self, rhs: Self) -> f32 {
- (impl) pub fn cross(self, rhs: Self) -> Self {
- (impl) pub fn length_sq(self) -> f32 {
- (impl) pub fn length(self) -> f32 {
- (impl) pub fn normalize(self) -> Self {
- (impl) pub fn lerp(self, other: Self, t: f32) -> Self {
- (impl) pub fn reflect(self, normal: Self) -> Self {
- (impl) pub fn min(self, rhs: Self) -> Self {
- (impl) pub fn max(self, rhs: Self) -> Self {
- (impl) pub fn from_color(c: Color) -> Self {
- (impl) pub fn to_aces_rgba8(self) -> [u8; 4] {
- (impl) pub const fn identity() -> Self {
- (impl) pub fn perspective(fov_rad: f32, aspect: f32, near: f32, far: f32) -> Self {
- (impl) pub fn look_at(eye: Vec3, target: Vec3, up: Vec3) -> Self {
- (impl) pub fn from_trs(position: Vec3, yaw_rad: f32, scale: Vec3) -> Self {
- (impl) pub fn from_trs_euler( position: Vec3, yaw_rad: f32, pitch_rad: f32, roll_rad: f32, scale: Vec3, ) -> Self {
- (impl) pub fn mul_point4(&self, p: Vec3) -> [f32; 4] {
- (impl) pub const fn empty() -> Self {
- (impl) pub fn expand_point(&mut self, point: Vec3) {
- (impl) pub fn expand_box(&mut self, other: Self) {
- (impl) pub fn center(&self) -> Vec3 {
- (impl) pub fn radius(&self) -> f32 {
- (impl) pub fn surface_area(&self) -> f32 {
- (impl) pub fn intersect_ray_near(&self, origin: Vec3, inv_dir: Vec3, t_min: f32, t_max: f32) -> f32 {
- (impl) pub fn intersects_ray(&self, ray: &Ray3D, t_min: f32, t_max: f32) -> bool {
- (impl) pub fn safe_inv_vec(dir: Vec3) -> Vec3 {
- (impl) pub fn new(origin: Vec3, direction: Vec3) -> Self {
- (impl) pub fn from_view_proj(vp: &Mat4) -> Self {
- (impl) pub fn intersects_aabb(&self, aabb: &Aabb3D) -> bool {
- (impl) pub fn forward(&self) -> Vec3 {
- (impl) pub fn right(&self) -> Vec3 {
- (impl) pub fn focal_length_to_fov_deg(focal_length_mm: f32, sensor_height_mm: f32) -> f32 {
- (impl) pub fn from_lens(position: Vec3, yaw: f32, pitch: f32, focal_length_mm: f32) -> Self {
- (impl) pub fn ev100(aperture_fstop: f32, shutter_seconds: f32, iso: f32) -> f32 {
- (impl) pub fn exposure_scale_from_ev100(ev100: f32) -> f32 {
- (impl) pub fn look_at(&mut self, target: Vec3) {
- (impl) pub fn view_projection(&self, aspect: f32) -> Mat4 {
- (mod) pub use r#struct::*;
- (struct) pub struct Vec3 {
- (struct) pub struct Mat4 {
- (struct) pub struct Aabb3D {
- (struct) pub struct Ray3D {
- (struct) pub struct Frustum3D {
- (struct) pub struct Camera3D {

### game::engine3d::mesh
- (enum) pub enum ModelFormat {
- (enum) pub enum SurfaceDetailMode {
- (impl) pub fn pbr(color: Color, metallic: f32, roughness: f32, reflectivity: f32) -> Self {
- (impl) pub fn metallic(color: Color, roughness: f32) -> Self {
- (impl) pub fn dielectric(color: Color, roughness: f32) -> Self {
- (impl) pub fn glass(color: Color, roughness: f32) -> Self {
- (impl) pub fn neon(color: Color, intensity: f32) -> Self {
- (impl) pub fn with_emissive(mut self, emissive: Vec3) -> Self {
- (impl) pub fn with_roughness(mut self, roughness: f32) -> Self {
- (impl) pub fn with_metallic(mut self, metallic: f32) -> Self {
- (impl) pub fn with_reflectivity(mut self, reflectivity: f32) -> Self {
- (impl) pub fn with_surface_detail(mut self, mode: SurfaceDetailMode) -> Self {
- (impl) pub fn new(name: &str, size: Vec3) -> Self {
- (impl) pub fn with_ground_pivot(mut self, ground_pivot: bool) -> Self {
- (impl) pub fn with_material(mut self, material: PbrMaterial) -> Self {
- (impl) pub fn new(name: &str, width: f32, depth: f32) -> Self {
- (impl) pub fn with_subdivisions(mut self, subdivisions: usize) -> Self {
- (impl) pub fn with_material(mut self, material: PbrMaterial) -> Self {
- (impl) pub fn build_meshlets_from_parts( vertices: &[Vertex3D], indices: &[[u32; 3]], ) -> Vec<Meshlet3D> {
- (impl) pub fn from_parts( name: String, vertices: Vec<Vertex3D>, indices: Vec<[u32; 3]>, material: PbrMaterial, ) -> Self {
- (impl) pub fn box_mesh( name: &str, w: f32, h: f32, d: f32, ground_pivot: bool, material: PbrMaterial, ) -> Self {
- (impl) pub fn ground_plane( name: &str, w: f32, d: f32, subdivisions: usize, material: PbrMaterial, ) -> Self {
- (impl) pub fn sports_car(name: &str, material: PbrMaterial) -> Self {
- (impl) pub fn from_box_desc(desc: &BoxMeshDesc) -> Self {
- (impl) pub fn from_ground_desc(desc: &GroundPlaneDesc) -> Self {
- (impl) pub fn build_lod_proxy(&self, suffix: &str) -> Self {
- (impl) pub fn build_mid_lod(&self, suffix: &str) -> Self {
- (impl) pub fn from_mesh(mesh: Mesh3D) -> Self {
- (impl) pub fn select(&self, distance: f32, lod_bias: f32) -> (&Mesh3D, usize) {
- (impl) pub fn select_screen_error( &self, distance: f32, bounds_radius: f32, focal_px: f32, lod_bias: f32, ) -> (&Mesh3D, usize) {
- (impl) pub fn import( format: ModelFormat, source: &str, fallback_material: PbrMaterial, ) -> Result<ImportedModel3D, String> {
- (impl) pub fn parse_obj(source: &str, material: PbrMaterial) -> Result<ImportedModel3D, String> {
- (impl) pub fn parse_gltf_json( source: &str, fallback_material: PbrMaterial, ) -> Result<ImportedModel3D, String> {
- (mod) pub use {r#enum::*, r#struct::*};
- (struct) pub struct Vertex3D {
- (struct) pub struct PbrMaterial {
- (struct) pub struct BoxMeshDesc {
- (struct) pub struct GroundPlaneDesc {
- (struct) pub struct Meshlet3D {
- (struct) pub struct Mesh3D {
- (struct) pub struct MeshLodChain {
- (struct) pub struct ImportedModel3D {
- (struct) pub struct ModelImporter3D;

### game::engine3d
- (mod) pub use {animation::*, bvh::*, math::*, mesh::*, physics::*, quality::*, renderer::*, world::*};

### game::engine3d::physics
- (impl) pub fn dynamic_box(position: Vec3, half_extents: Vec3, mass: f32) -> Self {
- (impl) pub fn static_box(position: Vec3, half_extents: Vec3) -> Self {
- (impl) pub fn world_aabb(&self) -> Aabb3D {
- (impl) pub fn apply_impulse(&mut self, impulse: Vec3) {
- (impl) pub fn add_body(&mut self, body: RigidBody3D) -> usize {
- (impl) pub fn step(&mut self, dt: f32) -> usize {
- (impl) pub fn raycast(&self, ray: &Ray3D, max_distance: f32) -> Option<RayHitPhysics3D> {
- (mod) pub use r#struct::*;
- (struct) pub struct RigidBody3D {
- (struct) pub struct RayHitPhysics3D {
- (struct) pub struct PhysicsWorld3D {

### game::engine3d::quality
- (enum) pub enum QualityPreset {
- (enum) pub enum ResolutionPreset {
- (enum) pub enum RayTracingMode {
- (enum) pub enum UpscalerMode {
- (enum) pub enum AntiAliasingMode {
- (impl) pub const fn dimensions(&self) -> (u32, u32) {
- (impl) pub fn from_preset(preset: QualityPreset) -> Self {
- (impl) pub fn adjust_dynamic_resolution(&mut self, frame_ms: f32) {
- (mod) pub use {r#enum::*, r#struct::*};
- (struct) pub struct RenderQualityConfig {

### game::engine3d::renderer
- (impl) pub fn sample_sky(dir: Vec3, sun: &DirectionalLight3D) -> Vec3 {
- (impl) pub fn render_world( &mut self, world: &mut World3D, viewport_w: u32, viewport_h: u32, quality: &RenderQualityConfig, ) -> ImageBuffer {
- (mod) pub use r#struct::*;
- (struct) pub struct RenderStats3D {
- (struct) pub struct Renderer3D {

### game::engine3d::world
- (enum) pub enum CameraMode3D {
- (impl) pub const fn new(position: Vec3, yaw_rad: f32, scale: Vec3) -> Self {
- (impl) pub fn with_euler(mut self, yaw_rad: f32, pitch_rad: f32, roll_rad: f32) -> Self {
- (impl) pub fn lerp(self, other: Self, t: f32) -> Self {
- (impl) pub fn to_mat4(&self) -> Mat4 {
- (impl) pub fn transform_point(&self, p: Vec3) -> Vec3 {
- (impl) pub fn transform_normal(&self, n: Vec3) -> Vec3 {
- (impl) pub fn transform_aabb(&self, local: Aabb3D) -> Aabb3D {
- (impl) pub const fn from_u8(index: u8) -> Self {
- (impl) pub const fn as_u8(self) -> u8 {
- (impl) pub fn new(name: &str, mesh_id: usize) -> Self {
- (impl) pub fn with_transform(mut self, transform: Transform3D) -> Self {
- (impl) pub fn with_material(mut self, material: PbrMaterial) -> Self {
- (impl) pub fn with_ray_trace(mut self, ray_trace_caster: bool) -> Self {
- (impl) pub fn with_spin(mut self, spin_speed: f32) -> Self {
- (impl) pub fn new(format: ModelFormat, source: &str) -> Self {
- (impl) pub fn with_transform(mut self, transform: Transform3D) -> Self {
- (impl) pub fn with_material(mut self, fallback_material: PbrMaterial) -> Self {
- (impl) pub fn with_spin(mut self, spin_speed: f32) -> Self {
- (impl) pub fn from_time_of_day(hour: f32) -> Self {
- (impl) pub fn register_mesh(&mut self, chain: MeshLodChain) -> usize {
- (impl) pub fn spawn_object( &mut self, name: &str, mesh_id: usize, transform: Transform3D, material: PbrMaterial, ray_trace_caster: bool, ) -> usize {
- (impl) pub fn import_model( &mut self, format: ModelFormat, source: &str, transform: Transform3D, fallback_material: PbrMaterial, spin_speed: f32, ) -> Result<ImportedModel3D, String> {
- (impl) pub fn spawn_with(&mut self, desc: &SpawnObjectDesc) -> usize {
- (impl) pub fn import_with(&mut self, desc: &ImportModelDesc) -> Result<ImportedModel3D, String> {
- (impl) pub fn active_camera_mode(&self) -> CameraMode3D {
- (impl) pub fn set_camera_mode_enum(&mut self, mode: CameraMode3D) {
- (impl) pub fn ensure_bvh(&mut self) {
- (impl) pub fn vehicle_index(&self) -> Option<usize> {
- (impl) pub fn create_open_world_city() -> Self {
- (impl) pub fn cycle_camera_mode(&mut self) -> u8 {
- (impl) pub fn step_simulation(&mut self, dt: f32, input: &InputState, actions: &ActionMap) {
- (mod) pub use {r#enum::*, r#struct::*};
- (struct) pub struct Transform3D {
- (struct) pub struct SpawnObjectDesc {
- (struct) pub struct ImportModelDesc {
- (struct) pub struct SceneObject3D {
- (struct) pub struct DirectionalLight3D {
- (struct) pub struct World3D {

### game::input
- (enum) pub enum GameAction {
- (impl) pub fn begin_frame(&mut self) {
- (impl) pub fn ingest(&mut self, event: &WindowEvent) {
- (impl) pub fn is_key_down(&self, key: KeyCode) -> bool {
- (impl) pub fn is_key_just_pressed(&self, key: KeyCode) -> bool {
- (impl) pub fn is_button_down(&self, button: PointerButton) -> bool {
- (impl) pub fn axis(&self, negative: KeyCode, positive: KeyCode) -> f32 {
- (impl) pub fn set_virtual_stick(&mut self, dx: f32, dy: f32) {
- (impl) pub fn clear_virtual_stick(&mut self) {
- (impl) pub fn bind_key(&mut self, action: GameAction, key: KeyCode) {
- (impl) pub fn bind_button(&mut self, action: GameAction, button: PointerButton) {
- (impl) pub fn is_active(&self, action: GameAction, input: &InputState) -> bool {
- (impl) pub fn is_just_pressed(&self, action: GameAction, input: &InputState) -> bool {
- (impl) pub fn movement_vector(&self, input: &InputState) -> Point {
- (mod) pub use {r#enum::*, r#struct::*};
- (struct) pub struct InputState {
- (struct) pub struct ActionMap {

### game
- (mod) pub use {

### game::particles
- (impl) pub fn with_capacity(capacity: usize) -> Self {
- (impl) pub fn emit_burst(&mut self, origin: Point, count: usize, config: ParticleEmitterConfig) {
- (impl) pub fn update(&mut self, dt_secs: f32) -> usize {
- (impl) pub fn clear(&mut self) {
- (mod) pub use r#struct::*;
- (struct) pub struct Particle {
- (struct) pub struct ParticleEmitterConfig {
- (struct) pub struct ParticleSystem {

### game::physics
- (const) pub const DEFAULT_SPATIAL_CELL_SIZE: f32 = 64.0;
- (const) pub const COLLISION_LAYER_ALL: u32 = u32::MAX;
- (const) pub const COLLISION_LAYER_PLAYER: u32 = 1 << 0;
- (const) pub const COLLISION_LAYER_ENEMY: u32 = 1 << 1;
- (const) pub const COLLISION_LAYER_PROJECTILE: u32 = 1 << 2;
- (const) pub const COLLISION_LAYER_WORLD: u32 = 1 << 3;
- (const) pub const COLLISION_LAYER_PICKUP: u32 = 1 << 4;
- (const) pub const COLLISION_MASK_PLAYER_DEFAULT: u32 = COLLISION_LAYER_ENEMY + COLLISION_LAYER_WORLD + COLLISION_LAYER_PICKUP;
- (impl) pub const fn new(origin: Point, direction: Point) -> Self {
- (impl) pub fn with_max_distance(mut self, max_distance: f32) -> Self {
- (impl) pub fn with_layer_mask(mut self, layer_mask: u32) -> Self {
- (impl) pub fn with_config(config: PhysicsConfig) -> Self {
- (impl) pub fn step(&mut self, world: &mut GameWorld, dt_secs: f32) -> Vec<CollisionEvent> {
- (impl) pub fn raycast( world: &GameWorld, origin: Point, direction: Point, max_distance: f32, layer_mask: u32, ) -> Option<RaycastHit> {
- (impl) pub fn raycast_query(world: &GameWorld, query: &RaycastQuery2D) -> Option<RaycastHit> {
- (mod) pub use {r#const::*, r#struct::*};
- (struct) pub struct PhysicsConfig {
- (struct) pub struct CollisionEvent {
- (struct) pub struct RaycastQuery2D {
- (struct) pub struct RaycastHit {
- (struct) pub struct PhysicsStepStats {
- (struct) pub struct PhysicsWorld2D {

### game::tilemap
- (impl) pub fn empty(columns: usize, rows: usize, tile_size: f32) -> Self {
- (impl) pub fn add_palette_entry(&mut self, entry: TilePaletteEntry) -> u16 {
- (impl) pub fn set_tile(&mut self, col: usize, row: usize, tile_id: u16) {
- (impl) pub fn tile_at(&self, col: usize, row: usize) -> u16 {
- (impl) pub fn is_solid_at_world(&self, world_pt: Point) -> bool {
- (impl) pub fn world_bounds(&self) -> Rect {
- (impl) pub fn from_grid(texture: ImageBuffer, frame_width: u32, frame_height: u32) -> Self {
- (impl) pub fn frame_rect(&self, frame_index: u32) -> Rect {
- (impl) pub fn tick(&mut self, dt_secs: f32) -> u32 {
- (impl) pub fn current_frame(&self) -> u32 {
- (mod) pub use r#struct::*;
- (struct) pub struct TilePaletteEntry {
- (struct) pub struct TileMap {
- (struct) pub struct SpriteSheet {
- (struct) pub struct SpriteAnimator {

### game::viewport
- (impl) pub fn new(bounds: Rect, display_list: &'a mut DisplayList) -> Self {
- (impl) pub fn viewport_size(&self) -> Size {
- (impl) pub fn clear(&mut self, color: Color) {
- (impl) pub fn fill_rect(&mut self, rect: Rect, color: Color) {
- (impl) pub fn fill_rounded_rect(&mut self, rect: Rect, color: Color, radius: f32) {
- (impl) pub fn stroke_rect(&mut self, rect: Rect, stroke_width: f32, color: Color) {
- (impl) pub fn fill_circle(&mut self, center: Point, radius: f32, color: Color) {
- (impl) pub fn draw_image(&mut self, rect: Rect, buffer: ImageBuffer) {
- (impl) pub fn draw_line(&mut self, from: Point, to: Point, width: f32, color: Color) {
- (impl) pub fn draw_text(&mut self, position: Point, text: String, font_size: f32, color: Color) {
- (impl) pub fn blit_framebuffer(&mut self, rect: Rect, buffer: ImageBuffer) {
- (impl) pub fn fill_triangle(&mut self, p0: Point, p1: Point, p2: Point, color: Color) {
- (impl) pub fn draw_sprite_frame( &mut self, sheet: &SpriteSheet, frame_index: u32, rect: Rect, tint: Color, ) {
- (impl) pub fn render_tilemap(&mut self, tilemap: &TileMap, camera: &Camera2D) {
- (impl) pub fn render_world(&mut self, world: &GameWorld, camera: &Camera2D) -> usize {
- (impl) pub fn render_particles(&mut self, particles: &ParticleSystem, camera: &Camera2D) -> usize {
- (impl) pub fn draw_debug_colliders(&mut self, world: &GameWorld, camera: &Camera2D) {
- (impl) pub fn new<S>(scene: S, fixed_dt: f32) -> Self where S: GameScene + 'static, {
- (impl) pub fn active_viewport_bounds(&self, tree: &SceneTree) -> Vec<Rect> {
- (impl) pub fn ingest_event(&self, event: &WindowEvent) {
- (impl) pub fn step(&self, dt_secs: f32) -> u32 {
- (impl) pub fn set_virtual_stick(&self, dx: f32, dy: f32) {
- (impl) pub fn press_key(&self, code: KeyCode) {
- (impl) pub fn release_key(&self, code: KeyCode) {
- (impl) pub fn mount_viewport(&self, style: Style) -> NodeId {
- (mod) pub use {r#struct::*, r#trait::*};
- (struct) pub struct GameRenderContext<'a> {
- (struct) pub struct GameEngineHost {
- (trait) pub trait GameScene {

### layout::cache
- (impl) pub fn root(viewport: Size) -> Self {
- (mod) pub use r#struct::*;
- (struct) pub struct AvailableSpace {
- (struct) pub struct LayoutStats {

### layout::engine
- (fn) pub fn hit_test(tree: &SceneTree, point: Point) -> Option<NodeId> {
- (impl) pub fn compute(&mut self, tree: &mut SceneTree, viewport: Size) -> LayoutStats {
- (mod) pub use {r#fn::*, r#struct::*};
- (struct) pub struct LayoutEngine {

### layout
- (mod) pub use {cache::*, engine::*};

### crate root
- (lib) pub use {

### media::codec
- (impl) pub fn detect_media_kind(uri: &str, bytes: &[u8]) -> MediaKind {
- (impl) pub fn detect_image_format(uri: &str, bytes: &[u8]) -> ImageFormat {
- (impl) pub fn decode_bmp(bytes: &[u8], alt_text: &str) -> Result<ImageAsset, String> {
- (impl) pub fn decode_gif(bytes: &[u8], title: &str) -> Result<GifAnimation, String> {
- (impl) pub fn decode_wav(bytes: &[u8], title: &str) -> Result<AudioTrack, String> {
- (impl) pub fn parse_pdf(bytes: &[u8]) -> Result<PdfDocument, String> {
- (impl) pub fn parse_html(raw: &str) -> HtmlDocument {
- (impl) pub fn parse_and_rasterize_svg( raw_svg: &str, out_w: u32, out_h: u32, ) -> Result<SvgDocument, String> {
- (impl) pub fn compute_waveform_peaks(samples: &[f32], bars: usize) -> Vec<f32> {
- (impl) pub fn synthesize_frame( width: u32, height: u32, bg: Color, accent: Color, frame_idx: usize, ) -> ImageBuffer {

### media
- (mod) pub use types::*;

### media::player
- (impl) pub fn sample_photo(alt_text: &str) -> Self {
- (impl) pub fn sample_neon_gif() -> Self {
- (impl) pub fn step_ms(&mut self, dt_ms: u32) -> bool {
- (impl) pub fn next_frame(&mut self) {
- (impl) pub fn active_image(&self) -> ImageBuffer {
- (impl) pub fn sample_live_photo() -> Self {
- (impl) pub fn set_motion_playing(&mut self, active: bool) {
- (impl) pub fn step_ms(&mut self, dt_ms: u32) {
- (impl) pub fn active_image(&self) -> ImageBuffer {
- (impl) pub fn sample_hdr_video() -> Self {
- (impl) pub fn toggle_play(&mut self) {
- (impl) pub fn seek(&mut self, secs: f32) {
- (impl) pub fn step(&mut self, dt_secs: f32) {
- (impl) pub fn active_frame(&self) -> ImageBuffer {
- (impl) pub fn active_caption(&self) -> String {
- (impl) pub fn sample_synth_wav() -> Self {
- (impl) pub fn toggle_play(&mut self) {
- (impl) pub fn seek(&mut self, secs: f32) {
- (impl) pub fn step(&mut self, dt_secs: f32) {
- (impl) pub fn preview_image(&self) -> Option<ImageBuffer> {
- (impl) pub fn sample_pdf() -> Self {
- (impl) pub fn next_page(&mut self) {
- (impl) pub fn prev_page(&mut self) {
- (impl) pub fn adjust_zoom(&mut self, delta: f32) {
- (impl) pub fn active_page(&self) -> Option<&PdfPage> {
- (impl) pub fn href_url(&self) -> Option<String> {
- (impl) pub fn image_src(&self) -> Option<String> {
- (impl) pub fn sample_html() -> Self {
- (impl) pub fn sample_svg() -> Self {

### media::types
- (enum) pub enum MediaKind {
- (enum) pub enum MediaFit {
- (enum) pub enum PlaybackState {
- (enum) pub enum ImageFormat {
- (enum) pub enum AudioCodec {
- (enum) pub enum VideoCodec {
- (enum) pub enum HtmlNodeKind {
- (mod) pub use {r#enum::*, r#struct::*};
- (struct) pub struct MediaSource {
- (struct) pub struct MediaMetadata {
- (struct) pub struct MediaFrame {
- (struct) pub struct ImageAsset {
- (struct) pub struct GifAnimation {
- (struct) pub struct LivePhotoAsset {
- (struct) pub struct VideoTrack {
- (struct) pub struct AudioTrack {
- (struct) pub struct PdfPage {
- (struct) pub struct PdfDocument {
- (struct) pub struct HtmlBlock {
- (struct) pub struct HtmlDocument {
- (struct) pub struct SvgDocument {
- (struct) pub struct MediaCodecRegistry;

### platform::android
- (fn) pub fn android_query_window_size(native_window: usize) -> Option<(u32, u32)> {
- (impl) pub fn attach_native_window(&mut self, native_window: usize, density_scale: f32) {
- (mod) pub use {r#fn::*, r#struct::*};
- (struct) pub struct AndroidWindowRecord {
- (struct) pub struct AndroidPlatform {

### platform::backend
- (enum) pub enum PlatformError {
- (fn) pub fn detect_current_platform() -> PlatformKind {
- (fn) pub fn create_native_platform() -> Box<dyn PlatformBackend> {
- (mod) pub use {r#enum::*, r#fn::*, r#trait::*};
- (trait) pub trait PlatformBackend: WindowController {

### platform::headless
- (impl) pub fn emulating(platform: PlatformKind, scale_factor: f32, safe_area: SafeAreaInsets) -> Self {
- (impl) pub fn push_event(&mut self, event: WindowEvent) {
- (impl) pub fn last_framebuffer(&self, id: WindowId) -> Option<&Framebuffer> {
- (mod) pub use r#struct::*;
- (struct) pub struct HeadlessWindowRecord {
- (struct) pub struct HeadlessPlatform {

### platform::info
- (const) pub const PLATFORM_NAME_WEB: &str = "web";
- (const) pub const PLATFORM_NAME_ANDROID: &str = "android";
- (const) pub const PLATFORM_NAME_IOS: &str = "ios";
- (const) pub const PLATFORM_NAME_IPADOS: &str = "ipados";
- (const) pub const PLATFORM_NAME_MACOS: &str = "macos";
- (const) pub const PLATFORM_NAME_WINDOWS: &str = "windows";
- (const) pub const PLATFORM_NAME_LINUX: &str = "linux";
- (const) pub const PLATFORM_NAME_HEADLESS: &str = "headless";
- (enum) pub enum PlatformKind {
- (enum) pub enum DeviceFormFactor {
- (enum) pub enum RawWindowHandle {
- (impl) pub const fn as_str(&self) -> &'static str {
- (impl) pub const fn form_factor(&self) -> DeviceFormFactor {
- (impl) pub const fn is_mobile_or_tablet(&self) -> bool {
- (impl) pub const fn all_targets() -> [Self; 7] {
- (impl) pub fn for_platform(platform: PlatformKind) -> Self {
- (mod) pub use {r#const::*, r#enum::*, r#struct::*};
- (struct) pub struct PlatformCapabilities {

### platform::ios
- (fn) pub fn ios_detect_platform_kind() -> PlatformKind {
- (fn) pub fn ios_screen_scale() -> f32 {
- (fn) pub fn ios_system_theme() -> ThemeMode {
- (mod) pub use {r#fn::*, r#struct::*};
- (struct) pub struct IosWindowRecord {
- (struct) pub struct IosPlatform {

### platform::linux
- (mod) pub use r#struct::*;
- (struct) pub struct LinuxWindowRecord {
- (struct) pub struct LinuxPlatform {

### platform::macos
- (fn) pub fn macos_backing_scale_factor() -> f32 {
- (fn) pub fn macos_system_theme() -> ThemeMode {
- (mod) pub use {r#fn::*, r#struct::*};
- (struct) pub struct MacOsWindowRecord {
- (struct) pub struct MacOsPlatform {

### platform
- (mod) pub use android::*;
- (mod) pub use ios::*;
- (mod) pub use linux::*;
- (mod) pub use macos::*;
- (mod) pub use web::*;
- (mod) pub use windows::*;
- (mod) pub use {backend::*, headless::*, info::*};

### platform::web
- (fn) pub fn web_system_theme() -> ThemeMode {
- (fn) pub fn web_device_pixel_ratio() -> f32 {
- (mod) pub use {r#fn::*, r#struct::*};
- (struct) pub struct WebWindowRecord {
- (struct) pub struct WebPlatform {

### platform::windows
- (mod) pub use r#struct::*;
- (struct) pub struct WindowsWindowRecord {
- (struct) pub struct WindowsPlatform {

### reactive::effect
- (impl) pub fn new<F>(callback: F) -> Self where F: FnMut() + 'static, {
- (impl) pub fn id(&self) -> EffectId {
- (impl) pub fn dispose(&self) {
- (mod) pub use r#struct::*;
- (struct) pub struct Effect {

### reactive::id
- (impl) pub fn as_usize(&self) -> usize {
- (impl) pub fn from_slot(slot: SlotId) -> Self {
- (impl) pub fn slot(&self) -> SlotId {
- (impl) pub fn from_slot(slot: SlotId) -> Self {
- (impl) pub fn slot(&self) -> SlotId {
- (impl) pub fn from_slot(slot: SlotId) -> Self {
- (impl) pub fn slot(&self) -> SlotId {
- (impl) pub fn from_slot(slot: SlotId) -> Self {
- (impl) pub fn slot(&self) -> SlotId {
- (mod) pub use r#struct::*;
- (struct) pub struct SlotId {
- (struct) pub struct SignalId(pub(crate) SlotId);
- (struct) pub struct MemoId(pub(crate) SlotId);
- (struct) pub struct EffectId(pub(crate) SlotId);
- (struct) pub struct ScopeId(pub(crate) SlotId);

### reactive::memo
- (impl) pub fn id(&self) -> MemoId {
- (impl) pub fn new<F>(mut compute: F) -> Self where F: FnMut() -> T + 'static, {
- (impl) pub fn try_get(&self) -> Option<T> {
- (impl) pub fn get(&self) -> T where T: Default, {
- (impl) pub fn dispose(&self) {
- (mod) pub use r#struct::*;
- (struct) pub struct Memo<T> where T: 'static, {

### reactive
- (mod) pub use {effect::*, id::*, memo::*, runtime::*, scope::*, selector::*, signal::*};

### reactive::runtime
- (enum) pub enum SubscriberId {
- (enum) pub enum DependencyId {
- (enum) pub enum NodeState {
- (fn) pub fn flush_effects() {
- (fn) pub fn batch<F, R>(operation: F) -> R where F: FnOnce() -> R, {
- (fn) pub fn untracked<F, R>(operation: F) -> R where F: FnOnce() -> R, {
- (fn) pub fn on_cleanup<F>(cleanup: F) where F: FnOnce() + 'static, {
- (fn) pub fn reactive_stats() -> ReactiveStats {
- (fn) pub fn reset_reactive_runtime() {
- (impl) pub fn stats(&self) -> ReactiveStats {
- (mod) pub use {r#enum::*, r#fn::*, r#struct::*};
- (struct) pub struct ReactiveRuntime {
- (struct) pub struct ReactiveStats {

### reactive::scope
- (impl) pub fn run<F, R>(body: F) -> (Self, R) where F: FnOnce(Self) -> R, {
- (impl) pub fn enter<F, R>(&self, body: F) -> R where F: FnOnce() -> R, {
- (impl) pub fn id(&self) -> ScopeId {
- (impl) pub fn dispose(&self) {
- (mod) pub use r#struct::*;
- (struct) pub struct Scope {

### reactive::selector
- (impl) pub fn new<F>(mut source: F) -> Self where F: FnMut() -> K + 'static, {
- (impl) pub fn is_selected(&self, key: K) -> bool {
- (impl) pub fn dispose(&self) {
- (mod) pub use r#struct::*;
- (struct) pub struct Selector<K> where K: Clone + Eq + Hash + 'static, {

### reactive::signal
- (impl) pub fn new(initial_value: T) -> Self {
- (impl) pub fn new_detached(initial_value: T) -> Self {
- (impl) pub fn id(&self) -> SignalId {
- (impl) pub fn track(&self) {
- (impl) pub fn try_get(&self) -> Option<T> where T: Clone, {
- (impl) pub fn get(&self) -> T where T: Clone + Default, {
- (impl) pub fn try_get_untracked(&self) -> Option<T> where T: Clone, {
- (impl) pub fn get_untracked(&self) -> T where T: Clone + Default, {
- (impl) pub fn with<F, R>(&self, reader: F) -> Option<R> where T: Clone, F: FnOnce(&T) -> R, {
- (impl) pub fn set(&self, value: T) -> bool {
- (impl) pub fn set_if_changed(&self, value: T) -> bool where T: PartialEq, {
- (impl) pub fn update<F>(&self, updater: F) -> bool where T: Clone, F: FnOnce(&mut T), {
- (impl) pub fn dispose(&self) {
- (mod) pub use r#struct::*;
- (struct) pub struct Signal<T> where T: 'static, {

### render::buffer
- (impl) pub fn allocate(width: u32, height: u32) -> Self {
- (impl) pub fn resize(&mut self, width: u32, height: u32) -> bool {
- (impl) pub fn clear(&mut self, color: Color) {
- (impl) pub fn fill_span(&mut self, x0: u32, x1: u32, y: u32, color: Color) {
- (impl) pub fn fill_span_linear(&mut self, x0: u32, x1: u32, y: u32, color: Color) {
- (impl) pub fn blend_glyph_row(&mut self, dx: u32, dy: u32, coverage: &[u8], color: Color) -> usize {
- (impl) pub fn get_pixel(&self, x: u32, y: u32) -> Option<Color> {
- (impl) pub fn blend_pixel_linear_dithered(&mut self, x: u32, y: u32, color: Color, dither: f32) {
- (impl) pub fn blend_pixel_f32_dithered( &mut self, x: u32, y: u32, color: Color, alpha_f: f32, dither: f32, ) {
- (impl) pub fn blend_pixel(&mut self, x: u32, y: u32, color: Color) {
- (impl) pub fn to_bgra_bytes(&self) -> Vec<u8> {
- (impl) pub fn fnv1a_hash(&self) -> u64 {
- (impl) pub fn as_band_mut(&mut self) -> PixelBand<'_> {
- (impl) pub fn split_bands_mut(&mut self, y0: u32, y1: u32, band_count: usize) -> Vec<PixelBand<'_>> {
- (impl) pub fn width(&self) -> u32 {
- (impl) pub fn y_offset(&self) -> u32 {
- (impl) pub fn y_end(&self) -> u32 {
- (impl) pub fn row_slice_mut(&mut self, y: u32) -> Option<&mut [u8]> {
- (impl) pub fn clear(&mut self, color: Color) {
- (impl) pub fn fill_span(&mut self, x0: u32, x1: u32, y: u32, color: Color) {
- (impl) pub fn fill_span_linear(&mut self, x0: u32, x1: u32, y: u32, color: Color) {
- (impl) pub fn blend_shadow_span_const_alpha( &mut self, x0: u32, x1: u32, y: u32, color: Color, alpha_f: f32, ) {
- (impl) pub fn blend_glyph_row(&mut self, dx: u32, dy: u32, coverage: &[u8], color: Color) -> usize {
- (impl) pub fn blend_pixel(&mut self, x: u32, y: u32, color: Color) {
- (impl) pub fn blend_pixel_linear_dithered(&mut self, x: u32, y: u32, color: Color, dither: f32) {
- (impl) pub fn blend_pixel_f32_dithered( &mut self, x: u32, y: u32, color: Color, alpha_f: f32, dither: f32, ) {
- (impl) pub fn full() -> Self {
- (impl) pub fn add_rect(&mut self, rect: Rect) {
- (impl) pub fn resolve(&self, width: u32, height: u32) -> Option<Rect> {
- (impl) pub fn bounds_rect(&self) -> Option<Rect> {
- (impl) pub fn clear(&mut self) {
- (mod) pub use r#struct::*;
- (struct) pub struct Framebuffer {
- (struct) pub struct PixelBand<'a> {
- (struct) pub struct DamageRegion {

### render::command
- (enum) pub enum DrawCommand {
- (impl) pub fn reset(&mut self, viewport: Size, scale_factor: f32) {
- (impl) pub fn push(&mut self, command: DrawCommand) {
- (impl) pub fn len(&self) -> usize {
- (impl) pub fn is_empty(&self) -> bool {
- (impl) pub fn fast_hash(&self) -> u64 {
- (impl) pub fn build( tree: &SceneTree, viewport: Size, scale_factor: f32, clear_color: Color, display_list: &mut DisplayList, ) {
- (mod) pub use {r#enum::*, r#struct::*};
- (struct) pub struct DisplayList {
- (struct) pub struct PaintPass;

### render::config
- (const) pub const DEFAULT_TILE_SIZE: u32 = 64;
- (const) pub const DEFAULT_MAX_FPS: u32 = 120;
- (enum) pub enum RenderMode {
- (enum) pub enum GraphicsBackend {
- (enum) pub enum PresentMode {
- (enum) pub enum AntialiasingMode {
- (enum) pub enum ColorSpace {
- (impl) pub fn software() -> Self {
- (impl) pub fn hardware() -> Self {
- (impl) pub fn hybrid() -> Self {
- (impl) pub fn preferred_backend_value(&self) -> Option<GraphicsBackend> {
- (mod) pub use {r#const::*, r#enum::*, r#struct::*};
- (struct) pub struct RenderConfig {
- (struct) pub struct FrameStats {

### render::gpu
- (const) pub const GPU_DEVICE_FALLBACK: &str = "euv-software-fallback";
- (const) pub const GPU_DEVICE_WEB: &str = "Browser WebGL2 / WebGPU";
- (const) pub const GPU_DEVICE_D3D12: &str = "Windows Direct3D 12";
- (const) pub const GPU_DEVICE_VULKAN: &str = "Vulkan Physical GPU";
- (fn) pub fn probe_native_gpu(backend: GraphicsBackend) -> (GpuAdapterInfo, usize, usize, usize) {
- (fn) pub fn submit_native_gpu_batches( device_handle: usize, queue_handle: usize, batches: &[GpuBatch], ) -> usize {
- (fn) pub fn release_native_gpu_handles( device_handle: usize, queue_handle: usize, library_handle: usize, ) {
- (fn) pub fn webgl2_compile_ui_program(gl: &WebGl2RenderingContext) -> Option<WebGlProgram> {
- (impl) pub fn probe(backend: GraphicsBackend) -> Self {
- (impl) pub fn switch_backend(&mut self, backend: GraphicsBackend) {
- (mod) pub use {r#const::*, r#fn::*, r#struct::*};
- (struct) pub struct GpuAdapterInfo {
- (struct) pub struct NativeGpuDriver {

### render::hardware
- (const) pub const WGSL_UI_SHADER: &str = r#" struct Uniforms {
- (const) pub const MSL_UI_SHADER: &str = r#" #include <metal_stdlib> using namespace metal;
- (const) pub const GLSL_ES3_UI_VERTEX_SHADER: &str = r#"#version 300 es precision highp float;
- (const) pub const GLSL_ES3_UI_FRAGMENT_SHADER: &str = r#"#version 300 es precision highp float;
- (const) pub const HLSL_UI_SHADER: &str = r#" struct PSInput {
- (const) pub const MAX_QUADS_PER_BATCH: usize = 4096;
- (enum) pub enum GpuPrimitiveKind {
- (impl) pub fn with_backend( backend: GraphicsBackend, width: u32, height: u32, config: RenderConfig, enable_readback: bool, ) -> Self {
- (impl) pub fn with_backend_and_font( backend: GraphicsBackend, width: u32, height: u32, config: RenderConfig, enable_readback: bool, font_provider: NativeSystemFont, ) -> Self {
- (impl) pub fn batch_hash(&self) -> u64 {
- (impl) pub fn render( &mut self, display_list: &DisplayList, damage: DamageRegion, ) -> Result<(usize, usize), PlatformError> {
- (mod) pub use {r#const::*, r#enum::*, r#struct::*, r#trait::*};
- (struct) pub struct GpuQuadInstance {
- (struct) pub struct GpuBatch {
- (struct) pub struct RecordingGpuDriver {
- (struct) pub struct HardwareRenderer {
- (trait) pub trait GpuDriver {

### render::hybrid
- (impl) pub fn with_backend( gpu_backend: GraphicsBackend, width: u32, height: u32, config: RenderConfig, ) -> Self {
- (impl) pub fn with_backend_and_font( gpu_backend: GraphicsBackend, width: u32, height: u32, config: RenderConfig, font_provider: NativeSystemFont, ) -> Self {
- (impl) pub fn render( &mut self, display_list: &DisplayList, damage: DamageRegion, ) -> Result<(usize, usize), PlatformError> {
- (mod) pub use r#struct::*;
- (struct) pub struct HybridRenderer {

### render
- (mod) pub use {

### render::pipeline
- (impl) pub fn new(viewport: Size) -> Self {
- (impl) pub fn with_scale(mut self, scale_factor: f32) -> Self {
- (impl) pub fn with_clear(mut self, clear_color: Color) -> Self {
- (impl) pub fn with_layout_stats(mut self, layout_stats: LayoutStats) -> Self {
- (impl) pub fn with_damage(mut self, damage: DamageRegion) -> Self {
- (impl) pub fn new( platform: PlatformKind, capabilities: PlatformCapabilities, width: u32, height: u32, config: RenderConfig, ) -> Self {
- (impl) pub fn resolve_mode_and_backend( platform: PlatformKind, capabilities: PlatformCapabilities, config: RenderConfig, ) -> (RenderMode, GraphicsBackend) {
- (impl) pub fn switch_mode( &mut self, platform: PlatformKind, capabilities: PlatformCapabilities, mode: RenderMode, ) {
- (impl) pub fn render_frame( &mut self, tree: &SceneTree, viewport: Size, scale_factor: f32, clear_color: Color, layout_stats: LayoutStats, damage: DamageRegion, ) -> Result<FrameStats, PlatformError> {
- (impl) pub fn render_with( &mut self, tree: &SceneTree, params: &FrameRenderParams, ) -> Result<FrameStats, PlatformError> {
- (impl) pub fn record_skipped_frame(&mut self) -> FrameStats {
- (impl) pub fn framebuffer(&self) -> Option<&Framebuffer> {
- (mod) pub use r#struct::*;
- (struct) pub struct FrameRenderParams {
- (struct) pub struct Renderer {

### render::software
- (fn) pub fn fast_gaussian_shadow_falloff(dist: f32, inv_sigma: f32) -> f32 {
- (fn) pub fn interleaved_gradient_noise(x: u32, y: u32) -> f32 {
- (fn) pub fn gaussian_shadow_falloff(dist: f32, sigma: f32) -> f32 {
- (fn) pub fn quadrant_corner_radius(radius: CornerRadius, px: f32, py: f32) -> f32 {
- (fn) pub fn rounded_box_sdf(px: f32, py: f32, half_w: f32, half_h: f32, radius: f32) -> f32 {
- (fn) pub fn sdf_coverage(distance: f32, aa: AntialiasingMode) -> f32 {
- (fn) pub fn rounded_box_supersampled_coverage( px: f32, py: f32, half_w: f32, half_h: f32, corner_r: f32, border_w: f32, ) -> (f32, f32) {
- (fn) pub fn circle_supersampled_coverage(dx: f32, dy: f32, radius: f32) -> f32 {
- (fn) pub fn triangle_supersampled_coverage(px: f32, py: f32, p0: Point, p1: Point, p2: Point) -> f32 {
- (fn) pub fn snap_physical_rect(rect: Rect, scale: f32) -> Rect {
- (fn) pub fn composite_fill_and_border( fill: Color, border: Color, outer_cov: f32, inner_cov: f32, ) -> Color {
- (impl) pub fn with_config(width: u32, height: u32, config: RenderConfig) -> Self {
- (impl) pub fn with_font_provider( width: u32, height: u32, config: RenderConfig, font_provider: NativeSystemFont, ) -> Self {
- (impl) pub fn render(&mut self, display_list: &DisplayList, damage: DamageRegion) -> (usize, usize) {
- (mod) pub use {r#fn::*, r#struct::*};
- (struct) pub struct SoftwareRenderer {

### scene::animation
- (enum) pub enum Easing {
- (impl) pub fn eval(&self, t: f32) -> f32 {
- (impl) pub fn for_node(node: NodeId) -> Self {
- (impl) pub fn with_duration(mut self, duration_secs: f32) -> Self {
- (impl) pub fn with_easing(mut self, easing: Easing) -> Self {
- (impl) pub fn with_opacity(mut self, from: f32, to: f32) -> Self {
- (impl) pub fn with_offset(mut self, from: Point, to: Point) -> Self {
- (impl) pub fn with_scale(mut self, from: f32, to: f32) -> Self {
- (impl) pub fn with_hide_on_complete(mut self, hide: bool) -> Self {
- (impl) pub fn route_enter(node: NodeId) -> Self {
- (impl) pub fn fade(node: NodeId, from: f32, to: f32, duration: f32, hide_on_complete: bool) -> Self {
- (impl) pub fn slide_fade( node: NodeId, from_offset: Point, to_offset: Point, from_opacity: f32, to_opacity: f32, duration: f32, hide_on_complete: bool, ) -> Self {
- (impl) pub fn modal_enter(node: NodeId) -> Self {
- (impl) pub fn modal_exit(node: NodeId) -> Self {
- (impl) pub fn sample(&self) -> (f32, Transform2D) {
- (impl) pub fn is_complete(&self) -> bool {
- (mod) pub use {r#enum::*, r#struct::*};
- (struct) pub struct NodeTransition {

### scene::event
- (enum) pub enum UiEventKind {
- (impl) pub fn handler_for(&self, kind: &UiEventKind) -> Option<UiEventHandler> {
- (mod) pub use {r#enum::*, r#struct::*, r#type::*};
- (struct) pub struct UiEvent {
- (struct) pub struct EventHandlers {
- (type) pub type UiEventHandler = Rc<RefCell<dyn FnMut(&UiEvent)>>;
- (type) pub type CanvasDrawCallback = Rc<RefCell<dyn FnMut(Rect, &mut DisplayList)>>;

### scene::flags
- (const) pub const DIRTY_NONE: u16 = 0;
- (const) pub const DIRTY_LAYOUT: u16 = 1 << 0;
- (const) pub const DIRTY_PAINT: u16 = 1 << 1;
- (const) pub const DIRTY_TEXT: u16 = 1 << 2;
- (const) pub const DIRTY_CHILDREN: u16 = 1 << 3;
- (const) pub const DIRTY_SCROLL: u16 = 1 << 4;
- (const) pub const DIRTY_SUBTREE_LAYOUT: u16 = 1 << 5;
- (const) pub const DIRTY_SUBTREE_PAINT: u16 = 1 << 6;
- (const) pub const DIRTY_ALL: u16 = DIRTY_LAYOUT | DIRTY_PAINT | DIRTY_TEXT | DIRTY_CHILDREN | DIRTY_SCROLL | DIRTY_SUBTREE_LAYOUT | DIRTY_SUBTREE_PAINT;
- (impl) pub const fn none() -> Self {
- (impl) pub const fn all() -> Self {
- (impl) pub fn insert(&mut self, mask: u16) {
- (impl) pub fn remove(&mut self, mask: u16) {
- (impl) pub fn intersects(&self, mask: u16) -> bool {
- (impl) pub fn is_clean(&self) -> bool {
- (mod) pub use {r#const::*, r#struct::*};
- (struct) pub struct DirtyFlags {

### scene::focus
- (impl) pub fn focused_node(&self) -> Option<NodeId> {
- (impl) pub fn hovered_node(&self) -> Option<NodeId> {
- (impl) pub fn pressed_node(&self) -> Option<NodeId> {
- (mod) pub use r#struct::*;
- (struct) pub struct FocusManager {

### scene::id
- (impl) pub fn as_usize(&self) -> usize {
- (impl) pub fn is_valid(&self) -> bool {
- (mod) pub use r#struct::*;
- (struct) pub struct NodeId {

### scene::kind
- (enum) pub enum NodeKind {
- (impl) pub fn solid(width: u32, height: u32, color: Color) -> Self {
- (impl) pub fn text<S>(value: S) -> Self where S: Into<String>, {
- (impl) pub fn with_placeholder<S>(mut self, placeholder: S) -> Self where S: Into<String>, {
- (impl) pub fn with_password(mut self, password: bool) -> Self {
- (impl) pub fn with_multiline(mut self, multiline: bool) -> Self {
- (impl) pub fn with_disabled(mut self, disabled: bool) -> Self {
- (impl) pub fn insert_str(&mut self, text: &str) {
- (impl) pub fn backspace(&mut self) {
- (mod) pub use {r#enum::*, r#struct::*};
- (struct) pub struct ImageBuffer {
- (struct) pub struct InputNodeState {

### scene
- (mod) pub use {animation::*, event::*, flags::*, focus::*, id::*, kind::*, node::*, tree::*};

### scene::node
- (impl) pub fn new(generation: u32, kind: NodeKind, style: Style) -> Self {
- (impl) pub fn parent_id(&self) -> Option<NodeId> {
- (impl) pub fn hover_paint(&self) -> Option<PaintStyle> {
- (impl) pub fn owned_scope(&self) -> Option<Scope> {
- (impl) pub fn canvas_callback(&self) -> Option<CanvasDrawCallback> {
- (impl) pub fn a11y_props(&self) -> Option<A11yProps> {
- (impl) pub fn virtual_scroll_metrics(&self) -> Option<(f32, f32)> {
- (mod) pub use r#struct::*;
- (struct) pub struct LayoutBox {
- (struct) pub struct InteractionState {
- (struct) pub struct SceneNode {

### scene::tree
- (fn) pub fn with_build_context<F, R>(ctx: BuildContext, operation: F) -> R where F: FnOnce() -> R, {
- (fn) pub fn current_build_context() -> BuildContext {
- (fn) pub fn has_build_context() -> bool {
- (fn) pub fn current_platform() -> PlatformKind {
- (fn) pub fn mount_current<M>(mountable: M) -> NodeId where M: Mountable, {
- (impl) pub fn create_node(&mut self, kind: NodeKind, style: Style) -> NodeId {
- (impl) pub fn create_view(&mut self, style: Style) -> NodeId {
- (impl) pub fn create_text(&mut self, content: String, style: Style) -> NodeId {
- (impl) pub fn create_input(&mut self, state: InputNodeState, style: Style) -> NodeId {
- (impl) pub fn create_image(&mut self, buffer: ImageBuffer, style: Style) -> NodeId {
- (impl) pub fn create_scroll_view(&mut self, style: Style) -> NodeId {
- (impl) pub fn create_canvas(&mut self, style: Style, painter: CanvasDrawCallback) -> NodeId {
- (impl) pub fn create_portal(&mut self, style: Style) -> NodeId {
- (impl) pub fn create_fragment(&mut self) -> NodeId {
- (impl) pub fn get_node(&self, id: NodeId) -> Option<&SceneNode> {
- (impl) pub fn get_node_mut(&mut self, id: NodeId) -> Option<&mut SceneNode> {
- (impl) pub fn live_node_count(&self) -> usize {
- (impl) pub fn append_child(&mut self, parent: NodeId, child: NodeId) {
- (impl) pub fn replace_children(&mut self, parent: NodeId, new_children: Vec<NodeId>) {
- (impl) pub fn set_style(&mut self, id: NodeId, style: Style) {
- (impl) pub fn set_text(&mut self, id: NodeId, text: String) {
- (impl) pub fn set_scroll_offset(&mut self, id: NodeId, offset: Point) {
- (impl) pub fn set_virtual_scroll(&mut self, id: NodeId, scroll_y: f32, content_height: f32) {
- (impl) pub fn node_screen_bounds(&self, id: NodeId) -> Option<Rect> {
- (impl) pub fn start_transition(&mut self, transition: NodeTransition) {
- (impl) pub fn tick_transitions(&mut self, dt_secs: f32) -> bool {
- (impl) pub fn has_active_transitions(&self) -> bool {
- (impl) pub fn attach_scope(&mut self, id: NodeId, scope: Scope) {
- (impl) pub fn mark_dirty(&mut self, id: NodeId, mask: u16) {
- (impl) pub fn is_node_visible(&self, id: NodeId) -> bool {
- (impl) pub fn collect_paint_damage(&mut self, scale: f32) -> DamageRegion {
- (impl) pub fn dispose_subtree(&mut self, id: NodeId) {
- (impl) pub fn update_focus(&mut self, target: Option<NodeId>) -> Vec<(UiEventHandler, UiEvent)> {
- (impl) pub fn new_tree() -> Self {
- (impl) pub fn set_virtual_scroll(&self, id: NodeId, scroll_y: f32, content_height: f32) {
- (impl) pub fn node_screen_bounds(&self, id: NodeId) -> Option<Rect> {
- (impl) pub fn start_transition(&self, transition: NodeTransition) {
- (impl) pub fn mark_dirty(&self, id: NodeId, mask: u16) {
- (impl) pub fn has_active_transitions(&self) -> bool {
- (impl) pub fn with_read<F, R>(&self, operation: F, fallback: R) -> R where F: FnOnce(&SceneTree) -> R, {
- (impl) pub fn with_write<F, R>(&self, operation: F, fallback: R) -> R where F: FnOnce(&mut SceneTree) -> R, {
- (impl) pub fn bind_text<F>(&self, node_id: NodeId, mut producer: F) -> Effect where F: FnMut() -> String + 'static, {
- (impl) pub fn bind_style<F>(&self, node_id: NodeId, mut producer: F) -> Effect where F: FnMut() -> Style + 'static, {
- (impl) pub fn new(scene: SceneHandle, platform: PlatformKind) -> Self {
- (impl) pub fn view(&mut self, style: Style) -> NodeId {
- (impl) pub fn text(&mut self, content: String, style: Style) -> NodeId {
- (impl) pub fn reactive_text<F>(&mut self, style: Style, producer: F) -> NodeId where F: FnMut() -> String + 'static, {
- (impl) pub fn scroll_view(&mut self, style: Style) -> NodeId {
- (impl) pub fn input(&mut self, state: InputNodeState, style: Style) -> NodeId {
- (impl) pub fn image(&mut self, buffer: ImageBuffer, style: Style) -> NodeId {
- (impl) pub fn canvas<F>(&mut self, style: Style, painter: F) -> NodeId where F: FnMut(Rect, &mut DisplayList) + 'static, {
- (impl) pub fn portal(&mut self, style: Style) -> NodeId {
- (impl) pub fn append(&mut self, parent: NodeId, child: NodeId) {
- (impl) pub fn on_click<F>(&mut self, node_id: NodeId, callback: F) where F: FnMut(&UiEvent) + 'static, {
- (impl) pub fn on_change<F>(&mut self, node_id: NodeId, callback: F) where F: FnMut(&UiEvent) + 'static, {
- (impl) pub fn set_a11y(&mut self, node_id: NodeId, props: A11yProps) {
- (impl) pub fn on_scroll<F>(&mut self, node_id: NodeId, callback: F) where F: FnMut(&UiEvent) + 'static, {
- (impl) pub fn on_pointer_down<F>(&mut self, node_id: NodeId, callback: F) where F: FnMut(&UiEvent) + 'static, {
- (impl) pub fn on_pointer_move<F>(&mut self, node_id: NodeId, callback: F) where F: FnMut(&UiEvent) + 'static, {
- (impl) pub fn on_pointer_up<F>(&mut self, node_id: NodeId, callback: F) where F: FnMut(&UiEvent) + 'static, {
- (impl) pub fn on_hover<F>(&mut self, node_id: NodeId, callback: F) where F: FnMut(&UiEvent) + 'static, {
- (impl) pub fn on_key<F>(&mut self, node_id: NodeId, callback: F) where F: FnMut(&UiEvent) + 'static, {
- (impl) pub fn set_virtual_scroll(&mut self, node_id: NodeId, scroll_y: f32, content_height: f32) {
- (impl) pub fn set_scroll_offset(&mut self, node_id: NodeId, offset: Point) {
- (impl) pub fn start_transition(&mut self, transition: NodeTransition) {
- (impl) pub fn bind_children<F>(&mut self, host: NodeId, mut builder: F) where F: FnMut() -> Vec<NodeId> + 'static, {
- (mod) pub use {r#fn::*, r#struct::*, r#trait::*};
- (struct) pub struct SceneTree {
- (struct) pub struct SceneHandle {
- (struct) pub struct BuildContext {
- (trait) pub trait Mountable {

### style::color
- (const) pub const COLOR_TRANSPARENT: Color = Color {
- (const) pub const COLOR_BLACK: Color = Color {
- (const) pub const COLOR_WHITE: Color = Color {
- (impl) pub const fn rgb(r: u8, g: u8, b: u8) -> Self {
- (impl) pub const fn rgba(r: u8, g: u8, b: u8, a: u8) -> Self {
- (impl) pub const fn hex(rgb: u32) -> Self {
- (impl) pub const fn hexa(rgba: u32) -> Self {
- (impl) pub fn with_alpha(&self, alpha: u8) -> Self {
- (impl) pub fn multiply_alpha(&self, opacity: f32) -> Self {
- (impl) pub fn to_f32_array(&self) -> [f32; 4] {
- (impl) pub fn to_rgba_bytes(&self) -> [u8; 4] {
- (impl) pub fn to_bgra_bytes(&self) -> [u8; 4] {
- (impl) pub fn lerp(&self, other: Self, t: f32) -> Self {
- (impl) pub fn blend_over(&self, dst: Self) -> Self {
- (mod) pub use {r#const::*, r#struct::*};
- (struct) pub struct Color {

### style::layout_prop
- (enum) pub enum Display {
- (enum) pub enum Position {
- (enum) pub enum FlexDirection {
- (enum) pub enum FlexWrap {
- (enum) pub enum JustifyContent {
- (enum) pub enum AlignItems {
- (enum) pub enum AlignSelf {
- (enum) pub enum Overflow {
- (enum) pub enum Breakpoint {
- (impl) pub fn from_width(width: f32) -> Self {
- (impl) pub fn is_compact(&self) -> bool {
- (impl) pub fn top_offset(&self) -> Option<f32> {
- (impl) pub fn right_offset(&self) -> Option<f32> {
- (impl) pub fn bottom_offset(&self) -> Option<f32> {
- (impl) pub fn left_offset(&self) -> Option<f32> {
- (impl) pub fn aspect_ratio_value(&self) -> Option<f32> {
- (mod) pub use {r#enum::*, r#struct::*};
- (struct) pub struct LayoutStyle {

### style::length
- (enum) pub enum Length {
- (impl) pub fn resolve(&self, parent_extent: f32, viewport: Size) -> Option<f32> {
- (impl) pub const fn all(value: f32) -> Self {
- (impl) pub const fn symmetric(vertical: f32, horizontal: f32) -> Self {
- (impl) pub fn horizontal(&self) -> f32 {
- (impl) pub fn vertical(&self) -> f32 {
- (impl) pub const fn all(radius: f32) -> Self {
- (impl) pub fn max_radius(&self) -> f32 {
- (impl) pub fn right(&self) -> f32 {
- (impl) pub fn bottom(&self) -> f32 {
- (impl) pub fn contains(&self, point: Point) -> bool {
- (impl) pub fn intersect(&self, other: Self) -> Option<Self> {
- (impl) pub fn union(&self, other: Self) -> Self {
- (impl) pub fn inset(&self, edges: Edges) -> Self {
- (mod) pub use {r#enum::*, r#struct::*};
- (struct) pub struct Edges {
- (struct) pub struct CornerRadius {
- (struct) pub struct Point {
- (struct) pub struct Size {
- (struct) pub struct Rect {

### style
- (mod) pub use {color::*, layout_prop::*, length::*, paint_prop::*, sheet::*, text_prop::*};

### style::paint_prop
- (enum) pub enum CursorIcon {
- (enum) pub enum PointerEvents {
- (impl) pub fn is_identity(&self) -> bool {
- (impl) pub fn background_color(&self) -> Option<Color> {
- (impl) pub fn background_gradient(&self) -> Option<LinearGradient> {
- (impl) pub fn box_shadow(&self) -> Option<Shadow> {
- (impl) pub fn focus_ring_border(&self) -> Option<Border> {
- (mod) pub use {r#enum::*, r#struct::*};
- (struct) pub struct Border {
- (struct) pub struct Shadow {
- (struct) pub struct LinearGradient {
- (struct) pub struct Transform2D {
- (struct) pub struct PaintStyle {

### style::sheet
- (enum) pub enum ThemeMode {
- (impl) pub fn empty() -> Self {
- (impl) pub fn display(mut self, display: Display) -> Self {
- (impl) pub fn position(mut self, position: Position) -> Self {
- (impl) pub fn row(mut self) -> Self {
- (impl) pub fn column(mut self) -> Self {
- (impl) pub fn grid(mut self, columns: u16) -> Self {
- (impl) pub fn wrap(mut self, wrap: FlexWrap) -> Self {
- (impl) pub fn justify(mut self, justify: JustifyContent) -> Self {
- (impl) pub fn align(mut self, align: AlignItems) -> Self {
- (impl) pub fn flex_grow(mut self, grow: f32) -> Self {
- (impl) pub fn flex_shrink(mut self, shrink: f32) -> Self {
- (impl) pub fn width(mut self, width: Length) -> Self {
- (impl) pub fn height(mut self, height: Length) -> Self {
- (impl) pub fn min_width(mut self, min_width: Length) -> Self {
- (impl) pub fn min_height(mut self, min_height: Length) -> Self {
- (impl) pub fn max_width(mut self, max_width: Length) -> Self {
- (impl) pub fn max_height(mut self, max_height: Length) -> Self {
- (impl) pub fn aspect_ratio(mut self, ratio: f32) -> Self {
- (impl) pub fn gap(mut self, gap: f32) -> Self {
- (impl) pub fn padding(mut self, padding: Edges) -> Self {
- (impl) pub fn margin(mut self, margin: Edges) -> Self {
- (impl) pub fn overflow(mut self, overflow: Overflow) -> Self {
- (impl) pub fn z_index(mut self, z_index: i32) -> Self {
- (impl) pub fn inset( mut self, top: Option<f32>, right: Option<f32>, bottom: Option<f32>, left: Option<f32>, ) -> Self {
- (impl) pub fn background(mut self, color: Color) -> Self {
- (impl) pub fn gradient(mut self, gradient: LinearGradient) -> Self {
- (impl) pub fn border(mut self, width: f32, color: Color) -> Self {
- (impl) pub fn radius(mut self, radius: f32) -> Self {
- (impl) pub fn shadow(mut self, shadow: Shadow) -> Self {
- (impl) pub fn focus_ring(mut self, ring: Border) -> Self {
- (impl) pub fn opacity(mut self, opacity: f32) -> Self {
- (impl) pub fn cursor(mut self, cursor: CursorIcon) -> Self {
- (impl) pub fn pointer_events(mut self, pointer_events: PointerEvents) -> Self {
- (impl) pub fn color(mut self, color: Color) -> Self {
- (impl) pub fn font_size(mut self, size: f32) -> Self {
- (impl) pub fn font_weight(mut self, weight: FontWeight) -> Self {
- (impl) pub fn font_family(mut self, family: FontFamily) -> Self {
- (impl) pub fn text_align(mut self, align: TextAlign) -> Self {
- (impl) pub fn text_overflow(mut self, overflow: TextOverflow) -> Self {
- (impl) pub fn stop_scroll_propagation(mut self, stop: bool) -> Self {
- (impl) pub fn stop_event_propagation(mut self, stop: bool) -> Self {
- (impl) pub fn resolve(&self, breakpoint: Breakpoint) -> Style {
- (mod) pub use {r#enum::*, r#struct::*};
- (struct) pub struct Style {
- (struct) pub struct ResponsiveStyle {

### style::text_prop
- (enum) pub enum FontWeight {
- (enum) pub enum TextAlign {
- (enum) pub enum TextOverflow {
- (enum) pub enum FontFamily {
- (impl) pub const fn numeric(&self) -> u16 {
- (impl) pub const fn is_bold(&self) -> bool {
- (mod) pub use {r#enum::*, r#struct::*};
- (struct) pub struct TextStyle {

### system::a11y
- (enum) pub enum A11yRole {
- (enum) pub enum A11yLiveRegion {
- (enum) pub enum A11yAction {
- (impl) pub const fn native_role_name(&self, platform: PlatformKind) -> &'static str {
- (impl) pub fn checked_state(&self) -> Option<bool> {
- (impl) pub fn from_scene(tree: &SceneTree) -> Self {
- (impl) pub fn find(&self, id: NodeId) -> Option<&A11yNode> {
- (impl) pub fn focused_node(&self) -> Option<NodeId> {
- (impl) pub fn format_summary(&self, platform: PlatformKind) -> String {
- (mod) pub use {r#enum::*, r#struct::*};
- (struct) pub struct A11yProps {
- (struct) pub struct A11yNode {
- (struct) pub struct A11yTree {
- (struct) pub struct A11yAnnouncement {

### system::capabilities
- (const) pub const NATIVE_ACTION_HAPTIC: &str = "haptic";
- (const) pub const NATIVE_ACTION_NOTIFY: &str = "notify";
- (const) pub const NATIVE_ACTION_ISLAND: &str = "island";
- (const) pub const NATIVE_ACTION_PERMISSION: &str = "permission";
- (const) pub const NATIVE_ACTION_FULLSCREEN: &str = "fullscreen";
- (const) pub const NATIVE_ACTION_PROTOCOL: &str = "protocol";
- (enum) pub enum IslandPresentationMode {
- (enum) pub enum HapticStyle {
- (enum) pub enum BiometricKind {
- (fn) pub fn register_native_action_bridge(bridge: NativeActionBridge) {
- (fn) pub fn dispatch_native_action(kind: &str, arg1: &str, arg2: &str) -> bool {
- (impl) pub fn progress(&self) -> Option<u8> {
- (impl) pub fn badge(&self) -> Option<u32> {
- (impl) pub const fn default_island_mode(platform: PlatformKind) -> IslandPresentationMode {
- (impl) pub fn start_live_activity( &mut self, activity_id: String, content: LiveActivityContent, ) -> LiveActivityHandle {
- (impl) pub fn update_live_activity( &mut self, activity_id: &str, content: LiveActivityContent, ) -> bool {
- (impl) pub fn end_live_activity(&mut self, activity_id: &str) -> bool {
- (impl) pub fn trigger_haptic(&mut self, style: HapticStyle) -> bool {
- (impl) pub fn biometric_kind(&self) -> BiometricKind {
- (impl) pub fn configure_tray(&mut self, config: SystemTrayConfig) -> Result<(), PlatformError> {
- (impl) pub fn tray_config(&self) -> Option<&SystemTrayConfig> {
- (impl) pub fn send_notification(&mut self, notification: SystemNotification) {
- (impl) pub fn announce_a11y(&mut self, message: String, politeness: A11yLiveRegion) {
- (impl) pub fn share(&self, payload: &SharePayload) -> Result<String, PlatformError> {
- (mod) pub use {r#const::*, r#enum::*, r#fn::*, r#struct::*, r#type::*};
- (struct) pub struct LiveActivityContent {
- (struct) pub struct LiveActivityHandle {
- (struct) pub struct SystemNotification {
- (struct) pub struct SystemTrayConfig {
- (struct) pub struct SharePayload {
- (struct) pub struct PlatformServiceHub {
- (type) pub type NativeActionBridge = fn(&str, &str, &str) -> bool;

### system
- (mod) pub use {a11y::*, capabilities::*, permissions::*, protocol::*};

### system::permissions
- (enum) pub enum SystemPermission {
- (enum) pub enum PermissionStatus {
- (impl) pub const fn native_key(&self, platform: PlatformKind) -> &'static str {
- (impl) pub const fn is_supported_on(&self, platform: PlatformKind) -> bool {
- (impl) pub fn check(&self, permission: SystemPermission, platform: PlatformKind) -> PermissionStatus {
- (impl) pub fn set_status(&mut self, permission: SystemPermission, status: PermissionStatus) {
- (impl) pub fn request( &mut self, permission: SystemPermission, rationale: String, platform: PlatformKind, ) -> PermissionDescriptor {
- (mod) pub use {r#enum::*, r#struct::*};
- (struct) pub struct PermissionDescriptor {
- (struct) pub struct PermissionManager {

### system::protocol
- (impl) pub fn is_valid_scheme(&self) -> bool {
- (impl) pub fn platform_descriptor(&self, platform: PlatformKind) -> ProtocolManifestEntry {
- (impl) pub fn parse(raw_url: &str) -> Result<Self, PlatformError> {
- (impl) pub fn register( &mut self, registration: ProtocolRegistration, platform: PlatformKind, ) -> Result<ProtocolManifestEntry, PlatformError> {
- (impl) pub fn is_registered(&self, scheme: &str) -> bool {
- (impl) pub fn push_raw_url(&mut self, raw_url: &str) -> Result<DeepLinkEvent, PlatformError> {
- (impl) pub fn drain_links(&mut self) -> Vec<DeepLinkEvent> {
- (mod) pub use r#struct::*;
- (struct) pub struct ProtocolRegistration {
- (struct) pub struct DeepLinkEvent {
- (struct) pub struct ProtocolManifestEntry {
- (struct) pub struct ProtocolRegistry {

### window::config
- (const) pub const DEFAULT_WINDOW_WIDTH: u32 = 1280;
- (const) pub const DEFAULT_WINDOW_HEIGHT: u32 = 800;
- (const) pub const DEFAULT_WINDOW_TITLE: &str = "euv application";
- (const) pub const DEFAULT_REFRESH_RATE_HZ: u32 = 60;
- (enum) pub enum FullscreenMode {
- (enum) pub enum OrientationLock {
- (enum) pub enum StatusBarStyle {
- (impl) pub fn to_edges(&self) -> Edges {
- (impl) pub fn set_size(&mut self, width: u32, height: u32) -> &mut Self {
- (impl) pub fn min_size_value(&self) -> Option<(u32, u32)> {
- (impl) pub fn max_size_value(&self) -> Option<(u32, u32)> {
- (impl) pub fn position_value(&self) -> Option<(i32, i32)> {
- (impl) pub fn preferred_theme_value(&self) -> Option<ThemeMode> {
- (impl) pub fn icon_value(&self) -> Option<ImageBuffer> {
- (impl) pub fn icon_path_value(&self) -> Option<String> {
- (impl) pub fn from_config(id: WindowId, config: &WindowConfig, scale_factor: f32) -> Self {
- (impl) pub fn logical_size(&self) -> Size {
- (impl) pub fn breakpoint(&self) -> Breakpoint {
- (mod) pub use {r#const::*, r#enum::*, r#struct::*};
- (struct) pub struct WindowId {
- (struct) pub struct SafeAreaInsets {
- (struct) pub struct DisplayInfo {
- (struct) pub struct WindowConfig {
- (struct) pub struct WindowState {

### window::control
- (enum) pub enum WindowCommand {
- (impl) pub fn push(&mut self, command: WindowCommand) {
- (impl) pub fn drain(&mut self) -> Vec<WindowCommand> {
- (impl) pub fn is_empty(&self) -> bool {
- (mod) pub use {r#enum::*, r#struct::*, r#trait::*};
- (struct) pub struct WindowCommandQueue {
- (trait) pub trait WindowController {

### window::input
- (enum) pub enum PointerDevice {
- (enum) pub enum PointerButton {
- (enum) pub enum KeyCode {
- (enum) pub enum LifecycleEvent {
- (enum) pub enum ImeEvent {
- (enum) pub enum WindowEvent {
- (enum) pub enum GestureEventKind {
- (impl) pub fn mouse(x: f32, y: f32) -> Self {
- (impl) pub fn touch(finger_id: u64, x: f32, y: f32) -> Self {
- (mod) pub use {r#enum::*, r#struct::*};
- (struct) pub struct Modifiers {
- (struct) pub struct PointerEvent {
- (struct) pub struct KeyEvent {
- (struct) pub struct GestureEvent {

### window
- (mod) pub use {config::*, control::*, input::*};

