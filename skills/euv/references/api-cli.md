# euv-cli full pub API

Source: `cli/src/` at `origin/master` (`aac1c450d6e8317c50c01dd6225dea7a29265495`, version 0.39.1), extracted from
`pub` declarations.
Re-verified against `origin/master` (`6ccb8599`, euv 0.43.0) on 2026-11-27: every declared API name below still resolves in that tree.

Subcommands: `run`, `dev`, `docs`, `build`, `check`, `fmt`, `doctor`, `new`.
The old `bundle` / `--all` / `--platforms` surface is gone: targets are now
selected with `--target <web|android|ios|ipad|macos|windows|linux|native|all>`
and every plan can be printed with `--plan` instead of executed.

### args
- (enum) pub enum TargetArg {
- (enum) pub enum RenderArg {
- (enum) pub enum DevTargetArg {
- (enum) pub enum DocsAction {
- (enum) pub enum Commands {
- (impl) pub const fn to_render_mode(self) -> RenderMode {
- (impl) pub const fn as_flag(self) -> &'static str {
- (mod) pub use {r#enum::*, r#struct::*};
- (struct) pub struct Cli {
- (struct) pub struct DocsBuildArgs {
- (struct) pub struct ServerBindArgs {

### command
- (fn) pub fn execute_cli(cli: &Cli) -> io::Result<String> {
- (fn) pub fn collect_doctor_report() -> DoctorReport {
- (fn) pub fn resolve_check_steps(target: TargetArg, package: Option<&str>) -> Vec<BuildStep> {
- (fn) pub fn resolve_run_step( target: TargetArg, render: RenderArg, release: bool, package: Option<&str>, ) -> BuildStep {
- (fn) pub fn scaffold_project(parent_dir: &Path, name: &str) -> io::Result<ScaffoldReport> {
- (fn) pub fn package_zero_js_web_bundle(out_dir: &Path, title: &str) -> io::Result<PathBuf> {
- (fn) pub fn format_doctor_report(report: &DoctorReport) -> String {
- (mod) pub use {r#fn::*, r#struct::*};
- (struct) pub struct TargetReadiness {
- (struct) pub struct DoctorReport {
- (struct) pub struct ScaffoldReport {

### hot
- (const) pub const HMR_ENDPOINT: &str = "/__euv_hmr";
- (const) pub const OTA_MANIFEST_ENDPOINT: &str = "/__euv_ota/manifest.json";
- (const) pub const OTA_MODULE_ENDPOINT: &str = "/__euv_ota/module.wasm";
- (const) pub const DEV_STATUS_ENDPOINT: &str = "/__euv_status";
- (const) pub const OTA_DEV_SIGNING_KEY: &str = "euv-dev-ota-key-2026";
- (const) pub const OTA_SLOT_DEV: &str = "euv-dev-hot-slot";
- (const) pub const DEFAULT_DEV_HOST: &str = "127.0.0.1";
- (const) pub const DEFAULT_DOCS_OUT_DIR: &str = "dist/docs";
- (enum) pub enum HmrEventKind {
- (fn) pub fn build_docs_site( src_dir: &Path, out_dir: &Path, options: &DocsBuildOptions, ) -> io::Result<GeneratedSiteReport> {
- (fn) pub fn build_dev_ota_state( version: u64, title: &str, changed_files: Vec<String>, ) -> OtaBundleState {
- (fn) pub fn inject_dev_hmr_into_html(html: &str, hmr_endpoint: &str) -> String {
- (fn) pub fn start_dev_server(config: DevServerConfig) -> io::Result<DevServerHandle> {
- (fn) pub fn run_dev_blocking(config: DevServerConfig) -> io::Result<DevServerReport> {
- (fn) pub fn mime_type_for_path(path: &Path) -> &'static str {
- (impl) pub fn is_empty(&self) -> bool {
- (impl) pub fn all_paths(&self) -> Vec<String> {
- (impl) pub fn scan(root: &Path, allowed_exts: &[&str]) -> io::Result<Self> {
- (impl) pub fn scan_excluding( root: &Path, allowed_exts: &[&str], exclude_dir: Option<&Path>, ) -> io::Result<Self> {
- (impl) pub fn diff(&self, next: &Self) -> FileChangeSet {
- (impl) pub fn new(initial_ota: OtaBundleState) -> Self {
- (impl) pub fn revision(&self) -> u64 {
- (impl) pub fn publish(&self, kind: HmrEventKind, message: String, changed_files: Vec<String>) -> u64 {
- (impl) pub fn set_ota_state(&self, next_state: OtaBundleState) {
- (impl) pub fn current_event(&self) -> Option<HmrEvent> {
- (impl) pub fn ota_snapshot(&self) -> Option<OtaBundleState> {
- (impl) pub fn stop(&self) {
- (impl) pub fn is_running(&self) -> bool {
- (impl) pub fn address(&self) -> SocketAddr {
- (impl) pub fn url(&self) -> String {
- (impl) pub fn revision(&self) -> u64 {
- (impl) pub fn report(&self) -> DevServerReport {
- (impl) pub fn shutdown(&mut self) {
- (mod) pub use {r#const::*, r#enum::*, r#fn::*, r#struct::*};
- (struct) pub struct FileStamp {
- (struct) pub struct WatchSnapshot {
- (struct) pub struct FileChangeSet {
- (struct) pub struct OtaManifest {
- (struct) pub struct OtaBundleState {
- (struct) pub struct HmrEvent {
- (struct) pub struct DevServerConfig {
- (struct) pub struct DevServerReport {
- (struct) pub struct HmrHub {
- (struct) pub struct DevServerHandle {

### crate root
- (lib) pub use {args::*, command::*, hot::*, platform::*};

### platform
- (const) pub const TRIPLE_WEB: &str = "wasm32-unknown-unknown";
- (const) pub const TRIPLE_ANDROID: &str = "aarch64-linux-android";
- (const) pub const TRIPLE_IOS: &str = "aarch64-apple-ios";
- (const) pub const TRIPLE_MACOS: &str = "aarch64-apple-darwin";
- (const) pub const TRIPLE_MACOS_X64: &str = "x86_64-apple-darwin";
- (const) pub const TRIPLE_WINDOWS: &str = "x86_64-pc-windows-msvc";
- (const) pub const TRIPLE_WINDOWS_ARM64: &str = "aarch64-pc-windows-msvc";
- (const) pub const TRIPLE_LINUX: &str = "x86_64-unknown-linux-gnu";
- (const) pub const TRIPLE_LINUX_ARM64: &str = "aarch64-unknown-linux-gnu";
- (fn) pub const fn host_native_target() -> TargetArg {
- (fn) pub const fn target_triple_for_host(target: TargetArg) -> &'static str {
- (fn) pub fn resolve_target_specs(target: TargetArg) -> Vec<TargetSpec> {
- (fn) pub fn spec_for_platform(target: TargetArg) -> TargetSpec {
- (fn) pub fn resolve_build_plans(target: TargetArg, render: RenderArg, release: bool) -> Vec<BuildPlan> {
- (mod) pub use {r#const::*, r#fn::*, r#struct::*};
- (struct) pub struct TargetSpec {
- (struct) pub struct BuildStep {
- (struct) pub struct BuildPlan {

