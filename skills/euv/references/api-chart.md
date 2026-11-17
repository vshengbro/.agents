# euv-chart full pub API

Source: `chart/src/` — auto-extracted from `pub` declarations.

Re-exported at the crate root via `chart/src/lib.rs` `pub use {animation::*, backend::*, chart::*, display::*, event::*, geo::*, geom::*, model::*, option::*, paint::*, series::*, text::*}`, plus `pub use euv_engine::Easing`.

### `animation::fn`

- `fn` **`collect_values`** — `pub(crate) fn collect_values(option: &ChartOption) -> Vec<Vec<f64>> {...}`
- `fn` **`animated_value`** — `pub(crate) fn animated_value(value: &DataValue) -> Option<f64> {...}`
- `fn` **`write_value`** — `pub(crate) fn write_value(data: &mut DataValue, value: f64) {...}`
- `fn` **`align_values`** — `pub(crate) fn align_values(current: &[Vec<f64>], target: &[Vec<f64>]) -> Vec<Vec<f64>> {...}`
- `fn` **`interpolate`** — `pub(crate) fn interpolate(from: &[Vec<f64>], to: &[Vec<f64>], progress: f64) -> Vec<Vec<f64>> {...}`

### `animation::impl`

- `fn` **`new`** — `pub fn new() -> Self {...}`
- `fn` **`duration`** — `pub fn duration(&self) -> f64 {...}`
- `fn` **`set_duration`** — `pub fn set_duration(&mut self, duration: f64) -> &mut Self {...}`
- `fn` **`delay`** — `pub fn delay(&self) -> f64 {...}`
- `fn` **`set_delay`** — `pub fn set_delay(&mut self, delay: f64) -> &mut Self {...}`
- `fn` **`easing`** — `pub fn easing(&self) -> Easing {...}`
- `fn` **`set_easing`** — `pub fn set_easing(&mut self, easing: Easing) -> &mut Self {...}`
- `fn` **`is_running`** — `pub fn is_running(&self) -> bool {...}`
- `fn` **`pause`** — `pub fn pause(&mut self) -> &mut Self {...}`
- `fn` **`resume`** — `pub fn resume(&mut self) -> &mut Self {...}`
- `fn` **`reset`** — `pub fn reset(&mut self) -> &mut Self {...}`
- `fn` **`remember_initial`** — `pub fn remember_initial(&mut self, option: &ChartOption) -> &mut Self {...}`
- `fn` **`begin`** — `pub fn begin(&mut self, option: &ChartOption) -> &mut Self {...}`
- `fn` **`advance`** — `pub fn advance(&mut self, delta: f64) -> bool {...}`
- `fn` **`apply`** — `pub fn apply(&self, option: &mut ChartOption) {...}`

### `animation::struct`

- `struct` **`Animator`** — `pub struct Animator {`

### `chart::enum`

- `enum` **`ChartCommand`** — `pub enum ChartCommand {`

### `chart::fn`

- `fn` **`canvas_size`** — `pub(crate) fn canvas_size(canvas: &HtmlCanvasElement) -> (f64, f64) {...}`
- `fn` **`detect_dpr`** — `pub(crate) fn detect_dpr() -> f64 {...}`
- `fn` **`draws_own_line`** — `pub(crate) fn draws_own_line(axis: &AxisLayout, grid: &GridLayout, horizontal: bool) -> bool {...}`

### `chart::impl`

- `fn` **`create`** — `pub async fn create(canvas: HtmlCanvasElement) -> Option<Self> {...}`
- `fn` **`create_with_backend`** — `pub async fn create_with_backend( canvas: HtmlCanvasElement, preferred: BackendKind, ) -> Option<Self> {...}`
- `fn` **`set_option`** — `pub fn set_option(&mut self, option: ChartOption) -> &mut Self {...}`
- `fn` **`advance`** — `pub fn advance(&mut self, delta: f64) -> bool {...}`
- `fn` **`animator`** — `pub fn animator(&mut self) -> &mut Animator {...}`
- `fn` **`option`** — `pub fn option(&self) -> &ChartOption {...}`
- `fn` **`option_mut`** — `pub fn option_mut(&mut self) -> &mut ChartOption {...}`
- `fn` **`render`** — `pub fn render(&mut self) -> &mut Self {...}`
- `fn` **`handle`** — `pub fn handle(&self) -> ChartHandle {...}`
- `fn` **`resize`** — `pub fn resize(&mut self, width: f64, height: f64) -> &mut Self {...}`
- `fn` **`backend_kind`** — `pub fn backend_kind(&self) -> BackendKind {...}`
- `fn` **`layout`** — `pub fn layout(&self) -> &ChartLayout {...}`
- `fn` **`display_list`** — `pub fn display_list(&self) -> &DisplayList {...}`
- `fn` **`canvas`** — `pub fn canvas(&self) -> &HtmlCanvasElement {...}`
- `fn` **`on`** — `pub fn on(&mut self, event_type: ChartEventType, handler: EventHandler) -> &mut Self {...}`
- `fn` **`off`** — `pub fn off(&mut self, event_type: ChartEventType) -> &mut Self {...}`
- `fn` **`emit`** — `pub fn emit(&mut self, event: ChartEvent) -> &mut Self {...}`
- `fn` **`dispatch_action`** — `pub fn dispatch_action(&mut self, action: ChartAction) -> &mut Self {...}`
- `fn` **`show_tip`** — `pub fn show_tip( &mut self, series_index: usize, data_index: usize, x: f64, y: f64, ) -> &mut Self {...}`
- `fn` **`hide_tip`** — `pub fn hide_tip(&mut self) -> &mut Self {...}`
- `fn` **`tooltip`** — `pub fn tooltip(&self) -> Option<&TooltipState> {...}`
- `fn` **`hit_test`** — `pub fn hit_test(&self, x: f64, y: f64) -> Option<ChartEvent> {...}`
- `fn` **`dispose`** — `pub fn dispose(&mut self) {...}`
- `fn` **`register_map`** — `pub fn register_map(&mut self, name: &str, geojson: &DataValue) -> Result<&mut Self, GeoError> {...}`
- `fn` **`register_map_data`** — `pub fn register_map_data(&mut self, data: MapData) -> &mut Self {...}`
- `fn` **`maps`** — `pub fn maps(&self) -> &MapRegistry {...}`
- `fn` **`map_names`** — `pub fn map_names(&self) -> Vec<String> {...}`
- `fn` **`to_data_url`** — `pub fn to_data_url(&self) -> Option<String> {...}`
- `fn` **`push`** — `pub fn push(&self, command: ChartCommand) -> &Self {...}`
- `fn` **`set_option`** — `pub fn set_option(&self, option: ChartOption) -> &Self {...}`
- `fn` **`resize`** — `pub fn resize(&self, width: f64, height: f64) -> &Self {...}`
- `fn` **`dispatch_action`** — `pub fn dispatch_action(&self, action: ChartAction) -> &Self {...}`
- `fn` **`pending`** — `pub fn pending(&self) -> usize {...}`
- `fn` **`new`** — `pub fn new() -> Self {...}`
- `fn` **`build`** — `pub fn build(&mut self, list: &mut DisplayList, option: &ChartOption, layout: &ChartLayout) {...}`
- `fn` **`build_with_tooltip`** — `pub fn build_with_tooltip( &mut self, list: &mut DisplayList, option: &ChartOption, layout: &ChartLayout, tooltip: Option<&TooltipState>, ) {...}`

### `chart::struct`

- `struct` **`Chart`** — `pub struct Chart {`
- `struct` **`ChartHandle`** — `pub struct ChartHandle {`
- `struct` **`TooltipState`** — `pub struct TooltipState {`
- `struct` **`ChartRenderer`** — `pub struct ChartRenderer {`

### `display::enum`

- `enum` **`DrawCmd`** — `pub enum DrawCmd {`
- `enum` **`DrawKind`** — `pub enum DrawKind {`

### `display::impl`

- `fn` **`kind`** — `pub fn kind(&self) -> DrawKind {...}`
- `fn` **`new`** — `pub fn new() -> Self {...}`
- `fn` **`items`** — `pub fn items(&self) -> &[DisplayItem] {...}`
- `fn` **`len`** — `pub fn len(&self) -> usize {...}`
- `fn` **`is_empty`** — `pub fn is_empty(&self) -> bool {...}`
- `fn` **`bounds`** — `pub fn bounds(&self) -> BBox {...}`
- `fn` **`clear`** — `pub fn clear(&mut self) {...}`
- `fn` **`fill`** — `pub fn fill(&mut self, path: Path, paint: Fill, opacity: f64, z: i32) {...}`
- `fn` **`stroke`** — `pub fn stroke(&mut self, path: Path, paint: Stroke, style: LineStyle, opacity: f64, z: i32) {...}`
- `fn` **`text`** — `pub fn text(&mut self, text: String, x: f64, y: f64, style: TextStyle, z: i32) {...}`
- `fn` **`image`** — `pub fn image( &mut self, image: HtmlImageElement, x: f64, y: f64, width: f64, height: f64, z: i32, ) {...}`
- `fn` **`clip`** — `pub fn clip(&mut self, path: Path, z: i32) {...}`
- `fn` **`pop_clip`** — `pub fn pop_clip(&mut self, z: i32) {...}`
- `fn` **`strip`** — `pub fn strip(&mut self, points: Vec<Point>, baseline: f32, paint: Fill, opacity: f64, z: i32) {...}`
- `fn` **`mark`** — `pub fn mark(&mut self, index: usize, element_id: u32, series_index: usize, data_index: usize) {...}`

