# HTTP/1.x wire behaviour (RFC 9110 / 9112)

Source: `type/src/response/impl.rs`, `type/src/chunked/`, `type/src/stream/`,
`core/src/protocol/`, `request/src/request/parser/` at `origin/master`
(workspace version `22.8.0`).

This page records the wire behaviour that the `22.6.0` release aligned with
RFC 9110 and RFC 9112. Everything here was read in the source at that ref;
the named test is the one that locks the behaviour. `22.7.0` and `22.8.0`
changed no wire contract.

## Bodyless statuses

`Response::build()` (`type/src/response/impl.rs`) branches on the status code
before it writes anything:

| status | body | framing headers |
|---|---|---|
| `100..=199` | none | none — `Content-Length` and `Transfer-Encoding` are removed |
| `204` | none | none |
| `205` | none | `Content-Length: 0` |
| `304` | none | none — the representation metadata (`ETag`, …) is kept |

The removal is a case-insensitive sweep over the response headers, so a
`content-length` written in lower case is removed too.

Locked by `type/tests/response/fn.rs`:

- `response_build_early_hints_omits_body_and_framing_headers` — a 103 with
  `Transfer-Encoding: chunked` and a body serializes to the status line, no
  `Content-Length`, no `Transfer-Encoding`, no body.
- `response_build_no_content_omits_body_and_framing_headers` — a 204 with a
  pre-existing `Content-Length: 10` loses it.
- `response_build_reset_content_writes_zero_length_even_for_event_stream` — a
  205 with `Content-Type: text/event-stream` still writes `Content-Length: 0`
  and no `Transfer-Encoding`.
- `response_build_not_modified_preserves_etag_without_body_or_generated_length`
  — a 304 keeps `ETag: "revision-1"`, gains no `Content-Length` and no body.

## HEAD

`Response::build_head()` (`type/src/response/impl.rs`) is the header-only
serializer. It never writes the body.

It first **removes** the framing headers (`Content-Length` and
`Transfer-Encoding`), then re-declares a `Content-Length` only when the body
is nonempty, is not `text/event-stream`, and carries no known
`Content-Encoding`. The length of a body that was never compressed cannot be
announced, so an empty body, an event stream and a compressed body all end up
without a length.

Verified on a real socket at `origin/master` (`22.6.0`), with the handler
rewriting the request method to `GET` so that only the *wire* method could
decide:

| request | response head |
|---|---|
| `HEAD`, no body set | `HTTP/1.1 200 OK` + `connection` + `content-type` — no `content-length` |
| `HEAD`, body `"head-body"` set | `HTTP/1.1 200 OK` + **`content-length: 9`** + `connection` + `content-type` — no body bytes |
| `HEAD`, body `"head-body"` + `content-encoding: gzip` | `HTTP/1.1 200 OK` + `connection` + `content-encoding: gzip` + `content-type` — no `content-length`, no body |

`Context::build_response()` (`core/src/context/impl.rs`) chooses the
serializer. It reads the recorded wire method first:

- `Context` carries `original_head: Option<bool>`, set by
  `Server::request_hook` (`core/src/server/impl.rs`) to
  `request.get_method().is_head()` **before** the request middleware runs.
- `build_response()` uses `try_get_original_head()` when it is set, and falls
  back to `self.get_request().get_method().is_head()` otherwise — that is the
  case for a manually constructed `Context`.

So a middleware that rewrites the method to `GET` does not make a HEAD request
answer with a body.

The macros use it: `macros/src/send/fn.rs` expands the argument-less form of
`#[send]` / `#[try_send]` to `stream.send(ctx.build_response()).await` and
`stream.try_send(ctx.build_response()).await`. An attribute **with** an
argument expands to the expression itself and is sent verbatim.

The unit tests are in `type/tests/response/fn.rs`
(`response_build_head_preserves_encoding_without_generating_a_length`,
`response_build_head_omits_length_when_no_representation_was_provided`) and
`tests/protocol/head/` at the workspace root drives a real socket:

- `http1_head_no_arg_send_attributes_preserve_length_without_body` — the
  argument-less `#[send]` on a HEAD request answers with the headers and no
  body.
- `http1_head_explicit_send_attributes_write_bytes_verbatim` — `#[send(bytes)]`
  writes exactly the given bytes.

`core/tests/protocol/limits/` covers the same behaviour over HTTP/2 and
HTTP/3 (`http2_head_response_carries_headers_without_a_body`,
`h3_head_and_no_body_statuses_carry_no_body`).

