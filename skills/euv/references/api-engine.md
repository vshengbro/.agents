# euv-engine full pub API (render engine)

Source: `engine/src/` — auto-extracted from `pub` declarations.

Re-exported at the crate root through the `pub use` chain in `engine/src/lib.rs`. `Engine` is a zero-sized namespace facade; `EngineHandle` is the stateful entity.

### `asset::enum`

- `enum` **`AssetType`** — `pub enum AssetType {`
- `enum` **`AssetState`** — `pub enum AssetState {`

### `asset::fn`

- `fn` **`mark_asset_closure_settled`** — `pub fn mark_asset_closure_settled(store: &Weak<EngineCell<AssetClosureStore>>, slot: usize) {...}`

### `asset::impl`

- `fn` **`get_state`** — `pub fn get_state<U>(&self, url: U) -> Option<AssetState> where U: AsRef<str>, {...}`
- `fn` **`get_image`** — `pub fn get_image<U>(&self, url: U) -> Option<HtmlImageElement> where U: AsRef<str>, {...}`
- `fn` **`is_all_loaded`** — `pub fn is_all_loaded(&self) -> bool {...}`
- `fn` **`loaded_count`** — `pub fn loaded_count(&self) -> usize {...}`
- `fn` **`clear`** — `pub fn clear(&mut self) {...}`
- `fn` **`load_image`** — `pub fn load_image(&mut self, url: String) {...}`
- `fn` **`pending_count`** — `pub fn pending_count(&self) -> u32 {...}`
- `fn` **`update`** — `pub fn update(&mut self, delta_time: f64) {...}`
- `fn` **`collect`** — `pub fn collect(&mut self) {...}`
- `fn` **`is_all_loaded`** — `pub fn is_all_loaded(&self) -> bool {...}`
- `fn` **`get_image`** — `pub fn get_image<U>(&self, url: U) -> Option<HtmlImageElement> where U: AsRef<str>, {...}`
- `fn` **`progress`** — `pub fn progress(&self) -> f64 {...}`
- `fn` **`create_image_element`** — `pub fn create_image_element<U>(url: U) -> Option<HtmlImageElement> where U: AsRef<str>, {...}`

### `asset::struct`

- `struct` **`AssetEntry`** — `pub struct AssetEntry {`
- `struct` **`AssetCache`** — `pub struct AssetCache {`
- `struct` **`AssetLoader`** — `pub struct AssetLoader {`
- `struct` **`AssetClosureStore`** — `pub struct AssetClosureStore {`

### `asset::type`

- `type` **`AssetClosures`** — `pub type AssetClosures = Rc<EngineCell<AssetClosureStore>>;`
- `type` **`AssetPending`** — `pub type AssetPending = Rc<EngineCell<u32>>;`

### `audio::enum`

- `enum` **`AudioPlayState`** — `pub enum AudioPlayState {`

### `audio::impl`

- `fn` **`create`** — `pub fn create() -> Option<GameAudioContext> {...}`
- `fn` **`apply_master_volume`** — `pub fn apply_master_volume(&self, volume: f64) {...}`
- `fn` **`resume`** — `pub fn resume(&self) {...}`
- `fn` **`suspend`** — `pub fn suspend(&self) {...}`
- `fn` **`close`** — `pub fn close(&self) {...}`
- `fn` **`sample_rate`** — `pub fn sample_rate(&self) -> f64 {...}`
- `fn` **`current_time`** — `pub fn current_time(&self) -> f64 {...}`
- `fn` **`create`** — `pub fn create(buffer: AudioBuffer) -> AudioClip {...}`
- `fn` **`play`** — `pub fn play(&mut self, audio_context: &GameAudioContext) {...}`
- `fn` **`stop`** — `pub fn stop(&mut self) {...}`
- `fn` **`update_looping`** — `pub fn update_looping(&mut self, looping: bool) {...}`
- `fn` **`update_volume`** — `pub fn update_volume(&mut self, volume: f64) {...}`
- `fn` **`update_playback_rate`** — `pub fn update_playback_rate(&mut self, rate: f64) {...}`
- `fn` **`duration`** — `pub fn duration(&self) -> f64 {...}`
- `fn` **`channel_count`** — `pub fn channel_count(&self) -> u32 {...}`

### `audio::struct`

- `struct` **`GameAudioContext`** — `pub struct GameAudioContext {`
- `struct` **`AudioClip`** — `pub struct AudioClip {`

### `cell::impl`

- `fn` **`get_inner`** — `pub fn get_inner(&self) -> &UnsafeCell<T> {...}`
- `fn` **`get_inner`** — `pub fn get_inner(&self) -> &UnsafeCell<Option<T>> {...}`
- `fn` **`set_inner`** — `pub fn set_inner(&mut self, val: UnsafeCell<Option<T>>) -> UnsafeCell<Option<T>> {...}`
- `fn` **`new`** — `pub fn new(value: T) -> Self where T: Sized, {...}`
- `fn` **`get_mut`** — `pub fn get_mut(&self) -> &'static mut T {...}`
- `fn` **`get`** — `pub fn get(&self) -> &'static T {...}`
- `fn` **`new`** — `pub const fn new() -> Self {...}`
- `fn` **`try_get`** — `pub fn try_get(&self) -> Option<&'static T> {...}`
- `fn` **`try_get_mut`** — `pub fn try_get_mut(&self) -> Option<&'static mut T> {...}`
- `fn` **`try_set`** — `pub fn try_set(&self, value: T) -> Result<(), T> {...}`
- `fn` **`try_take`** — `pub fn try_take(&self) -> Option<T> {...}`
- `fn` **`try_replace`** — `pub fn try_replace(&self, value: T) -> Option<T> {...}`

### `cell::struct`

- `struct` **`EngineCell`** — `pub struct EngineCell<T: ?Sized> {`
- `struct` **`MaybeEngineCell`** — `pub struct MaybeEngineCell<T> {`

### `collider::enum`

- `enum` **`ColliderShape`** — `pub enum ColliderShape {`
- `enum` **`ColliderShape3D`** — `pub enum ColliderShape3D {`

### `collider::impl`

- `fn` **`from_center`** — `pub fn from_center(center: Vector2D, width: f64, height: f64) -> AabbCollider {...}`
- `fn` **`collide_with_aabb`** — `pub fn collide_with_aabb(&self, other: &AabbCollider) -> Option<CollisionResult> {...}`
- `fn` **`collide_with_circle`** — `pub fn collide_with_circle(&self, circle: &CircleCollider) -> Option<CollisionResult> {...}`
- `fn` **`from_center`** — `pub fn from_center(center: Vector2D, radius: f64) -> CircleCollider {...}`
- `fn` **`collide_with_circle`** — `pub fn collide_with_circle(&self, other: &CircleCollider) -> Option<CollisionResult> {...}`
- `fn` **`from_center`** — `pub fn from_center(center: Vector3D, width: f64, height: f64, depth: f64) -> AabbCollider3D {...}`
- `fn` **`collide_with_aabb`** — `pub fn collide_with_aabb(&self, other: &AabbCollider3D) -> Option<CollisionResult3D> {...}`
- `fn` **`collide_with_sphere`** — `pub fn collide_with_sphere(&self, sphere: &SphereCollider3D) -> Option<CollisionResult3D> {...}`
- `fn` **`from_center`** — `pub fn from_center(center: Vector3D, radius: f64) -> SphereCollider3D {...}`
- `fn` **`collide_with_sphere`** — `pub fn collide_with_sphere(&self, other: &SphereCollider3D) -> Option<CollisionResult3D> {...}`
- `fn` **`broad_phase`** — `pub fn broad_phase(a: AABB3D, b: AABB3D) -> bool {...}`

### `collider::struct`

- `struct` **`CollisionResult`** — `pub struct CollisionResult {`
- `struct` **`AabbCollider`** — `pub struct AabbCollider {`
- `struct` **`CircleCollider`** — `pub struct CircleCollider {`
- `struct` **`CollisionResult3D`** — `pub struct CollisionResult3D {`
- `struct` **`AabbCollider3D`** — `pub struct AabbCollider3D {`
- `struct` **`SphereCollider3D`** — `pub struct SphereCollider3D {`

### `collider::trait`

- `trait` **`Collider`** — `pub trait Collider {`
- `trait` **`Collider3D`** — `pub trait Collider3D {`

### `config::enum`

- `enum` **`RenderBackendType`** — `pub enum RenderBackendType {`
- `enum` **`GpuPowerPreference`** — `pub enum GpuPowerPreference {`

### `config::impl`

- `fn` **`canvas2d`** — `pub fn canvas2d<S>(canvas_selector: S, width: f64, height: f64) -> RenderConfig where S: AsRef<str>, {...}`
- `fn` **`webgpu`** — `pub fn webgpu<S>(canvas_selector: S, width: f64, height: f64) -> RenderConfig where S: AsRef<str>, {...}`
- `fn` **`webgl`** — `pub fn webgl<S>(canvas_selector: S, width: f64, height: f64) -> RenderConfig where S: AsRef<str>, {...}`
- `fn` **`create`** — `pub fn create(render: RenderConfig) -> EngineConfig {...}`
- `fn` **`with_scheduler`** — `pub fn with_scheduler(mut self, scheduler: SchedulerConfig) -> EngineConfig {...}`
- `fn` **`to_web_sys_string`** — `pub fn to_web_sys_string(&self) -> &'static str {...}`

### `config::struct`

- `struct` **`RenderConfig`** — `pub struct RenderConfig {`
- `struct` **`EngineConfig`** — `pub struct EngineConfig {`

### `easing::enum`

- `enum` **`Easing`** — `pub enum Easing {`

### `easing::impl`

- `fn` **`evaluate`** — `pub fn evaluate(&self, t: f64) -> f64 {...}`
- `fn` **`interpolate`** — `pub fn interpolate(&self, start: f64, end: f64, t: f64) -> f64 {...}`

### `engine::impl`

- `fn` **`new_handle`** — `pub fn new_handle(config: EngineConfig) -> EngineHandle {...}`
- `fn` **`run`** — `pub async fn run(config: EngineConfig, handler: TickHandlerRc) -> EngineHandle {...}`
- `fn` **`default_config`** — `pub fn default_config() -> EngineConfig {...}`
- `fn` **`canvas_renderer`** — `pub fn canvas_renderer(config: &RenderConfig) -> Option<CanvasRenderer> {...}`
- `fn` **`webgpu_renderer`** — `pub async fn webgpu_renderer(config: &RenderConfig) -> Result<WebGpuRenderer, WebGpuInitError> {...}`
- `fn` **`webgl_renderer`** — `pub fn webgl_renderer(config: &RenderConfig) -> Result<WebGl2Backend, WebGl2InitError> {...}`
- `fn` **`init_canvas`** — `pub(crate) fn init_canvas(&mut self) -> bool {...}`
- `fn` **`init_webgpu`** — `pub async fn init_webgpu(&mut self) -> Result<WebGpuRenderer, WebGpuInitError> {...}`
- `fn` **`init_webgl`** — `pub(crate) fn init_webgl(&mut self) -> Result<WebGl2Backend, WebGl2InitError> {...}`
- `fn` **`register_input`** — `pub fn register_input(&mut self) -> Option<InputStateCell> {...}`
- `fn` **`start`** — `pub fn start(&mut self, handler: TickHandlerRc) {...}`
- `fn` **`tasks`** — `pub fn tasks(&self) -> &TaskRegistryRc {...}`
- `fn` **`register_task`** — `pub fn register_task<T>(&self, task: T) -> TaskHandle where T: Updatable + 'static, {...}`
- `fn` **`unregister_task`** — `pub fn unregister_task(&self, handle: &TaskHandle) -> bool {...}`
- `fn` **`register_assets`** — `pub fn register_assets(&mut self) -> AssetLoader {...}`
- `fn` **`asset_loader`** — `pub fn asset_loader(&self) -> Option<AssetLoader> {...}`
- `fn` **`stop`** — `pub fn stop(&self) {...}`
- `fn` **`is_running`** — `pub fn is_running(&self) -> bool {...}`
- `fn` **`has_canvas_renderer`** — `pub fn has_canvas_renderer(&self) -> bool {...}`
- `fn` **`has_webgpu_renderer`** — `pub fn has_webgpu_renderer(&self) -> bool {...}`
- `fn` **`has_webgl_renderer`** — `pub fn has_webgl_renderer(&self) -> bool {...}`

### `engine::struct`

- `struct` **`Engine`** — `pub struct Engine;`
- `struct` **`EngineHandle`** — `pub struct EngineHandle {`

### `entity::enum`

- `enum` **`EntityEvent`** — `pub enum EntityEvent {`

### `entity::impl`

- `fn` **`generate_id`** — `pub fn generate_id() -> u64 {...}`
- `fn` **`create`** — `pub fn create<N>(name: N) -> Entity where N: AsRef<str>, {...}`
- `fn` **`create_at`** — `pub fn create_at(position: Vector2D) -> Entity {...}`
- `fn` **`create_pooled`** — `pub fn create_pooled<N>(name: N, pool: &mut ObjectPool<Entity>) -> Self where N: Into<String>, {...}`
- `fn` **`create_pooled_at`** — `pub fn create_pooled_at(position: Vector2D, pool: &mut ObjectPool<Entity>) -> Self {...}`
- `fn` **`prewarm_pool`** — `pub fn prewarm_pool(count: usize, pool: &mut ObjectPool<Entity>) -> usize {...}`
- `fn` **`release_to_pool`** — `pub fn release_to_pool(entity: &mut Entity, pool: &mut ObjectPool<Entity>) {...}`
- `fn` **`add_component`** — `pub fn add_component(&mut self, component: ComponentRc) {...}`
- `fn` **`remove_component_by_name`** — `pub fn remove_component_by_name<N>(&mut self, name: N) -> Option<ComponentRc> where N: AsRef<str>, {...}`
- `fn` **`get_component_by_name`** — `pub fn get_component_by_name<N>(&self, name: N) -> Option<ComponentRc> where N: AsRef<str>, {...}`
- `fn` **`update`** — `pub fn update(&mut self, delta_time: f64) {...}`
- `fn` **`render`** — `pub fn render(&self, draw_list: &mut DrawList) {...}`
- `fn` **`destroy`** — `pub fn destroy(&mut self) {...}`
- `fn` **`add_tag`** — `pub fn add_tag(&mut self, tag: String) {...}`
- `fn` **`has_tag`** — `pub fn has_tag<T>(&self, tag: T) -> bool where T: AsRef<str>, {...}`
- `fn` **`create`** — `pub fn create() -> EventBus {...}`
- `fn` **`subscribe`** — `pub fn subscribe(&mut self, event_name: String, handler: EventHandler) {...}`
- `fn` **`emit`** — `pub fn emit(&self, event: &EntityEvent) {...}`
- `fn` **`unsubscribe_all`** — `pub fn unsubscribe_all<E>(&mut self, event_name: E) where E: AsRef<str>, {...}`
- `fn` **`handler_count`** — `pub fn handler_count<E>(&self, event_name: E) -> usize where E: AsRef<str>, {...}`

### `entity::static`

- `static` **`NEXT_ENTITY_ID`** — `pub(crate) static NEXT_ENTITY_ID: AtomicU64 = AtomicU64::new(1);`

### `entity::struct`

- `struct` **`Entity`** — `pub struct Entity {`
- `struct` **`EventBus`** — `pub struct EventBus {`

### `entity::trait`

- `trait` **`Lifecycle`** — `pub trait Lifecycle {`
- `trait` **`Component`** — `pub trait Component: Lifecycle {`

### `entity::type`

- `type` **`ComponentRc`** — `pub type ComponentRc = Rc<EngineCell<dyn Component>>;`
- `type` **`EntityRc`** — `pub type EntityRc = Rc<EngineCell<Entity>>;`
- `type` **`EventHandler`** — `pub type EventHandler = Rc<dyn Fn(&EntityEvent)>;`
- `type` **`EventHandlers`** — `pub type EventHandlers = HashMap<String, Vec<EventHandler>>;`

### `input::enum`

- `enum` **`MouseButton`** — `pub enum MouseButton {`
- `enum` **`InputAction`** — `pub enum InputAction {`

### `input::fn`

- `fn` **`apply_axis_deadzone`** — `pub fn apply_axis_deadzone(value: f64) -> f64 {...}`
- `fn` **`compute_pressed_buttons`** — `pub fn compute_pressed_buttons( previous_held: &GamepadButtonSet, values: &[f64], ) -> GamepadButtonSet {...}`
- `fn` **`compute_released_buttons`** — `pub fn compute_released_buttons( previous_held: &GamepadButtonSet, values: &[f64], ) -> GamepadButtonSet {...}`
- `fn` **`compute_held_buttons`** — `pub fn compute_held_buttons(values: &[f64]) -> GamepadButtonSet {...}`
- `fn` **`is_button_down`** — `pub fn is_button_down(value: f64) -> bool {...}`
- `fn` **`read_raw_axis`** — `pub fn read_raw_axis(axes: &[f64], axis: u32) -> f64 {...}`

### `input::impl`