### `display::struct`

- `struct` **`DisplayItem`** — `pub struct DisplayItem {`
- `struct` **`DisplayList`** — `pub struct DisplayList {`

### `event::enum`

- `enum` **`ChartEventType`** — `pub enum ChartEventType {`
- `enum` **`ChartAction`** — `pub enum ChartAction {`

### `event::struct`

- `struct` **`ChartEvent`** — `pub struct ChartEvent {`
- `struct` **`EventRegistration`** — `pub(crate) struct EventRegistration {`

### `event::type`

- `type` **`EventHandler`** — `pub type EventHandler = Rc<dyn Fn(&ChartEvent)>;`

### `geo::enum`

- `enum` **`GeoError`** — `pub enum GeoError {`

### `geo::fn`

- `fn` **`parse_geojson`** — `pub(crate) fn parse_geojson(name: &str, value: &DataValue) -> Result<MapData, GeoError> {...}`
- `fn` **`parse_feature`** — `pub(crate) fn parse_feature(value: &DataValue) -> Result<MapRegion, GeoError> {...}`
- `fn` **`feature_name`** — `pub(crate) fn feature_name(value: &DataValue) -> String {...}`
- `fn` **`parse_geometry`** — `pub(crate) fn parse_geometry(value: &DataValue) -> Result<Vec<RegionPolygon>, GeoError> {...}`
- `fn` **`parse_polygon`** — `pub(crate) fn parse_polygon(value: &DataValue) -> Result<RegionPolygon, GeoError> {...}`
- `fn` **`parse_ring`** — `pub(crate) fn parse_ring(value: &DataValue) -> Result<Vec<GeoPoint>, GeoError> {...}`
- `fn` **`ring_center`** — `pub(crate) fn ring_center(ring: &[GeoPoint]) -> Option<GeoPoint> {...}`
- `fn` **`fit_aspect`** — `pub(crate) fn fit_aspect(rect: BBox, aspect: f64) -> BBox {...}`
- `fn` **`region_path`** — `pub(crate) fn region_path(region: &MapRegion, transform: &Transform2D) -> Path {...}`
- `fn` **`region_center`** — `pub(crate) fn region_center(region: &MapRegion, transform: &Transform2D) -> Point {...}`

### `geo::impl`

- `fn` **`new`** — `pub fn new(lng: f64, lat: f64) -> Self {...}`
- `fn` **`width`** — `pub fn width(&self) -> f64 {...}`
- `fn` **`height`** — `pub fn height(&self) -> f64 {...}`
- `fn` **`is_empty`** — `pub fn is_empty(&self) -> bool {...}`
- `fn` **`extend`** — `pub fn extend(&mut self, point: GeoPoint) {...}`
- `fn` **`center`** — `pub fn center(&self) -> Option<GeoPoint> {...}`
- `fn` **`from_regions`** — `pub fn from_regions(name: &str, regions: Vec<MapRegion>) -> Self {...}`
- `fn` **`from_geojson`** — `pub fn from_geojson(name: &str, value: &DataValue) -> Result<Self, GeoError> {...}`
- `fn` **`region`** — `pub fn region(&self, name: &str) -> Option<&MapRegion> {...}`
- `fn` **`new`** — `pub fn new() -> Self {...}`
- `fn` **`register`** — `pub fn register(&mut self, data: MapData) -> &mut Self {...}`
- `fn` **`register_geojson`** — `pub fn register_geojson( &mut self, name: &str, value: &DataValue, ) -> Result<&mut Self, GeoError> {...}`
- `fn` **`get`** — `pub fn get(&self, name: &str) -> Option<&MapData> {...}`
- `fn` **`names`** — `pub fn names(&self) -> Vec<String> {...}`
- `fn` **`len`** — `pub fn len(&self) -> usize {...}`
- `fn` **`is_empty`** — `pub fn is_empty(&self) -> bool {...}`
- `fn` **`clear`** — `pub fn clear(&mut self) {...}`
- `fn` **`compute`** — `pub fn compute(data: &MapData, rect: BBox, aspect_scale: f64) -> Self {...}`
- `fn` **`region`** — `pub fn region(&self, name: &str) -> Option<&GeoRegionLayout> {...}`

### `geo::struct`

- `struct` **`GeoPoint`** — `pub struct GeoPoint {`
- `struct` **`GeoBounds`** — `pub struct GeoBounds {`
- `struct` **`RegionPolygon`** — `pub struct RegionPolygon {`
- `struct` **`MapRegion`** — `pub struct MapRegion {`
- `struct` **`MapData`** — `pub struct MapData {`
- `struct` **`MapRegistry`** — `pub struct MapRegistry {`
- `struct` **`GeoRegionLayout`** — `pub struct GeoRegionLayout {`
- `struct` **`GeoLayout`** — `pub struct GeoLayout {`

### `model::enum`

- `enum` **`ScaleKind`** — `pub enum ScaleKind {`
- `enum` **`AxisSide`** — `pub enum AxisSide {`

### `model::fn`

- `fn` **`tick_decimals`** — `pub(crate) fn tick_decimals(value: f64) -> usize {...}`
- `fn` **`format_tick`** — `pub(crate) fn format_tick(value: f64, interval: f64) -> String {...}`
- `fn` **`parse_colors`** — `pub(crate) fn parse_colors(colors: &[String]) -> Vec<Color> {...}`
- `fn` **`parse_pieces`** — `pub(crate) fn parse_pieces(pieces: &[DataValue]) -> Vec<VisualPiece> {...}`
- `fn` **`resolve_edge`** — `pub(crate) fn resolve_edge(position: Option<&Position>, default: f64, total: f64) -> f64 {...}`
- `fn` **`font_string`** — `pub(crate) fn font_string(size: f64) -> String {...}`
- `fn` **`collect_categories`** — `pub(crate) fn collect_categories(series: &[SeriesOption]) -> Vec<String> {...}`
- `fn` **`category_count`** — `pub(crate) fn category_count(series: &[SeriesOption]) -> usize {...}`
- `fn` **`value_extent`** — `pub(crate) fn value_extent(series: &[SeriesOption], axis: Option<&AxisOption>) -> (f64, f64) {...}`
- `fn` **`nice_extent`** — `pub(crate) fn nice_extent(min: f64, max: f64, split: usize) -> (f64, f64) {...}`
- `fn` **`nice_scale`** — `pub(crate) fn nice_scale(min: f64, max: f64, split: usize) -> (f64, f64, f64) {...}`
- `fn` **`nice_number`** — `pub(crate) fn nice_number(value: f64, round: bool) -> f64 {...}`
- `fn` **`value_ticks`** — `pub(crate) fn value_ticks(domain_min: f64, domain_max: f64, split: usize) -> Vec<AxisTick> {...}`
- `fn` **`place_ticks`** — `pub(crate) fn place_ticks(scale: &Scale, ticks: Vec<AxisTick>) -> Vec<AxisTick> {...}`
- `fn` **`ticks_at_interval`** — `pub(crate) fn ticks_at_interval(min: f64, max: f64, interval: f64) -> Vec<AxisTick> {...}`
- `fn` **`log_ticks`** — `pub(crate) fn log_ticks( domain_min: f64, domain_max: f64, base: f64, range_min: f64, range_max: f64, ) -> Vec<AxisTick> {...}`
- `fn` **`category_ticks`** — `pub(crate) fn category_ticks(scale: &Scale) -> Vec<AxisTick> {...}`
- `fn` **`stack_position`** — `pub(crate) fn stack_position(option: &ChartOption, index: usize) -> (usize, usize) {...}`

### `model::impl`

- `fn` **`linear`** — `pub fn linear(domain_min: f64, domain_max: f64, range_min: f64, range_max: f64) -> Self {...}`
- `fn` **`log`** — `pub fn log( domain_min: f64, domain_max: f64, range_min: f64, range_max: f64, base: f64, ) -> Self {...}`
- `fn` **`category`** — `pub fn category(categories: Vec<String>, range_min: f64, range_max: f64, band: f64) -> Self {...}`
- `fn` **`category_count`** — `pub fn category_count(count: usize, range_min: f64, range_max: f64, band: f64) -> Self {...}`
- `fn` **`map`** — `pub fn map(&self, value: f64) -> f64 {...}`
- `fn` **`invert`** — `pub fn invert(&self, pixel: f64) -> f64 {...}`
- `fn` **`band_width`** — `pub fn band_width(&self) -> f64 {...}`
- `fn` **`is_ordinal`** — `pub fn is_ordinal(&self) -> bool {...}`
- `fn` **`position_of`** — `pub fn position_of(&self, value: f64) -> f64 {...}`
- `fn` **`category_at`** — `pub fn category_at(&self, pixel: f64) -> Option<usize> {...}`
- `fn` **`x_axis`** — `pub fn x_axis(&self, index: usize) -> Option<&AxisLayout> {...}`
- `fn` **`y_axis`** — `pub fn y_axis(&self, index: usize) -> Option<&AxisLayout> {...}`
- `fn` **`compute`** — `pub fn compute( option: &ChartOption, width: f64, height: f64, measurer: &TextMeasurer, ) -> ChartLayout {...}`
- `fn` **`compute_with_maps`** — `pub fn compute_with_maps( option: &ChartOption, width: f64, height: f64, measurer: &TextMeasurer, maps: &MapRegistry, ) -> ChartLayout {...}`
- `fn` **`geo`** — `pub fn geo(&self, name: &str) -> Option<&GeoLayout> {...}`
- `fn` **`resolve`** — `pub fn resolve(option: &VisualMapOption, values: &[f64]) -> Self {...}`
- `fn` **`color_of`** — `pub fn color_of(&self, value: f64) -> Color {...}`