## Chunked request bodies

The server-side decoder lives in `type/src/chunked/`:

| file | what it holds |
|---|---|
| `type/src/chunked/const.rs` | the bounds and the two error values |
| `type/src/chunked/fn.rs` | `fill_chunked_body` and its helpers |

`fill_chunked_body(reader, body, config)` decodes one chunked body into the
reusable `RequestBody`. It is reached from `type/src/stream/fn.rs`:
`fill_chunked_request` calls it and then `Request::normalize_chunked_headers`.

### The framing rules

`Request::get_http_headers` (`type/src/request/impl.rs`) returns a
`RequestFraming` — `Fixed(usize)` or `Chunked` — instead of a bare length.
The rules it enforces:

- `Transfer-Encoding` on an **HTTP/1.0** request is `400 Bad Request`.
- `Transfer-Encoding` **together with** `Content-Length` is `400 Bad Request`,
  in either order.
- A repeated `Content-Length` is still `400`; a comma separated length list,
  a non decimal length and an overflowing length are still refused.

`parse_transfer_encoding` (`type/src/request/fn.rs`) then resolves the coding
list:

- the last coding must be `chunked`; a coding **after** `chunked` is `400`;
- `chunked` must be present at all — a request with only another coding is
  `400`, whatever that coding is;
- a coding that is neither a valid token nor `chunked` is `400`;
- a coding the server does not implement (`gzip`, `identity`, …) that appears
  **next to** `chunked` is `501 Not Implemented`. The check runs only after
  the list is confirmed to end in `chunked`, so `Transfer-Encoding: identity`
  alone is `400` while `Transfer-Encoding: gzip, chunked` is `501`.

Locked by `type/tests/stream/fn.rs::http1_rejects_unsupported_or_invalid_transfer_codings`:

| headers | status |
|---|---|
| `transfer-encoding: identity` | `400` |
| `TRANSFER-ENCODING: gzip, chunked` | `501` |
| `Transfer-Encoding: ` (empty) | `400` |
| `Content-Length: 0` + `Transfer-Encoding: chunked` | `400` |
| `Transfer-Encoding: chunked` + `Content-Length: 0` | `400` |

### What the handler receives

`Request::normalize_chunked_headers` (`type/src/request/impl.rs`) rewrites the
headers after the decode: it removes `Transfer-Encoding` and `Trailer`, and
inserts `Content-Length` with the **decoded** length.

The trailer fields are validated and discarded — they never reach the
handler's headers. `validate_chunk_trailer` (`type/src/chunked/fn.rs`) refuses
a trailer whose name is `Content-Length`, `Transfer-Encoding` or `Host`, whose
name is not a token, whose value carries a forbidden byte, or that exceeds the
configured key or value size limit.

Locked by `type/tests/stream/fn.rs::http1_chunked_decodes_binary_and_preserves_the_next_request`:
a request with `Transfer-Encoding: chunked`, a `Trailer: X-Checksum` header, a
chunk extension `4;note="a;b"` and a trailer `X-Checksum: sample` yields the
body `b"\0\xff\r\n0123456789"`, a `Content-Length: 14`, **no**
`Transfer-Encoding`, **no** `trailer` and **no** `x-checksum`, and the next
pipelined request is still parsed.

### The bounds

| bound | value | where |
|---|---|---|
| one chunk-size or trailer line | 8 KiB | `MAX_CHUNK_LINE_BYTES` |
| extension bytes across all chunk sizes | 64 KiB | `MAX_CHUNK_EXTENSION_BYTES` |
| the whole trailer section | 64 KiB | `MAX_CHUNK_TRAILER_BYTES` |
| the decoded body | the configured `max_body_size` | `RequestConfig` |

The body limit applies to the **decoded** size. Locked by
`type/tests/stream/fn.rs::http1_chunked_enforces_the_cumulative_decoded_body_limit`:
with `max_body_size` 6 the body `abcdef` is accepted, with 5 it is refused
with `413 Payload Too Large`.

Verified on a real socket at `origin/master` (`22.6.0`). A handler that
reports the request body length and the framing headers it can see received
`len=4 cl=4 te=false trailer=false` for a chunked request whose wire body was
`4\r\nabcd\r\n0\r\nX-C: v\r\n\r\n` — the decoded length is 4, the
`Content-Length` header is 4, and neither `Transfer-Encoding` nor `Trailer`
nor the trailer field is visible to the handler.

