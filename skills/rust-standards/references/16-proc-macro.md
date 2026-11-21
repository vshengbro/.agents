# 16. 过程宏 crate 专属约定(仅 proc-macro crate 适用)

过程宏 crate(`proc-macro = true`)有别于普通 lib crate,需遵守以下额外约束。

## 16.1 lib.rs 是所有宏的注册入口

- 文件开头使用 `//! Crate name //! Description` 顶层 doc comment
- 紧接着 `mod helper;` 列出所有 helper 子模块(**子模块名是普通 snake_case**,不带 `r#`)
- 然后 `use { closed::*, ... };`(`{}` 内**不带 `r#`** 因为子模块不是关键字)一次性把 helper glob 进 `lib.rs`
- 之后才是 `use proc_macro::TokenStream;` 等外部依赖
- 所有 `#[proc_macro_attribute] pub fn attr_macro(...) -> TokenStream { ... }` **必须** 在 `lib.rs` 中实现,**不允许拆到子模块**

## 16.2 helper 子模块的 mod.rs

同样遵守普通 lib crate 的 `mod r#xxx;` + `pub use`/`pub(crate) use` + `use super::*;` 三段式(参见 references/06-module-imports.md)。

## 16.3 依赖方向(避免循环)

- 过程宏 crate 可以依赖对应的 lib crate(`proc-macro = ...` 依赖 `lib-crate = "..."`)
- 反过来 lib crate **不能** 依赖 proc-macro

## 16.4 测试

过程宏 crate 通常不写 `tests/`(因为宏测试通常放在使用宏的 lib crate 的 `tests/` 里做集成测试,或作为宏的 README 示例代码)。

## 16.5 宏体内的路径必须写完整命名空间(user 钦定)

宏体持有的 token 是在**使用该宏的 crate** 里展开的,不是在定义宏的 crate 里展开的。由此产生两条后果:

- 宏体发出的 `use` 会落在**消费者的作用域**里 —— 它可能与消费者自己的 import 冲突,并且它依赖的是消费者的依赖集而不是宏作者的依赖集;
- 宏体里用裸名写的路径,在消费者的作用域里解析 —— 它指向消费者恰好拥有的东西,而宏作者无从知道。

所以 `quote!` 宏体必须:

- **不发出任何 `use`**;
- **把每个 crate 都写完整**:`::hyperlane::Status::Continue`,而不是 `hyperlane::Status::Continue`。

```rust
// ❌ 违规:import 落在消费者的作用域里
quote! { use hyperlane::Status; }

// ❌ 违规:路径在消费者的作用域里解析
quote! { hyperlane::Status::Continue }

// ✅ 正确:绝对路径,指向宏作者指定的那个 crate
quote! { ::hyperlane::Status::Continue }
```

**豁免**:

- `macro_rules!` 宏体 —— 它在**定义它的 crate** 里展开,那是那个 crate 自己的代码,它的 import 与路径都在那里解析;
- `crate::` / `self::` / `super::` 路径 —— 它们指名定义 crate 自己的模块树,永远正确;
- 插值(`#input_struct`)—— 那是宏自己的局部绑定,不是 crate 路径。

**验证脚本** `scripts/verify_no_macro_use.py`(audit check 55 + `staged_file_gate.py` 已注册):

```bash
python3 <path>/verify_no_macro_use.py <repo_root>
```

自测 `python3 <path>/self_test_no_macro_use.py` 双向断言(合规树 0 命中 / 违规树精确命中)+ 两项变异验证(把 `use` 禁令或宏体识别关掉,违规用例必须不再被报出 —— 证明规则真的在跑)。真仓实测:hyperlane 0 / euv 0。

**实现要点(踩过的坑)**:宏体边界必须按**列**切,不能按行切 —— `let x: proc_macro2::TokenStream = quote! { ... }` 里类型在 `quote!` **之前**、同一行,按行切会把它误吞进宏体;插值 `#name` 后面紧跟的 `::` 不能当成 crate 路径;Rust 关键字(`use`、`crate`、`self` 等)不是 crate 名。
