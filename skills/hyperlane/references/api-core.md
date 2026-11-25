# hyperlane-core complete pub API

Source: `core/src/` — auto-extracted from `pub` and `pub(crate)` declarations.

Verified against `origin/master` (`a1846f6`, workspace version `22.8.2`). The
`22.6.0` release added `Context::build_response()` and the request-error helpers
in `protocol::response::fn`; the `22.7.0`/`22.8.0` releases narrowed the public
struct fields to `pub(crate)` without changing the public API. See
[Wire behaviour](wire-behaviour.md).

Re-exported at root via `hyperlane-core::*` (then `hyperlane::*` re-exports it).

`Context::get_request_target()` returns the wire target (path plus query) as
the client spelled it, captured before routing and before the query map is
built. It is `None` for a manually constructed `Context`. The backing
attribute key is `hyperlane.request.target` (`pub(crate)`), so a client cannot
spoof it with a header. The crate-internal helper `request_target(path, query)`
is **not** reachable from outside the crate.

**The crate has a public half and an internal half.** The public half is what
`hyperlane-core` re-exports: `config`, `context`, `error`, `hook`, `route` and
`server`. The internal half is `listener`, `protocol` and `tls`, which are
`pub(crate)` and reach no consumer. `protocol/` is where the wire lives, and it
is nine modules — `aliases`, `constants`, `http2`, `http3`, `inline`, `pump`,
`request`, `response` and `transport` — plus `uring` under
`#[cfg(target_os = "linux")]`, each split again into
`const`/`enum`/`fn`/`impl`/`struct`/`type` files. The former `framing` and
`lifecycle` modules were removed: the framing trait and the server-lifecycle
struct are gone, and `pump` now owns the pooled buffers, the body budget and
the status-code check. `inline` is new — it holds the stack-allocated inline
hook dispatch and the compiled route pipeline. A fix to request framing, the
HTTP/2 or HTTP/3 framer, the connection pump or the transport belongs there —
not in `server`, and never in a route handler.

This page indexes the internal half too, because the rule is "read the source
before you change it". An entry here does **not** mean the item is callable
from outside the crate: `hyperlane::request_target` and every `protocol::`
item stay unreachable.

### `config::enum`

- `enum` **`ServerProtocol`** — `pub enum ServerProtocol`;

### `config::impl`

- `fn` **`get_alpn_protocol`** — `pub fn get_alpn_protocol(&self) -> &'static [u8]`;
- `fn` **`get_version`** — `pub fn get_version(&self) -> HttpVersion`;
- `fn` **`is_quic`** — `pub fn is_quic(&self) -> bool`;
- `fn` **`from_json`** — `pub fn from_json<C>(json: C) -> Result<Self, serde_json::Error> where C: AsRef<str>`;
- `fn` **`get_alpn_protocol`** — `pub fn get_alpn_protocol(&self) -> &'static [u8]`;

### `config::struct`

- `struct` **`TlsConfig`** — `pub struct TlsConfig`;
- `struct` **`ServerConfig`** — `pub struct ServerConfig`;

### `context::impl`

- `fn` **`build_response`** — `pub fn build_response(&mut self) -> ResponseData`;
- `fn` **`reset_request_attributes`** — `pub(crate) fn reset_request_attributes(&mut self) -> &mut Self`;
- `fn` **`clear_route_params`** — `pub(crate) fn clear_route_params(&mut self) -> &mut Self`;
- `fn` **`try_get_route_param`** — `pub fn try_get_route_param<T>(&self, name: T) -> Option<String> where T: AsRef<str>`;
- `fn` **`get_route_param`** — `pub fn get_route_param<T>(&self, name: T) -> String where T: AsRef<str>`;
- `fn` **`get_request_target`** — `pub fn get_request_target(&self) -> Option<String>`;
- `fn` **`get_request_target_ref`** — `pub(crate) fn get_request_target_ref(&self) -> Option<&String>`;
- `fn` **`take_original_target`** — `pub(crate) fn take_original_target(&mut self) -> Option<String>`;
- `fn` **`set_request_target`** — `pub(crate) fn set_request_target<T>(&mut self, target: T) -> &mut Self where T: AsRef<str> + Into<String>`;
- `fn` **`try_get_attribute`** — `pub fn try_get_attribute<V, K>(&self, key: K) -> Option<V> where V: AnySendSyncClone, K: AsRef<str>`;
- `fn` **`get_attribute`** — `pub fn get_attribute<V, K>(&self, key: K) -> V where V: AnySendSyncClone, K: AsRef<str>`;
- `fn` **`set_attribute`** — `pub fn set_attribute<K, V>(&mut self, key: K, value: V) -> &mut Self where K: AsRef<str>, V: AnySendSyncClone`;
- `fn` **`remove_attribute`** — `pub fn remove_attribute<K>(&mut self, key: K) -> &mut Self where K: AsRef<str>`;
- `fn` **`clear_attribute`** — `pub fn clear_attribute(&mut self) -> &mut Self`;
- `fn` **`set_task_panic`** — `pub fn set_task_panic(&mut self, panic_data: PanicData) -> &mut Self`;
- `fn` **`try_get_task_panic_data`** — `pub fn try_get_task_panic_data(&self) -> Option<PanicData>`;
- `fn` **`get_task_panic_data`** — `pub fn get_task_panic_data(&self) -> PanicData`;
- `fn` **`set_request_error_data`** — `pub(crate) fn set_request_error_data(&mut self, request_error: RequestError) -> &mut Self`;
- `fn` **`try_get_request_error_data`** — `pub fn try_get_request_error_data(&self) -> Option<RequestError>`;
- `fn` **`get_request_error_data`** — `pub fn get_request_error_data(&self) -> RequestError`;

