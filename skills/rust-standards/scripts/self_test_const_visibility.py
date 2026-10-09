#!/usr/bin/env python3
"""Self-test for verify_const_visibility.py + fix_const_visibility.py.

Absolute ban (user ruling 2026-10-07): every `pub const`/`pub static` is a
violation, external readers included. Builds a two-crate throwaway workspace
and asserts:

  USED_EXTERNALLY (read by beta)      -> violation (no exemption)
  VIA_TESTS (read by alpha's tests/)  -> violation (tests get inline copies)
  CARGO_TOML (read by own main.rs)    -> violation (bin is its own crate)
  STRING_MENTIONED (in a beta string) -> violation
  INTERNAL_ONLY (alpha-internal only) -> violation
  COMMENT_ONLY (only a beta comment)  -> violation
  NOWHERE (zero readers at all)       -> unwired report, NOT a violation
  pub(crate) / private items          -> never flagged
  pub const fn                        -> never flagged (function, not const)
  fixer                               -> dry-run writes nothing, --write
                                        converges + idempotent + content kept

Run: python3 self_test_const_visibility.py
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import fix_const_visibility as fixer  # noqa: E402
import verify_const_visibility as verifier  # noqa: E402

ROOT_MANIFEST = "[workspace]\nmembers = [\"alpha\", \"beta\"]\nresolver = \"2\"\n"
ALPHA_MANIFEST = "[package]\nname = \"alpha\"\nversion = \"0.1.0\"\n"
BETA_MANIFEST = "[package]\nname = \"beta\"\nversion = \"0.1.0\"\n"

ALPHA_LIB = """pub const USED_EXTERNALLY: u8 = 1;
pub const VIA_TESTS: u8 = 2;

/// Aggregates the crate-internal constants.
pub fn total() -> u8 {
    USED_EXTERNALLY + VIA_TESTS + INTERNAL_ONLY + COMMENT_ONLY
}
"""

ALPHA_CONST = """pub const CARGO_TOML: &str = "Cargo.toml";
pub const INTERNAL_ONLY: u8 = 3;
pub const COMMENT_ONLY: u8 = 4;
pub const STRING_MENTIONED: u8 = 5;
pub const NOWHERE: u8 = 6;
pub(crate) const ALREADY_CRATE: u8 = 7;
const PRIVATE_ONE: u8 = 8;
"""

ALPHA_TEST = """use alpha::*;

#[test]
fn reads_via_tests() {
    assert_eq!(VIA_TESTS, 2);
}
"""

BETA_LIB = """/// Mentions COMMENT_ONLY in prose - documentation is not a reader.
pub fn read() -> u8 {
    let emitted: &str = "generated code names STRING_MENTIONED verbatim";
    let _keep: &str = emitted;
    alpha::USED_EXTERNALLY
}
"""

ALPHA_MAIN = """use alpha::*;

