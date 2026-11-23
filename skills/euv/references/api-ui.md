# euv-ui full pub API (components + hooks + style)

Source: `ui/src/` — auto-extracted from `pub` declarations.

Re-exported at the crate root as `euv::euv_button`, `euv::use_async`, etc. via `ui/src/lib.rs` `pub use {component::*, hook::*, style::*}`.

**Components are split into parts, not just built as one umbrella.** A
component the shadcn/ui reference splits into parts exposes each part as its
own `euv_*` function with its own props struct: a field has its label and
error parts, an empty state its media and description, a message its title and
body, a combobox its chip family, a navbar and menubar their menu parts, the
carousel and calendar theirs, the sidebar its tree, the notification the toast
provider, and the chart its tooltip and legend. A caller composes them the way
the reference site does, and the slot names are the reference's own. Five
parts the framework cannot express are the four portals — there is no portal
API — and the chart style, which is injected on the root element instead of a
style element.

The shadcn-aligned parts are now complete: the alert has its icon, title,
description and action, the card its header, title, description, content,
footer and action, the breadcrumb its list, item, link, page, separator and
ellipsis, the dropdown menu its group, sub, sub-trigger, sub-content, radio
group, radio item and checkbox item, the context menu its group, sub,
sub-trigger, sub-content and radio group, and the button its grouped and link
forms. The tree holds 119 component directories, 414 `euv_*` part functions
and 403 `Euv*Props` structs, and the docs site publishes 66 component pages
under `docs/docs/en/components/` (65 component pages plus the section
`README.md`).

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

### `style::css::const`

- `static` **`EMPTY_CLASS`** — `pub(crate) static EMPTY_CLASS: LazyLock<Css> = LazyLock::new(Css::default);`

### `style::css::fn`

- `fn` **`class_property`** — `pub(crate) fn class_property(css: &Css, property: &str) -> Option<String> {...}`
- `fn` **`inject_app_global_css`** — `pub fn inject_app_global_css() {...}`
- `fn` **`euv_md_css`** — `pub fn euv_md_css() -> &'static str {...}`

### `style::var::theme::fn`

- `fn` **`scheme_class_name`** — `pub fn scheme_class_name() -> &'static str {...}`
- `fn` **`scheme_name`** — `pub fn scheme_name() -> &'static str {...}`

### `style::var::theme::fn` — new theme tokens

Five tokens were added to both the light and the dark scheme blocks, so a card or a navigation row has one shared owner for its spacing:

| Token | Value |
|---|---|
| `card-padding` | `var(--space-md)` |
| `card-content-gap` | `var(--gap-component)` |
| `nav-row-height` | `calc(var(--control-height) + var(--space-lg))` |
| `nav-row-padding` | `var(--space-md)` |
| `nav-item-inset` | `var(--space-xs)` |

A sixth token, **`gap-caret`** (`8px`), was added later to both blocks. It is the
**minimum distance between a caret-bearing trigger's label and its caret**, and
every caret in the form family reads it — the select trigger, the date-picker,
the time-picker, the cascader and the tree-select trigger, plus the dropdown
sub-menu row. Before it, each trigger kept that distance by accident: the
select trigger happened to carry the same 8px gap as every other flex row,
while the other four carets had no size at all and were squeezed to the width
of their glyph.

- Every caret now reserves the same **16px box** (`width`/`height`:
  `var(--space-lg)`), is `inline-flex` and centred, and refuses to shrink
  (`flex-shrink: 0`), so a long label can never push into it.
- Every trigger's **placeholder class** carries the same ellipsis contract as
  its value class (`flex: 1`, `min-width: 0`, `overflow: hidden`,
  `text-overflow: ellipsis`, `white-space: nowrap`) — the ellipsis used to
  disappear the moment the control had no selection.
- The dropdown sub-menu row's label was a bare text node; it is now wrapped in
  the existing `c_euv_dropdown_menu_item_label` class so it ellipsizes too.
- The gap is proved in a **real browser**: the automation fixture mounts all
  five triggers and the `caret-gap` case measures the rendered boxes against
  the shared token. The measurement reads whichever of the value/placeholder
  classes is on screen, so the gap has to hold in both states.

### `style::class::display::fn` (new class)

- `class` **`c_card_stack`** — `pub c_card_stack { ... }` — a flex column that owns the spacing of a card stack: `gap: var(--page-block-gap)` (mobile: `var(--page-block-gap-mobile)`), zeroes the block margins of its children and gives the first card a `margin-top`, including through transparent dynamic (`slot`, `[data-euv-dynamic-id]`) boundaries.

### `style::css::const` (global reset)

- `static` **`APP_GLOBAL_CSS_ROOT`** — `pub(crate) const APP_GLOBAL_CSS_ROOT: &str = ...` — now includes `-webkit-tap-highlight-color: transparent` on `:where(html)`, so the inherited tap highlight is gone without suppressing control feedback, text selection or keyboard focus.

### `component::accordion::view::enum`

- `enum` **`EuvAccordionType`** — `pub enum EuvAccordionType {`

### `component::accordion::view::fn`

- `fn` **`euv_accordion`** — `pub fn euv_accordion(node: VirtualNode<EuvAccordionProps>) -> VirtualNode {...}`

### `component::accordion::view::struct`

- `struct` **`EuvAccordionItem`** — `pub struct EuvAccordionItem {`
- `struct` **`EuvAccordionProps`** — `pub struct EuvAccordionProps {`

### `component::affix::view::fn`

- `fn` **`euv_affix`** — `pub fn euv_affix(node: VirtualNode<EuvAffixProps>) -> VirtualNode {...}`

### `component::affix::view::struct`

- `struct` **`EuvAffixProps`** — `pub struct EuvAffixProps {`

### `component::alert::view::enum`

- `enum` **`AlertVariant`** — `pub enum AlertVariant {`

### `component::alert::view::fn`

- `fn` **`euv_alert`** — `pub fn euv_alert(node: VirtualNode<EuvAlertProps>) -> VirtualNode {...}`
- `fn` **`euv_alert_icon`** — `pub fn euv_alert_icon(node: VirtualNode<EuvAlertIconProps>) -> VirtualNode {...}`
- `fn` **`euv_alert_title`** — `pub fn euv_alert_title(node: VirtualNode<EuvAlertTitleProps>) -> VirtualNode {...}`
- `fn` **`euv_alert_description`** — `pub fn euv_alert_description(node: VirtualNode<EuvAlertDescriptionProps>) -> VirtualNode {...}`
- `fn` **`euv_alert_action`** — `pub fn euv_alert_action(node: VirtualNode<EuvAlertActionProps>) -> VirtualNode {...}`

### `component::alert::view::struct`

- `struct` **`EuvAlertProps`** — `pub struct EuvAlertProps {`
- `struct` **`EuvAlertIconProps`** — `pub struct EuvAlertIconProps {`
- `struct` **`EuvAlertTitleProps`** — `pub struct EuvAlertTitleProps {`
- `struct` **`EuvAlertDescriptionProps`** — `pub struct EuvAlertDescriptionProps {`
- `struct` **`EuvAlertActionProps`** — `pub struct EuvAlertActionProps {`

### `component::alert_dialog::view::fn`

- `fn` **`euv_alert_dialog`** — `pub fn euv_alert_dialog(node: VirtualNode<EuvAlertDialogProps>) -> VirtualNode {...}`
- `fn` **`euv_alert_dialog_trigger`** — `pub fn euv_alert_dialog_trigger(node: VirtualNode<EuvAlertDialogTriggerProps>) -> VirtualNode {...}`
- `fn` **`euv_alert_dialog_overlay`** — `pub fn euv_alert_dialog_overlay(node: VirtualNode<EuvAlertDialogOverlayProps>) -> VirtualNode {...}`
- `fn` **`euv_alert_dialog_content`** — `pub fn euv_alert_dialog_content(node: VirtualNode<EuvAlertDialogContentProps>) -> VirtualNode {...}`
- `fn` **`euv_alert_dialog_header`** — `pub fn euv_alert_dialog_header(node: VirtualNode<EuvAlertDialogHeaderProps>) -> VirtualNode {...}`
- `fn` **`euv_alert_dialog_footer`** — `pub fn euv_alert_dialog_footer(node: VirtualNode<EuvAlertDialogFooterProps>) -> VirtualNode {...}`
- `fn` **`euv_alert_dialog_media`** — `pub fn euv_alert_dialog_media(node: VirtualNode<EuvAlertDialogMediaProps>) -> VirtualNode {...}`
- `fn` **`euv_alert_dialog_title`** — `pub fn euv_alert_dialog_title(node: VirtualNode<EuvAlertDialogTitleProps>) -> VirtualNode {...}`
- `fn` **`euv_alert_dialog_description`** — `pub fn euv_alert_dialog_description( node: VirtualNode<EuvAlertDialogDescriptionProps>, ) -> VirtualNode {...}`
- `fn` **`euv_alert_dialog_action`** — `pub fn euv_alert_dialog_action(node: VirtualNode<EuvAlertDialogActionProps>) -> VirtualNode {...}`
- `fn` **`euv_alert_dialog_cancel`** — `pub fn euv_alert_dialog_cancel(node: VirtualNode<EuvAlertDialogCancelProps>) -> VirtualNode {...}`

### `component::alert_dialog::view::struct`

- `struct` **`EuvAlertDialogProps`** — `pub struct EuvAlertDialogProps {`
- `struct` **`EuvAlertDialogTriggerProps`** — `pub struct EuvAlertDialogTriggerProps {`
- `struct` **`EuvAlertDialogOverlayProps`** — `pub struct EuvAlertDialogOverlayProps {`
- `struct` **`EuvAlertDialogContentProps`** — `pub struct EuvAlertDialogContentProps {`
- `struct` **`EuvAlertDialogMediaProps`** — `pub struct EuvAlertDialogMediaProps {`
- `struct` **`EuvAlertDialogHeaderProps`** — `pub struct EuvAlertDialogHeaderProps {`
- `struct` **`EuvAlertDialogFooterProps`** — `pub struct EuvAlertDialogFooterProps {`
- `struct` **`EuvAlertDialogTitleProps`** — `pub struct EuvAlertDialogTitleProps {`
- `struct` **`EuvAlertDialogDescriptionProps`** — `pub struct EuvAlertDialogDescriptionProps {`
- `struct` **`EuvAlertDialogActionProps`** — `pub struct EuvAlertDialogActionProps {`
- `struct` **`EuvAlertDialogCancelProps`** — `pub struct EuvAlertDialogCancelProps {`

### `component::anchor::view::fn`

- `fn` **`euv_anchor`** — `pub fn euv_anchor(node: VirtualNode<EuvAnchorProps>) -> VirtualNode {...}`

### `component::anchor::view::struct`

- `struct` **`EuvAnchorItem`** — `pub struct EuvAnchorItem {`
- `struct` **`EuvAnchorProps`** — `pub struct EuvAnchorProps {`

### `component::aspect_ratio::view::fn`

- `fn` **`euv_aspect_ratio`** — `pub fn euv_aspect_ratio(node: VirtualNode<EuvAspectRatioProps>) -> VirtualNode {...}`

### `component::aspect_ratio::view::struct`

- `struct` **`EuvAspectRatioProps`** — `pub struct EuvAspectRatioProps {`

### `component::attachment::view::enum`

- `enum` **`EuvAttachmentState`** — `pub enum EuvAttachmentState {`
- `enum` **`EuvAttachmentSize`** — `pub enum EuvAttachmentSize {`
- `enum` **`EuvAttachmentOrientation`** — `pub enum EuvAttachmentOrientation {`
- `enum` **`EuvAttachmentMediaVariant`** — `pub enum EuvAttachmentMediaVariant {`

### `component::attachment::view::fn`

- `fn` **`euv_attachment`** — `pub fn euv_attachment(node: VirtualNode<EuvAttachmentProps>) -> VirtualNode {...}`
- `fn` **`euv_attachment_media`** — `pub fn euv_attachment_media(node: VirtualNode<EuvAttachmentMediaProps>) -> VirtualNode {...}`
- `fn` **`euv_attachment_content`** — `pub fn euv_attachment_content(node: VirtualNode<EuvAttachmentContentProps>) -> VirtualNode {...}`
- `fn` **`euv_attachment_title`** — `pub fn euv_attachment_title(node: VirtualNode<EuvAttachmentTitleProps>) -> VirtualNode {...}`
- `fn` **`euv_attachment_description`** — `pub fn euv_attachment_description(node: VirtualNode<EuvAttachmentDescriptionProps>) -> VirtualNode {...}`
- `fn` **`euv_attachment_actions`** — `pub fn euv_attachment_actions(node: VirtualNode<EuvAttachmentActionsProps>) -> VirtualNode {...}`
- `fn` **`euv_attachment_action`** — `pub fn euv_attachment_action(node: VirtualNode<EuvAttachmentActionProps>) -> VirtualNode {...}`
- `fn` **`euv_attachment_trigger`** — `pub fn euv_attachment_trigger(node: VirtualNode<EuvAttachmentTriggerProps>) -> VirtualNode {...}`
- `fn` **`euv_attachment_group`** — `pub fn euv_attachment_group(node: VirtualNode<EuvAttachmentGroupProps>) -> VirtualNode {...}`

### `component::attachment::view::struct`

- `struct` **`EuvAttachmentProps`** — `pub struct EuvAttachmentProps {`
- `struct` **`EuvAttachmentMediaProps`** — `pub struct EuvAttachmentMediaProps {`
- `struct` **`EuvAttachmentContentProps`** — `pub struct EuvAttachmentContentProps {`
- `struct` **`EuvAttachmentTitleProps`** — `pub struct EuvAttachmentTitleProps {`
- `struct` **`EuvAttachmentDescriptionProps`** — `pub struct EuvAttachmentDescriptionProps {`
- `struct` **`EuvAttachmentActionsProps`** — `pub struct EuvAttachmentActionsProps {`
- `struct` **`EuvAttachmentActionProps`** — `pub struct EuvAttachmentActionProps {`
- `struct` **`EuvAttachmentTriggerProps`** — `pub struct EuvAttachmentTriggerProps {`
- `struct` **`EuvAttachmentGroupProps`** — `pub struct EuvAttachmentGroupProps {`

### `component::auto_complete::view::fn`

- `fn` **`auto_complete_matches`** — `pub fn auto_complete_matches(option: &EuvAutoCompleteOption, query: &str) -> bool {...}`
- `fn` **`auto_complete_active`** — `pub fn auto_complete_active<'a>( filtered: &'a [EuvAutoCompleteOption], query: &str, ) -> Option<&'a EuvAutoCompleteOption> {...}`
- `fn` **`euv_auto_complete`** — `pub fn euv_auto_complete(node: VirtualNode<EuvAutoCompleteProps>) -> VirtualNode {...}`

### `component::auto_complete::view::struct`

- `struct` **`EuvAutoCompleteOption`** — `pub struct EuvAutoCompleteOption {`
- `struct` **`EuvAutoCompleteProps`** — `pub struct EuvAutoCompleteProps {`
- `struct` **`EuvAutoCompleteInputProps`** — `pub(crate) struct EuvAutoCompleteInputProps {`

### `component::avatar::view::enum`

- `enum` **`EuvAvatarSize`** — `pub enum EuvAvatarSize {`

### `component::avatar::view::fn`

- `fn` **`euv_avatar`** — `pub fn euv_avatar(node: VirtualNode<EuvAvatarProps>) -> VirtualNode {...}`
- `fn` **`euv_avatar_fallback`** — `pub fn euv_avatar_fallback(node: VirtualNode<EuvAvatarFallbackProps>) -> VirtualNode {...}`
- `fn` **`euv_avatar_badge`** — `pub fn euv_avatar_badge(node: VirtualNode<EuvAvatarBadgeProps>) -> VirtualNode {...}`
- `fn` **`euv_avatar_group`** — `pub fn euv_avatar_group(node: VirtualNode<EuvAvatarGroupProps>) -> VirtualNode {...}`
- `fn` **`euv_avatar_group_count`** — `pub fn euv_avatar_group_count(node: VirtualNode<EuvAvatarGroupCountProps>) -> VirtualNode {...}`

### `component::avatar::view::impl`

- `fn` **`px`** — `pub fn px(&self) -> i32 {...}`

### `component::avatar::view::struct`

- `struct` **`EuvAvatarProps`** — `pub struct EuvAvatarProps {`
- `struct` **`EuvAvatarFallbackProps`** — `pub struct EuvAvatarFallbackProps {`
- `struct` **`EuvAvatarBadgeProps`** — `pub struct EuvAvatarBadgeProps {`
- `struct` **`EuvAvatarGroupProps`** — `pub struct EuvAvatarGroupProps {`
- `struct` **`EuvAvatarGroupCountProps`** — `pub struct EuvAvatarGroupCountProps {`

