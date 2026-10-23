# The hyperlane performance harness

Source: `bench/` in the hyperlane workspace.

## What it is, and what it is not

`bench/` is a **separate Cargo workspace**, not a member of the root workspace.
`bench/Cargo.toml` declares its own `[workspace]` with three members. The root
`cargo metadata --no-deps` therefore does not list the `bench-*` crates, and
`cargo test --workspace` in the root never builds them. The CI runs them with an
explicit `--manifest-path bench/Cargo.toml`.

All three crates carry `publish = false`, so the release job's `crate publish`
cannot publish them, and `bench/Cargo.lock` is tracked separately from the
root lockfile.

| crate | what it is |
|---|---|
| `bench-server` | the server under test, written against the public API only |
| `bench-loadgen` | a closed-loop keep-alive HTTP/1.1 client |
| `bench-control` | a minimal server with no framework, one read and one write per request |

`bench-server` depends on the framework through the **path** `../../`, so it
measures the working tree, not a published release.

The control server is the reference that makes the other numbers readable. It
answers the same request shapes with no framework in between, so a drop in its
throughput means the machine changed, not the framework.

## The three sub-commands

`bench/run-perf.sh` is the orchestrator. It drives Docker, not cargo directly.

```sh
cd bench
./run-perf.sh build candidate ..              # build the images of one variant
./run-perf.sh bench candidate baseline        # measure both variants at once
./run-perf.sh report                          # turn the rows into a verdict
```

- `build <variant> <context>` — the context holds two trees: `hyperlane/` (the
  library under test) and `bench/` (the harness). It builds three images:
  `<prefix>-server:<variant>`, `<prefix>-loadgen:1.0` and `<prefix>-control:1.0`.
- `bench <variant-a> <variant-b>` — runs both variants **at the same time**,
  each with its own load generator, over the same wall-clock window, and writes
  the raw rows to `<results>/raw.jsonl`.
- `report` — runs `bench/summarize.py` over `raw.jsonl` and prints the table
  and the verdict.

The script creates the Docker network `hyperlane-perf` and removes the
containers it started on exit through a trap. It never removes the network, so
clean that up yourself when the task ends.

To measure a change against the committed state, build a second context from
the merge-base and copy the harness into it:

```sh
mkdir -p /tmp/hyperlane-perf-baseline
git archive "$(git merge-base origin/master HEAD)" | tar -x -C /tmp/hyperlane-perf-baseline
cp -R bench /tmp/hyperlane-perf-baseline/
./run-perf.sh build baseline /tmp/hyperlane-perf-baseline
```

## The knobs

Every knob is an environment variable.

| variable | default | meaning |
|---|---|---|
| `PERF_CONNECTIONS` | `64 256` | the concurrency levels to measure |
| `PERF_DURATION` | `12` | the length of a measured window, in seconds |
| `PERF_WARMUP` | `4` | the length of the warm-up window, in seconds |
| `PERF_REPEATS` | `3` | how many times a level is measured |
| `PERF_SERVER_CPUS` | `4` | the CPU quota of each server container |
| `PERF_LOADGEN_CPUS` | `4` | the CPU quota of each load generator container |
| `PERF_MEMORY` | `4g` | the memory limit of each container |
| `PERF_RESULTS` | `bench/results` | where the raw rows are written |
| `PERF_NETWORK` | `hyperlane-perf` | the Docker network name |
| `PERF_IMAGE_PREFIX` | `hyperlane-perf` | the image name prefix |

The defaults assume a four-vCPU machine, which is what a GitHub hosted runner
has. The CI workflow overrides the quotas to `1` CPU each and drives the same
levels through the `workflow_dispatch` inputs.

The measurement is only meaningful while the load generator is not the
bottleneck; `docker stats` shows that directly.

## The verdict

`bench/summarize.py` computes the **median of the per-repeat paired
differences**, not the difference of two medians. The reasoning is in the
script: two runs of the same binary were measured to differ by up to 65
percent, which is larger than any real difference the comparison is meant to
detect, so a sequential comparison was tried and rejected.

| verdict | meaning |
|---|---|
| `improvement` | the median paired difference is at least +5 % and larger than the spread |
| `regression` | the median paired difference is at most -10 %, larger than the spread, and the control was stable |
| `within noise` | the difference is smaller than the spread, or smaller than the thresholds |
| `inconclusive` | the control moved more than 10 %, so the machine changed underneath the measurement |

The thresholds are the constants `IMPROVEMENT_THRESHOLD = 5.0`,
`REGRESSION_THRESHOLD = -10.0` and `CONTROL_TOLERANCE = 10.0` at the top of
the script. A verified example: a candidate at +20 % against a flat baseline
with a stable control prints
`=> improvement: median paired difference +20.00%, spread 0.0 points`.

**The verdict never blocks a build.** `summarize.py` exits non-zero only when
the measurement itself is broken — no rows, or an unusable file — because a
harness that fails quietly would report "no regression" for a server that never
answered.

## The load generator's output

Each run prints one JSON object with `connections`, `duration_s`, `requests`,
`errors`, `rps`, `p50_us`, `p90_us`, `p99_us`, `p999_us`, `max_us` and
`mean_us`. The `bench` sub-command wraps it into a row of
`{"variant", "connections", "repeat", "result"}` and appends it to `raw.jsonl`.

The load generator takes `--addr`, `--connections`, `--duration` and
`--warmup`. Its defaults are 64 connections, a 10 second window and a 3 second
warm-up.

## In the pipeline

`.github/workflows/perf.yml` runs the harness on pull requests that touch
`core/**`, `type/**` or `bench/**`, on a daily schedule, and on demand. It
builds the candidate from the pull request and the baseline from the
merge-base of `master`, measures both, and prints the table and the verdict
into the job log. It uploads `bench/results` as an artifact.

The main `rust.yml` workflow also covers the harness separately: a format
check on `bench/Cargo.toml` (which is allowed to fail), a test run over the
bench workspace, and a clippy run over it. Those steps are what keep the
harness compiling; they are not the same as the measurement.

A pull request's numbers are not comparable with a dedicated machine's
numbers. The runner is a shared virtual machine, and the control probe is what
tells the two apart.
