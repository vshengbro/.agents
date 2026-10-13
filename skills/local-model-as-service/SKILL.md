---
name: local-model-as-service
description: "Expose a local model to other programs: HTTP service or one-shot CLI."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [mlx, local-model, serving, http, apple-silicon, inference]
---

# Running a local model and exposing it as a service

End-to-end path for a local checkpoint: install → verify real inference → wrap it
so other programs can call it → publish the wrapper. Read the sequence before
starting; each step is the precondition for the next being *provable*.

## When to Use

Load this skill when the task involves a model that runs on the local machine
rather than a hosted API — MLX, llama.cpp, ONNX, or any package with a
`.safetensors` / `.gguf` checkpoint on disk. Triggers:

- setting up, installing, or first-running a local checkpoint
- "run this model locally", "run it on my Mac", "it fails to load"
- a loader rejecting a download that "looks complete"
- wrapping a local model so **another** model, agent, or script can call it
- "so I don't have to keep it running", "without a resident process", or any
  request for a CLI/batch shape instead of a server
- measuring model latency, or choosing between two checkpoints
- publishing that wrapper (fork + PR)

## Procedure

### 1. Verify the environment before installing anything

Check architecture, OS, and the Python that will actually run. A repo's README
states a tested platform; match it before assuming a failure is the code's.

```bash
uname -m && sw_vers && python3 -V
command -v uv || echo "no uv"
```

### 2. Install into a dedicated venv, not the system Python

macOS ships a too-old system Python. Create a pinned venv with `uv`; never
`pip install` into `/usr/bin/python3`.

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python <package>
```

Long installs can exceed a foreground command's approval window. Run them as a
background process with completion notification rather than re-issuing them — a
re-run of a half-finished install is how you get two copies of a package.

### 3. Check the checkpoint layout against what the loader expects

**This is the most common first-run failure.** Loaders validate a specific
directory shape and reject anything else even when every required file is
present. Desktop tools (LM Studio, some downloaders) *flatten* the Hub layout
into one directory, and the loader then fails with a message that reads like a
corrupt download.

Compare the two shapes before blaming the weights:

```bash
ls -1 /path/to/checkpoint/
# loader wants:  encoder/config.json  +  tokenizer/  (subdirectories)
# you may have:   config.json         +  tokenizer.json  (top level)
```

Hash the weights against the checkpoint's own manifest, so "the model is fine,
the layout is wrong" is a proven claim rather than a guess:

```bash
shasum -a 256 model.safetensors
python3 -c "import json;print(json.load(open('manifest.json'))['files']['model.safetensors']['sha256'])"
```

**Repair the layout with symlinks into a scratch tree, never by moving the
user's files.** The download is often shared with another tool that expects the
flat shape; mutating it breaks that tool and is hard to notice.

```bash
mkdir -p work/encoder work/tokenizer
ln -sf "$SRC/config.json"        work/encoder/config.json
ln -sf "$SRC/tokenizer.json"     work/tokenizer/tokenizer.json
ln -sf "$SRC/model.safetensors"  work/model.safetensors
```

Prove the repair by confirming the **original** hash is unchanged afterwards.
When productized, the resolver must be idempotent (build once, reuse) and must
never write into the source directory.

### 4. Prove real inference before building anything on top

Do not accept a successful import as verification. Run an actual prediction and
inspect the output shape.

**Measure latency twice, and report both numbers.** The first call pays kernel
compilation and weight paging; it can be 100–300× slower and is not the
steady-state cost. A single-call measurement is the most common way to misreport
a model as slow.

```python
t0 = time.perf_counter(); result = agent.predict(state, questions)
print(f"cold {(time.perf_counter()-t0)*1000:.0f} ms")