- `fn` **`extract_key_code`** — `pub fn extract_key_code(event: &Event) -> String {...}`
- `fn` **`extract_mouse_button`** — `pub fn extract_mouse_button(event: &Event) -> MouseButton {...}`
- `fn` **`extract_mouse_position`** — `pub fn extract_mouse_position(event: &Event) -> Vector2D {...}`
- `fn` **`attach`** — `pub fn attach( state_cell: InputStateCell, window: &Window, pointer_target: &EventTarget, ) -> InputStateCell {...}`
- `fn` **`attach_keyboard`** — `pub(crate) fn attach_keyboard(state_cell: &InputStateCell, window: &Window) {...}`
- `fn` **`attach_pointer`** — `pub(crate) fn attach_pointer(state_cell: &InputStateCell, target: &EventTarget) {...}`
- `fn` **`press_key`** — `pub fn press_key(&mut self, key_code: String) {...}`
- `fn` **`release_key`** — `pub fn release_key(&mut self, key_code: String) {...}`
- `fn` **`is_key_pressed`** — `pub fn is_key_pressed<K>(&self, key_code: K) -> bool where K: AsRef<str>, {...}`
- `fn` **`is_key_held`** — `pub fn is_key_held<K>(&self, key_code: K) -> bool where K: AsRef<str>, {...}`
- `fn` **`is_key_released`** — `pub fn is_key_released<K>(&self, key_code: K) -> bool where K: AsRef<str>, {...}`
- `fn` **`press_mouse_button`** — `pub fn press_mouse_button(&mut self, button: MouseButton, position: Vector2D) {...}`
- `fn` **`release_mouse_button`** — `pub fn release_mouse_button(&mut self, button: MouseButton) {...}`
- `fn` **`update_mouse_position`** — `pub fn update_mouse_position(&mut self, position: Vector2D) {...}`
- `fn` **`is_mouse_button_pressed`** — `pub fn is_mouse_button_pressed(&self, button: MouseButton) -> bool {...}`
- `fn` **`is_mouse_button_held`** — `pub fn is_mouse_button_held(&self, button: MouseButton) -> bool {...}`
- `fn` **`update_touch`** — `pub fn update_touch(&mut self, identifier: i32, position: Vector2D) {...}`
- `fn` **`start_touch`** — `pub fn start_touch(&mut self, identifier: i32, position: Vector2D) {...}`
- `fn` **`end_touch`** — `pub fn end_touch(&mut self, identifier: i32) {...}`
- `fn` **`primary_touch_position`** — `pub fn primary_touch_position(&self) -> Option<Vector2D> {...}`
- `fn` **`end_frame`** — `pub fn end_frame(&mut self) {...}`
- `fn` **`axis`** — `pub fn axis(&self, axis: u32) -> f64 {...}`
- `fn` **`button_value`** — `pub fn button_value(&self, button: u32) -> f64 {...}`
- `fn` **`is_button_pressed`** — `pub fn is_button_pressed(&self, button: u32) -> bool {...}`
- `fn` **`is_button_held`** — `pub fn is_button_held(&self, button: u32) -> bool {...}`
- `fn` **`is_button_released`** — `pub fn is_button_released(&self, button: u32) -> bool {...}`
- `fn` **`button_action`** — `pub fn button_action(&self, button: u32) -> InputAction {...}`
- `fn` **`axis_pressed`** — `pub fn axis_pressed(&self, axis: u32, threshold: f64) -> bool {...}`
- `fn` **`end_frame`** — `pub fn end_frame(&mut self) {...}`
- `fn` **`state`** — `pub fn state(&self, index: u32) -> Option<&GamepadState> {...}`
- `fn` **`state_mut`** — `pub fn state_mut(&mut self, index: u32) -> Option<&mut GamepadState> {...}`
- `fn` **`is_connected`** — `pub fn is_connected(&self, index: u32) -> bool {...}`
- `fn` **`axis`** — `pub fn axis(&self, index: u32, axis: u32) -> Option<f64> {...}`
- `fn` **`button_value`** — `pub fn button_value(&self, index: u32, button: u32) -> Option<f64> {...}`
- `fn` **`is_button_pressed`** — `pub fn is_button_pressed(&self, index: u32, button: u32) -> bool {...}`
- `fn` **`is_button_held`** — `pub fn is_button_held(&self, index: u32, button: u32) -> bool {...}`
- `fn` **`is_button_released`** — `pub fn is_button_released(&self, index: u32, button: u32) -> bool {...}`
- `fn` **`button_action`** — `pub fn button_action(&self, index: u32, button: u32) -> InputAction {...}`
- `fn` **`connected_count`** — `pub fn connected_count(&self) -> usize {...}`
- `fn` **`end_frame`** — `pub fn end_frame(&mut self) {...}`
- `fn` **`poll`** — `pub fn poll(&mut self, window: &Window) {...}`
- `fn` **`attach`** — `pub fn attach(manager_cell: GamepadManagerCell, window: &Window) -> GamepadManagerCell {...}`
- `fn` **`attach_gamepad`** — `pub(crate) fn attach_gamepad(manager_cell: &GamepadManagerCell, window: &Window) {...}`

### `input::struct`

- `struct` **`Input`** — `pub struct Input;`
- `struct` **`InputState`** — `pub struct InputState {`
- `struct` **`GamepadState`** — `pub struct GamepadState {`
- `struct` **`GamepadManager`** — `pub struct GamepadManager {`

### `input::type`

- `type` **`KeyStateSet`** — `pub(crate) type KeyStateSet = HashSet<String>;`
- `type` **`TouchPointMap`** — `pub(crate) type TouchPointMap = HashMap<i32, Vector2D>;`
- `type` **`InputStateCell`** — `pub type InputStateCell = Rc<EngineCell<InputState>>;`
- `type` **`GamepadButtonSet`** — `pub type GamepadButtonSet = HashSet<u32>;`
- `type` **`GamepadIndexSet`** — `pub(crate) type GamepadIndexSet = HashSet<u32>;`
- `type` **`GamepadStateMap`** — `pub(crate) type GamepadStateMap = HashMap<u32, GamepadState>;`
- `type` **`GamepadManagerCell`** — `pub(crate) type GamepadManagerCell = Rc<EngineCell<GamepadManager>>;`

### `lighting::enum`

- `enum` **`LightType`** — `pub enum LightType {`
- `enum` **`MaterialKind`** — `pub enum MaterialKind {`

### `lighting::fn`

- `fn` **`compute_lambert`** — `pub fn compute_lambert(light: &Light, normal: Vector3D, material: &Material) -> Vector3D {...}`
- `fn` **`lambert_term`** — `pub(crate) fn lambert_term( sample: &LightSample, normal: Vector3D, material: &Material, ) -> Vector3D {...}`
- `fn` **`compute_phong`** — `pub fn compute_phong( light: &Light, normal: Vector3D, view_dir: Vector3D, material: &Material, ) -> Vector3D {...}`
- `fn` **`phong_specular_term`** — `pub(crate) fn phong_specular_term( sample: &LightSample, normal: Vector3D, view_dir: Vector3D, material: &Material, ) -> Vector3D {...}`
- `fn` **`phong_specular_factor`** — `pub(crate) fn phong_specular_factor( light_dir: Vector3D, normal: Vector3D, view_dir: Vector3D, shininess: f64, ) -> f64 {...}`
- `fn` **`apply_falloff`** — `pub fn apply_falloff(distance: f64, falloff: f64) -> f64 {...}`
- `fn` **`apply_schlick_fresnel`** — `pub fn apply_schlick_fresnel(light_dir: Vector3D, view_dir: Vector3D, normal: Vector3D) -> f64 {...}`
- `fn` **`unit_vector`** — `pub(crate) fn unit_vector(vector: Vector3D) -> Vector3D {...}`
- `fn` **`unit_vector_and_length`** — `pub(crate) fn unit_vector_and_length(vector: Vector3D) -> (Vector3D, f64) {...}`
- `fn` **`light_reaches_position`** — `pub(crate) fn light_reaches_position(light: &Light, light_dir: Vector3D) -> bool {...}`
- `fn` **`ray_sphere_intersect`** — `pub fn ray_sphere_intersect( origin: Vector3D, dir: Vector3D, center: Vector3D, radius: f64, ) -> Option<(f64, Vector3D)> {...}`
- `fn` **`ray_aabb_intersect`** — `pub fn ray_aabb_intersect( origin: Vector3D, dir: Vector3D, aabb_min: Vector3D, aabb_max: Vector3D, ) -> Option<(f64, f64, Vector3D)> {...}`
- `fn` **`soft_shadow_factor`** — `pub fn soft_shadow_factor( origin: Vector3D, light_pos: Vector3D, occluders: &[(Vector3D, f64)], ) -> f64 {...}`
- `fn` **`segment_crosses_sphere`** — `pub(crate) fn segment_crosses_sphere( segment: &ShadowSegment, center: Vector3D, radius: f64, ) -> bool {...}`

### `lighting::impl`

- `fn` **`new_directional`** — `pub fn new_directional(direction: Vector3D, color: Vector3D) -> Light {...}`
- `fn` **`new_point`** — `pub fn new_point(position: Vector3D, color: Vector3D, intensity: f64) -> Light {...}`
- `fn` **`new_spot`** — `pub fn new_spot( position: Vector3D, direction: Vector3D, color: Vector3D, intensity: f64, half_angle_rad: f64, ) -> Light {...}`
- `fn` **`lambert`** — `pub fn lambert(albedo: Vector3D) -> Material {...}`
- `fn` **`phong`** — `pub fn phong(albedo: Vector3D, specular: f64, shininess: f64) -> Material {...}`
- `fn` **`pbr`** — `pub fn pbr(albedo: Vector3D) -> Material {...}`
- `fn` **`emissive`** — `pub fn emissive(color: Vector3D) -> Material {...}`
- `fn` **`with_eye`** — `pub fn with_eye(eye: Vector3D) -> LightingUniforms {...}`
- `fn` **`add_light`** — `pub fn add_light(&mut self, light: Light) {...}`
- `fn` **`shade`** — `pub fn shade( &self, position: Vector3D, normal: Vector3D, material: &Material, occluders: &[(Vector3D, f64)], ) -> Vector3D {...}`
- `fn` **`shade_with_visibility`** — `pub fn shade_with_visibility<F>( &self, position: Vector3D, normal: Vector3D, material: &Material, mut visibility: F, ) -> Vector3D where F: FnMut(&Light, Vector3D, f64) -> f64, {...}`

### `lighting::struct`

- `struct` **`Light`** — `pub struct Light {`
- `struct` **`Material`** — `pub struct Material {`
- `struct` **`LightSample`** — `pub(crate) struct LightSample {`
- `struct` **`ShadowSegment`** — `pub(crate) struct ShadowSegment {`
- `struct` **`LightingUniforms`** — `pub struct LightingUniforms {`

### `math::impl`

- `fn` **`clamp`** — `pub fn clamp(value: f64, min: f64, max: f64) -> f64 {...}`
- `fn` **`lerp`** — `pub fn lerp(start: f64, end: f64, factor: f64) -> f64 {...}`
- `fn` **`deg_to_rad`** — `pub fn deg_to_rad(degrees: f64) -> f64 {...}`
- `fn` **`rad_to_deg`** — `pub fn rad_to_deg(radians: f64) -> f64 {...}`
- `fn` **`normalize_angle`** — `pub fn normalize_angle(radians: f64) -> f64 {...}`
- `fn` **`angle_delta`** — `pub fn angle_delta(from: f64, to: f64) -> f64 {...}`
- `fn` **`lerp_angle`** — `pub fn lerp_angle(from: f64, to: f64, factor: f64) -> f64 {...}`
- `fn` **`distance`** — `pub fn distance(a: Vector2D, b: Vector2D) -> f64 {...}`
- `fn` **`distance_squared`** — `pub fn distance_squared(a: Vector2D, b: Vector2D) -> f64 {...}`
- `fn` **`smoothstep`** — `pub fn smoothstep(edge_min: f64, edge_max: f64, value: f64) -> f64 {...}`
- `fn` **`approach`** — `pub fn approach(current: f64, target: f64, max_delta: f64) -> f64 {...}`
- `fn` **`sign`** — `pub fn sign(value: f64) -> f64 {...}`
- `fn` **`wrap`** — `pub fn wrap(value: f64, max: f64) -> f64 {...}`
- `fn` **`sign_or_positive`** — `pub fn sign_or_positive(value: f64) -> f64 {...}`
- `fn` **`distance_3d`** — `pub fn distance_3d(a: Vector3D, b: Vector3D) -> f64 {...}`
- `fn` **`distance_squared_3d`** — `pub fn distance_squared_3d(a: Vector3D, b: Vector3D) -> f64 {...}`
- `fn` **`zero`** — `pub fn zero() -> Vector2D {...}`
- `fn` **`right`** — `pub fn right() -> Vector2D {...}`
- `fn` **`up`** — `pub fn up() -> Vector2D {...}`
- `fn` **`from_angle`** — `pub fn from_angle(radians: f64) -> Vector2D {...}`
- `fn` **`magnitude`** — `pub fn magnitude(&self) -> f64 {...}`
- `fn` **`magnitude_squared`** — `pub fn magnitude_squared(&self) -> f64 {...}`
- `fn` **`normalized`** — `pub fn normalized(&self) -> Vector2D {...}`
- `fn` **`normalize`** — `pub fn normalize(&mut self) {...}`
- `fn` **`dot`** — `pub fn dot(&self, other: Vector2D) -> f64 {...}`
- `fn` **`cross`** — `pub fn cross(&self, other: Vector2D) -> f64 {...}`
- `fn` **`perp`** — `pub fn perp(&self) -> Vector2D {...}`
- `fn` **`angle`** — `pub fn angle(&self) -> f64 {...}`
- `fn` **`angle_to`** — `pub fn angle_to(&self, other: Vector2D) -> f64 {...}`
- `fn` **`rotated`** — `pub fn rotated(&self, radians: f64) -> Vector2D {...}`
- `fn` **`rotate`** — `pub fn rotate(&mut self, radians: f64) {...}`
- `fn` **`distance_to`** — `pub fn distance_to(&self, other: Vector2D) -> f64 {...}`
- `fn` **`distance_squared_to`** — `pub fn distance_squared_to(&self, other: Vector2D) -> f64 {...}`
- `fn` **`direction_to`** — `pub fn direction_to(&self, other: Vector2D) -> Vector2D {...}`
- `fn` **`lerp`** — `pub fn lerp(&self, other: Vector2D, factor: f64) -> Vector2D {...}`
- `fn` **`scale`** — `pub fn scale(&mut self, scalar: f64) {...}`
- `fn` **`scaled`** — `pub fn scaled(&self, scalar: f64) -> Vector2D {...}`
- `fn` **`from_center`** — `pub fn from_center(center: Vector2D, width: f64, height: f64) -> Rect {...}`
- `fn` **`center`** — `pub fn center(&self) -> Vector2D {...}`
- `fn` **`min`** — `pub fn min(&self) -> Vector2D {...}`
- `fn` **`max`** — `pub fn max(&self) -> Vector2D {...}`
- `fn` **`size`** — `pub fn size(&self) -> Vector2D {...}`
- `fn` **`contains`** — `pub fn contains(&self, point: Vector2D) -> bool {...}`
- `fn` **`intersects`** — `pub fn intersects(&self, other: Rect) -> bool {...}`
- `fn` **`broad_phase_alias`** — `pub fn broad_phase_alias(a: Rect, b: Rect) -> bool {...}`
- `fn` **`intersection`** — `pub fn intersection(&self, other: Rect) -> Option<Rect> {...}`
- `fn` **`contains`** — `pub fn contains(&self, point: Vector2D) -> bool {...}`
- `fn` **`intersects`** — `pub fn intersects(&self, other: Circle) -> bool {...}`
- `fn` **`circumference`** — `pub fn circumference(&self) -> f64 {...}`
- `fn` **`area`** — `pub fn area(&self) -> f64 {...}`
- `fn` **`identity`** — `pub fn identity() -> Transform2D {...}`
- `fn` **`translate`** — `pub fn translate(&mut self, offset: Vector2D) {...}`
- `fn` **`rotate`** — `pub fn rotate(&mut self, radians: f64) {...}`
- `fn` **`scale_by`** — `pub fn scale_by(&mut self, factors: Vector2D) {...}`
- `fn` **`apply_to_point`** — `pub fn apply_to_point(&self, point: Vector2D) -> Vector2D {...}`
- `fn` **`from_rgb`** — `pub fn from_rgb(red: u8, green: u8, blue: u8) -> Color {...}`
- `fn` **`to_css_rgba`** — `pub fn to_css_rgba(&self) -> String {...}`
- `fn` **`write_css_rgba`** — `pub fn write_css_rgba(&self, buffer: &mut String) {...}`
- `fn` **`black`** — `pub fn black() -> Color {...}`
- `fn` **`white`** — `pub fn white() -> Color {...}`
- `fn` **`transparent`** — `pub fn transparent() -> Color {...}`
- `fn` **`lerp`** — `pub fn lerp(&self, other: Color, factor: f64) -> Color {...}`
- `fn` **`zero`** — `pub fn zero() -> Vector3D {...}`
- `fn` **`right`** — `pub fn right() -> Vector3D {...}`
- `fn` **`up`** — `pub fn up() -> Vector3D {...}`
- `fn` **`forward`** — `pub fn forward() -> Vector3D {...}`
- `fn` **`magnitude`** — `pub fn magnitude(&self) -> f64 {...}`
- `fn` **`magnitude_squared`** — `pub fn magnitude_squared(&self) -> f64 {...}`
- `fn` **`normalized`** — `pub fn normalized(&self) -> Vector3D {...}`
- `fn` **`normalize`** — `pub fn normalize(&mut self) {...}`
- `fn` **`dot`** — `pub fn dot(&self, other: Vector3D) -> f64 {...}`
- `fn` **`cross`** — `pub fn cross(&self, other: Vector3D) -> Vector3D {...}`
- `fn` **`distance_to`** — `pub fn distance_to(&self, other: Vector3D) -> f64 {...}`
- `fn` **`distance_squared_to`** — `pub fn distance_squared_to(&self, other: Vector3D) -> f64 {...}`
- `fn` **`direction_to`** — `pub fn direction_to(&self, other: Vector3D) -> Vector3D {...}`
- `fn` **`lerp`** — `pub fn lerp(&self, other: Vector3D, factor: f64) -> Vector3D {...}`
- `fn` **`scale`** — `pub fn scale(&mut self, scalar: f64) {...}`
- `fn` **`scaled`** — `pub fn scaled(&self, scalar: f64) -> Vector3D {...}`
- `fn` **`rotated_by`** — `pub fn rotated_by(&self, quaternion: Quaternion) -> Vector3D {...}`
- `fn` **`identity`** — `pub fn identity() -> Quaternion {...}`
- `fn` **`from_axis_angle`** — `pub fn from_axis_angle(axis: Vector3D, angle: f64) -> Quaternion {...}`
- `fn` **`from_euler`** — `pub fn from_euler(yaw: f64, pitch: f64, roll: f64) -> Quaternion {...}`
- `fn` **`magnitude`** — `pub fn magnitude(&self) -> f64 {...}`
- `fn` **`normalized`** — `pub fn normalized(&self) -> Quaternion {...}`
- `fn` **`conjugate`** — `pub fn conjugate(&self) -> Quaternion {...}`
- `fn` **`dot`** — `pub fn dot(&self, other: Quaternion) -> f64 {...}`
- `fn` **`slerp`** — `pub fn slerp(&self, other: Quaternion, factor: f64) -> Quaternion {...}`
- `fn` **`identity`** — `pub fn identity() -> Matrix4x4 {...}`
- `fn` **`translation`** — `pub fn translation(translation: Vector3D) -> Matrix4x4 {...}`
- `fn` **`scaling`** — `pub fn scaling(scale: Vector3D) -> Matrix4x4 {...}`
- `fn` **`rotation`** — `pub fn rotation(quaternion: Quaternion) -> Matrix4x4 {...}`
- `fn` **`perspective`** — `pub fn perspective(fov: f64, aspect: f64, near: f64, far: f64) -> Matrix4x4 {...}`
- `fn` **`orthographic`** — `pub fn orthographic( left: f64, right: f64, bottom: f64, top: f64, near: f64, far: f64, ) -> Matrix4x4 {...}`
- `fn` **`look_at`** — `pub fn look_at(eye: Vector3D, target: Vector3D, up: Vector3D) -> Matrix4x4 {...}`
- `fn` **`multiply`** — `pub fn multiply(&self, other: Matrix4x4) -> Matrix4x4 {...}`
- `fn` **`transform_point`** — `pub fn transform_point(&self, point: Vector3D) -> Vector3D {...}`
- `fn` **`identity`** — `pub fn identity() -> Transform3D {...}`
- `fn` **`translate`** — `pub fn translate(&mut self, offset: Vector3D) {...}`
- `fn` **`rotate`** — `pub fn rotate(&mut self, rotation: Quaternion) {...}`
- `fn` **`scale_by`** — `pub fn scale_by(&mut self, factors: Vector3D) {...}`
- `fn` **`apply_to_point`** — `pub fn apply_to_point(&self, point: Vector3D) -> Vector3D {...}`
- `fn` **`to_matrix`** — `pub fn to_matrix(&self) -> Matrix4x4 {...}`
- `fn` **`from_center`** — `pub fn from_center(center: Vector3D, width: f64, height: f64, depth: f64) -> AABB3D {...}`
- `fn` **`center`** — `pub fn center(&self) -> Vector3D {...}`
- `fn` **`size`** — `pub fn size(&self) -> Vector3D {...}`
- `fn` **`contains`** — `pub fn contains(&self, point: Vector3D) -> bool {...}`
- `fn` **`intersects`** — `pub fn intersects(&self, other: AABB3D) -> bool {...}`
- `fn` **`contains`** — `pub fn contains(&self, point: Vector3D) -> bool {...}`
- `fn` **`intersects`** — `pub fn intersects(&self, other: Sphere) -> bool {...}`
- `fn` **`volume`** — `pub fn volume(&self) -> f64 {...}`
- `fn` **`surface_area`** — `pub fn surface_area(&self) -> f64 {...}`
- `fn` **`from_normal_and_point`** — `pub fn from_normal_and_point(normal: Vector3D, point: Vector3D) -> Plane {...}`
- `fn` **`distance_to_point`** — `pub fn distance_to_point(&self, point: Vector3D) -> f64 {...}`
- `fn` **`normalize`** — `pub fn normalize(&mut self) {...}`
- `fn` **`point_at`** — `pub fn point_at(&self, t: f64) -> Vector3D {...}`
- `fn` **`intersect_sphere`** — `pub fn intersect_sphere(&self, sphere: Sphere) -> Option<f64> {...}`
- `fn` **`intersect_plane`** — `pub fn intersect_plane(&self, plane: Plane) -> Option<f64> {...}`
- `fn` **`intersect_aabb`** — `pub fn intersect_aabb(&self, aabb: AABB3D) -> Option<f64> {...}`

