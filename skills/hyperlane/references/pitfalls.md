# hyperlane 框架踩坑表(consolidated index)

> **本文件是索引** — 每个坑的详细 repro / 修复 / 不该做的事放在各自 reference 文档中。

## 22 个核心坑(原 hyperlane-standards §10)

> 维护:这些是 hyperlane 框架反复踩过的坑,任何 hyperlane PR 提交前**逐条对照**。

| # | 坑 | 详细 |
|---|---|---|
| 1 | 路由注册是 **async**:`server.route::<T>(path).await` — 不能链式 `.route().route()` | `references/hyperlane-macros-route-params.md` |
| 2 | response setter 是 **sync**:`ctx.get_mut_response().set_xxx()` — 不要 `.await` | `references/response.md` |
| 3 | `ServerControlHook` 有 `Default`,用 `unwrap_or_default()` 不要 `expect()` | `references/run.md` |
| 4 | 不要自己 `use Stream`;框架 `Stream` 类型与 `tokio::net::TcpStream` 是两个不同类型 | `references/stream.md` |
| 5 | **`inventory::collect!` 框架调用**:不要在自己代码里再 `collect!` 一遍(重复注册 panic) | `references/hyperlane-macros-hyperlane-init.md` |
| 6 | `#[route]` / `#[hyperlane]` / `#[task_panic]` 来自 `hyperlane-macros`,不是 `hyperlane`;`use hyperlane_macros::*;` | `references/hyperlane-macros-attributes.md` |
| 7 | `Server` 必须 `let mut`(所有注册方法都 `&mut self`)| `references/run.md` |
| 8 | `Status::Continue` vs `Status::Next` 区别:继续走下一个 hook vs 跳到下一阶段 | `api-core.md` §ServerHook |
| 9 | `hook` 函数签名是 `async fn handle(self, ...)`:拿 `self` 而非 `&self`(per-request instance) | `api-core.md` §hook trait |
| 10 | `new()` 钩子也拿 `&mut Stream, &mut Context`:可在 `new` 里做请求级初始化(轻量) | `api-core.md` §hook |
| 11 | `RouteParams` 是 `HashMap<String, String>`:字符串拥有权 — 修改前 `clone()` | `references/hyperlane-macros-route-params.md` |
| 12 | dynamic segment 必须 `{name}` 包裹,**不能** `/users/:id` | `references/hyperlane-macros-route-params.md` |
| 13 | regex segment `{name:pattern}` 写法;**注意 Rust string literal 双反斜杠** `/users/{id:\\d+}` | `references/hyperlane-macros-route-params.md` |
| 14 | response body `set_body` 接收 `Into<Vec<u8>>` — `&str` 也行,内部 `.into()` | `references/response.md` |
| 15 | `build()` 返回 `Vec<u8>`(这个值通常 `let _ = ...;` 丢掉,setter 已经写 body) | `references/send.md` |
| 16 | `server_config()` / `request_config()` 是 **sync**:不要 `.await` | `references/run.md` |
| 17 | `config_from_json` 是 sync,接收 `impl AsRef<str>` | `references/run.md` |
| 18 | Tokio runtime 自己起:`#[tokio::main] async fn main() { ... }` — 框架不自动起 | `references/run.md` |
| 19 | 每个 hook 的 `new()` **每次请求都执行**:**不要**在 `new` 里放 expensive IO,放 `handle` 里 | `references/hyperlane-macros-method-filter.md` |
| 20 | panics 在 `handle` 里会被 `TaskPanic` hook 捕获;**不要**在 `handle` 里 `catch_unwind` | `references/hyperlane-macros-send-flush.md` |
| 21 | 404 / 405 默认走 `RequestError` hook;未注册时框架内置 default(返回空 404 body) | `references/hyperlane-macros-request.md` |
| 22 | `panic = "unwind"`:`TaskPanic` hook 才能拿到 panic;`panic = "abort"` 直接 abort 不触发 | `references/hyperlane-macros-attributes.md` |

## monorepo / 工具链相关

| # | 坑 | 详细 |
|---|---|---|
| 23 | `hyperlane-cli` 只有 `watch / new / template / help / version`;**不要**找 `hyperlane fmt` | `references/api-cli.md` |
| 24 | `bump / sync / fmt / publish` 在外部 `crate-cli`(`~/.cargo/bin/crate`),不是 `hyperlane-cli` | `references/release-bump-flow.md` |
| 25 | bump commit 只改根 `Cargo.toml`,**不要**对 7 个 sub-crate 做任何 sed | `references/release-bump-flow.md` |
| 26 | CI `sync_workspace_version` 在 master push 上自动补齐 sub-crate `Cargo.toml` | `references/release-bump-flow.md` |
| 27 | publish 顺序: `http-constant → http-compress → http-type → http-request → hyperlane-core → hyperlane-macros → hyperlane-cli`(拓扑序;`http-type` 依赖 constant+compress,`hyperlane-macros` 硬依赖 core,**不能**把 type/macros 提前)| `references/release-bump-flow.md` |
| 28 | monorepo 切换:旧版 21.3.x 单仓无 path-dep;新版 21.7.x monorepo 必须 path-dep | 原 hyperlane-standards 迁移清单(已移除) |
| 29 | `readme = "../../README.md"` 拒绝陷阱:子 crate 写错路径会让 crates.io publish 失败 | `references/release-bump-flow.md` |
| 30 | `http-request` 客户端不能用 `use super::parser::*` 跨 crate 模块;**用绝对路径** `crate::request::parser::fn::split_*`(parser 子模块的文件是 `fn.rs`,不是 `wire.rs`) | `api-request.md` |

