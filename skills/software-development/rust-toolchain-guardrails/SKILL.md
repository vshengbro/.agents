---
name: rust-toolchain-guardrails
description: 'Guardrails for crate upgrades and pre-commit gates.'
version: 1.0.0
author: hermes-curator
tags: [rust, cargo, dependencies, pre-commit, audit]
related_skills: [rust-standards, git-standards, crates-cli-usage]
license: MIT
---

# Rust 依赖升级与完工校验护栏

本 skill 是 `rust-standards` 的**执行侧补充** —— 规范说"改完必须跑到 exit 0",本 skill 说"跑之前先确认不会炸,被拦了怎么判"。

**加载顺序**:`rust-standards`(硬性规范,总是先加载)→ 本 skill。规范冲突时以 `rust-standards` 为准。

## When to Use

出现以下任一情况就加载本 skill:

- 用户说「升级了依赖版本,修复报错」/「升级 syn / jsonwebtoken / tokio / serde」—— 任何 crate 大版本跳跃
- 准备跑 `rust_pre_commit.py` 当完工检查
- `git commit` 被 `~/.git-hooks/pre-commit` 拦下,需要判断是新增违规还是历史债
- 需要证明「我的改动没有引入新的 audit 违规」
- 刚跑完某个会写盘的 fixer / audit 脚本,发现工作区多出意料之外的文件改动

**不适用**:纯 query 类任务(读代码解释实现)、不涉及 cargo 的脚本。

## 1. 升级依赖:先确认这个依赖**真被使用**,再改版本

`[workspace.dependencies]` 里列出的依赖**不等于**有 crate 在用。孤儿声明
(声明了但没有任何成员 crate 引用)升级它对构建零影响,只会留下一堆无意义
diff,并且会让人误以为“跨大版本已经验证过”。

```bash
# 反查:哪些 workspace 依赖真被成员 crate 消费(只算 workspace = true 的)
python3 - <<'PY'
import re, glob
root = open("Cargo.toml").read()
m = re.search(r'\[workspace\.dependencies\](.*?)(?=\n\[|\Z)', root, re.S)
ws = {}
for line in m.group(1).split("\n"):
    line = line.strip()
    if not line or line.startswith("#") or "path =" in line: continue
    mm = re.match(r'^([A-Za-z0-9_-]+)\s*=\s*"([^"]+)"', line)
    if mm: ws[mm.group(1)] = mm.group(2)
used = set()
for f in glob.glob("**/Cargo.toml", recursive=True):
    if f == "Cargo.toml": continue
    t = open(f).read()
    used |= set(re.findall(r'^\s*([A-Za-z0-9_-]+)\s*=\s*\{\s*workspace\s*=\s*true', t, re.M))
for n in sorted(used):
    if n in ws: print(f"{n:26} {ws[n]}")
PY
```

**判据:不在这个列表里的依赖,升级它 = 0 收益。** 先回滚 / 别动。

**为什么这个检查必须在最前面**:用户说“跨大版本如果报错就修复”时,前提是这些
包真的进编译。实际上一批跨大版本依赖可能是孤儿声明,编译器根本碰不到,于是
“升了、没报错”是个假绿信号 —— 它掩盖了“这些改动其实什么也没验证”。

**Cargo.lock 被 gitignore 的库仓**:看到 `cargo update` 后 `git diff Cargo.lock`
为空,先 `grep -n Cargo.lock .gitignore` 确认。库仓忽略 lock 是正确做法,此时
**只能靠编译验证,不能靠 lock diff**。

**无 lockfile 仓的传递依赖漂移**:这类仓每次 CI、每个新 worktree 都是全新解析
—— 不在你 `Cargo.toml` 里的传递依赖可以在你零改动时跳到破坏 API 的新版本
(实测 hyperlane-core 21.10→21.11 把 `Server::route` 从单泛型改成双泛型,cli
在两个分支都没动的情况下编译失败)。**症状**:昨天还绿的代码在新 checkout 上
挂且 `git diff` 为空;**诊断**:对比两个工作区的 lock(`grep -A1 'name = "
<crate>"' Cargo.lock`),`cargo update -p <crate> --precise <旧版>` 复绿即坐实;
**修法**:把该传递 crate 写进根 `[workspace.dependencies]` 精确钉版
`"=<version>"` 并在消费成员加 `{ workspace = true }` —— 直接依赖的 `=` 钉版是
Cargo.toml 里**唯一**能约束传递解析的机制(父 crate 的 caret 要求管不住它自己
的传递依赖)。钉版行上写一句注释说明被钉的原因与迁移出口。

