# hyperlane-core complete pub API

Source: `core/src/` — auto-extracted from `pub` declarations.

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
is eleven modules — `aliases`, `constants`, `framing`, `http2`, `http3`,
`lifecycle`, `pump`, `request`, `response` and `transport`, each split again
into `const`/`enum`/`fn`/`impl`/`struct`/`type` files. A fix to request
framing, the HTTP/2 or HTTP/3 framer, the connection pump or the transport
belongs there — not in `server`, and never in a route handler.

This page indexes the internal half too, because the rule is "read the source
before you change it". An entry here does **not** mean the item is callable
from outside the crate: `hyperlane::request_target` and every `protocol::`
item stay unreachable.


### `config::enum`

- `enum` **`ServerProtocol`** — `pub enum ServerProtocol {`

### `config::impl`

- `fn` **`from_json`** — `pub fn from_json<C>(json: C) -> Result<Self, serde_json::Error> where C: AsRef<str>, {...}`
- `fn` **`get_alpn_protocol`** — `pub fn get_alpn_protocol(&self) -> &'static [u8] {...}`
- `fn` **`get_version`** — `pub fn get_version(&self) -> HttpVersion {...}`
- `fn` **`is_quic`** — `pub fn is_quic(&self) -> bool {...}`
- `fn` **`get_alpn_protocol`** — `pub fn get_alpn_protocol(&self) -> &'static [u8] {...}`

### `config::struct`

- `struct` **`ServerConfig`** — `pub struct ServerConfig {`
- `struct` **`TlsConfig`** — `pub struct TlsConfig {`

### `context::impl`

- `fn` **`clear_route_params`** — `pub(crate) fn clear_route_params(&mut self) -> &mut Self {...}`
- `fn` **`try_get_route_param`** — `pub fn try_get_route_param<T>(&self, name: T) -> Option<String> where T: AsRef<str>, {...}`
- `fn` **`get_route_param`** — `pub fn get_route_param<T>(&self, name: T) -> String where T: AsRef<str>, {...}`
- `fn` **`get_request_target`** — `pub fn get_request_target(&self) -> Option<String> {...}`
- `fn` **`set_request_target`** — `pub(crate) fn set_request_target(&mut self, target: String) -> &mut Self {...}`
- `fn` **`try_get_attribute`** — `pub fn try_get_attribute<V, K>(&self, key: K) -> Option<V> where V: AnySendSyncClone, K: AsRef<str>, {...}`
- `fn` **`get_attribute`** — `pub fn get_attribute<V, K>(&self, key: K) -> V where V: AnySendSyncClone, K: AsRef<str>, {...}`
- `fn` **`set_attribute`** — `pub fn set_attribute<K, V>(&mut self, key: K, value: V) -> &mut Self where K: AsRef<str>, V: AnySendSyncClone, {...}`
- `fn` **`remove_attribute`** — `pub fn remove_attribute<K>(&mut self, key: K) -> &mut Self where K: AsRef<str>, {...}`
- `fn` **`clear_attribute`** — `pub fn clear_attribute(&mut self) -> &mut Self {...}`
- `fn` **`set_task_panic`** — `pub fn set_task_panic(&mut self, panic_data: PanicData) -> &mut Self {...}`
- `fn` **`try_get_task_panic_data`** — `pub fn try_get_task_panic_data(&self) -> Option<PanicData> {...}`
- `fn` **`get_task_panic_data`** — `pub fn get_task_panic_data(&self) -> PanicData {...}`
- `fn` **`set_request_error_data`** — `pub(crate) fn set_request_error_data(&mut self, request_error: RequestError) -> &mut Self {...}`
- `fn` **`try_get_request_error_data`** — `pub fn try_get_request_error_data(&self) -> Option<RequestError> {...}`
- `fn` **`get_request_error_data`** — `pub fn get_request_error_data(&self) -> RequestError {...}`

### `context::struct`

- `struct` **`Context`** — `pub struct Context {`

### `error::enum`

