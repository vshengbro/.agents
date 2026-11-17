# euv-docs full pub API

Source: `docs/src/` — auto-extracted from `pub` declarations.

### `lib`

- `fn` **`main`** — `pub fn main() {...}`

### `data::struct`

- `struct` **`DocsFeature`** — `pub(crate) struct DocsFeature {`
- `struct` **`DocsStat`** — `pub(crate) struct DocsStat {`
- `struct` **`DocsPage`** — `pub(crate) struct DocsPage {`
- `struct` **`DocsLocale`** — `pub(crate) struct DocsLocale {`
- `struct` **`DocsSite`** — `pub(crate) struct DocsSite {`
- `struct` **`DocsLanguageLink`** — `pub(crate) struct DocsLanguageLink {`
- `struct` **`DocsRedirect`** — `pub(crate) struct DocsRedirect {`

### `locale::fn`

- `fn` **`locale_tag_for`** — `pub fn locale_tag_for(route: &str) -> &'static str {...}`
- `fn` **`locale_text`** — `pub fn locale_text(route: &str, key: &str) -> String {...}`
- `fn` **`lookup_table`** — `pub fn lookup_table(tag: &str, key: &str) -> Option<String> {...}`
- `fn` **`table_for`** — `pub fn table_for(tag: &str) -> &'static [(&'static str, &'static str)] {...}`
- `fn` **`supported_locale_tags`** — `pub fn supported_locale_tags() -> &'static [&'static str] {...}`
- `fn` **`gate_translation_keys`** — `pub fn gate_translation_keys() -> &'static [&'static str] {...}`
- `fn` **`gate_key_hint`** — `pub fn gate_key_hint() -> &'static str {...}`
- `fn` **`gate_fallback_tag`** — `pub fn gate_fallback_tag() -> &'static str {...}`
- `fn` **`locale_tag_bindings`** — `pub fn locale_tag_bindings() -> &'static [(&'static str, &'static str)] {...}`

### `route::fn`

- `fn` **`normalize_route`** — `pub fn normalize_route(route: &str) -> String {...}`
- `fn` **`route_stem`** — `pub fn route_stem(route: &str) -> String {...}`
- `fn` **`route_candidates`** — `pub fn route_candidates(path: &str) -> Vec<String> {...}`
- `fn` **`route_variants`** — `pub fn route_variants(route: &str) -> Vec<String> {...}`
- `fn` **`route_without_locale_prefix`** — `pub fn route_without_locale_prefix(route: &str, locale_prefix: &str) -> String {...}`
- `fn` **`route_root`** — `pub fn route_root() -> &'static str {...}`
- `fn` **`route_variant_capacity`** — `pub fn route_variant_capacity() -> usize {...}`

### `route::impl`

- `fn` **`get_route`** — `pub fn get_route(&self) -> &'static str {...}`
- `fn` **`get_prefix`** — `pub fn get_prefix(&self) -> &'static str {...}`
- `fn` **`get_locale`** — `pub fn get_locale(&self, route: &str) -> &'static RouteLocale {...}`
- `fn` **`get_locales`** — `pub fn get_locales(&self) -> &'static [RouteLocale] {...}`
- `fn` **`get_pages`** — `pub fn get_pages(&self) -> &'static [RoutePage] {...}`
- `fn` **`new`** — `pub fn new(locales: &'static [RouteLocale], pages: &'static [RoutePage]) -> RouteSite {...}`
- `fn` **`locale_of`** — `pub fn locale_of(&self, route: &str) -> Option<&'static RouteLocale> {...}`
- `fn` **`find_page`** — `pub fn find_page(&self, request: &str) -> Option<&'static RoutePage> {...}`
- `fn` **`audit_route_variants`** — `pub fn audit_route_variants(&self, route: &str) -> Vec<(String, bool)> {...}`
- `fn` **`find_page_without_locale_prefix`** — `pub fn find_page_without_locale_prefix( &self, route: &str, locale_prefix: &str, ) -> Option<&'static RoutePage> {...}`
- `fn` **`audit_all_route_variants`** — `pub fn audit_all_route_variants(&self) -> Vec<String> {...}`

### `route::static`

- `static` **`ROUTE_LOCALE_ROOT`** — `pub(crate) static ROUTE_LOCALE_ROOT: RouteLocale = RouteLocale { prefix: ROUTE_ROOT };`

### `route::struct`

- `struct` **`RouteSite`** — `pub struct RouteSite {`
- `struct` **`RouteLocale`** — `pub struct RouteLocale {`
- `struct` **`RoutePage`** — `pub struct RoutePage {`

### `router::fn`