### `model::struct`

- `struct` **`Scale`** — `pub struct Scale {`
- `struct` **`AxisTick`** — `pub struct AxisTick {`
- `struct` **`AxisLayout`** — `pub struct AxisLayout {`
- `struct` **`GridLayout`** — `pub struct GridLayout {`
- `struct` **`SeriesPoint`** — `pub struct SeriesPoint {`
- `struct` **`SeriesLayout`** — `pub struct SeriesLayout {`
- `struct` **`ChartLayout`** — `pub struct ChartLayout {`
- `struct` **`VisualPiece`** — `pub struct VisualPiece {`
- `struct` **`VisualMap`** — `pub struct VisualMap {`

### `option::enum`

- `enum` **`SymbolSize`** — `pub enum SymbolSize {`
- `enum` **`DataValue`** — `pub enum DataValue {`
- `enum` **`AxisType`** — `pub enum AxisType {`
- `enum` **`Position`** — `pub enum Position {`
- `enum` **`Orientation`** — `pub enum Orientation {`
- `enum` **`TriggerType`** — `pub enum TriggerType {`
- `enum` **`SymbolType`** — `pub enum SymbolType {`
- `enum` **`DataZoomType`** — `pub enum DataZoomType {`
- `enum` **`VisualMapType`** — `pub enum VisualMapType {`
- `enum` **`LineType`** — `pub enum LineType {`
- `enum` **`LineSmooth`** — `pub enum LineSmooth {`
- `enum` **`SeriesType`** — `pub enum SeriesType {`
- `enum` **`DatasetSourceType`** — `pub enum DatasetSourceType {`
- `enum` **`MarkLineType`** — `pub enum MarkLineType {`
- `enum` **`TreemapLayout`** — `pub enum TreemapLayout {`
- `enum` **`GraphLayout`** — `pub enum GraphLayout {`
- `enum` **`GaugeProgressType`** — `pub enum GaugeProgressType {`

### `option::fn`

- `fn` **`parse_percent`** — `pub(crate) fn parse_percent(input: &str) -> Option<f64> {...}`
- `fn` **`format_number`** — `pub(crate) fn format_number(value: f64) -> String {...}`
- `fn` **`map_series_name`** — `pub(crate) fn map_series_name(series: &SeriesOption, option: &ChartOption) -> Option<String> {...}`
- `fn` **`map_series_aspect`** — `pub(crate) fn map_series_aspect(series: &SeriesOption, option: &ChartOption) -> f64 {...}`

### `option::impl`

- `fn` **`as_number`** — `pub fn as_number(&self) -> Option<f64> {...}`
- `fn` **`to_number`** — `pub fn to_number(&self) -> Option<f64> {...}`
- `fn` **`as_text`** — `pub fn as_text(&self) -> Option<&str> {...}`
- `fn` **`as_list`** — `pub fn as_list(&self) -> Option<&[DataValue]> {...}`
- `fn` **`as_object`** — `pub fn as_object(&self) -> Option<&[(String, DataValue)]> {...}`
- `fn` **`get`** — `pub fn get(&self, name: &str) -> Option<&DataValue> {...}`
- `fn` **`get_mut`** — `pub fn get_mut(&mut self, name: &str) -> Option<&mut DataValue> {...}`
- `fn` **`as_object_mut`** — `pub fn as_object_mut(&mut self) -> Option<&mut [(String, DataValue)]> {...}`
- `fn` **`is_null`** — `pub fn is_null(&self) -> bool {...}`
- `fn` **`name`** — `pub fn name(&self) -> &'static str {...}`
- `fn` **`parse`** — `pub fn parse(name: &str) -> Option<Self> {...}`
- `fn` **`new`** — `pub fn new() -> Self {...}`
- `fn` **`title`** — `pub fn title(mut self, title: TitleOption) -> Self {...}`
- `fn` **`legend`** — `pub fn legend(mut self, legend: LegendOption) -> Self {...}`
- `fn` **`grid`** — `pub fn grid(mut self, grid: GridOption) -> Self {...}`
- `fn` **`x_axis`** — `pub fn x_axis(mut self, axis: AxisOption) -> Self {...}`
- `fn` **`y_axis`** — `pub fn y_axis(mut self, axis: AxisOption) -> Self {...}`
- `fn` **`polar`** — `pub fn polar(mut self, polar: PolarOption) -> Self {...}`
- `fn` **`radar`** — `pub fn radar(mut self, radar: RadarOption) -> Self {...}`
- `fn` **`geo`** — `pub fn geo(mut self, geo: GeoOption) -> Self {...}`
- `fn` **`calendar`** — `pub fn calendar(mut self, calendar: CalendarOption) -> Self {...}`
- `fn` **`dataset`** — `pub fn dataset(mut self, dataset: DatasetOption) -> Self {...}`
- `fn` **`series`** — `pub fn series(mut self, series: SeriesOption) -> Self {...}`
- `fn` **`tooltip`** — `pub fn tooltip(mut self, tooltip: TooltipOption) -> Self {...}`
- `fn` **`toolbox`** — `pub fn toolbox(mut self, toolbox: ToolboxOption) -> Self {...}`
- `fn` **`data_zoom`** — `pub fn data_zoom(mut self, data_zoom: DataZoomOption) -> Self {...}`
- `fn` **`visual_map`** — `pub fn visual_map(mut self, visual_map: VisualMapOption) -> Self {...}`
- `fn` **`graphic`** — `pub fn graphic(mut self, graphic: GraphicOption) -> Self {...}`
- `fn` **`brush`** — `pub fn brush(mut self, brush: BrushOption) -> Self {...}`
- `fn` **`axis_pointer`** — `pub fn axis_pointer(mut self, axis_pointer: AxisPointerOption) -> Self {...}`
- `fn` **`color`** — `pub fn color(mut self, color: Vec<String>) -> Self {...}`
- `fn` **`add_color`** — `pub fn add_color(mut self, color: &str) -> Self {...}`
- `fn` **`background_color`** — `pub fn background_color(mut self, color: &str) -> Self {...}`
- `fn` **`text_style`** — `pub fn text_style(mut self, text_style: LabelOption) -> Self {...}`
- `fn` **`animation`** — `pub fn animation(mut self, animation: bool) -> Self {...}`
- `fn` **`animation_duration`** — `pub fn animation_duration(mut self, duration: f64) -> Self {...}`
- `fn` **`line`** — `pub fn line() -> Self {...}`
- `fn` **`bar`** — `pub fn bar() -> Self {...}`
- `fn` **`pie`** — `pub fn pie() -> Self {...}`
- `fn` **`scatter`** — `pub fn scatter() -> Self {...}`
- `fn` **`effect_scatter`** — `pub fn effect_scatter() -> Self {...}`
- `fn` **`radar`** — `pub fn radar() -> Self {...}`
- `fn` **`gauge`** — `pub fn gauge() -> Self {...}`
- `fn` **`funnel`** — `pub fn funnel() -> Self {...}`
- `fn` **`heatmap`** — `pub fn heatmap() -> Self {...}`
- `fn` **`graph`** — `pub fn graph() -> Self {...}`
- `fn` **`treemap`** — `pub fn treemap() -> Self {...}`
- `fn` **`sunburst`** — `pub fn sunburst() -> Self {...}`
- `fn` **`boxplot`** — `pub fn boxplot() -> Self {...}`
- `fn` **`candlestick`** — `pub fn candlestick() -> Self {...}`
- `fn` **`theme_river`** — `pub fn theme_river() -> Self {...}`
- `fn` **`sankey`** — `pub fn sankey() -> Self {...}`
- `fn` **`parallel`** — `pub fn parallel() -> Self {...}`
- `fn` **`pictorial_bar`** — `pub fn pictorial_bar() -> Self {...}`
- `fn` **`lines`** — `pub fn lines() -> Self {...}`
- `fn` **`map`** — `pub fn map() -> Self {...}`
- `fn` **`custom`** — `pub fn custom() -> Self {...}`
- `fn` **`name`** — `pub fn name(mut self, name: &str) -> Self {...}`
- `fn` **`data`** — `pub fn data(mut self, data: Vec<DataValue>) -> Self {...}`
- `fn` **`add_data`** — `pub fn add_data(&mut self, value: DataValue) -> &mut Self {...}`
- `fn` **`stack`** — `pub fn stack(mut self, stack: &str) -> Self {...}`
- `fn` **`x_axis_index`** — `pub fn x_axis_index(mut self, index: usize) -> Self {...}`
- `fn` **`y_axis_index`** — `pub fn y_axis_index(mut self, index: usize) -> Self {...}`
- `fn` **`item_style`** — `pub fn item_style(mut self, item_style: ItemStyleOption) -> Self {...}`
- `fn` **`line_style`** — `pub fn line_style(mut self, line_style: LineStyleOption) -> Self {...}`
- `fn` **`label`** — `pub fn label(mut self, label: LabelOption) -> Self {...}`
- `fn` **`emphasis`** — `pub fn emphasis(mut self, emphasis: EmphasisOption) -> Self {...}`
- `fn` **`bar_options`** — `pub fn bar_options(mut self, options: BarOptions) -> Self {...}`
- `fn` **`line_options`** — `pub fn line_options(mut self, options: LineOptions) -> Self {...}`
- `fn` **`pie_options`** — `pub fn pie_options(mut self, options: PieOptions) -> Self {...}`
- `fn` **`scatter_options`** — `pub fn scatter_options(mut self, options: ScatterOptions) -> Self {...}`
- `fn` **`radar_options`** — `pub fn radar_options(mut self, options: RadarOptions) -> Self {...}`
- `fn` **`gauge_options`** — `pub fn gauge_options(mut self, options: GaugeOptions) -> Self {...}`
- `fn` **`funnel_options`** — `pub fn funnel_options(mut self, options: FunnelOptions) -> Self {...}`
- `fn` **`heatmap_options`** — `pub fn heatmap_options(mut self, options: HeatmapOptions) -> Self {...}`
- `fn` **`is_line_like`** — `pub fn is_line_like(&self) -> bool {...}`
- `fn` **`has_area`** — `pub fn has_area(&self) -> bool {...}`
- `fn` **`category`** — `pub fn category() -> Self {...}`
- `fn` **`value`** — `pub fn value() -> Self {...}`
- `fn` **`time`** — `pub fn time() -> Self {...}`
- `fn` **`log`** — `pub fn log() -> Self {...}`
- `fn` **`data`** — `pub fn data(mut self, data: Vec<DataValue>) -> Self {...}`
- `fn` **`name`** — `pub fn name(mut self, name: &str) -> Self {...}`
- `fn` **`axis_label`** — `pub fn axis_label(mut self, label: LabelOption) -> Self {...}`
- `fn` **`axis_line`** — `pub fn axis_line(mut self, line: AxisLineOption) -> Self {...}`
- `fn` **`axis_tick`** — `pub fn axis_tick(mut self, tick: AxisTickOption) -> Self {...}`
- `fn` **`split_line`** — `pub fn split_line(mut self, line: SplitLineOption) -> Self {...}`
- `fn` **`min`** — `pub fn min(mut self, min: f64) -> Self {...}`
- `fn` **`max`** — `pub fn max(mut self, max: f64) -> Self {...}`
- `fn` **`new`** — `pub fn new(text: &str) -> Self {...}`
- `fn` **`subtext`** — `pub fn subtext(mut self, subtext: &str) -> Self {...}`
- `fn` **`new`** — `pub fn new(data: Vec<String>) -> Self {...}`
- `fn` **`new`** — `pub fn new() -> Self {...}`
- `fn` **`new`** — `pub fn new() -> Self {...}`
- `fn` **`trigger`** — `pub fn trigger(mut self, trigger: TriggerType) -> Self {...}`
- `fn` **`new`** — `pub fn new() -> Self {...}`
- `fn` **`color`** — `pub fn color(mut self, color: &str) -> Self {...}`
- `fn` **`font_size`** — `pub fn font_size(mut self, size: f64) -> Self {...}`
- `fn` **`font_family`** — `pub fn font_family(mut self, family: &str) -> Self {...}`
- `fn` **`filled`** — `pub fn filled(color: &str) -> Self {...}`
- `fn` **`new`** — `pub fn new(color: &str, width: f64) -> Self {...}`

