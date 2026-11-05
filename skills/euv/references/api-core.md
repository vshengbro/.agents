# euv-core full pub API

Source: `core/src/` — auto-extracted from `pub` declarations.

Re-exported at the crate root as `euv::*` via `core/src/lib.rs`.

### `app::impl`

- `fn` **`use_signal`** — `pub fn use_signal<T, F>(init: F) -> Signal<T> where T: Clone + PartialEq + 'static, F: FnOnce() -> T, {...}`
- `fn` **`batch`** — `pub fn batch<F, R>(callback: F) -> R where F: FnOnce() -> R, {...}`
- `fn` **`mount`** — `pub fn mount<S, F>(selector: S, render_fn: F) where S: AsRef<str>, F: FnOnce() -> VirtualNode, {...}`
- `fn` **`schedule_update`** — `pub fn schedule_update(dependents: &[usize]) {...}`
- `fn` **`use_cleanup`** — `pub fn use_cleanup<F>(cleanup: F) where F: FnOnce() + 'static, {...}`
- `fn` **`use_interval`** — `pub fn use_interval<F>(millis: i32, callback: F) -> IntervalHandle where F: FnMut() + 'static, {...}`
- `fn` **`use_window_event`** — `pub fn use_window_event<E, F>(event_name: E, callback: F) where E: AsRef<str>, F: FnMut() + 'static, {...}`
- `fn` **`use_node_ref`** — `pub fn use_node_ref<T>() -> NodeRef<T> where T: ?Sized + 'static, {...}`

### `app::struct`

- `struct` **`App`** — `pub struct App;`

### `noderef::impl`

- `fn` **`new`** — `pub fn new() -> Self {...}`
- `fn` **`get`** — `pub fn get(&self) -> Option<JsValue> {...}`
- `fn` **`get_cloned`** — `pub fn get_cloned(&self) -> Option<T> where T: JsCast, {...}`
- `fn` **`set`** — `pub fn set(&self, value: JsValue) {...}`
- `fn` **`share_cell`** — `pub(crate) fn share_cell(&self) -> NodeRefEntry {...}`
- `fn` **`clear`** — `pub fn clear(&self) {...}`
- `fn` **`is_set`** — `pub fn is_set(&self) -> bool {...}`

### `noderef::struct`

- `struct` **`NodeRef`** — `pub struct NodeRef<T: ?Sized> {`

### `event::handler::impl`

- `fn` **`create`** — `pub fn create<F>(event_name: &'static str, callback: F) -> Self where F: FnMut(Event) + 'static, {...}`
- `fn` **`handle`** — `pub(crate) fn handle(&self, event: Event) {...}`

### `event::handler::struct`

- `struct` **`NativeEventHandler`** — `pub struct NativeEventHandler {`

### `event::handler::type`

- `type` **`EventCallback`** — `pub type EventCallback = Box<dyn FnMut(Event)>;`
- `type` **`SharedEventCallback`** — `pub type SharedEventCallback = Rc<UnsafeCell<EventCallback>>;`

### `reactive::cache::impl`

- `fn` **`len`** — `pub fn len(&self) -> usize {...}`
- `fn` **`is_empty`** — `pub fn is_empty(&self) -> bool {...}`
- `fn` **`is_full`** — `pub fn is_full(&self) -> bool {...}`
- `fn` **`contains`** — `pub fn contains(&self, key: &K) -> bool {...}`
- `fn` **`get`** — `pub fn get(&mut self, key: &K) -> Option<&V> {...}`
- `fn` **`peek`** — `pub fn peek(&self, key: &K) -> Option<&V> {...}`
- `fn` **`put`** — `pub fn put(&mut self, key: K, value: V) -> Option<(K, V)> {...}`
- `fn` **`remove`** — `pub fn remove(&mut self, key: &K) -> Option<V> {...}`
- `fn` **`clear`** — `pub fn clear(&mut self) {...}`
- `fn` **`iter`** — `pub fn iter(&self) -> impl Iterator<Item = (&K, &V)> {...}`
- `fn` **`keys`** — `pub fn keys(&self) -> impl Iterator<Item = &K> {...}`
- `fn` **`values`** — `pub fn values(&self) -> impl Iterator<Item = &V> {...}`
- `fn` **`resize`** — `pub fn resize(&mut self, new_capacity: usize) {...}`

