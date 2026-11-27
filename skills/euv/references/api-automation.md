# euv-automation full pub API

Source: `automation/src/` at `origin/master` (`aac1c450d6e8317c50c01dd6225dea7a29265495`, version 0.39.1),
extracted from `pub` declarations.
Re-verified against `origin/master` (`6ccb8599`, euv 0.43.0) on 2026-11-27: every declared API name below still resolves in that tree.

Dev-only: every hook compiles to a no-op outside `debug_assertions`
(`#[cfg(not(debug_assertions))]`), so release builds carry no automation code.
The `euv.ai.schema.v1` protocol (`AiSchemaProtocol`) exposes snapshot, a11y
tree, node query, hit-test, action and script ops over a local dev bridge.

### dev_gate
- (const) pub const DEV_AI_INSPECTOR_ADDR: &str = "127.0.0.1:4174";
- (impl) pub const fn is_enabled() -> bool {
- (impl) pub fn start(addr: &str) -> Self {
- (impl) pub fn with_hooks(mut self, hooks: AiAppHooks) -> Self {
- (impl) pub fn bound_address(&self) -> Option<&str> {
- (impl) pub fn poll(&mut self, app: &mut App) -> usize {
- (impl) pub const fn is_enabled() -> bool {
- (impl) pub const fn start(_addr: &str) -> Self {
- (impl) pub fn with_hooks(self, _hooks: AiAppHooks) -> Self {
- (impl) pub const fn bound_address(&self) -> Option<&str> {
- (impl) pub fn poll(&mut self, _app: &mut App) -> usize {
- (mod) pub use {r#const::*, r#struct::*};
- (struct) pub struct DevAutomationBridge {
- (struct) pub struct DevAutomationBridge;

### driver
- (enum) pub enum AutomationError {
- (enum) pub enum UiTestStep {
- (impl) pub fn new(app: &'a mut App) -> Self {
- (impl) pub fn app_ref(&self) -> &App {
- (impl) pub fn step(&mut self) -> Result<FrameStats, AutomationError> {
- (impl) pub fn query_all(&self, selector: &UiSelector) -> Vec<AiLayoutNode> {
- (impl) pub fn query(&self, selector: &UiSelector) -> Result<AiLayoutNode, AutomationError> {
- (impl) pub fn exists(&self, selector: &UiSelector) -> bool {
- (impl) pub fn wait_until( &mut self, selector: &UiSelector, max_frames: usize, ) -> Result<AiLayoutNode, AutomationError> {
- (impl) pub fn hover(&mut self, selector: &UiSelector) -> Result<FrameStats, AutomationError> {
- (impl) pub fn click_at(&mut self, x: f32, y: f32) -> Result<FrameStats, AutomationError> {
- (impl) pub fn click(&mut self, selector: &UiSelector) -> Result<FrameStats, AutomationError> {
- (impl) pub fn focus(&mut self, selector: &UiSelector) -> Result<FrameStats, AutomationError> {
- (impl) pub fn double_click(&mut self, selector: &UiSelector) -> Result<FrameStats, AutomationError> {
- (impl) pub fn type_text( &mut self, selector: &UiSelector, text: &str, ) -> Result<FrameStats, AutomationError> {
- (impl) pub fn clear_input(&mut self, selector: &UiSelector) -> Result<FrameStats, AutomationError> {
- (impl) pub fn drag_points( &mut self, from_x: f32, from_y: f32, to_x: f32, to_y: f32, ) -> Result<FrameStats, AutomationError> {
- (impl) pub fn drag( &mut self, from: &UiSelector, to: &UiSelector, ) -> Result<FrameStats, AutomationError> {
- (impl) pub fn gesture( &mut self, kind: AiGestureKind, x: f32, y: f32, dx: f32, dy: f32, scale: f32, ) -> Result<FrameStats, AutomationError> {
- (impl) pub fn step_frames(&mut self, count: usize) -> Result<FrameStats, AutomationError> {
- (impl) pub fn step_game( &mut self, dt_secs: f32, frames: usize, ) -> Result<FrameStats, AutomationError> {
- (impl) pub fn set_fps_limit(&mut self, fps: Option<u32>) -> Result<FrameStats, AutomationError> {
- (impl) pub fn press_key_name(&mut self, key: &str) -> Result<FrameStats, AutomationError> {
- (impl) pub fn press_key(&mut self, code: KeyCode) -> Result<FrameStats, AutomationError> {
- (impl) pub fn scroll( &mut self, selector: &UiSelector, dx: f32, dy: f32, ) -> Result<FrameStats, AutomationError> {
- (impl) pub fn resize( &mut self, width: u32, height: u32, scale: f32, ) -> Result<FrameStats, AutomationError> {
- (impl) pub fn assert_visible(&self, selector: &UiSelector) -> Result<(), AutomationError> {
- (impl) pub fn assert_no_horizontal_overflow(&self) -> Result<(), AutomationError> {
- (impl) pub fn assert_no_text_overlap(&self) -> Result<(), AutomationError> {
- (impl) pub fn assert_not_visible(&self, selector: &UiSelector) -> Result<(), AutomationError> {
- (impl) pub fn assert_text_equals( &self, selector: &UiSelector, expected: &str, ) -> Result<(), AutomationError> {
- (impl) pub fn run_script(&mut self, script: &UiTestScript) -> UiTestReport {
- (mod) pub use {r#enum::*, r#struct::*};
- (struct) pub struct UiTestScript {
- (struct) pub struct UiStepResult {
- (struct) pub struct UiTestReport {
- (struct) pub struct UiAutomator<'a> {

### crate root
- (lib) pub use {dev_gate::*, driver::*, schema::*, selector::*};

### schema
- (const) pub const AI_SCHEMA_PROTOCOL_VERSION: &str = "euv.ai.schema.v1";
- (const) pub const AI_SCHEMA_JSON_SPEC: &str = r#"{
- (enum) pub enum AiAnomalyKind {
- (enum) pub enum AiGestureKind {
- (enum) pub enum AiAction {
- (enum) pub enum AiSchemaRequest {
- (impl) pub fn from_rect(rect: Rect) -> Self {
- (impl) pub fn center(&self) -> Point {
- (impl) pub fn right(&self) -> f32 {
- (impl) pub fn bottom(&self) -> f32 {
- (impl) pub fn text_value(&self) -> Option<&str> {
- (impl) pub fn placeholder_value(&self) -> Option<&str> {
- (impl) pub fn input_value(&self) -> Option<&str> {
- (impl) pub fn a11y_label_value(&self) -> Option<&str> {
- (impl) pub fn a11y_hint_value(&self) -> Option<&str> {
- (impl) pub fn find_matches(&self, selector: &UiSelector) -> Vec<AiLayoutNode> {
- (impl) pub fn active_route_value(&self) -> Option<&str> {
- (impl) pub fn active_scheme_value(&self) -> Option<&str> {
- (impl) pub fn root_layout_node(&self) -> Option<&AiLayoutNode> {
- (impl) pub fn game_stats_value(&self) -> Option<&Value> {
- (impl) pub fn on_route<F>(mut self, getter: F) -> Self where F: Fn() -> String + 'static, {
- (impl) pub fn on_scheme<F>(mut self, getter: F) -> Self where F: Fn() -> String + 'static, {
- (impl) pub fn on_game_stats<F>(mut self, getter: F) -> Self where F: Fn() -> Value + 'static, {
- (impl) pub fn on_navigate<F>(mut self, handler: F) -> Self where F: FnMut(&str) -> Result<(), String> + 'static, {
- (impl) pub fn on_set_theme<F>(mut self, handler: F) -> Self where F: FnMut(Option<&str>, Option<&str>) -> Result<(), String> + 'static, {
- (impl) pub fn on_game_control<F>(mut self, handler: F) -> Self where F: FnMut(&str, &Value) -> Result<Value, String> + 'static, {
- (impl) pub fn success(data: Value) -> Self {
- (impl) pub fn failure(message: String) -> Self {
- (impl) pub fn error_message(&self) -> Option<&str> {
- (impl) pub fn accessibility_tree(app: &App) -> Vec<AiA11yNode> {
- (impl) pub fn snapshot(app: &App, include_layout_tree: bool) -> AiRuntimeSnapshot {
- (impl) pub fn snapshot_with_hooks( app: &App, include_layout_tree: bool, hooks: Option<&AiAppHooks>, ) -> AiRuntimeSnapshot {
- (impl) pub fn hit_test_at(app: &App, x: f32, y: f32) -> AiHitTestResult {
- (impl) pub fn handle(app: &mut App, request: AiSchemaRequest) -> AiSchemaResponse {
- (impl) pub fn handle_with_hooks( app: &mut App, request: AiSchemaRequest, hooks: Option<&AiAppHooks>, ) -> AiSchemaResponse {
- (impl) pub fn handle_json(app: &mut App, request_json: &str) -> String {
- (impl) pub fn handle_json_with_hooks( app: &mut App, request_json: &str, hooks: Option<&AiAppHooks>, ) -> String {
- (impl) pub fn parse_json_value(raw: &str) -> Value {
- (impl) pub fn snapshot_pretty_json(app: &App) -> String {
- (impl) pub fn snapshot_pretty_json_with_hooks(app: &App, hooks: Option<&AiAppHooks>) -> String {
- (mod) pub use {r#const::*, r#enum::*, r#struct::*, r#type::*};
- (struct) pub struct AiRect {
- (struct) pub struct AiWindowInfo {
- (struct) pub struct AiPerfInfo {
- (struct) pub struct AiReactiveInfo {
- (struct) pub struct AiA11yNode {
- (struct) pub struct AiInteractionInfo {
- (struct) pub struct AiRuntimeMeta {
- (struct) pub struct AiStyleSummary {
- (struct) pub struct AiLayoutNode {
- (struct) pub struct AiLayoutAnomaly {
- (struct) pub struct AiRuntimeSnapshot {
- (struct) pub struct AiAppHooks {
- (struct) pub struct AiHitTestResult {
- (struct) pub struct AiSchemaResponse {
- (struct) pub struct AiSchemaProtocol;
- (type) pub type AiJsonValue = Value;
- (type) pub type AiRouteGetter = Rc<dyn Fn() -> String>;
- (type) pub type AiSchemeGetter = Rc<dyn Fn() -> String>;
- (type) pub type AiGameStatsGetter = Rc<dyn Fn() -> Value>;
- (type) pub type AiNavigateHandler = Rc<RefCell<dyn FnMut(&str) -> Result<(), String>>>;
- (type) pub type AiThemeHandler = Rc<RefCell<dyn FnMut(Option<&str>, Option<&str>) -> Result<(), String>>>;
- (type) pub type AiGameControlHandler = Rc<RefCell<dyn FnMut(&str, &Value) -> Result<Value, String>>>;

### selector
- (enum) pub enum UiSelector {
- (impl) pub fn text(label: &str) -> Self {
- (impl) pub fn text_contains(substr: &str) -> Self {
- (impl) pub fn placeholder(hint: &str) -> Self {
- (impl) pub fn input_value(value: &str) -> Self {
- (impl) pub fn a11y_label(label: &str) -> Self {
- (impl) pub fn role(role_name: &str) -> Self {
- (impl) pub fn kind(kind_name: &str) -> Self {
- (impl) pub fn nth(self, index: usize) -> Self {
- (impl) pub fn matches_node(&self, node: &AiLayoutNode) -> bool {
- (mod) pub use r#enum::*;