### `component::back_top::view::fn`

- `fn` **`euv_back_top`** — `pub fn euv_back_top(node: VirtualNode<EuvBackTopProps>) -> VirtualNode {...}`

### `component::back_top::view::struct`

- `struct` **`EuvBackTopProps`** — `pub struct EuvBackTopProps {`

### `component::badge::view::enum`

- `enum` **`EuvBadgeVariant`** — `pub enum EuvBadgeVariant {`

### `component::badge::view::fn`

- `fn` **`euv_badge`** — `pub fn euv_badge(node: VirtualNode<EuvBadgeProps>) -> VirtualNode {...}`

### `component::badge::view::struct`

- `struct` **`EuvBadgeProps`** — `pub struct EuvBadgeProps {`

### `component::breadcrumb::view::fn`

- `fn` **`euv_breadcrumb`** — `pub fn euv_breadcrumb(node: VirtualNode<EuvBreadcrumbProps>) -> VirtualNode {...}`
- `fn` **`euv_breadcrumb_list`** — `pub fn euv_breadcrumb_list(node: VirtualNode<EuvBreadcrumbListProps>) -> VirtualNode {...}`
- `fn` **`euv_breadcrumb_item`** — `pub fn euv_breadcrumb_item(node: VirtualNode<EuvBreadcrumbItemProps>) -> VirtualNode {...}`
- `fn` **`euv_breadcrumb_link`** — `pub fn euv_breadcrumb_link(node: VirtualNode<EuvBreadcrumbLinkProps>) -> VirtualNode {...}`
- `fn` **`euv_breadcrumb_page`** — `pub fn euv_breadcrumb_page(node: VirtualNode<EuvBreadcrumbPageProps>) -> VirtualNode {...}`
- `fn` **`euv_breadcrumb_separator`** — `pub fn euv_breadcrumb_separator(node: VirtualNode<EuvBreadcrumbSeparatorProps>) -> VirtualNode {...}`
- `fn` **`euv_breadcrumb_ellipsis`** — `pub fn euv_breadcrumb_ellipsis(node: VirtualNode<EuvBreadcrumbEllipsisProps>) -> VirtualNode {...}`

### `component::breadcrumb::view::struct`

- `struct` **`EuvBreadcrumbItem`** — `pub struct EuvBreadcrumbItem {`
- `struct` **`EuvBreadcrumbProps`** — `pub struct EuvBreadcrumbProps {`
- `struct` **`EuvBreadcrumbListProps`** — `pub struct EuvBreadcrumbListProps {`
- `struct` **`EuvBreadcrumbItemProps`** — `pub struct EuvBreadcrumbItemProps {`
- `struct` **`EuvBreadcrumbLinkProps`** — `pub struct EuvBreadcrumbLinkProps {`
- `struct` **`EuvBreadcrumbPageProps`** — `pub struct EuvBreadcrumbPageProps {`
- `struct` **`EuvBreadcrumbSeparatorProps`** — `pub struct EuvBreadcrumbSeparatorProps {`
- `struct` **`EuvBreadcrumbEllipsisProps`** — `pub struct EuvBreadcrumbEllipsisProps {`

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

### `component::bubble::view::enum`

- `enum` **`EuvBubbleVariant`** — `pub enum EuvBubbleVariant {`
- `enum` **`EuvBubbleAlign`** — `pub enum EuvBubbleAlign {`
- `enum` **`EuvBubbleSide`** — `pub enum EuvBubbleSide {`

### `component::bubble::view::fn`

- `fn` **`euv_bubble_group`** — `pub fn euv_bubble_group(node: VirtualNode<EuvBubbleGroupProps>) -> VirtualNode {...}`
- `fn` **`euv_bubble`** — `pub fn euv_bubble(node: VirtualNode<EuvBubbleProps>) -> VirtualNode {...}`
- `fn` **`euv_bubble_content`** — `pub fn euv_bubble_content(node: VirtualNode<EuvBubbleContentProps>) -> VirtualNode {...}`
- `fn` **`euv_bubble_reactions`** — `pub fn euv_bubble_reactions(node: VirtualNode<EuvBubbleReactionsProps>) -> VirtualNode {...}`

### `component::bubble::view::struct`

- `struct` **`EuvBubbleProps`** — `pub struct EuvBubbleProps {`
- `struct` **`EuvBubbleGroupProps`** — `pub struct EuvBubbleGroupProps {`
- `struct` **`EuvBubbleContentProps`** — `pub struct EuvBubbleContentProps {`
- `struct` **`EuvBubbleReactionsProps`** — `pub struct EuvBubbleReactionsProps {`

### `component::button::view::enum`

- `enum` **`EuvButtonVariant`** — `pub enum EuvButtonVariant {`
- `enum` **`EuvButtonSize`** — `pub enum EuvButtonSize {`

### `component::button::view::fn`

- `fn` **`euv_button`** — `pub fn euv_button(node: VirtualNode<EuvButtonProps>) -> VirtualNode {...}`
- `fn` **`euv_button_grouped`** — `pub fn euv_button_grouped(node: VirtualNode<EuvButtonGroupedProps>) -> VirtualNode {...}`
- `fn` **`button_class`** — `pub(crate) fn button_class(variant: EuvButtonVariant, size: EuvButtonSize) -> String {...}`
- `fn` **`euv_button_link`** — `pub fn euv_button_link(node: VirtualNode<EuvButtonLinkProps>) -> VirtualNode {...}`

### `component::button::view::struct`

- `struct` **`EuvButtonProps`** — `pub struct EuvButtonProps {`
- `struct` **`EuvButtonGroupedProps`** — `pub struct EuvButtonGroupedProps {`
- `struct` **`EuvButtonLinkProps`** — `pub struct EuvButtonLinkProps {`

### `component::button_group::view::enum`

- `enum` **`EuvButtonGroupOrientation`** — `pub enum EuvButtonGroupOrientation {`
- `enum` **`EuvButtonGroupSeparatorOrientation`** — `pub enum EuvButtonGroupSeparatorOrientation {`

### `component::button_group::view::fn`

- `fn` **`euv_button_group`** — `pub fn euv_button_group(node: VirtualNode<EuvButtonGroupProps>) -> VirtualNode {...}`
- `fn` **`euv_button_group_button`** — `pub fn euv_button_group_button(node: VirtualNode<EuvButtonGroupButtonProps>) -> VirtualNode {...}`
- `fn` **`euv_button_group_text`** — `pub fn euv_button_group_text(node: VirtualNode<EuvButtonGroupTextProps>) -> VirtualNode {...}`
- `fn` **`euv_button_group_separator`** — `pub fn euv_button_group_separator(node: VirtualNode<EuvButtonGroupSeparatorProps>) -> VirtualNode {...}`

### `component::button_group::view::struct`

- `struct` **`EuvButtonGroupProps`** — `pub struct EuvButtonGroupProps {`
- `struct` **`EuvButtonGroupTextProps`** — `pub struct EuvButtonGroupTextProps {`
- `struct` **`EuvButtonGroupSeparatorProps`** — `pub struct EuvButtonGroupSeparatorProps {`
- `struct` **`EuvButtonGroupButtonProps`** — `pub struct EuvButtonGroupButtonProps {`

### `component::calendar::view::enum`

- `enum` **`EuvCalendarWeekday`** — `pub enum EuvCalendarWeekday {`

### `component::calendar::view::fn`

- `fn` **`euv_calendar`** — `pub fn euv_calendar(node: VirtualNode<EuvCalendarProps>) -> VirtualNode {...}`
- `fn` **`euv_calendar_day_button`** — `pub fn euv_calendar_day_button(node: VirtualNode<EuvCalendarDayButtonProps>) -> VirtualNode {...}`
- `fn` **`on_calendar_day_click`** — `pub fn on_calendar_day_click(selected: Signal<u32>, day: u32) -> Option<Rc<dyn Fn(Event)>> {...}`

### `component::calendar::view::struct`

- `struct` **`EuvCalendarDay`** — `pub struct EuvCalendarDay {`
- `struct` **`EuvCalendarDayButtonProps`** — `pub struct EuvCalendarDayButtonProps {`
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

### `component::card::view::enum`

- `enum` **`EuvHeadingLevel`** — `pub enum EuvHeadingLevel {`

### `component::card::view::fn`

- `fn` **`euv_card`** — `pub fn euv_card(node: VirtualNode<EuvCardProps>) -> VirtualNode {...}`
- `fn` **`euv_card_header`** — `pub fn euv_card_header(node: VirtualNode<EuvCardHeaderProps>) -> VirtualNode {...}`
- `fn` **`euv_card_title`** — `pub fn euv_card_title(node: VirtualNode<EuvCardTitleProps>) -> VirtualNode {...}`
- `fn` **`euv_card_description`** — `pub fn euv_card_description(node: VirtualNode<EuvCardDescriptionProps>) -> VirtualNode {...}`
- `fn` **`euv_card_content`** — `pub fn euv_card_content(node: VirtualNode<EuvCardContentProps>) -> VirtualNode {...}`
- `fn` **`euv_card_footer`** — `pub fn euv_card_footer(node: VirtualNode<EuvCardFooterProps>) -> VirtualNode {...}`
- `fn` **`euv_card_action`** — `pub fn euv_card_action(node: VirtualNode<EuvCardActionProps>) -> VirtualNode {...}`

### `component::card::view::struct`

- `struct` **`EuvCardProps`** — `pub struct EuvCardProps {`
- `struct` **`EuvCardHeaderProps`** — `pub struct EuvCardHeaderProps {`
- `struct` **`EuvCardTitleProps`** — `pub struct EuvCardTitleProps {`
- `struct` **`EuvCardDescriptionProps`** — `pub struct EuvCardDescriptionProps {`
- `struct` **`EuvCardContentProps`** — `pub struct EuvCardContentProps {`
- `struct` **`EuvCardFooterProps`** — `pub struct EuvCardFooterProps {`
- `struct` **`EuvCardActionProps`** — `pub struct EuvCardActionProps {`

### `component::carousel::view::enum`

- `enum` **`EuvCarouselOrientation`** — `pub enum EuvCarouselOrientation {`

### `component::carousel::view::fn`

- `fn` **`euv_carousel`** — `pub fn euv_carousel(node: VirtualNode<EuvCarouselProps>) -> VirtualNode {...}`
- `fn` **`euv_carousel_content`** — `pub fn euv_carousel_content(node: VirtualNode<EuvCarouselContentProps>) -> VirtualNode {...}`
- `fn` **`euv_carousel_item`** — `pub fn euv_carousel_item(node: VirtualNode<EuvCarouselItemProps>) -> VirtualNode {...}`
- `fn` **`euv_carousel_next`** — `pub fn euv_carousel_next(node: VirtualNode<EuvCarouselNextProps>) -> VirtualNode {...}`
- `fn` **`euv_carousel_previous`** — `pub fn euv_carousel_previous(node: VirtualNode<EuvCarouselPreviousProps>) -> VirtualNode {...}`

### `component::carousel::view::struct`

- `struct` **`EuvCarouselSlide`** — `pub struct EuvCarouselSlide {`
- `struct` **`EuvCarouselContentProps`** — `pub struct EuvCarouselContentProps {`
- `struct` **`EuvCarouselItemProps`** — `pub struct EuvCarouselItemProps {`
- `struct` **`EuvCarouselNextProps`** — `pub struct EuvCarouselNextProps {`
- `struct` **`EuvCarouselPreviousProps`** — `pub struct EuvCarouselPreviousProps {`
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

### `component::chart::view::fn`

- `fn` **`euv_chart`** — `pub fn euv_chart(node: VirtualNode<EuvChartProps>) -> VirtualNode {...}`
- `fn` **`euv_chart_container`** — `pub fn euv_chart_container(node: VirtualNode<EuvChartContainerProps>) -> VirtualNode {...}`
- `fn` **`euv_chart_tooltip`** — `pub fn euv_chart_tooltip(node: VirtualNode<EuvChartTooltipProps>) -> VirtualNode {...}`
- `fn` **`euv_chart_tooltip_label`** — `pub fn euv_chart_tooltip_label(node: VirtualNode<EuvChartTooltipLabelProps>) -> VirtualNode {...}`
- `fn` **`euv_chart_tooltip_content`** — `pub fn euv_chart_tooltip_content(node: VirtualNode<EuvChartTooltipContentProps>) -> VirtualNode {...}`
- `fn` **`euv_chart_tooltip_item`** — `pub fn euv_chart_tooltip_item(node: VirtualNode<EuvChartTooltipItemProps>) -> VirtualNode {...}`
- `fn` **`euv_chart_legend`** — `pub fn euv_chart_legend(node: VirtualNode<EuvChartLegendProps>) -> VirtualNode {...}`
- `fn` **`euv_chart_legend_item`** — `pub fn euv_chart_legend_item(node: VirtualNode<EuvChartLegendItemProps>) -> VirtualNode {...}`
- `fn` **`euv_chart_legend_content`** — `pub fn euv_chart_legend_content(node: VirtualNode<EuvChartLegendContentProps>) -> VirtualNode {...}`

### `component::chart::view::struct`

- `struct` **`EuvChartProps`** — `pub struct EuvChartProps {`
- `struct` **`EuvChartTooltipItemProps`** — `pub struct EuvChartTooltipItemProps {`
- `struct` **`EuvChartLegendItemProps`** — `pub struct EuvChartLegendItemProps {`
- `struct` **`EuvChartTooltipProps`** — `pub struct EuvChartTooltipProps {`
- `struct` **`EuvChartTooltipLabelProps`** — `pub struct EuvChartTooltipLabelProps {`
- `struct` **`EuvChartLegendProps`** — `pub struct EuvChartLegendProps {`
- `struct` **`EuvChartContainerProps`** — `pub struct EuvChartContainerProps {`
- `struct` **`EuvChartTooltipContentProps`** — `pub struct EuvChartTooltipContentProps {`
- `struct` **`EuvChartLegendContentProps`** — `pub struct EuvChartLegendContentProps {`

### `component::checkbox::view::fn`

- `fn` **`euv_checkbox`** — `pub fn euv_checkbox(node: VirtualNode<EuvCheckboxProps>) -> VirtualNode {...}`

### `component::checkbox::view::struct`

- `struct` **`EuvCheckboxProps`** — `pub struct EuvCheckboxProps {`

### `component::checkbox_group::view::fn`

- `fn` **`euv_checkbox_group`** — `pub fn euv_checkbox_group(node: VirtualNode<EuvCheckboxGroupProps>) -> VirtualNode {...}`

### `component::checkbox_group::view::struct`

- `struct` **`EuvCheckboxGroupOption`** — `pub struct EuvCheckboxGroupOption {`
- `struct` **`EuvCheckboxGroupProps`** — `pub struct EuvCheckboxGroupProps {`

### `component::code_block::view::enum`

- `enum` **`EuvCodeBlockVariant`** — `pub enum EuvCodeBlockVariant {`
- `enum` **`EuvCodeBlockSize`** — `pub enum EuvCodeBlockSize {`
- `enum` **`EuvCodeBlockLineVariant`** — `pub enum EuvCodeBlockLineVariant {`

### `component::code_block::view::fn`

- `fn` **`euv_code_block`** — `pub fn euv_code_block(node: VirtualNode<EuvCodeBlockProps>) -> VirtualNode {...}`
- `fn` **`euv_code_block_header`** — `pub fn euv_code_block_header(node: VirtualNode<EuvCodeBlockHeaderProps>) -> VirtualNode {...}`
- `fn` **`euv_code_block_title`** — `pub fn euv_code_block_title(node: VirtualNode<EuvCodeBlockTitleProps>) -> VirtualNode {...}`
- `fn` **`euv_code_block_actions`** — `pub fn euv_code_block_actions(node: VirtualNode<EuvCodeBlockActionsProps>) -> VirtualNode {...}`
- `fn` **`euv_code_block_copy_button`** — `pub fn euv_code_block_copy_button(node: VirtualNode<EuvCodeBlockCopyButtonProps>) -> VirtualNode {...}`
- `fn` **`euv_code_block_content`** — `pub fn euv_code_block_content(node: VirtualNode<EuvCodeBlockContentProps>) -> VirtualNode {...}`
- `fn` **`euv_code_block_line`** — `pub fn euv_code_block_line(node: VirtualNode<EuvCodeBlockLineProps>) -> VirtualNode {...}`
- `fn` **`euv_code_block_footer`** — `pub fn euv_code_block_footer(node: VirtualNode<EuvCodeBlockFooterProps>) -> VirtualNode {...}`