### `reactive::cache::struct`

- `struct` **`LruCache`** — `pub struct LruCache<K, V> where K: Clone + Eq + Hash, {`

### `reactive::hook::impl`

- `fn` **`reset_index`** — `pub fn reset_index(&mut self) {...}`
- `fn` **`switch_arm`** — `pub fn switch_arm(&mut self, changed: usize) {...}`
- `fn` **`noderef`** — `pub(crate) fn noderef<T>() -> NodeRef<T> where T: ?Sized + 'static, {...}`
- `fn` **`clear`** — `pub fn clear(&self) {...}`
- `fn` **`current`** — `pub fn current() -> HookContext {...}`
- `fn` **`with`** — `pub fn with<F, R>(context: HookContext, callback: F) -> R where F: FnOnce() -> R, {...}`
- `fn` **`signal`** — `pub(crate) fn signal<T, F>(init: F) -> Signal<T> where T: Clone + PartialEq + 'static, F: FnOnce() -> T, {...}`
- `fn` **`cleanup`** — `pub(crate) fn cleanup<F>(cleanup: F) where F: FnOnce() + 'static, {...}`
- `fn` **`window_event`** — `pub(crate) fn window_event<E, F>(event_name: E, callback: F) where E: AsRef<str>, F: FnMut() + 'static, {...}`
- `fn` **`interval`** — `pub(crate) fn interval<F>(millis: i32, callback: F) -> IntervalHandle where F: FnMut() + 'static, {...}`
- `fn` **`use_hook`** — `pub fn use_hook<T, F>(factory: F) -> T where F: FnOnce() -> T, T: Clone + 'static, {...}`

### `reactive::hook::struct`

- `struct` **`HookContextInner`** — `pub struct HookContextInner {`
- `struct` **`HookContext`** — `pub struct HookContext {`
- `struct` **`IntervalHandle`** — `pub struct IntervalHandle {`

### `reactive::schedule::impl`

- `fn` **`update`** — `pub(crate) fn update(dependents: &[usize]) {...}`
- `fn` **`batch`** — `pub(crate) fn batch<F, R>(callback: F) -> R where F: FnOnce() -> R, {...}`
- `fn` **`dispatch_updates`** — `pub(crate) fn dispatch_updates() {...}`

### `reactive::schedule::static`

- `static` **`SCHEDULED`** — `pub(crate) static SCHEDULED: AtomicBool = AtomicBool::new(false);`
- `static` **`SUPPRESS_SCHEDULE`** — `pub(crate) static SUPPRESS_SCHEDULE: AtomicBool = AtomicBool::new(false);`
- `static` **`CURRENT_HOOK_CONTEXT`** — `pub(crate) static CURRENT_HOOK_CONTEXT: RefCell<Option<HookContextRc>> = const { RefCell::new(None) };`
- `static` **`CURRENT_TRACKING_DYNAMIC_ID`** — `pub(crate) static CURRENT_TRACKING_DYNAMIC_ID: AtomicUsize = AtomicUsize::new(usize::MAX);`
- `static` **`DISPATCH_CLOSURE`** — `pub(crate) static DISPATCH_CLOSURE: Closure<dyn FnMut()> = Closure::wrap(Box::new(|| { SCHEDULED.store(false, Ordering::Relaxed); Scheduler::dispatch_updates(); }));`
- `static` **`MICROTASK_CACHE`** — `pub(crate) static MICROTASK_CACHE: RefCell<MicrotaskCache> = RefCell::new(MicrotaskCache { queue_microtask: None });`

