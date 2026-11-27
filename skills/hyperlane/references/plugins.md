# hyperlane plugin crates

Source: `plugin/*/src/` in the hyperlane workspace. **Twenty** plugin crates are
in the tree at `origin/master` (`04dee24`, workspace version `22.13.0`); all
twenty carry `publish = true`, are `[workspace] members`, and are named in
`.github/workflows/rust.yml`'s `PACKAGES` array. `cargo metadata --no-deps
--format-version 1` is the authority for the member list; the root `hyperlane`
package counts too, so the workspace holds **29 packages sharing one version**.

| crate | directory | req order | resp order |
|---|---|---|---|
| `hyperlane-plugin-auth` | `plugin/auth` | `-90` | — |
| `hyperlane-plugin-cache` | `plugin/cache` | `-80` | `-65` |
| `hyperlane-plugin-cors` | `plugin/cors` | `-100` | `-80` |
| `hyperlane-plugin-gateway` | `plugin/gateway` | `-50` | — |
| `hyperlane-plugin-grpc` | `plugin/grpc` | `-65` | — |
| `hyperlane-plugin-health` | `plugin/health` | `-110` | — |
| `hyperlane-plugin-logger` | `plugin/logger` | `-120` | `100` |
| `hyperlane-plugin-mcp` | `plugin/mcp` | `-60` | — |
| `hyperlane-plugin-metrics` | `plugin/metrics` | `-115` | `95` |
| `hyperlane-plugin-mq` | `plugin/mq` | broker | — |
| `hyperlane-plugin-negotiate` | `plugin/negotiate` | explicit | explicit |
| `hyperlane-plugin-rate-limit` | `plugin/rate_limit` | `-95` | — |
| `hyperlane-plugin-rpc` | `plugin/rpc` | `-70` | — |
| `hyperlane-plugin-security` | `plugin/security` | `-105` | `-75` |
| `hyperlane-plugin-session` | `plugin/session` | `-85` | `-70` |
| `hyperlane-plugin-shutdown` | `plugin/shutdown` | control hook | — |
| `hyperlane-plugin-sse` | `plugin/sse` | route helper | — |
| `hyperlane-plugin-static-files` | `plugin/static_files` | `-55` | — |
| `hyperlane-plugin-tracing` | `plugin/tracing` | `-130` | `90` |
| `hyperlane-plugin-websocket` | `plugin/websocket` | route helper | — |

The orders above are read from the `#[hyperlane::request_middleware(N)]` /
`#[hyperlane::response_middleware(N)]` attribute on the hook struct in each
crate's `src/struct.rs` — read them from the source, not from a README. `—`
means the crate registers no hook of that kind.

All twenty depend on the `hyperlane` facade crate, so they compile against the
workspace source, not against a released version.

## How a plugin attaches to the server

**Fifteen of the twenty** — auth, cache, cors, gateway, grpc, health, logger,
mcp, metrics, rate-limit, rpc, security, session, static-files and tracing —
attach through the attribute macros. `#[hyperlane::request_middleware(N)]` and
`#[hyperlane::response_middleware(N)]` expand into an `inventory::submit!` of a
`HookType`, and `#[hyperlane(server: Server)]` collects every submitted hook,
asserts the orders are unique, sorts them and installs them. Such a plugin
needs no registration call of its own: it becomes active by being a dependency
of the application.

The other five attach some other way:

| crate | how it attaches |
|---|---|
| `hyperlane-plugin-negotiate` | the application registers each middleware explicitly with `.response_middleware::<T>()` |
| `hyperlane-plugin-shutdown` | joins the framework's `ServerControlHook` for graceful drain |
| `hyperlane-plugin-websocket` | a trait-and-config surface the application wires into a route |
| `hyperlane-plugin-sse` | a route helper: WHATWG framing plus a topic pub/sub bus |
| `hyperlane-plugin-mq` | no hook at all — a pluggable `MessageBroker` trait and an in-memory broker |

**`hyperlane-plugin-negotiate` is the one that breaks the "a plugin needs no
registration call" rule.** It ships no attribute macro and no
`inventory::submit!`, so being a dependency changes nothing:

```rust
server
    .response_middleware::<CompressMiddleware>()
    .response_middleware::<ConditionalMiddleware>();
```