### `component::code_block::view::struct`

- `struct` **`EuvCodeBlockProps`** — `pub struct EuvCodeBlockProps {`
- `struct` **`EuvCodeBlockHeaderProps`** — `pub struct EuvCodeBlockHeaderProps {`
- `struct` **`EuvCodeBlockTitleProps`** — `pub struct EuvCodeBlockTitleProps {`
- `struct` **`EuvCodeBlockActionsProps`** — `pub struct EuvCodeBlockActionsProps {`
- `struct` **`EuvCodeBlockCopyButtonProps`** — `pub struct EuvCodeBlockCopyButtonProps {`
- `struct` **`EuvCodeBlockContentProps`** — `pub struct EuvCodeBlockContentProps {`
- `struct` **`EuvCodeBlockLineProps`** — `pub struct EuvCodeBlockLineProps {`
- `struct` **`EuvCodeBlockFooterProps`** — `pub struct EuvCodeBlockFooterProps {`

### `component::collapse::view::fn`

- `fn` **`euv_collapse`** — `pub fn euv_collapse(node: VirtualNode<EuvCollapseProps>) -> VirtualNode {...}`

### `component::collapse::view::struct`

- `struct` **`EuvCollapseItem`** — `pub struct EuvCollapseItem {`
- `struct` **`EuvCollapseProps`** — `pub struct EuvCollapseProps {`

### `component::collapsible::view::fn`

- `fn` **`euv_collapsible`** — `pub fn euv_collapsible(node: VirtualNode<EuvCollapsibleProps>) -> VirtualNode {...}`
- `fn` **`euv_collapsible_trigger`** — `pub fn euv_collapsible_trigger(node: VirtualNode<EuvCollapsibleTriggerProps>) -> VirtualNode {...}`
- `fn` **`euv_collapsible_content`** — `pub fn euv_collapsible_content(node: VirtualNode<EuvCollapsibleContentProps>) -> VirtualNode {...}`

### `component::collapsible::view::struct`

- `struct` **`EuvCollapsibleProps`** — `pub struct EuvCollapsibleProps {`
- `struct` **`EuvCollapsibleTriggerProps`** — `pub struct EuvCollapsibleTriggerProps {`
- `struct` **`EuvCollapsibleContentProps`** — `pub struct EuvCollapsibleContentProps {`

### `component::combobox::view::fn`

- `fn` **`euv_combobox`** — `pub fn euv_combobox(node: VirtualNode<EuvComboboxProps>) -> VirtualNode {...}`
- `fn` **`euv_combobox_chips`** — `pub fn euv_combobox_chips(node: VirtualNode<EuvComboboxChipsProps>) -> VirtualNode {...}`
- `fn` **`euv_combobox_chip_list`** — `pub fn euv_combobox_chip_list(node: VirtualNode<EuvComboboxChipListProps>) -> VirtualNode {...}`
- `fn` **`euv_combobox_chip`** — `pub fn euv_combobox_chip(node: VirtualNode<EuvComboboxChipProps>) -> VirtualNode {...}`
- `fn` **`euv_combobox_chips_input`** — `pub fn euv_combobox_chips_input(node: VirtualNode<EuvComboboxChipsInputProps>) -> VirtualNode {...}`
- `fn` **`euv_combobox_value`** — `pub fn euv_combobox_value(node: VirtualNode<EuvComboboxValueProps>) -> VirtualNode {...}`
- `fn` **`euv_combobox_trigger`** — `pub fn euv_combobox_trigger(node: VirtualNode<EuvComboboxTriggerProps>) -> VirtualNode {...}`
- `fn` **`euv_combobox_input`** — `pub fn euv_combobox_input(node: VirtualNode<EuvComboboxInputProps>) -> VirtualNode {...}`
- `fn` **`euv_combobox_content`** — `pub fn euv_combobox_content(node: VirtualNode<EuvComboboxContentProps>) -> VirtualNode {...}`
- `fn` **`euv_combobox_list`** — `pub fn euv_combobox_list(node: VirtualNode<EuvComboboxListProps>) -> VirtualNode {...}`
- `fn` **`euv_combobox_item`** — `pub fn euv_combobox_item(node: VirtualNode<EuvComboboxItemProps>) -> VirtualNode {...}`
- `fn` **`euv_combobox_group`** — `pub fn euv_combobox_group(node: VirtualNode<EuvComboboxGroupProps>) -> VirtualNode {...}`
- `fn` **`euv_combobox_label`** — `pub fn euv_combobox_label(node: VirtualNode<EuvComboboxLabelProps>) -> VirtualNode {...}`
- `fn` **`euv_combobox_empty`** — `pub fn euv_combobox_empty(node: VirtualNode<EuvComboboxEmptyProps>) -> VirtualNode {...}`
- `fn` **`euv_combobox_separator`** — `pub fn euv_combobox_separator(node: VirtualNode<EuvComboboxSeparatorProps>) -> VirtualNode {...}`
- `fn` **`euv_combobox_clear`** — `pub fn euv_combobox_clear(node: VirtualNode<EuvComboboxClearProps>) -> VirtualNode {...}`

### `component::combobox::view::struct`

- `struct` **`EuvComboboxProps`** — `pub struct EuvComboboxProps {`
- `struct` **`EuvComboboxTriggerProps`** — `pub struct EuvComboboxTriggerProps {`
- `struct` **`EuvComboboxInputProps`** — `pub struct EuvComboboxInputProps {`
- `struct` **`EuvComboboxContentProps`** — `pub struct EuvComboboxContentProps {`
- `struct` **`EuvComboboxListProps`** — `pub struct EuvComboboxListProps {`
- `struct` **`EuvComboboxItemProps`** — `pub struct EuvComboboxItemProps {`
- `struct` **`EuvComboboxGroupProps`** — `pub struct EuvComboboxGroupProps {`
- `struct` **`EuvComboboxLabelProps`** — `pub struct EuvComboboxLabelProps {`
- `struct` **`EuvComboboxEmptyProps`** — `pub struct EuvComboboxEmptyProps {`
- `struct` **`EuvComboboxSeparatorProps`** — `pub struct EuvComboboxSeparatorProps {`
- `struct` **`EuvComboboxClearProps`** — `pub struct EuvComboboxClearProps {`
- `struct` **`EuvComboboxChipsProps`** — `pub struct EuvComboboxChipsProps {`
- `struct` **`EuvComboboxChipListProps`** — `pub struct EuvComboboxChipListProps {`
- `struct` **`EuvComboboxChipProps`** — `pub struct EuvComboboxChipProps {`
- `struct` **`EuvComboboxChipsInputProps`** — `pub struct EuvComboboxChipsInputProps {`
- `struct` **`EuvComboboxValueProps`** — `pub struct EuvComboboxValueProps {`

### `component::command::view::fn`

- `fn` **`euv_command`** — `pub fn euv_command(node: VirtualNode<EuvCommandProps>) -> VirtualNode {...}`
- `fn` **`euv_command_input`** — `pub fn euv_command_input(node: VirtualNode<EuvCommandInputProps>) -> VirtualNode {...}`
- `fn` **`euv_command_list`** — `pub fn euv_command_list(node: VirtualNode<EuvCommandListProps>) -> VirtualNode {...}`
- `fn` **`euv_command_empty`** — `pub fn euv_command_empty(node: VirtualNode<EuvCommandEmptyProps>) -> VirtualNode {...}`
- `fn` **`euv_command_group`** — `pub fn euv_command_group(node: VirtualNode<EuvCommandGroupProps>) -> VirtualNode {...}`
- `fn` **`euv_command_item`** — `pub fn euv_command_item(node: VirtualNode<EuvCommandItemProps>) -> VirtualNode {...}`
- `fn` **`euv_command_separator`** — `pub fn euv_command_separator(node: VirtualNode<EuvCommandSeparatorProps>) -> VirtualNode {...}`
- `fn` **`euv_command_shortcut`** — `pub fn euv_command_shortcut(node: VirtualNode<EuvCommandShortcutProps>) -> VirtualNode {...}`

### `component::command::view::struct`

- `struct` **`EuvCommandProps`** — `pub struct EuvCommandProps {`
- `struct` **`EuvCommandInputProps`** — `pub struct EuvCommandInputProps {`
- `struct` **`EuvCommandListProps`** — `pub struct EuvCommandListProps {`
- `struct` **`EuvCommandEmptyProps`** — `pub struct EuvCommandEmptyProps {`
- `struct` **`EuvCommandGroupProps`** — `pub struct EuvCommandGroupProps {`
- `struct` **`EuvCommandItemProps`** — `pub struct EuvCommandItemProps {`
- `struct` **`EuvCommandSeparatorProps`** — `pub struct EuvCommandSeparatorProps {`
- `struct` **`EuvCommandShortcutProps`** — `pub struct EuvCommandShortcutProps {`

### `component::context_menu::view::fn`

- `fn` **`context_menu_next_index`** — `pub(crate) fn context_menu_next_index( labels: &[String], current: Option<usize>, key: &str, ) -> Option<usize> {...}`
- `fn` **`context_menu_direction_keys`** — `pub(crate) fn context_menu_direction_keys(rtl: bool) -> (&'static str, &'static str) {...}`
- `fn` **`context_menu_sub_position`** — `pub(crate) fn context_menu_sub_position( anchor: (f64, f64, f64), panel: (f64, f64), viewport: (f64, f64), rtl: bool, ) -> (f64, f64) {...}`
- `fn` **`euv_context_menu`** — `pub fn euv_context_menu(node: VirtualNode<EuvContextMenuProps>) -> VirtualNode {...}`
- `fn` **`euv_context_menu_trigger`** — `pub fn euv_context_menu_trigger(node: VirtualNode<EuvContextMenuTriggerProps>) -> VirtualNode {...}`
- `fn` **`euv_context_menu_content`** — `pub fn euv_context_menu_content(node: VirtualNode<EuvContextMenuContentProps>) -> VirtualNode {...}`
- `fn` **`euv_context_menu_group`** — `pub fn euv_context_menu_group(node: VirtualNode<EuvContextMenuGroupProps>) -> VirtualNode {...}`
- `fn` **`use_context_menu_radio_group`** — `pub fn use_context_menu_radio_group( value: Option<Signal<String>>, default_value: &'static str, on_value_change: Option<Rc<dyn Fn(String)>>, ) -> EuvContextMenuRadioGroupState {...}`
- `fn` **`activate_context_menu_radio`** — `pub(crate) fn activate_context_menu_radio(props: &EuvContextMenuRadioItemProps) -> bool {...}`
- `fn` **`euv_context_menu_radio_group`** — `pub fn euv_context_menu_radio_group( node: VirtualNode<EuvContextMenuRadioGroupProps>, ) -> VirtualNode {...}`
- `fn` **`use_context_menu_sub_binding`** — `pub(crate) fn use_context_menu_sub_binding(parent_open: Signal<bool>, open: Signal<bool>) {...}`
- `fn` **`euv_context_menu_sub`** — `pub fn euv_context_menu_sub(node: VirtualNode<EuvContextMenuSubProps>) -> VirtualNode {...}`
- `fn` **`euv_context_menu_sub_trigger`** — `pub fn euv_context_menu_sub_trigger( node: VirtualNode<EuvContextMenuSubTriggerProps>, ) -> VirtualNode {...}`
- `fn` **`euv_context_menu_sub_content`** — `pub fn euv_context_menu_sub_content( node: VirtualNode<EuvContextMenuSubContentProps>, ) -> VirtualNode {...}`
- `fn` **`euv_context_menu_item`** — `pub fn euv_context_menu_item(node: VirtualNode<EuvContextMenuItemProps>) -> VirtualNode {...}`
- `fn` **`euv_context_menu_checkbox_item`** — `pub fn euv_context_menu_checkbox_item( node: VirtualNode<EuvContextMenuCheckboxItemProps>, ) -> VirtualNode {...}`
- `fn` **`euv_context_menu_radio_item`** — `pub fn euv_context_menu_radio_item(node: VirtualNode<EuvContextMenuRadioItemProps>) -> VirtualNode {...}`
- `fn` **`euv_context_menu_label`** — `pub fn euv_context_menu_label(node: VirtualNode<EuvContextMenuLabelProps>) -> VirtualNode {...}`
- `fn` **`euv_context_menu_separator`** — `pub fn euv_context_menu_separator(node: VirtualNode<EuvContextMenuSeparatorProps>) -> VirtualNode {...}`
- `fn` **`euv_context_menu_shortcut`** — `pub fn euv_context_menu_shortcut(node: VirtualNode<EuvContextMenuShortcutProps>) -> VirtualNode {...}`
- `fn` **`context_menu_hover_eligible`** — `pub(crate) fn context_menu_hover_eligible( pointer: &str, hover: bool, disabled: bool, enabled: bool, parent: bool, ) -> bool {...}`
- `fn` **`context_menu_hover_intent`** — `pub(crate) fn context_menu_hover_intent( open: bool, trigger: bool, branch: bool, bridge: bool, eligible: bool, ) -> Option<bool> {...}`
- `fn` **`context_menu_hover_bridge`** — `pub(crate) fn context_menu_hover_bridge( point: (f64, f64), exit: (f64, f64), trigger: (f64, f64, f64, f64), panel: (f64, f64, f64, f64), ) -> bool {...}`

### `component::context_menu::view::struct`

- `struct` **`ContextMenuLongPress`** — `pub(crate) struct ContextMenuLongPress {`
- `struct` **`EuvContextMenuProps`** — `pub struct EuvContextMenuProps {`
- `struct` **`EuvContextMenuTriggerProps`** — `pub struct EuvContextMenuTriggerProps {`
- `struct` **`EuvContextMenuContentProps`** — `pub struct EuvContextMenuContentProps {`
- `struct` **`EuvContextMenuGroupProps`** — `pub struct EuvContextMenuGroupProps {`
- `struct` **`EuvContextMenuRadioGroupProps`** — `pub struct EuvContextMenuRadioGroupProps {`
- `struct` **`EuvContextMenuRadioGroupState`** — `pub struct EuvContextMenuRadioGroupState {`
- `struct` **`EuvContextMenuSubProps`** — `pub struct EuvContextMenuSubProps {`
- `struct` **`ContextMenuSubBindingScope`** — `pub(crate) struct ContextMenuSubBindingScope {`
- `struct` **`ContextMenuSubBinding`** — `pub(crate) struct ContextMenuSubBinding {`
- `struct` **`EuvContextMenuSubTriggerProps`** — `pub struct EuvContextMenuSubTriggerProps {`
- `struct` **`EuvContextMenuSubContentProps`** — `pub struct EuvContextMenuSubContentProps {`
- `struct` **`EuvContextMenuItemProps`** — `pub struct EuvContextMenuItemProps {`
- `struct` **`EuvContextMenuCheckboxItemProps`** — `pub struct EuvContextMenuCheckboxItemProps {`
- `struct` **`EuvContextMenuRadioItemProps`** — `pub struct EuvContextMenuRadioItemProps {`
- `struct` **`EuvContextMenuLabelProps`** — `pub struct EuvContextMenuLabelProps {`
- `struct` **`EuvContextMenuSeparatorProps`** — `pub struct EuvContextMenuSeparatorProps {`
- `struct` **`EuvContextMenuShortcutProps`** — `pub struct EuvContextMenuShortcutProps {`
- `struct` **`ContextMenuSubHover`** — `pub(crate) struct ContextMenuSubHover {`
- `struct` **`ContextMenuHoverOwner`** — `pub(crate) struct ContextMenuHoverOwner {`

### `component::context_menu::view::impl`

- `fn` **`start`** — `pub(crate) fn start(&mut self, disabled: bool, count: u32, x: i32, y: i32, now: f64) {...}`
- `fn` **`moved`** — `pub(crate) fn moved(&mut self, count: u32, x: i32, y: i32) {...}`
- `fn` **`finish`** — `pub(crate) fn finish(&mut self, now: f64) -> Option<(i32, i32)> {...}`
- `fn` **`cancel`** — `pub(crate) fn cancel(&mut self) {...}`

### `component::context_menu::view::static`

- `static` **`CONTEXT_MENU_SUB_PARENTS`** — `pub(crate) static CONTEXT_MENU_SUB_PARENTS: RefCell<HashMap<usize, Weak<ContextMenuHoverOwner>>> = RefCell::new(HashMap::new());`

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

### `component::direction::view::enum`

- `enum` **`EuvDirection`** — `pub enum EuvDirection {`

### `component::direction::view::fn`

- `fn` **`euv_direction`** — `pub fn euv_direction(node: VirtualNode<EuvDirectionProps>) -> VirtualNode {...}`
- `fn` **`euv_direction_provider`** — `pub fn euv_direction_provider(node: VirtualNode<EuvDirectionProviderProps>) -> VirtualNode {...}`