### `reactive::schedule::struct`

- `struct` **`MicrotaskCache`** — `pub(crate) struct MicrotaskCache {`
- `struct` **`Scheduler`** — `pub(crate) struct Scheduler;`

### `reactive::schedule::type`

- `type` **`HookContextRc`** — `pub(crate) type HookContextRc = Rc<RefCell<HookContextInner>>;`

### `reactive::signal::impl`

- `fn` **`create`** — `pub fn create(value: T) -> Self {...}`
- `fn` **`get`** — `pub fn get(&self) -> T {...}`
- `fn` **`with`** — `pub fn with<F, R>(&self, f: F) -> R where F: FnOnce(&T) -> R, {...}`
- `fn` **`subscribe`** — `pub fn subscribe<F>(&self, callback: F) -> usize where F: FnMut() + 'static, {...}`
- `fn` **`unsubscribe`** — `pub fn unsubscribe(&self, id: usize) {...}`
- `fn` **`deactivate`** — `pub(crate) fn deactivate(&self) {...}`
- `fn` **`take_dependents`** — `pub(crate) fn take_dependents(&self) -> Vec<usize> {...}`
- `fn` **`set`** — `pub fn set(&self, value: T) {...}`
- `fn` **`none`** — `pub const fn none() -> Self {...}`
- `fn` **`set`** — `pub fn set(&self, signal: Signal<T>) {...}`
- `fn` **`loaded`** — `pub fn loaded(&self) -> Option<Signal<T>> {...}`
- `fn` **`new`** — `pub fn new<F>(fire: F) -> Self where F: FnMut() + 'static, {...}`
- `fn` **`fire`** — `pub unsafe fn fire(self) {...}`
- `fn` **`fire_at`** — `pub unsafe fn fire_at(addr: usize) {...}`
- `fn` **`new`** — `pub(crate) fn new() -> Self {...}`
- `fn` **`insert`** — `pub(crate) fn insert<T>(&mut self, inner: SignalInner<T>) -> usize where T: Clone + PartialEq + 'static, {...}`
- `fn` **`get_mut`** — `pub(crate) fn get_mut<T>(&mut self, idx: usize) -> Option<&mut SignalInner<T>> where T: Clone + PartialEq + 'static, {...}`

### `reactive::signal::static`

- `static` **`SIGNAL_SLAB`** — `pub(crate) static SIGNAL_SLAB: RefCell<SignalSlab> = RefCell::new(SignalSlab::new());`

### `reactive::signal::struct`

- `struct` **`SignalInner`** — `pub(crate) struct SignalInner<T> where T: Clone, {`
- `struct` **`Signal`** — `pub struct Signal<T> where T: Clone + PartialEq + 'static, {`
- `struct` **`SignalCell`** — `pub struct SignalCell<T> where T: Clone + PartialEq + 'static, {`
- `struct` **`SignalSlab`** — `pub(crate) struct SignalSlab {`
- `struct` **`FireHandle`** — `pub struct FireHandle {`

### `reactive::signal::trait`

- `trait` **`AnySignalInner`** — `pub(crate) trait AnySignalInner: Any {`

### `reactive::signal::type`

- `type` **`ListenerEntry`** — `pub(crate) type ListenerEntry = (usize, Box<dyn FnMut()>);`

### `renderer::dom::trait`

- `trait` **`ElementExt`** — `pub(crate) trait ElementExt {`

### `renderer::dom_ops::enum`

- `enum` **`ChildOp`** — `pub(crate) enum ChildOp {`

### `renderer::dom_ops::fn`

