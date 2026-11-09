---
name: hyperlane
description: "Use when implementing or debugging the Hyperlane Rust HTTP framework: server routes, lifecycle hooks, Context, request targets, the plugin crates, or the perf harness. Publishing to ltpp.vip uses hyperlane-upload instead."
license: MIT
metadata:
  hermes:
    related_skills: [rust-standards]
---

# Hyperlane framework entry

## Index

Shortest path · Current source contracts to verify · Published versus local · Request parsing refuses what it cannot frame · The original request target · The protocol layer is internal · Load by task

## Shortest path

1. Resolve the actual dependency version and workspace with `cargo metadata
   --no-deps --format-version 1`. Local uncommitted APIs are not necessarily
   available in the published `hyperlane` / `http-type` package, and only the
   root `Cargo.toml` version is bumped for a publishable change.
2. Load `rust-standards` and the one relevant reference below. Inspect the
   actual route/hook implementation in the selected version before copying a
   tutorial.
3. Keep route paths and configuration values in the project's named constants.
   Implement against public contracts; do not widen visibility merely for tests.
4. Format, compile, lint and test through the project's real gates. Exercise the
   exact request and response bytes for wire changes; a registered route or an
   HTTP connection alone is not proof a nonempty response was sent.

## Current source contracts to verify

These are checked at `core/src/server/impl.rs`, `core/src/hook/trait.rs` and
`type/src/response/impl.rs`; recheck for another version.

- `Server::route::<Handler>(path)` is **synchronous**, returning `&mut Self`.
  Request/response middleware registration is also synchronous. Do not append `.await`.
- `Server::run().await` returns `Result<ServerControlHook, Box<ServerError>>`;
  propagate or report binding failure. `unwrap_or_default()` must not hide it.
- `ServerHook::new(stream, ctx)` returns a future of `Self`;
  `handle(self, stream, ctx)` returns a future of `Status`. `stream` comes first.
- Returning `Status::Continue` continues the lifecycle; `Status::Reject` stops it.
  Check which response middleware actually runs before deciding who sends bytes.
- Setting a response body alone does not transmit it. In a direct-send handler,
  build the response (`build()` is synchronous), await `stream.try_send(data)`
  (asynchronous), handle its error, then stop the pipeline with `Status::Reject`
  to avoid duplicate downstream sending.
- Treat generated accessors as real APIs, but verify them through generated
  docs/compiler output rather than guessing from a field name.

The registration/start sequence inside an existing async startup function is
`server.route::<Index>(ROOT_PATH);` then `server.run().await?` then
`control.wait().await;`. It assumes the application's existing `Index`,
`ROOT_PATH` and `Server` configuration; it is not a standalone server template.

### Hook order and priority

`HookType` carries an `Option<isize>` order. The framework sorts hooks by that
key with `sort_by_key`, and `Option` orders `None` **before** every `Some`. The
consequences are mechanical, not stylistic:

- A hook with no order runs **before** every hook that has an order.
- Among hooks that have an order, the **smaller** number runs earlier.
- `HookType::assert_unique_order` panics when one hook type is registered twice
  with the same order. Two *different* hook types may share a number without
  tripping it.

The attribute macro only accepts an integer literal or a **string** literal.
A negative integer literal such as `#[response_middleware(-110)]` is parsed as
a unary expression, not as a literal, so it silently degrades to no order at
all. Write `#[response_middleware("-110")]` when a negative priority is meant.

### Published versus local

`http-constant`, `http-compress`, `http-type`, `http-request`,
`hyperlane-core`, `hyperlane-macros`, `hyperlane-cli`, `hyperlane`,
`hyperlane-plugin-logger`, `hyperlane-plugin-websocket` and
`hyperlane-performance` are published to crates.io; the framework crates are at
`22.2.0`, and the workspace tree and the registry agree on that number. The
other four plugin crates (`hyperlane-plugin-compression`, `-cors`, `-shutdown`,
`-static-files`) were removed from the tree on 2026-10-24, and their last
versions stay on crates.io at `22.0.6`. Three version numbers must still be
kept apart — the committed HEAD, the local working tree and the published
registry — and only the last one is what a consumer can install. Verify the
live registry before asserting a version.

