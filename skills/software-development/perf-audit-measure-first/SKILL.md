---
name: perf-audit-measure-first
description: 'Use when judging whether performance can be improved.'
version: 1.0.0
author: hermes-curator
license: MIT
metadata:
  hermes:
    tags: [performance, wasm, browser, cdp, rust]
    related_skills:
      - rust-wasm-perf-audit
      - euv-engine-renderer-api
      - browser-app-self-verification
---

# Perf audit: measure before proposing

## When to Use

- 用户问「性能还能不能优化」「制定优化计划」「验证优化效果」。
- 任何在动手改之前需要先判断「值不值得改」的 Rust-WASM / 前端性能场景。

## The rule

**A user asking "can we optimize performance?" is asking for a measurement, not a
plan.** Answering with a plan built from reading code is the failure mode.

## Procedure

1. **Baseline build + gates first.** Unpiped `cargo check` across every WASM entry
   crate; capture the real exit code (see `rust-wasm-perf-audit` §2).
2. **Read the codebase for prior optimization markers** (`grep -rhoE 'OPT[- ]?[0-9]+'`)
   before proposing anything new. Continuous numbering means work already landed.
3. **Measure in the browser, do not read code to find hotspots.** Concretely:
   - FPS per page/route
   - rAF frame interval median + p95, and count of long tasks
   - JS-boundary crossings per frame (patch `Reflect.get` / count calls)
   - boundary crossings + attribute writes per *signal update* (the framework's
     real re-render cost)
4. **Compute the headroom before recommending.** crossings x ~110ns vs the 16.7ms
   frame budget. If the win is under ~1% of budget, say so plainly.
5. **Report the verdict even when it is "there is nothing meaningful left."**

## Pitfalls

- **A 60 FPS vsync-capped app tells you nothing about headroom.** Every page pinned
  at 60 means the demos are not the bottleneck. Say that instead of inventing work.
- **Never recommend micro-optimizations whose win you cannot measure.** Removing one
  boundary crossing per frame against a 16.7ms budget is noise, and touching that code
  risks regressing a just-fixed path. Recommend it as *not worth doing*, explicitly.
- **Patching `Reflect.get` after first call undercounts**, because engines cache the
  `Function` object. Install the spy *before* the first render, or the number is 0 and
  looks like "the loop isn't running."
- **Distinguish demo cost from engine cost.** A raymarching page at 55 FPS is shader
  load, not framework overhead. Do not present it as an engine defect.
- **Verify the measurement changed the thing you observed** (e.g. counter value
  incremented). A click that silently missed yields a confident, meaningless "0 writes."

## Reporting shape

Lead with the measured table, then the verdict, then tiers (low-risk / architectural
/ do-not-do). Give the honest recommendation to stop when the evidence says stop, and
name the regression risk for each tier given the tree's current state.

## Support files

- `references/measurement-recipes.md` - the CDP snippets for FPS, frame interval,
  long tasks, and per-signal-update boundary counting.