It is therefore also the only plugin whose hooks are ordered by the order the
application registers them in, not by an attribute order. See
[Negotiate](plugin-negotiate.md).

The hook itself implements `ServerHook` with the usual two methods,
`async fn new(&mut Stream, &mut Context) -> Self` and
`async fn handle(self, &mut Stream, &mut Context) -> Status`.

## The configuration pattern

Every plugin keeps its settings in a process-wide `OnceLock` behind a static,
exposed through an `init` that takes the configuration and a `get` that returns
it. The pattern is identical across the twenty crates:

```rust
PluginName::init(Config { .. })?;      // Result<(), String>, refuses a second set
let config: Option<&'static Config> = PluginName::get();
```

`init` returns `Err` with a human-readable string when the configuration was
already set, so call it once during startup and propagate the error.

**A plugin that is a dependency but that the application did not configure must
not change the server's behaviour.** Every hook checks its own `OnceLock` first
and returns `Status::Continue` when the configuration is absent. Verify this
when reading a plugin: a hook that reads the configuration without the `None`
arm would break every application that does not use it.

`hyperlane-plugin-negotiate` deviates deliberately: `CompressMiddleware`
falls back to `CompressConfig::default()` (a `256` byte threshold) when no
configuration was installed, so it still negotiates without one. Only its
`init` is `OnceLock`-guarded, and it refuses a second set.

## Order and priorities

The order lives in the attribute on the hook struct. Read the numbers from the
source, not from the README, and note the two traps:

| plugin | hook | attribute in source | effective order |
|---|---|---|---|
| tracing | `TracingRequestHook` | `#[hyperlane::request_middleware(-130)]` | `-130` |
| logger | `RequestLogger` | `#[hyperlane::request_middleware(-120)]` | `-120` |
| metrics | `MetricsRequestHook` | `#[hyperlane::request_middleware(-115)]` | `-115` |
| health | `HealthHook` | `#[hyperlane::request_middleware(-110)]` | `-110` |
| security | `SecurityRequestHook` | `#[hyperlane::request_middleware(-105)]` | `-105` |
| cors | `CorsRequestHook` | `#[hyperlane::request_middleware(-100)]` | `-100` |
| rate-limit | `RateLimitHook` | `#[hyperlane::request_middleware(-95)]` | `-95` |
| auth | `AuthHook` | `#[hyperlane::request_middleware(-90)]` | `-90` |
| session | `SessionRequestHook` | `#[hyperlane::request_middleware(-85)]` | `-85` |
| cache | `CacheRequestHook` | `#[hyperlane::request_middleware(-80)]` | `-80` |
| rpc | `RpcHook` | `#[hyperlane::request_middleware(-70)]` | `-70` |
| grpc | `GrpcHook` | `#[hyperlane::request_middleware(-65)]` | `-65` |
| mcp | `McpHook` | `#[hyperlane::request_middleware(-60)]` | `-60` |
| static-files | `StaticFilesHook` | `#[hyperlane::request_middleware(-55)]` | `-55` |
| gateway | `GatewayHook` | `#[hyperlane::request_middleware(-50)]` | `-50` |
| logger | `ResponseLogger` | `#[hyperlane::response_middleware(100)]` | `100` |
| metrics | `MetricsResponseHook` | `#[hyperlane::response_middleware(95)]` | `95` |
| tracing | `TracingResponseHook` | `#[hyperlane::response_middleware(90)]` | `90` |
| security | `SecurityResponseHook` | `#[hyperlane::response_middleware(-75)]` | `-75` |
| session | `SessionResponseHook` | `#[hyperlane::response_middleware(-70)]` | `-70` |
| cache | `CacheResponseHook` | `#[hyperlane::response_middleware(-65)]` | `-65` |
| cors | `CorsResponseHook` | `#[hyperlane::response_middleware(-80)]` | `-80` |
| negotiate | `CompressMiddleware` | none — registered by `response_middleware::<T>()` | registration order |
| negotiate | `ConditionalMiddleware` | none — registered by `response_middleware::<T>()` | registration order |
| shutdown | `ShutdownGuard` | none — joins `ServerControlHook` | — |
| websocket | none | it is a trait and config surface, not a hook | — |
| sse | none | it is a route helper, not a hook | — |
| mq | none | it is a broker, not a hook | — |

