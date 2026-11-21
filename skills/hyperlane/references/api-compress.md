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
- `fn` **`from`** — `pub fn from(header: &HashMap<String, String, BuildHasherDefault<XxHash3_64>>) -> Self {...}`
- `fn` **`decode`** — `pub fn decode<'a>(&self, data: &'a [u8], buffer_size: usize) -> Cow<'a, [u8]> {...}`
- `fn` **`encode`** — `pub fn encode<'a>(&self, data: &'a [u8], buffer_size: usize) -> Cow<'a, [u8]> {...}`

### `deflate::fn`

- `fn` **`encode`** — `pub fn encode(data: &'_ [u8], buffer_size: usize) -> Cow<'_, [u8]> {...}`
- `fn` **`decode`** — `pub fn decode(data: &'_ [u8], buffer_size: usize) -> Cow<'_, [u8]> {...}`

### `gzip::fn`

- `fn` **`encode`** — `pub fn encode(data: &'_ [u8], buffer_size: usize) -> Cow<'_, [u8]> {...}`
- `fn` **`decode`** — `pub fn decode(data: &'_ [u8], buffer_size: usize) -> Cow<'_, [u8]> {...}`
