---
name: rust-verifier-cleanup-at-scale
description: Use when zeroing rust-standards verifiers across files.
version: 1.0.0
author: curator
license: MIT
hermes:
  tags:
    - rust
    - verifiers
    - proc-macro
    - refactoring
  related_skills:
    - rust-standards
    - euv-standards
    - euv-ui-html-macro-gotchas
---

# rust-standards 违规清零 + 宏层修复

多文件批量清理 rust-standards 违规（doc-comment 格式 / 硬编码字符串 / 关键字文件纯净）
时的工作流。适用于「一批文件要全部归零」以及「验证器只是症状、根因在宏」这两类任务。

## When to Use

- 一批文件要同时清零 doc-comment / 硬编码字符串 / 关键字文件纯净违规；
- 验证器或 lint 报错，但根因在 proc-macro / DSL 解析层；
- 别人（或别的 agent）刚在同一工作树上改过你要动的文件。

**不要**用于：单文件一次性小修（直接改就行）、以及纯 PR 流程 / 版本 bump
（那是 `euv-standards` 的事）。

## 0. 先确认范围口径，别按页面名 grep

验证器是**按文件**报的，按 `page/<name>/` grep 会把同页面下**不属于你的文件**（如
`view/fn.rs`）一起算进来，导致 baseline 虚高、最后无法自证清零。

```bash
python3 ~/.agents/skills/rust-standards/scripts/verify_doc_comment_format.py . | grep -E "<你的确切文件路径正则>"
```

**baseline 必须按你真正负责的文件列表统计**，并把「同页面但不是你负责的文件」单独列出来
说明差异来源。任务描述里报的条数要用实测覆盖；实测和描述不一致时明确指出差异来源。

## 1. 共享工作树上的并发纪律

多 agent 同时改一个 repo 时，**开工前和收工前各测一次 mtime/hash**，判断你要动的文件
是否正在被别人写：

```bash
stat -f "%Sm %N" -t "%H:%M:%S" <file>; sleep 20; stat -f "%Sm %N" -t "%H:%M:%S" <file>
```

- 没在动 → 正常修。
- **正在动 → 不要动**。先重跑验证器看是不是别人已经修完了；修完就核验并跳过。

⚠️ 收尾时若发现「最后要修的文件已被别人修好」，**不要为了交差再改一遍**。
核验 + 报告「已被修复、我未改动」是正确结果。

**永远禁止**：`git add` / `commit` / `stash push` / `reset` / `checkout -- .` / `cargo fmt --all`。
`git stash` 作用域是整个工作树，会把同伴在途改动一起扫走；`cargo fmt --all` 会重写别人
正在编辑的文件。要临时存自己的东西用 `cp` 到 scratch 目录。

## 2. 字面量 → 常量：先 grep 找现成的，再建 const.rs

```bash
grep -rn --include=const.rs -E '= "值"' .          # 同值是否已有常量
ls <dir>/ && cat <dir>/mod.rs                        # const.rs 是否已存在
find <dir> -mindepth 1 -type d | wc -l               # §1.3d：有子目录则不能放代码文件
```

新建 `const.rs` 后**必须在同目录 `mod.rs` 注册**，否则不会被编译（表现为
`cannot find value ... in this scope`）：

```rust
mod r#const;
mod r#fn;
pub(crate) use {r#const::*, r#fn::*};
```

- 每条常量都要 `///` 一行文档，命名 = 目录前缀 + **角色**
  （`LIST_ERROR_ITEM_NAME_REQUIRED`），不是值本身。
- **字节一致性必须机器校验**，不要靠眼看：把 `git show HEAD:<file>` 的字符串字面量集合
  与新常量值集合求差，确认提取的每个字面量都原样存在。
- 豁免项（format 宏格式串、`class!{}`/`vars!{}` 块内字面量、`#[doc="..."]`、注释）
  不要提取，但要在报告里说明为什么留下。

## 3. 编译才是唯一验收

改完 `html!` / 宏 / 任何宏调用点，**一律重新全量编译**，不要只看你改的那几行。

```bash
touch macros/src/<file>.rs                      # 强制重编，排除缓存
cargo check --workspace --all-features --offline
cargo test --workspace --all-features --offline
```

`touch` 很重要：workspace 有其他 crate 编译失败时，你改的文件可能**根本没被编译**，
却显示「绿」。

## 4. 根因在宏时：先判断「设计」还是「bug」

验证器/警告逼着调用方做额外操作（加花括号、加 `#[allow]`）才能通过时，先分清：

- **症状修法** —— 在宏里把包裹用的 block 剥掉，lint 消失，但歧义还在，调用方依旧要写
  那圈花括号。错误的抽象层，user 会打回。
- **设计修法** —— 改宏的解析规则，让自然写法原生合法，调用方零负担。

**判据：修复让 lint 消失、却没让调用方变简单，就是治标。**
user 明确说过「只有动态的才需要花括号」这类设计意图时，以设计为准，别去满足症状。

**用户会直接问「为什么不能改 X 让它本来就该这样」。** 这句话出现的信号是：你选了
症状层修法。正确反应不是把症状修法做得更精巧，而是回到解析层改规则。
遇到「但去掉这个写法会报错」时，先假设那是宏的 bug 而不是用法约束——本例就是
任务 SPEC 把一个宏 bug 写成了硬规则，导致后续 agent 照着错误规则继续写绕行代码。
改完后回头搜 SPEC / RULES / 持久化 skill，把那条「规则」改回自然写法 + 历史注记。