### `math::struct`

- `struct` **`Numeric`** — `pub struct Numeric;`
- `struct` **`Vector2D`** — `pub struct Vector2D {`
- `struct` **`Rect`** — `pub struct Rect {`
- `struct` **`Circle`** — `pub struct Circle {`
- `struct` **`Transform2D`** — `pub struct Transform2D {`
- `struct` **`Color`** — `pub struct Color {`
- `struct` **`Vector3D`** — `pub struct Vector3D {`
- `struct` **`Quaternion`** — `pub struct Quaternion {`
- `struct` **`Matrix4x4`** — `pub struct Matrix4x4 {`
- `struct` **`Transform3D`** — `pub struct Transform3D {`
- `struct` **`AABB3D`** — `pub struct AABB3D {`
- `struct` **`Sphere`** — `pub struct Sphere {`
- `struct` **`Plane`** — `pub struct Plane {`
- `struct` **`Ray3D`** — `pub struct Ray3D {`
- `struct` **`Ray2D`** — `pub struct Ray2D {`

### `math::trait`

- `trait` **`Interpolable`** — `pub trait Interpolable {`
- `trait` **`Vector`** — `pub trait Vector: Copy + Clone + Default + Debug + PartialEq + Add<Output = Self> + Sub<Output = Self> + Mul<f64, Output = Self> + Neg<Output = Self> + AddAssign + SubAssign + MulAssign<f64> {`

### `particle::impl`

- `fn` **`with_seed`** — `pub fn with_seed(seed: u64) -> ParticleRng {...}`
- `fn` **`next_u64`** — `pub fn next_u64(&mut self) -> u64 {...}`
- `fn` **`next_f64`** — `pub fn next_f64(&mut self) -> f64 {...}`
- `fn` **`range`** — `pub fn range(&mut self, min: f64, max: f64) -> f64 {...}`
- `fn` **`create`** — `pub fn create(position: Vector2D, config: ParticleConfig) -> ParticleEmitter {...}`
- `fn` **`with_defaults`** — `pub fn with_defaults(position: Vector2D) -> ParticleEmitter {...}`
- `fn` **`update`** — `pub fn update(&mut self, delta_time: f64) {...}`
- `fn` **`burst`** — `pub fn burst(&mut self, count: usize) {...}`
- `fn` **`render`** — `pub fn render(&self, draw_list: &mut DrawList) {...}`
- `fn` **`alive_count`** — `pub fn alive_count(&self) -> usize {...}`
- `fn` **`quantize`** — `pub(crate) fn quantize(color: &Color) -> u8 {...}`
- `fn` **`clear`** — `pub fn clear(&mut self) {...}`

### `particle::static`

- `static` **`PARTICLE_PALETTE`** — `pub(crate) static PARTICLE_PALETTE: LazyLock<[Color;`

### `particle::struct`

- `struct` **`ParticleRng`** — `pub struct ParticleRng {`
- `struct` **`ParticleConfig`** — `pub struct ParticleConfig {`
- `struct` **`Particle`** — `pub struct Particle {`
- `struct` **`ParticleEmitter`** — `pub struct ParticleEmitter {`

### `physics::enum`

- `enum` **`BodyType`** — `pub enum BodyType {`
- `enum` **`BodyCollider`** — `pub enum BodyCollider {`
- `enum` **`BodyCollider3D`** — `pub enum BodyCollider3D {`

### `physics::impl`

- `fn` **`new_dynamic`** — `pub fn new_dynamic(id: u64, position: Vector2D) -> RigidBody2D {...}`
- `fn` **`new_static`** — `pub fn new_static(id: u64, position: Vector2D) -> RigidBody2D {...}`
- `fn` **`apply_force`** — `pub fn apply_force(&mut self, force: Vector2D) {...}`
- `fn` **`apply_impulse`** — `pub fn apply_impulse(&mut self, impulse: Vector2D) {...}`
- `fn` **`update_mass`** — `pub fn update_mass(&mut self, mass: f64) {...}`
- `fn` **`is_dynamic`** — `pub fn is_dynamic(&self) -> bool {...}`
- `fn` **`update_collider`** — `pub fn update_collider(&mut self, collider: BodyCollider) {...}`
- `fn` **`bounding_box`** — `pub fn bounding_box(&self) -> Option<Rect> {...}`
- `fn` **`with_config`** — `pub fn with_config(config: PhysicsConfig) -> PhysicsWorld2D {...}`
- `fn` **`add_body`** — `pub fn add_body(&mut self, body: RigidBody2D) {...}`
- `fn` **`remove_body`** — `pub fn remove_body(&mut self, id: u64) {...}`
- `fn` **`get_body`** — `pub fn get_body(&self, id: u64) -> Option<&RigidBody2D> {...}`
- `fn` **`get_body_mut`** — `pub fn get_body_mut(&mut self, id: u64) -> Option<&mut RigidBody2D> {...}`
- `fn` **`step`** — `pub fn step(&mut self, delta_time: f64) {...}`
- `fn` **`new_dynamic`** — `pub fn new_dynamic(id: u64, position: Vector3D) -> RigidBody3D {...}`
- `fn` **`new_static`** — `pub fn new_static(id: u64, position: Vector3D) -> RigidBody3D {...}`
- `fn` **`apply_force`** — `pub fn apply_force(&mut self, force: Vector3D) {...}`
- `fn` **`apply_torque`** — `pub fn apply_torque(&mut self, torque: Vector3D) {...}`
- `fn` **`apply_impulse`** — `pub fn apply_impulse(&mut self, impulse: Vector3D) {...}`
- `fn` **`update_mass`** — `pub fn update_mass(&mut self, mass: f64) {...}`
- `fn` **`update_inertia`** — `pub fn update_inertia(&mut self, inertia: f64) {...}`
- `fn` **`is_dynamic`** — `pub fn is_dynamic(&self) -> bool {...}`
- `fn` **`update_collider`** — `pub fn update_collider(&mut self, collider: BodyCollider3D) {...}`
- `fn` **`bounding_box`** — `pub fn bounding_box(&self) -> Option<AABB3D> {...}`
- `fn` **`with_config`** — `pub fn with_config(config: PhysicsConfig3D) -> PhysicsWorld3D {...}`
- `fn` **`add_body`** — `pub fn add_body(&mut self, body: RigidBody3D) {...}`
- `fn` **`remove_body`** — `pub fn remove_body(&mut self, id: u64) {...}`
- `fn` **`get_body`** — `pub fn get_body(&self, id: u64) -> Option<&RigidBody3D> {...}`
- `fn` **`get_body_mut`** — `pub fn get_body_mut(&mut self, id: u64) -> Option<&mut RigidBody3D> {...}`
- `fn` **`step`** — `pub fn step(&mut self, delta_time: f64) {...}`

### `physics::struct`

- `struct` **`PhysicsConfig`** — `pub struct PhysicsConfig {`
- `struct` **`RigidBody2D`** — `pub struct RigidBody2D {`
- `struct` **`PhysicsWorld2D`** — `pub struct PhysicsWorld2D {`
- `struct` **`PhysicsConfig3D`** — `pub struct PhysicsConfig3D {`
- `struct` **`RigidBody3D`** — `pub struct RigidBody3D {`
- `struct` **`PhysicsWorld3D`** — `pub struct PhysicsWorld3D {`

### `pool::impl`

- `fn` **`new`** — `pub fn new(initial: Vec<T>) -> ObjectPool<T> {...}`
- `fn` **`empty`** — `pub fn empty() -> ObjectPool<T> {...}`
- `fn` **`get_active`** — `pub fn get_active(&self) -> usize {...}`
- `fn` **`set_active`** — `pub fn set_active(&mut self, active: usize) {...}`
- `fn` **`get_free`** — `pub fn get_free(&self) -> &Vec<T> {...}`
- `fn` **`get_mut_free`** — `pub fn get_mut_free(&mut self) -> &mut Vec<T> {...}`
- `fn` **`available`** — `pub fn available(&self) -> usize {...}`
- `fn` **`len`** — `pub fn len(&self) -> usize {...}`
- `fn` **`is_empty`** — `pub fn is_empty(&self) -> bool {...}`
- `fn` **`acquire`** — `pub fn acquire(&mut self) -> Option<T> {...}`
- `fn` **`acquire_with`** — `pub fn acquire_with<F>(&mut self, mut make: F) -> T where F: FnMut() -> T, {...}`
- `fn` **`release`** — `pub fn release(&mut self, value: T) {...}`
- `fn` **`prewarm`** — `pub fn prewarm<F>(&mut self, count: usize, mut make: F) -> usize where F: FnMut() -> T, {...}`
- `fn` **`clear`** — `pub fn clear(&mut self) -> usize {...}`

### `pool::struct`

- `struct` **`ObjectPool`** — `pub struct ObjectPool<T> {`

### `scene::impl`

- `fn` **`create_scene`** — `pub fn create_scene<T>(scene: T) -> SceneRc where T: Scene + 'static, {...}`
- `fn` **`register`** — `pub fn register(&mut self, name: String, scene: SceneRc) {...}`
- `fn` **`unregister`** — `pub fn unregister<N>(&mut self, name: N) where N: AsRef<str>, {...}`
- `fn` **`switch_to`** — `pub fn switch_to<N>(&mut self, name: N) -> bool where N: AsRef<str>, {...}`
- `fn` **`request_transition`** — `pub fn request_transition(&mut self, name: String) {...}`
- `fn` **`process_pending_transition`** — `pub fn process_pending_transition(&mut self) {...}`
- `fn` **`update`** — `pub fn update(&mut self, delta_time: f64) {...}`
- `fn` **`render`** — `pub fn render(&mut self, context: &CanvasRenderingContext2d) {...}`
- `fn` **`has_scene`** — `pub fn has_scene<N>(&self, name: N) -> bool where N: AsRef<str>, {...}`
- `fn` **`current_name`** — `pub fn current_name(&self) -> Option<&str> {...}`

### `scene::struct`

- `struct` **`SceneManager`** — `pub struct SceneManager {`

### `scene::trait`

- `trait` **`Scene`** — `pub trait Scene: Lifecycle {`

### `scene::type`

- `type` **`SceneRc`** — `pub type SceneRc = Rc<EngineCell<dyn Scene>>;`

### `scheduler::impl`

- `fn` **`current_time`** — `pub fn current_time() -> f64 {...}`
- `fn` **`tick`** — `pub fn tick( &mut self, config: &SchedulerConfig, handler: &TickHandlerRc, tasks: Option<&TaskRegistryRc>, input_cell: Option<&InputStateCell>, ) {...}`
- `fn` **`register`** — `pub fn register<T>(&mut self, task: T) -> TaskHandle where T: Updatable + 'static, {...}`
- `fn` **`unregister`** — `pub fn unregister(&mut self, handle: &TaskHandle) -> bool {...}`
- `fn` **`update_all`** — `pub fn update_all(&mut self, delta_time: f64) {...}`
- `fn` **`len`** — `pub fn len(&self) -> usize {...}`
- `fn` **`is_empty`** — `pub fn is_empty(&self) -> bool {...}`
- `fn` **`clear`** — `pub fn clear(&mut self) {...}`
- `fn` **`stop`** — `pub fn stop(&self) {...}`
- `fn` **`is_running`** — `pub fn is_running(&self) -> bool {...}`
- `fn` **`update_count`** — `pub fn update_count(&self) -> u64 {...}`
- `fn` **`frame_count`** — `pub fn frame_count(&self) -> u64 {...}`
- `fn` **`register_task`** — `pub fn register_task<T>(registry: &TaskRegistryRc, task: T) -> TaskHandle where T: Updatable + 'static, {...}`
- `fn` **`start`** — `pub fn start( config: SchedulerConfig, handler: TickHandlerRc, tasks: Option<&TaskRegistryRc>, input_cell: Option<&InputStateCell>, ) -> SchedulerHandle {...}`

### `scheduler::struct`

- `struct` **`SchedulerConfig`** — `pub struct SchedulerConfig {`
- `struct` **`SchedulerState`** — `pub struct SchedulerState {`
- `struct` **`SchedulerHandle`** — `pub struct SchedulerHandle {`
- `struct` **`TaskRegistry`** — `pub struct TaskRegistry {`
- `struct` **`TaskHandle`** — `pub struct TaskHandle {`

### `scheduler::trait`

- `trait` **`TickHandler`** — `pub trait TickHandler {`
- `trait` **`Updatable`** — `pub trait Updatable {`

