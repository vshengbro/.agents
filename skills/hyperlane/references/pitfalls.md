# hyperlane pitfall table (consolidated index)

> **This file is an index.** The detailed repro, the fix and the thing not to do
> for each pitfall live in the reference document named in its row.

## The 22 core pitfalls (from hyperlane-standards §10)

> These are pitfalls the hyperlane framework has hit repeatedly. Check every one
> of them before opening a hyperlane pull request.

| # | Pitfall | Detail |
|---|---|---|
| 1 | Route registration is **sync**: `server.route::<T>(path)` returns `&mut Self` — it **can** be chained as `.route().route()`; **do not** add `.await` | `references/hyperlane-macros-route-params.md` |
| 2 | A response setter is **sync**: `ctx.get_mut_response().set_xxx()` — do not `.await` | `references/response.md` |
| 3 | `ServerControlHook` has a `Default`, so use `unwrap_or_default()` instead of `expect()` | `references/run.md` |
| 4 | Do not `use Stream` yourself; the framework's `Stream` and `tokio::net::TcpStream` are two different types | `references/stream.md` |
| 5 | **`inventory::collect!` is the framework's call**: do not `collect!` again in your own code (a duplicate registration panics) | `references/hyperlane-macros-hyperlane-init.md` |
| 6 | `#[route]` / `#[hyperlane]` / `#[task_panic]` come from `hyperlane-macros`, not `hyperlane`; `use hyperlane_macros::*;` | `references/hyperlane-macros-attributes.md` |
| 7 | `Server` must be `let mut` (every registration method takes `&mut self`) | `references/run.md` |
| 8 | `Status` has exactly two variants: `Continue` (carry on to the next hook) and `Reject` (stop the pipeline and abort the connection lifecycle); there is **no** `Status::Next` | `api-core.md` §ServerHook |
| 9 | The hook signature is `async fn handle(self, ...)`: it takes `self`, not `&self` (a per-request instance) | `api-core.md` §hook trait |
| 10 | The `new()` hook also takes `&mut Stream, &mut Context`: request-level setup belongs here (keep it light) | `api-core.md` §hook |
| 11 | `RouteParams` is `HashMap<String, String>`: the strings are owned — `clone()` before modifying | `references/hyperlane-macros-route-params.md` |
| 12 | A dynamic segment must be wrapped in `{name}`; `/users/:id` **does not work** | `references/hyperlane-macros-route-params.md` |
| 13 | A regex segment is written `{name:pattern}`; **note the doubled backslash** in the Rust string literal: `/users/{id:\\d+}` | `references/hyperlane-macros-route-params.md` |
| 14 | The response body's `set_body` takes `Into<Vec<u8>>` — a `&str` works too, it is converted internally | `references/response.md` |
| 15 | `build()` returns `Vec<u8>`, and **that is the response bytes to send** — dropping it means no response was sent (see `try_send(ctx.get_mut_response().build())` in `performance/src/bin/server/main.rs`) | `references/send.md` |
| 16 | `server_config()` / `request_config()` are **sync**: do not `.await` | `references/run.md` |
| 17 | `config_from_json` is sync and takes `impl AsRef<str>` | `references/run.md` |
| 18 | Start the Tokio runtime yourself: `#[tokio::main] async fn main() { ... }` — the framework does not start one | `references/run.md` |
| 19 | A hook's `new()` runs **on every request**: **do not** put expensive IO there, put it in `handle` | `references/hyperlane-macros-method-filter.md` |
| 20 | A panic in `handle` is caught by the `TaskPanic` hook; **do not** `catch_unwind` inside `handle` yourself | `references/hyperlane-macros-send-flush.md` |
| 21 | A 404 / 405 goes to the `RequestError` hook by default; with no hook registered the framework uses its built-in default (an empty 404 body) | `references/hyperlane-macros-request.md` |
| 22 | `panic = "unwind"`: only then can the `TaskPanic` hook see the panic; `panic = "abort"` aborts without triggering it | `references/hyperlane-macros-attributes.md` |

## Monorepo and toolchain

