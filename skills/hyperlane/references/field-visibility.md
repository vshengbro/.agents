# Public-field narrowing and the `protocol/` layout

Source: `origin/master` (`4d22b46`, workspace version `22.8.0`) of
`hyperlane-dev/hyperlane`. Verified against the committed tree and the
crates.io API, not against a local branch.

## Why a public struct keeps its fields crate-internal

A `pub` field on a `pub` struct is part of the crate's published API. A
consumer can write `response.status_code` instead of
`response.get_status_code()`, which bypasses the accessor the struct was
designed around and freezes the field layout into the API: renaming the field
or changing its type becomes a breaking change instead of a private refactor.

So a public struct keeps its fields crate-internal and the consumer reaches
them through the generated `get_*` and `set_*` accessors. **The accessor stays
public — that is the whole point.**

The narrowing moved **105 fields across 23 files** from `pub` to
`pub(crate)`. The call sites that read a field directly moved to the accessor.

## The two exemptions

- **A package that ships BOTH a library and a binary has two crates**, and the
  binary is an external consumer of the library. `hyperlane-cli`'s `Args` keeps
  its fields public, because the `hyperlane` binary reads it.
- **A struct that a package's own binary target reads through its accessors**
  is exempt for the same reason.

The first pass of the narrowing exempted every accessor a package's binary
target reads, matched by name alone. That exempted more than it should: the
binary reads `Args::get_project_name`, and `NewProjectConfig` has a
`project_name` of its own. The exemption now resolves the struct through the
**type** of the binding the accessor is called on, so it exempts the struct the
binary actually reads and no other. The four fields that were wrongly left
public moved to crate-internal.

## The published API did not change

The rustdoc JSON of all seven crates was compared before and after the
narrowing: **0 items removed and 0 items added**. The narrowing is a visibility
change inside the crate, not a change to the exported surface.

## A gated path is not covered by a macOS test run

`core/src/protocol/uring/` is `#[cfg(target_os = "linux")]`. Narrowing
`Stream`'s transport field to crate-internal broke the Linux build silently:
the io_uring path could no longer shut the transport down through the field.
The field narrowing was verified on macOS only, so the breakage only showed up
in the Linux build.

The fix is `Stream::shutdown()` — a public method on `Stream` that reaches the
transport through the accessor — and the io_uring path calls that instead of
touching the field. The workspace is now checked and tested on Linux as well,
so a gated path cannot break unnoticed again.

Verification for that fix:

- `cargo check --workspace --all-targets` — 0 error, 0 warning;
- `cargo test --workspace --all-features` on macOS — 1066 passed, 0 failed;
- the same on Linux, in `rust:1.100-slim` — 1082 passed, 0 failed;
- the rust-standards audit 56/56 PASS, `cargo fmt` idempotent,
  `cargo clippy --all-targets` 0 warnings.

## The current `protocol/` layout

`hyperlane-core` splits into a public half and an internal half.

| Half | Modules | Visibility |
|---|---|---|
| public | `config`, `context`, `error`, `hook`, `route`, `server` | re-exported at the root |
| internal | `listener`, `protocol`, `tls` | `pub(crate)` — unreachable from outside the crate |

`protocol/` is now **nine modules plus `uring`**:

| Module | Holds |
|---|---|
| `aliases` | the type aliases (`ProtocolHeaders`, `ConnectionH2`, `QuicConnection`, …) |
| `constants` | the wire constants and the error message strings |
| `http2` | the HTTP/2 framer, request task and fail path |
| `http3` | `qpack` (encoder/decoder), `shard` (connection shards), `stream` (the HTTP/3 framer, request task and fail path) |
| `inline` | the stack-allocated inline hook dispatch and the compiled route pipeline |
| `pump` | the pooled buffers, the body budget, the status-code check, the poll helper |
| `request` | building the framework request from a protocol head |
| `response` | the response head parser, the request-error reply, the 100-continue response |
| `transport` | the TLS transport and the connection environment |
| `uring` | the io_uring reactor — `#[cfg(target_os = "linux")]` only |

Two modules were **removed**: `framing` (the `ResponseFramer` trait) and
`lifecycle` (the `ServerLifecycle` struct). `pump` now owns the pooled
buffers, the body budget and the status-code check that used to sit in
`framing` and `lifecycle`.

`inline` is new. It holds `INLINE_FUTURE_WORDS` (32 machine words) of
stack-allocated inline hook storage, the `InlineHookGuard` that unregisters an
inline initializer when its handler `Arc` is dropped, the `CompiledPipeline`
dispatch table built once when `Server::run` starts, and the compiled route
maps.

A fix to request framing, the HTTP/2 or HTTP/3 framer, the connection pump or
the transport belongs in `protocol/` — never in `server`, and never in a route
handler. `api-core.md` indexes the internal half too, which does **not** mean
those items are callable outside the crate.
