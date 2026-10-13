---
name: verifying-documented-tool-interfaces
description: Verify documented CLI/SDK commands really exist.
license: MIT
metadata:
  version: "1.0"
  category: software-development
  hermes:
    tags: [documentation, verification, drift, cli, sdk]
    related_skills: [agent-skills-source-sync, skill-index-and-english-titles, verifying-against-a-real-gate]
---

# 验证文档里的工具接口是否真实存在

## When to Use

- 任何在**文档 / skill 里写了外部工具的调用方式**的地方，且这些调用会被 agent 直接照拄执行。
- 触发词：更新到最新版、对账、skill 同步、这个命令报 `Unknown command`、文档里的命令还能用吗、模型名是不是变了。
- **不适用**：只改了措辞 / 排版 / 翻译，没有触碰任何命令、参数、模型名。

## 为什么这条独立于「版本对账」

版本/数字对账（版本号、class 数、模块数）只保证「数字和源仓库一致」。
**接口对账**保证「照着文档敲命令不会 `Unknown command`」。

两者是**独立的漂移轴**：源仓库可能几个月不提交，文档与源仓库完美一致，
但文档描述的工具接口早已面目全非。**仓库干净 ≠ 文档正确。**

## 铁律

1. **未经 `--help` 验证的命令，不得写进文档。** 凭记忆或旧文档写下的命令一律视为未验证。
2. **不确定就问工具本人**：`--help` / `--version` / `--dry-run` 的输出优先于任何记忆、README、训练数据。
3. **三处都否定才判定「不存在」**，不要凭一次失败就下结论。
4. **不存在时要写明**：文档里显式写「该命令不存在」+ 真实替代路径。既不保留假装能用的写法，也不整节静默删除（静默删除会让读者以为「本来就没这功能」）。
5. **退出码为 0 不证明命令存在。** 部分 CLI 把未知子命令当成合法的顶层查询，打印根 help 后正常退出。判据是**输出签名**：真命令的 help 含自己的 usage 行（`Usage: <tool> <resource> <command>`）且**不含** resource 总表；根 fallback 会同时出现泛用 usage 行和完整 resource 列表。两者同时出现 = 根 fallback = 该命令不存在。
6. **文档里引用的每个命令都要探一次，不只是改动的那些。** 假命令往往在同一个 skill 的另一节、或兄弟 skill 里已经存在很久；只验证本次改动的那几行会漏掉。探针脚本见 `scripts/verify_doc_commands.py`。
7. **日期要确认挂在哪个事实上。** 官方原文常把日期只挂在其中一个事实（如“自 X 日起付费 API 对新用户关闭；免费模型将下线”）。改写时把日期整体搬到另一个事实上，就是用一个错误替换另一个错误。逐个事实回原文核；官方没给日期就写“官方未给出日期”，不要顺手补一个。

## 判定命令是否真实存在（按可信度降序）

```bash
# 1. 最直接：让工具自己回答 —— 但必须比对**输出签名**，不能只看 exit code
<tool> <resource> <command> --help 2>&1 | head -5; echo "exit=$?"

# 2. 解包最新发布产物，在 bundle 里 grep（确认「最新版也没有」）
npm pack <pkg>@latest && tar xzf *.tgz && grep -c '<kw>' package/dist/*.mjs
#    python: pip download <pkg> -d /tmp/x --no-deps; tar tzf /tmp/x/*.whl | grep <kw>
#    rust:  git clone --depth 1 <repo>（或 cargo download <crate>）

# 3. 看源码命令注册表（确认没有对应目录）
curl -sS https://api.github.com/repos/<org>/<repo>/contents/src/commands
```

## 批量对账流程

```bash
<tool> --help                        # 资源/命令总表
for r in <resource...>; do <tool> $r --help; done   # 逐个 resource 展开
```

然后把文档里的**每个**声明与实际输出逐项对齐：资源列表、命令名、默认模型、默认参数、退出码。

| 声明项 | 文档值 | 实际值 | 证据 |
|---|---|---|---|
| 子命令 | ... | ... | `<tool> ... --help` |

## 改写原则

