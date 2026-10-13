# A falling test count is a measurement question before it is a regression

A slice that only runs `cargo test` on the host target reports fewer tests than
a previous run simply because the wasm-gated ones never executed — the count
moved without a single test being deleted. Establish which it is before
reporting.

## Three commands, in order

```bash
# 1. did the target-gated suite even run?  exit 126 = no wasm runner on host
cargo test --target wasm32-unknown-unknown 2>&1 | tail -3
# 2. are the test files themselves still there?
grep -rc '#\[test\]' --include=*.rs <dir>/tests | grep -v ':0$'
# 3. did THIS session touch them?
git status --porcelain -- <dir>/tests
```

Command 3 is the one that decides it: an empty result proves the files are
byte-identical to `HEAD`, so the lower count is a harness difference and not
lost work.

## How to report it

**"N passed on the host target; M more are wasm-gated and did not run."**
Reporting the bare smaller number invites a review that you deleted tests.

Reporting `cargo test --workspace` as if it passed is worse: on a wasm-only
crate the workspace invocation fails outright with
`can't find crate for euv_core`, and a test run that reports `0 passed` from a
single package is not a suite at all.

## Sum the results yourself

Run the suites per package and **sum the `test result:` lines yourself**:

```bash
cargo test -p <a> -p <b> --offline > /tmp/t1.log 2>&1; echo "exit=$?"
python3 - <<'EOF'
import re, pathlib
t = f = 0
for x in ("/tmp/t1.log",):
    for l in pathlib.Path(x).read_text().split("\n"):
        m = re.match(r"^test result: ok\. (\d+) passed; (\d+) failed", l)
        if m:
            t += int(m.group(1)); f += int(m.group(2))
print(f"passed={t} failed={f}")
EOF
```

Never trust a wrapper's summary, and never assume a workspace-wide `cargo test`
covers every package. Parse the `test result:` lines — a `grep` on a pipeline
reports the exit code of the last command in the pipe, not the one you cared
about.

## The same discipline when the count goes UP

After activating previously-uncompiled tests the total rises. Report the new
total **and** how many tests were newly activated, so the increase reads as
recovered coverage rather than an unexplained change.