fn main() {
    let _manifest: &str = CARGO_TOML;
}
"""


def build_ws(root: Path) -> None:
    (root / ".git").mkdir(parents=True)
    (root / "Cargo.toml").write_text(ROOT_MANIFEST)
    (root / "alpha/Cargo.toml").parent.mkdir(parents=True, exist_ok=True)
    (root / "alpha/Cargo.toml").write_text(ALPHA_MANIFEST)
    (root / "beta/Cargo.toml").parent.mkdir(parents=True, exist_ok=True)
    (root / "beta/Cargo.toml").write_text(BETA_MANIFEST)
    (root / "alpha/src").mkdir(parents=True, exist_ok=True)
    (root / "alpha/src/lib.rs").write_text(ALPHA_LIB)
    (root / "alpha/src/main.rs").write_text(ALPHA_MAIN)
    (root / "alpha/src/const.rs").write_text(ALPHA_CONST)
    (root / "alpha/tests/at").mkdir(parents=True, exist_ok=True)
    (root / "alpha/tests/at/fn.rs").write_text(ALPHA_TEST)
    (root / "beta/src").mkdir(parents=True, exist_ok=True)
    (root / "beta/src/lib.rs").write_text(BETA_LIB)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="const_visibility_selftest_"))
    try:
        build_ws(tmp)
        failures: list[str] = []
        violations, unwired = verifier.analyze(tmp)
        flagged = set()
        for v in violations:
            for cand in ("INTERNAL_ONLY", "COMMENT_ONLY", "STRING_MENTIONED", "NOWHERE", "USED_EXTERNALLY", "VIA_TESTS", "CARGO_TOML"):
                if f" {cand}'" in v:
                    flagged.add(cand)
        want = {"INTERNAL_ONLY", "COMMENT_ONLY", "STRING_MENTIONED", "USED_EXTERNALLY", "VIA_TESTS", "CARGO_TOML"}
        if flagged != want:
            failures.append(f"violations flagged {sorted(flagged)}, want {sorted(want)}: {violations}")
        unwired_flag = [u for u in unwired if " NOWHERE'" in u]
        if len(unwired_flag) != 1:
            failures.append(f"unwired should name NOWHERE exactly once: {unwired}")
        if any("NOWHERE" in v for v in violations):
            failures.append("NOWHERE must not be a violation (unwired class)")

        # audit_one adapter
        hits = verifier.audit_one(tmp / "alpha/src/const.rs")
        if not any("INTERNAL_ONLY" in h for h in hits):
            failures.append(f"audit_one missed INTERNAL_ONLY: {hits}")
        lib_hits = verifier.audit_one(tmp / "alpha/src/lib.rs")
        if not any("USED_EXTERNALLY" in h for h in lib_hits) or not any("VIA_TESTS" in h for h in lib_hits):
            failures.append(f"audit_one must flag externally-read consts too (absolute ban): {lib_hits}")

        # constant-table exemption via rust-standards.toml (2026-10-09 ruling;
        # patterns are repo-relative directory/file globs, `**` crosses segments)
        (tmp / "gamma/src").mkdir(parents=True, exist_ok=True)
        (tmp / "gamma/Cargo.toml").write_text(
            "[package]\nname = \"gamma\"\nversion = \"0.1.0\"\n"
        )
        (tmp / "gamma/src/lib.rs").write_text("pub const GAMMA_TABLE: u8 = 42;\n")
        with (tmp / "beta/src/lib.rs").open("a") as fh:
            fh.write("\npub fn read_gamma() -> u8 {\n    gamma::GAMMA_TABLE\n}\n")
        violations, unwired = verifier.analyze(tmp)
        if not any(" GAMMA_TABLE'" in v for v in violations):
            failures.append(f"GAMMA_TABLE must be a violation before exemption: {violations}")
        cfg = tmp / "rust-standards.toml"
        for label, pattern in (
            ("bare directory prefix", "gamma"),
            ("exact file", "gamma/src/lib.rs"),
            ("** spanning segments", "**/gamma/**"),
            ("segment glob + **", "g?mma/*"),
        ):
            cfg.write_text(f'pub_const_exempt = ["{pattern}"]\n')
            violations, unwired = verifier.analyze(tmp)
            if any("GAMMA" in v for v in violations) or any("GAMMA" in u for u in unwired):
                failures.append(f"{label} pattern {pattern!r} left gamma flagged: {violations} {unwired}")
            if not any("INTERNAL_ONLY" in v for v in violations):
                failures.append(f"exemption must stay scoped, alpha still flagged under {pattern!r}")
        cfg.write_text('pub_const_exempt = ["beta"]\n')
        violations, _ = verifier.analyze(tmp)
        if not any(" GAMMA_TABLE'" in v for v in violations):
            failures.append(f"non-matching pattern must not exempt gamma: {violations}")
        cfg.write_text('pub_const_exempt = ["gamma"]\n')
        if verifier.audit_one(tmp / "gamma/src/lib.rs"):
            failures.append("audit_one must honor the exemption for the staged file")

        # fixer: dry-run must not write
        target = tmp / "alpha/src/const.rs"
        before = target.read_text()
        argv = sys.argv
        sys.argv = ["fix_const_visibility.py", str(tmp)]
        try:
            dry_rc = fixer.main()
        finally:
            sys.argv = argv
        if dry_rc != 1:
            failures.append(f"dry-run exit {dry_rc}, want 1")
        if target.read_text() != before:
            failures.append("dry-run MODIFIED the file")

        # --write converges, idempotent, content-preserving
        sys.argv = ["fix_const_visibility.py", str(tmp), "--write"]
        try:
            write_rc = fixer.main()
        finally:
            sys.argv = argv
        if write_rc != 0:
            failures.append(f"--write exit {write_rc}, want 0 (re-verify clean)")
        fixed = target.read_text()
        for needle in (
            "pub(crate) const CARGO_TOML: &str = \"Cargo.toml\";",
            "pub(crate) const INTERNAL_ONLY: u8 = 3;",
            "pub(crate) const COMMENT_ONLY: u8 = 4;",
            "pub(crate) const STRING_MENTIONED: u8 = 5;",
            "pub const NOWHERE: u8 = 6;",
            "pub(crate) const ALREADY_CRATE: u8 = 7;",
            "const PRIVATE_ONE: u8 = 8;",
        ):
            if needle not in fixed:
                failures.append(f"lost or wrongly rewrote {needle!r}")
        lib_fixed = (tmp / "alpha/src/lib.rs").read_text()
        if "pub(crate) const USED_EXTERNALLY: u8 = 1;" not in lib_fixed:
            failures.append("USED_EXTERNALLY not reduced (absolute ban)")
        if "pub(crate) const VIA_TESTS: u8 = 2;" not in lib_fixed:
            failures.append("VIA_TESTS not reduced (absolute ban)")
        if (tmp / "gamma/src/lib.rs").read_text() != "pub const GAMMA_TABLE: u8 = 42;\n":
            failures.append("fixer must not rewrite an exempt constant-table crate")
        violations_after, _ = verifier.analyze(tmp)
        if violations_after:
            failures.append(f"violations remain after fix: {violations_after}")
        sys.argv = ["fix_const_visibility.py", str(tmp), "--write"]
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
        print("SELF-TEST OK: verify_const_visibility + fix_const_visibility")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
