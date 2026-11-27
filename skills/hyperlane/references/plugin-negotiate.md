# hyperlane-plugin-negotiate

Source: `plugin/negotiate/src/` at `origin/master` (`04dee24`, workspace
version `22.13.0`). The crate description: "A response negotiation plugin for
the Hyperlane framework, answering with the content coding the client accepts
and with 304 Not Modified while a validator still matches."

Published with the workspace: it is a workspace member, carries `publish = true`
and is named in `.github/workflows/rust.yml`'s `PACKAGES` array, so it ships at
whatever version the workspace is at. The newest crates.io release confirmed
while writing this page was `22.8.2`; the workspace has since moved to
`22.13.0`. It depends on the `hyperlane` facade
plus `http-compress`, so it compiles against workspace source, not against a
released version. `cargo metadata --no-deps --format-version 1` is the
authority for the member list; the root `hyperlane` package counts too.

## Opt-in, not attribute-registered

This is the plugin that breaks the "a plugin needs no registration call" rule.
It ships **no** `#[hyperlane::request_middleware]` / `#[hyperlane::response_middleware]`
attribute and therefore no `inventory::submit!`. Being a dependency does
nothing. The application registers each middleware explicitly on the server:

```rust
use hyperlane_plugin_negotiate::{CompressMiddleware, ConditionalMiddleware};

server
    .response_middleware::<CompressMiddleware>()
    .response_middleware::<ConditionalMiddleware>()
    .response_middleware::<SendMiddleware>();
```

`Server::response_middleware::<S>()` where `S: ServerHook` is **synchronous**,
takes no argument and returns `&mut Self` — do not append `.await`. Both
middlewares run **after the route and before the sender**: a route keeps
building its response and returning `Status::Continue`, and the middleware
that writes the bytes onto the stream runs last. A route that answers with
`#[hyperlane::send]` writes the bytes itself and leaves nothing for a response
middleware to negotiate.

Register the coding middleware **before** the conditional middleware: the
coding middleware declares `Vary: accept-encoding`, and the conditional
middleware can then turn the answer into a `304` that keeps it.

### The README example names a middleware the crate does not export

The crate README's snippet ends with `.response_middleware::<SendMiddleware>()`,
but `plugin/negotiate/src/lib.rs` re-exports `struct::*` only —
`CompressConfig`, `CompressMiddleware`, `ConditionalMiddleware` and `EntityTag`.
There is **no `SendMiddleware` in this crate**; the only `SendMiddleware` in the
workspace is the one `performance/src/bin/server/main.rs` defines for its own
harness. The README block is `rust,ignore`, so nothing compiles it and the name
never broke a build. Copying it verbatim fails to compile.

The application supplies its own sender. `SenderMiddleware` in
`plugin/negotiate/tests/negotiate/impl.rs` is the shape to copy — build the
response, send it, keep going:

```rust
async fn handle(self, stream: &mut Stream, ctx: &mut Context) -> Status {
    let data: Vec<u8> = ctx.build_response();
    let _: Result<(), ResponseError> = stream.try_send(data).await;
    Status::Continue
}
```

Register it **last**: the coding and conditional middlewares run before it, and
a `#[hyperlane::send]` route writes the bytes itself and leaves nothing to
negotiate.

## `CompressMiddleware`

Declares the negotiated coding on the response and lets the response builder
apply it. The middleware **never writes to the stream** — it only sets
`Content-Encoding`, and the sender serializes (and compresses) from there.

`negotiated_coding` reads every `Accept-Encoding` field of the request. When
the field occurs once it hands that value straight to
`Compress::from_accept_encoding`; when it occurs more than once it joins the
occurrences with a comma first, because every occurrence names codings the
client accepts.

A response is left alone — no coding, no `Vary` — when any of these holds:

| Skip | Check in source |
|---|---|
| The client accepts no implemented coding | `negotiated_coding` returned `None` |
| The response already declares a coding | `headers.contains_key(CONTENT_ENCODING)` |
| The response forbids transformation | `has_no_transform(response)` — any `Cache-Control` field carrying the `no-transform` directive |
| The body is below the threshold | `body.len() < config.min_length` |
| The status carries no body | `has_no_body(status)` |
| It is an event stream | `is_event_stream(response)` |

`has_no_body` covers `100..=199`, `204 NoContent`, `205 ResetContent` and
`304 NotModified` — a subset of the framework's own bodyless set, which also
omits `Content-Length` for `304`. `is_event_stream` matches the
`Content-Type` value against `text/event-stream` case-insensitively, because
a coded stream would hold bytes back until the whole stream was compressed.

Every coded response declares `Vary: accept-encoding`. An existing `Vary` is
**extended, not replaced**: if the response already declares `vary` it gains a
second field entry (`add_header`), so a wire response can carry both
`vary: origin` and `vary: accept-encoding`. If the response already declares
`accept-encoding` among its `Vary` entries (comma-split, case-insensitive),
nothing is added — and **neither is anything added when the response declares
`Vary: *`**, because a wildcard variance already covers every request header,
`accept-encoding` included.