### `component::direction::view::struct`

- `struct` **`EuvDirectionProps`** — `pub struct EuvDirectionProps {`
- `struct` **`EuvDirectionProviderProps`** — `pub struct EuvDirectionProviderProps {`

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
- `fn` **`euv_drawer_trigger`** — `pub fn euv_drawer_trigger(node: VirtualNode<EuvDrawerTriggerProps>) -> VirtualNode {...}`
- `fn` **`euv_drawer_content`** — `pub fn euv_drawer_content(node: VirtualNode<EuvDrawerContentProps>) -> VirtualNode {...}`
- `fn` **`euv_drawer_header`** — `pub fn euv_drawer_header(node: VirtualNode<EuvDrawerHeaderProps>) -> VirtualNode {...}`
- `fn` **`euv_drawer_footer`** — `pub fn euv_drawer_footer(node: VirtualNode<EuvDrawerFooterProps>) -> VirtualNode {...}`
- `fn` **`euv_drawer_title`** — `pub fn euv_drawer_title(node: VirtualNode<EuvDrawerTitleProps>) -> VirtualNode {...}`
- `fn` **`euv_drawer_description`** — `pub fn euv_drawer_description(node: VirtualNode<EuvDrawerDescriptionProps>) -> VirtualNode {...}`
- `fn` **`euv_drawer_close`** — `pub fn euv_drawer_close(node: VirtualNode<EuvDrawerCloseProps>) -> VirtualNode {...}`
- `fn` **`euv_drawer_overlay`** — `pub fn euv_drawer_overlay(node: VirtualNode<EuvDrawerOverlayProps>) -> VirtualNode {...}`

### `component::drawer::view::struct`

- `struct` **`EuvDrawerProps`** — `pub struct EuvDrawerProps {`
- `struct` **`EuvDrawerTriggerProps`** — `pub struct EuvDrawerTriggerProps {`
- `struct` **`EuvDrawerContentProps`** — `pub struct EuvDrawerContentProps {`
- `struct` **`EuvDrawerCloseProps`** — `pub struct EuvDrawerCloseProps {`
- `struct` **`EuvDrawerHeaderProps`** — `pub struct EuvDrawerHeaderProps {`
- `struct` **`EuvDrawerFooterProps`** — `pub struct EuvDrawerFooterProps {`
- `struct` **`EuvDrawerTitleProps`** — `pub struct EuvDrawerTitleProps {`
- `struct` **`EuvDrawerDescriptionProps`** — `pub struct EuvDrawerDescriptionProps {`
- `struct` **`EuvDrawerOverlayProps`** — `pub struct EuvDrawerOverlayProps {`

### `component::dropdown::view::fn`

- `fn` **`euv_dropdown`** — `pub fn euv_dropdown(node: VirtualNode<EuvDropdownProps>) -> VirtualNode {...}`
- `fn` **`euv_dropdown_menu`** — `pub fn euv_dropdown_menu(node: VirtualNode<EuvDropdownMenuProps>) -> VirtualNode {...}`
- `fn` **`euv_dropdown_menu_content`** — `pub fn euv_dropdown_menu_content(node: VirtualNode<EuvDropdownMenuContentProps>) -> VirtualNode {...}`
- `fn` **`dropdown_portal_target`** — `pub(crate) fn dropdown_portal_target(open: Signal<bool>) -> String {...}`
- `fn` **`use_dropdown_menu_parent_binding`** — `pub(crate) fn use_dropdown_menu_parent_binding( open: Signal<bool>, parent_open: Option<Signal<bool>>, ) {...}`
- `fn` **`dropdown_menu_parent_binding`** — `pub(crate) fn dropdown_menu_parent_binding( open: Signal<bool>, parent_open: Option<Signal<bool>>, ) -> Box<dyn FnOnce()> {...}`
- `fn` **`euv_dropdown_trigger`** — `pub fn euv_dropdown_trigger(node: VirtualNode<EuvDropdownTriggerProps>) -> VirtualNode {...}`
- `fn` **`dropdown_direction_keys`** — `pub(crate) fn dropdown_direction_keys(rtl: bool) -> (&'static str, &'static str) {...}`
- `fn` **`euv_dropdown_menu_item`** — `pub fn euv_dropdown_menu_item(node: VirtualNode<EuvDropdownMenuItemProps>) -> VirtualNode {...}`
- `fn` **`euv_dropdown_menu_group`** — `pub fn euv_dropdown_menu_group(node: VirtualNode<EuvDropdownMenuGroupProps>) -> VirtualNode {...}`
- `fn` **`euv_dropdown_menu_checkbox_item`** — `pub fn euv_dropdown_menu_checkbox_item( node: VirtualNode<EuvDropdownMenuCheckboxItemProps>, ) -> VirtualNode {...}`
- `fn` **`use_dropdown_menu_radio_group`** — `pub fn use_dropdown_menu_radio_group( value: Option<Signal<String>>, default_value: &str, on_value_change: Option<Rc<dyn Fn(String)>>, ) -> EuvDropdownMenuRadioGroupState {...}`
- `fn` **`activate_dropdown_menu_radio`** — `pub(crate) fn activate_dropdown_menu_radio(props: &EuvDropdownMenuRadioItemProps) -> bool {...}`
- `fn` **`euv_dropdown_menu_radio_group`** — `pub fn euv_dropdown_menu_radio_group( node: VirtualNode<EuvDropdownMenuRadioGroupProps>, ) -> VirtualNode {...}`
- `fn` **`euv_dropdown_menu_radio_item`** — `pub fn euv_dropdown_menu_radio_item( node: VirtualNode<EuvDropdownMenuRadioItemProps>, ) -> VirtualNode {...}`
- `fn` **`use_dropdown_menu_sub_binding`** — `pub(crate) fn use_dropdown_menu_sub_binding(parent_open: Signal<bool>, open: Signal<bool>) {...}`
- `fn` **`euv_dropdown_menu_sub`** — `pub fn euv_dropdown_menu_sub(node: VirtualNode<EuvDropdownMenuSubProps>) -> VirtualNode {...}`
- `fn` **`euv_dropdown_menu_sub_trigger`** — `pub fn euv_dropdown_menu_sub_trigger( node: VirtualNode<EuvDropdownMenuSubTriggerProps>, ) -> VirtualNode {...}`
- `fn` **`euv_dropdown_menu_sub_content`** — `pub fn euv_dropdown_menu_sub_content( node: VirtualNode<EuvDropdownMenuSubContentProps>, ) -> VirtualNode {...}`
- `fn` **`euv_dropdown_menu_label`** — `pub fn euv_dropdown_menu_label(node: VirtualNode<EuvDropdownMenuLabelProps>) -> VirtualNode {...}`
- `fn` **`euv_dropdown_menu_separator`** — `pub fn euv_dropdown_menu_separator( node: VirtualNode<EuvDropdownMenuSeparatorProps>, ) -> VirtualNode {...}`
- `fn` **`euv_dropdown_menu_shortcut`** — `pub fn euv_dropdown_menu_shortcut(node: VirtualNode<EuvDropdownMenuShortcutProps>) -> VirtualNode {...}`
- `fn` **`dropdown_next_index`** — `pub(crate) fn dropdown_next_index( labels: &[String], current: Option<usize>, query: &str, ) -> Option<usize> {...}`
- `fn` **`dropdown_search_prefix`** — `pub(crate) fn dropdown_search_prefix(previous: &str, key: &str, elapsed: f64) -> String {...}`
- `fn` **`dropdown_geometry_policy`** — `pub(crate) fn dropdown_geometry_policy(css: &Css) -> DropdownGeometryPolicy {...}`
- `fn` **`dropdown_popup_width`** — `pub(crate) fn dropdown_popup_width( anchor_width: f64, available_width: f64, scale: f64, content_width: bool, submenu: bool, ) -> Option<f64> {...}`
- `fn` **`dropdown_popup_position`** — `pub(crate) fn dropdown_popup_position( anchor: (f64, f64, f64, f64), size: (f64, f64), viewport: (f64, f64), gap: f64, ) -> (f64, f64, f64) {...}`
- `fn` **`dropdown_popup_position_aligned`** — `pub(crate) fn dropdown_popup_position_aligned( anchor: (f64, f64, f64, f64), size: (f64, f64), viewport: (f64, f64), gap: f64, align_start: bool, ) -> (f64, f64, f64) {...}`
- `fn` **`dropdown_sub_position`** — `pub(crate) fn dropdown_sub_position( anchor: (f64, f64, f64), size: (f64, f64), viewport: (f64, f64), rtl: bool, ) -> (f64, f64, f64) {...}`
- `fn` **`dropdown_sub_trigger_exit`** — `pub(crate) fn dropdown_sub_trigger_exit(open: bool, key: &str, rtl: bool) -> bool {...}`
- `fn` **`dropdown_hover_eligible`** — `pub(crate) fn dropdown_hover_eligible( pointer: &str, hover: bool, disabled: bool, enabled: bool, parent: bool, ) -> bool {...}`
- `fn` **`dropdown_hover_intent`** — `pub(crate) fn dropdown_hover_intent( open: bool, trigger: bool, branch: bool, bridge: bool, eligible: bool, ) -> Option<bool> {...}`
- `fn` **`dropdown_hover_bridge`** — `pub(crate) fn dropdown_hover_bridge( point: (f64, f64), exit: (f64, f64), trigger: (f64, f64, f64, f64), panel: (f64, f64, f64, f64), ) -> bool {...}`

### `component::dropdown::view::struct`

- `struct` **`DropdownGeometryPolicy`** — `pub(crate) struct DropdownGeometryPolicy {`
- `struct` **`EuvDropdownItem`** — `pub struct EuvDropdownItem {`
- `struct` **`EuvDropdownProps`** — `pub struct EuvDropdownProps {`
- `struct` **`EuvDropdownMenuProps`** — `pub struct EuvDropdownMenuProps {`
- `struct` **`EuvDropdownMenuContentProps`** — `pub struct EuvDropdownMenuContentProps {`
- `struct` **`EuvDropdownTriggerProps`** — `pub struct EuvDropdownTriggerProps {`
- `struct` **`EuvDropdownMenuGroupProps`** — `pub struct EuvDropdownMenuGroupProps {`
- `struct` **`EuvDropdownMenuCheckboxItemProps`** — `pub struct EuvDropdownMenuCheckboxItemProps {`
- `struct` **`EuvDropdownMenuRadioGroupProps`** — `pub struct EuvDropdownMenuRadioGroupProps {`
- `struct` **`EuvDropdownMenuRadioGroupState`** — `pub struct EuvDropdownMenuRadioGroupState {`
- `struct` **`EuvDropdownMenuRadioItemProps`** — `pub struct EuvDropdownMenuRadioItemProps {`
- `struct` **`EuvDropdownMenuSubProps`** — `pub struct EuvDropdownMenuSubProps {`
- `struct` **`EuvDropdownMenuSubTriggerProps`** — `pub struct EuvDropdownMenuSubTriggerProps {`
- `struct` **`EuvDropdownMenuSubContentProps`** — `pub struct EuvDropdownMenuSubContentProps {`
- `struct` **`EuvDropdownMenuItemProps`** — `pub struct EuvDropdownMenuItemProps {`
- `struct` **`EuvDropdownMenuLabelProps`** — `pub struct EuvDropdownMenuLabelProps {`
- `struct` **`EuvDropdownMenuSeparatorProps`** — `pub struct EuvDropdownMenuSeparatorProps {`
- `struct` **`EuvDropdownMenuShortcutProps`** — `pub struct EuvDropdownMenuShortcutProps {`

### `component::dropdown::view::static`

- `static` **`DROPDOWN_SUB_PARENTS`** — `pub(crate) static DROPDOWN_SUB_PARENTS: RefCell<HashMap<usize, Weak<Cell<Signal<bool>>>>> = RefCell::new(HashMap::new());`

### `component::dropdown::view::type`

- `type` **`DropdownParentBinding`** — `pub(crate) type DropdownParentBinding = (Signal<bool>, Option<Signal<bool>>, Box<dyn FnOnce()>);`
- `type` **`DropdownSubParentBinding`** — `pub(crate) type DropdownSubParentBinding = (Signal<bool>, Signal<bool>, usize, usize);`

### `component::empty::view::enum`

- `enum` **`EuvEmptyMediaVariant`** — `pub enum EuvEmptyMediaVariant {`

### `component::empty::view::fn`

- `fn` **`euv_empty`** — `pub fn euv_empty(node: VirtualNode<EuvEmptyProps>) -> VirtualNode {...}`
- `fn` **`euv_empty_header`** — `pub fn euv_empty_header(node: VirtualNode<EuvEmptyHeaderProps>) -> VirtualNode {...}`
- `fn` **`euv_empty_media`** — `pub fn euv_empty_media(node: VirtualNode<EuvEmptyMediaProps>) -> VirtualNode {...}`
- `fn` **`euv_empty_title`** — `pub fn euv_empty_title(node: VirtualNode<EuvEmptyTitleProps>) -> VirtualNode {...}`
- `fn` **`euv_empty_description`** — `pub fn euv_empty_description(node: VirtualNode<EuvEmptyDescriptionProps>) -> VirtualNode {...}`
- `fn` **`euv_empty_content`** — `pub fn euv_empty_content(node: VirtualNode<EuvEmptyContentProps>) -> VirtualNode {...}`

### `component::empty::view::struct`

- `struct` **`EuvEmptyProps`** — `pub struct EuvEmptyProps {`
- `struct` **`EuvEmptyHeaderProps`** — `pub struct EuvEmptyHeaderProps {`
- `struct` **`EuvEmptyMediaProps`** — `pub struct EuvEmptyMediaProps {`
- `struct` **`EuvEmptyTitleProps`** — `pub struct EuvEmptyTitleProps {`
- `struct` **`EuvEmptyDescriptionProps`** — `pub struct EuvEmptyDescriptionProps {`
- `struct` **`EuvEmptyContentProps`** — `pub struct EuvEmptyContentProps {`

### `component::feature_grid::view::fn`

- `fn` **`euv_feature_grid`** — `pub fn euv_feature_grid(node: VirtualNode<EuvFeatureGridProps>) -> VirtualNode {...}`

### `component::feature_grid::view::struct`

- `struct` **`EuvFeature`** — `pub struct EuvFeature {`
- `struct` **`EuvFeatureGridProps`** — `pub struct EuvFeatureGridProps {`

### `component::field::view::enum`

- `enum` **`EuvFieldOrientation`** — `pub enum EuvFieldOrientation {`
- `enum` **`EuvFieldLegendVariant`** — `pub enum EuvFieldLegendVariant {`

### `component::field::view::fn`

- `fn` **`euv_field`** — `pub fn euv_field(node: VirtualNode<EuvFieldProps>) -> VirtualNode {...}`
- `fn` **`euv_field_set`** — `pub fn euv_field_set(node: VirtualNode<EuvFieldSetProps>) -> VirtualNode {...}`
- `fn` **`euv_field_legend`** — `pub fn euv_field_legend(node: VirtualNode<EuvFieldLegendProps>) -> VirtualNode {...}`
- `fn` **`euv_field_group`** — `pub fn euv_field_group(node: VirtualNode<EuvFieldGroupProps>) -> VirtualNode {...}`
- `fn` **`euv_field_content`** — `pub fn euv_field_content(node: VirtualNode<EuvFieldContentProps>) -> VirtualNode {...}`
- `fn` **`euv_field_label`** — `pub fn euv_field_label(node: VirtualNode<EuvFieldLabelProps>) -> VirtualNode {...}`
- `fn` **`euv_field_title`** — `pub fn euv_field_title(node: VirtualNode<EuvFieldTitleProps>) -> VirtualNode {...}`
- `fn` **`euv_field_description`** — `pub fn euv_field_description(node: VirtualNode<EuvFieldDescriptionProps>) -> VirtualNode {...}`
- `fn` **`euv_field_error`** — `pub fn euv_field_error(node: VirtualNode<EuvFieldErrorProps>) -> VirtualNode {...}`
- `fn` **`euv_field_separator`** — `pub fn euv_field_separator(node: VirtualNode<EuvFieldSeparatorProps>) -> VirtualNode {...}`

### `component::field::view::struct`