### 1.1 单 crate 仓的孤儿依赖

上面那段脚本只扫 `workspace = true`,单 crate 仓(没有 `[workspace.dependencies]`)
跑不出任何东西。对普通 `[dependencies]` 逐个反查:

```bash
grep -rn "euv_engine\|euv-engine" src --include='*.rs'   # 期望 0 命中
```

**doc-comment 会伪造「已使用」信号**:模块头 `//! 技术栈:euv + euv-engine`
是唯一命中,`use` 一个都没有。看到命中数非 0 时,先看命中行是注释还是代码 ——
`grep -c "^use\|^//!"` 分一下就清楚。孤儿声明要么删掉(升级时少编译一个用不到
的 crate),要么在报告里写明为什么保留,**不要**默默升它然后汇报「无报错」。

## 1d. 绿色的本地构建不证明 CI 会绿:CI 装的是**已发布**的 crate

当某个 CI job 用 `cargo install <crate>` 而不是 `--git <repo>@<sha>` 时,它解析的是 **crates.io 上的已发布版本**,不是你的工作树。本地走 `path` 依赖的 workspace 永远不会复现这类断裂。两种隐藏形态:

- **传递依赖 API 漂移**:已发布 crate 声明 `foo ^X`,解析时浮到 `X.Y`,而 `foo` 在该版本改了 API 形状(如方法多了一个泛型参数)。**症状**:编译错误的 `--> ` 路径指向 **registry 缓存目录**(`.../.cargo/registry/src/index.crates.io-*/`)而不是你的源码树 —— 这个路径就是判据,一眼可辨。修法是改调用点 + 改版本要求,而不是只补本地 pin。
- **一个什么都不约束的 pin**:直接依赖上的 `=` 精确钉版 **不约束** 已发布 crate 自己为传递依赖解析出的版本。验证方法:查已发布 crate 真正要什么,而不是相信仓库里的 pin。

```bash
curl -s https://crates.io/api/v1/crates/<crate>/<ver>/dependencies | python3 -c "
import json,sys
for x in json.load(sys.stdin)['dependencies']:
    if '<被漂移的crate>' in x['crate_id']: print(x['crate_id'], x['req'])"
```

**验证规则:CI 从 crates.io 装包时,在干净 checkout 里复现 CI 的解析**(`git clone <branch> <tmp>` 后从那里构建),并把出错依赖**实际解析到的版本**贴进报告。共享同一份 dev-time lockfile 的工作树构建,恰恰会盖住这一整类 bug。

**描述一个不存在的约束的注释,比没有注释更糟** —— 它制造虚假信心,而且让下一个读者以为问题已被处理。本节 §1 那条「钉版行上写一句注释说明被钉的原因与迁移出口」的规则,只有在 pin 真的生效时才有意义;若 pin 约束不到目标传递依赖,要么把它改成真正生效的形式(`=` + 直接依赖 + 消费成员 `{ workspace = true }`),要么删掉注释别声称已修。

## 1e. 依赖漂移会沉默很久:部署流水线长期红 ≠ 刚坏

用户报「线上站点报错」时,**先查上一次成功部署是什么时候**,再去查站点本身。一个从上游 API 漂移导致的编译失败,可以在 `master` 上连续红好几天的定时任务里没人注意,而用户看到的是「今天才发现坏了」。

```bash
gh run list --branch master --limit 5 --json conclusion,createdAt,event,displayTitle
# 一串连续 failure ⇒ 坏的不是这次改动,查最早失败的那次日志
RUN=$(gh run list --branch master --limit 1 --json databaseId -q '.[0].databaseId')
gh api repos/<owner>/<repo>/actions/runs/$RUN/logs > /tmp/r.zip && unzip -oq /tmp/r.zip -d /tmp/r/
grep -rhE 'error\[|error:' /tmp/r/*.txt | head
```

**读部署失败的真实错误,不要采信子代理转述的失败原因。** 本次子代理报的是镜像 job 的 403,而日志里的真实错误是一条编译错误(E0107)——按 403 去修会完全跑偏。子代理报的往往是它最后撞见的那条,不是根因。

