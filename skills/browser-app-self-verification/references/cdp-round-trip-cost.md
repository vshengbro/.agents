# The round trip is the budget, not the simulation

The recipes above treat a `Runtime.evaluate` as free. It is not: on a
busy page a single one costs **~670 ms**, not ~1 ms, because the renderer
main thread is saturated and the evaluate queues behind the frame being
built. A harness that spends 5 round trips per stride pays 3.4 s of pure
protocol to advance 0.7 m of ground. That is the whole optimisation.

**Measure it before designing anything.** The number decides the design and
is not guessable from either end — a loop that looks correct can be 99%
protocol.

```python
lat = []
for _ in range(60):
    t = time.monotonic()
    await d.ev("__vcw.frames")
    lat.append((time.monotonic() - t) * 1000)
print(f"median {statistics.median(lat):.1f} ms  max {max(lat):.1f} ms")
```

Then count the round trips per unit of work and multiply. Where a loop does
`st` + `ev` + two polls + `st` per iteration, the fix is not a smaller sleep
— it is fewer round trips.

## Batch the loop into the page, decide nothing there

Move the aim/step/sample loop into one async IIFE that returns an array of
samples. The page half must **not decide anything**: arrival, stall
counting, thresholds and recovery all stay in Python, and thresholds are
passed in as parameters so each predicate keeps exactly one owner. A faster
stride through an unchanged predicate cannot change what counts as arrived,
which is what makes the change safe to make at all.

The payoff is proportional: a 20-frame chunk that cost ~200 round trips now
costs one.

## Traps that each cost more than the optimisation saved

These were all silent — the harness kept running, kept getting faster, and
kept producing wrong numbers.

**`JSON.stringify` on a promise is `undefined`.** Wrapping a
promise-returning expression in a *synchronous* `try/catch` and then
stringifying the result returns `undefined`, not an error, and the caller
receives `None` on every call. The symptom is that every leg skips straight
to the fallback path and no exception is ever raised. Make the wrapper
`async` and `await` inside the `try` so a rejected promise is reported the
same way a synchronous throw is.

**One awaited `rAF` is not one frame.** The sampler callback is queued
*ahead* of the renderer callback that writes the frame counter, so the
counter is often unchanged after a single `rAF` — measured at 2 unchanged
out of 6 samples. Treat that as "no frame happened yet" and keep yielding
until the counter actually moves, with bounded patience. The symptom is a
chunk returning 2-3 samples having covered ~0.2 m.

**A threshold tuned for one sample rate silently inverts at another.** A
stall threshold calibrated against a 0.7 m stride, applied per *frame*
(0.08 m at walking speed), saturates on the first tick: every leg declares
itself stuck and the recovery path never runs. Re-derive it when the sample
rate changes — window the displacement to span the original threshold, and
**skip samples while the window is still filling**, or the warm-up logs
phantom stalls and trips the counter on open floor.

**Check the trip condition inside the sample loop.** Checked once per batch,
the counter runs to 18 while the actor sits against a wall, and the extra
samples then count as continued progress.

## Count diagnostics before and after — a vanished token is a dead path

The only cheap way to notice a code path silently stopped running. Tally a
fixed set of diagnostic tokens on both logs:

```bash
for t in "\[slide \d\]" "STUCK at" "gave back" "\[walkReq="; do
  printf '%-14s before=%s after=%s\n' "$t" \
    "$(grep -c "$t" before.log)" "$(grep -c "$t" after.log)"
done
```

**Zero of a token the baseline had means a branch is now unreachable**, and
it will not show up in a pass/fail verdict. Two such bugs hid here: a stall
trip evaluated only after a whole batch, and a recovery branch whose
early-return condition held on *every* blocked leg, so the slide after it
never executed. Both runs passed and both were faster.

Two corollaries:

- **An early `return` on a recovery path is a deletion.** If the condition
  holds on every case the path is meant to handle, everything after it is
  dead code and ships untested.
- **A speedup can make a fallback path unexercised.** Once every leg
  succeeds directly, recovery never runs, so a clean run proves nothing
  about it. Force the failure (aim into a known wall) and assert the
  recovery diagnostics still fire.

## Verify the page-side logic offline too

Stop conditions are testable without a browser: generate the JS, run it in
`node` against a stub debug object that models the *measured* browser
behaviour — dropped frame counters, a hung tab, a wall. Bugs in stop
conditions are otherwise invisible in a browser run, because the leg just
fails later and the log points at the geometry.

Two substitution traps, both of which produce a parse error that reads like
a logic bug:

- the harness body is full of literal `%` (`toFixed(3)`), so `%`-formatting
  raises `not enough arguments`;
- a placeholder token that also appears in one of your own comments splits
  that `//` line and the injected multi-line JS gets parsed as real
  statements.

Use a plain `.replace()` with a marker that appears exactly once, in
expression position only.

## Baseline hygiene on a shared machine

- Snapshot the baseline to a **frozen file** before the first edit
  (`cp harness.py baseline_harness.py`). Other agents edit the same scratch
  files concurrently, so `git HEAD` is not a baseline and neither is the
  live file.
- Run before and after on the **same** browser instance and record the
  observed frame rate for both. A 2.7x measured at 12 fps against an 18 fps
  baseline is not 2.7x.
- **Measure frame rate on a quiet machine.** Under load — many stale tabs,
  a concurrent build — it reads 1 fps instead of 20, and every timing
  conclusion inverts. A dedicated instance is worth launching for a
  measurement you intend to quote.
