# Classifying a blocking gate finding

A `staged_file_gate.py` rejection is not automatically a source defect. Editing
source until the gate goes quiet is the wrong first move: it is how a real
verifier bug gets papered over with a change that makes the codebase worse.

## Three probes, in order

```bash
# 1. Is the finding even in MY diff, or legacy in HEAD? Legacy does not block.
git show HEAD:<file> | grep -n '<the reported literal or construct>'

# 2. Is this a position the grammar requires a literal in?
grep -nE 'extern "C"|cfg!\(|assert(_eq|_ne)?!|format!|panic!' <file> | head

# 3. Do SIBLINGS of the identical shape go unflagged in the same file?
grep -c '<the same construct shape>' <file>
```

Probe 3 identifies a verifier bug. If three literals of exactly the same shape
in the same file report clean while the fourth is flagged, the rule is
discriminating on something other than the shape you think it is — and the
exemption belongs **in the verifier**, not in your edit.

## Findings with no compliant source spelling

§1.3c hoists program data to `const.rs`. Some positions are not program data;
the literal is part of the construct's shape, so hoisting produces a compile
error, not compliance:

```rust
const ABI: &str = "system";  extern ABI { }   // error: expected `fn`
cfg!(target_os = CONST)                        // error: expected a literal
assert!(cond, "{}", CONST)                     // error: format arg must be a literal
```

The format-string slot recurs hardest because every assertion with a message
produces one. For a test asserting with interpolated values there is **no**
compliant spelling. The deliverable is the message hoisted as far as it goes —
a `const` for the static prefix, interpolation left in the literal — plus a
reported count with the reason.

## Never trade a finding for an undiagnosable test

Collapsing

```rust
"{} at={:?}, want {:?}", CONST, at, want
```

into

```rust
"{}", CONST
```

silences the check **and deletes the offending values from the failure output**.
A test that fails without naming what failed is worse than the verifier
finding that was blocking you. The same applies to shortening a literal to
slip under a minimum-length match. Neither is a fix.

## Converge limit: two attempts, then revert and report

If a fix does not pass the gate **and** `cargo test` / `clippy` on the second
try, it is not a source-shape problem. Restore the file to its exact pre-session
state and prove it:

```bash
git diff HEAD --stat -- <file>    # must match the pre-session count
```

Then report the finding with probes 1-3 attached and let the user choose
between: rewriting the assertion's information content, accepting a
deliberately narrower commit, or fixing the verifier. Do not pick for them —
each option costs something different, and only they know which.

## Where the real fix goes

The exemption is committed in the **skill repo** — the verifier, every gate
that calls it, and the spec sentence, together. Never a change to the user's
repo to make a check go quiet. An exemption is global across every repo running
that verifier, so diff its counts on all of them and report the blast radius
before shipping it.

The full classification table (wrapper artifact / macro fragment / grammar
slot / second language), the proof obligations, and the four-probe fixture
method live in the `rust-audit-fix-workflow` skill under
`references/verifier-scope-bugs.md`.