- `struct` **`EuvFieldProps`** — `pub struct EuvFieldProps {`
- `struct` **`EuvFieldSetProps`** — `pub struct EuvFieldSetProps {`
- `struct` **`EuvFieldLegendProps`** — `pub struct EuvFieldLegendProps {`
- `struct` **`EuvFieldGroupProps`** — `pub struct EuvFieldGroupProps {`
- `struct` **`EuvFieldContentProps`** — `pub struct EuvFieldContentProps {`
- `struct` **`EuvFieldLabelProps`** — `pub struct EuvFieldLabelProps {`
- `struct` **`EuvFieldTitleProps`** — `pub struct EuvFieldTitleProps {`
- `struct` **`EuvFieldDescriptionProps`** — `pub struct EuvFieldDescriptionProps {`
- `struct` **`EuvFieldErrorProps`** — `pub struct EuvFieldErrorProps {`
- `struct` **`EuvFieldSeparatorProps`** — `pub struct EuvFieldSeparatorProps {`

### `component::footer::view::fn`

- `fn` **`euv_footer`** — `pub fn euv_footer(node: VirtualNode<EuvFooterProps>) -> VirtualNode {...}`

### `component::footer::view::struct`

- `struct` **`EuvFooterItem`** — `pub struct EuvFooterItem {`
- `struct` **`EuvFooterProps`** — `pub struct EuvFooterProps {`

### `component::form::view::fn`

- `fn` **`euv_form`** — `pub fn euv_form(node: VirtualNode<EuvFormProps>) -> VirtualNode {...}`
- `fn` **`euv_form_field`** — `pub fn euv_form_field(node: VirtualNode<EuvFormFieldProps>) -> VirtualNode {...}`
- `fn` **`euv_form_item`** — `pub fn euv_form_item(node: VirtualNode<EuvFormItemProps>) -> VirtualNode {...}`

### `component::form::view::struct`

- `struct` **`EuvFormProps`** — `pub struct EuvFormProps {`
- `struct` **`EuvFormFieldProps`** — `pub struct EuvFormFieldProps {`
- `struct` **`EuvFormItemProps`** — `pub struct EuvFormItemProps {`

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

### `component::hover_card::view::fn`

- `fn` **`euv_hover_card`** — `pub fn euv_hover_card(node: VirtualNode<EuvHoverCardProps>) -> VirtualNode {...}`
- `fn` **`euv_hover_card_trigger`** — `pub fn euv_hover_card_trigger(node: VirtualNode<EuvHoverCardTriggerProps>) -> VirtualNode {...}`
- `fn` **`euv_hover_card_content`** — `pub fn euv_hover_card_content(node: VirtualNode<EuvHoverCardContentProps>) -> VirtualNode {...}`

### `component::hover_card::view::struct`

- `struct` **`EuvHoverCardProps`** — `pub struct EuvHoverCardProps {`
- `struct` **`EuvHoverCardTriggerProps`** — `pub struct EuvHoverCardTriggerProps {`
- `struct` **`EuvHoverCardContentProps`** — `pub struct EuvHoverCardContentProps {`

### `component::icon::view::enum`

- `enum` **`EuvIconSize`** — `pub enum EuvIconSize {`

### `component::icon::view::fn`

- `fn` **`svg_glyph_markup`** — `pub(crate) fn svg_glyph_markup(markup: &str, px: i32) -> String {...}`
- `fn` **`euv_icon`** — `pub fn euv_icon(node: VirtualNode<EuvIconProps>) -> VirtualNode {...}`

### `component::icon::view::impl`

- `fn` **`px`** — `pub fn px(&self) -> i32 {...}`

### `component::icon::view::struct`

- `struct` **`EuvIconProps`** — `pub struct EuvIconProps {`

### `component::icon::view::type`

- `type` **`EuvSvgMarkup`** — `pub type EuvSvgMarkup = &'static str;`

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

### `component::input_group::view::enum`

- `enum` **`EuvInputGroupAlign`** — `pub enum EuvInputGroupAlign {`
- `enum` **`EuvInputGroupButtonSize`** — `pub enum EuvInputGroupButtonSize {`

### `component::input_group::view::fn`

- `fn` **`euv_input_group`** — `pub fn euv_input_group(node: VirtualNode<EuvInputGroupProps>) -> VirtualNode {...}`
- `fn` **`euv_input_group_addon`** — `pub fn euv_input_group_addon(node: VirtualNode<EuvInputGroupAddonProps>) -> VirtualNode {...}`
- `fn` **`euv_input_group_button`** — `pub fn euv_input_group_button(node: VirtualNode<EuvInputGroupButtonProps>) -> VirtualNode {...}`
- `fn` **`euv_input_group_text`** — `pub fn euv_input_group_text(node: VirtualNode<EuvInputGroupTextProps>) -> VirtualNode {...}`
- `fn` **`euv_input_group_input`** — `pub fn euv_input_group_input(node: VirtualNode<EuvInputGroupInputProps>) -> VirtualNode {...}`
- `fn` **`euv_input_group_textarea`** — `pub fn euv_input_group_textarea(node: VirtualNode<EuvInputGroupTextareaProps>) -> VirtualNode {...}`

### `component::input_group::view::struct`

- `struct` **`EuvInputGroupProps`** — `pub struct EuvInputGroupProps {`
- `struct` **`EuvInputGroupAddonProps`** — `pub struct EuvInputGroupAddonProps {`
- `struct` **`EuvInputGroupButtonProps`** — `pub struct EuvInputGroupButtonProps {`
- `struct` **`EuvInputGroupTextProps`** — `pub struct EuvInputGroupTextProps {`
- `struct` **`EuvInputGroupInputProps`** — `pub struct EuvInputGroupInputProps {`
- `struct` **`EuvInputGroupTextareaProps`** — `pub struct EuvInputGroupTextareaProps {`

### `component::input_otp::view::fn`

- `fn` **`euv_input_otp`** — `pub fn euv_input_otp(node: VirtualNode<EuvInputOtpProps>) -> VirtualNode {...}`
- `fn` **`euv_input_otp_group`** — `pub fn euv_input_otp_group(node: VirtualNode<EuvInputOtpGroupProps>) -> VirtualNode {...}`
- `fn` **`euv_input_otp_slot`** — `pub fn euv_input_otp_slot(node: VirtualNode<EuvInputOtpSlotProps>) -> VirtualNode {...}`
- `fn` **`euv_input_otp_separator`** — `pub fn euv_input_otp_separator(node: VirtualNode<EuvInputOtpGroupProps>) -> VirtualNode {...}`

### `component::input_otp::view::struct`

- `struct` **`EuvInputOtpProps`** — `pub struct EuvInputOtpProps {`
- `struct` **`EuvInputOtpGroupProps`** — `pub struct EuvInputOtpGroupProps {`
- `struct` **`EuvInputOtpSlotProps`** — `pub struct EuvInputOtpSlotProps {`

### `component::item::view::enum`

- `enum` **`EuvItemVariant`** — `pub enum EuvItemVariant {`
- `enum` **`EuvItemSize`** — `pub enum EuvItemSize {`
- `enum` **`EuvItemMediaVariant`** — `pub enum EuvItemMediaVariant {`

### `component::item::view::fn`

- `fn` **`euv_item_group`** — `pub fn euv_item_group(node: VirtualNode<EuvItemProps>) -> VirtualNode {...}`
- `fn` **`euv_item`** — `pub fn euv_item(node: VirtualNode<EuvItemProps>) -> VirtualNode {...}`
- `fn` **`euv_item_media`** — `pub fn euv_item_media(node: VirtualNode<EuvItemMediaProps>) -> VirtualNode {...}`
- `fn` **`euv_item_content`** — `pub fn euv_item_content(node: VirtualNode<EuvItemProps>) -> VirtualNode {...}`
- `fn` **`euv_item_title`** — `pub fn euv_item_title(node: VirtualNode<EuvItemTitleProps>) -> VirtualNode {...}`
- `fn` **`euv_item_description`** — `pub fn euv_item_description(node: VirtualNode<EuvItemDescriptionProps>) -> VirtualNode {...}`
- `fn` **`euv_item_actions`** — `pub fn euv_item_actions(node: VirtualNode<EuvItemProps>) -> VirtualNode {...}`
- `fn` **`euv_item_header`** — `pub fn euv_item_header(node: VirtualNode<EuvItemProps>) -> VirtualNode {...}`
- `fn` **`euv_item_footer`** — `pub fn euv_item_footer(node: VirtualNode<EuvItemProps>) -> VirtualNode {...}`
- `fn` **`euv_item_separator`** — `pub fn euv_item_separator(node: VirtualNode<EuvItemProps>) -> VirtualNode {...}`

### `component::item::view::struct`

- `struct` **`EuvItemProps`** — `pub struct EuvItemProps {`
- `struct` **`EuvItemMediaProps`** — `pub struct EuvItemMediaProps {`
- `struct` **`EuvItemTitleProps`** — `pub struct EuvItemTitleProps {`
- `struct` **`EuvItemDescriptionProps`** — `pub struct EuvItemDescriptionProps {`

### `component::kbd::view::fn`

- `fn` **`euv_kbd`** — `pub fn euv_kbd(node: VirtualNode<EuvKbdProps>) -> VirtualNode {...}`
- `fn` **`euv_kbd_group`** — `pub fn euv_kbd_group(node: VirtualNode<EuvKbdGroupProps>) -> VirtualNode {...}`

### `component::kbd::view::struct`

- `struct` **`EuvKbdProps`** — `pub struct EuvKbdProps {`
- `struct` **`EuvKbdGroupProps`** — `pub struct EuvKbdGroupProps {`

### `component::label::view::fn`

- `fn` **`euv_label`** — `pub fn euv_label(node: VirtualNode<EuvLabelProps>) -> VirtualNode {...}`

### `component::label::view::struct`

- `struct` **`EuvLabelProps`** — `pub struct EuvLabelProps {`

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

- `enum` **`EuvMdBlock`** — `pub enum EuvMdBlock {` — gained a **`Diagram { svg: &'static str }`** variant. The SVG is produced before the page data is generated — the diagram engine is a build-time dependency of the generator, not a runtime dependency of the browser bundle — so the browser only ever carries the finished markup. `euv_markdown_blocks` renders it as a `div` with `inner_html`.
- `enum` **`EuvMdInline`** — `pub enum EuvMdInline {`

### `component::markdown::view::fn`

- `fn` **`euv_markdown`** — `pub fn euv_markdown(node: VirtualNode<EuvMarkdownProps>) -> VirtualNode {...}`
- `fn` **`euv_markdown_blocks`** — `pub fn euv_markdown_blocks(blocks: &'static [EuvMdBlock]) -> VirtualNode {...}`
- `fn` **`mark_image_loaded`** — `pub(crate) fn mark_image_loaded() -> Option<Rc<dyn Fn(Event)>> {...}`

### `component::markdown::view::struct`

- `struct` **`EuvMarkdownProps`** — `pub struct EuvMarkdownProps {`

### `component::marker::view::enum`

- `enum` **`EuvMarkerVariant`** — `pub enum EuvMarkerVariant {`

### `component::marker::view::fn`

- `fn` **`euv_marker`** — `pub fn euv_marker(node: VirtualNode<EuvMarkerProps>) -> VirtualNode {...}`
- `fn` **`euv_marker_icon`** — `pub fn euv_marker_icon(node: VirtualNode<EuvMarkerIconProps>) -> VirtualNode {...}`
- `fn` **`euv_marker_content`** — `pub fn euv_marker_content(node: VirtualNode<EuvMarkerContentProps>) -> VirtualNode {...}`

### `component::marker::view::struct`

- `struct` **`EuvMarkerProps`** — `pub struct EuvMarkerProps {`
- `struct` **`EuvMarkerIconProps`** — `pub struct EuvMarkerIconProps {`
- `struct` **`EuvMarkerContentProps`** — `pub struct EuvMarkerContentProps {`

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
- `fn` **`euv_message_group`** — `pub fn euv_message_group(node: VirtualNode<EuvMessageGroupProps>) -> VirtualNode {...}`
- `fn` **`euv_message_header`** — `pub fn euv_message_header(node: VirtualNode<EuvMessageHeaderProps>) -> VirtualNode {...}`
- `fn` **`euv_message_avatar`** — `pub fn euv_message_avatar(node: VirtualNode<EuvMessageAvatarProps>) -> VirtualNode {...}`
- `fn` **`euv_message_content`** — `pub fn euv_message_content(node: VirtualNode<EuvMessageContentProps>) -> VirtualNode {...}`
- `fn` **`euv_message_bubble`** — `pub fn euv_message_bubble(node: VirtualNode<EuvMessageBubbleProps>) -> VirtualNode {...}`
- `fn` **`euv_message_footer`** — `pub fn euv_message_footer(node: VirtualNode<EuvMessageFooterProps>) -> VirtualNode {...}`

### `component::message::view::struct`

- `struct` **`EuvMessageItem`** — `pub struct EuvMessageItem {`
- `struct` **`EuvMessageProps`** — `pub struct EuvMessageProps {`
- `struct` **`EuvMessageGroupProps`** — `pub struct EuvMessageGroupProps {`
- `struct` **`EuvMessageHeaderProps`** — `pub struct EuvMessageHeaderProps {`
- `struct` **`EuvMessageAvatarProps`** — `pub struct EuvMessageAvatarProps {`
- `struct` **`EuvMessageContentProps`** — `pub struct EuvMessageContentProps {`
- `struct` **`EuvMessageBubbleProps`** — `pub struct EuvMessageBubbleProps {`
- `struct` **`EuvMessageFooterProps`** — `pub struct EuvMessageFooterProps {`

### `component::message_scroller::view::enum`

- `enum` **`EuvMessageScrollerDirection`** — `pub enum EuvMessageScrollerDirection {`

### `component::message_scroller::view::fn`

- `fn` **`euv_message_scroller`** — `pub fn euv_message_scroller(node: VirtualNode<EuvMessageScrollerProps>) -> VirtualNode {...}`
- `fn` **`euv_message_scroller_viewport`** — `pub fn euv_message_scroller_viewport( node: VirtualNode<EuvMessageScrollerViewportProps>, ) -> VirtualNode {...}`
- `fn` **`euv_message_scroller_content`** — `pub fn euv_message_scroller_content( node: VirtualNode<EuvMessageScrollerContentProps>, ) -> VirtualNode {...}`
- `fn` **`euv_message_scroller_item`** — `pub fn euv_message_scroller_item(node: VirtualNode<EuvMessageScrollerItemProps>) -> VirtualNode {...}`
- `fn` **`euv_message_scroller_button`** — `pub fn euv_message_scroller_button( node: VirtualNode<EuvMessageScrollerButtonProps>, ) -> VirtualNode {...}`

### `component::message_scroller::view::struct`

- `struct` **`EuvMessageScrollerProps`** — `pub struct EuvMessageScrollerProps {`
- `struct` **`EuvMessageScrollerViewportProps`** — `pub struct EuvMessageScrollerViewportProps {`
- `struct` **`EuvMessageScrollerContentProps`** — `pub struct EuvMessageScrollerContentProps {`
- `struct` **`EuvMessageScrollerItemProps`** — `pub struct EuvMessageScrollerItemProps {`
- `struct` **`EuvMessageScrollerButtonProps`** — `pub struct EuvMessageScrollerButtonProps {`

### `component::modal::view::fn`

- `fn` **`euv_modal`** — `pub fn euv_modal(node: VirtualNode<EuvModalProps>) -> VirtualNode {...}`
- `fn` **`euv_dialog`** — `pub fn euv_dialog(node: VirtualNode<EuvDialogProps>) -> VirtualNode {...}`
- `fn` **`euv_dialog_header`** — `pub fn euv_dialog_header(node: VirtualNode<EuvDialogHeaderProps>) -> VirtualNode {...}`
- `fn` **`euv_dialog_title`** — `pub fn euv_dialog_title(node: VirtualNode<EuvDialogTitleProps>) -> VirtualNode {...}`
- `fn` **`euv_dialog_description`** — `pub fn euv_dialog_description(node: VirtualNode<EuvDialogDescriptionProps>) -> VirtualNode {...}`
- `fn` **`euv_dialog_footer`** — `pub fn euv_dialog_footer(node: VirtualNode<EuvDialogFooterProps>) -> VirtualNode {...}`
- `fn` **`euv_dialog_trigger`** — `pub fn euv_dialog_trigger(node: VirtualNode<EuvDialogTriggerProps>) -> VirtualNode {...}`
- `fn` **`euv_dialog_close`** — `pub fn euv_dialog_close(node: VirtualNode<EuvDialogCloseProps>) -> VirtualNode {...}`
- `fn` **`euv_dialog_overlay`** — `pub fn euv_dialog_overlay(node: VirtualNode<EuvDialogOverlayProps>) -> VirtualNode {...}`
- `fn` **`euv_dialog_content`** — `pub fn euv_dialog_content(node: VirtualNode<EuvDialogContentProps>) -> VirtualNode {...}`