同时:**同一个 PR 上的其他 job 红,不代表它和你的改动有关。** 先确认那个 job 在你的 commit 之前就已经红了(`master` 上的历史 run),再决定要不要把它算进本次范围。

## 1f. 配置驱动的生成站:「空集合要报错」不是洁癖

build script 用 `filter_map` / `.ok()?` 逐项解析用户配置时,**每一项都失败会产生一个合法但灾难性的产物:空列表**。空列表会让后续所有校验循环迭代零次(让 "目录不存在" / "无 .md 文件" 这类守卫变成永远走不到的死代码),codegen 发出空数组,运行时在 `[0]` 上 panic —— **失败点从 build log 移到了浏览器控制台**。

规则:**用户提供的配置解析失败必须是硬错误,永远不是空集合。** 写任何新的 `filter_map(parse_x)` 时问一句「全部被丢弃会产出什么」,并让那条路径响亮地失败。参见 `rust-standards` 里的同款 pitfall。

同一族的第二个陷阱:**`cargo:rerun-if-changed` 只监视内容目录,通常不监视 `<docs_dir>/../README.md` 这类配置位置**。只改配置不改 markdown 时 build script 不会重跑,你会去调试一个「什么都没发生」的改动 —— 改配置后 `touch build.rs` 强制重跑。

### 1c. 上游有本地 clone 时,先按 tag diff 给破坏面分诊

消费者升级框架时,如果框架本身在本地有 clone(带 tag),**先 diff tag 再动消费
者** —— 这把「猜 API 变化」换成「读上游真实 diff」,并且能提前判定某次 bump 是
真迁移还是空转。sparse index 版本列表、diff 形状 → 消费者影响的分类表、
以及「用新 API」的判据边界,见 `references/upstream-tag-diff-triage.md`。

判定要落到一句可验证的话上,例如「root `src/` 零 diff,`ui` 的 pub 变化只增不
减,`core` 只有内部模块搬家 ⇒ 消费者用到的重导出面没变」 —— **然后仍然跑消费者
的 `cargo check`**,不能拿 diff 结论代替编译。

### 1c.1 目标仓已有未提交改动时,先单独提交再升级

依赖升级仓往往带着上一轮会话的未提交 / 已 `git add` 未 commit 的改动。**先按它
本来的语义单独 commit,再动依赖**。混在一起的 commit 无法按「只改了 Cargo.toml
的依赖」来复核,回滚其中一个诉求时会连带另一个。开工前先看清三样:

```bash
git -C <repo> status --short          # 已暂存 vs 未暂存 vs 未跟踪
git -C <repo> rev-list --left-right --count origin/<branch>...HEAD
git -C <repo> diff --cached --stat    # 暂存区里到底压了多少行
```

「当前仓库」没有唯一指向时(CWD 不是 git 仓、同目录下有多个同框架项目),按
**最后活动 mtime** 判定,并在动手前把候选列给用户。

## 1b. 跨大版本升级:先拿到真实错误,再改代码

**不要**先猜 API 变化再全量改。先定位编译器报的具体行,再去 registry 源码里 diff 字段。

```bash
# 1. 拿到真实错误
cargo check --workspace --all-targets --message-format short
# 2. 读出 struct 在新版本里的真实定义 —— 不靠记忆,读 registry 源码
find ~/Library/Caches/cargo-home/registry/src -maxdepth 2 -name "syn-3*"
grep -n "pub struct TypeParen" -A 8 <that-path>/src/ty.rs
```

### 1.1 不要对“需要下载新包”的构建加 `--offline`

`--offline` 是在依赖已经全部缓存时省时间的优化,不是默认值。**一旦你刚改过
`Cargo.toml`,lock 里就出现了本地没缓存的版本**,此时任何带 `--offline` 的
`check` / `test` 必然失败:

```
error: failed to download `tokio-broadcast v10.2.2`
attempting to make an HTTP request, but --offline was specified
```

这个报错**不是升级失败**,是命令选错了。看到 `failed to download` + `--offline`
组合,直接去掉该 flag 重跑。**因为它发生在下载阶段,编译根本没开始** ——
把它当成“跨大版本炸了”去 debug 源码,方向就完全错了。

**规则:改过 `Cargo.toml` 之后的第一轮构建一律不带 `--offline`。** 确认
无新包后再在后续重复构建用 `--offline` 提速。

