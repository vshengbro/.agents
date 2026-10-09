#!/usr/bin/env python3
"""Strip vestigial single-reader `pub` prefixes inside tests/ directories
(§18 tests clause, narrow rule - see verify_no_pub_in_tests.py docstring).

Only lines the verifier's cross-file analysis flags are rewritten:
same-file-only `pub` items. `pub use` re-exports and child-module items
consumed through a parent's `use r#xxx::*;` glob are load-bearing and are
never touched. Default is --dry-run; --write applies then re-verifies.
Idempotent.

Usage:
    python3 fix_no_pub_in_tests.py ROOT [--write]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from verify_no_pub_in_tests import analyze

FINDING_RE = re.compile(r"^(?P<rel>.+):(?P<lineno>\d+):")
STRIP_RE = re.compile(r"^pub(?:\(crate\)|\(super\))?\s+")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", help="repo root to scan")
    parser.add_argument("--write", action="store_true", help="apply fixes (default: dry-run)")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    planned: dict[Path, list[int]] = {}
    for finding in analyze(root):
        m = FINDING_RE.match(finding)
        if m:
            planned.setdefault(root / m.group("rel"), []).append(int(m.group("lineno")))
    changed: list[str] = []
    skipped = 0
    for path, linenos in sorted(planned.items()):
        try:
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        except (OSError, UnicodeDecodeError):
            skipped += len(linenos)
            continue
        touched = False
        for lineno in linenos:
            idx = lineno - 1
            if idx >= len(lines) or not STRIP_RE.match(lines[idx]):
                skipped += 1
                continue
            lines[idx] = STRIP_RE.sub("", lines[idx], count=1)
            touched = True
        if touched:
            changed.append(str(path.relative_to(root)))
            if args.write:
                path.write_text("".join(lines), encoding="utf-8")
    mode = "stripped" if args.write else "would-strip"
    for rel in changed:
        print(f"  {mode}: {rel}")
    total = sum(len(v) for v in planned.values())
    print(f"=== no-pub-in-tests-fixer: {total} item(s) {mode} in {len(changed)} file(s), {skipped} skipped (drifted) ===")
    if args.write and changed:
        remaining = analyze(root)
        print(f"=== no-pub-in-tests-fixer: re-verify {len(remaining)} violation(s) remaining ===")
        return 1 if remaining else 0
    return 1 if (changed and not args.write) else 0


if __name__ == "__main__":
    sys.exit(main())