### `component::modal::view::struct`

- `struct` **`EuvModalProps`** — `pub struct EuvModalProps {`
- `struct` **`EuvDialogProps`** — `pub struct EuvDialogProps {`
- `struct` **`EuvDialogHeaderProps`** — `pub struct EuvDialogHeaderProps {`
- `struct` **`EuvDialogTitleProps`** — `pub struct EuvDialogTitleProps {`
- `struct` **`EuvDialogDescriptionProps`** — `pub struct EuvDialogDescriptionProps {`
- `struct` **`EuvDialogFooterProps`** — `pub struct EuvDialogFooterProps {`
- `struct` **`EuvDialogTriggerProps`** — `pub struct EuvDialogTriggerProps {`
- `struct` **`EuvDialogCloseProps`** — `pub struct EuvDialogCloseProps {`
- `struct` **`EuvDialogOverlayProps`** — `pub struct EuvDialogOverlayProps {`
- `struct` **`EuvDialogContentProps`** — `pub struct EuvDialogContentProps {`

### `component::native_select::view::enum`

- `enum` **`EuvNativeSelectSize`** — `pub enum EuvNativeSelectSize {`

### `component::native_select::view::fn`

- `fn` **`euv_native_select`** — `pub fn euv_native_select(node: VirtualNode<EuvNativeSelectProps>) -> VirtualNode {...}`
- `fn` **`euv_native_select_option`** — `pub fn euv_native_select_option(node: VirtualNode<EuvNativeSelectOptionProps>) -> VirtualNode {...}`
- `fn` **`euv_native_select_opt_group`** — `pub fn euv_native_select_opt_group(node: VirtualNode<EuvNativeSelectOptGroupProps>) -> VirtualNode {...}`

### `component::native_select::view::struct`

- `struct` **`EuvNativeSelectProps`** — `pub struct EuvNativeSelectProps {`
- `struct` **`EuvNativeSelectOptionProps`** — `pub struct EuvNativeSelectOptionProps {`
- `struct` **`EuvNativeSelectOptGroupProps`** — `pub struct EuvNativeSelectOptGroupProps {`

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
- `fn` **`euv_menubar`** — `pub fn euv_menubar(node: VirtualNode<EuvMenubarProps>) -> VirtualNode {...}`
- `fn` **`euv_menubar_menu`** — `pub fn euv_menubar_menu(node: VirtualNode<EuvMenubarMenuProps>) -> VirtualNode {...}`
- `fn` **`euv_menubar_trigger`** — `pub fn euv_menubar_trigger(node: VirtualNode<EuvMenubarTriggerProps>) -> VirtualNode {...}`
- `fn` **`euv_menubar_content`** — `pub fn euv_menubar_content(node: VirtualNode<EuvMenubarContentProps>) -> VirtualNode {...}`
- `fn` **`menubar_enabled_tab_stop`** — `pub(crate) fn menubar_enabled_tab_stop( disabled: &[bool], preferred: Option<usize>, ) -> Option<usize> {...}`
- `fn` **`menubar_next_enabled_trigger`** — `pub(crate) fn menubar_next_enabled_trigger( disabled: &[bool], current: usize, key: &str, rtl: bool, ) -> Option<usize> {...}`
- `fn` **`euv_menubar_item`** — `pub fn euv_menubar_item(node: VirtualNode<EuvMenubarItemProps>) -> VirtualNode {...}`
- `fn` **`euv_menubar_group`** — `pub fn euv_menubar_group(node: VirtualNode<EuvMenubarGroupProps>) -> VirtualNode {...}`
- `fn` **`euv_menubar_separator`** — `pub fn euv_menubar_separator(node: VirtualNode<EuvMenubarSeparatorProps>) -> VirtualNode {...}`
- `fn` **`euv_menubar_label`** — `pub fn euv_menubar_label(node: VirtualNode<EuvMenubarLabelProps>) -> VirtualNode {...}`
- `fn` **`euv_menubar_shortcut`** — `pub fn euv_menubar_shortcut(node: VirtualNode<EuvMenubarShortcutProps>) -> VirtualNode {...}`
- `fn` **`euv_menubar_checkbox_item`** — `pub fn euv_menubar_checkbox_item(node: VirtualNode<EuvMenubarCheckboxItemProps>) -> VirtualNode {...}`
- `fn` **`euv_menubar_radio_item`** — `pub fn euv_menubar_radio_item(node: VirtualNode<EuvMenubarRadioItemProps>) -> VirtualNode {...}`
- `fn` **`euv_menubar_radio_group`** — `pub fn euv_menubar_radio_group(node: VirtualNode<EuvMenubarRadioGroupProps>) -> VirtualNode {...}`
- `fn` **`euv_menubar_sub`** — `pub fn euv_menubar_sub(node: VirtualNode<EuvMenubarSubProps>) -> VirtualNode {...}`
- `fn` **`euv_menubar_sub_trigger`** — `pub fn euv_menubar_sub_trigger(node: VirtualNode<EuvMenubarSubTriggerProps>) -> VirtualNode {...}`
- `fn` **`euv_menubar_sub_content`** — `pub fn euv_menubar_sub_content(node: VirtualNode<EuvMenubarSubContentProps>) -> VirtualNode {...}`

### `component::navbar::view::struct`

- `struct` **`EuvNavbarItem`** — `pub struct EuvNavbarItem {`
- `struct` **`EuvNavbarProps`** — `pub struct EuvNavbarProps {`
- `struct` **`EuvNavbarLinkProps`** — `pub struct EuvNavbarLinkProps {`
- `struct` **`EuvMenubarProps`** — `pub struct EuvMenubarProps {`
- `struct` **`EuvMenubarMenuProps`** — `pub struct EuvMenubarMenuProps {`
- `struct` **`EuvMenubarTriggerProps`** — `pub struct EuvMenubarTriggerProps {`
- `struct` **`EuvMenubarContentProps`** — `pub struct EuvMenubarContentProps {`
- `struct` **`EuvMenubarItemProps`** — `pub struct EuvMenubarItemProps {`
- `struct` **`EuvMenubarGroupProps`** — `pub struct EuvMenubarGroupProps {`
- `struct` **`EuvMenubarSeparatorProps`** — `pub struct EuvMenubarSeparatorProps {`
- `struct` **`EuvMenubarLabelProps`** — `pub struct EuvMenubarLabelProps {`
- `struct` **`EuvMenubarShortcutProps`** — `pub struct EuvMenubarShortcutProps {`
- `struct` **`EuvMenubarCheckboxItemProps`** — `pub struct EuvMenubarCheckboxItemProps {`
- `struct` **`EuvMenubarRadioItemProps`** — `pub struct EuvMenubarRadioItemProps {`
- `struct` **`EuvMenubarRadioGroupProps`** — `pub struct EuvMenubarRadioGroupProps {`
- `struct` **`EuvMenubarSubProps`** — `pub struct EuvMenubarSubProps {`
- `struct` **`EuvMenubarSubTriggerProps`** — `pub struct EuvMenubarSubTriggerProps {`
- `struct` **`EuvMenubarSubContentProps`** — `pub struct EuvMenubarSubContentProps {`

### `component::navigation_menu::view::fn`

- `fn` **`euv_navigation_menu`** — `pub fn euv_navigation_menu(node: VirtualNode<EuvNavigationMenuProps>) -> VirtualNode {...}`
- `fn` **`euv_navigation_menu_list`** — `pub fn euv_navigation_menu_list(node: VirtualNode<EuvNavigationMenuListProps>) -> VirtualNode {...}`
- `fn` **`euv_navigation_menu_item`** — `pub fn euv_navigation_menu_item(node: VirtualNode<EuvNavigationMenuItemProps>) -> VirtualNode {...}`
- `fn` **`euv_navigation_menu_trigger`** — `pub fn euv_navigation_menu_trigger( node: VirtualNode<EuvNavigationMenuTriggerProps>, ) -> VirtualNode {...}`
- `fn` **`euv_navigation_menu_content`** — `pub fn euv_navigation_menu_content( node: VirtualNode<EuvNavigationMenuContentProps>, ) -> VirtualNode {...}`
- `fn` **`euv_navigation_menu_link`** — `pub fn euv_navigation_menu_link(node: VirtualNode<EuvNavigationMenuLinkProps>) -> VirtualNode {...}`
- `fn` **`euv_navigation_menu_viewport`** — `pub fn euv_navigation_menu_viewport( node: VirtualNode<EuvNavigationMenuViewportProps>, ) -> VirtualNode {...}`
- `fn` **`euv_navigation_menu_indicator`** — `pub fn euv_navigation_menu_indicator( node: VirtualNode<EuvNavigationMenuIndicatorProps>, ) -> VirtualNode {...}`

### `component::navigation_menu::view::struct`

- `struct` **`EuvNavigationMenuProps`** — `pub struct EuvNavigationMenuProps {`
- `struct` **`EuvNavigationMenuListProps`** — `pub struct EuvNavigationMenuListProps {`
- `struct` **`EuvNavigationMenuItemProps`** — `pub struct EuvNavigationMenuItemProps {`
- `struct` **`EuvNavigationMenuTriggerProps`** — `pub struct EuvNavigationMenuTriggerProps {`
- `struct` **`EuvNavigationMenuContentProps`** — `pub struct EuvNavigationMenuContentProps {`
- `struct` **`EuvNavigationMenuLinkProps`** — `pub struct EuvNavigationMenuLinkProps {`
- `struct` **`EuvNavigationMenuViewportProps`** — `pub struct EuvNavigationMenuViewportProps {`
- `struct` **`EuvNavigationMenuIndicatorProps`** — `pub struct EuvNavigationMenuIndicatorProps {`

### `component::notification::view::enum`

- `enum` **`EuvToastVariant`** — `pub enum EuvToastVariant {`

### `component::notification::view::fn`

- `fn` **`euv_notification`** — `pub fn euv_notification(node: VirtualNode<EuvNotificationProps>) -> VirtualNode {...}`
- `fn` **`notification_callback_handler`** — `pub fn notification_callback_handler<E: 'static>( callback: Option<Rc<dyn Fn()>>, ) -> Option<Rc<dyn Fn(E)>> {...}`
- `fn` **`euv_toast`** — `pub fn euv_toast(node: VirtualNode<EuvToastProps>) -> VirtualNode {...}`
- `fn` **`euv_toast_card`** — `pub fn euv_toast_card(node: VirtualNode<EuvToastCardProps>) -> VirtualNode {...}`
- `fn` **`euv_toast_title`** — `pub fn euv_toast_title(node: VirtualNode<EuvToastTitleProps>) -> VirtualNode {...}`
- `fn` **`euv_toast_description`** — `pub fn euv_toast_description(node: VirtualNode<EuvToastDescriptionProps>) -> VirtualNode {...}`
- `fn` **`euv_toast_action`** — `pub fn euv_toast_action(node: VirtualNode<EuvToastActionProps>) -> VirtualNode {...}`
- `fn` **`euv_toast_provider`** — `pub fn euv_toast_provider(node: VirtualNode<EuvToastProviderProps>) -> VirtualNode {...}`
- `fn` **`euv_toast_viewport`** — `pub fn euv_toast_viewport(node: VirtualNode<EuvToastViewportProps>) -> VirtualNode {...}`
- `fn` **`euv_toast_close`** — `pub fn euv_toast_close(node: VirtualNode<EuvToastCloseProps>) -> VirtualNode {...}`

### `component::notification::view::struct`

- `struct` **`EuvNotificationItem`** — `pub struct EuvNotificationItem {`
- `struct` **`EuvNotificationProps`** — `pub struct EuvNotificationProps {`
- `struct` **`EuvToastProps`** — `pub struct EuvToastProps {`
- `struct` **`EuvToastTitleProps`** — `pub struct EuvToastTitleProps {`
- `struct` **`EuvToastDescriptionProps`** — `pub struct EuvToastDescriptionProps {`
- `struct` **`EuvToastActionProps`** — `pub struct EuvToastActionProps {`
- `struct` **`EuvToastCardProps`** — `pub struct EuvToastCardProps {`
- `struct` **`EuvToastProviderProps`** — `pub struct EuvToastProviderProps {`
- `struct` **`EuvToastViewportProps`** — `pub struct EuvToastViewportProps {`
- `struct` **`EuvToastCloseProps`** — `pub struct EuvToastCloseProps {`

### `component::number_input::view::fn`

- `fn` **`stepped_value`** — `pub fn stepped_value(current: i64, step: i64, min: Option<i64>, max: Option<i64>) -> Option<i64> {...}`
- `fn` **`stepper_disabled`** — `pub fn stepper_disabled(current: i64, step: i64, min: Option<i64>, max: Option<i64>) -> bool {...}`
- `fn` **`euv_number_input`** — `pub fn euv_number_input(node: VirtualNode<EuvNumberInputProps>) -> VirtualNode {...}`

### `component::number_input::view::struct`

- `struct` **`EuvNumberInputProps`** — `pub struct EuvNumberInputProps {`

### `component::pagination::view::fn`

- `fn` **`euv_pagination`** — `pub fn euv_pagination(node: VirtualNode<EuvPaginationProps>) -> VirtualNode {...}`
- `fn` **`euv_pagination_item`** — `pub fn euv_pagination_item(node: VirtualNode<EuvPaginationItemProps>) -> VirtualNode {...}`
- `fn` **`euv_pagination_content`** — `pub fn euv_pagination_content(node: VirtualNode<EuvPaginationContentProps>) -> VirtualNode {...}`
- `fn` **`euv_pagination_ellipsis`** — `pub fn euv_pagination_ellipsis(node: VirtualNode<EuvPaginationEllipsisProps>) -> VirtualNode {...}`
- `fn` **`euv_pagination_link`** — `pub fn euv_pagination_link(node: VirtualNode<EuvPaginationLinkProps>) -> VirtualNode {...}`

### `component::pagination::view::struct`

- `struct` **`EuvPaginationItem`** — `pub struct EuvPaginationItem {`
- `struct` **`EuvPaginationProps`** — `pub struct EuvPaginationProps {`
- `struct` **`EuvPaginationItemProps`** — `pub struct EuvPaginationItemProps {`
- `struct` **`EuvPaginationContentProps`** — `pub struct EuvPaginationContentProps {`
- `struct` **`EuvPaginationEllipsisProps`** — `pub struct EuvPaginationEllipsisProps {`
- `struct` **`EuvPaginationLinkProps`** — `pub struct EuvPaginationLinkProps {`

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
- `fn` **`euv_popover_trigger`** — `pub fn euv_popover_trigger(node: VirtualNode<EuvPopoverTriggerProps>) -> VirtualNode {...}`
- `fn` **`on_popover_toggle`** — `pub fn on_popover_toggle(open: Signal<bool>) -> Option<Rc<dyn Fn(Event)>> {...}`

### `component::popover::view::struct`

- `struct` **`EuvPopoverProps`** — `pub struct EuvPopoverProps {`
- `struct` **`EuvPopoverTriggerProps`** — `pub struct EuvPopoverTriggerProps {`

### `component::progress::view::fn`

- `fn` **`euv_progress`** — `pub fn euv_progress(node: VirtualNode<EuvProgressProps>) -> VirtualNode {...}`
- `fn` **`progress_percent_clamp`** — `pub fn progress_percent_clamp(percent: f64) -> f64 {...}`

### `component::progress::view::struct`

- `struct` **`EuvProgressProps`** — `pub struct EuvProgressProps {`

### `component::questionnaire::view::enum`

- `enum` **`EuvQuestionnaireChoiceType`** — `pub enum EuvQuestionnaireChoiceType {`

### `component::questionnaire::view::fn`

