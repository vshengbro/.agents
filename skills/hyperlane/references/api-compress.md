# http-compress complete pub API

Source: `compress/src/` — auto-extracted from `pub` declarations.

Crate name: `http-compress`. Provides Brotli / Deflate / Gzip codecs.

### `xx_hash3_64::impl`

- `fn` **`get_inner`** — `pub(crate) fn get_inner(&self) -> &RawHasher<&'static [u8; DEFAULT_SECRET_LENGTH]> {...}`
- `fn` **`get_mut_inner`** — `pub(crate) fn get_mut_inner(&mut self) -> &mut RawHasher<&'static [u8; DEFAULT_SECRET_LENGTH]> {...}`

### `xx_hash3_64::struct`

- `struct` **`XxHash3_64`** — `pub struct XxHash3_64 {`

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