- `enum` **`ServerError`** — `pub enum ServerError {`
- `enum` **`RouteError`** — `pub enum RouteError {`

### `hook::enum`

- `enum` **`HookType`** — `pub enum HookType {`

### `hook::impl`

- `fn` **`wait`** — `pub async fn wait(&self) {...}`
- `fn` **`shutdown`** — `pub async fn shutdown(&self) {...}`
- `fn` **`default_control_handler`** — `pub fn default_control_handler() -> ServerControlHookHandler<()> {...}`
- `fn` **`default_handler`** — `pub fn default_handler() -> ServerHookHandler {...}`
- `fn` **`factory`** — `pub fn factory<R>() -> ServerHookHandler where R: ServerHook, {...}`
- `fn` **`try_get_order`** — `pub fn try_get_order(&self) -> Option<isize> {...}`
- `fn` **`try_get_hook`** — `pub fn try_get_hook(&self) -> Option<ServerHookHandlerFactory> {...}`
- `fn` **`assert_unique_order`** — `pub fn assert_unique_order(list: Vec<HookType>) {...}`

### `hook::struct`

- `struct` **`DefaultServerHook`** — `pub struct DefaultServerHook;`
- `struct` **`Hook`** — `pub struct Hook;`
- `struct` **`ServerControlHook`** — `pub struct ServerControlHook {`

### `hook::trait`

- `trait` **`FnContext`** — `pub trait FnContext<R>: Fn(&mut Context) -> R + Send + Sync {}`
- `trait` **`FnContextPinBox`** — `pub trait FnContextPinBox<T>: FnContext<FutureBox<T>> {}`
- `trait` **`FnContextStatic`** — `pub trait FnContextStatic<Fut, T>: FnContext<Fut> + 'static where Fut: Future<Output = T> + Send, {}`
- `trait` **`FutureSendStatic`** — `pub trait FutureSendStatic<T>: Future<Output = T> + Send + 'static {}`
- `trait` **`FutureSend`** — `pub trait FutureSend<T>: Future<Output = T> + Send {}`
- `trait` **`FutureFn`** — `pub trait FutureFn<T>: Fn() -> FutureBox<T> + Send + Sync {}`
- `trait` **`ServerHook`** — `pub trait ServerHook: Send + Sync + 'static {`

### `hook::type`

- `type` **`HookHandler`** — `pub type HookHandler<T> = Arc<dyn FnContextPinBox<T>>;`
- `type` **`HookHandlerChain`** — `pub type HookHandlerChain<T> = Vec<HookHandler<T>>;`
- `type` **`FutureBox`** — `pub type FutureBox<T> = Pin<Box<dyn Future<Output = T> + Send>>;`
- `type` **`ServerControlHookHandler`** — `pub type ServerControlHookHandler<T> = Arc<dyn FutureFn<T>>;`
- `type` **`ServerHookHandlerFactory`** — `pub type ServerHookHandlerFactory = fn() -> ServerHookHandler;`
- `type` **`ServerHookHandler`** — `pub type ServerHookHandler = Arc<dyn Fn(&mut Stream, &mut Context) -> FutureBox<Status> + Send + Sync>;`
- `type` **`ServerHookList`** — `pub type ServerHookList = Vec<ServerHookHandler>;`
- `type` **`ServerHookMap`** — `pub type ServerHookMap = HashMapXxHash3_64<String, ServerHookHandler>;`
- `type` **`ServerHookPatternRoute`** — `pub type ServerHookPatternRoute = HashMapXxHash3_64<usize, Vec<(RoutePattern, ServerHookHandler)>>;`

### `route::enum`

- `enum` **`RouteSegment`** — `pub enum RouteSegment {`

### `route::impl`

