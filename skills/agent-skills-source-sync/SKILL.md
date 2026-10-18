---
name: agent-skills-source-sync
description: "Use when auditing or updating skill documents against their source repositories: stale versions, API claims, paths, counts, links and entry-point duplication. Not the entry point for ordinary browsing or app work."
---

# Skill documents → source verification

## 仓库硬规则

- 不自动新增 skill；只有用户明确要求时才创建。优先精简现有入口，删除重复路径。
- 临时文件、缓存、`.pyc`、`__pycache__` 不进入 `.agents`；探针和报告写到
  `~/.hermes/cache/scratch`，删除自己创建的临时资源，不清理别人的工作。
- 先记录现有改动和用户排除的路径；受保护目录核对完整文件集合及内容指纹，不能只查 Git diff。
- 所有临时验证资源必须回收；失败、超时、中断、取消同样适用。

### 临时验证资源生命周期（硬规则 3 细则）

1. **范围**：本任务创建的浏览器实例、tab/context、renderer、CDP/WebSocket，临时
   容器及自建临时 volume/network，HTTP/测试服务、watcher、代理/隧道和其他子/后台进程。
2. **先登记再使用**：记录原有资源基线和自己创建的 PID/进程组、启动时间/命令、
   会话/targetId、容器 ID、端口及路径；创建时就注册 `finally`、RAII、context manager
   或 `EXIT/INT/TERM` trap，不等验证完成再补。无法捕获的退出由父/监督进程按登记表兜底。
3. **只清自己的**：借用浏览器只关自己创建的 tab/窗口和 socket；借用服务、容器、
   目录不等于拥有它们。禁止退出用户原有浏览器、删共享数据或按名字批量 `pkill/killall`。
4. **有界终止**：先正常关闭/SIGTERM，明确等待上限；核对进程身份防 PID 复用，
   超时只强制终止自己的存活进程。父 PID 退出不等于其 renderer/helper 子进程也退出。
5. **停掉不等于回收**：临时容器停止后删除，并删除本任务自建的临时卷/网络；
   不运行 `docker system prune`、全局 volume prune 或 `agent-browser close --all`。
6. **逐项读回**：浏览器仍存活时确认精确 targetId 消失；核验 PID/进程组及子进程
   已退出、任务监听端口相对基线已释放、容器已删除，再删除自己的临时 profile/路径。
   数量对上、请求超时或清理命令退出 0 都不是充分证据。
7. **主 agent 验收**：子 agent 上报创建/回收的精确标识及证据，主 agent 亲自核对。
   遗留资源必须点名并说明原因，不能报验证已全部完成。
8. **唯一保留条件**：用户明确要求留存；报告归属、原因、访问地址/路径和停止方式。

## 最短对账流程

1. 枚举所有真实 `SKILL.md`（包括目录下的子 skill），解析 frontmatter、按入口和
   支撑文件分别计量；先保存基线，再改内容。文件大或没有入链都不等于无用。
2. 找到声明对应的真实源仓库和目标版本。区分工作树、已提交源码与已发布包，
   不把本地尚未发布的 API 写成已可用于 crates.io 用户。
3. 通过源文件、编译器生成的 API、命令 `--help` 或最小可运行探针核对存疑声明。
   Rust workspace 用 `cargo metadata --no-deps --format-version 1` 查成员/路径；
   派生宏 API 必须查展开/生成文档，不能因 `.rs` 文本没有方法就判它不存在。
4. 按职责选择一个入口，保留触发条件、最短执行路径、错误处理和可验证结果。
   API 细节按需链接；删除重复教程、历史执行记录、无关关键词和失效路径，不藏进大型档案。
5. 删除入口前搜索所有引用，先保留独有能力并修复可改的调用方。受保护文件仍依赖
   的名字、路径或锚点必须保留；没有工具/凭据不能单独作为删除独有能力的理由。
6. 只更新已核对的声明，其他存疑项明确标注并继续验证。比较语义条目而非重排整篇，
   不误改第三方依赖版本，不用原始文本正则重构 Rust 源码。

## 命中与验收

- 描述开头直接说明任务意图；把邻近但不适用的场景排除，避免任意工具可用就加载。
- 为实际意图准备中英文正例和相邻反例。让独立评审只看描述和问题选择入口，
  再与预先固定的期望比较；歧义改描述后重测，不改期望凑通过。
- YAML、名称唯一性、相对链接、锚点、代码围栏、删除引用及受保护指纹都用脚本验。
- [结构审计](../../scripts/audit_skills.py) 与 [锁文件同步](../../scripts/update_skill_lock.py)
  分别验证文档和实际注册表；`--check` 必须在存在漂移时真失败，重复同步不得再改字节。
- 体积报告区分入口和支撑文件，不能把全文搬进 references 后声称总库变小。
- 命中回归只证明这些用例，不代表线上实际命中率。网络/凭据缺失路径要报未验证。
- 暂存精确路径，跑 `git diff --cached --check` 和英文提交检查；`.agents` 按
  [Git 规范](../git-standards/SKILL.md) 直推，再读回远端精确版本与内容。
