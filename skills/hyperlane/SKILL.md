---
name: hyperlane
description: "Use when implementing or debugging the Hyperlane Rust HTTP framework: server routes, lifecycle hooks, Context, request targets, the plugin crates, or the perf harness. Publishing to ltpp.vip uses hyperlane-upload instead."
license: MIT
metadata:
  hermes:
    related_skills: [rust-standards]
---

# Hyperlane framework entry

## Shortest path

1. Resolve the actual dependency version and workspace with `cargo metadata --no-deps --format-version 1`. Local uncommitted APIs are not necessarily in the published `hyperlane` / `http-type` package, and only the root `Cargo.toml` version is bumped for a publishable change.
2. Load `rust-standards` and the one relevant reference below. Inspect the actual route/hook implementation in the selected version before copying a tutorial. Keep route paths and configuration values in the project's named constants; implement against public contracts and do not widen visibility merely for tests.
3. Format, compile, lint and test through the project's real gates. Exercise the exact request and response bytes for wire changes; a registered route alone is not proof a response was sent.

## Source contracts to verify

Checked at `core/src/server/impl.rs`, `core/src/hook/trait.rs`, `type/src/response/impl.rs`; recheck for another version.

| Contract | What it is |
|---|---|
| `Server::route::<Handler>(path)` | **synchronous**, returning `&mut Self`. Middleware registration is also synchronous — do not append `.await` |
| `Server::run().await` | returns `Result<ServerControlHook, Box<ServerError>>`; propagate or report binding failure — `unwrap_or_default()` must not hide it |
| `ServerHook::new(stream, ctx)` / `handle(self, stream, ctx)` | a future of `Self` / a future of `Status`; `stream` comes first |
| `Status::Continue` / `Status::Reject` | continues the lifecycle / stops it — check which response middleware actually runs before deciding who sends bytes |
| Setting a response body | does **not** transmit it. In a direct-send handler, build the response, await `stream.try_send(data)`, handle its error, then stop the pipeline with `Status::Reject` to avoid duplicate downstream sending |
| `ctx.build_response()` | **use it**, not `ctx.get_mut_response().build()`, for the HEAD-aware serialization. It is synchronous and returns `ResponseData` (`Vec<u8>`); it picks `build_head()` for a wire HEAD request and `build()` otherwise. The `#[hyperlane::send]` and `#[hyperlane::try_send]` macros already call it when the attribute carries no argument |
| Generated accessors | treat them as real APIs, but verify them through compiler output rather than guessing from a field name |

The registration/start sequence inside an existing async startup function is
`server.route::<Index>(ROOT_PATH);` → `server.run().await?` → `control.wait().await;`
— it assumes the application's own `Index` and `ROOT_PATH`, so it is not a standalone template.

### Hook order and priority

`HookType` carries an `Option<isize>` order; the framework sorts hooks by that key
with `sort_by_key`, and `Option` orders `None` **before** every `Some`, so an
unordered hook runs before every ordered hook and the **smaller** number runs
earlier. The attribute macro accepts only an integer or a **string** literal — a
negative integer literal degrades to no order.

### Published versus local

`http-constant`, `http-compress`, `http-type`, `http-request`, `hyperlane-core`,
`hyperlane-macros`, `hyperlane-cli`, `hyperlane`, `hyperlane-plugin-logger`,
`hyperlane-plugin-negotiate`, `hyperlane-plugin-websocket` and
`hyperlane-performance` are published to crates.io; every crate is at `22.8.2`,
and the committed tree and the registry agree (every crate checked against the
crates.io API). The four plugin crates that left the tree stay at `22.0.6`. Three
version numbers must stay apart — committed HEAD, working tree, registry — and only
the last is what a consumer can install.

`hyperlane-performance` is the harness crate and a **workspace member** (twelve
packages in total) — see [Benchmark](references/bench.md). `hyperlane-macros` has
a second, older release line: `23.0.21` depends on `hyperlane ^21.3.6` and
`syn ^2.0.119` while the workspace uses `syn ^3.0.6`, and `23.0.21` is the highest
number on the registry, so a plain `cargo add hyperlane-macros` resolves to that
stale line — pin the workspace version.

## The wire follows RFC 9110 and 9112

`22.6.0` aligns the HTTP/1.x wire behaviour with those RFCs, each change locked by
a wire-level test. `22.7.0` and `22.8.0` add performance work and change no wire
contract; `22.8.1` changes no source file; `22.8.2` adds the opt-in
`plugin/negotiate` crate and `http-compress`'s `Accept-Encoding` negotiation API,
with no wire change: [Wire behaviour](references/wire-behaviour.md).

| Rule | Behaviour |
|---|---|
| **Bodyless statuses** | 1xx, 204, 205 and 304 serialize no body and no framing headers. A 205 declares `Content-Length: 0`; 1xx, 204 and 304 omit `Content-Length` and `Transfer-Encoding` entirely. A 304 keeps its representation metadata (for example `ETag`) |
| **Wire HEAD** | the status line and headers only — the body is neither serialized nor compressed. The decision is bound to the *wire* method: a middleware that rewrites the method to `GET` does not make a HEAD request answer with a body |
| **Chunked request bodies** | `Transfer-Encoding: chunked` on an HTTP/1.1 request is decoded with a bounded decoder; the handler receives the **decoded** bytes plus a `Content-Length` for them. The framing fields (`Transfer-Encoding`, `Trailer`) and the trailer fields themselves are consumed but never exposed to the handler. A coding list that does not end in `chunked`, or a coding after it, is `400`; an unimplemented coding beside `chunked` is `501` |
| **`Expect: 100-continue`** | the server sends a 100 Continue interim response before awaiting the body on HTTP/1.1, HTTP/2 and HTTP/3, but only when the expectation applies — the token is matched case-insensitively and commas inside a quoted extension value are not separators |
| **A malformed request** | now gets an answer: the server replies with a default error response (the status the `RequestError` maps to, an empty body, `Content-Length: 0`, plus `Connection: close` on HTTP/1.x) instead of dropping the connection silently — unless a request-error hook is registered, which keeps control |