- `fn` **`new`** — `pub(crate) fn new(route: &str) -> Result<RoutePattern, RouteError> {...}`
- `fn` **`try_match_path`** — `pub(crate) fn try_match_path(&self, path: &str) -> Option<RouteParams> {...}`
- `fn` **`is_static`** — `pub(crate) fn is_static(&self) -> bool {...}`
- `fn` **`is_dynamic`** — `pub(crate) fn is_dynamic(&self) -> bool {...}`
- `fn` **`segment_count`** — `pub(crate) fn segment_count(&self) -> usize {...}`
- `fn` **`has_tail_regex`** — `pub(crate) fn has_tail_regex(&self) -> bool {...}`
- `fn` **`new`** — `pub(crate) fn new() -> Self {...}`
- `fn` **`add`** — `pub(crate) fn add(&mut self, pattern: &str, hook: ServerHookHandler) -> Result<(), RouteError> {...}`
- `fn` **`try_resolve_route`** — `pub fn try_resolve_route<'a>( &'a self, ctx: &mut Context, path: &str, ) -> Option<&'a ServerHookHandler> {...}`

- `fn` **`try_resolve_static_route`** — `pub(crate) fn try_resolve_static_route<'a>( &'a self, path: &str, ) -> Option<&'a ServerHookHandler> {...}`

### `route::struct`

- `struct` **`RoutePattern`** — `pub struct RoutePattern( pub(super) RouteSegmentList, );`
- `struct` **`RouteMatcher`** — `pub struct RouteMatcher {`

### `route::type`

- `type` **`RouteParams`** — `pub type RouteParams = HashMapXxHash3_64<String, String>;`
- `type` **`RouteSegmentList`** — `pub type RouteSegmentList = Vec<RouteSegment>;`
- `type` **`PathComponentList`** — `pub(crate) type PathComponentList<'a> = Vec<&'a str>;`

### `server::impl`

- `fn` **`handle_hook`** — `pub fn handle_hook(&mut self, hook: HookType) {...}`
- `fn` **`config_from_json`** — `pub fn config_from_json<C>(&mut self, json: C) -> &mut Self where C: AsRef<str>, {...}`
- `fn` **`server_config`** — `pub fn server_config(&mut self, config: ServerConfig) -> &mut Self {...}`
- `fn` **`request_config`** — `pub fn request_config(&mut self, config: RequestConfig) -> &mut Self {...}`
- `fn` **`task_panic`** — `pub fn task_panic<S>(&mut self) -> &mut Self where S: ServerHook, {...}`
- `fn` **`request_error`** — `pub fn request_error<S>(&mut self) -> &mut Self where S: ServerHook, {...}`
- `fn` **`route`** — `pub fn route<S>(&mut self, path: impl AsRef<str>) -> &mut Self where S: ServerHook, {...}`
- `fn` **`request_middleware`** — `pub fn request_middleware<S>(&mut self) -> &mut Self where S: ServerHook, {...}`
- `fn` **`response_middleware`** — `pub fn response_middleware<S>(&mut self) -> &mut Self where S: ServerHook, {...}`
- `fn` **`format_bind_address`** — `pub fn format_bind_address<H>(host: H, port: u16) -> String where H: AsRef<str>, {...}`
- `fn` **`try_flush_stdout`** — `pub fn try_flush_stdout() -> io::Result<()> {...}`
- `fn` **`flush_stdout`** — `pub fn flush_stdout() {...}`
- `fn` **`try_flush_stderr`** — `pub fn try_flush_stderr() -> io::Result<()> {...}`
- `fn` **`flush_stderr`** — `pub fn flush_stderr() {...}`
- `fn` **`try_flush_stdout_and_stderr`** — `pub fn try_flush_stdout_and_stderr() -> io::Result<()> {...}`
- `fn` **`flush_stdout_and_stderr`** — `pub fn flush_stdout_and_stderr() {...}`
- `fn` **`handle_request_middleware`** — `pub(super) async fn handle_request_middleware( &self, stream: &mut Stream, ctx: &mut Context, ) -> bool {...}`
- `fn` **`handle_route_matcher`** — `pub(super) async fn handle_route_matcher( &self, stream: &mut Stream, ctx: &mut Context, path: &str, ) -> bool {...}`
- `fn` **`handle_response_middleware`** — `pub(super) async fn handle_response_middleware( &self, stream: &mut Stream, ctx: &mut Context, ) -> bool {...}`
- `fn` **`handle_request_error`** — `pub async fn handle_request_error( &self, stream: &mut Stream, ctx: &mut Context, error: &RequestError, ) {...}`
- `fn` **`run`** — `pub async fn run(&self) -> Result<ServerControlHook, Box<ServerError>> {...}`