### `option::struct`

- `struct` **`LabelOffset`** — `pub struct LabelOffset {`
- `struct` **`ItemStyleOption`** — `pub struct ItemStyleOption {`
- `struct` **`ShadowOption`** — `pub struct ShadowOption {`
- `struct` **`LineStyleOption`** — `pub struct LineStyleOption {`
- `struct` **`LabelOption`** — `pub struct LabelOption {`
- `struct` **`LabelLayoutOption`** — `pub struct LabelLayoutOption {`
- `struct` **`EmphasisOption`** — `pub struct EmphasisOption {`
- `struct` **`BlurOption`** — `pub struct BlurOption {`
- `struct` **`MarkPointOption`** — `pub struct MarkPointOption {`
- `struct` **`MarkLineOption`** — `pub struct MarkLineOption {`
- `struct` **`MarkAreaOption`** — `pub struct MarkAreaOption {`
- `struct` **`BarOptions`** — `pub struct BarOptions {`
- `struct` **`LineOptions`** — `pub struct LineOptions {`
- `struct` **`PieOptions`** — `pub struct PieOptions {`
- `struct` **`ScatterOptions`** — `pub struct ScatterOptions {`
- `struct` **`RadarOptions`** — `pub struct RadarOptions {`
- `struct` **`GaugeOptions`** — `pub struct GaugeOptions {`
- `struct` **`GaugeProgressOption`** — `pub struct GaugeProgressOption {`
- `struct` **`AxisLineOption`** — `pub struct AxisLineOption {`
- `struct` **`AxisTickOption`** — `pub struct AxisTickOption {`
- `struct` **`SplitLineOption`** — `pub struct SplitLineOption {`
- `struct` **`PointerOption`** — `pub struct PointerOption {`
- `struct` **`FunnelOptions`** — `pub struct FunnelOptions {`
- `struct` **`HeatmapOptions`** — `pub struct HeatmapOptions {`
- `struct` **`GraphOptions`** — `pub struct GraphOptions {`
- `struct` **`TreemapOptions`** — `pub struct TreemapOptions {`
- `struct` **`SunburstOptions`** — `pub struct SunburstOptions {`
- `struct` **`BoxplotOptions`** — `pub struct BoxplotOptions {`
- `struct` **`CandlestickOptions`** — `pub struct CandlestickOptions {`
- `struct` **`ThemeRiverOptions`** — `pub struct ThemeRiverOptions {`
- `struct` **`SankeyOptions`** — `pub struct SankeyOptions {`
- `struct` **`ParallelOptions`** — `pub struct ParallelOptions {`
- `struct` **`PictorialBarOptions`** — `pub struct PictorialBarOptions {`
- `struct` **`LinesOptions`** — `pub struct LinesOptions {`
- `struct` **`LinesEffectOption`** — `pub struct LinesEffectOption {`
- `struct` **`MapOptions`** — `pub struct MapOptions {`
- `struct` **`CustomOptions`** — `pub struct CustomOptions {`
- `struct` **`SeriesOption`** — `pub struct SeriesOption {`
- `struct` **`TitleOption`** — `pub struct TitleOption {`
- `struct` **`LegendOption`** — `pub struct LegendOption {`
- `struct` **`GridOption`** — `pub struct GridOption {`
- `struct` **`AxisOption`** — `pub struct AxisOption {`
- `struct` **`AxisPointerOption`** — `pub struct AxisPointerOption {`
- `struct` **`TooltipOption`** — `pub struct TooltipOption {`
- `struct` **`ToolboxOption`** — `pub struct ToolboxOption {`
- `struct` **`ToolboxFeatureOption`** — `pub struct ToolboxFeatureOption {`
- `struct` **`ToolboxFeatureSettings`** — `pub struct ToolboxFeatureSettings {`
- `struct` **`DataZoomOption`** — `pub struct DataZoomOption {`
- `struct` **`VisualMapOption`** — `pub struct VisualMapOption {`
- `struct` **`PolarOption`** — `pub struct PolarOption {`
- `struct` **`SplitAreaOption`** — `pub struct SplitAreaOption {`
- `struct` **`RadarOption`** — `pub struct RadarOption {`
- `struct` **`GeoOption`** — `pub struct GeoOption {`
- `struct` **`CalendarOption`** — `pub struct CalendarOption {`
- `struct` **`DatasetOption`** — `pub struct DatasetOption {`
- `struct` **`GraphicOption`** — `pub struct GraphicOption {`
- `struct` **`BrushOption`** — `pub struct BrushOption {`
- `struct` **`ChartOption`** — `pub struct ChartOption {`
- `struct` **`AriaOption`** — `pub struct AriaOption {`

### `paint::enum`

- `enum` **`TextAlign`** — `pub enum TextAlign {`
- `enum` **`TextVerticalAlign`** — `pub enum TextVerticalAlign {`
- `enum` **`TextOverflow`** — `pub enum TextOverflow {`
- `enum` **`Fill`** — `pub enum Fill {`
- `enum` **`Stroke`** — `pub enum Stroke {`
- `enum` **`LineDashType`** — `pub enum LineDashType {`

### `paint::fn`

- `fn` **`parse_css_color`** — `pub(crate) fn parse_css_color(input: &str) -> Option<Color> {...}`
- `fn` **`named_color`** — `pub(crate) fn named_color(name: &str) -> Option<Color> {...}`

### `paint::impl`