- `fn` **`euv_questionnaire`** — `pub fn euv_questionnaire(node: VirtualNode<EuvQuestionnaireProps>) -> VirtualNode {...}`
- `fn` **`euv_questionnaire_progress`** — `pub fn euv_questionnaire_progress(node: VirtualNode<EuvQuestionnaireProgressProps>) -> VirtualNode {...}`
- `fn` **`euv_questionnaire_item`** — `pub fn euv_questionnaire_item(node: VirtualNode<EuvQuestionnaireItemProps>) -> VirtualNode {...}`
- `fn` **`euv_questionnaire_title`** — `pub fn euv_questionnaire_title(node: VirtualNode<EuvQuestionnaireTitleProps>) -> VirtualNode {...}`
- `fn` **`euv_questionnaire_description`** — `pub fn euv_questionnaire_description( node: VirtualNode<EuvQuestionnaireDescriptionProps>, ) -> VirtualNode {...}`
- `fn` **`euv_questionnaire_choices`** — `pub fn euv_questionnaire_choices(node: VirtualNode<EuvQuestionnaireChoicesProps>) -> VirtualNode {...}`
- `fn` **`euv_questionnaire_choice`** — `pub fn euv_questionnaire_choice(node: VirtualNode<EuvQuestionnaireChoiceProps>) -> VirtualNode {...}`
- `fn` **`euv_questionnaire_choice_label`** — `pub fn euv_questionnaire_choice_label( node: VirtualNode<EuvQuestionnaireChoiceLabelProps>, ) -> VirtualNode {...}`
- `fn` **`euv_questionnaire_choice_description`** — `pub fn euv_questionnaire_choice_description( node: VirtualNode<EuvQuestionnaireChoiceDescriptionProps>, ) -> VirtualNode {...}`
- `fn` **`euv_questionnaire_choice_indicator`** — `pub fn euv_questionnaire_choice_indicator( node: VirtualNode<EuvQuestionnaireChoiceIndicatorProps>, ) -> VirtualNode {...}`
- `fn` **`euv_questionnaire_input`** — `pub fn euv_questionnaire_input(node: VirtualNode<EuvQuestionnaireInputProps>) -> VirtualNode {...}`
- `fn` **`euv_questionnaire_error`** — `pub fn euv_questionnaire_error(node: VirtualNode<EuvQuestionnaireErrorProps>) -> VirtualNode {...}`
- `fn` **`euv_questionnaire_actions`** — `pub fn euv_questionnaire_actions(node: VirtualNode<EuvQuestionnaireActionsProps>) -> VirtualNode {...}`
- `fn` **`euv_questionnaire_previous`** — `pub fn euv_questionnaire_previous(node: VirtualNode<EuvQuestionnairePreviousProps>) -> VirtualNode {...}`
- `fn` **`euv_questionnaire_skip`** — `pub fn euv_questionnaire_skip(node: VirtualNode<EuvQuestionnaireSkipProps>) -> VirtualNode {...}`
- `fn` **`euv_questionnaire_next`** — `pub fn euv_questionnaire_next(node: VirtualNode<EuvQuestionnaireNextProps>) -> VirtualNode {...}`
- `fn` **`euv_questionnaire_submit`** — `pub fn euv_questionnaire_submit(node: VirtualNode<EuvQuestionnaireSubmitProps>) -> VirtualNode {...}`
- `fn` **`euv_questionnaire_choice_shortcut`** — `pub fn euv_questionnaire_choice_shortcut( node: VirtualNode<EuvQuestionnaireChoiceShortcutProps>, ) -> VirtualNode {...}`

### `component::questionnaire::view::struct`

- `struct` **`EuvQuestionnaireProps`** — `pub struct EuvQuestionnaireProps {`
- `struct` **`EuvQuestionnaireProgressProps`** — `pub struct EuvQuestionnaireProgressProps {`
- `struct` **`EuvQuestionnaireItemProps`** — `pub struct EuvQuestionnaireItemProps {`
- `struct` **`EuvQuestionnaireTitleProps`** — `pub struct EuvQuestionnaireTitleProps {`
- `struct` **`EuvQuestionnaireDescriptionProps`** — `pub struct EuvQuestionnaireDescriptionProps {`
- `struct` **`EuvQuestionnaireChoicesProps`** — `pub struct EuvQuestionnaireChoicesProps {`
- `struct` **`EuvQuestionnaireChoiceProps`** — `pub struct EuvQuestionnaireChoiceProps {`
- `struct` **`EuvQuestionnaireChoiceLabelProps`** — `pub struct EuvQuestionnaireChoiceLabelProps {`
- `struct` **`EuvQuestionnaireChoiceDescriptionProps`** — `pub struct EuvQuestionnaireChoiceDescriptionProps {`
- `struct` **`EuvQuestionnaireChoiceIndicatorProps`** — `pub struct EuvQuestionnaireChoiceIndicatorProps {`
- `struct` **`EuvQuestionnaireInputProps`** — `pub struct EuvQuestionnaireInputProps {`
- `struct` **`EuvQuestionnaireErrorProps`** — `pub struct EuvQuestionnaireErrorProps {`
- `struct` **`EuvQuestionnaireActionsProps`** — `pub struct EuvQuestionnaireActionsProps {`
- `struct` **`EuvQuestionnairePreviousProps`** — `pub struct EuvQuestionnairePreviousProps {`
- `struct` **`EuvQuestionnaireSkipProps`** — `pub struct EuvQuestionnaireSkipProps {`
- `struct` **`EuvQuestionnaireNextProps`** — `pub struct EuvQuestionnaireNextProps {`
- `struct` **`EuvQuestionnaireSubmitProps`** — `pub struct EuvQuestionnaireSubmitProps {`
- `struct` **`EuvQuestionnaireChoiceShortcutProps`** — `pub struct EuvQuestionnaireChoiceShortcutProps {`

### `component::radio::view::fn`

