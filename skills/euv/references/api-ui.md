# euv-ui full pub API (components + hooks + style)

Source: `ui/src/` — auto-extracted from `pub` declarations.

Re-exported at the crate root as `euv::euv_button`, `euv::use_async`, etc. via `ui/src/lib.rs` `pub use {component::*, hook::*, style::*}`.

### `dom::fn`

- `fn` **`after_mount`** — `pub(crate) fn after_mount<F>(callback: F) where F: FnOnce() + 'static, {...}`
- `fn` **`schedule_after`** — `pub(crate) fn schedule_after<F>(delay_ms: u32, callback: F) where F: FnOnce() + 'static, {...}`
- `fn` **`browser_window`** — `pub(crate) fn browser_window() -> Option<Window> {...}`
- `fn` **`browser_document`** — `pub(crate) fn browser_document() -> Option<Document> {...}`
- `fn` **`node_contains`** — `pub(crate) fn node_contains(container: &Node, candidate: &Node) -> bool {...}`

### `dom::type`

- `type` **`Teardown`** — `pub(crate) type Teardown = Rc<RefCell<Option<Box<dyn Fn()>>>>;`

### `hook::counter::impl`

- `fn` **`increment`** — `pub fn increment(&self) {...}`
- `fn` **`decrement`** — `pub fn decrement(&self) {...}`
- `fn` **`set`** — `pub fn set(&self, next: i32) {...}`
- `fn` **`set_unchecked`** — `pub fn set_unchecked(&self, next: i32) {...}`
- `fn` **`is_at_max`** — `pub fn is_at_max(&self) -> bool {...}`
- `fn` **`is_at_min`** — `pub fn is_at_min(&self) -> bool {...}`
- `fn` **`get`** — `pub fn get(&self) -> i32 {...}`

### `hook::counter::struct`

- `struct` **`Counter`** — `pub struct Counter {`

### `hook::debounced_value::enum`

- `enum` **`DebounceState`** — `pub(crate) enum DebounceState<T> {`

### `hook::debounced_value::fn`

- `fn` **`use_debounced_value`** — `pub fn use_debounced_value<T>(delay_ms: u32) -> DebouncedValue<T> where T: Clone + PartialEq + Debug + Default + 'static, {...}`

### `hook::debounced_value::impl`

- `fn` **`set`** — `pub fn set(&self, next: T, now_ms: u64) {...}`
- `fn` **`tick`** — `pub fn tick(&self, now_ms: u64) -> bool {...}`
- `fn` **`cancel`** — `pub fn cancel(&self) {...}`
- `fn` **`get`** — `pub fn get(&self) -> T {...}`
- `fn` **`is_pending`** — `pub fn is_pending(&self) -> bool {...}`

### `hook::debounced_value::struct`

- `struct` **`DebouncedValue`** — `pub struct DebouncedValue<T: Clone + PartialEq + Default + 'static> {`

### `hook::error_boundary::enum`

- `enum` **`ErrorBoundaryPhase`** — `pub enum ErrorBoundaryPhase {`

### `hook::error_boundary::fn`

- `fn` **`extract_message`** — `pub(crate) fn extract_message(payload: &Box<dyn Any + Send>) -> String {...}`
- `fn` **`use_error_boundary`** — `pub fn use_error_boundary() -> ErrorBoundary {...}`

### `hook::error_boundary::impl`

- `fn` **`new`** — `pub fn new() -> Self {...}`
- `fn` **`try_with`** — `pub fn try_with<F, R>(&self, closure: F) -> Result<R, String> where F: FnOnce() -> R + UnwindSafe, {...}`
- `fn` **`report_error`** — `pub fn report_error(&self, message: &str) -> String {...}`
- `fn` **`reset`** — `pub fn reset(&self) {...}`

### `hook::error_boundary::struct`

- `struct` **`ErrorBoundary`** — `pub struct ErrorBoundary {`

### `hook::form::impl`

- `fn` **`field`** — `pub fn field(&self, name: &'static str) -> String {...}`
- `fn` **`error`** — `pub fn error(&self, name: &'static str) -> String {...}`
- `fn` **`is_touched`** — `pub fn is_touched(&self, name: &'static str) -> bool {...}`
- `fn` **`set_field`** — `pub fn set_field(&self, name: &'static str, value: &str) {...}`
- `fn` **`touch`** — `pub fn touch(&self, name: &'static str) {...}`
- `fn` **`validate`** — `pub fn validate(&self, validators: &HashMap<&'static str, Validator>) -> bool {...}`
- `fn` **`submit`** — `pub fn submit<F>(&self, validators: &HashMap<&'static str, Validator>, on_submit: F) -> bool where F: FnOnce(&HashMap<&'static str, String>), {...}`
- `fn` **`reset`** — `pub fn reset(&self) {...}`
- `fn` **`error_count`** — `pub fn error_count(&self) -> usize {...}`

### `hook::form::struct`

- `struct` **`FormState`** — `pub struct FormState {`

### `hook::form::trait`

- `trait` **`HookContextFormExt`** — `pub trait HookContextFormExt {`

### `hook::form::type`

- `type` **`Validator`** — `pub type Validator = Box<dyn Fn(&str) -> Option<String>>;`

### `hook::i18n::fn`

- `fn` **`interpolate`** — `pub(crate) fn interpolate(template: &str, vars: &HashMap<&'static str, &'static str>) -> String {...}`
- `fn` **`use_i18n`** — `pub fn use_i18n(init_locale: &str) -> I18n {...}`
- `fn` **`i18n_register`** — `pub fn i18n_register(handle: I18n, locale: &str, entries: &[(&'static str, &'static str)]) {...}`
- `fn` **`i18n_reset_for_tests`** — `pub fn i18n_reset_for_tests() {...}`
- `fn` **`messages_lock`** — `pub(crate) fn messages_lock() -> &'static RwLock<HashMap<String, HashMap<String, String>>> {...}`

### `hook::i18n::impl`

- `fn` **`change_locale`** — `pub fn change_locale(&self, locale: &str) {...}`
- `fn` **`change_fallback_locale`** — `pub fn change_fallback_locale(&self, locale: &str) {...}`
- `fn` **`add_messages`** — `pub fn add_messages(&self, locale: &str, entries: &[MessageEntry]) {...}`
- `fn` **`remove_locale`** — `pub fn remove_locale(&self, locale: &str) {...}`
- `fn` **`remove_message`** — `pub fn remove_message(&self, locale: &str, key: &str) {...}`
- `fn` **`t`** — `pub fn t(&self, key: &str) -> String {...}`
- `fn` **`t_with`** — `pub fn t_with(&self, key: &str, vars: &HashMap<&'static str, &'static str>) -> String {...}`
- `fn` **`locale_count`** — `pub fn locale_count(&self) -> usize {...}`
- `fn` **`active_message_count`** — `pub fn active_message_count(&self) -> usize {...}`

### `hook::i18n::struct`

- `static` **`I18N_MESSAGES`** — `pub(crate) static I18N_MESSAGES: OnceLock<RwLock<HashMap<String, HashMap<String, String>>>> = OnceLock::new();`
- `struct` **`I18n`** — `pub struct I18n {`

### `hook::i18n::trait`

- `trait` **`HookContextI18nExt`** — `pub trait HookContextI18nExt {`

### `hook::i18n::type`

- `type` **`MessageEntry`** — `pub type MessageEntry = (&'static str, &'static str);`

### `hook::lazy::enum`

- `enum` **`LoadState`** — `pub enum LoadState<T> {`

### `hook::lazy::fn`

- `fn` **`use_lazy_component`** — `pub fn use_lazy_component<T, F>(factory: F) -> LazyComponent<T> where T: Clone + PartialEq + Debug + 'static, F: Fn() -> T + 'static, {...}`

### `hook::lazy::impl`

- `fn` **`new`** — `pub fn new<F>(factory: F) -> Self where F: Fn() -> T + 'static, {...}`
- `fn` **`prefetch`** — `pub fn prefetch(&self) {...}`
- `fn` **`get`** — `pub fn get(&self) -> Option<T> {...}`
- `fn` **`loaded`** — `pub fn loaded(&self) -> Option<T> {...}`
- `fn` **`reset`** — `pub fn reset(&self) {...}`
- `fn` **`change_factory`** — `pub fn change_factory<F>(&self, factory: F) where F: Fn() -> T + 'static, {...}`

### `hook::lazy::struct`

- `struct` **`LazyComponent`** — `pub struct LazyComponent<T: Clone + PartialEq + 'static> {`

### `hook::previous::fn`

- `fn` **`use_previous`** — `pub fn use_previous<T>() -> Previous<T> where T: Clone + PartialEq + Debug + 'static, {...}`
- `fn` **`previous_step`** — `pub fn previous_step<T>(previous: Previous<T>, current: T) -> Option<T> where T: Clone + PartialEq + Debug + 'static, {...}`

### `hook::previous::impl`

- `fn` **`new`** — `pub fn new() -> Self {...}`
- `fn` **`record`** — `pub fn record(&self, current: T) {...}`
- `fn` **`get_previous_snapshot`** — `pub fn get_previous_snapshot(&self) -> Option<T> {...}`
- `fn` **`clear`** — `pub fn clear(&self) {...}`

### `hook::previous::struct`

- `struct` **`Previous`** — `pub struct Previous<T: Clone + PartialEq + 'static> {`

### `hook::profiler::fn`

- `fn` **`now_ms`** — `pub fn now_ms() -> f64 {...}`
- `fn` **`use_profiler`** — `pub fn use_profiler() -> ProfilerHandle {...}`
- `fn` **`profiler_measure`** — `pub fn profiler_measure<F, R>(label: &str, body: F) -> R where F: FnOnce() -> R, {...}`

### `hook::profiler::impl`

- `fn` **`new_with_empty_entries`** — `pub fn new_with_empty_entries() -> Self {...}`
- `fn` **`measure`** — `pub fn measure<F, R>(&self, label: &str, f: F) -> R where F: FnOnce() -> R, {...}`
- `fn` **`begin`** — `pub fn begin(&self, label: &str) -> ProfilerMark {...}`
- `fn` **`clear`** — `pub fn clear(&self) {...}`
- `fn` **`end`** — `pub fn end(self) {...}`

### `hook::profiler::struct`

- `struct` **`ProfileEntry`** — `pub struct ProfileEntry {`
- `struct` **`ProfilerHandle`** — `pub struct ProfilerHandle {`
- `struct` **`ProfilerMark`** — `pub struct ProfilerMark {`

### `hook::suspense::enum`

- `enum` **`SuspensePhase`** — `pub enum SuspensePhase<T> {`

### `hook::suspense::fn`

- `fn` **`use_suspense`** — `pub fn use_suspense<T>() -> SuspenseHandle<T> where T: Clone + PartialEq + Debug + 'static, {...}`

### `hook::suspense::impl`

- `fn` **`new`** — `pub fn new() -> Self {...}`
- `fn` **`resolve_sync`** — `pub fn resolve_sync(&self, value: T) {...}`
- `fn` **`fail`** — `pub fn fail(&self, message: String) {...}`
- `fn` **`reset`** — `pub fn reset(&self) {...}`

### `hook::suspense::struct`

- `struct` **`SuspenseHandle`** — `pub struct SuspenseHandle<T: Clone + PartialEq + 'static> {`

### `hook::throttled_value::enum`

- `enum` **`ThrottleState`** — `pub(crate) enum ThrottleState {`

### `hook::throttled_value::fn`

- `fn` **`use_throttled_value`** — `pub fn use_throttled_value<T>(interval_ms: u32) -> ThrottledValue<T> where T: Clone + PartialEq + Debug + Default + 'static, {...}`

### `hook::throttled_value::impl`

- `fn` **`set`** — `pub fn set(&self, next: T, now_ms: u64) {...}`
- `fn` **`tick`** — `pub fn tick(&self, now_ms: u64) -> bool {...}`
- `fn` **`cancel`** — `pub fn cancel(&self) {...}`
- `fn` **`get`** — `pub fn get(&self) -> T {...}`
- `fn` **`is_throttling`** — `pub fn is_throttling(&self) -> bool {...}`

### `hook::throttled_value::struct`

- `struct` **`ThrottledValue`** — `pub struct ThrottledValue<T: Clone + PartialEq + Default + 'static> {`