`Request::matches_if_none_match`, the **public `http-type`** helper
`ConditionalMiddleware` answers `304` from, and the full refusal list:
[Wire behaviour](references/wire-behaviour.md).

## Responses are negotiated, not assumed

`22.8.2` adds `hyperlane-plugin-negotiate`, the one crate that is **opt-in**: no
`#[hyperlane::response_middleware]` attribute and no `inventory::submit!`, so a
dependency alone changes nothing until it is registered. Both middlewares run after
the route and before the sender; a `#[hyperlane::send]` route writes the bytes itself.

```rust
server
    .response_middleware::<CompressMiddleware>()
    .response_middleware::<ConditionalMiddleware>();
```

`CompressMiddleware` picks the best implemented coding out of every
`Accept-Encoding` field through `Compress::from_accept_encoding`, declares it as
`Content-Encoding` plus `Vary: accept-encoding`, and never writes to the stream —
the sender applies the coding, so the advertised `Content-Length` is the **coded**
length. It leaves alone a response that already declares a coding, an event stream,
a bodyless status (1xx, 204, 205, 304) and a body below `min_length` (`256` by
default); an existing `Vary` is extended, not replaced. `ConditionalMiddleware`
declares a **strong** `ETag` (the quoted hexadecimal digest of the body) unless
the application declared one, and answers `304 Not Modified` when `If-None-Match` of
a safe request matches, keeping the representation metadata and dropping the body.

`CompressMiddleware::init(CompressConfig::new(1_024))?` installs the **process
wide** threshold (the framework registers a middleware by its type and builds a
hook per request); a missing configuration is not a no-op — it falls back to the
default `256`. `Compress::as_str` renders the field token and
`Compress::from_accept_encoding` parses the field without allocating, honours `q`,
refuses `q=0`, applies `*` to unnamed codings and breaks ties toward the smaller
output (`br` > `gzip` > `deflate`). Full contract: [Negotiate](references/plugin-negotiate.md) · [Compression](references/api-compress.md).

## The request path owns less, and the original target is preserved

The request path stopped allocating for work it can do in place — see [Request path ownership](references/request-path-ownership.md).

`Context::get_request_target() -> Option<String>` returns the wire target (path
plus query) exactly as the client spelled it, captured before routing and before the
query map is built. The protocol layer stores it before any user middleware runs, so
a middleware sees the original target even after a handler rewrote the request path;
it is refreshed per request, so a keep-alive connection never carries the previous
target, and it is `None` for a manually constructed `Context`.

## Fields are crate-internal, and the protocol layer is internal

A `pub` field on a `pub` struct is published API, so a public struct's fields are
`pub(crate)` and consumers read them through the generated `get_*` / `set_*`
accessors — the accessor stays `pub`. The narrowing moved **105 fields across 23 files**;
the published API did not change (rustdoc JSON: 0 removed, 0 added).

`hyperlane-core` splits into a public half — `config`, `context`, `error`,
`hook`, `route`, `server` — and an internal half — `listener`, `protocol`,
`tls` — that is `pub(crate)`. A fix to request framing, the HTTP/2 or HTTP/3
framer, the connection pump or the transport belongs in `protocol/` — never in
`server` or a route handler. `references/api-core.md` indexes the
internal half too, which does **not** mean those items are callable outside.
**A gated path is not covered by a macOS test run** — `core/src/protocol/uring/` is
`#[cfg(target_os = "linux")]`: [Field visibility](references/field-visibility.md).

## Load by task

| Task | Reference |
|---|---|
| Server, Context, hooks, configuration | [Core](references/api-core.md) |
| Route/hyperlane/request/response/filter macros | [Macros](references/api-macros.md) |
| Request, Response, Stream, cookies and protocol types | [HTTP types](references/api-type.md) |
| Client requests, proxying and response decoding | [Client](references/api-request.md) |
| Compression, constants, content negotiation, ETags, conditional 304 | [Compression](references/api-compress.md) · [Constants](references/api-constant.md) · [Negotiate](references/plugin-negotiate.md) |
| Plugin crates, priorities and configuration | [Plugins](references/plugins.md) |
| Performance harness and throughput verdicts | [Benchmark](references/bench.md) |
| Wire bytes, statuses, chunking, 100-continue · WebSocket · SSE | [Wire behaviour](references/wire-behaviour.md) · [WS](references/hyperlane-plugin-websocket.md) · [SSE](references/sse.md) |
| Release delivery, request-path ownership, field visibility | [Release flow](references/release-bump-flow.md) · [Ownership](references/request-path-ownership.md) · [Field visibility](references/field-visibility.md) |

Cached reference pages can lag current source. Reject a claimed path or signature
when the actual selected package disagrees; do not force code to match the cache.
For service validation, reclaim task-owned listeners, processes, browser tabs and
containers on success and failure, and verify exact IDs/ports against the baseline.
Normal euv UI work, generic Cargo/Git tasks and ltpp.vip publication are not this
entry point — see [hyperlane-upload](../hyperlane-upload/SKILL.md).