- `fn` **`rgb`** — `pub fn rgb(red: u8, green: u8, blue: u8) -> Self {...}`
- `fn` **`rgba`** — `pub fn rgba(red: u8, green: u8, blue: u8, alpha: u8) -> Self {...}`
- `fn` **`from_u32`** — `pub fn from_u32(packed: u32) -> Self {...}`
- `fn` **`to_u32`** — `pub fn to_u32(self) -> u32 {...}`
- `fn` **`to_css`** — `pub fn to_css(self) -> String {...}`
- `fn` **`lerp`** — `pub fn lerp(self, other: Self, amount: f64) -> Self {...}`
- `fn` **`parse`** — `pub fn parse(input: &str) -> Option<Self> {...}`
- `fn` **`with_alpha`** — `pub fn with_alpha(self, alpha: u8) -> Self {...}`
- `fn` **`mix`** — `pub fn mix(self, other: Self, ratio: f64) -> Self {...}`
- `fn` **`lighten`** — `pub fn lighten(self, ratio: f64) -> Self {...}`
- `fn` **`darken`** — `pub fn darken(self, ratio: f64) -> Self {...}`
- `fn` **`new`** — `pub fn new(start: (f64, f64), end: (f64, f64)) -> Self {...}`
- `fn` **`with_stop`** — `pub fn with_stop(mut self, offset: f64, color: Color) -> Self {...}`
- `fn` **`new`** — `pub fn new(center: (f64, f64), radius: f64) -> Self {...}`
- `fn` **`with_stop`** — `pub fn with_stop(mut self, offset: f64, color: Color) -> Self {...}`
- `fn` **`new`** — `pub fn new() -> Self {...}`
- `fn` **`font`** — `pub fn font(&self) -> String {...}`
- `fn` **`line_height_px`** — `pub fn line_height_px(&self) -> f64 {...}`
- `fn` **`with_rich`** — `pub fn with_rich(mut self, name: &str, style: RichTextStyle) -> Self {...}`
- `fn` **`new`** — `pub fn new() -> Self {...}`
- `fn` **`new`** — `pub fn new() -> Self {...}`
- `fn` **`geometry`** — `pub fn geometry(&self) -> StrokeStyle {...}`
- `fn` **`dash_for`** — `pub fn dash_for(dash_type: LineDashType, width: f64) -> DashPattern {...}`
- `fn` **`new`** — `pub fn new() -> Self {...}`
- `fn` **`solid_color`** — `pub fn solid_color(&self) -> Option<Color> {...}`
- `fn` **`solid_color`** — `pub fn solid_color(&self) -> Option<Color> {...}`

### `paint::struct`

- `struct` **`Color`** — `pub struct Color {`
- `struct` **`GradientStop`** — `pub struct GradientStop {`
- `struct` **`LinearGradient`** — `pub struct LinearGradient {`
- `struct` **`RadialGradient`** — `pub struct RadialGradient {`
- `struct` **`Shadow`** — `pub struct Shadow {`
- `struct` **`TextStyle`** — `pub struct TextStyle {`
- `struct` **`RichTextStyle`** — `pub struct RichTextStyle {`
- `struct` **`LineStyle`** — `pub struct LineStyle {`
- `struct` **`ShapeStyle`** — `pub struct ShapeStyle {`

### `series::enum`

- `enum` **`StepPosition`** — `pub enum StepPosition {`
- `enum` **`SymbolShape`** — `pub enum SymbolShape {`

### `series::fn`

- `fn` **`baseline_of`** — `pub(crate) fn baseline_of(points: &[SeriesPoint]) -> f64 {...}`
- `fn` **`pie_geometry`** — `pub(crate) fn pie_geometry(series: &SeriesOption, layout: &SeriesLayout) -> (f64, f64, f64) {...}`
- `fn` **`sector_path`** — `pub(crate) fn sector_path( center_x: f64, center_y: f64, radius: f64, inner_radius: f64, start_angle: f64, end_angle: f64, ) -> Path {...}`
- `fn` **`average_spacing`** — `pub(crate) fn average_spacing(points: &[SeriesPoint]) -> f64 {...}`
- `fn` **`palette_color`** — `pub(crate) fn palette_color(option: &ChartOption, index: usize) -> Color {...}`
- `fn` **`series_fill`** — `pub(crate) fn series_fill(option: &SeriesOption, color: Color) -> Fill {...}`
- `fn` **`series_stroke`** — `pub(crate) fn series_stroke(option: &SeriesOption, color: Color) -> Stroke {...}`
- `fn` **`series_line_style`** — `pub(crate) fn series_line_style(option: &SeriesOption, color: Color) -> LineStyle {...}`
- `fn` **`series_label_style`** — `pub(crate) fn series_label_style(option: &SeriesOption, color: Color) -> TextStyle {...}`
- `fn` **`symbol_path`** — `pub(crate) fn symbol_path(kind: SymbolType, x: f64, y: f64, size: f64) -> Path {...}`
- `fn` **`polyline_path`** — `pub(crate) fn polyline_path(points: &[Point]) -> Path {...}`
- `fn` **`smooth_path`** — `pub(crate) fn smooth_path(points: &[Point]) -> Path {...}`
- `fn` **`step_path`** — `pub(crate) fn step_path(points: &[Point], step: StepPosition) -> Path {...}`
- `fn` **`draw_custom`** — `pub(crate) fn draw_custom( list: &mut DisplayList, series: &SeriesOption, series_layout: &SeriesLayout, layout: &ChartLayout, color: Color, z: i32, ) {...}`
- `fn` **`draw_parallel`** — `pub(crate) fn draw_parallel( list: &mut DisplayList, series: &SeriesOption, layout: &SeriesLayout, color: Color, z: i32, ) {...}`
- `fn` **`draw_lines`** — `pub(crate) fn draw_lines( list: &mut DisplayList, series: &SeriesOption, layout: &SeriesLayout, color: Color, z: i32, ) {...}`
- `fn` **`draw_theme_river`** — `pub(crate) fn draw_theme_river( list: &mut DisplayList, series: &SeriesOption, layout: &SeriesLayout, color: Color, z: i32, ) {...}`
- `fn` **`draw_pictorial_bar`** — `pub(crate) fn draw_pictorial_bar( list: &mut DisplayList, series: &SeriesOption, layout: &SeriesLayout, color: Color, z: i32, ) {...}`
- `fn` **`draw_funnel`** — `pub(crate) fn draw_funnel( list: &mut DisplayList, series: &SeriesOption, layout: &SeriesLayout, color: Color, z: i32, ) {...}`
- `fn` **`draw_gauge`** — `pub(crate) fn draw_gauge( list: &mut DisplayList, series: &SeriesOption, layout: &SeriesLayout, color: Color, z: i32, ) {...}`
- `fn` **`arc_path`** — `pub(crate) fn arc_path( center_x: f64, center_y: f64, outer_radius: f64, inner_radius: f64, start_angle: f64, end_angle: f64, ) -> Path {...}`
- `fn` **`graph_nodes`** — `pub(crate) fn graph_nodes(series: &SeriesOption) -> Vec<GraphNode> {...}`
- `fn` **`graph_links`** — `pub(crate) fn graph_links(series: &SeriesOption) -> Vec<GraphLink> {...}`
- `fn` **`place_graph_nodes`** — `pub(crate) fn place_graph_nodes(nodes: &mut [GraphNode], plot: &BBox, radius: f64) {...}`
- `fn` **`draw_graph`** — `pub(crate) fn draw_graph( list: &mut DisplayList, series: &SeriesOption, layout: &SeriesLayout, color: Color, z: i32, ) {...}`
- `fn` **`draw_map`** — `pub(crate) fn draw_map( list: &mut DisplayList, option: &ChartOption, series: &SeriesOption, series_layout: &SeriesLayout, layout: &ChartLayout, color: Color, z: i32, ) {...}`
- `fn` **`radar_geometry`** — `pub(crate) fn radar_geometry(option: &ChartOption, layout: &SeriesLayout) -> RadarGeometry {...}`
- `fn` **`draw_radar`** — `pub(crate) fn draw_radar( list: &mut DisplayList, option: &ChartOption, series: &SeriesOption, layout: &SeriesLayout, color: Color, z: i32, ) {...}`
- `fn` **`series_values`** — `pub(crate) fn series_values(series: &SeriesOption) -> Vec<f64> {...}`
- `fn` **`sankey_nodes`** — `pub(crate) fn sankey_nodes(series: &SeriesOption) -> Vec<SankeyNode> {...}`
- `fn` **`sankey_links`** — `pub(crate) fn sankey_links(series: &SeriesOption) -> Vec<SankeyLink> {...}`
- `fn` **`place_sankey_nodes`** — `pub(crate) fn place_sankey_nodes(nodes: &mut [SankeyNode], links: &[SankeyLink], plot: &BBox) {...}`
- `fn` **`draw_sankey`** — `pub(crate) fn draw_sankey( list: &mut DisplayList, series: &SeriesOption, layout: &SeriesLayout, color: Color, z: i32, ) {...}`
- `fn` **`flatten_sectors`** — `pub(crate) fn flatten_sectors( series: &SeriesOption, depth: usize, start_angle: f64, end_angle: f64, output: &mut Vec<SunburstSector>, ) {...}`
- `fn` **`draw_sunburst`** — `pub(crate) fn draw_sunburst( list: &mut DisplayList, series: &SeriesOption, layout: &SeriesLayout, color: Color, z: i32, ) {...}`
- `fn` **`flatten_tiles`** — `pub(crate) fn flatten_tiles(series: &SeriesOption, rect: BBox, depth: usize) -> Vec<TreeTile> {...}`
- `fn` **`squarify`** — `pub(crate) fn squarify(tiles: &mut [TreeTile], rect: BBox, gap: f64) {...}`
- `fn` **`draw_treemap`** — `pub(crate) fn draw_treemap( list: &mut DisplayList, series: &SeriesOption, layout: &SeriesLayout, color: Color, z: i32, ) {...}`

