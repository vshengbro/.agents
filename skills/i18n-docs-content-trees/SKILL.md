---
name: i18n-docs-content-trees
description: Use when a docs site keeps parallel per-locale page copies.
license: MIT
author: hermes-curator
metadata:
  version: 1.0.0
  hermes:
    tags:
      - i18n
      - docs
      - locale
      - content-trees
      - migration
    related_skills:
      - euv-docs-contribution
      - docs-pages-docs-contribution
      - delegate-task-contract-pitfalls
      - rust-wasm-gh-pages-deploy-pitfalls
---

# 多语言文档内容树 (parallel-locale docs sites)

## When to Use

站点的每个页面在多个语言目录下各存一份 (`docs/en/`, `docs/ja/`, `docs/ko/`, `docs/zh/`),
内容是**平行副本**而不是共享片段。遇到以下任一情况时加载:

- “多语言文档不全 / 某个页面在别的语言打不开”
- “这个页面找不到 / 侧边栏里没有它”
- “能不能把父级目录删掉”(根目录同时存在裸内容和 locale 副本)
- 需要把内容从裸目录搬进 locale 目录
- 站点是 hash 路由 SPA,`curl <route>` 无法判断页面是否存在

## 核心心智模型:locale 目录是唯一的导航来源

多语言文档站点的**侧边栏 / 导航从 locale 目录树生成**,不是从裸内容目录。
这推出最重要的一条规则:

> **只存在于裸目录(无 locale 前缀)的内容 = 在任何语言的导航里都不存在。**

这类内容的路由往往**能打开**(无前缀路由照样生成),所以症状具有欺骗性:
页面是活的,但没有任何入口,而带前缀的路径 404。**「多语言文档不全」和「某页面找不到」
通常是同一个缺口,不要当成两个 bug 分别排。**

具体到某套构建脚本的路由/侧边栏规则(前缀识别、哪个 locale 从哪个目录生成、
`README.md` → 目录路由的映射),见 `references/euv-docs-routing.md`。

## 核心工作流

### 1. 先量化,再动手

在移动或删除任何内容前,算清三件事:

```python
# 逐字节比对:哪些是副本,哪些只此一份
import os, filecmp
identical = [k for k in set(root) & set(lo)
             if filecmp.cmp(root[k], lo[k], shallow=False)]
unique    = sorted(set(root) - set(lo))
```

- **副本** → 冗余,删掉或搬进 locale 目录都安全
- **unique** → 删了就是静默丢内容。**先搬进每个 locale 目录,确认落盘,才允许删源**

不要目测 `git status` 的行数判断冗余。用逐字节比对,README 里一个看不见的空格差异
就足以改变结论。

### 2. 迁移时按「源文件」切分,不是按语言切分

`N 个源文件 × M 个语言` 的搬运/翻译任务,切分轴必须是**源文件**:一个源文件及其所有
语言版本永远归同一个子 agent。按语言切会让 N 个 agent 同时读同一批源文件、各自重建
上下文,术语跨语言漂移。给每个 agent 的 context 里写死这个乘积让它自查
(`12 source files x 4 locales = 48 target files`)。详见 `delegate-task-contract-pitfalls` §2b。

### 3. 搬运的硬约束(会真的弄坏页面/构建)

- **不翻 LICENSE / 法律文本** —— 逐字节复制,并在指令里**明说「不翻译」**,
  否则会被「顺手润色」
- **密码门控值**(`password:` 等)与 keywords meta —— 原样复制,改了会锁页
- **frontmatter 的 key 集合**不许增删改名,只翻 value;`order:` 等保持源值
- **代码块 / 数字 / 标识符 / 命令行**跨语言逐字节一致
- **文档骨架**(标题层级序列、表格、告警块)不许因翻译而改变
- 已存在的 locale `README.md` 常带 `index: false`(只借标题给分组,不出页面)——
  **不要覆盖**,迁移只创建非 README 文件

### 4. 站内链接必须逐语言写死

locale 副本里的站内链接**各自写死前缀**,不做推导。四份首页都写 `/appreciate.html`,
意味着在 `/en/` 上点按钮会跳到裸根的中文页。正确做法:每份 locale 的链接指向
`/<locale>/...`。外部 `https://` 链接不受影响。