### `context::struct`

- `struct` **`Context`** — `pub struct Context`;

### `error::enum`

- `enum` **`ServerError`** — `pub enum ServerError`;
- `enum` **`RouteError`** — `pub enum RouteError`;

### `hook::enum`

- `enum` **`HookType`** — `pub enum HookType`;

### `hook::impl`

- `fn` **`wait`** — `pub fn wait(&self)`;
- `fn` **`shutdown`** — `pub fn shutdown(&self)`;
- `fn` **`default_control_handler`** — `pub fn default_control_handler() -> ServerControlHookHandler<()>`;
- `fn` **`default_handler`** — `pub fn default_handler() -> ServerHookHandler`;
- `fn` **`factory`** — `pub fn factory<R>() -> ServerHookHandler where R: ServerHook`;
- `fn` **`try_get_order`** — `pub fn try_get_order(&self) -> Option<isize>`;
- `fn` **`try_get_hook`** — `pub fn try_get_hook(&self) -> Option<ServerHookHandlerFactory>`;
- `fn` **`assert_unique_order`** — `pub fn assert_unique_order(list: Vec<HookType>)`;

### `hook::struct`

- `struct` **`DefaultServerHook`** — `pub struct DefaultServerHook`;
- `struct` **`Hook`** — `pub struct Hook`;
- `struct` **`ServerControlHook`** — `pub struct ServerControlHook`;

### `hook::trait`

- `trait` **`FnContext`** — `pub trait FnContext<R>: Fn(&mut Context) -> R + Send + Sync`;
- `trait` **`FnContextPinBox`** — `pub trait FnContextPinBox<T>: FnContext<FutureBox<T>>`;
- `trait` **`FnContextStatic`** — `pub trait FnContextStatic<Fut, T>: FnContext<Fut> + 'static where Fut: Future<Output = T> + Send`;
- `trait` **`FutureSendStatic`** — `pub trait FutureSendStatic<T>: Future<Output = T> + Send + 'static`;
- `trait` **`FutureSend`** — `pub trait FutureSend<T>: Future<Output = T> + Send`;
- `trait` **`FutureFn`** — `pub trait FutureFn<T>: Fn() -> FutureBox<T> + Send + Sync`;
- `trait` **`ServerHook`** — `pub trait ServerHook : Send + Sync + 'static`

### `hook::type`

- `type` **`HookHandler`** — `pub type HookHandler<T> = Arc<dyn FnContextPinBox<T>>`;
- `type` **`HookHandlerChain`** — `pub type HookHandlerChain<T> = Vec<HookHandler<T>>`;
- `type` **`FutureBox`** — `pub type FutureBox<T> = Pin<Box<dyn Future<Output = T> + Send>>`;
- `type` **`ServerControlHookHandler`** — `pub type ServerControlHookHandler<T> = Arc<dyn FutureFn<T>>`;
- `type` **`ServerHookHandlerFactory`** — `pub type ServerHookHandlerFactory = fn() -> ServerHookHandler;`
- `type` **`ServerHookHandler`** — `pub type ServerHookHandler = Arc<dyn Fn(&mut Stream, &mut Context) -> FutureBox<Status> + Send + Sync>;`
- `type` **`ServerHookList`** — `pub type ServerHookList = Vec<ServerHookHandler>;`
- `type` **`ServerHookMap`** — `pub type ServerHookMap = HashMapXxHash3_64<String, ServerHookHandler>;`
- `type` **`ServerHookPatternRoute`** — `pub type ServerHookPatternRoute = HashMapXxHash3_64<usize, Vec<(RoutePattern, ServerHookHandler)>>;`

### `route::enum`

- `enum` **`RouteSegment`** — `pub enum RouteSegment`;

### `route::impl`

- `fn` **`new`** — `pub(crate) fn new(route: &str) -> Result<RoutePattern, RouteError>`;
- `fn` **`try_match_path_into`** — `pub(crate) fn try_match_path_into(&self, path: &str, params: &mut RouteParams) -> bool`;
- `fn` **`try_match_path`** — `pub(crate) fn try_match_path(&self, path: &str) -> Option<RouteParams>`;
- `fn` **`is_static`** — `pub(crate) fn is_static(&self) -> bool`;
- `fn` **`is_dynamic`** — `pub(crate) fn is_dynamic(&self) -> bool`;
- `fn` **`segment_count`** — `pub(crate) fn segment_count(&self) -> usize`;
- `fn` **`has_tail_regex`** — `pub(crate) fn has_tail_regex(&self) -> bool`;
- `fn` **`new`** — `pub(crate) fn new() -> Self`;
- `fn` **`add`** — `pub(crate) fn add(&mut self, pattern: &str, hook: ServerHookHandler) -> Result<(), RouteError>`;
- `fn` **`try_resolve_route`** — `pub fn try_resolve_route<'a>( &'a self, ctx: &mut Context, path: &str, ) -> Option<&'a ServerHookHandler>`;

