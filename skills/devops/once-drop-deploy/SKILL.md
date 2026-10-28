---
name: once-drop-deploy
description: Use when deploying, rebuilding or debugging the once-drop app on this host (/home/web/once-drop, /home/shell/once-drop.sh, once-drop.ltpp.vip). Covers log/state layout, staging cleanup, JWKS mirror, and deploy verification.
---

# once-drop 部署与排障

**本机部署**: `/home/web/once-drop`(git,HEAD `a1df09d`),部署脚本 `/home/shell/once-drop.sh`,
域名 `once-drop.ltpp.vip` / `once-drop.devhub.vip`,后端 `127.0.0.1:9100`
(容器 `release_once_drop_server`,network `once-drop`)。

**入口**:`/root/scripts/once-drop-deploy.sh`(包装脚本,写日志 + 记 commit),
实际部署逻辑在 `/home/shell/once-drop.sh`。

```
/root/scripts/once-drop-deploy.sh   -> /home/shell/once-drop.sh
                                    -> /var/log/once-drop/deploy-<ts>.log
                                    -> /var/lib/once-drop/deployed-commit
```

## 坑 1:脚本目录不能留任何产物

**症状**:部署跑完 `/home/shell/` 里多出日志、commit marker 等文件。

`/home/shell` 是**脚本目录**,不是产物目录。产物一律去:

| 用途 | 位置 |
|---|---|
| 部署日志 | `/var/log/once-drop/deploy-<ts>.log`(logrotate prune) |
| build 日志 | `/var/log/once-drop/build-<ts>.log` |
| 当前日志路径指针 | `/var/lib/once-drop/deploy-current` |
| 已部署 commit | `/var/lib/once-drop/deployed-commit` |

`/etc/logrotate.d/once-drop`:daily / rotate 14 / compress / copytruncate。

**已清理的历史遗留**(2026-10-28):`/home/shell/once-drop*.log`、`once-drop.deployed-commit`、
`once-drop.sh.bak.*`、`/root/once-drop-build.sh`、`/tmp/{run_build,server_build,host_check}.sh`、
`/tmp/oncemap`、`/tmp/baked-*`、`/home/web/once-drop/data/release/web-dist.bak.*`。
旧日志已挪到 `/var/log/once-drop/legacy-*`。

## 坑 2:staging 目录必须在 /tmp,且 trap 清理

前端构建先输出到 staging 再 swap 进服务目录。staging 用 `mktemp -d`:

```bash
STAGING="$(mktemp -d "${TMPDIR:-/tmp}/once-drop-web-dist.XXXXXX")"
trap 'rm -rf "$STAGING"' EXIT INT TERM
```

放 `/tmp` 而不是 release 目录:构建失败时不会在 release 目录里留下"看起来像部署产物"的目录。
trap 覆盖**所有退出路径**(构建失败、Ctrl-C、被 kill)。

**swap 只能换内容,不能换目录**:容器 bind-mount 的是 inode,`rm -rf` 掉目录再新建 → 容器
仍读旧 inode,站点继续发旧 bundle,新 bundle 躺在盘上没人用。

```bash
find "$WEB_DIST_DIR" -mindepth 1 -delete
cp -a "$STAGING/." "$WEB_DIST_DIR/"
```

## 坑 3:cp -a 会把源目录权限盖到目标

`cp -a "$STAGING/." "$DIR/"` 里 `src/.` 这种写法会把**源目录自身**的 mode 应用到目标目录。
staging 是 `mktemp -d`(700),于是服务目录 `web-dist` 悄悄从 755 变成 700。

修法:swap 前记下原权限,swap 后还回去。

```bash
WEB_DIST_MODE="$(stat -c '%a' "$WEB_DIST_DIR")"
find "$WEB_DIST_DIR" -mindepth 1 -delete
cp -a "$STAGING/." "$WEB_DIST_DIR/"
chmod "$WEB_DIST_MODE" "$WEB_DIST_DIR"
```

容器内以 root 跑(root uid 0),700 不会立刻暴露 —— 但 nginx / 其它非 root 进程就读不到了。

## 坑 4:JWKS 镜像要手写

`www.googleapis.com` 在本机**不可达**(DNS 解析得到 IPv4 但连接超时)。前端校验 ID token 需要
Google 的公钥集,拿不到就**所有登录 401**,而且没有别的报错。

`/root/scripts/refresh_google_jwks.sh` 从 git 协议拉镜像(`github.com/vshengbro/google-jwks.git`)
—— 该仓被 GitHub spam 检测标记,raw file host / CDN 全部 404,**只有 git 端点能用**。

写出的 key 文档路径是 `/home/web/once-drop/data/release/web-dist/assets/google-jwks.json`,
**必须在 swap 之后写** —— swap 会 `find -delete` 清空目录,swap 前写的会被删掉。

校验:文档里 `keys` 非空且每条都有 `kid`/`kty`/`n`,否则**不写**(拿空文档覆盖好文档 = 全站登录坏掉)。

## 验证一次部署没留垃圾

```bash
# 1. 部署前后 diff 脚本目录
ls -la /home/shell > /tmp/a.txt
bash /root/scripts/once-drop-deploy.sh
ls -la /home/shell > /tmp/b.txt
diff /tmp/a.txt /tmp/b.txt          # 必须为空

# 2. staging 没泄漏
ls -d /tmp/once-drop-web-dist.*      # 必须 No such file

# 3. 服务正常
curl -sS http://127.0.0.1:9100/api/health
curl -sS -o /dev/null -w '%{http_code}\n' https://once-drop.ltpp.vip/
```

**故障路径也要测**:故意用不存在的 image 触发构建失败,确认 trap 仍清掉 staging
(`ls -d /tmp/once-drop-web-dist.*` 仍为空)。只测成功路径会漏掉 trap 写错的情况。

## 端口 / 容器

| 东西 | 值 |
|---|---|
| 后端 | `127.0.0.1:9100` |
| 容器 | `release_once_drop_server` / `release_once_drop_postgresql` |
| network | `once-drop` |
| PG | `postgres:17-alpine`,挂 `/var/lib/postgresql/data`(**PG17 布局,不要改成父目录**) |
| nginx vhost | `/www/server/panel/vhost/nginx/once-drop.conf` |

`www` 用户**不在 docker 组**,跑不了 docker —— 部署脚本需 root 跑。

## 权限约定

`/home/shell` 下脚本统一 `www:www 755`。改脚本后记得 `chown www:www && chmod 755`
(用 `write_file`/`patch` 改会变成 `root:root 700`)。

## 相关文件

| 文件 | 内容 |
|---|---|
| `/home/shell/once-drop.sh` | 真正的部署逻辑(pull → 前端构建 → swap → JWKS → 起容器) |
| `/root/scripts/once-drop-deploy.sh` | 包装:写 `/var/log/once-drop` + 记 `/var/lib/once-drop/deployed-commit` |
| `/root/scripts/once-drop-build.sh` | 本机 build 镜像(日志在 `/var/log/once-drop`) |
| `/root/scripts/refresh_google_jwks.sh` | 拉 Google JWKS 镜像到服务目录 |
| `/etc/logrotate.d/once-drop` | `/var/log/once-drop/*.log` daily/rotate 14 |
