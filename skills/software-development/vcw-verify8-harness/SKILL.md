---
name: vcw-verify8-harness
description: "Use when verifying vice-city-web via CDP. Probe traps."
version: 1.1.0
author: hermes-curator
metadata:
  hermes:
    tags:
      - verification
      - cdp
      - browser-automation
      - game-testing
    related_skills:
      - verifying-against-a-real-gate
      - delegated-result-verification
      - verifying-before-dispatching-repairs
---

# Verifying vice-city-web (`/Users/sqs/code/vice-city-web`)

Rust + WASM (euv) single-player GTA-V-style game. Read-only acceptance work runs
through `tools/verify8/` (8 workers, ports 9340-9347) plus ad-hoc CDP scripts.

## When to Use

- Running or repairing the 8-worker acceptance suite (`tools/verify8/`) for this repo
- Writing any ad-hoc CDP probe against `__VCW_DEBUG__` / `__vcw` / `__vcw_probe`
- Reviewing an agent's "the app is broken" claim before acting on it
- Judging whether an acceptance FAIL is a real defect or a measurement artifact

Related: `verifying-against-a-real-gate`, `delegated-result-verification`,
`verifying-live-state-in-a-persistent-session`, `systematic-debugging`.

**The single most expensive mistake in this project is declaring a defect from a
measurement artifact.** Three separate "defects" (walking stutter, vehicle
steering, sprint speed) were harness artifacts, not bugs. Before reporting any
anomaly, prove the *channel* is valid — see "Validate the channel first" below.

## Build and deploy

```bash
cd /Users/sqs/code/vice-city-web
export CARGO_TARGET_DIR=/Users/sqs/Library/Caches/cargo-target/vcweb
cargo build --release --target wasm32-unknown-unknown
wasm-bindgen --target web --no-typescript --out-dir www/pkg --out-name vice_city_web \
  "$CARGO_TARGET_DIR/wasm32-unknown-unknown/release/vice_city_web.wasm"
```

The wasm is **not** in `./target`. Omitting the `export` (or the var not being
inherited by a subagent's shell) makes `wasm-bindgen` fail with
`failed reading 'target/.../vice_city_web.wasm'` even though `cargo build` succeeded.

**Always confirm the artifact is newer than the sources** — otherwise you measure
an old build:

```bash
stat -f '%Sm %N' -t '%H:%M' www/pkg/vice_city_web_bg.wasm src/*.rs | sort
```

Static server (share it; don't restart it if already up):

```bash
cd www && nohup /Users/sqs/.hermes/hermes-agent/venv/bin/python3.11 \
  -m http.server 8877 --bind 127.0.0.1 > /tmp/v8877.log 2>&1 &
```

## Interpreter

Always `/Users/sqs/.hermes/hermes-agent/venv/bin/python3.11`.
Bare `python3` resolves to Xcode's 3.9 (no numpy); `~/.local/bin/python3.11`
also lacks numpy. numpy 2.4.3 lives only in the Hermes venv.

## Chrome flags (software rendering)

```
--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader
```

Under SwiftShader rAF runs at **~1.7 fps** (measured median 0.5833 s/frame).

## 浏览器纪律:一个窗口,复用 tab,不开新实例

**用户硬规则(2026-10-07):「打开浏览器禁止使用新窗口,应该复用最开始的窗口去新建tab」。**

`tools/verify8/verify8.sh` 的原设计是 **8 个 worker 各起一个独立 Chrome**(端口 9340-9347)——这**违反**这条规则。实测代价已经付过了:某一棒写手在追缺陷 3 时连续换端口 9351 → 9352 → 9354 → 9355,**每换一个就是一个新窗口**,最后 6 个 Chrome 实例同时开着,收尾时报「探针反复 socket 超时」而实际上是自己开的窗口太多。

**正确做法:**

- **一个 Chrome 实例 + 一个 tab**。整轮验收在这个 tab 里跑完,需要换页面就 `goto_url()` 复用它。
- 需要并���采样多条测项时,用**同一个 tab 内重置游戏状态**(刷新或重新导航),不要新开窗口。
- 端口是**历史实现**,不是需求。要复用单窗口就别用端口区分 worker。

**遗留清理(2026-10-07 已执行):** 杀掉 9350/9351/9352/9353/9354/9355 六个残留实例。下次发现机器上 Chrome 实例数异常,先查:

```bash
ps aux | grep -c "[C]hrome"
lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null | grep -E "93[0-9][0-9]"
```

**`browser_exec` 的 profile 锁 ≠ 不能用浏览器。** `~/.hermes/config.yaml` 里 `use_real_profile: true`,你的 Chrome 开着时会持有 `Login Data` / `Web Data` 的写锁,于是 `browser_exec` 报 `profile lock ... write lock`。两条出路:

1. **代理层不行就用 `computer_use`** —— 它驱动屏幕上**已运行的**窗口、走 AX tree,根本不碰 profile 库。`capture` 必须同时给 `pid` + `window_id`(只给 `window_id` 返回 0x0 + `capture targeting requires both`)。`list_apps` 对运行中的 app 可能返回 `windows: []`,`list_windows` 才可靠。
2. **改配置**(推荐,验收本地 WASM 不需要登录态):把 `~/.hermes/config.yaml` 的 `use_real_profile` 改成 `false`。**agent 改不了这个文件** —— patch 会被拒(`Refusing to write to Hermes config file`),必须用户本人改,或 `hermes config`。

**但要分清「你的浏览器」和「测试浏览器」。** `computer_use` 驱动的是**用户正在用的** Chrome 窗口(实测正开着 Kimi AI 官网、带真实登录态)。拿它跑验收会占用用户的窗口、加载测试页面、抢 tab strip——这跟用户「不要新窗口」的意图正好相反。**验收本地 `127.0.0.1:8877` 应该用 Hermes 自己的浏览器后端,不是用户的 Chrome。**

## The measurement traps (each one cost a wrong diagnosis)

1. **`__VCW_DEBUG__` publishes every 3 frames.** Sampling it via `wait_frames`
   reads a stale value and reports false "stuck" readings. Observed frame
   sequences like 267/270/273/276 are throttle artifacts, not gaps. Sample the
   per-frame HUD channel and report frame-number contiguity as evidence.

2. **`{speed: N}` is a time-warp multiplier, not walk speed.** It writes
   `game.speed_scale`, which is assigned at `game.rs:4522` and **never read** —
   a dead field. 1x and 8x are bit-identical. Measure speed from `|v|` or dx
   per frame instead.

3. **`afterStatic` / `afterVertical` are `[x, z]` arrays published one phase
   apart.** Differencing them across snapshots mixes frames.

4. **`charBox` is two-point form** (`[feet.x, feet.y, crown.x, crown.y, depth]`).
   Facing the camera, `feet.x == crown.x` and the box width is 0.

5. **Read `__vcw` as one atomic snapshot** — `v = await s.st()`, then take all
   fields from `v`. Repeated cross-line `v["door"]` reads hit the write window
   between the 3-frame publishes and raise `KeyError` on a half-written object.

6. **Sky is not black.** Luma-range / non-black-fraction gates pass on a
   gradient sky. A sky-blue character region can be statistically identical to
   its surround (in-box mean 193.6 vs out-of-box 193.3) while being obviously
   distinct to a human. Only pixel *differences* or vision are trustworthy here.

7. **Results JSON schema is `{"worker": ..., "results": [{"name", "ok", "note"}]}`
   — the field is `ok` (true / false / null), not `verdict`. Parsing the wrong
   key yields a bogus 0 PASS / 0 FAIL / all-SKIP summary.

8. **Subsequent runs delete prior results.** `cp -r results results_prevN` before
   every rerun, or you lose the baseline you were comparing against.

8b. **A fix invalidates the suite that graded it — repair the harness before
   you re-baseline, or every post-fix reading is a false FAIL.** The
   expectation tables are hard-coded key bindings, and a binding fix moves
   the thing they assert. After a commit that rebinds a key or deletes a
   feature, the suite now tests a function that no longer exists and reports
   FAIL against a perfectly correct build. Sequence per round:
   (a) grep the suite for the old binding **and** the suite's README truth
   table -- prose tables drift as fast as the code; (b) rewrite both to the
   post-fix wiring, read from source, not from the previous verdict's note;
   (c) only then rebuild the wasm and take the post-fix baseline.
   **Date-stamp the saved results against the fix commits before trusting
   any P/F tally as a baseline**: a `results_prev_final/` whose mtime predates
   the fix commits is a *pre*-fix tally, so comparing a post-fix run against
   it manufactures a regression that does not exist. When a verdict names a
   feature that the diff deleted, that is suite debt, not an app defect.

9. `tac` is not on PATH in this environment. Use `git log --format=... | tail -r`
   or Python.

10. **`__VCW_DEBUG__` is the SLIM visibility channel, `__vcw` is the full
    snapshot.** `__VCW_DEBUG__` only carries `charVisible/charBox/
    afterStatic/afterVertical/afterDynamic/nearShapes/...` — it has **no
    `playerY`, no `route`, no `afterStatic` JSON of the stair state**. Anything
    about vertical position or the walk route must read `window.__vcw`.
    Both are **already-parsed JS objects**, NOT JSON strings: `JSON.parse(
    window.__vcw)` throws `SyntaxError: "[object Object]" is not valid JSON`.

11. **A teleport request must NOT carry `safe` unless it also carries
    `walk`.** `apply_teleport_request` hits the safe branch first and
    `return`s unless `wants_walk` is true, so `{x, z, safe: true}` sets
    invincibility and **silently drops the teleport** — the player never
    moves and the probe looks like a broken channel. Use `{x, z}` to
    teleport, then `{walk:true, dx, dz, safe:true}` to walk.

12. **Per-frame travel must be measured against the TRUE rAF count, not the
    hook's `frames`.** The hook publishes every 3rd frame, so differencing
    two hook reads spans 3 frames. Wrap `requestAnimationFrame` to count
    real callbacks, then `h = total_displacement / raf_count`.
    Measured here: **0.613 m/frame at ~1.1 fps** (implicit dt 0.133 s) —
    which is `WALK_SPEED 4.6 x 0.133`, i.e. the app integrates with a
    LARGER dt than `simulate`'s own `delta.min(FIXED_DT * 4 = 0.0667)` cap
    implies. That 2x discrepancy is unexplained and is the reason a single
    horizontal move crosses 1.36 stair treads in one step; any stair/step
    logic must tolerate a long frame.
    **Settled (measured 2026-10-02):** the effective per-frame dt really is
    ~0.131 s — walk reads 0.6 m/frame with `vel = -4.5998` (= `WALK_SPEED`),
    sprint reads 1.1 m/frame with `vel = -8.3999` (= `RUN_SPEED`). The HUD's
    own `frame {n}` field advances by exactly 1 per recorded row, so each
    row IS one simulate() frame. Do not re-derive dt from CDP polling gaps.

13. **The ONLY gap-free per-frame channel is the HUD DOM (`#vcw-hud`).**
    `format_hud` runs **every frame** and writes `xyz {x:.1} {y:.1} {z:.1}`
    plus `frame {n}`. An in-page rAF recorder that samples `window.__vcw`
    instead still gets the 3-frame-throttled values (measured: dframes were
    exactly `[0, 3]`, and a real peak of 3.20 read back as 3.1022). Parse the
    HUD text inside the rAF callback; `frame N` gives you the true frame
    index, so `dX / (N[i+1] - N[i])` is exact per-sim-frame displacement.
    Downside: coordinates are rounded to 1 decimal (tread tops 0.455/0.760
    still read as 0.5/0.8, so treads stay distinguishable).

14. **`__vcw_teleport` preserves Y — it cannot place you on a stair tread.**
    `apply_teleport_request` does `set_position([x, here[1], z])`, keeping the
    current height. Teleporting to a mid-stair XZ drops you at ground level
    *under* the treads (`on_tread=False`). To start on a tread you must WALK
    there (climb up, then turn around). A probe that teleports to a tread and
    concludes "descent is broken" is measuring its own setup.

15. **Walking straight along -X off the top tread falls into the stairwell.**
    In the LOFT, the upper deck is two L-shaped slabs: deck A covers
    `z >= 25.55`, the landing B covers `x >= 23.05`. The top tread is
    `x = [23.05, 23.50]`, so continuing -X leaves the landing and free-falls
    to the ground floor. Judge a climb by its **peak on the stair segment**,
    never by the final frame.

13. **The player fires on canvas `mousedown`, not on a key.** `fire_held` is set
    from a `mousedown` listener (`game.rs:4605-4613` carries a comment saying
    exactly this). Injecting `Digit2` / `KeyX` goes through `TRACKED_KEYS` and
    never touches it, so `fire_held` stays `false`, every shot misses, and
    "player fire is broken" looks true. Inject
    `Input.dispatchMouseEvent {type:"mousePressed", button:"left"}` at the canvas
    centre. Judge on `enemies[].hp` or `kills`; `mag` is a fine diagnostic but
    is consumed in a **one-frame window** (`hold_frames=1`), so read it in the
    next frame or nothing fires at all.

14. **Never judge look direction from image centroid or whole-frame
    cross-correlation.** Both were tried and both are invalid here: the
    centroid is the luminance-weighted centre of whatever is on screen, so it
    jumps whenever content enters or leaves the frame (measured: -1.87, -13.52,
    +33.51, +14.15 across four drags of the same direction); and a large yaw
    change rotates the whole scene, so whole-frame correlation aliases — a known
    +24px shift read back as -36. A correlation peak of 0 means "the
    whole-frame-translation assumption is false", **not** "nothing moved".

    Working method: take a **static world anchor**, project it through the
    game's own `view_projection`, and first prove the projection copy is faithful
    by matching it bit-for-bit against a coordinate the game reports itself
    (e.g. `charBox` centre). Then drag once and watch the anchor's screen x:

    ```
    drag 12px: dyaw=-0.0720  anchor 640.0 -> 634.5   (dx -5.50px)
    drag 24px: dyaw=-0.1440  anchor 640.0 -> 629.0   (dx -11.03px)
    drag 48px: dyaw=-0.2880  anchor 640.0 -> 617.6   (dx -22.38px)
    drag 96px: dyaw=-0.5760  anchor 640.0 -> 592.5   (dx -47.50px)
    ```

    Four gauges, all negative, strictly proportional to dyaw => mouse right
    moves the scene left => **direction is correct**. Cross-check analytically
    too: press W after the drag and compare the world displacement direction
    against the previous forward vector rotated by dyaw (must agree within a few
    degrees). `LOOK_YAW_SENSITIVITY = -0.006` is negative on purpose; the
    sign relationship lives in one place (`apply_look_delta`, documented as the
    sole view write entry) and must stay in sync with the doc comment above it.

15. **After any teleport, read the position back and abort if it missed.** A
    test route that never reached the stairs reported `peak_y=0.200` and read as
    "the fix regressed", when the player was 110 m away and had simply never
    walked to the stair foot. Assert arrival before starting a measurement.

16. **`python -m http.server` is single-threaded.** Eight Chromes booting at once
    exhaust its backlog and the affected workers die with
    `Connection reset by peer` / `Errno 54`. That is a harness failure, never an
    application result — rerun the affected workers on their own
    (`verify8.sh w4_keys w5_vehicle`) rather than letting the crash count as
    FAIL.

17. **This machine has neither `timeout` nor `gtimeout`** (no GNU coreutils).
    A subagent wrapping a probe in `timeout 600 probe.py` dies with
    `command not found: timeout` and burns a whole run. Tell agents to drop the
    wrapper and bound the script itself. Same class of failure as #16: a shell
    error is never an application result.

18. **Never run two writers against this working tree — unless their scopes are
    provably disjoint.** It is one shared checkout, so a second agent commits
    whatever the first had staged. Observed: two fix agents both editing
    `src/interior.rs`, the first landing `cf0f3cc` (interior.rs +198/-4)
    while the second still had uncommitted work on the same file, and one
    commit swallowing another group's changes (`HUD_FIRST_PERSON` folded into
    a stair commit). So when fanning work out, the gate is **file scope, not
    agent count**:
    * *Disjoint* -> parallel is fine, but both agents must be told the other
      one's scope verbatim, must not run `git add -A`, and must show full
      `git status --short` on delivery as proof. (Repairing the acceptance
      suite in `tools/verify8/` alongside a `src/` fixer is the safe pairing.)
    * *Overlapping* (any second writer under `src/`, or a graphics agent that
      would touch the same crate the physics fixer is in) -> **sequence**.
      Queue the second one rather than racing it, because the commit it makes
      is whatever the first one happened to have staged.
    After any delegation returns, run `git log --oneline -3` plus
    `git diff --stat -- src/` before trusting any in-flight claim about the
    tree.

    **Check the tree is clean BEFORE dispatching the next writer, not only
    after the previous one reports.** `git status --porcelain` showing a
    modified tracked file under `src/` means an earlier writer has unlanded
    work; you cannot tell from the main agent whether that agent is still
    running, and a second writer committing into the same tree will land on
    top of it. Sequence explicitly: wait for the delegation result, then
    `git log --oneline -3` + `git status --porcelain`, and only then decide
    the next dispatch. The reverse order (dispatch, then inspect) is how a
    writer inherits someone else's half-finished file.

19. **A test fixture that does not match the real layout is a false regression
    test.** `197fa29`'s descent test built its slabs with `slab_world()`, whose
    upper slab stopped at the tread edge, so it passed while the shipping
    geometry in `game.rs:1196` roofed the whole stair run (`z` upper bound ran
    from `stair_end` to `hz`, so `support_height(23.7, 2.895)` returned 3.2 and
    descent was impossible by construction). When a physics fixture is added for
    a real scene, build it from the scene's own coordinates and assert the test
    **fails before the fix** — otherwise it pins the intended geometry instead
    of the actual one.
    **Fixed in `f9290e5`**: the second upper slab's z range is now
    `-hz ..= stair_end`, leaving the run open. The defect was a sign error
    present since `1ff7c38`, and the game's own `bldg_*_showcase.json` assets
    were correct the whole time — only the collision slabs were wrong. When a
    collision/visual disagreement shows up, read the asset before editing the
    solver; and prefer fixing the slab over teaching `step_down_along` to cope
    with a surface the player can see through, which desyncs collision from
    the asset permanently.

20. **A fallback sweep bounded by the frame-start height overwrites a
    same-frame ascent.** The sprint-on-stairs failure was not a coarse
    substep: `support_along_frame` already splits adaptively (a 1.13 m sprint
    frame became 6 x 0.19 m) and the ascent correctly reached 1.370. The next
    stage, `step_down_along`, bounded its sweep at `frame_start_y - 0.355`
    (= 0.100) while the ground floor sits at 0.150, so any long frame swept it
    and reset the player to the ground. Fixed in `e284801`/`6667fb2` by
    skipping the step-down pass when the ascent already raised `y` this frame —
    climbing a tread and stepping down one are mutually exclusive in a frame.
    Threshold measured at a stride of ~0.75 m: walk (0.6 m) was always safe,
    sprint (1.1 m) never was. **Re-test any swept-support change at the fastest
    speed the game allows, not just at walk speed.**

42. **零输入下的匀速位移,几乎总是「解算扰动被逐帧重复施加」,不是输入 bug。**
   2026-10-12 本仓实测:玩家零输入恒定沿 +Z 漂 0.094 m/帧(5.66 m/s),
   `x` 精确不动、`vel=[0,0]`、`walkReq=[0,0]`、`__vcw_teleport` 未定义。
   按 S 仍朝 +Z 走、按 W 时 `vel=[0,-4.6]` 而 z 反而增加 ——
   **速度方向与位置写入互相矛盾,这条矛盾本身就是定位线索。**

   定位靠逐段插桩,而**插桩必须打在「读」的位置,不是「写」的位置**:
   我第一轮把 `[X_DYNBODY]` 打在 `resolve_dynamic_bodies(game)` **之前**,
   于是读数显示推进发生在它之后,实际发生在它内部,白白多花一轮。
   判据:相邻两个探针之间只有一个被调用的函数时,那个函数就是嫌疑人。

   机制不是笔误:动态碰撞层 `resolve_all` 解算的是**互相让位的扰动**,
   而它每帧重新求解。行人按各自世界坐标建体,相对几何逐帧相同 →
   推出同一个分离向量 → 净位移累加成单向棘轮。**修法是区分「解算结果」
   与「解算扰动」**:静态层把人从墙里推出来必须保留,人群让位只在实体
   自身在动时才施加(`PLAYER_PUSH_MIN_SPEED` / 死区)。

   **写在本仓的回归测试必须先验证它会红。** 我第一版 fixture 用了
   0.79 m 间距,而半径和是 0.75 m —— **根本没重叠**,于是把门槛去掉测试
   照样绿,等于什么都没守住。修法是按实测的棘轮量把行人收到 0.60 m。

43. **「站着不动就被打」先读 AI 源码再判缺陷。** 本仓实测零输入 1.2 s
   掉 6 HP、13→15 个敌人。`enemy.rs` 的 `decide` 里写明
   `Faction::Thug => true` —— 混混**一开始就是敌对的,不需要理由**
   (警察才需要 `wanted`)。这是设计,不是缺陷。判据:敌对表里有显式
   faction 分支且带注释说明,就不是漏判;只有「所有 faction 一律 hostile」
   且无出处才该怀疑。

43. **本仓 headless 页面对 `Runtime.evaluate` 极敏感:任何一次 `js()` 探测都可能把
    页面挂死,表现为后续所有 CDP 读超时。** 2026-10-12 连续踩中 3 次
    (`__vcw_teleport={probe:true}` 重探针、`window.__vcw` 枚举、查 canvas rect
    之后)。规则:
    - 位置/帧号/HP 一律走 **HUD `innerText`** 通道(per-frame 更新,自带时间轴),
      不要用 `__vcw` 一次性快照做连续采样。
    - 启动参数用 `?res=0.3` 压低分辨率(0.5 时 fill rate 足以拖死 headless)。
    - 一旦 `snap()` 抛 `TimeoutError`,直接 `pkill -9 -f vc-chrome-*` 重开,
      不要在同一 socket 上重试 —— socket 已经死了。
    - 用 `c.call("Runtime.evaluate", ...)` 直接拿值比 `js()` 少一层封装,同样会挂。

44. **「转向无效 / 输入无效」的判定必须先证伪测量通道。** 2026-10-12 我在车上
    测出 `dyaw = 0.0000`(连按 3 轮、每次 20 帧),一度以为 `STEER_MIN_SPEED`
    门限或 `steer` 符号写反;实际只是**在旧快照上读 `playerYaw`**,而那一帧
    采样早于按键生效。改成长按 8 秒 + 每秒重读,实测 −0.52 rad/s,转向完全正常。
    同一次测试还确认 A→左 / D→右 与 `steer`(正=右转)契约一致。
    —— 任何读到精确 `0.0000` 的「物理量没动」,先怀疑采样,再怀疑代码。

45. **`window.__vcw_teleport` 是多用途注入通道,不要只当传送用。** 已确认:
    `{hold:true}` = 开一枪(弹匣精确 −1);`{safe:true}` = 无敌(HP 稳定 100,
    HP 掉到 0 后仍被拉回,适合跑长距离瞬移检测)。用它造前置条件比硬等自然死亡
    快得多 —— 上一次测瞬移,21 处 >1m 的「跳变」里 20 处是死亡重生,只有把
    safe 打开才能把重生噪声彻底排除。

46. **「走到远处城市变空」几乎总是 NPC 没有跟着流式换块,而不是 bug 在别处。**
   2026-10-12 实测:车开到 `z = 651`,最近行人 **563 m**、最近敌人 **566 m**。
   `step_streamed_surface` 只换地面/水面,`populate_combatants` 一辈子只在
   初始化跑一次。诊断手法:连续传送几个远点,每点读 `nearest NPC 距离`
   —— 距离随位置线性增长就说明 NPC 没跟过来。
   修法要点:共用 `STREAM_REBUILD_STEP` 触发(不额外花一次判定);生成原点用
   **街道对齐后的格子中心**而不是玩家脚下,否则同一街区来回走几步就换一批
   行人,看着像瞬移;相位由街区坐标算出,同一街区永远同一批。
   踩过的坑:我给敌人替换加了 `if wanted.get_stars() == 0` 的条件,理由是
   「警察由 `deploy_police` 重派」—— 结果打过一场之后玩家永远带星,混混就
   永远留在出生点。**别给「整体替换」加条件**,`deploy_police` 本来就是
   每帧按星数补齐,不需要你保护。

47. **回归测试要驱动「有守卫的那一层」,否则守卫本身写错也测不出来。**
    我第一版 `npcs_follow_the_streamed_blocks` 直接调抽出来的 helper
    (`repopulate_combatants_at`),helper 绿了,但 Game 层多包了一层
    `if stars == 0` 照样漏 —— 测试压根碰不到那个分支,浏览器才暴露出来
    (行人 14 m / 敌人 566 m)。
    规则:如果生产代码在 helper 之外还有条件分支,要么让测试驱动那一层,
    要么把分支删掉让它**结构上不可能写错**。这次选了后者:敌人无条件整体
    替换,`deploy_police` 天然兜底。

48. **高速物体 vs 小目标的判定必须是扫掠(线段),不能只测帧末点。**
   2026-10-12 实测:24 m/s 的车从行人旁 2.3 m 掠过,判定圈明明够宽
   (`CAR_HIT_RADIUS` 2.0 + `PED_RADIUS` 0.35 = 2.35 m),20 s 零次命中。
   一帧走 0.4 m,长帧能走 1 m 以上,行人正好落在两个采样点之间就漏掉了。
   判据:凡是有速度的物体参与碰撞判定,先问「一帧走多远 vs 目标直径」。
   走过的距离超过目标尺寸就必须扫掠 —— 本仓的修法是
   `point_to_segment_distance(point, prev_xz, this_xz)`。

49. **「警觉半径 / 反应半径」乘大于 1 的系数,会让目标永远追不上。**
   行人警觉半径本来 11 m,开车时被放大 1.8 倍 → 19.8 m 就开始横穿马路逃。
   而 24 m/s 的车转弯半径 46 m(`v / yaw_rate`,`yaw_rate = STEER_RATE /
   (1 + v·falloff)`),根本追不上一个横向已经跑开 4.4 m 的目标。
   判据:**任何「提前反应」的系数乘完,要拿目标速度和追击者的转向能力对表**,
   目标能跑出的距离必须小于追击者能拉近的距离,否则这个系数就是在
   「保证这件事永远不发生」。这类系数应当 ≤ 1。

50. **闭式公式推相对运动经常推错,逐帧模拟才和浏览器一致。**
   同一个缺陷我写了两版测试:
   - 闭式版:`reach = ped_speed * (catch_up / closing)`,算出 2.6 m > 判定圈
     2.35 m → 判定 FAIL。方向看起来对,但**结论和浏览器相反** —— 浏览器
     (修复后)测得最小间距 2.63 m,真实值确实略超圈,可是扫掠一加上就命中了。
   - 逐帧版:按 60 fps 推 300 帧,1.8 → 4.39 m / 0.85 → 2.11 m,与浏览器
     定性一致。
   原因:闭式公式假设了「追赶方向 = 逃离方向」,而行人逃离方向**垂直**于
   车行方向。规则:只要是**相对运动 + 有限转向能力**,就按帧模拟,别推公式。

51. **写「不应该命中」的对照断言前,先确认判定圈的语义。** 我断言
   「路径外 2.0 m 的行人不该被撞到」,测试红了 —— 但 2.0 m 正好在
   `CAR_HIT_RADIUS + PED_RADIUS` = 2.35 m 之内,撞到才是对的。是断言写错,
   不是代码写错。顺手把这条反过来写成正向断言(2.0 m 该撞 / 3.0 m 不该撞),
   判定圈的语义就固化在测试里了。

52. **「换了状态就把旧字段清空」的 setter,会把「先设后 advance」变成静默失效。**
   2026-10-12 实测:任务击杀段永远完不成(面板卡在 `take out the target`,
   撞死好几个敌人、现金涨到 $480,任务不变)。三处叠加:
   a) GOTO 段转 KILL 段时 `target_index` 还是 `usize::MAX`(还没「要干掉谁」),
      直接存进 mission → `index != usize::MAX` 恒 false;
   b) `set_target_enemy(i)` 写在 `advance(KILL, t)` **之前**,而 `advance`
      内部带一句 `set_target_enemy_opt(None)` —— 刚设上就被抹掉;
   c) 命中处理里的 `set_target_enemy(usize::MAX)` 想「标记完成」,实际把
      「目标是谁」自己删了。
   判据:**任何一个 setter 如果会清字段,就必须检查调用顺序**;读源码时
   看到 `advance` / `begin` / `start` 这类动词,先确认它内部有没有顺手
   清理。另外「用哨兵值表示没有目标」的字段,清成哨兵 ≠ 表示「已完成」。