**为什么读源码而不是查 docs**:结构体新增字段只体现在 `E0063: missing field ... in initializer` 这条错误里,migration guide 不一定列全。读完直接补 `attrs: Vec::new()` 一行解决。

**大版本跳跃的实际形态**:多个依赖一起升,通常只有一个真炸。典型是 syn 2→3 给 `TypeParen` 加了 `attrs: Vec<Attribute>`,而 jsonwebtoken 10→11 完全兼容(0 处改动)。**逐个验证,不要因为一个报错就假设全部需要改**。

### 1g. 新版本用 marker trait 卡类型时:读 impl 列表,别按错误文案找 bug

有些大版本把「这个参数该是什么类型」从签名里拿掉,换成一个只对极少数类型实现的新
marker trait。**未实现的类型报 `E0277`,而错误文案讲的是策略、不是类型** —— sqlx 0.9
的 `SqlSafeStr` 只为 `&'static str` 实现,其余(连 `&String` 算)都报
`dynamic SQL strings should be audited for possible injections`。

**文案在讲安全策略时立刻停止排查漏洞** —— 那里没有漏洞,是 trait 实现面收窄了。
判据动作:去 registry 源码 grep 这个 trait 的**全部** `impl`,一次拿到当前版本接受
的类型全集,别去读迁移指南(指南不会列出「哪些类型仍然被接受」):

```bash
find ~/Library/Caches/cargo-home/registry/src -maxdepth 2 -name "<crate>-<新版本>"
grep -rn "impl .* for " <该路径>/src/ | grep -E "&'static str|Assert|pub struct"
```

看到 `impl` 行里带一个 opt-in 包装类型(sqlx 的 `AssertSqlSafe`、`String::leak()`),
那就是官方给的逃生舱。**用它之前必须证明数据流里没有用户输入** —— 逐个列出被插值进
SQL 的表达式来源(const / 内部生成值 / 请求参数),把结论写进汇报;只要有一个来自请求
参数,就别包,改写成 bind 参数。

原生实现只有 `&'static str` 时,`format!` 出来的东西即使内容全部来自 const 也不再满足
签名 —— 包装是唯一出路,**不要用 `String::leak()` 去伪造 `'static`**,那会把编译期约束
换成常驻内存泄漏。

完整的诊断 recipe、逃生舱分类和「最小修复 vs 重写」决策表 →
`references/marker-trait-api-breaks.md`。

### 1h. 任务是「修构建」时,只做行为等价的最小改动

升级报了一屏错时,顺手把周边的烂写法一起重写(比如把字符串拼接的批量插入换成
`QueryBuilder` + bind 参数)在技术上更漂亮,但那是**另一件事**:它改变运行时行为,
而你多半没有可运行环境去验证它(`#[cfg(feature = "dev")]` 的初始化路径本地根本没
数据库)。

判据:**先让构建绿,用行为等价的最小改动;重写另起一个 commit,并且必须先能真的跑
它。** 汇报里把两件事分开写,别让 review 以为「升级顺手优化了」。

如果你已经写了一版重写又退回来了 —— 说明你在做第三件事,收手。

## 2. 跑 `rust_pre_commit.py` 之前:必须先确认工作区状态

**`rust_pre_commit.py` 的 Phase 1 会重写源码。** 它的 `doc_comment_audit` auto-fixer 给全仓每个无 doc-comment 的 fn 批量补注释,实测在 24-crate monorepo 上一次跑出 **84 文件 / +7165 行** 的无关 diff,而且三轮迭代都在往里写 —— **违规文件的行号逐轮漂移就是识别信号**。

**跑之前必做**:

```bash
git status --short          # 必须先看清楚工作区已经有什么
git stash list              # 确认没有别人的 stash
```

**三条硬规则**:

1. **工作区不干净就不要跑。** 它会把你的改动和它的批量改写混在一起,之后无法区分、回滚成本极高。用户自己的未提交改动(Cargo.toml 依赖升级等)最容易被淹没。
2. **只想做只读检查时用 `--no-fix`**,或直接跑 `audit_rust_standards.py` + `cargo clippy` + `cargo fmt --check`,绕开 auto-fixer。
3. **它污染过工作区之后,`git diff` 里混着两类改动。** 回滚时先 `git diff > /tmp/collateral.patch` 留底,再全量清,最后**只手工重放自己那几行** —— 不要 `git apply` 整个 patch,那样把它的破坏也一起恢复了。