| # | Pitfall | Detail |
|---|---|---|
| 23 | `hyperlane-cli` has only `watch / new / template / help / version`; **do not** look for `hyperlane fmt` | `references/api-cli.md` |
| 24 | `bump / sync / fmt / publish` live in the external `crate-cli` (`~/.cargo/bin/crate`), not in `hyperlane-cli` | `references/release-bump-flow.md` |
| 25 | A bump commit touches only the root `Cargo.toml`; **do not** sed any of the 11 workspace members | `references/release-bump-flow.md` |
| 26 | The CI `publish` job runs `crate sync` + `crate fmt` to bring the member versions in line; there is **no** separate `sync_workspace_version` job | `references/release-bump-flow.md` |
| 27 | Publish order: `http-compress → http-constant → http-type → http-request → hyperlane-core → hyperlane-macros → hyperlane-cli → hyperlane → hyperlane-plugin-logger → hyperlane-plugin-websocket → hyperlane-performance` (measured from the crates.io 22.1.0 publish timestamps; `http-type` depends on constant+compress; `hyperlane-macros` does **not** depend on core — its path-only dev-dep on the root crate imposes no ordering constraint; both plugin crates depend on the `hyperlane` facade, so both publish after it) | `references/release-bump-flow.md` |
| 28 | The monorepo switch: the old 21.3.x single-crate layout had no path-deps; the 21.7.x+ monorepo requires them | the old hyperlane-standards migration list (removed) |
| 29 | The `readme = "../../README.md"` trap: a wrong path in a member crate makes the crates.io publish fail | `references/release-bump-flow.md` |
| 30 | The `http-request` parser helpers are `pub(crate)` and **invisible outside the crate** (E0603); `crate::request::parser::fn::split_*` does **not** compile either (the `parser` module is private and `fn` is a keyword). The only usable path is the crate-internal re-export `crate::request::split_*`; the file is `fn.rs`, not `wire.rs` | `api-request.md` |

## The plugin and bench pitfalls (verified 2026-10-23)

| # | Pitfall | Detail |
|---|---|---|
| 31 | **Hook priority runs the smaller value first**: the framework sorts with `sort_by_key(try_get_order())` over an `Option<isize>` (in `macros/src/hyperlane/fn.rs`), so `None` comes before every `Some`. The 21.14.0 docs said higher values execute first; **22.0.2 corrected that to the smaller value running earlier**, and 22.1.0 still does it that way | `references/plugins.md` |
| 32 | **A negative integer literal is swallowed**: `#[response_middleware(-110)]` compiles to `None`, not `Some(-110)` — `expr_to_isize` accepts integer and string literals only, and `-110` is a unary expression. A negative priority has to be written as the string `"-110"`. The `hyperlane-plugin-logger` request hook still writes `#[hyperlane::request_middleware(-120)]`, so **it registers with no order at all** and runs before every ordered hook | `references/plugins.md` |
| 33 | `assert_unique_order` panics only for the **same hook type with the same order** (it compares the factory function pointer); two **different** hook types sharing a number do not panic | `references/plugins.md` |
| 34 | Only **two** plugin crates are in the tree, and both are published: `hyperlane-plugin-logger` and `hyperlane-plugin-websocket` carry `publish = true` and are on crates.io at `22.1.0`. The other four (`-compression`, `-cors`, `-shutdown`, `-static-files`) left the tree and stay on crates.io at their last version, `22.0.6` | `references/plugins.md` |
| 35 | An unconfigured plugin **must** pass the request through: the hook reads its own `OnceLock` first and returns `Status::Continue` when it is `None`, otherwise every application that does not use the plugin changes behaviour | `references/plugins.md` |
| 36 | The harness is the crate `hyperlane-performance`, a **member of the root workspace**, not a separate one: a root `cargo test --workspace` builds and tests it, and there is no second `Cargo.lock` | `references/bench.md` |
| 37 | The harness crate is `publish = true` and is published as `hyperlane-performance`; it produces four binaries (`hyperlane-performance`, `-server`, `-loadgen`, `-control`) from one package | `references/bench.md` |
| 38 | A perf verdict **never blocks the build**: the Rust report renderer exits non-zero only when the measurement itself is broken (no measurements, the two variants were not measured together, or no repeat produced a usable pair) | `references/bench.md` |
| 39 | `hyperlane-macros` has **two version lines** on crates.io: `21.x`/`22.x` is the current monorepo line, while `23.0.21` is the old single-crate line (it needs `hyperlane ^21.3.6` + `syn ^2.0.119`, while the current workspace uses `syn 3.0.6`, so the two are **incompatible**). `23.0.21` is the highest number on the registry, so a plain `cargo add hyperlane-macros` resolves to it | `references/api-macros.md` |
| 40 | The multipart parsing of `http-type` (`MultipartFormData` / `BodyPart`) **shipped with 21.14.0**; it is not local-tree only — `http-type` 21.14.0, 22.0.6 and 22.1.0 on crates.io all contain `src/body/` (verified by unpacking the `.crate` files) | `references/api-type.md` |
| 41 | The `Transport` trait is public, but the framework's `Stream` **does not implement it** — `tokio::net::TcpStream` does | `references/api-type.md` |