### `route::struct`

- `struct` **`RoutePattern`** — `pub struct RoutePattern( /// The collection of segments that make up the route pattern. pub(super) RouteSegmentList, )`;
- `struct` **`RouteMatcher`** — `pub struct RouteMatcher`;

### `route::type`

- `type` **`RouteParams`** — `pub type RouteParams = HashMapXxHash3_64<String, String>;`
- `type` **`RouteSegmentList`** — `pub type RouteSegmentList = Vec<RouteSegment>;`
- `type` **`PathComponentList`** — `pub(crate) type PathComponentList<'a> = Vec<&'a str>`;

### `server::impl`

- `fn` **`handle_hook`** — `pub fn handle_hook(&mut self, hook: HookType)`;
- `fn` **`config_from_json`** — `pub fn config_from_json<C>(&mut self, json: C) -> &mut Self where C: AsRef<str>`;
- `fn` **`server_config`** — `pub fn server_config(&mut self, config: ServerConfig) -> &mut Self`;
- `fn` **`request_config`** — `pub fn request_config(&mut self, config: RequestConfig) -> &mut Self`;
- `fn` **`task_panic`** — `pub fn task_panic<S>(&mut self) -> &mut Self where S: ServerHook`;
- `fn` **`request_error`** — `pub fn request_error<S>(&mut self) -> &mut Self where S: ServerHook`;
- `fn` **`route`** — `pub fn route<S>(&mut self, path: impl AsRef<str>) -> &mut Self where S: ServerHook`;
- `fn` **`request_middleware`** — `pub fn request_middleware<S>(&mut self) -> &mut Self where S: ServerHook`;
- `fn` **`response_middleware`** — `pub fn response_middleware<S>(&mut self) -> &mut Self where S: ServerHook`;
- `fn` **`format_bind_address`** — `pub fn format_bind_address<H>(host: H, port: u16) -> String where H: AsRef<str>`;
- `fn` **`try_flush_stdout`** — `pub fn try_flush_stdout() -> io::Result<()>`;
- `fn` **`flush_stdout`** — `pub fn flush_stdout()`;
- `fn` **`try_flush_stderr`** — `pub fn try_flush_stderr() -> io::Result<()>`;
- `fn` **`flush_stderr`** — `pub fn flush_stderr()`;
- `fn` **`try_flush_stdout_and_stderr`** — `pub fn try_flush_stdout_and_stderr() -> io::Result<()>`;
- `fn` **`flush_stdout_and_stderr`** — `pub fn flush_stdout_and_stderr()`;
- `fn` **`handle_request_error`** — `pub fn handle_request_error( &self, stream: &mut Stream, ctx: &mut Context, error: &RequestError, )`;
- `fn` **`serve_h1_connection_stream`** — `pub(crate) fn serve_h1_connection_stream( &self, pipeline: &CompiledPipeline, stream: &mut Stream, )`;
- `fn` **`run_protocol_lifecycle_in_place`** — `pub(crate) fn run_protocol_lifecycle_in_place( &self, pipeline: &CompiledPipeline, stream: &mut Stream, ctx: &mut Context, target: String, )`;
- `fn` **`run`** — `pub fn run(&self) -> Result<ServerControlHook, Box<ServerError>>`;

### `server::struct`

- `struct` **`Server`** — `pub struct Server`;

### `listener::fn`