**判据**:如果这个仓的 audit 本来就有历史债(比如 32/39),那 `rust_pre_commit.py` 大概率永远 exit 非零,此时 auto-fixer 只会越跑越多。历史债应该单独开 sweep 修,不要混进依赖升级的 commit。

## 3. Audit 数字要跟 baseline 比,不能只看绝对值

大量 FAIL(doc-comment 几百 hits / hardcoded-strings / closure / let 标注)是**历史债**,不是这次升级引入的。

```bash
python3 ~/.agents/skills/rust-standards/scripts/audit_rust_standards.py <repo> | grep -E "SUMMARY|FAIL:"
# 再 stash 掉自己的改动跑 clean HEAD,数字必须一模一样
git stash push -- <你的文件> && python3 ... <repo> | grep -E "SUMMARY|FAIL:" && git stash pop
```

两次数字一致 = 零新增违规,可以在 commit message / 对用户汇报里**明确说"历史债,零新增"**。这是把"我觉得没引入"变成可验证结论的唯一办法。

**逐 check 对比,不要只比总数** —— 总量相等也可能是一增一减互相抵消。机械版:

```bash
bash <此 skill>/scripts/audit_baseline_diff.sh <repo> <你改动的文件...>
```

它 stash 掉你的改动跑 BEFORE、pop 回来跑 AFTER,按 check 号 + 标题对齐逐行 diff,
exit 0 = 完全一致(零新增),exit 1 = 有漂移并打印差异行。`AUDIT_SCRIPT=` 环境变量可覆盖
audit 路径。**注意 pop 之后文件变 unstaged**,后面要 commit 记得重新 `git add`。

## 4. Pre-commit hook 被拦:先分类,再修代码

被拦时**先查是"新增违规"还是"历史债"**,分类的目的是知道**改哪里**,不是决定要不要绕过 —— 本仓属于 owned 仓(`eastspire/*` 等),`--no-verify` 一律禁止,详见 `git-standards` §3.6。

```bash
# 用 importlib 调 verifier 的 audit_one(),单文件精确计数
# (绕开 main() 的 is_dir 限制 —— verify_*.py 只接受目录,传文件必 exit 2)
python3 -c "
import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location('m', '$HOME/.agents/skills/rust-standards/scripts/verify_doc_comment_format.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print(len(m.audit_one(Path('<file>'))), 'violations')"
```

**两类 bug 必须分清**:

- **gate 自身有 bug**(passes 文件路径给只收目录的 verifier / 没有 baseline 对比)→ **该修 gate,不是绕过**。绕过等于把"挡新错"永久关掉,后续 session 会照踩同一个坑。
- **真违规且是新增** → 修代码。

**判据**:把同一批文件改用**目录**参数跑一遍 verifier。目录形态全 exit 0 而文件形态全 exit 非零 → gate 的参数 bug,不是你代码的问题。

### 4.1 禁止用"反正 gate 也拦不到"来合理化 `--no-verify`

最容易上当的一种借口是**技术上正确**的那种:"这次 commit 只动了 LICENSE / 只动 .md,staged_file_gate 根本没扫到 .rs,加了 `--no-verify` 结果完全一样。"

结论对,行为错。这个理由可以无限推广 —— 任何一条你**用肉眼已经确认过**的检查都能这样跳过,而那恰好是人无法从日志里复核的一类。**判断依据是"命令被禁止",不是"这次结果会一样"。** 反过来用:如果某个禁止命令的理由需要先证明"这次 gate 本来就是空转",正确动作是**把 gate 跑一遍**,而不是去证明它多余。

已提交之后才发现用错了,原地重写而不是补一个"修正说明"commit:

```bash
git reset --soft HEAD~1      # 保留暂存内容,只丢掉 commit
git status --short           # 确认同一批改动还在暂存区
git commit -m "<原 message>" # 这次真的跑 hook
```

`--soft` 是对的档位:工作区没动,不需要重新 `git add`,重出来的 commit diff 完全一致。**然后在汇报里明说"我用了 `--no-verify`,已重做"** —— 悄悄重写会让用户以为第一次就跑过 gate。没 push 过就不需要 force-push。

### 4.2 全量 audit 通过 ≠ 一定能 commit

