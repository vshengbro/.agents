# Verifier scope bugs: findings that are not Rust

Three classes of `rust-standards` finding that no source edit can fix. Each
needs a fix to the *verifier* in the skill repo, committed with the verifier,
any gate that calls it, and the spec sentence — never a change to the user's
repo to make the check go quiet.

Rule of thumb for classifying a finding: **read the reported line itself.** A
banner, a summary, a traceback, or text whose operators belong to another
language is never a source violation.

| Class | Reported as | Actually | Fixable in source? |
|---|---|---|---|
| wrapper artifact | a FAIL whose detail line is a `===` banner / summary / traceback | the wrapper's `grep -v` filter, written against a stale banner | n/a — fix the wrapper |
| macro fragment | `closure param without type` on `$( $arg:ident )`, `hardcoded string` in a template | `macro_rules!` matcher / body | only the macro's own `const.rs` |
| grammar slot | `hardcoded string` on `extern "C"`, `cfg!(target_os = "…")`, an `assert!` message | a position where the grammar requires a literal | **no** — `const ABI: &str = "system"; extern ABI {}` is `error: expected fn` |
| **second language** | a `let` / `hardcoded string` on a line inside a string literal | shader / query / template source in a `r#"…"#` | **no** — mask the literal's lines |

---

## 1. Wrapper artifact — the check is clean and still FAILs

`audit_rust_standards.py` counts **stdout lines**, and a verifier prints a
summary banner on every run. A `grep -v` written against the old banner stops
matching, the success line leaks, and a check with zero violations reports
`1 hits`.

```
FAIL: 30. no comments in test files (§14.5): 1 hits
  === no-comments-in-test-files: 0 violation(s) in 0 file(s) ===   <- the leak
```

A finding with **no `file:line`** is this class. Two variants:

- *inflates on the failing path* — a delta of exactly 1 is the unstripped
  summary line, not a miscounted violation.
- *fails on the clean path* — worse: it looks like a source violation to chase.

Audit every wrapper at once; the drift is usually in several:

```python
for name, wrapper_filter in wrappers.items():
    out = subprocess.run([verifier, repo], capture_output=True, text=True).stdout
    banner = next((l for l in out.splitlines() if l.startswith("===")), "")
    assert re.match(wrapper_filter, banner), f"stale filter for {verifier}"
```

Anchor filters on the banner's **shape** (`'^=== <rule-name>:'`), never on its
current count. Then **prove the repair both ways**: mutate in a real violation
and confirm the filter still lets it through — a filter widened to swallow the
success line easily becomes one that swallows the findings, turning a noisy
gate into a silent one.

---

## 2. Grammar slot — the literal is part of the item's shape

§1.3c hoists program data to `const.rs`. An ABI name, a `cfg!` predicate, or a
format string is not program data.

```rust
const ABI: &str = "system";
extern ABI { }        // error: expected `fn`, found `ABI`
```

`cfg!(target_os = CONST)` → `error: expected a literal, found expression`.
`assert!(cond, "{}", CONST)` → `error: format argument must be a string
literal`.

The format-string slot recurs hardest, because every assertion with a message
produces one. For a test asserting with interpolated values there is **no**
compliant spelling; the honest deliverable is the message hoisted as far as it
goes — a `const` for the static prefix, interpolation left in place. Report
the residue as a count with the reason; never convert a dynamic message into a
static one that stops naming the offending value, or you trade a verifier
finding for a test that can no longer be diagnosed from its output.

**Anchor the exemption on the construct, and scope it to the span — never the
line.**

- *Anchoring on the literal* (`"system"`) misses `"C"` and `"C-unwind"` and
  teaches the rule as a string allowlist. Match the construct
  (`EXTERN_ABI_LINE`, allowing `pub` / `pub(crate)` / `pub(in path)` /
  `unsafe`).
- *Anchoring on the line* (`if matches(line): continue`) drops **every other
  literal on that line** — a one-line
  `extern "C" fn f() -> &'static str { "/home/u/.ssh/id_ed25519" }` passes
  clean, and `#![rustfmt::skip]` keeps it on one line while still satisfying
  `cargo fmt --check`, so neither gate sees it. Capture the ABI literal as a
  **named group** and exclude only that span.
- The span fix has its own trap: a quote-pairing regex re-entered at the
  exempt literal's **closing** quote pairs with the next quote in the line,
  swallowing the code between into one bogus match. Restart the scan *past*
  the span (`STRING_LITERAL.finditer(line, abi_end)`), not from zero.

