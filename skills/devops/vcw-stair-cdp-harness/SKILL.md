---
name: vcw-stair-cdp-harness
description: Use when driving vice-city-web's CDP harness for stairs.
---

# vice-city-web CDP harness traps

Every one of these was hit while measuring the stair paths. Each produces a
*plausible but meaningless* reading, so check them before believing any number.

## 1. `__vcw_teleport` has early-return branches that eat the whole request

`apply_teleport_request` (game.rs) checks, in order: `probe` -> `speed` ->
`safe` -> `walk` -> `hold` -> teleport. **Each matched branch `return`s**, so any
unmatched field in the same object is silently dropped.

```js
window.__vcw_teleport = {safe: true, x: 27.3, z: 24.9}   // teleports NOWHERE
```
The `safe` branch returns before the x/z read. The player stays at
`SPAWN_POINT` (33.5, 45) -- open ground, no stairs -- and every subsequent
reading is garbage. **Send `safe` as its own request.** Field names are `x` /
`z` (not `posX`); `walk` is one-shot, `walk_request` then persists.

## 2. Always read the position back, with a tight tolerance

`tp()` must poll until `|x-want| < 0.02`, print `dx_err` / `dz_err`, and
**raise** on mismatch. `0.6` is far too loose -- it passes while the player is
still on the ground floor.

## 3. `frames` is incremented per rAF but published every 3rd

`frame_count += 1` runs every frame (game.rs ~8053); `publish_debug_state` runs
only on `is_multiple_of(3)` (~8128). So:
- consecutive samples span **3 real frames** -- report stride as
  `dist / frame span`, never per-sample;
- a per-rAF sampler records the same snapshot 3x; dedupe on `frames`;
- a freshly teleported position can be up to 2 frames stale -- poll, don't
  read once.

## 4. Don't poll from Python once per frame

Each frame = one CDP round trip; a 22-frame run took minutes and the socket
died twice with `ConnectionClosedError`. Wait **inside the page** keyed on
`window.__vcw.frames`, using `setTimeout` (not a tight rAF chain, which keeps
the renderer main thread busy enough to blow the evaluate timeout).

## 5. Sample before you send the walk request

The walk request is consumed on the very next frame. A gap between the request
and enabling the sampler loses the first two frames -- on a 1.7 fps renderer
that is the entire first tread.

## 6. Teleport preserves foot height

`set_position([x, here[1], z])` -- there is no y channel. A bare x/z teleport can
**never** place the player on the upper floor. Any descent run must walk up
first, then reverse. And the run must **stop at the landing**: left running, it
crosses the floor and steps off the far edge (ends x=18.3, y=0.15 -- a fall,
not a stair), so the next run starts on the ground floor.

## 7. Save incrementally

Flush the JSON after each path. Two runs crashed before the final write and
lost every reading.

## The fixture trap (not harness, but it burned the same run)

`slab_world()` in interior.rs has the ground floor and the treads **overlapping
in X** (floor to 5.75, treads 4.45..5.75), so a below-the-feet surface can
never win there -- the real defect is unreproducible on that fixture. The real
showcase geometry has the floor reaching x=27.75 while tread 1 starts at
27.10. Use `overhanging_ground_world()` for anything about stair descent.