`rust_pre_commit.py` / `audit_rust_standards.py` 报满 PASS,`pre-commit` hook 仍可能拦下。原因:**全量 audit 会豁免测试目录,staged-file gate 不会**。实测:全量 40/40 PASS,hook 仍报 `server/tests/signature/fn.rs` 新增 1 条 doc-comment 违规 —— 测试文件里的一个**没有文档注释的辅助函数**(`fn signed_event(...) -> WebhookEvent`)在全量口径下不算问题,在 staged 口径下算。

所以流程是:**本地全量绿 ≠ 可以直接 commit**,要以 hook 的判定为准,拦下就按 §4.1 修。

**这个场景下两条规则会正面冲突,不要试图两全**:给它补 doc-comment 会撞上"测试文件零注释"那一条。解法是**删掉这个辅助函数**、把构造逻辑内联进各个 `#[test]`,一次同时满足两条 —— 让测试文件里只剩 `#[test]` 函数,冲突就不存在了。

## 5. Commit 时的 destructive-command 红线

**`git checkout -- .` 不是 scoped 的** —— 它会连带 revert 掉**用户自己**的未提交改动。修 collateral damage 时用 `git checkout -- <精确路径>`,绝不整仓一把梭。

**`git stash pop` 之后文件变 unstaged** —— 紧接着的 `git commit` 会报 "no changes added to commit",原因不明显。pop 完必须重新 `git add`。

用户说"直接提交,不需要 PR"时:commit 完**默认不 push**,除非明确要求 —— 上游仓(如 `crates-dev/*`)push 走直推 master,不可逆。

## 6. 验证完成的最小充分集

```bash
cargo check --workspace --all-targets            # exit 0
cargo clippy --workspace --all-targets --offline # 0 warning
cargo test --workspace --offline                 # 汇总 passed 数,不只看 exit
~/.cargo/bin/crate fmt --check                   # exit 0
```

`cargo clippy | grep -cE "^warning: |^error"` 数出来是 0 才是 0 warning —— **clippy 的 warning 不影响 exit code,只看 exit 会误判**。

**编辑工具返回的 lint 结论不可信,以 `cargo check` 为准。** `patch` / 写文件工具在编辑后
会跑一次不带 edition 的 lint,因此对 edition 2024 的 crate 会整片报
`E0670: async fn is not permitted in Rust 2015` / `async move blocks are only allowed in
Rust 2018 or later`。这是工具层假阳性:每个 `async fn` 都报,而 `cargo check` 是干净的。
**判据是 `Cargo.toml` 的 `edition` 字段 + `cargo check` 的真实 exit code**,不要按
E0670 去「修」async 语法 —— 那会把文件改坏。

### 6.1 合并提交前的编译清扫:零冲突标记 ≠ 可编译

git 对**不重叠**的编辑静默 auto-merge,分支双方都在增长的 const.rs / mod.rs /
tests 合并后是可预测的破损,只有编译器能发现:

- **重复定义(E0428)/ 重复 import(E0252)**:双方各自向同一文件追加,grep
  双方分支都碰过的 const.rs/mod.rs 找同名 item。
- **复活删除**:一方删了某 item,另一方没碰该区域 → 被刻意删掉的 item 悄悄
  回来。判据:`git show <对方分支>:<file> | grep <name>`,对方删了就跟着删。
- **可见性-消费者错位**:一方收窄 `pub`→`pub(crate)`,另一方新增的外部 crate
  测试在调这些 item → E0624 成片。accessor 被测试(外部消费者)调用就恢复成
  pub(逐字段剥掉 fix 方加的 `#[get(pub(crate))]` 收窄行,对照父分支该字段的
  attr 集);const 走 §18 一律不许 pub,测试改用本地副本或字面量。
- **陈旧测试**:断言另一方刻意改过的行为。同仓已有断言新行为的兄弟测试 = 该
  行为变更是刻意选择的证据,反转旧测试对齐新语义,不是改实现迁就旧测试。

清扫命令:`cargo clippy --workspace --all-targets` 到 0/0 + 全量测试,然后才
`git commit` 合并。委托子代理解冲突时它们被禁止跑 cargo,**编译真相只在编排
方** —— 子代理报告的「0 残留标记」不是构建证据。

**`--all-features` 只证明 cfg 分支能编译,不证明它能跑。** `#[cfg(feature = "dev")]`
下面的建表 / 灌数据代码在 `cargo check --all-features` 下是绿的,但要接上真实依赖
(数据库 / 网络 / 文件系统)才会暴露问题。**汇报里必须单列一句「这些分支只编译未执行」**,
不能并进「验证通过」—— 这一句就是防止把 compile-green 读成 run-green。