for _ in range(5): agent.predict(state, questions)   # warmup
samples = [timeit_once(agent) for _ in range(50)]
print(f"P50 {statistics.median(samples):.2f} ms")
```

### 5. Choose the smaller checkpoint when the task allows it

If the package ships several checkpoints for different languages or context
lengths, benchmark the input you actually have against **both** rather than
assuming the larger one is better. A common result: the smaller multilingual
model is both faster and *more confident* on non-English input, because the
larger model's vocabulary byte-falls back to gibberish. Compare token counts — a
much higher count on one model is the tell that its tokenizer is struggling.

### 6. Verify one suspicious answer before reporting a bug

When a result looks wrong, construct a second probe that isolates the variable
before declaring a defect. A test state that said "unsubscribe" instead of
"refund" will correctly report low refund-probability; reading that as a model
bug wastes a turn and produces a false bug report upstream.

**Also check whether surprising behavior is inherited from the library's own
heuristic.** Call the library's detector directly and compare. If it agrees with
your wrapper, the behavior is upstream and your report must say so explicitly —
otherwise you will be asked to fix something that is not yours.

### 7. Serve it with the standard library (no new dependency)

If the package is stdlib-only, keep the service stdlib-only — adding FastAPI or
Flask to serve one endpoint widens the install surface for nothing. Load
`references/python-stdlib-http-service.md` for the full recipe.

**A resident server is not the only shape — offer the one-shot CLI too.** If the
caller is a cron job, a shell script, a Makefile, or a `subprocess`, a process
that exits is what they actually want. When a model exposes an HTTP service,
also give it a one-shot entry point: it reuses the layout resolver, the
question validator and the presets, so it is a small addition rather than a
second implementation. See `references/one-shot-cli.md`.

Benchmark both shapes on the same machine before recommending either, and put
the measured numbers in the README: a one-shot call re-reads the weights every
time, and that cost dwarfs inference. State the guidance plainly instead of
leaving the reader to discover the order of magnitude themselves.

Then settle the auth question **once, and let it be the user's call**. Two
failures bracket the right behavior: inventing an auth layer nobody asked for
(wasted work, and a config surface the user must now maintain), and shipping
none without saying so (the next reader cannot tell a decision from an
omission). When the user declines auth, take the default that matches their
threat model — bind the loopback address, add an explicit `--host` flag for the
routable case, and never expose a routable address by default.

**Write the no-auth stance into the README as a decision, not a status.** Say it
is deliberate, state the one consequence that matters (binding `0.0.0.0`
publishes the model to every client that can reach the port), and point at a
reverse proxy for callers who later need per-caller identity. Prose that only
describes the current state reads as an unfinished feature and invites someone
to "fix" it. A docs-only change like this routes as a direct push, not a PR.

### 8. Prove the service end to end, under concurrency

A sequential `curl` cannot surface either of the service's real failure modes
(accept-queue overflow, slot leak). Ship a script that runs the full matrix —
health, each endpoint, routing decisions, error codes, and a concurrent burst
asserting **determinism** — and exits non-zero on the first failure so it can
gate a deploy. Asserting only "no exceptions" misses a racing shared-state bug
that returns correct-looking answers.

### 9. Publish to a fork

Confirm the upstream license permits it, fork, and add `upstream` as a second
remote so the fork can be synced later. Write the new code as a proper subpackage
inside the project's own layout and style, and keep its tests in the project's
test directory so they run in its existing suite and CI.

Mark the addition in the README as fork-specific with the install command that
actually gets it, since the published wheel and upstream will not contain it.

Before committing, reproduce CI's steps locally **with CI's exact environment
variables** (see the `github/github-pr-workflow` skill for why a fork's CI may
never run at all). Code changes go through a PR, per the user's commit standards.

Expect `gh pr create` and `gh pr merge` to fail on a freshly created fork with
`Head sha can't be blank` / `No commits between main and <branch>` /
`Could not resolve to a PullRequest with the number of N`, while `gh api` on the
same resources works. That is GitHub's fork-creation propagation lag in the
GraphQL layer, not a problem with the branch: `gh api repos/<o>/<r>/branches`
lists it and `gh api repos/<o>/<r>/compare/<base>...<head>` returns
`ahead_by: 1`. Skip the CLI for both operations and use REST — the recipe is in
`references/publishing-to-a-fork.md`.

**Do not report a fork's CI as passing when no run exists.** New forks have
Actions disabled by default, so `gh api .../actions/runs` and
`.../check-suites` both return zero for a freshly pushed branch. Reproduce the
CI steps locally and say that is what you did; mention that enabling Actions
in the fork's settings is a manual UI step.

## Pitfalls

- **Reporting a first-call latency as the model's speed.** The first inference
  compiles kernels and pages weights in; it can be three orders of magnitude
  slower than steady state. Always warm up and report both.
- **Assuming a flat checkpoint directory means a corrupt download.** Flat-vs-
  nested is a layout mismatch, not corruption. Hash against the manifest to prove
  which it is.
- **Repairing a shared download directory in place.** The download belongs to
  another tool with its own expectations. Symlink into a scratch tree and leave
  the original byte-identical — then prove it with a hash.
- **Accepting an import as proof the model runs.** Import success and correct
  inference are different claims. Run a prediction.
- **Treating a surprising answer as a model bug without a control probe.** Vary
  one input at a time, and check the library's own detector, before filing.
- **Verifying a service with sequential requests only.** Concurrency bugs
  (accept-queue overflow, slot leaks) are invisible to a serial smoke test.
- **Adding a web framework to serve a stdlib-only package.** It widens the
  dependency surface for one endpoint; the stdlib recipe in the reference
  suffices and its pitfalls are documented there.
- **Shipping only the service when the caller wants a process that exits.**
  A server held open for a cron job or a one-off script is a port, a process
  table entry and a shutdown path the caller did not want. Ship both shapes and
  let the caller pick.
- **Leaving the CLI-vs-service cost unstated.** One-shot calls pay full weight
  load every invocation. Without the measured number a reader assumes they are
  interchangeable and picks the slow one.
- **Returning a traceback and exit 1 from a CLI usage error.** The exit code is
  the interface a shell script depends on; reserve distinct codes for usage
  versus model failure, and catch the specific exception subclass rather than
  its `ValueError` base.
- **Building a layout-repair test fixture from memory of the format.** Read the
  real directory on disk first — a fixture that guesses the shape exercises the
  wrong branch.
- **Adding authentication the user did not ask for, or staying silent about
  its absence.** Both are wrong in opposite directions. The boundary decision
  is the user's; your job is to pick the safe default, ask once, and then record
  the answer as a decision in the README.
- **Reporting a fresh fork's PR as CI-green.** Actions is off on new forks, so
  zero runs looks exactly like a pass. Reproduce the steps locally and say so.
- **Assuming `gh pr create` failing means the branch is missing.** On a fork
  created minutes earlier, GraphQL has not indexed the refs while REST already
  has. Go straight to REST instead of re-pushing.
- **Attributing a squashed commit's wrong author to your own commit.** Squash
  merge stamps the account profile identity over the branch commit's author.
