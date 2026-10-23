#!/usr/bin/env python3
"""Self-test for verify_no_redundant_accessor_derive.py (§17.16 + §17.16.1).

Run:  python3 scripts/self_test_no_redundant_accessor_derive.py

Coverage:
  1. compliant fixture -> 0 findings, verifier main() exit 0
  2. violating fixture -> exact per-file finding counts PER RULE (`--rule`
     must isolate them), main() exit 1
  3. tricky fixture (enum trio, raw string, byte string, nested block
     comment, qualified single, cfg_attr, cfg field, partial skip, `skip`
     inside a `type(..)`, macro token blobs, raw identifier) -> 0 findings,
     so neither rule is over-broad
  4. unit assertions on the shapes the fixtures only imply: tuple/empty
     structs, all-get-skipped, adjacent structs with different derives,
     multi-line attrs, generic/compound field types, and that a derive
     list never leaks onto its neighbour
  4a. duplicate accessor attributes of one kind: ONE `skip` anywhere in the
     run suppresses that accessor regardless of order (union), for get,
     get_mut and set alike — each confirmed by a real `cargo check` against
     lombok-macros 10.2.7
  5. audit_one adapter returns findings on the violating file and [] on the
     compliant one (the staged_file_gate entry point is real, not a stub)
  6. gate simulation: scratch git repo, staged violation blocked by
     staged_file_gate.py (only this verifier), fixed form allowed, legacy
     debt at HEAD + unrelated staged change allowed, new violation over
     legacy debt blocked. Every git step's exit code is asserted, so a
     commit that never happened cannot pass the later step for the wrong
     reason.

Exits 0 when every assertion holds, 1 otherwise.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures" / "accessor-derive"
VERIFIER = HERE / "verify_no_redundant_accessor_derive.py"

# rule id -> expected finding count on fixtures/accessor-derive/violating
EXPECTED_VIOLATING = {
    "trio": 4,
    "getter-only": 2,
    "all": 6,
}
EXPECTED_FILES = 1


def load(name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(script: Path, *args: str, env: dict[str, str] | None = None) -> tuple[int, str, str]:
    result = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


def main() -> int:
    verifier = load("verify_no_redundant_accessor_derive")
    failures: list[str] = []

    def expect(findings: list[str], count: int, where: str) -> None:
        if len(findings) != count:
            failures.append(
                f"{where}: {len(findings)} finding(s) (expected {count}): "
                f"{findings[0] if findings else '<none>'}"
            )

    # --- 1. compliant fixture: 0 findings everywhere, exit 0 ----------
    compliant_root = FIXTURES / "compliant"
    for path in sorted(compliant_root.rglob("*.rs")):
        findings = list(verifier.audit_one(path))
        if findings:
            failures.append(
                f"compliant: {path.relative_to(compliant_root)} -> "
                f"{len(findings)} finding(s): {findings[0]}"
            )
    rc, out, err = run(VERIFIER, str(compliant_root))
    if rc != 0:
        failures.append(f"compliant: main() exit {rc} (expected 0): {out} {err}")

    # --- 2. violating fixture: exact counts per rule, exit 1 ----------
    violating_root = FIXTURES / "violating"
    target = violating_root / "src" / "struct.rs"
    if not target.is_file():
        failures.append(f"violating fixture file missing: {target}")
    else:
        # The gate/audit call `audit_one`, which runs BOTH rules. Count them
        # per rule through `check_text` so a regression in one rule cannot
        # hide behind the other's count.
        text = target.read_text()
        for rule, expected in EXPECTED_VIOLATING.items():
            hits = verifier.check_text(text, rule)
            if len(hits) != expected:
                failures.append(
                    f"violating: rule {rule!r} -> {len(hits)} finding(s) "
                    f"(expected {expected}): {hits}"
                )
        # The two rules must partition the total, not overlap.
        both = sum(1 for hit in verifier.check_text(text) if hit[3] == "trio")
        if both != EXPECTED_VIOLATING["trio"]:
            failures.append(f"violating: audit_one trio count {both} != 4")
        expect(list(verifier.audit_one(target)), EXPECTED_VIOLATING["all"], "audit_one")

        # Each rule must be reported under its OWN message and its own §:
        # a swapped routing would still print the right COUNT while telling
        # the author to do the opposite fix.
        findings = list(verifier.audit_one(target))
        getter_only_lines = [line for line in findings if "§17.16.1" in line]
        trio_lines = [line for line in findings if "§17.16)" in line]
        if len(getter_only_lines) != EXPECTED_VIOLATING["getter-only"]:
            failures.append(
                f"audit_one: {len(getter_only_lines)} §17.16.1 line(s) "
                f"(expected {EXPECTED_VIOLATING['getter-only']}): {findings}"
            )
        if len(trio_lines) != EXPECTED_VIOLATING["trio"]:
            failures.append(
                f"audit_one: {len(trio_lines)} §17.16 line(s) "
                f"(expected {EXPECTED_VIOLATING['trio']}): {findings}"
            )
        for line in getter_only_lines:
            if "derives `Data` but" not in line or "#[derive(Getter)]" not in line:
                failures.append(f"getter-only message malformed: {line}")
            # The struct NAME and the REASON must not be swapped. The reason
            # always starts with `all N field(s)`, so a swap is visible even
            # when the struct name happens to read like prose.
            if "derives `Data` but all " not in line:
                failures.append(f"getter-only message args swapped: {line}")
            if "struct all " in line:
                failures.append(f"struct name and reason swapped: {line}")
        for line in trio_lines:
            if "derive list" not in line:
                failures.append(f"trio message malformed: {line}")

    # `--rule` must isolate each rule at the process level too.
    for rule, expected in (("trio", 4), ("getter-only", 2)):
        rc, out, err = run(VERIFIER, "--rule", rule, str(violating_root))
        if rc != 1:
            failures.append(f"violating --rule {rule}: exit {rc} (expected 1): {out}{err}")
        if f"{expected} violations" not in out:
            failures.append(
                f"violating --rule {rule}: summary missing '{expected} violations': {out!r}"
            )
    rc, out, err = run(VERIFIER, str(violating_root))
    if rc != 1:
        failures.append(f"violating: main() exit {rc} (expected 1): {out} {err}")
    if "6 violations" not in out:
        failures.append(f"violating: summary line missing count 6: {out!r}")
    if f"{EXPECTED_FILES} files checked" not in out:
        failures.append(f"violating: file count wrong: {out!r}")
    # An unknown --rule must be rejected, not silently ignored.
    rc, _out, err = run(VERIFIER, "--rule", "nope", str(violating_root))
    if rc != 2 or "unknown rule" not in err:
        failures.append(f"unknown --rule accepted (rc={rc}): {err!r}")

    # --- 3. tricky fixture: exempt shapes stay quiet ------------------
    tricky_root = FIXTURES / "tricky"
    for path in sorted(tricky_root.rglob("*.rs")):
        for rule in verifier.RULES:
            findings = list(verifier.check_file(path, rule))
            if findings:
                failures.append(
                    f"tricky: {path.relative_to(tricky_root)} [{rule}] -> "
                    f"{len(findings)} finding(s): {findings[0]}"
                )
    rc, out, err = run(VERIFIER, str(tricky_root))
    if rc != 0:
        failures.append(f"tricky: main() exit {rc} (expected 0): {out} {err}")

    # --- 4. shape assertions the fixtures only imply ------------------
    cases: list[tuple[str, str, int]] = [
        # (label, source, expected finding count)
        (
            "tuple struct with Data and no named field is exempt",
            "#[derive(Data)]\npub struct T(pub u32);\n",
            0,
        ),
        (
            "empty braced Data struct is exempt",
            "#[derive(Data)]\npub struct E {}\n",
            0,
        ),
        (
            "unit Data struct is exempt",
            "#[derive(Data)]\npub struct U;\n",
            0,
        ),
        (
            "every field skips get as well -> no accessor at all, exempt",
            "#[derive(Data)]\npub struct S {\n    #[get(skip)]\n    #[get_mut(skip)]\n"
            "    #[set(skip)]\n    a: u32,\n}\n",
            0,
        ),
        (
            "one live setter keeps the struct as Data",
            "#[derive(Data)]\npub struct S {\n    #[get(pub(crate))]\n    #[get_mut(skip)]\n"
            "    #[set(skip)]\n    a: u32,\n    #[get(pub(crate))]\n    #[get_mut(skip)]\n"
            "    b: u32,\n}\n",
            0,
        ),
        (
            "adjacent structs: only the getter-only one is reported",
            "#[derive(Data)]\npub struct Keep {\n    #[get(pub(crate))]\n    a: u32,\n}\n"
            "#[derive(Data)]\npub struct Report {\n    #[get(pub(crate))]\n    #[get_mut(skip)]\n"
            "    #[set(skip)]\n    a: u32,\n}\n",
            1,
        ),
        (
            "derive list does not leak from one struct onto the next",
            "#[derive(Data)]\npub struct First {\n    #[get(pub(crate))]\n    #[get_mut(skip)]\n"
            "    #[set(skip)]\n    a: u32,\n}\n#[derive(Clone, Debug)]\n"
            "pub struct Second {\n    #[get(pub(crate))]\n    a: u32,\n}\n",
            1,
        ),
        (
            "a Getter struct is never reported by rule 2",
            "#[derive(Getter)]\npub struct S {\n    #[get(pub(crate))]\n    a: u32,\n}\n",
            0,
        ),
        (
            "multi-line derive list still binds",
            "#[derive(\n    Clone,\n    Debug,\n    Data,\n)]\npub struct S {\n"
            "    #[get(pub(crate))]\n    #[get_mut(skip)]\n    #[set(skip)]\n"
            "    a: u32,\n}\n",
            1,
        ),
        (
            "field attributes may appear in any order",
            "#[derive(Data)]\npub struct S {\n    #[set(skip)]\n    #[get_mut(skip)]\n"
            "    #[get(pub(crate))]\n    a: u32,\n}\n",
            1,
        ),
        (
            "compound generic field types are one field, not many",
            "#[derive(Data)]\npub struct S {\n    #[get(pub(crate))]\n    #[get_mut(skip)]\n"
            "    #[set(skip)]\n    a: HashMap<String, Vec<u32>>,\n"
            "    #[get(pub(crate))]\n    #[get_mut(skip)]\n    #[set(skip)]\n"
            "    b: (u32, u64),\n}\n",
            1,
        ),
        (
            "a field with no skips at all still generates a setter -> exempt",
            "#[derive(Data)]\npub struct S {\n    #[get(pub(crate))]\n    #[get_mut(skip)]\n"
            "    #[set(skip)]\n    a: HashMap<String, Vec<u32>>,\n    b: (u32, u64),\n}\n",
            0,
        ),
        (
            "a bare `skip` beside real args still counts as skip",
            "#[derive(Data)]\npub struct S {\n    #[get(pub(crate), type(copy), skip)]\n"
            "    #[get_mut(skip)]\n    #[set(skip)]\n    a: u32,\n}\n",
            0,
        ),
        (
            "doc comments holding the shape are prose",
            "/// #[derive(Data)]\n/// #[get_mut(skip)]\n/// #[set(skip)]\n"
            "#[derive(Data)]\npub struct S {\n    #[get(pub(crate))]\n    a: u32,\n}\n",
            0,
        ),
        (
            "macro invocation tokens are not an item",
            "const _: () = { let _ = m! { #[derive(Data)] pub struct S {"
            " #[get(pub(crate))] #[get_mut(skip)] #[set(skip)] a: u32, } }; };\n",
            0,
        ),
        (
            "generic struct with a where clause is still scanned",
            "#[derive(Data)]\npub struct S<T: Clone>\nwhere\n    T: Debug,\n{\n"
            "    #[get(pub(crate))]\n    #[get_mut(skip)]\n    #[set(skip)]\n    a: T,\n}\n",
            1,
        ),
        (
            "cfg_attr exemption is load-bearing: removing it reports",
            "#[derive(Data)]\npub struct S {\n    #[get(pub(crate))]\n    #[get_mut(skip)]\n"
            "    #[set(skip)]\n    a: u32,\n    #[get(pub(crate))]\n"
            "    #[cfg_attr(feature = \"x\", get_mut(pub(crate)))]\n    #[get_mut(skip)]\n"
            "    #[set(skip)]\n    b: u32,\n}\n",
            0,
        ),
        (
            "a non-derive attribute in front must not be mined for names",
            "#[marker = Data]\n#[allow(dead_code)]\n#[derive(Clone)]\npub struct S {\n"
            "    #[get(pub(crate))]\n    #[get_mut(skip)]\n    #[set(skip)]\n    a: u32,\n}\n",
            0,
        ),
        (
            "derive binding survives an unrelated attribute in the run",
            "#[cfg_attr(all(), allow(dead_code))]\n#[derive(Data)]\npub struct S {\n"
            "    #[get(pub(crate))]\n    #[get_mut(skip)]\n    #[set(skip)]\n    a: u32,\n}\n",
            1,
        ),
        # --- regressions from the 2026-10-18 review ---------------------
        # All three were real misses against lombok-macros 10.2.7, confirmed
        # with a per-case `cargo check` (one fresh crate each, so no shared
        # build could mask the result).
        (
            # Discriminating for the `->` guard itself. `Box<dyn Fn() -> u32>`
            # measured 15 chars instead of 20 when the arrow was treated as a
            # closer, i.e. the body span ended inside the type. Putting a
            # live-setter field AFTER the arrow makes that truncation
            # change the verdict, so removing the guard flips this to 1.
            "R1 `->` arrow must not close the `<` and truncate the body",
            "#[derive(Data)]\npub struct Mixed {\n    #[get(pub(crate))]\n"
            "    #[get_mut(skip)]\n    #[set(skip)]\n    cb: Box<dyn Fn() -> u32>,\n"
            "    #[get(pub(crate))]\n    #[set(pub(crate))]\n    value: u32,\n}\n",
            0,
        ),
        (
            "R1b bare field after the arrow also generates a setter",
            "#[derive(Data)]\npub struct Mixed {\n    #[get(pub(crate))]\n"
            "    #[get_mut(skip)]\n    #[set(skip)]\n    cb: Box<dyn Fn() -> u32>,\n"
            "    value: u32,\n}\n",
            0,
        ),
        (
            "R1b `->` in a bare fn pointer is the same shape",
            "#[derive(Data)]\npub struct FnPtr {\n    #[get(pub(crate))]\n"
            "    #[get_mut(skip)]\n    #[set(skip)]\n    cb: fn(u32) -> Vec<u32>,\n}\n",
            1,
        ),
        (
            # R2/R2b/R2c are the union-skip cases. A wrong build of this rule
            # treated duplicates as "first non-skipping wins" and expected 0;
            # the macro's FIRST pass (`generate/fn.rs` 866-874) marks
            # `added_flags` from every attribute before the generating pass
            # runs, so one skip kills the kind regardless of order. Each of
            # the three orderings below was re-proven by its own
            # `cargo check` (exit 101, E0599 on the mutator).
            "R2 duplicate get_mut, non-skipping FIRST -> still no mutator",
            "#[derive(Data)]\npub struct Dup {\n    #[get(pub(crate))]\n"
            "    #[get_mut(pub(crate))]\n    #[get_mut(skip)]\n    #[set(skip)]\n"
            "    value: u32,\n}\n",
            1,
        ),
        (
            "R2b duplicate get_mut, skip FIRST -> same verdict, order is moot",
            "#[derive(Data)]\npub struct Dup {\n    #[get(pub(crate))]\n"
            "    #[get_mut(skip)]\n    #[get_mut(pub(crate))]\n    #[set(skip)]\n"
            "    value: u32,\n}\n",
            1,
        ),
        (
            "R2c duplicate set -> no setter",
            "#[derive(Data)]\npub struct Dup {\n    #[get(pub(crate))]\n"
            "    #[get_mut(skip)]\n    #[set(pub(crate))]\n    #[set(skip)]\n"
            "    value: u32,\n}\n",
            1,
        ),
        (
            # The `get` half of the same union, in the direction that makes it
            # a false POSITIVE if the union is broken the other way: one
            # `#[get(skip)]` among duplicates removes the last getter, so
            # nothing is generated at all and the struct is out of scope.
            "R2d duplicate get, one skipping -> no accessor at all, exempt",
            "#[derive(Data)]\npub struct Dup {\n    #[get(pub(crate))]\n"
            "    #[get(skip)]\n    #[get_mut(skip)]\n    #[set(skip)]\n"
            "    value: u32,\n}\n",
            0,
        ),
        (
            "R3 a tuple struct IS checked (Fields::Unnamed generates too)",
            "#[derive(Data)]\npub struct Wrapped(#[get(pub(crate))] "
            "#[get_mut(skip)] #[set(skip)] pub(crate) u32);\n",
            1,
        ),
        (
            "R3b tuple struct with a live setter on the second field",
            "#[derive(Data)]\npub struct Wrapped(#[get(pub(crate))] "
            "#[get_mut(skip)] #[set(skip)] u32, pub u64);\n",
            0,
        ),
        (
            "R4 a field with NO attribute generates every accessor",
            "#[derive(Data)]\npub struct Bare { a: u32, b: u32 }\n",
            0,
        ),
    ]
    for label, source, expected in cases:
        hits = verifier.check_text(source, "getter-only")
        if len(hits) != expected:
            failures.append(
                f"shape [{label}]: {len(hits)} finding(s) (expected {expected}): {hits}"
            )

    # --- 4b. the balanced-delimiter reader itself --------------------
    # R1's `->` guard cannot be observed through the field scan: a struct
    # body span that ends early still yields the same VERDICT, because the
    # truncated tail happens to be getter-only shaped either way. So it is
    # asserted where it acts — on the span `_match_forward` returns. Every
    # case was measured against the real macro's supported syntax.
    spans = [
        ("HashMap<String, Vec<u32>>", 25),
        ("Box<dyn Fn() -> u32>", 20),
        ("Vec<u32>", 8),
        ("Option<Vec<Box<dyn Fn(u32) -> u32>>>", 36),
        ("HashMap<String, HashMap<K, V>>", 30),
        ("std::collections::HashMap<String, Vec<u32>>", 43),
    ]
    for text, expected_len in spans:
        start = text.index("<")
        got = verifier._match_forward(text, start)
        if got != expected_len:
            failures.append(
                f"delimiter [{text}]: _match_forward returned {got} "
                f"(expected {expected_len}): {text[start:got] if got else '<None>'}"
            )
        else:
            span = text[start:got]
            # The span must be the WHOLE generic, balanced and self-closing.
            if not span.endswith(">") or span.count("(") != span.count(")"):
                failures.append(f"delimiter [{text}]: span is not balanced: {span!r}")

    # --- 5. audit_one adapter on both directions ----------------------
    if not verifier.audit_one(violating_root / "src" / "struct.rs"):
        failures.append("audit_one returned [] for a violating struct.rs")
    if verifier.audit_one(compliant_root / "src" / "struct.rs"):
        failures.append("audit_one reported on the compliant struct.rs")
    if verifier.audit_one(tricky_root / "src" / "macro_blob.rs"):
        failures.append("audit_one reported on the tricky macro_blob.rs")

    # --- 6. gate simulation -------------------------------------------
    gate = HERE / "staged_file_gate.py"
    scratch = Path(tempfile.mkdtemp(prefix="accessor-derive-gate-"))
    try:
        repo = scratch / "repo"
        (repo / "src").mkdir(parents=True)
        env = dict(os.environ)
        env["STAGED_FILE_GATE_ONLY_VERIFIERS"] = "verify_no_redundant_accessor_derive"
        env["STAGED_FILE_GATE_JOBS"] = "1"
        env["PYTHONDONTWRITEBYTECODE"] = "1"

        def git(*args: str) -> int:
            """Run one git command in the scratch repo, recording any failure.

            Every call's exit code is checked: a silently failed `commit`
            would leave the "legacy debt at HEAD" step running against a
            HEAD that never moved, and the next gate call would then pass for
            the wrong reason — a false green.
            """
            result = subprocess.run(
                ["git", "-C", str(repo), *args],
                capture_output=True,
                text=True,
                env=env,
            )
            if result.returncode != 0:
                failures.append(
                    f"git {' '.join(args)}: exit {result.returncode} "
                    f"(expected 0): {result.stdout}{result.stderr}"
                )
            return result.returncode

        git("init", "-q")
        git("checkout", "-q", "-b", "master")
        # The global hooks (core.hooksPath = ~/.git-hooks) are deliberately
        # NOT detached, and the global committer identity is deliberately NOT
        # overridden. Neither needs to be: this scratch repo has no
        # Cargo.toml, and both hooks exit 0 at their "not a Rust repo" check
        # before running any gate. (prepare-commit-msg cannot be skipped via
        # --no-verify, so detaching it used to be tempting — but the real
        # red/green behaviour of the gate against hooks that DO run is proved
        # by an ordinary clone with a Cargo.toml, not by muting the hooks.)
        # This harness is a unit simulation of the gate, so it also adds no
        # Cargo.toml: a synthetic manifest would only invite the real hooks to
        # rule on the deliberately-bad baselines this test commits.

        target = repo / "src" / "struct.rs"
        shutil.copy2(compliant_root / "src" / "struct.rs", target)
        git("add", "-A")
        git("commit", "-q", "-m", "baseline")

        # staged violation -> gate must block
        shutil.copy2(violating_root / "src" / "struct.rs", target)
        git("add", "-A")
        rc, out, err = run(gate, str(repo), env=env)
        if rc != 1 or "verify_no_redundant_accessor_derive" not in out:
            failures.append(
                f"gate did not block the staged violation: rc={rc}\n{out}\n{err}"
            )
        # Both rules must be attributed in the gate report, proving the
        # verifier really ran rather than the gate failing for another rule.
        if "§17.16.1" not in out:
            failures.append(f"gate report lacks the §17.16.1 finding:\n{out}")

        # fixed form -> gate must allow
        shutil.copy2(compliant_root / "src" / "struct.rs", target)
        git("add", "-A")
        rc, out, err = run(gate, str(repo), env=env)
        if rc != 0:
            failures.append(f"gate blocked the fixed form: rc={rc}\n{out}\n{err}")

        # legacy violation at HEAD + unrelated staged change -> allowed
        # --allow-empty is required, not decoration: at this point the index
        # holds the SAME compliant content as the baseline commit, so a plain
        # `git commit` dies with "nothing to commit". The empty commit is the
        # checkpoint marking "clean here, debt introduced next", which is what
        # the following step diffs against.
        git("commit", "-q", "--allow-empty", "-m", "clean")
        shutil.copy2(violating_root / "src" / "struct.rs", target)
        git("add", "-A")
        git("commit", "-q", "-m", "introduce debt")
        shutil.copy2(compliant_root / "src" / "struct.rs", repo / "src" / "other.rs")
        git("add", "-A")
        rc, out, err = run(gate, str(repo), env=env)
        if rc != 0:
            failures.append(
                f"gate blocked on legacy debt (should diff vs HEAD): rc={rc}\n{out}\n{err}"
            )
        # a NEW violation on top of the debt -> blocked again
        shutil.copy2(violating_root / "src" / "struct.rs", repo / "src" / "third.rs")
        git("add", "-A")
        rc, out, err = run(gate, str(repo), env=env)
        if rc != 1:
            failures.append(
                f"gate did not catch a NEW violation over legacy debt: "
                f"rc={rc}\n{out}\n{err}"
            )
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    if failures:
        print(f"SELF-TEST FAIL ({len(failures)} assertion(s)):")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("SELF-TEST PASS: verify_no_redundant_accessor_derive + gate wiring")
    return 0


if __name__ == "__main__":
    sys.exit(main())
