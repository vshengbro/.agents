---
name: cdp-browser-harness-speed
description: Use when a CDP browser harness is slow.
---

# Speeding up a CDP browser harness

## Measure the round trip before optimising anything

A single `Runtime.evaluate` can cost **~670 ms** — not ~1 ms — because the
renderer's main thread is saturated. Measure it, do not assume:

```python
lat = [await timed(lambda: d.ev("__vcw.frames")) for _ in range(60)]
median(lat)   # the number that decides the whole design
```

Count round trips per unit of work, then multiply. A loop doing 5
evaluates per iteration pays 3.4 s per iteration of pure protocol.

## Batch the work into the page

Move the aim/step/sample loop *into* the page as one async IIFE returning
an array of samples. The page half must **not decide anything** —
arrival, stall counting, thresholds and recovery all stay in Python. Pass
thresholds in as parameters so each predicate keeps exactly one owner. A
faster stride through an unchanged predicate cannot change what counts as
arrived.

## Traps that cost more than the optimisation saved

1. **`JSON.stringify` on a promise yields `undefined`.** Wrapping a
   promise-returning expression in a *synchronous* `try/catch` then
   stringifying silently returns None. Make the wrapper `async` and
   `await` inside the `try`. Symptom: every leg skips straight to the
   fallback path and no error is raised.

2. **One awaited `rAF` is not one frame.** The sampler callback is queued
   *ahead* of the renderer callback that writes the frame counter, so the
   counter is often unchanged after a single `rAF` (measured: 2 of 6
   samples). Keep yielding until the counter actually moves, with bounded
   patience. Symptom: a chunk returns 2-3 samples and walks ~0.2 m.

3. **Re-deriving a threshold when the sample rate changes.** A stall
   threshold tuned for a ~0.7 m stride read per *frame* (~0.08 m) saturates
   on the first tick, so every leg declares itself stuck and the recovery
   path never runs. Re-derive: window the displacement to span the original
   threshold, and **skip samples while the window is still filling** or the
   warm-up logs phantom stalls.

4. **Check the trip condition inside the sample loop**, not after it.
   Checking once per chunk lets the counter run to 18 while the extra
   samples count as continued progress.

5. **A diagnostic disappearing is a regression, not a win.** Compare
   diagnostic token counts before/after (`slide`, `STUCK`, per-stride
   fields). Zero of a diagnostic the baseline had means a path stopped
   running — find why before shipping.

6. **An early `return` on a recovery path can delete diagnostics.** If
   recovery is reachable on every blocked leg it will always be taken and
   everything after it is dead code.

## Baseline hygiene

- Run before and after on the **same** instance; record fps for both and
  only compare equal-fps runs.
- Snapshot the baseline to a frozen file *before* editing
  (`cp full_sweep.py baseline_full_sweep.py`) — other agents edit
  concurrently, so `HEAD` is not a baseline.
- **Measure fps on a quiet machine.** Under load (many Chrome tabs, clippy)
  it reads 1 fps instead of 20, and every timing conclusion inverts.

## Verify offline too

Page-side logic is testable without a browser: generate the JS, run it in
`node` against a stub `__vcw` that models the *measured* browser behaviour
(dropped counters, hung tab, wall). Bugs in stop conditions are otherwise
invisible in a browser run — the leg just fails later. Substitute a unique
marker: not `%`-formatting (the JS is full of `%` from `toFixed`), and not
a token that also appears in a comment, or the injected multi-line JS
splits the comment and is parsed as statements.

## bash `GROUPS` is a read-only special variable

A parallel-verification script that does `GROUPS=(p1 p2 p3 ...)` **fails
silently**: bash's `GROUPS` holds the current user's supplementary group IDs
(16 elements on this machine), so the assignment is ignored and the loop
iterates `20 12 61 79 80 81 701 ...` — the script then tries to run
`sweep/20.py`. One-line proof:

```bash
bash -c 'GROUPS=(a b c); echo ${#GROUPS[@]}'   # prints 16, not 3
```

Prefix your variable names (`PROBE_GROUPS`, `CASE_GROUPS`). Same trap for
`UID` `EUID` `SECONDS` `PIPESTATUS` `FUNCNAME` `HOSTNAME` `SHELLOPTS`.

Related: `for i in "${!ARR[@]}"` + `x="${ARR[$i]}"` breaks silently on
out-of-range indices (expands empty, `x` degrades to the previous `$!`).
Iterate values with `for x in "${ARR[@]}"` and bump a port counter separately.

## Never judge a long group from its mid-run log

The heavy group (9 waypoints x 3 slide retries each) takes **13+ minutes**.
Mid-run it prints `wp0 err=1.17m -> wp1 err=3.35m -> wp2 err=4.73m` — error
grows monotonically and looks like a functional regression, but it is normal
waypoint progress; the final verdict is `best y=3.20 m` PASS.

Trust only the `=== summary ===` block. Two related traps:

- **Don't use log mtime to decide "did it run"** — record a baseline mtime
  first, then compare; a `rm -f`'d-but-not-yet-recreated log still exists
- **`| tee file` buffers** — a live process can have a 0-byte log, which is
  not a hang

## 6 parallel headless Chromes intermittently kill renderers

Symptom: `ConnectionClosedError: no close frame received or sent`, while
`curl /json/version` on that port still returns **UP** — the *page renderer*
died, not the browser, so "the browser is alive" does not rule this out.
Re-run the failed group alone; it passes. Don't change the code under test.