## 5. DSL 解析歧义：在解析层消歧，不要让调用方绕

`KEY: VALUE` 后紧跟 `{ .. }` 时，通用解析器会把 `IDENT { .. }` 当 **struct literal**，
错误报在**子节点内部**（`expected ,` / `expected struct, found local variable`），
看着像子节点写错，实际是值的边界没切开。

正确修法：`fork()` 一份 buffer，peek 花括号内部 —— 真 struct literal 必须以字段初始化
（`ident :`）开头，子节点表达式永远不会，所以判定成立。只取标识符、**不动原 buffer 位置**。

```rust
if content.peek(Ident) && content.peek2(Brace) {
    let forked: ParseBuffer<'_> = content.fork();
    let _probe: Ident = forked.parse()?;
    let inner: ParseBuffer<'_>;
    braced!(inner in forked);
    let is_struct_literal: bool = inner.peek(Ident) && inner.peek2(Colon);
    if !is_struct_literal { /* 取 bare ident，child 留给调用方继续解析 */ }
}
```

### 三个必踩的坑

1. **先 grep 找现成 helper 复用。** 同样形态的消歧通常已为 `if` 条件 / `match` scrutinee
   / `for` iterable 实现过（这类 helper 常叫 `strip_braces_from_expr` /
   `parse_expr_until_brace`）。另写一份近似实现是重复，且漏掉已修好的位置。
2. **别把「读到顶层 brace 为止」的 helper 挪到 attribute 位置。** 它在 `if cond { body }`
   里成立（body 的 brace 就是定界符），但在 attribute 列表里会越界 —— `class: c_foo()` 的
   右括号不是 brace，helper 会继续吞掉后续 token，**全仓炸出上百处错误**。改完立刻全量
   `cargo check --workspace`，不要只看改的那处。
3. **编译通过 ≠ 覆盖到了。** 若某形态（如 struct literal 作为属性值）在仓库里**当前
   没有任何调用点**，编译根本证明不了你没破坏它。必须**补一个回归测试**专门锁住它，
   否则你的修改是未验证的。

## 6. 验证器盲区：自己审计，别交差

部分检查是**集合比对**，签名里重复 3 次的同一个类型可能用 1 行文档「通过」。
验证器不报错 ≠ 文档对。

```bash
# 按文件统计仍然被标记的行，确认剩下的都是别人的文件
{ python3 .../verify_doc_comment_format.py .; \
  python3 .../verify_hardcoded_strings.py .; } \
 | grep -oE "src/[a-z_0-9/]+\.rs" | sort | uniq -c | sort -rn
```

写正则脚本解析 Rust 签名很容易出错（`pub(crate)` 里的括号、`-> T` 里含 `;` 的返回类型、
let-chain 语法），**解析结果与源码不符时不要相信它**。逐函数人工核对，或委派给
subagent 并明确说明「按源码逐行比对，不要写正则解析器」。

## 7. 跑完整门禁，不要只跑你在任务里提到的那几个

**「全仓 0 违规」这种结论，只有跑完脚本目录下全部 `verify_*.py` 才成立。**
只跑任务描述里点名的三四个（本例 `doc_comment` / `hardcoded_strings` /
`no_sibling_dirs`）就下结论，会漏掉没提到的检查项——本例就漏掉了
`let_type_annotations` 和 `module_imports_centralized` 两项共 8 条真实违规。

```bash
for s in ~/.agents/skills/rust-standards/scripts/verify_*.py; do
  printf '%-40s ' "$(basename "$s" .py)"
  python3 "$s" . 2>&1 | tail -1
done
```

**属于别人的违规也必须点名报告**（文件名 + 行号 + 是否已在 HEAD 存在 + 是否为
未提交的在制品），而不是让「全仓 0」这个说法含糊掉。判断归属用：

```bash
git show --stat --format='' <my-commit>          # 我的提交含哪些文件
git status --porcelain -- <疑似别人的文件>          # 未提交 = 在制品
git show "HEAD:<file>" | grep -c <违规行模式>      # HEAD 已有 = 历史遗留
```

**per-file 核验要用完整路径 grep，不要用 basename。** 文件名大量重名（几十个
`fn.rs`），`grep -c "$(basename $f)"` 会把每个 `fn.rs` 都算成有违规，得出的
「全部违规」是假的。用 `grep -c "/euv/$f:"`。

## 8. 收尾同步文档

框架行为变了（尤其是「什么写法合法」这类约定），**任务里引用的 SPEC / RULES 文档必须
同步改掉过时规则**，否则后续 agent 会照着旧文档继续写被禁的写法。

- 改的是**规则本身**时，在原地重写那一条，并把「这是 bug 已修」写成历史注记；
  不要在文末追加「UPDATE: 其实……」——那会让错误规则继续留在文件里。
- 顺手搜一遍持久化 skill 目录（`~/.agents/skills/`）和仓库内 `.md`，确认没有第二处
  抄着同一条过时规则。

## 9. 报告口径

必须给：改了哪些文件、**before/after 的实测条数**（分文件或分验证器）、编译结果、
以及**做不了的部分和原因**。没实测的数字不要写。别人已经修完的部分明确说
「非我改动，我只核验」。