### `series::impl`

- `fn` **`new`** — `pub fn new() -> Self {...}`
- `fn` **`draw`** — `pub fn draw(&mut self, list: &mut DisplayList, option: &ChartOption, layout: &ChartLayout) {...}`
- `fn` **`point`** — `pub fn point(&self, index: usize, ratio: f64) -> (f64, f64) {...}`

### `series::struct`

- `struct` **`SeriesRenderer`** — `pub struct SeriesRenderer {`
- `struct` **`GraphNode`** — `pub(crate) struct GraphNode {`
- `struct` **`GraphLink`** — `pub(crate) struct GraphLink {`
- `struct` **`RadarGeometry`** — `pub(crate) struct RadarGeometry {`
- `struct` **`SankeyNode`** — `pub(crate) struct SankeyNode {`
- `struct` **`SankeyLink`** — `pub(crate) struct SankeyLink {`
- `struct` **`SunburstSector`** — `pub(crate) struct SunburstSector {`
- `struct` **`TreeTile`** — `pub(crate) struct TreeTile {`

### `text::enum`

- `enum` **`LabelAlign`** — `pub enum LabelAlign {`
- `enum` **`LabelVerticalAlign`** — `pub enum LabelVerticalAlign {`

### `text::fn`

- `fn` **`split_rich_text`** — `pub(crate) fn split_rich_text(text: &str) -> Vec<(Option<String>, String)> {...}`
- `fn` **`font_size_of`** — `pub(crate) fn font_size_of(font: &str) -> f64 {...}`
- `fn` **`approximate_metrics`** — `pub(crate) fn approximate_metrics(text: &str, size: f64) -> TextMetrics {...}`

### `text::impl`

- `fn` **`new`** — `pub fn new(measurer: TextMeasurer, atlas: GlyphAtlas) -> Self {...}`
- `fn` **`measurer`** — `pub fn measurer(&self) -> &TextMeasurer {...}`
- `fn` **`atlas`** — `pub fn atlas(&self) -> &GlyphAtlas {...}`
- `fn` **`atlas_mut`** — `pub fn atlas_mut(&mut self) -> &mut GlyphAtlas {...}`
- `fn` **`shape`** — `pub fn shape(&mut self, text: &str, style: &TextStyle, x: f64, y: f64) -> TextRun {...}`
- `fn` **`new`** — `pub fn new(width: u32, height: u32) -> Option<Self> {...}`
- `fn` **`canvas`** — `pub fn canvas(&self) -> &HtmlCanvasElement {...}`
- `fn` **`width`** — `pub fn width(&self) -> u32 {...}`
- `fn` **`height`** — `pub fn height(&self) -> u32 {...}`
- `fn` **`is_dirty`** — `pub fn is_dirty(&self) -> bool {...}`
- `fn` **`mark_clean`** — `pub fn mark_clean(&mut self) {...}`
- `fn` **`len`** — `pub fn len(&self) -> usize {...}`
- `fn` **`is_empty`** — `pub fn is_empty(&self) -> bool {...}`
- `fn` **`glyph`** — `pub fn glyph(&mut self, character: char, font: &str) -> GlyphEntry {...}`
- `fn` **`new`** — `pub fn new() -> Option<Self> {...}`
- `fn` **`approximate`** — `pub fn approximate() -> Self {...}`
- `fn` **`measure`** — `pub fn measure(&self, text: &str, font: &str) -> TextMetrics {...}`
- `fn` **`cache_size`** — `pub fn cache_size(&self) -> usize {...}`
- `fn` **`clear_cache`** — `pub fn clear_cache(&self) {...}`

### `text::struct`

- `struct` **`GlyphAtlas`** — `pub struct GlyphAtlas {`
- `struct` **`GlyphQuad`** — `pub struct GlyphQuad {`
- `struct` **`TextLine`** — `pub struct TextLine {`
- `struct` **`TextRun`** — `pub struct TextRun {`
- `struct` **`TextShaper`** — `pub struct TextShaper {`
- `struct` **`TextMetrics`** — `pub struct TextMetrics {`
- `struct` **`GlyphEntry`** — `pub struct GlyphEntry {`
- `struct` **`GlyphKey`** — `pub struct GlyphKey {`
- `struct` **`TextMeasurer`** — `pub struct TextMeasurer {`

### `backend::canvas2d::fn`

- `fn` **`line_cap_name`** — `pub(crate) fn line_cap_name(cap: LineCap) -> &'static str {...}`
- `fn` **`line_join_name`** — `pub(crate) fn line_join_name(join: LineJoin) -> &'static str {...}`

### `backend::canvas2d::impl`

- `fn` **`create`** — `pub fn create(canvas: &HtmlCanvasElement) -> Option<Self> {...}`
- `fn` **`canvas`** — `pub fn canvas(&self) -> &HtmlCanvasElement {...}`
- `fn` **`dpr`** — `pub fn dpr(&self) -> f64 {...}`
- `fn` **`trace_path`** — `pub(crate) fn trace_path(&self, path: &Path) {...}`
- `fn` **`trace_strip`** — `pub(crate) fn trace_strip(&self, points: &[Point], baseline: f32) {...}`
- `fn` **`apply_fill`** — `pub(crate) fn apply_fill(&self, paint: &Fill) {...}`
- `fn` **`apply_stroke`** — `pub(crate) fn apply_stroke(&self, paint: &Stroke) {...}`

### `backend::canvas2d::struct`

- `struct` **`Canvas2dChartBackend`** — `pub struct Canvas2dChartBackend {`

### `backend::common::enum`

- `enum` **`BackendKind`** — `pub enum BackendKind {`

### `backend::common::impl`

- `fn` **`name`** — `pub fn name(&self) -> &'static str {...}`
- `fn` **`is_gpu`** — `pub fn is_gpu(&self) -> bool {...}`
- `fn` **`new`** — `pub fn new() -> Self {...}`
- `fn` **`create`** — `pub async fn create( canvas: &HtmlCanvasElement, preferred: BackendKind, ) -> Option<Box<dyn ChartBackend>> {...}`
- `fn` **`detect`** — `pub fn detect(preferred: BackendKind) -> BackendKind {...}`

### `backend::common::struct`

- `struct` **`BackendFactory`** — `pub struct BackendFactory;`

### `backend::common::trait`

- `trait` **`ChartBackend`** — `pub trait ChartBackend {`

### `backend::webgl::enum`

- `enum` **`WebGl2VertexKind`** — `pub enum WebGl2VertexKind {`
- `enum` **`WebGl2BatchKind`** — `pub enum WebGl2BatchKind {`
- `enum` **`WebGl2Gradient`** — `pub(crate) enum WebGl2Gradient {`

### `backend::webgl::fn`

- `fn` **`is_supported`** — `pub(crate) fn is_supported() -> bool {...}`
- `fn` **`fingerprint`** — `pub(crate) fn fingerprint(list: &DisplayList) -> u64 {...}`
- `fn` **`ramp_bytes`** — `pub(crate) fn ramp_bytes(gradient: &WebGl2Gradient) -> Vec<u8> {...}`
- `fn` **`parameter_values`** — `pub(crate) fn parameter_values(gradient: &WebGl2Gradient) -> [f32; 8] {...}`
- `fn` **`dash_contours`** — `pub(crate) fn dash_contours(contours: &[Contour], pattern: &[f32], offset: f32) -> Vec<Contour> {...}`
- `fn` **`unpack_color`** — `pub(crate) fn unpack_color(packed: u32) -> [f32; 4] {...}`
- `fn` **`scissor_of`** — `pub(crate) fn scissor_of(bounds: &BBox) -> WebGl2Scissor {...}`
- `fn` **`intersect_scissor`** — `pub(crate) fn intersect_scissor( current: Option<WebGl2Scissor>, rectangle: WebGl2Scissor, ) -> WebGl2Scissor {...}`
- `fn` **`scaled_color`** — `pub(crate) fn scaled_color(color: Color, opacity: f64) -> [f32; 4] {...}`
- `fn` **`compile_shader`** — `pub(crate) fn compile_shader( context: &WebGl2RenderingContext, kind: u32, source: &str, ) -> Option<WebGlShader> {...}`

### `backend::webgl::impl`

