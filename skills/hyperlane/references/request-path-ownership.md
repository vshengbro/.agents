# Request path ownership

The request path stopped allocating for work it can do in place. The bytes on
the wire are unchanged; what changed is who owns the memory.

## The hash secret stays on the stack

`http-compress` ships `XxHash3_64`. The `twox_hash` hasher it replaces
allocates its 192-byte secret on the heap, so every hash operation costs one
allocation — and a request that looks a header up in a map pays that
allocation per lookup. `XxHash3_64` holds the secret in the hasher itself.

It keeps the same secret and produces the same hash values. The crate's own
test (`compress/tests/xx_hash3_64/fn.rs::xx_hash3_64_matches_the_allocating_hasher`)
asserts that for eight inputs, including an empty one and one long enough to
pass the small-input cutoff. `HashMapXxHash3_64` therefore keeps its meaning:
a map keyed by it hashes a header name exactly as before.

```rust
use http_compress::XxHash3_64;
use std::hash::Hasher;

let mut hasher: XxHash3_64 = XxHash3_64::default();
hasher.write(b"connection");
let _: u64 = hasher.finish();
```

## The response is built into bytes

`http-type` builds a response into a `ResponseData` (`Vec<u8>`) rather than a
`String`, and renders the body length into a caller-owned buffer
(`response::fn::render_length`). The reason phrase is borrowed rather than
copied: `HttpStatus::phrase_ref` returns `&'static str`, and `build()` writes
it into the phrase buffer the response already owns.

`22.6.0` split the serializer in two: `build()` for a normal response and
`build_head()` for the header-only answer a `HEAD` request gets.
`Context::build_response()` picks between them from the recorded wire method,
and the `#[send]` / `#[try_send]` macros call it. See
[Wire behaviour](wire-behaviour.md).

These bytes are what the wire sees, so a change here is a change to the
protocol: check the exact bytes a response produces, not only that a route
answered.

## Buffers and header entries are recycled

`type/src/stream/static.rs` holds two thread-local pools: `READ_BUFFER_POOL`
for read buffers and `HEADER_ENTRY_POOL` for header entries. A header entry
keeps the buffers it owns when it is recycled, so the next request that needs
a header reuses them instead of allocating a fresh name, a fresh value list
and a fresh value.

The old `STRING_POOL` is gone, and so are `take_recycled_string` /
`return_recycled_string`; the string pool was replaced by the header-entry
pool.
