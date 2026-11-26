# euv-performance full pub API

Source: `performance/src/` at `origin/master` (`aac1c450d6e8317c50c01dd6225dea7a29265495`, version 0.39.1),
extracted from `pub` declarations.

`performance` is a workspace member but is **excluded from the published
package** (the root `exclude` list names it), and it is built as its own
manifest (`--manifest-path performance/Cargo.toml`) in CI. Its suite covers
reactivity, the layout cache, both rasterizers, the glyph atlas, the game
ECS/physics/particles paths, the 3D PBR/BVH path and the stress scenarios
(100k list, 2000-node layout, 1000 bulk signals, wasm hot-swap, 4x HiDPI).

### crate root
- (lib) pub use suite::*;

### suite
- (const) pub const BENCH_FLAG_JSON: &str = "--json";
- (fn) pub fn bench_reactive_signals_and_memos(iterations: usize) -> BenchMetric {
- (fn) pub fn bench_selector_o1(iterations: usize) -> BenchMetric {
- (fn) pub fn bench_layout_cache(iterations: usize) -> BenchMetric {
- (fn) pub fn bench_software_rasterizer(iterations: usize) -> BenchMetric {
- (fn) pub fn bench_hardware_gpu_batching(iterations: usize) -> BenchMetric {
- (fn) pub fn bench_unicode_glyph_atlas(iterations: usize) -> BenchMetric {
- (fn) pub fn bench_software_full_redraw(iterations: usize) -> BenchMetric {
- (fn) pub fn bench_game_ecs_physics(iterations: usize) -> BenchMetric {
- (fn) pub fn bench_game_particles(iterations: usize) -> BenchMetric {
- (fn) pub fn bench_game3d_pbr_bvh_raytrace(iterations: usize) -> BenchMetric {
- (fn) pub fn bench_game3d_cinematic_max_rt(iterations: usize) -> BenchMetric {
- (fn) pub fn bench_stress_long_list_100k(iterations: usize) -> BenchMetric {
- (fn) pub fn bench_stress_complex_layout_2000(iterations: usize) -> BenchMetric {
- (fn) pub fn bench_stress_bulk_reactive_1000(iterations: usize) -> BenchMetric {
- (fn) pub fn bench_stress_wasm_dynamic_hotswap(iterations: usize) -> BenchMetric {
- (fn) pub fn bench_stress_hidpi_4x_1440x3168(iterations: usize) -> BenchMetric {
- (fn) pub fn bench_stress_scroll_physics_and_hittest(iterations: usize) -> BenchMetric {
- (fn) pub fn run_full_benchmark_suite() -> BenchReport {
- (fn) pub fn format_bench_report(report: &BenchReport) -> String {
- (fn) pub fn report_to_json(report: &BenchReport) -> String {
- (mod) pub use {r#const::*, r#fn::*, r#struct::*};
- (struct) pub struct BenchMetric {
- (struct) pub struct BenchReport {