### `hook::toggle::impl`

- `fn` **`set_true`** — `pub fn set_true(&self) {...}`
- `fn` **`set_false`** — `pub fn set_false(&self) {...}`
- `fn` **`toggle`** — `pub fn toggle(&self) {...}`
- `fn` **`set`** — `pub fn set(&self, next: bool) {...}`
- `fn` **`get`** — `pub fn get(&self) -> bool {...}`

### `hook::toggle::struct`

- `struct` **`Toggle`** — `pub struct Toggle {`

### `hook::transition::enum`

- `enum` **`TransitionPhase`** — `pub enum TransitionPhase {`

### `hook::transition::impl`

- `fn` **`exited`** — `pub const fn exited() -> Self {...}`
- `fn` **`with_ms`** — `pub const fn with_ms(ms: u32) -> Self {...}`
- `fn` **`with_durations`** — `pub const fn with_durations(enter_ms: u32, exit_ms: u32) -> Self {...}`
- `fn` **`duration_for`** — `pub fn duration_for(&self, phase: TransitionPhase) -> u32 {...}`
- `fn` **`is_animating`** — `pub fn is_animating(&self) -> bool {...}`
- `fn` **`change_config`** — `pub fn change_config(&self, config: TransitionConfig) {...}`
- `fn` **`enter`** — `pub fn enter(&self) {...}`
- `fn` **`exit`** — `pub fn exit(&self) {...}`
- `fn` **`toggle`** — `pub fn toggle(&self) {...}`
- `fn` **`tick`** — `pub fn tick(&self, elapsed_ms: u32) {...}`
- `fn` **`tick_until_done`** — `pub fn tick_until_done(&self, step_ms: u32) {...}`
- `fn` **`reset`** — `pub fn reset(&self) {...}`
- `fn` **`remaining_ms`** — `pub fn remaining_ms(&self) -> u32 {...}`

### `hook::transition::struct`

- `struct` **`TransitionConfig`** — `pub struct TransitionConfig {`
- `struct` **`TransitionState`** — `pub struct TransitionState {`

### `hook::transition::trait`

- `trait` **`HookContextTransitionExt`** — `pub trait HookContextTransitionExt {`

### `hook::use_async::enum`

- `enum` **`AsyncState`** — `pub enum AsyncState<T, L = ()> {`

### `hook::use_async::fn`

- `fn` **`use_async`** — `pub fn use_async<T, L>() -> UseAsyncHandle<T, L> where T: Clone + PartialEq + 'static, L: Clone + PartialEq + HasLoadingHint + 'static, {...}`

### `hook::use_async::impl`

- `fn` **`new_for_fallback`** — `pub(crate) fn new_for_fallback() -> Self {...}`
- `fn` **`state`** — `pub fn state(&self) -> AsyncState<T, L> {...}`
- `fn` **`set_state`** — `pub fn set_state(&self, next: AsyncState<T, L>) {...}`
- `fn` **`refetch`** — `pub fn refetch<F, Fut, E>(&self, factory: F) where F: FnOnce() -> Fut + 'static, Fut: Future<Output = Result<T, E>> + 'static, E: Into<String> + 'static, {...}`

### `hook::use_async::struct`

- `struct` **`UseAsyncHandle`** — `pub struct UseAsyncHandle<T, L> where T: Clone + PartialEq + 'static, L: Clone + PartialEq + HasLoadingHint + 'static, {`
- `struct` **`UseAsyncSlot`** — `pub(crate) struct UseAsyncSlot<T, L> where T: Clone + PartialEq + 'static, L: Clone + PartialEq + HasLoadingHint + 'static, {`

### `hook::use_async::trait`

- `trait` **`HasLoadingHint`** — `pub trait HasLoadingHint: Clone + 'static {`

### `hook::use_async::type`

- `type` **`DefaultLoadingHandle`** — `pub type DefaultLoadingHandle<T> = UseAsyncHandle<T, ()>;`

### `hook::use_boolean::fn`

- `fn` **`use_boolean`** — `pub fn use_boolean(initial: bool) -> UseBoolean {...}`

### `hook::use_boolean::impl`

- `fn` **`set_true`** — `pub fn set_true(&self) {...}`
- `fn` **`set_false`** — `pub fn set_false(&self) {...}`
- `fn` **`toggle`** — `pub fn toggle(&self) {...}`
- `fn` **`set_value`** — `pub fn set_value(&self, next: bool) {...}`
- `fn` **`get`** — `pub fn get(&self) -> bool {...}`

### `hook::use_boolean::struct`

- `struct` **`UseBoolean`** — `pub struct UseBoolean {`

### `hook::use_click_outside::fn`

- `fn` **`use_click_outside`** — `pub fn use_click_outside() -> UseClickOutside {...}`
- `fn` **`press_is_outside`** — `pub(crate) fn press_is_outside(target: &NodeRef<Element>, event: &Event) -> bool {...}`

### `hook::use_click_outside::impl`

- `fn` **`new`** — `pub(crate) fn new() -> Self {...}`
- `fn` **`is_triggered`** — `pub fn is_triggered(&self) -> bool {...}`
- `fn` **`reset`** — `pub fn reset(&self) {...}`
- `fn` **`attach`** — `pub(crate) fn attach(&self) {...}`
- `fn` **`detach`** — `pub(crate) fn detach(&self) {...}`

### `hook::use_click_outside::struct`

- `struct` **`UseClickOutside`** — `pub struct UseClickOutside {`

### `hook::use_clipboard::enum`

- `enum` **`UseClipboardStatus`** — `pub enum UseClipboardStatus {`

### `hook::use_clipboard::fn`

- `fn` **`use_clipboard`** — `pub fn use_clipboard() -> UseClipboard {...}`

### `hook::use_clipboard::impl`

- `fn` **`new`** — `pub(crate) fn new() -> Self {...}`
- `fn` **`current_status`** — `pub fn current_status(&self) -> UseClipboardStatus {...}`
- `fn` **`copy`** — `pub fn copy(&self, text: &str) -> bool {...}`

### `hook::use_clipboard::struct`

- `struct` **`UseClipboard`** — `pub struct UseClipboard {`

### `hook::use_hover::fn`

- `fn` **`use_hover`** — `pub fn use_hover() -> UseHover {...}`
- `fn` **`pointer_is_inside`** — `pub(crate) fn pointer_is_inside(target: &NodeRef<Element>, event: &Event) -> bool {...}`

### `hook::use_hover::impl`

- `fn` **`new`** — `pub(crate) fn new() -> Self {...}`
- `fn` **`is_hovered`** — `pub fn is_hovered(&self) -> bool {...}`
- `fn` **`attach`** — `pub(crate) fn attach(&self) {...}`
- `fn` **`detach`** — `pub(crate) fn detach(&self) {...}`

### `hook::use_hover::struct`

- `struct` **`UseHover`** — `pub struct UseHover {`

### `hook::use_id::fn`

- `fn` **`use_id`** — `pub fn use_id(prefix: &'static str) -> UseId {...}`

### `hook::use_id::static`

- `static` **`ID_COUNTER`** — `pub(crate) static ID_COUNTER: AtomicUsize = AtomicUsize::new(0);`

### `hook::use_id::struct`

- `struct` **`UseId`** — `pub struct UseId {`

### `hook::use_intersection_observer::fn`

- `fn` **`use_intersection_observer`** — `pub fn use_intersection_observer() -> UseIntersectionObserver {...}`

### `hook::use_intersection_observer::impl`

- `fn` **`new`** — `pub(crate) fn new() -> Self {...}`
- `fn` **`is_visible`** — `pub fn is_visible(&self) -> bool {...}`
- `fn` **`current_ratio`** — `pub fn current_ratio(&self) -> f64 {...}`
- `fn` **`attach`** — `pub(crate) fn attach(&self) {...}`
- `fn` **`detach`** — `pub(crate) fn detach(&self) {...}`

### `hook::use_intersection_observer::struct`

- `struct` **`UseIntersectionObserver`** — `pub struct UseIntersectionObserver {`

### `hook::use_keyboard::fn`

- `fn` **`use_keyboard`** — `pub fn use_keyboard() -> UseKeyboard {...}`

### `hook::use_keyboard::impl`

- `fn` **`new`** — `pub(crate) fn new() -> Self {...}`
- `fn` **`current_key`** — `pub fn current_key(&self) -> String {...}`
- `fn` **`is_pressed`** — `pub fn is_pressed(&self, key: &str) -> bool {...}`
- `fn` **`attach`** — `pub(crate) fn attach(&self) {...}`
- `fn` **`detach`** — `pub(crate) fn detach(&self) {...}`

### `hook::use_keyboard::struct`

- `struct` **`UseKeyboard`** — `pub struct UseKeyboard {`

### `hook::use_media_query::fn`

- `fn` **`use_media_query`** — `pub fn use_media_query(query: &'static str) -> UseMediaQuery {...}`

### `hook::use_media_query::impl`

- `fn` **`new`** — `pub(crate) fn new(query: &'static str) -> Self {...}`
- `fn` **`is_matching`** — `pub fn is_matching(&self) -> bool {...}`
- `fn` **`attach`** — `pub(crate) fn attach(&self) {...}`
- `fn` **`detach`** — `pub(crate) fn detach(&self) {...}`

### `hook::use_media_query::struct`

- `struct` **`UseMediaQuery`** — `pub struct UseMediaQuery {`

### `hook::use_mounted::fn`

- `fn` **`use_mounted`** — `pub fn use_mounted() -> UseMounted {...}`

### `hook::use_mounted::impl`

- `fn` **`new`** — `pub(crate) fn new() -> Self {...}`
- `fn` **`is_mounted`** — `pub fn is_mounted(&self) -> bool {...}`
- `fn` **`attach`** — `pub(crate) fn attach(&self) {...}`

### `hook::use_mounted::struct`

- `struct` **`UseMounted`** — `pub struct UseMounted {`

### `hook::use_online_status::fn`

- `fn` **`use_online_status`** — `pub fn use_online_status() -> UseOnlineStatus {...}`

### `hook::use_online_status::impl`

- `fn` **`new`** — `pub(crate) fn new() -> Self {...}`
- `fn` **`is_online`** — `pub fn is_online(&self) -> bool {...}`
- `fn` **`attach`** — `pub(crate) fn attach(&self) {...}`
- `fn` **`detach`** — `pub(crate) fn detach(&self) {...}`

### `hook::use_online_status::struct`

- `struct` **`UseOnlineStatus`** — `pub struct UseOnlineStatus {`

### `hook::use_reduced_motion::fn`

- `fn` **`use_reduced_motion`** — `pub fn use_reduced_motion() -> UseReducedMotion {...}`

### `hook::use_reduced_motion::impl`

- `fn` **`new`** — `pub(crate) fn new() -> Self {...}`
- `fn` **`is_reduced`** — `pub fn is_reduced(&self) -> bool {...}`
- `fn` **`attach`** — `pub(crate) fn attach(&self) {...}`
- `fn` **`detach`** — `pub(crate) fn detach(&self) {...}`

### `hook::use_reduced_motion::struct`

- `struct` **`UseReducedMotion`** — `pub struct UseReducedMotion {`

### `hook::use_resize_observer::fn`

- `fn` **`use_resize_observer`** — `pub fn use_resize_observer() -> UseResizeObserver {...}`

### `hook::use_resize_observer::impl`

- `fn` **`new`** — `pub(crate) fn new() -> Self {...}`
- `fn` **`current_width`** — `pub fn current_width(&self) -> f64 {...}`
- `fn` **`current_height`** — `pub fn current_height(&self) -> f64 {...}`
- `fn` **`attach`** — `pub(crate) fn attach(&self) {...}`
- `fn` **`detach`** — `pub(crate) fn detach(&self) {...}`

### `hook::use_resize_observer::struct`

- `struct` **`UseResizeObserver`** — `pub struct UseResizeObserver {`

### `hook::use_scroll::fn`

- `fn` **`use_scroll`** — `pub fn use_scroll() -> UseScroll {...}`

### `hook::use_scroll::impl`

