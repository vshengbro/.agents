#!/usr/bin/env python3
"""Self-test for verify_no_inline_cfg_test.py (§14.4).

Fixtures assert:

  inline `#[cfg(test)] mod tests { ... }` in a production file -> flagged
  the sanctioned `#[cfg(test)] #[path = "../tests/mod.rs"] mod tests;`
                                                      -> NOT flagged
  `#[cfg(test)] mod tests;` (declaration, no body)     -> NOT flagged
  `#[cfg(all(test, unix))] mod tests { ... }`           -> flagged
  the block text inside a `//` comment                  -> NOT flagged
  the block text inside a doc comment                   -> NOT flagged
  a tests/ file                                         -> never scanned
  a `mod` block with no cfg(test) above it              -> NOT flagged

Run: python3 self_test_no_inline_cfg_test.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import verify_no_inline_cfg_test as verifier  # noqa: E402

INLINE_BLOCK = """use super::*;

/// A production helper.
pub fn helper() -> u8 {
    1
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn helper_works() {
        assert_eq!(helper(), 1);
    }
}
"""

SANCTIONED_INCLUDE = """use super::*;

/// A production helper.
pub fn helper() -> u8 {
    1
}

#[cfg(test)]
#[path = "../tests/mod.rs"]
mod tests;
"""

DECLARATION_ONLY = """use super::*;

/// A production helper.
pub fn helper() -> u8 {
    1
}

#[cfg(test)]
mod tests;
"""

CFG_ALL = """use super::*;

/// A production helper.
pub fn helper() -> u8 {
    1
}

#[cfg(all(test, unix))]
mod tests {
    #[test]
    fn helper_works() {
        assert_eq!(helper(), 1);
    }
}
"""

IN_COMMENT = """use super::*;

/// A production helper.
pub fn helper() -> u8 {
    1
}

// #[cfg(test)]
// mod tests {
//     #[test]
//     fn helper_works() {}
// }
"""

IN_DOC_COMMENT = """use super::*;

/// A production helper.
///
/// ```rust
/// #[cfg(test)]
/// mod tests {
///     #[test]
///     fn helper_works() {}
/// }
/// ```
pub fn helper() -> u8 {
    1
}
"""

PLAIN_MOD_BLOCK = """use super::*;

/// A production helper.
pub fn helper() -> u8 {
    1
}

mod helper_tests {
    pub fn helper() -> u8 {
        1
    }
}
"""


def build(root: Path) -> None:
    src = root / "src"
    src.mkdir(parents=True, exist_ok=True)
    (root / "Cargo.toml").write_text("[package]\nname = \"probe\"\n")
    (src / "lib.rs").write_text("pub fn helper() -> u8 { 1 }\n")
    (src / "fn.rs").write_text(INLINE_BLOCK)
    tests = root / "tests"
    tests.mkdir(parents=True, exist_ok=True)
    (tests / "fn.rs").write_text(INLINE_BLOCK)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="no_inline_cfg_test_selftest_"))
    failures: list[str] = []
    try:
        build(tmp)
        root = tmp
        src_fn = root / "src" / "fn.rs"

        hits = verifier.audit_one(src_fn, root)
        if len(hits) != 1:
            failures.append(f"inline block should be flagged once, got {hits}")
        elif "fn.rs" not in hits[0]:
            failures.append(f"hit lost its file attribution: {hits}")

        # tests/ tree is never scanned.
        test_fn = root / "tests" / "fn.rs"
        if verifier.audit_one(test_fn, root):
            failures.append("a tests/ file must never be flagged")

        # lib.rs is exempt by name? No — only the tests/ tree is exempt.
        # lib.rs holds the sanctioned include form and must stay silent.
        lib_rs = root / "src" / "lib.rs"
        if verifier.audit_one(lib_rs, root):
            failures.append("a clean lib.rs must not be flagged")

        cases = [
            ("sanctioned #[path] include", SANCTIONED_INCLUDE, False),
            ("mod declaration without a body", DECLARATION_ONLY, False),
            ("#[cfg(all(test, unix))] inline block", CFG_ALL, True),
            ("block inside a // comment", IN_COMMENT, False),
            ("block inside a doc comment", IN_DOC_COMMENT, False),
            ("plain mod block without cfg(test)", PLAIN_MOD_BLOCK, False),
        ]
        for label, content, should_flag in cases:
            src_fn.write_text(content)
            hits = verifier.audit_one(src_fn, root)
            if should_flag and not hits:
                failures.append(f"{label}: expected a violation, got none")
            if not should_flag and hits:
                failures.append(f"{label}: expected no violation, got {hits}")

        # Whole-repo mode: only the src/ file is a violation.
        src_fn.write_text(INLINE_BLOCK)
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "verify_no_inline_cfg_test.py"), str(root)],
            capture_output=True, text=True,
        )
        if result.returncode != 1:
            failures.append(f"whole-repo mode rc={result.returncode}, want 1")
        if "1 violation(s)" not in result.stdout:
            failures.append(f"whole-repo mode summary wrong: {result.stdout!r}")

        if failures:
            print("SELF-TEST FAIL:")
            for failure in failures:
                print(f"  - {failure}")
            return 1
        print("SELF-TEST OK: verify_no_inline_cfg_test (§14.4)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
