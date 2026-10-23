# hyperlane plugin crates

Source: `plugin/*/src/` in the hyperlane workspace. Six plugin crates exist;
only one is published.

| crate | directory | published |
|---|---|---|
| `hyperlane-plugin-compression` | `plugin/compression` | no (`publish = false`) |
| `hyperlane-plugin-cors` | `plugin/cors` | no (`publish = false`) |
| `hyperlane-plugin-logger` | `plugin/logger` | no (`publish = false`) |
| `hyperlane-plugin-shutdown` | `plugin/shutdown` | no (`publish = false`) |
| `hyperlane-plugin-static-files` | `plugin/static-files` | no (`publish = false`) |
| `hyperlane-plugin-websocket` | `plugin/websocket` | yes, crates.io `21.14.0` |

All six are workspace members and all six depend on the `hyperlane` facade
crate, so they compile against the workspace source, not against a released
version. `cargo metadata --no-deps --format-version 1` is the authority for the
member list.

## How a plugin attaches to the server

A plugin is a crate whose hook structs are registered through the attribute
macros. `#[hyperlane::request_middleware(N)]` and
`#[hyperlane::response_middleware(N)]` expand into an `inventory::submit!` of a
`HookType`, and `#[hyperlane(server: Server)]` collects every submitted hook,
asserts the orders are unique, sorts them and installs them. A plugin therefore
needs no registration call of its own: it becomes active by being a dependency
of the application.

The hook itself implements `ServerHook` with the usual two methods,
`async fn new(&mut Stream, &mut Context) -> Self` and
`async fn handle(self, &mut Stream, &mut Context) -> Status`.

## The configuration pattern

Every plugin keeps its settings in a process-wide `OnceLock` behind a static,
exposed through an `init` that takes the configuration and a `get` that returns
it. The pattern is identical in all six crates:

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

## Order and priorities

The order lives in the attribute on the hook struct. Read the numbers from the
source, not from the README, and note the negative-literal trap:

| plugin | hook | attribute in source | effective order |
|---|---|---|---|
| compression | `CompressionMiddleware` | `#[hyperlane::response_middleware(-110)]` | none (see below) |
| cors | `CorsMiddleware` | `#[hyperlane::request_middleware(-110)]` | none (see below) |
| logger | `RequestLogger` | `#[hyperlane::request_middleware(-120)]` | none (see below) |
| logger | `ResponseLogger` | `#[hyperlane::response_middleware(100)]` | `100` |
| shutdown | none | no hook is registered | — |
| static-files | `StaticFilesRoute` | no attribute; the application registers it | — |

The three negative attributes are written as negative **integer literals**. The
macro's parser only recognises an integer literal or a string literal; a
negative integer is a unary expression and falls through to "no order". The
consequence is mechanical and was confirmed by running the compiled hooks:

- `CompressionMiddleware`, `CorsMiddleware` and `RequestLogger` register with
  **no order**, which under `sort_by_key` puts them **before** every hook that
  has an order, not after the application's positive middlewares as the plugin
  READMEs describe.
- `ResponseLogger` at `100` does carry its order and runs after positive
  application middlewares.
- `assert_unique_order` does not fire for these, because it only checks hooks
  that *have* an order.

If the intended behaviour matters, write the order as a string
(`#[hyperlane::response_middleware("-110")]`), which the parser does accept and
which produces `Some(-110)`. Confirm the result by reading the compiled
`HookType` rather than by trusting the attribute text.

## What each plugin does

### `hyperlane-plugin-compression`

Reads `accept-encoding`, picks the first offered encoding the client accepts in
the configuration's preferred order, and writes `content-encoding` plus
`vary: accept-encoding` on the answer. The framework compresses the body when
the answer is built, so the middleware only writes the header.

Configuration: `CompressionConfig { min_size: usize, encodings: Vec<Compress> }`.
Defaults are `min_size` 1024 and the encodings `[Compress::Gzip, Compress::Br]`.
The public helpers are `CompressionConfig::pick(&str) -> Option<Compress>` and
`CompressionConfig::is_compressible(&str) -> bool`.

A body is left alone when it is smaller than `min_size`, when the answer
already carries an encoding, when the client asked for no encoding, or when the
content type is already compressed (`application/zip`, `application/gzip`,
`application/x-gzip`, `application/x-bzip2`, `application/x-xz`,
`application/zstd`, and the `image/`, `video/`, `audio/`, `font/` prefixes).
`text/event-stream` is never compressed.

The crate re-exports `hyperlane::Compress` so the application needs no direct
`http-compress` dependency.

### `hyperlane-plugin-cors`

Reads `origin` and, when the origin is allowed, writes
`access-control-allow-origin`, `access-control-allow-methods`,
`access-control-allow-headers`, optionally `access-control-max-age` and
`access-control-allow-credentials`, and `vary: origin`. A request without an
origin, and a request from an origin that is not allowed, are left alone.

Configuration: `CorsConfig { allowed_origins, allowed_methods, allowed_headers,
max_age, allow_credentials }`. The default allows the `*` origin and the `*`
request header, and names the nine methods explicitly
(`GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS, CONNECT, TRACE`), with no max
age and no credentials. `CorsConfig::allowed_origin` returns the wildcard for a
wildcard configuration and the origin itself for a list, and `None` when the
origin is not allowed.

### `hyperlane-plugin-logger`

Installs a `log` logger that writes to the console and, when a file is
configured, appends to that file. The request log is a middleware pair:
`RequestLogger` notes when a request arrived and `ResponseLogger` writes the
line with the method, the path, the status and the elapsed time.

Configuration: `LoggerConfig { level: LevelFilter, file: Option<String> }`.
The default level is `Info` and there is no file. The crate re-exports
`LevelFilter`. The helpers are `LoggerPlugin::log_info`, `log_error`,
`log_warn`, `log_debug` and `log_trace`.

`init` calls `log::set_logger`, so it fails with "a logger was already
installed" if the process already has one.

### `hyperlane-plugin-shutdown`

Turns the operating system's termination signals into a graceful shutdown.
`ShutdownPlugin::init(ShutdownConfig { watch_terminate, message })` stores the
configuration; `ShutdownPlugin::watch(&ServerControlHook)` spawns the watcher;
`ShutdownPlugin::on_shutdown(&ServerControlHookHandler<()>)` installs the
handler that runs when the server stops.

The plugin registers **no hook**, so it changes nothing until the application
asks for it. `watch_terminate` defaults to `true` and selects the terminate
signal on unix in addition to the interrupt signal.

### `hyperlane-plugin-static-files`

Serves the files of a directory. The application registers the route itself,
because the path belongs to the application:

```rust
StaticFilesPlugin::init(StaticFilesConfig { root: PathBuf::from("./public"), index: "index.html".to_owned() })?;
server.route::<StaticFilesRoute>(&StaticFilesPlugin::pattern("/assets"));
```

`StaticFilesPlugin::pattern(prefix)` builds the route pattern so the parameter
name stays the same across applications. `StaticFilesConfig::resolve(&str)`
refuses a path that climbs out of the root, and `content_type(&Path)` uses the
framework's own extension table, falling back to `application/octet-stream` for
an unknown extension. The route answers a missing file with the not-found
status and a directory with the index file.

The plugin registers a route and no middleware, so it has no order.

### `hyperlane-plugin-websocket`

The only published plugin. It provides `WebSocket`, `WebSocketConfig`,
`BroadcastType` and the `BroadcastTypeTrait` bound, and integrates with
`hyperlane-broadcast` for message dissemination. It is a trait-and-config
surface rather than a middleware: the application supplies the connected,
request, sended and closed hooks through the config setters.
