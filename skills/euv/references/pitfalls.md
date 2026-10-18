# euv 框架踩坑速查 (symptom → cause index)

Symptom-first lookup. Each row names the symptom you observed and the cause or
the place to look. Every "where" below is a real path in the repo — this file
carries no links to documents that don't exist.

## 症状索引

| 症状 | 原因 / 去哪看 |
|---|---|
| reactive `if` 换 arm 后，新 arm 的 click handler 不响应 | handler 没随 arm 重绑；查 `core/src/renderer/` 的事件注册路径，或改用 class 切换代替该形态 |
| 跨 arm / 跨 route 的 `Signal` 状态残留，overlay 错位 | 组件状态没随 unmount 清理；检查 hook 的 cleanup 是否注册 |
| iOS Safari 把 `<div>` tap 当滚动，delegated `onclick` 静默失效 | 触控与滚动的判定交给浏览器；可点击元素用真实 `<button>` |
| canvas 固定宽高比放进全屏容器被拉成椭圆 | 容器没锁 aspect ratio；给容器加 `aspect-ratio` |
| header/drawer 顶部出现大片死空白 | 误用了 `env(safe-area-inset-top)`；见 `euv-ui-standards` §2.3 的 `--euv-mobile-safe-top` 变量契约 |
| `euv fmt` 与 `cargo fmt --check` 结果不一致 | `cargo fmt` 不重排宏体；`class!`/`html!` 一律用 macro-aware 的 `euv fmt` |
| 下游 crate 写 `euv = "*"` 导致 CSS / API 不匹配 | 依赖漂移；版本只由根 `[workspace.package]` 决定，pin 到同一版本 |
| bump 之后 sub-crate 版本 stale，或 master push 失败 | 核对根版本提交、同步流水线及其结果；成员/依赖版本由 CI 同步，不另跑本地改版本路径 |
| `use_async` 在组件卸载后仍 fire | 异步 hook 缺 cleanup（`use_async` 在 `ui/src/hook/`） |
| profiler hook 挂在 hot path 上拖慢生产构建 | 测量代码进了 release 路径（`use_profiler`） |
| Signal 订阅与 DOM 节点 lifetime 不匹配 → 内存涨 | 订阅未随节点销毁解绑 |
| 多个 render root 时 `use_node_ref` 串号 | NodeRef 跨 root 复用；每个 root 独立取（`core/src/app/impl.rs`） |
| signal 重渲染路径某些 case 不生效 | `patch_attributes` fast-path 未被走到；查 `core/src/renderer/render/impl.rs` |
| css reset / keyframes 与 page CSS 优先级冲突 | 注入顺序：`inject_app_global_css`（`ui/src/style/css/fn.rs`）；用 `html body` 前缀提 specificity |
| 内部 CSS minify / inline pipeline 在某些输入爆栈 | 宏产物体积或嵌套深度；见 `euv-ui-standards` §3.G 的展平 selector 规则 |
| release 时 crates.io publish 顺序写错 → path-dep 解析失败 | 按实际依赖图及发布流水线核对；workspace 成员列出的顺序本身不是拓扑序证明 |

## 工具分工

| 工具 | 提供 | 不提供 |
|---|---|---|
| `euv` (euv-cli) | `run` / `build` / `fmt` / `help` | `bump` / `sync` / `publish` |
| `crate-cli` (`~/.cargo/bin/crate`) | `bump` / `sync` / `fmt` / `publish` | dev server / 模板生成 |
| `cargo fmt` | impl 代码 | `class!` / `html!` 宏体重排 |

## 关键词速查

- **click 不响应** → reactive `if` 换 arm 行 / iOS delegated 行
- **状态错位** → 卸载未清理行 / `use_node_ref` 跨 root 行
- **样式回退** → 依赖漂移行 / `inject_app_global_css` 优先级行
- **build / publish 失败** → `euv fmt` 行 / bump sync 行 / publish 顺序行