- `fn` **`ensure_dom_op_table`** — `pub(crate) fn ensure_dom_op_table() -> Option<DomOpTable> {...}`
- `fn` **`is_property_attr`** — `pub(crate) fn is_property_attr(name: &str) -> bool {...}`
- `fn` **`apply_set_attr_batch`** — `pub(crate) fn apply_set_attr_batch(element: &Element, ops: &[(String, String)]) {...}`
- `fn` **`apply_remove_attr_batch`** — `pub(crate) fn apply_remove_attr_batch(element: &Element, ops: &[String]) {...}`
- `fn` **`apply_child_ops_batch`** — `pub(crate) fn apply_child_ops_batch(parent: &Element, ops: &[ChildOp]) {...}`
- `fn` **`build_dom_op_names`** — `pub(crate) fn build_dom_op_names() -> DomOpNames {...}`
- `fn` **`encoded_name_suffix`** — `pub(crate) fn encoded_name_suffix() -> String {...}`
- `fn` **`now_micros`** — `pub(crate) fn now_micros() -> u64 {...}`

### `renderer::dom_ops::impl`

- `fn` **`get`** — `pub(crate) fn get() -> &'static DomOpNames {...}`
- `fn` **`set`** — `pub(crate) fn set(names: DomOpNames) -> bool {...}`
- `fn` **`build`** — `pub(crate) fn build() -> DomOpNames {...}`

### `renderer::dom_ops::struct`

- `struct` **`DomOpTable`** — `pub(crate) struct DomOpTable {`
- `static` **`DOM_OP_TABLE`** — `pub(crate) static DOM_OP_TABLE: RefCell<Option<DomOpTable>> = const { RefCell::new(None) };`
- `struct` **`DomOpNames`** — `pub(crate) struct DomOpNames {`

### `renderer::registry::const`

- `static` **`EVENT_ID_CHAIN_FN`** — `pub(crate) static EVENT_ID_CHAIN_FN: RefCell< Option<Option<js_sys::Function>>, > = const { RefCell::new(None) };`

### `renderer::registry::fn`

- `fn` **`ensure_event_id_chain_global`** — `pub(crate) fn ensure_event_id_chain_global() -> bool {...}`
- `fn` **`euv_event_collect_id_chain`** — `pub(crate) fn euv_event_collect_id_chain(event: &JsValue, max_depth: usize) -> Float64Array {...}`

### `renderer::registry::impl`

