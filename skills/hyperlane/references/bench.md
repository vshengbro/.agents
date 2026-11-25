# The hyperlane performance harness

Source: `performance/` in the hyperlane workspace. Verified against the tree at
`origin/master` (`a1846f6`, workspace version `22.8.2`).

**Name the binary.** The package publishes four binaries, so `cargo run -p
hyperlane-performance` cannot pick one and fails with an ambiguity error. Every
invocation needs `--bin hyperlane-performance`. The CI workflow
(`.github/workflows/perf.yml`) was fixed for exactly this reason.

## What it is, and what it is not

The harness is **one publishable crate**, `hyperlane-performance`, and it is a
**member of the root workspace** — `cargo metadata --no-deps --format-version 1`
lists it among the twelve packages. It is not a separate workspace: there is no
second `Cargo.lock`, and a root `cargo test --workspace` builds and tests it.

The crate produces **four binaries** from one package:

| binary | what it is |
|---|---|
| `hyperlane-performance` | the orchestrator, certificate generator and report renderer |
| `hyperlane-performance-server` | the server under test, written against the public API only |
| `hyperlane-performance-loadgen` | a closed-loop client that speaks every protocol of the matrix |
| `hyperlane-performance-control` | a minimal server with no framework, one read and one write per request |

**The harness is Rust, not shell.** There is no `run-perf.sh`, no `summarize.py`
and no `scripts/generate-certs.sh`: the orchestrator is the
`hyperlane-performance` binary and the report renderer is Rust too. A reference
that tells you to run `./run-perf.sh` describes a harness that no longer exists.

The control speaks the same protocol as the row it references. A control that
spoke HTTP/1.1 could not say what the machine allowed for HTTP/3, so the
control would be an incomparable number in every row but one. The control has no
dependency on the framework at all, which is what keeps it an independent
reference.

`hyperlane-performance-server` depends on the framework through the **path**
`hyperlane = { workspace = true }`, so it measures the working tree, not a
published release.

## The five sub-commands

The orchestrator drives Docker, not cargo directly. The usage string in
`performance/src/runner/const.rs` is
`usage: hyperlane-performance <instrument|build|bench|report|certificates> ...`.

```sh
cargo run --locked -q -p hyperlane-performance --bin hyperlane-performance -- instrument .
cargo run --locked -q -p hyperlane-performance --bin hyperlane-performance -- build candidate .
cargo run --locked -q -p hyperlane-performance --bin hyperlane-performance -- build baseline /path/to/baseline
cargo run --locked -q -p hyperlane-performance --bin hyperlane-performance -- bench candidate baseline
cargo run --locked -q -p hyperlane-performance --bin hyperlane-performance -- report
cargo run --locked -q -p hyperlane-performance --bin hyperlane-performance -- certificates performance/certs
```

- `instrument <context>` — builds the load generator and control images and
  copies the harness into the build context.
- `build <variant> <context>` — the context holds the library tree and the
  harness. It builds `<prefix>-server:<variant>`, `<prefix>-loadgen:1.0` and
  `<prefix>-control:1.0` from `performance/docker/Dockerfile.perf`.
- `bench <variant-a> <variant-b>` — runs both variants **at the same time**,
  each with its own load generator, over the same wall-clock window, and writes
  the raw rows to `<results>/raw.jsonl`.
- `report [path]` — renders the table and the verdict. Without an argument it
  reads `<results>/raw.jsonl`.
- `certificates <dir>` — generates the certificate material.

The runner creates the Docker network `hyperlane-perf` when it does not exist
(`ensure_network` inspects first, then creates). It removes the containers it
started on exit but **not** the network, so clean that up yourself when the
task ends.

To measure a change against the committed state, build a second context from
the merge-base. The runner copies the harness into that context itself, so the
two images differ only in the library under test:

```sh
mkdir -p /tmp/hyperlane-perf-baseline
git archive "$(git merge-base origin/master HEAD)" | tar -x -C /tmp/hyperlane-perf-baseline
cargo run --locked -q -p hyperlane-performance --bin hyperlane-performance -- build baseline /tmp/hyperlane-perf-baseline
```

The build is `--locked`: the lock is authoritative, and the runner rewrites the
workspace members of each context's lock before the build, because the
baseline's source carries a different version than the candidate's. Only the
workspace members move; every third-party pin stays exactly as it was. A
build that cannot honour the lock must fail rather than resolve again: a
fallback would let the two arms drift apart without anything reporting it.