53. **用哨兵值(`usize::MAX`)同时表示「没有」和「完成」,迟早会打架。**
   本仓三处都踩了:`unwrap_or(usize::MAX)` → `!= usize::MAX` 当成「有目标」,
   于是「主动清空」和「本来就没有」变成同一件事。改成 `Option<usize>` +
   `set_target_enemy_opt`,语义分开就再也说不清了。

54. **浏览器会话会耗尽:`js()` 用得越多,越要一开始就定好采样通道。**
   本轮页面挂了 4 次(第 5 次之后基本只能靠重新导航)。一开始就把
   「位置/HP/帧号走 HUD `innerText`,一次性状态走 `__vcw` JSON」分开,
   每次只做一件事,能省掉一半的重启。另外**子进程 Chrome 会静默退出**
   (上一轮的后台实例在下一轮已经没了),每轮都要重新确认端口在监听。

55. **`playerInsideCollider` / `collisionShapes` 是穿模验证的现成权威通道,别自己造。**
   `window.__vcw` 上有 `collisionShapes`(= 1769)和 `playerInsideCollider`
   (bool)。判据:传送 30 个位置 + 冲刺撞墙 20 次采样,`playerInsideCollider`
   全程 `false` 就是没穿模。同类的还有 `charBox`(像素包围盒)、`camOccluded`
   (相机遮挡)。有现成信号就别用截图比对。

56. **实体互相重叠用「两两最近距离」一次算完,不要逐对采样。**
   玩家 / 行人 / 敌人的重叠预算就是半径和(0.35 + 0.35 = 0.70 m)。
   实测:最近行人 3.16 m、最近敌人 17.8 m、最近行人对 5.40 m —— 全部远离
   预算,说明 `resolve_dynamic_bodies` 的分离在正常工作。

## Validate the channel first

41. **后台进程通知里的读数是一次独立运行,不是同一缺陷的两次观察 —— 永远不要把两条通知串成因果链。**
每个 delegation / background process 完成通知只包含**那一次探针运行**的输出片段,而每次运行有**自己的世界状态**:玩家位置、流式中心 `stream=(x,z)`、批次号 `bn`、帧号都可能完全不同。把两条通知当成「同一现象的前后两帧」去推因果,就是在比 dts 不同的两条腿 —— 是本 skill 反复警告过的那类错误的变体。

本轮实例(同一个「角色不展示」缺陷,两次探针):
```
d2b      : pos=(-23.91, 31.69)  bn=37   limbN=0    vis=T
d2_repro : pos=( 33.50, 35.55)  bn=100  limbN=13   vis=T  ink=42%→93%
```
我据第一条断言「肢体实例表始终是空的,走远后没重新填」,第二条直接推翻(`limbN=13`,`runs=2` 是连通人形)。**两次运行连批次号都不是同一批**(`bn=37` vs `bn=100`),根本不在量同一个东西。

推论:**单条通知内部的趋势**(同一 `pos`/`bn` 序列随帧的变化)是可用的证据;跨通知比较只有在你**显式核对了两边 `pos` / `bn` / `stream` 都一致**时才成立,否则一律标「不同次运行」。看到 `ink=42%→93%` 这种同一序列内的单调趋势才值得追,而它指向的是「角色占框比例异常放大」,不是「消失」。

`soft_limit_speed` "looked guilty" on inspection — it was already an identity
function. The real fault sat in a probe that produced plausible-looking numbers.
So: when a reading looks like a bug, confirm the probe can produce a *known-good*
reading before concluding. Ask what a healthy signal looks like and check you got
it.

**A "user sees X after moving for a while" report is a streaming-rebuild
report until proven otherwise.** Symptom class: something renders fine at
spawn and vanishes once the player has travelled far enough. The city rebuilds
its batch table when the streaming centre crosses a street, and the rebuild is
where anything that lived in the batch table can be lost -- so the trigger
word is "after moving", and the suspect is the rebuild path, not the renderer.

Two distinct failures live there, and they look identical from the player's
seat:
* **static objects left where they should not be** -- e.g. scatter placement
  adds per-instance jitter to a base offset that already sits at the edge of
  its legal band, so a +/-0.8 m jitter pushes instances into a region they are
  forbidden from (palms in the roadway). The base position is legal and the
  jitter is legal; only the sum is not. Test the **sum against the constraint**,
  never the jitter in isolation.
* **dynamic groups dropped on rebuild** -- when the static segment is swapped,
  everything after it in the table (player limbs, vehicles, pickups) must be
  re-placed at the new offset. Omitting that leaves an empty instance array for
  a group that is still logically live: the batch exists, its instance count is
  0, and the object silently stops drawing.