- `fn` **`new`** — `pub(crate) fn new() -> Self {...}`
- `fn` **`current_y`** — `pub fn current_y(&self) -> f64 {...}`
- `fn` **`current_x`** — `pub fn current_x(&self) -> f64 {...}`
- `fn` **`scroll_to_top`** — `pub fn scroll_to_top(&self) {...}`
- `fn` **`attach`** — `pub(crate) fn attach(&self) {...}`
- `fn` **`detach`** — `pub(crate) fn detach(&self) {...}`

### `hook::use_scroll::struct`

- `struct` **`UseScroll`** — `pub struct UseScroll {`

### `hook::use_storage::enum`

- `enum` **`UseStorageKind`** — `pub enum UseStorageKind {`

### `hook::use_storage::fn`

- `fn` **`use_storage`** — `pub fn use_storage(key: &'static str, kind: UseStorageKind, initial: &str) -> UseStorage {...}`
- `fn` **`read_storage`** — `pub(crate) fn read_storage(kind: UseStorageKind, key: &str) -> Option<String> {...}`
- `fn` **`write_storage`** — `pub(crate) fn write_storage(kind: UseStorageKind, key: &str, value: &str) {...}`
- `fn` **`remove_storage`** — `pub(crate) fn remove_storage(kind: UseStorageKind, key: &str) {...}`

### `hook::use_storage::impl`

- `fn` **`new`** — `pub(crate) fn new(key: &'static str, kind: UseStorageKind, initial: &str) -> Self {...}`
- `fn` **`current`** — `pub fn current(&self) -> String {...}`
- `fn` **`set_value`** — `pub fn set_value(&self, value: &str) {...}`
- `fn` **`clear`** — `pub fn clear(&self) {...}`

### `hook::use_storage::struct`

- `struct` **`UseStorage`** — `pub struct UseStorage {`

### `hook::use_timer::fn`

- `fn` **`use_timer`** — `pub fn use_timer(interval_ms: u32) -> UseTimer {...}`
- `fn` **`use_timeout`** — `pub fn use_timeout<F>(delay_ms: u32, callback: F) where F: FnOnce() + 'static, {...}`

### `hook::use_timer::impl`

- `fn` **`new`** — `pub(crate) fn new(interval_ms: u32) -> Self {...}`
- `fn` **`current_ticks`** — `pub fn current_ticks(&self) -> u64 {...}`
- `fn` **`reset`** — `pub fn reset(&self) {...}`

### `hook::use_timer::struct`

- `struct` **`UseTimer`** — `pub struct UseTimer {`

### `hook::use_window_size::fn`

- `fn` **`use_window_size`** — `pub fn use_window_size() -> UseWindowSize {...}`
- `fn` **`read_dimension`** — `pub(crate) fn read_dimension(window: &Window, width: bool) -> i32 {...}`

### `hook::use_window_size::impl`

- `fn` **`new`** — `pub(crate) fn new() -> Self {...}`
- `fn` **`current_width`** — `pub fn current_width(&self) -> i32 {...}`
- `fn` **`current_height`** — `pub fn current_height(&self) -> i32 {...}`
- `fn` **`attach`** — `pub(crate) fn attach(&self) {...}`
- `fn` **`detach`** — `pub(crate) fn detach(&self) {...}`

### `hook::use_window_size::struct`

- `struct` **`UseWindowSize`** — `pub struct UseWindowSize {`

### `style::css::fn`

- `fn` **`inject_app_global_css`** — `pub fn inject_app_global_css() {...}`
- `fn` **`euv_md_css`** — `pub fn euv_md_css() -> &'static str {...}`

### `component::affix::view::fn`

- `fn` **`euv_affix`** — `pub fn euv_affix(node: VirtualNode<EuvAffixProps>) -> VirtualNode {...}`

### `component::affix::view::struct`

- `struct` **`EuvAffixProps`** — `pub struct EuvAffixProps {`

### `component::alert::view::enum`

- `enum` **`AlertVariant`** — `pub enum AlertVariant {`

### `component::alert::view::fn`

- `fn` **`euv_alert`** — `pub fn euv_alert(node: VirtualNode<EuvAlertProps>) -> VirtualNode {...}`

### `component::alert::view::struct`

- `struct` **`EuvAlertProps`** — `pub struct EuvAlertProps {`

### `component::anchor::view::fn`

- `fn` **`euv_anchor`** — `pub fn euv_anchor(node: VirtualNode<EuvAnchorProps>) -> VirtualNode {...}`

### `component::anchor::view::struct`

- `struct` **`EuvAnchorItem`** — `pub struct EuvAnchorItem {`
- `struct` **`EuvAnchorProps`** — `pub struct EuvAnchorProps {`

### `component::auto_complete::view::fn`

- `fn` **`auto_complete_matches`** — `pub fn auto_complete_matches(option: &EuvAutoCompleteOption, query: &str) -> bool {...}`
- `fn` **`auto_complete_active`** — `pub fn auto_complete_active<'a>( filtered: &'a [EuvAutoCompleteOption], query: &str, ) -> Option<&'a EuvAutoCompleteOption> {...}`
- `fn` **`euv_auto_complete`** — `pub fn euv_auto_complete(node: VirtualNode<EuvAutoCompleteProps>) -> VirtualNode {...}`

### `component::auto_complete::view::struct`

- `struct` **`EuvAutoCompleteOption`** — `pub struct EuvAutoCompleteOption {`
- `struct` **`EuvAutoCompleteProps`** — `pub struct EuvAutoCompleteProps {`

### `component::avatar::view::enum`

- `enum` **`EuvAvatarSize`** — `pub enum EuvAvatarSize {`

### `component::avatar::view::fn`

- `fn` **`euv_avatar`** — `pub fn euv_avatar(node: VirtualNode<EuvAvatarProps>) -> VirtualNode {...}`

### `component::avatar::view::impl`

- `fn` **`px`** — `pub fn px(&self) -> i32 {...}`

### `component::avatar::view::struct`

- `struct` **`EuvAvatarProps`** — `pub struct EuvAvatarProps {`

### `component::back_top::view::fn`

- `fn` **`euv_back_top`** — `pub fn euv_back_top(node: VirtualNode<EuvBackTopProps>) -> VirtualNode {...}`

### `component::back_top::view::struct`

- `struct` **`EuvBackTopProps`** — `pub struct EuvBackTopProps {`

### `component::badge::view::fn`

- `fn` **`euv_badge`** — `pub fn euv_badge(node: VirtualNode<EuvBadgeProps>) -> VirtualNode {...}`

### `component::badge::view::struct`

- `struct` **`EuvBadgeProps`** — `pub struct EuvBadgeProps {`

### `component::breadcrumb::view::fn`

- `fn` **`euv_breadcrumb`** — `pub fn euv_breadcrumb(node: VirtualNode<EuvBreadcrumbProps>) -> VirtualNode {...}`

### `component::breadcrumb::view::struct`

- `struct` **`EuvBreadcrumbItem`** — `pub struct EuvBreadcrumbItem {`
- `struct` **`EuvBreadcrumbProps`** — `pub struct EuvBreadcrumbProps {`

### `component::browser::hook::impl`