## 工具冲突 quick map

| 工具 | 提供 | 不提供 |
|---|---|---|
| `hyperlane-cli` | `watch / new / template / help / version` | `bump / sync / fmt / publish` |
| `crate-cli`(`~/.cargo/bin/crate`)| `bump / sync / fmt / publish` | server 启动 / template 生成 |
| `cargo fmt` | impl 代码 | (没有 hyperlane-specific 宏重排) |

## 关键词速查

- **hook 不触发** → 坑 #5(`inventory::collect!` 重复)、坑 #6(use 路径错)
- **panic 不被捕获** → 坑 #20(catch_unwind 重复)、坑 #22(`panic = "abort"`)
- **404 default** → 坑 #21(`RequestError` hook 未注册)
- **build / publish fail** → 坑 #24(用错工具)、坑 #25(bump sed 错文件)、坑 #27(发布顺序)
- **路由不匹配** → 坑 #11(RouteParams 拥有权)、坑 #12(/users/:id 错)、坑 #13(正则双反斜杠)


## async-stripe 0.41 的 Event schema 比 Stripe 现网旧 —— 验签要用自己写的 HMAC

`Webhook::construct_event` 先验 HMAC 再反序列化。实测它对 Stripe 现网投递的真事件报:

```
BadParse(Error("unknown variant `hosted_page`, expected `embedded` or `hosted`", line: 139))
```

也就是 **签名是对的,炸在解析**。Checkout Session 的 `ui_mode` 已经是 `hosted_page`,而这个版本的 enum 只有 `embedded` / `hosted`。任何走 `async-stripe::Event` 的代码在当前 Stripe 上都会收不到钱。

本项目的处理:只用 `Webhook::construct_event` 里的 HMAC 思路,**自己验签**,再只用 `serde_json::Value` 取 `id` / `type`,metadata 本来就从原始 payload 读。这样既过了签名关,又不受 stale schema 约束。**注意**:`VerifiedEvent` 只能在验签通过后产生,不能为了绕过解析就信任未验签的 body。

### 两个反直觉的密钥事实

1. `HD_STRIPE_WEBHOOK_SECRET` 的值(`whsec_hJPIjDnVZDhZG5PoNSm4s7Ehith8nSNe`)**不是十六进制**,`hex::decode` 会失败。当成原始字节做 HMAC key,**`whsec_` 前缀要留着**。
2. 验签必须对 **raw body 字节**做,不能先 parse 再重新序列化 —— 重新格式化过的 JSON 算出的 HMAC 必然不同。

### 手写 HMAC-SHA256 时的两个坑

- RFC 2104 的外层 `SHA256(opad || inner_digest)` **必须再哈希一次**。我漏了这步、直接 append 后 `truncate(32)`,结果返回的是一串 `0x5c` 外层填充。**写完立刻用 RFC 4231 向量验**:case1 key 是 20 字节 `0x0b`(不是 1 字节),case2 key 是 `"Jefe"`,case6 是 131 字节 `0xaa` 配超长消息。
- 比较摘要要走 `constant_time_eq`(逐字节 XOR 累积),不要用 `==` 早退。

### 这个仓库里 sha2 有两个版本

`hyperlane-utils` 拉 `sha2 0.11`,`async-stripe` 要 `sha2 0.10`,而 `hmac 0.12` 的 `Mac` trait **不跨这两个版本统一**。症状是 `no method named update found for struct CoreWrapper<T>`。所以本项目不依赖 `hmac` 的 `Mac` trait,自己按 RFC 2104 算,只借用 `sha2::Sha256::digest`。**在同一个 HMAC 里混用两版 sha2 一定编译不过**,别浪费时间试。

## 写这类测试的教训:不要手拼转义

我花了几轮在 `r##"{"id":"x"}"##` 这种 raw string 上翻车 —— raw string 里的 `"` 是**字面反斜杠加引号**,于是我算 HMAC 用的字节和 Rust 实际发出的字节不一致,签名永远对不上,而且报错是 `BadSignature`,极具误导性。

**正确做法**:真实事件放 fixture 文件,测试里用 `include_str!` 读,HMAC 用 Python/JS 现算好再写死进测试。改 fixture 后**必须**确认字节没变(我这次是 `cmp` + 比对 sha256)。同理,时间戳要现算 —— 写死的 `const TIMESTAMP` 会随时间漂移,一旦超过 300 秒容差就开始假失败,而报错同样只会说 `BadSignature`。

**通用判据**:验签类测试失败时,先把「我算的输入」和「程序实际收到的字节」逐字节比一遍,再怀疑算法。我这次连着三次都在自己的 fixture 上错,而不是在 Stripe 或 async-stripe 上错。
