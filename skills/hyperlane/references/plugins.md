# hyperlane plugin crates

Source: `plugin/*/src/` in the hyperlane workspace. Two plugin crates are in the
tree. Four others were in it until 2026-10-24 and are not any more.

| crate | directory | published |
|---|---|---|
| `hyperlane-plugin-logger` | `plugin/logger` | yes, crates.io `22.2.0` |
| `hyperlane-plugin-websocket` | `plugin/websocket` | yes, crates.io `22.2.0` |

Both are workspace members and both depend on the `hyperlane` facade crate, so
they compile against the workspace source, not against a released version.
`cargo metadata --no-deps --format-version 1` is the authority for the member
list.

The four plugin crates that used to sit here — `hyperlane-plugin-compression`,
`hyperlane-plugin-cors`, `hyperlane-plugin-shutdown` and
`hyperlane-plugin-static-files` — were removed from the tree on 2026-10-24. The
rules they held were not lost: they moved to the crates-dev family (the
`ctares` workspace) as the four standalone rule crates listed further down, and
those crates are published. So a task that needs one of them depends on the
matching rule crate rather than writing the hook from scratch.

The last published versions of the removed plugin crates stay on crates.io at
`22.0.6`, and the crates.io releases of the rules that were published there
stay as they are: a yanked dependency would break the resolution of the
packages that depend on it.

The two plugin crates that remain are published with the rest of the workspace:
both carry `publish = true` and are on crates.io at `22.2.0`.

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
it. The pattern is identical in the two crates:

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
| logger | `RequestLogger` | `#[hyperlane::request_middleware(-120)]` | none (see below) |
| logger | `ResponseLogger` | `#[hyperlane::response_middleware(100)]` | `100` |
| websocket | none | it is a trait and config surface, not a hook | — |

The negative attribute is written as a negative **integer literal**. The
macro's parser only recognises an integer literal or a string literal; a
negative integer is a unary expression and falls through to "no order". The
consequence is mechanical and was confirmed by running the compiled hooks:

- `RequestLogger` registers with **no order**, which under `sort_by_key` puts
  it **before** every hook that has an order, not after the application's
  positive middlewares as the plugin README describes.
- `ResponseLogger` at `100` does carry its order and runs after positive
  application middlewares.
- `assert_unique_order` does not fire for these, because it only checks hooks
  that *have* an order.

If the intended behaviour matters, write the order as a string
(`#[hyperlane::response_middleware("-110")]`), which the parser does accept and
which produces `Some(-110)`. Confirm the result by reading the compiled
`HookType` rather than by trusting the attribute text.

## What each plugin does

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

### `hyperlane-plugin-websocket`

The published plugin that carries the most state. It provides `WebSocket`,
`WebSocketConfig`, `BroadcastType` and the `BroadcastTypeTrait` bound, and
integrates with `hyperlane-broadcast` for message dissemination. It is a
trait-and-config surface rather than a middleware: the application supplies the
connected, request, sended and closed hooks through the config setters.

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