The same probe confirmed the refusal statuses:

| request | response |
|---|---|
| `Transfer-Encoding: gzip, chunked` | `501 Not Implemented`, `content-length: 0`, `connection: close` |
| `Transfer-Encoding: identity` | `400 Bad Request`, `content-length: 0`, `connection: close` |
| `Transfer-Encoding: chunked` + `Content-Length: 4` | `400 Bad Request`, `content-length: 0`, `connection: close` |

A malformed chunk is `400` (`INVALID_CHUNK`), and metadata over its bound is
`431` (`CHUNK_METADATA_TOO_LARGE`).

## Expect: 100-continue

The interim response is `HTTP/1.1 100 Continue\r\n\r\n` with no fields and no
body — `type/src/stream/const.rs::HTTP_CONTINUE_RESPONSE` for HTTP/1.x, and
`core/src/protocol/response/fn.rs::continue_response()` for the HTTP/2 and
HTTP/3 framers.

The expectation is detected by matching the bare token `100-continue`
(`CONTINUE_EXPECT` in `http-constant`) inside the `Expect` list,
case-insensitively, **without** splitting on a comma inside a quoted
extension value. Two independent implementations do this — `type/src/stream/fn.rs::contains_continue_member`
for HTTP/1.x and `core/src/protocol/request/fn.rs::contains_continue_member`
for the multiplexed protocols.

The interim response is sent only when it applies:

- the request must be **HTTP/1.1** (`expects_http_continue` checks
  `request.get_version().is_http1_1()`);
- for a **fixed-length** body the body must not already have arrived — for
  HTTP/1.x the server compares the declared length against the bytes already
  in the read buffer, and for HTTP/2 the stream must not already be ended. A
  chunked request has no declared length to compare, so it always gets the
  interim response when the expectation applies.

Verified on a real socket at `origin/master` (`22.6.0`): a request that
declares `Expect: 100-continue` and holds its body back receives exactly
`HTTP/1.1 100 Continue\r\n\r\n` before the body is sent.

Locked by `type/tests/stream/fn.rs::http1_expect_omits_interim_when_continue_does_not_apply`
— the four cases produce **zero** bytes back to the client:

| version | `Expect` value | body | buffer |
|---|---|---|---|
| HTTP/1.1 | `100-continue` | empty | 64 |
| HTTP/1.1 | `100-continue` | 128 bytes | 4096 |
| HTTP/1.0 | `100-continue` | 128 bytes | 64 |
| HTTP/1.1 | `extension="value, 100-continue, end"` | 128 bytes | 64 |

The positive side is locked by `core/tests/protocol/limits/`:
`http1_expect_continue_releases_the_waiting_request_body`,
`http2_expect_continue_releases_the_waiting_request_body` and
`http3_expect_continue_releases_the_waiting_request_body` each get the
declared body back, and `http2_expect_oversized_body_is_rejected_without_continue`
and its HTTP/3 twin confirm that a body over the limit is refused **without**
an interim response.

## The default request error response

`core/src/protocol/response/fn.rs` holds the two new helpers:

- `h1_error_response_version(stream, error)` — picks `HTTP/1.0` or `HTTP/1.1`
  from the request line the parser saw. It returns `None` when the line buffer
  is empty **and** the error is `HttpRequestPartsInsufficient` or
  `ReadTimeout`, which is the idle-connection case: no reply is sent.
- `reply_to_request_error(server, stream, ctx, error, version)` — sends the
  reply. When the server has request-error hooks it calls
  `handle_request_error` instead and the default reply is **not** sent. When
  there is no hook it builds a `Response` with the status from
  `error.get_http_status_code()`, adds `Connection: close` for HTTP/1.x,
  sends it with `stream.try_send` and flushes.

The reply body is empty and carries `Content-Length: 0`. The disconnect
errors (`ClientDisconnected`, `ClientClosedConnection`,
`ServerClosedConnection`) are never answered — there is nobody left to answer.

`core/src/server/impl.rs` calls it from both failure paths: the first request
on a connection (`handle_connection`) and the next request on a keep-alive
connection (`handle_http_requests`).

Verified on a real socket at `origin/master` (`22.6.0`): a request with a
duplicate `Content-Length` and **no** request-error hook received
`HTTP/1.1 400 Bad Request` with `content-length: 0` and `connection: close`;
with a hook registered, the hook's own body (`handled`) was sent instead and
the default reply was not.