- `fn` **`is_supported`** — `pub fn is_supported() -> bool {...}`
- `fn` **`create`** — `pub fn create(canvas: &HtmlCanvasElement) -> Option<Self> {...}`
- `fn` **`canvas`** — `pub fn canvas(&self) -> &HtmlCanvasElement {...}`
- `fn` **`draw_call_count`** — `pub fn draw_call_count(&self) -> usize {...}`
- `fn` **`code`** — `pub fn code(self) -> f32 {...}`
- `fn` **`new`** — `pub(crate) fn new() -> Self {...}`
- `fn` **`write_u64`** — `pub(crate) fn write_u64(&mut self, value: u64) {...}`
- `fn` **`write_u32`** — `pub(crate) fn write_u32(&mut self, value: u32) {...}`
- `fn` **`write_f32`** — `pub(crate) fn write_f32(&mut self, value: f32) {...}`
- `fn` **`write_f64`** — `pub(crate) fn write_f64(&mut self, value: f64) {...}`
- `fn` **`write_str`** — `pub(crate) fn write_str(&mut self, value: &str) {...}`
- `fn` **`finish`** — `pub(crate) fn finish(&self) -> u64 {...}`

### `backend::webgl::struct`

- `struct` **`WebGl2ChartBackend`** — `pub struct WebGl2ChartBackend {`
- `struct` **`WebGl2Program`** — `pub(crate) struct WebGl2Program {`
- `struct` **`WebGl2Style`** — `pub(crate) struct WebGl2Style {`
- `struct` **`WebGl2TextureRect`** — `pub(crate) struct WebGl2TextureRect {`
- `struct` **`WebGl2Batch`** — `pub(crate) struct WebGl2Batch {`
- `struct` **`WebGl2Scissor`** — `pub(crate) struct WebGl2Scissor {`
- `struct` **`WebGl2Image`** — `pub(crate) struct WebGl2Image {`
- `struct` **`DisplayHasher`** — `pub(crate) struct DisplayHasher {`

### `backend::webgpu::enum`

- `enum` **`WebGpuBatchKind`** — `pub enum WebGpuBatchKind {`

### `backend::webgpu::fn`

- `fn` **`gpu_object`** — `pub(crate) fn gpu_object(entries: &[(&str, &JsValue)]) -> JsValue {...}`
- `fn` **`gpu_array`** — `pub(crate) fn gpu_array(values: &[JsValue]) -> JsValue {...}`
- `fn` **`gpu_get`** — `pub(crate) fn gpu_get(target: &JsValue, key: &str) -> Option<JsValue> {...}`
- `fn` **`gpu_method`** — `pub(crate) fn gpu_method(target: &JsValue, key: &str) -> Option<Function> {...}`
- `fn` **`gpu_set`** — `pub(crate) fn gpu_set(target: &JsValue, key: &str, value: &JsValue) -> bool {...}`
- `fn` **`gpu_queue`** — `pub(crate) fn gpu_queue(device: &JsValue) -> Option<JsValue> {...}`
- `fn` **`hash_path`** — `pub(crate) fn hash_path(hasher: &mut GpuHasher, path: &Path) {...}`
- `fn` **`hash_fill`** — `pub(crate) fn hash_fill(hasher: &mut GpuHasher, paint: &Fill) {...}`
- `fn` **`hash_stroke`** — `pub(crate) fn hash_stroke(hasher: &mut GpuHasher, paint: &Stroke) {...}`
- `fn` **`hash_line_style`** — `pub(crate) fn hash_line_style(hasher: &mut GpuHasher, style: &LineStyle) {...}`
- `fn` **`hash_text_style`** — `pub(crate) fn hash_text_style(hasher: &mut GpuHasher, style: &TextStyle) {...}`
- `fn` **`linear_gradient_color`** — `pub(crate) fn linear_gradient_color(gradient: &LinearGradient, x: f64, y: f64) -> Color {...}`
- `fn` **`radial_gradient_color`** — `pub(crate) fn radial_gradient_color(gradient: &RadialGradient, x: f64, y: f64) -> Color {...}`
- `fn` **`sample_gradient`** — `pub(crate) fn sample_gradient(stops: &[GradientStop], position: f64) -> Color {...}`
- `fn` **`push_solid_vertex`** — `pub(crate) fn push_solid_vertex(out: &mut Vec<u8>, x: f32, y: f32, color: Color, alpha: u8) {...}`
- `fn` **`push_textured_vertex`** — `pub(crate) fn push_textured_vertex( out: &mut Vec<u8>, x: f32, y: f32, u: f32, v: f32, color: Color, alpha: u8, ) {...}`
- `fn` **`scaled_alpha`** — `pub(crate) fn scaled_alpha(color: Color, opacity: f64) -> u8 {...}`

### `backend::webgpu::impl`

- `fn` **`is_supported`** — `pub fn is_supported() -> bool {...}`
- `fn` **`create`** — `pub async fn create(canvas: &HtmlCanvasElement) -> Option<Self> {...}`
- `fn` **`canvas`** — `pub fn canvas(&self) -> &HtmlCanvasElement {...}`
- `fn` **`dpr`** — `pub fn dpr(&self) -> f64 {...}`
- `fn` **`format`** — `pub fn format(&self) -> &str {...}`
- `fn` **`batch_count`** — `pub fn batch_count(&self) -> usize {...}`
- `fn` **`invalidate`** — `pub fn invalidate(&mut self) {...}`
- `fn` **`new`** — `pub(crate) fn new() -> Self {...}`
- `fn` **`write_f32`** — `pub(crate) fn write_f32(&mut self, value: f32) {...}`
- `fn` **`write_f64`** — `pub(crate) fn write_f64(&mut self, value: f64) {...}`

### `backend::webgpu::struct`

- `struct` **`WebGpuChartBackend`** — `pub struct WebGpuChartBackend {`
- `struct` **`WebGpuBuffer`** — `pub(crate) struct WebGpuBuffer {`
- `struct` **`WebGpuAtlas`** — `pub(crate) struct WebGpuAtlas {`
- `struct` **`WebGpuImage`** — `pub(crate) struct WebGpuImage {`
- `struct` **`WebGpuBatch`** — `pub(crate) struct WebGpuBatch {`
- `struct` **`WebGpuScissor`** — `pub(crate) struct WebGpuScissor {`
- `struct` **`WebGpuApi`** — `pub(crate) struct WebGpuApi {`
- `struct` **`WebGpuEncoderApi`** — `pub(crate) struct WebGpuEncoderApi {`
- `struct` **`WebGpuPassApi`** — `pub(crate) struct WebGpuPassApi {`
- `struct` **`GpuHasher`** — `pub(crate) struct GpuHasher {`

### `geom::base::enum`

- `enum` **`PathCommand`** — `pub enum PathCommand {`
- `enum` **`FillRule`** — `pub enum FillRule {`
- `enum` **`LineCap`** — `pub enum LineCap {`
- `enum` **`LineJoin`** — `pub enum LineJoin {`

### `geom::base::fn`

- `fn` **`arc_to_cubic`** — `pub(crate) fn arc_to_cubic<F>( ellipse: Ellipse, start_angle: f64, sweep: f64, segments: usize, mut emit: F, ) where F: FnMut(f64, f64, f64, f64, f64, f64), {...}`
- `fn` **`arc_segment_count`** — `pub(crate) fn arc_segment_count(sweep: f64, radius: f64, tolerance: f64) -> usize {...}`
- `fn` **`cubic_segment_count`** — `pub(crate) fn cubic_segment_count(points: [(f64, f64); 4], tolerance: f64) -> usize {...}`

### `geom::base::impl`