- `fn` **`request_hook`** — `pub(crate) async fn request_hook( &self, stream: &mut Stream, ctx: &mut Context, request: Request, target: Option<String>, ) -> bool {...}`
- `fn` **`serve_h1_connection_stream`** — `pub(crate) async fn serve_h1_connection_stream(&self, stream: &mut Stream) {...}`
- `fn` **`run_protocol_lifecycle`** — `pub(crate) async fn run_protocol_lifecycle( &self, stream: &mut Stream, ctx: &mut Context, request: Request, target: String, ) {...}`

### `server::struct`

- `struct` **`Server`** — `pub struct Server {`

### `listener::fn`

- `fn` **`tcp_accept`** — `pub(crate) async fn tcp_accept( env: ConnectionEnv, stream_tls: Option<Arc<rustls::ServerConfig>>, signal: AcceptSignal, ) {...}`
- `fn` **`serve_tcp_connection`** — `pub(crate) async fn serve_tcp_connection( env: ConnectionEnv, stream_tls: Option<Arc<rustls::ServerConfig>>, stream: TcpStream, remote: SocketAddr, ) {...}`
- `fn` **`negotiated_protocol_matches`** — `pub(crate) fn negotiated_protocol_matches( session: &tokio_rustls::server::TlsStream<TcpStream>, protocol: &ServerProtocol, ) -> bool {...}`
- `fn` **`negotiated_quic_protocol_matches`** — `pub(crate) fn negotiated_quic_protocol_matches(connection: &quinn::Connection) -> bool {...}`
- `fn` **`bounded_handshake`** — `pub(crate) async fn bounded_handshake<F, T>( request_config: RequestConfig, handshake: F, ) -> Result<T, tokio::time::error::Elapsed> where F: Future<Output = T>, {...}`
- `fn` **`configure_socket`** — `pub(crate) fn configure_socket(stream: &TcpStream, server: &Arc<Server>) {...}`
- `fn` **`serve_plain_tcp`** — `pub(crate) async fn serve_plain_tcp(env: ConnectionEnv, peers: StreamPeers, stream: TcpStream) {...}`
- `fn` **`serve_tls_stream`** — `pub(crate) async fn serve_tls_stream( env: ConnectionEnv, peers: StreamPeers, transport: TlsTransport, ) {...}`
- `fn` **`quic_accept`** — `pub(crate) async fn quic_accept( env: ConnectionEnv, endpoint: Endpoint, mut shutdown_receiver: Receiver<()>, running_sender: Sender<bool>, ) -> Result<(), Box<ServerError>> {...}`
- `fn` **`serve_h1_connection`** — `pub(crate) async fn serve_h1_connection( server: Arc<Server>, request_config: RequestConfig, stream: TcpStream, ) {...}`
- `fn` **`serve_h1_transport`** — `pub(crate) async fn serve_h1_transport( server: Arc<Server>, request_config: RequestConfig, transport: TlsTransport, ) {...}`
- `fn` **`serve_h1_stream`** — `pub(crate) async fn serve_h1_stream(server: Arc<Server>, stream: &mut Stream) {...}`
- `fn` **`catch_connection_panic`** — `pub(crate) async fn catch_connection_panic<F>(connection: F) -> Option<PanicData> where F: Future<Output = ()>, {...}`
- `fn` **`panic_data_from_payload`** — `pub(crate) fn panic_data_from_payload(payload: Box<dyn Any + Send>) -> PanicData {...}`

### `listener::struct`

- `struct` **`AcceptSignal`** — `pub(crate) struct AcceptSignal {`

### `protocol::aliases::type`

