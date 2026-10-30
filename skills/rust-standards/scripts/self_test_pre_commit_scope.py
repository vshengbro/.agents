#!/usr/bin/env python3
"""Self-test for the pre-commit wrapper's scope handling.

Two defects are covered:

1. `--no-scope` ran ZERO fixers. The file lists are empty in whole-repo
   mode, so the `continue` guards skipped every fixer before it ran,
   while the banner still announced "fixers may rewrite any file".

2. In whole-repo mode the argv kept a bare `--files` with no values.
   `nargs="*"` parses that as an EMPTY list, which
   strictify_tests_layout.py and doc_comment_audit.py read as "an empty
   scope" — they fix nothing. Dropping the flag gives every fixer its
   own documented whole-repo default.

The test builds a real fixture repo, runs the wrapper in both modes,
and asserts on what actually happened.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PRE_COMMIT = SCRIPT_DIR / "rust_pre_commit.py"

failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if cond:
        print(f"  PASS  {msg}")
    else:
        print(f"  FAIL  {msg}")
        failures.append(msg)


def make_fixture(root: Path) -> None:
    """A minimal repo the fixers will actually change.

    The Cargo.toml has a non-canonical dependency order, so the
    dep-order fixer has something to rewrite.
    """
    (root / "src").mkdir(parents=True)
    (root / "Cargo.toml").write_text(
        "[package]\n"
        'name = "fixture"\n'
        'version = "0.1.0"\n'
        'edition = "2021"\n'
        "\n"
        "[dependencies]\n"
        'serde = "1"\n'
        'anyhow = "1"\n'
        "\n",
        encoding="utf-8",
    )
    (root / "src" / "lib.rs").write_text(
        "pub fn alpha() -> u8 {\n    1\n}\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q", "."], cwd=root, check=True)
    # The fixture is a throwaway repo, not a change under review. Point
    # hooks at an empty directory so the global rust-standards hook does
    # not block the fixture's own setup commit.
    empty_hooks = root / ".no-hooks"
    empty_hooks.mkdir(exist_ok=True)
    subprocess.run(
        ["git", "config", "core.hooksPath", str(empty_hooks)],
        cwd=root,
        check=True,
    )
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=t@example.com",
            "-c",
            "user.name=t",
            "commit",
            "-qm",
            "init",
        ],
        cwd=root,
        check=True,
    )


def run_wrapper(root: Path, *args: str) -> str:
    """Run the wrapper with the fixers ENABLED (no --no-fix)."""
    proc = subprocess.run(
        [sys.executable, str(PRE_COMMIT), *args, str(root)],
        capture_output=True,
        text=True,
        timeout=600,
    )
    return proc.stdout + proc.stderr


def phase1_lines(out: str) -> list[str]:
    return [line for line in out.splitlines() if "Phase 1 [" in line]


def test_no_scope_runs_the_fixers() -> None:
    print("\n[1] --no-scope must actually RUN the fixers")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "repo"
        root.mkdir()
        make_fixture(root)
        out = run_wrapper(root, "--no-scope")
        lines = phase1_lines(out)
        ran = [l for l in lines if "[SKIP]" not in l]
        check(
            len(ran) > 0,
            f"--no-scope ran at least one fixer "
            f"(got {len(ran)} of {len(lines)} Phase 1 lines)",
        )
        check(
            "Phase 1 [SKIP] auto-fixers" not in out,
            "--no-scope did not skip Phase 1 entirely",
        )


def test_no_scope_drops_the_files_flag() -> None:
    print("\n[2] --no-scope must not leave a bare --files in the argv")
    probe = (
        "import importlib.util, sys\n"
        f"spec = importlib.util.spec_from_file_location('rpc', {str(PRE_COMMIT)!r})\n"
        "m = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(m)\n"
        "a = ['python3', 'x.py', '--write', '/r', '--files']\n"
        "b = m._drop_empty_files_flag(a)\n"
        "assert '--files' not in b, b\n"
        "c = m._drop_empty_files_flag(['x.py', '--files', 'a.rs', 'b.rs'])\n"
        "assert c == ['x.py', '--files', 'a.rs', 'b.rs'], c\n"
        "print('helper ok')\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True
    )
    check(
        proc.returncode == 0 and "helper ok" in proc.stdout,
        f"_drop_empty_files_flag removes an empty flag and keeps a populated one "
        f"(rc={proc.returncode}, err={proc.stderr.strip()[:120]})",
    )


def test_whole_repo_argv_has_no_bare_files_flag() -> None:
    """Capture the REAL argv each fixer receives in whole-repo mode.

    This is the integration-level guard for defect #2: it does not rely
    on the helper being present, it asserts that no fixer is ever handed
    a `--files` with no values after it.
    """
    print("\n[2b] whole-repo mode: no fixer may receive a bare --files")
    probe = (
        "import importlib.util, sys, json\n"
        "from pathlib import Path\n"
        f"spec = importlib.util.spec_from_file_location('rpc', {str(PRE_COMMIT)!r})\n"
        "m = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(m)\n"
        "captured = []\n"
        "def fake_run(label, argv, cwd, timeout=300):\n"
        "    captured.append((label, list(argv)))\n"
        "    return 0, '', ''\n"
        "m._run = fake_run\n"
        "m.phase_fixers(Path('/tmp'), False, None)\n"
        "bad = []\n"
        "for label, argv in captured:\n"
        "    if '--files' in argv:\n"
        "        i = argv.index('--files')\n"
        "        if i + 1 >= len(argv) or argv[i+1].startswith('-'):\n"
        "            bad.append((label, argv))\n"
        "print(json.dumps({'n': len(captured), 'bad': bad}))\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True
    )
    ok = proc.returncode == 0
    payload = {}
    if ok:
        for line in proc.stdout.splitlines():
            if line.startswith("{"):
                import json

                payload = json.loads(line)
    check(
        ok and payload.get("n", 0) > 0,
        f"captured {payload.get('n', 0)} fixer argv(s) in whole-repo mode "
        f"(rc={proc.returncode}, err={proc.stderr.strip()[:200]})",
    )
    check(
        ok and not payload.get("bad"),
        f"no fixer received a bare --files in whole-repo mode "
        f"(bad={payload.get('bad')})",
    )


def test_scoped_argv_carries_real_file_paths() -> None:
    """Scoped mode must pass each file as its OWN argv element.

    The old form substituted one space-joined string, so `nargs="*"`
    parsed "a.rs b.rs" as a single path that resolves to nothing.
    """
    print("\n[2c] scoped mode: each file must be its own argv element")
    probe = (
        "import importlib.util, sys, json\n"
        "from pathlib import Path\n"
        f"spec = importlib.util.spec_from_file_location('rpc', {str(PRE_COMMIT)!r})\n"
        "m = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(m)\n"
        "captured = []\n"
        "def fake_run(label, argv, cwd, timeout=300):\n"
        "    captured.append((label, list(argv)))\n"
        "    return 0, '', ''\n"
        "m._run = fake_run\n"
        "m.phase_fixers(Path('/tmp'), False, ['a.rs', 'b.rs', 'Cargo.toml'])\n"
        "joined = []\n"
        "for label, argv in captured:\n"
        "    for a in argv:\n"
        "        if ' ' in a:\n"
        "            joined.append((label, a))\n"
        "print(json.dumps({'n': len(captured), 'joined': joined}))\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True
    )
    payload = {}
    if proc.returncode == 0:
        for line in proc.stdout.splitlines():
            if line.startswith("{"):
                import json

                payload = json.loads(line)
    check(
        proc.returncode == 0 and payload.get("n", 0) > 0,
        f"captured {payload.get('n', 0)} fixer argv(s) in scoped mode",
    )
    check(
        proc.returncode == 0 and not payload.get("joined"),
        f"no argv element contains a space-joined file list "
        f"(joined={payload.get('joined')})",
    )


def test_no_scope_does_not_report_false_drift() -> None:
    print("\n[3] --no-scope must not report out-of-scope drift")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "repo"
        root.mkdir()
        make_fixture(root)
        out = run_wrapper(root, "--no-scope")
        check(
            "OUTSIDE the change scope" not in out,
            "no out-of-scope drift warning in whole-repo mode",
        )


def test_no_scope_reports_what_it_rewrote() -> None:
    """A whole-repo sweep must never rewrite files silently."""
    print("\n[3b] --no-scope must report the files it rewrote")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "repo"
        root.mkdir()
        make_fixture(root)
        out = run_wrapper(root, "--no-scope")
        # Either nothing was rewritten (no report needed), or the rewrite
        # was reported. The failure mode is a rewrite with no report.
        check(
            ("rewrote" in out) or ("whole-repo sweep" in out),
            "a whole-repo sweep that rewrote files reports them",
        )


def test_scoped_mode_skips_fixers_when_nothing_changed() -> None:
    print("\n[4] scoped mode with no changes must still skip the fixers")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "repo"
        root.mkdir()
        make_fixture(root)
        out = run_wrapper(root)
        check(
            "no changes detected" in out,
            "scoped mode reports that the fixers were skipped",
        )
        check(
            not [
                l
                for l in phase1_lines(out)
                if "[SKIP] auto-fixers (no changed" not in l
                and "[SKIP] auto-fixers (--no-fix)" not in l
            ],
            "scoped mode ran no fixer when nothing changed",
        )


def test_scoped_mode_only_touches_changed_files() -> None:
    print("\n[5] scoped mode must not rewrite unchanged files")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "repo"
        root.mkdir()
        make_fixture(root)
        # Change ONE .rs file, leaving the Cargo.toml untouched. The
        # scoped fixers must not rewrite the Cargo.toml.
        (root / "src" / "lib.rs").write_text(
            "pub fn alpha() -> u8 {\n    2\n}\n", encoding="utf-8"
        )
        before = (root / "Cargo.toml").read_text(encoding="utf-8")
        out = run_wrapper(root)
        after = (root / "Cargo.toml").read_text(encoding="utf-8")
        check(
            before == after,
            "an unchanged Cargo.toml was not rewritten by a scoped run",
        )


def main() -> int:
    print("self_test_pre_commit_scope — pre-commit wrapper scope handling")
    test_no_scope_runs_the_fixers()
    test_no_scope_drops_the_files_flag()
    test_whole_repo_argv_has_no_bare_files_flag()
    test_scoped_argv_carries_real_file_paths()
    test_no_scope_does_not_report_false_drift()
    test_no_scope_reports_what_it_rewrote()
    test_scoped_mode_skips_fixers_when_nothing_changed()
    test_scoped_mode_only_touches_changed_files()

    print()
    if failures:
        print(f"FAIL — {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASS — all checks clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
