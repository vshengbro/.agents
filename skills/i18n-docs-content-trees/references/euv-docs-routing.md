# euv-docs 路由 / 侧边栏规则与验证配方

具体规则以 `build.rs` 为准(本文档所在仓库 `/Users/sqs/code/euv/docs` 读出)。
换版本时先重新读 `build.rs` 的 `main()` / `process_page` / `route_for` / `build_sidebar`
四个函数再套用。

## 路由生成规则

1. `build.rs::collect_md` 递归收集 `docs/` 下所有 `*.md`;跳过根下的 `public/` 目录。
2. `process_page` 取文件相对 `docs_dir` 的路径,**第一段**若是 locale 目录名
   (`en`/`ja`/`ko`/`zh`…)则剥掉并作为 locale 前缀 `/<locale>/`;否则 locale 为 `/`。
3. `route_for`:`README.md` / `index.md` → `/<dir>/`(带尾斜杠);其他 → `/<dir>/<stem>.html`。
   `join_locale_route` 在 locale 为 `/` 时**不加前缀**。
4. 裸根内容因此产生**无前缀路由**(`/essay/`、`/hyperlane/config/config.html`)。

## 侧边栏生成规则(关键)

`build.rs::main` 逐个 locale 构造 sidebar 根目录:

```rust
let (root, build_locale) = if locale.prefix == "/" {
    (docs_dir.join("zh"), "/zh/".to_string())   // <-- "/" locale 也从 docs/zh 生成
} else {
    (docs_dir.join(locale.prefix.trim_matches('/')), locale.prefix.clone())
};
```

**后果:`docs/` 根目录下的裸内容不进任何语言的侧边栏。** 包括 `/` 这个 locale ——
它照样从 `docs/zh/` 生成。这就是「页面能打开但导航里没有」的全部原因。

### `index: false` 语义

目录 README 带 `index: false` 时:**不出页面**(`find_page` 404),但**把标题借给
sidebar 分组**(分组无链接,只用于折叠)。所以这些 README 迁移时**已经存在、不要覆盖**,
只需创建同目录下的非 README 文件。

### 可达性判定

某页面「用户能到达」当且仅当它的路由出现在对应 locale 的 `build_sidebar` 结果里。
裸根路由(`/` 前缀)只属于无前缀那一类,不在任何 locale 导航中。

## 验证配方(hash 路由 SPA)

站点只产出**单个** `index.html` + 一个 wasm 包,所有路由靠 `location.hash` 解析。
`curl` 对所有路由返回同一份 shell,无法区分存在与否。用 headless dump DOM:

```bash
CHROME="$HOME/Library/Caches/ms-playwright/chromium-*/chrome-mac-*/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"

# 路由是否存在:抓到 c_docs_page_title 即存在
"$CHROME" --headless --disable-gpu --no-sandbox --virtual-time-budget=9000 \
  --dump-dom "http://127.0.0.1:PORT/index.html#/en/essay/" \
  | grep -o 'c_docs_page_title[^>]*>[^<]*'

# 侧边栏条目:抓 c_euv_sidebar_link 之后的 href
"$CHROME" ... --dump-dom "http://127.0.0.1:PORT/index.html#/en/" \
  | grep -oE 'class="c_euv_sidebar_link[^"]*"[^>]*>|href="#/[^"]*"' | head -40
```

`--virtual-time-budget` 是必需的:wasm 需要时间初始化,不等待就 dump 只会拿到空壳。

确认「某 locale 的导航 100% 带前缀」:

```bash
grep -oE 'href="#/[^"]*"' /tmp/dom.html | sed 's|href="#||;s|"$||' | sort -u \
  | grep -vE '^/(en|ja|ko|zh)/' || echo "all locale-prefixed"
```

图片是否真的加载成功:euv-docs 用 `data-loaded` 属性控制图片加载前的占位,
`<img src="markdown-images/x.png" data-loaded="1">` 即完成加载。

## 首页 actions 的 locale 正确性

`actions[].link` 里的站内链接在每份 locale 首页中**各自写死**,不做前缀推导。
四份首页都写 `/appreciate.html` ⇒ 在 `/en/` 点按钮跳到中文页。逐语言改成
`/<locale>/appreciate.html`。外部 `https://` 链接不受影响。

注意 `mailto:` 作为 hash 路由会 404 —— 框架只对 `http(s)://` 前缀做外链特判,
`link:` 值一律当内部路由处理。

## 本地构建脚本 PATH 回退模板

内容仓库的 `./build.sh` 不要写死 CI runner 路径:

```bash
if   [ -n "${CARGO_HOME:-}" ];  then CARGO_BIN_DIR="$CARGO_HOME/bin"
elif [ -d "$HOME/.cargo/bin" ]; then CARGO_BIN_DIR="$HOME/.cargo/bin"
elif [ -d "/root/.cargo/bin" ]; then CARGO_BIN_DIR="/root/.cargo/bin"
else echo "build.sh: cannot locate a cargo bin directory" >&2; exit 1
fi
export PATH="$CARGO_BIN_DIR:$PATH"

# sccache 只在真的存在时导出;存在时必须关掉 incremental
if [ -x "$CARGO_BIN_DIR/sccache" ]; then
    export RUSTC_WRAPPER="$CARGO_BIN_DIR/sccache"
    export CARGO_INCREMENTAL=false
else
    unset RUSTC_WRAPPER || true
fi
```

`sccache` 遇到 `CARGO_INCREMENTAL=1` 会直接报错退出,所以两个变量要成对设置。