- `type` **`DuplexStream`** — `pub(crate) type DuplexStream = tokio::io::DuplexStream;`
- `type` **`ProtocolHeaders`** — `pub(crate) type ProtocolHeaders = http::HeaderMap;`
- `type` **`RequestH3Stream`** — `pub(crate) type RequestH3Stream = h3::server::RequestStream<h3_quinn::BidiStream<Bytes>, Bytes>;`
- `type` **`RequestResolverH3`** — `pub(crate) type RequestResolverH3 = h3::server::RequestResolver<h3_quinn::Connection, Bytes>;`
- `type` **`ConnectionH2`** — `pub(crate) type ConnectionH2<T> = h2::server::Connection<T, Bytes>;`
- `type` **`H2Error`** — `pub(crate) type H2Error = h2::Error;`
- `type` **`H2RecvStream`** — `pub(crate) type H2RecvStream = h2::RecvStream;`
- `type` **`H2SendStream`** — `pub(crate) type H2SendStream = h2::SendStream<Bytes>;`
- `type` **`ProtocolRequest`** — `pub(crate) type ProtocolRequest<T> = http::Request<T>;`
- `type` **`ProtocolResponse`** — `pub(crate) type ProtocolResponse<T> = http::Response<T>;`
- `type` **`ProtocolBuildError`** — `pub(crate) type ProtocolBuildError = http::Error;`
- `type` **`ProtocolMethod`** — `pub(crate) type ProtocolMethod = http::Method;`
- `type` **`SplitLines`** — `pub(crate) type SplitLines<'a> = Split<'a, &'static str>;`

### `protocol::framing::trait`

- `trait` **`ResponseFramer`** — `pub(crate) trait ResponseFramer {`

### `protocol::http2::fn`

- `fn` **`serve_h2_connection`** — `pub(crate) async fn serve_h2_connection<T>( env: ConnectionEnv, peers: StreamPeers, connection: Result<ConnectionH2<T>, String>, ) where T: AsyncRead + AsyncWrite + Unpin + Send + Sync + 'static, {...}`
- `fn` **`h2_request_task`** — `pub(crate) async fn h2_request_task( env: H2RequestEnv, request: ProtocolRequest<H2RecvStream>, send_response: h2::server::SendResponse<Bytes>, ) {...}`
- `fn` **`h2_fail_request`** — `pub(crate) async fn h2_fail_request( env: &H2RequestEnv, framer: &mut H2Framer, version: HttpVersion, error: RequestError, ) {...}`
- `fn` **`collect_h2_body`** — `pub(crate) async fn collect_h2_body( recv_stream: &mut H2RecvStream, request_config: &RequestConfig, headers: &ProtocolHeaders, body: &mut Vec<u8>, ) -> Result<(), RequestError> {...}`

### `protocol::http2::impl`

- `fn` **`new`** — `pub(crate) fn new(send_response: h2::server::SendResponse<Bytes>) -> Self {...}`
- `fn` **`reset`** — `pub(crate) fn reset(&mut self) {...}`

### `protocol::http2::struct`

- `struct` **`H2Framer`** — `pub(crate) struct H2Framer {`
- `struct` **`H2RequestEnv`** — `pub(crate) struct H2RequestEnv {`

### `protocol::http3::fn`

- `fn` **`serve_h3_connection`** — `pub(crate) async fn serve_h3_connection( env: ConnectionEnv, peers: StreamPeers, mut connection: h3::server::Connection<h3_quinn::Connection, Bytes>, ) {...}`
- `fn` **`h3_request_task`** — `pub(crate) async fn h3_request_task(env: H3RequestEnv, resolver: RequestResolverH3) {...}`
- `fn` **`collect_h3_body`** — `pub(crate) async fn collect_h3_body( framer: &mut H3Framer, request_config: &RequestConfig, headers: &ProtocolHeaders, body: &mut Vec<u8>, ) -> Result<(), RequestError> {...}`
- `fn` **`h3_fail_request`** — `pub(crate) async fn h3_fail_request( env: &H3RequestEnv, framer: &mut H3Framer, version: HttpVersion, error: RequestError, ) {...}`

