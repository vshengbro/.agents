#!/usr/bin/env python3
"""Self-test for verify_no_toml_mod_comments.py + fix_no_toml_mod_comments.py.

Run:  python3 scripts/self_test_no_toml_mod_comments.py

Coverage:
  1. compliant fixture -> every file 0 findings, verifier main() exit 0
  2. violating fixture -> exact per-file finding counts, main() exit 1
  3. string-masking unit checks (TOML strings, Rust strings / raw strings /
     char literals / lifetimes / nested block comments)
  4. fixer: dry-run writes nothing, --write converges to 0 findings and is
     idempotent, compliant fixture is untouched by --write
  5. gate simulation: scratch git repo, staged violation blocked by
     staged_file_gate.py (only this verifier), fixed file allowed

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
FIXTURES = HERE / "fixtures" / "toml-mod-comments"

EXPECTED_VIOLATING = {
    "Cargo.toml": 2,
    "src/mod.rs": 2,
    "src/doc/mod.rs": 2,
    "src/block/mod.rs": 1,
    "tests/mod.rs": 1,
}


def load(name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(
    script: Path, *args: str, env: dict[str, str] | None = None
) -> tuple[int, str, str]:
    result = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


def main() -> int:
    verifier = load("verify_no_toml_mod_comments")
    failures: list[str] = []

    # --- 1. compliant fixture: 0 findings everywhere, exit 0 ----------
    compliant_root = FIXTURES / "compliant"
    for path in sorted(compliant_root.rglob("*")):
        if not path.is_file():
            continue
        findings = list(verifier.audit_one(path))
        if findings:
            failures.append(
                f"compliant: {path.relative_to(compliant_root)} -> "
                f"{len(findings)} finding(s): {findings[0]}"
            )
    rc, out, err = run(HERE / "verify_no_toml_mod_comments.py", str(compliant_root))
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
    rc, out, err = run(HERE / "verify_no_toml_mod_comments.py", str(violating_root))
    if rc != 1:
        failures.append(f"violating: main() exit {rc} (expected 1)")
    if f"{total} violation(s)" not in out:
        failures.append(f"violating: summary line missing count {total}: {out!r}")

    # --- 3. string-masking unit checks --------------------------------
    unit_cases = [
        # (finder, text, expected_span_count, label)
        (verifier.find_toml_comments, 'a = "# not a comment"\n', 0, "toml basic string"),
        (verifier.find_toml_comments, "a = '# not a comment'\n", 0, "toml literal string"),
        (verifier.find_toml_comments, 'a = """\n# data\n"""\n', 0, "toml ml basic"),
        (verifier.find_toml_comments, "a = '''\n# data\n'''\n", 0, "toml ml literal"),
        (verifier.find_toml_comments, 'a = "x" # real\n', 1, "toml trailing"),
        (verifier.find_toml_comments, 'a = "unclosed\n# comment\n', 1, "toml unclosed string then comment"),
        (verifier.find_toml_comments, 'a = "\\" #" # real\n', 1, "toml escaped quote"),
        (verifier.find_rust_comments, 'let s = "http://x";', 0, "rust string with //"),
        (verifier.find_rust_comments, "let s = r#\"//\"#;", 0, "rust raw string"),
        (verifier.find_rust_comments, "let c = '/'; // c", 1, "rust char literal then comment"),
        (verifier.find_rust_comments, "fn f<'a>(x: &'a str) {} // c", 1, "rust lifetime then comment"),
        (verifier.find_rust_comments, "let c = '\\''; // c", 1, "rust escaped char literal"),
        (verifier.find_rust_comments, "/* a /* b */ c */ mod x;", 1, "rust nested block"),
        (verifier.find_rust_comments, "/// doc\n//! inner\n// plain", 3, "rust all comment forms"),
    ]
    for finder, text, expected, label in unit_cases:
        spans = finder(text)
        if len(spans) != expected:
            failures.append(
                f"unit[{label}]: {len(spans)} span(s) (expected {expected}) "
                f"in {text!r}"
            )

    # --- 4. fixer: dry-run no-write, --write converges + idempotent ---
    fixer = HERE / "fix_no_toml_mod_comments.py"
    scratch = Path(tempfile.mkdtemp(prefix="toml-mod-comments-fix-"))
    try:
        work = scratch / "violating"
        shutil.copytree(violating_root, work)
        before = {p: p.read_bytes() for p in work.rglob("*") if p.is_file()}
        rc, out, err = run(fixer, str(work))
        if rc != 0:
            failures.append(f"fixer dry-run exit {rc} (expected 0): {err}")
        after = {p: p.read_bytes() for p in work.rglob("*") if p.is_file()}
        if before != after:
            failures.append("fixer dry-run MODIFIED files on disk")
        if "dry-run" not in out:
            failures.append(f"fixer dry-run output missing hint: {out!r}")

        rc, out, err = run(fixer, "--write", str(work))
        if rc != 0:
            failures.append(f"fixer --write exit {rc} (expected 0): {err}")
        remaining = 0
        for path in work.rglob("*"):
            if path.is_file():
                remaining += len(list(verifier.audit_one(path)))
        if remaining != 0:
            failures.append(f"fixer --write left {remaining} finding(s)")

        rc, out, err = run(fixer, "--write", str(work))
        if rc != 0 or "Nothing to do" not in out:
            failures.append(f"fixer second --write not idempotent: rc={rc} {out!r}")

        # --files scoping: only the named file is rewritten
        work2 = scratch / "scoped"
        shutil.copytree(violating_root, work2)
        target = work2 / "Cargo.toml"
        rc, out, err = run(fixer, "--write", str(work2), "--files", str(target))
        if rc != 0:
            failures.append(f"fixer --files exit {rc}: {err}")
        if list(verifier.audit_one(target)):
            failures.append("fixer --files: named file still has findings")
        if list(verifier.audit_one(work2 / "src" / "mod.rs")) == []:
            failures.append("fixer --files: un-named file was rewritten")

        # compliant fixture untouched by --write
        work3 = scratch / "compliant"
        shutil.copytree(compliant_root, work3)
        before3 = {p: p.read_bytes() for p in work3.rglob("*") if p.is_file()}
        rc, out, err = run(fixer, "--write", str(work3))
        after3 = {p: p.read_bytes() for p in work3.rglob("*") if p.is_file()}
        if rc != 0 or before3 != after3:
            failures.append("fixer --write modified the compliant fixture")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    # --- 5. gate simulation -------------------------------------------
    gate = HERE / "staged_file_gate.py"
    scratch = Path(tempfile.mkdtemp(prefix="toml-mod-comments-gate-"))
    try:
        repo = scratch / "repo"
        repo.mkdir()
        env = dict(os.environ)
        env["STAGED_FILE_GATE_ONLY_VERIFIERS"] = "verify_no_toml_mod_comments"
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
        # Hermetic fixture: detach from the GLOBAL hooks (core.hooksPath is
        # set user-wide to ~/.git-hooks, and prepare-commit-msg cannot be
        # skipped even with --no-verify — that is the §3.6 no-bypass design
        # this very gate lives under). The harness commits known-bad states
        # as HEAD baselines, which the real hooks would (correctly) block.
        no_hooks = scratch / "no-hooks"
        no_hooks.mkdir()
        git("config", "core.hooksPath", str(no_hooks))
        shutil.copytree(compliant_root / "src", repo / "src")
        shutil.copy2(compliant_root / "Cargo.toml", repo / "Cargo.toml")
        git("add", "-A")
        git("commit", "-q", "-m", "baseline", "--no-verify")

        # stage a violating Cargo.toml + mod.rs -> gate must block
        shutil.copy2(violating_root / "Cargo.toml", repo / "Cargo.toml")
        shutil.copy2(violating_root / "src" / "mod.rs", repo / "src" / "mod.rs")
        git("add", "-A")
        rc, out, err = run(gate, str(repo), env=env)
        if rc != 1 or "verify_no_toml_mod_comments" not in out:
            failures.append(
                f"gate did not block staged violation: rc={rc}\n{out}\n{err}"
            )

        # fix + restage -> gate must allow
        shutil.copy2(compliant_root / "Cargo.toml", repo / "Cargo.toml")
        shutil.copy2(compliant_root / "src" / "mod.rs", repo / "src" / "mod.rs")
        git("add", "-A")
        rc, out, err = run(gate, str(repo), env=env)
        if rc != 0:
            failures.append(f"gate blocked the fixed tree: rc={rc}\n{out}\n{err}")

        # legacy debt at HEAD + unrelated staged change -> allowed
        # (the gate diffs against HEAD, so pre-existing debt must not block)
        git("commit", "-q", "-m", "clean", "--no-verify")
        shutil.copy2(violating_root / "Cargo.toml", repo / "Cargo.toml")
        git("add", "Cargo.toml")
        git("commit", "-q", "-m", "introduce debt", "--no-verify")
        (repo / "src" / "inner" / "mod.rs").write_text("mod r#struct;\n")
        git("add", "-A")
        rc, out, err = run(gate, str(repo), env=env)
        if rc != 0:
            failures.append(
                f"gate blocked on legacy TOML debt (should diff vs HEAD): "
                f"rc={rc}\n{out}\n{err}"
            )
        # a NEW comment staged on top of the debt -> blocked (+1)
        with open(repo / "Cargo.toml", "a") as handle:
            handle.write("# one more\n")
        git("add", "Cargo.toml")
        rc, out, err = run(gate, str(repo), env=env)
        if rc != 1:
            failures.append(
                f"gate did not catch a NEW comment over legacy debt: "
                f"rc={rc}\n{out}\n{err}"
            )
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    if failures:
        print(f"SELF-TEST FAIL ({len(failures)} assertion(s)):")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("SELF-TEST PASS: verify_no_toml_mod_comments + fix + gate wiring")
    return 0


if __name__ == "__main__":
    sys.exit(main())
