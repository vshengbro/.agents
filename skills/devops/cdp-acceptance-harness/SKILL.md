---
name: cdp-acceptance-harness
description: Speed up slow or lossy CDP browser acceptance harnesses.
---

# Speeding up a CDP acceptance harness

A harness that drives a real page over the Chrome DevTools Protocol spends
almost all its wall clock in `Runtime.evaluate` round trips, not in the
simulation. Optimize the round trips, but verify the frame rate first — if
the page is throttled, no protocol change can fix the runtime.

## Measure before touching anything

Three probes, in this order. Each one invalidates a common assumption.

1. **Round-trip latency.** `Runtime.evaluate` on a busy renderer costs
   ~670 ms, not ~1 ms. Time 60 consecutive calls and take the median. If
   the median is in the hundreds of milliseconds, count round trips as the
   budget and divide the segment's total by it to get the number to remove.
2. **Real frame rate.** Read the page's own frame counter twice, 5 s
   apart. Headless Chrome with many tabs on the same machine runs at
   1-2 fps, not 60 — and a multi-minute "hang" is usually a machine at
   load average 50+ with 80 renderer processes, not a code defect.
3. **Work per round trip.** How far does the player actually move while a
   protocol call is outstanding? If it is 0.08 m per 670 ms, the harness
   is protocol-bound and the fix is batching.

Before/after numbers are only comparable if both runs saw the same frame
rate. Re-measure fps in every run and report it, or normalize by
`wall * fps` to compare simulated seconds.

## Batch the sampling page-side

Put the sample loop in the page and return the whole trace in one
`Runtime.evaluate`. Keep every *decision* in the harness language:
arrival tests, stall counters, retry schedules and fallback strategies
stay outside, so a faster stride cannot change what counts as success.
The page re-aims and records; it does not decide.

- Persistent request state does not need re-sending every iteration. If
  the game holds the last direction until cleared, re-writing it is a
  no-op — but confirm in the source before relying on it.
- A request *magnitude* is often only a direction hint; the speed comes
  from a constant in the engine. Check before assuming it scales.
- Pass thresholds *into* the page rather than hard-coding them there, so
  the predicate keeps exactly one owner.

## Three traps that cost real time

**A synchronous try/catch around an async IIFE silently returns
`undefined`.** `JSON.stringify((() => { try { return (async () => ...)()
} catch (e) { ... } })())` stringifies a *Promise*, which is `undefined` —
so every call returns None and the code under test never runs. The wrapper
must be `(async () => { try { return JSON.stringify(await EXPR) } catch
(e) { ... } })()`. Verify it against a real page before trusting a green
run: an async-IIFE expression must come back a dict, not None. A harness
whose *own* boundary is dead will still report every downstream check as
passing, because the fallback path is slower but reaches the same verdicts.

**A "clean" acceptance run can be clean because the harness never ran the
thing under test.** When a page-side batcher always returns None, callers
fall through to a slower fallback that reaches the same verdicts — the
result table looks perfect while the optimization is dead. Before reporting
a full pass, assert one representative call returns a value of the
expected type, and diff the working lib against the file you are editing:
fixes often land in a scratch copy that nothing imports.

**One awaited `requestAnimationFrame` is not one frame.** The sampler's
rAF can be queued ahead of the renderer callback that writes the frame
counter, so the counter often has not ticked when the promise resolves —
measured at 2 in 6 samples. Wait until the counter *moves*, with a bounded
retry, before concluding the loop is dead.

**Retune distance thresholds when the sample interval changes.** A 0.30 m
"did not move" threshold is sane for a 0.7 m stride and catastrophic for
a 0.08 m one: every sample trips it, the loop exits on the first tick, and
every downstream diagnostic silently stops appearing. Measure the
per-sample distance first, then size the window so a free walk clears the
bar with margin. The robust form measures displacement over a *window of
samples* spanning a fixed distance rather than against the previous sample:
pick `N` so `N * per_sample_distance` clears the threshold with margin
(0.08 m/frame against a 0.30 m bar → N=6 → 0.38 m), and while the window is
still filling skip the test instead of measuring from the walk's origin —
otherwise a free walk logs phantom stalls and trips immediately.

## Distinguishing "no lines" from "no code"

Fewer log lines is ambiguous: it can mean the code is gone, or that the
fast path succeeded and never needed it. After a speedup, drive a
*deliberately blocked* target to force the slow path and assert the
diagnostics still print. Check each required field explicitly.

## Test the page-side logic offline

The JS a harness injects can be replayed against a stub in `node`, with a
`__vcw`-shaped fake and a fake `requestAnimationFrame`. Model the awkward
real behaviours (dropped counters, a hung tab, a wall) and assert the
sampler survives them. This is far faster than a browser round trip and
catches the silent-empty-result class of bug, which a browser run reports
only as "the whole segment failed".

Model wall-time and output-format behaviour in the stub too, or the tests
will pass against behaviour the browser does not have.

## Static checks worth keeping

- A name assigned only inside a loop and read after it is a real
  UnboundLocalError that fires minutes into a run. Check for it. Keep the
  check advisory: sibling loops under one block can pair unrelated names,
  and a check that cries wolf gets ignored.
- Freeze a baseline copy of the script before editing, and load the
  helpers out of both by path in one harness, so before/after runs use the
  real code without duplication.

## Before finishing

- Sync any re-exported/shared prefix by splitting on a content marker
  (`# ---- N. name`), never a hard-coded line number, and re-check it
  after every edit — it goes stale silently.
- Always set `Network.setCacheDisabled` and open tabs with `/json/new`; a
  cached `.wasm` makes a server-side fix look like it did nothing.
- Note that concurrent agents editing the same file will overwrite your
  work. Re-read before patching, and re-run the benchmark at the end
  rather than trusting an earlier number.