### `scheduler::type`

- `type` **`TickHandlerRc`** — `pub type TickHandlerRc = Rc<EngineCell<dyn TickHandler>>;`
- `type` **`RafClosureCell`** — `pub type RafClosureCell = Rc<MaybeEngineCell<Closure<dyn FnMut()>>>;`
- `type` **`TaskRegistryRc`** — `pub type TaskRegistryRc = Rc<EngineCell<TaskRegistry>>;`

### `spatial::impl`

- `fn` **`create`** — `pub fn create(cell_size: f64) -> SpatialHashGrid2D {...}`
- `fn` **`with_default_size`** — `pub fn with_default_size() -> SpatialHashGrid2D {...}`
- `fn` **`insert`** — `pub fn insert(&mut self, index: usize, min: Vector2D, max: Vector2D) {...}`
- `fn` **`query`** — `pub fn query(&self, min: Vector2D, max: Vector2D) -> Vec<usize> {...}`
- `fn` **`clear`** — `pub fn clear(&mut self) {...}`
- `fn` **`query_into`** — `pub fn query_into( &self, min: Vector2D, max: Vector2D, out: &mut Vec<usize>, seen: &mut HashSet<usize>, ) {...}`
- `fn` **`create`** — `pub fn create(cell_size: f64) -> SpatialHashGrid3D {...}`
- `fn` **`with_default_size`** — `pub fn with_default_size() -> SpatialHashGrid3D {...}`
- `fn` **`insert`** — `pub fn insert(&mut self, index: usize, min: Vector3D, max: Vector3D) {...}`
- `fn` **`query`** — `pub fn query(&self, min: Vector3D, max: Vector3D) -> Vec<usize> {...}`
- `fn` **`clear`** — `pub fn clear(&mut self) {...}`
- `fn` **`query_into`** — `pub fn query_into( &self, min: Vector3D, max: Vector3D, out: &mut Vec<usize>, seen: &mut HashSet<usize>, ) {...}`
- `fn` **`create`** — `pub fn create( bounds_min: Vector2D, bounds_max: Vector2D, capacity: usize, max_depth: usize, ) -> QuadTree2D {...}`
- `fn` **`with_default_size`** — `pub fn with_default_size() -> QuadTree2D {...}`
- `fn` **`with_half_extent`** — `pub fn with_half_extent(half_extent: f64) -> QuadTree2D {...}`
- `fn` **`len`** — `pub fn len(&self) -> usize {...}`
- `fn` **`is_empty`** — `pub fn is_empty(&self) -> bool {...}`
- `fn` **`bounds`** — `pub fn bounds(&self) -> (Vector2D, Vector2D) {...}`
- `fn` **`insert`** — `pub fn insert(&mut self, index: usize, min: Vector2D, max: Vector2D) {...}`
- `fn` **`query`** — `pub fn query(&self, min: Vector2D, max: Vector2D) -> Vec<usize> {...}`
- `fn` **`query_into`** — `pub fn query_into( &self, min: Vector2D, max: Vector2D, out: &mut Vec<usize>, seen: &mut HashSet<usize>, ) {...}`
- `fn` **`clear`** — `pub fn clear(&mut self) {...}`
- `fn` **`boxes_overlap`** — `pub fn boxes_overlap( a_min: Vector2D, a_max: Vector2D, b_min: Vector2D, b_max: Vector2D, ) -> bool {...}`

### `spatial::struct`

- `struct` **`SpatialHashGrid2D`** — `pub struct SpatialHashGrid2D {`
- `struct` **`SpatialHashGrid3D`** — `pub struct SpatialHashGrid3D {`
- `struct` **`QuadTreeEntry2D`** — `pub struct QuadTreeEntry2D {`
- `struct` **`QuadTreeNode2D`** — `pub struct QuadTreeNode2D {`
- `struct` **`QuadTree2D`** — `pub struct QuadTree2D {`

### `spatial::type`

- `type` **`CellKey2D`** — `pub type CellKey2D = (i32, i32);`
- `type` **`CellKey3D`** — `pub type CellKey3D = (i32, i32, i32);`
- `type` **`CellEntries`** — `pub type CellEntries = Vec<usize>;`
- `type` **`SpatialCellMap2D`** — `pub type SpatialCellMap2D = HashMap<CellKey2D, CellEntries>;`
- `type` **`SpatialCellMap3D`** — `pub type SpatialCellMap3D = HashMap<CellKey3D, CellEntries>;`
- `type` **`QuadTreeChildren2D`** — `pub type QuadTreeChildren2D = [usize;`
- `type` **`QuadTreeEntryList2D`** — `pub type QuadTreeEntryList2D = Vec<QuadTreeEntry2D>;`
- `type` **`QuadTreeNodeList2D`** — `pub type QuadTreeNodeList2D = Vec<QuadTreeNode2D>;`
- `type` **`QuadTreeNodeStack2D`** — `pub type QuadTreeNodeStack2D = Vec<usize>;`

### `sprite::enum`

- `enum` **`AnimationMode`** — `pub enum AnimationMode {`
- `enum` **`AnimationState`** — `pub enum AnimationState {`

### `sprite::impl`

- `fn` **`from_image`** — `pub fn from_image(image: HtmlImageElement, frame_width: f64, frame_height: f64) -> SpriteSheet {...}`
- `fn` **`frame_source`** — `pub(crate) fn frame_source(&self, index: u32) -> Rect {...}`
- `fn` **`frame`** — `pub fn frame(&self, index: u32) -> SpriteFrame {...}`
- `fn` **`animation`** — `pub fn animation( &self, name: &str, start: u32, end: u32, mode: AnimationMode, ) -> SpriteAnimation {...}`
- `fn` **`draw_frame`** — `pub fn draw_frame( &self, context: &CanvasRenderingContext2d, frame_index: u32, transform: &Transform2D, ) {...}`
- `fn` **`create`** — `pub fn create() -> Animator {...}`
- `fn` **`play`** — `pub fn play(&mut self, animation: SpriteAnimation) {...}`
- `fn` **`pause`** — `pub fn pause(&mut self) {...}`
- `fn` **`resume`** — `pub fn resume(&mut self) {...}`
- `fn` **`stop`** — `pub fn stop(&mut self) {...}`
- `fn` **`update`** — `pub fn update(&mut self, delta_time: f64) {...}`
- `fn` **`current_frame_source`** — `pub fn current_frame_source(&self) -> Option<Rect> {...}`
- `fn` **`draw`** — `pub fn draw( &self, context: &CanvasRenderingContext2d, sheet: &SpriteSheet, transform: &Transform2D, ) {...}`
- `fn` **`get_top_left`** — `pub fn get_top_left(&self) -> Rect {...}`
- `fn` **`get_top`** — `pub fn get_top(&self) -> Rect {...}`
- `fn` **`get_top_right`** — `pub fn get_top_right(&self) -> Rect {...}`
- `fn` **`get_left`** — `pub fn get_left(&self) -> Rect {...}`
- `fn` **`get_center`** — `pub fn get_center(&self) -> Rect {...}`
- `fn` **`get_right`** — `pub fn get_right(&self) -> Rect {...}`
- `fn` **`get_bottom_left`** — `pub fn get_bottom_left(&self) -> Rect {...}`
- `fn` **`get_bottom`** — `pub fn get_bottom(&self) -> Rect {...}`
- `fn` **`get_bottom_right`** — `pub fn get_bottom_right(&self) -> Rect {...}`
- `fn` **`to_vec`** — `pub fn to_vec(&self) -> Vec<Rect> {...}`
- `fn` **`source_rects`** — `pub fn source_rects(&self, source: Rect) -> NineSliceRects {...}`
- `fn` **`dest_rects`** — `pub fn dest_rects(&self, dest: Rect) -> NineSliceRects {...}`
- `fn` **`from_image`** — `pub fn from_image(image: HtmlImageElement, border: f64) -> NineSlice {...}`
- `fn` **`source_rects`** — `pub fn source_rects(&self) -> NineSliceRects {...}`
- `fn` **`dest_rects`** — `pub fn dest_rects(&self, dest: Rect) -> NineSliceRects {...}`
- `fn` **`draw_into`** — `pub fn draw_into(&self, context: &CanvasRenderingContext2d, dest: Rect) {...}`
- `fn` **`record`** — `pub fn record( &self, list: &mut DrawList, dest_position: Vector2D, dest_width: f64, dest_height: f64, ) {...}`
- `fn` **`insert`** — `pub fn insert(&mut self, name: &str, region: Rect) {...}`
- `fn` **`get`** — `pub fn get(&self, name: &str) -> Option<Rect> {...}`
- `fn` **`contains`** — `pub fn contains(&self, name: &str) -> bool {...}`
- `fn` **`len`** — `pub fn len(&self) -> usize {...}`
- `fn` **`is_empty`** — `pub fn is_empty(&self) -> bool {...}`
- `fn` **`names`** — `pub fn names(&self) -> Vec<String> {...}`
- `fn` **`create`** — `pub fn create(image: HtmlImageElement) -> SpriteAtlas {...}`
- `fn` **`insert`** — `pub fn insert(&mut self, name: &str, region: Rect) {...}`
- `fn` **`get`** — `pub fn get(&self, name: &str) -> Option<Rect> {...}`
- `fn` **`contains`** — `pub fn contains(&self, name: &str) -> bool {...}`
- `fn` **`len`** — `pub fn len(&self) -> usize {...}`
- `fn` **`is_empty`** — `pub fn is_empty(&self) -> bool {...}`
- `fn` **`uv`** — `pub fn uv(&self, region: Rect) -> UvRect {...}`
- `fn` **`normalize_uv`** — `pub fn normalize_uv(region: Rect, width: f64, height: f64) -> UvRect {...}`
- `fn` **`draw`** — `pub fn draw(&self, context: &CanvasRenderingContext2d, name: &str, dest: Rect) {...}`
- `fn` **`record`** — `pub fn record( &self, list: &mut DrawList, name: &str, dest_position: Vector2D, dest_width: f64, dest_height: f64, ) {...}`

### `sprite::struct`

- `struct` **`SpriteFrame`** — `pub struct SpriteFrame {`
- `struct` **`SpriteSheet`** — `pub struct SpriteSheet {`
- `struct` **`SpriteAnimation`** — `pub struct SpriteAnimation {`
- `struct` **`Animator`** — `pub struct Animator {`
- `struct` **`NineSliceRects`** — `pub struct NineSliceRects {`
- `struct` **`NineSliceInsets`** — `pub struct NineSliceInsets {`
- `struct` **`NineSlice`** — `pub struct NineSlice {`
- `struct` **`UvRect`** — `pub struct UvRect {`
- `struct` **`AtlasRegions`** — `pub struct AtlasRegions {`
- `struct` **`SpriteAtlas`** — `pub struct SpriteAtlas {`

### `timer::impl`

- `fn` **`create`** — `pub fn create(duration: f64) -> Timer {...}`
- `fn` **`create_repeating`** — `pub fn create_repeating(duration: f64) -> Timer {...}`
- `fn` **`update`** — `pub fn update(&mut self, delta_time: f64) -> u32 {...}`
- `fn` **`reset`** — `pub fn reset(&mut self) {...}`
- `fn` **`pause`** — `pub fn pause(&mut self) {...}`
- `fn` **`resume`** — `pub fn resume(&mut self) {...}`
- `fn` **`is_paused`** — `pub fn is_paused(&self) -> bool {...}`
- `fn` **`is_finished`** — `pub fn is_finished(&self) -> bool {...}`
- `fn` **`progress`** — `pub fn progress(&self) -> f64 {...}`
- `fn` **`remaining`** — `pub fn remaining(&self) -> f64 {...}`

### `timer::struct`

- `struct` **`Timer`** — `pub struct Timer {`

### `tween::enum`

- `enum` **`TweenState`** — `pub enum TweenState {`

### `tween::impl`

- `fn` **`get_from`** — `pub fn get_from(&self) -> T {...}`
- `fn` **`get_to`** — `pub fn get_to(&self) -> T {...}`
- `fn` **`get_easing`** — `pub fn get_easing(&self) -> Easing {...}`
- `fn` **`get_delay`** — `pub fn get_delay(&self) -> f64 {...}`
- `fn` **`get_elapsed`** — `pub fn get_elapsed(&self) -> f64 {...}`
- `fn` **`get_elapsed_mut`** — `pub fn get_elapsed_mut(&mut self) -> &mut f64 {...}`
- `fn` **`get_mode`** — `pub fn get_mode(&self) -> AnimationMode {...}`
- `fn` **`get_direction`** — `pub fn get_direction(&self) -> f64 {...}`
- `fn` **`try_get_on_complete`** — `pub fn try_get_on_complete(&self) -> &Option<Rc<dyn Fn()>> {...}`
- `fn` **`set_easing`** — `pub fn set_easing(&mut self, easing: Easing) {...}`
- `fn` **`set_delay`** — `pub fn set_delay(&mut self, delay: f64) {...}`
- `fn` **`set_elapsed`** — `pub fn set_elapsed(&mut self, elapsed: f64) {...}`
- `fn` **`set_state`** — `pub fn set_state(&mut self, state: TweenState) {...}`
- `fn` **`set_mode`** — `pub fn set_mode(&mut self, mode: AnimationMode) {...}`
- `fn` **`set_direction`** — `pub fn set_direction(&mut self, direction: f64) {...}`
- `fn` **`set_on_complete`** — `pub fn set_on_complete(&mut self, on_complete: Option<Rc<dyn Fn()>>) {...}`
- `fn` **`create`** — `pub fn create(from: T, to: T, duration: f64) -> Tween<T> {...}`
- `fn` **`with_easing`** — `pub fn with_easing(mut self, easing: Easing) -> Tween<T> {...}`
- `fn` **`with_delay`** — `pub fn with_delay(mut self, delay: f64) -> Tween<T> {...}`
- `fn` **`with_mode`** — `pub fn with_mode(mut self, mode: AnimationMode) -> Tween<T> {...}`
- `fn` **`with_on_complete`** — `pub fn with_on_complete(mut self, on_complete: Rc<dyn Fn()>) -> Tween<T> {...}`
- `fn` **`update`** — `pub fn update(&mut self, delta_time: f64) -> T {...}`
- `fn` **`value`** — `pub fn value(&self) -> T {...}`
- `fn` **`eased_progress`** — `pub fn eased_progress(&self) -> f64 {...}`
- `fn` **`raw_progress`** — `pub fn raw_progress(&self) -> f64 {...}`
- `fn` **`pause`** — `pub fn pause(&mut self) {...}`
- `fn` **`resume`** — `pub fn resume(&mut self) {...}`
- `fn` **`reset`** — `pub fn reset(&mut self) {...}`
- `fn` **`is_finished`** — `pub fn is_finished(&self) -> bool {...}`
- `fn` **`get_state`** — `pub fn get_state(&self) -> TweenState {...}`
- `fn` **`get_duration`** — `pub fn get_duration(&self) -> f64 {...}`

### `tween::struct`

- `struct` **`Tween`** — `pub struct Tween<T: Interpolable + Copy> {`

### `raytracing::scene::enum`

- `enum` **`OccluderKind`** — `pub enum OccluderKind {`

### `raytracing::scene::fn`

- `fn` **`intersect_triangle`** — `pub fn intersect_triangle(ray: &Ray, vertices: [Vector3D; {...}`
- `fn` **`collect_occluder_points`** — `pub(crate) fn collect_occluder_points(occluders: &[Occluder]) -> Vec<(Vector3D, f64)> {...}`
- `fn` **`build_bvh`** — `pub(crate) fn build_bvh(occluders: &[Occluder]) -> (Vec<RayTraceNode>, Vec<usize>) {...}`
- `fn` **`closest_hit_indexed`** — `pub(crate) fn closest_hit_indexed( ray: &Ray, scene: &RayTraceScene, ) -> Option<(usize, f64, Vector3D, Vector3D)> {...}`
- `fn` **`occluded_indexed`** — `pub(crate) fn occluded_indexed(ray: &Ray, scene: &RayTraceScene) -> bool {...}`
- `fn` **`shadow_visibility`** — `pub(crate) fn shadow_visibility<'a>( scene: &'a RayTraceScene, position: Vector3D, normal: Vector3D, ) -> impl FnMut(&Light, Vector3D, f64) -> f64 + 'a {...}`
- `fn` **`trace_bounces`** — `pub(crate) fn trace_bounces( ray: Ray, scene: &RayTraceScene, lights: &LightingUniforms, max_bounces: u32, ) -> Vector3D {...}`

### `raytracing::scene::impl`

- `fn` **`new`** — `pub fn new(origin: Vector3D, direction: Vector3D) -> Ray {...}`
- `fn` **`at`** — `pub fn at(&self, t: f64) -> Vector3D {...}`
- `fn` **`with_depth`** — `pub fn with_depth(&self, depth: u32) -> Ray {...}`
- `fn` **`with_range`** — `pub fn with_range(&self, t_min: f64, t_max: f64) -> Ray {...}`
- `fn` **`intersect_triangle`** — `pub fn intersect_triangle(&self, vertices: [Vector3D; {...}`
- `fn` **`sphere`** — `pub fn sphere(center: Vector3D, radius: f64, material: Material) -> Occluder {...}`
- `fn` **`aabb`** — `pub fn aabb(min: Vector3D, max: Vector3D, material: Material) -> Occluder {...}`
- `fn` **`triangle`** — `pub fn triangle(v0: Vector3D, v1: Vector3D, v2: Vector3D, material: Material) -> Occluder {...}`
- `fn` **`occluder_points`** — `pub fn occluder_points(&self) -> Vec<(Vector3D, f64)> {...}`
- `fn` **`new`** — `pub fn new(occluders: Vec<Occluder>) -> RayTraceScene {...}`
- `fn` **`trace`** — `pub fn trace(&self, ray: Ray, lights: &LightingUniforms) -> Vector3D {...}`
- `fn` **`trace_with_bounces`** — `pub fn trace_with_bounces( &self, ray: Ray, lights: &LightingUniforms, max_bounces: u32, ) -> Vector3D {...}`
- `fn` **`closest_hit`** — `pub fn closest_hit(&self, ray: &Ray) -> Option<Hit> {...}`
- `fn` **`occluded`** — `pub fn occluded(&self, ray: &Ray) -> bool {...}`