`hyperlane-performance` is the harness crate and it is a **workspace member**,
not a separate workspace: `cargo metadata --no-deps --format-version 1` lists
it among the eleven packages. See [Benchmark](references/bench.md).
`hyperlane-macros` has a second, older release line on crates.io: `23.0.21`
depends on `hyperlane ^21.3.6` and `syn ^2.0.119`, which does not match the
current workspace's `syn ^3.0.6`, and it is the highest number on the registry.
A plain `cargo add hyperlane-macros` therefore resolves to that stale line. Pin
the version the workspace uses instead of taking the highest.
## Request parsing refuses what it cannot frame

The server parser does not accept a request it cannot frame unambiguously.
A request is refused with a `RequestError` when it carries `Transfer-Encoding`,
a repeated `Content-Length`, a comma separated length list, a non decimal or
overflowing length, a folded header, whitespace before the field colon, a
control byte in a field value, a malformed field name, a repeated `Host`, or a
request line that does not hold exactly three fields. HTTP/1.0 without `Host`
is still accepted, so legacy clients keep working. The client refuses to build
a request whose name, value or target carries a control byte, whose scheme is
not http or https, or whose host is empty; for HTTP/2 and HTTP/3 a request
whose authority disagrees with the `Host` header is refused. The repository's
`SECURITY.md` lists every covered bug class with the test that proves it.

## The original request target

`Context::get_request_target() -> Option<String>` returns the wire target
(path plus query) exactly as the client spelled it, captured before routing and
before the query map is built. The protocol layer stores it before any user
middleware runs, so a middleware sees the original target even after a handler
rewrote the request path; it is refreshed per request, so a keep-alive
connection never carries the previous target. It is `None` for a manually
constructed `Context`. An empty query keeps its `?` marker — `/target?` stays
`/target?` — and `/target?q=a%20b` keeps its percent escapes.

The helper that joins the two (`request_target(path, query)`) is crate-internal
— `hyperlane::request_target` does not compile from outside the crate. HTTP/1.1
falls back to the request line's second field, the other protocols to the
parsed URI. The attribute key is `hyperlane.request.target`, so a client cannot
spoof it with a header.

## The protocol layer is internal

`hyperlane-core` splits into a public half and an internal half. The public
half is what it re-exports — `config`, `context`, `error`, `hook`, `route` and
`server`. The internal half is `listener`, `protocol` and `tls`, which are
`pub(crate)`. A fix to request framing, the HTTP/2 or HTTP/3 framer, the
connection pump or the transport belongs in `protocol/`, not in `server` and
never in a route handler. `references/api-core.md` opens with the map and
indexes the internal half too, which does **not** mean those items are
callable from outside the crate.

## Load by task

| Task | Reference |
|---|---|
| Server, Context, hooks, configuration | [Core](references/api-core.md) |
| Route/hyperlane/request/response/filter macros | [Macros](references/api-macros.md) |
| Request, Response, Stream, cookies and protocol types | [HTTP types](references/api-type.md) |
| Client requests, proxying and response decoding | [Client](references/api-request.md) |
| Compression | [Compression](references/api-compress.md) |
| HTTP constants | [Constants](references/api-constant.md) |
| Plugin crates, priorities and configuration | [Plugins](references/plugins.md) |
| Performance harness and throughput verdicts | [Benchmark](references/bench.md) |
| WebSocket | [Plugin](references/hyperlane-plugin-websocket.md) |
| SSE and multi-stage sending | [SSE](references/sse.md) |
| Release delivery | [Release flow](references/release-bump-flow.md) |

Cached reference pages can lag current source. Reject a claimed path or
signature when the actual selected package disagrees; do not force code to
match the cache. For service validation, reclaim task-owned listeners,
processes, browser tabs and containers on success and failure; verify exact
IDs/ports against the baseline. Normal euv UI work, generic Cargo/Git tasks and
ltpp.vip publication are not this entry point. Use
[hyperlane-upload](../hyperlane-upload/SKILL.md) only for that explicitly
selected public hosting destination.