- **保留**与工具无关的硬内容：prompt 写法、领域知识、错误处理、agent flag 纪律、输入校验。
- **只替换**与工具接口耦合的部分。
- frontmatter 的 `description` 前 57 字符仍要能独立当触发条件用；描述仅在**事实性错误**时才改。

## 易踩的坑

### ❌ 用 exit code 当存在性判据
“跑一下看退出码”是最自然、也最危险的做法：未知子命令常被当作顶层查询，**打印根 help 并 exit 0**。只看退出码会把一个根本不存在的命令当成已验证写进文档。必须比对输出是否含**根 fallback 特征**（泛用 usage 行 + resource 总表同时出现）。伪信号的正例见下方脚本的 `ROOT-FALLBACK` 标记。

### ❌ 只验证本次改动的那几行
同一个 skill 的其他节、甚至兄弟 skill 里，往往已经藏着同一个假命令很久了。改完 A 节不代表 B 节的 `mmx music generate` 会自己消失。全量 grep + 全量探测才能收口。

### ❌ 把自己写给子 agent 的简报当事实
派发时列的默认值和 flag 列表是**假设**。子 agent 实跑一遍的结论通常比简报可靠（它有执行证据）；它报出与简报冲突的项时，默认它对，并在最终汇报里把纠正后的值说清楚。简报里要写明“逐条实跑复核，不要相信简报”。

### ❌ 源仓库 diff 为空就收工
上游 HEAD 时间戳久远 = 上游已不维护 = 文档正确性**只能**靠对工具本身保证。这是要主动核对接口的信号，不是收工信号。

### ❌ diff 被行尾符污染
vendor 来的文件常是 CRLF，上游是 LF，`diff -q` 报 differ。**先剥行尾符再比**：
```bash
diff --strip-trailing-cr -q <upstream> <local>
diff --strip-trailing-cr -u <upstream> <local>   # 判为 differ 后再看真实差异行
```

### ❌ 忘了 skill 目录被 symlink 共享
skill 常在多个运行时目录间共享，编辑源目录会**同时**影响所有引用方。改完确认引用关系，只在一处落地：
```bash
ls -la <live-skills-dir> | grep -i <skill-name>   # name -> /abs/path = symlink
```

### ❌ 改完不重算 lock/指纹
共享树带一份 manifest 记录每个 skill 的指纹哈希与 `updatedAt`。内容改完不重算，下次对账会把自己刚改的继续报成 drift。**先只读后写**：
```bash
<python> scripts/update_skill_lock.py --check    # 只报 drift
<python> scripts/update_skill_lock.py           # 重算指纹 + 时间戳
```

### ❌ 拿「无变化」包装成一次更新交付
上游没动却产出一堆看起来像更新的改动，和把「上游没动」当结论直接收工、把已失效命令留在文档里，**同样是失败**。交付必须是三段式：

1. **上游结论**：HEAD sha/日期 + 逐项 identical / differ 清单
2. **真实漂移**：文档声明 vs 工具实际，表格化（含证据来源）
3. **做了什么 / 没做什么**：改了哪些文件，哪些发现故意没改及原因

## 验证清单

- [ ] 跑过 `scripts/verify_doc_commands.py`，文档内所有命令型引用均已探测
- [ ] 每条命令都存在；`ROOT-FALLBACK` 标记要么修掉、要么已在文档中显式声明“不存在”
- [ ] 模型名/默认参数与 `--version` / `--help` 输出一致
- [ ] 「不存在」的命令已从文档移除，且以显式说明代替而非静默删除
- [ ] `grep -rn '<不存在的命令>' <改过的目录>` 命中为 0
- [ ] lock/指纹已重算（reconcile 脚本跑过）
- [ ] symlink 型 skill 确认只需改源目录一处

## 关联

- `agent-skills-source-sync` — 数字/版本声明对账（用户自建 skill；本文覆盖其未涉及的**接口**轴）
- `scripts/verify_doc_commands.py` — 本 skill 的全量探测脚本，直接跑
- `skill-index-and-english-titles` — 本仓库 skill 批量维护与 symlink/同步路径
- `verifying-against-a-real-gate` — 同源思想：拿到「通过」结论后重新量一遍