### `raytracing::scene::struct`

- `struct` **`Ray`** — `pub struct Ray {`
- `struct` **`Hit`** — `pub struct Hit {`
- `struct` **`Occluder`** — `pub struct Occluder {`
- `struct` **`RayTraceNode`** — `pub(crate) struct RayTraceNode {`
- `struct` **`BvhBuild`** — `pub(crate) struct BvhBuild {`
- `struct` **`BvhRange`** — `pub(crate) struct BvhRange {`
- `struct` **`BvhSubtree`** — `pub(crate) struct BvhSubtree {`
- `struct` **`SahSplit`** — `pub(crate) struct SahSplit {`
- `struct` **`BvhBuildContext`** — `pub(crate) struct BvhBuildContext<'a> {`
- `struct` **`RayTraceScene`** — `pub struct RayTraceScene {`

### `renderer::canvas::enum`

- `enum` **`DrawCommand`** — `pub enum DrawCommand {`

### `renderer::canvas::fn`

- `fn` **`draw_sprite_immediate`** — `pub(crate) fn draw_sprite_immediate( context: &CanvasRenderingContext2d, image: &HtmlImageElement, source: &Rect, transform: &Transform2D, ) {...}`

### `renderer::canvas::impl`

- `fn` **`create`** — `pub fn create(viewport_width: f64, viewport_height: f64) -> Camera2D {...}`
- `fn` **`world_to_screen`** — `pub fn world_to_screen(&self, world: Vector2D) -> Vector2D {...}`
- `fn` **`screen_to_world`** — `pub fn screen_to_world(&self, screen: Vector2D) -> Vector2D {...}`
- `fn` **`translate`** — `pub fn translate(&mut self, offset: Vector2D) {...}`
- `fn` **`zoom_by`** — `pub fn zoom_by(&mut self, factor: f64) {...}`
- `fn` **`font`** — `pub fn font<F>(size: f64, family: F) -> String where F: AsRef<str>, {...}`
- `fn` **`default_font`** — `pub fn default_font() -> String {...}`
- `fn` **`enable_smoothing_on`** — `pub fn enable_smoothing_on(context: &CanvasRenderingContext2d) {...}`
- `fn` **`detect_dpr`** — `pub fn detect_dpr() -> f64 {...}`
- `fn` **`apply_quality`** — `pub(crate) fn apply_quality(context: &CanvasRenderingContext2d, quality: RenderQuality) {...}`
- `fn` **`to_css`** — `pub fn to_css(color: &Color) -> String {...}`
- `fn` **`create`** — `pub fn create() -> DrawList {...}`
- `fn` **`is_empty`** — `pub fn is_empty(&self) -> bool {...}`
- `fn` **`len`** — `pub fn len(&self) -> usize {...}`
- `fn` **`commands`** — `pub fn commands(&self) -> &[DrawCommand] {...}`
- `fn` **`clear`** — `pub fn clear(&mut self) {...}`
- `fn` **`fill_rect`** — `pub fn fill_rect(&mut self, position: Vector2D, width: f64, height: f64, color: Color) {...}`
- `fn` **`stroke_rect`** — `pub fn stroke_rect( &mut self, position: Vector2D, width: f64, height: f64, color: Color, line_width: f64, ) {...}`
- `fn` **`fill_circle`** — `pub fn fill_circle(&mut self, center: Vector2D, radius: f64, color: Color) {...}`
- `fn` **`stroke_circle`** — `pub fn stroke_circle(&mut self, center: Vector2D, radius: f64, color: Color, line_width: f64) {...}`
- `fn` **`draw_line`** — `pub fn draw_line(&mut self, start: Vector2D, end: Vector2D, color: Color, line_width: f64) {...}`
- `fn` **`fill_text`** — `pub fn fill_text<T, F>(&mut self, text: T, position: Vector2D, color: Color, font: F) where T: AsRef<str>, F: AsRef<str>, {...}`
- `fn` **`draw_sprite`** — `pub fn draw_sprite(&mut self, image: &HtmlImageElement, source: Rect, transform: Transform2D) {...}`
- `fn` **`draw_image_rect`** — `pub fn draw_image_rect( &mut self, image: &HtmlImageElement, source: Rect, dest_position: Vector2D, dest_width: f64, dest_height: f64, ) {...}`
- `fn` **`set_global_alpha`** — `pub fn set_global_alpha(&mut self, alpha: f64) {...}`
- `fn` **`set_blend_mode`** — `pub fn set_blend_mode(&mut self, mode: BlendMode) {...}`
- `fn` **`from_selector`** — `pub fn from_selector<S>( canvas_selector: S, viewport_width: f64, viewport_height: f64, ) -> Option<CanvasRenderer> where S: AsRef<str>, {...}`
- `fn` **`enable_smoothing`** — `pub(crate) fn enable_smoothing(&self) {...}`
- `fn` **`clear`** — `pub fn clear(&self) {...}`
- `fn` **`clear_color`** — `pub fn clear_color<C>(&self, color: C) where C: AsRef<str>, {...}`
- `fn` **`save`** — `pub fn save(&self) {...}`
- `fn` **`restore`** — `pub fn restore(&self) {...}`
- `fn` **`replay`** — `pub fn replay(&self, list: &DrawList) {...}`
- `fn` **`replay_context`** — `pub(crate) fn replay_context(context: &CanvasRenderingContext2d, list: &DrawList) {...}`
- `fn` **`apply_camera`** — `pub fn apply_camera(&self) {...}`
- `fn` **`set_fill_color`** — `pub fn set_fill_color<C>(&self, color: C) where C: AsRef<str>, {...}`
- `fn` **`set_stroke_color`** — `pub fn set_stroke_color<C>(&self, color: C) where C: AsRef<str>, {...}`
- `fn` **`set_line_width`** — `pub fn set_line_width(&self, width: f64) {...}`
- `fn` **`set_global_alpha`** — `pub fn set_global_alpha(&self, alpha: f64) {...}`
- `fn` **`fill_rect`** — `pub fn fill_rect(&self, position: Vector2D, width: f64, height: f64) {...}`
- `fn` **`stroke_rect`** — `pub fn stroke_rect(&self, position: Vector2D, width: f64, height: f64) {...}`
- `fn` **`fill_circle`** — `pub fn fill_circle(&self, center: Vector2D, radius: f64) {...}`
- `fn` **`stroke_circle`** — `pub fn stroke_circle(&self, center: Vector2D, radius: f64) {...}`
- `fn` **`draw_line`** — `pub fn draw_line(&self, start: Vector2D, end: Vector2D) {...}`
- `fn` **`fill_text`** — `pub fn fill_text<T>(&self, text: T, position: Vector2D) where T: AsRef<str>, {...}`
- `fn` **`set_font`** — `pub fn set_font<F>(&self, font: F) where F: AsRef<str>, {...}`
- `fn` **`draw_image`** — `pub fn draw_image( &self, image: &HtmlImageElement, position: Vector2D, width: f64, height: f64, ) {...}`
- `fn` **`draw_image_rect`** — `pub fn draw_image_rect( &self, image: &HtmlImageElement, source: Rect, dest_position: Vector2D, dest_width: f64, dest_height: f64, ) {...}`
- `fn` **`create`** — `pub fn create( position: Vector3D, target: Vector3D, viewport_width: f64, viewport_height: f64, ) -> Camera3D {...}`
- `fn` **`aspect`** — `pub fn aspect(&self) -> f64 {...}`
- `fn` **`forward`** — `pub fn forward(&self) -> Vector3D {...}`
- `fn` **`right`** — `pub fn right(&self) -> Vector3D {...}`
- `fn` **`view_matrix`** — `pub fn view_matrix(&self) -> Matrix4x4 {...}`
- `fn` **`projection_matrix`** — `pub(crate) fn projection_matrix(&self) -> Matrix4x4 {...}`
- `fn` **`view_proj_matrix`** — `pub fn view_proj_matrix(&self) -> Matrix4x4 {...}`
- `fn` **`world_to_screen`** — `pub fn world_to_screen(&self, world: Vector3D) -> Vector3D {...}`
- `fn` **`in_frustum`** — `pub fn in_frustum(&self, world: Vector3D) -> bool {...}`
- `fn` **`translate`** — `pub fn translate(&mut self, offset: Vector3D) {...}`
- `fn` **`zoom`** — `pub fn zoom(&mut self, distance: f64) {...}`
- `fn` **`orbit`** — `pub fn orbit(&mut self, yaw_delta: f64, pitch_delta: f64) {...}`
- `fn` **`from_selector`** — `pub fn from_selector<S>(canvas_selector: S, width: f64, height: f64) -> Option<SsaaCanvas> where S: AsRef<str>, {...}`
- `fn` **`from_selector_with_scale`** — `pub fn from_selector_with_scale<S>( canvas_selector: S, width: f64, height: f64, scale_factor: f64, ) -> Option<SsaaCanvas> where S: AsRef<str>, {...}`
- `fn` **`present`** — `pub fn present(&self) {...}`
- `fn` **`clear`** — `pub fn clear(&self) {...}`
- `fn` **`clear_color`** — `pub fn clear_color<C>(&self, color: C) where C: AsRef<str>, {...}`
- `fn` **`enable_smoothing`** — `pub(crate) fn enable_smoothing(&self) {...}`
- `fn` **`create`** — `pub fn create(start: Vector2D, end: Vector2D, stops: Vec<(f64, String)>) -> LinearGradient {...}`
- `fn` **`to_gradient`** — `pub fn to_gradient(&self, context: &CanvasRenderingContext2d) -> Option<CanvasGradient> {...}`
- `fn` **`create`** — `pub fn create( inner_center: Vector2D, inner_radius: f64, outer_center: Vector2D, outer_radius: f64, stops: Vec<(f64, String)>, ) -> RadialGradient {...}`
- `fn` **`to_gradient`** — `pub fn to_gradient(&self, context: &CanvasRenderingContext2d) -> Option<CanvasGradient> {...}`
- `fn` **`create`** — `pub fn create() -> ShadowConfig {...}`
- `fn` **`create`** — `pub fn create(z_index: i32, visible: bool) -> RenderLayer {...}`
- `fn` **`background`** — `pub fn background() -> RenderLayer {...}`
- `fn` **`foreground`** — `pub fn foreground() -> RenderLayer {...}`
- `fn` **`ui`** — `pub fn ui() -> RenderLayer {...}`
- `fn` **`set_blend_mode`** — `pub fn set_blend_mode(&self, mode: BlendMode) {...}`
- `fn` **`set_shadow`** — `pub fn set_shadow(&self, config: &ShadowConfig) {...}`
- `fn` **`clear_shadow`** — `pub fn clear_shadow(&self) {...}`
- `fn` **`set_linear_gradient_fill`** — `pub fn set_linear_gradient_fill(&self, gradient: &LinearGradient) {...}`
- `fn` **`set_radial_gradient_fill`** — `pub fn set_radial_gradient_fill(&self, gradient: &RadialGradient) {...}`
- `fn` **`set_linear_gradient_stroke`** — `pub fn set_linear_gradient_stroke(&self, gradient: &LinearGradient) {...}`
- `fn` **`set_radial_gradient_stroke`** — `pub fn set_radial_gradient_stroke(&self, gradient: &RadialGradient) {...}`

### `renderer::canvas::struct`

- `struct` **`Camera2D`** — `pub struct Camera2D {`
- `struct` **`Camera3D`** — `pub struct Camera3D {`
- `struct` **`CanvasRenderer`** — `pub struct CanvasRenderer {`
- `struct` **`LinearGradient`** — `pub struct LinearGradient {`
- `struct` **`RadialGradient`** — `pub struct RadialGradient {`
- `struct` **`ShadowConfig`** — `pub struct ShadowConfig {`
- `struct` **`RenderLayer`** — `pub struct RenderLayer {`
- `struct` **`DrawList`** — `pub struct DrawList {`
- `struct` **`SsaaCanvas`** — `pub struct SsaaCanvas {`

### `renderer::canvas::trait`

- `trait` **`Renderable`** — `pub trait Renderable {`
- `trait` **`RenderBackend`** — `pub trait RenderBackend {`

### `renderer::descriptor::enum`

- `enum` **`BindGroupEntry`** — `pub enum BindGroupEntry {`
- `enum` **`BindGroupEntryType`** — `pub enum BindGroupEntryType {`

### `renderer::descriptor::impl`

- `fn` **`default_for`** — `pub fn default_for(width: u32, height: u32, format: GpuTextureFormat) -> Self {...}`
- `fn` **`full`** — `pub fn full() -> Self {...}`
- `fn` **`effective_dimension`** — `pub(crate) fn effective_dimension(&self) -> &'static str {...}`
- `fn` **`effective_aspect`** — `pub(crate) fn effective_aspect(&self) -> &'static str {...}`
- `fn` **`mip`** — `pub fn mip(level: u32) -> Self {...}`
- `fn` **`depth_only`** — `pub fn depth_only() -> Self {...}`
- `fn` **`for_2d`** — `pub fn for_2d(data: Vec<u8>, bytes_per_row: u32, texture: JsValue) -> Self {...}`
- `fn` **`binding`** — `pub fn binding(&self) -> u32 {...}`
- `fn` **`uniform`** — `pub fn uniform<V: Into<ShaderStages>>(binding: u32, visibility: V) -> Self {...}`
- `fn` **`storage`** — `pub fn storage<V: Into<ShaderStages>>(binding: u32, visibility: V, read_only: bool) -> Self {...}`
- `fn` **`texture`** — `pub fn texture<V: Into<ShaderStages>>(binding: u32, visibility: V, sample_type: &str) -> Self {...}`
- `fn` **`texture_multisampled`** — `pub fn texture_multisampled<V: Into<ShaderStages>>( binding: u32, visibility: V, sample_type: &str, ) -> Self {...}`
- `fn` **`storage_texture`** — `pub fn storage_texture<V: Into<ShaderStages>>( binding: u32, visibility: V, format: &str, read_only: bool, ) -> Self {...}`
- `fn` **`sampler`** — `pub fn sampler<V: Into<ShaderStages>>(binding: u32, visibility: V) -> Self {...}`
- `fn` **`sampler_non_filtering`** — `pub fn sampler_non_filtering<V: Into<ShaderStages>>(binding: u32, visibility: V) -> Self {...}`
- `fn` **`sampler_comparison`** — `pub fn sampler_comparison<V: Into<ShaderStages>>(binding: u32, visibility: V) -> Self {...}`
- `fn` **`for_format`** — `pub fn for_format(format: GpuTextureFormat) -> Self {...}`
- `fn` **`with_sample_count`** — `pub fn with_sample_count(count: u32) -> Self {...}`
- `fn` **`writing_depth`** — `pub fn writing_depth(format: GpuTextureFormat) -> Self {...}`
- `fn` **`source_alpha_over`** — `pub fn source_alpha_over() -> Self {...}`
- `fn` **`alpha_over`** — `pub fn alpha_over() -> Self {...}`
- `fn` **`nearest_clamp`** — `pub fn nearest_clamp() -> Self {...}`
- `fn` **`whole_stream`** — `pub fn whole_stream(vertex_count: u32, instance_count: u32) -> Self {...}`
- `fn` **`whole_buffer`** — `pub fn whole_buffer(index_count: u32, instance_count: u32) -> Self {...}`
- `fn` **`grid`** — `pub fn grid(x: u32, y: u32, z: u32) -> Self {...}`

### `renderer::descriptor::struct`

- `struct` **`ViewportDescriptor`** — `pub struct ViewportDescriptor {`
- `struct` **`VertexAttribute`** — `pub struct VertexAttribute {`
- `struct` **`VertexBufferLayout`** — `pub struct VertexBufferLayout {`
- `struct` **`Texture2DDescriptor`** — `pub struct Texture2DDescriptor {`
- `struct` **`TextureViewDescriptor`** — `pub struct TextureViewDescriptor {`
- `struct` **`TextureWriteDescriptor`** — `pub struct TextureWriteDescriptor {`
- `struct` **`BindGroupLayoutEntry`** — `pub struct BindGroupLayoutEntry {`
- `struct` **`SamplerDescriptor`** — `pub struct SamplerDescriptor {`
- `struct` **`ColorAttachment`** — `pub struct ColorAttachment {`
- `struct` **`DepthStencilAttachment`** — `pub struct DepthStencilAttachment {`
- `struct` **`BlendComponent`** — `pub struct BlendComponent {`
- `struct` **`BlendState`** — `pub struct BlendState {`
- `struct` **`ColorTargetState`** — `pub struct ColorTargetState {`
- `struct` **`DepthStencilState`** — `pub struct DepthStencilState {`
- `struct` **`MultisampleState`** — `pub struct MultisampleState {`
- `struct` **`PrimitiveState`** — `pub struct PrimitiveState {`
- `struct` **`VertexState`** — `pub struct VertexState {`
- `struct` **`FragmentState`** — `pub struct FragmentState {`
- `struct` **`RenderPipelineDescriptor`** — `pub struct RenderPipelineDescriptor {`
- `struct` **`ComputePipelineDescriptor`** — `pub struct ComputePipelineDescriptor {`
- `struct` **`TextureDescriptor`** — `pub struct TextureDescriptor {`
- `struct` **`BufferDescriptor`** — `pub(crate) struct BufferDescriptor {`
- `struct` **`UniformSlice`** — `pub struct UniformSlice {`
- `struct` **`DrawIndexedArgs`** — `pub struct DrawIndexedArgs {`
- `struct` **`DrawArgs`** — `pub struct DrawArgs {`
- `struct` **`DispatchArgs`** — `pub struct DispatchArgs {`

