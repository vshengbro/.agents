#!/usr/bin/env python3
"""Self-test for verify_no_redundant_accessor_derive.py (§17.16).

Run:  python3 scripts/self_test_no_redundant_accessor_derive.py

Coverage:
  1. compliant fixture -> 0 findings, verifier main() exit 0
  2. violating fixture -> exact per-file finding counts, main() exit 1
  3. tricky fixture (enum trio, raw string, block comment, qualified single)
     -> 0 findings, so the rule is not over-broad
  4. audit_one adapter returns findings on the violating file and [] on the
     compliant one (the staged_file_gate entry point is real, not a stub)
  5. gate simulation: scratch git repo, staged trio blocked by
     staged_file_gate.py (only this verifier), `Data` form allowed, legacy
     debt at HEAD + unrelated staged change allowed, new trio over legacy
     debt blocked

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

EXPECTED_VIOLATING = {"src/struct.rs": 4}


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

    # --- 1. compliant fixture: 0 findings everywhere, exit 0 ----------
    compliant_root = FIXTURES / "compliant"
    for path in sorted(compliant_root.rglob("*.rs")):
        findings = list(verifier.audit_one(path))
        if findings:
            failures.append(
                f"compliant: {path.relative_to(compliant_root)} -> "
                f"{len(findings)} finding(s): {findings[0]}"
            )
    rc, out, err = run(HERE / "verify_no_redundant_accessor_derive.py", str(compliant_root))
    if rc != 0:
        failures.append(f"compliant: main() exit {rc} (expected 0): {out} {err}")

    # --- 2. violating fixture: exact counts, exit 1 -------------------
    violating_root = FIXTURES / "violating"
    total = 0
    for rel, expected in EXPECTED_VIOLATING.items():
        candidate = violating_root / rel
        if not candidate.is_file():
            failures.append(f"violating fixture file missing: {candidate}")
            continue
        findings = list(verifier.audit_one(candidate))
        total += len(findings)
        if len(findings) != expected:
            failures.append(
                f"violating: {rel} -> {len(findings)} finding(s) "
                f"(expected {expected}): {findings}"
            )
    rc, out, err = run(HERE / "verify_no_redundant_accessor_derive.py", str(violating_root))
    if rc != 1:
        failures.append(f"violating: main() exit {rc} (expected 1): {out} {err}")
    if f"{total} violation" not in out:
        failures.append(f"violating: summary line missing count {total}: {out!r}")

    # --- 3. tricky fixture: exempt shapes stay quiet -------------------
    tricky_root = FIXTURES / "tricky"
    for path in sorted(tricky_root.rglob("*.rs")):
        findings = list(verifier.audit_one(path))
        if findings:
            failures.append(
                f"tricky: {path.relative_to(tricky_root)} -> "
                f"{len(findings)} finding(s): {findings[0]}"
            )
    rc, out, err = run(HERE / "verify_no_redundant_accessor_derive.py", str(tricky_root))
    if rc != 0:
        failures.append(f"tricky: main() exit {rc} (expected 0): {out} {err}")

    # --- 4. audit_one adapter on both directions -----------------------
    if not verifier.audit_one(violating_root / "src" / "struct.rs"):
        failures.append("audit_one returned [] for a violating struct.rs")
    if verifier.audit_one(compliant_root / "src" / "struct.rs"):
        failures.append("audit_one reported on the compliant struct.rs")

    # --- 5. gate simulation -------------------------------------------
    gate = HERE / "staged_file_gate.py"
    scratch = Path(tempfile.mkdtemp(prefix="accessor-derive-gate-"))
    try:
        repo = scratch / "repo"
        (repo / "src").mkdir(parents=True)
        env = dict(os.environ)
        env["STAGED_FILE_GATE_ONLY_VERIFIERS"] = "verify_no_redundant_accessor_derive"
        env["STAGED_FILE_GATE_JOBS"] = "1"

        def git(*args: str) -> int:
            result = subprocess.run(
                ["git", "-C", str(repo), *args],
                capture_output=True,
                text=True,
                env={
                    **env,
                    "GIT_AUTHOR_NAME": "t",
                    "GIT_AUTHOR_EMAIL": "t@t",
                    "GIT_COMMITTER_NAME": "t",
                    "GIT_COMMITTER_EMAIL": "t@t",
                },
            )
            return result.returncode

        git("init", "-q")
        git("checkout", "-q", "-b", "master")
        # Detach from the global hooks: core.hooksPath points at
        # ~/.git-hooks and prepare-commit-msg cannot be skipped, while this
        # harness has to commit known-bad baselines on purpose.
        no_hooks = scratch / "no-hooks"
        no_hooks.mkdir()
        git("config", "core.hooksPath", str(no_hooks))

        target = repo / "src" / "struct.rs"
        shutil.copy2(compliant_root / "src" / "struct.rs", target)
        git("add", "-A")
        git("commit", "-q", "-m", "baseline", "--no-verify")

        # staged trio -> gate must block
        shutil.copy2(violating_root / "src" / "struct.rs", target)
        git("add", "-A")
        rc, out, err = run(gate, str(repo), env=env)
        if rc != 1 or "verify_no_redundant_accessor_derive" not in out:
            failures.append(
                f"gate did not block the staged trio: rc={rc}\n{out}\n{err}"
            )

        # `Data` form -> gate must allow
        shutil.copy2(compliant_root / "src" / "struct.rs", target)
        git("add", "-A")
        rc, out, err = run(gate, str(repo), env=env)
        if rc != 0:
            failures.append(f"gate blocked the Data form: rc={rc}\n{out}\n{err}")

        # legacy trio at HEAD + unrelated staged change -> allowed
        git("commit", "-q", "-m", "clean", "--no-verify")
        shutil.copy2(violating_root / "src" / "struct.rs", target)
        git("add", "-A")
        git("commit", "-q", "-m", "introduce debt", "--no-verify")
        shutil.copy2(compliant_root / "src" / "struct.rs", repo / "src" / "other.rs")
        git("add", "-A")
        rc, out, err = run(gate, str(repo), env=env)
        if rc != 0:
            failures.append(
                f"gate blocked on legacy trio debt (should diff vs HEAD): "
                f"rc={rc}\n{out}\n{err}"
            )
        # a NEW trio on top of the debt -> blocked again
        shutil.copy2(violating_root / "src" / "struct.rs", repo / "src" / "third.rs")
        git("add", "-A")
        rc, out, err = run(gate, str(repo), env=env)
        if rc != 1:
            failures.append(
                f"gate did not catch a NEW trio over legacy debt: "
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