**A request for a route that does not exist is a different case and gets no
reply at all.** The route matcher simply finds no hook, the pipeline finishes
and nothing is written — not a `404`, and not the request-error hook.
Verified on a real socket at `origin/master` (`22.6.0`): `GET /missing`
returned zero bytes, both with and without a registered request-error hook.

Locked by `core/tests/protocol/limits/assert.rs`:

- `http1_default_request_error_replies_with_413_and_closes` — status `413`,
  `Connection: close`, `Content-Length: 0`, empty body.
- `http1_default_request_error_sends_nothing_on_clean_eof` — nothing is sent.
- `http2_default_request_error_replies_with_413_and_keeps_connection_usable`
  and the HTTP/3 twin — status `413`, `Content-Length: 0`, **no** `Connection`
  header, and the connection stays usable.
- `default_request_error_does_not_override_the_existing_http1_hook` — a
  registered hook still owns the body.

## The client side

`request/src/request/parser/` gained a framing layer:

| file | what it holds |
|---|---|
| `request/src/request/parser/enum.rs` | `ResponseFraming` — `Fixed(usize)`, `Chunked`, `Close` |
| `request/src/request/parser/type.rs` | `FinalResponseHead`, `ResponseHeadFields` |
| `request/src/request/parser/fn.rs` | the framing helpers |

`parse_response_headers(headers_bytes, is_head)` now returns the framing and
the redirect target, or `None` for an **interim** response (status < 200).
`find_final_response_head(bytes, search_start, is_head)` skips the interim
heads, drains them out of the buffer and returns the offset of the final head
with its framing.

The rules:

- a status below `100` or above `599`, a status line that is not
  `HTTP/x.y <code>`, or a malformed status line is
  `RequestError::Request(INVALID_RESPONSE_FRAMING)`;
- `101 Switching Protocols`, `204 No Content` and `304 Not Modified` end the
  body at the headers;
- a **HEAD** response ends at the headers regardless of the framing fields it
  carries — the length it announces is representation metadata (RFC 9112
  §6.3);
- `Content-Length` together with `Transfer-Encoding: chunked` is refused;
- no `Content-Length` and no chunked coding means the body ends at EOF
  (`ResponseFraming::Close`).

`get_content_length` now returns `Option<usize>` — it distinguishes an absent
`Content-Length` from a declared zero.

The client accepts the bad whitespace RFC 9112 §7.1.1 permits before a chunk
extension delimiter: `parse_chunk_size` trims the trailing whitespace of the
size bytes when an extension delimiter is present. The bad whitespace is still
refused when there is no extension, because RFC 9112 does not permit it there.

`HttpRequest::send` / `send_async` accept **HEAD** as well as GET and POST
(`send_bodyless_request_sync` / `send_bodyless_request_async` in
`request/src/request/http_request/impl.rs`). A HEAD response is not decoded,
even when the client is configured to decode.

## Request parsing refuses what it cannot frame

The server parser refuses a request it cannot frame unambiguously. Each of
these is a `RequestError`, and HTTP/1.0 without `Host` is still accepted:

- a repeated `Content-Length`;
- a comma separated length list;
- a non decimal or overflowing length;
- a folded header;
- whitespace before the field colon;
- a control byte in a field value;
- a malformed field name;
- a repeated `Host`;
- a request line that does not hold exactly three fields.

The client refuses a request whose name, value or target carries a control
byte, whose scheme is not http or https, or whose host is empty — and for
HTTP/2 and HTTP/3 a request whose authority disagrees with the `Host` header.

Each bug class has a test in `type/tests/stream/fn.rs` and `request/tests/`.

`Request::matches_if_none_match(current_etag)` is a **public helper on
`http-type`**: it checks `If-None-Match` against the entity-tag of a
representation that already exists, compares the opaque tag values
case-sensitively with weak comparison, and returns `false` for a missing field,
an empty list, an invalid tag or any malformed suffix — a matching predicate
only, so it sends nothing and does not implement `If-Match`.

## What did not change

- The route registration, the hook order and the plugin surfaces are
  untouched by this release.
- The hot-path ownership work (the stack hash secret, the pooled buffers, the
  borrowed reason phrase) is unchanged; see
  [Request path ownership](request-path-ownership.md).
- The `Expect` handling does not change the request body, the limit or the
  parser: an interim response only releases a client that was waiting.
