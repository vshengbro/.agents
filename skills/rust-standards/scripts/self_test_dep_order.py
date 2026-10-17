#!/usr/bin/env python3
"""Self-test for verify_dep_order.py + fix_dep_order.py.

Run:  python3 scripts/self_test_dep_order.py

Coverage:
  1. `[patch.*]` blocks are ordered too (§13.7 patch-override order).
     A patch table redirects upstream crates, so it has no local/third-party
     split and no blank-line group boundary — but it is still sorted, with the
     same (length, key) key every other dependency block uses. Before this the
     verifier skipped `[patch.crates-io]` entirely, so an unsorted patch table
     passed unnoticed (and the hook reported nothing for it).
  2. fixer converges a violating fixture to 0 findings, preserves every
     dependency's value, keeps the TOML parseable, and is idempotent.
  3. The existing dependency-block rules still hold (local/third split and the
     single boundary blank line).

Exits 0 when every assertion holds, 1 otherwise.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERIFY = HERE / "verify_dep_order.py"
FIX = HERE / "fix_dep_order.py"


def write_manifest(path: Path, patch_block: str, deps: str = 'serde = "1.0"\n') -> None:
    path.write_text(
        "[package]\n"
        'name = "demo"\n'
        'version = "0.1.0"\n'
        'edition = "2024"\n'
        "\n"
        "[dependencies]\n"
        + deps
        + "\n"
        "[patch.crates-io]\n"
        + patch_block
        + "\n"
        "[profile.release]\n"
        "opt-level = 3\n",
        encoding="utf-8",
    )


def make_repo(root: Path, patch_block: str, deps: str | None = None) -> Path:
    # A single (non-workspace) crate: `cargo metadata` refuses a manifest with
    # no target, so the crate needs one source file to act as the TOML validator.
    (root / "src").mkdir(parents=True)
    (root / "src" / "lib.rs").write_text("", encoding="utf-8")
    manifest = root / "Cargo.toml"
    write_manifest(manifest, patch_block, deps if deps is not None else 'serde = "1.0"\n')
    return manifest


def run(script: Path, root: Path, *extra: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(script), str(root), *extra],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


def main() -> int:
    # --- 1. verifier: patch block order is enforced --------------------------
    sorted_patch = 'a = { path = "sub" }\nmmmm = { git = "https://x.invalid/b" }\nzzzzz = { git = "https://x.invalid/a" }\n'
    cases = [
        ("sorted patch block passes", sorted_patch, 0),
        ("reversed patch block fails", "zzzzz = { git = \"https://x.invalid/a\" }\na = { path = \"src\" }\nmmmm = { git = \"https://x.invalid/b\" }\n", 1),
        ("long key before short key fails", 'bbbbbbbb = { git = "https://x.invalid/c" }\na = { path = "sub" }\n', 1),
        ("same length, reverse alpha fails", 'bbb = { git = "https://x.invalid/c" }\naaa = { path = "sub" }\n', 1),
    ]
    for label, block, expect_fail in cases:
        root = Path(tempfile.mkdtemp(prefix="dep-order-patch-"))
        try:
            make_repo(root, block)
            code, out = run(VERIFY, root)
            if expect_fail and code == 0:
                raise AssertionError(f"{label}: expected exit 1, got 0\n{out}")
            if not expect_fail and code != 0:
                raise AssertionError(f"{label}: expected exit 0, got {code}\n{out}")
            if expect_fail and "patch.crates-io" not in out:
                raise AssertionError(f"{label}: violation not attributed to the patch block\n{out}")
        finally:
            shutil.rmtree(root, ignore_errors=True)

    # --- 2. fixer: converges, preserves values, idempotent -------------------
    root = Path(tempfile.mkdtemp(prefix="dep-order-fix-"))
    try:
        manifest = make_repo(
            root,
            'zzzzz = { git = "https://x.invalid/a" }\n'
            'a = { path = "sub" }\n'
            'mmmm = { git = "https://x.invalid/b" }\n',
            deps='serde = "1.0"\nzzz = "1.0"\n',
        )
        before = manifest.read_text()
        code, out = run(FIX, root)
        if "patch.crates-io" not in out:
            raise AssertionError(f"fixer did not report the patch block\n{out}")
        code, out = run(FIX, root, "--write")
        if code != 0:
            raise AssertionError(f"fixer --write failed: {code}\n{out}")
        after = manifest.read_text()
        if after == before:
            raise AssertionError("fixer --write changed nothing")
        # cargo is the authority on whether the manifest is still valid TOML,
        # and it needs no third-party parser (python < 3.11 has no tomllib).
        proc = subprocess.run(
            ["cargo", "metadata", "--no-deps", "--format-version", "1"],
            capture_output=True, text=True, cwd=root,
        )
        if proc.returncode != 0:
            raise AssertionError(f"fixer produced an invalid manifest:\n{proc.stderr}")
        import json
        meta = json.loads(proc.stdout)
        patch = meta["packages"][0]["manifest_path"]
        if not patch:
            raise AssertionError("cargo could not read the manifest")
        for value in ('path = "sub"', 'https://x.invalid/a', 'https://x.invalid/b'):
            if value not in after:
                raise AssertionError(f"fixer dropped a dependency value: {value}")
        if "opt-level = 3" not in after:
            raise AssertionError("fixer damaged a following section")
        code, out = run(VERIFY, root)
        if code != 0:
            raise AssertionError(f"verifier still fails after fix:\n{out}")
        code, out = run(FIX, root, "--write")
        if manifest.read_text() != after:
            raise AssertionError("fixer is not idempotent")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # --- 3. pre-existing dependency-block rules still hold -------------------
    root = Path(tempfile.mkdtemp(prefix="dep-order-deps-"))
    try:
        # Same length, reverse alpha: only the secondary sort key can reject
        # this, so it proves the length-then-key rule is still applied.
        manifest = make_repo(root, sorted_patch, deps='bbb = "1.0"\naaa = "1.0"\n')
        code, out = run(VERIFY, root)
        if code == 0:
            raise AssertionError("dep-block order regressed (expected failure)")
        if "patch.crates-io" in out:
            raise AssertionError(f"a sorted patch block must not be reported:\n{out}")
        if "[dependencies]" not in out:
            raise AssertionError(f"violation not attributed to [dependencies]:\n{out}")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print("SELF-TEST PASS: verify_dep_order + fix_dep_order (incl. [patch.*])")
    return 0


if __name__ == "__main__":
    sys.exit(main())