**Trap 1 — the smaller value runs first.** The framework sorts with
`sort_by_key(try_get_order())` over an `Option<isize>` (in
`macros/src/hyperlane/fn.rs`), so `None` comes before every `Some`, and a
negative priority runs before a positive one. A plugin that answers a request
keeps the negative priorities; an application that gives its own middlewares
positive priorities runs after them.

**Trap 2 — a negative literal used to be swallowed; it is not any more.**
Before `02a26b8`, `expr_to_isize` accepted only an integer literal or a string
literal, so `#[response_middleware(-110)]` — a unary expression — fell through
to `None`, and the hook registered with **no order at all**. `02a26b8` added an
`Expr::Unary` / `UnOp::Neg` arm, so a negative integer literal now yields
`Some(-110)`. **Every negative order in the table above is live at `22.13.0`**;
the old advice "write it as the string `\"-110\"`" is obsolete, though the
string form still parses. `assert_unique_order` still only checks hooks that
*have* an order, so two unordered hooks never collide.

Register the negotiate middlewares with the coding one first: it declares
`Vary: accept-encoding`, which the conditional middleware then preserves
through a `304`.

## What each plugin does

The one-line responsibility of every crate is in the workspace tables of
`README.md` and `AGENTS.md` at the same ref — read them there, because the
plugin set is now large enough that a stale copy is worse than none. The three
that carry the most subtle contracts are documented in full below.

### `hyperlane-plugin-logger`

Installs a `log` logger that writes to the console and, when a file is
configured, appends to that file. The request log is a middleware pair:
`RequestLogger` notes when a request arrived and `ResponseLogger` writes the
line with the method, the path, the status and the elapsed time.

Configuration: `LoggerConfig { level: LevelFilter, file: Option<String>,
console: bool, format: LogFormat, channel_capacity: usize, sink:
Option<SharedLogSink> }` — the crate re-exports `LevelFilter`, and `LogFormat`
selects plain text or structured JSON. The default level is `Info` and there is
no file. The helpers are `LoggerPlugin::log_info`, `log_error`, `log_warn`,
`log_debug` and `log_trace`.

`init` calls `log::set_logger`, so it fails with "a logger was already
installed" if the process already has one.

### `hyperlane-plugin-negotiate`

Two response middlewares, added at `22.8.2`:

- `CompressMiddleware` declares the `Content-Encoding` the client accepts,
  from every `Accept-Encoding` field, through
  `Compress::from_accept_encoding`, and declares
  `Vary: accept-encoding` on the responses it codes. It leaves alone a
  response that already declares a coding, an event stream, a bodyless status
  and a body below the threshold (`256` bytes by default). It never writes to
  the stream — the sender applies the coding when it serializes.
- `ConditionalMiddleware` declares a strong `ETag` — the quoted hex digest of
  the body — on every body-carrying response under a safe method, unless the
  application declared one, and answers `304 Not Modified` when
  `If-None-Match` matches, keeping the representation metadata.

Configuration: `CompressConfig::new(min_length)`, process wide, `256` by
default. The conditional middleware takes no configuration. Full contract and
wire tests: [Negotiate](plugin-negotiate.md).

### `hyperlane-plugin-websocket`

The published plugin that carries the most state. It provides `WebSocket`,
`WebSocketConfig`, `BroadcastType` and the `BroadcastTypeTrait` bound, and
integrates with `hyperlane-broadcast` for message dissemination. It is a
trait-and-config surface rather than a middleware: the application supplies the
connected, request, sended and closed hooks through the config setters, and an
opt-in `WebSocketPlugin` hook.

`WebSocketConfig::new` takes **both** the stream and the context:
`WebSocketConfig::new(&mut stream, &mut ctx)`. The hooks it holds are then
`ServerHookHandler` values, so a hook implements the current
`ServerHook` signature — `async fn new(&mut Stream, &mut Context) -> Self` and
`async fn handle(self, &mut Stream, &mut Context) -> Status`.

The `22.6.0` release replaced the ignored doc examples with runnable ones, so
the examples in `plugin/websocket/src/impl.rs` now show the real signature
rather than an older one. Read them there instead of trusting an older
snippet.

## The plugin crates that left, and came back

The history matters because the old advice is still findable:

