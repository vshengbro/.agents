#!/usr/bin/env python3
"""Prove that external-path findings include committed and uncommitted work."""
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("verify_no_external_crate_path.py")


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, stdout=subprocess.DEVNULL)


def verify(root: Path, expected: int) -> None:
    result = subprocess.run(
        [os.environ.get("PYTHON", "python3"), str(SCRIPT), str(root)],
        capture_output=True,
        text=True,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
    )
    assert result.returncode == (1 if expected else 0), result.stdout + result.stderr
    assert result.stdout.count("serde_json::Value") == expected, result.stdout


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="external-path-", dir=os.environ.get("TMPDIR")) as directory:
        root = Path(directory)
        git(root, "init", "--initial-branch=master")
        (root / "Cargo.toml").write_text('[package]\nname="fixture"\nversion="0.1.0"\n\n[workspace]\n\n[dependencies]\nserde_json="1"\n')
        (root / "src").mkdir()
        (root / "src/lib.rs").write_text("//! fixture\n//!\n//! External-path verifier fixture.\npub mod r#fn;\n")
        source = root / "src/fn.rs"
        source.write_text("")
        git(root, "add", ".")
        git(root, "commit", "-m", "test: baseline")
        git(root, "update-ref", "refs/remotes/origin/master", "HEAD")
        source.write_text("pub fn changed() { let value: serde_json::Value = todo!(); }\n")
        verify(root, 1)
        git(root, "add", "src/fn.rs")
        verify(root, 1)
        source.write_text("")
        verify(root, 0)
        source.write_text("pub fn changed() { let value: serde_json::Value = todo!(); }\n")
        verify(root, 1)
        git(root, "update-ref", "-d", "refs/remotes/origin/master")
        verify(root, 1)
        (root / "src/untracked.rs").write_text("pub fn untracked() { let value: serde_json::Value = todo!(); }\n")
        result = subprocess.run(["python3", str(SCRIPT), str(root)], capture_output=True, text=True)
        assert result.returncode == 1 and "untracked.rs" in result.stdout, result.stdout
    with tempfile.TemporaryDirectory(prefix="external-path-unborn-", dir=os.environ.get("TMPDIR")) as directory:
        root = Path(directory)
        git(root, "init", "--initial-branch=master")
        (root / "Cargo.toml").write_text('[package]\nname="fixture"\nversion="0.1.0"\n\n[dependencies]\nserde_json="1"\n')
        (root / "src").mkdir()
        (root / "src/fn.rs").write_text("pub fn staged() { let value: serde_json::Value = todo!(); }\n")
        git(root, "add", ".")
        verify(root, 1)
    print("SELF-TEST PASS: external-path committed, working-tree, staged and untracked coverage")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())