**worktree 被删 ≠ 合并丢失**:`.git/worktrees/<name>/` 里的 `index`(含全部
已暂存决议)、`MERGE_HEAD`、`MERGE_MSG` 都还在。重建目录 + 写 `.git` 指针文
件(内容 `gitdir: <主仓>/.git/worktrees/<name>`),`git checkout-index -f -a`
物化暂存树,合并从断点继续,决议零丢失。

## 7. 测试文件的布局陷阱:顶层 `tests/*.rs` 会被编译两次

`tests/mod.rs` 里的 `mod signature;` 会把 `tests/signature.rs` 编进 `mod` 这个 test target;**同时** cargo 把 `tests/` 下每个 `.rs` 都当成独立的 integration-test target。于是同一个文件里的测试跑了两遍 —— 现象是测试计数翻倍(`29 passed` 出现在两个 target 里),看起来像重复注册,实际是两个 target。

**修法是标准嵌套布局**,和 `rust-standards` §14.4/§14.5 一致:

```
tests/
  mod.rs              ← 只写 mod a; mod b;
  signature/mod.rs    ← mod r#fn; + use stripe_pay_server::*;
  signature/fn.rs
```

注意两个连带变化:

- 子文件从 `tests/` 顶层挪到子目录后,`use super::*;` 重新成立(顶层文件里 `super` 是 crate root,没有可 glob 的东西)。反过来,留在顶层的文件必须写 `use <crate_name>::*;`。
- 顶层 `mod.rs` 里那份 `use <crate_name>::*;` 在没有任何子模块通过 `super::*` 继承时是 **unused import warning**,直接删掉。

数一遍 target:正确布局下 `Running tests/mod.rs` 只出现一次。

## 8. 断言写错的时候,先怀疑断言

改完之后测试红了,有可能是实现错了,也有可能是测试把自己的预期写反了。**先分辨再动手** —— 改错的一侧会把 bug 固化下来。

这次的实例:测试断言 `body.contains("currency=usd")`,实现输出的是 `currency=USD`。读实现的 `Currency::code()` 确认返回的是大写 ISO code(Stripe wire 格式确实是大写),**是断言写错了**,改测试。

分辨方法很直接:**去读被测的那一行实现**,看它返回什么。`grep -n -A14 "fn <被测函数>" <源文件>`。不要靠"哪个看着更合理"来选 —— 支付/协议类字段的大小写、精度、符号都有行业惯例,猜不得。

## 相关

- `scripts/audit_baseline_diff.sh` — 机械执行 §3:stash 你的改动跑 BEFORE、pop 跑 AFTER、按 check 逐行 diff,零新增即 exit 0(注意 pop 后文件变 unstaged,commit 前重新 `git add`)
- `rust-standards` —— 硬性规范 + audit 流水线(本 skill 的上游规范)
- `git-standards` —— commit / PR 约定(含 §3.6 `--no-verify` 红线)
- `crates-cli-usage` —— `crate` 子命令(bump / sync / publish)
- `references/cross-repo-dependency-chains.md` —— 跨仓依赖升级链(ctares → hyperlane → euv)的逐步流程:先确认下一步是否存在、先反查真被使用的依赖、跨大版本分诊、等待 CI
- `references/upstream-tag-diff-triage.md` —— 消费者侧升级框架时先 diff 上游 tag 分诊破坏面:sparse index 版本列表、diff 形状 → 消费者影响分类表、「用新 API」的判据边界
- `references/marker-trait-api-breaks.md` —— 大版本用 marker trait 收窄参数类型时的诊断 recipe:从错误文案判断是不是这类断裂、grep 全部 impl 拿到接受面、逃生舱(包装类型 vs `leak` vs 改写成 bind 参数)的取舍、最小修复 vs 重写的决策表
- `references/generated-docs-site-locale-config.md` —— build script 从 README.md frontmatter 生成整个站点的仓(euv-docs 一族):`dir` 必填契约、一个内容目录只能对应一个 URL 前缀(`.find()` 先声明者胜)、如何验证 `docs_gen.rs` 里的 locales 与 route 而不是只看构建退出码、`rerun-if-changed` 不监视配置文件、内容树根目录残留文件的 route 冲突对账