- `fn` **`get_handler`** — `pub(crate) fn get_handler( euv_id: usize, event_name: &'static str, ) -> Option<NativeEventHandler> {...}`
- `fn` **`has_handler`** — `pub(crate) fn has_handler(euv_id: usize, event_name: &'static str) -> bool {...}`
- `fn` **`set_handler`** — `pub(crate) fn set_handler( euv_id: usize, event_name: &'static str, handler: &NativeEventHandler, ) {...}`
- `fn` **`insert_handler`** — `pub(crate) fn insert_handler( euv_id: usize, event_name: &'static str, slot: HandlerSlot, ) -> Option<HandlerEntry> {...}`
- `fn` **`take_handler`** — `pub(crate) fn take_handler(euv_id: usize, event_name: &'static str) -> Option<HandlerEntry> {...}`
- `fn` **`take_element_handlers`** — `pub(crate) fn take_element_handlers(euv_id: usize) -> Vec<(&'static str, HandlerEntry)> {...}`
- `fn` **`free_handler_slot`** — `pub(crate) fn free_handler_slot(event_name: &'static str, entry: HandlerEntry) {...}`
- `fn` **`delegation`** — `pub(crate) fn delegation(event_name: &'static str) {...}`
- `fn` **`mark_dirty`** — `pub(crate) fn mark_dirty(dynamic_ids: &[usize]) {...}`
- `fn` **`has_dirty`** — `pub(crate) fn has_dirty() -> bool {...}`
- `fn` **`register_dynamic`** — `pub(crate) fn register_dynamic(dynamic_id: usize, callback: Box<dyn FnMut()>) {...}`
- `fn` **`put_dynamic`** — `pub(crate) fn put_dynamic(dynamic_id: usize, entry: SignalUpdateEntry) {...}`
- `fn` **`has_dynamic`** — `pub(crate) fn has_dynamic(dynamic_id: usize) -> bool {...}`
- `fn` **`take_dynamic`** — `pub(crate) fn take_dynamic(dynamic_id: usize) -> Option<SignalUpdateEntry> {...}`
- `fn` **`cleanup_dynamic_node`** — `pub(crate) fn cleanup_dynamic_node(dynamic_id: usize) {...}`
- `fn` **`take_dirty_update_ids`** — `pub(crate) fn take_dirty_update_ids() -> HashSet<usize> {...}`
- `fn` **`cleanup_element`** — `pub(crate) fn cleanup_element(euv_id: usize) {...}`
- `fn` **`push_binding_cleanup`** — `pub(crate) fn push_binding_cleanup(euv_id: usize, cleanup: BindingCleanup) {...}`
- `fn` **`take_binding_cleanups`** — `pub(crate) fn take_binding_cleanups(euv_id: usize) -> Option<Vec<BindingCleanup>> {...}`
- `fn` **`is_non_bubbling`** — `pub(crate) fn is_non_bubbling(event_name: &str) -> bool {...}`
- `fn` **`is_delegated`** — `pub(crate) fn is_delegated(event_name: &str) -> bool {...}`
- `fn` **`mark_delegated`** — `pub(crate) fn mark_delegated(event_name: &'static str) {...}`
- `fn` **`register_window_event`** — `pub(crate) fn register_window_event<F>(event_name: &str, callback: F) -> usize where F: FnMut() + 'static, {...}`
- `fn` **`unregister_window_event`** — `pub(crate) fn unregister_window_event(event_name: &str, handler_id: usize) {...}`
- `fn` **`restore_window_event`** — `pub(crate) fn restore_window_event(event_name: &str, entry: WindowEventHandlerEntry) {...}`
- `fn` **`register_noderef`** — `pub(crate) fn register_noderef(euv_id: usize, entry: NodeRefEntry) {...}`
- `fn` **`cleanup_noderefs`** — `pub(crate) fn cleanup_noderefs(euv_id: usize) {...}`

### `renderer::registry::static`

- `static` **`NEXT_EUV_ID`** — `pub(crate) static NEXT_EUV_ID: AtomicUsize = AtomicUsize::new(0);`
- `static` **`NEXT_EUV_DYNAMIC_ID`** — `pub(crate) static NEXT_EUV_DYNAMIC_ID: AtomicUsize = AtomicUsize::new(0);`
- `static` **`SIGNAL_UPDATE_DISPATCHING`** — `pub(crate) static SIGNAL_UPDATE_DISPATCHING: AtomicBool = AtomicBool::new(false);`
- `static` **`NEXT_WINDOW_HANDLER_ID`** — `pub(crate) static NEXT_WINDOW_HANDLER_ID: AtomicUsize = AtomicUsize::new(0);`
- `static` **`DIRTY_UPDATE_IDS`** — `pub(crate) static DIRTY_UPDATE_IDS: RefCell<HashSet<usize>> = RefCell::new(HashSet::new());`
- `static` **`HANDLER_REGISTRY`** — `pub(crate) static HANDLER_REGISTRY: RefCell<HandlerRegistryMap> = RefCell::new(HashMap::new());`
- `static` **`DELEGATED_EVENTS`** — `pub(crate) static DELEGATED_EVENTS: RefCell<HashSet<&'static str>> = RefCell::new(HashSet::new());`
- `static` **`SIGNAL_UPDATE_REGISTRY`** — `pub(crate) static SIGNAL_UPDATE_REGISTRY: RefCell<HashMap<usize, SignalUpdateEntry>> = RefCell::new(HashMap::new());`
- `static` **`WINDOW_EVENT_REGISTRY`** — `pub(crate) static WINDOW_EVENT_REGISTRY: RefCell<WindowEventRegistryMap> = RefCell::new(HashMap::new());`
- `static` **`NODEREF_REGISTRY`** — `pub(crate) static NODEREF_REGISTRY: RefCell<NodeRefRegistryMap> = RefCell::new(HashMap::new());`
- `static` **`BINDING_CLEANUPS`** — `pub(crate) static BINDING_CLEANUPS: RefCell<BindingCleanupsMap> = RefCell::new(HashMap::new());`

