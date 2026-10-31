#!/usr/bin/env python3
"""
Self-test for `verify_no_test_in_production.py` (§14.4).

Two directions have to hold, and both are asserted here:

  * a production file that carries a bare test attribute IS reported, and
  * every sanctioned / innocent shape is NOT reported.

The innocent shapes are the ones that matter most: a false positive on a
doc comment, on a string literal or on the `#[path]` include form would
block a correct commit.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VERIFIER = SCRIPT_DIR / "verify_no_test_in_production.py"

spec = importlib.util.spec_from_file_location("rsv_self_test_no_test_in_production", VERIFIER)
if spec is None or spec.loader is None:
    print("self-test: cannot load verifier", file=sys.stderr)
    raise SystemExit(2)
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    if ok:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}" + (f" — {detail}" if detail else ""))
        FAILURES.append(name)


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def build(root: Path) -> dict[str, Path]:
    """Fixture tree: root/pkg/{src,tests}."""
    (root / "pkg" / "src").mkdir(parents=True, exist_ok=True)
    (root / "pkg" / "tests").mkdir(parents=True, exist_ok=True)
    write(root, "pkg/Cargo.toml", "[package]\nname = \"pkg\"\n")
    files = {
        "bare": write(
            root,
            "pkg/src/bare.rs",
            "pub fn compute() -> usize {\n    1\n}\n\n#[test]\nfn compute_works() {\n"
            "    assert_eq!(compute(), 1);\n}\n",
        ),
        "tokio": write(
            root,
            "pkg/src/async_case.rs",
            "#[tokio::test]\nasync fn async_case_works() {\n    assert!(true);\n}\n",
        ),
        "wasm": write(
            root,
            "pkg/src/wasm_case.rs",
            "#[wasm_bindgen_test]\nfn wasm_case_works() {\n    assert!(true);\n}\n",
        ),
        "inline_mod": write(
            root,
            "pkg/src/inline_mod.rs",
            "pub fn compute() -> usize {\n    1\n}\n\n#[cfg(test)]\nmod tests {\n"
            "    use super::*;\n\n    #[test]\n    fn inner() {\n        assert_eq!(compute(), 1);\n"
            "    }\n}\n",
        ),
        "include": write(
            root,
            "pkg/src/include.rs",
            "#[cfg(test)]\n#[path = \"../tests/mod.rs\"]\nmod tests;\n",
        ),
        "doc_comment": write(
            root,
            "pkg/src/doc_comment.rs",
            "/// ```rust\n/// #[test]\n/// fn example() {}\n/// ```\npub fn helper() {}\n",
        ),
        "string_literal": write(
            root,
            "pkg/src/string_literal.rs",
            "pub const SNIPPET: &str = \"#[test] fn example() {}\";\n",
        ),
        "block_comment": write(
            root,
            "pkg/src/block_comment.rs",
            "/*\n#[test]\nfn example() {}\n*/\npub fn helper() {}\n",
        ),
        "plain": write(
            root,
            "pkg/src/plain.rs",
            "pub fn helper() -> usize {\n    1\n}\n",
        ),
        "helper_mod": write(
            root,
            "pkg/src/helper_mod.rs",
            "mod helpers {\n    #[test]\n    fn inner() {\n        assert!(true);\n    }\n}\n",
        ),
        "cfg_test_fn": write(
            root,
            "pkg/src/cfg_test_fn.rs",
            "#[cfg(test)]\nfn helper() -> usize {\n    1\n}\n",
        ),
        # A character literal carrying an unbalanced brace.  The inline
        # block's extent is found by brace counting, so an unmasked '{'
        # makes the block look like it runs to end-of-file and every
        # `#[test]` after it escapes the report.
        "brace_char": write(
            root,
            "pkg/src/brace_char.rs",
            "pub fn helper() -> usize {\n    1\n}\n\n#[cfg(test)]\nmod tests {\n"
            "    use super::*;\n\n    const BRACE: char = '{';\n\n"
            "    #[test]\n    fn inner() {\n        assert_eq!(helper(), 1);\n    }\n}\n\n"
            "#[test]\nfn bare_after_block() {\n    assert_eq!(helper(), 1);\n}\n",
        ),
        "lifetime": write(
            root,
            "pkg/src/lifetime.rs",
            "pub fn borrowed<'a>(x: &'a str) -> usize {\n    x.len()\n}\n\n"
            "#[test]\nfn borrowed_works() {\n    assert_eq!(borrowed(\"ab\"), 2);\n}\n",
        ),
        "in_tests": write(
            root,
            "pkg/tests/mod.rs",
            "#[test]\nfn a_test_lives_in_tests() {\n    assert!(true);\n}\n",
        ),
    }
    return files


def main() -> int:
    if not VERIFIER.is_file():
        print(f"self-test: missing {VERIFIER}", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        files = build(root)
        crate_root = root / "pkg"

        # --- violating shapes must be reported -------------------------
        # `brace_char` has BOTH an inline block (owned by the sibling
        # verifier) and a bare `#[test]` after it; only the bare one is
        # this verifier's finding.
        for name in ("bare", "tokio", "wasm", "helper_mod", "brace_char", "lifetime"):
            found = verifier.audit_one(files[name], crate_root)
            check(
                f"reports bare test attribute: {name}",
                len(found) == 1,
                f"got {len(found)} finding(s): {found}",
            )
            if found:
                check(
                    f"finding names the attribute: {name}",
                    "bare `#" in found[0] and "§14.4" in found[0],
                    found[0],
                )

        # --- innocent shapes must NOT be reported ----------------------
        for name in (
            "inline_mod",
            "include",
            "doc_comment",
            "string_literal",
            "block_comment",
            "plain",
            "cfg_test_fn",
            "in_tests",
        ):
            found = verifier.audit_one(files[name], crate_root)
            check(
                f"clean: {name}",
                not found,
                f"unexpected finding(s): {found}",
            )

        # --- CLI mode --------------------------------------------------
        result = subprocess.run(
            [sys.executable, str(VERIFIER), str(crate_root)],
            capture_output=True,
            text=True,
        )
        check(
            "CLI exits 1 on a violating tree",
            result.returncode == 1,
            f"rc={result.returncode}",
        )
        # Every violating fixture in the tree is counted: bare, tokio, wasm,
        # helper_mod (a #[test] fn in a non-cfg(test) mod is still a test
        # living in a production file), brace_char (the bare `#[test]` AFTER
        # the inline block) and lifetime.
        expected = 6
        check(
            "CLI prints the violation count",
            f"{expected} violation(s)" in result.stdout,
            result.stdout.strip()[-200:],
        )

        clean_root = root / "clean"
        (clean_root / "src").mkdir(parents=True, exist_ok=True)
        write(clean_root, "Cargo.toml", "[package]\nname = \"clean\"\n")
        write(clean_root, "src/lib.rs", "pub fn helper() -> usize {\n    1\n}\n")
        result = subprocess.run(
            [sys.executable, str(VERIFIER), str(clean_root)],
            capture_output=True,
            text=True,
        )
        check(
            "CLI exits 0 on a clean tree",
            result.returncode == 0,
            f"rc={result.returncode} stdout={result.stdout.strip()!r}",
        )

    if FAILURES:
        print(f"\nself-test FAILED: {len(FAILURES)} check(s) failed", file=sys.stderr)
        for name in FAILURES:
            print(f"  - {name}", file=sys.stderr)
        return 1
    print("\nself-test PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