- Until 2026-10-24 the tree held **seven** plugin crates. Four of them —
  `hyperlane-plugin-compression`, `-cors`, `-shutdown` and `-static-files` —
  were removed from the tree on that date, and their last published versions
  stay on crates.io at `22.0.6`. The rules they held were not lost: they moved
  to the crates-dev family (the `ctares` workspace) as the four standalone rule
  crates listed further down, and those crates are published.
- `267dac7` ("refactor plugins and add 11 core plugins for v22.10.0") then
  **re-added three of the four** as brand-new crates — `plugin/cors`,
  `plugin/shutdown` and `plugin/static_files` — and added eight more besides.
  **`hyperlane-plugin-compression` never came back**: its job is now
  `plugin/negotiate`'s `CompressMiddleware`, which negotiates the coding
  instead of compressing itself.

So "there are only three plugin crates" and "the cors / shutdown /
static-files plugins are gone" are both **stale as of `22.13.0`**. The four
crates.io artefacts at `22.0.6` are still there and still resolvable — a yanked
dependency would break the packages that depend on it — but they are not what
the tree builds.

## The rules that left the tree

The four crates below held what the removed plugin crates held, and they were
published from the crates-dev family on 2026-10-24, in the same commit that
removed the hyperlane plugin crates, before that family was rolled back. Their
source is in the git history of the ctares repository (added in `4b8319c`,
removed again in `4b9c8a8`), and the crates themselves stay on crates.io at
`10.3.0`.

| crate | crates.io | what it holds |
|---|---|---|
| `encoding-negotiator` | `10.3.0` | the encoding a client asked for, and whether a body is worth compressing |
| `cors-policy` | `10.3.0` | the cross origin headers of an answer |
| `signal-watcher` | `10.3.0` | the signal that asks the process to stop |
| `static-file-resolver` | `10.3.0` | the file a path names under a root, without the traversal |

Their contracts, in one paragraph each:

- `CompressionPolicy { encodings: Vec<String>, min_size: usize }` picks the
  first offered encoding the client accepts, in the order the policy prefers,
  and `CompressionPolicy::is_compressible(&str)` tells whether a body of a
  content type is worth compressing. The defaults are `min_size` 1024 and the
  encodings `gzip` and `br`. The policy itself does **not** act on `min_size`
  — it only carries the value; the size check, the "the answer already carries
  an encoding" check and the "the client asked for no encoding" check lived in
  the removed `hyperlane-plugin-compression` hook, so a caller that uses the
  policy directly has to make them. `is_compressible` is what the policy does
  decide: a body is left alone when the content type is already compressed
  (`application/zip`, `application/gzip`, `application/x-gzip`,
  `application/x-bzip2`, `application/x-xz`, `application/zstd`, and the
  `image/`, `video/`, `audio/`, `font/` prefixes), and `text/event-stream` is
  never compressed. An encoding the client refused with a quality of zero is
  dropped.
- `CorsPolicy { allowed_origins, allowed_methods, allowed_headers, max_age,
  allow_credentials }` decides whether an origin is allowed and builds the
  cross origin headers of the answer: `access-control-allow-origin`,
  `access-control-allow-methods`, `access-control-allow-headers`, optionally
  `access-control-max-age` and `access-control-allow-credentials`, and
  `vary: origin`. The default allows the `*` origin and the `*` request
  header, and names the nine methods explicitly (`GET, POST, PUT, DELETE,
  PATCH, HEAD, OPTIONS, CONNECT, TRACE`), with no max age and no credentials.
- `wait_for_signal(watch_terminate)` waits for the interrupt signal, and on
  unix for the terminate signal as well when `watch_terminate` is set.
  `spawn_watcher(watch_terminate, handler)` runs the same wait in the
  background and calls the handler with the `TerminationSignal` that arrived.
- `StaticFileResolver { root: &Path, index: &str }` resolves the file a path
  names under the root, and refuses a path that climbs out of the root. An
  empty path answers with the index file. The resolver carries **no** content
  type: it depends only on `lombok-macros`, and it returns a `PathBuf`. The
  content type of the answer is the caller's business — the removed
  `hyperlane-plugin-static-files` took it from the framework's extension
  table, `http-type`'s `FileExtension`, but `static-file-resolver` does not
  and cannot: it has no dependency on `http-type`.
