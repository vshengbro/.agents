# http-compress complete pub API

Source: `compress/src/` — auto-extracted from `pub` declarations.

Crate name: `http-compress`. Provides Brotli / Deflate / Gzip codecs.

### `xx_hash3_64::const`

- `const` **`HASH_PREFIX_CAPACITY`** — `pub(crate) const HASH_PREFIX_CAPACITY: usize = 128;`

### `xx_hash3_64::struct`

- `struct` **`XxHash3_64`** — `pub struct XxHash3_64 {`

`XxHash3_64` keeps the hash secret on the stack. Since the hot-path work it
now holds an `Option<RawHasher<...>>` streaming state (initialized only when
an input outgrows the short prefix) plus a `HASH_PREFIX_CAPACITY` (128 byte)
`MaybeUninit` prefix buffer and its initialized length. The struct is
`Clone`; the clone copies only the initialized prefix bytes.

### `brotli::fn`

- `fn` **`encode`** — `pub fn encode(data: &'_ [u8], buffer_size: usize) -> Cow<'_, [u8]> {...}`
- `fn` **`decode`** — `pub fn decode(data: &'_ [u8], buffer_size: usize) -> Cow<'_, [u8]> {...}`

### `compress::enum`

- `enum` **`Compress`** — `pub enum Compress {`

### `compress::impl`

- `fn` **`is_unknown`** — `pub fn is_unknown(&self) -> bool {...}`
- `fn` **`as_str`** — `pub fn as_str(&self) -> &'static str {...}`
- `fn` **`from`** — `pub fn from(header: &HashMap<String, String, BuildHasherDefault<XxHash3_64>>) -> Self {...}`
- `fn` **`from_accept_encoding`** — `pub fn from_accept_encoding<H>(header: H) -> Option<Self> where H: AsRef<str> {...}`
- `fn` **`decode`** — `pub fn decode<'a>(&self, data: &'a [u8], buffer_size: usize) -> Cow<'a, [u8]> {...}`
- `fn` **`encode`** — `pub fn encode<'a>(&self, data: &'a [u8], buffer_size: usize) -> Cow<'a, [u8]> {...}`

### `deflate::fn`

- `fn` **`encode`** — `pub fn encode(data: &'_ [u8], buffer_size: usize) -> Cow<'_, [u8]> {...}`
- `fn` **`decode`** — `pub fn decode(data: &'_ [u8], buffer_size: usize) -> Cow<'_, [u8]> {...}`

### `gzip::fn`

- `fn` **`encode`** — `pub fn encode(data: &'_ [u8], buffer_size: usize) -> Cow<'_, [u8]> {...}`
- `fn` **`decode`** — `pub fn decode(data: &'_ [u8], buffer_size: usize) -> Cow<'_, [u8]> {...}`

## Accept-Encoding negotiation

`Compress::as_str` renders the coding as its `Content-Encoding` field token —
`gzip`, `deflate`, `br`, and the empty string for `Compress::Unknown`. It is
the token to write on a response, and `Display` now delegates to it.

`Compress::from_accept_encoding` picks the best coding **this crate
implements** out of one `Accept-Encoding` field value. It is generic over
`H: AsRef<str>`, parses without allocating, and returns `None` when the client
accepts none of the three codings. Locked by the tests in
`compress/tests/compress/fn.rs`:

| Rule | Behaviour |
|---|---|
| Quality order | `gzip;q=0.5, br` → `br`; `br;q=0.5, gzip` → `gzip`; the highest `q` wins |
| Absent quality | counts as `1.0` (`DEFAULT_QUALITY`) |
| Tie-break | equal qualities resolve toward the smaller output: `br` > `gzip` > `deflate`, whatever order the field lists them in |
| `q=0` | refuses the coding outright (`br;q=0` → `None`; `br;q=0, gzip` → `gzip`) |
| `*` | stands for every supported coding the field does not name, at the quality the `*` carries (`*` → `br`; `gzip, *;q=0` → `gzip`; `*;q=0` → `None`) |
| Unknown codings | ignored — `zstd`, `identity` and a coding the crate does not implement never win |
| Case | the coding name and the parameter name are matched case-insensitively (`BR;Q=1.0` → `br`) |
| Whitespace | trimmed around the coding, the parameter name and the value (`"  gzip ; q = 0.9  "` → `gzip`) |
| Unknown parameters | ignored (`gzip;version=2` → `gzip`), so a parameter list may hold more than `q` |
| Bad quality | a `q` that is absent, non-numeric, or outside `0.0..=1.0` refuses that **entry**, not the whole field (`gzip;q=1.5` → `None`; `gzip;q=2, br;q=0.5` → `br`) |
| Empty field | `""`, `"   "`, `","` and `";;"` → `None` |

`Compress::from` is the older direction: it reads a `Content-Encoding`
response header map and returns the coding to decode with. Negotiation and
decoding are separate APIs — do not use `from` to answer a client.
