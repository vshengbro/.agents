# Running many models — concurrency, slots, and believing the number

Rendering a catalog is a throughput problem before it is a modelling problem.
A 700-model sweep at full quality is ~110 CPU-seconds per model; serially that
is over twenty hours, and no amount of modelling care matters if the batch never
finishes.

## `blrun.py` renders a batch CONCURRENTLY

```bash
python3 scripts/blrun.py catalog/ <render_root> --max-procs 8 --threads 1 \
        --samples 48 --res 800x620
```

One worker per slot, up to `--max-procs` Blender processes at a time. Measured
on this catalog: **6 models in 138 s where the serial total was 665 s — 4.8x.**

Use `--threads 1`. Cycles scales poorly across threads (one model on 8 threads
ran at only 6.65x its CPU time, not 8x), so more single-threaded processes beat
fewer multi-threaded ones. Eight concurrent one-threaded renders also bound the
damage: a crash or a pathological model costs one model, not a whole wave.

## The slot pool guards *across* invocations

Each job takes a slot from `<render_root>/.slots/` before launching and
releases it after. Admission is guarded by an flock plus a liveness check, so N
agents each running `--max-procs 4` still never exceed the cap **in total**.

Slot files are never deleted, because `/tmp` is append-only on some hosts and
`unlink` is denied there. Liveness is tracked by rewriting a slot's contents to
`done`, and a slot whose pid is dead is treated as reusable. A crashed run
leaves no permanent lock.

The slot directory is **per output directory**. Two sweeps writing to different
roots do not see each other's slots — which is also what makes `block_slots.py`
below usable as a targeted brake.

## Believe `peak_concurrency`, not `--max-procs`

The summary reports what the runner actually did:

```json
{"total": 4, "cap": 4, "observed_peak_concurrency": 4,
 "serial_seconds": 110.6, "wall_seconds": 30.2, "speedup": 3.66}
```

```
BLRUN DONE ok=717/717 wall=16594.3s serial=79512.0s speedup=4.79x peak_concurrency=8 (cap=8)
```

This is not decoration. The runner once had a **serial** main loop — acquire,
blocking `subprocess.call`, release — while advertising a cap it never used.
Every catalog sweep had rendered one model at a time, and because the log
printed the requested cap, nothing revealed it. `observed_peak_concurrency` is
computed from the jobs' own start/end intervals, so the runner can no longer
claim a parallelism it did not achieve.

**When a batch feels slow, check `speedup` and `peak_concurrency` first.** A low
speedup with a high cap is a runner bug, not a slow machine.

## When a runaway batch cannot be killed

Some hosts forbid signalling processes: `kill` returns `EPERM` and `ps` /
`pgrep` cannot enumerate, so a stuck sweep cannot be stopped the normal way and
`pkill` silently does nothing. Check for this before assuming a kill worked —
a `pkill` that reports success and leaves the pids running is worse than none.

```bash
python3 scripts/block_slots.py <render_root> <cap>
```

This writes `<cap>` slot files naming pid 1, which is always alive. Admission
counts live slots, so the runners block, hit their `acquire` timeout, raise and
exit on their own. It touches no process and affects only that one render root —
so point the batch you actually want at a **different** root first, then brake
the one you are abandoning.

This is a shutdown path of last resort. The first response to a stuck batch
should still be finding out why it is stuck.

## Where the time actually goes

Measured with `bench.py` on `acoustic_guitar`, full 6-shot set, 8 threads:

| setting | wall | vs base |
|---|---|---|
| samples 48, threshold 0.02, bounces 8/6 | 19.8 s | 1.00x |
| bounces 4/3 | 19.8 s | 1.00x |
| bounces 3/2 | 20.1 s | 1.01x |
| **threshold 0.05** | **15.6 s** | **0.78x** |
| threshold 0.05, samples 24 | 13.6 s | 0.68x |
| threshold 0.10, samples 16 | 13.0 s | 0.66x |

Two things worth keeping from this:

- **Bounces were measured and did nothing.** They are left at 8/6. A knob that
  turns out not to matter should be recorded as not mattering, not "improved"
  on principle.
- **The adaptive threshold is the whole lever.** `samples` is a ceiling, and a
  lit studio surface converges in a fraction of it. The denoiser already
  smooths what is left, so the threshold sits loose at 0.05.

The curve flattens below ~13 s, which is the fixed per-shot cost (BVH build,
kernel launch, PNG write) times six shots. Past that point the only remaining
lever is fewer shots, and the six-shot set is what the vision rubric scores —
so it stays.