- `fn` **`bind_quic_endpoints`** — `pub(crate) fn bind_quic_endpoints( quic_config: Arc<QuicServerConfig>, bind_addr: SocketAddr, ) -> Result<QuicEndpointSet, Box<ServerError>>`;
- `fn` **`bind_tcp_listeners`** — `pub(crate) fn bind_tcp_listeners( bind_address: &str, nodelay: bool, ) -> Result<Vec<TcpListener>, Box<ServerError>>`;
- `fn` **`tcp_accept_all`** — `pub(crate) fn tcp_accept_all( env: ConnectionEnv, mut listeners: Vec<TcpListener>, shutdown_receiver: Receiver<()>, running_sender: Sender<bool>, )`;
- `fn` **`quic_accept_all`** — `pub(crate) fn quic_accept_all( env: ConnectionEnv, endpoint_set: QuicEndpointSet, shutdown_receiver: Receiver<()>, running_sender: Sender<bool>, )`;
- `fn` **`serve_tcp_connection`** — `pub(crate) fn serve_tcp_connection( env: ConnectionEnv, stream: TcpStream, remote: SocketAddr, )`;
- `fn` **`negotiated_protocol_matches`** — `pub(crate) fn negotiated_protocol_matches<T>( transport: &TlsTransport<T>, protocol: &ServerProtocol, ) -> bool where T: AsyncRead + AsyncWrite + Unpin`;
- `fn` **`negotiated_quic_protocol_matches`** — `pub(crate) fn negotiated_quic_protocol_matches(connection: &quinn::Connection) -> bool`;
- `fn` **`bounded_handshake`** — `pub(crate) fn bounded_handshake<F, T>( request_config: RequestConfig, handshake: F, ) -> Result<T, Elapsed> where F: Future<Output = T>`;
- `fn` **`configure_socket`** — `pub(crate) fn configure_socket(stream: &TcpStream, server: &Server)`;
- `fn` **`serve_plain_tcp`** — `pub(crate) fn serve_plain_tcp(env: ConnectionEnv, peers: StreamPeers, stream: TcpStream)`;
- `fn` **`serve_tls_stream`** — `pub(crate) fn serve_tls_stream( env: ConnectionEnv, peers: StreamPeers, transport: TlsTransport, )`;
- `fn` **`serve_h1_connection`** — `pub(crate) fn serve_h1_connection(env: ConnectionEnv, stream: TcpStream)`;
- `fn` **`serve_h1_transport`** — `pub(crate) fn serve_h1_transport(env: ConnectionEnv, transport: TlsTransport)`;
- `fn` **`serve_h1_stream`** — `pub(crate) fn serve_h1_stream(env: ConnectionEnv, stream: &mut Stream)`;
- `fn` **`catch_connection_panic`** — `pub(crate) fn catch_connection_panic<F>(connection: F) -> Option<PanicData> where F: Future<Output = ()>`;
- `fn` **`panic_data_from_payload`** — `pub(crate) fn panic_data_from_payload(payload: Box<dyn Any + Send>) -> PanicData`;

### `tls::fn`

- `fn` **`build_server_tls_config`** — `pub fn build_server_tls_config( tls: &TlsConfig, alpn: &[u8], versions: &[&'static SupportedProtocolVersion], ) -> Result<Arc<TlsServerConfig>, Box<ServerError>>`;
- `fn` **`build_stream_tls_config`** — `pub fn build_stream_tls_config( tls: &TlsConfig, protocol: &ServerProtocol, ) -> Result<Arc<TlsServerConfig>, Box<ServerError>>`;
- `fn` **`build_quic_tls_config`** — `pub fn build_quic_tls_config(tls: &TlsConfig) -> Result<Arc<TlsServerConfig>, Box<ServerError>>`;

### `tls::type`

- `type` **`SupportedProtocolVersion`** — `pub(crate) type SupportedProtocolVersion = rustls::SupportedProtocolVersion;`
- `type` **`TlsServerConfig`** — `pub(crate) type TlsServerConfig = rustls::ServerConfig;`
- `type` **`TlsError`** — `pub(crate) type TlsError = rustls::Error;`

### `protocol::aliases::type`

- `type` **`ProtocolHeaders`** — `pub(crate) type ProtocolHeaders = HeaderMap;`
- `type` **`ConnectionH2`** — `pub(crate) type ConnectionH2<T> = h2::server::Connection<T, Bytes>`;
- `type` **`H2Error`** — `pub(crate) type H2Error = h2::Error;`
- `type` **`H2RecvStream`** — `pub(crate) type H2RecvStream = h2::RecvStream;`
- `type` **`H2SendStream`** — `pub(crate) type H2SendStream = h2::SendStream<Bytes>;`
- `type` **`H2SendResponse`** — `pub(crate) type H2SendResponse = SendResponse<Bytes>;`
- `type` **`H2ServerBuilder`** — `pub(crate) type H2ServerBuilder = Builder;`
- `type` **`StdTcpListener`** — `pub(crate) type StdTcpListener = net::TcpListener;`
- `type` **`StdUdpSocket`** — `pub(crate) type StdUdpSocket = net::UdpSocket;`
- `type` **`QuicConnection`** — `pub(crate) type QuicConnection = Connection;`
- `type` **`QuicRecvStream`** — `pub(crate) type QuicRecvStream = RecvStream;`
- `type` **`QuicSendStream`** — `pub(crate) type QuicSendStream = SendStream;`
- `type` **`QuicWriteError`** — `pub(crate) type QuicWriteError = WriteError;`
- `type` **`ThreadBuilder`** — `pub(crate) type ThreadBuilder = thread::Builder;`
- `type` **`ThreadJoinHandle`** — `pub(crate) type ThreadJoinHandle<T> = thread::JoinHandle<T>`;
- `type` **`RuntimeBuilder`** — `pub(crate) type RuntimeBuilder = runtime::Builder;`
- `type` **`StdRwLock`** — `pub(crate) type StdRwLock<T> = sync::RwLock<T>`;
- `type` **`AtomicOrdering`** — `pub(crate) type AtomicOrdering = sync::atomic::Ordering;`
- `type` **`ProtocolRequest`** — `pub(crate) type ProtocolRequest<T> = http::Request<T>`;
- `type` **`ProtocolResponse`** — `pub(crate) type ProtocolResponse<T> = http::Response<T>`;
- `type` **`ProtocolMethod`** — `pub(crate) type ProtocolMethod = http::Method;`
- `const` **`LF_U8`** — `pub(crate) const LF_U8 : u8 = b'\n'`
- `const` **`CR_U8`** — `pub(crate) const CR_U8 : u8 = b'\r'`
- `const` **`CRLF`** — `pub(crate) const CRLF : &str = "\r\n"`
- `const` **`HTTP_VERSION_PREFIX`** — `pub(crate) const HTTP_VERSION_PREFIX : &str = "HTTP/"`
- `type` **`SplitLines`** — `pub(crate) type SplitLines<'a> = Split<'a, &'static str>`;
- `const` **`COMMA_STR`** — `pub(crate) const COMMA_STR : &str = ","`
- `const` **`LF_CHAR`** — `pub(crate) const LF_CHAR : char = '\n'`
- `const` **`MISSING_RESPONSE_VERSION`** — `pub(crate) const MISSING_RESPONSE_VERSION : &str = "response head has no version line"`
- `const` **`MISSING_RESPONSE_STATUS`** — `pub(crate) const MISSING_RESPONSE_STATUS : &str = "response head has no status code"`
- `const` **`CONTENT_LENGTH_MISMATCH`** — `pub(crate) const CONTENT_LENGTH_MISMATCH : &str = "request body length does not match its content-length"`

