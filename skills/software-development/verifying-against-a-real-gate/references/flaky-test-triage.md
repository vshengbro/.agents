# Triaging a test that fails only in parallel

Depth for the "measure the rate, validate both directions" rule in SKILL.md.
The procedure for separating a shared-state race from a hang, from a
missing registration, and from your own edit.

## The isolation ladder

Run these in order. Skipping a rung produces a fix aimed at the wrong cause.

1. **Run the whole suite once.** Confirms the symptom is real, not a
   one-off you saw in a truncated log.
2. **Run the affected module alone** (`<binary> --test-threads=8 <module>::`).
   A module that passes alone and fails in the suite shares state with
   *another* module. A module that fails alone is broken on its own.
3. **Run it single-threaded** (`--test-threads=1`). This **localises** — it
   says the state is shared — and nothing more. It is not a fix, and treating
   it as one is the single most common way this class of bug survives.
4. **Re-run with `--nocapture` and a timeout.** The last test to print is
   the one that hung, and its name is the whole lead.
5. **Print the shared object and its accessors**, then grep every call site.
   The failing test names one test; the racing one names another. Neither
   names the shared state. Only the `static`/`OnceLock` definition does.

## A hang and a race have the same shape and opposite causes

Both are "state shared across tests", so both are fixed by a lock, and
that shared fix is why they get confused. They are distinguishable:

| | Race | Hang |
|---|---|---|
| Runs N times clean, then | stops | stops |
| Single-threaded | passes | **also hangs** |
| Cause | two threads interleave | one thread waits on itself |
| Typical | parallel asserts disagree | recursive acquire, or a guard held across a nested call |

**Single-threaded passing is the only thing that separates them.** If it
hangs single-threaded, adding a second lock is the wrong move — you already
removed the concurrency and it still fails, so the cause is on one thread's
path. Read the call graph of whatever is shared instead of adding locks to
it.

## Your own edit can manufacture the hang

The most common hang is self-inflicted and arrives looking like a
concurrency bug. A scripted rewrite whose pattern is an **inline code
fragment** (`reset(); let x = C::new(..);`) also matches the **function
definitions** that contain that fragment — the fixtures themselves. The
result is a fixture that calls itself: infinite recursion plus a second
acquisition of the lock it just took.

Two properties make it survive casual testing:

- **It is slow, not immediately fatal**, so short sweeps pass. It hung on
  the ~200th run of a sweep that had passed 20 straight.
- **It looks exactly like the bug you were fixing.** You were adding a
  lock, so a hang reads as "the lock is wrong", and you go look at locking.

Defences, in order of cost:

- Match the **whole function**, not a fragment of its body:
  `re.sub(r"fn NAME\(\)[\s\S]*?\n\}\n", new, count=1)`.
- After editing a fixture, **print the rewritten function in full** and read
  it. An `assert count == 1` proves the replace matched, not that what
  landed is correct.
- Count the definitions separately from the call sites
  (`len(re.findall(r"fn NAME", s))` should equal 1).

## Sizing the replacement sweep

A sweep that passed 20 times has not excluded a 5% failure rate to any
useful confidence. Size it from the failure you actually observed.

```python
import subprocess, re, collections, time

BIN = "<compiled test binary>"          # not `cargo test` — it wraps panics
NAMES = collections.Counter()
for threads, n in ((1, 100), (8, 300), (16, 300)):
    passed = failed = 0
    t0 = time.time()
    for _ in range(n):
        try:
            r = subprocess.run([BIN, f"--test-threads={threads}"],
                               capture_output=True, text=True, timeout=30)
            rc = r.returncode
        except subprocess.TimeoutExpired:
            rc = -99                       # a hang is an anomaly, not a pass
        if rc == 0:
            passed += 1
        else:
            failed += 1
            m = re.search(r"^---- (\S+) stdout ----", r.stdout, re.M)
            NAMES[m.group(1) if m else f"rc={rc}"] += 1
    print(f"threads={threads:2d} {n:3d}x pass={passed} fail={failed} "
          f"({time.time()-t0:.1f}s)")
print("anomalies:", dict(NAMES) or "none")
```

Two details carry the weight:

- **A timeout is its own bucket.** Treating an exception as "flaky, retry"
  makes a hang look like a pass forever, because a hung process never
  reports a failure — it just stops. Count `-99` separately and report it.
- **Compile the binary, then loop on the binary.** `cargo test` re-resolves
  and re-locks on every invocation and returns a wrapped status; the binary
  returns the real one (`-11` is SIGSEGV, `101` is panic) and runs fast
  enough to make a large sweep cheap.

Report the shape of the result — `700/700 across 1/8/16/32 threads, 0 fail,
0 timeout` — because that is a claim a reader can check. "Tests pass" is not,
and after changing test serialisation it is exactly the claim that matters.
