# euv-ui full pub API

Source: `ui/src/` at `origin/master` (`aac1c450d6e8317c50c01dd6225dea7a29265495`, version 0.39.1), extracted from
`pub` declarations.

`euv-ui` is **not** re-exported through the `euv` root crate — add it as its
own dependency (`cargo add euv-ui`) and `use euv_ui::*`. Its only dependency is
`euv` (plus `lombok-macros`), and it ships 17 `theme-*` features plus
`default`; there is no `theme-custom` feature.

Modules: `component` (16 component groups), `hook`, `overlay_stack`,
`router`, `theme`. Components implement `Mountable`, so they compose inside
`view!` as `{ EuvButton::new(...) }` and mount with `.mount_current()`.

### component::button
- (enum) pub enum EuvButtonVariant {
- (enum) pub enum EuvButtonSize {
- (impl) pub fn on_click<F>(mut self, callback: F) -> Self where F: FnMut(&UiEvent) + 'static, {
- (impl) pub fn variant(mut self, variant: EuvButtonVariant) -> Self {
- (impl) pub fn size(mut self, size: EuvButtonSize) -> Self {
- (impl) pub fn secondary(self) -> Self {
- (impl) pub fn outline(self) -> Self {
- (impl) pub fn ghost(self) -> Self {
- (impl) pub fn destructive(self) -> Self {
- (impl) pub fn link(self) -> Self {
- (impl) pub fn sm(self) -> Self {
- (impl) pub fn lg(self) -> Self {
- (impl) pub fn icon(self) -> Self {
- (impl) pub fn disabled(mut self, disabled: bool) -> Self {
- (impl) pub fn resolved_style(&self) -> Style {
- (mod) pub use {r#enum::*, r#struct::*};
- (struct) pub struct EuvButton {

### component::card
- (impl) pub fn subtitle(mut self, subtitle: impl Into<String>) -> Self {
- (impl) pub fn child(mut self, child: NodeId) -> Self {
- (mod) pub use r#struct::*;
- (struct) pub struct EuvCard {
- (struct) pub struct EuvHeader {
- (struct) pub struct EuvStatCard {

### component::data_display
- (enum) pub enum EuvTypographyVariant {
- (impl) pub fn selected(mut self, selected: Signal<Option<String>>) -> Self {
- (mod) pub use {r#enum::*, r#struct::*};
- (struct) pub struct EuvTag {
- (struct) pub struct EuvAvatar {
- (struct) pub struct EuvIcon {
- (struct) pub struct EuvKbd {
- (struct) pub struct EuvTypography {
- (struct) pub struct EuvEmpty {
- (struct) pub struct EuvSkeleton {
- (struct) pub struct EuvSpinner {
- (struct) pub struct EuvTimelineItem {
- (struct) pub struct EuvTimeline {
- (struct) pub struct EuvList {
- (struct) pub struct EuvTreeNode {
- (struct) pub struct EuvTree {

### component::display
- (enum) pub enum EuvTone {
- (impl) pub fn colors(&self, palette: ThemePalette) -> (Color, Color) {
- (impl) pub fn tone(mut self, tone: EuvTone) -> Self {
- (impl) pub fn height(mut self, height: f32) -> Self {
- (impl) pub fn viewport_height(mut self, height: f32) -> Self {
- (impl) pub fn overscan(mut self, overscan: usize) -> Self {
- (impl) pub fn max_scroll_y(&self) -> f32 {
- (impl) pub fn scroll_by(&self, delta_y: f32) {
- (impl) pub fn visible_range(&self) -> (usize, usize) {
- (impl) pub fn mount_with<F>(&self, row_builder: F) -> NodeId where F: FnMut(usize) -> NodeId + 'static, {
- (mod) pub use {r#enum::*, r#struct::*};
- (struct) pub struct EuvBadge {
- (struct) pub struct EuvAlert {
- (struct) pub struct EuvProgress {
- (struct) pub struct EuvCodeBlock {
- (struct) pub struct EuvVirtualList {
- (struct) pub struct EuvTable {

### component::form
- (const) pub const CHECKBOX_MARK: &str = "x";
- (impl) pub fn password(mut self, password: bool) -> Self {
- (impl) pub fn disabled(mut self, disabled: bool) -> Self {
- (impl) pub fn borderless(mut self, borderless: bool) -> Self {
- (impl) pub fn error<S>(mut self, error: S) -> Self where S: Into<String>, {
- (mod) pub use {r#const::*, r#struct::*};
- (struct) pub struct EuvInput {
- (struct) pub struct EuvField {
- (struct) pub struct EuvSwitch {
- (struct) pub struct EuvCheckbox {
- (struct) pub struct EuvSegmented {

### component::form_extra
- (impl) pub fn field(mut self, node: NodeId) -> Self {
- (impl) pub fn range(mut self, min: i64, max: i64) -> Self {
- (impl) pub fn step(mut self, step: i64) -> Self {
- (impl) pub fn presets(mut self, presets: Vec<Color>) -> Self {
- (impl) pub fn placeholder<S>(mut self, placeholder: S) -> Self where S: Into<String>, {
- (mod) pub use r#struct::*;
- (struct) pub struct EuvLabel {
- (struct) pub struct EuvForm {
- (struct) pub struct EuvTextarea {
- (struct) pub struct EuvNumberInput {
- (struct) pub struct EuvRadioGroup {
- (struct) pub struct EuvSlider {
- (struct) pub struct EuvSelect {
- (struct) pub struct EuvRating {
- (struct) pub struct EuvColorPicker {
- (struct) pub struct EuvTimePicker {
- (struct) pub struct EuvTagInput {

### component::layout
- (impl) pub fn route(mut self, route_signal: Signal<String>) -> Self {
- (impl) pub fn top_bar_actions(mut self, actions: NodeId) -> Self {
- (impl) pub fn mobile_header_actions(mut self, actions: NodeId) -> Self {
- (impl) pub fn sidebar_footer(mut self, footer: NodeId) -> Self {
- (impl) pub fn breadcrumb(mut self, breadcrumb: Signal<String>) -> Self {
- (impl) pub fn horizontal(tokens: ThemeTokens) -> Self {
- (impl) pub fn vertical(tokens: ThemeTokens) -> Self {
- (impl) pub fn section(mut self, node: NodeId) -> Self {
- (impl) pub fn child(mut self, node: NodeId) -> Self {
- (impl) pub fn card(mut self, node: NodeId) -> Self {
- (mod) pub use r#struct::*;
- (struct) pub struct EuvAppShell {
- (struct) pub struct EuvDivider {
- (struct) pub struct EuvPage {
- (struct) pub struct EuvActionRow {
- (struct) pub struct EuvStatGrid {

### component::media
- (impl) pub fn new(asset: ImageAsset, tokens: ThemeTokens) -> Self {
- (impl) pub fn height(mut self, px: f32) -> Self {
- (impl) pub fn with_fit(mut self, fit: MediaFit) -> Self {
- (impl) pub fn new(document: SvgDocument, label: String, tokens: ThemeTokens) -> Self {
- (impl) pub fn new(state: Signal<GifAnimation>, tokens: ThemeTokens) -> Self {
- (impl) pub fn new(state: Signal<LivePhotoAsset>, tokens: ThemeTokens) -> Self {
- (impl) pub fn new(state: Signal<VideoTrack>, tokens: ThemeTokens) -> Self {
- (impl) pub fn new(state: Signal<AudioTrack>, tokens: ThemeTokens) -> Self {
- (impl) pub fn new(state: Signal<PdfDocument>, tokens: ThemeTokens) -> Self {
- (impl) pub fn new(document: HtmlDocument, tokens: ThemeTokens) -> Self {
- (impl) pub fn on_link<F>(mut self, callback: F) -> Self where F: FnMut(String) + 'static, {
- (mod) pub use {r#struct::*, r#type::*};
- (struct) pub struct EuvImage {
- (struct) pub struct EuvSvgView {
- (struct) pub struct EuvGifPlayer {
- (struct) pub struct EuvLivePhoto {
- (struct) pub struct EuvVideoPlayer {
- (struct) pub struct EuvAudioPlayer {
- (struct) pub struct EuvPdfViewer {
- (struct) pub struct EuvHtmlView {
- (type) pub type HtmlLinkCallback = Rc<RefCell<dyn FnMut(String)>>;

### component
- (mod) pub use {

### component::nav_extra
- (impl) pub fn active(mut self, active: Signal<usize>) -> Self {
- (mod) pub use r#struct::*;
- (struct) pub struct EuvBreadcrumb {
- (struct) pub struct EuvPagination {
- (struct) pub struct EuvSteps {
- (struct) pub struct EuvAccordionItem {
- (struct) pub struct EuvAccordion {
- (struct) pub struct EuvToc {

### component::navigation
- (impl) pub fn section(mut self, group: &str) -> Self {
- (mod) pub use r#struct::*;
- (struct) pub struct EuvNavItem {
- (struct) pub struct EuvSidebarNav {
- (struct) pub struct EuvTabs {

### component::overlay
- (mod) pub use {r#struct::*, r#type::*};
- (struct) pub struct EuvModal {
- (struct) pub struct EuvToast {
- (type) pub type EuvDialog = EuvModal;

### component::overlay_extra
- (impl) pub fn always_visible(mut self, always_visible: bool) -> Self {
- (impl) pub fn open(mut self, open: Signal<bool>) -> Self {
- (impl) pub fn selected(mut self, last_selected: Signal<Option<usize>>) -> Self {
- (impl) pub fn tone(mut self, tone: EuvTone) -> Self {
- (mod) pub use r#struct::*;
- (struct) pub struct EuvDrawer {
- (struct) pub struct EuvSheet {
- (struct) pub struct EuvPopover {
- (struct) pub struct EuvTooltip {
- (struct) pub struct EuvDropdown {
- (struct) pub struct EuvNotification {
- (struct) pub struct EuvLoading {

### component::shadcn_complete
- (enum) pub enum EuvChartKind {
- (enum) pub enum EuvTextDirection {
- (impl) pub fn placeholder<S>(mut self, placeholder: S) -> Self where S: Into<String>, {
- (impl) pub fn query(mut self, query: Signal<String>) -> Self {
- (impl) pub fn filter(mut self, filter: Signal<String>) -> Self {
- (impl) pub fn sort_ascending(mut self, sort_ascending: Signal<bool>) -> Self {
- (impl) pub fn selected_row(mut self, selected_row: Signal<Option<usize>>) -> Self {
- (impl) pub fn prefix<S>(mut self, prefix: S) -> Self where S: Into<String>, {
- (impl) pub fn placeholder<S>(mut self, placeholder: S) -> Self where S: Into<String>, {
- (impl) pub fn suffix<S>(mut self, suffix: S) -> Self where S: Into<String>, {
- (impl) pub fn leading<S>(mut self, leading: S) -> Self where S: Into<String>, {
- (impl) pub fn description<S>(mut self, description: S) -> Self where S: Into<String>, {
- (impl) pub fn trailing<S>(mut self, trailing: S) -> Self where S: Into<String>, {
- (impl) pub fn on_click<F>(mut self, handler: F) -> Self where F: FnMut(&UiEvent) + 'static, {
- (impl) pub fn timestamp<S>(mut self, timestamp: S) -> Self where S: Into<String>, {
- (impl) pub fn outgoing(mut self, outgoing: bool) -> Self {
- (impl) pub fn open(mut self, open: Signal<bool>) -> Self {
- (impl) pub fn selected(mut self, selected: Signal<Option<usize>>) -> Self {
- (mod) pub use {r#enum::*, r#struct::*};
- (struct) pub struct EuvChartPoint {
- (struct) pub struct EuvChart {
- (struct) pub struct EuvCombobox {
- (struct) pub struct EuvDataTable {
- (struct) pub struct EuvDatePicker {
- (struct) pub struct EuvInputGroup {
- (struct) pub struct EuvItem {
- (struct) pub struct EuvNativeSelect {
- (struct) pub struct EuvNavigationMenu {
- (struct) pub struct EuvResizable {
- (struct) pub struct EuvSeparator {
- (struct) pub struct EuvSonner {
- (struct) pub struct EuvDirection {
- (struct) pub struct EuvTraceSpan {
- (struct) pub struct EuvTrace {
- (struct) pub struct EuvAttachment {
- (struct) pub struct EuvBubble {
- (struct) pub struct EuvMarker {
- (struct) pub struct EuvQuestionnaire {
- (struct) pub struct EuvContextMenu {

### component::shadcn_extra
- (impl) pub fn description<S>(mut self, description: S) -> Self where S: Into<String>, {
- (impl) pub fn labels<S1, S2>(mut self, cancel_label: S1, confirm_label: S2) -> Self where S1: Into<String>, S2: Into<String>, {
- (impl) pub fn query(mut self, query: Signal<String>) -> Self {
- (impl) pub fn placeholder<S>(mut self, placeholder: S) -> Self where S: Into<String>, {
- (impl) pub fn open(mut self, open: Signal<bool>) -> Self {
- (impl) pub fn description<S>(mut self, description: S) -> Self where S: Into<String>, {
- (mod) pub use r#struct::*;
- (struct) pub struct EuvAlertDialog {
- (struct) pub struct EuvCollapsible {
- (struct) pub struct EuvToggleGroup {
- (struct) pub struct EuvInputOtp {
- (struct) pub struct EuvCommand {
- (struct) pub struct EuvHoverCard {
- (struct) pub struct EuvCalendar {
- (struct) pub struct EuvAspectRatio {
- (struct) pub struct EuvMenubar {
- (struct) pub struct EuvCarousel {

### component::surface
- (impl) pub fn child(mut self, node: NodeId) -> Self {
- (impl) pub fn child(mut self, node: NodeId) -> Self {
- (impl) pub fn row(gap: f32) -> Self {
- (impl) pub fn column(gap: f32) -> Self {
- (impl) pub fn child(mut self, node: NodeId) -> Self {
- (impl) pub fn child(mut self, node: NodeId) -> Self {
- (impl) pub fn child(mut self, node: NodeId) -> Self {
- (impl) pub fn action(mut self, node: NodeId) -> Self {
- (mod) pub use r#struct::*;
- (struct) pub struct EuvPageContainer {
- (struct) pub struct EuvPanel {
- (struct) pub struct EuvSpace {
- (struct) pub struct EuvGrid {
- (struct) pub struct EuvScrollArea {
- (struct) pub struct EuvSplitter {
- (struct) pub struct EuvNavbar {
- (struct) pub struct EuvFooter {
- (struct) pub struct EuvButtonGroup {
- (struct) pub struct EuvToggle {

### hook::context
- (impl) pub fn new(initial_scheme: DesignScheme, initial_mode: ThemeMode) -> Self {
- (impl) pub fn toggle_mode(&self) {
- (impl) pub fn select_scheme(&self, scheme: DesignScheme) {
- (impl) pub fn current_tokens(&self) -> ThemeTokens {
- (mod) pub use r#struct::*;
- (struct) pub struct UiThemeState {

### hook::gesture
- (const) pub const TAP_MAX_DISPLACEMENT_PX: f32 = 12.0;
- (const) pub const TAP_MAX_PATH_LENGTH_PX: f32 = 18.0;
- (const) pub const SWIPE_MIN_DISTANCE_PX: f32 = 36.0;
- (enum) pub enum GestureKind {
- (impl) pub fn begin(&mut self, point: Point) {
- (impl) pub fn update(&mut self, point: Point) {
- (impl) pub fn end(&mut self, point: Point) -> Option<GestureKind> {
- (mod) pub use {r#const::*, r#enum::*, r#struct::*};
- (struct) pub struct GestureRecognizer {

### hook::i18n
- (impl) pub fn new(default_locale: String) -> Self {
- (impl) pub fn insert(&mut self, locale: String, key: String, value: String) {
- (impl) pub fn t(&self, key: &str) -> String {
- (mod) pub use r#struct::*;
- (struct) pub struct I18nCatalog {

### hook
- (mod) pub use {context::*, gesture::*, i18n::*, runtime::*};

### hook::runtime
- (fn) pub fn use_theme(scheme: DesignScheme, mode: ThemeMode) -> UiThemeState {
- (fn) pub fn use_i18n(locale: String) -> I18nCatalog {
- (fn) pub fn use_breakpoint() -> Signal<Breakpoint> {
- (fn) pub fn use_viewport_size() -> Signal<Size> {
- (fn) pub fn use_router(initial_path: String) -> Router {
- (fn) pub fn use_gesture() -> GestureRecognizer {
- (fn) pub fn use_gesture_events() -> Signal<Option<GestureEvent>> {
- (fn) pub fn use_window() -> (Signal<SafeAreaInsets>, Signal<ThemeMode>) {
- (mod) pub use r#fn::*;

### crate root
- (lib) pub use {component::*, hook::*, overlay_stack::*, router::*, theme::*};

### overlay_stack
- (impl) pub fn push<F>(label: &str, z_index: i32, on_dismiss: F) -> u64 where F: FnMut() + 'static, {
- (impl) pub fn remove(id: u64) {
- (impl) pub fn dismiss_top() -> bool {
- (impl) pub fn dismiss_all() -> usize {
- (impl) pub fn active_count() -> usize {
- (impl) pub fn active_labels() -> Vec<String> {
- (impl) pub fn clear() {
- (impl) pub fn bind_signal(open: Signal<bool>, label: &str, z_index: i32) -> Effect {
- (mod) pub use {r#struct::*, r#type::*};
- (struct) pub struct OverlayStackEntry {
- (struct) pub struct EuvOverlayStack;
- (type) pub type OverlayDismissCallback = Rc<RefCell<dyn FnMut()>>;

### router
- (impl) pub fn new(initial_path: &str) -> Self {
- (impl) pub fn route<F>(self, pattern: &str, title: &str, builder: F) -> Self where F: Fn(&EuvRouteMatch) -> NodeId + 'static, {
- (impl) pub fn with_dynamic_hub(self, hub: DynamicUpdateHub) -> Self {
- (impl) pub fn push(&self, path: &str) {
- (impl) pub fn replace(&self, path: &str) {
- (impl) pub fn back(&self) -> bool {
- (impl) pub fn forward(&self) -> bool {
- (impl) pub fn handle_system_back(&self) -> bool {
- (impl) pub fn resolve(&self, raw_path: &str) -> (EuvRouteMatch, Option<EuvRouteBuilder>) {
- (impl) pub fn outlet<F>(&self, fallback: F) -> EuvRouterOutlet where F: Fn(&EuvRouteMatch) -> NodeId + 'static, {
- (mod) pub use {r#struct::*, r#type::*};
- (struct) pub struct EuvRouteMatch {
- (struct) pub struct EuvRouteDef {
- (struct) pub struct EuvRouter {
- (struct) pub struct EuvRouterOutlet {
- (struct) pub struct EuvLink {
- (type) pub type EuvRouteBuilder = Rc<dyn Fn(&EuvRouteMatch) -> NodeId>;

### theme
- (mod) pub use {scheme::*, token::*};

### theme::scheme
- (const) pub const SCHEME_NAME_SHADCN: &str = "shadcn";
- (const) pub const SCHEME_NAME_CUPERTINO: &str = "cupertino";
- (const) pub const SCHEME_NAME_MATERIAL: &str = "material";
- (const) pub const SCHEME_NAME_FLUENT: &str = "fluent";
- (const) pub const SCHEME_NAME_ANTDESIGN: &str = "antdesign";
- (const) pub const SCHEME_NAME_BOOTSTRAP: &str = "bootstrap";
- (const) pub const SCHEME_NAME_DAISYUI: &str = "daisyui";
- (const) pub const SCHEME_NAME_GEIST: &str = "geist";
- (const) pub const SCHEME_NAME_HEROUI: &str = "heroui";
- (const) pub const SCHEME_NAME_LINEAR: &str = "linear";
- (const) pub const SCHEME_NAME_MANTINE: &str = "mantine";
- (const) pub const SCHEME_NAME_MONOCHROME: &str = "monochrome";
- (const) pub const SCHEME_NAME_NOTION: &str = "notion";
- (const) pub const SCHEME_NAME_PARK: &str = "park";
- (const) pub const SCHEME_NAME_RADIX: &str = "radix";
- (const) pub const SCHEME_NAME_STRIPE: &str = "stripe";
- (const) pub const SCHEME_NAME_SUPABASE: &str = "supabase";
- (enum) pub enum DesignScheme {
- (fn) pub const fn active_feature_scheme() -> DesignScheme {
- (impl) pub const fn all() -> [Self; 17] {
- (impl) pub const fn as_str(&self) -> &'static str {
- (mod) pub use {r#const::*, r#enum::*, r#fn::*};

### theme::token
- (const) pub const SPACE_XS: f32 = 4.0;
- (const) pub const SPACE_SM: f32 = 8.0;
- (const) pub const SPACE_MD: f32 = 12.0;
- (const) pub const SPACE_LG: f32 = 16.0;
- (const) pub const SPACE_XL: f32 = 20.0;
- (const) pub const SPACE_2XL: f32 = 24.0;
- (const) pub const NAV_SIDEBAR_WIDTH: f32 = 240.0;
- (const) pub const CONTENT_MAX_WIDTH: f32 = 960.0;
- (const) pub const MOBILE_HEADER_HEIGHT: f32 = 52.0;
- (const) pub const Z_INDEX_CONTENT: i32 = 1;
- (const) pub const Z_INDEX_CHROME: i32 = 100;
- (const) pub const Z_INDEX_TOOLTIP: i32 = 140;
- (const) pub const Z_INDEX_FLOATING: i32 = 150;
- (const) pub const Z_INDEX_OVERLAY: i32 = 200;
- (const) pub const Z_INDEX_DRAWER: i32 = 201;
- (const) pub const Z_INDEX_MODAL: i32 = 1000;
- (const) pub const Z_INDEX_TOAST: i32 = 1100;
- (impl) pub fn resolve(scheme: DesignScheme, mode: ThemeMode) -> Self {
- (impl) pub fn card_style(&self) -> Style {
- (mod) pub use {r#const::*, r#struct::*};
- (struct) pub struct ThemePalette {
- (struct) pub struct ThemeGeometry {
- (struct) pub struct ThemeTokens {