### `protocol::constants::const`

- `const` **`HTTP_QUOTED_FIELD_QUOTE`** — `pub(crate) const HTTP_QUOTED_FIELD_QUOTE : u8 = b'"'`
- `const` **`HTTP_QUOTED_FIELD_ESCAPE`** — `pub(crate) const HTTP_QUOTED_FIELD_ESCAPE : u8 = b'\\'`
- `const` **`PSEUDO_HEADER_PREFIX`** — `pub(crate) const PSEUDO_HEADER_PREFIX : &str = ":"`
- `const` **`QUESTION_MARK`** — `pub(crate) const QUESTION_MARK : char = '?'`
- `const` **`AT_SIGN`** — `pub(crate) const AT_SIGN : char = '@'`
- `const` **`TRAILER_HEADER`** — `pub(crate) const TRAILER_HEADER : &str = "trailer"`
- `const` **`HTTP_SCHEME`** — `pub(crate) const HTTP_SCHEME : &str = "http"`
- `const` **`HTTPS_SCHEME`** — `pub(crate) const HTTPS_SCHEME : &str = "https"`
- `const` **`RESPONSE_HEAD_MAX`** — `pub(crate) const RESPONSE_HEAD_MAX : usize = 16 * 1024`
- `const` **`RESPONSE_HEAD_TOO_LONG`** — `pub(crate) const RESPONSE_HEAD_TOO_LONG : &str = "response head exceeds its bound"`
- `const` **`MISSING_RESPONSE_HEAD`** — `pub(crate) const MISSING_RESPONSE_HEAD : &str = "response ended before a head was written"`
- `const` **`UNSUPPORTED_TRANSFER_ENCODING`** — `pub(crate) const UNSUPPORTED_TRANSFER_ENCODING : &str = "response transfer-encoding is not supported on this protocol"`
- `const` **`STATIC_CT_HTML_UTF8`** — `pub(crate) const STATIC_CT_HTML_UTF8 : &str = "text/html`
- `const` **`STATIC_CT_PLAIN`** — `pub(crate) const STATIC_CT_PLAIN : &str = "text/plain"`
- `const` **`STATIC_CT_PLAIN_UTF8`** — `pub(crate) const STATIC_CT_PLAIN_UTF8 : &str = "text/plain`
- `const` **`STATIC_CT_JSON`** — `pub(crate) const STATIC_CT_JSON : &str = "application/json"`
- `const` **`INVALID_RESPONSE_STATUS`** — `pub(crate) const INVALID_RESPONSE_STATUS : &str = "response head has an unusable status code"`
- `const` **`MALFORMED_RESPONSE_HEADER`** — `pub(crate) const MALFORMED_RESPONSE_HEADER : &str = "response head has a malformed header line"`
- `const` **`TRUNCATED_RESPONSE_BODY`** — `pub(crate) const TRUNCATED_RESPONSE_BODY : &str = "response ended before the announced content length arrived"`
- `const` **`OVERFLOWING_RESPONSE_BODY`** — `pub(crate) const OVERFLOWING_RESPONSE_BODY : &str = "response carried more bytes than the announced content length"`
- `const` **`MISSING_SEND_CAPACITY`** — `pub(crate) const MISSING_SEND_CAPACITY : &str = "the send stream was closed before capacity was granted"`
- `const` **`MIN_STATUS_CODE`** — `pub(crate) const MIN_STATUS_CODE : usize = 100`
- `const` **`MAX_STATUS_CODE`** — `pub(crate) const MAX_STATUS_CODE : usize = 999`

### `protocol::inline::const`

- `const` **`INLINE_FUTURE_WORDS`** — `pub(crate) const INLINE_FUTURE_WORDS : usize = 32`

### `protocol::inline::enum`

- `enum` **`InlinePollState`** — `pub(crate) enum InlinePollState`;
- `enum` **`CompiledHook`** — `pub(crate) enum CompiledHook`;

### `protocol::inline::fn`