### `renderer::registry::struct`

- `struct` **`HandlerSlot`** — `pub(crate) struct HandlerSlot {`
- `struct` **`SignalUpdateSlot`** — `pub(crate) struct SignalUpdateSlot {`
- `struct` **`Registry`** — `pub(crate) struct Registry;`

### `renderer::registry::type`

- `type` **`HandlerEntry`** — `pub(crate) type HandlerEntry = *mut HandlerSlot;`
- `type` **`SignalUpdateEntry`** — `pub(crate) type SignalUpdateEntry = *mut SignalUpdateSlot;`
- `type` **`HandlerRegistryMap`** — `pub(crate) type HandlerRegistryMap = HashMap<usize, HashMap<&'static str, HandlerEntry>>;`
- `type` **`WindowEventHandlerEntry`** — `pub(crate) type WindowEventHandlerEntry = (usize, *mut Box<dyn FnMut()>);`
- `type` **`WindowEventRegistryMap`** — `pub(crate) type WindowEventRegistryMap = HashMap<String, Vec<WindowEventHandlerEntry>>;`
- `type` **`NodeRefEntry`** — `pub(crate) type NodeRefEntry = Rc<UnsafeCell<Option<JsValue>>>;`
- `type` **`NodeRefRegistryMap`** — `pub(crate) type NodeRefRegistryMap = HashMap<usize, Vec<NodeRefEntry>>;`
- `type` **`BindingCleanup`** — `pub(crate) type BindingCleanup = Box<dyn FnOnce()>;`
- `type` **`BindingCleanupsMap`** — `pub(crate) type BindingCleanupsMap = HashMap<usize, Vec<BindingCleanup>>;`

### `renderer::render::const`

- `static` **`DOCUMENT_CACHE`** — `pub(crate) static DOCUMENT_CACHE: UnsafeCell<Option<Document>> = const { UnsafeCell::new(None) };`

### `renderer::render::enum`

- `enum` **`ChildOpPlan`** — `pub(crate) enum ChildOpPlan {`

### `renderer::render::fn`

- `fn` **`bind_signal_to_element`** — `pub(crate) fn bind_signal_to_element<T, F>(element: &Element, write: F, signal: Signal<T>) where T: Clone + PartialEq + Display + 'static, F: Fn(&Element, &str) + 'static, {...}`
- `fn` **`lis_indices`** — `pub(crate) fn lis_indices<T: Ord>(keys: &[T]) -> Vec<usize> {...}`
- `fn` **`cached_document`** — `pub(crate) fn cached_document() -> Option<Document> {...}`
- `fn` **`append_nodes`** — `pub(crate) fn append_nodes<I>(parent: &Element, nodes: I) where I: IntoIterator<Item = Node>, {...}`
- `fn` **`compute_child_ops_plan`** — `pub(crate) fn compute_child_ops_plan<'a>( old_keys: &[Option<&'a str>], new_keys: &[Option<&'a str>], ) -> Vec<ChildOpPlan> {...}`
- `fn` **`euv_collect_subtree_ids`** — `pub(crate) fn euv_collect_subtree_ids(root: &Element) -> Float64Array {...}`

### `renderer::render::impl`

- `fn` **`new`** — `pub(crate) fn new(pointer: *mut T) -> Self {...}`
- `fn` **`render`** — `pub(crate) fn render(&mut self, vnode: VirtualNode) {...}`
- `fn` **`render_full_replace`** — `pub(crate) fn render_full_replace(&mut self, vnode: VirtualNode) {...}`
- `fn` **`setup`** — `pub(crate) fn setup<S, F>(selector: S, render_fn: F) where S: AsRef<str>, F: FnOnce() -> VirtualNode, {...}`

