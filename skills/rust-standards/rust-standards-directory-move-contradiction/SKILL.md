---
name: rust-standards-directory-move-contradiction
description: Use when a §1.3d fix says "move foo.rs to foo/mod.rs".
---

# 「搬进子目录」不能靠改名为 mod.rs 达成

## 触发

任何 Wave 0 / 「只做文件搬迁」的任务书里出现这句话:
「把 `foo.rs` 搬进 `foo/` 子目录, 改名 `mod.rs`」。

## 实测(vice-city-web, 2026-10-12, 基线 audit 41/51)

把 `src/*.rs` 13 个文件全部改成 `<name>/mod.rs` 的模拟结果:

| 指标 | 搬迁前 | 全改 mod.rs 后 |
|------|--------|--------------|
| §1.4 `is not a keyword file name` | 13 | **0** ✅ |
| check 44 §1.3d sibling dirs | 1 violation | **0** ✅ |
| check 26 keyword purity 总违规 | 13 | **1374** ❌ |
| check 51 §2.5 mod.rs 零注释 | 0(PASS) | **12563** ❌ PASS→FAIL |

单文件试点更直观 —— `src/enemy.rs` → `src/enemy/mod.rs`(284 行, 11 个 top-level item):
check 26 +10 `forbidden decl in mod.rs file`, check 51 +115。

## 原因(三条独立的硬约束)

1. **`verify_keyword_file_purity.py` 的 `FORBIDDEN_DECLS["mod.rs"]`** 覆盖
   `struct|enum|fn|trait|impl|type|const|static`。mod.rs 是**唯一不许放声明**的
   关键字文件 —— §1.3 表格里它的职责是「组织导出与导入」。
2. **`verify_no_toml_mod_comments.py`(check 51, 2026-10-09 绝对化)** 要求
   每个 mod.rs **零注释**。而这些文件顶部都有 `//!` 模块说明(几行到十几行)、
   每个 item 带 `///` 文档。搬一次就是几万条违规。
3. **§1.4 的名字约束是双向的**:只要文件名不是关键字名,放哪个目录都违规。
   所以「先搬、后拆分」在**中间态必然 FAIL**,不存在「只搬不拆」的合法终态。

## 正确形态

`foo.rs`(混合 11 个 item)只能落成:

```
src/<responsibility>/mod.rs   ← 零注释, mod decl + re-export + use super::*;
src/<responsibility>/const.rs ← 只放 const
src/<responsibility>/struct.rs
src/<responsibility>/fn.rs
src/<responsibility>/impl.rs
```

即**搬迁与拆分必须同一次完成**。「本轮只搬不拆」与「§1.4 归零」互斥。

## 目录命名

不要建 `const/` `struct/` `impl/` `fn/` 目录(按关键字命名 = §1.3d 明令禁止);
用职责名词 `config/` `alias/` `camera/` 等。

## 附带坑:git rename 检测会断

`git mv src/foo.rs src/foo/mod.rs` 后,`git diff origin/master` 把它显示为
**新增文件**(rename 检测未命中),于是所有 diff-scoped audit check
(4 `#[test]` / 8 `#[cfg(test)]` / 9 `use crate::` / 40 hardcoded strings)
都会把整文件当新增行扫一遍 —— 搬迁本身就能把这些 check 从 PASS 打成 FAIL。
评估 diff-scoped check 时先确认 rename 检测有没有命中。