- `fn` **`register_inline_hook`** — `pub(crate) fn register_inline_hook(key: usize, init: InlineInitFn)`;
- `fn` **`unregister_inline_hook`** — `pub(crate) fn unregister_inline_hook(key: usize)`;
- `fn` **`lookup_inline_hook`** — `pub(crate) fn lookup_inline_hook(handler: &ServerHookHandler) -> CompiledHook`;
- `fn` **`inline_init_hook`** — `pub(crate) fn inline_init_hook<R>( stream_addr: usize, ctx_addr: usize, slot: *mut u8, slot_len: usize, ) -> InlinePollState where R: ServerHook`;

### `protocol::inline::impl`

- `fn` **`new`** — `pub(crate) fn new(stream: &'a mut Stream, ctx: &'a mut Context, init: InlineInitFn) -> Self`;
- `fn` **`call`** — `pub(crate) fn call(&self, stream: &mut Stream, ctx: &mut Context) -> Status`;
- `fn` **`from_server`** — `pub(crate) fn from_server(server: &Server) -> Self`;
- `fn` **`resolve_route`** — `pub(crate) fn resolve_route( &self, params: &mut RouteParams, path: &str, ) -> Option<&CompiledHook>`;
- `fn` **`run_request`** — `pub(crate) fn run_request( &self, stream: &mut Stream, ctx: &mut Context, target: Option<String>, ) -> bool`;

### `protocol::inline::static`

- `static` **`INLINE_HOOK_REGISTRY`** — `pub(crate) static INLINE_HOOK_REGISTRY : OnceLock<StdRwLock<HashMap<usize, InlineInitFn>>> = OnceLock::new()`

### `protocol::inline::struct`

- `struct` **`InlineHookGuard`** — `pub(crate) struct InlineHookGuard`;
- `struct` **`InlineHookCall`** — `pub(crate) struct InlineHookCall<'a>`;
- `struct` **`CompiledPipeline`** — `pub(crate) struct CompiledPipeline`;

### `protocol::inline::type`

- `type` **`InlinePollFn`** — `pub(crate) type InlinePollFn = unsafe fn(*mut u8, &mut task::Context<'_>) -> Poll<Status>;`
- `type` **`InlineDropFn`** — `pub(crate) type InlineDropFn = unsafe fn(*mut u8);`
- `type` **`InlineInitFn`** — `pub(crate) type InlineInitFn = fn(usize, usize, *mut u8, usize) -> InlinePollState;`
- `type` **`CompiledHookMap`** — `pub(crate) type CompiledHookMap = HashMapXxHash3_64<String, CompiledHook>;`
- `type` **`CompiledPatternRoutes`** — `pub(crate) type CompiledPatternRoutes = HashMapXxHash3_64<usize, Vec<(RoutePattern, CompiledHook)>>;`

### `protocol::http2::fn`

- `fn` **`serve_h2_connection`** — `pub(crate) fn serve_h2_connection<T>( env: ConnectionEnv, peers: StreamPeers, connection: Result<ConnectionH2<T>, String>, ) where T: AsyncRead + AsyncWrite + Unpin + Send + Sync + 'static`;
- `fn` **`h2_request_task`** — `pub(crate) fn h2_request_task( env: H2RequestEnv, request: ProtocolRequest<H2RecvStream>, mut send_response: H2SendResponse, )`;
- `fn` **`h2_fail_request`** — `pub(crate) fn h2_fail_request( server: &Server, request_config: RequestConfig, peers: StreamPeers, send_response: H2SendResponse, ctx: &mut Context, version: HttpVersion, error: RequestError, )`;

### `protocol::http2::impl`

- `fn` **`new`** — `pub(crate) fn new(send_response: H2SendResponse, peers: StreamPeers, is_head: bool) -> Self`;

### `protocol::http2::struct`

- `struct` **`H2DirectState`** — `pub(crate) struct H2DirectState`;
- `struct` **`H2DirectTransport`** — `pub(crate) struct H2DirectTransport`;
- `struct` **`H2RequestEnv`** — `pub(crate) struct H2RequestEnv`;

### `protocol::http3::stream::fn`

- `fn` **`take_h3_buffer`** — `pub(crate) fn take_h3_buffer() -> Vec<u8>`;
- `fn` **`return_h3_buffer`** — `pub(crate) fn return_h3_buffer(mut buffer: Vec<u8>)`;
- `fn` **`serve_h3_connection`** — `pub(crate) fn serve_h3_connection( env: ConnectionEnv, peers: StreamPeers, connection: QuicConnection, )`;
- `fn` **`h3_request_task`** — `pub(crate) fn h3_request_task( env: H3RequestEnv, connection: &QuicConnection, mut send_stream: QuicSendStream, mut recv_stream: QuicRecvStream, )`;
- `fn` **`h3_fail_request`** — `pub(crate) fn h3_fail_request( server: &Server, request_config: RequestConfig, peers: StreamPeers, send_stream: QuicSendStream, ctx: &mut Context, version: HttpVersion, error: RequestError, )`;

### `protocol::http3::stream::impl`

- `fn` **`new`** — `pub(crate) fn new(send_stream: QuicSendStream, peers: StreamPeers, is_head: bool) -> Self`;