- `fn` **`decode_anchor`** — `pub(crate) fn decode_anchor(encoded: &str) -> String {...}`
- `fn` **`parse_route`** — `pub fn parse_route(raw: &str) -> (String, Option<String>) {...}`
- `fn` **`same_route_anchor`** — `pub fn same_route_anchor(left: &str, right: &str) -> bool {...}`
- `fn` **`route_page_matches`** — `pub(crate) fn route_page_matches(path: &str, hash: &str) -> bool {...}`
- `fn` **`locale_of`** — `pub(crate) fn locale_of(route: &str) -> &'static DocsLocale {...}`
- `fn` **`find_page`** — `pub(crate) fn find_page(route: &str) -> Option<&'static DocsPage> {...}`
- `fn` **`flatten_links`** — `pub fn flatten_links(items: &'static [EuvSidebarItem]) -> Vec<&'static EuvSidebarItem> {...}`
- `fn` **`sidebar_group_key`** — `pub fn sidebar_group_key(prefix: &str, text: &str) -> String {...}`
- `fn` **`all_group_keys`** — `pub fn all_group_keys(items: &'static [EuvSidebarItem]) -> Vec<String> {...}`
- `fn` **`site_root`** — `pub(crate) fn site_root() -> String {...}`
- `fn` **`redirect_foreign_route`** — `pub(crate) fn redirect_foreign_route() -> bool {...}`
- `fn` **`build_route_site`** — `pub(crate) fn build_route_site() -> RouteSite {...}`
- `fn` **`leak_locales`** — `pub(crate) fn leak_locales(locales: &'static [DocsLocale]) -> &'static [RouteLocale] {...}`
- `fn` **`leak_pages`** — `pub(crate) fn leak_pages(pages: &'static [DocsPage]) -> &'static [RoutePage] {...}`
- `fn` **`route_site`** — `pub fn route_site() -> RouteSite {...}`
- `fn` **`locale_prefix_for`** — `pub fn locale_prefix_for(route: &str) -> &'static str {...}`
- `fn` **`locale_label_for`** — `pub fn locale_label_for(route: &str) -> &'static str {...}`

### `router::impl`

- `static` **`ROUTE_SITE`** — `pub static ROUTE_SITE: RouteSite = build_route_site();`

### `bin::docs::fn`

- `fn` **`parse_args`** — `pub(crate) fn parse_args() -> Result<Args, String> {...}`
- `fn` **`run`** — `pub(crate) fn run(args: &Args) -> Result<(), String> {...}`
- `fn` **`print_usage`** — `pub(crate) fn print_usage() {...}`

### `bin::docs::struct`

- `struct` **`Args`** — `pub(crate) struct Args {`
- `struct` **`LocaleManifestEntry`** — `pub(crate) struct LocaleManifestEntry {`

### `component::code_block::view::fn`

- `fn` **`docs_code_block`** — `pub(crate) fn docs_code_block(node: VirtualNode<DocsCodeBlockProps>) -> VirtualNode {...}`

### `component::code_block::view::struct`

- `struct` **`DocsCodeBlockProps`** — `pub(crate) struct DocsCodeBlockProps {`

### `component::doc_page::view::fn`

- `fn` **`docs_main`** — `pub(crate) fn docs_main(node: VirtualNode<DocsPageProps>) -> VirtualNode {...}`
- `fn` **`docs_doc_page`** — `pub(crate) fn docs_doc_page(node: VirtualNode<DocsPageProps>) -> VirtualNode {...}`

### `component::doc_page::view::struct`

- `struct` **`DocsPageProps`** — `pub(crate) struct DocsPageProps {`

### `component::header::view::fn`

- `fn` **`docs_header`** — `pub(crate) fn docs_header( locale: &'static DocsLocale, route_signal: Signal<String>, theme_signal: Signal<String>, search_query: Signal<String>, ) -> VirtualNode {...}`

### `component::home_page::view::fn`

- `fn` **`docs_home_page`** — `pub(crate) fn docs_home_page(node: VirtualNode<DocsPageProps>) -> VirtualNode {...}`
- `fn` **`docs_stats_row`** — `pub(crate) fn docs_stats_row(node: VirtualNode<DocsStatsRowProps>) -> VirtualNode {...}`
- `fn` **`docs_feature_card`** — `pub(crate) fn docs_feature_card(node: VirtualNode<DocsFeatureProps>) -> VirtualNode {...}`
- `fn` **`docs_feature_grid`** — `pub(crate) fn docs_feature_grid(node: VirtualNode<DocsFeatureGridProps>) -> VirtualNode {...}`

### `component::home_page::view::struct`

- `struct` **`DocsFeatureProps`** — `pub(crate) struct DocsFeatureProps {`
- `struct` **`DocsFeatureGridProps`** — `pub(crate) struct DocsFeatureGridProps {`
- `struct` **`DocsStatsRowProps`** — `pub(crate) struct DocsStatsRowProps {`