So when a report says "it disappears after I walk a bit", reach for the batch
table *before* the shading, the culling radius, or the model. Confirm it by
reading per-batch instance counts across a streaming-centre crossing, and by
checking whether the count drops exactly at the crossing. For the placement
variant, sample the generated positions and assert each against the exclusion
band directly.

### Sequential RNG over a traversal is not deterministic generation

The chunk rebuild advances one RNG cursor in traversal order, re-seeding at the
function entry each time. The output therefore depends on **how the traversal
happened to be ordered**, not only on the coordinates — so the same world
position can yield a different building or a different tree on a second visit,
and nothing in the code looks wrong while it happens.

The fix is coordinate-keyed seeding, and it is a design constraint on any
streamed world, not a local patch:

- Derive each chunk's seed from an immutable world seed **plus the chunk
  coordinate** (`hash(world_seed, cx, cy, cz)`), never from a running cursor.
- Draw terrain, buildings, vegetation, props, colliders and render instances
  from **one** per-chunk description. Two consumers each rolling their own RNG
  is how visuals and collision drift apart again — the failure mode already
  documented for the showcase slabs.
- Make the commit atomic: the visual geometry, the collider set and the draw
  batches must swap together. Swapping one before the others is precisely the
  class of bug that produces a player inside invisible walls, or an object that
  renders while nothing collides with it.
- Use separate load/unload radii (hysteresis) so a player hovering on a boundary
  does not thrash the chunk set every frame.

The acceptance gate is a **stable structure hash per coordinate**, compared
across first entry, unload-and-reenter, and page reload. Field-by-field equality
is the requirement; "it looked the same" is not evidence. Report the hash, not
a description.

While verifying, also assert the streaming centre moves with the player — a
window that never advances never reloads anything, and identical hashes would then
pass without having tested determinism at all.

Two further rules, both learned the expensive way:

**A geometric judgement needs two independent paths that agree.** Three separate
runs of "is the camera eye outside the room shell?" produced `5/8 outside, outBy
+1.969`, then `d wandering 2.4-4.3`, then `three segments byte-identical`. The
turning point was a run that computed the same verdict twice — once from a
hand-transcribed envelope, once from a measured one — and had both agree
(`inShell=True` everywhere, `outBy` negative). A single-path metric whose
derivation you have not read is not evidence. Get the threshold from source
(`interior.rs` room AABB), not from a probe, and compute it two ways.

**A fix verified at one operating scale is unverified.** The stair fix passed at
walk speed (0.6 m/frame) while sprint covers 1.4 m/frame — 2.3x — over treads
0.45 m deep. Re-measure every physics fix at the fastest speed the game allows,
and at a normal frame rate as well as the pathological one. Here the fix turned
out to be a genuine no-op at 60 fps (`substeps == 1` degenerates to the old
path), which is the property worth asserting in a regression test, not a
comment.

**Two agents disagreeing is a signal to fix the measurement, not to pick a
side.** When two runs contradict each other, the right move is to find the metric
that both can be checked against — not to report the newer number and dispatch a
fix. Twice this session a "defect" was dispatched to a writer on one run's
single reading and dissolved on the next.

## Sampling discipline