### `protocol::http3::stream::struct`

- `struct` **`H3DirectState`** — `pub(crate) struct H3DirectState`;
- `struct` **`H3DirectTransport`** — `pub(crate) struct H3DirectTransport`;
- `struct` **`H3ControlState`** — `pub(crate) struct H3ControlState`;
- `struct` **`H3RequestEnv`** — `pub(crate) struct H3RequestEnv`;

### `protocol::pump::const`

- `const` **`MAX_POOLED_BUFFER_CAPACITY`** — `pub(crate) const MAX_POOLED_BUFFER_CAPACITY : usize = 64 * 1024`
- `const` **`MAX_POOLED_CONTEXTS`** — `pub(crate) const MAX_POOLED_CONTEXTS : usize = 64`
- `const` **`MAX_POOLED_PROTOCOL_HEADERS`** — `pub(crate) const MAX_POOLED_PROTOCOL_HEADERS : usize = 256`
- `const` **`MAX_POOLED_STRING_CAPACITY`** — `pub(crate) const MAX_POOLED_STRING_CAPACITY : usize = 4 * 1024`

### `protocol::pump::fn`

- `fn` **`take_pooled_context`** — `pub(crate) fn take_pooled_context() -> Context`;
- `fn` **`return_pooled_context`** — `pub(crate) fn return_pooled_context(mut ctx: Context)`;
- `fn` **`take_protocol_header_entry`** — `pub(crate) fn take_protocol_header_entry() -> Option<(String, VecDeque<String>)>`;
- `fn` **`take_target_buffer`** — `pub(crate) fn take_target_buffer() -> String`;
- `fn` **`return_target_buffer`** — `pub(crate) fn return_target_buffer(mut buffer: String)`;
- `fn` **`take_route_param_entry`** — `pub(crate) fn take_route_param_entry() -> (String, String)`;
- `fn` **`return_route_param_entry`** — `pub(crate) fn return_route_param_entry(mut pair: (String, String))`;
- `fn` **`poll_once_protocol`** — `pub(crate) fn poll_once_protocol<F>(mut future: Pin<&mut F>) -> Option<F::Output> where F: Future`;
- `fn` **`hides_entity_length`** — `pub(crate) fn hides_entity_length(status_code: usize, _is_head: bool) -> bool`;
- `fn` **`check_body_budget`** — `pub(crate) fn check_body_budget( announced_len: Option<usize>, forwarded: usize, incoming: usize, ) -> bool`;
- `fn` **`validate_status_code`** — `pub(crate) fn validate_status_code(status_code: usize) -> Result<(), ResponseError>`;

### `protocol::pump::static`

- `static` **`CONTEXT_POOL`** — `pub(crate) static CONTEXT_POOL : RefCell<Vec<Context>> = const`
- `static` **`PROTOCOL_HEADER_POOL`** — `pub(crate) static PROTOCOL_HEADER_POOL : RefCell<Vec<(String, VecDeque<String>)>> = const`
- `static` **`TARGET_BUFFER_POOL`** — `pub(crate) static TARGET_BUFFER_POOL : RefCell<Vec<String>> = const`
- `static` **`ROUTE_PARAM_POOL`** — `pub(crate) static ROUTE_PARAM_POOL : RefCell<Vec<(String, String)>> = const`

### `protocol::request::fn`

- `fn` **`fill_protocol_request`** — `pub(crate) fn fill_protocol_request( config: &RequestConfig, head: ProtocolRequestHead, request: &mut Request, target: &mut String, ) -> Result<(), RequestError>`;
- `fn` **`write_request_host`** — `pub(crate) fn write_request_host(headers: &ProtocolHeaders, uri: &Uri, out: &mut String)`;
- `fn` **`write_request_target`** — `pub(crate) fn write_request_target(path: &str, query: Option<&str>, target: &mut String)`;
- `fn` **`check_request_authority`** — `pub fn check_request_authority(headers: &ProtocolHeaders, uri: &Uri) -> Result<(), RequestError>`;
- `fn` **`same_authority`** — `pub fn same_authority(authority: &str, host: &str, scheme: Option<&str>) -> bool`;
- `fn` **`normalize_authority`** — `pub fn normalize_authority(authority: &str, scheme: Option<&str>) -> (String, Option<String>)`;
- `fn` **`split_authority_port`** — `pub fn split_authority_port(authority: &str) -> (&str, Option<&str>)`;
- `fn` **`split_target_query`** — `pub fn split_target_query( target: &str, query_index: Option<usize>, hash_index: Option<usize>, ) -> &str`;
- `fn` **`split_target_path`** — `pub fn split_target_path( target: &str, query_index: Option<usize>, hash_index: Option<usize>, ) -> &str`;
- `fn` **`fill_request_querys`** — `pub fn fill_request_querys(query: &str, querys: &mut RequestQuerys)`;
- `fn` **`protocol_method`** — `pub fn protocol_method(method: ProtocolMethod) -> RequestMethod`;
- `fn` **`fill_request_headers`** — `pub fn fill_request_headers( headers: &ProtocolHeaders, config: &RequestConfig, request: &mut Request, ) -> Result<(), RequestError>`;
- `fn` **`is_hop_by_hop`** — `pub fn is_hop_by_hop(name: &str) -> bool`;
- `fn` **`declared_content_length`** — `pub fn declared_content_length( headers: &ProtocolHeaders, max_body_size: usize, ) -> Result<Option<usize>, RequestError>`;
- `fn` **`has_continue_expectation`** — `pub(crate) fn has_continue_expectation(headers: &ProtocolHeaders) -> bool`;
- `fn` **`parse_ascii_length`** — `pub(crate) fn parse_ascii_length(value: &str) -> Result<usize, RequestError>`;
- `fn` **`is_bodyless_status`** — `pub fn is_bodyless_status(status_code: usize, is_head: bool) -> bool`;
- `fn` **`push_bounded_body`** — `pub fn push_bounded_body( limit: usize, body: &mut Vec<u8>, chunk: Bytes, ) -> Result<(), RequestError>`;
- `fn` **`request_target`** — `pub fn request_target(path: &str, query: Option<&str>) -> String`;