### `renderer::status::enum`

- `enum` **`BlendMode`** — `pub enum BlendMode {`
- `enum` **`RenderQuality`** — `pub enum RenderQuality {`
- `enum` **`VertexStepMode`** — `pub enum VertexStepMode {`
- `enum` **`LoadOp`** — `pub enum LoadOp {`
- `enum` **`StoreOp`** — `pub enum StoreOp {`
- `enum` **`BufferUsage`** — `pub enum BufferUsage {`
- `enum` **`TextureUsage`** — `pub enum TextureUsage {`
- `enum` **`FilterMode`** — `pub enum FilterMode {`
- `enum` **`MipmapFilter`** — `pub enum MipmapFilter {`
- `enum` **`AddressMode`** — `pub enum AddressMode {`
- `enum` **`CompareFunction`** — `pub enum CompareFunction {`
- `enum` **`BlendFactor`** — `pub enum BlendFactor {`
- `enum` **`BlendOperation`** — `pub enum BlendOperation {`
- `enum` **`PrimitiveTopology`** — `pub enum PrimitiveTopology {`
- `enum` **`IndexFormat`** — `pub enum IndexFormat {`
- `enum` **`ShaderStage`** — `pub enum ShaderStage {`
- `enum` **`FrontFace`** — `pub enum FrontFace {`
- `enum` **`CullMode`** — `pub enum CullMode {`
- `enum` **`VertexAttributeFormat`** — `pub enum VertexAttributeFormat {`
- `enum` **`GpuTextureFormat`** — `pub enum GpuTextureFormat {`
- `enum` **`GpuErrorFilter`** — `pub enum GpuErrorFilter {`

### `renderer::status::fn`

- `fn` **`load_op_name`** — `pub(crate) fn load_op_name(value: LoadOp) -> &'static str {...}`
- `fn` **`store_op_name`** — `pub(crate) fn store_op_name(value: StoreOp) -> &'static str {...}`
- `fn` **`buffer_usage_bit`** — `pub(crate) fn buffer_usage_bit(value: BufferUsage) -> u32 {...}`
- `fn` **`texture_usage_bit`** — `pub(crate) fn texture_usage_bit(value: TextureUsage) -> u32 {...}`
- `fn` **`shader_stage_bit`** — `pub(crate) fn shader_stage_bit(value: ShaderStage) -> u32 {...}`
- `fn` **`filter_mode_name`** — `pub fn filter_mode_name(value: FilterMode) -> &'static str {...}`
- `fn` **`mipmap_filter_name`** — `pub fn mipmap_filter_name(value: MipmapFilter) -> &'static str {...}`
- `fn` **`address_mode_name`** — `pub fn address_mode_name(value: AddressMode) -> &'static str {...}`
- `fn` **`compare_function_name`** — `pub(crate) fn compare_function_name(value: CompareFunction) -> &'static str {...}`
- `fn` **`blend_factor_name`** — `pub(crate) fn blend_factor_name(value: BlendFactor) -> &'static str {...}`
- `fn` **`blend_operation_name`** — `pub(crate) fn blend_operation_name(value: BlendOperation) -> &'static str {...}`
- `fn` **`primitive_topology_name`** — `pub(crate) fn primitive_topology_name(value: PrimitiveTopology) -> &'static str {...}`
- `fn` **`index_format_name`** — `pub(crate) fn index_format_name(value: IndexFormat) -> &'static str {...}`
- `fn` **`front_face_name`** — `pub(crate) fn front_face_name(value: FrontFace) -> &'static str {...}`
- `fn` **`cull_mode_name`** — `pub(crate) fn cull_mode_name(value: CullMode) -> &'static str {...}`
- `fn` **`vertex_attribute_format_name`** — `pub(crate) fn vertex_attribute_format_name(value: VertexAttributeFormat) -> &'static str {...}`
- `fn` **`gpu_texture_format_name`** — `pub(crate) fn gpu_texture_format_name(value: GpuTextureFormat) -> &'static str {...}`
- `fn` **`gpu_error_filter_name`** — `pub(crate) fn gpu_error_filter_name(value: GpuErrorFilter) -> &'static str {...}`
- `fn` **`texture_usage_mask`** — `pub fn texture_usage_mask(usages: &[TextureUsage]) -> u32 {...}`
- `fn` **`buffer_usage_mask`** — `pub(crate) fn buffer_usage_mask(usages: &[BufferUsage]) -> u32 {...}`

### `renderer::status::impl`

- `fn` **`to_css`** — `pub fn to_css(&self) -> &str {...}`
- `fn` **`as_str`** — `pub fn as_str(&self) -> &'static str {...}`
- `fn` **`bits`** — `pub fn bits(self) -> u32 {...}`
- `fn` **`is_empty`** — `pub fn is_empty(self) -> bool {...}`
- `fn` **`contains`** — `pub fn contains(self, stage: ShaderStage) -> bool {...}`
- `fn` **`usage_bit`** — `pub fn usage_bit(self) -> u32 {...}`
- `fn` **`usage_bit`** — `pub fn usage_bit(self) -> u32 {...}`
- `fn` **`stage_bit`** — `pub fn stage_bit(self) -> u32 {...}`

### `renderer::status::struct`

- `struct` **`ShaderStages`** — `pub struct ShaderStages(pub(crate) u32);`

### `renderer::webgl::enum`

- `enum` **`GlShaderKind`** — `pub enum GlShaderKind {`
- `enum` **`GlFramebufferStatus`** — `pub enum GlFramebufferStatus {`
- `enum` **`WebGl2InitError`** — `pub enum WebGl2InitError {`
- `enum` **`WebGlProgramError`** — `pub enum WebGlProgramError {`

### `renderer::webgl::fn`

- `fn` **`gl_shader_type`** — `pub(crate) fn gl_shader_type(kind: GlShaderKind) -> u32 {...}`
- `fn` **`gl_primitive_mode`** — `pub(crate) fn gl_primitive_mode(topology: PrimitiveTopology) -> u32 {...}`
- `fn` **`gl_index_type`** — `pub fn gl_index_type(format: IndexFormat) -> (u32, u32) {...}`
- `fn` **`gl_buffer_target`** — `pub fn gl_buffer_target(usage: BufferUsage) -> u32 {...}`
- `fn` **`gl_buffer_usage_hint`** — `pub fn gl_buffer_usage_hint(usage: BufferUsage) -> u32 {...}`
- `fn` **`gl_filter_mode`** — `pub fn gl_filter_mode(filter: FilterMode) -> u32 {...}`
- `fn` **`gl_min_filter`** — `pub fn gl_min_filter(filter: FilterMode, mipmap: MipmapFilter) -> u32 {...}`
- `fn` **`gl_address_mode`** — `pub fn gl_address_mode(mode: AddressMode) -> u32 {...}`
- `fn` **`gl_compare_function`** — `pub fn gl_compare_function(compare: CompareFunction) -> u32 {...}`
- `fn` **`gl_blend_factor`** — `pub fn gl_blend_factor(factor: BlendFactor) -> u32 {...}`
- `fn` **`gl_blend_equation`** — `pub fn gl_blend_equation(operation: BlendOperation) -> u32 {...}`
- `fn` **`gl_cull_face`** — `pub fn gl_cull_face(mode: CullMode) -> u32 {...}`
- `fn` **`gl_front_face`** — `pub fn gl_front_face(face: FrontFace) -> u32 {...}`
- `fn` **`gl_attribute_layout`** — `pub fn gl_attribute_layout(format: VertexAttributeFormat) -> (u32, u32, bool) {...}`
- `fn` **`gl_texture_layout`** — `pub fn gl_texture_layout(format: GpuTextureFormat) -> (i32, u32, u32) {...}`
- `fn` **`gl_renderbuffer_format`** — `pub fn gl_renderbuffer_format(format: GpuTextureFormat) -> u32 {...}`
- `fn` **`gl_framebuffer_status`** — `pub fn gl_framebuffer_status(status: u32) -> GlFramebufferStatus {...}`
- `fn` **`gl_texture_unit`** — `pub fn gl_texture_unit(unit: u32) -> u32 {...}`
- `fn` **`gl_texture_target_2d`** — `pub fn gl_texture_target_2d() -> u32 {...}`
- `fn` **`gl_matrix4_into_f32`** — `pub fn gl_matrix4_into_f32(matrix: &Matrix4x4, out: &mut [f32]) {...}`
- `fn` **`gl_flip_y`** — `pub fn gl_flip_y(flip: bool) -> i32 {...}`

### `renderer::webgl::impl`

- `fn` **`code`** — `pub fn code(&self) -> &'static str {...}`
- `fn` **`create`** — `pub fn create( context: &WebGl2RenderingContext, target: u32, size: u32, usage: u32, ) -> Option<GlBuffer> {...}`
- `fn` **`create_for`** — `pub fn create_for( context: &WebGl2RenderingContext, usage: BufferUsage, size: u32, ) -> Option<GlBuffer> {...}`
- `fn` **`fits`** — `pub fn fits(&self, size: u32) -> bool {...}`
- `fn` **`bind`** — `pub fn bind(&self, context: &WebGl2RenderingContext, target: u32) {...}`
- `fn` **`upload`** — `pub fn upload(&mut self, context: &WebGl2RenderingContext, target: u32, data: &[u8]) {...}`
- `fn` **`update`** — `pub fn update( &mut self, context: &WebGl2RenderingContext, target: u32, offset: u32, data: &[u8], ) -> bool {...}`
- `fn` **`delete`** — `pub fn delete(&mut self, context: &WebGl2RenderingContext, target: u32) {...}`
- `fn` **`create`** — `pub fn create( context: &WebGl2RenderingContext, width: u32, height: u32, format: GpuTextureFormat, pixels: &[u8], ) -> Option<GlTexture> {...}`
- `fn` **`create_from_image`** — `pub fn create_from_image( context: &WebGl2RenderingContext, image: &HtmlImageElement, format: GpuTextureFormat, ) -> Option<GlTexture> {...}`
- `fn` **`create_from_canvas`** — `pub fn create_from_canvas( context: &WebGl2RenderingContext, canvas: &HtmlCanvasElement, format: GpuTextureFormat, ) -> Option<GlTexture> {...}`
- `fn` **`create_from_bitmap`** — `pub fn create_from_bitmap( context: &WebGl2RenderingContext, bitmap: &Object, width: u32, height: u32, format: GpuTextureFormat, ) -> Option<GlTexture> {...}`
- `fn` **`set_parameters`** — `pub fn set_parameters( &self, context: &WebGl2RenderingContext, filter: FilterMode, mipmap: MipmapFilter, address: AddressMode, ) {...}`
- `fn` **`generate_mipmap`** — `pub fn generate_mipmap( &mut self, context: &WebGl2RenderingContext, filter: FilterMode, mipmap: MipmapFilter, address: AddressMode, ) {...}`
- `fn` **`update`** — `pub fn update( &self, context: &WebGl2RenderingContext, region: &GlScissor, format: GpuTextureFormat, data: &[u8], ) -> bool {...}`
- `fn` **`delete`** — `pub fn delete(&mut self, context: &WebGl2RenderingContext) {...}`
- `fn` **`create`** — `pub fn create(context: &WebGl2RenderingContext) -> Option<GlVertexArray> {...}`
- `fn` **`bind`** — `pub fn bind(&self, context: &WebGl2RenderingContext) {...}`
- `fn` **`set_layout`** — `pub fn set_layout( &self, context: &WebGl2RenderingContext, buffer: &GlBuffer, layout: &VertexBufferLayout, ) {...}`
- `fn` **`set_instance_layout`** — `pub fn set_instance_layout( &self, context: &WebGl2RenderingContext, buffer: &GlBuffer, layout: &VertexBufferLayout, ) {...}`
- `fn` **`set_divisor`** — `pub fn set_divisor(&self, context: &WebGl2RenderingContext, index: u32, divisor: u32) {...}`
- `fn` **`unbind`** — `pub fn unbind(context: &WebGl2RenderingContext) {...}`
- `fn` **`delete`** — `pub fn delete(&self, context: &WebGl2RenderingContext) {...}`
- `fn` **`create`** — `pub fn create( context: &WebGl2RenderingContext, width: u32, height: u32, color_format: GpuTextureFormat, depth_format: Option<GpuTextureFormat>, ) -> Option<GlFramebuffer> {...}`
- `fn` **`bind`** — `pub fn bind(&self, context: &WebGl2RenderingContext) -> GlFramebufferStatus {...}`
- `fn` **`matches`** — `pub fn matches(&self, width: u32, height: u32) -> bool {...}`
- `fn` **`delete`** — `pub fn delete(&mut self, context: &WebGl2RenderingContext) {...}`
- `fn` **`create`** — `pub fn create( context: &WebGl2RenderingContext, vertex_source: &str, fragment_source: &str, ) -> Result<GlProgram, WebGlProgramError> {...}`
- `fn` **`bind`** — `pub fn bind(&self, context: &WebGl2RenderingContext) {...}`
- `fn` **`uniform`** — `pub fn uniform( &mut self, context: &WebGl2RenderingContext, name: &str, ) -> Option<WebGlUniformLocation> {...}`
- `fn` **`set_uniform_1f`** — `pub fn set_uniform_1f(&mut self, context: &WebGl2RenderingContext, name: &str, value: f32) {...}`
- `fn` **`set_uniform_2f`** — `pub fn set_uniform_2f(&mut self, context: &WebGl2RenderingContext, name: &str, x: f32, y: f32) {...}`
- `fn` **`set_uniform_3f`** — `pub fn set_uniform_3f( &mut self, context: &WebGl2RenderingContext, name: &str, x: f32, y: f32, z: f32, ) {...}`
- `fn` **`set_uniform_4f`** — `pub fn set_uniform_4f( &mut self, context: &WebGl2RenderingContext, name: &str, x: f32, y: f32, z: f32, w: f32, ) {...}`
- `fn` **`set_uniform_mat4`** — `pub fn set_uniform_mat4( &mut self, context: &WebGl2RenderingContext, name: &str, matrix: &Matrix4x4, ) {...}`
- `fn` **`set_uniform_vec4_array`** — `pub fn set_uniform_vec4_array( &mut self, context: &WebGl2RenderingContext, name: &str, data: &[f32], ) {...}`
- `fn` **`bind_uniform_block`** — `pub fn bind_uniform_block( &mut self, context: &WebGl2RenderingContext, name: &str, binding: u32, ) -> bool {...}`
- `fn` **`delete`** — `pub fn delete(&mut self, context: &WebGl2RenderingContext) {...}`
- `fn` **`create`** — `pub fn create( context: &WebGl2RenderingContext, size: u32, binding: u32, ) -> Option<GlUniformBlock> {...}`
- `fn` **`bind`** — `pub fn bind(&self, context: &WebGl2RenderingContext) {...}`
- `fn` **`update`** — `pub fn update(&mut self, context: &WebGl2RenderingContext, offset: u32, data: &[u8]) -> bool {...}`
- `fn` **`set_mat4`** — `pub fn set_mat4( &mut self, context: &WebGl2RenderingContext, offset: u32, matrix: &Matrix4x4, ) -> bool {...}`
- `fn` **`delete`** — `pub fn delete(&mut self, context: &WebGl2RenderingContext) {...}`
- `fn` **`from_init`** — `pub fn from_init(init: GlRenderStateInit) -> Self {...}`
- `fn` **`context_defaults`** — `pub fn context_defaults(width: i32, height: i32) -> GlRenderState {...}`
- `fn` **`init`** — `pub fn init(config: &RenderConfig) -> Result<WebGl2Backend, WebGl2InitError> {...}`
- `fn` **`from_init`** — `pub fn from_init(init: WebGl2BackendInit) -> Self {...}`
- `fn` **`is_available`** — `pub fn is_available() -> bool {...}`
- `fn` **`resize`** — `pub fn resize(&mut self, width: u32, height: u32) {...}`
- `fn` **`is_context_lost`** — `pub fn is_context_lost(&self) -> bool {...}`
- `fn` **`apply_state`** — `pub fn apply_state(&mut self, state: &GlRenderState) {...}`
- `fn` **`invalidate_state`** — `pub fn invalidate_state(&mut self, width: u32, height: u32) {...}`
- `fn` **`set_clear_color`** — `pub(crate) fn set_clear_color(&mut self, color: Color) {...}`
- `fn` **`begin_frame`** — `pub(crate) fn begin_frame( &mut self, context: &WebGl2RenderingContext, width: u32, height: u32, ) {...}`
- `fn` **`clear_depth`** — `pub fn clear_depth(&self, context: &WebGl2RenderingContext) {...}`
- `fn` **`render_frame`** — `pub fn render_frame( &mut self, context: &WebGl2RenderingContext, program: &GlProgram, color: Color, vertex_count: u32, ) {...}`
- `fn` **`use_program`** — `pub(crate) fn use_program(&mut self, context: &WebGl2RenderingContext, program: &GlProgram) {...}`
- `fn` **`bind_texture_unit`** — `pub fn bind_texture_unit( &mut self, context: &WebGl2RenderingContext, unit: u32, texture: &GlTexture, ) {...}`
- `fn` **`draw_arrays`** — `pub(crate) fn draw_arrays( &self, context: &WebGl2RenderingContext, topology: PrimitiveTopology, args: &DrawArgs, ) {...}`
- `fn` **`draw_elements`** — `pub fn draw_elements( &self, context: &WebGl2RenderingContext, topology: PrimitiveTopology, args: &DrawIndexedArgs, index_format: IndexFormat, ) -> bool {...}`
- `fn` **`draw_element_range`** — `pub fn draw_element_range( &self, context: &WebGl2RenderingContext, topology: PrimitiveTopology, start: u32, end: u32, index_format: IndexFormat, ) -> bool {...}`
- `fn` **`draw_arrays_instanced`** — `pub fn draw_arrays_instanced( &self, context: &WebGl2RenderingContext, topology: PrimitiveTopology, args: &DrawArgs, ) {...}`
- `fn` **`draw_elements_instanced`** — `pub fn draw_elements_instanced( &self, context: &WebGl2RenderingContext, topology: PrimitiveTopology, args: &DrawIndexedArgs, index_format: IndexFormat, ) -> bool {...}`
- `fn` **`read_pixels`** — `pub fn read_pixels( &mut self, context: &WebGl2RenderingContext, x: i32, y: i32, width: u32, height: u32, ) -> Vec<u8> {...}`