### `renderer::render::struct`

- `struct` **`OwnedPtr`** — `pub(crate) struct OwnedPtr<T> {`
- `struct` **`Renderer`** — `pub(crate) struct Renderer {`
- `struct` **`Mount`** — `pub(crate) struct Mount;`
- `struct` **`DynamicRenderState`** — `pub(crate) struct DynamicRenderState {`

### `vdom::attribute::enum`

- `enum` **`AttributeValue`** — `pub enum AttributeValue {`

### `vdom::attribute::fn`

- `fn` **`split_class_names`** — `pub(crate) fn split_class_names(text: &str) -> Vec<String> {...}`

### `vdom::attribute::impl`

- `fn` **`class_names`** — `pub fn class_names(&self) -> Vec<String> {...}`
- `fn` **`text_value`** — `pub fn text_value(&self) -> Option<String> {...}`
- `fn` **`is_injected`** — `pub(crate) fn is_injected(class_name: &str) -> bool {...}`
- `fn` **`mark_injected`** — `pub(crate) fn mark_injected(class_name: &str) {...}`
- `fn` **`reactive`** — `pub fn reactive<F>(compute: F) -> Self where F: Fn() -> String + 'static, {...}`
- `fn` **`merge_class`** — `pub fn merge_class(values: &[Self]) -> Self {...}`
- `fn` **`merge_style`** — `pub fn merge_style(values: &[Self]) -> Self {...}`
- `fn` **`bool_to_attr`** — `pub(crate) fn bool_to_attr(source: Signal<bool>) -> AttributeValue {...}`
- `fn` **`parse_pseudo_rules`** — `pub fn parse_pseudo_rules<I>(input: I) -> Vec<PseudoRule> where I: AsRef<str>, {...}`
- `fn` **`parse_media_rules`** — `pub fn parse_media_rules<S>(input: S) -> Vec<MediaRule> where S: AsRef<str>, {...}`
- `fn` **`inject_style`** — `pub fn inject_style(&self) {...}`
- `fn` **`style_string`** — `pub fn style_string<K, V>(props: &[(K, V)]) -> String where K: AsRef<str>, V: AsRef<str>, {...}`
- `fn` **`param_class_name`** — `pub fn param_class_name(value: &str) -> String {...}`
- `fn` **`style_string_owned`** — `pub fn style_string_owned(props: &[(String, String)]) -> String {...}`
- `fn` **`inject_css`** — `pub fn inject_css<S>(css_text: S) where S: AsRef<str>, {...}`

### `vdom::attribute::static`

- `static` **`INJECTED_CLASSES`** — `pub(crate) static INJECTED_CLASSES: LazyLock<RwLock<HashSet<String>>> = LazyLock::new(|| RwLock::new(HashSet::new()));`

### `vdom::attribute::struct`

- `struct` **`AttributeEntry`** — `pub struct AttributeEntry {`
- `struct` **`PseudoRule`** — `pub struct PseudoRule {`
- `struct` **`Css`** — `pub struct Css {`
- `struct` **`MediaRule`** — `pub struct MediaRule {`
- `struct` **`EventAdapter`** — `pub struct EventAdapter<T> {`
- `struct` **`EventNamedAdapter`** — `pub struct EventNamedAdapter<T> {`
- `struct` **`AttrValueAdapter`** — `pub struct AttrValueAdapter<T> {`
- `struct` **`InnerHtmlAdapter`** — `pub struct InnerHtmlAdapter<T> {`
- `struct` **`CallbackNamedAdapter`** — `pub struct CallbackNamedAdapter<T> {`
- `struct` **`InjectedClassesCell`** — `pub(crate) struct InjectedClassesCell;`