Restrict a doc-comment exemption to `^\s*//[/!]`, the forms that cannot be
code — a loose `^\s*//` also exempts plain comments, so
`// TODO: hoist "/home/u/.ssh/id_ed25519"` passes clean.

**Measure the blast radius before shipping.** An exemption is global across
every repo running that verifier; diff the counts on all of them and report
them.

---

## 3. Second language — the source is inside a string literal

Neither macro syntax nor a grammar slot: these are real Rust lines *inside a
string*. A shader, query language, or template is commonly carried in a
`r#"…"#` literal, and its statements are written in that other language's
syntax while looking, to a line scanner, exactly like the host language.

```rust
// example/src/page/game_2d/hook/fn.rs and siblings
let shader = r#"
    struct BallData { pos_radius: vec4<f32>, ... }   // WGSL
    let ball = u_balls.balls[vi / 6u];              // reported as a §5.1 hit
    @fragment fn fs_main(…) -> vec4<f32> { … }
"#;
```

**Tell:** the reported line's operators and types do not belong to the host
language — `vec4<f32>`, `u_balls`, `@vertex`, `@builtin(vertex_index)`, a
bare `uniform` / `precision` keyword. Confirm by locating the enclosing
literal, not by reading more of the surrounding Rust:

```bash
# raw-string spans with their line ranges, per file
python3 - <<'PY'
import re, pathlib, sys
for f in map(pathlib.Path, sys.argv[1:]):
    s = f.read_text()
    for m in re.finditer(r'r#*"(.*?)"#*', s, re.S):
        lo = s[:m.start()].count("\n") + 1
        print(f"{f}:{lo}-{lo + m.group(1).count(chr(10))}")
PY
```

**Fix: mask the lines a string literal occupies.** A per-file line mask over
raw strings (any `r` / `r#`..`r##` hash count) and ordinary strings, tracked
as a line state machine. **Do not mask doc comments** — those are real source
position and belong to the doc-format verifier.

**Prove the mask with four probes.** A single fixture whose file ends inside
the string cannot express a leak, so the after-close probe is the one that
finds the bug:

| Probe | Expected | Catches |
|---|---|---|
| payload line **inside** `r#"…"#` | 0 | the mask does nothing |
| payload line inside a plain `"…"` spanning lines | 0 | raw-only tracking |
| real `let` **after** the literal closes | +1 | state machine running to EOF |
| real `let` **before** the literal opens | +1 | state machine starting too early |

A line-anchored pattern is a trap while building the probe: `^\s*let` does not
match `fn f() { let x = 5; }`, so a one-line fixture reports "the exemption
over-reached" when the truth is that nothing was ever tested. **Write probe
fixtures multi-line**, or you will debug the verifier for a bug that is in the
test.

---

## 4. Block-scoped exemption — the same triad, different anchor

A declarative macro whose literals *are* the payload (`class! { … }`,
`vars! { … }`) is exempted by tracking brace depth and re-arming on every
opener. One failure mode, silent:

```python
# WRONG — exempts to end of file; the block's real tail becomes a blind spot
if path.name == "const.rs" or path.parts[:2] == ("ui", "style"):
    return []
```

The same four probes apply, with the third one decisive — a single-block
fixture ends before the bug can express itself. Write the docstring so the next
session can tell the two apart: a **payload-whole block** exempts on *lines*,
an **in-code token** exempts on a *span*.

---

## Proof obligations before calling any of these fixed

Both fixtures, in the skill repo, with the baseline captured first:

- *compliant* — the exempt construct in every legal shape → 0 violations,
  exit 0. Capture what it reported **before** the patch: a compliant fixture
  that never failed proves nothing.
- *violating* — decoys that must still be caught → N real violations, exit 1.
  Audit the fixture for over-broad exemption: a payload in a function body is
  a genuine hit and belongs in the *violating* fixture. An exemption that
  swallows real violations is worse than the bug.

Then reconcile the aggregate: the audit's hit count must **equal** the
verifier's violation count, not exceed it by one.

Finally, remember the score is binary. A whole-repo check records FAIL for any
`N > 0`, so findings going `3160 → 1437` leaves `SUMMARY` at `40/45` — report
the count *and* the score, and say explicitly that a count that never reaches
zero has not converted a FAIL into a PASS.
