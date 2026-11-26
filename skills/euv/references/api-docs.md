# euv-docs full pub API

Source: `docs/src/` at `origin/master` (`aac1c450d6e8317c50c01dd6225dea7a29265495`, version 0.39.1), extracted from
`pub` declarations.

The docs crate is a **native euv application** plus a static-site generator:
`parser` reads Markdown into a `DocSite`, `generator` renders HTML, `viewer`
mounts the same pages as a native/wasm window. There is no `build.rs`, no
locale table and no mermaid engine any more — the old multi-locale
`docs/build.rs` pipeline was removed with the rewrite.

### generator
- (fn) pub fn build_docs_bundle( src_dir: &Path, out_dir: &Path, options: &DocsBuildOptions, ) -> io::Result<GeneratedSiteReport> {
- (fn) pub fn generate_static_docs(site: &DocSite, out_dir: &Path) -> io::Result<GeneratedSiteReport> {
- (fn) pub fn generate_static_docs_with_options( site: &DocSite, out_dir: &Path, options: &DocsBuildOptions, ) -> io::Result<GeneratedSiteReport> {
- (fn) pub fn render_page_html(site: &DocSite, page: &DocPage, generated_at: &str) -> String {
- (mod) pub use {r#fn::*, r#struct::*};
- (struct) pub struct GeneratedSiteReport {
- (struct) pub struct DocsBuildOptions {

### crate root
- (lib) pub use {generator::*, model::*, parser::*, viewer::*};

### model
- (const) pub const DEFAULT_DOC_TITLE: &str = "Untitled Document";
- (const) pub const DOCS_SITE_TITLE: &str = "Euv Documentation";
- (const) pub const DOCS_SITE_TAGLINE: &str = "Cross-platform native Rust UI framework across Web, Android, iOS, iPadOS, macOS, Windows, and Linux.";
- (enum) pub enum DocBlock {
- (impl) pub fn search(&self, query: &str) -> Vec<&DocPage> {
- (impl) pub fn find_by_route(&self, route: &str) -> Option<&DocPage> {
- (impl) pub fn search_entries(&self) -> Vec<SearchIndexEntry> {
- (impl) pub fn matches_query(&self, needle: &str) -> bool {
- (mod) pub use {r#const::*, r#enum::*, r#struct::*};
- (struct) pub struct DocSiteFrontmatter {
- (struct) pub struct DocFrontmatter {
- (struct) pub struct SearchIndexEntry {
- (struct) pub struct DocTocItem {
- (struct) pub struct DocPage {
- (struct) pub struct DocSite {

### parser
- (fn) pub fn parse_markdown_page(route: &str, default_section: &str, raw: &str) -> DocPage {
- (fn) pub fn load_doc_site(root_dir: &Path) -> io::Result<DocSite> {
- (fn) pub fn load_doc_site_with_options( root_dir: &Path, title_override: Option<&str>, ) -> io::Result<DocSite> {
- (mod) pub use r#fn::*;

### viewer
- (const) pub const DOCS_WINDOW_TITLE: &str = "euv Documentation Viewer";
- (const) pub const DOCS_WINDOW_WIDTH: u32 = 1200;
- (const) pub const DOCS_WINDOW_HEIGHT: u32 = 800;
- (const) pub const DOCS_FLAG_HEADLESS: &str = "--headless";
- (const) pub const DOCS_FLAG_GENERATE: &str = "--generate";
- (const) pub const DOCS_FLAG_INTERACTIVE: &str = "--interactive";
- (fn) pub fn mount_docs_viewer( site: &DocSite, active_route: Signal<String>, search_query: Signal<String>, tokens: ThemeTokens, ) -> NodeId {
- (fn) pub fn mount_doc_page(page: &DocPage, tokens: ThemeTokens) -> NodeId {
- (fn) pub fn render_docs_smoke(site: &DocSite, headless: bool) -> Result<FrameStats, PlatformError> {
- (fn) pub fn render_docs_app( site: &DocSite, headless: bool, interactive: bool, ) -> Result<FrameStats, PlatformError> {
- (mod) pub use {r#const::*, r#fn::*};

