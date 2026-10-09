#!/usr/bin/env python3
"""Self-test for verify_no_pub_in_tests.py + fix_no_pub_in_tests.py
(narrow rule, pitfalls §92).

Fixtures assert:

  pub fn used only inside its own fn.rs            -> flagged, stripped
  pub const in <sub>/const.rs globbed by parent    -> NOT flagged (load-bearing)
  pub use re-export in tests/mod.rs                -> NOT flagged (load-bearing)
  pub struct named by a sibling test file          -> NOT flagged (cross-file)
  pub fn helper called from a sibling file         -> NOT flagged (cross-file)
  "pub fn" inside a string literal                 -> not flagged
  pub items in src/ (not a tests dir)              -> never scanned
  fixer: dry-run byte-identical, --write converges + idempotent

Run: python3 self_test_no_pub_in_tests.py
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import fix_no_pub_in_tests as fixer  # noqa: E402
import verify_no_pub_in_tests as verifier  # noqa: E402

TESTS_MOD = """mod api;

pub use std::{fs, path::PathBuf};

use super::*;
"""

API_MOD = """mod r#const;
mod r#fn;

use r#const::*;

use super::*;
"""

API_CONST = """pub const SHARED_BASE: &str = "www";
pub const LOCAL_ONLY: &str = "unused-elsewhere";
"""

API_FN = """use super::*;

pub struct Probe {
    pub hits: u8,
}

#[test]
pub fn reads_files() {
    let msg: &str = "pub fn inside a string is not code";
    let root: PathBuf = SHARED_BASE.into();
    assert!(msg.contains("pub fn"));
    assert!(root.is_absolute() || true);
}

pub fn local_helper() -> u8 {
    1
}

#[test]
fn uses_local_helper() {
    assert_eq!(local_helper(), 1);
}
"""

OTHER_FN = """use super::*;

#[test]
fn uses_probe() {
    let probe: Probe = Probe { hits: 1 };
    assert_eq!(probe.hits, 1);
}
"""

SRC_LIB = """pub fn production_api() {}
pub const KEEP_ME: u8 = 9;
"""


def build_ws(root: Path) -> None:
    (root / "src").mkdir(parents=True)
    (root / "src/lib.rs").write_text(SRC_LIB)
    (root / "tests/api").mkdir(parents=True)
    (root / "tests/other").mkdir(parents=True)
    (root / "tests/mod.rs").write_text(TESTS_MOD)
    (root / "tests/api/mod.rs").write_text(API_MOD)
    (root / "tests/api/const.rs").write_text(API_CONST)
    (root / "tests/api/fn.rs").write_text(API_FN)
    (root / "tests/other/fn.rs").write_text(OTHER_FN)
    (root / "tests/other/mod.rs").write_text("mod r#fn;\n\nuse super::*;\n")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="no_pub_in_tests_selftest_"))
    try:
        build_ws(tmp)
        failures: list[str] = []
        hits = verifier.analyze(tmp)
        # pub use in tests/mod.rs is now BANNED (2026-10-07 user rule) ->
        # flagged and stripped to plain use; the glob chain still reaches it.
        want = {"reads_files", "local_helper", "LOCAL_ONLY"}
        names = set()
        for h in hits:
            for cand in ("reads_files", "local_helper", "LOCAL_ONLY", "SHARED_BASE", "Probe", "hits"):
                if f"'{cand}'" in h:
                    names.add(cand)
        pub_use_hits = [h for h in hits if "pub-marked use is banned" in h]
        if len(pub_use_hits) != 1 or "tests/mod.rs:3" not in pub_use_hits[0]:
            failures.append(f"pub use in tests/mod.rs should be flagged once at :3: {pub_use_hits}")
        if names != want:
            failures.append(f"flagged {sorted(names)}, want {sorted(want)}: {hits}")

        target = tmp / "tests/api/fn.rs"
        before = target.read_text()
        argv = sys.argv
        sys.argv = ["fix_no_pub_in_tests.py", str(tmp)]
        try:
            dry_rc = fixer.main()
        finally:
            sys.argv = argv
        if dry_rc != 1 or target.read_text() != before:
            failures.append(f"dry-run rc={dry_rc} or modified the file")

        sys.argv = ["fix_no_pub_in_tests.py", str(tmp), "--write"]
        try:
            write_rc = fixer.main()
        finally:
            sys.argv = argv
        if write_rc != 0:
            failures.append(f"--write exit {write_rc}, want 0")
        fixed = target.read_text()
        for needle in (
            "fn reads_files()",
            "fn local_helper() -> u8 {",
            "pub struct Probe {",
            '"pub fn inside a string is not code"',
        ):
            if needle not in fixed:
                failures.append(f"lost or wrongly rewrote {needle!r}")
        const_fixed = (tmp / "tests/api/const.rs").read_text()
        if "pub const SHARED_BASE" not in const_fixed:
            failures.append("SHARED_BASE (cross-file) lost its pub")
        if "const LOCAL_ONLY" not in const_fixed:
            failures.append("LOCAL_ONLY (single-reader) not stripped")
        mod_fixed = (tmp / "tests/mod.rs").read_text()
        if "use std::{fs, path::PathBuf};" not in mod_fixed:
            failures.append("banned pub use not stripped to plain use")
        if "pub use" in mod_fixed or "pub(crate) use" in mod_fixed:
            failures.append("tests/mod.rs still holds a pub-marked use")
        if (tmp / "src/lib.rs").read_text() != SRC_LIB:
            failures.append("fixer touched src/ (out of scope)")
        if verifier.analyze(tmp):
            failures.append(f"violations remain after fix: {verifier.analyze(tmp)}")
        sys.argv = ["fix_no_pub_in_tests.py", str(tmp), "--write"]
        try:
            second_rc = fixer.main()
        finally:
            sys.argv = argv
        if second_rc != 0:
            failures.append("second --write was not idempotent")

        if failures:
            print("SELF-TEST FAIL:")
            for failure in failures:
                print(f"  - {failure}")
            return 1
        print("SELF-TEST OK: verify_no_pub_in_tests + fix_no_pub_in_tests (narrow rule)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