### `protocol::http3::impl`

- `fn` **`new`** — `pub(crate) fn new(request_stream: RequestH3Stream) -> Self {...}`
- `fn` **`reset`** — `pub(crate) fn reset(&mut self) {...}`

### `protocol::http3::struct`

- `struct` **`H3Framer`** — `pub(crate) struct H3Framer {`
- `struct` **`H3RequestEnv`** — `pub(crate) struct H3RequestEnv {`

### `protocol::lifecycle::impl`

- `fn` **`new`** — `pub(crate) fn new(server: Arc<Server>, request: Request, target: String) -> Self {...}`
- `fn` **`run`** — `pub(crate) async fn run(self, mut stream: Stream) {...}`

### `protocol::lifecycle::struct`

- `struct` **`ServerLifecycle`** — `pub(crate) struct ServerLifecycle {`

### `protocol::pump::fn`

- `fn` **`pump_response`** — `pub(crate) async fn pump_response<F>( framer: &mut F, reader: DuplexStream, max_head_size: usize, is_head: bool, ) -> Result<(), ResponseError> where F: ResponseFramer, {...}`
- `fn` **`hides_entity_length`** — `pub(crate) fn hides_entity_length(status_code: usize, _is_head: bool) -> bool {...}`
- `fn` **`check_body_budget`** — `pub(crate) fn check_body_budget( announced_len: Option<usize>, forwarded: usize, incoming: usize, ) -> bool {...}`
- `fn` **`validate_status_code`** — `pub(crate) fn validate_status_code(status_code: usize) -> Result<(), ResponseError> {...}`

### `protocol::pump::static`

- `static` **`BODY_BUFFER_POOL`** — `pub(crate) static BODY_BUFFER_POOL: RefCell<Vec<Vec<u8>>> = const { RefCell::new(Vec::new()) };`

### `protocol::pump::struct`

- `struct` **`FramedHead`** — `pub(crate) struct FramedHead {`

### `protocol::request::fn`

- `fn` **`build_protocol_request`** — `pub fn build_protocol_request( config: &RequestConfig, head: ProtocolRequestHead, ) -> Result<Request, RequestError> {...}`
- `fn` **`resolve_request_host`** — `pub fn resolve_request_host(headers: &ProtocolHeaders, uri: &http::Uri) -> String {...}`
- `fn` **`check_request_authority`** — `pub fn check_request_authority( headers: &ProtocolHeaders, uri: &http::Uri, ) -> Result<(), RequestError> {...}`
- `fn` **`same_authority`** — `pub fn same_authority(authority: &str, host: &str, scheme: Option<&str>) -> bool {...}`
- `fn` **`normalize_authority`** — `pub fn normalize_authority(authority: &str, scheme: Option<&str>) -> (String, Option<String>) {...}`
- `fn` **`split_authority_port`** — `pub fn split_authority_port(authority: &str) -> (&str, Option<&str>) {...}`
- `fn` **`split_target_query`** — `pub fn split_target_query( target: &str, query_index: Option<usize>, hash_index: Option<usize>, ) -> &str {...}`
- `fn` **`split_target_path`** — `pub fn split_target_path( target: &str, query_index: Option<usize>, hash_index: Option<usize>, ) -> &str {...}`
- `fn` **`fill_request_querys`** — `pub fn fill_request_querys(query: &str, querys: &mut RequestQuerys) {...}`
- `fn` **`protocol_method`** — `pub fn protocol_method(method: ProtocolMethod) -> RequestMethod {...}`
- `fn` **`fill_request_headers`** — `pub fn fill_request_headers( headers: &ProtocolHeaders, config: &RequestConfig, request: &mut Request, ) -> Result<(), RequestError> {...}`
- `fn` **`is_hop_by_hop`** — `pub fn is_hop_by_hop(name: &str) -> bool {...}`
- `fn` **`declared_content_length`** — `pub fn declared_content_length( headers: &ProtocolHeaders, max_body_size: usize, ) -> Result<Option<usize>, RequestError> {...}`
- `fn` **`parse_ascii_length`** — `pub(crate) fn parse_ascii_length(value: &str) -> Result<usize, RequestError> {...}`
- `fn` **`is_bodyless_status`** — `pub fn is_bodyless_status(status_code: usize, is_head: bool) -> bool {...}`
- `fn` **`push_bounded_body`** — `pub fn push_bounded_body( limit: usize, body: &mut Vec<u8>, chunk: Bytes, ) -> Result<(), RequestError> {...}`
- `fn` **`request_target`** — `pub fn request_target(path: &str, query: Option<&str>) -> String {...}`