### `renderer::webgl::struct`

- `struct` **`GlBuffer`** — `pub struct GlBuffer {`
- `struct` **`GlTexture`** — `pub struct GlTexture {`
- `struct` **`GlVertexArray`** — `pub struct GlVertexArray {`
- `struct` **`GlFramebuffer`** — `pub struct GlFramebuffer {`
- `struct` **`GlProgram`** — `pub struct GlProgram {`
- `struct` **`GlUniformBlock`** — `pub struct GlUniformBlock {`
- `struct` **`GlBlendState`** — `pub struct GlBlendState {`
- `struct` **`GlDepthState`** — `pub struct GlDepthState {`
- `struct` **`GlCullState`** — `pub struct GlCullState {`
- `struct` **`GlColorMask`** — `pub struct GlColorMask {`
- `struct` **`GlScissor`** — `pub struct GlScissor {`
- `struct` **`GlViewport`** — `pub struct GlViewport {`
- `struct` **`GlRenderState`** — `pub struct GlRenderState {`
- `struct` **`WebGl2Backend`** — `pub struct WebGl2Backend {`
- `struct` **`WebGl2BackendInit`** — `pub struct WebGl2BackendInit {`
- `struct` **`GlRenderStateInit`** — `pub struct GlRenderStateInit {`

### `renderer::webgpu::enum`

- `enum` **`WebGpuInitError`** — `pub enum WebGpuInitError {`
- `enum` **`GpuReceiverClass`** — `pub enum GpuReceiverClass {`

### `renderer::webgpu::fn`

- `fn` **`js_error_to_string`** — `pub(crate) fn js_error_to_string(value: &JsValue) -> String {...}`
- `fn` **`pick_depth_format`** — `pub(crate) fn pick_depth_format(high_precision: bool, with_stencil: bool) -> &'static str {...}`
- `fn` **`map_mode_for`** — `pub(crate) fn map_mode_for(read: bool, write: bool) -> u32 {...}`
- `fn` **`texture_usage`** — `pub(crate) fn texture_usage( render_target: bool, copy_src: bool, copy_dst: bool, sampled: bool, storage: bool, ) -> u32 {...}`
- `fn` **`cached_method_name`** — `pub(crate) fn cached_method_name(name: &'static str) -> JsValue {...}`
- `fn` **`cached_method`** — `pub(crate) fn cached_method( class: GpuReceiverClass, obj: &JsValue, method_name: &'static str, ) -> Result<Function, JsValue> {...}`
- `fn` **`cached_method_call`** — `pub(crate) fn cached_method_call( class: GpuReceiverClass, obj: &JsValue, method_name: &'static str, arg: &JsValue, ) -> Result<JsValue, JsValue> {...}`

### `renderer::webgpu::impl`

- `fn` **`new`** — `pub fn new(init: WebGpuRendererInit) -> Self {...}`
- `fn` **`is_available`** — `pub fn is_available() -> bool {...}`
- `fn` **`probe`** — `pub async fn probe() -> bool {...}`
- `fn` **`init`** — `pub async fn init(config: &RenderConfig) -> Result<WebGpuRenderer, WebGpuInitError> {...}`
- `fn` **`resize`** — `pub fn resize(&mut self, physical_width: u32, physical_height: u32) -> bool {...}`
- `fn` **`sync_to_current_canvas`** — `pub fn sync_to_current_canvas(&mut self) -> bool {...}`
- `fn` **`create_shader_module`** — `pub(crate) fn create_shader_module<S>(&self, code: S) -> JsValue where S: AsRef<str>, {...}`
- `fn` **`create_command_encoder`** — `pub(crate) fn create_command_encoder(&self) -> JsValue {...}`
- `fn` **`get_current_texture_view`** — `pub(crate) fn get_current_texture_view(&self) -> JsValue {...}`
- `fn` **`begin_render_pass`** — `pub(crate) fn begin_render_pass(&mut self, encoder: &JsValue, clear_color: Color) -> JsValue {...}`
- `fn` **`begin_render_pass_full`** — `pub fn begin_render_pass_full( &mut self, encoder: &JsValue, color: &ColorAttachment, depth: Option<&DepthStencilAttachment>, ) -> JsValue {...}`
- `fn` **`submit`** — `pub fn submit(&self, command_buffers: &[JsValue]) {...}`
- `fn` **`create_render_pipeline`** — `pub fn create_render_pipeline<S>(&self, shader_code: S) -> JsValue where S: AsRef<str>, {...}`
- `fn` **`create_render_pipeline_full`** — `pub fn create_render_pipeline_full(&self, descriptor: &RenderPipelineDescriptor) -> JsValue {...}`
- `fn` **`set_pipeline`** — `pub(crate) fn set_pipeline(&self, pass: &JsValue, pipeline: &JsValue) {...}`
- `fn` **`set_vertex_buffer`** — `pub fn set_vertex_buffer(&self, pass: &JsValue, slot: u32, buffer: &JsValue) {...}`
- `fn` **`set_index_buffer`** — `pub fn set_index_buffer(&self, pass: &JsValue, buffer: &JsValue, format: IndexFormat) {...}`
- `fn` **`draw`** — `pub fn draw(&self, pass: &JsValue, args: &DrawArgs) {...}`
- `fn` **`draw_indexed`** — `pub fn draw_indexed(&self, pass: &JsValue, args: &DrawIndexedArgs) {...}`
- `fn` **`draw_indexed_offset`** — `pub fn draw_indexed_offset( &self, pass: &JsValue, index_offset: u32, index_count: u32, instance_count: u32, ) {...}`
- `fn` **`end_render_pass`** — `pub(crate) fn end_render_pass(&self, pass: &JsValue) {...}`
- `fn` **`finish_command_encoder`** — `pub(crate) fn finish_command_encoder(&self, encoder: &JsValue) -> JsValue {...}`
- `fn` **`create_uniform_buffer`** — `pub fn create_uniform_buffer(&self, data: &[f32]) -> JsValue {...}`
- `fn` **`update_uniform_buffer`** — `pub fn update_uniform_buffer(&self, buffer: &JsValue, data: &[f32]) {...}`
- `fn` **`create_compute_pipeline`** — `pub fn create_compute_pipeline<S>(&self, shader_code: S, entry_point: &str) -> JsValue where S: AsRef<str>, {...}`
- `fn` **`begin_compute_pass`** — `pub fn begin_compute_pass(&self, encoder: &JsValue) -> JsValue {...}`
- `fn` **`dispatch`** — `pub fn dispatch(&self, pass: &JsValue, args: &DispatchArgs) {...}`
- `fn` **`push_error_scope`** — `pub fn push_error_scope(&self, filter: GpuErrorFilter) {...}`
- `fn` **`pop_error_sync`** — `pub(crate) fn pop_error_sync(&self) -> Option<JsValue> {...}`
- `fn` **`take_last_error`** — `pub fn take_last_error(&self) -> Option<JsValue> {...}`
- `fn` **`begin_render_pass_to_texture`** — `pub fn begin_render_pass_to_texture( &mut self, encoder: &JsValue, color_view: &JsValue, clear_color: Option<Color>, depth_view: Option<&JsValue>, depth_clear: Option<f64>, ) -> JsValue {...}`
- `fn` **`copy_texture_to_buffer`** — `pub fn copy_texture_to_buffer( &self, source: &JsValue, destination: &JsValue, bytes_per_row: u32, width: u32, height: u32, ) {...}`
- `fn` **`create_offline_render_target`** — `pub fn create_offline_render_target( &self, width: u32, height: u32, format: &str, ) -> (JsValue, JsValue) {...}`
- `fn` **`create_texture_view`** — `pub fn create_texture_view(&self, texture: &JsValue) -> JsValue {...}`
- `fn` **`on_device_lost`** — `pub fn on_device_lost(&mut self, callback: Function) {...}`
- `fn` **`create_buffer`** — `pub(crate) fn create_buffer(&self, descriptor: &BufferDescriptor) -> JsValue {...}`
- `fn` **`create_vertex_buffer`** — `pub fn create_vertex_buffer(&self, data: &[u8]) -> JsValue {...}`
- `fn` **`create_index_buffer`** — `pub fn create_index_buffer(&self, data: &[u8]) -> JsValue {...}`
- `fn` **`write_buffer`** — `pub fn write_buffer(&self, buffer: &JsValue, offset: u64, data: &[u8]) {...}`
- `fn` **`create_depth_texture`** — `pub(crate) fn create_depth_texture(&mut self) -> Option<JsValue> {...}`
- `fn` **`create_texture_2d`** — `pub fn create_texture_2d(&self, descriptor: &Texture2DDescriptor) -> JsValue {...}`
- `fn` **`create_texture`** — `pub fn create_texture(&self, descriptor: &TextureDescriptor) -> JsValue {...}`
- `fn` **`create_sampler`** — `pub fn create_sampler(&self, descriptor: &SamplerDescriptor) -> JsValue {...}`
- `fn` **`create_uniform_bind_group`** — `pub fn create_uniform_bind_group(&self, pipeline: &JsValue, buffer: &JsValue) -> JsValue {...}`
- `fn` **`create_bind_group`** — `pub fn create_bind_group( &self, pipeline: &JsValue, index: u32, entries: &[BindGroupEntry], ) -> JsValue {...}`
- `fn` **`set_bind_group`** — `pub(crate) fn set_bind_group(&self, pass: &JsValue, index: u32, bind_group: &JsValue) {...}`
- `fn` **`set_bind_group_on`** — `pub(crate) fn set_bind_group_on( &self, class: GpuReceiverClass, pass: &JsValue, index: u32, bind_group: &JsValue, ) {...}`
- `fn` **`render_frame`** — `pub fn render_frame(&mut self, pipeline: &JsValue, clear_color: Color, vertex_count: u32) {...}`
- `fn` **`render_frame_with_bind_group`** — `pub fn render_frame_with_bind_group( &mut self, pipeline: &JsValue, bind_group: &JsValue, clear_color: Color, vertex_count: u32, ) {...}`
- `fn` **`set_compute_pipeline`** — `pub fn set_compute_pipeline(&self, pass: &JsValue, pipeline: &JsValue) {...}`
- `fn` **`create_bind_group_for_layout`** — `pub fn create_bind_group_for_layout( &self, layout: &JsValue, entries: &[BindGroupEntry], ) -> JsValue {...}`
- `fn` **`create_bind_group_layout`** — `pub fn create_bind_group_layout(&self, entries: &[BindGroupLayoutEntry]) -> JsValue {...}`
- `fn` **`dispatch_with_bind_group`** — `pub fn dispatch_with_bind_group( &self, pass: &JsValue, pipeline: &JsValue, bind_group: &JsValue, args: &DispatchArgs, ) {...}`
- `fn` **`create_storage_texture`** — `pub fn create_storage_texture(&self, width: u32, height: u32, format: &str) -> JsValue {...}`
- `fn` **`create_timestamp_query_set`** — `pub fn create_timestamp_query_set(&self, count: u32) -> JsValue {...}`
- `fn` **`write_timestamp`** — `pub fn write_timestamp(&self, pass: &JsValue, query_set: &JsValue, index: u32) {...}`
- `fn` **`resolve_timestamp`** — `pub fn resolve_timestamp( &self, encoder: &JsValue, query_set: &JsValue, first_query: u32, query_count: u32, destination: &JsValue, destination_offset: u64, ) {...}`
- `fn` **`create_render_pipeline_with_layout`** — `pub fn create_render_pipeline_with_layout( &self, descriptor: &RenderPipelineDescriptor, layout: &JsValue, ) -> JsValue {...}`
- `fn` **`dispose`** — `pub fn dispose(&self) {...}`
- `fn` **`set_viewport`** — `pub fn set_viewport(&self, pass: &JsValue, viewport: &ViewportDescriptor) {...}`
- `fn` **`set_scissor_rect`** — `pub fn set_scissor_rect(&self, pass: &JsValue, x: u32, y: u32, width: u32, height: u32) {...}`
- `fn` **`set_blend_constant`** — `pub fn set_blend_constant(&self, pass: &JsValue, r: f32, g: f32, b: f32, a: f32) {...}`
- `fn` **`set_stencil_reference`** — `pub fn set_stencil_reference(&self, pass: &JsValue, reference: u32) {...}`
- `fn` **`set_bind_group_with_dynamic_offsets`** — `pub fn set_bind_group_with_dynamic_offsets( &self, pass: &JsValue, index: u32, group: &JsValue, dynamic_offsets: &[u32], ) {...}`
- `fn` **`set_bind_group_compute_with_dynamic_offsets`** — `pub fn set_bind_group_compute_with_dynamic_offsets( &self, pass: &JsValue, index: u32, group: &JsValue, dynamic_offsets: &[u32], ) {...}`
- `fn` **`create_view`** — `pub fn create_view( &self, texture: &JsValue, descriptor: Option<&TextureViewDescriptor>, ) -> JsValue {...}`
- `fn` **`generate_mipmaps`** — `pub fn generate_mipmaps(&self, texture: &JsValue) {...}`
- `fn` **`write_texture`** — `pub fn write_texture(&self, descriptor: &TextureWriteDescriptor) {...}`
- `fn` **`create_shader_module_with_label`** — `pub fn create_shader_module_with_label(&self, wgsl_source: &str, label: &str) -> JsValue {...}`
- `fn` **`read_buffer`** — `pub async fn read_buffer(&self, buffer: &JsValue, offset: u64, size: u64) -> Option<Vec<u8>> {...}`
- `fn` **`code`** — `pub fn code(&self) -> &'static str {...}`
- `fn` **`js_error`** — `pub fn js_error(&self) -> Option<&JsValue> {...}`
- `fn` **`new`** — `pub fn new() -> Self {...}`
- `fn` **`as_ptr`** — `pub(crate) fn as_ptr(&self) -> *mut Option<JsValue> {...}`

### `renderer::webgpu::struct`

- `struct` **`WebGpuRendererInit`** — `pub struct WebGpuRendererInit {`
- `struct` **`WebGpuRenderer`** — `pub struct WebGpuRenderer {`
- `struct` **`RenderPassDescriptorCache`** — `pub struct RenderPassDescriptorCache {`
- `struct` **`PendingErrorCell`** — `pub(crate) struct PendingErrorCell( pub(crate) UnsafeCell<Option<JsValue>>, );`

### `raytracing::backend::canvas::fn`

- `fn` **`attach_canvas_context`** — `pub(crate) fn attach_canvas_context( canvas: &HtmlCanvasElement, ) -> Result<CanvasRenderingContext2d, JsValue> {...}`
- `fn` **`allocate_canvas_surface`** — `pub(crate) fn allocate_canvas_surface( width: u32, height: u32, ) -> Result<(ImageData, Uint8ClampedArray), JsValue> {...}`
- `fn` **`surface_rgba_length`** — `pub(crate) fn surface_rgba_length(width: u32, height: u32) -> Option<usize> {...}`

### `raytracing::backend::canvas::impl`

- `fn` **`attach`** — `pub fn attach(canvas: &HtmlCanvasElement, width: u32, height: u32) -> Result<Self, JsValue> {...}`
- `fn` **`dimension_limit`** — `pub fn dimension_limit(&self) -> Option<u32> {...}`
- `fn` **`resize`** — `pub fn resize(&mut self, width: u32, height: u32) -> Result<(), JsValue> {...}`
- `fn` **`present`** — `pub fn present(&mut self, pixels: &[u8]) -> Result<(), JsValue> {...}`
- `fn` **`release`** — `pub fn release(&mut self) {...}`

### `raytracing::backend::canvas::struct`

- `struct` **`CanvasRayTraceBackend`** — `pub struct CanvasRayTraceBackend {`

### `raytracing::backend::data::enum`

- `enum` **`RayTraceBackend`** — `pub enum RayTraceBackend {`

### `raytracing::backend::data::fn`