- `fn` **`identity`** — `pub fn identity() -> Self {...}`
- `fn` **`translate`** — `pub fn translate(tx: f64, ty: f64) -> Self {...}`
- `fn` **`scale`** — `pub fn scale(sx: f64, sy: f64) -> Self {...}`
- `fn` **`rotate`** — `pub fn rotate(angle: f64) -> Self {...}`
- `fn` **`from_rect_to_rect`** — `pub fn from_rect_to_rect(from: BBox, to: BBox) -> Self {...}`
- `fn` **`then`** — `pub fn then(&self, other: &Self) -> Self {...}`
- `fn` **`apply`** — `pub fn apply(&self, x: f64, y: f64) -> (f64, f64) {...}`
- `fn` **`apply_f32`** — `pub fn apply_f32(&self, x: f32, y: f32) -> (f32, f32) {...}`
- `fn` **`determinant`** — `pub fn determinant(&self) -> f64 {...}`
- `fn` **`invert`** — `pub fn invert(&self) -> Option<Self> {...}`
- `fn` **`empty`** — `pub fn empty() -> Self {...}`
- `fn` **`from_min_size`** — `pub fn from_min_size(min_x: f64, min_y: f64, width: f64, height: f64) -> Self {...}`
- `fn` **`from_corners`** — `pub fn from_corners(x0: f64, y0: f64, x1: f64, y1: f64) -> Self {...}`
- `fn` **`is_empty`** — `pub fn is_empty(&self) -> bool {...}`
- `fn` **`width`** — `pub fn width(&self) -> f64 {...}`
- `fn` **`height`** — `pub fn height(&self) -> f64 {...}`
- `fn` **`center_x`** — `pub fn center_x(&self) -> f64 {...}`
- `fn` **`center_y`** — `pub fn center_y(&self) -> f64 {...}`
- `fn` **`extend_point`** — `pub fn extend_point(&mut self, x: f64, y: f64) {...}`
- `fn` **`extend_box`** — `pub fn extend_box(&mut self, other: &BBox) {...}`
- `fn` **`contains`** — `pub fn contains(&self, x: f64, y: f64) -> bool {...}`
- `fn` **`intersects`** — `pub fn intersects(&self, other: &BBox) -> bool {...}`
- `fn` **`intersection`** — `pub fn intersection(&self, other: &BBox) -> Option<BBox> {...}`
- `fn` **`union`** — `pub fn union(&self, other: &BBox) -> BBox {...}`
- `fn` **`new`** — `pub fn new(x: f32, y: f32) -> Self {...}`
- `fn` **`distance_to`** — `pub fn distance_to(&self, other: &Point) -> f32 {...}`
- `fn` **`distance_squared_to`** — `pub fn distance_squared_to(&self, other: &Point) -> f32 {...}`
- `fn` **`from_coordinates`** — `pub fn from_coordinates(coordinates: &[f32]) -> Self {...}`
- `fn` **`signed_area`** — `pub fn signed_area(&self) -> f64 {...}`
- `fn` **`is_clockwise`** — `pub fn is_clockwise(&self) -> bool {...}`
- `fn` **`reverse`** — `pub fn reverse(&mut self) {...}`
- `fn` **`new`** — `pub fn new() -> Self {...}`
- `fn` **`builder`** — `pub fn builder() -> PathBuilder {...}`
- `fn` **`commands`** — `pub fn commands(&self) -> &[PathCommand] {...}`
- `fn` **`fill_rule`** — `pub fn fill_rule(&self) -> FillRule {...}`
- `fn` **`is_empty`** — `pub fn is_empty(&self) -> bool {...}`
- `fn` **`len`** — `pub fn len(&self) -> usize {...}`
- `fn` **`bounds`** — `pub fn bounds(&self) -> BBox {...}`
- `fn` **`transformed`** — `pub fn transformed(&self, transform: &Transform2D) -> Path {...}`
- `fn` **`new`** — `pub fn new() -> Self {...}`
- `fn` **`fill_rule`** — `pub fn fill_rule(mut self, rule: FillRule) -> Self {...}`
- `fn` **`move_to`** — `pub fn move_to(mut self, x: f32, y: f32) -> Self {...}`
- `fn` **`line_to`** — `pub fn line_to(mut self, x: f32, y: f32) -> Self {...}`
- `fn` **`quad_to`** — `pub fn quad_to(mut self, control_x: f32, control_y: f32, x: f32, y: f32) -> Self {...}`
- `fn` **`cubic_to`** — `pub fn cubic_to( mut self, control1_x: f32, control1_y: f32, control2_x: f32, control2_y: f32, x: f32, y: f32, ) -> Self {...}`
- `fn` **`close`** — `pub fn close(mut self) -> Self {...}`
- `fn` **`arc`** — `pub fn arc( mut self, center_x: f32, center_y: f32, radius_x: f32, radius_y: f32, start_angle: f64, end_angle: f64, ) -> Self {...}`
- `fn` **`ellipse`** — `pub fn ellipse(mut self, center_x: f32, center_y: f32, radius_x: f32, radius_y: f32) -> Self {...}`
- `fn` **`rect`** — `pub fn rect(mut self, x: f32, y: f32, width: f32, height: f32) -> Self {...}`
- `fn` **`round_rect`** — `pub fn round_rect(mut self, x: f32, y: f32, width: f32, height: f32, radius: f32) -> Self {...}`
- `fn` **`polygon`** — `pub fn polygon(mut self, points: &[Point]) -> Self {...}`
- `fn` **`build`** — `pub fn build(self) -> Path {...}`
- `fn` **`solid`** — `pub fn solid() -> Self {...}`
- `fn` **`new`** — `pub fn new(pattern: Vec<f32>, offset: f32) -> Self {...}`
- `fn` **`is_solid`** — `pub fn is_solid(&self) -> bool {...}`

### `geom::base::struct`

- `struct` **`Transform2D`** — `pub struct Transform2D {`
- `struct` **`BBox`** — `pub struct BBox {`
- `struct` **`Point`** — `pub struct Point {`
- `struct` **`Polygon`** — `pub struct Polygon {`
- `struct` **`Path`** — `pub struct Path {`
- `struct` **`PathBuilder`** — `pub struct PathBuilder {`
- `struct` **`Ellipse`** — `pub(crate) struct Ellipse {`
- `struct` **`StrokeStyle`** — `pub struct StrokeStyle {`
- `struct` **`DashPattern`** — `pub struct DashPattern {`

### `geom::tess::fn`

- `fn` **`polygon_signed_area`** — `pub(crate) fn polygon_signed_area(points: &[Point], start: usize, count: usize) -> f64 {...}`
- `fn` **`point_in_polygon`** — `pub(crate) fn point_in_polygon(x: f64, y: f64, points: &[Point]) -> bool {...}`
- `fn` **`eval_quad`** — `pub(crate) fn eval_quad(p0: (f64, f64), p1: (f64, f64), p2: (f64, f64), t: f64) -> (f64, f64) {...}`
- `fn` **`eval_cubic`** — `pub(crate) fn eval_cubic( p0: (f64, f64), p1: (f64, f64), p2: (f64, f64), p3: (f64, f64), t: f64, ) -> (f64, f64) {...}`
- `fn` **`quad_segment_count`** — `pub(crate) fn quad_segment_count( p0: (f64, f64), p1: (f64, f64), p2: (f64, f64), tolerance: f64, ) -> usize {...}`
- `fn` **`offset_point`** — `pub(crate) fn offset_point(from: Point, to: Point, distance: f32) -> Point {...}`
- `fn` **`rectangle_of`** — `pub(crate) fn rectangle_of(path: &Path) -> Option<[Point; 4]> {...}`
- `fn` **`fill_contours_into`** — `pub(crate) fn fill_contours_into( mesh: &mut SolidMesh, contours: &[Contour], color: u32, working: &mut Vec<Point>, indices: &mut Vec<usize>, ) {...}`
- `fn` **`stroke_contours_into`** — `pub(crate) fn stroke_contours_into( mesh: &mut SolidMesh, contours: &[Contour], style: &StrokeStyle, color: u32, ) {...}`
- `fn` **`ear_clip`** — `pub(crate) fn ear_clip(points: &[Point], output: &mut Vec<usize>) {...}`

### `geom::tess::impl`

- `fn` **`new`** — `pub fn new() -> Self {...}`
- `fn` **`with_tolerance`** — `pub fn with_tolerance(tolerance: f64) -> Self {...}`
- `fn` **`tolerance`** — `pub fn tolerance(&self) -> f64 {...}`
- `fn` **`flatten`** — `pub fn flatten(&mut self, path: &Path) -> &FlatPath {...}`
- `fn` **`fill`** — `pub fn fill(&mut self, path: &Path, color: u32) -> SolidMesh {...}`
- `fn` **`fill_flattened`** — `pub fn fill_flattened(&mut self, path: &Path, color: u32, rule: FillRule) -> SolidMesh {...}`
- `fn` **`fill_contours`** — `pub fn fill_contours(&mut self, contours: &[Contour], color: u32, rule: FillRule) -> SolidMesh {...}`
- `fn` **`fill_strip`** — `pub fn fill_strip(&mut self, points: &[Point], baseline: f32, color: u32) -> SolidMesh {...}`
- `fn` **`stroke`** — `pub fn stroke(&mut self, path: &Path, style: &StrokeStyle, color: u32) -> SolidMesh {...}`
- `fn` **`stroke_contours`** — `pub fn stroke_contours( &mut self, contours: &[Contour], style: &StrokeStyle, color: u32, ) -> SolidMesh {...}`
- `fn` **`new`** — `pub fn new() -> Self {...}`
- `fn` **`is_empty`** — `pub fn is_empty(&self) -> bool {...}`
- `fn` **`triangle_count`** — `pub fn triangle_count(&self) -> usize {...}`
- `fn` **`reserve`** — `pub fn reserve(&mut self, vertices: usize, triangles: usize) {...}`
- `fn` **`push_triangle`** — `pub fn push_triangle(&mut self, a: SolidVertex, b: SolidVertex, c: SolidVertex) {...}`
- `fn` **`push_quad`** — `pub fn push_quad(&mut self, a: SolidVertex, b: SolidVertex, c: SolidVertex, d: SolidVertex) {...}`
- `fn` **`new`** — `pub fn new() -> Self {...}`
- `fn` **`is_empty`** — `pub fn is_empty(&self) -> bool {...}`
- `fn` **`reserve`** — `pub fn reserve(&mut self, quads: usize) {...}`
- `fn` **`push_quad`** — `pub fn push_quad(&mut self, corners: [(f32, f32); 4], uvs: [(f32, f32); 4], color: u32) {...}`

### `geom::tess::struct`

- `struct` **`Contour`** — `pub struct Contour {`
- `struct` **`FlatPath`** — `pub struct FlatPath {`
- `struct` **`Tessellator`** — `pub struct Tessellator {`
- `struct` **`SolidVertex`** — `pub struct SolidVertex {`
- `struct` **`SolidMesh`** — `pub struct SolidMesh {`
- `struct` **`TextVertex`** — `pub struct TextVertex {`
- `struct` **`TextMesh`** — `pub struct TextMesh {`