## Tool conflict quick map

| Tool | Provides | Does not provide |
|---|---|---|
| `hyperlane-cli` | `watch / new / template / help / version` | `bump / sync / fmt / publish` |
| `crate-cli` (`~/.cargo/bin/crate`) | `bump / sync / fmt / publish` | starting a server / generating a template |
| `cargo fmt` | impl code | (no hyperlane-specific macro reordering) |

## Keyword quick reference

- **a hook does not fire** → pitfall #5 (a duplicate `inventory::collect!`), pitfall #6 (wrong `use` path)
- **a panic is not caught** → pitfall #20 (a duplicate `catch_unwind`), pitfall #22 (`panic = "abort"`)
- **the 404 default** → pitfall #21 (no `RequestError` hook registered)
- **build / publish fails** → pitfall #24 (the wrong tool), pitfall #25 (sed on the wrong file), pitfall #27 (the publish order)
- **a route does not match** → pitfall #11 (RouteParams ownership), pitfall #12 (a wrong `/users/:id`), pitfall #13 (a doubled backslash in a regex)
- **the hook order is wrong** → pitfall #31 (the smaller value runs first), pitfall #32 (a negative literal is swallowed), pitfall #33 (uniqueness is only checked per hook type)
- **a plugin does nothing / affects others** → pitfall #34 (not published, path dependency only), pitfall #35 (an unconfigured plugin must pass through)
- **the bench does not run / the verdict is untrustworthy** → pitfall #36 (a separate workspace), pitfall #38 (the verdict never blocks the build)


## The async-stripe 0.41 Event schema is older than live Stripe — verify the signature with your own HMAC

`Webhook::construct_event` verifies the HMAC first and deserializes second. Against a
real event delivered by live Stripe it reports:

```
BadParse(Error("unknown variant `hosted_page`, expected `embedded` or `hosted`", line: 139))
```

So **the signature is valid and the parse is what blows up**. A Checkout Session's
`ui_mode` is already `hosted_page`, while this version's enum only has `embedded` /
`hosted`. Any code going through `async-stripe::Event` therefore receives nothing on
current Stripe.

The project's handling: take only the HMAC idea from `Webhook::construct_event`,
**verify the signature yourself**, and then read `id` / `type` with
`serde_json::Value` alone — the metadata was read from the raw payload anyway. That
clears the signature gate without being bound by the stale schema. **Note**: a
`VerifiedEvent` may only be produced after the signature passes; never trust an
unverified body in order to get past the parse.

### Two counterintuitive facts about the key

1. The value of `HD_STRIPE_WEBHOOK_SECRET` (`whsec_[REDACTED]`) **is not hex**, so
   `hex::decode` fails on it. Use the raw bytes as the HMAC key and **keep the
   `whsec_` prefix**.
2. Verification must run over the **raw body bytes**. Parsing first and
   re-serializing produces a different HMAC, always.

### Two pitfalls when hand-rolling HMAC-SHA256

- The outer `SHA256(opad || inner_digest)` of RFC 2104 **must be hashed once more**.
  Skipping that step and appending before `truncate(32)` returns a string of the
  `0x5c` outer padding. **Verify against the RFC 4231 vectors as soon as you write
  it**: case 1's key is 20 bytes of `0x0b` (not 1 byte), case 2's key is `"Jefe"`,
  and case 6 is 131 bytes of `0xaa` with an over-long message.
- Compare digests with `constant_time_eq` (accumulate a byte-wise XOR); do not use
  `==`, which returns early.

### Two versions of sha2 in this repository

`hyperlane-utils` pulls `sha2 0.11` while `async-stripe` wants `sha2 0.10`, and
`hmac 0.12`'s `Mac` trait **does not unify across the two**. The symptom is
`no method named update found for struct CoreWrapper<T>`. So this project does not
depend on the `Mac` trait from `hmac`: it computes RFC 2104 itself and borrows only
`sha2::Sha256::digest`. **Mixing two versions of sha2 inside one HMAC never
compiles** — do not waste time trying.

## Lesson from writing these tests: never hand-roll the escaping

I lost several rounds to a raw string like `r##"{"id":"x"}"##` — the `"` inside a
raw string is a **literal backslash followed by a quote**, so the bytes I hashed
were not the bytes Rust actually sent, the signature never matched, and the error
was `BadSignature`, which is deeply misleading.

