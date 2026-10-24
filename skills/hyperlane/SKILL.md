---
name: hyperlane
description: "Use when implementing or debugging the Hyperlane Rust HTTP framework: server routes, lifecycle hooks, Context, requests and responses, the plugin crates, or the perf harness. Publishing files to ltpp.vip uses hyperlane-upload instead."
license: MIT
metadata:
  hermes:
    related_skills: [rust-standards]
---

# Hyperlane framework entry

## Index

Shortest path · Current source contracts to verify · Load by task

## Shortest path

1. Resolve the actual dependency version and workspace with `cargo metadata
   --no-deps --format-version 1`. Local uncommitted APIs are not necessarily
   available in the published `hyperlane` / `http-type` package.
2. Load `rust-standards` and the one relevant reference below. Inspect the
   actual route/hook implementation in the selected version before copying a
   tutorial.
3. Keep route paths and configuration values in the project's named constants.
   Implement against public contracts; do not widen visibility merely for tests.
4. Format, compile, lint and test through the project's real gates. Exercise the
   exact request and response bytes for wire changes; a registered route or an
   HTTP connection alone is not proof a nonempty response was sent.
5. Increment only the root `Cargo.toml` version for publishable code changes.
   CI synchronizes member/dependency versions; do not manually change those pins.

## Current source contracts to verify

These are checked at `core/src/server/impl.rs`, `core/src/hook/trait.rs`,
`type/src/response/impl.rs` and `type/src/stream/impl.rs`; recheck for another
version.

- `Server::route::<Handler>(path)` is **synchronous**, returning `&mut Self`.
  Request/response middleware registration is also synchronous. Do not append `.await`.
- `Server::run().await` returns `Result<ServerControlHook, Box<ServerError>>`;
  propagate or report binding failure. `unwrap_or_default()` must not hide it.
- `ServerHook::new(stream, ctx)` returns a future of `Self`;
  `handle(self, stream, ctx)` returns a future of `Status`. `stream` comes first.
- Returning `Status::Continue` continues the lifecycle; `Status::Reject` stops it.
  Check which response middleware actually runs before deciding who sends bytes.
- Setting a response body alone does not transmit it. In a direct-send handler,
  build the response, await `stream.try_send(data)`, handle its error, then stop
  the pipeline with `Status::Reject` to avoid duplicate downstream sending.
- Response setters and `build()` are synchronous; `try_send` is asynchronous.
  Treat generated accessors as real APIs, but verify them through generated
  docs/compiler output rather than guessing from a field name.

Within an existing async startup function, the registration/start sequence is:

```rust
server.route::<Index>(ROOT_PATH);
let control: ServerControlHook = server.run().await?;
control.wait().await;
```

This fragment assumes the application's existing `Index`, `ROOT_PATH`, `Server`
configuration and error-returning context; it is not a standalone server template.
For a full handler, adapt the selected source's real example and compile it.

### Hook order and priority

`HookType` carries an `Option<isize>` order. The framework sorts hooks by that
key with `sort_by_key`, and `Option` orders `None` **before** every `Some`.
The consequences are mechanical, not stylistic:

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
`hyperlane-plugin-logger` and `hyperlane-plugin-websocket` are published to
crates.io; the framework crates are at `22.0.6`. The other four plugin crates
(`hyperlane-plugin-compression`, `-cors`, `-shutdown`, `-static-files`) were
removed from the tree on 2026-10-24, and their last versions stay on crates.io
at `22.0.6`. The four `bench-*` crates carry `publish = false` and are usable
only from a path dependency. Verify the live registry before asserting a
version.

The workspace tree is one patch ahead of the registry: the root `Cargo.toml`
says `22.0.7` in the working tree, and that version is **not** on crates.io.
Three version numbers must be kept apart — the committed HEAD, the local
working tree and the published registry — and only the last one is what a
consumer can install.

`hyperlane-macros` has a second, older release line on crates.io: `23.0.21`
depends on `hyperlane ^21.3.6` and `syn ^2`, which does not match the current
workspace's `syn ^3`, and it is the highest number on the registry. A plain
`cargo add hyperlane-macros` therefore resolves to that stale line. Pin the
version the workspace uses instead of taking the highest.

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

Cached reference pages can lag current source. Reject a claimed path or signature
when the actual selected package disagrees; do not force code to match the cache.
For service validation, reclaim task-owned listeners, processes, browser tabs and
containers on success and failure; verify exact IDs/ports against the baseline.
Normal euv UI work, generic Cargo/Git tasks and ltpp.vip publication are not this
entry point. Use [hyperlane-upload](../hyperlane-upload/SKILL.md) only for that
explicitly selected public hosting destination.
