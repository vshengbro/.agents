# 生成的文档站:locale 配置契约与验证

适用于「build script 从 README.md frontmatter 生成整个站点」这一类仓(euv-docs 一族):
内容是 markdown,站点配置在 `<SRC_DIR>/../README.md` 的 frontmatter 里,build.rs 在编译期
把它 codegen 成 `docs_gen.rs`。

## 1. 配置契约:`dir` 是每个 locale 的必填项

最小可用形态 —— **每个 entry 必须同时有 `prefix`、`dir`、`label`**:

```yaml
---
site:
  title: <site title>
locales:
  - prefix: /          # URL 前缀
    dir: zh            # 内容目录(相对 <SRC_DIR>)—— 必填
    lang: zh-CN
    label: 简体中文
    title: ...
    footer: ...
    toc_label: ...
    prev_label: ...
    next_label: ...
    navbar:
      - { text: 首页, link: / }
  - prefix: /en/
    dir: en
    ...
---
```

`dir` 必填的**理由**要写进注释:引擎拒绝猜测一个 locale 的内容在哪。早年的实现对 `/` 硬编码
过 `zh` 回退,结果产出一个只有一页、且没有任何报错的站点。显式声明把这个失败变成 build error。

## 2. 一个内容目录只能对应一个 URL 前缀

页面的 locale 由**文件路径的第一段**匹配配置里的 `dir` 决定,匹配用 `.find()` ——
**先声明者胜出**。所以两个 locale entry 声明同一个 `dir`,不会两份都拿到页面:
第一个前缀认领该目录,第二个 locale 拿到零页面 + 空 sidebar。

推论(踩过的坑):想让同一份内容同时挂在 `/x/` 和 `/zh/x/` 两个 URL 家族下,
**加一条共享 `dir` 的 alias 配置是不够的** —— 它会构建成功、CI 全绿、然后每个页面 404。
这需要引擎侧支持「一个 dir 多个 prefix」。

诊断方式:看生成的 `docs_gen.rs`(locales 列表 + route 列表),不要只读配置。
配置文件读起来完全正常。

反向歧义也要处理:**两个不同 `dir` 声明同一个 `prefix`** 是硬错误(两边都会发出 `/x`,route 冲突),
不能静默挑一个。

## 3. 验证「生成结果」而不是「构建退出码」

构建 exit 0 只说明没报错,不说明生成对了。三个必查:

```bash
# 1. locales 非空,且数量/prefix 与配置一致
find <target>/build -name docs_gen.rs -newer <marker> | head -1
grep -o 'prefix: "[^"]*"' <that-file>          # 期望看到每个 locale 一条
grep -c 'DocsLocale {' <that-file>              # 数量对不上就是有 entry 被丢

# 2. 关键 route 确实存在(尤其是多前缀/alias 场景)
grep -c 'route: "/ltpp/"' <that-file>
grep -c 'route: "/zh/ltpp/"' <that-file>       # alias 场景必查,见 §2

# 3. 站点真的能加载:无 panic、无 unreachable
#    serve dist/ + 浏览器加载,看 console。
#    典型失败签名:index out of bounds / Uncaught RuntimeError: unreachable
```

**console 必须干净。** 一个带 panic 的 WASM 包可以构建成功、页面 200、所有资源 404 fallback 都正常 ——
只有 console 里那条 panic 揭示真相(见 SKILL.md §9「numeric gate passing ≠ artifact correct」)。

## 4. 增量构建陷阱

`cargo:rerun-if-changed` 一般只监视内容目录,**不监视 `<SRC_DIR>/../README.md`**。
只改 frontmatter 不改 markdown 时,build script 不会重跑,`docs_gen.rs` 是旧的。

```bash
touch build.rs          # 强制重跑 build script
```

同理,验证前确认你看的是本次改动生成的文件:比对 `docs_gen.rs` 的 mtime 与你的改动时间。
共享 target dir 时 `Finished in 0.03s` 表示全部命中缓存 —— 那是「没有重新编译」,不是「验证通过」。

## 5. 内容树的整洁性

- 内容树根目录下、不属于任何 locale `dir` 的 `.md` 文件会同时产生两处问题:它们不在任何
  sidebar 里,且如果内容与某个 locale 目录重复,会发出**冲突 route**。
- 合并/迁移内容后,跑一次「根目录残留 + 与 locale 目录重名文件」对账:

```bash
git ls-files 'docs/*.md'                                    # 根目录直接文件,应为空
diff <(git show HEAD:docs/README.md) docs/zh/README.md     # 是否只是重复
```

## 6. 删除重复文件前先确认 remote 安全

站点内容仓里的重复页面删除用 `git rm`(保留历史),确认内容已在目标处落地再删。
删远程仓 / 删分支是另一回事,需要单独授权。