**The right way**: put the real event in a fixture file, read it with
`include_str!` in the test, and compute the HMAC with Python/JS and hard-code the
result. After changing a fixture you **must** confirm the bytes did not change (I
used `cmp` plus a sha256 comparison). The same applies to timestamps — compute them
at run time. A hard-coded `const TIMESTAMP` drifts, and once it passes the
300-second tolerance the test starts failing for the wrong reason, again reported
only as `BadSignature`.

**The general rule**: when a signature-verification test fails, compare "the input I
hashed" with "the bytes the program actually received" byte by byte before
suspecting the algorithm. All three of my failures were in my own fixture, not in
Stripe or async-stripe.


## Credentials belong only in an env file, and prove the service starts from that file alone

Load `resources/env/dev/server.env` when starting the hyperlane service with
`set -a && . ./resources/env/dev/server.env && set +a`, and do not repeat
`KEY=...` on the command line (it lands in the shell history). Do not verify by
checking that the variable exists; verify like this:

```bash
set -a && . ./resources/env/dev/server.env && set +a && unset DATABASE_URL
<binary>
curl -s localhost:9099/api/health
ps eww -p <pid> | grep -c HD_STRIPE   # confirm the process really got it
```

That `ps eww` step is the key part: it proves **the file's values reached the
process**, rather than being passed in by hand. The `unset DATABASE_URL` alongside
it proves the application is not quietly depending on some external injection.

Three companions:
- file permission `chmod 600`
- `.gitignore` needs `resources/env/*/server.env` plus `!resources/env/*/server.env.example`, and `git ls-files resources/env/` must show only `.example`
- generate the template from the real file: replace the value of `KEY|SECRET|PASSWORD|TOKEN|DATABASE_URL` with `<set this in your own copy>`, then diff the two **key names** (not the values) to confirm the structure matches

## `#[cfg(test)]` is not safety — do not put test constants in tracked source

Marking a fixture constant `#[cfg(test)]` only keeps it out of the release binary;
**the file is still tracked by git**, so its value travels with the repository.
Putting a real webhook secret in `application/controller/billing/const.rs` leaks it
exactly that way.

The right way: use a **synthetic value** for the HMAC key in tests
(`whsec_fixture_key_for_unit_tests_only`). As long as it signs the same bytes
stably, the coverage is identical — HMAC verifies "were the bytes changed", not
"is this key the real one". Then redact the real identifiers in the fixture (event
id / account id / payment_intent / email), but **keep the field that triggered the
bug** (for example `ui_mode: "hosted_page"`).

Before committing, run a pattern scan over the staged diff for secret, restricted
key, and event/account/pi/cs id: all of them must be 0.

## Dynamic route segments use `{name}`, never `[name]` (§ recorded 2026-10-13)

A bracket segment is NOT a placeholder. `#[route("/api/admin/keys/[id]")]` registers a
**literal** `[id]` path segment, compiles cleanly, shows up in the route table, and then
never matches any real request.

The symptom is unusually quiet: the request falls through to the SPA catch-all, which
answers `404 NOT_FOUND` with the app's own JSON envelope. So the endpoint looks like it
returns a well-formed error rather than not existing — and because the catch-all excludes
`/api/*`, it does not even serve HTML that would have hinted at a routing problem.

```rust
// wrong: matches the literal path "/api/admin/keys/[id]"
pub(crate) const API_KEY_PATH: &str = "/api/admin/keys/[id]";
// right: matches "/api/admin/keys/490" and binds `id` -> "490"
pub(crate) const API_KEY_PATH: &str = "/api/admin/keys/{id}";
```

Read the param with `ctx.try_get_route_param(ROUTE_PARAM_KEY_ID)`.

**How it was found:** a browser E2E pass clicked Revoke, the button fired, nothing happened,
and the DB column stayed NULL. Only comparing `/api/admin/keys` (200) against
`/api/admin/keys/490` (404) on the same session revealed the route never matched. Unit and
integration tests had passed because none of them asserted the route *shape*.

**Guard:** assert the pattern's shape, not just its behaviour — `API_KEY_PATH.ends_with("{id}")`
plus `!API_KEY_PATH.contains("[id]")`. Mutation-tested: reverting to brackets fails both
assertions. A behavioural test would not catch this, because the 404 comes from a
different component than the one under test.

**Related:** a route can match while another listener on the same port serves a stale
build, which looks exactly like the route is broken. Check `lsof -ti :<port>` before
concluding a route is wrong — this cost a confusing detour.