### Where the harness lives at run time

`config_from_env` resolves the harness root before anything else:

- `PERF_ROOT` names the harness source directory explicitly. Without it, the
  runner uses `<cwd>/performance` when that directory exists, and `<cwd>`
  otherwise. When `PERF_ROOT` points at a directory without
  `docker/Dockerfile.perf`, the runner refuses with `not a performance source
  tree; set PERF_ROOT to the checkout's performance directory`.
- `PERF_RESULTS` defaults to `<root>/results`, and `PERF_CERTS` defaults to
  `<root>/certs`.

### The certificate material

The TLS rows need a chain. The material is **generated**, not committed: a
private key in a repository is a private key in every clone of that
repository.

```sh
cargo run --locked -q -p hyperlane-performance --bin hyperlane-performance -- certificates performance/certs
```

The generator makes a certificate authority and one leaf certificate
(`ca.pem`, `leaf.pem`, `leaf.key`; the names are the constants
`CA_FILE_NAME`, `LEAF_CERT_FILE_NAME` and `LEAF_KEY_FILE_NAME`). The clients
verify the chain against the authority explicitly: the authority is the trust
anchor, and the leaf is the end entity. The `build` sub-command generates the
material itself when a required file is missing.

## The matrix

The measurement is a grid, not a single row. The protocol axis is the wire
protocol the server speaks, and the connection axis is whether a connection
carries many requests or exactly one.

| | `keepalive` | `short` |
|---|---|---|
| `h1` | HTTP/1.1 over a plain socket | one connection per request |
| `h1-tls` | HTTP/1.1 over TLS | one connection per request |
| `h2c` | HTTP/2 with prior knowledge | one connection per request |
| `h2-tls` | HTTP/2 over TLS | one connection per request |
| `h3` | HTTP/3 over QUIC | one connection per request |

The connection axis is not a dial on the same code path. A short connection
exercises the accept loop, the per-connection handshake and the disconnect
cleanup once per request, and it spends one ephemeral port per request as
well, so the generator caps its connection rate: without the cap the kernel
runs out of ports and the run fails with `EADDRNOTAVAIL`, which reads as a
server defect and is not one.

Every protocol is driven by its own client library. `curl` cannot speak
HTTP/2 without TLS, cannot speak HTTP/2 in cleartext, and cannot speak
HTTP/3 at all, so the harness uses `h2`, `h3` and `quinn` directly.

## The knobs

Every knob is an environment variable. The variable names live in
`performance/src/config/const.rs` as `ENV_*` constants.

| variable | default | meaning |
|---|---|---|
| `PERF_PROTOCOLS` | `h1 h1-tls h2c h2-tls h3` | the protocol rows to measure |
| `PERF_MODES` | `keepalive short` | the connection rows to measure |
| `PERF_CONNECTIONS` | `64 256` | the concurrency levels of the keep-alive rows |
| `PERF_CONNECTIONS_SHORT` | `16 64` | the concurrency levels of the short rows |
| `PERF_RATE_SHORT` | `200` | the connection rate cap of the short rows, per second |
| `PERF_COOLDOWN_SHORT` | `20` | the pause between two short rows, in seconds |
| `PERF_DURATION` | `12` | the length of a measured window, in seconds |
| `PERF_WARMUP` | `4` | the length of the warm-up window, in seconds |
| `PERF_REPEATS` | `3` | how many times a level is measured |
| `PERF_SERVER_CPUS` | `4` | the CPU quota of each server container |
| `PERF_LOADGEN_CPUS` | `4` | the CPU quota of each load generator container |
| `PERF_MEMORY` | `4g` | the memory limit of each container |
| `PERF_RESULTS` | `<root>/results` | where the raw rows are written |
| `PERF_NETWORK` | `hyperlane-perf` | the Docker network name |
| `PERF_IMAGE_PREFIX` | `hyperlane-perf` | the image name prefix |
| `PERF_CERTS` | `<root>/certs` | where the certificate material lives |
| `PERF_CA_CERT` | `<certs>/ca.pem` | the certificate authority file |
| `PERF_TLS_CERT` | `<certs>/leaf.pem` | the leaf certificate file |
| `PERF_TLS_KEY` | `<certs>/leaf.key` | the leaf private key file |
| `PERF_ROOT` | `<cwd>/performance` | the harness source directory |