- `fn` **`euv_radio`** — `pub fn euv_radio(node: VirtualNode<EuvRadioGroupProps>) -> VirtualNode {...}`
- `fn` **`on_radio_change`** — `pub fn on_radio_change( signal: Signal<String>, option_value: &'static str, ) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`euv_radio_group`** — `pub fn euv_radio_group(node: VirtualNode<EuvRadioGroupRootProps>) -> VirtualNode {...}`
- `fn` **`euv_radio_group_item`** — `pub fn euv_radio_group_item(node: VirtualNode<EuvRadioGroupItemProps>) -> VirtualNode {...}`

### `component::radio::view::struct`

- `struct` **`EuvRadioOption`** — `pub struct EuvRadioOption {`
- `struct` **`EuvRadioGroupProps`** — `pub struct EuvRadioGroupProps {`
- `struct` **`EuvRadioGroupRootProps`** — `pub struct EuvRadioGroupRootProps {`
- `struct` **`EuvRadioGroupItemProps`** — `pub struct EuvRadioGroupItemProps {`

### `component::rating::view::enum`

- `enum` **`EuvRatingSize`** — `pub enum EuvRatingSize {`

### `component::rating::view::fn`

- `fn` **`rating_fill_percent`** — `pub fn rating_fill_percent(value: f64, max: f64) -> f64 {...}`
- `fn` **`euv_rating`** — `pub fn euv_rating(node: VirtualNode<EuvRatingProps>) -> VirtualNode {...}`

### `component::rating::view::impl`

- `fn` **`px`** — `pub fn px(&self) -> i32 {...}`

### `component::rating::view::struct`

- `struct` **`EuvRatingProps`** — `pub struct EuvRatingProps {`

### `component::resizable::view::enum`

- `enum` **`EuvResizableDirection`** — `pub enum EuvResizableDirection {`

### `component::resizable::view::fn`

- `fn` **`euv_resizable_panel_group`** — `pub fn euv_resizable_panel_group(node: VirtualNode<EuvResizablePanelGroupProps>) -> VirtualNode {...}`
- `fn` **`euv_resizable_panel`** — `pub fn euv_resizable_panel(node: VirtualNode<EuvResizablePanelProps>) -> VirtualNode {...}`
- `fn` **`euv_resizable_handle`** — `pub fn euv_resizable_handle(node: VirtualNode<EuvResizableHandleProps>) -> VirtualNode {...}`

### `component::resizable::view::struct`

- `struct` **`EuvResizablePanelGroupProps`** — `pub struct EuvResizablePanelGroupProps {`
- `struct` **`EuvResizablePanelProps`** — `pub struct EuvResizablePanelProps {`
- `struct` **`EuvResizableHandleProps`** — `pub struct EuvResizableHandleProps {`
- `struct` **`ResizableDragSession`** — `pub(crate) struct ResizableDragSession {`

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

### `component::scroll_area::view::fn`

- `fn` **`scroll_area_geometry`** — `pub(crate) fn scroll_area_geometry( viewport: f64, content: f64, track: f64, padding: f64, scroll: f64, ) -> (f64, f64, f64) {...}`
- `fn` **`scroll_area_drag_offset`** — `pub(crate) fn scroll_area_drag_offset(position: f64, travel: f64, range: f64) -> f64 {...}`
- `fn` **`scroll_area_key_offset`** — `pub(crate) fn scroll_area_key_offset( key: &str, scroll: f64, viewport: f64, range: f64, ) -> Option<f64> {...}`
- `fn` **`euv_scroll_area`** — `pub fn euv_scroll_area(node: VirtualNode<EuvScrollAreaProps>) -> VirtualNode {...}`
- `fn` **`euv_scroll_area_viewport`** — `pub fn euv_scroll_area_viewport(node: VirtualNode<EuvScrollAreaProps>) -> VirtualNode {...}`
- `fn` **`euv_scroll_bar`** — `pub fn euv_scroll_bar(node: VirtualNode<EuvScrollAreaProps>) -> VirtualNode {...}`

### `component::scroll_area::view::struct`

- `struct` **`EuvScrollAreaProps`** — `pub struct EuvScrollAreaProps {`
- `struct` **`ScrollAreaParts`** — `pub(crate) struct ScrollAreaParts {`
- `struct` **`ScrollAreaController`** — `pub(crate) struct ScrollAreaController {`

### `component::scroll_area::view::impl`

- `fn` **`attach`** — `pub(crate) fn attach(root: NodeRef<Element>) -> Rc<Self> {...}`
- `fn` **`schedule`** — `pub(crate) fn schedule(&self) {...}`
- `fn` **`dispose`** — `pub(crate) fn dispose(&self) {...}`

### `component::scroll_area::view::type`

- `type` **`ScrollAreaListener`** — `pub(crate) type ScrollAreaListener = (EventTarget, &'static str, Closure<dyn FnMut(Event)>);`
- `type` **`ScrollAreaObserverCallback`** — `pub(crate) type ScrollAreaObserverCallback = Closure<dyn FnMut(Array)>;`

### `component::segmented::view::fn`

- `fn` **`euv_segmented`** — `pub fn euv_segmented(node: VirtualNode<EuvSegmentedProps>) -> VirtualNode {...}`

### `component::segmented::view::struct`

- `struct` **`EuvSegmentedOption`** — `pub struct EuvSegmentedOption {`
- `struct` **`EuvSegmentedProps`** — `pub struct EuvSegmentedProps {`

### `component::select::view::enum`

- `enum` **`EuvSelectSize`** — `pub enum EuvSelectSize {`
- `enum` **`SelectPanelEntry`** — `pub(crate) enum SelectPanelEntry {`

### `component::select::view::fn`

- `fn` **`euv_select`** — `pub fn euv_select(node: VirtualNode<EuvSelectProps>) -> VirtualNode {...}`
- `fn` **`use_euv_select_open`** — `pub fn use_euv_select_open() -> Signal<bool> {...}`
- `fn` **`select_scroll_button_target`** — `pub(crate) fn select_scroll_button_target( scroll_top: i32, client_height: i32, scroll_height: i32, is_upward: bool, ) -> i32 {...}`
- `fn` **`euv_select_scroll_up_button`** — `pub fn euv_select_scroll_up_button(node: VirtualNode<EuvSelectScrollUpButtonProps>) -> VirtualNode {...}`
- `fn` **`euv_select_scroll_down_button`** — `pub fn euv_select_scroll_down_button( node: VirtualNode<EuvSelectScrollDownButtonProps>, ) -> VirtualNode {...}`

### `component::select::view::impl`

- `fn` **`matches_typeahead`** — `pub(crate) fn matches_typeahead(&self, query: &str) -> bool {...}`

### `component::select::view::struct`

- `struct` **`EuvSelectOption`** — `pub struct EuvSelectOption {`
- `struct` **`EuvSelectProps`** — `pub struct EuvSelectProps {`
- `struct` **`EuvSelectFormInputProps`** — `pub(crate) struct EuvSelectFormInputProps {`
- `struct` **`EuvSelectOptionContext`** — `pub(crate) struct EuvSelectOptionContext {`
- `struct` **`EuvSelectOpenEffect`** — `pub(crate) struct EuvSelectOpenEffect;`
- `struct` **`EuvSelectOpenEffect`** — `pub(crate) struct EuvSelectOpenEffect {`
- `struct` **`EuvSelectScrollUpButtonProps`** — `pub struct EuvSelectScrollUpButtonProps {`
- `struct` **`EuvSelectScrollDownButtonProps`** — `pub struct EuvSelectScrollDownButtonProps {`

### `component::separator::view::enum`

- `enum` **`EuvSeparatorOrientation`** — `pub enum EuvSeparatorOrientation {`

### `component::separator::view::fn`

- `fn` **`euv_separator`** — `pub fn euv_separator(node: VirtualNode<EuvSeparatorProps>) -> VirtualNode {...}`

### `component::separator::view::struct`

- `struct` **`EuvSeparatorProps`** — `pub struct EuvSeparatorProps {`

### `component::sheet::view::enum`

- `enum` **`EuvSheetSide`** — `pub enum EuvSheetSide {`

### `component::sheet::view::fn`

- `fn` **`euv_sheet`** — `pub fn euv_sheet(node: VirtualNode<EuvSheetProps>) -> VirtualNode {...}`
- `fn` **`euv_sheet_trigger`** — `pub fn euv_sheet_trigger(node: VirtualNode<EuvSheetTriggerProps>) -> VirtualNode {...}`
- `fn` **`euv_sheet_overlay`** — `pub fn euv_sheet_overlay(node: VirtualNode<EuvSheetOverlayProps>) -> VirtualNode {...}`
- `fn` **`euv_sheet_content`** — `pub fn euv_sheet_content(node: VirtualNode<EuvSheetContentProps>) -> VirtualNode {...}`
- `fn` **`euv_sheet_header`** — `pub fn euv_sheet_header(node: VirtualNode<EuvSheetHeaderProps>) -> VirtualNode {...}`
- `fn` **`euv_sheet_footer`** — `pub fn euv_sheet_footer(node: VirtualNode<EuvSheetFooterProps>) -> VirtualNode {...}`
- `fn` **`euv_sheet_title`** — `pub fn euv_sheet_title(node: VirtualNode<EuvSheetTitleProps>) -> VirtualNode {...}`
- `fn` **`euv_sheet_description`** — `pub fn euv_sheet_description(node: VirtualNode<EuvSheetDescriptionProps>) -> VirtualNode {...}`
- `fn` **`euv_sheet_close`** — `pub fn euv_sheet_close(node: VirtualNode<EuvSheetCloseProps>) -> VirtualNode {...}`
- `fn` **`sheet_parent_binding`** — `pub(crate) fn sheet_parent_binding( open: Signal<bool>, parent_open: Option<Signal<bool>>, ) -> Box<dyn FnOnce()> {...}`
- `fn` **`sheet_handles_event`** — `pub(crate) fn sheet_handles_event(open: bool, prevented: bool, nearest: bool) -> bool {...}`
- `fn` **`sheet_dismiss`** — `pub(crate) fn sheet_dismiss(open: Signal<bool>) -> Option<Rc<dyn Fn(Event)>> {...}`
- `fn` **`sheet_scroll_owns_property`** — `pub(crate) fn sheet_scroll_owns_property(name: &str, gutter: bool) -> bool {...}`

### `component::sheet::view::struct`

- `struct` **`SheetScrollLease`** — `pub(crate) struct SheetScrollLease {`
- `struct` **`EuvSheetProps`** — `pub struct EuvSheetProps {`
- `struct` **`EuvSheetTriggerProps`** — `pub struct EuvSheetTriggerProps {`
- `struct` **`EuvSheetOverlayProps`** — `pub struct EuvSheetOverlayProps {`
- `struct` **`EuvSheetContentProps`** — `pub struct EuvSheetContentProps {`
- `struct` **`EuvSheetHeaderProps`** — `pub struct EuvSheetHeaderProps {`
- `struct` **`EuvSheetFooterProps`** — `pub struct EuvSheetFooterProps {`
- `struct` **`EuvSheetTitleProps`** — `pub struct EuvSheetTitleProps {`
- `struct` **`EuvSheetDescriptionProps`** — `pub struct EuvSheetDescriptionProps {`
- `struct` **`EuvSheetCloseProps`** — `pub struct EuvSheetCloseProps {`

### `component::sheet::view::static`

- `static` **`SHEET_SCROLL_LOCKS`** — `pub(crate) static SHEET_SCROLL_LOCKS: SheetScrollRegistry = const { RefCell::new(Vec::new()) };`

### `component::sheet::view::type`

- `type` **`SheetScrollOwner`** — `pub(crate) type SheetScrollOwner = (Document, Rc<SheetScrollLease>);`
- `type` **`SheetScrollSlot`** — `pub(crate) type SheetScrollSlot = RefCell<Option<SheetScrollOwner>>;`
- `type` **`SheetScrollRegistry`** — `pub(crate) type SheetScrollRegistry = RefCell<Vec<(Document, Weak<SheetScrollLease>)>>;`
- `type` **`SheetNextFrame`** — `pub(crate) type SheetNextFrame = RefCell<Option<Weak<dyn Fn()>>>;`
- `type` **`SheetScrollSnapshot`** — `pub(crate) type SheetScrollSnapshot = Vec<(String, String, String)>;`
- `type` **`SheetParentBinding`** — `pub(crate) type SheetParentBinding = (Signal<bool>, Option<Signal<bool>>, Box<dyn FnOnce()>);`

### `component::sidebar::view::fn`

- `fn` **`first_navigable_route`** — `pub fn first_navigable_route(items: &[EuvSidebarItem]) -> Option<&'static str> {...}`
- `fn` **`euv_sidebar_provider`** — `pub fn euv_sidebar_provider(node: VirtualNode<EuvSidebarProviderProps>) -> VirtualNode {...}`
- `fn` **`euv_sidebar`** — `pub fn euv_sidebar(node: VirtualNode<EuvSidebarProps>) -> VirtualNode {...}`
- `fn` **`euv_sidebar_item`** — `pub fn euv_sidebar_item(node: VirtualNode<EuvSidebarItemProps>) -> VirtualNode {...}`
- `fn` **`euv_sidebar_header`** — `pub fn euv_sidebar_header(node: VirtualNode<EuvSidebarHeaderProps>) -> VirtualNode {...}`
- `fn` **`euv_sidebar_content`** — `pub fn euv_sidebar_content(node: VirtualNode<EuvSidebarContentProps>) -> VirtualNode {...}`
- `fn` **`euv_sidebar_footer`** — `pub fn euv_sidebar_footer(node: VirtualNode<EuvSidebarFooterProps>) -> VirtualNode {...}`
- `fn` **`euv_sidebar_group`** — `pub fn euv_sidebar_group(node: VirtualNode<EuvSidebarGroupProps>) -> VirtualNode {...}`
- `fn` **`euv_sidebar_group_label`** — `pub fn euv_sidebar_group_label(node: VirtualNode<EuvSidebarGroupLabelProps>) -> VirtualNode {...}`
- `fn` **`euv_sidebar_group_action`** — `pub fn euv_sidebar_group_action(node: VirtualNode<EuvSidebarGroupActionProps>) -> VirtualNode {...}`
- `fn` **`euv_sidebar_group_content`** — `pub fn euv_sidebar_group_content(node: VirtualNode<EuvSidebarGroupContentProps>) -> VirtualNode {...}`
- `fn` **`euv_sidebar_menu`** — `pub fn euv_sidebar_menu(node: VirtualNode<EuvSidebarMenuProps>) -> VirtualNode {...}`
- `fn` **`euv_sidebar_menu_item`** — `pub fn euv_sidebar_menu_item(node: VirtualNode<EuvSidebarMenuItemProps>) -> VirtualNode {...}`
- `fn` **`euv_sidebar_menu_button`** — `pub fn euv_sidebar_menu_button(node: VirtualNode<EuvSidebarMenuButtonProps>) -> VirtualNode {...}`
- `fn` **`euv_sidebar_menu_action`** — `pub fn euv_sidebar_menu_action(node: VirtualNode<EuvSidebarMenuActionProps>) -> VirtualNode {...}`
- `fn` **`euv_sidebar_menu_badge`** — `pub fn euv_sidebar_menu_badge(node: VirtualNode<EuvSidebarMenuBadgeProps>) -> VirtualNode {...}`
- `fn` **`euv_sidebar_menu_sub`** — `pub fn euv_sidebar_menu_sub(node: VirtualNode<EuvSidebarMenuSubProps>) -> VirtualNode {...}`
- `fn` **`euv_sidebar_menu_sub_item`** — `pub fn euv_sidebar_menu_sub_item(node: VirtualNode<EuvSidebarMenuSubItemProps>) -> VirtualNode {...}`
- `fn` **`euv_sidebar_menu_sub_button`** — `pub fn euv_sidebar_menu_sub_button(node: VirtualNode<EuvSidebarMenuSubButtonProps>) -> VirtualNode {...}`
- `fn` **`euv_sidebar_menu_skeleton`** — `pub fn euv_sidebar_menu_skeleton(node: VirtualNode<EuvSidebarMenuSkeletonProps>) -> VirtualNode {...}`
- `fn` **`euv_sidebar_input`** — `pub fn euv_sidebar_input(node: VirtualNode<EuvSidebarInputProps>) -> VirtualNode {...}`
- `fn` **`euv_sidebar_inset`** — `pub fn euv_sidebar_inset(node: VirtualNode<EuvSidebarInsetProps>) -> VirtualNode {...}`
- `fn` **`euv_sidebar_rail`** — `pub fn euv_sidebar_rail(node: VirtualNode<EuvSidebarRailProps>) -> VirtualNode {...}`
- `fn` **`euv_sidebar_separator`** — `pub fn euv_sidebar_separator(node: VirtualNode<EuvSidebarSeparatorProps>) -> VirtualNode {...}`
- `fn` **`euv_sidebar_trigger`** — `pub fn euv_sidebar_trigger(node: VirtualNode<EuvSidebarTriggerProps>) -> VirtualNode {...}`

### `component::sidebar::view::struct`

- `struct` **`EuvSidebarItem`** — `pub struct EuvSidebarItem {`
- `struct` **`EuvSidebarProps`** — `pub struct EuvSidebarProps {`
- `struct` **`EuvSidebarProviderProps`** — `pub struct EuvSidebarProviderProps {`
- `struct` **`EuvSidebarItemProps`** — `pub struct EuvSidebarItemProps {`
- `struct` **`EuvSidebarHeaderProps`** — `pub struct EuvSidebarHeaderProps {`
- `struct` **`EuvSidebarContentProps`** — `pub struct EuvSidebarContentProps {`
- `struct` **`EuvSidebarFooterProps`** — `pub struct EuvSidebarFooterProps {`
- `struct` **`EuvSidebarGroupProps`** — `pub struct EuvSidebarGroupProps {`
- `struct` **`EuvSidebarGroupLabelProps`** — `pub struct EuvSidebarGroupLabelProps {`
- `struct` **`EuvSidebarGroupActionProps`** — `pub struct EuvSidebarGroupActionProps {`
- `struct` **`EuvSidebarGroupContentProps`** — `pub struct EuvSidebarGroupContentProps {`
- `struct` **`EuvSidebarMenuProps`** — `pub struct EuvSidebarMenuProps {`
- `struct` **`EuvSidebarMenuItemProps`** — `pub struct EuvSidebarMenuItemProps {`
- `struct` **`EuvSidebarMenuButtonProps`** — `pub struct EuvSidebarMenuButtonProps {`
- `struct` **`EuvSidebarMenuActionProps`** — `pub struct EuvSidebarMenuActionProps {`
- `struct` **`EuvSidebarMenuBadgeProps`** — `pub struct EuvSidebarMenuBadgeProps {`
- `struct` **`EuvSidebarMenuSubProps`** — `pub struct EuvSidebarMenuSubProps {`
- `struct` **`EuvSidebarMenuSubItemProps`** — `pub struct EuvSidebarMenuSubItemProps {`
- `struct` **`EuvSidebarMenuSubButtonProps`** — `pub struct EuvSidebarMenuSubButtonProps {`
- `struct` **`EuvSidebarMenuSkeletonProps`** — `pub struct EuvSidebarMenuSkeletonProps {`
- `struct` **`EuvSidebarInputProps`** — `pub struct EuvSidebarInputProps {`
- `struct` **`EuvSidebarInsetProps`** — `pub struct EuvSidebarInsetProps {`
- `struct` **`EuvSidebarRailProps`** — `pub struct EuvSidebarRailProps {`
- `struct` **`EuvSidebarSeparatorProps`** — `pub struct EuvSidebarSeparatorProps {`
- `struct` **`EuvSidebarTriggerProps`** — `pub struct EuvSidebarTriggerProps {`

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

### `component::spinner::view::fn`

- `fn` **`euv_spinner`** — `pub fn euv_spinner(node: VirtualNode<EuvSpinnerProps>) -> VirtualNode {...}`

### `component::spinner::view::struct`

- `struct` **`EuvSpinnerProps`** — `pub struct EuvSpinnerProps {`

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
- `fn` **`euv_table_header`** — `pub fn euv_table_header(node: VirtualNode<EuvTableHeaderProps>) -> VirtualNode {...}`
- `fn` **`euv_table_body`** — `pub fn euv_table_body(node: VirtualNode<EuvTableBodyProps>) -> VirtualNode {...}`
- `fn` **`euv_table_footer`** — `pub fn euv_table_footer(node: VirtualNode<EuvTableFooterProps>) -> VirtualNode {...}`
- `fn` **`euv_table_caption`** — `pub fn euv_table_caption(node: VirtualNode<EuvTableCaptionProps>) -> VirtualNode {...}`
- `fn` **`euv_table_row`** — `pub fn euv_table_row(node: VirtualNode<EuvTableRowProps>) -> VirtualNode {...}`
- `fn` **`euv_table_head`** — `pub fn euv_table_head(node: VirtualNode<EuvTableHeadProps>) -> VirtualNode {...}`
- `fn` **`euv_table_cell`** — `pub fn euv_table_cell(node: VirtualNode<EuvTableCellProps>) -> VirtualNode {...}`

### `component::table::view::struct`

- `struct` **`EuvTableColumn`** — `pub struct EuvTableColumn {`
- `struct` **`EuvTableRow`** — `pub struct EuvTableRow {`
- `struct` **`EuvTableProps`** — `pub struct EuvTableProps {`
- `struct` **`EuvTableHeaderProps`** — `pub struct EuvTableHeaderProps {`
- `struct` **`EuvTableBodyProps`** — `pub struct EuvTableBodyProps {`
- `struct` **`EuvTableFooterProps`** — `pub struct EuvTableFooterProps {`
- `struct` **`EuvTableCaptionProps`** — `pub struct EuvTableCaptionProps {`
- `struct` **`EuvTableRowProps`** — `pub struct EuvTableRowProps {`
- `struct` **`EuvTableHeadProps`** — `pub struct EuvTableHeadProps {`
- `struct` **`EuvTableCellProps`** — `pub struct EuvTableCellProps {`

### `component::tabs::view::fn`

- `fn` **`euv_tabs`** — `pub fn euv_tabs(node: VirtualNode<EuvTabsProps>) -> VirtualNode {...}`

### `component::tabs::view::struct`

- `struct` **`EuvTabItem`** — `pub struct EuvTabItem {`
- `struct` **`EuvTabsProps`** — `pub struct EuvTabsProps {`

### `component::tabs::view::enum`

- `enum` **`EuvTabsActivationMode`** — `pub enum EuvTabsActivationMode {`

### `component::tag::view::enum`

- `enum` **`EuvTagVariant`** — `pub enum EuvTagVariant {`
- `enum` **`EuvTagColor`** — `pub enum EuvTagColor {`

### `component::tag::view::fn`

- `fn` **`euv_tag`** — `pub fn euv_tag(node: VirtualNode<EuvTagProps>) -> VirtualNode {...}`

### `component::tag::view::struct`

- `struct` **`EuvTagProps`** — `pub struct EuvTagProps {`

### `component::textarea::view::fn`

- `fn` **`euv_textarea`** — `pub fn euv_textarea(node: VirtualNode<EuvTextareaProps>) -> VirtualNode {...}`

### `component::textarea::view::struct`

- `struct` **`EuvTextareaProps`** — `pub struct EuvTextareaProps {`

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

### `component::toggle::view::enum`

- `enum` **`EuvToggleVariant`** — `pub enum EuvToggleVariant {`
- `enum` **`EuvToggleSize`** — `pub enum EuvToggleSize {`

### `component::toggle::view::fn`

- `fn` **`euv_toggle`** — `pub fn euv_toggle(node: VirtualNode<EuvToggleProps>) -> VirtualNode {...}`
- `fn` **`toggle_class`** — `pub(crate) fn toggle_class( variant: EuvToggleVariant, size: EuvToggleSize, is_pressed: bool, ) -> String {...}`

### `component::toggle::view::struct`

- `struct` **`EuvToggleProps`** — `pub struct EuvToggleProps {`

### `component::toggle_group::view::fn`

- `fn` **`euv_toggle_group`** — `pub fn euv_toggle_group(node: VirtualNode<EuvToggleGroupProps>) -> VirtualNode {...}`

### `component::toggle_group::view::struct`

- `struct` **`EuvToggleGroupItem`** — `pub struct EuvToggleGroupItem {`
- `struct` **`EuvToggleGroupProps`** — `pub struct EuvToggleGroupProps {`
- `struct` **`ToggleGroupEntry`** — `pub(crate) struct ToggleGroupEntry {`

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

### `component::trace::view::enum`

- `enum` **`EuvTraceStatus`** — `pub enum EuvTraceStatus {`

### `component::trace::view::fn`

- `fn` **`euv_trace`** — `pub fn euv_trace(node: VirtualNode<EuvTraceProps>) -> VirtualNode {...}`
- `fn` **`euv_trace_line`** — `pub fn euv_trace_line(node: VirtualNode<EuvTraceLineProps>) -> VirtualNode {...}`
- `fn` **`euv_trace_icon`** — `pub fn euv_trace_icon(node: VirtualNode<EuvTraceIconProps>) -> VirtualNode {...}`
- `fn` **`euv_trace_title`** — `pub fn euv_trace_title(node: VirtualNode<EuvTraceTitleProps>) -> VirtualNode {...}`
- `fn` **`euv_trace_description`** — `pub fn euv_trace_description(node: VirtualNode<EuvTraceDescriptionProps>) -> VirtualNode {...}`
- `fn` **`euv_trace_collapsible`** — `pub fn euv_trace_collapsible(node: VirtualNode<EuvTraceCollapsibleProps>) -> VirtualNode {...}`
- `fn` **`euv_trace_collapsible_trigger`** — `pub fn euv_trace_collapsible_trigger( node: VirtualNode<EuvTraceCollapsibleTriggerProps>, ) -> VirtualNode {...}`
- `fn` **`euv_trace_collapsible_content`** — `pub fn euv_trace_collapsible_content( node: VirtualNode<EuvTraceCollapsibleContentProps>, ) -> VirtualNode {...}`

### `component::trace::view::struct`

- `struct` **`EuvTraceProps`** — `pub struct EuvTraceProps {`
- `struct` **`EuvTraceLineProps`** — `pub struct EuvTraceLineProps {`
- `struct` **`EuvTraceIconProps`** — `pub struct EuvTraceIconProps {`
- `struct` **`EuvTraceTitleProps`** — `pub struct EuvTraceTitleProps {`
- `struct` **`EuvTraceDescriptionProps`** — `pub struct EuvTraceDescriptionProps {`
- `struct` **`EuvTraceCollapsibleProps`** — `pub struct EuvTraceCollapsibleProps {`
- `struct` **`EuvTraceCollapsibleTriggerProps`** — `pub struct EuvTraceCollapsibleTriggerProps {`
- `struct` **`EuvTraceCollapsibleContentProps`** — `pub struct EuvTraceCollapsibleContentProps {`

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

### `component::layout::view::enum`

- `enum` **`EuvLayoutMode`** — `pub enum EuvLayoutMode {`

### `component::layout::view::fn`

- `fn` **`euv_layout`** — `pub fn euv_layout(node: VirtualNode<EuvLayoutProps>) -> VirtualNode {...}`
- `fn` **`layout_frame`** — `pub(crate) fn layout_frame( props: EuvLayoutProps, mode: EuvLayoutMode, drawer_id: String, ) -> VirtualNode {...}`
- `fn` **`close_layout_drawer`** — `pub(crate) fn close_layout_drawer<F>(open: Signal<bool>, close_history: F) where F: Fn(), {...}`

### `component::layout::view::struct`

- `struct` **`LayoutSettings`** — `pub(crate) struct LayoutSettings {`
- `struct` **`EuvLayoutClasses`** — `pub struct EuvLayoutClasses {`
- `struct` **`EuvLayoutSlots`** — `pub struct EuvLayoutSlots {`
- `struct` **`EuvLayoutProps`** — `pub struct EuvLayoutProps {`

### `component::layout::view::type`

- `type` **`EuvLayoutSlot`** — `pub type EuvLayoutSlot = Rc<dyn Fn(EuvLayoutMode) -> VirtualNode>;`

### `hook::reset::fn`

- `fn` **`use_form_reset`** — `pub(crate) fn use_form_reset(element_id: String, form_id: &'static str, on_reset: Rc<dyn Fn()>) {...}`
