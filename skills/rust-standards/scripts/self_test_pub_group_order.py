#!/usr/bin/env python3
"""Self-test for verify_pub_group_order.py + fix_pub_group_order.py.

Builds throwaway fixture trees and asserts both directions:

  compliant -> exit 0, 0 hits
  violating -> exit 1, exact per-file counts
  tricky    -> exempt shapes stay quiet (private after pub(crate) is legal)
  fixer     -> dry-run writes nothing, --write converges to 0, idempotent,
               and preserves every declaration's name + value + doc block

Run: python3 self_test_pub_group_order.py
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import fix_pub_group_order as fixer  # noqa: E402
import verify_pub_group_order as verifier  # noqa: E402

COMPLIANT = '''use super::*;

/// First public constant.
pub const ALPHA: &str = "a";

/// Second public constant, multi-line value.
pub const BETA_LIST: &[u8] = &[
    1,
    2,
];

/// Crate-local constant.
pub(crate) const GAMMA: u32 = 7;

/// Private constant.
const DELTA: u32 = 8;
'''

VIOLATING = '''/// Crate-local constant.
pub(crate) const GAMMA: u32 = 7;

/// Public constant trapped below the crate-local group.
pub const ALPHA: &str = "a";
'''

VIOLATING_TWO = '''const DELTA: u32 = 8;

/// crate-visible.
pub(crate) const GAMMA: u32 = 7;

/// public one.
pub const ALPHA: &str = "a";

/// public two.
pub const BETA: &str = "b";
'''

TRICKY = '''use super::*;

/// Brackets inside a literal must not confuse the span parser.
pub const OPEN_BRACKET: &str = "[{(}])";

/// A crate-local item.
pub(crate) const MID: u8 = 1;

/// Private AFTER pub(crate) is the legal tail of the file.
const LOW: u8 = 2;

/// Another private one, with an attribute block.
#[allow(dead_code)]
const LOWER: u8 = 3;
'''

UNSAFE_UNTERMINATED = '''pub(crate) const BROKEN: &[u8] = &[
    1,
'''

VIOLATING_RAW = '''pub(crate) const LOCAL: u8 = 1;

/// The `index.html` template, kept inline for the dev server.
pub const INDEX_HTML_DEV: &str = r#"<!doctype html>
<html lang="en">
  <head>
    <style>
      body { margin: 0; padding: 0; }
    </style>
  </head>
  <body>
    <script>
      const payload = {"type":"Reload"};
      fetch('/__euv_reload');
    </script>
  </body>
</html>
"#;

/// Another crate-local constant.
pub(crate) const TAIL: u8 = 2;
'''


def write_tree(root: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def run_verifier(root: Path) -> tuple[int, list[str]]:
    hits: list[str] = []
    for path in verifier.iter_targets(root):
        hits += verifier.check_file(path, str(path.relative_to(root)))
    return (1 if hits else 0), hits


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="pub_group_order_selftest_"))
    try:
        failures: list[str] = []

        # --- compliant tree: verifier silent --------------------------------
        compliant = tmp / "compliant"
        write_tree(compliant, {"src/const.rs": COMPLIANT})
        rc, hits = run_verifier(compliant)
        if rc != 0 or hits:
            failures.append(f"compliant tree reported {len(hits)} hit(s): {hits}")

        # --- violating tree: exact counts ------------------------------------
        violating = tmp / "violating"
        write_tree(
            violating,
            {"src/const.rs": VIOLATING, "src/deeper/static.rs": VIOLATING_TWO},
        )
        rc, hits = run_verifier(violating)
        if rc != 1:
            failures.append(f"violating tree exit {rc}, want 1")
        const_hits = [h for h in hits if h.startswith("src/const.rs:")]
        static_hits = [h for h in hits if h.startswith("src/deeper/static.rs:")]
        if len(const_hits) != 1:
            failures.append(f"src/const.rs: {len(const_hits)} hit(s), want 1: {const_hits}")
        if len(static_hits) != 3:
            failures.append(f"src/deeper/static.rs: {len(static_hits)} hit(s), want 3: {static_hits}")

        # --- tricky tree: exempt shapes stay quiet ---------------------------
        tricky = tmp / "tricky"
        write_tree(tricky, {"src/const.rs": TRICKY})
        rc, hits = run_verifier(tricky)
        if rc != 0 or hits:
            failures.append(f"tricky tree reported {len(hits)} hit(s): {hits}")

        # --- unsafe shape: skipped, never mangled ----------------------------
        unsafe = tmp / "unsafe"
        write_tree(unsafe, {"src/const.rs": UNSAFE_UNTERMINATED})
        rc, _ = run_verifier(unsafe)
        if fixer.fix_file(unsafe / "src/const.rs", write=True):
            failures.append("fixer touched an unterminated declaration")

        # --- audit_one adapter ------------------------------------------------
        if not verifier.audit_one(violating / "src/const.rs"):
            failures.append("audit_one returned [] for a violating const.rs")
        if verifier.audit_one(violating / "src" / "fn.rs"):
            failures.append("audit_one reported on a non-const/static file")

        # --- fixer: dry-run writes nothing -----------------------------------
        dry_target = violating / "src/const.rs"
        before = dry_target.read_text()
        if not fixer.fix_file(dry_target, write=False):
            failures.append("dry-run did not detect the violating file")
        if dry_target.read_text() != before:
            failures.append("dry-run MODIFIED the file")

        # --- fixer: --write converges, idempotent, content-preserving --------
        if not fixer.fix_file(dry_target, write=True):
            failures.append("--write reported no change on a violating file")
        fixed = dry_target.read_text()
        rc, hits = run_verifier(violating)
        if [h for h in hits if h.startswith("src/const.rs:")]:
            failures.append(f"verifier still reports on fixed file: {hits}")
        if fixer.fix_file(dry_target, write=True):
            failures.append("second --write was not idempotent")
        for needle in ('pub const ALPHA: &str = "a";', "pub(crate) const GAMMA: u32 = 7;"):
            if needle not in fixed:
                failures.append(f"fixed file lost declaration {needle!r}")
        if fixed.index("pub const ALPHA") > fixed.index("pub(crate) const GAMMA"):
            failures.append("fixed file still has pub after pub(crate)")
        if "/// Public constant trapped below the crate-local group." not in fixed:
            failures.append("fixed file lost the doc comment")
        doc_pos = fixed.index("/// Public constant trapped below the crate-local group.")
        alpha_pos = fixed.index("pub const ALPHA")
        between = fixed[doc_pos:alpha_pos]
        if "pub(crate)" in between:
            failures.append("doc comment no longer attaches to its declaration")

        # --- fixer keeps compliant files untouched ----------------------------
        compliant_target = compliant / "src/const.rs"
        if fixer.fix_file(compliant_target, write=True):
            failures.append("fixer rewrote a compliant file")

        # --- section banner between items travels with the FOLLOWING item ----
        banner = tmp / "banner"
        write_tree(
            banner,
            {"src/const.rs": 'pub(crate) const FIRST: u8 = 1;\n\n'
             '// ---------------------------------------------------------------------------\n'
             '// Public surface\n'
             '// ---------------------------------------------------------------------------\n\n'
             'pub const EXPORTED: u8 = 2;\n'},
        )
        banner_target = banner / "src/const.rs"
        if not fixer.fix_file(banner_target, write=True):
            failures.append("fixer skipped a file with a // section banner")
        fixed_banner = banner_target.read_text()
        if fixed_banner.index("pub const EXPORTED") > fixed_banner.index("pub(crate) const FIRST"):
            failures.append("banner file: EXPORTED did not move above FIRST")
        if "// Public surface" not in fixed_banner.split("pub const EXPORTED")[0].split("pub(crate) const FIRST")[-1]:
            failures.append("section banner did not travel with its item")
        rc, hits = run_verifier(banner)
        if [h for h in hits if h.startswith("src/const.rs:")]:
            failures.append(f"verifier still reports on fixed banner file: {hits}")

        # --- multi-line const span moves as one block -------------------------
        multi = tmp / "multi"
        write_tree(
            multi,
            {"src/static.rs": 'pub(crate) const ONE: u8 = 1;\n\n'
             '/// docs\npub const TABLE: &[u8] = &[\n    9,\n    10,\n];\n'},
        )
        multi_target = multi / "src/static.rs"
        if not fixer.fix_file(multi_target, write=True):
            failures.append("fixer missed a multi-line const item")
        fixed_multi = multi_target.read_text()
        if fixed_multi.index("pub const TABLE") > fixed_multi.index("pub(crate) const ONE"):
            failures.append("multi-line item did not move above pub(crate) item")
        if "&[\n    9,\n    10,\n];" not in fixed_multi:
            failures.append("multi-line item body was mangled")

        # --- raw-string template: `;` lines inside r#"..."# must not end the span
        raw = tmp / "raw"
        write_tree(raw, {"src/const.rs": VIOLATING_RAW})
        raw_target = raw / "src/const.rs"
        rc, hits = run_verifier(raw)
        raw_hits = [h for h in hits if h.startswith("src/const.rs:")]
        if len(raw_hits) != 1:
            failures.append(f"raw-string file: {len(raw_hits)} hit(s), want 1: {raw_hits}")
        if not fixer.fix_file(raw_target, write=True):
            failures.append("fixer missed the raw-string violating file")
        fixed_raw = raw_target.read_text()
        rc, hits = run_verifier(raw)
        if [h for h in hits if h.startswith("src/const.rs:")]:
            failures.append(f"verifier still reports on fixed raw file: {hits}")
        for needle in (
            'body { margin: 0; padding: 0; }',
            'const payload = {"type":"Reload"};',
            'pub(crate) const TAIL: u8 = 2;',
        ):
            if needle not in fixed_raw:
                failures.append(f"raw template body mangled, lost {needle!r}")
        if fixed_raw.index("pub const INDEX_HTML_DEV") > fixed_raw.index("pub(crate) const LOCAL"):
            failures.append("raw-string item did not move above pub(crate) item")

        if failures:
            print("SELF-TEST FAIL:")
            for failure in failures:
                print(f"  - {failure}")
            return 1
        print("SELF-TEST OK: verify_pub_group_order + fix_pub_group_order")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