### `protocol::request::struct`

- `struct` **`ProtocolRequestHead`** — `pub(crate) struct ProtocolRequestHead`;

### `protocol::response::fn`

- `fn` **`h1_error_response_version`** — `pub(crate) fn h1_error_response_version( stream: &Stream, error: &RequestError, ) -> Option<HttpVersion>`;
- `fn` **`reply_to_request_error`** — `pub(crate) fn reply_to_request_error( server: &Server, stream: &mut Stream, ctx: &mut Context, error: &RequestError, version: Option<HttpVersion>, )`;
- `fn` **`continue_response`** — `pub(crate) fn continue_response() -> ProtocolResponse<()>`;
- `fn` **`find_head_end`** — `pub fn find_head_end(buffer: &[u8]) -> Option<usize>`;
- `fn` **`find_line_end`** — `pub fn find_line_end(bytes: &[u8]) -> Option<usize>`;
- `fn` **`parse_protocol_response_head`** — `pub(crate) fn parse_protocol_response_head( head: &[u8], is_head: bool, ) -> Result<ParsedProtocolHead, ResponseError>`;
- `fn` **`parse_response_head`** — `pub fn parse_response_head(head: &[u8]) -> Result<(usize, ProtocolHeaders), ResponseError>`;
- `fn` **`has_transfer_encoding`** — `pub fn has_transfer_encoding(headers: &ProtocolHeaders) -> bool`;
- `fn` **`parse_content_length`** — `pub fn parse_content_length(headers: &ProtocolHeaders) -> Result<Option<usize>, ResponseError>`;
- `fn` **`connection_nominates`** — `pub fn connection_nominates(headers: &ProtocolHeaders, name: &str) -> bool`;

### `protocol::response::struct`

- `struct` **`ParsedProtocolHead`** — `pub(crate) struct ParsedProtocolHead`;

### `protocol::transport::const`

- `const` **`TLS_RECORD_BUFFER_SIZE`** — `pub(crate) const TLS_RECORD_BUFFER_SIZE : usize = 18 * 1024`
- `const` **`TLS_MAX_PLAINTEXT_CHUNK`** — `pub(crate) const TLS_MAX_PLAINTEXT_CHUNK : usize = 16 * 1024`
- `const` **`TLS_MAX_INCOMING_BUFFER`** — `pub(crate) const TLS_MAX_INCOMING_BUFFER : usize = 64 * 1024`
- `const` **`MAX_POOLED_TLS_BUFFERS`** — `pub(crate) const MAX_POOLED_TLS_BUFFERS : usize = 64`
- `const` **`TLS_TRANSMIT_WRITE_ZERO`** — `pub(crate) const TLS_TRANSMIT_WRITE_ZERO : &str = "tcp write zero during tls transmit"`

### `protocol::transport::fn`

- `fn` **`take_tls_buffer`** — `pub(crate) fn take_tls_buffer(size: usize) -> Vec<u8>`;
- `fn` **`return_tls_buffer`** — `pub(crate) fn return_tls_buffer(buf: Vec<u8>)`;
- `fn` **`accept_unbuffered_tls`** — `pub(crate) fn accept_unbuffered_tls<T>( config: Arc<TlsServerConfig>, mut tcp: T, ) -> Result<TlsTransport<T>, io::Error> where T: AsyncRead + AsyncWrite + Unpin`;

### `protocol::transport::impl`

- `fn` **`alpn_protocol`** — `pub(crate) fn alpn_protocol(&self) -> Option<&[u8]>`;

### `protocol::transport::static`

- `static` **`TLS_BUFFER_POOL`** — `pub(crate) static TLS_BUFFER_POOL : RefCell<Vec<Vec<u8>>> = const`

### `protocol::transport::struct`

- `struct` **`TlsTransport`** — `pub(crate) struct TlsTransport<T = TcpStream>`;
- `struct` **`ConnectionShared`** — `pub(crate) struct ConnectionShared`;
- `struct` **`ConnectionEnv`** — `pub(crate) struct ConnectionEnv`;
- `struct` **`StreamPeers`** — `pub(crate) struct StreamPeers`;