### Configuration

| knob | default | meaning |
|---|---|---|
| `min_length` | `256` (`DEFAULT_MIN_LENGTH`) | the body length below which a response is answered without a coding |

```rust
CompressMiddleware::init(CompressConfig::new(1_024))?;  // Result<(), String>
```

The configuration is **process wide**: the framework registers a middleware
by its type and builds a hook per request, so a server cannot carry a
configuration of its own. It lives in a `OnceLock` behind `static CONFIG`, so
`init` refuses a second set with `"the compress configuration was already
set"`. `CompressConfig::get_min_length()` reads the threshold;
`CompressConfig::default()` is `256`. Unlike the logger plugin, a missing
configuration is **not** a no-op — the middleware falls back to the default
threshold and still negotiates.

## `ConditionalMiddleware`

Declares a strong entity-tag on every response that carries a body under a
safe method, unless the response already declares one, and answers
`304 Not Modified` when the request's `If-None-Match` matches it.

`entity_tag` reads the response's existing `ETag` (the **last** value) and
keeps it when present — "the application knows what its representation is
better than a digest of the bytes it happens to produce". Otherwise it
computes `EntityTag::strong(body)`.

`EntityTag::strong(&[u8])` is the quoted hexadecimal digest of the data:
`XxHash3_64` over the body, `format!("{:016x}")` rendered into an 18-byte ASCII
buffer without `format!`, wrapped in `"`. The same
body therefore always produces the same tag, across processes and across
restarts. `EntityTag::as_str()` renders it as the `ETag` field carries it.
The field name is `ETAG` and the tag the middleware computes is always
**strong** (no `W/` prefix).

**A weak tag is a first-class value, not a string the middleware invents.**
`EntityTag::weak(&[u8])` builds `W/"<hex>"`, `is_weak()` reports the prefix,
`opaque_tag()` returns the quoted portion without it, and `weak_eq()` /
`strong_eq()` perform the RFC 9110 §8.8.3.2 weak and strong comparisons.
`ConditionalMiddleware` itself only ever computes a strong tag — an application
that wants a weak validator calls `EntityTag::weak` itself and declares the
field, and `existing_etag` then keeps it, because "the application knows what
its representation is better than a digest of the bytes it happens to produce".

`handle` skips when:

| Skip | Check in source |
|---|---|
| The method is unsafe | `!method.is_get() && !method.is_head()` |
| The status is not a success | `!(200..300).contains(&status_code)` |
| The status carries no body | `has_no_body(status)` |

The `200..300` guard is the newer of the three: a redirect or an error answer
carries no representation to validate, so the middleware leaves it alone. It
also means the middleware never rewrites a `3xx` into a `304`.

On a match — `ctx.get_request().matches_if_none_match(etag.as_str())`, the
public `http-type` helper — it sets the status to `304 NotModified` and
replaces the body with `EMPTY_STR`. The response keeps its representation
metadata, so the validator, the variance and the content type survive the
`304`. On a mismatch the response is answered as it stands.

A HEAD request is treated as safe, so it can be answered with a `304` — which
matches the wire rule that a HEAD response ends at the headers and carries no
body.

## Wire evidence

`plugin/negotiate/tests/negotiate/` drives a real `HTTP/1.1` server on
loopback and asserts on the exact bytes. The routes it registers are
`LargeRoute`, `SmallRoute`, `CodedRoute`, `StreamRoute`, `NoContentRoute`,
`VaryRoute` and `ValidatedRoute`, each behind
`.response_middleware::<CompressMiddleware>()`
`.response_middleware::<ConditionalMiddleware>()`
`.response_middleware::<SenderMiddleware>()`.

- A coded response declares `content-encoding`, `vary: accept-encoding`, and a
  `content-length` equal to the **coded** body length; the gzip body starts
  with the `1f 8b` magic.
- A small body is sent as it is, with no coding and no variance.
- A route that already declares `content-encoding: br` keeps it.
- A `text/event-stream` response is sent as it is.
- A `204` is sent plain.
- An absent field, an unimplemented coding (`zstd`) and a refused coding
  (`br;q=0`) all leave the response plain.
- A HEAD of a coded body declares the coding but no `content-length` and no
  body.
- A response that declared `vary: origin` carries two `vary` fields.
- A first response declares an `ETag`; a repeat carrying
  `If-None-Match: <that tag>` answers `304` with no body and the same `ETag`.
- A request carrying a non-matching `If-None-Match` answers `200` with the
  plain body.
- `test_security_conditional_never_turns_error_status_into_304_and_honors_no_transform`
  locks the two newer guards: a non-`2xx` answer is never rewritten into a
  `304`, and a response that declares `Cache-Control: public, no-transform` is
  answered plain.