移植完成后逐条验证:在每个 locale 的首页渲染里 dump 按钮 `href`,确认都带正确前缀。

### 4b. 删页必须同步扫掉所有入站链接（否则你亲手制造 404）

删除一个内容页(合并、去除第三方内容、去掉赞赏页)不只是 `rm` 文件:构建器会从目录树
自动生成该路由的导航项,但**markdown 正文里手写的入站链接不会被自动清理**,它们会
原地指向一个不再生成的路由 —— 用户点进去就是 404。删页的工作量在清链接,不在删文件。

删除前必须跑一次机械的入站扫描(见 §4c),确认链接数;删除后重跑,必须归零。删页前
先确认被删文件在 git 历史里(`git log --oneline -- <path>`)—— 内容删除不可逆,历史
里没有就是真丢了。

### 4c. 站内链接 404 要用脚本枚举,不要靠通读

「很多 hash 页面跳转地址不对」这类反馈必须机械枚举,人工抽查必然漏。把内容树里
所有站内链接(`](/...)`、`](/<locale>/...)`、相对路径、纯锚点)抽出来,与「实际存在的
页面集合」交叉验证,分三类输出:

| 类别 | 判据 | 归属 |
|---|---|---|
| A 指向不存在的页面 | 链接路径不在页面集合里 | **内容侧**改写(除下面第 4 条例外) |
| B 链接形态与实际 route 不一致 | 页存在,但带/缺后缀、尾斜杠、缺 locale 前缀、大小写 | 看框架是否做归一化,见下 |
| C 只有锚点或可疑写法 | 无页面的 `#anchor`、相对路径解析歧义 | 内容侧逐条判断 |

**框架侧归一化 vs 内容侧改写,按这条分界**:改内容永远比改路由便宜且可回滚,所以先用
内容改写消掉能消的;剩下的 B 类若本质是「用户从站外/别处粘贴了一份形态不同的合法
地址」,才值得在路由查找里补归一化。**但不要为了消灭告警强行合并两个真实存在的页面**
(例如同时存在 `/foo` 与 `/foo.html` 两个真页面),那是把一个 bug 换成一个更隐蔽的 bug。

改完**重跑同一个脚本**并把两次输出贴出来,A 类必须归零才算完。只说「我改了几条」
不算证据。

### 4d. 组件内的固定文案也要走 locale,不是只有 markdown

站点里的框架组件(密码门控页、404 页、搜索框空态、返回/重试提示)常有硬编码的单一
语言文案。这类文案不在内容树里,locale 覆盖率天然是 1/N,用户会直接看见。两条硬约束:

1. **locale 判定复用路由器已有的 locale 解析**,不要在组件里另写一套前缀匹配 —— 两套
   判定迟早在「根 locale 与子 locale 前缀互相包含」时给出不同答案。
2. **翻译表集中在站点 crate 内**,缺语言要有确定的回退(一般落英文),不允许渲染空串 ——
   空串比英文更糟,因为用户看到的是「标题在、正文没了」。

验收是**逐语言数键**,不是抽查一两个页面。

### 5. 验证用渲染,不用 curl

hash 路由 SPA 只产出**单个** `index.html` + 一个包,所有路由靠 `location.hash` 解析。
`curl /essay/` 永远返回同一份 shell,**无法区分路由存在与否**。

用 headless `--dump-dom` + `--virtual-time-budget`(给 wasm/JS 初始化时间),
抓页面标题元素判断路由是否存在,并 dump 导航链接验证条目。轻量,也不受本机真实
浏览器 profile 锁影响。`references/euv-docs-routing.md` 有可直接复制的命令。

### 6. 图片/静态资源通常跨语言共用一份

站点根相对的图片路径配合 `<base href="./">` 在所有 locale 下命中同一份资源。
**不要**为每个 locale 复制一套图片目录。验证时确认资源在构建产物里位于 locale 无关
的路径,且目标页面的 `<img>` 确实完成了加载。

## 删除源目录的判定标准

全部满足才可删:

1. 逐字节比对确认:该目录下每个文件在 locale 副本里都有对应物
2. 独有内容已搬进**每一个** locale 目录,并已重新构建验证路由可达
3. 全站没有指向待删路由的入站链接(检查裸根路由的前缀重名:`/essay/` 与 `/zh/essay/`
   是两条不同路由,删掉源会改变 `/essay/` 的行为)
4. 删除后**重新构建一次**并抽验若干条路由,确认没有断链

任何一条不满足就**停下来问**,不要替用户决定删哪些。删除是不可逆的,内容损失不会
在 git 里留下明显痕迹(尤其是被 locale 副本「看起来覆盖」过的目录)。

## 构建脚本的 locale 契约(2026-09-29 实测踩坑)

**locale 的「内容目录」和「URL 前缀」必须是两个独立声明的字段,不能互相推导,也不能硬编码。**

euv-docs 的 `build.rs` 曾把 `/` 这个 locale 的内容目录**硬编码成 `zh`**:

```rust
let root = if locale.prefix == "/" { docs_dir.join("zh") } else { ... };
```

而配置里写的是 `prefix: /` + `lang: en-US`。后果不是报错,是**静默生成一个只有 1 个页面的站点**:
`docs_gen.rs` 里只剩 `route: "/"`,`/appreciate.html`、`/guide/…` 全部消失,
`cargo build` 成功、clippy 干净、零 warning。

现在的契约:

| 字段 | 含义 | 缺失时 |
|---|---|---|
| `prefix` | URL 前缀(`/`、`/zh/`) | 解析失败 |
| `dir` | 内容目录(`en`、`chinese`) | **构建 panic** |

两条硬约束:

1. **不猜内容目录。** locale 的内容位置是数据不是约定。实测:目录 `chinese/` 配
   `prefix: /zh/` 正常产出 `/zh/…` 路由 —— 目录名与 URL 前缀彻底解耦,
   改内容树不会悄悄改动所有公开 URL。
2. **空 locale 必须让构建失败。** 断言 `<SRC_DIR>/<dir>` 存在且至少含 1 个 `.md`,
   否则 panic 并打印 locale / dir / 路径。宁可构建失败,也不要静默产出空站。

**验证方式**:不要只看 `cargo build` 成功。查 `docs_gen.rs` 的路由清单:

```bash
T=$(grep target-dir ~/.cargo/config.toml | cut -d'"' -f2)
F=$(find "$T" -name docs_gen.rs -newermt '-2 minutes' | head -1)
grep -oE 'route: "[^"]*"' "$F" | sort -u
```

路由数对不上就是内容没被收进来。再用 headless `--dump-dom` 确认 `#app` 真有子节点。

**A/B 陷阱**:想确认某个行为是不是自己引入的,必须**从 HEAD 重新构建一份**再对比。
euv-docs 的 HEAD 构建在浏览器里是**完全空白**(`#app` 子节点 0、正文 0 字符),
所以「HEAD 也有这个 bug」这种判断在它身上根本不成立 —— HEAD 根本没渲染。
先确认对照组能渲染,再谈 A/B。

## Pitfalls

- **别把「路由能打开」当成「用户能到达」** —— 裸根路由能打开恰恰是没有导航入口的症状
- **别在量化 unique 之前删任何目录** —— 45 个目录里 40 个是纯重复并不代表另外 5 个也是
- **别让子 agent 翻译 LICENSE / 密码 / 版本号** —— 这些必须逐字节保留
- **别按语言切分翻译任务** —— 术语会跨语言漂移
- **别用 curl 验证 hash 路由** —— 它对所有路由返回同一份 shell
- **别只删页面不清链接** —— 导航项会自动消失,正文里的手写入站链接不会
- **别手工通读 markdown 找 404 链接** —— 几百个文件的站内链接必然抽查漏,写脚本枚举
- **别在组件里另写一套 locale 前缀匹配** —— 复用路由器已有的 locale 解析,否则两套判定会打架
- **别把「构建成功」当作用户能到达** —— 路由生成成功与链接指向它是两件事

## References

- `references/euv-docs-routing.md` — euv-docs 的具体路由/侧边栏规则(前缀识别、
  `/` locale 从 `docs/zh/` 生成、`index: false` 语义)、headless `--dump-dom`
  验证配方、构建脚本 PATH 回退模板。