- `fn` **`use_browser_state`** — `pub fn use_browser_state() -> UseEuvBrowser {...}`
- `fn` **`local_storage_get`** — `pub fn local_storage_get<K>(key: K) -> Option<String> where K: AsRef<str>, {...}`
- `fn` **`local_storage_set`** — `pub fn local_storage_set<K, V>(key: K, value: V) where K: AsRef<str>, V: AsRef<str>, {...}`
- `fn` **`local_storage_remove`** — `pub(crate) fn local_storage_remove<K>(key: K) where K: AsRef<str>, {...}`
- `fn` **`session_storage_get`** — `pub(crate) fn session_storage_get<K>(key: K) -> Option<String> where K: AsRef<str>, {...}`
- `fn` **`session_storage_set`** — `pub(crate) fn session_storage_set<K, V>(key: K, value: V) where K: AsRef<str>, V: AsRef<str>, {...}`
- `fn` **`session_storage_remove`** — `pub(crate) fn session_storage_remove<K>(key: K) where K: AsRef<str>, {...}`
- `fn` **`clipboard_read_text`** — `pub(crate) async fn clipboard_read_text() -> String {...}`
- `fn` **`clipboard_write_text`** — `pub(crate) async fn clipboard_write_text<T>(text: T) -> bool where T: AsRef<str>, {...}`
- `fn` **`window_inner_size`** — `pub(crate) fn window_inner_size() -> (i32, i32) {...}`
- `fn` **`navigator_user_agent`** — `pub(crate) fn navigator_user_agent() -> String {...}`
- `fn` **`navigator_language`** — `pub(crate) fn navigator_language() -> String {...}`
- `fn` **`location_href`** — `pub(crate) fn location_href() -> String {...}`
- `fn` **`location_origin`** — `pub(crate) fn location_origin() -> String {...}`
- `fn` **`location_pathname`** — `pub(crate) fn location_pathname() -> String {...}`
- `fn` **`on_local_storage_set`** — `pub fn on_local_storage_set(self) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`on_local_storage_get`** — `pub fn on_local_storage_get(self) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`on_local_storage_remove`** — `pub fn on_local_storage_remove(self) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`on_session_storage_set`** — `pub fn on_session_storage_set(self) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`on_session_storage_get`** — `pub fn on_session_storage_get(self) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`on_session_storage_remove`** — `pub fn on_session_storage_remove(self) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`on_clipboard_copy`** — `pub fn on_clipboard_copy(self) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`on_clipboard_paste`** — `pub fn on_clipboard_paste(self) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`on_window_refresh_size`** — `pub fn on_window_refresh_size(self) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`on_console_log`** — `pub fn on_console_log(console_input: Signal<String>) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`on_console_warn`** — `pub fn on_console_warn(console_input: Signal<String>) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`on_console_error`** — `pub fn on_console_error(console_input: Signal<String>) -> Option<Rc<dyn Fn(Event)>> {...}`

### `component::browser::hook::struct`

- `struct` **`UseEuvBrowser`** — `pub struct UseEuvBrowser {`

### `component::button::view::enum`

- `enum` **`EuvButtonVariant`** — `pub enum EuvButtonVariant {`

### `component::button::view::fn`

- `fn` **`euv_button`** — `pub fn euv_button(node: VirtualNode<EuvButtonProps>) -> VirtualNode {...}`

### `component::button::view::struct`

- `struct` **`EuvButtonProps`** — `pub struct EuvButtonProps {`

### `component::calendar::view::enum`

- `enum` **`EuvCalendarWeekday`** — `pub enum EuvCalendarWeekday {`

### `component::calendar::view::fn`

- `fn` **`euv_calendar`** — `pub fn euv_calendar(node: VirtualNode<EuvCalendarProps>) -> VirtualNode {...}`
- `fn` **`on_calendar_day_click`** — `pub fn on_calendar_day_click(selected: Signal<u32>, day: u32) -> Option<Rc<dyn Fn(Event)>> {...}`

### `component::calendar::view::struct`

- `struct` **`EuvCalendarDay`** — `pub struct EuvCalendarDay {`
- `struct` **`EuvCalendarProps`** — `pub struct EuvCalendarProps {`

### `component::camera::hook::enum`

- `enum` **`EuvCameraFacing`** — `pub enum EuvCameraFacing {`

### `component::camera::hook::impl`

- `fn` **`use_camera_state`** — `pub fn use_camera_state() -> UseEuvCamera {...}`
- `fn` **`open`** — `pub(crate) fn open(video_selector: &str, facing: EuvCameraFacing) -> Result<(), String> {...}`
- `fn` **`close`** — `pub(crate) fn close(video_selector: &str) {...}`
- `fn` **`open_and_scan`** — `pub(crate) fn open_and_scan(self, config: Option<&EuvCameraConfig>) {...}`
- `fn` **`switch`** — `pub(crate) fn switch(self, config: Option<&EuvCameraConfig>) {...}`
- `fn` **`start_qr_scan`** — `pub(crate) fn start_qr_scan(self, config: Option<&EuvCameraConfig>) {...}`
- `fn` **`stop_qr_scan`** — `pub(crate) fn stop_qr_scan(self) {...}`
- `fn` **`is_valid_qr_url`** — `pub(crate) fn is_valid_qr_url(text: &str) -> bool {...}`
- `fn` **`extract_hostname`** — `pub(crate) fn extract_hostname(url: &str) -> String {...}`
- `fn` **`is_private_host`** — `pub(crate) fn is_private_host(hostname: &str) -> bool {...}`
- `fn` **`navigate_qr_url`** — `pub(crate) fn navigate_qr_url(url: &str) {...}`
- `fn` **`on_close`** — `pub fn on_close(self, config: Option<&EuvCameraConfig>) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`on_switch`** — `pub fn on_switch(self, config: Option<&EuvCameraConfig>) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`on_open`** — `pub fn on_open(self, config: Option<&EuvCameraConfig>) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`cleanup`** — `pub fn cleanup(self, config: Option<&EuvCameraConfig>) {...}`

### `component::camera::hook::struct`

- `struct` **`UseEuvCamera`** — `pub struct UseEuvCamera {`
- `struct` **`EuvCameraConfig`** — `pub struct EuvCameraConfig {`

### `component::camera::hook::type`

- `type` **`QrDetectedCallback`** — `pub type QrDetectedCallback = Rc<dyn Fn(&str)>;`
- `type` **`CameraErrorCallback`** — `pub type CameraErrorCallback = Rc<dyn Fn(String)>;`

### `component::card::view::fn`

- `fn` **`euv_card`** — `pub fn euv_card(node: VirtualNode<EuvCardProps>) -> VirtualNode {...}`

### `component::card::view::struct`

- `struct` **`EuvCardProps`** — `pub struct EuvCardProps {`

### `component::carousel::view::fn`

- `fn` **`euv_carousel`** — `pub fn euv_carousel(node: VirtualNode<EuvCarouselProps>) -> VirtualNode {...}`

### `component::carousel::view::struct`

- `struct` **`EuvCarouselSlide`** — `pub struct EuvCarouselSlide {`
- `struct` **`EuvCarouselProps`** — `pub struct EuvCarouselProps {`

### `component::cascader::view::fn`

- `fn` **`euv_cascader`** — `pub fn euv_cascader(node: VirtualNode<EuvCascaderProps>) -> VirtualNode {...}`
- `fn` **`cascader_path_labels`** — `pub fn cascader_path_labels(options: &[EuvCascaderOption], path: &[String]) -> Vec<&'static str> {...}`
- `fn` **`cascader_columns`** — `pub fn cascader_columns<'a>( options: &'a [EuvCascaderOption], path: &[String], ) -> Vec<&'a [EuvCascaderOption]> {...}`
- `fn` **`cascader_option_handler`** — `pub fn cascader_option_handler<E: 'static>( value: Signal<Vec<String>>, browsed: Signal<Vec<String>>, open: Signal<bool>, on_select: Option<Rc<dyn Fn(&'static str)>>, option_value: &'static str, depth: usize, has_children: bool, ) -> Option<Rc<dyn Fn(E)>> {...}`
- `fn` **`cascader_trigger_handler`** — `pub fn cascader_trigger_handler<E: 'static>( open: Signal<bool>, browsed: Signal<Vec<String>>, value: Signal<Vec<String>>, ) -> Option<Rc<dyn Fn(E)>> {...}`

### `component::cascader::view::struct`

- `struct` **`EuvCascaderOption`** — `pub struct EuvCascaderOption {`
- `struct` **`EuvCascaderProps`** — `pub struct EuvCascaderProps {`

### `component::checkbox::view::fn`

- `fn` **`euv_checkbox`** — `pub fn euv_checkbox(node: VirtualNode<EuvCheckboxProps>) -> VirtualNode {...}`

### `component::checkbox::view::struct`

- `struct` **`EuvCheckboxProps`** — `pub struct EuvCheckboxProps {`

### `component::checkbox_group::view::fn`

- `fn` **`euv_checkbox_group`** — `pub fn euv_checkbox_group(node: VirtualNode<EuvCheckboxGroupProps>) -> VirtualNode {...}`

### `component::checkbox_group::view::struct`

- `struct` **`EuvCheckboxGroupOption`** — `pub struct EuvCheckboxGroupOption {`
- `struct` **`EuvCheckboxGroupProps`** — `pub struct EuvCheckboxGroupProps {`

### `component::collapse::view::fn`

- `fn` **`euv_collapse`** — `pub fn euv_collapse(node: VirtualNode<EuvCollapseProps>) -> VirtualNode {...}`

### `component::collapse::view::struct`

- `struct` **`EuvCollapseItem`** — `pub struct EuvCollapseItem {`
- `struct` **`EuvCollapseProps`** — `pub struct EuvCollapseProps {`

### `component::date_picker::view::fn`

- `fn` **`days_from_civil`** — `pub fn days_from_civil(year: i64, month: u32, day: u32) -> i64 {...}`
- `fn` **`civil_from_days`** — `pub fn civil_from_days(days: i64) -> (i64, u32, u32) {...}`
- `fn` **`weekday_index`** — `pub fn weekday_index(year: i64, month: u32, day: u32) -> u32 {...}`
- `fn` **`is_leap_year`** — `pub fn is_leap_year(year: i64) -> bool {...}`
- `fn` **`days_in_month`** — `pub fn days_in_month(year: i64, month: u32) -> u32 {...}`
- `fn` **`adjacent_month`** — `pub fn adjacent_month(year: i64, month: u32, delta: i64) -> (i64, u32) {...}`
- `fn` **`encode_month`** — `pub fn encode_month(year: i64, month: u32) -> i64 {...}`
- `fn` **`decode_month`** — `pub fn decode_month(code: i64) -> (i64, u32) {...}`
- `fn` **`format_date`** — `pub fn format_date(year: i64, month: u32, day: u32) -> String {...}`
- `fn` **`parse_date`** — `pub fn parse_date(text: &str) -> Option<(i64, u32, u32)> {...}`
- `fn` **`date_within_bounds`** — `pub fn date_within_bounds(date: (i64, u32, u32), min: &str, max: &str) -> bool {...}`
- `fn` **`month_grid`** — `pub fn month_grid(year: i64, month: u32, today: (i64, u32, u32)) -> Vec<EuvCalendarDay> {...}`
- `fn` **`resolve_clicked_date`** — `pub fn resolve_clicked_date( year: i64, month: u32, day: u32, muted: bool, ) -> Option<(i64, u32, u32)> {...}`
- `fn` **`euv_date_picker`** — `pub fn euv_date_picker(node: VirtualNode<EuvDatePickerProps>) -> VirtualNode {...}`

### `component::date_picker::view::impl`

- `fn` **`caption`** — `pub(crate) fn caption(&self, year: i64, month: u32) -> &'static str {...}`

### `component::date_picker::view::struct`

- `struct` **`EuvDatePickerProps`** — `pub struct EuvDatePickerProps {`
- `struct` **`MonthCaption`** — `pub(crate) struct MonthCaption {`

### `component::date_picker::view::type`

- `type` **`CachedCaption`** — `pub(crate) type CachedCaption = Rc<RefCell<Option<(i64, u32, &'static str)>>>;`

### `component::debug::view::fn`

- `fn` **`euv_debug`** — `pub fn euv_debug(node: VirtualNode<EuvDebugProps>) -> VirtualNode {...}`

### `component::debug::view::struct`

- `struct` **`EuvDebugProps`** — `pub struct EuvDebugProps {`

### `component::debug::view::type`

- `type` **`DebugValueFormatter`** — `pub type DebugValueFormatter = Rc<dyn Fn() -> String>;`

### `component::descriptions::view::fn`

- `fn` **`euv_descriptions`** — `pub fn euv_descriptions(node: VirtualNode<EuvDescriptionsProps>) -> VirtualNode {...}`

### `component::descriptions::view::struct`

- `struct` **`EuvDescriptionsItem`** — `pub struct EuvDescriptionsItem {`
- `struct` **`EuvDescriptionsProps`** — `pub struct EuvDescriptionsProps {`

### `component::divider::view::enum`

- `enum` **`EuvDividerOrientation`** — `pub enum EuvDividerOrientation {`

### `component::divider::view::fn`

- `fn` **`euv_divider`** — `pub fn euv_divider(node: VirtualNode<EuvDividerProps>) -> VirtualNode {...}`

### `component::divider::view::struct`

- `struct` **`EuvDividerProps`** — `pub struct EuvDividerProps {`

### `component::doc_layout::view::fn`

- `fn` **`euv_doc_layout`** — `pub fn euv_doc_layout(node: VirtualNode<EuvDocLayoutProps>) -> VirtualNode {...}`

### `component::doc_layout::view::struct`

- `struct` **`EuvDocLayoutProps`** — `pub struct EuvDocLayoutProps {`

### `component::drawer::view::fn`

- `fn` **`euv_drawer`** — `pub fn euv_drawer(node: VirtualNode<EuvDrawerProps>) -> VirtualNode {...}`

### `component::drawer::view::struct`

- `struct` **`EuvDrawerProps`** — `pub struct EuvDrawerProps {`

### `component::dropdown::view::fn`

- `fn` **`euv_dropdown`** — `pub fn euv_dropdown(node: VirtualNode<EuvDropdownProps>) -> VirtualNode {...}`

### `component::dropdown::view::struct`

- `struct` **`EuvDropdownItem`** — `pub struct EuvDropdownItem {`
- `struct` **`EuvDropdownProps`** — `pub struct EuvDropdownProps {`

### `component::empty::view::fn`

- `fn` **`euv_empty`** — `pub fn euv_empty(node: VirtualNode<EuvEmptyProps>) -> VirtualNode {...}`

### `component::empty::view::struct`

- `struct` **`EuvEmptyProps`** — `pub struct EuvEmptyProps {`

### `component::feature_grid::view::fn`

- `fn` **`euv_feature_grid`** — `pub fn euv_feature_grid(node: VirtualNode<EuvFeatureGridProps>) -> VirtualNode {...}`

### `component::feature_grid::view::struct`

- `struct` **`EuvFeature`** — `pub struct EuvFeature {`
- `struct` **`EuvFeatureGridProps`** — `pub struct EuvFeatureGridProps {`

### `component::field::view::fn`

- `fn` **`euv_field`** — `pub fn euv_field(node: VirtualNode<EuvFieldProps>) -> VirtualNode {...}`

### `component::field::view::struct`

- `struct` **`EuvFieldProps`** — `pub struct EuvFieldProps {`

### `component::footer::view::fn`

- `fn` **`euv_footer`** — `pub fn euv_footer(node: VirtualNode<EuvFooterProps>) -> VirtualNode {...}`

### `component::footer::view::struct`

- `struct` **`EuvFooterItem`** — `pub struct EuvFooterItem {`
- `struct` **`EuvFooterProps`** — `pub struct EuvFooterProps {`

### `component::form::view::fn`

- `fn` **`euv_form`** — `pub fn euv_form(node: VirtualNode<EuvFormProps>) -> VirtualNode {...}`

### `component::form::view::struct`

- `struct` **`EuvFormProps`** — `pub struct EuvFormProps {`

### `component::grid::view::fn`

- `fn` **`euv_grid`** — `pub fn euv_grid(node: VirtualNode<EuvGridProps>) -> VirtualNode {...}`

### `component::grid::view::struct`

- `struct` **`EuvGridCol`** — `pub struct EuvGridCol {`
- `struct` **`EuvGridProps`** — `pub struct EuvGridProps {`

### `component::header::view::fn`

- `fn` **`euv_header`** — `pub fn euv_header(node: VirtualNode<EuvHeaderProps>) -> VirtualNode {...}`

### `component::header::view::struct`

- `struct` **`EuvHeaderProps`** — `pub struct EuvHeaderProps {`

### `component::hero::view::fn`

- `fn` **`euv_hero`** — `pub fn euv_hero(node: VirtualNode<EuvHeroProps>) -> VirtualNode {...}`
- `fn` **`euv_hero_action`** — `pub fn euv_hero_action(node: VirtualNode<EuvHeroActionProps>) -> VirtualNode {...}`

### `component::hero::view::struct`

- `struct` **`EuvHeroAction`** — `pub struct EuvHeroAction {`
- `struct` **`EuvHeroProps`** — `pub struct EuvHeroProps {`
- `struct` **`EuvHeroActionProps`** — `pub struct EuvHeroActionProps {`

### `component::icon::view::enum`

- `enum` **`EuvIconSize`** — `pub enum EuvIconSize {`

### `component::icon::view::fn`

- `fn` **`euv_icon`** — `pub fn euv_icon(node: VirtualNode<EuvIconProps>) -> VirtualNode {...}`

### `component::icon::view::impl`

- `fn` **`px`** — `pub fn px(&self) -> i32 {...}`

### `component::icon::view::struct`

- `struct` **`EuvIconProps`** — `pub struct EuvIconProps {`

### `component::image::view::enum`

- `enum` **`EuvImageStatus`** — `pub enum EuvImageStatus {`

### `component::image::view::fn`

- `fn` **`euv_image`** — `pub fn euv_image(node: VirtualNode<EuvImageProps>) -> VirtualNode {...}`

### `component::image::view::struct`

- `struct` **`EuvImageProps`** — `pub struct EuvImageProps {`

### `component::info::view::fn`

- `fn` **`euv_info`** — `pub fn euv_info(node: VirtualNode<EuvInfoProps>) -> VirtualNode {...}`

### `component::info::view::struct`

- `struct` **`EuvInfoProps`** — `pub struct EuvInfoProps {`

### `component::input::hook::impl`

- `fn` **`use_toggle`** — `pub fn use_toggle(signal: Signal<bool>) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`on_input_value`** — `pub fn on_input_value(signal: Signal<String>) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`on_change_value`** — `pub fn on_change_value(signal: Signal<String>) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`on_change_checked`** — `pub fn on_change_checked(signal: Signal<bool>) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`on_focus_scroll_into_view`** — `pub fn on_focus_scroll_into_view() -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`on_blur_restore_height`** — `pub fn on_blur_restore_height() -> Option<Rc<dyn Fn(Event)>> {...}`

### `component::input::hook::struct`

- `struct` **`UseEuvInput`** — `pub struct UseEuvInput;`

### `component::input::view::fn`

- `fn` **`euv_input`** — `pub fn euv_input(node: VirtualNode<EuvInputProps>) -> VirtualNode {...}`

### `component::input::view::struct`

- `struct` **`EuvInputProps`** — `pub struct EuvInputProps {`

### `component::layout::hook::fn`

- `fn` **`is_edge_to_edge_viewport`** — `pub fn is_edge_to_edge_viewport(declared_immersive: bool, viewport_gap: Option<f64>) -> bool {...}`
- `fn` **`safe_area_contract_value`** — `pub fn safe_area_contract_value(is_trusted: bool, measured: &str) -> String {...}`
- `fn` **`measure_viewport_screen_gap`** — `pub(crate) fn measure_viewport_screen_gap() -> Option<f64> {...}`

### `component::layout::hook::impl`

- `fn` **`use_resize`** — `pub fn use_resize() -> Signal<bool> {...}`
- `fn` **`use_drawer_toggle`** — `pub fn use_drawer_toggle(drawer_open: Signal<bool>) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`use_safe_area_fix`** — `pub fn use_safe_area_fix() {...}`
- `fn` **`is_immersive_declared`** — `pub(crate) fn is_immersive_declared() -> bool {...}`
- `fn` **`apply_cached_insets`** — `pub fn apply_cached_insets() {...}`

### `component::layout::hook::static`

- `static` **`SAFE_AREA_INSET_TOP`** — `pub(crate) static SAFE_AREA_INSET_TOP: RefCell<String> = const { RefCell::new(String::new()) };`
- `static` **`SAFE_AREA_INSET_RIGHT`** — `pub(crate) static SAFE_AREA_INSET_RIGHT: RefCell<String> = const { RefCell::new(String::new()) };`
- `static` **`SAFE_AREA_INSET_BOTTOM`** — `pub(crate) static SAFE_AREA_INSET_BOTTOM: RefCell<String> = const { RefCell::new(String::new()) };`
- `static` **`SAFE_AREA_INSET_LEFT`** — `pub(crate) static SAFE_AREA_INSET_LEFT: RefCell<String> = const { RefCell::new(String::new()) };`
- `static` **`NATIVE_FULLSCREEN_ACTIVE`** — `pub(crate) static NATIVE_FULLSCREEN_ACTIVE: Cell<bool> = const { Cell::new(false) };`
- `static` **`NATIVE_FULLSCREEN_EXIT_BY_POPSTATE`** — `pub(crate) static NATIVE_FULLSCREEN_EXIT_BY_POPSTATE: Cell<bool> = const { Cell::new(false) };`

### `component::layout::hook::struct`

- `struct` **`UseEuvLayout`** — `pub struct UseEuvLayout;`

### `component::link::view::fn`

- `fn` **`euv_link`** — `pub fn euv_link(node: VirtualNode<EuvLinkProps>) -> VirtualNode {...}`

### `component::link::view::struct`

- `struct` **`EuvLinkProps`** — `pub struct EuvLinkProps {`

### `component::list::view::fn`

- `fn` **`euv_list`** — `pub fn euv_list(node: VirtualNode<EuvListProps>) -> VirtualNode {...}`

### `component::list::view::struct`

- `struct` **`EuvListItem`** — `pub struct EuvListItem {`
- `struct` **`EuvListProps`** — `pub struct EuvListProps {`

### `component::loading::view::fn`

- `fn` **`euv_loading`** — `pub fn euv_loading(node: VirtualNode<EuvLoadingProps>) -> VirtualNode {...}`

### `component::loading::view::struct`

- `struct` **`EuvLoadingProps`** — `pub struct EuvLoadingProps {`

### `component::logo::view::enum`

- `enum` **`LogoButtonVariant`** — `pub enum LogoButtonVariant {`

### `component::logo::view::fn`

- `fn` **`euv_logo`** — `pub fn euv_logo(node: VirtualNode<EuvLogoProps>) -> VirtualNode {...}`

### `component::logo::view::struct`

- `struct` **`EuvLogoProps`** — `pub struct EuvLogoProps {`

### `component::markdown::view::enum`

- `enum` **`EuvMdBlock`** — `pub enum EuvMdBlock {`
- `enum` **`EuvMdInline`** — `pub enum EuvMdInline {`

### `component::markdown::view::fn`

- `fn` **`euv_markdown`** — `pub fn euv_markdown(node: VirtualNode<EuvMarkdownProps>) -> VirtualNode {...}`
- `fn` **`euv_markdown_blocks`** — `pub fn euv_markdown_blocks(blocks: &'static [EuvMdBlock]) -> VirtualNode {...}`
- `fn` **`mark_image_loaded`** — `pub(crate) fn mark_image_loaded() -> Option<Rc<dyn Fn(Event)>> {...}`

### `component::markdown::view::struct`

- `struct` **`EuvMarkdownProps`** — `pub struct EuvMarkdownProps {`

### `component::mentions::view::fn`

- `fn` **`euv_mentions`** — `pub fn euv_mentions(node: VirtualNode<EuvMentionsProps>) -> VirtualNode {...}`
- `fn` **`mentions_trigger`** — `pub fn mentions_trigger(text: &str) -> Option<&str> {...}`
- `fn` **`mentions_matches`** — `pub fn mentions_matches(item: &EuvMentionItem, query: &str) -> bool {...}`
- `fn` **`mentions_filter`** — `pub fn mentions_filter(items: &[EuvMentionItem], query: &str) -> Vec<EuvMentionItem> {...}`
- `fn` **`mentions_apply`** — `pub fn mentions_apply(text: &str, label: &str) -> String {...}`
- `fn` **`on_mentions_select`** — `pub fn on_mentions_select<E: 'static>( value: Signal<String>, open: Signal<bool>, item_value: &'static str, item_label: &'static str, on_select: Option<Rc<dyn Fn(&'static str)>>, ) -> Option<Rc<dyn Fn(E)>> {...}`

### `component::mentions::view::struct`

- `struct` **`EuvMentionItem`** — `pub struct EuvMentionItem {`
- `struct` **`EuvMentionsProps`** — `pub struct EuvMentionsProps {`

### `component::message::view::fn`

- `fn` **`euv_message`** — `pub fn euv_message(node: VirtualNode<EuvMessageProps>) -> VirtualNode {...}`
- `fn` **`message_callback_handler`** — `pub fn message_callback_handler<E: 'static>( callback: Option<Rc<dyn Fn()>>, ) -> Option<Rc<dyn Fn(E)>> {...}`

### `component::message::view::struct`

- `struct` **`EuvMessageItem`** — `pub struct EuvMessageItem {`
- `struct` **`EuvMessageProps`** — `pub struct EuvMessageProps {`

### `component::modal::view::fn`

- `fn` **`euv_modal`** — `pub fn euv_modal(node: VirtualNode<EuvModalProps>) -> VirtualNode {...}`

### `component::modal::view::struct`

- `struct` **`EuvModalProps`** — `pub struct EuvModalProps {`

### `component::nav::view::fn`

- `fn` **`euv_nav_item`** — `pub fn euv_nav_item(node: VirtualNode<EuvNavItemProps>) -> VirtualNode {...}`
- `fn` **`euv_mobile_nav_item`** — `pub fn euv_mobile_nav_item(node: VirtualNode<EuvMobileNavItemProps>) -> VirtualNode {...}`
- `fn` **`euv_nav_items`** — `pub fn euv_nav_items(node: VirtualNode<EuvNavItemsProps>) -> VirtualNode {...}`

### `component::nav::view::struct`

- `struct` **`EuvNavItemProps`** — `pub struct EuvNavItemProps {`
- `struct` **`EuvMobileNavItemProps`** — `pub struct EuvMobileNavItemProps {`
- `struct` **`EuvNavItemConfig`** — `pub struct EuvNavItemConfig {`
- `struct` **`EuvNavItemsProps`** — `pub struct EuvNavItemsProps {`

### `component::nav::view::type`

- `type` **`NavItemClickCallback`** — `pub type NavItemClickCallback = Rc<dyn Fn(&str)>;`
- `type` **`NavEventCallback`** — `pub type NavEventCallback = Rc<dyn Fn()>;`
- `type` **`ClickEventHandler`** — `pub type ClickEventHandler = Rc<dyn Fn(Event)>;`

### `component::navbar::view::fn`

- `fn` **`euv_navbar`** — `pub fn euv_navbar(node: VirtualNode<EuvNavbarProps>) -> VirtualNode {...}`
- `fn` **`euv_navbar_link`** — `pub fn euv_navbar_link(node: VirtualNode<EuvNavbarLinkProps>) -> VirtualNode {...}`

### `component::navbar::view::struct`

- `struct` **`EuvNavbarItem`** — `pub struct EuvNavbarItem {`
- `struct` **`EuvNavbarProps`** — `pub struct EuvNavbarProps {`
- `struct` **`EuvNavbarLinkProps`** — `pub struct EuvNavbarLinkProps {`

### `component::notification::view::fn`

- `fn` **`euv_notification`** — `pub fn euv_notification(node: VirtualNode<EuvNotificationProps>) -> VirtualNode {...}`
- `fn` **`notification_callback_handler`** — `pub fn notification_callback_handler<E: 'static>( callback: Option<Rc<dyn Fn()>>, ) -> Option<Rc<dyn Fn(E)>> {...}`

### `component::notification::view::struct`

- `struct` **`EuvNotificationItem`** — `pub struct EuvNotificationItem {`
- `struct` **`EuvNotificationProps`** — `pub struct EuvNotificationProps {`

### `component::number_input::view::fn`

- `fn` **`stepped_value`** — `pub fn stepped_value(current: i64, step: i64, min: Option<i64>, max: Option<i64>) -> Option<i64> {...}`
- `fn` **`stepper_disabled`** — `pub fn stepper_disabled(current: i64, step: i64, min: Option<i64>, max: Option<i64>) -> bool {...}`
- `fn` **`euv_number_input`** — `pub fn euv_number_input(node: VirtualNode<EuvNumberInputProps>) -> VirtualNode {...}`

### `component::number_input::view::struct`

- `struct` **`EuvNumberInputProps`** — `pub struct EuvNumberInputProps {`

### `component::pagination::view::fn`

- `fn` **`euv_pagination`** — `pub fn euv_pagination(node: VirtualNode<EuvPaginationProps>) -> VirtualNode {...}`

### `component::pagination::view::struct`

- `struct` **`EuvPaginationItem`** — `pub struct EuvPaginationItem {`
- `struct` **`EuvPaginationProps`** — `pub struct EuvPaginationProps {`

### `component::panel::view::enum`

- `enum` **`EuvPanelVariant`** — `pub enum EuvPanelVariant {`

### `component::panel::view::fn`

- `fn` **`euv_panel`** — `pub fn euv_panel(node: VirtualNode<EuvPanelProps>) -> VirtualNode {...}`

### `component::panel::view::struct`

- `struct` **`EuvPanelProps`** — `pub struct EuvPanelProps {`

### `component::popconfirm::view::fn`

- `fn` **`euv_popconfirm`** — `pub fn euv_popconfirm(node: VirtualNode<EuvPopconfirmProps>) -> VirtualNode {...}`
- `fn` **`popconfirm_toggle_handler`** — `pub fn popconfirm_toggle_handler<E: 'static>(open: Signal<bool>) -> Option<Rc<dyn Fn(E)>> {...}`
- `fn` **`popconfirm_ok_handler`** — `pub fn popconfirm_ok_handler<E: 'static>( on_ok: Option<Rc<dyn Fn()>>, open: Signal<bool>, ) -> Rc<dyn Fn(E)> {...}`
- `fn` **`popconfirm_cancel_handler`** — `pub fn popconfirm_cancel_handler<E: 'static>( on_cancel: Option<Rc<dyn Fn()>>, open: Signal<bool>, ) -> Rc<dyn Fn(E)> {...}`

### `component::popconfirm::view::struct`

- `struct` **`EuvPopconfirmProps`** — `pub struct EuvPopconfirmProps {`

### `component::popover::view::fn`

- `fn` **`euv_popover`** — `pub fn euv_popover(node: VirtualNode<EuvPopoverProps>) -> VirtualNode {...}`
- `fn` **`on_popover_toggle`** — `pub fn on_popover_toggle(open: Signal<bool>) -> Option<Rc<dyn Fn(Event)>> {...}`

### `component::popover::view::struct`

- `struct` **`EuvPopoverProps`** — `pub struct EuvPopoverProps {`

### `component::progress::view::fn`

- `fn` **`euv_progress`** — `pub fn euv_progress(node: VirtualNode<EuvProgressProps>) -> VirtualNode {...}`
- `fn` **`progress_percent_clamp`** — `pub fn progress_percent_clamp(percent: f64) -> f64 {...}`

### `component::progress::view::struct`

- `struct` **`EuvProgressProps`** — `pub struct EuvProgressProps {`

### `component::radio::view::fn`

- `fn` **`euv_radio`** — `pub fn euv_radio(node: VirtualNode<EuvRadioGroupProps>) -> VirtualNode {...}`
- `fn` **`on_radio_change`** — `pub fn on_radio_change( signal: Signal<String>, option_value: &'static str, ) -> Option<Rc<dyn Fn(Event)>> {...}`

### `component::radio::view::struct`

- `struct` **`EuvRadioOption`** — `pub struct EuvRadioOption {`
- `struct` **`EuvRadioGroupProps`** — `pub struct EuvRadioGroupProps {`

### `component::rating::view::enum`

- `enum` **`EuvRatingSize`** — `pub enum EuvRatingSize {`

### `component::rating::view::fn`

- `fn` **`rating_fill_percent`** — `pub fn rating_fill_percent(value: f64, max: f64) -> f64 {...}`
- `fn` **`euv_rating`** — `pub fn euv_rating(node: VirtualNode<EuvRatingProps>) -> VirtualNode {...}`

### `component::rating::view::impl`

- `fn` **`px`** — `pub fn px(&self) -> i32 {...}`

### `component::rating::view::struct`

- `struct` **`EuvRatingProps`** — `pub struct EuvRatingProps {`

### `component::result::view::fn`

- `fn` **`euv_result`** — `pub fn euv_result(node: VirtualNode<EuvResultProps>) -> VirtualNode {...}`

### `component::result::view::struct`

- `struct` **`EuvResultProps`** — `pub struct EuvResultProps {`

### `component::router::hook::impl`

- `fn` **`use_scroll_to_top`** — `pub fn use_scroll_to_top(route_signal: Signal<String>) {...}`
- `fn` **`use_hash_change`** — `pub fn use_hash_change(route_signal: Signal<String>) {...}`
- `fn` **`use_overlay_history`** — `pub fn use_overlay_history(drawer_open: Signal<bool>, mobile_signal: Signal<bool>) {...}`
- `fn` **`use_scroll_drawer_to_active`** — `pub fn use_scroll_drawer_to_active(drawer_open: Signal<bool>) {...}`
- `fn` **`register_popstate_guard`** — `pub fn register_popstate_guard(guard: Rc<dyn Fn() -> bool>) -> usize {...}`
- `fn` **`unregister_popstate_guard`** — `pub fn unregister_popstate_guard(guard_id: usize) -> bool {...}`
- `fn` **`overlay_push_state`** — `pub fn overlay_push_state() {...}`
- `fn` **`overlay_back`** — `pub fn overlay_back(navigate_target: Option<String>) {...}`
- `fn` **`overlay_stack_push`** — `pub(crate) fn overlay_stack_push(closer: Rc<dyn Fn()>) {...}`
- `fn` **`overlay_stack_pop`** — `pub(crate) fn overlay_stack_pop() -> Option<Rc<dyn Fn()>> {...}`
- `fn` **`overlay_stack_close`** — `pub fn overlay_stack_close() {...}`
- `fn` **`modal_push`** — `pub fn modal_push(visible: Signal<bool>, closer: Rc<dyn Fn()>) {...}`
- `fn` **`modal_close_via_ui`** — `pub fn modal_close_via_ui(visible: Signal<bool>) {...}`
- `fn` **`open_system_browser`** — `pub fn open_system_browser<U>(url: U) where U: AsRef<str>, {...}`
- `fn` **`external_link_handler`** — `pub fn external_link_handler<U>(url: U) -> NativeEventHandler where U: AsRef<str>, {...}`
- `fn` **`close_drawer_and_navigate`** — `pub fn close_drawer_and_navigate<T>(_drawer_open: Signal<bool>, target: T) where T: AsRef<str>, {...}`

### `component::router::hook::static`

- `static` **`BACK_PENDING`** — `pub(crate) static BACK_PENDING: Cell<bool> = const { Cell::new(false) };`
- `static` **`NAVIGATE_AFTER_BACK`** — `pub(crate) static NAVIGATE_AFTER_BACK: Cell<Option<String>> = const { Cell::new(None) };`
- `static` **`MODAL_STACK`** — `pub(crate) static MODAL_STACK: ModalStack = const { RefCell::new(Vec::new()) };`
- `static` **`OVERLAY_STACK`** — `pub(crate) static OVERLAY_STACK: OverlayStack = const { RefCell::new(Vec::new()) };`
- `static` **`WINDOW_EVENT_DEPTH`** — `pub(crate) static WINDOW_EVENT_DEPTH: Cell<usize> = const { Cell::new(0) };`
- `static` **`DEFERRED_NAVIGATION`** — `pub(crate) static DEFERRED_NAVIGATION: Cell<Option<String>> = const { Cell::new(None) };`
- `static` **`POPSTATE_GUARDS`** — `pub(crate) static POPSTATE_GUARDS: PopstateGuardList = const { RefCell::new(Vec::new()) };`
- `static` **`NEXT_POPSTATE_GUARD_ID`** — `pub(crate) static NEXT_POPSTATE_GUARD_ID: Cell<usize> = const { Cell::new(0) };`

### `component::router::hook::struct`

- `struct` **`Router`** — `pub struct Router;`
- `struct` **`OverlayEntry`** — `pub(crate) struct OverlayEntry {`

### `component::router::hook::type`

- `type` **`ModalStackEntry`** — `pub(crate) type ModalStackEntry = (Signal<bool>, Rc<dyn Fn()>);`
- `type` **`ModalStack`** — `pub(crate) type ModalStack = RefCell<Vec<ModalStackEntry>>;`
- `type` **`OverlayStack`** — `pub(crate) type OverlayStack = RefCell<Vec<OverlayEntry>>;`
- `type` **`PopstateGuard`** — `pub(crate) type PopstateGuard = Rc<dyn Fn() -> bool>;`
- `type` **`PopstateGuardEntry`** — `pub(crate) type PopstateGuardEntry = (usize, PopstateGuard);`
- `type` **`PopstateGuardList`** — `pub(crate) type PopstateGuardList = RefCell<Vec<PopstateGuardEntry>>;`

### `component::router::select::fn`

- `fn` **`normalize_path`** — `pub fn normalize_path(path: &str) -> String {...}`
- `fn` **`route_matches`** — `pub fn route_matches(route_path: &str, request_path: &str) -> bool {...}`
- `fn` **`find_active_route`** — `pub fn find_active_route<'a>( path: &str, routes: &'a [NestedRouteConfig], ) -> Option<&'a NestedRouteConfig> {...}`
- `fn` **`route_chain`** — `pub fn route_chain<'a>(path: &str, routes: &'a [NestedRouteConfig]) -> Vec<&'a NestedRouteConfig> {...}`
- `fn` **`build_chain`** — `pub(crate) fn build_chain<'a>( path: &str, routes: &'a [NestedRouteConfig], chain: &mut Vec<&'a NestedRouteConfig>, ) -> bool {...}`

### `component::router::select::impl`

- `fn` **`new`** — `pub fn new<P, F>(path: P, component: F, children: Vec<NestedRouteConfig>) -> Self where P: Into<String>, F: Fn() -> VirtualNode + 'static, {...}`
- `fn` **`component`** — `pub fn component(&self) -> Rc<dyn Fn() -> VirtualNode> {...}`
- `fn` **`children`** — `pub fn children(&self) -> &[NestedRouteConfig] {...}`

### `component::router::select::struct`

- `struct` **`NestedRouteConfig`** — `pub struct NestedRouteConfig {`

### `component::router::view::fn`

- `fn` **`euv_routes`** — `pub fn euv_routes(node: VirtualNode<EuvRoutesProps>) -> VirtualNode {...}`
- `fn` **`euv_page_router`** — `pub fn euv_page_router(node: VirtualNode<EuvPageRouterProps>) -> VirtualNode {...}`

### `component::router::view::impl`

- `fn` **`new`** — `pub fn new<F>(path: &'static str, component: F) -> Self where F: Fn() -> VirtualNode + 'static, {...}`
- `fn` **`current_route`** — `pub fn current_route() -> String {...}`
- `fn` **`navigate`** — `pub fn navigate<R>(route: R) where R: AsRef<str>, {...}`
- `fn` **`link_handler`** — `pub fn link_handler<R>(route: R) -> NativeEventHandler where R: AsRef<str>, {...}`
- `fn` **`is_mobile`** — `pub fn is_mobile() -> bool {...}`

### `component::router::view::struct`

- `struct` **`EuvPageRouterProps`** — `pub struct EuvPageRouterProps {`
- `struct` **`EuvRouteConfig`** — `pub struct EuvRouteConfig {`
- `struct` **`EuvRoutesProps`** — `pub struct EuvRoutesProps {`

### `component::segmented::view::fn`

- `fn` **`euv_segmented`** — `pub fn euv_segmented(node: VirtualNode<EuvSegmentedProps>) -> VirtualNode {...}`

### `component::segmented::view::struct`

- `struct` **`EuvSegmentedOption`** — `pub struct EuvSegmentedOption {`
- `struct` **`EuvSegmentedProps`** — `pub struct EuvSegmentedProps {`

### `component::select::view::enum`

- `enum` **`SelectPanelEntry`** — `pub(crate) enum SelectPanelEntry {`

### `component::select::view::fn`

- `fn` **`euv_select`** — `pub fn euv_select(node: VirtualNode<EuvSelectProps>) -> VirtualNode {...}`
- `fn` **`use_euv_select_open`** — `pub fn use_euv_select_open() -> Signal<bool> {...}`

### `component::select::view::struct`

- `struct` **`EuvSelectOption`** — `pub struct EuvSelectOption {`
- `struct` **`EuvSelectProps`** — `pub struct EuvSelectProps {`

### `component::sidebar::view::fn`

- `fn` **`first_navigable_route`** — `pub fn first_navigable_route(items: &[EuvSidebarItem]) -> Option<&'static str> {...}`
- `fn` **`euv_sidebar`** — `pub fn euv_sidebar(node: VirtualNode<EuvSidebarProps>) -> VirtualNode {...}`
- `fn` **`euv_sidebar_item`** — `pub fn euv_sidebar_item(node: VirtualNode<EuvSidebarItemProps>) -> VirtualNode {...}`

### `component::sidebar::view::struct`

- `struct` **`EuvSidebarItem`** — `pub struct EuvSidebarItem {`
- `struct` **`EuvSidebarProps`** — `pub struct EuvSidebarProps {`
- `struct` **`EuvSidebarItemProps`** — `pub struct EuvSidebarItemProps {`

### `component::skeleton::view::fn`

- `fn` **`skeleton_line_count`** — `pub fn skeleton_line_count(count: usize) -> usize {...}`
- `fn` **`euv_skeleton`** — `pub fn euv_skeleton(node: VirtualNode<EuvSkeletonProps>) -> VirtualNode {...}`

### `component::skeleton::view::struct`

- `struct` **`EuvSkeletonProps`** — `pub struct EuvSkeletonProps {`

### `component::slider::view::fn`

- `fn` **`euv_slider`** — `pub fn euv_slider(node: VirtualNode<EuvSliderProps>) -> VirtualNode {...}`

### `component::slider::view::impl`

- `fn` **`percent`** — `pub fn percent(value: f64, min: f64, max: f64) -> f64 {...}`
- `fn` **`on_slider_input`** — `pub fn on_slider_input(signal: Signal<f64>, min: f64, max: f64) -> Option<Rc<dyn Fn(Event)>> {...}`

### `component::slider::view::struct`

- `struct` **`EuvSliderProps`** — `pub struct EuvSliderProps {`
- `struct` **`EuvSliderHelpers`** — `pub struct EuvSliderHelpers;`

### `component::space::view::enum`

- `enum` **`EuvSpaceSize`** — `pub enum EuvSpaceSize {`

### `component::space::view::fn`

- `fn` **`euv_space`** — `pub fn euv_space(node: VirtualNode<EuvSpaceProps>) -> VirtualNode {...}`

### `component::space::view::impl`

- `fn` **`token`** — `pub fn token(&self) -> &'static str {...}`

### `component::space::view::struct`

- `struct` **`EuvSpaceProps`** — `pub struct EuvSpaceProps {`

### `component::splitter::view::fn`

- `fn` **`euv_splitter`** — `pub fn euv_splitter(node: VirtualNode<EuvSplitterProps>) -> VirtualNode {...}`

### `component::splitter::view::struct`

- `struct` **`EuvSplitterProps`** — `pub struct EuvSplitterProps {`
- `struct` **`DragSession`** — `pub(crate) struct DragSession {`

### `component::stat::view::fn`

- `fn` **`euv_stat`** — `pub fn euv_stat(node: VirtualNode<EuvStatProps>) -> VirtualNode {...}`

### `component::stat::view::struct`

- `struct` **`EuvStatProps`** — `pub struct EuvStatProps {`

### `component::steps::view::fn`

- `fn` **`euv_steps`** — `pub fn euv_steps(node: VirtualNode<EuvStepsProps>) -> VirtualNode {...}`

### `component::steps::view::struct`

- `struct` **`EuvStep`** — `pub struct EuvStep {`
- `struct` **`EuvStepsProps`** — `pub struct EuvStepsProps {`

### `component::switch::view::fn`

- `fn` **`euv_switch`** — `pub fn euv_switch(node: VirtualNode<EuvSwitchProps>) -> VirtualNode {...}`
- `fn` **`use_euv_switch_state`** — `pub fn use_euv_switch_state(checked: Signal<bool>) -> EuvSwitchState {...}`

### `component::switch::view::impl`

- `fn` **`new`** — `pub fn new(checked: Signal<bool>) -> Self {...}`
- `fn` **`toggle`** — `pub fn toggle(&self) {...}`
- `fn` **`on_toggle`** — `pub fn on_toggle(&self, disabled: Signal<bool>) -> Option<Rc<dyn Fn(Event)>> {...}`

### `component::switch::view::struct`

- `struct` **`EuvSwitchProps`** — `pub struct EuvSwitchProps {`
- `struct` **`EuvSwitchState`** — `pub struct EuvSwitchState {`

### `component::table::view::enum`

- `enum` **`EuvTableAlign`** — `pub enum EuvTableAlign {`

### `component::table::view::fn`

- `fn` **`euv_table`** — `pub fn euv_table(node: VirtualNode<EuvTableProps>) -> VirtualNode {...}`

### `component::table::view::struct`

- `struct` **`EuvTableColumn`** — `pub struct EuvTableColumn {`
- `struct` **`EuvTableRow`** — `pub struct EuvTableRow {`
- `struct` **`EuvTableProps`** — `pub struct EuvTableProps {`

### `component::tabs::view::fn`

- `fn` **`euv_tabs`** — `pub fn euv_tabs(node: VirtualNode<EuvTabsProps>) -> VirtualNode {...}`

### `component::tabs::view::struct`

- `struct` **`EuvTabItem`** — `pub struct EuvTabItem {`
- `struct` **`EuvTabsProps`** — `pub struct EuvTabsProps {`

### `component::tag::view::enum`

- `enum` **`EuvTagVariant`** — `pub enum EuvTagVariant {`
- `enum` **`EuvTagColor`** — `pub enum EuvTagColor {`

### `component::tag::view::fn`

- `fn` **`euv_tag`** — `pub fn euv_tag(node: VirtualNode<EuvTagProps>) -> VirtualNode {...}`

### `component::tag::view::struct`

- `struct` **`EuvTagProps`** — `pub struct EuvTagProps {`

### `component::theme::hook::impl`

- `fn` **`use_theme_state`** — `pub fn use_theme_state(mobile_signal: Signal<bool>) -> ThemeState {...}`
- `fn` **`use_system_theme_change`** — `pub fn use_system_theme_change(theme_signal: Signal<String>) {...}`
- `fn` **`detect_system_theme`** — `pub fn detect_system_theme() -> String {...}`
- `fn` **`theme_class_name`** — `pub(crate) fn theme_class_name(theme: &str) -> &'static str {...}`
- `fn` **`toggle`** — `pub fn toggle(theme_signal: Signal<String>) -> Option<Rc<dyn Fn(Event)>> {...}`

### `component::theme::hook::struct`

- `struct` **`ThemeState`** — `pub struct ThemeState {`

### `component::time_picker::view::fn`

- `fn` **`parse_time`** — `pub fn parse_time(text: &str) -> Option<(u32, u32)> {...}`
- `fn` **`format_time`** — `pub fn format_time(hour: u32, minute: u32) -> String {...}`
- `fn` **`clamp_hour_range`** — `pub fn clamp_hour_range(min_hour: u32, max_hour: u32) -> (u32, u32) {...}`
- `fn` **`hour_values`** — `pub fn hour_values(min_hour: u32, max_hour: u32) -> Vec<u32> {...}`
- `fn` **`minute_values`** — `pub fn minute_values(minute_step: u32) -> Vec<u32> {...}`
- `fn` **`time_with_hour`** — `pub fn time_with_hour(current: &str, hour: u32) -> String {...}`
- `fn` **`time_with_minute`** — `pub fn time_with_minute(current: &str, minute: u32, fallback_hour: u32) -> String {...}`
- `fn` **`current_time`** — `pub fn current_time() -> Option<(u32, u32)> {...}`
- `fn` **`time_picker_toggle_handler`** — `pub fn time_picker_toggle_handler<E: 'static>(open: Signal<bool>) -> Option<Rc<dyn Fn(E)>> {...}`
- `fn` **`time_picker_pick_hour_handler`** — `pub fn time_picker_pick_hour_handler<E: 'static>( value: Signal<String>, open: Signal<bool>, on_change: Option<Rc<dyn Fn(&'static str)>>, hour: u32, ) -> Option<Rc<dyn Fn(E)>> {...}`
- `fn` **`time_picker_pick_minute_handler`** — `pub fn time_picker_pick_minute_handler<E: 'static>( value: Signal<String>, open: Signal<bool>, on_change: Option<Rc<dyn Fn(&'static str)>>, minute: u32, fallback_hour: u32, ) -> Option<Rc<dyn Fn(E)>> {...}`
- `fn` **`time_picker_now_handler`** — `pub fn time_picker_now_handler<E: 'static>( value: Signal<String>, open: Signal<bool>, on_change: Option<Rc<dyn Fn(&'static str)>>, ) -> Rc<dyn Fn(E)> {...}`
- `fn` **`time_picker_clear_handler`** — `pub fn time_picker_clear_handler<E: 'static>( value: Signal<String>, open: Signal<bool>, on_change: Option<Rc<dyn Fn(&'static str)>>, ) -> Rc<dyn Fn(E)> {...}`
- `fn` **`euv_time_picker`** — `pub fn euv_time_picker(node: VirtualNode<EuvTimePickerProps>) -> VirtualNode {...}`

### `component::time_picker::view::struct`

- `struct` **`EuvTimePickerProps`** — `pub struct EuvTimePickerProps {`

### `component::timeline::view::fn`

- `fn` **`euv_timeline`** — `pub fn euv_timeline(node: VirtualNode<EuvTimelineProps>) -> VirtualNode {...}`

### `component::timeline::view::struct`

- `struct` **`EuvTimelineItem`** — `pub struct EuvTimelineItem {`
- `struct` **`EuvTimelineProps`** — `pub struct EuvTimelineProps {`

### `component::toc::view::fn`

- `fn` **`euv_toc`** — `pub fn euv_toc(node: VirtualNode<EuvTocProps>) -> VirtualNode {...}`

### `component::toc::view::struct`

- `struct` **`EuvTocItem`** — `pub struct EuvTocItem {`
- `struct` **`EuvTocProps`** — `pub struct EuvTocProps {`

### `component::tooltip::view::enum`

- `enum` **`EuvTooltipPlacement`** — `pub enum EuvTooltipPlacement {`

### `component::tooltip::view::fn`

- `fn` **`euv_tooltip`** — `pub fn euv_tooltip(node: VirtualNode<EuvTooltipProps>) -> VirtualNode {...}`

### `component::tooltip::view::struct`

- `struct` **`EuvTooltipProps`** — `pub struct EuvTooltipProps {`

### `component::touch::hook::enum`

- `enum` **`EuvGesture`** — `pub enum EuvGesture {`

### `component::touch::hook::fn`

- `fn` **`now_millis`** — `pub(crate) fn now_millis() -> f64 {...}`

### `component::touch::hook::impl`

- `fn` **`extract_all`** — `pub fn extract_all(event: &Event) -> Vec<NativeTouchPoint> {...}`
- `fn` **`extract_changed`** — `pub fn extract_changed(event: &Event) -> Vec<NativeTouchPoint> {...}`
- `fn` **`extract_all`** — `pub fn extract_all(event: &Event) -> Vec<NativeTouchPointF64> {...}`
- `fn` **`new`** — `pub fn new() -> EuvGestureRecognizer {...}`
- `fn` **`with_config`** — `pub fn with_config(config: EuvGestureConfig) -> EuvGestureRecognizer {...}`
- `fn` **`use_gesture`** — `pub fn use_gesture(self) -> EuvGestureState {...}`
- `fn` **`classify`** — `pub fn classify( &self, dx: f64, dy: f64, elapsed_millis: f64, travel: f64, ) -> Option<EuvGesture> {...}`
- `fn` **`pinch_from`** — `pub fn pinch_from(&self, points: &[NativeTouchPoint], start_distance: f64) -> Option<EuvPinch> {...}`
- `fn` **`pinch_is_significant`** — `pub fn pinch_is_significant(&self, distance: f64, start_distance: f64) -> bool {...}`
- `fn` **`drag_from`** — `pub fn drag_from( &self, point: &GesturePoint, start_x: f64, start_y: f64, travel: f64, ) -> EuvDrag {...}`
- `fn` **`name`** — `pub fn name(self) -> &'static str {...}`
- `fn` **`begin`** — `pub fn begin(&mut self, points: &[NativeTouchPoint]) {...}`
- `fn` **`advance`** — `pub fn advance(&mut self, points: &[NativeTouchPoint]) {...}`
- `fn` **`primary`** — `pub fn primary(&self) -> Option<GesturePoint> {...}`
- `fn` **`finish`** — `pub fn finish(&mut self, config: &EuvGestureConfig) -> Option<EuvGesture> {...}`
- `fn` **`reset`** — `pub fn reset(&mut self) {...}`

### `component::touch::hook::struct`

- `struct` **`NativeTouchPoint`** — `pub struct NativeTouchPoint {`
- `struct` **`NativeTouchPointF64`** — `pub struct NativeTouchPointF64 {`
- `struct` **`EuvPinch`** — `pub struct EuvPinch {`
- `struct` **`EuvDrag`** — `pub struct EuvDrag {`
- `struct` **`EuvGestureConfig`** — `pub struct EuvGestureConfig {`
- `struct` **`EuvGestureState`** — `pub struct EuvGestureState {`
- `struct` **`EuvGestureRecognizer`** — `pub struct EuvGestureRecognizer {`
- `struct` **`GestureProgress`** — `pub struct GestureProgress {`
- `struct` **`GesturePoint`** — `pub struct GesturePoint {`

### `component::transfer::view::fn`

- `fn` **`euv_transfer`** — `pub fn euv_transfer(node: VirtualNode<EuvTransferProps>) -> VirtualNode {...}`
- `fn` **`transfer_is_marked`** — `pub fn transfer_is_marked(marked: &[String], value: &str) -> bool {...}`
- `fn` **`transfer_toggle_value`** — `pub fn transfer_toggle_value(selected: Signal<Vec<String>>, value: &'static str) {...}`
- `fn` **`transfer_move_to_target`** — `pub fn transfer_move_to_target<E: 'static>( selected: Signal<Vec<String>>, source_values: Vec<&'static str>, on_move: Option<Rc<dyn Fn(&'static str)>>, ) -> Rc<dyn Fn(E)> {...}`
- `fn` **`transfer_move_to_source`** — `pub fn transfer_move_to_source<E: 'static>( selected: Signal<Vec<String>>, target_values: Vec<&'static str>, on_move: Option<Rc<dyn Fn(&'static str)>>, ) -> Rc<dyn Fn(E)> {...}`
- `fn` **`transfer_report_moves`** — `pub fn transfer_report_moves( selected: Signal<Vec<String>>, values: &[&'static str], on_move: &Option<Rc<dyn Fn(&'static str)>>, ) {...}`

### `component::transfer::view::struct`

- `struct` **`EuvTransferItem`** — `pub struct EuvTransferItem {`
- `struct` **`EuvTransferProps`** — `pub struct EuvTransferProps {`

### `component::tree::view::fn`

- `fn` **`euv_tree`** — `pub fn euv_tree(node: VirtualNode<EuvTreeProps>) -> VirtualNode {...}`
- `fn` **`use_euv_tree_expanded`** — `pub fn use_euv_tree_expanded(nodes: &[EuvTreeNode], default_expanded: bool) -> Signal<Vec<String>> {...}`
- `fn` **`select_tree_node`** — `pub fn select_tree_node( selected: Signal<String>, on_select: Option<Rc<dyn Fn(&'static str)>>, value: &'static str, ) {...}`
- `fn` **`toggle_expanded_value`** — `pub fn toggle_expanded_value(values: &mut Vec<String>, value: &str) {...}`

### `component::tree::view::struct`

- `struct` **`EuvTreeNode`** — `pub struct EuvTreeNode {`
- `struct` **`EuvTreeProps`** — `pub struct EuvTreeProps {`

### `component::tree_select::view::fn`

- `fn` **`euv_tree_select`** — `pub fn euv_tree_select(node: VirtualNode<EuvTreeSelectProps>) -> VirtualNode {...}`
- `fn` **`tree_select_find_label`** — `pub fn tree_select_find_label(nodes: &[EuvTreeNode], value: &str) -> Option<&'static str> {...}`
- `fn` **`tree_select_toggle_handler`** — `pub fn tree_select_toggle_handler<E: 'static>(open: Signal<bool>) -> Option<Rc<dyn Fn(E)>> {...}`
- `fn` **`tree_select_pick_node`** — `pub fn tree_select_pick_node( value: Signal<String>, on_select: Option<Rc<dyn Fn(&'static str)>>, open: Signal<bool>, node_value: &'static str, ) {...}`

### `component::tree_select::view::struct`

- `struct` **`EuvTreeSelectProps`** — `pub struct EuvTreeSelectProps {`

### `component::typography::view::enum`

- `enum` **`EuvTextVariant`** — `pub enum EuvTextVariant {`

### `component::typography::view::fn`

- `fn` **`euv_text`** — `pub fn euv_text(node: VirtualNode<EuvTextProps>) -> VirtualNode {...}`

### `component::typography::view::struct`

- `struct` **`EuvTextProps`** — `pub struct EuvTextProps {`

### `component::upload::view::enum`

- `enum` **`EuvUploadStatus`** — `pub enum EuvUploadStatus {`

### `component::upload::view::fn`

- `fn` **`on_upload_files_change`** — `pub fn on_upload_files_change( on_files: Option<Rc<dyn Fn(&'static str)>>, ) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`on_upload_drag_over`** — `pub fn on_upload_drag_over(drag_active: Signal<bool>) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`on_upload_drag_leave`** — `pub fn on_upload_drag_leave(drag_active: Signal<bool>) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`euv_upload`** — `pub fn euv_upload(node: VirtualNode<EuvUploadProps>) -> VirtualNode {...}`

### `component::upload::view::struct`

- `struct` **`EuvUploadFile`** — `pub struct EuvUploadFile {`
- `struct` **`EuvUploadProps`** — `pub struct EuvUploadProps {`

### `component::vconsole::hook::enum`

- `enum` **`LogLevel`** — `pub enum LogLevel {`
- `enum` **`LogFilter`** — `pub enum LogFilter {`

### `component::vconsole::hook::fn`

- `fn` **`console_log_ref`** — `pub(crate) fn console_log_ref() -> Option<Rc<RefCell<Vec<ConsoleEntry>>>> {...}`
- `fn` **`install_console_log_ref`** — `pub(crate) fn install_console_log_ref(logs_ref: Rc<RefCell<Vec<ConsoleEntry>>>) {...}`

### `component::vconsole::hook::impl`

- `fn` **`init`** — `pub fn init() {...}`
- `fn` **`log`** — `pub fn log<M>(message: M) where M: AsRef<str>, {...}`
- `fn` **`warn`** — `pub fn warn<M>(message: M) where M: AsRef<str>, {...}`
- `fn` **`error`** — `pub fn error<M>(message: M) where M: AsRef<str>, {...}`
- `fn` **`clear`** — `pub fn clear() {...}`
- `fn` **`get_signal`** — `pub(crate) fn get_signal() -> Option<Signal<Vec<ConsoleEntry>>> {...}`
- `fn` **`fab_on_click`** — `pub(crate) fn fab_on_click(panel_open: Signal<bool>) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`push`** — `pub fn push(entry: ConsoleEntry) {...}`
- `fn` **`badge`** — `pub(crate) fn badge(self) -> &'static str {...}`
- `fn` **`on_filter_all`** — `pub(crate) fn on_filter_all(filter_signal: Signal<LogFilter>) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`on_filter_log`** — `pub(crate) fn on_filter_log(filter_signal: Signal<LogFilter>) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`on_filter_warn`** — `pub(crate) fn on_filter_warn(filter_signal: Signal<LogFilter>) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`on_filter_error`** — `pub(crate) fn on_filter_error(filter_signal: Signal<LogFilter>) -> Option<Rc<dyn Fn(Event)>> {...}`

### `component::vconsole::hook::static`

- `static` **`CONSOLE_LOG_REF`** — `pub(crate) static CONSOLE_LOG_REF: RefCell<Option<Rc<RefCell<Vec<ConsoleEntry>>>>> = const { RefCell::new(None) };`
- `static` **`CONSOLE_LOG_SIGNAL`** — `pub(crate) static CONSOLE_LOG_SIGNAL: SignalCell<Vec<ConsoleEntry>> = SignalCell::none();`

### `component::vconsole::hook::struct`

- `struct` **`Console`** — `pub struct Console;`
- `struct` **`ConsoleEntry`** — `pub struct ConsoleEntry {`

### `component::vconsole::view::fn`

- `fn` **`euv_vconsole_panel`** — `pub fn euv_vconsole_panel(node: VirtualNode<EuvVconsolePanelProps>) -> VirtualNode {...}`
- `fn` **`euv_vconsole_fab`** — `pub fn euv_vconsole_fab(node: VirtualNode<EuvVconsoleFabProps>) -> VirtualNode {...}`
- `fn` **`euv_vconsole_drawer`** — `pub fn euv_vconsole_drawer(node: VirtualNode<EuvVconsoleDrawerProps>) -> VirtualNode {...}`

### `component::vconsole::view::struct`

- `struct` **`EuvVconsolePanelProps`** — `pub struct EuvVconsolePanelProps {`
- `struct` **`EuvVconsoleFabProps`** — `pub struct EuvVconsoleFabProps {`
- `struct` **`EuvVconsoleDrawerProps`** — `pub struct EuvVconsoleDrawerProps {`

### `component::virtual_list::hook::impl`

- `fn` **`use_scroll_state`** — `pub fn use_scroll_state() -> UseVirtualList {...}`
- `fn` **`on_scroll`** — `pub fn on_scroll(self) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`update_viewport_height`** — `pub fn update_viewport_height(self) {...}`
- `fn` **`schedule_measure`** — `pub fn schedule_measure(self) {...}`
- `fn` **`schedule_measure_by_id`** — `pub(crate) fn schedule_measure_by_id(self, container_id: &str) {...}`
- `fn` **`try_get_container`** — `pub fn try_get_container() -> Option<Element> {...}`
- `fn` **`try_get_container_by_id`** — `pub fn try_get_container_by_id<C>(container_id: C) -> Option<Element> where C: AsRef<str>, {...}`
- `fn` **`compute_visible_range`** — `pub(crate) fn compute_visible_range( scroll_offset: i32, viewport_height: i32, total_count: usize, item_height: i32, overscan_count: usize, ) -> (usize, usize, usize, usize) {...}`

### `component::virtual_list::hook::static`

- `static` **`PENDING_MEASURE`** — `pub(crate) static PENDING_MEASURE: AtomicBool = AtomicBool::new(false);`
- `static` **`mut`** — `pub(crate) static mut PENDING_MEASURE_BY_ID: LazyLock<PendingMeasureCell> = LazyLock::new(|| PendingMeasureCell(UnsafeCell::new(HashSet::new())));`

### `component::virtual_list::hook::struct`

- `struct` **`UseVirtualList`** — `pub struct UseVirtualList {`
- `struct` **`PendingMeasureCell`** — `pub(crate) struct PendingMeasureCell( #[get(pub(crate))] #[get_mut(pub(crate))] #[set(pub(crate))] pub(crate) UnsafeCell<HashSet<String>>, );`

### `component::virtual_list::view::fn`

- `fn` **`euv_virtual_list`** — `pub fn euv_virtual_list(node: VirtualNode<EuvVirtualListProps>) -> VirtualNode {...}`

### `component::virtual_list::view::struct`

- `struct` **`EuvVirtualListConfig`** — `pub struct EuvVirtualListConfig {`
- `struct` **`EuvVirtualListProps`** — `pub struct EuvVirtualListProps {`

### `component::virtual_list::view::type`

- `type` **`VirtualListItemRenderer`** — `pub type VirtualListItemRenderer = Rc<dyn Fn(usize) -> VirtualNode>;`
- `type` **`VirtualListScrollHandler`** — `pub type VirtualListScrollHandler = Rc<dyn Fn(i32)>;`
- `type` **`VirtualListRangeHandler`** — `pub type VirtualListRangeHandler = Rc<dyn Fn((usize, usize))>;`
- `type` **`VirtualListConfig`** — `pub type VirtualListConfig = EuvVirtualListConfig;`
- `type` **`VirtualListProps`** — `pub type VirtualListProps = EuvVirtualListProps;`

### `component::watermark::view::fn`

- `fn` **`euv_watermark`** — `pub fn euv_watermark(node: VirtualNode<EuvWatermarkProps>) -> VirtualNode {...}`

### `component::watermark::view::struct`

- `struct` **`EuvWatermarkProps`** — `pub struct EuvWatermarkProps {`
