---
name: verify-before-optimizing
description: Use before changing code to make it faster.
---

# Measure, then optimise, then re-measure the same thing

## Freeze the baseline before the first edit

```sh
cp target.py baseline_target.py
```

Do not rely on `git HEAD` or the live file: concurrent agents edit the same
scratch files, so "the original" is whatever was on disk when you started.
Keep the snapshot, and load the *live* file for the after-run so both
measurements use each version's real code path.

## Compare equal conditions or not at all

Record an environment variable both runs hold fixed:

- observed frame rate (the dominant one)
- machine load, other browser instances, concurrent builds

A "2.7x win" measured at 12 fps against an 18 fps baseline is not 2.7x.
Say which pair you are quoting and why it is the fair one.

## State honestly when the target is missed

If the goal was under 30 s and the result is 38.7 s, report 38.7 s and
"not met". Do not round, and do not swap in a run that happened to meet it.

## A fast FAIL is still a FAIL

Speed does not fix correctness. Report the outcome separately from the
timing, and if a change made a previously-passing check fail, say so before
optimising anything else.

## Prefer the change that makes the thing work

If the correct predicate both speeds the run up **and** makes it pass, that
is the real deliverable. Say both: "33x faster, and it now reaches the upper
slab" — not just the number.