- Never use `wait_frames` for motion/change assertions under 1.7 fps.
- Drive sampling by the frame counter, not wall clock.
- Report `frame_gap` contiguity alongside any measurement.
- A harness failure (worker crash, `exit 143`, `ConnectionClosedError`, a
  subagent's wrong interpreter) is **never** an application PASS or FAIL — label
  it as harness.

42. **A "prescribed fix" from a prior agent can be exactly backwards — verify the premise before applying it, and calibrate against a KNOWN-GOOD frame.** Three consecutive misdiagnoses in one WebGPU port, each of which looked correct on paper:
- *Bug 1*: the depth remap loop indexed `out[8+c]`/`out[12+c]` thinking those were rows 2/3. In a **column-major** matrix they are **columns 2/3**, so clip.x/clip.y had their z coefficients halved — squashing the whole scene into a thin horizon band. Signature: flat field with a compressed sliver. Index rows as `r + c*4`.
- *Bug 2*: I told the agent to raise a window-recess constant because the detail measured sub-pixel. A **raycast** showed the glass had **0.0% self-visibility** (0 of 16,200 probes) — a sign inversion buried it 15 mm inside the solid wall. Raising the constant would have deepened the burial. The audit's "3 px at 40 m" measurement was real; its *cause* was wrong.
- *Bug 3*: I told it to negate the y row because WebGPU's NDC +Y points down. The camera **already produced a WebGPU-convention matrix**, so negating flipped it twice and rendered the world upside down. The resolution came from calibrating a **vertical luminance profile** against the verified-good WebGL2 control using identical code: sky-high/dark-low is correct, its mirror is not.
- *Also rejected*: a reported "genuine mesh break" that was actually a legitimately separate emissive part. Measured the parts before acting.

**Rules that generalize:** (a) when handed a fix from a prior finding, re-derive the premise by measurement before editing; (b) calibrate against a known-good artifact from the SAME pipeline, not against intuition about conventions; (c) a test must pin the *specific* wrong behaviour — "it compiles" passed while three separate matrix bugs shipped; (d) prefer one metric both states can be checked against over reasoning about which of two contradictory readings to believe. **And a self-referential trap:** `check_window_recess.py` had encoded the inverted sign as its invariant, so it certified the broken asset as healthy — a verifier can enshrine the bug it was written to catch.

## Bloom parity is a CROSS-BACKEND budget question, and vision misreads dark sky as a roof

Two measurements that cost real time in the WebGPU bloom port (2026-10-10).

**1. Vision will call open night sky an "overhead canopy/roof/bridge".** It was
wrong three separate times at three different camera positions, including one
where the camera was provably on a street axis looking straight down it. It is
not a framing failure and re-shooting from a different spot does not fix it.
Settle it numerically using the phase's OWN `sky_color` (src/render.rs):

| phase | sky_color | test |
|---|---|---|
| Night | `[0.045, 0.055, 0.13]` | upper band must read **B > R** |
| Dusk | `[0.95, 0.46, 0.36]` | upper band must read **R > B** |

Measured hue cosine vs `sky_color` was 0.96 for both, and the upper band's
vertical `|dLuma|` was 6-7x smoother than a mid-frame geometry strip -- two
independent channels agreeing with the renderer's own constants, against one
impressionistic one. **Before re-framing a shot because vision says "under an
overpass", check the sky hue against `sky_color`.** Vision also claimed the
world was "upside down" on the dusk frame; the same test refuted it (top band
was warm coral R 0.380 > B 0.292, matching dusk `sky_color`, not mirrored).

**2. "Is the glow strong enough?" is only answerable as a ratio between the two
backends at ONE camera.** A single frame can't distinguish "subtle bloom" from
"bloom 80x too weak" -- both look like small halos. What settles it: zero the
composite strength on BOTH backends (`webgpu/fn.rs bloom_composite_strength`
and `render.rs render_composite`), rebuild, re-shoot all four legs at the same
camera, and compare *added light*. Measured at one street camera:

```
                     WebGL2      WebGPU    GL/GPU
night  mean added    0.29629    0.00359    82.6x
dusk   mean added    0.25056    0.02265    11.1x
night  bloom/base    146.9%       1.9%
```

Both backends call the SAME `BLOOM_STRENGTH * emissive_gain.max(BLOOM_MIN_GAIN)`,
so a large ratio looked like a porting gap. **It was not. The 82.6x was the
REFERENCE being broken** — read the next section before acting on a cross-backend
ratio this large.

**A/B discipline that mattered:** compare in a scene-only crop. The bottom-right
minimap's moving traffic dots differ between runs and produced a
`min luma delta = -0.957` that looked exactly like bloom removing light.
Before believing a negative delta, print WHERE it is; 78 px in one minimap
corner is the harness, not the feature.

## 一个大比例差,先怀疑参照实现坏了 —— 静默失效的 uniform

上一节那张 `82.6x` 表是**错的结论**,而它的算术和测量全都是对的。真相是
**参照端(WebGL2)的 bloom 根本没在跑**,而它渲染出的画面看上去完全正常。

`get_uniform_location` 对一个着色器里不存在的名字返回 `None`,而
`uniform1f(None, …)` 是**彻底的空操作** —— 无警告、无异常、画面照常出图:

| 常量 | 传的名字 | GLSL 实际声明 | 后果 |
|---|---|---|---|
| `U_BLOOM_THRESHOLD` | `u_bloom_threshold` | `u_threshold` (`render.rs:1595`) | 阈值钉在 0.0,**整幅画面**被当成 bloom 图 |
| `U_BLOOM_DIR` | `u_bloom_dir` | `u_direction` | 方向 (0,0),可分离高斯塌成同纹素加权,**完全没有模糊** |

合成时再乘 `0.85 × 1.85 = 1.5725`,于是「WebGL2 的 bloom」= 整帧 × 1.57。
夜间整片粉彩青白、亮度远超预期 —— 那就是 bug 本身,肉眼可见。

修好后两个后端终于一致:超过阈值的像素 WebGL2 **0.2050%** vs WebGPU
**0.2129%**(比例 1.05x,不再是 82.6x)。

**通用规则:一个「某后端 X 倍强/弱」的测量,必须先证明参照端那条路径
真的在执行。** 静默失效的特征是「什么都不报错」,所以门禁全绿、validation
clean、截图非空 —— 所有既有信号都通过。可判定的做法:

- **写一条测试断言每个被 `get_uniform_location` 查过的名字,都在某段 GLSL
  里声明过**,并且验证它在旧的错值上**会失败**。一个从不在旧代码上变红的
  回归测试没有守住任何东西。
- **一个 CPU 上重建共享链路的模型,如果它与「坏掉的那一侧」一致而不是与
  另一侧一致,就把怀疑指向参照端** —— 这轮正是如此:重建预测两个后端都应该
  是 ~0.0023,WebGPU 命中,WebGL2 跑了 0.296。

**顺带:那道被怀疑「没移植」的 pass 其实什么都不做。** `render.rs:4651` 的
加法 glow pass 用 `depth_mask(false)` 但把 `depth_func` 留在 `LESS`,然后
**重绘完全相同的几何** —— 等深度通不过测试,整个 pass 根本不光栅化。实测贡献
**−0.00000**。**「这个 pass 看起来在做事」不是它做事的证据;量它的 ablation。**

## 多个写手共用一个 checkout:门禁读数会被并发编辑污染

本仓一个 checkout 上同时跑 4-5 个写手时,**任何门禁读数在树安静下来之前都
不可信**。本轮两次「回归」都是假的:一次 `182 vs 180`、一次 `230 vs 228`、
一次 doctest 失败,全都发生在别的 agent 正在重写 `src/const.rs` /
`src/game.rs` 的时候。

- **污染会同时制造假阳性和假阴性**,包括「树根本编译不过」这种一眼假的读数。
- **归因要按文件逐条数**,不要凭总量猜:
  ```bash
  cargo check --all-targets --message-format=short 2>&1 | grep "warning:" \
    | grep -oE "src/[a-z/_]+\.rs" | sort | uniq -c | sort -rn
  ```
  只有落在**你自己拥有**的文件里的计数才是你的;本次 `collision.rs` 的
  dead-code 警告就是本轮的,`const.rs` 的 159 条不是。
- **在一棵还在动的树上量出来的数字不要采信,也不要据此改代码** —— 重测,
  或者在隔离 worktree 里量(`git worktree add` + 只带自己那几个文件)。
- **派活时就说清这条**:「若门禁读数看着不对,先等并重测,不要假定是你造成的」。

**共享 checkout 的另一个真实风险:一个 agent 的 `git checkout` 会抹掉另一个
agent 未提交的工作。** 本轮发生过一次,幸而 diff 还在、随后恢复了。commit 前
用显式路径 stage,再 `git diff --cached --stat` 确认没卷进别人的东西。

## 重构后遗留的死代码本身就是门禁回归

把「圆近似」换成「真实轮廓」之后,旧的 `resolve_car` / `CAR_RADIUS` /
`soft_limit` 变成死代码,`cargo clippy` 立刻 +2。**死代码比没有代码更糟**:
它会诱导下一个人去调那个已经不再生效的入口。

- **删掉,不要 `#[allow(...)]`**(本仓 rust-standards 把 allow 宏本身当违规)。
- **`pub` 方法在 lib 内部可能看起来是死的** —— 它可能有测试或 tools/ 的调用者,
  所以删之前 `grep` 整个仓库(含 tests 和 tools/),不要只信 dead_code 警告。
- **同一个物理常量在两处声明(`collision.rs:42` 和 `game.rs:232` 都有
  `CAR_RADIUS`)是潜在 bug**:两份拷贝必然漂移,其中一份会静默变成错的。
  重构碰到这种常量时顺手合一。
- **写手自己的新测试变红时不要提交。** 本轮
  `a_car_hitting_a_thin_wall_at_an_angle_slides_along_it` 就是红的,要么实现
  还不对,要么断言写错了 —— 两者都要在提交前解决。

## Adding a post pass reverses orientation AND creates a black-screen class

Moving the main pass from the swap chain to an **offscreen colour target** (which
any post-processing chain requires) breaks two things at once. Both shipped as
user reports, not as test failures, and neither is visible in a stationary
verification frame.

**1. Orientation.** An offscreen texture and a canvas have opposite v
conventions. With `out.clip = p*2-1; out.uv = p;` and the composite doing
`textureSample(source, samp, uv)`, the image comes out vertically mirrored.
Reason about it **per pass** — the extract and blur passes sample the same
texture with the same `uv`, so fixing only the composite still leaves the blur
reading the wrong orientation. Establish the sign by measurement (sample known
pixels), not by reasoning alone: a wrong guess reproduces the exact bug you are
fixing. **Also check whether any regression test pins the buggy orientation** —
if it does, the test is the bug, not a barrier to the fix.

Note the diagnostic trap: an upside-down world makes forward/back and left/right
*look* inverted, so "movement is reversed" is often the same single defect.
Fix the image, re-verify, and report steering separately only if it is still
wrong — changing input code on a guess is worse than an honest report.

**2. Black frames.** This restructure is exactly what produces
`[Invalid CommandBuffer]`, stale-view-after-resize, and zero-sized-texture
failures. Symptom is "画面突然变黑" — intermittent, so it survives every short
verification run. When it appears, **ask the user for the console output
verbatim**; they can paste in seconds what took an agent hours to reproduce.

**3. The clean-console signal dies with the bug.** Chrome emits, once the
threshold is crossed:

```
WebGPU: too many warnings, no more warnings will be reported to the console for this GPUDevice.
```

After that line, **absence of console errors is not evidence of correctness** —
and it retroactively invalidates any earlier "validation clean" claim from the
same session. A correct fix is one where **zero** validation errors occur over a
long run, not one where the console went quiet. Instrument a violation counter
and surface it in the HUD so the signal cannot be lost this way again.

### 退化状态会打崩验证脚本本身 —— 而被测的性质是「恢复」不是「不崩」

黑屏修复的验收里有两个坑,都会让人以为「修法失败了」或「修好了」,而两者都不是:

1. **0 尺寸画布拿不到 PNG。** 故意把 canvas 打成 0×0 来测退化路径时,
   `toDataURL()` 返回的根本不是 `data:image/png`,于是
   `png_nonblack()` 里那句 `assert data[:8] == b"\x89PNG\r\n\x1a\n"`
   抛 `AssertionError: not a png` —— **崩的是探针,不是被测代码**,而且崩的
   恰恰是本次要测的那个边界。**不要 catch 掉异常继续跑**:那等于把这个触发器
   的证据悄悄扔掉。正确做法是把退化采样显式记成一个结果(「画布不可栅格化
   WxH」),然后**继续采样**,报告恢复情况。
2. **能触发但走不完的触发器不算通过。** `Emulation.setPageVisibilityOverride`
   在这个 chrome-for-testing 上不存在(`-32601`),`Page.setWebLifecycleState`
   的 freeze 能触发但 `headless=new` **无法恢复**被冻结的 tab。所以「fired」
   和「fired 且完成并恢复」是两回事,报告里必须分开写。跑不通就如实说
   「这个触发器在本环境无法完成,并说明试过什么」,不要把它算进覆盖率。

**被测的性质是恢复能力。** 本轮的黑屏修复,真正的判据是每次退化之后
`canvas_nonblack` 回到 `1.00000` —— 不是「触发时没崩」,而是**下一帧能画回来**。
修完播一次 soak 要给的是:总帧数、**全程** `canvas_nonblack` 的最小值、
每个触发器的 fired / recovered 两列、以及每个触发器**确实生效**的证据
(帧号确实停住、画布尺寸确实变了)。一个 200 帧的 soak 不算证据。

**顺便记一条取证纪律:截图会把 HUD 一起拍进去。** 「画面全黑」的截图里
minimap 的几个像素仍然非黑,截图体积读出 1.6% 的 non-black,而底层
`toDataURL` 实测是 `0.00000`。**判定黑屏要看画布自己的像素,不是整张截图** ——
否则 HUD 会一直在那里替你把「全黑」伪装成「局部变暗」。

### Read the arithmetic in the error before theorising

A `Write range ... does not fit in Buffer` error states both sizes; divide them.
This session's three errors reduced to one cause by arithmetic alone:

```
index  need 300456 u32 = 1,201,824 B   have 1,174,656 B   short 27,168 B
1,174,656 / 80 = 14,683.2   -> not an integer -> NOT the instance buffer
                              -> it is the mesh/index buffer
```

A non-integer quotient names which buffer you are looking at. The mechanism was
a capacity guard (`if capacity <= self.capacity { return }`) whose size check and
whose `writeBuffer` payload were computed at different points, so growth between
them overflowed the buffer. **The rule generalises: a size check and the write
it guards must derive from the same count, at the same point in the frame.**

**Stationary-camera verification cannot find this class.** It only appears when
the streaming centre moves and the mesh set grows. Any test of a streaming or
growing resource must **make the player travel far enough to force growth**, and
report the observed max `payload/buffer` ratio (must never exceed 1.0).

## 隐形碰撞体(invisible colliders)是这个仓库反复出现的已知坑

用户报「空气墙」时,先假设**存在一个看得见的碰撞体而看不见的图形**,而不是
先去找 bug。`build_collision_world` (`src/game.rs:3527`) 把整栋楼推成一个
**实心 AABB**;源码注释本身就记录了这个坑 —— showcase 楼当年就是因此被
**排除**在二维碰撞世界之外的(「推一个进去就等于在门洞外面砌了一堵看不见
的墙」),棕榈树也踩过(用展开树叶的包围盒当树干碰撞体 → 「看不见的树桩墙」),
静态摆件车同样(留在车道中间 → 「车不动」)。

**所以排查顺序是:先列出哪些 asset 被推进了碰撞世界,再问每一类的几何是否
可见。** 一个物体可以在三种情况下产生空气墙:
1. 整个 asset 可见,但**包围盒远大于实物**(倾斜枝干、展开树叶、装饰挑檐);
   修法是收窄碰撞体(`prop_collider_scale` 已经是这个模式),**不是**删掉它。
2. 该 asset 被特意排除 / 缩小过,于是**另一套**碰撞表示(`FloorWorld`)
   在生效而你在调试 `CollisionWorld` —— 两套世界内容不同,见本 skill 中
   `interiors.inSolid` / `playerInsideCollider` 恒为 `false` 那一条。
3. 薄道具(消防栓 / 锥桶 / 长椅,半厚 0.07~0.30 m)确实会被高速隧穿 ——
   实测过普通城市楼单帧门槛 11.018 m 而最大单帧位移只有 1.6000 m,
   **6.9 倍余量**,所以「车穿楼」几乎一定是碰撞体选错,不是隧穿。

**反向的判据同样重要:** 一个圆不是车的形状。 `resolve_car` 用 1.25 m 半径
的圆去近似一辆 4.5 m × 2 m 的车,车身探出边界约 1 m;而且圆撞薄墙时可能从
**错误的一侧**被弹出。修法是用真实轮廓(胶囊/OBB),**不要**直接把半径调大
—— 那会让车过不去门。

**空气墙的枚举方式是量化,不是目测。** 对每个被推进碰撞世界的 asset,
拿它的碰撞盒和**实际实心几何**比,输出「碰撞盒里有多少是可通行空间」:

```
prop_fire_hydrant  collider 0.62 x 0.60  void 0.41  -> 109.2% of box
prop_newsstand     collider 2.34 x 2.25  void 5.43  ->  79.9% of box
prop_phone_booth   collider 1.24 x 1.27  void 1.59  ->  34.5% of box
prop_traffic_cone  collider 0.44 x 0.44  void 0.22  ->   3.3% of box
```

这个表就是可执行的证据:百分比 >100% 意味着空洞体积**比它自己的盒子还大**,
而 3.3% 说明那个 asset 建模是实心的、根本不是空气墙。修法按情况分:
包围盒远大于实物 → **收窄**碰撞体(不是删掉,否则就把空气墙换成了可穿墙);
空心 asset → 改用**逐部件**碰撞体(数据里通常已经有 per-part bounds)。

**验证的唯一标准是「能不能真的走过去」。** 空气墙只在你把玩家走到那个位置、
人真的穿过去之后才算修好;代码改了不等于修好了。修完留截图。

## 地面着色:一个基于高度的项用在平面上,结构上就是错的

本仓的接触 AO 用的是**离地高度**而不是**离几何体的距离**:

```wgsl
v_contact_ao = mix(u_ao_floor, 1.0,
                   clamp(world.y / max(u_ao_height, 0.001), 0.0, 1.0));
```

**地面就在 y = 0。** 所以每一个地面片元都 clamp 到 0、拿到**最大**压暗,
而且**与周围有什么完全无关**。接触 AO 应该是「靠墙/靠基脚暗、空地不暗」,
这个项做的正好相反 —— 不是强度调错,是模型选错了。

可判定的测量:**把地面亮度按「到墙的水平距离」分桶**。正确行为是靠近墙暗、
在空地恢复;如果这条曲线是**平的**,就定量确认了结构缺陷。

派活给写手时要先分清**归谁**:WebGL2 路径有真的 SSAO pass(`u_ao_map`,
`render.rs` 约 :1458/:1689,带一个多抽头循环),而 WebGPU 路径还没有 ——
如果症状出现在 WebGPU 上,修法可能根本不在同一个文件里。**明确告诉写手:如果
正确的修复落在你不拥有的文件里,报告出来,不要去改它。** 这比让它去改别人的
文件造成互相覆盖要好得多。

### 「修在另一个后端」是一种全绿的失败模式

这条纪律本轮被真正考验了一次,而且**失败得毫无破绽**:地面光照的写手把
WebGL2 路径修得完全正确 —— 四处 bug 全找到、门禁全绿、还附了修前修后的
亮度分桶表 —— 但用户玩的是 **WebGPU**,而修复只落在 `src/render.rs`。

**判据不是写手做了什么,是用户跑的那条路径里有没有那个修复。** 修完必须
自己 grep 一次**出货后端**而不是信报告:

```bash
grep -c "ssao\|SSAO" src/webgpu/const.rs        # 0 = WebGPU 根本没有
sed -n '826,834p' src/webgpu/const.rs            # 缺陷公式是否还在原地
```

**派活时就要写死:症状出现在哪个后端,就修哪个后端的文件。** 项目同时存在
WebGL2 / WebGPU / Canvas2D 三条路径时,「门禁绿 + 数字漂亮 + vision 引用完整」
三者同时成立,**仍然**可能完全没解决用户的问题 —— 三个信号都在量另一条
管线。报告里必须写明「这次改动落在哪个后端」。

**同一推广到别的平行实现**:如果同一功能有多个实现(渲染后端、平台分支、
新旧 API 层),任何「已修复」的说法都要附一句「出货路径里的那一处也改了」。
没这句话的交付默认只改了一半。

## 「部署失败了」先查有没有 push,再查 CI

用户报「部署失败」时,**先确认本地 HEAD 是否真的到了远端** —— 本项目上「部署失败」的真实成因是攒了 7 个 commit 没 push,线上跑的是旧构建,CI 全程绿灯。顺序:

```bash
git log --oneline origin/main..HEAD   # 有输出 = 有没推的东西
gh run list --limit 3                 # 再看 CI
gh api repos/:owner/:repo/pages --jq .html_url   # 拿部署地址
curl -sSI https://<user>.github.io/<repo>/ | head -1
curl -sS -o /dev/null -w '%{http_code} %{size_download}\n' https://<user>.github.io/<repo>/pkg/vice_city_web_bg.wasm
```

**判据**:远端 `main` 的 sha 不等于本地 HEAD 时,问题不在 CI;反过来 CI `success` 而线上仍是旧产物时,先查 wasm 体积有没有变,体积不变就是没推上去。`gh run view --log-failed` 为空 + 状态 `success` 就是没有失败可查,不要从 Node.js 弃用警告里编一个失败出来。

推之前先 `git merge-base --is-ancestor origin/main HEAD` 确认 fast-forward,再 push 完**回读** `git ls-remote origin refs/heads/main` 与本地 sha 比对 —— push 返回成功不等于远端已更新。

## 本仓 audit 脚本:checker 通过不代表 fixer 安全

`doc_comment_audit.py` 的 **audit 侧**已经会跳过 raw string(`verify_doc_comment_format.py` 的 `_blank_string_bodies` 就明确点出这类 bug),但 **fixer 侧**是纯正则 `^\s*(pub |async |const |unsafe )*fn \w+[<(]`,于是把 **64 行 `///` 注入 WGSL 原始字符串**(落在 `@vertex` 与 `fn vs_main` 之间)。

**为什么它能活这么久:注入的 `///` 在 WGSL 里只是 `//` 行注释,语义完全不变,渲染逐像素一致 —— 而且 audit 报零 findings,因为 checker 那侧确实跳过了。** 所以「audit 过了」在这类工具里是**误导性证据**,不是安全信号。

通用规则:**任何 audit/fixer 自动改完文件后必须看 `git diff`** —— 只看它报了什么违规,不看它动了什么。同族坑:wrapper 模板里的 FAIL trailer 必须 `>&2`,否则被 `run_check` 的 stdout 行数统计算成 hit(+1);`audit_rust_standards.py:1152` 硬编码 `origin/master`,而本仓默认分支是 `main`,所以 pre-commit 的全仓审计**恒定失败** —— 修它要动 ~21 处,只修 guard 会把响亮的失败变成静默的空过,更糟。

## 派活时:先量 ablation,再决定要不要移植那个 pass

一个 pass「看起来在做事」不是它做事的证据。本轮一道 bloom 任务被派去移植
WebGL2 的加法 glow pass,而 agent 先量了它的 ablation,结果是 **−0.00000**
(贡献为零),于是**没有**移植,并给出了机制:`render.rs:4651` 那个 pass 用了
`depth_mask(false)` 但把 `depth_func` 留在 `LESS`,然后重绘**完全相同的几何**
—— 等深度通不过测试,整个 pass 根本不光栅化。

**派活时把「先测 ablation,再决定动不动手」写进 brief。** 一个写手发现被派的
任务前提为假、于是如实报告「没有东西可移植」,是**好结果**,不是任务失败。
判据:要求它交 ablation 数字(贡献多少),数字为零就**不要**为了交付而硬写一个
实现。

## 派活时:量一个比例差之前,先证明参照端那条路径真的在跑

「某后端强/弱 N 倍」这个测量的算术可以完全正确、而结论完全错误 —— 本轮
82.6x 的真实成因是**参照端**坏了(见上面「静默失效的 uniform」一节)。静默失效
的特征是「什么都不报错」,所以门禁全绿、validation clean、截图非空,**所有既有
信号都通过**。

- 一个在 CPU 上重建**共享链路**的模型,如果它与「坏掉的那一侧」一致而不是与
  另一侧一致,就把怀疑指向参照端 —— 这轮正是如此:重建预测两个后端都应该是
  ~0.0023,WebGPU 命中,WebGL2 跑了 0.296。
- **静态常量的前端读数不能作为后端在工作���证据**(见「`{N} tris` 是静态常量」)。
- **别拿固定相机的一对截图做跨会话对照**:本轮一次 A/B 里,另一个 agent 未提交
  的竖直翻转修正在会话中途进了 served wasm,把两帧变成「0.12 相关(未翻转) vs
  0.70(翻转)」,任何跨越那个时间窗的 diff 都是垃圾。**拍对照帧前先确认树上没有
  别人的在途修改**,或对每张图先验一个方向性相关系数(~0.99)再采信。

## 多个写手共用一个 checkout 的派活纪律

上面「门禁读数会被并发编辑污染」一节讲的是**测量**。派活时还要多给三条:

- **每个写手都要被告知其他写手的文件范围**(逐字),并且**必须按显式路径 stage**,
  再用 `git diff --cached --stat` 确认没卷进别人的在途改动。
- **一个 agent 的 `git checkout` 会抹掉另一个 agent 未提交的工作。** 本轮发生过
  一次,幸而 diff 还在。派活时明确写「不要用 `git checkout <ref> -- .`」——
  用隔离 worktree(`git worktree add --detach`)测门禁,而不是在共享树上 reset。
- **自己在树安静前不要读门禁。** 本轮三次读数(`182 vs 180`、`230 vs 228`、一次
  doctest 失败、一次「树根本编译不过」)全部是污染,靠 `stat -f '%Sm' -t '%H:%M:%S'`
  逐文件对比当前时间才确认。**最终验收要在所有 agent 落地后串行重测一遍。**

## Reporting standard

Numeric gates passing proves nothing about visual quality — a 45x88 px
fragmented character had perfect batch-instance counts and passed every
adjacency check while rendering as disconnected shards. For anything visual,
call vision and quote it.

`git status` is authoritative for what is committed. Child agents' prose
summaries are self-reports; check `--numstat` per commit and read the source
before repeating a claim as fact.

21. **A verdict that cannot be satisfied by ANY app state is not a verdict.**
    Three of them shipped and made a working build look broken:
    - `w3_pointerlock` assumed the camera forward was `(-sin,-cos)` or
      `(sin,cos)`. The real one is **`[cos yaw, -sin yaw]`**
      (`src/game.rs:5872`, restated in `camera.rs:988` and `update_aim`).
      Both guesses are **orthogonal** to it, so the dot product is identically
      0 and `best >= FORWARD_COS_MIN` fails forever. Fixed by *parsing* the
      expression out of game.rs (`camera_forward()` in w3) — write the value
      down in a comment if you must, but parsing means a future convention
      change gets caught by the harness instead of silently passing.
    - `w7_camera` hard-coded `Verdict("d V 切相机", False, ...)` and then
      tested **Tab** for camera toggling. Tab is the **map** now
      (`KEY_MAP => map_open`, `src/game.rs:4334`); V is the camera
      (`KEY_CAMERA => toggle_camera_mode`, `src/game.rs:4324`).
    - `w4_keys` shipped a hard-coded "missing" table for Space/G/H/Tab
      asserting they had no keybinding. All four exist, and the worker's
      **own readings already proved it** — a table that contradicts your own
      data hides real defects. Grepping `"KeyG"` in game.rs finds nothing
      because the match arms read `KEY_GRENADE =>`, not the literal.

22. **Distinguish "correctly refused" from "broken".** Two w4 verdicts were
    FAILs for a fully correct app: F with **no car nearby** (the app writes
    `no vehicle nearby` into the notice itself) and C on a **full magazine**
    (`Arsenal::reload` returns false at `magazine() >= capacity`,
    `src/combat.rs:393`). Neither is a defect; both are now SKIP with the
    reason recorded.

23. **`charBox[4]` is a saturated NDC z, not a distance.** `world_to_screen`
    clamps it to `[0,1]` (`src/camera.rs:1079`), so anything a few steps
    ahead reads exactly `1.00000` and Δdepth is `+0.00000`. Judging "did the
    character get further away" on it fails forever. Use the feet-screen-y
    instead (y grows downward, so moving away = y decreases).

24. **A `bad == []` check over an empty collection is a vacuous pass.** w5
    judged "the car never ended up inside a building" against the parsed
    `__vcw_probe` AABBs — and when the probe came back **empty** the verdict
    was PASS. A one-shot channel plus a loaded machine makes empty reads
    routine (measured: 0/64 populated on one port, 64/64 on another with
    identical code). Retry the probe until non-empty, and when it is still
    empty return **None** — never PASS, never FAIL.

25. **A single-frame flag can never be observed through a 3-frame channel.**
    `combat.fire_held` is set and cleared inside ONE `simulate` call
    (`hold_frames = 1`, request nulled in the frame it is read), while
    `__vcw` publishes every 3rd frame — so reading it back returns `false`
    **always**, and that proves nothing. A verdict built on that readback
    fails on every run. Judge on a **cumulative** signal (`enemies[].hp`,
    `kills`); if the app exposes no cumulative fire counter, return SKIP
    and say why. `mag` is a diagnostic consumed in a one-frame window, not
    a verdict. And in a burst of one-shot requests under load, verify
    arrival before you measure — a `teleport` that was silently dropped
    leaves you measuring wherever the player happened to be, 110 m from
    the thing under test.

26. **Hitting a wall is not being stuck.**
26. **Hitting a wall is not being stuck.** w1 judged "reached a wall within
    the sample window" as defect 1. Measured on the true per-frame channel:
    holding W from spawn leaves **58 consecutive zero-displacement frames**
    at `gap exactly 0.000 m` from a wall with `vel` still `4.5998 m/s` —
    correct blocking. Make the stall bar **clearance-aware** (probe the
    game's own AABBs; treat gap <= ~0.02 m as wall contact), and never
    compare two speed samples taken on different ground — a 9.39x
    "sprint ratio" was wall-vs-street, not walk-vs-run.

28. **Implicit string concatenation makes only the FIRST fragment an
    f-string.** In `_map_dom` the `{{}}` escape was written in a *plain*
    fragment, so it reached the JS as `{{}}` -> `SyntaxError` -> `ev()`
    returns `None` -> the helper reported `{"missing": true}` forever. The
    symptom ("the map panel never appears") was indistinguishable from a
    real Tab bug; only printing the concatenated string reveals it. When
    one fragment is an f-string, **all** the others must be plain JS with
    single braces.

29. **Disproportionate mean is not speed.** Measuring "walk vs sprint" as
    the mean of *moving* frames produced **6.101 m/frame** against a true
    0.6 m/frame (WALK_SPEED 4.6 x dt 0.133) and inverted the sprint ratio
    to 0.53. Use the **median** of the per-frame deltas: robust to both the
    slow first frames and the few large slide frames against a wall.

33. **`__vcw_probe` only reports walls within 0.8 m — never use its
    extremes as a building shell.** `probe_nearby_shapes` (game.rs:1291)
    gates on `pen_x.abs() < 0.8`, so standing mid-room it sees only the
    walls you are pressed against. Deriving the shell from its min/max
    yields a ~7 m box and a bogus `outBy 7.28 m` "eye outside the building"
    reading. For a room-sized AABB use `__VCW_DEBUG__.nearInteriors`, which
    uses `NEAR_SHAPE_REPORT_RADIUS = 6.0` (const.rs:731) and reports full 3D
    `{"y":[y0,y1],"c":[cx,cz],"h":[hx,hz]}` per wall. Also note `2DB`/`2DC`
    entries (from `game.world`) have **no `y` field at all** — a parser that
    does `d["y"]` dies with `KeyError: 'y'` on the first city prop and loses
    the whole run; skip incomplete entries with `.get()` + `continue`.

33b. **The camera follow focus is an ABSOLUTE world height, not
    "feet + height" — confirmed defect.** `game.rs:7452` does
    `next[1] += (FOLLOW_HEIGHT - next[1]) * blend` with
    `FOLLOW_HEIGHT = 1.45` (game.rs:203), so on the upper floor (feet
    `y = 3.20`) the focus stays pinned at `y = 1.45` and the eye
    (`1.45 + sin(pitch)·d`) cannot exceed `2.76 m` even at full `d = 8.2` —
    always under the upper slab `y = [2.95, 3.20]`. Measured
    `follow_target = [20, 1.4500000476837158, 30]`. Note
    `toggle_camera_mode` (game.rs:7733) has the mirror-image issue: it sets
    `follow_target = player.get_position()`, dropping the focus to the feet
    on the way back to third-person.

34. **A verdict whose inputs are read from different frames will flip
    between runs.** `__vcw` publishes every 3rd frame, so `playerY` and
    `camEyeY` in one snapshot can describe different instants. A check like
    `eye_y == foot_y + 1.62` passed on one run and failed on the next with
    identical application behaviour. Judge camera state from fields that are
    published **in the same snapshot** (`cameraDist`, `cameraMode`, HUD
    label), and turn exact float equality into an interval. Separately: a
    collector that maps `cameraDistTarget` to the key `"dt_"` while the
    verdict reads `"t"` yields `None` forever and reports a correct app as
    FAIL — check the key names match on both sides of the harness.

35. **`game.rs:752` shadows `const.rs:1676`.** Both are named
    `SHOWCASE_WALL_THICKNESS`; the local one is `0.20` and the const one
    `0.25`. `push_showcase_interior` (game.rs:1142) reads the **local** value,
    confirmed by `__vcw_probe` reporting 0.20-thick walls. `const.rs`'s 0.25
    is still used by `showcase_door_center` (game.rs:981). Transcribe 0.20
    when deriving showcase geometry by hand.

29. **`camOccluded == true` means a low `cameraDist` is correct.** The
    avoidance logic pulls the camera in to `FOLLOW_DISTANCE_MIN` (2.2) so it
    does not end up behind a wall, so on those frames `dist != target` is
    the intended behaviour. Judge follow-convergence only on frames with
    `camOccluded == false`; the "does it clip through walls" question is the
    separate `camClearance` check.

30. **Under 8 concurrent Chromes a worker can die with
    `ConnectionClosedError` and an empty log** — `python -m http.server` is
    single-threaded and its backlog is exhausted during boot. That is
    harness, never app. Rerun the affected worker alone.

31. **A constant declared exactly once is a keybinding that was never wired.**
    `git grep -c 'ARROWUP' -- src/` returning **1** — the `const.rs` definition
    and nothing else — means the key is accepted by the type but read by no
    code path, so pressing it does nothing while every other check stays green.
    Two or more hits means it is wired. The same count settles "is this a real
    gap or a non-target key": compare the reference product first, because
    GTA-style movement deliberately omits the arrow keys while its *driving*
    does not, and a check that never consults the reference will call a
    deliberate omission a defect or a real gap a non-issue.

32. **Assert the mode precondition, not just the position.** A verdict run
    while the player is `DRIVING` measures a walking key, and the resulting
    near-zero delta is reported as a dead key. Read the mode out of the same
    atomic snapshot and require it before reading the field under test.

## 三个 2026-10-07 这一轮亲手测出来的坑

## 两条新纪律(2026-10-07 修鞋子/穿楼缺陷时各交一次学费)

43. **解析器里一个多余的右括号,和一个真的空通道长得一模一样。**
`nearShapes` 的形状串是 `"AABB c=(33.50,45.00) half=(0.92,0.29)"`。按
`half=` 切片的写法若不 `rstrip(") ")`,切出来的是 `"0.92,0.29)"`,
`float()` 直接抛 `ValueError`。如果外面套了 `except: continue`,
探针就**静默丢掉每一个条目**并报告「通道全空」—— 而原始通道其实满满
当当。两次连续踩坑:先是 `channel non-empty 0/30` + `worst_pen 0.0`,
被误读成「人物没穿过房子」。**判据:通道空的时候,必须先打印一条原始
记录(json.dumps 单条)证明不是解析器吃掉了它**,再谈结论。
与陷阱 #24 同类但入口更隐蔽 —— #24 是集合判空,这条是解析失败伪装成
集合判空。

44. **「把实体瞬移进墙里,再问我在墙里吗」不是有效的对照。**
碰撞求解器会在到达的瞬间把人**推出去**,所以诚实读数就是「不在墙里」,
与「穿过去了」完全无法区分。实测:showcase 墙 x∈[17.80,18.00],传送到
x=17.90 → 落地 x=18.387,已被推到远面之外 0.387 m。**正确的判据是
「穿越(transit)」**:从墙的一侧出发,朝另一侧冲,看**远面有没有被达到**。
被挡住的身体永远到不了远面,穿墙的身体会。控制组用已知良好的速度档
(步行 0.31 m/帧 vs 0.2 m 墙 = 1.5×),测试组用最坏档(冲刺 0.56 m/帧
= 2.8×)。

**写「建筑必须是实体」这类结论前的实测结论(2026-10-07)**:普通城市楼的
碰撞 AABB 是**整栋实心盒**,实测最薄的一栋 `bldg_lilac_tower` 半厚
4.259 m、厚度 8.518 m;汽车半径 1.25 m,所以单帧穿过去的门槛是
`厚度 + 2×1.25 = 11.018 m`,而车能走到的最大单帧位移是
`SPEED_MAX×1.6×dt_cap = 24×0.0667 = 1.6000 m` —— **6.9 倍余量**,
任何速度都穿不过去。人的 `resolve_slide` 按 0.05 m 子步扫掠,更是
结构性不可能。真正会被高速穿透的是**薄道具**(消防栓 / 锥桶 / 长椅,
半厚 0.07~0.30 m),不是楼。把这条写下来是为了下次不必重新做一遍资产
包围盒统计。

**推论(2026-10-10 补上):这条只否定了「隧穿」,**没有**否定「碰撞体形状
不对」。用户报的「车穿墙」在楼体上是**几何误差**而非隧穿 —— 见上面
「隐形碰撞体」一节:`resolve_car` 用 1.25 m **圆**近似 4.5 m × 2 m 的车,
车身探出约 1 m,圆撞薄墙还可能被从错误一侧弹出。**所以「隧穿余量充足」
与「车看起来穿模」可以同时为真,不要因为算过隧穿就驳回穿模报告。**

42. **车转向的符号基准:yaw 增大 = 车向左转,不是向右。** `traffic.rs` 的
    `fwd = [cos yaw, −sin yaw]` 决定 `d(fwd)/d(yaw) = [−sin, −cos]`,那是车头的
    **左**方向。所以 `yaw_rate = steer * …`(steer 约定正 = 右)会把车往左拐 ——
    这就是「方向键反向」整轮藏了这么久的根因,`steer_sign` 本身完全正确。
    **不要从 `Δyaw` 的符号判转向对错**:它只告诉你 yaw 变没变,不告诉你车往哪拐。

43. **判「车往哪转」要先标定世界右手,而且标定要用一条与被测代码无关的路径。**
    最省事的是**步行横移**:把相机 yaw 钉在 0 和 π/2,按 D 各走一段。
    yaw=0 时前向 = (1,0),D 走 +Z;yaw=π/2 时前向 = (0,−1),D 走 +X。两处合起来
    唯一确定 `right = (−fwd.z, fwd.x)`。然后判据就是
    `dot(fwd_end − fwd_start, right)`:>0 = 往右拐。这条路径走的是 `Player::step`
    的移动轴,和车的 `drive()` 毫无共享代码,所以它是一条**真正独立**的基准。
    **注意:**「位移在平均值基向量上的投影」是个**假判据** —— 左转和右转的
    弧线投影到起止朝向的平均值上会同时给出同号(实测 +0.64 / +0.80),它分不开
    左右。必须用**朝向差**,不能只用**位移**。

44. **倒车这条线一旦接上,下游三处会静默地反向或归零,必须一起改。**
    `speed` 从无符号变带符号之后:转向死区写 `speed > STEER_MIN_SPEED` 会让整段
    倒车恒假(转不动);漂移滑移比写 `lateral.abs() / speed.max(1.0)` 在负速度下
    分母退化成 1.0,滑移比放大好几倍(一打方向就掉速);漂移掉速的 `.max(0.0)` 会
    让车「滑着滑着自动挂上倒挡」。三处都是**恒真/恒假**,不报错、不 panic,只
    在倒车这一段表现异常 —— 单测若不专门写倒车用例就一个都测不出来。
    另外**前进和倒车必须分开测**:修好之后倒车时转向符号是**故意**与前进相反的
    (真车倒库就这样),把它当成残留缺陷去「修」会把正确的行为改坏。

## HUD 的 `{N} tris` 是静态常量,不是本帧读数

`scene.total_triangles` 是一个**编译期就定下来的常量**,WebGL2 和 WebGPU 打印
**同一个数字**——哪怕某个后端一帧都没画。所以 HUD 上读到 `2740048 tris`
**不构成任何后端在工作的证据**。真正能读「本帧真的提交了多少」的是
`__vcw` 里那个 `gpuSubmitted`(与 `tris` 是两个不同的字段,别混用)。

这条已经造成一次错误结论:一棒交付 `WebGPU · 2740048 tris` 并宣告成功,
而画布其实是一整片均匀蓝、几何被压成地平线上一条窄带,截图 72 KB 对照组
332 KB。**非零三角形数只证明提交量,不证明输出。**

判后端是否真的出图,按这个顺序:

1. **先比截图体积**。与一张已知正常的对照图比,空画面只有零头,一眼可辨。
2. **再 vision 看图**,并引用你实际看到的。72 KB 的图不需要解释。
3. HUD 后端标签(`WebGPU` / `WebGL2` / `Canvas2D`)只说明**选中了哪个后端**,
   不说明它画出了东西。

## `gpu_submitted` 是**累积**计数器,两次会话之间做差没有意义

`__vcw.gpuSubmitted`(以及任何 pass 的提交计数)是进程内**累积**值,不是
每帧读数。一次 WebGPU 阴影移植里,写手报「提交量从 2,741,184 涨到
3,014,234,delta 273,050」并据此推断阴影 pass 只提交了一小部分实例 ——
而这个 delta 是把**两次不同浏览器会话**(帧数分别 2100 与 2520)的累计值相减
得到的,数字纯属两个会话长度之差。

**规则:所有 pass 的提交量必须在同一帧内同时读出**,写成
`shadow=230298 main=2773984` 这种一行两个数,而不是两个时间点的快照相减。
另外,主 pass 的绝对值**本身也随流式中心变化**,所以「改动前 vs 改动后」即使
同相机也不能直接比 —— 要么同会话同帧内读,要么明确锁定相机与流式中心。

区分「累积量」与「每帧量」的判据:在**同一个页面会话**里隔 N 帧连读两次,
若第二次 > 第一次且差值正比于 N,它是累积量。

## 功能「管线全对但看不见」时,先问当前参数能不能表达这个效果

一个特性可以 validation 全绿、零错误、几何照常提交、深度照常写入并采样,
**同时完全不可见** —— 这不是 bug,是当前场景参数没给它表达的机会。
本项目实测:阴影 pass 一切正确(230,298 tri/frame,135/1980 实例存活,
`textureDimensions` 读回 2056 ≈ 2048,`textureSampleCompareLevel` 返回 1.0,
零 acne),但画面上「没有可辨认的投影」。

**第一步永远是读光照表,不是相信附近的注释。** 本仓库的坑:

| phase | `light_dir` | 位置 | 阴影表现 |
|---|---|---|---|
| `Noon` | `normalize3([0.35, 0.86, 0.36])` | `render.rs:482` | y=0.86 **近乎垂直**,影子藏在遮挡物正下方 |
| `Dusk` | `normalize3([0.86, 0.24, -0.44])` | `render.rs:517` | y=0.24 **很斜**,长而明显 |

`render.rs:137` 的文档注释里写着「黄昏光 `light_dir = [0.86, 0.24, -0.44]`
相当斜」—— 那是 **Dusk** 的值,却出现在一个与 phase 无关的函数上方,读它的人
很容易以为默认就是斜光。写手就是这么推断「太阳接近垂直所以影子看不见」的,
结论碰巧对了,但依据取自错的常量。

**第二步是把「看不见」变成可判定的对照,而不是继续调参数。** harness 够不到
触发条件(此处 `DEFAULT_PHASE = Noon`,而页面没有任何 phase 开关),那就先
补一条通路:按 `?res=` / `?hide=` 已有的 URL 参数解析惯例加一个 `?phase=dusk`
(见 `hidden_batches()` 在 `src/render.rs:4296` 每帧重读 `window.location().search`
的既有模式,以及 boot 期读一次的 `?res=`),然后拍**同相机位置的 dusk/noon 一对**
截图。这一对才是「阴影项真的在起作用」的证据;单张 Noon 图里影子短,和
「阴影压根没生效」在像素上无法区分。

**如果补了通路仍不可见**,按这个顺序排查(都是「几何正确但没画出来」的类别):
(a) 正交阴影半宽 `SHADOW_HALF_EXTENT = 45 m` 覆盖不住斜光抛出的几十米影子;
(b) 斜光下 ortho 的 near/far 不再包住遮挡物;(c) PCF 参考深度或 bias 没有
按斜光缩放;(d) 光照矩阵没有逐帧按当前 phase 重建。

**别用「累积计数器涨了」当作阴影生效的证据** —— 那只证明多提交了几何。

## 上 CDP 之前先验实例的 GPU flag,不要相信任何摘要

本轮 brief 里写「9240 端口有 GPU」,`ps aux | grep "[C]hrome"` 一查就是
`--disable-gpu`;另一个端口 9225 是 SwiftShader。**两者 `requestAdapter()`
都返回 null**,于是每个读数都是在量后端回退,不是量你的改动。

```bash
lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null | grep -E "92[0-9][0-9]|93[0-9][0-9]"
ps aux | grep "[C]hrome" | grep -o "remote-debugging-port=PORT.*" | cut -c1-160
```

判据不是 `navigator.gpu` 存在,而是 `requestAdapter()` resolve 出**非 null
adapter 且 `requestDevice()` 成功**。`--use-angle=swiftshader` /
`--enable-unsafe-swiftshader` / `--disable-gpu` 各自**单独**就能让 adapter 变
null——**验证 WebGPU 时一个都不要带**,连 `about:blank` 都不行(navigator.gpu 只
在 secure context 暴露,必须导航到 `http://127.0.0.1/...`)。

WebGPU 验收用 `tools/gpu-probe/run.sh` 起的**独立 chrome-for-testing**
(`--headless=new`,**不带任何 GPU flag**,实测 `apple / metal-3`)。无头实例
没有窗口没有 tab bar,不违反用户「不开新窗口」的规则;那条规则针对的是用户
自己可见的那个 Chrome,永远不要碰它。

## 子 agent 的视觉主张必须由主 agent 独立 vision 复核,子 agent 的数字主张必须自己重测

这两类主张本轮各被推翻一次,都是子 agent **并非**说谎,而是它的判据本身
不成立 —— 所以派活时的 brief 要明确要求**先测量再断言**:

- 数字主张:一次 bloom 交付报「验证全绿、night 辉光 clearly visible」。我重测
  三个门禁(cold,`cargo clean -p` 后)全部对得上,但 vision 看它自己的图得到
  「some mild bloom, but no strong cinematic halos」,而且画面里最明显的辉光
  是 **HUD 图形**。**门禁全绿与视觉成立是两件事。**
- 前提主张:另一个 agent 报「已经清理了 77 行注入的 doc 注释」。我解析文件发现
  仍有 77 处在 raw string 内 —— 它的判断其实是对的(64 行垃圾 + 13 行真注释),
  但**没有说出「我保留了 13 行」这个关键事实**,差点被我按错误结论当成误报。

派活时固定加两条:**(a) 任何视觉主张必须给出 vision 引用原文,不许写
「clearly visible / 效果明显」这种形容词,写你实际看到的;**(b) 任何部分完成的
清理必须明确报告「保留了什么、为什么」,而不是只报删了多少。

还有一条**用户能秒给、你花几小时拿不到**的输入:当用户说「画面变黑」这类
**间歇性**缺陷时,**直接向用户要 console 输出原文**。他们粘贴只要几秒,而
复现要几小时。这不是偷懒,是正确的取证顺序。

## 派活时必须给出 cold 基线命令,不能只给数字

本轮子 agent 报的 clippy 是 231,我实测基线 228 —— 但更糟的是**两边都不是
可靠值**:warm / 部分构建的 target 目录会给出无意义的计数(实测同一命令读到
12 / 37 / 180 / 181 不等)。**门禁数字必须配 `cargo clean -p` 前缀才是基线。**

派活时把这三行连数字一起给出去,不要让 agent 自己去猜基线:

```bash
export CARGO_TARGET_DIR=/Users/sqs/Library/Caches/cargo-target/vcweb
cargo clean -p vice-city-web
cargo check --all-targets --message-format=short | grep -c warning   # 180
cargo test | grep 'test result'                                      # 146 passed
cargo clippy --all-targets | grep -c '^warning'                      # 228
```

并明写:**修 warning 要按原因修,不得用 `#[allow(...)]`** —— 本仓 rust-standards
把 allow 宏本身当作第 14 条违规。

另外:**基线也会因为别的工作漂移**。基线 worktree 上读到 180 而主工作树读到 181,
差 1 是 target 缓存状态,不是代码变更 —— 遇到这种 1 的差异,重测两边再决定
基线取谁,不要把差异当成回归去「修」。

## 子 agent 报「已修复」不等于已验证

主 agent 必须自己 `vision_analyze` 看一眼截图才算数。这条被用户驳回过一次:
一棒附了对照表,主 agent 据此宣布「已修」,用户回「问题依然存在」——它量的
是它自己会话里的状态。**判定完成的门槛:主 agent 自己看过像素,或用户眼验。**

## pre-commit 的 dep-order 是**全仓**检查,不是暂存区检查

`~/.git-hooks/pre-commit` 里只要有**任何** `.toml` 暂存,就对整个 repo 跑
`verify_dep_order.py`,**不看 delta**。所以一个跟本次改动毫无关系的未跟踪目录
能让你的 commit 被拒,而且报错指向 `Cargo.toml`(你确实动过的那个文件),
极具误导性。

判定是不是你的锅,两步就能定论:

```bash
# 1) 把你暂存的 Cargo.toml 单独复制到干净目录跑,是否为 0 violation?
# 2) 暂存一个只改注释的 .toml,再试 commit —— 仍然 exit 1 就证明是存量问题
```

存量的 offender 通常是 `tools/gpu-probe/Cargo.toml` 之类未跟踪的探针目录。
**按规则修它,不要绕开**:找出权威期望顺序,把依赖块重排到位(不改任何版本
号),而不是去改 hook 或跳过它。

排序规则本身有个反直觉点:**它按版本字符串的字符数排序依赖**。所以
`euv = "0.28.13"`(15 字符)会排到 `js-sys = "0.3"`(14 字符)前面,一次版本
升级就能翻转依赖顺序并触发 gate。升级后如果 commit 被这条卡住,先怀疑是它。

## `cargo test --target wasm32-unknown-unknown` 在本仓库**跑不了这些测试

136 个测试都是普通 `#[test]`,不是 `wasm_bindgen_test`,wasm 测试二进制无法
自执行,会报 `cannot execute binary file` / `no tests to run!`。
**测试门禁必须用原生 `cargo test`**。别把「wasm target 上跑不起来」误报成
测试挂了,也不要把这条写进 CI。

顺带:基线数字必须**同命令同 flag 实测**,不能拿 `cargo check` 的
warning 数当 `cargo clippy` 的基线(分别是 173 和 227)。派活时把基线的
**测量命令**和数字一起给出。

## 起一个能验证几何的浏览器:唯一可靠的 recipe

要自己连 CDP 复现几何类缺陷(角色不展示、车身缺失、穿墙),浏览器必须
**真的在画东西**。HUD 里 `0 tris` 或 backend 标签报 `none` 就是没画 ——
那个实例对几何问题零信息量。

**唯一已验证可用的起法**(用户在跑自己的 Chrome 时另开一个独立实例,不碰
他的 profile、不关他的窗口、不抢他的登录态):

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9333 \
  --user-data-dir=/tmp/vc-chrome-profile \
  --enable-gpu --use-angle=metal \
  --window-size=1600,900 \
  "http://127.0.0.1:8877/index.html?res=1.0"
```

然后 `curl -s http://127.0.0.1:9333/json` 拿 target 的 `webSocketDebuggerUrl`,
用 stdlib 手写 websocket(项目里 `tools/` 下已有探针可参考)连上去,
`Runtime.evaluate` 读 `window.__vcw` / `#vcw-hud`。

**注意:`--user-data-dir` 必须指到一个独立目录。** 用默认 profile 时,浏览器
已经在运行就会拒绝新实例,而复用正在运行的实例又连不上 CDP(它没开调试端口)。
独立 profile + 独立端口是唯一同时满足「不干扰用户」和「我能连上」的做法。

**机器上可能已经有一个 CDP 端口在监听,但它可能没有 GPU。** 先确认再动手:

```bash
lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null | grep -E "92[0-9][0-9]|93[0-9][0-9]"
```

连上之后**第一件事读 HUD 的三角形计数**。读 0 就说明这个实例是
`--disable-gpu` 起的,renderer 初始化失败,你在它上面量到的所有几何读数都是
空的 —— 这不是「没复现出缺陷」,是「这个实例根本看不见」。

## 在用户自己的窗口里开 tab(用户要自己看时)

用户要自己验证时,用 `computer_use` 驱动**他已经开着**的那个窗口,不要新开
实例。已验证可用的顺序:

1. `capture(pid=..., window_id=..., mode='ax')` —— 必须**同时**给 pid 和
   window_id,只给 window_id 会返回 0x0 加一句 `capture targeting requires both`
2. `key('cmd+t')` 开新 tab
3. `click(element=<地址栏>)` 再 `set_value(element=<地址栏>, value=url)` ——
   **`set_value` 单独调有时会开出新窗口**,先点一下地址栏能避免
4. `key('return', delivery_mode='foreground')` —— 同 pid 有多个窗口时,
   `background` 会被拒(`same_pid_keyboard_ambiguity`:无法证明按键送到哪个窗口)

**不要用 `bring_to_front` / 前台抢焦点去做这些**,除非 `verdict` 明确要求
升级到 `foreground`(它自己是分级升级的:先 `px` → 再 `foreground`)。

## 判帧率低:先证明测量有效,再谈瓶颈在哪

**SwiftShader 下 ~1.7 fps 是环境限制**(`--use-gl=angle --use-angle=swiftshader
--enable-unsafe-swiftshader`)。但「真 GPU」不等于「测量有效」—— 下面这套
归因链整条作废过一次,先按步骤重新自证。

**第一步:证明它真的在画东西。** 带 `--disable-gpu` 启动会让
`WebGlRenderer::new()` 失败、`game.renderer = None`,于是一个三角形都没画,
而你测到的「帧率」只是空转循环的节奏。特征在 HUD/遥测里:**三角形计数读 0**,
或 backend 标签报 `none`。修 flag 后**把之前所有读数全部作废**—— 它们不是
慢,是没跑。正确 flag 是 `--enable-gpu --use-angle=metal`(本机真 GPU 报
`ANGLE Metal Renderer: Apple M5 Max`),headless 也一样可用。

**第二步:解除垂直同步上限。** 带 vsync 时两次跑都精确报 60.00 fps。这个精确度
是警告不是结果——说明变量根本没动。补 `--disable-frame-rate-limit
--disable-gpu-vsync` 之后才测得到真实成本。在 60 Hz 锁下「改了阴影读数不动」
会被读成「优化无效」。

**第三步:确认计数器覆盖了你怀疑的那一趟 pass。** HUD 里那个三角形计数
(`render.rs:4495`)只在**主 pass** 累加,**阴影和 G-buffer 循环都不计入**。
所以「阴影占 33% 三角形」是把提交量当成了时间成本。**三角形提交量 ≠ 时间**,
一个 pass 可以占三分之一几何量而几乎不耗时。

**先测「把嫌疑功能整个关掉」的上限。** 没有这个基准,「已经拿回 90% 的
可获得收益」无法计算,一次真实收益和噪声区分不开。这是一个 run 的事,它决定
整个任务值不值得做。

**把嫌疑资源跨数量级扫一遍。** 本项目把阴影贴图像素从 1.68M 扫到 67K
(**1/16 像素量**),帧率只动了 6% → 不是填充率瓶颈,顶点/几何才是。据此**放弃**
了降 `SHADOW_MAP_SIZE`(最容易想到的那条路)并回退:实测换不来帧率,为此牺牲
画质没有必要。被否掉的候选要**写进报告并说明为什么**,它是结果不是失败。

**实测结论(修完,HEAD 之后)**:阴影 pass 加视锥剔除,366.71 → 443.57 fps
(+20.9%),帧时 2.5626 → 2.2544 ms,吃到「阴影全关」上限(448.91)的 92%,残差
只有 4.4 fps —— **阴影不再是瓶颈,继续在阴影上投入没有回报**。剩余大头是主
pass 的 274 万三角形,下一步得做主 pass 剔除。分辨率扫描(1/16 像素 → +6%)与
JS 侧实测(0.0033 ms/帧)两条证据都指向顶点吞吐,不是像素也不是 JS。

**分桶统计的写法**:`bindFramebuffer` / `viewport` 上打补丁记录当前目标,再在
四个 draw 入口累加索引数。**不要 hook `requestAnimationFrame`** —— wasm 侧的
主循环如果已经抓住了 rAF 引用,你后装的 wrapper 根本不会被调用(实测抓到 0 帧)。
`?hide=all` 那个开关也不适合用来论证几何量:实测它只砍掉约 5% 的绘制(批次表的
静态段仍会画),不足以说明「几何量是不是瓶颈」。

**剔除几何体时,别只拿模型原点判。** 单测抓到过一个真 bug:斜光下 40 m 高的楼,
原点落点距 focus 119 m(该剔),但**底部**落点只有 61 m(仍在视锥内,不该剔)——
按原点判会误剔掉阴影落在玩家附近的高楼。改成探两个高度(原点 + 下移一个
剔除余量)后修复,帧率无损失。

## Triaging a FAIL

Reading a FAIL correctly before dispatching a fix is the whole loop — see
`references/verdict-triage.md` for the real-defect / broken-verdict /
harness-limit table and the three rules behind it. Two load-bearing ones
repeated this round: **comparing two legs of a measurement requires their
implied dts to match** (implied dts of 1.326 s vs 0.385 s void the ratio
entirely), and **"conservatively" reporting FAIL when a check cannot measure
the property it names is not allowed** — that hides a defect behind a number
that looks safe. When repairing a suite with structurally unsatisfiable
verdicts, pair the improved tally with the per-item adjudication, because a
silenced suite and a repaired one report the same numbers.

33. **A 40 ms click at 1.7 fps never reaches `simulate()` — hold the button
    across a real frame instead.** `fire_held` is set on canvas `mousedown`
    and cleared on `mouseup` (game.rs:4296/4314), so a click shorter than one
    frame is set *and* cleared between two `simulate()` calls and the app
    never sees it. Under SwiftShader one frame is ~583 ms, so a
    `mousePressed`/`mouseReleased` pair 40 ms apart reads back as
    `mag = 12` forever and looks exactly like "player fire is broken".
    **Correct pattern: `mousePressed` → wait until the HUD's own `frame N`
    advances by 2 → `mouseReleased`.** Measured result: `mag` 12→11→10→9→8→7,
    one round per held pair. 40 ms is also below human reaction time, so it
    is not a real user gesture at all; `fire_held` means *hold*, and GTA V
    holds LMB to keep firing. Do not inject `Digit2`/`KeyX` to "fire" —
    those go through `TRACKED_KEYS` and never touch `fire_held`.

34. **Never judge `interiors.inSolid` or `playerInsideCollider` for "am I
    inside the building" — both are constant `false` in a room.** Two
    separate reasons, each fatal on its own:
    * `interiors.inSolid` = `contains_interior_point([x,z], y+0.5)`
      (game.rs:5063-5068), and that is "does this point fall *inside* some
      collider" (interior.rs:638-648). Standing in an **empty room** is
      inside no AABB, so it is `false` indoors and outdoors alike. A 9 m
      scan grid over both showcase buildings returned `false` at all 81
      points *while the player was standing on the building's ground slab*.
    * `__vcw.playerInsideCollider` = `world.contains_point(...)`
      (game.rs:5043) on the **static** `CollisionWorld`, but the showcase
      buildings' walls live in `FloorWorld` — game.rs:5271-5275 says so
      outright ("第一次跑探针只扫 `world` 拿回来 12 个圆柱道具、零个
      AABB —— 因为墙根本不在那儿").
    **The two channels that do work for "am I inside a wall":**
    1. `y == 0.15` (`SHOWCASE_GROUND_TOP`, const.rs:1667) while the street
       is `y == 0.0`. A raised slab is the cleanest indoor discriminator
       and it reads only the player's height — independent of any collision
       world.
    2. `__VCW_DEBUG__.nearInteriors` non-empty (game.rs:5303-5344) — the
       only channel that enumerates `FloorWorld`, i.e. where the walls
       actually are. Carries `y0/y1/cx/cz/hx/hz` per wall.

35. **"HP dropped while I was behind a wall" is not a wall-block failure
    until you prove every enemy was wall-separated.** A building interior
    is *multiple rooms*; the ground floor has a partition at local
    `z = SHOWCASE_PARTITION_Y = 2.40`. Measured: 40 frames at (21, 30)
    showed `HP 100→97.4` with `shotsBlocked 1→2` and **14 same-room
    enemy-frames** — an enemy inside the *same* back room has unobstructed
    LOS, so that hit is legal and the 3 HP is correct behavior. Judge it
    per-frame, not on the segment total:
    * `shotsBlocked` (`shots_blocked_by_geometry`, game.rs:6610) is a
      **monotonic cumulative** counter — every increment is exactly one
      shot vetoed by geometry, so the 3-frame publish throttle does not
      distort it. To infer LOS-gate health you must still project each
      enemy into building-local coordinates and check room membership.
    * Segment-level "HP didn't drop" is unjudgeable whenever any enemy is
      co-located; report SKIP with the same-room count rather than FAIL.
    * Place the open-ground control on the real street between the two
      showcase buildings (`x ≈ 30.25`; their footprints are x[18,28] and
      x[32.5,41.5]) — a "street" point at x=35 is *inside* the SHOP
      building and silently has walls too, which is how a control group
      turns into a second test case with no discrimination.
    * A control group must prove it actually fired (HP down **and**
      `shotsBlocked` flat). If it can't, both groups are false negatives.

36. **`min()`/`max()` over a positional slice raises `ValueError` when the
    slice is empty.** `rows[start:i+1]` with `i < start` — i.e. the first
    record already showing a `shotsBlocked` increment — is `[]`, and the
    crash kills the whole worker after the expensive sampling is done.
    **Guard every min/max over a window: check `if i + 1 <= start: continue`
    and skip, and treat a 0-length window as "not a verdict" (SKIP), never
    as a pass.** Same class as the `bad == []` vacuous pass: an empty
    collection is not evidence.

37. **A magazine that empties under a held trigger never rests at 0.**
    `fire_weapon` auto-reloads on the frame the last round leaves the
    magazine: `if wants && magazine()==0 && !is_reloading() { notice(EMPTY);
    reload() }` (game.rs:6354-6360). Measured: draining 12 rounds showed
    `1 → 'PISTOL · RELOADING'` and reserve `48 → 36` **by itself**. So to
    test the reload key you must **release the trigger first** and then
    press the key; otherwise the auto-reload masks what the key does. Also
    a **full** magazine is a *correct refusal* (`Arsenal::reload` returns
    false at `magazine() >= capacity`, combat.rs:388-398) — reload tests
    need a genuinely non-full magazine, or the verdict is vacuous.

38. **`#vcw-ammo` (per-frame DOM) is the channel for weapon identity, not
    `__vcw.combat.weapon`.** The snapshot publishes every 3rd frame, so a
    weapon switch reads back stale and produced two phantom failures:
    `Digit2 → snap_weapon=0` while the DOM said `SMG`, and `KeyH →
    snap_weapon=2` while the DOM said `UNARMED · 0/0`. Judge on the DOM
    label. Also note `Weapon::Bat` prints `BAT · melee` with **no** mag/reserve
    fields (`Weapon::magazine() == 0`), so a regex-based ammo parser must
    treat a missing number as a *legal* state, not a parse failure.

35. **`__vcw` 的 3 帧节流会让「按一下键立刻读」永远读到旧值。**
    本轮在方向键 / 换弹 / 冲突三组测项上各踩了一次,症状都是同一个:
    FAIL 的 note 里写着「按了没反应」,而应用其实完全正常。按键 keydown
    之后必须**等 >= 4 帧**(`is_multiple_of(3)` 的发布节流)再读任何
    `__vcw` 字段;`playerYaw` / `throttle` / `grenadeTubes` 这类尤其如此。
    判据能用**累积量**就别用瞬时量(车速起落、`tubes` 下降、
    「没有变化」),累积量不受采样相位影响。
    反向对照每组都要带:「按另一个真会动的键,读数确实动」—— 这才能把
    「探针读不到」和「应用没反应」分开。

36. **对着会动的目标用固定容差校验传送,必然误判。** 车巡航 8-14 m/s,
    `__vcw` 快照最旧也近 1 s,读到坐标时车早开走了;`tp()` 里的
    `|x - want| < 0.05` 于是永远失败,表现为「进不去车」或「传送到
    24.6,30 但校验不过」。要传送到车上,必须**每轮重发**当前坐标
    (`__vcw_teleport = {x, z}` 是普通对象赋值,不是函数),传完立刻按 F。
    固定目标(拾取物、出生点)才可以用紧容差。

37. **转向类判据的硬前置是「车速 > STEER_MIN_SPEED」。**
    `TrafficCar::drive` 的 `yaw_rate` 有下限(`traffic.rs`
    `if speed > STEER_MIN_SPEED (1.2)`),静止时打满舵 `yaw` 恒定不变。
    上一条测项如果用 S 把车刹停了,下一条转向测项会全读出 `0.0000` ——
    那是物理,不是缺陷。每个转向测项都要**自己重新踩油门提速**并断言
    车速达标,否则一律 SKIP 并写明原因。
    车上的 `playerYaw` 就是 `car.get_yaw()`(`game.rs:5994`),所以驾驶时
    可以直接拿它当车头角度 —— 但仍然要先断言 `veh != null`。

38. **测「方向盘抢占」要用逐步增量,每步等 >= 4 帧。** `claim_steer` 的
    语义是「后按的赢,拥有者松手则控制权作废回到谁在按谁说话」
    (`game.rs:1905`)。按累计 `yaw - yaw_start` 判会把
    「D 接管」和「松 D 后回到 A」两步读成同一个数(3 帧节流),
    假 FAIL 一次。逐步增量 A 独占 -0.313 / D 接管 +0.152 /
    松 D 回到 A -0.334 / 全松 0.000 才是可分辨的。

## 参照产品先查,再判「缺陷」

判「键位对不齐」之前**必须**先查 GTA V 的默认键,否则会两头出错:
把刻意的省略判成缺陷,或者把真缺口判成「非目标键」。
本轮核实(官方 PC 手册,primary source;注意 Rockstar **没有**官方
controls 支持页,手册才是权威):R 换弹 / F 上下车 / V 切视角 / G 手雷 /
Space 跳跃 / WASD / Shift 冲刺 / A-D 转向 / 1-2-3 武器位。
以及三条容易搞反的:

* **ArrowUp/ArrowDown 在 GTA V 默认没有任何绑定**(相机是纯鼠标,
  `INPUT_LOOK_UP_*` 为 NONE)。所以「本游戏 ARROWUP/ARROWDOWN 在
  `TRACKED_KEYS` 里但没有消费者」**不是缺陷** —— `grep -c` 命中数
  4(定义 + `TRACKED_KEYS` + 两处 `#[cfg(test)]`)会让人以为它「像接了」,
  但命中数**必须区分测试模块和运行时消费者**,否则会既误判为已接线
  又误判为缺陷。
* **GTA V 没有独立地图键**(地图在暂停菜单里)。本游戏把 Tab 绑成
  地图属于**超出参照产品的增强**,不是缺陷。
* **GTA V 没有 holster 键**(1 就是徒手位)。本游戏的 H 属次要来源支持,
  官方文档未确认 —— 判为非缺陷,但 note 要写清「文档未确认」。

另外 `gta.fandom.com` 在转向键上写 `A, D / Left, Right Arrows`,
与官方手册矛盾(fandom 确实这么写),**不要采信**。

**不要从「光标进游戏就消失」判成缺陷。** 这是指针锁的正常表现,不是 bug。
锁定确实存在:canvas 的 click 监听里调 `locked_canvas.request_pointer_lock()`
(`game.rs:3949`),该调用必须由用户手势触发,所以启动时不能直接调。
仓库里曾经流传过一条「`src/` 全文无 `request_pointer_lock`」的结论,那是
过时的 —— 事实相反。凡是引用某条「不存在/不存在于 src/」的旧结论之前,
**重新 grep 一次**,这个仓库的渲染/输入接线改得很快。

## 反面教材:这一轮有三个 FAIL 全是探针自己的错

`w4` 的第一版对 Space/G/H/V/Tab/F/C/R 报了 4 条 FAIL,其中 **3 条是探针错**,
只有 R 是真的:

* **G**:`grenadeTubes` 是 3 帧节流字段,按下后 0.06 s 就读,拿到的是
  按下**之前**的快照。改成轮询到 `tubes` 真的下降 -> PASS。
* **C**:`Arsenal::reload()` 只是**开始**换弹(`set_reloading(RELOAD_TIME)`,
  `RELOAD_TIME = 1.1 s`),补弹在之后的 `finish_reload`。等 6 帧
  (~0.78 s)不够,读到的永远是 0。另一个坑:基线 mag 是在 H 测试留下的
  `Unarmed` 状态上取的(`magazine() == 0`,数字全是 0),
  必须先 `Digit1` 切 Pistol 再取基线。
* **Tab**:断言自己写反了(`dom0 == dom1` 才判失败)。地图本来就好。

判据:**每一��� FAIL 都要先问「这条通道能读出已知正确的值吗」**,再问
「应用是不是真的错了」。同一条测项重跑一次、换一个独立读数路径
(比如 camDist 换成「眼点到玩家的水平距离」)、再带一个反向对照,三条路
都指向同一结论,才是结论。

## 真实缺陷:`KEYR` 把相机从玩家身上扯走

`KEYR` 走 `camera.reset()` + `apply_default_view`(`game.rs:4386-4387`),
而 `apply_default_view`(`game.rs:2148`)把 `distance` /
`desired_distance` 设成 **250**、`target` 设成 `[0, 8, -30]` —— 那是
「城市全景机位」的自由观察预设(`game.rs:8391` 注释:只在按 Tab 切到
自由观察时用),不是「复位到跟随构图」。

三路独立读数一致(干净会话,无前置污染):

```
基线   camDist 8.2   眼点↔玩家 8.10 m
R×3    camDist 22    眼点↔玩家 18.76 m   (R 之后走路也不跟)
对照 C×3  camDist 8.2  眼点↔玩家 8.10 m  极差 0.000(通道能读出「不变」)
```

玩家按 R 之后镜头停在离自己 18 m 开外,自己走也不跟 —— 视角坏掉。
**修法**:R 应该复位到跟随构图(`FOLLOW_DISTANCE` + `follow_target = 玩家`),
把自由观察的 250 预设留给原本想用它的地方(比如另设一个键)。
注意 22 而不是 250,是因为 `update_camera` 每帧把镜头往 `follow_target`
阻尼收敛,250 会滑落到 22 —— 但落点不是 `FOLLOW_DISTANCE`。

 It stays on `window` once
    written, so an unguarded read returns the **previous position's** probe
    (measuring clearance at the wrong point), while a too-early read returns
    `""`. Correct pattern, every single time: clear the field, send the
    one-shot `{probe: true}`, wait, read, then **verify the probe's own
    `at (x,z)` header matches the point you asked about** — otherwise treat
    it as unavailable. Skipping the header check silently produced
    "净空读不到" everywhere in `w1`, which is how the stall verdict degraded
    to SKIP instead of measuring.

33. **`w5`'s 1500 s wall clock was too tight for its own work.** The
    building-collision step is a "30 frames x 2 candidate yaws" loop, each
    frame doing a 6-attempt probe with 2-frame waits, at 1.7 fps. It timed
    out standalone and reported "没跑完", indistinguishable from a real
    hang. Raised to 3000 s (time only, no verdict relaxed) and added
    `step()` breadcrumbs to stderr so a timeout names the phase it died in.

34. **`_static_check.py` does not catch `SyntaxError`.** A nested `def`
    helper using `await` passed the static check and then died at import with
    `'await' outside async function` — and because `verify8.sh` pipes through
    `grep`, the traceback was filtered out and the run looked like it
    produced no output at all. Always `ast.parse()` the file yourself after
    editing, and beware "worker exited with empty output" as a symptom of a
    traceback, not of a fast pass.

35. **`limbState.t` exports only the TRANSLATION column, so it can never
    show gait.** `src/game.rs:5210-5237` formats `m[12],m[13],m[14]` and
    nothing else. But limb posing is **pure rotation** --
    `limb_swing` feeds `Mat4::rotation_x` inside `limb_chain_matrix`
    (`src/player.rs:709-720`). So a "limb matrices did not change while
    walking" reading is **structurally guaranteed to be 0.0000**, not a
    defect. The rotation basis vectors (m[0..11]) are never exported, so
    no acceptance script can judge posing from this channel at all.
    **Use `gaitPhase` / `gaitAmount` from `__vcw` instead** (they are
    exported at `src/game.rs:5018` and *are* consumed by the renderer at
    `src/game.rs:7973-7997`, which clears and re-pushes every limb instance
    each frame). Measured: idle `gaitAmount=[0,0,0,0,0,0]`; walking
    `[0, 0.613, 0.887, 0.969]` with `gaitPhase` advancing
    `0 -> 1.907 -> 4.269 -> 0.376`. That is the whole animation proof, with
    no pixel work.

36. **Per-row ink-segment runs is the criterion that settles "fragmented
    or connected".** For a crop of the character, threshold luma against
    the crop's background (`abs(sub - median) > 18`), then count how many
    separate `True` runs each scanline has, and take the median over rows.
    A connected human figure gives **median 1-2** (one column through the
    torso, two through the legs); scattered shards give **median 5-7**.
    Measured at res=1.0, charBox 155x311: `median=2, max=7` for normal
    rendering and `median=1, max=5` with the world hidden. This is
    resolution-independent, needs no vision call, and -- unlike the
    in-box/out-of-box luma mean (trap 6) -- has no background gradient to
    hide in. Ship it as the numeric gate and use vision only to describe.

37. **Run a character-shape check at `res=1.0`, not `res=0.4`.** `?res=`
    scales the canvas *backing store* (`src/game.rs:8316`), so at
    `res=0.4` a 1280x657 CSS page is only 512x263 device px and the
    character is ~20x38 **device** px; at `res=0.25` it is ~22x11 px,
    where two legs cannot physically resolve. Vision then confidently
    reports "fragmented" about a perfectly good figure -- the two
    disagreements in this round (full frame "complete human figure" vs
    8x blow-up "fragmented") were entirely this artefact. `res=1.0` makes
    device px == CSS px (`rect.bw == rect.w`) and the question becomes
    answerable. Also zoom the camera to `FOLLOW_DISTANCE_MIN` first
    (`cameraDist` 2.2 gives charBox height 311 px instead of 88).

38. **`?hide=` is a real runtime debug switch, and the A/B can be run in
    ONE session.** `hidden_batches()` (`src/game.rs:2910`) re-reads
    `window.location().search` on **every rendered frame**
    (`src/render.rs:4296`), so `history.pushState` toggles batch
    visibility with no reboot. Do the A/B this way rather than booting two
    Chromes: same boot state, same player position, same camera. Read the
    limb batch ids from `__vcw.limbBatches` (they are `38..50` today but
    are **not a constant** -- hardcoding them is the same mistake as every
    other magic number in this suite).

    **Why they drift, so you stop treating a batch number as an identity:**
    the batch table is rebuilt on every streaming-centre change, and its size
    is data-dependent, so the same logical group gets a different index in a
    different part of the city. Measured composition:

    ```
    static_len over 140 streaming centres: {11: 2, 12: 63}
    batch count = 2 (ground+water) + static_len + DYNAMIC
    DYNAMIC = 13 player limbs + car bodies + 4*10 wheel batches + pickups
    ```

    So `limbBatches` read as `[37..49]` near one centre and the limb batch
    sat at `bn=100` near another -- **same app, same code, different index**.
    Never compare a batch id across runs, and never carry a batch id into a
    new probe: read `__vcw.limbBatches` in the same session you measure in.
    If a probe's verdict depends on the batch index, assert on the *set*
    (count + membership) and on per-batch instance counts, never on the
    literal number.

39. **The DOM crosshair is inside every charBox crop, and it is small.**
    `#vcw-crosshair` is a 16px white ring at `left:50%;top:50%`
    (`src/const.rs:1517`) and charBox is centred on the same axis, so it
    always lands in the crop. Measured footprint: **49 px = 1.02% of a
    51x94 box**, sitting in the upper half. It cancels exactly in a
    normal-vs-hide A/B (identical in both legs) and only mildly inflates
    absolute stats -- excluding its rows *raised* the std ratio from
    1.28x to 1.51x. Hide it (`el.style.display='none'`) before any vision
    call so it cannot be read as geometry, but do not attribute a verdict
    to it.

40. **`charBox` size is a function of camera distance, not a constant.**
    Its height is the projection of `PED_SCREEN_PROBE_HEIGHT` (1.75 m,
    `src/const.rs:710`) at the current follow distance. Sweeping the wheel
    moves it monotonically: `cameraDist 6.73 -> 4.86 -> 4.08 -> 2.2` gives
    charBox height `26.7 -> 36.6 -> 43.3 -> 311 px`. So a "charBox is
    51x94 not 45x88" report is usually the probe's own padding, not the
    app: `pad=3` per side adds 6px to each dimension, and
    `50.12-6 x 94.18-6 = 44.12 x 88.18` matches the expected `45 x 88`
    exactly.

36. **`walk_request` 会整个顶掉 WASD,所以键盘腿必须先显式清零。**
    `simulate` 里 `world_walk != [0,0]` 时,`forward` 直接取 `world_walk`
    且 `intent` 被改写成 `(1,0)`(game.rs:5960-5970)——按键轴根本不参与。
    不清零就去测 W,测到的其实是上一段残留的世界方向。
    同理 `W` 是**相机相对**的(`forward = [cos yaw, -sin yaw]`),
    用 `window.__vcw_aim = <裸数字>` 一次性钉住朝向;传对象会被
    `as_f64()` 静默丢掉(那是 `camera.set_yaw` 唯一入口)。

37. **`__vcw.vel` 是最好的速度通道,别再从位移反推 dt。**
    `Player::step` 结尾把 `vel` 设成 `achieved / dt` 并 clamp 到 ±speed
    (player.rs:549-554),所以它**与 dt 无关**,直接比 `WALK_SPEED` /
    `RUN_SPEED` 即可。实测 4.5998 / 8.3997,比值 1.8261。
    代价:`vel` 每 3 帧才 publish,所以**取中位数**,不要取首个值。

38. **页面内状态机里任何阈值都必须走对象前缀,不能写成裸全局。**
    把 `st.turnY` 写成裸 `TURN_Y_` 会 ReferenceError,而 `try/catch`
    会把它吞成一个安静的「判定永不触发」——掉头不发生,腿整段跑过头。
    同类:轮询用的 HUD 正则必须与 `format_hud` 的实际格式一致
    (`xyz x y z ... frame N`,**三个**坐标)。正则写成 5 连数字会静默
    失配,帧号读不出来,于是既采不到 `vel`、也等不到停止条件。

39. **楼梯下楼在门垛处「冻住」是正确碰撞,不是卡死。**
    逐帧全精度(`__vcw.playerY` + `vy` + `grounded`)显示:玩家在
    tread1 上 `y=0.455`、`grounded=true`、`|v|=4.5998` 满速,x 顶在
    `27.40` 不动 —— 那是前墙右门垛内表面 `27.75` 减半径 `0.35`。
    梯脚 `z=24.9` 正好落在门垛(world z[24.25,29.2])后面,几何上
    就该被挡。判「下楼」要**允许**在最后一级停住。

40. **冲刺会穿过 0.2 m 厚的室内墙(真缺陷)。** `resolve_interior_slide`
    用 `separate_interior` 做**位置推离**而不是**扫掠**
    (interior.rs:417-451):一帧位移 1.1 m > 墙厚 0.2 m,帧末人已在
    墙另一侧,推离向量为 0,`length <= EPS` 分支直接放行。
    同一面墙、同一时刻,步行(0.6 m/帧)零穿透。隔墙(0.15 m 厚)同样复现。
    **测任何室内碰撞修复都要在冲刺速度下测**,并且逐帧看 x 越过
    墙面内表面的那一帧。

    **已修(2026-10-06,HEAD `28d334f`)** —— 冲刺现在停在 `x=27.40`
    (= 门坎内表面 27.75 − 半径 0.35),隔墙停在 `25.825`。修法里藏着一个
    比缺陷本身更值钱的教训:**「子步细分」单测全绿也可能在应用里是彻底的
    no-op。** 第一版给 `resolve_interior_slide` 的帧位移做子步(每步从上一个
    子步的合法位置重走),单测通过 —— 浏览器里照样冲到 `x=41.5`。根因是
    **调用点传的子步起点错了**:`step_vertical` 喂进去的是**静态层推进之后**
    的位置,而静态 `CollisionWorld` 根本不含室内墙 —— 它把人推进墙里
    (`x=27.873`,已越过 27.75 面),随后 `push_out_aabb` 的「点在盒内」分支
    又把他从**远面**弹出去:

    ```
    x=27.850 -> 27.400   正确
    x=27.900 -> 28.300   穿透
    ```

    **推广:凡是「上一阶段输出喂给下一阶段」的管线,加子步/加迭代时必须确认
    起点是上一阶段的**起点**,不是上一阶段的**产物**。** 起点取错时,子步
    逻辑本身再正确,也只是在一个已经错的位置上做精细计算。配套:**缺陷活在
    调用点的参数里时,单测那个函数是测不到的** —— 必须有一条测**帧序列**的
    回归测试(第三个 commit 就是干这个的,验证过:还原起点就变红)。

    **由此得到一条验收纪律:改了碰撞/物理求解之后,「cargo test 全绿」不算
    验证,浏览器实测才算。** 上面这例是第一版修复单测通过、应用里是彻底的
    no-op;两者的差别只有在真引擎里跑冲刺才看得出来。给写手派活时要把这条
    写成硬要求:每个缺陷先在浏览器里复现出**具体读数**,修完再用同一通道
    复测同一读数,并把前后数据都交上来。复现不出来的就如实标「复现不了」,
    不要硬凑一个改动 —— 那会产出一个无法验证的 commit。

    **写手的自述里「单测 120 passed」不能代替你亲自跑一次。** 子 agent 的
    总结是自述,不是事实:自己跑一次 `cargo test`,再用 `git show --numstat`
    看每个 commit 到底动了哪些文件、动了多少行。一个声称「两个缺陷各一个
    commit」的交付常常是三四个 commit(补测、返工、起点修正各一个) —— 这不
    算超范围,但你必须知道实际数目才能判断它是不是真的收敛了。

    **「子 agent 说它跑过浏览器」同样不能代替你亲自看一眼。** 这一条是被用户
    驳回后才补上的:一棒交付「浏览器实测修复生效」并附了对照表,主 agent 据此
    对用户宣布「已修」,用户回「问题依然存在」。子 agent 的浏览器读数只证明
    **它那个会话**的状态,可能量的是别的东西 —— 批次号不同、流式中心不同、
    甚至是它自己新建的另一个窗口里的另一个页面。用户看的是自己那个窗口。
    **判定完成的门槛:主 agent 自己连上 CDP 复现过、或者用户眼验过。** 两者
    都没做之前,对外只能说「已修 + 子 agent 实测」,不能说「已验证」。

    **用户要求「自己通过浏览器验证」时,不要用转述代替执行。** 这是明确的
    工作方式要求,不是客套:把子 agent 的数字复述一遍不构成验证。要么按下面
    的 recipe 自己连上 CDP 量一遍,要么明说「我连不上,原因 X」并给出用户自己
    能跑的那条命令。

    41. **Graphics quality work must be gated on the rasterizer, not applied
       globally.** The context is created with `antialias: false` for a stated
        reason: the city is hard-edged low-poly and MSAA is too slow on the
        software rasterizer the test harness runs under. That is the right call
        for the harness and the wrong one for a real GPU, so toggling it globally
        either destroys the acceptance runs' frame budget or silently leaves real
        users on aliased edges. Same trap class as everything else here: a
        deliberate harness-only compromise becomes a shipped default when nobody
        re-reads the comment. Any rendering change in this repo must (a) re-derive
        the current backend and its deliberate compromises from source before
        proposing anything, (b) gate expensive quality features on a detectable
        runtime capability rather than on which machine is testing, and (c) be
        checked against an in-flight backend migration plan before it lands,
        because migrating the backend invalidates the diff. See
        `references/render-graphics-work.md` for the re-derivation recipe.

## Real application defects this harness has confirmed

2. **Sprint tunnels through thin interior walls** (confirmed 2026-10-02,
   HEAD 43c340a). Holding Shift+W from the LOFT stair foot toward the
   front wall: walk stops dead at x=27.40 for 16+ frames (correct, =
   jamb face 27.75 minus radius 0.35); sprint goes 27.40 -> 43.0 in 15
   frames, 15.25 m of penetration. Reproduces on the 0.15 m partition
   wall too, so it is a general long-frame tunnelling bug, not a
   stair-corner artifact. `resolve_interior_slide` (interior.rs:417)
   resolves by *position push-out*, never by sweeping the frame's
   segment, so any frame longer than the wall thickness skips the wall
   entirely. Fix belongs in `resolve_interior_slide`: substep the
   frame's `delta` against the wall AABBs (the same treatment
   `support_along_frame` already gets for treads) and clamp each
   substep's normal component.

3. **Diagonal movement is sqrt(2)x faster, contradicting its own
   comment.** `Player::step` builds the target as
   `dir*forward + perp*strafe` (player.rs:509-516), so W+D yields
   `|v| = 4.6*sqrt(2) = 6.5052` and Shift+W+D yields `8.4*sqrt(2) =
   11.8792` — measured 6.5052 and 11.8787, both to 4 decimals. The
   comment right above it claims "斜向移动不会比直线快". If diagonals
   are meant to be capped like GTA V, normalise `intent` before use;
   if the sqrt(2) diagonal is intended, the comment is wrong and
   every speed criterion that assumes |W+D| == |W| is wrong with it.

1. **Arrow keys are dead.** `git grep -c ArrowUp -- src/` = 1: only the
   constants at `src/const.rs:76/107/109/129`, referenced nowhere else.
   Not in `TRACKED_KEYS`, no `keydown` branch. Driving steers from
   `game.rs:5859/5865` `steer_input = strafe_input = axis(KEYD, KEYA)`
   (A/D only). GTA V binds arrow keys for steering by default, so this is
   a genuine gap. Fix belongs in the app: fold `ARROWLEFT/ARROWRIGHT` into
   the steer input and add them to `TRACKED_KEYS`. Note `__vcw` exposes no
   `carYaw` (only `carX[]/carZ[]/carSpeed[]` and
   `carDriveX/Z/Speed`), so steering must be measured from the change in
   travel direction, with a working control key to prove the measurement.
   **CONFIRMED FIXED 2026-10-02 at HEAD 43c340a** (measured, not inferred):
   while driving, `dyaw` per frame ArrowLeft -0.1063 / ArrowRight +0.1044
   against A/D controls at -0.2313 / +0.1044; sign confirmed by **two**
   independent paths — the angle sign, and the geometry (displacement
   dotted with the game's own `right = [fwd[1], -fwd[0]]`), which does not
   assume any sign convention. On foot the arrow keys are correctly inert
   (dx = dz = 0 for all four). Do not re-dispatch this one.

2. **The reload key does not match GTA V (R).** `KEY_RELOAD = "KeyC"`
   (const.rs:1097) while `KeyR` is bound to `camera.reset()` +
   `apply_default_view()` (game.rs:4384-4388), and GTA V PC defaults to
   **R** for reload. Isolated by a controlled same-magazine A/B on one
   page: a non-full `PISTOL · 6/36` left **unchanged** by R over 19 frames,
   and the *same* magazine became `RELOADING` -> `PISTOL · 12/30` under C
   (reserve 36-12=24 drawn, 6+24=30 -- the arithmetic confirms a real
   reload, not a UI string). Both keys are in `TRACKED_KEYS`
   (game.rs:114/118) and never shadow each other, so this is a pure
   binding choice, not a wiring gap. Every other GTA V-aligned key in
   `const.rs` carries an explicit "GTA V 的 X" doc comment (Space/G/H/V/Tab)
   -- `KEY_RELOAD`'s doc is a bare `/// 换弹键。`, i.e. the deviation was
   never a recorded decision. Fix belongs in the app: move reload to `KeyR`
   and re-home or drop the camera reset (GTA V has no R-camera binding).

   **The R binding is worse than a wrong key — it breaks the camera.**
   `apply_default_view` (`game.rs:2148`) sets `distance` /
   `desired_distance` to **250** and `target` to `[0, 8, -30]`: the
   city-panorama free-look preset, not "reset to follow". So pressing R
   leaves the camera parked ~19 m away from the player and it does **not**
   re-attach when the player walks. Clean-session A/B, three paths agreeing,
   with a live control:

   ```
   baseline    camDist 8.2   eye-to-player  8.10 m
   R x3        camDist 22    eye-to-player 18.76 m   (walking after R: still detached)
   control C x3 camDist 8.2  eye-to-player  8.10 m   spread 0.000
   ```

   The control matters: it proves the channel can read "no change", so the
   8.2 -> 22 jump is R's doing and not measurement drift. Note 22 rather
   than 250 because `update_camera` damps the eye toward `follow_target`
   every frame, so 250 slides down to 22 — but it does not land on
   `FOLLOW_DISTANCE`. Judge R on **eye-to-player horizontal distance**, not
   `cameraDist` alone, since the two disagree while the eye converges.

      **CONFIRMED FIXED** (reload moved to `KeyR`, C released, `camera.reset`
      + `apply_default_view` **deleted rather than merely unbound** -- they had
      a single caller, the R arm, and no test depended on them; and the `KEYR`
      constant had to be deleted too, because once `KEY_RELOAD` is `"KeyR"` the
      two constants are the same code and the earlier camera arm would shadow
      the reload arm). Post-fix readings: `R` on a non-full magazine gives
      consecutive `RELOADING` then full magazine with reserve decremented by the
      drawn count (real arithmetic, not a UI string); `C` is inert across 24
      frames; camera `camDist` holds at `FOLLOW_DISTANCE` across `R`. **Do not
      re-dispatch this one** -- but do repair the suite, which still asserts
      `C` reloads and `R` resets (trap 8b).

   3. **Nothing else.** The rest of the historical FAILs were judgment bugs --
   including the combat "player cannot fire" and "wall-clip damage" reports,
   both of which were harness artifacts (see #33, #34, #35, #37).

4. **Street scatter placed props inside the roadway** (fixed). My own diagnosis
   for this was wrong and the fix agent caught it: I asserted the lateral
   jitter was pushing palms into the lane, and the agent measured the lateral
   offset landing well inside the sidewalk band — the real violation was
   **along-street**: the along-street coordinate is unconstrained, so it crossed
   a crossing street's axis every block and dropped a palm on the asphalt at
   every junction (138 of 830 in the sampled region). Fixed by excluding
   intersections from planting, keeping the irregular spacing that the jitter
   exists to provide. Regression assertion: every generated prop's distance to
   the nearest road centreline must be `>= STREET_HALF_WIDTH`.
   **Generalised: when a placement rule is `base + jitter`, both terms are
   individually legal and the sum may not be — so assert the SUM against the
   constraint, never either term alone, and re-derive which axis actually
   violates it before fixing.** The wrong-axis diagnosis is invisible in review
   because both axes look plausible in the source.

5. **Dynamic groups were not re-placed when the static batch segment was
   swapped** (fixed). Crossing a streaming-centre boundary rebuilt the static
   part of the batch table, and appending the new static groups at the tail kept
   them *in order* but did nothing to keep them *within the truncate*: the
   rebuild truncates to the static count, and everything after it in the table
   — 13 player limbs, car bodies, wheel batches, pickups — went with it. Their
   stored indices then indexed past the shortened table, the instance writer
   got `None`, and the player mesh stopped drawing partway through a walk,
   matching "the character disappears after I move a short distance". The
   static-segment length is also **data-dependent** (both 11 and 12 measured),
   so a count cached at scene build time makes the next rebuild slice at the
   wrong offset — the same bug at a different offset. Fix re-places the dynamic
   segment on every rebuild and writes the new length back.
   Note this is the *second* defect with that exact user-visible symptom, so
   when one shows up, read the rebuild path before anything else.

6. **Groups sharing one draw batch erase each other** (fixed; measured, visual
   confirmation still owed). The body-group path looked up an existing batch by
   mesh identity, so two cars of the same model — and the roster has fewer
   models than cars — resolved to the same batch index. The per-frame instance
   writer clears before pushing, so the second car wipes the matrices the first
   just wrote: one frame ends with bodies drawn for only as many cars as there
   are distinct models, while wheels (each in their own batch) are all present.
   That is exactly the reported symptom "only the wheels are there". Fixed by
   giving each body its own batch, matching how wheels are already handled.
   **The general trap: `clear()`-then-push instance writers make batch sharing a
   correctness requirement, not an optimisation.** Any two objects that can
   coexist in one frame must own separate batches, or the last writer silently
   wins.

Defects 4 and 5 were both reported from the rendered frame, not from a probe,
and both were invisible to `cargo test`.

## Known-stable app facts (verify before relying on them)

- **Reload is `KeyR` (GTA V's key); `camera.reset` / `apply_default_view`
  no longer exist at all.** There is no `Digit4` -- only `DIGIT1/2/3` map to
  Pistol/Smg/Bat; grenades are `KeyG` and unarmed is `KeyH`. `Weapon::Bat`
  prints `BAT · melee` with no mag/reserve (`Weapon::magazine() == 0`).
  `Camera::new()` still initialises `distance`/`desired_distance` to 250 --
  that is the orbit-constructor default, NOT a live camera preset, because
  `Game::new` calls `set_desired_distance` on the very next line. Do not
  "fix" it as if it were reachable at runtime.
- **Firing the last round auto-reloads** (game.rs:6354-6360), so a held
  trigger never leaves the magazine resting at 0.
- **Spawn HP is 100**, and armor regen pushes HP back up over time --
  measure drops with min/max over a trace, never against a 100 baseline.

- Speed: `WALK_SPEED = 4.6`, `RUN_SPEED = 8.4` (`player.rs`)
- Jump: `JUMP_VELOCITY = 7.4`, apex ~1.245 m analytic
- Keybinds: `KEY_SPACE` / `KEY_GRENADE`("KeyG") / `KEY_UNARMED`("KeyH") /
  `KEY_CAMERA`("KeyV") / `KEY_MAP`("Tab") — `const.rs`, always via named
  constants. Grepping the literal `"KeyG"` in `game.rs` finds nothing and looks
  like a missing binding.