### `component::layout::view::fn`

- `fn` **`app`** — `pub(crate) fn app() -> VirtualNode {...}`
- `fn` **`docs_desktop_shell`** — `pub(crate) fn docs_desktop_shell(node: VirtualNode<DocsShellProps>) -> VirtualNode {...}`
- `fn` **`docs_mobile_shell`** — `pub(crate) fn docs_mobile_shell(node: VirtualNode<DocsShellProps>) -> VirtualNode {...}`
- `fn` **`theme_icon_node`** — `pub(crate) fn theme_icon_node(theme_signal: Signal<String>) -> VirtualNode {...}`

### `component::layout::view::struct`

- `struct` **`DocsShellProps`** — `pub(crate) struct DocsShellProps {`

### `component::markdown::view::fn`

- `fn` **`docs_markdown`** — `pub(crate) fn docs_markdown(blocks: &'static [EuvMdBlock]) -> VirtualNode {...}`

### `component::not_found::view::fn`

- `fn` **`docs_not_found`** — `pub(crate) fn docs_not_found(node: VirtualNode<DocsPageProps>) -> VirtualNode {...}`

### `component::password_gate::view::fn`

- `fn` **`docs_password_gate`** — `pub(crate) fn docs_password_gate(node: VirtualNode<DocsPasswordGateProps>) -> VirtualNode {...}`
- `fn` **`is_unlocked`** — `pub(crate) fn is_unlocked(route: &str) -> bool {...}`

### `component::password_gate::view::struct`

- `struct` **`DocsPasswordGateProps`** — `pub(crate) struct DocsPasswordGateProps {`

### `component::site_footer::view::fn`

- `fn` **`docs_footer_props`** — `pub(crate) fn docs_footer_props( locale: &DocsLocale, page: Option<&DocsPage>, site: &DocsSite, ) -> EuvFooterProps {...}`
- `fn` **`docs_site_footer`** — `pub(crate) fn docs_site_footer(node: VirtualNode<DocsSiteFooterProps>) -> VirtualNode {...}`

### `component::site_footer::view::struct`

- `struct` **`DocsSiteFooterProps`** — `pub(crate) struct DocsSiteFooterProps {`

### `description::fn`

- `fn` **`description_for_slug`** — `pub(crate) fn description_for_slug(slug: &str) -> Option<&'static str> {...}`
- `fn` **`route_slug`** — `pub(crate) fn route_slug(route: &str) -> &str {...}`
- `fn` **`description_for_route`** — `pub(crate) fn description_for_route(route: &str) -> Option<&'static str> {...}`

### `highlight::enum`

- `enum` **`CodeTokenKind`** — `pub(crate) enum CodeTokenKind {`
- `enum` **`CodeLanguage`** — `pub(crate) enum CodeLanguage {`

### `highlight::fn`

- `fn` **`tokenize`** — `pub(crate) fn tokenize(lang: &str, code: &str) -> Vec<CodeToken> {...}`
- `fn` **`highlighted_html`** — `pub(crate) fn highlighted_html(lang: &str, code: &str) -> String {...}`
- `fn` **`token_class`** — `pub(crate) fn token_class(kind: CodeTokenKind) -> Option<&'static str> {...}`

### `highlight::struct`

- `struct` **`CodeToken`** — `pub(crate) struct CodeToken {`

### `component::header::preview::fn`

- `fn` **`header_search_preview`** — `pub(crate) fn header_search_preview( route_signal: Signal<String>, query: Signal<String>, state: Signal<HeaderSearchState>, input_id: String, target: NodeRef<Element>, ) -> VirtualNode {...}`

### `component::header::search::fn`

- `fn` **`header_search_matches`** — `pub(crate) fn header_search_matches(pages: &[DocsPage], query: &str) -> Vec<DocsPage> {...}`
- `fn` **`header_search_focus`** — `pub(crate) fn header_search_focus(state: Signal<HeaderSearchState>) {...}`
- `fn` **`header_search_select`** — `pub(crate) fn header_search_select( route_signal: Signal<String>, query: Signal<String>, state: Signal<HeaderSearchState>, route: &'static str, ) {...}`

### `component::header::search::impl`

- `fn` **`focus`** — `pub(crate) fn focus(&mut self) {...}`
- `fn` **`dismiss`** — `pub(crate) fn dismiss(&mut self) {...}`
- `fn` **`key`** — `pub(crate) fn key( &mut self, key: &str, composing: bool, results: &[DocsPage], ) -> (bool, Option<&'static str>) {...}`

### `component::header::search::struct`

- `struct` **`HeaderSearchState`** — `pub(crate) struct HeaderSearchState {`