### `vdom::attribute::type`

- `type` **`NodeRefDyn`** — `pub type NodeRefDyn = NodeRef<JsValue>;`
- `type` **`InjectedClassesWriteGuard`** — `pub(crate) type InjectedClassesWriteGuard<'a> = RwLockWriteGuard<'a, HashSet<String>>;`

### `vdom::cast::impl`

- `fn` **`into_inner`** — `pub(crate) fn into_inner(self) -> T {...}`
- `fn` **`into_attribute`** — `pub fn into_attribute(self, event_name: &'static str) -> AttributeValue {...}`
- `fn` **`into_attribute`** — `pub fn into_attribute(self, event_name: &'static str) -> AttributeValue {...}`
- `fn` **`into_attribute`** — `pub fn into_attribute(self, event_name: &'static str) -> AttributeValue {...}`
- `fn` **`into_attribute`** — `pub fn into_attribute(self, event_name: &'static str) -> AttributeValue {...}`
- `fn` **`into_inner`** — `pub(crate) fn into_inner(self) -> T {...}`
- `fn` **`into_inner`** — `pub(crate) fn into_inner(self) -> T {...}`
- `fn` **`into_callback`** — `pub fn into_callback(self) -> AttributeValue {...}`
- `fn` **`into_callback_named`** — `pub fn into_callback_named(self, name: &'static str) -> AttributeValue {...}`
- `fn` **`into_callback_named`** — `pub fn into_callback_named(self, name: &'static str) -> AttributeValue {...}`
- `fn` **`into_callback`** — `pub fn into_callback(self) -> AttributeValue {...}`
- `fn` **`into_callback_named`** — `pub fn into_callback_named(self, name: &'static str) -> AttributeValue {...}`

### `vdom::node::enum`

- `enum` **`Tag`** — `pub enum Tag {`
- `enum` **`VirtualNode`** — `pub enum VirtualNode<T = ()> {`

### `vdom::node::impl`

- `fn` **`render`** — `pub(crate) fn render(&self, hook_context: &mut HookContext) -> VirtualNode {...}`
- `fn` **`try_get_tag_name`** — `pub fn try_get_tag_name(&self) -> Option<String> {...}`
- `fn` **`get_children`** — `pub fn get_children(&self) -> &[VirtualNode] {...}`
- `fn` **`get_first_child`** — `pub fn get_first_child(&self) -> Option<&VirtualNode> {...}`
- `fn` **`has_children`** — `pub fn has_children(&self) -> bool {...}`
- `fn` **`try_get_props`** — `pub fn try_get_props(&self) -> Option<T> where T: Clone, {...}`
- `fn` **`try_get_children`** — `pub fn try_get_children(&self) -> Option<&[VirtualNode]> {...}`
- `fn` **`extend_attributes`** — `pub fn extend_attributes<I>(self, extra: I) -> Self where I: IntoIterator<Item = AttributeEntry>, {...}`
- `fn` **`key`** — `pub fn key(&self) -> Option<&str> {...}`
- `fn` **`has_key`** — `pub fn has_key(&self) -> bool {...}`
- `fn` **`create_dynamic`** — `pub fn create_dynamic<F>(render_fn: F) -> Self where F: FnMut(&mut HookContext) -> Self + 'static, {...}`

### `vdom::node::struct`

- `struct` **`RenderFnInner`** — `pub(crate) struct RenderFnInner {`
- `struct` **`TextNode`** — `pub struct TextNode {`
- `struct` **`DynamicNode`** — `pub struct DynamicNode {`

### `vdom::node::trait`

- `trait` **`AsReactiveText`** — `pub trait AsReactiveText {`

### `vdom::node::type`

- `type` **`TextNodeBinder`** — `pub type TextNodeBinder = Rc<dyn Fn(&Text)>;`

### `vdom::raw::struct`

- `struct` **`RawHtml`** — `pub struct RawHtml {`