### `protocol::request::struct`

- `struct` **`ProtocolRequestHead`** — `pub(crate) struct ProtocolRequestHead {`

### `protocol::response::fn`

- `fn` **`find_head_end`** — `pub fn find_head_end(buffer: &[u8]) -> Option<usize> {...}`
- `fn` **`find_line_end`** — `pub fn find_line_end(bytes: &[u8]) -> Option<usize> {...}`
- `fn` **`parse_response_head`** — `pub fn parse_response_head(head: &[u8]) -> Result<(usize, ProtocolHeaders), ResponseError> {...}`
- `fn` **`has_transfer_encoding`** — `pub fn has_transfer_encoding(headers: &ProtocolHeaders) -> bool {...}`
- `fn` **`parse_content_length`** — `pub fn parse_content_length(headers: &ProtocolHeaders) -> Result<Option<usize>, ResponseError> {...}`
- `fn` **`connection_nominates`** — `pub fn connection_nominates(headers: &ProtocolHeaders, name: &str) -> bool {...}`
- `fn` **`next_h2_capacity`** — `pub(crate) async fn next_h2_capacity( send_stream: &mut h2::SendStream<Bytes>, wanted: usize, ) -> Result<usize, ResponseError> {...}`

### `protocol::transport::fn`

- `fn` **`build_duplex_transport`** — `pub(crate) fn build_duplex_transport( request_config: RequestConfig, peers: StreamPeers, ) -> (Stream, DuplexStream) {...}`

### `protocol::transport::impl`

- `fn` **`new`** — `pub(crate) fn new(session: tokio_rustls::server::TlsStream<TcpStream>) -> Self {...}`
- `fn` **`get_session_ref`** — `pub(crate) fn get_session_ref(&self) -> &tokio_rustls::server::TlsStream<TcpStream> {...}`

### `protocol::transport::struct`

- `struct` **`DuplexTransport`** — `pub(crate) struct DuplexTransport {`
- `struct` **`TlsTransport`** — `pub(crate) struct TlsTransport {`
- `struct` **`ConnectionEnv`** — `pub(crate) struct ConnectionEnv {`
- `struct` **`StreamPeers`** — `pub(crate) struct StreamPeers {`

### `tls::fn`

- `fn` **`build_server_tls_config`** — `pub fn build_server_tls_config( tls: &TlsConfig, alpn: &[u8], versions: &[&'static SupportedProtocolVersion], ) -> Result<Arc<TlsServerConfig>, Box<ServerError>> {...}`
- `fn` **`build_stream_tls_config`** — `pub fn build_stream_tls_config( tls: &TlsConfig, protocol: &ServerProtocol, ) -> Result<Arc<TlsServerConfig>, Box<ServerError>> {...}`
- `fn` **`build_quic_tls_config`** — `pub fn build_quic_tls_config(tls: &TlsConfig) -> Result<Arc<TlsServerConfig>, Box<ServerError>> {...}`

### `tls::type`

- `type` **`SupportedProtocolVersion`** — `pub(crate) type SupportedProtocolVersion = rustls::SupportedProtocolVersion;`
- `type` **`TlsServerConfig`** — `pub(crate) type TlsServerConfig = rustls::ServerConfig;`
- `type` **`TlsError`** — `pub(crate) type TlsError = rustls::Error;`
