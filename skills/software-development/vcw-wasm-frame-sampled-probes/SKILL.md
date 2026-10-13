---
name: vcw-wasm-frame-sampled-probes
description: Use when probing a WASM game over CDP with slow rAF.
---

# 采样 WebAssembly 游戏里的瞬时状态

`__vcw` / `__VCW_DEBUG__` 这类快照钩子不是逐帧写的。`vice-city-web`
里 `publish_debug_state` 每 3 帧才跑一次(`frame_count.is_multiple_of(3)`),
而无头 SwiftShader 下 rAF 只有约 1.7 fps。两者叠加,快照相对模拟有
**最多 3 个 rAF 帧**的滞后,混合时间可达数百毫秒。

## 规则

**按帧计数推进,绝不按墙钟。** `vlib.wait_frames(budget)` / `frames()`
读的是 `window.__vcw.frames`,不是 `time.sleep()`。

**读「最后一次」而不是「第一次」。** 事件闭包跑在 RAF 之外,按键效果
出现在 trace 的**后面**几行。取首值读到的是「按之前」的状态 —— 这一条
曾把 V / Tab 两个已经生效的功能判成 FAIL,而 DOM 读数明明是对的。

**瞬态现象(顶点、峰值)不能直接从快照读。** 采样网格几乎必然错过
apex。跳跃顶点 0.673 s 滞空 ≈ 40 个逻辑帧,3 帧一采样只有约 13 个点;
实测读到的 0.9067 m 是 apex **之后**的那一次。判据要么放宽到
「apex 之前最后一个采样格必然覆盖到的值」,要么把精确值交给单元测试
(解析式 + 真积分),快照只验「形状对不对」。

**物理常量从代码反解,别用快照顶格。** 快照里读到的高度受
`MAX_FRAME_TIME` 钳位影响:同一个 `v0 = 7.4` / `g = 22`,60 Hz 下
apex 1.183 m,无头被钳到 `dt = 4/60` 时 1.000 m。拿无头读数当真机
规格会写错测试。

**判据要认「恰好 -1」而不是「变了」。** 手雷数变化既可能是投了一颗,
也可能是地上捡了一颗。

**枚举判别值要从源码数,别背。** `Weapon` 里加一个新变体在末尾,
判别值就是旧的最大值 +1;写死数字会随别的插入而失效。

## 陷阱

- web-sys 的 `set_text_content` / `set_attribute` 会**重入 JS**;持有
  `RefMut<Game>` 时调它会 panic。写 DOM 前必须先 `drop(game)`。
- 造 DOM 面板默认给 `display:none`,但**验收要查 DOM 的 style 真的
  变了**,而不只是查状态布尔 —— 布尔可能对而面板没显示。

## 相关

- `verifying-against-a-real-gate` —— 同类「读数不等于事实」的坑。