The defaults assume a four-vCPU machine, which is what a GitHub hosted runner
has. The CI workflow overrides the quotas to `1` CPU each and sets its own
levels in the job's `env:` block.

The measurement is only meaningful while the load generator is not the
bottleneck; `docker stats` shows that directly.

## The verdict

The report renderer computes the **median of the per-repeat paired
differences**, not the difference of two medians. Two runs of the same binary
were measured to differ by up to 65 percent, which is larger than any real
difference the comparison is meant to detect, so a sequential comparison was
tried and rejected.

| verdict | meaning |
|---|---|
| `improvement` | the median paired difference is at least +5 % and larger than the spread |
| `regression` | the median paired difference is at most -10 %, larger than the spread, and the control was stable |
| `within noise` | the difference is smaller than the spread, or smaller than the thresholds |
| `inconclusive` | the control moved more than 10 %, so the machine changed underneath the measurement |

The thresholds are the constants `IMPROVEMENT_THRESHOLD = 5.0`,
`REGRESSION_THRESHOLD = -10.0` and `CONTROL_TOLERANCE = 10.0` in
`performance/src/report/const.rs`. The verdict text is formatted as
`median paired difference {median_delta:+.2}%, spread {spread:.1} points`, so a
candidate at +20 % against a flat baseline with a stable control prints
`=> improvement: median paired difference +20.00%, spread 0.0 points`.

The report footer says it outright: `The verdict is a report. It never blocks
a build.` The renderer exits non-zero only when the measurement itself is
broken — `no measurements were found`, `the two variants were not measured
together` or `no repeat produced a usable pair` — because a harness that
fails quietly would report "no regression" for a server that never answered.

## The load generator's output

Each run prints one JSON object with `connections`, `duration_s`, `requests`,
`errors`, `rps`, `p50_us`, `p90_us`, `p99_us`, `p999_us`, `max_us` and
`mean_us`. The `bench` sub-command wraps it into a row of
`{"variant", "protocol", "mode", "connections", "repeat", "result"}` and
appends it to `raw.jsonl`.

The load generator takes `--addr`, `--connections`, `--duration`, `--warmup`,
`--protocol`, `--mode`, `--ca` and `--rate`.

### The order of the arms

The runner alternates which arm goes first across the repeats: in `run_pair`,
the two arms are swapped whenever the repeat index is even. The first arm
starts its server and its load generator first, so it measures a slightly
different machine state than the second; measuring one arm first in every
repeat puts that bias on the same arm in every pair. A path that no change
touched cannot have regressed, so when the untouched rows come out
consistently negative, the bias is in the harness and not in the code.

## In the pipeline

`.github/workflows/perf.yml` runs the harness on **every push** to any branch
(`on: push: branches: ['**']`). It resolves the baseline as `HEAD^`, builds
the baseline context with `git archive`, then:

```sh
cargo run --locked -q -p hyperlane-performance --bin hyperlane-performance -- instrument .
cargo run --locked -q -p hyperlane-performance --bin hyperlane-performance -- build candidate .
cargo run --locked -q -p hyperlane-performance --bin hyperlane-performance -- build baseline "${{ runner.temp }}/baseline"
cargo run --locked -q -p hyperlane-performance --bin hyperlane-performance -- bench candidate baseline
cargo run --locked -q -p hyperlane-performance --bin hyperlane-performance -- report | tee "${{ github.workspace }}/performance/results/report.txt"
```

It uploads `performance/results` as an artifact. The job has a 90 minute
timeout and a concurrency group that cancels an in-flight run of the same ref.

**There is no pull-request trigger and no schedule.** A reference that says the
workflow runs "on pull requests that touch `core/**`, `type/**` or
`performance/**`, on a daily schedule, and on demand" describes an older
workflow: the current one runs on push only, and it has no `workflow_dispatch`
input.

The main `rust.yml` workflow covers the harness with the ordinary workspace
jobs — a format check, a test run and a clippy run over `--workspace`, which
now includes `hyperlane-performance`. Those steps are what keep the harness
compiling; they are not the same as the measurement.

A pull request's numbers are not comparable with a dedicated machine's
numbers. The runner is a shared virtual machine, and the control probe is what
tells the two apart.