- `fn` **`describe`** — `pub(crate) fn describe(reason: &JsValue) -> String {...}`
- `fn` **`backend_error`** — `pub(crate) fn backend_error(code: &str, detail: String) -> JsValue {...}`
- `fn` **`validate_surface`** — `pub(crate) fn validate_surface( width: u32, height: u32, limit: Option<u32>, ) -> Result<usize, JsValue> {...}`
- `fn` **`resize_pixel_buffer`** — `pub(crate) fn resize_pixel_buffer(pixels: &mut Vec<u8>, length: usize) {...}`

### `raytracing::backend::data::impl`

- `fn` **`init`** — `pub async fn init( canvas: HtmlCanvasElement, backend: RayTraceBackend, scene: &RayTraceScene, ) -> Result<Self, JsValue> {...}`
- `fn` **`update_scene`** — `pub fn update_scene(&mut self, scene: &RayTraceScene) -> Result<(), JsValue> {...}`
- `fn` **`render`** — `pub fn render( &mut self, camera: &Camera3D, lights: &LightingUniforms, settings: &RayTraceSettings, ) -> Result<(), JsValue> {...}`
- `fn` **`resize`** — `pub fn resize(&mut self, width: u32, height: u32) -> Result<(), JsValue> {...}`
- `fn` **`dispose`** — `pub fn dispose(&mut self) {...}`
- `fn` **`release_backend`** — `pub(crate) fn release_backend(&mut self) {...}`

### `raytracing::backend::data::struct`

- `struct` **`RayTraceRenderer`** — `pub struct RayTraceRenderer {`

### `raytracing::backend::state::enum`

- `enum` **`RayTraceBackendAdapter`** — `pub(crate) enum RayTraceBackendAdapter {`

### `raytracing::backend::state::impl`

- `fn` **`attach`** — `pub(crate) async fn attach( canvas: &HtmlCanvasElement, backend: RayTraceBackend, width: u32, height: u32, ) -> Result<Self, JsValue> {...}`
- `fn` **`dimension_limit`** — `pub(crate) fn dimension_limit(&self) -> Option<u32> {...}`
- `fn` **`resize`** — `pub(crate) fn resize(&mut self, width: u32, height: u32) -> Result<(), JsValue> {...}`
- `fn` **`upload_scene`** — `pub(crate) fn upload_scene(&mut self, packed: &[f32]) -> Result<(), JsValue> {...}`
- `fn` **`draw`** — `pub(crate) fn draw(&mut self, frame: &[f32]) -> Result<(), JsValue> {...}`
- `fn` **`present`** — `pub(crate) fn present(&mut self, pixels: &[u8]) -> Result<(), JsValue> {...}`
- `fn` **`release`** — `pub(crate) fn release(&mut self) {...}`

### `raytracing::backend::webgl::fn`

- `fn` **`describe_webgl`** — `pub(crate) fn describe_webgl(reason: &JsValue) -> String {...}`
- `fn` **`compile_stage`** — `pub(crate) fn compile_stage( context: &WebGl2RenderingContext, vertex: bool, source: &str, ) -> Result<WebGlShader, JsValue> {...}`
- `fn` **`link_raytrace_program`** — `pub(crate) fn link_raytrace_program( context: &WebGl2RenderingContext, ) -> Result<WebGlProgram, JsValue> {...}`
- `fn` **`resolve_sampler`** — `pub(crate) fn resolve_sampler( context: &WebGl2RenderingContext, program: &WebGlProgram, name: &str, ) -> Result<WebGlUniformLocation, JsValue> {...}`
- `fn` **`require_clear_gl_error`** — `pub(crate) fn require_clear_gl_error( context: &WebGl2RenderingContext, code: &'static str, call: &str, ) -> Result<(), JsValue> {...}`
- `fn` **`packed_slot_count`** — `pub(crate) fn packed_slot_count(floats: usize) -> usize {...}`
- `fn` **`packed_shape`** — `pub(crate) fn packed_shape(floats: usize, limit: u32) -> Result<(i32, i32), JsValue> {...}`
- `fn` **`validate_block_capacity`** — `pub(crate) fn validate_block_capacity(floats: usize, limit: u32) -> Result<(), JsValue> {...}`
- `fn` **`create_packed_texture`** — `pub(crate) fn create_packed_texture( context: &WebGl2RenderingContext, unit: u32, width: i32, height: i32, ) -> Result<WebGlRayTraceTexture, JsValue> {...}`
- `fn` **`bind_data_texture`** — `pub(crate) fn bind_data_texture( context: &WebGl2RenderingContext, unit: u32, texture: &WebGlTexture, ) -> Result<(), JsValue> {...}`
- `fn` **`upload_packed`** — `pub(crate) fn upload_packed( upload: &WebGlPackedUpload, target: &WebGlRayTraceTexture, scratch: &mut Vec<f32>, ) -> Result<(), JsValue> {...}`
- `fn` **`ensure_packed_texture`** — `pub(crate) fn ensure_packed_texture( upload: &WebGlPackedUpload, current: &mut WebGlRayTraceTexture, scratch: &mut Vec<f32>, ) -> Result<(), JsValue> {...}`
- `fn` **`texture_size_limit`** — `pub(crate) fn texture_size_limit(context: &WebGl2RenderingContext) -> u32 {...}`
- `fn` **`viewport_dimension_limit`** — `pub(crate) fn viewport_dimension_limit(context: &WebGl2RenderingContext) -> u32 {...}`
- `fn` **`validate_webgl_surface`** — `pub(crate) fn validate_webgl_surface( context: &WebGl2RenderingContext, width: u32, height: u32, limit: u32, ) -> Result<(), JsValue> {...}`
- `fn` **`apply_full_viewport`** — `pub(crate) fn apply_full_viewport(context: &WebGl2RenderingContext) -> Result<(), JsValue> {...}`
- `fn` **`attach_context`** — `pub(crate) fn attach_context( canvas: &HtmlCanvasElement, ) -> Result<WebGl2RenderingContext, JsValue> {...}`
- `fn` **`release_partial`** — `pub(crate) fn release_partial(context: &WebGl2RenderingContext, owned: &WebGlPartialAttach) {...}`

### `raytracing::backend::webgl::impl`

- `fn` **`attach`** — `pub fn attach(canvas: &HtmlCanvasElement, width: u32, height: u32) -> Result<Self, JsValue> {...}`
- `fn` **`dimension_limit`** — `pub fn dimension_limit(&self) -> Option<u32> {...}`
- `fn` **`resize`** — `pub fn resize(&mut self, width: u32, height: u32) -> Result<(), JsValue> {...}`
- `fn` **`draw`** — `pub fn draw(&mut self, frame: &[f32]) -> Result<(), JsValue> {...}`
- `fn` **`upload_scene`** — `pub fn upload_scene(&mut self, packed: &[f32]) -> Result<(), JsValue> {...}`
- `fn` **`release`** — `pub fn release(&mut self) {...}`

### `raytracing::backend::webgl::struct`

- `struct` **`WebGlRayTraceTexture`** — `pub(crate) struct WebGlRayTraceTexture {`
- `struct` **`WebGlRayTraceBackend`** — `pub(crate) struct WebGlRayTraceBackend {`
- `struct` **`WebGlPackedUpload`** — `pub(crate) struct WebGlPackedUpload<'a> {`
- `struct` **`WebGlPartialAttach`** — `pub(crate) struct WebGlPartialAttach<'a> {`

### `raytracing::backend::webgpu::fn`

- `fn` **`describe_webgpu`** — `pub(crate) fn describe_webgpu(reason: &JsValue) -> String {...}`
- `fn` **`descriptor`** — `pub(crate) fn descriptor(pairs: &[(&str, JsValue)]) -> Result<Object, JsValue> {...}`
- `fn` **`attribute`** — `pub(crate) fn attribute(target: &JsValue, name: &str) -> Result<JsValue, JsValue> {...}`
- `fn` **`method`** — `pub(crate) fn method(target: &JsValue, name: &str) -> Result<Function, JsValue> {...}`
- `fn` **`call1`** — `pub(crate) fn call1(target: &JsValue, name: &str, argument: &JsValue) -> Result<JsValue, JsValue> {...}`
- `fn` **`call0`** — `pub(crate) fn call0(target: &JsValue, name: &str) -> Result<JsValue, JsValue> {...}`
- `fn` **`call2`** — `pub(crate) fn call2( target: &JsValue, name: &str, first: &JsValue, second: &JsValue, ) -> Result<JsValue, JsValue> {...}`
- `fn` **`draw_vertices`** — `pub(crate) fn draw_vertices(pass: &JsValue, args: &DrawArgs) -> Result<JsValue, JsValue> {...}`
- `fn` **`await_promise`** — `pub(crate) async fn await_promise(pending: JsValue) -> Result<JsValue, JsValue> {...}`
- `fn` **`pop_validation_scope`** — `pub(crate) async fn pop_validation_scope(device: &JsValue) -> Result<Option<String>, JsValue> {...}`
- `fn` **`navigator_gpu`** — `pub(crate) fn navigator_gpu() -> Result<JsValue, JsValue> {...}`
- `fn` **`preferred_format`** — `pub(crate) fn preferred_format(gpu: &JsValue) -> String {...}`
- `fn` **`configure_context`** — `pub(crate) fn configure_context( canvas: &HtmlCanvasElement, device: &JsValue, format_name: &str, ) -> Result<JsValue, JsValue> {...}`
- `fn` **`packed_byte_length`** — `pub(crate) fn packed_byte_length(floats: usize) -> u32 {...}`
- `fn` **`number_property`** — `pub(crate) fn number_property(target: &JsValue, name: &str) -> Option<f64> {...}`
- `fn` **`device_limit`** — `pub(crate) fn device_limit(device: &JsValue, name: &str) -> u32 {...}`
- `fn` **`observe_device`** — `pub(crate) fn observe_device( device: &JsValue, failure: &Rc<RefCell<Option<String>>>, ) -> Result<JsValue, JsValue> {...}`
- `fn` **`unregister_error_listener`** — `pub(crate) fn unregister_error_listener(device: &JsValue, listener: &JsValue) {...}`
- `fn` **`lost_reason`** — `pub(crate) fn lost_reason(info: &JsValue) -> String {...}`
- `fn` **`is_device_lost`** — `pub(crate) fn is_device_lost(recorded: &str) -> bool {...}`
- `fn` **`rejection`** — `pub(crate) fn rejection(pending: Option<String>) -> Result<(), JsValue> {...}`
- `fn` **`scope_message`** — `pub(crate) fn scope_message(resolved: &JsValue) -> Option<String> {...}`
- `fn` **`compilation_messages`** — `pub(crate) fn compilation_messages(info: &JsValue) -> String {...}`
- `fn` **`write_packed`** — `pub(crate) fn write_packed( queue: &JsValue, buffer: &JsValue, packed: &[f32], ) -> Result<(), JsValue> {...}`
- `fn` **`destroy_buffer`** — `pub(crate) fn destroy_buffer(buffer: &JsValue) -> Result<(), JsValue> {...}`
- `fn` **`destroy_device`** — `pub(crate) fn destroy_device(device: &JsValue) {...}`
- `fn` **`abandon`** — `pub(crate) fn abandon( device: &JsValue, scene: Option<&JsValue>, frame: Option<&JsValue>, context: Option<&JsValue>, ) {...}`
- `fn` **`packed_layout`** — `pub(crate) fn packed_layout(device: &JsValue) -> Result<JsValue, JsValue> {...}`
- `fn` **`bind_group_of`** — `pub(crate) fn bind_group_of( device: &JsValue, scene: &JsValue, frame: &JsValue, layout: &JsValue, ) -> Result<JsValue, JsValue> {...}`
- `fn` **`clear_attachment`** — `pub(crate) fn clear_attachment(view: &JsValue) -> Result<Object, JsValue> {...}`

### `raytracing::backend::webgpu::impl`

- `fn` **`attach`** — `pub async fn attach(canvas: &HtmlCanvasElement) -> Result<Self, JsValue> {...}`
- `fn` **`dimension_limit`** — `pub fn dimension_limit(&self) -> Option<u32> {...}`
- `fn` **`resize`** — `pub fn resize(&mut self, width: u32, height: u32) -> Result<(), JsValue> {...}`
- `fn` **`upload_scene`** — `pub fn upload_scene(&mut self, packed: &[f32]) -> Result<(), JsValue> {...}`
- `fn` **`draw`** — `pub fn draw(&mut self, frame: &[f32]) -> Result<(), JsValue> {...}`
- `fn` **`release`** — `pub fn release(&mut self) {...}`
- `fn` **`pending_failure`** — `pub(crate) fn pending_failure(&self) -> Option<String> {...}`
- `fn` **`byte_ceiling`** — `pub(crate) fn byte_ceiling(&self) -> u32 {...}`

### `raytracing::backend::webgpu::struct`

- `struct` **`WebGpuRayTraceBackend`** — `pub struct WebGpuRayTraceBackend {`

### `raytracing::pipeline::data::fn`

- `fn` **`pack_finite`** — `pub fn pack_finite(value: f64, non_finite: &str, out_of_range: &str) -> Result<f32, String> {...}`
- `fn` **`next_down`** — `pub(crate) fn next_down(value: f32) -> f32 {...}`
- `fn` **`next_up`** — `pub(crate) fn next_up(value: f32) -> f32 {...}`
- `fn` **`pack_lower_bound`** — `pub(crate) fn pack_lower_bound(value: f64) -> Result<f32, String> {...}`
- `fn` **`pack_upper_bound`** — `pub(crate) fn pack_upper_bound(value: f64) -> Result<f32, String> {...}`
- `fn` **`pack_vector`** — `pub fn pack_vector( vector: Vector3D, non_finite: &str, out_of_range: &str, ) -> Result<[f32; {...}`
- `fn` **`pack_vector_lower`** — `pub fn pack_vector_lower( vector: Vector3D, non_finite: &str, out_of_range: &str, ) -> Result<[f32; {...}`
- `fn` **`pack_vector_upper`** — `pub fn pack_vector_upper( vector: Vector3D, non_finite: &str, out_of_range: &str, ) -> Result<[f32; {...}`
- `fn` **`pack_index`** — `pub fn pack_index(index: usize) -> Result<f32, String> {...}`
- `fn` **`packed_shape_code`** — `pub fn packed_shape_code(kind: OccluderKind) -> f32 {...}`
- `fn` **`packed_material_code`** — `pub fn packed_material_code(kind: MaterialKind) -> f32 {...}`
- `fn` **`packed_light_code`** — `pub fn packed_light_code(kind: LightType) -> f32 {...}`
- `fn` **`half_ulp`** — `pub(crate) fn half_ulp(probe: f32) -> f64 {...}`
- `fn` **`pack_sphere_radius`** — `pub fn pack_sphere_radius(center: Vector3D, radius: f64) -> Result<f32, String> {...}`
- `fn` **`pack_primitive`** — `pub(crate) fn pack_primitive( out: &mut Vec<f32>, occluder: &Occluder, original_index: usize, ) -> Result<(), String> {...}`
- `fn` **`pack_node`** — `pub(crate) fn pack_node(out: &mut Vec<f32>, node: &RayTraceNode) -> Result<(), String> {...}`
- `fn` **`frame_basis`** — `pub(crate) fn frame_basis( camera: &Camera3D, width: u32, height: u32, ) -> Result<FrameBasis, String> {...}`
- `fn` **`pack_raytrace_frame`** — `pub fn pack_raytrace_frame(out: &mut Vec<f32>, frame: &RayTraceFrame<'_>) -> Result<(), String> {...}`

### `raytracing::pipeline::data::impl`

- `fn` **`new_default`** — `pub fn new_default() -> RayTraceSettings {...}`
- `fn` **`with_quality`** — `pub fn with_quality(samples_per_axis: u32, max_bounces: u32) -> RayTraceSettings {...}`
- `fn` **`rays_per_pixel`** — `pub fn rays_per_pixel(&self) -> u32 {...}`
- `fn` **`validate`** — `pub fn validate(&self) -> Result<(), String> {...}`
- `fn` **`encode_gpu`** — `pub fn encode_gpu(&self) -> Result<Vec<f32>, String> {...}`

### `raytracing::pipeline::data::struct`

- `struct` **`RayTraceSettings`** — `pub struct RayTraceSettings {`
- `struct` **`RayTraceFrame`** — `pub struct RayTraceFrame<'a> {`
- `struct` **`FrameBasis`** — `pub(crate) struct FrameBasis {`

### `raytracing::pipeline::render::fn`

- `fn` **`pixel_direction`** — `pub(crate) fn pixel_direction(basis: &FrameBasis, sample: &PixelSample) -> Vector3D {...}`
- `fn` **`gamma_byte`** — `pub fn gamma_byte(channel: f64) -> u8 {...}`
- `fn` **`render_raytrace_rgba`** — `pub fn render_raytrace_rgba( scene: &RayTraceScene, frame: &RayTraceFrame<'_>, out: &mut Vec<u8>, ) -> Result<(), String> {...}`

### `raytracing::pipeline::render::struct`

- `struct` **`PixelSample`** — `pub(crate) struct PixelSample {`

### `raytracing::pipeline::shader::source::fn`

- `fn` **`raytrace_glsl_vertex`** — `pub fn raytrace_glsl_vertex() -> &'static str {...}`
- `fn` **`raytrace_glsl_fragment`** — `pub fn raytrace_glsl_fragment() -> &'static str {...}`
- `fn` **`raytrace_wgsl`** — `pub fn raytrace_wgsl() -> &'static str {...}`
